
import re

# 提取范围值列表
def extract_skill_numbers(text, type):
    # 添加 re.DOTALL 以匹配换行符
    if type == "攻击":
        strength_text = re.search(r"技能强度：(.*?)，属性倍率", text, re.DOTALL).group(1)
    elif type == "治疗":
        strength_text = re.search(r"回复DP(.*?)，属性倍率", text, re.DOTALL).group(1)
    elif type == "防御上升":
        strength_text = re.search(r"防御上升(.*?)，属性倍率", text, re.DOTALL).group(1)
    elif type == "上升":
        strength_text = re.search(r"上升(.*?)，属性倍率", text, re.DOTALL).group(1)
    elif type == "下降":
        strength_text = re.search(r"下降(.*?)，属性倍率", text, re.DOTALL).group(1)
    elif type == "心眼":
        strength_text = re.search(r"伤害增加：(.*?)，属性倍率", text, re.DOTALL).group(1)

    # 提取所有数字并转为整数（偶数个）
    result = [int(num.replace(",", "")) for num in re.findall(r"\d{1,3}(?:,\d{3})*|\d+", strength_text)]
    n = len(result)
    effective_range = n if n % 2 == 0 else n - 1
    return result[:effective_range]

# 回写字符串
def write_numbers_back(text, modified_numbers, type):
    # 使用 re.DOTALL 分割原字符串

    if type == "攻击":
        parts = re.split(r"(技能强度：.*?，属性倍率)", text, flags=re.DOTALL)
    elif type == "治疗":
        parts = re.split(r"(回复DP.*?，属性倍率)", text, flags=re.DOTALL)
    elif type == "防御上升":
        parts = re.split(r"(防御上升.*?，属性倍率)", text, flags=re.DOTALL)
    elif type == "上升":
        parts = re.split(r"(上升.*?，属性倍率)", text, flags=re.DOTALL)
    elif type == "下降":
        parts = re.split(r"(下降.*?，属性倍率)", text, flags=re.DOTALL)
    elif type == "心眼":
        parts = re.split(r"(伤害增加：.*?，属性倍率)", text, flags=re.DOTALL)

    strength_text = parts[1]
    numbers_with_commas = re.findall(r"\d{1,3}(?:,\d{3})*|\d+", strength_text)
    n = len(numbers_with_commas)
    effective_range = n if n % 2 == 0 else n - 1

    if "充能" in text:
        numbers_with_commas = numbers_with_commas[:2]
        effective_range = 2
    
    # 替换数字（保留原始格式的逗号）
    for i, num in enumerate(numbers_with_commas[:effective_range]):
        new_num = "{:,}".format(modified_numbers[i]) # 添加千位分隔符
        strength_text = strength_text.replace(num, new_num, 1)  # 只替换第一次出现
    
    parts[1] = strength_text
    return "".join(parts)

# [] 返回技能强度最大值 最小值 列表形式 [min, max]
def get_strength_min_max(strength):
    strength_min_max_str = strength.replace(',', '').split(' ~ ')
    return [int(strength_min_max_str[0]), int(strength_min_max_str[1])]

# [] 返回不同等级技能强度最大值 最小值 列表形式 [min, max]
def get_lv_strength_min_max(strength_min_max, lv):
    strength_min_base = float(strength_min_max[0])
    strength_max_base = float(strength_min_max[1])

    step_len_min = strength_min_base * 0.05
    step_len_max = strength_min_base * 0.1
    lv_strength_min = round(step_len_min * (lv - 1) + strength_min_base)
    lv_strength_max = round(step_len_max * (lv - 1) + strength_max_base)

    return [lv_strength_min, lv_strength_max]

# [] 返回不同等级回复量最大值 最小值 列表形式 [min, max]
def get_lv_heal_min_max(heal_min_max, lv):
    heal_min_base = float(heal_min_max[0])
    heal_max_base = float(heal_min_max[1])

    step_len_min = heal_min_base * 0.05
    step_len_max = heal_min_base * 0.06
    lv_heal_min = round(step_len_min * (lv - 1) + heal_min_base)
    lv_heal_max = round(step_len_max * (lv - 1) + heal_max_base)

    return [lv_heal_min, lv_heal_max]

# [] 返回不同等级buff最大值 最小值 列表形式 [min, max]
def get_lv_buff_min_max(buff_min_max, lv):
    buff_min_base = float(buff_min_max[0])
    buff_max_base = float(buff_min_max[1])

    lv_buff_min = buff_min_base * (1 + 0.03 * (lv - 1))
    lv_buff_max = buff_max_base * (1 + 0.02 * (lv - 1))
    # 保留一位小数
    lv_buff_min = float(f"{lv_buff_min:.1f}")
    lv_buff_max = float(f"{lv_buff_max:.1f}")

    # 如果小数部分为0则转换为整数
    lv_buff_min = int(lv_buff_min) if lv_buff_min.is_integer() else lv_buff_min
    lv_buff_max = int(lv_buff_max) if lv_buff_max.is_integer() else lv_buff_max

    return [lv_buff_min, lv_buff_max]


# [] 返回不同等级defense上升最大值 最小值 列表形式 [min, max]
def get_lv_defense_min_max(defense_min_max, lv):
    defense_min_base = float(defense_min_max[0])
    defense_max_base = float(defense_min_max[1])

    lv_defense_min = defense_min_base * (1 + 0.05 * (lv - 1))
    lv_defense_max = defense_max_base * (1 + 0.02 * (lv - 1))
    # 保留一位小数
    lv_defense_min = float(f"{lv_defense_min:.1f}")
    lv_defense_max = float(f"{lv_defense_max:.1f}")

    # 如果小数部分为0则转换为整数
    lv_defense_min = int(lv_defense_min) if lv_defense_min.is_integer() else lv_defense_min
    lv_defense_max = int(lv_defense_max) if lv_defense_max.is_integer() else lv_defense_max

    return [lv_defense_min, lv_defense_max]

# [] 返回不同等级debuff最大值 最小值 列表形式 [min, max]
def get_lv_debuff_min_max(debuff_min_max, lv):
    debuff_min_base = float(debuff_min_max[0])
    debuff_max_base = float(debuff_min_max[1])

    lv_debuff_min = debuff_min_base * (1 + 0.05 * (lv - 1))
    lv_debuff_max = debuff_max_base * (1 + 0.02 * (lv - 1))
    # 保留一位小数
    lv_debuff_min = float(f"{lv_debuff_min:.1f}")
    lv_debuff_max = float(f"{lv_debuff_max:.1f}")

    # 如果小数部分为0则转换为整数
    lv_debuff_min = int(lv_debuff_min) if lv_debuff_min.is_integer() else lv_debuff_min
    lv_debuff_max = int(lv_debuff_max) if lv_debuff_max.is_integer() else lv_debuff_max

    return [lv_debuff_min, lv_debuff_max]


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

# 暗忍用
def on_buff_attack_combo_select(event, desc_labs, lv1_skill_strengths):
    on_attack_combo_select(event, desc_labs[0], lv1_skill_strengths[0])
    on_buff_combo_select(event, desc_labs[1], lv1_skill_strengths[1])


# 绑定事件：当选项改变时触发，优先使用 event.widget 获取事件来源的控件
def on_attack_combo_select(event, desc_lab, lv1_skill_strength):
    try:
        lv_select = event.widget.get()
        lv = int(lv_select.replace("Skill Lv.",""))

        original_numbers = extract_skill_numbers(lv1_skill_strength, "攻击")
        if len(original_numbers) == 2:
            new_original_numbers = get_lv_strength_min_max(original_numbers, lv)
            new_text = write_numbers_back(lv1_skill_strength, new_original_numbers, "攻击")
        else:
            new_original_numbers0 = get_lv_strength_min_max(original_numbers[:2], lv)
            new_original_numbers1 = get_lv_strength_min_max(original_numbers[2:], lv)
            new_text = write_numbers_back(lv1_skill_strength, new_original_numbers0+new_original_numbers1, "攻击")

        desc_lab["text"] = new_text
    except:
        return


# 绑定事件：当选项改变时触发，优先使用 event.widget 获取事件来源的控件
def on_heal_combo_select(event, desc_lab, lv1_skill_strength):

    # try:
    lv_select = event.widget.get()
    lv = int(lv_select.replace("Skill Lv.",""))

    original_numbers = extract_skill_numbers(lv1_skill_strength, "治疗")
    if len(original_numbers) == 2:
        new_original_numbers = get_lv_heal_min_max(original_numbers, lv)
        new_text = write_numbers_back(lv1_skill_strength, new_original_numbers, "治疗")
    else:
        new_original_numbers0 = get_lv_heal_min_max(original_numbers[:2], lv)
        new_original_numbers1 = get_lv_heal_min_max(original_numbers[2:], lv)
        new_text = write_numbers_back(lv1_skill_strength, new_original_numbers0+new_original_numbers1, "治疗")

    desc_lab["text"] = new_text
    # except:
    #     return

# 不同等级时的防御上升数值处理
def on_defense_combo_select(event, desc_lab, lv1_skill_strength):

    try:
        lv_select = event.widget.get()
        lv = int(lv_select.replace("Skill Lv.",""))

        original_numbers = extract_skill_numbers(lv1_skill_strength, "防御上升")
        if len(original_numbers) == 2:
            new_original_numbers = get_lv_defense_min_max(original_numbers, lv)
            new_text = write_numbers_back(lv1_skill_strength, new_original_numbers, "防御上升")
        else:
            new_original_numbers0 = get_lv_defense_min_max(original_numbers[:2], lv)
            new_original_numbers1 = get_lv_defense_min_max(original_numbers[2:], lv)
            new_text = write_numbers_back(lv1_skill_strength, new_original_numbers0+new_original_numbers1, "防御上升")

        desc_lab["text"] = new_text
    except:
        return

# 不同等级时的增益数值处理
def on_buff_combo_select(event, desc_lab, lv1_skill_strength):

    try:
        lv_select = event.widget.get()
        lv = int(lv_select.replace("Skill Lv.",""))

        original_numbers = extract_skill_numbers(lv1_skill_strength, "上升")
        if len(original_numbers) == 2:
            new_original_numbers = get_lv_buff_min_max(original_numbers, lv)
            new_text = write_numbers_back(lv1_skill_strength, new_original_numbers, "上升")
        else:
            new_original_numbers0 = get_lv_buff_min_max(original_numbers[:2], lv)
            new_original_numbers1 = get_lv_buff_min_max(original_numbers[2:], lv)
            new_text = write_numbers_back(lv1_skill_strength, new_original_numbers0+new_original_numbers1, "上升")

        desc_lab["text"] = new_text
    except:
        return

# 不同等级时的心眼数值处理
def on_mindeye_combo_select(event, desc_lab, lv1_skill_strength):

    try:
        lv_select = event.widget.get()
        lv = int(lv_select.replace("Skill Lv.",""))

        original_numbers = extract_skill_numbers(lv1_skill_strength, "心眼")
        if len(original_numbers) == 2:
            new_original_numbers = get_lv_buff_min_max(original_numbers, lv)
            new_text = write_numbers_back(lv1_skill_strength, new_original_numbers, "心眼")
        else:
            new_original_numbers0 = get_lv_buff_min_max(original_numbers[:2], lv)
            new_original_numbers1 = get_lv_buff_min_max(original_numbers[2:], lv)
            new_text = write_numbers_back(lv1_skill_strength, new_original_numbers0+new_original_numbers1, "心眼")

        desc_lab["text"] = new_text
    except:
        return

# 不同等级时的减益值处理
def on_debuff_combo_select(event, desc_lab, lv1_skill_strength):

    try:
        lv_select = event.widget.get()
        lv = int(lv_select.replace("Skill Lv.",""))

        original_numbers = extract_skill_numbers(lv1_skill_strength, "下降")
        if len(original_numbers) == 2:
            new_original_numbers = get_lv_debuff_min_max(original_numbers, lv)
            new_text = write_numbers_back(lv1_skill_strength, new_original_numbers, "下降")
        else:
            new_original_numbers0 = get_lv_debuff_min_max(original_numbers[:2], lv)
            new_original_numbers1 = get_lv_debuff_min_max(original_numbers[2:], lv)
            new_text = write_numbers_back(lv1_skill_strength, new_original_numbers0+new_original_numbers1, "下降")

        desc_lab["text"] = new_text
    except:
        return


# 返回不同等级百分比值
def get_lv_percentage(percentage_base, lv):
    lv_percentage_base = float(percentage_base)
    lv_percentage = lv_percentage_base + 1.668 * (lv - 1)
    lv_percentage = float(f"{lv_percentage:.1f}")

    # 如果小数部分为0则转换为整数
    lv_percentage = int(lv_percentage) if lv_percentage.is_integer() else lv_percentage

    return lv_percentage

# 提取百分比数字
def extract_percentage_skill_numbers(text):
    # 添加 re.DOTALL 以匹配换行符
    percentage = re.search(r"百分比的伤害：(.*?)%", text, re.DOTALL).group(1).strip()
    return percentage

# 回写
def write_percentage_numbers_back(text, new_percentage):
    new_text = re.sub(
        r"(百分比的伤害：)(\d+\.?\d*)(%，)",  # 匹配模式
        lambda m: f"{m.group(1)}{new_percentage}{m.group(3)}",  # 替换逻辑
        text
    )
    return new_text

# 不同等级时的百分比分数处理
def on_percentage_combo_select(event, desc_lab, lv1_skill_strength):

    try:
        lv_select = event.widget.get()
        lv = int(lv_select.replace("Skill Lv.",""))

        original_numbers = extract_percentage_skill_numbers(lv1_skill_strength)
        lv_percentage = get_lv_percentage(original_numbers, lv)
        new_text = write_percentage_numbers_back(lv1_skill_strength, lv_percentage)

        desc_lab["text"] = new_text
    except:
        return