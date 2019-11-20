# pylint: disable=all

import os
import sys
import pandas
import json

loc_idx = {}
statistics = []

def handle_tick(tick):
    global statistics

    if not isinstance(tick['loc'], str):
        return

    loc_id = tick['loc'][0:4]
    loc_name = tick['loc'][4:]
    if loc_id not in loc_idx:
        loc_idx[loc_id] = len(statistics)
        statistics.append({
            'id': loc_id,
            'name': loc_name,
            'bid_vol': 0,
            'ask_vol': 0,
            'bid_amount': 0,
            'ask_amount': 0
        })

    if isinstance(tick['bid'], int) and tick['bid'] > 0:
        statistics[loc_idx[loc_id]]['bid_vol'] += tick['bid']
        statistics[loc_idx[loc_id]]['bid_amount'] += tick['bid'] * tick['price']

    if isinstance(tick['ask'], int) and tick['ask'] > 0:
        statistics[loc_idx[loc_id]]['ask_vol'] += tick['ask']
        statistics[loc_idx[loc_id]]['ask_amount'] += tick['ask'] * tick['price']

def main():
    fpath = os.path.realpath(sys.argv[1])
    if not os.path.isfile(fpath):
        exit(1)

    dfrm = pandas.read_csv(fpath, skiprows=2)
    for index, row in dfrm.iterrows():
        tick_odd = {
            'loc': row['券商'],
            'price': row['價格'],
            'bid': row['買進股數'],
            'ask': row['賣出股數']
        }
        handle_tick(tick_odd)
        tick_even = {
            'loc': row['券商.1'],
            'price': row['價格.1'],
            'bid': row['買進股數.1'],
            'ask': row['賣出股數.1']
        }
        handle_tick(tick_even)

    top_len = 10

    statistics.sort(key=lambda s: s['bid_amount'], reverse=True)
    print(' ' * 15, '買進分點 Top %d' % top_len)
    print('-' * 50)
    top_bid = statistics[0:top_len]
    for s in top_bid:
        avg = s['bid_amount'] / s['bid_vol']
        print('%8d  %12.2f  %3.2f  %s %s' % (s['bid_vol'], s['bid_amount'], avg, s['id'], s['name']))

    print('')

    statistics.sort(key=lambda s: s['ask_amount'], reverse=True)
    print(' ' * 15, '賣出分點 Top %d' % top_len)
    print('-' * 50)
    top_ask = statistics[0:top_len]
    for s in top_ask:
        avg = s['ask_amount'] / s['ask_vol']
        print('%8d  %12.2f  %3.2f  %s %s' % (s['ask_vol'], s['ask_amount'], avg, s['id'], s['name']))

    print('')

    get_name = lambda s: s['name']
    intersections = set(map(get_name, top_bid)) & set(map(get_name, top_ask))
    print('造市分點:', ', '.join(intersections))

def heatmap():
    fpath = os.path.realpath(sys.argv[1])
    if not os.path.isfile(fpath):
        exit(1)

    # 統計買賣狀況
    stat = {}
    dfrm = pandas.read_csv(fpath, skiprows=2)
    for index, row in dfrm.iterrows():
        loc, bid, ask = (row['券商'][0:4], int(row['買進股數']), int(row['賣出股數']))
        if loc in stat:
            stat[loc]['bid'] += bid
            stat[loc]['ask'] += ask
        else:
            stat[loc] = { 'bid': bid, 'ask': ask }
        if isinstance(row['券商.1'], str):
            loc, bid, ask = (row['券商.1'][0:4], int(row['買進股數.1']), int(row['賣出股數.1']))
            if loc in stat:
                stat[loc]['bid'] += bid
                stat[loc]['ask'] += ask
            else:
                stat[loc] = { 'bid': bid, 'ask': ask }

    # 轉換 geojson 格式
    fc = None
    path = os.path.realpath(os.path.dirname(__file__) + '/../res/security_firms.geojson')
    with open(path, 'r') as ffc:
        fc = json.load(ffc)
        fcnt = len(fc['features'])
        filtered_features = []
        for i in range(fcnt):
            feature = fc['features'][i]
            loc = feature['properties']['id']
            if loc in stat:
                feature['properties']['bid'] = stat[loc]['bid']
                feature['properties']['ask'] = stat[loc]['ask']
                filtered_features.append(feature)
        fc['features'] = filtered_features

    if fc is None:
        exit(1)

    # 生成熱區圖網頁
    path = os.path.realpath(os.path.dirname(__file__) + '/../res/heatmap-template.html')
    with open(path, 'r') as tplf:
        fcstr = json.dumps(fc)
        template = tplf.read()
        template = template.replace('__FEATURE_COLLECTION__', fcstr, 1)
        template = template.replace('__SECURITY_ID__', '9955', 1)
        template = template.replace('__SECURITY_NAME__', '佳龍', 1)
        html = template.replace('__DATE__', '2019-11-12', 1)
        with open('heatmap.html', 'w') as out:
            out.write(html)

if __name__ == '__main__':
    # main()
    heatmap()
