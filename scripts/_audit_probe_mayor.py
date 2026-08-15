# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tests"))
from conftest import C
for nid, npc in C.NPCS.items():
    if "镇长" in (npc.get("name") or "") or "mayor" in nid:
        print("NPC", nid, "name=", npc.get("name"), "map=", npc.get("map"))
for mid, m in C.MAP_BY_ID.items():
    for sa in (m.get("subareas") or []):
        for nid in (sa.get("npcs") or []):
            npc = C.NPCS.get(nid) or {}
            if _n in ((npc.get("name") or "")):
                pass
for mid, m in C.MAP_BY_ID.items():
    if m.get("id") in ("oak_town", "tiegue_town", "aurora_city"):
        pass
# just find mayor locations
print("--- mayor subarea placements ---")
for mid, m in C.MAP_BY_ID.items():
    for sa in (m.get("subareas") or []):
        for nid in (sa.get("npcs") or []):
            npc = C.NPCS.get(nid) or {}
            if "镇长" in (npc.get("name") or ""):
                print(f"  {m.get('id')} sa={sa['id']} name={sa.get('name')} npc={nid} {npc.get('name')}")
    for nid in (m.get("npcs") or []):
        npc = C.NPCS.get(nid) or {}
        if "镇长" in (npc.get("name") or ""):
            print(f"  {m.get('id')} MAP-level npc={nid} {npc.get('name')}")
