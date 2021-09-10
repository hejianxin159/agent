# -*- coding: utf-8 -*-
# Author : hejianxin
# Time : 2021/9/6 10:54 上午
import sys
import threading
import multiprocessing
import logging
import optparse
from libs.config import *
import socket


# 端口映射配置信息
REMOTE_IP = '192.168.99.238'
REMOTE_PORT = 99
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
        # self.source_fd.close()
        # self.target_fd.close()


class Forwarder(multiprocessing.Process):

    def __init__(self, ip, port, remote_ip, remote_port, backlog=5):
        super(Forwarder, self).__init__()
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # SO_REUSEADDR 标志告诉内核将处于 TIME_WAIT 状态的本地套接字重新使用，而不必等到固有的超时到期。
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ip, port))
        self.sock.listen(backlog)

    def run(self):
        while True:
            client_fd, client_addr = self.sock.accept()
            target_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_fd.connect((self.remote_ip, self.remote_port))

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
