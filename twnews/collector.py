import os
import os.path
import requests

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
            with open(csv_file, 'wt') as csvf:
                csvf.write(csv)
        else:
            print('檔案已存在，不用儲存')
    else:
        print('無法下載')

if __name__ == '__main__':
    holder_dist()
