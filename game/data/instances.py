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

v173 问题D：副本 Boss 血量难度重标（2026-09-04 鱼鱼拍板 60-80 轮目标）：
  此前 hp_mult 手填乱（哥布林 4.0 vs 海蚀 2.4 导致 15/22 级本血量几乎一样；
  多人本过速 30-50 轮、单人本拖 100+ 轮）。本次按【标准打法人装备档】重标：
    - 单人本（min=1）按 solo 装备档（蓝+5/升级档）单刷 60-80 轮
    - 多人本按对应阶段 team 档（team_mid/team_purple9/team_orange9）满编 60-80 轮
    - 终局本（龙墓/深渊王座/云中圣殿等）按橙+9 毕业装标定（鱼鱼：高本要求高配）
  单人本 atk_mult 同步下调（×0.9）让单刷承伤可过。
  校准：scripts/numeric_lib/team.py team_matrix（每本按其档位全量扫）；门禁 test_numeric_team_comp。
  注：不同阶段玩家装备不同（32 章 P2 蓝+5 / P3 紫 / P4 橙 / P5 橙+9满），
  副本难度按阶段装备标，不是全本统一蓝装。

v173.1 副本 Boss 攻击重标（2026-09-04 鱼鱼拍板：平砍统一 12-15% 坦克 HP，牧师高压）：
  此前副本 Boss 被排除在野外 BOSS_ATK_STAGE_MULT 外（v156 怕打崩 4 人队），后期玩家
  装备 HP 涨 ~11 倍、Boss atk 只涨 ~3 倍 → 平砍仅 2-4% 坦克 HP，牧师失业。本次治本：
    - 新增段乘区 INSTANCE_BOSS_ATK_STAGE_MULT（stat_templates.py，monster_stats 对
      area=instance 的 boss 生效）：≤15 ×1.0 → 25 级 ×2.3 → 60 级 ×4.2 → 95 级 ~×4.9
    - 本文件 atk_mult 全 22 本迭代校准（0.86-1.61）：统一按 4 人标准坦克 HP 12-15% 平砍。
      单刷本 solo 装被秒 = 设计意图（Boss 攻击不因单刷而降，逼玩家组队）
    - 治疗预期 = Boss 战牧师全职奶（numeric_lib HEAL_CAST_SHARE 0.5→1.0 + heal 输出 0）；
      击杀轮带纯奶变长（多人本 74-87，鱼鱼接受）；承伤模型分层（坦伤被奶覆盖、后排溅射自扛）
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
        "mech": "enrage,phase_open,player_low,phase,summon,stacks",
        "hp_mult": 2.343,

        "atk_mult": 1.1324,

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
        "boss": ["b_jack_pirate", "海盗王·独眼杰克", "boss", 27,
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
                    27,
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
        "mech": "phase,summon,phase_open",
        "hp_mult": 2.0563,  # v173.3 Boss降级hp补偿 ×1.094
        "atk_mult": 0.908,  # v173.3 Boss降级atk补偿 ×1.057
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
        "boss": ["b_king_odric", "古王·奥德里克", "boss", 40,
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
                    40,
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
        "mech": "phase,summon,enrage",
        "minions": [
        {
            "name": "王冠核心",
            "count": 1,
            "monster": [
                "m_skeleton",
                "骷髅兵",
                "dps",
                35,
                [
                    "ms_jian_ji",
                ],
                [
                    "碎骨",
                ],
            ],
        },
        {
            "name": "骷髅卫兵",
            "count": 0,
            "monster": [
                "m_skeleton",
                "骷髅兵",
                "dps",
                37,
                [
                    "ms_jian_ji",
                ],
                [
                    "碎骨",
                ],
            ],
        },
    ],
        "phases": [
        {
            "min": 60,
            "phase_id": "normal",
            "add_skills": [
                "ms_zhao_ku_lou_mi",
            ],
            "script": {"name": "王冠威临", "icon": "👑", "enter_line": "👑 王冠核心在场：本体受伤减半、召唤加速——先拆冠！"},
            "counter": "💡 先打王冠核心——它的王冠在维持减伤与召唤！",
        },
        {
            "min": 30,
            "phase_id": "enrage",
            "atk_mult": 1.25,
            "add_skills": [
                "ms_wang_zhe_zhi_nu",
                "ms_wang_yu_huan_hun",
            ],
            "script": {"name": "王座之怒", "icon": "⚔️", "warn_line": "王者之怒开始蓄力！读条意图可见——打断或提前防御减半！"},
            "counter": "失冕 5 刻是唯一安心输出窗；窗口结束前清掉骷髅防『亡语唤魂』立即拉回！",
        },
        {
            "min": 0,
            "phase_id": "rampage",
            "atk_mult": 1.3,
            "script": {"name": "亡者终末", "icon": "💀", "warn_line": "狂暴×1.35！30% 以下召唤更密——王冠必须优先处理！"},
            "counter": "末段：失冕窗口 5 刻打桩，破冠永远第一优先级！",
        },
    ],
        "hp_mult": 2.356,  # v173.3 Boss降级hp补偿 ×1.207
        "atk_mult": 1.3861,  # v173.3 Boss降级atk补偿 ×1.193
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
        "boss": ["b_marcus", "审判长·马尔库斯", "boss", 47,
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
                    47,
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
        "mech": "phase,enrage",
        "minions": [
        {
            "name": "审判猎犬",
            "count": 0,
            "monster": [
                "m_inquisitor_hound",
                "审判猎犬",
                "speedster",
                45,
                [
                    "ms_si_yao",
                ],
                [
                    "猎犬项圈",
                ],
            ],
        },
    ],
        "phases": [
        {
            "min": 60,
            "phase_id": "normal",
            "add_skills": [],
            "script": {"name": "预审", "icon": "⚖️", "enter_line": "『奉命看守此门者……退去，或领受审判。』锁链扬起——定罪将至！"},
            "counter": "看到锁链 → 留净化/免控；处刑宣读读条 2 刻——打断技只留给它！",
        },
        {
            "min": 30,
            "phase_id": "enrage",
            "atk_mult": 1.2,
            "freq_mult": 0.85,
            "add_skills": [
                "ms_chi_re_bu_dao",
            ],
            "script": {"name": "狂热公审", "icon": "🔥", "warn_line": "布道开始——自身攻击大幅提升！定罪 6→4 刻，打断资源要省着用！"},
            "counter": "优先清他身上 atk_up（净化/驱散），别硬吃布道后的连招！",
        },
        {
            "min": 0,
            "phase_id": "rampage",
            "atk_mult": 1.3,
            "script": {"name": "末日审判", "icon": "⚖️", "warn_line": "终审姿态：定罪+处刑连招更密！读条=唯一生机，防定罪=少挨一刀！"},
            "counter": "处刑被打断 = 判决流产 1 刻空窗 → 全队爆发；阶段 3 也照此节奏打！",
        },
    ],
        "hp_mult": 12.429,  # v173.3 Boss降级hp补偿 ×1.180

        "atk_mult": 1.3537,  # v173.3 Boss降级atk补偿 ×1.156
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
        "boss": ["b_dawn_elf", "远古精灵王·晨曦", "boss", 63,
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
                    63,
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
        "mech": "phase,summon,heal",
        "minions": [
        {
            "name": "树人",
            "count": 0,
            "monster": [
                "m_ancient_golem",
                "远古魔像",
                "tank",
                62,
                [
                    "ms_zhong_ji",
                    "ms_fu_wen_chong_ji",
                ],
                [
                    "远古符文石",
                ],
            ],
        },
    ],
        "phases": [
        {
            "min": 60,
            "add_skills": [
                "ms_yue_shi_jiang_lin",
            ],
            "phase_id": "normal",
            "script": {"name": "月相轮转·教学", "icon": "🌕", "enter_line": "🌕盈月：它在蓄力——开减伤！🌑新月：树人在回血——清林！🌒月蚀：打断读条！"},
            "counter": "盈月龟缩；新月清林（AOE 断回血+断月蚀增幅）；月蚀读条必断！",
        },
        {
            "min": 30,
            "add_skills": [],
            "phase_id": "enrage",
            "atk_mult": 1.15,
            "script": {"name": "月辉灼烧", "icon": "🌒", "warn_line": "新月召唤提速、月蚀读条更紧——清林节奏跟不上=回血+增幅双压力！"},
            "counter": "树人每只=他每刻回 2%+月蚀 +25%——AOE 一轮清空最赚！",
        },
        {
            "min": 0,
            "phase_id": "rampage",
            "atk_mult": 1.3,
            "script": {"name": "月陨终局", "icon": "💀", "warn_line": "狂暴！月蚀打断窗口只剩第 1 刻——漏一次=3.5× 团伤+一轮回血！"},
            "counter": "末段纪律：清林+断唱双重考验，别被拖进下一轮新月！",
        },
    ],
        "hp_mult": 2.4295,  # v173.3 Boss降级hp补偿 ×1.071
        "atk_mult": 1.2275,  # v173.3 Boss降级atk补偿 ×1.045
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
        "boss": ["b_helga", "恶魔祭司·赫尔加", "boss", 87,
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
                    87,
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
        "mech": "phase,summon",
        "minions": [
        {
            "name": "恶魔",
            "count": 1,
            "monster": [
                "m_demon_priest",
                "恶魔祭司",
                "healer",
                85,
                [
                    "ms_an_ying_dan",
                    "ms_hei_an_zhi_liao",
                ],
                [
                    "染血祭器",
                ],
            ],
        },
    ],
        "phases": [
        {
            "min": 50,
            "add_skills": [
                "ms_hei_an_yi_shi_helga",
                "ms_zhao_huan_e_mo_helga",
            ],
            "phase_id": "normal",
            "script": {"name": "黑暗祭礼", "icon": "🕯️", "enter_line": "🕯️ 恶魔低语环绕祭坛——赫尔加开始诵念黑暗仪式！打断它，别让她吃怪！"},
            "counter": "仪式读条 2 刻必断；恶魔优先清——没饲料她就没法献祭！",
        },
        {
            "min": 30,
            "add_skills": [
                "ms_shen_yuan_zhi_yan",
            ],
            "phase_id": "enrage",
            "atk_mult": 1.15,
            "freq_mult": 0.85,
            "script": {"name": "暴食", "icon": "😈", "warn_line": "恶魔越召越快、仪式越念越急——打断窗口收紧，清怪别停！"},
            "counter": "打断技留给仪式；恶魔死光=断粮真空期，全力爆发！",
        },
        {
            "min": 0,
            "phase_id": "rampage",
            "atk_mult": 1.3,
            "script": {"name": "魔化", "icon": "💀", "warn_line": "魔化！已吃恶魔的永久增伤叠高——控好仪式+清怪把伤害压住！"},
            "counter": "一次仪式都别放：漏=回血+永久增伤慢性死亡！",
        },
    ],
        "hp_mult": 1.5747,  # v173.3 Boss降级hp补偿 ×1.091
        "atk_mult": 1.3657,  # v173.3 Boss降级atk补偿 ×1.048
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
        "boss": ["b_eter", "蚀夜(真相形态)", "boss", 95,
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
                    95,
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
        "mech": "phase,phase,phase,enrage",
        "phases": [
        {
            "min": 75,
            "add_skills": [
                "ms_f6_an_ying_jian_yu",
            ],
            "script": {"name": "暗影形态·轻响", "icon": "🌑"},
        },
        {
            "min": 50,
            "add_skills": [
                "ms_f6_fen_shen_huo_lang",
            ],
            "script": {"name": "烈焰形态·怒燃", "icon": "🔥"},
        },
        {
            "min": 25,
            "add_skills": [
                "ms_f6_shen_han",
                "ms_han_bing_tu_xi",
            ],
            "script": {"name": "寒冰形态·霜语", "icon": "❄️"},
        },
    ],
        # v116.1 剧本化示范：三阶段换招（追加技能）/演出文案/阈值预告（可选字段，不配置则旧行为）
        "phases": [
            {"min": 60, "add_skills": ["ms_zhao_huan_shen_yuan"],
             "script": {"name": "深渊裂隙张开", "icon": "🌑"}},
            {"min": 30, "add_skills": ["ms_shen_yuan_zhi_nu"],
             "script": {"name": "深渊之怒倾泻", "icon": "💀"}},
        ],
        "hp_mult": 1.0992,  # v173.3 Boss降级hp补偿 ×1.084
        "atk_mult": 1.1848,  # v173.3 Boss降级atk补偿 ×1.045
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
        "boss": ["b_om_shadow", "古龙·奥姆之影", "boss", 95,
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
                    95,
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
        "mech": "reflect,heal,summon,phase,player_low",
        "phases": [
        {
            "min": 50,
            "add_skills": [
                "ms_f6_ling_hun_bo_li",
            ],
            "script": {"name": "灵魂窃取开始", "icon": "💀"},
        },
        {
            "min": 40,
            "add_skills": [
                "ms_f6_zhao_huan_ku_long",
                "ms_f6_chuan_cheng_he_fu_huo",
            ],
            "phase_id": "enrage",
            "script": {"name": "传承之核·亮起", "icon": "🔮"},
        },
    ],
        "hp_mult": 6.7327,  # v173.3 Boss降级hp补偿 ×1.084

        "atk_mult": 1.2227,  # v173.3 Boss降级atk补偿 ×1.045
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
        "boss": ["b_fort_ghost", "要塞幽灵", "boss", 23,
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
                "boss": ["b_fort_ghost", "要塞幽灵", "boss", 23,
                         ["ms_ai_hao", "ms_chuan_shen", "ms_zhao_huan_ku_lou"],
                         ["要塞残片"]],
            },
        ],
                "key_item": "军旗碎片",
        # v110 审计修复：key_item 回退材料名（v110.11 消歧误改为消耗品名——材料
        # items.py:1565 desc 明示"可作钥匙进入鹿角要塞"，采集池 ancient/old_battlefield
        # 产 mat_jun_qi_sui_pian；改后入口按名校验与背包材料匹配，钥匙链恢复）
        "key_source": "古战场/旧战场遗迹采集",
        "mech": "phase,summon,phase_open,enrage",
        "phys_reduce": 0.5,
        "hp_mult": 2.5676,  # v173.3 Boss降级hp补偿 ×1.108

        "atk_mult": 1.103,  # v173.3 Boss降级atk补偿 ×1.103

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
        "boss": ["b_trial_knight", "试炼骑士长", "boss", 41,
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
                "boss": ["b_trial_knight", "试炼骑士长", "boss", 41,
                         ["ms_sheng_guang_dan", "ms_jian_ji", "ms_zhao_huan"],
                         ["试炼徽记"]],
            },
        ],
                "key_item": "试炼令",
        "key_source": "铁盾镇军械铺购买(400 金)",
        "mech": "phase,phase_open,player_low,enrage",
        "phases": [
        {
            "min": 70,
            "phase_id": "normal",
            "add_skills": [
                "ms_dun_ji_shi_lian",
                "ms_shi_zi_zhan",
            ],
            "script": {"name": "入门考核", "icon": "⚔️", "enter_line": "⚠️ 意图：骑士长正在蓄力【十字斩】！——用『防御』接下它，骑士团会认可你的胆识！"},
            "counter": "看见【蓄力十字斩】读条就『防御』——防反成功 = 全额格挡 + 破绽爆发窗！",
        },
        {
            "min": 35,
            "phase_id": "enrage",
            "atk_mult": 1.2,
            "freq_mult": 0.85,
            "add_skills": [
                "ms_sheng_guang_qi_yuan",
            ],
            "script": {"name": "进阶考核", "icon": "🏹", "warn_line": "圣光弹后可能连发——双连读条可见，布甲脆皮记得提前防御！"},
            "counter": "盾击·试炼带沉默：中了就放不出打断——法系看见盾击前摇预先防御！",
        },
        {
            "min": 0,
            "phase_id": "rampage",
            "atk_mult": 1.3,
            "add_skills": [
                "ms_sheng_guang_cai_jue",
            ],
            "script": {"name": "终考·骑士之誓", "icon": "🏅", "warn_line": "追加第 5 招【圣光裁决】！圣光笼罩全场——读条防御依然是最稳答案！"},
            "counter": "稳定防反 = 在破绽窗口内快速压血——防反打桩的正确姿势！",
        },
    ],
        "hp_mult": 3.1302,  # v173.3 Boss降级hp补偿 ×1.203

        "atk_mult": 1.4189,  # v173.3 Boss降级atk补偿 ×1.182

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
        "boss": ["b_moon_guard", "月神守卫", "boss", 65,
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
                "boss": ["b_moon_guard", "月神守卫", "boss", 65,
                         ["ms_yue_guang_zhan", "ms_zhi_yu", "ms_zhao_huan"],
                         ["月辉碎片"]],
            },
        ],
                "key_item": "月辉钥匙",
        "key_source": "月冠王庭购买(3000 金)",
        "mech": "phase,summon,shield",
        "minions": [
        {
            "name": "光柱圣像",
            "count": 0,
            "monster": [
                "m_moon_knight",
                "月骑士",
                "dps",
                64,
                [
                    "ms_yue_guang_zhan",
                    "ms_dun_ji",
                ],
                [
                    "月辉碎片",
                ],
            ],
        },
        {
            "name": "镜面圣像",
            "count": 0,
            "monster": [
                "m_moon_priest",
                "月神侍僧",
                "dps",
                60,
                [
                    "ms_yue_guang_zhan",
                ],
                [
                    "月辉碎片",
                ],
            ],
        },
    ],
        "phases": [
        {
            "min": 60,
            "add_skills": [
                "ms_ji_huo_guang_zhu",
                "ms_ji_huo_jing_mian",
            ],
            "phase_id": "normal",
            "script": {"name": "朝圣之礼", "icon": "🏛️", "enter_line": "🏛️ 圣像低鸣——守卫正在激活【光柱圣像】！打断可封印它！"},
            "counter": "断>光柱>圣盾>镜面；光柱在场先碎（还叠攻）；镜面让坦克转火碎！",
        },
        {
            "min": 30,
            "add_skills": [
                "ms_ji_huo_sheng_dun",
                "ms_yue_guang_cai_jue",
            ],
            "phase_id": "enrage",
            "atk_mult": 1.15,
            "freq_mult": 0.9,
            "script": {"name": "试炼加严", "icon": "⚔️", "warn_line": "圣盾苏醒：守卫获得 30% 护盾+读条免疫打断——先破盾再断唱！"},
            "counter": "盾碎=2 刻崩解爆发窗；机关留 2 座=共鸣审判（1.6×全队+裁决+50%）！",
        },
        {
            "min": 0,
            "phase_id": "rampage",
            "atk_mult": 1.3,
            "script": {"name": "神威降临", "icon": "🌙", "warn_line": "机关顺序反转：圣盾→镜面→光柱——优先级跟着反过来！"},
            "counter": "终局：断一个碎一个；断不干净=共鸣审判+裁决连招！",
        },
    ],
        "hp_mult": 2.4841,  # v173.3 Boss降级hp补偿 ×1.069

        "atk_mult": 1.2477,  # v173.3 Boss降级atk补偿 ×1.043

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
        "boss": ["b_frost_lord", "冰霜领主", "boss", 79,
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
                "boss": ["b_frost_lord", "冰霜领主", "boss", 79,
                         ["ms_bing_xi", "ms_dong_jie", "ms_zhao_huan"],
                         ["永冻之核"]],
            },
        ],
                "key_item": "寒冰令",
        "key_source": "永冻冰原精英·冰原猛犸·雪岭掉落",
        "mech": "phase,phase_open",
        "minions": [
        {
            "name": "冰元素",
            "count": 0,
            "monster": [
                "m_frost_guard",
                "寒冰守卫",
                "dps",
                74,
                [
                    "ms_bing_xi",
                    "ms_bing_dan",
                ],
                [
                    "永冻之核",
                ],
            ],
        },
    ],
        "phases": [
        {
            "min": 50,
            "add_skills": [
                "ms_bing_feng_li_zhao",
            ],
            "phase_id": "normal",
            "script": {"name": "凛冬王座", "icon": "❄️", "enter_line": "❄️ 冰霜领主抬手凝霜——挨冰越多越接近冻僵，4 层停手清层！"},
            "counter": "冰息叠层、冻结技引爆——净化/暖身是清层工具，别贪读条！",
        },
        {
            "min": 30,
            "add_skills": [
                "ms_ji_han_feng_bao",
                "ms_zhao_bing_yuan_su_lord",
            ],
            "phase_id": "enrage",
            "atk_mult": 1.15,
            "freq_mult": 0.85,
            "script": {"name": "严寒", "icon": "🌨️", "warn_line": "极寒风暴！全队冻结威胁+冰元素叠层——清层节奏被迫提速！"},
            "counter": "AOE 清冰元素（防层数爆炸）；极寒风暴出现=全队准备净化！",
        },
        {
            "min": 0,
            "phase_id": "rampage",
            "atk_mult": 1.3,
            "script": {"name": "永冻", "icon": "🧊", "warn_line": "永冻领域展开——冻住=大概率团灭，极限清层时刻！"},
            "counter": "4 层必清层；防御姿态减冰伤（冰息可防 80%）；火系爆发！",
        },
    ],
        "hp_mult": 7.0456,  # v173.3 Boss降级hp补偿 ×1.098

        "atk_mult": 1.2654,  # v173.3 Boss降级atk补偿 ×1.057
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
        "boss": ["b_storm_king", "雷霆君主", "boss", 95,
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
                "boss": ["b_storm_king", "雷霆君主", "boss", 95,
                         ["ms_lei_bao", "ms_feng_bao_zhi_yan", "ms_zhao_huan_lei_niao"],
                         ["风暴之核"]],
            },
        ],
                "key_item": "雷光令",
        "key_source": "风暴崖精英·风暴崖主·雷鸣掉落",
        "mech": "phase,phase,summon",
        "phases": [
        {
            "min": 60,
            "add_skills": [
                "ms_f6_lian_lei",
            ],
            "script": {"name": "雷云激化", "icon": "⚡"},
        },
        {
            "min": 30,
            "add_skills": [
                "ms_f6_lian_lei",
                "ms_f6_jing_dian_jie_dian",
            ],
            "phase_id": "enrage",
            "script": {"name": "审判风暴", "icon": "🌩️"},
        },
    ],
        "hp_mult": 7.5297,  # v173.3 Boss降级hp补偿 ×1.050

        "atk_mult": 1.6038,  # v173.3 Boss降级atk补偿 ×1.026
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
        "boss": ["b_ghost_captain", "幽灵船长·克罗", "boss", 43,
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
                    43,
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
        "mech": "phase,summon,enrage",
        "minions": [
        {
            "name": "幽灵水手",
            "count": 0,
            "monster": [
                "m_ghost_sailor",
                "幽灵水手",
                "dps",
                38,
                [
                    "ms_xiu_jian",
                    "ms_ai_hao",
                ],
                [
                    "幽灵帆布",
                ],
            ],
        },
    ],
        "phases": [
        {
            "min": 60,
            "phase_id": "normal",
            "add_skills": [
                "ms_wang_chao_zu_zhou",
            ],
            "script": {"name": "起雾", "icon": "🌫️", "enter_line": "🌊 亡潮诅咒叠至 1 层：幽灵伤害 +12%×N！层越高越痛！"},
            "counter": "诅咒叠层不是即死是增伤——治疗够就硬吃，DPS 越快越划算！",
        },
        {
            "min": 30,
            "phase_id": "enrage",
            "atk_mult": 1.15,
            "freq_mult": 0.85,
            "add_skills": [
                "ms_wan_dao_an_ying",
                "ms_chen_chuan_mei_ying",
            ],
            "script": {"name": "涨潮", "icon": "🌊", "warn_line": "诅咒 3 层后追加【沉船魅影】（蓄力 2.2 单体）——中招者治疗压力陡增！"},
            "counter": "清层优先清 T；沉船魅影读条必断或防御减半；别把主力输出从克罗身上挪走太久！",
        },
        {
            "min": 0,
            "phase_id": "rampage",
            "atk_mult": 1.3,
            "freq_mult": 0.7,
            "script": {"name": "风暴眼", "icon": "⛈️", "warn_line": "狂暴×1.35！诅咒叠层更快、幽灵补位更快——DPS 慢就清层保命！"},
            "counter": "末段=治疗资源规划+击杀节奏；牧师圣辉涤净可一次压掉诅咒+哀嚎双压力！",
        },
    ],
        "hp_mult": 3.0488,  # v173.3 Boss降级hp补偿 ×1.194

        "atk_mult": 1.3931,  # v173.3 Boss降级atk补偿 ×1.171

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
        "boss": ["b_siren_queen", "海妖女王·蓝歌", "boss", 57,
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
                    57,
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
        "mech": "phase,summon,heal",
        "minions": [
        {
            "name": "触手",
            "count": 0,
            "monster": [
                "m_kraken_tentacle",
                "海妖触手",
                "tank",
                54,
                [
                    "ms_jiao_sha",
                    "ms_shui_xi",
                ],
                [
                    "触手皮",
                ],
            ],
        },
    ],
        "phases": [
        {
            "min": 60,
            "add_skills": [
                "ms_chao_yong_ling_yu",
            ],
            "phase_id": "normal",
            "freq_mult": 0.8,
            "script": {"name": "重唱·潮鸣渐起", "icon": "🎶", "warn_line": "召唤越来越密……触手满 3 只时女王会进入潮鸣姿态（本体加攻）！"},
            "counter": "清触手 > 打 Boss：触手压到 0 = 幽蓝回响只剩减速！",
        },
        {
            "min": 30,
            "phase_id": "enrage",
            "atk_mult": 1.3,
            "freq_mult": 0.85,
            "script": {"name": "谢幕·葬歌", "icon": "🖤", "warn_line": "召唤与歌声开始同拍——被歌声+缠绕同时控制=团灭点！"},
            "counter": "终局：看见召唤立刻清，绝不让触手和歌同刻生效！",
        },
    ],
        "hp_mult": 10.4977,  # v173.3 Boss降级hp补偿 ×1.090

        "atk_mult": 1.2503,  # v173.3 Boss降级atk补偿 ×1.074
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
        "boss": ["b_lange", "海神祭司·澜歌", "boss", 69,
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
                    69,
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
        "mech": "phase,summon,heal",
        "minions": [
        {
            "name": "鲨鱼",
            "count": 0,
            "monster": [
                "m_shell_warrior",
                "甲壳战士",
                "dps",
                68,
                [
                    "ms_qian_ji",
                    "ms_ying_hua",
                ],
                [
                    "甲壳残片",
                ],
            ],
        },
    ],
        "phases": [
        {
            "min": 65,
            "add_skills": [
                "ms_chao_xi_yi_shi",
                "ms_yin_chao_hui_chun",
            ],
            "phase_id": "normal",
            "script": {"name": "潮信初至", "icon": "🌊", "enter_line": "🌊 潮落（引潮回春/清鲨鱼窗）→ 潮起（怒浪 dot）→ ⚠️ 仪式读条必断！"},
            "counter": "潮落清鲨鱼补状态；潮起扛浪；仪式读条打断=免团伤+2 刻反噬爆发窗！",
        },
        {
            "min": 35,
            "add_skills": [
                "ms_lang_yong_pai_ji",
                "ms_lang_chao_dot",
            ],
            "phase_id": "enrage",
            "atk_mult": 1.1,
            "freq_mult": 0.85,
            "script": {"name": "怒潮渐急", "icon": "🌊", "warn_line": "周期 8→6 刻！仪式咏唱与潮起几乎无缝——打断窗口变紧！"},
            "counter": "读条 2 刻抢断；浪潮 dot 0.55/刻——群疗铺潮起期！",
        },
        {
            "min": 0,
            "phase_id": "rampage",
            "atk_mult": 1.3,
            "script": {"name": "海神之怒", "icon": "⛈️", "warn_line": "狂暴！浪潮 dot 0.7/刻；漏断 2 次=怒海化身常驻！"},
            "counter": "一次都别漏：反噬窗 1.5 刻变薄——爆发质量定胜负！",
        },
    ],
        "hp_mult": 8.7321,  # v173.3 Boss降级hp补偿 ×1.066

        "atk_mult": 1.2494,  # v173.3 Boss降级atk补偿 ×1.040
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
        "boss": ["b_aolan", "深海龙王·敖澜", "boss", 75,
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
                    75,
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
        "mech": "phase,stacks,phase_open",
        "phases": [
        {
            "min": 50,
            "add_skills": [
                "ms_long_wei_ji_tui",
            ],
            "phase_id": "normal",
            "script": {"name": "水压积累", "icon": "🌊", "enter_line": "🌊 深水压强启动：每刻压力递增，全队承伤加重——防御/群奶轮转扛压！"},
            "counter": "龙威读条每 6 刻一次：打断=压力回落+输出窗！",
        },
        {
            "min": 30,
            "phase_id": "enrage",
            "atk_mult": 1.15,
            "freq_mult": 0.85,
            "script": {"name": "高压深渊", "icon": "🌊", "warn_line": "水压叠满！龙威读条更频繁+低血追击——高压斩杀段！"},
            "counter": "层数别叠太高；打断资源全留给龙威读条！",
        },
        {
            "min": 0,
            "phase_id": "rampage",
            "atk_mult": 1.3,
            "script": {"name": "深渊龙威", "icon": "🐲", "warn_line": "深渊水压碾来——必须靠打断龙威读条压压力，否则团灭！"},
            "counter": "终局：每次龙威读条=稳定打断点，断=压力回落+全队爆发！",
        },
    ],
        "hp_mult": 9.6093,  # v173.3 Boss降级hp补偿 ×1.061

        "atk_mult": 1.2541,  # v173.3 Boss降级atk补偿 ×1.036
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
        "boss": ["b_gray_lord", "灰矮人领主·石炉", "boss", 79,
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
                    79,
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
        "mech": "phase,summon",
        "minions": [
        {
            "name": "自爆傀儡",
            "count": 1,
            "monster": [
                "m_gray_engineer",
                "灰矮人技师",
                "healer",
                76,
                [
                    "ms_bao_dan",
                    "ms_xiu_li",
                ],
                [
                    "机械零件",
                ],
            ],
        },
        {
            "name": "修理傀儡",
            "count": 1,
            "monster": [
                "m_gray_engineer",
                "灰矮人技师",
                "healer",
                76,
                [
                    "ms_xiu_li",
                    "ms_bao_dan",
                ],
                [
                    "机械零件",
                ],
            ],
        },
        {
            "name": "激振炉",
            "count": 0,
            "monster": [
                "m_gray_dwarf",
                "灰矮人战士",
                "dps",
                74,
                [
                    "ms_zhan_chui",
                    "ms_kuang_bao",
                ],
                [
                    "灰矮人徽记",
                ],
            ],
        },
    ],
        "phases": [
        {
            "min": 50,
            "add_skills": [
                "ms_zhao_zi_bao_kui_lei",
                "ms_zhao_xiu_li_kui_lei",
                "ms_zhao_ji_zhen_kui_lei",
            ],
            "phase_id": "normal",
            "script": {"name": "锻造台轰鸣", "icon": "⛏️", "enter_line": "⛏️ 三台傀儡挡在石炉身前——自爆的会团灭、修理的在回血、激振的在加攻！"},
            "counter": "清除顺序：自爆>修理>激振——修理工不杀=白打！",
        },
        {
            "min": 30,
            "add_skills": [
                "ms_rong_lu_bao_fa",
            ],
            "phase_id": "enrage",
            "atk_mult": 1.15,
            "freq_mult": 0.85,
            "script": {"name": "锻炉过热", "icon": "🔥", "warn_line": "炉膛发红！傀儡越造越快+熔炉爆发 AOE——清傀儡节奏提速！"},
            "counter": "AOE 一次清多傀儡；打断召唤=阻止造新傀儡！",
        },
        {
            "min": 0,
            "add_skills": [
                "ms_zhong_chui_lian_da",
            ],
            "phase_id": "rampage",
            "atk_mult": 1.3,
            "script": {"name": "狂暴锻打", "icon": "🔨", "warn_line": "狂暴锻打！激振炉还在加攻——先拆激振炉，清完本体暴露！"},
            "counter": "终局：清完傀儡=本体暴露爆发窗，集火秒本体！",
        },
    ],
        "hp_mult": 7.0456,  # v173.3 Boss降级hp补偿 ×1.098

        "atk_mult": 1.2654,  # v173.3 Boss降级atk补偿 ×1.057
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
        "boss": ["b_under_dragon", "地底古龙·黑渊", "boss", 89,
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
                    89,
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
        "mech": "phase,summon",
        "minions": [
        {
            "name": "幼龙",
            "count": 1,
            "monster": [
                "m_under_drake",
                "地底幼龙",
                "dps",
                84,
                [
                    "ms_suan_xi",
                    "ms_long_zhao",
                ],
                [
                    "地底龙鳞",
                ],
            ],
        },
    ],
        "phases": [
        {
            "min": 60,
            "add_skills": [
                "ms_suan_xi_under",
                "ms_di_di_li_zhao",
            ],
            "phase_id": "normal",
            "script": {"name": "蚀骨之地", "icon": "🐍", "enter_line": "🐍 黑渊盘踞岩浆湖中央——看到『正在施展酸息』就打断或准备净化！"},
            "counter": "腐蚀 3 层前净化掉；酸息读条=免费输出窗；幼龙 AOE 清掉！",
        },
        {
            "min": 30,
            "add_skills": [
                "ms_fu_shi_tu_xi_heng_sao",
                "ms_zhao_you_long_under",
            ],
            "phase_id": "enrage",
            "atk_mult": 1.15,
            "freq_mult": 0.85,
            "script": {"name": "溶骨", "icon": "🧪", "warn_line": "鳞甲泛起酸泡——横扫吐息让全队都叠腐蚀，净化按人分配！"},
            "counter": "横扫=全队 1 层腐蚀；幼龙第二腐蚀来源，AOE 一轮清空最赚！",
        },
        {
            "min": 0,
            "phase_id": "rampage",
            "atk_mult": 1.2,
            "script": {"name": "噬骸", "icon": "☠️", "warn_line": "酸血沸腾——黑渊越战越凶，噬骨深吞 2 刻读条=必断点！"},
            "counter": "终局：层数 3+ 必清（引爆真伤）；吞噬读条打断=虚脱爆发窗！",
        },
    ],
        "hp_mult": 9.1768,  # v173.3 Boss降级hp补偿 ×1.053

        "atk_mult": 1.5414,  # v173.3 Boss降级atk补偿 ×1.027
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
        "boss": ["b_storm_master", "风暴之主·云怒", "boss", 97,
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
                    97,
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
        "mech": "phase,phase,summon",
        "chains": [
        {
            "seq": [
                "ms_f6_lei_bao_feng_yan",
                "ms_lei_bao",
                "ms_f6_feng_bao_feng_yan",
            ],
            "cd": 1,
            "break": 0.1,
        },
    ],
        "phases": [
        {
            "min": 60,
            "add_skills": [
                "ms_f6_lei_ting_shen_pan",
            ],
            "script": {"name": "疾风·短条", "icon": "🌪️"},
        },
        {
            "min": 30,
            "add_skills": [
                "ms_f6_lei_ting_shen_pan",
            ],
            "phase_id": "enrage",
            "script": {"name": "风暴之怒", "icon": "🌀"},
        },
    ],
        "hp_mult": 15.4298,  # v173.3 Boss降级hp补偿 ×1.049

        "atk_mult": 1.6091,  # v173.3 Boss降级atk补偿 ×1.026
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
        "boss": ["b_moro", "深渊领主·摩罗", "boss", 95,
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
                    95,
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
        "mech": "stacks,summon,phase,enrage",
        "phases": [
        {
            "min": 60,
            "add_skills": [
                "ms_f6_fu_shi_wa_di",
            ],
            "script": {"name": "腐化领域扩张", "icon": "🌑"},
        },
        {
            "min": 30,
            "add_skills": [
                "ms_f6_fu_shi_wa_di",
                "ms_f6_mo_yu_kong_xi",
            ],
            "script": {"name": "恶魔军势·魔焰扩散", "icon": "👹"},
        },
    ],
        "hp_mult": 7.2871,  # v173.3 Boss降级hp补偿 ×1.050

        "atk_mult": 1.3012,  # v173.3 Boss降级atk补偿 ×1.026
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
        "boss": ["b_ola", "云中圣者·奥拉", "boss", 99,
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
                    99,
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
        "mech": "shield,phase,summon,phase_open",
        "opening": {"name": "天象轮替·预读开始", "effect": "atk_up", "power": 1},
        "phases": [
        {
            "min": 60,
            "add_skills": [
                "ms_f6_sheng_guang_ling_yu",
                "ms_f6_sheng_guang_tan",
                "ms_f6_lei_bao_tian_xiang",
                "ms_f6_lei_ji_tian_xiang",
                "ms_f6_sheng_yu",
                "ms_f6_yu_wei_zhao_huan",
            ],
            "script": {"name": "晴→雷→雨→云", "icon": "☁️"},
        },
        {
            "min": 30,
            "add_skills": [
                "ms_f6_sheng_guang_ling_yu",
                "ms_f6_lei_bao_tian_xiang",
                "ms_f6_sheng_yu",
            ],
            "phase_id": "enrage",
            "script": {"name": "天象归一", "icon": "🌟"},
        },
    ],
        "hp_mult": 15.2803,  # v173.3 Boss降级hp补偿 ×1.016

        "atk_mult": 1.6179,  # v173.3 Boss降级atk补偿 ×1.008
        "gold": 2451,
        "exp": 50069,
        "materials": ["奥拉圣印碎片"],
        "mat_count": 5,
        "blueprint": True,
    },

    # ================= v178 新副本（补等级缺口，2026-09-05） =================
    "inst_rust_dock": {
    "entry": {"map": "harbor_docks", "subarea": "harbor_docks_2"},
    "name": "锈潮船坞",
    "icon": "🦀",
    "lv": 25,
    "min_players": 2,
    "max_players": 3,
    "desc": "铁港码头废弃船坞下的锈蚀水道，潮水把整座旧船坞泡成了螃蟹的乐园。巨钳蟹王·锈钳盘踞船底，钳上还挂着一百艘沉船的船牌。(海港支线)",
    "intro": "码头货仓区尽头有道锈死的闸门，推开时潮声裹着铁锈味扑面而来——废弃船坞的水道里，锈壳蟹窸窣爬行，深处时不时传来钳甲碰撞的闷响。铁港的老水手说，蟹王·锈钳的巢就在最深的船底，它钳上的船牌，还在等船主们来认领。",
    "boss_line": "『咔——』锈钳的双钳缓缓张开，每片甲壳上都嵌着一枚沉船的船牌：『又是来讨船牌的活人？老子在这船坞底下活了三百年，连龙王都懒得收我！』",
    "outro": "蟹王的锈壳裂成满地碎片，沉船船牌叮叮当当散了一地。潮水漫过船底，锈潮第一次有了退去的迹象——铁港的船主们，终于能把自己的船牌挂回桅杆上了。",
    "boss": [
        "b_rust_crab",
        "巨钳蟹王·锈钳",
        "boss",
        31,
        ["ms_zhong_qian_xiu", "ms_heng_sao_xiu", "ms_qian_jia_lie_shi", "ms_xiu_qiao"],
        [
            "锈潮蟹甲",
        ],
    ],
    "minions": [
        {
            "name": "锈壳蟹",
            "count": 0,
            "monster": [
                "m_rust_crab",
                "锈壳蟹",
                "tank",
                27,
                [
                    "ms_qian_ji",
                    "ms_ying_hua",
                ],
                [
                    "锈潮蟹甲",
                ],
            ],
        },
    ],
    "stages": [
        {
            "name": "闸门水道",
            "monsters": [
                [
                    "m_rust_crab",
                    "锈壳蟹",
                    "tank",
                    25,
                    [
                        "ms_qian_ji",
                        "ms_ying_hua",
                    ],
                    [
                        "锈潮蟹甲",
                    ],
                ],
                [
                    "m_water_ghost",
                    "水鬼",
                    "dps",
                    27,
                    [
                        "ms_zhao_ji",
                        "ms_chan_rao",
                    ],
                    [
                        "锈潮蟹甲",
                    ],
                ],
            ],
            "elite": None,
            "boss": None,
        },
        {
            "name": "沉船坞池",
            "monsters": [
                [
                    "m_pirate",
                    "海盗水手",
                    "dps",
                    28,
                    [
                        "ms_wan_dao",
                    ],
                    [
                        "锈潮蟹甲",
                    ],
                ],
            ],
            "elite": [
                "e_rust_rigger",
                "锈潮水手鬼",
                "elite",
                30,
                [
                    "ms_xiu_jian",
                    "ms_ai_hao",
                ],
                [
                    "锈潮蟹甲",
                ],
            ],
            "boss": None,
        },
        {
            "name": "蟹王船底",
            "monsters": [],
            "elite": None,
            "boss": [
                "b_rust_crab",
                "巨钳蟹王·锈钳",
                "boss",
                31,
                [],
                [
                    "锈潮蟹甲",
                ],
            ],
        },
    ],
    "mech": "phase,enrage",
    "hp_mult": 5.2,
    "atk_mult": 0.75,
    "gold": 458,
    "exp": 7865,
    "materials": [
        "锈潮蟹甲",
    ],
    "mat_count": 2,
    "blueprint": True,
    "装备": [
        "锈潮蟹甲",
    ],
    "phases": [
        {
            "min": 60,
            "phase_id": "normal",
            "add_skills": [
                "ms_xiu_qiao",
                "ms_qian_jia_lie_shi",
            ],
            "script": {"name": "锈蚀外壳", "icon": "🦀", "enter_line": "🦀 蟹王船底：锈钳的双钳嵌满沉船船牌——锈壳减伤 40%，先把它打到 60% 震碎外壳！"},
            "counter": "硬打锈壳是白耗！压血到 60% 破壳；看见【钳夹猎食】读条=它要夹人，打断救队友！",
        },
        {
            "min": 30,
            "phase_id": "exhaust",
            "dmg_taken_mult": 1.4,
            "add_skills": [
                "ms_heng_sao_xiu",
            ],
            "exit_turns": 8,
            "script": {"name": "外壳破碎", "icon": "💥", "enter_line": "💥 蟹壳震碎、船牌散落一地！破甲窗 8 刻承伤 ×1.4——蟹王的软肋露出来了！"},
            "counter": "破壳窗 8 刻：大招全砸！看到【修壳】读条（破壳窗尾声）立刻打断=窗口续期！",
        },
        {
            "min": 0,
            "phase_id": "rampage",
            "atk_mult": 1.3,
            "dmg_taken_mult": 0.8,
            "freq_mult": 0.85,
            "add_skills": [],
            "script": {"name": "锈壳再生", "icon": "⚔️", "warn_line": "狂暴！锈壳再生但更脆（减伤 20%）——钳夹与横扫更密，打断【修壳】的手不能停！"},
            "counter": "终局：破壳窗短而珍贵——每次【修壳】读条都是最后一次续期机会，必断！",
        },
    ],
},
    "inst_candle_crypt": {
    "entry": {"map": "dawn_cathedral", "subarea": "dawn_cathedral_1"},
    "name": "烛影墓窟",
    "icon": "🕯️",
    "lv": 29,
    "min_players": 1,
    "max_players": 2,
    "desc": "大圣堂地下被封死的古墓廊道，数百年的烛油在地面凝成厚壳。烛影主教·赫尔嘉在此布道——给死人布道，也给误入者布道。(教会地下支线)",
    "intro": "圣堂侧廊的祭衣间后有一扇被蜡封死的门，撬开时，一股混合着烛油与尘土的气味涌出。墓窟廊道两侧的烛台明明灭灭，墙上手绘的圣像全被涂去了眼睛——赫尔嘉的声音从廊道尽头传来，像在诵经，又像在等你走近。",
    "boss_line": "『光明太吵了。』赫尔嘉抬手拂过一排烛火，火苗齐齐矮了半截：『让它们熄灭一会儿，好让我听见死者真正的声音——你们，也是来听布道的吗？』",
    "outro": "最后一盏烛火在赫尔嘉指尖熄灭，墓窟彻底沉入黑暗——随即，廊道尽头的天窗透进一线晨光。那些被涂掉眼睛的圣像在光里重新显出轮廓，仿佛终于可以安息。",
    "boss": [
        "b_candle_bishop",
        "烛影主教·赫尔嘉",
        "boss",
        35,
        ["ms_zhu_huo_zhu", "ms_xi_deng", "ms_zhao_zhu_hun", "ms_an_ying_qin_shi"],
        [
            "烛影烛泪",
        ],
    ],
    "minions": [
        {
            "name": "烛魂",
            "count": 1,
            "monster": [
                "m_candle_wraith",
                "烛魂",
                "caster",
                32,
                [
                    "ms_zhuo_shao",
                    "ms_you_ling",
                ],
                [
                    "烛影烛泪",
                ],
            ],
        },
    ],
    "stages": [
        {
            "name": "蜡封廊道",
            "monsters": [
                [
                    "m_candle_wraith",
                    "烛魂",
                    "caster",
                    29,
                    [
                        "ms_zhuo_shao",
                        "ms_you_ling",
                    ],
                    [
                        "烛影烛泪",
                    ],
                ],
                [
                    "m_cultist",
                    "暗影教徒",
                    "dps",
                    30,
                    [
                        "ms_an_ying_dan",
                        "ms_an_ying_zhao",
                    ],
                    [
                        "烛影烛泪",
                    ],
                ],
            ],
            "elite": None,
            "boss": None,
        },
        {
            "name": "涂目圣像厅",
            "monsters": [
                [
                    "m_grave_priest",
                    "墓窟祭司",
                    "healer",
                    33,
                    [
                        "ms_hei_an_zhi_liao",
                        "ms_an_ying_dan",
                    ],
                    [
                        "烛影烛泪",
                    ],
                ],
            ],
            "elite": [
                "e_candle_guard",
                "烛卫",
                "elite",
                34,
                [
                    "ms_sheng_guang_dan",
                    "ms_dun_ji",
                ],
                [
                    "烛影烛泪",
                ],
            ],
            "boss": None,
        },
        {
            "name": "烛影礼拜堂",
            "monsters": [],
            "elite": None,
            "boss": [
                "b_candle_bishop",
                "烛影主教·赫尔嘉",
                "boss",
                35,
                [],
                [
                    "烛影烛泪",
                ],
            ],
        },
    ],
    "mech": "phase,phase_open,summon",
    "hp_mult": 1.57,
    "atk_mult": 0.79,
    "gold": 561,
    "exp": 9900,
    "materials": [
        "烛影烛泪",
    ],
    "mat_count": 2,
    "blueprint": True,
    "装备": [
        "烛影烛泪",
    ],
    "phases": [
        {
            "min": 60,
            "phase_id": "normal",
            "exit_turns": 6,
            "add_skills": [
                "ms_xi_deng",
                "ms_zhao_zhu_hun",
            ],
            "script": {"name": "烛光摇曳", "icon": "🕯️", "enter_line": "🕯️ 礼拜堂烛火通明——烛光态！她在烛光里布道，读条【熄灯】时打断她=全场继续亮着打！"},
            "counter": "看见【熄灯】（读条 2 刻）立刻打断；被黑进熄灭态就清烛魂+防御拖 4 刻复燃！",
        },
        {
            "min": 0,
            "phase_id": "exhaust",
            "dmg_taken_mult": 1.3,
            "def_add": 60,
            "freq_mult": 1.5,
            "exit_turns": 4,
            "add_skills": [
                "ms_an_ying_qin_shi",
            ],
            "script": {
                "name": "烛影幢幢",
                "icon": "🌑",
                "enter_line": "🌑 赫尔嘉吹熄了烛火——大殿陷入黑暗 4 刻（暗影庇护）！她的影子每刻都在侵蚀你们！",
                "warn_line": "⚠️ 熄灭态：优先清掉烛魂（黑暗中 +50%！）——全队防御+治疗拖过 4 刻，烛火会自动复燃！",
            },
            "counter": "黑暗里别硬拼：清烛魂 > 保血线；复燃瞬间 2 刻是安全爆发窗！",
        },
    ],
    "on_interrupt": {"effect": "vulnerable", "value": 1.3, "turns": 1},
},
    "inst_thunder_mine": {
    "entry": {"map": "hill_mine", "subarea": "hill_mine_4"},
    "name": "雷鸣矿道",
    "icon": "⚡",
    "lv": 32,
    "min_players": 1,
    "max_players": 2,
    "desc": "山丘矿洞最深处被雷晶矿脉炸开的巷道，矿车轨道上趴着雷晶蜥，雷灵在电线般的矿脉间流窜。雷晶巨像·轰鸣守着整条矿脉的心脏。(矿务支线)",
    "intro": "塌方矿厅尽头传出一声闷雷，脚下每一颗碎石都在跟着震。矿道里嵌满幽蓝的雷晶，空气里静电扎得人汗毛直立——老矿工说，这条矿脉是活的，而轰鸣，就是矿脉长出来的心脏。",
    "boss_line": "『轰——！』巨像胸口的雷晶核骤然亮起，整条矿道的雷晶跟着共鸣：『矿脉……是我的……心跳……也是你们的……葬歌！』",
    "outro": "巨像轰然跪倒，胸口的雷晶核黯淡成一块死石。矿道的雷光第一次安静下来，采空的矿脉深处，传来矿工们试探的脚步声——这条矿道，终于能重新点灯了。",
    "boss": [
        "b_thunder_golem",
        "雷晶巨像·轰鸣",
        "boss",
        37,
        ["ms_lei_jing_zhong_chui", "ms_dian_hu_jian_she", "ms_lei_ting_zha_lie", "ms_lei_jing_ning_ju", "ms_lei_jing_sui_xie"],
        [
            "雷晶矿核",
        ],
    ],
    "minions": [
        {
            "name": "雷晶核",
            "count": 2,
            "monster": [
                "m_crystal_core",
                "雷晶核",
                "tank",
                34,
                [
                    "ms_ying_hua",
                ],
                [
                    "雷晶矿核",
                ],
            ],
        },
    ],
    "stages": [
        {
            "name": "雷光巷道",
            "monsters": [
                [
                    "m_goblin_miner",
                    "地精矿工",
                    "dps",
                    30,
                    [
                        "ms_gao_ji",
                    ],
                    [
                        "雷晶矿核",
                    ],
                ],
                [
                    "m_crystal_gecko",
                    "雷晶蜥",
                    "speedster",
                    32,
                    [
                        "ms_lei_ji",
                        "ms_ji_pao",
                    ],
                    [
                        "雷晶矿核",
                    ],
                ],
            ],
            "elite": None,
            "boss": None,
        },
        {
            "name": "矿脉心脏前厅",
            "monsters": [
                [
                    "m_mine_sprite",
                    "矿道雷灵",
                    "caster",
                    34,
                    [
                        "ms_shan_dian_lian",
                        "ms_lei_jian",
                    ],
                    [
                        "雷晶矿核",
                    ],
                ],
            ],
            "elite": [
                "e_thunder_lizard",
                "雷晶蜥王",
                "elite",
                36,
                [
                    "ms_lei_ji",
                    "ms_yao_sui",
                ],
                [
                    "雷晶矿核",
                ],
            ],
            "boss": None,
        },
        {
            "name": "雷晶巨像穴",
            "monsters": [],
            "elite": None,
            "boss": [
                "b_thunder_golem",
                "雷晶巨像·轰鸣",
                "boss",
                37,
                [],
                [
                    "雷晶矿核",
                ],
            ],
        },
    ],
    "mech": "phase,stacks,summon,phase_open",
    "hp_mult": 3.35,
    "atk_mult": 1.38,
    "gold": 635,
    "exp": 11373,
    "materials": [
        "雷晶矿核",
    ],
    "mat_count": 2,
    "blueprint": True,
    "装备": [
        "雷晶矿核",
    ],
    "phases": [
        {
            "min": 65,
            "phase_id": "normal",
            "add_skills": [
                "ms_lei_ting_zha_lie",
                "ms_lei_jing_ning_ju",
            ],
            "script": {
                "name": "初触雷晶",
                "icon": "⚡",
                "enter_line": "⚡ 巨像穴：轰鸣胸口雷晶亮起——⚡ 已充能 0/5！你打它=给它充能，碎雷晶核放能！",
                "warn_line": "⚠️ 口诀：充能记账、满前泄压、溢出必断！雷晶核=它的泄压阀！",
            },
            "counter": "层数到 3 就碎晶核（清层+短路 2 刻爆发窗）；满 5 无核可碎=打断【雷霆炸裂】！",
        },
        {
            "min": 35,
            "phase_id": "enrage",
            "atk_mult": 1.15,
            "freq_mult": 0.85,
            "add_skills": [
                "ms_lei_jing_sui_xie",
            ],
            "script": {"name": "矿脉共振", "icon": "💠", "warn_line": "矿脉共振！充能叠得更快、电弧更凶、碎屑震晕——碎晶节奏必须跟上！"},
            "counter": "别把晶核当杂兵清光——留 1 颗应急泄压阀；爆发技排在碎晶之后！",
        },
        {
            "min": 0,
            "phase_id": "rampage",
            "atk_mult": 1.3,
            "freq_mult": 0.85,
            "add_skills": [
                "ms_lei_ting_jian_ta",
            ],
            "script": {"name": "过载核心", "icon": "🌩️", "warn_line": "过载核心！狂暴叠在充能上、雷霆践踏震落矿道落石——把碎晶排进输出循环当第 5 个技能！"},
            "counter": "终局：满层失守=断【雷霆炸裂】保命；碎晶=2 刻 ×1.3 承伤爆发窗，白嫖！",
        },
    ],
    "on_minion_died": {"effect": "stacks_clear", "value": 1},
    "on_interrupt": {"effect": "stacks_set", "key": "charge", "value": 3},
},
    "inst_whirl_arena": {
    "entry": {"map": "storm_strait", "subarea": "storm_strait_1"},
    "name": "旋涡竞技场",
    "icon": "🐢",
    "lv": 46,
    "min_players": 2,
    "max_players": 3,
    "desc": "风暴海峡中央一座随潮汐沉浮的环形礁台，潮水在礁台四周绞成永不停歇的旋涡。石壳龟·磐涡把这里当成了它的角斗场——打赢它，才能从旋涡眼里游出去。(群岛支线)",
    "intro": "海峡口的水面下有一座环形的白石礁台，潮汐把它托起又吞没。礁台四周的旋涡绞着碎船板与鱼骨，而磐涡就趴在礁台中央——它背上刻满了挑战者的名字，每一道划痕，都是一场没打完的角斗。",
    "boss_line": "『石壳一缩，潮水听话。』磐涡慢悠悠探出龟首，旋涡在它身后轰然加速：『三百年来，还没人能在我的潮汐里站满六个数。你——要来试试吗？』",
    "outro": "磐涡的壳裂开一道缝，旋涡缓缓平息，礁台第一次完整地浮出水面。你把名字刻上它的背壳，又在后面补了一行小字——『打赢了』。海峡的潮声，像在鼓掌。",
    "boss": [
        "b_whirl_turtle",
        "石壳龟·磐涡",
        "boss",
        52,
        ["ms_ju_qian_heng_sao", "ms_xuan_wo_la_che", "ms_shui_dan_chong_ji", "ms_luo_shi_po_qiao", "ms_suo_qiao_xi"],
        [
            "磐涡龟甲",
        ],
    ],
    "minions": [
        {
            "name": "漩涡鲛兵",
            "count": 0,
            "monster": [
                "m_whirl_merrow",
                "漩涡鲛兵",
                "dps",
                48,
                [
                    "ms_san_cha_ji",
                    "ms_xuan_wo",
                ],
                [
                    "磐涡龟甲",
                ],
            ],
        },
    ],
    "stages": [
        {
            "name": "潮间礁台",
            "monsters": [
                [
                    "m_whirlpool_spirit",
                    "漩涡精灵",
                    "healer",
                    46,
                    [
                        "ms_shui_dan",
                        "ms_xuan_wo",
                    ],
                    [
                        "磐涡龟甲",
                    ],
                ],
                [
                    "m_merrow",
                    "鲛人战士",
                    "dps",
                    47,
                    [
                        "ms_san_cha_ji",
                        "ms_shui_dan",
                    ],
                    [
                        "磐涡龟甲",
                    ],
                ],
            ],
            "elite": None,
            "boss": None,
        },
        {
            "name": "漩涡内环",
            "monsters": [
                [
                    "m_whirl_merrow",
                    "漩涡鲛兵",
                    "dps",
                    49,
                    [
                        "ms_san_cha_ji",
                        "ms_xuan_wo",
                    ],
                    [
                        "磐涡龟甲",
                    ],
                ],
                [
                    "m_arena_shark",
                    "竞技鲨",
                    "dps",
                    50,
                    [
                        "ms_si_yao",
                        "ms_jiao_sha",
                    ],
                    [
                        "磐涡龟甲",
                    ],
                ],
            ],
            "elite": [
                "e_whirl_guard",
                "漩涡卫士",
                "elite",
                51,
                [
                    "ms_shui_xi",
                    "ms_dun_ji",
                ],
                [
                    "磐涡龟甲",
                ],
            ],
            "boss": None,
        },
        {
            "name": "磐涡角斗场",
            "monsters": [],
            "elite": None,
            "boss": [
                "b_whirl_turtle",
                "石壳龟·磐涡",
                "boss",
                52,
                [],
                [
                    "磐涡龟甲",
                ],
            ],
        },
    ],
    "mech": "phase,enrage",
    "hp_mult": 8.4,
    "atk_mult": 1.27,
    "gold": 998,
    "exp": 18729,
    "materials": [
        "磐涡龟甲",
    ],
    "mat_count": 3,
    "blueprint": True,
    "装备": [
        "磐涡龟甲",
    ],
    "phases": [
        {
            "min": 65,
            "phase_id": "normal",
            "exit_turns": 3,
            "add_skills": [
                "ms_ju_qian_heng_sao",
                "ms_xuan_wo_la_che",
                "ms_shui_dan_chong_ji",
                "ms_luo_shi_po_qiao",
                "ms_suo_qiao_xi",
            ],
            "script": {
                "name": "初识潮汐",
                "icon": "🌪️",
                "enter_line": "🌪️ 角斗场四周旋涡绞起——潮汐涌动：3 刻拉扯期（缩壳挨打）→ 3 刻破壳期（爆发窗）循环！",
                "warn_line": "⚠️ 拉扯期少输出稳血线；破壳期（承伤 +25%）把所有大招砸进去！",
            },
            "counter": "拉扯期=防御/用药/群疗；破壳期第 1 刻起手读大招；【落石破壳】读条必断！",
        },
        {
            "min": 30,
            "phase_id": "enrage",
            "atk_mult": 1.15,
            "freq_mult": 0.9,
            "exit_turns": 2,
            "add_skills": [],
            "script": {"name": "涡流加剧", "icon": "🌀", "warn_line": "旋涡绞得更急！拉扯期压到 2 刻、退潮更快——被拖到中心的话落石 ×1.5 专砸你！"},
            "counter": "被拖住（减速标记）立刻防御+治疗预读；打断【落石破壳】永远优先！",
        },
        {
            "min": 0,
            "phase_id": "rampage",
            "atk_mult": 1.3,
            "freq_mult": 0.85,
            "exit_turns": 4,
            "add_skills": [],
            "script": {"name": "怒涛核心", "icon": "⛈️", "warn_line": "怒涛核心！拉扯期拉长到 4 刻、破壳期只剩 2 刻——DPS 不足会永远在拉扯期挨打！"},
            "counter": "终局=斩杀节奏：破壳 2 刻打满爆发，拉扯期绝不贪刀——血线就是你的 DPS！",
        },
    ],
    "on_interrupt": {"effect": "vulnerable", "value": 1.15, "turns": 1},
},
    "inst_blacktide_opera": {
    "entry": {"map": "mist_tide_passage", "subarea": "mist_tide_passage_3"},
    "name": "黑潮歌剧院",
    "icon": "🎭",
    "lv": 50,
    "min_players": 2,
    "max_players": 4,
    "desc": "黑潮海峡底下沉没的旧歌剧厅，潮水在包厢与舞台之间来回涨落。首席海妖·歌澜每晚都在这里开唱——观众席上坐满溺亡的乐迷，而她们，已经不会鼓掌了。(深海支线)",
    "intro": "雾潮航道尽头的灯塔下，一条缠满海藻的石阶直通海底。推开锈蚀的剧场大门，海水从穹顶的破洞泻下，像一束追光打在舞台上——歌澜就站在光柱里调音，她身后，溺亡的合唱团正缓缓浮出水面，等着今晚的开幕。",
    "boss_line": "『欢迎光临黑潮歌剧院。』歌澜捻了捻喉间的珍珠，声音穿过海水依旧清亮：『今晚的曲目是《溺亡者的谢幕》——请安静欣赏，不要……打断我的高音。』",
    "outro": "歌澜最后一个音符沉入海底，剧场的追光缓缓熄灭。溺亡的合唱团化作泡沫浮向海面，歌澜摘下胸前的歌谱别针，轻轻放在你手心——这座歌剧院终于散场了，而它的曲谱，换了一位新的保管人。",
    "boss": [
        "b_opera_siren",
        "首席海妖·歌澜",
        "boss",
        56,
        ["ms_yong_tan_lang_yong", "ms_gao_yin_gong_ming", "ms_he_sheng_zhao_huan", "ms_xie_mu_qu", "ms_di_yin_wei_mu"],
        [
            "咏叹谱残页",
        ],
    ],
    "minions": [
        {
            "name": "和声海妖",
            "count": 1,
            "monster": [
                "m_choir_siren",
                "和声海妖",
                "healer",
                52,
                [
                    "ms_mei_huo_zhi_ge",
                    "ms_zhi_yu",
                ],
                [
                    "咏叹谱残页",
                ],
            ],
        },
    ],
    "stages": [
        {
            "name": "淹没门厅",
            "monsters": [
                [
                    "m_choir_siren",
                    "和声海妖",
                    "healer",
                    50,
                    [
                        "ms_mei_huo_zhi_ge",
                        "ms_zhi_yu",
                    ],
                    [
                        "咏叹谱残页",
                    ],
                ],
                [
                    "m_siren_scout",
                    "海妖斥候",
                    "speedster",
                    51,
                    [
                        "ms_mei_huo_zhi_ge",
                    ],
                    [
                        "咏叹谱残页",
                    ],
                ],
            ],
            "elite": None,
            "boss": None,
        },
        {
            "name": "包厢回廊",
            "monsters": [
                [
                    "m_drowned_chorister",
                    "溺亡唱诗班",
                    "dps",
                    53,
                    [
                        "ms_chen_mo_jian_xiao",
                        "ms_you_ling",
                    ],
                    [
                        "咏叹谱残页",
                    ],
                ],
                [
                    "m_merrow",
                    "鲛人战士",
                    "dps",
                    52,
                    [
                        "ms_san_cha_ji",
                        "ms_shui_dan",
                    ],
                    [
                        "咏叹谱残页",
                    ],
                ],
            ],
            "elite": [
                "e_opera_guard",
                "剧场护卫",
                "elite",
                54,
                [
                    "ms_ju_lang",
                    "ms_dun_ji",
                ],
                [
                    "咏叹谱残页",
                ],
            ],
            "boss": None,
        },
        {
            "name": "主舞台",
            "monsters": [],
            "elite": None,
            "boss": [
                "b_opera_siren",
                "首席海妖·歌澜",
                "boss",
                56,
                [],
                [
                    "咏叹谱残页",
                ],
            ],
        },
    ],
    "mech": "phase,summon,phase_open",
    "hp_mult": 8.9,
    "atk_mult": 0.98,
    "gold": 1111,
    "exp": 21081,
    "materials": [
        "咏叹谱残页",
    ],
    "mat_count": 3,
    "blueprint": True,
    "装备": [
        "咏叹谱残页",
    ],
    "phases": [
        {
            "min": 60,
            "phase_id": "normal",
            "add_skills": [
                "ms_xie_mu_qu",
                "ms_he_sheng_zhao_huan",
            ],
            "script": {
                "name": "序曲",
                "icon": "🎭",
                "enter_line": "🎭 主舞台的追光打在歌澜身上——她开始咏唱【谢幕曲】！3 刻读条，全队都能抢断！",
                "warn_line": "⚠️ 断唱=2 刻破音虚脱（承伤 ×1.4）爆发窗；咏唱间隙 AOE 清和声海妖！",
            },
            "counter": "咏唱第 1-2 刻立刻打断 → ×1.4 虚脱窗全队爆发；整场目标=谢幕曲 0 成功！",
        },
        {
            "min": 30,
            "phase_id": "enrage",
            "atk_mult": 1.15,
            "freq_mult": 0.9,
            "add_skills": [
                "ms_di_yin_wei_mu",
            ],
            "script": {"name": "咏叹调", "icon": "🎶", "warn_line": "咏唱前她会先开【低音帷幕】护盾——不破盾断不了唱；和声召唤 4→3 刻，放大器越堆越多！"},
            "counter": "先破盾（20% 血）再断唱；清和声 > 贪本体——3 只满和声 = 3.84× 核弹！",
        },
        {
            "min": 0,
            "phase_id": "rampage",
            "atk_mult": 1.3,
            "freq_mult": 0.8,
            "add_skills": [],
            "script": {"name": "终曲·安可", "icon": "🎼", "warn_line": "终幕高音！谢幕曲一轮接一轮——高音共鸣的震晕专骗打断资源，被晕=断不了唱=团灭点！"},
            "counter": "免疫控制/净化硬吃高音共鸣；打断永远只留给谢幕曲；虚脱窗打满收尾！",
        },
    ],
    "on_interrupt": {"effect": "vulnerable", "value": 1.4, "turns": 2},
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
    "inst_rust_dock":       {"pool": ["eq_jin_gou_wan_dao", "eq_qi_shi_chang_xue", "eq_mi_wu_xiang_lian"], "pool_rate": 0.35, "boss_rate": 0.0},
    "inst_candle_crypt":    {"pool": ["eq_sheng_guang_chang_jian", "eq_sheng_guang_zhan_kui", "eq_sheng_dian_zhan_chui"], "pool_rate": 0.35, "boss_rate": 0.0},
    "inst_thunder_mine":    {"pool": ["eq_lie_zong_liao_ya", "eq_qi_shi_chang_xue", "eq_sheng_guang_chang_jian"], "pool_rate": 0.35, "boss_rate": 0.0},
    "inst_whirl_arena":     {"pool": ["eq_xu_shi_quan_tao", "eq_mao_yan_shi_xiong_zhen", "eq_sheng_guang_zhan_tui"], "pool_rate": 0.35, "boss_rate": 0.0},
    "inst_blacktide_opera": {"pool": ["eq_jing_ling_lian_jia", "eq_hai_shen_chang_xue", "eq_xing_yu_xiang_lian"], "pool_rate": 0.35, "boss_rate": 0.0},
}
