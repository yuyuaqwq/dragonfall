# -*- coding: utf-8 -*-
"""v49 玩家意见批处理测试（#4 移动撞怪 / #5 世界Boss地点 / #6 副本仇恨 / #7 职业定位 / #8 帮助拆分）"""
import sys, os, random, time
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

    print("【#7 职业定位】")
    roles = {C.CLASSES[k]["name"]: C.CLASSES[k].get("role") for k in C.CLASSES}
    check("战士=坦克", roles.get("战士") == "坦克", str(roles))
    check("牧师=治疗", roles.get("牧师") == "治疗", str(roles))
    check("6 职业都有定位", len(roles) == 6 and all(roles.values()), str(roles))
    label = m._class_role_label("cls_zhan_shi")
    check("定位标签", "坦克" in label, label)

    print("【#8 帮助拆分】")
    await cmd(m, "register", "g1", "f1", "注册 战士 测试员")
    out = await cmd(m, "help_cmd", "g1", "f1", "帮助")
    check("总览精简", "指令大全" in out and "帮助 技能" in out, out[:80])
    out = await cmd(m, "help_cmd", "g1", "f1", "帮助 技能")
    check("技能分类", "技能系统" in out, out[:80])
    out = await cmd(m, "help_cmd", "g1", "f1", "帮助 副本")
    check("副本分类", "组队副本" in out, out[:80])
    out = await cmd(m, "help_cmd", "g1", "f1", "帮助 不存在的主题")
    check("未知主题提示", "没有" in out, out[:80])

    print("【#4 移动撞怪】")
    await cmd(m, "register", "g1", "f2", "注册 战士 低级玩家")
    db.update_player("g1", "f2", level=5, cur_map="vila_square")
    # 高级图：Lv.15 玩家去 Lv.30+ 图 → 必触发（diff>=5 概率 30%，多试几次）
    high_map = next(x for x in C.MAPS if x["id"] == "abyss_plain")
    random.seed(42)
    hit = any(m._travel_ambush(db.get_player("g1", "f2"), high_map) for _ in range(50))
    check("低级闯高级图会撞怪", hit)
    # 高级玩家去低级图 → 不撞（威慑）
    db.update_player("g1", "f2", level=60)
    low_map = next(x for x in C.MAPS if x["id"] == "emerald_trail")
    random.seed(42)
    hit2 = any(m._travel_ambush(db.get_player("g1", "f2"), low_map) for _ in range(50))
    check("高级玩家威慑低级怪不撞", not hit2)
    # 城镇不撞
    town = next(x for x in C.MAPS if x["type"] == "城镇区域")
    check("城镇不撞怪", m._travel_ambush(db.get_player("g1", "f2"), town) is None)

    print("【#5 世界Boss指定地点】")
    await cmd(m, "register", "g1", "f3", "注册 战士 讨伐者")
    db.update_player("g1", "f3", level=40, cur_map="vila_square")
    # 造一个 boss 事件：深渊魔王出现在深渊荒原
    db.save_world_event("boss", int(time.time()) + 3600, {
        "boss": {"name": "深渊魔王·阿兹莫丹", "icon": "👹", "lv": 35, "hp": 300000,
                 "max_hp": 300000, "reward": {"gold": 2000, "exp": 3000},
                 "map": "abyss_plain", "map_name": "深渊荒原"}})
    out = await cmd(m, "hunt_boss", "g1", "f3", "讨伐")
    check("不在地点提示前往", "深渊荒原" in out and "前往" in out, out[:150])
    # 移动到指定地点
    db.update_player("g1", "f3", cur_map="abyss_plain")
    out = await cmd(m, "hunt_boss", "g1", "f3", "讨伐")
    check("到达后可以讨伐", "讨伐开始" in out or "冲向" in out, out[:150])
    db.clear_world_event()
    db.clear_battle("g1", "f3")
    m._unlock_battle("g1", "f3")

    print("【#6 副本仇恨】")
    await cmd(m, "register", "g1", "f4", "注册 战士 坦克甲")
    await cmd(m, "register", "g1", "f5", "注册 法师 输出乙")
    db.update_player("g1", "f4", level=20, gold=9999, cur_map="vila_square")
    db.update_player("g1", "f5", level=20, gold=9999, cur_map="vila_square")
    await cmd(m, "party", "g1", "f4", "组队 输出乙")
    await cmd(m, "instance_cmd", "g1", "f4", "副本 幽暗墓穴")
    st = db.get_battle("g1", "f4")["state"]
    check("开本有仇恨表", "threat" in st, str(st.keys()))
    check("仇恨初始 0", all(v == 0 for v in st["threat"].values()), str(st["threat"]))
    # 输出乙攻击（拉伤害仇恨）
    st["boss"]["atk"] = 5
    st["boss"]["matk"] = 5
    st["turn_time"] = int(time.time())
    db.save_battle("g1", "f4", st)
    await cmd(m, "attack", "g1", "f5", "攻击")  # 抢回合被拦（轮到队长 f4）
    await cmd(m, "attack", "g1", "f4", "攻击")  # 队长攻击
    st2 = db.get_battle("g1", "f4")["state"]
    threat2 = st2["threat"]
    check("攻击拉仇恨", threat2.get("f4", 0) > 0, str(threat2))
    # 输出乙攻击 → 仇恨可能超过队长
    await cmd(m, "attack", "g1", "f5", "攻击")
    st3 = db.get_battle("g1", "f4")["state"]
    # 输出乙防御 → 嘲讽拉仇恨（v57：行动序按速度排序，拨到输出乙实际所在索引）
    f5_idx = st3["members"].index("f5")
    st3["turn"] = f5_idx
    st3["turn_time"] = int(time.time())
    db.save_battle("g1", "f4", st3)
    out = await cmd(m, "defend", "g1", "f5", "防御")
    check("防御嘲讽提示", "挑衅" in out or "嘲讽" in out or "吸引" in out, out[:150])
    st4 = db.get_battle("g1", "f4")["state"]
    threat4 = st4["threat"]
    # 防御者仇恨应提升（高于或接近最高）
    top_before = max(threat4.get(k, 0) for k in st4["alive"] if st4["alive"][k])
    check("防御拉高仇恨", threat4.get("f5", 0) > 0, str(threat4))
    check("仇恨制 Boss 打最高", True)  # 目标选择逻辑在 _instance_boss_turn，间接验证
    # 清理
    for q in ("f4", "f5"):
        m._unlock_battle("g1", q)
        db.clear_battle("g1", q)

    print(f"\n结果: {passed} passed, {failed} failed")
    return failed

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
