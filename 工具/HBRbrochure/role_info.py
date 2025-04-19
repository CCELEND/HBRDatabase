
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

# 有一些风格的 id 不确定是否正确（有些角色的风格 id 并不连续。。。。）
style_id_all_infos = {
# 31A
    "1001103":{
        "style_name":"闪光的电气脉冲", "character_role":"攻击者", "element_type":"无", "weapon_type":"斩",
    },
    "1001104":{
        "style_name":"黎明的感性之魂", "character_role":"攻击者", "element_type":"火", "weapon_type":"斩",
    },
    "1001105":{
        "style_name":"红衣主教的残响", "character_role":"攻击者", "element_type":"光", "weapon_type":"斩",
    },
    "1001107":{
        "style_name":"夜间巡航护卫", "character_role":"攻击者", "element_type":"雷", "weapon_type":"斩",
    },
    "1001203":{
        "style_name":"终焉炮火", "character_role":"破盾者", "element_type":"无", "weapon_type":"突",
    },
    "1001204":{
        "style_name":"夏椿、闪耀的夜明星", "character_role":"破盾者", "element_type":"火", "weapon_type":"突",
    },
    "1001205":{
        "style_name":"夜间巡航随从", "character_role":"破盾者", "element_type":"雷", "weapon_type":"突",
    },
    "1001207":{
        "style_name":"舞动的轮回", "character_role":"破盾者", "element_type":"光", "weapon_type":"突",
    },
    "1001208":{
        "style_name":"红玉待君来", "character_role":"破盾者", "element_type":"暗", "weapon_type":"突",
    },
    "1001303":{
        "style_name":"窒息强击", "character_role":"减益者", "element_type":"无", "weapon_type":"打",
    },
    "1001305":{
        "style_name":"一夜之梦", "character_role":"减益者", "element_type":"光", "weapon_type":"打",
    },
    "1001306":{
        "style_name":"心跃欣舞Fuel", "character_role":"减益者", "element_type":"火", "weapon_type":"打",
    },
    "1001307":{
        "style_name":"薄暮时分·飞升", "character_role":"减益者", "element_type":"暗", "weapon_type":"打",
    },
    "1001403":{
        "style_name":"谨记死亡的美少女", "character_role":"增益者", "element_type":"火", "weapon_type":"突",
    },
    "1001404":{
        "style_name":"盛夏的祈祷", "character_role":"增益者", "element_type":"火", "weapon_type":"突",
    },
    "1001405":{
        "style_name":"秘密特工·静谧", "character_role":"增益者", "element_type":"光", "weapon_type":"突",
    },
    "1001503":{
        "style_name":"红莲月华之杀戮镰刀", "character_role":"破坏者", "element_type":"无", "weapon_type":"斩",
    },
    "1001504":{
        "style_name":"猩红叛乱", "character_role":"破坏者", "element_type":"火", "weapon_type":"斩",
    },
    "1001505":{
        "style_name":"秘密特工·摧毁", "character_role":"破坏者", "element_type":"光", "weapon_type":"斩",
    },
    "1001703":{
        "style_name":"气势一闪天使水手", "character_role":"治疗者", "element_type":"无", "weapon_type":"斩",
    },
    "1001705":{
        "style_name":"魔法之国的元素精灵", "character_role":"治疗者", "element_type":"火", "weapon_type":"斩",
    },
    "1001706":{
        "style_name":"猛冲！！空气贝斯", "character_role":"治疗者", "element_type":"雷", "weapon_type":"斩",
    },
    "1001707":{
        "style_name":"梦幻珊瑚", "character_role":"治疗者", "element_type":"光", "weapon_type":"斩",
    },
    "1001708":{
        "style_name":"薄暮时分·追忆", "character_role":"增益者", "element_type":"无", "weapon_type":"斩",
    },

# 31B
    "1002103":{
        "style_name":"心绪inspire", "character_role":"防御者", "element_type":"无", "weapon_type":"打",
    },
    "1002104":{
        "style_name":"传递Miracle", "character_role":"防御者", "element_type":"雷", "weapon_type":"打",
    },
    "1002105":{
        "style_name":"闪耀·究极偶像", "character_role":"防御者", "element_type":"火", "weapon_type":"打",
    },
    "1002203":{
        "style_name":"嬉笑间坠入爱河", "character_role":"攻击者", "element_type":"雷", "weapon_type":"突",
    },
    "1002204":{
        "style_name":"你的眼眸属于我", "character_role":"攻击者", "element_type":"火", "weapon_type":"突",
    },
    "1002303":{
        "style_name":"残光", "character_role":"攻击者", "element_type":"雷", "weapon_type":"斩",
    },
    "1002304":{
        "style_name":"炽热的暗杀者", "character_role":"攻击者", "element_type":"冰", "weapon_type":"斩",
    },
    "1002403":{
        "style_name":"生者的稳态", "character_role":"增益者", "element_type":"雷", "weapon_type":"突",
    },
    "1002404":{
        "style_name":"宇宙浩瀚，星光璀璨", "character_role":"增益者", "element_type":"无", "weapon_type":"突",
    },
    "1002503":{
        "style_name":"苍蓝夜曲", "character_role":"减益者", "element_type":"无", "weapon_type":"斩",
    },
    "1002504":{
        "style_name":"剧终的黄昏", "character_role":"减益者", "element_type":"冰", "weapon_type":"斩",
    },
    "1002603":{
        "style_name":"狂怒之兽", "character_role":"破坏者", "element_type":"无", "weapon_type":"突",
    },
    "1002604":{
        "style_name":"兽之心暖", "character_role":"破坏者", "element_type":"雷", "weapon_type":"突",
    },

# 31C
    "1003103":{
        "style_name":"Ebon Knight", "character_role":"攻击者", "element_type":"冰", "weapon_type":"斩",
    },
    "1003104":{
        "style_name":"Holy Knight", "character_role":"攻击者", "element_type":"光", "weapon_type":"斩",
    },
    "1003106":{
        "style_name":"Daydream Believer", "character_role":"攻击者", "element_type":"雷", "weapon_type":"斩",
    },
    "1003203":{
        "style_name":"飘荡于星海的占卜师", "character_role":"增益者", "element_type":"无", "weapon_type":"打",
    },
    "1003204":{
        "style_name":"对决！!空气舞台", "character_role":"防御者", "element_type":"冰", "weapon_type":"打",
    },
    "1003303":{
        "style_name":"实验性的你", "character_role":"减益者", "element_type":"无", "weapon_type":"突",
    },
    "1003304":{
        "style_name":"山胁大人的手下：喵喵法师", "character_role":"减益者", "element_type":"冰", "weapon_type":"突",
    },
    "1003403":{
        "style_name":"夜空的明星", "character_role":"破盾者", "element_type":"冰", "weapon_type":"突",
    },
    "1003404":{
        "style_name":"Happy Legion", "character_role":"破盾者", "element_type":"光", "weapon_type":"突",
    },
    "1003503":{
        "style_name":"忍法大乱炖", "character_role":"破坏者", "element_type":"冰", "weapon_type":"斩",
    },
    "1003504":{
        "style_name":"飞雪魔法", "character_role":"破坏者", "element_type":"冰", "weapon_type":"斩",
    },
    "1003505":{
        "style_name":"少女的休憩", "character_role":"破坏者", "element_type":"暗", "weapon_type":"斩",
    },
    "1003603":{
        "style_name":"甜美的枪口", "character_role":"增益者", "element_type":"冰", "weapon_type":"突",
    },
    "1003604":{
        "style_name":"暗杀者忍法源源不断", "character_role":"增益者", "element_type":"无", "weapon_type":"突",
    },
    "1003605":{
        "style_name":"Crying Tears", "character_role":"攻击者", "element_type":"冰", "weapon_type":"突",
    },

# 30G
    "1004103":{
        "style_name":"Awakening Iris", "character_role":"攻击者", "element_type":"光", "weapon_type":"斩",
    },
    "1004104":{
        "style_name":"Infernal Sanctuary", "character_role":"破坏者", "element_type":"雷", "weapon_type":"斩",
    },
    "1004106":{
        "style_name":"盛夏的近卫", "character_role":"攻击者", "element_type":"暗", "weapon_type":"斩",
    },
    "1004203":{
        "style_name":"黑夜散去，一闪心静", "character_role":"攻击者", "element_type":"暗", "weapon_type":"打",
    },
    "1004204":{
        "style_name":"不为人知的闲暇", "character_role":"攻击者", "element_type":"光", "weapon_type":"打",
    },
    "1004303":{
        "style_name":"星林的留客雨", "character_role":"减益者", "element_type":"光", "weapon_type":"突",
    },
    "1004304":{
        "style_name":"丰饶喜乐神秘莫测", "character_role":"减益者", "element_type":"雷", "weapon_type":"突",
    },
    "1004403":{
        "style_name":"末日洛丽塔白书", "character_role":"防御者", "element_type":"无", "weapon_type":"打",
    },
    "1004404":{
        "style_name":"亡国的纯洁之心", "character_role":"防御者", "element_type":"暗", "weapon_type":"打",
    },
    "1004503":{
        "style_name":"朦胧月夜的子弹", "character_role":"破盾者", "element_type":"无", "weapon_type":"突",
    },
    "1004504":{
        "style_name":"萌萌天才剑士", "character_role":"攻击者", "element_type":"暗", "weapon_type":"突",
    },
    "1004505":{
        "style_name":"希求与渴望", "character_role":"破盾者", "element_type":"雷", "weapon_type":"突",
    },
    "1004603":{
        "style_name":"此时期盼丰登之神", "character_role":"破坏者", "element_type":"光", "weapon_type":"斩",
    },
    "1004605":{
        "style_name":"年轻老板娘的日常", "character_role":"破坏者", "element_type":"暗", "weapon_type":"斩",
    },

#31D
    "1005103":{
        "style_name":"无上的终局", "character_role":"攻击者", "element_type":"暗", "weapon_type":"打",
    },
    "1005104":{
        "style_name":"Holiday Ring a Bell", "character_role":"攻击者", "element_type":"冰", "weapon_type":"打",
    },
    "1005203":{
        "style_name":"击碎无彩色", "character_role":"增益者", "element_type":"暗", "weapon_type":"突",
    },
    "1005303":{
        "style_name":"末日要干嘛？", "character_role":"减益者", "element_type":"无", "weapon_type":"斩",
    },
    "1005403":{
        "style_name":"早点回家吧", "character_role":"治疗者", "element_type":"无", "weapon_type":"突",
    },
    "1005405":{
        "style_name":"潜入，面带笑容参加技术交流会", "character_role":"治疗者", "element_type":"无", "weapon_type":"突",
    },
    "1005503":{
        "style_name":"网球场的恶魔", "character_role":"破盾者", "element_type":"暗", "weapon_type":"打",
    },
    "1005504":{
        "style_name":"Holiday Star Night", "character_role":"破盾者", "element_type":"冰", "weapon_type":"打",
    },
    "1005603":{
        "style_name":"禁锢的虎鲸", "character_role":"减益者", "element_type":"无", "weapon_type":"打",
    },

# 31E
    "1006103":{
        "style_name":"无止境慈爱的守护者", "character_role":"治疗者", "element_type":"火", "weapon_type":"打",
    },
    "1006104":{
        "style_name":"Sweet Phantasy", "character_role":"防御者", "element_type":"火", "weapon_type":"打",
    },
    "1006203":{
        "style_name":"Brand New Mind", "character_role":"破坏者", "element_type":"火", "weapon_type":"斩",
    },
    "1006205":{
        "style_name":"激情满满的温泉之旅", "character_role":"攻击者", "element_type":"光", "weapon_type":"斩",
    },
    "1006303":{
        "style_name":"Realize Your Mind", "character_role":"攻击者", "element_type":"火", "weapon_type":"打",
    },
    "1006403":{
        "style_name":"慵懒破灭", "character_role":"增益者", "element_type":"火", "weapon_type":"突",
    },
    "1006404":{
        "style_name":"懒洋洋的睡衣之夜", "character_role":"增益者", "element_type":"光", "weapon_type":"突",
    },
    "1006503":{
        "style_name":"制胜之锁", "character_role":"减益者", "element_type":"火", "weapon_type":"斩",
    },
    "1006504":{
        "style_name":"出浴后的朦胧天地", "character_role":"减益者", "element_type":"无", "weapon_type":"斩",
    },
    "1006603":{
        "style_name":"危机棒极了", "character_role":"治疗者", "element_type":"无", "weapon_type":"突",
    },
    "1006605":{
        "style_name":"初春之风扑面来", "character_role":"治疗者", "element_type":"无", "weapon_type":"突",
    },
    

# 31F
    "1007103":{
        "style_name":"Wild Rose", "character_role":"治疗者", "element_type":"无", "weapon_type":"突",
    },
    "1007104":{
        "style_name":"深夜疾风拂面时", "character_role":"治疗者", "element_type":"无", "weapon_type":"突",
    },
    "1007203":{
        "style_name":"不断进化的敏感性", "character_role":"破盾者", "element_type":"暗", "weapon_type":"突",
    },
    "1007303":{
        "style_name":"与你齐奏", "character_role":"增益者", "element_type":"暗", "weapon_type":"斩",
    },
    "1007403":{
        "style_name":"急速消失的烽火", "character_role":"防御者", "element_type":"暗", "weapon_type":"打",
    },
    "1007503":{
        "style_name":"刀光凛冽", "character_role":"攻击者", "element_type":"暗", "weapon_type":"斩",
    },
    "1007504":{
        "style_name":"衣香犹记化梦蝶", "character_role":"攻击者", "element_type":"无", "weapon_type":"斩",
    },
    "1007603":{
        "style_name":"特别之日鬼舞狂刀", "character_role":"破坏者", "element_type":"暗", "weapon_type":"打",
    },

# 31X
    "1008103":{
        "style_name":"摩天楼上的暗夜英雄", "character_role":"攻击者", "element_type":"雷", "weapon_type":"斩",
    },
    "1008203":{
        "style_name":"吾若不勇，与无将同", "character_role":"增益者", "element_type":"无", "weapon_type":"斩",
    },
    "1008204":{
        "style_name":"引路一袭露草色", "character_role":"增益者", "element_type":"雷", "weapon_type":"斩",
    },
    "1008303":{
        "style_name":"蓝色石榴石", "character_role":"破盾者", "element_type":"无", "weapon_type":"突",
    },
    "1008403":{
        "style_name":"凛然的杜尔迦", "character_role":"防御者", "element_type":"无", "weapon_type":"打",
    },
    "1008503":{
        "style_name":"血红浮雕", "character_role":"治疗者", "element_type":"冰", "weapon_type":"打",
    },
    "1008504":{
        "style_name":"刹那的邂逅", "character_role":"治疗者", "element_type":"雷", "weapon_type":"打",
    },
    "1008603":{
        "style_name":"逆境绽放之花", "character_role":"减益者", "element_type":"暗", "weapon_type":"突",
    },
    "1008604":{
        "style_name":"永恒的思念", "character_role":"减益者", "element_type":"雷", "weapon_type":"突",
    },

# Angel Beats!
    "1020103":{
        "style_name":"Earth Angel", "character_role":"攻击者", "element_type":"光", "weapon_type":"斩",
    },
    "1020104":{
        "style_name":"翱翔天际之剑", "character_role":"攻击者", "element_type":"冰", "weapon_type":"斩",
    },
    "1020203":{
        "style_name":"Rain Fire", "character_role":"破坏者", "element_type":"火", "weapon_type":"突",
    },
    "1020204":{
        "style_name":"平凡的非日常", "character_role":"破盾者", "element_type":"冰", "weapon_type":"突",
    },
    "1020303":{
        "style_name":"Faraway Eden", "character_role":"防御者", "element_type":"冰", "weapon_type":"打",
    }

}



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
