# -*- coding: utf-8 -*-
"""commands 层：世界域（地图/移动/传送/NPC/任务/探索/事件/垂钓/采集）（源自 v6/v6_events/v7/v11/v18/v19/v20/v30/v36/v38）

验证：
  1. 地图/移动：地图列表/移动/跨地图
  2. 传送：方碑激活/传送付费
  3. NPC：找/对话（含主线完成动态台词）
  4. 任务：主线/每日/支线接取与交还
  5. 探索：野外探索/精英怪
  6. 世界事件：讨伐/拍卖
  7. 垂钓/采集/挖掘
"""
import sys, os, sqlite3, time, json
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
    await cmd(m, "register", "g1", "w1", "注册 战士 旅人")
    db.update_player("g1", "w1", level=5, gold=1000, cur_map="vila_square")

    print("【地图：地图列表】")
    out = await cmd(m, "map_view", "g1", "w1", "地图")
    check("地图显示", "维拉" in out or "地图" in out, out[:120])

    print("【移动】")
    out = await cmd(m, "move", "g1", "w1", "移动 维拉镇中央大街")
    check("移动有返回", len(out) > 5, out[:120])
    p = db.get_player("g1", "w1")
    check("地图切换", p.get("cur_map") == "vila_street", str(p.get("cur_map")))
    # v54.1 修复：垂钓点地图查看不再抛 get_prof_level 缺参异常
    db.update_player("g1", "w1", cur_map="vila_gate")
    out = await cmd(m, "map_view", "g1", "w1", "地图")
    check("垂钓点地图显示正常", len(out) > 5 and "垂钓" in out or "此地" in out, out[:150])

    print("【探索：野外】")
    db.update_player("g1", "w1", cur_map="vila_gate")
    out = await cmd(m, "explore", "g1", "w1", "探索")
    check("探索有返回", len(out) > 10, out[:100])

    print("【传送：方碑】")
    out = await cmd(m, "portal_view", "g1", "w1", "方碑")
    check("方碑有返回", len(out) > 3, out[:120])
    # 激活/传送（若已激活过则提示不同）
    out = await cmd(m, "portal_activate", "g1", "w1", "激活 维拉镇")
    check("激活有返回", len(out) > 3, out[:120])

    print("【NPC：找/对话】")
    out = await cmd(m, "find_npc", "g1", "w1", "找 铁匠")
    check("找NPC有返回", len(out) > 5, out[:120])
    out = await cmd(m, "find_npc", "g1", "w1", "找 镇长")
    check("NPC对话有返回", len(out) > 5, out[:120])

    print("【任务：主线】")
    out = await cmd(m, "quest_view", "g1", "w1", "任务")
    check("任务列表有返回", "主线" in out or "任务" in out, out[:120])
    # 主线完成 → NPC 台词动态化（v36 模式）
    db.save_quests("g1", "w1", {"main_quest": None, "main_status": "", "main_progress": 0,
                               "daily": {}, "completed_main": ["q1"], "side": []})
    out = await cmd(m, "find_npc", "g1", "w1", "找 镇长")
    check("主线完成后NPC台词", len(out) > 5, out[:120])

    print("【世界事件：讨伐】")
    out = await cmd(m, "world_event", "g1", "w1", "事件")
    check("事件列表有返回", len(out) > 5, out[:120])

    print("【垂钓/采集】")
    db.update_player("g1", "w1", cur_map="vila_gate")
    db.clear_battle("g1", "w1")  # v55：先清战斗状态（前面探索/事件可能进过战斗）
    out = await cmd(m, "fishing", "g1", "w1", "垂钓")
    check("垂钓有返回", len(out) > 5, out[:120])
    # v55 等待制：开始垂钓后是等待状态，立即再发提示剩余
    out = await cmd(m, "fishing", "g1", "w1", "垂钓")
    check("垂钓等待中提示剩余", "还在垂钓" in out, out[:120])
    # v55 等待制：垂钓等待中采集被互斥拦截
    out = await cmd(m, "gather", "g1", "w1", "采集")
    check("等待中采集互斥拦截", "还在垂钓" in out, out[:120])
    # v55 等待制：把完成时间改成过去 → 惰性结算 + 自动开新轮
    st = m._prof_wait_state("g1", "w1")
    st["finish"] = int(time.time()) - 1
    db.set_event_state(m._prof_wait_key("g1", "w1"), json.dumps(st, ensure_ascii=False))
    out = await cmd(m, "fishing", "g1", "w1", "垂钓")
    check("垂钓到期结算+自动开新", ("钓上来" in out or "钓上了" in out or "垃圾" in out or "宝物" in out or "鱼王" in out) and "开始垂钓" in out, out[:200])
    # v55 等待制：清状态后采集正常开轮
    m._prof_wait_clear("g1", "w1")
    out = await cmd(m, "gather", "g1", "w1", "采集")
    check("采集有返回", len(out) > 5 and "开始采集" in out, out[:120])
    # v55 等待制：等级越高等待越短 + 保底 10 秒
    db.add_prof_exp("g1", "w1", "fishing", 900)
    lv = db.get_prof_level("g1", "w1", "fishing")
    wait_hi = m._prof_wait_duration("fishing", lv)
    wait_lo = m._prof_wait_duration("fishing", 1)
    check("等待随等级缩短", wait_hi <= wait_lo and wait_hi >= 10, f"Lv{lv}={wait_hi}s Lv1={wait_lo}s")
    # v55 装饰器统一互斥：垂钓等待中 移动/传送/探索/副本/讨伐 全被拦
    m._prof_wait_clear("g1", "w1")  # 先清掉前面测试残留的采集等待
    await cmd(m, "fishing", "g1", "w1", "垂钓")
    for hname, msg, label in [("move", "移动 维拉镇", "移动"), ("portal_travel", "传送 维拉镇", "传送"),
                               ("explore", "探索", "探索"), ("instance_cmd", "副本", "副本"), ("hunt_boss", "讨伐", "讨伐")]:
        out = await cmd(m, hname, "g1", "w1", msg)
        check(f"副业等待中{label}被拦", "还在垂钓" in out, out[:80])

    print("【数据：主线任务完整性】")
    missing = [q for q in C.MAIN_QUESTS if not q.get("story") or not q.get("ending")] if hasattr(C, "MAIN_QUESTS") else []
    if hasattr(C, "MAIN_QUESTS"):
        check("30 主线任务全部有 story/ending", len(missing) == 0, str([q.get("id") for q in missing[:5]]))
    else:
        print("  ⚠️ MAIN_QUESTS 未暴露，跳过")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
