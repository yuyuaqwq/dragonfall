# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - instance_stage_maps.py（v87.2 副本地图化）

每层 = 小地图：环境描述 desc + 可交互点 pois + 层内 NPC + 隐藏房间 secret。
按 29 章十三节 13.2 结构 / 13.8 亮点设计。装配逻辑见 _assembly.py（merge 进 stages）。

POI 结构：
  {"id": str, "type": chest|campfire|rune_stone|mechanism|trap|supply|corpse,
   "name": str, "hint": str,
   "loot": {"gold": int, "materials": [名字], "equip": "eq_id"},   # 宝箱/补给/遗骸
   "lore": str,                                                    # 石碑
   "effect": {...}}                                                # 篝火/机关/陷阱
secret 结构：
  {"cond": {"poi": "poi_id"}, "desc": str, "pois": [POI...]}
"""

INSTANCE_STAGE_MAPS = {
    # ================= 主线 8 =================
    "inst_goblin_camp": {
        0: {
            "desc": "商路边的营地外围：兽皮晾在木栅栏上，篝火堆散落，咕噜语吆喝声此起彼伏。",
            "pois": [
                {"id": "chest_1", "type": "chest", "name": "生锈的铁箱",
                 "hint": "铁箱的锁已经锈穿，看起来能撬开",
                 "loot": {"gold": 50, "materials": ["哥布林铁片"]}},
                {"id": "fire_1", "type": "campfire", "name": "将熄的篝火",
                 "hint": "火堆还温着，可以烤烤火恢复体力"},
            ],
        },
        1: {
            "desc": "营地中央的大帐篷：兽骨装饰的门帘，酒桶堆在角落，酋长的宝座垫着兽皮。",
            "pois": [
                {"id": "chest_2", "type": "chest", "name": "贡品箱",
                 "hint": "箱子上捆着麻绳，里面可能是献给酋长的贡品",
                 "loot": {"gold": 80, "materials": ["哥布林铁片"]}},
                {"id": "fire_2", "type": "campfire", "name": "暖火盆",
                 "hint": "火盆里的炭火正旺，能驱散夜战的疲惫"},
            ],
        },
        2: {
            "desc": "帐篷深处：咕噜酋长坐在兽骨宝座上，身边堆着抢来的货物与酒。",
            "pois": [
                {"id": "corpse_1", "type": "corpse", "name": "被抢的商队货箱",
                 "hint": "货箱被砸开过，里面还有没被拿走的零碎",
                 "loot": {"gold": 60, "materials": ["哥布林铁片"]}},
            ],
        },
    },
    "inst_sea_cave": {
        0: {
            "desc": "咸腥的海风灌进洞口，滩涂上散落着贝壳与沉船木，浪声在洞中轰鸣。",
            "pois": [
                {"id": "corpse_1", "type": "corpse", "name": "搁浅的水手",
                 "hint": "水手的衣服被海水泡烂，怀里似乎抱着什么",
                 "loot": {"materials": ["海盗的藏宝图"]}},
                {"id": "trap_1", "type": "trap", "name": "湿滑礁石",
                 "hint": "礁石上长满青苔，踩上去很容易滑倒"},
            ],
        },
        1: {
            "desc": "洞穴向内延伸，滴水声回荡，海盗的火把在黑暗中晃动。",
            "pois": [
                {"id": "chest_1", "type": "chest", "name": "海盗宝箱",
                 "hint": "木箱上烙着骷髅标记，锁头是新换的",
                 "loot": {"gold": 120, "materials": ["海盗的藏宝图"]}},
            ],
        },
        2: {
            "desc": "密室堆满抢来的货物：木箱、酒桶、珠宝散落一地，独眼杰克的旗子挂在墙上。",
            "secret": {
                "cond": {"poi": "corpse_1"},
                "desc": "你想起水手怀里的藏宝图——图上画着密室角落的一块松动地砖！",
                "pois": [
                    {"id": "secret_chest", "type": "chest", "name": "藏起来的珠宝盒",
                     "hint": "地砖下的暗格，藏着独眼杰克最值钱的战利品",
                     "loot": {"gold": 300, "materials": ["海妖鳞片"]}},
                ],
            },
        },
    },
    "inst_old_king_tomb": {
        0: {
            "desc": "石板墓道两侧是壁龛，烛火幽绿，脚步声在空旷中回响。",
            "pois": [
                {"id": "rune_1", "type": "rune_stone", "name": "墓志铭石碑",
                 "hint": "碑上刻着古王奥德里克的生卒与功绩",
                 "lore": "『吾王奥德里克，戍边四十年，以血换民安。魂归于此，勿扰其眠。』"},
                {"id": "trap_1", "type": "trap", "name": "翻板机关",
                 "hint": "石板有松动的痕迹，可能踩空"},
            ],
        },
        1: {
            "desc": "巨大的石棺立在中央，棺盖上刻着古王的生平浮雕。",
            "pois": [
                {"id": "rune_2", "type": "rune_stone", "name": "古王铭文",
                 "hint": "棺盖边缘刻着一行小字",
                 "lore": "『王座之下，机关常鸣。知吾者，可免一劫。』",
                 # R3 P2-4：POI id 实例内唯一化（原 rune_1 与 L0 墓志铭石碑撞 id，
                 # _any_poi_used/poi_unlocks 跨层语义依赖 id 巧合）——铭文本身即机关
                 # 启示：effect.unlock 指向 rune_1，读任一石碑均解锁王座机关（行为不变）
                 "effect": {"unlock": "rune_1"}},
            ],
        },
        2: {
            "desc": "王座厅，古王奥德里克的安息之所：王座上的铠甲仿佛还在呼吸。",
            "pois": [
                {"id": "mech_1", "type": "mechanism", "name": "王座机关",
                 "hint": "王座扶手处有个隐蔽的机关，似乎需要某种铭文启示",
                 "need": {"poi_read": "rune_1"},
                 "effect": {"skip_elite": True},
                 "desc": "你依照铭文转动机关，地面裂开一条捷径——可以绕过守卫！"},
                {"id": "chest_1", "type": "chest", "name": "陪葬宝箱",
                 "hint": "石箱上雕着古王的家徽，落满灰尘",
                 "loot": {"gold": 200, "materials": ["古王碎片"]}},
            ],
        },
    },
    "inst_secret_crypt": {
        0: {
            "desc": "教堂地下的石廊，圣光从气窗漏下，墙上有烧焦的痕迹。",
            "pois": [
                {"id": "trap_1", "type": "trap", "name": "圣光陷阱",
                 "hint": "地板上刻着圣徽，踩上去会触发圣光灼烧"},
                {"id": "rune_1", "type": "rune_stone", "name": "审判纪要石碑",
                 "hint": "碑上刻着教会审判异端的记录",
                 "lore": "『凡被圣光标记者，不可通行。沿墙而行，可避其锋。』",
                 "effect": {"avoid_trap": "trap_1"}},
            ],
        },
        1: {
            "desc": "审判庭中央是铁刑架，周围摆着囚笼，空气里还留着铁锈与火油味。",
            "pois": [
                {"id": "supply_1", "type": "supply", "name": "教会物资箱",
                 "hint": "铁箱里码着整齐的补给",
                 "loot": {"materials": ["圣水"], "equip": None}},
            ],
        },
        2: {
            "desc": "枢机主教藏匿的密室：书架、密信、封印的圣物，烛台还在燃烧。",
            "pois": [
                {"id": "chest_1", "type": "chest", "name": "圣物箱",
                 "hint": "银质箱体上刻着封印符文，微微发光",
                 "loot": {"gold": 150, "materials": ["圣堂密卷"]}},
            ],
        },
    },
    "inst_elven_ruins": {
        0: {
            "desc": "倒塌的精灵柱廊，藤蔓缠绕，月光从破顶洒下，落叶铺了厚厚一层。",
            "pois": [
                {"id": "fire_1", "type": "campfire", "name": "残垣火堆",
                 "hint": "不知谁点的火堆还亮着，能暖暖身子"},
            ],
        },
        1: {
            "desc": "走廊尽头的精灵石像一字排开，眼窝里嵌着宝石，仿佛在注视来者。",
            "pois": [
                {"id": "mech_1", "type": "mechanism", "name": "精灵石像",
                 "hint": "其中一尊石像的底座有个可以转动的机关",
                 "effect": {"open_secret": True},
                 "desc": "你转动石像底座，走廊侧面无声地滑开一道暗门！"},
                {"id": "corpse_1", "type": "corpse", "name": "精灵战士遗骸",
                 "hint": "精灵弓手的遗骸，箭袋已经朽烂",
                 "loot": {"materials": ["月光石"]}},
            ],
            "secret": {
                "cond": {"poi": "mech_1"},
                "desc": "暗门后是一间藏宝室，月光透过天窗照亮满地的精灵古物。",
                "pois": [
                    {"id": "secret_chest", "type": "chest", "name": "精灵宝箱",
                     "hint": "木箱上缠绕着藤蔓纹，锁是月牙形的",
                     "loot": {"gold": 250, "materials": ["月光石"]}},
                ],
            },
        },
        2: {
            "desc": "王座厅的地面嵌着星图，晨曦的雕像俯瞰众生，星辉在穹顶流转。",
            "pois": [],
        },
    },
    "inst_ash_temple": {
        0: {
            "desc": "灼热的空气中飘着灰烬，熔岩在远处缓缓流淌，火光映红整片岩壁。",
            "pois": [
                {"id": "fire_1", "type": "campfire", "name": "熔岩裂隙",
                 "hint": "裂隙里透出红光，靠过去能感到热浪——但比被恶魔追着打好多了"},
            ],
        },
        1: {
            "desc": "回廊两侧是燃烧的火盆，地面石板被烤得发烫，热浪扭曲了视线。",
            "pois": [
                {"id": "supply_1", "type": "supply", "name": "祭品匣",
                 "hint": "石匣里供奉着祭品，恶魔似乎没来得及取走",
                 "loot": {"materials": ["大生命药水"]}},
                {"id": "trap_1", "type": "trap", "name": "灼热地板",
                 "hint": "某些石板烧得通红，踩上去会烫伤"},
            ],
        },
        2: {
            "desc": "封印之殿：地面刻着巨大的封印阵，恶魔祭司赫尔加正在进行最后的仪式。",
            "pois": [
                {"id": "rune_1", "type": "rune_stone", "name": "封印符文碑",
                 "hint": "碑上刻着上古封印的符文",
                 "lore": "『火非烬，烬非灭。余烬之中，新生萌发。』"},
            ],
        },
    },
    "inst_abyss_gate": {
        0: {
            "desc": "大地裂开的伤口，黑暗从裂缝深处涌出，仿佛在呼吸。",
            "pois": [
                {"id": "corpse_1", "type": "corpse", "name": "深渊骑士残骸",
                 "hint": "骑士的铠甲被黑暗腐蚀，胸口还挂着护符",
                 "loot": {"materials": ["深渊骑士护符"]}},
            ],
        },
        1: {
            "desc": "长廊的墙壁上刻着扭曲的浮雕，深渊法师的低语声在黑暗中不断回响。",
            "pois": [
                {"id": "rune_1", "type": "rune_stone", "name": "深渊铭文碑",
                 "hint": "碑文在黑暗中泛着幽光",
                 "lore": "『它曾是我们之中的一个，直到它学会以黑暗为食。』"},
            ],
        },
        2: {
            "desc": "巢穴中央是蠕动的黑暗之核，蚀夜的真身正在凝聚——这是它的真相形态。",
            "pois": [],
        },
    },
    "inst_dragon_tomb": {
        0: {
            "desc": "巨大的龙骨拱门，两侧的龙牙比人还高，龙威仿佛还残留在骨架上。",
            "pois": [
                {"id": "rune_1", "type": "rune_stone", "name": "龙语碑文",
                 "hint": "碑上刻着弯弯曲曲的龙语",
                 "lore": "『眠者之殿，龙鳞为钥。』",
                 "effect": {"unlock": "mechanism_dragon_gate"}},
            ],
        },
        1: {
            "desc": "甬道堆满龙骨，踩上去嘎吱作响，骨缝里闪着磷火。",
            "pois": [
                {"id": "corpse_1", "type": "corpse", "name": "龙裔遗骸",
                 "hint": "半龙人的遗骸蜷在骨堆边，怀里抱着什么",
                 "loot": {"materials": ["龙鳞"]}},
            ],
        },
        2: {
            "desc": "大殿中央，古龙奥姆的骸骨盘踞成山，幽火在它的眼窝中燃烧。",
            "pois": [
                {"id": "mech_1", "type": "mechanism", "name": "暗门机关",
                 "hint": "大殿侧壁有道龙纹暗门，需要龙语启示",
                 "need": {"poi_read": "rune_1"},
                 "effect": {"open_secret": True},
                 "desc": "你按碑文低吟龙语，暗门轰然开启！"},
            ],
            "secret": {
                "cond": {"poi": "mech_1"},
                "desc": "暗门后的藏龙窟：满地龙鳞与金银，龙的财宝在这里沉睡。",
                "pois": [
                    {"id": "secret_chest", "type": "chest", "name": "龙鳞宝箱",
                     "hint": "箱体覆满龙鳞，锁孔是龙爪的形状",
                     "loot": {"gold": 400, "materials": ["龙鳞"]}},
                ],
            },
        },
    },
    # ================= 区域支线 5 =================
    "inst_deer_fort": {
        0: {
            "desc": "城门半塌，锈蚀的绞盘还挂着半截吊桥铁链，墙头插着折断的军旗。",
            "pois": [
                {"id": "mech_1", "type": "mechanism", "name": "城门绞盘",
                 "hint": "绞盘还能转动，也许能放下吊桥少走些弯路",
                 "effect": {"skip_wave": True},
                 "desc": "你转动绞盘，吊桥轰然落下——庭院里的守卫被引开了一波！"},
                {"id": "corpse_1", "type": "corpse", "name": "守军残骸",
                 "hint": "鹿角要塞守军的尸体，铠甲上还插着箭",
                 "loot": {"materials": ["军旗碎片"]}},
            ],
        },
        1: {
            "desc": "庭院里散落着折断的兵器与烧毁的战车，地面被马蹄踏得泥泞。",
            "pois": [
                {"id": "supply_1", "type": "supply", "name": "军械箱",
                 "hint": "半埋在土里的军械箱",
                 "loot": {"materials": ["精铁锭"]}},
            ],
        },
        2: {
            "desc": "主厅的壁炉早已熄灭，要塞幽灵的虚影在梁柱间游荡。",
            "pois": [
                {"id": "chest_1", "type": "chest", "name": "要塞宝箱",
                 "hint": "主厅角落的箱子，锁上刻着鹿角徽记",
                 "loot": {"gold": 150, "materials": ["军旗碎片"]}},
            ],
        },
    },
    "inst_holy_trial": {
        0: {
            "desc": "刻满誓言的石门，圣光从门缝中透出，门上挂着历代冠军的名牌。",
            "pois": [
                {"id": "rune_1", "type": "rune_stone", "name": "试炼誓言碑",
                 "hint": "碑上刻着骑士的誓言",
                 "lore": "『无畏之心，百炼成钢。试炼不是考验，是馈赠。』"},
            ],
        },
        1: {
            "desc": "回廊两侧立着历代冠军的雕像，一名老兵坐在角落擦拭长剑。",
            "pois": [
                {"id": "chest_1", "type": "chest", "name": "老兵补给箱",
                 "hint": "老兵脚边的箱子，装着伤药与干粮",
                 "loot": {"materials": ["圣水"]}},
            ],
            "npcs": ["npc_trial_veteran"],
        },
        2: {
            "desc": "圆形竞技场，圣光如柱般垂落，试炼骑士长在中央等待着挑战者。",
            "pois": [],
        },
    },
    "inst_moon_temple": {
        0: {
            "desc": "银白的月门，月光凝成实质在门框上流淌，仿佛踏进月色本身。",
            "pois": [
                {"id": "supply_1", "type": "supply", "name": "月光供品",
                 "hint": "祭台上的供品，信徒还未取走",
                 "loot": {"materials": ["月辉石"]}},
                {"id": "rune_1", "type": "rune_stone", "name": "月神祷文碑",
                 "hint": "碑上刻着月神的祷文",
                 "lore": "『月亏月盈，皆为月恩。』"},
            ],
        },
        1: {
            "desc": "回廊的穹顶绘着月相变迁，月光在地面铺成一条银毯。",
            "pois": [
                {"id": "chest_1", "type": "chest", "name": "月光宝箱",
                 "hint": "银白色的箱子，在月光下几乎隐形",
                 "loot": {"gold": 200, "materials": ["月辉石"]}},
            ],
        },
        2: {
            "desc": "神殿中央，月神守卫沐浴在圣光中，月光凝成的长矛斜插在地。",
            "pois": [],
        },
    },
    "inst_frost_throne": {
        0: {
            "desc": "寒风灌入口中，冰霜在墙壁上结出荆棘般的冰晶，呼出的气立刻成雾。",
            "pois": [
                {"id": "fire_1", "type": "campfire", "name": "冰封火堆",
                 "hint": "火堆被冰封了一半，拨开冰壳还能点燃"},
            ],
        },
        1: {
            "desc": "回廊的冰柱如剑林，寒气透骨，脚下的冰面映出模糊的倒影。",
            "pois": [
                {"id": "mech_1", "type": "mechanism", "name": "冰晶机关",
                 "hint": "墙上的冰晶簇中嵌着一块不寻常的蓝宝石",
                 "effect": {"unlock": "campfire_throne"},
                 "desc": "你打碎冰晶取下蓝宝石——远处传来冰层碎裂的声音，似乎打通了什么！"},
            ],
        },
        2: {
            "desc": "王座由整块寒冰雕成，冰霜领主坐在其上，呼出的气都是冰雾。",
            "pois": [
                {"id": "fire_2", "type": "campfire", "name": "取暖火堆",
                 "hint": "王座旁有个火盆——蓝宝石的光芒似乎让它亮了起来",
                 "need": {"unlock": "campfire_throne"},
                 "effect": {"heal_pct": 0.2}},
            ],
        },
    },
    "inst_storm_throne": {
        0: {
            "desc": "雷云在门框上翻滚，电光不时劈在门柱上，风刃割得脸生疼。",
            "pois": [
                {"id": "rune_1", "type": "rune_stone", "name": "风暴预言碑",
                 "hint": "碑文被雷劈过，字迹模糊但可辨",
                 "lore": "『雷落九重，云怒难平。取风为翼，可登云巅。』"},
            ],
        },
        1: {
            "desc": "回廊的地面是导电的金属板，雷光在脚下流窜，空气中满是臭氧味。",
            "pois": [
                {"id": "trap_1", "type": "trap", "name": "雷池",
                 "hint": "地面有块金属板格外闪亮，恐怕是通电的"},
            ],
        },
        2: {
            "desc": "风暴龙王盘踞在王座上，周身环绕着雷暴，王座由云与雷铸成。",
            "pois": [],
        },
    },
    # ================= 外域 6 =================
    "inst_sunken_ship": {
        0: {
            "desc": "倾斜的甲板泡在海水里，桅杆断裂，帆布腐烂，海鸟在残骸上盘旋。",
            "pois": [
                {"id": "corpse_1", "type": "corpse", "name": "水手遗骸",
                 "hint": "水手抱着一只酒瓶，瓶塞还完好",
                 "loot": {"materials": ["朗姆酒"]}},
            ],
        },
        1: {
            "desc": "船舱里堆着霉烂的货物，幽灵水手在暗处低声哼着水手歌。",
            "pois": [
                {"id": "chest_1", "type": "chest", "name": "船长酒柜",
                 "hint": "酒柜的锁被砸开了，里面还有存货",
                 "loot": {"gold": 100, "materials": ["朗姆酒"]}},
            ],
            "npcs": ["npc_ghost_sailor"],
        },
        2: {
            "desc": "船长室的门半掩，里面传来金币碰撞的声音，克罗的旗子挂在墙上。",
            "pois": [
                {"id": "chest_2", "type": "chest", "name": "船长宝箱",
                 "hint": "最大的铁箱，锁着三重锁",
                 "loot": {"gold": 300, "materials": ["幽灵船票"]}},
            ],
        },
    },
    "inst_siren_nest": {
        0: {
            "desc": "茂密的海藻挡住光线，水波在洞壁上投下摇曳的光影，歌声在深处回荡。",
            "pois": [
                {"id": "mech_1", "type": "mechanism", "name": "海藻帷幕",
                 "hint": "厚厚一层海藻帘子，后面似乎藏着什么",
                 "effect": {"unlock": "supply_hidden"},
                 "desc": "你拨开海藻帷幕，露出后面一条隐秘的礁石岔道！"},
            ],
        },
        1: {
            "desc": "珊瑚如水晶般发光，照亮整个回廊，鱼群在珊瑚间穿梭。",
            "pois": [
                {"id": "supply_1", "type": "supply", "name": "珊瑚藏物",
                 "hint": "珊瑚丛中有个贝壳匣子",
                 "need": {"unlock": "supply_hidden"},
                 "loot": {"materials": ["荧光鳞"]}},
            ],
        },
        2: {
            "desc": "巢穴中央，海妖女王蓝歌坐在珍珠王座上，歌声就是从这里传出的。",
            "pois": [
                {"id": "chest_1", "type": "chest", "name": "珍珠宝箱",
                 "hint": "珍珠母贝做成的箱子，散发着柔光",
                 "loot": {"gold": 220, "materials": ["海妖鳞片"]}},
            ],
        },
    },
    "inst_sea_god_temple": {
        0: {
            "desc": "海底神殿的入口，海神雕像手持三叉戟，注视来者，水流在柱间穿行。",
            "pois": [
                {"id": "rune_1", "type": "rune_stone", "name": "海神祷文碑",
                 "hint": "碑上刻着海神的祷文",
                 "lore": "『潮起潮落，皆为吾意。敬畏者，得海之庇护。』"},
            ],
        },
        1: {
            "desc": "回廊的潮水随节奏涨落，贝壳在墙壁上嵌成花纹，一名祭司在礁石上祈祷。",
            "pois": [
                # R3 P1-4：潮汐祭司支线素材（29 章 13.4：集齐 3 片潮汐贝壳换潮汐护符）
                {"id": "shell_1", "type": "supply", "name": "嵌贝壁龛",
                 "hint": "墙壁上嵌成花纹的贝壳，泛着海神的微光",
                 "loot": {"materials": ["潮汐贝壳"]}},
                {"id": "shell_2", "type": "supply", "name": "散落的贝壳",
                 "hint": "礁石旁散落的贝壳，潮水刚退",
                 "loot": {"materials": ["潮汐贝壳"]}},
            ],
            "npcs": ["npc_tide_priest"],
        },
        2: {
            "desc": "祭坛上的水镜映出天空，海神祭司澜歌正在进行祈潮仪式，海水在她脚下臣服。",
            "pois": [
                {"id": "chest_1", "type": "chest", "name": "贡品宝箱",
                 "hint": "祭坛旁的箱子，装着信徒的贡品",
                 "loot": {"gold": 260, "materials": ["海神祷文"]}},
            ],
        },
    },
    "inst_deep_dragon_palace": {
        0: {
            "desc": "龙宫的珊瑚宫门，夜明珠在门楣上发光，虾兵蟹将在门外巡逻。",
            "pois": [
                {"id": "corpse_1", "type": "corpse", "name": "虾兵残甲",
                 "hint": "一副被遗弃的虾兵铠甲，腰牌还挂着",
                 "loot": {"materials": ["龙宫珠"]}},
            ],
        },
        1: {
            "desc": "长廊两侧是水晶珊瑚，鱼群在廊外游过，水波把光影揉碎。",
            "pois": [
                {"id": "chest_1", "type": "chest", "name": "珊瑚宝箱",
                 "hint": "珊瑚长成的箱子，卡在礁石间",
                 "loot": {"gold": 240, "materials": ["龙宫珠"]}},
            ],
        },
        2: {
            "desc": "大殿金碧辉煌，深海龙王敖澜盘踞在宝座上，龙须随水流浮动。",
            "pois": [],
        },
    },
    "inst_gray_dwarf": {
        0: {
            "desc": "铁门厚重，门楣刻着灰矮人的锤徽，一名囚犯被锁在门边的铁笼里。",
            "pois": [
                {"id": "corpse_1", "type": "corpse", "name": "守卫残骸",
                 "hint": "灰矮人守卫的尸体，腰带上挂着钥匙串",
                 "loot": {"materials": ["精铁锭"]}},
            ],
            "npcs": ["npc_dwarf_prisoner"],
        },
        1: {
            "desc": "锻造炉还在燃烧，兵器架上插满铁制武器，火星在空气中飞舞。",
            "pois": [
                {"id": "chest_1", "type": "chest", "name": "军械箱",
                 "hint": "铁箱里码着整齐的军械",
                 "loot": {"gold": 180, "materials": ["精铁锭"]}},
            ],
        },
        2: {
            "desc": "石炉领主坐在铁王座上，面前摆着斟满的酒杯，火光在他脸上跳动。",
            "pois": [
                {"id": "fire_1", "type": "campfire", "name": "领主壁炉",
                 "hint": "壁炉里的火烧得正旺，决战前烤烤火吧"},
            ],
        },
    },
    "inst_under_dragon": {
        0: {
            "desc": "洞穴入口堆着巨兽的骸骨，硫磺味刺鼻，地底的热气从岩缝中喷出。",
            "pois": [
                {"id": "mech_1", "type": "mechanism", "name": "龙骸骨门",
                 "hint": "一扇由龙骸拼成的巨门，卡在轨道上",
                 "effect": {"skip_elite": True},
                 "desc": "你扳动骨门的机括，巨门轰然落下——甬道里的幼龙被隔开了一批！"},
            ],
        },
        1: {
            "desc": "甬道的墙壁嵌着龙鳞，被磨损的地面发亮，深处传来幼龙的嘶鸣。",
            "pois": [
                {"id": "corpse_1", "type": "corpse", "name": "幼龙残骸",
                 "hint": "一只还没成年的地底幼龙尸体",
                 "loot": {"materials": ["地底龙鳞"]}},
            ],
        },
        2: {
            "desc": "黑渊的古龙盘在巢中，周身缭绕着地底熔光，这里是它的领地。",
            "pois": [],
        },
    },
    # ================= 扩展 3 =================
    "inst_eye_of_storm": {
        0: {
            "desc": "云端之上的石门，风从门缝呼啸而过，云海在脚下翻涌。",
            "pois": [
                {"id": "rune_1", "type": "rune_stone", "name": "风神铭文碑",
                 "hint": "碑上的铭文被风磨得发亮",
                 "lore": "『风是天空的血脉。追风者，得风之速。』",
                 "effect": {"boss_buff": "spd_up"}},
            ],
        },
        1: {
            "desc": "回廊悬在云海上，风元素在四周游荡，脚下的云桥时隐时现。",
            "pois": [
                {"id": "chest_1", "type": "chest", "name": "云中铁箱",
                 "hint": "铁箱被风绳捆在云桥上",
                 "loot": {"gold": 320, "materials": ["雷核"]}},
            ],
        },
        2: {
            "desc": "风暴的平静中心，风暴之主云怒悬浮在空中，雷云在他脚下翻腾。",
            "pois": [],
        },
    },
    "inst_abyss_throne": {
        0: {
            "desc": "深渊的入口是张开的巨口，黑暗仿佛有重量，一名先知跪在入口处喃喃自语。",
            "pois": [
                {"id": "rune_1", "type": "rune_stone", "name": "深渊预言碑",
                 "hint": "碑上的文字不断在黑暗中明灭",
                 "lore": "『魔像走廊的机关，动一处则万处皆动。智者绕行，愚者触之。』"},
            ],
            "npcs": ["npc_abyss_seer"],
        },
        1: {
            "desc": "走廊两侧的深渊魔像排成队列，空洞的眼窝注视着过客，仿佛随时会苏醒。",
            "pois": [
                {"id": "trap_1", "type": "trap", "name": "魔像陷阱",
                 "hint": "地板上有细微的震动纹路，恐怕会唤醒魔像"},
            ],
        },
        2: {
            "desc": "摩罗坐在骸骨王座上，四周漂浮着暗影，王座之下是无尽的深渊。",
            "pois": [],
        },
    },
    "inst_cloud_sanctum": {
        0: {
            "desc": "云层凝成的门扉，光从门缝中流泻，脚下是软绵绵的云阶。",
            "pois": [
                {"id": "fire_1", "type": "campfire", "name": "云端火堆",
                 "hint": "云上竟有火堆，火苗是淡金色的"},
            ],
        },
        1: {
            "desc": "回廊的地面是流动的云，云中守卫的身影时隐时现，星辉在穹顶流淌。",
            "pois": [
                {"id": "mech_1", "type": "mechanism", "name": "星门机关",
                 "hint": "回廊尽头有道星门，门框上嵌着七颗星石",
                 "effect": {"open_secret": True},
                 "desc": "你按下七颗星石，星门无声开启——圣殿的藏宝室出现了！"},
            ],
            "npcs": ["npc_cloud_guardian"],
            "secret": {
                "cond": {"poi": "mech_1"},
                "desc": "星门后的藏宝室：云凝成的架子上摆着闪闪发光的圣物。",
                "pois": [
                    {"id": "secret_chest", "type": "chest", "name": "云中宝箱",
                     "hint": "箱子是半透明的，像一块凝固的云",
                     "loot": {"gold": 500, "materials": ["星辉石"]}},
                ],
            },
        },
        2: {
            "desc": "圣殿中央，云中圣者奥拉被光环环绕，圣歌在云间回荡。",
            "pois": [],
        },
    },
}

# 层内 NPC 数据（引用 03 章 NPC 命名空间，装配时校验存在性）
INSTANCE_STAGE_NPCS = {
    "npc_trial_veteran": {
        "name": "试炼老兵",
        "icon": "🛡️",
        "map": "inst_holy_trial",
        "funcs": ["lore"],
        "dialogue": "『当年我也像你一样站在这里。记住：冠军的剑从不犹豫。』",
    },
    "npc_ghost_sailor": {
        "name": "幽灵水手",
        "icon": "👻",
        "map": "inst_sunken_ship",
        "funcs": ["lore"],
        "dialogue": "『那晚的风暴……不是风暴。是克罗把船驶进了海妖的歌声里。』",
    },
    "npc_tide_priest": {
        "name": "潮汐祭司",
        "icon": "🌊",
        "map": "sea_god_temple",
        "funcs": ["lore", "quest"],
        "quest": "s_tide_shells",
        "dialogue": "『海神注视着你。潮汐回廊的贝壳，是海神散落的鳞片——集齐 3 片，我为你祝福。』",
    },
    "npc_dwarf_prisoner": {
        "name": "灰矮人囚犯",
        "icon": "⛓️",
        "map": "inst_gray_dwarf",
        "funcs": ["lore"],
        "dialogue": "『放我出去？呵，钥匙在队长腰带上——就是兵工厂里那个铁疙瘩队长。』",
    },
    "npc_abyss_seer": {
        "name": "深渊先知",
        "icon": "🔮",
        "map": "abyss_throne",
        "funcs": ["lore"],
        "dialogue": "『摩罗不是王，是深渊的胃。别碰魔像走廊的机关，那是它消化的方式。』",
    },
    "npc_cloud_guardian": {
        "name": "云中守卫",
        "icon": "☁️",
        "map": "inst_cloud_sanctum",
        "funcs": ["lore"],
        "dialogue": "『圣殿千年不坠，因星门常闭。你若有缘，星石自会回应你。』",
    },
}
