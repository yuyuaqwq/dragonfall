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

v173 问题C：通关奖励数值模型化（此前 22 本 gold/exp 手填无模型，量化怪相：
  通关金=同级野外 Boss 怪金模型 14-39%、通关 exp=升级所需 5-10%）。
  公式（economy_lib.instance_reward，scripts/economy_lib/core.py）：
    gold = monster_gold(inst_lv, 'boss') × 0.30   # 通关 = 约 1/3 只同级野外 Boss 怪金
    exp  = monster_exp(inst_lv, 'boss')  × 2.8    # 通关 ≈ 升级所需 4-24%（前期高后期低，随成长曲线自然回落）
  以下各本 gold/exp = 按公式标定的生成值（含战利品堆 30% / 调查点等消费端自动跟随）。
  数值门禁 tests/test_numeric_instance_reward.py 断言全本落在模型带内、跨级比单调。
"""
INSTANCES = {
    # ================= 主线 8（多人/进阶） =================
    "inst_goblin_camp": {
        "entry": {"map": "misty_swamp", "subarea": "misty_swamp_3"},
        "name": "哥布林营地",
        "icon": "👺",
        "lv": 15,
        "min_players": 1,
        "max_players": 2,  # v101.24：1-2 人（鱼鱼拍板，双人小队可一起打）
        "desc": "商路旁的哥布林聚落，哥布林酋长·咕噜盘踞于此，靠抢劫商队为生。冒险者行会悬赏讨伐。(主线第 2 章)",
        "intro": "商路旁的营地还冒着劫掠后的烟，翻倒的货车旁散落着没来得及搬走的货物。行会的悬赏令在怀里发烫——今晚，该让哥布林酋长·咕噜尝尝被讨伐的滋味了。",
        "boss_line": "『金币！宝石！都是咕噜的！』咕噜把抢来的皇冠往头上一扣，咧开满嘴尖牙：『你们这些商队的小跟班，也敢来掀咕噜的帐篷？』",
        "outro": "咕噜的皇冠滚落在篝火边，商路上的劫掠就此画上句号。行会的赏金结清了，可你总觉得，这条商路尽头的风声，才刚刚开始。",
        "boss": ["b_goblin_chief", "哥布林酋长·咕噜", "boss", 20,
                ["ms_lian_zhan", "ms_nu_hou", "ms_zhao_huan"],
                ["咕噜皇冠"]],
        "minions": [{"name": "哥布林打手", "monster": ["m_goblin_guard", "哥布林守卫", "tank", 15,
                           ["ms_dun_ji"], ["哥布林铁片"]], "count": 2}],  # v163：爪牙=同图小怪模板（鱼鱼拍板，非 Boss 缩放）
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
                        "咕噜皇冠"
                    ]
                ]
            }
        ],
"mech": "summon,stacks",
        "hp_mult": 4.0,
        "atk_mult": 1.0,
        "gold": 234,
        "exp": 3653,
        "materials": ["咕噜皇冠"],
        "mat_count": 1,
        "blueprint": False,
    },
    "inst_sea_cave": {
        "entry": {"map": "harbor_docks", "subarea": "harbor_docks_3"},
        "name": "海蚀洞窟",
        "icon": "🌊",
        "lv": 22,
        "min_players": 1,  # v155 单刷放开（鱼鱼拍板）：主线 q3_3，单人可进
        "max_players": 3,
        "desc": "铁港码头下的海蚀洞穴，海盗王·独眼杰克的老巢。潮水声里混着金币碰撞的脆响。(主线第 3 章)",
        "intro": "铁港码头下的礁石缝隙里，潮声裹着若有若无的金币脆响。独眼杰克的老巢就在洞中暗湾——铁港的船主们，已经很久不敢起锚了。",
        "boss_line": "『老子纵横七海三十年，还没见过敢摸进杰克宝库的耗子！』独眼杰克的金钩在火光里一晃：『留下你们的船，或者留下命！』",
        "outro": "金钩从杰克手中脱落，暗湾里终于只剩下潮水的呼吸。铁港的船主们可以重新起锚了，而你从战利品里翻出的那张旧海图，似乎指向更深的水域。",
        "boss": ["b_jack_pirate", "海盗王·独眼杰克", "boss", 28,
                 ["ms_wan_dao", "ms_huo_qiang", "ms_zhao_huan_shui_gui"],
                 ["杰克的金钩碎片"]],
        "minions": [{"name": "海盗喽啰", "monster": ["m_sea_slime", "海史莱姆", "tank", 22,
                           ["ms_zhuang_ji", "ms_nian_ye"], ["海盐结晶"]], "count": 2}],  # v163：爪牙=同图小怪模板（鱼鱼拍板，非 Boss 缩放）
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
                        "杰克的金钩碎片"
                    ]
                ]
            }
        ],
"mech": "phase",
        "hp_mult": 2.4,  # v155 单刷档（原 3.6 多人标定）
        "atk_mult": 1.0,  # v155 单刷档（原 1.15）
        "gold": 385,
        "exp": 6465,
        "materials": ["杰克的金钩碎片"],
        "mat_count": 2,
        "blueprint": True,
        "装备": ["影袭之刃"],
    },
    "inst_old_king_tomb": {
        "entry": {"map": "king_road", "subarea": "king_road_3"},
        "name": "旧王陵",
        "icon": "🦴",
        "lv": 35,
        "min_players": 1,  # v155 单刷放开（鱼鱼拍板）：主线 q6_2，单人可进
        "max_players": 3,
        "desc": "晨曦城北的古老王陵，埋葬着圣战前的历代君王。古王·奥德里克在棺椁中苏醒，亡灵的低语回荡在石壁之间。(主线第 6 章)",
        "intro": "陵门在王陵钥匙的转动下缓缓开启，积尘的石壁后传来低沉的亡灵呓语。圣战前的历代君王长眠于此，而其中一位——古王·奥德里克——已经不再安眠。",
        "boss_line": "『孤在位时，圣战尚未燃起。』奥德里克拄剑起身，王座厅的烛火齐齐亮起：『来者报上名来，让孤看看三百年后的晨曦城，还记不记得忠骨。』",
        "outro": "古王的剑重归尘土，王陵重归寂静。奥德里克消散前望向北方的那一眼，让你想起他未说完的话——圣战的真相，似乎比棺椁里的陪葬品埋得更深。",
        "boss": ["b_king_odric", "古王·奥德里克", "boss", 45,
                 ["ms_jian_ji", "ms_wang_wei", "ms_zhao_huan_ku_lou"],
                 ["古王剑碎片"]],
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
                        "古王剑碎片"
                    ]
                ]
            }
        ],
        "key_item": "王陵钥匙",
        "key_source": "白鹿城铁匠铺购买(500 金)",
"mech": "enrage,summon",
        "hp_mult": 2.9,  # v155 单刷档（保持原 1.5，本就是单刷档量级）
        "atk_mult": 1.0,  # v155 单刷档（原 1.2）
        "gold": 709,
        "exp": 12835,
        "materials": ["古王剑碎片"],
        "mat_count": 2,
        "blueprint": True,
    },
    "inst_secret_crypt": {
        "entry": {"map": "dawn_cathedral", "subarea": "dawn_cathedral_3"},
        "name": "圣堂地窖",
        "icon": "⛪",
        "lv": 42,
        "min_players": 3,
        "max_players": 4,
        "desc": "晨曦大圣堂下的密室，教会最深的秘密沉睡于此。审判长·马尔库斯奉命看守——他的锁链，从不问对错。(主线第 11 章)",
        "intro": "地窖的烛火只够照亮三步以内的路，墙上的壁画被白布遮得严严实实。教会最深的秘密就在回廊尽头，而看守它的锁链声，已经在你前方响起。",
        "boss_line": "『奉命看守此门者，不问门后是什么，只问来者为何。』马尔库斯的锁链在手中绷直：『审判长·马尔库斯在此——退去，或领受审判。』",
        "outro": "马尔库斯的法冠滚落在地，锁链垂到他脚边，不再作响。你掀开一角白布，壁画上的图案让所有人沉默——教会掩埋的阴影，比这间地窖更深、更古老。",
        "boss": ["b_marcus", "审判长·马尔库斯", "boss", 52,
                 ["ms_an_ying_dan", "ms_suo_lian", "ms_shen_pan_zhi_yan"],
                 ["马尔库斯的法冠残片"]],
                "stages":         [
            {
                "name": "地窖回廊",
                "monsters": [
                    [
                        "m_shadow_priest",
                        "血祭祭司",
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
                        "马尔库斯的法冠残片"
                    ]
                ]
            }
        ],
        "key_item": "圣堂信物",
        "key_source": "晨曦城大教堂购买(300 金)",
"mech": "shield,enrage",
        "hp_mult": 5.4,
        "atk_mult": 1.25,
        "gold": 890,
        "exp": 16489,
        "materials": ["马尔库斯的法冠残片"],
        "mat_count": 3,
        "blueprint": True,
    },
    "inst_elven_ruins": {
        "entry": {"map": "moon_court", "subarea": "moon_court_gate"},
        "name": "精灵废墟",
        "icon": "🏛️",
        "lv": 58,
        "min_players": 1,  # v155 单刷放开（鱼鱼拍板）：主线 q7_4 探索，单人可进
        "max_players": 4,
        "desc": "银月林海深处的失落王城，远古精灵王的安息之所。月光照不进坍塌的穹顶，只有亡灵精灵的吟唱。(主线第 7 章)",
        "intro": "坍塌的穹顶漏不进半点月光，银月林海的夜风却在断柱间呜咽，像谁在唱一首没唱完的歌。这座月神眷顾过的失落王城，如今只剩亡灵精灵的吟唱，引你走向王座。",
        "boss_line": "『月神弃我们而去的那一夜，这座城就死了。』晨曦从王座上起身，冠冕下的目光像月光一样冷：『可死去的王，也还记得如何守土。』",
        "outro": "晨曦之冠落回王座，废墟中的吟唱终于停歇。你抬头看见穹顶的裂缝里漏进一线月光——月神或许从未离开，只是等了太久。",
        "boss": ["b_dawn_elf", "远古精灵王·晨曦", "boss", 66,
                 ["ms_yue_guang_zhan", "ms_zhao_huan_shu_ren", "ms_zhi_yu"],
                 ["晨曦之冠碎片"]],
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
                        "晨曦之冠碎片"
                    ]
                ]
            }
        ],
        "key_item": "精灵遗印",
        "key_source": "翡翠森林精英·狼王·灰影掉落",
"mech": "heal,shield",
        "hp_mult": 3.3,  # v155 单刷档（原 3.1 多人标定）
        "atk_mult": 1.0,  # v155 单刷档（原 1.25）
        "gold": 1347,
        "exp": 26098,
        "materials": ["晨曦之冠碎片"],
        "mat_count": 3,
        "blueprint": True,
    },
    "inst_ash_temple": {
        "entry": {"map": "cinder_mountain", "subarea": "cinder_mountain_3"},
        "name": "烬山祭坛",
        "icon": "🌋",
        "lv": 82,
        "min_players": 1,  # v155 单刷放开（鱼鱼拍板）：主线 q9_3/q9_4/q10_3，单人可进
        "max_players": 4,
        "desc": "烬山之巅的古老祭坛，三百年前圣战的主战场。恶魔祭司·赫尔加在此主持黑暗仪式，试图解开蚀夜的封印。(主线第 9 章)",
        "intro": "烬山之巅的焦土下，还埋着三百年前圣战的断剑。祭坛上的黑焰正在成形，恶魔祭司·赫尔加的低吟顺着风传来——她手中的仪式，正撼动着那道古老的封印。",
        "boss_line": "『三百年前，你们的英雄王在这里流尽了血。』赫尔加抚过祭坛上的刻痕，声音里带着虔诚的狂热：『今夜，我要把那份封印，连本带利地讨回来。』",
        "outro": "祭器碎裂，黑焰熄灭，烬山第一次安静得只剩下风声。你站在英雄王当年战斗过的地方，忽然明白那道封印守护着什么——而北方裂隙的低语，似乎又近了一些。",
        "boss": ["b_helga", "恶魔祭司·赫尔加", "boss", 92,
                 ["ms_an_ying_dan", "ms_zhao_huan_e_mo", "ms_hei_an_yi_shi"],
                 ["赫尔加的祭器碎片"]],
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
                        "赫尔加的祭器碎片"
                    ]
                ]
            }
        ],
        "key_item": "烬火令",
        "key_source": "烬山精英·恶魔战士掉落",
"mech": "summon,phase",
        "hp_mult": 2.2,  # v155 单刷档（原 3.2 多人标定）
        "atk_mult": 1.05,  # v155 单刷档（原 1.3）
        "gold": 2064,
        "exp": 41521,
        "materials": ["赫尔加的祭器碎片"],
        "mat_count": 4,
        "blueprint": True,
    },
    "inst_abyss_gate": {
        "entry": {"map": "ash_temple", "subarea": "ash_temple_1"},
        "name": "深渊裂隙",
        "icon": "🌑",
        "lv": 90,
        "min_players": 1,  # v155 单刷放开（鱼鱼拍板）：主线 q12_2/q12_3，单人可进
        "max_players": 4,
        "desc": "封印的尽头，深渊裂隙的裂口。被误认为魔王的守护者蚀夜，在这里镇守了三百年——你终于要直面真相。(主线第 12 章·最终决战)",
        "intro": "裂隙的裂口横亘在天地之间，像一道三百年未曾愈合的伤。那个被唤作魔王的身影仍守在封印之核旁——这一次，你不是来讨伐他，而是来听他说完真相。",
        "boss_line": "『……你来了。』蚀夜抬起头，封印的光在他身上明灭：『裂痕在扩大，我已撑了三百年。若这真是最后一战，就让我看看，人类是否已准备好接过守夜。』",
        "outro": "封印之核重归平静，裂隙的轰鸣缓缓止息，守夜者终于可以歇一歇了。黎明之光碎片在你掌心里微微发烫，仿佛在说——下一个守夜人，已经站在这里。",
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
        # v116.1 剧本化示范：三阶段换招（追加技能）/演出文案/阈值预告（可选字段，不配置则旧行为）
        "phases": [
            {"min": 60, "add_skills": ["ms_zhao_huan_shen_yuan"],
             "script": {"name": "深渊裂隙张开", "icon": "🌑"}},
            {"min": 30, "add_skills": ["ms_shen_yuan_zhi_nu"],
             "script": {"name": "深渊之怒倾泻", "icon": "💀"}},
        ],
        "hp_mult": 1.2,  # v155 单刷档（原 2.8 多人标定）
        "atk_mult": 1.05,  # v155 单刷档（原 1.35）
        "gold": 2319,
        "exp": 47154,
        "materials": ["黎明之光碎片"],
        "mat_count": 5,
        "blueprint": True,
    },
    "inst_dragon_tomb": {
        "entry": {"map": "dragon_roost", "subarea": "dragon_roost_3"},
        "name": "龙之墓",
        "icon": "🐉",
        "lv": 90,
        "min_players": 4,
        "max_players": 4,
        "desc": "龙骨山脉深处的巨龙墓地，古龙·奥姆之影在此守望龙族传承。龙语回荡——只有真正的勇士才配带走它。(主线第 10 章)",
        "intro": "龙骨山脉深处，巨大的龙骨横陈如一片白色森林。古龙·奥姆之影盘踞在传承之核上方，龙语的低吟穿过骨骸间的风——它在等一个配得上这份传承的人。",
        "boss_line": "『凡人，你的脚步惊醒了沉睡的龙骨。』奥姆之影缓缓睁眼，龙语如雷：『龙族的传承只托付给勇士——证明给吾看，你的心配得上这份重量。』",
        "outro": "龙语传承落入你手中，骨骸间的风忽然变得温柔，像一声长长的叹息。奥姆之影最后望了你一眼，缓缓沉入墓穴深处——古龙的守望结束了，而你的路才刚刚开始。",
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
        "key_source": "龙脊山脉·石龙掉落",
"mech": "reflect,heal",
        "hp_mult": 2.5,
        "atk_mult": 1.35,
        "gold": 2319,
        "exp": 47154,
        "materials": ["龙语传承"],
        "mat_count": 5,
        "blueprint": True,
    },
    # ================= 区域支线 5（可单人） =================
    "inst_deer_fort": {
        "entry": {"map": "hill_mine", "subarea": "hill_mine_3"},
        "name": "鹿角要塞",
        "icon": "🛡️",
        "lv": 18,
        "min_players": 1,
        "max_players": 1,
        "desc": "白鹿城北的废弃要塞，百年前毁于战火。要塞幽灵仍在城墙上游荡，寻找着失落的军旗。(支线)",
        "intro": "白鹿城的号角在风中呜咽，北境防线最前沿的要塞已沉寂百年。踏过焦黑的城门，城墙上游荡的幽灵仍在列队巡行，仿佛战火从未熄灭。找回那面失落的军旗，让要塞的英魂得以安息。",
        "boss_line": "军旗……那面军旗在哪里？没有它，我该如何向死去的弟兄们复命！",
        "outro": "军旗碎片在月光下拼合成完整的旗帜，要塞幽灵单膝跪地，向旗帜行了一个百年未竟的军礼。晨光穿透破败的穹顶，英魂化作点点微光消散——北境的防线，终于有人替他们守住了。",
        "boss": ["b_fort_ghost", "要塞幽灵", "boss", 24,
                 ["ms_ai_hao", "ms_chuan_shen", "ms_zhao_huan_ku_lou"],
                 ["要塞残片"]],
        "stages": [
            {
                "name": "破败城门",
                "monsters": [
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
        # v110 审计修复：key_item 回退材料名（v110.11 消歧误改为消耗品名——材料
        # items.py:1565 desc 明示"可作钥匙进入鹿角要塞"，采集池 ancient/old_battlefield
        # 产 mat_jun_qi_sui_pian；改后入口按名校验与背包材料匹配，钥匙链恢复）
        "key_source": "古战场/旧战场遗迹采集",
"mech": "enrage,summon",
        "hp_mult": 3.8,
        "atk_mult": 1.0,
        "gold": 295,
        "exp": 4779,
        "materials": ["要塞残片"],
        "mat_count": 1,
        "blueprint": False,
        "装备": ["晨光法杖", "曙光权杖"],
    },
    "inst_holy_trial": {
        "entry": {"map": "king_road", "subarea": "king_road_2"},
        "name": "圣光试炼场",
        "icon": "⚜️",
        "lv": 36,
        "min_players": 1,
        "max_players": 1,
        "desc": "圣光骑士团的试炼之地。试炼骑士长把守最后一关——通过者将获得骑士团的认可。(支线)",
        "intro": "铁盾镇的钟声敲响三下，圣光骑士团的试炼之门缓缓开启。每一道回廊都刻着历代骑士的誓言，而通往认可的路只有一条。持试炼令而入者，须以剑与信念，走到骑士长面前。",
        "boss_line": "举起你的剑，挑战者！圣光不认可软弱的祈祷——让骑士团看看，你配不配这枚徽记。",
        "outro": "试炼骑士长收剑入鞘，将圣光徽记郑重地别在你胸前：「从今日起，你便是骑士团认可的战士。」回廊尽头，晨光如剑，劈开长夜。",
        "boss": ["b_trial_knight", "试炼骑士长", "boss", 46,
                 ["ms_sheng_guang_dan", "ms_jian_ji", "ms_zhao_huan"],
                 ["试炼徽记"]],
        "stages": [
            {
                "name": "试炼之门",
                "monsters": [
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
        "key_source": "铁盾镇军械铺购买(400 金)",
"mech": "shield,enrage",
        "hp_mult": 4.0,
        "atk_mult": 1.05,
        "gold": 734,
        "exp": 13333,
        "materials": ["试炼徽记"],
        "mat_count": 2,
        "blueprint": False,
    },
    "inst_moon_temple": {
        "entry": {"map": "moon_glade", "subarea": "moon_glade_3"},
        "name": "月神圣殿",
        "icon": "🌙",
        "lv": 60,
        "min_players": 1,
        "max_players": 1,
        "desc": "月冠王庭深处的月神神殿，月光从穹顶倾泻而下。月神守卫守护着月之试炼——只有月神认可者才能进入。(支线)",
        "intro": "月冠王庭的夜色最深处，月光如银瀑自穹顶倾泻，照出神殿千年的轮廓。月神守卫静立月门之前，银甲上流转着不灭的月华。唯有被月神认可之人，才能穿过这片月光，抵达试炼的核心。",
        "boss_line": "月神的目光从未离开过你，凡世之人。若你的心与剑同样皎洁，便穿过我的银甲；若否，就留在月光之下。",
        "outro": "月神守卫的身形在月华中渐渐淡去，只留下一声低语：「月神已记住你的名字。」穹顶的月光第一次为你铺成道路，掌心的月辉碎片微微发烫，如同回应。",
        "boss": ["b_moon_guard", "月神守卫", "boss", 68,
                 ["ms_yue_guang_zhan", "ms_zhi_yu", "ms_zhao_huan"],
                 ["月辉碎片"]],
        "stages": [
            {
                "name": "月门",
                "monsters": [
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
        "key_source": "月冠王庭购买(3000 金)",
"mech": "shield,phase",
        "hp_mult": 3.5,
        "atk_mult": 1.05,
        "gold": 1409,
        "exp": 27417,
        "materials": ["月辉碎片"],
        "mat_count": 2,
        "blueprint": False,
    },
    "inst_frost_throne": {
        "entry": {"map": "winter_lake", "subarea": "winter_lake_3"},
        "name": "冰霜王座",
        "icon": "❄️",
        "lv": 74,
        "min_players": 2,
        "max_players": 3,
        "desc": "永冻冰原深处的寒冰王座，冰霜领主在此称王。它冻结了三百年的时光，也在等待一个挑战者。(支线)",
        "intro": "永冻冰原的寒风如刀，割开皮肉与呼吸，冰霜王座就矗立在风暴尽头。三百年间，无数挑战者被冻成王座前的冰雕，成为领主沉默的陈列。你带着寒冰令而来——是成为下一座冰雕，还是让王座解冻？",
        "boss_line": "三百年了……我的冰封国度终于等来一个敢踏上王座的活人。来吧，让我看看你的热血，能在我的寒冬里撑过几息。",
        "outro": "冰霜领主连同王座一同碎裂，化作漫天冰尘，被北风卷向天际。永冻冰原的暴雪第一次停歇，阳光落上三百年未见天日的冻土。你呵出的白气里，春天正从裂缝中苏醒。",
        "boss": ["b_frost_lord", "冰霜领主", "boss", 84,
                 ["ms_bing_xi", "ms_dong_jie", "ms_zhao_huan"],
                 ["永冻之核"]],
        "stages": [
            {
                "name": "冰封入口",
                "monsters": [
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
        "key_source": "永冻冰原精英·冰原猛犸·雪岭掉落",
"mech": "stacks,enrage",
        "hp_mult": 3.1,
        "atk_mult": 1.2,
        "gold": 1818,
        "exp": 36153,
        "materials": ["永冻之核"],
        "mat_count": 3,
        "blueprint": True,
    },
    "inst_storm_throne": {
        "entry": {"map": "storm_cliff", "subarea": "storm_cliff_3"},
        "name": "风暴王座",
        "icon": "🌩️",
        "lv": 90,
        "min_players": 3,
        "max_players": 4,
        "desc": "龙脊山脉之巅的风暴王座，雷霆君主统御着雷云。雷霆为冠，狂风为座——能坐上去的，只有风暴本身。(支线)",
        "intro": "龙脊山脉之巅，雷云终年不散，风暴王座藏于雷鸣的最深处。雷霆为冠、狂风为座的君主俯瞰着风暴群岛，拒绝一切凡俗的觐见。握紧雷光令，踏上雷霆回廊——风暴只臣服于敢于直面的勇者。",
        "boss_line": "雷霆为我加冕，狂风为我铺座——凡人之躯，也敢觊觎风暴的王座？那就让雷云见证你的成色！",
        "outro": "雷霆君主的身躯化作最后一道闪电，劈开漫天雷云。风暴群岛的天气第一次放晴，阳光穿透云层，洒在王座残骸之上。你接过风暴之核，群山之巅的风，第一次为你而安静。",
        "boss": ["b_storm_king", "雷霆君主", "boss", 98,
                 ["ms_lei_bao", "ms_feng_bao_zhi_yan", "ms_zhao_huan_lei_niao"],
                 ["风暴之核"]],
        "stages": [
            {
                "name": "风暴之门",
                "monsters": [
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
                "boss": ["b_storm_king", "雷霆君主", "boss", 98,
                         ["ms_lei_bao", "ms_feng_bao_zhi_yan", "ms_zhao_huan_lei_niao"],
                         ["风暴之核"]],
            },
        ],
                "key_item": "雷光令",
        "key_source": "风暴崖精英·风暴崖主·雷鸣掉落",
"mech": "phase,phase",
        "hp_mult": 3.1,
        "atk_mult": 1.3,
        "gold": 2319,
        "exp": 47154,
        "materials": ["风暴之核"],
        "mat_count": 4,
        "blueprint": True,
        "装备": ["大贤者圣衣"],
    },
    # ================= 外域 6（翡翠海/无尽海/地底） =================
    "inst_sunken_ship": {
        "entry": {"map": "storm_strait", "subarea": "storm_strait_3"},
        "name": "沉船湾",
        "icon": "⚓",
        "lv": 38,
        "min_players": 1,
        "max_players": 1,
        "desc": "翡翠海深处的沉船墓地，幽灵船长·克罗的旗舰在此永沉。传说船底的宝箱装着它的罗盘——还有它不甘的灵魂。(群岛支线)",
        "intro": "翡翠海深处，断裂的桅杆如墓碑般立在幽绿的水光里。沉船湾的每一块甲板都浸着旧日的航线——幽灵船长·克罗的旗舰，已在这里等了很久。",
        "boss_line": "「活人的气息……把我的罗盘还回来，那是我唯一记得的归途。」",
        "outro": "罗盘在你掌心轻轻转动，指向一座早已沉没的旧港。克罗的残魂随潮水远去，沉船湾的迷雾第一次散开，露出通往海面的光。",
        "boss": ["b_ghost_captain", "幽灵船长·克罗", "boss", 48,
                 ["ms_wan_dao", "ms_zhao_huan_you_ling", "ms_zu_zhou"],
                 ["克罗的罗盘碎片"]],
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
                        "克罗的罗盘碎片"
                    ]
                ]
            }
        ],
        "key_item": "幽灵船票",
        # v110 审计修复：key_item 回退材料名（v110.11 消歧误改为消耗品名——采集池
        # shipwreck_graveyard 产 mat_you_ling_chuan_piao，材料 desc 明示"可作钥匙进入沉船湾"）
        "key_source": "沉船湾墓地采集",
"mech": "summon,heal",
        "hp_mult": 4.0,
        "atk_mult": 1.1,
        "gold": 785,
        "exp": 14358,
        "materials": ["克罗的罗盘碎片"],
        "mat_count": 2,
        "blueprint": False,
    },
    "inst_siren_nest": {
        "entry": {"map": "mermaid_bay", "subarea": "mermaid_bay_3"},
        "name": "海妖巢穴",
        "icon": "🧜‍♀️",
        "lv": 52,
        "min_players": 2,
        "max_players": 3,
        "desc": "海妖湾下的珊瑚巢穴，海妖女王·蓝歌的领地。她的歌声能魅惑水手，也能掀起巨浪——别被歌声骗进深海。(群岛支线)",
        "intro": "珊瑚丛深处传来若有若无的歌声，像月光落在水面上。海妖女王·蓝歌坐在珍珠王座间，用歌声为迷途的水手编织归乡的幻梦——也编织他们的葬身之处。",
        "boss_line": "「留下来吧，旅人——我的歌里，有你想回的家。」",
        "outro": "蓝歌的歌声戛然而止，巢穴恢复了海底本来的寂静。那些被歌声骗来的灵魂挣脱幻梦，化作点点荧光，随洋流游向海面。",
        "boss": ["b_siren_queen", "海妖女王·蓝歌", "boss", 60,
                 ["ms_mei_huo_zhi_ge", "ms_ju_lang", "ms_zhao_huan_chu_shou"],
                 ["蓝歌之冠残片"]],
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
                        "蓝歌之冠残片"
                    ]
                ]
            }
        ],
        "key_item": "海妖鳞片信物",
        "key_source": "海妖湾精英·海妖领主·潮汐掉落",
"mech": "phase,heal",
        "hp_mult": 4.4,
        "atk_mult": 1.15,
        "gold": 1169,
        "exp": 22296,
        "materials": ["蓝歌之冠残片"],
        "mat_count": 2,
        "blueprint": True,
    },
    "inst_sea_god_temple": {
        "entry": {"map": "storm_sea", "subarea": "storm_sea_3"},
        "name": "海神神殿",
        "icon": "🌊",
        "lv": 64,
        "min_players": 3,
        "max_players": 4,
        "desc": "无尽海底的海神神殿，海神祭司·澜歌守护着海神的圣物。潮汐在此倒流——海神的目光，正注视着入侵者。(无尽海支线)",
        "intro": "海神神殿的廊柱间，潮汐违背常理地向上倒流，仿佛整座大海都在朝圣。海神祭司·澜歌立于祭坛前，圣物的光辉映着她平静而决绝的眼眸。",
        "boss_line": "「海神正注视着你，凡人——跪下，或者被潮水带走。」",
        "outro": "祭坛上的圣物重归沉寂，倒流的潮水缓缓落回海底。澜歌的身影化作一缕水光消散，神殿深处传来海神古老的叹息，像是认可，又像是告别。",
        "boss": ["b_lange", "海神祭司·澜歌", "boss", 72,
                 ["ms_hai_chao", "ms_zhao_huan_sha_yu", "ms_jing_hua_zhi_chao"],
                 ["澜歌之泪残片"]],
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
                        "澜歌之泪残片"
                    ]
                ]
            }
        ],
        "key_item": "海神祷文",
        # v110 审计修复：key_item 回退材料名（v110.11 消歧误改为消耗品名）
        "key_source": "无名港港务厅购买",
"mech": "shield,phase",
        "hp_mult": 4.3,
        "atk_mult": 1.2,
        "gold": 1523,
        "exp": 29825,
        "materials": ["澜歌之泪残片"],
        "mat_count": 3,
        "blueprint": True,
    },
    "inst_deep_dragon_palace": {
        "entry": {"map": "storm_sea", "subarea": "storm_sea_2"},
        "name": "深海龙宫",
        "icon": "🐲",
        "lv": 70,
        "min_players": 4,
        "max_players": 4,
        "desc": "无尽海最深处的水晶龙宫，深海龙王·敖澜在此沉睡。它一翻身，海面就要掀起风暴——别吵醒它太久。(无尽海支线)",
        "intro": "水晶宫墙在深海的黑暗中泛着冷光，沉睡的龙王每一声呼吸都让珊瑚海轻轻震颤。深海龙王·敖澜睁开一只眼，金色的竖瞳里映出闯入者的倒影。",
        "boss_line": "「是谁吵醒了万年的沉眠？龙宫的规矩，要用水晶来偿。」",
        "outro": "敖澜重新阖上双眼，龙宫的潮水恢复了亘古的平稳。你带着敖澜之珠离去时，整座水晶宫亮起送别的微光——龙王记住了你的名字。",
        "boss": ["b_aolan", "深海龙王·敖澜", "boss", 78,
                 ["ms_shui_xi", "ms_long_wei", "ms_zhao_huan_hai_shou"],
                 ["敖澜之珠碎片"]],
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
                        "敖澜之珠碎片"
                    ]
                ]
            }
        ],
        "key_item": "龙宫珠",
        # v110 审计修复：key_item 回退材料名（v110.11 消歧误改为消耗品名）
        # F3 P1-1 修复：掉落源补全——龙鲸海域精英·龙鲸王·涛声掉落（原仅副本内掉落=死锁）
        "key_source": "龙鲸海域精英·龙鲸王·涛声掉落",
"mech": "reflect,stacks",
        "hp_mult": 4.4,
        "atk_mult": 1.25,
        "gold": 1698,
        "exp": 33569,
        "materials": ["敖澜之珠碎片"],
        "mat_count": 3,
        "blueprint": True,
    },
    "inst_gray_dwarf": {
        "entry": {"map": "deep_lake", "subarea": "deep_lake_3"},
        "name": "灰矮人要塞",
        "icon": "⛏️",
        "lv": 74,
        "min_players": 2,
        "max_players": 3,
        "desc": "幽暗地域深处的灰矮人要塞，灰矮人领主·石炉统治着这片地底。它的锻造炉昼夜不息，烧的是地底恶魔的骨头。(地底支线)",
        "intro": "幽暗地域的岩壁之间，铁砧的轰鸣昼夜不息，震得整座要塞嗡嗡作响。灰矮人领主·石炉抡起巨锤，火星溅落处，恶魔的骨头正被锻成崭新的甲片。",
        "boss_line": "「地底只认锤子说话的规矩——你的骨头，够硬吗？」",
        "outro": "石炉的巨锤终于垂下，要塞的炉火黯淡了几分。他盯着你的背影哼了一声，转身继续锻打——仿佛这场战斗，只是漫长锤音里的一段插曲。",
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
        "key_source": "地底集市购买(2800 金)",
"mech": "shield,stacks",
        "hp_mult": 3.1,
        "atk_mult": 1.2,
        "gold": 1818,
        "exp": 36153,
        "materials": ["石炉之锤"],
        "mat_count": 3,
        "blueprint": True,
        "装备": ["疾风挽歌"],
    },
    "inst_under_dragon": {
        "entry": {"map": "molten_abyss", "subarea": "molten_abyss_3"},
        "name": "地底龙巢",
        "icon": "🐍",
        "lv": 84,
        "min_players": 4,
        "max_players": 4,
        "desc": "熔火深渊之下的地底龙巢，地底古龙·黑渊盘踞于此。它吞食地底岩浆与恶魔，是幽暗地域最古老的掠食者。(地底支线)",
        "intro": "熔火深渊的光从地缝中涌上来，照亮龙巢里堆积如山的白骨。地底古龙·黑渊盘踞在岩浆湖中央，古老的竖瞳缓缓睁开——它已经很久没有闻到活物的气味了。",
        "boss_line": "「幽暗地域最古老的掠食者，不挑食。」",
        "outro": "黑渊的咆哮在岩壁间回荡许久才平息，岩浆湖重归暗红。它沉入湖底前看了你一眼，那目光仿佛在说：地底记住了你的味道。",
        "boss": ["b_under_dragon", "地底古龙·黑渊", "boss", 92,
                 ["ms_suan_xi", "ms_tun_shi", "ms_zhao_huan_you_long"],
                 ["黑渊之眼残片"]],
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
                        "黑渊之眼残片"
                    ]
                ]
            }
        ],
        "key_item": "龙鳞钥匙",
        "key_source": "熔火深渊精英·熔火领主·烬核掉落",
"mech": "reflect,enrage",
        "hp_mult": 3.7,
        "atk_mult": 1.3,
        "gold": 2127,
        "exp": 42904,
        "materials": ["黑渊之眼残片"],
        "mat_count": 4,
        "blueprint": True,
        "装备": ["云端护腿"],
    },
    # ================= 扩展 3（天空/地底终极） =================
    "inst_eye_of_storm": {
        "entry": {"map": "storm_plateau", "subarea": "storm_plateau_3"},
        "name": "风暴之眼",
        "icon": "🌀",
        "lv": 92,
        "min_players": 4,
        "max_players": 4,
        "desc": "雷暴高原的风暴之眼，风暴之主·云怒在此执掌雷霆。雷云之上是天空的尽头——也是风暴的故乡。(天空支线)",
        "intro": "雷暴高原的风眼异象百年一现：万道雷霆倒悬天穹，汇聚成一只凝视大地的巨瞳。穿过云巅之门与风暴回廊，元素军团在狂风中列阵——天空的尽头，正为来客缓缓睁开。",
        "boss_line": "风暴之主·云怒立于雷云之巅，号令万雷齐鸣：『竟敢踏入天空的尽头？就让风暴，为你们送葬！』",
        "outro": "雷云散尽，风眼归于沉寂，天空的尽头重归湛蓝。云怒之核落入掌心，那是苍穹赐予胜者的徽记——从今往后，风暴也记住了你们的名字。",
        "boss": ["b_storm_master", "风暴之主·云怒", "boss", 100,
                 ["ms_lei_bao", "ms_feng_bao_zhi_yan", "ms_zhao_huan_lei_niao"],
                 ["云怒之核碎片"]],
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
                        "云怒之核碎片"
                    ]
                ]
            }
        ],
        "key_item": "雷核钥匙",
        "key_source": "雷暴高原·雷元素掉落",
"mech": "phase,phase",
        "hp_mult": 6.3,
        "atk_mult": 1.32,
        "gold": 2384,
        "exp": 48602,
        "materials": ["云怒之核碎片"],
        "mat_count": 4,
        "blueprint": True,
    },
    "inst_abyss_throne": {
        "entry": {"map": "abyss_altar", "subarea": "abyss_altar_3"},
        "name": "深渊王座",
        "icon": "👹",
        "lv": 90,
        "min_players": 4,
        "max_players": 4,
        "desc": "深渊祭坛最深处的王座，深渊领主·摩罗凝视着一切。地底恶魔的军团在此列队——它们等这一天，等了不止三百年。(地底支线)",
        "intro": "深渊祭坛的最深处，王座静候了三百年。恶魔军团在黑暗中列队低吼，火把映出摩罗的冠冕——地底世界的主人，早已等得不耐烦了。踏入深渊入口的那一刻，你们便再无退路。",
        "boss_line": "深渊领主·摩罗自王座上起身，狱火般的目光扫过众人：『三百年了，终于有人敢来献上头颅！』",
        "outro": "摩罗之冠坠地，深渊军团如潮水般退去，王座上的阴影就此消散。三百年的恩怨，在这一战中画上句点——而勇者的名字，将被刻入祭坛的碑文，永镇深渊。",
        "boss": ["b_moro", "深渊领主·摩罗", "boss", 98,
                 ["ms_shen_yuan_zhi_nu", "ms_zhao_huan_e_mo", "ms_fu_shi_ling_yu"],
                 ["摩罗之冠碎片"]],
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
                        "摩罗之冠碎片"
                    ]
                ]
            }
        ],
        "key_item": "深渊圣印",
        "key_source": "深渊祭坛精英·祭坛守卫·魔眼掉落",
"mech": "stacks,summon",
        "hp_mult": 2.8,
        "atk_mult": 1.35,
        "gold": 2319,
        "exp": 47154,
        "materials": ["摩罗之冠碎片"],
        "mat_count": 4,
        "blueprint": True,
    },
    "inst_cloud_sanctum": {
        "entry": {"map": "rainbow_cloud", "subarea": "rainbow_cloud_3"},
        "name": "云中圣殿",
        "icon": "☁️",
        "lv": 94,
        "min_players": 4,
        "max_players": 4,
        "desc": "风翼群岛之巅的云中圣殿，云中圣者·奥拉守护着天空的传承。圣光与风暴在此交织——最后的试炼，留给最强的冒险者。(天空支线)",
        "intro": "风翼群岛之巅，云中圣殿在圣光中若隐若现——天空的传承封存于此，静候最后的试炼。穿过云门与圣殿回廊，圣光与风暴在廊柱间交织，每一级阶梯都通向云端之上。能走到殿心的，唯有最强的冒险者。",
        "boss_line": "云中圣者·奥拉张开圣光之翼，声音响彻云端：『传承只授予配得上天空之人——证明你们的勇气吧！』",
        "outro": "圣光敛去，奥拉将天空的传承交付于胜者之手，云中圣殿重归安详。风翼群岛的传说翻开新的一页，云端之上，圣印的微光将永远为勇者长明。",
        "boss": ["b_ola", "云中圣者·奥拉", "boss", 100,
                 ["ms_sheng_guang", "ms_feng_bao", "ms_zhao_huan_yun_wei"],
                 ["奥拉圣印碎片"]],
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
                        "云怒之核碎片"
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
                        "奥拉圣印碎片"
                    ]
                ]
            }
        ],
        "key_item": "云玺",
        "key_source": "星辉台精英·星龙掉落",
"mech": "shield,phase",
        "hp_mult": 6.4,
        "atk_mult": 1.35,
        "gold": 2451,
        "exp": 50069,
        "materials": ["奥拉圣印碎片"],
        "mat_count": 5,
        "blueprint": True,
    },
}

# ================= v168 副本 Boss 装备掉落池表（22 条，由 v140 单件表升级） =================
# 2026-09-03 掉落池化（鱼鱼拍板：主题装出现频率 > 主专属，专属保持稀有惊喜感）。
# 来源：v140 波1 原 game/data/drop_add_v140.py 之 BOSS_EQUIP_DROP（2026-08-30 孤儿文件表并入本文件；
# 本表纯数据、无逻辑，供掉落逻辑 drops.py/instance.py 消费）。
# 结构：{副本id: {
#   "boss_equip": 主专属装备 rid（Boss 身份物，稀有，首杀向惊喜），
#   "boss_rate":  主专属掉率（0.05-0.12，保留 v140 原 rate 值），
#   "pool":       [主题装 rid...]（同等级段主题装池，常见），
#   "pool_rate":  主题装池整体出装率（0.35，命中后从 pool 内等权随机 1 件），
#   "pity":       v140 保底击杀数（保留字段；仍指主专属保底，向前兼容）}}
# 注：eq_* 拼音 id（西幻命名）；旧单件键 equip/rate 已并入 boss_equip/boss_rate（读取方以新键为准）。
INSTANCE_BOSS_EQUIP_DROP = {
    "inst_goblin_camp":     {"boss_equip": "eq_gu_lu_de_huang_guan", "boss_rate": 0.05, "pool": ["eq_gu_lu_jin_jie", "eq_gu_lu_jun_dao", "eq_gu_lu_zhan_hui"], "pool_rate": 0.35, "pity": 20},
    "inst_sea_cave":        {"boss_equip": "eq_jin_gou_wan_dao", "boss_rate": 0.08, "pool": ["eq_jin_bi_dai", "eq_xiu_mao_hu_shou"], "pool_rate": 0.35, "pity": 15},
    "inst_sea_god_temple":  {"boss_equip": "eq_ying_xi_zhi_ren", "boss_rate": 0.1, "pool": ["eq_nu_tao_san_cha_ji", "eq_ying_xi_zhi_ren"], "pool_rate": 0.35, "pity": 12},
    "inst_old_king_tomb":   {"boss_equip": "eq_gu_wang_jian", "boss_rate": 0.08, "pool": ["eq_wang_du_shi_yue_zhi_jian", "eq_jing_ji_zhan_jia"], "pool_rate": 0.35, "pity": 15},
    "inst_secret_crypt":    {"boss_equip": "eq_ma_er_ku_si_de_fa_guan", "boss_rate": 0.1, "pool": ["eq_shi_xiang_gui_jing_jia", "eq_wang_zhe_zhan_xue", "eq_shi_xiang_gui_zhi_xin"], "pool_rate": 0.35, "pity": 12},
    "inst_elven_ruins":     {"boss_equip": "eq_chen_xi_zhi_guan", "boss_rate": 0.1, "pool": ["eq_chen_xi_sheng_jian", "eq_shu_guang_bi_lei"], "pool_rate": 0.35, "pity": 12},
    "inst_ash_temple":      {"boss_equip": "eq_he_er_jia_de_ji_qi", "boss_rate": 0.1, "pool": ["eq_hui_jin_chang_jian", "eq_hui_jin_kai_jia", "eq_hui_jin_zhi_kui", "eq_hui_jin_zhi_dun", "eq_hui_jin_hu_tui", "eq_hui_jin_zhan_xue"], "pool_rate": 0.35, "pity": 12},
    "inst_abyss_gate":      {"boss_equip": "eq_shi_ye_zhi_mian", "boss_rate": 0.1, "pool": ["eq_si_wang_zhi_wu", "eq_mu_guang_zhi_ci", "eq_da_xian_zhe_fa_guan", "eq_da_xian_zhe_sheng_yi"], "pool_rate": 0.35, "pity": 12},
    "inst_dragon_tomb":     {"boss_equip": "eq_long_yu_sheng_jian", "boss_rate": 0.1, "pool": ["eq_long_ji_lin_jia", "eq_cang_qiong_zhi_guan", "eq_zhu_feng_pi_jia_92"], "pool_rate": 0.35, "pity": 12},
    "inst_deer_fort":       {"boss_equip": "eq_yao_sai_you_ling_zhi_kui", "boss_rate": 0.08, "pool": ["eq_you_ling_jun_qi", "eq_qi_shi_can_jia", "eq_yao_sai_shi_zhang"], "pool_rate": 0.35, "pity": 15},
    "inst_storm_throne":    {"boss_equip": "eq_feng_bao_zhi_guan", "boss_rate": 0.1, "pool": ["eq_ben_lei_da_jian", "eq_da_xian_zhe_sheng_yi"], "pool_rate": 0.35, "pity": 12},
    "inst_holy_trial":      {"boss_equip": "eq_shi_lian_hui_zhang", "boss_rate": 0.08, "pool": ["eq_shen_pan_zhi_lian"], "pool_rate": 0.35, "pity": 15},
    "inst_moon_temple":     {"boss_equip": "eq_yue_hui_zhi_jie", "boss_rate": 0.08, "pool": ["eq_han_shuang_zhi_guan", "eq_lan_dun_zhi_jie"], "pool_rate": 0.35, "pity": 15},
    "inst_frost_throne":    {"boss_equip": "eq_yong_dong_zhi_xin", "boss_rate": 0.1, "pool": ["eq_bing_mai_hu_tui", "eq_sheng_dian_zhan_xue", "eq_shuang_lang_zhi_wang_ya", "eq_ying_xi_zhi_ren"], "pool_rate": 0.35, "pity": 12},
    "inst_sunken_ship":     {"boss_equip": "eq_ke_luo_de_luo_pan", "boss_rate": 0.1, "pool": ["eq_shi_guang_sha_lou"], "pool_rate": 0.35, "pity": 12},
    "inst_siren_nest":      {"boss_equip": "eq_lan_ge_zhi_guan", "boss_rate": 0.1, "pool": ["eq_shu_zui_sheng_zhang", "eq_xing_yun_chang_gong"], "pool_rate": 0.35, "pity": 12},
    "inst_deep_dragon_palace": {"boss_equip": "eq_ao_lan_zhi_zhu", "boss_rate": 0.1, "pool": ["eq_zhen_hai_zhi_dun", "eq_lie_feng_zhang_gong"], "pool_rate": 0.35, "pity": 12},
    "inst_gray_dwarf":      {"boss_equip": "eq_ji_feng_wan_ge", "boss_rate": 0.1, "pool": ["eq_pan_shi_wang_guan", "eq_lei_wen_quan_jia", "eq_ji_feng_wan_ge"], "pool_rate": 0.35, "pity": 12},
    "inst_under_dragon":    {"boss_equip": "eq_hei_yuan_zhi_yan", "boss_rate": 0.1, "pool": ["eq_shen_yuan_xiong_jia", "eq_yan_mie_fa_dian_fa_zhang"], "pool_rate": 0.35, "pity": 12},
    "inst_eye_of_storm":    {"boss_equip": "eq_yun_nu_zhi_he", "boss_rate": 0.12, "pool": ["eq_shi_zhi_ling_zhu_shi_jie", "eq_shi_zhi_ling_zhu_mi_yi"], "pool_rate": 0.35, "pity": 12},
    "inst_cloud_sanctum":   {"boss_equip": "eq_sheng_yu_quan_zhang", "boss_rate": 0.1, "pool": ["eq_da_xian_zhe_mi_dian", "eq_tai_tan_hu_tui", "eq_xu_kong_xing_zhe_zhi_xue", "eq_sheng_hui_xiong_jia", "eq_bu_mie_yi_zhi", "eq_xing_hui_zhi_guan", "eq_sheng_yu_quan_zhang"], "pool_rate": 0.35, "pity": 12},
    "inst_abyss_throne":    {"boss_equip": "eq_sui_xing_quan_tao", "boss_rate": 0.1, "pool": ["eq_yuan_su_shi_tu_zhi_guan", "eq_yuan_su_shi_tu_chang_pao", "eq_yuan_su_shi_tu_fa_zhang", "eq_yuan_su_shi_tu_zhui_shi", "eq_sui_xing_quan_tao", "eq_an_xing_quan_tao"], "pool_rate": 0.35, "pity": 12},
}
