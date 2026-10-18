# -*- coding: utf-8 -*-
"""排轴 → 轴图（PNG）。

把排轴存档（``AxleODWindow.to_dict()`` 的结构）画成一张可以直接分享的轴图，
样式参考 ``工具/排轴/hbr_axle.jpg``：

    ┌ 6 个角色头像（右上角突破数、左下角共鸣等级）──────────────┐
    │ Passive Skill  每名成员携带的被动                        │
    │ Skill          每名成员在这条轴里用到的技能              │
    ├──────────── 红色分隔线 ────────────────────────────────┤
    │ T1            行动1（头像 + 技能） 行动2 … 行动3 …      │
    │ 追加回合      …                                          │
    │ T1 Bonus 1    …（超频回合，深绿底）                      │
    └──────────────────────────────────────────────────────────┘

只依赖 PyQt5（QImage / QPainter），不创建窗口、不读界面控件状态，
输入就是存档 dict，方便单独测试与批量出图。
"""
import datetime
import os

from PyQt5.QtCore import QPointF, QRect, QRectF, Qt
from PyQt5.QtGui import (QColor, QFont, QFontDatabase, QFontMetrics, QImage,
                         QPainter, QPainterPath, QPen, QPixmap)

try:
    from 工具.排轴.data_source import get_data_source, talent_element_ok
except ImportError:                                  # 直接在本目录运行
    from data_source import get_data_source, talent_element_ok

# ----------------------------------------------------------------------------
# 版式常量（数值参考 hbr_axle.jpg，宽 1170）
# ----------------------------------------------------------------------------
BASE_WIDTH = 1340
COLUMN_GAP_LEFT = 176.0    # 左侧「Passive Skill / Skill」标签占的宽度
COLUMN_GAP_RIGHT = 20.0    # 右侧留白
PORTRAIT_D = 92            # 顶部头像直径
RESONANCE_ICON_D = 30      # 共鸣天赋所属风格的小缩略图边长
ACTION_PORTRAIT_D = 46     # 回合行里的小头像直径
TARGET_PORTRAIT_D = 35     # 回合行里「对象」小头像直径
LABEL_W = 176              # 回合行左侧标签宽度
ROW_H = 88                 # 回合行高

# 颜色
BG = "#0B0B0B"
PASSIVE_CHIP_BG = "#2D3951"
PASSIVE_CHIP_BORDER = "#41506E"
PASSIVE_CHIP_TEXT = "#C9CDD6"
PANEL_BG = "#241F1E"
SKILL_CHIP_BG = "#332B28"
SKILL_CHIP_BORDER = "#4C3E39"
SKILL_CHIP_TEXT = "#EAE6E2"
LABEL_PINK = "#EBB6B6"
SEP_RED = "#D64041"
ROW_COLORS = {
    "通常回合": "#000000",
    "追加回合": "#1E1E1E",
    "超频回合": "#2E3E34",
    "特殊回合": "#33281E",
    "占位回合": "#0F0F0F",
}
LABEL_WHITE = "#F3EAE7"
LABEL_GRAY = "#C6B6B0"
LABEL_GREEN = "#A9CFA9"
ROW_TEXT = "#F5F5F5"
FOOTER_TEXT = "#7A7A7A"

MAX_CHIP_W = 186           # 技能/被动芯片最大宽度（超出自动换行）
# 不是技能的「行动」：轴图里不显示、也不统计使用次数（和通常攻击一样）
NON_SKILL_ACTIONS = ("通常攻击", "指挥行动")
_FONT_FAMILIES = ["Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans CJK SC",
                  "Source Han Sans SC", "SimHei", "PingFang SC"]


# ----------------------------------------------------------------------------
# 小工具
# ----------------------------------------------------------------------------
def _font(size, bold=False):
    """取一个支持中文的字体（找不到就退回默认字体）。"""
    families = set(QFontDatabase().families())
    for name in _FONT_FAMILIES:
        if name in families:
            f = QFont(name)
            break
    else:
        f = QFont()
    f.setPixelSize(int(size))
    f.setBold(bool(bold))
    return f


def _color(value, alpha=None):
    c = QColor(value)
    if alpha is not None:
        c.setAlpha(int(alpha))
    return c


def _load_image(path, size):
    """读图片并裁成正方形（用于圆形头像）；失败返回 None。"""
    if not path or not os.path.exists(path):
        return None
    pm = QPixmap(path)
    if pm.isNull():
        return None
    if pm.width() != pm.height():
        side = min(pm.width(), pm.height())
        x = (pm.width() - side) // 2
        y = (pm.height() - side) // 2
        pm = pm.copy(x, y, side, side)
    return pm.scaled(int(size), int(size), Qt.KeepAspectRatio,
                     Qt.SmoothTransformation)


def _draw_round(painter, rect, pixmap, border_alpha=40):
    """在 rect 里画圆形头像；pixmap 为空时画一个占位圆。"""
    path = QPainterPath()
    path.addEllipse(rect)
    painter.save()
    painter.setClipPath(path)
    if pixmap is not None and not pixmap.isNull():
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.drawPixmap(rect.toRect(), pixmap)
    else:
        painter.fillPath(path, _color("#3A3A3A"))
    painter.restore()
    painter.setPen(QPen(_color("#FFFFFF", border_alpha), 2))
    painter.setBrush(Qt.NoBrush)
    painter.drawEllipse(rect.adjusted(1, 1, -1, -1))


def _draw_thumb(painter, rect, pixmap, radius=7, border_alpha=90):
    """圆角方形缩略图（用于「共鸣天赋所属风格」的小图标）。"""
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    painter.save()
    painter.setClipPath(path)
    if pixmap is not None and not pixmap.isNull():
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.drawPixmap(rect.toRect(), pixmap)
    else:
        painter.fillPath(path, _color("#33373F"))
    painter.restore()
    painter.setPen(QPen(_color("#FFFFFF", border_alpha), 1))
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(rect, radius, radius)


def _wrapped_size(fm, text, max_width):
    """按最大宽度换行后的尺寸。"""
    rect = fm.boundingRect(QRect(0, 0, int(max_width), 10000),
                           Qt.TextWordWrap | Qt.AlignHCenter, text)
    return rect.width(), rect.height()


def _draw_chip(painter, center_x, top, text, fill, border, color,
               font, pad_x=14, pad_y=7, radius=8, max_width=MAX_CHIP_W):
    """画一个居中的圆角芯片，返回它的高度。

    宽度：能一行放下就用文字实际宽度，否则用满 max_width 并自动换行。
    高度：按 QFontMetrics 量出来的换行行数（只多不少），保证文字装得下。
    """
    painter.setFont(font)
    fm = QFontMetrics(font)
    adv = fm.horizontalAdvance(text)
    if adv + 2 * pad_x <= max_width:
        w = adv + 2 * pad_x
        h = fm.height() + 2 * pad_y
    else:
        w = max_width
        _tw, th = _wrapped_size(fm, text, max_width - 2 * pad_x)
        h = max(fm.height(), th) + 2 * pad_y
    rect = QRectF(center_x - w / 2.0, top, w, h)
    painter.setPen(QPen(_color(border), 1))
    painter.setBrush(_color(fill))
    painter.drawRoundedRect(rect, radius, radius)
    painter.setPen(_color(color))
    painter.save()
    painter.setClipRect(rect)
    painter.drawText(rect, Qt.TextWordWrap | Qt.AlignCenter, text)
    painter.restore()
    return h


def _badge_metrics(text, radius, font=None):
    """徽章的 (宽, 高)：宽度按文字长度算，至少是 radius*2。"""
    font = font or _font(19, True)
    fm = QFontMetrics(font)
    w = max(radius * 2, fm.horizontalAdvance(str(text)) + 14 * 2)
    return w, radius * 2


def _badge(painter, center, text, dark=True, radius=15):
    """头像上的小徽章（突破 / 共鸣）。"""
    text = str(text)
    font = _font(19, True)
    painter.setFont(font)
    w, h = _badge_metrics(text, radius, font)
    rect = QRectF(center[0] - w / 2.0, center[1] - radius, w, h)
    if dark:
        painter.setBrush(_color("#1C1C1C", 235))
        painter.setPen(QPen(_color("#FFFFFF", 130), 1))
        painter.drawRoundedRect(rect, radius, radius)
        painter.setPen(_color("#FFFFFF"))
    else:
        painter.setBrush(_color("#EFEFF2", 240))
        painter.setPen(QPen(_color("#FFFFFF", 200), 1))
        painter.drawRoundedRect(rect, radius, radius)
        painter.setPen(_color("#1A1A1A"))
    painter.drawText(rect, Qt.AlignCenter, text)


# ----------------------------------------------------------------------------
# 数据整理
# ----------------------------------------------------------------------------
def _style_of(ds, role, style):
    if not role:
        return None
    try:
        for st in ds.styles(role):
            if st.name == style:
                return st
    except Exception:
        return None
    return None


def _icon_path(ds, role, style):
    st = _style_of(ds, role, style)
    icon = getattr(st, "icon_path", None) if st is not None else None
    if not icon:
        return None
    return os.path.join(ds.base_dir, str(icon).lstrip("./"))


def _skill_order(ds, role, style):
    """该风格技能在游戏里的顺序（用于「Skill」栏排序）。"""
    st = _style_of(ds, role, style)
    if st is None:
        return {}
    return {sk.name: i for i, sk in enumerate(getattr(st, "skills", []) or [])}


def _split_od(text):
    """把 "OD2/Bonus1" 拆成 (2, 1)；解析失败返回 (None, None)。"""
    level = bonus = None
    for part in str(text or "").replace("／", "/").split("/"):
        part = part.strip()
        low = part.lower()
        if low.startswith("od"):
            try:
                level = int(part[2:].strip())
            except ValueError:
                level = None
        elif low.startswith("bonus"):
            try:
                bonus = int(part[5:].strip())
            except ValueError:
                bonus = None
    return level, bonus


def _resonance_icon(ds, talent_name, element=None):
    """共鸣天赋「所属风格」的缩略图路径（找不到返回 None）。

    同名天赋可能有多个来源风格（不同属性），优先取**属性与 element 相符**的那一个
    （和下拉标签的取法一致），例如 SSR·无 的 Excelsior! 取「绚烂华美琉璃色」。
    """
    if not talent_name:
        return None
    try:
        entry = (ds.resonance_pool() or {}).get(str(talent_name)) or {}
    except Exception:
        return None
    sources = entry.get("sources") or []
    picked = None
    for src in sources:
        # element=None 表示「无」属性，交给同一个匹配规则判断
        if talent_element_ok([src.get("element") or "无"], element):
            picked = src
            break
    if picked is None and sources:
        picked = sources[0]
    icon = (picked or {}).get("icon_path") or entry.get("icon_path")
    if not icon:
        return None
    return os.path.join(ds.base_dir, str(icon).lstrip("./"))


def is_non_skill(name):
    """通常攻击 / 指挥行动 不是技能：**回合行照样显示**（它们也是行动），
    只是不进「Skill」栏、也不统计使用次数。"""
    return str(name or "").strip() in NON_SKILL_ACTIONS


def _clean_passive(name):
    """界面上被动名带「（被动技能）」后缀，轴图里去掉更清爽。"""
    text = str(name or "").strip()
    for suffix in ("（被动技能）", "(被动技能)", "（被动）"):
        if text.endswith(suffix):
            return text[: -len(suffix)].strip()
    return text


def collect_turn_rows(data):
    """把 turns 整理成 [(标签1, 标签2, 类型, [行动...]), ...]。

    行动 = {"member": 槽位, "skill": 技能名}。
    通常回合才占 T 序号（追加/特殊/占位不计），和排轴的规则一致。
    """
    rows = []
    turn_no = 0
    bonus_no = 0
    for turn in data.get("turns") or []:
        ttype = str(turn.get("type") or "通常回合")
        line1, line2 = "", ""
        if ttype == "通常回合":
            turn_no += 1
            line1 = "T%d" % turn_no
        elif ttype == "超频回合":
            bonus_no += 1
            level, bonus = _split_od(turn.get("od"))
            if bonus is None:
                bonus = bonus_no
            line1 = "T%d" % max(1, turn_no)
            line2 = ("OD%d · Bonus %d" % (level, bonus) if level
                     else "Bonus %d" % bonus)
        else:
            line1 = ttype
        actions = []
        for act in turn.get("actions") or []:
            skill = str(act.get("skill") or "").strip()
            if not skill:
                continue
            target = act.get("sp_target", None)
            if not isinstance(target, int) or isinstance(target, bool):
                target = None
            actions.append({"member": int(act.get("member", 0) or 0),
                            "skill": skill,
                            "target": target})
        rows.append({"line1": line1, "line2": line2, "type": ttype,
                     "actions": actions})
    return rows


def collect_member_skills(data, with_counts=False):
    """每名成员在整条轴里用到的技能（按游戏技能顺序，去重）。

    :param with_counts: True 时返回 ``[(技能名, 使用次数), ...]``（次数 >1 时轴图里显示成
                        ``名称[次数]``，如 ``放学后的小小刺激[2]``）。
    通常攻击 / 指挥行动 不是技能，**只不进 Skill 栏**（回合行仍会显示）。
    """
    team = data.get("team") or []
    used = [[] for _ in range(6)]
    counts = [{} for _ in range(6)]
    for turn in data.get("turns") or []:
        for act in turn.get("actions") or []:
            skill = str(act.get("skill") or "").strip()
            try:
                member = int(act.get("member", 0) or 0)
            except (TypeError, ValueError):
                member = 0
            if not skill or is_non_skill(skill) or not (0 <= member < 6):
                continue
            if skill not in used[member]:
                used[member].append(skill)
            counts[member][skill] = counts[member].get(skill, 0) + 1
    if with_counts:
        return [[(n, counts[i][n]) for n in used[i]] for i in range(6)], team
    return used[:max(6, len(team))][:6], team


# ----------------------------------------------------------------------------
# 渲染
# ----------------------------------------------------------------------------
def render_axle_image(data, ds=None, width=BASE_WIDTH):
    """把排轴数据画成 QImage（宽固定，高按内容自适应）。"""
    ds = ds or get_data_source()
    width = int(width)
    scale = width / float(BASE_WIDTH)

    team = list(data.get("team") or [])[:6]
    while len(team) < 6:
        team.append({})
    rows = collect_turn_rows(data)
    # 技能按游戏技能顺序排（和参考图一致），用过多次的显示成「名称[次数]」
    skills_with_counts, _ = collect_member_skills(data, with_counts=True)
    member_skills = []
    for i in range(6):
        pairs = list(skills_with_counts[i])
        order = _skill_order(ds, team[i].get("role"), team[i].get("style"))
        if order:
            pairs.sort(key=lambda p: order.get(p[0], len(order) + 1))
        member_skills.append([("%s[%d]" % (name, cnt)) if cnt > 1 else name
                              for name, cnt in pairs])
    # 被动名去掉「（被动技能）」后缀
    member_passives = [[_clean_passive(x) for x in (m.get("passives") or []) if x]
                       for m in team]
    col_span = width - COLUMN_GAP_LEFT - COLUMN_GAP_RIGHT * scale
    col_x = [COLUMN_GAP_LEFT + (i + 0.5) * col_span / 6.0 for i in range(6)]

    images = [_load_image(_icon_path(ds, m.get("role"), m.get("style")),
                          PORTRAIT_D * scale) for m in team]
    # 共鸣天赋「所属风格」的小缩略图（画在共鸣等级徽章左边）
    # 按该队员风格的属性挑来源（如 SSR·无 的 Excelsior! 取「绚烂华美琉璃色」的图）
    res_icons = []
    for m in team:
        st = _style_of(ds, m.get("role"), m.get("style"))
        res_icons.append(_load_image(
            _resonance_icon(ds, m.get("resonance_talent"),
                            getattr(st, "element", None)),
            RESONANCE_ICON_D * scale))
    action_images = {}

    def action_pixmap(member):
        if member not in action_images:
            action_images[member] = _load_image(
                _icon_path(ds, team[member].get("role"),
                           team[member].get("style")),
                ACTION_PORTRAIT_D * scale)
        return action_images[member]

    # ---- 预先量一遍，算出总高度 ----
    f_passive = _font(19 * scale, True)
    f_skill = _font(19 * scale, True)
    f_row = _font(21 * scale, True)
    f_label = _font(26 * scale, True)
    f_label_s = _font(20 * scale, True)
    passive_h = 0
    for i, m in enumerate(team):
        passives = member_passives[i]
        h = 0
        for p in passives:
            _w, th = _wrapped_size(QFontMetrics(f_passive), p,
                                   MAX_CHIP_W * scale - 28 * scale)
            h += th + 14 * scale + 6 * scale
        passive_h = max(passive_h, h)

    panel_h = 0
    for i in range(6):
        h = 8 * scale
        for name in member_skills[i]:
            _w, th = _wrapped_size(QFontMetrics(f_skill), name,
                                   MAX_CHIP_W * scale - 28 * scale)
            h += th + 14 * scale + 8 * scale
        panel_h = max(panel_h, h)

    header_h = (14 + PORTRAIT_D + 26) * scale
    passive_row_h = max(46 * scale, passive_h + 18 * scale) if passive_h else 40 * scale
    panel_top = header_h + passive_row_h
    panel_h = max(panel_h, 46 * scale)
    sep_y = panel_top + panel_h + 16 * scale
    rows_top = sep_y + 12 * scale
    total_h = rows_top + ROW_H * len(rows) * scale + 46 * scale

    image = QImage(int(width), int(total_h), QImage.Format_ARGB32)
    image.fill(_color(BG))
    p = QPainter(image)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.TextAntialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)

    # ---- 顶部：头像 + 徽章 ----
    cy = 14 * scale + PORTRAIT_D * scale / 2.0
    for i, m in enumerate(team):
        d = PORTRAIT_D * scale
        rect = QRectF(col_x[i] - d / 2.0, cy - d / 2.0, d, d)
        _draw_round(p, rect, images[i])
        lb = m.get("lb")
        if lb is not None and m.get("role"):
            _badge(p, (rect.center().x() + d * 0.34, rect.center().y() - d * 0.34),
                   int(lb), dark=True, radius=15 * scale)
        res_lv = m.get("resonance_level")
        if m.get("resonance_talent") and res_lv is not None:
            by = rect.center().y() + d * 0.34
            bx = rect.center().x() - d * 0.24
            bw, _bh = _badge_metrics(str(int(res_lv)), 13 * scale)
            iw = RESONANCE_ICON_D * scale
            ix = bx - bw / 2.0 - 6 * scale - iw / 2.0
            _draw_thumb(p, QRectF(ix - iw / 2.0, by - iw / 2.0, iw, iw),
                        res_icons[i], radius=7 * scale)
            _badge(p, (bx, by), int(res_lv), dark=False, radius=13 * scale)

    # ---- Passive Skill ----
    label_font = _font(24 * scale, True)
    p.setFont(label_font)
    p.setPen(_color(LABEL_WHITE))
    passive_top = header_h + 2 * scale
    p.drawText(QRectF(36 * scale, passive_top, 140 * scale, 60 * scale),
               Qt.AlignLeft | Qt.AlignVCenter, "Passive\nSkill")
    y = passive_top + 6 * scale
    for i, m in enumerate(team):
        cy2 = y
        for name in member_passives[i]:
            ch = _draw_chip(p, col_x[i], cy2, name, PASSIVE_CHIP_BG,
                            PASSIVE_CHIP_BORDER, PASSIVE_CHIP_TEXT,
                            f_passive, max_width=MAX_CHIP_W * scale)
            cy2 += ch + 6 * scale

    # ---- Skill 面板 ----
    panel_rect = QRectF(14 * scale, panel_top, width - 28 * scale, panel_h)
    p.setPen(Qt.NoPen)
    p.setBrush(_color(PANEL_BG))
    p.drawRoundedRect(panel_rect, 12 * scale, 12 * scale)
    p.setFont(label_font)
    p.setPen(_color(LABEL_PINK))
    p.drawText(QRectF(36 * scale, panel_top, 120 * scale, panel_h),
               Qt.AlignLeft | Qt.AlignVCenter, "Skill")
    for i in range(6):
        cy2 = panel_top + 9 * scale
        for name in member_skills[i]:
            ch = _draw_chip(p, col_x[i], cy2, name, SKILL_CHIP_BG,
                            SKILL_CHIP_BORDER, SKILL_CHIP_TEXT, f_skill,
                            max_width=MAX_CHIP_W * scale)
            cy2 += ch + 8 * scale

    # ---- 红色分隔线（带一点辉光） ----
    for k in range(6):
        alpha = 26 - k * 4
        if alpha <= 0:
            continue
        p.setPen(QPen(_color(SEP_RED, alpha), 2 * scale))
        yy = sep_y - (k + 1) * 2 * scale
        p.drawLine(QPointF(0, yy), QPointF(width, yy))
    p.setPen(QPen(_color(SEP_RED), 3 * scale))
    p.drawLine(QPointF(0, sep_y), QPointF(width, sep_y))

    # ---- 回合行 ----
    row_h = ROW_H * scale
    col_w = (width - LABEL_W * scale) / 3.0
    for r, row in enumerate(rows):
        top = rows_top + r * row_h
        p.fillRect(QRectF(0, top, width, row_h),
                   _color(ROW_COLORS.get(row["type"], "#000000")))
        # 左侧标签
        if row["line2"]:
            p.setFont(f_label)
            p.setPen(_color(LABEL_WHITE))
            p.drawText(QRectF(30 * scale, top + 6 * scale,
                              LABEL_W * scale - 30 * scale, row_h / 2),
                       Qt.AlignLeft | Qt.AlignVCenter, row["line1"])
            p.setFont(f_label_s)
            p.setPen(_color(LABEL_GREEN))
            p.drawText(QRectF(30 * scale, top + row_h / 2 - 2 * scale,
                              LABEL_W * scale - 24 * scale, row_h / 2),
                       Qt.AlignLeft | Qt.AlignVCenter, row["line2"])
        else:
            big = row["type"] == "通常回合"
            p.setFont(f_label if big else f_label_s)
            p.setPen(_color(LABEL_WHITE if big else LABEL_GRAY))
            p.drawText(QRectF(30 * scale, top, LABEL_W * scale - 30 * scale,
                              row_h),
                       Qt.AlignLeft | Qt.AlignVCenter, row["line1"])
        # 3 个行动
        for c, act in enumerate(row["actions"][:3]):
            x0 = LABEL_W * scale + c * col_w
            d = ACTION_PORTRAIT_D * scale
            cx = x0 + 18 * scale + d / 2.0
            rect = QRectF(cx - d / 2.0, top + (row_h - d) / 2.0, d, d)
            _draw_round(p, rect, action_pixmap(act["member"]), border_alpha=30)
            p.setFont(f_row)
            p.setPen(_color(ROW_TEXT))
            text_w = col_w - d - 40 * scale
            label = QFontMetrics(f_row).elidedText(
                act["skill"], Qt.ElideRight, int(max(40, text_w)))
            p.drawText(QRectF(rect.right() + 16 * scale, top, text_w, row_h),
                       Qt.AlignLeft | Qt.AlignVCenter, label)
            # 「对象」：单名友方技能（回复SP / 连击数上升）的目标头像，画在技能名右边
            tgt = act.get("target")
            if isinstance(tgt, int) and 0 <= tgt < 6:
                tw = QFontMetrics(f_row).horizontalAdvance(label)
                td = TARGET_PORTRAIT_D * scale
                tx = rect.right() + 16 * scale + tw + 8 * scale + td / 2.0
                if tx + td / 2.0 <= x0 + col_w:
                    _draw_round(p, QRectF(tx - td / 2.0,
                                          top + (row_h - td) / 2.0, td, td),
                                action_pixmap(tgt), border_alpha=30)

    # ---- 页脚 ----
    p.setFont(_font(14 * scale))
    p.setPen(_color(FOOTER_TEXT))
    foot_top = rows_top + len(rows) * row_h + 12 * scale
    p.drawText(QRectF(20 * scale, foot_top, width / 2.0, 22 * scale),
               Qt.AlignLeft | Qt.AlignVCenter, "HBRDatabase · 排轴 OD 计算")
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    p.drawText(QRectF(width / 2.0, foot_top, width / 2.0 - 20 * scale,
                      22 * scale),
               Qt.AlignRight | Qt.AlignVCenter, stamp)
    p.end()
    return image


def save_image(image, path):
    """把 QImage 存成图片（按扩展名选格式），返回路径。"""
    ext = os.path.splitext(path)[1].lower() or ".png"
    fmt = {".jpg": "JPG", ".jpeg": "JPG", ".bmp": "BMP",
           ".webp": "WEBP"}.get(ext, "PNG")
    if not image.save(path, fmt):
        raise IOError("保存图片失败：%s" % path)
    return path


def save_axle_image(data, path, ds=None, width=BASE_WIDTH):
    """渲染并保存成图片，返回路径。"""
    return save_image(render_axle_image(data, ds=ds, width=width), path)
