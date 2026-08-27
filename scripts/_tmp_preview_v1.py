# -*- coding: utf-8 -*-
"""数值重设计 方案v1 预演：curve_override 覆盖怪物曲线 → 引擎胜率矩阵 + 轮数表。

参数（v1，依据 2026-08-27 全量矩阵分析）：
  - 普通怪 HP成长 ×2（dps 15→30），def成长 ×2.2~4.5（dps 2.0→5.0），atk/matk成长 ~×1.4
  - elite：HP成长 40→70（满装精英 3.8 轮 → 目标 5-8）、def 2.8→5.5
  - hp_stage：16-30 每级 8%→5%，30 级锚点 2.2→1.75（平滑，整体 -25%）
  - atk_stage 不动；boss/副本 Boss 不动
"""
import os, sys, random
_PD = os.getcwd()
sys.path.insert(0, os.path.join(_PD, "tests")); sys.path.insert(0, os.path.join(_PD, "scripts"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(_PD))))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PD, "tests", "test_game_data.db"))

from numeric_lib.env import setup_env
from numeric_lib.monster import curve_override
import gen_numeric_matrix as GM  # noqa
from numeric_lib.constants import CLASSES, LOADOUTS, TEAM_BUFF
from numeric_lib.gear import gear_loadout
import numeric_sim as NS

GROWTH_V1 = {
    "tank":      {"hp": 36, "atk": 3.5, "def": 4.0, "matk": 1.2, "mdef": 2.8, "spd": 0.3},
    "dps":       {"hp": 30, "atk": 5.0, "def": 5.0, "matk": 1.5, "mdef": 2.4, "spd": 1.0},
    "caster":    {"hp": 22, "atk": 1.8, "def": 3.5, "matk": 5.0, "mdef": 4.0, "spd": 0.9},
    "speedster": {"hp": 22, "atk": 3.5, "def": 4.5, "matk": 1.5, "mdef": 2.0, "spd": 1.8},
    "healer":    {"hp": 20, "atk": 1.5, "def": 3.0, "matk": 4.0, "mdef": 3.0, "spd": 0.8},
    "elite":     {"hp": 70, "atk": 6.5, "def": 5.5, "matk": 5.0, "mdef": 4.5, "spd": 1.5},
    # boss 不动
}
HP_STAGE_V1 = [(15, 1.0), (30, 1.75), (60, 2.65), (999, 3.45)]
# 原曲线对照：(15,1.0),(30,2.2),(60,3.4),(999,4.6)

def run_matrix(label, growth, hp_stage):
    print(f"\n{'='*80}\n【{label}】\n{'='*80}")
    with curve_override(growth=growth, hp_stage=hp_stage):
        # 1. 裸装跨级胜率（真实引擎）
        for mlv, tag in [(11, "同级"), (16, "越5级"), (18, "越7级")]:
            w, r = NS.class_battle_matrix("战士", 11, {"str": 39}, {}, "dps", mlv, seeds=8)
            print(f"  裸装战士 11v{mlv}({tag}): {w}/8 胜 均{r}轮")
        w, r = NS.class_battle_matrix("法师", 11, {"int": 39}, {}, "dps", 11, seeds=8)
        print(f"  裸装法师 11v11: {w}/8 胜 均{r}轮")
        # 2. 满装战士 11v16
        g5 = gear_loadout(11, "solo_mid")
        w, r = NS.class_battle_matrix("战士", 11, {"str": 39}, g5, "dps", 16, seeds=8)
        print(f"  蓝+5战士 11v16: {w}/8 胜 均{r}轮")
        # 3. 精英/野外boss 轮数（模型）
        for cn, *_ in CLASSES:
            for lo in ("naked", "solo_mid"):
                g = gear_loadout(11, lo)
                k, s, v = GM.eval_fight(cn, 11, g, "elite", 11)
                print(f"  {LOADOUTS[lo]['label']:6s} {cn} vs 11精英: {k}轮 承伤{s} {v}")
            break  # 只打印战士代表
        k, s, v = GM.eval_fight("战士", 20, gear_loadout(20, "solo_mid"), "boss", 20)
        print(f"  蓝+5战士 20v20野外Boss: {k}轮 承伤{s} {v}")

run_matrix("方案v1（新参数）", GROWTH_V1, HP_STAGE_V1)
run_matrix("现状对照", None, None)