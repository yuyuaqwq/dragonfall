# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 v115 网状子区域房间 - 西境（银月林海）+ 北境（霜原）

本文件独占：西境+北境的网状子区域扩容数据（Agent C 属主）。
仅存放三个数据结构，装配由 game/core/maps.py + game/data/_assembly.py 统一合并：

- EXTRA_SUBAREAS:   每图新增房间（id 从该图既有最大序号 +1 起，旧 _1.._3 保持原样）
- SUBAREA_LINKS:    每图全部房间（含旧房间）的网状双向连接
- MESH_POI_MOUNTS:  新增房间的 POI 挂载（key = "地图id:子区域id"，value = poi id 列表），
                    装配时并入 game/data/pois.py 的 SUBAREA_POIS

拓扑铁律（33 号文档 §2.2）：
- 入口唯一（_1）；全图从 _1 BFS 可达（隐藏房除外，揭示后可达且不得成断点）
- 每图 ≥1 岔路（≥3 连接）或环/捷径；允许 ≤1 死胡同（挂 elite/boss/高价值 POI，不得是入口）
- 允许 ≤1 隐藏房间（hidden: True + reveal: explore:N，N=5-15，藏 elite 或稀有 POI）
- 除死胡同外每房 ≥2 连接；相邻房间等级差 ≤15
"""

# ============================================================================
# 一、新增房间（EXTRA_SUBAREAS）
# ============================================================================
EXTRA_SUBAREAS = {
    # ==================== 西境·银月林海 ====================
    "silverwood": [
        {
            "id": "silverwood_4", "name": "银叶溪", "icon": "🌊",
            "type": "野外", "lv": 50,
            "desc": "银叶溪在林间蜿蜒，月光把水面镀成银色。月狼蹲在溪石上，绿眼盯着粼粼的水光。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_moon_wolf", "月狼", "dps", 50,
                 ["ms_si_yao", "ms_yue_guang_zhan"], ["月狼毛皮"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "silverwood_5", "name": "风语台", "icon": "🍃",
            "type": "野外", "lv": 54,
            "desc": "一道探出树冠的银木台，风把银叶吹成雨。传说精灵吟游诗人曾在此唱过足以让月狼驻足的歌。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_treant_elder", "古树人", "tank", 54,
                 ["ms_teng_bian", "ms_ying_hua", "ms_gen_xu"], ["古树之心"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "silverwood_6", "name": "月泉秘涧", "icon": "🕳️",
            "type": "野外", "lv": 54,
            "desc": "被藤蔓掩住的隐蔽涧湾，一泓月泉从岩缝涌出，水温冰凉却泛着银辉。月狼王·银鬃曾在此歇脚，爪痕浸在泉边的冻土里。",
            "npcs": [], "hidden": True, "reveal": "explore:8",
            "monsters": [
                ["m_moon_wolf", "月狼", "dps", 53,
                 ["ms_si_yao", "ms_yue_guang_zhan"], ["月狼毛皮"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
    ],
    "starlake": [
        {
            "id": "starlake_4", "name": "星砂湾", "icon": "🏖️",
            "type": "野外", "lv": 54,
            "desc": "湖湾的浅滩堆着会发光的星砂，水精灵战士在湾口巡弋。星光沉在水底，像一串点燃的银灯。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_water_elf", "水精灵战士", "dps", 54,
                 ["ms_san_cha_ji"], ["水精灵鳞"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "starlake_5", "name": "湖底洞窟", "icon": "⛰️",
            "type": "野外", "lv": 58,
            "desc": "湖岸脚下的岩壁裂开一道水洞，湖水漫过膝盖，深处传来嗡鸣。星语湖王·冰瞳的旧巢就在洞底，散落着被水打磨圆润的巨鱼骸骨。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_giant_bass", "巨鲈", "tank", 58,
                 ["ms_zhuang_ji", "ms_shui_dan"], ["巨鲈鱼骨"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
    ],
    "moon_glade": [
        {
            "id": "moon_glade_4", "name": "月桂小径", "icon": "🌼",
            "type": "野外", "lv": 56,
            "desc": "小径两旁的月桂开得正盛，香气在月光下凝成淡淡的雾。月熊在花丛边扒拉野蜂蜜，鼻尖沾满金黄。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_moon_bear", "月熊", "tank", 56,
                 ["ms_xiong_zhang", "ms_yue_guang_zhan"], ["月熊皮"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "moon_glade_5", "name": "月影断崖", "icon": "⛰️",
            "type": "野外", "lv": 60,
            "desc": "断崖下的阴影浓得化不开，只有月光从裂隙漏下。月光精灵在崖壁的凹处栖身，警惕地打量来者。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_moon_spirit", "月光精灵", "healer", 60,
                 ["ms_yue_guang_zhan", "ms_zhi_yu"], ["月光精华"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "moon_glade_6", "name": "银月墓园", "icon": "🪦",
            "type": "野外", "lv": 60,
            "desc": "一片被遗忘的精灵墓园，石棺上刻着古老的名字，月光在青苔上流转。有人在此留下未圈完的花环，风一吹便散开。",
            "npcs": [], "hidden": True, "reveal": "explore:10",
            "monsters": [
                ["m_moon_deer", "月鹿", "speedster", 55,
                 ["ms_ji_chi", "ms_yue_guang_zhan"], ["月鹿角"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
    ],
    "emerald_valley": [
        {
            "id": "emerald_valley_4", "name": "翠溪", "icon": "💧",
            "type": "野外", "lv": 50,
            "desc": "一条清冽的翠溪穿过谷中，水底的卵石像泡着翡翠。谷地仙灵在溪边拨弄水面，见人便隐进花丛。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_valley_faerie", "谷地仙灵", "healer", 50,
                 ["ms_cai_guang", "ms_zhu_fu"], ["谷地露水"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "emerald_valley_5", "name": "藤蔓穹顶", "icon": "🌿",
            "type": "野外", "lv": 53,
            "desc": "无数藤蔓在头顶交缠成一座绿色的穹顶，光漏进来斑斑驳驳。绿角雄鹿曾在穹顶下决斗，鹿角刮落的藤须至今悬着。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_green_stag", "绿角雄鹿", "tank", 53,
                 ["ms_ding_zhuang", "ms_ying_hua"], ["绿鹿角"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
    ],
    "windvale": [
        {
            "id": "windvale_4", "name": "风铃林", "icon": "🔔",
            "type": "野外", "lv": 52,
            "desc": "林间挂满精灵串起的银铃，风一过便叮当作响。风语精灵在铃声中穿行，每一步都踩在风声的节拍上。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_whisper_spirit", "风语精灵", "healer", 52,
                 ["ms_feng_ren", "ms_wei_feng_zhu_fu"], ["风语结晶"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "windvale_5", "name": "鹰翼崖", "icon": "⛰️",
            "type": "野外", "lv": 56,
            "desc": "崖顶风势能把人掀下深渊，谷地巨鹰的巢嵌在峭壁的岩缝里。风语王·岚歌曾在此振翅，把谷中所有的云都搅成漩涡。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_valley_eagle", "谷地巨鹰", "dps", 56,
                 ["ms_fu_chong", "ms_zhao_ji"], ["巨鹰羽"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
    ],
    "moonshadow_wood": [
        {
            "id": "moonshadow_wood_4", "name": "荧光洞", "icon": "💡",
            "type": "野外", "lv": 56,
            "desc": "洞穴的岩壁上长满荧光菌，幽光如水波流动。月影兽的绿眼在暗处一闪，随即没入更深的阴影。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_moon_shade", "月影兽", "dps", 56,
                 ["ms_an_ying_zhao", "ms_yue_guang_zhan"], ["月影之爪", "月影之皮"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "moonshadow_wood_5", "name": "影沼", "icon": "🕸️",
            "type": "野外", "lv": 60,
            "desc": "暗沼的泥面泛着诡异的油光，荧光狐在沼边的枯木上小憩，尾巴拖出一道微光。沼泽深处响起夜歌的余韵。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_glow_fox", "荧光狐", "healer", 60,
                 ["ms_mei_huo", "ms_ying_guang_shan"], ["荧光狐尾"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "moonshadow_wood_6", "name": "夜歌墓穴", "icon": "🕳️",
            "type": "野外", "lv": 60,
            "desc": "藏在倒伏巨木根系下的隐穴，石阶上覆满松针。有人曾在此供奉月影之眼，祭台上的烛油尚未凝固，仿佛主人刚离去。",
            "npcs": [], "hidden": True, "reveal": "explore:12",
            "monsters": [
                ["m_shadow_panther", "影豹", "speedster", 54,
                 ["ms_pu_ji", "ms_qian_xing"], ["影豹皮"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
    ],
    "ancient_tree": [
        {
            "id": "ancient_tree_4", "name": "气根桥", "icon": "🌉",
            "type": "野外", "lv": 64,
            "desc": "巨树的气根垂成一座天然的桥，横跨深涧。暗影精灵的身影在气根间若隐若现，像风一样难以捕捉。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_shadow_elf", "暗影精灵", "dps", 64,
                 ["ms_an_ying_jian", "ms_qian_xing"], ["暗影精灵刃"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "ancient_tree_5", "name": "树冠暗室", "icon": "🍂",
            "type": "野外", "lv": 68,
            "desc": "树干中空的暗室透着干枯的清香，古树守卫曾在此休眠，树皮上的爪印深可寸许。暗室角落堆着被岁月磨圆的旧物。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_old_tree_guardian", "古树守卫", "tank", 68,
                 ["ms_teng_bian", "ms_ying_hua"], ["守卫古木"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
    ],

    # ==================== 北境·霜原 ====================
    "frost_field": [
        {
            "id": "frost_field_4", "name": "冰隙", "icon": "❄️",
            "type": "野外", "lv": 65,
            "desc": "冰层裂开一道幽蓝的缝隙，寒气从地底涌出。冰元素在各奔涌处游荡，身体像凝固的风。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_ice_elemental", "冰元素", "tank", 65,
                 ["ms_bing_dan", "ms_dong_jie"], ["冰元素核心"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "frost_field_5", "name": "雪原冰洞", "icon": "🧊",
            "type": "野外", "lv": 70,
            "desc": "雪坡下塌出一个冰洞入口，洞内蓝莹莹一片。霜巨魔曾在此囤猎，洞壁的爪印层叠交错，像一部冻住的战史。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_frost_troll", "霜巨魔", "dps", 70,
                 ["ms_zhong_ji", "ms_zai_sheng", "ms_bing_ji"], ["霜巨魔血"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "frost_field_6", "name": "冻湖湾", "icon": "🌊",
            "type": "野外", "lv": 68,
            "desc": "被流冰封住的小湖湾，冰面下隐约有巨大的黑影滑过。雪狼群曾在此伏猎，冻岸上还留着凌乱而新鲜的爪印。",
            "npcs": [], "hidden": True, "reveal": "explore:8",
            "monsters": [
                ["m_snow_wolf", "雪狼", "dps", 62,
                 ["ms_si_yao", "ms_bing_ya"], ["雪狼皮", "雪之精华", "雪之精华"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
    ],
    "forge_valley": [
        {
            "id": "forge_valley_4", "name": "黑曜石小径", "icon": "🪨",
            "type": "野外", "lv": 70,
            "desc": "小径由散落的黑曜石铺就，被地热点得微微发烫。熔岩元素在石缝间沉浮，热浪把空气都扭成波纹。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_lava_elemental", "熔岩元素", "tank", 70,
                 ["ms_rong_yan_dan", "ms_zhuo_shao"], ["熔岩核心", "熔岩石"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "forge_valley_5", "name": "熔岩断谷", "icon": "🌋",
            "type": "野外", "lv": 74,
            "desc": "一道被岩浆切出的断谷横在谷底尽头，热气蒸腾。矿魔曾在此凿取曜石，岩壁的凿痕至今泛着未散的高温。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_mining_demon", "矿魔", "dps", 74,
                 ["ms_gao_ji", "ms_huo_yan"], ["矿魔之角"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
    ],
    "black_forest": [
        {
            "id": "black_forest_4", "name": "腐牙营地", "icon": "⛺",
            "type": "野外", "lv": 75,
            "desc": "腐牙兽人废弃的营地，倒下的木棚里还搁着磨了一半的兽骨磨刀石。黑暗精灵借这处地形隐蔽，无声掠走营边的猎物。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_dark_elf", "黑暗精灵", "speedster", 75,
                 ["ms_an_ying_jian", "ms_qian_xing"], ["黑暗精灵刃"]]
            ],
            # v124 S18 猎手的救赎：腐牙萨满·嚎骨（腐牙营地精英，任务期击杀目标，掉落腐牙血囊）
            "elite": ["m_fu_ya_sa_man_hao_gu", "腐牙萨满·嚎骨", "elite", 70,
                      ["ms_ai_hao", "ms_an_ying_dan"], ["腐牙血囊"]],
            "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "black_forest_5", "name": "腐林腹地", "icon": "🍄",
            "type": "野外", "lv": 80,
            "desc": "腐林深处菌菇高过人腰，脚下一踩便渗出暗绿的汁水。腐蚀兽的巢就筑在倒下的大树根下，尸骨与腐泥混在一起。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_corrupt_beast", "腐蚀兽", "tank", 80,
                 ["ms_zhao_ji", "ms_fu_shi"], ["腐蚀兽爪"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "black_forest_6", "name": "黑渊巨木", "icon": "🕳️",
            "type": "野外", "lv": 80,
            "desc": "巨树的根系盘旋成一个通往地下的入口，树洞深处有冷光。北地猎人留下的记号钉在树皮上，褪色的字迹写着『莫入』。",
            "npcs": [], "hidden": True, "reveal": "explore:11",
            "monsters": [
                ["m_rot_orc", "腐牙兽人", "dps", 72,
                 ["ms_fu_ji", "ms_fu_shi"], ["腐牙兽牙"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
    ],
    "cinder_mountain": [
        {
            "id": "cinder_mountain_4", "name": "灰烬小径", "icon": "🌫️",
            "type": "野外", "lv": 81,
            "desc": "小径被厚厚的火山灰覆盖，踩上去扑扑作响。地狱犬循着热源在灰雾里游走，鼻息喷出的火星像游弋的萤火。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_hellhound", "地狱犬", "dps", 81,
                 ["ms_si_yao", "ms_di_yu_huo"], ["地狱犬牙"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "cinder_mountain_5", "name": "烬岩祭台", "icon": "🗿",
            "type": "野外", "lv": 86,
            "desc": "一块突出的烬黑岩台，岩面被香火烫出焦痕，朝圣者曾在此向山火祈祷。深渊奴仆守在台周，铁索拖曳在地上发出刮擦声。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_demon_servant", "深渊奴仆", "tank", 86,
                 ["ms_zhong_ji", "ms_an_ying_dan"], ["奴仆锁链"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
    ],
    "frost_fang": [
        {
            "id": "frost_fang_4", "name": "冰牙岔道", "icon": "↪️",
            "type": "野外", "lv": 66,
            "desc": "谷中一处三岔口，冰柱如屏障般隔出数条小径。雪原猛犸震地的脚步声从其中一条传来，忽近忽远。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_snow_mammoth", "雪原猛犸", "tank", 66,
                 ["ms_chong_zhuang", "ms_jian_ta"], ["猛犸毛"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "frost_fang_5", "name": "冰川冰窟", "icon": "🧊",
            "type": "野外", "lv": 69,
            "desc": "冰川裂隙深处嵌成一座冰窟，透进幽蓝的光。冰川雪兔的巢穴遍布窟壁，而窟底那面冰墙背后，冰牙领主·霜白的气息隐约可循。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_glacier_rabbit", "冰川雪兔", "speedster", 69,
                 ["ms_ji_pao", "ms_bing_dan"], ["雪兔皮"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
    ],
    "winter_lake": [
        {
            "id": "winter_lake_4", "name": "冰岸苇丛", "icon": "🌾",
            "type": "野外", "lv": 73,
            "desc": "湖岸的芦苇被冻成银色的冰刃，风一吹便沙沙作响。冰封鱼怪贴着冰面游过，尾鳍激起一道细碎的冰屑。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_frozen_fish", "冰封鱼怪", "dps", 73,
                 ["ms_zhuang_ji", "ms_shui_dan"], ["冻鱼鳞"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "winter_lake_5", "name": "永冻回廊", "icon": "⛸️",
            "type": "野外", "lv": 78,
            "desc": "断裂的冰脊围出一条回廊，冰面滑得站不住脚。湖中水灵的歌声从冰面下方传来，若即若离，像在引路，又像在设伏。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_lake_spirit", "湖中水灵", "healer", 78,
                 ["ms_shui_dan", "ms_zhi_liao"], ["湖灵泪"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
    ],
    "permafrost_field": [
        {
            "id": "permafrost_field_4", "name": "极风雪巷", "icon": "🌬️",
            "type": "野外", "lv": 71,
            "desc": "两座冰脊夹成一条雪巷，风灌进来卷起飞雪。极地冰狼贴着雪巷两侧潜行，只露出一双双灰绿色的眼。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_ice_wolf", "极地冰狼", "dps", 71,
                 ["ms_si_yao", "ms_bing_ya"], ["冰狼牙"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "permafrost_field_5", "name": "极光渊", "icon": "🌌",
            "type": "野外", "lv": 76,
            "desc": "极光垂落到雪原的裂缝边，把裂缝染成流动的绿。极光狐沿着崖壁奔跑，像是在追逐那道光。裂缝深处传来冰块崩裂的声音。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_aurora_fox", "极光狐", "speedster", 76,
                 ["ms_ji_chi", "ms_ji_guang_shan"], ["极光狐尾"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "permafrost_field_6", "name": "冻土高台", "icon": "🗿",
            "type": "野外", "lv": 76,
            "desc": "冰原中央一处罕见的冻土高台，冰层下埋着某种古老祭器。极光正巧悬在台顶，光晕在台面流成符文般的纹路。",
            "npcs": [], "hidden": True, "reveal": "explore:14",
            "monsters": [
                ["m_frost_bear", "冰原巨熊", "tank", 68,
                 ["ms_xiong_zhang", "ms_bing_hou"], ["冰熊皮"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
    ],
    "frostwhisper_canyon": [
        {
            "id": "frostwhisper_canyon_4", "name": "冰帘洞", "icon": "🧊",
            "type": "野外", "lv": 75,
            "desc": "峡谷壁上一道挂满冰帘的洞口，冰柱碰在一起叮咚作响。霜语祭司曾在洞中低声祈祷，把一段祷文刻进最粗的冰柱里。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_frost_cultist", "霜语祭司", "healer", 75,
                 ["ms_bing_dan", "ms_bing_shuang_zhu_fu"], ["霜语圣典"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "frostwhisper_canyon_5", "name": "霜语冰渊", "icon": "❄️",
            "type": "野外", "lv": 80,
            "desc": "峡谷尽头一道下陷的冰渊，寒气如刀。霜语巨魔的足印一路通向渊底，那里泛着幽蓝的光，隐约可见被冻住的旧物。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_frost_giant", "霜语巨魔", "tank", 80,
                 ["ms_zhong_ji", "ms_bing_ji"], ["霜语巨魔血"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
    ],
    "cold_spine_snow_trail": [
        {
            "id": "cold_spine_snow_trail_4", "name": "雪岭侧坡", "icon": "⛰️",
            "type": "野外", "lv": 68,
            "desc": "雪道侧坡的一条绕行岔道，避开正风口，却也藏着别的眼睛。古树守卫裹着冰甲立在坡口，像一尊冻住的路标。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_old_tree_guardian", "古树守卫", "tank", 68,
                 ["ms_teng_bian", "ms_ying_hua"], ["守卫古木"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
        {
            "id": "cold_spine_snow_trail_5", "name": "寒脊回峰", "icon": "🧊",
            "type": "野外", "lv": 71,
            "desc": "雪道尽头一块被冰封的崖壁回弯，冰原巨熊的巢就在回弯深处，柴枝与兽骨堆成一座小丘。崖顶的冰棱在暮色里折射出七色光。",
            "npcs": [], "hidden": False, "reveal": None,
            "monsters": [
                ["m_frost_bear", "冰原巨熊", "tank", 69,
                 ["ms_xiong_zhang", "ms_bing_hou"], ["冰熊皮"]]
            ],
            "elite": None, "boss": None, "funcs": ["explore"], "shop": False, "healer": False,
        },
    ],
}

# ============================================================================
# 二、网状拓扑（SUBAREA_LINKS）——覆盖每图全部房间（含旧房间），双向对称
# ============================================================================
SUBAREA_LINKS = {
    # ---- 西境·银月林海 ----
    "silverwood": {
        "silverwood_1": ["silverwood_2", "silverwood_4"],
        "silverwood_2": ["silverwood_1", "silverwood_3", "silverwood_4"],
        "silverwood_3": ["silverwood_2", "silverwood_4"],
        "silverwood_4": ["silverwood_1", "silverwood_2", "silverwood_3", "silverwood_5", "silverwood_6"],
        "silverwood_5": ["silverwood_4"],
        "silverwood_6": ["silverwood_4"],
    },
    "starlake": {
        "starlake_1": ["starlake_2", "starlake_4"],
        "starlake_2": ["starlake_1", "starlake_3", "starlake_4"],
        "starlake_3": ["starlake_2", "starlake_4"],
        "starlake_4": ["starlake_1", "starlake_2", "starlake_3", "starlake_5"],
        "starlake_5": ["starlake_4"],
    },
    "moon_glade": {
        "moon_glade_1": ["moon_glade_2", "moon_glade_4"],
        "moon_glade_2": ["moon_glade_1", "moon_glade_3", "moon_glade_4"],
        "moon_glade_3": ["moon_glade_2", "moon_glade_4"],
        "moon_glade_4": ["moon_glade_1", "moon_glade_2", "moon_glade_3", "moon_glade_5", "moon_glade_6"],
        "moon_glade_5": ["moon_glade_4"],
        "moon_glade_6": ["moon_glade_4"],
    },
    "emerald_valley": {
        "emerald_valley_1": ["emerald_valley_2", "emerald_valley_4"],
        "emerald_valley_2": ["emerald_valley_1", "emerald_valley_3", "emerald_valley_4"],
        "emerald_valley_3": ["emerald_valley_2", "emerald_valley_4"],
        "emerald_valley_4": ["emerald_valley_1", "emerald_valley_2", "emerald_valley_3", "emerald_valley_5"],
        "emerald_valley_5": ["emerald_valley_4"],
    },
    "windvale": {
        "windvale_1": ["windvale_2", "windvale_4"],
        "windvale_2": ["windvale_1", "windvale_3", "windvale_4"],
        "windvale_3": ["windvale_2", "windvale_4"],
        "windvale_4": ["windvale_1", "windvale_2", "windvale_3", "windvale_5"],
        "windvale_5": ["windvale_4"],
    },
    "moonshadow_wood": {
        "moonshadow_wood_1": ["moonshadow_wood_2", "moonshadow_wood_4"],
        "moonshadow_wood_2": ["moonshadow_wood_1", "moonshadow_wood_3", "moonshadow_wood_4"],
        "moonshadow_wood_3": ["moonshadow_wood_2", "moonshadow_wood_4"],
        "moonshadow_wood_4": ["moonshadow_wood_1", "moonshadow_wood_2", "moonshadow_wood_3", "moonshadow_wood_5", "moonshadow_wood_6"],
        "moonshadow_wood_5": ["moonshadow_wood_4"],
        "moonshadow_wood_6": ["moonshadow_wood_4"],
    },
    "ancient_tree": {
        "ancient_tree_1": ["ancient_tree_2", "ancient_tree_4"],
        "ancient_tree_2": ["ancient_tree_1", "ancient_tree_3", "ancient_tree_4"],
        "ancient_tree_3": ["ancient_tree_2", "ancient_tree_4"],
        "ancient_tree_4": ["ancient_tree_1", "ancient_tree_2", "ancient_tree_3", "ancient_tree_5"],
        "ancient_tree_5": ["ancient_tree_4"],
    },

    # ---- 北境·霜原 ----
    "frost_field": {
        "frost_field_1": ["frost_field_2", "frost_field_4"],
        "frost_field_2": ["frost_field_1", "frost_field_3", "frost_field_4"],
        "frost_field_3": ["frost_field_2", "frost_field_4"],
        "frost_field_4": ["frost_field_1", "frost_field_2", "frost_field_3", "frost_field_5", "frost_field_6"],
        "frost_field_5": ["frost_field_4"],
        "frost_field_6": ["frost_field_4"],
    },
    "forge_valley": {
        "forge_valley_1": ["forge_valley_2", "forge_valley_4"],
        "forge_valley_2": ["forge_valley_1", "forge_valley_3", "forge_valley_4"],
        "forge_valley_3": ["forge_valley_2", "forge_valley_4"],
        "forge_valley_4": ["forge_valley_1", "forge_valley_2", "forge_valley_3", "forge_valley_5"],
        "forge_valley_5": ["forge_valley_4"],
    },
    "black_forest": {
        "black_forest_1": ["black_forest_2", "black_forest_4"],
        "black_forest_2": ["black_forest_1", "black_forest_3", "black_forest_4"],
        "black_forest_3": ["black_forest_2", "black_forest_4"],
        "black_forest_4": ["black_forest_1", "black_forest_2", "black_forest_3", "black_forest_5", "black_forest_6"],
        "black_forest_5": ["black_forest_4"],
        "black_forest_6": ["black_forest_4"],
    },
    "cinder_mountain": {
        "cinder_mountain_1": ["cinder_mountain_2", "cinder_mountain_4"],
        "cinder_mountain_2": ["cinder_mountain_1", "cinder_mountain_3", "cinder_mountain_4"],
        "cinder_mountain_3": ["cinder_mountain_2", "cinder_mountain_4"],
        "cinder_mountain_4": ["cinder_mountain_1", "cinder_mountain_2", "cinder_mountain_3", "cinder_mountain_5"],
        "cinder_mountain_5": ["cinder_mountain_4"],
    },
    "frost_fang": {
        "frost_fang_1": ["frost_fang_2", "frost_fang_4"],
        "frost_fang_2": ["frost_fang_1", "frost_fang_3", "frost_fang_4"],
        "frost_fang_3": ["frost_fang_2", "frost_fang_4"],
        "frost_fang_4": ["frost_fang_1", "frost_fang_2", "frost_fang_3", "frost_fang_5"],
        "frost_fang_5": ["frost_fang_4"],
    },
    "winter_lake": {
        "winter_lake_1": ["winter_lake_2", "winter_lake_4"],
        "winter_lake_2": ["winter_lake_1", "winter_lake_3", "winter_lake_4"],
        "winter_lake_3": ["winter_lake_2", "winter_lake_4"],
        "winter_lake_4": ["winter_lake_1", "winter_lake_2", "winter_lake_3", "winter_lake_5"],
        "winter_lake_5": ["winter_lake_4"],
    },
    "permafrost_field": {
        "permafrost_field_1": ["permafrost_field_2", "permafrost_field_4"],
        "permafrost_field_2": ["permafrost_field_1", "permafrost_field_3", "permafrost_field_4"],
        "permafrost_field_3": ["permafrost_field_2", "permafrost_field_4"],
        "permafrost_field_4": ["permafrost_field_1", "permafrost_field_2", "permafrost_field_3", "permafrost_field_5", "permafrost_field_6"],
        "permafrost_field_5": ["permafrost_field_4"],
        "permafrost_field_6": ["permafrost_field_4"],
    },
    "frostwhisper_canyon": {
        "frostwhisper_canyon_1": ["frostwhisper_canyon_2", "frostwhisper_canyon_4"],
        "frostwhisper_canyon_2": ["frostwhisper_canyon_1", "frostwhisper_canyon_3", "frostwhisper_canyon_4"],
        "frostwhisper_canyon_3": ["frostwhisper_canyon_2", "frostwhisper_canyon_4"],
        "frostwhisper_canyon_4": ["frostwhisper_canyon_1", "frostwhisper_canyon_2", "frostwhisper_canyon_3", "frostwhisper_canyon_5"],
        "frostwhisper_canyon_5": ["frostwhisper_canyon_4"],
    },
    "cold_spine_snow_trail": {
        "cold_spine_snow_trail_1": ["cold_spine_snow_trail_2", "cold_spine_snow_trail_4"],
        "cold_spine_snow_trail_2": ["cold_spine_snow_trail_1", "cold_spine_snow_trail_3", "cold_spine_snow_trail_4"],
        "cold_spine_snow_trail_3": ["cold_spine_snow_trail_2", "cold_spine_snow_trail_4"],
        "cold_spine_snow_trail_4": ["cold_spine_snow_trail_1", "cold_spine_snow_trail_2", "cold_spine_snow_trail_3", "cold_spine_snow_trail_5"],
        "cold_spine_snow_trail_5": ["cold_spine_snow_trail_4"],
    },
}

# ============================================================================
# 三、新增房间 POI 挂载（MESH_POI_MOUNTS）——key = "地图id:子区域id"
# ============================================================================
MESH_POI_MOUNTS = {
    # ---- 西境：bird_nest / ancient_altar ----
    "silverwood:silverwood_4": ["bird_nest", "campfire", "fishing_spot"],
    "silverwood:silverwood_5": ["ancient_altar", "loot_pile"],            # 死胡同·高价值
    "silverwood:silverwood_6": ["ancient_altar", "loot_pile"],            # 隐藏·稀有
    "starlake:starlake_4": ["bird_nest", "fishing_spot", "star_gazing"],
    "starlake:starlake_5": ["ancient_altar", "loot_pile"],                # 死胡同·高价值
    "moon_glade:moon_glade_4": ["bird_nest", "campfire"],
    "moon_glade:moon_glade_5": ["ancient_altar", "loot_pile"],            # 死胡同·高价值
    "moon_glade:moon_glade_6": ["ancient_altar", "loot_pile"],            # 隐藏·稀有
    "emerald_valley:emerald_valley_4": ["bird_nest", "herb_patch"],
    "emerald_valley:emerald_valley_5": ["ancient_altar", "loot_pile"],    # 死胡同·高价值
    "windvale:windvale_4": ["bird_nest", "campfire", "scenic_view"],
    "windvale:windvale_5": ["ancient_altar", "loot_pile"],                # 死胡同·高价值
    "moonshadow_wood:moonshadow_wood_4": ["bird_nest", "campfire"],
    "moonshadow_wood:moonshadow_wood_5": ["ancient_altar", "loot_pile"],  # 死胡同·高价值
    "moonshadow_wood:moonshadow_wood_6": ["ancient_altar", "loot_pile"],  # 隐藏·稀有
    "ancient_tree:ancient_tree_4": ["bird_nest", "campfire", "herb_patch"],
    "ancient_tree:ancient_tree_5": ["ancient_altar", "loot_pile"],        # 死胡同·高价值

    # ---- 北境：ice_sculpture / ancient_altar / merchant_camp ----
    "frost_field:frost_field_4": ["ice_sculpture", "campfire"],
    "frost_field:frost_field_5": ["ice_sculpture", "loot_pile"],          # 死胡同·高价值
    "frost_field:frost_field_6": ["ice_sculpture", "ancient_altar"],      # 隐藏·稀有
    "forge_valley:forge_valley_4": ["merchant_camp", "campfire"],
    "forge_valley:forge_valley_5": ["ancient_altar", "loot_pile"],        # 死胡同·高价值
    "black_forest:black_forest_4": ["merchant_camp", "campfire"],
    "black_forest:black_forest_5": ["ancient_altar", "loot_pile"],        # 死胡同·高价值
    "black_forest:black_forest_6": ["ancient_altar", "loot_pile"],        # 隐藏·稀有
    "cinder_mountain:cinder_mountain_4": ["merchant_camp", "campfire"],
    "cinder_mountain:cinder_mountain_5": ["ancient_altar", "loot_pile"],  # 死胡同·高价值
    "frost_fang:frost_fang_4": ["ice_sculpture", "campfire", "herb_patch"],
    "frost_fang:frost_fang_5": ["ice_sculpture", "loot_pile"],            # 死胡同·高价值
    "winter_lake:winter_lake_4": ["ice_sculpture", "fishing_spot"],
    "winter_lake:winter_lake_5": ["ancient_altar", "loot_pile"],          # 死胡同·高价值
    "permafrost_field:permafrost_field_4": ["ice_sculpture", "campfire"],
    "permafrost_field:permafrost_field_5": ["ice_sculpture", "loot_pile"],  # 死胡同·高价值
    "permafrost_field:permafrost_field_6": ["ancient_altar", "loot_pile"],  # 隐藏·稀有
    "frostwhisper_canyon:frostwhisper_canyon_4": ["ice_sculpture", "campfire"],
    "frostwhisper_canyon:frostwhisper_canyon_5": ["ancient_altar", "loot_pile"],  # 死胡同·高价值
    "cold_spine_snow_trail:cold_spine_snow_trail_4": ["ice_sculpture", "campfire"],
    "cold_spine_snow_trail:cold_spine_snow_trail_5": ["ancient_altar", "loot_pile"],  # 死胡同·高价值
}
