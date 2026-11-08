# -*- coding: utf-8 -*-
"""排轴中的状态跟踪。"""

# 「状态」的显示名（内部键 → 游戏内名称）
STATE_DISPLAY = {
    "歌姬": "歌姬之加护",
    "仆人": "山胁大人的仆人",
    "干劲": "干劲",
}

# 状态对计算的实际影响（只写工具**已建模**的效果，供「状态总览」展示）
STATE_EFFECT_TEXT = {
    "歌姬": "月芒→连击+3（特大/3次）；共鸣 前锋SP+2；绝唱 自身消耗SP-2",
    "仆人": "「处于该状态的友方 SP+N」；「处于该状态的友方≥N名」的 OD/被动条件",
    "干劲": "「干劲为极佳的友方SP+1」「自身干劲良好以上SP+1」等被动据此判定",
}


class _StateTracker:
    """跟踪技能赋予的「状态」（如 歌姬之加护）。

    技能可以给（自己/前锋/全体友方…）附加持续 N 个己方回合的状态，
    带状态条件的技能与被动（如 月芒、共鸣、绝唱）据此切换效果。
    各计算阶段（SP / OD）各自按回合顺序推进一个实例即可。
    """

    def __init__(self, owner):
        self.owner = owner
        self.until = {}      # {(slot, 状态名): 生效到的回合下标（含）}
        self.active = {}     # {slot: {状态名}} 当前状态（本回合内随行动更新）
        self.sources = {}    # {(slot, 状态名): 来源描述}（供状态总览展示）

    def begin_turn(self, turn_idx):
        """进入新回合：按已记录的到期时间刷新当前状态。"""
        self.active = {}
        for slot in self.owner._active_slots():
            names = {n for (s, n), u in self.until.items()
                     if s == slot and turn_idx <= u}
            if names:
                self.active[slot] = names

    def states(self, slot):
        """该队员当前所处的状态集合（无则 None）。"""
        return self.active.get(slot)

    def apply(self, action, turn_idx, turn_front):
        """结算该行动赋予的状态（同回合之后的行动即可见）。"""
        skill = action._find_skill()
        for grant in (getattr(skill, "state_grants", None) or []):
            targets = self.owner._scope_targets(
                grant.get("scope"), grant.get("element"),
                action.member_index, self.owner._active_slots(), turn_front)
            label = getattr(skill, "name", "") or "技能"
            src_role = ""
            if (action.member_index is not None
                    and 0 <= action.member_index < len(self.owner.team)):
                src_role = self.owner.team[action.member_index].get("role") or ""
            source = "%s（%s）" % (label, src_role) if src_role else label
            for tgt in targets:
                self.until[(tgt, grant["state"])] = (
                    turn_idx + max(1, grant.get("duration", 1)) - 1)
                self.active.setdefault(tgt, set()).add(grant["state"])
                self.sources[(tgt, grant["state"])] = source
