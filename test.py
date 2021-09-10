# -*- coding: utf-8 -*-
# Author : hejianxin
# Time : 2021/8/27 3:43 下午
import socket
import requests
from multiprocessing import Process
import random


urls = ["http://192.168.99.238:90/", "http://192.168.99.238:91/"]


def test_url():
    url = random.choice(urls)
    print(requests.get(url).content)



for i in range(100):
    Process(target=test_url).start()
#
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
