# -*- coding: utf-8 -*-
import sys, os, random, time
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
    await cmd(m, "register", "g1", "f4", "注册 战士 坦克甲 男")
    await cmd(m, "register", "g1", "f5", "注册 法师 输出乙 男")
    for q in ("f4", "f5"):
        p = db.get_player("g1", q)
        db.update_player("g1", q, level=40, gold=9999, cur_map="king_road", cur_subarea="king_road_3", hp=p["max_hp"], mp=p["max_mp"])
    out = await cmd(m, "party", "g1", "f4", "组队 输出乙")
    print("PARTY:", out[:100])
    db.add_item("g1", "f4", "i_key_old_king", {"name": "王陵钥匙", "type": "钥匙", "stackable": True, "price": 500})
    out = await cmd(m, "instance_cmd", "g1", "f4", "副本 旧王陵")
    print("INSTANCE:", out[:200])
    bt = db.get_battle("g1", "f4")
    if bt:
        st = bt["state"]
        print("mode:", st.get("mode"), "rooms:", list((st.get("rooms") or {}).keys()))
    for i in range(30):
        out = await cmd(m, "explore", "g1", "f4", "探索")
        bt = db.get_battle("g1", "f4")
        if bt is None:
            print(f"  explore{i}: battle=None  out={out[:120]!r}")
            break
        st = bt["state"]
        if st.get("mode") == "battle":
            print(f"  explore{i}: BATTLE mode keys={list(st.keys())}")
            print("    threat:", st.get("threat"))
            print("    players:", {k: {kk: vv for kk, vv in v.items() if kk in ('ct','hp','spd')} for k, v in (st.get('players') or {}).items()})
            print("    enemies ct:", [(e.get('name'), e.get('ct')) for e in (st.get('enemies') or [])])
            break
    else:
        print("no battle after 30 explores")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
