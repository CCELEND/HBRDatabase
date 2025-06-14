
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


# 攻击技能
class MasterAttackSkill:
    def __init__(self, weapon_attribute = None, element_attribute = None, 
        hit_num = None, hit_damage = None, 
        strength = None, attribute_multiplier = None, biased = None, 
        attribute_difference = None, destructive_multiplier = None, target = None,
        probability = "100%"):

        self.weapon_attribute = weapon_attribute   # 武器属性
        self.element_attribute = element_attribute  # 元素属性
        self.hit_num = hit_num                  # hit 数 5
        self.hit_damage = hit_damage            # hit 伤害分布 e.g., [0.1, 0.1, 0.25, 0.25, 0.3]
        self.strength = strength                # 技能强度 2,673 ~ 13,365
        self.attribute_multiplier = attribute_multiplier # 属性倍率 {"力量": 2, "灵巧": 1}
        self.biased = biased                    # 技能偏向 DP+30% HP+50% None
        self.attribute_difference = attribute_difference        # 属性差值 149
        self.destructive_multiplier = destructive_multiplier    # 破坏倍率 3.625
        self.target = target  # 单体或者全体、群体

        self.probability = probability          # 成功概率值

    @classmethod
    def from_list(cls, effect_data):
        params = {
            'weapon_attribute': None,
            'element_attribute': None,
            'hit_num': None,
            'hit_damage': None,
            'strength': None,
            'attribute_multiplier': None,
            'biased': None,
            'attribute_difference': None,
            'destructive_multiplier': None,
            'target': None,
            'probability': "100%"
        }
        
        for i, data in enumerate(effect_data):
            if i == 0:
                params['weapon_attribute'] = data
            elif i == 1:
                params['element_attribute'] = data
            elif i == 2:
                params['hit_num'] = data
            elif i == 3:
                params['hit_damage'] = data
            elif i == 4:
                params['strength'] = data
            elif i == 5:
                params['attribute_multiplier'] = data
            elif i == 6:
                params['biased'] = data
            elif i == 7:
                params['attribute_difference'] = data
            elif i == 8:
                params['destructive_multiplier'] = data
            elif i == 9:
                params['target'] = data
            elif i == 10:
                params['probability'] = data
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
        if effect[0] in ["斩","突","打"]:
            effect_obj = MasterAttackSkill.from_list(effect)
        else:
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

