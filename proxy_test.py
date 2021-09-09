# -*- coding: utf-8 -*-
# Author : hejianxin
# Time : 2021/9/6 9:48 上午
# encoding:utf-8
import socket
import sys
import re
import os
import time
import select
import threading
#
# def client(conn, addr, proxy_port):
#     while True:
#         try:
#             data = conn.recv(4096)
#             s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             print("目的服务器：", addr)
#             s.connect((addr, proxy_port))
#             print('发给目的服务器数据：', b'123123')
#             s.sendall(data)     #将请求数据发给目的服务器
#             d = s.recv(40960)   #接收目的服务器发过来的数据
#             s.close()           #断开与目的服务器的连接
#             print('接收目的服务器数据:', d)
#             conn.sendall(d)     #发送给代理的客户端
#         except Exception as e:
#             print('代理的客户端异常：%s, ERROR:%s'%(addr, e))
#             conn.close()
#             break
#
#
# def serve(listen_port, proxy_addr, proxy_port):
#     # 创建
#     ip = "0.0.0.0"
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.bind((ip, listen_port))
#     s.listen(10)
#     print('proxy start...')
#     while True:
#         conn, addr = s.accept()
#         print('conn:', conn)
#         print("addr:", addr)
#         threading.Thread(target=client, args=(conn, proxy_addr, proxy_port)).start()
#
#         # try:
#         #     serve(listen_port, proxy_addr, proxy_port)
#         # except Exception as e:
#         #     print('代理服务器异常', e)
#
#
# serve(11112, '127.0.0.1', 8080)


HEADER_SIZE = 4096

host = '0.0.0.0'
port = 8000


#子进程进行socket 网络请求
def http_socket(client, addr):
    #创建 select 检测 fd 列表
    inputs = [client]
    outputs = []
    remote_socket = 0
    print("client connect:{0}:{1}".format(addr[0], addr[1]))
    while True:
        readable, writable, exceptional = select.select(inputs, outputs, inputs)
        try:
            for s in readable:
                if s is client:
                    #读取 http 请求头信息
                    request_header = s.recv(HEADER_SIZE)
                    if remote_socket is 0:
                        #拆分头信息
                        host_addr = request_header.split("\r\n")[1].split(":")
                        #如果未指定端口则为默认 80
                        if 2 == len(host_addr):
                            host_addr.append("80")
                        name, host, port = map(lambda x: x.strip(), host_addr)
                        #建立 socket tcp 连接
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.connect((host, int(port)))
                        remote_socket = sock
                        inputs.append(sock)
                    #发送原始请求头
                    remote_socket.sendall(request_header)
                else:
                    #接收数据并发送给浏览器
                    while True:
                        resp = s.recv(512)
                        if resp:
                            client.sendall(resp)
                    else:
                        break
        except Exception as e:
            print("http socket error {0}".format(e))


#创建socket对象
http_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    http_server.bind((host, port))
except:
    sys.exit("python proxy bind error ")

print("python proxy start")

http_server.listen(1024)

while True:
    client, addr = http_server.accept()
    http_thread = threading.Thread(target=http_socket, args=(client, addr))
    http_thread.start()
    time.sleep(1)

#关闭所有连接
http_server.close()
print("python proxy close")
