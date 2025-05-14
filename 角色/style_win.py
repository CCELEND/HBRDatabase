import sys
import os
from PIL import Image, ImageTk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from functools import partial
import re
import math

from canvas_events import get_photo, create_canvas_with_image, VideoPlayer, ArtworkDisplayer, ArtworkDisplayerHeight
from canvas_events import ImageViewerWithScrollbar, VideoPlayerWithScrollbar
from window import set_window_expand, set_window_icon, creat_Toplevel, set_window_top
from scrollbar_frame_win import ScrollbarFrameWin
from tools import load_json, output_string, is_parentstring, int_to_comma_str

from style_info import SkillEffect
from style_proc import get_hit_damage_str
from style_proc import on_attack_combo_select, on_heal_combo_select, on_buff_combo_select, on_debuff_combo_select, on_mindeye_combo_select

import 强化素材.strengthen_materials_win
import 职业.careers_info
import 属性.attributes_info
import 状态.status_info

# 加载资源文件
def load_resources():
    强化素材.strengthen_materials_win.load_resources()
    职业.careers_info.get_all_career_obj()
    状态.status_info.get_all_statu_obj()
    属性.attributes_info.get_all_attribute_obj()

skill_options = ["Skill Lv.1", "Skill Lv.2", "Skill Lv.3", "Skill Lv.4", "Skill Lv.5", "Skill Lv.6", "Skill Lv.7", "Skill Lv.8", "Skill Lv.9", "Skill Lv.10", "Skill Lv.11", "Skill Lv.12", "Skill Lv.13", "Skill Lv.14", "Skill Lv.15", "Skill Lv.16", "Skill Lv.17"]

special_effects = [
    "心眼", "脆弱", "额外回合", "净化减益", "禁锢", "灾厄","特殊状态", "影分身", "混乱", 
    "弱点强击破", "退避", "充能", "贯通暴击", "斗志", "持续回复DP", "击破保护",
    "强化领域", "上升增益技能强化", "减益效果强化", "无敌", "掩护", "嘲讽", "抗性清除", "抗性下降", 
    "眩晕","清除病毒状态","攻击上升且减益效果强化","回复技能强化","永恒誓言","对HP百分比攻击"
]
def skill_effect_text(skill):

    text = ""
    text += output_string(skill.turn_num) + output_string(skill.duration) + output_string(skill.target)
    text += output_string(skill.effect_type) + '\n'
    
    # 如果 skill.effect_type 是 special_effects 中字符串的父串
    if is_parentstring(skill.effect_type, special_effects):
        if skill.value:
            text += 状态.status_info.status[skill.effect_type].description + "：" + skill.value
        else:
            text += 状态.status_info.status[skill.effect_type].description
    else:
        text += output_string(skill.value)

    if skill.effect_type in ["连击数上升（大）", "连击数上升（小）"]:
        text += "，" + 状态.status_info.status[skill.effect_type].description

    return text

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

    # attack_combos = {}
    # heal_combos = {}
    combos = {}
    # 创建自定义样式
    style_tc = ttk.Style()
    # 定义自定义样式
    style_tc.configure(
        "Custom.TCombobox",  # 样式名格式：自定义名.控件类型
        background="#f0f0f0",  # 背景色
        fieldbackground="#f0f0f0"  # 输入框背景色
    )

    # 主动技能
    active_skill_frame = ttk.LabelFrame(parent_frame, text="主动技能")
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

        lv1_attack_skill_strength_flag = False
        lv_combo_name = ""
        lv_combo_text = ""
        lv_combo_lab = None
        # 技能效果列表
        for j, skill in enumerate(active_skill.effects):
            # 属性倍率
            if skill.attribute_multiplier:
                attribute_multiplier = "、".join(
                    [f"{key}×{value}" for key, value in skill.attribute_multiplier.items()]
                )

            # 技能效果 frame
            effect_frame = ttk.Frame(row_frame)
            effect_frame.grid(row=j+1, column=0, columnspan=4, pady=(0,5), sticky="nsew")
            effect_frame.grid_rowconfigure(0, weight=1)  # 确保行填充
            # 为 effect_frame 设置列权重 1:6
            effect_frame.grid_columnconfigure(0, weight=1, minsize=100)  # Canvas 列
            effect_frame.grid_columnconfigure(1, weight=6, minsize=600)  # 右侧信息列，权重更大以填充更多空间

            # 检查是否是技能效果的实例
            if isinstance(skill, SkillEffect):
                # 创建技能效果图标 canvas
                effect_photo = get_photo(状态.status_info.status[skill.effect_type].path, (60, 60))
                effect_canvas = create_canvas_with_image(effect_frame, 
                    effect_photo, 60, 60, 0, 0, 0, 0)

                text = skill_effect_text(skill)

                if skill.attribute_multiplier:
                    text += '，属性倍率：' + attribute_multiplier  + '\n'
                if skill.attribute_difference:
                    text += '技能属性差值：' + skill.attribute_difference
                    if skill.target in ['单体','全体'] and skill.effect_type not in special_effects:
                        text += f"（{skill.attribute_difference}+敌方属性）"

            # 否则就是攻击技能
            else:
                weapon_attribute = skill.weapon_attribute
                # 判断元素属性
                if skill.element_attribute:
                    attack_img_path = 属性.attributes_info.attributes[skill.element_attribute+weapon_attribute].path
                else:
                    attack_img_path = 属性.attributes_info.attributes[weapon_attribute].path
                # 创建攻击技能图标 canvas
                attack_photo = get_photo(attack_img_path, (60, 60))
                attack_canvas = create_canvas_with_image(effect_frame, 
                    attack_photo, 60, 60, 0, 0, 0, 0)

                text = skill.hit_num + '-hit' + skill.target + '攻击'
                if skill.hit_damage:
                    hit_damage = get_hit_damage_str(skill.hit_damage)
                    text += "，hit伤害分布：" + f"（{hit_damage}）"
                text += '\n'

                if skill.biased:
                    text += "技能偏向：" + skill.biased + '\n'

                if skill.strength:
                    text += "技能强度：" + skill.strength 
                if skill.attribute_multiplier:
                    text += '，属性倍率：' + attribute_multiplier + '\n'
                    
                if skill.attribute_difference:
                    text += '技能属性差值：' + skill.attribute_difference + f"（{skill.attribute_difference}+敌方属性），"
                if skill.destructive_multiplier:
                    text += "破坏倍率：" + skill.destructive_multiplier

            desc_lab = ttk.Label(effect_frame, text=text, justify="left", font=("Monospace", 10, "bold"))
            desc_lab.grid(row=0, column=1, sticky="nsw", padx=5, pady=0)
            if "技能强度" in text and "属性倍率" in text:
                lv_combo_lab = desc_lab
                lv_combo_text = text
            else:
                if not lv_combo_text:
                    lv_combo_text = text
                    lv_combo_lab = desc_lab

        lv_combo_name = active_skill.name
        lv_combo_row = 1 + len(active_skill.effects)
        level_max = int(active_skill.level_max)

        lv_combo = ttk.Combobox(row_frame, 
            values=skill_options[:level_max], style="Custom.TCombobox")
        lv_combo.grid(row=lv_combo_row, column=0, sticky="nswe", padx=10, pady=(5,10))
        lv_combo.configure(state="readonly")
        lv_combo.set("Skill Lv.1")

        if "技能强度" in lv_combo_text:
            combos[active_skill.name+"_attack"] = lv_combo
            lv_combo.bind(
                "<<ComboboxSelected>>", 
                partial(on_attack_combo_select, desc_lab=lv_combo_lab, lv1_skill_strength=lv_combo_text)
            )
        elif "回复DP" in lv_combo_text:
            combos[active_skill.name+"_heal"] = lv_combo
            lv_combo.bind(
                "<<ComboboxSelected>>", 
                partial(on_heal_combo_select, desc_lab=lv_combo_lab, lv1_skill_strength=lv_combo_text)
            )
        elif "上升" in lv_combo_text:
            combos[active_skill.name+"_buff"] = lv_combo
            lv_combo.bind(
                "<<ComboboxSelected>>", 
                partial(on_buff_combo_select, desc_lab=lv_combo_lab, lv1_skill_strength=lv_combo_text)
            )
        elif "下降" in lv_combo_text:
            combos[active_skill.name+"_buff"] = lv_combo
            lv_combo.bind(
                "<<ComboboxSelected>>", 
                partial(on_debuff_combo_select, desc_lab=lv_combo_lab, lv1_skill_strength=lv_combo_text)
            )
        elif "心眼" in lv_combo_text:
            combos[active_skill.name+"_buff"] = lv_combo
            lv_combo.bind(
                "<<ComboboxSelected>>", 
                partial(on_mindeye_combo_select, desc_lab=lv_combo_lab, lv1_skill_strength=lv_combo_text)
            )        

        

# 被动技能
def creat_passive_skill_frame(parent_frame, style):
    passive_skill_frame = ttk.LabelFrame(parent_frame, text="天赋/被动技能")
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
        effect_photo = get_photo(状态.status_info.status[passive_skill.effect_type].path, (60, 60))
        effect_canvas = create_canvas_with_image(effect_frame, 
            effect_photo, 60, 60, 0, 0, 0, 0)

        text = skill_effect_text(passive_skill)

        effect_lab = ttk.Label(effect_frame, text=text, justify="left", font=("Monospace", 10, "bold"))
        effect_lab.grid(row=0, column=1, sticky="nsw", padx=5, pady=5)

def show_style(scrollbar_frame_obj, style):

    # 清除之前的组件
    scrollbar_frame_obj.destroy_components()

    # 职业
    career = 职业.careers_info.careers[style.career]
    career_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text=style.career)
    career_frame.grid(row=0, column=0, columnspan=4, padx=10, pady=5, sticky="nsew")
    career_frame.grid_rowconfigure(0, weight=1)
    career_photo = get_photo(career.path, (200, 40))
    career_canvas = create_canvas_with_image(career_frame, 
        career_photo, 240, 40, 20, 0, 0, 0)

    # 主动技能
    creat_active_skill_frame(scrollbar_frame_obj.scrollable_frame, style)

    # 被动技能
    creat_passive_skill_frame(scrollbar_frame_obj.scrollable_frame, style)

    if style.growth_ability:

        # 宝珠强化
        growth_ability_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text="强化")
        growth_ability_frame.grid(row=3, column=0, columnspan=4, padx=10, pady=5, sticky="nsew")
        growth_ability_frame.grid_rowconfigure(0, weight=1)
        growth_ability_frame.grid_columnconfigure(0, weight=1, minsize=100)  # 图片列
        growth_ability_frame.grid_columnconfigure(1, weight=6, minsize=600)  # 描述列

        # 判断元素属性
        if style.element_attribute:
            if len(style.element_attribute) == 1:
                hoju_img_path = 强化素材.strengthen_materials_win.strengthen_materials_dir[
                    f"宝珠（{style.element_attribute}属性）"]['path']
            else:
                hoju_img_path0 = 强化素材.strengthen_materials_win.strengthen_materials_dir[
                    f"宝珠（{style.element_attribute[0]}属性）"]['path']
                hoju_img_path1 = 强化素材.strengthen_materials_win.strengthen_materials_dir[
                    f"宝珠（{style.element_attribute[1]}属性）"]['path']
        else:
            hoju_img_path = 强化素材.strengthen_materials_win.strengthen_materials_dir[
                f"宝珠（{style.weapon_attribute}属性）"]['path']

        if not style.element_attribute or len(style.element_attribute) == 1:
            hoju_photo = get_photo(hoju_img_path, (66, 66))
            hoju_canvas = create_canvas_with_image(growth_ability_frame, 
                hoju_photo, 66, 66, 0, 0, 0, 0, padx=15)
            text = style.growth_ability.description
            growth_ability_lab = ttk.Label(growth_ability_frame, text=text, 
                justify="left", font=("Monospace", 10, "bold"))
            growth_ability_lab.grid(row=0, column=1, sticky="nsw", padx=15, pady=5)
        else:
            growth_ability_frame.grid_columnconfigure(1, weight=1, minsize=100)  # 图片列
            growth_ability_frame.grid_columnconfigure(2, weight=5, minsize=500)  # 描述列

            hoju_photo0 = get_photo(hoju_img_path0, (66, 66))
            hoju_canvas0 = create_canvas_with_image(growth_ability_frame, 
                hoju_photo0, 66, 66, 0, 0, 0, 0, padx=15)
            hoju_photo1 = get_photo(hoju_img_path1, (66, 66))
            hoju_canvas1 = create_canvas_with_image(growth_ability_frame, 
                hoju_photo1, 66, 66, 0, 0, 0, 1, padx=15)

            text = style.growth_ability.description
            growth_ability_lab = ttk.Label(growth_ability_frame, text=text, 
                justify="left", font=("Monospace", 10, "bold"))
            growth_ability_lab.grid(row=0, column=2, sticky="nsw", padx=15, pady=5)

        growth_status_row = 4
    else:
        growth_status_row = 3

    # 成长状态
    growth_status_frame = ttk.LabelFrame(scrollbar_frame_obj.scrollable_frame, text="成长状态")
    growth_status_frame.grid(row=growth_status_row, column=0, 
        columnspan=4, padx=10, pady=(5,10), sticky="nsew")
    growth_status_frame.grid_rowconfigure(0, weight=1)
    growth_status_frame.grid_columnconfigure(0, weight=1)
    growth_status_frame.grid_columnconfigure(1, weight=1)


    text = f"DP {style.status_growth['DP']}\n"
    text += "力量" + f"{style.status_growth['力量']}\n".rjust(10)
    text += "体力" + f"{style.status_growth['体力']}\n".rjust(10)
    text += "智慧" + f"{style.status_growth['智慧']}".rjust(9)
    growth_status_lab = ttk.Label(growth_status_frame, text=text, 
        justify="right", font=("Monospace", 10, "bold"))
    growth_status_lab.grid(row=0, column=0, sticky="sw", padx=20, pady=5)

    text =  "灵巧" + f"{style.status_growth['灵巧']}\n".rjust(10)
    text += "精神" + f"{style.status_growth['精神']}\n".rjust(10)
    text += "运气" + f"{style.status_growth['运气']}".rjust(9)

    growth_status_lab1 = ttk.Label(growth_status_frame, text=text, 
        justify="right", font=("Monospace", 10, "bold"))
    growth_status_lab1.grid(row=0, column=1, sticky="sw", padx=20, pady=5)

    scrollbar_frame_obj.update_canvas()

# 获取别名
def get_style_win_name(style):  
    if style.nicknames:
        style_win_name = style.name + f"（{style.nicknames[0]}）"
    else:
        style_win_name = style.name
    style_win_name += "-" + style.rarity

    return style_win_name


# 已打开的风格窗口字典，键：风格名，值：窗口句柄
open_style_wins = {}
# 关闭窗口时，清除风格名列表中对应的风格名，并销毁窗口
def style_win_closing(parent_frame):

    open_style_win = parent_frame.title()
    while open_style_win in open_style_wins:
        del open_style_wins[open_style_win]

    parent_frame.destroy()  # 销毁窗口

# 清除所有打开的窗口
# 遍历时不能修改字典元素，遍历条件应改为列表
def clean_up_open_style_wins():
    for open_style_win in list(open_style_wins.keys()):
        style_win_frame = open_style_wins[open_style_win]
        del open_style_wins[open_style_win]
        style_win_frame.destroy()  # 销毁窗口


def creat_style_skill_win(event, parent_frame, team, style):

    # 初始化资源文件
    load_resources()

    open_style_win = get_style_win_name(style)
    # 重复打开时，窗口置顶并直接返回
    if open_style_win in open_style_wins:
        # 判断窗口是否存在
        if open_style_wins[open_style_win].winfo_exists():
            set_window_top(open_style_wins[open_style_win])
            return "break"
        del open_style_wins[open_style_win]

    style_win_frame = creat_Toplevel(open_style_win, 812, 880, 440, 50) #780
    set_window_icon(style_win_frame, team.logo_path)
    set_window_expand(style_win_frame, rowspan=1, columnspan=2)
    scrollbar_frame_obj = ScrollbarFrameWin(style_win_frame, columnspan=2)

    open_style_wins[open_style_win] = style_win_frame

    # 绑定鼠标点击事件到父窗口，点击置顶
    style_win_frame.bind("<Button-1>", lambda event: set_window_top(style_win_frame))
    # 窗口关闭时清理
    style_win_frame.protocol("WM_DELETE_WINDOW", lambda: style_win_closing(style_win_frame))

    show_style(scrollbar_frame_obj, style)

    return "break"  # 阻止事件冒泡

# 创建右键菜单
def creat_style_right_menu(event, parent_frame, team, style):
    
    right_click_menu = ttk.Menu(parent_frame, tearoff=0)

    right_click_menu.add_command(label="动画", 
        command=lambda: show_style_animation(parent_frame, team, style))

    right_click_menu.add_command(label="静态图", 
        command=lambda: show_style_artwork(parent_frame, team, style))

    right_click_menu.add_command(label="静态图3D", 
        command=lambda: show_style_artwork_3d(parent_frame, team, style))

    right_click_menu.post(event.x_root, event.y_root)


# 显示风格动画
def show_style_animation(parent_frame, team, style):

    animation_path = style.path.replace("_Thumbnail", "")
    animation_path = animation_path[:-4] + "webm"

    # 判断有没有动画
    if os.path.exists(animation_path):

        open_style_win = get_style_win_name(style) + "-animation"
        # 重复打开时，窗口置顶并直接返回
        if open_style_win in open_style_wins:
            # 判断窗口是否存在
            if open_style_wins[open_style_win].winfo_exists():
                set_window_top(open_style_wins[open_style_win])
                return "break"
            del open_style_wins[open_style_win]

        style_animation_win_frame = creat_Toplevel(open_style_win, 1366, 768)
        set_window_icon(style_animation_win_frame, team.logo_path)
        open_style_wins[open_style_win] = style_animation_win_frame

        player = VideoPlayerWithScrollbar(style_animation_win_frame, 1366, 768, animation_path)

        # 窗口关闭时清理
        style_animation_win_frame.protocol("WM_DELETE_WINDOW", 
            lambda: (player.destroy(), style_win_closing(style_animation_win_frame)))
    else:
        return

# 显示风格静态图
def show_style_artwork(parent_frame, team, style):

    artwork_path = style.path.replace("_Thumbnail", "")

    if os.path.exists(artwork_path):
        open_style_win = get_style_win_name(style) + "-artwork"
        # 重复打开时，窗口置顶并直接返回
        if open_style_win in open_style_wins:
            # 判断窗口是否存在
            if open_style_wins[open_style_win].winfo_exists():
                set_window_top(open_style_wins[open_style_win])
                return "break"
            del open_style_wins[open_style_win]

        style_artwork_win_frame = creat_Toplevel(open_style_win, 1366, 769)
        set_window_icon(style_artwork_win_frame, team.logo_path)
        open_style_wins[open_style_win] = style_artwork_win_frame

        displayer = ImageViewerWithScrollbar(style_artwork_win_frame, 1366, 769, artwork_path)

        # 窗口关闭时清理
        style_artwork_win_frame.protocol("WM_DELETE_WINDOW", 
            lambda: (displayer.destroy(), style_win_closing(style_artwork_win_frame)))

    else:
        return


# 显示风格3d静态图
def show_style_artwork_3d(parent_frame, team, style):

    artwork_3d_path = style.path.replace("_Thumbnail", "_3d")
    artwork_3d_path = artwork_3d_path[:-4] + "png"

    if os.path.exists(artwork_3d_path):

        open_style_win = get_style_win_name(style) + "-artwork-3d"
        # 重复打开时，窗口置顶并直接返回
        if open_style_win in open_style_wins:
            # 判断窗口是否存在
            if open_style_wins[open_style_win].winfo_exists():
                set_window_top(open_style_wins[open_style_win])
                return "break"
            del open_style_wins[open_style_win]

        style_artwork_3d_win_frame = creat_Toplevel(open_style_win)
        set_window_icon(style_artwork_3d_win_frame, team.logo_path)
        open_style_wins[open_style_win] = style_artwork_3d_win_frame

        displayer = ArtworkDisplayerHeight(style_artwork_3d_win_frame, artwork_3d_path, 710, 0)

        # 窗口关闭时清理
        style_artwork_3d_win_frame.protocol("WM_DELETE_WINDOW", 
            lambda: (style_win_closing(style_artwork_3d_win_frame)))

    else:
        return


