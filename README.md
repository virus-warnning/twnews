# 台灣新聞拆拆樂 (twnews)
台灣新聞拆拆樂用來分解各大新聞網站的內容

### 用法
```python
nsoup = NewsSoup('https://tw.news.appledaily.com/local/realtime/20181025/1453825', mobile=False)
print('頻道: {}'.format(nsoup.channel))
print('標題: {}'.format(nsoup.title()))
print('日期: {}'.format(nsoup.date().isoformat()))
print('記者: {}'.format(nsoup.author()))
print('內文:')
print(nsoup.contents())
```

### 環境需求
#### 使用
* BeautifulSoup 4
* requests
#### 開發
* green (僅開發時需要)

### 單元測試
如果發生問題可以利用 green 檢查失敗狀況，了解哪些分解設定沒和新聞網站同步
```sh
green -vvv twnews.tests
```
