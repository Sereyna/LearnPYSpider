# 可以实现socket_server和socket_client 一来一回不间断通信，通信内容通过键盘输入
# 多线程

import socket
import threading

server = socket.socket()
# 绑定IP和端口
server.bind(('0.0.0.0', 8000))
# 监听
server.listen()


def handle_sock():
    while True:
        data = ""

        # 接收来自client的信息
        tm_data = sock.recv(1024)
        if tm_data:
            data += tm_data.decode("utf8")

            # 如果来自client的信息以‘#’结尾，就中断接收开始打印
            if tm_data.decode("utf8").endswith("#"):
                print("client data: {}".format(data.encode("utf8")))
                print("please input data:")
                input_data = input()
                sock.send(input_data.encode("utf8"))
        else:
            break

# 多线程，每来一个client请求链接，就创建一个线程
while True:
    # 阻塞等待连接，建立链接，获取到client地址
    sock, addr = server.accept()

    # 创建线程，并指定执行方法handle_sock()
    client_thread = threading.Thread(target=handle_sock(), args=(sock, addr))

    # 开始执行
    client_thread.start()
