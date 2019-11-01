"""
券商與分公司資訊與門牌定位

已知問題:
* 有筆紀錄無法成功定位
  1. 8770 大鼎
  2. 1115 台灣企銀-太平
  3. 779m 國票-中港
  4. 9636 富邦-中壢
  這 4 筆用工人智慧取經緯度，其餘自動化
* TGOS 服務查詢 500 次的時候，會拒絕之後的 request
  可能需要重置 requests session，現階段程式無法一口氣完成 9xx 筆定位
"""

import os
import re
import json
import sqlite3
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Float, create_engine
from pyproj import Transformer

Base = declarative_base()

class TradingLocation(Base):
    """
    分點資料
    """
    __tablename__ = 'trading_locs'
    id = Column(String(4), primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(100), nullable=False)
    phone = Column(String(100), nullable=False)
    parent = Column(String(100), nullable=False, default=-1)
    lat = Column(Float(), nullable=False, default=0.0)
    lng = Column(Float(), nullable=False, default=0.0)
    started_at = Column(String(100), nullable=False)

def date_conv(hw_date):
    """
    民國日期轉西元日期 ISO 格式
    """
    patterns = [
        r'^(\d{2,3})(\d{2})(\d{2})$',
        r'^(\d{2,3})/(\d{2})/(\d{2})$',
    ]

    ad_date = None
    for pattern in patterns:
        m = re.match(pattern, hw_date)
        if not m:
            continue
        d_yy = int(m[1]) + 1911
        d_mm = int(m[2])
        d_dd = int(m[3])
        ad_date = '%4d-%02d-%02d' % (d_yy, d_mm, d_dd)
        break

    return ad_date

def visit_branch(session, parent_id):
    """
    爬分公司
    """
    url = 'https://www.twse.com.tw/brokerService/brokerServiceAudit'
    params = {
        'stkNo': parent_id,
        'showType': 'list',
        'focus': 6
    }
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        exit(1)

    branches = []
    soup = BeautifulSoup(resp.text, 'lxml')
    table = soup.select('#table6 > table')[0]
    for row in table.select('tr'):
        cols = row.select('td')
        if not cols:
            continue
        if cols[0].has_attr('colspan'):
            break

        loc = TradingLocation()
        loc.id = cols[0].text.strip()
        loc.name = cols[1].text.strip()
        loc.address = cols[3].text.strip()
        loc.phone = cols[4].text.strip()
        loc.started_at = date_conv(cols[2].text.strip())
        loc.parent = parent_id
        session.merge(loc)

def visit_parent(session):
    """
    爬母公司
    """
    resp = requests.get('https://www.twse.com.tw/zh/brokerService/brokerServiceAudit')
    if resp.status_code != 200:
        exit(1)

    db_path = os.path.expanduser('~/.twnews/db/finance.sqlite')
    db_conn = sqlite3.connect(db_path)
    soup = BeautifulSoup(resp.text, 'lxml')
    table = soup.select('#table2 > table')[0]
    for row in table.select('tr'):
        cols = row.select('td')
        if not cols:
            continue

        loc = TradingLocation()
        loc.id = cols[0].text.strip()
        loc.name = cols[1].text.strip()
        loc.address = cols[3].text.strip()
        loc.phone = cols[4].text.strip()
        loc.started_at = date_conv(cols[2].text.strip())
        session.merge(loc)

        visit_branch(session, loc.id)

def geocode_single(address, req_session, sid, transformer):
    """
    處理單筆地址定位
    """
    # 騙到 EPSG:3826 座標
    time.sleep(0.5)
    url = 'https://map.tgos.tw/TGOSCloud/Generic/Project/GHTGOSViewer_Map.ashx'
    params = {
        'method': 'querymoiaddr',
        'address': address,
        'useoddeven': False,
        'sid': sid
    }
    resp = req_session.post(url, data=params)
    if resp.status_code != 200:
        # print(resp.status_code)
        return (0.0, 0.0)

    try:
        respjson = json.loads(resp.text)
    except:
        return (0.0, 0.0)

    if not respjson['AddressList']:
        # print(json.dumps(respjson, indent=2))
        return (0.0, 0.0)

    result = json.loads(resp.text)['AddressList'][0]
    point = transformer.transform(result['X'], result['Y'])
    return point

def geocode(orm_session):
    # 座標轉換器，只需要做一次 (需要 pyproj)
    transformer = Transformer.from_crs("EPSG:3826", "EPSG:4326")

    # 做個給掰的 session
    # 目前發現偽裝真實用戶只能查 500 個地址，可能需要重置連線才能處理更多資料
    req_session = requests.Session()
    req_session.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) ' \
            + 'AppleWebKit/537.36 (KHTML, like Gecko) ' \
            + 'Chrome/46.0.2490.76 Mobile Safari/537.36'
    })

    # 騙到 pagekey, 只需要做一次
    url = 'https://map.tgos.tw/TGOSCloud/Web/Map/TGOSViewer_Map.aspx'
    resp = req_session.get(url)
    if resp.status_code != 200:
        print(resp.status_code)
        exit(1)

    match = re.search(r"sircPAGEKEY\s?='([^\']+)';", resp.text)
    if not match:
        print('無法取得 pagekey')
        exit(1)

    pagekey = urllib.parse.unquote(match[1])
    # print(pagekey)

    # 加上這一行其他的 request 才不會被擋掉
    req_session.headers['Referer'] = url

    # 騙到 sid, 只需要做一次
    url = 'https://map.tgos.tw/TGOSCloud/Generic/Utility/UG_Handler.ashx'
    params = {
        'method': 'GetSessionID',
        'pagekey': pagekey
    }
    resp = req_session.post(url, params=params)
    if resp.status_code != 200:
        print(resp.status_code)
        exit(1)

    fields = json.loads(resp.text)
    sid = fields['id']
    # print(sid)

    q = orm_session.query(TradingLocation).filter(
        TradingLocation.lat == 0.0,
        TradingLocation.lng == 0.0
    )
    for loc in q.all():
        slices = loc.address.split('、')
        m = re.search('^.+號', slices[0])
        if m:
            fixed_address = m[0]
        else:
            fixed_address = slices[0] + '號'
        (lat, lng) = geocode_single(fixed_address, req_session, sid, transformer)
        print(loc.id, fixed_address, lat, lng)
        loc.lat = lat
        loc.lng = lng
        orm_session.merge(loc)
        #orm_session.commit()
    #address = '台北市114內湖區石潭路151號'
    #geocode_single(address, req_session, sid, transformer)

def main():
    db_repl = 'sqlite:///' + os.path.expanduser('~/.twnews/db/finance.sqlite')
    engine = create_engine(db_repl, echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    # 爬券商分點
    # visit_parent(session)
    # 券商分點做地理定位
    geocode(session)
    session.commit()

if __name__ == '__main__':
    main()
