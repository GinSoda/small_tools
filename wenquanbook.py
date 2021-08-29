# coding : utf-8
# co-author: ginsoda
# modifified from https://www.52pojie.cn/thread-1108776-1-1.html
# modified time: 2021.08.14
# No module named 'Crypto'解决方案: https://segmentfault.com/a/1190000039335378
# webdriver Python FileNotFoundError: [WinError 2]: https://blog.csdn.net/u014094184/article/details/80085336
# 手动登录 https://blog.csdn.net/q965844841qq/article/details/105708138
# 注意 .\chrome.exe --remote-debugging-port=9999 --user-data-dir="C:\test" 命令中--remote-debugging-port是一体的，不要加多余空格，启动后chrome后，localhost:9999/json能够正常打开
"""
introduction: a simple python crawler for wqbook.wqxuetang.com
"""

import logging
import logging.handlers
from PIL import Image
from reportlab.lib.pagesizes import A4, portrait, landscape, mm
from reportlab.pdfgen import canvas
import os
from io import BytesIO
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import datetime
import base64
import queue
from Crypto.Util.number import *
from PyPDF2 import PdfFileReader, PdfFileWriter
import requests

BEGIN_PAGE = 1
url = "https://wqbook.wqxuetang.com/read/pdf/3215800"
# 手动写str_cookie
str_cookie = "***********************************"
cookie_dict = {}  # cookie字典，这里不用管，下面代码会把str_cookie转换为cookie_dict
# 图片路径
_image_path = "C:\\tmp\\img"
# PDF路径(不要与图片路径相同)
_pdf_path = "C:\\tmp\\pdf"

formatter = "%(asctime)s %(pathname)s(%(lineno)d): %(levelname)s %(message)s"
formatter = logging.Formatter(formatter)
handler = logging.handlers.RotatingFileHandler("C:\\tmp\\wqbook.log", encoding='utf-8') 
handler.setFormatter(formatter)
logger = logging.getLogger(name='wqbook')
logger.addHandler(handler)
logger.setLevel('INFO')

def get_cookie_dict(cookie_para) :
    """
    :param cookie_para: 传入的cookie字符串
    :return:返回cookie字典
    """
    cookie_para = cookie_para.replace(" ", "")
    list = cookie_para.split(";")

    cookie_dict = {}
    for i in list :
        index = i.find('=')
        key = i[:index]
        value = i[index + 1 :]
        cookie_dict[key] = value
    return cookie_dict


def get_image_size(content) :
    """
    :param content: 图片的二进制数据
    :return: 图片的宽高
    """
    tmpIm = BytesIO(content)
    im = Image.open(tmpIm)
    w = im.size[0]  # 宽
    h = im.size[1]  # 高
    return w, h


def get_size() :
    """
    获取图片的宽高，来计算比例，用来合成PDF
    :return:PDF的尺寸
    """
    with open(_image_path + "\\1.jpeg", "rb") as f :
        A4_MY = [0, 297 * mm]
        f.seek(16)
        w = bytes_to_long(f.read(4))
        h = bytes_to_long(f.read(4))
    bili = h / w
    A4_MY[0] = (297 // bili) * mm
    return A4_MY


def get_pdf_name() :
    """
    :return: 将要下载PDF书籍的名字
    """
    try :
        index = url.find("pdf")
        # name_url = "https://lib-nuanxin.wqxuetang.com/v1/book/initbook?bid=" + url[index + 4 :]
        name_url = "https://wqbook.wqxuetang.com/read/pdf?bid=" + url[index + 4 :]
        
        headers = {
            'Accept' : 'application/json, text/plain, */*',
            'Accept-Encoding' : 'gzip, deflate, br',
            'Accept-Language' : 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'BA' : 'bapkg/com.bookask.wqxuetang baver/0.0.1',
            'Cache-Control' : 'no-cache',
            'Connection' : 'keep-alive',
            'Cookie' : str_cookie,
            # 'Host' : 'lib-nuanxin.wqxuetang.com',
            'Host' : 'wqbook.wqxuetang.com',
            'Pragma' : 'no-cache',
            # 'Referer' : 'https://lib-nuanxin.wqxuetang.com/',
            'Referer' : 'https://wqbook.wqxuetang.com/',
            'Sec-Fetch-Dest' : 'empty',
            'Sec-Fetch-Mode' : 'cors',
            'Sec-Fetch-Site' : 'same-origin',
            'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.100 Safari/537.36'
        }

        res = requests.get(name_url, headers=headers)
        dict = res.json()
        return dict['data']['name']
    except :
        return "default"


def convert_images_to_pdf(img_path, pdf_path, size, pdf_count) :
    """
    将图片合成为PDF
    :param img_path:图片文件夹路径
    :param pdf_path:PDF文件路径(包含PDF文件名)
    :param size: PDF的尺寸
    :param pdf_count: PDF的总页数
    :return:
    """
    pages = 0
    (w, h) = size
    c = canvas.Canvas(pdf_path, pagesize=portrait((w, h)))
    l = os.listdir(img_path)
    l.sort(key=lambda x : int(x[:-5]))      # 因为后缀都是.jpeg，所以是-5，对图片进行排序
    for i in l :
        f = img_path + os.sep + str(i)
        c.drawImage(f, 0, 0, w, h)
        c.showPage()
        pages = pages + 1
        logger.info(f"添加进度: {pages} / {pdf_count}")
    c.save()


def get_book_pages(html_text) :
    """
    :param html_text:传入的整个页面
    :return: 返回这本数的页数
    """
    soup = BeautifulSoup(html_text, "html.parser")
    help_contents = soup.find_all('div', class_="page-img-box")
    return len(help_contents) - 1


def add_cookie(browser) :
    """
    增加cookie访问
    :param browser:webdriver.Chrome()
    :return:
    """
    _cookie = {}
    for key in cookie_dict :
        _cookie['name'] = key
        _cookie['value'] = cookie_dict[key]
        browser.delete_cookie(key)
        browser.add_cookie(_cookie)


def delay(browser, page, is_last) :
    """
    此函数非常关键，它等待两个页面全部加载完毕
    原理是根据此页面的图片是否高清
    输入页码之后，一次加载的是2页，比如输入3，加载的是3,4两页的图片
    :param browser:webdriver.Chrome()
    :param page:页数
    :param is_last: 是否是最后一页
    :return:图片字节流
    """
    start_tm = datetime.datetime.now()
    while True :
        try :
            # 如果长时间没反应就刷新当前页面，并且把当前下载页面输入进去
            end_tm = datetime.datetime.now()
            if (end_tm - start_tm).seconds > 8 :
                start_tm = datetime.datetime.now()
                browser.refresh()
                time.sleep(1)
                input_ = browser.find_element_by_id('input')
                input_.clear()
                input_.send_keys('1')
                time.sleep(0.5)
                input_.clear()
                input_.send_keys(str(page))
                input_.send_keys(Keys.ENTER)

            html = browser.page_source
            soup = BeautifulSoup(html, "html.parser")
            help_contents = soup.find_all('div', class_="page-img-box")
            text1 = help_contents[page].find('img')['src']
            index1 = text1.find(",")
            img_byte1 = base64.b64decode(text1[index1 + 1 :].encode("utf-8"))
            num1, tmp = get_image_size(img_byte1)
            if not is_last :  # 如果不是最后一个
                text2 = help_contents[page + 1].find('img')['src']
                index2 = text2.find(",")
                img_byte2 = base64.b64decode(text2[index2 + 1 :].encode("utf-8"))
                num2, tmp = get_image_size(img_byte2)
                if num1 > 500 and num2 > 500 :
                    return [img_byte1, img_byte2]
                time.sleep(0.5)
            else :  # 如果是最后一个
                if num1 > 500 :
                    return img_byte1
        except :
            pass


def input_action(browser, page_num, is_last) :
    """
    开始模拟自动输入页码，加载
    """
    input = browser.find_element_by_id('input')
    input.clear()
    input.send_keys(str(page_num))
    input.send_keys(Keys.ENTER)

    # 延迟，等待页面加载完毕
    _list = delay(browser, page_num, is_last)
    return _list


def download_image(text, page, dataQueue) :
    """
    :param text: 图片字节流
    :param page: 页码，防止保存失败的时候，加入到dataQueue中方便最后重新下载
    :param dataQueue:
    :return:
    """
    try :
        byte_text = text
        img_name = str(page) + ".jpeg"
        with open(_image_path + "\\" + img_name, "wb") as f :
            f.write(byte_text)
    except :
        logger.info(f"第{page}页下载失败")
        dataQueue.put(page)


def shu_q_action(browser) :
    """
    开始模拟打开所有目录(经过测试，只有打开所有目录之后，子书签才会出现在html文档中)
    :param browser:
    :return:返回包含子书签的html文档，以便后期用BeautifulSoup获取保存书签
    """
    mulu = browser.find_element_by_css_selector("[class='iconfont2 icon-wq-catalog']")
    mulu.click()
    # 打开所有的三角形
    sjxs = browser.find_elements_by_css_selector("[class='el-tree-node__expand-icon el-icon-caret-right']")
    for sjx in sjxs :
        sjx.click()
        time.sleep(0.5)
    time.sleep(2)  # 等待2秒，开始
    html = browser.page_source.encode("utf-8")
    return html


def download_shu_q(html) :
    """
    爬取书签保存为列表,格式如下
    无子书签： [name, num, 0]
    有子书签: [name, num, [[child_name1, child_num1],[child_name2, child_num2]...... ]]
    :param html: html字符串
    :return:返回书签列表
    """
    soup = BeautifulSoup(html, "html.parser")
    help_contents = soup.find('div', role="tree")
    xs = help_contents.contents
    parent_tag_list = []
    for i in range(len(xs)) :  # 筛选出父节点
        try :
            if xs[i]['role'] == "treeitem" :
                parent_tag_list.append(xs[i])
        except :
            pass

    shu_q = []
    for i in range(len(parent_tag_list)) :
        temp_shu_q = [0, 0, 0]  # 名字，序号，子节点
        temp_shu_q[0] = parent_tag_list[i].find("div", class_="el-tree-node__content").find("span",
                                                                                            class_="BookCatTree-node-left").string.replace(
            "\n", "")
        temp_shu_q[1] = parent_tag_list[i].find("div", class_="el-tree-node__content").find("span",
                                                                                            class_="BookCatTree-node-pagenum").string.replace(
            "\n", "").replace(" ", "")
        a = parent_tag_list[i].find("div", class_="el-tree-node__children")
        if a :  # 如果存在子节点
            tag_children = a.find_all('div', role="treeitem")

            children_shu_q = []
            for i in range(len(tag_children)) :
                child_shu_q = [0, 0]  # 名字，序号
                child_shu_q[0] = tag_children[i].find("div", class_="el-tree-node__content").find("span",
                                                                                                  class_="BookCatTree-node-left").string.replace(
                    "\n", "")
                child_shu_q[1] = tag_children[i].find("div", class_="el-tree-node__content").find("span",
                                                                                                  class_="BookCatTree-node-pagenum").string.replace(
                    "\n", "").replace(" ", "")
                children_shu_q.append(child_shu_q)
            temp_shu_q[2] = children_shu_q
        else :
            temp_shu_q[2] = 0
        shu_q.append(temp_shu_q)
    # for i in range(len(shu_q)) :
    #     print(shu_q[i][0], shu_q[i][1])
    #     if shu_q[i][2] != 0 :
    #         for j in range(len(shu_q[i][2])) :
    #             print("  ", shu_q[i][2][j][0], shu_q[i][2][j][1])

    return shu_q


def add_shu_q(shu_q, pdf_path) :
    """
    书签的列表格式
    无子书签： [name, num, 0]
    有子书签: [name, num, [[child_name1, child_num1],[child_name2, child_num2]...... ]]
    根据shu_q列表来对PDF文件添加书签
    :param shu_q:
    :return:
    """
    # 读取PDF文件，创建PdfFileReader对象
    book = PdfFileReader(pdf_path)

    # 创建PdfFileWriter对象，并用拷贝reader对象进行初始化
    pdf = PdfFileWriter()
    pdf.cloneDocumentFromReader(book)

    # 添加书签
    # 注意：页数是从0开始的，中文要用unicode字符串，否则会出现乱码
    # 如果这里的页码超过文档的最大页数，会报IndexError异常

    for i in range(len(shu_q)) :
        parent = pdf.addBookmark(shu_q[i][0], int(shu_q[i][1]) - 1)
        if shu_q[i][2] != 0 :  # 如果有子书签
            for j in range(len(shu_q[i][2])) :
                pdf.addBookmark(shu_q[i][2][j][0], int(shu_q[i][2][j][1]) - 1, parent=parent)

    # 保存修改后的PDF文件内容到文件中
    # 注意：这里必须用二进制的'wb'模式来写文件，否则写到文件中的内容都为乱码
    with open(pdf_path, 'wb') as fout :
        pdf.write(fout)


if __name__ == "__main__" :
    cookie_dict = get_cookie_dict(str_cookie)
    start = time.time()  # 开始时间
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9999")
    browser = webdriver.Chrome("C:\Software\chromedriver.exe", chrome_options=chrome_options)
    browser.get(url=url)  # 先访问一次
    # time.sleep(30)
    dataQueue = queue.Queue(500)  # 初始化队列
    try :
        add_cookie(browser)  # 增加cookie
        browser.get(url=url)  # 打开网页
        time.sleep(4)

        pages = get_book_pages(browser.page_source)
        logger.info(f"总页数为 {pages}")  # 获取书本总页数
        for i in range(BEGIN_PAGE, pages, 2) :
            list = input_action(browser, i, False)
            download_image(list[0], i, dataQueue)
            download_image(list[1], i + 1, dataQueue)
            logger.info(f"下载进度: {i} / {pages}")

        if pages % 2 == 1 :  # 如果是奇数的话，最后一页没有下载
            text = input_action(browser, pages, True)
            download_image(text, pages, dataQueue)

        while not dataQueue.empty() :
            index = dataQueue.get(False)
            b_text = input_action(browser, index, True)
            download_image(b_text, index, dataQueue)
        end = time.time()
        logger.info("-------------下载图片完毕-------------")
        # 开始获取尺寸

        shu_q = download_shu_q(shu_q_action(browser))  # 打开目录，准备下载书签
        logger.info("下载书签完毕")
        # 所有图片下载完毕，准备合成PDF
        pdf_name = get_pdf_name().replace("/", "_")
        logger.info(f"获取书名完毕，书名为《{pdf_name}》")
        img_path = _image_path
        pdf_path = _pdf_path + "\\" + pdf_name + ".pdf"
        convert_images_to_pdf(img_path, pdf_path, get_size(), pages)
        logger.info("转换完毕，准备添加书签")
        # 添加书签
        add_shu_q(shu_q, pdf_path)
        logger.info(f"下载完成，时间{end - start}秒")
    finally :
        browser.close()
