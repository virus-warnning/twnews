import os.path
import logging

from twnews.soup import NewsSoup, pkgdir

def main():
    samples = [
        '{}/samples/appledaily.html'.format(pkgdir),
        'https://tw.news.appledaily.com/local/realtime/20181025/1453825',
    ]

    logging.info('-' * 80)
    for path in samples:
        ns = NewsSoup(path, mobile=False)
        logging.info('路徑: {}'.format(path))
        logging.info('頻道: {}'.format(ns.channel))
        logging.info('標題: {}'.format(ns.title()))
        logging.info('日期: {}'.format(ns.date().isoformat()))
        logging.info('記者: {}'.format(ns.author()))
        logging.info('內文:')
        logging.info(ns.contents())
        logging.info('有效內容率: {:.2f}%'.format(ns.effective_text_rate() * 100))
        logging.info('-' * 80)

if __name__ == '__main__':
    main()
