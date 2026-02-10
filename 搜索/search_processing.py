import re

from tools import list_val_in_another, is_parentstring, output_string, list_is, check_dict_in_list
from tools import load_json

from 角色.style_info import is_skill_effect
import 角色.team_info

from 搜索.search_processing_resonance import check_resonance

# 选中处理
def on_select(check_vars, options, last, selected_values, all_index=0):

    # 如果 all 的状态发生变化
    if last[all_index] != check_vars[all_index].get():
        # 更新其他选项的状态
        for i in range(1, len(check_vars)):
            check_vars[i].set(check_vars[all_index].get())
    else:
        # 检查其他选项是否全部被选中
        if all(check_vars[i].get() for i in range(1, len(check_vars))):
            check_vars[all_index].set(True)
        else:
            check_vars[all_index].set(False)

    # 更新 last 列表
    last[:] = [check_vars[i].get() for i in range(len(check_vars))]

    # 输出当前选中的值，排除 all
    selected_values[:] = [value for i, (value, check_var) in enumerate(zip(options, check_vars)) 
                      if check_var.get() and i != all_index]

# 复选判断
def check_filter(style, filter_dict):

    element_attribute = style.element_attribute if style.element_attribute is not None else "无"

    filters = [
        ('队伍', lambda: style.team_name in filter_dict.get('队伍')),
        ('稀有度', lambda: style.rarity in filter_dict.get('稀有度')),
        ('职能', lambda: style.career in filter_dict.get('职能')),
        ('武器属性', lambda: style.weapon_attribute in filter_dict.get('武器属性')),
        ('元素属性', lambda: is_parentstring(element_attribute, filter_dict.get('元素属性')))
    ]
    return all(not filter_dict.get(key) or check() for key, check in filters)

# 角色名称昵称关键词判断
def should_include(role, style, keyword_list):
    if not keyword_list:
        return True
    
    checks = [
        list_val_in_another(role.nicknames, keyword_list),
        is_parentstring(role.en.upper(), keyword_list),
        list_val_in_another(style.nicknames, keyword_list),
        is_parentstring(style.role_name, keyword_list),
        is_parentstring(style.name, keyword_list),
        check_dict_in_list(style.id_en, keyword_list)
    ]
    
    return any(checks)

# 技能关键词判断
def check_keywords_in_skills(style, keyword_list, filter_dict):
    if not keyword_list:
        return False

    # 定义技能类型与获取方法的映射
    skill_type_map = {
        "主动/被动": lambda: style.active_skills,
        "天赋/大师被动": lambda: style.passive_skills
    }

    # 定义主动技能效果的检查函数
    def check_active_effect(effect):
        if is_skill_effect(effect):
            return (is_parentstring(effect.target, keyword_list) or
                    is_parentstring(effect.effect_type, keyword_list) or
                    is_parentstring(output_string(effect.target) + output_string(effect.effect_type), keyword_list))
        else:
            return (is_parentstring(effect.target + "攻击", keyword_list) or
                    is_parentstring(effect.biased, keyword_list) and not list_is(keyword_list, "+"))

    # 定义被动技能效果的检查函数
    def check_passive_effect(skill):
        if isinstance(skill.effect_type, list): return False
        return (is_parentstring(skill.effect_type, keyword_list) or
                is_parentstring(skill.description, keyword_list) or
                is_parentstring(output_string(skill.target) + output_string(skill.effect_type), keyword_list))

    # 遍历筛选的技能类型
    for select_skill in filter_dict.get('技能、天赋'):
        if select_skill in skill_type_map:
            skills = skill_type_map[select_skill]()
            
            # 列表遍历该类型下的所有技能对象
            for skill in skills:

                # 检查技能名称
                if is_parentstring(skill.name, keyword_list):
                    return True
                
                # 检查技能描述
                if is_parentstring(skill.description, keyword_list) and not list_is(keyword_list, "+"):
                    return True
                
                # 根据技能类型检查不同的效果
                if select_skill == "主动/被动":
                    for effect in skill.effects:
                        if check_active_effect(effect):
                            return True

                elif select_skill == "天赋/大师被动":
                    if check_passive_effect(skill): return True

    return False

# 检查风格是否符合筛选条件
def filter_judge(filter_dict, keyword_list, role, style):
    if check_filter(style, filter_dict):

        if filter_dict.get("技能、天赋") == ["共鸣天赋"]:
            if check_resonance(role, style, keyword_list): return True
        else:
            if should_include(role, style, keyword_list):
                return True

            if check_keywords_in_skills(style, keyword_list, filter_dict):
                return True

# 根据筛选条件和关键词列表获取风格对象列表
def get_filtered_styles(filter_dict, keyword_list):

    # 存储符合条件的风格对象
    filtered_styles = []

    # 构建角色到风格的映射列表
    role_style_pairs = [
        (role, style)
        for team in 角色.team_info.teams.values()
        for role in team.roles
        for style in role.SSRstyles + role.SSstyles + role.Sstyles + role.Astyles
    ]

    # 映射列表过滤，保持role和style的关联
    for role, style in role_style_pairs:
        if filter_judge(filter_dict, keyword_list, role, style):
            filtered_styles.append(style)

    return filtered_styles


# DP、SP 正则表达式替换
def replace_dp_sp(text):
    # 替换与 DP 相关的词为：回复DP
    text = re.sub(r'(回复DP|恢复DP|DP回复|DP恢复)', '回复DP', text)
    # 替换与 SP 相关的词为：回复SP
    text = re.sub(r'(SP回复|SP恢复|恢复SP|回复SP)', '回复SP', text)
    return text

# 替换与 OD 相关的词为：OD
def replace_od_up(text):
    text = re.sub(r'(超频条|超频|OD条|OD)', 'OD条', text)
    text = re.sub(r'(增加OD条|OD条增加|OD条上升)', 'OD条上升', text)
    return text

# 替换与场地相关的词为：强化领域
def replace_zone(text):
    text = re.sub(r'(场地|场|强化领域|领域)', '强化领域', text)
    text = re.sub(r'(大强化领域)', '强化领域（大）', text)
    text = re.sub(r'(小强化领域)', '强化领域（小）', text)
    return text

# 关键词处理
def keyword_processing(key_word_str):
    if not key_word_str:
        return []

    key_word_str = key_word_str.upper()
    key_word_str = replace_dp_sp(key_word_str)
    key_word_str = replace_od_up(key_word_str)
    key_word_str = replace_zone(key_word_str)
    key_word_str = key_word_str.replace(',', '，')
    key_word_str = key_word_str.replace('、', '，')

    # 加载替换字典
    replacement_dict = load_json("./搜索/replace_dict.json")

    # 关键词分割并放入列表中
    keyword_list = key_word_str.split('，')

    # 遍历替换字典，对每个字符串进行替换
    for old, new in replacement_dict.items():
        keyword_list = [s.replace(old, new) for s in keyword_list]

    return keyword_list


