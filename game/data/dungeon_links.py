# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - dungeon_links.py（v137 副本地图化·房间连通表）

为 22 个副本的子区域（多房间）定义房间连通表 SUBAREA_LINKS，
供玩家在副本内使用『移动』指令往返探索。由 _assembly.py 装配进
SUBAREA_LINKS_INDEX。

设计原则（与 mesh_rooms_*.py 一致）：
  - 双向对称（a 连 b 则 b 连 a）
  - 主链必通：入口 → 房间2 → ... → Boss 房，可来回走
  - 4-6 房副本加 1 条岔路/捷径（入口直达深处 / 中间房互通）
  - 无出口：只连副本内部房间，不连外部地图
  - Boss 房（最后房间）只连倒数第 2 房（死胡同，打完即通关）
  - 相邻房间等级差 <= 15（等级数据已配好，均满足）
"""
# ---------------------------------------------------------------------------
# SUBAREA_LINKS：副本房间连通表
# key = 地图id, value = {子区域id: [可达子区域id列表]}
# ---------------------------------------------------------------------------
SUBAREA_LINKS = {
    # =================== 中小副本（3 房，纯链状） ===================
    "goblin_camp": {
        "goblin_camp_1": ["goblin_camp_2"],
        "goblin_camp_2": ["goblin_camp_1", "goblin_camp_3"],
        "goblin_camp_3": ["goblin_camp_2"],  # Boss-酋长帐篷
    },
    "sea_cave": {
        "sea_cave_1": ["sea_cave_2"],
        "sea_cave_2": ["sea_cave_1", "sea_cave_3"],
        "sea_cave_3": ["sea_cave_2"],  # Boss-藏宝密室
    },
    "deer_fort": {
        "deer_fort_1": ["deer_fort_2"],
        "deer_fort_2": ["deer_fort_1", "deer_fort_3"],
        "deer_fort_3": ["deer_fort_2"],  # Boss-要塞主厅
    },
    "old_king_tomb": {
        "old_king_tomb_1": ["old_king_tomb_2"],
        "old_king_tomb_2": ["old_king_tomb_1", "old_king_tomb_3"],
        "old_king_tomb_3": ["old_king_tomb_2"],  # Boss-王座厅
    },
    "secret_crypt": {
        "secret_crypt_1": ["secret_crypt_2"],
        "secret_crypt_2": ["secret_crypt_1", "secret_crypt_3"],
        "secret_crypt_3": ["secret_crypt_2"],  # Boss-枢机密室
    },
    "holy_trial": {
        "holy_trial_1": ["holy_trial_2"],
        "holy_trial_2": ["holy_trial_1", "holy_trial_3"],
        "holy_trial_3": ["holy_trial_2"],  # Boss-圣光竞技场
    },
    "elven_ruins": {
        "elven_ruins_1": ["elven_ruins_2"],
        "elven_ruins_2": ["elven_ruins_1", "elven_ruins_3"],
        "elven_ruins_3": ["elven_ruins_2"],  # Boss-精灵王座
    },
    "moon_temple": {
        "moon_temple_1": ["moon_temple_2"],
        "moon_temple_2": ["moon_temple_1", "moon_temple_3"],
        "moon_temple_3": ["moon_temple_2"],  # Boss-月神圣殿
    },
    "sunken_ship": {
        "sunken_ship_1": ["sunken_ship_2"],
        "sunken_ship_2": ["sunken_ship_1", "sunken_ship_3"],
        "sunken_ship_3": ["sunken_ship_2"],  # Boss-船长室
    },
    "siren_nest": {
        "siren_nest_1": ["siren_nest_2"],
        "siren_nest_2": ["siren_nest_1", "siren_nest_3"],
        "siren_nest_3": ["siren_nest_2"],  # Boss-珍珠王座
    },
    "sea_god_temple": {
        "sea_god_temple_1": ["sea_god_temple_2"],
        "sea_god_temple_2": ["sea_god_temple_1", "sea_god_temple_3"],
        "sea_god_temple_3": ["sea_god_temple_2"],  # Boss-海神祭坛
    },
    "deep_dragon_palace": {
        "deep_dragon_palace_1": ["deep_dragon_palace_2"],
        "deep_dragon_palace_2": ["deep_dragon_palace_1", "deep_dragon_palace_3"],
        "deep_dragon_palace_3": ["deep_dragon_palace_2"],  # Boss-龙王大殿
    },

    # =================== 次顶级副本（4 房，主链+1 捷径） ===================
    "ash_temple": {
        "ash_temple_1": ["ash_temple_2", "ash_temple_3"],  # 捷径-直通熔火厅
        "ash_temple_2": ["ash_temple_1", "ash_temple_3"],
        "ash_temple_3": ["ash_temple_1", "ash_temple_2", "ash_temple_4"],
        "ash_temple_4": ["ash_temple_3"],  # Boss-封印之殿
    },
    "frost_throne": {
        "frost_throne_1": ["frost_throne_2", "frost_throne_3"],  # 捷径-直通永冻大厅
        "frost_throne_2": ["frost_throne_1", "frost_throne_3"],
        "frost_throne_3": ["frost_throne_1", "frost_throne_2", "frost_throne_4"],
        "frost_throne_4": ["frost_throne_3"],  # Boss-冰霜王座
    },
    "under_dragon": {
        "under_dragon_1": ["under_dragon_2", "under_dragon_3"],  # 捷径-直通熔岩通道
        "under_dragon_2": ["under_dragon_1", "under_dragon_3"],
        "under_dragon_3": ["under_dragon_1", "under_dragon_2", "under_dragon_4"],
        "under_dragon_4": ["under_dragon_3"],  # Boss-岩浆龙巢
    },

    # =================== 次顶级副本（5 房，主链+中间互通） ===================
    "gray_dwarf": {
        "gray_dwarf_1": ["gray_dwarf_2"],
        "gray_dwarf_2": ["gray_dwarf_1", "gray_dwarf_3", "gray_dwarf_4"],  # 岔路-直通锻造大厅
        "gray_dwarf_3": ["gray_dwarf_2", "gray_dwarf_4"],
        "gray_dwarf_4": ["gray_dwarf_2", "gray_dwarf_3", "gray_dwarf_5"],
        "gray_dwarf_5": ["gray_dwarf_4"],  # Boss-领主大厅
    },
    "storm_throne": {
        "storm_throne_1": ["storm_throne_2"],
        "storm_throne_2": ["storm_throne_1", "storm_throne_3", "storm_throne_4"],  # 岔路-直通雷云殿
        "storm_throne_3": ["storm_throne_2", "storm_throne_4"],
        "storm_throne_4": ["storm_throne_2", "storm_throne_3", "storm_throne_5"],
        "storm_throne_5": ["storm_throne_4"],  # Boss-风暴王座
    },
    "abyss_throne": {
        "abyss_throne_1": ["abyss_throne_2"],
        "abyss_throne_2": ["abyss_throne_1", "abyss_throne_3", "abyss_throne_4"],  # 岔路-直通血祭广场
        "abyss_throne_3": ["abyss_throne_2", "abyss_throne_4"],
        "abyss_throne_4": ["abyss_throne_2", "abyss_throne_3", "abyss_throne_5"],
        "abyss_throne_5": ["abyss_throne_4"],  # Boss-深渊王座
    },

    # =================== 顶级副本（6 房，主链+入口捷径） ===================
    "abyss_gate": {
        "abyss_gate_1": ["abyss_gate_2", "abyss_gate_3"],  # 捷径-直通深渊长廊
        "abyss_gate_2": ["abyss_gate_1", "abyss_gate_3"],
        "abyss_gate_3": ["abyss_gate_1", "abyss_gate_2", "abyss_gate_4"],
        "abyss_gate_4": ["abyss_gate_3", "abyss_gate_5"],
        "abyss_gate_5": ["abyss_gate_4", "abyss_gate_6"],
        "abyss_gate_6": ["abyss_gate_5"],  # Boss-蚀夜之巢
    },
    "dragon_tomb": {
        "dragon_tomb_1": ["dragon_tomb_2", "dragon_tomb_3"],  # 捷径-直通骨堆甬道
        "dragon_tomb_2": ["dragon_tomb_1", "dragon_tomb_3"],
        "dragon_tomb_3": ["dragon_tomb_1", "dragon_tomb_2", "dragon_tomb_4"],
        "dragon_tomb_4": ["dragon_tomb_3", "dragon_tomb_5"],
        "dragon_tomb_5": ["dragon_tomb_4", "dragon_tomb_6"],
        "dragon_tomb_6": ["dragon_tomb_5"],  # Boss-龙眠大殿
    },
    "eye_of_storm": {
        "eye_of_storm_1": ["eye_of_storm_2", "eye_of_storm_3"],  # 捷径-直通风暴回廊
        "eye_of_storm_2": ["eye_of_storm_1", "eye_of_storm_3"],
        "eye_of_storm_3": ["eye_of_storm_1", "eye_of_storm_2", "eye_of_storm_4"],
        "eye_of_storm_4": ["eye_of_storm_3", "eye_of_storm_5"],
        "eye_of_storm_5": ["eye_of_storm_4", "eye_of_storm_6"],
        "eye_of_storm_6": ["eye_of_storm_5"],  # Boss-风暴之眼
    },
    "cloud_sanctum": {
        "cloud_sanctum_1": ["cloud_sanctum_2", "cloud_sanctum_3"],  # 捷径-直通圣殿回廊
        "cloud_sanctum_2": ["cloud_sanctum_1", "cloud_sanctum_3"],
        "cloud_sanctum_3": ["cloud_sanctum_1", "cloud_sanctum_2", "cloud_sanctum_4"],
        "cloud_sanctum_4": ["cloud_sanctum_3", "cloud_sanctum_5"],
        "cloud_sanctum_5": ["cloud_sanctum_4", "cloud_sanctum_6"],
        "cloud_sanctum_6": ["cloud_sanctum_5"],  # Boss-云中圣殿
    },
}
