# -*- coding: utf-8 -*-
# Author : hejianxin
# Time : 2021/9/13 9:42 上午
import grpc
from grpcd import sensor_pb2
from grpcd import sensor_pb2_grpc
from libs.config import *
from libs.network_message import combination_message


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel(f'{globals()["GRPC"].host}:{globals()["GRPC"].port}') as channel:
        print(f'{globals()["GRPC"].host}:{globals()["GRPC"].port}')
        # pass
        stub = sensor_pb2_grpc.InnerSensorStub(channel)
        message = combination_message()
        print(message)
        response = stub.UploadProbeInfo(sensor_pb2.ProbeInfo(**message))
        print(response)


if __name__ == '__main__':
    run()
    run()
