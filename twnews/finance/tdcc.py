import logging
import os
import os.path
import re
import requests
import subprocess
import sys

import busm
import pandas

import twnews.common as common
import twnews.finance.db as db

def import_dist(csv_date='latest'):
    """
    匯入指定日期的股權分散表到資料庫
    """
    logger = common.get_logger('finance')

    if csv_date == 'latest':
        max_date = ''
        dir = os.path.expanduser('~/.twnews/cache/tdcc')
        for filename in os.listdir(dir):
            match = re.match(r'dist-(\d{8}).csv', filename)
            if match is not None:
                if max_date < match.group(1):
                    max_date = match.group(1)
        csv_date = max_date

    iso_date = re.sub(r'(\d{4})(\d{2})(\d{2})', r'\1-\2-\3', csv_date)
    csv_path = os.path.expanduser('~/.twnews/cache/tdcc/dist-%s.csv' % csv_date)
    if not os.path.isfile(csv_path):
        logger.error('沒有這個日期的股權分散表檔案: %s', csv_path)
        return

    db_conn = db.get_connection()
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
            iso_date,
            row['security_id'],
            row['numof_holders'],
            row['numof_stocks'],
            row['percentof_stocks']
        ))
        if index > 0 and index % 5000 == 0:
            msg = '已儲存 %s 的 %d 筆股權分散資料' % (iso_date, index)
            logger.debug(msg)
    db_conn.commit()
    db_conn.close()

def rebuild_dist():
    """
    重建股權分散表資料庫
    """
    # 清除現有資料
    db_conn = db.get_connection()
    for level in range(1, 18):
        sql = 'DELETE FROM level%02d;' % level
        db_conn.execute(sql)
    db_conn.commit()
    db_conn.execute('VACUUM') # cannot VACUUM from within a transaction
    db_conn.close()

    # 確認可以重建的日期
    dir = os.path.expanduser('~/.twnews/cache/tdcc')
    date_list = []
    for filename in os.listdir(dir):
        match = re.match(r'dist-(\d{8}).csv', filename)
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
    changed = False
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

        if refresh:
            changed = True
        elif not os.path.isfile(csv_file):
            changed = True
        else:
            sz_local = os.path.getsize(csv_file)
            sz_remote = int(resp.headers['Content-Length'])
            if sz_local != sz_remote:
                changed = True

        # 製作備份檔
        if changed:
            with open(csv_file, 'wt') as csvf:
                csvf.write(csv)
                logger.debug('已更新股權分散表: %s', csv_date)
        else:
            logger.debug('已存在股權分散表: %s, 不需更新', csv_date)
    else:
        logger.error('無法更新股權分散表')

    return changed

def get_action():
    if len(sys.argv) > 1:
        return sys.argv[1]
    return 'update'

@busm.through_telegram
def main():
    """
    下載最新的股權分散表，轉檔到資料庫:
      python3 -m twnews.finance.tdcc
    使用既有的 CSV 檔案重建股權分散表資料庫:
      python3 -m twnews.finance.tdcc rebuild
    """
    action = get_action()
    logger = common.get_logger('finance')

    if action == 'update':
        changed = backup_dist()
        if changed:
            import_dist()
    elif action == 'rebuild':
        rebuild_dist()
    else:
        logger.error('無法識別的動作 %s', action)

if __name__ == '__main__':
    main()
