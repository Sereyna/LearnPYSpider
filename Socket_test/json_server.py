# socket服务端
# 可在浏览器中访问127.0.0.1：8000
import socket
import json
import threading
server = socket.socket()
# 绑定到0.0.0.0:8000端口上
server.bind(('0.0.0.0', 8000))
server.listen()

def handle_sock(sock, addr):
    while True:
        # recv方法是阻塞的
        tmp_data = sock.recv(1024)
        print(tmp_data.decode("utf8"))
        response_template = '''HTTP/1.1 200 OK
Content-Type: application/json
Access-Control-Allow-Origin:http://localhost:63342

{}

'''
        data = [
            {
                "name":"django打造在线教育",
                "teacher":"bobby",
                "url":"https://coding.imooc.com/class/78.html"
            },
            {
                "name": "python高级编程",
                "teacher": "bobby",
                "url": "https://coding.imooc.com/class/200.html"
            },
            {
                "name": "scrapy分布式爬虫",
                "teacher": "bobby",
                "url": "https://coding.imooc.com/class/92.html"
            },
            {
                "name": "django rest framework打造生鲜电商",
                "teacher": "bobby",
                "url": "https://coding.imooc.com/class/131.html"
            },
            {
                "name": "tornado从入门到精通",
                "teacher": "bobby",
                "url": "https://coding.imooc.com/class/290.html"
            },
        ]
        sock.send(response_template.format(json.dumps(data)).encode("utf8"))
        sock.close()
        break

# 获取客户端连接并启动线程去处理
while True:
    # 阻塞等待连接
    sock, addr = server.accept()

    # 启动一个线程去处理新的用户连接
    client_thread = threading.Thread(target=handle_sock, args=(sock, addr))
    client_thread.start()