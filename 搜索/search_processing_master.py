

from tools import list_val_in_another, is_parentstring, output_string, list_is

from 角色.master_skill_info import is_master_skill_effect, is_master_skill_passive, get_master_skill_type
import 角色.team_info


# 复选判断
def check_filter(role, filter_dict):

    filters = [
        ('队伍', lambda: role.team in filter_dict['队伍']),
        ('武器属性', lambda: role.weapon_attribute in filter_dict['武器属性']),
        ('技能', lambda: get_master_skill_type(role.master_skill) in filter_dict['技能'])
    ]
    return all(not filter_dict.get(key) or check() for key, check in filters)

# 角色名称关键词判断
def should_include(role, keyword_list, filter_dict):
    # 没有关键词和选中技能时返回真
    if not keyword_list and not filter_dict["技能"]:
        return True

    checks = [
        list_val_in_another(role.nicknames, keyword_list),
        is_parentstring(role.en, keyword_list),
        is_parentstring(role.name, keyword_list)
    ]
    
    return any(checks)


# 技能关键词判断
def check_keywords_in_skills(master_skill, keyword_list, filter_dict):
    # 关键词为空返回
    if not keyword_list:
        return False

    # 定义技能效果的检查函数
    def check_effect(effect):
        if is_master_skill_effect(effect):
            return (is_parentstring(effect.target, keyword_list) or
                    is_parentstring(effect.effect_type, keyword_list) or
                    is_parentstring(output_string(effect.target) + output_string(effect.effect_type), keyword_list))
        else:
            return (is_parentstring(effect.target + "攻击", keyword_list) or
                    is_parentstring(effect.biased, keyword_list) and not list_is(keyword_list, "+"))



    for select_skill in filter_dict['技能']:
        is_select_active = (select_skill == "主动技能")
        # 判断master_skill是主动还是被动
        is_master_passive = is_master_skill_passive(master_skill)
        is_master_active = not is_master_passive
        
        # 技能类型不匹配时跳过检查（主动对被动 或 被动对主动）
        if (is_select_active and is_master_passive) or (not is_select_active and is_master_active):
            continue
        
        # 检查技能名称
        if is_parentstring(master_skill.name, keyword_list):
            return True
        
        # 检查技能描述
        if is_parentstring(master_skill.description, keyword_list) and not list_is(keyword_list, "+"):
            return True

        # 检查技能效果
        for effect in master_skill.effects:
            if check_effect(effect):
                return True

    return False

# 检查大师技能对象是否符合筛选条件
def filter_judge(filter_dict, keyword_list, role):

    if not role.master_skill:
        return False

    if check_filter(role, filter_dict):

        if should_include(role, keyword_list, filter_dict):
            return True

        master_skill = role.master_skill
        if check_keywords_in_skills(master_skill, keyword_list, filter_dict):
            return True

        if not keyword_list:
            return True


# 根据筛选条件和关键词列表获取大师技能对象列表
def get_filtered_master_skills(filter_dict, keyword_list):

    # 存储符合条件的大师技能对象
    filtered_master_skills = []

    for team in 角色.team_info.teams.values():
        for role in team.roles:
            if filter_judge(filter_dict, keyword_list, role):
                filtered_master_skills.append(role.master_skill)

    return filtered_master_skills







