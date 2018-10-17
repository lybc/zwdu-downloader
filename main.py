from ebook import Ebook

url = input('请输入需要下载的目录链接(https://www.zwdu.com/): ')

book = Ebook(url)
book.run()