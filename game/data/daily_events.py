# -*- coding: utf-8 -*-
"""《奥兰迪亚·余烬纪年》今日奇遇（v115）—— 每日地图修饰数据

DAILY_MAP_EVENTS：key=地图 id（仅 `野外` 类型迁移图），value=当日变体列表。
每天经日期哈希（game/core/daily_events.py::today_map_event）从列表选中一个，
同一天全服一致（参考 roam NPC 的 _day_hash 设计）。

effects 合法键（由 combat.py explore() 消费，详见 design/new_world/33 ... §三）：
  encounter_rate : 探索遇怪率绝对值加成（±0.1 内，空手率 = 0.25-enconder_rate）
  event_chance   : 探索随机事件率绝对值加成（±0.1 内）
  elite_chance   : 精英遭遇率加成（0 - 0.05）
  loot_mult      : 探索金币/材料倍率（1.2 - 1.5）
  mats           : 材料倾向池（事件材料抽取优先命中；必须在 items.py MATERIALS 中存在）

v115 调用方：game/core/daily_events.py → game/commands/combat.py explore() +
              game/commands/world.py 地图面板。
"""
DAILY_MAP_EVENTS = {
    # ================= 新手区 =================
    "oak_plain": [
        {"id": "oak_boar_rush", "name": "野猪暴走", "desc": "野猪群躁动不安，横冲直撞！",
         "effects": {"encounter_rate": 0.10, "elite_chance": 0.04}},
        {"id": "oak_flower_bloom", "name": "花潮盛放", "desc": "遍地野花盛开，药草香弥漫。",
         "effects": {"event_chance": 0.10, "mats": ["草药", "浆果"]}},
        {"id": "oak_fog_veil", "name": "晨雾迷蒙", "desc": "晨雾笼罩平原，视野模糊。",
         "effects": {"loot_mult": 1.5}},
    ],
    "white_deer_forest": [
        {"id": "deer_migration", "name": "鹿群迁徙", "desc": "成群白鹿穿林而过，蹄声如雨。",
         "effects": {"encounter_rate": -0.10, "event_chance": 0.05}},
        {"id": "deer_berry_boom", "name": "浆果大年", "desc": "林间浆果结得又密又亮。",
         "effects": {"event_chance": 0.10, "mats": ["浆果", "草药"]}},
        {"id": "deer_wood_scent", "name": "林间暖阳", "desc": "阳光透过叶隙洒落，猎物纷纷出没。",
         "effects": {"loot_mult": 1.3, "encounter_rate": 0.05}},
    ],
    "emerald_forest": [
        {"id": "emerald_nectar", "name": "蜜源丰沛", "desc": "蜂群忙碌，到处是甜的蜜香。",
         "effects": {"event_chance": 0.10, "mats": ["蜂蜜", "草药"]}},
        {"id": "emerald_predators", "name": "掠食者苏醒", "desc": "阴影里多了一双双眼睛。",
         "effects": {"encounter_rate": 0.10, "elite_chance": 0.04}},
        {"id": "emerald_glade_dust", "name": "萤火微光", "desc": "林间漂浮着点点暖光。",
         "effects": {"loot_mult": 1.3}},
    ],
    "misty_swamp": [
        {"id": "swamp_boiling", "name": "沼气翻涌", "desc": "泥沼咕嘟冒泡，毒雾弥漫。",
         "effects": {"encounter_rate": 0.10, "elite_chance": 0.05}},
        {"id": "swamp_herbalist", "name": "药草洄潮", "desc": "沼泽深处浮出大量珍贵草药根茎。",
         "effects": {"event_chance": 0.10, "mats": ["草药", "浆果"]}},
        {"id": "swamp_calm", "name": "雾散天青", "desc": "雾气难得散开，视野豁然开朗。",
         "effects": {"loot_mult": 1.4}},
    ],
    "hill_mine": [
        {"id": "mine_ore_gush", "name": "矿脉返潮", "desc": "岩壁渗出的矿液闪闪发亮。",
         "effects": {"loot_mult": 1.5, "mats": ["铁矿石"]}},
        {"id": "mine_cave_howl", "name": "洞穴兽啸", "desc": "深处的兽吼此起彼伏。",
         "effects": {"encounter_rate": 0.08, "elite_chance": 0.04}},
        {"id": "mine_vapor", "name": "矿井蒸汽", "desc": "矿道弥漫着温热蒸汽，宝藏若隐若现。",
         "effects": {"event_chance": 0.10}},
    ],
    # ================= 中域 =================
    "gold_plain": [
        {"id": "gold_harvest", "name": "金黄麦田", "desc": "风过麦浪，沙沙作响。",
         "effects": {"event_chance": 0.10, "mats": ["面粉", "浆果"]}},
        {"id": "gold_warband", "name": "游骑突袭", "desc": "远处传来马蹄与喊杀声。",
         "effects": {"encounter_rate": 0.10, "elite_chance": 0.04}},
        {"id": "gold_dust_wind", "name": "金沙漫卷", "desc": "狂风卷起金色的尘土。",
         "effects": {"loot_mult": 1.4}},
    ],
    "silver_river": [
        {"id": "river_spawn", "name": "鱼汛涨潮", "desc": "河鱼成群逆流而上。",
         "effects": {"event_chance": 0.10, "mats": ["兽肉", "面粉"]}},
        {"id": "river_glint", "name": "银光粼粼", "desc": "河面泛起比平日更亮的银光。",
         "effects": {"loot_mult": 1.5}},
        {"id": "river_mist", "name": "河雾弥漫", "desc": "水汽蒸腾，前路朦胧。",
         "effects": {"encounter_rate": 0.08, "elite_chance": 0.04}},
    ],
    "king_road": [
        {"id": "road_caravan", "name": "商队往来", "desc": "过往的商队遗落了许多货物。",
         "effects": {"loot_mult": 1.4}},
        {"id": "road_bandit", "name": "匪患猖獗", "desc": "官道两旁暗藏刀光。",
         "effects": {"encounter_rate": 0.10, "elite_chance": 0.05}},
        {"id": "road_flower_wall", "name": "野花夹道", "desc": "路畔野花烂漫，香气扑鼻。",
         "effects": {"event_chance": 0.10, "mats": ["草药", "蜂蜜"]}},
    ],
    # ================= 西境 =================
    "silverwood": [
        {"id": "silverwood_moonlite", "name": "月华倾泻", "desc": "银白月光不散，林间如梦似幻。",
         "effects": {"loot_mult": 1.4}},
        {"id": "silverwood_elf_hunt", "name": "猎影潜行", "desc": "树影间有精灵箭手在游弋。",
         "effects": {"encounter_rate": 0.08, "elite_chance": 0.05}},
        {"id": "silverwood_phloem", "name": "树汁甘甜", "desc": "古老银树的汁液渗出香甜的气息。",
         "effects": {"event_chance": 0.10, "mats": ["蜂蜜", "浆果"]}},
    ],
    "starlake": [
        {"id": "starlake_glow", "name": "星光倒影", "desc": "湖面映满繁星，似可捞起。",
         "effects": {"loot_mult": 1.5}},
        {"id": "starlake_spawn", "name": "夜鱼翻腾", "desc": "夜晚的湖鱼格外活跃。",
         "effects": {"event_chance": 0.10, "mats": ["面粉", "兽肉"]}},
        {"id": "starlake_fog", "name": "寒潭雾锁", "desc": "雾气贴着湖面爬行。",
         "effects": {"encounter_rate": 0.08, "elite_chance": 0.04}},
    ],
    # ================= 北境 =================
    "frost_field": [
        {"id": "frost_aurora", "name": "极光破碎", "desc": "天幕上极光流泻如瀑。",
         "effects": {"loot_mult": 1.5}},
        {"id": "frost_wolfmoon", "name": "狼啸荒原", "desc": "雪原上狼嚎此起彼伏。",
         "effects": {"encounter_rate": 0.10, "elite_chance": 0.05}},
        {"id": "frost_herb_burial", "name": "冻土回春", "desc": "冻土下冒出倔强的药草。",
         "effects": {"event_chance": 0.10, "mats": ["霜花", "草药"]}},
    ],
    "black_forest": [
        {"id": "black_corpseglow", "name": "死气沉沉", "desc": "腐木与白骨间弥漫异样气息。",
         "effects": {"encounter_rate": 0.10, "elite_chance": 0.05}},
        {"id": "black_shadeloot", "name": "旧战场遗物", "desc": "落叶下埋着先人遗落的财富。",
         "effects": {"loot_mult": 1.4}},
        {"id": "black_mushroom", "name": "菌毯蔓延", "desc": "黑暗里长出成片的荧光菌类。",
         "effects": {"event_chance": 0.10, "mats": ["草药", "浆果"]}},
    ],
    "cinder_mountain": [
        {"id": "cinder_eruption", "name": "余烬喷溅", "desc": "山体的裂隙喷出火星与硫磺。",
         "effects": {"encounter_rate": 0.10, "elite_chance": 0.05}},
        {"id": "cinder_iron_heart", "name": "矿心沸腾", "desc": "山腹的岩浆映红岩壁，矿石异常富集。",
         "effects": {"loot_mult": 1.4, "mats": ["铁矿石"]}},
        {"id": "cinder_smoke_screen", "name": "烟尘蔽日", "desc": "浓烟遮蔽天日，视野受阻。",
         "effects": {"event_chance": 0.05}},
    ],
    # ================= 东境 =================
    "dragon_ridge": [
        {"id": "dragon_roar", "name": "龙吼回响", "desc": "龙吟穿透云层，山脊震颤。",
         "effects": {"elite_chance": 0.05}},
        {"id": "dragon_scales", "name": "鳞片之雨", "desc": "风里卷着细碎闪亮的龙鳞。",
         "effects": {"loot_mult": 1.5}},
        {"id": "dragon_fire_smoke", "name": "热浪翻涌", "desc": "灼热气流沿着山脊攀升。",
         "effects": {"encounter_rate": 0.08}},
    ],
    "storm_cliff": [
        {"id": "storm_lightning", "name": "雷暴云集", "desc": "雷云压顶，电光在崖间跳跃。",
         "effects": {"encounter_rate": 0.10, "elite_chance": 0.05}},
        {"id": "storm_windfall", "name": "狂风拾遗", "desc": "狂风把崖顶的断木与货箱刮落崖下。",
         "effects": {"loot_mult": 1.4}},
        {"id": "storm_calm_eye", "name": "风眼暂歇", "desc": "风暴难得暂歇，视野开阔。",
         "effects": {"event_chance": 0.10, "mats": ["草药", "兽肉"]}},
    ],
    # ================= 海域 =================
    "coral_reef": [
        {"id": "coral_spawn", "name": "鱼群回游", "desc": "珊瑚间的鱼群密密麻麻。",
         "effects": {"event_chance": 0.10, "mats": ["兽肉", "面粉"]}},
        {"id": "coral_tide_glow", "name": "潮光泛彩", "desc": "退潮后礁光伏出温润的光泽。",
         "effects": {"loot_mult": 1.4}},
        {"id": "coral_predator", "name": "鲨影游弋", "desc": "水下的黑影环绕礁石巡游。",
         "effects": {"encounter_rate": 0.10, "elite_chance": 0.05}},
    ],
    "storm_sea": [
        {"id": "stormsea_squall", "name": "风暴骤起", "desc": "巨浪接天，船骸在浪尖沉浮。",
         "effects": {"encounter_rate": 0.10, "elite_chance": 0.05}},
        {"id": "stormsea_wreck", "name": "沉宝浮现", "desc": "风暴过后，海面浮起残破的宝箱。",
         "effects": {"loot_mult": 1.5}},
        {"id": "stormsea_lull", "name": "海面暂平", "desc": "风暴剑拔弩张，海面反而异常平静。",
         "effects": {"event_chance": 0.10, "mats": ["铁矿石", "兽肉"]}},
    ],
    # ================= 地底 =================
    "molten_abyss": [
        {"id": "abyss_magma_surge", "name": "岩浆奔涌", "desc": "熔岩沿着裂隙涌出，映红了洞壁。",
         "effects": {"encounter_rate": 0.10, "elite_chance": 0.05}},
        {"id": "abyss_orevein", "name": "炽铁矿露", "desc": "高温熔炼出裸露的金属矿脉。",
         "effects": {"loot_mult": 1.4, "mats": ["铁矿石"]}},
        {"id": "abyss_glowshroom", "name": "幽光菌海", "desc": "地底菌类疯狂生长，溢彩流光。",
         "effects": {"event_chance": 0.10, "mats": ["草药", "浆果"]}},
    ],
    "fungus_forest": [
        {"id": "fungus_sporeburst", "name": "孢子风暴", "desc": "菌盖齐齐裂开，撒落漫天孢子。",
         "effects": {"encounter_rate": 0.10, "elite_chance": 0.05}},
        {"id": "fungus_sweetcap", "name": "蜜菇丰收", "desc": "蜜色的菌菇成簇冒出，香气诱人。",
         "effects": {"event_chance": 0.10, "mats": ["蜂蜜", "草药"]}},
        {"id": "fungus_feast", "name": "菌潮盛宴", "desc": "菌类疯长，几乎覆盖整个林床。",
         "effects": {"loot_mult": 1.4}},
    ],
    # ================= 天空 =================
    "cloud_sea": [
        {"id": "cloud_windfall", "name": "流云财宝", "desc": "破碎的方舟与浮岛遗落重重宝藏。",
         "effects": {"loot_mult": 1.5}},
        {"id": "cloud_turbulence", "name": "乱流激荡", "desc": "云海翻涌，浮台剧烈摇晃。",
         "effects": {"encounter_rate": 0.10, "elite_chance": 0.05}},
        {"id": "cloud_rainbow_spect", "name": "虹桥横跨", "desc": "一道彩虹架在云海之间。",
         "effects": {"event_chance": 0.10, "mats": ["霜花", "浆果"]}},
    ],
}
