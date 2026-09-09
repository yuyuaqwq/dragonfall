# -*- coding: utf-8 -*-
"""v173.x 意见#154/#155：逃跑失败敌方读条越界补结算路径死亡判定。

玩家『逃跑』失败（慢动作，cast_flee > 0）后，敌方出招读条命中时刻 > 玩家下次
可行动点（越界）→ _hostile_phase 补结算分支（v167.3）直接调 _damage_player 结算，
此前该分支缺 _player_dead 判定 → 玩家 hp 归 0 但 result 不置 defeat → 命令层
ended=False 只存战斗状态，玩家血 0 不触发死亡（玩家实抓：逃跑时归0不会死）。

用 unittest.mock.patch 把 random.random 钉死（逃跑必败 + 敌方必命中），
低血玩家 10 档敌速扫描：任何一档 hp<=0 都必须 result=defeat 且 ended=True。
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


def make_monster(spd, atk=9999):
    return {
        "id": "t_flee_death", "name": "读条怪", "lv": 1, "role": "normal",
        "hp": 100000, "max_hp": 100000, "atk": atk, "def": 5,
        "matk": atk, "mdef": 5, "spd": spd, "crit": 0.05,
        "exp": 10, "gold": 10, "skills": [], "drops": [],
        "map": "测试", "map_area": "vila", "is_boss": False, "is_elite": False,
    }


def make_player(level=1):
    p = {
        "class_name": "战士", "level": level, "equipment": {}, "attributes": {},
        "class_tier": 0, "evolve_path": 1,
        "learned_skills": [], "skills": [], "skill_levels": {},
        "max_hp": 0, "max_mp": 0, "hp": 0, "mp": 0, "name": "测试勇者",
    }
    st = E.player_final_stats("战士", level, {}, 0, {})
    p["max_hp"], p["max_mp"] = st["max_hp"], st["max_mp"]
    p["hp"], p["mp"] = st["max_hp"], st["max_mp"]
    return p


def main():
    clean_db()
    print("【v173.x 意见#154/#155：逃跑失败读条越界补结算 → 死亡判定】")
    buggy = 0
    for spd in (5, 8, 10, 12, 15, 18, 20, 25, 30, 40):
        p = make_player(1)
        p["hp"] = 30  # 低血：敌方一击必杀
        b = BT.Battle("monster", make_monster(spd), {}, p)
        # roll 0.999 → 逃跑必败（同级同速 0.75 < 0.999）；敌方普攻必命中
        with unittest.mock.patch("random.random", return_value=0.999):
            logs, ended = b.actor_turn("flee", None, p)
        if p.get("hp", 1) <= 0:
            name = f"敌速 {spd}：玩家 hp<=0 → 必须 defeat 且战斗结束"
            ok = b.result == "defeat" and ended
            check(name, ok, f"result={b.result} ended={ended}")
            if not ok:
                buggy += 1
        # hp>0（敌方太慢没轮到）→ 战斗未结束可继续，不强制 defeat
    check("10 档敌速无一『血 0 不死』", buggy == 0, f"{buggy} 档异常")

    print(f"\n===== 结果：通过 {passed} / 失败 {failed} / 断言总数 {passed + failed} =====")
    return failed == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
