#!/usr/bin/env python3
"""v180E 阶段4 武器特效断链修复 + 数值下沉门禁。

背景（2026-09-07 发现）：
- equip_roster 99 处 weapon_effect 声明，但 generate_roster_equip 从名册生成装备时
  不带 weapon_effect 字段 → 玩家穿上特效装备实际不触发（P0 系统性断链）
- 本门禁验证：
  1. 带 weapon_effect 的名册装备 → generate_roster_equip 产出实例带 weapon_effect + we_data
  2. 装备后 has_effect/effect_data 能读到参数
  3. 特效真实触发（以龙脊大剑 star_pierce 穿星为代表：每 4 次攻击附带真伤）
  4. 无 we_data 的旧装备（手工塞 key）→ effect_data 回退空 → handler 缺省兜底（回归）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import clean_db

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


async def main():
    clean_db()
    from data.plugins.dragonfall.game.core import drops
    from data.plugins.dragonfall.game.data.equip_roster import EQUIP_ROSTER
    from data.plugins.dragonfall.game.core.weapon_effects import (
        weapon_effect_ids, effect_data, has_effect,
    )

    print("===== v180E 阶段4 武器特效断链修复 =====\n")

    # 1. 带 weapon_effect 的名册装备 → 实例带 key + we_data
    we_items = [(rid, r) for rid, r in EQUIP_ROSTER.items() if r.get("weapon_effect")]
    check("名册有带 weapon_effect 装备", len(we_items) >= 9, f"n={len(we_items)}")

    bad = []
    for rid, r in we_items:
        eq = drops.generate_roster_equip(rid)
        if eq.get("weapon_effect") != r.get("weapon_effect"):
            bad.append(f"{rid}: 实例无 weapon_effect")
    check("generate_roster_equip 带 weapon_effect（断链修复）", not bad, str(bad[:3]))

    # 2. we_data 随实例携带（9 件已配参）
    for rid, r in we_items:
        eq = drops.generate_roster_equip(rid)
        if r.get("we_data") and eq.get("we_data") != r.get("we_data"):
            bad.append(f"{rid}: we_data 不一致")
    check("we_data 随实例携带", not bad, str(bad[:3]))

    # 3. 装备后 has_effect / effect_data 读到参数
    r0 = we_items[0][1]
    eq0 = drops.generate_roster_equip(we_items[0][0])
    player = {
        "class_name": "战士", "level": 85, "hp": 9999, "max_hp": 9999,
        "equipment": {"weapon": eq0}, "buffs": {}, "attributes": {"str": 90},
        "learned_skills": [], "race": "human",
    }
    ids = weapon_effect_ids(None, player)
    check("装备后 weapon_effect_ids 返回 key", r0["weapon_effect"] in ids, f"ids={ids}")

    # 4. 特效真实触发（龙脊大剑 star_pierce：穿星）
    import random as _rnd
    _rnd.seed(7)
    from data.plugins.dragonfall.game import battle as BT
    p = player
    e = {"name": "测试怪", "hp": 9000, "max_hp": 10000, "atk": 100, "def": 50, "mdef": 50,
         "spd": 10, "lv": 85, "buffs": {}}
    b = BT.Battle("monster", e, {}, p)
    # 4 次 hit 后触发穿星真伤
    st = b._player_stats(p)
    logs_all = []
    for i in range(4):
        b._do_hit_weapon_effects(p, st, logs_all) if hasattr(b, "_do_hit_weapon_effects") else None
    # 直接走 weapon proc hit 分发
    from data.plugins.dragonfall.game.core.weapon_effects import proc as we_proc
    hp_before = e["hp"]
    for i in range(4):
        we_proc(b, p, "hit", {"dmg": 500}, [])
    check("穿星 4 次攻击触发（真伤 >0）", e["hp"] < hp_before, f"dmg={hp_before - e['hp']}")

    # 5. 无 we_data 旧装备（手工塞 key）→ effect_data 回退参数表权威默认（v180E 阶段4）
    p2 = {
        "class_name": "战士", "level": 85, "hp": 9999, "max_hp": 9999,
        "equipment": {"weapon": {"name": "旧特效", "weapon_effect": "wind_split",
                                  "slot": "weapon", "quality": "purple"}},
        "buffs": {}, "attributes": {"str": 90}, "learned_skills": [], "race": "human",
    }
    wd = effect_data(None, p2, "wind_split")
    check("无 we_data 旧装备 → effect_data 回退参数表默认", abs(float(wd.get("chance", 0)) - 0.25) < 1e-9,
          f"wd={wd} (应含 chance=0.25 表默认)")
    check("旧装备 has_effect 仍 True（key 在就识别）", has_effect(None, p2, "wind_split"))

    print(f"\n===== 结果: {passed} 通过, {failed} 失败 =====")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
