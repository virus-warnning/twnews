import os
import re
import os.path
import requests
import subprocess

def mlstr_reduce(mlstr):
    return re.sub(r'\n\s+', ' ', mlstr)

def holder_import(csv_file):
    # 消除 csv header (sqlite3 無法跳過 header)
    nh_file = csv_file[:-4] + '-nh.csv'
    with open(csv_file, 'r') as stdin, open(nh_file, 'w') as stdout:
        subprocess.run(['tail', '-n', '+2'], stdin=stdin, stdout=stdout)

    # 匯入資料
    db_file = os.path.expanduser('~/.twnews/holder-dist/holder-dist.sqlite')
    dml = '.import {} temp_for_csv'.format(nh_file)
    subprocess.run(['sqlite3', '-separator', ',', db_file, dml])

    # 依 level 分配
    for lv in range(1, 18):
        dml = mlstr_reduce('''
            INSERT INTO level{}
            SELECT
                `stock_id`,
                substr(`date`,1,4) || '-' || substr(`date`,5,2) || '-' || substr(`date`,7,2),
                `numof_holders`,
                `numof_stocks`,
                `percentof_stocks`
                FROM temp_for_csv
                WHERE level={}
        ''').format(lv, lv)
        subprocess.run(['sqlite3', db_file, dml])

    # 刪除匯入資料
    subprocess.run(['sqlite3', db_file, 'DELETE FROM temp_for_csv'])
    subprocess.run(['sqlite3', db_file, 'VACUUM'])

    # 刪除無 header csv 檔
    os.remove(nh_file)

def holder_rebuild():
    print('重建資料庫 ...')

    # 移除 database
    db_file = os.path.expanduser('~/.twnews/holder-dist/holder-dist.sqlite')
    r = subprocess.run(['rm', '-f', db_file])

    # 產生匯入暫存表
    ddl = []
    ddl.append(mlstr_reduce('''
        CREATE TABLE temp_for_csv (
            `date` TEXT NOT NULL,
            `stock_id` TEXT NOT NULL,
            `level` INTEGER NOT NULL,
            `numof_holders` INTEGER NOT NULL,
            `numof_stocks` INTEGER NOT NULL,
            `percentof_stocks` REAL NOT NULL,
            PRIMARY KEY(`date`, `stock_id`, `level`)
        );
    '''))

    # 產生 level 表 (1-17)
    for lv in range(1, 18):
        ddl.append(mlstr_reduce('''
            CREATE TABLE level{} (
                `stock_id` TEXT NOT NULL,
                `date` TEXT NOT NULL,
                `numof_holders` INTEGER NOT NULL,
                `numof_stocks` INTEGER NOT NULL,
                `percentof_stocks` REAL NOT NULL,
                PRIMARY KEY(`date`, `stock_id`)
            );
        ''').format(lv))

    # 執行所有的 create table
    for sql in ddl:
        subprocess.run(['sqlite3', db_file, sql])

    # 重新匯入 csv
    csv_list = []
    csv_dir = os.path.expanduser('~/.twnews/holder-dist')
    for fname in os.listdir(csv_dir):
        if re.match(r'hd-\d{8}.csv', fname) is not None:
            csv_path = '{}/{}'.format(csv_dir, fname)
            csv_list.append(csv_path)
    csv_list.sort()
    for csv_file in csv_list:
        msg = '* 匯入 {}'.format(csv_file[-12:-4])
        print(msg)
        holder_import(csv_file)

    print('搞定!')

def holder_dist(refresh=False):
    # 取得最新的股權分散表完整檔
    url = 'https://smart.tdcc.com.tw/opendata/getOD.ashx?id=1-5'
    resp = requests.get(url)
    if resp.status_code == 200:
        csv_dir = os.path.expanduser('~/.twnews/holder-dist')
        if not os.path.isdir(csv_dir):
            os.makedirs(csv_dir)

        csv = resp.text
        dt_beg = csv.find('\n') + 1
        dt_end = csv.find(',', dt_beg)
        csv_date = csv[dt_beg:dt_end]
        csv_file = '{}/hd-{}.csv'.format(csv_dir, csv_date)

        save_it = False
        if refresh:
            # 強制更新
            save_it = True
        elif not os.path.isfile(csv_file):
            # 檔案不存在
            save_it = True
        else:
            # 檔案下載不完全
            sz_local = os.path.getsize(csv_file)
            sz_remote = int(resp.headers['Content-Length'])
            if sz_local < sz_remote:
                save_it = True

        if save_it:
            # 存檔
            with open(csv_file, 'wt') as csvf:
                csvf.write(csv)
            holder_import(csv_file)
        else:
            print('檔案已存在，不用儲存')
    else:
        print('無法下載')

if __name__ == '__main__':
    holder_rebuild()
