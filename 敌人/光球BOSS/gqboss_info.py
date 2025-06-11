
# 光球BOSS敌人
class Gqboss:
    def __init__(self, img_path = "", logo_path = "", 
        name = "",guide_path = ""
        ):
        self.img_path = img_path                    # 光球BOSS头像路径
        self.logo_path = logo_path                  # 光球BOSSico路径
        self.name = name                            # 光球BOSS敌人名
        self.guide_path = guide_path                # 攻略图片路径



# 键：光球BOSS敌人名，值：对象
gqbosss = {}

# 根据字典 创建并返回光球BOSS敌人对象
def creat_gqboss(gqboss_json):
    global gqbosss

    img_path = gqboss_json['img_path']
    logo_path = gqboss_json['logo_path']
    name = gqboss_json['name']
    guide_path = gqboss_json['guide_path']

    gqboss = Gqboss(
        img_path,
        logo_path,
        name,
        guide_path,
    )

    return gqboss

def get_gqboss_obj(gqboss_json):
    name = gqboss_json['name']

    if name in gqbosss:
        gqboss = gqbosss[name]
    else:
        gqboss = creat_gqboss(gqboss_json)

    return gqboss


def get_all_gqboss_obj(gqbosss_json):
    for gqboss_name in gqbosss_json:
        if gqboss_name not in gqbosss:
            gqboss = get_gqboss_obj(gqbosss_json[gqboss_name])
            gqbosss[gqboss_name] = gqboss

