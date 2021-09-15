# -*- coding: utf-8 -*-
# Author : hejianxin
# Time : 2021/8/27 3:43 下午
# import socket
# import requests
# from multiprocessing import Process
# import random
#
#
# urls = ["http://192.168.99.238:90/", "http://192.168.99.238:91/"]
#
#
# def test_url():
#     url = random.choice(urls)
#     print(requests.get(url).content)
#
#
#
# for i in range(100):
#     Process(target=test_url).start()
# #
# import time
#
# time.sleep(3)
# def net_is_used(port, ip='127.0.0.1'):
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     try:
#         s.connect((ip, port))
#         s.shutdown(2)
#         print('sorry, %s:%d is used' % (ip,port))
#         return False
#     except Exception as e:
#         print('hahahaha %s:%d is unused' % (ip,port))
#         print(e)
#         return True
#
#
# print(net_is_used(10023))
import socket
from libs.config import *
from proxy.proxy_server import Forwarder
import json

remote_ip = '192.168.99.160'
remote_port = 55535
local_ip = '0.0.0.0'
local_port = 91

# forwarder = Forwarder(local_ip, local_port, remote_ip, remote_port, 11)
# forwarder.start()
# import time
target_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
target_fd.bind(("0.0.0.0", 91))
#
target_fd.connect((remote_ip, remote_port))
target_fd.send(json.dumps({"probe_id": globals()["SENSOR"].id, "interface": "VLAN"}).encode())

# while True:
#     pass

# while True:
#     target_fd.send(b'1111')
#     time.sleep(10)
# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.bind((local_ip, local_port))
# sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock2.bind((local_ip, 92))

