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
# import socket
# from libs.config import *
# from proxy.proxy_server import Forwarder
# import json
# #
# remote_ip = '192.168.99.177'
# remote_port = 555
# local_ip = '0.0.0.0'
# local_port = 90
#
# forwarder = Forwarder(local_ip, local_port, remote_ip, remote_port, "VLAN")
# forwarder.start()
# import time
# target_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# target_fd.bind(("0.0.0.0", 91))
#
# target_fd.connect((remote_ip, remote_port))
# target_fd.send(json.dumps({"probe_id": globals()["SENSOR"].id, "interface": "VLAN"}).encode())

# while True:
#     pass

# while True:
#     target_fd.send(b'1111')
#     time.sleep(10)
# sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.bind((local_ip, local_port))
# sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock2.bind((local_ip, 92))
#tcp server
remote_ip = '192.168.99.177'
remote_port = 555
local_ip = '0.0.0.0'
local_port = 90


# -*- coding: utf-8 -*-

import socket
import asyncore


class Receiver(asyncore.dispatcher):
    def __init__(self, conn):
        asyncore.dispatcher.__init__(self, conn)
        self.from_remote_buffer = b''
        self.to_remote_buffer = b''
        self.sender = None

    def handle_connect(self):
        pass

    def handle_read(self):
        read = self.recv(4096)
        # print '%04i -->'%len(read)
        self.from_remote_buffer += read

    def writable(self):
        return len(self.to_remote_buffer) > 0

    def handle_write(self):
        sent = self.send(self.to_remote_buffer)
        # print '%04i <--'%sent
        self.to_remote_buffer = self.to_remote_buffer[sent:]

    def handle_close(self):
        self.close()
        if self.sender:
            self.sender.close()


class Sender(asyncore.dispatcher):
    def __init__(self, receiver, remoteaddr, remoteport):
        asyncore.dispatcher.__init__(self)
        self.receiver = receiver
        receiver.sender = self
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((remoteaddr, remoteport))

    def handle_connect(self):
        pass

    def handle_read(self):
        read = self.recv(4096)
        # print '<-- %04i'%len(read)
        self.receiver.to_remote_buffer += read

    def writable(self):
        return len(self.receiver.from_remote_buffer) > 0

    def handle_write(self):
        sent = self.send(self.receiver.from_remote_buffer)
        # print '--> %04i'%sent
        self.receiver.from_remote_buffer = self.receiver.from_remote_buffer[sent:]

    def handle_close(self):
        self.close()
        self.receiver.close()


class Forwarder(asyncore.dispatcher):
    def __init__(self, ip, port, remoteip, remoteport, backlog=5):
        asyncore.dispatcher.__init__(self)
        self.remoteip = remoteip
        self.remoteport = remoteport
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((ip, port))
        self.listen(backlog)

    def handle_accept(self):
        conn, addr = self.accept()
        # print '--- Connect --- '
        self.log_info('Connected from %s:%s to %s:%s' % (addr[0], addr[1], self.remoteip, self.remoteport))
        Sender(Receiver(conn), self.remoteip, self.remoteport)

# if __name__ == '__main__':
#     f = Forwarder('127.0.0.1', 5089, '127.0.0.1', 55535)
#     asyncore.loop()
import binascii
import chardet

data = b'\xff\xff\xff\xff\xff\xffb\x93>H\x8b\x9e\x08\x06\x00\x01\x08\x00\x06\x04\x00\x01b\x93>H\x8b\x9e\xa9\xfeH\xcc\x00\x00\x00\x00\x00\x00\xa9\xfe\x10;\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
# chardit1 = chardet.detect(data)#cf_r为要查看的编码
# print(chardit1)

# # print(data)
# print(binascii.hexlify(data))
#
# data_2 = str(data, encoding='ascii')
# print(data_2)
# print(binascii.hexlify(eval(data_2)))


#!/usr/bin/env python

from scapy.all import *
#
# # VARIABLES
interface = 'en0'
filter_bpf = "port 8000"


def pkt_change(pkt):
    # print(pkt["Ethernet"].type)
    print(pkt["Ethernet"].src)
    print(pkt["Ethernet"].dst)
    print(binascii.hexlify(eval(str(pkt))))

    print('-'*20)

# start sniffing
print("Start Sniffing")
sniff(iface=interface, filter=filter_bpf, store=0, prn=pkt_change, count=10)
#
