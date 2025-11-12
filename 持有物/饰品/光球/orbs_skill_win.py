
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import get_photo, create_canvas_with_image
from window import set_window_expand, creat_Toplevel, set_window_icon
from window import win_open_manage, win_close_manage, is_win_open, win_set_top
from scrollbar_frame_win import ScrollbarFrameWin

from 角色.style_text import output_skill_effect
import 战斗系统.状态.status_info

# 加载资源文件
def load_resources():
    战斗系统.状态.status_info.get_all_statu_obj()


# 光球技能描述 frame
def creat_desc_frame(row_frame, orb_skill):
    
    desc_frame = ttk.Frame(row_frame)
    desc_frame.grid(row=0, column=0, columnspan=4, pady=(0,5), sticky="nsew")
    desc_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    # 为 desc_frame 设置列权重 4:1
    desc_frame.grid_columnconfigure(0, weight=4, minsize=400)
    desc_frame.grid_columnconfigure(1, weight=1, minsize=100)

    # 技能描述
    desc_lab = ttk.Label(desc_frame, text=orb_skill.description, 
        justify="left", font=("Monospace", 10, "bold"))
    desc_lab.grid(row=0, column=0, sticky="nsw", padx=5, pady=0)

    # 技能消耗SP和使用次数
    if orb_skill.max_uses:
        text = "SP" + orb_skill.sp_cost + '\n' + orb_skill.max_uses
    else:
        text = "SP" + orb_skill.sp_cost + '\n' + "∞"
    sp_use_lab = ttk.Label(desc_frame, text=text, 
        justify="right", font=("Monospace", 10, "bold"))
    sp_use_lab.grid(row=0, column=1, sticky="nse", padx=5, pady=5)


# 光球技能
def creat_orb_skill_frame(scrollbar_frame_obj, orb_skill):

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    row_frame = ttk.Labelframe(scrollbar_frame_obj.scrollable_frame, text=orb_skill.name)
    row_frame.grid(row=0, column=0, columnspan=4, padx=10, pady=(0,10), sticky="nsew") #5
    row_frame.grid_rowconfigure(0, weight=1)
    # 配置 row_frame 的每一列权重
    for col_index in range(4):
        row_frame.grid_columnconfigure(col_index, weight=1)

    # 一个主动技能的描述 frame
    creat_desc_frame(row_frame, orb_skill)

    # 技能效果列表
    for j, skill in enumerate(orb_skill.effects):

        # 技能效果 frame
        effect_frame = ttk.Frame(row_frame)
        effect_frame.grid(row=j+1, column=0, columnspan=4, pady=(0,5), sticky="nsew")
        effect_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
        # 为 effect_frame 设置列权重 1:6
        effect_frame.grid_columnconfigure(0, weight=1, minsize=100)  # Canvas 列
        effect_frame.grid_columnconfigure(1, weight=6, minsize=600)  # 右侧信息列，权重更大以填充更多空间

        # 创建技能效果图标 canvas
        effect_photo = get_photo(战斗系统.状态.status_info.status[skill.effect_type].path, (60, 60))
        effect_canvas = create_canvas_with_image(effect_frame, 
            effect_photo, 60, 60, 0, 0, 0, 0)

        text = output_skill_effect(skill.turn_num, skill.duration, skill.target, skill.effect_type,
            战斗系统.状态.status_info.status[skill.effect_type].description, skill.value, skill.attribute_multiplier,
            skill.attribute_difference,
            IsActive=True
        )

        desc_lab = ttk.Label(effect_frame, text=text, justify="left", font=("Monospace", 10, "bold"))
        desc_lab.grid(row=0, column=1, sticky="nsw", padx=5, pady=0)


def creat_orb_skill_win(event, parent_frame, orb):

    # 初始化资源文件
    load_resources()

    # 光球技能对象
    orb_skill = orb.skill

    open_orb_win = orb_skill.name
    # 重复打开时，窗口置顶并直接返回
    if is_win_open(open_orb_win, __name__):
        win_set_top(open_orb_win, __name__)
        return "break"

    orb_win_frame = creat_Toplevel(open_orb_win, 812, 300, 350, 280)
    set_window_expand(orb_win_frame, rowspan=1, columnspan=2)
    set_window_icon(orb_win_frame, orb.path)
    scrollbar_frame_obj = ScrollbarFrameWin(orb_win_frame, columnspan=2)

    win_open_manage(orb_win_frame, __name__)

    # 绑定鼠标点击事件到父窗口，点击置顶
    orb_win_frame.bind("<Button-1>", win_set_top(orb_win_frame, __name__))
    # 窗口关闭时清理
    orb_win_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(orb_win_frame, __name__))

    creat_orb_skill_frame(scrollbar_frame_obj, orb_skill)

    return "break"  # 阻止事件冒泡
