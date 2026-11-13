# -*- coding: utf-8 -*-
"""排轴回合卡片。"""

from contextlib import contextmanager
from PyQt5.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFrame, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpinBox, QVBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal

from window_qt import install_no_wheel
from 工具.排轴.axle_common import *
from 工具.排轴.axle_common import (
    _build_action_header, _color_with_alpha, _fmt_sp
)
from 工具.排轴.axle_action_row import ActionRow

_TURN_STYLE_CACHE = {}


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
        # 同一 OD 组的后续 Bonus 回合：OD/时机由组内第一回合统一决定
        self._od_group_locked = False
        self.last_front_sig = None     # 上次同步的前锋签名（用于向上传播）
        self._loading = 0
        self._build_ui()
        self.add_action()
        self._apply_style()
        install_no_wheel(self)      # 滚轮不修改下拉框 / 数值框

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 4, 6, 4)
        root.setSpacing(2)

        header = QHBoxLayout()
        header.setSpacing(6)

        # 第二行：OD 发动 / 破坏率 / 超越条（第一行太长了）
        row2 = QHBoxLayout()
        row2.setSpacing(6)

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

        # 破坏率：手动设置该回合**开始时**敌人的破坏率（%）
        # 用于「若回合开始时存在破坏率为 N% 或以上的敌人」类被动（如山胁「最终手段」）
        self.destruction_label = QLabel("破坏率")
        self.destruction_spin = QSpinBox()
        self.destruction_spin.setRange(0, 999)
        self.destruction_spin.setSingleStep(10)
        self.destruction_spin.setSuffix(" %")
        self.destruction_spin.setFixedWidth(84)
        tip = ("该回合**开始时**敌人的破坏率（%）。\n"
               "用于「若回合开始时存在破坏率为 N% 或以上的敌人」类被动，\n"
               "例如山胁「最终手段」：破坏率 ≥200% 时 全体友方 SP+5（每次出击限1次）。")
        self.destruction_label.setToolTip(tip)
        self.destruction_spin.setToolTip(tip)
        self.destruction_spin.valueChanged.connect(self._on_destruction_changed)
        row2.addWidget(self.destruction_label)
        row2.addWidget(self.destruction_spin)

        # 增加SP消耗：该回合所有有消耗的技能 SP 消耗 +N（0 / +2 / +4）
        self.sp_up_label = QLabel("增加SP消耗")
        self.sp_up_combo = QComboBox()
        for _up in SP_COST_UP_CHOICES:
            self.sp_up_combo.addItem("+%d" % _up if _up else "0", _up)
        self.sp_up_combo.setFixedWidth(78)
        _tip = ("该回合所有**有 SP 消耗**的技能 SP 消耗 +N。\n"
                "与其它「增加SP消耗」的被动冲突时**取最大**（不叠加），\n"
                "并与「降低SP消耗」相抵；SP 消耗为 0 的技能不受影响。")
        self.sp_up_label.setToolTip(_tip)
        self.sp_up_combo.setToolTip(_tip)
        self.sp_up_combo.currentIndexChanged.connect(self._on_destruction_changed)
        row2.addWidget(self.sp_up_label)
        row2.addWidget(self.sp_up_combo)

        # OD调整：直接加在该回合的「回合开始OD」上（例 -10 -> 回合开始OD −10）
        self.od_adjust_label = QLabel("OD调整")
        self.od_adjust_spin = QDoubleSpinBox()
        self.od_adjust_spin.setDecimals(2)          # OD 有小数，允许到 0.01
        self.od_adjust_spin.setRange(-300.0, 300.0)
        self.od_adjust_spin.setSingleStep(0.5)
        self.od_adjust_spin.setFixedWidth(92)
        _tip2 = ("直接加在该回合的「回合开始OD」上（例：-10 = 回合开始OD −10），\n"
                 "可输入小数（如 -12.5、+0.32）；并计入之后的累计。")
        self.od_adjust_label.setToolTip(_tip2)
        self.od_adjust_spin.setToolTip(_tip2)
        self.od_adjust_spin.valueChanged.connect(self._on_destruction_changed)
        row2.addWidget(self.od_adjust_label)
        row2.addWidget(self.od_adjust_spin)

        self.enemy_turn_label = QLabel("敌方回合：0")
        self.enemy_turn_label.setToolTip(
            "该回合开始前已经历的「敌方回合」数：\n"
            "两个通常回合之间的敌方行动算 1 次（T1=0、T2=1、T3=2）。\n"
            "用于「速攻◯」这类按敌方回合计的效果。")
        self.enemy_turn_label.setStyleSheet("color: #666666;")
        row2.addWidget(self.enemy_turn_label)

        self.rhythm_label = QLabel("超越条：—")
        self.rhythm_label.setToolTip(
            "超越条（X之律动）：战斗开始时 = 15%×该属性风格数；该属性风格行动后 +4%；\n"
            "达到 100% 时触发「OD条上升 100%」（出击中限1次，计入当前OD）。\n"
            "显示的是本回合行动结束后的值")
        self.rhythm_label.setStyleSheet("color: #7a5c00;")
        row2.addStretch(1)
        row2.addWidget(self.rhythm_label)

        self.start_od_label = QLabel("回合开始OD：0.00")
        self.start_od_label.setFixedWidth(140)
        self.start_od_label.setToolTip(
            "该回合开始时的 OD 槽 = 上一回合结束OD + 回合开始被动 − 发动OD消耗")
        self.start_od_label.setStyleSheet("color: #555555;")
        row2.addWidget(self.start_od_label)

        self.result_label = QLabel("本回合OD：0.00")
        self.result_label.setStyleSheet("font-weight: bold;")
        self.result_label.setToolTip(
            "本回合行动产生的 OD（不含回合开始被动；回合开始被动计入「回合开始OD」）")
        row2.addWidget(self.result_label)

        self.cumulative_label = QLabel("累计：0.00")
        self.cumulative_label.setFixedWidth(110)
        row2.addWidget(self.cumulative_label)

        self.current_od_label = QLabel("当前OD：0.00")
        self.current_od_label.setFixedWidth(130)
        self.current_od_label.setToolTip(
            "行动结束后的 OD 槽：累计获得 − 已发动 OD 消耗")
        self.current_od_label.setStyleSheet("font-weight: bold; color: #3355aa;")
        row2.addWidget(self.current_od_label)

        self.delete_button = QPushButton("删除回合")
        self.delete_button.setFixedWidth(80)
        self.delete_button.clicked.connect(
            lambda: self.delete_requested.emit(self))
        header.addWidget(self.delete_button)

        root.addLayout(header)
        root.addLayout(row2)
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

        追加回合/特殊回合/占位回合不影响前锋/SP，故返回空。
        """
        if self.turn_type() in UNTIMED_TURN_TYPES:
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
        """本回合应有的行动数：队伍 ≥3 人时为 3，否则为队伍人数（空队伍为 0）。"""
        active = len(self.owner._active_slots())
        if active <= 0:
            return 0
        return min(MAX_ACTIONS_PER_TURN, active)

    def min_actions(self):
        """本回合最少行动数。"""
        if not self.owner._active_slots():
            return 0          # 队伍为空时没有行动
        if self.turn_type() in UNTIMED_TURN_TYPES:
            return 1          # 追加/特殊/占位回合可自由增删，至少保留 1 条
        return self.required_actions()

    def max_actions(self):
        """本回合最多行动数。"""
        if not self.owner._active_slots():
            return 0          # 队伍为空时没有行动
        if self.turn_type() in UNTIMED_TURN_TYPES:
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

        追加回合只能由「上一个普通回合的前锋」行动；
        特殊回合/占位回合性质与追加回合一致，但**角色不限前锋**。
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
        if not self.owner._active_slots():
            return None       # 队伍为空时没有行动
        if len(self.actions) >= self.max_actions():
            return None
        action = ActionRow(self.owner, turn=self, data=data,
                           default_member=self._first_free_member())
        action.changed.connect(self._on_action_changed)
        action.delete_requested.connect(self._delete_action)
        action.member_edited.connect(self._on_member_edited)
        self.actions.append(action)
        self.actions_layout.addWidget(action)
        if not action.style_override:
            # 同一队员的形态一直保持到下一次切换（含新建行动/新回合）
            self.owner.inherit_action_style(action)
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

    def _sync_turn_type(self):
        """选了 OD 则类型显示「超频回合」，无 OD 显示「通常回合」（追加/特殊/占位回合不变）。"""
        if getattr(self, "_syncing_type", False):
            return
        text = self.type_combo.currentText()
        if text in UNTIMED_TURN_TYPES:
            return
        want = "超频回合" if self.od_level() > 0 else "通常回合"
        if text != want:
            self._syncing_type = True
            try:
                with self._suspended():
                    self.type_combo.setCurrentText(want)
            finally:
                self._syncing_type = False

    def _on_type_changed(self, text):
        # 追加/特殊/占位回合不能发动 OD
        no_od = (text in UNTIMED_TURN_TYPES)
        with self._suspended():
            self.od_combo.setEnabled(not no_od)
            self.od_timing_combo.setEnabled(
                not no_od and not self._od_group_locked
                and self.od_combo.currentText() != "无")
            if no_od:
                self.od_combo.setCurrentText("无")
        self._sync_turn_type()
        self._apply_style()
        if not self._loading:
            self.refresh_member_options()   # 追加回合的可选角色不同
            self.ensure_action_count()
            self.owner._reindex()           # 追加回合不计入回合数
        self.changed.emit()

    def _on_od_changed(self, text):
        if self._loading:
            return
        self.od_timing_combo.setEnabled(
            not self._od_group_locked
            and self.od_combo.currentText() != "无")
        self._sync_turn_type()
        self._apply_style()
        self.owner._reindex()   # 后置OD 沿用上一回合号
        self.changed.emit()

    def set_od_group_state(self, od_text=None, timing=None, locked=False):
        """统一同一 OD 组：后续 Bonus 回合沿用第一回合的时机并锁定。"""
        self._od_group_locked = bool(locked)
        with self._suspended():
            if od_text is not None and self.od_combo.currentText() != od_text:
                self.od_combo.setCurrentText(od_text)
            if timing is not None and self.od_timing_combo.currentText() != timing:
                self.od_timing_combo.setCurrentText(timing)
            no_od = self.turn_type() in UNTIMED_TURN_TYPES
            self.od_combo.setEnabled(not no_od)
            self.od_timing_combo.setEnabled(
                not no_od and not locked
                and self.od_combo.currentText() != "无")
            self.od_combo.setToolTip(
                "该回合发动的 OD 等级；发动后 OD 槽 -等级×100")
            if locked:
                self.od_timing_combo.setToolTip(
                    "同一 OD 组的后续回合，时机由组内第一个回合统一决定")
            else:
                self.od_timing_combo.setToolTip(
                    "前置OD=当前回合直接发动；后置OD=当前回合结束马上发动"
                    "（OD回合都是当前回合的）")

    def _on_destruction_changed(self, value):
        """破坏率变化：重算（影响「破坏率≥N%」类 SP 被动）。"""
        self.changed.emit()

    def destruction(self):
        """该回合开始时敌人的破坏率（%，手动设置）。"""
        return self.destruction_spin.value()

    def sp_cost_up(self):
        """该回合手动增加的 SP 消耗（0 / 2 / 4）。"""
        return int(self.sp_up_combo.currentData() or 0)

    def od_adjust(self):
        """直接加在该回合「回合开始OD」上的调整值（默认 0，可为小数）。"""
        return round(float(self.od_adjust_spin.value()), 2)

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
            kind = self.turn_type() or "追加回合"
            short = kind.replace("回合", "")
            text = kind if index <= 0 else "第%d回合 %s" % (index, short)
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

    def set_enemy_turns(self, count):
        """显示该回合开始前已经历的「敌方回合」数。"""
        self.enemy_turn_label.setText("敌方回合：%d" % int(count))

    def set_rhythm(self, text):
        """显示超越条（本回合行动结束后的值）。"""
        self.rhythm_label.setText(text if text else "超越条：—")

    def set_start_od(self, value):
        """记录并显示回合开始 OD 槽（回合开始被动结算之后；用于显示与条件判定）。"""
        self._start_od = value
        self.start_od_label.setText("回合开始OD：%.2f" % value)

    def set_follow_up_od(self, entries):
        """记录本回合的追击信息：[(原始Hit, 元素, 队员下标, 是否吃OD耳环), ...]。"""
        self._follow_up_od = list(entries or [])

    def follow_up_od(self):
        return list(getattr(self, "_follow_up_od", []))

    def start_od(self):
        return getattr(self, "_start_od", 0.0)

    def _format_team_sp(self, entries, prefix):
        if not entries:
            return "%s：-" % prefix
        parts = []
        for slot, role, sp, is_front in entries:
            pos = "前" if is_front else "后"
            parts.append("角色%d(%s) %s:%s" % (slot + 1, pos, role, _fmt_sp(sp)))
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
        turn_type = (self.type_combo.currentText()
                     if hasattr(self, "type_combo") else "")
        # 回合类型配色：追加/特殊/占位回合用固定颜色区分
        type_color, type_bg = TURN_TYPE_COLORS.get(turn_type, ("#c0c0c0", None))
        accent = type_color
        bg = type_bg
        if type_bg is None:
            # 通常/超频回合：按所选 OD 等级上色（主色做竖条，淡化后做背景）
            bg = "#ffffff"
            for key, color in OD_COLORS.items():
                if od.startswith(key):
                    accent = color
                    bg = _color_with_alpha(color)
                    break
        key = (bg, accent)
        style = _TURN_STYLE_CACHE.get(key)
        if style is None:
            style = TURN_CARD_STYLE % {"bg": bg, "accent": accent}
            _TURN_STYLE_CACHE[key] = style
        self.setStyleSheet(style)

    def to_data(self):
        return {
            "type": self.turn_type(),
            "od": self.od_combo.currentText(),
            "od_timing": self.od_timing(),
            "destruction": self.destruction(),
            "sp_cost_up": self.sp_cost_up(),
            "od_adjust": self.od_adjust(),
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
            try:
                self.destruction_spin.setValue(int(data.get("destruction") or 0))
            except (TypeError, ValueError):
                self.destruction_spin.setValue(0)
            try:
                _up = int(data.get("sp_cost_up") or 0)
            except (TypeError, ValueError):
                _up = 0
            _pos_up = self.sp_up_combo.findData(_up)
            self.sp_up_combo.setCurrentIndex(_pos_up if _pos_up >= 0 else 0)
            try:
                self.od_adjust_spin.setValue(float(data.get("od_adjust") or 0))
            except (TypeError, ValueError):
                self.od_adjust_spin.setValue(0.0)
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
            try:
                action.setParent(None)
                action.deleteLater()
            except RuntimeError:
                pass          # C++ 对象可能已随窗口销毁
        self.actions = []
