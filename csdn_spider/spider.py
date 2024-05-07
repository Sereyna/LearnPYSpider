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
from models_db import Topic, Answer, Author
from datetime import datetime
import csv


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

    """
    解析URL
    
    输入参数：
        完整URL：https://bizapi.csdn.net/community-cloud/v1/homepage/community/by/tag?deviceType=PC&tagId=1
    
    输出：
        去掉域名的后半部分：/community-cloud/v1/homepage/community/by/tag?deviceType=PC&tagId=1
    """
    def get_path(self, url):
        parse_result = urlparse(url)
        path = f"{parse_result.path}?{parse_result.query}"
        return path

    """
    获取签名

    输入参数：
        url : 完整URL : 需要签名才能访问的完整URL
        accept : self.accept
        nonce_str : self.x_ca_nonce
        ca_key : self.x_ca_key
        secrect_key : 密钥 self.secret_key

    输出：
        签名 ： x-ca-signature
    """
    def get_sign(self, url, accept, nonce_str, ca_key, secrect_key):
        url_path = self.get_path(url)  # 如果在get_html()已经被解析过了，就不用解析了，如果没有，就必须要解析
        message = "GET\n"
        message += f"{accept}\n\n\n\n"
        message += f"x-ca-key:{ca_key}\n"
        message += f"x-ca-nonce:{nonce_str}\n"
        message += url_path
        sign = b64encode(hmac.new(secrect_key.encode('utf-8'), message.encode('utf-8'),
                                  digestmod=hashlib.sha256).digest()).decode()
        return sign

    """
    获取需要签名的HTML

    输入参数：
        url : 完整URL

    输出：
        response.text : 网页字符串
    """
    def get_html(self, url):
        headers = {
            "accept": self.accept,
            "user-agent": self.user_agent,
            "x-ca-key": self.x_ca_key,
            "x-ca-signature": self.get_sign(url, self.accept, self.x_ca_nonce, self.x_ca_key, self.secret_key),
            "x-ca-nonce": f'{self.x_ca_nonce}',
            "x-ca-signature-headers": "x-ca-key,x-ca-nonce"
        }
        response = req.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"{response.status_code} + 反爬了")
        return response.text

    """
    将所有索引：index_name_1、index_name_2_1、index_name_2_2全部写入文件

    无输入

    无输出
    
    文件参数：
        以字符串表示，无Title
    """
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
        script = sel.xpath("//script.json/text()").get()  # 因为只有一个<script.json>标签，所以用get()
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

        # 将索引写进文件
        with open('data/index_name_1.txt', 'w') as w:
            w.writelines(f'{self.index_name_1}')
        with open('data/index_name_2_1.txt', 'w') as w:
            w.writelines(f'{self.index_name_2_1}')
        with open('data/index_name_2_2.txt', 'w') as w:
            w.writelines(f'{self.index_name_2_2}')
        return

    """
    读取所有索引：index_name_1、index_name_2_1、index_name_2_2

    无输入

    无输出

    文件参数：
        以字符串表示，无Title
    """
    def get_index_name(self):
        # with open('data/index_name_1.txt', 'r') as w:
        #     r = w.read()
        #     self.index_name_1 = list(eval(r))
        # with open('data/index_name_2_1.txt', 'r') as w:
        #     r = w.read()
        #     self.index_name_2_1 = list(eval(r))
        with open('data/index_name_2_2.txt', 'r') as w:
            r = w.read()
            self.index_name_2_2 = list(eval(r))

        # print(f"这是2-2级索引：{self.index_name_2_2}, 共{len(self.index_name_2_2)}个")
        return

    """
    解析索引index_name_2_2的二级目录，即社区目录
    
    无输入
    
    无返回
    
    存储文件：
        tag_{number}.json
        tag_{number}.csv
        
    文件包含参数：
        id ： 社区ID
        tagName ： 社区名
        url ： 社区URL
        avatarUrl : 图片文件URL
    """

    def get_second_url(self):
        url_no_index = "https://bizapi.csdn.net/community-cloud/v1/homepage/community/by/tag?deviceType=PC&tagId="
        for ind, i in enumerate(self.index_name_2_2):
            if ind >= 32:
                ind = ind+1
            url_second = f'{url_no_index}{ind+1}'
            html_text = self.get_html(url_second)
            text_json = json.loads(html_text)

            # 如果需要保存到json文件
            with open(f'data/tag_{ind+1}.json', 'w') as f:
                json.dump(text_json, f, indent=4, ensure_ascii=False)

            # 如果需要保存到csv文件
            with open(f'data/tag_{ind+1}.csv', 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # 写入标题行
                writer.writerow(text_json['data'][0].keys())

                # 写入数据
                for item in text_json['data']:
                    writer.writerow(item.values())
        return

    """
    解析社区内容，提取出话题列表

    无输入

    无返回
    """
    def parse_list(self):
        # 读取json 或者csv都行，然后遍历
        # 先爬一个社区：3240,哪吒社区,https://bbs.csdn.net/forums/nezha

        # 将爬取的话题写入json文件
        # id = 3240
        # tagname = '哪吒社区'
        # url = 'https://bbs.csdn.net/forums/nezha'
        # headers = {
        #     "user-agent": self.user_agent,
        # }
        # response = req.get(url, headers=headers)
        # if response.status_code != 200:
        #     raise Exception(f'反爬，错误为{response.status_code}')
        # script = re.search("window.__INITIAL_STATE__= (.*});</script>", response.text, re.IGNORECASE)
        # if script:
        #     script = script.group(1)
        #     script_json = json.loads(script)
        #     with open(f'data/script.json', 'w') as f:
        #         json.dump(script_json, f, indent=4, ensure_ascii=False)

        with open(f'data/script.json', 'r') as r:
            script_dict = json.load(r)
        page_size = script_dict["pageData"]["data"]["baseInfo"]["page"]["pageSize"]
        page_total = script_dict["pageData"]["data"]["baseInfo"]["page"]["total"]
        page_total_test = 2  # 测试用
        tabid = script_dict["pageData"]["data"]["baseInfo"]["defaultActiveTab"]
        datalist = script_dict["pageData"]["dataList"][0]
        self.extract_topic(datalist)

        # else:
        #     raise Exception(f'{url} 爬取内容为空！')

        return

    """
    解析话题列表，获得话题数据

    输入:
        data_list : 话题列表，json数据

    无返回
    
    存储数据库参数：topic = Topic()
        话题标题 : topic.title
        话题简介 : topic.description
        话题ID : topic.id
        话题发布时间 : topic.create_time
        话题回复数量 : topic.answer_nums
        话题查看数量 : topic.click_nums
        话题点赞数量 : topic.praised_nums
        话题作者 : topic.author
    """
    def extract_topic(self, data_list):
        for data in data_list:
            content = data["content"]
            topic = Topic()
            topic.title = content["topicTitle"]
            topic.description = content["description"]
            topic.id = content["contentId"]
            topic.create_time = datetime.strptime(content["createTime"], '%Y-%m-%d %H:%M:%S')
            topic.answer_nums = content["commentCount"]
            topic.click_nums = content["viewCount"]
            topic.praised_nums = content["diggNum"]
            topic.author = content["username"]

            existed_topics = Topic.select().where(Topic.id == topic.id)
            if existed_topics:
                topic.save()
            else:
                topic.save(force_insert=True)

            # parse_topic(content["url"])
            self.parse_author(f'https://blog.csdn.net/{content["username"]}')
        return

    def parse_author(self, url):
        return


if __name__ == '__main__':
    url1 = "https://ai.csdn.net/?utm_source=bbs"
    spider = CsdnSpider()
    spider.get_index_name()
    spider.parse_list()
