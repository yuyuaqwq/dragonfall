# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - instances.py（阶段四重写，2026-08-06）

22 副本（02 章八·副本总览）：
- 主线 8：哥布林营地/海蚀洞窟/旧王陵/圣堂地窖/精灵废墟/烬山祭坛/深渊裂隙/龙之墓
- 区域支线 5：鹿角要塞/圣光试炼场/月神圣殿/冰霜王座/风暴王座
- 外域 6：沉船湾/海妖巢穴/海神神殿/深海龙宫/灰矮人要塞/地底龙巢
- 扩展 3：风暴之眼/深渊王座/云中圣殿

Boss 全部引用 04 章 b_* 定义（阶段三/四已挂进地图 monsters）：
- boss 6 元组 = (id, 名, role, lv, [技能ID], [掉落材料])
- 血量缩放：hp_mult + 0.65 × (实际人数 - min_players)
- 通关：每人金币/经验 + 专属材料；blueprint=True 额外图纸
"""
INSTANCES = {
    # ================= 主线 8（多人/进阶） =================
    "inst_goblin_camp": {
        "name": "哥布林营地",
        "icon": "👺",
        "lv": 15,
        "min_players": 1,
        "max_players": 2,  # v101.24：1-2 人（鱼鱼拍板，双人小队可一起打）
        "desc": "商路旁的哥布林聚落，哥布林酋长·咕噜盘踞于此，靠抢劫商队为生。冒险者行会悬赏讨伐。(主线第 2 章)",
        "boss": ["b_goblin_chief", "哥布林酋长·咕噜", "boss", 20,
                 ["ms_lian_zhan", "ms_nu_hou", "ms_zhao_huan"],
                 ["咕噜的皇冠"]],
                "stages":         [
            {
                "name": "营地前哨",
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
                    ]
                ]
            },
            {
                "name": "酋长帐篷",
                "monsters": [
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
                    ]
                ],
                "elite": [
                    "e_goblin_berserker",
                    "哥布林狂战士",
                    "elite",
                    18,
                    [
                        "ms_kuang_bao",
                        "ms_lian_zhan"
                    ],
                    [
                        "哥布林徽记"
                    ]
                ]
            },
            {
                "name": "酋长宝座",
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
                ]
            }
        ],
"mech": "summon,stacks",
        "hp_mult": 1.6,
        "atk_mult": 1.0,
        "gold": 120,
        "exp": 180,
        "materials": ["咕噜的皇冠"],
        "mat_count": 1,
        "blueprint": False,
    },
    "inst_sea_cave": {
        "name": "海蚀洞窟",
        "icon": "🌊",
        "lv": 22,
        "min_players": 2,
        "max_players": 3,
        "desc": "铁港码头下的海蚀洞穴，海盗王·独眼杰克的老巢。潮水声里混着金币碰撞的脆响。(主线第 3 章)",
        "boss": ["b_jack_pirate", "海盗王·独眼杰克", "boss", 28,
                 ["ms_wan_dao", "ms_huo_qiang", "ms_zhao_huan_shui_gui"],
                 ["杰克的金钩"]],
                "stages":         [
            {
                "name": "洞口滩涂",
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
                    ]
                ]
            },
            {
                "name": "洞窟深处",
                "monsters": [
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
                    ]
                ],
                "elite": [
                    "e_pirate_elite",
                    "海盗精锐",
                    "elite",
                    26,
                    [
                        "ms_wan_dao",
                        "ms_huo_qiang"
                    ],
                    [
                        "海妖鳞片"
                    ]
                ]
            },
            {
                "name": "藏宝密室",
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
                ]
            }
        ],
"mech": "phase",
        "hp_mult": 2.2,
        "atk_mult": 1.15,
        "gold": 220,
        "exp": 320,
        "materials": ["杰克的金钩"],
        "mat_count": 2,
        "blueprint": True,
    },
    "inst_old_king_tomb": {
        "name": "旧王陵",
        "icon": "🦴",
        "lv": 35,
        "min_players": 2,
        "max_players": 3,
        "desc": "晨曦城北的古老王陵，埋葬着圣战前的历代君王。古王·奥德里克在棺椁中苏醒，亡灵的低语回荡在石壁之间。(主线第 6 章)",
        "boss": ["b_king_odric", "古王·奥德里克", "boss", 45,
                 ["ms_jian_ji", "ms_wang_wei", "ms_zhao_huan_ku_lou"],
                 ["古王剑"]],
                "stages":         [
            {
                "name": "墓道",
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
                    ]
                ]
            },
            {
                "name": "主墓室",
                "monsters": [
                    [
                        "m_ghost",
                        "幽灵",
                        "speedster",
                        37,
                        [
                            "ms_chuan_shen",
                            "ms_ai_hao"
                        ],
                        [
                            "幽灵之尘"
                        ]
                    ]
                ],
                "elite": [
                    "e_ghost_king",
                    "幽灵骑士",
                    "elite",
                    40,
                    [
                        "ms_you_ling",
                        "ms_zhao_huan"
                    ],
                    [
                        "古王碎片"
                    ]
                ]
            },
            {
                "name": "王座厅",
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
                ]
            }
        ],
        "key_item": "王陵钥匙",
        "key_source": "白鹿城铁匠铺购买(500 金)",
"mech": "enrage,summon",
        "hp_mult": 2.5,
        "atk_mult": 1.2,
        "gold": 400,
        "exp": 550,
        "materials": ["古王剑"],
        "mat_count": 2,
        "blueprint": True,
    },
    "inst_secret_crypt": {
        "name": "圣堂地窖",
        "icon": "⛪",
        "lv": 42,
        "min_players": 3,
        "max_players": 4,
        "desc": "晨曦大圣堂下的密室，教会最深的秘密沉睡于此。审判长·马尔库斯奉命看守——他的锁链，从不问对错。(主线第 11 章)",
        "boss": ["b_marcus", "审判长·马尔库斯", "boss", 52,
                 ["ms_an_ying_dan", "ms_suo_lian", "ms_shen_pan_zhi_yan"],
                 ["马尔库斯的法冠"]],
                "stages":         [
            {
                "name": "地窖回廊",
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
                    ]
                ]
            },
            {
                "name": "审判庭",
                "monsters": [],
                "elite": [
                    "e_judge_hound",
                    "审判猎犬",
                    "elite",
                    45,
                    [
                        "ms_kuang_bao",
                        "ms_si_yao"
                    ],
                    [
                        "圣光圣徽"
                    ]
                ]
            },
            {
                "name": "枢机密室",
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
                ]
            }
        ],
        "key_item": "圣堂信物",
        "key_source": "晨曦城大教堂任务奖励",
"mech": "shield,enrage",
        "hp_mult": 2.6,
        "atk_mult": 1.25,
        "gold": 600,
        "exp": 800,
        "materials": ["马尔库斯的法冠"],
        "mat_count": 3,
        "blueprint": True,
    },
    "inst_elven_ruins": {
        "name": "精灵废墟",
        "icon": "🏛️",
        "lv": 58,
        "min_players": 3,
        "max_players": 4,
        "desc": "银月林海深处的失落王城，远古精灵王的安息之所。月光照不进坍塌的穹顶，只有亡灵精灵的吟唱。(主线第 7 章)",
        "boss": ["b_dawn_elf", "远古精灵王·晨曦", "boss", 66,
                 ["ms_yue_guang_zhan", "ms_zhao_huan_shu_ren", "ms_zhi_yu"],
                 ["晨曦之冠"]],
                "stages":         [
            {
                "name": "残垣入口",
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
                    ]
                ]
            },
            {
                "name": "神殿走廊",
                "monsters": [],
                "elite": [
                    "e_ancient_golem",
                    "远古魔像",
                    "elite",
                    62,
                    [
                        "ms_ying_hua",
                        "ms_zhen_ji"
                    ],
                    [
                        "魔像核心"
                    ]
                ]
            },
            {
                "name": "精灵王座",
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
                ]
            }
        ],
        "key_item": "精灵遗印",
        "key_source": "翡翠森林精英·森林长老掉落",
"mech": "heal,shield",
        "hp_mult": 2.7,
        "atk_mult": 1.25,
        "gold": 900,
        "exp": 1200,
        "materials": ["晨曦之冠"],
        "mat_count": 3,
        "blueprint": True,
    },
    "inst_ash_temple": {
        "name": "烬山祭坛",
        "icon": "🌋",
        "lv": 82,
        "min_players": 3,
        "max_players": 4,
        "desc": "烬山之巅的古老祭坛，三百年前圣战的主战场。恶魔祭司·赫尔加在此主持黑暗仪式，试图解开蚀夜的封印。(主线第 9 章)",
        "boss": ["b_helga", "恶魔祭司·赫尔加", "boss", 92,
                 ["ms_an_ying_dan", "ms_zhao_huan_e_mo", "ms_hei_an_yi_shi"],
                 ["赫尔加的祭器"]],
                "stages":         [
            {
                "name": "祭坛外围",
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
                    ]
                ]
            },
            {
                "name": "火焰回廊",
                "monsters": [],
                "elite": [
                    "e_seal_guard",
                    "封印守卫(腐蚀)",
                    "elite",
                    86,
                    [
                        "ms_an_ying",
                        "ms_xu_kong"
                    ],
                    [
                        "烬核"
                    ]
                ]
            },
            {
                "name": "封印之殿",
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
                ]
            }
        ],
        "key_item": "烬火令",
        "key_source": "烬山精英·炎魔掉落",
"mech": "summon,phase",
        "hp_mult": 2.8,
        "atk_mult": 1.3,
        "gold": 1800,
        "exp": 2400,
        "materials": ["赫尔加的祭器"],
        "mat_count": 4,
        "blueprint": True,
    },
    "inst_abyss_gate": {
        "name": "深渊裂隙",
        "icon": "🌑",
        "lv": 90,
        "min_players": 4,
        "max_players": 4,
        "desc": "封印的尽头，深渊裂隙的裂口。被误认为魔王的守护者蚀夜，在这里镇守了三百年——你终于要直面真相。(主线第 12 章·最终决战)",
        "boss": ["b_eter", "蚀夜(真相形态)", "boss", 100,
                 ["ms_an_ying_zhan", "ms_shen_yuan_zhi_nu", "ms_zhao_huan_shen_yuan"],
                 ["黎明之光碎片"]],
                "stages":         [
            {
                "name": "裂隙入口",
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
                    ]
                ]
            },
            {
                "name": "深渊长廊",
                "monsters": [
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
                    ]
                ],
                "elite": [
                    "e_abyss_knight",
                    "深渊骑士",
                    "elite",
                    92,
                    [
                        "ms_an_ying",
                        "ms_xu_kong"
                    ],
                    [
                        "深渊珍珠"
                    ]
                ]
            },
            {
                "name": "蚀夜之巢",
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
                ]
            }
        ],
        "key_item": "深渊钥匙",
        "key_source": "深渊骑士掉落",
"mech": "phase,phase,phase",
        "hp_mult": 3.0,
        "atk_mult": 1.35,
        "gold": 3000,
        "exp": 4000,
        "materials": ["黎明之光碎片"],
        "mat_count": 5,
        "blueprint": True,
    },
    "inst_dragon_tomb": {
        "name": "龙之墓",
        "icon": "🐉",
        "lv": 90,
        "min_players": 4,
        "max_players": 4,
        "desc": "龙骨山脉深处的巨龙墓地，古龙·奥姆之影在此守望龙族传承。龙语回荡——只有真正的勇士才配带走它。(主线第 10 章)",
        "boss": ["b_om_shadow", "古龙·奥姆之影", "boss", 100,
                 ["ms_long_xi", "ms_long_zhao", "ms_gu_long_wei_ya"],
                 ["龙语传承"]],
                "stages":         [
            {
                "name": "龙墓入口",
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
                        92,
                        [
                            "ms_long_xi",
                            "ms_long_wei_190",
                            "ms_wei_ya"
                        ],
                        [
                            "古龙鳞"
                        ]
                    ]
                ]
            },
            {
                "name": "骨堆甬道",
                "monsters": [],
                "elite": [
                    "e_dragon_soul",
                    "龙魂",
                    "elite",
                    95,
                    [
                        "ms_long_xi",
                        "ms_zhao_huan"
                    ],
                    [
                        "龙魂碎片"
                    ]
                ]
            },
            {
                "name": "龙眠大殿",
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
                ]
            }
        ],
        "key_item": "龙牙信物",
        "key_source": "龙脊山脉精英·石龙掉落",
"mech": "reflect,heal",
        "hp_mult": 3.0,
        "atk_mult": 1.35,
        "gold": 3000,
        "exp": 4000,
        "materials": ["龙语传承"],
        "mat_count": 5,
        "blueprint": True,
    },
    # ================= 区域支线 5（可单人） =================
    "inst_deer_fort": {
        "name": "鹿角要塞",
        "icon": "🛡️",
        "lv": 18,
        "min_players": 1,
        "max_players": 1,
        "desc": "白鹿城北的废弃要塞，百年前毁于战火。要塞幽灵仍在城墙上游荡，寻找着失落的军旗。(支线)",
        "boss": ["b_fort_ghost", "要塞幽灵", "boss", 24,
                 ["ms_ai_hao", "ms_chuan_shen", "ms_zhao_huan_ku_lou"],
                 ["要塞残片"]],
        "stages": [
            {
                "name": "破败城门",
                "monsters": [
                    ["m_fort_guard", "要塞守卫", "dps", 18, ["ms_lian_zhan"], ["要塞残片"]],
                    ["m_fort_guard", "要塞守卫", "dps", 18, ["ms_lian_zhan"], ["要塞残片"]],
                ],
                "elite": None,
                "boss": None,
            },
            {
                "name": "战火庭院",
                "monsters": [
                    ["m_fort_archer", "要塞弓手", "speedster", 20, ["ms_jian_ji"], ["要塞残片"]],
                ],
                "elite": ["e_fort_ghost", "要塞幽灵护卫", "elite", 22, ["ms_you_ling"], ["要塞残片"]],
                "boss": None,
            },
            {
                "name": "主厅",
                "monsters": [],
                "elite": None,
                "boss": ["b_fort_ghost", "要塞幽灵", "boss", 24,
                         ["ms_ai_hao", "ms_chuan_shen", "ms_zhao_huan_ku_lou"],
                         ["要塞残片"]],
            },
        ],
                "key_item": "军旗碎片",
        "key_source": "鹿角要塞地图探索掉落",
"mech": "enrage,summon",
        "hp_mult": 1.6,
        "atk_mult": 1.0,
        "gold": 160,
        "exp": 240,
        "materials": ["要塞残片"],
        "mat_count": 1,
        "blueprint": False,
    },
    "inst_holy_trial": {
        "name": "圣光试炼场",
        "icon": "⚜️",
        "lv": 36,
        "min_players": 1,
        "max_players": 1,
        "desc": "圣光骑士团的试炼之地。试炼骑士长把守最后一关——通过者将获得骑士团的认可。(支线)",
        "boss": ["b_trial_knight", "试炼骑士长", "boss", 46,
                 ["ms_sheng_guang_dan", "ms_jian_ji", "ms_zhao_huan"],
                 ["试炼徽记"]],
        "stages": [
            {
                "name": "试炼之门",
                "monsters": [
                    ["m_trial_squire", "试炼侍从", "dps", 36, ["ms_lian_zhan"], ["试炼徽记"]],
                    ["m_trial_squire", "试炼侍从", "dps", 36, ["ms_lian_zhan"], ["试炼徽记"]],
                ],
                "elite": None,
                "boss": None,
            },
            {
                "name": "骑士回廊",
                "monsters": [
                    ["m_trial_knight2", "试炼骑士", "dps", 40, ["ms_dun_ji", "ms_sheng_guang_dan"], ["试炼徽记"]],
                ],
                "elite": ["e_trial_champion", "试炼冠军", "elite", 43, ["ms_sheng_guang_dan", "ms_lian_zhan"], ["试炼徽记"]],
                "boss": None,
            },
            {
                "name": "圣光试炼场",
                "monsters": [],
                "elite": None,
                "boss": ["b_trial_knight", "试炼骑士长", "boss", 46,
                         ["ms_sheng_guang_dan", "ms_jian_ji", "ms_zhao_huan"],
                         ["试炼徽记"]],
            },
        ],
                "key_item": "试炼令",
        "key_source": "铁盾镇兵营任务奖励",
"mech": "shield,enrage",
        "hp_mult": 1.7,
        "atk_mult": 1.05,
        "gold": 350,
        "exp": 480,
        "materials": ["试炼徽记"],
        "mat_count": 2,
        "blueprint": False,
    },
    "inst_moon_temple": {
        "name": "月神圣殿",
        "icon": "🌙",
        "lv": 60,
        "min_players": 1,
        "max_players": 1,
        "desc": "月冠王庭深处的月神神殿，月光从穹顶倾泻而下。月神守卫守护着月之试炼——只有月神认可者才能进入。(支线)",
        "boss": ["b_moon_guard", "月神守卫", "boss", 68,
                 ["ms_yue_guang_zhan", "ms_zhi_yu", "ms_zhao_huan"],
                 ["月辉碎片"]],
        "stages": [
            {
                "name": "月门",
                "monsters": [
                    ["m_moon_priest", "月神侍僧", "dps", 60, ["ms_yue_guang_zhan"], ["月辉碎片"]],
                    ["m_moon_priest", "月神侍僧", "dps", 60, ["ms_yue_guang_zhan"], ["月辉碎片"]],
                ],
                "elite": None,
                "boss": None,
            },
            {
                "name": "月光回廊",
                "monsters": [
                    ["m_moon_knight", "月骑士", "dps", 64, ["ms_dun_ji", "ms_yue_guang_zhan"], ["月辉碎片"]],
                ],
                "elite": ["e_moon_elite", "月光猎手", "elite", 66, ["ms_yue_guang_zhan", "ms_jian_ji"], ["月辉碎片"]],
                "boss": None,
            },
            {
                "name": "月神圣殿",
                "monsters": [],
                "elite": None,
                "boss": ["b_moon_guard", "月神守卫", "boss", 68,
                         ["ms_yue_guang_zhan", "ms_zhi_yu", "ms_zhao_huan"],
                         ["月辉碎片"]],
            },
        ],
                "key_item": "月辉钥匙",
        "key_source": "月冠王庭月市购买(3000 金)",
"mech": "shield,phase",
        "hp_mult": 1.7,
        "atk_mult": 1.05,
        "gold": 950,
        "exp": 1300,
        "materials": ["月辉碎片"],
        "mat_count": 2,
        "blueprint": False,
    },
    "inst_frost_throne": {
        "name": "冰霜王座",
        "icon": "❄️",
        "lv": 74,
        "min_players": 2,
        "max_players": 3,
        "desc": "永冻冰原深处的寒冰王座，冰霜领主在此称王。它冻结了三百年的时光，也在等待一个挑战者。(支线)",
        "boss": ["b_frost_lord", "冰霜领主", "boss", 84,
                 ["ms_bing_xi", "ms_dong_jie", "ms_zhao_huan"],
                 ["永冻之核"]],
        "stages": [
            {
                "name": "冰封入口",
                "monsters": [
                    ["m_frost_guard", "寒冰守卫", "dps", 74, ["ms_bing_xi"], ["永冻之核"]],
                    ["m_frost_guard", "寒冰守卫", "dps", 74, ["ms_bing_xi"], ["永冻之核"]],
                ],
                "elite": None,
                "boss": None,
            },
            {
                "name": "寒冰回廊",
                "monsters": [
                    ["m_frost_mage", "冰霜法师", "speedster", 78, ["ms_bing_xi", "ms_dong_jie"], ["永冻之核"]],
                ],
                "elite": ["e_frost_elite", "冰霜巨人", "elite", 81, ["ms_bing_xi", "ms_dun_ji"], ["永冻之核"]],
                "boss": None,
            },
            {
                "name": "冰霜王座",
                "monsters": [],
                "elite": None,
                "boss": ["b_frost_lord", "冰霜领主", "boss", 84,
                         ["ms_bing_xi", "ms_dong_jie", "ms_zhao_huan"],
                         ["永冻之核"]],
            },
        ],
                "key_item": "寒冰令",
        "key_source": "永冻冰原精英·冰原巨兽掉落",
"mech": "stacks,enrage",
        "hp_mult": 2.4,
        "atk_mult": 1.2,
        "gold": 1500,
        "exp": 2000,
        "materials": ["永冻之核"],
        "mat_count": 3,
        "blueprint": True,
    },
    "inst_storm_throne": {
        "name": "风暴王座",
        "icon": "🌩️",
        "lv": 90,
        "min_players": 3,
        "max_players": 4,
        "desc": "龙脊山脉之巅的风暴王座，风暴龙王统御着雷云。雷霆为冠，狂风为座——能坐上去的，只有风暴本身。(支线)",
        "boss": ["b_storm_king", "风暴龙王", "boss", 98,
                 ["ms_lei_bao", "ms_feng_bao_zhi_yan", "ms_zhao_huan_lei_niao"],
                 ["风暴之核"]],
        "stages": [
            {
                "name": "风暴之门",
                "monsters": [
                    ["m_storm_guard", "雷暴守卫", "dps", 90, ["ms_lei_bao"], ["风暴之核"]],
                    ["m_storm_guard", "雷暴守卫", "dps", 90, ["ms_lei_bao"], ["风暴之核"]],
                ],
                "elite": None,
                "boss": None,
            },
            {
                "name": "雷霆回廊",
                "monsters": [
                    ["m_storm_priest", "风暴祭司", "speedster", 94, ["ms_lei_bao", "ms_feng_bao_zhi_yan"], ["风暴之核"]],
                ],
                "elite": ["e_storm_elite2", "雷霆巨人", "elite", 96, ["ms_lei_bao", "ms_dun_ji"], ["风暴之核"]],
                "boss": None,
            },
            {
                "name": "风暴王座",
                "monsters": [],
                "elite": None,
                "boss": ["b_storm_king", "风暴龙王", "boss", 98,
                         ["ms_lei_bao", "ms_feng_bao_zhi_yan", "ms_zhao_huan_lei_niao"],
                         ["风暴之核"]],
            },
        ],
                "key_item": "雷光令",
        "key_source": "风暴崖精英·雷鸟掉落",
"mech": "phase,phase",
        "hp_mult": 2.7,
        "atk_mult": 1.3,
        "gold": 2600,
        "exp": 3500,
        "materials": ["风暴之核"],
        "mat_count": 4,
        "blueprint": True,
    },
    # ================= 外域 6（翡翠海/无尽海/地底） =================
    "inst_sunken_ship": {
        "name": "沉船湾",
        "icon": "⚓",
        "lv": 38,
        "min_players": 1,
        "max_players": 1,
        "desc": "翡翠海深处的沉船墓地，幽灵船长·克罗的旗舰在此永沉。传说船底的宝箱装着它的罗盘——还有它不甘的灵魂。(群岛支线)",
        "boss": ["b_ghost_captain", "幽灵船长·克罗", "boss", 48,
                 ["ms_wan_dao", "ms_zhao_huan_you_ling", "ms_zu_zhou"],
                 ["克罗的罗盘"]],
                "stages":         [
            {
                "name": "甲板",
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
                    ]
                ]
            },
            {
                "name": "船舱",
                "monsters": [],
                "elite": [
                    "e_ghost_captain",
                    "幽灵大副",
                    "elite",
                    42,
                    [
                        "ms_you_ling",
                        "ms_wan_dao"
                    ],
                    [
                        "幽灵船票"
                    ]
                ]
            },
            {
                "name": "船长室",
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
                ]
            }
        ],
        "key_item": "幽灵船票",
        "key_source": "铁港码头精英·海盗精锐掉落",
"mech": "summon,heal",
        "hp_mult": 1.8,
        "atk_mult": 1.1,
        "gold": 450,
        "exp": 600,
        "materials": ["克罗的罗盘"],
        "mat_count": 2,
        "blueprint": False,
    },
    "inst_siren_nest": {
        "name": "海妖巢穴",
        "icon": "🧜‍♀️",
        "lv": 52,
        "min_players": 2,
        "max_players": 3,
        "desc": "海妖湾下的珊瑚巢穴，海妖女王·蓝歌的领地。她的歌声能魅惑水手，也能掀起巨浪——别被歌声骗进深海。(群岛支线)",
        "boss": ["b_siren_queen", "海妖女王·蓝歌", "boss", 60,
                 ["ms_mei_huo_zhi_ge", "ms_ju_lang", "ms_zhao_huan_chu_shou"],
                 ["蓝歌之冠"]],
                "stages":         [
            {
                "name": "海藻洞",
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
                    ]
                ]
            },
            {
                "name": "珊瑚回廊",
                "monsters": [],
                "elite": [
                    "e_siren_guard",
                    "海妖守卫",
                    "elite",
                    55,
                    [
                        "ms_hai_yao",
                        "ms_du_ya"
                    ],
                    [
                        "海妖鳞片"
                    ]
                ]
            },
            {
                "name": "海妖巢穴",
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
                ]
            }
        ],
        "key_item": "海妖鳞片信物",
        "key_source": "海妖湾精英·海妖守卫掉落",
"mech": "phase,heal",
        "hp_mult": 2.2,
        "atk_mult": 1.15,
        "gold": 700,
        "exp": 950,
        "materials": ["蓝歌之冠"],
        "mat_count": 2,
        "blueprint": True,
    },
    "inst_sea_god_temple": {
        "name": "海神神殿",
        "icon": "🌊",
        "lv": 64,
        "min_players": 3,
        "max_players": 4,
        "desc": "无尽海底的海神神殿，海神祭司·澜歌守护着海神的圣物。潮汐在此倒流——海神的目光，正注视着入侵者。(无尽海支线)",
        "boss": ["b_lange", "海神祭司·澜歌", "boss", 72,
                 ["ms_hai_chao", "ms_zhao_huan_sha_yu", "ms_jing_hua_zhi_chao"],
                 ["澜歌之泪"]],
                "stages":         [
            {
                "name": "神殿入口",
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
                    ]
                ]
            },
            {
                "name": "潮汐回廊",
                "monsters": [
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
                    ]
                ],
                "elite": [
                    "e_sea_priest",
                    "海神护卫",
                    "elite",
                    68,
                    [
                        "ms_hai_yao",
                        "ms_sheng_guang"
                    ],
                    [
                        "潮汐之泪"
                    ]
                ]
            },
            {
                "name": "海神祭坛",
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
                ]
            }
        ],
        "key_item": "海神祷文",
        "key_source": "无名港灯塔任务奖励",
"mech": "shield,phase",
        "hp_mult": 2.5,
        "atk_mult": 1.2,
        "gold": 1100,
        "exp": 1500,
        "materials": ["澜歌之泪"],
        "mat_count": 3,
        "blueprint": True,
    },
    "inst_deep_dragon_palace": {
        "name": "深海龙宫",
        "icon": "🐲",
        "lv": 70,
        "min_players": 4,
        "max_players": 4,
        "desc": "无尽海最深处的水晶龙宫，深海龙王·敖澜在此沉睡。它一翻身，海面就要掀起风暴——别吵醒它太久。(无尽海支线)",
        "boss": ["b_aolan", "深海龙王·敖澜", "boss", 78,
                 ["ms_shui_xi", "ms_long_wei", "ms_zhao_huan_hai_shou"],
                 ["敖澜之珠"]],
                "stages":         [
            {
                "name": "宫门",
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
                    ]
                ]
            },
            {
                "name": "珊瑚长廊",
                "monsters": [
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
                    ]
                ],
                "elite": [
                    "e_dragon_guard",
                    "龙宫守卫",
                    "elite",
                    74,
                    [
                        "ms_long_xi",
                        "ms_du_ya"
                    ],
                    [
                        "龙宫珠"
                    ]
                ]
            },
            {
                "name": "龙王大殿",
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
                ]
            }
        ],
        "key_item": "龙宫珠",
        "key_source": "龙鲸海域精英·龙鲸掉落",
"mech": "reflect,stacks",
        "hp_mult": 2.7,
        "atk_mult": 1.25,
        "gold": 1400,
        "exp": 1900,
        "materials": ["敖澜之珠"],
        "mat_count": 3,
        "blueprint": True,
    },
    "inst_gray_dwarf": {
        "name": "灰矮人要塞",
        "icon": "⛏️",
        "lv": 74,
        "min_players": 2,
        "max_players": 3,
        "desc": "幽暗地域深处的灰矮人要塞，灰矮人领主·石炉统治着这片地底。它的锻造炉昼夜不息，烧的是地底恶魔的骨头。(地底支线)",
        "boss": ["b_gray_lord", "灰矮人领主·石炉", "boss", 84,
                 ["ms_zhan_chui", "ms_zhao_huan_gong_cheng_shou"],
                 ["石炉之锤"]],
                "stages":         [
            {
                "name": "要塞入口",
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
                    ]
                ]
            },
            {
                "name": "兵工厂",
                "monsters": [],
                "elite": [
                    "e_dwarf_guard",
                    "灰矮人守卫",
                    "elite",
                    78,
                    [
                        "ms_dun_ji",
                        "ms_kuang_bao"
                    ],
                    [
                        "灰矮人徽记"
                    ]
                ]
            },
            {
                "name": "领主大厅",
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
                ]
            }
        ],
        "key_item": "灰矮人通行令",
        "key_source": "地底集市矿工区任务奖励",
"mech": "shield,stacks",
        "hp_mult": 2.4,
        "atk_mult": 1.2,
        "gold": 1500,
        "exp": 2000,
        "materials": ["石炉之锤"],
        "mat_count": 3,
        "blueprint": True,
    },
    "inst_under_dragon": {
        "name": "地底龙巢",
        "icon": "🐍",
        "lv": 84,
        "min_players": 4,
        "max_players": 4,
        "desc": "熔火深渊之下的地底龙巢，地底古龙·黑渊盘踞于此。它吞食地底岩浆与恶魔，是幽暗地域最古老的掠食者。(地底支线)",
        "boss": ["b_under_dragon", "地底古龙·黑渊", "boss", 92,
                 ["ms_suan_xi", "ms_tun_shi", "ms_zhao_huan_you_long"],
                 ["黑渊之眼"]],
                "stages":         [
            {
                "name": "巢穴入口",
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
                    ]
                ]
            },
            {
                "name": "龙骸甬道",
                "monsters": [],
                "elite": [
                    "e_deep_dragon",
                    "地底幼龙",
                    "elite",
                    88,
                    [
                        "ms_long_xi",
                        "ms_an_ying"
                    ],
                    [
                        "地底龙鳞"
                    ]
                ]
            },
            {
                "name": "地底龙巢",
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
                ]
            }
        ],
        "key_item": "龙鳞钥匙",
        "key_source": "熔火深渊精英·地底恶魔掉落",
"mech": "reflect,enrage",
        "hp_mult": 2.8,
        "atk_mult": 1.3,
        "gold": 1900,
        "exp": 2500,
        "materials": ["黑渊之眼"],
        "mat_count": 4,
        "blueprint": True,
    },
    # ================= 扩展 3（天空/地底终极） =================
    "inst_eye_of_storm": {
        "name": "风暴之眼",
        "icon": "🌀",
        "lv": 92,
        "min_players": 4,
        "max_players": 4,
        "desc": "雷暴高原的风暴之眼，风暴之主·云怒在此执掌雷霆。雷云之上是天空的尽头——也是风暴的故乡。(天空支线)",
        "boss": ["b_storm_master", "风暴之主·云怒", "boss", 100,
                 ["ms_lei_bao", "ms_feng_bao_zhi_yan", "ms_zhao_huan_lei_niao"],
                 ["云怒之核"]],
                "stages":         [
            {
                "name": "云巅之门",
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
                    ]
                ]
            },
            {
                "name": "风暴回廊",
                "monsters": [],
                "elite": [
                    "e_storm_elite",
                    "风暴元素",
                    "elite",
                    96,
                    [
                        "ms_feng_bao",
                        "ms_lei_ji"
                    ],
                    [
                        "风暴之核"
                    ]
                ]
            },
            {
                "name": "风暴之眼",
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
                ]
            }
        ],
        "key_item": "雷核钥匙",
        "key_source": "雷暴高原精英·雷元素掉落",
"mech": "phase,phase",
        "hp_mult": 2.9,
        "atk_mult": 1.32,
        "gold": 2800,
        "exp": 3700,
        "materials": ["云怒之核"],
        "mat_count": 4,
        "blueprint": True,
    },
    "inst_abyss_throne": {
        "name": "深渊王座",
        "icon": "👹",
        "lv": 90,
        "min_players": 4,
        "max_players": 4,
        "desc": "深渊祭坛最深处的王座，深渊领主·摩罗凝视着一切。地底恶魔的军团在此列队——它们等这一天，等了不止三百年。(地底支线)",
        "boss": ["b_moro", "深渊领主·摩罗", "boss", 98,
                 ["ms_shen_yuan_zhi_nu", "ms_zhao_huan_e_mo", "ms_fu_shi_ling_yu"],
                 ["摩罗之冠"]],
                "stages":         [
            {
                "name": "深渊入口",
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
                    ]
                ]
            },
            {
                "name": "魔像走廊",
                "monsters": [],
                "elite": [
                    "e_abyss_elite",
                    "深渊魔像",
                    "elite",
                    94,
                    [
                        "ms_an_ying",
                        "ms_xu_kong"
                    ],
                    [
                        "魔像核心"
                    ]
                ]
            },
            {
                "name": "深渊王座",
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
                ]
            }
        ],
        "key_item": "深渊圣印",
        "key_source": "深渊祭坛精英·深渊魔像掉落",
"mech": "stacks,summon",
        "hp_mult": 3.0,
        "atk_mult": 1.35,
        "gold": 2900,
        "exp": 3800,
        "materials": ["摩罗之冠"],
        "mat_count": 4,
        "blueprint": True,
    },
    "inst_cloud_sanctum": {
        "name": "云中圣殿",
        "icon": "☁️",
        "lv": 94,
        "min_players": 4,
        "max_players": 4,
        "desc": "风翼群岛之巅的云中圣殿，云中圣者·奥拉守护着天空的传承。圣光与风暴在此交织——最后的试炼，留给最强的冒险者。(天空支线)",
        "boss": ["b_ola", "云中圣者·奥拉", "boss", 100,
                 ["ms_sheng_guang", "ms_feng_bao", "ms_zhao_huan_yun_wei"],
                 ["奥拉圣印"]],
                "stages":         [
            {
                "name": "云门",
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
                    ]
                ]
            },
            {
                "name": "圣殿回廊",
                "monsters": [],
                "elite": [
                    "e_cloud_guard",
                    "云中守卫",
                    "elite",
                    96,
                    [
                        "ms_sheng_guang",
                        "ms_feng_bao"
                    ],
                    [
                        "云怒之核"
                    ]
                ]
            },
            {
                "name": "云中圣殿",
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
                ]
            }
        ],
        "key_item": "云玺",
        "key_source": "星辉台精英·星龙掉落",
"mech": "shield,phase",
        "hp_mult": 3.0,
        "atk_mult": 1.35,
        "gold": 3200,
        "exp": 4200,
        "materials": ["奥拉圣印"],
        "mat_count": 5,
        "blueprint": True,
    },
}
