# -*- coding: utf-8 -*-
"""v115 文档同步辅助：按实际数据输出 02 章 §六 各野外图的房间列表（一次性工具）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.data import SUBAREAS
from game.data.maps import MAP_BY_ID

order = [
    # 6.1 南境
    'oak_plain', 'white_deer_forest', 'emerald_forest', 'misty_swamp', 'silver_wind_road',
    'harbor_docks', 'silver_valley', 'windmill_plain', 'rockfall_gorge', 'boar_ridge', 'hill_mine',
    # 6.2 中域
    'silver_river', 'gold_plain', 'white_abbey', 'ironshield_hills', 'old_battlefield',
    'border_castle', 'king_road', 'knight_yard', 'dawn_cathedral', 'west_ridge_wilds', 'dusk_ridge_road',
    # 6.3 西境
    'silverwood', 'emerald_valley', 'starlake', 'moon_glade', 'moonshadow_wood', 'ancient_tree', 'windvale',
    # 6.4 北境
    'frost_field', 'forge_valley', 'black_forest', 'cinder_mountain', 'frost_fang', 'winter_lake',
    'permafrost_field', 'frostwhisper_canyon', 'cold_spine_snow_trail',
    # 6.5 东境
    'dragon_ridge_old_road', 'dragon_ridge', 'dragon_roost', 'bone_wild', 'ancient_battlefield',
    'storm_cliff', 'redridge_plateau', 'dragonsfall_valley', 'dragonborn_valley_trail',
    # 6.6 外域
    'coral_reef', 'sunset_isle', 'storm_strait', 'mermaid_bay', 'mist_trench', 'whale_domain',
    'shipwreck_graveyard', 'storm_sea', 'mist_tide_passage', 'black_tide_strait', 'fungus_forest',
    'deep_lake', 'molten_abyss', 'lava_bed', 'abyss_altar', 'sky_ladder_path', 'cloud_sea',
    'storm_plateau', 'rainbow_cloud', 'starlight_terrace',
]

for mid in order:
    m = MAP_BY_ID.get(mid)
    sas = SUBAREAS.get(mid, [])
    if not m or not sas:
        print(f"⚠ {mid}: NOT FOUND")
        continue
    rooms = []
    for s in sas:
        name = s.get("name", "?")
        lv = s.get("lv", "")
        hid = "🔒" if s.get("hidden") else ""
        rooms.append(f"{hid}{name}({lv})")
    print(f"| {m['name']} {mid} | {' / '.join(rooms)} |")
