# -*- coding: utf-8 -*-
"""Probe: investigate a chest in v137 dungeon and dump battle state structure."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, Main, FakeEvent, run

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "i1", "注册 战士 队长 男")
    db.update_player("g1", "i1", level=70, gold=100000, cur_map="dawn_city", hp=500, max_hp=500)
    out = await cmd(m, "instance_cmd", "g1", "i1", "副本 哥布林营地")
    print("== 开本输出 ==")
    print(out[:800])
    st = db.get_battle("g1", "i1")["state"]
    print("== rooms ==")
    print(json.dumps(st.get("rooms"), ensure_ascii=False, indent=1)[:1500])
    print("== resources_pool ==")
    print(json.dumps(st.get("resources_pool"), ensure_ascii=False)[:600])
    print("== stage_pois ==")
    print(json.dumps(st.get("stage_pois"), ensure_ascii=False)[:400])
    print("== cur_subarea / player ==")
    p = db.get_player("g1", "i1")
    print(f"cur_map={p['cur_map']} cur_subarea={p.get('cur_subarea')}")
    print("== stage_pending / stage_idx / mode ==")
    print(st.get("stage_idx"), st.get("mode"), st.get("stage_pending"))
    print("== POI mount for goblin_camp_1 ==")
    print(C.subarea_pois("goblin_camp", "goblin_camp_1"))
    for pid in C.subarea_pois("goblin_camp", "goblin_camp_1"):
        print(" ", pid, "->", C.POIS.get(pid, {}).get("name"), C.POIS.get(pid, {}).get("type"))

    # now investigate the chest
    out = await cmd(m, "instance_investigate", "g1", "i1", "调查 生锈的铁箱")
    print("== 调查输出 ==")
    print(out[:500])
    st = db.get_battle("g1", "i1")["state"]
    print("== after: rooms[goblin_camp_1] ==")
    print(json.dumps(st.get("rooms", {}).get("goblin_camp_1"), ensure_ascii=False)[:600])
    print("== after: resources_pool ==")
    print(json.dumps(st.get("resources_pool"), ensure_ascii=False)[:600])
    print("== after: stage_pois ==")
    print(json.dumps(st.get("stage_pois"), ensure_ascii=False)[:600])
    print("== after: gold ==")
    print(db.get_player("g1", "i1")["gold"])

    # investigate again
    out = await cmd(m, "instance_investigate", "g1", "i1", "调查 生锈的铁箱")
    print("== 二次调查输出 ==")
    print(out[:300])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
