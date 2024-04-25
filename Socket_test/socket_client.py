# 可以实现socket_server和socket_client 一来一回不间断通信，通信内容通过键盘输入
# 多线程


import socket
client = socket.socket()
client.connect(('127.0.0.1', 8000))

while True:
    server_data = ""

    # keyboard input
    print("please input data:")
    input_data = input()
    client.send(input_data.encode("utf8"))
    server_tmp_data = client.recv(1024)
    if server_tmp_data:
        server_data += server_tmp_data.decode("utf8")
        if server_tmp_data.decode("utf8").endswith("#"):
            print("server response: {}".format(server_data.encode("utf8")))
            continue
    else:
        break
# client.close()

