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
    cache_dir = common.get_cache_dir('twse')
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
    url = 'http://www.twse.com.tw/exchangeReport/MI_MARGN?response=json&date=%s&selectType=ALL' % datestr
    resp = session.get(url)
    if resp.status_code == 200:
        dataset = resp.json()
        status = dataset['stat']
        if status == 'OK':
            if len(dataset['data']) == 0:
                raise SyncException('可能尚未結算或是非交易日')
        else:
            raise SyncException(status)
    else:
        raise SyncException('HTTP ERROR %d' % resp.status_code)

    return dataset

def download_block(datestr):
    """
    下載鉅額交易資料集
    """
    session = common.get_session(False)
    url = 'http://www.twse.com.tw/block/BFIAUU?response=json&date=%s&selectType=S' % datestr
    resp = session.get(url)
    if resp.status_code == 200:
        dataset = resp.json()
        status = dataset['stat']
        if status == 'OK':
            if len(dataset['data']) == 0:
                raise SyncException('可能尚未結算或是非交易日')
        else:
            raise SyncException(status)
    else:
        raise SyncException('HTTP ERROR %d' % resp.status_code)

    return dataset

def download_institution(datestr):
    """
    下載三大法人資料集
    """
    session = common.get_session(False)
    url = 'http://www.twse.com.tw/fund/T86?response=json&date=%s&selectType=ALL' % datestr
    resp = session.get(url)
    if resp.status_code == 200:
        dataset = resp.json()
        status = dataset['stat']
        if status != 'OK':
            raise SyncException(status)
    else:
        raise SyncException('HTTP ERROR %d' % resp.status_code)

    return dataset

def download_borrowed(datestr):
    """
    下載可借券賣出資料集 (只有當天資料)
    TODO: 待確認資料切換時間
    """
    session = common.get_session(False)
    url = 'http://www.twse.com.tw/SBL/TWT96U?response=csv'
    resp = session.get(url)
    if resp.status_code == 200:
        dataset = resp.text
        line1 = dataset[:dataset.find('\r\n')]
        match = re.search(r'(\d{3})年(\d{2})月(\d{2})日', line1)
        if match is not None:
            yy = int(match.group(1)) + 1911
            mm = match.group(2)
            dd = match.group(3)
            dsdate = '%04d%s%s' % (yy, mm, dd)
            if dsdate != datestr:
                raise SyncException('資料日期 %s 與指定日期不同' % dsdate)
        else:
            raise SyncException('無法取得 CSV 內的日期字串')
    else:
        raise SyncException('HTTP ERROR %d' % resp.status_code)

    return dataset

def download_selled(datestr):
    """
    下載已借券賣出
    """
    session = common.get_session(False)
    url = 'http://www.twse.com.tw/exchangeReport/TWT93U?response=json&date=%s' % datestr
    resp = session.get(url)
    if resp.status_code == 200:
        dataset = resp.json()
        status = dataset['stat']
        if status == 'OK':
            if len(dataset['data']) == 0:
                raise SyncException('可能尚未結算或非交易日')
        else:
            raise SyncException(status)
    else:
        raise SyncException('HTTP ERROR %d' % resp.status_code)

    return dataset

def download_etfnet(datestr):
    """
    下載 ETF 淨值折溢價率
    """
    url = 'https://mis.twse.com.tw/stock/data/all_etf.txt'
    session = common.get_session(False)
    resp = session.get(url)
    if resp.status_code == 200:
        dataset = resp.json()
        dsdate = dataset['a1'][1]['msgArray'][0]['i']
        if datestr != dsdate:
            raise SyncException('資料日期 %s 與指定日期不同' % dsdate)
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
    for detail in dataset['data']:
        security_id = detail[0]
        security_name = detail[1].strip()
        buying_balance = int(detail[6].replace(',', ''))
        selling_balance = int(detail[12].replace(',', ''))
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
    sql = '''
        INSERT INTO `block` (
            trading_date, security_id, security_name,
            tick_rank, tick_type,
            close, volume, total
        ) VALUES (?,?,?,?,?,?,?,?)
    '''
    tick_rank = {}
    for trade in dataset['data']:
        if trade[0] == '總計':
            break
        security_id = trade[0]
        security_name = trade[1]
        tick_type = trade[2]
        close = float(trade[3].replace(',', ''))
        volume = int(trade[4].replace(',', ''))
        total = int(trade[5].replace(',', ''))
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
        """
        logger.debug('[%s %s] #%d %s 成交價: %s 股數: %s 金額: %s' % (
            security_id,
            security_name,
            tick_rank[security_id],
            tick_type,
            close,
            volume,
            total
        ))
        """

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
    for detail in dataset['data']:
        security_id = detail[0]
        security_name = detail[1].strip()
        foreign_trend = int(detail[4].replace(',', '')) // 1000
        stic_trend = int(detail[10].replace(',', '')) // 1000
        dealer_trend = int(detail[11].replace(',', '')) // 1000
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

def import_borrowed(dbcon, trading_date, dataset):
    """
    匯入可借券賣出資料集 (使用 pandas 處理 CSV)
    """
    sql = '''
        INSERT INTO `short_sell` (
            trading_date, security_id, borrowed
        ) VALUES (?,?,?)
    '''
    col_names = ['sec1', 'vol1', 'sec2', 'vol2', 'shit']
    # Pandas 只能吃 file-like 參數，需要把 dataset 轉成 StringIO
    df = pandas.read_csv(io.StringIO(dataset), sep=',', skiprows=3, header=None, names=col_names)
    cnt = 0
    for index, row in df.iterrows():
        # 匯入左側資料
        security_id = row['sec1'].strip('="')
        borrowed = int(row['vol1'].replace(',', ''))
        dbcon.execute(sql, (trading_date, security_id, borrowed))
        cnt += 1
        # 匯入右側資料
        security_id = row['sec2'].strip('="')
        if security_id != '_':
            borrowed = int(row['vol2'].replace(',', ''))
            dbcon.execute(sql, (trading_date, security_id, borrowed))
            cnt += 1

def import_selled(dbcon, trading_date, dataset):
    """
    匯入已借券賣出資料集
    """
    sql = '''
        UPDATE `short_sell` SET `security_name`=?, `selled`=?
        WHERE `trading_date`=? AND `security_id`=?
    '''
    for detail in dataset['data']:
        security_id = detail[0]
        security_name = detail[1].strip()
        balance = int(detail[12].replace(',', '')) // 1000
        if security_id != '':
            # TODO: 如果 WHERE 條件不成立，沒更新到資料，應該要產生 Exception 觸發錯誤回報
            dbcon.execute(sql, (
                security_name, balance,
                trading_date, security_id
            ))
            """
            logger.debug('[%s %s] 已借券賣出餘額: %s',
                security_id, security_name, balance
            )
            """

def import_etfnet(dbcon, trading_date, dataset):
    """
    匯入 ETF 淨值折溢價率
    """
    # 來源資料轉換 key/value 形式
    # 相同發行者的 ETF 會放一組
    etf_dict = {}
    for fund in dataset['a1']:
        if 'msgArray' in fund:
            for etf in fund['msgArray']:
                etf_dict[etf['a']] = etf

    # 依證券代碼順序處理
    sql = '''
        INSERT INTO `etf_offset` (
            trading_date, security_id, security_name,
            close, net, offset
        ) VALUES (?,?,?,?,?,?)
    '''
    for k in sorted(etf_dict.keys()):
        etf = etf_dict[k]
        dbcon.execute(sql, (trading_date, etf['a'], etf['b'], etf['e'], etf['f'], etf['g']))
        """
        logger.debug('%s, %s, %s, %s%%', etf['a'], etf['b'], etf['f'], etf['g'])
        """

def sync_dataset(dsitem, trading_date='latest'):
    """
    同步資料集共用流程
    """
    if trading_date == 'latest':
        trading_date = datetime.today().strftime('%Y-%m-%d')

    logger = common.get_logger('finance')
    datestr = trading_date.replace('-', '')
    format = 'csv' if dsitem == 'borrowed' else 'json'
    this_mod = sys.modules[__name__]

    if has_cache(dsitem, datestr, format):
        # 載入快取資料集
        logger.info('套用 %s 的 %s 快取', trading_date, dsitem)
        dataset = load_cache(dsitem, datestr, format)
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
                logger.info('下載 %s 的 %s', trading_date, dsitem)
                dataset = hookfunc(datestr)
                logger.info('儲存 %s 的 %s', trading_date, dsitem)
                save_cache(dsitem, datestr, dataset, format)
            except Exception as ex:
                # 2019-08-08: 這裡的重試效果不夠理想，3 次重試的結果都失敗，可能要改用別的重試機制
                logger.error('無法取得 %s 的 %s (重試: %d, %s)', trading_date, dsitem, repeat, ex.reason)

    if dataset is None:
        return

    # 匯入資料庫
    dbcon = db.get_connection()
    hookfunc = hookfunc = getattr(this_mod, 'import_' + dsitem)
    try:
        hookfunc(dbcon, trading_date, dataset)
        logger.info('匯入 %s 的 %s', trading_date, dsitem)
    except sqlite3.IntegrityError as ex:
        logger.warning('已經匯入過 %s 的 %s', trading_date, dsitem)
    except Exception as ex:
        # TODO: ex.args[0] 不確定是否可靠, 需要再確認
        logger.error('無法匯入 %s 的 %s (%s)', trading_date, dsitem, ex.args[0])
    dbcon.commit()
    dbcon.close()

@busm.through_telegram
def main():
    """
    python3 -m twnews.finance.twse {action}
    python3 -m twnews.finance.twse {action} {date}
    """
    action = get_argument(1)
    trading_date = get_argument(2, 'latest')

    if trading_date != 'latest' and re.match(r'^\d{4}-\d{2}-\d{2}$', trading_date) is None:
        print('日期格式錯誤')
        return

    if action in ['block', 'margin', 'institution', 'borrowed', 'selled', 'etfnet']:
        sync_dataset(action, trading_date)
    else:
        print('參數錯誤')

if __name__ == '__main__':
    main()
