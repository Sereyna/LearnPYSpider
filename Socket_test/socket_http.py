"""
socket 客户端
对百度发起HTTP请求，获取HTTP response
"""
import socket

http_client = socket.socket()
http_client.connect(("127.0.0.1", 8000))
http_client.send("GET / HTTP/1.1\r\nConnection:close\r\n\r\n".encode("utf8"))
data = b""
while True:
    tmp_data = http_client.recv(1024)
    if tmp_data:
        data += tmp_data
    else:
        break

print(data.decode("utf8"))
