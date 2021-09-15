# -*- coding: utf-8 -*-
# Author : hejianxin
# Time : 2021/8/27 3:43 下午
import grpc
from grpcd import sensor_pb2
from grpcd import sensor_pb2_grpc
import json
from scapy.all import sniff
from libs.config import *
from models import db_session, Task, ProxyTask, GrabTask
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
exist_proxy_dict = {}


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
            "probe_id": globals()["PROBE"].id,
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
            "payload": binascii.hexlify(eval(str(packet.payload))),
            "layer": len(packet.layers()),
            "raw_log": binascii.hexlify(eval(str(packet))),
            "detail": "",
            "require_analysis": True,
            "created_time": datetime.datetime.fromtimestamp(time.time()).isoformat(),
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
        self.parser_type()
        print(
            self.result["probe_id"], self.result["dst_ip"], self.result["src_ip"], self.result["type"]
        )
        # print(self.result)
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
            self.result["src_port"] = str(packet["TCP"].sport)
            self.result["dst_port"] = str(packet["TCP"].dport)
        elif protocol == "UDP":
            self.result["src_port"] = str(packet["UDP"].sport)
            self.result["dst_port"] = str(packet["UDP"].dport)

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
        response = stub.UploadTaskStatus(sensor_pb2.TaskStatus(task_id=task_id, status=status, detail=detail))


def put_flow_message(message):
    with grpc.insecure_channel(f'{globals()["GRPC"].host}:{globals()["GRPC"].port}') as channel:
        # pass
        stub = sensor_pb2_grpc.InnerSensorStub(channel)
        response = stub.UploadProbeTrafficLog(sensor_pb2.ProbeTrafficLog(**message))


# listen_port = "port 80"
# CreatePackageTool(listen_port, globals()["NETWORK"].name).run()

def net_is_used(port, ip='127.0.0.1'):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, port))
        s.shutdown(2)
        print('sorry, %s:%d is used' % (ip, port))
        return False
    except Exception as e:
        print('%s:%d is unused' % (ip, port))
        return True


def start_listen(network_name, all_port, data_id):
    exist_listen_port = listening_port_dict.get(network_name)
    if exist_listen_port and exist_listen_port == all_port:
        return
    stop_listen(network_name, data_id)
    template = "port {} or " * (len(all_port))
    filter_rule = template.format(*all_port)[:-4]
    try:
        process = CreatePackageTool(filter_rule, network_name)
        process.start()
    except Exception as e:
        print(e)
        db_session.query(GrabTask).filter(GrabTask.id == data_id).update({"detail": str(e)})
        db_session.commit()
        # put_task_message(task_id, "SUCCESS")
    else:
        process_dict[network_name] = process
        listening_port_dict[network_name] = all_port


def stop_listen(network_name, data_id):
    exist_process = process_dict.get(network_name)
    if exist_process:
        try:
            exist_process.terminate()
            del process_dict[network_name]
        except Exception as e:
            db_session.query(GrabTask).filter(GrabTask.id == data_id).update({"detail": str(e)})
            db_session.commit()


def start_proxy(data_id, remote_port, remote_ip, local_port, network_card, local_ip="0.0.0.0"):
    # 开启代理
    find_key = f'{remote_port}-{remote_ip}-{local_port}'
    exist_proxy = exist_proxy_dict.get(local_port)
    if exist_proxy and exist_proxy == find_key:
        # 不处理，和上一轮的代理是没变化的
        return
    # 停止之前的代理
    stop_proxy(remote_port, remote_ip, local_port, data_id)

    if net_is_used(local_port):
        process = Forwarder(local_ip, local_port, remote_ip, remote_port, network_card, data_id)
        try:
            process.start()
        except Exception as e:
            db_session.query(ProxyTask).filter(ProxyTask.id == data_id).update({"detail": str(e),
                                                                                "status": 1})
        else:
            proxy_dict[local_port] = process
            exist_proxy_dict[local_port] = find_key
    else:
        db_session.query(ProxyTask).filter(ProxyTask.id == data_id).update({"detail": "port is using",
                                                                            "status": 1})
    db_session.commit()


def stop_proxy(remote_port, remote_ip, port, data_id):
    find_key = f'{remote_port}-{remote_ip}-{port}'
    exist_process = proxy_dict.get(find_key)
    if exist_process:
        try:
            exist_process.terminate()
            del process_dict[find_key]
        except Exception as e:
            db_session.query(ProxyTask).filter(ProxyTask.id == data_id).update({"detail": str(e)})
            db_session.commit()


def main():
    while True:
        # 获取所有网卡最新的一条任务
        network_card = db_session.query(Task.network_card,
                                        func.max(Task.id)).group_by(Task.network_card)

        for network_item in network_card:
            network_name = network_item[0]
            # 获取最新的一条任务
            search_task = db_session.query(Task).filter(Task.id == network_item[1]).first()
            task_id = search_task.task_id
            data_id = network_item[1]
            grab_task = db_session.query(GrabTask.id, GrabTask.port).filter(GrabTask.task_id == data_id).first()
            proxy_task = search_task.proxy_task
            if search_task.enable == False or search_task.status == "delete_proxy":
                # 任务删除或者暂停
                stop_listen(network_name, grab_task[0])
                exist_listening = listening_port_dict.get(network_name)
                if exist_listening:
                    del listening_port_dict[network_name]
                # 关闭所有代理
                for proxy_task_item in proxy_task:
                    stop_proxy(proxy_task_item.proxy_port, proxy_task_item.proxy_host,
                               proxy_task_item.port, proxy_task_item.id)
            else:
                # 找出当前任务的所有需要监听的端口
                all_port = grab_task[1]
                # 开启抓包任务
                start_listen(network_name, all_port, grab_task[0])
                # 开启代理
                for proxy_task_item in proxy_task:
                    start_proxy(proxy_task_item.id, proxy_task_item.proxy_port,
                                proxy_task_item.proxy_host, proxy_task_item.port,
                                search_task.network_card)
        #
        time.sleep(5)
        db_session.commit()


if __name__ == '__main__':
    main()




















