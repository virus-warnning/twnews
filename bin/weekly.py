#!/usr/bin/env python3

import json
import os
import os.path

import smtplib
from email.header import Header
from email.mime.text import MIMEText

conf = None
CONF_PATH = os.path.expanduser('~/.twnews/weekly.json')
if os.path.isfile(CONF_PATH):
    with open(CONF_PATH, 'r') as conf_file:
        conf = json.load(conf_file)

if conf is None:
    print('Cannot load "{}".'.format(CONF_PATH))
    exit(1)

working_dir = os.path.realpath(os.path.dirname(__file__) + '/..')
cmd = 'cd {} && python3 -m unittest discover -v 2>&1 1>/dev/null'.format(working_dir)
pipe = os.popen(cmd, 'r')
detail = pipe.read()
ret = pipe.close()

if ret is None:
    subject = '[twnews] 每週單元測試成功'
    contents = '''
        <span style="color:#00f;">每週單元測試成功</span>
        <br><br>
        <pre style="border:1px solid #aaa; background:#eee; padding:10px;">
        {}
        </pre>
        '''.format(detail)
else:
    subject = '[twnews] 每週單元測試失敗'
    contents = '''
        <span style="color:#f00;">每週單元測試失敗 ({})</span>
        <br><br>
        <pre style="border:1px solid #aaa; background:#eee; padding:10px;">
        {}
        </pre>
        '''.format(ret, detail)

msg = MIMEText(contents, 'html', 'utf-8')
msg['Subject'] = Header(subject)
msg['From'] = '{} <{}>'.format(Header(conf['from_name']).encode(), conf['from_mail'])
msg['To'] = '{} <{}>'.format(Header(conf['to_name']).encode(), conf['to_mail'])
smtp_data = msg.as_string()

try:
    server = smtplib.SMTP(conf['smtp_host'], conf['smtp_port'])
    server.set_debuglevel(1)
    server.starttls()
    server.login(conf['smtp_user'], conf['smtp_pass'])
    server.sendmail(conf['from_mail'], conf['to_mail'], smtp_data)
    server.close()
except Exception as ex:
    print('Something went wrong.', ex)
