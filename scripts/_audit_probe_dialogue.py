# -*- coding: utf-8 -*-
import sys, os, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))
from conftest import C, db, clean_db, Main, FakeEvent, run

async def main():
    clean_db(); db.init_db()
    m = Main(None)
    # find where npc_mayor lives
    for mid, mm in C.MAP_BY_ID.items():
        if mid == "oak_town":
            print("oak_town subareas:", [(s['id'], s.get('name')) for s in mm.get('subareas', [])])
            for sa in mm.get('subareas', []):
                if 'npc_mayor' in (sa.get('npcs') or []):
                    print("  mayor at subarea", sa['id'], sa.get('name'))
            print("  map-level npcs:", mm.get('npcs', []))
    # Simulate the test #51 state
    from conftest import make_player
    make_player("g1", "1001", "甲", "战士", level=5)
    db.update_player("g1", "1001", cur_map="oak_town", cur_subarea="oak_town_4")
    ev = FakeEvent("g1", "1001", "找 镇长")
    out = "".join(str(x) for x in await run(m.find_npc, ev))
    print("FIND 镇长 at oak_town_4 ->", out[:200])
    db.update_player("g1", "1001", cur_map="ironharbor", cur_subarea="ironharbor_1")
    ev = FakeEvent("g1", "1001", "找 城主")
    out = "".join(str(x) for x in await run(m.find_npc, ev))
    print("FIND 城主 at ironharbor_1 ->", out[:200])

asyncio.run(main())
