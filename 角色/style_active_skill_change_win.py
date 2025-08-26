
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from tools import get_list_not_isinstance_index
from 角色.style_effect_win import delete_all_effect_frame, set_effect_frames
from 角色.style_combobox_win import bind_lv_combo_lab

# 如果有技能切换
def is_skill_change(active_skill):
    if active_skill.switch:
        return True
    else:
        return False

# 技能切换按钮触发
def active_skill_change_proc(row_frame, change_effects_infos, active_skill):

    # 获取切换技能效果信息列表的描述索引
    desc_index = get_list_not_isinstance_index(change_effects_infos)
    if desc_index:
        desc = change_effects_infos[desc_index]
        sp_cost = change_effects_infos[desc_index+1]
        max_uses = change_effects_infos[desc_index+2]
        name = change_effects_infos[desc_index+3]

        # desc_frame = row_frame.grid_slaves(row=0, column=0)[0]
        # desc_frame_desc_lab = desc_frame.grid_slaves(row=0, column=0)[0]
        desc_frame = row_frame.nametowidget("desc_frame")
        desc_frame_desc_lab = desc_frame.nametowidget("desc_frame_desc_lab")
        desc_frame_desc_lab.config(text=desc)

        if name:
            row_frame.config(text=name)

    # 遍历 effect_frames 销毁之前的 effect_frame
    effect_frames = row_frame.nametowidget("effect_frames")
    delete_all_effect_frame(effect_frames)

    show_effects = []
    for effects_index in change_effects_infos[:desc_index]:
        show_effects.append(active_skill.effects[effects_index])

    # 重新设置 effect_frames
    lv_combo_labs, lv_combo_texts = set_effect_frames(effect_frames, show_effects)

    # 绑定
    lv_combo_lab_frame = row_frame.nametowidget("lv_combo_lab_frame")
    lv_combo = lv_combo_lab_frame.nametowidget("lv_combo")
    bind_lv_combo_lab(lv_combo, lv_combo_labs, lv_combo_texts)
    lv_combo.set("Skill Lv.1")


# 创建切换技能按钮并绑定点击处理函数
def creat_active_skill_change_frame(parent_frame, active_skill):

    change_button_frame = ttk.Frame(parent_frame)
    change_button_frame.grid(row=1, column=0, columnspan=4, pady=5, sticky="nsew")
    change_button_frame.grid_rowconfigure(0, weight=1)  # 确保行填充

    default_change_name = ""
    for i, change_name in enumerate(active_skill.switch):
        if not default_change_name: 
            default_change_name = change_name

        # 切换技能效果信息列表
        change_effects_infos = active_skill.switch[change_name]

        change_button = ttk.Button(change_button_frame, 
            width=5, text=change_name, bootstyle="primary-outline",
            command=lambda change_effects_infos=change_effects_infos: active_skill_change_proc(parent_frame, change_effects_infos, active_skill))

        change_button.grid(row=0, column=i, padx=(10,0), sticky="nsew")
        change_button_frame.grid_columnconfigure(i, weight=1)

    # 默认的切换技能列表
    default_change_effects = []
    default_change_effects_infos = active_skill.switch[default_change_name]
    desc_index = get_list_not_isinstance_index(change_effects_infos)
    for default_effects_index in default_change_effects_infos[:desc_index]:
        default_change_effects.append(active_skill.effects[default_effects_index])

    # print(default_change_effects)
    return default_change_effects