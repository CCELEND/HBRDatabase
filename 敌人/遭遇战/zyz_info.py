
# 遭遇战敌人
class Zyz:
    def __init__(self, img_path = "", logo_path = "", 
        name = "",guide_path = ""
        ):
        self.img_path = img_path                    # 遭遇战头像路径
        self.logo_path = logo_path                  # 遭遇战ico路径
        self.name = name                            # 遭遇战敌人名
        self.guide_path = guide_path                # 攻略图片路径



# 键：遭遇战敌人名，值：对象
zyzs = {}

# 根据字典 创建并返回遭遇战敌人对象
def creat_zyz(zyz_json):
    global zyzs

    img_path = zyz_json['img_path']
    logo_path = zyz_json['logo_path']
    name = zyz_json['name']
    guide_path = zyz_json['guide_path']

    zyz = Zyz(
        img_path,
        logo_path,
        name,
        guide_path,
    )

    return zyz

def get_zyz_obj(zyz_json):
    name = zyz_json['name']

    if name in zyzs:
        zyz = zyzs[name]
    else:
        zyz = creat_zyz(zyz_json)

    return zyz


def get_all_zyz_obj(zyzs_json):
    for zyz_name in zyzs_json:
        if zyz_name not in zyzs:
            zyz = get_zyz_obj(zyzs_json[zyz_name])
            zyzs[zyz_name] = zyz

