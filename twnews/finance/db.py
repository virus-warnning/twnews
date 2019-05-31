import os
import os.path
import sqlite3

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
    CREATE TABLE IF NOT EXISTS `short_selling` (
        trading_date TEXT,
        security_id TEXT,
        security_name TEXT,
        balance INTEGER,
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
        for ddl in DDL_LIST:
            db_conn.execute(ddl)
        db_conn.commit()

    return db_conn
