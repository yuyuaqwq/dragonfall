# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - pois.py（v87 02 章 7.6：探索点 POI 系统）

每个子区域可挂 0-3 个探索点（POI）——玩家『查看』当前子区域时列出，
『探索』有 15% 概率额外触发当前子区域随机 POI（独立判定）。
POI 与 NPC/商店/怪物独立，不占 NPC 位。
"""

POIS = {
    # ---- 城镇 POI（生活气息）----
    "campfire": {
        "name": "篝火", "icon": "🔥",
        "desc": "一堆噼啪作响的篝火，火光照亮周围的空地。",
        "effect": "recover",  # 恢复 30% 生命/魔力 + 随机烹饪食材
    },
    "shrine": {
        "name": "古老神龛", "icon": "🛕",
        "desc": "一座半埋进土里的古老神龛，石像面容模糊。",
        "effect": "buff",  # 随机 buff：攻击/防御/速度 +10% 持续 5 次战斗
    },
    "herb_patch": {
        "name": "草药丛", "icon": "🌿",
        "desc": "一片长势喜人的野生草药，散发着淡淡的药香。",
        "effect": "herb",  # 随机 1-2 份炼金材料
    },
    "loot_pile": {
        "name": "可疑包裹", "icon": "🎁",
        "desc": "路边扔着一个绑着麻绳的包裹，不知道装着什么。",
        "effect": "loot",  # 随机金币 / 图纸 / 陷阱（扣血）——v105 M23 P3-6：v94 经济改革后装备→图纸，注释同步
    },
    "rune_stone": {
        "name": "符文石", "icon": "🪨",
        "desc": "一块刻满符文的古老石碑，符文中似乎蕴含着知识。",
        "effect": "rune",  # 读符文：随机知识（图鉴补全 / 隐藏成就线索）
    },
    # v105 M23 线索类 POI 治理：rune_stone 挂载收敛至 4 个（策划案 02 章种族分布原则，
    # 矮人/龙裔/地底/遗迹 各留代表性 1-2 个）——dragon_ridge_3（龙裔，测试必需）、
    # dwarf_long_gallery_2（矮人）、dragonborn_valley_trail_3（龙裔）、hill_mine_3（地底）。
    "fishing_spot": {
        "name": "鱼群聚集", "icon": "🐟",
        "desc": "水面泛起细密的涟漪，一大群鱼正聚在水面下。",
        "effect": "fish",  # 立即获得 1 次免费垂钓机会（不耗次数）
    },
    "note": {
        "name": "神秘字条", "icon": "📜",
        "desc": "一张钉在树干上的字条，墨迹已经有些褪色。",
        "effect": "note",  # 收集线索（H6 书页/H7 信标前置）
    },
    # v105 M23 线索类 POI 治理：note 挂载收敛至 4 个（策划案 02 章种族分布原则）——
    # cinder_mountain_3（H7 灰烬回廊前置链功能保留，老守墓人·灰须在烬山）、
    # old_battlefield_3 / dawn_cathedral_3（遗迹）、abyss_altar_3（地底·深渊）。
    # ---- v87.9 风景 POI（探索触发，纯氛围）----
    "scenic_view": {
        "name": "观景台", "icon": "🏞️",
        "desc": "一块探出山崖的天然平台，视野豁然开朗。",
        "effect": "sight",  # 探索触发：一段风景描写（纯 flavor）
    },
    "ancient_tree_sight": {
        "name": "古木参天", "icon": "🌳",
        "desc": "一株盘根错节的老树，树冠几乎遮蔽了半边天空。",
        "effect": "sight",
    },
    "star_gazing": {
        "name": "星野", "icon": "🌌",
        "desc": "夜空澄澈如洗，繁星低垂，仿佛伸手就能摘下。",
        "effect": "sight",
    },
    # ---- v115 探索体验扩容：新 POI +7（33 号文档 §5.1）----
    "merchant_camp": {
        "name": "行商营地", "icon": "🧺",
        "desc": "一处支着布棚的行商营地，货物还热乎着。",
        "effect": "merchant",  # 触发一次流浪商人式优惠购买（金币/图纸，不强卖）——由 _handle_poi 结算
    },
    "ancient_altar": {
        "name": "古老祭坛", "icon": "🗿",
        "desc": "一座爬满藤蔓的古老祭坛，石台上残留着香火痕迹。",
        "effect": "buff",  # 随机 buff（同 shrine：+10% 持续 5 战）
    },
    "bird_nest": {
        "name": "高悬鸟巢", "icon": "🪺",
        "desc": "树杈间挂着一只精巧的鸟巢，几片绒羽随风飘落。",
        "effect": "herb",  # 随机 1-2 份材料（羽毛/蛋/草药）
    },
    "ice_sculpture": {
        "name": "天然冰雕", "icon": "🧊",
        "desc": "寒风把冰雪雕琢成奇形怪状的雕塑，在暮色里泛着幽蓝的光。",
        "effect": "sight",  # 北境风景 POI（纯 flavor）
    },
    "dragon_bone": {
        "name": "远古龙骸", "icon": "🦴",
        "desc": "半埋在山岩里的巨大龙骨，肋骨间卡着什么东西在发光。",
        "effect": "loot",  # 东境专属：随机金币/龙系材料
    },
    "shipwreck": {
        "name": "沉船残骸", "icon": "⛵",
        "desc": "一艘搁浅的旧船斜插在礁石间，舱门半开。",
        "effect": "loot",  # 海域专属：金币/航海材料
    },
    "traveler_grave": {
        "name": "旅者之墓", "icon": "🪦",
        "desc": "一座无名墓碑，碑前放着半枯的花环。",
        "effect": "note",  # 见闻 flag：grave_{map}，第一次触发记 flag（低概率 lore）——_handle_poi 区分
    },
}

# 子区域 → POI 分配（key = "地图id:子区域id"，value = poi id 列表）
# 子区域 ID 为 map_N 数字格式（map_1=入口/广场，map_3=深处）
# v105 M23 线索类 POI 治理（61→8，策划案 02 章限 8 个·种族分布原则）：
#   note/rune_stone 仅保留 8 个挂载——矮人/龙裔/地底/遗迹 各 1-2 个代表性 + 功能必需项：
#   矮人: dwarf_long_gallery_2(rune) | 龙裔: dragon_ridge_3(rune,必需)/dragonborn_valley_trail_3(rune)
#   地底: hill_mine_3(rune)/abyss_altar_3(note) | 遗迹: old_battlefield_3(note)/dawn_cathedral_3(note)
#   功能必需: cinder_mountain_3(note, H7 灰烬回廊线索链) + dragon_ridge_3（7 重点子区域共存测试）
SUBAREA_POIS = {
    # ==== 绿野·橡木镇 ====
    "oak_town:oak_town_1": ["shrine", "campfire"],   # 冒险者广场
    # ==== 白鹿城 ====
    "white_deer:white_deer_1": ["shrine"],            # 白鹿广场
    "white_deer:white_deer_5": ["herb_patch", "loot_pile"],  # 南市
    # ==== 铁港城 ====
    "ironharbor:ironharbor_1": ["fishing_spot", "loot_pile"],  # 港口广场
    "ironharbor:ironharbor_5": ["fishing_spot"],       # 东码头
    # ==== 晨曦城 ====
    "dawn_city:dawn_city_3": ["shrine"],      # 圣光大教堂
    "dawn_city:dawn_city_1": ["loot_pile"],           # 王都广场（南门遗物）
    # ==== 月冠王庭 ====
    "moon_court:moon_court_1": ["shrine"],  # 王庭广场
    # ==== 野外·南境 ====
    "oak_plain:oak_plain_3": ["campfire", "herb_patch", "scenic_view"],  # 草地尽头：远眺丘陵
    "white_deer_forest:white_deer_forest_3": ["campfire"],
    "emerald_forest:emerald_forest_3": ["herb_patch", "ancient_tree_sight"],  # 翡翠森林深处：古木参天
    "misty_swamp:misty_swamp_3": ["loot_pile"],
    "hill_mine:hill_mine_3": ["rune_stone", "loot_pile"],
    # ==== 野外·中域 ====
    "gold_plain:gold_plain_2": ["campfire", "herb_patch"],
    "silver_river:silver_river_2": ["fishing_spot", "campfire"],
    "old_battlefield:old_battlefield_3": ["note"],
    "dawn_cathedral:dawn_cathedral_3": ["note"],
    # ==== 野外·西境 ====
    "silverwood:silverwood_3": ["shrine", "herb_patch"],
    "starlake:starlake_3": ["fishing_spot", "star_gazing"],  # 星湖：星空倒映
    # ==== 野外·北境 ====
    "frost_field:frost_field_3": ["campfire", "loot_pile", "scenic_view"],  # 霜原：雪线远眺
    "cinder_mountain:cinder_mountain_3": ["note", "star_gazing"],  # 烬山：夜观星火（H7 灰烬回廊线索）
    "black_forest:black_forest_3": ["loot_pile"],
    # ==== 野外·东境 ====
    "dragon_ridge:dragon_ridge_3": ["rune_stone", "scenic_view"],  # 龙脊：群山之巅
    # ==== 外域 ====
    "coral_reef:coral_reef_3": ["fishing_spot", "loot_pile", "scenic_view"],  # 珊瑚礁：海天一线
    "molten_abyss:molten_abyss_3": ["loot_pile"],
    "abyss_altar:abyss_altar_3": ["note"],
    # ==== v87.7 城镇间新图（02 章 13.4.6 通路自然化）====
    "silver_wind_road:silver_wind_road_1": ["loot_pile"],      # 银风道口：被遗落的货箱
    "silver_wind_road:silver_wind_road_2": ["campfire"],  # 银风驿站：商队营地
    "west_ridge_wilds:west_ridge_wilds_1": ["herb_patch"],     # 西岭口：荒原药草
    "mist_tide_passage:mist_tide_passage_2": ["loot_pile"],    # 雾潮中段：漂流残骸
    "dwarf_long_gallery:dwarf_long_gallery_2": ["rune_stone"], # 长廊中段：矮人符文
    "cold_spine_snow_trail:cold_spine_snow_trail_1": ["shrine"],  # 铁砧北门：冰封神龛
    "sky_ladder_path:sky_ladder_path_3": ["shrine"],           # 风翼台：云中神龛
    # ==== v87.9 风景 POI（探索触发，纯氛围）====
    "gold_plain:gold_plain_3": ["star_gazing"],            # 金穗平原：旷野星野
    "sky_ladder_path:sky_ladder_path_1": ["star_gazing", "campfire"],  # 天梯云径：云端星空
    "dragon_ridge_old_road:dragon_ridge_old_road_3": ["scenic_view"],  # 龙脊古道尽头
    "west_ridge_wilds:west_ridge_wilds_3": ["scenic_view"],  # 西岭荒原深处

    'oak_plain:oak_plain_1': ['herb_patch', 'campfire'],
    'oak_plain:oak_plain_2': ['herb_patch', 'campfire'],
    'white_deer_forest:white_deer_forest_1': ['herb_patch', 'campfire'],
    'white_deer_forest:white_deer_forest_2': ['herb_patch', 'campfire'],
    'emerald_forest:emerald_forest_1': ['herb_patch', 'campfire'],
    'emerald_forest:emerald_forest_2': ['herb_patch', 'campfire'],
    'misty_swamp:misty_swamp_1': ['herb_patch', 'loot_pile', 'campfire'],
    'misty_swamp:misty_swamp_2': ['herb_patch', 'fishing_spot'],
    'hill_mine:hill_mine_1': ['loot_pile', 'campfire'],
    'hill_mine:hill_mine_2': ['loot_pile'],
    'harbor_docks:harbor_docks_1': ['fishing_spot', 'loot_pile'],
    'harbor_docks:harbor_docks_2': ['campfire', 'loot_pile'],
    'harbor_docks:harbor_docks_3': ['fishing_spot', 'loot_pile'],
    'silver_valley:silver_valley_1': ['herb_patch', 'campfire'],
    'silver_valley:silver_valley_2': ['fishing_spot', 'herb_patch'],
    'silver_valley:silver_valley_3': ['herb_patch', 'campfire'],
    'windmill_plain:windmill_plain_1': ['campfire', 'loot_pile'],
    'windmill_plain:windmill_plain_2': ['campfire', 'loot_pile'],
    'windmill_plain:windmill_plain_3': ['campfire', 'loot_pile'],
    'rockfall_gorge:rockfall_gorge_1': ['herb_patch', 'campfire'],
    'rockfall_gorge:rockfall_gorge_2': ['herb_patch', 'campfire'],
    'rockfall_gorge:rockfall_gorge_3': ['herb_patch', 'campfire'],
    'boar_ridge:boar_ridge_1': ['campfire'],
    'boar_ridge:boar_ridge_2': ['campfire'],
    'boar_ridge:boar_ridge_3': ['campfire', 'loot_pile'],
    'dawn_cathedral:dawn_cathedral_1': ['shrine', 'campfire'],
    'dawn_cathedral:dawn_cathedral_2': ['campfire', 'loot_pile'],
    'gold_plain:gold_plain_1': ['campfire', 'loot_pile'],
    'white_abbey:white_abbey_1': ['shrine', 'herb_patch'],
    'white_abbey:white_abbey_2': ['campfire', 'loot_pile'],
    'white_abbey:white_abbey_3': ['campfire', 'loot_pile'],
    'border_castle:border_castle_1': ['campfire', 'loot_pile'],
    'border_castle:border_castle_2': ['campfire', 'loot_pile'],
    'border_castle:border_castle_3': ['campfire', 'loot_pile'],
    'silver_river:silver_river_1': ['fishing_spot', 'herb_patch'],
    'silver_river:silver_river_3': ['fishing_spot', 'herb_patch'],
    'knight_yard:knight_yard_1': ['campfire', 'loot_pile'],
    'knight_yard:knight_yard_2': ['campfire', 'loot_pile'],
    'knight_yard:knight_yard_3': ['campfire', 'loot_pile'],
    'king_road:king_road_1': ['campfire', 'loot_pile'],
    'king_road:king_road_2': ['campfire', 'loot_pile'],
    'king_road:king_road_3': ['shrine'],
    'ironshield_hills:ironshield_hills_1': ['shrine', 'campfire'],
    'ironshield_hills:ironshield_hills_2': ['shrine'],
    'ironshield_hills:ironshield_hills_3': ['shrine'],
    'old_battlefield:old_battlefield_1': ['loot_pile'],
    'old_battlefield:old_battlefield_2': ['campfire', 'loot_pile'],
    'silverwood:silverwood_1': ['fishing_spot', 'loot_pile', 'campfire'],
    'silverwood:silverwood_2': ['fishing_spot', 'loot_pile'],
    'starlake:starlake_1': ['fishing_spot', 'shrine', 'campfire'],
    'starlake:starlake_2': ['fishing_spot', 'shrine'],
    'ancient_tree:ancient_tree_1': ['campfire'],
    'ancient_tree:ancient_tree_2': ['herb_patch', 'campfire'],
    'moon_glade:moon_glade_1': ['herb_patch', 'campfire'],
    'moon_glade:moon_glade_2': ['campfire', 'loot_pile'],
    'moon_glade:moon_glade_3': ['herb_patch', 'campfire'],
    'emerald_valley:emerald_valley_1': ['herb_patch', 'campfire'],
    'emerald_valley:emerald_valley_2': ['herb_patch', 'campfire'],
    'emerald_valley:emerald_valley_3': ['herb_patch', 'campfire'],
    'windvale:windvale_1': ['herb_patch', 'campfire'],
    'windvale:windvale_2': ['herb_patch', 'campfire'],
    'windvale:windvale_3': ['herb_patch', 'campfire'],
    'moonshadow_wood:moonshadow_wood_1': ['herb_patch', 'campfire'],
    'moonshadow_wood:moonshadow_wood_2': ['campfire', 'loot_pile'],
    'moonshadow_wood:moonshadow_wood_3': ['campfire', 'loot_pile'],
    'frost_field:frost_field_1': ['campfire', 'shrine'],
    'frost_field:frost_field_2': ['campfire', 'shrine'],
    'forge_valley:forge_valley_1': ['herb_patch', 'campfire'],
    'forge_valley:forge_valley_2': ['fishing_spot', 'herb_patch'],
    'forge_valley:forge_valley_3': ['campfire', 'loot_pile'],
    'black_forest:black_forest_1': ['herb_patch', 'campfire'],
    'black_forest:black_forest_2': ['herb_patch', 'campfire'],
    'cinder_mountain:cinder_mountain_1': ['campfire'],
    'cinder_mountain:cinder_mountain_2': ['campfire'],
    'frost_fang:frost_fang_1': ['herb_patch', 'campfire'],
    'frost_fang:frost_fang_2': ['campfire', 'shrine'],
    'frost_fang:frost_fang_3': ['campfire', 'shrine'],
    'winter_lake:winter_lake_1': ['fishing_spot', 'shrine'],
    'winter_lake:winter_lake_2': ['campfire', 'shrine'],
    'winter_lake:winter_lake_3': ['fishing_spot', 'shrine'],
    'permafrost_field:permafrost_field_1': ['campfire', 'shrine'],
    'permafrost_field:permafrost_field_2': ['campfire', 'shrine'],
    'permafrost_field:permafrost_field_3': ['campfire', 'shrine'],
    'frostwhisper_canyon:frostwhisper_canyon_1': ['herb_patch', 'campfire'],
    'frostwhisper_canyon:frostwhisper_canyon_2': ['herb_patch', 'campfire'],
    'frostwhisper_canyon:frostwhisper_canyon_3': ['campfire', 'shrine'],
    'dragon_ridge:dragon_ridge_1': ['campfire'],
    'dragon_ridge:dragon_ridge_2': ['campfire'],
    'dragon_roost:dragon_roost_1': ['campfire', 'loot_pile'],
    'dragon_roost:dragon_roost_2': ['campfire', 'loot_pile'],
    'dragon_roost:dragon_roost_3': ['campfire', 'loot_pile'],
    'ancient_battlefield:ancient_battlefield_1': ['loot_pile', 'campfire'],
    'ancient_battlefield:ancient_battlefield_2': ['loot_pile'],
    'bone_wild:bone_wild_1': ['campfire', 'loot_pile'],
    'bone_wild:bone_wild_2': ['campfire', 'loot_pile'],
    'bone_wild:bone_wild_3': ['campfire', 'loot_pile'],
    'storm_cliff:storm_cliff_1': ['scenic_view', 'campfire'],
    'storm_cliff:storm_cliff_2': ['scenic_view', 'campfire'],
    'storm_cliff:storm_cliff_3': ['scenic_view', 'campfire'],
    'redridge_plateau:redridge_plateau_1': ['scenic_view'],
    'redridge_plateau:redridge_plateau_2': ['campfire', 'loot_pile'],
    'redridge_plateau:redridge_plateau_3': ['scenic_view'],
    'dragonsfall_valley:dragonsfall_valley_1': ['herb_patch', 'campfire'],
    'dragonsfall_valley:dragonsfall_valley_2': ['campfire', 'loot_pile'],
    'dragonsfall_valley:dragonsfall_valley_3': ['herb_patch', 'campfire'],
    'coral_reef:coral_reef_1': ['fishing_spot', 'loot_pile'],
    'coral_reef:coral_reef_2': ['campfire', 'loot_pile'],
    'sunset_isle:sunset_isle_1': ['fishing_spot', 'loot_pile'],
    'sunset_isle:sunset_isle_2': ['herb_patch', 'campfire'],
    'sunset_isle:sunset_isle_3': ['campfire', 'loot_pile'],
    'storm_strait:storm_strait_1': ['fishing_spot', 'loot_pile'],
    'storm_strait:storm_strait_2': ['campfire', 'loot_pile'],
    'storm_strait:storm_strait_3': ['fishing_spot', 'loot_pile'],
    'mermaid_bay:mermaid_bay_1': ['fishing_spot', 'loot_pile', 'campfire'],
    'mermaid_bay:mermaid_bay_2': ['fishing_spot', 'loot_pile'],
    'mermaid_bay:mermaid_bay_3': ['fishing_spot', 'loot_pile'],
    'mist_trench:mist_trench_1': ['fishing_spot', 'loot_pile', 'campfire'],
    'mist_trench:mist_trench_2': ['loot_pile', 'herb_patch'],
    'mist_trench:mist_trench_3': ['fishing_spot', 'loot_pile'],
    'whale_domain:whale_domain_1': ['fishing_spot', 'loot_pile'],
    'whale_domain:whale_domain_2': ['campfire', 'loot_pile'],
    'whale_domain:whale_domain_3': ['fishing_spot', 'loot_pile'],
    'shipwreck_graveyard:shipwreck_graveyard_1': ['shrine'],
    'shipwreck_graveyard:shipwreck_graveyard_2': ['campfire', 'loot_pile'],
    'shipwreck_graveyard:shipwreck_graveyard_3': ['shrine'],
    'storm_sea:storm_sea_1': ['fishing_spot', 'loot_pile'],
    'storm_sea:storm_sea_2': ['scenic_view', 'campfire'],
    'fungus_forest:fungus_forest_1': ['herb_patch', 'campfire'],
    'fungus_forest:fungus_forest_2': ['campfire', 'loot_pile'],
    'fungus_forest:fungus_forest_3': ['herb_patch', 'campfire'],
    'deep_lake:deep_lake_1': ['fishing_spot', 'shrine', 'campfire'],
    'deep_lake:deep_lake_2': ['fishing_spot', 'shrine'],
    'deep_lake:deep_lake_3': ['fishing_spot', 'shrine'],
    'molten_abyss:molten_abyss_1': ['loot_pile', 'campfire'],
    'molten_abyss:molten_abyss_2': ['loot_pile'],
    'lava_bed:lava_bed_1': ['fishing_spot', 'herb_patch', 'campfire'],
    'lava_bed:lava_bed_2': ['fishing_spot', 'loot_pile'],
    'lava_bed:lava_bed_3': ['fishing_spot', 'herb_patch'],
    'abyss_altar:abyss_altar_1': ['shrine', 'campfire'],
    'abyss_altar:abyss_altar_2': ['shrine'],
    'cloud_sea:cloud_sea_1': ['fishing_spot', 'loot_pile', 'campfire'],
    'cloud_sea:cloud_sea_2': ['star_gazing', 'scenic_view'],
    'cloud_sea:cloud_sea_3': ['fishing_spot', 'loot_pile'],
    'storm_plateau:storm_plateau_1': ['scenic_view', 'campfire'],
    'storm_plateau:storm_plateau_2': ['scenic_view'],
    'storm_plateau:storm_plateau_3': ['scenic_view'],
    'rainbow_cloud:rainbow_cloud_1': ['herb_patch', 'campfire'],
    'rainbow_cloud:rainbow_cloud_2': ['star_gazing', 'scenic_view'],
    'rainbow_cloud:rainbow_cloud_3': ['herb_patch', 'campfire'],
    'starlight_terrace:starlight_terrace_1': ['scenic_view', 'campfire'],
    'starlight_terrace:starlight_terrace_2': ['star_gazing', 'scenic_view'],
    'starlight_terrace:starlight_terrace_3': ['star_gazing', 'scenic_view'],
    'west_ridge_wilds:west_ridge_wilds_2': ['campfire', 'loot_pile'],
    'dusk_ridge_road:dusk_ridge_road_1': ['campfire'],
    'dusk_ridge_road:dusk_ridge_road_3': ['campfire', 'loot_pile'],
    'mist_tide_passage:mist_tide_passage_1': ['fishing_spot', 'loot_pile'],
    'mist_tide_passage:mist_tide_passage_3': ['campfire', 'loot_pile'],
    'black_tide_strait:black_tide_strait_1': ['fishing_spot', 'loot_pile'],
    'black_tide_strait:black_tide_strait_2': ['campfire', 'loot_pile'],
    'dwarf_long_gallery:dwarf_long_gallery_1': ['campfire', 'loot_pile'],
    'dwarf_long_gallery:dwarf_long_gallery_3': ['campfire', 'loot_pile'],
    'cold_spine_snow_trail:cold_spine_snow_trail_2': ['campfire', 'shrine'],
    'cold_spine_snow_trail:cold_spine_snow_trail_3': ['scenic_view', 'campfire'],
    'dragon_ridge_old_road:dragon_ridge_old_road_1': ['campfire', 'loot_pile'],
    'dragonborn_valley_trail:dragonborn_valley_trail_1': ['campfire', 'loot_pile'],
    'dragonborn_valley_trail:dragonborn_valley_trail_2': ['herb_patch', 'campfire'],
    'dragonborn_valley_trail:dragonborn_valley_trail_3': ['rune_stone', 'campfire'],
    'sky_ladder_path:sky_ladder_path_2': ['star_gazing', 'scenic_view'],
    # ==== v115 探索体验扩容：新 POI 挂载（33 号文档 §5.2）====
    # 线索治理延续既有原则：traveler_grave 为见闻 flag 型 note（非线索收集），此处为地底/荒野见闻，未纳入 8 个线索挂载配额。
    # ---- merchant_camp：南境 2-3 处 + 中域 1 处 ----
    "oak_plain:oak_plain_2": ["merchant_camp", "herb_patch", "campfire"],   # 橡木平原深处旁：行商路边营地
    "oak_plain:oak_plain_3": ["merchant_camp", "herb_patch", "scenic_view"],  # 草地尽头：行商歇脚
    "gold_plain:gold_plain_3": ["merchant_camp", "star_gazing"],          # 中域金穗平原：旷野市集
    # ---- ancient_altar：中域 1-2 处 + 地底 1 处 ----
    "gold_plain:gold_plain_2": ["ancient_altar", "campfire", "herb_patch"],  # 金穗平原中段：古祭坛
    "deep_lake:deep_lake_2": ["ancient_altar", "fishing_spot", "shrine"],  # 地底深湖：水畔古祭坛
    # ---- bird_nest：西境 2 处 + 南境森林 1 处 ----
    "silverwood:silverwood_2": ["bird_nest", "fishing_spot", "loot_pile"],  # 银木林深处：高枝鸟巢
    "starlake:starlake_2": ["bird_nest", "fishing_spot", "shrine"],      # 星湖：林缘鸟巢
    "emerald_forest:emerald_forest_2": ["bird_nest", "herb_patch", "campfire"],  # 翡翠森林中段：鸟巢
    # ---- ice_sculpture：北境 3 处 ----
    "frost_field:frost_field_1": ["ice_sculpture", "campfire", "shrine"],  # 霜原入口：冰雕奇观
    "frost_field:frost_field_2": ["ice_sculpture", "campfire", "shrine"],  # 霜原中段：天然冰雕
    "permafrost_field:permafrost_field_2": ["ice_sculpture", "campfire", "shrine"],  # 永冻原：暮色冰雕
    # ---- dragon_bone：东境 2 处 ----
    "dragon_ridge:dragon_ridge_1": ["dragon_bone", "campfire"],          # 龙脊入口：半埋龙骨
    "bone_wild:bone_wild_2": ["dragon_bone", "campfire", "loot_pile"],   # 骨野：巨大龙骸
    # ---- shipwreck：海域 2 处 ----
    "coral_reef:coral_reef_1": ["shipwreck", "fishing_spot", "loot_pile"],  # 珊瑚礁：搁浅旧船
    "storm_sea:storm_sea_2": ["shipwreck", "scenic_view", "campfire"],  # 风暴海：斜插礁石的沉船
    # ---- traveler_grave：地底/荒野 2 处 ----
    "misty_swamp:misty_swamp_1": ["traveler_grave", "herb_patch", "loot_pile", "campfire"],  # 迷雾沼泽入口：无名墓碑
    "molten_abyss:molten_abyss_1": ["traveler_grave", "loot_pile", "campfire"],  # 熔渊入口：荒原孤墓
}

# 随机线索 POI 文案池（note 效果：线索收集）
NOTE_POOL = [
    "纸条上写着：『三页旧纸，一扇石门——书页不齐，石门不开。』(失落图书馆线索)",
    "纸条上写着：『烬山深处，火光不灭。守墓人知道那扇门在哪。』(灰烬回廊线索)",
    "纸条上写着：『夜晚的城镇，有人高价收材料——只收识货人。』(夜行者商人线索)",
]

# 符文石知识池（rune 效果：图鉴补全/隐藏线索）
RUNE_POOL = [
    "符文在光芒中浮现：『黄金史莱姆只在最普通的草地出没，但极其罕见。』(图鉴线索)",
    "符文在光芒中浮现：『白鹿王只会在月光下的森林现身。』(图鉴线索)",
    "符文在光芒中浮现：『符文魔像守护着失落的图书馆。』(隐藏区域线索)",
    "符文在光芒中浮现：『暗影猎手喜欢在深夜捕猎。』(图鉴线索)",
]

# v87.9 风景描写池（sight 效果：探索触发的纯氛围观景）
SIGHT_POOL = [
    "你站在这处风景前，山风拂过面颊。远处的山峦在暮色中勾勒出深蓝色的剪影，像一幅泼墨的画卷。",
    "天地在这里豁然开朗。你忽然明白，为什么无数冒险者愿意为了这一刻的风景，走这么远的路。",
    "你静静地看了一会儿。这一刻没有敌人、没有任务，只有风声、光影，和你微微发烫的心跳。",
    "日落的光把整片大地染成金色，你眯起眼睛，把这幅画面刻进记忆里。旅程漫长，但值得。",
    "你俯身看了看脚下的世界——有人在这片土地上生活、战斗、相爱、死去，而你正走在他们的脚印里。",
]
