"""
證交所資料蒐集模組
"""

from datetime import datetime
import io
import re
import sqlite3
import sys
import time

import pandas

import twnews.common as common
from twnews.finance import get_argument, fucking_get, get_connection, REPEAT_LIMIT, REPEAT_INTERVAL
from twnews.cache import DailyCache
from twnews.exceptions import NetworkException, InvalidDataException

def download_margin(datestr):
    """
    下載信用交易資料集
    """
    url = 'http://www.twse.com.tw/exchangeReport/MI_MARGN'
    params = {
        'date': datestr,
        'response': 'json',
        'selectType': 'ALL'
    }
    def hook(resp):
        dataset = resp.json()
        status = dataset['stat']
        if status == 'OK':
            if dataset['data']:
                raise InvalidDataException('可能尚未結算或是非交易日')
        else:
            raise NetworkException(status)
        return dataset
    return fucking_get(hook, url, params)

def download_block(datestr):
    """
    下載鉅額交易資料集
    """
    url = 'http://www.twse.com.tw/block/BFIAUU'
    params = {
        'date': datestr,
        'response': 'json',
        'selectType': 'S'
    }
    def hook(resp):
        dataset = resp.json()
        status = dataset['stat']
        if status == 'OK':
            if dataset['data']:
                raise InvalidDataException('可能尚未結算或是非交易日')
        else:
            raise NetworkException(status)
        return dataset
    return fucking_get(hook, url, params)

def download_institution(datestr):
    """
    下載三大法人資料集
    """
    url = 'http://www.twse.com.tw/fund/T86'
    params = {
        'date': datestr,
        'response': 'json',
        'selectType': 'ALL'
    }
    def hook(resp):
        # TODO: 需要驗證資料完整性
        dataset = resp.json()
        status = dataset['stat']
        if status != 'OK':
            raise NetworkException(status)
        return dataset
    return fucking_get(hook, url, params)

def download_borrowed(datestr):
    """
    下載可借券賣出資料集 (只有當天資料)
    TODO: 待確認資料切換時間
    """
    url = 'http://www.twse.com.tw/SBL/TWT96U'
    params = {
        'response': 'csv'
    }
    def hook(resp):
        dataset = resp.text
        line1 = dataset[:dataset.find('\r\n')]
        match = re.search(r'(\d{3})年(\d{2})月(\d{2})日', line1)
        if match is not None:
            dtup = (
                int(match.group(1)) + 1911,
                match.group(2),
                match.group(3)
            )
            dsdate = '%04d%s%s' % dtup
            if dsdate != datestr:
                raise InvalidDataException('資料日期 %s 與指定日期不同' % dsdate)
        else:
            raise NetworkException('無法取得 CSV 內的日期字串')
        return dataset
    return fucking_get(hook, url, params)

def download_selled(datestr):
    """
    下載已借券賣出
    """
    url = 'http://www.twse.com.tw/exchangeReport/TWT93U'
    params = {
        'date': datestr,
        'response': 'json'
    }
    def hook(resp):
        dataset = resp.json()
        status = dataset['stat']
        if status == 'OK':
            if dataset['data']:
                raise InvalidDataException('可能尚未結算或非交易日')
        else:
            raise NetworkException(status)
        return dataset
    return fucking_get(hook, url, params)

def download_etfnet(datestr):
    """
    下載 ETF 淨值折溢價率
    """
    url = 'https://mis.twse.com.tw/stock/data/all_etf.txt'
    params = {}
    def hook(resp):
        dataset = resp.json()
        dsdate = dataset['a1'][1]['msgArray'][0]['i']
        if datestr != dsdate:
            raise InvalidDataException('資料日期 %s 與指定日期不同' % dsdate)
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
    dfrm = pandas.read_csv(io.StringIO(dataset), sep=',', skiprows=3, header=None, names=col_names)
    cnt = 0
    for _, row in dfrm.iterrows():
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

def sync_dataset(dsitem, trading_date='latest'):
    """
    同步資料集共用流程
    """
    if trading_date == 'latest':
        trading_date = datetime.today().strftime('%Y-%m-%d')

    logger = common.get_logger('finance')
    datestr = trading_date.replace('-', '')
    data_format = 'csv' if dsitem == 'borrowed' else 'json'
    this_mod = sys.modules[__name__]

    daily_cache = DailyCache('twse', dsitem, data_format)
    if daily_cache.has(datestr):
        # 載入快取資料集
        logger.debug('套用 TWSE %s 的 %s 快取', trading_date, dsitem)
        dataset = daily_cache.load(datestr)
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
                logger.info('下載 TWSE %s 的 %s', trading_date, dsitem)
                dataset = hookfunc(datestr)
                logger.debug('儲存 TWSE %s 的 %s', trading_date, dsitem)
                daily_cache.save(datestr, dataset)
            except InvalidDataException as ex:
                logger.error(
                    '無法取得 TWSE %s 的 %s (重試: %d, %s)',
                    trading_date, dsitem, repeat, ex.reason
                )
                repeat = REPEAT_LIMIT
            except NetworkException as ex:
                logger.error(
                    '無法取得 TWSE %s 的 %s (重試: %d, %s)',
                    trading_date, dsitem, repeat, ex.reason
                )

    if dataset is None:
        return

    # 匯入資料庫
    # pylint: disable=bare-except
    dbcon = get_connection()
    hookfunc = getattr(this_mod, 'import_' + dsitem)
    try:
        hookfunc(dbcon, trading_date, dataset)
        logger.info('匯入 TWSE %s 的 %s', trading_date, dsitem)
    except sqlite3.IntegrityError as ex:
        logger.warning('已經匯入過 TWSE %s 的 %s', trading_date, dsitem)
    except:
        # TODO: ex.args[0] 不確定是否可靠, 需要再確認
        logger.error('無法匯入 TWSE %s 的 %s', trading_date, dsitem)
    dbcon.commit()
    dbcon.close()

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
