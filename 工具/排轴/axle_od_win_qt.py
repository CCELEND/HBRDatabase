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
    * SP：参考 https://www.hbr-tool.com/#/simulator 模拟每名队员的 SP。
      回合开始按「回合开始时的前锋」回复（第 1 回合 = 队伍配置前 3 人，
      之后 = 上一回合行动的队员）：前锋 +3 / 后卫 +2（上限默认 20）；
      技能/被动里的「前锋」回复范围按本回合行动的队员结算；
      行动扣除技能 SP，发动 OD 额外获得 OD1 +5 / OD2 +12 / OD3 +20，
      并显示每行动的剩余 SP。
"""

import os
import json
import types
from contextlib import contextmanager

from PyQt5.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QHBoxLayout, QVBoxLayout, QGridLayout,
    QScrollArea, QFileDialog, QMessageBox, QGroupBox, QSizePolicy,
    QToolButton, QMenu
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
HELP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "help.txt")

HELP_TEXT = """排轴OD计算 使用说明
========================================

【排轴】
- 一个队伍 6 人（前锋 3 / 后卫 3）；队伍配置可选 角色、风格、携带被动、突破数、
  31X共鸣、OD耳环；角色不可重复（已选的角色在其它位置会置灰不可选）。
  31X共鸣 / OD耳环 按角色设置（31X共鸣仅在勾选「击破敌人」的行动中生效；
  OD耳环对该角色所有回合生效）。
- 队伍≥3人时每回合固定 3 人行动；同一回合内队员不重复。
- 追加回合不计回合数、不触发回合开始回复，也不能发动 OD。
- 新增回合会自动沿用上一回合行动的队员；修改上一回合前锋会同步后续（未手动编辑的）回合。
- 技能：同角色各风格技能通用；但 SSR/SS 的第一个主动技能为专属（仅装备该风格时可用）。
  已通用化的例外：第一个 SS 风格的专属技能（如 幻象泡影）、星火燎原+。
- 「（被动技能）」在队伍配置里选择携带（默认全部），选中后全程（所有回合）生效。
- 同一风格的不同形态（如 CODE:Virtual Killer / CODE:Virtual Killer2）共享技能与被动，可自由选择。
- 所有角色共有的通用技能：「点数援助」（自身 SP+3，消耗 SP1）、
  「驱动增益」（超频条 +15%，消耗 SP6）。两者均为「每次出击1次」，但排轴暂不限制使用次数。
- 击破：勾选行动的「击破敌人」表示该行动击破敌人，触发「击破时回复 SP」的技能/被动。
- 「单名友方回复SP」的技能（如 日常维护）：行动行的「对象」下拉框选择回复对象
  （「其他友方」类的对象不含自身）；其它技能该列显示「—」。

【OD 公式】来自「等效破坏率与OD计算表」
- 耳环系数 = 1 + (5 + MIN(原始Hit,10)×10/9 − 10/9)/100 × OD耳环
- HIT OD = (原始Hit + 连击数) × ROUNDDOWN(2.5×总系数×敌方OD率, 2) × 敌人数量 × (抗性?0:1)
- 固定OD = ROUNDDOWN(固定OD×100×总系数, 2) + ROUNDDOWN(31X共鸣×100×总系数, 2)
- 总系数 = 耳环系数 + 其他OD增量
- 通常攻击不享受 OD 耳环加成；通常攻击视为「无属性」。
- 抗性可按属性勾选（含「无」）：行动的攻击元素（技能元素 → 角色风格元素 → 无）被抗性时，
  该次 HIT OD 记 0。
- 「OD条下降 X%」为该次行动 OD 的固定扣减（如 50% → −50，可为负）。
- 风格被动「OD条上升」（如 V字回复）：「回合开始时」每回合结算、「战斗开始时」仅第 1 回合；
  按「位于前锋/后卫」判定位置；「超频条不足N%」为触发阈值；「出击中1次」整场只触发一次；
  均为「直接增加超频条」，收益为固定值（不吃 OD 耳环加成）；也需满足突破数。
  「回合开始时」类在 **OD 回合（含其加成回合）与追加回合**中不结算。
- 「击破敌人时超频条+X%」类（如 托付给你了 / 势如破竹）：勾选行动的「击破敌人」**且该行动是攻击**时，
  自动同步到该行动的**固定OD**输入框（X% → X/100，如 25% → 0.250），
  因此会吃到 OD 耳环加成；取消勾选会自动移除（手填值保留）。
- 技能的「OD条上升 X%」效果：**攻击技能**（带伤害 Hit，如 无限光晕）→ 自动同步到**固定OD**
  （吃 OD 耳环加成）；**非攻击技能**（如 威严号令）→ 作为**直接增加超频条 +X**，不吃耳环。
  若限定「以此技能击破敌人时」（如 原子火焰 / 哀伤的雪花莲），则仅在勾选击破敌人时计入。
  例外：**驱动增益**虽非攻击技能，但实测也会吃 OD 耳环，故同按固定OD结算。
  换其它技能时会自动移除。
- 概率类被动（如福运 70%）按必定触发计算；
  无法判定的条件（干劲/领域/解除BUFF/EX/SP提升等）不计入。

【OD 发动与回合数】
- 前置OD：当前回合直接发动；后置OD：当前回合结束马上发动（两者 OD 回合都是当前回合）。
- 后置OD 的回合沿用上一个回合号（显示「第N回合 后置OD」），不计入回合数。
- 发动消耗 OD 槽 = 等级×100（OD1=100 / OD2=200 / OD3=300）；
  同一次发动只扣一次（连续相同 OD 等级的回合，如 OD2 / OD2/Bonus1 / OD2/Bonus2 视为同一次）。
- 每回合显示：「回合开始OD」（= 上一回合结束OD + 回合开始被动 − 发动OD消耗）、
  「本回合OD」（仅本回合行动产生的 OD）、「当前OD」= 回合开始OD + 本回合OD；
  汇总的「净OD」即最后一个回合的当前OD。

【SP】
- 第 1 回合前锋 = 队伍配置前 3 人；之后 = 上一回合行动的队员。
- 回合开始：基础回复（前锋/后卫）+ 风格被动的前锋SP（闪光/佳音/机敏/俊敏…，需满足突破数）；
  以及「回合开始时回复友方SP」的被动（如 与伙伴一起【朝仓可怜专属】：除自身外全体友方 SP+1）。
- 后置OD 属上一回合：不触发回合开始回复与闪光，仅结算 OD 额外 SP（同一次发动只给一次）。
- 发动 OD 额外获得 OD1 +5 / OD2 +12 / OD3 +20（同一次发动只给一次）。
- 技能/被动里的「前锋」回复范围按本回合行动的队员结算。
- 行动扣除技能 SP；被动/大师技能对 SP 消耗的增减会自动结算
  （同种效果只生效一次：降低取最大降幅、增加取最大增幅，两者相抵；
  且 SP 消耗为 0 的技能不受任何增减影响）；「剩余SP」列红色负值表示不足（缺口，实际 SP 不变）。
- 「红宝石香水（被动技能）」启用「高阶增强」（SP消耗 +2、SP上限 30），仅在携带该被动时生效；
  它只作用于消耗 SP 的技能，通常攻击与 SP 消耗为 0 的技能不受影响。
- 部分技能带「N(M)」式条件消耗：当敌人处于**倒地/超倒地**状态（本场已发生击破）时，
  改用较小值（如 对称·启示 0(16)：未倒地消耗 16、击破敌人后消耗 0）。
- 每回合下方显示两行全队 SP（含未行动的后卫）：
  「队伍SP（行动前）」（回合开始回复 / OD 结算之后、行动之前）与
  「队伍SP（行动后）」（本回合结算结束时）。
- 「大师技能」作为可携带被动出现在队伍配置的「被动」菜单里（默认携带），
  其中影响 SP 消耗的效果会结算（如 大岛一千子「彩凤连理」：全体31E友方 消耗SP-1；
  丸山奏多「丸山部队！出发！」：指定几名角色 消耗SP-1）。按队伍/角色名匹配，假设已解放。
- 可**主动释放**的大师技能（如 逢川惠「灵能充能」：单体友方 SP+3、对象为 31A 再 +3）
  会作为该角色的可选技能出现（消耗按 0 计）。
- SP 上限默认 20；若风格有「SP上限变为 N」则自动取较大者（界面显示「（自动 N）」）。
- 需「状态/加护/领域/印/信念/士气/DP/EX 等」才能判定的 SP 被动暂不计入（避免多算）；
  可判定的条件会结算：「战斗开始时」类仅第 1 回合、「位于前锋/后卫」按回合开始时的前锋、
  「SP不大于N」按当前 SP、「超频条不足N%」按回合开始时的超频条、
  「存在被击破的敌人」（含 SP 消耗增减类，如 算法 / 最佳位置）按是否已发生击破。
"""


def write_help_file():
    """把使用说明输出到 工具/排轴/help.txt。"""
    try:
        with open(HELP_FILE, "w", encoding="utf-8") as f:
            f.write(HELP_TEXT)
    except Exception as e:
        logger.error("写入 help.txt 失败: %s", e)

TEAM_SIZE = 6
MAX_ACTIONS_PER_TURN = 3
TURN_OPTIONS = ["通常回合", "追加回合"]

# 与参考站点一致的 OD 选项
# 敌人可抗性的属性
ELEMENTS = ["火", "冰", "雷", "光", "暗", "无"]

# OD 发动时机：前置=当前回合直接发动；后置=当前回合结束马上发动
OD_TIMING_OPTIONS = ["前置OD", "后置OD"]
# 每级 OD 消耗的 OD 槽
OD_GAUGE_PER_LEVEL = 100

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
MEMBER_W, SKILL_W, TARGET_W = 150, 200, 96
HIT_W, COMBO_W = 58, 58
FIXED_W, RES_W, EARRING_W = 72, 72, 72
BREAK_W, SP_W, RESULT_W = 96, 62, 66
DEL_W = 26
ACTION_COLUMNS = [
    ("角色", MEMBER_W), ("行动", SKILL_W), ("对象", TARGET_W),
    ("原始Hit", HIT_W), ("连击", COMBO_W), ("固定OD", FIXED_W),
    ("击破敌人", BREAK_W), ("剩余SP", SP_W), ("该次OD", RESULT_W), ("", DEL_W),
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
#passiveButton {
    color: #222222;
    background-color: #ffffff;
    border: 1px solid #c8c8c8;
    border-radius: 3px;
    padding: 1px 16px 1px 6px;
    text-align: left;
}
#passiveButton:hover {
    background-color: #eef3fb;
}
#passiveButton:disabled {
    color: #999999;
    background-color: #f0f0f0;
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
        self.style_combo.setFixedWidth(190)
        self.style_combo.currentTextChanged.connect(self._on_style_changed)
        self.style_combo.currentTextChanged.connect(
            lambda text: self.style_combo.setToolTip(text))
        layout.addWidget(self.style_combo)

        # 「（被动技能）」选择：配置时携带，之后所有回合都生效
        self.passive_button = QToolButton()
        self.passive_button.setObjectName("passiveButton")
        self.passive_button.setText("被动")
        self.passive_button.setPopupMode(QToolButton.InstantPopup)
        self.passive_button.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.passive_button.setFixedWidth(64)
        self.passive_button.setToolTip("选择该风格携带的被动技能（默认全部携带）")
        self.passive_menu = QMenu(self.passive_button)
        self.passive_button.setMenu(self.passive_menu)
        layout.addWidget(self.passive_button)

        lb_label = QLabel("突破")
        lb_label.setFixedWidth(30)
        layout.addWidget(lb_label)
        self.lb_spin = QSpinBox()
        self.lb_spin.setRange(0, 4)
        self.lb_spin.setValue(4)   # 默认满突破（被动全生效），可下调
        self.lb_spin.setFixedWidth(46)
        self.lb_spin.setToolTip("风格突破数（0~4），部分被动需达到要求才生效（如闪光需突破 1）")
        self.lb_spin.valueChanged.connect(self._emit_changed)
        layout.addWidget(self.lb_spin)

        res_label = QLabel("31X共鸣")
        res_label.setFixedWidth(52)
        layout.addWidget(res_label)
        self.resonance_spin = _make_double_spin(0.0, 100.0, 0.01, 2, 0.0, 56)
        self.resonance_spin.setToolTip(
            "该角色的 31X 共鸣（仅在勾选「击破敌人」的行动中生效）")
        self.resonance_spin.valueChanged.connect(self._emit_changed)
        layout.addWidget(self.resonance_spin)

        ear_label = QLabel("OD耳环")
        ear_label.setFixedWidth(48)
        layout.addWidget(ear_label)
        self.earring_spin = _make_double_spin(0.0, 10.0, 1.0, 2, 1.0, 56)
        self.earring_spin.setToolTip(
            "该角色的 OD 耳环（对所有回合生效；通常攻击不享受）")
        self.earring_spin.valueChanged.connect(self._emit_changed)
        layout.addWidget(self.earring_spin)

        self._selected_passives = None   # None = 全部携带

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
        self._selected_passives = None   # 换角色后默认携带全部被动
        self._populate_styles(preserve="")
        self._emit_changed()

    def set_roles_enabled(self, used, my_index):
        """队伍角色不可重复：禁用其它位置已选的角色。

        used: {role_name: [slot_index, ...]}
        """
        model = self.role_combo.model()
        for j in range(self.role_combo.count()):
            role = self.role_combo.itemText(j)
            if not role or role == "无":
                continue
            taken = any(idx != my_index for idx in used.get(role, []))
            item = model.item(j)
            if item is not None:
                item.setEnabled(not taken)

    def _on_style_changed(self, style):
        if self._loading:
            return
        self._selected_passives = None   # 换风格后默认携带全部被动
        self._populate_passives()
        self._emit_changed()

    def _style_info(self):
        role = self.role()
        style = self.style()
        for st in self.data_source.styles(role):
            if st.name == style:
                return st
        return None

    def _populate_passives(self):
        self.passive_menu.clear()
        style_info = self._style_info()
        options = style_info.passive_options if style_info else []
        if not options:
            action = self.passive_menu.addAction("（无）")
            action.setEnabled(False)
            self.passive_button.setToolTip("该风格没有可携带的被动技能")
            return
        for name in options:
            action = self.passive_menu.addAction(name)
            action.setCheckable(True)
            action.setChecked(self._selected_passives is None
                              or name in self._selected_passives)
            action.toggled.connect(
                lambda checked, n=name: self._on_passive_toggled(n, checked))
        self.passive_button.setToolTip(
            "已携带：%s（点击选择）" % "、".join(self.selected_passives()))

    def selected_passives(self):
        style_info = self._style_info()
        options = style_info.passive_options if style_info else []
        if self._selected_passives is None:
            return list(options)
        return [n for n in options if n in self._selected_passives]

    def _on_passive_toggled(self, name, checked):
        if self._loading:
            return
        style_info = self._style_info()
        options = style_info.passive_options if style_info else []
        if self._selected_passives is None:
            self._selected_passives = set(options)
        if checked:
            self._selected_passives.add(name)
        else:
            self._selected_passives.discard(name)
        self.passive_button.setToolTip(
            "已携带：%s（点击选择）" % "、".join(self.selected_passives()))
        self.changed.emit()

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
        self._populate_passives()

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
        return {"role": self.role(), "style": self.style(),
                "passives": self.selected_passives(),
                "lb": self.lb_spin.value(),
                "resonance_31x": self.resonance_spin.value(),
                "od_earring": self.earring_spin.value()}

    def set_data(self, data):
        with self._suspended():
            if "passives" in data:
                self._selected_passives = set(data.get("passives") or [])
            else:
                self._selected_passives = None
            if "lb" in data:
                self.lb_spin.setValue(int(data.get("lb") or 0))
            self.resonance_spin.setValue(
                float(data.get("resonance_31x", 0) or 0))
            self.earring_spin.setValue(float(data.get("od_earring", 1) or 0))
            role = data.get("role", "")
            self.role_combo.setCurrentText(role if role else "无")
            self._populate_styles(preserve=data.get("style", ""))
            style = data.get("style", "")
            pos = self.style_combo.findData(style) if style else -1
            if pos >= 0:
                self.style_combo.setCurrentIndex(pos)
            self._populate_passives()


# ======================================================================
# 一次行动
# ======================================================================
class ActionRow(QFrame):
    """回合中的一次行动。"""

    changed = pyqtSignal()
    delete_requested = pyqtSignal(object)
    member_edited = pyqtSignal()   # 用户手动更改了行动角色

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
        self._sync_fixed_od()
        self._populate_targets()
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

        self.target_combo = QComboBox()
        self.target_combo.setFixedWidth(TARGET_W)
        self.target_combo.setToolTip(
            "「单名友方回复SP」类技能的回复对象（如 日常维护）；其它技能无效")
        self.target_combo.currentIndexChanged.connect(self._emit_changed)
        layout.addWidget(self.target_combo)

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

        self.break_check = QCheckBox("击破敌人")
        self.break_check.setFixedWidth(BREAK_W)
        self.break_check.setToolTip(
            "本次行动击破敌人（触发「击破时回复SP」的技能/被动）")
        self.break_check.stateChanged.connect(self._on_break_toggled)
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

    def _populate_targets(self):
        """按技能的「单名友方回复SP」范围填充「对象」下拉框。"""
        prev = self.target_combo.currentData()
        skill = self._find_skill()
        scope = None
        if skill is not None and skill.sp_recover and skill.sp_recover_scope:
            scope = skill.sp_recover_scope
        with self._suspended():
            self.target_combo.clear()
            if scope in ("one_other", "one_any"):
                for slot in sorted(self.owner._active_slots()):
                    if scope == "one_other" and slot == self.member_index:
                        continue
                    role = self.owner.team[slot].get("role") or ""
                    self.target_combo.addItem(
                        "角色%d %s" % (slot + 1, role), slot)
                pos = self.target_combo.findData(prev)
                if pos >= 0:
                    self.target_combo.setCurrentIndex(pos)
                self.target_combo.setEnabled(True)
            else:
                self.target_combo.addItem("—", None)
                self.target_combo.setEnabled(False)

    def get_sp_target(self):
        """单名友方回复 SP 的目标队员下标（无则 None）。"""
        return self.target_combo.currentData()

    def _all_skills(self):
        team = self.owner.team
        if not team:
            return []
        idx = min(max(self.member_index, 0), len(team) - 1)
        member = team[idx]
        # 同角色各风格技能通用；SSR/SS 的第一个主动技能为专属
        return self.data_source.available_skills(member.get("role", ""),
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
        self._sync_fixed_od()
        self._populate_targets()
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
        self._sync_fixed_od()
        self._populate_targets()
        if self.turn is not None:
            self.turn.refresh_member_options(self)
        self.member_edited.emit()
        self._emit_changed()

    def set_member(self, member):
        """程序化设置队员（用于前锋同步，不标记为手动编辑）。"""
        if member == self.member_index:
            return
        with self._suspended():
            self.member_index = member
            pos = self.member_combo.findData(member)
            if pos >= 0:
                self.member_combo.setCurrentIndex(pos)
            self._populate_skills(preserve=self._current_skill_name())
            self._apply_skill_data()
        self._sync_fixed_od()
        self._populate_targets()
        if self.turn is not None:
            self.turn.refresh_member_options(self)

    def _on_skill_changed(self, name):
        if self._loading:
            return
        self._apply_skill_data()
        self._sync_fixed_od()
        self._populate_targets()
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

    # ------------------------------------------------------------- helpers
    def is_normal_attack(self):
        skill = self._find_skill()
        return bool(skill and skill.is_normal_attack)

    def _member_setting(self, key, default):
        """该行动角色在「队伍配置」里的设置（如 31X共鸣 / OD耳环）。"""
        team = self.owner.team if self.owner is not None else []
        if not team:
            return default
        idx = min(max(self.member_index, 0), len(team) - 1)
        return team[idx].get(key, default)

    def get_od_skill(self):
        # 31X共鸣 / OD耳环 在队伍配置里按角色设置，作用于该角色的所有回合；
        # 31X共鸣仅在「攻击击破敌人」（勾选击破敌人）时生效
        return ODSkill(
            base_hits=self.base_hits_spin.value(),
            combo_count=self.combo_spin.value(),
            fixed_od=self.fixed_od_spin.value(),
            resonance_31x=(float(self._member_setting("resonance_31x", 0.0) or 0)
                           if self.is_break() else 0.0),
            od_earring=0.0 if self.is_normal_attack()
            else float(self._member_setting("od_earring", 1.0) or 0),
        )

    def _is_attack(self):
        """该行动是否为攻击行为（技能带攻击/伤害 Hit）。"""
        skill = self._find_skill()
        return bool(skill is not None and skill.hits is not None)

    def _od_up_uses_earring(self):
        """技能的「OD条上升」是否按固定OD结算（吃 OD 耳环）。

        攻击技能 -> 吃耳环；非攻击技能默认不吃，但标记 od_up_earring 的
        例外（如 驱动增益）也吃。
        """
        skill = self._find_skill()
        if skill is None:
            return False
        return (skill.hits is not None
                or getattr(skill, "od_up_earring", False))

    def get_od_up_flat(self):
        """非攻击且不吃耳环的技能「OD条上升 X%」：直接增加超频条。"""
        skill = self._find_skill()
        if skill is None or skill.hits is not None:
            return 0.0
        if getattr(skill, "od_up_earring", False):
            return 0.0
        if getattr(skill, "od_up_on_break", False) and not self.is_break():
            return 0.0
        return getattr(skill, "od_up_fixed", 0.0) * 100.0

    def _auto_fixed_od(self):
        """该行动自动计入「固定OD」的部分（吃 OD 耳环）：

        * 「击破敌人时超频条+X%」被动（勾选击破敌人且为攻击行为时）；
        * 技能自带的「OD条上升 X%」效果（攻击技能，或标记吃耳环的例外，
          如 驱动增益；若限定「以此技能击破敌人时」则需勾选击破敌人）。
        """
        total = 0.0
        if self.owner is None:
            return total
        if self._is_attack() and self.is_break():
            total += self.owner._member_break_od_fraction(self.member_index)
        skill = self._find_skill()
        if skill is not None and self._od_up_uses_earring():
            if not getattr(skill, "od_up_on_break", False) or self.is_break():
                total += getattr(skill, "od_up_fixed", 0.0)
        return total

    def _sync_fixed_od(self):
        """把自动固定OD同步到「固定OD」输入框（不覆盖用户手填的值）。"""
        frac = self._auto_fixed_od()
        prev = getattr(self, "_auto_fixed_added", 0.0)
        if abs(frac - prev) > 1e-9:
            self.fixed_od_spin.setValue(self.fixed_od_spin.value() - prev + frac)
            self._auto_fixed_added = frac

    def _on_break_toggled(self, *args):
        self._sync_fixed_od()
        self._emit_changed()

    def set_result(self, contribution):
        self.result_label.setText("%.2f" % contribution)

    def get_sp_cost(self, downed=False):
        """该次行动消耗的 SP；通常攻击为 0。

        downed=True 表示敌人处于倒地/超倒地状态：带该条件的技能
        （如 对称·启示 0(16)）改用条件消耗。
        """
        skill = self._find_skill()
        if not skill:
            return 0
        if (downed and skill.sp_cost_cond == "downed"
                and skill.sp_cost_alt is not None):
            return skill.sp_cost_alt
        return skill.sp_cost

    def get_sp_recover(self):
        """该次行动回复的 SP：(回复量, 范围, 元素)。"""
        skill = self._find_skill()
        if skill and skill.sp_recover and skill.sp_recover_scope:
            return (skill.sp_recover, skill.sp_recover_scope,
                    skill.sp_recover_element)
        return 0, None, None

    def get_sp_recover_extra(self):
        """对象属于指定队伍时的额外回复 SP：(额外量, 队伍)。"""
        skill = self._find_skill()
        if skill is None:
            return 0, None
        return (getattr(skill, "sp_recover_extra", 0) or 0,
                getattr(skill, "sp_recover_extra_team", None))

    def is_break(self):
        return self.break_check.isChecked()

    def get_attack_element(self):
        """本次行动的攻击元素：通常攻击固定为「无」；其余取技能攻击元素 → 角色风格元素 → 无。"""
        skill = self._find_skill()
        if skill is not None and skill.is_normal_attack:
            return "无"
        if skill and skill.element:
            return skill.element
        return self.owner._member_element(self.member_index) or "无"

    def get_break_skill_recover(self):
        """本次行动击破敌人时，技能自带的 SP 回复 (回复量, 范围)。"""
        skill = self._find_skill()
        if skill and skill.sp_break_recover and skill.sp_break_scope:
            return skill.sp_break_recover, skill.sp_break_scope
        return 0, None

    def get_od_down_fixed(self):
        """本次行动「OD条下降」的固定下降值（如 50）。"""
        skill = self._find_skill()
        return skill.od_down_fixed if skill else 0.0

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
            "该次行动后队员剩余 SP" if enough
            else "SP 不足：红色负数为缺口（还差多少），实际 SP 不变")

    def to_data(self):
        return {
            "member": self.member_index,
            "skill": self._current_skill_name(),
            "base_hits": self.base_hits_spin.value(),
            "combo": self.combo_spin.value(),
            # 只存「手动」固定OD；击破被动的部分读取时再自动加上
            "fixed_od": (self.fixed_od_spin.value()
                         - getattr(self, "_auto_fixed_added", 0.0)),
            "break": self.break_check.isChecked(),
            "sp_target": self.get_sp_target(),
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
            self.break_check.setChecked(bool(data.get("break", False)))
            self._populate_targets()
            tpos = self.target_combo.findData(data.get("sp_target"))
            if tpos >= 0:
                self.target_combo.setCurrentIndex(tpos)
        self._sync_fixed_od()


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
        self.manual_front = False      # 用户是否手动改过本回合的前锋队员
        self.last_front_sig = None     # 上次同步的前锋签名（用于向上传播）
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
        self.index_label.setFixedWidth(118)
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
        self.od_combo.setToolTip("该回合发动的 OD 等级；发动后 OD 槽 -等级×100")
        self.od_combo.currentTextChanged.connect(self._on_od_changed)
        header.addWidget(self.od_combo)

        self.od_timing_combo = QComboBox()
        self.od_timing_combo.addItems(OD_TIMING_OPTIONS)
        self.od_timing_combo.setFixedWidth(84)
        self.od_timing_combo.setToolTip(
            "前置OD=当前回合直接发动；后置OD=当前回合结束马上发动（OD回合都是当前回合）")
        self.od_timing_combo.currentTextChanged.connect(self._on_od_changed)
        self.od_timing_combo.setEnabled(False)
        header.addWidget(self.od_timing_combo)

        header.addStretch(1)

        self.start_od_label = QLabel("回合开始OD：0.00")
        self.start_od_label.setFixedWidth(140)
        self.start_od_label.setToolTip(
            "该回合开始时的 OD 槽 = 上一回合结束OD + 回合开始被动 − 发动OD消耗")
        self.start_od_label.setStyleSheet("color: #555555;")
        header.addWidget(self.start_od_label)

        self.result_label = QLabel("本回合OD：0.00")
        self.result_label.setStyleSheet("font-weight: bold;")
        self.result_label.setToolTip(
            "本回合行动产生的 OD（不含回合开始被动；回合开始被动计入「回合开始OD」）")
        header.addWidget(self.result_label)

        self.cumulative_label = QLabel("累计：0.00")
        self.cumulative_label.setFixedWidth(110)
        header.addWidget(self.cumulative_label)

        self.current_od_label = QLabel("当前OD：0.00")
        self.current_od_label.setFixedWidth(130)
        self.current_od_label.setToolTip(
            "行动结束后的 OD 槽：累计获得 − 已发动 OD 消耗")
        self.current_od_label.setStyleSheet("font-weight: bold; color: #3355aa;")
        header.addWidget(self.current_od_label)

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

        # 行动前 / 行动后的全队 SP（含后卫），便于观察未行动角色
        self.team_sp_before_label = QLabel("队伍SP（行动前）：-")
        self.team_sp_before_label.setWordWrap(True)
        self.team_sp_before_label.setStyleSheet(
            "color: #557799; font-size: 12px;")
        root.addWidget(self.team_sp_before_label)

        self.team_sp_label = QLabel("队伍SP（行动后）：-")
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

        追加回合不影响前锋/SP，故返回空。
        """
        if self.turn_type() == "追加回合":
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

        通常回合 ≥3 人时固定 3 人；追加回合可自由增删（1~3）。
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
        action.member_edited.connect(self._on_member_edited)
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

    def _on_member_edited(self):
        # 用户手动改了本回合的队员，则本回合不再自动跟随上一回合的前锋
        self.manual_front = True

    def set_action_members(self, members):
        """按给定队员下标同步本回合各行动的队员（保持技能尽量不变）。"""
        names = list(members)
        for i, action in enumerate(self.actions):
            if i < len(names):
                action.set_member(names[i])
        self.refresh_member_options()

    def _update_controls(self):
        self.add_action_button.setEnabled(len(self.actions) < self.max_actions())
        can_delete = len(self.actions) > self.min_actions()
        for action in self.actions:
            action.delete_button.setEnabled(can_delete)

    def _on_type_changed(self, text):
        # 追加回合不能发动 OD
        no_od = (text == "追加回合")
        with self._suspended():
            self.od_combo.setEnabled(not no_od)
            self.od_timing_combo.setEnabled(
                not no_od and self.od_combo.currentText() != "无")
            if no_od:
                self.od_combo.setCurrentText("无")
        self._apply_style()
        if not self._loading:
            self.refresh_member_options()   # 追加回合的可选角色不同
            self.ensure_action_count()
            self.owner._reindex()           # 追加回合不计入回合数
        self.changed.emit()

    def _on_od_changed(self, text):
        self.od_timing_combo.setEnabled(self.od_combo.currentText() != "无")
        self._apply_style()
        self.owner._reindex()   # 后置OD 沿用上一回合号
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

    def od_timing(self):
        return self.od_timing_combo.currentText()

    def od_gauge_cost(self):
        """本回合发动 OD 消耗的 OD 槽（等级×100）。"""
        return self.od_level() * OD_GAUGE_PER_LEVEL

    def set_index(self, index, additional=False, post_od=False):
        if additional:
            text = "追加回合" if index <= 0 else "第%d回合 追加" % index
        elif post_od:
            # 后置OD：OD 在上一个回合结束发动，故沿用上一个回合号
            text = "第%d回合 后置OD" % max(index, 1)
        else:
            text = "第%d回合" % index
        self.index_label.setText(text)

    def set_result(self, contribution, cumulative):
        self.result_label.setText("本回合OD：%.2f" % contribution)
        self.cumulative_label.setText("累计：%.2f" % cumulative)

    def set_current_od(self, value):
        self.current_od_label.setText("当前OD：%.2f" % value)

    def set_start_od(self, value):
        """记录并显示回合开始 OD 槽（回合开始被动结算之后；用于显示与条件判定）。"""
        self._start_od = value
        self.start_od_label.setText("回合开始OD：%.2f" % value)

    def start_od(self):
        return getattr(self, "_start_od", 0.0)

    def _format_team_sp(self, entries, prefix):
        if not entries:
            return "%s：-" % prefix
        parts = []
        for slot, role, sp, is_front in entries:
            pos = "前" if is_front else "后"
            parts.append("角色%d(%s) %s:%s" % (slot + 1, pos, role, sp))
        return "%s　%s" % (prefix, "　".join(parts))

    def set_team_sp(self, entries, before=None):
        """显示全队 SP。

        entries: 行动结束后 [(slot_index, role_name, sp, is_front), ...]
        before:  行动前（回合开始回复/OD 结算后）的同结构列表
        """
        if before is not None:
            self.team_sp_before_label.setText(
                self._format_team_sp(before, "队伍SP（行动前）"))
        self.team_sp_label.setText(
            self._format_team_sp(entries, "队伍SP（行动后）"))

    def _apply_style(self):
        od = self.od_combo.currentText()
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
            "od_timing": self.od_timing(),
            "actions": [a.to_data() for a in self.actions],
        }

    def set_data(self, data):
        with self._suspended():
            turn_type = data.get("type", TURN_OPTIONS[0])
            if turn_type not in TURN_OPTIONS:   # 兼容旧存档（如已移除的「切换」）
                turn_type = TURN_OPTIONS[0]
            self.type_combo.setCurrentText(turn_type)
            od = data.get("od", "无")
            if od in OD_OPTIONS:
                self.od_combo.setCurrentText(od)
            timing = data.get("od_timing", OD_TIMING_OPTIONS[0])
            if timing in OD_TIMING_OPTIONS:
                self.od_timing_combo.setCurrentText(timing)
            for action in list(self.actions):
                self.actions_layout.removeWidget(action)
                action.setParent(None)
                action.deleteLater()
            self.actions = []
            for action_data in data.get("actions", [])[:MAX_ACTIONS_PER_TURN]:
                action = ActionRow(self.owner, turn=self, data=action_data)
                action.changed.connect(self._on_action_changed)
                action.delete_requested.connect(self._delete_action)
                action.member_edited.connect(self._on_member_edited)
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
        # 用队伍行实际数据同步（含突破数/携带被动等）
        self.team = [row.to_data() for row in self.team_rows]
        self._refresh_role_choices()
        self.add_turn()

    def _default_team(self):
        roles = self.data_source.role_names()
        team = []
        for i in range(TEAM_SIZE):
            role = roles[i] if i < len(roles) else ""
            styles = self.data_source.styles_names(role) if role else []
            team.append({"role": role, "style": styles[0] if styles else "",
                         "resonance_31x": 0.0, "od_earring": 1.0})
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
        root.addWidget(self._build_resist_group())
        root.addWidget(self._build_sp_group())
        root.addWidget(self._build_rows_area(), 1)

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
            # 单列 6 行：每行含 31X共鸣 / OD耳环，宽度可控
            layout.addWidget(row, i, 0)
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

        self.net_od_label = QLabel("净OD：0.00")
        self.net_od_label.setToolTip(
            "净OD = 累计获得 − 发动 OD 消耗（OD1=100 / OD2=200 / OD3=300）")
        layout.addWidget(self.net_od_label)

        self.percent_label = QLabel("实际OD：0.0000")
        layout.addWidget(self.percent_label)

        self.actual_hits_label = QLabel("实际Hit数：0.000")
        layout.addWidget(self.actual_hits_label)
        return group

    def _build_resist_group(self):
        group = QGroupBox("敌人抗性（对应属性行动 HIT OD 记 0）")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        self.resistance_check = QCheckBox("全部（命中无效）")
        self.resistance_check.setToolTip("勾选后所有行动的 HIT OD 记 0")
        self.resistance_check.stateChanged.connect(self.recalculate)
        layout.addWidget(self.resistance_check)

        layout.addWidget(QLabel("按属性："))
        self.resist_element_checks = {}
        for element in ELEMENTS:
            cb = QCheckBox(element)
            cb.setToolTip("敌人对「%s」属性抗性，该属性角色的行动 HIT OD 记 0" % element)
            cb.stateChanged.connect(self.recalculate)
            layout.addWidget(cb)
            self.resist_element_checks[element] = cb

        layout.addStretch(1)
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
        self.sp_regen_front_spin.setValue(2)
        self.sp_regen_front_spin.setFixedWidth(56)
        self.sp_regen_front_spin.setToolTip(
            "每回合开始时前锋的基础回复；风格被动的「闪光/佳音…」会额外叠加")
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

        self.sp_limit_hint = QLabel("")
        self.sp_limit_hint.setStyleSheet("color: #cc6600; font-size: 12px;")
        layout.addWidget(self.sp_limit_hint)

        layout.addStretch(1)
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

    # ------------------------------------------------------------- team ops
    def _normalize_team(self):
        """后卫存在的必要条件是前锋有 3 人。"""
        front_full = all(self.team_rows[i].role() for i in range(3))
        for i in range(3, TEAM_SIZE):
            row = self.team_rows[i]
            if not front_full and row.role():
                row.set_role("无")
            row.set_slot_enabled(front_full)

    def _refresh_role_choices(self):
        """队伍角色不可重复：禁用其它位置已选的角色。"""
        used = {}
        for i, row in enumerate(self.team_rows):
            role = row.role()
            if role:
                used.setdefault(role, []).append(i)
        for i, row in enumerate(self.team_rows):
            row.set_roles_enabled(used, i)

    def _on_team_changed(self):
        if self._team_updating:
            return
        self._team_updating = True
        try:
            self._normalize_team()
            self.team = [row.to_data() for row in self.team_rows]
        finally:
            self._team_updating = False
        self._refresh_role_choices()
        for turn in self.turns:
            turn.refresh_team()
        self.recalculate()

    # ------------------------------------------------------------- turn ops
    def _last_front_actors(self, exclude=None):
        """最近一个有效回合的行动队员（跳过追加回合）。"""
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
        turn.changed.connect(lambda t=turn: self._on_turn_changed(t))
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
        turn.last_front_sig = tuple(turn.actor_members())
        self._reindex()
        self._select_turn(turn)
        self.recalculate()
        return turn

    def add_additional_turn(self):
        """添加「追加回合」：不计回合数、不影响 SP。"""
        return self.add_turn(turn_type="追加回合")

    def _on_turn_changed(self, turn):
        """某回合变更时，若其前锋变化则同步到后面（未被手动编辑的）回合。"""
        self._sync_following_turns(turn)
        self.recalculate()

    def _sync_following_turns(self, turn):
        try:
            idx = self.turns.index(turn)
        except ValueError:
            return
        sig = tuple(turn.actor_members())
        if not sig or sig == turn.last_front_sig:
            return
        turn.last_front_sig = sig
        for nxt in self.turns[idx + 1:]:
            if nxt.manual_front:
                break
            nxt.last_front_sig = sig
            nxt.set_action_members(sig)

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
        """重新编号：追加回合、以及后置OD 回合都不计入回合数。"""
        number = 0
        for turn in self.turns:
            is_additional = turn.turn_type() == "追加回合"
            is_post_od = (not is_additional and turn.od_level() > 0
                          and turn.od_timing() == "后置OD")
            if is_additional:
                turn.set_index(number, additional=True)
            elif is_post_od:
                turn.set_index(number, post_od=True)
            else:
                number += 1
                turn.set_index(number)

    # --------------------------------------------------------- calculation
    def _battle_params(self, resistance=False):
        return ODBattle(
            target_count=self.target_spin.value(),
            resistance=resistance,
            other_od=self.other_od_spin.value(),
            enemy_od_rate=self.enemy_od_spin.value(),
        )

    def _resisted_elements(self):
        return {el for el, cb in self.resist_element_checks.items()
                if cb.isChecked()}

    def recalculate(self):
        blanket = self.resistance_check.isChecked()
        resisted = self._resisted_elements()
        cumulative = 0.0
        running_od = 0.0   # 行动结束后的 OD 槽（累计获得 − 已发动消耗）
        consumed = 0.0
        prev_level = 0     # 上一次发动的 OD 等级（连续同等级视为同一次发动）
        od_gain_used = set()   # 已触发「OD条上升」被动的队员（出击中1次）
        start_front = self._initial_front()   # 回合开始时的前锋
        for turn_idx, turn in enumerate(self.turns):
            # 回合开始：风格被动「OD条上升」（如 V字回复）——
            # 按触发时机/位置/阈值/是否出击中1次结算。
            # OD 回合（发动 OD 的回合，含其加成回合）与追加回合不触发「回合开始时」效果。
            starts_turn = (not turn.od_level() and turn.turn_type() != "追加回合")
            turn_bonus = 0.0   # 回合开始时被动带来的 OD 增加
            for slot in (self._active_slots() if starts_turn else []):
                if slot in od_gain_used:
                    continue
                for mod in self._member_turn_start_od(slot):
                    if mod.get("timing") == "battle" and turn_idx != 0:
                        continue
                    pos = mod.get("position")
                    if pos == "front" and slot not in start_front:
                        continue
                    if pos == "back" and slot in start_front:
                        continue
                    threshold = mod.get("threshold")
                    if threshold is not None and running_od >= threshold:
                        continue
                    turn_bonus += mod.get("amount", 0.0)
                    if mod.get("once", True):
                        od_gain_used.add(slot)
                    break
            # 发动 OD 消耗（同一次发动只扣一次）
            level = turn.od_level()
            cost = 0
            if level > 0 and level != prev_level:
                cost = level * OD_GAUGE_PER_LEVEL
                consumed += cost
            prev_level = level

            # 「回合开始OD」= 上一回合结束OD + 回合开始被动 − 发动OD消耗
            # 「本回合OD」只统计本回合行动；因此 回合开始OD + 本回合OD = 当前OD
            turn.set_start_od(running_od + turn_bonus - cost)
            turn_actions = 0.0
            for action in turn.actions:
                element = action.get_attack_element()
                resist = blanket or bool(element and element in resisted)
                battle = self._battle_params(resist)
                value = calc_od(action.get_od_skill(), battle).total_od
                # 「OD条下降」：固定扣减（如 50% → −50）
                value -= action.get_od_down_fixed()
                # 非攻击技能的「OD条上升 X%」：直接增加超频条（不吃 OD 耳环）
                value += action.get_od_up_flat()
                action.set_result(value)
                turn_actions += value

            cumulative += turn_bonus + turn_actions
            running_od += turn_bonus + turn_actions - cost
            turn.set_result(turn_actions, cumulative)
            turn.set_current_od(running_od)

            # 回合结束：更新前锋（供下一回合「回合开始时」判定使用）
            actors = turn.actor_members()
            if actors:
                merged = list(actors)
                for m in start_front:
                    if len(merged) >= 3:
                        break
                    if m not in merged:
                        merged.append(m)
                for m in self._active_slots():
                    if len(merged) >= 3:
                        break
                    if m not in merged:
                        merged.append(m)
                start_front = merged[:3]
        self.total_label.setText("总OD：%.2f" % cumulative)
        self.net_od_label.setText("净OD：%.2f（消耗 %.0f）" % (
            cumulative - consumed, consumed))
        self.percent_label.setText("实际OD：%.4f" % (cumulative / 100.0))
        self.actual_hits_label.setText(
            "实际Hit数：%.3f" % (cumulative / 100.0 * 40.0))

        limit = self._effective_sp_limit()
        if limit != self.sp_limit_spin.value():
            self.sp_limit_hint.setText("（自动 %d）" % limit)
        else:
            self.sp_limit_hint.setText("")

        self._recalc_sp()

    def _active_slots(self):
        """队伍中已安排角色的位置下标。"""
        return [i for i in range(len(self.team)) if self.team[i].get("role")]

    def _initial_front(self):
        """初始前锋：队伍中前 3 个已安排角色的位置。"""
        return self._active_slots()[:3]

    def _effective_sp_limit(self):
        """当前 SP 上限：设置值与该风格「SP上限」被动（如 30）取较大者。"""
        limit = self.sp_limit_spin.value()
        for slot in self._active_slots():
            role = self.team[slot].get("role")
            style = self.team[slot].get("style")
            selected = self._selected_passives(slot)
            for st in self.data_source.styles(role):
                if st.name != style or not st.sp_limit_override:
                    continue
                if (st.boost_enabler is None or selected is None
                        or st.boost_enabler in selected):
                    limit = max(limit, st.sp_limit_override)
        return limit

    def _recalc_sp(self):
        """模拟全队 SP。

        * 回合开始时的前锋：第 1 回合 = 队伍配置前 3 人；之后 = 上一回合行动的队员。
        * 回合开始按「回合开始时的前锋/后卫」回复：前锋 +3、后卫 +2。
        * 回合中/结束时的前锋 = 本回合行动的队员；
          技能/被动里的「前锋」回复范围以此（本回合行动队员）为准。
        * 行动扣费，发动 OD 额外回复。
        """
        limit = self._effective_sp_limit()
        front_regen = self.sp_regen_front_spin.value()
        back_regen = self.sp_regen_back_spin.value()
        count = max(len(self.team), 1)
        active = self._active_slots()

        sp = [self.sp_init_spin.value()] * count
        # front = 「回合开始时」的前锋。第 1 回合 = 队伍配置前 3 人
        front = self._initial_front()
        break_seen = False   # 是否已经发生过击破（用于「首次击破」类被动）
        prev_od_level = 0    # 上一次发动的 OD 等级（同一次发动只给一次额外 SP）
        sp_once_used = set()  # 已触发过「每次出击1次」类 SP 被动的队员

        for turn_idx, turn in enumerate(self.turns):
            # 追加回合不计回合数：不触发「回合开始回复」与 OD 回复，
            # 但行动仍然消耗 SP、技能回复 SP 也照常生效。
            is_additional = turn.turn_type() == "追加回合"
            # 回合开始时的前锋（用于回合开始 +3/+2）
            start_front = set(front)
            # 本回合行动的队员 = 回合中/结束时的前锋（用于技能/被动「前锋」范围）
            actors = turn.actor_members()
            turn_front = set(actors) if actors else start_front
            first_turn = (turn_idx == 0)

            # 后置OD 属于上一回合：不触发回合开始回复与闪光
            level = turn.od_level()
            is_new_od = level > 0 and level != prev_od_level
            is_post_od = (not is_additional and level > 0
                          and turn.od_timing() == "后置OD")

            if is_post_od:
                # 仅结算 OD 的额外 SP（无回合开始回复、无闪光）；同一次发动只给一次
                if is_new_od:
                    self._apply_od_sp_bonus(turn, sp, active)
            elif not is_additional:
                start_od = turn.start_od()
                # 回合开始回复：基础回复（前锋/后卫）+ 风格被动的前锋 SP（闪光等）
                for i in active:
                    regen = front_regen if i in start_front else back_regen
                    if i in start_front:
                        for mod in self._member_front_sp(i):
                            if mod.get("battle_start") and not first_turn:
                                continue
                            low = mod.get("sp_below")
                            if low is not None and sp[i] > low:
                                continue
                            ob = mod.get("od_below")
                            if ob is not None and start_od >= ob:
                                continue
                            regen += mod.get("amount", 0)
                    if sp[i] < limit:
                        sp[i] = min(limit, sp[i] + regen)

                # 回合开始：「回合开始时/战斗开始时」回复友方 SP 的被动（如 与伙伴一起）
                for i in active:
                    for mod in self._member_turn_start_sp(i):
                        if mod.get("battle_start") and not first_turn:
                            continue
                        pos = mod.get("position")
                        if pos == "front" and i not in start_front:
                            continue
                        if pos == "back" and i in start_front:
                            continue
                        low = mod.get("sp_below")
                        if low is not None and sp[i] > low:
                            continue
                        ob = mod.get("od_below")
                        if ob is not None and start_od >= ob:
                            continue
                        if mod.get("downed") and not break_seen:
                            continue
                        if mod.get("once") and i in sp_once_used:
                            continue
                        self._apply_scope_recover(
                            mod.get("amount", 0), mod.get("scope"),
                            mod.get("element"), i, sp, active,
                            start_front, limit)
                        if mod.get("once"):
                            sp_once_used.add(i)

                # 前置OD：当前回合直接发动，回合开始给 OD 额外 SP（同一次发动只给一次）
                if turn.od_timing() == "前置OD" and is_new_od:
                    self._apply_od_sp_bonus(turn, sp, active)
            prev_od_level = level

            # 记录「行动前」全队 SP（回合开始回复 / 前置OD 之后）
            pre_entries = [(i, self.team[i].get("role"), sp[i], i in start_front)
                           for i in active]

            # 行动：扣除技能 SP，并结算技能的 SP 回复效果
            for action in turn.actions:
                i = action.member_index
                if i not in active:
                    action.set_sp_result(None)
                    continue
                cost = action.get_sp_cost(downed=break_seen)
                if cost >= 99:      # 消耗全部 SP
                    cost = sp[i]
                else:
                    # SP 消耗增减被动（同名只叠加一次）；
                    # 「高阶增强」（红宝石香水）不作用于通常攻击与 SP 消耗为 0 的技能
                    cost = max(0, cost + self._sp_cost_modifier(
                        i, active, turn_front, cost, downed=break_seen))
                enough = sp[i] >= cost
                if enough:
                    sp[i] -= cost
                    self._apply_sp_recover(action, i, sp, active,
                                           turn_front, limit)
                    if action.is_break():
                        self._apply_break_recover(
                            action, i, sp, active, turn_front, limit,
                            not break_seen)
                        break_seen = True
                    action.set_sp_result(sp[i], True)
                else:
                    # SP 不足：显示红色负值（还差多少），实际 SP 不变
                    action.set_sp_result(sp[i] - cost, False)

            # 记录本回合结束时全队 SP（含后卫）；前锋标注用回合中的前锋
            entries = [(i, self.team[i].get("role"), sp[i], i in turn_front)
                       for i in active]
            turn.set_team_sp(entries, before=pre_entries)

            # 回合结束：本回合行动的队员成为新的前锋（供下一回合开始使用）
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

    def _apply_od_sp_bonus(self, turn, sp, active):
        """发动 OD 给全队的额外 SP（OD1+5 / OD2+12 / OD3+20）。"""
        level = turn.od_level()
        if 1 <= level < len(OD_SP_BONUS):
            bonus = OD_SP_BONUS[level]
            for i in active:
                sp[i] = min(99, sp[i] + bonus)

    def _member_element(self, slot):
        """队员所装备风格的元素属性。"""
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        for st in self.data_source.styles(role):
            if st.name == style:
                return st.element
        return None

    def _scope_targets(self, scope, element, actor, active, front_set):
        """返回某作用范围影响到的队员下标列表。"""
        if scope == "self":
            return [actor]
        if scope == "all":
            # 全体友方：包含自身
            return list(active)
        if scope == "others":
            # 全体其他友方：除自身外的所有友方
            return [i for i in active if i != actor]
        if scope == "front":
            # 前锋：包含自身
            return [i for i in active if i in front_set]
        if scope == "front_others":
            # 前锋其他友方：前锋中除自身外
            return [i for i in active if i in front_set and i != actor]
        if scope == "others_element":
            # 全体其他{X}属性风格：除自身外该元素（含双属性）的友方
            return [i for i in active
                    if i != actor and element
                    and element in (self._member_element(i) or "")]
        if scope == "all_element":
            # 全体{X}属性风格：含自身该元素（含双属性）的友方
            return [i for i in active
                    if element and element in (self._member_element(i) or "")]
        return []

    def _apply_scope_recover(self, amount, scope, element, actor,
                             sp, active, front_set, limit):
        """按范围结算一次 SP 回复。"""
        if amount <= 0 or not scope:
            return
        for t in self._scope_targets(scope, element, actor, active, front_set):
            if sp[t] < limit:
                sp[t] = min(limit, sp[t] + amount)

    def _member_lb(self, slot):
        """队员风格突破数（0~4）。"""
        try:
            return int(self.team[slot].get("lb", 0) or 0)
        except Exception:
            return 0

    def _member_front_sp(self, slot):
        """风格被动里「回合开始时位于前锋则自身 SP+X」的合计（闪光等，满足突破要求）。"""
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        lb = self._member_lb(slot)
        for st in self.data_source.styles(role):
            if st.name == style:
                return [m for m in st.front_sp_passives if m.get("lb", 0) <= lb]
        return []

    def _selected_passives(self, slot):
        """队员在队伍配置里携带的「（被动技能）」；None 表示全部。"""
        selected = self.team[slot].get("passives")
        return set(selected) if selected is not None else None

    def _member_turn_start_od(self, slot):
        """风格被动里「回合开始时增加 OD 槽」的项（如 V字回复，满足突破要求）。"""
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        lb = self._member_lb(slot)
        for st in self.data_source.styles(role):
            if st.name == style:
                return [m for m in st.turn_start_od if m.get("lb", 0) <= lb]
        return []

    def _member_turn_start_sp(self, slot):
        """风格被动里「回合开始时回复友方 SP」的项（如 与伙伴一起，满足突破要求）。"""
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        lb = self._member_lb(slot)
        for st in self.data_source.styles(role):
            if st.name == style:
                return [m for m in st.turn_start_sp if m.get("lb", 0) <= lb]
        return []

    def _member_break_od(self, slot):
        """风格被动里「击破敌人时增加 OD 槽」的项（满足突破要求）。"""
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        lb = self._member_lb(slot)
        for st in self.data_source.styles(role):
            if st.name == style:
                return [m for m in st.break_od if m.get("lb", 0) <= lb]
        return []

    def _member_break_od_fraction(self, slot):
        """击破敌人时增加 OD 槽的被动，换算为「固定OD」小数（25% → 0.25）。"""
        return sum(m.get("amount", 0.0)
                   for m in self._member_break_od(slot)) / 100.0

    def _member_sp_cost_mods(self, slot):
        """队员所装备风格里影响 SP 消耗的被动（过滤未携带的）。"""
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        selected = self._selected_passives(slot)
        lb = self._member_lb(slot)
        for st in self.data_source.styles(role):
            if st.name == style:
                mods = []
                for mod in st.sp_cost_mods:
                    if mod.get("lb", 0) > lb:
                        continue
                    req = mod.get("requires")
                    if req and selected is not None and req not in selected:
                        continue
                    mods.append(mod)
                return mods
        return []

    def _member_master_mods(self, slot):
        """队员「大师技能」中影响 SP 消耗的项（过滤未携带的被动）。"""
        role = self.team[slot].get("role")
        selected = self._selected_passives(slot)
        mods = []
        for mod in self.data_source.master_sp_cost_mods(role):
            name = mod.get("name")
            if selected is not None and name not in selected:
                continue
            mods.append(mod)
        return mods

    def _sp_cost_modifier(self, actor, active, front_set, base_cost=None,
                          downed=False):
        """作用于该队员的 SP 消耗增减合计。

        同种效果只生效一次并取大值：所有「降低SP消耗」取降幅最大者、
        所有「增加SP消耗」取增幅最大者，两者相抵。
        base_cost 为该技能的原始 SP 消耗；SP 消耗为 0 的技能（通常攻击等）
        不受任何 SP 消耗增减影响。
        downed=True 表示敌人处于倒地/被击破状态（带该条件的被动生效）。
        """
        if base_cost is not None and base_cost == 0:
            return 0          # SP 消耗为 0 的技能不受增减影响

        reductions = []   # 负值
        increases = []    # 正值

        def collect(amount):
            if amount < 0:
                reductions.append(amount)
            elif amount > 0:
                increases.append(amount)

        for slot in active:
            for mod in self._member_sp_cost_mods(slot):
                if mod.get("downed") and not downed:
                    continue
                if actor in self._scope_targets(mod.get("scope"),
                                                mod.get("element"), slot,
                                                active, front_set):
                    collect(mod.get("amount", 0))
            # 「大师技能」：影响全体同队（如 彩凤连理：全体31E友方 SP消耗-1）
            for mod in self._member_master_mods(slot):
                team = mod.get("team")
                names = mod.get("names") or []
                if team:
                    if not self._member_in_team(actor, team):
                        continue
                elif names:
                    if not self._member_name_matches(actor, names):
                        continue
                else:
                    continue          # 目标无法判定 -> 不生效
                collect(mod.get("amount", 0))
        total = 0
        if reductions:
            total += min(reductions)
        if increases:
            total += max(increases)
        return total

    def _member_in_team(self, slot, team):
        """队员所属队伍是否为 team（如 31E）。"""
        role = self.team[slot].get("role")
        return bool(role and self.data_source.role_team(role) == team)

    def _member_name_matches(self, slot, names):
        """队员角色名是否匹配给定的名字片段（如 丸山 / 四叶草）。"""
        role = self.team[slot].get("role") or ""
        return any(n and n in role for n in names)

    def _apply_sp_recover(self, action, actor, sp, active, front_set, limit):
        """结算技能自带的 SP 回复效果。"""
        amount, scope, element = action.get_sp_recover()
        if scope in ("one_other", "one_any"):
            # 单名友方：回复到行动里选择的「对象」
            target = action.get_sp_target()
            if target is None or not (0 <= target < len(sp)):
                return
            extra, team = action.get_sp_recover_extra()
            if extra and team and self._member_in_team(target, team):
                amount += extra
            if sp[target] < limit:
                sp[target] = min(limit, sp[target] + amount)
            return
        self._apply_scope_recover(amount, scope, element, actor,
                                  sp, active, front_set, limit)

    def _member_break_sp(self, slot):
        """队员所装备风格里「击破敌人时回复SP」的被动（满足突破要求）。"""
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        lb = self._member_lb(slot)
        for st in self.data_source.styles(role):
            if st.name == style:
                return [b for b in st.break_sp if b.get("lb", 0) <= lb]
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
                "resist_elements": sorted(self._resisted_elements()),
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
        resist = set(battle.get("resist_elements") or [])
        for element, cb in self.resist_element_checks.items():
            cb.setChecked(element in resist)
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
    # 使用说明输出到 工具/排轴/help.txt
    write_help_file()

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
