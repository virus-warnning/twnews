# 製作新聞離線範本
SAMPLE_DIR='twnews/samples'

wget -O $SAMPLE_DIR/appledaily.html https://www.appledaily.com.tw/realtimenews/article/local/20160521/867195/%E5%92%8C%E7%94%B7%E5%8F%8B%E5%8F%A3%E8%A7%92%E9%8E%96%E9%96%80%E5%90%9E%E8%97%A5%E3%80%80%E5%A5%B3%E5%A2%9C%E6%A8%93%E4%B8%8D%E6%B2%BB
wget -O $SAMPLE_DIR/chinatimes.html https://www.chinatimes.com/realtimenews/20180916001767-260402
wget -O $SAMPLE_DIR/cna.html https://www.cna.com.tw/news/asoc/201603190029-1.aspx
wget -O $SAMPLE_DIR/ettoday.html https://www.ettoday.net/news/20171209/1069025.htm
wget -O $SAMPLE_DIR/ltn.html https://news.ltn.com.tw/news/life/breakingnews/2504351
wget -O $SAMPLE_DIR/setn.html https://www.setn.com/News.aspx?NewsID=350370
wget -O $SAMPLE_DIR/udn.html https://udn.com/news/story/7315/3004543

wget -O $SAMPLE_DIR/judicial-cp950.html http://aomp.judicial.gov.tw/abbs/wkw/WHD2ASHOW.jsp?rowid=%2Fsld%2F10703%2F09162840289.020
iconv -f cp950 -t utf8 $SAMPLE_DIR/judicial-cp950.html > $SAMPLE_DIR/judicial.html
rm -f $SAMPLE_DIR/judicial-cp950.html
