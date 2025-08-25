
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from tools import get_list_not_isinstance_index

# 如果有技能切换
def is_skill_change(active_skill):
    if active_skill.switch:
        return True
    else:
        return False

# 技能切换按钮触发
def active_skill_change_proc(parent_frame, change_effects_infos, active_skill):

    # 获取切换技能效果信息列表的描述索引
    desc_index = get_list_not_isinstance_index(change_effects_infos)
    if desc_index:
        desc = change_effects_infos[desc_index]
        sp_cost = change_effects_infos[desc_index+1]
        max_uses = change_effects_infos[desc_index+2]
        name = change_effects_infos[desc_index+3]


        # desc_frame = parent_frame.grid_slaves(row=0, column=0)[0]
        # desc_frame_desc_lab = desc_frame.grid_slaves(row=0, column=0)[0]
        desc_frame = parent_frame.nametowidget("desc_frame")
        desc_frame_desc_lab = desc_frame.nametowidget("desc_frame_desc_lab")
        desc_frame_desc_lab.config(text="test")
        # parent_frame.config(text=f"AAAA")


    # lv_combo_lab_frame = parent_frame.nametowidget("lv_combo_lab_frame")
    # lv_combo_lab_frame.destroy()
    # change_effect_indexs = change_effects_infos[:desc_index]
    # creat_effect_frame()


# active_skill.effects

def creat_active_skill_change_frame(parent_frame, active_skill_change_frame_row, 
    active_skill):

    change_button_frame = ttk.Frame(parent_frame)
    change_button_frame.grid(row=active_skill_change_frame_row, 
        column=0, pady=5, sticky="nsew")

    default_change_effects = []
    default_change_name = ""
    for i, change_name in enumerate(active_skill.switch):
        if not default_change_name: 
            default_change_name = change_name

        # 切换技能效果信息列表
        change_effects_infos = active_skill.switch[change_name]

        change_button = ttk.Button(change_button_frame, 
            width=5, text=change_name, bootstyle="primary-outline",
            command=lambda: active_skill_change_proc(parent_frame, change_effects_infos, active_skill))

        change_button.grid(row=0, column=i, padx=(10,0))

    
    default_change_effects_infos = active_skill.switch[default_change_name]
    desc_index = get_list_not_isinstance_index(change_effects_infos)
    for default_effects_index in default_change_effects_infos[:desc_index]:
        default_change_effects.append(active_skill.effects[default_effects_index])

    
    # print(default_change_effects)
    return default_change_effects