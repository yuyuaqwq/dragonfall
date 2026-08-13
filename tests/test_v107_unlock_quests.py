# -*- coding: utf-8 -*-
"""v107 隐藏职业解锁任务链 11（test_v107_unlock_quests.py）

覆盖：
 1. 数据完整性：11 条解锁支线注册（id 唯一 / unlock_class 一一映射 / min_level=40 /
    giver NPC 存在且 funcs 含 quest / 试炼目标怪在对应地图怪物表）
 2. NPC 挂载：11 导师 NPC 挂到对应地图子区域 npcs（SUBAREAS）
 3. min_level 拦截：Lv.30 玩家对话导师 → 拒绝接取提示
 4. 解锁写入：击杀达标 → 『交付任务』→ hidden_class_unlock 写入 + 40 级提示

运行：python tests/test_v107_unlock_quests.py（exit=0 全绿）
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, Main, run, make_player

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
    ev = __import__("conftest").FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return "".join(str(x) for x in results)

# 11 职业 → 支线/NPC/地图/试炼怪 映射（与 quests.py/npcs.py 一致）
EXPECT = [
    ("cls_arcanist",      "s_arcanist_trial",      "npc_arcanist_warden", "secret_crypt",     "审判猎犬",   3),
    ("cls_shadow_blade",  "s_shadow_blade_trial",  "npc_shadow_master",   "moonshadow_wood",  "影豹",       3),
    ("cls_dragon_warrior","s_dragon_warrior_trial","npc_dragon_veteran",  "dusk_ridge_road",  "战争魔像(残)", 2),
    ("cls_void_walker",   "s_void_walker_trial",   "npc_void_watcher",    "storm_strait",     "风暴元素",   3),
    ("cls_astrologer",    "s_astrologer_trial",    "npc_astrologer",      "starlake",         "湖妖",       3),
    ("cls_jungle_hunter", "s_jungle_hunter_trial", "npc_jungle_hunter",   "emerald_valley",   "谷地仙灵",   3),
    ("cls_templar",       "s_templar_trial",       "npc_templar_knight",  "holy_trial",       "试炼骑士长", 1),
    ("cls_wu_sheng",      "s_wu_sheng_trial",      "npc_wusheng_monk",    "border_castle",    "兽人劫掠者", 3),
    ("cls_blood_mage",    "s_blood_mage_trial",    "npc_blood_priest",    "secret_crypt",     "暗影祭司",   3),
    ("cls_necromancer",   "s_necromancer_trial",   "npc_grave_watcher",   "old_king_tomb",    "骷髅兵",     3),
    ("cls_beast_king",    "s_beast_king_trial",    "npc_beast_tamer",     "silverwood",       "月狼",       3),
]

async def main():
    clean_db()
    m = Main(None)

    print("[1] 解锁支线数据完整性")
    sq_by_id = {q["id"]: q for q in C.SIDE_QUESTS}
    for cls_id, sid, npc_id, map_id, mob, cnt in EXPECT:
        sq = sq_by_id.get(sid)
        check(f"{cls_id} 支线 {sid} 注册", sq is not None, "缺失")
        if not sq:
            continue
        check(f"  {sid} unlock_class={cls_id}", sq.get("unlock_class") == cls_id, str(sq.get("unlock_class")))
        check(f"  {sid} min_level=40", sq.get("min_level") == 40, str(sq.get("min_level")))
        check(f"  {sid} giver={npc_id}", sq.get("giver") == npc_id, str(sq.get("giver")))
        obj = sq.get("objective", {})
        check(f"  {sid} 目标 {mob}×{cnt}", obj.get("kill") == mob and obj.get("count") == cnt, str(obj))
        # 试炼怪必须在对应地图怪物表
        mobs = [e[0] for e in C.ENCY_MAP_MONSTERS.get(map_id, [])]
        check(f"  {sid} 怪 {mob} 在 {map_id}", mob in mobs, f"该图怪: {mobs}")
    # id 唯一 + unlock_class 唯一（12 = 11 v107 + 旧魔剑士 s_spellblade_trial）
    uq = [q for q in C.SIDE_QUESTS if q.get("unlock_class")]
    ids = [q["id"] for q in uq]
    check("unlock_class 支线 id 唯一", len(ids) == len(set(ids)) == 12, str(len(ids)))
    cls_set = [q["unlock_class"] for q in uq]
    check("unlock_class 一一映射 12 职业", len(cls_set) == len(set(cls_set)) == 12, str(cls_set))
    check("11 新职业全覆盖", all(c in cls_set for c, *_ in EXPECT), "缺: " + str([c for c, *_ in EXPECT if c not in cls_set]))

    print("[2] 导师 NPC + 子区域挂载")
    for cls_id, sid, npc_id, map_id, mob, cnt in EXPECT:
        npc = C.NPCS.get(npc_id)
        check(f"{npc_id} NPC 注册", npc is not None, "缺失")
        if not npc:
            continue
        check(f"  {npc_id} map={map_id}", npc.get("map") == map_id, str(npc.get("map")))
        check(f"  {npc_id} quest={sid}", npc.get("quest") == sid, str(npc.get("quest")))
        check(f"  {npc_id} funcs 含 quest", "quest" in (npc.get("funcs") or []), str(npc.get("funcs")))
        # 子区域挂载：地图任一子区域 npcs 含该 NPC
        sas = C.SUBAREAS.get(map_id, [])
        mounted = any(npc_id in (sa.get("npcs") or []) for sa in sas)
        check(f"  {npc_id} 挂载到 {map_id} 子区域", mounted, f"子区域数 {len(sas)}")

    print("[3] min_level 拦截（Lv.30 被拒）")
    make_player("g2", "p1", "新手", "战士", level=30)
    npc = C.NPCS["npc_arcanist_warden"]
    out_lines = m._offer_side_quests("g2", "p1", "npc_arcanist_warden", npc)
    out = "".join(out_lines)
    check("Lv.30 对话奥术导师被拒", "Lv.40" in out and "练练" in out, out[:120])
    check("Lv.30 未接取支线", "s_arcanist_trial" not in (db.get_quests("g2", "p1").get("side") or {}), str(db.get_quests("g2", "p1").get("side")))

    print("[4] 击杀达标 → 交付 → 解锁写入")
    make_player("g2", "p2", "学徒", "法师", level=45)
    db.update_player("g2", "p2", cur_map="secret_crypt")
    # 直接接取（模拟 Lv.45 对话自动接）
    m._offer_side_quests("g2", "p2", "npc_arcanist_warden", C.NPCS["npc_arcanist_warden"])
    qs = db.get_quests("g2", "p2")
    check("Lv.45 接取奥术回响", "s_arcanist_trial" in (qs.get("side") or {}), str(qs.get("side")))
    # 模拟击杀 3 只审判猎犬（战斗胜利计数逻辑同款）
    side = qs["side"]
    side["s_arcanist_trial"] = {"status": "active", "progress": {"审判猎犬": 3}}
    side["s_arcanist_trial"]["status"] = "ready"
    db.save_quests("g2", "p2", qs)
    # 交付
    out = await cmd(m, "turn_in", "g2", "p2", "交付任务")
    check("交付解锁奥术师", "奥术师" in out and "已解锁" in out, out[:200])
    check("hidden_class_unlock 写入", "cls_arcanist" in (db.get_player("g2", "p2").get("hidden_class_unlock") or []),
          str(db.get_player("g2", "p2").get("hidden_class_unlock")))
    check("交付提示 40 级", "40 级" in out and "转职 奥术师" in out, out[:200])
    # 支线标记 done 防重接
    qs2 = db.get_quests("g2", "p2")
    check("支线标记 done", (qs2.get("side") or {}).get("s_arcanist_trial", {}).get("status") == "done", str(qs2.get("side")))

    print("[5] 转职命令解锁后可用（全流程闭环）")
    # 已解锁 + 40 级 → 『转职 奥术师』成功
    out = await cmd(m, "evolve", "g2", "p2", "转职 奥术师")
    check("转职 奥术师 成功", "传承完成" in out and "奥术师" in out, out[:200])
    check("职业切换为奥术师", db.get_player("g2", "p2")["class_name"] == "cls_arcanist", str(db.get_player("g2", "p2")["class_name"]))
    # 未解锁职业被拦
    out2 = await cmd(m, "evolve", "g2", "p2", "转职 龙血战士")
    check("未解锁 龙血战士 被拦", "传承还未向你敞开" in out2, out2[:120])

    print(f"\n===== v107 解锁任务链测试: {passed} passed, {failed} failed =====")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
