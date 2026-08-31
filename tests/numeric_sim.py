# -*- coding: utf-8 -*-
"""N01 模拟战斗助手 numeric_sim —— 供所有数值胜率类测试 import（不 import 任何测试文件）

用法：
    from numeric_sim import class_battle_matrix, player_panel, monster_of

    wins, avg_round = class_battle_matrix("战士", 11, {"str": 39}, {}, "dps", 16, seeds=8)
    # -> (8, 4.6)：8 场里胜 8 场，平均 4.6 回合

    st = player_panel("法师", 11, {"int": 39})          # E.player_final_stats 面板
    m  = monster_of("dps", 16)                           # C.build_monster 展开的怪 dict

实现口径（与 FRAMEWORK.md 一致）：
  - 直接构造 BT.Battle(btype="monster", enemy=怪, player=玩家)，
    循环 player_turn("attack"/"skill", ...) 直到 b.result 非空
  - 固定种子序列 seed 0..N-1：每场先 random.seed(seed) 再建怪建人开打（可复现）
  - 用真实引擎 E.player_final_stats / C.build_monster / BT.Battle，不 mock 核心公式
  - GWEN_GAME_DB 用 setdefault 指向 tests/test_game_data.db（尊重测试脚本预置的私有库）
"""
import os
import sys

_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # dragonfall/
_QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN_DIR))) # qqbot/
if _QQBOT_DIR not in sys.path:
    sys.path.insert(0, _QQBOT_DIR)
if _PLUGIN_DIR not in sys.path:
    sys.path.insert(0, _PLUGIN_DIR)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PLUGIN_DIR, "tests", "test_game_data.db"))

import random  # noqa: E402

from data.plugins.dragonfall.game import content as C  # noqa: E402
from data.plugins.dragonfall.game import engine as E  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402

# 自由属性点：初始 DEFAULT_ATTR_PTS=9 + 每级 +3（engine.py:841 升级结算），
# 11 级 = 9 + 10×3 = 39 点。任务卡 N01 明确用 39 点。
PLAYER_LV = 11
ATTR_PTS_TOTAL = C.DEFAULT_ATTR_PTS + (PLAYER_LV - 1) * 3  # 9 + 30 = 39

# 各职业代表技能（lv<=11 可学的攻击技能，use_skill=True 时使用；中文名，进 learned_skills）
REP_SKILL = {
    "战士": "猛击",     # 120% 物理
    "法师": "冰晶术",   # 105% 魔法
    "游侠": "瞄准射击",  # 140% 物理
    "牧师": "惩戒",     # 120% 魔法（lv10，单机唯一输出技）
    "刺客": "割裂",     # 115% 物理
    "拳师": "碎骨拳",   # 150% 物理
}

# 标准 39 点分配（职业主流加点，任务卡 N01）
STD_ATTR = {
    "战士": {"str": 39},
    "法师": {"int": 39},
    "游侠": {"agi": 39},
    "牧师": {"int": 39},
    "刺客": {"agi": 39},
    "拳师": {"str": 39},
}

_MAX_TURNS = 500  # 单场回合护栏（防极端情况死循环；正常对局远低于此）


def player_panel(cls: str, lv: int = PLAYER_LV, attr: dict | None = None, equip: dict | None = None) -> dict:
    """玩家最终面板：E.player_final_stats(cls, lv, equip, tier=0, attr) 结果 dict。

    docstring 用法：st["max_hp"] / st["atk"] / st["matk"] / st["def"] / st["spd"] / st["crit"] ...
    """
    return E.player_final_stats(cls, lv, equip or {}, 0, attr if attr is not None else {})


def monster_of(role: str, lv: int) -> dict:
    """C.build_monster 展开一只怪：role ∈ tank/dps/caster/speedster/healer/boss/elite。

    返回带 hp/max_hp/atk/def/matk/mdef/spd/exp/gold... 的完整怪 dict（无掉落、无技能）。
    """
    mid = "m_sim_%s_%d" % (role, lv)
    return C.build_monster(
        (mid, "测试%s" % role, role, lv, [], []),
        {"id": mid, "name": "测试%s" % role, "area": "field", "lv": lv},
    )


def class_battle_matrix(cls: str, lv: int, attr: dict, equip: dict | None,
                        monster_role: str, monster_lv: int,
                        seeds: int = 8, use_skill: bool = False) -> tuple[int, float]:
    """跨级胜率模拟：同一职业玩家 vs 同一只怪，固定种子跑 seeds 场。

    返回 (胜场数, 平均回合)。每场：random.seed(seed)（seed=0..seeds-1）→
    构造玩家（FRAMEWORK 模板，learned_skills 默认 []）→ BT.Battle → 循环
    player_turn 直到 b.result 为 victory/defeat（护栏 _MAX_TURNS 兜底）。

    use_skill=True：每回合按 REP_SKILL[cls] 施放代表技能（自动写入 learned_skills）；
    技能施放被拦截（蓝/资源/CD 未就绪）当回合自动转普攻。
    use_skill=False（默认）：纯普攻，基础战斗力对比。
    """
    equip = equip or {}
    assert cls in REP_SKILL, "未知职业: %s" % cls
    assert attr, "必须给属性点 dict（标准 39 点可查 STD_ATTR）"

    wins, rounds_sum = 0, 0
    m = monster_of(monster_role, monster_lv)  # 每格（怪）只建一次，与等级/角色完全确定
    for seed in range(max(1, int(seeds))):
        random.seed(seed)  # 固定种子序列 seed 0..N-1，可复现
        st = E.player_final_stats(cls, lv, equip, 0, attr)
        learned = [REP_SKILL[cls]] if use_skill else []
        player = {
            "class_name": cls, "level": lv, "class_tier": 0, "evolve_path": 0,
            "equipment": dict(equip), "attributes": dict(attr), "learned_skills": learned,
            "hp": st["max_hp"], "mp": st["max_mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
            "race": "human", "title_bonus": None,
        }
        b = BT.Battle(btype="monster", enemy=dict(m), player=player)
        skill_name = REP_SKILL[cls] if use_skill else None
        turns = 0
        while b.result is None and turns < _MAX_TURNS:
            # v152：round 已删除 → 用 _p_acts（玩家行动次数）判定技能拦截（未消耗行动则不变）
            prev_acts = b._p_acts
            b.player_turn("skill" if use_skill else "attack", skill_name, player)
            # 技能施放被拦截：player_turn 不消耗行动（_p_acts 不变、result 仍空）→ 转普攻
            if use_skill and b._p_acts == prev_acts and b.result is None:
                b.player_turn("attack", None, player)
            turns += 1
        if b.result == "victory":
            wins += 1
        # v152：回合数展示口径 = 行动轮次 _tick_no()（int(now/ACT_TICK)+1）
        rounds_sum += b._tick_no()
    avg_round = rounds_sum / max(1, int(seeds))
    return wins, round(avg_round, 2)


if __name__ == "__main__":
    # 自检示例：直接 python tests/numeric_sim.py
    for cls, attr in STD_ATTR.items():
        w, ar = class_battle_matrix(cls, 11, attr, {}, "dps", 11)
        print("%s 11v11 dps: %d/%d 胜, 平均 %s 回合" % (cls, w, 8, ar))