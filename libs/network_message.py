# encoding: utf-8
# -*- coding: utf8 -*-
import netifaces
import winreg as wr
from models import db_session, Task
from sqlalchemy.sql import func
from libs.config import *


def ifnames():
    gateway_info = {j[1]: j[0] for i, v in netifaces.gateways().items() if isinstance(v, list) for j in v}
    # 获取所有网络接口卡的键值
    interfaces = netifaces.interfaces()
    # 存放网卡键值与键值名称的字典
    key_name = {}
    try:
        # 建立链接注册表，"HKEY_LOCAL_MACHINE"，None表示本地计算机
        reg = wr.ConnectRegistry(None, wr.HKEY_LOCAL_MACHINE)
        # 打开r'SYSTEM\CurrentControlSet\Control\Network\{4d36e972-e325-11ce-bfc1-08002be10318}'，固定的
        reg_key = wr.OpenKey(reg, r'SYSTEM\CurrentControlSet\Control\Network\{4d36e972-e325-11ce-bfc1-08002be10318}')
    except :
        return '路径出错或者其他问题，请仔细检查'

    for interface in interfaces:
        try:
            # 尝试读取每一个网卡键值下对应的Name
            reg_subkey = wr.OpenKey(reg_key, interface + r'\Connection')
            # 如果存在Name，写入key_name字典
            address = netifaces.ifaddresses(f'{interface}').get(netifaces.AF_INET)
            if address:
                address = address[0]
                gateway = gateway_info.get(interface)
                address["gateway"] = gateway if gateway else ""
                key_name[wr.QueryValueEx(reg_subkey, 'Name')[0]] = address

        except FileNotFoundError:
            pass
    return key_name


def task_status():
    network_card = db_session.query(Task.network_card,
                                    func.max(Task.id)).group_by(Task.network_card)
    error_proxy_task = {}
    normal_proxy_task = {}
    for network_item in network_card:
        network_name = network_item[0]
        proxy_list = db_session.query(Task).filter(Task.id == network_item[1]).first().proxy_task
        # 找出有问题的代理
        for proxy in proxy_list:
            error_message = proxy.detail
            if error_message:
                error_proxy_task[network_name] = error_message

        for proxy in proxy_list:
            if not proxy.detail and network_name not in error_proxy_task:
                normal_proxy_task[network_name] = ""
    return error_proxy_task, normal_proxy_task


def combination_message():
    error_task, normal_proxy = task_status()
    network_list = []
    proxy_list = []
    for network_card, network_info in ifnames().items():
        network_list.append({
            "interface": network_card,
            "ip": network_info["addr"],
            "netmask": network_info["netmask"],
            "gateway": network_info["gateway"]
                             })
    for k, v in error_task.items():
        proxy_list.append({"interface": k, "enabled": False})
    for k, v in normal_proxy.items():
        proxy_list.append({"interface": k, "enabled": True})

    return {
        "probe_id": globals()["SENSOR"].id,
        "network": network_list,
        "proxy": proxy_list
    }


if __name__ == '__main__':
    print(combination_message())
