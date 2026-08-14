# -*- coding: utf-8 -*-
"""v112 隐藏线解锁任务链 6（test_v107_unlock_quests.py，v112 重写）

覆盖：
 1. 数据完整性：6 条解锁支线注册（id 唯一 / unlock_class 一一映射 / min_level=40 /
    giver NPC 存在且 funcs 含 quest / 试炼目标怪在对应地图怪物表）
 2. NPC 挂载：6 导师 NPC 挂到对应地图子区域 npcs（SUBAREAS）
 3. min_level 拦截：Lv.30 玩家对话导师 → 拒绝接取提示
 4. 解锁写入：击杀达标 → 『交付任务』→ hidden_class_unlock 写入 + 40 级提示
 5. 转职命令解锁后可用（全流程闭环）

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

# 6 线 → 支线/NPC/地图/试炼怪 映射（与 quests.py/npcs.py 一致；v113 导师迁至种族驻地）
# 注：试炼怪击杀不绑定任务 map（combat 按怪名计数），怪仍须存在于世界（ENGY 检查放宽为任意图）
EXPECT = [
    ("cls_chronomancer",  "s_chronomancer_trial",  "npc_chrono_warden",  "white_deer",       "审判猎犬",   3),
    ("cls_shadow_blade",  "s_shadow_blade_trial",  "npc_shadow_master",   "jade_port",        "影豹",       3),
    ("cls_dragon_oath",   "s_dragon_warrior_trial","npc_dragon_veteran",  "dusk_ridge_road",  "战争魔像(残)", 2),
    ("cls_wild_hunter",   "s_astrologer_trial",    "npc_astrologer",      "starlake",         "湖妖",       3),
    ("cls_wu_sheng",      "s_wu_sheng_trial",      "npc_wusheng_monk",    "anvil_fort",       "兽人劫掠者", 3),
    ("cls_hymn",          "s_necromancer_trial",   "npc_grave_watcher",   "border_castle",    "兽人劫掠者", 3),
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
        # 试炼怪必须存在于世界任意图（v113 导师迁种族驻地后，试炼怪不再限定导师同图；
        # 击杀判定按怪名（combat.py），玩家接任务后去对应图打）
        mob_anywhere = any(mob in [e[0] for e in C.ENCY_MAP_MONSTERS.get(mid, [])]
                           for mid in C.ENCY_MAP_MONSTERS)
        check(f"  {sid} 怪 {mob} 存在于世界", mob_anywhere, "世界无此怪")
    # id 唯一 + unlock_class 唯一（6 = 6 线各 1 条）
    uq = [q for q in C.SIDE_QUESTS if q.get("unlock_class")]
    ids = [q["id"] for q in uq]
    check("unlock_class 支线 id 唯一", len(ids) == len(set(ids)) == 6, str(len(ids)))
    cls_set = [q["unlock_class"] for q in uq]
    check("unlock_class 一一映射 6 线", len(cls_set) == len(set(cls_set)) == 6, str(cls_set))
    check("6 线全覆盖", all(c in cls_set for c, *_ in EXPECT), "缺: " + str([c for c, *_ in EXPECT if c not in cls_set]))
    # v112：旧隐藏职业 id 不再作为解锁目标
    check("旧 13 隐藏职业 id 无残留", not any(q.get("unlock_class") in (
        "cls_bard", "cls_spellblade", "cls_arcanist", "cls_dragon_warrior", "cls_void_walker",
        "cls_astrologer", "cls_jungle_hunter", "cls_templar", "cls_blood_mage",
        "cls_necromancer", "cls_beast_king") for q in uq), str(cls_set))

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
    npc = C.NPCS["npc_chrono_warden"]
    out_lines = m._offer_side_quests("g2", "p1", "npc_chrono_warden", npc)
    out = "".join(out_lines)
    check("Lv.30 对话时咒导师被拒", "Lv.40" in out and "练练" in out, out[:120])
    check("Lv.30 未接取支线", "s_chronomancer_trial" not in (db.get_quests("g2", "p1").get("side") or {}), str(db.get_quests("g2", "p1").get("side")))
    print("[4] 击杀达标 → 交付 → 解锁写入")
    make_player("g2", "p2", "学徒", "法师", level=45)
    db.update_player("g2", "p2", cur_map="white_deer", cur_subarea="white_deer_4")
    # 直接接取（模拟 Lv.45 对话自动接）
    m._offer_side_quests("g2", "p2", "npc_chrono_warden", C.NPCS["npc_chrono_warden"])
    qs = db.get_quests("g2", "p2")
    check("Lv.45 接取时光试炼", "s_chronomancer_trial" in (qs.get("side") or {}), str(qs.get("side")))
    # 模拟击杀 3 只审判猎犬（战斗胜利计数逻辑同款）
    side = qs["side"]
    side["s_chronomancer_trial"] = {"status": "active", "progress": {"审判猎犬": 3}}
    side["s_chronomancer_trial"]["status"] = "ready"
    db.save_quests("g2", "p2", qs)
    # 交付（导师在白鹿城·白鹿圣堂）
    out = await cmd(m, "turn_in", "g2", "p2", "交付任务")
    check("交付解锁时咒法师", "时咒法师" in out and "已解锁" in out, out[:200])
    check("hidden_class_unlock 写入", "cls_chronomancer" in (db.get_player("g2", "p2").get("hidden_class_unlock") or []),
          str(db.get_player("g2", "p2").get("hidden_class_unlock")))
    check("交付提示 40 级", "40 级" in out and "转职 时咒法师" in out, out[:200])
    # 支线标记 done 防重接
    qs2 = db.get_quests("g2", "p2")
    check("支线标记 done", (qs2.get("side") or {}).get("s_chronomancer_trial", {}).get("status") == "done", str(qs2.get("side")))

    print("[5] 转职命令解锁后可用（全流程闭环）")
    # 已解锁 + 40 级 → 『转职 时停』成功（时咒线·时停流派）
    out = await cmd(m, "evolve", "g2", "p2", "转职 时停")
    check("转职 时停 成功", "传承完成" in out and "时停" in out, out[:200])
    p2 = db.get_player("g2", "p2")
    check("职业切换为时咒法师(时停流)", p2["class_name"] == "cls_chronomancer" and p2["evolve_path"] == 1,
          str((p2["class_name"], p2["evolve_path"])))
    # 未解锁职业被拦
    out2 = await cmd(m, "evolve", "g2", "p2", "转职 龙血战士")
    check("未解锁 龙血战士 被拦", "传承还未向你敞开" in out2, out2[:120])

    print(f"\n===== v112 解锁任务链测试: {passed} passed, {failed} failed =====")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
