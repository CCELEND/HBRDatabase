import sys
import os
import threading
from threading import Lock
from tools import load_json

# 饰品
class jewelry:
    def __init__(self, path = "", 
        name = "",en="",description = "",hit=""
        ):
        self.path = path                    # 饰品图路径
        self.name = name                    # 饰品名
        self.en = en                        # 英文
        self.description = description      # 描述
        self.rarity = rarity

jewelrys_json = {}
# 加载资源文件
def load_resources():
    global jewelrys_json
    if jewelrys_json:
        return
    jewelrys_json = load_json("./战斗系统/饰品/jewelrys.json")

# 键：饰品名，值：对象
jewelrys = {}

# 根据字典 创建并返回饰品对象
def creat_jewelry(jewelry_json):

    path = jewelry_json['path']
    name = jewelry_json['name']
    en = jewelry_json['en']
    description = jewelry_json['description']
    hit = jewelry_json['hit']

    jewelry = jewelry(
        path,
        name,
        en,
        description,
        hit
    )

    return jewelry

def get_jewelry_obj(jewelry_json):
    name = jewelry_json['name']

    if name in jewelrys:
        jewelry = jewelrys[name]
    else:
        jewelry = creat_jewelry(jewelry_json)
        jewelrys[name] = jewelry

    return jewelry

def get_all_jewelry_obj():

    load_resources()

    if not jewelrys_json:
        return

    if len(jewelrys) == len(jewelrys_json):
        return

    for jewelry_name in jewelrys_json:
        if jewelry_name not in jewelrys:
            jewelry = get_jewelry_obj(jewelrys_json[jewelry_name])
            jewelrys[jewelry_name] = jewelry
            



