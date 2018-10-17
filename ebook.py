import requests
import os
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import threading
from pprint import pprint


class Ebook(object):
    __source = 'https://www.zwdu.com'
    __local_path = 'books'
    __name = None      # 小说标题
    __cover = None     # 封面图片
    __author = None
    __description = None

    __chapter_index = []

    def __init__(self, url):
        self.__url = url
        self.__parse()

    def __parse(self):
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
        for title in title_list.find_all('a'):
            self.__chapter_index.append({
                'name': title.get_text(),
                'url': self.__source + title['href']
            })

    def __create_ebook(self):
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
        
    def __downloads(self, start, end):
        indexes = range(start, end+1)
        for i in indexes:
            chapter = self.__chapter_index[i]
            print('正在下载：{}'.format(chapter['name']))
            res = requests.get(chapter['url'])
            if res.status_code != 200:
                print('{}下载错误。'.format(chapter['name']))
            soup = BeautifulSoup(res.content, 'html.parser')
            article = soup.find(id='content').get_text()
            article = article.replace('\xa0\xa0\xa0\xa0', '\n\n')
            self.__chapter_index[i]['content'] = article
    
    def send_to_kindle(self, kindle_receive_address):
        pass
        

    def run(self):
        self.__create_ebook()

        print('正在下载《{}》，{}'.format(self.__title, self.__author))
        thread_list = []
        keys = []
        for index, chapter in enumerate(self.__chapter_index):
            keys.append(index)
            if len(keys) >= 20:
                t = threading.Thread(target=self.__downloads, args=(keys[0], keys[-1]))
                t.start()
                thread_list.append(t)
                keys = []

        # 不满20的keys
        t = threading.Thread(target=self.__downloads, args=(keys[0], keys[-1]))
        t.start()
        thread_list.append(t)

        for tread in thread_list:
            tread.join()

        for article in self.__chapter_index:
            if 'content' not in article.keys():
                print(article)
                continue
            self.__file.write('## ' + article['name'])
            self.__file.write('\n')
            self.__file.write(article['content'] + '\n\n')