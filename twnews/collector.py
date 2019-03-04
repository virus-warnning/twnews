import os
import re
import os.path
import requests
import subprocess

def holder_dist(refresh=False):
    """
    取得最新的股權分散表完整檔
    - 換行符: '\r\n'
    - 分隔符: ','
    """
    url = 'https://smart.tdcc.com.tw/opendata/getOD.ashx?id=1-5'
    resp = requests.get(url)
    if resp.status_code == 200:
        csv_dir = os.path.expanduser('~') + '/.twnews/holder-dist'
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

            # 匯入:
            # 1. 確認 table 存在, 一季一個 table
            # 2. 消除 csv header
            # 3. 匯入 csv
            # 4. 移除暫存檔
            y = csv_date[0:4]
            q = str(int(csv_date[4:6]) // 4 + 1)
            qtable = 'dist_{}q{}'.format(y, q)
            nh_file = '{}/hd-{}-nh.csv'.format(csv_dir, csv_date)
            sql1 = re.sub('\n\s+', '', '''
            CREATE TABLE IF NOT EXISTS "{}" (
                `date` TEXT NOT NULL,
            	`stock_id` TEXT NOT NULL,
            	`level` INTEGER NOT NULL,
            	`numof_holders` INTEGER NOT NULL,
            	`numof_stocks` INTEGER NOT NULL,
            	`percentof_stocks` REAL NOT NULL,
            	PRIMARY KEY(`date`,`stock_id`,`level`)
            );
            '''.format(qtable))
            sql2 = '.import {} {}'.format(nh_file, qtable)

            subprocess.run(['sqlite3', 'holder-dist.sqlite', sql1], cwd=csv_dir)
            with open(csv_file, 'r') as stdin, open(nh_file, 'w') as stdout:
                subprocess.run(['tail', '-n', '+2'], stdin=stdin, stdout=stdout)
            subprocess.run(['sqlite3', '-separator', ',', 'holder-dist.sqlite', sql2], cwd=csv_dir)
            os.remove(nh_file)
        else:
            print('檔案已存在，不用儲存')
    else:
        print('無法下載')

if __name__ == '__main__':
    holder_dist()
