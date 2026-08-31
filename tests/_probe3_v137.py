# -*- coding: utf-8 -*-
"""Probe 3: room-by-room progression to hidden room / boss in sea_cave (v137)."""
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
    p = db.get_player(gid, qid)
    return p.get("cur_subarea")

async def room_clear(m, gid, qid, max_iter=10):
    """explore+fight until current room monsters_left empty, mode=map."""
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
    db.update_player("g1", "i1", level=40, gold=100000, cur_map="dawn_city", hp=500, max_hp=500)
    db.update_player("g1", "i2", level=40, gold=100000, cur_map="dawn_city", hp=500, max_hp=500)
    await cmd(m, "party", "g1", "i1", "组队 队员")
    await cmd(m, "instance_cmd", "g1", "i1", "副本 海蚀洞窟")

    # investigate corpse + trap on room 1
    await cmd(m, "instance_investigate", "g1", "i1", "调查 搁浅的水手")
    await cmd(m, "instance_investigate", "g1", "i1", "调查 湿滑礁石")
    print("room1 clear:", await room_clear(m, "g1", "i1"))
    st = db.get_battle("g1", "i1")["state"]
    print("stage_cleared:", st.get("stage_cleared"), "mode:", st.get("mode"))

    # move to room 2 (sea_cave_2 沉船滩涂) -- links: sea_cave_1 -> sea_cave_2
    out = await cmd(m, "move", "g1", "i1", "移动 沉船滩涂")
    print("== move to 沉船滩涂 ==")
    print(out[:500])
    print("cur_sa:", cur_sa(m, "g1", "i1"))
    battle = db.get_battle("g1", "i1")
    if battle:
        st = battle["state"]
        print("mode:", st.get("mode"), "boss:", (st.get("boss") or {}).get("name"))
        print("rooms[sea_cave_2]:", json.dumps(st.get("rooms", {}).get("sea_cave_2"), ensure_ascii=False)[:400])

    # investigate chest on room 2
    out = await cmd(m, "instance_investigate", "g1", "i1", "调查 海盗宝箱")
    print("== 海盗宝箱 ==")
    print(out[:300])

    # clear room 2
    print("room2 clear:", await room_clear(m, "g1", "i1"))
    st = db.get_battle("g1", "i1")["state"]
    print("stage_cleared:", st.get("stage_cleared"), "mode:", st.get("mode"))

    # move to room 3 (sea_cave_3 藏宝密室)
    out = await cmd(m, "move", "g1", "i1", "移动 藏宝密室")
    print("== move to 藏宝密室 ==")
    print(out[:600])
    battle = db.get_battle("g1", "i1")
    if battle:
        st = battle["state"]
        print("mode:", st.get("mode"), "boss:", (st.get("boss") or {}).get("name"), "stage_idx:", st.get("stage_idx"))
        print("stage_secret_found:", st.get("stage_secret_found"))
        print("rooms[sea_cave_3]:", json.dumps(st.get("rooms", {}).get("sea_cave_3"), ensure_ascii=False)[:400])

    # map view
    out = await cmd(m, "instance_map_view_cmd", "g1", "i1", "副本地图")
    print("== 副本地图 ==")
    print(out[:800])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
