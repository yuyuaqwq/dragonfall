#!/usr/bin/env python3
"""v180E 阶段4 武器特效端到端门禁（99 件特效装备全链路）。

验证：
1. roster 全部带 weapon_effect 的装备 → generate_roster_equip 实例带 key（断链回归）
2. 走 weapon_effect 通道的 key → WEAPON_EFFECT_DATA 参数表有默认（数值下沉回归）
   （例外：divine_execution/dragon_annihilation/star_destruction 是 affix 词条通道，不要求）
3. 代表性事件触发（battle_start/hit/taken/heal 四类抽样）真实生效
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
    from data.plugins.dragonfall.game.data.weapon_effect_data import WEAPON_EFFECT_DATA

    print("===== v180E 武器特效端到端（99 件） =====\n")

    we_roster = {rid: r for rid, r in EQUIP_ROSTER.items() if r.get("weapon_effect")}
    check("roster 特效装备 >= 90 件", len(we_roster) >= 90, f"n={len(we_roster)}")

    # 1. 实例化带 key
    bad = []
    random.seed(9)
    for rid, r in we_roster.items():
        eq = drops.generate_roster_equip(rid)
        if eq.get("weapon_effect") != r.get("weapon_effect"):
            bad.append(f"{rid}: 实例key丢失")
    check("全部实例化带 weapon_effect key", not bad, str(bad[:5]))

    # 2. 参数表覆盖（affix 通道 3 key 豁免）
    AFFIX_CHANNEL_KEYS = {"divine_execution", "dragon_annihilation", "star_destruction"}
    no_param = []
    for rid, r in we_roster.items():
        key = r.get("weapon_effect")
        if key in AFFIX_CHANNEL_KEYS:
            continue
        if key not in WEAPON_EFFECT_DATA:
            no_param.append(f"{rid}:{key}")
    check("weapon_effect 通道 key 全有参数表默认", not no_param, str(no_param[:5]))

    # 3. 四类事件抽样触发（复用 chain 测试的触发路径）
    from data.plugins.dragonfall.game import battle as BT
    from data.plugins.dragonfall.game.core.weapon_effects import proc as we_proc

    def mk_player(eq_items):
        eq = {}
        for i, item in enumerate(eq_items):
            eq[f"slot{i}"] = item
        return {"class_name": "战士", "level": 50, "hp": 5000, "max_hp": 5000,
                "mp": 200, "max_mp": 200, "atk": 500, "def": 100, "matk": 300, "mdef": 100,
                "equipment": eq, "buffs": {}, "stacks": {}, "eff": {},
                "attributes": {"str": 50}, "learned_skills": [], "race": "human"}

    def mk_enemy(hp=99999):
        return {"name": "测试怪", "hp": hp, "max_hp": hp, "atk": 100, "def": 50, "mdef": 50,
                "spd": 10, "lv": 50, "buffs": {}, "debuffs": {}}

    # battle_start 盾（哨兵短剑 starlight_bulwark）
    eq1 = drops.generate_roster_equip("eq_shao_bing_duan_jian")
    p1 = mk_player([eq1])
    b1 = BT.Battle("monster", mk_enemy(), {}, p1)
    logs1 = []
    random.seed(5)
    we_proc(b1, p1, "battle_start", {}, logs1)
    check("星辉壁垒开战触发", any("星辉壁垒" in l for l in logs1), str(logs1))
    check("星辉壁垒护盾生成", bool((p1.get("shields") or {}).get("we_starlight")), str(p1.get("shields")))

    # hit 穿星（星陨长弓 star_pierce 4连真伤）
    eq2 = drops.generate_roster_equip("eq_xing_yun_chang_gong")
    p2 = mk_player([eq2])
    e2 = mk_enemy()
    e2["hp"] = 5000
    b2 = BT.Battle("monster", e2, {}, p2)
    logs2 = []
    random.seed(6)
    hp0 = e2["hp"]
    for _ in range(4):
        we_proc(b2, p2, "hit", {"dmg": 400}, logs2)
    check("穿星 4 连触发真伤", e2["hp"] < hp0 and any("穿星" in l for l in logs2),
          f"dmg={hp0 - e2['hp']} logs={logs2[:2]}")

    # taken 反伤（荆棘战甲 thorn_armor）
    eq3 = drops.generate_roster_equip("eq_jing_ji_zhan_jia")
    p3 = mk_player([eq3])
    e3 = mk_enemy()
    b3 = BT.Battle("monster", e3, {}, p3)
    logs3 = []
    random.seed(7)
    we_proc(b3, p3, "taken", {"dmg": 300}, logs3)
    check("荆棘缠绕反伤触发", any("荆棘" in l for l in logs3), str(logs3))

    # heal 加成（铁卫之戒 vital_band +15%）
    eq4 = drops.generate_roster_equip("eq_tie_wei_zhi_jie")
    p4 = mk_player([eq4])
    b4 = BT.Battle("monster", mk_enemy(), {}, p4)
    ctx4 = {"heal": 100}
    we_proc(b4, p4, "heal", ctx4, [])
    check("坚毅祝福治疗 +15%", ctx4["heal"] == 114, f"heal={ctx4['heal']}")

    print(f"\n===== 结果: {passed} 通过, {failed} 失败 =====")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
