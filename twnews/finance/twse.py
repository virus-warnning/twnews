from datetime import datetime
import json
import os.path
import re
import sys

import pandas

import twnews.common as common
import twnews.finance.db as db

def get_cache_path(item, datestr, format='json'):
    cache_dir = common.get_cache_dir('twse')
    return '%s/%s-%s.%s' % (cache_dir, item, datestr, format)

def has_cache(item, datestr, format='json'):
    cache_path = get_cache_path(item, datestr, format)
    return os.path.isfile(cache_path)

def load_cache(item, datestr, format='json'):
    content = None
    cache_path = get_cache_path(item, datestr, format)
    with open(cache_path, 'r') as f_cache:
        if format == 'json':
            content = json.load(f_cache)
        else:
            content = f_cache.read()
    return content

def save_cache(item, datestr, content, format='json'):
    cache_path = get_cache_path(item, datestr, format)
    with open(cache_path, 'w') as f_cache:
        if format == 'json':
            json.dump(content, f_cache)
        else:
            f_cache.write(content)

def sync_margin_trading(trading_date):
    """
    融資融券
    """
    dsitem = 'margin_trading'
    logger = common.get_logger('finance')
    datestr = trading_date.replace('-', '')

    # 快取處理
    if has_cache(dsitem, datestr):
        logger.info('載入 %s 的融資融券', datestr)
        ds = load_cache(dsitem, datestr)
    else:
        logger.info('沒有 %s 的融資融券', datestr)
        session = common.get_session(False)
        url = 'http://www.twse.com.tw/exchangeReport/MI_MARGN?response=json&date=%s&selectType=ALL' % datestr
        resp = session.get(url)
        ds = resp.json()
        status = ds['stat']
        # 注意! 即使發生問題, HTTP 回應碼也是 200, 必須依 JSON 分辨成功或失敗
        # 成功: OK
        # 失敗: 查詢日期大於可查詢最大日期，請重新查詢!
        #      很抱歉，目前線上人數過多，請您稍候再試
        if status != 'OK':
            logger.error('無法取得 %s 的融資融券資料, 原因: %s', datestr, status)
            return
        if len(ds['data']) == 0:
            logger.error('沒有 %s 的融資融券資料, 可能尚未結算或是非交易日', datestr)
            return
        logger.info('儲存 %s 的融資融券', datestr)
        save_cache(dsitem, datestr, ds)

    db_conn = db.get_connection()
    sql = '''
        INSERT INTO `margin` (
            trading_date, security_id, security_name,
            buying_balance, selling_balance
        ) VALUES (?,?,?,?,?)
    '''
    for detail in ds['data']:
        security_id = detail[0]
        security_name = detail[1].strip()
        buying_balance = int(detail[6].replace(',', ''))
        selling_balance = int(detail[12].replace(',', ''))
        db_conn.execute(sql, (
            trading_date,
            security_id,
            security_name,
            buying_balance,
            selling_balance
        ))
        logger.debug('[%s %s] 融資餘額: %s, 融券餘額: %s' % (
            security_id,
            security_name,
            buying_balance,
            selling_balance
        ))
    db_conn.commit()
    db_conn.close()

def sync_block_trading(trading_date):
    """
    鉅額交易
    """
    dsitem = 'block_trading'
    logger = common.get_logger('finance')
    datestr = trading_date.replace('-', '')

    # 快取處理
    if has_cache(dsitem, datestr):
        logger.info('載入 %s 的鉅額交易', datestr)
        ds = load_cache(dsitem, datestr)
    else:
        logger.info('沒有 %s 的鉅額交易', datestr)
        session = common.get_session(False)
        url = 'http://www.twse.com.tw/block/BFIAUU?response=json&date=%s&selectType=S' % datestr
        resp = session.get(url)
        ds = resp.json()
        status = ds['stat']
        # 注意! 即使發生問題, HTTP 回應碼也是 200, 必須依 JSON 分辨成功或失敗
        # 成功: OK
        # 失敗: 查詢日期大於可查詢最大日期，請重新查詢!
        #      很抱歉，目前線上人數過多，請您稍候再試
        if status != 'OK':
            logger.error('無法取得 %s 的鉅額交易資料, 原因: %s', datestr, status)
            return
        if len(ds['data']) == 0:
            logger.error('沒有 %s 的鉅額交易資料, 可能尚未結算或是非交易日', datestr)
            return
        logger.info('儲存 %s 的鉅額交易', datestr)
        save_cache(dsitem, datestr, ds)

    db_conn = db.get_connection()
    sql = '''
        INSERT INTO `block` (
            trading_date, security_id, security_name,
            tick_rank, tick_type,
            close, volume, total
        ) VALUES (?,?,?,?,?,?,?,?)
    '''
    tick_rank = {}
    for trade in ds['data']:
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
        db_conn.execute(sql, (
            trading_date,
            security_id,
            security_name,
            tick_rank[security_id],
            tick_type,
            close,
            volume,
            total
        ))
        logger.debug('[%s %s] #%d %s 成交價: %s 股數: %s 金額: %s' % (
            security_id,
            security_name,
            tick_rank[security_id],
            tick_type,
            close,
            volume,
            total
        ))
    db_conn.commit()
    db_conn.close()

def sync_institution_trading(trading_date):
    """
    三大法人
    """
    dsitem = 'institution_trading'
    logger = common.get_logger('finance')
    datestr = trading_date.replace('-', '')

    # 快取處理
    if has_cache(dsitem, datestr):
        logger.info('載入 %s 的三大法人', datestr)
        ds = load_cache(dsitem, datestr)
    else:
        logger.info('沒有 %s 的三大法人', datestr)
        session = common.get_session(False)
        url = 'http://www.twse.com.tw/fund/T86?response=json&date=%s&selectType=ALL' % datestr
        resp = session.get(url)
        ds = resp.json()
        status = ds['stat']
        # 注意! 即使發生問題, HTTP 回應碼也是 200, 必須依 JSON 分辨成功或失敗
        # 成功: OK
        # 失敗: 查詢日期大於可查詢最大日期，請重新查詢!
        #      很抱歉，目前線上人數過多，請您稍候再試
        if status != 'OK':
            logger.error('無法取得 %s 的三大法人資料, 原因: %s', datestr, status)
            return
        logger.info('儲存 %s 的三大法人', datestr)
        save_cache(dsitem, datestr, ds)

    # 匯入 SQLite
    db_conn = db.get_connection()
    sql = '''
        INSERT INTO `institution` (
            trading_date, security_id, security_name,
            foreign_trend, stic_trend, dealer_trend
        ) VALUES (?,?,?,?,?,?)
    '''
    for detail in ds['data']:
        security_id = detail[0]
        security_name = detail[1].strip()
        foreign_trend = int(detail[4].replace(',', '')) // 1000
        stic_trend = int(detail[10].replace(',', '')) // 1000
        dealer_trend = int(detail[11].replace(',', '')) // 1000
        db_conn.execute(sql, (
            trading_date, security_id, security_name,
            foreign_trend, stic_trend, dealer_trend
        ))
        logger.debug('[%s %s] 外資: %s 投信: %s 自營商: %s',
            security_id, security_name,
            foreign_trend, stic_trend, dealer_trend
        )
    db_conn.commit()
    db_conn.close()

def sync_short_borrowed(trading_date):
    """
    可借券賣出
    - 只有當天資料
    - 待確認資料切換時間
    """
    dsitem = 'short_borrowed'
    logger = common.get_logger('finance')
    datestr = trading_date.replace('-', '')

    if not has_cache(dsitem, datestr, 'csv'):
        session = common.get_session(False)
        url = 'http://www.twse.com.tw/SBL/TWT96U?response=csv'
        resp = session.get(url)
        ds = resp.text
        line1 = ds[:ds.find('\r\n')]
        match = re.search(r'(\d{3})年(\d{2})月(\d{2})日', line1)
        if match is None:
            logger.error('可借券賣出的 CSV 無法取得日期字串')
            return
        yy = int(match.group(1)) + 1911
        mm = match.group(2)
        dd = match.group(3)
        dsdate = '%04d%s%s' % (yy, mm, dd)
        if dsdate != datestr:
            logger.error('可借券賣出的資料日期與指定日期不同, 資料日期 %s, 指定日期 %s', dsdate, datestr)
            return
        logger.error('可借券賣出的資料寫入快取: %s', datestr)
        save_cache(dsitem, datestr, ds, 'csv')

    db_conn = db.get_connection()
    sql = '''
        INSERT INTO `short_sell` (
            trading_date, security_id, borrowed
        ) VALUES (?,?,?)
    '''
    logger.info('載入 %s 的可借券賣出', datestr)
    csv_path = get_cache_path(dsitem, datestr, 'csv')
    col_names = ['sec1', 'vol1', 'sec2', 'vol2', 'shit']
    df = pandas.read_csv(csv_path, sep=',', skiprows=3, header=None, names=col_names)
    cnt = 0
    for index, row in df.iterrows():
        security_id = row['sec1'].strip('="')
        borrowed = int(row['vol1'].replace(',', ''))
        db_conn.execute(sql, (trading_date, security_id, borrowed))
        cnt += 1
        security_id = row['sec2'].strip('="')
        if security_id != '_':
            borrowed = int(row['vol2'].replace(',', ''))
            db_conn.execute(sql, (trading_date, security_id, borrowed))
            cnt += 1
    db_conn.commit()
    db_conn.close()

def sync_short_selled(trading_date):
    """
    已借券賣出
    """
    dsitem = 'short_selled'
    logger = common.get_logger('finance')
    datestr = trading_date.replace('-', '')

    # 快取處理
    if has_cache(dsitem, datestr):
        logger.info('載入 %s 的已借券賣出', datestr)
        ds = load_cache(dsitem, datestr)
    else:
        logger.info('沒有 %s 的已借券賣出', datestr)
        session = common.get_session(False)
        url = 'http://www.twse.com.tw/exchangeReport/TWT93U?response=json&date=%s' % datestr
        resp = session.get(url)
        ds = resp.json()
        status = ds['stat']
        # 注意! 即使發生問題, HTTP 回應碼也是 200, 必須依 JSON 分辨成功或失敗
        # 成功: OK
        # 失敗: 查詢日期大於可查詢最大日期，請重新查詢!
        #      很抱歉，目前線上人數過多，請您稍候再試
        if status != 'OK':
            logger.error('無法取得 %s 的已借券賣出資料, 原因: %s', datestr, status)
            return
        if len(ds['data']) == 0:
            logger.error('尚未生成 %s 的已借券賣出資料, 可能尚未結算或非交易日', datestr)
            return
        logger.info('儲存 %s 的已借券賣出', datestr)
        save_cache(dsitem, datestr, ds)

    db_conn = db.get_connection()
    sql = '''
        UPDATE `short_sell` SET `security_name`=?, `selled`=?
        WHERE `trading_date`=? AND `security_id`=?
    '''
    for detail in ds['data']:
        security_id = detail[0]
        security_name = detail[1].strip()
        balance = int(detail[12].replace(',', '')) // 1000
        if security_id != '':
            db_conn.execute(sql, (
                security_name, balance,
                trading_date, security_id
            ))
            logger.debug('[%s %s] 已借券賣出餘額: %s',
                security_id, security_name, balance
            )
    db_conn.commit()
    db_conn.close()

def sync_etf_net(trading_date):
    """
    https://mis.twse.com.tw/stock/data/all_etf.txt
    {
      "a1": [
        {
          "msgArray": [
            {
              "a": "", 代碼
              "b": "", 名稱
              "c": "", 發行量
              "d": "", 與前日發行量變化
              "e": "", 成交價
              "f": "", 淨值
              "g": "", 折溢價率
              "h": "", 前日淨值
              "i": "", 日期
              "j": "", 時間
              "k": "", ETF 類型 (1~4)
            },
            ...
          ]
          "refURL": "https://www.kgifund.com.tw/ETF/RWD/Introduction.aspx",
          "userDelay": "15000",
          "rtMessage": "OK",
          "rtCode": "0000"
        },
        ...
        {} <-- 最後有一組空的
      ]
    }
    """
    dsitem = 'etf_net'
    logger = common.get_logger('finance')
    datestr = trading_date.replace('-', '')

    # 快取處理
    if has_cache(dsitem, datestr):
        logger.info('載入 %s 的 ETF 溢價率快取', datestr)
        ds = load_cache(dsitem, datestr)
    else:
        logger.info('沒有 %s 的 ETF 溢價率快取', datestr)
        session = common.get_session(False)
        resp = session.get('https://mis.twse.com.tw/stock/data/all_etf.txt')
        ds = resp.json()
        dsdate = ds['a1'][1]['msgArray'][0]['i']
        if datestr == dsdate:
            logger.info('儲存 %s 的 ETF 溢價率快取', datestr)
            save_cache(dsitem, datestr, ds)
        else:
            logger.info('無法取得 %s 的 ETF 溢價率資料', datestr)
            return

    # 來源資料轉換 key/value 形式
    etf_dict = {}
    for fund in ds['a1']:
        if 'msgArray' in fund:
            for etf in fund['msgArray']:
                etf_dict[etf['a']] = etf

    # 依證券代碼順序處理
    db_conn = db.get_connection()
    sql = '''
        INSERT INTO `etf_offset` (
            trading_date, security_id, security_name,
            close, net, offset
        ) VALUES (?,?,?,?,?,?)
    '''
    for k in sorted(etf_dict.keys()):
        etf = etf_dict[k]
        db_conn.execute(sql, (trading_date, etf['a'], etf['b'], etf['e'], etf['f'], etf['g']))
        logger.debug('%s, %s, %s, %s%%', etf['a'], etf['b'], etf['f'], etf['g'])
    db_conn.commit()
    db_conn.close()

def get_argument(index, default=''):
    if len(sys.argv) <= index:
        return default
    return sys.argv[index]

def main():
    """
    python3 -m twnews.finance.twse {action}
    python3 -m twnews.finance.twse {action} {date}
    """
    # 08:30 爬可借券賣出餘額
    # 16:00 爬三大法人、鉅額交易、ETF折溢價
    # 19:00 爬融資融券、已借券賣出餘額
    action_funcs = {
        'block': sync_block_trading,
        'borrowed': sync_short_borrowed,
        'etfnet': sync_etf_net,
        'institution': sync_institution_trading,
        'margin': sync_margin_trading,
        'selled': sync_short_selled
    }
    today = datetime.today().strftime('%Y-%m-%d')
    action = get_argument(1)
    trading_date = get_argument(2, today)

    if re.match(r'\d{4}-\d{2}-\d{2}', trading_date) is None:
        print('日期格式錯誤')
        return

    if action in action_funcs:
        action_funcs[action](trading_date)
    else:
        print('參數錯誤')

if __name__ == '__main__':
    main()
