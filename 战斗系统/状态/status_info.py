
import threading
from threading import Lock
from tools import load_json

# 状态
class Statu:
    def __init__(self, path = "", 
        name = "",effect="",description = "",stack="",type="",series=""
        ):
        self.path = path                    # 状态图路径
        self.name = name                    # 状态名
        self.effect = effect                # 效果描述
        self.description = description      # 描述
        self.stack = stack                  # 叠加次数
        self.type = type                    # 状态类型
        self.series = series                # 所属系列

status_json = {}
# 加载资源文件
def load_resources():
    global status_json
    if status_json:
        return
    status_json = load_json("./战斗系统/状态/status.json")

# 键：状态名，值：对象
status = {}
# 使用字典存储所有状态分类
statu_categories = {
    "回复": {
        "回复EP":{},"回复SP":{}, "降低SP消耗":{},"回复技能使用次数":{},"技能次数上限提升":{},"回复DP":{}
    },
    "增益":{
        
        "属性攻击上升":{},"攻击上升":{},"所有攻击上升":{},
        "元素攻击上升":{},"元素暴击率上升":{},"暴击率上升":{},
        "属性暴击伤害上升":{},"元素暴击伤害上升":{},"暴击伤害上升":{},
        "强化领域":{},"充能":{},"弱点伤害上升":{},
        "连击数上升":{},"破坏率上升":{},"防御上升":{},
        "状态值上升":{},"信念":{},"躲避":{},
        "技能效果强化":{},"歌姬加护":{},"影分身":{},
        "速弹":{},"Babied":{},"永恒誓言":{},
        "跟班":{},"高阶增强":{}
    },
    "减益": {
        "攻击下降": {},"防御下降": {},"属性防御下降": {},"元素防御下降": {},
        "DP防御下降": {},"弱点伤害上升":{},"抗性":{},"状态值下降":{},
        "回复效果下降":{},"驱散":{},"退避":{},"倒下回合数上升":{},"DP伤害":{},"负面情绪":{}, "暴击率下降":{}, "轰鸣麻痹":{}
    },
    "异常": {
        "禁锢": {},"眩晕": {},"混乱": {},"病毒": {},"持续伤害": {},"DP破坏":{},"锁定": {},"迷惑": {},"幻觉":{},"强击破": {}
    },
    "其他": {
        "挑衅，关注": {},"减益，异常移除": {},"OD条上升": {},"OD条下降": {},"额外回合": {},"双倍EX技能": {},"EShield":{},"承伤上限": {},"无敌":{},
        "贯通暴击": {},"特殊状态":{},"减益效果回合数上升":{},"击破保护":{},"无法换位":{},"召唤":{},
        "破坏率抗性上升":{},"对HP百分比伤害":{},"扣除SP":{},"SP上限增加":{},"SP消耗增加":{},
        "浓雾":{}
        
    }
}

# 线程锁，确保对全局变量的线程安全
status_lock = Lock()
statu_categories_lock = Lock()

def set_statu_category(statu):
    global statu_categories
    with statu_categories_lock:
        if statu.type == '回复':
            statu_categories["回复"][statu.series][statu.name] = statu
        elif statu.type == '增益':
            statu_categories["增益"][statu.series][statu.name] = statu
        elif statu.type == '减益':
            statu_categories["减益"][statu.series][statu.name] = statu
        elif statu.type == '异常':
            statu_categories["异常"][statu.series][statu.name] = statu
        else:
            statu_categories["其他"][statu.series][statu.name] = statu


# 根据字典 创建并返回状态对象
def creat_statu(statu_json):

    path = statu_json['path']
    name = statu_json['name']
    effect = statu_json['effect']
    description = statu_json['description']
    stack = statu_json['stack']
    type = statu_json['type']
    series = statu_json['series']
    statu = Statu(
        path,
        name,
        effect,
        description,
        stack,
        type,
        series
    )

    return statu

def get_statu_obj(statu_json):
    name = statu_json['name']
    with status_lock:
        if name in status:
            statu = status[name]
        else:
            statu = creat_statu(statu_json)
            status[name] = statu
            set_statu_category(statu)

    return statu


# def get_all_statu_obj(status_json):
#     for statu_name in status_json:
#         if statu_name not in status:
#             statu = get_statu_obj(status_json[statu_name])
#             status[statu_name] = statu
#             set_statu_category(statu)

# 多线程处理所有状态对象
def get_all_statu_obj():

    load_resources()

    if not status_json:
        return

    if len(status) == len(status_json):
        return

    threads = []
    for statu_name in status_json:
        thread = threading.Thread(target=get_statu_obj, args=(status_json[statu_name],))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()



