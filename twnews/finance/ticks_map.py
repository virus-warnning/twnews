# pylint: disable=all

import io
import json
import os
import re
import requests
import sys
import tkinter as tk
from datetime import datetime

from PIL import ImageTk, Image
from bs4 import BeautifulSoup

from twnews.cache import DateCache

def handle_captcha(captcha_stream):
    """
    TODO: 改用 wxPython 設計
    """
    root = tk.Tk()
    root.title('請輸入驗證碼')
    root.geometry('250x300')

    bm = ImageTk.PhotoImage(Image.open(captcha_stream))
    lbl_captcha = tk.Label(root, image=bm)
    lbl_captcha.pack()

    txt_captcha = tk.Text(
        root,
        background='#ffffff',
        font=('Arial', 12),
        bd=1,
        relief='ridge',
        width=200,
        height=30
    )
    txt_captcha.config(wrap='none')
    txt_captcha.pack()

    code = ''
    def enter_pressed(evt):
        nonlocal code
        code = txt_captcha.get('1.0', 'end-1c').strip()
        root.destroy()

    txt_captcha.bind('<Return>', enter_pressed)

    root.mainloop()
    return code

def load_soup(security_id, date_str):
    """
    分點進出 HTML 載入作業，含快取管理與下載流程
    """

    # 自動轉換今天的日期字串
    today_str = datetime.now().strftime('%Y%m%d')
    if date_str == 'today':
        date_str = today_str

    # 偵測快取
    dc = DateCache('bsr.twse', security_id, 'html')
    if dc.has(date_str):
        soup = BeautifulSoup(dc.load(date_str), 'lxml')
        return soup

    # 歷史資料不在快取內，不下載網頁
    if today_str != date_str:
        exit(1)

    # 無快取狀況下載分點進出網頁
    session = requests.Session()
    resp = session.get('https://bsr.twse.com.tw/bshtm/bsMenu.aspx')
    if resp.status_code != 200:
        exit(1)

    soup = BeautifulSoup(resp.text, 'lxml')
    nodes = soup.select('form input')
    params = {}
    for node in nodes:
        name = node.attrs['name']

        # 忽略鉅額交易的 radio button
        if name in ('RadioButton_Excd', 'Button_Reset'):
            continue

        if 'value' in node.attrs:
            params[node.attrs['name']] = node.attrs['value']
        else:
            params[node.attrs['name']] = ''

    # 找 captcha 圖片
    captcha_image = soup.select('#Panel_bshtm img')[0]['src']
    m = re.search(r'guid=(.+)', captcha_image)
    if m is None:
        exit(1)

    # 顯示 captcha 圖片
    url = 'https://bsr.twse.com.tw/bshtm/' + captcha_image
    resp = requests.get(url)
    if resp.status_code != 200:
        exit(1)

    captcha_stream = io.BytesIO(resp.content)
    params['CaptchaControl1'] = handle_captcha(captcha_stream)
    params['TextBox_Stkno'] = security_id

    # 送出
    resp = session.post('https://bsr.twse.com.tw/bshtm/bsMenu.aspx', data=params)
    if resp.status_code != 200:
        print('任務失敗: %d' % resp.status_code)
        exit(1)

    soup = BeautifulSoup(resp.text, 'lxml')
    nodes = soup.select('#HyperLink_DownloadCSV')
    if len(nodes) == 0:
        print('任務失敗，沒有下載連結')
        exit(1)

    # 下載分點進出 CSV
    # 分點進出 CSV 沒有日期
    # HTML https://bsr.twse.com.tw/bshtm/bsContent.aspx?v=t (其實任意參數都是 HTML)
    # CSV  https://bsr.twse.com.tw/bshtm/bsContent.aspx
    url = 'https://bsr.twse.com.tw/bshtm/bsContent.aspx?v=t'
    resp = session.get(url)
    if resp.status_code != 200:
        print('任務失敗，無法下載分點進出 CSV')
        exit(1)

    # 拆解分點進出網頁，找日期欄，然後存入快取
    soup = BeautifulSoup(resp.text, 'lxml')
    root_tables = soup.select('#sp_HtmlCode > table')

    # 取日期資訊，製作快取檔
    # TODO: 簡化與容錯處理
    meta_path = 'tr > td > table > tr:nth-of-type(1) > td > table'
    meta_table = root_tables[0].select(meta_path)[0]
    date_item = meta_table.select('#receive_date')[0]
    date_str = date_item.get_text().strip().replace('/', '')
    if date_str != today_str:
        exit(1)

    dc.save(date_str, resp.text)
    return soup

def main(captcha_hook=handle_captcha):
    """
    分點進出表下載工具
    TODO: 改抓網頁取得完整資訊
    """
    if len(sys.argv) < 2:
        exit(1)

    soup = load_soup(sys.argv[1], 'today')

    # 取最頂層的表格，數目應該是頁數的 2 倍
    # * 偶數表是 meta data 與 detail
    # * 奇數表是 pagination
    root_tables = soup.select('#sp_HtmlCode > table')

    # 處理偶數表
    for even in range(0, len(root_tables), 2):
        # 撮合紀錄表，左表奇數次交易，右表偶數次交易
        page_table = root_tables[even]
        sel = '#table2 > tr > td > table'
        ticks_table = page_table.select(sel)
        # TODO: 分析資料
        print(len(ticks_table))
        break

if __name__ == '__main__':
    main()
