import sys
import os.path
from twnews.soup import NewsSoup, pkgdir

def main():
    if sys.argv[1].startswith('https'):
        samples = [sys.argv[1]]
    else:
        samples = [
            '{}/samples/appledaily.html'.format(pkgdir),
            'https://tw.news.appledaily.com/local/realtime/20181025/1453825',
        ]

    print('-' * 80)
    for path in samples:
        ns = NewsSoup(path, mobile=False)
        print('路徑: {}'.format(path))
        print('頻道: {}'.format(ns.channel))
        print('標題: {}'.format(ns.title()))
        ndt = ns.date()
        if ndt is not None:
            print('日期: {}'.format(ndt.strftime('%Y-%m-%d %H:%M:%S')))
        print('記者: {}'.format(ns.author()))
        print('內文:')
        print(ns.contents())
        print('有效內容率: {:.2f}%'.format(ns.effective_text_rate() * 100))
        print('-' * 80)

if __name__ == '__main__':
    main()
