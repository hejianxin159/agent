# -*- coding: utf-8 -*-
# Author : hejianxin
# Time : 2021/9/6 10:54 上午
import sys
import threading
import multiprocessing
from models import db_session, ProxyTask
import logging
import optparse
from libs.config import *
import json
import socket
import hashlib


# 端口映射配置信息
REMOTE_IP = '192.168.99.160'
REMOTE_PORT = 55535
LOCAL_IP = '0.0.0.0'
LOCAL_PORT = 90


class PipeThread(threading.Thread):

    def __init__(self, source_fd, target_fd):
        super(PipeThread, self).__init__()
        self.logger = logging.getLogger('PipeThread')
        self.source_fd = source_fd
        self.target_fd = target_fd
        self.source_addr = self.source_fd.getpeername()
        self.target_addr = self.target_fd.getpeername()

    def run(self):
        while True:
            try:
                data = self.source_fd.recv(4096)
                if len(data) > 0:
                    self.logger.debug('read  %04i from %s:%d', len(data),
                                      self.source_addr[0], self.source_addr[1])
                    sent = self.target_fd.send(data)
                    self.logger.debug('write %04i to   %s:%d', sent,
                                      self.target_addr[0], self.target_addr[1])
                else:
                    break
            except socket.error:
                break
        self.logger.debug('connection %s:%d is closed.', self.source_addr[0],
                          self.source_addr[1])
        self.logger.debug('connection %s:%d is closed.', self.target_addr[0],
                          self.target_addr[1])
        self.source_fd.close()
        self.target_fd.close()


class Forwarder(multiprocessing.Process):

    def __init__(self, ip, port, remote_ip, remote_port, network_card, data_id, backlog=5):
        super(Forwarder, self).__init__()
        db_session.query(ProxyTask).filter(ProxyTask.id == data_id).update({"detail": "",
                                                                            "status": 0})
        db_session.commit()
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # SO_REUSEADDR 标志告诉内核将处于 TIME_WAIT 状态的本地套接字重新使用，而不必等到固有的超时到期。
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # 在客户端开启心跳维护
        self.port = port
        self.data_id = data_id
        self.status = False     # 判断需要去数据库改变数据不
        self.err_message = ""
        self.network_card = network_card
        self.sock.bind((ip, port))
        self.sock.listen(backlog)

    def run(self):
        # target_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # target_fd.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)  # 在客户端开启心跳维护
        # target_fd.bind(("0.0.0.0", self.port + 100))
        # target_fd.connect((self.remote_ip, self.remote_port))
        # target_fd.send(json.dumps({"probe_id": globals()["SENSOR"].id, "interface": self.network_card}).encode())
        while True:
            client_fd, client_addr = self.sock.accept()
            target_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_fd.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                target_fd.connect((self.remote_ip, self.remote_port))
            except Exception as e:
                e = str(e)
                if self.err_message != e:
                    self.err_message = e
                    self.status = True
            else:
                if self.err_message:
                    self.status = True
                self.err_message = ""
            if self.status:
                # 修改任务状态
                db_session.query(ProxyTask).filter(ProxyTask.id==self.data_id).update({"detail": self.err_message,
                                                                                       "status": 1 if self.err_message else 0})
                db_session.commit()
                self.status = False
            if self.err_message:
                continue
            data = target_fd.recv(1024).decode()

            if "random:" in data:
                key = data.split("random:")[1].strip()
            else:
                key = ""
            target_fd.send(hashlib.md5((globals()["SECRET"].key + key).encode()).hexdigest().encode())
            target_fd.send(json.dumps({"probe_id": globals()["PROBE"].id,
                                       "interface": self.network_card,
                                       "port": self.port
                                       }).encode())
            threads = [
                PipeThread(client_fd, target_fd),
                PipeThread(target_fd, client_fd)
            ]

            for t in threads:
                t.setDaemon(True)
                t.start()

    def __del__(self):
        self.sock.close()


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option(
        '-l', '--local-ip', dest='local_ip',
        help='Local IP address to bind to')
    parser.add_option(
        '-p', '--local-port',
        type='int', dest='local_port',
        help='Local port to bind to')
    parser.add_option(
        '-r', '--remote-ip', dest='remote_ip',
        help='Local IP address to bind to')
    parser.add_option(
        '-P', '--remote-port',
        type='int', dest='remote_port',
        help='Remote port to bind to')
    parser.add_option(
        '-v', '--verbose',
        action='store_true', dest='verbose',
        help='verbose')
    opts, args = parser.parse_args()

    if len(sys.argv) == 1 or len(args) > 0:
        opts.local_ip = LOCAL_IP
        opts.local_port = LOCAL_PORT
        opts.remote_ip = REMOTE_IP
        opts.remote_port = REMOTE_PORT
        # parser.print_help()

    if not (opts.local_ip and opts.local_port and opts.remote_ip and opts.remote_port):
        parser.print_help()
        exit()

    if opts.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.CRITICAL

    logging.basicConfig(level=log_level, format='%(name)-11s: %(message)s')
    forwarder = Forwarder(opts.local_ip, opts.local_port, opts.remote_ip, opts.remote_port)

    try:
        forwarder.run()
    except KeyboardInterrupt:
        print('quit')
        exit()
