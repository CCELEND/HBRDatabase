import sys
import os

# 异时层敌人
class Ysc:
    def __init__(self, img_path = "", logo_path = "", 
        name = "", en = "", nicknames = "", description = "",
        guide_path = ""
        ):
        self.img_path = img_path                    # 异时层头像路径
        self.logo_path = logo_path                  # 异时层ico路径
        self.name = name                            # 异时层敌人名
        self.en = en                                # 英文
        self.nicknames = nicknames                  # 别名列表
        self.description = description              # 描述
        self.guide_path = guide_path                # 攻略图片路径



# 键：异时层敌人名，值：对象
yscs = {}

# 根据字典 创建并返回异时层敌人对象
def creat_ysc(ysc_json):
    global yscs

    img_path = ysc_json['img_path']
    logo_path = ysc_json['logo_path']
    name = ysc_json['name']
    en = ysc_json['en']
    nicknames = ysc_json['nicknames']
    description = ysc_json['description']
    guide_path = ysc_json['guide_path']

    ysc = Ysc(
        img_path,
        logo_path,
        name,
        en,
        nicknames,
        description,
        guide_path,
    )

    return ysc

def get_ysc_obj(ysc_json):
    name = ysc_json['name']

    if name in yscs:
        ysc = yscs[name]
    else:
        ysc = creat_ysc(ysc_json)

    return ysc


def get_all_ysc_obj(yscs_json):
    for ysc_name in yscs_json:
        if ysc_name not in yscs:
            ysc = get_ysc_obj(yscs_json[ysc_name])
            yscs[ysc_name] = ysc

