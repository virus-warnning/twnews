import os
import re
import os.path
import requests
import subprocess

def holder_import(csv_file):
    y = csv_file[-12:-8]
    q = (int(csv_file[-8:-6]) // 4) + 1
    qtable = 'hd{}q{}'.format(y, q)
    ddl = re.sub(r'\n\s+', ' ', '''
        CREATE TABLE IF NOT EXISTS `{}` (
            `date` TEXT NOT NULL,
            `stock_id` TEXT NOT NULL,
            `level` INTEGER NOT NULL,
            `numof_holders` INTEGER NOT NULL,
            `numof_stocks` INTEGER NOT NULL,
            `percentof_stocks` REAL NOT NULL,
            PRIMARY KEY(`date`, `stock_id`, `level`)
        );
    ''').format(qtable)

    nh_file = csv_file[:-4] + '-nh.csv'
    dml = '.import {} {}'.format(nh_file, qtable)

    with open(csv_file, 'r') as stdin, open(nh_file, 'w') as stdout:
        subprocess.run(['tail', '-n', '+2'], stdin=stdin, stdout=stdout)

    db_file = os.path.expanduser('~/.twnews/holder-dist/holder-dist.sqlite')
    subprocess.run(['rm', '-f', db_file])
    subprocess.run(['sqlite3', db_file, ddl])
    subprocess.run(['sqlite3', '-separator', ',', db_file, dml])
    os.remove(nh_file)

def holder_rebuild():
    csv_list = []
    csv_dir = os.path.expanduser('~/.twnews/holder-dist')
    for fname in os.listdir(csv_dir):
        if re.match(r'hd-\d{8}.csv', fname) is not None:
            csv_path = '{}/{}'.format(csv_dir, fname)
            csv_list.append(csv_path)

    print('重建資料庫 ...')
    for csv_file in csv_list:
        msg = '* {}'.format(csv_file[-12:-4])
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
