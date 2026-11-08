# -*- coding: utf-8 -*-
"""排轴回合中的单次行动行。"""

from contextlib import contextmanager
from PyQt5.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSpinBox, QToolButton
)
from PyQt5.QtCore import Qt, pyqtSignal

from window_qt import install_no_wheel
from 工具.排轴.od_calc import ODSkill
from 工具.排轴.data_source import generic_skill_names
from 工具.排轴.axle_common import *
from 工具.排轴.axle_common import _fmt_sp, _make_double_spin

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
        # 只影响本次行动后续的风格形态（None = 跟随队伍配置）
        self.style_override = None
        # True = 用户在这一行主动切换（下一次切换的边界）
        self.style_switch = False
        self._skills_cache = None
        self._skills_cache_key = None
        self._build_ui()
        self._populate_members()
        self._populate_skills()
        self._apply_skill_data()
        self._sync_fixed_od()
        self._populate_targets()
        if data:
            self.set_data(data)
        self._update_form_button()
        install_no_wheel(self)      # 滚轮不修改下拉框 / 数值框

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 2, 6, 2)
        layout.setSpacing(5)

        self.member_combo = QComboBox()
        self.member_combo.setFixedWidth(MEMBER_W)
        self.member_combo.currentIndexChanged.connect(self._on_member_changed)
        layout.addWidget(self.member_combo)

        # 同一风格的多形态：只影响**本行动行**，不改变队伍配置
        self.form_button = QToolButton()
        self.form_button.setText("切换")
        self.form_button.setFixedWidth(46)
        self.form_button.setToolTip("切换本次行动使用的风格形态")
        self.form_button.clicked.connect(self._switch_action_form)
        self.form_button.setVisible(False)
        layout.addWidget(self.form_button)

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
        self.combo_spin.setToolTip("连击数（只对攻击技能、且非通常攻击生效）")
        self.combo_spin.valueChanged.connect(self._on_combo_changed)
        self.combo_spin.valueChanged.connect(self._emit_changed)
        layout.addWidget(self.combo_spin)
        self._manual_combo = 0.0    # 用户手动设置的连击
        self._auto_combo = 0.0      # 「连击数上升」buff 自动提供的连击

        self.fixed_od_spin = _make_double_spin(0.0, 100.0, 0.05, 3, 0.0, FIXED_W)
        self.fixed_od_spin.setToolTip("固定OD")
        self.fixed_od_spin.valueChanged.connect(self._emit_changed)
        layout.addWidget(self.fixed_od_spin)

        self.trigger_combo = QComboBox()
        self.trigger_combo.setFixedWidth(TRIGGER_W)
        for text, value in TRIGGER_CHOICES:
            self.trigger_combo.addItem(text, value)
        self.trigger_combo.setToolTip(
            "本次行动的「条件触发」（手动指定）：\n"
            "· 击破敌人 —— 该行动击破敌人，触发「击破时回复SP」的技能/被动\n"
            "· 【炸裂！！贝斯独奏】发动 —— 逢川惠「特别之夜·少女即兴演奏会」"
            "四破被动：\n"
            "    回合开始时若有处于击破状态的友方则发动，"
            "全体友方 SP+5（可突破上限至 30）")
        self.trigger_combo.currentIndexChanged.connect(self._on_trigger_changed)
        layout.addWidget(self.trigger_combo)

        self.sp_label = QLabel("-")
        self.sp_label.setFixedWidth(SP_W)
        self.sp_label.setAlignment(Qt.AlignCenter)
        self.sp_label.setToolTip("该次行动的剩余 SP＝行动前SP − 本次消耗（不含任何 SP 回复）")
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

    @contextmanager
    def _action_style_ctx(self):
        if self.owner is None:
            yield
            return
        with self.owner._action_style_ctx(self):
            yield

    def _style_group(self):
        """当前行动队员的风格形态列表和当前形态名。"""
        team = self.owner.team
        if not team:
            return [], None
        idx = min(max(self.member_index, 0), len(team) - 1)
        member = team[idx]
        role = member.get("role", "")
        if not role:
            return [], None
        style_name = self.style_override or member.get("style", "")
        for style in self.data_source.styles(role):
            forms = [style] + [f for f in (getattr(style, "forms", None) or [])
                               if f is not style]
            if any(form.name == style_name for form in forms):
                return forms, style_name
        return [], style_name

    def _current_style_name(self):
        forms, style_name = self._style_group()
        if style_name:
            return style_name
        team = self.owner.team
        if not team:
            return ""
        idx = min(max(self.member_index, 0), len(team) - 1)
        return team[idx].get("style", "")

    def _update_form_button(self):
        forms, current = self._style_group()
        has_forms = len(forms) > 1
        self.form_button.setVisible(has_forms)
        self.form_button.setEnabled(has_forms and self.member_combo.isEnabled())
        if has_forms:
            names = [form.name for form in forms]
            i = names.index(current) if current in names else 0
            nxt = forms[(i + 1) % len(forms)]
            self.form_button.setToolTip(
                "切换本次行动的形态：%s → %s"
                % (forms[i].display_name(), nxt.display_name()))

    def set_style_override(self, style_name, emit=False, mark=False):
        """设置本行动的形态，并刷新技能等界面（不负责传播）。"""
        if style_name == self.style_override and not mark:
            return
        with self._suspended():
            self.style_override = style_name
            self.style_switch = bool(mark and style_name)
            self._update_form_button()
            self._populate_skills(preserve=self._current_skill_name())
            self._apply_skill_data()
        self._sync_fixed_od()
        self._populate_targets()
        if emit:
            self._emit_changed()

    def _switch_action_form(self):
        forms, current = self._style_group()
        if len(forms) < 2:
            return
        names = [form.name for form in forms]
        i = names.index(current) if current in names else 0
        new_style = forms[(i + 1) % len(forms)].name
        self.set_style_override(new_style, mark=True)
        # 形态一直保持到下一次切换：同步同一队员后续的所有行动
        if self.owner is not None:
            self.owner.propagate_action_style(self, new_style)
        self._emit_changed()

    # ---------------------------------------------------------- population
    def _populate_members(self):
        team = self.owner.team
        # 同一回合内每位队员只能行动一次
        used = self.turn.used_members(self) if self.turn else set()
        # 追加回合只能选择上一个普通回合的前锋；特殊回合不限
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
        generic = generic_skill_names()
        with self._suspended():
            self.skill_combo.clear()
            heading_added = False
            for skill in skills:
                # 通用（光球）技能前插一个不可选的「通用技能」分组标题
                if not heading_added and skill.name in generic:
                    heading_added = True
                    self.skill_combo.addItem(SKILL_GROUP_GENERIC)
                    idx = self.skill_combo.count() - 1
                    item = self.skill_combo.model().item(idx)
                    if item is not None:
                        item.setEnabled(False)   # 标题不可选中
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
        """按技能的「单名友方」范围填充「对象」下拉框（回复SP / 连击数上升）。"""
        prev = self.target_combo.currentData()
        skill = self._find_skill()
        scope = None
        if skill is not None and skill.sp_recover and skill.sp_recover_scope:
            scope = skill.sp_recover_scope
        buff = getattr(skill, "combo_buff", None) if skill is not None else None
        if scope is None and buff and buff.get("scope") in ("one_other", "one_any"):
            scope = buff["scope"]
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
            self._skills_cache = []
            self._skills_cache_key = None
            return []
        idx = min(max(self.member_index, 0), len(team) - 1)
        member = team[idx]
        # 同角色各风格技能通用；SSR/SS 的第一个主动技能为专属
        # 「指挥行动」：一个队伍只能有一个指挥者，非指挥者恢复通常攻击
        role = member.get("role", "")
        style = self._current_style_name()
        commander = self.owner.is_commander(idx)
        cache_key = (role, style, commander)
        if getattr(self, "_skills_cache_key", None) == cache_key:
            return self._skills_cache or []
        skills = self.data_source.available_skills(
            role, style, commander=commander)
        self._skills_cache_key = cache_key
        self._skills_cache = skills
        return skills

    def _find_skill(self, name=None):
        if name is None:
            name = self._current_skill_name()
        for skill in self._all_skills():
            if skill.name == name:
                return skill
        return None

    def refresh(self):
        """队伍变化后刷新成员与技能。"""
        self._skills_cache = None
        self._skills_cache_key = None
        # 队伍配置改了以后，若原先选的形态已不存在则回到配置形态
        forms, current = self._style_group()
        if self.style_override and not any(f.name == self.style_override
                                           for f in forms):
            self.style_override = None
            self.style_switch = False
        self._populate_members()
        self._populate_skills()
        self._apply_skill_data()
        self._sync_fixed_od()
        self._populate_targets()
        self._update_form_button()
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
        self.style_override = None
        self.style_switch = False
        self._update_form_button()
        if self.owner is not None:
            self.owner.reset_action_style_from(self)
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
            self.style_override = None
            self.style_switch = False
            pos = self.member_combo.findData(member)
            if pos >= 0:
                self.member_combo.setCurrentIndex(pos)
            self._update_form_button()
            if self.owner is not None:
                self.owner.reset_action_style_from(self)
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
        """该行动角色在「队伍配置」里的设置（如 共鸣天赋 / OD耳环）。"""
        team = self.owner.team if self.owner is not None else []
        if not team:
            return default
        idx = min(max(self.member_index, 0), len(team) - 1)
        return team[idx].get(key, default)

    def _od_earring_exempt(self):
        """该技能是否不吃 OD 耳环（如 魔界骑兵启动：不受友方BUFF影响）。"""
        skill = self._find_skill()
        return bool(skill is not None
                    and getattr(skill, "od_earring_exempt", False))

    def get_od_skill(self):
        # 共鸣天赋（B19 31X共鸣）与 OD耳环 在队伍配置里按角色设置；
        # 共鸣天赋的「击破敌人时 超频条+N%」仅在「条件触发」选「击破敌人」时生效
        earring = float(self._member_setting("od_earring", 1.0) or 0)
        is_normal = self.is_normal_attack()
        if is_normal or self._od_earring_exempt():
            earring = 0.0
        # 连击只对「攻击技能（非通常攻击）」生效：通常攻击与非攻击技能都不计连击
        skill = self._find_skill()
        is_attack = bool(skill is not None and skill.hits is not None)
        combo = 0.0
        if is_attack and not is_normal:
            # 手动连击 + 本次实际生效的连击（buff 最多 2 层）
            combo = (getattr(self, "_manual_combo", 0.0)
                     + self.get_effective_combo())
        resonance_31x = 0.0
        if self.is_break() and self.owner is not None:
            with self._action_style_ctx():
                resonance_31x = self.owner._member_resonance_break(
                    self.member_index)
        return ODSkill(
            base_hits=self.base_hits_spin.value(),
            combo_count=combo,
            fixed_od=self.fixed_od_spin.value(),
            resonance_31x=resonance_31x,
            od_earring=earring,
        )

    def get_skill_is_ex(self):
        """该次行动使用的技能是否为「EX技能」。"""
        skill = self._find_skill()
        return bool(skill is not None and getattr(skill, "is_ex_skill", False))

    def is_combo_eligible(self):
        """是否属于「连击生效」的行动：攻击技能且非通常攻击。"""
        skill = self._find_skill()
        return bool(skill is not None and skill.hits is not None
                    and not skill.is_normal_attack)

    def allows_negative_sp(self):
        """该技能是否「SP0或以上即可使用」（SP 不足也能使用，会变负）。"""
        skill = self._find_skill()
        return bool(skill is not None
                    and getattr(skill, "allow_negative_sp", False))

    def set_effective_combo(self, value):
        """记录本次攻击技能实际生效的连击（最多 2 层）。"""
        self._effective_combo = float(value or 0.0)

    def get_effective_combo(self):
        return float(getattr(self, "_effective_combo", 0.0) or 0.0)

    def get_combo_buff(self, active_states=None):
        """该技能附带的「连击数上升」buff（如 连结未来的苍之意志）。

        active_states 为施放者当前所处的状态集合（如 {"歌姬"}）；
        带状态变体的技能（如 月芒）会据此返回对应的那条效果
        （歌姬中：连击+3（特大）／非歌姬：连击+5（中））。
        """
        skill = self._find_skill()
        buff = getattr(skill, "combo_buff", None) if skill is not None else None
        if not buff or not active_states:
            return buff
        variants = buff.get("state_variants") or {}
        for state in active_states:
            spec = variants.get(state)
            if not spec:
                continue
            alt = spec.get("active")
            if not alt:
                continue
            out = dict(alt)
            out["solo"] = buff.get("solo", False)
            out["source"] = buff.get("source")
            out["state_variants"] = variants
            return out
        return buff

    def _on_combo_changed(self, value):
        """用户手动编辑连击：视为「总连击」，手动部分 = 总 − 自动。"""
        if getattr(self, "_setting_combo", False) or self._loading:
            return
        self._manual_combo = max(0.0, float(value) - self.get_auto_combo())

    def set_auto_combo(self, value):
        """记录本回合自动获得的连击（来自「连击数上升」buff）并显示在连击框。"""
        self._auto_combo = float(value or 0.0)
        self._setting_combo = True
        try:
            self.combo_spin.setValue(int(round(
                max(0.0, getattr(self, "_manual_combo", 0.0)
                    + self._auto_combo))))
        finally:
            self._setting_combo = False
        hint = getattr(self, "_combo_grant_hint", None)
        if hint:
            self.combo_spin.setToolTip(hint)
        elif self._auto_combo > 0:
            self.combo_spin.setToolTip(
                "连击数：手动 %d ＋ 自动（连击数上升 buff）%g"
                % (getattr(self, "_manual_combo", 0), self._auto_combo))
        else:
            self.combo_spin.setToolTip("连击数（只对攻击技能、且非通常攻击生效）")

    def set_combo_grant_hint(self, text):
        """本技能「给予对象」的连击数提示（显示在连击框 tooltip）。"""
        self._combo_grant_hint = text

    def get_auto_combo(self):
        return float(getattr(self, "_auto_combo", 0.0) or 0.0)

    def is_all_target(self):
        """该技能是否为「全体」攻击（攻击范围含「全体」）。"""
        skill = self._find_skill()
        return bool(skill is not None and skill.target_scope
                    and "全体" in skill.target_scope)

    def get_target_count(self):
        """该次行动的有效目标数：**全体攻击**按「敌人数量」，**单体攻击**恒为 1。

        通常攻击等单体技能不会因为场上有多个敌人而多算 OD。
        """
        if self.owner is None:
            return 1
        if self.is_all_target():
            return self.owner.target_spin.value()
        return 1

    def _is_attack(self):
        """该行动是否为攻击行为（技能带攻击/伤害 Hit）。"""
        skill = self._find_skill()
        return bool(skill is not None and skill.hits is not None)

    def _od_up_uses_earring(self):
        """该技能是否为「攻击技能」（用于 EX 技能触发的超频条是否吃 OD 耳环）。

        注：技能自带的「OD条上升 X%」**一律吃 OD 耳环**（含非攻击技能，如 驱动增益 /
        连结未来的苍之意志）；只有「自身使用EX技能后 超频条+X%」这种被动，
        在 EX 技能为**非攻击**时才直接加。
        """
        skill = self._find_skill()
        if skill is None:
            return False
        return skill.hits is not None

    def get_od_up_flat(self):
        """不吃耳环、**直接**增加超频条的部分。

        只有「自身使用EX技能后 超频条+X%」在 EX 技能为**非攻击**时直接加；
        技能自带的「OD条上升」一律走「固定OD」（吃 OD 耳环）。
        """
        total = 0.0
        if (self.owner is not None and self.get_skill_is_ex()
                and not self._od_up_uses_earring()):
            with self._action_style_ctx():
                total += self.owner._member_ex_od_fraction(
                    self.member_index) * 100.0
        return total

    def _auto_fixed_od(self):
        """该行动自动计入「固定OD」的部分（吃 OD 耳环）：

        * 「击破敌人时超频条+X%」被动（「条件触发」选「击破敌人」且为攻击行为时）；
        * 技能自带的「OD条上升 X%」效果（攻击技能，或标记吃耳环的例外，
          如 驱动增益；若限定「以此技能击破敌人时」则需选「击破敌人」）。
        """
        total = 0.0
        if self.owner is None:
            return total
        with self._action_style_ctx():
            if self._is_attack() and self.is_break():
                total += self.owner._member_break_od_fraction(self.member_index)
            # 「自身使用EX技能后 超频条+X%」：EX 技能为**攻击技能**时吃 OD 耳环（按固定OD结算）
            if self.get_skill_is_ex() and self._od_up_uses_earring():
                total += self.owner._member_ex_od_fraction(self.member_index)
        skill = self._find_skill()
        # 技能自带的「OD条上升 X%」**一律**按固定OD结算（吃 OD 耳环），
        # 包括非攻击技能（驱动增益 / 连结未来的苍之意志 等）。
        if skill is not None:
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

    def _on_trigger_changed(self, *args):
        self._sync_fixed_od()
        self._emit_changed()

    def set_result(self, contribution):
        self.result_label.setText("%.2f" % contribution)

    def get_sp_cost(self, downed=False, extra=False, sigil_levels=None,
                    first_use=False):
        """该次行动消耗的 SP；通常攻击为 0。

        downed=True 表示敌人处于倒地/超倒地状态：带该条件的技能
        （如 对称·启示 0(16)）改用条件消耗。
        extra=True 表示处于追加回合/特殊回合：带该条件的技能
        （如 苍焰螺旋 7(14)）改用条件消耗。
        sigil_levels 为当前各「X之印」等级 {元素: 等级}：带该条件的技能
        （如 暮色中升腾绽放的幻影：火之印≥4 时 SP消耗减半）改用条件消耗。
        first_use=True 表示该队员是**第一次**使用这个技能：带该条件的技能
        （如 血腥之舞+ 6(11)：首次使用时消耗SP-5）改用折扣后的消耗。
        """
        skill = self._find_skill()
        if not skill:
            return 0
        if skill.sp_cost_alt is not None:
            if skill.sp_cost_cond == "first" and first_use:
                return skill.sp_cost_alt
            if skill.sp_cost_cond == "downed" and downed:
                return skill.sp_cost_alt
            if skill.sp_cost_cond == "extra" and extra:
                return skill.sp_cost_alt
            if skill.sp_cost_cond == "sigil":
                element = getattr(skill, "sp_cost_sigil_element", None)
                need = getattr(skill, "sp_cost_sigil_min", None) or 0
                if element is not None and (sigil_levels or {}).get(element, 0) >= need:
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

    def trigger(self):
        """本次行动的「条件触发」标识（'' / 'break' / 'bass_solo' …）。"""
        return self.trigger_combo.currentData() or ""

    def is_break(self):
        return self.trigger() == "break"

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
        """显示「剩余 SP」= 行动前SP − 本次消耗（不含任何 SP 回复）；不足时标红。"""
        if remaining is None:
            self.sp_label.setText("-")
            self.sp_label.setStyleSheet(
                "background-color: #f0f0f0; color: #888888;"
                "border-radius: 3px;")
            return
        self.sp_label.setText(_fmt_sp(remaining))
        if enough:
            self.sp_label.setStyleSheet(
                "background-color: #eef3ff; border-radius: 3px;")
        else:
            self.sp_label.setStyleSheet(
                "background-color: #f5b5b5; color: #7a0000;"
                "border-radius: 3px; font-weight: bold;")
        self.sp_label.setToolTip(
            "剩余SP＝行动前SP − 本次消耗（不含任何 SP 回复）" if enough
            else "SP 不足：红色负数为缺口（还差多少），实际 SP 不变")

    def to_data(self):
        data = {
            "member": self.member_index,
            "skill": self._current_skill_name(),
            "base_hits": self.base_hits_spin.value(),
            "combo": int(max(0, round(getattr(self, "_manual_combo", 0.0)))),
            # 只存「手动」固定OD；击破被动的部分读取时再自动加上
            "fixed_od": (self.fixed_od_spin.value()
                         - getattr(self, "_auto_fixed_added", 0.0)),
            "break": self.is_break(),
            "trigger": self.trigger(),
            "sp_target": self.get_sp_target(),
        }
        if self.style_override:
            data["style_override"] = self.style_override
        if self.style_switch:
            data["style_switch"] = True
        return data

    def set_data(self, data):
        with self._suspended():
            self.member_index = int(data.get("member", 0) or 0)
            self.style_override = data.get("style_override") or None
            self.style_switch = bool(data.get("style_switch", False))
            self._populate_members()
            forms, _current = self._style_group()
            if self.style_override and not any(
                    form.name == self.style_override for form in forms):
                self.style_override = None
            self._update_form_button()
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
            self._manual_combo = float(data.get("combo", 0) or 0)
            self.combo_spin.setValue(int(self._manual_combo))
            self.fixed_od_spin.setValue(float(data.get("fixed_od", 0) or 0))
            # 存档里保存的是「手填值」，不含自动部分；这里复位后由下面的
            # _sync_fixed_od() 重新把自动固定OD加回去（否则会被覆盖掉）
            self._auto_fixed_added = 0.0
            # 「条件触发」：新存档读 trigger，旧存档（只有 break 布尔）向后兼容
            trigger = data.get("trigger")
            if trigger is None:
                trigger = "break" if data.get("break") else ""
            tpos = self.trigger_combo.findData(trigger)
            self.trigger_combo.setCurrentIndex(tpos if tpos >= 0 else 0)
            self._populate_targets()
            tpos = self.target_combo.findData(data.get("sp_target"))
            if tpos >= 0:
                self.target_combo.setCurrentIndex(tpos)
        self._sync_fixed_od()
