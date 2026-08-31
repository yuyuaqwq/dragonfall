# -*- coding: utf-8 -*-
"""Probe 4: old_king_tomb hidden room + elven_ruins mechanism + trial_ground NPC in v137."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, Main, FakeEvent, run

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

async def enter_combat(m, gid, qid):
    return await cmd(m, "explore", gid, qid, "探索")

def weaken(st):
    for _eu in (st.get("enemies") or []):
        _eu["hp"] = 1
        _eu["atk"] = 5
        _eu["matk"] = 5
    st["turn_time"] = int(time.time())

def cur_sa(m, gid, qid):
    return (db.get_player(gid, qid) or {}).get("cur_subarea")

async def room_clear(m, gid, qid, max_iter=12):
    for _ in range(max_iter):
        battle = db.get_battle(gid, qid)
        if not battle:
            return "no battle"
        stt = battle["state"]
        if stt.get("mode") == "map":
            sa = cur_sa(m, gid, qid)
            ml = (stt.get("rooms", {}).get(sa, {}) or {}).get("monsters_left") or []
            if not ml:
                return f"cleared sa={sa}"
            out = await cmd(m, "explore", gid, qid, "探索")
        else:
            weaken(stt)
            db.save_battle(gid, qid, stt)
            out = await cmd(m, "attack", gid, stt["members"][stt["turn"]], "攻击")
    return "loop-end"

async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "i1", "注册 战士 队长 男")
    await cmd(m, "register", "g1", "i2", "注册 法师 队员 男")
    db.update_player("g1", "i1", level=70, gold=100000, cur_map="dawn_city", hp=500, max_hp=500)
    db.update_player("g1", "i2", level=70, gold=100000, cur_map="dawn_city", hp=500, max_hp=500)
    await cmd(m, "party", "g1", "i1", "组队 队员")

    # ---- old_king_tomb: rune → mech(need poi_read) → skip_elite ----
    for _ in range(10):
        db.add_item("g1", "i1", "i_key_old_king", {"name": "王陵钥匙", "type": "钥匙", "stackable": True, "price": 500})
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 旧王陵")
    print("== 旧王陵开本 ==", out[:200].replace("\n", " | "))
    # room1: 墓道 - rune_1 墓志铭石碑, trap_1 翻板机关
    out = await cmd(m, "instance_investigate", "g1", "i1", "调查 墓志铭石碑")
    print("== 调查石碑 ==", out[:200].replace("\n", " | "))
    st = db.get_battle("g1", "i1")["state"]
    print("poi_unlocks:", json.dumps(st.get("poi_unlocks"), ensure_ascii=False)[:200])
    print("stage_pois:", json.dumps(st.get("stage_pois"), ensure_ascii=False)[:200])
    # move to room2 (old_king_tomb_2)
    out = await cmd(m, "move", "g1", "i1", "移动 2")
    print("== move2 ==", out[:300].replace("\n", " | "))
    battle = db.get_battle("g1", "i1")
    if battle:
        st = battle["state"]
        print("mode:", st.get("mode"), "boss:", (st.get("boss") or {}).get("name"), "sa:", cur_sa(m, "g1", "i1"))
    out = await cmd(m, "instance_investigate", "g1", "i1", "调查 古王铭文")
    print("== 调查古王铭文 ==", out[:200].replace("\n", " | "))
    st = db.get_battle("g1", "i1")["state"]
    print("poi_unlocks:", json.dumps(st.get("poi_unlocks"), ensure_ascii=False)[:300])
    # move to room3 (old_king_tomb_3): mech 王座机关 need poi_read old_king_tomb_0_rune_1
    out = await cmd(m, "move", "g1", "i1", "移动 2")
    print("== move3 ==", out[:300].replace("\n", " | "))
    battle = db.get_battle("g1", "i1")
    if battle:
        st = battle["state"]
        print("mode:", st.get("mode"), "boss:", (st.get("boss") or {}).get("name"), "sa:", cur_sa(m, "g1", "i1"))
    out = await cmd(m, "instance_investigate", "g1", "i1", "调查 王座机关")
    print("== 调查王座机关 ==", out[:300].replace("\n", " | "))
    st = db.get_battle("g1", "i1")["state"]
    print("skip_elite_next:", st.get("skip_elite_next"))
    # investigate 陪葬宝箱 (chest)
    out = await cmd(m, "instance_investigate", "g1", "i1", "调查 陪葬宝箱")
    print("== 陪葬宝箱 ==", out[:200].replace("\n", " | "))
    st = db.get_battle("g1", "i1")["state"]
    print("rooms[old_king_tomb_3]:", json.dumps(st.get("rooms", {}).get("old_king_tomb_3"), ensure_ascii=False)[:300])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
