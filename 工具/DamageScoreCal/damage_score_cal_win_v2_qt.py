#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import math
from decimal import Decimal, DecimalException

from PyQt5.QtWidgets import (
    QFrame, QLabel, QPushButton, QTextEdit, QGridLayout
)
from PyQt5.QtCore import Qt

from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top
from window_qt import show_context_menu, clear_text, edit_text

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

threshold_value_text = None
damage_coefficient_text = None
input_text_v2 = None
output_text_v2 = None


def get_threshold_value():
    threshold_value_str = threshold_value_text.toPlainText()
    threshold_value_str = threshold_value_str.strip()
    if threshold_value_str == "":
        return 42000000

    try:
        threshold_value = int(threshold_value_str, 0)
    except Exception as e:
        logger.error(str(e))
        edit_text(output_text_v2, f"[-] {e}")
        return -1

    return threshold_value


def get_damage_coefficient():
    damage_coefficient_str = damage_coefficient_text.toPlainText()
    damage_coefficient_str = damage_coefficient_str.strip()
    if damage_coefficient_str == "":
        return 0.47

    try:
        damage_coefficient = float(damage_coefficient_str)
    except Exception as e:
        logger.error(str(e))
        edit_text(output_text_v2, f"[-] {e}")
        return -1

    return damage_coefficient


def get_input():
    input_text_v2_str = input_text_v2.toPlainText()
    input_text_v2_str = input_text_v2_str.strip()
    if input_text_v2_str == "":
        clear_text(output_text_v2)
        return 0

    try:
        input_val = int(input_text_v2_str, 0)
    except Exception as e:
        logger.error(str(e))
        edit_text(output_text_v2, f"[-] {e}")
        return -1

    return input_val


def damage_value():
    threshold_value = get_threshold_value()
    if threshold_value == -1:
        return

    damage_coefficient = get_damage_coefficient()
    if damage_coefficient == -1:
        return

    damage_reward = get_input()
    if damage_reward == -1:
        return

    damage_reward = Decimal(str(damage_reward))
    threshold_value = Decimal(str(threshold_value))
    damage_coefficient = Decimal(str(damage_coefficient))

    try:
        exponent = (Decimal('100') * damage_reward) / (threshold_value * damage_coefficient) - Decimal('1') + threshold_value.ln()
        damage_value = Decimal(str(math.exp(exponent)))
    except DecimalException as de:
        logger.error(str(de))
        raise ValueError(f"Decimal计算错误: {de}")
    except Exception as e:
        logger.error(str(e))
        raise ValueError(f"计算错误: {e}")

    edit_text(output_text_v2, int(damage_value))


def damage_reward():
    threshold_value = get_threshold_value()
    if threshold_value == -1:
        return

    damage_coefficient = get_damage_coefficient()
    if damage_coefficient == -1:
        return

    damage_value = get_input()
    if damage_value == -1:
        return

    damage_coefficient = Decimal(str(damage_coefficient))
    threshold_value = Decimal(str(threshold_value))
    damage_value = Decimal(str(damage_value))

    try:
        log_damage = damage_value.ln()
        log_threshold = threshold_value.ln()
    except Exception as e:
        logger.error(str(e))
        raise ValueError(f"对数计算错误: {e}")

    if damage_value < threshold_value:
        raise ValueError("damage_value 必须大于或等于 threshold_value")

    damage_reward = (damage_coefficient / Decimal('100')) * threshold_value * (Decimal('1') + log_damage - log_threshold)
    edit_text(output_text_v2, int(damage_reward))


def creat_dsc_win_v2():
    global threshold_value_text
    global damage_coefficient_text
    global input_text_v2
    global output_text_v2

    if is_win_open('伤害分计算V2', __name__):
        win_set_top('伤害分计算V2', __name__)
        return "break"

    dsc_win_frame = creat_Toplevel("伤害分计算V2", 650, 520, 160, 160)
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

    input_text_v2 = QTextEdit()
    input_text_v2.setAcceptRichText(False)
    input_text_v2.setContextMenuPolicy(Qt.CustomContextMenu)
    input_text_v2.customContextMenuRequested.connect(
        lambda pos, tw=input_text_v2: show_context_menu(pos, tw)
    )
    input_frame.layout().addWidget(input_text_v2, 1, 0, 1, 2)

    threshold_value_label = QLabel("伤害阈值（默认为42000000）")
    threshold_value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    input_frame.layout().addWidget(threshold_value_label, 2, 0)

    threshold_value_text = QTextEdit()
    threshold_value_text.setAcceptRichText(False)
    threshold_value_text.setContextMenuPolicy(Qt.CustomContextMenu)
    threshold_value_text.customContextMenuRequested.connect(
        lambda pos, tw=threshold_value_text: show_context_menu(pos, tw)
    )
    input_frame.layout().addWidget(threshold_value_text, 3, 0, 1, 2)

    damage_coefficient_label = QLabel("伤害分系数（默认为0.47）")
    damage_coefficient_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    input_frame.layout().addWidget(damage_coefficient_label, 4, 0)

    damage_coefficient_text = QTextEdit()
    damage_coefficient_text.setAcceptRichText(False)
    damage_coefficient_text.setContextMenuPolicy(Qt.CustomContextMenu)
    damage_coefficient_text.customContextMenuRequested.connect(
        lambda pos, tw=damage_coefficient_text: show_context_menu(pos, tw)
    )
    input_frame.layout().addWidget(damage_coefficient_text, 5, 0, 1, 2)

    damage_value_button = QPushButton("伤害奖励->伤害值")
    damage_value_button.clicked.connect(damage_value)
    input_frame.layout().addWidget(damage_value_button, 6, 0)

    damage_reward_button = QPushButton("伤害值->伤害奖励")
    damage_reward_button.clicked.connect(damage_reward)
    input_frame.layout().addWidget(damage_reward_button, 6, 1)

    output_frame = QFrame(dsc_win_frame.centralWidget())
    output_frame.setLayout(QGridLayout())
    output_frame.layout().setColumnStretch(0, 1)
    layout.addWidget(output_frame, 1, 0, 1, 2)

    output_label2 = QLabel("输出")
    output_label2.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    output_frame.layout().addWidget(output_label2, 0, 0)

    output_text_v2 = QTextEdit()
    output_text_v2.setReadOnly(True)
    output_text_v2.setContextMenuPolicy(Qt.CustomContextMenu)
    output_text_v2.customContextMenuRequested.connect(
        lambda pos, tw=output_text_v2: show_context_menu(pos, tw)
    )
    output_frame.layout().addWidget(output_text_v2, 1, 0)

    clear_button = QPushButton("清空")
    clear_button.clicked.connect(
        lambda: clear_text(input_text_v2, threshold_value_text, output_text_v2)
    )
    layout.addWidget(clear_button, 2, 0, 1, 2)

    win_open_manage(dsc_win_frame, __name__)

    # 正确关闭事件
    def on_close(ev):
        win_close_manage(dsc_win_frame, __name__)
        ev.accept()
    dsc_win_frame.closeEvent = on_close

    return "break"

    return "break"
