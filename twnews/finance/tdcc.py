import logging
import os
import os.path
import re
import requests
import subprocess

import pandas

import twnews.common as common
import twnews.finance.db as db

def import_dist(csv_date):
    """
    匯入指定日期的股權分散表到資料庫
    """
    logger = common.get_logger('finance')
    csv_path = os.path.expanduser('~/.twnews/cache/tdcc/dist-%s.csv' % csv_date)
    if not os.path.isfile(csv_path):
        logger.error('沒有這個日期的股權分散表檔案: %s', csv_path)
        return

    db_conn = db.get_connection(True)
    col_names = [
        'trading_date',
        'security_id',
        'level',
        'numof_holders',
        'numof_stocks',
        'percentof_stocks'
    ]
    df = pandas.read_csv(csv_path, skiprows=1, header=None, names=col_names)
    # print(df.head(3))
    # print(df.tail(3))
    sql_template = '''
    INSERT INTO level%02d (
        trading_date, security_id,
        numof_holders, numof_stocks, percentof_stocks
    ) VALUES (?,?,?,?,?);
    '''
    for index, row in df.iterrows():
        sql = sql_template % row['level']
        db_conn.execute(sql, (
            row['trading_date'],
            row['security_id'],
            row['numof_holders'],
            row['numof_stocks'],
            row['percentof_stocks']
        ))
        if index > 0 and index % 5000 == 0:
            msg = '已處理 %d 筆' % (index)
            logger.debug(msg)
    db_conn.commit()
    db_conn.close()

def rebuild_dist():
    """
    重建股權分散表資料庫
    """
    pass

def backup_dist(refresh=False):
    """
    備份最新的股權分散表
    """
    logger = common.get_logger('finance')
    url = 'https://smart.tdcc.com.tw/opendata/getOD.ashx?id=1-5'
    resp = requests.get(url)
    if resp.status_code == 200:
        # 確認統計日期
        csv = resp.text
        dt_beg = csv.find('\n') + 1
        dt_end = csv.find(',', dt_beg)
        csv_date = csv[dt_beg:dt_end]
        csv_dir = os.path.expanduser('~/.twnews/cache/tdcc')
        if not os.path.isdir(csv_dir):
            os.makedirs(csv_dir)
        csv_file = '{}/dist-{}.csv'.format(csv_dir, csv_date)

        # 製作備份檔
        with open(csv_file, 'wt') as csvf:
            csvf.write(csv)
            logger.debug('已更新股權分散表: %s', csv_date)
    else:
        logger.error('無法更新股權分散表')

if __name__ == '__main__':
    # backup_dist()
    # import_dist('20190531')
    pass
