import requests

res = requests.get("http://www.baidu.com")
print(res.headers)
