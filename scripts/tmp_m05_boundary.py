# -*- coding: utf-8 -*-
"""M05 副本系统边界实测（只读验证，测试库）"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)).replace("scripts", "tests"))
from conftest import C, db, clean_db, Main, FakeEvent, run

passed = 0
failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

def mk_snap(hp=500, maxhp=500, spd=10):
    return {"name": "格温", "qq_id": "i1", "class_name": "战士", "level": 25,
            "hp": hp, "max_hp": maxhp, "mp": 100, "max_mp": 100,
            "atk": 50, "def": 30, "matk": 10, "mdef": 20, "spd": spd,
            "equipment": {}, "skills": [], "learned_skills": [], "class_tier": 0,
            "evolve_path": 0, "attributes": None, "title_bonus": {}, "race": None}

def mk_boss(atk=100, maxhp=2000, mech=""):
    b = {"id": "b_test", "name": "测试Boss", "lv": 25, "role": "boss",
         "hp": maxhp, "max_hp": maxhp, "atk": atk, "def": 20, "matk": atk,
         "mdef": 20, "spd": 10, "exp": 100, "gold": 100, "skills": [],
         "drops": [], "map": "x", "map_area": "x", "is_boss": True,
         "is_elite": False, "mech": mech, "mod": ""}
    return b

async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "i1", "注册 战士 格温 男")
    db.update_player("g1", "i1", level=25, gold=10000)

    print("【边界 1：低等级开高等级副本（拦截）】")
    db.update_player("g1", "i1", level=10)
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 海蚀洞窟")
    check("Lv.10 开 Lv.22 副本被拦截", "等级" in out or "需要" in out, out[:150])
    db.update_player("g1", "i1", level=25)

    print("【边界 2：1 人开 4 人本（拦截/提示）】")
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 深渊裂隙")
    check("无队开 4 人本提示组队", "组队" in out, out[:150])

    print("【边界 3：0 血进本（拦截）】")
    db.update_player("g1", "i1", hp=0)
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 鹿角要塞")
    check("0 血进本拦截", "生命值为 0" in out, out[:150])
    db.update_player("g1", "i1", hp=500)

    print("【边界 4：单人副本开本（哥布林营地弹性）】")
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 哥布林营地")
    check("单人开哥布林营地成功", "副本开启" in out or "营地" in out, out[:150])
    b = db.get_battle("g1", "i1")
    check("开本状态已建", b is not None, "")
    if b:
        for mm in b["state"]["members"]:
            m._unlock_battle("g1", mm)
        db.clear_battle("g1", mm)

    print("【边界 5：护盾在副本 Boss 回合是否生效】")
    # 构造旧王陵战斗状态（单人），成员带 500 盾，Boss atk=200
    inst = C.INSTANCES["inst_old_king_tomb"]
    boss = mk_boss(atk=200, maxhp=2000)
    st = m._instance_build_state("inst_old_king_tomb", inst, ["i1"], boss, int(time.time()), "i1")
    st["players"]["i1"] = mk_snap(hp=500, maxhp=500)
    st["members"] = ["i1"]
    st["acted"] = [False]
    st["turn"] = 0
    st["mode"] = "battle"
    st["turn_time"] = int(time.time())
    st["players"]["i1"]["p_shields"] = {"test_shield": {"value": 500, "turns": 3}}
    st["threat"] = {"i1": 100}
    st["boss"] = boss
    st["enemy"] = boss
    st["mode"] = "battle"
    db.save_battle("g1", "i1", st)
    st = db.get_battle("g1", "i1")["state"]
    hp0 = st["players"]["i1"]["hp"]
    logs = m._instance_boss_one_turn(st, "g1")
    hp1 = st["players"]["i1"]["hp"]
    check(f"护盾吸收 Boss 伤害（盾500 vs 伤{hp0-hp1}，期望扣0）", hp1 == hp0, f"hp {hp0}->{hp1}, logs={logs[-2:]}")
    check("护盾未被消耗", (st["players"]["i1"].get("p_shields") or {}).get("test_shield", {}).get("value", -1) == 500,
          str(st["players"]["i1"].get("p_shields")))

    print("【边界 6：地图模式篝火回血后被进战斗回滚】")
    inst2 = C.INSTANCES["inst_goblin_camp"]
    boss2 = mk_boss(atk=10, maxhp=500)
    st2 = m._instance_build_state("inst_goblin_camp", inst2, ["i1"], boss2, int(time.time()), "i1")
    st2["players"]["i1"] = mk_snap(hp=500, maxhp=1000)
    st2["members"] = ["i1"]
    st2["acted"] = [False]
    st2["turn"] = 0
    st2["mode"] = "map"
    st2["stage_idx"] = 0
    st2["stage_cleared"] = True      # 首层已肃清（可调查）
    st2["stage_pending"] = []        # 无残留怪
    db.save_battle("g1", "i1", st2)
    out = await cmd(m, "instance_investigate", "g1", "i1", "调查 将熄的篝火")
    st2 = db.get_battle("g1", "i1")["state"]
    hp_after_fire = st2["players"]["i1"]["hp"]
    check("篝火回血生效（快照 500->>500）", hp_after_fire > 500, f"hp={hp_after_fire}, out={out[:80]}")
    # 现在探索遇怪（pending 塞一只怪）→ _enter_stage_combat 用 DB 刷新快照
    st2["stage_pending"] = [["m_goblin_guard", "哥布林守卫", "tank", 15, ["ms_dun_ji"], ["哥布林铁片"]]]
    st2["stage_cleared"] = False
    db.save_battle("g1", "i1", st2)
    out = await cmd(m, "explore", "g1", "i1", "探索")
    st2 = db.get_battle("g1", "i1")["state"]
    hp_in_battle = st2["players"]["i1"]["hp"]
    db_hp = db.get_player("g1", "i1")["hp"]
    check(f"进战斗后快照保留篝火回血（期望 {hp_after_fire}，实际 {hp_in_battle}）",
          hp_in_battle >= hp_after_fire, f"DB hp={db_hp}")

    print("【边界 7：poi_read 机关断链（旧王陵王座机关）】")
    inst3 = C.INSTANCES["inst_old_king_tomb"]
    boss3 = mk_boss(atk=1, maxhp=100)
    st3 = m._instance_build_state("inst_old_king_tomb", inst3, ["i1"], boss3, int(time.time()), "i1")
    st3["players"]["i1"] = mk_snap(hp=100, maxhp=100)
    st3["members"] = ["i1"]
    st3["acted"] = [False]
    st3["turn"] = 0
    st3["mode"] = "map"
    st3["stage_idx"] = 1            # 主墓室（读碑文）
    st3["stage_cleared"] = True
    db.save_battle("g1", "i1", st3)
    out = await cmd(m, "instance_investigate", "g1", "i1", "调查 古王铭文")
    check("读到碑文", "古王铭文" in out or "机关被解锁" in out, out[:120])
    st3 = db.get_battle("g1", "i1")["state"]
    check("poi_unlocks 记录了 mechanism_king_throne", st3.get("poi_unlocks", {}).get("mechanism_king_throne") is True, str(st3.get("poi_unlocks")))
    # 去王座厅开机关
    st3["stage_idx"] = 2
    db.save_battle("g1", "i1", st3)
    out = await cmd(m, "instance_investigate", "g1", "i1", "调查 王座机关")
    check("读过碑文后王座机关可打开（期望成功）", "捷径" in out or "机关" in out and "纹丝不动" not in out, out[:150])

    print("【边界 8：全体阵亡 → 销毁+回城】")
    st4 = m._instance_build_state("inst_goblin_camp", inst2, ["i1"], mk_boss(atk=1, maxhp=100), int(time.time()), "i1")
    st4["players"]["i1"] = mk_snap(hp=1, maxhp=100)
    st4["members"] = ["i1"]
    st4["acted"] = [False]
    st4["turn"] = 0
    st4["mode"] = "battle"
    st4["turn_time"] = int(time.time())
    st4["boss"] = mk_boss(atk=1, maxhp=100)
    st4["enemy"] = st4["boss"]
    db.save_battle("g1", "i1", st4)
    st4 = db.get_battle("g1", "i1")["state"]
    st4["alive"]["i1"] = False
    st4["turn"] = 0
    db.save_battle("g1", "i1", st4)
    out = await cmd(m, "attack", "g1", "i1", "攻击")
    check("全灭失败文案", "副本失败" in out or "全灭" in out, out[:150])
    b8 = db.get_battle("g1", "i1")
    check("失败后战斗已销毁", b8 is None, str(b8)[:100])
    p8 = db.get_player("g1", "i1")
    check("失败后回城", p8["cur_map"] == C.START_MAP, p8["cur_map"])

    print("【边界 9：通关后停留再打（攻击引导）】")
    st5 = m._instance_build_state("inst_old_king_tomb", inst, mk_boss(atk=1, maxhp=100), int(time.time()), "i1")
    st5["players"]["i1"] = mk_snap(hp=100, maxhp=100)
    st5["members"] = ["i1"]
    st5["acted"] = [False]
    st5["turn"] = 0
    st5["mode"] = "map"
    st5["cleared"] = True
    st5["stage_idx"] = 2
    st5["stage_cleared"] = True
    db.save_battle("g1", "i1", st5)
    out = await cmd(m, "attack", "g1", "i1", "攻击")
    check("通关后攻击引导搜刮/离开", "已通关" in out or "离开副本" in out or "搜刮" in out, out[:150])

    print("【边界 10：通关后『传送』是否放行（静态验证）】")
    out = await cmd(m, "teleport", "g1", "i1", "传送")
    check("通关后传送不拦截（状态残留风险确认）", "传送" in out or "方碑" in out, out[:100])

    print(f"\n结果: {passed} 通过, {failed} 失败")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
