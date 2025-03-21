import sys
import os
import re

from tools import list_val_in_another, is_parentstring, output_string

sys.path.append(os.path.abspath("./角色"))
from style_info import style_categories, SkillEffect
import team_info

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

# 检查风格是否符合筛选条件
def filter_judge(filter_dict, keyword_list, style):
    element_attribute = style.element_attribute if style.element_attribute is not None else "无"

    if (not filter_dict.get('队伍') or style.team_name in filter_dict['队伍']) and \
       (not filter_dict.get('稀有度') or style.rarity in filter_dict['稀有度']) and \
       (not filter_dict.get('职能') or style.career in filter_dict['职能']) and \
       (not filter_dict.get('武器属性') or style.weapon_attribute in filter_dict['武器属性']) and \
       (not filter_dict.get('元素属性') or element_attribute in filter_dict['元素属性']):

        # if not keyword_list or list_val_in_another(keyword_list, style.nicknames):
        if not keyword_list or list_val_in_another(style.nicknames, keyword_list):
            return True

        if not keyword_list or is_parentstring(style.role_name, keyword_list):
            return True

        if keyword_list:
            for select_skill in filter_dict['技能']:
                if select_skill == "主动技能":
                    for active_skill in style.active_skills:
                        if is_parentstring(active_skill.name, keyword_list):
                            return True
                        # if is_parentstring(active_skill.description, keyword_list):
                        #     return True
                        for skill in active_skill.effects:
                            if isinstance(skill, SkillEffect):
                                if (is_parentstring(skill.target, keyword_list)) or \
                                   (is_parentstring(skill.effect_type, keyword_list)) or \
                                   (is_parentstring(output_string(skill.target)+output_string(skill.effect_type), keyword_list)):
                                    return True
                            else:
                                if (is_parentstring(skill.target+"攻击", keyword_list)) or \
                                   (is_parentstring(skill.biased, keyword_list)):
                                    return True
                if select_skill == "被动技能":
                    for passive_skill in style.passive_skills:
                        if is_parentstring(passive_skill.name, keyword_list):
                            return True
                        # if is_parentstring(passive_skill.description, keyword_list):
                        #     return True
                        if (is_parentstring(passive_skill.effect_type, keyword_list)) or \
                           (is_parentstring(passive_skill.description, keyword_list)) or \
                           (is_parentstring(output_string(passive_skill.target)+output_string(passive_skill.effect_type), keyword_list)):
                            return True


# 根据筛选条件获取风格对象列表
def get_filtered_styles(filter_dict, keyword_list):

    filtered_styles = []  # 存储符合条件的风格对象

    # 遍历队伍
    for team in team_info.teams.values():
        # 遍历队伍中的角色
        for role in team.roles:
            # 遍历角色中的风格
            for style in role.SSstyles + role.Sstyles + role.Astyles:
                if (filter_judge(filter_dict, keyword_list, style)):
                    filtered_styles.append(style)

    return filtered_styles


# DP、SP 正则表达式替换
def replace_dp_sp(text):
    # 替换与 DP 相关的词为：回复DP
    text = re.sub(r'(回复DP|恢复DP|DP回复|DP恢复)', '回复DP', text)
    # 替换与 SP 相关的词为：回复SP
    text = re.sub(r'(SP回复|SP恢复|恢复SP|回复SP)', '回复SP', text)
    return text

# 关键词处理
def keyword_processing(key_word_str):
    if not key_word_str:
        return []

    key_word_str = key_word_str.upper()
    key_word_str = replace_dp_sp(key_word_str)

    # 定义替换字典
    replacement_dict = {
        "减防": "防御下降","降防": "防御下降","降攻": "攻击下降","加防": "防御上升","加攻": "攻击上升",
        "超频": "OD",
        "TOKEN": "信念","象征":"信念",
        "大范围": "全体","群体": "全体","AOE":"全体",
        "场":"强化领域",
        "追加回合":"额外回合",
        "暴伤":"暴击伤害",
        "TAMA":"玉","AOI":"苍井",
        "大连击":"连击数上升（大）","小连击":"连击数上升（小）",
        "封印":"禁锢"
    }

    # 关键词分割并放入列表中
    keyword_list = key_word_str.split('，')

    # 遍历替换字典，对每个字符串进行替换
    for old, new in replacement_dict.items():
        keyword_list = [s.replace(old, new) for s in keyword_list]

    return keyword_list


