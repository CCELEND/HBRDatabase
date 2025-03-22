import sys
import os
import threading
from threading import Lock
from tools import load_json

# 饰品
class Jewelry:
    def __init__(self, path = "", 
        name = "",en="",type="",description = "",rarity="",location=""
        ):
        self.path = path                    # 饰品图路径
        self.name = name                    # 饰品名
        self.en = en                        # 英文
        self.type = type                    # 饰品类型
        self.description = description      # 描述
        self.rarity = rarity                # 稀有度
        self.location = location            # 获取地点

jewelrys_type_json = {}
# 加载资源文件
def load_type_resources():
    global jewelrys_type_json
    if jewelrys_type_json:
        return
    jewelrys_type_json = load_json("./持有物/饰品/jewelrys_type.json")


# 根据字典 创建并返回饰品对象
def creat_jewelry(jewelry_json):

    path = jewelry_json['path']
    name = jewelry_json['name']
    en = jewelry_json['en']
    type = jewelry_json['type']
    description = jewelry_json['description']
    rarity = jewelry_json['rarity']
    location = jewelry_json['location']

    jewelry = Jewelry(
        path,
        name,
        en,
        type,
        description,
        rarity,
        location
    )

    return jewelry

# 获取饰品对象
def get_jewelry_obj(jewelry_json):
    name = jewelry_json['name']

    if name in jewelry_categories["all"]:
        jewelry = jewelry_categories["all"][name]
    else:
        jewelry = creat_jewelry(jewelry_json)

    return jewelry

def get_jewelrys_obj(jewelry_type_json):

    jewelrys = {}

    jewelry_json_path = jewelry_type_json['resource']
    jewelrys_json = load_json(jewelry_json_path)

    for jewelry_name in jewelrys_json:
        if jewelry_name not in jewelry_categories["all"]:
            jewelry = get_jewelry_obj(jewelrys_json[jewelry_name])
            set_jewelry_category(jewelry)

    jewelrys = jewelry_categories[jewelry_type_json['name']]
    return jewelrys


# 使用字典存储所有饰品分类
jewelry_categories = {
    "rarity": {
        "1": {},
        "2": {},
        "3": {},
        "4": {},
        "5": {}
    },
    "吊饰": {},
    "耳坠": {},
    "戒指": {},
    "手环": {},
    "项链": {},
    "专武": {},
    "光球": {},
    "all":{}
}

# 根据风格对象的稀有度、武器属性和元素属性分类存储样式
def set_jewelry_category(jewelry):

    # 按稀有度分类
    if jewelry.rarity in jewelry_categories["rarity"]:
        jewelry_categories["rarity"][jewelry.rarity][jewelry.name] = jewelry

    # 按职能分类
    if jewelry.type in "吊饰" :
        jewelry_categories["吊饰"][jewelry.name] = jewelry

    elif jewelry.type in "耳坠":
        jewelry_categories["耳坠"][jewelry.name] = jewelry

    elif jewelry.type in "戒指":
        jewelry_categories["戒指"][jewelry.name] = jewelry

    elif jewelry.type in "手环":
        jewelry_categories["手环"][jewelry.name] = jewelry

    elif jewelry.type in "项链":
        jewelry_categories["项链"][jewelry.name] = jewelry

    elif jewelry.type in "专武":
        jewelry_categories["专武"][jewelry.name] = jewelry

    else:
        jewelry_categories["光球"][jewelry.name] = jewelry

    if jewelry.name in jewelry_categories["all"]:
        return
    jewelry_categories["all"][jewelry.name]  = jewelry

            



