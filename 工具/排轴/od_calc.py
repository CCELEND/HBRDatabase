# -*- coding: utf-8 -*-
"""
OD 计算引擎

公式来源：./工具/等效破坏率与OD计算表.xlsx -> 工作表「破坏率OD计算表」中的
「OD计算器」区域（B16:B24、I22:I26、E21:E22）。

Excel 公式对应关系：
    耳环系数 (I22) = 1 + IF(B16=0, 5, 5+MIN(B16,10)*10/9-10/9)/100 * B20
    总系数   (I23) = I22 + B23
    HIT OD   (I24) = (B16+B17) * ROUNDDOWN(2.5*I23*B24, 2) * B21 * IF(B22,0,1)
    固定 OD  (I25) = ROUNDDOWN(B18*100*I23, 2) + ROUNDDOWN(B19*100*I23, 2)
    总OD     (I26) = I24 + I25
    实际OD百分比 (E21) = I26 / 100
    实际Hit数    (E22) = E21 * 40

其中：
    B16 技能原始Hit数   B17 连击数      B18 固定OD     B19 31X共鸣
    B20 OD耳环         B21 目标数(敌人数量)  B22 抗性   B23 其他OD增量
    B24 敌方OD率
"""

import math
from dataclasses import dataclass


def rounddown(value, digits=0):
    """等价于 Excel 的 ROUNDDOWN（向零方向取整）。

    加入极小误差量，避免二进制浮点误差导致 2.875 被算成 2.874999... 而少 0.01。
    """
    factor = 10 ** digits
    scaled = value * factor
    epsilon = 1e-9
    if scaled >= 0:
        result = math.floor(scaled + epsilon)
    else:
        result = math.ceil(scaled - epsilon)
    return result / factor


@dataclass
class ODSkill:
    """单个技能/单次出招的 OD 参数。"""
    base_hits: float = 0.0        # 技能原始Hit数 (B16)
    combo_count: float = 0.0      # 连击数 (B17)
    fixed_od: float = 0.0         # 固定OD (B18)
    resonance_31x: float = 0.0    # 31X共鸣 (B19)
    od_earring: float = 1.0       # OD耳环 (B20)


@dataclass
class ODBattle:
    """整场战斗通用的 OD 参数。"""
    target_count: int = 1         # 目标数 / 敌人数量 (B21)
    resistance: bool = False      # 抗性 (B22)，为真则 HIT OD 记 0
    other_od: float = 0.0         # 其他OD增量 (B23)
    enemy_od_rate: float = 1.0    # 敌方OD率 (B24)


@dataclass
class ODResult:
    earring_coef: float = 0.0     # 耳环系数 I22
    total_coef: float = 0.0       # 总系数 I23
    per_hit_od: float = 0.0       # 单 Hit OD（已按敌方OD率取整）
    hit_od: float = 0.0           # HIT OD I24
    fixed_od_total: float = 0.0   # 固定 OD I25
    total_od: float = 0.0         # 总OD I26
    od_percent: float = 0.0       # 实际OD百分比 E21
    actual_hits: float = 0.0      # 实际Hit数 E22


def calc_earring_coef(base_hits: float, od_earring: float) -> float:
    """计算 OD 耳环系数（I22）。"""
    if od_earring == 0:
        return 1.0
    if base_hits == 0:
        bonus = 5.0
    else:
        bonus = 5.0 + min(base_hits, 10.0) * 10.0 / 9.0 - 10.0 / 9.0
    return 1.0 + bonus / 100.0 * od_earring


def calc_od(skill: ODSkill, battle: ODBattle) -> ODResult:
    """按计算表公式计算一次出招的 OD 收益。"""
    earring_coef = calc_earring_coef(skill.base_hits, skill.od_earring)
    total_coef = earring_coef + battle.other_od

    per_hit_od = rounddown(2.5 * total_coef * battle.enemy_od_rate, 2)
    target_factor = 0 if battle.resistance else 1
    hit_od = (skill.base_hits + skill.combo_count) * per_hit_od \
        * battle.target_count * target_factor

    fixed_od_total = (
        rounddown(skill.fixed_od * 100 * total_coef, 2)
        + rounddown(skill.resonance_31x * 100 * total_coef, 2)
    )

    total_od = hit_od + fixed_od_total

    return ODResult(
        earring_coef=earring_coef,
        total_coef=total_coef,
        per_hit_od=per_hit_od,
        hit_od=hit_od,
        fixed_od_total=fixed_od_total,
        total_od=total_od,
        od_percent=total_od / 100.0,
        actual_hits=total_od / 100.0 * 40.0,
    )


if __name__ == "__main__":
    # 与计算表默认值比对，期望 total_od == 85.02
    skill = ODSkill(base_hits=8, combo_count=5, fixed_od=0.25,
                    resonance_31x=0.18, od_earring=1)
    battle = ODBattle(target_count=1, resistance=False,
                      other_od=0, enemy_od_rate=1)
    r = calc_od(skill, battle)
    print("耳环系数 =", r.earring_coef, " 期望 1.12777777777778")
    print("总系数   =", r.total_coef)
    print("HIT OD   =", r.hit_od, " 期望 36.53")
    print("固定 OD  =", r.fixed_od_total, " 期望 48.49")
    print("总OD     =", r.total_od, " 期望 85.02")
    print("百分比   =", r.od_percent, " 期望 0.8502")
    print("实际Hit数=", r.actual_hits, " 期望 34.008")
