import sys
import os
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from canvas_events import ArtworkDisplayerHeight
from window import set_window_expand, set_window_icon, creat_window, set_window_top, set_global_bg
from window import load_menu_icon, get_ico_path_by_name
from scrollbar_frame_win import ScrollbarFrameWin
from tools import delete_old_file_and_subdirs, is_admin

sys.path.append(os.path.abspath("./持有物"))
from 持有物.饰品.jewelrys_win import show_jewelrys_type
from 持有物.奖杯勋章.trophy_medals_win import show_trophy_medals
from 持有物.道具.props_win import show_props
from 持有物.主线道具.main_props_win import show_main_props
from 持有物.饰品材料.jewelry_materials_win import show_jewelry_materials
from 持有物.成长素材.growth_materials_win import show_growth_materials
from 持有物.活动奖章.medals_win import show_medals
from 持有物.强化素材.strengthen_materials_win import show_strengthen_materials
from 持有物.入场券.tickets_win import show_tickets
from 持有物.货币.currencys_win import show_currencys
from 持有物.增幅器.amplifiers_win import show_amplifiers
from 持有物.扭蛋材料.capsuletoys_win import show_capsuletoys
from 持有物.芯片.chips_win import show_chips
from 持有物.碎片.fragments_win import show_fragments

sys.path.append(os.path.abspath("./战斗系统"))
from 战斗系统.基础.jc_win import creat_jc_win
from 战斗系统.OD.od_win import creat_od_win
from 战斗系统.乘区.cq_win import creat_cq_win
from 战斗系统.职业.careers_win import show_career
from 战斗系统.武器.weapons_win import show_weapon
from 战斗系统.属性.attributes_win import show_attribute
from 战斗系统.状态.status_win import show_statu

sys.path.append(os.path.abspath("./敌人"))
from 敌人.主线.zx_win import show_zx_enemys
from 敌人.时钟塔.szt_win import show_szt_enemys
from 敌人.光球BOSS.gqboss_win import show_gqboss_enemys
from 敌人.时之修炼场.szxlc_win import show_szxlc_enemys
from 敌人.棱镜战.ljz_win import show_ljz_enemys
from 敌人.宝石棱镜战.bsljz_win import show_bsljz_enemys
from 敌人.异时层.ysc_win import show_ysc_enemys
from 敌人.高分挑战.gftz_win import show_gftz_enemys
from 敌人.恒星战.hxz_win import show_hxz_enemys
from 敌人.遭遇战.zyz_win import show_zyz_enemys

sys.path.append(os.path.abspath("./搜索"))
from 搜索.search_win import creat_search_win

sys.path.append(os.path.abspath("./角色"))
from 角色.team_win import creat_team_win

sys.path.append(os.path.abspath("./更新"))
from 更新.http_update_processing import http_update_data

sys.path.append(os.path.abspath("./音乐"))
from 音乐.music_win import creat_music_win

sys.path.append(os.path.abspath("./工具"))
from 工具.GetEntriesGUILocal.seed_tools.Load import load_seed_tools
from 工具.GetEntriesGUILocal.get_entries_win import creat_ct_win
from 工具.DamageScoreCal.damage_score_cal_win import creat_dsc_win
from 工具.DamageScoreCal.damage_score_cal_win_v2 import creat_dsc_win_v2
from 工具.HBRbrochure.HBRbrochure import get_hbr_brochure
from 工具.HBR伤害模拟.Load import load_hbr_damage_simulation
from 工具.hbr_tool.Load import load_hbr_tool
from 工具.hbr_tool_old_damage_calculator.Load import load_hbr_tool_old_damage_calculator
from 工具.hbr_axletool.Load import load_hbr_axletool
from 工具.wiki_hbr_hd.Load import load_wiki_hbr_hd
from 工具.词条计算器.Load import load_entry_calculator
from 工具.o_hbr_quest.Load import load_o_hbr_quest
from 工具.hbr_quest.Load import load_hbr_quest
from 工具.game8_hbr.Load import load_game8_hbr
from 工具.gamekee_hbr.Load import load_gamekee_hbr
from 工具.入队培训手册.Load import load_game_bilibili_com

sys.path.append(os.path.abspath("./关于"))
from 关于.about_win import creat_about_win

sys.path.append(os.path.abspath("./日志"))
from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

# 占位函数
def update_output(text):
    print(text)

# 创建单个菜单项，并绑定命令
def create_menu_item(menu, label, image, command, *args):
    if image:
        menu.add_command(label=label, image=image, compound="left", command=lambda: command(*args))
    else:
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
        "31A", "31B", "31C", "30G", "31D", "31E", "31F", "31X", "Angel Beats!", "司令部"
    ]
    for team_name in team_names:
        ico_path = get_ico_path_by_name(team_name)
        icon = load_menu_icon(ico_path, team_name)
        create_menu_item(team_menu, team_name, icon,
            creat_team_win, parent_frame, team_name)
    menu_bar.add_cascade(label="👤角色", menu=team_menu)

    # 物品材料菜单
    item_menu = ttk.Menu(menu_bar, tearoff=0)
    item_names = [
        "活动道具"
    ]
    for item_name in item_names:
        create_menu_item(item_menu, item_name, None, update_output, item_name)

    # 定义菜单项的名称和对应的回调函数
    menu_item_calls = [
        ("主线道具", show_main_props),
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
        ico_path = get_ico_path_by_name(item_call_name)
        icon = load_menu_icon(ico_path, item_call_name)
        create_menu_item(item_menu, item_call_name, icon, callback, scrollbar_frame_obj)
    menu_bar.add_cascade(label="📜持有物", menu=item_menu)

    # 敌人菜单
    enemy_menu = ttk.Menu(menu_bar, tearoff=0)
    enemy_names = [
        "活动棱镜战","废域"
    ]
    for enemy_name in enemy_names:
        create_menu_item(enemy_menu, enemy_name, None, update_output, enemy_name)

    menu_enemy_calls = [
        ("时钟塔", show_szt_enemys),
        ("主线", show_zx_enemys),
        ("光球BOSS", show_gqboss_enemys),
        ("时之修炼场", show_szxlc_enemys),
        ("棱镜战", show_ljz_enemys),
        ("宝石棱镜战", show_bsljz_enemys),
        ("恒星扫荡战线", show_hxz_enemys),
        ("高分挑战", show_gftz_enemys),
        ("异时层", show_ysc_enemys),
        ("遭遇战", show_zyz_enemys),
    ]
    # 循环创建菜单项
    for enemy_call_name, callback in menu_enemy_calls:
        ico_path = get_ico_path_by_name(enemy_call_name)
        icon = load_menu_icon(ico_path, enemy_call_name)
        create_menu_item(enemy_menu, enemy_call_name, icon, callback, scrollbar_frame_obj)
    # menu_bar.add_cascade(label="🪬敌人", menu=enemy_menu)
    menu_bar.add_cascade(label="👾敌人", menu=enemy_menu)
    
    # 战斗系统菜单
    battle_menu = ttk.Menu(menu_bar, tearoff=0)
    # 定义菜单项的名称和对应的回调函数
    menu_battle_calls = [
        ("基础", creat_jc_win),
        ("Hit", creat_od_win),
        ("乘区", creat_cq_win),
        ("职业", show_career),
        ("武器", show_weapon),
        ("属性", show_attribute),
        ("效果、状态", show_statu)  
    ]
    # 循环创建菜单项
    for battle_call_name, callback in menu_battle_calls:
        if battle_call_name in ['基础','Hit','乘区']:
            icon = load_menu_icon("./战斗系统/help.ico", battle_call_name)
            create_menu_item(battle_menu, battle_call_name, icon, callback, parent_frame)
        else:
            ico_path = get_ico_path_by_name(battle_call_name)
            icon = load_menu_icon(ico_path, battle_call_name)
            create_menu_item(battle_menu, battle_call_name, icon, callback, scrollbar_frame_obj)
    menu_bar.add_cascade(label="⚔战斗系统", menu=battle_menu)

    # 搜索菜单
    menu_bar.add_command(label="🔍搜索", 
        command=lambda: creat_search_win(parent_frame, scrollbar_frame_obj))

    # 音乐菜单
    menu_bar.add_command(label="🎧音乐", 
        command=lambda: creat_music_win())

    # 工具菜单
    tool_menu = ttk.Menu(menu_bar, tearoff=0)
    menu_tool_calls = [
        ("seed tools", load_seed_tools),
        ("词条获取", creat_ct_win),
        ("伤害分计算", creat_dsc_win),
        ("伤害分计算V2", creat_dsc_win_v2),
        ("风格图鉴获取", get_hbr_brochure),
        ("伤害模拟", load_hbr_damage_simulation),
        ("hbr-tool", load_hbr_tool),
        ("hbr-tool伤害计算", load_hbr_tool_old_damage_calculator),
        ("hbr-axletool", load_hbr_axletool),
        ("wiki.hbr-hd", load_wiki_hbr_hd),
        ("词条计算器（在线）", load_entry_calculator),

        ("o.hbr.quest（v5.10）", load_o_hbr_quest),
        ("hbr.quest", load_hbr_quest),
        ("入队培训手册", load_game_bilibili_com),
        ("gamekee", load_gamekee_hbr),
        ("game8", load_game8_hbr),
    ]
    # 循环创建菜单项
    for tool_call_name, callback in menu_tool_calls:
        icon = load_menu_icon("./工具/w1.ico", tool_call_name)
        create_menu_item(tool_menu, tool_call_name, icon, callback)
    menu_bar.add_cascade(label="🛠️工具", menu=tool_menu)


    # 更新数据菜单
    menu_bar.add_command(label="📲更新", 
        command=lambda: http_update_data())

    # 关于菜单
    menu_bar.add_command(label="🏷️关于", 
        command=lambda: creat_about_win(parent_frame))

    parent_frame.config(menu=menu_bar)

if __name__ == "__main__":

    if is_admin():
        root_win_name = "HBRDatabase - 以管理员身份运行"
    else:
        root_win_name = "HBRDatabase"

    delete_old_file_and_subdirs()

    # 创建主窗口
    root = creat_window(root_win_name, 1160, 717, 440, 50)#1160
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
