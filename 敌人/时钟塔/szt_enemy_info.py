import sys
import os

class SztEnemy:
    def __init__(self, img_path = "",
        name = "",border = "", 
        DP="",HP="",weakness="",resist=""):
        self.img_path = img_path                    # 时钟塔头像路径
        self.name = name                            # 时钟塔敌人名
        self.border = border                        # 属性值
        self.DP = DP
        self.HP = HP
        self.weakness = weakness
        self.resist = resist


# 键：时钟塔敌人名，值：对象
szt_enemys = {}

# 根据字典 创建并返回时钟塔敌人对象
def creat_szt_enemy(szt_enemy_json):

    img_path = szt_enemy_json['img_path']
    name = szt_enemy_json['name']
    border = szt_enemy_json['border']
    DP = szt_enemy_json['DP']
    HP = szt_enemy_json['HP']
    weakness = szt_enemy_json['weakness']
    resist = szt_enemy_json['resist']

    szt_enemy = SztEnemy(
        img_path,
        name,
        border,
        DP,HP,
        weakness,resist
    )

    return szt_enemy


# 获取时钟塔敌人对象列表
def get_enemys(szt_enemys_json):
    enemys = []
    for szt_enemy_name in szt_enemys_json:
        szt_enemy_json = szt_enemys_json[szt_enemy_name]
        szt_enemy_obj = get_szt_enemy_obj(szt_enemy_json)
        enemys.append(szt_enemy_obj)

    return enemys

# 获取时钟塔敌人对象
def get_szt_enemy_obj(szt_enemy_json):
    global szt_enemys
    name = szt_enemy_json['name']

    if name in szt_enemys:
        szt_enemy = szt_enemys[name]
    else:
        szt_enemy = creat_szt_enemy(szt_enemy_json)
        szt_enemys[name] = szt_enemy

    return szt_enemy


