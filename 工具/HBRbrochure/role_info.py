
from tools import load_json

# style_id[0:4]
team_id_names = {
    "1001":"31A", "1002":"31B", "1003":"31C", 
    "1004":"30G", "1005": "31D", "1006":"31E", 
    "1007":"31F", "1008":"31X", "1020":"Angel Beats!"
}

# style_id[0:5]
role_id_names = {
    "10011":"茅森月歌", "10012":"和泉由希", "10013":"逢川惠", "10014":"东城司", "10015":"朝仓可怜", "10017":"国见玉",
    "10021":"苍井绘里香", "10022":"水濑莓", "10023":"水濑李", "10024":"樋口圣华", "10025":"柊木梢", "10026":"白虎",
    "10031":"山胁", "10032":"樱庭星罗", "10033":"天音巫呼", "10034":"丰后弥生", "10035":"神崎阿迪尔海德", "10036":"佐月麻里",
    "10041":"白河结奈", "10042":"月城最中", "10043":"桐生美也", "10044":"菅原千惠", "10045":"小笠原绯雨", "10046":"藏里见",
    "10051":"二阶堂三乡", "10052":"石井色叶", "10053":"命吹雪", "10054":"室伏理沙", "10055":"伊达朱里", "10056":"瑞原蓝娜",
    "10061":"大岛一千子", "10062":"大岛二以奈", "10063":"大岛三野里", "10064":"大岛四叶草", "10065":"大岛五十铃", "10066":"大岛六宇亚",
    "10071":"柳美音", "10072":"丸山奏多", "10073":"华村诗纪", "10074":"松岗绮罗路", "10075":"夏目祈", "10076":"黑泽真希",
    "10081":"卡罗尔利帕", "10082":"李映夏", "10083":"艾琳雷德梅因", "10084":"芙里提卡芭拉克莉希南", "10085":"玛丽亚黛安杰利斯", "10086":"夏洛特斯可波夫斯加",
    "10201":"立华奏", "10202":"仲村百合", "10203":"入江美雪"
}


style_id_all_infos = {}
# 加载资源文件
def load_resources():
    global style_id_all_infos
    if style_id_all_infos:
        return
    style_id_all_infos = load_json("./工具/HBRbrochure/style_id_all_infos.json")


# 根据风格id获取角色名
def GetRoleNameByStyleId(style_id):
    role_name = role_id_names[style_id[0:5]]
    return role_name

# 根据风格id获取队伍名
def GetTeamNameByStyleId(style_id):
    team_name = team_id_names[style_id[0:4]]
    return team_name

# 根据风格名获取风格id
def GetStyleIdByStyleName(style_id_infos, style_name):
    for style_id, style_info in style_id_infos.items():
        if style_name == style_info["style_name"]:
            return style_id

# 根据风格id获取风格名
def GetStyleNameByStyleId(style_id_infos, style_id):
    return style_id_infos[style_id]["style_name"]

# 根据风格id获取角色属性
def GetCharacterRoleByStyleId(style_id_infos, style_id):
    return style_id_infos[style_id]["character_role"]

# 根据风格id获取元素属性
def GetElementTypeByStyleId(style_id_infos, style_id):
    return style_id_infos[style_id]["element_type"]

# 根据风格id获取武器属性
def GetWeaponTypeByStyleId(style_id_infos, style_id):
    return style_id_infos[style_id]["weapon_type"]

# 根据风格id获取当前等级
def GetCurrentLevelByStyleId(style_id_infos, style_id):
    return style_id_infos[style_id]["current_level"]

# 根据风格id获取最大等级
def GetMaximumLevelByStyleId(style_id_infos, style_id):
    return style_id_infos[style_id]["maximum_level"]

# 根据风格id获取上限突破
def GetLimitBreakLevelByStyleId(style_id_infos, style_id):
    return style_id_infos[style_id]["limit_break_level"]
