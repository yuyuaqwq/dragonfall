# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - subareas.py(自动生成，2026－08－07)"""
# 子区域拆分：02 章 13 节。key=地图id，value=子区域列表（顺序即默认落点）
SUBAREAS = {
    "oak_town": [
        {
            "id": "oak_town_1",
            "name": "冒险者广场",
            "icon": "🏘️",
            "desc": "橡木镇·冒险者广场",
            "type": "城镇",
            "lv": 1,
            "npcs": [
                "npc_guild_clerks"
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
            "desc": "橡木镇·镇长办公处",
            "type": "城镇",
            "lv": 1,
            "npcs": [
                "npc_mayor"
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
            "desc": "橡木镇·老铁铁匠铺",
            "type": "城镇",
            "lv": 1,
            "npcs": [
                "npc_blacksmith"
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
            "desc": "橡木镇·橡木桶旅店",
            "type": "城镇",
            "lv": 1,
            "npcs": [
                "npc_innkeeper"
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
            "desc": "橡木镇·草药铺",
            "type": "城镇",
            "lv": 1,
            "npcs": [
                "npc_herb_master"
            ],
            "monsters": [],
            "elite": None,
            "boss": None,
            "funcs": [],
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
            "npcs": ["npc_oak_street_vendor"],
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
            "npcs": ["npc_oak_outskirts_farmer"],
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
            "desc": "橡木平原·草地边缘",
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
            "desc": "橡木平原·草地深处",
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
            "desc": "橡木平原·溪边草地",
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
                [
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
                ]
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
            "desc": "白鹿之森·林间入口",
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
            "desc": "白鹿之森·白鹿之森深处",
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
            "desc": "白鹿之森·溪谷",
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
            "desc": "白鹿城·白鹿广场",
            "type": "城镇",
            "lv": 5,
            "npcs": [
                "npc_tavern_owner",
                "npc_warrior_tutor",
                "npc_mage_tutor",
                "npc_priest_tutor"
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
            "desc": "白鹿城·城主府",
            "type": "城镇",
            "lv": 5,
            "npcs": [
                "npc_baron"
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
            "desc": "白鹿城·鹿角铁匠铺",
            "type": "城镇",
            "lv": 5,
            "npcs": [
                "npc_blacksmith2"
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
            "desc": "白鹿城·白鹿圣堂",
            "type": "城镇",
            "lv": 5,
            "npcs": [
                "npc_priest"
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
            "desc": "白鹿城·白鹿与麦酒酒馆",
            "type": "城镇",
            "lv": 5,
            "npcs": [
                "npc_deer_newsboy",
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
            "desc": "白鹿城·医师馆",
            "type": "城镇",
            "lv": 5,
            "npcs": [
                "npc_doctor"
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
            "id": "white_deer_7",
            "name": "烹饪坊",
            "icon": "🏘️",
            "desc": "白鹿城·烹饪坊",
            "type": "城镇",
            "lv": 5,
            "npcs": [
                "npc_cook_master"
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
            "desc": "白鹿城·强化工坊",
            "type": "城镇",
            "lv": 5,
            "npcs": [
                "npc_enhance_master"
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
            "npcs": ["npc_white_deer_gate_guard"],
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
            "desc": "翡翠森林·林间小径",
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
            "desc": "翡翠森林·森林深处",
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
            "desc": "翡翠森林·古树空地",
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
                [
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
                ]
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
            "desc": "迷雾沼泽·沼泽边缘",
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
            "desc": "迷雾沼泽·芦苇荡",
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
            "desc": "迷雾沼泽·沼泽深处",
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
                [
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
                ]
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
            "desc": "哥布林营地入口",
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
            "desc": "山丘矿洞·矿洞入口",
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
            "desc": "山丘矿洞·矿道",
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
            "desc": "山丘矿洞·矿洞深处",
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
                [
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
                ]
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
            "desc": "铁港城·港口广场",
            "type": "城镇",
            "lv": 10,
            "npcs": [
                "npc_bard",
                "npc_goblin_merchant",
                "npc_fish_master",
                "npc_craft_master",
                "npc_ranger_tutor",
                "npc_assassin_tutor",
                "npc_monk_tutor"
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
            "desc": "铁港城·城主府",
            "type": "城镇",
            "lv": 10,
            "npcs": [
                "npc_citylord"
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
            "desc": "铁港城·冒险者行会总部",
            "type": "城镇",
            "lv": 10,
            "npcs": [
                "npc_guildmaster"
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
            "desc": "铁港城·金槌拍卖行",
            "type": "城镇",
            "lv": 10,
            "npcs": [
                "npc_auctioneer"
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
            "desc": "铁港城·铁锚酒馆",
            "type": "城镇",
            "lv": 10,
            "npcs": [
                "npc_harbor_rope",
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
            "id": "ironharbor_6",
            "name": "金齿轮商行",
            "icon": "🏘️",
            "desc": "铁港城·金齿轮商行",
            "type": "城镇",
            "lv": 10,
            "npcs": [
                "npc_harbor_fishwife",
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
            "desc": "铁港城·矿工工会",
            "type": "城镇",
            "lv": 10,
            "npcs": [
                "npc_mine_master"
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
            "desc": "铁港城·渔人码头",
            "type": "城镇",
            "lv": 10,
            "npcs": [],
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
            "desc": "铁港城·锻造坊",
            "type": "城镇",
            "lv": 10,
            "npcs": [
                "npc_harbor_watchman",
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
            "npcs": ["npc_ironharbor_gate_guard"],
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
            "desc": "铁港码头·码头栈桥",
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
            "desc": "铁港码头·货仓区",
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
            "desc": "铁港码头·海堤",
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
                [
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
                ]
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
            "desc": "海蚀洞窟入口",
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
            "desc": "银溪镇·银溪广场",
            "type": "城镇",
            "lv": 12,
            "npcs": [
                "npc_silver_fisher",
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
            "desc": "银溪镇·磨坊街",
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
            "desc": "银溪镇·河畔旅店",
            "type": "城镇",
            "lv": 12,
            "npcs": [
                "npc_silver_apprentice",
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
            "desc": "银溪镇·集市",
            "type": "城镇",
            "lv": 12,
            "npcs": [
                "npc_silver_peddler",
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
            "desc": "银溪谷地·谷地入口",
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
            "desc": "银溪谷地·溪谷",
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
            "desc": "银溪谷地·谷地深处",
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
                [
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
                ]
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
            "desc": "风车原野·原野边缘",
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
            "desc": "风车原野·风车田",
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
            "desc": "风车原野·原野深处",
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
                [
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
                ]
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
            "desc": "鹿角要塞入口",
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
            "desc": "枫橡村·村口广场",
            "type": "城镇",
            "lv": 6,
            "npcs": [
                "npc_maple_woodcutter",
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
            "desc": "枫橡村·村长屋",
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
            "desc": "枫橡村·猎人小屋",
            "type": "城镇",
            "lv": 6,
            "npcs": [
                "npc_hunter_gray"
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
            "desc": "枫橡村·枫叶旅店",
            "type": "城镇",
            "lv": 6,
            "npcs": [
                "npc_inn_tess"
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
            "desc": "落石峡谷·峡谷口",
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
            "desc": "落石峡谷·峡谷栈道",
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
            "desc": "落石峡谷·峡谷深处",
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
                [
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
                ]
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
            "desc": "野猪岭·山脚",
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
            "desc": "野猪岭·山腰",
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
            "desc": "野猪岭·野猪王巢",
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
                [
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
                ]
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
            "desc": "晨曦城·王都广场",
            "type": "城镇",
            "lv": 25,
            "npcs": [
                "npc_knight_commander",
                "npc_alchemy_master"
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
            "desc": "晨曦城·圣光王宫",
            "type": "城镇",
            "lv": 25,
            "npcs": [
                "npc_king"
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
            "desc": "晨曦城·圣光大教堂",
            "type": "城镇",
            "lv": 25,
            "npcs": [
                "npc_pope",
                "npc_cardinal",
                "npc_saintess"
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
            "desc": "晨曦城·骑士团驻地",
            "type": "城镇",
            "lv": 25,
            "npcs": [
                "npc_dawn_gardener",
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
            "desc": "晨曦城·炼金工坊",
            "type": "城镇",
            "lv": 25,
            "npcs": [
                "npc_dawn_squire",
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
            "npcs": ["npc_dawn_city_gate_guard"],
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
            "desc": "晨曦大圣堂·圣堂前庭",
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
            "desc": "晨曦大圣堂·回廊",
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
            "desc": "晨曦大圣堂·圣堂地窟",
            "type": "野外",
            "lv": 35,
            "npcs": [],
            "monsters": [
                [
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
            "desc": "金穗平原·平原边缘",
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
            "desc": "金穗平原·麦田区",
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
            "desc": "金穗平原·平原深处",
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
                [
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
                ]
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
            "desc": "白石修道院·修道院门口",
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
            "desc": "白石修道院·庭院",
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
            "desc": "白石修道院·地窖",
            "type": "野外",
            "lv": 38,
            "npcs": [],
            "monsters": [
                [
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
                ]
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
            "desc": "旧王陵入口",
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
            "desc": "边境堡·堡外荒野",
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
            "desc": "边境堡·城墙下",
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
            "desc": "边境堡·堡内广场",
            "type": "野外",
            "lv": 50,
            "npcs": [],
            "monsters": [
                [
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
                ]
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
            "desc": "银铃河·河岸",
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
            "desc": "银铃河·渡口",
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
            "desc": "银铃河·河心洲",
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
                [
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
                ]
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
            "desc": "圣堂地窖入口",
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
            "desc": "圣骑士训练场·训练场入口",
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
            "desc": "圣骑士训练场·靶场",
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
            "desc": "圣骑士训练场·魔像试炼区",
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
    "king_road": [
        {
            "id": "king_road_1",
            "name": "古道口",
            "icon": "🌲",
            "desc": "王陵古道·古道口",
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
            "desc": "王陵古道·古道中段",
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
            "desc": "王陵古道·王陵前",
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
                [
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
                ]
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
            "desc": "圣光试炼场入口",
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
            "desc": "铁盾镇·铁盾广场",
            "type": "城镇",
            "lv": 30,
            "npcs": [
                "npc_ironshield_smith"
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
            "desc": "铁盾镇·镇公所",
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
            "desc": "铁盾镇·军械铺",
            "type": "城镇",
            "lv": 30,
            "npcs": [
                "npc_shield_watch",
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
            "desc": "铁盾镇·斥候营",
            "type": "城镇",
            "lv": 30,
            "npcs": [
                "npc_ironshield_scout"
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
            "npcs": ["npc_ironshield_town_gate_guard"],
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
            "desc": "铁盾丘陵·丘陵脚",
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
            "desc": "铁盾丘陵·丘陵中",
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
            "desc": "铁盾丘陵·丘陵顶",
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
                [
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
                ]
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
            "desc": "旧战场遗址·遗址边缘",
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
            "desc": "旧战场遗址·战壕区",
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
            "desc": "旧战场遗址·遗址核心",
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
                [
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
                ]
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
            "desc": "月冠隘口·月门广场",
            "type": "城镇",
            "lv": 45,
            "npcs": [
                "npc_moongate_guard",
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
            "desc": "月冠隘口·银月旅店",
            "type": "城镇",
            "lv": 45,
            "npcs": [
                "npc_moongate_astronomer",
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
            "desc": "月冠隘口·哨塔集市",
            "type": "城镇",
            "lv": 45,
            "npcs": [
                "npc_moongate_silk",
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
            "desc": "银月林海·林海边缘",
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
            "desc": "银月林海·林海深处",
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
            "desc": "银月林海·月辉空地",
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
                [
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
                ]
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
            "desc": "星语湖·湖畔",
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
            "desc": "星语湖·湖岸小径",
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
            "desc": "星语湖·湖心岛",
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
    "moon_court": [
        {
            "id": "moon_court_1",
            "name": "王庭广场",
            "icon": "🏘️",
            "desc": "月冠王庭·王庭广场",
            "type": "城镇",
            "lv": 55,
            "npcs": [
                "npc_elf_sage"
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
            "desc": "月冠王庭·月辉王宫",
            "type": "城镇",
            "lv": 55,
            "npcs": [
                "npc_elf_queen",
                "npc_elf_guardian"
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
            "desc": "月冠王庭·月影卫营",
            "type": "城镇",
            "lv": 55,
            "npcs": [
                "npc_elf_gardener",
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
            "desc": "月冠王庭·贤者书阁",
            "type": "城镇",
            "lv": 55,
            "npcs": [
                "npc_elf_rabbit",
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
            "npcs": ["npc_moon_court_gate_guard"],
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
            "desc": "精灵废墟入口",
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
            "desc": "古树隘口·隘口下",
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
            "desc": "古树隘口·树道",
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
            "desc": "古树隘口·古树之巅",
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
    "star_song": [
        {
            "id": "star_song_1",
            "name": "星歌广场",
            "icon": "🏘️",
            "desc": "星歌镇·星歌广场",
            "type": "城镇",
            "lv": 48,
            "npcs": [
                "npc_starsong_bardling",
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
            "desc": "星歌镇·星光集市",
            "type": "城镇",
            "lv": 48,
            "npcs": [
                "npc_starsong_baker",
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
            "desc": "星歌镇·星歌旅店",
            "type": "城镇",
            "lv": 48,
            "npcs": [
                "npc_starsong_drunkard",
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
            "desc": "月光林·林缘",
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
            "desc": "月光林·月光空地",
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
            "desc": "月光林·林深处",
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
                [
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
                ]
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
            "desc": "翠谷·谷口",
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
            "desc": "翠谷·谷中",
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
            "desc": "翠谷·翠谷深处",
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
                [
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
                ]
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
            "desc": "月神圣殿入口",
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
            "desc": "风语谷·谷口",
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
            "desc": "风语谷·风语草原",
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
            "desc": "风语谷·谷底",
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
                [
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
                ]
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
            "desc": "月影林·林缘",
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
            "desc": "月影林·影径",
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
            "desc": "月影林·月影深处",
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
                [
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
                ]
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
            "desc": "霜角堡·堡垒广场",
            "type": "城镇",
            "lv": 60,
            "npcs": [
                "npc_tavern_burnkettle",
                "npc_garrison"
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
            "desc": "霜角堡·酋长大厅",
            "type": "城镇",
            "lv": 60,
            "npcs": [
                "npc_north_chief"
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
            "desc": "霜角堡·霜角酒馆",
            "type": "城镇",
            "lv": 60,
            "npcs": [
                "npc_frost_hunter",
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
            "desc": "霜角堡·守备营",
            "type": "城镇",
            "lv": 60,
            "npcs": [
                "npc_frost_weaver",
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
            "desc": "霜角堡·随军圣堂",
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
            "desc": "霜原·霜原边缘",
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
            "desc": "霜原·雪地",
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
            "desc": "霜原·霜原深处",
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
                [
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
                ]
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
            "desc": "铁砧要塞·熔炉广场",
            "type": "城镇",
            "lv": 65,
            "npcs": [
                "npc_rune_master"
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
            "desc": "铁砧要塞·铁砧议会厅",
            "type": "城镇",
            "lv": 65,
            "npcs": [
                "npc_dwarf_elder"
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
            "desc": "铁砧要塞·符文工坊",
            "type": "城镇",
            "lv": 65,
            "npcs": [
                "npc_anvil_brewer",
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
            "npcs": ["npc_anvil_fort_gate_guard"],
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
            "desc": "熔炉谷·谷口",
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
            "desc": "熔炉谷·熔岩河畔",
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
            "desc": "熔炉谷·熔炉心",
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
                [
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
                ]
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
            "desc": "黑森林·林缘",
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
            "desc": "黑森林·腐林",
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
            "desc": "黑森林·森林深处",
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
                [
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
                ]
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
            "desc": "烬山·山脚",
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
            "desc": "烬山·山腰",
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
            "desc": "烬山·火山口",
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
    ],
    "ash_temple": [
        {
            "id": "ash_temple_1",
            "name": "入口",
            "icon": "🚪",
            "desc": "烬山祭坛入口",
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
            "desc": "深渊裂隙入口",
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
            "desc": "冰牙谷·谷口",
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
            "desc": "冰牙谷·冰径",
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
            "desc": "冰牙谷·冰牙深处",
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
                [
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
                ]
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
            "desc": "寒脊营地·营地口",
            "type": "城镇",
            "lv": 68,
            "npcs": [
                "npc_cold_hunter",
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
            "desc": "寒脊营地·主帐篷",
            "type": "城镇",
            "lv": 68,
            "npcs": [
                "npc_cold_herder",
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
            "desc": "寒脊营地·补给站",
            "type": "城镇",
            "lv": 68,
            "npcs": [
                "npc_cold_firekeeper",
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
            "npcs": ["npc_cold_ridge_gate_guard"],
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
            "desc": "永冬湖·湖畔",
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
            "desc": "永冬湖·冰面",
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
            "desc": "永冬湖·湖心",
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
                [
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
                ]
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
            "desc": "冰霜王座入口",
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
            "desc": "极光镇·极光广场",
            "type": "城镇",
            "lv": 70,
            "npcs": [
                "npc_aurora_scribe",
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
            "desc": "极光镇·镇长公馆",
            "type": "城镇",
            "lv": 70,
            "npcs": [
                "npc_aurora_mayor"
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
            "desc": "极光镇·猎手营",
            "type": "城镇",
            "lv": 70,
            "npcs": [
                "npc_frost_blade"
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
            "desc": "极光镇·暖炉旅店",
            "type": "城镇",
            "lv": 70,
            "npcs": [
                "npc_warm_stove"
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
            "npcs": ["npc_aurora_town_gate_guard"],
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
            "desc": "永冻冰原·冰原边缘",
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
            "desc": "永冻冰原·冰原中",
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
            "desc": "永冻冰原·冰原深处",
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
                [
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
                ]
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
            "desc": "霜语峡谷·峡谷口",
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
            "desc": "霜语峡谷·峡谷道",
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
            "desc": "霜语峡谷·霜语尽头",
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
    "dragon_pass": [
        {
            "id": "dragon_pass_1",
            "name": "山口广场",
            "icon": "🏘️",
            "desc": "龙脊山口·山口广场",
            "type": "城镇",
            "lv": 80,
            "npcs": [
                "npc_pass_stationmaster",
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
            "desc": "龙脊山口·龙裔长老堂",
            "type": "城镇",
            "lv": 80,
            "npcs": [
                "npc_dragon_elder"
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
            "npcs": ["npc_dragon_pass_gate_guard"],
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
            "desc": "龙脊山脉·山脚",
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
            "desc": "龙脊山脉·山道",
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
            "desc": "龙脊山脉·龙脊之巅",
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
            "desc": "龙巢·巢外峭壁",
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
            "desc": "龙巢·龙巢口",
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
            "desc": "龙巢·巢穴深处",
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
                [
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
                ]
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
            "desc": "古战场·战场边缘",
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
            "desc": "古战场·战场中",
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
            "desc": "古战场·战场核心",
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
            "desc": "龙之墓入口",
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
            "desc": "龙裔聚落·聚落广场",
            "type": "城镇",
            "lv": 82,
            "npcs": [
                "npc_dragonkin_youth",
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
            "desc": "龙裔聚落·龙裔祭坛",
            "type": "城镇",
            "lv": 82,
            "npcs": [
                "npc_dragonkin_elder",
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
            "desc": "龙裔聚落·旅店",
            "type": "城镇",
            "lv": 82,
            "npcs": [
                "npc_dragonkin_smith",
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
            "desc": "龙骨荒野·荒野边缘",
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
            "desc": "龙骨荒野·骨堆区",
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
            "desc": "龙骨荒野·荒野深处",
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
                [
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
                ]
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
            "desc": "风暴崖·崖脚",
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
            "desc": "风暴崖·崖道",
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
            "desc": "风暴崖·风暴崖顶",
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
                [
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
                ]
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
            "desc": "风暴王座入口",
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
            "desc": "赤脊高原·高原边缘",
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
            "desc": "赤脊高原·赤脊中",
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
            "desc": "赤脊高原·高原深处",
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
                [
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
                ]
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
            "desc": "龙陨谷·谷口",
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
            "desc": "龙陨谷·龙骸区",
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
            "desc": "龙陨谷·谷底",
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
                [
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
                ]
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
            "desc": "翡翠港·港口广场",
            "type": "城镇",
            "lv": 35,
            "npcs": [
                "npc_jade_docker",
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
            "desc": "翡翠港·翡翠集市",
            "type": "城镇",
            "lv": 35,
            "npcs": [
                "npc_jade_carver",
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
            "desc": "翡翠港·船坞旅店",
            "type": "城镇",
            "lv": 35,
            "npcs": [
                "npc_jade_helmsman",
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
            "desc": "贝壳镇·贝壳集市",
            "type": "城镇",
            "lv": 40,
            "npcs": [
                "npc_shell_picker",
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
            "desc": "贝壳镇·码头",
            "type": "城镇",
            "lv": 40,
            "npcs": [
                "npc_shell_netter",
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
            "desc": "贝壳镇·旅店",
            "type": "城镇",
            "lv": 40,
            "npcs": [
                "npc_shell_gatherer",
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
            "npcs": ["npc_shell_town_gate_guard"],
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
            "desc": "珊瑚礁·礁滩",
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
            "desc": "珊瑚礁·珊瑚丛",
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
            "desc": "珊瑚礁·礁群深处",
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
                [
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
                ]
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
            "desc": "落日岛·岛滩",
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
            "desc": "落日岛·岛林",
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
            "desc": "落日岛·岛心",
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
    "storm_strait": [
        {
            "id": "storm_strait_1",
            "name": "海峡口",
            "icon": "🌲",
            "desc": "风暴海峡·海峡口",
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
            "desc": "风暴海峡·急流区",
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
            "desc": "风暴海峡·海峡深处",
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
                [
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
                ]
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
            "desc": "海妖湾·湾口",
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
            "desc": "海妖湾·珊瑚湾",
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
            "desc": "海妖湾·海妖巢",
            "type": "野外",
            "lv": 55,
            "npcs": [],
            "monsters": [
                [
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
                ]
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
            "desc": "沉船湾入口",
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
            "desc": "海妖巢穴入口",
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
            "desc": "无名港·港口广场",
            "type": "城镇",
            "lv": 55,
            "npcs": [
                "npc_nameless_catwoman",
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
            "desc": "无名港·港务厅",
            "type": "城镇",
            "lv": 55,
            "npcs": [
                "npc_harbor_master"
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
            "desc": "无名港·远洋码头",
            "type": "城镇",
            "lv": 55,
            "npcs": [
                "npc_captain_maelian"
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
            "npcs": ["npc_nameless_harbor_gate_guard"],
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
            "desc": "珍珠城·珍珠广场",
            "type": "城镇",
            "lv": 62,
            "npcs": [
                "npc_sea_gull_tim",
                "npc_old_whale"
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
            "desc": "珍珠城·城主府",
            "type": "城镇",
            "lv": 62,
            "npcs": [
                "npc_pearl_lord"
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
            "desc": "珍珠城·珊瑚拍卖行",
            "type": "城镇",
            "lv": 62,
            "npcs": [
                "npc_coral_auctioneer"
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
            "desc": "珍珠城·商行",
            "type": "城镇",
            "lv": 62,
            "npcs": [
                "npc_pearl_diver",
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
            "desc": "珍珠城·渔港",
            "type": "城镇",
            "lv": 62,
            "npcs": [
                "npc_pearl_shuttler",
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
            "desc": "迷雾海沟·海沟口",
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
            "desc": "迷雾海沟·迷雾区",
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
            "desc": "迷雾海沟·海沟深处",
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
                [
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
                ]
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
            "desc": "龙鲸海域·海域边缘",
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
            "desc": "龙鲸海域·龙鲸路",
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
            "desc": "龙鲸海域·海域深处",
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
                [
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
                ]
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
            "desc": "沉船墓地·墓地边缘",
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
            "desc": "沉船墓地·沉船区",
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
            "desc": "沉船墓地·墓地核心",
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
                [
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
                ]
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
            "desc": "风暴之海·海缘",
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
            "desc": "风暴之海·风暴区",
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
            "desc": "风暴之海·海眼",
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
                [
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
                ]
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
            "desc": "海神神殿入口",
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
            "desc": "深海龙宫入口",
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
            "desc": "深岩隧道·隧道口",
            "type": "城镇",
            "lv": 65,
            "npcs": [
                "npc_tunnel_miner",
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
            "desc": "深岩隧道·中央大厅",
            "type": "城镇",
            "lv": 65,
            "npcs": [
                "npc_tunnel_lamp",
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
            "desc": "深岩隧道·营地区",
            "type": "城镇",
            "lv": 65,
            "npcs": [
                "npc_tunnel_carter",
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
            "npcs": ["npc_deep_tunnel_gate_guard"],
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
            "desc": "地底集市·集市广场",
            "type": "城镇",
            "lv": 70,
            "npcs": [
                "npc_under_trader",
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
            "desc": "地底集市·拍卖区",
            "type": "城镇",
            "lv": 70,
            "npcs": [
                "npc_under_guard",
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
            "desc": "地底集市·旅店",
            "type": "城镇",
            "lv": 70,
            "npcs": [
                "npc_under_whisper",
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
            "desc": "真菌森林·菌林边缘",
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
            "desc": "真菌森林·孢子区",
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
            "desc": "真菌森林·菌林深处",
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
                [
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
                ]
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
            "desc": "地下湖·湖岸",
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
            "desc": "地下湖·湖桥",
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
            "desc": "地下湖·湖底",
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
                [
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
                ]
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
            "desc": "熔火深渊·深渊口",
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
            "desc": "熔火深渊·熔岩道",
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
            "desc": "熔火深渊·深渊深处",
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
                [
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
                ]
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
            "desc": "灰矮人要塞入口",
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
            "desc": "地底龙巢入口",
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
            "desc": "灰烬营地·营地口",
            "type": "城镇",
            "lv": 85,
            "npcs": [
                "npc_under_guide",
                "npc_ember_merchant"
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
            "desc": "灰烬营地·营长帐",
            "type": "城镇",
            "lv": 85,
            "npcs": [
                "npc_ember_camp_leader"
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
            "desc": "灰烬营地·地底向导所",
            "type": "城镇",
            "lv": 85,
            "npcs": [
                "npc_ember_cook",
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
            "desc": "灰烬营地·补给站",
            "type": "城镇",
            "lv": 85,
            "npcs": [
                "npc_ember_scout",
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
            "desc": "熔岩河床·河床口",
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
            "desc": "熔岩河床·熔岩滩",
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
            "desc": "熔岩河床·河床深处",
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
                [
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
                ]
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
            "desc": "深渊祭坛·祭坛外围",
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
            "desc": "深渊祭坛·祭坛廊道",
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
            "desc": "深渊祭坛·祭坛核心",
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
                [
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
                ]
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
            "desc": "深渊王座入口",
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
            "desc": "风翼城·浮空广场",
            "type": "城镇",
            "lv": 85,
            "npcs": [
                "npc_wind_kitemaker",
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
            "desc": "风翼城·云翼议会厅",
            "type": "城镇",
            "lv": 85,
            "npcs": [
                "npc_wind_elder"
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
            "npcs": ["npc_wind_city_gate_guard"],
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
            "desc": "云海·云海边",
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
            "desc": "云海·云岛",
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
            "desc": "云海·云海深处",
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
                [
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
                ]
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
            "desc": "雷暴高原·高原边缘",
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
            "desc": "雷暴高原·雷区",
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
            "desc": "雷暴高原·高原核心",
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
                [
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
                ]
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
            "desc": "风暴之眼入口",
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
            "desc": "彩虹云谷·云谷口",
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
            "desc": "彩虹云谷·彩虹桥",
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
            "desc": "彩虹云谷·云谷深处",
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
                [
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
                ]
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
            "desc": "星辉台·台缘",
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
            "desc": "星辉台·星辉路",
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
            "desc": "星辉台·星辉之巅",
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
                [
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
                ]
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
            "desc": "云中圣殿入口",
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
            "desc": "失落图书馆入口",
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
                [
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
                ]
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
            "desc": "灰烬回廊入口",
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
                [
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
                ]
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
        "desc": "银风商道·银风道口",
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
        "desc": "银风商道·银风驿站",
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
        "desc": "西岭荒原·西岭口",
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
        "desc": "西岭荒原·荒原腹地",
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
        "desc": "西岭荒原·落霞坡",
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
        "desc": "暮岭古道·岭脚石阶",
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
        "desc": "暮岭古道·半山烽台",
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
        "desc": "暮岭古道·月冠垭口",
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
        "desc": "雾潮航道·港外锚地",
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
        "desc": "雾潮航道·雾潮中段",
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
        "desc": "雾潮航道·无名灯塔",
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
        "desc": "黑潮海峡·无名礁口",
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
        "desc": "黑潮海峡·黑潮中流",
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
        "desc": "黑潮海峡·珍珠湾",
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
        "desc": "矮人长廊·要塞铁门",
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
        "desc": "矮人长廊·长廊中段",
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
        "desc": "矮人长廊·深岩闸门",
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
        "desc": "寒脊雪道·铁砧北门",
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
        "desc": "寒脊雪道·雪道中段",
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
        "desc": "寒脊雪道·寒脊风口",
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
        "desc": "龙脊古道·王庭东门",
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
        "desc": "龙脊古道·古道龙纹",
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
        "desc": "龙脊古道·龙脊崖脚",
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
        "desc": "龙裔谷道·聚落石阶",
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
        "desc": "龙裔谷道·谷道中段",
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
        "desc": "龙裔谷道·山口龙喉",
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
        "desc": "天梯云径·云梯起步",
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
        "desc": "天梯云径·云径中段",
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
        "desc": "天梯云径·风翼台",
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