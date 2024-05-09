import time

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

    """
    类初始化

    参数：
        self.secret_key : 密钥 : 分析网页请求获取，为固定值
        self.accept : 数据格式？ : 分析网页请求获取，为固定值
        self.x_ca_key : 生成签名的参数之一 : 分析网页请求获取，为固定值
        self.x_ca_nonce : 生成签名的参数之一 : 为网页端随机生成，将网页端生成随机数代码原样拷贝就行
        self.user_agent : 浏览器
        self.home_url : 主页 : 即CSDN首页"https://ai.csdn.net/?utm_source=bbs"
        self.index_name = [] : 二级索引-其他社区 : 所有社区和帖子出自这里
        self.community_url = [] : 所有社区的URL
    """
    def __init__(self):
        # 以下数据是固定的，可根据需要修改
        self.secret_key = "bK9jk5dBEtjauy6gXL7vZCPJ1fOy076H"  # 密钥
        self.accept = "application/json, text/plain, */*"  # 数据格式？
        self.x_ca_key = "203899271"  # 签名参数
        self.user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"
        self.home_url = "https://ai.csdn.net/?utm_source=bbs"
        self.index_name = []  # 二级索引-其他社区 : 所有社区和帖子出自这里
        self.community = []  # 所有社区，包括社区ID、名称、URL、图片URL

        # 生成随机数
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
    私有方法 : 解析URL
    
    输入参数：
        完整URL：https://bizapi.csdn.net/community-cloud/v1/homepage/community/by/tag?deviceType=PC&tagId=1
    
    输出：
        去掉域名的后半部分：/community-cloud/v1/homepage/community/by/tag?deviceType=PC&tagId=1
    """
    def __get_path(self, url):
        parse_result = urlparse(url)
        path = f"{parse_result.path}?{parse_result.query}"
        return path

    """
    私有方法 : 获取签名

    输入参数：
        url : 完整URL : 需要签名才能访问的完整URL
        accept : self.accept
        nonce_str : self.x_ca_nonce
        ca_key : self.x_ca_key
        secrect_key : 密钥 self.secret_key

    输出：
        签名 ： x-ca-signature
    """
    def __get_sign(self, url, accept, nonce_str, ca_key, secrect_key):
        url_path = self.__get_path(url)  # 如果在get_html()已经被解析过了，就不用解析了，如果没有，就必须要解析
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
            "x-ca-signature": self.__get_sign(url, self.accept, self.x_ca_nonce, self.x_ca_key, self.secret_key),
            "x-ca-nonce": f'{self.x_ca_nonce}',
            "x-ca-signature-headers": "x-ca-key,x-ca-nonce"
        }
        response = req.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"签名不通过，错误信息：{response.status_code}")
        return response.text

    """
    拉取所有索引，并赋值于self.index_name，并将所有索引即index_name全部写入文件

    无输入

    无输出
    
    写入文件参数：json数据格式
        "id": 索引id,
        "tagName": 二级索引的名称,
        "childCount": 该索引的社区数
    例如：
        {
        "id": 1,
        "tagName": "编程语言&开发工具",
        "childCount": 1006
        }
        
    """
    def get_index(self):
        headers = {
            "user-agent": self.user_agent,
        }
        response = req.get(self.home_url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"爬取网页：{self.home_url}，错误信息：{response.status_code}")

        # 将获取json格式数据，以Match[str]类型传递给变量，group(1)并将Match[str]类型转换为string
        script_string = re.search('window.__INITIAL_STATE__=(.*});</script>', response.text, re.IGNORECASE).group(1)
        script_dict = json.loads(script_string)  # 字典类型

        # 获取2级索引，即其他社区
        index_name_list = script_dict["pageData"]["data"]["community-tree"]["otherCommunityTree"]["tags"]
        if not self.index_name:  # 判断数组是否为空
            for inn in index_name_list:
                self.index_name.append({"id": inn["id"], "tagName": inn["tagName"], "childCount": inn["childCount"]})
            # 将索引写进文件
            with open('data/index_name.json', 'w') as w:
                json.dump(self.index_name, w, indent=4, ensure_ascii=False)
        else:
            pass
        return

    """
    拉取索引index_name下的所有社区目录
    
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

    def get_community(self):
        url_no_index = "https://bizapi.csdn.net/community-cloud/v1/homepage/community/by/tag?deviceType=PC&tagId="
        # 遍历获取所有社区的信息，包括ID，名称，URL，图片URL
        if not self.index_name:
            self.get_index()
        for inn in self.index_name:
            index_url = f'{url_no_index}{inn["id"]}'
            try:
                html_text = self.get_html(index_url)
            except Exception as e:
                print(f"爬取社区信息失败，失败原因为:{e}")
                with open(f'exception_log', 'wa', encoding='utf-8') as w:
                    w.writelines(f'爬取社区信息失败！社区ID：{inn["id"]}社区名称：{inn["tagName"]}，社区URL：{inn["url"]}')
                continue
            community_list_json = json.loads(html_text)["data"]
            for clj_json in community_list_json:
                self.community.append(clj_json)

        # 如果需要保存到json文件
        with open(f'data/community.json', 'w') as f:
            json.dump(self.community, f, indent=4, ensure_ascii=False)

        # 如果需要保存到csv文件
        with open(f'data/community.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # 写入标题行
            writer.writerow(self.community[0].keys())

            # 写入数据
            for item in self.community:
                writer.writerow(item.values())
        return

    def read_all_info(self):
        # 读取社区信息
        with open(f'data/community.json', 'r', encoding='utf-8') as r:
            self.community = json.loads(r.read())

    """
    解析社区内容，提取出话题列表data_list

    无输入

    无返回
    """
    def parse_topic_list(self):
        if len(self.community) == 0:
            self.get_community()
        for clj in self.community:
            community_url = clj["url"]
            community_id = clj["id"]
            headers = {
                "user-agent": self.user_agent,
            }
            response = req.get(community_url, headers=headers)
            if response.status_code != 200:
                raise Exception(f'爬取社区页面失败，社区名称：{clj["tagName"]}，社区URL：{clj["url"]}，错误为{response.status_code}')
            script = re.search("window.__INITIAL_STATE__= (.*});</script>", response.text, re.IGNORECASE)
            if script:
                script = script.group(1)
                script_dict = json.loads(script)
                page = 1
                page_size = script_dict["pageData"]["data"]["baseInfo"]["page"]["pageSize"]
                page_total = script_dict["pageData"]["data"]["baseInfo"]["page"]["total"]
                tabid = script_dict["pageData"]["data"]["baseInfo"]["defaultActiveTab"]
                data_list_dict = script_dict["pageData"]["dataList"]
                data_list = data_list_dict[list(data_list_dict.keys())[0]]  # 获取字典第一个键值对的值
                print(f"正在拉取社区{community_id}:第{page}页，共有{page_total}页")
                self.extract_topic(data_list)
                page += 1
                time.sleep(5)
                while page <= page_total:
                    page_next_url = (f"https://bizapi.csdn.net/community-cloud/v1/community/listV2?"
                                     f"communityId={community_id}&noMore=false&page={page}&pageSize={page_size}&tabId={tabid}&type=1&viewType=0")
                    try:
                        text = self.get_html(page_next_url)
                    except Exception as e:
                        print(f'错误信息：{e}')
                        return
                    datalist = json.loads(text)["data"]["dataList"]
                    print(f"正在拉取社区{community_id}:第{page}页，共有{page_total}页")
                    self.extract_topic(datalist)
                    time.sleep(10)
                    page += 1
            else:
                with open(f'exception_log', 'wa', encoding='utf-8') as w:
                    w.writelines(f'爬取社区页面为空！社区名称：{clj["tagName"]}，社区URL：{clj["url"]}')

        with open(f'data/script.json', 'r') as r:
            script_dict = json.load(r)

        # page_total_test = 2  # 测试用
        data_list_dict = script_dict["pageData"]["dataList"]
        data_list = data_list_dict[list(data_list_dict.keys())[0]]  # 获取字典第一个键值对的值
        self.extract_topic(data_list)

        return

    def test(self):
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
    def extract_topic(self, data_list_dict):
        for data in data_list_dict:
            content = data["content"]
            topic = Topic()
            topic.title = content["topicTitle"]
            if content["description"]:
                topic.description = content["description"]
            else:
                topic.description = ''
            topic.id = content["contentId"]
            topic.create_time = datetime.strptime(content["createTime"], '%Y-%m-%d %H:%M:%S')
            topic.answer_nums = content["commentCount"]
            topic.click_nums = content["viewCount"]
            topic.praised_nums = content["diggNum"]
            topic.author = content["username"]

            # 如果话题存在，就更新，不存在，就新增
            existed_topics = Topic.select().where(Topic.id == topic.id)
            if existed_topics:
                topic.save()  # 这是更新操作，无法新增
            else:
                topic.save(force_insert=True)  # 强制插入

            # parse_topic(content["url"])
            # self.parse_author(f'https://blog.csdn.net/{content["username"]}')
        return

    def parse_author(self, url):
        # url = "https://blog.csdn.net/qq_33437675"
        author_id = url.split("/")[-1]
        # 获取用户的详情
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0',
        }
        res_text = requests.get(url, headers=headers).text
        user_text = re.search('window.__INITIAL_STATE__=(.*});</script>', res_text, re.IGNORECASE)
        if user_text:
            author = Author()
            data = user_text.group(1)
            data = json.loads(data)
            author.name = author_id
            base_info = data["pageData"]["data"]["baseInfo"]
            author.desc = base_info["seoModule"]["description"]

            interested = []
            if len(base_info["interestModule"]):
                tags = base_info["interestModule"][0]["tags"]
                for tag in tags:
                    interested.append(tag["name"])
            author.industry = ",".join(interested)
            if base_info["blogModule"]:
                author.id = base_info["blogModule"]["blogId"]

            if base_info["achievementModule"]["viewCount"]:
                author.click_nums = int(base_info["achievementModule"]["viewCount"].replace(",", ""))
            if base_info["achievementModule"]["rank"]:
                author.rate = int(base_info["achievementModule"]["rank"].replace(",", ""))
            if base_info["achievementModule"]["achievementList"]:
                author.parised_nums = int(
                    base_info["achievementModule"]["achievementList"][0]["variable"].replace(",", ""))
                author.answer_nums = int(
                    base_info["achievementModule"]["achievementList"][1]["variable"].replace(",", ""))
                author.forward_nums = int(
                    base_info["achievementModule"]["achievementList"][2]["variable"].replace(",", ""))
            if base_info["achievementModule"]["originalCount"]:
                author.original_nums = int(base_info["achievementModule"]["originalCount"].replace(",", ""))
            if base_info["achievementModule"]["fansCount"]:
                author.follower_nums = int(base_info["achievementModule"]["fansCount"].replace(",", ""))

            existed_author = Author.select().where(Author.id == author_id)
            if existed_author:
                author.save()
            else:
                author.save(force_insert=True)

            print(data)
        return


if __name__ == '__main__':
    url1 = "https://ai.csdn.net/?utm_source=bbs"
    spider = CsdnSpider()
    # spider.get_community()
    # print(spider.community)
    spider.parse_topic_list()
