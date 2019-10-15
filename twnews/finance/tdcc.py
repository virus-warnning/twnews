"""
集保中心資料蒐集模組
"""

import os
import re
import sqlite3

import pandas

import twnews.common as common
from twnews.finance import get_argument, fucking_get, get_connection
from twnews.cache import DateCache

def import_dist(csv_date='latest'):
    """
    匯入指定日期的股權分散表到資料庫
    """
    logger = common.get_logger('finance')
    csv_dir = common.get_cache_dir('tdcc')

    if csv_date == 'latest':
        max_date = ''
        for filename in os.listdir(csv_dir):
            match = re.match(r'dist-(\d{8}).csv.xz', filename)
            if match is not None:
                if max_date < match.group(1):
                    max_date = match.group(1)
        csv_date = max_date

    csv_file = '{}/dist-{}.csv.xz'.format(csv_dir, csv_date)
    iso_date = re.sub(r'(\d{4})(\d{2})(\d{2})', r'\1-\2-\3', csv_date)
    if not os.path.isfile(csv_file):
        logger.error('沒有 TDCC %s 的股權分散表檔案: %s', iso_date, csv_file)
        return

    db_conn = get_connection()
    col_names = [
        'trading_date',
        'security_id',
        'level',
        'numof_holders',
        'numof_stocks',
        'percentof_stocks'
    ]
    # Pandas 會自動偵測 extension 解壓縮, 不需要自幹
    dfrm = pandas.read_csv(csv_file, skiprows=1, header=None, names=col_names)
    # print(df.head(3))
    # print(df.tail(3))
    sql_template = '''
    INSERT INTO level%02d (
        trading_date, security_id,
        numof_holders, numof_stocks, percentof_stocks
    ) VALUES (?,?,?,?,?);
    '''
    affected = -1
    for index, row in dfrm.iterrows():
        sql = sql_template % row['level']
        try:
            db_conn.execute(sql, (
                iso_date,
                row['security_id'],
                row['numof_holders'],
                row['numof_stocks'],
                row['percentof_stocks']
            ))
            if index > 0 and index % 5000 == 0:
                logger.debug('已儲存 TDCC %s 的股權分散資料 %d 筆', iso_date, index)
            affected = index
        except sqlite3.IntegrityError:
            affected = 0
            break

    if affected > 0:
        logger.info('已匯入 TDCC %s 的股權分散資料 %d 筆', iso_date, affected)
    else:
        logger.warning('已匯入過 TDCC %s 的股權分散資料', iso_date)
    db_conn.commit()
    db_conn.close()

def rebuild_dist():
    """
    重建股權分散表資料庫
    """
    # 清除現有資料
    db_conn = get_connection()
    for level in range(1, 18):
        sql = 'DELETE FROM level%02d;' % level
        db_conn.execute(sql)
    db_conn.commit()
    db_conn.execute('VACUUM') # cannot VACUUM from within a transaction
    db_conn.close()

    # 確認可以重建的日期
    csv_dir = common.get_cache_dir('tdcc')
    date_list = []
    for filename in os.listdir(csv_dir):
        match = re.match(r'dist-(\d{8}).csv.xz', filename)
        if match is not None:
            date_list.append(match.group(1))

    # 依日期順序重建資料
    date_list.sort()
    for csv_date in date_list:
        import_dist(csv_date)

def backup_dist(refresh=False):
    """
    備份最新的股權分散表
    """
    url = 'https://smart.tdcc.com.tw/opendata/getOD.ashx'
    params = {
        'id': '1-5'
    }
    def hook(resp):
        logger = common.get_logger('finance')
        # 確認統計日期
        csv = resp.text
        dt_beg = csv.find('\n') + 1
        dt_end = csv.find(',', dt_beg)
        csv_date = csv[dt_beg:dt_end]
        date_cache = DateCache('tdcc', 'dist', 'csv')
        changed = refresh or not date_cache.has(csv_date)

        # 製作備份檔
        if changed:
            date_cache.save(csv_date, csv)
            logger.info('已更新 TDCC %s 的股權分散表', csv_date)
        else:
            logger.info('已存在 TDCC %s 的股權分散表, 不需更新', csv_date)

        return changed

    return fucking_get(hook, url, params)

def sync_dataset():
    """
    暫時寫成這個形式方便排程用
    """
    changed = backup_dist()
    if changed:
        import_dist()

    # 測試時，即使快取存在也重新匯入一次
    # backup_dist()
    # import_dist()

def main():
    """
    下載最新的股權分散表，轉檔到資料庫:
      python3 -m twnews.finance.tdcc
    使用既有的 CSV 檔案重建股權分散表資料庫:
      python3 -m twnews.finance.tdcc rebuild
    """
    action = get_argument(0, 'update')
    logger = common.get_logger('finance')

    if action == 'update':
        sync_dataset()
    elif action == 'rebuild':
        rebuild_dist()
    else:
        logger.error('無法識別的動作 %s', action)

if __name__ == '__main__':
    main()
