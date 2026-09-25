# -*- coding: utf-8 -*-
"""
排轴 + OD 计算

参考 https://hbr-axletool.pages.dev/ 的排轴界面形式，使用 PyQt5 实现，
并在其基础上补充 OD 计算功能（参考 ./工具/等效破坏率与OD计算表.xlsx）。

规则：
    * 一个队伍有 6 人，每人装备一个风格。
    * 一个回合最多 3 人行动。
    * 所有风格都有「通常攻击」：默认 3 Hit，且不享受 OD 耳环加成。

界面：
    * 队伍配置：6 个位置，各选择角色与风格。
    * 排轴：每个回合最多 3 次行动，每次行动选择队员、技能，并配置
      该次行动的 OD 参数（原始Hit数 / 连击数 / 固定OD / 31X共鸣 / OD耳环）。
    * 全局战斗设置：敌人数量、抗性、其他OD增量、敌方OD率。
    * 按公式实时计算每个回合的 OD 与累计总 OD。
    * SP：参考 https://www.hbr-tool.com/#/simulator 模拟每名队员的 SP，
      回合开始全队回复（默认 +2，上限默认 20），行动扣除技能 SP，
      发动 OD 额外获得 OD1 +5 / OD2 +12 / OD3~5 +20，并显示每行动的剩余 SP。
"""

import os
import json
import types
from contextlib import contextmanager

from PyQt5.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QHBoxLayout, QVBoxLayout, QGridLayout,
    QScrollArea, QFileDialog, QMessageBox, QGroupBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal

from window_qt import set_window_icon, creat_Toplevel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top

from 工具.排轴.od_calc import ODSkill, ODBattle, calc_od
from 工具.排轴.data_source import (
    get_data_source, NORMAL_ATTACK_NAME, NORMAL_ATTACK_HITS)

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


WINDOW_TITLE = "排轴OD计算"
MODULE_NAME = __name__
DEFAULT_SAVE_PATH = os.path.join("工具", "排轴", "排轴存档.json")

TEAM_SIZE = 6
MAX_ACTIONS_PER_TURN = 3
TURN_OPTIONS = ["通常回合", "切换", "追加回合"]

# 与参考站点一致的 OD 选项
# OD 最高 3 级
OD_OPTIONS = [
    "无",
    "OD1", "OD1/Bonus1",
    "OD2", "OD2/Bonus1", "OD2/Bonus2",
    "OD3", "OD3/Bonus1", "OD3/Bonus2", "OD3/Bonus3",
]

# 发动 OD 时全队获得的 SP（下标为 OD 等级，参考 hbr-tool）
OD_SP_BONUS = [0, 5, 12, 20, 20, 20]

# OD 等级 -> 行背景色（参考站点配色）
OD_COLORS = {
    "OD1": "rgba(229, 131, 207, 0.25)",
    "OD2": "rgba(189, 247, 211, 0.25)",
    "OD3": "rgba(237, 225, 108, 0.25)",
    "OD4": "rgba(91, 163, 239, 0.25)",
    "OD5": "rgba(177, 98, 237, 0.25)",
}

# 行动列宽（表头与数据行共用）
MEMBER_W, SKILL_W = 150, 200
HIT_W, COMBO_W = 58, 58
FIXED_W, RES_W, EARRING_W = 72, 72, 72
BREAK_W, SP_W, RESULT_W = 48, 62, 66
DEL_W = 26
ACTION_COLUMNS = [
    ("角色", MEMBER_W), ("行动", SKILL_W), ("原始Hit", HIT_W), ("连击", COMBO_W),
    ("固定OD", FIXED_W), ("31X共鸣", RES_W), ("OD耳环", EARRING_W),
    ("击破", BREAK_W), ("剩余SP", SP_W), ("该次OD", RESULT_W), ("", DEL_W),
]

# 下拉框样式：显式指定文字与选中项配色，避免因全局 QSS 只给滚动条设样式
# 而使用 QStyleSheetStyle 渲染时，下拉项选中文字变成白色难以辨认。
COMBO_QSS = """
QComboBox {
    color: #222222;
}
QComboBox:disabled {
    color: #999999;
}
QComboBox QAbstractItemView {
    color: #222222;
    background-color: #ffffff;
    outline: 0;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
}
QComboBox QAbstractItemView::item {
    color: #222222;
    min-height: 20px;
    padding: 2px 6px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #e6f0fb;
    color: #222222;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}
"""

TURN_CARD_STYLE = """
    #turnCard {
        background-color: %(bg)s;
        border: 1px solid #d0d0d0;
        border-left: 6px solid %(accent)s;
        border-radius: 4px;
    }
    #turnCard QLabel { background-color: transparent; }
"""


def _make_double_spin(minimum, maximum, step, decimals, value, width=72):
    spin = QDoubleSpinBox()
    spin.setRange(minimum, maximum)
    spin.setSingleStep(step)
    spin.setDecimals(decimals)
    spin.setValue(value)
    spin.setFixedWidth(width)
    spin.setAlignment(Qt.AlignCenter)
    return spin


def _build_action_header():
    """行动列表的列名表头。"""
    header = QWidget()
    layout = QHBoxLayout(header)
    layout.setContentsMargins(28, 0, 6, 0)
    layout.setSpacing(5)
    for text, width in ACTION_COLUMNS:
        label = QLabel(text)
        label.setFixedWidth(width)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(label)
    return header


# ======================================================================
# 队伍成员
# ======================================================================
class TeamMemberRow(QFrame):
    """队伍中的一个位置：角色 + 风格。"""

    changed = pyqtSignal()

    def __init__(self, slot, data_source, parent=None):
        super().__init__(parent)
        self.slot = slot
        self.data_source = data_source
        self._loading = 0
        self._build_ui()
        self._populate_styles()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel("角色%d" % self.slot)
        label.setFixedWidth(42)
        layout.addWidget(label)

        self.role_combo = QComboBox()
        # 「无」表示该位置不安排角色，从而可自由调整队伍人数
        self.role_combo.addItem("无")
        self.role_combo.addItems(self.data_source.role_names())
        self.role_combo.setFixedWidth(104)
        self.role_combo.currentTextChanged.connect(self._on_role_changed)
        layout.addWidget(self.role_combo)

        self.style_combo = QComboBox()
        self.style_combo.setFixedWidth(210)
        self.style_combo.currentTextChanged.connect(self._on_style_changed)
        self.style_combo.currentTextChanged.connect(
            lambda text: self.style_combo.setToolTip(text))
        layout.addWidget(self.style_combo)

    @contextmanager
    def _suspended(self):
        self._loading += 1
        try:
            yield
        finally:
            self._loading -= 1

    def _on_role_changed(self, role):
        if self._loading:
            return
        self._populate_styles(preserve="")
        self._emit_changed()

    def _on_style_changed(self, style):
        if self._loading:
            return
        self._emit_changed()

    def _populate_styles(self, preserve=None):
        if self.role_combo.currentText() == "无":
            with self._suspended():
                self.style_combo.clear()
                self.style_combo.setEnabled(False)
                self.style_combo.setToolTip("")
            return
        self.style_combo.setEnabled(True)
        current = preserve if preserve is not None else self.style()
        styles = self.data_source.styles(self.role_combo.currentText())
        with self._suspended():
            self.style_combo.clear()
            for style in styles:
                # 显示「风格名-稀有度」，实际值仍保存纯风格名
                self.style_combo.addItem(style.display_name(), style.name)
            pos = self.style_combo.findData(current)
            if pos >= 0:
                self.style_combo.setCurrentIndex(pos)
            elif styles:
                self.style_combo.setCurrentIndex(0)
            self.style_combo.setToolTip(self.style_combo.currentText())

    def _emit_changed(self, *args):
        if self._loading:
            return
        self.changed.emit()

    def set_slot_enabled(self, enabled):
        """前锋未满 3 人时禁用后卫位置。"""
        self.role_combo.setEnabled(enabled)
        if not enabled:
            self.style_combo.setEnabled(False)
            self.role_combo.setToolTip("前锋满 3 人后才能安排后卫")
        else:
            self.role_combo.setToolTip("")
            self.style_combo.setEnabled(self.role_combo.currentText() != "无")

    def set_role(self, role):
        self.role_combo.setCurrentText(role if role else "无")

    def role(self):
        text = self.role_combo.currentText()
        return "" if text == "无" else text

    def style(self):
        # 下拉显示带稀有度，实际值取 itemData（纯风格名）
        data = self.style_combo.currentData()
        return data if data else self.style_combo.currentText()

    def to_data(self):
        return {"role": self.role(), "style": self.style()}

    def set_data(self, data):
        with self._suspended():
            role = data.get("role", "")
            self.role_combo.setCurrentText(role if role else "无")
            self._populate_styles(preserve=data.get("style", ""))
            style = data.get("style", "")
            pos = self.style_combo.findData(style) if style else -1
            if pos >= 0:
                self.style_combo.setCurrentIndex(pos)


# ======================================================================
# 一次行动
# ======================================================================
class ActionRow(QFrame):
    """回合中的一次行动。"""

    changed = pyqtSignal()
    delete_requested = pyqtSignal(object)

    def __init__(self, owner, turn=None, data=None, default_member=0,
                 parent=None):
        super().__init__(parent)
        self.owner = owner
        self.turn = turn
        self.data_source = owner.data_source
        self._loading = 0
        self._earring_backup = 1.0
        self.member_index = default_member
        self._build_ui()
        self._populate_members()
        self._populate_skills()
        self._apply_skill_data()
        if data:
            self.set_data(data)

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 2, 6, 2)
        layout.setSpacing(5)

        self.member_combo = QComboBox()
        self.member_combo.setFixedWidth(MEMBER_W)
        self.member_combo.currentIndexChanged.connect(self._on_member_changed)
        layout.addWidget(self.member_combo)

        self.skill_combo = QComboBox()
        self.skill_combo.setFixedWidth(SKILL_W)
        self.skill_combo.currentTextChanged.connect(self._on_skill_changed)
        layout.addWidget(self.skill_combo)

        self.base_hits_spin = QSpinBox()
        self.base_hits_spin.setRange(0, 999)
        self.base_hits_spin.setFixedWidth(HIT_W)
        self.base_hits_spin.setAlignment(Qt.AlignCenter)
        self.base_hits_spin.setToolTip("技能原始Hit数（选择技能后自动带出）")
        self.base_hits_spin.valueChanged.connect(self._emit_changed)
        layout.addWidget(self.base_hits_spin)

        self.combo_spin = QSpinBox()
        self.combo_spin.setRange(0, 999)
        self.combo_spin.setFixedWidth(COMBO_W)
        self.combo_spin.setAlignment(Qt.AlignCenter)
        self.combo_spin.setToolTip("连击数")
        self.combo_spin.valueChanged.connect(self._emit_changed)
        layout.addWidget(self.combo_spin)

        self.fixed_od_spin = _make_double_spin(0.0, 100.0, 0.05, 3, 0.0, FIXED_W)
        self.fixed_od_spin.setToolTip("固定OD")
        self.fixed_od_spin.valueChanged.connect(self._emit_changed)
        layout.addWidget(self.fixed_od_spin)

        self.resonance_spin = _make_double_spin(0.0, 100.0, 0.01, 2, 0.0, RES_W)
        self.resonance_spin.setToolTip("31X 共鸣")
        self.resonance_spin.valueChanged.connect(self._emit_changed)
        layout.addWidget(self.resonance_spin)

        self.earring_spin = _make_double_spin(0.0, 10.0, 1.0, 2, 1.0, EARRING_W)
        self.earring_spin.setToolTip("OD耳环（通常攻击不享受，自动为 0）")
        self.earring_spin.valueChanged.connect(self._emit_changed)
        layout.addWidget(self.earring_spin)

        self.break_check = QCheckBox("破")
        self.break_check.setFixedWidth(BREAK_W)
        self.break_check.setToolTip(
            "本次行动击破敌人（触发「击破时回复SP」的技能/被动）")
        self.break_check.stateChanged.connect(self._emit_changed)
        layout.addWidget(self.break_check)

        self.sp_label = QLabel("-")
        self.sp_label.setFixedWidth(SP_W)
        self.sp_label.setAlignment(Qt.AlignCenter)
        self.sp_label.setToolTip("该次行动后队员的剩余 SP")
        self.sp_label.setStyleSheet(
            "background-color: #eef3ff; border-radius: 3px;")
        layout.addWidget(self.sp_label)

        self.result_label = QLabel("0.00")
        self.result_label.setFixedWidth(RESULT_W)
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setStyleSheet(
            "background-color: #eef3ff; border-radius: 3px;")
        layout.addWidget(self.result_label)

        self.delete_button = QPushButton("×")
        self.delete_button.setFixedWidth(DEL_W)
        self.delete_button.setToolTip("删除该次行动")
        self.delete_button.clicked.connect(
            lambda: self.delete_requested.emit(self))
        layout.addWidget(self.delete_button)

    @contextmanager
    def _suspended(self):
        self._loading += 1
        try:
            yield
        finally:
            self._loading -= 1

    # ---------------------------------------------------------- population
    def _populate_members(self):
        team = self.owner.team
        # 同一回合内每位队员只能行动一次
        used = self.turn.used_members(self) if self.turn else set()
        # 追加回合只能选择上一个普通回合的前锋
        allowed = self.turn.available_member_slots() if self.turn \
            else list(range(len(team)))
        with self._suspended():
            self.member_combo.clear()
            for i in allowed:
                if not (0 <= i < len(team)) or not (team[i].get("role")):
                    continue
                if i in used and i != self.member_index:
                    continue
                role = team[i].get("role") or ""
                self.member_combo.addItem("角色%d %s" % (i + 1, role), i)
            pos = self.member_combo.findData(self.member_index)
            if pos < 0:
                pos = 0
                if self.member_combo.count():
                    self.member_index = self.member_combo.itemData(0)
            self.member_combo.setCurrentIndex(pos)

    def _populate_skills(self, preserve=None):
        current = preserve if preserve is not None else self._current_skill_name()
        skills = self._all_skills()
        with self._suspended():
            self.skill_combo.clear()
            for skill in skills:
                # 显示「技能名（SP消耗）」，实际值保存纯技能名
                self.skill_combo.addItem(skill.display_name(), skill.name)
                tip = skill.sp_tooltip()
                if tip:
                    self.skill_combo.setItemData(
                        self.skill_combo.count() - 1, tip, Qt.ToolTipRole)
            pos = self.skill_combo.findData(current)
            if pos >= 0:
                self.skill_combo.setCurrentIndex(pos)
            elif skills:
                self.skill_combo.setCurrentIndex(0)

    def _current_skill_name(self):
        data = self.skill_combo.currentData()
        return data if data else self.skill_combo.currentText()

    def _all_skills(self):
        team = self.owner.team
        if not team:
            return []
        idx = min(max(self.member_index, 0), len(team) - 1)
        member = team[idx]
        return self.data_source.skills(member.get("role", ""),
                                       member.get("style", ""))

    def _find_skill(self, name=None):
        if name is None:
            name = self._current_skill_name()
        for skill in self._all_skills():
            if skill.name == name:
                return skill
        return None

    def refresh(self):
        """队伍变化后刷新成员与技能。"""
        self._populate_members()
        self._populate_skills()
        self._apply_skill_data()
        self._emit_changed()

    # ------------------------------------------------------------- signals
    def _emit_changed(self, *args):
        if self._loading:
            return
        self.changed.emit()

    def _on_member_changed(self, position):
        if self._loading:
            return
        member = self.member_combo.itemData(position)
        if member is None:
            return
        self.member_index = member
        self._populate_skills(preserve="")
        self._apply_skill_data()
        if self.turn is not None:
            self.turn.refresh_member_options(self)
        self._emit_changed()

    def _on_skill_changed(self, name):
        if self._loading:
            return
        self._apply_skill_data()
        self._emit_changed()

    def _apply_skill_data(self, name=None):
        skill = self._find_skill(name)
        with self._suspended():
            if skill is None:
                return
            if skill.hits is not None:
                self.base_hits_spin.setValue(int(skill.hits))
            else:
                # 无 Hit 信息的技能（非通常攻击）原始Hit 记 0
                self.base_hits_spin.setValue(0)
            if skill.is_normal_attack:
                if self.earring_spin.isEnabled():
                    self._earring_backup = self.earring_spin.value()
                self.earring_spin.setValue(0)
                self.earring_spin.setEnabled(False)
            else:
                self.earring_spin.setEnabled(True)
                if self.earring_spin.value() == 0:
                    self.earring_spin.setValue(self._earring_backup or 1.0)

    # ------------------------------------------------------------- helpers
    def is_normal_attack(self):
        skill = self._find_skill()
        return bool(skill and skill.is_normal_attack)

    def get_od_skill(self):
        return ODSkill(
            base_hits=self.base_hits_spin.value(),
            combo_count=self.combo_spin.value(),
            fixed_od=self.fixed_od_spin.value(),
            resonance_31x=self.resonance_spin.value(),
            od_earring=0.0 if self.is_normal_attack()
            else self.earring_spin.value(),
        )

    def set_result(self, contribution):
        self.result_label.setText("%.2f" % contribution)

    def get_sp_cost(self):
        """该次行动消耗的 SP；通常攻击为 0。"""
        skill = self._find_skill()
        return skill.sp_cost if skill else 0

    def get_sp_recover(self):
        """该次行动回复的 SP：(回复量, 范围, 元素)。"""
        skill = self._find_skill()
        if skill and skill.sp_recover and skill.sp_recover_scope:
            return (skill.sp_recover, skill.sp_recover_scope,
                    skill.sp_recover_element)
        return 0, None, None

    def is_break(self):
        return self.break_check.isChecked()

    def get_break_skill_recover(self):
        """本次行动击破敌人时，技能自带的 SP 回复 (回复量, 范围)。"""
        skill = self._find_skill()
        if skill and skill.sp_break_recover and skill.sp_break_scope:
            return skill.sp_break_recover, skill.sp_break_scope
        return 0, None

    def set_sp_result(self, remaining, enough=True):
        """显示该次行动后的剩余 SP；不足时标红。"""
        if remaining is None:
            self.sp_label.setText("-")
            self.sp_label.setStyleSheet(
                "background-color: #f0f0f0; color: #888888;"
                "border-radius: 3px;")
            return
        self.sp_label.setText(str(remaining))
        if enough:
            self.sp_label.setStyleSheet(
                "background-color: #eef3ff; border-radius: 3px;")
        else:
            self.sp_label.setStyleSheet(
                "background-color: #f5b5b5; color: #7a0000;"
                "border-radius: 3px; font-weight: bold;")
        self.sp_label.setToolTip(
            "该次行动后队员剩余 SP" if enough else "SP 不足，无法释放该技能")

    def to_data(self):
        return {
            "member": self.member_index,
            "skill": self._current_skill_name(),
            "base_hits": self.base_hits_spin.value(),
            "combo": self.combo_spin.value(),
            "fixed_od": self.fixed_od_spin.value(),
            "resonance_31x": self.resonance_spin.value(),
            "od_earring": self.earring_spin.value(),
            "break": self.break_check.isChecked(),
        }

    def set_data(self, data):
        with self._suspended():
            self.member_index = int(data.get("member", 0) or 0)
            self._populate_members()
            self._populate_skills(preserve=data.get("skill", ""))

            skill = data.get("skill", "")
            pos = self.skill_combo.findData(skill) if skill else -1
            if pos >= 0:
                self.skill_combo.setCurrentIndex(pos)

            self._apply_skill_data()

            # 仅在数据中显式给出时才覆盖，避免新建行动（只带 member）把
            # 技能自动带出的 Hit 数重置为 0
            if "base_hits" in data:
                self.base_hits_spin.setValue(int(data.get("base_hits") or 0))
            self.combo_spin.setValue(int(data.get("combo", 0) or 0))
            self.fixed_od_spin.setValue(float(data.get("fixed_od", 0) or 0))
            self.resonance_spin.setValue(float(data.get("resonance_31x", 0) or 0))
            if not self.is_normal_attack():
                self.earring_spin.setValue(float(data.get("od_earring", 1) or 0))
            self.break_check.setChecked(bool(data.get("break", False)))


# ======================================================================
# 一个回合
# ======================================================================
class TurnCard(QFrame):
    """一个回合：回合信息 + 最多 3 次行动。"""

    changed = pyqtSignal()
    delete_requested = pyqtSignal(object)
    turn_selected = pyqtSignal(object)

    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self.setObjectName("turnCard")
        self.owner = owner
        self.actions = []
        self._loading = 0
        self._build_ui()
        self.add_action()
        self._apply_style()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 4, 6, 4)
        root.setSpacing(2)

        header = QHBoxLayout()
        header.setSpacing(6)

        self.index_label = QLabel("第1回合")
        self.index_label.setFixedWidth(96)
        self.index_label.setAlignment(Qt.AlignCenter)
        header.addWidget(self.index_label)

        self.type_combo = QComboBox()
        self.type_combo.addItems(TURN_OPTIONS)
        self.type_combo.setFixedWidth(104)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        header.addWidget(self.type_combo)

        self.add_action_button = QPushButton("＋行动")
        self.add_action_button.setFixedWidth(64)
        self.add_action_button.setToolTip("每个回合最多 3 人行动")
        self.add_action_button.clicked.connect(lambda: self.add_action())
        header.addWidget(self.add_action_button)

        self.od_combo = QComboBox()
        self.od_combo.addItems(OD_OPTIONS)
        self.od_combo.setFixedWidth(112)
        self.od_combo.currentTextChanged.connect(self._on_od_changed)
        header.addWidget(self.od_combo)

        header.addStretch(1)

        self.result_label = QLabel("本回合 OD：0.00")
        self.result_label.setStyleSheet("font-weight: bold;")
        header.addWidget(self.result_label)

        self.cumulative_label = QLabel("累计：0.00")
        self.cumulative_label.setFixedWidth(110)
        header.addWidget(self.cumulative_label)

        self.delete_button = QPushButton("删除回合")
        self.delete_button.setFixedWidth(80)
        self.delete_button.clicked.connect(
            lambda: self.delete_requested.emit(self))
        header.addWidget(self.delete_button)

        root.addLayout(header)
        root.addWidget(_build_action_header())

        self.actions_layout = QVBoxLayout()
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(2)
        root.addLayout(self.actions_layout)

        # 本回合结束后全队的 SP（含后卫），便于观察未行动角色
        self.team_sp_label = QLabel("队伍SP：-")
        self.team_sp_label.setWordWrap(True)
        self.team_sp_label.setStyleSheet("color: #3355aa; font-size: 12px;")
        root.addWidget(self.team_sp_label)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    @contextmanager
    def _suspended(self):
        self._loading += 1
        try:
            yield
        finally:
            self._loading -= 1

    # ------------------------------------------------------------- actions
    def used_members(self, exclude=None):
        """本回合已被其他行动占用的队员下标。"""
        return {a.member_index for a in self.actions if a is not exclude}

    def actor_members(self):
        """本回合行动的队员下标（按行动顺序，去重，最多 3 人）。

        切换回合不行动；追加回合不影响前锋/SP，故均返回空。
        """
        if self.turn_type() in ("切换", "追加回合"):
            return []
        result = []
        for action in self.actions:
            if action.member_index not in result:
                result.append(action.member_index)
        return result[:MAX_ACTIONS_PER_TURN]

    def clear_actions(self):
        """移除全部行动（用于按上一回合继承行动）。"""
        for action in list(self.actions):
            self.actions_layout.removeWidget(action)
            action.setParent(None)
            action.deleteLater()
        self.actions = []
        self._update_controls()

    def required_actions(self):
        """本回合应有的行动数：队伍 ≥3 人时为 3，否则为队伍人数。"""
        active = len(self.owner._active_slots())
        if active <= 0:
            return 1
        return min(MAX_ACTIONS_PER_TURN, active)

    def min_actions(self):
        """本回合最少行动数。"""
        if self.turn_type() == "追加回合":
            return 1          # 追加回合可自由增删，至少保留 1 条
        return self.required_actions()

    def max_actions(self):
        """本回合最多行动数。"""
        if self.turn_type() == "追加回合":
            return MAX_ACTIONS_PER_TURN
        return self.required_actions()

    def ensure_action_count(self):
        """保证回合行动数符合要求。

        普通/切换回合 ≥3 人时固定 3 人；追加回合可自由增删（1~3）。
        """
        while len(self.actions) > self.max_actions():
            self._force_remove(self.actions[-1])
        while len(self.actions) < self.min_actions():
            if self.add_action() is None:
                break
        self.refresh_member_options()
        self._update_controls()

    def available_member_slots(self):
        """本回合可选的角色位置。

        追加回合只能由「上一个普通回合的前锋」行动。
        """
        if self.turn_type() == "追加回合":
            return self.owner.front_members_before(self)
        return self.owner._active_slots()

    def _first_free_member(self):
        used = self.used_members()
        for i in self.available_member_slots():
            if i not in used:
                return i
        allowed = self.available_member_slots()
        return allowed[0] if allowed else 0

    def refresh_member_options(self, except_action=None):
        for action in self.actions:
            if action is not except_action:
                action._populate_members()

    def add_action(self, data=None):
        if len(self.actions) >= MAX_ACTIONS_PER_TURN:
            return None
        action = ActionRow(self.owner, turn=self, data=data,
                           default_member=self._first_free_member())
        action.changed.connect(self._on_action_changed)
        action.delete_requested.connect(self._delete_action)
        self.actions.append(action)
        self.actions_layout.addWidget(action)
        if data is None:
            self.refresh_member_options(except_action=action)
        self._update_controls()
        self.changed.emit()
        return action

    def _force_remove(self, action):
        if action not in self.actions:
            return
        self.actions.remove(action)
        self.actions_layout.removeWidget(action)
        action.setParent(None)
        action.deleteLater()

    def _delete_action(self, action):
        if action not in self.actions:
            return
        if len(self.actions) <= self.min_actions():
            return  # 普通回合不可少于固定人数；追加回合至少保留 1 条
        self._force_remove(action)
        self.refresh_member_options()
        self._update_controls()
        self.changed.emit()

    def _on_action_changed(self):
        self.changed.emit()

    def _update_controls(self):
        self.add_action_button.setEnabled(len(self.actions) < self.max_actions())
        can_delete = len(self.actions) > self.min_actions()
        for action in self.actions:
            action.delete_button.setEnabled(can_delete)

    def _on_type_changed(self, text):
        is_switch = (text == "切换")
        with self._suspended():
            self.od_combo.setEnabled(not is_switch)
            if is_switch:
                self.od_combo.setCurrentText("无")
            for action in self.actions:
                action.setEnabled(not is_switch)
        self._apply_style()
        if not self._loading:
            self.refresh_member_options()   # 切换/追加回合的可选角色不同
            self.ensure_action_count()
            self.owner._reindex()           # 追加回合不计入回合数
        self.changed.emit()

    def _on_od_changed(self, text):
        self._apply_style()
        self.changed.emit()

    def mousePressEvent(self, event):
        self.turn_selected.emit(self)
        super().mousePressEvent(event)

    # ------------------------------------------------------------- helpers
    def turn_type(self):
        return self.type_combo.currentText()

    def od_level(self):
        """本回合发动的 OD 等级（0 表示未发动）。"""
        od = self.od_combo.currentText()
        if od.startswith("OD") and len(od) > 2 and od[2].isdigit():
            return int(od[2])
        return 0

    def set_index(self, index, additional=False):
        if additional:
            text = "追加回合" if index <= 0 else "第%d回合 追加" % index
            self.index_label.setText(text)
        else:
            self.index_label.setText("第%d回合" % index)

    def set_result(self, contribution, cumulative):
        self.result_label.setText("本回合 OD：%.2f" % contribution)
        self.cumulative_label.setText("累计：%.2f" % cumulative)

    def set_team_sp(self, entries):
        """显示本回合结束时全队的 SP。

        entries: [(slot_index, role_name, sp, is_front), ...]
        """
        if not entries:
            self.team_sp_label.setText("队伍SP：-")
            return
        parts = []
        for slot, role, sp, is_front in entries:
            pos = "前" if is_front else "后"
            parts.append("角色%d(%s) %s:%s" % (slot + 1, pos, role, sp))
        self.team_sp_label.setText("队伍SP　" + "　".join(parts))

    def _apply_style(self):
        od = self.od_combo.currentText()
        if self.turn_type() == "切换":
            self.setStyleSheet(TURN_CARD_STYLE % {
                "bg": "rgba(26, 26, 26, 0.9)", "accent": "#1a1a1a"})
            return
        bg = OD_COLORS.get(od[:3], "#ffffff")
        accent = "#c0c0c0"
        for key, color in OD_COLORS.items():
            if od.startswith(key):
                accent = color
                break
        self.setStyleSheet(TURN_CARD_STYLE % {"bg": bg, "accent": accent})

    def to_data(self):
        return {
            "type": self.turn_type(),
            "od": self.od_combo.currentText(),
            "actions": [a.to_data() for a in self.actions],
        }

    def set_data(self, data):
        with self._suspended():
            self.type_combo.setCurrentText(data.get("type", TURN_OPTIONS[0]))
            od = data.get("od", "无")
            if od in OD_OPTIONS:
                self.od_combo.setCurrentText(od)
            for action in list(self.actions):
                self.actions_layout.removeWidget(action)
                action.setParent(None)
                action.deleteLater()
            self.actions = []
            for action_data in data.get("actions", [])[:MAX_ACTIONS_PER_TURN]:
                action = ActionRow(self.owner, turn=self, data=action_data)
                action.changed.connect(self._on_action_changed)
                action.delete_requested.connect(self._delete_action)
                self.actions.append(action)
                self.actions_layout.addWidget(action)
        self._update_controls()
        if not self.actions:
            self.add_action()
        self._on_type_changed(self.type_combo.currentText())

    def refresh_team(self):
        self.ensure_action_count()
        for action in self.actions:
            action.refresh()

    def destroy(self):
        for action in list(self.actions):
            action.setParent(None)
            action.deleteLater()
        self.actions = []


# ======================================================================
# 主界面
# ======================================================================
class AxleODWindow(QFrame):
    """排轴 + OD 计算主界面。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_source = get_data_source()
        self.team = self._default_team()
        self.turns = []
        self.team_rows = []
        self.selected_turn = None
        self._team_updating = False
        self._build_ui()
        self._normalize_team()
        self.add_turn()

    def _default_team(self):
        roles = self.data_source.role_names()
        team = []
        for i in range(TEAM_SIZE):
            role = roles[i] if i < len(roles) else ""
            styles = self.data_source.styles_names(role) if role else []
            team.append({"role": role, "style": styles[0] if styles else ""})
        return team

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        # 统一本窗口下拉框配色，保证选中的文字清晰可辨
        self.setStyleSheet(COMBO_QSS)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        root.addLayout(self._build_toolbar())
        root.addWidget(self._build_team_group())
        root.addWidget(self._build_battle_group())
        root.addWidget(self._build_sp_group())
        root.addWidget(self._build_rows_area(), 1)
        root.addWidget(self._build_footer())

    def _build_toolbar(self):
        bar = QHBoxLayout()
        bar.setSpacing(6)
        buttons = [
            ("＋添加回合", self.add_turn),
            ("＋追加回合", self.add_additional_turn),
            ("删除选中回合", self.remove_selected_turn),
            ("上移", lambda: self.move_selected_turn(-1)),
            ("下移", lambda: self.move_selected_turn(1)),
            ("清空", self.clear_turns),
            ("保存", self.save_axle),
            ("读取", self.load_axle),
        ]
        for text, callback in buttons:
            button = QPushButton(text)
            button.setMinimumWidth(92)
            button.clicked.connect(callback)
            bar.addWidget(button)
        bar.addStretch(1)
        tip = QLabel("提示：队伍≥3人时每回合固定 3 人行动；点击回合选中")
        tip.setStyleSheet("color: #666666;")
        bar.addWidget(tip)
        return bar

    def _build_team_group(self):
        group = QGroupBox("队伍配置（6 人：前锋 3 人 / 后卫 3 人）")
        layout = QGridLayout(group)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(4)

        for i in range(TEAM_SIZE):
            row = TeamMemberRow(i + 1, self.data_source)
            row.set_data(self.team[i])
            row.changed.connect(self._on_team_changed)
            self.team_rows.append(row)
            layout.addWidget(row, i // 3, i % 3)
        return group

    def _build_battle_group(self):
        group = QGroupBox("全局战斗设置（OD计算）")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        layout.addWidget(QLabel("敌人数量"))
        self.target_spin = QSpinBox()
        self.target_spin.setRange(1, 10)
        self.target_spin.setValue(1)
        self.target_spin.setFixedWidth(60)
        self.target_spin.setToolTip("目标数 / 敌人数量，参与 HIT OD 计算")
        self.target_spin.valueChanged.connect(self.recalculate)
        layout.addWidget(self.target_spin)

        self.resistance_check = QCheckBox("抗性（命中无效）")
        self.resistance_check.setToolTip("勾选后 HIT OD 记 0")
        self.resistance_check.stateChanged.connect(self.recalculate)
        layout.addWidget(self.resistance_check)

        layout.addWidget(QLabel("其他OD增量"))
        self.other_od_spin = _make_double_spin(0.0, 100.0, 0.01, 3, 0.0)
        self.other_od_spin.setToolTip("计入总系数的额外 OD 增量")
        self.other_od_spin.valueChanged.connect(self.recalculate)
        layout.addWidget(self.other_od_spin)

        layout.addWidget(QLabel("敌方OD率"))
        self.enemy_od_spin = _make_double_spin(0.0, 10.0, 0.1, 2, 1.0)
        self.enemy_od_spin.setToolTip("敌方 OD 率倍率（默认 1.0）")
        self.enemy_od_spin.valueChanged.connect(self.recalculate)
        layout.addWidget(self.enemy_od_spin)

        layout.addStretch(1)

        self.total_label = QLabel("总OD：0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 15px;")
        layout.addWidget(self.total_label)

        self.percent_label = QLabel("实际OD：0.0000")
        layout.addWidget(self.percent_label)

        self.actual_hits_label = QLabel("实际Hit数：0.000")
        layout.addWidget(self.actual_hits_label)
        return group

    def _build_sp_group(self):
        group = QGroupBox("SP 设置")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        layout.addWidget(QLabel("初始SP"))
        self.sp_init_spin = QSpinBox()
        self.sp_init_spin.setRange(0, 20)
        self.sp_init_spin.setValue(4)
        self.sp_init_spin.setFixedWidth(56)
        self.sp_init_spin.setToolTip("全队初始 SP（默认 4）")
        self.sp_init_spin.valueChanged.connect(self.recalculate)
        layout.addWidget(self.sp_init_spin)

        layout.addWidget(QLabel("前锋回复"))
        self.sp_regen_front_spin = QSpinBox()
        self.sp_regen_front_spin.setRange(0, 20)
        self.sp_regen_front_spin.setValue(3)
        self.sp_regen_front_spin.setFixedWidth(56)
        self.sp_regen_front_spin.setToolTip("每回合开始时前锋（角色1~3）回复的 SP")
        self.sp_regen_front_spin.valueChanged.connect(self.recalculate)
        layout.addWidget(self.sp_regen_front_spin)

        layout.addWidget(QLabel("后卫回复"))
        self.sp_regen_back_spin = QSpinBox()
        self.sp_regen_back_spin.setRange(0, 20)
        self.sp_regen_back_spin.setValue(2)
        self.sp_regen_back_spin.setFixedWidth(56)
        self.sp_regen_back_spin.setToolTip("每回合开始时后卫（角色4~6）回复的 SP")
        self.sp_regen_back_spin.valueChanged.connect(self.recalculate)
        layout.addWidget(self.sp_regen_back_spin)

        layout.addWidget(QLabel("SP上限"))
        self.sp_limit_spin = QSpinBox()
        self.sp_limit_spin.setRange(1, 99)
        self.sp_limit_spin.setValue(20)
        self.sp_limit_spin.setFixedWidth(56)
        self.sp_limit_spin.setToolTip("SP 上限（参考 hbr-tool 默认 20）")
        self.sp_limit_spin.valueChanged.connect(self.recalculate)
        layout.addWidget(self.sp_limit_spin)

        layout.addStretch(1)

        note = QLabel("前锋 +3 / 后卫 +2；OD 额外 +5/+12/+20（首回合按队伍配置）")
        note.setStyleSheet("color: #777777; font-size: 12px;")
        layout.addWidget(note)
        return group

    def _build_rows_area(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.turns_container = QWidget()
        self.turns_layout = QVBoxLayout(self.turns_container)
        self.turns_layout.setContentsMargins(0, 0, 0, 0)
        self.turns_layout.setSpacing(6)
        self.turns_layout.addStretch(1)
        scroll.setWidget(self.turns_container)
        return scroll

    def _build_footer(self):
        label = QLabel(
            "OD公式来自「等效破坏率与OD计算表」："
            "耳环系数 = 1+(5+MIN(原始Hit,10)×10/9−10/9)/100×OD耳环；"
            "HIT OD = (原始Hit+连击数) × ROUNDDOWN(2.5×总系数×敌方OD率,2) × 敌人数量 × (抗性?0:1)；"
            "固定OD = ROUNDDOWN(固定OD×100×总系数,2) + ROUNDDOWN(31X共鸣×100×总系数,2)；"
            "总系数 = 耳环系数 + 其他OD增量。通常攻击不享受 OD 耳环加成。\n"
            "SP：第1回合按队伍配置顺序（前 3 人为前锋），其后以「上一回合行动的队员」为前锋；"
            "回合开始前锋 +3、后卫 +2（上限默认 20）；"
            "发动 OD 额外获得 OD1 +5 / OD2 +12 / OD3 +20；行动扣除技能 SP"
            "（「剩余SP」列红色表示不足；技能自带的 SP 回复会自动结算；"
            "勾选行动的「破」表示该行动击破敌人，会触发「击破时回复SP」的技能/被动）。"
            "队伍≥3人时每回合固定 3 人行动；新增回合会自动沿用上一回合行动的队员；"
            "追加回合不计回合数、不触发回合开始回复，但行动消耗与技能 SP 回复照常生效；"
            "每个回合下方显示全队 SP（含未行动的后卫）。"
        )
        label.setWordWrap(True)
        label.setStyleSheet("color: #777777; font-size: 12px;")
        return label

    # ------------------------------------------------------------- team ops
    def _normalize_team(self):
        """后卫存在的必要条件是前锋有 3 人。"""
        front_full = all(self.team_rows[i].role() for i in range(3))
        for i in range(3, TEAM_SIZE):
            row = self.team_rows[i]
            if not front_full and row.role():
                row.set_role("无")
            row.set_slot_enabled(front_full)

    def _on_team_changed(self):
        if self._team_updating:
            return
        self._team_updating = True
        try:
            self._normalize_team()
            self.team = [row.to_data() for row in self.team_rows]
        finally:
            self._team_updating = False
        for turn in self.turns:
            turn.refresh_team()
        self.recalculate()

    # ------------------------------------------------------------- turn ops
    def _last_front_actors(self, exclude=None):
        """最近一个有效回合的行动队员（跳过切换/追加回合）。"""
        for turn in reversed(self.turns):
            if turn is exclude:
                continue
            actors = turn.actor_members()
            if actors:
                return actors
        return []

    def front_members_before(self, turn):
        """指定回合之前（不含自身）最近一个普通回合的前锋队员。"""
        try:
            idx = self.turns.index(turn)
        except ValueError:
            idx = len(self.turns)
        for prev in reversed(self.turns[:idx]):
            actors = prev.actor_members()
            if actors:
                return actors
        return self._initial_front()

    def add_turn(self, data=None, turn_type=None):
        turn = TurnCard(self)
        turn.changed.connect(self.recalculate)
        turn.delete_requested.connect(self._delete_turn)
        turn.turn_selected.connect(self._select_turn)
        self.turns.append(turn)
        self.turns_layout.insertWidget(len(self.turns) - 1, turn)
        if data:
            turn.set_data(data)
            turn.ensure_action_count()
        else:
            # 新回合沿用上一回合(最近有效回合)行动的队员，不足则用队伍前几人补齐
            actors = self._last_front_actors(exclude=turn)
            required = turn.required_actions()
            members = []
            for member in actors:
                if member not in members:
                    members.append(member)
            for member in self._active_slots():
                if len(members) >= required:
                    break
                if member not in members:
                    members.append(member)
            turn.clear_actions()
            for member in members[:required]:
                turn.add_action({"member": member})
            turn.refresh_member_options()
        if turn_type:
            turn.type_combo.setCurrentText(turn_type)
        self._reindex()
        self._select_turn(turn)
        self.recalculate()
        return turn

    def add_additional_turn(self):
        """添加「追加回合」：不计回合数、不影响 SP。"""
        return self.add_turn(turn_type="追加回合")

    def _delete_turn(self, turn):
        if turn not in self.turns:
            return
        self.turns.remove(turn)
        self.turns_layout.removeWidget(turn)
        turn.destroy()
        turn.setParent(None)
        turn.deleteLater()
        if self.selected_turn is turn:
            self.selected_turn = None
        if not self.turns:
            self.add_turn()
            return
        self._reindex()
        self.recalculate()

    def remove_selected_turn(self):
        if self.selected_turn is not None:
            self._delete_turn(self.selected_turn)
        else:
            QMessageBox.information(self, "提示", "请先点击选择一个回合")

    def move_selected_turn(self, offset):
        turn = self.selected_turn
        if turn is None:
            QMessageBox.information(self, "提示", "请先点击选择一个回合")
            return
        index = self.turns.index(turn)
        new_index = index + offset
        if new_index < 0 or new_index >= len(self.turns):
            return
        self.turns.insert(new_index, self.turns.pop(index))
        for widget in self.turns:
            self.turns_layout.removeWidget(widget)
        for i, widget in enumerate(self.turns):
            self.turns_layout.insertWidget(i, widget)
        self._reindex()
        self.recalculate()

    def clear_turns(self):
        for turn in list(self.turns):
            self.turns_layout.removeWidget(turn)
            turn.destroy()
            turn.setParent(None)
            turn.deleteLater()
        self.turns = []
        self.selected_turn = None
        self.add_turn()

    def _select_turn(self, turn):
        self.selected_turn = turn
        for item in self.turns:
            if item is turn:
                item.index_label.setStyleSheet(
                    "background-color: #0078d4; color: white;"
                    "border-radius: 3px; font-weight: bold;")
            else:
                item.index_label.setStyleSheet("")

    def _reindex(self):
        """重新编号：追加回合不计入回合数。"""
        number = 0
        for turn in self.turns:
            if turn.turn_type() == "追加回合":
                turn.set_index(number, additional=True)
            else:
                number += 1
                turn.set_index(number)

    # --------------------------------------------------------- calculation
    def _battle_params(self):
        return ODBattle(
            target_count=self.target_spin.value(),
            resistance=self.resistance_check.isChecked(),
            other_od=self.other_od_spin.value(),
            enemy_od_rate=self.enemy_od_spin.value(),
        )

    def recalculate(self):
        battle = self._battle_params()
        cumulative = 0.0
        for turn in self.turns:
            contribution = 0.0
            if turn.turn_type() != "切换":
                for action in turn.actions:
                    value = calc_od(action.get_od_skill(), battle).total_od
                    action.set_result(value)
                    contribution += value
            else:
                for action in turn.actions:
                    action.set_result(0.0)
            cumulative += contribution
            turn.set_result(contribution, cumulative)

        self.total_label.setText("总OD：%.2f" % cumulative)
        self.percent_label.setText("实际OD：%.4f" % (cumulative / 100.0))
        self.actual_hits_label.setText(
            "实际Hit数：%.3f" % (cumulative / 100.0 * 40.0))

        self._recalc_sp()

    def _active_slots(self):
        """队伍中已安排角色的位置下标。"""
        return [i for i in range(len(self.team)) if self.team[i].get("role")]

    def _initial_front(self):
        """初始前锋：队伍中前 3 个已安排角色的位置。"""
        return self._active_slots()[:3]

    def _recalc_sp(self):
        """模拟全队 SP。

        * 第 1 回合开始时，前锋/后卫按队伍配置顺序（前 3 人为前锋）。
        * 每回合开始按「上一回合结束时」的前锋/后卫回复 SP：
          前锋 +3、后卫 +2。
        * 回合结束后，本回合行动的队员成为新的前锋（沿用上一回合前锋补齐）。
        * 行动扣费，发动 OD 额外回复。
        """
        limit = self.sp_limit_spin.value()
        front_regen = self.sp_regen_front_spin.value()
        back_regen = self.sp_regen_back_spin.value()
        count = max(len(self.team), 1)
        active = self._active_slots()

        sp = [self.sp_init_spin.value()] * count
        # 第 1 回合开始时的前锋 = 队伍配置顺序的前 3 人
        front = self._initial_front()
        break_seen = False   # 是否已经发生过击破（用于「首次击破」类被动）

        for turn in self.turns:
            # 追加回合不计回合数：不触发「回合开始回复」与 OD 回复，
            # 但行动仍然消耗 SP、技能回复 SP 也照常生效。
            is_additional = turn.turn_type() == "追加回合"
            front_set = set(front)

            if not is_additional:
                # 回合开始回复（前锋 +front，后卫 +back）
                for i in active:
                    regen = front_regen if i in front_set else back_regen
                    if sp[i] < limit:
                        sp[i] = min(limit, sp[i] + regen)

                # 发动 OD 的额外 SP
                level = turn.od_level()
                if 1 <= level < len(OD_SP_BONUS):
                    bonus = OD_SP_BONUS[level]
                    for i in active:
                        sp[i] = min(99, sp[i] + bonus)

            # 行动：扣除技能 SP，并结算技能的 SP 回复效果
            if turn.turn_type() == "切换":
                for action in turn.actions:
                    action.set_sp_result(None)
            else:
                for action in turn.actions:
                    i = action.member_index
                    if i not in active:
                        action.set_sp_result(None)
                        continue
                    cost = action.get_sp_cost()
                    if cost >= 99:      # 消耗全部 SP
                        cost = sp[i]
                    enough = sp[i] >= cost
                    if enough:
                        sp[i] -= cost
                        self._apply_sp_recover(action, i, sp, active,
                                               front_set, limit)
                        if action.is_break():
                            self._apply_break_recover(
                                action, i, sp, active, front_set, limit,
                                not break_seen)
                            break_seen = True
                    action.set_sp_result(sp[i], enough)

            # 记录本回合结束时全队 SP（含后卫）
            entries = [(i, self.team[i].get("role"), sp[i], i in front_set)
                       for i in active]
            turn.set_team_sp(entries)

            # 追加回合不改变前锋
            if is_additional:
                continue

            # 回合结束：本回合行动的队员成为新的前锋
            actors = turn.actor_members()
            if actors:
                merged = list(actors)
                for m in front:
                    if len(merged) >= 3:
                        break
                    if m not in merged:
                        merged.append(m)
                for m in active:
                    if len(merged) >= 3:
                        break
                    if m not in merged:
                        merged.append(m)
                front = merged[:3]

    def _member_element(self, slot):
        """队员所装备风格的元素属性。"""
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        for st in self.data_source.styles(role):
            if st.name == style:
                return st.element
        return None

    def _apply_scope_recover(self, amount, scope, element, actor,
                             sp, active, front_set, limit):
        """按范围结算一次 SP 回复。"""
        if amount <= 0 or not scope:
            return
        if scope == "self":
            targets = [actor]
        elif scope == "all":
            # 全体友方：包含自身
            targets = list(active)
        elif scope == "others":
            # 全体其他友方：除自身外的所有友方
            targets = [i for i in active if i != actor]
        elif scope == "front":
            # 前锋：包含自身
            targets = [i for i in active if i in front_set]
        elif scope == "front_others":
            # 前锋其他友方：前锋中除自身外
            targets = [i for i in active if i in front_set and i != actor]
        elif scope == "others_element":
            # 全体其他{X}属性风格：除自身外该元素（含双属性）的友方
            targets = [i for i in active
                       if i != actor and element
                       and element in (self._member_element(i) or "")]
        elif scope == "all_element":
            # 全体{X}属性风格：含自身该元素（含双属性）的友方
            targets = [i for i in active
                       if element and element in (self._member_element(i) or "")]
        else:
            return
        for t in targets:
            if sp[t] < limit:
                sp[t] = min(limit, sp[t] + amount)

    def _apply_sp_recover(self, action, actor, sp, active, front_set, limit):
        """结算技能自带的 SP 回复效果。"""
        amount, scope, element = action.get_sp_recover()
        self._apply_scope_recover(amount, scope, element, actor,
                                  sp, active, front_set, limit)

    def _member_break_sp(self, slot):
        """队员所装备风格里「击破敌人时回复SP」的被动。"""
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        for st in self.data_source.styles(role):
            if st.name == style:
                return st.break_sp
        return []

    def _apply_break_recover(self, action, actor, sp, active, front_set,
                             limit, is_first_break):
        """结算「击破敌人」触发的 SP 回复（技能 + 装备风格被动）。"""
        amount, scope = action.get_break_skill_recover()
        self._apply_scope_recover(amount, scope, None, actor,
                                  sp, active, front_set, limit)
        for eff in self._member_break_sp(actor):
            if eff.get("first_only") and not is_first_break:
                continue
            self._apply_scope_recover(eff.get("amount", 0), eff.get("scope"),
                                      None, actor, sp, active, front_set, limit)

    # ------------------------------------------------------------ file I/O
    def to_dict(self):
        return {
            "version": 2,
            "team": [row.to_data() for row in self.team_rows],
            "battle": {
                "target_count": self.target_spin.value(),
                "resistance": self.resistance_check.isChecked(),
                "other_od": self.other_od_spin.value(),
                "enemy_od_rate": self.enemy_od_spin.value(),
                "sp_init": self.sp_init_spin.value(),
                "sp_regen_front": self.sp_regen_front_spin.value(),
                "sp_regen_back": self.sp_regen_back_spin.value(),
                "sp_limit": self.sp_limit_spin.value(),
            },
            "turns": [turn.to_data() for turn in self.turns],
        }

    def from_dict(self, data):
        if not isinstance(data, dict):
            return False

        team = data.get("team") or []
        self._team_updating = True
        try:
            for i, row in enumerate(self.team_rows):
                if i < len(team):
                    row.set_data(team[i])
        finally:
            self._team_updating = False
        self._on_team_changed()

        battle = data.get("battle", {}) or {}
        self.target_spin.setValue(int(battle.get("target_count", 1)))
        self.resistance_check.setChecked(bool(battle.get("resistance", False)))
        self.other_od_spin.setValue(float(battle.get("other_od", 0)))
        self.enemy_od_spin.setValue(float(battle.get("enemy_od_rate", 1)))
        self.sp_init_spin.setValue(int(battle.get("sp_init", 4)))
        self.sp_regen_front_spin.setValue(
            int(battle.get("sp_regen_front", battle.get("sp_regen", 3))))
        self.sp_regen_back_spin.setValue(
            int(battle.get("sp_regen_back", battle.get("sp_regen", 2))))
        self.sp_limit_spin.setValue(int(battle.get("sp_limit", 20)))

        turns = data.get("turns", [])
        if not turns:
            return False

        for turn in list(self.turns):
            self.turns_layout.removeWidget(turn)
            turn.destroy()
            turn.setParent(None)
            turn.deleteLater()
        self.turns = []
        self.selected_turn = None
        for turn_data in turns:
            self.add_turn(turn_data)
        self._reindex()
        self.recalculate()
        return True

    def save_axle(self):
        if not self.turns:
            QMessageBox.information(self, "提示", "排轴为空，无需保存")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "保存排轴", os.path.abspath(DEFAULT_SAVE_PATH),
            "JSON 文件 (*.json)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "提示", "排轴已保存")
        except Exception as e:
            logger.error("保存排轴失败: %s", e)
            QMessageBox.warning(self, "错误", "保存失败：%s" % e)

    def load_axle(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "读取排轴", os.path.abspath(DEFAULT_SAVE_PATH),
            "JSON 文件 (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error("读取排轴失败: %s", e)
            QMessageBox.warning(self, "错误", "读取失败：%s" % e)
            return
        if not self.from_dict(data):
            QMessageBox.information(self, "提示", "文件中没有排轴数据")

    # -------------------------------------------------------------- close
    def destroy(self):
        for turn in list(self.turns):
            turn.destroy()
            turn.setParent(None)
            turn.deleteLater()
        self.turns = []


def creat_axle_od_win():
    if is_win_open(WINDOW_TITLE, MODULE_NAME):
        win_set_top(WINDOW_TITLE, MODULE_NAME)
        return "break"

    win_frame = creat_Toplevel(WINDOW_TITLE, 1200, 820, 160, 60)
    set_window_icon(win_frame, "./工具/help.png")

    view = AxleODWindow(win_frame.centralWidget())
    win_frame.grid_layout.addWidget(view, 0, 0)
    win_frame.grid_layout.setRowStretch(0, 1)
    win_frame.grid_layout.setColumnStretch(0, 1)

    win_open_manage(win_frame, MODULE_NAME)

    def on_close(self, event):
        win_close_manage(win_frame, MODULE_NAME, view)
        event.accept()

    win_frame.closeEvent = types.MethodType(on_close, win_frame)

    return "break"
