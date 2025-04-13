import sys
import os
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import json
import tkinter

from canvas_events import ArtworkDisplayerHeight2, ImageViewerWithScrollbar, ArtworkDisplayerHeight
from window import set_window_expand, set_window_icon, creat_window, set_window_top, set_bg_opacity, set_global_bg
from scrollbar_frame_win import ScrollbarFrameWin
from tools import load_json

sys.path.append(os.path.abspath("./持有物"))
from 饰品.jewelrys_win import show_jewelrys_type
from 奖杯勋章.trophy_medals_win import show_trophy_medals
from 道具.props_win import show_props
from 饰品材料.jewelry_materials_win import show_jewelry_materials
from 成长素材.growth_materials_win import show_growth_materials
from 活动奖章.medals_win import show_medals
from 强化素材.strengthen_materials_win import show_strengthen_materials
from 入场券.tickets_win import show_tickets
from 货币.currencys_win import show_currencys
from 增幅器.amplifiers_win import show_amplifiers
from 扭蛋材料.capsuletoys_win import show_capsuletoys
from 芯片.chips_win import show_chips
from 碎片.fragments_win import show_fragments

sys.path.append(os.path.abspath("./战斗系统"))
from 基础.jc_win import creat_jc_win
from 乘区.cq_win import creat_cq_win
from 职业.careers_win import show_career
from 武器.weapons_win import show_weapon
from 属性.attributes_win import show_attribute
from 状态.status_win import show_statu

sys.path.append(os.path.abspath("./敌人"))
from 主线.zx_win import show_zx_enemys
from 光球BOSS.gqboss_win import show_gqboss_enemys
from 时之修炼场.szxlc_win import show_szxlc_enemys
from 棱镜战.ljz_win import show_ljz_enemys
from 宝石棱镜战.bsljz_win import show_bsljz_enemys
from 异时层.ysc_win import show_ysc_enemys
from 高分挑战.gftz_win import show_gftz_enemys
from 恒星战.hxz_win import show_hxz_enemys

sys.path.append(os.path.abspath("./搜索"))
from search_win import creat_search_win

sys.path.append(os.path.abspath("./角色"))
from team_win import creat_team_win
from team_info import get_all_team_obj

sys.path.append(os.path.abspath("./更新"))
from update_processing import update_data
from http_update_processing import http_update_data

sys.path.append(os.path.abspath("./音乐"))
from music_win import creat_music_win

sys.path.append(os.path.abspath("./关于"))
from about_win import creat_about_win

# 占位函数
def update_output(text):
    print(text)

# 创建单个菜单项，并绑定命令
def create_menu_item(menu, label, command, *args):
    menu.add_command(label=label, command=lambda: command(*args))

# 创建菜单栏
def create_menu(parent_frame, scrollbar_frame_obj):
    
    # 创建自定义菜单样式
    style = ttk.Style()
    style.configure(
        "Custom.TMenubutton",  # 控制菜单按钮样式
        background="#f0f0f0"  # 背景色
    )
    menu_bar = ttk.Menu(parent_frame)


    # 角色菜单 菜单不可分离
    team_menu = ttk.Menu(menu_bar, tearoff=0)
    team_names = [
        "31A", "31B", "31C", "30G", "31D", "31E", "31F", "31X", "Angel Beats!"
    ]
    for team_name in team_names:
        create_menu_item(team_menu, team_name, 
            creat_team_win, parent_frame, team_name)
    menu_bar.add_cascade(label="👤角色", menu=team_menu)

    # 物品材料菜单
    item_menu = ttk.Menu(menu_bar, tearoff=0)
    item_names = [
        "主线道具", "活动道具"
    ]
    for item_name in item_names:
        create_menu_item(item_menu, item_name, update_output, item_name)

    # 定义菜单项的名称和对应的回调函数
    menu_item_calls = [
        ("道具", show_props),
        ("饰品", show_jewelrys_type),
        ("饰品材料", show_jewelry_materials),
        ("活动奖章", show_medals),
        ("奖杯勋章", show_trophy_medals),
        ("成长素材", show_growth_materials),
        ("强化素材", show_strengthen_materials),
        ("增幅器", show_amplifiers),
        ("芯片", show_chips),
        ("入场券", show_tickets),
        ("扭蛋材料", show_capsuletoys),
        ("碎片", show_fragments),
        ("货币", show_currencys)  
    ]
    # 循环创建菜单项
    for item_call_name, callback in menu_item_calls:
        create_menu_item(item_menu, item_call_name, callback, scrollbar_frame_obj)
    menu_bar.add_cascade(label="📜持有物", menu=item_menu)

    # 敌人菜单
    enemy_menu = ttk.Menu(menu_bar, tearoff=0)
    enemy_names = [
        "活动棱镜战", "时钟塔", "废域"
    ]
    for enemy_name in enemy_names:
        create_menu_item(enemy_menu, enemy_name, update_output, enemy_name)

    menu_enemy_calls = [
        ("主线", show_zx_enemys),
        ("光球BOSS", show_gqboss_enemys),
        ("时之修炼场", show_szxlc_enemys),
        ("棱镜战", show_ljz_enemys),
        ("宝石棱镜战", show_bsljz_enemys),
        ("恒星扫荡战线", show_hxz_enemys),
        ("高分挑战", show_gftz_enemys),
        ("异时层", show_ysc_enemys),
    ]
    # 循环创建菜单项
    for enemy_call_name, callback in menu_enemy_calls:
        create_menu_item(enemy_menu, enemy_call_name, callback, scrollbar_frame_obj)
    menu_bar.add_cascade(label="🪬敌人", menu=enemy_menu)
    
    # 战斗系统菜单
    battle_menu = ttk.Menu(menu_bar, tearoff=0)
    # 定义菜单项的名称和对应的回调函数
    menu_battle_calls = [
        ("基础", creat_jc_win),
        ("乘区", creat_cq_win),
        ("职业", show_career),
        ("武器", show_weapon),
        ("属性", show_attribute),
        ("效果、状态", show_statu)  
    ]
    # 循环创建菜单项
    for battle_call_name, callback in menu_battle_calls:
        if battle_call_name in ['基础','乘区']:
            create_menu_item(battle_menu, battle_call_name, callback, parent_frame)
        else:
            create_menu_item(battle_menu, battle_call_name, callback, scrollbar_frame_obj)
    menu_bar.add_cascade(label="⚔战斗系统", menu=battle_menu)

    # 搜索菜单
    menu_bar.add_command(label="🔍搜索", 
        command=lambda: creat_search_win(parent_frame, scrollbar_frame_obj))

    # 音乐菜单
    menu_bar.add_command(label="🎧音乐", 
        command=lambda: creat_music_win())

    # 更新数据菜单
    menu_bar.add_command(label="📲更新", 
        command=lambda: http_update_data())

    # 关于菜单
    menu_bar.add_command(label="🏷️关于", 
        command=lambda: creat_about_win(parent_frame))

    parent_frame.config(menu=menu_bar)


bg = []
if __name__ == "__main__":

    # 创建主窗口
    root = creat_window("HBRDatabase", 1160, 717, 440, 50)#1160
    set_global_bg(root)
    set_window_icon(root, "./favicon.ico")
    set_window_expand(root, rowspan=1, columnspan=6)
    root.update()

    # 绑定鼠标点击事件到父窗口，点击置顶
    root.bind("<Button-1>", lambda event: set_window_top(root))

    scrollbar_frame_obj = ScrollbarFrameWin(root, columnspan=6)
    scrollbar_frame_obj.scrollable_frame.grid_rowconfigure(0, weight=1)
    # 创建菜单
    create_menu(root, scrollbar_frame_obj)

    ArtworkDisplayerHeight(scrollbar_frame_obj.scrollable_frame,
        "vbg_hbr.png", 717, 0, "70%")

    root.mainloop()
