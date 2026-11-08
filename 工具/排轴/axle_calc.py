# -*- coding: utf-8 -*-
"""排轴 OD 的核心计算逻辑（AxleODWindow 的 mixin）。"""

from contextlib import contextmanager
from 工具.排轴.axle_common import *
from 工具.排轴.axle_common import _element_matches, _talent_element_ok
from 工具.排轴.axle_state import (
    _StateTracker, STATE_DISPLAY, STATE_EFFECT_TEXT,
)

class AxleCalcMixin:
    """队伍/回合/SP/OD 的计算方法。"""

    def _battle_params(self, resistance=False, target_count=None):
        return ODBattle(
            target_count=(self.target_spin.value() if target_count is None
                          else target_count),
            resistance=resistance,
            other_od=self.other_od_spin.value(),
            enemy_od_rate=self.enemy_od_spin.value(),
        )

    def _resisted_elements(self):
        return {el for el, cb in self.resist_element_checks.items()
                if cb.isChecked()}

    @contextmanager
    def _suspend_recalc(self):
        """批量修改（读档 / 队伍批量同步）期间挂起重算，结束后只算一次。

        否则读一次档会触发几十次全量重算（实测 49 次 × ~13ms）。
        """
        self._recalc_suspend += 1
        try:
            yield
        finally:
            self._recalc_suspend -= 1
            if self._recalc_suspend <= 0:
                self._recalc_suspend = 0
                if self._recalc_pending:
                    self._recalc_pending = False
                    self.recalculate()

    def schedule_recalculate(self, *args):
        """防抖入口：连续调参时只在停顿后全量重算一次。"""
        if self._recalc_suspend:
            self._recalc_pending = True
            return
        self._recalc_timer.start(50)

    def recalculate(self):
        # 批量修改期间只登记待重算，避免反复全量计算
        if self._recalc_suspend:
            self._recalc_pending = True
            return
        self._recalc_timer.stop()
        self._rebuild_calc_caches()
        self._state_book = {}
        # 先结算一次 SP：「追击」及其 SP 消耗/回复会影响 OD，需要先算出来
        self._recalc_sp()

        blanket = self.resistance_check.isChecked()
        resisted = self._resisted_elements()
        cumulative = 0.0
        # 行动结束后的 OD 槽（= 初始OD + 累计获得 − 已发动消耗）
        running_od = float(self.initial_od_combo.currentData() or 0)
        consumed = 0.0
        prev_level = 0     # 上一次发动的 OD 等级（连续同等级视为同一次发动）
        od_gain_used = set()   # 已触发「OD条上升」被动的队员（出击中1次）
        start_front = self._initial_front()   # 回合开始时的前锋
        # 「X之律动」（超越条）：战斗开始时 = 15% × 该属性风格数（出击中限1次）；
        # 该属性风格行动后 +4%；达到 100% 时触发「OD条上升 100%」（出击中限1次）
        rhythm_state = {}
        for element, rhythm in self._team_rhythms().items():
            rhythm_state[element] = {
                "def": rhythm,
                "value": rhythm.get("initial_per_style", 15.0)
                * len(self._rhythm_members(element)),
                "triggered": False,
            }
        # 「连击数上升」buff（如 连结未来的苍之意志）：「己方回合」数消耗——
        # 通常/超频回合**所有队员**各 −1；追加/特殊回合只有**当回合出手的队员** −1
        combo_buffs = {}   # {slot: [{"amount","left","kind","source"}]}
        # 技能赋予的「状态」（如 若向流星歌唱 → 全体友方 歌姬之加护 N 回合）
        state_tracker = _StateTracker(self)
        # 「战斗/初战开始时 使自身进入X状态」（如 山胁大人的仆人/万岁）
        self._seed_battle_states(state_tracker)
        initial_front = self._initial_front()
        turn_states = {}      # {回合下标: {slot: 状态集合}}（回合**开始时**的快照）
        for turn_idx, turn in enumerate(self.turns):
            # 本回合行动过的队员（追加/特殊回合也算「己方回合」）
            actors = [a.member_index for a in turn.actions
                      if a.member_index is not None]
            turn_front = set(actors) or start_front
            state_tracker.begin_turn(turn_idx)
            # 记录本回合**开始时**的状态持有者（供 OD 的「仆人≥N名」条件）
            turn_states[turn_idx] = {
                slot: set(state_tracker.states(slot) or ())
                for slot in self._active_slots()}
            # 「状态总览」：记录该回合**开始时**的状态 / 连击 buff
            self._state_book[turn_idx] = self._snapshot_turn_states(
                turn_idx, state_tracker, combo_buffs)
            # 1) 被动类连击（如 山胁「梅雨」：战斗开始时位于前锋 连击+5（1次））
            for slot in self._active_slots():
                for mod in self._member_passive_combo(slot):
                    if mod.get("timing") == "battle" and turn_idx != 0:
                        continue
                    pos = mod.get("position")
                    if pos == "front" and slot not in initial_front:
                        continue
                    if pos == "back" and slot in initial_front:
                        continue
                    entries = combo_buffs.setdefault(slot, [])
                    # 「出击中仅1次」的被动、以及「持续+N」的**常驻**被动都只登记一次
                    if (mod.get("timing") == "battle"
                            or int(mod.get("count", 0) or 0) >= 999):
                        if any(e.get("source") == mod.get("name")
                               and e.get("passive") for e in entries):
                            continue
                    entries.append({
                        "amount": mod.get("amount", 0),
                        "left": mod.get("count", 0),
                        "kind": mod.get("kind", "turn"),
                        "source": mod.get("name"),
                        "passive": True,
                    })
            # 2) 本回合使用的「连击数上升」技能：当回合即生效
            for action in turn.actions:
                action.set_combo_grant_hint(None)
                skill_now = action._find_skill()
                states_now = state_tracker.states(action.member_index)
                buff = action.get_combo_buff(states_now)
                # 本行动结算完再赋予状态（同回合之后的行动即可见；
                # 施放该技能本身不享受它赋予的状态）
                state_tracker.apply(action, turn_idx, turn_front)
                if not buff or not buff.get("amount") or not buff.get("duration"):
                    continue
                # 连击框提示：本技能给「对象」的连击数（带状态变体时标注）
                base_buff = getattr(skill_now, "combo_buff", None) or {}
                extra = ""
                if (states_now and base_buff.get("state_variants")
                        and buff.get("amount") != base_buff.get("amount")):
                    extra = "（%s状态中）" % "、".join(sorted(states_now))
                action.set_combo_grant_hint(
                    "本技能给予对象：连击 +%g，持续 %d %s%s"
                    % (buff["amount"], buff["duration"],
                       buff.get("timing") or "己方回合", extra))
                scope = buff.get("scope")
                if scope in ("one_any", "one_other"):
                    # 单名友方：取行动里的「对象」
                    tgt = action.get_sp_target()
                    targets = ([tgt] if tgt is not None else [])
                    if scope == "one_other" and tgt == action.member_index:
                        targets = []
                else:
                    targets = self._scope_targets(
                        scope, buff.get("element"),
                        action.member_index, self._active_slots(), turn_front)
                for target in targets:
                    entries = combo_buffs.setdefault(target, [])
                    if buff.get("solo"):
                        # 「[单独发动]」：重复发动不叠加，只刷新回合数
                        entries[:] = [e for e in entries
                                      if e.get("source") != buff.get("source")]
                    entries.append({
                        "amount": buff["amount"],
                        "left": buff["duration"],
                        "kind": buff.get("kind", "turn"),
                        "source": buff.get("source"),
                        "source_role": self.team[action.member_index].get("role") or "",
                        "solo": bool(buff.get("solo")),
                    })
            # 3) 连击框显示全部可用层之和；一次攻击技能**最多生效 2 层**，
            #    其余层留到下一次攻击技能；「按次数」的层生效时消耗 1 次
            for action in turn.actions:
                entries = combo_buffs.get(action.member_index, [])
                active = [e for e in entries if e["left"] > 0]
                action.set_auto_combo(sum(e["amount"] for e in active))
                if action.is_combo_eligible():
                    # 被动给的层不占「2 层」名额；主动层最多生效 2 层，
                    # 「[单独发动]」的主动层独占（其它主动层不生效），其余层留到下次攻击
                    passive = [e for e in active if e.get("passive")]
                    actives = [e for e in active if not e.get("passive")]
                    solo = [e for e in actives if e.get("solo")]
                    chosen = solo[:1] if solo else actives[:2]
                    applied = passive + chosen
                    action.set_effective_combo(
                        sum(e["amount"] for e in applied))
                    for e in applied:
                        if e.get("kind") == "use":
                            e["left"] -= 1
                else:
                    action.set_effective_combo(0.0)
            # 4) 「己方回合」计数：
            #    - 通常回合 / 超频回合：**所有队员**各 −1（真正的己方回合）
            #    - 追加 / 特殊回合：只有**当回合出手的队员**−1
            #      （额外回合只属于出手的那个人，如释放者本人）
            #    - 占位回合：**不属于任何己方回合**，不消耗
            if turn.turn_type() in PLACEHOLDER_TURN_TYPES:
                tick_slots = set()
            elif turn.turn_type() in EXTRA_TURN_TYPES:
                tick_slots = set(actors)
            else:
                tick_slots = set(combo_buffs)
            for slot in tick_slots:
                for e in combo_buffs.get(slot, []):
                    if e["left"] > 0 and e.get("kind") != "use":
                        e["left"] -= 1
        for turn_idx, turn in enumerate(self.turns):
            # 「敌方回合」数（两个通常回合之间的敌方行动）：供速攻◯等使用
            turn.set_enemy_turns(self._enemy_turns_before(turn_idx))
            # 占位回合：不触发任何被动
            self._passives_off = turn.turn_type() in PLACEHOLDER_TURN_TYPES
            # 发动 OD 消耗（同一次发动只扣一次：连续相同等级视为同一次发动）
            # 追加/特殊/占位回合没有 OD，不参与「同一次发动」的判定，
            # 因此「OD2/Bonus1 → 追加回合 → OD2/Bonus2」仍属同一次发动。
            is_extra = turn.turn_type() in UNTIMED_TURN_TYPES
            level = turn.od_level()
            if is_extra:
                is_new_activation = False
                cost = 0
            else:
                is_new_activation = level > 0 and level != prev_level
                if is_new_activation:
                    cost = level * OD_GAUGE_PER_LEVEL
                    consumed += cost
                else:
                    cost = 0
                prev_level = level
            # 回合开始：风格被动「OD条上升」（如 V字回复）——
            # 按触发时机/位置/阈值/是否出击中1次结算。
            # 只有「通常回合」，或「前置OD 且为本次发动的第一回合（如 OD3/Bonus1）」
            # 才有回合开始；后置OD 与后续的 Bonus 回合（Bonus2/3）、追加/占位回合都不结算。
            is_post_od = (level > 0 and turn.od_timing() == "后置OD")
            starts_turn = (turn.turn_type() not in UNTIMED_TURN_TYPES
                           and not is_post_od
                           and (level == 0 or is_new_activation))
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
                    # 「若自身干劲为良好或以上」（如 球界头脑：超频条+10%）
                    cmin = mod.get("condition_min")
                    if cmin is not None and not self._condition_ok(
                            slot, cmin, bool(mod.get("condition_exact"))):
                        continue
                    # 「处于X状态的友方为N名或以上」（如 魔王军的大攻势！）
                    sc = mod.get("state_count")
                    if sc and self._state_holders(turn_states.get(turn_idx),
                                                  sc[0]) < sc[1]:
                        continue
                    turn_bonus += mod.get("amount", 0.0)
                    if mod.get("once", True):
                        od_gain_used.add(slot)
                    break

            # 「共鸣天赋」的回合开始 OD（如 神圣恩典：位于前锋 则超频条+N%），
            # 每回合都生效（与「出击中1次」的被动无关）
            if starts_turn:
                for slot in self._active_slots():
                    res_od = self._member_resonance_od(slot)
                    if res_od is None:
                        continue
                    if (res_od.get("position") == "front"
                            and slot not in start_front):
                        continue
                    turn_bonus += res_od.get("amount", 0.0)

            # 「回合开始OD」= 上一回合结束OD + 回合开始被动 − 发动OD消耗（上限 300）
            # 「本回合OD」只统计本回合行动；因此 回合开始OD + 本回合OD = 当前OD
            # 手动「OD调整」：直接加在该回合的回合开始OD 上（并影响之后的累计）
            od_adjust = turn.od_adjust()
            turn.set_start_od(min(running_od + turn_bonus - cost + od_adjust,
                                  OD_GAUGE_MAX))
            turn_actions = 0.0
            for action in turn.actions:
                with self._action_style_ctx(action):
                    element = action.get_attack_element()
                    resist = blanket or bool(element and element in resisted)
                    # 目标数：全体攻击按「敌人数量」，单体攻击恒为 1
                    battle = self._battle_params(
                        resist, action.get_target_count())
                    value = calc_od(action.get_od_skill(), battle).total_od
                    # 「OD条下降」：固定扣减（如 50% → −50）
                    value -= action.get_od_down_fixed()
                    # 非攻击技能的「OD条上升 X%」：直接增加超频条（不吃 OD 耳环）
                    value += action.get_od_up_flat()
                    action.set_result(value)
                    turn_actions += value

            # 「追击」（由 SP 侧算出）：按固定OD参数（原始Hit=追击Hit、连击0）计入本回合OD。
            # 实测：追击（含替换后的「猫咪喷射打靶」）均**不吃 OD 耳环**；追击均为单体 → 目标数 1。
            for hits, elem, slot, _switch in turn.follow_up_od():
                resist = blanket or bool(elem and elem in resisted)
                battle = self._battle_params(resist, 1)
                od_skill = ODSkill(base_hits=hits, combo_count=0.0, fixed_od=0.0,
                                   resonance_31x=0.0, od_earring=0.0)
                turn_actions += calc_od(od_skill, battle).total_od

            # 「X之律动」（超越条）：本回合该属性风格每行动一次 +4%；满 100% 触发 OD +100
            # （占位回合不触发任何被动，律动也不推进）
            if rhythm_state:
                if not self._passives_off:
                    for element, state in rhythm_state.items():
                        rhythm = state["def"]
                        acted = sum(
                            1 for action in turn.actions
                            if action.member_index is not None
                            and _element_matches(
                                self._member_element(action.member_index), element))
                        state["value"] = min(
                            rhythm.get("threshold", 100.0),
                            state["value"] + rhythm.get("per_action", 4.0) * acted)
                        if (not state["triggered"]
                                and state["value"] >= rhythm.get("threshold", 100.0)
                                and rhythm.get("od_bonus")):
                            turn_actions += rhythm["od_bonus"]
                            state["triggered"] = True
                turn.set_rhythm(" ".join(
                    "超越条(%s)：%.0f" % (el, st["value"])
                    for el, st in rhythm_state.items()))
            else:
                turn.set_rhythm("")

            cumulative += turn_bonus + turn_actions
            running_od += turn_bonus + turn_actions - cost + od_adjust
            running_od = min(running_od, OD_GAUGE_MAX)   # OD 槽上限 300
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
        self._passives_off = False
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
        self._refresh_state_panel()

    def _rebuild_calc_caches(self):
        """重算开始时重建风格/印记缓存，避免回合循环里反复扫 styles。"""
        self._style_lookup = {}
        self._sigils_cache = None
        self._sigil_levels_cache = None
        for slot in range(len(self.team)):
            info = self.team[slot]
            role = info.get("role")
            if role:
                self._find_style(role, info.get("style"),
                                 info.get("style_rarity"))

    def _find_style(self, role, style_name, rarity=None):
        """按 (role, style[, rarity]) 查风格对象，带会话内缓存。

        rarity 仅用于双稀有度风格区分 SS / SSR 身份。
        """
        if not role:
            return None
        key = (role, style_name, rarity)
        cache = self._style_lookup
        if key in cache:
            return cache[key]
        found = None
        for st in self.data_source.styles(role):
            if st.name != style_name:
                continue
            if rarity is not None and st.rarity != rarity:
                continue
            found = st
            break
        if found is None and rarity is not None:
            # 指定稀有度没找到时退回同名任意稀有度
            for st in self.data_source.styles(role):
                if st.name == style_name:
                    found = st
                    break
        cache[key] = found
        return found

    @contextmanager
    def _action_style_ctx(self, action):
        """在本行动计算期间，让该队员临时使用行动行选择的形态。

        只临时改 ``self.team[slot]["style"]``，不影响队伍配置 UI；
        形态差异（技能、被动、击破 OD 等）都会按当前行动形态结算。
        """
        slot = getattr(action, "member_index", None)
        style = getattr(action, "style_override", None)
        if (style is None or slot is None
                or not (0 <= slot < len(self.team))):
            yield
            return
        member = self.team[slot]
        old_style = member.get("style")
        if old_style == style:
            yield
            return
        member["style"] = style
        try:
            yield
        finally:
            member["style"] = old_style

    def _ordered_actions(self):
        """按界面顺序展开全部行动行。"""
        return [action for turn in self.turns
                for action in getattr(turn, "actions", [])]

    def propagate_action_style(self, source_action, style_name):
        """形态切换后，让同一队员后续行动一直沿用，直到下一次切换。"""
        started = False
        for action in self._ordered_actions():
            if action is source_action:
                started = True
                continue
            if not started or action.member_index != source_action.member_index:
                continue
            # 遇到该队员后面的主动切换就停下，后面的切换优先
            if action.style_switch and action.style_override:
                break
            action.set_style_override(style_name)

    def inherit_action_style(self, action):
        """新建行动行时继承该队员之前最后一次选择的形态。"""
        style_name = None
        for previous in self._ordered_actions():
            if previous is action:
                break
            if previous.member_index == action.member_index:
                if previous.style_override:
                    style_name = previous.style_override
        if style_name:
            action.set_style_override(style_name)

    def reset_action_style_from(self, source_action):
        """队员改变后，清除该位置后续行动继承的旧形态。"""
        started = False
        for action in self._ordered_actions():
            if action is source_action:
                started = True
                continue
            if started and action.member_index == source_action.member_index:
                action.set_style_override(None)

    def _member_style_obj(self, slot):
        try:
            info = self.team[slot]
            return self._find_style(
                info.get("role"),
                info.get("style"),
                info.get("style_rarity"))
        except Exception:
            return None

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
            st = self._member_style_obj(slot)
            if st is None or not st.sp_limit_override:
                continue
            selected = self._selected_passives(slot)
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
        # 各「X之印」等级（用于「X之印等级≥N」类的 SP 消耗/回复条件）
        sigil_levels = self._team_sigil_levels()

        sp = [self.sp_init_spin.value()] * count
        # front = 「回合开始时」的前锋。第 1 回合 = 队伍配置前 3 人
        front = self._initial_front()
        break_seen = False   # 是否已经发生过击破（用于「首次击破」类被动）
        prev_od_level = 0    # 上一次发动的 OD 等级（同一次发动只给一次额外 SP）
        sp_once_used = set()  # 已触发过「每次出击1次」类 SP 被动的队员
        state_tracker = _StateTracker(self)   # 技能赋予的状态（如 歌姬之加护）
        # 「战斗/初战开始时 使自身进入X状态」（如 山胁大人的仆人/万岁）
        self._seed_battle_states(state_tracker)

        # 「首次使用该技能」类的 SP 折扣（如 血腥之舞+ 6(11)：首次使用时消耗SP-5）：
        # 按整条轴的行动顺序（同回合内非攻击技能在前，与下面的扣费顺序一致），
        # 每名队员的每个技能只有**第一次使用**享受折扣。
        seen_skill_use = set()
        for _turn in self.turns:
            for _action in sorted(_turn.actions,
                                  key=lambda a: 1 if a._is_attack() else 0):
                _skill = _action._find_skill()
                _name = getattr(_skill, "name", None)
                _key = (_action.member_index, _name)
                _action._first_use = bool(_name) and _key not in seen_skill_use
                if _name:
                    seen_skill_use.add(_key)

        for turn_idx, turn in enumerate(self.turns):
            # 追加/特殊回合不计回合数：不触发「回合开始回复」与 OD 回复，
            # 但行动仍然消耗 SP、技能回复 SP 也照常生效。
            is_additional = turn.turn_type() in UNTIMED_TURN_TYPES
            # 占位回合：不算己方回合、不触发任何被动、技能不消耗 SP
            is_placeholder = turn.turn_type() in PLACEHOLDER_TURN_TYPES
            self._passives_off = is_placeholder
            state_tracker.begin_turn(turn_idx)
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
            elif is_placeholder:
                # 占位回合：不触发任何回合开始结算（也没有基础回复）
                pass
            elif not is_additional:
                # 「回合开始」的结算条件与 OD 增加被动一致：
                # 通常回合，或「前置OD 且为本次发动的第一回合」；
                # 后续 Bonus 回合（Bonus2/3）不再有回合开始。
                starts_turn = (level == 0
                               or (is_new_od and turn.od_timing() == "前置OD"))
                if starts_turn:
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
                            # 「X之印」等级6：回合开始时若位于前锋则自身 SP+N
                            regen += self._member_sigil_bonus(i)
                        if sp[i] < limit:
                            sp[i] = min(limit, sp[i] + regen)

                    # 回合开始：「回合开始时/战斗开始时」回复友方 SP 的被动（如 与伙伴一起）
                    for i in active:
                        for mod in self._member_turn_start_sp(i):
                            if mod.get("extra"):
                                continue    # 「追加回合开始时」类在另外的分支处理
                            if mod.get("battle_start") and not first_turn:
                                continue
                            # 「若回合开始时 X之印 等级为 N 或以上」（如 冰岚之进击）
                            sig_el = mod.get("sigil_element")
                            if sig_el is not None:
                                if self._sigil_level(sig_el) < (mod.get("sigil_min_level") or 0):
                                    continue
                            # 「若回合开始时自身处于X状态」（如 共鸣：歌姬之加护→前锋SP+2）
                            st_cond = mod.get("state")
                            if st_cond and st_cond not in (state_tracker.states(i) or ()):
                                continue
                            # 「干劲为极佳 / 良好或以上」（如 干劲极佳的少女 / 怪童）
                            cmin = mod.get("condition_min")
                            if cmin is not None:
                                exact = bool(mod.get("condition_exact"))
                                if mod.get("condition_on") == "self":
                                    if not self._condition_ok(i, cmin, exact):
                                        continue
                                else:
                                    # 「干劲为X的友方SP+N」：只给满足干劲的队员
                                    for ct in active:
                                        if self._condition_ok(ct, cmin, exact):
                                            self._apply_scope_recover(
                                                mod.get("amount", 0), "self",
                                                None, ct, sp, active,
                                                start_front, limit)
                                    if mod.get("once"):
                                        sp_once_used.add(i)
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
                            # 「若回合开始时存在破坏率为N%或以上的敌人」
                            # （如 山胁「最终手段」）：破坏率由回合行手动设置
                            dmin = mod.get("destruction_min")
                            if dmin is not None and turn.destruction() < dmin:
                                continue
                            if mod.get("once") and i in sp_once_used:
                                continue
                            # 「处于X状态的友方SP+N」：只给**拥有该状态**的队员
                            # （如 山胁「开始进军！」/ 丰后「帮忙毁灭世界的说！」）
                            ts = mod.get("target_state")
                            if ts:
                                for t in active:
                                    if ts in (state_tracker.states(t) or ()):
                                        self._apply_scope_recover(
                                            mod.get("amount", 0), "self", None,
                                            t, sp, active, start_front, limit)
                                if mod.get("once"):
                                    sp_once_used.add(i)
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
            elif is_additional:
                # 追加/特殊回合开始时：「追加回合开始时」类被动
                # （如 战场之花：追加回合开始时 自身SP+5，每次出击仅1次）
                for i in active:
                    for mod in self._member_turn_start_sp(i):
                        if not mod.get("extra"):
                            continue
                        if mod.get("once") and i in sp_once_used:
                            continue
                        self._apply_scope_recover(
                            mod.get("amount", 0), mod.get("scope"),
                            mod.get("element"), i, sp, active,
                            start_front, limit)
                        if mod.get("once"):
                            sp_once_used.add(i)
            # 追加/特殊回合没有 OD，不参与「同一次发动」的判定
            # （中间隔着追加回合时 OD2/Bonus1 与 OD2/Bonus2 仍只给一次额外 SP）
            if not is_additional:
                prev_od_level = level

            # 记录「行动前」全队 SP（回合开始回复 / 前置OD 之后）
            # pre_sp：「行动前SP」——各行动的「剩余SP」都以它为基准（不随行动中的回复变化）
            # post ：累积本次回合的**扣费**与**所有行动触发的 SP 回复** → 就是「行动后」的队伍SP
            pre_sp = list(sp)
            post = list(sp)
            pre_entries = [(i, self.team[i].get("role"), sp[i], i in start_front)
                           for i in active]

            # 行动：扣除技能 SP，并结算技能的 SP 回复效果。
            # 结算顺序：非攻击技能先于攻击技能（同类按行动行顺序）。
            is_extra_turn = turn.turn_type() in EXTRA_TURN_TYPES
            action_order = sorted(
                turn.actions, key=lambda a: 1 if a._is_attack() else 0)
            # 「分享」类被动（自身以外的友方的主动技能使自身SP提升时 额外使全体SP+N）：
            # 先登记，回合结束时再统一结算到 post（如 东城司「分享」）。
            # share_self_seen：「自身」范围类（如 惹人怜爱）按**回合**去重，每回合只触发一次。
            share_pending = []
            share_self_seen = set()
            for action in action_order:
                i = action.member_index
                if i not in active:
                    action.set_sp_result(None)
                    continue
                cost = action.get_sp_cost(downed=break_seen,
                                          extra=is_extra_turn,
                                          sigil_levels=sigil_levels,
                                          first_use=getattr(action, "_first_use", False))
                # 「速攻◯」类：开局 N 回合内指定技能 SP 消耗固定为 X
                _pin = self._member_sp_cost_pin(i, action, turn_idx)
                if _pin is not None:
                    cost = _pin
                if is_placeholder:
                    cost = 0          # 占位回合：所有技能不消耗 SP
                elif cost >= 99:      # 消耗全部 SP
                    cost = pre_sp[i]
                else:
                    # SP 消耗增减被动（同名只叠加一次）；
                    # 「高阶增强」（红宝石香水）不作用于通常攻击与 SP 消耗为 0 的技能
                    cost = max(0, cost + self._sp_cost_modifier(
                        i, active, turn_front, cost, downed=break_seen,
                        extra=is_extra_turn, states=state_tracker.states(i),
                        manual_up=turn.sp_cost_up()))
                    cost = int(round(cost))    # SP 是整数，避免出现 8.0
                enough = pre_sp[i] >= cost
                if not enough and action.allows_negative_sp():
                    enough = True     # 「SP0或以上即可使用」：SP 可为负
                if enough:
                    post[i] -= cost
                    # 「剩余SP」= **行动前SP − 本次消耗**（用行动前的值算，
                    # 与行动顺序、与行动中产生的任何 SP 回复都无关）
                    remaining_after_cost = pre_sp[i] - cost
                    # 以下回复全部作用在 post 上（不会影响本回合其它行动的剩余SP）
                    self._apply_sp_recover(action, i, post, active,
                                           turn_front, limit, share_pending,
                                           share_self_seen)
                    if action.is_break():
                        self._apply_break_recover(
                            action, i, post, active, turn_front, limit,
                            not break_seen)
                        break_seen = True
                    # 「条件触发」附带的全队 SP 效果（如 贝斯独奏：全体 SP+5，上限 30）
                    self._apply_trigger_sp(action.trigger(), post, active, limit)
                    # 「自身使用EX技能后」回复SP（如 注入活力 / 开辟希望的一箭）
                    if action.get_skill_is_ex():
                        for mod in self._member_ex_sp(i):
                            self._apply_scope_recover(
                                mod.get("amount", 0), mod.get("scope"),
                                mod.get("element"), i, post, active,
                                turn_front, limit)
                    action.set_sp_result(remaining_after_cost, True)
                else:
                    # SP 不足：显示红色负值（还差多少），实际 SP 不变
                    action.set_sp_result(pre_sp[i] - cost, False)
                # 本行动**结算完**再赋予状态（如 若向流星歌唱 → 歌姬之加护）：
                # 施放当回合的自身消耗不吃该状态，之后（含同回合后续行动）才生效
                state_tracker.apply(action, turn_idx, turn_front)

            # 「追击」：友方使用 SP≤N 的攻击行动时触发（如 温泉巡游）。
            # 追击不计入行动、只在后卫发动；装备 温泉通行木牌 时首变为 猫咪喷射打靶（整回合1次）。
            follow_entries = []
            for m_slot in active:
                fu = self._member_follow_up(m_slot)
                if fu is None or m_slot in start_front:
                    continue
                threshold = fu.get("sp_below", 8)
                quals = []
                for a in action_order:
                    if not a._is_attack():
                        continue
                    c = a.get_sp_cost(downed=break_seen, extra=is_extra_turn,
                                      sigil_levels=sigil_levels,
                                      first_use=getattr(a, "_first_use", False))
                    if 0 < c <= threshold:
                        quals.append(a)
                if not quals:
                    continue
                switch = self._member_follow_up_switch(m_slot)
                used_switch = False
                for _a in quals:
                    hits = fu.get("hits") or 1
                    elem = fu.get("element")
                    is_switch = False
                    if (switch is not None and not used_switch
                            and post[m_slot] >= switch["skill"].sp_cost):
                        sk = switch["skill"]
                        hits = sk.hits or 1
                        elem = sk.element
                        post[m_slot] -= sk.sp_cost
                        used_switch = True
                        is_switch = True
                    # 追击本体（温泉巡游）不吃 OD 耳环；替换后的「猫咪喷射打靶」是实际技能，吃耳环
                    follow_entries.append((hits, elem, m_slot, is_switch))
                    # 发动追击时的 SP 回复（如 嫩绿摇曳：前锋SP+2）
                    for mod in self._member_follow_up_sp(m_slot):
                        self._apply_scope_recover(
                            mod.get("amount", 0), mod.get("scope"),
                            mod.get("element"), m_slot, post, active,
                            turn_front, limit)
            turn.set_follow_up_od(follow_entries)

            # 回合结束：把本回合登记下来的「分享」类被动也结算到 post（即「行动后」）
            for owner, mod in share_pending:
                self._apply_scope_recover(
                    mod.get("amount", 0), mod.get("scope"), mod.get("element"),
                    owner, post, active, turn_front, mod.get("limit") or limit)

            # 记录本回合结束时全队 SP（含后卫）；前锋标注用回合中的前锋
            entries = [(i, self.team[i].get("role"), post[i], i in turn_front)
                       for i in active]
            turn.set_team_sp(entries, before=pre_entries)
            # 本回合的「行动后」SP 成为下一回合的起点
            sp = list(post)

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

        self._passives_off = False

    def _apply_od_sp_bonus(self, turn, sp, active):
        """发动 OD 给全队的额外 SP（OD1+5 / OD2+12 / OD3+20）。"""
        level = turn.od_level()
        if 1 <= level < len(OD_SP_BONUS):
            bonus = OD_SP_BONUS[level]
            for i in active:
                sp[i] = min(99, sp[i] + bonus)

    def _member_element(self, slot):
        """队员所装备风格的元素属性。"""
        st = self._member_style_obj(slot)
        return getattr(st, "element", None) if st is not None else None

    def _style_has_command(self, slot):
        """该队员所装备风格的职业是否为「指挥者」。"""
        st = self._member_style_obj(slot)
        return bool(st is not None and getattr(st, "career", None) == "指挥者")

    def _commander_slot(self):
        """队伍唯一的指挥者：职业为「指挥者」的最靠前的一名队员。"""
        for slot in self._active_slots():
            if self._style_has_command(slot):
                return slot
        return None

    def is_commander(self, slot):
        """该队员是否为队伍唯一的指挥者（职业为「指挥者」的最靠前者）。"""
        return self._commander_slot() == slot

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
        if scope == "back":
            # 后卫：不在前锋里的友方（如 增加同伴之舞：使后卫友方进入仆人状态）
            return [i for i in active if i not in front_set]
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

    def _apply_trigger_sp(self, trigger, sp, active, limit):
        """「条件触发」附带的全队 SP 回复。

        如 贝斯独奏：全体友方 SP+5，且可突破上限至 30（超过 30 的部分不加）。
        只加不减——已经高于上限的队员不会被压回去。
        """
        effect = TRIGGER_SP_EFFECTS.get(trigger)
        if not effect:
            return
        amount, cap_override = effect
        cap = max(limit, cap_override)
        for m in active:
            if sp[m] < cap:
                sp[m] = min(cap, sp[m] + amount)

    def _member_lb(self, slot):
        """队员风格突破数（0~4）。"""
        try:
            return int(self.team[slot].get("lb", 0) or 0)
        except Exception:
            return 0

    def _member_front_sp(self, slot):
        """风格被动里「回合开始时位于前锋则自身 SP+X」的合计（闪光等，满足突破要求）。"""
        if getattr(self, "_passives_off", False):
            return []          # 占位回合：不触发任何被动
        st = self._member_style_obj(slot)
        if st is None:
            return []
        lb = self._member_lb(slot)
        return [m for m in st.front_sp_passives if m.get("lb", 0) <= lb]

    def _passive_carried(self, slot, name):
        """该队员是否携带指定的「（被动技能）」条目（None 表示默认全选）。"""
        selected = self._selected_passives(slot)
        return selected is None or name in selected

    def _member_rhythm(self, slot):
        """该队员风格的「X之律动」（超越条）定义（满足突破要求）。"""
        if getattr(self, "_passives_off", False):
            return None        # 占位回合：不触发任何被动
        st = self._member_style_obj(slot)
        if st is None:
            return None
        lb = self._member_lb(slot)
        r = getattr(st, "rhythm", None)
        if r and r.get("lb", 0) <= lb:
            return r
        return None

    def _team_rhythms(self):
        """队伍里存在的「X之律动」：{元素: 定义}。"""
        found = {}
        for slot in self._active_slots():
            r = self._member_rhythm(slot)
            if r and r.get("element") not in found:
                found[r["element"]] = r
        return found

    def _rhythm_members(self, element):
        """队伍里属于该元素的队员下标（双属性任一命中）。"""
        return [slot for slot in self._active_slots()
                if _element_matches(self._member_element(slot), element)]

    def _team_sigils(self):
        """队伍里存在的「X之印」：{元素: sigil 定义}。"""
        if self._sigils_cache is not None:
            return self._sigils_cache
        found = {}
        for slot in self._active_slots():
            st = self._member_style_obj(slot)
            if st is None:
                continue
            lb = self._member_lb(slot)
            sig = getattr(st, "sigil", None)
            if sig and sig.get("lb", 0) <= lb:
                req = sig.get("requires")
                if req is None or self._passive_carried(slot, req):
                    found.setdefault(sig.get("element"), sig)
        self._sigils_cache = found
        return found

    def _sigil_level(self, element):
        """「X之印」等级 = 初战开始时同属性风格的数量（队伍里存在该印记时才有效）。

        双属性风格（如「冰雷」）只要含该属性就算一份，所以这里用属性包含判断。
        """
        if self._sigil_levels_cache is not None:
            return self._sigil_levels_cache.get(element, 0)
        levels = {}
        sigils = self._team_sigils()
        if sigils:
            counts = {}
            for slot in self._active_slots():
                el = self._member_element(slot)
                for sig_el in sigils:
                    if _element_matches(el, sig_el):
                        counts[sig_el] = counts.get(sig_el, 0) + 1
            levels = counts
        self._sigil_levels_cache = levels
        if element is None:
            return 0
        return levels.get(element, 0)

    def _team_sigil_levels(self):
        """当前队伍各「X之印」的等级：{元素: 等级}。"""
        if self._sigil_levels_cache is None:
            self._sigil_level(next(iter(self._team_sigils()), None))
        return dict(self._sigil_levels_cache or {})

    def _seed_battle_states(self, tracker):
        """把「战斗/初战开始时 使自身进入X状态」的被动记进状态跟踪器。

        如 山胁「魔王大人降临！」→ 自身进入山胁大人万岁！（= 仆人），
        以及神崎/松冈/天音/樱庭/丰后等「侍奉魔王…」风格 → 自身进入山胁大人的仆人。
        这些状态是**永久**的，所以直接记成「一直有效」。
        """
        for slot in self._active_slots():
            role = self.team[slot].get("role")
            style = self.team[slot].get("style")
            lb = self._member_lb(slot)
            for st in self.data_source.styles(role):
                if st.name != style:
                    continue
                for bs in (getattr(st, "battle_states", None) or []):
                    if bs.get("lb", 0) > lb:
                        continue
                    tracker.until[(slot, bs["state"])] = 10 ** 6
                    tracker.sources[(slot, bs["state"])] = "%s（战斗开始时）" % (
                        bs.get("name") or "被动")
        # 「比赛开始」给全队赋予干劲：没有这类风格时就不记
        if self._team_has_condition():
            for slot in self._active_slots():
                tracker.until[(slot, "干劲")] = 10 ** 6
                tracker.sources[(slot, "干劲")] = "比赛开始（战斗开始时）"

    def _state_holders(self, turn_states, state):
        """某回合开始时，处于指定状态的队员数量。"""
        if not turn_states:
            return 0
        return sum(1 for names in turn_states.values() if state in names)

    def _member_sigil_bonus(self, slot):
        """该队员因「X之印」等级6 获得的回合开始自身 SP（需位于前锋，0 表示不触发）。

        队员可能是双属性风格（如「冰雷」），此时只要**任一**属性命中印记就算生效。
        """
        if getattr(self, "_passives_off", False):
            return 0           # 占位回合：不触发任何被动
        member_element = self._member_element(slot)
        for element, sig in self._team_sigils().items():
            if not _element_matches(member_element, element):
                continue
            if self._sigil_level(element) < sig.get("level", 6):
                continue
            return int(sig.get("amount", 0) or 0)
        return 0

    def _selected_passives(self, slot):
        """队员在队伍配置里携带的「（被动技能）」；None 表示全部。"""
        selected = self.team[slot].get("passives")
        return set(selected) if selected is not None else None

    def _member_turn_start_od(self, slot):
        """风格被动里「回合开始时增加 OD 槽」的项（满足突破要求）。

        「（被动技能）」条目（带 requires）按**角色**通用：任一风格解锁后，
        该角色所有风格携带它都生效。
        """
        if getattr(self, "_passives_off", False):
            return []          # 占位回合：不触发任何被动
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        lb = self._member_lb(slot)
        selected = self._selected_passives(slot)
        mods = []
        for st in self.data_source.styles(role):
            equipped = (st.name == style)
            for m in st.turn_start_od:
                if m.get("lb", 0) > lb:
                    continue
                req = m.get("requires")
                if req is not None:
                    if selected is not None and req not in selected:
                        continue
                elif not equipped:
                    continue
                mods.append(m)
        return mods

    def _member_ex_sp(self, slot):
        """该队员「自身使用EX技能后 回复SP」的项（风格被动 + 大师技能）。

        如 注入活力（31D 六宇亚 的 SS 被动）、桐生美也大师技能 开辟希望的一箭。
        """
        if getattr(self, "_passives_off", False):
            return []          # 占位回合：不触发任何被动
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        lb = self._member_lb(slot)
        mods = []
        for st in self.data_source.styles(role):
            if st.name == style:
                mods.extend(m for m in st.ex_sp if m.get("lb", 0) <= lb)
                break
        # 大师技能（默认可携带，未取消时生效）
        selected = self._selected_passives(slot)
        name = self.data_source.master_skill_name(role)
        if name and (selected is None or name in selected):
            mods.extend(self.data_source.master_ex_sp(role))
        return mods

    def _member_ex_od(self, slot):
        """该队员「自身使用EX技能后 超频条+X%」的项。

        「（被动技能）」条目（如 千里眼）按**角色**通用：任一风格解锁后，
        该角色所有风格携带它都生效。
        """
        if getattr(self, "_passives_off", False):
            return []          # 占位回合：不触发任何被动
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        lb = self._member_lb(slot)
        selected = self._selected_passives(slot)
        mods = []
        for st in self.data_source.styles(role):
            equipped = (st.name == style)
            for mod in st.ex_od:
                if mod.get("lb", 0) > lb:
                    continue
                req = mod.get("requires")
                if req is not None:
                    if selected is not None and req not in selected:
                        continue
                elif not equipped:
                    continue
                mods.append(mod)
        return mods

    def _member_ex_od_fraction(self, slot):
        """使用 EX 技能时增加 OD 槽的被动，换算为「固定OD」小数（10% → 0.10）。"""
        return sum(m.get("amount", 0.0)
                   for m in self._member_ex_od(slot)) / 100.0

    @staticmethod
    def _filter_passive_mods(mods, lb):
        """按突破数过滤被动项，并处理「XX[天赋强化]」**替换**「XX（小）」。

        两者是同一效果的基础/强化版（突破2/3）：强化版解锁后基础版不再单独生效，
        否则会重复计算（如 QUEEN 微积分 +2 与 +5 叠加成 +7）。
        """
        ok = [m for m in mods if m.get("lb", 0) <= lb]
        enhanced = {m.get("family") for m in ok
                    if m.get("enhanced") and m.get("family")}
        if not enhanced:
            return ok
        return [m for m in ok
                if not (m.get("family") in enhanced and not m.get("enhanced"))]

    def _member_passive_combo(self, slot):
        """该队员风格被动里的「连击数上升」项（满足突破要求）。"""
        if getattr(self, "_passives_off", False):
            return []          # 占位回合：不触发任何被动
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        lb = self._member_lb(slot)
        for st in self.data_source.styles(role):
            if st.name == style:
                return self._filter_passive_mods(st.passive_combo, lb)
        return []

    def _member_share_sp(self, slot):
        """该队员「友方主动技能使自身SP提升时 额外使全体SP+N」的项（如 东城司「分享」）。"""
        if getattr(self, "_passives_off", False):
            return []          # 占位回合：不触发任何被动
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        lb = self._member_lb(slot)
        for st in self.data_source.styles(role):
            if st.name == style:
                return [m for m in st.share_sp if m.get("lb", 0) <= lb]
        return []

    def _team_has_condition(self):
        """队伍里是否有「战斗开始时 赋予友方干劲」的风格。

        没有这类风格时，全队都**没有干劲**（干劲相关被动不生效）。
        """
        for slot in self._active_slots():
            role = self.team[slot].get("role")
            style = self.team[slot].get("style")
            for st in self.data_source.styles(role):
                if st.name == style and getattr(st, "grants_condition", False):
                    return True
        return False

    def _member_condition_rank(self, slot):
        """队员「干劲」阶段下标（0=极差 … 4=极佳）；队伍没有干劲时返回 None。"""
        if not self._team_has_condition():
            return None
        name = self.team[slot].get("condition") or "极佳"
        try:
            return CONDITION_TIERS.index(name)
        except ValueError:
            return len(CONDITION_TIERS) - 1

    def _condition_ok(self, slot, minimum, exact=False):
        """该队员的干劲是否满足「阶段 = minimum（或以上）」；没有干劲则 False。"""
        rank = self._member_condition_rank(slot)
        if rank is None:
            return False
        return rank == minimum if exact else rank >= minimum

    def _member_turn_start_sp(self, slot):
        """风格被动里「回合开始时回复友方 SP」的项（如 与伙伴一起，满足突破要求）。"""
        if getattr(self, "_passives_off", False):
            return []          # 占位回合：不触发任何被动
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        lb = self._member_lb(slot)
        for st in self.data_source.styles(role):
            if st.name == style:
                return self._filter_passive_mods(st.turn_start_sp, lb)
        return []

    def _member_follow_up(self, slot):
        """风格被动的「追击」定义（如 温泉巡游），满足突破要求则返回。"""
        if getattr(self, "_passives_off", False):
            return None        # 占位回合：不触发任何被动
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        lb = self._member_lb(slot)
        for st in self.data_source.styles(role):
            if st.name == style:
                fu = st.follow_up
                if fu and fu.get("lb", 0) <= lb:
                    return fu
                return None
        return None

    def _member_follow_up_sp(self, slot):
        """风格被动里「发动追击时回复友方 SP」的项（如 嫩绿摇曳）。"""
        if getattr(self, "_passives_off", False):
            return []          # 占位回合：不触发任何被动
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        lb = self._member_lb(slot)
        for st in self.data_source.styles(role):
            if st.name == style:
                return [m for m in st.follow_up_sp if m.get("lb", 0) <= lb]
        return []

    def _member_follow_up_switch(self, slot):
        """追击替换（如 温泉通行木牌 → 猫咪喷射打靶）；未携带该被动则 None。"""
        if getattr(self, "_passives_off", False):
            return None        # 占位回合：不触发任何被动
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        selected = self._selected_passives(slot)
        for st in self.data_source.styles(role):
            if st.name == style:
                sw = st.follow_up_switch
                if not sw:
                    return None
                req = sw.get("requires")
                if selected is not None and req not in selected:
                    return None
                return sw
        return None

    def _member_break_od(self, slot):
        """风格被动里「击破敌人时增加 OD 槽」的项（满足突破要求）。"""
        if getattr(self, "_passives_off", False):
            return []          # 占位回合：不触发任何被动
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        lb = self._member_lb(slot)
        for st in self.data_source.styles(role):
            if st.name == style:
                return [m for m in st.break_od if m.get("lb", 0) <= lb]
        return []

    def _member_resonance_break(self, slot):
        """共鸣天赋里「击破敌人时 超频条+N%」的项，换算为 B19 的 31X共鸣小数。"""
        res = self._member_resonance(slot)
        if not res:
            return 0.0
        eff = resonance_od_effect(res.get("text"))
        if eff and eff.get("kind") == "break":
            return eff.get("amount", 0.0) / 100.0
        return 0.0

    def _member_resonance(self, slot):
        """该队员**参与计算**的「共鸣天赋」（含等级）。

        选择逻辑上 SS / SSR 都能配置（见 TeamMemberRow）；
        但**只有 SSR 身份才生效**——SS 选的天赋只显示在轴图，不进 OD 计算。
        返回 {"name","type","levels","level","text"} 或 None。
        """
        if getattr(self, "_passives_off", False):
            return None        # 占位回合：不触发任何被动
        style_info = self._member_style_obj(slot)
        if style_info is None or style_info.rarity != "SSR":
            return None          # 仅 SSR 身份的共鸣天赋参与计算
        choice = self.team[slot].get("resonance_talent", None)
        if choice == "":
            return None
        res = self.data_source.resonance_pool().get(choice) if choice else None
        if res is not None and not _talent_element_ok(res.get("owners") or [],
                                                     style_info.element):
            return None          # 属性不符，不能配置
        if res is None:
            res = getattr(style_info, "resonance", None)
        if not res:
            return None
        level = int(self.team[slot].get("resonance_level", 4) or 0)
        level = max(0, min(4, level))
        levels = dict(res.get("levels") or {})
        return {"name": res.get("name"), "type": list(res.get("type") or []),
                "levels": levels, "level": level,
                "text": levels.get(str(level), "")}

    def _member_resonance_display(self, slot):
        """轴图/展示用：SS / SSR 选中的共鸣天赋（不判断是否生效）。

        与 _member_resonance 的差别：SS 身份也返回所选天赋，供 axle_image 显示。
        """
        style_info = self._member_style_obj(slot)
        if style_info is None:
            return None
        if style_info.rarity not in ("SSR", "SS"):
            return None
        choice = self.team[slot].get("resonance_talent", None)
        if choice == "":
            return None
        res = self.data_source.resonance_pool().get(choice) if choice else None
        if res is not None and not _talent_element_ok(res.get("owners") or [],
                                                     style_info.element):
            return None
        if res is None:
            res = getattr(style_info, "resonance", None)
        if not res:
            return None
        level = int(self.team[slot].get("resonance_level", 4) or 0)
        level = max(0, min(4, level))
        levels = dict(res.get("levels") or {})
        return {"name": res.get("name"), "type": list(res.get("type") or []),
                "levels": levels, "level": level,
                "text": levels.get(str(level), "")}

    def _member_resonance_od(self, slot):
        """共鸣天赋里「回合开始时位于前锋 则超频条+N%」的项（无则 None）。"""
        res = self._member_resonance(slot)
        if not res:
            return None
        eff = resonance_od_effect(res.get("text"))
        if eff and eff.get("kind") == "turn_start":
            return eff
        return None

    def _member_break_od_fraction(self, slot):
        """击破敌人时增加 OD 槽的被动，换算为「固定OD」小数（25% → 0.25）。"""
        return sum(m.get("amount", 0.0)
                   for m in self._member_break_od(slot)) / 100.0

    def _enemy_turn_counts(self):
        """每个回合开始前的「敌方回合」数（按回合顺序一次性算好）。

        两个通常回合之间敌方行动一次；追加 / 特殊 / 超频 / 占位回合
        都属于同一个玩家回合，不额外产生敌方回合。
        T1=0、T2=1、T3=2；T1 后面的追加回合仍是 0。
        """
        counts = []
        count = 0
        seen_normal = False
        for turn in self.turns:
            if turn.turn_type() == NORMAL_TURN_TYPE:
                if seen_normal:
                    count += 1
                seen_normal = True
            counts.append(count)
        return counts

    def _enemy_turns_before(self, turn_idx):
        """该回合开始前已经历的「敌方回合」数。"""
        counts = self._enemy_turn_counts()
        if 0 <= turn_idx < len(counts):
            return counts[turn_idx]
        return counts[-1] if counts else 0

    def _member_sp_cost_pin(self, slot, action, turn_idx):
        """「指定 SP 消耗」类被动（如 速攻◯）。

        战斗开始时【夺取荣耀！满垒本垒打！】消耗的SP为8（2回合）：
        开局 N 个（敌方）回合内，该技能的 SP 消耗固定为 X。
        """
        if getattr(self, "_passives_off", False):
            return None
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        selected = self._selected_passives(slot)
        name = action._current_skill_name()
        for st in self.data_source.styles(role):
            if st.name != style:
                continue
            for pin in (getattr(st, "sp_cost_pins", None) or []):
                if pin.get("skill") != name:
                    continue
                req = pin.get("passive")
                if req and selected is not None and req not in selected:
                    continue
                turns = int(pin.get("turns") or 0)
                if turns > 0:
                    used = (self._enemy_turns_before(turn_idx)
                            if pin.get("unit") == "enemy" else turn_idx)
                    if used >= turns:
                        continue
                return int(pin.get("cost") or 0)
            return None
        return None

    def _member_sp_cost_mods(self, slot):
        """队员所装备风格里影响 SP 消耗的被动（过滤未携带的）。"""
        if getattr(self, "_passives_off", False):
            return []          # 占位回合：不触发任何被动
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
        if getattr(self, "_passives_off", False):
            return []          # 占位回合：不触发任何被动
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
                          downed=False, extra=False, states=None, manual_up=0):
        """作用于该队员的 SP 消耗增减合计。

        同种效果只生效一次并取大值：所有「降低SP消耗」取降幅最大者、
        所有「增加SP消耗」取增幅最大者，两者相抵。
        base_cost 为该技能的原始 SP 消耗；SP 消耗为 0 的技能（通常攻击等）
        不受任何 SP 消耗增减影响。
        downed=True 表示敌人处于倒地/被击破状态（带该条件的被动生效）。
        extra=True 表示处于追加回合/特殊回合（带「追加回合」条件的被动生效）。
        states 为该队员当前所处的状态集合（如 {"歌姬"}），带状态条件的被动据此生效。
        """
        if base_cost is not None and base_cost == 0:
            return 0          # SP 消耗为 0 的技能不受增减影响
        if getattr(self, "_passives_off", False):
            return 0          # 占位回合：不触发任何被动

        reductions = []   # 负值
        increases = []    # 正值
        if manual_up:     # 回合行手动增加的 SP 消耗（与其它增耗取最大）
            collect_manual = int(manual_up)
        else:
            collect_manual = 0

        def collect(amount):
            if amount < 0:
                reductions.append(amount)
            elif amount > 0:
                increases.append(amount)

        for slot in active:
            for mod in self._member_sp_cost_mods(slot):
                if mod.get("downed") and not downed:
                    continue
                if mod.get("extra") and not extra:
                    continue
                # 「若自身处于X状态」（如 绝唱：歌姬之加护 → 自身消耗SP-2）
                st_cond = mod.get("state")
                if st_cond and st_cond not in (states or ()):
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
        if collect_manual > 0:
            increases.append(collect_manual)
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

    def _apply_sp_recover(self, action, actor, sp, active, front_set, limit,
                          share_pending=None, seen_self=None):
        """结算技能自带的 SP 回复效果。

        **每一段回复都会单独触发一次「分享」类被动**：例如「灵能充能」对 31A 对象
        是「本体回复3」+「额外回复3」两段，全体类的「分享」会触发**两次**。

        特例：作用范围是**自身**的分享类（如「惹人怜爱」）**每个回合只触发一次**
        （见 seen_self，由 _recalc_sp 按回合维护）——若每段都触发，实测会比游戏里多。
        """
        amount, scope, element = action.get_sp_recover()
        if scope in ("one_other", "one_any"):
            # 单名友方：回复到行动里选择的「对象」
            target = action.get_sp_target()
            if target is None or not (0 <= target < len(sp)):
                return
            extra, team = action.get_sp_recover_extra()
            # 第一段：技能本体回复
            self._recover_and_share(
                lambda: self._recover_one(sp, target, amount, limit),
                actor, sp, active, share_pending, seen_self)
            # 第二段：「对象属于指定队伍时额外回复」（如 灵能充能 对 31A +3）
            if extra and team and self._member_in_team(target, team):
                self._recover_and_share(
                    lambda: self._recover_one(sp, target, extra, limit),
                    actor, sp, active, share_pending, seen_self)
            return
        self._recover_and_share(
            lambda: self._apply_scope_recover(amount, scope, element, actor,
                                              sp, active, front_set, limit),
            actor, sp, active, share_pending, seen_self)

    @staticmethod
    def _recover_one(sp, target, amount, limit):
        """给单个队员回复 SP（不超过 SP 上限）。"""
        if 0 <= target < len(sp) and sp[target] < limit:
            sp[target] = min(limit, sp[target] + amount)

    def _recover_and_share(self, apply_fn, actor, sp, active, share_pending,
                           seen_self=None):
        """执行一次 SP 回复，并登记这次回复触发的「分享」类被动。

        「分享」类（友方主动技能使自身SP提升时 额外使全体/自身 SP+N）按**每次回复**
        触发，所以这里一次只处理一段回复（登记后回合结束时统一结算）。
        作用范围是「自身」的（如 惹人怜爱）每个回合只登记一次（见 seen_self）。
        """
        if share_pending is None:
            apply_fn()
            return
        before = list(sp)
        apply_fn()
        for m in active:
            if m == actor or sp[m] <= before[m]:
                continue
            for mod in self._member_share_sp(m):
                if mod.get("scope") == "self" and seen_self is not None:
                    key = (m, mod.get("name"))
                    if key in seen_self:
                        continue      # 自身类：每个回合只触发一次
                    seen_self.add(key)
                share_pending.append((m, mod))

    def _member_break_sp(self, slot):
        """队员所装备风格里「击破敌人时回复SP」的被动（满足突破要求）。

        另外包含「大师技能」里的同类效果（如 小笠原「友缘之剑」：击破时 全体友方SP+1）。
        """
        if getattr(self, "_passives_off", False):
            return []          # 占位回合：不触发任何被动
        role = self.team[slot].get("role")
        style = self.team[slot].get("style")
        lb = self._member_lb(slot)
        mods = []
        for st in self.data_source.styles(role):
            if st.name == style:
                mods = [b for b in st.break_sp if b.get("lb", 0) <= lb]
                break
        selected = self._selected_passives(slot)
        name = self.data_source.master_skill_name(role)
        if name and (selected is None or name in selected):
            mods = mods + list(self.data_source.master_break_sp(role))
        return mods

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
