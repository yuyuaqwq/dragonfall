# -*- coding: utf-8 -*-
"""数值重设计 方案v2 预演：普通怪 v1 + Boss 血量成长 ×2.5（副本 Boss 保底大几十轮）。

曲线覆盖（curve_override 已修绑定链 bug，v131 教训）：
  - 普通怪五 role：HP成长 ×2、def成长 ×2~4.5、atk/matk ~×1.4
  - elite：HP 40→70（满装 3.8 轮 → 5-8 轮）、def 2.8→5.5
  - boss：**HP 成长 58→145（×2.5）** ← 鱼鱼 2026-08-27 拍板：副本 Boss 应保底大几十轮拼策略
  - hp_stage：16-30 每级 8%→5%（30级锚点 2.2→1.75）；atk_stage 不动
"""
import os, sys
_PD = os.getcwd()
sys.path.insert(0, os.path.join(_PD, "tests")); sys.path.insert(0, os.path.join(_PD, "scripts"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(_PD))))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PD, "tests", "test_game_data.db"))

from numeric_lib.env import setup_env
from numeric_lib.monster import curve_override
from numeric_lib.team import team_matrix
from numeric_lib.constants import LOADOUTS
from numeric_lib.report import md_table
from numeric_lib.gear import gear_loadout
import gen_numeric_matrix as GM
import numeric_sim as NS

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

with curve_override(growth=GROWTH_V2, hp_stage=HP_STAGE_V2):
    print("=" * 80)
    print("【方案v2 野外战斗（真实引擎胜率）】")
    print("=" * 80)
    for mlv, tag in [(11, "同级"), (16, "越5级"), (18, "越7级")]:
        w, r = NS.class_battle_matrix("战士", 11, {"str": 39}, {}, "dps", mlv, seeds=8)
        print(f"  裸装战士 11v{mlv}({tag}): {w}/8 胜 均{r}轮")
    w, r = NS.class_battle_matrix("法师", 11, {"int": 39}, {}, "dps", 11, seeds=8)
    print(f"  裸装法师 11v11: {w}/8 胜 均{r}轮")
    for lo, tag in [("solo_mid", "蓝+5"), ("team_purple9", "紫+9")]:
        g = gear_loadout(11, lo)
        w, r = NS.class_battle_matrix("战士", 11, {"str": 39}, g, "dps", 16, seeds=8)
        print(f"  {tag}战士 11v16: {w}/8 胜 均{r}轮")
    w, r = NS.class_battle_matrix("拳师", 11, {"str": 39}, {}, "dps", 11, seeds=8)
    print(f"  裸装拳师 11v11: {w}/8 胜 均{r}轮")
    for cn, *_ in GM.CLASSES:
        for lo in ("naked",):
            g = gear_loadout(11, lo)
            k, s, v = GM.eval_fight(cn, 11, g, "elite", 11)
            print(f"  裸装{cn} vs 11精英: {k}轮 承伤{s} {v}")
    k, s, v = GM.eval_fight("战士", 20, gear_loadout(20, "solo_mid"), "boss", 20)
    print(f"  蓝+5战士 20v20野外Boss: {k}轮 承伤{s} {v}")

    print("=" * 80)
    print("【方案v2 副本 Boss（新判定：✅40~80 策略长盘 / 🟡20~40·80~100 / ⚠️<20 秒杀 / 🔴>100 或扛不住）】")
    print("=" * 80)
    for lo in ("team_mid", "team_purple9"):
        rows = team_matrix(loadout=lo)
        print(f"\n--- {LOADOUTS[lo]['label']} ---")
        print(md_table(rows, ["iid", "lv", "boss_lv", "boss_hp", "ratio", "rounds", "survive", "flag"],
                       {"iid": "副本", "lv": "Lv", "boss_lv": "BossLv", "boss_hp": "BossHP",
                        "ratio": "B:普", "rounds": "击杀轮", "survive": "承伤轮", "flag": "判定"}))
        ok = [r for r in rows if r["flag"] == "✅"]
        fast = [r for r in rows if r["flag"] == "⚠️"]
        print(f"  ✅{len(ok)} 🟡{sum(1 for r in rows if r['flag']=='🟡')} ⚠️{len(fast)} 🔴{sum(1 for r in rows if r['flag']=='🔴')}")