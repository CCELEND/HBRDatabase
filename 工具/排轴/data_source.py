# -*- coding: utf-8 -*-
"""
排轴数据源

从本地游戏资料中读取 队伍 / 角色 / 风格 / 技能，
用于排轴界面的下拉选择，并在选中技能时自动带出
「技能原始Hit数」等信息（对应 OD 计算表的 B16）。

数据来源：
    ./角色/teams.json                  队伍与角色列表
    ./角色/<队伍>/<角色>/<稀有度>styles.json   风格与技能
"""

import os
import re
import json

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)

ATTACK_ATTRS = ("斩", "突", "打")
RARITY_FILES = ("SSRstyles.json", "SSstyles.json", "Sstyles.json", "Astyles.json")

# 通常攻击：所有风格都拥有，默认 3 Hit，不享受 OD 耳环加成
NORMAL_ATTACK_NAME = "通常攻击"
NORMAL_ATTACK_HITS = 3


def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("读取 %s 失败: %s", path, e)
        return None


class SkillInfo:
    """技能简要信息。"""

    def __init__(self, name, hits=None, destructive_multiplier=None,
                 is_normal_attack=False, sp_cost=0, sp_cost_note=None,
                 sp_recover=0, sp_recover_scope=None, sp_recover_element=None):
        self.name = name
        self.hits = hits                              # 技能原始Hit数，攻击技能才有
        self.destructive_multiplier = destructive_multiplier  # 破坏倍率
        self.is_normal_attack = is_normal_attack      # 是否通常攻击
        self.sp_cost = sp_cost or 0                   # 消耗 SP（用于计算）
        self.sp_cost_note = sp_cost_note              # SP 原始写法（用于展示）
        self.sp_recover = sp_recover or 0             # 回复 SP 量
        # 回复范围：self/all/others/front/front_others/others_element/all_element
        self.sp_recover_scope = sp_recover_scope
        self.sp_recover_element = sp_recover_element  # 元素限定（如「火」）

    def _sp_display(self):
        note = self.sp_cost_note
        if not note:
            return None
        upper = note.upper()
        if "TOKEN" in upper or upper.startswith("EP") or "全部" in note:
            return note
        return "SP" + note

    def display_name(self):
        """下拉列表中展示的名称，附带 SP 消耗。"""
        label = self._sp_display()
        return "%s（%s）" % (self.name, label) if label else self.name

    def sp_tooltip(self):
        parts = []
        label = self._sp_display()
        if label:
            parts.append("消耗 %s" % label)
        if self.sp_recover:
            scope_name = {
                "self": "自身", "all": "全体友方",
                "others": "全体其他友方", "front": "前锋",
                "front_others": "前锋其他友方",
                "others_element": "全体其他%s属性风格" % (self.sp_recover_element or ""),
                "all_element": "全体%s属性风格" % (self.sp_recover_element or ""),
            }.get(self.sp_recover_scope, "")
            parts.append("回复 SP %d（%s）" % (self.sp_recover, scope_name))
        return "，".join(parts)

    def __repr__(self):
        return "SkillInfo(%r, hits=%r, sp=%r, recover=%r)" % (
            self.name, self.hits, self.sp_cost, self.sp_recover)


class StyleInfo:
    """风格及其技能列表。"""

    def __init__(self, name, skills, rarity=None, element=None):
        self.name = name
        self.skills = skills
        self.rarity = rarity
        self.element = element    # 元素属性（火/冰/雷/光/暗/无…）

    def display_name(self):
        """下拉列表中展示的名称，如「谨记死亡的美少女-SS」。"""
        if self.rarity:
            return "%s-%s" % (self.name, self.rarity)
        return self.name

    def __repr__(self):
        return "StyleInfo(%r, %r, %d skills)" % (
            self.rarity, self.name, len(self.skills))


_SP_SCOPE_FIXED = {
    "自身": ("self", None),
    "全体友方": ("all", None),
    "全体其他友方": ("others", None),
    "前锋": ("front", None),
    "前锋其他友方": ("front_others", None),
}


def _parse_number(text):
    """从字符串中取第一个数字，返回 int/float，取不到返回 None。"""
    if text is None:
        return None
    match = re.search(r'\d+(?:\.\d+)?', str(text))
    if not match:
        return None
    token = match.group()
    return float(token) if "." in token else int(token)


def _parse_sp_cost(raw):
    """解析 SP 消耗，返回 (消耗值, 展示文本)。

    兼容数据中的多种写法：
        7  /  7(14) / (6)11     普通数值，括号内为另一种消耗
        TOKEN5 / 全部TOKEN      消耗 TOKEN（不消耗 SP）
        EP7 / EP8               消耗 EP（不消耗 SP）
        全部SP                  消耗全部 SP（用 99 表示）
    """
    if raw is None:
        return 0, None
    text = str(raw).strip()
    if not text:
        return 0, None
    upper = text.upper()
    if "TOKEN" in upper:
        return 0, text
    if upper.startswith("EP"):
        return 0, text
    if "全部SP" in text:
        return 99, text
    # 「7(14)」这类写法中，较大的数值是正常消耗，较小值是有条件/首次等折扣
    numbers = [int(n) for n in re.findall(r'\d+', text)]
    if not numbers:
        return 0, text
    return max(numbers), text


def _sp_recover_scope(target):
    """把效果的 target 映射为 (范围, 元素)。

    self           自身
    all            全体友方（含自身）
    others         全体其他友方（除自身外的所有友方）
    front          前锋（含自身）
    front_others   前锋其他友方（前锋中除自身外）
    others_element 全体其他{X}属性风格（除自身外该元素的友方）
    all_element    全体{X}属性风格（含自身该元素的友方）
    """
    if not target:
        return None
    if target in _SP_SCOPE_FIXED:
        return _SP_SCOPE_FIXED[target]
    # 全体其他火属性风格 / 全体光属性风格 之类
    if target.startswith("全体其他") and target.endswith("属性风格"):
        element = target[len("全体其他"):-len("属性风格")]
        if element:
            return ("others_element", element)
    if target.startswith("全体") and target.endswith("属性风格"):
        element = target[len("全体"):-len("属性风格")]
        if element:
            return ("all_element", element)
    return None


def _extract_skill(group):
    """从一个 ActiveSkills 条目中提取技能名、SP 消耗/回复与攻击信息。"""
    name = None
    hits = None
    destructive = None
    sp_cost = 0
    sp_cost_note = None
    sp_recover = 0
    sp_scope = None
    sp_element = None
    try:
        name = group[0][0]
        # group[0] = [技能名, 描述, SP消耗, 使用次数, ...]
        raw_sp = group[0][2] if len(group[0]) > 2 else None
        sp_cost, sp_cost_note = _parse_sp_cost(raw_sp)
    except Exception:
        name = "?"

    effects = group[1] if len(group) > 1 and isinstance(group[1], list) else []
    for effect in effects:
        if not isinstance(effect, list) or not effect:
            continue
        # 攻击技能：取 Hit 数与破坏倍率
        if len(effect) > 2 and effect[0] in ATTACK_ATTRS:
            try:
                hits = int(effect[2])
            except Exception:
                hits = None
            if len(effect) > 8:
                value = _parse_number(effect[8])
                destructive = float(value) if value is not None else None
            continue
        # 回复 SP：仅取可确定的固定数值（概率/条件类不解析）
        if effect[0] == "回复SP" and len(effect) > 1:
            try:
                amount = int(str(effect[1]).strip())
            except Exception:
                amount = 0
            scope_info = _sp_recover_scope(
                effect[6] if len(effect) > 6 else None)
            if amount > 0 and scope_info:
                sp_recover = amount
                sp_scope, sp_element = scope_info

    return SkillInfo(name, hits, destructive, False, sp_cost, sp_cost_note,
                     sp_recover, sp_scope, sp_element)


class HBRDataSource:
    """本地角色资料读取器（带缓存）。"""

    def __init__(self, base_dir=None):
        self.base_dir = base_dir or os.getcwd()
        self._roles = None          # [(team, role_name, role_path)]
        self._role_by_name = None   # {role_name: role_path}
        self._style_cache = {}      # {role_path: [StyleInfo]}

    def _teams_path(self):
        return os.path.join(self.base_dir, "角色", "teams.json")

    def load_roles(self):
        if self._roles is not None:
            return self._roles
        self._roles = []
        self._role_by_name = {}
        data = _load_json(self._teams_path())
        if not data:
            return self._roles
        for team_name, team_info in data.items():
            for role_name, role_dir in (team_info.get("roles") or {}).items():
                role_path = role_dir.get("path")
                if not role_path:
                    continue
                self._roles.append((team_name, role_name, role_path))
                self._role_by_name.setdefault(role_name, role_path)
        return self._roles

    def role_names(self):
        return [role_name for _, role_name, _ in self.load_roles()]

    def role_path(self, role_name):
        if self._role_by_name is None:
            self.load_roles()
        return self._role_by_name.get(role_name)

    def styles(self, role_name):
        """返回该角色的风格列表（按 SSR/SS/S/A 顺序去重）。"""
        role_path = self.role_path(role_name)
        if not role_path:
            return []
        if role_path in self._style_cache:
            return self._style_cache[role_path]

        styles = []
        seen = set()
        for rarity_file in RARITY_FILES:
            path = os.path.join(self.base_dir, role_path.lstrip("./"),
                                rarity_file)
            data = _load_json(path)
            if not data:
                continue
            for style_name, style_data in data.items():
                if style_name in seen:
                    continue
                seen.add(style_name)
                # style_info 结构：[path, team, role, name, nicknames,
                #                    description, rarity, career, ...]
                style_info = style_data.get("style_info") or []
                rarity = style_info[6] if len(style_info) > 6 else None
                element = style_info[9] if len(style_info) > 9 else None
                # 通常攻击为所有风格共有，置于技能列表最前
                skills = [SkillInfo(NORMAL_ATTACK_NAME, NORMAL_ATTACK_HITS,
                                    None, True)]
                for group in (style_data.get("ActiveSkills") or []):
                    skills.append(_extract_skill(group))
                styles.append(StyleInfo(style_name, skills, rarity, element))

        self._style_cache[role_path] = styles
        return styles

    def styles_names(self, role_name):
        return [style.name for style in self.styles(role_name)]

    def skills(self, role_name, style_name):
        for style in self.styles(role_name):
            if style.name == style_name:
                return style.skills
        return []


_default_source = None


def get_data_source():
    global _default_source
    if _default_source is None:
        _default_source = HBRDataSource()
    return _default_source
