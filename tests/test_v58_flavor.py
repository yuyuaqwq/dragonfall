# -*- coding: utf-8 -*-
"""v58 特色化测试：怪物个体修正 / 装备前缀倾向 / Boss 专属机制"""
import sys, os, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, BT, db, clean_db, Main, FakeEvent, run

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

def mk_monster(mid, name, role, lv):
    return C.build_monster([mid, name, role, lv, [], []], {"id": mid, "name": name, "area": "x"})

async def main():
    clean_db()
    print("【怪物个体修正（v58）】")
    # 有 mods 的怪数值与公式不同（monster_stats 通过 C 模块访问）
    rat = mk_monster("m_giant_rat", "巨型老鼠", "speedster", 2)
    base_rat = C.monster_stats(2, "speedster")
    check("巨型老鼠 hp 修正(0.75x)", rat["hp"] == int(base_rat["hp"] * 0.75),
          f"{rat['hp']} vs {int(base_rat['hp']*0.75)}")
    check("巨型老鼠 spd 修正(1.35x)", rat["spd"] == int(base_rat["spd"] * 1.35),
          f"{rat['spd']} vs {int(base_rat['spd']*1.35)}")
    check("有 mod 描述", "快而脆" in rat.get("mod", ""), rat.get("mod", ""))
    # 无 mods 的怪保持公式值（m_corpse_crawler 未配置 mods）
    plain = mk_monster("m_corpse_crawler", "腐尸爬行者", "dps", 12)
    base_dog = C.monster_stats(12, "dps")
    check("无 mods 怪不受影响", plain["hp"] == base_dog["hp"], f"{plain['hp']} vs {base_dog['hp']}")
    # 精英 mods
    elite = mk_monster("e_bandit_leader", "山贼头目", "elite", 4)
    base_elite = C.monster_stats(4, "elite")
    check("山贼头目 hp 修正(1.3x)", elite["hp"] == int(base_elite["hp"] * 1.3),
          f"{elite['hp']} vs {int(base_elite['hp']*1.3)}")
    # 图鉴/怪猎信息带 mod
    check("怪物带 mod 字段", "mod" in elite, str(elite.keys()))

    print("【装备前缀倾向（v58）】")
    random.seed(123)
    # 固定前缀测试：直接验证 EQUIP_PREFIX_FLAVOR 表
    from game.data import EQUIP_PREFIX_FLAVOR
    check("前缀表非空", len(EQUIP_PREFIX_FLAVOR) > 10, str(len(EQUIP_PREFIX_FLAVOR)))
    # 寒霜 → matk+3 spd+1
    # 生成大量蓝装，统计名字与属性关联
    random.seed(7)
    flame_seen = frost_seen = False
    for _ in range(200):
        eq = C.generate_equip("weapon", 10, "blue", "sword")
        nm = eq["name"]
        st = eq["stats"]
        if nm.startswith("烈焰"):
            flame_seen = True
            check("烈焰武器 atk 偏高", st.get("atk", 0) >= 22, str(st))
            break
    if not flame_seen:
        check("烈焰武器出现", False, "200 次未出现")
    random.seed(8)
    for _ in range(200):
        eq = C.generate_equip("armor", 10, "blue")
        nm = eq["name"]
        if nm.startswith("秘银"):
            check("秘银防具 def 偏高", eq["stats"].get("def", 0) >= 15, str(eq["stats"]))
            break
    else:
        check("秘银防具出现", False, "200 次未出现")
    # 白装前缀也有倾向（陈旧 → hp-4）
    random.seed(9)
    for _ in range(200):
        eq = C.generate_equip("helm", 5, "white")
        if eq["name"].startswith("陈旧"):
            check("陈旧白装 hp 偏低", eq["stats"].get("hp", 99) < 20, str(eq["stats"]))
            break
    else:
        check("陈旧白装出现", False, "200 次未出现")

    print("【Boss 专属机制（v58）】")
    # enrage：血量 <30% 触发狂暴，攻击提升
    random.seed(11)
    p = {"qq_id": "t", "class_name": "cls_zhan_shi", "level": 10,
         "equipment": {}, "attributes": {"str": 0, "agi": 0, "int": 0, "vit": 0},
         "learned_skills": [], "skill_levels": {}, "class_tier": 0, "evolve_path": 0,
         "hp": 9999, "mp": 9999}
    boss = mk_monster("b_tunnel_king", "隧洞之王", "boss", 11)
    boss["mech"] = "enrage"
    boss["hp"] = int(boss["max_hp"] * 0.2)  # 20% 血
    b = BT.Battle("monster", boss)
    st = E.player_final_stats(p["class_name"], p["level"], p["equipment"], 0, p["attributes"])
    p["max_hp"] = st["max_hp"]; p["max_mp"] = st["max_mp"]; p["hp"] = st["max_hp"]; p["mp"] = st["max_mp"]
    logs, _ = b.player_turn("attack", None, p)
    check("enrage 触发狂暴日志", any("狂暴" in x for x in logs), "|".join(logs)[:200])
    check("enrage 标记", boss.get("enraged") is True, str(boss.get("enraged")))
    est = b._enemy_stats()
    check("狂暴后攻击提升", est["atk"] > boss["atk"], f"{est['atk']} vs {boss['atk']}")

    # summon：第 3 回合召唤援军
    random.seed(13)
    boss2 = mk_monster("b_decay_lord", "腐朽领主", "boss", 14)
    boss2["mech"] = "summon"
    boss2["hp"] = 99999; boss2["max_hp"] = 99999; boss2["atk"] = 1
    b2 = BT.Battle("monster", boss2)
    p2 = dict(p)
    b2.player_turn("attack", None, p2)  # 回合 1
    b2.player_turn("attack", None, p2)  # 回合 2
    logs3, _ = b2.player_turn("attack", None, p2)  # 回合 3 → 召唤
    check("summon 第3回合召唤", any("召唤" in x for x in logs3), "|".join(logs3)[:200])

    # heal：第 4 回合自愈
    random.seed(17)
    boss3 = mk_monster("b_ancient_elk", "远古圣鹿", "boss", 8)
    boss3["mech"] = "heal"
    boss3["max_hp"] = 1000
    b3 = BT.Battle("monster", boss3)
    p3 = dict(p)
    for _ in range(3):
        b3.player_turn("attack", None, p3)
    hp_before = boss3["hp"]
    logs4, _ = b3.player_turn("attack", None, p3)  # 回合 4 → 自愈
    check("heal 第4回合自愈", boss3["hp"] > hp_before or any("恢复" in x for x in logs4),
          f"{hp_before}→{boss3['hp']} logs={'|'.join(logs4)[:200]}")

    print("【实例 Boss mech 透传】")
    m = Main(None)
    async def cmd(m, handler_name, gid, qid, msg):
        ev = FakeEvent(gid, qid, msg)
        results = await run(getattr(m, handler_name), ev)
        return results[-1] if results else ""
    await cmd(m, "register", "g1", "i1", "注册 战士 队长")
    await cmd(m, "register", "g1", "i2", "注册 法师 队员")
    db.update_player("g1", "i1", level=40, gold=10000, cur_map="dawn_city")
    db.update_player("g1", "i2", level=40, gold=10000, cur_map="dawn_city")
    await cmd(m, "party", "g1", "i1", "组队 队员")
    await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    st = db.get_battle("g1", "i1")["state"]
    check("古王·奥德里克 mech=enrage,summon", st["boss"].get("mech") == "enrage,summon", str(st["boss"].get("mech")))
    for q in ("i1", "i2"):
        m._unlock_battle("g1", q)
        db.clear_battle("g1", q)

    print(f"\n结果: {passed} passed, {failed} failed")
    return failed

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
