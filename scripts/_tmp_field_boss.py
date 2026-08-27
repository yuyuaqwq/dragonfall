# -*- coding: utf-8 -*-
"""野外 Boss 团队化（方案C）预演：v2 曲线 + MONSTER_MODS hp_mult=8.0（进程内注入）。

目标（鱼鱼 2026-08-27）：野外 Boss = 团队首领 —— 单刷蓝+5 打不动（>100轮），
4 人组队蓝+5 40~80 轮策略战；野外精英保持 5-8 轮遭遇战。
"""
import os, sys
_PD = os.getcwd()
sys.path.insert(0, os.path.join(_PD, "tests")); sys.path.insert(0, os.path.join(_PD, "scripts"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(_PD))))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PD, "tests", "test_game_data.db"))

from numeric_lib.env import setup_env
from numeric_lib.monster import curve_override
from numeric_lib.player import PlayerOptions, build_player, per_action_dmg
from numeric_lib.gear import gear_loadout
from numeric_lib.constants import CLASSES, TEAM_BUFF
from data.plugins.dragonfall.game import content as C
from data.plugins.dragonfall.game import engine as E
from data.plugins.dragonfall.game.data import monster_mods as MM

GROWTH_V2 = {
    "tank":      {"hp": 36, "atk": 3.5, "def": 4.0, "matk": 1.2, "mdef": 2.8, "spd": 0.3},
    "dps":       {"hp": 30, "atk": 5.0, "def": 5.0, "matk": 1.5, "mdef": 2.4, "spd": 1.0},
    "caster":    {"hp": 22, "atk": 1.8, "def": 3.5, "matk": 5.0, "mdef": 4.0, "spd": 0.9},
    "speedster": {"hp": 22, "atk": 3.5, "def": 4.5, "matk": 1.5, "mdef": 2.0, "spd": 1.8},
    "healer":    {"hp": 20, "atk": 1.5, "def": 3.0, "matk": 4.0, "mdef": 3.0, "spd": 0.8},
    "elite":     {"hp": 70, "atk": 6.5, "def": 5.5, "matk": 5.0, "mdef": 4.5, "spd": 1.5},
    "boss":      {"hp": 145, "atk": 7.5, "def": 3.8, "matk": 6.0, "mdef": 3.4, "spd": 1.8},
}
HP_STAGE_V2 = [(15, 1.0), (30, 1.75), (60, 2.65), (999, 3.45)]
FIELD_BOSS_HP_MULT = 8.0

def field_mult(lv):
    """野外 Boss 团队血量系数分档：低段人多血厚（团队首领）、高段玩家输出成长快需放缓。
    目标：4 人组队蓝+5 全员 40~80 轮（鱼鱼 2026-08-27 团队化标准）。"""
    if lv <= 50:
        return 8.0
    if lv <= 80:
        return 6.0
    return 5.0

def scan_field_bosses():
    """扫描 subareas 配置里所有 role=boss 的条目（(mid, name, role, lv, skills, drops)）。"""
    found = []
    for _, sub in getattr(C, "SUBAREAS", {}).items():
        # 兼容两种容器形态：dict 直接 / list 含 dict
        items = sub.values() if isinstance(sub, dict) else sub
        for it in items:
            if not isinstance(it, dict):
                continue
            for key in ("boss",):
                b = it.get(key)
                if isinstance(b, (list, tuple)) and len(b) >= 4 and b[2] == "boss":
                    found.append(b)
    return found

# 若 SUBAREAS 不存在换个取法：直接扫 subareas.py 模块数据
if not hasattr(C, "SUBAREAS"):
    from data.plugins.dragonfall.game.data import subareas as SA
    C.SUBAREAS = dict(getattr(SA, "SUBAREAS", {}))

with curve_override(growth=GROWTH_V2, hp_stage=HP_STAGE_V2):
    bosses = scan_field_bosses()
    print(f"扫描到野外 Boss {len(bosses)} 条")
    rows = []
    for b in bosses:
        mid, name, role, lv, skills, drops = b[:6]
        # 进程内注入 MONSTER_MODS hp_mult（不落盘；按等级分档）
        saved_mod = MM.MONSTER_MODS.get(mid, {})
        MM.MONSTER_MODS[mid] = dict(saved_mod, hp_mult=field_mult(lv))
        try:
            m = C.build_monster(tuple(b), {"id": mid, "name": name, "area": "field"})
            for n, tag in [(1, "单刷"), (4, "4人组队")]:
                st = build_player("cls_zhan_shi", lv, gear_loadout(lv, "solo_mid"), PlayerOptions(), potion=0.0)
                d = per_action_dmg("cls_zhan_shi", lv, gear_loadout(lv, "solo_mid"),
                                   m.get("def", 0), m.get("mdef", 0), PlayerOptions(), potion_on=True)
                kill = m.get("max_hp", 1) / max(d * n * (TEAM_BUFF if n > 1 else 1.0), 1)
                hit = max(E.calc_damage(int(m.get("atk", 0) * 1.35), int(st.get("def", 0)), variance=0.0),
                          E.calc_damage(int(m.get("matk", 0) * 1.35), int(st.get("mdef", 0)), variance=0.0), 1)
                surv = st.get("max_hp", 1000) * n / hit
                rows.append({"Boss": name[:14], "Lv": lv, "档": tag,
                             "HP": f"{m.get('max_hp',0):,}", "杀轮": round(kill, 1), "承伤": round(surv, 1)})
        finally:
            if saved_mod:
                MM.MONSTER_MODS[mid] = saved_mod
            else:
                MM.MONSTER_MODS.pop(mid, None)
    for tag in ("单刷", "4人组队"):
        print(f"\n--- 野外 Boss（蓝+5 战士，{tag}，hp_mult 分档 8/6/5）---")
        for r in [x for x in rows if x["档"] == tag]:
            flag = "🔴" if r["杀轮"] > 100 or r["承伤"] < r["杀轮"] * 0.9 else "✅" if 30 <= r["杀轮"] <= 90 else "🟡"
            print(f"  {r['Boss']:<16} Lv{r['Lv']:<3} HP{r['HP']:>10} 杀{r['杀轮']:>6.1f}轮 承伤{r['承伤']:>6.1f} {flag}")