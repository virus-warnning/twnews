# pylint: disable=all

import io
import json
import os
import re
import requests
import sys
import subprocess
from datetime import datetime

import wx
import wx.xrc
from bs4 import BeautifulSoup

from twnews.cache import DateCache

class CaptchaDialog(wx.App):
    """
    驗證碼詢問 GUI
    """

    def __init__(self, captcha_stream):
        self.captcha_code = False
        self.captcha_stream = captcha_stream
        super().__init__(self)

    def OnInit(self):
        """
        載入 GUI 與 Enter 事件配置
        """
        try:
            path = os.path.realpath(os.path.dirname(__file__) + '/../res/ticksmap-captcha.xrc')
            res = wx.xrc.XmlResource(path)
            self.frame = res.LoadFrame(None, 'main_frame')

            cpi = wx.xrc.XRCCTRL(self.frame, 'captcha_image', 'wxStaticBitmap')
            im = wx.Image(self.captcha_stream)
            bm = wx.Bitmap(im)
            cpi.SetBitmap(bm)

            self.cpc = wx.xrc.XRCCTRL(self.frame, 'captcha_code', 'wxTextCtrl')
            self.cpc.Bind(wx.EVT_KEY_UP, self.OnKeyPress, id=wx.xrc.XRCID('captcha_code'))

            self.frame.Centre()
            self.frame.Show()
        except:
            return False

        return True

    def OnKeyPress(self, event):
        """
        文字輸入框按下 Enter 後送出
        """
        if event.GetKeyCode() == 13:
            self.captcha_code = self.cpc.GetValue()
            self.frame.Close()

def handle_captcha(captcha_stream):
    """
    用 wxPython 介面詢問驗證碼
    """
    app = CaptchaDialog(captcha_stream)
    app.MainLoop()
    return app.captcha_code

def load_soup(security_id, date_str):
    """
    分點進出 HTML 載入作業，含快取管理與下載流程
    TODO: 加強錯誤處理
    """

    dc = DateCache('bsr.twse', security_id, 'html')

    # 偵測快取
    if date_str != 'latest':
        if dc.has(date_str):
            soup = BeautifulSoup(dc.load(date_str), 'lxml')
            return soup
        return None

    # 無快取狀況下載分點進出網頁
    session = requests.Session()
    resp = session.get('https://bsr.twse.com.tw/bshtm/bsMenu.aspx')
    if resp.status_code != 200:
        return None

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
        return None

    # 顯示 captcha 圖片
    url = 'https://bsr.twse.com.tw/bshtm/' + captcha_image
    resp = requests.get(url)
    if resp.status_code != 200:
        return None

    captcha_stream = io.BytesIO(resp.content)
    captcha_code = handle_captcha(captcha_stream)
    if captcha_code == False:
        return None

    params['CaptchaControl1'] = captcha_code
    params['TextBox_Stkno'] = security_id

    # 送出
    resp = session.post('https://bsr.twse.com.tw/bshtm/bsMenu.aspx', data=params)
    if resp.status_code != 200:
        print('任務失敗: %d' % resp.status_code)
        return None

    soup = BeautifulSoup(resp.text, 'lxml')
    nodes = soup.select('#HyperLink_DownloadCSV')
    if len(nodes) == 0:
        print('任務失敗，沒有下載連結')
        return None

    # 下載分點進出 CSV
    # 分點進出 CSV 沒有日期
    # HTML https://bsr.twse.com.tw/bshtm/bsContent.aspx?v=t (其實任意參數都是 HTML)
    # CSV  https://bsr.twse.com.tw/bshtm/bsContent.aspx
    url = 'https://bsr.twse.com.tw/bshtm/bsContent.aspx?v=t'
    resp = session.get(url)
    if resp.status_code != 200:
        print('任務失敗，無法下載分點進出 CSV')
        return None

    # 拆解分點進出網頁，找日期欄，然後存入快取
    soup = BeautifulSoup(resp.text, 'lxml')
    root_tables = soup.select('#sp_HtmlCode > table')

    # 取日期資訊，製作快取檔
    # TODO: 簡化與容錯處理
    meta_path = 'tr > td > table > tr:nth-of-type(1) > td > table'
    meta_table = root_tables[0].select(meta_path)[0]
    date_item = meta_table.select('#receive_date')[0]
    date_str = date_item.get_text().strip().replace('/', '')
    dc.save(date_str, resp.text)
    return soup

def parse_tick_node(row):
    """
    撮合值的 td 取出 (分點 ID, 買量, 賣量)
    """
    cols = row.select('td')
    rank = cols[0].get_text().strip()
    if rank == '':
        return (False, False, False)
    loc_id = cols[1].get_text().strip()[0:4]
    bid_vol = int(cols[3].get_text().strip().replace(',', ''))
    ask_vol = int(cols[4].get_text().strip().replace(',', ''))
    return (loc_id, bid_vol, ask_vol)

def main():
    """
    分點進出表下載工具
    """
    if len(sys.argv) < 2:
        exit(1)

    if len(sys.argv) == 3:
        datestr = sys.argv[2]
    else:
        datestr = 'latest'

    print('* 載入分點進出明細', flush=True)
    soup = load_soup(sys.argv[1], datestr)
    if soup is None:
        exit(1)

    # 取最頂層的表格，數目應該是頁數的 2 倍
    # * 偶數表是 meta data 與 detail
    # * 奇數表是 pagination
    print('* 製作熱值圖 HTML', flush=True)
    root_tables = soup.select('#sp_HtmlCode > table')
    meta_path = 'tr > td > table > tr:nth-of-type(1) > td > table'
    meta_table = root_tables[0].select(meta_path)[0]
    trading_date = meta_table.select('#receive_date')[0] \
        .get_text() \
        .strip() \
        .replace('/', '-')
    (security_id, security_name) = meta_table.select('#stock_id')[0] \
        .get_text() \
        .strip() \
        .split('\xa0') # 注意這裡是 ascii 160, &nbsp; 不能使用一般空白字元切

    # 處理根層級的偶數表，蒐集撮合紀錄
    tick_nodes = []
    for even in range(0, len(root_tables), 2):
        # 偶數表中取撮合紀錄表，左表奇數次交易，右表偶數次交易
        sel = '#table2 > tr > td > table'
        ticks_table = root_tables[even].select(sel)
        even_ticks = ticks_table[0].select('tr')
        odd_ticks = ticks_table[1].select('tr')
        i = 1
        while i < len(even_ticks):
            tick_nodes.append(even_ticks[i])
            tick_nodes.append(odd_ticks[i])
            i += 1

    # 分點買賣明細加總
    volsum = {}
    for tick_node in tick_nodes:
        (loc_id, bid, ask) = parse_tick_node(tick_node)
        if loc_id != False:
            if loc_id not in volsum:
                volsum[loc_id] = { 'bid': bid, 'ask': ask }
            else:
                volsum[loc_id]['bid'] += bid
                volsum[loc_id]['ask'] += ask

    # 置入 geojson
    path = os.path.realpath(os.path.dirname(__file__) + '/../res/ticksmap-locations.geojson')
    with open(path, 'r') as ffc:
        fc = json.load(ffc)
        filtered_features = []
        for feature in fc['features']:
            loc_id = feature['properties']['id']
            if loc_id in volsum:
                feature['properties']['bid'] = volsum[loc_id]['bid']
                feature['properties']['ask'] = volsum[loc_id]['ask']
                filtered_features.append(feature)
        fc['features'] = filtered_features

    # 置入 heatmap 模板
    path = os.path.realpath(os.path.dirname(__file__) + '/../res/ticksmap-template.html')
    with open(path, 'r') as tplf:
        leaflet = os.path.expanduser('~/Desktop/ticksmap-{}-{}.html'.format(
            security_id,
            trading_date.replace('-', '')
        ))
        screenshot = os.path.expanduser('~/Desktop/ticksmap-{}-{}.png'.format(
            security_id,
            trading_date.replace('-', '')
        ))

        # 將分點進出資料套版，生成 leaflet 熱值圖網頁
        fcstr = json.dumps(fc)
        template = tplf.read()
        template = template.replace('__FEATURE_COLLECTION__', fcstr, 1)
        template = template.replace('__SECURITY_ID__', security_id, 1)
        template = template.replace('__SECURITY_NAME__', security_name, 1)
        html = template.replace('__DATE__', trading_date, 1)
        with open(leaflet, 'w') as out:
            out.write(html)

        # 用 headless browser 將 leaflet 網頁轉換成圖檔
        # TODO: 自動偵測瀏覽器路徑
        #   * Windows 使用者 Chrome
        #   * Windows 系統 Chrome
        #   * Windows Brave
        #   * Chrome for MacOS
        chrome_bin = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'
        chrome_bin = r'C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe' # ok!

        # 相關參數參考 https://peter.sh/experiments/chromium-command-line-switches/
        cmd = [
            chrome_bin,
            '--headless',
            '--hide-scrollbars',
            '--window-size=1000x850',
            '--screenshot=' + screenshot,
            leaflet
        ]
        print('* 製作熱值圖 PNG', flush=True)
        subprocess.run(cmd, stderr=subprocess.DEVNULL)

        # 用預設軟體開啟圖檔
        #         MacOS: open
        # Windows + cmd: start
        #  Windows + PS: start-process -file
        print(os.path.realpath(screenshot))
        cmd = [ 'powershell', 'start-process', '-file', os.path.realpath(screenshot) ]
        # cmd = [ 'cmd', 'start', os.path.realpath(screenshot) ]
        print(cmd)
        subprocess.run(cmd)

if __name__ == '__main__':
    main()
