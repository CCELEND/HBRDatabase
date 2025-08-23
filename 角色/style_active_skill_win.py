
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import get_photo, create_canvas_with_image

from 角色.style_info import is_skill_effect
from 角色.style_text import output_attack_skill, output_skill_effect
from 角色.style_combobox_win import bind_lv_combo_lab

import 战斗系统.属性.attributes_info
import 战斗系统.状态.status_info

# 主动技能描述 frame
def creat_desc_frame(row_frame, active_skill):
    
    desc_frame = ttk.Frame(row_frame)
    desc_frame.grid(row=0, column=0, columnspan=4, pady=(0,5), sticky="nsew")
    desc_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    # 为 desc_frame 设置列权重 4:1:1
    desc_frame.grid_columnconfigure(0, weight=4, minsize=400)
    desc_frame.grid_columnconfigure(1, weight=1, minsize=100)
    desc_frame.grid_columnconfigure(2, weight=1, minsize=100)
    # 技能描述
    desc_lab = ttk.Label(desc_frame, text=active_skill.description, 
        justify="left", font=("Monospace", 10, "bold"))
    desc_lab.grid(row=0, column=0, sticky="nsw", padx=5, pady=0)
    # 技能强化等级需求
    text = ""
    for level_req in active_skill.level_reqs:
        text += "Lv" + level_req + " "
    level_req_lab = ttk.Label(desc_frame, text=text, 
        justify="left", font=("Monospace", 10, "bold"))
    level_req_lab.grid(row=0, column=1, sticky="nse", padx=5, pady=5)
    # 技能消耗SP和使用次数
    if active_skill.max_uses:
        text = "SP" + active_skill.sp_cost + '\n' + active_skill.max_uses
    else:
        text = "SP" + active_skill.sp_cost + '\n' + "∞"
    sp_use_lab = ttk.Label(desc_frame, text=text, 
        justify="right", font=("Monospace", 10, "bold"))
    sp_use_lab.grid(row=0, column=2, sticky="nse", padx=5, pady=5)



# 主动技能
def creat_active_skill_frame(parent_frame, style):

    # combos = {}
    # 创建自定义样式
    style_tc = ttk.Style()
    # 定义自定义样式
    style_tc.configure(
        "Custom.TCombobox",  # 样式名格式：自定义名.控件类型
        background="#f0f0f0",  # 背景色
        fieldbackground="#f0f0f0"  # 输入框背景色
    )

    # 主动技能、被动
    active_skill_frame = ttk.LabelFrame(parent_frame, text="主动技能 / 被动技能")
    active_skill_frame.grid(row=1, column=0, columnspan=4, padx=10, pady=5, sticky="nsew")
    active_skill_frame.grid_rowconfigure(0, weight=1)
    # 配置 active_skill_frame 的每一列权重
    for col_index in range(4):
        active_skill_frame.grid_columnconfigure(col_index, weight=1)

    # 主动技能列表
    for i, active_skill in enumerate(style.active_skills):
        row_frame = ttk.LabelFrame(active_skill_frame, text=active_skill.name)
        row_frame.grid(row=i, column=0, columnspan=4, padx=10, pady=(0,10), sticky="nsew") #5
        row_frame.grid_rowconfigure(0, weight=1)
        # 配置 row_frame 的每一列权重
        for col_index in range(4):
            row_frame.grid_columnconfigure(col_index, weight=1)

        # 一个主动技能的描述 frame
        creat_desc_frame(row_frame, active_skill)

        att_lv_combo_text = ""
        att_lv_combo_lab = None
        main_lv_combo_text = ""
        main_lv_combo_lab = None
        main_effect_flag = False
        # 技能效果列表
        for j, skill in enumerate(active_skill.effects):

            # 技能效果 frame
            effect_frame = ttk.Frame(row_frame)
            effect_frame.grid(row=j+1, column=0, columnspan=4, pady=(0,5), sticky="nsew")
            effect_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
            # 为 effect_frame 设置列权重 1:6
            effect_frame.grid_columnconfigure(0, weight=1, minsize=100)  # Canvas 列
            effect_frame.grid_columnconfigure(1, weight=6, minsize=600)  # 右侧信息列，权重更大以填充更多空间

            # 检查是否是技能效果的实例
            # if isinstance(skill, SkillEffect):
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

            desc_lab = ttk.Label(effect_frame, text=text, justify="left", font=("Monospace", 10, "bold"))
            desc_lab.grid(row=0, column=1, sticky="nsw", padx=5, pady=0)

            # 如果是攻击技能
            # if not isinstance(skill, SkillEffect):
            if not is_skill_effect(skill):
                if not att_lv_combo_text:
                    att_lv_combo_text = text
                    att_lv_combo_lab = desc_lab
            else:
                if not main_lv_combo_text:
                    main_lv_combo_text = text
                    main_lv_combo_lab = desc_lab

                # 主效果（暗忍触发）
                if skill.main_effect:
                    main_effect_flag = True
                    main_lv_combo_text = text
                    main_lv_combo_lab = desc_lab

        lv_combo_labs = []
        lv_combo_texts = []
        if att_lv_combo_text:
            lv_combo_texts.append(att_lv_combo_text)
            lv_combo_labs.append(att_lv_combo_lab)
            if main_effect_flag:
                lv_combo_texts.append(main_lv_combo_text)
                lv_combo_labs.append(main_lv_combo_lab)
        else:
            lv_combo_texts.append(main_lv_combo_text)
            lv_combo_labs.append(main_lv_combo_lab)

        # print(lv_combo_texts)
        # 新建并绑定技能等级选择框
        bind_lv_combo_lab(row_frame, active_skill, lv_combo_labs, lv_combo_texts)