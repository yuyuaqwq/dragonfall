# -*- coding: utf-8 -*-
"""Probe 2: sea cave hidden room secret flow in v137 (rooms-based)."""
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

async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "i1", "注册 战士 队长 男")
    await cmd(m, "register", "g1", "i2", "注册 法师 队员 男")
    db.update_player("g1", "i1", level=40, gold=100000, cur_map="dawn_city", hp=500, max_hp=500)
    db.update_player("g1", "i2", level=40, gold=100000, cur_map="dawn_city", hp=500, max_hp=500)
    await cmd(m, "party", "g1", "i1", "组队 队员")
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 海蚀洞窟")
    print("== 开本 ==")
    print(out[:400])

    # investigate corpse on sea_cave_1
    out = await cmd(m, "instance_investigate", "g1", "i1", "调查 搁浅的水手")
    print("== 调查水手 ==")
    print(out[:400])
    st = db.get_battle("g1", "i1")["state"]
    print("rooms[sea_cave_1]=", json.dumps(st.get("rooms", {}).get("sea_cave_1"), ensure_ascii=False)[:300])
    print("stage_pois=", json.dumps(st.get("stage_pois"), ensure_ascii=False)[:400])
    print("poi_unlocks=", json.dumps(st.get("poi_unlocks"), ensure_ascii=False)[:200])

    # trap
    hp_before = st["players"]["i1"]["hp"]
    out = await cmd(m, "instance_investigate", "g1", "i1", "调查 湿滑礁石")
    print("== 调查礁石 ==")
    print(out[:400])
    st = db.get_battle("g1", "i1")["state"]
    print("i1 hp:", st["players"]["i1"]["hp"], "before:", hp_before)
    print("rooms[sea_cave_1]=", json.dumps(st.get("rooms", {}).get("sea_cave_1"), ensure_ascii=False)[:300])

    # clear room 1: explore -> combat -> weaken -> attack until map mode again
    for i in range(8):
        battle = db.get_battle("g1", "i1")
        if not battle:
            print("battle gone at iter", i); break
        stt = battle["state"]
        if stt.get("mode") == "map":
            # check if monsters remain in current room
            rstate = stt.get("rooms", {}).get(stt.get("cur_subarea") or "goblin_camp_1", {})
            # cur_subarea stored under leader? read from player
            p = db.get_player("g1", "i1")
            sa = p.get("cur_subarea")
            rstate = stt.get("rooms", {}).get(sa, {})
            ml = rstate.get("monsters_left") or []
            if not ml:
                print("room cleared at iter", i, "sa=", sa)
                break
            await enter_combat(m, "g1", "i1")
            continue
        weaken(stt)
        db.save_battle("g1", "i1", stt)
        out = await cmd(m, "attack", "g1", stt["members"][stt["turn"]], "攻击")
        # print("attacked:", out[-80:].replace("\n", " | "))

    battle = db.get_battle("g1", "i1")
    st = battle["state"]
    print("== after room1 clear ==")
    p = db.get_player("g1", "i1")
    print("cur_subarea:", p.get("cur_subarea"), "mode:", st.get("mode"), "stage_cleared:", st.get("stage_cleared"))
    print("rooms[sea_cave_1]=", json.dumps(st.get("rooms", {}).get("sea_cave_1"), ensure_ascii=False)[:200])

    # advance to room 2 (sea_cave_2)
    out = await cmd(m, "move", "g1", "i1", "移动 海蚀洞窟·洞窟深处" if False else "移动 2")
    print("== move 2 ==")
    print(out[:400])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
