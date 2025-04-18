import sys
import os
from functools import partial
import re
import math

def extract_skill_numbers(text):
    # 添加 re.DOTALL 以匹配换行符
    strength_text = re.search(r"技能强度：(.*?)，属性倍率", text, re.DOTALL).group(1)
    # 提取所有数字并转为整数
    return [int(num.replace(",", "")) for num in re.findall(r"\d{1,3}(?:,\d{3})*|\d+", strength_text)]

def write_numbers_back(text, modified_numbers):
    # 使用 re.DOTALL 分割原字符串
    parts = re.split(r"(技能强度：.*?，属性倍率)", text, flags=re.DOTALL)
    
    strength_text = parts[1]
    numbers_with_commas = re.findall(r"\d{1,3}(?:,\d{3})*|\d+", strength_text)
    
    # 替换数字（保留原始格式的逗号）
    for i, num in enumerate(numbers_with_commas):
        new_num = "{:,}".format(modified_numbers[i]) # 添加千位分隔符
        strength_text = strength_text.replace(num, new_num, 1)  # 只替换第一次出现
    
    parts[1] = strength_text
    return "".join(parts)

def heal_extract_skill_numbers(text):
    # 添加 re.DOTALL 以匹配换行符
    strength_text = re.search(r"回复DP(.*?)，属性倍率", text, re.DOTALL).group(1)
    # 提取所有数字并转为整数
    return [int(num.replace(",", "")) for num in re.findall(r"\d{1,3}(?:,\d{3})*|\d+", strength_text)]

def heal_write_numbers_back(text, modified_numbers):
    # 使用 re.DOTALL 分割原字符串
    parts = re.split(r"(回复DP.*?，属性倍率)", text, flags=re.DOTALL)
    
    strength_text = parts[1]
    numbers_with_commas = re.findall(r"\d{1,3}(?:,\d{3})*|\d+", strength_text)
    
    # 替换数字（保留原始格式的逗号）
    for i, num in enumerate(numbers_with_commas):
        new_num = "{:,}".format(modified_numbers[i]) # 添加千位分隔符
        strength_text = strength_text.replace(num, new_num, 1)  # 只替换第一次出现
    
    parts[1] = strength_text
    return "".join(parts)

# [] 返回技能强度最大值 最小值 列表形式 [min, max]
def get_strength_min_max(strength):
    strength_min_max_str = strength.replace(',', '').split(' ~ ')
    return [int(strength_min_max[0]), int(strength_min_max[1])]

# [] 返回不同等级技能强度最大值 最小值 列表形式 [min, max]
def get_lv_strength_min_max(strength_min_max, lv):
    strength_min_base = float(strength_min_max[0])
    strength_max_base = float(strength_min_max[1])

    step_len_min = strength_min_base / 20
    step_len_max = strength_min_base / 10
    lv_strength_min = round(step_len_min * (lv - 1) + strength_min_base)
    lv_strength_max = round(step_len_max * (lv - 1) + strength_max_base)

    return [lv_strength_min, lv_strength_max]

# [] 返回不同等级回量最大值 最小值 列表形式 [min, max]
def get_lv_heal_min_max(heal_min_max, lv):
    heal_min_base = float(heal_min_max[0])
    heal_max_base = float(heal_min_max[1])

    step_len_min = heal_min_base / 20
    step_len_max = step_len_min * 1.2
    lv_heal_min = round(step_len_min * (lv - 1) + heal_min_base)
    lv_heal_max = round(step_len_max * (lv - 1) + heal_max_base)

    return [lv_heal_min, lv_heal_max]

# 技能 hit 伤害分布：0.1×2，0.25×2，0.3×1
def get_hit_damage_str(hit_damage):
    # 统计每个数值出现的次数
    damage_count = {}
    for damage in hit_damage:
        if damage in damage_count:
            damage_count[damage] += 1
        else:
            damage_count[damage] = 1

    # 生成格式化的字符串
    hit_damage_str = "，".join([f"{damage}×{count}" for damage, count in damage_count.items()])
    return hit_damage_str

# 技能 hit 伤害分布：0.1，0.1，0.25，0.25，0.3
def get_hit_damage_expand_str(hit_damage):
    hit_damage_expand_str = "，".join(map(str, hit_damage))
    return hit_damage_expand_str

# 绑定事件：当选项改变时触发，优先使用 event.widget 获取事件来源的控件
def on_attack_combo_select(event, desc_lab, lv1_skill_strength):
    try:
        lv_select = event.widget.get()
        lv = int(lv_select.replace("Skill Lv.",""))

        original_numbers = extract_skill_numbers(lv1_skill_strength)
        if len(original_numbers) == 2:
            new_original_numbers = get_lv_strength_min_max(original_numbers, lv)
            new_text = write_numbers_back(lv1_skill_strength, new_original_numbers)
        else:
            new_original_numbers0 = get_lv_strength_min_max(original_numbers[:2], lv)
            new_original_numbers1 = get_lv_strength_min_max(original_numbers[2:], lv)
            new_text = write_numbers_back(lv1_skill_strength, new_original_numbers0+new_original_numbers1)

        desc_lab["text"] = new_text
    except:
        return


# 绑定事件：当选项改变时触发，优先使用 event.widget 获取事件来源的控件
def on_heal_combo_select(event, desc_lab, lv1_skill_strength):

    try:
        last_text = desc_lab["text"]
        lv_select = event.widget.get()
        lv = int(lv_select.replace("Skill Lv.",""))

        original_numbers = heal_extract_skill_numbers(lv1_skill_strength)
        if len(original_numbers) == 2:
            new_original_numbers = get_lv_heal_min_max(original_numbers, lv)
            new_text = heal_write_numbers_back(lv1_skill_strength, new_original_numbers)
        else:
            new_original_numbers0 = get_lv_heal_min_max(original_numbers[:2], lv)
            new_original_numbers1 = get_lv_heal_min_max(original_numbers[2:], lv)
            new_text = heal_write_numbers_back(lv1_skill_strength, new_original_numbers0+new_original_numbers1)

        desc_lab["text"] = new_text
    except:
        return
