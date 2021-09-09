# -*- coding: utf-8 -*-
# Author : hejianxin
# Time : 2021/8/27 3:43 下午
import grpc
from grpcd import sensor_pb2
from grpcd import sensor_pb2_grpc
import json
from scapy.all import sniff
from libs.config import *
from models import db_session, ListenTask
from sqlalchemy.sql import func
import binascii
import datetime
from itertools import chain
import time
from multiprocessing import Process
import socket
from proxy.proxy_server import Forwarder

'''
只捕获某个IP主机进行交互的流量：host 192.168.1.124
只捕获某个MAC地址主机的交互流量：ether src host 00:87:df:98:65:d8
只捕获来源于某一IP的主机流量：src host 192.168.1.125
只捕获去往某一IP的主机流量：dst host 192.168.1.154
只捕获80端口的流量：port 80
只捕获除80端口以外的其他端口流量：!port 80
只捕获ICMP流量：ICMP
只捕获源地址为192.168.1.125且目的端口为80的流量：src host 192.168.1.125 && dst port 80
'''
ip_type = {
    6: "TCP",
    17: "UDP"
}
process_dict = {}
listening_port_dict = {}
proxy_dict = {}


class CreatePackageTool(Process):
    flag = {
        1: "ARP",
        2: "IP",
        3: "IPv6"
    }
    ethernet_type = {
        2054: "ARP",
        2048: "IP",
        34525: "IPv6"
    }

    def __init__(self, port, iface):
        super().__init__()
        self.port = port
        self.iface = iface

    def run(self):
        self.local_ip = [item[4][0] for item in socket.getaddrinfo(socket.gethostname(), None)]
        sniff(filter=self.port, iface=self.iface, prn=self.parser_package)

    def parser_package(self, packet):
        ethernet = packet["Ethernet"]
        protocol = ''
        self.result = {
            "sensor_id": globals()["SENSOR"].id,
            "interface": self.iface,
            "src_ethernet": "",
            "dst_ethernet": "",
            "src_ip": "",
            "dst_ip": "",
            "src_port": "",
            "dst_port": "",
            "protocol": "",
            "action": "",
            "desc": "",
            "payload": binascii.hexlify(str(packet.payload).encode()),
            "layer": len(packet.layers()),
            "raw_log": binascii.hexlify(str(packet).encode()),
            "detail": "",
            "require_analysis": True,
            "create_time": "",
            "type": 0
        }
        # self.result["layer"] = len(packet.layers())
        # self.result["payload"] = binascii.hexlify(str(packet.payload).encode())
        # self.result["raw_log"] = binascii.hexlify(str(packet).encode())
        if ethernet.type == 2048:
            # IPV4
            address_item = packet["IP"]
            self.parser_mac_ip(address_item, "IP")
            protocol = ip_type.get(address_item.proto, "")
            self.parser_port(protocol, packet)
        elif ethernet.type == 34525:
            # IPV6
            address_item = packet["IPv6"]
            self.parser_mac_ip(address_item, "IPv6")
            protocol = ip_type.get(address_item.nh, "")
            self.parser_port(protocol, packet)
        elif ethernet.type == 2054:
            # ARP
            protocol = "ARP"
            self.parser_mac_ip(packet["ARP"], "ARP")
        else:
            packet.show()
        if ethernet.type in self.ethernet_type:
            # mac address
            self.result["src_ethernet"] = ethernet.src
            self.result["dst_ethernet"] = ethernet.dst
        self.result["protocol"] = protocol
        self.result["datetime"] = datetime.datetime.now()
        self.parser_type()
        print(
            self.result["sensor_id"], self.result["dst_ip"], self.result["src_ip"], self.result["type"]
        )
        put_flow_message(self.result)

    def parser_mac_ip(self, packet, packet_type):
        # ip address
        if packet_type == "ARP":
            self.result["src_ip"] = packet.psrc
            self.result["dst_ip"] = packet.pdst
        else:
            self.result["src_ip"] = packet.src
            self.result["dst_ip"] = packet.dst

    def parser_port(self, protocol, packet):
        # port
        if protocol:
            self.result["require_analysis"] = False
        if protocol == "TCP":
            self.result["src_port"] = packet["TCP"].sport
            self.result["dst_port"] = packet["TCP"].dport
        elif protocol == "UDP":
            self.result["src_port"] = packet["UDP"].sport
            self.result["dst_port"] = packet["UDP"].dport

    def parser_type(self):
        # 0: 不进入会话，1: 请求日志，2: 响应日志
        if self.result["dst_ip"] in self.local_ip:
            self.result["type"] = 1
        elif self.result["src_ip"] in self.local_ip:
            self.result["type"] = 2


def put_task_message(task_id, status, detail=""):
    with grpc.insecure_channel(f'{globals()["GRPC"].host}:{globals()["GRPC"].port}') as channel:
        # pass
        stub = sensor_pb2_grpc.InnerSensorStub(channel)
        response = stub.FetchTask(sensor_pb2.TaskStatus(task_id=task_id, status=status, detail=detail))


def put_flow_message(message):
    with grpc.insecure_channel(f'{globals()["GRPC"].host}:{globals()["GRPC"].port}') as channel:
        # pass
        stub = sensor_pb2_grpc.InnerSensorStub(channel)
        response = stub.FetchTask(sensor_pb2.ProbeTrafficLog(**message))


# listen_port = "port 80"
# CreatePackageTool(listen_port, globals()["NETWORK"].name).run()

def net_is_used(port, ip='127.0.0.1'):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, port))
        s.shutdown(2)
        print('sorry, %s:%d is used' % (ip,port))
        return False
    except Exception as e:
        print('hahahaha %s:%d is unused' % (ip,port))
        print(e)
        return True


def start_listen(network_name, all_port, task_id):
    listening_port_dict[network_name] = all_port
    template = "port {} or " * (len(all_port))
    filter_rule = template.format(*all_port)[:-4]
    try:
        process = CreatePackageTool(filter_rule, network_name)
        process_dict[network_name] = process
        process.start()
    except Exception as e:
        print(e)
        put_task_message(task_id, "FAIL", str(e))
    else:
        put_task_message(task_id, "SUCCESS")


def stop_listen(network_name, task_id, is_push):
    exist_process = process_dict.get(network_name)
    if exist_process:
        try:
            exist_process.terminate()
        except Exception as e:
            if is_push:
                put_task_message(task_id, "FAIL", str(e))
        else:
            if is_push:
                put_task_message(task_id, "SUCCESS")


def start_proxy(remote_port, remote_ip, local_port, local_ip="0.0.0.0"):
    if net_is_used(local_port):
        process = Forwarder(local_ip, local_port, remote_ip, remote_port)
        process.start()
        proxy_dict["port"] = process


def stop_proxy(port):
    exist_process = proxy_dict.get(port)
    if exist_process:
        exist_process.terminate()


def main():
    while True:
        # 获取所有网卡，和最新的一条任务
        network_card = db_session.query(ListenTask.network_card,
                                        func.max(ListenTask.id)).group_by(ListenTask.network_card)

        for network_item in network_card:
            network_name = network_item[0]
            # 获取最新的一条任务
            search_task = db_session.query(ListenTask).filter(ListenTask.id == network_item[1]).first()
            task_id = search_task.task_id
            if search_task.enable == False or search_task.status == True:
                # 任务删除或者暂停
                stop_listen(network_name, task_id, True)
                exist_listening = listening_port_dict.get(network_name)
                if exist_listening:
                    del listening_port_dict[network_name]
            else:
                # 找出当前任务的所有需要监听的端口
                all_task = db_session.query(ListenTask.port).filter(ListenTask.task_id == task_id,
                                                                    ListenTask.status == False,
                                                                    ListenTask.enable == True)
                all_port = list(chain(*chain(*all_task)))
                exist_listen_port = listening_port_dict.get(network_name)
                if not exist_listen_port:
                    # 新增抓包任务
                    start_listen(network_name, all_port, task_id)
                else:
                    if exist_listen_port != all_port:
                        # 任务有变化时, 停止之前的任务
                        stop_listen(network_name, task_id, False)
                        if all_port != []:
                            start_listen(network_name, all_port, task_id)

        time.sleep(5)
        db_session.commit()


if __name__ == '__main__':
    main()




















