from datetime import datetime
import io
import re
import sqlite3
import sys
import time

import busm
import pandas
from requests.exceptions import RequestException

import twnews.common as common
from twnews.finance import get_argument, fucking_get, get_connection, REPEAT_LIMIT, REPEAT_INTERVAL
from twnews.cache import DailyCache
from twnews.exceptions import NetworkException, InvalidDataException

URL_BASE = 'https://www.tpex.org.tw/web/stock/'

def download_margin(datestr):
    """
    下載信用交易資料集
    """
    url = URL_BASE + 'margin_trading/margin_balance/margin_bal_result.php'
    params = {
        'd': datestr,
        'l': 'zh_tw',
        'o': 'json'
    }
    def hook(resp):
        dataset = resp.json()
        if dataset['iTotalRecords'] == 0:
            raise InvalidDataException('日期格式錯誤，或是 %s 的資料尚未產出' % datestr)
        return dataset
    return fucking_get(hook, url, params)

def download_block(datestr):
    """
    下載鉅額交易資料集
    """
    url = URL_BASE + 'block_trade/daily_qutoes/block_day_download.php'
    params = {
        'd': datestr,
        'l': 'zh_tw',
        's': '0,asc,0',
        'charset': 'UTF-8'
    }
    def hook(resp):
        # TODO: 需要檢查資料完整性，任意日期都有資料
        dataset = resp.text
        return dataset
    return fucking_get(hook, url, params)

def download_institution(datestr):
    """
    下載三大法人資料集
    """
    url = URL_BASE + '3insti/daily_trade/3itrade_hedge_result.php'
    params = {
        'd': datestr,
        'l': 'zh_tw',
        'o': 'json',
        's': '0,asc',
        't': 'D',
        'se': 'EW'
    }
    def hook(resp):
        dataset = resp.json()
        # 取標題內日期，轉換成與輸入參數相同的格式
        title = dataset['reportTitle']
        date_in_title = re.sub('[年月]', '/', title[:title.find(' ') - 1])
        # 參數日期與標題日期相同才視為有效資料
        if datestr != date_in_title:
            raise InvalidDataException('日期格式錯誤，或是 %s 的資料尚未產出' % datestr)
        return dataset
    return fucking_get(hook, url, params)

def download_selled(datestr):
    """
    下載已借券賣出
    """
    url = URL_BASE + 'margin_trading/margin_sbl/margin_sbl_download.php'
    params = {
        'd': datestr,
        'l': 'zh-tw',
        's': '0,asc,0',
        'charset': 'utf-8'
    }
    def hook(resp):
        # TODO: 非交易日還是有資料，不過只有 header 和 footer
        obuf = io.StringIO()
        ibuf = io.StringIO(resp.text)

        # 過濾 header, footer & 欄位名稱消除空白字元
        enabled = False
        line = ibuf.readline()
        while len(line) > 0:
            if not enabled:
                enabled = line.startswith('股票代號')
                if enabled:
                    line = line.replace(' ', '')
            else:
                enabled = line.startswith('"')
            if enabled:
                obuf.write(line)
            line = ibuf.readline()

        dataset = obuf.getvalue()
        ibuf.close()
        obuf.close()
        return dataset
    return fucking_get(hook, url, params)

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
    sql = '''
        UPDATE `short_sell` SET `security_name`=?,`selled`=?
        WHERE `trading_date`=? AND `security_id`=?
    '''
    df = pandas.read_csv(io.StringIO(dataset), sep=',')
    for index, row in df.iterrows():
        security_id = row['股票代號']
        security_name = row['股票名稱'].strip()
        balance = int(row['借券賣出當日餘額'].replace(',', ''))
        dbcon.execute(sql, (security_name, balance, trading_date, security_id))

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
    format = 'csv' if dsitem in ['block', 'selled'] else 'json'
    this_mod = sys.modules[__name__]

    daily_cache = DailyCache('tpex', dsitem, format)
    if daily_cache.has(trading_date):
        # 載入快取資料集
        logger.info('套用 TPEX %s 的 %s 快取', trading_date, dsitem)
        dataset = daily_cache.load(trading_date)
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
                daily_cache.save(trading_date, dataset)
            except InvalidDataException as ex:
                logger.error('無法取得 TPEX %s 的 %s (重試: %d, %s)', trading_date, dsitem, repeat, ex.reason)
                repeat = REPEAT_LIMIT
            except Exception as ex:
                logger.error('無法取得 TPEX %s 的 %s (重試: %d, %s)', trading_date, dsitem, repeat, ex.reason)

    if dataset is None:
        return

    # return

    # 匯入資料庫
    dbcon = get_connection()
    hookfunc = getattr(this_mod, 'import_' + dsitem)
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
