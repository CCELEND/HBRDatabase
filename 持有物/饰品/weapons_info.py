import sys
import os
import threading
from threading import Lock
from tools import load_json

# 武器
class Weapon:
    def __init__(self, path = "", 
        name = "",en="",description = "",hit=""
        ):
        self.path = path                    # 武器图路径
        self.name = name                    # 武器名
        self.en = en                        # 英文
        self.description = description      # 描述
        self.hit = hit                      # hit

weapons_json = {}
# 加载资源文件
def load_resources():
    global weapons_json
    if weapons_json:
        return
    weapons_json = load_json("./战斗系统/武器/weapons.json")

# 键：武器名，值：对象
weapons = {}

# 根据字典 创建并返回武器对象
def creat_weapon(weapon_json):

    path = weapon_json['path']
    name = weapon_json['name']
    en = weapon_json['en']
    description = weapon_json['description']
    hit = weapon_json['hit']

    weapon = Weapon(
        path,
        name,
        en,
        description,
        hit
    )

    return weapon

def get_weapon_obj(weapon_json):
    name = weapon_json['name']

    if name in weapons:
        weapon = weapons[name]
    else:
        weapon = creat_weapon(weapon_json)
        weapons[name] = weapon

    return weapon

def get_all_weapon_obj():

    load_resources()

    if not weapons_json:
        return

    if len(weapons) == len(weapons_json):
        return

    for weapon_name in weapons_json:
        if weapon_name not in weapons:
            weapon = get_weapon_obj(weapons_json[weapon_name])
            weapons[weapon_name] = weapon
            



