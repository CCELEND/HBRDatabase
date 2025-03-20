import sys
import os

# 高分挑战敌人
class Gftz:
    def __init__(self, img_path = "", logo_path = "", 
        name = "",guide_path = ""
        ):
        self.img_path = img_path                    # 高分挑战头像路径
        self.logo_path = logo_path                  # 高分挑战ico路径
        self.name = name                            # 高分挑战敌人名
        self.guide_path = guide_path                # 攻略图片路径



# 键：高分挑战敌人名，值：对象
gftzs = {}

# 根据字典 创建并返回高分挑战敌人对象
def creat_gftz(gftz_json):
    global gftzs

    img_path = gftz_json['img_path']
    logo_path = gftz_json['logo_path']
    name = gftz_json['name']
    guide_path = gftz_json['guide_path']

    gftz = Gftz(
        img_path,
        logo_path,
        name,
        guide_path,
    )

    return gftz

def get_gftz_obj(gftz_json):
    name = gftz_json['name']

    if name in gftzs:
        gftz = gftzs[name]
    else:
        gftz = creat_gftz(gftz_json)

    return gftz


def get_all_gftz_obj(gftzs_json):
    for gftz_name in gftzs_json:
        if gftz_name not in gftzs:
            gftz = get_gftz_obj(gftzs_json[gftz_name])
            gftzs[gftz_name] = gftz

