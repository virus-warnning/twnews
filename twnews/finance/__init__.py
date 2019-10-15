import os
import sqlite3
import sys

from requests.exceptions import RequestException

import twnews.common as common
from twnews.exceptions import NetworkException

DDL_LIST = [
    # 三大法人
    '''
    CREATE TABLE IF NOT EXISTS `institution` (
        trading_date TEXT,
        security_id TEXT,
        security_name TEXT,
        foreign_trend INTEGER,
        stic_trend INTEGER,
        dealer_trend INTEGER,
        PRIMARY KEY (`trading_date`, `security_id`)
    );
    ''',
    # 融資融券
    '''
    CREATE TABLE IF NOT EXISTS `margin` (
        trading_date TEXT,
        security_id TEXT,
        security_name TEXT,
        buying_balance INTEGER,
        selling_balance INTEGER,
        PRIMARY KEY (`trading_date`, `security_id`)
    );
    ''',
    # 借券賣出
    '''
    CREATE TABLE IF NOT EXISTS `short_sell` (
        trading_date TEXT,
        security_id TEXT,
        security_name TEXT,
        borrowed INTEGER,
        selled INTEGER,
        PRIMARY KEY (`trading_date`, `security_id`)
    );
    ''',
    # 鉅額交易
    '''
    CREATE TABLE IF NOT EXISTS `block` (
        trading_date TEXT,
        security_id TEXT,
        security_name TEXT,
        tick_rank INTEGER,
        tick_type TEXT,
        close REAL,
        volume INTEGER,
        total INTEGER,
        PRIMARY KEY (`trading_date`, `security_id`, `tick_rank`)
    );
    ''',
    # ETF 淨值折溢價
    '''
    CREATE TABLE IF NOT EXISTS `etf_offset` (
        trading_date TEXT,
        security_id TEXT,
        security_name TEXT,
        close REAL,
        net REAL,
        offset REAL,
        PRIMARY KEY (`trading_date`, `security_id`)
    );
    '''
]

# 股權分散
DDL_DIST = '''
CREATE TABLE IF NOT EXISTS level{:02d} (
    `trading_date` TEXT NOT NULL,
    `security_id` TEXT NOT NULL,
    `numof_holders` INTEGER NOT NULL,
    `numof_stocks` INTEGER NOT NULL,
    `percentof_stocks` REAL NOT NULL,
    PRIMARY KEY(`trading_date`, `security_id`)
);
'''

REPEAT_LIMIT = 3
REPEAT_INTERVAL = 5

def get_connection(rebuild=False):
    """
    自動產生財經資料庫與取得連線
    """
    db_dir = os.path.expanduser('~/.twnews/db')
    if not os.path.isdir(db_dir):
        os.makedirs(db_dir)

    db_path = db_dir + '/finance.sqlite'
    if rebuild:
        os.remove(db_path)
    db_ready = os.path.isfile(db_path)

    db_conn = sqlite3.connect(db_path)
    if not db_ready:
        # 產生籌碼資料表
        for ddl in DDL_LIST:
            db_conn.execute(ddl)

        # 產生各級股權分散表, 有 1~17 級
        for level in range(1,18):
            ddl = DDL_DIST.format(level)
            db_conn.execute(ddl)

        db_conn.commit()

    return db_conn

def get_argument(index, default=''):
    """
    取得 shell 參數, 或使用預設值
    """
    if len(sys.argv) <= index:
        return default
    return sys.argv[index]

def fucking_get(hook, url, params):
    """
    共用 HTTP GET 處理邏輯
    """
    session = common.get_session(False)
    try:
        resp = session.get(url, params=params)
        if resp.status_code == 200:
            return hook(resp)
        else:
            msg = 'Got HTTP error, status code: %d' % resp.status_code
            raise NetworkException(msg)
    except RequestException as ex:
        msg = 'Cannot get response, exception type: %s' % type(ex).__name__
        raise NetworkException(msg)

    return dataset
