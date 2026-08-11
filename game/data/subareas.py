# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - subareas.py(自动生成，2026－08－07)"""
# 子区域拆分：02 章 13 节。key=地图id，value=子区域列表（顺序即默认落点）
SUBAREAS = {
    "oak_town": [
        {
            "id": "oak_town_1",
            "name": "冒险者广场",
            "icon": "🏘️",
            "desc": "镇中心的青石广场，行会接待员守在告示板前。这里永远是橡木镇最热闹的地方，冒险者们在此集合、交换情报、接下委托。",
            "type": "城镇",
            "lv": 1,
            "npcs": [
                "npc_guild_clerks",
                'npc_oak_candy', 'npc_oak_novice', 'npc_oak_oldman', 'npc_oak_kid',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "oak_town_2",
            "name": "镇长办公处",
            "icon": "🏘️",
            "desc": "镇长办公处是栋整洁的木楼，门前挂着橡木镇的徽记。镇长常在案前处理镇务，来访者总能在午后找到他。",
            "type": "城镇",
            "lv": 1,
            "npcs": [
                "npc_mayor",
                'npc_oak_clerk',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "oak_town_3",
            "name": "老铁铁匠铺",
            "icon": "🏘️",
            "desc": "老铁的铺子日夜叮当作响，炉火把半条街映得通红。墙上挂满刀剑农具，铁与火的气味混着汗水的味道。",
            "type": "城镇",
            "lv": 1,
            "npcs": [
                "npc_blacksmith",
                'npc_oak_apprentice_smith',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop",
                "craft"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "oak_town_4",
            "name": "橡木桶旅店",
            "icon": "🏘️",
            "desc": "旅店门口挂着巨大的橡木桶招牌，推门就是炉火与麦酒的暖香。老板娘擦着杯子，给每个风尘仆仆的旅人递上一杯热酒。",
            "type": "城镇",
            "lv": 1,
            "npcs": [
                "npc_innkeeper",
                'npc_oak_bellboy',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "heal"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "oak_town_5",
            "name": "草药铺",
            "icon": "🏘️",
            "desc": "草药铺里弥漫着干燥草木的苦香，架子上摆满瓶瓶罐罐。草药师低头研磨，偶尔抬头招呼一声熟客。",
            "type": "城镇",
            "lv": 1,
            "npcs": [
                "npc_herb_master",
                'npc_oak_herb_girl',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                # v101.25 #350：草药铺收草药/精华类材料（v101.25e 分设施回收后新手村无 alchemy 设施，黏液等卖不掉）
                "alchemy"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "oak_town_street",
            "name": "东大街",
            "icon": "🏘️",
            "desc": "橡木镇最热闹的街道，两侧是木板房与布棚摊，沿街飘着烤面包的香气。走到尽头，镇子就融进了田野。",
            "type": "城镇街道",
            "lv": 1,
            "npcs": ["npc_oak_street_vendor", 'npc_oak_vegwife'],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
        {
            "id": "oak_town_outskirts",
            "name": "镇郊",
            "icon": "🌾",
            "desc": "橡木镇边缘的田野，麦垛堆在路边，一条土路向东延伸进橡木平原，向西通往枫橡村。",
            "type": "城镇出口",
            "lv": 1,
            "npcs": ["npc_oak_outskirts_farmer", 'npc_oak_farmer'],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "oak_plain": [
        {
            "id": "oak_plain_1",
            "name": "草地边缘",
            "icon": "🌲",
            "desc": "橡木平原的入口，矮草没过脚踝，绿史莱姆懒洋洋地滚在草丛间。牧羊人赶着羊群经过，提醒你小心脚下。",
            "type": "野外",
            "lv": 1,
            "npcs": ["npc_oak_shepherd"],
            "monsters": [
                [
                    "m_slime",
                    "绿史莱姆",
                    "tank",
                    1,
                    [
                        "ms_zhuang_ji"
                    ],
                    [
                        "史莱姆黏液"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "oak_plain_2",
            "name": "草地深处",
            "icon": "🌲",
            "desc": "野草越长越高，风一吹沙沙作响。野兔从草丛里窜出来又消失在更深处，这里安静得只听得见风声。",
            "type": "野外",
            "lv": 2,
            "npcs": [],
            "monsters": [
                [
                    "m_rabbit",
                    "野兔",
                    "speedster",
                    1,
                    [
                        "ms_ji_pao"
                    ],
                    [
                        "兔毛"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "oak_plain_3",
            "name": "溪边草地",
            "icon": "🌲",
            "desc": "一条浅溪从草地间流过，溪边泥地上满是野猪的蹄印。巨型野猪偶尔在此饮水，打扰它可不是好主意。",
            "type": "野外",
            "lv": 3,
            "npcs": [],
            "monsters": [
                [
                    "m_boar",
                    "野猪",
                    "dps",
                    3,
                    [
                        "ms_chong_zhuang"
                    ],
                    [
                        "野猪牙"
                    ]
                ],
                ],
            "elite": [
                "e_great_boar",
                "巨型野猪",
                "elite",
                4,
                [
                    "ms_chong_zhuang",
                    "ms_jian_ta"
                ],
                [
                    "巨型野猪牙"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "white_deer_forest": [
        {
            "id": "white_deer_forest_1",
            "name": "林间入口",
            "icon": "🌲",
            "desc": "白鹿之森的入口，白桦与橡树交错成荫。林间传来野狗的吠叫，护林人提醒入林者结伴而行。",
            "type": "野外",
            "lv": 3,
            "npcs": ["npc_deer_forester"],
            "monsters": [
                [
                    "m_wild_dog",
                    "野狗",
                    "dps",
                    3,
                    [
                        "ms_si_yao"
                    ],
                    [
                        "狗牙"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "white_deer_forest_2",
            "name": "白鹿之森深处",
            "icon": "🌲",
            "desc": "越往深处走，树冠越密，光线被切成碎片。毒蛇盘在落叶间，这里的每一步都要当心。",
            "type": "野外",
            "lv": 5,
            "npcs": [],
            "monsters": [
                [
                    "m_snake",
                    "毒蛇",
                    "speedster",
                    4,
                    [
                        "ms_du_ya"
                    ],
                    [
                        "蛇皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "white_deer_forest_3",
            "name": "溪谷",
            "icon": "🌲",
            "desc": "林间溪谷水声潺潺，却是哥布林斥候出没的地带。溪石上偶尔能看到他们留下的粗糙刻痕。",
            "type": "野外",
            "lv": 6,
            "npcs": [],
            "monsters": [
                [
                    "m_goblin_scout",
                    "哥布林斥候",
                    "speedster",
                    5,
                    [
                        "ms_duan_dao"
                    ],
                    [
                        "哥布林耳朵"
                    ]
                ],
                [
                    "e_goblin_raider",
                    "哥布林劫掠者",
                    "dps",
                    6,
                    [
                        "ms_duan_dao",
                        "ms_tou_shi"
                    ],
                    [
                        "劫掠者徽记"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "white_deer": [
        {
            "id": "white_deer_1",
            "name": "白鹿广场",
            "icon": "🏘️",
            "desc": "白鹿城的中心广场，白石铺地，中央矗立着一尊回眸的白鹿雕像。酒馆老板与导师们常在广场边招揽生意，人来人往。",
            "type": "城镇",
            "lv": 5,
            "npcs": [
                "npc_tavern_owner",
                "npc_warrior_tutor",
                "npc_mage_tutor",
                "npc_priest_tutor",
                'npc_deer_guard', 'npc_deer_bard',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "white_deer_2",
            "name": "城主府",
            "icon": "🏘️",
            "desc": "城主府的石阶高阔，门前立着持戟卫兵。南境的大小事务都在这里定夺，来访者需先递上名帖。",
            "type": "城镇",
            "lv": 5,
            "npcs": [
                "npc_baron",
                'npc_deer_scribe',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "white_deer_3",
            "name": "鹿角铁匠铺",
            "icon": "🏘️",
            "desc": "铁匠铺的招牌是一对铁铸鹿角，炉火终日不熄。叮当的锤声里，一件件好兵器在白鹿城匠人手中成型。",
            "type": "城镇",
            "lv": 5,
            "npcs": [
                "npc_blacksmith2",
                'npc_deer_blacksmith_h',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop",
                "craft"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "white_deer_4",
            "name": "白鹿圣堂",
            "icon": "🏘️",
            "desc": "圣堂的穹顶画着白鹿衔枝的壁画，烛火在圣像前长明。牧师在圣坛前低声诵念，为来者抚平伤痛。",
            "type": "城镇",
            "lv": 5,
            "npcs": [
                "npc_priest",
                'npc_deer_nun',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "heal"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "white_deer_5",
            "name": "白鹿与麦酒酒馆",
            "icon": "🏘️",
            "desc": "酒馆的木梁上挂满旅人留下的信物，麦酒的香气混着故事。报童在桌间穿梭，兜售着南境的最新消息。",
            "type": "城镇",
            "lv": 5,
            "npcs": [
                "npc_deer_newsboy",
                'npc_deer_drunk',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "lore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "white_deer_6",
            "name": "医师馆",
            "icon": "🏘️",
            "desc": "医师馆里药香清苦，白袍医师在案前问诊。架上整齐码着药剂瓶，伤病之人总能在这里找到慰藉。",
            "type": "城镇",
            "lv": 5,
            "npcs": [
                "npc_doctor",
                'npc_deer_nurse',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "heal",
                # v101.25 #350：医师馆收草药/精华类材料（v101.25e 分设施回收后白鹿城无 alchemy 设施）
                "alchemy"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "white_deer_7",
            "name": "烹饪坊",
            "icon": "🏘️",
            "desc": "烹饪坊的灶台热气腾腾，香料的味道飘满街角。大师傅翻动着锅铲，指点着学徒的火候。",
            "type": "城镇",
            "lv": 5,
            "npcs": [
                "npc_cook_master",
                'npc_deer_cook',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "apprentice"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "white_deer_8",
            "name": "强化工坊",
            "icon": "🏘️",
            "desc": "强化工坊里摆满磨石与符文，工匠仔细检查着每一件装备。叮叮当当的敲打声里，武器变得更锋利。",
            "type": "城镇",
            "lv": 5,
            "npcs": [
                "npc_enhance_master",
                'npc_deer_enchanter',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop",
                "craft"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "white_deer_gate",
            "name": "白鹿城门",
            "icon": "🏰",
            "desc": "白鹿城的白石城门，门楣雕着一头回眸的白鹿。城门内外，人声与风一起流动。",
            "type": "城镇出口",
            "lv": 1,
            "npcs": ["npc_white_deer_gate_guard", 'npc_deer_gatekeeper'],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "emerald_forest": [
        {
            "id": "emerald_forest_1",
            "name": "林间小径",
            "icon": "🌲",
            "desc": "翡翠森林的林间小径覆着厚厚的落叶，阳光在树冠间跳跃。猎人挎着弓沿径而行，森林狼的低吠在林间回荡。",
            "type": "野外",
            "lv": 8,
            "npcs": ["npc_emerald_hunter"],
            "monsters": [
                [
                    "m_forest_wolf",
                    "森林狼",
                    "dps",
                    8,
                    [
                        "ms_si_yao",
                        "ms_hao_jiao"
                    ],
                    [
                        "狼皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "emerald_forest_2",
            "name": "森林深处",
            "icon": "🌲",
            "desc": "古木参天，藤蔓垂成绿帘，光线渐渐暗淡。哥布林战士的嚎叫在林深处此起彼伏。",
            "type": "野外",
            "lv": 11,
            "npcs": [],
            "monsters": [
                [
                    "m_goblin_warrior",
                    "哥布林战士",
                    "dps",
                    10,
                    [
                        "ms_duan_dao",
                        "ms_dun_ji"
                    ],
                    [
                        "哥布林徽记"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "emerald_forest_3",
            "name": "古树空地",
            "icon": "🌲",
            "desc": "空地被一圈巨树环抱，树根虬结如巨掌。传说狼王·灰影曾在此长啸，树皮上还留着深深的爪痕。",
            "type": "野外",
            "lv": 14,
            "npcs": [],
            "monsters": [
                [
                    "m_treant",
                    "树人",
                    "tank",
                    12,
                    [
                        "ms_teng_bian",
                        "ms_ying_hua"
                    ],
                    [
                        "古木枝"
                    ]
                ],
                ],
            "elite": [
                "e_wolf_alpha",
                "狼王·灰影",
                "elite",
                14,
                [
                    "ms_si_yao",
                    "ms_hao_jiao",
                    "ms_pu_ji"
                ],
                [
                    "灰影狼牙"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "misty_swamp": [
        {
            "id": "misty_swamp_1",
            "name": "沼泽边缘",
            "icon": "🌲",
            "desc": "迷雾从沼泽深处漫出，像一层面纱。渔人蹲在岸边守着钓竿，大史莱姆在浅水里缓缓蠕动。",
            "type": "野外",
            "lv": 12,
            "npcs": ["npc_swamp_fisher"],
            "monsters": [
                [
                    "m_big_slime",
                    "大史莱姆",
                    "tank",
                    12,
                    [
                        "ms_zhuang_ji",
                        "ms_nian_ye"
                    ],
                    [
                        "大史莱姆核"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "misty_swamp_2",
            "name": "芦苇荡",
            "icon": "🌲",
            "desc": "芦苇高过人头，风过时沙沙作响。水面下偶尔翻起一道涟漪——那是沼泽鳄鱼在潜行。",
            "type": "野外",
            "lv": 15,
            "npcs": [],
            "monsters": [
                [
                    "m_crocodile",
                    "沼泽鳄鱼",
                    "dps",
                    14,
                    [
                        "ms_yao_sui",
                        "ms_shuai_wei"
                    ],
                    [
                        "鳄鱼皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "misty_swamp_3",
            "name": "沼泽深处",
            "icon": "🌲",
            "desc": "雾气在这里浓得化不开，脚下的泥地软烂。巫师的低语在雾中回荡，巨鳄的脊背缓缓滑过水面。",
            "type": "野外",
            "lv": 18,
            "npcs": [],
            "monsters": [
                [
                    "m_swamp_mage",
                    "沼泽巫师",
                    "healer",
                    16,
                    [
                        "ms_du_wu",
                        "ms_shui_dan"
                    ],
                    [
                        "巫师法杖碎片"
                    ]
                ],
                ],
            "elite": [
                "e_swamp_king",
                "沼泽巨鳄",
                "elite",
                18,
                [
                    "ms_yao_sui",
                    "ms_shuai_wei",
                    "ms_ni_jiang"
                ],
                [
                    "巨鳄鳞"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "goblin_camp": [
        {
            "id": "goblin_camp_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "哥布林营地入口：歪斜的木栅栏围出一片喧闹的营地，绿皮身影在篝火间窜动，臭味与叫嚷声隔着老远就能闻到。",
            "type": "副本",
            "lv": 15,
            "npcs": [],
            "monsters": [
                [
                    "m_goblin_guard",
                    "哥布林守卫",
                    "tank",
                    15,
                    [
                        "ms_dun_ji"
                    ],
                    [
                        "哥布林铁片"
                    ]
                ],
                [
                    "m_goblin_shaman",
                    "哥布林萨满",
                    "healer",
                    16,
                    [
                        "ms_zhi_liao",
                        "ms_du_wu"
                    ],
                    [
                        "萨满图腾"
                    ]
                ],
                [
                    "m_goblin_berserker",
                    "哥布林狂战士",
                    "dps",
                    18,
                    [
                        "ms_lian_zhan"
                    ],
                    [
                        "狂战士腰带"
                    ]
                ],
                [
                    "b_goblin_chief",
                    "哥布林酋长·咕噜",
                    "boss",
                    20,
                    [
                        "ms_lian_zhan",
                        "ms_nu_hou",
                        "ms_zhao_huan"
                    ],
                    [
                        "咕噜的皇冠"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_goblin_chief",
                "哥布林酋长·咕噜",
                "boss",
                20,
                [
                    "ms_lian_zhan",
                    "ms_nu_hou",
                    "ms_zhao_huan"
                ],
                [
                    "咕噜的皇冠"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "hill_mine": [
        {
            "id": "hill_mine_1",
            "name": "矿洞入口",
            "icon": "🌲",
            "desc": "山壁上的矿洞口架着粗木支架，里面黑得望不见底。矿工们进进出出，矿灯的光在深处摇晃。",
            "type": "野外",
            "lv": 18,
            "npcs": ["npc_mine_miner"],
            "monsters": [
                [
                    "m_cave_bat",
                    "洞穴蝙蝠",
                    "speedster",
                    18,
                    [
                        "ms_fu_chong"
                    ],
                    [
                        "蝠翼"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "hill_mine_2",
            "name": "矿道",
            "icon": "🌲",
            "desc": "潮湿的矿道里滴着水，岩壁上闪着矿脉的微光。地精矿工的镐声在黑暗里忽远忽近。",
            "type": "野外",
            "lv": 21,
            "npcs": [],
            "monsters": [
                [
                    "m_goblin_miner",
                    "地精矿工",
                    "dps",
                    20,
                    [
                        "ms_gao_ji"
                    ],
                    [
                        "矿石碎片"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "hill_mine_3",
            "name": "矿洞深处",
            "icon": "🌲",
            "desc": "矿道在深处豁然开阔，空气变得闷热。岩石蜥蜴贴着洞壁爬行，洞穴巨魔的呼吸声沉重而可怖。",
            "type": "野外",
            "lv": 24,
            "npcs": [],
            "monsters": [
                [
                    "m_rock_lizard",
                    "岩石蜥蜴",
                    "tank",
                    22,
                    [
                        "ms_yao_sui",
                        "ms_ying_hua"
                    ],
                    [
                        "岩蜥鳞"
                    ]
                ],
                ],
            "elite": [
                "e_cave_troll",
                "洞穴巨魔",
                "elite",
                24,
                [
                    "ms_zhong_ji",
                    "ms_zai_sheng"
                ],
                [
                    "巨魔血"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "ironharbor": [
        {
            "id": "ironharbor_1",
            "name": "港口广场",
            "icon": "🏘️",
            "desc": "铁港城的中心广场，海风裹着咸味灌进来。吟游诗人拨着琴弦，水手与商人在各色摊位间讨价还价。",
            "type": "城镇",
            "lv": 10,
            "npcs": [
                "npc_bard",
                "npc_goblin_merchant",
                "npc_fish_master",
                "npc_craft_master",
                "npc_ranger_tutor",
                "npc_assassin_tutor",
                "npc_monk_tutor",
                'npc_harbor_sailor', 'npc_harbor_trader',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "ironharbor_2",
            "name": "城主府",
            "icon": "🏘️",
            "desc": "城主府以铁石砌成，门前两尊持锚石像。铁港城的大小事务都在这扇大门后定夺，海风也吹不散它的威严。",
            "type": "城镇",
            "lv": 10,
            "npcs": [
                "npc_citylord",
                'npc_harbor_ledger',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "ironharbor_3",
            "name": "冒险者行会总部",
            "icon": "🏘️",
            "desc": "大陆冒险者行会的总部，大厅挂满各色旗帜与委托书。来自各地的冒险者在此接取委托，名声在这里铸就。",
            "type": "城镇",
            "lv": 10,
            "npcs": [
                "npc_guildmaster",
                'npc_harbor_mule',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "ironharbor_4",
            "name": "金槌拍卖行",
            "icon": "🏘️",
            "desc": "拍卖行里人声鼎沸，金槌落下的脆响此起彼伏。珍奇宝物在灯下流转，出价声一浪高过一浪。",
            "type": "城镇",
            "lv": 10,
            "npcs": [
                "npc_auctioneer",
                'npc_harbor_auction',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "auction"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "ironharbor_5",
            "name": "铁锚酒馆",
            "icon": "🏘️",
            "desc": "铁锚酒馆的招牌是一只锈铁锚，店里飘着麦酒与海盐的气味。水手们聚在角落吹嘘远航见闻，这里消息最灵通。",
            "type": "城镇",
            "lv": 10,
            "npcs": [
                "npc_harbor_rope",
                'npc_harbor_bartender',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "lore"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "ironharbor_6",
            "name": "金齿轮商行",
            "icon": "🏘️",
            "desc": "商行的橱窗里陈列着来自各地的货物，齿轮招牌缓缓转动。老板娘打着算盘，与船队老板谈着下一批货。",
            "type": "城镇",
            "lv": 10,
            "npcs": [
                "npc_harbor_fishwife",
                'npc_harbor_clerk',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "ironharbor_7",
            "name": "矿工工会",
            "icon": "🏘️",
            "desc": "工会大厅里挂着矿井的分布图，粗壮的矿工们围着火炉谈论矿脉。这里的规矩很简单：汗水换酬劳。",
            "type": "城镇",
            "lv": 10,
            "npcs": [
                "npc_mine_master",
                'npc_harbor_miner_old',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
        {
            "id": "ironharbor_8",
            "name": "渔人码头",
            "icon": "🏘️",
            "desc": "码头的木栈道延伸到海里，渔船随浪起伏。渔人们吆喝着卸下满舱的鱼获，海鸥在头顶盘旋争食。",
            "type": "城镇",
            "lv": 10,
            "npcs": ['npc_harbor_fisher'],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "ironharbor_9",
            "name": "锻造坊",
            "icon": "🏘️",
            "desc": "锻造坊里炉火不熄，铁砧声震得地面发颤。这里的匠人专为冒险者打造利器，每一件都淬过海风。",
            "type": "城镇",
            "lv": 10,
            "npcs": [
                "npc_harbor_watchman",
                'npc_harbor_forge_app',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop",
                "craft"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "ironharbor_gate",
            "name": "铁港城门",
            "icon": "🏰",
            "desc": "铁港城的铁闸门锈迹斑斑却坚实无比，门缝里能闻到海风的咸味。",
            "type": "城镇出口",
            "lv": 1,
            "npcs": ["npc_ironharbor_gate_guard", 'npc_harbor_gate'],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "harbor_docks": [
        {
            "id": "harbor_docks_1",
            "name": "码头栈桥",
            "icon": "🌲",
            "desc": "铁港城的栈桥向海中延伸，缆绳绷得笔直。海水拍打着桥柱，水鬼的影子在波光下若隐若现。",
            "type": "野外",
            "lv": 20,
            "npcs": ["npc_dock_foreman"],
            "monsters": [
                [
                    "m_water_ghost",
                    "水鬼",
                    "dps",
                    20,
                    [
                        "ms_zhao_ji"
                    ],
                    [
                        "水鬼之泪"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "harbor_docks_2",
            "name": "货仓区",
            "icon": "🌲",
            "desc": "成排的货仓堆满木箱与麻袋，空气中混着沥青与咸鱼的气味。海盗水手的身影在货堆间鬼祟闪动。",
            "type": "野外",
            "lv": 23,
            "npcs": [],
            "monsters": [
                [
                    "m_pirate",
                    "海盗水手",
                    "dps",
                    22,
                    [
                        "ms_wan_dao"
                    ],
                    [
                        "弯刀碎片"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "harbor_docks_3",
            "name": "海堤",
            "icon": "🌲",
            "desc": "长堤伸入海面，浪花拍上石面。大海鸥在堤上歇脚，海盗副官曾在此眺望过远方的船影。",
            "type": "野外",
            "lv": 26,
            "npcs": [],
            "monsters": [
                [
                    "m_seagull",
                    "大海鸥",
                    "speedster",
                    22,
                    [
                        "ms_fu_chong"
                    ],
                    [
                        "海鸥羽毛"
                    ]
                ],
                ],
            "elite": [
                "e_pirate_lieutenant",
                "海盗副官",
                "elite",
                25,
                [
                    "ms_wan_dao",
                    "ms_huo_qiang"
                ],
                [
                    "副官勋章"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "sea_cave": [
        {
            "id": "sea_cave_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "海蚀洞窟入口：潮水在洞口涨落，岩壁上挂着海藻与盐霜。洞内漆黑，只有深处传来水珠滴落的回声。",
            "type": "副本",
            "lv": 22,
            "npcs": [],
            "monsters": [
                [
                    "m_sea_slime",
                    "海史莱姆",
                    "tank",
                    22,
                    [
                        "ms_zhuang_ji",
                        "ms_nian_ye"
                    ],
                    [
                        "海盐结晶"
                    ]
                ],
                [
                    "m_siren",
                    "海妖",
                    "healer",
                    24,
                    [
                        "ms_mei_huo_zhi_ge",
                        "ms_shui_dan"
                    ],
                    [
                        "海妖鳞片"
                    ]
                ],
                [
                    "m_pirate_elite",
                    "海盗精锐",
                    "dps",
                    26,
                    [
                        "ms_wan_dao",
                        "ms_huo_qiang"
                    ],
                    [
                        "精锐佩剑"
                    ]
                ],
                [
                    "b_jack_pirate",
                    "海盗王·独眼杰克",
                    "boss",
                    28,
                    [
                        "ms_wan_dao",
                        "ms_huo_qiang",
                        "ms_zhao_huan_shui_gui"
                    ],
                    [
                        "杰克的金钩"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_jack_pirate",
                "海盗王·独眼杰克",
                "boss",
                28,
                [
                    "ms_wan_dao",
                    "ms_huo_qiang",
                    "ms_zhao_huan_shui_gui"
                ],
                [
                    "杰克的金钩"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "silver_brook": [
        {
            "id": "silver_brook_1",
            "name": "银溪广场",
            "icon": "🏘️",
            "desc": "银溪镇的广场傍着一条清浅的小溪，水车在镇边吱呀转动。渔人坐在溪石上，等着银鱼上钩。",
            "type": "城镇",
            "lv": 12,
            "npcs": [
                "npc_silver_fisher",
                'npc_silver_miller',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "silver_brook_2",
            "name": "磨坊街",
            "icon": "🏘️",
            "desc": "磨坊街的石板路上铺着薄薄的麦粉，风车的影子缓缓转动。浣衣妇在溪边槌洗衣物，笑声清脆。",
            "type": "城镇",
            "lv": 12,
            "npcs": [
                "npc_silver_washer",
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "silver_brook_3",
            "name": "河畔旅店",
            "icon": "🏘️",
            "desc": "旅店就建在河畔，窗下就是潺潺流水。店主招呼着过路的客商，炉子上炖着热汤。",
            "type": "城镇",
            "lv": 12,
            "npcs": [
                "npc_silver_apprentice",
                'npc_silver_inn',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "heal"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "silver_brook_4",
            "name": "集市",
            "icon": "🏘️",
            "desc": "集市上搭着布棚，银溪的物产摆满摊头。货郎的吆喝声与溪水声混成一片，热闹而亲切。",
            "type": "城镇",
            "lv": 12,
            "npcs": [
                "npc_silver_peddler",
                'npc_silver_granny',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop",
                "stall"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "silver_brook_outskirts",
            "name": "镇郊田垄",
            "icon": "🌾",
            "desc": "银溪镇外的麦田与菜畦，田垄间的小路通向谷地与风车原野，空气中满是新麦的味道。",
            "type": "城镇出口",
            "lv": 12,
            "npcs": ["npc_silver_brook_gate_guard"],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "silver_valley": [
        {
            "id": "silver_valley_1",
            "name": "谷地入口",
            "icon": "🌲",
            "desc": "银溪谷地的入口，溪水从乱石间奔出。渔人逆流而上，溪鹿在岸边的灌木丛中探头。",
            "type": "野外",
            "lv": 10,
            "npcs": ["npc_valley_fisher"],
            "monsters": [
                [
                    "m_river_deer",
                    "溪鹿",
                    "speedster",
                    10,
                    [
                        "ms_ji_chi"
                    ],
                    [
                        "溪鹿皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "silver_valley_2",
            "name": "溪谷",
            "icon": "🌲",
            "desc": "峡谷里溪流湍急，谷山羊在崖壁间跳跃。水声轰鸣，遮住了更深处传来的动静。",
            "type": "野外",
            "lv": 13,
            "npcs": [],
            "monsters": [
                [
                    "m_valley_goat",
                    "谷山羊",
                    "dps",
                    12,
                    [
                        "ms_ding_zhuang"
                    ],
                    [
                        "山羊角"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "silver_valley_3",
            "name": "谷地深处",
            "icon": "🌲",
            "desc": "谷地在深处收窄，溪水汇成深潭。溪蜥伏在水边的石头上，谷地巨魔的脚印印在淤泥里。",
            "type": "野外",
            "lv": 16,
            "npcs": [],
            "monsters": [
                [
                    "m_stream_lizard",
                    "溪蜥",
                    "tank",
                    14,
                    [
                        "ms_yao_sui",
                        "ms_ying_hua"
                    ],
                    [
                        "溪蜥鳞"
                    ]
                ],
                ],
            "elite": [
                "e_valley_troll",
                "谷地巨魔",
                "elite",
                16,
                [
                    "ms_zhong_ji",
                    "ms_tou_shi"
                ],
                [
                    "巨魔牙"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "windmill_plain": [
        {
            "id": "windmill_plain_1",
            "name": "原野边缘",
            "icon": "🌲",
            "desc": "风车原野的边缘，草浪在风里起伏。磨坊主赶着驴车经过，平原兔在车轮前惊跳开去。",
            "type": "野外",
            "lv": 14,
            "npcs": ["npc_windmill_miller"],
            "monsters": [
                [
                    "m_plain_rabbit",
                    "平原兔",
                    "speedster",
                    14,
                    [
                        "ms_ji_pao"
                    ],
                    [
                        "兔皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "windmill_plain_2",
            "name": "风车田",
            "icon": "🌲",
            "desc": "成片麦田围着风车铺展，风车叶片缓缓转动。风车野猪在田埂上拱土，惊起一群麻雀。",
            "type": "野外",
            "lv": 17,
            "npcs": [],
            "monsters": [
                [
                    "m_windmill_boar",
                    "风车野猪",
                    "dps",
                    16,
                    [
                        "ms_chong_zhuang"
                    ],
                    [
                        "野猪牙"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "windmill_plain_3",
            "name": "原野深处",
            "icon": "🌲",
            "desc": "风在这里变得粗野，草被压成一道道浪。平原狼王的身影偶尔出现在视野尽头，随即消失在草丛中。",
            "type": "野外",
            "lv": 20,
            "npcs": [],
            "monsters": [
                [
                    "m_plain_ox",
                    "平原野牛",
                    "tank",
                    18,
                    [
                        "ms_chong_zhuang",
                        "ms_jian_ta"
                    ],
                    [
                        "牛角"
                    ]
                ],
                ],
            "elite": [
                "e_plain_wolf",
                "平原狼王",
                "elite",
                20,
                [
                    "ms_si_yao",
                    "ms_hao_jiao"
                ],
                [
                    "狼王牙"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "deer_fort": [
        {
            "id": "deer_fort_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "鹿角要塞入口：废弃要塞的拱门爬满藤蔓，门楣上残存着白鹿纹章。风穿过门洞，带来陈年的铁锈气。",
            "type": "副本",
            "lv": 18,
            "npcs": [],
            "monsters": [],
            "elite": None,
            "boss": [
                "b_fort_ghost",
                "要塞幽灵",
                "boss",
                24,
                [
                    "ms_ai_hao",
                    "ms_chuan_shen",
                    "ms_zhao_huan_ku_lou"
                ],
                [
                    "要塞残片"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "maple_village": [
        {
            "id": "maple_village_1",
            "name": "村口广场",
            "icon": "🏘️",
            "desc": "枫橡村的村口立着一棵老枫树，树下坐着乘凉的村民。广场不大，却容得下整个村庄的闲话。",
            "type": "城镇",
            "lv": 6,
            "npcs": [
                "npc_maple_woodcutter",
                'npc_maple_granny', 'npc_maple_child',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "maple_village_2",
            "name": "村长屋",
            "icon": "🏘️",
            "desc": "村长屋是一栋结实的木屋，门口挂着枫叶形的木牌。老村长坐在窗前，给每个访客倒上一杯枫糖茶。",
            "type": "城镇",
            "lv": 6,
            "npcs": [
                "npc_oak_elder"
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "maple_village_3",
            "name": "猎人小屋",
            "icon": "🏘️",
            "desc": "猎人小屋的墙上挂着兽皮与弓箭，炉火边蹲着打瞌睡的猎犬。老猎人擦拭着猎刀，讲述山里的故事。",
            "type": "城镇",
            "lv": 6,
            "npcs": [
                "npc_hunter_gray",
                'npc_maple_hunter_w',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
        {
            "id": "maple_village_4",
            "name": "枫叶旅店",
            "icon": "🏘️",
            "desc": "旅店门口挂着枫叶招牌，屋里弥漫着柴火与蜂蜜的甜香。老板娘苔丝热情地招呼每一位客人。",
            "type": "城镇",
            "lv": 6,
            "npcs": [
                "npc_inn_tess",
                'npc_maple_innkeep',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "heal"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "maple_village_fields",
            "name": "村外田野",
            "icon": "🌾",
            "desc": "枫橡村外的田野与木栅，麦田尽头的小路通向落石峡谷与野猪岭，村口的老枫树在风里沙沙响。",
            "type": "城镇出口",
            "lv": 6,
            "npcs": ["npc_maple_village_gate_guard"],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "rockfall_gorge": [
        {
            "id": "rockfall_gorge_1",
            "name": "峡谷口",
            "icon": "🌲",
            "desc": "落石峡谷的入口，两侧岩壁陡立，碎石堆满谷底。石匠们在崖边凿石，岩鼠在乱石间探头探脑。",
            "type": "野外",
            "lv": 4,
            "npcs": ["npc_gorge_stonecutter"],
            "monsters": [
                [
                    "m_rock_rat",
                    "岩鼠",
                    "speedster",
                    4,
                    [
                        "ms_ken_yao"
                    ],
                    [
                        "岩鼠牙"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "rockfall_gorge_2",
            "name": "峡谷栈道",
            "icon": "🌲",
            "desc": "贴着崖壁的栈道窄得只容一人通过，脚下是深谷。岩羊在对面崖壁上淡定地眺望行人。",
            "type": "野外",
            "lv": 6,
            "npcs": [],
            "monsters": [
                [
                    "m_mountain_goat",
                    "岩羊",
                    "dps",
                    5,
                    [
                        "ms_ding_zhuang"
                    ],
                    [
                        "岩羊毛"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "rockfall_gorge_3",
            "name": "峡谷深处",
            "icon": "🌲",
            "desc": "峡谷在此处合拢成一道天缝，光线黯淡。石蜥蜴盘踞在岩缝里，峡谷巨魔的咆哮从深处传来。",
            "type": "野外",
            "lv": 8,
            "npcs": [],
            "monsters": [
                [
                    "m_cave_lizard",
                    "石蜥蜴",
                    "tank",
                    6,
                    [
                        "ms_yao_sui",
                        "ms_ying_hua"
                    ],
                    [
                        "石蜥鳞"
                    ]
                ],
                ],
            "elite": [
                "e_gorge_troll",
                "峡谷巨魔",
                "elite",
                8,
                [
                    "ms_zhong_ji",
                    "ms_tou_shi"
                ],
                [
                    "巨魔獠牙"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "boar_ridge": [
        {
            "id": "boar_ridge_1",
            "name": "山脚",
            "icon": "🌲",
            "desc": "野猪岭的山脚下，灌木丛生，泥地上到处是翻拱的痕迹。猎人在此设下陷阱，野猪的哼叫声从坡上传来。",
            "type": "野外",
            "lv": 6,
            "npcs": ["npc_boar_hunter"],
            "monsters": [
                [
                    "m_wild_boar",
                    "野猪",
                    "dps",
                    6,
                    [
                        "ms_chong_zhuang"
                    ],
                    [
                        "野猪牙"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "boar_ridge_2",
            "name": "山腰",
            "icon": "🌲",
            "desc": "山腰的密林里树干上满是蹭痒留下的泥印。母猪兽带着幼崽在林中觅食，见到人影便发出警告的低吼。",
            "type": "野外",
            "lv": 8,
            "npcs": [],
            "monsters": [
                [
                    "m_boar_sow",
                    "母猪兽",
                    "tank",
                    7,
                    [
                        "ms_si_yao",
                        "ms_hu_zai"
                    ],
                    [
                        "母猪皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "boar_ridge_3",
            "name": "野猪王巢",
            "icon": "🌲",
            "desc": "岭顶的巢穴被粗壮的树根盘绕，地上散落着被撞断的树干。野猪王·裂鬃的獠牙在阴影里闪着寒光。",
            "type": "野外",
            "lv": 10,
            "npcs": [],
            "monsters": [
                [
                    "m_hornet",
                    "巨型马蜂",
                    "speedster",
                    8,
                    [
                        "ms_du_ci"
                    ],
                    [
                        "蜂针"
                    ]
                ],
                ],
            "elite": [
                "e_boar_king",
                "野猪王·裂鬃",
                "elite",
                10,
                [
                    "ms_chong_zhuang",
                    "ms_jian_ta",
                    "ms_hao_jiao"
                ],
                [
                    "裂鬃獠牙"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "dawn_city": [
        {
            "id": "dawn_city_1",
            "name": "王都广场",
            "icon": "🏘️",
            "desc": "圣光王都的广场宽阔得能容下整支军队，白色石柱撑起圣辉穹顶。骑士与朝圣者在此汇聚，晨曦城的荣光写在每一块石砖上。",
            "type": "城镇",
            "lv": 25,
            "npcs": [
                "npc_knight_commander",
                "npc_alchemy_master",
                'npc_dawn_guard', 'npc_dawn_herald',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "dawn_city_2",
            "name": "圣光王宫",
            "icon": "🏘️",
            "desc": "王宫以白玉砌成，尖塔刺入云霄。宫门前卫兵甲胄森然，圣光王国的权柄就握在这座宫殿之中。",
            "type": "城镇",
            "lv": 25,
            "npcs": [
                "npc_king",
                'npc_dawn_chancellor',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "dawn_city_3",
            "name": "圣光大教堂",
            "icon": "🏘️",
            "desc": "大教堂的穹顶高得让人仰望，彩窗洒下圣洁的光。教皇的布道声在石柱间回荡，烛火映着信徒虔诚的脸。",
            "type": "城镇",
            "lv": 25,
            "npcs": [
                "npc_pope",
                "npc_cardinal",
                "npc_saintess",
                'npc_dawn_deacon',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "heal"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "dawn_city_4",
            "name": "骑士团驻地",
            "icon": "🏘️",
            "desc": "骑士团的驻地，训练场上传来整齐的踏步声。园丁在墙边修剪花木，战马在厩中嘶鸣。",
            "type": "城镇",
            "lv": 25,
            "npcs": [
                "npc_dawn_gardener",
                'npc_dawn_stableboy',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "dawn_city_5",
            "name": "炼金工坊",
            "icon": "🏘️",
            "desc": "炼金工坊里坩埚咕嘟作响，彩色烟雾从瓶瓶罐罐间升起。学徒手忙脚乱地记录着配方，导师在旁摇头。",
            "type": "城镇",
            "lv": 25,
            "npcs": [
                "npc_dawn_squire",
                'npc_dawn_alchemist',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop",
                "craft"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "dawn_city_gate",
            "name": "王都城门",
            "icon": "🏰",
            "desc": "圣光王都的巍峨城门，白色石墙上刻着圣辉纹章，两列卫兵持戟而立。",
            "type": "城镇出口",
            "lv": 1,
            "npcs": ["npc_dawn_city_gate_guard", 'npc_dawn_gate'],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "dawn_cathedral": [
        {
            "id": "dawn_cathedral_1",
            "name": "圣堂前庭",
            "icon": "🌲",
            "desc": "大圣堂的前庭铺着白色石板，圣殿守卫如雕像般立在廊柱旁。虔诚者在此驻足，阳光把影子拉得很长。",
            "type": "野外",
            "lv": 28,
            "npcs": ["npc_cathedral_deacon"],
            "monsters": [
                [
                    "m_temple_guard",
                    "圣殿守卫(魔像)",
                    "tank",
                    28,
                    [
                        "ms_zhong_ji",
                        "ms_tie_bi"
                    ],
                    [
                        "圣殿铁块"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "dawn_cathedral_2",
            "name": "回廊",
            "icon": "🌲",
            "desc": "回廊的拱顶绘满壁画，脚步声在空旷的廊道里回响。暗影教徒的踪迹就藏在这些圣像的阴影里。",
            "type": "野外",
            "lv": 31,
            "npcs": [],
            "monsters": [
                [
                    "m_cultist",
                    "暗影教徒",
                    "dps",
                    30,
                    [
                        "ms_an_ying_dan"
                    ],
                    [
                        "暗影徽记"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "dawn_cathedral_3",
            "name": "圣堂地窟",
            "icon": "🌲",
            "desc": "地窟阴冷潮湿，烛火在铁架上摇曳。枢机主教·奥古斯都的布道声在黑暗中回荡，带着说不出的诡异。",
            "type": "野外",
            "lv": 35,
            "npcs": [],
            "monsters": [
                
                [
                    "b_cardinal",
                    "枢机主教·奥古斯都",
                    "boss",
                    94,
                    [
                        "ms_an_ying_dan",
                        "ms_suo_lian",
                        "ms_zhao_huan"
                    ],
                    [
                        "审判官之链"
                    ]
                ]
            ],
            "elite": [
                "e_inquisitor",
                "审判官",
                "elite",
                33,
                [
                    "ms_an_ying_dan",
                    "ms_suo_lian"
                ],
                [
                    "审判官之链"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "gold_plain": [
        {
            "id": "gold_plain_1",
            "name": "平原边缘",
            "icon": "🌲",
            "desc": "金穗平原的边缘，麦浪一望无际。农长站在田埂上眺望，野牛群在远处的坡地游荡。",
            "type": "野外",
            "lv": 30,
            "npcs": ["npc_gold_farmchief"],
            "monsters": [
                [
                    "m_wild_bull",
                    "野牛",
                    "tank",
                    30,
                    [
                        "ms_chong_zhuang"
                    ],
                    [
                        "牛角"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "gold_plain_2",
            "name": "麦田区",
            "icon": "🌲",
            "desc": "麦田在风里翻着金浪，麦穗沉甸甸地低垂。盗贼的身影在田垄间一闪而过，留下一串慌乱倒伏的麦秆。",
            "type": "野外",
            "lv": 35,
            "npcs": [],
            "monsters": [
                [
                    "m_bandit",
                    "盗贼",
                    "speedster",
                    32,
                    [
                        "ms_duan_jian",
                        "ms_tou_qie"
                    ],
                    [
                        "盗贼面巾"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "gold_plain_3",
            "name": "平原深处",
            "icon": "🌲",
            "desc": "平原深处地势起伏，麦浪尽头是一片荒草。草原狼在暮色里嗥叫，盗贼头目·黑鸦的营地在更深处。",
            "type": "野外",
            "lv": 40,
            "npcs": [],
            "monsters": [
                [
                    "m_steppe_wolf",
                    "草原狼",
                    "dps",
                    34,
                    [
                        "ms_si_yao"
                    ],
                    [
                        "草原狼皮"
                    ]
                ],
                ],
            "elite": [
                "e_bandit_leader",
                "盗贼头目·黑鸦",
                "elite",
                38,
                [
                    "ms_duan_jian",
                    "ms_yan_wu"
                ],
                [
                    "黑鸦披风"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "white_abbey": [
        {
            "id": "white_abbey_1",
            "name": "修道院门口",
            "icon": "🌲",
            "desc": "白石修道院的门口立着残破的圣母像，苔藓爬上台阶。院长站在门廊下，目光空洞地望着来客。",
            "type": "野外",
            "lv": 32,
            "npcs": [
                "npc_abbess"
            ],
            "monsters": [
                [
                    "m_corrupted_nun",
                    "腐蚀修女",
                    "healer",
                    32,
                    [
                        "ms_an_ying_zhi_liao",
                        "ms_fu_shi_shu"
                    ],
                    [
                        "染黑圣铃"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "white_abbey_2",
            "name": "庭院",
            "icon": "🌲",
            "desc": "庭院里的喷泉早已干涸，石魔像散落在花圃间。曾经的花香变成了尘土的气息。",
            "type": "野外",
            "lv": 35,
            "npcs": [],
            "monsters": [
                [
                    "m_stone_golem",
                    "石魔像",
                    "tank",
                    34,
                    [
                        "ms_zhong_ji",
                        "ms_ying_hua"
                    ],
                    [
                        "魔像核心"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "white_abbey_3",
            "name": "地窖",
            "icon": "🌲",
            "desc": "地窖的台阶通向黑暗深处，霉味扑面而来。修道院守护者的低语从墙角传来，像是祷告，又像是诅咒。",
            "type": "野外",
            "lv": 38,
            "npcs": [],
            "monsters": [
                ],
            "elite": [
                "e_abbey_guardian",
                "修道院守护者",
                "elite",
                37,
                [
                    "ms_zhong_ji",
                    "ms_sheng_guang_zhan_bei_wu_ran"
                ],
                [
                    "守护者碎片"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "old_king_tomb": [
        {
            "id": "old_king_tomb_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "旧王陵入口：石门半掩在荒草间，门前的石狮已风化得面目模糊。王陵深处的黑暗仿佛在等待什么。",
            "type": "副本",
            "lv": 35,
            "npcs": [],
            "monsters": [
                [
                    "m_skeleton",
                    "骷髅兵",
                    "dps",
                    35,
                    [
                        "ms_jian_ji"
                    ],
                    [
                        "碎骨"
                    ]
                ],
                [
                    "m_zombie",
                    "僵尸",
                    "tank",
                    37,
                    [
                        "ms_zhao_ji",
                        "ms_gan_ran"
                    ],
                    [
                        "腐肉"
                    ]
                ],
                [
                    "m_ghost",
                    "幽灵",
                    "speedster",
                    40,
                    [
                        "ms_chuan_shen",
                        "ms_ai_hao"
                    ],
                    [
                        "幽灵之尘"
                    ]
                ],
                [
                    "b_king_odric",
                    "古王·奥德里克",
                    "boss",
                    45,
                    [
                        "ms_jian_ji",
                        "ms_wang_wei",
                        "ms_zhao_huan_ku_lou"
                    ],
                    [
                        "古王剑"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_king_odric",
                "古王·奥德里克",
                "boss",
                45,
                [
                    "ms_jian_ji",
                    "ms_wang_wei",
                    "ms_zhao_huan_ku_lou"
                ],
                [
                    "古王剑"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "border_castle": [
        {
            "id": "border_castle_1",
            "name": "堡外荒野",
            "icon": "🌲",
            "desc": "边境堡外的荒野风沙弥漫，枯草伏地。军需官在营帐前清点辎重，远处传来兽人劫掠者的号角。",
            "type": "野外",
            "lv": 40,
            "npcs": ["npc_border_quartermaster"],
            "monsters": [
                [
                    "m_orc_raider",
                    "兽人劫掠者",
                    "dps",
                    40,
                    [
                        "ms_fu_ji"
                    ],
                    [
                        "兽人斧刃"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "border_castle_2",
            "name": "城墙下",
            "icon": "🌲",
            "desc": "高墙的影子落在脚下，投石机的残骸横在墙根。战争机器的零件散落一地，攻城战留下的伤痕犹在。",
            "type": "野外",
            "lv": 45,
            "npcs": [],
            "monsters": [
                [
                    "m_war_machine",
                    "战争机器",
                    "tank",
                    44,
                    [
                        "ms_chong_zhuang",
                        "ms_huo_pao"
                    ],
                    [
                        "战争机器零件"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "border_castle_3",
            "name": "堡内广场",
            "icon": "🌲",
            "desc": "堡内广场的地砖被战靴磨得发亮，旗帜在风中猎猎作响。兽人战士的咆哮隔墙可闻，这里随时准备再战。",
            "type": "野外",
            "lv": 50,
            "npcs": [],
            "monsters": [
                ],
            "elite": [
                "e_orc_warrior",
                "兽人战士",
                "elite",
                47,
                [
                    "ms_fu_ji",
                    "ms_zhan_hou"
                ],
                [
                    "兽人战徽"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "silver_river": [
        {
            "id": "silver_river_1",
            "name": "河岸",
            "icon": "🌲",
            "desc": "银铃河的河岸水草丰茂，渡船在岸边摇晃。水精灵在河面上飘忽，圣光骑士团的追兵在远处搜寻着什么。",
            "type": "野外",
            "lv": 20,
            "npcs": ["npc_river_ferryman"],
            "monsters": [
                [
                    "m_river_spirit",
                    "水精灵",
                    "healer",
                    20,
                    [
                        "ms_shui_dan",
                        "ms_zhi_liao"
                    ],
                    [
                        "水精灵泪"
                    ]
                ],
                [
                    "m_knight_pursuer",
                    "圣光骑士团追兵",
                    "dps",
                    22,
                    [
                        "ms_sheng_guang_zhui_bing"
                    ],
                    [
                        "骑士团徽记"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "silver_river_2",
            "name": "渡口",
            "icon": "🌲",
            "desc": "渡口的木桩被水泡得发黑，摆渡人撑着长篙。鲛人的歌声从河心传来，让人心头一紧。",
            "type": "野外",
            "lv": 25,
            "npcs": [],
            "monsters": [
                [
                    "m_mermaid",
                    "鲛人",
                    "dps",
                    22,
                    [
                        "ms_cha_ji",
                        "ms_shui_dan"
                    ],
                    [
                        "鲛人鳞"
                    ]
                ],
                [
                    "m_roland",
                    "罗兰·圣剑",
                    "dps",
                    25,
                    [
                        "ms_sheng_guang_jian_zhen"
                    ],
                    [
                        "罗兰的断剑"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "silver_river_3",
            "name": "河心洲",
            "icon": "🌲",
            "desc": "河心洲被水流环抱，芦苇在风里摇晃。河龙的脊背在水下缓缓游动，河龙领主的气息让整条河都安静下来。",
            "type": "野外",
            "lv": 30,
            "npcs": [],
            "monsters": [
                [
                    "m_river_dragon",
                    "河龙",
                    "tank",
                    25,
                    [
                        "ms_shui_xi",
                        "ms_shuai_wei"
                    ],
                    [
                        "河龙鳞"
                    ]
                ],
                ],
            "elite": [
                "e_river_dragon_lord",
                "河龙领主",
                "elite",
                27,
                [
                    "ms_shui_xi",
                    "ms_xuan_wo"
                ],
                [
                    "河龙领主鳞"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "secret_crypt": [
        {
            "id": "secret_crypt_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "圣堂地窖入口：大圣堂深处的暗门，石阶盘旋向下。烛台的余烬还冒着轻烟，空气里混着蜡与尘土的味道。",
            "type": "副本",
            "lv": 42,
            "npcs": [],
            "monsters": [
                [
                    "m_shadow_priest",
                    "暗影祭司",
                    "healer",
                    42,
                    [
                        "ms_an_ying_dan",
                        "ms_hei_an_zhi_liao"
                    ],
                    [
                        "染黑圣典"
                    ]
                ],
                [
                    "m_inquisitor_hound",
                    "审判猎犬",
                    "speedster",
                    45,
                    [
                        "ms_si_yao"
                    ],
                    [
                        "猎犬项圈"
                    ]
                ],
                [
                    "b_marcus",
                    "审判长·马尔库斯",
                    "boss",
                    52,
                    [
                        "ms_an_ying_dan",
                        "ms_suo_lian",
                        "ms_shen_pan_zhi_yan"
                    ],
                    [
                        "马尔库斯的法冠"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_marcus",
                "审判长·马尔库斯",
                "boss",
                52,
                [
                    "ms_an_ying_dan",
                    "ms_suo_lian",
                    "ms_shen_pan_zhi_yan"
                ],
                [
                    "马尔库斯的法冠"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "knight_yard": [
        {
            "id": "knight_yard_1",
            "name": "训练场入口",
            "icon": "🌲",
            "desc": "圣骑士训练场的入口立着两尊持盾石像，教官在门口核对名册。训练魔像整齐地列在场地一角。",
            "type": "野外",
            "lv": 26,
            "npcs": ["npc_knight_instructor"],
            "monsters": [
                [
                    "m_training_golem",
                    "训练魔像",
                    "tank",
                    26,
                    [
                        "ms_zhong_ji",
                        "ms_tie_bi"
                    ],
                    [
                        "魔像核心"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "knight_yard_2",
            "name": "靶场",
            "icon": "🌲",
            "desc": "靶场上箭垛林立，木桩上布满劈砍的痕迹。见习骑士们一遍遍冲过障碍，汗水洒在沙地上。",
            "type": "野外",
            "lv": 30,
            "npcs": [],
            "monsters": [
                [
                    "m_training_dummy",
                    "训练木桩",
                    "dps",
                    28,
                    [
                        "ms_pi_kan"
                    ],
                    [
                        "木桩碎片"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "knight_yard_3",
            "name": "魔像试炼区",
            "icon": "🌲",
            "desc": "试炼区里魔像沉重地移动，发出齿轮的咔咔声。骑士教官站在场地中央，目光锐利如剑。",
            "type": "野外",
            "lv": 34,
            "npcs": [],
            "monsters": [
                [
                    "m_knight_apprentice",
                    "见习骑士",
                    "dps",
                    30,
                    [
                        "ms_jian_ji"
                    ],
                    [
                        "骑士徽记"
                    ]
                ],
                ],
            "elite": [
                "e_knight_instructor",
                "骑士教官",
                "elite",
                34,
                [
                    "ms_jian_ji",
                    "ms_zhan_hou"
                ],
                [
                    "教官之剑"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "king_road": [
        {
            "id": "king_road_1",
            "name": "古道口",
            "icon": "🌲",
            "desc": "王陵古道的入口，两侧古柏森森。守墓人倚在石门前，告诫来者：过了这道门，就是亡者的地界。",
            "type": "野外",
            "lv": 33,
            "npcs": ["npc_kingroad_gravekeeper"],
            "monsters": [
                [
                    "m_road_skeleton",
                    "古道骷髅",
                    "dps",
                    33,
                    [
                        "ms_jian_ji"
                    ],
                    [
                        "碎骨"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "king_road_2",
            "name": "古道中段",
            "icon": "🌲",
            "desc": "石板路被苔藓染绿，古墓幽灵的白影在树间游荡。风穿过石缝，发出呜咽般的声音。",
            "type": "野外",
            "lv": 37,
            "npcs": [],
            "monsters": [
                [
                    "m_grave_ghost",
                    "古墓幽灵",
                    "speedster",
                    36,
                    [
                        "ms_chuan_shen",
                        "ms_ai_hao"
                    ],
                    [
                        "幽灵之尘"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "king_road_3",
            "name": "王陵前",
            "icon": "🌲",
            "desc": "王陵的石门半开，门楣上的王冠浮雕已风化。古代骑士的铠甲立在门内，仿佛仍在守卫最后的王。",
            "type": "野外",
            "lv": 42,
            "npcs": [],
            "monsters": [
                [
                    "m_ancient_knight",
                    "古代骑士",
                    "tank",
                    39,
                    [
                        "ms_jian_ji",
                        "ms_tie_bi"
                    ],
                    [
                        "锈甲碎片"
                    ]
                ],
                ],
            "elite": [
                "e_grave_lord",
                "古墓领主",
                "elite",
                42,
                [
                    "ms_an_ying_zhan",
                    "ms_zhao_huan_ku_lou"
                ],
                [
                    "领主骨甲"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "holy_trial": [
        {
            "id": "holy_trial_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "圣光试炼场入口：试炼场的石拱门刻着圣辉纹章，门前立着两尊持剑骑士像。据说只有通过试炼者才能踏过门槛。",
            "type": "副本",
            "lv": 36,
            "npcs": [],
            "monsters": [],
            "elite": None,
            "boss": [
                "b_trial_knight",
                "试炼骑士长",
                "boss",
                46,
                [
                    "ms_sheng_guang_dan",
                    "ms_jian_ji",
                    "ms_zhao_huan"
                ],
                [
                    "试炼徽记"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "ironshield_town": [
        {
            "id": "ironshield_town_1",
            "name": "铁盾广场",
            "icon": "🏘️",
            "desc": "铁盾镇的广场中央立着一面巨大的铁盾雕塑，铁匠铺的锤声是全城的心跳。这里的日子硬朗而踏实。",
            "type": "城镇",
            "lv": 30,
            "npcs": [
                "npc_ironshield_smith",
                'npc_shield_townfolk',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "ironshield_town_2",
            "name": "镇公所",
            "icon": "🏘️",
            "desc": "镇公所是一栋结实的石头房子，镇长在案前翻看军报。镇上的每一件大事都从这里传达。",
            "type": "城镇",
            "lv": 30,
            "npcs": [
                "npc_ironshield_mayor"
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "ironshield_town_3",
            "name": "军械铺",
            "icon": "🏘️",
            "desc": "军械铺的墙上挂满盾牌与兵刃，铁锈与机油的气味混在一起。店主擦拭着一面崭新的铁盾。",
            "type": "城镇",
            "lv": 30,
            "npcs": [
                "npc_shield_watch",
                'npc_shield_smith',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop",
                "craft"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "ironshield_town_4",
            "name": "斥候营",
            "icon": "🏘️",
            "desc": "斥候营的帐篷搭得整整齐齐，马匹拴在桩上。斥候们在地图上标着丘陵与旧战场的路线。",
            "type": "城镇",
            "lv": 30,
            "npcs": [
                "npc_ironshield_scout",
                'npc_shield_scout',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
        {
            "id": "ironshield_town_sentry",
            "name": "镇口哨卡",
            "icon": "🛡️",
            "desc": "铁盾镇口的拒马与烽火台，哨兵在此盘查过往旅人。木栅外是通往丘陵与旧战场的路。",
            "type": "城镇出口",
            "lv": 30,
            "npcs": ["npc_ironshield_town_gate_guard", 'npc_shield_sentry'],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "ironshield_hills": [
        {
            "id": "ironshield_hills_1",
            "name": "丘陵脚",
            "icon": "🌲",
            "desc": "铁盾丘陵的脚下，灌木与乱石交错。斥候藏在岩石后观察，丘陵狼在坡上逡巡。",
            "type": "野外",
            "lv": 28,
            "npcs": ["npc_hills_scout"],
            "monsters": [
                [
                    "m_hill_wolf",
                    "丘陵狼",
                    "dps",
                    28,
                    [
                        "ms_si_yao",
                        "ms_hao_jiao"
                    ],
                    [
                        "丘陵狼皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "ironshield_hills_2",
            "name": "丘陵中",
            "icon": "🌲",
            "desc": "丘陵起伏如铁甲，铁甲野猪在灌木间拱行，背上的硬皮泛着金属光泽。",
            "type": "野外",
            "lv": 32,
            "npcs": [],
            "monsters": [
                [
                    "m_iron_boar",
                    "铁甲野猪",
                    "tank",
                    30,
                    [
                        "ms_chong_zhuang",
                        "ms_tie_pi"
                    ],
                    [
                        "铁甲猪皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "ironshield_hills_3",
            "name": "丘陵顶",
            "icon": "🌲",
            "desc": "丘陵顶上视野开阔，秃鹫在头顶盘旋。丘陵狼王·铁牙的巢穴就在这片乱石之间。",
            "type": "野外",
            "lv": 36,
            "npcs": [],
            "monsters": [
                [
                    "m_hill_vulture",
                    "秃鹫",
                    "speedster",
                    32,
                    [
                        "ms_fu_chong"
                    ],
                    [
                        "秃鹫羽"
                    ]
                ],
                ],
            "elite": [
                "e_hill_wolf_king",
                "丘陵狼王·铁牙",
                "elite",
                34,
                [
                    "ms_si_yao",
                    "ms_pu_ji",
                    "ms_hao_jiao"
                ],
                [
                    "铁牙狼皮"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "old_battlefield": [
        {
            "id": "old_battlefield_1",
            "name": "遗址边缘",
            "icon": "🌲",
            "desc": "旧战场遗址的边缘，锈蚀的刀剑插在土里，像是墓碑。老兵坐在残垣上，摩挲着怀中的勋章。",
            "type": "野外",
            "lv": 32,
            "npcs": ["npc_battlefield_veteran"],
            "monsters": [
                [
                    "m_rust_warrior",
                    "锈甲亡兵",
                    "dps",
                    32,
                    [
                        "ms_xiu_jian"
                    ],
                    [
                        "锈甲碎片"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "old_battlefield_2",
            "name": "战壕区",
            "icon": "🌲",
            "desc": "蜿蜒的战壕已被荒草覆盖，战场幽魂在暮色里若隐若现。风穿过壕沟，像极了当年的号角。",
            "type": "野外",
            "lv": 36,
            "npcs": [],
            "monsters": [
                [
                    "m_field_ghost",
                    "战场幽魂",
                    "speedster",
                    34,
                    [
                        "ms_chuan_shen",
                        "ms_ai_hao"
                    ],
                    [
                        "幽魂尘"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "old_battlefield_3",
            "name": "遗址核心",
            "icon": "🌲",
            "desc": "遗址核心散落着破碎的战争魔像，百族战将·亡影的传说还压在每一个幸存者心头。",
            "type": "野外",
            "lv": 40,
            "npcs": [],
            "monsters": [
                [
                    "m_war_golem",
                    "战争魔像(残)",
                    "tank",
                    37,
                    [
                        "ms_zhong_ji",
                        "ms_tie_bi"
                    ],
                    [
                        "魔像残核"
                    ]
                ],
                ],
            "elite": [
                "e_battle_lord",
                "百族战将·亡影",
                "elite",
                40,
                [
                    "ms_zhan_chui",
                    "ms_zhan_hou",
                    "ms_zhao_huan_you_hun"
                ],
                [
                    "亡影战徽"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "moon_gate": [
        {
            "id": "moon_gate_1",
            "name": "月门广场",
            "icon": "🏘️",
            "desc": "月冠隘口的广场铺着月光色的石板，城门洞开，银月的光辉洒满地面。守卫在这里盘查每一队商旅。",
            "type": "城镇",
            "lv": 45,
            "npcs": [
                "npc_moongate_guard",
                'npc_moongate_traveler',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "moon_gate_2",
            "name": "银月旅店",
            "icon": "🏘️",
            "desc": "旅店的招牌是一弯银月，窗边坐着观星人。这里的床铺暖和，窗外的月色更美。",
            "type": "城镇",
            "lv": 45,
            "npcs": [
                "npc_moongate_astronomer",
                'npc_moongate_inn',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "heal"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "moon_gate_3",
            "name": "哨塔集市",
            "icon": "🏘️",
            "desc": "集市沿着哨塔墙根展开，丝绸与香料摊连成一排。商人们压低声音谈着山口另一侧的消息。",
            "type": "城镇",
            "lv": 45,
            "npcs": [
                "npc_moongate_silk",
                'npc_moongate_spice',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop",
                "stall"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "moon_gate_gate",
            "name": "月门城门",
            "icon": "🏰",
            "desc": "月门城的银白色城门，门拱形如满月，夜里会泛起柔和的月光。",
            "type": "城镇出口",
            "lv": 1,
            "npcs": ["npc_moon_gate_gate_guard"],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "silverwood": [
        {
            "id": "silverwood_1",
            "name": "林海边缘",
            "icon": "🌲",
            "desc": "银月林海的边缘，银叶在风里翻出粼粼的光。巡林人挎着弓沿林缘巡视，精灵鹿在树影间时隐时现。",
            "type": "野外",
            "lv": 46,
            "npcs": ["npc_silverwood_ranger"],
            "monsters": [
                [
                    "m_elf_beast",
                    "精灵鹿",
                    "speedster",
                    46,
                    [
                        "ms_ji_pao",
                        "ms_ding_zhuang"
                    ],
                    [
                        "精灵鹿角"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "silverwood_2",
            "name": "林海深处",
            "icon": "🌲",
            "desc": "林海深处银叶如浪，光线被揉成细碎的月光。月狼的绿眼在树丛间一闪而没。",
            "type": "野外",
            "lv": 51,
            "npcs": [],
            "monsters": [
                [
                    "m_moon_wolf",
                    "月狼",
                    "dps",
                    50,
                    [
                        "ms_si_yao",
                        "ms_yue_guang_zhan"
                    ],
                    [
                        "月狼毛皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "silverwood_3",
            "name": "月辉空地",
            "icon": "🌲",
            "desc": "空地上月光如纱，古树人静静立着，枝叶垂成胡须。月狼王·银鬃的脚印印在苔藓上，深而清晰。",
            "type": "野外",
            "lv": 56,
            "npcs": [],
            "monsters": [
                [
                    "m_treant_elder",
                    "古树人",
                    "tank",
                    54,
                    [
                        "ms_teng_bian",
                        "ms_ying_hua",
                        "ms_gen_xu"
                    ],
                    [
                        "古树之心"
                    ]
                ],
                ],
            "elite": [
                "e_moon_wolf_alpha",
                "月狼王·银鬃",
                "elite",
                56,
                [
                    "ms_si_yao",
                    "ms_yue_guang_zhan",
                    "ms_hao_jiao"
                ],
                [
                    "银鬃狼皮"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "starlake": [
        {
            "id": "starlake_1",
            "name": "湖畔",
            "icon": "🌲",
            "desc": "星语湖的湖水倒映着天光，湖面平静如镜。诗人坐在湖畔石上，哼着不成调的歌，湖妖在深处聆听。",
            "type": "野外",
            "lv": 50,
            "npcs": [
                "npc_elf_poet"
            ],
            "monsters": [
                [
                    "m_lake_demon",
                    "湖妖",
                    "healer",
                    50,
                    [
                        "ms_shui_dan",
                        "ms_mei_huo"
                    ],
                    [
                        "湖妖泪"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "starlake_2",
            "name": "湖岸小径",
            "icon": "🌲",
            "desc": "湖岸的小径蜿蜒穿过芦苇丛，水精灵战士的影子在水面上晃动。每一步都惊起一圈涟漪。",
            "type": "野外",
            "lv": 55,
            "npcs": [],
            "monsters": [
                [
                    "m_water_elf",
                    "水精灵战士",
                    "dps",
                    54,
                    [
                        "ms_san_cha_ji"
                    ],
                    [
                        "水精灵鳞"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "starlake_3",
            "name": "湖心岛",
            "icon": "🌲",
            "desc": "湖心岛草木葱茏，巨鲈在浅湾里甩尾。星语湖王栖息的深水区就在岛的另一侧，水色幽蓝。",
            "type": "野外",
            "lv": 60,
            "npcs": [],
            "monsters": [
                [
                    "m_giant_bass",
                    "巨鲈",
                    "tank",
                    56,
                    [
                        "ms_zhuang_ji",
                        "ms_shui_dan"
                    ],
                    [
                        "巨鲈鱼骨"
                    ]
                ],
                ],
            "elite": [
                "e_lake_king",
                "星语湖王",
                "elite",
                58,
                [
                    "ms_shui_dan",
                    "ms_xuan_wo",
                    "ms_zhao_huan_shui_jing_ling"
                ],
                [
                    "湖王珠"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "moon_court": [
        {
            "id": "moon_court_1",
            "name": "王庭广场",
            "icon": "🏘️",
            "desc": "月冠王庭的广场铺着月光石，精灵族的建筑在月色下泛着柔和的光。贤者与卫兵的身影在廊柱间穿行。",
            "type": "城镇",
            "lv": 55,
            "npcs": [
                "npc_elf_sage",
                'npc_elf_poet2',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "moon_court_2",
            "name": "月辉王宫",
            "icon": "🏘️",
            "desc": "月辉王宫的尖塔如月牙般翘起，精灵女王接见来客的殿堂缀满星辉。守卫的银甲上流转着月光。",
            "type": "城镇",
            "lv": 55,
            "npcs": [
                "npc_elf_queen",
                "npc_elf_guardian",
                'npc_elf_maid',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "moon_court_3",
            "name": "月影卫营",
            "icon": "🏘️",
            "desc": "月影卫营的帐篷以银线缝制，园丁在墙根修剪月桂。这里的纪律与月光一样清冷。",
            "type": "城镇",
            "lv": 55,
            "npcs": [
                "npc_elf_gardener",
                'npc_elf_trainee',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "moon_court_4",
            "name": "贤者书阁",
            "icon": "🏘️",
            "desc": "书阁里卷轴堆到天花板，月光从穹顶的圆窗漏下。贤者们在此研读星象，兔子在书架间跳来跳去。",
            "type": "城镇",
            "lv": 55,
            "npcs": [
                "npc_elf_rabbit",
                'npc_elf_librarian',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "lore",
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "moon_court_gate",
            "name": "月庭宫门",
            "icon": "🏰",
            "desc": "月辉王庭的宫门由银木与月光石砌成，门上的精灵纹样流转着微光。",
            "type": "城镇出口",
            "lv": 1,
            "npcs": ["npc_moon_court_gate_guard", 'npc_elf_gateguard2'],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "elven_ruins": [
        {
            "id": "elven_ruins_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "精灵废墟入口：坍塌的月白石柱散落一地，浮雕上的精灵文字已被风雨磨平。废墟深处有微光一闪而逝。",
            "type": "副本",
            "lv": 58,
            "npcs": [],
            "monsters": [
                [
                    "m_corrupted_elf",
                    "堕落精灵",
                    "dps",
                    58,
                    [
                        "ms_jing_ling_jian_shu",
                        "ms_an_ying_zhan"
                    ],
                    [
                        "堕落精灵护符"
                    ]
                ],
                [
                    "m_ancient_golem",
                    "远古魔像",
                    "tank",
                    62,
                    [
                        "ms_zhong_ji",
                        "ms_fu_wen_chong_ji"
                    ],
                    [
                        "远古符文石"
                    ]
                ],
                [
                    "b_dawn_elf",
                    "远古精灵王·晨曦",
                    "boss",
                    66,
                    [
                        "ms_yue_guang_zhan",
                        "ms_zhao_huan_shu_ren",
                        "ms_zhi_yu"
                    ],
                    [
                        "晨曦之冠"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_dawn_elf",
                "远古精灵王·晨曦",
                "boss",
                66,
                [
                    "ms_yue_guang_zhan",
                    "ms_zhao_huan_shu_ren",
                    "ms_zhi_yu"
                ],
                [
                    "晨曦之冠"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "ancient_tree": [
        {
            "id": "ancient_tree_1",
            "name": "隘口下",
            "icon": "🌲",
            "desc": "古树隘口之下，巨树的气根垂成门帘。德鲁伊在树下打坐，巨型蜘蛛在高处的枝桠间结网。",
            "type": "野外",
            "lv": 62,
            "npcs": [
                "npc_druid_oakheart"
            ],
            "monsters": [
                [
                    "m_giant_spider",
                    "巨型蜘蛛",
                    "speedster",
                    62,
                    [
                        "ms_du_ya",
                        "ms_zhi_wang"
                    ],
                    [
                        "蜘蛛丝"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "ancient_tree_2",
            "name": "树道",
            "icon": "🌲",
            "desc": "树道沿着巨树的枝干盘旋而上，脚下是厚厚的树皮。暗影精灵的身影在叶影里闪动。",
            "type": "野外",
            "lv": 66,
            "npcs": [],
            "monsters": [
                [
                    "m_shadow_elf",
                    "暗影精灵",
                    "dps",
                    64,
                    [
                        "ms_an_ying_jian",
                        "ms_qian_xing"
                    ],
                    [
                        "暗影精灵刃"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "ancient_tree_3",
            "name": "古树之巅",
            "icon": "🌲",
            "desc": "树冠之巅风很大，能望见整片林海。古树守卫环抱树干，古树领主的低语从树心传来。",
            "type": "野外",
            "lv": 70,
            "npcs": [],
            "monsters": [
                [
                    "m_old_tree_guardian",
                    "古树守卫",
                    "tank",
                    68,
                    [
                        "ms_teng_bian",
                        "ms_ying_hua"
                    ],
                    [
                        "守卫古木"
                    ]
                ],
                ],
            "elite": [
                "e_tree_lord",
                "古树领主",
                "elite",
                70,
                [
                    "ms_teng_bian",
                    "ms_gen_xu_chan_rao",
                    "ms_zhao_huan_shu_ren"
                ],
                [
                    "领主古木心"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "star_song": [
        {
            "id": "star_song_1",
            "name": "星歌广场",
            "icon": "🏘️",
            "desc": "星歌镇的广场铺着星光色的碎石，小诗人坐在喷泉边练琴。镇子的夜晚总是最先亮起灯火。",
            "type": "城镇",
            "lv": 48,
            "npcs": [
                "npc_starsong_bardling",
                'npc_starsong_acrobat',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "star_song_2",
            "name": "星光集市",
            "icon": "🏘️",
            "desc": "集市上的灯笼像一串星星，面包的香气飘满街巷。烘焙师傅把刚出炉的面包码上案板。",
            "type": "城镇",
            "lv": 48,
            "npcs": [
                "npc_starsong_baker",
                'npc_starsong_florist',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop",
                "stall"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "star_song_3",
            "name": "星歌旅店",
            "icon": "🏘️",
            "desc": "旅店的窗台上摆着盆栽，醉汉在角落数着星星。店主擦着杯子，给晚归的客人留一盏灯。",
            "type": "城镇",
            "lv": 48,
            "npcs": [
                "npc_starsong_drunkard",
                'npc_starsong_waiter',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "heal"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "star_song_path",
            "name": "镇口林径",
            "icon": "🌿",
            "desc": "星歌镇口掩在银叶林间的林间小径，萤火虫在暮色里浮动，小路向南通向翠谷。",
            "type": "城镇出口",
            "lv": 48,
            "npcs": ["npc_star_song_gate_guard"],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "moon_glade": [
        {
            "id": "moon_glade_1",
            "name": "林缘",
            "icon": "🌲",
            "desc": "月光林的边缘，月桂的香气在夜里弥漫。月祭司站在林缘，向月亮低声祈祷，月鹿在雾中现身。",
            "type": "野外",
            "lv": 52,
            "npcs": ["npc_moonglade_moonpriest"],
            "monsters": [
                [
                    "m_moon_deer",
                    "月鹿",
                    "speedster",
                    52,
                    [
                        "ms_ji_chi",
                        "ms_yue_guang_zhan"
                    ],
                    [
                        "月鹿角"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "moon_glade_2",
            "name": "月光空地",
            "icon": "🌲",
            "desc": "空地中央的月光浓得像水，月熊在光柱下缓缓踱步，皮毛泛着银辉。",
            "type": "野外",
            "lv": 57,
            "npcs": [],
            "monsters": [
                [
                    "m_moon_bear",
                    "月熊",
                    "tank",
                    56,
                    [
                        "ms_xiong_zhang",
                        "ms_yue_guang_zhan"
                    ],
                    [
                        "月熊皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "moon_glade_3",
            "name": "林深处",
            "icon": "🌲",
            "desc": "林深处只有月光与寂静，月光精灵在林间起舞。月光领主·银辉的领地就在这片光与影的尽头。",
            "type": "野外",
            "lv": 62,
            "npcs": [],
            "monsters": [
                [
                    "m_moon_spirit",
                    "月光精灵",
                    "healer",
                    58,
                    [
                        "ms_yue_guang_zhan",
                        "ms_zhi_yu"
                    ],
                    [
                        "月光精华"
                    ]
                ],
                ],
            "elite": [
                "e_moon_lord",
                "月光领主·银辉",
                "elite",
                62,
                [
                    "ms_yue_guang_zhan",
                    "ms_zhao_huan_yue_lu"
                ],
                [
                    "银辉月石"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "emerald_valley": [
        {
            "id": "emerald_valley_1",
            "name": "谷口",
            "icon": "🌲",
            "desc": "翠谷的谷口藤蔓垂挂，鹿群在溪边饮水。牧鹿人吹着木笛，翠鹿抬起头聆听。",
            "type": "野外",
            "lv": 47,
            "npcs": ["npc_emeraldvalley_deerherd"],
            "monsters": [
                [
                    "m_emerald_deer",
                    "翠鹿",
                    "speedster",
                    47,
                    [
                        "ms_ji_chi",
                        "ms_ding_zhuang"
                    ],
                    [
                        "翠鹿角"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "emerald_valley_2",
            "name": "谷中",
            "icon": "🌲",
            "desc": "谷中草木青翠欲滴，谷地仙灵在花丛间打转。这里的美景让人几乎忘了危险。",
            "type": "野外",
            "lv": 51,
            "npcs": [],
            "monsters": [
                [
                    "m_valley_faerie",
                    "谷地仙灵",
                    "healer",
                    50,
                    [
                        "ms_cai_guang",
                        "ms_zhu_fu"
                    ],
                    [
                        "谷地露水"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "emerald_valley_3",
            "name": "翠谷深处",
            "icon": "🌲",
            "desc": "翠谷深处的绿意浓得化不开，绿角雄鹿站在石上昂首。翠谷领主·林语的树屋藏在藤蔓之后。",
            "type": "野外",
            "lv": 55,
            "npcs": [],
            "monsters": [
                [
                    "m_green_stag",
                    "绿角雄鹿",
                    "tank",
                    52,
                    [
                        "ms_ding_zhuang",
                        "ms_ying_hua"
                    ],
                    [
                        "绿鹿角"
                    ]
                ],
                ],
            "elite": [
                "e_valley_lord",
                "翠谷领主·林语",
                "elite",
                55,
                [
                    "ms_teng_bian",
                    "ms_gen_xu_chan_rao"
                ],
                [
                    "林语之叶"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "moon_temple": [
        {
            "id": "moon_temple_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "月神圣殿入口：银白的神殿大门半开，门楣上的月牙纹样在夜里会泛起柔光。殿内寂静得能听见自己的心跳。",
            "type": "副本",
            "lv": 60,
            "npcs": [],
            "monsters": [],
            "elite": None,
            "boss": [
                "b_moon_guard",
                "月神守卫",
                "boss",
                68,
                [
                    "ms_yue_guang_zhan",
                    "ms_zhi_yu",
                    "ms_zhao_huan"
                ],
                [
                    "月辉碎片"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "windvale": [
        {
            "id": "windvale_1",
            "name": "谷口",
            "icon": "🌲",
            "desc": "风语谷的谷口风声低吟，像有人在耳语。低语者坐在风口，闭眼聆听风带来的消息。",
            "type": "野外",
            "lv": 50,
            "npcs": ["npc_windvale_whisperer"],
            "monsters": [
                [
                    "m_wind_deer",
                    "风语鹿",
                    "speedster",
                    50,
                    [
                        "ms_ji_chi",
                        "ms_feng_ren"
                    ],
                    [
                        "风语鹿角"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "windvale_2",
            "name": "风语草原",
            "icon": "🌲",
            "desc": "草原上风不断，草尖齐齐俯身。风语精灵在风里穿梭，衣袂与草浪同频。",
            "type": "野外",
            "lv": 54,
            "npcs": [],
            "monsters": [
                [
                    "m_whisper_spirit",
                    "风语精灵",
                    "healer",
                    52,
                    [
                        "ms_feng_ren",
                        "ms_wei_feng_zhu_fu"
                    ],
                    [
                        "风语结晶"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "windvale_3",
            "name": "谷底",
            "icon": "🌲",
            "desc": "谷底风势狂暴，谷地巨鹰在崖壁间盘旋。风语王·岚歌的巢就在那道最高的石柱上。",
            "type": "野外",
            "lv": 58,
            "npcs": [],
            "monsters": [
                [
                    "m_valley_eagle",
                    "谷地巨鹰",
                    "dps",
                    54,
                    [
                        "ms_fu_chong",
                        "ms_zhao_ji"
                    ],
                    [
                        "巨鹰羽"
                    ]
                ],
                ],
            "elite": [
                "e_wind_king",
                "风语王·岚歌",
                "elite",
                58,
                [
                    "ms_feng_ren",
                    "ms_feng_bao",
                    "ms_zhao_huan_feng_yu_jing_ling"
                ],
                [
                    "岚歌之羽"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "moonshadow_wood": [
        {
            "id": "moonshadow_wood_1",
            "name": "林缘",
            "icon": "🌲",
            "desc": "月影林的边缘，树影比夜色更浓。猎人在此熄灭火把，教人用耳朵听林中的动静。",
            "type": "野外",
            "lv": 54,
            "npcs": ["npc_moonshadow_hunter"],
            "monsters": [
                [
                    "m_shadow_panther",
                    "影豹",
                    "speedster",
                    54,
                    [
                        "ms_pu_ji",
                        "ms_qian_xing"
                    ],
                    [
                        "影豹皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "moonshadow_wood_2",
            "name": "影径",
            "icon": "🌲",
            "desc": "影径上光斑碎成一片，月影兽贴着树影潜行。荧光狐在暗处拖出一道微光。",
            "type": "野外",
            "lv": 58,
            "npcs": [],
            "monsters": [
                [
                    "m_moon_shade",
                    "月影兽",
                    "dps",
                    56,
                    [
                        "ms_an_ying_zhao",
                        "ms_yue_guang_zhan"
                    ],
                    [
                        "月影之爪"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "moonshadow_wood_3",
            "name": "月影深处",
            "icon": "🌲",
            "desc": "林深处一片漆黑，只有荧光生物零星闪烁。月影领主·夜歌的歌声从某个方向飘来，辨不清远近。",
            "type": "野外",
            "lv": 62,
            "npcs": [],
            "monsters": [
                [
                    "m_glow_fox",
                    "荧光狐",
                    "healer",
                    58,
                    [
                        "ms_mei_huo",
                        "ms_ying_guang_shan"
                    ],
                    [
                        "荧光狐尾"
                    ]
                ],
                ],
            "elite": [
                "e_moonshadow_lord",
                "月影领主·夜歌",
                "elite",
                62,
                [
                    "ms_an_ying_zhao",
                    "ms_yue_guang_zhan",
                    "ms_zhao_huan_ying_bao"
                ],
                [
                    "夜歌之眼"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "frost_horn": [
        {
            "id": "frost_horn_1",
            "name": "堡垒广场",
            "icon": "🏘️",
            "desc": "霜角堡的广场上竖着兽骨图腾，炉火盆烧得正旺。守备军与猎人来来往往，北地的粗犷写在这座堡垒的每一块石头上。",
            "type": "城镇",
            "lv": 60,
            "npcs": [
                "npc_tavern_burnkettle",
                "npc_garrison",
                'npc_frost_leather',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "frost_horn_2",
            "name": "酋长大厅",
            "icon": "🏘️",
            "desc": "酋长大厅里挂着巨熊皮与战矛，火塘把大厅烤得温暖。酋长坐在主位上，目光如北地的风。",
            "type": "城镇",
            "lv": 60,
            "npcs": [
                "npc_north_chief",
                'npc_frost_elder',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "frost_horn_3",
            "name": "霜角酒馆",
            "icon": "🏘️",
            "desc": "酒馆的梁上挂着霜冻的鹿角，炉火边围坐着猎人。他们的酒杯里装着北地的烈酒与传说。",
            "type": "城镇",
            "lv": 60,
            "npcs": [
                "npc_frost_hunter",
                'npc_frost_drinker',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "lore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "frost_horn_4",
            "name": "守备营",
            "icon": "🏘️",
            "desc": "守备营的帐篷排列整齐，织工在灯下修补旗面。营火映着巡逻兵的脸，北风在帐外呼啸。",
            "type": "城镇",
            "lv": 60,
            "npcs": [
                "npc_frost_weaver",
                'npc_frost_armorer',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "frost_horn_5",
            "name": "随军圣堂",
            "icon": "🏘️",
            "desc": "随军圣堂是一间石头小屋，祭坛上点着不灭的烛火。随军牧师为出征的战士祈祷，声音低沉而坚定。",
            "type": "城镇",
            "lv": 60,
            "npcs": [
                "npc_field_priest"
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "heal"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "frost_horn_gate",
            "name": "寒角堡城门",
            "icon": "🏰",
            "desc": "寒角堡的兽骨城门裹着铁皮，门缝里透出北地的寒气。",
            "type": "城镇出口",
            "lv": 1,
            "npcs": ["npc_frost_horn_gate_guard"],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "frost_field": [
        {
            "id": "frost_field_1",
            "name": "霜原边缘",
            "icon": "🌲",
            "desc": "霜原的边缘覆着薄霜，草茎被冻成银针。猎人裹着皮裘跺脚取暖，雪狼在远处嗥叫。",
            "type": "野外",
            "lv": 62,
            "npcs": ["npc_frostfield_hunter"],
            "monsters": [
                [
                    "m_snow_wolf",
                    "雪狼",
                    "dps",
                    62,
                    [
                        "ms_si_yao",
                        "ms_bing_ya"
                    ],
                    [
                        "雪狼皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "frost_field_2",
            "name": "雪地",
            "icon": "🌲",
            "desc": "雪地一望无际，冰元素在雪雾中缓缓移动，身体像半透明的冰柱。",
            "type": "野外",
            "lv": 67,
            "npcs": [],
            "monsters": [
                [
                    "m_ice_elemental",
                    "冰元素",
                    "tank",
                    65,
                    [
                        "ms_bing_dan",
                        "ms_dong_jie"
                    ],
                    [
                        "冰元素核心"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "frost_field_3",
            "name": "霜原深处",
            "icon": "🌲",
            "desc": "霜原深处风雪交加，霜巨魔的身影在暴雪中若隐若现。霜巨魔王的山洞洞口结着厚厚的冰棱。",
            "type": "野外",
            "lv": 72,
            "npcs": [],
            "monsters": [
                [
                    "m_frost_troll",
                    "霜巨魔",
                    "dps",
                    68,
                    [
                        "ms_zhong_ji",
                        "ms_zai_sheng",
                        "ms_bing_ji"
                    ],
                    [
                        "霜巨魔血"
                    ]
                ],
                ],
            "elite": [
                "e_frost_troll_lord",
                "霜巨魔王",
                "elite",
                72,
                [
                    "ms_zhong_ji",
                    "ms_bing_ji",
                    "ms_zhao_huan_xue_lang"
                ],
                [
                    "霜巨魔王角"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "anvil_fort": [
        {
            "id": "anvil_fort_1",
            "name": "熔炉广场",
            "icon": "🏘️",
            "desc": "铁砧要塞的广场中央立着巨型铁砧，熔炉的火光映亮半边天。符文大师在这里接待来访者，矮人的锻声昼夜不息。",
            "type": "城镇",
            "lv": 65,
            "npcs": [
                "npc_rune_master",
                'npc_anvil_apprentice',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "anvil_fort_2",
            "name": "铁砧议会厅",
            "icon": "🏘️",
            "desc": "议会厅的圆桌由整块铁矿石凿成，矮人长老们围桌而坐，胡须被炉火映成金色。",
            "type": "城镇",
            "lv": 65,
            "npcs": [
                "npc_dwarf_elder",
                'npc_anvil_clerk',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "anvil_fort_3",
            "name": "符文工坊",
            "icon": "🏘️",
            "desc": "符文工坊里刻刀与符文石摆满长桌，工匠们屏息凝神地凿刻。酿酒的矮人偶尔探头，送来一桶麦酒。",
            "type": "城镇",
            "lv": 65,
            "npcs": [
                "npc_anvil_brewer",
                'npc_anvil_runeapp',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop",
                "craft"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "anvil_fort_gate",
            "name": "铁砧堡闸门",
            "icon": "🏰",
            "desc": "铁砧堡的矮人闸门是整块精铁浇铸，门闩粗如树桩，凿着符文。",
            "type": "城镇出口",
            "lv": 1,
            "npcs": ["npc_anvil_fort_gate_guard", 'npc_anvil_mule'],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "forge_valley": [
        {
            "id": "forge_valley_1",
            "name": "谷口",
            "icon": "🌲",
            "desc": "熔炉谷的谷口热气扑面，火蜥蜴趴在滚烫的岩石上。矿工们沿着谷壁凿取矿石。",
            "type": "野外",
            "lv": 66,
            "npcs": ["npc_forge_miner"],
            "monsters": [
                [
                    "m_fire_lizard",
                    "火蜥蜴",
                    "speedster",
                    66,
                    [
                        "ms_huo_dan"
                    ],
                    [
                        "火蜥蜴鳞"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "forge_valley_2",
            "name": "熔岩河畔",
            "icon": "🌲",
            "desc": "熔岩河在谷底缓缓流淌，红光映着岩壁。熔岩元素在河面浮沉，卷起一阵热浪。",
            "type": "野外",
            "lv": 71,
            "npcs": [],
            "monsters": [
                [
                    "m_lava_elemental",
                    "熔岩元素",
                    "tank",
                    70,
                    [
                        "ms_rong_yan_dan",
                        "ms_zhuo_shao"
                    ],
                    [
                        "熔岩核心"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "forge_valley_3",
            "name": "熔炉心",
            "icon": "🌲",
            "desc": "谷底最深处像个巨大的熔炉，矿魔在铁砧般的岩石间搬运矿石。熔岩领主的低吼让整个山谷震颤。",
            "type": "野外",
            "lv": 76,
            "npcs": [],
            "monsters": [
                [
                    "m_mining_demon",
                    "矿魔",
                    "dps",
                    72,
                    [
                        "ms_gao_ji",
                        "ms_huo_yan"
                    ],
                    [
                        "矿魔之角"
                    ]
                ],
                ],
            "elite": [
                "e_lava_lord",
                "熔岩领主",
                "elite",
                76,
                [
                    "ms_rong_yan_dan",
                    "ms_zhuo_shao",
                    "ms_di_lie"
                ],
                [
                    "熔岩领主核"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "black_forest": [
        {
            "id": "black_forest_1",
            "name": "林缘",
            "icon": "🌲",
            "desc": "黑森林的林缘，树木漆黑如炭。堕落的兽人酋长在树下磨刀，火把的光照不亮他的脸。",
            "type": "野外",
            "lv": 72,
            "npcs": [
                "npc_fallen_chief"
            ],
            "monsters": [
                [
                    "m_rot_orc",
                    "腐牙兽人",
                    "dps",
                    72,
                    [
                        "ms_fu_ji",
                        "ms_fu_shi"
                    ],
                    [
                        "腐牙兽牙"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "black_forest_2",
            "name": "腐林",
            "icon": "🌲",
            "desc": "腐林里气味刺鼻，树皮上长着发光的菌斑。黑暗精灵在枝桠间无声移动，像融化的影子。",
            "type": "野外",
            "lv": 77,
            "npcs": [],
            "monsters": [
                [
                    "m_dark_elf",
                    "黑暗精灵",
                    "speedster",
                    75,
                    [
                        "ms_an_ying_jian",
                        "ms_qian_xing"
                    ],
                    [
                        "黑暗精灵刃"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "black_forest_3",
            "name": "森林深处",
            "icon": "🌲",
            "desc": "森林深处连光都躲着走，腐蚀兽在泥潭边徘徊。北境猎人蹲在树后，示意来者噤声。",
            "type": "野外",
            "lv": 82,
            "npcs": [
                "npc_north_hunter"
            ],
            "monsters": [
                [
                    "m_corrupt_beast",
                    "腐蚀兽",
                    "tank",
                    78,
                    [
                        "ms_zhao_ji",
                        "ms_fu_shi"
                    ],
                    [
                        "腐蚀兽爪"
                    ]
                ],
                ],
            "elite": [
                "e_rot_chief_guard",
                "腐牙亲卫",
                "elite",
                80,
                [
                    "ms_fu_ji",
                    "ms_zhan_hou"
                ],
                [
                    "腐牙战徽"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "cinder_mountain": [
        {
            "id": "cinder_mountain_1",
            "name": "山脚",
            "icon": "🌲",
            "desc": "烬山的山脚覆着厚厚的火山灰，朝圣者跪在灰地里叩拜。小恶魔在岩缝间探头，发出尖细的笑声。",
            "type": "野外",
            "lv": 78,
            "npcs": [
                "npc_pilgrim"
            ],
            "monsters": [
                [
                    "m_imp",
                    "小恶魔",
                    "speedster",
                    78,
                    [
                        "ms_huo_dan",
                        "ms_zhao_ji"
                    ],
                    [
                        "小恶魔角"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "cinder_mountain_2",
            "name": "山腰",
            "icon": "🌲",
            "desc": "山腰的岩石被地热烤得发烫，地狱犬在热浪中穿行，鼻息喷出火星。",
            "type": "野外",
            "lv": 83,
            "npcs": [],
            "monsters": [
                [
                    "m_hellhound",
                    "地狱犬",
                    "dps",
                    80,
                    [
                        "ms_si_yao",
                        "ms_di_yu_huo"
                    ],
                    [
                        "地狱犬牙"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "cinder_mountain_3",
            "name": "火山口",
            "icon": "🌲",
            "desc": "火山口的岩浆翻涌如沸，深渊奴仆在边缘巡行。恶魔战士的巨影立在黑烟里，俯瞰着整座山。",
            "type": "野外",
            "lv": 88,
            "npcs": [],
            "monsters": [
                [
                    "m_demon_servant",
                    "深渊奴仆",
                    "tank",
                    82,
                    [
                        "ms_zhong_ji",
                        "ms_an_ying_dan"
                    ],
                    [
                        "奴仆锁链"
                    ]
                ],
                ],
            "elite": [
                "e_demon_warrior",
                "恶魔战士",
                "elite",
                86,
                [
                    "ms_zhang_jian",
                    "ms_di_yu_huo"
                ],
                [
                    "恶魔战刃"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "ash_temple": [
        {
            "id": "ash_temple_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "烬山祭坛入口：黑曜石砌成的门廊布满焦痕，门内飘出硫磺与灰烬的气味。祭坛深处的火光忽明忽暗。",
            "type": "副本",
            "lv": 82,
            "npcs": [
                "npc_eter",
                "npc_demon_priestess"
            ],
            "monsters": [
                [
                    "m_demon_priest",
                    "恶魔祭司",
                    "healer",
                    82,
                    [
                        "ms_an_ying_dan",
                        "ms_hei_an_zhi_liao"
                    ],
                    [
                        "染血祭器"
                    ]
                ],
                [
                    "m_seal_guardian",
                    "封印守卫(腐蚀)",
                    "tank",
                    86,
                    [
                        "ms_zhong_ji",
                        "ms_fu_shi"
                    ],
                    [
                        "碎裂封印石"
                    ]
                ],
                [
                    "b_helga",
                    "恶魔祭司·赫尔加",
                    "boss",
                    92,
                    [
                        "ms_an_ying_dan",
                        "ms_zhao_huan_e_mo",
                        "ms_hei_an_yi_shi"
                    ],
                    [
                        "赫尔加的祭器"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_helga",
                "恶魔祭司·赫尔加",
                "boss",
                92,
                [
                    "ms_an_ying_dan",
                    "ms_zhao_huan_e_mo",
                    "ms_hei_an_yi_shi"
                ],
                [
                    "赫尔加的祭器"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "abyss_gate": [
        {
            "id": "abyss_gate_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "深渊裂隙入口：大地裂开一道巨缝，边缘的岩石泛着诡异的紫光。缝隙深处传来若有若无的低语。",
            "type": "副本",
            "lv": 90,
            "npcs": [],
            "monsters": [
                [
                    "m_abyss_hound",
                    "深渊猎犬",
                    "dps",
                    90,
                    [
                        "ms_si_yao",
                        "ms_an_ying_zhao"
                    ],
                    [
                        "深渊犬牙"
                    ]
                ],
                [
                    "m_abyss_knight",
                    "深渊骑士",
                    "tank",
                    92,
                    [
                        "ms_jian_ji",
                        "ms_an_ying_zhan"
                    ],
                    [
                        "深渊骑士盔甲碎片"
                    ]
                ],
                [
                    "m_abyss_mage",
                    "深渊法师",
                    "healer",
                    94,
                    [
                        "ms_an_ying_dan",
                        "ms_hei_an_zhi_liao",
                        "ms_zhao_huan"
                    ],
                    [
                        "深渊法师杖"
                    ]
                ],
                [
                    "b_eter",
                    "蚀夜(真相形态)",
                    "boss",
                    100,
                    [
                        "ms_an_ying_zhan",
                        "ms_shen_yuan_zhi_nu",
                        "ms_zhao_huan_shen_yuan"
                    ],
                    [
                        "黎明之光碎片"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_eter",
                "蚀夜(真相形态)",
                "boss",
                100,
                [
                    "ms_an_ying_zhan",
                    "ms_shen_yuan_zhi_nu",
                    "ms_zhao_huan_shen_yuan"
                ],
                [
                    "黎明之光碎片"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "frost_fang": [
        {
            "id": "frost_fang_1",
            "name": "谷口",
            "icon": "🌲",
            "desc": "冰牙谷的谷口挂着冰凌，剑齿虎的脚印印在雪上。猎人裹紧皮衣，朝谷里张望。",
            "type": "野外",
            "lv": 63,
            "npcs": ["npc_frostfang_hunter"],
            "monsters": [
                [
                    "m_ice_sabre",
                    "冰牙剑齿虎",
                    "dps",
                    63,
                    [
                        "ms_si_yao",
                        "ms_bing_ya"
                    ],
                    [
                        "剑齿虎牙"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "frost_fang_2",
            "name": "冰径",
            "icon": "🌲",
            "desc": "冰径两侧冰柱如牙，雪原猛犸踏着积雪缓慢前行，震得冰面嗡嗡作响。",
            "type": "野外",
            "lv": 67,
            "npcs": [],
            "monsters": [
                [
                    "m_snow_mammoth",
                    "雪原猛犸",
                    "tank",
                    66,
                    [
                        "ms_chong_zhuang",
                        "ms_jian_ta"
                    ],
                    [
                        "猛犸毛"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "frost_fang_3",
            "name": "冰牙深处",
            "icon": "🌲",
            "desc": "谷底一片冰蓝，冰川雪兔在雪洞里探头。冰牙领主·霜白的巢穴就在那面冰壁之后。",
            "type": "野外",
            "lv": 71,
            "npcs": [],
            "monsters": [
                [
                    "m_glacier_rabbit",
                    "冰川雪兔",
                    "speedster",
                    68,
                    [
                        "ms_ji_pao",
                        "ms_bing_dan"
                    ],
                    [
                        "雪兔皮"
                    ]
                ],
                ],
            "elite": [
                "e_ice_fang_lord",
                "冰牙领主·霜白",
                "elite",
                71,
                [
                    "ms_si_yao",
                    "ms_bing_hou",
                    "ms_zhao_huan_xue_lang"
                ],
                [
                    "霜白獠牙"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "cold_ridge": [
        {
            "id": "cold_ridge_1",
            "name": "营地口",
            "icon": "🏘️",
            "desc": "寒脊营地的入口立着木栅与兽皮旗，篝火在风中跳动。猎人从雪原归来，靴子上挂着冰碴。",
            "type": "城镇",
            "lv": 68,
            "npcs": [
                "npc_cold_hunter",
                'npc_cold_skinner',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "cold_ridge_2",
            "name": "主帐篷",
            "icon": "🏘️",
            "desc": "主帐篷里炉火烧得正旺，牧民围坐喝着热汤。帐角的兽皮堆得老高，是这一季的收获。",
            "type": "城镇",
            "lv": 68,
            "npcs": [
                "npc_cold_herder",
                'npc_cold_oldherder',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "heal"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "cold_ridge_3",
            "name": "补给站",
            "icon": "🏘️",
            "desc": "补给站的货架上堆满干粮与箭矢，守火人往炉里添着柴。这里的热气与食物，是雪原上最实在的慰藉。",
            "type": "城镇",
            "lv": 68,
            "npcs": [
                "npc_cold_firekeeper",
                'npc_cold_bowyer',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "cold_ridge_sentry",
            "name": "雪原哨卡",
            "icon": "🛡️",
            "desc": "寒脊营地边缘的木栅哨卡，雪地里插着狼皮旗，哨位外是通往铁砧的雪道。",
            "type": "城镇出口",
            "lv": 68,
            "npcs": ["npc_cold_ridge_gate_guard", 'npc_cold_patrol'],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "winter_lake": [
        {
            "id": "winter_lake_1",
            "name": "湖畔",
            "icon": "🌲",
            "desc": "永冬湖的湖面结着厚厚的冰，湖冰元素在岸边徘徊。渔夫凿开冰洞，守着那根细线。",
            "type": "野外",
            "lv": 70,
            "npcs": ["npc_winterlake_fisher"],
            "monsters": [
                [
                    "m_lake_ice_elemental",
                    "湖冰元素",
                    "tank",
                    70,
                    [
                        "ms_bing_dan",
                        "ms_dong_jie"
                    ],
                    [
                        "湖冰核心"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "winter_lake_2",
            "name": "冰面",
            "icon": "🌲",
            "desc": "冰面光滑如镜，冰封鱼怪的影子在冰下缓缓游过，像冻结的梦。",
            "type": "野外",
            "lv": 75,
            "npcs": [],
            "monsters": [
                [
                    "m_frozen_fish",
                    "冰封鱼怪",
                    "dps",
                    72,
                    [
                        "ms_zhuang_ji",
                        "ms_shui_dan"
                    ],
                    [
                        "冻鱼鳞"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "winter_lake_3",
            "name": "湖心",
            "icon": "🌲",
            "desc": "湖心的冰层下隐约有巨大的黑影游动，湖中水灵在冰面上漂浮。永冬湖主·冰瞳就在这最冷的地方。",
            "type": "野外",
            "lv": 80,
            "npcs": [],
            "monsters": [
                [
                    "m_lake_spirit",
                    "湖中水灵",
                    "healer",
                    74,
                    [
                        "ms_shui_dan",
                        "ms_zhi_liao"
                    ],
                    [
                        "湖灵泪"
                    ]
                ],
                ],
            "elite": [
                "e_lake_lord",
                "永冬湖主·冰瞳",
                "elite",
                78,
                [
                    "ms_bing_xi",
                    "ms_ju_lang",
                    "ms_zhao_huan_shui_ling"
                ],
                [
                    "冰瞳之珠"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "frost_throne": [
        {
            "id": "frost_throne_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "冰霜王座入口：冰晶凝结的拱门晶莹剔透，寒气从门内涌出，在门槛上结成一层薄霜。",
            "type": "副本",
            "lv": 74,
            "npcs": [],
            "monsters": [],
            "elite": None,
            "boss": [
                "b_frost_lord",
                "冰霜领主",
                "boss",
                84,
                [
                    "ms_bing_xi",
                    "ms_dong_jie",
                    "ms_zhao_huan"
                ],
                [
                    "永冻之核"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "aurora_town": [
        {
            "id": "aurora_town_1",
            "name": "极光广场",
            "icon": "🏘️",
            "desc": "极光镇的广场上方，极光如纱幔般垂落。书记官在灯下抄录，把极光的颜色写进书里。",
            "type": "城镇",
            "lv": 70,
            "npcs": [
                "npc_aurora_scribe",
                'npc_aurora_lantern',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "aurora_town_2",
            "name": "镇长公馆",
            "icon": "🏘️",
            "desc": "镇长公馆的烟囱冒着白烟，门口挂着暖融融的灯笼。镇长在炉边接待来客，热茶冒着热气。",
            "type": "城镇",
            "lv": 70,
            "npcs": [
                "npc_aurora_mayor",
                'npc_aurora_butler',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "aurora_town_3",
            "name": "猎手营",
            "icon": "🏘️",
            "desc": "猎手营的墙上挂着狼皮与冰镐，刀锋般的北风在帐外呼啸。猎手们磨着刀，等着极光最亮的夜。",
            "type": "城镇",
            "lv": 70,
            "npcs": [
                "npc_frost_blade",
                'npc_aurora_reindeer',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "aurora_town_4",
            "name": "暖炉旅店",
            "icon": "🏘️",
            "desc": "旅店的炉火整夜不熄，暖炉边烤着湿透的手套。老板娘往汤里加着香料，屋里弥漫着安心的气味。",
            "type": "城镇",
            "lv": 70,
            "npcs": [
                "npc_warm_stove",
                'npc_aurora_innkeep2',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "heal"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "aurora_town_path",
            "name": "镇口雪径",
            "icon": "❄️",
            "desc": "极光镇口的雪径在极光下泛着幽蓝的光，雪松夹道，小路通向冰原与霜语峡谷。",
            "type": "城镇出口",
            "lv": 70,
            "npcs": ["npc_aurora_town_gate_guard", 'npc_aurora_sled'],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "permafrost_field": [
        {
            "id": "permafrost_field_1",
            "name": "冰原边缘",
            "icon": "🌲",
            "desc": "永冻冰原的边缘，冰脊如刀。雪橇夫系紧缰绳，冰原巨熊的足迹一直延伸到天际线。",
            "type": "野外",
            "lv": 68,
            "npcs": ["npc_permafrost_sledder"],
            "monsters": [
                [
                    "m_frost_bear",
                    "冰原巨熊",
                    "tank",
                    68,
                    [
                        "ms_xiong_zhang",
                        "ms_bing_hou"
                    ],
                    [
                        "冰熊皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "permafrost_field_2",
            "name": "冰原中",
            "icon": "🌲",
            "desc": "冰原中一片苍茫，极地冰狼在风中站成灰点。雪被风卷起，天地只剩下白与更白。",
            "type": "野外",
            "lv": 73,
            "npcs": [],
            "monsters": [
                [
                    "m_ice_wolf",
                    "极地冰狼",
                    "dps",
                    70,
                    [
                        "ms_si_yao",
                        "ms_bing_ya"
                    ],
                    [
                        "冰狼牙"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "permafrost_field_3",
            "name": "冰原深处",
            "icon": "🌲",
            "desc": "冰原深处的极光垂到地面，极光狐在光幕下奔跑。冰原猛犸·雪岭的巨影在雾中缓缓移动。",
            "type": "野外",
            "lv": 78,
            "npcs": [],
            "monsters": [
                [
                    "m_aurora_fox",
                    "极光狐",
                    "speedster",
                    72,
                    [
                        "ms_ji_chi",
                        "ms_ji_guang_shan"
                    ],
                    [
                        "极光狐尾"
                    ]
                ],
                ],
            "elite": [
                "e_frost_mammoth",
                "冰原猛犸·雪岭",
                "elite",
                76,
                [
                    "ms_chong_zhuang",
                    "ms_jian_ta",
                    "ms_bing_hou"
                ],
                [
                    "雪岭獠牙"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "frostwhisper_canyon": [
        {
            "id": "frostwhisper_canyon_1",
            "name": "峡谷口",
            "icon": "🌲",
            "desc": "霜语峡谷的谷口覆着冰霜，登山者系好绳索。冰蛇盘在岩缝里，吐着寒气。",
            "type": "野外",
            "lv": 72,
            "npcs": ["npc_frostwhisper_mountaineer"],
            "monsters": [
                [
                    "m_ice_serpent",
                    "冰蛇",
                    "speedster",
                    72,
                    [
                        "ms_du_ya",
                        "ms_bing_dong"
                    ],
                    [
                        "冰蛇鳞"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "frostwhisper_canyon_2",
            "name": "峡谷道",
            "icon": "🌲",
            "desc": "峡谷道两侧的冰壁上刻着古老的符文，霜语祭司在符文前低语，寒气随话音加重。",
            "type": "野外",
            "lv": 77,
            "npcs": [],
            "monsters": [
                [
                    "m_frost_cultist",
                    "霜语祭司",
                    "healer",
                    74,
                    [
                        "ms_bing_dan",
                        "ms_bing_shuang_zhu_fu"
                    ],
                    [
                        "霜语圣典"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "frostwhisper_canyon_3",
            "name": "霜语尽头",
            "icon": "🌲",
            "desc": "峡谷尽头的冰瀑凝固成蓝色，霜语巨魔守在瀑前。冰川龙·霜牙的吐息在冰雾中若隐若现。",
            "type": "野外",
            "lv": 82,
            "npcs": [],
            "monsters": [
                [
                    "m_frost_giant",
                    "霜语巨魔",
                    "tank",
                    78,
                    [
                        "ms_zhong_ji",
                        "ms_bing_ji"
                    ],
                    [
                        "霜语巨魔血"
                    ]
                ],
                ],
            "elite": [
                "e_glacier_wyrm",
                "冰川龙·霜牙",
                "elite",
                82,
                [
                    "ms_bing_xi",
                    "ms_long_zhao",
                    "ms_dong_jie"
                ],
                [
                    "霜牙龙鳞"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "dragon_pass": [
        {
            "id": "dragon_pass_1",
            "name": "山口广场",
            "icon": "🏘️",
            "desc": "龙脊山口的广场风很大，旗帜猎猎作响。驿站长在登记过往商旅，山道通向更高的龙脊。",
            "type": "城镇",
            "lv": 80,
            "npcs": [
                "npc_pass_stationmaster",
                'npc_pass_caravan',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "dragon_pass_2",
            "name": "龙裔长老堂",
            "icon": "🏘️",
            "desc": "长老堂的梁柱雕着龙纹，龙裔长老端坐堂中，鳞片在火光下泛着古铜色。",
            "type": "城镇",
            "lv": 80,
            "npcs": [
                "npc_dragon_elder",
                'npc_pass_attendant',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "dragon_pass_gate",
            "name": "山口关隘",
            "icon": "🏰",
            "desc": "龙裔山口的老关隘，石墙斑驳，风从隘口灌进来，呼呼作响。",
            "type": "城镇出口",
            "lv": 1,
            "npcs": ["npc_dragon_pass_gate_guard", 'npc_pass_sentinel'],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "dragon_ridge": [
        {
            "id": "dragon_ridge_1",
            "name": "山脚",
            "icon": "🌲",
            "desc": "龙脊山脉的山脚下，风裹着碎石。向导指着山道，龙裔战士的营地就扎在半山。",
            "type": "野外",
            "lv": 82,
            "npcs": ["npc_dragonridge_guide"],
            "monsters": [
                [
                    "m_dragonkin",
                    "龙裔战士",
                    "dps",
                    82,
                    [
                        "ms_long_jian_shu"
                    ],
                    [
                        "龙鳞碎片"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "dragon_ridge_2",
            "name": "山道",
            "icon": "🌲",
            "desc": "山道沿着龙脊蜿蜒，石龙伏在山脊上晒太阳，像一块活过来的岩石。",
            "type": "野外",
            "lv": 86,
            "npcs": [],
            "monsters": [
                [
                    "m_stone_dragon",
                    "石龙",
                    "tank",
                    85,
                    [
                        "ms_shi_xi",
                        "ms_zhong_ji"
                    ],
                    [
                        "石龙鳞"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "dragon_ridge_3",
            "name": "龙脊之巅",
            "icon": "🌲",
            "desc": "山巅云海翻涌，风龙在云层间盘旋，长啸声震得山石簌簌而落。",
            "type": "野外",
            "lv": 90,
            "npcs": [],
            "monsters": [
                [
                    "m_wind_dragon",
                    "风龙",
                    "speedster",
                    88,
                    [
                        "ms_feng_ren",
                        "ms_fu_chong"
                    ],
                    [
                        "风龙羽"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "dragon_roost": [
        {
            "id": "dragon_roost_1",
            "name": "巢外峭壁",
            "icon": "🌲",
            "desc": "龙巢外的峭壁被爪痕划得面目全非，幼年龙在崖边练习展翅，扇起一阵阵风。",
            "type": "野外",
            "lv": 88,
            "npcs": ["npc_dragonroost_dragonspeaker"],
            "monsters": [
                [
                    "m_young_dragon",
                    "幼年龙",
                    "dps",
                    88,
                    [
                        "ms_long_xi",
                        "ms_long_zhao"
                    ],
                    [
                        "幼龙鳞"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "dragon_roost_2",
            "name": "龙巢口",
            "icon": "🌲",
            "desc": "龙巢口堆着巨大的兽骨与财宝，龙崽在骨堆间打滚，发出奶声奶气的咆哮。",
            "type": "野外",
            "lv": 92,
            "npcs": [],
            "monsters": [
                [
                    "m_dragon_hatchling",
                    "龙崽",
                    "speedster",
                    90,
                    [
                        "ms_si_yao",
                        "ms_huo_dan"
                    ],
                    [
                        "龙崽爪"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "dragon_roost_3",
            "name": "巢穴深处",
            "icon": "🌲",
            "desc": "巢穴深处铺着厚厚的龙鳞，成年龙的呼吸如风箱般沉重。龙巢王·焰翼盘踞在黄金之上，眼神如熔岩。",
            "type": "野外",
            "lv": 96,
            "npcs": [],
            "monsters": [
                [
                    "m_adult_dragon",
                    "成年龙",
                    "tank",
                    92,
                    [
                        "ms_long_xi",
                        "ms_long_wei_190",
                        "ms_wei_ya"
                    ],
                    [
                        "成年龙鳞"
                    ]
                ],
                ],
            "elite": [
                "e_dragon_roost_king",
                "龙巢王·焰翼",
                "elite",
                96,
                [
                    "ms_long_xi",
                    "ms_lie_yan_zhao",
                    "ms_zhao_huan_long_zai"
                ],
                [
                    "焰翼龙鳞"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "ancient_battlefield": [
        {
            "id": "ancient_battlefield_1",
            "name": "战场边缘",
            "icon": "🌲",
            "desc": "古战场的边缘插着锈剑与断矛，战死骷髅从土里伸出半截指骨。学者蹲在地上，拓印着石碑上的铭文。",
            "type": "野外",
            "lv": 85,
            "npcs": [
                "npc_war_scholar"
            ],
            "monsters": [
                [
                    "m_battle_skeleton",
                    "战死骷髅",
                    "dps",
                    85,
                    [
                        "ms_jian_ji"
                    ],
                    [
                        "锈剑碎片"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "ancient_battlefield_2",
            "name": "战场中",
            "icon": "🌲",
            "desc": "战场中央雾气弥漫，战魂的轮廓在雾中游荡。马蹄印与兵刃的残骸铺满大地，仿佛战斗还没结束。",
            "type": "野外",
            "lv": 90,
            "npcs": [],
            "monsters": [
                [
                    "m_war_ghost",
                    "战魂",
                    "speedster",
                    88,
                    [
                        "ms_chuan_shen",
                        "ms_ai_hao"
                    ],
                    [
                        "战魂之尘"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "ancient_battlefield_3",
            "name": "战场核心",
            "icon": "🌲",
            "desc": "战场核心立着一座巨大的方尖碑，百族残骸环绕其下。风在这里呜咽，像在替亡者低诉。",
            "type": "野外",
            "lv": 95,
            "npcs": [],
            "monsters": [
                [
                    "m_battle_remnant",
                    "百族残骸",
                    "tank",
                    92,
                    [
                        "ms_zhong_ji",
                        "ms_fu_hua"
                    ],
                    [
                        "残骸核心"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "dragon_tomb": [
        {
            "id": "dragon_tomb_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "龙之墓入口：巨龙骸骨的胸腔形成天然拱门，龙骨上还残留着微弱的魔力光辉。墓穴深处仿佛有龙吟回荡。",
            "type": "副本",
            "lv": 90,
            "npcs": [],
            "monsters": [
                [
                    "m_dragon_ghost",
                    "龙魂",
                    "dps",
                    90,
                    [
                        "ms_long_xi",
                        "ms_long_zhao"
                    ],
                    [
                        "龙魂碎片"
                    ]
                ],
                [
                    "m_ancient_dragon",
                    "古龙",
                    "tank",
                    95,
                    [
                        "ms_long_xi",
                        "ms_long_wei_190",
                        "ms_wei_ya"
                    ],
                    [
                        "古龙鳞"
                    ]
                ],
                [
                    "b_om_shadow",
                    "古龙·奥姆之影",
                    "boss",
                    100,
                    [
                        "ms_long_xi",
                        "ms_long_zhao",
                        "ms_gu_long_wei_ya"
                    ],
                    [
                        "龙语传承"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_om_shadow",
                "古龙·奥姆之影",
                "boss",
                100,
                [
                    "ms_long_xi",
                    "ms_long_zhao",
                    "ms_gu_long_wei_ya"
                ],
                [
                    "龙语传承"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "dragon_kin": [
        {
            "id": "dragon_kin_1",
            "name": "聚落广场",
            "icon": "🏘️",
            "desc": "龙裔聚落的广场铺着龙纹石板，年轻龙裔在广场上比试拳脚。祭坛的烟柱在远处升腾。",
            "type": "城镇",
            "lv": 82,
            "npcs": [
                "npc_dragonkin_youth",
                'npc_dragonkin_child',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "dragon_kin_2",
            "name": "龙裔祭坛",
            "icon": "🏘️",
            "desc": "祭坛由龙骨与黑曜石砌成，长老在坛前低声吟诵。龙鳞在火光下微微发亮，仿佛仍在呼吸。",
            "type": "城镇",
            "lv": 82,
            "npcs": [
                "npc_dragonkin_elder",
                'npc_dragonkin_priestess',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "lore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "dragon_kin_3",
            "name": "旅店",
            "icon": "🏘️",
            "desc": "旅店由龙翼骨搭成骨架，铁匠在炉边打铁。炉火与肉香让这个聚落有了家的温度。",
            "type": "城镇",
            "lv": 82,
            "npcs": [
                "npc_dragonkin_smith",
                'npc_dragonkin_cook',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "heal"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "dragon_kin_mouth",
            "name": "聚落口",
            "icon": "🐉",
            "desc": "龙裔聚落的入口，两根龙牙石柱分立两侧，石阶向下延伸进龙裔谷道。",
            "type": "城镇出口",
            "lv": 82,
            "npcs": ["npc_dragon_kin_gate_guard"],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "bone_wild": [
        {
            "id": "bone_wild_1",
            "name": "荒野边缘",
            "icon": "🌲",
            "desc": "龙骨荒野的边缘，巨大的肋骨从沙土里拱出，像一座座白色的拱门。拾荒者弯腰翻找着骨头堆。",
            "type": "野外",
            "lv": 84,
            "npcs": ["npc_bonewild_scavenger"],
            "monsters": [
                [
                    "m_bone_wyrm",
                    "骨虫",
                    "speedster",
                    84,
                    [
                        "ms_gu_xi",
                        "ms_chuan_shen"
                    ],
                    [
                        "骨虫壳"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "bone_wild_2",
            "name": "骨堆区",
            "icon": "🌲",
            "desc": "骨堆区白骨累累，骨魔像在骨头间缓慢移动，关节发出咔咔的声响。",
            "type": "野外",
            "lv": 88,
            "npcs": [],
            "monsters": [
                [
                    "m_bone_golem",
                    "骨魔像",
                    "tank",
                    86,
                    [
                        "ms_zhong_ji",
                        "ms_gu_xi"
                    ],
                    [
                        "骨魔像核"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "bone_wild_3",
            "name": "荒野深处",
            "icon": "🌲",
            "desc": "荒野深处有一具完整的巨龙骸骨，骨鹫在脊骨上栖落。骨龙领主·骸王盘踞在龙骸的胸腔里。",
            "type": "野外",
            "lv": 92,
            "npcs": [],
            "monsters": [
                [
                    "m_bone_vulture",
                    "骨鹫",
                    "dps",
                    88,
                    [
                        "ms_fu_chong",
                        "ms_gu_xi"
                    ],
                    [
                        "骨鹫羽"
                    ]
                ],
                ],
            "elite": [
                "e_bone_lord",
                "骨龙领主·骸王",
                "elite",
                92,
                [
                    "ms_gu_xi",
                    "ms_long_zhao",
                    "ms_zhao_huan_gu_chong"
                ],
                [
                    "骸王龙骨"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "storm_cliff": [
        {
            "id": "storm_cliff_1",
            "name": "崖脚",
            "icon": "🌲",
            "desc": "风暴崖的崖脚浪花拍岸，风暴猎鹰在崖顶盘旋。守望者裹着斗篷，注视着海平面。",
            "type": "野外",
            "lv": 86,
            "npcs": ["npc_stormcliff_watcher"],
            "monsters": [
                [
                    "m_storm_hawk",
                    "风暴猎鹰",
                    "speedster",
                    86,
                    [
                        "ms_fu_chong",
                        "ms_lei_ji"
                    ],
                    [
                        "风暴鹰羽"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "storm_cliff_2",
            "name": "崖道",
            "icon": "🌲",
            "desc": "崖道贴着峭壁，雷蜥趴在岩石上，鳞片间偶尔迸出电弧。",
            "type": "野外",
            "lv": 90,
            "npcs": [],
            "monsters": [
                [
                    "m_thunder_lizard",
                    "雷蜥",
                    "dps",
                    88,
                    [
                        "ms_lei_ji",
                        "ms_si_yao"
                    ],
                    [
                        "雷蜥皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "storm_cliff_3",
            "name": "风暴崖顶",
            "icon": "🌲",
            "desc": "崖顶乌云压顶，风之守卫立在最高处，披风被风扯成直线。风暴崖主·雷鸣的雷光在云中穿梭。",
            "type": "野外",
            "lv": 94,
            "npcs": [],
            "monsters": [
                [
                    "m_wind_guardian",
                    "风之守卫",
                    "tank",
                    90,
                    [
                        "ms_feng_ren",
                        "ms_ying_hua"
                    ],
                    [
                        "风之核心"
                    ]
                ],
                ],
            "elite": [
                "e_storm_cliff_lord",
                "风暴崖主·雷鸣",
                "elite",
                94,
                [
                    "ms_lei_bao",
                    "ms_feng_bao_zhi_nu",
                    "ms_zhao_huan_lie_ying"
                ],
                [
                    "雷鸣之翼"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "storm_throne": [
        {
            "id": "storm_throne_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "风暴王座入口：雷云在入口上空盘旋，石阶上布满焦黑的闪电痕迹。门内狂风不止，吹得人睁不开眼。",
            "type": "副本",
            "lv": 90,
            "npcs": [],
            "monsters": [],
            "elite": None,
            "boss": [
                "b_storm_king",
                "风暴龙王",
                "boss",
                98,
                [
                    "ms_lei_bao",
                    "ms_feng_bao_zhi_yan",
                    "ms_zhao_huan_lei_niao"
                ],
                [
                    "风暴之核"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "redridge_plateau": [
        {
            "id": "redridge_plateau_1",
            "name": "高原边缘",
            "icon": "🌲",
            "desc": "赤脊高原的边缘，红土裸露，赤脊迅猛龙在远处奔跑，扬起一路尘烟。龙牧人吹着号角收拢龙群。",
            "type": "野外",
            "lv": 84,
            "npcs": ["npc_redridge_dragonherd"],
            "monsters": [
                [
                    "m_red_raptor",
                    "赤脊迅猛龙",
                    "speedster",
                    84,
                    [
                        "ms_pu_ji",
                        "ms_si_yao"
                    ],
                    [
                        "迅猛龙爪"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "redridge_plateau_2",
            "name": "赤脊中",
            "icon": "🌲",
            "desc": "高原中部岩柱林立，岩龙伏在石柱上，皮肤与岩石浑然一体。",
            "type": "野外",
            "lv": 88,
            "npcs": [],
            "monsters": [
                [
                    "m_rock_drake",
                    "岩龙",
                    "tank",
                    86,
                    [
                        "ms_shi_xi",
                        "ms_zhong_ji"
                    ],
                    [
                        "岩龙鳞"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "redridge_plateau_3",
            "name": "高原深处",
            "icon": "🌲",
            "desc": "高原深处的天空常有赤翼飞龙掠过，赤龙领主·烬翼的巢穴就在那座冒烟的火山上。",
            "type": "野外",
            "lv": 92,
            "npcs": [],
            "monsters": [
                [
                    "m_red_wyvern",
                    "赤翼飞龙",
                    "dps",
                    88,
                    [
                        "ms_fu_chong",
                        "ms_huo_dan"
                    ],
                    [
                        "赤翼羽"
                    ]
                ],
                ],
            "elite": [
                "e_red_dragon_lord",
                "赤龙领主·烬翼",
                "elite",
                92,
                [
                    "ms_long_xi",
                    "ms_lie_yan_zhao",
                    "ms_wei_ya"
                ],
                [
                    "烬翼龙鳞"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "dragonsfall_valley": [
        {
            "id": "dragonsfall_valley_1",
            "name": "谷口",
            "icon": "🌲",
            "desc": "龙陨谷的谷口竖着一块断碑，学者们在碑前争论着铭文的含义。骨龙在谷中低空滑过。",
            "type": "野外",
            "lv": 88,
            "npcs": ["npc_dragonsfall_scholar"],
            "monsters": [
                [
                    "m_bone_dragon",
                    "骨龙",
                    "tank",
                    88,
                    [
                        "ms_gu_xi",
                        "ms_si_yao"
                    ],
                    [
                        "骨龙残骸"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "dragonsfall_valley_2",
            "name": "龙骸区",
            "icon": "🌲",
            "desc": "龙骸区散落着巨大的龙骨，龙裔亡灵在骨头间徘徊，空洞的眼窝里燃着幽火。",
            "type": "野外",
            "lv": 92,
            "npcs": [],
            "monsters": [
                [
                    "m_dragon_wraith",
                    "龙裔亡灵",
                    "speedster",
                    90,
                    [
                        "ms_chuan_shen",
                        "ms_long_yu_ai_hao"
                    ],
                    [
                        "龙裔残魂"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "dragonsfall_valley_3",
            "name": "谷底",
            "icon": "🌲",
            "desc": "谷底铺满龙鳞与碎石，龙鳞兽在裂缝间爬行。龙陨战魂·暮影立在谷底最深处，铠甲上刻着古老的纹章。",
            "type": "野外",
            "lv": 96,
            "npcs": [],
            "monsters": [
                [
                    "m_dragonscale_beast",
                    "龙鳞兽",
                    "dps",
                    92,
                    [
                        "ms_si_yao",
                        "ms_long_lin_chong_ji"
                    ],
                    [
                        "龙鳞兽皮"
                    ]
                ],
                ],
            "elite": [
                "e_dragon_lord_ghost",
                "龙陨战魂·暮影",
                "elite",
                96,
                [
                    "ms_long_xi",
                    "ms_long_zhao",
                    "ms_zhao_huan_gu_long"
                ],
                [
                    "暮影龙魂"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "jade_port": [
        {
            "id": "jade_port_1",
            "name": "港口广场",
            "icon": "🏘️",
            "desc": "翡翠港的广场堆着木箱与绳缆，卸货工的号子声此起彼伏。港务官拿着账本，清点着到港的船只。",
            "type": "城镇",
            "lv": 35,
            "npcs": [
                "npc_jade_docker",
                'npc_jade_sailor',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "jade_port_2",
            "name": "翡翠集市",
            "icon": "🏘️",
            "desc": "集市上玉石与香料摆满摊位，雕刻匠在摊后雕着翡翠。讨价还价声混着海风，热闹非常。",
            "type": "城镇",
            "lv": 35,
            "npcs": [
                "npc_jade_carver",
                'npc_jade_spice',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop",
                "stall"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "jade_port_3",
            "name": "船坞旅店",
            "icon": "🏘️",
            "desc": "船坞旅店的窗子正对着船桅，掌舵手们在这里歇脚。入夜后，港湾的灯火在窗玻璃上摇晃。",
            "type": "城镇",
            "lv": 35,
            "npcs": [
                "npc_jade_helmsman",
                'npc_jade_waiter',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "heal"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "jade_port_dock",
            "name": "翡翠码头",
            "icon": "⛵",
            "desc": "翡翠港的泊位栈桥，船缆系在木桩上，潮声阵阵，从这里登船可去往群岛海域。",
            "type": "城镇出口",
            "lv": 35,
            "npcs": ["npc_jade_port_gate_guard"],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "shell_town": [
        {
            "id": "shell_town_1",
            "name": "贝壳集市",
            "icon": "🏘️",
            "desc": "贝壳镇的集市用贝壳和珊瑚搭成摊位，拾贝人把新捡的贝壳摆上架，在阳光下闪着珠光。",
            "type": "城镇",
            "lv": 40,
            "npcs": [
                "npc_shell_picker",
                'npc_shell_coral',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop",
                "stall"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "shell_town_2",
            "name": "码头",
            "icon": "🏘️",
            "desc": "码头拴着几艘渔船，渔网挂在桩上滴着水。织网人坐在栈桥边，哼着潮水的调子。",
            "type": "城镇",
            "lv": 40,
            "npcs": [
                "npc_shell_netter",
                'npc_shell_fisher',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "shell_town_3",
            "name": "旅店",
            "icon": "🏘️",
            "desc": "旅店的墙上嵌着各色贝壳，海风从窗缝里钻进来。店主端上一碗热鱼汤，驱散海上的寒气。",
            "type": "城镇",
            "lv": 40,
            "npcs": [
                "npc_shell_gatherer",
                'npc_shell_helper',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "heal"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "shell_town_beach",
            "name": "渔港滩",
            "icon": "🌊",
            "desc": "贝壳镇外的沙滩泊着几艘独木舟，退潮后礁石露出来，海路通向珊瑚礁与海妖湾。",
            "type": "城镇出口",
            "lv": 40,
            "npcs": ["npc_shell_town_gate_guard", 'npc_shell_kelp'],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "coral_reef": [
        {
            "id": "coral_reef_1",
            "name": "礁滩",
            "icon": "🌲",
            "desc": "珊瑚礁的礁滩水色清浅，巨钳海蟹在礁石间横行。采珠人深吸一口气，潜入碧蓝的水中。",
            "type": "野外",
            "lv": 36,
            "npcs": ["npc_coral_pearldiver"],
            "monsters": [
                [
                    "m_sea_crab",
                    "巨钳海蟹",
                    "tank",
                    36,
                    [
                        "ms_qian_ji",
                        "ms_ying_hua"
                    ],
                    [
                        "蟹壳"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "coral_reef_2",
            "name": "珊瑚丛",
            "icon": "🌲",
            "desc": "珊瑚丛如海底森林，海星怪趴在珊瑚枝上，色彩斑斓得让人目眩。",
            "type": "野外",
            "lv": 40,
            "npcs": [],
            "monsters": [
                [
                    "m_star_beast",
                    "海星怪",
                    "dps",
                    38,
                    [
                        "ms_chan_rao",
                        "ms_du_ci"
                    ],
                    [
                        "海星片"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "coral_reef_3",
            "name": "礁群深处",
            "icon": "🌲",
            "desc": "礁群深处的珊瑚如巨树般林立，河豚怪鼓着身子游过。珊瑚礁主·红棘的巢穴藏在最艳丽的珊瑚后面。",
            "type": "野外",
            "lv": 44,
            "npcs": [],
            "monsters": [
                [
                    "m_puffer",
                    "河豚怪",
                    "speedster",
                    40,
                    [
                        "ms_du_ci",
                        "ms_peng_zhang"
                    ],
                    [
                        "河豚毒素"
                    ]
                ],
                ],
            "elite": [
                "e_reef_king",
                "珊瑚礁主·红棘",
                "elite",
                42,
                [
                    "ms_qian_ji",
                    "ms_jing_ji_chan_rao"
                ],
                [
                    "红棘珊瑚"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "sunset_isle": [
        {
            "id": "sunset_isle_1",
            "name": "岛滩",
            "icon": "🌲",
            "desc": "落日岛的沙滩泛着金色的光，岛野猪在椰林边拱土。岛民晒着渔网，海风里带着果香。",
            "type": "野外",
            "lv": 42,
            "npcs": ["npc_sunset_islander"],
            "monsters": [
                [
                    "m_island_boar",
                    "岛野猪",
                    "dps",
                    42,
                    [
                        "ms_chong_zhuang"
                    ],
                    [
                        "岛猪牙"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "sunset_isle_2",
            "name": "岛林",
            "icon": "🌲",
            "desc": "岛林里藤蔓交错，巨型鬣蜥趴在树干上，吐着分叉的舌头。",
            "type": "野外",
            "lv": 47,
            "npcs": [],
            "monsters": [
                [
                    "m_giant_iguana",
                    "巨型鬣蜥",
                    "speedster",
                    44,
                    [
                        "ms_si_yao",
                        "ms_shuai_wei"
                    ],
                    [
                        "鬣蜥皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "sunset_isle_3",
            "name": "岛心",
            "icon": "🌲",
            "desc": "岛心有一座沉睡的火山口，鹦鹉魔在树冠间聒噪。落日岛虎·金焰的领地就在火山口的林间。",
            "type": "野外",
            "lv": 52,
            "npcs": [],
            "monsters": [
                [
                    "m_parrot_demon",
                    "鹦鹉魔",
                    "healer",
                    46,
                    [
                        "ms_jian_xiao",
                        "ms_feng_ren"
                    ],
                    [
                        "鹦鹉羽"
                    ]
                ],
                ],
            "elite": [
                "e_island_tiger",
                "落日岛虎·金焰",
                "elite",
                48,
                [
                    "ms_si_yao",
                    "ms_pu_ji",
                    "ms_lie_yan_zhao"
                ],
                [
                    "金焰虎皮"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "storm_strait": [
        {
            "id": "storm_strait_1",
            "name": "海峡口",
            "icon": "🌲",
            "desc": "风暴海峡的入口浪急风高，风暴元素在浪尖上成形又消散。领航员眯眼望着天色，估算着过峡的时机。",
            "type": "野外",
            "lv": 48,
            "npcs": ["npc_stormstrait_navigator"],
            "monsters": [
                [
                    "m_storm_element",
                    "风暴元素",
                    "dps",
                    48,
                    [
                        "ms_lei_ji",
                        "ms_feng_ren"
                    ],
                    [
                        "风暴核心"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "storm_strait_2",
            "name": "急流区",
            "icon": "🌲",
            "desc": "急流区的水像沸腾的墨，漩涡精灵在旋涡中旋转，卷起白沫。",
            "type": "野外",
            "lv": 53,
            "npcs": [],
            "monsters": [
                [
                    "m_whirlpool_spirit",
                    "漩涡精灵",
                    "healer",
                    50,
                    [
                        "ms_shui_dan",
                        "ms_xuan_wo"
                    ],
                    [
                        "漩涡泪"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "storm_strait_3",
            "name": "海峡深处",
            "icon": "🌲",
            "desc": "海峡深处暗流涌动，海蛇在水下翻卷。风暴巨兽的背脊偶尔破开海面，又沉入深处。",
            "type": "野外",
            "lv": 58,
            "npcs": [],
            "monsters": [
                [
                    "m_sea_serpent",
                    "海蛇",
                    "tank",
                    52,
                    [
                        "ms_jiao_sha",
                        "ms_shui_xi"
                    ],
                    [
                        "海蛇鳞"
                    ]
                ],
                ],
            "elite": [
                "e_storm_leviathan",
                "风暴巨兽",
                "elite",
                56,
                [
                    "ms_lei_ji",
                    "ms_ju_lang"
                ],
                [
                    "巨兽之牙"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "mermaid_bay": [
        {
            "id": "mermaid_bay_1",
            "name": "湾口",
            "icon": "🌲",
            "desc": "海妖湾的湾口飘着雾气，渔家女在礁石上晾着网。海妖斥候的身影在雾中一闪而过。",
            "type": "野外",
            "lv": 45,
            "npcs": ["npc_mermaidbay_fishergirl"],
            "monsters": [
                [
                    "m_siren_scout",
                    "海妖斥候",
                    "speedster",
                    45,
                    [
                        "ms_mei_huo_zhi_ge"
                    ],
                    [
                        "海妖鳞"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "mermaid_bay_2",
            "name": "珊瑚湾",
            "icon": "🌲",
            "desc": "珊瑚湾的水色如蓝宝石，鲛人战士持着三叉戟在珊瑚间巡游。",
            "type": "野外",
            "lv": 50,
            "npcs": [],
            "monsters": [
                [
                    "m_merrow",
                    "鲛人战士",
                    "dps",
                    48,
                    [
                        "ms_san_cha_ji",
                        "ms_shui_dan"
                    ],
                    [
                        "鲛人鳞"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "mermaid_bay_3",
            "name": "海妖巢",
            "icon": "🌲",
            "desc": "海妖巢的洞口挂着海藻帘幕，歌声从深处传来，像丝绸一样缠上人的脚步。海妖领主·潮汐就在最深处。",
            "type": "野外",
            "lv": 55,
            "npcs": [],
            "monsters": [
                ],
            "elite": [
                "e_siren_lord",
                "海妖领主·潮汐",
                "elite",
                52,
                [
                    "ms_mei_huo",
                    "ms_ju_lang"
                ],
                [
                    "潮汐之泪"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "sunken_ship": [
        {
            "id": "sunken_ship_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "沉船湾入口：一艘古船的残骸半埋在沙滩上，船身倾斜，桅杆折断。退潮时能看到船舷上的古老徽记。",
            "type": "副本",
            "lv": 38,
            "npcs": [],
            "monsters": [
                [
                    "m_ghost_sailor",
                    "幽灵水手",
                    "dps",
                    38,
                    [
                        "ms_xiu_jian",
                        "ms_ai_hao"
                    ],
                    [
                        "幽灵帆布"
                    ]
                ],
                [
                    "m_drowned",
                    "溺死者",
                    "tank",
                    42,
                    [
                        "ms_zhao_ji",
                        "ms_chan_rao"
                    ],
                    [
                        "海藻缠绕"
                    ]
                ],
                [
                    "b_ghost_captain",
                    "幽灵船长·克罗",
                    "boss",
                    48,
                    [
                        "ms_wan_dao",
                        "ms_zhao_huan_you_ling",
                        "ms_zu_zhou"
                    ],
                    [
                        "克罗的罗盘"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_ghost_captain",
                "幽灵船长·克罗",
                "boss",
                48,
                [
                    "ms_wan_dao",
                    "ms_zhao_huan_you_ling",
                    "ms_zu_zhou"
                ],
                [
                    "克罗的罗盘"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "siren_nest": [
        {
            "id": "siren_nest_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "海妖巢穴入口：礁石间的洞口被贝壳与海藻覆盖，洞口传出缥缈的歌声，让人不由自主地想要靠近。",
            "type": "副本",
            "lv": 52,
            "npcs": [],
            "monsters": [
                [
                    "m_siren_elite",
                    "海妖精英",
                    "dps",
                    52,
                    [
                        "ms_mei_huo",
                        "ms_du_ci"
                    ],
                    [
                        "海妖之羽"
                    ]
                ],
                [
                    "m_kraken_tentacle",
                    "海妖触手",
                    "tank",
                    54,
                    [
                        "ms_jiao_sha",
                        "ms_shui_xi"
                    ],
                    [
                        "触手皮"
                    ]
                ],
                [
                    "b_siren_queen",
                    "海妖女王·蓝歌",
                    "boss",
                    60,
                    [
                        "ms_mei_huo_zhi_ge",
                        "ms_ju_lang",
                        "ms_zhao_huan_chu_shou"
                    ],
                    [
                        "蓝歌之冠"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_siren_queen",
                "海妖女王·蓝歌",
                "boss",
                60,
                [
                    "ms_mei_huo_zhi_ge",
                    "ms_ju_lang",
                    "ms_zhao_huan_chu_shou"
                ],
                [
                    "蓝歌之冠"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "nameless_harbor": [
        {
            "id": "nameless_harbor_1",
            "name": "港口广场",
            "icon": "🏘️",
            "desc": "无名港的广场没有旗帜也没有名字，猫女掌柜在摊位后数着硬币。这里的规矩只有一条：不问来处。",
            "type": "城镇",
            "lv": 55,
            "npcs": [
                "npc_nameless_catwoman",
                'npc_nameless_sellsword',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "nameless_harbor_2",
            "name": "港务厅",
            "icon": "🏘️",
            "desc": "港务厅的墙上贴满发黄的航图，港务长在灯下描着航线。进港的船在这里留下名字与货单。",
            "type": "城镇",
            "lv": 55,
            "npcs": [
                "npc_harbor_master",
                'npc_nameless_clerk',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "nameless_harbor_3",
            "name": "远洋码头",
            "icon": "🏘️",
            "desc": "远洋码头的船都吃水很深，船长梅利安站在船头，眺望着无尽海的方向。这里出发的船，不问归期。",
            "type": "城镇",
            "lv": 55,
            "npcs": [
                "npc_captain_maelian",
                'npc_nameless_deckhand',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "nameless_harbor_anchorage",
            "name": "外锚地",
            "icon": "⚓",
            "desc": "无名港灯塔下的外海锚区，雾钟在风里低鸣，远洋船从这里启航驶向无尽海。",
            "type": "城镇出口",
            "lv": 55,
            "npcs": ["npc_nameless_harbor_gate_guard", 'npc_nameless_pilot'],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "pearl_city": [
        {
            "id": "pearl_city_1",
            "name": "珍珠广场",
            "icon": "🏘️",
            "desc": "珍珠城的广场铺着珍珠母碎屑，在阳光下泛着虹彩。海鸥在雕像上歇脚，老鲸夫在长椅上讲着海的故事。",
            "type": "城镇",
            "lv": 62,
            "npcs": [
                "npc_sea_gull_tim",
                "npc_old_whale",
                'npc_pearl_crafter',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "pearl_city_2",
            "name": "城主府",
            "icon": "🏘️",
            "desc": "城主府的穹顶镶着整排夜明珠，珍珠城主在殿中接见来客。潮声透过墙壁，像这座城的呼吸。",
            "type": "城镇",
            "lv": 62,
            "npcs": [
                "npc_pearl_lord",
                'npc_pearl_lady',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "pearl_city_3",
            "name": "珊瑚拍卖行",
            "icon": "🏘️",
            "desc": "拍卖行的展台上摆着珍稀珊瑚与深海宝物，拍卖师的木槌敲一下，就是一笔以海为名的交易。",
            "type": "城镇",
            "lv": 62,
            "npcs": [
                "npc_coral_auctioneer",
                'npc_pearl_auction2',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "auction"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "pearl_city_4",
            "name": "商行",
            "icon": "🏘️",
            "desc": "商行的货架上摆满珍珠与海货，采珠人把今日的收获倒上柜台，掌柜眯眼估价。",
            "type": "城镇",
            "lv": 62,
            "npcs": [
                "npc_pearl_diver",
                'npc_pearl_merchant',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "pearl_city_5",
            "name": "渔港",
            "icon": "🏘️",
            "desc": "渔港里桅杆林立，渔船随波起伏。摆渡人撑着船在船缝间穿行，把渔获一篓篓送上岸。",
            "type": "城镇",
            "lv": 62,
            "npcs": [
                "npc_pearl_shuttler",
                'npc_pearl_fishwife',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "pearl_city_gate",
            "name": "珍珠城水门",
            "icon": "🏰",
            "desc": "珍珠城的水门立在浅湾中，门柱镶着蚌壳与珍珠母，潮起潮落。",
            "type": "城镇出口",
            "lv": 1,
            "npcs": ["npc_pearl_city_gate_guard"],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "mist_trench": [
        {
            "id": "mist_trench_1",
            "name": "海沟口",
            "icon": "🌲",
            "desc": "迷雾海沟的入口雾气翻涌，潜水人检查着气囊。深渊水母在沟口缓缓漂浮，触须泛着幽蓝的光。",
            "type": "野外",
            "lv": 56,
            "npcs": ["npc_misttrench_diver"],
            "monsters": [
                [
                    "m_abyss_jelly",
                    "深渊水母",
                    "healer",
                    56,
                    [
                        "ms_du_ci",
                        "ms_ying_guang_shan"
                    ],
                    [
                        "水母凝胶"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "mist_trench_2",
            "name": "迷雾区",
            "icon": "🌲",
            "desc": "迷雾区的海水浑浊如墨，暗礁鲨的背鳍在水面划出一道道轨迹。",
            "type": "野外",
            "lv": 60,
            "npcs": [],
            "monsters": [
                [
                    "m_reef_shark",
                    "暗礁鲨",
                    "dps",
                    58,
                    [
                        "ms_si_yao",
                        "ms_chong_zhuang"
                    ],
                    [
                        "鲨鱼牙"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "mist_trench_3",
            "name": "海沟深处",
            "icon": "🌲",
            "desc": "海沟深处的光线彻底消失，迷雾章鱼的触手从黑暗中探出。海沟巨兽·渊影的呼吸让海水都在震颤。",
            "type": "野外",
            "lv": 64,
            "npcs": [],
            "monsters": [
                [
                    "m_mist_octopus",
                    "迷雾章鱼",
                    "tank",
                    60,
                    [
                        "ms_chan_rao",
                        "ms_mo_zhi"
                    ],
                    [
                        "章鱼墨囊"
                    ]
                ],
                ],
            "elite": [
                "e_trench_leviathan",
                "海沟巨兽·渊影",
                "elite",
                64,
                [
                    "ms_tun_shi",
                    "ms_ju_lang",
                    "ms_zhao_huan_shui_mu"
                ],
                [
                    "渊影之鳞"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "whale_domain": [
        {
            "id": "whale_domain_1",
            "name": "海域边缘",
            "icon": "🌲",
            "desc": "龙鲸海域的边缘，海面平静如毯。观鲸人举着望远镜，幼年龙鲸在不远处喷出水柱。",
            "type": "野外",
            "lv": 60,
            "npcs": ["npc_whale_watcher"],
            "monsters": [
                [
                    "m_whale_calf",
                    "幼年龙鲸",
                    "tank",
                    60,
                    [
                        "ms_chong_zhuang",
                        "ms_shui_xi"
                    ],
                    [
                        "龙鲸脂"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "whale_domain_2",
            "name": "龙鲸路",
            "icon": "🌲",
            "desc": "龙鲸路的海面下掠过巨大的影子，巨型乌贼的腕足偶尔翻出水面，又缩回深处。",
            "type": "野外",
            "lv": 64,
            "npcs": [],
            "monsters": [
                [
                    "m_giant_squid",
                    "巨型乌贼",
                    "dps",
                    62,
                    [
                        "ms_jiao_sha",
                        "ms_mo_zhi"
                    ],
                    [
                        "乌贼腕足"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "whale_domain_3",
            "name": "海域深处",
            "icon": "🌲",
            "desc": "海域深处的洋流带着暖意，海蛇盘成团漂在海面。龙鲸王·涛声的歌声低沉悠长，传遍整片海域。",
            "type": "野外",
            "lv": 68,
            "npcs": [],
            "monsters": [
                [
                    "m_sea_serpent",
                    "海蛇",
                    "speedster",
                    64,
                    [
                        "ms_jiao_sha",
                        "ms_shui_xi"
                    ],
                    [
                        "海蛇鳞"
                    ]
                ],
                ],
            "elite": [
                "e_whale_king",
                "龙鲸王·涛声",
                "elite",
                68,
                [
                    "ms_shui_xi",
                    "ms_ju_lang",
                    "ms_zhao_huan_you_jing"
                ],
                [
                    "涛声鲸角"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "shipwreck_graveyard": [
        {
            "id": "shipwreck_graveyard_1",
            "name": "墓地边缘",
            "icon": "🌲",
            "desc": "沉船墓地的边缘，船骨从沙里戳出，像折断的手指。打捞人划着小船，在残骸间搜寻值钱的东西。",
            "type": "野外",
            "lv": 63,
            "npcs": ["npc_shipwreck_salvager"],
            "monsters": [
                [
                    "m_drowned_sailor",
                    "溺亡水手",
                    "dps",
                    63,
                    [
                        "ms_xiu_jian"
                    ],
                    [
                        "水手骨牌"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "shipwreck_graveyard_2",
            "name": "沉船区",
            "icon": "🌲",
            "desc": "沉船区桅杆林立，船幽灵在破甲板上飘荡。缆绳与帆布在风里拍打，像在招魂。",
            "type": "野外",
            "lv": 67,
            "npcs": [],
            "monsters": [
                [
                    "m_ship_ghost",
                    "船幽灵",
                    "speedster",
                    65,
                    [
                        "ms_chuan_shen",
                        "ms_ai_hao"
                    ],
                    [
                        "幽灵帆布"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "shipwreck_graveyard_3",
            "name": "墓地核心",
            "icon": "🌲",
            "desc": "墓地核心沉着一艘巨大的古船，受诅船长站在船头，目光空洞。沉船领主·溺骨的气息让海水都变冷。",
            "type": "野外",
            "lv": 71,
            "npcs": [],
            "monsters": [
                [
                    "m_cursed_captain",
                    "受诅船长",
                    "healer",
                    67,
                    [
                        "ms_zu_zhou",
                        "ms_zhi_hui"
                    ],
                    [
                        "船长罗盘"
                    ]
                ],
                ],
            "elite": [
                "e_graveyard_lord",
                "沉船领主·溺骨",
                "elite",
                71,
                [
                    "ms_wan_dao",
                    "ms_zhao_huan_shui_shou",
                    "ms_zu_zhou"
                ],
                [
                    "溺骨之锚"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "storm_sea": [
        {
            "id": "storm_sea_1",
            "name": "海缘",
            "icon": "🌲",
            "desc": "风暴之海的边缘，云层低低压着海面。观测者守在崖上，记录着每一道闪电的方向。",
            "type": "野外",
            "lv": 66,
            "npcs": ["npc_stormsea_observer"],
            "monsters": [
                [
                    "m_storm_wisp",
                    "风暴之灵",
                    "speedster",
                    66,
                    [
                        "ms_lei_ji",
                        "ms_feng_ren"
                    ],
                    [
                        "风暴之灵尘"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "storm_sea_2",
            "name": "风暴区",
            "icon": "🌲",
            "desc": "风暴区的浪有城墙高，雷鳗在闪电落下的瞬间跃出水面，银光一闪。",
            "type": "野外",
            "lv": 70,
            "npcs": [],
            "monsters": [
                [
                    "m_thunder_eel",
                    "雷鳗",
                    "dps",
                    68,
                    [
                        "ms_lei_ji",
                        "ms_chan_rao"
                    ],
                    [
                        "雷鳗皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "storm_sea_3",
            "name": "海眼",
            "icon": "🌲",
            "desc": "海眼的风暴永不停歇，海巨人踩着浪峰走过。风暴海龙·雷鸣盘踞在风暴中央，龙翼掀起的风搅动着整片海。",
            "type": "野外",
            "lv": 74,
            "npcs": [],
            "monsters": [
                [
                    "m_sea_titan",
                    "海巨人",
                    "tank",
                    70,
                    [
                        "ms_ju_lang",
                        "ms_zhong_ji"
                    ],
                    [
                        "海巨人鳞"
                    ]
                ],
                ],
            "elite": [
                "e_storm_dragon",
                "风暴海龙·雷鸣",
                "elite",
                74,
                [
                    "ms_long_xi",
                    "ms_lei_bao",
                    "ms_ju_lang"
                ],
                [
                    "雷鸣龙鳞"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "sea_god_temple": [
        {
            "id": "sea_god_temple_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "海神神殿入口：珊瑚与贝壳砌成的殿门立在浅海中，门柱上雕刻着持三叉戟的海神像，潮水在门槛外徘徊。",
            "type": "副本",
            "lv": 64,
            "npcs": [],
            "monsters": [
                [
                    "m_sea_priest",
                    "海神祭司",
                    "healer",
                    64,
                    [
                        "ms_shui_dan",
                        "ms_hai_chao_zhu_fu"
                    ],
                    [
                        "海神祭器"
                    ]
                ],
                [
                    "m_tidal_guard",
                    "潮汐守卫",
                    "tank",
                    66,
                    [
                        "ms_ju_lang",
                        "ms_tie_bi"
                    ],
                    [
                        "潮汐碎片"
                    ]
                ],
                [
                    "m_shell_warrior",
                    "甲壳战士",
                    "dps",
                    68,
                    [
                        "ms_qian_ji",
                        "ms_ying_hua"
                    ],
                    [
                        "甲壳残片"
                    ]
                ],
                [
                    "b_lange",
                    "海神祭司·澜歌",
                    "boss",
                    72,
                    [
                        "ms_hai_chao",
                        "ms_zhao_huan_sha_yu",
                        "ms_jing_hua_zhi_chao"
                    ],
                    [
                        "澜歌之泪"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_lange",
                "海神祭司·澜歌",
                "boss",
                72,
                [
                    "ms_hai_chao",
                    "ms_zhao_huan_sha_yu",
                    "ms_jing_hua_zhi_chao"
                ],
                [
                    "澜歌之泪"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "deep_dragon_palace": [
        {
            "id": "deep_dragon_palace_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "深海龙宫入口：水晶拱门在深海中泛着蓝光，门两侧立着龙形的雕像，水压在这里骤然加重。",
            "type": "副本",
            "lv": 70,
            "npcs": [],
            "monsters": [
                [
                    "m_coral_mage",
                    "珊瑚法师",
                    "healer",
                    70,
                    [
                        "ms_shui_dan",
                        "ms_shan_hu_hu_dun"
                    ],
                    [
                        "珊瑚枝"
                    ]
                ],
                [
                    "m_deep_knight",
                    "深海骑士",
                    "tank",
                    72,
                    [
                        "ms_san_cha_ji",
                        "ms_shui_xi"
                    ],
                    [
                        "深海骑士甲"
                    ]
                ],
                [
                    "m_dragon_prawn",
                    "龙虾战士",
                    "dps",
                    74,
                    [
                        "ms_qian_ji",
                        "ms_chong_zhuang"
                    ],
                    [
                        "龙虾壳"
                    ]
                ],
                [
                    "b_aolan",
                    "深海龙王·敖澜",
                    "boss",
                    78,
                    [
                        "ms_shui_xi",
                        "ms_long_wei",
                        "ms_zhao_huan_hai_shou"
                    ],
                    [
                        "敖澜之珠"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_aolan",
                "深海龙王·敖澜",
                "boss",
                78,
                [
                    "ms_shui_xi",
                    "ms_long_wei",
                    "ms_zhao_huan_hai_shou"
                ],
                [
                    "敖澜之珠"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "deep_tunnel": [
        {
            "id": "deep_tunnel_1",
            "name": "隧道口",
            "icon": "🏘️",
            "desc": "深岩隧道的入口开在山壁下，铁轨伸进黑暗。矿工们扛着镐子鱼贯而入，头灯的光消失在隧道深处。",
            "type": "城镇",
            "lv": 65,
            "npcs": [
                "npc_tunnel_miner",
                'npc_tunnel_foreman',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "deep_tunnel_2",
            "name": "中央大厅",
            "icon": "🏘️",
            "desc": "中央大厅被凿成穹顶状，灯挂在铁架上。工头在墙上的图板前分配任务，脚步声在厅里回荡。",
            "type": "城镇",
            "lv": 65,
            "npcs": [
                "npc_tunnel_lamp",
                'npc_tunnel_engineer',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "deep_tunnel_3",
            "name": "营地区",
            "icon": "🏘️",
            "desc": "营地区的帐篷靠着岩壁搭着，炉灶上煮着浓汤。车夫卸下货物，矿工们围坐取暖。",
            "type": "城镇",
            "lv": 65,
            "npcs": [
                "npc_tunnel_carter",
                'npc_tunnel_cook',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "heal"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "deep_tunnel_mouth",
            "name": "深隧口",
            "icon": "🕳️",
            "desc": "深岩隧道尽头的开阔口，铁轨从这里伸进矮人长廊，矿灯的光在岩壁上晃动。",
            "type": "城镇出口",
            "lv": 65,
            "npcs": ["npc_deep_tunnel_gate_guard", 'npc_tunnel_trackman'],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "under_market": [
        {
            "id": "under_market_1",
            "name": "集市广场",
            "icon": "🏘️",
            "desc": "地底集市的广场被菌灯照亮，商贩们支起布棚，叫卖着地表见不到的货物。这里的货币与秘密一样多。",
            "type": "城镇",
            "lv": 70,
            "npcs": [
                "npc_under_trader",
                'npc_under_herbalist', 'npc_under_farmer',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop",
                "stall"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "under_market_2",
            "name": "拍卖区",
            "icon": "🏘️",
            "desc": "拍卖区的台子上摆着地底挖出的奇物，守卫抱着臂站在角落。落槌声在岩壁间回响。",
            "type": "城镇",
            "lv": 70,
            "npcs": [
                "npc_under_guard",
                'npc_under_broker',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "auction"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "under_market_3",
            "name": "旅店",
            "icon": "🏘️",
            "desc": "地底旅店的房间嵌在岩壁里，低语者在前台登记。这里的床铺安静，适合不想被找到的人。",
            "type": "城镇",
            "lv": 70,
            "npcs": [
                "npc_under_whisper",
                'npc_under_helper',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "heal"
            ],
            "shop": False,
            "healer": True
        },
        {
            "id": "under_market_mouth",
            "name": "集市口",
            "icon": "🪜",
            "desc": "地底集市的悬梯口，菌灯在头顶发着幽光，悬梯通往真菌森林与熔火深渊方向。",
            "type": "城镇出口",
            "lv": 70,
            "npcs": ["npc_under_market_gate_guard"],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "fungus_forest": [
        {
            "id": "fungus_forest_1",
            "name": "菌林边缘",
            "icon": "🌲",
            "desc": "真菌森林的边缘，孢子在空中漂浮，像下了一场金色的雪。菌农提着篮子在采蘑菇，孢子史莱姆在脚下蠕动。",
            "type": "野外",
            "lv": 66,
            "npcs": ["npc_fungus_farmer"],
            "monsters": [
                [
                    "m_spore_slime",
                    "孢子史莱姆",
                    "tank",
                    66,
                    [
                        "ms_zhuang_ji",
                        "ms_bao_zi_du"
                    ],
                    [
                        "孢子囊"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "fungus_forest_2",
            "name": "孢子区",
            "icon": "🌲",
            "desc": "孢子区的菌菇比人还高，真菌兽在菌丛间拱食，发出湿漉漉的咀嚼声。",
            "type": "野外",
            "lv": 71,
            "npcs": [],
            "monsters": [
                [
                    "m_fungus_beast",
                    "真菌兽",
                    "dps",
                    68,
                    [
                        "ms_si_yao",
                        "ms_bao_zi_pen_she"
                    ],
                    [
                        "真菌肉"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "fungus_forest_3",
            "name": "菌林深处",
            "icon": "🌲",
            "desc": "菌林深处的荧光蛾成群飞过，把黑暗染成蓝绿色。真菌领主·腐冠的菌冠在雾气中若隐若现。",
            "type": "野外",
            "lv": 76,
            "npcs": [],
            "monsters": [
                [
                    "m_glow_moth",
                    "荧光蛾",
                    "speedster",
                    70,
                    [
                        "ms_lin_fen",
                        "ms_zhi_mang"
                    ],
                    [
                        "荧光粉"
                    ]
                ],
                ],
            "elite": [
                "e_fungus_lord",
                "真菌领主·腐冠",
                "elite",
                74,
                [
                    "ms_bao_zi_bao",
                    "ms_zhao_huan_zhen_jun_shou"
                ],
                [
                    "腐冠菌"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "deep_lake": [
        {
            "id": "deep_lake_1",
            "name": "湖岸",
            "icon": "🌲",
            "desc": "地下湖的湖岸岩石湿滑，湖面漆黑如墨。渔人点着油灯，深渊盲鱼在灯影边缘游过。",
            "type": "野外",
            "lv": 72,
            "npcs": ["npc_deeplake_fisher"],
            "monsters": [
                [
                    "m_abyss_fish",
                    "深渊盲鱼",
                    "speedster",
                    72,
                    [
                        "ms_si_yao"
                    ],
                    [
                        "盲鱼鳞"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "deep_lake_2",
            "name": "湖桥",
            "icon": "🌲",
            "desc": "湖桥是几块石板搭成的，地底巨龟在桥下的浅水里缓缓爬行，甲壳上长满苔藓。",
            "type": "野外",
            "lv": 77,
            "npcs": [],
            "monsters": [
                [
                    "m_under_turtle",
                    "地底巨龟",
                    "tank",
                    75,
                    [
                        "ms_jia_ji",
                        "ms_shui_xi"
                    ],
                    [
                        "巨龟甲"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "deep_lake_3",
            "name": "湖底",
            "icon": "🌲",
            "desc": "湖底的黑水没有一丝光，湖底怨灵的哀叹从深处传来。黑暗水蛭王盘踞在最深的泥穴里。",
            "type": "野外",
            "lv": 82,
            "npcs": [],
            "monsters": [
                [
                    "m_lake_haunt",
                    "湖底怨灵",
                    "healer",
                    78,
                    [
                        "ms_ai_hao",
                        "ms_an_ying_dan"
                    ],
                    [
                        "怨灵之尘"
                    ]
                ],
                ],
            "elite": [
                "e_dark_leech",
                "黑暗水蛭王",
                "elite",
                80,
                [
                    "ms_xi_xue",
                    "ms_chan_rao"
                ],
                [
                    "水蛭王牙"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "molten_abyss": [
        {
            "id": "molten_abyss_1",
            "name": "深渊口",
            "icon": "🌲",
            "desc": "熔火深渊的入口热浪翻涌，侦察兵在岩台边向下张望。熔岩蠕虫在岩缝里蠕动，留下焦黑的痕迹。",
            "type": "野外",
            "lv": 78,
            "npcs": ["npc_molten_scout"],
            "monsters": [
                [
                    "m_magma_worm",
                    "熔岩蠕虫",
                    "dps",
                    78,
                    [
                        "ms_huo_dan",
                        "ms_zuan_di"
                    ],
                    [
                        "熔岩蠕虫皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "molten_abyss_2",
            "name": "熔岩道",
            "icon": "🌲",
            "desc": "熔岩道两侧是流动的岩浆，地底小恶魔在石桥间跳跃，发出尖啸。",
            "type": "野外",
            "lv": 83,
            "npcs": [],
            "monsters": [
                [
                    "m_under_imp",
                    "地底小恶魔",
                    "speedster",
                    80,
                    [
                        "ms_huo_dan",
                        "ms_zhao_ji"
                    ],
                    [
                        "地底恶魔角"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "molten_abyss_3",
            "name": "深渊深处",
            "icon": "🌲",
            "desc": "深渊最深处岩浆成瀑，黑曜石魔像立在熔岩河边。熔火领主·烬核的王座就在那瀑布之后。",
            "type": "野外",
            "lv": 88,
            "npcs": [],
            "monsters": [
                [
                    "m_obsidian_golem",
                    "黑曜石魔像",
                    "tank",
                    82,
                    [
                        "ms_zhong_ji",
                        "ms_ying_hua"
                    ],
                    [
                        "黑曜碎片"
                    ]
                ],
                ],
            "elite": [
                "e_molten_lord",
                "熔火领主·烬核",
                "elite",
                86,
                [
                    "ms_rong_yan_dan",
                    "ms_zhuo_shao"
                ],
                [
                    "烬核"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "gray_dwarf": [
        {
            "id": "gray_dwarf_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "灰矮人要塞入口：厚重的石门嵌在岩壁中，门楣刻着矮人符文。门缝里透出熔炉的红光与沉闷的锻声。",
            "type": "副本",
            "lv": 74,
            "npcs": [],
            "monsters": [
                [
                    "m_gray_dwarf",
                    "灰矮人战士",
                    "dps",
                    74,
                    [
                        "ms_zhan_chui",
                        "ms_dun_ji"
                    ],
                    [
                        "灰矮人徽记"
                    ]
                ],
                [
                    "m_gray_engineer",
                    "灰矮人技师",
                    "healer",
                    76,
                    [
                        "ms_xiu_li",
                        "ms_bao_dan"
                    ],
                    [
                        "机械零件"
                    ]
                ],
                [
                    "b_gray_lord",
                    "灰矮人领主·石炉",
                    "boss",
                    84,
                    [
                        "ms_zhan_chui",
                        "ms_zhao_huan_gong_cheng_shou"
                    ],
                    [
                        "石炉之锤"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_gray_lord",
                "灰矮人领主·石炉",
                "boss",
                84,
                [
                    "ms_zhan_chui",
                    "ms_zhao_huan_gong_cheng_shou"
                ],
                [
                    "石炉之锤"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "under_dragon": [
        {
            "id": "under_dragon_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "地底龙巢入口：巨大的龙爪痕迹刻在岩壁上，洞口堆着磨得发亮的兽骨。巢内传来沉重的呼吸声。",
            "type": "副本",
            "lv": 84,
            "npcs": [],
            "monsters": [
                [
                    "m_under_drake",
                    "地底幼龙",
                    "dps",
                    84,
                    [
                        "ms_suan_xi",
                        "ms_long_zhao"
                    ],
                    [
                        "地底龙鳞"
                    ]
                ],
                [
                    "m_under_wyrm",
                    "地底古龙裔",
                    "tank",
                    88,
                    [
                        "ms_suan_xi",
                        "ms_long_wei_190"
                    ],
                    [
                        "古龙裔甲"
                    ]
                ],
                [
                    "b_under_dragon",
                    "地底古龙·黑渊",
                    "boss",
                    92,
                    [
                        "ms_suan_xi",
                        "ms_tun_shi",
                        "ms_zhao_huan_you_long"
                    ],
                    [
                        "黑渊之眼"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_under_dragon",
                "地底古龙·黑渊",
                "boss",
                92,
                [
                    "ms_suan_xi",
                    "ms_tun_shi",
                    "ms_zhao_huan_you_long"
                ],
                [
                    "黑渊之眼"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "ember_camp": [
        {
            "id": "ember_camp_1",
            "name": "营地口",
            "icon": "🏘️",
            "desc": "灰烬营地的入口立着黑铁哨栏，向导与商贩在门口搭话。岩浆渠在营地边缓缓流过，把黑夜映成橘红色。",
            "type": "城镇",
            "lv": 85,
            "npcs": [
                "npc_under_guide",
                "npc_ember_merchant",
                'npc_ember_weaponsmith',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "ember_camp_2",
            "name": "营长帐",
            "icon": "🏘️",
            "desc": "营长帐里挂着地底的地图，营长在灯下圈着新的路线。这里的每一份委托都通往黑暗深处。",
            "type": "城镇",
            "lv": 85,
            "npcs": [
                "npc_ember_camp_leader",
                'npc_ember_adjutant',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "ember_camp_3",
            "name": "地底向导所",
            "icon": "🏘️",
            "desc": "向导所的木牌上刻着各条地底路线的记号，老向导坐在火盆边，给新手讲深层的禁忌。炊事员端来热汤。",
            "type": "城镇",
            "lv": 85,
            "npcs": [
                "npc_ember_cook",
                'npc_ember_mapper',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest",
                "lore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "ember_camp_4",
            "name": "补给站",
            "icon": "🏘️",
            "desc": "补给站的货架摆满干粮、绳索与火把，侦察兵清点着装备。这里的光亮与物资，是地底旅途的底气。",
            "type": "城镇",
            "lv": 85,
            "npcs": [
                "npc_ember_scout",
                'npc_ember_storeman',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "shop"
            ],
            "shop": True,
            "healer": False
        },
        {
            "id": "ember_camp_sentry",
            "name": "灰烬哨口",
            "icon": "🔥",
            "desc": "灰烬营地边缘的黑铁栏哨位，岩浆渠在旁边流过，哨口外是熔岩道与熔岩滩方向。",
            "type": "城镇出口",
            "lv": 85,
            "npcs": ["npc_ember_camp_gate_guard"],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "lava_bed": [
        {
            "id": "lava_bed_1",
            "name": "河床口",
            "icon": "🌲",
            "desc": "熔岩河床的入口岩石滚烫，岩浆蠕虫在裂缝里蠕动。矿工用铁锹试探着地面，寻找可以落脚的地方。",
            "type": "野外",
            "lv": 86,
            "npcs": ["npc_lavabed_miner"],
            "monsters": [
                [
                    "m_magma_worm",
                    "岩浆蠕虫",
                    "dps",
                    86,
                    [
                        "ms_huo_dan",
                        "ms_zuan_di"
                    ],
                    [
                        "岩浆蠕虫皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "lava_bed_2",
            "name": "熔岩滩",
            "icon": "🌲",
            "desc": "熔岩滩上岩浆如河，熔岩甲虫在滩边爬行，甲壳泛着暗红的光。",
            "type": "野外",
            "lv": 90,
            "npcs": [],
            "monsters": [
                [
                    "m_lava_beetle",
                    "熔岩甲虫",
                    "tank",
                    88,
                    [
                        "ms_chong_zhuang",
                        "ms_zhuo_shao"
                    ],
                    [
                        "熔岩甲壳"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "lava_bed_3",
            "name": "河床深处",
            "icon": "🌲",
            "desc": "河床深处的岩浆汇成瀑布，火蝠在热浪中盘旋。岩浆王·烬核沉睡在瀑布下的岩洞里。",
            "type": "野外",
            "lv": 94,
            "npcs": [],
            "monsters": [
                [
                    "m_fire_bat",
                    "火蝠",
                    "speedster",
                    90,
                    [
                        "ms_fu_chong",
                        "ms_huo_dan"
                    ],
                    [
                        "火蝠翼"
                    ]
                ],
                ],
            "elite": [
                "e_magma_king",
                "岩浆王·烬核",
                "elite",
                94,
                [
                    "ms_rong_yan_dan",
                    "ms_zhuo_shao",
                    "ms_zhao_huan_ru_chong"
                ],
                [
                    "烬核之心"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "abyss_altar": [
        {
            "id": "abyss_altar_1",
            "name": "祭坛外围",
            "icon": "🌲",
            "desc": "深渊祭坛的外围立着扭曲的石柱，深渊信徒在柱间低语，黑袍下露出苍白的脸。",
            "type": "野外",
            "lv": 88,
            "npcs": ["npc_abyssaltar_whisperer"],
            "monsters": [
                [
                    "m_abyss_cultist",
                    "深渊信徒",
                    "healer",
                    88,
                    [
                        "ms_an_ying_dan",
                        "ms_hei_an_qi_dao"
                    ],
                    [
                        "染血圣典"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "abyss_altar_2",
            "name": "祭坛廊道",
            "icon": "🌲",
            "desc": "廊道的石壁上刻着看不懂的符文，虚空猎犬在阴影里走动，喉咙里发出低沉的咕噜声。",
            "type": "野外",
            "lv": 92,
            "npcs": [],
            "monsters": [
                [
                    "m_void_hound",
                    "虚空猎犬",
                    "speedster",
                    90,
                    [
                        "ms_si_yao",
                        "ms_an_ying_zhao"
                    ],
                    [
                        "虚空犬牙"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "abyss_altar_3",
            "name": "祭坛核心",
            "icon": "🌲",
            "desc": "祭坛核心的黑暗浓得像实质，深渊恶魔在祭坛上等待。祭坛守卫·魔眼悬在半空，瞳孔中映着每一个来者。",
            "type": "野外",
            "lv": 96,
            "npcs": [],
            "monsters": [
                [
                    "m_abyss_demon",
                    "深渊恶魔",
                    "dps",
                    92,
                    [
                        "ms_zhao_ji",
                        "ms_di_yu_huo"
                    ],
                    [
                        "深渊恶魔角"
                    ]
                ],
                ],
            "elite": [
                "e_altar_guardian",
                "祭坛守卫·魔眼",
                "elite",
                96,
                [
                    "ms_an_ying_dan",
                    "ms_zhao_huan_lie_quan",
                    "ms_fu_shi"
                ],
                [
                    "魔眼之核"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "abyss_throne": [
        {
            "id": "abyss_throne_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "深渊王座入口：黑曜石巨门矗立在黑暗尽头，门上的纹路如同蠕动的触须。门后是深渊的最深处。",
            "type": "副本",
            "lv": 90,
            "npcs": [],
            "monsters": [
                [
                    "m_abyss_guard",
                    "深渊守卫",
                    "tank",
                    90,
                    [
                        "ms_zhong_ji",
                        "ms_an_ying_zhan"
                    ],
                    [
                        "深渊守卫甲"
                    ]
                ],
                [
                    "m_abyss_warlock",
                    "深渊术士",
                    "healer",
                    92,
                    [
                        "ms_an_ying_dan",
                        "ms_zhao_huan_e_mo"
                    ],
                    [
                        "术士法杖"
                    ]
                ],
                [
                    "b_moro",
                    "深渊领主·摩罗",
                    "boss",
                    98,
                    [
                        "ms_shen_yuan_zhi_nu",
                        "ms_zhao_huan_e_mo",
                        "ms_fu_shi_ling_yu"
                    ],
                    [
                        "摩罗之冠"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_moro",
                "深渊领主·摩罗",
                "boss",
                98,
                [
                    "ms_shen_yuan_zhi_nu",
                    "ms_zhao_huan_e_mo",
                    "ms_fu_shi_ling_yu"
                ],
                [
                    "摩罗之冠"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "wind_city": [
        {
            "id": "wind_city_1",
            "name": "浮空广场",
            "icon": "🏘️",
            "desc": "风翼城的浮空广场悬在云海之上，风筝匠人放飞着巨大的纸鸢。风托着城体轻轻晃动，脚下就是万丈云海。",
            "type": "城镇",
            "lv": 85,
            "npcs": [
                "npc_wind_kitemaker",
                'npc_wind_cloudmerchant',
            ],            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "wind_city_2",
            "name": "云翼议会厅",
            "icon": "🏘️",
            "desc": "议会厅的圆窗开向云海，风长老们在厅中议事，长袍被气流轻轻拂动。",
            "type": "城镇",
            "lv": 85,
            "npcs": [
                "npc_wind_elder",
                'npc_wind_scribe',
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [
                "quest"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "wind_city_gate",
            "name": "云门",
            "icon": "🏰",
            "desc": "风之城的云门浮在断崖边，门框由云母石砌成，脚下便是万丈云海。",
            "type": "城镇出口",
            "lv": 1,
            "npcs": ["npc_wind_city_gate_guard", 'npc_wind_guard2'],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
            "shop": False,
            "healer": False
        },
    ],
    "cloud_sea": [
        {
            "id": "cloud_sea_1",
            "name": "云海边",
            "icon": "🌲",
            "desc": "云海的边缘像海岸，云浪缓缓翻涌。船夫撑着云舟，云兽在云浪里沉浮，像海中的鱼。",
            "type": "野外",
            "lv": 86,
            "npcs": ["npc_cloudsea_boatman"],
            "monsters": [
                [
                    "m_cloud_beast",
                    "云兽",
                    "tank",
                    86,
                    [
                        "ms_yun_dan",
                        "ms_piao_fu"
                    ],
                    [
                        "云絮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "cloud_sea_2",
            "name": "云岛",
            "icon": "🌲",
            "desc": "云岛漂在云海里，风精灵在岛上的风铃间穿行，铃声清脆。",
            "type": "野外",
            "lv": 90,
            "npcs": [],
            "monsters": [
                [
                    "m_wind_spirit",
                    "风精灵",
                    "speedster",
                    88,
                    [
                        "ms_feng_ren",
                        "ms_ji_chi"
                    ],
                    [
                        "风之羽"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "cloud_sea_3",
            "name": "云海深处",
            "icon": "🌲",
            "desc": "云海深处的云层浓密如棉，天鹰在云上盘旋。云海领主·雾冠的宫殿藏在一片永不散去的云团里。",
            "type": "野外",
            "lv": 94,
            "npcs": [],
            "monsters": [
                [
                    "m_sky_hawk",
                    "天鹰",
                    "dps",
                    90,
                    [
                        "ms_fu_chong",
                        "ms_zhao_ji"
                    ],
                    [
                        "天鹰羽"
                    ]
                ],
                ],
            "elite": [
                "e_cloud_lord",
                "云海领主·雾冠",
                "elite",
                92,
                [
                    "ms_yun_dan",
                    "ms_feng_bao"
                ],
                [
                    "雾冠晶"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "storm_plateau": [
        {
            "id": "storm_plateau_1",
            "name": "高原边缘",
            "icon": "🌲",
            "desc": "雷暴高原的边缘雷云低垂，雷元素在旷野上游荡，偶尔炸出一串电花。观雷人支着铜杆，记录着落雷的位置。",
            "type": "野外",
            "lv": 90,
            "npcs": ["npc_stormplateau_lightning"],
            "monsters": [
                [
                    "m_thunder_element",
                    "雷元素",
                    "dps",
                    90,
                    [
                        "ms_lei_ji",
                        "ms_shan_dian_lian"
                    ],
                    [
                        "雷晶"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "storm_plateau_2",
            "name": "雷区",
            "icon": "🌲",
            "desc": "雷区的空气带着焦味，风暴兽在电光间奔跑，皮毛上跳着电弧。",
            "type": "野外",
            "lv": 94,
            "npcs": [],
            "monsters": [
                [
                    "m_storm_beast",
                    "风暴兽",
                    "tank",
                    92,
                    [
                        "ms_lei_ji",
                        "ms_jian_ta"
                    ],
                    [
                        "风暴兽皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "storm_plateau_3",
            "name": "高原核心",
            "icon": "🌲",
            "desc": "高原核心的雷云压到地面，雷鸟在云中穿梭。雷暴领主·雷霆站在最高的石台上，闪电环绕其身。",
            "type": "野外",
            "lv": 98,
            "npcs": [],
            "monsters": [
                [
                    "m_lightning_bird",
                    "雷鸟",
                    "speedster",
                    94,
                    [
                        "ms_fu_chong",
                        "ms_lei_yu"
                    ],
                    [
                        "雷鸟羽"
                    ]
                ],
                ],
            "elite": [
                "e_storm_lord",
                "雷暴领主·雷霆",
                "elite",
                96,
                [
                    "ms_lei_ji",
                    "ms_feng_bao_zhi_nu"
                ],
                [
                    "雷霆之心"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "eye_of_storm": [
        {
            "id": "eye_of_storm_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "风暴之眼入口：风眼正对着一道石门，气流在门前旋转成漩涡。门内平静得反常，仿佛风暴都被驯服了。",
            "type": "副本",
            "lv": 92,
            "npcs": [],
            "monsters": [
                [
                    "m_eye_guardian",
                    "风暴守卫",
                    "tank",
                    92,
                    [
                        "ms_lei_ji",
                        "ms_tie_bi"
                    ],
                    [
                        "守卫铠甲碎片"
                    ]
                ],
                [
                    "m_sky_warrior",
                    "天空战士",
                    "dps",
                    94,
                    [
                        "ms_feng_ren",
                        "ms_lei_jian"
                    ],
                    [
                        "天空战刃"
                    ]
                ],
                [
                    "b_storm_master",
                    "风暴之主·云怒",
                    "boss",
                    100,
                    [
                        "ms_lei_bao",
                        "ms_feng_bao_zhi_yan",
                        "ms_zhao_huan_lei_niao"
                    ],
                    [
                        "云怒之核"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_storm_master",
                "风暴之主·云怒",
                "boss",
                100,
                [
                    "ms_lei_bao",
                    "ms_feng_bao_zhi_yan",
                    "ms_zhao_huan_lei_niao"
                ],
                [
                    "云怒之核"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "rainbow_cloud": [
        {
            "id": "rainbow_cloud_1",
            "name": "云谷口",
            "icon": "🌲",
            "desc": "彩虹云谷的入口横着一条彩虹桥，彩虹小仙灵在桥边嬉戏。牧云人赶着云朵，像赶着一群绵羊。",
            "type": "野外",
            "lv": 90,
            "npcs": ["npc_rainbow_herder"],
            "monsters": [
                [
                    "m_rainbow_faerie",
                    "彩虹小仙灵",
                    "healer",
                    90,
                    [
                        "ms_cai_guang",
                        "ms_zhu_fu"
                    ],
                    [
                        "彩虹露"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "rainbow_cloud_2",
            "name": "彩虹桥",
            "icon": "🌲",
            "desc": "彩虹桥横跨云谷，云熊在桥下打滚，把云压出一个坑。",
            "type": "野外",
            "lv": 93,
            "npcs": [],
            "monsters": [
                [
                    "m_cloud_bear",
                    "云熊",
                    "tank",
                    92,
                    [
                        "ms_pai_ji",
                        "ms_yun_dan"
                    ],
                    [
                        "云熊毛"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "rainbow_cloud_3",
            "name": "云谷深处",
            "icon": "🌲",
            "desc": "云谷深处的云彩五彩斑斓，彩虹蛇盘在云柱上。彩虹龙·霞光的鳞片折射着七色光。",
            "type": "野外",
            "lv": 96,
            "npcs": [],
            "monsters": [
                [
                    "m_rainbow_serpent",
                    "彩虹蛇",
                    "speedster",
                    94,
                    [
                        "ms_chan_rao",
                        "ms_cai_guang"
                    ],
                    [
                        "彩虹鳞"
                    ]
                ],
                ],
            "elite": [
                "e_rainbow_dragon",
                "彩虹龙·霞光",
                "elite",
                96,
                [
                    "ms_cai_xi",
                    "ms_cai_hong_zhan",
                    "ms_zhao_huan_xian_ling"
                ],
                [
                    "霞光龙鳞"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "starlight_terrace": [
        {
            "id": "starlight_terrace_1",
            "name": "台缘",
            "icon": "🌲",
            "desc": "星辉台的边缘星光如尘，观星人架着望远镜。星光精灵在台缘飞舞，像被吹散的星屑。",
            "type": "野外",
            "lv": 92,
            "npcs": ["npc_starlight_stargazer"],
            "monsters": [
                [
                    "m_star_spirit",
                    "星光精灵",
                    "speedster",
                    92,
                    [
                        "ms_xing_hui_dan",
                        "ms_shan_shuo"
                    ],
                    [
                        "星辉尘"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "starlight_terrace_2",
            "name": "星辉路",
            "icon": "🌲",
            "desc": "星辉路铺着星砂，星狼在路旁的石柱间走动，皮毛上落着星光。",
            "type": "野外",
            "lv": 95,
            "npcs": [],
            "monsters": [
                [
                    "m_astral_wolf",
                    "星狼",
                    "dps",
                    94,
                    [
                        "ms_si_yao",
                        "ms_xing_hui_zhan"
                    ],
                    [
                        "星狼皮"
                    ]
                ]
            ],
            "elite": None,
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        },
        {
            "id": "starlight_terrace_3",
            "name": "星辉之巅",
            "icon": "🌲",
            "desc": "星辉之巅的夜空低得仿佛触手可及，陨星魔像立在星石之间。星龙·辰光盘踞在山巅，龙鳞如银河。",
            "type": "野外",
            "lv": 98,
            "npcs": [],
            "monsters": [
                [
                    "m_meteor_golem",
                    "陨星魔像",
                    "tank",
                    96,
                    [
                        "ms_zhong_ji",
                        "ms_yun_shi"
                    ],
                    [
                        "陨星核"
                    ]
                ],
                ],
            "elite": [
                "e_star_dragon",
                "星龙·辰光",
                "elite",
                98,
                [
                    "ms_xing_xi",
                    "ms_long_zhao",
                    "ms_zhao_huan_xing_ling"
                ],
                [
                    "辰光龙鳞"
                ]
            ],
            "boss": None,
            "funcs": [
                "explore"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "cloud_sanctum": [
        {
            "id": "cloud_sanctum_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "云中圣殿入口：云梯的尽头是一扇月光石大门，门框镶着风纹。殿门半开，圣光从门缝中倾泻而出。",
            "type": "副本",
            "lv": 94,
            "npcs": [],
            "monsters": [
                [
                    "m_cloud_guard",
                    "云殿守卫",
                    "tank",
                    94,
                    [
                        "ms_yun_dun",
                        "ms_feng_ren"
                    ],
                    [
                        "云殿铠甲"
                    ]
                ],
                [
                    "m_light_priest",
                    "光之祭司",
                    "healer",
                    96,
                    [
                        "ms_sheng_guang_dan",
                        "ms_zhu_fu"
                    ],
                    [
                        "光之圣典"
                    ]
                ],
                [
                    "b_ola",
                    "云中圣者·奥拉",
                    "boss",
                    100,
                    [
                        "ms_sheng_guang",
                        "ms_feng_bao",
                        "ms_zhao_huan_yun_wei"
                    ],
                    [
                        "奥拉圣印"
                    ]
                ]
            ],
            "elite": None,
            "boss": [
                "b_ola",
                "云中圣者·奥拉",
                "boss",
                100,
                [
                    "ms_sheng_guang",
                    "ms_feng_bao",
                    "ms_zhao_huan_yun_wei"
                ],
                [
                    "奥拉圣印"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "lost_library": [
        {
            "id": "lost_library_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "失落图书馆入口：石阶通向地下的穹顶大厅，门前的雕像捧着翻开的书卷。馆内飘着纸墨与灰尘的古老气息。",
            "type": "隐藏区域",
            "lv": 55,
            "npcs": [
                "npc_spellblade_ghost"
            ],
            "monsters": [
                [
                    "m_lib_guard",
                    "图书馆守卫",
                    "tank",
                    55,
                    [
                        "ms_tie_bi",
                        "ms_fu_shi_shu"
                    ],
                    [
                        "旧书残页",
                        "剑圣残页"
                    ]
                ],
                [
                    "m_book_spirit",
                    "书页精灵",
                    "speedster",
                    56,
                    [
                        "ms_jing_ling_jian_shu",
                        "ms_shan_shuo"
                    ],
                    [
                        "墨水瓶"
                    ]
                ],
                [
                    "m_paper_wraith",
                    "纸墨幽魂",
                    "dps",
                    58,
                    [
                        "ms_an_ying_zhan",
                        "ms_fu_shi"
                    ],
                    [
                        "褪色墨水"
                    ]
                ],
                ],
            "elite": [
                "e_archive_warden",
                "档案馆长·奥古斯特",
                "elite",
                60,
                [
                    "ms_fu_wen_chong_ji",
                    "ms_jian_xiao",
                    "ms_zhao_huan_ku_lou"
                ],
                [
                    "档案室钥匙"
                ]
            ],
            "boss": [
                "b_lost_archivist",
                "守馆者·遗忘贤者",
                "boss",
                62,
                [
                    "ms_fu_shi_ling_yu",
                    "ms_an_ying_dan",
                    "ms_zhao_huan_yun_wei"
                ],
                [
                    "星尘沙漏"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "ember_corridor": [
        {
            "id": "ember_corridor_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "灰烬回廊入口：焦黑的石廊在灰烬平原尽头敞开，廊壁上的浮雕描绘着烈焰与陨落。回廊深处红光隐现。",
            "type": "隐藏区域",
            "lv": 85,
            "npcs": [],
            "monsters": [
                [
                    "m_ember_guard",
                    "烬火守卫",
                    "tank",
                    85,
                    [
                        "ms_lie_yan_zhao",
                        "ms_tie_bi"
                    ],
                    [
                        "余烬甲片"
                    ]
                ],
                [
                    "m_cinder_wolf",
                    "烬狼",
                    "speedster",
                    86,
                    [
                        "ms_si_yao",
                        "ms_huo_yan"
                    ],
                    [
                        "烬狼牙"
                    ]
                ],
                [
                    "m_ash_knight",
                    "灰烬骑士",
                    "dps",
                    87,
                    [
                        "ms_duan_jian",
                        "ms_huo_qiang"
                    ],
                    [
                        "烧焦剑刃"
                    ]
                ],
                ],
            "elite": [
                "e_ash_champion",
                "灰烬勇士",
                "elite",
                88,
                [
                    "ms_huo_pao",
                    "ms_lian_zhan",
                    "ms_bao_zi_bao"
                ],
                [
                    "勇士余烬"
                ]
            ],
            "boss": [
                "b_ember_lord",
                "烬火领主·伊格尼斯",
                "boss",
                90,
                [
                    "ms_rong_yan_dan",
                    "ms_di_yu_huo",
                    "ms_zhao_huan"
                ],
                [
                    "灰烬之核"
                ]
            ],
            "funcs": [
                "instance"
            ],
            "shop": False,
            "healer": False
        }
    ],
    "silver_wind_road": [
      {
        "id": "silver_wind_road_1",
        "name": "银风道口",
        "icon": "🌲",
        "desc": "银风商道的入口立着指路碑，货郎挑着担子吆喝。野狗在路边草丛里盯着来往的商队。",
        "type": "野外",
        "lv": 6,
        "npcs": [
            "npc_road_peddler",
        ],        "monsters": [
          [
            "m_wild_dog",
            "野狗",
            "dps",
            3,
            [
              "ms_si_yao"
            ],
            [
              "狗牙"
            ]
          ],
          [
            "m_cave_lizard",
            "石蜥蜴",
            "tank",
            6,
            [
              "ms_yao_sui",
              "ms_ying_hua"
            ],
            [
              "石蜥鳞"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "silver_wind_road_2",
        "name": "银风驿站",
        "icon": "🌲",
        "desc": "驿站的马棚里拴着骡马，商队长在桌前核对货物清单。森林狼的嗥叫在夜幕降临时响起。",
        "type": "野外",
        "lv": 8,
        "npcs": ["npc_caravan_leader"],
        "monsters": [
          [
            "m_forest_wolf",
            "森林狼",
            "dps",
            8,
            [
              "ms_si_yao",
              "ms_hao_jiao"
            ],
            [
              "狼皮"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      }
    ],
    "west_ridge_wilds": [
      {
        "id": "west_ridge_wilds_1",
        "name": "西岭口",
        "icon": "🌲",
        "desc": "西岭荒原的入口风大土干，草药师在乱石间弯腰采药。丘陵狼的脚印印在干裂的土上。",
        "type": "野外",
        "lv": 28,
        "npcs": [
            "npc_wild_herbalist",
        ],        "monsters": [
          [
            "m_hill_wolf",
            "丘陵狼",
            "dps",
            28,
            [
              "ms_si_yao",
              "ms_hao_jiao"
            ],
            [
              "丘陵狼皮"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "west_ridge_wilds_2",
        "name": "荒原腹地",
        "icon": "🌲",
        "desc": "荒原腹地杂草丛生，野牛群在远处移动，盗贼的影子在残墙后晃动。巡逻兵拍着马，向这边赶来。",
        "type": "野外",
        "lv": 31,
        "npcs": ["npc_border_patrol"],
        "monsters": [
          [
            "m_wild_bull",
            "野牛",
            "tank",
            30,
            [
              "ms_chong_zhuang"
            ],
            [
              "牛角"
            ]
          ],
          [
            "m_bandit",
            "盗贼",
            "speedster",
            32,
            [
              "ms_duan_jian",
              "ms_tou_qie"
            ],
            [
              "盗贼面巾"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "west_ridge_wilds_3",
        "name": "落霞坡",
        "icon": "🌲",
        "desc": "落霞坡在黄昏时最美，斜阳把荒原染成金红色。古道骷髅从土里爬出，在晚风中活动着关节。",
        "type": "野外",
        "lv": 34,
        "npcs": [],
        "monsters": [
          [
            "m_road_skeleton",
            "古道骷髅",
            "dps",
            33,
            [
              "ms_jian_ji"
            ],
            [
              "碎骨"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      }
    ],
    "dusk_ridge_road": [
      {
        "id": "dusk_ridge_road_1",
        "name": "岭脚石阶",
        "icon": "🌲",
        "desc": "暮岭古道的岭脚石阶长满青苔，商队赶着车缓缓上行。战场幽魂在石阶两旁的树影间游荡。",
        "type": "野外",
        "lv": 36,
        "npcs": ["npc_dusk_caravan"],
        "monsters": [
          [
            "m_field_ghost",
            "战场幽魂",
            "speedster",
            34,
            [
              "ms_chuan_shen",
              "ms_ai_hao"
            ],
            [
              "幽魂尘"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "dusk_ridge_road_2",
        "name": "半山烽台",
        "icon": "🌲",
        "desc": "半山的烽火台早已废弃，古墓幽灵在台顶徘徊，像守望了千年的哨兵。",
        "type": "野外",
        "lv": 39,
        "npcs": [],
        "monsters": [
          [
            "m_grave_ghost",
            "古墓幽灵",
            "speedster",
            36,
            [
              "ms_chuan_shen",
              "ms_ai_hao"
            ],
            [
              "幽灵之尘"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "dusk_ridge_road_3",
        "name": "月冠垭口",
        "icon": "🌲",
        "desc": "月冠垭口风大，能望见月冠隘口的灯火。战争魔像的残骸横在路中，骑士教官在残骸旁点查着兵器。",
        "type": "野外",
        "lv": 42,
        "npcs": [],
        "monsters": [
          [
            "m_war_golem",
            "战争魔像(残)",
            "tank",
            37,
            [
              "ms_zhong_ji",
              "ms_tie_bi"
            ],
            [
              "魔像残核"
            ]
          ],
          [
            "e_knight_instructor",
            "骑士教官",
            "elite",
            34,
            [
              "ms_jian_ji",
              "ms_zhan_hou"
            ],
            [
              "教官之剑"
            ]
          ]
        ],
        "elite": [
          "e_knight_instructor",
          "骑士教官",
          "elite",
          34,
          [
            "ms_jian_ji",
            "ms_zhan_hou"
          ],
          [
            "教官之剑"
          ]
        ],
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      }
    ],
    "mist_tide_passage": [
      {
        "id": "mist_tide_passage_1",
        "name": "港外锚地",
        "icon": "🌲",
        "desc": "雾潮航道的锚地雾气弥漫，老水手蹲在船头抽烟斗，渔夫在船舷挂起风灯。海妖斥候的歌声在雾中若隐若现。",
        "type": "野外",
        "lv": 45,
        "npcs": [
            "npc_old_sailor",
            "npc_mist_fisher",
        ],
        "monsters": [
          [
            "m_siren_scout",
            "海妖斥候",
            "speedster",
            45,
            [
              "ms_mei_huo_zhi_ge"
            ],
            [
              "海妖鳞"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "mist_tide_passage_2",
        "name": "雾潮中段",
        "icon": "🌲",
        "desc": "雾潮中段的雾浓得像墙，审判猎犬在雾里低吠，声音忽远忽近。",
        "type": "野外",
        "lv": 47,
        "npcs": [],
        "monsters": [
          [
            "m_inquisitor_hound",
            "审判猎犬",
            "speedster",
            45,
            [
              "ms_si_yao"
            ],
            [
              "猎犬项圈"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "mist_tide_passage_3",
        "name": "无名灯塔",
        "icon": "🌲",
        "desc": "无名灯塔的灯还在转，却没有人看守。翠鹿在灯塔下的荒滩吃草，落日岛虎·金焰的脚印印在沙上。",
        "type": "野外",
        "lv": 50,
        "npcs": [],
        "monsters": [
          [
            "m_emerald_deer",
            "翠鹿",
            "speedster",
            47,
            [
              "ms_ji_chi",
              "ms_ding_zhuang"
            ],
            [
              "翠鹿角"
            ]
          ],
          [
            "e_island_tiger",
            "落日岛虎·金焰",
            "elite",
            48,
            [
              "ms_si_yao",
              "ms_pu_ji",
              "ms_lie_yan_zhao"
            ],
            [
              "金焰虎皮"
            ]
          ]
        ],
        "elite": [
          "e_island_tiger",
          "落日岛虎·金焰",
          "elite",
          48,
          [
            "ms_si_yao",
            "ms_pu_ji",
            "ms_lie_yan_zhao"
          ],
          [
            "金焰虎皮"
          ]
        ],
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      }
    ],
    "black_tide_strait": [
      {
        "id": "black_tide_strait_1",
        "name": "无名礁口",
        "icon": "🌲",
        "desc": "黑潮海峡的无名礁口暗礁林立，摆渡人撑着长竿在礁缝间穿行。堕落精灵立在礁石上，望着来船。",
        "type": "野外",
        "lv": 58,
        "npcs": [
            "npc_strait_ferryman",
        ],        "monsters": [
          [
            "m_corrupted_elf",
            "堕落精灵",
            "dps",
            58,
            [
              "ms_jing_ling_jian_shu",
              "ms_an_ying_zhan"
            ],
            [
              "堕落精灵护符"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "black_tide_strait_2",
        "name": "黑潮中流",
        "icon": "🌲",
        "desc": "黑潮中流的水色如墨，月光精灵在水面飘忽，像月亮的碎片。",
        "type": "野外",
        "lv": 60,
        "npcs": [],
        "monsters": [
          [
            "m_moon_spirit",
            "月光精灵",
            "healer",
            58,
            [
              "ms_yue_guang_zhan",
              "ms_zhi_yu"
            ],
            [
              "月光精华"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "black_tide_strait_3",
        "name": "珍珠湾",
        "icon": "🌲",
        "desc": "珍珠湾的水面浮着珍珠母的微光，迷雾章鱼的触手在湾底舒展。星语湖王的水影在水湾深处一闪。",
        "type": "野外",
        "lv": 63,
        "npcs": [],
        "monsters": [
          [
            "m_mist_octopus",
            "迷雾章鱼",
            "tank",
            60,
            [
              "ms_chan_rao",
              "ms_mo_zhi"
            ],
            [
              "章鱼墨囊"
            ]
          ],
          [
            "e_lake_king",
            "星语湖王",
            "elite",
            58,
            [
              "ms_shui_dan",
              "ms_xuan_wo",
              "ms_zhao_huan_shui_jing_ling"
            ],
            [
              "湖王珠"
            ]
          ]
        ],
        "elite": [
          "e_lake_king",
          "星语湖王",
          "elite",
          58,
          [
            "ms_shui_dan",
            "ms_xuan_wo",
            "ms_zhao_huan_shui_jing_ling"
          ],
          [
            "湖王珠"
          ]
        ],
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      }
    ],
    "dwarf_long_gallery": [
      {
        "id": "dwarf_long_gallery_1",
        "name": "要塞铁门",
        "icon": "🌲",
        "desc": "矮人长廊的要塞铁门由整块钢板铸成，门闩粗如房梁。骡队驮着货物在门前排队，远古魔像在门后发出沉重的脚步声。",
        "type": "野外",
        "lv": 62,
        "npcs": [
            "npc_gallery_mule",
        ],        "monsters": [
          [
            "m_ancient_golem",
            "远古魔像",
            "tank",
            62,
            [
              "ms_zhong_ji",
              "ms_fu_wen_chong_ji"
            ],
            [
              "远古符文石"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "dwarf_long_gallery_2",
        "name": "长廊中段",
        "icon": "🌲",
        "desc": "长廊中段的墙壁上刻满矮人的历史浮雕，工程师在灯下检修铁轨。冰元素在廊道尽头泛着寒气。",
        "type": "野外",
        "lv": 65,
        "npcs": ["npc_dwarf_engineer"],
        "monsters": [
          [
            "m_ice_elemental",
            "冰元素",
            "tank",
            65,
            [
              "ms_bing_dan",
              "ms_dong_jie"
            ],
            [
              "冰元素核心"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "dwarf_long_gallery_3",
        "name": "深岩闸门",
        "icon": "🌲",
        "desc": "深岩闸门半开着，门后是更深的黑暗。霜巨魔的低吼从门缝里传出来，震得铁链哗哗响。",
        "type": "野外",
        "lv": 68,
        "npcs": [],
        "monsters": [
          [
            "m_frost_troll",
            "霜巨魔",
            "dps",
            68,
            [
              "ms_zhong_ji",
              "ms_zai_sheng",
              "ms_bing_ji"
            ],
            [
              "霜巨魔血"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      }
    ],
    "cold_spine_snow_trail": [
      {
        "id": "cold_spine_snow_trail_1",
        "name": "铁砧北门",
        "icon": "🌲",
        "desc": "寒脊雪道的起点是铁砧堡的北门，雪原猛犸的足迹从门口一直延伸到雪线。猎人系紧雪靴，朝北进发。",
        "type": "野外",
        "lv": 66,
        "npcs": [
            "npc_snow_hunter",
        ],        "monsters": [
          [
            "m_snow_mammoth",
            "雪原猛犸",
            "tank",
            66,
            [
              "ms_chong_zhuang",
              "ms_jian_ta"
            ],
            [
              "猛犸毛"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "cold_spine_snow_trail_2",
        "name": "雪道中段",
        "icon": "🌲",
        "desc": "雪道中段风如刀割，古树守卫裹着冰甲立在路旁，像一座雪雕。",
        "type": "野外",
        "lv": 68,
        "npcs": [],
        "monsters": [
          [
            "m_old_tree_guardian",
            "古树守卫",
            "tank",
            68,
            [
              "ms_teng_bian",
              "ms_ying_hua"
            ],
            [
              "守卫古木"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "cold_spine_snow_trail_3",
        "name": "寒脊风口",
        "icon": "🌲",
        "desc": "寒脊风口的风能把人吹倒，冰原巨熊在风口蹲伏，毛发上结着冰晶。",
        "type": "野外",
        "lv": 71,
        "npcs": [],
        "monsters": [
          [
            "m_frost_bear",
            "冰原巨熊",
            "tank",
            68,
            [
              "ms_xiong_zhang",
              "ms_bing_hou"
            ],
            [
              "冰熊皮"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      }
    ],
    "dragon_ridge_old_road": [
      {
        "id": "dragon_ridge_old_road_1",
        "name": "王庭东门",
        "icon": "🌲",
        "desc": "龙脊古道的起点是月冠王庭的东门，暗影精灵在门外的树影间闪动。拾骨人背着袋子，沿着古道搜寻。",
        "type": "野外",
        "lv": 64,
        "npcs": [
            "npc_ridge_bonecollector",
        ],        "monsters": [
          [
            "m_shadow_elf",
            "暗影精灵",
            "dps",
            64,
            [
              "ms_an_ying_jian",
              "ms_qian_xing"
            ],
            [
              "暗影精灵刃"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "dragon_ridge_old_road_2",
        "name": "古道龙纹",
        "icon": "🌲",
        "desc": "古道的石板上刻着巨大的龙纹，远古魔像沿着龙纹巡行，每一步都震得碎石跳动。守墓人守在纹路尽头。",
        "type": "野外",
        "lv": 67,
        "npcs": ["npc_grave_keeper"],
        "monsters": [
          [
            "m_ancient_golem",
            "远古魔像",
            "tank",
            62,
            [
              "ms_zhong_ji",
              "ms_fu_wen_chong_ji"
            ],
            [
              "远古符文石"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "dragon_ridge_old_road_3",
        "name": "龙脊崖脚",
        "icon": "🌲",
        "desc": "龙脊崖脚的岩壁上留着龙爪的痕迹，熔岩元素在崖缝间散发热气。古树领主的根须从崖顶垂下，像一道绿色的瀑布。",
        "type": "野外",
        "lv": 70,
        "npcs": [],
        "monsters": [
          [
            "m_lava_elemental",
            "熔岩元素",
            "tank",
            70,
            [
              "ms_rong_yan_dan",
              "ms_zhuo_shao"
            ],
            [
              "熔岩核心"
            ]
          ],
          [
            "e_tree_lord",
            "古树领主",
            "elite",
            70,
            [
              "ms_teng_bian",
              "ms_gen_xu_chan_rao",
              "ms_zhao_huan_shu_ren"
            ],
            [
              "领主古木心"
            ]
          ]
        ],
        "elite": [
          "e_tree_lord",
          "古树领主",
          "elite",
          70,
          [
            "ms_teng_bian",
            "ms_gen_xu_chan_rao",
            "ms_zhao_huan_shu_ren"
          ],
          [
            "领主古木心"
          ]
        ],
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      }
    ],
    "dragonborn_valley_trail": [
      {
        "id": "dragonborn_valley_trail_1",
        "name": "聚落石阶",
        "icon": "🌲",
        "desc": "龙裔谷道的起点是聚落的石阶，朝圣者一级级往上走。深渊奴仆的影子在石阶两侧的阴影里潜伏。",
        "type": "野外",
        "lv": 81,
        "npcs": [
            "npc_valley_pilgrim",
        ],        "monsters": [
          [
            "m_demon_servant",
            "深渊奴仆",
            "tank",
            82,
            [
              "ms_zhong_ji",
              "ms_an_ying_dan"
            ],
            [
              "奴仆锁链"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "dragonborn_valley_trail_2",
        "name": "谷道中段",
        "icon": "🌲",
        "desc": "谷道中段两侧立着龙牙石柱，龙裔战士在柱下盘坐。长老的吟诵声在山谷间回荡。",
        "type": "野外",
        "lv": 83,
        "npcs": ["npc_dragonborn_elder"],
        "monsters": [
          [
            "m_dragonkin",
            "龙裔战士",
            "dps",
            82,
            [
              "ms_long_jian_shu"
            ],
            [
              "龙鳞碎片"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "dragonborn_valley_trail_3",
        "name": "山口龙喉",
        "icon": "🌲",
        "desc": "山口龙喉是一道天然的石门，形如龙口。骨虫在岩缝里蠕动，冰川龙·霜牙的寒气从门内漫出。",
        "type": "野外",
        "lv": 86,
        "npcs": [],
        "monsters": [
          [
            "m_bone_wyrm",
            "骨虫",
            "speedster",
            84,
            [
              "ms_gu_xi",
              "ms_chuan_shen"
            ],
            [
              "骨虫壳"
            ]
          ],
          [
            "e_glacier_wyrm",
            "冰川龙·霜牙",
            "elite",
            82,
            [
              "ms_bing_xi",
              "ms_long_zhao",
              "ms_dong_jie"
            ],
            [
              "霜牙龙鳞"
            ]
          ]
        ],
        "elite": [
          "e_glacier_wyrm",
          "冰川龙·霜牙",
          "elite",
          82,
          [
            "ms_bing_xi",
            "ms_long_zhao",
            "ms_dong_jie"
          ],
          [
            "霜牙龙鳞"
          ]
        ],
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      }
    ],
    "sky_ladder_path": [
      {
        "id": "sky_ladder_path_1",
        "name": "云梯起步",
        "icon": "🌲",
        "desc": "天梯云径的第一级石阶悬在崖边，云僧在阶前打坐。黑曜石魔像立在山道口，像一尊沉默的门卫。",
        "type": "野外",
        "lv": 82,
        "npcs": [
            "npc_sky_monk",
        ],        "monsters": [
          [
            "m_obsidian_golem",
            "黑曜石魔像",
            "tank",
            82,
            [
              "ms_zhong_ji",
              "ms_ying_hua"
            ],
            [
              "黑曜碎片"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "sky_ladder_path_2",
        "name": "云径中段",
        "icon": "🌲",
        "desc": "云径中段云雾缭绕，恶魔祭司在云间低语，声音被风撕成碎片。",
        "type": "野外",
        "lv": 85,
        "npcs": [],
        "monsters": [
          [
            "m_demon_priest",
            "恶魔祭司",
            "healer",
            82,
            [
              "ms_an_ying_dan",
              "ms_hei_an_zhi_liao"
            ],
            [
              "染血祭器"
            ]
          ]
        ],
        "elite": None,
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      },
      {
        "id": "sky_ladder_path_3",
        "name": "风翼台",
        "icon": "🌲",
        "desc": "风翼台悬在云海之上，石龙伏在台上晒着日光，恶魔战士在台边巡视。从这里再往上，就是风翼城。",
        "type": "野外",
        "lv": 88,
        "npcs": [],
        "monsters": [
          [
            "m_stone_dragon",
            "石龙",
            "tank",
            85,
            [
              "ms_shi_xi",
              "ms_zhong_ji"
            ],
            [
              "石龙鳞"
            ]
          ],
          [
            "e_demon_warrior",
            "恶魔战士",
            "elite",
            86,
            [
              "ms_zhang_jian",
              "ms_di_yu_huo"
            ],
            [
              "恶魔战刃"
            ]
          ]
        ],
        "elite": [
          "e_demon_warrior",
          "恶魔战士",
          "elite",
          86,
          [
            "ms_zhang_jian",
            "ms_di_yu_huo"
          ],
          [
            "恶魔战刃"
          ]
        ],
        "boss": None,
        "funcs": [
          "explore"
        ],
        "shop": False,
        "healer": False
      }
    ]
}