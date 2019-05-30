import requests

def main():
    """
    {
      "a1": [
        {
          "msgArray": [
            {
              "a": "", 代碼
              "b": "", 名稱
              "c": "", 發行量
              "d": "", 與前日發行量變化
              "e": "", 成交價
              "f": "", 淨值
              "g": "", 折溢價率
              "h": "", 前日淨值
              "i": "", 日期
              "j": "", 時間
              "k": "", ETF 類型 (1~4)
            },
            ...
          ]
          "refURL": "https://www.kgifund.com.tw/ETF/RWD/Introduction.aspx",
          "userDelay": "15000",
          "rtMessage": "OK",
          "rtCode": "0000"
        },
        ...
        {} <-- 最後有一組空的
      ]
    }
    """
    url = 'https://mis.twse.com.tw/stock/data/all_etf.txt'
    resp = requests.get(url)
    funds = resp.json()['a1']
    etf_dict = {}
    for fund in funds:
        if 'msgArray' in fund:
            for etf in fund['msgArray']:
                etf_dict[etf['a']] = etf

    for k in sorted(etf_dict.keys()):
        etf = etf_dict[k]
        print('%s, %s, %s%%' % (etf['a'], etf['e'], etf['g']))

if __name__ == '__main__':
    main()
