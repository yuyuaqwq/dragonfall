# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:/Users/yuyu/qqbot")
sys.path.insert(0, r"C:/Users/yuyu/qqbot/data/plugins/dragonfall")
from data.plugins.dragonfall.game.data import SUBAREAS, SUBAREA_LINKS_INDEX, MAP_BY_ID
sas = SUBAREAS["oak_plain"]
print("=== oak_plain subareas ===")
for s in sas:
    print(f"  {s['id']}: name={s.get('name')} type={s.get('type')} hidden={s.get('hidden')} reveal={s.get('reveal')} lv={s.get('lv')}")
print("=== mesh links ===")
for k, v in SUBAREA_LINKS_INDEX.get("oak_plain", {}).items():
    print(f"  {k} -> {v}")
m = MAP_BY_ID["oak_plain"]
print("map lv", m.get("lv"), "region", m.get("region"))
