
from tools import output_string, is_parentstring
from 角色.style_proc import get_hit_damage_str

# 特殊的效果状态，下列状态会显示：描述：值，或者描述
special_effects = [
    "心眼", "脆弱", "额外回合", "净化减益", "禁锢", "灾厄","特殊状态", "影分身", "混乱", 
    "弱点强击破", "退避", "充能", "斗志", "持续回复DP", "击破保护",
    "强化领域", "上升增益技能强化", "减益效果强化", "无敌", "掩护", "嘲讽", "抗性清除", "抗性下降", 
    "眩晕","清除病毒状态","清除攻击下降类状态","攻击上升且减益效果强化","回复技能强化","永恒誓言","对HP百分比攻击","对火弱点HP百分比攻击",
    "对冰弱点HP百分比攻击","对雷弱点HP百分比攻击","对光弱点HP百分比攻击","对暗弱点HP百分比攻击","防御下降技能强化","所有攻击上升","黑客"
]

# 次数、持续时间、目标、效果
# 描述：数值或者数值、属性倍率
# 属性差值
def output_skill_effect(turn_num, duration, target, effect_type,
    description, value, attribute_multiplier_dir=None,
    attribute_difference=None,
    IsActive=True) -> str:

    text = output_string(turn_num) + output_string(duration) + output_string(target)
    text += output_string(effect_type) + '\n'
    
    # 如果 effect_type 是 special_effects 中字符串的父串
    if is_parentstring(effect_type, special_effects):
        if value:
            text += description + "：" + value
        else:
            text += description
    else:
        text += output_string(value)

    if effect_type in ["连击数上升（大）", "连击数上升（小）", "连击数上升（特大）", "连击数上升（中）"]:
        text += "，" + description

    if IsActive:
        if attribute_multiplier_dir:
            attribute_multiplier = "、".join(
                [f"{key}×{value}" for key, value in attribute_multiplier_dir.items()]
            )
            text += '，属性倍率：' + attribute_multiplier  + '\n'
        if attribute_difference:
            text += '技能属性差值：' + attribute_difference
            if target in ['单体','全体'] and effect_type not in special_effects:
                text += f"（{attribute_difference}+敌方属性）"

    return text


# hit 数、目标、伤害分布
# 技能偏向
# 技能强度、属性倍率
# 技能属性差值、破坏倍率
def output_attack_skill(hit_num, target, hit_damage,
    biased,
    strength, attribute_multiplier_dir, 
    attribute_difference, destructive_multiplier) -> str:

    text = hit_num + '-hit' + target + '攻击'
    if hit_damage:
        hit_damage = get_hit_damage_str(hit_damage)
        text += "，hit伤害分布：" + f"（{hit_damage}）"
    text += '\n'

    if biased:
        text += "技能偏向：" + biased + '\n'

    if strength:
        text += "技能强度：" + strength 
    if attribute_multiplier_dir:
        attribute_multiplier = "、".join(
            [f"{key}×{value}" for key, value in attribute_multiplier_dir.items()]
        )
        text += '，属性倍率：' + attribute_multiplier + '\n'
        
    if attribute_difference:
        text += '技能属性差值：' + attribute_difference + f"（{attribute_difference}+敌方属性），"
    if destructive_multiplier:
        text += "破坏倍率：" + destructive_multiplier

    return text
    
