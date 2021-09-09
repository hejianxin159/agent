# # -*- coding: utf-8 -*-
# # Author : hejianxin
# # Time : 2021/9/6 2:20 下午
import os
from sqlalchemy import create_engine
import enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, SmallInteger, Enum, JSON, BOOLEAN
from sqlalchemy.orm import sessionmaker, scoped_session


engine = create_engine(f'sqlite:///{os.path.join(os.path.dirname(__file__), "foo.db")}')

session = sessionmaker(bind=engine)
db_session = scoped_session(session)
Base = declarative_base()


class OperateStatusEnum(enum.Enum):
    create_proxy = 1
    modify_proxy = 2
    delete_proxy = 3
    control_proxy = 4


class DataStatusEnum(enum.Enum):
    success = 1
    fail = 2
    init = 3


class ListenTask(Base):
    __tablename__ = "listen_task"
    id = Column(Integer, primary_key=True)
    network_card = Column(String(64), comment="网卡名字")
    port = Column(JSON, comment="监听端口")
    proxy_port = Column(Integer, comment="代理端口")
    proxy_host = Column(String(32), comment="代理地址")
    task_id = Column(String(36), comment="任务id")
    operate_type = Column(Enum(OperateStatusEnum), comment="操作方式")
    data_status = Column(Enum(DataStatusEnum), comment="是否成功状态", default="init")
    # doing = Column(BOOLEAN, default=1)
    enable = Column(BOOLEAN, default=1, comment="是否开启")
    status = Column(BOOLEAN, default=0, comment="是否删除")


if __name__ == '__main__':
    Base.metadata.create_all(engine)
    # task = ListenTask(network_card='123',
    #                port=[1, 2],
    #                proxy_port=123,
    #                proxy_host='121',
    #                operate_status="add",
    #                data_status="success")
    # session.add(task)
    # session.commit()
    # a = db_session.query(ListenTask).filter(ListenTask.id == 2).first()
    ListenTask.__table__.drop(engine)
    ListenTask.__table__.create(engine)

#
# from sqlalchemy import Column, Integer, String, create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.declarative import declarative_base
#
# import uuid, random
#
# Base = declarative_base()
#
#
# class ApplyCode(Base):
#     __tablename__ = 'applycode'
#     id = Column(Integer, primary_key=True)
#     code = Column('code', String)
#     status = Column(Integer, default=1)
#     uid = Column('uid', String)
#
#
# engine = create_engine('sqlite:///data.db', echo=True)
# Database = sessionmaker(bind=engine)
#
# if __name__ == '__main__':
#     Base.metadata.create_all(engine)
#
#     db = Database()
#     # try:
#     # 	for x in range(17):
#     # 		code = ''
#     # 		for i in xrange(3): code += random.choice('abcdefghijklmnopqrstuvwxyz'.upper())
#     # 		for i in xrange(3): code += random.choice('0123456789')
#     # 		app = ApplyCode(code=code,uid=str(uuid.uuid4()))
#     # 		db.add(app)
#     # 	db.commit()
#     # except Exception,e:
#     # 	print e
#     # 	db.rollback()
#
#     idlist = [144, 143, 142, 141, 140]
#     query = db.query(ApplyCode)
#     query = query.filter(ApplyCode.id.in_(idlist))
#     query = query.order_by(-ApplyCode.id)
#     data = query.all()
#     # print data.id
#     # print data.code
#     # print data.uid
#     print(data)
#     for x in data:
#         print(x.id)
