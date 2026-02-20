
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from tools import get_list_not_isinstance_index
from 角色.style_effect_win import delete_all_effect_frame, set_effect_frames
from 角色.style_combobox_win import bind_lv_combo_lab

# 如果有技能切换
def is_skill_change(active_skill) -> bool:
    if active_skill.switch:
        return True
    else:
        return False

# 技能切换按钮触发
def active_skill_change_proc(scrollbar_frame_obj, row_frame, change_effects_infos, active_skill):

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

        desc_frame_sp_use_lab = desc_frame.nametowidget("desc_frame_sp_use_lab")
        if sp_cost:
            # 有SP消耗时才处理显示
            uses_text = max_uses if max_uses else "∞"
            text = f"SP{sp_cost}\n{uses_text}"
            desc_frame_sp_use_lab.config(text=text)

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

    # effect_frames 重新设置会导致布局改变，需要重新刷新滚动条
    scrollbar_frame_obj.update_canvas()

# 共享管理器
class ChangeButtonManager:
    def __init__(self):
        self.current_button = None
        self.current_name = ""
    
    def handle_button_click(self, scrollbar_frame_obj, parent_frame, change_effects_infos, 
                          active_skill, button, change_name):

        active_skill_change_proc(scrollbar_frame_obj, parent_frame, change_effects_infos, active_skill)
        
        # 高亮处理
        if self.current_button is not None:
            self.current_button.config(bootstyle="primary-outline")
        
        # 设置当前按钮为高亮
        button.config(bootstyle="primary")
        self.current_button = button
        self.current_name = change_name


# 创建切换技能按钮并绑定点击处理函数
def creat_active_skill_change_frame(scrollbar_frame_obj, parent_frame, active_skill) -> list:
    # 创建共享管理器实例
    button_manager = ChangeButtonManager()
    
    change_button_frame = ttk.Frame(parent_frame)
    change_button_frame.grid(row=1, column=0, columnspan=4, pady=5, sticky="nsew")
    change_button_frame.grid_rowconfigure(0, weight=1)

    default_change_name = ""
    buttons = []  # 存储所有按钮引用
    for i, change_name in enumerate(active_skill.switch):
        if not default_change_name: 
            default_change_name = change_name

        change_effects_infos = active_skill.switch[change_name]

        # 创建按钮
        change_button = ttk.Button(change_button_frame, 
            text=change_name, bootstyle="primary-outline")
        
        # 闭包保存当前按钮
        def make_command(cn=change_name, cei=change_effects_infos, btn=change_button):
            return lambda: button_manager.handle_button_click(
                scrollbar_frame_obj, parent_frame, cei, active_skill, btn, cn
            )
        
        change_button.config(command=make_command())
        change_button.grid(row=0, column=i, padx=(10,0), sticky="nsew")
        buttons.append(change_button)
    
    # 默认选中第一个按钮
    if buttons:
        buttons[0].config(bootstyle="primary")
        button_manager.current_button = buttons[0]
        button_manager.current_name = list(active_skill.switch.keys())[0]

    # 默认的切换技能列表
    default_change_effects = []
    default_change_effects_infos = active_skill.switch[default_change_name]
    desc_index = get_list_not_isinstance_index(default_change_effects_infos)
    for default_effects_index in default_change_effects_infos[:desc_index]:
        # print(default_effects_index)
        default_change_effects.append(active_skill.effects[default_effects_index])

    # print(default_change_effects)
    # print(default_change_effects_infos)
    return default_change_effects