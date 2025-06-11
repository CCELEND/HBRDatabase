
from tools import load_json

# 职业
class Career:
    def __init__(self, path = "", 
        name = "",en="",description = "",hit=""
        ):
        self.path = path                    # 职业图路径
        self.name = name                    # 职业名
        self.en = en                        # 英文
        self.description = description      # 描述

careers_json = {}
# 加载资源文件
def load_resources():
    global careers_json
    if careers_json:
        return
    careers_json = load_json("./战斗系统/职业/careers.json")

# 键：职业名，值：对象
careers = {}

# 根据字典 创建并返回职业对象
def creat_career(career_json):

    path = career_json['path']
    name = career_json['name']
    en = career_json['en']
    description = career_json['description']

    career = Career(
        path,
        name,
        en,
        description
    )

    return career

def get_career_obj(career_json):
    name = career_json['name']

    if name in careers:
        career = careers[name]
    else:
        career = creat_career(career_json)
        careers[name] = career

    return career

def get_all_career_obj():

    load_resources()

    if not careers_json:
        return

    if len(careers) == len(careers_json):
        return

    for career_name in careers_json:
        if career_name not in careers:
            career = get_career_obj(careers_json[career_name])
            careers[career_name] = career
            



