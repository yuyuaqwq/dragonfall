# -*- coding: utf-8 -*-
"""v130.7 意见#28：逃跑成功率受等级差+速度差影响（battle._do_flee）

公式（数值全走 constants.py）：
    flee_rate = clamp(FLEE_CHANCE + (玩家lv-敌lv)*FLEE_LEVEL_STEP
                      + (玩家spd-敌spd)*FLEE_SPD_STEP, FLEE_MIN, FLEE_MAX)
    FLEE_CHANCE=0.75  FLEE_LEVEL_STEP=0.05/级  FLEE_SPD_STEP=0.01/点  clamp [0.15, 0.95]
用 unittest.mock.patch 把 random.random 钉死，逐边界断言（比统计稳定）。
"""
import os
import sys
import unittest.mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, BT, db, clean_db  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def make_monster(lv=5, spd=10, hp=100000):
    return {
        "id": "t_flee", "name": "测试怪", "lv": lv, "role": "normal",
        "hp": hp, "max_hp": hp, "atk": 10, "def": 5,
        "matk": 5, "mdef": 5, "spd": spd, "crit": 0.05,
        "exp": 10, "gold": 10, "skills": [], "drops": [],
        "map": "测试", "map_area": "vila", "is_boss": False, "is_elite": False,
    }


def make_player(level=10):
    p = {
        "class_name": "战士", "level": level, "equipment": {}, "attributes": {},
        "class_tier": 0 if level < 30 else 1, "evolve_path": 1,
        "learned_skills": [], "skills": [], "skill_levels": {},
        "max_hp": 0, "max_mp": 0, "hp": 0, "mp": 0, "name": "测试勇者",
    }
    st = E.player_final_stats("战士", level, {}, 0 if level < 30 else 1, {})
    p["max_hp"], p["max_mp"] = st["max_hp"], st["max_mp"]
    p["hp"], p["mp"] = st["max_hp"], st["max_mp"]
    return p


def _spd_of(level):
    return E.player_final_stats("战士", level, {}, 0 if level < 30 else 1, {})["spd"]


def flee(p_lv, e_lv, e_spd=None, roll=None, btype="monster"):
    """构造战斗并执行一次逃跑（roll = 钉死的 random.random 返回值）。"""
    p = make_player(p_lv)
    if e_spd is None:
        e_spd = _spd_of(p_lv)
    b = BT.Battle(btype, make_monster(lv=e_lv, spd=e_spd), {}, p)
    with unittest.mock.patch("random.random", return_value=roll):
        logs, ended = b.player_turn("flee", None, p)
    return b, logs, ended


def main():
    clean_db()
    print("【v130.7 意见#28：逃跑率 = 基础 0.75 ± 等级差/速度差，clamp [0.15, 0.95]】")

    print("· 常量落位（数据驱动，不进引擎硬编码）")
    from data.plugins.dragonfall.game.core.constants import (
        FLEE_CHANCE, FLEE_LEVEL_STEP, FLEE_SPD_STEP, FLEE_MIN, FLEE_MAX,
    )
    check("FLEE_CHANCE=0.75 保留为基础值", FLEE_CHANCE == 0.75, FLEE_CHANCE)
    check("FLEE_LEVEL_STEP=0.05（每级 ±5%）", FLEE_LEVEL_STEP == 0.05, FLEE_LEVEL_STEP)
    check("FLEE_SPD_STEP=0.01（每点 ±1%）", FLEE_SPD_STEP == 0.01, FLEE_SPD_STEP)
    check("FLEE_MIN=0.15（下限）", FLEE_MIN == 0.15, FLEE_MIN)
    check("FLEE_MAX=0.95（上限）", FLEE_MAX == 0.95, FLEE_MAX)

    print("· 同级同速 → 成功率 0.75（既有行为不回归）")
    b, logs, ended = flee(10, 10, roll=0.74)
    check("roll 0.74(<0.75) 逃成", ended and b.result == "fled", f"result={b.result} ended={ended}")
    check("成功文案『成功脱离了战斗』", any("成功脱离了战斗" in x for x in logs), logs)
    b, logs, ended = flee(10, 10, roll=0.76)
    check("roll 0.76(>0.75) 逃败", not ended and b.result is None, f"result={b.result} ended={ended}")
    check("失败文案无修正原因", any("逃跑失败" in x and "几乎逃不脱" not in x for x in logs), logs)

    print("· 玩家高 5 级 → 0.75+0.25=1.0 clamp 到上限 0.95")
    b, logs, ended = flee(15, 10, roll=0.949)
    check("roll 0.949(<0.95) 逃成", ended and b.result == "fled", f"result={b.result}")
    b, logs, ended = flee(15, 10, roll=0.951)
    check("roll 0.951(>0.95) 逃败（上限生效，不保 100%）", not ended, f"ended={ended}")

    print("· 玩家低 8 级 → 0.75-0.40=0.35")
    b, logs, ended = flee(2, 10, roll=0.349)
    check("roll 0.349(<0.35) 逃成", ended and b.result == "fled", f"result={b.result}")
    b, logs, ended = flee(2, 10, roll=0.351)
    check("roll 0.351(>0.35) 逃败", not ended and b.result is None, f"result={b.result}")
    check("失败提示含『敌方比你高 8 级』", any("敌方比你高 8 级" in x for x in logs), logs)

    print("· 玩家低 15 级 → 0.75-0.75=0 clamp 到下限 0.15")
    b, logs, ended = flee(1, 16, roll=0.149)
    check("roll 0.149(<0.15) 仍可逃成（下限保底）", ended and b.result == "fled", f"result={b.result}")
    b, logs, ended = flee(1, 16, roll=0.151)
    check("roll 0.151(>0.15) 逃败", not ended, f"ended={ended}")

    print("· 速度差单独生效：同级敌快 10 点 → 0.75-0.10=0.65")
    p_spd = _spd_of(10)
    b, logs, ended = flee(10, 10, e_spd=p_spd + 10, roll=0.649)
    check("roll 0.649(<0.65) 逃成", ended and b.result == "fled", f"result={b.result}")
    b, logs, ended = flee(10, 10, e_spd=p_spd + 10, roll=0.651)
    check("roll 0.651(>0.65) 逃败", not ended, f"ended={ended}")
    check("失败提示含『敌方比你快 10 点』", any("敌方比你快 10 点" in x for x in logs), logs)

    print("· 速度差单独生效：同级我快 10 点 → 0.75+0.10=0.85")
    b, logs, ended = flee(10, 10, e_spd=p_spd - 10, roll=0.849)
    check("roll 0.849(<0.85) 逃成", ended and b.result == "fled", f"result={b.result}")
    b, logs, ended = flee(10, 10, e_spd=p_spd - 10, roll=0.851)
    check("roll 0.851(>0.85) 逃败", not ended, f"ended={ended}")

    print("· worldboss / pvp 仍不可逃（既有行为不回归）")
    b, logs, ended = flee(10, 10, roll=0.74, btype="worldboss")
    check("worldboss 提示『这里无法逃跑』", any("这里无法逃跑" in x for x in logs), logs)
    check("worldboss 未逃跑未结束", not ended and b.result is None, f"result={b.result} ended={ended}")
    b, logs, ended = flee(10, 10, roll=0.74, btype="pvp")
    check("pvp 提示『这里无法逃跑』", any("这里无法逃跑" in x for x in logs), logs)
    check("pvp 未逃跑未结束", not ended and b.result is None, f"result={b.result} ended={ended}")

    print(f"\n===== 结果：通过 {passed} / 失败 {failed} / 断言总数 {passed + failed} =====")
    return failed == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)