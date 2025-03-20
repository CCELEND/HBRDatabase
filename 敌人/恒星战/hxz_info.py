import sys
import os

# 恒星战敌人
class Hxz:
    def __init__(self, img_path = "", img_path_enemy="", logo_path = "", 
        name = "",guide_path = ""
        ):
        self.img_path = img_path                    # 恒星战头像路径
        self.img_path_enemy = img_path_enemy        # 恒星战敌人头像路径
        self.logo_path = logo_path                  # 恒星战ico路径
        self.name = name                            # 恒星战敌人名
        self.guide_path = guide_path                # 攻略图片路径



# 键：恒星战敌人名，值：对象
hxzs = {}

# 根据字典 创建并返回恒星战敌人对象
def creat_hxz(hxz_json):
    global hxzs

    img_path = hxz_json['img_path']
    img_path_enemy = hxz_json['img_path_enemy']
    logo_path = hxz_json['logo_path']
    name = hxz_json['name']
    guide_path = hxz_json['guide_path']

    hxz = Hxz(
        img_path,
        img_path_enemy,
        logo_path,
        name,
        guide_path,
    )

    return hxz

def get_hxz_obj(hxz_json):
    name = hxz_json['name']

    if name in hxzs:
        hxz = hxzs[name]
    else:
        hxz = creat_hxz(hxz_json)

    return hxz


def get_all_hxz_obj(hxzs_json):
    for hxz_name in hxzs_json:
        if hxz_name not in hxzs:
            hxz = get_hxz_obj(hxzs_json[hxz_name])
            hxzs[hxz_name] = hxz

