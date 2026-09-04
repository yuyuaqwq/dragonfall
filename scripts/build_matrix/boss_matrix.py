# -*- coding: utf-8 -*-
"""v175 Boss 侧提取：22 副本 × 阶段档位匹配 → 门禁/期望引擎共用。

单人职业流派矩阵只打 min_players=1 的 12 本（用对应阶段档位）；
多人本沿用 team_comp 口径（test_numeric_team_comp），不硬塞单人。

接口：
  BOSS_LIST           全部 Boss 简表
  solo_instances()    单人可进副本列表（min_players=1）
  stage_boss_target(stage) 每阶段推荐打的单人 Boss（玩家lv 对齐 Boss lv）
  boss_panel(boss_def)     Boss 真实面板（C.build_monster 展开，boss role）
"""
from __future__ import annotations
import os, sys, json

_BM_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS = os.path.dirname(_BM_DIR)
_PLUGIN = os.path.dirname(_SCRIPTS)
_QQBOT = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN)))
_TESTS = os.path.join(_PLUGIN, "tests")
for _p in (_QQBOT, _PLUGIN, _TESTS, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_TESTS, "test_game_data.db"))

from data.plugins.dragonfall.game import content as C        # noqa: E402
from data.plugins.dragonfall.game.data import instances as I  # noqa: E402

# 阶段 → 玩家等级/装备档（与 numeric_lib STAGES / build_matrix STAGE_CFG 对齐）
STAGE_CFG = [
    ("P1", 10, "solo_low"),
    ("P2", 24, "solo_mid"),
    ("P3", 45, "team_purple9"),
    ("P4", 75, "team_purple9"),
    ("P5", 95, "team_orange9"),
]

# 单人可进副本（min_players=1）—— 实时从 instances.py 数据判断（勿硬编码，防数据改后失真）
SOLO_INSTANCES = [iid for iid, inst in C.INSTANCES.items()
                  if inst.get("boss") and inst.get("min_players", 1) == 1]

# 阶段推荐 Boss（对齐玩家 lv 与 Boss lv；单人本优先，多人本标注 team）
STAGE_BOSS = {
    "P1": ["inst_goblin_camp", "inst_deer_fort"],        # 哥布林15/20、鹿角18/23
    "P2": ["inst_sea_cave", "inst_holy_trial"],           # 海蚀22/27、试炼36/41
    "P3": ["inst_old_king_tomb", "inst_sunken_ship"],     # 老王35/40、沉船38/43
    "P4": ["inst_elven_ruins", "inst_moon_temple"],       # 精灵58/63、月神60/65
    "P5": ["inst_ash_temple", "inst_abyss_gate"],         # 烬山82/87、深渊90/95
}


def boss_def_of(iid: str):
    """单副本 Boss 定义（instances.py 6元组 or None）。"""
    inst = C.INSTANCES.get(iid)
    if not inst:
        return None
    return inst.get("boss")


def boss_panel(boss_def, boss_lv: int | None = None):
    """Boss 真实面板（C.build_monster 展开）。boss_def 6元组 (id,名,role,lv,技能,掉落)。"""
    if boss_def is None:
        return None
    from numeric_lib.monster import build as _mb
    lv = boss_lv or int(boss_def[3])
    # numeric_lib.monster.build 需要 mid + map_obj
    mid = boss_def[0]
    map_obj = {"id": mid, "name": boss_def[1], "area": "instance", "lv": lv}
    try:
        m = _mb(boss_def[2], lv, mid=mid, map_obj=map_obj)
        if not m.get("max_hp"):
            m["max_hp"] = m.get("hp", 1000)
        return m
    except Exception:
        # fallback 简单 boss 模板
        m = _mb("boss", lv)
        return m


def solo_instances() -> list[dict]:
    """单人可进副本简表（按 inst_lv 排序）。"""
    out = []
    for iid in SOLO_INSTANCES:
        inst = C.INSTANCES.get(iid)
        boss = inst.get("boss") if inst else None
        if not inst or not boss:
            continue
        out.append({
            "iid": iid, "name": inst.get("name"), "inst_lv": inst.get("lv"),
            "min_players": inst.get("min_players"), "max_players": inst.get("max_players"),
            "boss_id": boss[0], "boss_name": boss[1], "boss_lv": boss[3],
        })
    return out


def stage_boss_target(stage: str) -> list[dict]:
    """阶段推荐 Boss 目标（STAGE_BOSS 映射到实例）。"""
    out = []
    for iid in STAGE_BOSS.get(stage, []):
        inst = C.INSTANCES.get(iid)
        boss = inst.get("boss") if inst else None
        if not boss:
            continue
        out.append({
            "iid": iid, "name": inst.get("name"), "inst_lv": inst.get("lv"),
            "min_players": inst.get("min_players"),
            "boss_name": boss[1], "boss_lv": boss[3],
        })
    return out


def all_bosses() -> list[dict]:
    """22 本全 Boss 简表。"""
    out = []
    for iid, inst in C.INSTANCES.items():
        boss = inst.get("boss")
        if not boss:
            continue
        out.append({
            "iid": iid, "name": inst.get("name"), "inst_lv": inst.get("lv"),
            "min_players": inst.get("min_players"), "max_players": inst.get("max_players"),
            "boss_name": boss[1], "boss_lv": boss[3],
        })
    out.sort(key=lambda x: x["inst_lv"])
    return out


if __name__ == "__main__":
    print("== 22 本全 Boss ==")
    for b in all_bosses():
        solo = "✅单" if b["min_players"] == 1 else f"多人{ b['min_players']}-{ b['max_players']}"
        print(f"  {b['iid']:<22} Lv{b['inst_lv']:<4} {solo:<10} {b['boss_name']} Lv{b['boss_lv']}")
    print("\n== 单人可进 12 本 ==")
    for s in solo_instances():
        print(f"  {s['iid']:<22} Lv{s['inst_lv']:<4} {s['boss_name']} Lv{s['boss_lv']}")
