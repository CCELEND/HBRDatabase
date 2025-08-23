
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import get_photo, create_canvas_with_image
from 角色.style_text import output_skill_effect

import 战斗系统.状态.status_info

# 被动技能
def creat_passive_skill_frame(parent_frame, style):
    passive_skill_frame = ttk.LabelFrame(parent_frame, text="天赋")
    passive_skill_frame.grid(row=2, column=0, columnspan=4, padx=10, pady=5, sticky="nsew")
    passive_skill_frame.grid_rowconfigure(0, weight=1)
    # 配置 passive_skill_frame 的每一列权重
    for col_index in range(4):
        passive_skill_frame.grid_columnconfigure(col_index, weight=1)

    for i, passive_skill in enumerate(style.passive_skills):
        # 使用 LabelFrame 作为每一行的容器
        row_frame = ttk.LabelFrame(passive_skill_frame, text="[Auto]"+passive_skill.name)
        row_frame.grid(row=i, column=0, columnspan=4, padx=10, pady=(0,10), sticky="nsew")
        row_frame.grid_rowconfigure(0, weight=1)
        # 配置 row_frame 的每一列权重
        for col_index in range(4):
            row_frame.grid_columnconfigure(col_index, weight=1)

        # 描述 frame
        desc_frame = ttk.Frame(row_frame)
        desc_frame.grid(row=0, column=0, columnspan=4, pady=(0,5), sticky="nsew")
        desc_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
        # 为 desc_frame 设置列权重 4:1
        desc_frame.grid_columnconfigure(0, weight=4)
        desc_frame.grid_columnconfigure(1, weight=1)

        # 技能描述
        desc_lab = ttk.Label(desc_frame, text=passive_skill.description, 
            justify="left", font=("Monospace", 10, "bold"))
        desc_lab.grid(row=0, column=0, sticky="nsw", padx=5, pady=5)

        # 突破数
        lb_lab = ttk.Label(desc_frame, text="LB"+passive_skill.LB, 
            justify="left", font=("Monospace", 10, "bold"))
        lb_lab.grid(row=0, column=1, sticky="nse", padx=5, pady=5)

        # 技能效果 frame
        effect_frame = ttk.Frame(row_frame)
        effect_frame.grid(row=1, column=0, columnspan=4, pady=(0,5),sticky="nsew")
        effect_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
        # 为 effect_frame 设置列权重 1:6
        effect_frame.grid_columnconfigure(0, weight=1, minsize=100)  # Canvas 列
        effect_frame.grid_columnconfigure(1, weight=6, minsize=600)  # 右侧信息列，权重更大以填充更多空间

        # 创建技能效果图标 canvas
        effect_photo = get_photo(战斗系统.状态.status_info.status[passive_skill.effect_type].path, (60, 60))
        effect_canvas = create_canvas_with_image(effect_frame, 
            effect_photo, 60, 60, 0, 0, 0, 0)

        text = output_skill_effect(passive_skill.turn_num, passive_skill.duration, passive_skill.target, passive_skill.effect_type,
            战斗系统.状态.status_info.status[passive_skill.effect_type].description, passive_skill.value,
            IsActive=False
        )

        effect_lab = ttk.Label(effect_frame, text=text, justify="left", font=("Monospace", 10, "bold"))
        effect_lab.grid(row=0, column=1, sticky="nsw", padx=5, pady=5)