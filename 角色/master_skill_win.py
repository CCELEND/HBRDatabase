
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import get_photo, create_canvas_with_image
from window import set_window_expand, creat_Toplevel, set_window_top, set_window_icon
from window import win_open_manage, win_close_manage, is_win_open, win_set_top
from scrollbar_frame_win import ScrollbarFrameWin

from 角色.master_skill_info import MasterSkillEffect
from 角色.style_text import output_skill_effect, output_attack_skill
from 角色.team_info import get_team_logo_path
import 战斗系统.状态.status_info
import 战斗系统.属性.attributes_info

# 加载资源文件
def load_resources():
    战斗系统.状态.status_info.get_all_statu_obj()
    战斗系统.属性.attributes_info.get_all_attribute_obj()


# 大师技能描述 frame
def creat_desc_frame(row_frame, master_skill):
    
    desc_frame = ttk.Frame(row_frame)
    desc_frame.grid(row=0, column=0, columnspan=4, pady=(0,5), sticky="nsew")
    desc_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
    # 为 desc_frame 设置列权重 4:1
    desc_frame.grid_columnconfigure(0, weight=4, minsize=400)
    desc_frame.grid_columnconfigure(1, weight=1, minsize=100)

    # 技能描述
    desc_lab = ttk.Label(desc_frame, text=master_skill.description, 
        justify="left", font=("Monospace", 10, "bold"))
    desc_lab.grid(row=0, column=0, sticky="nsw", padx=5, pady=0)

    # 技能消耗SP和使用次数
    if master_skill.max_uses:
        text = "SP" + master_skill.sp_cost + '\n' + master_skill.max_uses
    else:
        if master_skill.sp_cost == "被动技能":
            text = master_skill.sp_cost + '\n' + "∞"
        else:
            text = "SP" + master_skill.sp_cost + '\n' + "∞"
    sp_use_lab = ttk.Label(desc_frame, text=text, 
        justify="right", font=("Monospace", 10, "bold"))
    sp_use_lab.grid(row=0, column=1, sticky="nse", padx=5, pady=5)


# 大师技能
def creat_master_skill_frame(scrollbar_frame_obj, master_skill):

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    row_frame = ttk.Labelframe(scrollbar_frame_obj.scrollable_frame, text=master_skill.name)
    row_frame.grid(row=0, column=0, columnspan=4, padx=10, pady=(0,10), sticky="nsew") #5
    row_frame.grid_rowconfigure(0, weight=1)
    # 配置 row_frame 的每一列权重
    for col_index in range(4):
        row_frame.grid_columnconfigure(col_index, weight=1)

    # 大师技能的描述 frame
    creat_desc_frame(row_frame, master_skill)

    # 技能效果或者攻击技能列表
    for j, skill in enumerate(master_skill.effects):
        # 技能效果 frame
        effect_frame = ttk.Frame(row_frame)
        effect_frame.grid(row=j+1, column=0, columnspan=4, pady=(0,5), sticky="nsew")
        effect_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
        # 为 effect_frame 设置列权重 1:6
        effect_frame.grid_columnconfigure(0, weight=1, minsize=100)  # Canvas 列
        effect_frame.grid_columnconfigure(1, weight=6, minsize=600)  # 右侧信息列，权重更大以填充更多空间

        if isinstance(skill, MasterSkillEffect):
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

    missions_row = 1 + len(master_skill.effects)
    missions_lab = ttk.Label(row_frame, text=master_skill.missions , justify="left", font=("Monospace", 10, "bold"))
    missions_lab.grid(row=missions_row, column=0, sticky="nsw", padx=5, pady=0)


def creat_master_skill_win(event, parent_frame, role):

    # 初始化资源文件
    load_resources()

    # 大师技能对象
    master_skill = role.master_skill

    # open_master_win = master_skill.name+"-大师技能"
    open_master_win = master_skill.name+f"—{role.name}"
    # 重复打开时，窗口置顶并直接返回
    if is_win_open(open_master_win, __name__):
        win_set_top(open_master_win, __name__)
        return "break"

    master_win_frame = creat_Toplevel(open_master_win, 812, 300, 560, 510)
    set_window_expand(master_win_frame, rowspan=1, columnspan=2)
    set_window_icon(master_win_frame, get_team_logo_path(role.team))
    scrollbar_frame_obj = ScrollbarFrameWin(master_win_frame, columnspan=2)

    win_open_manage(master_win_frame, __name__)

    # 绑定鼠标点击事件到父窗口，点击置顶
    master_win_frame.bind("<Button-1>", lambda event: set_window_top(master_win_frame))
    # 窗口关闭时清理
    master_win_frame.protocol("WM_DELETE_WINDOW", 
        lambda: win_close_manage(master_win_frame, __name__))


    creat_master_skill_frame(scrollbar_frame_obj, master_skill)

    return "break"  # 阻止事件冒泡
