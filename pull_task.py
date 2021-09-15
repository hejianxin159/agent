# -*- coding: utf-8 -*-
# Author : hejianxin
# Time : 2021/9/6 10:15 上午
import grpc
import time
from libs.config import *
from grpcd import sensor_pb2
from grpcd import sensor_pb2_grpc
# from grab_package import CreatePackageTool
import json
from models import db_session, Task, ProxyTask, GrabTask
from sqlalchemy.sql import func


class DispatchTask:
    def __init__(self, task_data):
        task_data = json.loads(task_data)
        self.task_data = task_data
        self.task_detail = task_data["detail"]
        self.task_id = task_data["task_id"]
        self.run()

    def run(self):
        task_type = self.task_data["type"]
        if task_type == "no_task":
            return
        # self.task = db_session.query(Task).filter(Task.task_id == self.task_id).first()
        # if not self.task and task_type not in ["control_proxy", "delete_proxy"]:
        if task_type not in ["control_proxy", "delete_proxy"]:
            self.task = Task(task_id=self.task_id, network_card=self.task_detail["interface"])
            db_session.add(self.task)
            db_session.commit()
        getattr(self, task_type)()

    def delete_proxy(self):
        # self.task.status = "delete_proxy"
        # db_session.add(self.task)
        # db_session.commit()
        # db_session.commit()
        self.operate_task("delete_proxy", False)

    def create_proxy(self):
        self.save_listen_data("create_proxy")

    def modify_proxy(self):
        self.save_listen_data("modify_proxy")

    def control_proxy(self):
        enable = False
        if self.task_detail["enabled"]:
            enable = True
        # self.task.status = "control_proxy"
        # self.task.enable = enable
        # db_session.add(self.task)
        # db_session.commit()
        self.operate_task("control_proxy", enable)

    def save_listen_data(self, action):
        # interface = self.task_detail["interface"]
        self.task.status = action
        ports = []
        for item in self.task_detail["proxy_rule"]:
            proxy_host = item["proxy_host"]
            proxy_port = item["proxy_port"]
            listen_port = item["port"]
            db_session.add(ProxyTask(proxy_port=proxy_port,
                                     proxy_host=proxy_host,
                                     port=listen_port,
                                     task_id=self.task.id))
            ports.append(listen_port)

        grab_task = GrabTask(port=ports,
                             task_id=self.task.id)
        db_session.add(grab_task)
        db_session.commit()

    def operate_task(self, enum_status, status=False):
        interface = self.task_detail["interface"]
        max_id = db_session.query(func.Max(Task.id)).filter(Task.network_card==interface).first()[0]
        task = db_session.query(Task).filter(Task.id==max_id).first()
        task.enable = status
        task.status = enum_status
        db_session.add(task)
        db_session.commit()


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel(f'{globals()["GRPC"].host}:{globals()["GRPC"].port}') as channel:
        # pass
        stub = sensor_pb2_grpc.InnerSensorStub(channel)
        response = stub.FetchTask(sensor_pb2.Flag(probe_id=globals()["PROBE"].id))
    for info in response.task:
        DispatchTask(info)


# while True:
#     run()
#     time.sleep(5)




# data = '''
# ['{"type": "delete_proxy", "detail": {"interface": "Intel(R) Wireless-AC 9260 160MHz", "probe_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}, "task_id": "b63e81f9-f7fb-4617-928b-74f94c42d8c3"}', '{"type": "create_proxy", "detail": {"interface": "Intel(R) Wireless-AC 9260 160MHz", "proxy_rule": [{"info": "HTTPS", "proxy_port": 55535, "proxy_host": "192.168.99.160", "type": 1, "port": 90},{"info": "HTTPS", "proxy_port": 55135, "proxy_host": "192.168.99.160", "type": 1, "port": 91}], "probe_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}, "task_id": "b63e8119-f7fb-4657-928b-74f94c42d8c3"}', '{"type": "delete_proxy", "detail": {"interface": "Intel(R) Wireless-AC 9260 160MHz", "probe_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}, "task_id": "b63e81f9-f7fb-5157-928b-74f94c42d8c3"}', '{"type": "create_proxy", "detail": {"interface": "Intel(R) Wireless-AC 9260 160MHz", "proxy_rule": [{"info": "HTTPS", "proxy_port": 55535, "proxy_host": "192.168.99.160", "type": 1, "port": 90}], "probe_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}, "task_id": "b63e18f9-f7fb-4657-928b-74f94c42d8c3"}', '{"type": "delete_proxy", "detail": {"interface": "Intel(R) Wireless-AC 9260 160MHz", "probe_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}, "task_id": "b63e81f9-f7fb-4657-911b-74f94c42d8c3"}', '{"type": "create_proxy", "detail": {"interface": "Intel(R) Wireless-AC 9260 160MHz", "proxy_rule": [{"info": "HTTPS", "proxy_port": 55535, "proxy_host": "192.168.99.160", "type": 1, "port": 90}], "probe_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}, "task_id": "b63e81f9-f7fb-4657-928b-74f91c42d8c3"}']
#
# # '''
# # data = '''
# # ['{"type": "control_proxy", "detail": {"interface": "Intel(R) Wireless-AC 9260 160MHz", "enabled": true, "probe_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}, "task_id": "a63e81f9-f7fb-4657-928b-74f94c42d8c3"}']
# # '''
#
# for i in eval(data):
#     print(i)
#     # DispatchTask(i)
# #
data = """{"type": "create_proxy", "detail": {"interface": "WLAN", "proxy_rule": [{"info": "HTTPS", "proxy_port": 55535, "proxy_host": "192.168.99.160", "type": 1, "port": 90}], "probe_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}, "task_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}"""
data2 = """{"type": "control_proxy", "detail": {"interface": "WLAN", "enabled": true, "probe_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}, "task_id": "b63e81f9-f7fb-4657-928b-74f94c42d1c3"}"""

for i in [data, data2]:
    print(i)
    DispatchTask(i)
