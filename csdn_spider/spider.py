import requests as req
from base64 import b64decode
import hashlib
from urllib.parse import urlparse
import execjs
import hmac
from base64 import b64encode
import hashlib
from scrapy import selector
import re
import json
import requests
from scrapy import Selector
from models import Topic, Answer, Author
from datetime import datetime


class CsdnSpider:
    def __init__(self):
        # 以下数据是固定的，可根据需要修改
        self.secret_key = "bK9jk5dBEtjauy6gXL7vZCPJ1fOy076H"  # 密钥
        self.accept = "application/json, text/plain, */*"  # 数据格式？
        self.x_ca_key = "203899271"  # 签名参数
        self.user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"
        self.home_url = "https://ai.csdn.net/?utm_source=bbs"
        self.index_name_1 = []
        self.index_name_2_1 = []
        self.index_name_2_2 = []

        # 随机数
        self.x_ca_nonce = nonce_func = execjs.compile(
            """
            f = function(e){
                var t = e || null;
                return null == t && (t = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (function(e){
                    var t = 16 * Math.random() | 0;
                    return ("x" === e ? t: 3 & t | 8).toString(16)
            }))),
            t
            }
            """)

    def get_path(self, url):
        parse_result = urlparse(url)
        path = f"{parse_result.path}?{parse_result.query}"
        return path

    def get_sign(self, url, accept, nonce_str, ca_key, secrect_key):
        url_path = self.get_path(url)
        message = "GET\n"
        message += f"{accept}\n\n\n\n"
        message += f"x-ca-key:{ca_key}\n"
        message += f"x-ca-nonce:{nonce_str}\n"
        message += url_path
        sign = b64encode(hmac.new(secrect_key.encode('utf-8'), message.encode('utf-8'),
                                  digestmod=hashlib.sha256).digest()).decode()
        return sign

    def get_html(self, url):
        url_path = self.get_path(url)
        headers = {
            "accept": self.accept,
            "user-agent": self.user_agent,
            "x-ca-key": self.x_ca_key,
            "x-ca-signature": self.get_sign(url_path, self.accept, self.x_ca_nonce, self.x_ca_key, self.secret_key),
            "x-ca-nonce": f'{self.x_ca_nonce}',
            "x-ca-signature-headers": "x-ca-key,x-ca-nonce"
        }
        response = req.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"{response.status_code} + 反爬了")
        return response.text

    def write_index_name(self):
        headers = {
            "user-agent": self.user_agent,
        }
        response = req.get(self.home_url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"{response.status_code} + 反爬了")
        sel = Selector(text=response.text)
        # nodes = sel.css('div.custom-tree-node')

        # 获取1级索引
        self.index_name_1 = sel.xpath("//span[@class='label textEllipsis']/text()").getall()

        # 获取2级索引-1，即官方推荐社区
        script = sel.xpath("//script/text()").get()  # 因为只有一个<script>标签，所以用get()
        patten2_1 = re.compile(r'communityName.{1,30}')
        index_name_2_1_list = re.findall(patten2_1, script)
        self.index_name_2_1 = []
        for inn in index_name_2_1_list:
            temp = f'{re.findall(r":.*,", inn)}'[4:-4]
            self.index_name_2_1.append(temp)
        self.index_name_2_1 = list(filter(None, self.index_name_2_1))  # 去掉list里的空值，虽然这里面没有
        self.index_name_2_1 = [e for e in self.index_name_2_1 if e != 'AI 前沿']  # 去掉list里的AI前沿

        # 获取2级索引-2，即其他社区
        patten2_2 = re.compile(r'tagName.{1,20}')
        index_name_2_2_list = re.findall(patten2_2, script)
        self.index_name_2_2 = []
        pat = ":.*\","
        for inn in index_name_2_2_list:
            temp = f'{re.findall(pat, inn)}'[4:-4]
            self.index_name_2_2.append(temp)
        self.index_name_2_2 = list(filter(None, self.index_name_2_2))  # 去掉list里的空值，虽然这里面没有
        # index_name_2_2 = [e for e in index_name_2_2 if e != 'AI 前沿']  # 去掉list里的AI前沿
        with open('data/index_name_1.txt', 'w') as w:
            w.writelines(f'{self.index_name_1}')
        with open('data/index_name_2_1.txt', 'w') as w:
            w.writelines(f'{self.index_name_2_1}')
        with open('data/index_name_2_2.txt', 'w') as w:
            w.writelines(f'{self.index_name_2_2}')

        # print(f"这是1级索引：{self.index_name_1}")
        # print(f"这是2-1级索引：{self.index_name_2_1}, 共{len(self.index_name_2_1)}个")
        # print(f"这是2-2级索引：{self.index_name_2_2}, 共{len(self.index_name_2_2)}个")
        return

    def get_index_name(self):
        with open('data/index_name_1.txt', 'r') as w:
            r = w.read()
            self.index_name_1 = list(eval(r))
        with open('data/index_name_2_1.txt', 'r') as w:
            r = w.read()
            self.index_name_2_1 = list(eval(r))
        with open('data/index_name_2_2.txt', 'r') as w:
            r = w.read()
            self.index_name_2_2 = list(eval(r))

        # print(f"这是1级索引：{self.index_name_1}")
        # print(f"这是2-1级索引：{self.index_name_2_1}, 共{len(self.index_name_2_1)}个")
        print(f"这是2-2级索引：{self.index_name_2_2}, 共{len(self.index_name_2_2)}个")
        return
    def get_second_url(self):
        # index = {}
        # url_no_index = "https://bizapi.csdn.net/community-cloud/v1/homepage/community/by/tag?deviceType=PC&tagId="
        # for ind, i in enumerate(self.index_name_2_2):
        #     if ind >= 32:
        #         ind = ind+1
        #     index[ind+1] = i
        #     url_second = f'{url_no_index}{ind+1}'
        #     html_text = self.get_html(url_second)
        #     # html_json = json.dumps(html_text)
        #     with open(f'data/tag_{ind+1}.txt', 'w') as w:
        #         w.write(html_text)
        #     # print(html_text)
        # index = json.dumps(index)
        # print(index)
        with open('data/tag_1.txt', 'r') as w:
            text = w.read()
            
        return

if __name__ == '__main__':
    url1 = "https://ai.csdn.net/?utm_source=bbs"
    spider = CsdnSpider()
    spider.get_index_name()
    spider.get_second_url()
