# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - dungeon_pois.py（v137 副本地图化·副本 POI 挂载）

把 instance_stage_maps.py 各层内联 POI（宝箱/篝火/石碑/机关/陷阱/补给/遗骸）
迁移到副本子区域（多房间）上，复用世界地图 POI 展示管线：
玩家在副本内『副本地图』时，经 SUBAREA_POIS → _map_scene 的
「🔎 可探索触发」区展示，『探索』可触发交互。

key = "地图id:子区域id"（'inst_xxx' 前缀去除，stage_idx 0/1/2 → _1/_2/_3）。
装配时由 _assembly.py 合并进 SUBAREA_POIS（与 MESH_POI_MOUNTS 一致）。

设计要点：
  - POI id 跨副本去重：原 'chest_1'/'rune_1' 等跨副本重复，
    迁移后统一加 '<map>_<stage>_' 前缀（如 goblin_camp_0_chest_1），
    保证副本内 / 跨副本 id 唯一（stage_pois 状态按 id 记录）。
  - type/name/hint/loot/effect/need/lore/desc 原样保留（desc 仅机关/机制用）。
  - secret（隐藏房间）不迁移——那是波次 3 的事。
  - NPC（INSTANCE_STAGE_NPCS）不迁移——后续处理。
  - 4-6 房副本的额外房间（_4/_5/_6）无 stage 数据 → 不挂 POI。
"""

DUNGEON_POI_MOUNTS = {
    # ================= 主线 8 =================
    "goblin_camp:goblin_camp_1": [
        {"id": "goblin_camp_0_chest_1", "type": "chest", "name": "生锈的铁箱",
         "hint": "铁箱的锁已经锈穿，看起来能撬开",
         "loot": {"gold": 50, "materials": ["哥布林铁片"]}},
        {"id": "goblin_camp_0_fire_1", "type": "campfire", "name": "将熄的篝火",
         "hint": "火堆还温着，可以烤烤火恢复体力"},
    ],
    "goblin_camp:goblin_camp_2": [
        {"id": "goblin_camp_1_chest_2", "type": "chest", "name": "贡品箱",
         "hint": "箱子上捆着麻绳，里面可能是献给酋长的贡品",
         "loot": {"gold": 80, "materials": ["哥布林铁片"]}},
        {"id": "goblin_camp_1_fire_2", "type": "campfire", "name": "暖火盆",
         "hint": "火盆里的炭火正旺，能驱散夜战的疲惫"},
    ],
    "goblin_camp:goblin_camp_3": [
        {"id": "goblin_camp_2_corpse_1", "type": "corpse", "name": "被抢的商队货箱",
         "hint": "货箱被砸开过，里面还有没被拿走的零碎",
         "loot": {"gold": 60, "materials": ["哥布林铁片"]}},
    ],
    "sea_cave:sea_cave_1": [
        {"id": "sea_cave_0_corpse_1", "type": "corpse", "name": "搁浅的水手",
         "hint": "水手的衣服被海水泡烂，怀里似乎抱着什么",
         "loot": {"materials": ["海盗的藏宝图"]}},
        {"id": "sea_cave_0_trap_1", "type": "trap", "name": "湿滑礁石",
         "hint": "礁石上长满青苔，踩上去很容易滑倒"},
    ],
    "sea_cave:sea_cave_2": [
        {"id": "sea_cave_1_chest_1", "type": "chest", "name": "海盗宝箱",
         "hint": "木箱上烙着骷髅标记，锁头是新换的",
         "loot": {"gold": 120, "materials": ["海盗的藏宝图"]}},
    ],
    "old_king_tomb:old_king_tomb_1": [
        {"id": "old_king_tomb_0_rune_1", "type": "rune_stone", "name": "墓志铭石碑",
         "hint": "碑上刻着古王奥德里克的生卒与功绩",
         "lore": "『吾王奥德里克，戍边四十年，以血换民安。魂归于此，勿扰其眠。』"},
        {"id": "old_king_tomb_0_trap_1", "type": "trap", "name": "翻板机关",
         "hint": "石板有松动的痕迹，可能踩空"},
    ],
    "old_king_tomb:old_king_tomb_2": [
        {"id": "old_king_tomb_1_rune_2", "type": "rune_stone", "name": "古王铭文",
         "hint": "棺盖边缘刻着一行小字",
         "lore": "『王座之下，机关常鸣。知吾者，可免一劫。』",
         "effect": {"unlock": "old_king_tomb_0_rune_1"}},
    ],
    "old_king_tomb:old_king_tomb_3": [
        {"id": "old_king_tomb_2_mech_1", "type": "mechanism", "name": "王座机关",
         "hint": "王座扶手处有个隐蔽的机关，似乎需要某种铭文启示",
         "need": {"poi_read": "old_king_tomb_0_rune_1"},
         "effect": {"skip_elite": True},
         "desc": "你依照铭文转动机关，地面裂开一条捷径——可以绕过守卫！"},
        {"id": "old_king_tomb_2_chest_1", "type": "chest", "name": "陪葬宝箱",
         "hint": "石箱上雕着古王的家徽，落满灰尘",
         "loot": {"gold": 200, "materials": ["古王碎片"]}},
    ],
    "secret_crypt:secret_crypt_1": [
        {"id": "secret_crypt_0_trap_1", "type": "trap", "name": "圣光陷阱",
         "hint": "地板上刻着圣徽，踩上去会触发圣光灼烧"},
        {"id": "secret_crypt_0_rune_1", "type": "rune_stone", "name": "审判纪要石碑",
         "hint": "碑上刻着教会审判异端的记录",
         "lore": "『凡被圣光标记者，不可通行。沿墙而行，可避其锋。』",
         "effect": {"avoid_trap": "secret_crypt_0_trap_1"}},
    ],
    "secret_crypt:secret_crypt_2": [
        {"id": "secret_crypt_1_supply_1", "type": "supply", "name": "教会物资箱",
         "hint": "铁箱里码着整齐的补给",
         "loot": {"materials": ["圣水"], "equip": None}},
    ],
    "secret_crypt:secret_crypt_3": [
        {"id": "secret_crypt_2_chest_1", "type": "chest", "name": "圣物箱",
         "hint": "银质箱体上刻着封印符文，微微发光",
         "loot": {"gold": 150, "materials": ["圣堂密卷"]}},
    ],
    "elven_ruins:elven_ruins_1": [
        {"id": "elven_ruins_0_fire_1", "type": "campfire", "name": "残垣火堆",
         "hint": "不知谁点的火堆还亮着，能暖暖身子"},
    ],
    "elven_ruins:elven_ruins_2": [
        {"id": "elven_ruins_1_mech_1", "type": "mechanism", "name": "精灵石像",
         "hint": "其中一尊石像的底座有个可以转动的机关",
         "effect": {"open_secret": True},
         "desc": "你转动石像底座，走廊侧面无声地滑开一道暗门！"},
        {"id": "elven_ruins_1_corpse_1", "type": "corpse", "name": "精灵战士遗骸",
         "hint": "精灵弓手的遗骸，箭袋已经朽烂",
         "loot": {"materials": ["月光石"]}},
    ],
    "ash_temple:ash_temple_1": [
        {"id": "ash_temple_0_fire_1", "type": "campfire", "name": "熔岩裂隙",
         "hint": "裂隙里透出红光，靠过去能感到热浪——但比被恶魔追着打好多了"},
    ],
    "ash_temple:ash_temple_2": [
        {"id": "ash_temple_1_supply_1", "type": "supply", "name": "祭品匣",
         "hint": "石匣里供奉着祭品，恶魔似乎没来得及取走",
         "loot": {"materials": ["大生命药水"]}},
        {"id": "ash_temple_1_trap_1", "type": "trap", "name": "灼热地板",
         "hint": "某些石板烧得通红，踩上去会烫伤"},
    ],
    "ash_temple:ash_temple_3": [
        {"id": "ash_temple_2_rune_1", "type": "rune_stone", "name": "封印符文碑",
         "hint": "碑上刻着上古封印的符文",
         "lore": "『火非烬，烬非灭。余烬之中，新生萌发。』"},
    ],
    "abyss_gate:abyss_gate_1": [
        {"id": "abyss_gate_0_corpse_1", "type": "corpse", "name": "深渊骑士残骸",
         "hint": "骑士的铠甲被黑暗腐蚀，胸口还挂着护符",
         "loot": {"materials": ["深渊骑士护符"]}},
    ],
    "abyss_gate:abyss_gate_2": [
        {"id": "abyss_gate_1_rune_1", "type": "rune_stone", "name": "深渊铭文碑",
         "hint": "碑文在黑暗中泛着幽光",
         "lore": "『它曾是我们之中的一个，直到它学会以黑暗为食。』"},
    ],
    "dragon_tomb:dragon_tomb_1": [
        {"id": "dragon_tomb_0_rune_1", "type": "rune_stone", "name": "龙语碑文",
         "hint": "碑上刻着弯弯曲曲的龙语",
         "lore": "『眠者之殿，龙鳞为钥。』",
         "effect": {"unlock": "mechanism_dragon_gate"}},
    ],
    "dragon_tomb:dragon_tomb_2": [
        {"id": "dragon_tomb_1_corpse_1", "type": "corpse", "name": "龙裔遗骸",
         "hint": "半龙人的遗骸蜷在骨堆边，怀里抱着什么",
         "loot": {"materials": ["龙鳞"]}},
    ],
    "dragon_tomb:dragon_tomb_3": [
        {"id": "dragon_tomb_2_mech_1", "type": "mechanism", "name": "暗门机关",
         "hint": "大殿侧壁有道龙纹暗门，需要龙语启示",
         "need": {"poi_read": "dragon_tomb_0_rune_1"},
         "effect": {"open_secret": True},
         "desc": "你按碑文低吟龙语，暗门轰然开启！"},
    ],
    # ================= 区域支线 5 =================
    "deer_fort:deer_fort_1": [
        {"id": "deer_fort_0_mech_1", "type": "mechanism", "name": "城门绞盘",
         "hint": "绞盘还能转动，也许能放下吊桥少走些弯路",
         "effect": {"skip_wave": True},
         "desc": "你转动绞盘，吊桥轰然落下——庭院里的守卫被引开了一波！"},
        {"id": "deer_fort_0_corpse_1", "type": "corpse", "name": "守军残骸",
         "hint": "鹿角要塞守军的尸体，铠甲上还插着箭",
         "loot": {"materials": ["军旗碎片"]}},
    ],
    "deer_fort:deer_fort_2": [
        {"id": "deer_fort_1_supply_1", "type": "supply", "name": "军械箱",
         "hint": "半埋在土里的军械箱",
         "loot": {"materials": ["精铁锭"]}},
    ],
    "deer_fort:deer_fort_3": [
        {"id": "deer_fort_2_chest_1", "type": "chest", "name": "要塞宝箱",
         "hint": "主厅角落的箱子，锁上刻着鹿角徽记",
         "loot": {"gold": 150, "materials": ["军旗碎片"]}},
    ],
    "holy_trial:holy_trial_1": [
        {"id": "holy_trial_0_rune_1", "type": "rune_stone", "name": "试炼誓言碑",
         "hint": "碑上刻着骑士的誓言",
         "lore": "『无畏之心，百炼成钢。试炼不是考验，是馈赠。』"},
    ],
    "holy_trial:holy_trial_2": [
        {"id": "holy_trial_1_chest_1", "type": "chest", "name": "老兵补给箱",
         "hint": "老兵脚边的箱子，装着伤药与干粮",
         "loot": {"materials": ["圣水"]}},
    ],
    "moon_temple:moon_temple_1": [
        {"id": "moon_temple_0_supply_1", "type": "supply", "name": "月光供品",
         "hint": "祭台上的供品，信徒还未取走",
         "loot": {"materials": ["月辉石"]}},
        {"id": "moon_temple_0_rune_1", "type": "rune_stone", "name": "月神祷文碑",
         "hint": "碑上刻着月神的祷文",
         "lore": "『月亏月盈，皆为月恩。』"},
    ],
    "moon_temple:moon_temple_2": [
        {"id": "moon_temple_1_chest_1", "type": "chest", "name": "月光宝箱",
         "hint": "银白色的箱子，在月光下几乎隐形",
         "loot": {"gold": 200, "materials": ["月辉石"]}},
    ],
    "frost_throne:frost_throne_1": [
        {"id": "frost_throne_0_fire_1", "type": "campfire", "name": "冰封火堆",
         "hint": "火堆被冰封了一半，拨开冰壳还能点燃"},
    ],
    "frost_throne:frost_throne_2": [
        {"id": "frost_throne_1_mech_1", "type": "mechanism", "name": "冰晶机关",
         "hint": "墙上的冰晶簇中嵌着一块不寻常的蓝宝石",
         "effect": {"unlock": "campfire_throne"},
         "desc": "你打碎冰晶取下蓝宝石——远处传来冰层碎裂的声音，似乎打通了什么！"},
    ],
    "frost_throne:frost_throne_3": [
        {"id": "frost_throne_2_fire_2", "type": "campfire", "name": "取暖火堆",
         "hint": "王座旁有个火盆——蓝宝石的光芒似乎让它亮了起来",
         "need": {"unlock": "campfire_throne"},
         "effect": {"heal_pct": 0.2}},
    ],
    "storm_throne:storm_throne_1": [
        {"id": "storm_throne_0_rune_1", "type": "rune_stone", "name": "风暴预言碑",
         "hint": "碑文被雷劈过，字迹模糊但可辨",
         "lore": "『雷落九重，云怒难平。取风为翼，可登云巅。』"},
    ],
    "storm_throne:storm_throne_2": [
        {"id": "storm_throne_1_trap_1", "type": "trap", "name": "雷池",
         "hint": "地面有块金属板格外闪亮，恐怕是通电的"},
    ],
    # ================= 外域 6 =================
    "sunken_ship:sunken_ship_1": [
        {"id": "sunken_ship_0_corpse_1", "type": "corpse", "name": "水手遗骸",
         "hint": "水手抱着一只酒瓶，瓶塞还完好",
         "loot": {"materials": ["朗姆酒"]}},
    ],
    "sunken_ship:sunken_ship_2": [
        {"id": "sunken_ship_1_chest_1", "type": "chest", "name": "船长酒柜",
         "hint": "酒柜的锁被砸开了，里面还有存货",
         "loot": {"gold": 100, "materials": ["朗姆酒"]}},
    ],
    "sunken_ship:sunken_ship_3": [
        {"id": "sunken_ship_2_chest_2", "type": "chest", "name": "船长宝箱",
         "hint": "最大的铁箱，锁着三重锁",
         "loot": {"gold": 300, "materials": ["幽灵船票"]}},
    ],
    "siren_nest:siren_nest_1": [
        {"id": "siren_nest_0_mech_1", "type": "mechanism", "name": "海藻帷幕",
         "hint": "厚厚一层海藻帘子，后面似乎藏着什么",
         "effect": {"unlock": "supply_hidden"},
         "desc": "你拨开海藻帷幕，露出后面一条隐秘的礁石岔道！"},
    ],
    "siren_nest:siren_nest_2": [
        {"id": "siren_nest_1_supply_1", "type": "supply", "name": "珊瑚藏物",
         "hint": "珊瑚丛中有个贝壳匣子",
         "need": {"unlock": "supply_hidden"},
         "loot": {"materials": ["荧光鳞"]}},
    ],
    "siren_nest:siren_nest_3": [
        {"id": "siren_nest_2_chest_1", "type": "chest", "name": "珍珠宝箱",
         "hint": "珍珠母贝做成的箱子，散发着柔光",
         "loot": {"gold": 220, "materials": ["海妖鳞片"]}},
    ],
    "sea_god_temple:sea_god_temple_1": [
        {"id": "sea_god_temple_0_rune_1", "type": "rune_stone", "name": "海神祷文碑",
         "hint": "碑上刻着海神的祷文",
         "lore": "『潮起潮落，皆为吾意。敬畏者，得海之庇护。』"},
    ],
    "sea_god_temple:sea_god_temple_2": [
        {"id": "sea_god_temple_1_shell_1", "type": "supply", "name": "嵌贝壁龛",
         "hint": "墙壁上嵌成花纹的贝壳，泛着海神的微光",
         "loot": {"materials": ["潮汐贝壳"]}},
        {"id": "sea_god_temple_1_shell_2", "type": "supply", "name": "散落的贝壳",
         "hint": "礁石旁散落的贝壳，潮水刚退",
         "loot": {"materials": ["潮汐贝壳"]}},
    ],
    "sea_god_temple:sea_god_temple_3": [
        {"id": "sea_god_temple_2_chest_1", "type": "chest", "name": "贡品宝箱",
         "hint": "祭坛旁的箱子，装着信徒的贡品",
         "loot": {"gold": 260, "materials": ["海神祷文"]}},
    ],
    "deep_dragon_palace:deep_dragon_palace_1": [
        {"id": "deep_dragon_palace_0_corpse_1", "type": "corpse", "name": "虾兵残甲",
         "hint": "一副被遗弃的虾兵铠甲，腰牌还挂着",
         "loot": {"materials": ["龙宫珠"]}},
    ],
    "deep_dragon_palace:deep_dragon_palace_2": [
        {"id": "deep_dragon_palace_1_chest_1", "type": "chest", "name": "珊瑚宝箱",
         "hint": "珊瑚长成的箱子，卡在礁石间",
         "loot": {"gold": 240, "materials": ["龙宫珠"]}},
    ],
    "gray_dwarf:gray_dwarf_1": [
        {"id": "gray_dwarf_0_corpse_1", "type": "corpse", "name": "守卫残骸",
         "hint": "灰矮人守卫的尸体，腰带上挂着钥匙串",
         "loot": {"materials": ["精铁锭"]}},
    ],
    "gray_dwarf:gray_dwarf_2": [
        {"id": "gray_dwarf_1_chest_1", "type": "chest", "name": "军械箱",
         "hint": "铁箱里码着整齐的军械",
         "loot": {"gold": 180, "materials": ["精铁锭"]}},
    ],
    "gray_dwarf:gray_dwarf_3": [
        {"id": "gray_dwarf_2_fire_1", "type": "campfire", "name": "领主壁炉",
         "hint": "壁炉里的火烧得正旺，决战前烤烤火吧"},
    ],
    "under_dragon:under_dragon_1": [
        {"id": "under_dragon_0_mech_1", "type": "mechanism", "name": "龙骸骨门",
         "hint": "一扇由龙骸拼成的巨门，卡在轨道上",
         "effect": {"skip_elite": True},
         "desc": "你扳动骨门的机括，巨门轰然落下——甬道里的幼龙被隔开了一批！"},
    ],
    "under_dragon:under_dragon_2": [
        {"id": "under_dragon_1_corpse_1", "type": "corpse", "name": "幼龙残骸",
         "hint": "一只还没成年的地底幼龙尸体",
         "loot": {"materials": ["地底龙鳞"]}},
    ],
    # ================= 扩展 3 =================
    "eye_of_storm:eye_of_storm_1": [
        {"id": "eye_of_storm_0_rune_1", "type": "rune_stone", "name": "风神铭文碑",
         "hint": "碑上的铭文被风磨得发亮",
         "lore": "『风是天空的血脉。追风者，得风之速。』",
         "effect": {"boss_buff": "spd_up"}},
    ],
    "eye_of_storm:eye_of_storm_2": [
        {"id": "eye_of_storm_1_chest_1", "type": "chest", "name": "云中铁箱",
         "hint": "铁箱被风绳捆在云桥上",
         "loot": {"gold": 320, "materials": ["雷核"]}},
    ],
    "abyss_throne:abyss_throne_1": [
        {"id": "abyss_throne_0_rune_1", "type": "rune_stone", "name": "深渊预言碑",
         "hint": "碑上的文字不断在黑暗中明灭",
         "lore": "『魔像走廊的机关，动一处则万处皆动。智者绕行，愚者触之。』"},
    ],
    "abyss_throne:abyss_throne_2": [
        {"id": "abyss_throne_1_trap_1", "type": "trap", "name": "魔像陷阱",
         "hint": "地板上有细微的震动纹路，恐怕会唤醒魔像"},
    ],
    "cloud_sanctum:cloud_sanctum_1": [
        {"id": "cloud_sanctum_0_fire_1", "type": "campfire", "name": "云端火堆",
         "hint": "云上竟有火堆，火苗是淡金色的"},
    ],
    "cloud_sanctum:cloud_sanctum_2": [
        {"id": "cloud_sanctum_1_mech_1", "type": "mechanism", "name": "星门机关",
         "hint": "回廊尽头有道星门，门框上嵌着七颗星石",
         "effect": {"open_secret": True},
         "desc": "你按下七颗星石，星门无声开启——圣殿的藏宝室出现了！"},
    ],
}
