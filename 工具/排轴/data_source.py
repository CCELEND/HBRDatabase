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

# 已「通用化」的技能：不再视为专属技能，可被同角色其它风格使用
GENERALIZED_SKILLS = {
    "星火燎原+",   # 茅森月歌
}

# SP 类被动里，排轴无法判定的条件——描述中出现任一关键词即整条跳过（避免多算）。
# 目前可判定的条件：位于前锋/后卫、回合开始时、战斗开始时、SP不大于N、超频条（未判定）。
_SP_CONDITION_SKIP = (
    "状态", "加护", "充能", "领域", "展开", "印", "信念", "士气", "仆人",
    "干劲", "倒地", "破坏率", "DP", "SP提升", "解除", "EX技能", "战斗胜利",
    "击败", "击破", "破盾", "伤害", "追击", "发动", "追加回合",
)


def _sp_condition_ok(desc):
    """SP 类被动的条件是否可判定（否则跳过）。"""
    return not any(k in str(desc) for k in _SP_CONDITION_SKIP)


def _sp_below(desc):
    """解析「SP不大于N」条件；无则返回 None。"""
    m = re.search(r'SP不大于(\d+)', str(desc))
    return int(m.group(1)) if m else None


def _apply_exclusive(styles):
    """标记 SSR/SS 的第一个主动技能为专属技能。

    例外（已通用化，不再算专属）：
      * 该角色第一个 SS 风格（style_id 最小）的专属技能；
      * GENERALIZED_SKILLS 中列出的技能。
    """
    ss_styles = [s for s in styles if s.rarity == "SS" and s.style_id]
    first_ss = min(ss_styles, key=lambda s: s.style_id) if ss_styles else None
    for style in styles:
        if style.rarity not in ("SSR", "SS") or len(style.skills) < 2:
            continue
        skill = style.skills[1]      # skills[0] 为通常攻击
        skill.is_exclusive = True
        if skill.name in GENERALIZED_SKILLS or style is first_ss:
            skill.is_exclusive = False


def _dedupe(items):
    """按值去重并保持顺序。"""
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def _share_style_forms(styles):
    """让「同一风格的不同形态」共享技能与被动。

    如 CODE:Virtual Killer / CODE:Virtual Killer2：数据显示为两条记录
    （style_label 带 Another），实为同一风格可在战斗中自由切换的两种形态，
    因此两者的技能、被动、OD/SP 相关效果取并集。
    """
    by_label = {}
    for style in styles:
        if style.style_label:
            by_label.setdefault(style.style_label, style)
    for style in styles:
        label = style.style_label or ""
        if "Another" not in label:
            continue
        base = by_label.get(label.replace("Another", ""))
        if base is None or base is style:
            continue
        _merge_forms(base, style)


def _merge_forms(a, b):
    """把 a、b 两个形态的内容取并集后写回双方。"""
    # 技能：按名称去重，保留原对象的专属标记
    merged_skills = []
    seen = set()
    for skill in list(a.skills) + list(b.skills):
        if skill.name not in seen:
            seen.add(skill.name)
            merged_skills.append(skill)
    a.skills = list(merged_skills)
    b.skills = list(merged_skills)
    # 被动类字段：并集（去重）
    for attr in ("front_sp_passives", "turn_start_od", "turn_start_sp",
                 "break_sp", "sp_cost_mods", "break_od"):
        combined = []
        for mod in list(getattr(a, attr)) + list(getattr(b, attr)):
            if mod not in combined:
                combined.append(mod)
        setattr(a, attr, list(combined))
        setattr(b, attr, list(combined))
    options = _dedupe(list(a.passive_options) + list(b.passive_options))
    a.passive_options = list(options)
    b.passive_options = list(options)
    limit = max(a.sp_limit_override or 0, b.sp_limit_override or 0) or None
    a.sp_limit_override = limit
    b.sp_limit_override = limit
    enabler = a.boost_enabler or b.boost_enabler
    a.boost_enabler = enabler
    b.boost_enabler = enabler


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
                 sp_recover=0, sp_recover_scope=None, sp_recover_element=None,
                 sp_break_recover=0, sp_break_scope=None, element=None,
                 od_down_fixed=0.0, is_exclusive=False, od_up_fixed=0.0,
                 sp_cost_alt=None, sp_cost_cond=None, od_up_on_break=False,
                 od_up_earring=False):
        self.name = name
        self.hits = hits                              # 技能原始Hit数，攻击技能才有
        self.element = element                        # 攻击效果的元素属性
        # 专属技能（SSR/SS 的第一个主动技能）：仅在装备该风格时可用
        self.is_exclusive = is_exclusive
        # 「OD条下降 X%」：该次行动 OD 固定减少 X（如 50% → 固定 −50）
        self.od_down_fixed = od_down_fixed or 0.0
        # 「OD条上升 X%」：该技能带来的超频条提升，按固定OD结算（X% → X/100）
        self.od_up_fixed = od_up_fixed or 0.0
        # 该「OD条上升」是否仅在「以此技能击破敌人」时触发
        self.od_up_on_break = od_up_on_break
        # 非攻击技能的「OD条上升」是否也按固定OD结算（吃 OD 耳环）；如 驱动增益
        self.od_up_earring = od_up_earring
        self.destructive_multiplier = destructive_multiplier  # 破坏倍率
        self.is_normal_attack = is_normal_attack      # 是否通常攻击
        self.sp_cost = sp_cost or 0                   # 消耗 SP（用于计算）
        self.sp_cost_note = sp_cost_note              # SP 原始写法（用于展示）
        # 有条件的 SP 消耗（如「存在处于倒地/超倒地状态的敌人时 SP消耗为0」）：
        # sp_cost_alt 为满足条件时的消耗，sp_cost_cond 为条件类型（目前仅 "downed"）
        self.sp_cost_alt = sp_cost_alt
        self.sp_cost_cond = sp_cost_cond
        self.sp_recover = sp_recover or 0             # 回复 SP 量
        # 回复范围：self/all/others/front/front_others/others_element/all_element
        self.sp_recover_scope = sp_recover_scope
        self.sp_recover_element = sp_recover_element  # 元素限定（如「火」）
        # 击破敌人时回复的 SP（如「攻击导致敌方破盾时回复8SP」）
        self.sp_break_recover = sp_break_recover or 0
        self.sp_break_scope = sp_break_scope

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
                "one_other": "单名其他友方", "one_any": "单名友方",
                "others_element": "全体其他%s属性风格" % (self.sp_recover_element or ""),
                "all_element": "全体%s属性风格" % (self.sp_recover_element or ""),
            }.get(self.sp_recover_scope, "")
            parts.append("回复 SP %d（%s）" % (self.sp_recover, scope_name))
        return "，".join(parts)

    def __repr__(self):
        return "SkillInfo(%r, hits=%r, sp=%r, recover=%r)" % (
            self.name, self.hits, self.sp_cost, self.sp_recover)


# 所有角色共有的通用技能（出击中每名角色都能使用）
GENERIC_SKILLS = [
    # 点数援助：自身 SP+3，消耗 SP1，使用次数1
    SkillInfo("点数援助", sp_cost=1, sp_cost_note="1",
              sp_recover=3, sp_recover_scope="self"),
    # 驱动增益：超频条（OD 槽）+15%（消耗 SP6，使用次数1）
    # 特殊：虽非攻击技能，但实测会吃 OD 耳环（按固定OD结算）
    SkillInfo("驱动增益", sp_cost=6, sp_cost_note="6", od_up_fixed=0.15,
              od_up_earring=True),
]


class StyleInfo:
    """风格及其技能列表。"""

    def __init__(self, name, skills, rarity=None, element=None, break_sp=None,
                 style_id=None, sp_cost_mods=None, sp_limit_override=None,
                 passive_options=None, boost_enabler=None,
                 front_sp_passives=None, turn_start_od=None,
                 turn_start_sp=None, style_label=None, break_od=None):
        self.name = name
        self.skills = skills
        self.rarity = rarity
        self.element = element    # 元素属性（火/冰/雷/光/暗/无…）
        # 击破敌人时回复 SP 的被动：[{amount, scope, first_only}, ...]
        self.break_sp = break_sp or []
        self.style_id = style_id  # 风格 ID（用于判断该角色第一个 SS 风格）
        # 风格内部标识（如 KAsakuraTwins_R3；用于识别「同一风格的不同形态」）
        self.style_label = style_label
        # 影响技能 SP 消耗的被动：[{name, amount(带符号), scope, element}, ...]
        self.sp_cost_mods = sp_cost_mods or []
        # SP 上限覆盖（如「SP上限变为30」）；需携带 boost_enabler 才生效
        self.sp_limit_override = sp_limit_override
        # 回合开始时「位于前锋则自身 SP+X」的被动（如 闪光/佳音/机敏/俊敏…）
        self.front_sp_passives = front_sp_passives or []
        # 回合开始时增加 OD 槽的被动（如 V字回复）：
        # [{name, amount, threshold, position, timing, once, lb}, ...]
        self.turn_start_od = turn_start_od or []
        # 击破敌人时增加 OD 槽的被动（如 托付给你了 / 势如破竹）：
        # [{name, amount, first_only, lb}, ...]
        self.break_od = break_od or []
        # 回合开始时回复友方 SP 的被动（如 与伙伴一起【朝仓可怜专属】）：
        # [{name, amount, scope, element, lb}, ...]
        self.turn_start_sp = turn_start_sp or []
        # 可在队伍配置里选择的「（被动技能）」条目名
        self.passive_options = passive_options or []
        # 「高阶增幅状态」的启用被动名（无则为 None）
        self.boost_enabler = boost_enabler

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
    # 单名友方（需要在行动里选择「对象」）
    "其他友方": ("one_other", None),
    "一名其他友方": ("one_other", None),
    "一名友方": ("one_any", None),
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
    sp_break_recover = 0
    sp_break_scope = None
    attack_element = None
    od_down_fixed = 0.0
    od_up_fixed = 0.0
    desc = ""
    sp_cost_alt = None
    sp_cost_cond = None
    od_up_on_break = False
    try:
        name = group[0][0]
        # group[0] = [技能名, 描述, SP消耗, 使用次数, ...]
        raw_sp = group[0][2] if len(group[0]) > 2 else None
        sp_cost, sp_cost_note = _parse_sp_cost(raw_sp)
        # 有条件的 SP 消耗（「N(M)」写法 + 描述含「倒地/倒下」）：
        # 较小值为「敌人处于倒地/超倒地状态」时的消耗
        desc = str(group[0][1]) if len(group[0]) > 1 else ""
        nums = [int(n) for n in re.findall(r'\d+', str(raw_sp))]
        if (len(nums) >= 2 and ("倒地" in desc or "倒下" in desc)
                and min(nums) != sp_cost):
            sp_cost_alt = min(nums)
            sp_cost_cond = "downed"
    except Exception:
        name = "?"

    effects = group[1] if len(group) > 1 and isinstance(group[1], list) else []
    for effect in effects:
        if not isinstance(effect, list) or not effect:
            continue
        # 攻击技能：取 Hit 数与破坏倍率
        if len(effect) > 2 and effect[0] in ATTACK_ATTRS:
            if len(effect) > 1 and effect[1]:
                attack_element = str(effect[1])
            try:
                hits = int(effect[2])
            except Exception:
                hits = None
            if len(effect) > 8:
                value = _parse_number(effect[8])
                destructive = float(value) if value is not None else None
            continue
        # OD 条下降（数据写作「OD条下降」）：固定下降值，如 50% → 固定 −50
        if (isinstance(effect[0], str) and effect[0].startswith("OD")
                and "下降" in effect[0] and len(effect) > 1):
            raw_down = str(effect[1])
            m = re.search(r'(\d+(?:\.\d+)?)', raw_down)
            if m:
                od_down_fixed = max(od_down_fixed, float(m.group(1)))
        # OD 条上升（数据写作「OD条上升」）：该技能带来的超频条提升，
        # 按固定OD结算（如 50% → 固定OD 0.50，会吃 OD 耳环加成）
        if (isinstance(effect[0], str) and effect[0].startswith("OD")
                and "上升" in effect[0] and len(effect) > 1):
            raw_up = str(effect[1])
            m = re.search(r'(\d+(?:\.\d+)?)', raw_up)
            if m:
                od_up_fixed = max(od_up_fixed, float(m.group(1)) / 100.0)
                # 「以此技能击破敌人时超频条+X%」：仅在勾选击破敌人时触发
                od_up_on_break = ("造成击破时" in desc or "击破敌人时" in desc)
        # 回复 SP：固定数值；或「攻击导致敌方破盾时回复8SP」这类击破触发
        if effect[0] == "回复SP" and len(effect) > 1:
            raw_value = str(effect[1])
            scope_info = _sp_recover_scope(
                effect[6] if len(effect) > 6 else None)
            try:
                amount = int(raw_value.strip())
            except Exception:
                amount = None
            if amount is not None and amount > 0 and scope_info:
                sp_recover = amount
                sp_scope, sp_element = scope_info
            elif (amount is None and scope_info
                  and ("破盾" in raw_value or "击破" in raw_value)):
                nums = re.findall(r'\d+', raw_value)
                if nums:
                    sp_break_recover = int(nums[-1])
                    sp_break_scope = scope_info[0]

    return SkillInfo(name, hits, destructive, False, sp_cost, sp_cost_note,
                     sp_recover, sp_scope, sp_element,
                     sp_break_recover, sp_break_scope, element=attack_element,
                     od_down_fixed=od_down_fixed, od_up_fixed=od_up_fixed,
                     sp_cost_alt=sp_cost_alt, sp_cost_cond=sp_cost_cond,
                     od_up_on_break=od_up_on_break)


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
                style_id = None
                if len(style_info) > 10 and isinstance(style_info[10], dict):
                    try:
                        style_id = int(next(iter(style_info[10].keys())))
                    except Exception:
                        style_id = None
                    style_label = next(iter(style_info[10].values()), None)
                else:
                    style_label = None
                def _passive_lb(passive):
                    try:
                        return int(str(passive[2]).strip() or 0)
                    except Exception:
                        return 0

                # 解析「击破敌人时回复SP」类被动
                break_sp = []
                for passive in (style_data.get("PassiveSkills") or []):
                    try:
                        pname = str(passive[0])
                        pdesc = str(passive[1])
                        ptype = str(passive[3]) if len(passive) > 3 else ""
                        pvalue = passive[4] if len(passive) > 4 else None
                        ptarget = passive[7] if len(passive) > 7 else None
                    except Exception:
                        continue
                    text = pname + pdesc
                    if ptype != "回复SP" or ("击破" not in text and "破盾" not in text):
                        continue
                    try:
                        amount = int(str(pvalue).strip())
                    except Exception:
                        amount = 0
                    scope_info = _sp_recover_scope(ptarget)
                    if amount > 0 and scope_info:
                        break_sp.append({
                            "amount": amount,
                            "scope": scope_info[0],
                            "first_only": "首次" in text,
                            "lb": _passive_lb(passive),
                        })
                # 「OD条上升」类被动（如 V字回复）：回合开始时增加 OD 槽。
                # 解析触发时机（回合开始/战斗开始）、位置（前锋/后卫）、
                # 阈值（超频条不足N%）、是否出击中1次；无法判定的条件跳过。
                turn_start_od = []
                break_od = []
                skip_od_keywords = ("解除", "EX技能",
                                    "SP提升", "仆人", "干劲", "DP", "领域")
                for passive in (style_data.get("PassiveSkills") or []):
                    try:
                        pname = str(passive[0])
                        pdesc = str(passive[1])
                        ptype = str(passive[3]) if len(passive) > 3 else ""
                        pvalue = passive[4] if len(passive) > 4 else None
                    except Exception:
                        continue
                    if ptype != "OD条上升":
                        continue
                    num = re.search(r'(\d+(?:\.\d+)?)', str(pvalue))
                    if not num:
                        continue
                    amount = float(num.group(1))
                    # 「击破敌人时」增加 OD 槽（如 托付给你了 / 势如破竹）
                    if "击破" in pdesc or "破盾" in pdesc:
                        break_od.append({
                            "name": pname,
                            "amount": amount,
                            "first_only": "首次" in pdesc,
                            "lb": _passive_lb(passive),
                        })
                        continue
                    if any(k in pdesc for k in skip_od_keywords):
                        continue
                    threshold = None
                    m = re.search(r'不足(\d+(?:\.\d+)?)%', pdesc)
                    if m:
                        threshold = float(m.group(1))
                    position = None
                    if "位于前锋" in pdesc:
                        position = "front"
                    elif "位于后卫" in pdesc:
                        position = "back"
                    timing = "battle" if "战斗开始时" in pdesc else "turn"
                    turn_start_od.append({
                        "name": pname,
                        "amount": amount,
                        "threshold": threshold,
                        "position": position,
                        "timing": timing,
                        "once": ("1次" in pdesc) or timing == "battle",
                        "lb": _passive_lb(passive),
                    })
                # 「回合开始时 / 战斗开始时」回复友方 SP 的被动（如 与伙伴一起）：
                # 「位于前锋 + 自身」类归入 front_sp_passives，其余按作用范围结算。
                turn_start_sp = []
                for passive in (style_data.get("PassiveSkills") or []):
                    try:
                        pname = str(passive[0])
                        pdesc = str(passive[1])
                        ptype = str(passive[3]) if len(passive) > 3 else ""
                        pvalue = passive[4] if len(passive) > 4 else None
                        ptarget = passive[7] if len(passive) > 7 else None
                    except Exception:
                        continue
                    if ptype != "回复SP":
                        continue
                    if ("回合开始时" not in pdesc
                            and "战斗开始时" not in pdesc
                            and "初战开始时" not in pdesc):
                        continue
                    if str(ptarget) == "自身" and "位于前锋" in pdesc:
                        continue          # 已由 front_sp_passives 处理
                    # 敌人处于倒地/被击破状态的回合开始时条件（如 算法）
                    downed_cond = "被击破的敌人" in pdesc
                    if not downed_cond and not _sp_condition_ok(pdesc):
                        continue
                    if (not downed_cond
                            and ("击破" in pdesc or "破盾" in pdesc or "击败" in pdesc)):
                        continue
                    num = re.search(r'\d+', str(pvalue))
                    scope_info = _sp_recover_scope(ptarget)
                    if not num or not scope_info:
                        continue
                    position = None
                    if "位于前锋" in pdesc:
                        position = "front"
                    elif "位于后卫" in pdesc:
                        position = "back"
                    turn_start_sp.append({
                        "name": pname,
                        "amount": int(num.group()),
                        "scope": scope_info[0],
                        "element": scope_info[1],
                        "position": position,
                        "battle_start": ("战斗开始时" in pdesc
                                         or "初战开始时" in pdesc),
                        "sp_below": _sp_below(pdesc),
                        "od_below": (lambda m: int(m.group(1)) if m else None)(
                            re.search(r'超频条不足(\d+)%', pdesc)),
                        "downed": downed_cond,
                        "once": "1次" in pdesc,
                        "lb": _passive_lb(passive),
                    })
                # 检测「高阶增幅状态」的启用被动（如 红宝石香水（被动技能））；
                # 只有存在该被动时，高阶增强的 SP+2 / SP上限+10 才生效。
                enables_boost = False
                boost_enabler = None
                sp_limit_override = None
                # 「（被动技能）」条目：可在队伍配置里选择携带（默认全选）
                passive_options = []
                for group in (style_data.get("ActiveSkills") or []):
                    try:
                        gname = str(group[0][0])
                        gtext = gname + str(group[0][1])
                    except Exception:
                        continue
                    if "（被动技能）" in gname or "(被动技能)" in gname:
                        passive_options.append(gname)
                        if "高阶增幅状态" in gtext:
                            enables_boost = True
                            boost_enabler = gname
                            m = re.search(r'SP上限变为(\d+)', gtext)
                            if m:
                                sp_limit_override = max(
                                    sp_limit_override or 0, int(m.group(1)))

                # 解析影响 SP 消耗的效果（降低/增加 SP 消耗；含「高阶增强」）
                sp_cost_mods = []
                added = set()

                def add_cost_mod(mod_name, amount, target, requires=None, lb=0,
                                 downed=False):
                    if not amount:
                        return
                    scope_info = _sp_recover_scope(target)
                    if not scope_info:
                        return
                    key = (mod_name, amount, scope_info[0])
                    if key in added:
                        return
                    added.add(key)
                    sp_cost_mods.append({
                        "name": mod_name,
                        "amount": amount,
                        "scope": scope_info[0],
                        "element": scope_info[1],
                        "requires": requires,   # 需携带的「（被动技能）」名
                        "lb": lb,               # 需要的突破数
                        "downed": downed,       # 需敌人处于倒地/被击破状态
                    })

                for passive in (style_data.get("PassiveSkills") or []):
                    try:
                        pname = str(passive[0])
                        pdesc = str(passive[1])
                        ptype = str(passive[3]) if len(passive) > 3 else ""
                        pvalue = passive[4] if len(passive) > 4 else None
                        ptarget = passive[7] if len(passive) > 7 else None
                    except Exception:
                        continue
                    if "SP" not in ptype or ("消耗" not in ptype and "消费" not in ptype):
                        continue
                    # 敌人处于倒地/被击破状态的条件（如 最佳位置）
                    downed_cond = ("倒地" in pdesc or "倒下" in pdesc
                                   or "被击破的敌人" in pdesc)
                    if not downed_cond and not _sp_condition_ok(pdesc):
                        continue
                    if any(k in ptype for k in ("降低", "减少", "下降")):
                        sign = -1
                    elif any(k in ptype for k in ("增加", "上升", "提高", "增")):
                        sign = 1
                    else:
                        continue
                    num = re.search(r'\d+', str(pvalue))
                    if num:
                        add_cost_mod(pname, sign * int(num.group()), ptarget,
                                     lb=_passive_lb(passive),
                                     downed=downed_cond)

                # 主动技能条目里也可能带效果（如「高阶增强」：SP消耗量增加N）
                for group in (style_data.get("ActiveSkills") or []):
                    effects = (group[1] if len(group) > 1
                               and isinstance(group[1], list) else [])
                    for eff in effects:
                        if not isinstance(eff, list) or not eff:
                            continue
                        etype = str(eff[0])
                        evalue = str(eff[1]) if len(eff) > 1 else ""
                        etarget = eff[6] if len(eff) > 6 else None
                        if enables_boost and ("高阶增强" in etype
                                              or "SP消耗量增加" in evalue):
                            num = re.search(r'SP消耗量增加(\d+)', evalue)
                            if num:
                                add_cost_mod("高阶增强", int(num.group(1)),
                                             etarget, requires=boost_enabler)
                # 「回合开始时位于前锋则自身 SP+X」的被动（闪光/佳音/机敏/俊敏…）
                front_sp_passives = []
                for passive in (style_data.get("PassiveSkills") or []):
                    try:
                        ptype = str(passive[3]) if len(passive) > 3 else ""
                        pvalue = passive[4] if len(passive) > 4 else None
                        ptarget = str(passive[7]) if len(passive) > 7 else ""
                        pdesc = str(passive[1])
                    except Exception:
                        continue
                    if ptype != "回复SP" or ptarget != "自身":
                        continue
                    if "位于前锋" not in pdesc:
                        continue
                    if not _sp_condition_ok(pdesc):
                        continue
                    num = re.search(r'\d+', str(pvalue))
                    if num:
                        ob = re.search(r'超频条不足(\d+)%', pdesc)
                        front_sp_passives.append({
                            "amount": int(num.group()),
                            "battle_start": ("战斗开始时" in pdesc
                                             or "初战开始时" in pdesc),
                            "sp_below": _sp_below(pdesc),
                            "od_below": int(ob.group(1)) if ob else None,
                            "lb": _passive_lb(passive),
                        })
                styles.append(StyleInfo(style_name, skills, rarity, element,
                                        break_sp, style_id, sp_cost_mods,
                                        sp_limit_override, passive_options,
                                        boost_enabler, front_sp_passives,
                                        turn_start_od, turn_start_sp,
                                        style_label, break_od))

        _apply_exclusive(styles)
        _share_style_forms(styles)
        self._style_cache[role_path] = styles
        return styles

    def styles_names(self, role_name):
        return [style.name for style in self.styles(role_name)]

    def skills(self, role_name, style_name):
        for style in self.styles(role_name):
            if style.name == style_name:
                return style.skills
        return []

    def available_skills(self, role_name, style_name):
        """该角色当前可用的技能列表。

        同角色各风格的技能通用；但 SSR/SS 的第一个主动技能为其专属，
        仅在装备该风格时可用。
        """
        styles = self.styles(role_name)
        result = []
        seen = set()

        def add(skill):
            # 「（被动技能）」属于被动，不作为可选行动技能
            if "（被动技能）" in skill.name or "(被动技能)" in skill.name:
                return
            if skill.name not in seen:
                seen.add(skill.name)
                result.append(skill)

        # 装备风格的技能（含其专属），排在最前
        equipped = None
        for style in styles:
            if style.name == style_name:
                equipped = style
                for skill in style.skills:
                    add(skill)
                break
        # 其它风格：只加入非专属技能
        for style in styles:
            if style is equipped:
                continue
            for skill in style.skills:
                if not skill.is_exclusive:
                    add(skill)
        # 所有角色共有的通用技能
        for skill in GENERIC_SKILLS:
            add(skill)
        return result


_default_source = None


def get_data_source():
    global _default_source
    if _default_source is None:
        _default_source = HBRDataSource()
    return _default_source
