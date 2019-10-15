"""
快取處理模組
"""

import os
import lzma
import json

class DateCache:
    """
    處理日期命名快取
    """

    def __init__(self, category, item, data_format):
        """
        建立日期命名快取
        """
        self.category = category
        self.item = item
        self.data_format = data_format

    def get_path(self, datestr):
        """
        產生快取檔路徑
        """
        cache_dir = os.path.expanduser('~/.twnews/cache/' + self.category)
        if not os.path.isdir(cache_dir):
            os.makedirs(cache_dir)
        return '%s/%s-%s.%s.xz' % (cache_dir, self.item, datestr, self.data_format)

    def has(self, datestr):
        """
        檢查快取檔是否存在
        """
        cache_path = self.get_path(datestr)
        return os.path.isfile(cache_path)

    def load(self, datestr):
        """
        載入快取檔
        """
        content = None
        cache_path = self.get_path(datestr)
        with lzma.open(cache_path, 'rt') as f_cache:
            if self.data_format == 'json':
                content = json.load(f_cache)
            else:
                content = f_cache.read()
        return content

    def save(self, datestr, content):
        """
        儲存快取檔
        """
        cache_path = self.get_path(datestr)
        with lzma.open(cache_path, 'wt') as f_cache:
            if self.data_format == 'json':
                json.dump(content, f_cache)
            else:
                f_cache.write(content)
