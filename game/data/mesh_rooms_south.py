# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - mesh_rooms_south.py（v115 网状子区域·南境+中域区域数据）

本文件由区域数据 agent（Agent B）填充，只含【新增房间】的网状扩充数据。由 Agent A 的
_assembly.py 装配进 SUBAREAS：
  - EXTRA_SUBAREAS  : 新增房间（id 从该图现有最大序号 +1 起，全图唯一；旧 _1.._3 不动）
  - SUBAREA_LINKS   : 每张图【全部房间】（含旧房间）的网状连接（key=地图id, value={子区域id:[可达id列表]}）
  - MESH_POI_MOUNTS : 给新增房间挂载的 POI（key="地图id:子区域id"，装配时合并进 SUBAREA_POIS）

POI id 契约：既有 10 个(campfire/shrine/herb_patch/loot_pile/rune_stone/fishing_spot/note/
scenic_view/ancient_tree_sight/star_gazing) + F agent 新 7 个(merchant_camp/ancient_altar/
bird_nest/ice_sculpture/dragon_bone/shipwreck/traveler_grave)。本文件只挂载不定义。

拓扑铁律：双向对称、_1 入口可达全图(隐藏除外)、除死胡同外每房>=2连接、死胡同=1连接(仅1个)、
相邻等级差<=15、至少 1 个岔路(>=3 连接)或环/捷径、死胡同不能是入口。隐藏房间 hidden:True+reveal。
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# 一、EXTRA_SUBAREAS：新增房间（南境+中域 野外）
# ---------------------------------------------------------------------------
# 每个 new room dict 与既有子区域同构：
#   id/name/icon/desc/type/lv/npcs/monsters/elite/boss/funcs/shop/healer
#   可选 hidden(bool) / reveal(str)。monsters 必非空（从同图/同区域既有条目复制，微调 lv）。
# ---------------------------------------------------------------------------
EXTRA_SUBAREAS = {
    # ============================ 南境·绿野 ============================
    "oak_plain": [
        {
            "id": "oak_plain_4",
            "name": "乱石岗",
            "icon": "🪨",
            "desc": "橡木平原边陲的乱石岗，巨石犬牙交错，岩鼠在石缝间奔窜。老猎人常说，翻过这片石岗有条通往溪边的捷径。",
            "type": "野外",
            "lv": 3,
            "npcs": [],
            "monsters": [
                ["m_rock_rat", "岩鼠", "speedster", 3, ["ms_ken_yao"], ["岩鼠牙"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "oak_plain_5",
            "name": "废弃磨坊",
            "icon": "🌾",
            "desc": "一座塌了半边屋顶的旧磨坊，风车叶片早已停摆。野猪把磨坊当成了窝，哼哧着在散落的麦袋间翻拱。",
            "type": "野外",
            "lv": 4,
            "npcs": [],
            "monsters": [
                ["m_boar", "野猪", "dps", 4, ["ms_chong_zhuang"], ["野猪牙", "野猪皮"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "oak_plain_6",
            "name": "野猪泥潭",
            "icon": "🟤",
            "desc": "一片被野猪拱得稀烂的泥潭，水花四溅。泥浆里翻动着一道巨大脊背——那是这片泥潭的地主。",
            "type": "野外",
            "lv": 5,
            "npcs": [],
            "monsters": [
                ["m_boar_sow", "母猪兽", "tank", 5, ["ms_si_yao", "ms_hu_zai"], ["母猪皮"]]
            ],
            "elite": ["e_great_boar", "巨型野猪", "elite", 6, ["ms_chong_zhuang", "ms_jian_ta"], ["巨型野猪牙"]],
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        }
    ],
    "white_deer_forest": [
        {
            "id": "white_deer_forest_4",
            "name": "鹿鸣谷",
            "icon": "🦌",
            "desc": "白鹿之森深处一条洒满月光的幽谷，溪水淙淙。传说纯白的鹿曾在此鸣叫，呼唤迷途的旅人回头。",
            "type": "野外",
            "lv": 7,
            "npcs": [],
            "monsters": [
                ["m_snake", "毒蛇", "speedster", 7, ["ms_du_ya"], ["蛇皮"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "white_deer_forest_5",
            "name": "猎户旧屋",
            "icon": "🪵",
            "desc": "一栋废弃的猎户小木屋，炉灰早已冰冷，墙上挂着生锈的猎刀。野狗把这里当成了地盘，警惕地守在门口。",
            "type": "野外",
            "lv": 8,
            "npcs": [],
            "monsters": [
                ["m_wild_dog", "野狗", "dps", 8, ["ms_si_yao"], ["狗牙"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "white_deer_forest_6",
            "name": "密林深处",
            "icon": "🌲",
            "desc": "树冠遮天蔽日，藤蔓纠缠成墙。哥布林斥候在阴影里藏了暗哨，此处正是返回林间的捷径要害。",
            "type": "野外",
            "lv": 9,
            "npcs": [],
            "monsters": [
                ["m_goblin_scout", "哥布林斥候", "speedster", 9, ["ms_duan_dao"], ["哥布林耳朵", "哥布林耳坠", "山贼徽章"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            # v124 S57 荒废的药园：月光药园（噬根藤精 Lv.11 任务怪，掉落草药/月光草）
            "id": "white_deer_forest_7",
            "name": "月光药园",
            "icon": "🌿",
            "desc": "密林深处一座被藤蔓缠死的废园，篱笆朽烂，药畦早已荒芜。噬根藤精把根扎进畦土，护着园心那株通体泛着银光的月光兰。",
            "type": "野外",
            "lv": 11,
            "npcs": [],
            "monsters": [
                ["m_shi_gen_teng_jing", "噬根藤精", "dps", 11,
                 ["ms_teng_bian", "ms_gen_xu_chan_rao"], ["草药", "月光草"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        }
    ],
    "emerald_forest": [
        {
            "id": "emerald_forest_4",
            "name": "蜂语花丛",
            "icon": "🌸",
            "desc": "翡翠森林一片盛开花丛，巨型马蜂嗡嗡振翅。花蜜的气味浓郁得发甜，也藏着尖针与毒。",
            "type": "野外",
            "lv": 15,
            "npcs": [],
            "monsters": [
                ["m_hornet", "巨型马蜂", "speedster", 15, ["ms_du_ci"], ["蜂针"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "emerald_forest_5",
            "name": "林荫岔道",
            "icon": "🌳",
            "desc": "两棵交错的古树分岔成更深的林道，猎人洒下的粟米引出一条被人忽视的密径——直通溪边。",
            "type": "野外",
            "lv": 16,
            "npcs": [],
            "monsters": [
                ["m_goblin_warrior", "哥布林战士", "dps", 16, ["ms_duan_dao", "ms_dun_ji"], ["哥布林徽记"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "emerald_forest_6",
            "name": "苔径密室",
            "icon": "🍃",
            "desc": "藤蔓后掩着一方连猎人都罕至的苔藓石室，石壁上刻着古老的精灵文字。此地罕有人至，宝贝却不少。",
            "type": "野外",
            "lv": 17,
            "npcs": [],
            "monsters": [
                ["m_treant", "树人", "tank", 17, ["ms_teng_bian", "ms_ying_hua"], ["古木枝"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": True,
            "reveal": "explore:8"
        }
    ],
    "misty_swamp": [
        {
            "id": "misty_swamp_4",
            "name": "垂柳浅滩",
            "icon": "🌿",
            "desc": "迷雾沼泽一片垂柳低垂的浅滩，水边湿泥上印着鳄鱼拖行的痕迹。此处能绕回沼泽边缘。",
            "type": "野外",
            "lv": 20,
            "npcs": [],
            "monsters": [
                ["m_crocodile", "沼泽鳄鱼", "dps", 20, ["ms_yao_sui", "ms_shuai_wei"], ["鳄鱼皮"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "misty_swamp_5",
            "name": "雾心浮岛",
            "icon": "🏝️",
            "desc": "沼泽中心一块可涉足的土地，雾气在这里划出一个小小的圆形空档。岛心立着一根湿滑的巫术图腾。",
            "type": "野外",
            "lv": 21,
            "npcs": [],
            "monsters": [
                ["m_swamp_mage", "沼泽巫师", "healer", 21, ["ms_du_wu", "ms_shui_dan"], ["巫师法杖碎片"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "misty_swamp_6",
            "name": "沉陷墓穴",
            "icon": "🪦",
            "desc": "雾中一座半陷进淤泥的古墓，墓碑风化得只剩轮廓。旅者之冢守护着这片无人祭扫的安眠之地。",
            "type": "野外",
            "lv": 22,
            "npcs": [],
            "monsters": [
                ["m_big_slime", "大史莱姆", "tank", 22, ["ms_zhuang_ji", "ms_nian_ye"], ["大史莱姆核"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        }
    ],
    "hill_mine": [
        {
            "id": "hill_mine_4",
            "name": "塌方矿厅",
            "icon": "🕳️",
            "desc": "一道塌方堵死旧矿道，却也从矿墙裂口露出新的缝隙。岩屑间散落着半埋的矿车与遗落的矿镐。",
            "type": "野外",
            "lv": 26,
            "npcs": [],
            "monsters": [
                ["m_goblin_miner", "地精矿工", "dps", 26, ["ms_gao_ji"], ["矿石碎片"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore", "instance"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "hill_mine_5",
            "name": "暗河渡口",
            "icon": "🌊",
            "desc": "矿洞最深处有一条幽暗的地下河，水流在岩壁间轰鸣。对岸是一条只容一人侧身的窄道，通往更深处。",
            "type": "野外",
            "lv": 27,
            "npcs": [],
            "monsters": [
                ["m_rock_lizard", "岩石蜥蜴", "tank", 27, ["ms_yao_sui", "ms_ying_hua"], ["岩蜥鳞"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "hill_mine_6",
            "name": "苔藓密室",
            "icon": "💎",
            "desc": "矿壁上覆着发光苔藓，一处被落石挡住大半的天然洞窟。洞窟里似乎曾有人避乱躲藏，遗下零星财货。",
            "type": "野外",
            "lv": 28,
            "npcs": [],
            "monsters": [
                ["m_cave_bat", "洞穴蝙蝠", "speedster", 28, ["ms_fu_chong"], ["蝠翼"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": True,
            "reveal": "explore:10"
        }
    ],
    "harbor_docks": [
        {
            "id": "harbor_docks_4",
            "name": "吊车平台",
            "icon": "🏗️",
            "desc": "一座锈蚀的吊车高高耸立，悬臂下缓驶着运货的缆车。水鬼顺着缆绳攀爬，随时准备扑向下方的行人。",
            "type": "野外",
            "lv": 28,
            "npcs": [],
            "monsters": [
                ["m_water_ghost", "水鬼", "dps", 28, ["ms_zhao_ji"], ["水鬼之泪"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "harbor_docks_5",
            "name": "旧货仓夹层",
            "icon": "📦",
            "desc": "货仓上方的夹层堆满封箱的旧货，灰尘里有不少被遗忘的木箱。海盗在货堆间鬼祟翻找，不知在找什么。",
            "type": "野外",
            "lv": 29,
            "npcs": [],
            "monsters": [
                ["m_pirate", "海盗水手", "dps", 29, ["ms_wan_dao"], ["弯刀碎片"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "harbor_docks_6",
            "name": "灯塔残基",
            "icon": "🛎️",
            "desc": "断崖上一座早不再点灯的灯塔残基，塔身爬满盐霜。海风里似有船笛的回响，传说这里是某个老船长指航的起点。",
            "type": "野外",
            "lv": 30,
            "npcs": [],
            "monsters": [
                ["m_seagull", "大海鸥", "speedster", 30, ["ms_fu_chong"], ["海鸥羽毛"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        }
    ],
    "silver_valley": [
        {
            "id": "silver_valley_4",
            "name": "银砂浅滩",
            "icon": "🏞️",
            "desc": "谷中溪流转出的一片银砂浅滩，清澈的溪水下闪着银色矿砂。渔人常在此摸鱼，偶尔能捡到稀罕的银光碎块。",
            "type": "野外",
            "lv": 17,
            "npcs": [],
            "monsters": [
                ["m_river_deer", "溪鹿", "speedster", 17, ["ms_ji_chi"], ["溪鹿皮"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "silver_valley_5",
            "name": "崖间栈径",
            "icon": "🪜",
            "desc": "常年浸水的崖壁旁架着一段松动的木栈道，脚下是轰鸣的谷底溪流。侧身而过，便绕回了谷口。",
            "type": "野外",
            "lv": 18,
            "npcs": [],
            "monsters": [
                ["m_valley_goat", "谷山羊", "dps", 18, ["ms_ding_zhuang"], ["山羊角"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "silver_valley_6",
            "name": "谷底深潭",
            "icon": "🌫️",
            "desc": "峡谷最深处的一汪幽深水潭，水面凝着薄雾。溪蜥盘在潭边湿石上，深潭里似乎还有什么在缓缓游动。",
            "type": "野外",
            "lv": 19,
            "npcs": [],
            "monsters": [
                ["m_stream_lizard", "溪蜥", "tank", 19, ["ms_yao_sui", "ms_ying_hua"], ["溪蜥鳞"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        }
    ],
    "windmill_plain": [
        {
            "id": "windmill_plain_4",
            "name": "麦垛田垄",
            "icon": "🌾",
            "desc": "成垛的麦秆堆在田垄边，干燥的麦香扑鼻。平原兔在垛缝间钻来钻去，偶尔惊起一阵窸窣。",
            "type": "野外",
            "lv": 22,
            "npcs": [],
            "monsters": [
                ["m_plain_rabbit", "平原兔", "speedster", 22, ["ms_ji_pao"], ["兔皮"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "windmill_plain_5",
            "name": "停转风车",
            "icon": "🌀",
            "desc": "一架叶片卡死、早已停转的老风车，磨坊主的驴车歪在门边。风车野猪在墙根下焦躁地拱土。",
            "type": "野外",
            "lv": 23,
            "npcs": [],
            "monsters": [
                ["m_windmill_boar", "风车野猪", "dps", 23, ["ms_chong_zhuang"], ["野猪牙"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "windmill_plain_6",
            "name": "草海深处",
            "icon": "🌊",
            "desc": "草浪在这里高过人头，风一过便层层涌起。平原狼王的脚印深陷在软泥里，这一片草海是它巡猎的领地。",
            "type": "野外",
            "lv": 24,
            "npcs": [],
            "monsters": [
                ["m_plain_ox", "平原野牛", "tank", 24, ["ms_chong_zhuang", "ms_jian_ta"], ["牛角"]]
            ],
            "elite": ["e_plain_wolf", "平原狼王", "elite", 25, ["ms_si_yao", "ms_hao_jiao"], ["狼王牙"]],
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        }
    ],
    "rockfall_gorge": [
        {
            "id": "rockfall_gorge_4",
            "name": "碎石坡",
            "icon": "🪨",
            "desc": "一处松动的碎石坡，踩下去便簌簌滑落。岩鼠在这里筑了窝，石缝里偶尔能看到被风吹来的物件。",
            "type": "野外",
            "lv": 9,
            "npcs": [],
            "monsters": [
                ["m_rock_rat", "岩鼠", "speedster", 9, ["ms_ken_yao"], ["岩鼠牙"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "rockfall_gorge_5",
            "name": "断桥对岸",
            "icon": "🌉",
            "desc": "一座早已断裂的木桥横在深涧上，对岸的石台正对峡谷栈道。跳过去，便省下一大段弯路。",
            "type": "野外",
            "lv": 10,
            "npcs": [],
            "monsters": [
                ["m_mountain_goat", "岩羊", "dps", 10, ["ms_ding_zhuang"], ["岩羊毛"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "rockfall_gorge_6",
            "name": "落岩裂隙",
            "icon": "🕳️",
            "desc": "崖壁上一道窄得只能侧身的天然裂隙，裂隙尽头豁然开朗。石蜥蜴盘踞在岩缝里，防备着一切闯入者。",
            "type": "野外",
            "lv": 11,
            "npcs": [],
            "monsters": [
                ["m_cave_lizard", "石蜥蜴", "tank", 11, ["ms_yao_sui", "ms_ying_hua"], ["石蜥鳞"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": True,
            "reveal": "explore:6"
        }
    ],
    "boar_ridge": [
        {
            "id": "boar_ridge_4",
            "name": "灌木陷阱带",
            "icon": "🌿",
            "desc": "猎人在山脚布下的一整片捕兽陷阱，木桩与套索隐在灌木后。母猪兽嗅着陷阱外的饵食，踌躇不前。",
            "type": "野外",
            "lv": 11,
            "npcs": [],
            "monsters": [
                ["m_wild_boar", "野猪", "dps", 11, ["ms_chong_zhuang"], ["野猪牙"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "boar_ridge_5",
            "name": "蹭皮古树",
            "icon": "🌳",
            "desc": "一棵被成年野猪蹭得树皮斑驳的古树，树下积着厚厚一层泥浆。母猪兽常带幼崽来这里，见到人影便低吼警告。",
            "type": "野外",
            "lv": 12,
            "npcs": [],
            "monsters": [
                ["m_boar_sow", "母猪兽", "tank", 12, ["ms_si_yao", "ms_hu_zai"], ["母猪皮"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "boar_ridge_6",
            "name": "密林跳径",
            "icon": "🧗",
            "desc": "一条几乎被枝叶吞没的隐秘跳径，踩着凸起的虬根攀爬，竟能直通岭顶巢穴——是猎人们口口相传的老路。",
            "type": "野外",
            "lv": 13,
            "npcs": [],
            "monsters": [
                ["m_hornet", "巨型马蜂", "speedster", 13, ["ms_du_ci"], ["蜂针"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        }
    ],
    "silver_wind_road": [
        {
            "id": "silver_wind_road_3",
            "name": "驿站后院",
            "icon": "🏟️",
            "desc": "银风驿站后开辟的一方土院，拴着换骡的商队牲口。货郎在墙根摆开杂物摊叫卖，森林狼偶尔趁夜从篱笆缝隙摸进来。",
            "type": "野外",
            "lv": 9,
            "npcs": [],
            "monsters": [
                ["m_forest_wolf", "森林狼", "dps", 9, ["ms_si_yao", "ms_hao_jiao"], ["狼皮"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "silver_wind_road_4",
            "name": "野狗岔道",
            "icon": "🛤️",
            "desc": "商道旁一条被野狗踩秃的岔道，通进路边密林，能绕回商道口。石蜥蜴常窝在岔道口的石块下晒太阳。",
            "type": "野外",
            "lv": 10,
            "npcs": [],
            "monsters": [
                ["m_wild_dog", "野狗", "dps", 10, ["ms_si_yao"], ["狗牙"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": True,
            "reveal": "explore:5"
        }
    ],
    # ============================ 中域·圣光之心 ============================
    "silver_river": [
        {
            "id": "silver_river_4",
            "name": "芦苇回湾",
            "icon": "🎋",
            "desc": "银铃河一段被芦苇围成的回湾，水流在这里放缓。鲛人常藏身苇丛，歌声忽近忽远。",
            "type": "野外",
            "lv": 32,
            "npcs": [],
            "monsters": [
                ["m_mermaid", "鲛人", "dps", 32, ["ms_cha_ji", "ms_shui_dan"], ["鲛人鳞"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "silver_river_5",
            "name": "水下石阶",
            "icon": "🪜",
            "desc": "河底一段被冲刷出级的白石阶，洪水退后才露出一角。踩着湿滑的石阶能涉水抄近路，河龙在深水处缓慢游弋。",
            "type": "野外",
            "lv": 33,
            "npcs": [],
            "monsters": [
                ["m_river_spirit", "水精灵", "healer", 33, ["ms_shui_dan", "ms_zhi_liao"], ["水精灵泪"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "silver_river_6",
            "name": "雁回高台",
            "icon": "🕊️",
            "desc": "河岸一处凸起的高台，是候鸟迁徙时歇脚的驿站。高台上的野雁羽落了一地，站在此处能望见整条银铃河的走势。",
            "type": "野外",
            "lv": 34,
            "npcs": [],
            "monsters": [
                ["m_river_dragon", "河龙", "tank", 34, ["ms_shui_xi", "ms_shuai_wei"], ["河龙鳞", "鼠狮核心"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": True,
            "reveal": "explore:12"
        }
    ],
    "gold_plain": [
        {
            "id": "gold_plain_4",
            "name": "晒粮场",
            "icon": "🌾",
            "desc": "金穗平原一处废弃的晒粮场，石碾与麦垛散在晒场上。盗贼在麦垛间藏身，望风的人远远打着唿哨。",
            "type": "野外",
            "lv": 42,
            "npcs": [],
            "monsters": [
                ["m_bandit", "盗贼", "speedster", 42, ["ms_duan_jian", "ms_tou_qie"], ["盗贼面巾", "山贼徽章"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "gold_plain_5",
            "name": "荒庙残垣",
            "icon": "🏛️",
            "desc": "平原深处一座被荒草吞没的古老庙宇，梁柱倾颓，台阶裂缝里钻出野花。草原狼在残垣间追逐捕猎。",
            "type": "野外",
            "lv": 43,
            "npcs": [],
            "monsters": [
                ["m_steppe_wolf", "草原狼", "dps", 43, ["ms_si_yao"], ["草原狼皮"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "gold_plain_6",
            "name": "北坡麦缘",
            "icon": "🌤️",
            "desc": "金穗平原北坡的麦田尽头是一道斜坡，站在坡顶能望见晨曦城的塔尖。这是个抄回平原边缘的近路。",
            "type": "野外",
            "lv": 44,
            "npcs": [],
            "monsters": [
                ["m_wild_bull", "野牛", "tank", 44, ["ms_chong_zhuang"], ["牛角"]]
            ],
            "elite": ["e_bandit_leader", "盗贼头目·黑鸦", "elite", 45, ["ms_duan_jian", "ms_yan_wu"], ["黑鸦披风"]],
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        }
    ],
    "white_abbey": [
        {
            "id": "white_abbey_4",
            "name": "苔园回廊",
            "icon": "🍀",
            "desc": "修道院一侧被青苔占领的荒废回廊，石柱间挂着蛛网。腐蚀修女的脚步声在廊间回荡，久久不肯散去。",
            "type": "野外",
            "lv": 40,
            "npcs": [],
            "monsters": [
                ["m_corrupted_nun", "腐蚀修女", "healer", 40, ["ms_an_ying_zhi_liao", "ms_fu_shi_shu"], ["染黑圣铃", "染黑玫瑰"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "white_abbey_5",
            "name": "枯井地洞",
            "icon": "🕳️",
            "desc": "庭院角落一口早已干涸的深井，井底侧壁破开一个黑洞。石魔像在井底处巡弋，死死守着这道不为人知的入口。",
            "type": "野外",
            "lv": 41,
            "npcs": [],
            "monsters": [
                ["m_stone_golem", "石魔像", "tank", 41, ["ms_zhong_ji", "ms_ying_hua"], ["魔像核心"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "white_abbey_6",
            "name": "圣龛密室",
            "icon": "🕯️",
            "desc": "回廊尽头一道可推动的石壁后，藏着修道院最深的密室，圣龛前烛火长明。守护者的低语就从这里透出来。",
            "type": "野外",
            "lv": 42,
            "npcs": [],
            "monsters": [
                ["m_corrupted_nun", "腐蚀修女", "healer", 42, ["ms_an_ying_zhi_liao", "ms_fu_shi_shu"], ["染黑圣铃"]]
            ],
            "elite": ["e_abbey_guardian", "修道院守护者", "elite", 43, ["ms_zhong_ji", "ms_sheng_guang_zhan_bei_wu_ran"], ["守护者碎片"]],
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": True,
            "reveal": "explore:12"
        }
    ],
    "ironshield_hills": [
        {
            "id": "ironshield_hills_4",
            "name": "铁砧石岗",
            "icon": "🪨",
            "desc": "丘陵中一片寸草不生的铁黑色石岗，岩面坚硬如铁。秃鹫在岩顶盘旋，等着下方猎物的动静。",
            "type": "野外",
            "lv": 38,
            "npcs": [],
            "monsters": [
                ["m_hill_wolf", "丘陵狼", "dps", 38, ["ms_si_yao", "ms_hao_jiao"], ["丘陵狼皮", "座狼犬齿"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "ironshield_hills_5",
            "name": "哨塔旧址",
            "icon": "🗼",
            "desc": "一座塌了顶的废弃哨塔立在丘陵脊线上，旗杆东倒西歪。丘陵狼在塔基下歇脚，把这里当成了巢穴入口。",
            "type": "野外",
            "lv": 39,
            "npcs": [],
            "monsters": [
                ["m_hill_vulture", "秃鹫", "speedster", 39, ["ms_fu_chong"], ["秃鹫羽"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "ironshield_hills_6",
            "name": "铁脊岩缝",
            "icon": "🕳️",
            "desc": "丘陵顶一处被风吹开的岩缝，铁甲野猪在此拱出窝洞。沿着岩缝能摸回丘陵脚，是条只闻其名的密路。",
            "type": "野外",
            "lv": 40,
            "npcs": [],
            "monsters": [
                ["m_iron_boar", "铁甲野猪", "tank", 40, ["ms_chong_zhuang", "ms_tie_pi"], ["铁甲猪皮"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": True,
            "reveal": "explore:10"
        }
    ],
    "old_battlefield": [
        {
            "id": "old_battlefield_4",
            "name": "断矛冢",
            "icon": "⚔️",
            "desc": "一片插满断矛与残旗的土丘，是百族战争时无名士兵的合葬之地。锈甲亡兵在冢间默默巡行。",
            "type": "野外",
            "lv": 42,
            "npcs": [],
            "monsters": [
                ["m_rust_warrior", "锈甲亡兵", "dps", 42, ["ms_xiu_jian"], ["锈甲碎片"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "old_battlefield_5",
            "name": "掩埋壕沟",
            "icon": "🕳️",
            "desc": "一段被土掩了一半的废弃壕沟，战场幽魂在沟底游荡。沟沿的缺口能直通战壕区，省去绕路。",
            "type": "野外",
            "lv": 43,
            "npcs": [],
            "monsters": [
                ["m_field_ghost", "战场幽魂", "speedster", 43, ["ms_chuan_shen", "ms_ai_hao"], ["幽魂尘"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "old_battlefield_6",
            "name": "将旗台下",
            "icon": "🚩",
            "desc": "遗址中央一座残破的将旗石台，台上旗杆早已折断。传说战将的遗物埋藏在台下，故百族战将·亡影的幽影常在附近徘徊。",
            "type": "野外",
            "lv": 44,
            "npcs": [],
            "monsters": [
                ["m_war_golem", "战争魔像(残)", "tank", 44, ["ms_zhong_ji", "ms_tie_bi"], ["魔像残核"]]
            ],
            "elite": ["e_battle_lord", "百族战将·亡影", "elite", 45, ["ms_zhan_hou", "ms_an_ying_zhan"], ["亡影铠甲片"]],
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        }
    ],
    "border_castle": [
        {
            "id": "border_castle_4",
            "name": "外堡马厩",
            "icon": "🐴",
            "desc": "堡墙外一片破败的马厩，栏杆已垮了大半。兽人劫掠者把这里当成了歇脚点，马粪与兽毛混着尘土的气味冲鼻。",
            "type": "野外",
            "lv": 52,
            "npcs": [],
            "monsters": [
                ["m_orc_raider", "兽人劫掠者", "dps", 52, ["ms_fu_ji"], ["兽人斧刃", "兽人獠牙"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "border_castle_5",
            "name": "角楼废墟",
            "icon": "🏰",
            "desc": "堡外一座倒塌的角楼废墟，瓦砾里埋着投石机的铁件。战争机器的断械横在瓦砾间，早已锈成一堆。",
            "type": "野外",
            "lv": 53,
            "npcs": [],
            "monsters": [
                ["m_war_machine", "战争机器", "tank", 53, ["ms_chong_zhuang", "ms_huo_pao"], ["战争机器零件"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "border_castle_6",
            "name": "藏兵甬道",
            "icon": "🕳️",
            "desc": "堡墙下一条隐蔽的藏兵甬道，直通堡内。兽人战士在甬道里设了暗哨，只有硬闯一路。",
            "type": "野外",
            "lv": 54,
            "npcs": [],
            "monsters": [
                ["m_orc_raider", "兽人劫掠者", "dps", 54, ["ms_fu_ji"], ["兽人战徽"]]
            ],
            "elite": ["e_orc_warrior", "兽人战士", "elite", 55, ["ms_fu_ji", "ms_zhan_hou"], ["兽人战徽"]],
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": True,
            "reveal": "explore:13"
        }
    ],
    "west_ridge_wilds": [
        {
            "id": "west_ridge_wilds_4",
            "name": "残墙穴地",
            "icon": "🧱",
            "desc": "西岭荒原一处倒塌的旧墙，墙根掏出一窝野洞。丘陵狼在洞外逡巡，洞里隐约传来幼崽的呜咽。",
            "type": "野外",
            "lv": 36,
            "npcs": [],
            "monsters": [
                ["m_hill_wolf", "丘陵狼", "dps", 36, ["ms_si_yao", "ms_hao_jiao"], ["丘陵狼皮", "座狼犬齿"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "west_ridge_wilds_5",
            "name": "风蚀石林",
            "icon": "🗿",
            "desc": "一片被大风吹蚀得奇形怪状的石林，石柱高出荒原。草原狼在石林间穿梭，这里能抄近路回落霞坡。",
            "type": "野外",
            "lv": 37,
            "npcs": [],
            "monsters": [
                ["m_wild_bull", "野牛", "tank", 37, ["ms_chong_zhuang"], ["牛角"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "west_ridge_wilds_6",
            "name": "孤坟岗",
            "icon": "🪦",
            "desc": "荒原一处隆起的神秘孤坟，坟前竖着一块无字碑。古道骷髅在这片坟地出没，似乎格外执拗地守着什么。",
            "type": "野外",
            "lv": 38,
            "npcs": [],
            "monsters": [
                ["m_road_skeleton", "古道骷髅", "dps", 38, ["ms_jian_ji"], ["碎骨"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": True,
            "reveal": "explore:9"
        }
    ],
    "dusk_ridge_road": [
        {
            "id": "dusk_ridge_road_4",
            "name": "碎石坡道",
            "icon": "🪨",
            "desc": "古道旁一条被落石冲稀的坡道，脚下的碎石打滑。战场幽魂在坡道两端游荡，把这里守着严实。",
            "type": "野外",
            "lv": 44,
            "npcs": [],
            "monsters": [
                ["m_field_ghost", "战场幽魂", "speedster", 44, ["ms_chuan_shen", "ms_ai_hao"], ["幽魂尘"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "dusk_ridge_road_5",
            "name": "破败寇寨",
            "icon": "⛺",
            "desc": "古道上一个早已废弃的盗寇山寨，栅栏歪斜，灶膛里积着冷灰。古墓幽灵在白骨间游移，像在数着当年的伤亡。",
            "type": "野外",
            "lv": 45,
            "npcs": [],
            "monsters": [
                ["m_grave_ghost", "古墓幽灵", "speedster", 45, ["ms_chuan_shen", "ms_ai_hao"], ["幽灵之尘", "鬼魂精华"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "dusk_ridge_road_6",
            "name": "隘口密道",
            "icon": "🕳️",
            "desc": "垭口侧壁一道被藤蔓盖住的密道，直通山腹又绕回古道。战争魔像的残骸堵在密道口，看守着这道要害。",
            "type": "野外",
            "lv": 46,
            "npcs": [],
            "monsters": [
                ["m_war_golem", "战争魔像(残)", "tank", 46, ["ms_zhong_ji", "ms_tie_bi"], ["魔像残核"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": True,
            "reveal": "explore:13"
        }
    ],
    "king_road": [
        {
            "id": "king_road_4",
            "name": "殉葬石室",
            "icon": "🪦",
            "desc": "古道旁一处被掘开的殉葬石室，白骨散落，陪葬的陶罐碎了一地。古墓幽灵在石室里无声地盘旋。",
            "type": "野外",
            "lv": 44,
            "npcs": [],
            "monsters": [
                ["m_grave_ghost", "古墓幽灵", "speedster", 44, ["ms_chuan_shen", "ms_ai_hao"], ["幽灵之尘", "鬼魂精华"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "king_road_5",
            "name": "石狮岔道",
            "icon": "🦁",
            "desc": "古道上一对掉了一头的石狮分守左右，岔道从狮下延展开去。古道骷髅在这里排着稀疏的队，沿着岔道走向王陵。",
            "type": "野外",
            "lv": 45,
            "npcs": [],
            "monsters": [
                ["m_road_skeleton", "古道骷髅", "dps", 45, ["ms_jian_ji"], ["碎骨"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "king_road_6",
            "name": "回廊密道",
            "icon": "🕳️",
            "desc": "道旁一段被苔藓掩住的矮回廊，尽头通向王陵侧的暗门。古代骑士的铠甲立在密道口，像是永远驻守着一道防线。",
            "type": "野外",
            "lv": 46,
            "npcs": [],
            "monsters": [
                ["m_ancient_knight", "古代骑士", "tank", 46, ["ms_jian_ji", "ms_tie_bi"], ["锈甲碎片"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": True,
            "reveal": "explore:13"
        }
    ],
    "dawn_cathedral": [
        {
            "id": "dawn_cathedral_4",
            "name": "侧翼墓园",
            "icon": "🪦",
            "desc": "大圣堂侧翼的一方荒废墓园，石墓碑东倒西歪。暗影教徒常在墓园里集会，用碑影遮住身影。",
            "type": "野外",
            "lv": 36,
            "npcs": [],
            "monsters": [
                ["m_cultist", "暗影教徒", "dps", 36, ["ms_an_ying_dan"], ["暗影徽记", "暗影碎片"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "dawn_cathedral_5",
            "name": "钟塔夹梯",
            "icon": "🛎️",
            "desc": "通往钟塔的狭窄夹梯盘旋向上，墙体斑驳。圣殿守卫魔像堵在楼梯转角，一步一阶地压下来。",
            "type": "野外",
            "lv": 37,
            "npcs": [],
            "monsters": [
                ["m_temple_guard", "圣殿守卫(魔像)", "tank", 37, ["ms_zhong_ji", "ms_tie_bi"], ["圣殿铁块", "圣光结晶"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "dawn_cathedral_6",
            "name": "圣辉暗室",
            "icon": "🕯️",
            "desc": "回廊深处一道几乎看不出暗门，室内烛火长明，墙上画满圣辉与暗影交缠的壁画。这是大圣堂最不为人知的一角。",
            "type": "野外",
            "lv": 38,
            "npcs": [],
            "monsters": [
                ["m_cultist", "暗影教徒", "dps", 38, ["ms_an_ying_dan"], ["暗影徽记"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": True,
            "reveal": "explore:12"
        }
    ],
    "knight_yard": [
        {
            "id": "knight_yard_4",
            "name": "木人棚",
            "icon": "🏟️",
            "desc": "训练场边一排放满训练木人的雨棚，木人身上刀痕累累。训练木桩被重修得桩桩坚硬，磕一剑能震得手臂发麻。",
            "type": "野外",
            "lv": 36,
            "npcs": [],
            "monsters": [
                ["m_training_dummy", "训练木桩", "dps", 36, ["ms_pi_kan"], ["木桩碎片"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "knight_yard_5",
            "name": "障碍沙场",
            "icon": "🏳️",
            "desc": "一片铺满沙地的障碍训练场，倒刺桩与跨栏高低错落。见习骑士们一遍遍冲过，泥渍混着汗水。",
            "type": "野外",
            "lv": 37,
            "npcs": [],
            "monsters": [
                ["m_knight_apprentice", "见习骑士", "dps", 37, ["ms_jian_ji"], ["骑士徽记"]]
            ],
            "elite": None,
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": False,
            "reveal": None
        },
        {
            "id": "knight_yard_6",
            "name": "武器库密室",
            "icon": "🗡️",
            "desc": "训练场侧壁一道钢铁门后，是骑士团密藏的武器库。训练魔像守在库前，任何未经允许的手都休想碰那些兵刃。",
            "type": "野外",
            "lv": 38,
            "npcs": [],
            "monsters": [
                ["m_training_golem", "训练魔像", "tank", 38, ["ms_zhong_ji", "ms_tie_bi"], ["魔像核心"]]
            ],
            "elite": ["e_knight_instructor", "骑士教官", "elite", 39, ["ms_jian_ji", "ms_zhan_hou"], ["教官之剑"]],
            "boss": None,
            "funcs": ["explore"],
            "shop": False,
            "healer": False,
            "hidden": True,
            "reveal": "explore:11"
        }
    ],
}


# ---------------------------------------------------------------------------
# 二、SUBAREA_LINKS：全房间网状连接（含旧房间）
# ---------------------------------------------------------------------------
# 双向对称；_1 入口可达全图(隐藏除外)；除死胡同外每房>=2连接；死胡同=1连接(仅1个)；相邻等级差<=15。
# ---------------------------------------------------------------------------
SUBAREA_LINKS = {
    # ------------------- 南境·绿野 -------------------
    "oak_plain": {
        "oak_plain_1": ["oak_plain_2", "oak_plain_4"],
        "oak_plain_2": ["oak_plain_1", "oak_plain_3", "oak_plain_5"],
        "oak_plain_3": ["oak_plain_2", "oak_plain_5"],
        "oak_plain_4": ["oak_plain_1", "oak_plain_5", "oak_plain_6"],
        "oak_plain_5": ["oak_plain_2", "oak_plain_3", "oak_plain_4"],
        "oak_plain_6": ["oak_plain_4"],  # 死胡同-野猪泥潭(elite)
    },
    "white_deer_forest": {
        "white_deer_forest_1": ["white_deer_forest_2", "white_deer_forest_4"],
        "white_deer_forest_2": ["white_deer_forest_1", "white_deer_forest_3", "white_deer_forest_5"],
        "white_deer_forest_3": ["white_deer_forest_2", "white_deer_forest_4"],
        "white_deer_forest_4": ["white_deer_forest_1", "white_deer_forest_3", "white_deer_forest_6"],
        "white_deer_forest_5": ["white_deer_forest_2", "white_deer_forest_6"],
        "white_deer_forest_6": ["white_deer_forest_4", "white_deer_forest_5", "white_deer_forest_7"],
        "white_deer_forest_7": ["white_deer_forest_6"],  # 死胡同-月光药园(v124 S57)
    },
    "emerald_forest": {
        "emerald_forest_1": ["emerald_forest_2", "emerald_forest_4"],
        "emerald_forest_2": ["emerald_forest_1", "emerald_forest_3", "emerald_forest_5"],
        "emerald_forest_3": ["emerald_forest_2", "emerald_forest_5"],
        "emerald_forest_4": ["emerald_forest_1", "emerald_forest_5", "emerald_forest_6"],
        "emerald_forest_5": ["emerald_forest_2", "emerald_forest_3", "emerald_forest_4", "emerald_forest_6"],
        "emerald_forest_6": ["emerald_forest_4", "emerald_forest_5"],  # 隐藏房(探索8)-苔径密室
    },
    "misty_swamp": {
        "misty_swamp_1": ["misty_swamp_2", "misty_swamp_4"],
        "misty_swamp_2": ["misty_swamp_1", "misty_swamp_3", "misty_swamp_5"],
        "misty_swamp_3": ["misty_swamp_2", "misty_swamp_4"],
        "misty_swamp_4": ["misty_swamp_1", "misty_swamp_3", "misty_swamp_6"],
        "misty_swamp_5": ["misty_swamp_2", "misty_swamp_6"],
        "misty_swamp_6": ["misty_swamp_4", "misty_swamp_5"],  # 捷径(沉陷墓穴)-traveler_grave
    },
    "hill_mine": {
        "hill_mine_1": ["hill_mine_2", "hill_mine_4"],
        "hill_mine_2": ["hill_mine_1", "hill_mine_3", "hill_mine_5"],
        "hill_mine_3": ["hill_mine_2", "hill_mine_4"],
        "hill_mine_4": ["hill_mine_1", "hill_mine_3", "hill_mine_6"],
        "hill_mine_5": ["hill_mine_2", "hill_mine_6"],
        "hill_mine_6": ["hill_mine_4", "hill_mine_5"],  # 隐藏房(探索10)-苔藓密室
    },
    "harbor_docks": {
        "harbor_docks_1": ["harbor_docks_2", "harbor_docks_4"],
        "harbor_docks_2": ["harbor_docks_1", "harbor_docks_3", "harbor_docks_5"],
        "harbor_docks_3": ["harbor_docks_2", "harbor_docks_4"],
        "harbor_docks_4": ["harbor_docks_1", "harbor_docks_3", "harbor_docks_6"],
        "harbor_docks_5": ["harbor_docks_2", "harbor_docks_6"],
        "harbor_docks_6": ["harbor_docks_4", "harbor_docks_5"],  # 捷径(灯塔残基)-shipwreck
    },
    "silver_valley": {
        "silver_valley_1": ["silver_valley_2", "silver_valley_4"],
        "silver_valley_2": ["silver_valley_1", "silver_valley_3", "silver_valley_5"],
        "silver_valley_3": ["silver_valley_2", "silver_valley_4"],
        "silver_valley_4": ["silver_valley_1", "silver_valley_3", "silver_valley_6"],
        "silver_valley_5": ["silver_valley_2", "silver_valley_6"],
        "silver_valley_6": ["silver_valley_4", "silver_valley_5"],  # 捷径(谷底深潭)
    },
    "windmill_plain": {
        "windmill_plain_1": ["windmill_plain_2", "windmill_plain_4"],
        "windmill_plain_2": ["windmill_plain_1", "windmill_plain_3", "windmill_plain_5"],
        "windmill_plain_3": ["windmill_plain_2", "windmill_plain_4"],
        "windmill_plain_4": ["windmill_plain_1", "windmill_plain_3", "windmill_plain_6"],
        "windmill_plain_5": ["windmill_plain_2", "windmill_plain_6"],
        "windmill_plain_6": ["windmill_plain_4", "windmill_plain_5"],  # 草海深处(elite)捷径
    },
    "rockfall_gorge": {
        "rockfall_gorge_1": ["rockfall_gorge_2", "rockfall_gorge_4"],
        "rockfall_gorge_2": ["rockfall_gorge_1", "rockfall_gorge_3", "rockfall_gorge_5"],
        "rockfall_gorge_3": ["rockfall_gorge_2", "rockfall_gorge_4"],
        "rockfall_gorge_4": ["rockfall_gorge_1", "rockfall_gorge_3", "rockfall_gorge_6"],
        "rockfall_gorge_5": ["rockfall_gorge_2", "rockfall_gorge_6"],
        "rockfall_gorge_6": ["rockfall_gorge_4", "rockfall_gorge_5"],  # 隐藏房(探索6)-落岩裂隙
    },
    "boar_ridge": {
        "boar_ridge_1": ["boar_ridge_2", "boar_ridge_4"],
        "boar_ridge_2": ["boar_ridge_1", "boar_ridge_3", "boar_ridge_5"],
        "boar_ridge_3": ["boar_ridge_2", "boar_ridge_4"],
        "boar_ridge_4": ["boar_ridge_1", "boar_ridge_3", "boar_ridge_6"],
        "boar_ridge_5": ["boar_ridge_2", "boar_ridge_6"],
        "boar_ridge_6": ["boar_ridge_4", "boar_ridge_5"],  # 捷径(密林跳径直通岭顶)
    },
    "silver_wind_road": {
        "silver_wind_road_1": ["silver_wind_road_2", "silver_wind_road_4"],
        "silver_wind_road_2": ["silver_wind_road_1", "silver_wind_road_3", "silver_wind_road_4"],
        "silver_wind_road_3": ["silver_wind_road_2", "silver_wind_road_4"],  # 驿站后院(岔路捷径)
        "silver_wind_road_4": ["silver_wind_road_1", "silver_wind_road_2", "silver_wind_road_3"],  # 隐藏房(探索5)-野狗岔道(岔路)
    },
    # ------------------- 中域·圣光之心 -------------------
    "silver_river": {
        "silver_river_1": ["silver_river_2", "silver_river_4"],
        "silver_river_2": ["silver_river_1", "silver_river_3", "silver_river_5"],
        "silver_river_3": ["silver_river_2", "silver_river_4"],
        "silver_river_4": ["silver_river_1", "silver_river_3", "silver_river_6"],
        "silver_river_5": ["silver_river_2", "silver_river_6"],
        "silver_river_6": ["silver_river_4", "silver_river_5"],  # 隐藏房(探索12)-雁回高台
    },
    "gold_plain": {
        "gold_plain_1": ["gold_plain_2", "gold_plain_4"],
        "gold_plain_2": ["gold_plain_1", "gold_plain_3", "gold_plain_5"],
        "gold_plain_3": ["gold_plain_2", "gold_plain_4"],
        "gold_plain_4": ["gold_plain_1", "gold_plain_3", "gold_plain_6"],
        "gold_plain_5": ["gold_plain_2", "gold_plain_6"],
        "gold_plain_6": ["gold_plain_4", "gold_plain_5"],  # 北坡麦缘(elite)
    },
    "white_abbey": {
        "white_abbey_1": ["white_abbey_2", "white_abbey_4"],
        "white_abbey_2": ["white_abbey_1", "white_abbey_3", "white_abbey_5"],
        "white_abbey_3": ["white_abbey_2", "white_abbey_4"],
        "white_abbey_4": ["white_abbey_1", "white_abbey_3", "white_abbey_6"],
        "white_abbey_5": ["white_abbey_2", "white_abbey_6"],
        "white_abbey_6": ["white_abbey_4", "white_abbey_5"],  # 隐藏房(探索12)-圣龛密室(elite)
    },
    "ironshield_hills": {
        "ironshield_hills_1": ["ironshield_hills_2", "ironshield_hills_4"],
        "ironshield_hills_2": ["ironshield_hills_1", "ironshield_hills_3", "ironshield_hills_5"],
        "ironshield_hills_3": ["ironshield_hills_2", "ironshield_hills_4"],
        "ironshield_hills_4": ["ironshield_hills_1", "ironshield_hills_3", "ironshield_hills_6"],
        "ironshield_hills_5": ["ironshield_hills_2", "ironshield_hills_6"],
        "ironshield_hills_6": ["ironshield_hills_4", "ironshield_hills_5"],  # 隐藏房(探索10)-铁脊岩缝
    },
    "old_battlefield": {
        "old_battlefield_1": ["old_battlefield_2", "old_battlefield_4"],
        "old_battlefield_2": ["old_battlefield_1", "old_battlefield_3", "old_battlefield_5"],
        "old_battlefield_3": ["old_battlefield_2", "old_battlefield_4"],
        "old_battlefield_4": ["old_battlefield_1", "old_battlefield_3", "old_battlefield_6"],
        "old_battlefield_5": ["old_battlefield_2", "old_battlefield_6"],
        "old_battlefield_6": ["old_battlefield_4", "old_battlefield_5"],  # 将旗台下(elite)
    },
    "border_castle": {
        "border_castle_1": ["border_castle_2", "border_castle_4"],
        "border_castle_2": ["border_castle_1", "border_castle_3", "border_castle_5"],
        "border_castle_3": ["border_castle_2", "border_castle_4"],
        "border_castle_4": ["border_castle_1", "border_castle_3", "border_castle_6"],
        "border_castle_5": ["border_castle_2", "border_castle_6"],
        "border_castle_6": ["border_castle_4", "border_castle_5"],  # 隐藏房(探索13)-藏兵甬道(elite)
    },
    "west_ridge_wilds": {
        "west_ridge_wilds_1": ["west_ridge_wilds_2", "west_ridge_wilds_4"],
        "west_ridge_wilds_2": ["west_ridge_wilds_1", "west_ridge_wilds_3", "west_ridge_wilds_5"],
        "west_ridge_wilds_3": ["west_ridge_wilds_2", "west_ridge_wilds_4"],
        "west_ridge_wilds_4": ["west_ridge_wilds_1", "west_ridge_wilds_3", "west_ridge_wilds_6"],
        "west_ridge_wilds_5": ["west_ridge_wilds_2", "west_ridge_wilds_6"],
        "west_ridge_wilds_6": ["west_ridge_wilds_4", "west_ridge_wilds_5"],  # 隐藏房(探索9)-孤坟岗 traveler_grave
    },
    "dusk_ridge_road": {
        "dusk_ridge_road_1": ["dusk_ridge_road_2", "dusk_ridge_road_4"],
        "dusk_ridge_road_2": ["dusk_ridge_road_1", "dusk_ridge_road_3", "dusk_ridge_road_5"],
        "dusk_ridge_road_3": ["dusk_ridge_road_2", "dusk_ridge_road_4"],
        "dusk_ridge_road_4": ["dusk_ridge_road_1", "dusk_ridge_road_3", "dusk_ridge_road_6"],
        "dusk_ridge_road_5": ["dusk_ridge_road_2", "dusk_ridge_road_6"],
        "dusk_ridge_road_6": ["dusk_ridge_road_4", "dusk_ridge_road_5"],  # 隐藏房(探索13)-隘口密道
    },
    "king_road": {
        "king_road_1": ["king_road_2", "king_road_4"],
        "king_road_2": ["king_road_1", "king_road_3", "king_road_5"],
        "king_road_3": ["king_road_2", "king_road_4"],
        "king_road_4": ["king_road_1", "king_road_3", "king_road_6"],
        "king_road_5": ["king_road_2", "king_road_6"],
        "king_road_6": ["king_road_4", "king_road_5"],  # 隐藏房(探索13)-回廊密道
    },
    "dawn_cathedral": {
        "dawn_cathedral_1": ["dawn_cathedral_2", "dawn_cathedral_4"],
        "dawn_cathedral_2": ["dawn_cathedral_1", "dawn_cathedral_3", "dawn_cathedral_5"],
        "dawn_cathedral_3": ["dawn_cathedral_2", "dawn_cathedral_4"],
        "dawn_cathedral_4": ["dawn_cathedral_1", "dawn_cathedral_3", "dawn_cathedral_6"],
        "dawn_cathedral_5": ["dawn_cathedral_2", "dawn_cathedral_6"],
        "dawn_cathedral_6": ["dawn_cathedral_4", "dawn_cathedral_5"],  # 隐藏房(探索12)-圣辉暗室
    },
    "knight_yard": {
        "knight_yard_1": ["knight_yard_2", "knight_yard_4"],
        "knight_yard_2": ["knight_yard_1", "knight_yard_3", "knight_yard_5"],
        "knight_yard_3": ["knight_yard_2", "knight_yard_4"],
        "knight_yard_4": ["knight_yard_1", "knight_yard_3", "knight_yard_6"],
        "knight_yard_5": ["knight_yard_2", "knight_yard_6"],
        "knight_yard_6": ["knight_yard_4", "knight_yard_5"],  # 隐藏房(探索11)-武器库密室(elite)
    },
}


# ---------------------------------------------------------------------------
# 三、MESH_POI_MOUNTS：给新增房间挂 POI（key="地图id:新房间id"）
# ---------------------------------------------------------------------------
# 死胡同/隐藏房间挂高价值 POI（ancient_altar/loot_pile/merchant_camp/traveler_grave 等）。每新房间>=1 个。
# 只挂载不定义；poi id 限于既有 10 个 + F 新 7 个。
# ---------------------------------------------------------------------------
MESH_POI_MOUNTS = {
    # ------------------- 南境·绿野 -------------------
    "oak_plain:oak_plain_4": ["herb_patch", "campfire"],
    "oak_plain:oak_plain_5": ["merchant_camp", "loot_pile"],       # 废弃磨坊：行商遗货
    "oak_plain:oak_plain_6": ["ancient_altar", "loot_pile"],       # 死胡同(elite)高价值

    "white_deer_forest:white_deer_forest_4": ["fishing_spot", "scenic_view"],  # 鹿鸣谷溪景
    "white_deer_forest:white_deer_forest_5": ["bird_nest", "herb_patch"],
    "white_deer_forest:white_deer_forest_6": ["loot_pile", "campfire"],

    "emerald_forest:emerald_forest_4": ["bird_nest", "herb_patch"],
    "emerald_forest:emerald_forest_5": ["campfire", "loot_pile"],
    "emerald_forest:emerald_forest_6": ["ancient_altar", "loot_pile"],  # 隐藏房-苔径密室高价值

    "misty_swamp:misty_swamp_4": ["traveler_grave", "campfire"],
    "misty_swamp:misty_swamp_5": ["herb_patch", "loot_pile"],
    "misty_swamp:misty_swamp_6": ["ancient_altar", "traveler_grave"],  # 沉陷墓穴高价值

    "hill_mine:hill_mine_4": ["loot_pile", "campfire"],
    "hill_mine:hill_mine_5": ["fishing_spot", "scenic_view"],   # 暗河渡口
    "hill_mine:hill_mine_6": ["ancient_altar", "loot_pile"],    # 隐藏房-苔藓密室高价值

    "harbor_docks:harbor_docks_4": ["shipwreck", "fishing_spot"],  # 吊车平台看沉船
    "harbor_docks:harbor_docks_5": ["loot_pile", "campfire"],
    "harbor_docks:harbor_docks_6": ["shipwreck", "ancient_altar"],  # 灯塔残基高价值

    "silver_valley:silver_valley_4": ["fishing_spot", "herb_patch"],
    "silver_valley:silver_valley_5": ["campfire", "scenic_view"],
    "silver_valley:silver_valley_6": ["ancient_altar", "loot_pile"],  # 谷底深潭高价值

    "windmill_plain:windmill_plain_4": ["campfire", "loot_pile"],
    "windmill_plain:windmill_plain_5": ["merchant_camp", "scenic_view"],  # 停转风车
    "windmill_plain:windmill_plain_6": ["ancient_altar", "loot_pile"],    # 草海深处(elite)高价值

    "rockfall_gorge:rockfall_gorge_4": ["herb_patch", "campfire"],
    "rockfall_gorge:rockfall_gorge_5": ["scenic_view", "loot_pile"],  # 断桥对岸远眺
    "rockfall_gorge:rockfall_gorge_6": ["ancient_altar", "loot_pile"],  # 隐藏房-落岩裂隙高价值

    "boar_ridge:boar_ridge_4": ["bird_nest", "herb_patch"],
    "boar_ridge:boar_ridge_5": ["campfire", "loot_pile"],
    "boar_ridge:boar_ridge_6": ["ancient_altar", "merchant_camp"],  # 密林跳径高价值

    "silver_wind_road:silver_wind_road_3": ["merchant_camp", "loot_pile"],  # 驿站后院：零担货摊
    "silver_wind_road:silver_wind_road_4": ["ancient_altar", "campfire"],   # 隐藏房-野狗岔道高价值

    # ------------------- 中域·圣光之心 -------------------
    "silver_river:silver_river_4": ["fishing_spot", "herb_patch"],
    "silver_river:silver_river_5": ["merchant_camp", "scenic_view"],  # 水下石阶近路
    "silver_river:silver_river_6": ["ancient_altar", "bird_nest"],    # 隐藏房-雁回高台高价值

    "gold_plain:gold_plain_4": ["merchant_camp", "loot_pile"],  # 晒粮场
    "gold_plain:gold_plain_5": ["ancient_altar", "campfire"],   # 荒庙残垣
    "gold_plain:gold_plain_6": ["loot_pile", "scenic_view"],    # 北坡麦缘(elite)

    "white_abbey:white_abbey_4": ["herb_patch", "campfire"],
    "white_abbey:white_abbey_5": ["loot_pile", "campfire"],
    "white_abbey:white_abbey_6": ["ancient_altar", "loot_pile"],  # 隐藏房-圣龛密室(elite)高价值

    "ironshield_hills:ironshield_hills_4": ["campfire", "loot_pile"],
    "ironshield_hills:ironshield_hills_5": ["scenic_view", "campfire"],  # 哨塔旧址远眺
    "ironshield_hills:ironshield_hills_6": ["ancient_altar", "loot_pile"],  # 隐藏房-铁脊岩缝高价值

    "old_battlefield:old_battlefield_4": ["traveler_grave", "loot_pile"],  # 断矛冢
    "old_battlefield:old_battlefield_5": ["campfire", "loot_pile"],
    "old_battlefield:old_battlefield_6": ["ancient_altar", "loot_pile"],  # 将旗台下(elite)高价值

    "border_castle:border_castle_4": ["campfire", "traveler_grave"],  # 外堡马厩
    "border_castle:border_castle_5": ["loot_pile", "campfire"],
    "border_castle:border_castle_6": ["ancient_altar", "loot_pile"],  # 隐藏房-藏兵甬道(elite)高价值

    "west_ridge_wilds:west_ridge_wilds_4": ["bird_nest", "herb_patch"],
    "west_ridge_wilds:west_ridge_wilds_5": ["scenic_view", "campfire"],  # 风蚀石林
    "west_ridge_wilds:west_ridge_wilds_6": ["traveler_grave", "ancient_altar"],  # 隐藏房-孤坟岗高价值

    "dusk_ridge_road:dusk_ridge_road_4": ["herb_patch", "campfire"],
    "dusk_ridge_road:dusk_ridge_road_5": ["loot_pile", "campfire"],  # 破败寇寨
    "dusk_ridge_road:dusk_ridge_road_6": ["ancient_altar", "loot_pile"],  # 隐藏房-隘口密道高价值

    "king_road:king_road_4": ["traveler_grave", "loot_pile"],  # 殉葬石室
    "king_road:king_road_5": ["campfire", "scenic_view"],
    "king_road:king_road_6": ["ancient_altar", "loot_pile"],  # 隐藏房-回廊密道高价值

    "dawn_cathedral:dawn_cathedral_4": ["traveler_grave", "herb_patch"],  # 侧翼墓园
    "dawn_cathedral:dawn_cathedral_5": ["campfire", "scenic_view"],  # 钟塔夹梯远眺
    "dawn_cathedral:dawn_cathedral_6": ["ancient_altar", "loot_pile"],  # 隐藏房-圣辉暗室高价值

    "knight_yard:knight_yard_4": ["campfire", "loot_pile"],
    "knight_yard:knight_yard_5": ["campfire", "scenic_view"],
    "knight_yard:knight_yard_6": ["ancient_altar", "loot_pile"],  # 隐藏房-武器库密室(elite)高价值
}
