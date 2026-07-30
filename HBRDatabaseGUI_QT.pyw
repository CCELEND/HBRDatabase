import sys
import os
import subprocess

sys.path.append(os.path.abspath("./持有物"))
sys.path.append(os.path.abspath("./战斗系统"))
sys.path.append(os.path.abspath("./敌人"))
sys.path.append(os.path.abspath("./搜索"))
sys.path.append(os.path.abspath("./角色"))
sys.path.append(os.path.abspath("./更新"))
sys.path.append(os.path.abspath("./音乐"))
sys.path.append(os.path.abspath("./工具"))
sys.path.append(os.path.abspath("./关于"))
sys.path.append(os.path.abspath("./日志"))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QMenu, QToolButton, QAction, QToolBar,
    QShortcut
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QKeySequence, QIcon

from canvas_events_qt import ResizableArtworkDisplayerHeight
from window_qt import (
    set_global_bg, creat_window, set_window_icon,
    load_menu_icon, get_ico_path_by_name
)
from scrollbar_frame_qt import ScrollbarFrameWin
from tools import delete_old_file_and_subdirs, is_admin

from 日志.error_queue_proc_qt import check_error_queue_qt
from 更新.check_proc_qt import check_for_updates

from 持有物.饰品.jewelrys_win_qt import show_jewelrys_type
from 持有物.奖杯勋章.trophy_medals_win_qt import show_trophy_medals
from 持有物.道具.props_win_qt import show_props
from 持有物.主线道具.main_props_win_qt import show_main_props
from 持有物.饰品材料.jewelry_materials_win_qt import show_jewelry_materials
from 持有物.成长素材.growth_materials_win_qt import show_growth_materials
from 持有物.活动奖章.medals_win_qt import show_medals
from 持有物.强化素材.strengthen_materials_win_qt import show_strengthen_materials
from 持有物.入场券.tickets_win_qt import show_tickets
from 持有物.货币.currencys_win_qt import show_currencys
from 持有物.增幅器.amplifiers_win_qt import show_amplifiers
from 持有物.扭蛋材料.capsuletoys_win_qt import show_capsuletoys
from 持有物.芯片.chips_win_qt import show_chips
from 持有物.碎片.fragments_win_qt import show_fragments

from 战斗系统.共鸣天赋.gmtf_win_qt import creat_gmtf_win
from 战斗系统.基础.jc_win_qt import creat_jc_win
from 战斗系统.OD.od_win_qt import creat_od_win
from 战斗系统.乘区.cq_win_qt import creat_cq_win
from 战斗系统.职业.careers_win_qt import show_career
from 战斗系统.武器.weapons_win_qt import show_weapon
from 战斗系统.属性.attributes_win_qt import show_attribute
from 战斗系统.状态.status_win_qt import show_statu

from 敌人.主线.zx_win_qt import show_zx_enemys
from 敌人.时钟塔.szt_win_qt import show_szt_enemys
from 敌人.光球BOSS.gqboss_win_qt import show_gqboss_enemys
from 敌人.时之修炼场.szxlc_win_qt import show_szxlc_enemys
from 敌人.棱镜战.ljz_win_qt import show_ljz_enemys
from 敌人.宝石棱镜战.bsljz_win_qt import show_bsljz_enemys
from 敌人.异时层.ysc_win_qt import show_ysc_enemys
from 敌人.高分挑战.gftz_win_qt import show_gftz_enemys
from 敌人.恒星战.hxz_win_qt import show_hxz_enemys
from 敌人.遭遇战.zyz_win_qt import show_zyz_enemys

from 搜索.search_win_qt import creat_search_win
from 角色.team_win_qt import creat_team_win
from 更新.http_update_processing_qt import http_update_data
from 音乐.music_win_qt import creat_music_win

from 工具.GetEntriesGUILocal.seed_tools.Load_qt import load_seed_tools
from 工具.GetEntriesGUILocal.get_entries_win_qt import creat_ct_win
from 工具.DamageScoreCal.damage_score_cal_win_qt import creat_dsc_win
from 工具.DamageScoreCal.damage_score_cal_win_v2_qt import creat_dsc_win_v2
from 工具.HBRbrochure.HBRbrochure import get_hbr_brochure
from 工具.HBR伤害模拟.Load import load_hbr_damage_simulation
from 工具.AFSGTools.Load import load_AFSGTools
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
from 工具.LineArt.LineArtGUI2_QT import load_LineArtGUI2_QT

from 关于.about_win_qt import creat_about_win

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


def update_output(text):
    print(text)


def bind_shortcuts(root: QMainWindow, scrollbar_frame_obj):
    # QShortcut(QKeySequence("Ctrl+S"), root,
    #           lambda: creat_search_win(root, scrollbar_frame_obj))
    QShortcut(QKeySequence("F1"), root,
              lambda: creat_search_win(root, scrollbar_frame_obj))
    QShortcut(QKeySequence("Ctrl+U"), root,
              lambda: http_update_data(root))
    QShortcut(QKeySequence("Ctrl+A"), root,
              lambda: creat_about_win(root))
    QShortcut(QKeySequence("Ctrl+M"), root,
              lambda: creat_music_win())
    QShortcut(QKeySequence("Ctrl+Q"), root,
              lambda: QApplication.quit())


def add_menu_action(menu: QMenu, label: str, icon: QIcon,
                    command: callable, accelerator: str = None, *args):
    action = QAction(icon, label, menu)
    if accelerator:
        action.setShortcut(accelerator)
    action.triggered.connect(lambda: command(*args))
    menu.addAction(action)


def add_top_menu_button(menu_bar: QToolBar, text: str, menu_title: str,
                        icon_path: str):
    """在菜单栏添加一个带图标和文字的顶层菜单按钮"""
    menu = QMenu(menu_title, menu_bar)
    btn = QToolButton(menu_bar)
    btn.setText(text)
    if icon_path:
        btn.setIcon(load_menu_icon(icon_path, text))
    btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    btn.setPopupMode(QToolButton.InstantPopup)
    btn.setMenu(menu)
    menu_bar.addWidget(btn)
    return menu, btn


def create_menu(root: QMainWindow, scrollbar_frame_obj: ScrollbarFrameWin):
    menu_bar = QToolBar(root)
    menu_bar.setMovable(False)
    menu_bar.setFloatable(False)
    menu_bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    menu_bar.setIconSize(QSize(22, 22))
    menu_bar.setStyleSheet("""
        QToolBar {
            background-color: #f8f8f8;
            border-bottom: 1px solid #d4d4d4;
            min-height: 36px;
            padding: 2px 6px;
            spacing: 4px;
        }
        QToolButton {
            padding: 4px 10px;
            border: none;
            color: #333333;
            background-color: transparent;
            border-radius: 4px;
            font-size: 16px;
            font-weight: bold;
        }
        QToolButton:hover {
            background-color: #e0e0e0;
        }
        QToolButton:pressed {
            background-color: #d0d0d0;
        }
        QToolButton::menu-indicator {
            image: none;
        }
    """)
    root.addToolBar(menu_bar)

    team_menu = add_top_menu_button(menu_bar, "👤角色", "👤角色", None)[0]
    team_names = [
        "31A", "31B", "31C", "30G", "31D", "31E", "31F", "31X",
        "Angel Beats!", "司令部", "persona5r"
    ]
    for team_name in team_names:
        ico_path = get_ico_path_by_name(team_name)
        icon = load_menu_icon(ico_path, team_name)
        add_menu_action(team_menu, team_name, icon,
                        creat_team_win, None, root, team_name)

    item_menu = add_top_menu_button(menu_bar, "📜持有物", "📜持有物", None)[0]
    item_names = ["活动道具"]
    for item_name in item_names:
        add_menu_action(item_menu, item_name, QIcon(), update_output, None, item_name)

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
    for item_call_name, callback in menu_item_calls:
        ico_path = get_ico_path_by_name(item_call_name)
        icon = load_menu_icon(ico_path, item_call_name)
        add_menu_action(item_menu, item_call_name, icon,
                        callback, None, scrollbar_frame_obj)

    enemy_menu = add_top_menu_button(menu_bar, "👾敌人", "👾敌人", None)[0]
    enemy_names = ["活动棱镜战", "废域"]
    for enemy_name in enemy_names:
        add_menu_action(enemy_menu, enemy_name, QIcon(), update_output, None, enemy_name)

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
    for enemy_call_name, callback in menu_enemy_calls:
        ico_path = get_ico_path_by_name(enemy_call_name)
        icon = load_menu_icon(ico_path, enemy_call_name)
        add_menu_action(enemy_menu, enemy_call_name, icon,
                        callback, None, scrollbar_frame_obj)

    battle_menu = add_top_menu_button(menu_bar, "⚔战斗系统", "⚔战斗系统", None)[0]
    menu_battle_calls = [
        ("共鸣天赋", creat_gmtf_win),
        ("基础", creat_jc_win),
        ("Hit", creat_od_win),
        ("乘区", creat_cq_win),
        ("职业", show_career),
        ("武器", show_weapon),
        ("属性", show_attribute),
        ("效果、状态", show_statu)
    ]
    for battle_call_name, callback in menu_battle_calls:
        if battle_call_name in ['共鸣天赋', '基础', 'Hit', '乘区']:
            icon = load_menu_icon("./战斗系统/help.ico", battle_call_name)
            add_menu_action(battle_menu, battle_call_name, icon,
                            callback, None, root)
        else:
            ico_path = get_ico_path_by_name(battle_call_name)
            icon = load_menu_icon(ico_path, battle_call_name)
            add_menu_action(battle_menu, battle_call_name, icon,
                            callback, None, scrollbar_frame_obj)


    # 搜索
    search_btn = QToolButton()
    search_btn.setText("🔍搜索")
    search_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    search_btn.setStyleSheet("""
        QToolButton {
            padding: 4px 10px;
            border: none;
            color: #333333;
            background-color: transparent;
            border-radius: 4px;
            font-size: 16px;
            font-weight: bold;
        }
        QToolButton:hover {
            background-color: #e0e0e0;
        }
        QToolButton:pressed {
            background-color: #d0d0d0;
        }
    """)
    search_btn.clicked.connect(lambda: creat_search_win(root, scrollbar_frame_obj))
    menu_bar.addWidget(search_btn)

    # 音乐
    music_btn = QToolButton()
    music_btn.setText("🎧音乐")
    music_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    music_btn.setStyleSheet(search_btn.styleSheet())  # 复用样式
    music_btn.clicked.connect(lambda: creat_music_win())
    menu_bar.addWidget(music_btn)

    tool_menu = add_top_menu_button(menu_bar, "🛠️工具", "🛠️工具", None)[0]
    menu_tool_calls = [
        ("图片转线稿工具2.0", load_LineArtGUI2_QT),
        ("seed tools", load_seed_tools),
        ("词条获取", creat_ct_win),
        ("伤害分计算", creat_dsc_win),
        ("伤害分计算V2", creat_dsc_win_v2),
        ("风格图鉴获取", get_hbr_brochure),
        ("AFSGTools伤害计算", load_AFSGTools),
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
    for tool_call_name, callback in menu_tool_calls:
        icon = load_menu_icon("./工具/w1.ico", tool_call_name)
        add_menu_action(tool_menu, tool_call_name, icon, callback)

    # 更新
    update_btn = QToolButton()
    update_btn.setText("📲更新")
    update_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    update_btn.setStyleSheet(search_btn.styleSheet())
    update_btn.clicked.connect(lambda: http_update_data(root))
    menu_bar.addWidget(update_btn)

    # 关于
    about_btn = QToolButton()
    about_btn.setText("🏷️关于")
    about_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    about_btn.setStyleSheet(search_btn.styleSheet())
    about_btn.clicked.connect(lambda: creat_about_win(root))
    menu_bar.addWidget(about_btn)

    bind_shortcuts(root, scrollbar_frame_obj)


if __name__ == "__main__":
    restart_args = [sys.executable] + sys.argv
    
    while True:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        base_dir = os.path.dirname(os.path.abspath(__file__))
        qss_path = os.path.join(base_dir, 'QSS', 'QMessageBox_qss', 'style.qss')
        with open(qss_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())

        if is_admin():
            root_win_name = "HBRDatabase - 以管理员身份运行"
        else:
            root_win_name = "HBRDatabase"

        delete_old_file_and_subdirs()
        set_global_bg(app)

        root = creat_window(root_win_name, 1160, 700, 440, 50)
        set_window_icon(root, "./favicon.ico")

        central_widget = QWidget()
        root.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scrollbar_frame_obj = ScrollbarFrameWin(central_widget, columnspan=6)
        create_menu(root, scrollbar_frame_obj)

        ResizableArtworkDisplayerHeight(
            scrollbar_frame_obj.scrollable_frame, "vbg_hbr.png", "70%"
        )

        check_error_queue_qt(root)
        check_for_updates()

        root.show()
        
        exit_code = app.exec_()
        
        # app.exec_() 返回后，Qt 事件循环已结束
        # 所有 Qt 对象已析构、aboutToQuit 信号已触发、文件句柄已关闭
        
        # 检查是否需要重启
        if app.property("_restart_requested"):
            logger.info("检测到重启标志，正在启动新进程...")
            # start_new_session=True 确保新进程完全脱离当前进程
            subprocess.Popen(restart_args, start_new_session=True)
            break  # 退出 while 循环，当前进程正常结束
        else:
            # 正常退出
            sys.exit(exit_code)

