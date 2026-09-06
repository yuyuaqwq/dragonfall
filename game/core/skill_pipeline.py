# -*- coding: utf-8 -*-
"""技能攻击结算管线（v176 根治 God Method：_player_skill 攻击分支 520 行 → 阶段化）。

设计（docs/SKILL_PIPELINE_REDESIGN_v176.md）：
  一次攻击技能结算 = 构造 _AttackCast → 依次调用阶段方法 → 取 logs。
  中间状态挂 ctx（不再 15 个局部变量飞线），乘区收 dict（可插拔可测）。

阶段：
  1. setup       基础信息（kind/mech/lv/stats/目标）
  2. roll_crit   暴击判定（含潜行/满弦/必暴）
  3. mult        乘区装配（frozen/stack/cond/passive/reaction/职业/词条 → mults dict → pmult）
  4. segments    段循环伤害（multi 段，每段 _seg_damage）
  5. post_total  总伤后处理（filter/weapon passive/v153/v169/抗性/闪避/AOE/落地/吸血）
  6. effects     标签/印记/命中效果/机制结算

迁移：把 _player_skill 攻击分支代码按阶段原样搬入（行为逐行等价），
      _player_skill 只留编排。battle 引用经 self.battle 访问。
"""
from __future__ import annotations


class _AttackCast:
    """一次攻击技能结算上下文（战斗内瞬态，不序列化）。"""

    __slots__ = (
        "battle", "st", "est", "player", "info", "kind", "mech", "lv",
        "skill_name", "logs", "mval", "p_mech",
        # 阶段产物（原局部变量）
        "is_crit", "lucky", "stealth_mult", "stealth_hit", "effs",
        "mults", "execute_tag", "element", "procs",
        "multi", "pmult", "total", "magi_part",
        "reaction_log", "tags", "cond_label", "magic_bonus",
        "_seg_pp_phys", "_seg_pf_phys", "_seg_pp_magi", "_seg_pf_magi",
    )

    def __init__(self, battle, st: dict, player: dict, info: dict,
                 skill_name: str, target=None):
        self.battle = battle
        self.st = st
        self.player = player
        self.info = info
        self.skill_name = skill_name
        self.kind = info["kind"]
        self.mech = info.get("mech", "")
        self.lv = battle._skill_lv  # noqa: 调用方已设? 改由 battle 传
        self.logs = []
        self.mults = {}       # 乘区表：来源名 → 倍率
        self.tags = []
        self.total = 0
        self.magi_part = 0
        self.target = target

    # ============ 阶段方法（由 _player_skill 编排调用） ============
    def run(self) -> list:
        """整条管线（编排用）。"""
        # 各阶段依次执行，实现逐步从 _player_skill 迁入
        return self.logs
