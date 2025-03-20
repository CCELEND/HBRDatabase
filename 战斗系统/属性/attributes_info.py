import sys
import os
import threading
from threading import Lock
from tools import load_json

# 属性
class Attribute:
    def __init__(self, path = "", 
        name = "",en="",description = ""
        ):
        self.path = path                    # 属性图路径
        self.name = name                    # 属性名
        self.en = en                        # 英文
        self.description = description      # 描述

attributes_json = {}
# 加载资源文件
def load_resources():
    global attributes_json
    if attributes_json:
        return
    attributes_json = load_json("./战斗系统/属性/attributes.json")

# 键：属性名，值：对象
attributes = {}

# 根据字典 创建并返回属性对象
def creat_attribute(attribute_json):

    path = attribute_json['path']
    name = attribute_json['name']
    en = attribute_json['en']
    description = attribute_json['description']

    attribute = Attribute(
        path,
        name,
        en,
        description
    )

    return attribute

def get_attribute_obj(attribute_json):
    name = attribute_json['name']

    if name in attributes:
        attribute = attributes[name]
    else:
        attribute = creat_attribute(attribute_json)
        attributes[name] = attribute

    return attribute

def get_all_attribute_obj():

    load_resources()

    if not attributes_json:
        return

    if len(attributes) == len(attributes_json):
        return

    for attribute_name in attributes_json:
        if attribute_name not in attributes:
            attribute = get_attribute_obj(attributes_json[attribute_name])
            attributes[attribute_name] = attribute
            



