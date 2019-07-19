# 製作新聞離線範本
SAMPLE_DIR='twnews/samples'
USER_AGENT='Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36'

wget -U "$USER_AGENT" -O $SAMPLE_DIR/appledaily.html https://tw.news.appledaily.com/local/realtime/20160521/867195
wget -U "$USER_AGENT" -O $SAMPLE_DIR/chinatimes.html https://www.chinatimes.com/realtimenews/20180916001767-260402
wget -U "$USER_AGENT" -O $SAMPLE_DIR/cna.html https://www.cna.com.tw/news/asoc/201603190029-1.aspx
wget -U "$USER_AGENT" -O $SAMPLE_DIR/ettoday.html https://www.ettoday.net/news/20171209/1069025.htm
wget -U "$USER_AGENT" -O $SAMPLE_DIR/ltn.html https://m.ltn.com.tw/news/life/breakingnews/2504351
wget -U "$USER_AGENT" -O $SAMPLE_DIR/setn.html https://www.setn.com/m/News.aspx?NewsID=350370
wget -U "$USER_AGENT" -O $SAMPLE_DIR/udn.html https://udn.com/news/story/7315/3705102

# $WGET -O $SAMPLE_DIR/judicial-cp950.html http://aomp.judicial.gov.tw/abbs/wkw/WHD2ASHOW.jsp?rowid=%2Fsld%2F10703%2F09162840289.020
# iconv -f cp950 -t utf8 $SAMPLE_DIR/judicial-cp950.html > $SAMPLE_DIR/judicial.html
# rm -f $SAMPLE_DIR/judicial-cp950.html

xz -f $SAMPLE_DIR/*.html
