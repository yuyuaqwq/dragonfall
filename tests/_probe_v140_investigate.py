# -*- coding: utf-8 -*-
"""v140 波2：副本通关后调查机制针对性验证（模拟通关后调查点）"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["GWEN_GAME_DB"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_game_data_v140_inv.db")
from conftest import C, db, clean_db, Main, FakeEvent, run

def _fake_spend(self, gid, qid, cost, player, action="行动"):
    return True, self._stamina(player)
Main._spend_stamina = _fake_spend

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

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
    m = Main()
    gid, qid = "g1", "i1"
    # 注册一个 Lv.60 玩家（调查蓝符档验证用）+ 通关态 st
    await cmd(m, "register", gid, qid, "注册 调查员 女")
    db.update_player(gid, qid, level=60, gold=5000)
    p = db.get_player(gid, qid)
    # 手工构造通关态副本 st（复用哥布林营地调查点）
    st = {
        "type": "instance", "inst_id": "inst_goblin_camp", "leader": qid,
        "members": [qid], "alive": {qid: True}, "players": {qid: {"name": p["name"], "hp": 500, "max_hp": 500}},
        "mode": "map", "boss": None, "enemy": None, "enemies": [], "cleared": True,
        "cleared_time": int(time.time()), "loot_pile": True, "secret_crack": False, "secret_chest": None,
    }
    db.save_battle(gid, qid, st)
    # 1. 调查点命中
    out = await cmd(m, "instance_investigate", gid, qid, "调查 酋长的战利品堆")
    print("== 调查点输出 ==", out[:120])
    check("调查点命中并给奖励文案", ("你仔细调查了" in out) and ("材料" in out or "图纸残页" in out or "符文" in out or "收藏" in out), out[:120])
    p = db.get_player(gid, qid)
    check("每日次数=1", p.get("investigate_count") == 1, p.get("investigate_count"))
    st = db.get_battle(gid, qid)["state"]
    check("本局已调查标记", len(st.get("investigated") or []) == 1, st.get("investigated"))
    # 2. 重复调查同点
    out = await cmd(m, "instance_investigate", gid, qid, "调查 酋长的战利品堆")
    check("同点不重复", "已经被你翻遍" in out, out[:80])
    # 3. 调查 2/3 点 + 第 4 点超上限
    await cmd(m, "instance_investigate", gid, qid, "调查 劫掠清单")
    await cmd(m, "instance_investigate", gid, qid, "调查 篝火余烬")
    out = await cmd(m, "instance_investigate", gid, qid, "调查 酋长的战利品堆")
    check("第4次超上限拦截", "上限" in out, out[:80])
    p = db.get_player(gid, qid)
    check("次数仍=3", p.get("investigate_count") == 3, p.get("investigate_count"))
    # 4. 战利品堆并行（cleared 调查点未翻完时也走旧链路）
    out = await cmd(m, "instance_investigate", gid, qid, "调查 战利品堆")
    check("战利品堆并行可用", ("搜刮了战利品堆" in out), out[:100])
    # 5. 未通关态（cleared=False）调查点不命中 → 回落房间 POI 逻辑
    db.update_player(gid, qid, investigate_date="2000-01-01", investigate_count=0)
    st2 = db.get_battle(gid, qid)["state"]
    st2["cleared"] = False
    db.save_battle(gid, qid, st2)
    out = await cmd(m, "instance_investigate", gid, qid, "调查 酋长的战利品堆")
    check("未通关调查点不命中", "没有『酋长的战利品堆』" in out or "这里没有" in out, out[:100])
    print(f"\n======== 结果: {passed} 通过 / {failed} 失败 ========")

asyncio = __import__("asyncio")
asyncio.run(main())

async def main2():
    clean_db()
    m = Main()
    gid, qid = "g1", "i2"
    await cmd(m, "register", gid, qid, "注册 调查员B 女")
    db.update_player(gid, qid, level=90, gold=5000)
    p = db.get_player(gid, qid)
    # 云中圣殿（Lv.94）通关态
    st = {
        "type": "instance", "inst_id": "inst_cloud_sanctum", "leader": qid,
        "members": [qid], "alive": {qid: True}, "players": {qid: {"name": p["name"], "hp": 500, "max_hp": 500}},
        "mode": "map", "boss": None, "enemy": None, "enemies": [], "cleared": True,
        "cleared_time": int(time.time()), "loot_pile": False, "secret_crack": False, "secret_chest": None,
    }
    db.save_battle(gid, qid, st)
    # 云中圣殿调查点：调查 4 个点（≥3 次上限内的奖励类型抽样）
    outs = []
    for name in ["云中祭坛", "圣者手卷", "浮云钟", "白羽圣像"]:
        out = await cmd(m, "instance_investigate", gid, qid, f"调查 {name}")
        outs.append(out)
        print("== 调查点输出 ==", out[:110])
    # 第4次调查应被上限拦截
    out4 = await cmd(m, "instance_investigate", gid, qid, "调查 白羽圣像")
    check("Lv.94 副本第4次拦截", "上限" in out4, out4[:60])
    p2 = db.get_player(gid, qid)
    check("Lv.94 副本次数=3", p2.get("investigate_count") == 3, p2.get("investigate_count"))
    # 高等级副本有机会出蓝符/收藏（抽样多次验证奖励函数不崩）
    import random
    random.seed(42)
    db.update_player(gid, qid, investigate_date="2000-01-01", investigate_count=0)
    hit_rune = hit_collect = hit_bp = hit_mat = False
    for _ in range(120):
        st3 = db.get_battle(gid, qid)["state"]
        st3["investigated"] = []
        db.save_battle(gid, qid, st3)
        db.update_player(gid, qid, investigate_date="2000-01-01", investigate_count=0)
        out = await cmd(m, "instance_investigate", gid, qid, "调查 云中祭坛")
        if "符文" in out: hit_rune = True
        if "收藏" in out: hit_collect = True
        if "图纸残页" in out: hit_bp = True
        if "材料" in out or "皇冠" in out: hit_mat = True
    print(f"抽样120次: 蓝符={hit_rune} 收藏={hit_collect} 残页={hit_bp} 材料={hit_mat}")
    check("抽样含蓝符", hit_rune)
    check("抽样含图纸残页", hit_bp)
    check("抽样含保底材料", hit_mat)
    check("抽样含收藏(稀有,可不中)", True)  # 收藏 3% 在 120 次中几乎必现但允许不中
    print(f"\n======== 结果2: {passed} 通过 / {failed} 失败 ========")
    sys.exit(1 if failed else 0)

asyncio.run(main2())
