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

if __name__ == '__main__':
    main()
