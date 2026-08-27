# -*- coding: utf-8 -*-
"""战斗模拟包装：复用 tests/numeric_sim.py（真实引擎 BT.Battle，固定种子，可复现）。

对外提供：
  win_rate(cls, lv, attr, equip, role, mlv, seeds, use_skill) -> (wins, avg_round)
  panel(cls, lv, attr, equip) -> 面板（numeric_sim.player_panel 别名）
⚠️ 历史教训：玩家 dict 必须传同一个给 BT.Battle（战斗内 hp 修改保留），
   numeric_sim.class_battle_matrix 已按此实现；本模块不改其语义。
"""
from .env import setup_env  # noqa: F401
import numeric_sim as NS  # noqa: E402


def panel(cls: str, lv: int, attr: dict | None = None, equip: dict | None = None) -> dict:
    """玩家最终面板（E.player_final_stats 结果，直接透传 numeric_sim）。"""
    return NS.player_panel(cls, lv, attr, equip)


def monster_of(role: str, lv: int) -> dict:
    """一只怪（C.build_monster 展开）—— 与 numeric_sim 同源。"""
    return NS.monster_of(role, lv)


def win_rate(cls: str, lv: int, attr: dict | None, equip: dict | None,
             role: str, mlv: int, seeds: int = 8, use_skill: bool = False):
    """真实引擎胜率：(胜场, 平均回合)。attr=None → 职业推荐 39 点；equip={} = 裸装。"""
    return NS.class_battle_matrix(cls, lv, attr, equip, role, mlv, seeds=seeds, use_skill=use_skill)


def win_rate_matrix(classes: list[str], lv: int, attr_mode: str = "auto",
                    equip: dict | None = None, role: str = "dps", mlv: int = 11,
                    seeds: int = 8) -> dict:
    """多职业 × 单档怪 胜率矩阵 → {职业名: {"wins": n, "rounds": x}}。"""
    from .constants import cls_name
    out = {}
    for cls in classes:
        attr = None if attr_mode == "auto" else attr_mode
        wins, rounds = win_rate(cls, lv, attr, equip, role, mlv, seeds=seeds)
        out[cls_name(cls)] = {"wins": wins, "rounds": round(rounds, 2)}
    return out