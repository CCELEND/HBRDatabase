

# 时之修炼场敌人
class Szxlc:
    def __init__(self, img_path = "", logo_path = "", 
        name = "",guide_path = ""
        ):
        self.img_path = img_path                    # 时之修炼场头像路径
        self.logo_path = logo_path                  # 时之修炼场ico路径
        self.name = name                            # 时之修炼场敌人名
        self.guide_path = guide_path                # 攻略图片路径



# 键：时之修炼场敌人名，值：对象
szxlcs = {}

# 根据字典 创建并返回时之修炼场敌人对象
def creat_szxlc(szxlc_json):
    global szxlcs

    img_path = szxlc_json['img_path']
    logo_path = szxlc_json['logo_path']
    name = szxlc_json['name']
    guide_path = szxlc_json['guide_path']

    szxlc = Szxlc(
        img_path,
        logo_path,
        name,
        guide_path,
    )

    return szxlc

def get_szxlc_obj(szxlc_json):
    name = szxlc_json['name']

    if name in szxlcs:
        szxlc = szxlcs[name]
    else:
        szxlc = creat_szxlc(szxlc_json)

    return szxlc


def get_all_szxlc_obj(szxlcs_json):
    for szxlc_name in szxlcs_json:
        if szxlc_name not in szxlcs:
            szxlc = get_szxlc_obj(szxlcs_json[szxlc_name])
            szxlcs[szxlc_name] = szxlc

