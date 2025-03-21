import sys
import os
import tkinter as tk
from PIL import Image, ImageTk
import json

from canvas_events import ArtworkDisplayerHeight2
from window import set_window_expand, set_window_icon, creat_window, set_window_top, set_bg_opacity
from scrollbar_frame_win import ScrollbarFrameWin
from tools import load_json

sys.path.append(os.path.abspath("./持有物"))
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
from 武器.weapons_win import show_weapon
from 属性.attributes_win import show_attribute
from 状态.status_win import show_statu

sys.path.append(os.path.abspath("./敌人"))
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
    
    menu_bar = tk.Menu(parent_frame)

    # 角色菜单 菜单不可分离
    team_menu = tk.Menu(menu_bar, tearoff=0)
    team_commands = [
        "31A", "31B", "31C", "30G", "31D", "31E", "31F", "31X", "Angel Beats!"
    ]
    for team_name in team_commands:
        create_menu_item(team_menu, team_name, 
            creat_team_win, parent_frame, team_name)
    menu_bar.add_cascade(label="👤角色", menu=team_menu)

    # 物品材料菜单
    items_menu = tk.Menu(menu_bar, tearoff=0)
    item_commands = [
        "主线道具", "活动道具",
        "饰品"
    ]
    for item in item_commands:
        create_menu_item(items_menu, item, update_output, item)

    # 定义菜单项的名称和对应的回调函数
    menu_items = [
        ("道具", show_props),
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
    for item_name, callback in menu_items:
        create_menu_item(items_menu, item_name, callback, scrollbar_frame_obj)
    menu_bar.add_cascade(label="📜持有物", menu=items_menu)

    # 敌人菜单
    enemies_menu = tk.Menu(menu_bar, tearoff=0)
    enemies_commands = [
        "主线", "活动棱镜战", "时钟塔", "废域"
    ]
    for enemy in enemies_commands:
        create_menu_item(enemies_menu, enemy, update_output, enemy)

    create_menu_item(enemies_menu, "光球BOSS", show_gqboss_enemys, scrollbar_frame_obj)
    create_menu_item(enemies_menu, "时之修炼场", show_szxlc_enemys, scrollbar_frame_obj)
    create_menu_item(enemies_menu, "棱镜战", show_ljz_enemys, scrollbar_frame_obj)
    create_menu_item(enemies_menu, "宝石棱镜战", show_bsljz_enemys, scrollbar_frame_obj)
    create_menu_item(enemies_menu, "恒星扫荡战线", show_hxz_enemys, scrollbar_frame_obj)
    create_menu_item(enemies_menu, "高分挑战", show_gftz_enemys, scrollbar_frame_obj)
    create_menu_item(enemies_menu, "异时层", show_ysc_enemys, scrollbar_frame_obj)
    menu_bar.add_cascade(label="🪬敌人", menu=enemies_menu)
    

    # 战斗系统菜单
    battle_info_menu = tk.Menu(menu_bar, tearoff=0)
    # 定义菜单项的名称和对应的回调函数
    menu_battle_infos = [
        ("基础", creat_jc_win),
        ("乘区", creat_cq_win),
        ("武器", show_weapon),
        ("属性", show_attribute),
        ("效果、状态", show_statu)  
    ]
    # 循环创建菜单项
    for battle_info_name, callback in menu_battle_infos:
        if battle_info_name in ['基础','乘区']:
            create_menu_item(battle_info_menu, battle_info_name, callback, parent_frame)
        else:
            create_menu_item(battle_info_menu, battle_info_name, callback, scrollbar_frame_obj)
    menu_bar.add_cascade(label="⚔战斗系统", menu=battle_info_menu)

    # 搜索菜单
    menu_bar.add_command(label="🔍搜索", 
        command=lambda: creat_search_win(parent_frame, scrollbar_frame_obj))

    # 更新数据菜单
    menu_bar.add_command(label="📲更新", 
        command=lambda: update_data())

    # 关于菜单
    menu_bar.add_command(label="🏷️关于", 
        command=lambda: creat_about_win(parent_frame))

    parent_frame.config(menu=menu_bar)


bg = []
if __name__ == "__main__":

    # 创建主窗口
    root = creat_window("HBRDatabase", 1160, 725, 440, 50)#1160
    set_window_icon(root, "./favicon.ico")
    set_window_expand(root, rowspan=1, columnspan=6)

    # 绑定鼠标点击事件到父窗口，点击置顶
    root.bind("<Button-1>", lambda event: set_window_top(root))

    scrollbar_frame_obj = ScrollbarFrameWin(root, columnspan=6)
    # 创建菜单
    create_menu(root, scrollbar_frame_obj)

    # # 显示猫猫头
    # displayer = ArtworkDisplayerHeight2(scrollbar_frame_obj.scrollable_frame, 
    #     "./角色/KamiSama.webp", 400)

    bg_photo = set_bg_opacity(root, 1253, 705, "vbg_hbr.png", "70%")
    bg.append([bg_photo])

    root.mainloop()
