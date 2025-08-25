

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from functools import partial

from 角色.style_proc import on_attack_combo_select, on_buff_attack_combo_select
from 角色.style_proc import on_heal_combo_select
from 角色.style_proc import on_hit_combo_select, on_defense_combo_select, on_buff_combo_select
from 角色.style_proc import on_debuff_combo_select
from 角色.style_proc import on_mindeye_combo_select
from 角色.style_proc import on_percentage_combo_select

# from 角色.style_active_skill_change_win import is_skill_change

skill_options = [
    "Skill Lv.1", "Skill Lv.2", "Skill Lv.3", "Skill Lv.4", "Skill Lv.5", "Skill Lv.6", "Skill Lv.7", "Skill Lv.8", "Skill Lv.9", "Skill Lv.10", 
    "Skill Lv.11", "Skill Lv.12", "Skill Lv.13", 
    "Skill Lv.14", "Skill Lv.15", "Skill Lv.16", "Skill Lv.17"
]

# 新建并绑定技能等级选择框
def bind_lv_combo_lab(parent_frame, active_skill, lv_combo_labs, lv_combo_texts):
    # lv_combo_name = active_skill.name

    level_max = int(active_skill.level_max)

    lv_combo = ttk.Combobox(parent_frame, 
        values=skill_options[:level_max], style="Custom.TCombobox")
    lv_combo.grid(row=0, column=0, sticky="nswe", padx=10, pady=(5,10))
    lv_combo.configure(state="readonly")
    lv_combo.set("Skill Lv.1")


    if "技能强度" in lv_combo_texts[0]:
        # combos[active_skill.name+"_attack"] = lv_combo
        if len(lv_combo_texts) == 2:
            lv_combo.bind(
                "<<ComboboxSelected>>", 
                partial(on_buff_attack_combo_select, desc_labs=lv_combo_labs, lv1_skill_strengths=lv_combo_texts)
            )
        else:            
            lv_combo.bind(
                "<<ComboboxSelected>>", 
                partial(on_attack_combo_select, desc_lab=lv_combo_labs[0], lv1_skill_strength=lv_combo_texts[0])
            )
    elif "回复DP" in lv_combo_texts[0]:
        # combos[active_skill.name+"_heal"] = lv_combo
        lv_combo.bind(
            "<<ComboboxSelected>>", 
            partial(on_heal_combo_select, desc_lab=lv_combo_labs[0], lv1_skill_strength=lv_combo_texts[0])
        )
    elif "防御上升" in lv_combo_texts[0]:
        # combos[active_skill.name+"_defense"] = lv_combo
        lv_combo.bind(
            "<<ComboboxSelected>>", 
            partial(on_defense_combo_select, desc_lab=lv_combo_labs[0], lv1_skill_strength=lv_combo_texts[0])
        )
    elif "连击数上升" in lv_combo_texts[0]:
        # combos[active_skill.name+"_defense"] = lv_combo
        lv_combo.bind(
            "<<ComboboxSelected>>", 
            partial(on_hit_combo_select, desc_lab=lv_combo_labs[0], lv1_skill_strength=lv_combo_texts[0])
        )
    elif "上升" in lv_combo_texts[0]:
        # combos[active_skill.name+"_buff"] = lv_combo
        lv_combo.bind(
            "<<ComboboxSelected>>", 
            partial(on_buff_combo_select, desc_lab=lv_combo_labs[0], lv1_skill_strength=lv_combo_texts[0])
        )
    elif "下降" in lv_combo_texts[0]:
        # combos[active_skill.name+"_debuff"] = lv_combo
        lv_combo.bind(
            "<<ComboboxSelected>>", 
            partial(on_debuff_combo_select, desc_lab=lv_combo_labs[0], lv1_skill_strength=lv_combo_texts[0])
        )
    elif "心眼" in lv_combo_texts[0]:
        # combos[active_skill.name+"_buff"] = lv_combo
        lv_combo.bind(
            "<<ComboboxSelected>>", 
            partial(on_mindeye_combo_select, desc_lab=lv_combo_labs[0], lv1_skill_strength=lv_combo_texts[0])
        )        
    elif "百分比的伤害" in lv_combo_texts[0]:
        # combos[active_skill.name+"_other"] = lv_combo
        lv_combo.bind(
            "<<ComboboxSelected>>", 
            partial(on_percentage_combo_select, desc_lab=lv_combo_labs[0], lv1_skill_strength=lv_combo_texts[0])
        )