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
      该次行动的 OD 参数（原始Hit数 / 连击数 / 固定OD / 31X共鸣(=共鸣天赋) / OD耳环）。
    * 全局战斗设置：敌人数量、抗性、其他OD增量、敌方OD率、**初始OD**
      （战斗开始时的 OD 槽，默认 0；可选 100/200/300 或 -100/-200/-300）。
    * 按公式实时计算每个回合的 OD 与累计总 OD。
    * SP：参考 https://www.hbr-tool.com/#/simulator 模拟每名队员的 SP。
      回合开始按「回合开始时的前锋」回复（第 1 回合 = 队伍配置前 3 人，
      之后 = 上一回合行动的队员）：前锋 +3 / 后卫 +2（上限默认 20）；
      技能/被动里的「前锋」回复范围按本回合行动的队员结算；
      行动扣除技能 SP，发动 OD 额外获得 OD1 +5 / OD2 +12 / OD3 +20，
      并显示每行动的剩余 SP。
"""

from 工具.排轴.axle_common import *
from 工具.排轴.axle_common import (
    _make_double_spin, _build_action_header, _element_matches,
    _talent_element_ok, _left_text, _fmt_sp, _talent_display,
    _color_with_alpha,
)
from 工具.排轴.axle_widgets import (
    _StatePanel, _AspectCanvas, _ScaledImageView,
)
from 工具.排轴.axle_team_row import TeamMemberRow
from 工具.排轴.axle_action_row import ActionRow
from 工具.排轴.axle_turn_card import TurnCard
from 工具.排轴.axle_state import (
    _StateTracker, STATE_DISPLAY, STATE_EFFECT_TEXT,
)
from 工具.排轴.axle_worker import _AxleImageWorker, keep_axle_worker
from 工具.排轴.axle_calc import AxleCalcMixin

# 窗口管理使用的模块名保持为入口模块（与拆分前一致）
MODULE_NAME = __name__

class AxleODWindow(AxleCalcMixin, QFrame):
    """排轴 + OD 计算主界面。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_source = get_data_source()
        try:
            self.team = self._default_team()
        except Exception as e:
            logger.warning("初始化默认队伍失败: %s", e)
            self.team = [{"role": "", "style": "", "condition": "极佳",
                          "resonance_talent": None,
                          "resonance_level": 4,
                          "od_earring": 1.0} for _ in range(TEAM_SIZE)]
        self.turns = []
        self.team_rows = []
        self.selected_turn = None
        self._state_book = {}       # {回合下标: [该回合开始时的队员状态]}
        self._state_sig = None      # 状态总览的缓存签名（内容没变就不重建表格）
        self._team_updating = False
        self._recalc_suspend = 0    # 批量修改时挂起重算
        self._recalc_pending = False
        # SpinBox/复选框连点时合并重算，避免每次 valueChanged 都全量跑两遍 SP
        self._recalc_timer = QTimer(self)
        self._recalc_timer.setSingleShot(True)
        self._recalc_timer.timeout.connect(self.recalculate)
        # recalculate 内热路径缓存（开始时重建）
        self._style_lookup = {}
        self._sigils_cache = None
        self._sigil_levels_cache = None
        self._axle_image_worker = None
        self._build_ui()
        self._normalize_team()
        # 用队伍行实际数据同步（含突破数/携带被动等）
        self.team = [row.to_data() for row in self.team_rows]
        self._refresh_role_choices()
        self._update_turn_buttons()
        self._update_clear_roles_btn()
        self.add_turn()

    def _default_team(self):
        """默认队伍为**空队伍**（角色/风格都为空，由用户自行编入）。"""
        return [{"role": "", "style": "", "condition": "极佳",
                 "resonance_talent": None,
                 "resonance_level": 4, "od_earring": 1.0}
                for _ in range(TEAM_SIZE)]

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        # 统一本窗口下拉框配色，保证选中的文字清晰可辨
        self.setStyleSheet(COMBO_QSS)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        root.addLayout(self._build_main_toolbar())
        root.addWidget(self._build_team_group())
        root.addWidget(self._build_battle_group())
        root.addWidget(self._build_resist_group())
        root.addWidget(self._build_sp_group())
        root.addStretch(1)
        # 回合列表（含操作按钮）放到独立窗口，避免主窗口拥挤
        self.turns_panel = self._build_turns_panel()
        # 状态总览也是独立窗口（由回合窗口的「状态总览」按钮打开）
        self.state_box = self._build_state_panel()
        self.state_box.hide()

    def _build_main_toolbar(self):
        bar = QHBoxLayout()
        bar.setContentsMargins(8, 2, 0, 0)
        bar.setSpacing(6)
        button = QPushButton("打开回合窗口")
        button.setMinimumWidth(110)
        button.setToolTip("回合列表在独立窗口；关闭后可在此重新打开")
        button.clicked.connect(self.open_turns_window)
        bar.addWidget(button)

        self.clear_roles_btn = QPushButton("清空角色")
        self.clear_roles_btn.setMinimumWidth(110)
        self.clear_roles_btn.setToolTip(
            "一键清空 6 个位置的角色与风格（回合列表与全局战斗设置会保留）")
        self.clear_roles_btn.clicked.connect(self.clear_roles)
        bar.addWidget(self.clear_roles_btn)

        bar.addStretch(1)
        return bar

    # ------------------------------------------------------------ 轴图
    @staticmethod
    def _default_image_path():
        """轴图默认存到「图片」文件夹 —— 不放项目目录，免得被更新逻辑当成待分发文件。"""
        home = os.path.expanduser("~")
        pics = os.path.join(home, "Pictures")
        if not os.path.isdir(pics):
            pics = home
        return os.path.join(pics, "轴图.png")

    def generate_axle_image(self):
        """把当前排轴导出成轴图（PNG / JPG）。"""
        data = self.to_dict()
        if not any(turn.get("actions") for turn in data.get("turns") or []):
            QMessageBox.information(self, "提示", "排轴为空，无法生成轴图")
            return
        default = self._default_image_path()
        path, _ = QFileDialog.getSaveFileName(
            self, "生成轴图", os.path.abspath(default),
            "PNG 图片 (*.png);;JPG 图片 (*.jpg)")
        if not path:
            return
        self._start_axle_image_job(
            data, "generate", path)

    def preview_axle_image(self):
        """只预览轴图，不保存文件。"""
        data = self.to_dict()
        if not any(turn.get("actions") for turn in data.get("turns") or []):
            QMessageBox.information(self, "提示", "排轴为空，无法生成轴图")
            return
        self._start_axle_image_job(data, "preview", None)

    def _start_axle_image_job(self, data, mode, path):
        if self._axle_image_worker is not None and self._axle_image_worker.isRunning():
            return
        worker = _AxleImageWorker(data, self.data_source)
        keep_axle_worker(worker)
        self._axle_image_worker = worker

        def on_done(image, error):
            self._axle_image_worker = None
            worker.deleteLater()
            if error is not None:
                logger.error("渲染轴图失败: %s", error)
                QMessageBox.warning(self, "错误", "渲染轴图失败：%s" % error)
                return
            if image is None:
                return
            try:
                if mode == "generate":
                    from 工具.排轴.axle_image import save_image
                    save_image(image, path)
                    self.show_image_preview(path)
                else:
                    self.show_image_preview(
                        QPixmap.fromImage(image), "轴图预览（未保存）")
            except Exception as e:
                logger.error("生成轴图失败: %s", e)
                QMessageBox.warning(self, "错误", "生成轴图失败：%s" % e)

        worker.done.connect(on_done)
        worker.start()

    def show_image_preview(self, source, title=None):
        """弹预览窗；source 可以是图片路径，也可以直接是 QPixmap。"""
        from_pixmap = isinstance(source, QPixmap)
        if from_pixmap:
            pixmap = source
            tip_text = "预览（未保存到文件）"
            name = "轴图"
        else:
            pixmap = QPixmap(source)
            tip_text = "已生成：%s" % source
            name = os.path.basename(source)
        dlg = QDialog(self)
        # 标题栏要「最小化 / 最大化 / 关闭」（QDialog 默认只有关闭 + 「?」帮助）
        dlg.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint
                           | Qt.WindowCloseButtonHint)
        try:
            set_window_icon(dlg, "./工具/help.png")
        except Exception as e:
            logger.debug("预览窗图标加载失败: %s", e)
        dlg.setWindowTitle(title or ("轴图预览 · %s" % name))
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(10, 10, 10, 10)
        tip = QLabel(tip_text)
        tip.setWordWrap(True)
        layout.addWidget(tip)
        # 图片按窗口宽度自适应；图很高时用垂直滚动条查看（不压缩）
        view = _ScaledImageView()
        if pixmap.isNull():
            view.setToolTip("图片无法预览")
        else:
            view.set_source(pixmap)
        layout.addWidget(view, 1)
        row = QHBoxLayout()
        row.addStretch(1)
        if from_pixmap:
            save_btn = QPushButton("保存为图片")
            save_btn.clicked.connect(self.generate_axle_image)
            row.addWidget(save_btn)
        else:
            open_btn = QPushButton("打开图片")
            open_btn.clicked.connect(lambda: self._open_local_file(source))
            row.addWidget(open_btn)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dlg.accept)
        row.addWidget(close_btn)
        layout.addLayout(row)
        # 初始尺寸：宽=图片原尺寸（≤屏幕 80%），**高固定 900**（≤屏幕 85%）
        screen = QApplication.desktop().availableGeometry(dlg) \
            if QApplication.instance() else None
        max_w = int(screen.width() * 0.8) if screen else 1100
        max_h = int(screen.height() * 0.92) if screen else 900
        w = min(max_w, max(640, pixmap.width() + 40))
        h = min(max_h, 900)          # 初始高度固定 900（屏幕放不下时才收缩）
        dlg.resize(w, h)
        # 关掉上一次的预览，避免开一堆窗口
        old = getattr(self, "_image_preview", None)
        if old is not None and old is not dlg:
            try:
                old.close()
                old.deleteLater()
            except Exception:
                pass
        self._image_preview = dlg          # 防止被 GC
        # 非模态显示：最小化、点其它窗口都正常（exec_() 模态时最小化会把主窗口卡住）
        dlg.setModal(False)
        dlg.show()

    @staticmethod
    def _open_local_file(path):
        try:
            os.startfile(path)             # Windows
        except Exception as e:
            logger.warning("打开文件失败: %s", e)

    def clear_roles(self):
        """一键清空 6 个位置的角色/风格（回合列表与全局战斗设置保留）。"""
        if not any(row.role() for row in self.team_rows):
            return
        ret = QMessageBox.question(
            self, "清空角色",
            "确定要清空全部 6 个位置的角色吗？\n"
            "（回合列表与「全局战斗设置」会保留）",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret != QMessageBox.Yes:
            return
        with self._suspend_recalc():
            for row in self.team_rows:
                row.set_role("")
        self._on_team_changed()

    def _update_clear_roles_btn(self):
        """队伍为空时「清空角色」置灰。"""
        btn = getattr(self, "clear_roles_btn", None)
        if btn is not None:
            btn.setEnabled(any(row.role() for row in self.team_rows))

    def open_state_window(self):
        """打开/置顶「状态总览」窗口。"""
        frame = _open_state_window(self)
        if frame is not None:
            self._state_sig = None      # 重新排版（窗口宽度可能变了）
            self._refresh_state_panel()
            win_set_top(STATE_TITLE, STATE_MODULE)

    def open_turns_window(self):
        """打开/置顶回合窗口。"""
        frame = _open_turns_window(self)
        if frame is not None:
            win_set_top(TURNS_TITLE, TURNS_MODULE)

    def _build_turns_panel(self):
        panel = QWidget()
        panel.setStyleSheet(COMBO_QSS)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addLayout(self._build_toolbar())
        self.rows_area = self._build_rows_area()
        layout.addWidget(self.rows_area, 1)
        return panel

    def _build_toolbar(self):
        bar = QHBoxLayout()
        bar.setContentsMargins(8, 2, 0, 0)
        bar.setSpacing(6)
        buttons = [
            ("＋添加回合", self.add_turn),
            ("＋追加回合", self.add_additional_turn),
            ("＋特殊回合", self.add_special_turn),
            ("＋占位回合", self.add_placeholder_turn),
            ("删除选中回合", self.remove_selected_turn),
            ("上移", lambda: self.move_selected_turn(-1)),
            ("下移", lambda: self.move_selected_turn(1)),
            ("清空", self.clear_turns),
            ("保存", self.save_axle),
            ("读取", self.load_axle),
        ]
        add_buttons = []
        for text, callback in buttons:
            button = QPushButton(text)
            button.setMinimumWidth(92)
            button.clicked.connect(callback)
            bar.addWidget(button)
            add_buttons.append(button)
        # 前四个是「添加回合」类：空队伍时禁用
        self.add_turn_buttons = add_buttons[:4]

        self.preview_image_btn = QPushButton("预览轴图")
        self.preview_image_btn.setMinimumWidth(92)
        self.preview_image_btn.setToolTip(
            "不保存文件，直接把当前排轴渲染成轴图看一眼\n"
            "（头像 + 突破/共鸣徽章 + 共鸣天赋所属风格缩略图 + 携带被动 + 用到的技能 + 回合行动）")
        self.preview_image_btn.clicked.connect(self.preview_axle_image)
        bar.addWidget(self.preview_image_btn)

        self.image_btn = QPushButton("生成轴图")
        self.image_btn.setMinimumWidth(92)
        self.image_btn.setToolTip(
            "把当前排轴导出成一张轴图（PNG / JPG），方便直接分享；\n"
            "配色与版式参考 工具/排轴/hbr_axle.jpg")
        self.image_btn.clicked.connect(self.generate_axle_image)
        bar.addWidget(self.image_btn)

        self.state_btn = QPushButton("状态总览")
        self.state_btn.setMinimumWidth(92)
        self.state_btn.setToolTip(
            "单独打开「状态总览」窗口：按风格列出该回合开始时的\n"
            "状态 / 效果 / 剩余回合 / 来源（只列参与 OD·SP 计算的内容）")
        self.state_btn.clicked.connect(self.open_state_window)
        bar.addWidget(self.state_btn)

        bar.addStretch(1)
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
            # 单列 6 行：每行含 共鸣天赋 / OD耳环，宽度可控
            layout.addWidget(row, i, 0)
        return group

    def _build_battle_group(self):
        group = QGroupBox("全局战斗设置（OD计算）")
        outer = QVBoxLayout(group)
        outer.setContentsMargins(10, 6, 10, 6)
        outer.setSpacing(4)

        layout = QHBoxLayout()
        layout.setSpacing(10)

        layout.addWidget(QLabel("敌人数量"))
        self.target_spin = QSpinBox()
        self.target_spin.setRange(1, 10)
        self.target_spin.setValue(1)
        self.target_spin.setFixedWidth(60)
        self.target_spin.setToolTip("目标数 / 敌人数量：仅全体攻击按此计算，单体攻击恒为 1")
        self.target_spin.valueChanged.connect(self.schedule_recalculate)
        layout.addWidget(self.target_spin)

        layout.addWidget(QLabel("其他OD增量"))
        self.other_od_spin = _make_double_spin(0.0, 100.0, 0.01, 3, 0.0)
        self.other_od_spin.setToolTip("计入总系数的额外 OD 增量")
        self.other_od_spin.valueChanged.connect(self.schedule_recalculate)
        layout.addWidget(self.other_od_spin)

        layout.addWidget(QLabel("敌方OD率"))
        self.enemy_od_spin = _make_double_spin(0.0, 10.0, 0.1, 2, 1.0)
        self.enemy_od_spin.setToolTip("敌方 OD 率倍率（默认 1.0）")
        self.enemy_od_spin.valueChanged.connect(self.schedule_recalculate)
        layout.addWidget(self.enemy_od_spin)

        # 初始OD：战斗开始时的 OD 槽（默认 0；也可设为 100/200/300 或 -100/-200/-300）
        layout.addWidget(QLabel("初始OD"))
        self.initial_od_combo = QComboBox()
        for _v in (0, 100, 200, 300, -100, -200, -300):
            self.initial_od_combo.addItem(str(_v), _v)
        self.initial_od_combo.setCurrentIndex(0)
        self.initial_od_combo.setFixedWidth(80)
        self.initial_od_combo.setToolTip(
            "战斗开始时的 OD 槽（默认 0）；之后按各回合的 OD 增减计算。\n"
            "上限 300（OD3 所需）；填负数表示开局 OD 不足 / 被扣。")
        self.initial_od_combo.currentIndexChanged.connect(self.schedule_recalculate)
        layout.addWidget(self.initial_od_combo)
        layout.addStretch(1)
        outer.addLayout(layout)

        summary = QHBoxLayout()
        summary.setSpacing(18)
        self.total_label = QLabel("总OD：0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 15px;")
        summary.addWidget(self.total_label)

        self.net_od_label = QLabel("净OD：0.00")
        self.net_od_label.setToolTip(
            "净OD = 累计获得 − 发动 OD 消耗（OD1=100 / OD2=200 / OD3=300）")
        summary.addWidget(self.net_od_label)

        self.percent_label = QLabel("实际OD：0.0000")
        summary.addWidget(self.percent_label)

        self.actual_hits_label = QLabel("实际Hit数：0.000")
        summary.addWidget(self.actual_hits_label)
        summary.addStretch(1)
        outer.addLayout(summary)
        return group

    def _build_resist_group(self):
        group = QGroupBox("敌人抗性（对应属性行动 HIT OD 记 0）")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        self.resistance_check = QCheckBox("全部（命中无效）")
        self.resistance_check.setToolTip("勾选后所有行动的 HIT OD 记 0")
        self.resistance_check.stateChanged.connect(self.schedule_recalculate)
        layout.addWidget(self.resistance_check)

        layout.addWidget(QLabel("按属性："))
        self.resist_element_checks = {}
        for element in ELEMENTS:
            cb = QCheckBox(element)
            cb.setToolTip("敌人对「%s」属性抗性，该属性角色的行动 HIT OD 记 0" % element)
            cb.stateChanged.connect(self.schedule_recalculate)
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
        self.sp_init_spin.valueChanged.connect(self.schedule_recalculate)
        layout.addWidget(self.sp_init_spin)

        layout.addWidget(QLabel("前锋回复"))
        self.sp_regen_front_spin = QSpinBox()
        self.sp_regen_front_spin.setRange(0, 20)
        self.sp_regen_front_spin.setValue(2)
        self.sp_regen_front_spin.setFixedWidth(56)
        self.sp_regen_front_spin.setToolTip(
            "每回合开始时前锋的基础回复；风格被动的「闪光/佳音…」会额外叠加")
        self.sp_regen_front_spin.valueChanged.connect(self.schedule_recalculate)
        layout.addWidget(self.sp_regen_front_spin)

        layout.addWidget(QLabel("后卫回复"))
        self.sp_regen_back_spin = QSpinBox()
        self.sp_regen_back_spin.setRange(0, 20)
        self.sp_regen_back_spin.setValue(2)
        self.sp_regen_back_spin.setFixedWidth(56)
        self.sp_regen_back_spin.setToolTip("每回合开始时后卫（角色4~6）回复的 SP")
        self.sp_regen_back_spin.valueChanged.connect(self.schedule_recalculate)
        layout.addWidget(self.sp_regen_back_spin)

        layout.addWidget(QLabel("SP上限"))
        self.sp_limit_spin = QSpinBox()
        self.sp_limit_spin.setRange(1, 99)
        self.sp_limit_spin.setValue(20)
        self.sp_limit_spin.setFixedWidth(56)
        self.sp_limit_spin.setToolTip("SP 上限（参考 hbr-tool 默认 20）")
        self.sp_limit_spin.valueChanged.connect(self.schedule_recalculate)
        layout.addWidget(self.sp_limit_spin)

        self.sp_limit_hint = QLabel("")
        self.sp_limit_hint.setStyleSheet("color: #cc6600; font-size: 12px;")
        layout.addWidget(self.sp_limit_hint)

        layout.addStretch(1)
        return group

    def _build_state_panel(self):
        """「状态总览」面板（独立窗口的内容）。

        按风格列出该回合**开始时**的状态 / 效果 / 剩余回合 / 来源，
        只收录实际参与 OD / SP 计算的状态与「连击数上升」buff。
        """
        box = _StatePanel()
        box.setTitle("状态总览（回合开始时）")
        self.state_box = box
        layout = box.body

        table = QTableWidget(0, 7)
        table.setHorizontalHeaderLabels(
            ["角色", "风格", "状态", "效果", "剩余", "来源", "全部状态"])
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setWordWrap(True)
        table.verticalHeader().setVisible(False)
        table.setMinimumHeight(62)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        header = table.horizontalHeader()
        for col, mode in ((0, QHeaderView.ResizeToContents),
                          (1, QHeaderView.ResizeToContents),
                          (2, QHeaderView.ResizeToContents),
                          (3, QHeaderView.Stretch),
                          (4, QHeaderView.ResizeToContents),
                          (5, QHeaderView.ResizeToContents),
                          (6, QHeaderView.Interactive)):
            header.setSectionResizeMode(col, mode)
        table.setColumnWidth(6, 210)      # 「全部状态」：悬停可看完整明细
        self.state_table = table
        layout.addWidget(table)

        hint = QLabel("「剩余」按己方回合计（含当前回合）；持续/永久状态分别显示。"
                      "状态与连击 buff 参与 OD / SP 计算；"
                      "攻击上升、心眼、暴击率上升等增益类效果**仅用于展示**。"
                      "「全部状态」列：鼠标悬停可看该风格身上的所有状态。")
        hint.setStyleSheet("color: #888888;")
        layout.addWidget(hint)
        return box

    def _snapshot_turn_states(self, turn_idx, tracker, combo_buffs,
                              buff_state=None):
        """记录该回合**开始时**每名队员的状态 / 连击 buff / 增益类效果。"""
        entries = []
        for slot in self._active_slots():
            role = self.team[slot].get("role") or ""
            style = self.team[slot].get("style") or ""
            states = []
            for name in sorted(tracker.states(slot) or ()):
                until = tracker.until.get((slot, name))
                if until is None:
                    continue
                left = (None if until >= 10 ** 5
                        else max(0, int(until) - turn_idx + 1))
                display = STATE_DISPLAY.get(name, name)
                if name == "干劲":
                    display = "干劲（%s）" % (self.team[slot].get("condition")
                                           or "极佳")
                states.append({
                    "name": display,
                    "left": left,
                    "effect": STATE_EFFECT_TEXT.get(name, ""),
                    "source": tracker.sources.get((slot, name), ""),
                })
            combos = []
            for entry in combo_buffs.get(slot, []):
                left = int(entry.get("left", 0) or 0)
                if left <= 0:
                    continue
                combos.append({
                    "amount": entry.get("amount", 0),
                    "left": left,
                    "kind": entry.get("kind", "turn"),
                    "source": entry.get("source") or "",
                    "source_role": entry.get("source_role") or "",
                })
            buffs = []
            for b in (buff_state or {}).get(slot, []):
                left = b.get("left")
                buffs.append({
                    "name": b.get("name") or "",
                    "value": b.get("value") or "",
                    "left": left,
                    "unit": b.get("unit") or "",
                    "source": b.get("source") or "",
                })
            if states or combos or buffs:
                entries.append({"slot": slot, "role": role, "style": style,
                                "states": states, "combos": combos,
                                "buffs": buffs})
        return entries

    def _buff_left_text(self, buff):
        """增益类效果的「剩余」文字（持续 / 永久 / N 回合 / N 次）。"""
        left = buff.get("left")
        unit = buff.get("unit") or ""
        if left is None:
            return "持续" if "持续" in unit else "永久"
        return _left_text(left, "use" if "次" in unit else None)

    def _state_summary(self, entry):
        """「全部状态」列：该风格身上所有状态 / 连击 buff 的摘要 + 悬停明细。"""
        names = []
        lines = []
        for st in entry.get("states", []):
            names.append(st["name"])
            lines.append("%s：%s（%s）" % (
                st["name"], st.get("effect") or "—",
                _left_text(st.get("left"))))
        for cb in entry.get("combos", []):
            label = "连击 +%g" % cb["amount"]
            names.append(label)
            lines.append("%s：%s" % (
                label, _left_text(cb["left"], cb.get("kind"))))
        for bf in entry.get("buffs", []):
            label = bf["name"]
            if bf.get("gained"):
                label += "（本回合获得）"
            names.append(label)
            lines.append("%s：%s（%s）" % (
                label, bf.get("value") or "—", self._buff_left_text(bf)))
        if not names:
            return "—", ""
        tip = "「%s」全部状态（%d 项）：\n%s" % (
            entry.get("style") or "—", len(names),
            "\n".join("  · " + line for line in lines))
        return "、".join(names), tip

    def _refresh_state_panel(self):
        """按「选中的回合」刷新状态总览（没选中则显示最后一个回合）。"""
        table = getattr(self, "state_table", None)
        if table is None:
            return
        turn = self.selected_turn
        if turn not in self.turns:
            turn = self.turns[-1] if self.turns else None
        if turn is None:
            self.state_box.setTitle("状态总览（回合开始时）")
            if self._state_sig is not None:
                self._state_sig = None
                table.setRowCount(0)
            return

        idx = self.turns.index(turn)
        rows = []
        tips = []
        # 一个风格（队员）一行：状态 / 效果 / 剩余 / 来源 用多行对齐
        for entry in self._state_book.get(idx, []):
            who = "角色%d %s" % (entry["slot"] + 1, entry["role"])
            summary, tip = self._state_summary(entry)
            names, effects, lefts, sources = [], [], [], []
            for st in entry["states"]:
                names.append(st["name"])
                effects.append(st.get("effect", ""))
                lefts.append(_left_text(st.get("left")))
                sources.append(st.get("source", ""))
            for cb in entry["combos"]:
                src = cb.get("source") or ""
                if cb.get("source_role"):
                    src = ("%s（%s）" % (src, cb["source_role"])
                           if src else cb["source_role"])
                names.append("连击数上升 +%g" % cb["amount"])
                effects.append("连击 +%g" % cb["amount"])
                lefts.append(_left_text(cb["left"], cb.get("kind")))
                sources.append(src)
            for bf in entry.get("buffs", []):
                names.append(bf["name"])
                effects.append(bf.get("value", ""))
                lefts.append(self._buff_left_text(bf))
                src = bf.get("source", "")
                if bf.get("gained"):
                    src = "%s（本回合获得）" % src if src else "本回合获得"
                sources.append(src)
            if not names:
                names = ["—"]
                effects = [""]
                lefts = [""]
                sources = [""]
            rows.append((who, entry["style"],
                         "\n".join(names), "\n".join(effects),
                         "\n".join(lefts), "\n".join(sources), summary))
            tips.append(tip)
        if not rows:
            rows = [("—", "", "（本回合开始时没有状态）", "", "", "", "")]
            tips = [""]

        title = "状态总览 · %s（回合开始时）" % turn.index_label.text()
        sig = (title, tuple(rows), tuple(tips))
        if sig == self._state_sig:
            return
        self._state_sig = sig
        self.state_box.setTitle(title)
        table.setRowCount(len(rows))
        for r, cells in enumerate(rows):
            for c, text in enumerate(cells):
                item = QTableWidgetItem(str(text))
                if c == 3:
                    item.setToolTip(str(text))
                if c == 6 and tips[r]:
                    item.setToolTip(tips[r])
                table.setItem(r, c, item)
        table.resizeRowsToContents()

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

    def _update_turn_buttons(self):
        """空队伍不能添加任何回合。"""
        ok = bool(self._active_slots())
        for button in getattr(self, "add_turn_buttons", []):
            button.setEnabled(ok)

    def _refresh_commander_choices(self):
        """指挥者只能编入一名：职业为「指挥者」的最靠前一名为指挥者，其它位置禁用指挥者风格。

        还没有任何指挥者时（commander is None）**所有位置都可选**，
        这样才选得进第一个指挥者；选中后其它位置的指挥者风格才会被禁用。
        """
        commander = None
        for slot, row in enumerate(self.team_rows):
            if row.role() and row.commander():
                commander = slot
                break
        for slot, row in enumerate(self.team_rows):
            row.set_commanders_enabled(commander is None or slot == commander)

    def _on_team_changed(self):
        if self._team_updating:
            return
        self._team_updating = True
        try:
            self._normalize_team()
            self._refresh_commander_choices()
            self.team = [row.to_data() for row in self.team_rows]
        finally:
            self._team_updating = False
        # 队伍批量同步（刷新所有回合/行动行）期间挂起重算，最后统一算一次
        with self._suspend_recalc():
            self._refresh_role_choices()
            self._update_turn_buttons()
            self._update_clear_roles_btn()
            # 默认是空队伍，因此开始时没有回合；首次编入角色后自动建一个回合
            if not self.turns and self._active_slots():
                self.add_turn()
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
        if not self._active_slots():
            return None       # 空队伍不能添加回合
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

    def add_special_turn(self):
        """添加「特殊回合」：性质同追加回合，但角色不限前锋。"""
        return self.add_turn(turn_type="特殊回合")

    def add_placeholder_turn(self):
        """添加「占位回合」：不计回合数、不算己方回合、不触发任何被动、技能不消耗 SP。"""
        return self.add_turn(turn_type="占位回合")

    def _on_turn_changed(self, turn):
        """某回合变更时，若其前锋变化则同步到后面（未被手动编辑的）回合。"""
        self._sync_following_turns(turn)
        self.schedule_recalculate()

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
        self._refresh_state_panel()
        for item in self.turns:
            if item is turn:
                item.index_label.setStyleSheet(
                    "background-color: #0078d4; color: white;"
                    "border-radius: 3px; font-weight: bold;")
            else:
                item.index_label.setStyleSheet("")

    def _reindex(self):
        """重新编号。

        * 追加回合不计入回合数；
        * 同一次 OD 发动的多个「超频回合」（连续相同等级，如
          OD3 / OD3/Bonus1 / OD3/Bonus2）共用同一个回合号；
        * 后置OD 在上一个回合结束发动，故沿用上一个回合号。
        """
        number = 0
        prev_level = 0
        group_first = None
        for turn in self.turns:
            is_additional = turn.turn_type() in UNTIMED_TURN_TYPES
            level = turn.od_level()
            if is_additional:
                turn.set_od_group_state(locked=False)
                turn.set_index(number, additional=True)
                continue

            if level > 0 and level == prev_level and group_first is not None:
                # 同一次 OD 发动的后续超频回合：OD 等级/时机由组内第一回合统一
                post_od = (group_first.od_timing() == "后置OD")
                turn.set_od_group_state(
                    timing=group_first.od_timing(), locked=True)
                turn.set_index(number, post_od=post_od)
            else:
                if level > 0:
                    group_first = turn
                    turn.set_od_group_state(locked=False)
                    if turn.od_timing() == "后置OD":
                        turn.set_index(number, post_od=True)
                    else:
                        number += 1
                        turn.set_index(number)
                else:
                    group_first = None
                    turn.set_od_group_state(locked=False)
                    number += 1
                    turn.set_index(number)
            prev_level = level

    # --------------------------------------------------------- calculation

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
                "initial_od": int(self.initial_od_combo.currentData() or 0),
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

        # 读档涉及大量控件赋值/建回合，先挂起重算，最后统一算一次
        with self._suspend_recalc():
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
            self.resistance_check.setChecked(
                bool(battle.get("resistance", False)))
            resist = set(battle.get("resist_elements") or [])
            for element, cb in self.resist_element_checks.items():
                cb.setChecked(element in resist)
            self.other_od_spin.setValue(float(battle.get("other_od", 0)))
            self.enemy_od_spin.setValue(float(battle.get("enemy_od_rate", 1)))
            init_od = int(battle.get("initial_od", 0) or 0)
            pos = self.initial_od_combo.findData(init_od)
            self.initial_od_combo.setCurrentIndex(pos if pos >= 0 else 0)
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
        # 轴图后台线程还在运行时，先断开回调，避免它完成后再访问已销毁的窗口
        worker = getattr(self, "_axle_image_worker", None)
        if worker is not None:
            self._axle_image_worker = None
            try:
                worker.done.disconnect()
            except (TypeError, RuntimeError):
                pass
            if worker.isRunning():
                worker.wait(3000)
            worker.finished.connect(worker.deleteLater)

        for turn in list(self.turns):
            try:
                turn.destroy()
                turn.setParent(None)
                turn.deleteLater()
            except RuntimeError:
                pass          # C++ 对象可能已随回合窗口销毁
        self.turns = []


TURNS_TITLE = WINDOW_TITLE + "-回合"
TURNS_MODULE = MODULE_NAME + "_TURNS"
STATE_TITLE = WINDOW_TITLE + "-状态总览"
STATE_MODULE = MODULE_NAME + "_STATE"
_active_view = None   # 当前打开的排轴窗口（用于重新打开回合窗口）


def _open_turns_window(view):
    """把回合列表放到独立窗口，避免主窗口拥挤。"""
    frame = getattr(view, "turns_frame", None)
    if frame is not None:
        return frame
    frame = creat_Toplevel(TURNS_TITLE, 1295, 760, 530, 170)
    set_window_icon(frame, "./工具/help.png")
    frame.grid_layout.addWidget(view.turns_panel, 0, 0)
    frame.grid_layout.setRowStretch(0, 1)
    frame.grid_layout.setColumnStretch(0, 1)
    view.turns_panel.show()   # 面板曾被隐藏，重新加入后需显式显示
    view.turns_frame = frame
    win_open_manage(frame, TURNS_MODULE)

    def on_close(self, event):
        if getattr(view, "_turns_closing", False):
            event.accept()
            return
        view._turns_closing = True
        try:
            view.turns_frame = None
            # 保留回合面板（不随窗口销毁），以便之后再次打开
            panel = view.turns_panel
            panel.setParent(None)
            panel.hide()
            win_close_manage(frame, TURNS_MODULE, None)
        finally:
            view._turns_closing = False
        event.accept()

    frame.closeEvent = types.MethodType(on_close, frame)
    return frame


def _open_state_window(view):
    """把「状态总览」放到独立窗口。"""
    frame = getattr(view, "state_frame", None)
    if frame is not None:
        return frame
    frame = creat_Toplevel(STATE_TITLE, 980, 460, 75, 520)
    set_window_icon(frame, "./工具/help.png")
    frame.grid_layout.addWidget(view.state_box, 0, 0)
    frame.grid_layout.setRowStretch(0, 1)
    frame.grid_layout.setColumnStretch(0, 1)
    view.state_box.show()
    view.state_frame = frame
    win_open_manage(frame, STATE_MODULE)

    def on_close(self, event):
        if getattr(view, "_state_closing", False):
            event.accept()
            return
        view._state_closing = True
        try:
            view.state_frame = None
            panel = view.state_box
            panel.setParent(None)
            panel.hide()
            win_close_manage(frame, STATE_MODULE, None)
        finally:
            view._state_closing = False
        event.accept()

    frame.closeEvent = types.MethodType(on_close, frame)
    return frame


def _close_state_window(view):
    frame = getattr(view, "state_frame", None)
    if frame is not None:
        view.state_frame = None
        win_close_manage(frame, STATE_MODULE, None)


def _close_turns_window(view):
    frame = getattr(view, "turns_frame", None)
    if frame is not None:
        view.turns_frame = None
        win_close_manage(frame, TURNS_MODULE, None)


def creat_axle_od_win():
    global _active_view
    # 使用说明输出到 工具/排轴/help.txt
    write_help_file()

    if is_win_open(WINDOW_TITLE, MODULE_NAME):
        win_set_top(WINDOW_TITLE, MODULE_NAME)
        if _active_view is not None:
            _open_turns_window(_active_view)
            win_set_top(TURNS_TITLE, TURNS_MODULE)
        return "break"

    win_frame = creat_Toplevel(WINDOW_TITLE, 780, 400, 75, 40)
    set_window_icon(win_frame, "./工具/help.png")

    view = AxleODWindow(win_frame.centralWidget())
    win_frame.grid_layout.addWidget(view, 0, 0)
    win_frame.grid_layout.setRowStretch(0, 1)
    win_frame.grid_layout.setColumnStretch(0, 1)

    _active_view = view
    win_open_manage(win_frame, MODULE_NAME)
    _open_turns_window(view)

    def on_close(self, event):
        global _active_view
        _active_view = None
        _close_turns_window(view)
        _close_state_window(view)
        win_close_manage(win_frame, MODULE_NAME, view)
        event.accept()

    win_frame.closeEvent = types.MethodType(on_close, win_frame)

    return "break"

