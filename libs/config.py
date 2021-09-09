# -*- coding: utf-8 -*-
# Author : hejianxin
# Time : 2021/8/27 4:44 下午
import configparser
import os
base_dir = os.path.dirname(os.path.dirname(__file__))
config_dir = os.path.join(base_dir, 'config')
config = configparser.ConfigParser()
# config.read(CONFIG_FILE)
config_list = ['config.ini', 'test.ini']

# 扫描配置文件，将配置文件中的变量定义到全局
for conf in map(lambda x: os.path.join(config_dir, x), config_list):
    config.read(conf)

sections = config.sections()
for section in sections:
    sec = section
    pairs = config.items(section)
    globals()[sec.upper()] = type(sec.title(), (), {i[0]: i[1] for i in pairs})


