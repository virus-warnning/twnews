import os.path
import logging

from twnews.soup import NewsSoup

def main():
    if os.path.isfile('conf/logging.ini'):
        logging.config.fileConfig('conf/logging.ini')
    logger = logging.getLogger()

    samples = [
        'samples/appledaily.html',
        'https://tw.news.appledaily.com/local/realtime/20181025/1453825/',
    ]

    logging.info('-' * 80)
    for path in samples:
        ns = NewsSoup(path, mobile=False)
        logging.info('頻道: {}'.format(ns.channel))
        logging.info('標題: {}'.format(ns.title()))
        logging.info('日期: {}'.format(ns.date().isoformat()))
        logging.info('記者: {}'.format(ns.author()))
        logging.info('內文:')
        logging.info(ns.contents())
        logging.info('-' * 80)

if __name__ == '__main__':
    main()
