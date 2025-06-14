
# 大师技能效果类
class MasterSkillEffect:
    def __init__(self, effect_type = None, value = None, 
        attribute_multiplier = None, attribute_difference = None, 
        turn_num = None, duration = None, target= None):

        self.effect_type = effect_type  # 效果类型 e.g., "降防 防御下降", "攻击上升" "暴击率上升" "攻击下降" "连击数上升" "强化领域"
        self.value = value  # 效果量 30 ~ 45% 没有就填 None
        self.attribute_multiplier = attribute_multiplier        # 属性倍率 {"智慧": 2, "运气": 1}
        self.attribute_difference = attribute_difference        # 属性差值 149

        self.turn_num = turn_num    # 回合数，次数如果没说明回合数或者持续生效或者次数这个成员就填 None
        self.duration = duration    # 敌方回合, 我方回合, 持续，次；如果没说明回合数或者次数这个成员就填 None
        self.target = target        # 敌方 全体敌方 自身 前锋 后卫 全体友方 一名友方


    @classmethod
    def from_list(cls, effect_data):
        params = {
            'effect_type': None,
            'value': None,
            'attribute_multiplier': None,
            'attribute_difference': None,
            'turn_num': None,
            'duration': None,
            'target': None
        }
        
        for i, data in enumerate(effect_data):
            if i == 0:
                params['effect_type'] = data
            elif i == 1:
                params['value'] = data
            elif i == 2:
                params['attribute_multiplier'] = data
            elif i == 3:
                params['attribute_difference'] = data
            elif i == 4:
                params['turn_num'] = data
            elif i == 5:
                params['duration'] = data
            elif i == 6:
                params['target'] = data

        return cls(**params)


# 大师技能类
class MasterSkill:
    def __init__(self, name = None, description = None, 
        sp_cost = None, max_uses = None, 
        effects = None, missions = None):
        self.name = name
        self.description = description      # 技能描述
        self.sp_cost = sp_cost              # SP 消耗
        self.max_uses = max_uses            # 使用次数 None：无限
        self.effects = effects              # 技能效果对象列表 []
        self.missions =  missions           # 达成的任务


# 获取大师技能对象
def get_master_skill_obj(skill_info):

    if skill_info == None:
        return None

    effects = []
    for effect in skill_info[4]:
        effect_obj = MasterSkillEffect.from_list(effect)
        effects.append(effect_obj)

    Master_skill = MasterSkill(
        skill_info[0],
        skill_info[1],
        skill_info[2],
        skill_info[3],
        effects,
        skill_info[5]
    )

    return Master_skill

