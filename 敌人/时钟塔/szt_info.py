

from 时钟塔.szt_enemy_info import get_enemys

# 时钟塔对象
class Szt:
    def __init__(self, img_path = "", logo_path = "", 
        name = "",enemys = None):
        self.img_path = img_path                    # 时钟塔头像路径
        self.logo_path = logo_path                  # 时钟塔logo路径
        self.name = name                            # 时钟塔名
        self.enemys = enemys                        # 敌人对象列表


# 键：时钟塔名，值：对象
szts = {}

# 根据字典和敌人对象列表 创建并返回时钟塔对象
def creat_szt(szt_json, enemys):
    global szts

    img_path = szt_json['img_path']
    logo_path = szt_json['logo_path']
    name = szt_json['name']

    szt = Szt(
        img_path,
        logo_path,
        name,
        enemys
    )

    return szt

def get_szt_obj(szt_json):
    global szts
    name = szt_json['name']

    if name in szts:
        szt = szts[name]
    else:
        szt_enemys_json = szt_json['enemys']
        enemys = get_enemys(szt_enemys_json)
        szt = creat_szt(szt_json, enemys)
        szts[name] = szt

    return szt


def get_all_szt_obj(szts_json):
    for szt_name in szts_json:
        if szt_name not in szts:
            szt = get_szt_obj(szts_json[szt_name])
            

