# -*- coding: utf-8 -*-
"""commands 层：组队副本（v49）

验证：
  1. 副本列表 / 未组队开本拦截 / 非队长开本拦截
  2. 队长开本：状态结构、Boss 血量倍率、队员自动参战
  3. 轮流回合：未轮到的人不能行动
  4. 超时自动防御（惰性检测：改 turn_time 模拟超时）
  5. 通关结算：奖励/材料/图纸/首通成就/战斗清除
  6. 全灭失败：回城 HP 0、战斗清除
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, FakeEvent, run

passed = failed = 0
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


async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "i1", "注册 战士 队长")
    await cmd(m, "register", "g1", "i2", "注册 法师 队员")
    db.update_player("g1", "i1", level=40, gold=10000, cur_map="dawn_city")
    db.update_player("g1", "i2", level=40, gold=10000, cur_map="dawn_city")

    print("【副本：列表】")
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本")
    check("显示副本列表", "旧王陵" in out, out[:200])

    print("【副本：未组队开本】")
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    check("提示先组队", "组队" in out, out[:120])

    print("【副本：组队后开本】")
    await cmd(m, "party", "g1", "i1", "组队 队员")
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    check("开本成功", "副本开启" in out, out[:200])
    check("显示行动顺序", "按速度" in out or "行动顺序" in out, out[:200])
    battle = db.get_battle("g1", "i1")
    check("状态存队长名下", battle and battle["state"]["type"] == "instance")
    st = battle["state"]
    check("成员 2 人", len(st["members"]) == 2, str(st["members"]))
    # v57：行动序按速度降序（快者 index 0）
    spd0 = st["players"][st["members"][0]].get("spd", 0)
    spd1 = st["players"][st["members"][1]].get("spd", 0)
    check("行动序按速度排序", spd0 >= spd1, f"{st['members']} spd={spd0},{spd1}")
    boss = st["boss"]
    check("Boss 血量 > 单人模板", boss["max_hp"] > 1500, f"hp={boss['max_hp']}")
    check("Boss 是首领标记", boss.get("is_boss") is True)

    print("【副本：轮流回合】")
    first_m = st["members"][0]
    second_m = st["members"][1]
    out = await cmd(m, "attack", "g1", second_m, "攻击")
    check("非当前行动者被拦", "等待" in out or "回合" in out, out[:120])
    out = await cmd(m, "attack", "g1", first_m, "攻击")
    check("当前行动者有返回", "古王·奥德里克" in out or "轮到" in out, out[:200])
    st2 = db.get_battle("g1", "i1")["state"]
    check("轮到下一位", st2["turn"] == 1, f"turn={st2['turn']}")

    print("【副本：超时自动防御】")
    st3 = db.get_battle("g1", "i1")["state"]
    # v57：Boss 速度可能触发多动秒人，调低攻击专注测轮转逻辑
    st3["boss"]["atk"] = 5
    st3["boss"]["matk"] = 5
    st3["turn"] = 0  # 把回合拨回首位
    st3["turn_time"] = int(time.time()) - 200  # 模拟首位超时 200s
    db.save_battle("g1", "i1", st3)
    out = await cmd(m, "attack", "g1", second_m, "攻击")
    check("超时自动防御并行动", "自动" in out, out[:200])

    print("【副本：通关结算】")
    st4 = db.get_battle("g1", "i1")["state"]
    st4["boss"]["hp"] = 1
    st4["turn_time"] = int(time.time())
    db.save_battle("g1", "i1", st4)
    cur = st4["members"][st4["turn"]]
    out = await cmd(m, "attack", "g1", cur, "攻击")
    check("通关结算", "通关" in out or "击败" in out, out[:300])
    check("金币奖励", "+200" in out or "金币" in out, out[:300])
    check("材料奖励", "古王剑" in out, out[:300])
    battle = db.get_battle("g1", "i1")
    check("战斗已清除", battle is None, "")
    achs = db.get_achievements("g1", "i1") or []
    found = any(a.get("ach_key") == "inst_clear_inst_old_king_tomb" and a.get("progress", 0) >= 1 for a in achs)
    check("首通成就", found, str(achs)[:200])

    print("【副本：3 人队】")
    await cmd(m, "register", "g1", "i3", "注册 游侠 第三人")
    db.update_player("g1", "i3", level=40, gold=10000, cur_map="dawn_city")
    out = await cmd(m, "party", "g1", "i1", "组队 第三人")
    check("队长拉第三人", "加入" in out and "3" in out, out[:150])
    members3 = db.party_members("g1", "i1")
    check("队伍 3 人", len(members3) == 3, str(members3))
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    check("3 人开本成功", "副本开启" in out, out[:150])
    st6 = db.get_battle("g1", "i1")["state"]
    check("3 人状态成员", len(st6["members"]) == 3, str(st6["members"]))
    boss6 = st6["boss"]
    # 2 人队基准 hp_mult=2.5 → 3 人 = 3.15
    base = C.build_monster(C.INSTANCES["inst_old_king_tomb"]["boss"], {"id": "x", "name": "x", "area": "x"})["max_hp"]
    expect = int(base * (2.5 + 0.65))
    check("Boss 血量 3.15 倍", abs(boss6["max_hp"] - expect) <= 1, f"{boss6['max_hp']} vs {expect}")
    # 调低 Boss 攻击，专注测轮转逻辑（避免随机秒杀脆皮导致 turn 跳变）
    st6["boss"]["atk"] = 5
    st6["boss"]["matk"] = 5
    db.save_battle("g1", "i1", st6)
    # v57：行动序按速度排序（快者 index 0）。i1/i2/i3 中速度最高者先动
    order3 = st6["members"]
    out = await cmd(m, "attack", "g1", order3[0], "攻击")
    st7 = db.get_battle("g1", "i1")["state"]
    check("轮到第二人", st7["turn"] == 1, f"turn={st7['turn']}")
    out = await cmd(m, "attack", "g1", order3[1], "攻击")
    st8 = db.get_battle("g1", "i1")["state"]
    check("轮到第三人", st8["turn"] == 2, f"turn={st8['turn']}")
    out = await cmd(m, "attack", "g1", order3[2], "攻击")
    st9 = db.get_battle("g1", "i1")["state"]
    check("三人后转回首人", st9["turn"] == 0, f"turn={st9['turn']}")
    # 清理 3 人测试战斗，避免影响后续用例
    for q in ("i1", "i2", "i3"):
        m._unlock_battle("g1", q)
        db.clear_battle("g1", q)

    print("【副本：团队技能广播（v50）】")
    # 三人队：战士(队长) 牧师 拳师，30 级学会团队技能
    # 上一用例残留队伍 → 先全员退队
    await cmd(m, "party_leave", "g1", "i1", "退队")
    await cmd(m, "party_leave", "g1", "i2", "退队")
    await cmd(m, "party_leave", "g1", "i3", "退队")
    db.update_player("g1", "i1", level=40, gold=10000, cur_map="dawn_city")
    db.update_player("g1", "i2", level=40, gold=10000, cur_map="dawn_city")
    db.update_player("g1", "i3", level=40, gold=10000, cur_map="dawn_city")
    # 注入学会的团队技能（learned_skills 存中文名，update_player 内部转 ID 存档）
    db.update_player("g1", "i1", learned_skills=["战吼", "铁壁"], skill_points=50)
    db.update_player("g1", "i2", learned_skills=["元素流转", "奥术强化"], skill_points=50)
    # v52 Build：技能必须装进技能栏才能战斗施放
    db.set_skill_bar("i1", ["战吼", "铁壁", None, None, None, None])
    db.set_skill_bar("i2", ["元素流转", "奥术强化", None, None, None, None])
    out = await cmd(m, "party", "g1", "i1", "组队 队员")
    check("队伍已建", "组队成功" in out, out[:100])
    out = await cmd(m, "party", "g1", "i1", "组队 第三人")
    check("第三人入队", "加入了你的队伍" in out, out[:100])
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    check("团队技能本开本", "副本开启" in out, out[:120])
    stt = db.get_battle("g1", "i1")["state"]
    # 全员低血量，便于验证团队治疗
    for key in stt["players"]:
        stt["players"][key]["hp"] = 50
        stt["players"][key]["max_hp"] = 500
    stt["boss"]["atk"] = 1
    stt["boss"]["matk"] = 1
    # v57：行动序按速度排序，分别把回合拨到施放者
    stt["turn"] = stt["members"].index("i1")
    stt["turn_time"] = int(time.time())
    db.save_battle("g1", "i1", stt)
    # 队长（战士）施放团队增益【战吼】(atk_all → 全队 atk_up)
    out = await cmd(m, "skill", "g1", "i1", "技能 战吼")
    stt2 = db.get_battle("g1", "i1")["state"]
    check("战吼广播全队 buff", all(stt2["p_buffs"].get(k, {}).get("atk_up", 0) > 0 for k in stt2["players"]),
          str(stt2["p_buffs"]))
    # 法师（队员2）施放团队增益【元素流转】(matk_all → 全队 matk_up)
    stt2["turn"] = stt2["members"].index("i2")
    stt2["turn_time"] = int(time.time())
    db.save_battle("g1", "i1", stt2)
    out = await cmd(m, "skill", "g1", "i2", "技能 元素流转")
    stt3 = db.get_battle("g1", "i1")["state"]
    check("元素流转广播全队", all(stt3["p_buffs"].get(k, {}).get("matk_up_strong", 0) > 0 or stt3["p_buffs"].get(k, {}).get("matk_up", 0) > 0 for k in stt3["players"]),
          str({k: stt3["p_buffs"].get(k, {}) for k in stt3["players"]}))
    # 清理
    for q in ("i1", "i2", "i3"):
        m._unlock_battle("g1", q)
        db.clear_battle("g1", q)

    print("【副本：全灭失败】")
    await cmd(m, "party", "g1", "i1", "组队 队员")
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    check("再次开本", "副本开启" in out, out[:120])
    st5 = db.get_battle("g1", "i1")["state"]
    for key in st5["players"]:
        st5["players"][key]["hp"] = 1
    st5["boss"]["atk"] = 99999   # Boss 秒杀，保证每轮杀一人
    st5["boss"]["matk"] = 99999
    st5["turn_time"] = int(time.time())
    db.save_battle("g1", "i1", st5)
    # 轮流攻击直到战斗结束（Boss 一轮杀一人，3 人队最多 3 轮全灭）
    last = ""
    for _ in range(15):
        battle = db.get_battle("g1", "i1")
        if battle is None:
            break
        st = battle["state"]
        # 找到当前行动者（跳过已阵亡者）
        idx = st["turn"]
        for _j in range(len(st["members"])):
            if st["alive"].get(str(st["members"][idx]), True):
                break
            idx = (idx + 1) % len(st["members"])
        cur = st["members"][idx]
        last = await cmd(m, "attack", "g1", cur, "攻击")
    battle = db.get_battle("g1", "i1")
    check("失败后战斗清除", battle is None, last[:200])
    check("失败提示", "失败" in last or "全灭" in last, last[:200])
    p1 = db.get_player("g1", "i1")
    check("队长 HP 0 回城", p1["hp"] == 0, f"hp={p1['hp']}")

    print("【副本：人数配置（v53）】")
    # 清理全灭残留队伍
    await cmd(m, "party_leave", "g1", "i1", "退队")
    await cmd(m, "party_leave", "g1", "i2", "退队")
    await cmd(m, "party_leave", "g1", "i3", "退队")
    db.update_player("g1", "i1", level=70, gold=10000, cur_map="dawn_city", hp=500)
    # 列表显示人数要求
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本")
    check("列表显示单人标记", "单人" in out, out[:300])
    check("列表显示 2-3 人", "2-3人" in out, out[:300])
    check("列表显示 4 人", "4人" in out, out[:300])
    # 单人副本：无需组队直接开本
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 哥布林营地")
    check("单人副本免组队开本", "副本开启" in out, out[:200])
    battle = db.get_battle("g1", "i1")
    stg = battle["state"]
    check("单人副本成员 1 人", len(stg["members"]) == 1, str(stg["members"]))
    base_g = C.build_monster(C.INSTANCES["inst_goblin_camp"]["boss"], {"id": "x", "name": "x", "area": "x"})["max_hp"]
    expect_g = int(base_g * 1.6)  # min_players=1 → hp_mult 不缩放
    check("单人 Boss 血量 = 1.6 倍", abs(stg["boss"]["max_hp"] - expect_g) <= 1, f"{stg['boss']['max_hp']} vs {expect_g}")
    check("单人无队伍构成警告", "没有坦克" not in out, out[:200])
    # 单人副本直接通关
    stg["boss"]["hp"] = 1
    stg["turn_time"] = int(time.time())
    db.save_battle("g1", "i1", stg)
    out = await cmd(m, "attack", "g1", "i1", "攻击")
    check("单人副本通关", "通关" in out or "击败" in out, out[:300])
    check("单人掉落咕噜的皇冠", "咕噜的皇冠" in out, out[:300])
    battle = db.get_battle("g1", "i1")
    check("单人副本战斗清除", battle is None, "")
    # 4 人副本：3 人队伍被拦截
    await cmd(m, "register", "g1", "i4", "注册 牧师 第四人")
    # 全队提到 70 级（深海龙宫 Lv.70+）
    for q in ("i2", "i3", "i4"):
        db.update_player("g1", q, level=70, gold=10000, cur_map="dawn_city")
    await cmd(m, "party", "g1", "i1", "组队 队员")
    await cmd(m, "party", "g1", "i1", "组队 第三人")
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 深海龙宫")
    check("4 人副本 3 人拦截", "至少需要 4 人" in out, out[:200])
    # 拉第四人 → 4 人队伍开本成功
    out = await cmd(m, "party", "g1", "i1", "组队 第四人")
    check("队长拉第四人", "加入了你的队伍" in out and "4" in out, out[:200])
    members4 = db.party_members("g1", "i1")
    check("队伍 4 人", len(members4) == 4, str(members4))
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 深海龙宫")
    check("4 人副本开本成功", "副本开启" in out, out[:200])
    stm = db.get_battle("g1", "i1")["state"]
    check("4 人副本成员 4 人", len(stm["members"]) == 4, str(stm["members"]))
    base_m = C.build_monster(C.INSTANCES["inst_deep_dragon_palace"]["boss"], {"id": "x", "name": "x", "area": "x"})["max_hp"]
    expect_m = int(base_m * 2.7)  # min_players=4 → 4 人不缩放
    check("4 人 Boss 血量 = 2.5 倍", abs(stm["boss"]["max_hp"] - expect_m) <= 1, f"{stm['boss']['max_hp']} vs {expect_m}")
    # 清理深海龙宫战斗（否则 instance_cmd 直接显示状态，走不到人数校验）
    for q in ("i1", "i2", "i3", "i4"):
        m._unlock_battle("g1", q)
        db.clear_battle("g1", q)
    # 2 人副本超限提示（队伍 4 人打旧王陵）
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    check("旧王陵 4 人超限", "最多 3 人" in out, out[:200])
    for q in ("i1", "i2", "i3", "i4"):
        m._unlock_battle("g1", q)
        db.clear_battle("g1", q)

    print(f"\n结果: {passed} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
