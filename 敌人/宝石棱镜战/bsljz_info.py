import sys
import os

# 宝石棱镜战敌人
class Bsljz:
    def __init__(self, img_path = "", logo_path = "", 
        name = "",guide_path = ""
        ):
        self.img_path = img_path                    # 宝石棱镜战头像路径
        self.logo_path = logo_path                  # 宝石棱镜战ico路径
        self.name = name                            # 宝石棱镜战敌人名
        self.guide_path = guide_path                # 攻略图片路径



# 键：宝石棱镜战敌人名，值：对象
bsljzs = {}

# 根据字典 创建并返回宝石棱镜战敌人对象
def creat_bsljz(bsljz_json):
    global bsljzs

    img_path = bsljz_json['img_path']
    logo_path = bsljz_json['logo_path']
    name = bsljz_json['name']
    guide_path = bsljz_json['guide_path']

    bsljz = Bsljz(
        img_path,
        logo_path,
        name,
        guide_path,
    )

    return bsljz

def get_bsljz_obj(bsljz_json):
    name = bsljz_json['name']

    if name in bsljzs:
        bsljz = bsljzs[name]
    else:
        bsljz = creat_bsljz(bsljz_json)

    return bsljz


def get_all_bsljz_obj(bsljzs_json):
    for bsljz_name in bsljzs_json:
        if bsljz_name not in bsljzs:
            bsljz = get_bsljz_obj(bsljzs_json[bsljz_name])
            bsljzs[bsljz_name] = bsljz

