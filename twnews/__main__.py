"""
__main__.py
"""

import sys
import locale
import os.path
from twnews.common import get_logger, VERSION
from twnews.soup import NewsSoup
from twnews.search import NewsSearch

def soup(path):
    """
    soup(path)
    """

    print('-' * 75)
    nsoup = NewsSoup(path, mobile=False)
    print('路徑: {}'.format(path))
    print('頻道: {}'.format(nsoup.channel))
    print('標題: {}'.format(nsoup.title()))
    ndt = nsoup.date()
    if ndt is not None:
        print('日期: {}'.format(ndt.strftime('%Y-%m-%d %H:%M:%S')))
    print('記者: {}'.format(nsoup.author()))
    print('內文:')
    print(nsoup.contents())
    print('有效內容率: {:.2f}%'.format(nsoup.effective_text_rate() * 100))
    print('-' * 75)


def search_and_list(keyword, channel):
    """
    search_and_list(keyword, channel)
    """

    print('測試搜尋')
    nsearch = NewsSearch(channel, limit=10)
    results = nsearch.by_keyword(keyword).to_dict_list()
    logger = get_logger()

    for (i, result) in enumerate(results):
        try:
            print('{:03d}: {}'.format(i, result['title']))
            print('     日期: {}'.format(result['date']))
            print('     連結: {}'.format(result['link']))
        except Exception as ex:
            logger.error('例外類型: %s', type(ex).__name__)
            logger.error(ex)


def search_and_soup(keyword, channel):
    """
    search_and_soup(keyword, channel)
    """

    print('測試搜尋與分解')
    logger = get_logger()
    nsearch = NewsSearch(channel, limit=10)
    nsoups = nsearch.by_keyword(keyword).to_soup_list()

    for (i, nsoup) in enumerate(nsoups):
        try:
            print('{:03d}: {}'.format(i, nsoup.path))
            print('     記者: {} / 日期: {}'.format(nsoup.author(), nsoup.date()))
            print('     標題: {}'.format(nsoup.title()))
            print('     {} ...'.format(nsoup.contents()[0:30]))
        except Exception as ex:
            logger.error('例外類型: %s', type(ex).__name__)
            logger.error(ex)


def search_and_compare_performance(keyword):
    """
    search_and_compare_performance(keyword):
    """

    print('測試各家新聞台的搜尋性能')
    summary = {}

    for channel in ['appledaily', 'cna', 'ettoday', 'ltn', 'setn', 'udn']:
        print()
        print(channel)
        print('-' * 60)
        summary[channel] = []
        for repeat in range(3):
            nsearch = NewsSearch(channel, limit=100)
            nsearch.by_keyword(keyword)
            results = nsearch.to_dict_list()
            total = len(results)
            tpp = nsearch.elapsed / nsearch.pages
            tpr = nsearch.elapsed / total
            summary[channel].append(tpp)
            msg = '{:03d}: {:.3f} 秒/頁, {:.3f} 秒/筆, 共 {} 頁, 總耗時: {:.3f} 秒'
            print(msg.format(repeat, tpp, tpr, nsearch.pages, nsearch.elapsed))
        print('-' * 60)

    print()
    print('Markdown 摘要表:')
    print()
    print('&nbsp; | 1st | 2nd | 3rd')
    print('---- | ---- | ---- | ----')
    for (channel, samples) in summary.items():
        print(channel, end='')
        for sample in samples:
            print(' | {:.3f}'.format(sample), end='')
        print()
    print()


def usage():
    """
    usage()
    """
    print('twnews {} (預設編碼: {})'.format(
        VERSION, locale.getpreferredencoding()))
    print()
    usage_path = os.path.dirname(__file__) + '/conf/usage.txt'
    with open(usage_path, 'r') as usage_file:
        print(usage_file.read())


def get_cmd_param(index, default=None):
    """
    get_cmd_param(index, default=None)
    """
    if len(sys.argv) > index:
        return sys.argv[index]
    return default

def main():
    """
    main()
    """
    action = get_cmd_param(1)
    if action == 'soup':
        keyword = get_cmd_param(
            2, 'https://tw.news.appledaily.com/local/realtime/20181025/1453825')
        soup(keyword)
    elif action == 'search':
        keyword = get_cmd_param(2, '酒駕')
        channel = get_cmd_param(3, 'appledaily')
        search_and_list(keyword, channel)
    elif action == 'snsp':
        keyword = get_cmd_param(2, '酒駕')
        channel = get_cmd_param(3, 'appledaily')
        search_and_soup(keyword, channel)
    elif action == 'sncp':
        keyword = get_cmd_param(2, '酒駕')
        search_and_compare_performance(keyword)
    else:
        if action != 'help':
            print('動作名稱錯誤')
            print()
        usage()


if __name__ == '__main__':
    main()
