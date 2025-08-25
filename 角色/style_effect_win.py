
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import get_photo, create_canvas_with_image

from 角色.style_text import output_attack_skill, output_skill_effect
from 角色.style_info import is_skill_effect

import 战斗系统.属性.attributes_info
import 战斗系统.状态.status_info

# 创建技能效果 frame
def creat_effect_frame(effect_frames, effect_frame_row, skill):
    
    # 技能效果 frame
    effect_frame = ttk.Frame(effect_frames)
    effect_frame.grid(row=effect_frame_row, column=0, pady=(0,5), sticky="nsew")

    effect_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    # 为 effect_frame 设置列权重 1:6
    effect_frame.grid_columnconfigure(0, weight=1, minsize=100)  # Canvas 列
    effect_frame.grid_columnconfigure(1, weight=6, minsize=600)  # 右侧信息列，权重更大以填充更多空间

    is_attack_skill = False
    # 检查是否是效果技能的实例
    if is_skill_effect(skill):
        # 创建技能效果图标 canvas
        effect_photo = get_photo(战斗系统.状态.status_info.status[skill.effect_type].path, (60, 60))
        effect_canvas = create_canvas_with_image(effect_frame, 
            effect_photo, 60, 60, 0, 0, 0, 0)

        text = output_skill_effect(skill.turn_num, skill.duration, skill.target, skill.effect_type,
            战斗系统.状态.status_info.status[skill.effect_type].description, skill.value, skill.attribute_multiplier,
            skill.attribute_difference,
            IsActive=True
        )

    # 否则就是攻击技能
    else:
        weapon_attribute = skill.weapon_attribute
        # 判断元素属性
        if skill.element_attribute:
            attack_img_path = 战斗系统.属性.attributes_info.attributes[skill.element_attribute+weapon_attribute].path
        else:
            attack_img_path = 战斗系统.属性.attributes_info.attributes[weapon_attribute].path
        # 创建攻击技能图标 canvas
        attack_photo = get_photo(attack_img_path, (60, 60))
        attack_canvas = create_canvas_with_image(effect_frame, 
            attack_photo, 60, 60, 0, 0, 0, 0)

        # 攻击技能信息
        text = output_attack_skill(skill.hit_num, skill.target, skill.hit_damage, 
            skill.biased, 
            skill.strength, skill.attribute_multiplier, 
            skill.attribute_difference, skill.destructive_multiplier
        )
        is_attack_skill = True

    desc_lab = ttk.Label(effect_frame, text=text, justify="left", font=("Monospace", 10, "bold"))
    desc_lab.grid(row=0, column=1, sticky="nsw", padx=5, pady=0)

    return desc_lab, text, is_attack_skill

