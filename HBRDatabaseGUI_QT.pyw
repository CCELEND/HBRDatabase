import sys

# 兼容 CPython 3.12/3.13 早期版本：退出时 _active_limbo_lock 可能为 None，
# 导致 DummyThread 清理抛出 TypeError。此处安全地忽略该异常。
try:
    import threading
    _dtd_cls = getattr(threading, "_DeleteDummyThreadOnDel", None)
    if _dtd_cls is not None:
        _orig_del = _dtd_cls.__del__
        def _safe_dummy_thread_del(self):
            try:
                _orig_del(self)
            except TypeError:
                pass
        _dtd_cls.__del__ = _safe_dummy_thread_del
except Exception:
    pass

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


TOOL_BUTTON_STYLE = """
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
"""

from 日志.error_queue_proc_qt import check_error_queue_qt

# ---------------------------------------------------------------------------
# 延迟导入：菜单里的工具模块（pandas / selenium / pygame / openpyxl 等）只在
# **真正点击**时才 import，避免每次启动都付出上秒级的导入开销。
# ---------------------------------------------------------------------------
import importlib


def lazy_call(module_path, attr):
    """返回一个函数：调用时才 import module_path 并取 attr 执行。"""
    def _call(*args, **kwargs):
        mod = importlib.import_module(module_path)
        return getattr(mod, attr)(*args, **kwargs)
    return _call


# 下面这些名字与原「模块级 import」完全一致，只是改为**点击时才导入**。

# ---- 持有物 ----
show_main_props = lazy_call("持有物.主线道具.main_props_win_qt", "show_main_props")
show_props = lazy_call("持有物.道具.props_win_qt", "show_props")
show_jewelrys_type = lazy_call("持有物.饰品.jewelrys_win_qt", "show_jewelrys_type")
show_jewelry_materials = lazy_call(
    "持有物.饰品材料.jewelry_materials_win_qt", "show_jewelry_materials")
show_medals = lazy_call("持有物.活动奖章.medals_win_qt", "show_medals")
show_trophy_medals = lazy_call(
    "持有物.奖杯勋章.trophy_medals_win_qt", "show_trophy_medals")
show_growth_materials = lazy_call(
    "持有物.成长素材.growth_materials_win_qt", "show_growth_materials")
show_strengthen_materials = lazy_call(
    "持有物.强化素材.strengthen_materials_win_qt", "show_strengthen_materials")
show_amplifiers = lazy_call("持有物.增幅器.amplifiers_win_qt", "show_amplifiers")
show_chips = lazy_call("持有物.芯片.chips_win_qt", "show_chips")
show_tickets = lazy_call("持有物.入场券.tickets_win_qt", "show_tickets")
show_capsuletoys = lazy_call("持有物.扭蛋材料.capsuletoys_win_qt",
                             "show_capsuletoys")
show_fragments = lazy_call("持有物.碎片.fragments_win_qt", "show_fragments")
show_currencys = lazy_call("持有物.货币.currencys_win_qt", "show_currencys")

# ---- 战斗系统 ----
creat_gmtf_win = lazy_call("战斗系统.共鸣天赋.gmtf_win_qt", "creat_gmtf_win")
creat_jc_win = lazy_call("战斗系统.基础.jc_win_qt", "creat_jc_win")
creat_od_win = lazy_call("战斗系统.OD.od_win_qt", "creat_od_win")
creat_cq_win = lazy_call("战斗系统.乘区.cq_win_qt", "creat_cq_win")
show_career = lazy_call("战斗系统.职业.careers_win_qt", "show_career")
show_weapon = lazy_call("战斗系统.武器.weapons_win_qt", "show_weapon")
show_attribute = lazy_call("战斗系统.属性.attributes_win_qt", "show_attribute")
show_statu = lazy_call("战斗系统.状态.status_win_qt", "show_statu")

# ---- 敌人 ----
show_szt_enemys = lazy_call("敌人.时钟塔.szt_win_qt", "show_szt_enemys")
show_zx_enemys = lazy_call("敌人.主线.zx_win_qt", "show_zx_enemys")
show_gqboss_enemys = lazy_call("敌人.光球BOSS.gqboss_win_qt",
                               "show_gqboss_enemys")
show_szxlc_enemys = lazy_call("敌人.时之修炼场.szxlc_win_qt",
                              "show_szxlc_enemys")
show_ljz_enemys = lazy_call("敌人.棱镜战.ljz_win_qt", "show_ljz_enemys")
show_bsljz_enemys = lazy_call("敌人.宝石棱镜战.bsljz_win_qt",
                              "show_bsljz_enemys")
show_hxz_enemys = lazy_call("敌人.恒星战.hxz_win_qt", "show_hxz_enemys")
show_gftz_enemys = lazy_call("敌人.高分挑战.gftz_win_qt", "show_gftz_enemys")
show_ysc_enemys = lazy_call("敌人.异时层.ysc_win_qt", "show_ysc_enemys")
show_zyz_enemys = lazy_call("敌人.遭遇战.zyz_win_qt", "show_zyz_enemys")

# ---- 搜索 / 角色 / 更新 / 音乐 / 关于 ----
creat_search_win = lazy_call("搜索.search_win_qt", "creat_search_win")
creat_team_win = lazy_call("角色.team_win_qt", "creat_team_win")
http_update_data = lazy_call("更新.http_update_processing_qt", "http_update_data")
creat_music_win = lazy_call("音乐.music_win_qt", "creat_music_win")
creat_about_win = lazy_call("关于.about_win_qt", "creat_about_win")
check_for_updates = lazy_call("更新.check_proc_qt", "check_for_updates")

# ---- 工具 ----
load_seed_tools = lazy_call("工具.GetEntriesGUILocal.seed_tools.Load_qt",
                            "load_seed_tools")
creat_ct_win = lazy_call("工具.GetEntriesGUILocal.get_entries_win_qt",
                         "creat_ct_win")
creat_dsc_win = lazy_call("工具.DamageScoreCal.damage_score_cal_win_qt",
                          "creat_dsc_win")
creat_dsc_win_v2 = lazy_call("工具.DamageScoreCal.damage_score_cal_win_v2_qt",
                             "creat_dsc_win_v2")
get_hbr_brochure = lazy_call("工具.HBRbrochure.HBRbrochure",
                             "get_hbr_brochure")
load_AFSGTools = lazy_call("工具.AFSGTools.Load", "load_AFSGTools")
load_hbr_damage_simulation = lazy_call("工具.HBR伤害模拟.Load",
                                       "load_hbr_damage_simulation")
load_hbr_tool = lazy_call("工具.hbr_tool.Load", "load_hbr_tool")
load_hbr_tool_old_damage_calculator = lazy_call(
    "工具.hbr_tool_old_damage_calculator.Load",
    "load_hbr_tool_old_damage_calculator")
load_hbr_axletool = lazy_call("工具.hbr_axletool.Load", "load_hbr_axletool")
load_hbr_axle_od = lazy_call("工具.排轴.Load", "load_hbr_axle_od")
load_wiki_hbr_hd = lazy_call("工具.wiki_hbr_hd.Load", "load_wiki_hbr_hd")
load_entry_calculator = lazy_call("工具.词条计算器.Load",
                                  "load_entry_calculator")
load_o_hbr_quest = lazy_call("工具.o_hbr_quest.Load", "load_o_hbr_quest")
load_hbr_quest = lazy_call("工具.hbr_quest.Load", "load_hbr_quest")
load_game8_hbr = lazy_call("工具.game8_hbr.Load", "load_game8_hbr")
load_gamekee_hbr = lazy_call("工具.gamekee_hbr.Load", "load_gamekee_hbr")
load_game_bilibili_com = lazy_call("工具.入队培训手册.Load",
                                   "load_game_bilibili_com")
load_LineArtGUI2_QT = lazy_call("工具.LineArt.LineArtGUI2_QT",
                                "load_LineArtGUI2_QT")

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
            icon = load_menu_icon("./工具/help.png", battle_call_name)
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
    search_btn.setStyleSheet(TOOL_BUTTON_STYLE)
    search_btn.clicked.connect(lambda: creat_search_win(root, scrollbar_frame_obj))
    menu_bar.addWidget(search_btn)

    # 音乐
    music_btn = QToolButton()
    music_btn.setText("🎧音乐")
    music_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    music_btn.setStyleSheet(TOOL_BUTTON_STYLE)
    music_btn.clicked.connect(lambda: creat_music_win())
    menu_bar.addWidget(music_btn)

    tool_menu = add_top_menu_button(menu_bar, "🛠️工具", "🛠️工具", None)[0]
    menu_tool_calls = [
        ("排轴OD计算", load_hbr_axle_od),
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
        icon = load_menu_icon("./工具/developer_mode.png", tool_call_name)
        add_menu_action(tool_menu, tool_call_name, icon, callback)

    # 更新
    update_btn = QToolButton()
    update_btn.setText("📲更新")
    update_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    update_btn.setStyleSheet(TOOL_BUTTON_STYLE)
    update_btn.clicked.connect(lambda: http_update_data(root))
    menu_bar.addWidget(update_btn)

    # 关于
    about_btn = QToolButton()
    about_btn.setText("🏷️关于")
    about_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    about_btn.setStyleSheet(TOOL_BUTTON_STYLE)
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
            qss_content = f.read()

        if is_admin():
            root_win_name = "HBRDatabase - 以管理员身份运行"
        else:
            root_win_name = "HBRDatabase"

        delete_old_file_and_subdirs()
        set_global_bg(app)
        app.setStyleSheet(app.styleSheet() + "\n" + qss_content)

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

