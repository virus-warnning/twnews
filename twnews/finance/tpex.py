from datetime import datetime
import io
import json
import lzma
import os.path
import re
import sqlite3
import sys
import time

import busm
import pandas

import twnews.common as common
import twnews.finance.db as db

REPEAT_LIMIT = 3
REPEAT_INTERVAL = 5

class SyncException(Exception):
    def __init__(self, reason):
        self.reason = reason

def get_cache_path(item, datestr, format):
    """
    產生快取檔路徑
    """
    cache_dir = common.get_cache_dir('tpex')
    return '%s/%s-%s.%s.xz' % (cache_dir, item, datestr, format)

def has_cache(item, datestr, format):
    """
    檢查快取檔是否存在
    """
    cache_path = get_cache_path(item, datestr, format)
    return os.path.isfile(cache_path)

def load_cache(item, datestr, format):
    """
    載入快取檔
    """
    content = None
    cache_path = get_cache_path(item, datestr, format)
    with lzma.open(cache_path, 'rt') as f_cache:
        if format == 'json':
            content = json.load(f_cache)
        else:
            content = f_cache.read()
    return content

def save_cache(item, datestr, content, format):
    """
    儲存快取檔
    """
    cache_path = get_cache_path(item, datestr, format)
    with lzma.open(cache_path, 'wt') as f_cache:
        if format == 'json':
            json.dump(content, f_cache)
        else:
            f_cache.write(content)

def get_argument(index, default=''):
    """
    取得 shell 參數, 或使用預設值
    """
    if len(sys.argv) <= index:
        return default
    return sys.argv[index]

def download_margin(datestr):
    """
    下載信用交易資料集
    """
    session = common.get_session(False)
    url = 'https://www.tpex.org.tw/web/stock/margin_trading/margin_balance/margin_bal_result.php?l=zh_tw&o=json&d=%s' % datestr
    resp = session.get(url)
    if resp.status_code == 200:
        dataset = resp.json()
        if dataset['iTotalRecords'] == 0:
            raise SyncException('日期格式錯誤，或是 %s 的資料尚未產出' % datestr)
    else:
        raise SyncException('HTTP ERROR %d' % resp.status_code)

    return dataset

def download_block(datestr):
    """
    下載鉅額交易資料集
    """
    session = common.get_session(False)
    url = 'https://www.tpex.org.tw/web/stock/block_trade/daily_qutoes/block_day_download.php?l=zh_tw&d=%s&s=0,asc,0&charset=UTF-8' % datestr
    resp = session.get(url)
    if resp.status_code == 200:
        # 不做日期驗證，因為 csv 顯示的時間，是我們傳入參數的字串，驗也是白驗
        dataset = resp.text
    else:
        raise SyncException('HTTP ERROR %d' % resp.status_code)

    return dataset

def download_institution(datestr):
    """
    下載三大法人資料集
    """
    session = common.get_session(False)
    url = 'https://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge_result.php?l=zh_tw&o=json&se=EW&t=D&d=%s&s=0,asc' % datestr
    resp = session.get(url)
    if resp.status_code == 200:
        dataset = resp.json()
        # 取標題內日期，轉換成與輸入參數相同的格式
        title = dataset['reportTitle']
        date_in_title = re.sub('[年月]', '/', title[:title.find(' ') - 1])
        # 參數日期與標題日期相同才視為有效資料
        if datestr != date_in_title:
            raise SyncException('日期格式錯誤，或是 %s 的資料尚未產出' % datestr)
    else:
        raise SyncException('HTTP ERROR %d' % resp.status_code)

    return dataset

def download_selled(datestr):
    """
    下載已借券賣出
    """
    session = common.get_session(False)
    url = 'https://www.tpex.org.tw/web/stock/margin_trading/margin_sbl/margin_sbl_download.php?l=zh-tw&d=%s&s=0,asc,0&charset=utf-8' % datestr
    resp = session.get(url)
    if resp.status_code == 200:
        dataset = resp.text
        # TODO: 移除 header 與 footer 的雜訊
        # TODO: 欄位名稱與 comma 之間的空格移除
    else:
        raise SyncException('HTTP ERROR %d' % resp.status_code)

    return dataset

def import_margin(dbcon, trading_date, dataset):
    """
    匯入信用交易資料集
    """
    sql = '''
        INSERT INTO `margin` (
            trading_date, security_id, security_name,
            buying_balance, selling_balance
        ) VALUES (?,?,?,?,?)
    '''
    for detail in dataset['aaData']:
        # TODO
        security_id = detail[0]
        security_name = detail[1].strip()
        buying_balance = int(detail[6].replace(',', ''))
        selling_balance = int(detail[14].replace(',', ''))
        dbcon.execute(sql, (
            trading_date,
            security_id,
            security_name,
            buying_balance,
            selling_balance
        ))
        """
        logger = common.get_logger('finance')
        logger.debug('[%s %s] 融資餘額: %s, 融券餘額: %s' % (
            security_id,
            security_name,
            buying_balance,
            selling_balance
        ))
        """

def import_block(dbcon, trading_date, dataset):
    """
    匯入鉅額交易資料集
    """
    col_names = ['交易型態', '交割期別', '代號', '名稱', '成交價格(元)', '成交股數', '成交值(元)', '成交時間']
    # Pandas 只能吃 file-like 參數，需要把 dataset 轉成 StringIO
    df = pandas.read_csv(io.StringIO(dataset), engine='python', sep=',', skiprows=3, skipfooter=1, names=col_names)

    sql = '''
        INSERT INTO `block` (
            trading_date, security_id, security_name,
            tick_rank, tick_type,
            close, volume, total
        ) VALUES (?,?,?,?,?,?,?,?)
    '''
    tick_rank = {}

    for _index, row in df.iterrows():
        security_id = row['代號']
        security_name = row['名稱']
        tick_type = row['交易型態']
        close = float(row['成交價格(元)'])
        volume = int(row['成交股數'].replace(',', ''))
        total = int(row['成交值(元)'].replace(',', ''))

        if security_id not in tick_rank:
            tick_rank[security_id] = 1
        else:
            tick_rank[security_id] += 1

        dbcon.execute(sql, (
            trading_date,
            security_id,
            security_name,
            tick_rank[security_id],
            tick_type,
            close,
            volume,
            total
        ))

def import_institution(dbcon, trading_date, dataset):
    """
    匯入三大法人資料集
    """
    sql = '''
        INSERT INTO `institution` (
            trading_date, security_id, security_name,
            foreign_trend, stic_trend, dealer_trend
        ) VALUES (?,?,?,?,?,?)
    '''
    for detail in dataset['aaData']:
        security_id = detail[0]
        security_name = detail[1].strip()
        # 外資 + 外資自營 + 陸資
        foreign_trend = int(detail[10].replace(',', '')) // 1000
        # 投信
        stic_trend = int(detail[13].replace(',', '')) // 1000
        # 自營投資 + 自營避險
        dealer_trend = int(detail[22].replace(',', '')) // 1000
        dbcon.execute(sql, (
            trading_date, security_id, security_name,
            foreign_trend, stic_trend, dealer_trend
        ))
        """
        logger.debug('[%s %s] 外資: %s 投信: %s 自營商: %s',
            security_id, security_name,
            foreign_trend, stic_trend, dealer_trend
        )
        """

def import_selled(dbcon, trading_date, dataset):
    """
    匯入借券賣出
    """
    df = pandas.read_csv(io.StringIO(dataset), engine='python', sep=',', skiprows=2, skipfooter=13)
    #print(df.head(3))
    #print(df.tail(3))
    for index, row in df.iterrows():
        print(row['股票代號'])
        print(row[' 融券前日餘額'])
        print(row)
        print(row[' 借券賣出當日餘額'])
        # break

    # TODO: 匯入 SQLite

def sync_dataset(dsitem, trading_date='latest'):
    """
    同步資料集共用流程

    * HTTP 日期格式: 108/05/29
    * DB, Cache 日期格式: 2019-05-29
    """
    if trading_date == 'latest':
        trading_date = datetime.today().strftime('%Y-%m-%d')

    logger = common.get_logger('finance')
    dtm = re.match(r'(\d{4})-(\d{2})-(\d{2})', trading_date)
    tokens = [
        str(int(dtm.group(1)) - 1911),
        dtm.group(2),
        dtm.group(3)
    ]
    datestr = '/'.join(tokens)
    format = 'json'
    this_mod = sys.modules[__name__]

    if has_cache(dsitem, trading_date, format):
        # 載入快取資料集
        logger.info('套用 TPEX %s 的 %s 快取', trading_date, dsitem)
        dataset = load_cache(dsitem, trading_date, format)
    else:
        # 下載資料集
        dataset = None
        repeat = 0
        hookfunc = getattr(this_mod, 'download_' + dsitem)
        while dataset is None and repeat < REPEAT_LIMIT:
            repeat += 1
            if repeat > 1:
                time.sleep(REPEAT_INTERVAL)
            try:
                logger.info('下載 TPEX %s 的 %s', trading_date, dsitem)
                dataset = hookfunc(datestr)
                logger.debug('儲存 TPEX %s 的 %s', trading_date, dsitem)
                save_cache(dsitem, trading_date, dataset, format)
            except Exception as ex:
                logger.error('無法取得 TPEX %s 的 %s (重試: %d, %s)', trading_date, dsitem, repeat, ex.reason)

    if dataset is None:
        return

    # return

    # 匯入資料庫
    dbcon = db.get_connection()
    hookfunc = hookfunc = getattr(this_mod, 'import_' + dsitem)
    try:
        hookfunc(dbcon, trading_date, dataset)
        logger.info('匯入 TPEX %s 的 %s', trading_date, dsitem)
    except sqlite3.IntegrityError as ex:
        logger.warning('已經匯入過 TPEX %s 的 %s', trading_date, dsitem)
    except Exception as ex:
        # TODO: ex.args[0] 不確定是否可靠, 需要再確認
        logger.error('無法匯入 TPEX %s 的 %s (%s)', trading_date, dsitem, ex.args[0])
    dbcon.commit()
    dbcon.close()

def main():
    """
    python3 -m twnews.finance.tpex {action}
    python3 -m twnews.finance.tpex {action} {date}
    """
    action = get_argument(1)
    trading_date = get_argument(2, 'latest')

    if trading_date != 'latest' and re.match(r'^\d{4}-\d{2}-\d{2}$', trading_date) is None:
        print('日期格式錯誤')
        return

    if action in ['block', 'margin', 'institution', 'selled']:
        sync_dataset(action, trading_date)
    else:
        print('參數錯誤')

if __name__ == '__main__':
    main()
