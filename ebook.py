import requests
import os
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import threading
from queue import Queue
from pprint import pprint


class Chapter(object):
    '''章节类
    存储小说章节
    '''

    content = None

    def __init__(self, title, index, url):
        self.title = title
        self.index = index
        self.url = url
        pass

    def get(self):
        '''下载小说章节的逻辑
        
        Raises:
            Exception -- 下载失败异常
        '''

        requests.adapters.DEFAULT_RETRIES = 5
        s = requests.session()
        s.keep_alive = False
        res = s.get(self.url)
        if res.status_code != 200:
            raise Exception('{}下载错误。'.format(self.title))
        soup = BeautifulSoup(res.content, 'html.parser')
        article = soup.find(id='content').get_text()
        article = article.replace('\xa0\xa0\xa0\xa0', '\n\n')
        self.content = article

    def success_download(self):
        if self.content is None:
            return False
        return True


class Ebook(object):
    __source = 'https://www.zwdu.com'
    __local_path = 'books'
    __name = None      # 小说标题
    __cover = None     # 封面图片
    __author = None
    __description = None

    __chapter_index = []
    __chapters = []

    def __init__(self, url):
        self.__url = url
        self.__chapter_queue = Queue()
        self.__parse()

    def __parse(self):
        '''解析小说元数据（书名，作者，章节等）
        
        Raises:
            Exception -- 解析失败异常
        '''

        res = requests.get(self.__url)
        if res.status_code != 200:
            raise Exception('Can not connect url')
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.content, 'html.parser')

        cover_img = soup.find(id='fmimg')
        self.__cover = cover_img.find('img')['src']
        main_info = soup.find(id='info')
        self.__title = main_info.find('h1').get_text()
        self.__author = main_info.find_all('p')[0].get_text()
        self.__author = self.__author.split('：')[1].strip()
        title_list = soup.find(id='list')
        index = 0
        for title in title_list.find_all('a'):
            self.__chapters.append(
                Chapter(
                    title=title.get_text(),
                    index=index,
                    url=(self.__source + title['href'])
                )
            )

    def __create_ebook(self):
        '''创建电子书文件(txt)
        '''

        if not self.__title:
            raise Exception('无法解析书名')
        if not self.__author:
            raise Exception('无法解析作者')
        img = requests.get(self.__cover)
        if img.status_code != 200:
            raise Exception('封面解析错误')
        dir_name = './books/[{}]-{}'.format(self.__author, self.__title)
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
        self.__file = open('{}/{}.txt'.format(dir_name, self.__title), 'w')
        with open('{}/cover.jpg'.format(dir_name), 'wb') as f:
            f.write(img.content)

    def send_to_kindle(self, kindle_receive_address):
        pass

    def __fetch(self):
        while not self.__chapter_queue.empty():
            try:
                chapter = self.__chapter_queue.get()
                print('正在下载：' + chapter.title)
                chapter.get()
                if not chapter.success_download():
                    self.__chapter_queue.put(chapter)
            except Exception as e:
                print('下载异常：', e)
                self.__chapter_queue.put(chapter)
                continue

    def run(self):
        '''入口
        '''

        for c in self.__chapters:
            self.__chapter_queue.put(c)

        threads = [threading.Thread(target=self.__fetch) for i in range(50)]
        for t in threads:
            t.start()

        for t in threads:
            if t.is_alive():
                t.join()

        self.__create_ebook()
        self.__file.write('# ' + self.__title)
        self.__file.write('\n')
        self.__file.write('作者：' + self.__author)
        self.__file.write('\n\n')
        for c in self.__chapters:
            if not c.success_download():
                print('下载失败：%s' % c.title)
                continue
            self.__file.write('## ' + c.title)
            self.__file.write('\n')
            self.__file.write(c.content)
            self.__file.write('\n\n')
