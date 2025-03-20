import sys
import os

# 棱镜战敌人
class Ljz:
    def __init__(self, img_path = "", logo_path = "", 
        name = "",guide_path = ""
        ):
        self.img_path = img_path                    # 棱镜战头像路径
        self.logo_path = logo_path                  # 棱镜战ico路径
        self.name = name                            # 棱镜战敌人名
        self.guide_path = guide_path                # 攻略图片路径



# 键：棱镜战敌人名，值：对象
ljzs = {}

# 根据字典 创建并返回棱镜战敌人对象
def creat_ljz(ljz_json):
    global ljzs

    img_path = ljz_json['img_path']
    logo_path = ljz_json['logo_path']
    name = ljz_json['name']
    guide_path = ljz_json['guide_path']

    ljz = Ljz(
        img_path,
        logo_path,
        name,
        guide_path,
    )

    return ljz

def get_ljz_obj(ljz_json):
    name = ljz_json['name']

    if name in ljzs:
        ljz = ljzs[name]
    else:
        ljz = creat_ljz(ljz_json)

    return ljz


def get_all_ljz_obj(ljzs_json):
    for ljz_name in ljzs_json:
        if ljz_name not in ljzs:
            ljz = get_ljz_obj(ljzs_json[ljz_name])
            ljzs[ljz_name] = ljz

