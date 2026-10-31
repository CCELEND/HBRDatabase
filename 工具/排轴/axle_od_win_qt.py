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

import os
import json
import types
from contextlib import contextmanager

from PyQt5.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QHBoxLayout, QVBoxLayout, QGridLayout,
    QScrollArea, QFileDialog, QMessageBox, QGroupBox, QSizePolicy,
    QToolButton, QMenu, QDialog, QApplication,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, QSize, QTimer, QEvent, pyqtSignal, QThread
from PyQt5.QtGui import QPainter, QPixmap

from window_qt import set_window_icon, creat_Toplevel, install_no_wheel
from window_qt import win_open_manage, win_close_manage, is_win_open, win_set_top

from 工具.排轴.od_calc import ODSkill, ODBattle, calc_od
from 工具.排轴.data_source import (
    get_data_source, NORMAL_ATTACK_NAME, NORMAL_ATTACK_HITS,
    resonance_od_effect, generic_skill_names, talent_element_ok,
    CONDITION_TIERS, DUAL_SS_SSR_STYLE_NAMES)

from 日志.advanced_logger import AdvancedLogger
logger = AdvancedLogger.get_logger(__name__)


WINDOW_TITLE = "排轴OD计算"
# 耳坠：只有「驱动耳坠」提升 OD 获取量（旧字段 od_earring 记 1），其余记 0；
# 轴图会把所选耳坠的图标画在风格头像右下角（图标见 持有物/饰品/耳坠/Earrings.json）
EARRING_CHOICES = ("", "击碎耳坠", "攻击耳坠", "驱动耳坠", "破坏耳坠")
OD_EARRING_NAME = "驱动耳坠"
# 回合行可以手动加 SP 消耗（0 / +2 / +4）；与其它「增加SP消耗」取最大，不叠加
SP_COST_UP_CHOICES = (0, 2, 4)
MODULE_NAME = __name__
DEFAULT_SAVE_PATH = os.path.join("工具", "排轴", "排轴存档.json")
HELP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "help.txt")

HELP_TEXT = """排轴OD计算 使用说明
========================================

【排轴】
- 一个队伍 6 人（前锋 3 / 后卫 3）；队伍配置可选 角色、风格、携带被动、突破数、
  共鸣天赋（含等级）、耳坠；角色不可重复（已选的角色在其它位置会置灰不可选）。
  风格下拉按「**风格名-稀有度-元素**」显示（双属性如「火暗」照原样；无属性的风格只显示前两项）。
  **默认队伍是空队伍**（角色/风格都为空），首次编入角色时会自动建立第 1 回合。
  共鸣天赋 / 耳坠 按角色设置（共鸣天赋里「击破敌人时 超频条+N%」仅在「条件触发」选「击破敌人」的行动中生效；
  耳坠对该角色所有回合生效）。
  **「耳坠」下拉**：击碎耳坠 / 攻击耳坠 / **驱动耳坠** / 破坏耳坠（另有「无（不装备）」）。
  其中**只有「驱动耳坠」会提升 OD 获取量**（计算时记 1），其余记 0（不影响 OD / SP），
  但所选耳坠会在**轴图**里画在该队员风格头像的**右下角**（图标取自 持有物/饰品/耳坠/Earrings.json）。
  「角色」下拉框按**队伍分组**（31A / 31B / 31C / 30G / 31D / 31E / 31F / 31X / Angel Beats! / 司令部 / persona5r），
  每个队伍前面有一个**不可选的分组标题**；「无」在最上面，表示该位置空着。
  配置窗口顶部有「**清空角色**」按钮：一键清空 6 个位置的角色/风格
  （回合列表与「全局战斗设置」会保留，点击后会先确认；队伍为空时按钮置灰）。
- 「回合列表」在**独立窗口**打开（与主窗口同时出现）；主窗口只保留队伍/全局设置，不显拥挤。
  回合的「添加/上移/下移/清空/保存/读取」等操作按钮也在该窗口，方便操作。
  回合窗口关闭后，可用配置窗口顶部的「打开回合窗口」按钮重新打开。
- 队伍≥3人时每回合固定 3 人行动；同一回合内队员不重复。
  **队伍为空时没有行动**（行动列表为空，也不再出现 点数援助/驱动增益 等光球通用技能），
  且**不能添加回合**（「添加回合 / 追加回合 / 特殊回合 / 占位回合」按钮禁用）。
- 追加回合不计回合数、不触发回合开始回复，也不能发动 OD。
- 「特殊回合」性质与追加回合一致（不计回合数/不触发回合开始/不能发动 OD），
  但**角色不限前锋**，任意队员都可行动。
- 「占位回合」同样不计回合数、不能发动 OD、角色不限前锋，且：
  **不算己方回合**（不消耗连击 buff 的「己方回合」，见下）、
  **不触发任何被动**（回合开始回复、OD条上升、击破回复、印记/律动/共鸣、SP消耗被动、追击、EX 被动等一律不生效）、
  **所有技能不消耗 SP**（技能自身的 OD/连击等效果照常结算）。
- 选了 OD 的回合，类型会显示为「超频回合」（与通常回合等价，仅作标识）。
- 回合卡片按类型配色，方便一眼区分：**追加回合=紫、特殊回合=橙、占位回合=灰**
  （通常/超频回合仍按所选 OD 等级配色）。
- 新增回合会自动沿用上一回合行动的队员；修改上一回合前锋会同步后续（未手动编辑的）回合。
- 技能：同角色各风格技能通用；但 SSR/SS 的第一个主动技能为专属（仅装备该风格时可用）。
  已通用化的例外：第一个 SS 风格的专属技能（如 幻象泡影）、星火燎原+。
- 「（被动技能）」在队伍配置里选择携带（默认全部），选中后全程（所有回合）生效；
  这些条目按**角色通用**（任一风格解锁后，该角色所有风格都能携带并生效），
  但条目里标了 **`{"exclusive":1}`（风格专属）** 的只在该风格可选 ——
  例如茅森月歌「怪物般的球威（被动技能）」属于「激烈！带来胜利的全力一球！」，她的其它风格不会出现它。
- 同一风格的不同形态（如 CODE:Virtual Killer / CODE:Virtual Killer2）共享技能与被动，可自由选择。
- 特殊被动里的攻击（如 山胁·冯·伊瓦尔「魔界骑兵启动！」，斩属性 6 连击）也可作为行动使用，
  且该攻击不吃 OD 耳环（不受友方 BUFF 影响）。
- 「追击」（如 大岛四叶草「悠然摇曳温泉之乐」）：该风格位于**后卫**时，友方每使用一次
  **SP 消耗≤8 的攻击行动**就触发一次追击（1 Hit，计入本回合 OD；**不吃 OD 耳环**）。
  装备「温泉通行木牌（被动技能）」且自身 **SP≥10** 时，该回合**首次**追击变为
  「猫咪喷射打靶」（整回合仅1次，消耗 SP10）；追击（含猫咪喷射打靶）**均不吃 OD 耳环**；
  「嫩绿摇曳」使每次追击给前锋 SP+2。
- 技能数据里的「切换形态」会被自动展开（如 白河由依奈「月色真美」的 苍焰迷宫 / 苍焰螺旋、
  朝仓可怜「Twinkle Eclosion」的 血腥燃烧 / 芬布尔之舞 与 红尖晶石 / 堇青石），
  同一条目下的形态共享该条目的专属标记；「指挥行动」只属于其所在风格，
  且带「指挥行动」的风格**不能使用通常攻击**（行动列表里不再出现通常攻击）。
  「指挥者」是一个**职业**（风格数据里的 职业 字段，如 茅森月歌「Glorious Blades」）。
  「指挥行动」是该职业**专属**的；**一个队伍只能编入一名指挥者**——
  尚未有指挥者时各位置都可选，选中一名后**其它位置的「指挥者」职业风格会被禁用（不可选）**。
- 所有角色共有的通用技能：**全部光球技能**（数据取自 `持有物/饰品/光球/Orbs.json`）。
  光球技能里除了**「遗能光球」是专属角色**的之外，其余**所有角色都能使用**，
  所以每个角色的行动列表里都能选到它们（如 软体化、暴击冥想、修缮之光、点数援助、驱动增益、
  5 种重力子、保护、专注、自我复原、衰灭之力、防御提升、充能注入、加油助威 等）；
  行动下拉框里用一个不可选的 **「通用技能」分组标题**把它们和角色自身的技能隔开。
  排轴只结算其中的 SP 消耗、回复 SP（点数援助：自身 SP+3，消耗 SP1）与超频条
  （驱动增益：+15%，消耗 SP6，按固定OD结算且吃 OD 耳环）；其余效果不影响 OD / SP。
  这些技能大多写「每次出击1次」，但排轴暂不限制使用次数。
- 条件触发：每个行动的「条件触发」下拉框手动指定该行动触发了什么条件（默认「无」）。
  · **击破敌人**：该行动击破敌人，触发「击破时回复 SP」的技能/被动
    （以及「击破敌人时超频条+X%」类被动，见下）。
  · **【炸裂！！贝斯独奏】发动**：逢川惠「特别之夜·少女即兴演奏会」的四破被动
    「【炸裂！！贝斯独奏】发动时 全体友方的SP+5（可突破上限至30）」。
    该被动本身是「回合开始时若有处于击破状态的友方则发动」，是否发动由这里手动指定；
    选中后该行动会给**全体友方 SP+5**，且可以突破当前 SP 上限、最多到 30
    （已经高于 30 的不会被压回去）。
- 「单名友方回复SP」的技能（如 日常维护）：行动行的「对象」下拉框选择回复对象
  （「其他友方」类的对象不含自身）；其它技能该列显示「—」。

【OD 公式】来自「等效破坏率与OD计算表」
- 耳环系数 = 1 + (5 + MIN(原始Hit,10)×10/9 − 10/9)/100 × OD耳环
- HIT OD = (原始Hit + 连击数) × ROUNDDOWN(2.5×总系数×敌方OD率, 2) × 目标数 × (抗性?0:1)
  目标数：**全体攻击** = 敌人数量；**单体攻击（含通常攻击）恒为 1**。
- 「X之律动」（超越条，如 茅森月歌「Glorious Blades」的 冰之律动）：战斗开始时超越条 = **15% × 该属性风格数**
  （出击中限1次）；**该属性风格每行动一次 +4%**（任何行动都算，含指挥行动）；
  达到 **100%** 时触发「OD条上升 100%」（出击中限1次，直接计入当前OD）。
  回合卡片上「超越条(X)：N」显示的是**本回合行动结束后**的值。
- 固定OD = ROUNDDOWN(固定OD×100×总系数, 2) + ROUNDDOWN(31X共鸣×100×总系数, 2)
- 总系数 = 耳环系数 + 其他OD增量
- 通常攻击不享受 OD 耳环加成、**不计连击**；通常攻击视为「无属性」。
  **连击只对「攻击技能（非通常攻击）」生效**：非攻击技能（无 Hit，如 增益/回复）也不计连击
  （连击输入框不禁用，只是不参与计算）。
- 「连击数上升」buff（如 苍井绘里香「传承·Legacy」的 连结未来的苍之意志：
  提升冰属性风格连击数 3 己方回合）会**自动计入**受影响队员行动的连击数，
  **连击框里直接显示「手动＋自动」的合计值**（手动部分另存，读档不会重复叠加）。
  带「**[单独发动]**」的这类效果**不会叠加**：重复发动只刷新持续回合数（连击值不变）。
  被动里的同类效果（如 山胁「梅雨」：战斗开始时位于前锋 自身连击+5（1次））同样自动计入；
  标「**次**」的按**释放攻击技能的次数**消耗——每释放一次攻击技能消耗 1 次。
  写「**持续+N**」的（如 QUEEN「微积分」+2/+5、伊达朱里「阴暗的五球连击」+5）是**常驻**加成，
  整场都生效、不会过期，也不会重复叠加。
  「**XX（小）**」与「**XX[天赋强化]**」是同一效果的基础/强化版（突破2 / 突破3），
  强化版解锁后**替换**基础版（不会 +2 与 +5 叠加成 +7）。
  目标是**单名友方**的（如 茅森月歌「月芒」、李映夏「第七击·无中生有」）：
  在行动行的「**对象**」下拉里选择受益的友方，该 buff 只加到他/她身上。
  带**状态条件**的（如 茅森月歌「月华歌姬」的 月芒：默认 连击+5（中量伤害/5次），
  **自身处于「歌姬之加护」时变为 连击+3（特大伤害/3次）**）会按施放者当时是否
  处于该状态自动切换。状态由技能赋予（如 若向流星歌唱：使**全体友方**进入
  歌姬之加护 **5 己方回合**，含施放当回合），生效期间该队员使用月芒即取「歌姬中」那条。
  一次攻击技能里**主动**给的连击层**最多生效 2 层**；被动给的层（如 梅雨）**不占名额**、
  每次攻击都会生效并被消耗；带「**[单独发动]**」的主动层会**独占**（该次攻击只生效它一个）。
  未生效的层**留到下一次攻击技能**（「次」数的层被生效时才消耗）。
  「己方回合」的消耗规则：**通常回合 / 超频回合（OD回合）所有队员各 −1**；
  **追加 / 特殊回合只有当回合出手的队员 −1**（额外回合只算出手那个人的）；
  **占位回合不属于任何己方回合，完全不消耗**。
  因此同一个 buff 对不同队员，其「3 己方回合」可能落在不同的回合上。
- 「**SP0或以上即可使用**」的技能（如 李映夏「第七击·无中生有」）：SP 不足时也能使用，
  消耗照扣、SP 会变成负数。
- 抗性可按属性勾选（含「无」）：行动的攻击元素（技能元素 → 角色风格元素 → 无）被抗性时，
  该次 HIT OD 记 0。
- 「OD条下降 X%」为该次行动 OD 的固定扣减（如 50% → −50，可为负）。
- 风格被动「OD条上升」（如 V字回复）：「回合开始时」每回合结算、「战斗开始时」仅第 1 回合；
  按「位于前锋/后卫」判定位置；「超频条不足N%」为触发阈值；「出击中1次」整场只触发一次；
  均为「直接增加超频条」，收益为固定值（不吃 OD 耳环加成）；也需满足突破数。
  「回合开始时」类只结算于：**通常回合**；或「**前置OD 且为本次发动的第一回合**」（如 OD3/Bonus1）。
  后置OD、后续 Bonus 回合（Bonus2/3）与追加/特殊/占位回合都不结算。
- 「击破敌人时超频条+X%」类（如 托付给你了 / 势如破竹）：「条件触发」选「击破敌人」**且该行动是攻击**时，
  自动同步到该行动的**固定OD**输入框（X% → X/100，如 25% → 0.250），
  因此会吃到 OD 耳环加成；改回「无」会自动移除（手填值保留）。
- 技能的「OD条上升 X%」效果：**一律按「固定OD」结算（吃 OD 耳环加成）**，
  包括**非攻击技能**（如 驱动增益 / 连结未来的苍之意志）。
  若限定「以此技能击破敌人时」（如 原子火焰 / 哀伤的雪花莲），则仅在「条件触发」选「击破敌人」时计入。
  换其它技能时会自动移除。
- 概率类被动（如福运 70%）按必定触发计算；
  无法判定的条件（干劲/领域/解除BUFF/EX/SP提升等）不计入。

【OD 发动与回合数】
- 前置OD：当前回合直接发动；后置OD：当前回合结束马上发动（两者 OD 回合都是当前回合）。
- 后置OD 的回合沿用上一个回合号（显示「第N回合 后置OD」），不计入回合数。
- 同一次 OD 发动的多个「超频回合」（连续相同等级，如 OD3 / OD3/Bonus1 / OD3/Bonus2）
  共用同一个回合号；**中间隔着追加/特殊/占位回合也算同一次发动**（只扣一次 OD 槽）。
- 发动消耗 OD 槽 = 等级×100（OD1=100 / OD2=200 / OD3=300）；
  同一次发动只扣一次（连续相同 OD 等级的回合，如 OD2 / OD2/Bonus1 / OD2/Bonus2 视为同一次）。
- 每回合显示：「回合开始OD」（= 上一回合结束OD + 回合开始被动 − 发动OD消耗，上限 300）、
  「本回合OD」（仅本回合行动产生的 OD）、「当前OD」= 回合开始OD + 本回合OD；
  汇总的「净OD」即最后一个回合的当前OD。

【SP】
- 第 1 回合前锋 = 队伍配置前 3 人；之后 = 上一回合行动的队员。
- 回合开始：基础回复（前锋/后卫）+ 风格被动的前锋SP（闪光/佳音/机敏/俊敏…，需满足突破数）；
  以及「回合开始时回复友方SP」的被动（如 与伙伴一起【朝仓可怜专属】：除自身外全体友方 SP+1）。
- 「X之印」（雷之印/冰之印/火之印…）：等级 = **初战开始时同属性风格的数量**，
  **双属性风格（如「冰雷」）只要含该属性就算一份**（自身也计入）。
  满 6 级时该属性风格位于前锋者在回合开始时**自身 SP+1**。
  印记来源有两种：被动里常驻的（如 白虎「兽之心暖」的 雷之印、苍井绘里香「传承·Legacy」的 冰之印），
  以及「（被动技能）」条目（如 桐生美也「海风的邀约」的 夏日晴空：需在队伍配置里携带）。
  依赖印记等级的效果也按等级结算：如 冰岚之进击（冰之印≥6 → 全体友方 SP+5，出击中限1次）、
  猛火进击（火之印≥6 → 全体友方 SP+5，出击中限1次）、
  暮色中升腾绽放的幻影（火之印≥4 → SP消耗减半 16→8）。
- 「共鸣天赋」（相当于角色的装备，也就是队伍配置里的这一项，对应计算表的 **B19 31X共鸣**）：
  **SSR / SS 风格都能配置**；每个位置可选（默认 = 风格自带、或无），**等级可自由选择（0~4）**。
  列表里**只列该风格可选的共鸣天赋**（属性不符的天赋不会出现在列表里）。
  **仅 SSR 身份的共鸣天赋参与 OD 计算**；SS 选的天赋只显示在轴图上，不计入效果。
  部分风格可在队伍配置中选 **SS / SSR 两种身份**（同技能，SSR 时共鸣才生效）：
  逢川惠 心跃欣舞Fuel、朝仓可怜 Twinkle Eclosion、苍井绘里香 响彻·Battlecry、
  桐生美也 丰饶喜乐神秘莫测、小笠原绯雨 夏暮色榴石、瑞原蓝娜 冲锋！突刺！金枪鱼！。
  标签标明**所属队伍·属性·提供该天赋的风格**（如 `Excelsior!（31X·无·绚烂华美琉璃色 等 3 个风格）`）。
  **属性按当前风格显示**：同一个天赋在不同属性上由不同风格提供，不会把属性堆在一起
  （不会出现「31X·无/暗/火」这种写法）；把鼠标停在选项上能看到该天赋的**全部来源**
  （队伍·属性·风格）。
  **只有与风格属性（火/冰/雷/光/暗/无）相同的天赋才能选**（没有「不限属性」——
  团队天赋也按其所属风格的属性判定；「无」是独立属性）。
  排轴只结算与 OD 相关的效果：如 神圣恩典（回合开始时位于前锋 → 超频条 +5/6/7/8/10%，计入回合开始OD）、
  Excelsior!（自身攻击击破敌人时 超频条 +12/14/16/18/20%，「条件触发」选「击破敌人」时作为 B19 计入该次行动）。
- 回合开始回复/闪光/「回合开始时」被动 只在**通常回合**或**前置OD 的首次发动回合**结算；
  后置OD 与后续 Bonus 回合（Bonus2/3）不结算，只结算 OD 额外 SP（同一次发动只给一次）；
  「追加回合开始时」类被动（如 战场之花：追加回合开始时 自身SP+5）只在追加/特殊回合开始时结算
  （占位回合不触发任何被动）。
- 发动 OD 额外获得 OD1 +5 / OD2 +12 / OD3 +20（同一次发动只给一次）。
- 「分享」类被动（如 东城司「哀情挽歌」的 分享 / 惹人怜爱）：**友方的主动技能使自身 SP 提升时**，
  额外给全体友方 / 自身 **SP+N**（可突破上限，最高到 SP30）。
  按**每一段 SP 回复**各触发一次——例如 逢川惠大师技能「灵能充能」对 31A 对象
  是「本体回复3」+「额外回复3」两段，「分享」（范围=全体）会触发**两次**（全体 +2×2）；
  但**范围是「自身」的**（如「惹人怜爱」）**每个回合只触发一次**（自身 +3×1）——
  按实测特例处理（若按每段/每行动触发，司的行动后SP 会比游戏里多）。
  这类被动**在回合结束时统一结算**——只体现在「行动后」的队伍SP里，
  **不计入本回合各行动的「剩余SP」**（实测：同伴给东城司补SP后，后续行动的剩余SP不受这份加成影响）。
- 「自身使用EX技能后 …」类效果（如 注入活力：全体友方SP+2、桐生美也大师技能
  「开辟希望的一箭」；追加支援 / 千里眼：超频条+10%）：在该队员使用 **EX技能** 后结算。
  **EX技能** = SS/SSR 风格的第一个主动技能（及其「+」进化版）；被通用化的
  （如 光茫一闪 / 光茫一闪+、星火燎原+）同样算 EX 技能。
  回复SP 类按作用范围回复；「超频条+X%」类：EX 技能是**攻击技能**时**吃 OD 耳环**
  （按固定OD结算），非攻击时**直接加 X 点**超频条。
- 技能/被动里的「前锋」回复范围按本回合行动的队员结算。
- 同一回合内 SP 的结算顺序：**非攻击技能先于攻击技能**（同类按行动行顺序）。
  该顺序只影响「状态」（如 歌姬之加护）的传承，**不影响各行动的「剩余SP」**（见下）。
- 行动扣除技能 SP；被动/大师技能对 SP 消耗的增减会自动结算
  （同种效果只生效一次：降低取最大降幅、增加取最大增幅，两者相抵；
  且 SP 消耗为 0 的技能不受任何增减影响）；「剩余SP」列红色负值表示不足（缺口，实际 SP 不变）。
- 「**剩余SP**」列 = **该队员的「行动前SP」− 本次消耗**。
  一回合内每个队员只行动一次，所以它对每个行动是**唯一确定**的，
  **与行动顺序无关**，也**不含任何 SP 回复**。
- **行动触发的所有 SP 回复**（技能自身的回复、被动/天赋/大师技能、击破回复、EX 回复、
  追击回复、条件触发、以及「分享」类被动…）**统一累加到「队伍SP（行动后）」**，
  不会让本回合其它行动的「剩余SP」变多——它们只影响之后的回合。
- 「红宝石香水（被动技能）」启用「高阶增强」（SP消耗 +2、SP上限 30），仅在携带该被动时生效；
  它只作用于消耗 SP 的技能，通常攻击与 SP 消耗为 0 的技能不受影响。
- 部分技能带「N(M)」式条件消耗，满足条件时改用较小值：
  「倒地/超倒地」（如 对称·启示 0(16)）、「追加回合内」（如 苍焰螺旋 7(14)：通常 14、追加回合 7）、
  **「首次使用该技能」**（如 血腥之舞+ 6(11)：首次 6、之后 11；无色子弹+ 6(12) 首次减半 6）。
  「首次使用」按**整条轴**算：每名队员的每个技能只有第一次使用享受折扣，之后按正常消耗。
- 回合行可手动设置**破坏率**（该回合**开始时**敌人的破坏率 %）：
  用于「若回合开始时存在破坏率为 N% 或以上的敌人」类被动 —— 如 山胁 SSR「拨云见日」
  3 突被动「最终手段」：破坏率 ≥200% 时 全体友方 SP+5（每次出击限 1 次，整条轴只结算一次）。
  没设（0%）就不触发；突破数不足 3 也不触发。
- 回合行（第二行）还能手动**增加SP消耗**（0 / +2 / +4，默认 0）：
  选 +N 时，该回合所有**有 SP 消耗**的技能 SP 消耗 +N；
  与其它「增加SP消耗」的被动冲突时**取最大**（不叠加，例：被动 +2 与手动 +4 只算 +4），
  并与「降低SP消耗」相抵；SP 消耗为 0 的技能（通常攻击等）不受影响。
- 同一行还有 **OD调整** 输入框（-300~300，默认 0，**支持小数**）：
  **直接加在该回合的「回合开始OD」上**，例如填 -10 就是该回合回合开始OD −10，
  也可以填 -12.5 / +0.32 这类小数；并且**计入之后的累计**（相当于回合开始时 OD 槽被加减）；
  正数同样生效，整体仍受 300 上限约束。
- **干劲**：只有队伍里有「战斗开始时 赋予全体友方任意一种干劲」的风格
  （如 月歌「激烈！带来胜利的全力一球！」、水濑莓「激战！奋力全垒打！」）时才存在，
  否则全队**没有干劲**、干劲相关被动不生效。默认按**极佳**结算
  （队伍配置里**不显示**该项；存档的 `condition` 字段保留）：
  「回合开始时 干劲为极佳的友方SP+1」（如 水濑莓「激战！奋力全垒打！」）、
  「回合开始时若自身干劲为良好或以上 则自身SP+1」（如 月歌「激烈！带来胜利的全力一球！」）、
  「回合开始时若自身干劲为良好或以上 则超频条+10%」（如 小笠原「球界头脑」）
  都会按各队员的干劲自动结算。
- 突破数按 0~4 模拟；S/A 风格的被动解锁需求在数据里写作 5 / 10，
  按「最高突破 4」处理（即突破 4 才算解锁，突破 3 及以下不生效）。
- **敌方回合**：两个**通常回合**之间的敌方行动算 1 个敌方回合
  （T1=0、T2=1、T3=2；追加/特殊/占位/超频回合不产生），显示在回合行里。
  「速攻◯（被动技能）」（水濑莓）：战斗开始时【夺取荣耀！满垒本垒打！】
  消耗的SP为 8（2 个敌方回合内），即前两个通常回合该技能只花 8 SP。
- 回合窗口工具栏的 **「状态总览」** 按钮会**单独打开状态总览窗口**
  （点选回合后刷新，默认显示最后一个回合）：
  按风格列出该回合**开始时**队员所处的状态、状态效果、**剩余回合**与来源，
  以及「连击数上升」buff 的剩余回合 / 次数。
  「剩余」按**己方回合**计（含当前回合），永久状态（如仆人）显示「永久」；
  只列出**实际参与 OD / SP 计算**的状态与 buff，方便核对持续时间。
- 回合窗口里的**下拉框 / 数值框不响应鼠标滚轮**（防止滚动页面时误改数值）：
  滚轮会转去滚动页面；要改值请先点击，再用键盘 / 箭头或直接输入。
- 「追加回合内」的 SP 消耗增减被动也只在追加回合/特殊回合生效
  （如 优美的剑技：追加回合中 自身消耗SP-2）。
- 每回合下方显示两行全队 SP（含未行动的后卫）：
  「队伍SP（行动前）」（回合开始回复 / OD 结算之后、行动之前）与
  「队伍SP（行动后）」（本回合结算结束时）。
- 「大师技能」作为可携带被动出现在队伍配置的「被动」菜单里（默认携带），
  其中影响 SP 消耗的效果会结算（如 大岛一千子「彩凤连理」：全体31E友方 消耗SP-1；
  丸山奏多「丸山部队！出发！」：指定几名角色 消耗SP-1）。按队伍/角色名匹配，假设已解放。
- 可**主动释放**的大师技能（如 逢川惠「灵能充能」：单体友方 SP+3、对象为 31A 再 +3）
  会作为该角色的可选技能出现（消耗按 0 计）。
- SP 上限默认 20；若风格有「SP上限变为 N」则自动取较大者（界面显示「（自动 N）」）。
- 需「状态/加护/领域/印/信念/士气/DP/EX 等」才能判定的 SP 被动暂不计入（避免多算）；
  可判定的条件会结算：「战斗开始时」类仅第 1 回合、「位于前锋/后卫」按回合开始时的前锋、
  「SP不大于N」按当前 SP、「超频条不足N%」按回合开始时的超频条、
  「存在被击破的敌人」（含 SP 消耗增减类，如 算法 / 最佳位置）按是否已发生击破。
- **状态类被动已支持「歌姬之加护」**（茅森月歌「月华歌姬」）：
  「若回合开始时自身处于歌姬之加护状态 则前锋SP+2」（共鸣）与
  「若自身处于歌姬之加护状态 则自身消耗SP-2」（绝唱，需突破3）都会按状态自动结算。
  状态由「若向流星歌唱」赋予全体友方 5 己方回合（含施放当回合）；
  但状态是在**该技能结算完之后**才生效，所以施放当回合的自身消耗不吃它的加成
  （例：月歌第 3 回合放「若向流星歌唱」时，消耗仍是 14−1（苍天）=13，不会减到 11）。
- **「山胁大人的仆人 / 山胁大人万岁！」状态**（魔王系风格，永久）：
  · 山胁「高傲魔王的凯旋 / 高处不胜寒」、丰后弥生「邪恶军团开始进军的说！」
    以及 神崎 / 佐月 / 天音 / 樱庭 的「侍奉魔王…」风格，**战斗开始时自身**进入该状态
    （山胁自己显示为「山胁大人万岁！」，按同一个状态计算，也计入人数）；
    山胁的「好心情之舞 / 魔王御前」、丰后的「增加同伴之舞」可以战斗中再授予他人。
  · 「回合开始时 处于该状态的友方 SP+N」→ **只给拥有该状态的队员**
    （山胁 lb1 +1 / lb3 +5、丰后 +1）。
  · 「若回合开始时处于该状态的友方为 6 名或以上 则超频条 +100%（出击中限1次）」
    （山胁 lb4 / 丰后 lb4）→ 人数不足 6 时不触发，且只结算一次。

【生成轴图】
- **回合窗口**工具栏里的「预览轴图」/「生成轴图」会把当前排轴渲染成一张图片：
  「预览轴图」不写文件、直接弹预览（预览窗里也有「保存为图片」按钮；
  预览图会**随窗口缩放**——按窗口宽度适配，拉动窗口时图片跟着拉伸，保持宽高比；
  **轴很长（图很高）时用垂直滚动条查看**，不会被压缩变形）；
  「生成轴图」直接选保存位置（PNG / JPG，默认存到「图片」文件夹）。
- 版式参考 `工具/排轴/hbr_axle.jpg`：
  · 顶部 6 个角色头像（右上角徽章 = 突破数；右下角 = 所装备**耳坠**的图标；
    左下角徽章 = 该位置的共鸣天赋等级，
    **徽章左边还会画上该共鸣天赋「所属风格」的小缩略图**，配了共鸣天赋的位置才有；
    同名天赋有多个来源风格时**按该队员风格的属性挑**，如 SSR·无 的 Excelsior! 用
    「绚烂华美琉璃色」的图，而不是别属性的来源）；
  · 「Passive Skill」= 每名成员在队伍配置里携带的被动；
  · 「Skill」= 每名成员在这条轴里用到的技能（按游戏技能顺序排列，长名字自动换行；
    **用过多次的会标出次数**，如「放学后的小小刺激[2]」「先导的领袖魅力[3]」）；
  · 红色分隔线下面按回合列出行动：左侧是回合标签（`T1` / `追加回合` / `T1` + `OD2 · Bonus 1`），
    每行最多 3 个行动（小头像 + 技能名）；**「对象」是单名友方时（回复SP / 连击数上升），
    技能名右边会画上目标队员的小头像**（如 柳美音「日常维护」→ 大岛一千子）。
- **通常攻击 / 指挥行动不是技能**：**回合行照样显示**（它们也是行动），
  但**不会出现在「Skill」栏里**，也不统计使用次数。
- **通常回合才计 T 序号**（追加/特殊/占位不计），超频回合沿用当前回合号并标出
  「OD 等级 · Bonus N」，底色用深绿；追加回合底色用深灰。
"""


def write_help_file():
    """把使用说明输出到 工具/排轴/help.txt。"""
    try:
        with open(HELP_FILE, "w", encoding="utf-8") as f:
            f.write(HELP_TEXT)
    except Exception as e:
        logger.error("写入 help.txt 失败: %s", e)

TEAM_SIZE = 6
MAX_ACTIONS_PER_TURN = 3
TURN_OPTIONS = ["通常回合", "超频回合", "追加回合", "特殊回合", "占位回合"]
# 「敌方回合」= 两个**通常回合**之间的敌方行动；
# 第 1 个通常回合前为 0，第 2 个前为 1，依此类推（速攻◯ 等按此计数）
NORMAL_TURN_TYPE = "通常回合"
# 额外回合（带「追加回合」条件的技能/被动在此生效）：
# 不计回合数、不触发回合开始、不能发动 OD
EXTRA_TURN_TYPES = ("追加回合", "特殊回合")
# 占位回合：不计回合数、不能发动 OD；且**不算己方回合**、**不触发任何被动**、
# 技能**不消耗 SP**（技能自身的 OD/连击等效果照常结算）
PLACEHOLDER_TURN_TYPES = ("占位回合",)
# 以上两类统称「不计回合数、不能发动 OD」的回合
UNTIMED_TURN_TYPES = EXTRA_TURN_TYPES + PLACEHOLDER_TURN_TYPES

# 与参考站点一致的 OD 选项
# 敌人可抗性的属性
ELEMENTS = ["火", "冰", "雷", "光", "暗", "无"]

# OD 发动时机：前置=当前回合直接发动；后置=当前回合结束马上发动
OD_TIMING_OPTIONS = ["前置OD", "后置OD"]
# 每级 OD 消耗的 OD 槽
OD_GAUGE_PER_LEVEL = 100
OD_GAUGE_MAX = 300   # OD 槽上限（OD3）

# OD 最高 3 级
OD_OPTIONS = [
    "无",
    "OD1", "OD1/Bonus1",
    "OD2", "OD2/Bonus1", "OD2/Bonus2",
    "OD3", "OD3/Bonus1", "OD3/Bonus2", "OD3/Bonus3",
]

# 发动 OD 时全队获得的 SP（下标为 OD 等级，参考 hbr-tool）
OD_SP_BONUS = [0, 5, 12, 20, 20, 20]

# OD 等级 -> 主色（游戏里 OD 条的颜色）；卡片背景自动用同色淡化
OD_COLORS = {
    "OD1": "#FD99E0",   # 粉
    "OD2": "#6BE9D6",   # 青
    "OD3": "#E2FF7D",   # 黄绿
    "OD4": "#5BA3EF",   # 暂无对应，保留
    "OD5": "#B162ED",   # 暂无对应，保留
}


def _color_with_alpha(hex_color, alpha=0.22):
    """#RRGGBB -> rgba(r, g, b, alpha)，用作卡片浅色背景。"""
    c = str(hex_color or "").lstrip("#")
    if len(c) != 6:
        return hex_color
    try:
        r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return hex_color
    return "rgba(%d, %d, %d, %.2f)" % (r, g, b, alpha)

# 回合类型 -> (左侧竖条颜色, 背景浅色)：
# 用来在回合列表里一眼区分 追加 / 特殊 / 占位 回合（通常/超频回合仍按 OD 配色）
TURN_TYPE_COLORS = {
    "通常回合": ("#c0c0c0", None),
    "超频回合": ("#c0c0c0", None),
    "追加回合": ("#7b61c9", "rgba(123, 97, 201, 0.10)"),   # 紫
    "特殊回合": ("#e08a2e", "rgba(224, 138, 46, 0.10)"),   # 橙
    "占位回合": ("#8a8a8a", "rgba(138, 138, 138, 0.12)"),  # 灰
}

# 行动列宽（表头与数据行共用）
MEMBER_W, SKILL_W, TARGET_W = 150, 200, 96
HIT_W, COMBO_W = 58, 58
FIXED_W, RES_W, EARRING_W = 72, 72, 72
TRIGGER_W, SP_W, RESULT_W = 210, 62, 66
DEL_W = 26
ACTION_COLUMNS = [
    ("角色", MEMBER_W), ("行动", SKILL_W), ("对象", TARGET_W),
    ("原始Hit", HIT_W), ("连击", COMBO_W), ("固定OD", FIXED_W),
    ("条件触发", TRIGGER_W), ("剩余SP", SP_W), ("该次OD", RESULT_W), ("", DEL_W),
]

# 行动行的「条件触发」下拉：手动指定该次行动触发了什么条件
#   (显示文字, 内部标识)
TRIGGER_CHOICES = [
    ("无", ""),
    ("击破敌人", "break"),
    ("【炸裂！！贝斯独奏】发动", "bass_solo"),
]

# 「条件触发」附带的全队 SP 效果：{标识: (SP 增量, 可突破到的上限)}
# 例：逢川惠「特别之夜·少女即兴演奏会」四破被动
#     「【炸裂！！贝斯独奏】发动时 全体友方的SP+5（可突破上限至30）」
#     —— 该被动在「回合开始时若有处于击破状态的友方」才会发动，是否发动由这里手动指定。
TRIGGER_SP_EFFECTS = {
    "bass_solo": (5, 30),
}

# 技能下拉框里「通用技能」（光球技能）分组标题（不可选中）
SKILL_GROUP_GENERIC = "──────  通用技能  ──────"

# 队伍配置里「角色」下拉框按队伍分组的标题（不可选中）
ROLE_GROUP_FMT = "── %s ──"
ROLE_GROUP_DATA = "__role_group__"

# 下拉框样式：显式指定文字与选中项配色，避免因全局 QSS 只给滚动条设样式
# 而使用 QStyleSheetStyle 渲染时，下拉项选中文字变成白色难以辨认。
COMBO_QSS = """
QComboBox {
    color: #222222;
}
QComboBox:disabled {
    color: #999999;
}
QComboBox QAbstractItemView {
    color: #222222;
    background-color: #ffffff;
    outline: 0;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
}
QComboBox QAbstractItemView::item {
    color: #222222;
    min-height: 20px;
    padding: 2px 6px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #e6f0fb;
    color: #222222;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}
#passiveButton {
    color: #222222;
    background-color: #ffffff;
    border: 1px solid #c8c8c8;
    border-radius: 3px;
    padding: 1px 16px 1px 6px;
    text-align: left;
}
#passiveButton:hover {
    background-color: #eef3fb;
}
#passiveButton:disabled {
    color: #999999;
    background-color: #f0f0f0;
}
"""

TURN_CARD_STYLE = """
    #turnCard {
        background-color: %(bg)s;
        border: 1px solid #d0d0d0;
        border-left: 6px solid %(accent)s;
        border-radius: 4px;
    }
    #turnCard QLabel { background-color: transparent; }
"""


def _make_double_spin(minimum, maximum, step, decimals, value, width=72):
    spin = QDoubleSpinBox()
    spin.setRange(minimum, maximum)
    spin.setSingleStep(step)
    spin.setDecimals(decimals)
    spin.setValue(value)
    spin.setFixedWidth(width)
    spin.setAlignment(Qt.AlignCenter)
    return spin


def _build_action_header():
    """行动列表的列名表头。"""
    header = QWidget()
    layout = QHBoxLayout(header)
    layout.setContentsMargins(28, 0, 6, 0)
    layout.setSpacing(5)
    for text, width in ACTION_COLUMNS:
        label = QLabel(text)
        label.setFixedWidth(width)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(label)
    return header


# ======================================================================
# 队伍成员
# ======================================================================
def _element_matches(style_element, element):
    """风格属性是否属于指定属性（双属性如「冰雷」任一命中即可；未知属性视为「无」）。"""
    if not style_element:
        return element == "无"
    return element in style_element


def _talent_element_ok(allowed, element):
    """（转发到 data_source.talent_element_ok，保留旧名字给界面/测试用。）"""
    return talent_element_ok(allowed, element)


class _StatePanel(QFrame):
    """「状态总览」容器：标题单独占一行。

    不用 QGroupBox 的标题：它的标题画在边框上，某些字体 / 缩放下
    预留高度不足，会被下面的表格表头压掉下半截。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statePanel")
        self.setFrameShape(QFrame.StyledPanel)
        self.title_label = QLabel()
        self.title_label.setTextFormat(Qt.PlainText)
        self.title_label.setStyleSheet(
            "font-weight: bold; padding: 2px 0 2px 2px;")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(8, 4, 8, 4)
        self.body.setSpacing(4)
        self.body.addWidget(self.title_label)

    def setTitle(self, text):
        self.title_label.setText(text)

    def title(self):
        return self.title_label.text()


def _left_text(left, kind=None):
    """「剩余」列的文字：永久 / N 回合 / N 次。"""
    if left is None:
        return "永久"
    if kind == "use":
        return "%d 次" % int(left)
    return "%d 回合" % int(left)


def _fmt_sp(value, width=3):
    """SP 数值显示：整数、定宽（默认 3 字符），避免出现「8.0」。

    中文字体里 ASCII 数字与空格都是半宽，所以「%3d」能让各行的 SP 数字对齐；
    留 3 字符是为了容纳负数（如「-3」）。
    """
    try:
        f = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(f - round(f)) < 1e-9:
        return "%*d" % (int(width), int(round(f)))
    return "%*g" % (int(width), f)


def _talent_display(name, entry, element, ok):
    """共鸣天赋下拉项的文字 + tooltip。

    可装备时只列**与该风格元素相符**的来源，例如
    ``Excelsior!（31X·无·绚烂华美琉璃色）``；不可装备时标注「属性不符」，
    并把该天赋的全部来源（队伍·属性·风格）放进 tooltip。
    """
    team = entry.get("team")
    sources = list(entry.get("sources") or [])
    match = [s for s in sources
             if _talent_element_ok([s.get("element") or "无"], element)]
    tip_lines = ["   %s·%s·%s" % (s.get("team") or "—", s.get("element") or "无",
                                  s.get("style") or "—")
                 for s in sources]
    tip = "可装备该天赋的风格（队伍·属性·风格）：\n" + \
          ("\n".join(tip_lines) if tip_lines else "   —")
    if ok and match:
        first = match[0]
        part = "%s·%s" % (first.get("element") or "无",
                          first.get("style") or "—")
        if len(match) > 1:
            part += " 等 %d 个风格" % len(match)
        text = "%s（%s）" % (name, "·".join(x for x in (team, part) if x))
    elif ok:                      # 兼容没有 sources 的旧数据
        attrs = "/".join(entry.get("owners") or [])
        text = "%s（%s）" % (name, "·".join(x for x in (team, attrs) if x))
    else:
        text = "%s（%s）" % (name, "·".join(x for x in (team, "属性不符") if x))
    return text, tip


class _AspectCanvas(QWidget):
    """按控件宽度显示图片，高度按宽高比自动增长（超长时交给外层滚动）。"""

    def __init__(self, source=None, parent=None):
        super().__init__(parent)
        self._src = None
        self._last = None
        self._cached_pixmap = None
        self._cached_size = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(80)
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._delayed_sync)
        if source is not None:
            self.set_source(source)

    # ------------------------------------------------------------ 数据
    def set_source(self, source):
        self._src = source
        self._cached_pixmap = None
        self._cached_size = None
        self._sync_height()
        self.update()

    def source(self):
        return self._src

    def drawn(self):
        """最近一次绘制用的像素图（测试用）。"""
        return self._last

    def target_height(self, width=None):
        """给定宽度下，按原图宽高比算出的显示高度（不超过原图尺寸）。"""
        if self._src is None or self._src.isNull() or self._src.width() <= 0:
            return 80
        w = self.width() if width is None else width
        if w >= self._src.width():          # 比原图窄才缩放；否则保持原尺寸
            return self._src.height()
        return int(round(w * self._src.height() / float(self._src.width())))

    def _sync_height(self):
        h = max(80, self.target_height())
        if self.minimumHeight() != h:
            self.setMinimumHeight(h)

    # ------------------------------------------------------------ Qt
    def sizeHint(self):
        if self._src is None or self._src.isNull():
            return QSize(480, 320)
        return QSize(self._src.width(), self._src.height())

    def minimumSizeHint(self):
        return QSize(160, 80)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 拖拽缩放期间只防抖同步高度/缓存，避免每次事件 Smooth 全图重缩放
        self._resize_timer.start(50)

    def _delayed_sync(self):
        self._sync_height()
        self._cached_pixmap = None
        self._cached_size = None
        self.update()

    def paintEvent(self, event):
        if self._src is None or self._src.isNull():
            return
        w = self.width()
        h = max(80, self.target_height())
        size = QSize(w, h)
        if self._cached_pixmap is None or self._cached_size != size:
            # 拖拽中用快速插值，静止后由防抖回调清缓存再用 Smooth 重画
            smooth = (not self._resize_timer.isActive())
            self._cached_size = size
            self._cached_pixmap = self._src.scaled(
                w, h, Qt.KeepAspectRatio,
                Qt.SmoothTransformation if smooth else Qt.FastTransformation)
        self._last = self._cached_pixmap
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._cached_pixmap)


class _ScaledImageView(QScrollArea):
    """轴图查看器：**宽度始终铺满窗口**（超长时出现垂直滚动条，不压缩变形）。"""

    def __init__(self, pixmap=None, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)                 # 画布宽度跟随可视区
        self.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._canvas = _AspectCanvas()
        self.setWidget(self._canvas)
        if pixmap is not None:
            self.set_source(pixmap)

    def set_source(self, pixmap):
        self._canvas.set_source(pixmap)

    def source(self):
        return self._canvas.source()

    def canvas(self):
        return self._canvas


class TeamMemberRow(QFrame):
    """队伍中的一个位置：角色 + 风格。"""

    changed = pyqtSignal()

    def __init__(self, slot, data_source, parent=None):
        super().__init__(parent)
        self.slot = slot
        self.data_source = data_source
        self._loading = 0
        self._block_role_signal = False
        self._build_ui()
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
        self.talent_combo.setFixedWidth(170)
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

    def _on_talent_changed(self, *args):
        self._update_talent_tip()
        self._emit_changed()

    def _talent_candidates(self):
        """当前风格**可选**的共鸣天赋名（属性匹配）。

        SS / SSR 都可以选（SS 只用于轴图显示，不参与 OD 计算）；
        天赋与属性一一对应，所以只保留与该风格元素相符的那些。
        """
        rarity = self._style_rarity()
        if rarity not in ("SSR", "SS"):
            return []
        element = self._style_element()
        pool = self.data_source.resonance_pool()
        return sorted(name for name, entry in pool.items()
                      if _talent_element_ok(entry.get("owners") or [], element))

    def _populate_talents(self):
        """填充「共鸣天赋」下拉：只列**该风格可选**的天赋，外加（默认）/无。

        不可选的（属性不符）**不入列表**，而不是列出来置灰。
        SS 也能选，但效果只在 SSR 时计入计算（见 _member_resonance）。
        """
        prev = self.talent_combo.currentData() if self.talent_combo.count() else None
        pool = self.data_source.resonance_pool()
        element = self._style_element()
        with self._suspended():
            self.talent_combo.clear()
            self.talent_combo.addItem("（默认）", None)
            self.talent_combo.addItem("无", "")
            for name in self._talent_candidates():
                entry = pool.get(name) or {}
                text, tip = _talent_display(name, entry, element, True)
                self.talent_combo.addItem(text, name)
                self.talent_combo.setItemData(self.talent_combo.count() - 1, tip,
                                              Qt.ToolTipRole)
            pos = self.talent_combo.findData(prev)
            self.talent_combo.setCurrentIndex(pos if pos >= 0 else 0)
        self._refresh_talent_enabled()
        self._update_talent_tip()

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
            ok = can_equip and _talent_element_ok(entry.get("owners") or [], element)
            item.setEnabled(ok)
            text, tip = _talent_display(name, entry, element, ok)
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
        self._selected_passives = None   # 换角色后默认携带全部被动
        self._populate_styles(preserve="")
        # 角色为「无」时 OD 耳环也必须是「无」
        if not self.role():
            self._clear_earring()
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

    def _populate_styles(self, preserve=None):
        if self.role_combo.currentText() == "无":
            with self._suspended():
                self.style_combo.clear()
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
        with self._suspended():
            self.style_combo.clear()
            for style in styles:
                # 显示「风格名-稀有度-元素」，实际值仍保存纯风格名
                # 双稀有度风格存 (name, rarity)，便于区分 SS / SSR 两项
                if (style.name in DUAL_SS_SSR_STYLE_NAMES
                        and style.rarity in ("SS", "SSR")):
                    self.style_combo.addItem(
                        style.display_name(), (style.name, style.rarity))
                else:
                    self.style_combo.addItem(style.display_name(), style.name)
            pos = -1
            if preserve_name:
                if preserve_rarity is not None:
                    for i in range(self.style_combo.count()):
                        d = self.style_combo.itemData(i)
                        if (isinstance(d, tuple)
                                and d[0] == preserve_name
                                and d[1] == preserve_rarity):
                            pos = i
                            break
                if pos < 0:
                    for i in range(self.style_combo.count()):
                        d = self.style_combo.itemData(i)
                        if d == preserve_name or (
                                isinstance(d, tuple) and d[0] == preserve_name):
                            pos = i
                            break
            if pos >= 0:
                self.style_combo.setCurrentIndex(pos)
            elif styles:
                self.style_combo.setCurrentIndex(0)
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
        self.role_combo.setCurrentText(role if role else "无")
        # 程序化清空/设置角色时，耳环同步为「无」
        if not self.role():
            self._clear_earring()

    def _clear_earring(self):
        """OD 耳环强制为「无（不装备）」。"""
        pos = self.earring_combo.findData("")
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
            tpos = self.talent_combo.findData(tal)
            self.talent_combo.setCurrentIndex(tpos if tpos >= 0 else 0)
            self._populate_passives()
        self._refresh_talent_enabled()
        self._update_talent_tip()


# ======================================================================
# 一次行动
# ======================================================================
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
        install_no_wheel(self)      # 滚轮不修改下拉框 / 数值框

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 2, 6, 2)
        layout.setSpacing(5)

        self.member_combo = QComboBox()
        self.member_combo.setFixedWidth(MEMBER_W)
        self.member_combo.currentIndexChanged.connect(self._on_member_changed)
        layout.addWidget(self.member_combo)

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
        style = member.get("style", "")
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
        self._populate_members()
        self._populate_skills()
        self._apply_skill_data()
        self._sync_fixed_od()
        self._populate_targets()
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
            pos = self.member_combo.findData(member)
            if pos >= 0:
                self.member_combo.setCurrentIndex(pos)
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
        return ODSkill(
            base_hits=self.base_hits_spin.value(),
            combo_count=combo,
            fixed_od=self.fixed_od_spin.value(),
            resonance_31x=(self.owner._member_resonance_break(self.member_index)
                           if self.is_break() else 0.0),
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
            total += self.owner._member_ex_od_fraction(self.member_index) * 100.0
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
        return {
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

    def set_data(self, data):
        with self._suspended():
            self.member_index = int(data.get("member", 0) or 0)
            self._populate_members()
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


# ======================================================================
# 一个回合
# ======================================================================
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
                not no_od and self.od_combo.currentText() != "无")
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
        self.od_timing_combo.setEnabled(self.od_combo.currentText() != "无")
        self._sync_turn_type()
        self._apply_style()
        self.owner._reindex()   # 后置OD 沿用上一回合号
        self.changed.emit()

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
        self.setStyleSheet(TURN_CARD_STYLE % {"bg": bg, "accent": accent})

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


# ======================================================================
# 主界面
# ======================================================================
class _AxleImageWorker(QThread):
    """后台渲染轴图，避免长轴时卡死 UI。"""

    done = pyqtSignal(object, object)  # (QImage, error)

    def __init__(self, data, ds):
        super().__init__()
        self._data = data
        self._ds = ds

    def run(self):
        try:
            from 工具.排轴.axle_image import render_axle_image
            image = render_axle_image(self._data, ds=self._ds)
            self.done.emit(image, None)
        except Exception as e:
            self.done.emit(None, e)


class AxleODWindow(QFrame):
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

        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(
            ["角色", "风格", "状态", "效果", "剩余", "来源"])
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
                          (5, QHeaderView.ResizeToContents)):
            header.setSectionResizeMode(col, mode)
        self.state_table = table
        layout.addWidget(table)

        hint = QLabel("「剩余」按己方回合计（含当前回合）；永久状态显示「永久」。"
                      "只列出参与 OD / SP 计算的状态与 buff。")
        hint.setStyleSheet("color: #888888;")
        layout.addWidget(hint)
        return box

    def _snapshot_turn_states(self, turn_idx, tracker, combo_buffs):
        """记录该回合**开始时**每名队员的状态 / 连击 buff。"""
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
            if states or combos:
                entries.append({"slot": slot, "role": role, "style": style,
                                "states": states, "combos": combos})
        return entries

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
        for entry in self._state_book.get(idx, []):
            who = "角色%d %s" % (entry["slot"] + 1, entry["role"])
            for st in entry["states"]:
                rows.append((who, entry["style"], st["name"],
                             st.get("effect", ""), _left_text(st.get("left")),
                             st.get("source", "")))
            for cb in entry["combos"]:
                src = cb.get("source") or ""
                if cb.get("source_role"):
                    src = "%s（%s）" % (src, cb["source_role"]) if src else cb["source_role"]
                rows.append((who, entry["style"],
                             "连击数上升 +%g" % cb["amount"],
                             "连击 +%g" % cb["amount"],
                             _left_text(cb["left"], cb.get("kind")),
                             src))
        if not rows:
            rows = [("—", "", "（本回合开始时没有状态）", "", "", "")]

        title = "状态总览 · %s（回合开始时）" % turn.index_label.text()
        sig = (title, tuple(rows))
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
        for turn in self.turns:
            is_additional = turn.turn_type() in UNTIMED_TURN_TYPES
            level = turn.od_level()
            if is_additional:
                turn.set_index(number, additional=True)
                continue
            is_post_od = (level > 0 and turn.od_timing() == "后置OD")
            if level > 0 and level == prev_level:
                # 同一次 OD 发动的后续超频回合：沿用同一个回合号
                turn.set_index(number, post_od=is_post_od)
            elif is_post_od:
                turn.set_index(number, post_od=True)
            else:
                number += 1
                turn.set_index(number)
            prev_level = level

    # --------------------------------------------------------- calculation
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
                element = action.get_attack_element()
                resist = blanket or bool(element and element in resisted)
                # 目标数：全体攻击按「敌人数量」，单体攻击恒为 1
                battle = self._battle_params(resist, action.get_target_count())
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
