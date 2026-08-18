# -*- coding: utf-8 -*-
"""v113 隐藏线血脉传承测试（test_v113_bloodline.py）

覆盖：
1. 数据完整性：6 试炼任务 require_race 全配；6 导师对话树存在且 start 合法
2. 对话条件：race_is / hidden_unlocked / not_hidden_current 注册且筛选正确
3. 血脉拒绝：非对应种族找导师对话 → 导师拒绝（无传承选项）
4. 血脉认可：对应种族找导师 → 显示试炼/传承选项
5. 『接取』指令种族门槛：非对应种族接试炼被拒
6. 对话传承：解锁后导师对话『接受传承』→ 转职成功（async hidden_evolve）
7. 传承后：导师对话不再显示传承选项
"""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, Main, FakeEvent, run

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {str(detail)[:200]}")


async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return "".join(str(x) for x in results)


# 六线映射：导师 / 种族 / 隐藏线 / 地图（导师新位置）/ 导师所在子区域 / 血脉台词关键词
LINES = [
    ("npc_dragon_veteran", "dragonborn", "cls_dragon_oath", "dusk_ridge_road", "dusk_ridge_road_1", "龙骨山脉"),
    ("npc_chrono_warden", "human", "cls_chronomancer", "white_deer", "white_deer_4", "人类的求知欲"),
    ("npc_astrologer", "elf", "cls_wild_hunter", "starlake", "starlake_1", "银月精灵"),
    ("npc_grave_watcher", "orc", "cls_hymn", "border_castle", "border_castle_1", "战血"),
    ("npc_shadow_master", "halfling", "cls_shadow_blade", "jade_port", "jade_port_1", "灵巧的血脉"),
    ("npc_wusheng_monk", "dwarf", "cls_wu_sheng", "anvil_fort", "anvil_fort_gate", "筋骨如铁"),
]


async def main():
    clean_db()
    m = Main(None)

    print("【1. 数据完整性】")
    for sq in C.SIDE_QUESTS:
        if sq.get("unlock_class"):
            check(f"{sq['id']} require_race 配置", bool(sq.get("require_race")), str(sq))
    for nid, race, cls_id, map_id, subarea, kw in LINES:
        dlg = C.DIALOGUES.get(nid)
        check(f"{nid} 对话树存在", bool(dlg and dlg.get("start") in (dlg.get("nodes") or {})), str(dlg and dlg.get("start")))
        # 试炼任务 require_race 与 src_race 一致
        cls = C.CLASSES[cls_id]
        check(f"{cls_id} src_race={race}", cls.get("src_race") == race, str(cls.get("src_race")))
        # 导师 map 与试炼任务 map 一致
        quest = next((q for q in C.SIDE_QUESTS if q.get("unlock_class") == cls_id), None)
        npc = C.NPCS.get(nid, {})
        check(f"{nid} 导师驻地={C.MAP_BY_ID.get(map_id, {}).get('name')}", npc.get("map") == map_id and quest and quest.get("map") == map_id,
              str((npc.get("map"), quest and quest.get("map"))))

    print("【2. 对话条件筛选】")
    for nid, race, cls_id, map_id, subarea, kw in LINES:
        dlg = C.get_dialogue(nid)
        ctx_ok = {"player": {"class_name": "cls_zhan_shi", "race": race, "hidden_class_unlock": [], "class_tier": 0, "level": 40},
                  "quests": {}, "flags": {}, "apprentices": [], "npc_id": nid,
                  "side_quests": C.SIDE_QUESTS, "item_counts": {}}
        ctx_bad = dict(ctx_ok)
        ctx_bad["player"] = dict(ctx_ok["player"], race="human" if race != "human" else "elf")
        opts_ok = C.visible_options(dlg, C.dialogue_node(dlg, "welcome"), ctx_ok)
        opts_bad = C.visible_options(dlg, C.dialogue_node(dlg, "welcome"), ctx_bad)
        check(f"{nid} 对应种族可见试炼选项", any("试炼" in o["text"] or "渴望" in o["text"] or "聆听" in o["text"] or "想" in o["text"] for o in opts_ok),
              str([o["text"] for o in opts_ok]))
        check(f"{nid} 非对应种族无传承选项", not any(o.get("action", {}).get("hidden_evolve") for o in opts_bad)
              and len(opts_bad) <= 2, str([o["text"] for o in opts_bad]))

    print("【3. 血脉拒绝（对话）】")
    await cmd(m, "register", "g1", "w1", "注册 战士 人类战 男")
    db.update_player("g1", "w1", level=40, cur_map="dusk_ridge_road", cur_subarea="dusk_ridge_road_1")
    out = await cmd(m, "talk_choice", "g1", "w1", "对话 龙裔老兵·铁鳞")
    check("人类找铁鳞被拒", "龙骨山脉" in out and "接受传承" not in out, out[:150])
    check("拒绝后无传承选项", "渴望龙血" not in out, out[:150])

    print("【4. 『接取』指令种族门槛】")
    await cmd(m, "register", "g1", "w2", "注册 战士 人类战2 男")
    db.update_player("g1", "w2", level=40, cur_map="dusk_ridge_road", cur_subarea="dusk_ridge_road_1")
    out = await cmd(m, "quest_accept", "g1", "w2", "接取 龙骨之血")
    check("人类接龙血被拒", "龙裔的血脉" in out, out[:150])
    q = db.get_quests("g1", "w2")
    check("任务未接", "s_dragon_warrior_trial" not in (q.get("side") or {}), str(q.get("side")))

    print("【5. 对话传承（6 线逐一）】")
    for i, (nid, race, cls_id, map_id, subarea, kw) in enumerate(LINES, 1):
        qid = f"b{i}"
        base_cls = C.CLASSES[cls_id]["src_base"]
        base_name = C.CLASSES[base_cls]["name"]
        await cmd(m, "register", "g1", qid, f"注册 {base_name} 传承{i} 男")
        db.update_player("g1", qid, level=40, race=race, cur_map=map_id,
                         cur_subarea=subarea, hidden_class_unlock=[cls_id])
        # 对话 → 选项1（试炼/渴望入口）→ trial 节点 → 选项1（接受传承）
        await cmd(m, "talk_choice", "g1", qid, f"对话 {C.NPCS[nid]['name']}")
        out = await cmd(m, "talk_choice", "g1", qid, "1")
        out = await cmd(m, "talk_choice", "g1", qid, "1")
        p = db.get_player("g1", qid)
        ok = p["class_name"] == cls_id and p["class_tier"] == 1 and p["evolve_path"] == 1
        check(f"{cls_id} 对话传承成功", ok, f"{p['class_name']}/{p['class_tier']}/{p['evolve_path']}")
        if not ok:
            check("  传承文案", "传承完成" in out, out[:200])
        # 传承后对话不再显示传承选项
        await cmd(m, "talk_choice", "g1", qid, f"对话 {C.NPCS[nid]['name']}")
        out2 = await cmd(m, "talk_choice", "g1", qid, "1")
        check(f"{cls_id} 传承后无传承选项", "接受传承" not in out2, out2[:120])

    print("【6. 升档对话（已传承 → T2）】")
    await cmd(m, "register", "g1", "z1", "注册 战士 龙升 男")
    db.update_player("g1", "z1", level=60, race="dragonborn", cur_map="dusk_ridge_road",
                     cur_subarea="dusk_ridge_road_1", hidden_class_unlock=["cls_dragon_oath"])
    await cmd(m, "talk_choice", "g1", "z1", "对话 龙裔老兵·铁鳞")
    await cmd(m, "talk_choice", "g1", "z1", "1")
    out = await cmd(m, "talk_choice", "g1", "z1", "1")
    p = db.get_player("g1", "z1")
    check("60 级传承=T2(修为继承)", p["class_name"] == "cls_dragon_oath" and p["class_tier"] == 2,
          str((p["class_name"], p["class_tier"])))

    print()
    print(f"===== v113 血脉传承测试: {passed} passed, {failed} failed =====")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
