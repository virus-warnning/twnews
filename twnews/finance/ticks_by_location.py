import io
import json
import os
import re
import requests
import sys
import tkinter as tk

from PIL import ImageTk, Image
from bs4 import BeautifulSoup

def handle_captcha(captcha_stream):
    """
    預設 captcha 處理程序，使用 tkinter 互動式詢問
    注意!! 會使用 Tesseract, OpenCV 的人請自行低調發揮，並且節制使用，避免自動化作業失效
    """
    root = tk.Tk()
    root.title('請輸入驗證碼')
    root.geometry('400x200')

    bm = ImageTk.PhotoImage(Image.open(captcha_stream))
    lbl_captcha = tk.Label(root, image=bm)
    lbl_captcha.pack()

    txt_captcha = tk.Text(
        root,
        background='#ffffff',
        font=('Arial', 12),
        border=1,
        width=50,
        height=1.5
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

def main(captcha_hook=handle_captcha):
    """ 分點進出表下載工具 """
    if len(sys.argv) < 2:
        exit(1)

    security_id = sys.argv[1]
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
    resp = session.get('https://bsr.twse.com.tw/bshtm/bsContent.aspx')
    if resp.status_code != 200:
        print('任務失敗，無法下載分點進出 CSV')
        exit(1)

    path = '%s.csv' % security_id
    with open(path, 'w') as f:
        f.write(resp.text)
        print('已下載 %s 的分點進出表 ... %s' % (security_id, path))

if __name__ == '__main__':
    main()
