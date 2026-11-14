# -*- coding: utf-8 -*-
"""排轴队伍配置中的单个位置。"""

from contextlib import contextmanager
from PyQt5.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QMenu, QSpinBox, QToolButton,
    QToolTip
)
from PyQt5.QtCore import Qt, QObject, QEvent, pyqtSignal

from 工具.排轴.axle_common import *
from 工具.排轴.axle_common import _talent_display, _talent_element_ok

class _TalentItemTip(QObject):
    """共鸣天赋弹出列表：鼠标停在某一项上时，用小提示窗口显示该天赋效果。

    QComboBox 的弹出列表默认不一定显示 item 的 ToolTipRole，
    这里直接在 view 的 viewport 上拦截 ToolTip 事件，保证能弹出来。
    """

    def __init__(self, row):
        super().__init__(row)
        self.row = row

    def eventFilter(self, obj, event):
        etype = event.type()
        if etype == QEvent.ToolTip:
            view = self.row.talent_combo.view()
            if view is not None:
                index = view.indexAt(event.pos())
                if index.isValid():
                    tip = index.data(Qt.ToolTipRole)
                    if tip:
                        QToolTip.showText(event.globalPos(), str(tip), obj)
                        return True
        elif etype == QEvent.Leave:
            QToolTip.hideText()
        return False


class TeamMemberRow(QFrame):
    """队伍中的一个位置：角色 + 风格。"""

    changed = pyqtSignal()

    def __init__(self, slot, data_source, parent=None):
        super().__init__(parent)
        self.slot = slot
        self.data_source = data_source
        self._loading = 0
        self._block_role_signal = False
        # 风格下拉里每一项对应的形态列表（主形态 + forms）
        self._combo_forms = []
        self._combo_form_datas = []
        self._build_ui()
        # 共鸣天赋列表：悬停显示天赋效果
        self._talent_tip_filter = _TalentItemTip(self)
        self.talent_combo.view().viewport().installEventFilter(
            self._talent_tip_filter)
        self._populate_styles()
        self._populate_talents()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel("角色%d" % self.slot)
        # 不设固定宽度：按文字自然宽度显示，避免被截断
        layout.addWidget(label)

        self.role_combo = QComboBox()
        # 「无」表示该位置不安排角色，从而可自由调整队伍人数
        self.role_combo.addItem("无")
        # 角色按队伍分组：每组前插一个不可选的分组标题
        # （弹出列表会自动加宽到最长条目，所以下拉框本身不用变宽）
        for team, names in self.data_source.roles_by_team():
            self.role_combo.addItem(ROLE_GROUP_FMT % team, ROLE_GROUP_DATA)
            heading = self.role_combo.model().item(self.role_combo.count() - 1)
            if heading is not None:
                heading.setEnabled(False)
            for name in names:
                self.role_combo.addItem(name)
        self.role_combo.setFixedWidth(104)
        self.role_combo.currentTextChanged.connect(self._on_role_changed)
        layout.addWidget(self.role_combo)

        self.style_combo = QComboBox()
        self.style_combo.setFixedWidth(250)   # 显示「风格名-稀有度-元素」
        self.style_combo.currentTextChanged.connect(self._on_style_changed)
        self.style_combo.currentTextChanged.connect(
            lambda text: self.style_combo.setToolTip(text))
        self.style_combo.currentTextChanged.connect(
            lambda *a: self._populate_talents())   # 换风格 -> 重建「可选天赋」列表
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
        layout.addWidget(lb_label)
        self.lb_spin = QSpinBox()
        self.lb_spin.setRange(0, 4)
        self.lb_spin.setValue(4)   # 默认满突破（被动全生效），可下调
        self.lb_spin.setFixedWidth(46)
        self.lb_spin.setToolTip("风格突破数（0~4），部分被动需达到要求才生效（如闪光需突破 1）")
        self.lb_spin.valueChanged.connect(self._emit_changed)
        layout.addWidget(self.lb_spin)

        # 「共鸣天赋」（相当于装备）：默认使用风格自带的；等级可自由选择（0~4）
        res_label = QLabel("共鸣天赋")
        layout.addWidget(res_label)
        self.talent_combo = QComboBox()
        self.talent_combo.setFixedWidth(190)
        self.talent_combo.currentIndexChanged.connect(self._on_talent_changed)
        layout.addWidget(self.talent_combo)
        self.talent_lb = QSpinBox()
        self.talent_lb.setRange(0, 4)
        self.talent_lb.setValue(4)
        self.talent_lb.setFixedWidth(46)
        self.talent_lb.setToolTip("共鸣天赋等级（0~4，可自由选择；SS 选的天赋只显示在轴图，不计入计算）")
        self.talent_lb.valueChanged.connect(self._on_talent_changed)
        layout.addWidget(self.talent_lb)

        ear_label = QLabel("OD耳环")
        layout.addWidget(ear_label)
        self.earring_combo = QComboBox()
        self.earring_combo.setFixedWidth(104)
        for _name in EARRING_CHOICES:
            self.earring_combo.addItem(_name or "无（不装备）", _name)
        self.earring_combo.setToolTip(
            "该角色装备的耳坠。\n"
            "只有「驱动耳坠」会提升 OD 获取量（对所有回合生效；通常攻击不享受），\n"
            "其余耳坠按 0 计算（不影响 OD），但会显示在轴图上。")
        self.earring_combo.currentIndexChanged.connect(self._emit_changed)
        layout.addWidget(self.earring_combo)

        self._condition = "极佳"         # 干劲阶段（默认极佳；界面不显示）
        self._selected_passives = None   # None = 全部携带
        self._last_role = ""             # 用于判断「从无 → 选上角色」时耳环默认驱动

    def _on_talent_changed(self, *args):
        self._update_talent_tip()
        self._emit_changed()

    def _talent_candidates(self):
        """当前风格**可选**的共鸣天赋名（属性匹配）。

        SS / SSR 都可以选（SS 只用于轴图显示，不参与 OD 计算）；
        天赋与属性一一对应，所以只保留与该风格元素相符的那些。
        SS 不能选「该风格自带」的天赋。
        """
        rarity = self._style_rarity()
        if rarity not in ("SSR", "SS"):
            return []
        element = self._style_element()
        pool = self.data_source.resonance_pool()
        own = self._own_resonance()
        own_name = (own or {}).get("name") if isinstance(own, dict) else None
        result = []
        for name, entry in pool.items():
            if not _talent_element_ok(entry.get("owners") or [], element):
                continue
            if rarity == "SS" and own_name and name == own_name:
                continue          # SS 不能装备自身自带的共鸣天赋
            srcs = [s for s in (entry.get("sources") or [])
                    if _talent_element_ok([s.get("element") or "无"], element)]
            if srcs:
                # 每个属性相符的**来源风格**各占一条（完整显示，不汇总）；
                # 同名风格（不同形态）只列一次，避免出现两条一模一样的文字
                seen = set()
                for src in srcs:
                    key = (src.get("team"), src.get("element"),
                           src.get("style"))
                    if key in seen:
                        continue
                    seen.add(key)
                    result.append((name, src))
            else:
                result.append((name, None))
        result.sort(key=lambda item: (
            str(item[0]),
            str((item[1] or {}).get("team") or ""),
            str((item[1] or {}).get("style") or "")))
        return result

    def _populate_talents(self):
        """填充「共鸣天赋」下拉：只列**该风格可选**的天赋，外加（默认）/无。

        不可选的（属性不符）**不入列表**，而不是列出来置灰。
        SS 也能选，但效果只在 SSR 时计入计算（见 _member_resonance）。
        SS 默认选「无」（不把风格自带当默认，导入存档时同样处理）。
        """
        prev = self.talent_combo.currentData() if self.talent_combo.count() else None
        _prev_src = (self.talent_combo.currentData(TALENT_SOURCE_ROLE)
                     if self.talent_combo.count() else None)
        prev_style = (_prev_src.get("style")
                      if isinstance(_prev_src, dict) else None)
        pool = self.data_source.resonance_pool()
        element = self._style_element()
        is_ss = (self._style_rarity() == "SS")
        with self._suspended():
            self.talent_combo.clear()
            self.talent_combo.addItem("（默认）", None)
            self.talent_combo.addItem("无", "")
            for name, src in self._talent_candidates():
                entry = pool.get(name) or {}
                text, tip = _talent_display(name, entry, element, True, src)
                self.talent_combo.addItem(text, name)
                idx = self.talent_combo.count() - 1
                self.talent_combo.setItemData(
                    idx, self._talent_item_tip(name, entry, src),
                    Qt.ToolTipRole)
                self.talent_combo.setItemData(idx, src, TALENT_SOURCE_ROLE)
            # 弹出列表按**最长条目**加宽：完整显示「队伍·属性·风格」，不省略
            self._fit_talent_popup()
            if is_ss:
                # SS：「（默认）」无意义（不生效也不该当展示默认），回落到「无」
                if prev is None:
                    prev = ""
                    prev_style = None
            # 优先还原「同一天赋 + 同一来源风格」
            pos = -1
            first = -1
            for i in range(self.talent_combo.count()):
                if self.talent_combo.itemData(i) != prev:
                    continue
                if first < 0:
                    first = i
                src = self.talent_combo.itemData(i, TALENT_SOURCE_ROLE)
                if (prev_style and isinstance(src, dict)
                        and src.get("style") == prev_style):
                    pos = i
                    break
            if pos < 0:
                pos = first
            if is_ss:
                self.talent_combo.setCurrentIndex(pos if pos >= 0 else 1)
            else:
                self.talent_combo.setCurrentIndex(pos if pos >= 0 else 0)
        self._refresh_talent_enabled()
        self._update_talent_tip()

    def _fit_talent_popup(self):
        """让共鸣天赋的弹出列表足够宽，完整显示每条文字。"""
        view = self.talent_combo.view()
        if view is None:
            return
        view.setTextElideMode(Qt.ElideNone)
        hint = view.sizeHintForColumn(0) + 36
        view.setMinimumWidth(max(self.talent_combo.width(), hint))

    def _style_element(self):
        """当前风格的元素属性（火/冰/雷/光/暗/无…）。"""
        st = self._style_info()
        return getattr(st, "element", None) if st is not None else None

    def _style_rarity(self):
        """当前风格的稀有度（SSR/SS/S/A）。"""
        st = self._style_info()
        return getattr(st, "rarity", None) if st is not None else None

    def _refresh_talent_enabled(self):
        """SS / SSR 风格都能配置共鸣天赋；下拉里只会有「该风格可选」的天赋。

        SS 选的天赋只用于轴图显示，不计入 OD 计算（见 _member_resonance）。
        """
        if self.talent_combo.count() == 0:
            return
        rarity = self._style_rarity()
        can_equip = rarity in ("SSR", "SS")
        self.talent_combo.setEnabled(can_equip)
        self.talent_lb.setEnabled(can_equip)
        element = self._style_element()
        pool = self.data_source.resonance_pool()
        model = self.talent_combo.model()
        for i in range(self.talent_combo.count()):
            name = self.talent_combo.itemData(i)
            item = model.item(i)
            if item is None:
                continue
            if name is None or name == "":
                item.setEnabled(can_equip)
                continue
            entry = pool.get(name) or {}
            src = self.talent_combo.itemData(i, TALENT_SOURCE_ROLE)
            ok = can_equip and _talent_element_ok(entry.get("owners") or [], element)
            item.setEnabled(ok)
            text, tip = _talent_display(name, entry, element, ok, src)
            if rarity == "SS" and ok:
                tip = "（SS 风格：仅显示在轴图，不参与 OD 计算）\n" + tip
            if self.talent_combo.itemText(i) != text:
                self.talent_combo.setItemText(i, text)
            self.talent_combo.setItemData(i, tip, Qt.ToolTipRole)
        # 当前选择不合法时回到「（默认）」
        cur = model.item(self.talent_combo.currentIndex())
        if cur is not None and not cur.isEnabled():
            self.talent_combo.setCurrentIndex(0)

    def earring(self):
        """所选耳坠名（空串 = 不装备）。"""
        return self.earring_combo.currentData() or ""

    def talent(self):
        """所选共鸣天赋名：None = 用风格自带的；"" = 不装备。"""
        if self.talent_combo.count() == 0:
            return None
        return self.talent_combo.currentData()

    def talent_style(self):
        """所选共鸣天赋的「来源风格名」（（默认）/无 → None）。

        同名天赋可以从多个风格取得，轴图据此画对应风格的缩略图。
        """
        if self.talent_combo.count() == 0:
            return None
        src = self.talent_combo.currentData(TALENT_SOURCE_ROLE)
        return src.get("style") if isinstance(src, dict) else None

    def _style_career_at(self, index):
        """风格下拉第 index 项对应风格的职业。"""
        name = self.style_combo.itemData(index)
        for st in self.data_source.styles(self.role()):
            if st.name == name:
                return getattr(st, "career", None)
        return None

    def set_commanders_enabled(self, is_commander):
        """指挥者只能编入一名：非指挥者的位置禁用「指挥者」职业的风格。

        （「指挥行动」专属且只有指挥者能用，故一个队伍不能编入两名指挥者。）

        注意：Qt 在「禁用当前项」时也会发 currentTextChanged，
        如果不管就会触发 _on_style_changed() 把已携带的被动重置成「全部携带」，
        所以这一段用 _suspended() 屏蔽掉。
        """
        model = self.style_combo.model()
        with self._suspended():
            for j in range(self.style_combo.count()):
                item = model.item(j)
                if item is None:
                    continue
                career = self._style_career_at(j)
                item.setEnabled(not (career == "指挥者" and not is_commander))
        if is_commander:
            return
        # 当前选中的风格若被禁用，回到第一个可用风格（这是真的换风格，保留信号）
        cur = model.item(self.style_combo.currentIndex())
        if cur is not None and not cur.isEnabled():
            for j in range(self.style_combo.count()):
                item = model.item(j)
                if item is not None and item.isEnabled():
                    self.style_combo.setCurrentIndex(j)
                    break

    def commander(self):
        """该队员所装备风格的职业是否为「指挥者」。"""
        return self._style_career() == "指挥者"

    def _style_career(self):
        """当前风格的职业（如 指挥者）。"""
        role = self.role()
        style = self.style()
        for st in self.data_source.styles(role):
            if st.name == style:
                return getattr(st, "career", None)
        return None

    def talent_level(self):
        """所选共鸣天赋等级（0~4，可自由选择）。"""
        return self.talent_lb.value()

    def _update_talent_tip(self):
        """提示里显示所选共鸣天赋在当前等级下的效果。"""
        name = self.talent()
        level = self.talent_level()
        pool = self.data_source.resonance_pool()
        if name is None:      # （默认）：取风格自带
            res = self._own_resonance()
        elif name == "":
            res = None
        else:
            res = pool.get(name)
        if not res:
            rarity = self._style_rarity()
            if rarity in ("SSR", "SS"):
                self.talent_combo.setToolTip(
                    "共鸣天赋（相当于装备）；等级可自由选择（0~4）。\n"
                    "SS / SSR 都能选；SS 选的天赋只显示在轴图上，不计入 OD 计算。")
            else:
                self.talent_combo.setToolTip(
                    "共鸣天赋（相当于装备）：只有 SSR / SS 风格才能配置；"
                    "等级可自由选择（0~4）")
            self._refresh_talent_item_tips()
            return
        entry = pool.get(res.get("name")) or {}
        text = res.get("levels", {}).get(str(level), "")
        rarity = self._style_rarity()
        effect_note = ("\n注意：当前为 SS 身份，该天赋仅显示在轴图，不参与计算。"
                       if rarity == "SS" else "")
        self.talent_combo.setToolTip(
            "共鸣天赋：%s（%s）\n所属队伍：%s\n属性：%s\nLv%d：%s%s" % (
                res.get("name", name), name if name else "（默认）",
                entry.get("team") or "—",
                "/".join(entry.get("owners") or []) or "—", level, text,
                effect_note))
        # 下拉列表里每一项的小提示也按当前等级刷新
        self._refresh_talent_item_tips()

    def _talent_effect_text(self, name):
        """天赋在**当前等级**下的效果文字；返回 (天赋名, 效果)。"""
        level = self.talent_level()
        if name is None:                 # （默认）→ 风格自带
            own = self._own_resonance()
            if not isinstance(own, dict):
                return None, ""
            entry = own
        elif name == "":                 # 无
            return None, ""
        else:
            entry = self.data_source.resonance_pool().get(name) or {}
        levels = entry.get("levels") or {}
        text = levels.get(str(level), "")
        if not text:                     # 该等级没写就取最近的更低等级
            for lv in range(int(level), -1, -1):
                if str(lv) in levels:
                    text = levels[str(lv)]
                    break
        return entry.get("name") or name, text

    def _talent_item_tip(self, name, entry, src=None):
        """共鸣天赋下拉项的悬停提示：天赋效果（当前等级）+ 来源。"""
        if name == "":
            return "无：不装备共鸣天赋"
        level = self.talent_level()
        real_name, text = self._talent_effect_text(name)
        if name is None:
            if not real_name:
                return "（默认）：使用风格自带的共鸣天赋（当前风格没有）"
            return "共鸣天赋：%s（风格自带）\nLv%d：%s" % (
                real_name, level, text or "—")
        lines = ["共鸣天赋：%s" % (entry.get("name") or name),
                 "Lv%d：%s" % (level, text or "—"),
                 "（等级用右侧的「共鸣天赋等级」调整）"]
        if isinstance(src, dict) and src.get("style"):
            lines.append("来源：%s·%s·%s" % (
                src.get("team") or "—", src.get("element") or "无",
                src.get("style") or "—"))
        return "\n".join(lines)

    def _refresh_talent_item_tips(self):
        """按当前等级刷新每个下拉项的悬停提示。"""
        pool = self.data_source.resonance_pool()
        for i in range(self.talent_combo.count()):
            name = self.talent_combo.itemData(i)
            entry = pool.get(name) or {}
            src = self.talent_combo.itemData(i, TALENT_SOURCE_ROLE)
            self.talent_combo.setItemData(
                i, self._talent_item_tip(name, entry, src), Qt.ToolTipRole)

    def _own_resonance(self):
        """当前风格的共鸣天赋（无则 None）。"""
        st = self._style_info()
        return getattr(st, "resonance", None) if st is not None else None

    @contextmanager
    def _suspended(self):
        self._loading += 1
        try:
            yield
        finally:
            self._loading -= 1

    def _on_role_changed(self, role):
        if self._loading or self._block_role_signal:
            return
        was_empty = not self._last_role
        self._selected_passives = None   # 换角色后默认携带全部被动
        self._populate_styles(preserve="")
        if not self.role():
            # 角色为「无」时 OD 耳环也必须是「无」
            self._clear_earring()
        elif was_empty:
            # 从「无」选上角色：耳环默认「驱动耳坠」
            self._set_earring_default()
        self._last_role = self.role()
        self._emit_changed()

    def set_roles_enabled(self, used, my_index):
        """队伍角色不可重复：禁用其它位置已选的角色。

        used: {role_name: [slot_index, ...]}
        注意：切换项的可选状态会触发 currentTextChanged，这里临时屏蔽，
        避免误触发「换角色 → 重置风格」。
        """
        model = self.role_combo.model()
        prev = self._block_role_signal
        self._block_role_signal = True
        try:
            for j in range(self.role_combo.count()):
                if self.role_combo.itemData(j) == ROLE_GROUP_DATA:
                    continue          # 分组标题：保持不可选
                role = self.role_combo.itemText(j)
                if not role or role == "无":
                    continue
                taken = any(idx != my_index for idx in used.get(role, []))
                item = model.item(j)
                if item is not None:
                    item.setEnabled(not taken)
        finally:
            self._block_role_signal = prev

    def _on_style_changed(self, style):
        if self._loading:
            return
        self._selected_passives = None   # 换风格后默认携带全部被动
        self._populate_passives()
        self._emit_changed()

    def _style_info(self):
        """按当前下拉项找 StyleInfo；双稀有度风格按 (name, rarity) 匹配。"""
        role = self.role()
        if not role:
            return None
        data = self.style_combo.currentData()
        styles = self.data_source.styles(role)
        if isinstance(data, tuple):
            name, rarity = data
            for st in styles:
                if st.name == name and st.rarity == rarity:
                    return st
            # 克隆失败时退回按名字找
            for st in styles:
                if st.name == name:
                    return st
            return None
        name = data if data else self.style_combo.currentText()
        for st in styles:
            if st.name == name:
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

    @staticmethod
    def _group_style_infos(styles):
        """把同一风格的主形态和 forms 合成一组，返回 [[主形态, ...], ...]。"""
        groups = []
        grouped_ids = set()
        for style in styles:
            if id(style) in grouped_ids:
                continue
            forms = [style] + [f for f in (getattr(style, "forms", None) or [])
                               if f is not style]
            for form in forms:
                grouped_ids.add(id(form))
            groups.append(forms)
        return groups

    @staticmethod
    def _form_item_datas(forms):
        """下拉项的实际值：双稀有度风格保留 (name, rarity)，其余为纯风格名。"""
        result = []
        for style in forms:
            if (style.name in DUAL_SS_SSR_STYLE_NAMES
                    and style.rarity in ("SS", "SSR")):
                result.append((style.name, style.rarity))
            else:
                result.append(style.name)
        return result

    def _apply_combo_form(self, index, form_index):
        """把下拉第 index 项切换为组内第 form_index 个形态。"""
        if index < 0 or index >= len(self._combo_forms):
            return
        forms = self._combo_forms[index]
        if not forms:
            return
        form_index %= len(forms)
        style = forms[form_index]
        datas = self._combo_form_datas[index]
        # 先改 itemData，再改文字：currentTextChanged 的槽会读到新形态
        self.style_combo.setItemData(index, datas[form_index])
        self.style_combo.setItemText(index, style.display_name())

    def _populate_styles(self, preserve=None):
        if self.role_combo.currentText() == "无":
            with self._suspended():
                self.style_combo.clear()
                self._combo_forms = []
                self._combo_form_datas = []
                self.style_combo.setEnabled(False)
                self.style_combo.setToolTip("")
            self._populate_talents()      # 没风格 -> 只留（默认）/无
            return
        self.style_combo.setEnabled(True)
        # preserve 可以是纯风格名，也可以是 (name, rarity)
        if isinstance(preserve, tuple):
            preserve_name, preserve_rarity = preserve
        else:
            preserve_name, preserve_rarity = preserve, None
        styles = self.data_source.styles(self.role_combo.currentText())
        groups = self._group_style_infos(styles)

        target_index = 0
        target_form = 0
        found = False
        with self._suspended():
            self.style_combo.clear()
            self._combo_forms = []
            self._combo_form_datas = []
            for group in groups:
                datas = self._form_item_datas(group)
                self.style_combo.addItem(group[0].display_name(), datas[0])
                self._combo_forms.append(group)
                self._combo_form_datas.append(datas)

            if preserve_name:
                # 先精确匹配 (name, rarity)，再退回纯风格名
                if preserve_rarity is not None:
                    for gi, group in enumerate(groups):
                        for fi, style in enumerate(group):
                            if (style.name == preserve_name
                                    and style.rarity == preserve_rarity):
                                target_index, target_form = gi, fi
                                found = True
                                break
                        if found:
                            break
                if not found:
                    for gi, group in enumerate(groups):
                        for fi, style in enumerate(group):
                            if style.name == preserve_name:
                                target_index, target_form = gi, fi
                                found = True
                                break
                        if found:
                            break

            if groups:
                self.style_combo.setCurrentIndex(target_index)
                self._apply_combo_form(target_index, target_form)
                self.style_combo.setToolTip(self.style_combo.currentText())

        self._populate_passives()
        self._populate_talents()          # 风格变了 -> 重建「可选天赋」列表

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
        was_empty = not self._last_role
        self.role_combo.setCurrentText(role if role else "无")
        if not self.role():
            self._clear_earring()
        elif was_empty:
            self._set_earring_default()
        self._last_role = self.role()

    def _clear_earring(self):
        """OD 耳环强制为「无（不装备）」。"""
        self._apply_earring_choice("")

    def _set_earring_default(self):
        """选上角色时 OD 耳环默认为「驱动耳坠」。"""
        self._apply_earring_choice(OD_EARRING_NAME)

    def _apply_earring_choice(self, name):
        pos = self.earring_combo.findData(name)
        if pos < 0:
            pos = 0
        if self.earring_combo.currentIndex() != pos:
            self.earring_combo.blockSignals(True)
            try:
                self.earring_combo.setCurrentIndex(pos)
            finally:
                self.earring_combo.blockSignals(False)

    def role(self):
        # 分组标题不可选，这里再兜一层，避免被程序设成标题
        if self.role_combo.currentData() == ROLE_GROUP_DATA:
            return ""
        text = self.role_combo.currentText()
        return "" if text == "无" else text

    def style(self):
        # 下拉显示带稀有度，实际值取 itemData（纯风格名；双稀有度为元组）
        data = self.style_combo.currentData()
        if isinstance(data, tuple):
            return data[0]
        return data if data else self.style_combo.currentText()

    def style_rarity_selected(self):
        """双稀有度风格选中的稀有度；普通风格返回 None。"""
        data = self.style_combo.currentData()
        if isinstance(data, tuple):
            return data[1]
        return None

    def condition(self):
        """该队员的「干劲」阶段（默认极佳；界面上不显示）。"""
        name = getattr(self, "_condition", "极佳") or "极佳"
        return name if name in CONDITION_TIERS else "极佳"

    def set_condition(self, name):
        """设置干劲阶段（界面上不显示，存档 / 程序内使用）。"""
        self._condition = name if name in CONDITION_TIERS else "极佳"

    def to_data(self):
        data = {"role": self.role(), "style": self.style(),
                "condition": self.condition(),
                "passives": self.selected_passives(),
                "lb": self.lb_spin.value(),
                "resonance_talent": self.talent(),
                "resonance_talent_style": self.talent_style(),
                "resonance_level": self.talent_level(),
                "earring": self.earring(),
                "od_earring": 1.0 if self.earring() == OD_EARRING_NAME else 0.0}
        rarity = self.style_rarity_selected()
        if rarity:
            data["style_rarity"] = rarity
        return data

    def set_data(self, data):
        with self._suspended():
            self.set_condition(str(data.get("condition") or "极佳"))
            if "passives" in data:
                self._selected_passives = set(data.get("passives") or [])
            else:
                self._selected_passives = None
            if "lb" in data:
                self.lb_spin.setValue(int(data.get("lb") or 0))
            name = str(data.get("earring") or "")
            if not name and float(data.get("od_earring", 1) or 0) > 0:
                name = OD_EARRING_NAME        # 旧存档：数值 1 = 驱动耳坠
            # 角色为「无」时耳环强制为「无」（忽略存档里的旧值）
            if not str(data.get("role") or ""):
                name = ""
            _pos = self.earring_combo.findData(name)
            self.earring_combo.setCurrentIndex(_pos if _pos >= 0 else 0)
            self.talent_lb.setValue(int(data.get("resonance_level", 4) or 0))
            role = data.get("role", "")
            self.role_combo.setCurrentText(role if role else "无")
            self._last_role = self.role()
            style = data.get("style", "")
            rarity = data.get("style_rarity")
            preserve = (style, rarity) if (style and rarity) else style
            self._populate_styles(preserve=preserve)
            if style:
                pos = -1
                if rarity:
                    for i in range(self.style_combo.count()):
                        d = self.style_combo.itemData(i)
                        if (isinstance(d, tuple)
                                and d[0] == style and d[1] == rarity):
                            pos = i
                            break
                if pos < 0:
                    pos = self.style_combo.findData(style)
                if pos < 0:
                    for i in range(self.style_combo.count()):
                        d = self.style_combo.itemData(i)
                        if d == style or (
                                isinstance(d, tuple) and d[0] == style):
                            pos = i
                            break
                if pos >= 0:
                    self.style_combo.setCurrentIndex(pos)
            # 共鸣天赋：None = （默认）；"" = 无；否则为天赋名
            tal = data.get("resonance_talent", None)
            # SS 风格导入时：默认/空 一律落成「无」（不把风格自带当默认）
            if tal is None and self._style_rarity() == "SS":
                tal = ""
            # SS 不能装备自身自带的天赋：导入时若命中则强制「无」
            if isinstance(tal, str) and tal and self._style_rarity() == "SS":
                own = self._own_resonance()
                if isinstance(own, dict) and tal == own.get("name"):
                    tal = ""
            tpos = self.talent_combo.findData(tal)
            if tpos < 0 and self._style_rarity() == "SS":
                tpos = self.talent_combo.findData("")
            saved_style = data.get("resonance_talent_style")
            if saved_style:
                for i in range(self.talent_combo.count()):
                    if self.talent_combo.itemData(i) != tal:
                        continue
                    src = self.talent_combo.itemData(i, TALENT_SOURCE_ROLE)
                    if isinstance(src, dict) and src.get("style") == saved_style:
                        tpos = i
                        break
            self.talent_combo.setCurrentIndex(tpos if tpos >= 0 else 0)
            self._populate_passives()
        self._refresh_talent_enabled()
        self._update_talent_tip()
