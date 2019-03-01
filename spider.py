# -*- coding: utf-8 -*-
from lxml import etree
import requests
import time
import re
import pymysql
from pprint import pprint

conn = pymysql.connect(host='localhost', port=3306, database='wechart', user='root', password='mysql',
                       charset='utf8mb4')
cur = conn.cursor()


# 目标url
def get_html():
    url = "https://mp.weixin.qq.com/cgi-bin/appmsg"

    # 使用Cookie，跳过登陆操作
    headers = {
        "Cookie": "noticeLoginFlag=1; pgv_pvid=7230638121; eas_sid=b1I5U4M0K5s4t0h7Z0a8S5Q4W5; pgv_pvi=6919959552; RK=iQR4vuvUMd; ptcz=ca7ef9ad32f53186db20c6d09bdfbe9982524c2c5be47a5cf474b70edd7e64d0; LW_uid=01c59421V4w7l7V0q6O7H4W4c3; LW_sid=61N5u4r104Y7N7s0j7h2T6a9w8; ua_id=Kemjz6sDMzY4WivzAAAAALddnGoeTZQY_JO2_GjG-Do=; mm_lang=zh_CN; openid2ticket_oZLfW1CbN_ZX1-nSfCceBk4adSdY=kGIDqxOBUVDg/NuCTBwR38qE7VW6IhRvhOTIc2XTZUg=; pgv_si=s2563801088; uuid=69aebc36a800896b23531cf1ca8ad396; data_bizuin=3570841444; bizuin=3570841444; data_ticket=ofnrbGAyyLQDMiIIIW1YjQOAmICMBYQtqtV1LR4K3HWLxlz7sIWZ2Ljzl7mHMJEE; slave_sid=TnZFWUYyRk9keGJnM0VfakRYZUpHNzc5ZXNNeHd1YklhdUdFVExpNXdfclY2d2VBdmFOaW5kTWk0TDJla0tUN0FUM0FWOWc2alNCUzhwbzZUQjA5M1ZSdllpbDVpQzBneDBmSHFGeTRrS0tzX1NKYmtycHR1SVJ3cjVXeXg3dzVJUFBPTEVoYjIzdWJJN25N; slave_user=gh_8f070f6d9ae4; xid=3f86c8a497f78f30cadd910328f14e6b",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36",
    }

    """
    需要提交的data
    number表示从第number页开始爬取，为5的倍数，从0开始。如0、5、10……
    token可以使用Chrome自带的工具进行获取
    fakeid是公众号独一无二的一个id，等同于后面的__biz
    """
    begin = 0
    data = {
        "token": 1990031817,
        "lang": "zh_CN",
        "f": "json",
        "ajax": "1",
        "action": "list_ex",
        "begin": begin,
        "count": "5",
        "query": "",
        "fakeid": "MzIzNjEyMDMwMw==",
        "type": "9",
    }
    begin += 5
    # 使用get方法进行提交
    content_json = requests.get(url=url, headers=headers, params=data).json()

    return content_json, headers


def parse_data(content_json, headers):
    # 返回了一个json，里面是每一页的数据
    urls = []
    titles = []
    # pprint.pprint(content_json.text)
    for item in content_json["app_msg_list"]:
        # 提取每页文章的标题及对应的url
        # print(item["title"], item["link"])
        urls.append(item['link'])
        titles.append(item['title'])
        urls_num = len(urls)
        # 每页有多少条数据
        for n in range(urls_num):
            # 循环进入详情页
            url = urls[n]
            title = titles[n]
            response = requests.get(url, headers=headers)

            with open('html.text', 'a+') as f:
                f.write(response.text)
            sql = "insert into data(href,title,data) values('%s','%s','%s')" % \
                  (url, title, pymysql.escape_string(response.text))
            # pprint(response.content)
            try:
                # 执行sql语句
                cur.execute(sql)
                # 提交到数据库执行
                conn.commit()
            except Exception as f:
                # Rollback in case there is any error
                print('存入失败')
                print(f)
                conn.rollback()

            n += 1
            # "获取响应的页面内容"
            html_str = response.text
            html = etree.HTML(html_str)
            """
            公众号名称
            """
            img1_list = html.xpath('//*[@id="js_content"]//img/@data-src')
            '''图片链接'''
            img_list = html.xpath('//*[@id="js_content"]//img/@src')
            text_list = html.xpath('//*[@id="img-content"]//span/text()')
            '''文章内容'''

            for text in text_list:
                print(text)

                with open('text', 'a+') as f:
                    f.write(text + "\n")
            # 图片链接列表
            page = 0
            for img in img_list:
                num = str(page)
                print(img)
                # 打印图片链接
                response = requests.get(img)

                pic_suffix = re.split("[=]", img)[1]  # 图片后缀(格式)

                print(pic_suffix)
                pic = response.content
                # 获取图片二进制数据
                path = '/home/lpubuntu/Desktop/pichur/'
                # 定义图片存储路径
                with open(path + num + '.' + pic_suffix, 'a+')as f:
                    f.write(pic)
                page += 1
            for img in img1_list:
                num = str(page)
                print(img)
                # 打印图片链接
                response = requests.get(img)

                pic_suffix = re.split("[=]", img)[1]  # 图片后缀(格式)

                print(pic_suffix)
                pic = response.content
                # 获取图片二进制数据
                path = '/home/lpubuntu/Desktop/pichur/'
                # 定义图片存储路径
                with open(path + num + '.' + pic_suffix, 'wb')as f:
                    f.write(pic)
                page += 1

            time.sleep(2)


def main():
    content_json, headers = get_html()
    parse_data(content_json, headers)


if __name__ == '__main__':
    main()
