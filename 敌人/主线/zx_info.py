import sys
import os

# 主线敌人
class Zx:
    def __init__(self, img_path = "", logo_path = "", 
        name = "",guide_path = ""
        ):
        self.img_path = img_path                    # 主线头像路径
        self.logo_path = logo_path                  # 主线ico路径
        self.name = name                            # 主线敌人名
        self.guide_path = guide_path                # 攻略图片路径



# 键：主线敌人名，值：对象
zxs = {}

# 根据字典 创建并返回主线敌人对象
def creat_zx(zx_json):
    global zxs

    img_path = zx_json['img_path']
    logo_path = zx_json['logo_path']
    name = zx_json['name']
    guide_path = zx_json['guide_path']

    zx = Zx(
        img_path,
        logo_path,
        name,
        guide_path,
    )

    return zx

def get_zx_obj(zx_json):
    name = zx_json['name']

    if name in zxs:
        zx = zxs[name]
    else:
        zx = creat_zx(zx_json)

    return zx


def get_all_zx_obj(zxs_json):
    for zx_name in zxs_json:
        if zx_name not in zxs:
            zx = get_zx_obj(zxs_json[zx_name])
            zxs[zx_name] = zx

