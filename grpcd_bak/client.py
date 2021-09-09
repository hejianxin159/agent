# -*- coding: utf-8 -*-
# Author : hejianxin
# Time : 2021/9/3 4:36 下午
import grpc
import time
import msg_pb2
import msg_pb2_grpc


def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('192.168.99.160:50051') as channel:
        # pass
        stub = msg_pb2_grpc.MsgServiceStub(channel)
        response = stub.GetMsg(msg_pb2.MsgRequest(name='world'))
    # print("Client received: " + response.msg)


# while True:
#     time.sleep(5)
run()
