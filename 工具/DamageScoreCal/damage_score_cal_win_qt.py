#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import math

from PyQt5.QtWidgets import (
    QFrame, QLabel, QPushButton, QTextEdit, QGridLayout
)
from PyQt5.QtCore import Qt

from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top
from window_qt import show_context_menu, clear_text, edit_text

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

maximum_damage_limit_text = None
input_text = None
output_text = None


def get_maximum_damage_limit():
    maximum_damage_limit_str = maximum_damage_limit_text.toPlainText()
    maximum_damage_limit_str = maximum_damage_limit_str.strip()
    if maximum_damage_limit_str == "":
        return 300000

    try:
        maximum_damage_limit = int(maximum_damage_limit_str, 0)
    except Exception as e:
        logger.error(str(e))
        edit_text(output_text, f"[-] {e}")
        return -1

    return maximum_damage_limit


def get_input():
    input_text_str = input_text.toPlainText()
    input_text_str = input_text_str.strip()
    if input_text_str == "":
        clear_text(output_text)
        return 0

    try:
        input_val = int(input_text_str, 0)
    except Exception as e:
        logger.error(str(e))
        edit_text(output_text, f"[-] {e}")
        return -1

    return input_val


def damage_value():
    maximum_damage_limit = get_maximum_damage_limit()
    if maximum_damage_limit == -1:
        return

    damage_reward = get_input()
    if damage_reward == -1:
        return

    damage_value = math.e ** (damage_reward / maximum_damage_limit - 1 + math.log(maximum_damage_limit * 100))
    edit_text(output_text, int(damage_value))


def damage_reward():
    maximum_damage_limit = get_maximum_damage_limit()
    if maximum_damage_limit == -1:
        return

    damage_value = get_input()
    if damage_value == -1:
        return

    damage_reward = 0
    if damage_value <= maximum_damage_limit * 100:
        damage_reward = damage_value / 100
    else:
        damage_reward = maximum_damage_limit * (1 + math.log(damage_value) - math.log(maximum_damage_limit * 100))
    edit_text(output_text, int(damage_reward))


def creat_dsc_win():
    global maximum_damage_limit_text
    global input_text
    global output_text

    if is_win_open('伤害分计算', __name__):
        win_set_top('伤害分计算', __name__)
        return "break"

    dsc_win_frame = creat_Toplevel("伤害分计算", 550, 400, 160, 160)
    set_window_icon(dsc_win_frame, "./工具/DamageScoreCal/dsc.ico")

    layout = dsc_win_frame.grid_layout
    layout.setColumnStretch(0, 1)
    layout.setColumnStretch(1, 1)
    layout.setRowStretch(0, 1)
    layout.setRowStretch(1, 1)

    input_frame = QFrame(dsc_win_frame.centralWidget())
    input_frame.setLayout(QGridLayout())
    input_frame.layout().setColumnStretch(0, 1)
    input_frame.layout().setColumnStretch(1, 1)
    layout.addWidget(input_frame, 0, 0, 1, 2)

    input_label = QLabel("输入伤害奖励 / 伤害值")
    input_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    input_frame.layout().addWidget(input_label, 0, 0)

    input_text = QTextEdit()
    input_text.setAcceptRichText(False)
    input_text.setContextMenuPolicy(Qt.CustomContextMenu)
    input_text.customContextMenuRequested.connect(
        lambda pos, tw=input_text: show_context_menu(pos, tw)
    )
    input_frame.layout().addWidget(input_text, 1, 0, 1, 2)

    maximum_damage_limit_label = QLabel("伤害上限（默认为300000）")
    maximum_damage_limit_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    input_frame.layout().addWidget(maximum_damage_limit_label, 2, 0)

    maximum_damage_limit_text = QTextEdit()
    maximum_damage_limit_text.setAcceptRichText(False)
    maximum_damage_limit_text.setContextMenuPolicy(Qt.CustomContextMenu)
    maximum_damage_limit_text.customContextMenuRequested.connect(
        lambda pos, tw=maximum_damage_limit_text: show_context_menu(pos, tw)
    )
    input_frame.layout().addWidget(maximum_damage_limit_text, 3, 0, 1, 2)

    damage_value_button = QPushButton("伤害奖励->伤害值")
    damage_value_button.clicked.connect(damage_value)
    input_frame.layout().addWidget(damage_value_button, 4, 0)

    damage_reward_button = QPushButton("伤害值->伤害奖励")
    damage_reward_button.clicked.connect(damage_reward)
    input_frame.layout().addWidget(damage_reward_button, 4, 1)

    output_frame = QFrame(dsc_win_frame.centralWidget())
    output_frame.setLayout(QGridLayout())
    output_frame.layout().setColumnStretch(0, 1)
    layout.addWidget(output_frame, 1, 0, 1, 2)

    output_label2 = QLabel("输出")
    output_label2.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    output_frame.layout().addWidget(output_label2, 0, 0)

    output_text = QTextEdit()
    output_text.setReadOnly(True)
    output_text.setContextMenuPolicy(Qt.CustomContextMenu)
    output_text.customContextMenuRequested.connect(
        lambda pos, tw=output_text: show_context_menu(pos, tw)
    )
    output_frame.layout().addWidget(output_text, 1, 0)

    clear_button = QPushButton("清空")
    clear_button.clicked.connect(
        lambda: clear_text(input_text, maximum_damage_limit_text, output_text)
    )
    layout.addWidget(clear_button, 2, 0, 1, 2)

    win_open_manage(dsc_win_frame, __name__)
    dsc_win_frame.closeEvent = lambda ev: win_close_manage(dsc_win_frame, __name__)

    return "break"
