
import types

from PyQt5.QtWidgets import (
    QLabel, QWidget, QGroupBox, QGridLayout, QVBoxLayout, 
    QPushButton, QCheckBox, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt

from window_qt import set_window_expand, set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top

from 角色.team_info import get_all_team_obj
from 角色.team_win_qt import bind_style_canvas, bind_master_skill_canvas
import 角色.team_info

from 搜索.search_processing import on_select, get_filtered_styles, keyword_processing
from 搜索.search_processing_master import get_filtered_master_skills


class CheckBoxVar:
    def __init__(self, cb):
        self.cb = cb

    def get(self):
        return self.cb.isChecked()

    def set(self, v):
        self.cb.setChecked(v)


has_shown_warning = False


def limit_text_length(text_edit):
    global has_shown_warning
    current_text = text_edit.toPlainText()
    max_length = 1000

    if len(current_text) > max_length:
        if not has_shown_warning:
            QMessageBox.warning(None, "输入过长", f"输入内容超出限制！最多可输入{max_length}个字符。")
            has_shown_warning = True
        text_edit.setPlainText(current_text[:max_length])
        text_edit.moveCursor(text_edit.textCursor().End)
    else:
        has_shown_warning = False


def creat_select_frame(label_content, options, selected_values, parent_frame, row, column):
    label_frame = QGroupBox(label_content)
    frame_layout = QVBoxLayout(label_frame)
    frame_layout.setContentsMargins(10, 10, 10, 10)
    frame_layout.setSpacing(5)
    frame_layout.setAlignment(Qt.AlignTop)

    check_frame = QWidget(label_frame)
    check_layout = QGridLayout(check_frame)
    check_layout.setContentsMargins(0, 0, 0, 0)
    check_layout.setSpacing(5)
    check_layout.setAlignment(Qt.AlignTop)

    check_vars = []
    last = [False] * len(options)

    if label_content == "技能、天赋":
        n = 2
    elif label_content == "稀有度":
        n = 5
    else:
        n = 4

    for i, value in enumerate(options):
        check_box = QCheckBox(value)
        check_box.stateChanged.connect(lambda: on_select(check_vars, options, last, selected_values))

        r = i // n
        c = i % n
        check_layout.addWidget(check_box, r, c)
        check_vars.append(CheckBoxVar(check_box))

    frame_layout.addWidget(check_frame)

    parent_layout = parent_frame.layout()
    if parent_layout is not None and isinstance(parent_layout, QGridLayout):
        parent_layout.addWidget(label_frame, row, column)

    return label_frame


def show_search(scrollbar_frame_obj, search_win_frame, key_word_text, selected_values_dir):
    win_set_top(search_win_frame, __name__)
    key_word_str = key_word_text.toPlainText().strip()
    keyword_list = keyword_processing(key_word_str)

    scrollbar_frame_obj.destroy_components()
    scroll_layout = scrollbar_frame_obj.scrollable_frame.layout()
    if scroll_layout is None:
        scroll_layout = QGridLayout(scrollbar_frame_obj.scrollable_frame)
        for col in range(5):
            scroll_layout.setColumnStretch(col, 1)

    scroll_layout.setContentsMargins(10, 10, 10, 10)
    scroll_layout.setSpacing(5)
    scroll_layout.setAlignment(Qt.AlignTop)

    if selected_values_dir["大师技能"]:
        filtered_master_skills = get_filtered_master_skills(selected_values_dir, keyword_list)
        for i, master_skill in enumerate(filtered_master_skills):
            role = None
            for team in 角色.team_info.teams.values():
                for r in team.roles:
                    if r.master_skill and r.master_skill.name == master_skill.name:
                        role = r
                        break
                if role:
                    break

            master_skill_frame = QGroupBox(master_skill.name)
            master_skill_frame.setFixedHeight(170)
            frame_layout = QGridLayout(master_skill_frame)
            frame_layout.setContentsMargins(5, 5, 5, 5)
            frame_layout.setSpacing(5)
            if role:
                bind_master_skill_canvas(master_skill_frame, role, 0, 0)

            row = i // 6
            column = i % 6
            scroll_layout.addWidget(master_skill_frame, row, column)

        scrollbar_frame_obj.update_canvas()
        return "break"

    filtered_styles = get_filtered_styles(selected_values_dir, keyword_list)

    for i, style in enumerate(filtered_styles):
        team = 角色.team_info.teams[style.team_name]

        style_frame = QGroupBox(style.name)
        style_frame.setFixedHeight(170)
        frame_layout = QGridLayout(style_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)
        frame_layout.setSpacing(5)
        bind_style_canvas(style_frame, team, style, 0, 0)

        row = i // 5
        column = i % 5
        scroll_layout.addWidget(style_frame, row, column)

    scrollbar_frame_obj.update_canvas()
    return "break"


def creat_search_win(parent_frame, scrollbar_frame_obj):
    if is_win_open("搜索", __name__):
        win_set_top("搜索", __name__)
        return "break"

    get_all_team_obj()

    search_win_frame = creat_Toplevel("搜索", 730, 570, 190, 210)
    set_window_icon(search_win_frame, "./搜索/search_temp.ico")


    search_win_frame.setStyleSheet("""
        /* ----- 按钮 ----- */
        QPushButton {
            background-color: #e6f0fa;
            border: 1px solid #b0c4de;
            border-radius: 8px;
            padding: 8px 18px;
            font-weight: bold;
            font-size: 13px;
            color: #1f3a5f;
        }
        QPushButton:hover {
            background-color: #c9dff5;
            border-color: #7fa9d4;
        }
        QPushButton:pressed {
            background-color: #a8c8e8;
            border-color: #4a7db0;
        }
        QPushButton:disabled {
            background-color: #e8e8e8;
            border-color: #d0d0d0;
            color: #999;
        }

        /* ----- 复选框 ----- */
        QCheckBox {
            background-color: transparent;
            spacing: 8px;
            font-size: 14px;
            font-weight: bold;
            color: #333333;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 1px solid #b0b0b0;
            background-color: #ffffff;
        }
        QCheckBox::indicator:hover {
            border-color: #0078d4;
            background-color: #e6f2ff;
        }
        QCheckBox::indicator:checked {
            background-color: #0078d4;
            border-color: #0078d4;
            image: url(./搜索/check.png);
        }
        QCheckBox::indicator:checked:hover {
            background-color: #005bb5;
            border-color: #005bb5;
        }
        QCheckBox::indicator:disabled {
            border-color: #d0d0d0;
            background-color: #f0f0f0;
        }

        /* ----- 文本框 ----- */
        QTextEdit {
            border: 1px solid #d0d0d0;
            border-radius: 6px;
            padding: 8px;
            font-size: 13px;
            background-color: #ffffff;
        }
        QTextEdit:focus {
            border-color: #0078d4;
            background-color: #fafcff;
        }

        /* ----- 窗口背景（保持与主窗口一致） ----- */
        QWidget {
            background-color: #f0f0f0;
        }
    """)

    set_window_expand(search_win_frame, rowspan=1, columnspan=2)

    role_search_frame = QGroupBox("角色、风格")
    role_search_layout = QGridLayout(role_search_frame)
    role_search_layout.setContentsMargins(10, 10, 10, 10)
    role_search_layout.setSpacing(5)

    rarity_options = ["ALL", "A", "S", "SS", "SSR"]
    rarity_selected_values = []
    creat_select_frame("稀有度", rarity_options, rarity_selected_values, role_search_frame, 0, 0)

    career_options = [
        "ALL", "攻击者", "破盾者", "破坏者", "治疗者",
        "增益者", "减益者", "防御者", "指挥者", "驰骋者"
    ]
    career_selected_values = []
    creat_select_frame("职能", career_options, career_selected_values, role_search_frame, 0, 1)

    team_options = [
        "ALL", "31A", "31B", "31C", "30G",
        "31D", "31E", "31F", "31X",
        "Angel Beats!", "司令部"
    ]
    team_selected_values = []
    creat_select_frame("队伍", team_options, team_selected_values, role_search_frame, 1, 0)

    weapon_attribute_options = ["ALL", "斩", "突", "打"]
    weapon_attribute_selected_values = []
    creat_select_frame("武器属性", weapon_attribute_options, weapon_attribute_selected_values, role_search_frame, 1, 1)

    element_attribute_options = [
        "ALL", "火", "冰", "雷", "光", "暗", "无"
    ]
    element_attribute_selected_values = []
    creat_select_frame("元素属性", element_attribute_options, element_attribute_selected_values, role_search_frame, 2, 0)

    skill_options = [
        "ALL", "主动/被动", "天赋/大师被动", "共鸣天赋"
    ]
    skill_selected_values = []
    creat_select_frame("技能、天赋", skill_options, skill_selected_values, role_search_frame, 2, 1)

    master_skill_options = ["ALL", "大师技能"]
    master_skill_selected_values = []
    creat_select_frame("大师技能", master_skill_options, master_skill_selected_values, role_search_frame, 3, 0)

    selected_values_dir = {
        "稀有度": rarity_selected_values,
        "职能": career_selected_values,
        "队伍": team_selected_values,
        "武器属性": weapon_attribute_selected_values,
        "元素属性": element_attribute_selected_values,
        "技能、天赋": skill_selected_values,
        "大师技能": master_skill_selected_values,
    }

    central = search_win_frame.centralWidget()
    layout = central.layout()
    if layout is not None:
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
    else:
        layout = QGridLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
    layout.addWidget(role_search_frame, 0, 0, 1, 2)

    key_word_label = QLabel("关键词")
    layout.addWidget(key_word_label, 1, 0)

    key_word_text = QTextEdit()
    key_word_text.setMaximumHeight(80)
    key_word_text.textChanged.connect(lambda: limit_text_length(key_word_text))
    layout.addWidget(key_word_text, 2, 0, 1, 2)

    search_button = QPushButton("搜索")
    search_button.setFixedWidth(120)
    search_button.clicked.connect(lambda: show_search(scrollbar_frame_obj, search_win_frame, key_word_text, selected_values_dir))
    layout.addWidget(search_button, 3, 0, 1, 2, alignment=Qt.AlignCenter)

    win_open_manage(search_win_frame, __name__)

    def on_close(self, event):
        win_close_manage(search_win_frame, __name__)
        event.accept()

    search_win_frame.closeEvent = types.MethodType(on_close, search_win_frame)

    return "break"

