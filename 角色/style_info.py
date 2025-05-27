
# 技能效果
class SkillEffect:
    def __init__(self, effect_type = None, value = None, 
        attribute_multiplier = None, attribute_difference = None, 
        turn_num = None, duration = None, target= None, 
        main_effect = False,
        probability = "100%"):

        self.effect_type = effect_type  # 效果类型 e.g., "降防 防御下降", "攻击上升" "暴击率上升" "攻击下降" "连击数上升" "强化领域"
        self.value = value  # 效果量 30 ~ 45% 没有就填 None
        self.attribute_multiplier = attribute_multiplier        # 属性倍率 {"智慧": 2, "运气": 1}
        self.attribute_difference = attribute_difference        # 属性差值 149

        self.turn_num = turn_num    # 回合数，次数如果没说明回合数或者持续生效或者次数这个成员就填 None
        self.duration = duration    # 敌方回合, 我方回合, 持续，次；如果没说明回合数或者次数这个成员就填 None
        self.target = target        # 敌方 全体敌方 自身 前锋 后卫 全体友方 一名友方
        
        self.main_effect = main_effect  # 是否是主效果

        self.probability = probability  # 成功概率值

    @classmethod
    def from_list(cls, effect_data):
        params = {
            'effect_type': None,
            'value': None,
            'attribute_multiplier': None,
            'attribute_difference': None,
            'turn_num': None,
            'duration': None,
            'target': None,
            'main_effect': False,
            'probability': "100%"
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
            elif i == 7:
                params['main_effect'] = data
            elif i == 8:
                params['probability'] = data

        return cls(**params)

# 攻击技能
class AttackSkill:
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

# 主动技能
class ActiveSkill:
    def __init__(self, name = None, description = None, 
        sp_cost = None, max_uses = None, 
        effects = None, 
        level_reqs = None, level_max="10"):
        self.name = name
        self.description = description      # 技能描述
        self.sp_cost = sp_cost              # SP 消耗
        self.max_uses = max_uses            # 使用次数 None：无限
        self.effects = effects              # 技能效果列表 []
        self.level_reqs = level_reqs        # 等级需求列表 []

        self.level_max = level_max          # 最大等级
        
# 被动技能
class PassiveSkill:
    def __init__(self, name = None, description = None, 
        LB = None, 
        effect_type = None, value = None, 
        turn_num = None, duration = None, target = None, 
        probability = None):
        self.name = name
        self.description = description
        self.LB = LB   # 突破数
        self.effect_type = effect_type  # 效果类型 e.g., "降防 防御下降", "攻击上升" "暴击率上升" "攻击下降" "连击数上升" "强化领域"
        self.value = value          # 效果量 30 ~ 45% 没有就填 None

        self.turn_num = turn_num    # 回合数，次数，如果没说明回合数或者持续生效或者次数这个成员就填 None
        self.duration = duration    # 敌方回合, 我方回合, 持续，次；如果没说明回合数或者次数这个成员就填 None
        self.target = target        # 敌方 全体敌方 自身 前锋 后卫 全体友方 一名友方

        self.probability = probability          # 成功概率值

    @classmethod
    def from_list(cls, effect_data):
        params = {
            'name': None,
            'description': None,
            'LB': None,
            'effect_type': None,
            'value': None,
            'turn_num': None,
            'duration': None,
            'target': None,
            'probability': "100%"
        }
        
        for i, data in enumerate(effect_data):
            if i == 0:
                params['name'] = data
            elif i == 1:
                params['description'] = data
            elif i == 2:
                params['LB'] = data
            elif i == 3:
                params['effect_type'] = data
            elif i == 4:
                params['value'] = data
            elif i == 5:
                params['turn_num'] = data
            elif i == 6:
                params['duration'] = data
            elif i == 7:
                params['target'] = data
            elif i == 8:
                params['probability'] = data

        return cls(**params)


# 成长技能
class GrowthAbility:
    def __init__(self, description):
        self.description = description


# 风格
class Style:
    def __init__(self, path = None, 
        team_name = None, role_name = None, name = None, nicknames = None, description = None, rarity = None, 
        career = None, 
        weapon_attribute = None, element_attribute = None,
        active_skills = None, passive_skills = None, 
        growth_ability = None, status_growth = None):
        self.path = path                        # 风格头像路径
        self.team_name = team_name              # 所属队伍名
        self.role_name = role_name              # 所属角色名
        self.name = name                        # 风格名
        self.nicknames = nicknames              # 别名列表
        self.description = description          # 描述
        self.rarity = rarity                    # 稀有度
        self.career = career                    # 职业 攻击者
        self.weapon_attribute = weapon_attribute    # 武器属性 斩 突 打
        self.element_attribute = element_attribute  # 元素属性

        self.active_skills = active_skills      # 主动技能列表
        self.passive_skills = passive_skills    # 被动技能列表
        self.growth_ability = growth_ability    # 成长能力
        self.status_growth = status_growth      # 成长状态值

# 使用字典存储所有风格分类
style_categories = {
    "rarity": {
        "A":  {},
        "S":  {},
        "SS": {}
    },
    "career":{
        "攻击者":{},
        "破坏者":{},
        "防御者":{},
        "破盾者":{},
        "减益者":{},
        "增益者":{},
        "治疗者":{}
    },
    "weapon_attribute": {
        "斩": {},
        "突": {},
        "打": {}
    },
    "element_attribute": {
        "火": {},
        "冰": {},
        "雷": {},
        "光": {},
        "暗": {},
        "火暗":{},
        "无": {}
    },
    "all":{}
}

# 根据风格对象的稀有度、武器属性和元素属性分类存储样式
def set_style_category(style):

    # 按稀有度分类
    if style.rarity in style_categories["rarity"]:
        style_categories["rarity"][style.rarity][style.name] = style

    # 按职能分类
    if style.career in style_categories["career"]:
        style_categories["career"][style.career][style.name] = style

    # 按武器属性分类
    if style.weapon_attribute in style_categories["weapon_attribute"]:
        style_categories["weapon_attribute"][style.weapon_attribute][style.name] = style

    # 按元素属性分类
    if style.element_attribute in style_categories["element_attribute"]:
        style_categories["element_attribute"][style.element_attribute][style.name] = style
    else:
        style_categories["element_attribute"]["无"][style.name] = style

    style_categories["all"][style.name]  = style


# 根据字典 创建并返回风格对象
def create_style(data):

    style_info = data['style_info']
    style_path, style_team_name, style_role_name, style_name, style_nicknames, style_description, style_rarity, style_career, style_weapon_attribute, style_element_attribute = style_info
    # 主动技能列表
    activeskills = []
    for active_skill_list in data['ActiveSkills']:
        name, description, sp_cost, max_uses = active_skill_list[0]

        effects = []
        for effect in active_skill_list[1]:
            if effect[0] in ["斩","突","打"]:
                effect_obj = AttackSkill.from_list(effect)
            else:
                effect_obj = SkillEffect.from_list(effect)

            effects.append(effect_obj)

        if len(active_skill_list) == 4:
            level_max = active_skill_list[3]
            # 主动技能对象
            ActiveSkill_obj = ActiveSkill(name, description, sp_cost, max_uses,
                effects,
                active_skill_list[2],
                level_max
            )
        else:
            # 主动技能对象
            ActiveSkill_obj = ActiveSkill(name, description, sp_cost, max_uses,
                effects,
                active_skill_list[2]
            )

        activeskills.append(ActiveSkill_obj)


    # 被动技能
    passiveskills = []
    for passive_skill in data['PassiveSkills']:
        PassiveSkill_obj = PassiveSkill.from_list(passive_skill)
        passiveskills.append(PassiveSkill_obj)


    growthability = GrowthAbility(data['GrowthAbility']) if 'GrowthAbility' in data else None

    statusgrowth = data['status_growth'] if 'status_growth' in data else None

    style = Style(
        style_path,
        style_team_name,
        style_role_name,
        style_name,
        style_nicknames,
        style_description,
        style_rarity,
        style_career,
        style_weapon_attribute,
        style_element_attribute,

        activeskills,
        passiveskills,
        growthability,
        statusgrowth
    )


    return style

# 获取风格对象
def get_style_obj(data):

    style_info = data['style_info']
    style_name = style_info[1]

    # 判断风格对象是否在字典中，在就复用，不在就生成
    if style_name in style_categories["all"]:
        style = style_categories["all"][style_name]
    else:
        style = create_style(data)
        set_style_category(style)

    return style
