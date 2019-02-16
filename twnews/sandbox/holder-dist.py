import twnews.common
import requests.exceptions
from bs4 import BeautifulSoup

def get_dates():
    url = 'https://www.tdcc.com.tw/smWeb/QryStockAjax.do'
    data = {
        'REQ_OPR': 'qrySelScaDates'
    }
    logger = twnews.common.get_logger()
    session = twnews.common.get_session(False)
    dates = None
    try:
        resp = session.post(url, data=data, allow_redirects=False)
        if resp.status_code == 200:
            logger.debug('回應 200 OK')
            dates = resp.json()
            dates.sort()
        else:
            logger.warning('回應碼: %d', resp.status_code)
    except requests.exceptions.ConnectionError as ex:
        logger.error('連線失敗: %s', ex)
    return dates

def main():
    logger = twnews.common.get_logger()
    session = twnews.common.get_session(False)
    dates = get_dates()
    url = 'https://www.tdcc.com.tw/smWeb/QryStockAjax.do'

    for date in dates:
        try:
            data = {
                'scaDate': date,
                'SqlMethod': 'StockNo',
                'REQ_OPR': 'SELECT',
                'clkStockNo': '3049'
            }
            resp = session.post(url, data=data, allow_redirects=False)
            if resp.status_code == 200:
                logger.debug('回應 200 OK')
                soup = BeautifulSoup(resp.text, 'lxml')
                groups = soup.select('form > table > tr > td > table:nth-of-type(6) > tbody > tr')
                for n in range(1, 16):
                    fields = groups[n].select('td')
                    level = fields[1].text
                    noh = int(fields[2].text.replace(',', ''))
                    nos = int(fields[3].text.replace(',', ''))
                    pos = float(fields[4].text.replace(',', ''))
                    #print('族群等級: {}'.format(level))
                    #print('族群人數: {}'.format(noh))
                    #print('持股總數: {}'.format(nos))
                    #print('持股比例: {}'.format(pos))
                # break
            else:
                logger.warning('回應碼: %d', resp.status_code)
        except requests.exceptions.ConnectionError as ex:
            logger.error('連線失敗: %s', ex)

if __name__ == '__main__':
    main()
