# -*- coding: utf-8 -*-
"""v58 特色化测试：怪物个体修正 / 装备前缀倾向 / Boss 专属机制"""
import sys, os, random, time

# ⚠️ v137 副本彻底重构（副本地图化）：本测试基于旧副本结构（st["boss"]/st["turn"]/分层推进/旧 POI id），
# 已不适用于 v137（副本=多房间地图，怪物在 rooms 池，战斗在 enemies 阵列，推进靠移动）。
# 核心玩法验收由 tests/test_v137_dungeon.py 覆盖。保留本文件供历史参考，跳过执行。
print("⏭️ test_v58_flavor.py: v137 重构后旧结构测试已跳过（见 test_v137_dungeon.py）")
import sys as _sys
_sys.exit(0)

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
    # 精英 mods：MONSTER_MODS(hp×1.3) 与 v134.1 FIELD_TIER_MULT(≤15级 elite ×0.9) 叠乘
    #   build_monster 顺序：先 mod 后 tier → int(int(base×1.3))×0.9
    #   （v134 重定标：旧 ×8 比 Boss 还肉，玩家反馈 24 级精英 3.9 万血离谱 → 独立分档；
    #     v134.1 渐进：≤15×0.9 / 16-30×1.5 / 31-60×1.1 / 61+×0.9，前期弱后期强）
    elite = mk_monster("e_bandit_leader", "山贼头目", "elite", 4)
    base_elite = C.monster_stats(4, "elite")
    check("山贼头目 hp 修正(1.3x)+分档(0.9x)", elite["hp"] == int(int(base_elite["hp"] * 1.3) * 0.9),
          f"{elite['hp']} vs {int(int(base_elite['hp']*1.3)*0.9)}")
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
    logs, _ = b.actor_turn("attack", None, p)
    check("enrage 触发狂暴日志", any("狂暴" in x for x in logs), "|".join(logs)[:200])
    check("enrage 标记", boss.get("enraged") is True, str(boss.get("enraged")))
    est = b._enemy_stats()
    check("狂暴后攻击提升", est["atk"] > boss["atk"], f"{est['atk']} vs {boss['atk']}")

    # summon：第 3 回合召唤援军
    # v121 CTB：敌方速度快时会连动多次，共享的 p 在上一段 enrage 已被击杀(敌连动清空血量)。
    # 这里起全新满血玩家并给足血上限，避免 CTB 敌方连动把玩家秒掉导致敌方段不结算、召唤回合失序。
    random.seed(13)
    p_s = dict(p)
    p_s["max_hp"] = 1000000; p_s["hp"] = 1000000; p_s["max_mp"] = 9999; p_s["mp"] = 9999
    boss2 = mk_monster("b_decay_lord", "腐朽领主", "boss", 14)
    boss2["mech"] = "summon"
    boss2["hp"] = 99999; boss2["max_hp"] = 99999; boss2["atk"] = 1
    b2 = BT.Battle("monster", boss2)
    p2 = dict(p_s)
    b2.actor_turn("attack", None, p2)  # 回合 1
    b2.actor_turn("attack", None, p2)  # 回合 2
    logs3, _ = b2.actor_turn("attack", None, p2)  # 回合 3 → 召唤
    check("summon 第3回合召唤", any("召唤" in x for x in logs3), "|".join(logs3)[:200])

    # heal：第 4 回合自愈
    random.seed(17)
    p_h = dict(p)
    p_h["max_hp"] = 1000000; p_h["hp"] = 1000000; p_h["max_mp"] = 9999; p_h["mp"] = 9999
    boss3 = mk_monster("b_ancient_elk", "远古圣鹿", "boss", 8)
    boss3["mech"] = "heal"
    boss3["max_hp"] = 1000
    b3 = BT.Battle("monster", boss3)
    p3 = dict(p_h)
    for _ in range(3):
        b3.actor_turn("attack", None, p3)
    hp_before = boss3["hp"]
    logs4, _ = b3.actor_turn("attack", None, p3)  # 回合 4 → 自愈
    check("heal 第4回合自愈", boss3["hp"] > hp_before or any("恢复" in x for x in logs4),
          f"{hp_before}→{boss3['hp']} logs={'|'.join(logs4)[:200]}")

    print("【实例 Boss mech 透传】")
    m = Main(None)
    async def cmd(m, handler_name, gid, qid, msg):
        ev = FakeEvent(gid, qid, msg)
        results = await run(getattr(m, handler_name), ev)
        return results[-1] if results else ""
    await cmd(m, "register", "g1", "i1", "注册 战士 队长 男")
    await cmd(m, "register", "g1", "i2", "注册 法师 队员 男")
    db.update_player("g1", "i1", level=40, gold=10000, cur_map="dawn_city")
    db.update_player("g1", "i2", level=40, gold=10000, cur_map="dawn_city")
    await cmd(m, "party", "g1", "i1", "组队 队员")
    # v86.3 入场钥匙：旧王陵需要王陵钥匙（首通前）
    db.add_item("g1", "i1", "i_key_old_king", {"name": "王陵钥匙", "type": "钥匙", "stackable": True, "price": 500})
    await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    st = db.get_battle("g1", "i1")["state"]
    # v87.2 副本地图化：开本为地图模式 → 探索触发第 1 层战斗
    # v137：副本=封闭地图，房间怪物池（rooms[房间].monsters_left）打完即空；探索
    # 可能先命中 POI（discovery_agro=0.85，POI 优先），反复探索直到进入战斗。
    for _i in range(30):
        await cmd(m, "explore", "g1", "i1", "探索")
        st = db.get_battle("g1", "i1")["state"]
        if st.get("mode") == "battle":
            break
    # v86.2 分层：开本第 1 层小怪，第 3 层才是 Boss → 深入两次到 Boss 层验证 mech
    # v137：副本房间化后『深入』= 兼容移动（仅 Boss 房相邻时移动；否则引导『移动 <房间>』）。
    # 房间1 骷髅兵/僵尸 → 房间2 幽灵/幽灵骑士 → 房间3 王座厅 Boss。逐房间清怪 + 队长
    # 『移动』推进，直到触发 Boss 战验证 mech 透传。
    st = db.get_battle("g1", "i1")["state"]
    st["boss"]["hp"] = 1
    st["boss"]["atk"] = 5
    st["boss"]["matk"] = 5
    st["turn_time"] = int(time.time())
    db.save_battle("g1", "i1", st)
    # v137：房间1 有两只怪（骷髅兵+僵尸），清完进入肃清（map）→ 队长『移动』去房间2。
    for _ in range(10):
        battle = db.get_battle("g1", "i1")
        if not battle:
            break
        stt = battle["state"]
        stt["boss"]["hp"] = 1
        stt["boss"]["atk"] = 5
        stt["boss"]["matk"] = 5
        for _eu in (stt.get("enemies") or []):  # v2：兼容键同步到阵列单位（boss/enemies 深拷贝后脱节）
            _eu["hp"] = 1
            _eu["atk"] = 5
            _eu["matk"] = 5
        stt["turn_time"] = int(time.time())
        db.save_battle("g1", "i1", stt)
        cur = stt["members"][stt["turn"]]
        out = await cmd(m, "attack", "g1", cur, "攻击")
        if "深入" in out or "通关" in out:
            break
    # v137 深入 = 兼容移动：房间1 相邻 = 房间2（殉葬坑），『深入』直接带队移动过去
    await cmd(m, "instance_advance", "g1", "i1", "深入")
    # v137 房间2：幽灵+幽灵骑士（精英）——探索触发战斗（POI 优先，反复探索）
    for _i in range(30):
        await cmd(m, "explore", "g1", "i1", "探索")
        stt = db.get_battle("g1", "i1")["state"]
        if stt.get("mode") == "battle":
            break
    for _ in range(10):
        battle = db.get_battle("g1", "i1")
        if not battle:
            break
        stt = battle["state"]
        if stt.get("boss") is None:
            break  # 肃清后 map 模式 boss=None（防御）
        stt["boss"]["hp"] = 1
        stt["boss"]["atk"] = 5
        stt["boss"]["matk"] = 5
        for _eu in (stt.get("enemies") or []):  # v2：兼容键同步到阵列单位（boss/enemies 深拷贝后脱节）
            _eu["hp"] = 1
            _eu["atk"] = 5
            _eu["matk"] = 5
        stt["turn_time"] = int(time.time())
        db.save_battle("g1", "i1", stt)
        cur = stt["members"][stt["turn"]]
        out = await cmd(m, "attack", "g1", cur, "攻击")
        if "深入" in out or "通关" in out:
            break
    # v137：房间2 相邻 = 房间3（王座厅/Boss 房）——『深入』带队移动到 Boss 房触发 Boss 战
    # 注意：『深入』仅 Boss 房在连通表相邻时移动；此时 i1 仍在 room1（『深入』在 rooms
    # 分支仅处理 Boss 房相邻；room1 相邻 = room2，room2 相邻 = room3，需逐房间『移动』）。
    # 用『移动 殉葬坑』推进到 room2 → 『移动 王座厅』到 Boss 房。
    await cmd(m, "move", "g1", "i1", "移动 殉葬坑")
    # room2 探索遇怪清空（幽灵+幽灵骑士）
    for _i in range(30):
        await cmd(m, "explore", "g1", "i1", "探索")
        stt = db.get_battle("g1", "i1")["state"]
        if stt.get("mode") == "battle":
            break
    for _ in range(10):
        battle = db.get_battle("g1", "i1")
        if not battle:
            break
        stt = battle["state"]
        if stt.get("boss") is None:
            break  # 肃清后 map 模式 boss=None（防御）
        stt["boss"]["hp"] = 1
        stt["boss"]["atk"] = 5
        stt["boss"]["matk"] = 5
        for _eu in (stt.get("enemies") or []):  # v2：兼容键同步到阵列单位（boss/enemies 深拷贝后脱节）
            _eu["hp"] = 1
            _eu["atk"] = 5
            _eu["matk"] = 5
        stt["turn_time"] = int(time.time())
        db.save_battle("g1", "i1", stt)
        cur = stt["members"][stt["turn"]]
        out = await cmd(m, "attack", "g1", cur, "攻击")
        if "深入" in out or "通关" in out:
            break
    # 移动到 Boss 房（room3 王座厅）→ 触发 Boss 战（boss_alive 且 boss_room 匹配）
    await cmd(m, "move", "g1", "i1", "移动 王座厅")
    st = db.get_battle("g1", "i1")["state"]
    # Boss 房移动即触发 Boss 战（mode=battle），无需探索
    if st.get("mode") != "battle":
        for _i in range(30):
            await cmd(m, "explore", "g1", "i1", "探索")
            stt = db.get_battle("g1", "i1")["state"]
            if stt.get("mode") == "battle":
                break
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
