
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from tools import not_letter

from 角色.style_combobox_win import creat_lv_combo_lab, bind_lv_combo_lab
from 角色.style_active_skill_change_win import creat_active_skill_change_frame, is_skill_change

from 角色.style_effect_win import set_effect_frames

# 主动技能描述 frame
def creat_desc_frame(row_frame, desc_frame_row, active_skill):
    
    desc_frame = ttk.Frame(row_frame, name="desc_frame")
    desc_frame.grid(row=desc_frame_row, column=0, columnspan=4, pady=(0,5), sticky="nsew")
    desc_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    # 为 desc_frame 设置列权重 4:1:1
    desc_frame.grid_columnconfigure(0, weight=4, minsize=400)
    desc_frame.grid_columnconfigure(1, weight=1, minsize=100)
    desc_frame.grid_columnconfigure(2, weight=1, minsize=100)

    # 技能描述
    desc_lab = ttk.Label(desc_frame, text=active_skill.description, 
        justify="left", font=("Monospace", 10, "bold"), name="desc_frame_desc_lab")
    desc_lab.grid(row=0, column=0, sticky="nsw", padx=5, pady=0)

    # 技能强化等级需求
    text = ""
    for level_req in active_skill.level_reqs:
        text += "Lv" + level_req + " "
    level_req_lab = ttk.Label(desc_frame, text=text, 
        justify="left", font=("Monospace", 10, "bold"))
    level_req_lab.grid(row=0, column=1, sticky="nse", padx=5, pady=5)

    # 技能消耗SP和使用次数
    sp_cost_text = "SP" + active_skill.sp_cost if not_letter(active_skill.sp_cost) else active_skill.sp_cost
    uses_text = active_skill.max_uses if active_skill.max_uses else "∞"
    text = f"{sp_cost_text}\n{uses_text}"
    
    sp_use_lab = ttk.Label(desc_frame, text=text, 
        justify="right", font=("Monospace", 10, "bold"), name="desc_frame_sp_use_lab")
    sp_use_lab.grid(row=0, column=2, sticky="nse", padx=5, pady=5)


# 主动技能
def creat_active_skill_frame(scrollbar_frame_obj, parent_frame, active_skill_frame_row, style):

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
    active_skill_frame = ttk.Labelframe(parent_frame, text="主动技能 / 被动技能")
    active_skill_frame.grid(row=active_skill_frame_row, column=0, columnspan=4, padx=10, pady=5, sticky="nsew")
    active_skill_frame.grid_rowconfigure(0, weight=1)
    # 配置 active_skill_frame 的每一列权重
    for col_index in range(4):
        active_skill_frame.grid_columnconfigure(col_index, weight=1)

    # 主动、被动技能列表
    for i, active_skill in enumerate(style.active_skills):
        row_frame = ttk.Labelframe(active_skill_frame, text=active_skill.name)
        row_frame.grid(row=i, column=0, columnspan=4, padx=10, pady=(0,10), sticky="nsew") #5
        row_frame.grid_rowconfigure(0, weight=1)
        # 配置 row_frame 的每一列权重
        for col_index in range(4):
            row_frame.grid_columnconfigure(col_index, weight=1)

        # 主动技能的描述 frame
        creat_desc_frame(row_frame, 0, active_skill)


        effect_frames_row = 1
        # 判断是否存在切换技能
        if is_skill_change(active_skill):
            # 创建技能切换按钮 frame
            show_effects = creat_active_skill_change_frame(scrollbar_frame_obj, row_frame, active_skill)
            effect_frames_row += 1
        else:
            show_effects = active_skill.effects


        # 技能效果 frames
        effect_frames = ttk.Frame(row_frame, name="effect_frames")
        effect_frames.grid(row=effect_frames_row, column=0, columnspan=4, sticky="nsew")
        effect_frames.grid_rowconfigure(0, weight=1)  # 确保行填充
        effect_frames.grid_columnconfigure(0, weight=1) # 列填充

        lv_combo_labs, lv_combo_texts = set_effect_frames(effect_frames, show_effects)

        # 新建并绑定技能等级选择框
        lv_combo_row = effect_frames_row + 1
        lv_combo_lab_frame = ttk.Frame(row_frame, name="lv_combo_lab_frame")
        lv_combo_lab_frame.grid(row=lv_combo_row, column=0, columnspan=4, sticky="nsew")
        lv_combo_lab_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
        lv_combo_lab_frame.grid_columnconfigure(0, weight=1) # 列填充
        lv_combo_lab_frame.grid_columnconfigure(1, weight=3) # 列填充

        level_max = int(active_skill.level_max)
        lv_combo = creat_lv_combo_lab(lv_combo_lab_frame, level_max)
        bind_lv_combo_lab(lv_combo, lv_combo_labs, lv_combo_texts)
