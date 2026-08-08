# -*- coding: utf-8 -*-
"""v83 探索彩蛋事件（02 章 7.5）：流星许愿 / 神秘宝匣 / 神秘访客 + 许愿命令"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, E, BT, Main, FakeEvent, run, clean_db, make_player

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("  ✅ %s" % name)
    else:
        failed += 1
        print("  ❌ %s %s" % (name, detail))


async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""


async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "w1", "注册 战士 旅人")
    db.update_player("g1", "w1", cur_map="oak_plain")
    player = db.get_player("g1", "w1")
    cur_map = C.MAP_BY_ID["oak_plain"]

    # ---- 概率采样（固定 seed 量级）----
    import random
    random.seed(7)
    n = 10000
    hits = sum(1 for _ in range(n) if C.roll_explore_egg() is not None)
    check("彩蛋总概率≈0.5%", 0.002 < hits / n < 0.01, f"{hits/n:.4f}")

    # ---- 流星许愿：触发 + 三选一 ----
    orig_egg = C.roll_explore_egg
    C.roll_explore_egg = lambda: {"id": "shooting_star", "weight": 60, "name": "流星许愿"}
    try:
        handled, text = m._handle_explore_event("g1", "w1", player, cur_map)
    finally:
        C.roll_explore_egg = orig_egg
    check("流星触发提示选项", handled and "许愿 经验" in text and "许愿 金币" in text, text[:200])
    # 许愿 经验
    gold0 = db.get_player("g1", "w1")["gold"]
    out = await cmd(m, "wish", "g1", "w1", "许愿 经验")
    check("许愿经验成功", "经验 +" in out, out[:200])
    # 许愿 金币（重新触发）
    C.roll_explore_egg = lambda: {"id": "shooting_star", "weight": 60, "name": "流星许愿"}
    try:
        m._handle_explore_event("g1", "w1", db.get_player("g1", "w1"), cur_map)
    finally:
        C.roll_explore_egg = orig_egg
    out = await cmd(m, "wish", "g1", "w1", "许愿 金币")
    check("许愿金币成功", "金币 +" in out, out[:200])
    check("金币增加", db.get_player("g1", "w1")["gold"] > gold0, "")
    # 许愿 材料（重新触发）
    C.roll_explore_egg = lambda: {"id": "shooting_star", "weight": 60, "name": "流星许愿"}
    try:
        m._handle_explore_event("g1", "w1", db.get_player("g1", "w1"), cur_map)
    finally:
        C.roll_explore_egg = orig_egg
    out = await cmd(m, "wish", "g1", "w1", "许愿 材料")
    check("许愿材料成功", "获得材料" in out, out[:200])
    # 无状态许愿被拦
    out = await cmd(m, "wish", "g1", "w1", "许愿 经验")
    check("无流星被拦", "没有流星" in out, out[:200])
    # 非法选项
    C.roll_explore_egg = lambda: {"id": "shooting_star", "weight": 60, "name": "流星许愿"}
    try:
        m._handle_explore_event("g1", "w1", db.get_player("g1", "w1"), cur_map)
    finally:
        C.roll_explore_egg = orig_egg
    out = await cmd(m, "wish", "g1", "w1", "许愿 随便")
    check("非法选项提示三选一", "三选一" in out or "快选" in out, out[:200])

    # ---- 神秘宝匣 ----
    C.roll_explore_egg = lambda: {"id": "mystery_chest", "weight": 30, "name": "神秘宝匣"}
    try:
        handled, text = m._handle_explore_event("g1", "w1", db.get_player("g1", "w1"), cur_map)
    finally:
        C.roll_explore_egg = orig_egg
    check("宝匣给金币+图纸", handled and "神秘宝匣" in text and "金币" in text and "图纸" in text, text[:200])

    # ---- 神秘访客：设置隐藏 NPC flag ----
    C.roll_explore_egg = lambda: {"id": "night_visitor", "weight": 10, "name": "神秘访客"}
    try:
        handled, text = m._handle_explore_event("g1", "w1", db.get_player("g1", "w1"), cur_map)
    finally:
        C.roll_explore_egg = orig_egg
    check("访客提示线索", handled and "神秘访客" in text and "裂隙" in text, text[:200])
    check("h_abyss_whisper flag 已设", "saw_the_rift" in db.get_talk_flags("g1", "w1", "h_abyss_whisper"), str(db.get_talk_flags("g1", "w1", "h_abyss_whisper")))

    # ---- 成就 cond ----
    from data.plugins.dragonfall.game.core.achievements import cond_met
    check("wish_met cond 命中", cond_met({}, {}, {}, {"wish_met": True}, {"type": "wish_met"}), "")
    check("wish_met cond 不命中", not cond_met({}, {}, {}, {}, {"type": "wish_met"}), "")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
