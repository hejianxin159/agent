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
from models import db_session, ListenTask


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
        getattr(self, task_type)()
        db_session.query(ListenTask).filter(ListenTask.task_id != self.task_id).update({"status": 1})
        db_session.commit()

    def delete_proxy(self):
        db_session.query(ListenTask).filter(ListenTask.network_card == self.task_detail["interface"]).\
            update({"status": True})
        db_session.commit()

    def create_proxy(self):
        self.save_listen_data("create_proxy")

    def modify_proxy(self):
        self.save_listen_data("modify_proxy")

    def control_proxy(self):
        status = {"enable": False}
        if self.task_detail["enabled"]:
            status["enable"] = True
        db_session.query(ListenTask).filter(ListenTask.network_card == self.task_detail["interface"],
                                            ListenTask.status == False). \
            update(status)
        db_session.commit()

    def save_listen_data(self, action):
        interface = self.task_detail["interface"]
        proxy_dict = {}
        for item in self.task_detail["proxy_rule"]:
            proxy_host = item["proxy_host"]
            proxy_port = item["proxy_port"]
            listen_port = item["port"]
            get_key = proxy_host + '-' + str(proxy_port)
            exist = proxy_dict.get(get_key)
            if not exist:
                proxy_dict[get_key] = [listen_port]
            else:
                exist.append(listen_port)
        for key, port in proxy_dict.items():
            key_split = key.split("-")
            proxy_host = key_split[0]
            proxy_port = key_split[1]
            # exist_data = db_session.query(ListenTask).filter(
            #     ListenTask.network_card == interface,
            #     ListenTask.proxy_host == proxy_host,
            #     ListenTask.proxy_port == proxy_port
            # ).first()
            # if exist_data:
            #     exist_data.task_id = self.task_id
            #     exist_data.operate_type = action
            #     exist_data.port = port
            # else:
            exist_data = ListenTask(port=port, network_card=interface,
                                    proxy_port=proxy_port, proxy_host=proxy_host,
                                    operate_type=action, task_id=self.task_id)
            db_session.add(exist_data)
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




data = '''
['{"type": "delete_proxy", "detail": {"interface": "Intel(R) Wireless-AC 9260 160MHz", "probe_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}, "task_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}', '{"type": "create_proxy", "detail": {"interface": "Intel(R) Wireless-AC 9260 160MHz", "proxy_rule": [{"info": "HTTPS", "proxy_port": 55535, "proxy_host": "192.168.99.160", "type": 1, "port": 90},{"info": "HTTPS", "proxy_port": 55135, "proxy_host": "192.168.99.160", "type": 1, "port": 91}], "probe_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}, "task_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}', '{"type": "delete_proxy", "detail": {"interface": "Intel(R) Wireless-AC 9260 160MHz", "probe_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}, "task_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}', '{"type": "create_proxy", "detail": {"interface": "Intel(R) Wireless-AC 9260 160MHz", "proxy_rule": [{"info": "HTTPS", "proxy_port": 55535, "proxy_host": "192.168.99.160", "type": 1, "port": 90}], "probe_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}, "task_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}', '{"type": "delete_proxy", "detail": {"interface": "Intel(R) Wireless-AC 9260 160MHz", "probe_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}, "task_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}', '{"type": "create_proxy", "detail": {"interface": "Intel(R) Wireless-AC 9260 160MHz", "proxy_rule": [{"info": "HTTPS", "proxy_port": 55535, "proxy_host": "192.168.99.160", "type": 1, "port": 90}], "probe_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}, "task_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}']

# '''
# data = '''
# ['{"type": "control_proxy", "detail": {"interface": "Intel(R) Wireless-AC 9260 160MHz", "enabled": true, "probe_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}, "task_id": "b63e81f9-f7fb-4657-928b-74f94c42d8c3"}']
# '''

for i in eval(data):
    # print(i)
    DispatchTask(i)

