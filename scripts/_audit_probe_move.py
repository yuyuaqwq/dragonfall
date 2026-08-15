# -*- coding: utf-8 -*-
import sys, asyncio, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))
from conftest import FakeEvent, run, clean_db, Main, db, make_player, C

async def main():
    clean_db(); db.init_db()
    m = Main(None)
    make_player("g1", "1001", "甲", "战士", level=10)
    db.update_player("g1", "1001", cur_map="oak_plain", cur_subarea="oak_plain_1")
    async def move(dest):
        ev = FakeEvent("g1", "1001", f"前往 {dest}")
        return "".join(str(x) for x in await run(m.move, ev))
    def pos():
        p = db.get_player("g1", "1001")
        return f"{p['cur_map']}:{p['cur_subarea']}"
    print("start", pos())
    print("links@entry", C.subarea_links("oak_plain", "oak_plain_1"))
    r = await move("3")
    print("after move3 pos", pos())
    print("msg:", (r or "")[:120].replace("\n"," | "))
    print("neighbors oak_plain:", C.MAP_CONNECTIONS.get("oak_plain"))
    print("exit_sa oak_plain:", C.map_exit_subarea("oak_plain"))

asyncio.run(main())
