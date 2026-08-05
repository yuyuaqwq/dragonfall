# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - maps.py（v48 怪物技能/掉落转 ID）"""
MAPS = [
    {
        "id": "vila_gate",
        "name": "维拉镇城门",
        "lv": 1,
        "region": "西境",
        "chapter": 1,
        "area": "vila",
        "area_name": "维拉镇",
        "desc": "维拉镇的东大门，商队与冒险者从这里进出。城门外的野地里偶尔有野兽出没。",
        "type": "城镇外郊",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_stray_dog",
                "野狗",
                "dps",
                1,
                [
                    "ms_si_yao"
                ],
                [
                    "mat_ye_gou_liao_ya"
                ]
            ],
            [
                "m_giant_rat",
                "巨型老鼠",
                "speedster",
                2,
                [
                    "ms_si_yao"
                ],
                [
                    "mat_shu_wei"
                ]
            ]
        ],
        "elite": [
            "e_bandit_leader",
            "山贼头目",
            "elite",
            4,
            [
                "ms_pi_kan",
                "ms_nu_hou"
            ],
            [
                "mat_shan_zei_hui_zhang"
            ]
        ],
        "boss": None,
        "npcs": []
    },
    {
        "id": "vila_street",
        "name": "维拉镇中央大街",
        "lv": 1,
        "region": "西境",
        "chapter": 1,
        "area": "vila",
        "area_name": "维拉镇",
        "desc": "石板铺就的主街，两侧商铺林立，叫卖声此起彼伏。铁匠铺的炉火昼夜不熄。",
        "type": "城镇区域",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_blacksmith"
        ]
    },
    {
        "id": "vila_square",
        "name": "维拉镇中心广场",
        "lv": 1,
        "region": "西境",
        "chapter": 1,
        "area": "vila",
        "area_name": "维拉镇",
        "desc": "城镇的心脏，喷泉旁竖着公告板，镇长府邸就在广场北侧。新来的冒险者都在这里报到。",
        "type": "城镇区域",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_mayor",
            "npc_bard"
        ]
    },
    {
        "id": "vila_tavern",
        "name": "维拉镇酒馆·醉熊",
        "lv": 1,
        "region": "西境",
        "chapter": 1,
        "area": "vila",
        "area_name": "维拉镇",
        "desc": "整个小镇最热闹的地方，麦酒与冒险故事一样管够。赏金猎人喜欢在这里物色搭档。",
        "type": "城镇区域",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_bartender",
            "npc_bounty"
        ]
    },
    {
        "id": "vila_inn",
        "name": "维拉镇旅店·星夜",
        "lv": 1,
        "region": "西境",
        "chapter": 1,
        "area": "vila",
        "area_name": "维拉镇",
        "desc": "干净温暖的旅店，老板娘玛丽总是笑眯眯的。在这里住宿能恢复全部状态。",
        "type": "城镇区域",
        "shop": False,
        "healer": True,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_innkeeper"
        ]
    },
    {
        "id": "emerald_edge",
        "name": "翡翠森林边缘",
        "lv": 4,
        "region": "西境",
        "chapter": 1,
        "area": "emerald",
        "area_name": "翡翠森林",
        "desc": "森林的边缘地带，阳光还能透过树冠。林间传来狼嚎，深入请小心。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_forest_wolf",
                "森林狼",
                "dps",
                4,
                [
                    "ms_si_yao",
                    "ms_hao_jiao"
                ],
                [
                    "mat_lang_pi"
                ]
            ],
            [
                "m_venom_spider",
                "毒蜘蛛",
                "speedster",
                5,
                [
                    "ms_du_yao"
                ],
                [
                    "mat_zhi_zhu_du_nang"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "emerald_trail",
        "name": "翡翠林间小径",
        "lv": 5,
        "region": "西境",
        "chapter": 1,
        "area": "emerald",
        "area_name": "翡翠森林",
        "desc": "精灵走出来的小径，树木会说话，魔法的光芒在林间流淌。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_venom_spider",
                "毒蜘蛛",
                "speedster",
                5,
                [
                    "ms_du_yao"
                ],
                [
                    "mat_zhi_zhu_du_nang"
                ]
            ],
            [
                "m_greensprite",
                "绿妖精",
                "caster",
                6,
                [
                    "ms_mo_fa_fei_dan"
                ],
                [
                    "mat_yao_jing_zhi_chen"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "emerald_heart",
        "name": "翡翠森林之心",
        "lv": 6,
        "region": "西境",
        "chapter": 1,
        "area": "emerald",
        "area_name": "翡翠森林",
        "desc": "森林最古老的神木所在，精灵的圣域。守护这里的远古圣鹿不容侵犯。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_greensprite",
                "绿妖精",
                "caster",
                6,
                [
                    "ms_mo_fa_fei_dan"
                ],
                [
                    "mat_yao_jing_zhi_chen"
                ]
            ],
            [
                "m_forest_wolf",
                "森林狼",
                "dps",
                6,
                [
                    "ms_si_yao",
                    "ms_hao_jiao"
                ],
                [
                    "mat_lang_pi"
                ]
            ]
        ],
        "elite": [
            "e_forest_treant",
            "远古树人",
            "elite",
            7,
            [
                "ms_zhong_ji",
                "ms_zi_ran_zhu_fu"
            ],
            [
                "mat_yuan_gu_shu_pi"
            ]
        ],
        "boss": [
            "b_ancient_elk",
            "远古圣鹿",
            "boss",
            8,
            [
                "ms_sheng_guang_chong_feng",
                "ms_zi_ran_zhu_fu",
                "ms_jian_ta"
            ],
            [
                "mat_sheng_lu_jiao"
            ]
        ],
        "npcs": [
            "npc_druid"
        ]
    },
    {
        "id": "stonefist_camp",
        "name": "石拳营地",
        "lv": 7,
        "region": "西境",
        "chapter": 1,
        "area": "stonefist",
        "area_name": "石拳丘陵",
        "desc": "矮人在丘陵脚下搭建的营地，篝火与铁砧声不断。矿洞方向常有地精的动静。",
        "type": "城镇区域",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_goblin_grunt",
                "地精步兵",
                "dps",
                7,
                [
                    "ms_pi_kan"
                ],
                [
                    "mat_di_jing_er_duo"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_dwarf_elder"
        ]
    },
    {
        "id": "stonefist_mine",
        "name": "矿洞入口",
        "lv": 8,
        "region": "西境",
        "chapter": 1,
        "area": "stonefist",
        "area_name": "石拳丘陵",
        "desc": "矮人世代开采的矿脉洞口，如今被地精占领，洞内幽深黑暗。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_goblin_grunt",
                "地精步兵",
                "dps",
                7,
                [
                    "ms_pi_kan"
                ],
                [
                    "mat_di_jing_er_duo"
                ]
            ],
            [
                "m_mine_bat",
                "矿洞蝙蝠",
                "speedster",
                8,
                [
                    "ms_fu_chong"
                ],
                [
                    "mat_bian_fu_yi"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "stonefist_deep",
        "name": "矿洞深处",
        "lv": 9,
        "region": "西境",
        "chapter": 1,
        "area": "stonefist",
        "area_name": "石拳丘陵",
        "desc": "矿洞最深处，巨大的蛇影在黑暗中游弋。地精萨满在这里举行诡异的仪式。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_tunnel_snake",
                "洞穴巨蛇",
                "tank",
                9,
                [
                    "ms_du_yao",
                    "ms_chan_rao"
                ],
                [
                    "mat_she_lin"
                ]
            ],
            [
                "m_mine_bat",
                "矿洞蝙蝠",
                "speedster",
                9,
                [
                    "ms_fu_chong"
                ],
                [
                    "mat_bian_fu_yi"
                ]
            ]
        ],
        "elite": [
            "e_goblin_shaman",
            "地精萨满",
            "elite",
            10,
            [
                "ms_an_ying_jian",
                "ms_zhao_huan"
            ],
            [
                "mat_sa_man_tu_teng"
            ]
        ],
        "boss": [
            "b_tunnel_king",
            "隧洞之王",
            "boss",
            11,
            [
                "ms_zhong_ji",
                "ms_nu_hou",
                "ms_xuan_yun_zhong_ji",
                "ms_di_dong"
            ],
            [
                "mat_di_jing_wang_guan"
            ]
        ],
        "npcs": []
    },
    {
        "id": "gloom_edge",
        "name": "幽暗沼泽边缘",
        "lv": 10,
        "region": "腐土",
        "chapter": 2,
        "area": "gloom",
        "area_name": "幽暗沼泽",
        "desc": "沼泽的最外围，瘴气开始弥漫，脚下的泥土松软而危险。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_swamp_zombie",
                "沼泽僵尸",
                "tank",
                10,
                [
                    "ms_zhao_ji"
                ],
                [
                    "mat_jiang_shi_fu_rou"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "gloom_mire",
        "name": "泥沼深处",
        "lv": 11,
        "region": "腐土",
        "chapter": 2,
        "area": "gloom",
        "area_name": "幽暗沼泽",
        "desc": "越深入，瘴气越浓。腐尸爬行者在泥水中蠕动着，鬼魂的哀嚎此起彼伏。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_bog_ghost",
                "沼泽鬼魂",
                "caster",
                11,
                [
                    "ms_ji_qu",
                    "ms_ai_hao"
                ],
                [
                    "mat_gui_hun_jing_hua"
                ]
            ],
            [
                "m_corpse_crawler",
                "腐尸爬行者",
                "dps",
                12,
                [
                    "ms_zhao_ji",
                    "ms_du_yao"
                ],
                [
                    "mat_pa_xing_chong_ke"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "gloom_heart",
        "name": "沼泽之心",
        "lv": 12,
        "region": "腐土",
        "chapter": 2,
        "area": "gloom",
        "area_name": "幽暗沼泽",
        "desc": "亡灵天灾的腐化源头，骸骨术士的祭坛立于此地，腐朽领主盘踞其上。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_corpse_crawler",
                "腐尸爬行者",
                "dps",
                12,
                [
                    "ms_zhao_ji",
                    "ms_du_yao"
                ],
                [
                    "mat_pa_xing_chong_ke"
                ]
            ],
            [
                "m_swamp_zombie",
                "沼泽僵尸",
                "tank",
                12,
                [
                    "ms_zhao_ji"
                ],
                [
                    "mat_jiang_shi_fu_rou"
                ]
            ]
        ],
        "elite": [
            "e_bone_warlock",
            "骸骨术士",
            "elite",
            13,
            [
                "ms_an_ying_jian",
                "ms_zhao_hun",
                "ms_ji_qu"
            ],
            [
                "mat_shu_shi_he_xin"
            ]
        ],
        "boss": [
            "b_decay_lord",
            "腐朽领主",
            "boss",
            14,
            [
                "ms_zhao_ji",
                "ms_fu_xi",
                "ms_zhao_hun",
                "ms_kuang_bao"
            ],
            [
                "mat_fu_xiu_zhi_ren"
            ]
        ],
        "npcs": []
    },
    {
        "id": "redridge_field",
        "name": "赤脊旷野",
        "lv": 13,
        "region": "腐土",
        "chapter": 2,
        "area": "redridge",
        "area_name": "赤脊荒原",
        "desc": "赤色岩石覆盖的旷野，兽人部落的巡逻队在此出没，座狼的嚎叫撕破寂静。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_orc_grunt",
                "兽人步兵",
                "dps",
                13,
                [
                    "ms_pi_kan",
                    "ms_nu_hou"
                ],
                [
                    "mat_shou_ren_liao_ya"
                ]
            ],
            [
                "m_warg",
                "座狼",
                "speedster",
                14,
                [
                    "ms_si_yao",
                    "ms_hao_jiao"
                ],
                [
                    "mat_zuo_lang_quan_chi"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "redridge_ridge",
        "name": "赤脊山脊",
        "lv": 15,
        "region": "腐土",
        "chapter": 2,
        "area": "redridge",
        "area_name": "赤脊荒原",
        "desc": "陡峭的山脊上风声猎猎，鹰身女妖在天空中盘旋，随时准备俯冲。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_harpy",
                "鹰身女妖",
                "caster",
                15,
                [
                    "ms_fu_chong",
                    "ms_jian_xiao"
                ],
                [
                    "mat_nv_yao_zhi_yu"
                ]
            ],
            [
                "m_warg",
                "座狼",
                "speedster",
                15,
                [
                    "ms_si_yao",
                    "ms_hao_jiao"
                ],
                [
                    "mat_zuo_lang_quan_chi"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "redridge_camp",
        "name": "战歌营地",
        "lv": 16,
        "region": "腐土",
        "chapter": 2,
        "area": "redridge",
        "area_name": "赤脊荒原",
        "desc": "战歌部落的大营，旌旗猎猎，兽人狂战士在营地中央的图腾柱下磨刀。",
        "type": "核心",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_orc_grunt",
                "兽人步兵",
                "dps",
                16,
                [
                    "ms_pi_kan",
                    "ms_nu_hou"
                ],
                [
                    "mat_shou_ren_liao_ya"
                ]
            ],
            [
                "m_harpy",
                "鹰身女妖",
                "caster",
                16,
                [
                    "ms_fu_chong",
                    "ms_jian_xiao"
                ],
                [
                    "mat_nv_yao_zhi_yu"
                ]
            ]
        ],
        "elite": [
            "e_orc_berserker",
            "兽人狂战士",
            "elite",
            16,
            [
                "ms_pi_kan",
                "ms_kuang_bao",
                "ms_zhong_ji"
            ],
            [
                "mat_kuang_zhan_zhi_xin"
            ]
        ],
        "boss": [
            "b_warband_chief",
            "战歌部落酋长",
            "boss",
            17,
            [
                "ms_pi_kan",
                "ms_zhan_hou",
                "ms_zhong_ji",
                "ms_kuang_bao"
            ],
            [
                "mat_qiu_zhang_zhan_ren"
            ]
        ],
        "npcs": [
            "npc_orc_prisoner"
        ]
    },
    {
        "id": "blackrock_gate",
        "name": "黑石城门",
        "lv": 16,
        "region": "腐土",
        "chapter": 2,
        "area": "blackrock",
        "area_name": "黑石城废墟",
        "desc": "曾是人类王国都城的东门，如今城门倒塌，骷髅卫兵在废墟间巡游。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_skeleton_guard",
                "骷髅卫兵",
                "tank",
                16,
                [
                    "ms_pi_kan",
                    "ms_dun_ji"
                ],
                [
                    "mat_gu_pian"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "blackrock_street",
        "name": "死城大街",
        "lv": 17,
        "region": "腐土",
        "chapter": 2,
        "area": "blackrock",
        "area_name": "黑石城废墟",
        "desc": "曾经繁华的主街，如今只剩下断壁残垣。食尸鬼在阴影中啃食着什么。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_ghoul",
                "食尸鬼",
                "dps",
                17,
                [
                    "ms_zhao_ji",
                    "ms_tun_shi"
                ],
                [
                    "mat_shi_shi_gui_zhi_zhao"
                ]
            ],
            [
                "m_spectre",
                "怨灵",
                "caster",
                18,
                [
                    "ms_ji_qu",
                    "ms_ai_hao",
                    "ms_fu_shen"
                ],
                [
                    "mat_ling_hun_sui_pian"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "blackrock_keep",
        "name": "黑石王座",
        "lv": 18,
        "region": "腐土",
        "chapter": 2,
        "area": "blackrock",
        "area_name": "黑石城废墟",
        "desc": "旧王国的王宫大殿，巫妖宰相的寒冰王座矗立于此，死亡骑士侍立两侧。",
        "type": "核心",
        "shop": False,
        "healer": True,
        "hidden": False,
        "monsters": [
            [
                "m_skeleton_guard",
                "骷髅卫兵",
                "tank",
                18,
                [
                    "ms_pi_kan",
                    "ms_dun_ji"
                ],
                [
                    "mat_gu_pian"
                ]
            ],
            [
                "m_spectre",
                "怨灵",
                "caster",
                18,
                [
                    "ms_ji_qu",
                    "ms_ai_hao",
                    "ms_fu_shen"
                ],
                [
                    "mat_ling_hun_sui_pian"
                ]
            ]
        ],
        "elite": [
            "e_death_knight",
            "死亡骑士",
            "elite",
            19,
            [
                "ms_pi_kan",
                "ms_si_wang_zhi_wo",
                "ms_an_ying_jian",
                "ms_kuang_bao"
            ],
            [
                "mat_si_wang_qi_shi_zhi_ren"
            ]
        ],
        "boss": [
            "b_lich_vizier",
            "巫妖宰相",
            "boss",
            20,
            [
                "ms_an_ying_jian",
                "ms_zhao_hun",
                "ms_ji_qu",
                "ms_wu_yao_qi_she"
            ],
            [
                "mat_wu_yao_fa_zhang"
            ]
        ],
        "npcs": [
            "npc_ghost_knight"
        ]
    },
    {
        "id": "magma_gorge",
        "name": "熔岩峡谷",
        "lv": 19,
        "region": "魔渊",
        "chapter": 3,
        "area": "magma",
        "area_name": "熔岩裂谷",
        "desc": "深渊恶魔撕开大地的裂隙，岩浆在脚下奔涌，火元素从熔岩中升起。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_fire_elemental",
                "火元素",
                "caster",
                19,
                [
                    "ms_huo_qiu",
                    "ms_zhuo_shao"
                ],
                [
                    "mat_huo_yan_he_xin"
                ]
            ],
            [
                "m_imp",
                "小恶魔",
                "speedster",
                20,
                [
                    "ms_huo_qiu",
                    "ms_jian_xiao"
                ],
                [
                    "mat_e_mo_zhi_jiao"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "magma_heart",
        "name": "熔岩核心",
        "lv": 21,
        "region": "魔渊",
        "chapter": 3,
        "area": "magma",
        "area_name": "熔岩裂谷",
        "desc": "裂谷的最深处，岩浆瀑布倾泻而下。熔岩暴君在此沉睡，火焰巨人看守着它的梦。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_lava_hound",
                "熔岩猎犬",
                "tank",
                21,
                [
                    "ms_si_yao",
                    "ms_zhuo_shao",
                    "ms_chong_zhuang"
                ],
                [
                    "mat_rong_yan_shi"
                ]
            ],
            [
                "m_imp",
                "小恶魔",
                "speedster",
                21,
                [
                    "ms_huo_qiu",
                    "ms_jian_xiao"
                ],
                [
                    "mat_e_mo_zhi_jiao"
                ]
            ]
        ],
        "elite": [
            "e_flame_giant",
            "火焰巨人",
            "elite",
            22,
            [
                "ms_zhong_ji",
                "ms_huo_qiu",
                "ms_zhuo_shao",
                "ms_lie_yan_zhen_ji"
            ],
            [
                "mat_ju_ren_yu_jin"
            ]
        ],
        "boss": [
            "b_magma_tyrant",
            "熔岩暴君",
            "boss",
            23,
            [
                "ms_huo_qiu",
                "ms_lie_yan_zhen_ji",
                "ms_zhuo_shao",
                "ms_yan_jiang_pen_fa"
            ],
            [
                "mat_rong_yan_zhi_jian"
            ]
        ],
        "npcs": []
    },
    {
        "id": "tundra_field",
        "name": "冰封旷野",
        "lv": 22,
        "region": "魔渊",
        "chapter": 3,
        "area": "tundra",
        "area_name": "冰封苔原",
        "desc": "极北的冰雪世界，暴风雪中传来冰原狼的低吼，冰霜巨魔在雪丘间游荡。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_ice_wolf",
                "冰原狼",
                "dps",
                22,
                [
                    "ms_si_yao",
                    "ms_bing_yao"
                ],
                [
                    "mat_bing_yuan_mao_pi"
                ]
            ],
            [
                "m_frost_troll",
                "冰霜巨魔",
                "tank",
                23,
                [
                    "ms_zhong_ji",
                    "ms_zai_sheng",
                    "ms_bing_yao"
                ],
                [
                    "mat_ju_mo_xue_rou"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "tundra_cave",
        "name": "冰霜洞穴",
        "lv": 24,
        "region": "魔渊",
        "chapter": 3,
        "area": "tundra",
        "area_name": "冰封苔原",
        "desc": "冰川下的巨大洞穴，冰晶折射着幽蓝的光。霜裔亚龙就在这里筑巢。",
        "type": "核心",
        "shop": False,
        "healer": True,
        "hidden": False,
        "monsters": [
            [
                "m_snow_wraith",
                "雪魅",
                "caster",
                24,
                [
                    "ms_ji_qu",
                    "ms_bing_yao",
                    "ms_bao_feng_xue"
                ],
                [
                    "mat_xue_zhi_jing_hua"
                ]
            ],
            [
                "m_frost_troll",
                "冰霜巨魔",
                "tank",
                24,
                [
                    "ms_zhong_ji",
                    "ms_zai_sheng",
                    "ms_bing_yao"
                ],
                [
                    "mat_ju_mo_xue_rou"
                ]
            ]
        ],
        "elite": [
            "e_glacier_golem",
            "冰川魔像",
            "elite",
            25,
            [
                "ms_zhong_ji",
                "ms_bing_qiang",
                "ms_shuang_xi"
            ],
            [
                "mat_yong_heng_zhi_bing"
            ]
        ],
        "boss": [
            "b_frost_wyrm",
            "霜裔亚龙",
            "boss",
            26,
            [
                "ms_shuang_xi",
                "ms_bao_feng_xue",
                "ms_si_yao",
                "ms_long_zhi_nu"
            ],
            [
                "mat_shuang_long_zhi_ya"
            ]
        ],
        "npcs": []
    },
    {
        "id": "stormpeak_path",
        "name": "风暴山道",
        "lv": 25,
        "region": "魔渊",
        "chapter": 3,
        "area": "stormpeak",
        "area_name": "风暴之巅",
        "desc": "通往山巅的陡峭山道，终年雷暴，雷电元素在云层中翻涌，巨鹰盘旋警戒。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_thunder_elemental",
                "雷电元素",
                "caster",
                25,
                [
                    "ms_shan_dian_jian",
                    "ms_lei_ji"
                ],
                [
                    "mat_lei_dian_he_xin"
                ]
            ],
            [
                "m_giant_eagle",
                "巨鹰",
                "speedster",
                26,
                [
                    "ms_fu_chong",
                    "ms_feng_ren"
                ],
                [
                    "mat_ju_ying_ling_yu"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "stormpeak_peak",
        "name": "风暴之巅",
        "lv": 27,
        "region": "魔渊",
        "chapter": 3,
        "area": "stormpeak",
        "area_name": "风暴之巅",
        "desc": "世界的屋脊，雷暴的中心。风暴巨人王手持雷霆之锤，君临此处。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_storm_serpent",
                "风暴巨蛇",
                "tank",
                27,
                [
                    "ms_shan_dian_jian",
                    "ms_chan_rao",
                    "ms_lei_ji"
                ],
                [
                    "mat_feng_bao_she_lin"
                ]
            ],
            [
                "m_giant_eagle",
                "巨鹰",
                "speedster",
                27,
                [
                    "ms_fu_chong",
                    "ms_feng_ren"
                ],
                [
                    "mat_ju_ying_ling_yu"
                ]
            ]
        ],
        "elite": [
            "e_sky_hunter",
            "苍穹猎手",
            "elite",
            28,
            [
                "ms_feng_ren",
                "ms_shan_dian_jian",
                "ms_feng_bao_zhao_huan"
            ],
            [
                "mat_cang_qiong_zhi_ren"
            ]
        ],
        "boss": [
            "b_storm_giant",
            "风暴巨人王",
            "boss",
            29,
            [
                "ms_lei_ji",
                "ms_feng_bao_zhao_huan",
                "ms_shan_dian_jian",
                "ms_bao_feng_zhi_nu"
            ],
            [
                "mat_lei_ting_zhi_chui"
            ]
        ],
        "npcs": [
            "npc_sky_hermit"
        ]
    },
    {
        "id": "shadow_gate",
        "name": "暗影城门",
        "lv": 28,
        "region": "魔渊",
        "chapter": 3,
        "area": "shadow_city",
        "area_name": "暗影之城",
        "desc": "深渊之门前的恶魔之城，城门由暗影恶魔把守，邪恶的气息扑面而来。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_shadow_demon",
                "暗影恶魔",
                "caster",
                28,
                [
                    "ms_an_ying_jian",
                    "ms_zhao_ji",
                    "ms_ji_qu"
                ],
                [
                    "mat_an_ying_sui_pian"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "shadow_street",
        "name": "暗影大街",
        "lv": 29,
        "region": "魔渊",
        "chapter": 3,
        "area": "shadow_city",
        "area_name": "暗影之城",
        "desc": "恶魔的集市大街，灾厄小魔在屋檐间跳跃，虚空掠夺者盯上了每一个闯入者。",
        "type": "野外",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_doom_imp",
                "灾厄小魔",
                "speedster",
                29,
                [
                    "ms_huo_qiu",
                    "ms_an_ying_jian",
                    "ms_jian_xiao"
                ],
                [
                    "mat_zai_e_zhi_xin"
                ]
            ],
            [
                "m_void_reaver",
                "虚空掠夺者",
                "dps",
                30,
                [
                    "ms_zhao_ji",
                    "ms_xu_kong_zhan",
                    "ms_kuang_bao"
                ],
                [
                    "mat_xu_kong_sui_pian"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "shadow_keep",
        "name": "暗影王座",
        "lv": 30,
        "region": "魔渊",
        "chapter": 3,
        "area": "shadow_city",
        "area_name": "暗影之城",
        "desc": "暗影主教的黑曜石王座大厅，深渊领主们在此匍匐。这里是深渊之门最后的屏障。",
        "type": "核心",
        "shop": False,
        "healer": True,
        "hidden": False,
        "monsters": [
            [
                "m_void_reaver",
                "虚空掠夺者",
                "dps",
                30,
                [
                    "ms_zhao_ji",
                    "ms_xu_kong_zhan",
                    "ms_kuang_bao"
                ],
                [
                    "mat_xu_kong_sui_pian"
                ]
            ],
            [
                "m_shadow_demon",
                "暗影恶魔",
                "caster",
                30,
                [
                    "ms_an_ying_jian",
                    "ms_zhao_ji",
                    "ms_ji_qu"
                ],
                [
                    "mat_an_ying_sui_pian"
                ]
            ]
        ],
        "elite": [
            "e_pit_lord",
            "深渊领主",
            "elite",
            30,
            [
                "ms_zhong_ji",
                "ms_huo_qiu",
                "ms_xu_kong_zhan",
                "ms_di_yu_huo"
            ],
            [
                "mat_shen_yuan_hui_ji"
            ]
        ],
        "boss": [
            "b_shadow_archon",
            "暗影主教",
            "boss",
            30,
            [
                "ms_an_ying_jian",
                "ms_xu_kong_zhan",
                "ms_ji_qu",
                "ms_an_ying_feng_bao"
            ],
            [
                "mat_an_ying_zhi_guan"
            ]
        ],
        "npcs": []
    },
    {
        "id": "abyss_plain",
        "name": "深渊荒原",
        "lv": 30,
        "region": "魔渊",
        "chapter": 3,
        "area": "abyss_gate",
        "area_name": "深渊之门",
        "desc": "深渊之门前的荒原，大地龟裂，虚空之力扭曲着空间。恶魔大军在此列阵。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_abyss_guardian",
                "深渊守卫",
                "tank",
                30,
                [
                    "ms_pi_kan",
                    "ms_xu_kong_zhan",
                    "ms_dun_ji"
                ],
                [
                    "mat_shen_yuan_jing_gang"
                ]
            ],
            [
                "m_void_hound",
                "虚空猎犬",
                "speedster",
                30,
                [
                    "ms_si_yao",
                    "ms_xu_kong_zhan",
                    "ms_hao_jiao"
                ],
                [
                    "mat_xu_kong_liao_ya"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "abyss_gate",
        "name": "深渊之门",
        "lv": 30,
        "region": "魔渊",
        "chapter": 3,
        "area": "abyss_gate",
        "area_name": "深渊之门",
        "desc": "魔王所在的最终战场，魔王·阿兹莫丹立于深渊之门下，大陆的命运在此一决。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_demon_herald",
                "恶魔先驱",
                "caster",
                30,
                [
                    "ms_huo_qiu",
                    "ms_an_ying_jian",
                    "ms_di_yu_huo"
                ],
                [
                    "mat_xian_qu_hao_jiao"
                ]
            ],
            [
                "m_void_hound",
                "虚空猎犬",
                "speedster",
                30,
                [
                    "ms_si_yao",
                    "ms_xu_kong_zhan",
                    "ms_hao_jiao"
                ],
                [
                    "mat_xu_kong_liao_ya"
                ]
            ]
        ],
        "elite": None,
        "boss": [
            "b_dark_lord",
            "魔王·阿兹莫丹",
            "boss",
            30,
            [
                "ms_xu_kong_zhan",
                "ms_di_yu_huo",
                "ms_an_ying_feng_bao",
                "ms_hui_mie_zhi_ji",
                "ms_han_bing_tu_xi"
            ],
            [
                "mat_hei_an_jun_zhu_zhi_ren"
            ]
        ],
        "npcs": []
    },
    {
        "id": "mithril_hall",
        "name": "秘银大厅",
        "lv": 26,
        "region": "魔渊",
        "chapter": 3,
        "area": "mithril",
        "area_name": "秘银遗迹",
        "desc": "上古矮人王的宝库大厅，秘银魔像沿着走廊巡视，符文骑士守卫着每一道门。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": True,
        "monsters": [
            [
                "m_mithril_golem",
                "秘银魔像",
                "tank",
                26,
                [
                    "ms_zhong_ji",
                    "ms_dun_ji"
                ],
                [
                    "mat_mi_yin_kuang_shi"
                ]
            ],
            [
                "m_runebound_knight",
                "符文骑士",
                "dps",
                28,
                [
                    "ms_pi_kan",
                    "ms_fu_wen_bao_fa",
                    "ms_dun_ji"
                ],
                [
                    "mat_fu_wen_sui_pian"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "mithril_vault",
        "name": "秘银宝库",
        "lv": 30,
        "region": "魔渊",
        "chapter": 3,
        "area": "mithril",
        "area_name": "秘银遗迹",
        "desc": "宝库的最深处，矮人王冠静静躺在王座上，宝藏守护者寸步不离。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": True,
        "monsters": [
            [
                "m_treasure_guardian",
                "宝藏守护者",
                "boss",
                30,
                [
                    "ms_zhong_ji",
                    "ms_xu_kong_zhan",
                    "ms_nu_hou"
                ],
                [
                    "mat_bao_cang_yao_shi"
                ]
            ]
        ],
        "elite": [
            "e_ancient_dwarf",
            "上古矮人王魂",
            "elite",
            30,
            [
                "ms_zhong_ji",
                "ms_fu_wen_bao_fa",
                "ms_zhan_hou",
                "ms_xian_zu_zhi_nu"
            ],
            [
                "mat_ai_ren_wang_zhi_jie"
            ]
        ],
        "boss": [
            "b_dwarf_king",
            "秘银之王",
            "boss",
            30,
            [
                "ms_zhong_ji",
                "ms_fu_wen_bao_fa",
                "ms_xian_zu_zhi_nu",
                "ms_mi_yin_zhen_ji"
            ],
            [
                "mat_mi_yin_wang_guan"
            ]
        ],
        "npcs": []
    },
    {
        "id": "holy_field",
        "name": "远境草甸",
        "lv": 31,
        "region": "远境高地",
        "chapter": 4,
        "area": "holy",
        "area_name": "远境高原",
        "desc": "远境高原的入口草甸，圣光透过云层洒下，却掩盖不住空气中弥漫的异样气息。光耀狼在草丛间游荡。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_holy_hawk",
                "远境猎鹰",
                "dps",
                31,
                [
                    "ms_fu_chong",
                    "ms_feng_ren"
                ],
                [
                    "mat_sheng_guang_yu_mao"
                ]
            ],
            [
                "m_radiant_wolf",
                "光耀狼",
                "speedster",
                32,
                [
                    "ms_si_yao",
                    "ms_hao_jiao"
                ],
                [
                    "mat_guang_yao_zhi_pi"
                ]
            ],
            [
                "m_holy_deer",
                "远境麋鹿",
                "tank",
                33,
                [
                    "ms_chong_zhuang",
                    "ms_zi_ran_zhu_fu"
                ],
                [
                    "mat_sheng_hui_lu_jiao"
                ]
            ]
        ],
        "elite": [
            "e_holy_knight",
            "远境骑士",
            "elite",
            34,
            [
                "ms_pi_kan",
                "ms_sheng_guang_zhan",
                "ms_dun_ji"
            ],
            [
                "mat_sheng_guang_hui_zhang"
            ]
        ],
        "boss": None,
        "npcs": []
    },
    {
        "id": "holy_altar",
        "name": "远境祭坛",
        "lv": 34,
        "region": "远境高地",
        "chapter": 4,
        "area": "holy",
        "area_name": "远境高原",
        "desc": "古老的圣光祭坛，信徒们曾在此祈祷。如今祭坛被暗影侵蚀，教会修士们神色诡异地低声吟唱。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_temple_adept",
                "教会修士",
                "caster",
                34,
                [
                    "ms_mo_fa_fei_dan",
                    "ms_sheng_guang_zhan"
                ],
                [
                    "mat_sheng_guang_jie_jing"
                ]
            ],
            [
                "m_radiant_wolf",
                "光耀狼",
                "speedster",
                33,
                [
                    "ms_si_yao",
                    "ms_hao_jiao"
                ],
                [
                    "mat_guang_yao_zhi_pi"
                ]
            ]
        ],
        "elite": [
            "e_holy_knight_captain",
            "远境骑士长",
            "elite",
            36,
            [
                "ms_pi_kan",
                "ms_sheng_guang_zhan",
                "ms_zhan_hou"
            ],
            [
                "mat_sheng_qi_shi_jian"
            ]
        ],
        "boss": None,
        "npcs": [
            "npc_holy_cardinal"
        ]
    },
    {
        "id": "holy_temple",
        "name": "远境大教堂",
        "lv": 38,
        "region": "远境高地",
        "chapter": 4,
        "area": "holy",
        "area_name": "远境高原",
        "desc": "远境大教堂的核心大殿，天使的雕像被暗影藤蔓缠绕。大主教说，赛拉斯大主教已经……堕落了。",
        "type": "核心",
        "shop": False,
        "healer": True,
        "hidden": False,
        "monsters": [
            [
                "m_holy_guard",
                "大教堂卫士",
                "tank",
                36,
                [
                    "ms_dun_ji",
                    "ms_sheng_guang_zhan"
                ],
                [
                    "mat_sheng_guang_dun_pai"
                ]
            ],
            [
                "m_seraph",
                "白翼教众",
                "caster",
                37,
                [
                    "ms_tian_fa",
                    "ms_sheng_guang_zhan"
                ],
                [
                    "mat_tian_shi_zhi_yu"
                ]
            ]
        ],
        "elite": [
            "e_seraph_captain",
            "白翼统领",
            "elite",
            37,
            [
                "ms_sheng_guang_zhan",
                "ms_tian_fa",
                "ms_shen_wei"
            ],
            [
                "mat_tian_shi_sheng_yin"
            ]
        ],
        "boss": [
            "b_archangel",
            "大主教·赛拉斯",
            "boss",
            38,
            [
                "ms_sheng_guang_zhan",
                "ms_tian_fa",
                "ms_shen_wei",
                "ms_sheng_guang_chong_feng"
            ],
            [
                "mat_tian_shi_sheng_yin"
            ]
        ],
        "npcs": []
    },
    {
        "id": "elf_forest",
        "name": "精灵之森",
        "lv": 41,
        "region": "远境高地",
        "chapter": 4,
        "area": "elf_court",
        "area_name": "精灵王庭",
        "desc": "精灵王庭外围的原始森林，古树参天，月光透过叶隙洒下。森林在低语，精灵们已经很久没有歌唱了。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_elf_archer",
                "精灵弓手",
                "dps",
                41,
                [
                    "ms_feng_ren",
                    "ms_fu_chong"
                ],
                [
                    "mat_jing_ling_jian_shi"
                ]
            ],
            [
                "m_moon_panther",
                "月影豹",
                "speedster",
                42,
                [
                    "ms_zhao_ji",
                    "ms_hao_jiao"
                ],
                [
                    "mat_yue_ying_zhi_pi"
                ]
            ],
            [
                "m_forest_spirit",
                "林间鹿灵",
                "caster",
                43,
                [
                    "ms_zi_ran_zhu_fu",
                    "ms_mo_fa_fei_dan"
                ],
                [
                    "mat_sen_lin_zhi_ling"
                ]
            ]
        ],
        "elite": [
            "e_moon_guard",
            "月光守卫",
            "elite",
            44,
            [
                "ms_feng_ren",
                "ms_chan_rao",
                "ms_zi_ran_zhu_fu"
            ],
            [
                "mat_yue_zhi_ren"
            ]
        ],
        "boss": None,
        "npcs": []
    },
    {
        "id": "elf_courtyard",
        "name": "月之庭院",
        "lv": 44,
        "region": "远境高地",
        "chapter": 4,
        "area": "elf_court",
        "area_name": "精灵王庭",
        "desc": "精灵王庭的月之庭院，银月泉水依旧流淌，但守护它的精灵法师们眼中只剩空洞。",
        "type": "野外",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_elf_mage",
                "精灵法师",
                "caster",
                44,
                [
                    "ms_huo_qiu",
                    "ms_shan_dian_jian"
                ],
                [
                    "mat_jing_ling_fa_zhu"
                ]
            ],
            [
                "m_jade_bird",
                "翠羽灵鸟",
                "speedster",
                45,
                [
                    "ms_fu_chong",
                    "ms_feng_ren"
                ],
                [
                    "mat_cui_yu"
                ]
            ]
        ],
        "elite": [
            "e_court_guard",
            "王庭禁卫",
            "elite",
            46,
            [
                "ms_pi_kan",
                "ms_feng_ren",
                "ms_dun_ji"
            ],
            [
                "mat_wang_ting_hui_zhang"
            ]
        ],
        "boss": None,
        "npcs": [
            "npc_elf_sage"
        ]
    },
    {
        "id": "elf_throne",
        "name": "王庭深处",
        "lv": 48,
        "region": "远境高地",
        "chapter": 4,
        "area": "elf_court",
        "area_name": "精灵王庭",
        "desc": "精灵王庭的最深处，月神祭坛上，女王的身影被暗影笼罩。她手中的月之泪，已化为黑色。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_court_guard",
                "王庭禁卫",
                "tank",
                48,
                [
                    "ms_pi_kan",
                    "ms_feng_ren",
                    "ms_dun_ji"
                ],
                [
                    "mat_wang_ting_hui_zhang"
                ]
            ],
            [
                "m_elf_mage",
                "精灵法师",
                "caster",
                47,
                [
                    "ms_huo_qiu",
                    "ms_shan_dian_jian"
                ],
                [
                    "mat_jing_ling_fa_zhu"
                ]
            ]
        ],
        "elite": [
            "e_moon_priest",
            "月神祭司",
            "elite",
            49,
            [
                "ms_mo_fa_fei_dan",
                "ms_bao_feng_xue",
                "ms_zi_ran_zhu_fu"
            ],
            [
                "mat_yue_zhi_lei"
            ]
        ],
        "boss": [
            "b_elf_queen",
            "精灵女王·艾薇安",
            "boss",
            50,
            [
                "ms_feng_ren",
                "ms_bao_feng_xue",
                "ms_zi_ran_zhu_fu",
                "ms_tian_fa"
            ],
            [
                "mat_yue_shen_zhi_guan"
            ]
        ],
        "npcs": []
    },
    {
        "id": "dragon_path",
        "name": "龙脊山道",
        "lv": 51,
        "region": "远境高地",
        "chapter": 4,
        "area": "dragon_ridge",
        "area_name": "龙脊山脉",
        "desc": "龙脊山脉的蜿蜒山道，灼热的气浪从山巅翻涌而下。龙裔战士在山道间巡逻，警惕地盯着每个闯入者。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_dragon_lizard",
                "龙鳞蜥蜴",
                "tank",
                51,
                [
                    "ms_si_yao",
                    "ms_long_zhi_nu"
                ],
                [
                    "mat_long_lin"
                ]
            ],
            [
                "m_cliff_wyvern",
                "岩脊飞龙",
                "speedster",
                52,
                [
                    "ms_fu_chong",
                    "ms_long_zhi_nu"
                ],
                [
                    "mat_fei_long_yi"
                ]
            ],
            [
                "m_dragonkin",
                "龙裔战士",
                "dps",
                53,
                [
                    "ms_pi_kan",
                    "ms_long_zhi_nu",
                    "ms_zhan_hou"
                ],
                [
                    "mat_long_yi_hui_ji"
                ]
            ]
        ],
        "elite": [
            "e_dragon_warrior",
            "龙脉战士长",
            "elite",
            54,
            [
                "ms_zhong_ji",
                "ms_long_zhi_nu",
                "ms_zhan_hou"
            ],
            [
                "mat_long_mai_zhan_ren"
            ]
        ],
        "boss": None,
        "npcs": []
    },
    {
        "id": "dragon_nest",
        "name": "龙巢之巅",
        "lv": 54,
        "region": "远境高地",
        "chapter": 4,
        "area": "dragon_ridge",
        "area_name": "龙脊山脉",
        "desc": "龙巢之巅，幼龙们在巢穴间嬉戏，却带着不属于幼龙的暴戾。贤者·岩语说，龙血正在被某种力量唤醒。",
        "type": "野外",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_ember_whelp",
                "赤炎幼龙",
                "caster",
                54,
                [
                    "ms_huo_qiu",
                    "ms_long_zhi_nu"
                ],
                [
                    "mat_long_yan_jing_hua"
                ]
            ],
            [
                "m_dragonkin",
                "龙裔战士",
                "dps",
                53,
                [
                    "ms_pi_kan",
                    "ms_long_zhi_nu",
                    "ms_zhan_hou"
                ],
                [
                    "mat_long_yi_hui_ji"
                ]
            ]
        ],
        "elite": [
            "e_dragon_guardian",
            "龙脉守护者",
            "elite",
            56,
            [
                "ms_long_zhi_nu",
                "ms_lie_yan_zhen_ji",
                "ms_zhan_hou"
            ],
            [
                "mat_long_mai_hu_fu"
            ]
        ],
        "boss": None,
        "npcs": [
            "npc_dragon_elder"
        ]
    },
    {
        "id": "dragon_shrine",
        "name": "龙眠圣殿",
        "lv": 58,
        "region": "远境高地",
        "chapter": 4,
        "area": "dragon_ridge",
        "area_name": "龙脊山脉",
        "desc": "龙眠圣殿，龙族的圣地。古龙·奥瑞斯盘踞在王座上，龙眼中燃烧着不属于龙族的混沌之火。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_flame_wyvern",
                "赤炎飞龙",
                "dps",
                58,
                [
                    "ms_huo_qiu",
                    "ms_long_zhi_nu",
                    "ms_fu_chong"
                ],
                [
                    "mat_fei_long_lin"
                ]
            ],
            [
                "m_dragon_guardian",
                "龙脉守护者",
                "tank",
                57,
                [
                    "ms_long_zhi_nu",
                    "ms_lie_yan_zhen_ji",
                    "ms_zhan_hou"
                ],
                [
                    "mat_long_mai_hu_fu"
                ]
            ]
        ],
        "elite": [
            "e_dragon_wing",
            "龙翼亲卫",
            "elite",
            59,
            [
                "ms_long_zhi_nu",
                "ms_sheng_guang_chong_feng",
                "ms_zhan_hou"
            ],
            [
                "mat_long_yi_jian"
            ]
        ],
        "boss": [
            "b_dragon_king",
            "古龙·奥瑞斯",
            "boss",
            60,
            [
                "ms_long_zhi_nu",
                "ms_lie_yan_zhen_ji",
                "ms_kuang_bao",
                "ms_tun_shi"
            ],
            [
                "mat_long_wang_zhi_jiao"
            ]
        ],
        "npcs": []
    },
    {
        "id": "void_edge",
        "name": "裂隙谷口",
        "lv": 61,
        "region": "旧战场",
        "chapter": 5,
        "area": "void_rift",
        "area_name": "裂隙谷地",
        "desc": "裂隙谷地的边缘地带，空间在这里扭曲成漩涡。裂隙蠕虫在裂隙间蠕动，发出令人牙酸的嘶鸣。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_void_worm",
                "裂隙蠕虫",
                "speedster",
                61,
                [
                    "ms_si_yao",
                    "ms_xu_kong_zhan"
                ],
                [
                    "mat_xu_kong_zhan_ye"
                ]
            ],
            [
                "m_rift_wraith",
                "裂隙魔灵",
                "caster",
                62,
                [
                    "ms_an_ying_jian",
                    "ms_xu_kong_zhan"
                ],
                [
                    "mat_lie_xi_sui_pian"
                ]
            ],
            [
                "m_void_minion",
                "废墟爪牙",
                "dps",
                63,
                [
                    "ms_zhao_ji",
                    "ms_xu_kong_zhan"
                ],
                [
                    "mat_xu_kong_zhi_zhao"
                ]
            ]
        ],
        "elite": [
            "e_void_ripper",
            "裂隙撕裂者",
            "elite",
            64,
            [
                "ms_xu_kong_zhan",
                "ms_an_ying_feng_bao",
                "ms_tun_shi"
            ],
            [
                "mat_si_lie_zhe_he_xin"
            ]
        ],
        "boss": None,
        "npcs": []
    },
    {
        "id": "void_corridor",
        "name": "古战场回廊",
        "lv": 64,
        "region": "旧战场",
        "chapter": 5,
        "area": "void_rift",
        "area_name": "裂隙谷地",
        "desc": "古战场回廊，无数破碎的世界在此重叠。谷口守望者悬浮在长廊两侧，空洞的眼眶注视着每一个过客。",
        "type": "野外",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_void_watcher",
                "谷口守望者",
                "tank",
                64,
                [
                    "ms_zhong_ji",
                    "ms_xu_kong_zhan",
                    "ms_dun_ji"
                ],
                [
                    "mat_xu_kong_hu_jia"
                ]
            ],
            [
                "m_rift_wraith",
                "裂隙魔灵",
                "caster",
                63,
                [
                    "ms_an_ying_jian",
                    "ms_xu_kong_zhan"
                ],
                [
                    "mat_lie_xi_sui_pian"
                ]
            ]
        ],
        "elite": [
            "e_void_lord",
            "裂隙领主",
            "elite",
            66,
            [
                "ms_xu_kong_zhan",
                "ms_xu_kong_beng_ta",
                "ms_an_ying_feng_bao"
            ],
            [
                "mat_lie_xi_ling_zhu_yin_ji"
            ]
        ],
        "boss": None,
        "npcs": [
            "npc_void_prophet"
        ]
    },
    {
        "id": "void_heart",
        "name": "战场中心",
        "lv": 68,
        "region": "旧战场",
        "chapter": 5,
        "area": "void_rift",
        "area_name": "裂隙谷地",
        "desc": "裂隙谷地的核心，一颗巨大的暗紫色心脏在虚空中跳动。裂隙巨像们守护着它——那是吞噬者的心脏。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_void_colossus",
                "裂隙巨像",
                "tank",
                68,
                [
                    "ms_zhong_ji",
                    "ms_xu_kong_beng_ta",
                    "ms_tun_shi"
                ],
                [
                    "mat_lie_xi_ju_xiang_he_xin"
                ]
            ],
            [
                "m_void_watcher",
                "谷口守望者",
                "tank",
                67,
                [
                    "ms_zhong_ji",
                    "ms_xu_kong_zhan",
                    "ms_dun_ji"
                ],
                [
                    "mat_xu_kong_hu_jia"
                ]
            ]
        ],
        "elite": [
            "e_void_overlord",
            "裂隙主宰",
            "elite",
            69,
            [
                "ms_xu_kong_beng_ta",
                "ms_an_ying_feng_bao",
                "ms_tun_shi"
            ],
            [
                "mat_lie_xi_zhu_zai_quan_zhang"
            ]
        ],
        "boss": [
            "b_void_devourer",
            "裂隙巨兽",
            "boss",
            70,
            [
                "ms_xu_kong_zhan",
                "ms_xu_kong_beng_ta",
                "ms_tun_shi",
                "ms_an_ying_feng_bao"
            ],
            [
                "mat_tun_shi_zhe_zhi_he"
            ]
        ],
        "npcs": []
    },
    {
        "id": "temple_hall",
        "name": "旧教团大厅",
        "lv": 71,
        "region": "旧战场",
        "chapter": 5,
        "area": "dark_temple",
        "area_name": "旧教团遗址",
        "desc": "旧教团遗址的前厅，曾经供奉光明神的殿堂如今爬满暗影。黑袍修士们低声吟唱着亵渎的祷词。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_dark_acolyte",
                "黑袍修士",
                "caster",
                71,
                [
                    "ms_an_ying_jian",
                    "ms_ji_qu"
                ],
                [
                    "mat_hei_an_jing_juan"
                ]
            ],
            [
                "m_abyss_servant",
                "教团仆从",
                "dps",
                72,
                [
                    "ms_zhao_ji",
                    "ms_an_ying_jian"
                ],
                [
                    "mat_shen_yuan_zhi_chen"
                ]
            ],
            [
                "m_fallen_paladin",
                "堕落骑士",
                "tank",
                73,
                [
                    "ms_pi_kan",
                    "ms_an_ying_jian",
                    "ms_dun_ji"
                ],
                [
                    "mat_duo_luo_sheng_hui"
                ]
            ]
        ],
        "elite": [
            "e_inquisitor",
            "审判官",
            "elite",
            74,
            [
                "ms_an_ying_jian",
                "ms_si_wang_zhi_wo",
                "ms_an_ying_feng_bao"
            ],
            [
                "mat_shen_pan_guan_zhi_yin"
            ]
        ],
        "boss": None,
        "npcs": []
    },
    {
        "id": "temple_aisle",
        "name": "忏悔回廊",
        "lv": 74,
        "region": "旧战场",
        "chapter": 5,
        "area": "dark_temple",
        "area_name": "旧教团遗址",
        "desc": "忏悔回廊，两侧是无数忏悔室的残骸。被囚禁的灵魂在此徘徊，发出永无止境的哀叹。",
        "type": "野外",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_penitent_wraith",
                "忏悔亡灵",
                "caster",
                74,
                [
                    "ms_ai_hao",
                    "ms_an_ying_jian"
                ],
                [
                    "mat_chan_hui_zhi_lei"
                ]
            ],
            [
                "m_abyss_priest",
                "黑袍牧师",
                "caster",
                75,
                [
                    "ms_an_ying_jian",
                    "ms_ji_qu",
                    "ms_si_wang_zhi_wo"
                ],
                [
                    "mat_shen_yuan_fa_zhu"
                ]
            ]
        ],
        "elite": [
            "e_heresy_executor",
            "处刑修士",
            "elite",
            76,
            [
                "ms_zhong_ji",
                "ms_an_ying_jian",
                "ms_an_ying_feng_bao"
            ],
            [
                "mat_chu_xing_zhe_zhi_fu"
            ]
        ],
        "boss": None,
        "npcs": [
            "npc_fallen_priest"
        ]
    },
    {
        "id": "temple_altar",
        "name": "旧教团祭坛",
        "lv": 78,
        "region": "旧战场",
        "chapter": 5,
        "area": "dark_temple",
        "area_name": "旧教团遗址",
        "desc": "旧教团祭坛，教团献祭的中心。祭坛之上，大祭司·克劳斯正在举行召唤仪式——他在召唤深渊真正的主人。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_abyss_ritualist",
                "教团祭祀",
                "caster",
                78,
                [
                    "ms_an_ying_jian",
                    "ms_di_yu_huo",
                    "ms_si_wang_zhi_wo"
                ],
                [
                    "mat_ji_si_zhi_huo"
                ]
            ],
            [
                "m_heresy_executor",
                "处刑修士",
                "dps",
                77,
                [
                    "ms_zhong_ji",
                    "ms_an_ying_jian",
                    "ms_an_ying_feng_bao"
                ],
                [
                    "mat_chu_xing_zhe_zhi_fu"
                ]
            ]
        ],
        "elite": [
            "e_archpriest",
            "教团大祭司",
            "elite",
            79,
            [
                "ms_di_yu_huo",
                "ms_an_ying_feng_bao",
                "ms_si_wang_zhi_wo"
            ],
            [
                "mat_da_ji_si_zhi_huan"
            ]
        ],
        "boss": [
            "b_abyss_pope",
            "大祭司·克劳斯",
            "boss",
            80,
            [
                "ms_di_yu_huo",
                "ms_an_ying_feng_bao",
                "ms_si_wang_zhi_wo",
                "ms_an_ying_qin_shi"
            ],
            [
                "mat_jiao_zong_quan_zhang"
            ]
        ],
        "npcs": []
    },
    {
        "id": "annih_front",
        "name": "白骨前线",
        "lv": 81,
        "region": "旧战场",
        "chapter": 5,
        "area": "annihilation",
        "area_name": "白骨平原",
        "desc": "白骨平原的前线阵地，大地被烧成焦黑。枯骨魔兵列成方阵，黑甲骑士的铁蹄震动着荒芜的地面。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_annih_soldier",
                "枯骨魔兵",
                "dps",
                81,
                [
                    "ms_zhong_ji",
                    "ms_an_ying_she_xian",
                    "ms_kuang_bao"
                ],
                [
                    "mat_yan_mie_sui_pian"
                ]
            ],
            [
                "m_doom_knight",
                "黑甲骑士",
                "tank",
                82,
                [
                    "ms_zhong_ji",
                    "ms_an_ying_she_xian",
                    "ms_dun_ji"
                ],
                [
                    "mat_zai_e_zhan_jia"
                ]
            ],
            [
                "m_soul_devourer",
                "噬魂怨灵",
                "caster",
                83,
                [
                    "ms_ji_qu",
                    "ms_an_ying_she_xian",
                    "ms_ai_hao"
                ],
                [
                    "mat_shi_hun_jie_jing"
                ]
            ]
        ],
        "elite": [
            "e_annih_vanguard",
            "枯骨先锋",
            "elite",
            84,
            [
                "ms_an_ying_she_xian",
                "ms_kuang_bao",
                "ms_an_ying_feng_bao"
            ],
            [
                "mat_xian_feng_zhan_qi"
            ]
        ],
        "boss": None,
        "npcs": []
    },
    {
        "id": "annih_field",
        "name": "白骨战场",
        "lv": 84,
        "region": "旧战场",
        "chapter": 5,
        "area": "annihilation",
        "area_name": "白骨平原",
        "desc": "白骨战场，尸骸遍野，破碎的旗帜在风中摇曳。枯骨魔将们在此督战，等待总攻的命令。",
        "type": "野外",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_annih_general",
                "枯骨魔将",
                "dps",
                84,
                [
                    "ms_an_ying_she_xian",
                    "ms_xu_kong_zhan",
                    "ms_kuang_bao"
                ],
                [
                    "mat_mo_jiang_zhi_ren"
                ]
            ],
            [
                "m_doom_knight",
                "黑甲骑士",
                "tank",
                83,
                [
                    "ms_zhong_ji",
                    "ms_an_ying_she_xian",
                    "ms_dun_ji"
                ],
                [
                    "mat_zai_e_zhan_jia"
                ]
            ]
        ],
        "elite": [
            "e_annih_lord",
            "枯骨领主",
            "elite",
            86,
            [
                "ms_an_ying_she_xian",
                "ms_xu_kong_beng_ta",
                "ms_kuang_bao"
            ],
            [
                "mat_ku_gu_ling_zhu_zhi_huan"
            ]
        ],
        "boss": None,
        "npcs": [
            "npc_annih_spy"
        ]
    },
    {
        "id": "annih_throne",
        "name": "旧王陵寝",
        "lv": 88,
        "region": "旧战场",
        "chapter": 5,
        "area": "annihilation",
        "area_name": "白骨平原",
        "desc": "旧王陵寝，亡灵大军的指挥中心。白骨君王端坐于骸骨堆成的王座上，静静等待最终时刻。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_annih_guard",
                "枯骨禁卫",
                "tank",
                88,
                [
                    "ms_an_ying_she_xian",
                    "ms_dun_ji",
                    "ms_kuang_bao"
                ],
                [
                    "mat_jin_wei_kai_jia"
                ]
            ],
            [
                "m_annih_general",
                "枯骨魔将",
                "dps",
                87,
                [
                    "ms_an_ying_she_xian",
                    "ms_xu_kong_zhan",
                    "ms_kuang_bao"
                ],
                [
                    "mat_mo_jiang_zhi_ren"
                ]
            ]
        ],
        "elite": [
            "e_silent_guard",
            "旧王亲卫",
            "elite",
            89,
            [
                "ms_an_ying_she_xian",
                "ms_an_ying_feng_bao",
                "ms_tun_shi"
            ],
            [
                "mat_si_ji_zhi_ren"
            ]
        ],
        "boss": [
            "b_silent_king",
            "白骨君王",
            "boss",
            90,
            [
                "ms_an_ying_she_xian",
                "ms_xu_kong_beng_ta",
                "ms_tun_shi",
                "ms_an_ying_qin_shi"
            ],
            [
                "mat_si_ji_wang_guan"
            ]
        ],
        "npcs": []
    },
    {
        "id": "divine_path",
        "name": "王国古道",
        "lv": 91,
        "region": "失落王国",
        "chapter": 6,
        "area": "divine_gate",
        "area_name": "失落王城",
        "desc": "通往失落王国的古道，云海在脚下翻涌。古道守卫们驻守在阶梯两侧，目光望向天空的尽头。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_sky_guard",
                "古道守卫",
                "tank",
                91,
                [
                    "ms_sheng_guang_zhan",
                    "ms_tian_fa",
                    "ms_dun_ji"
                ],
                [
                    "mat_tian_qiong_hu_jia"
                ]
            ],
            [
                "m_astral_messenger",
                "旧宫使者",
                "caster",
                92,
                [
                    "ms_tian_fa",
                    "ms_sheng_guang_zhan",
                    "ms_mo_fa_fei_dan"
                ],
                [
                    "mat_xing_jie_zhi_chen"
                ]
            ],
            [
                "m_divine_warrior",
                "古王战灵",
                "dps",
                93,
                [
                    "ms_sheng_guang_zhan",
                    "ms_tian_fa",
                    "ms_shen_wei"
                ],
                [
                    "mat_shen_yu_zhan_hun"
                ]
            ]
        ],
        "elite": [
            "e_astral_knight",
            "王家骑士长",
            "elite",
            94,
            [
                "ms_sheng_guang_zhan",
                "ms_tian_fa",
                "ms_shen_wei",
                "ms_sheng_guang_chong_feng"
            ],
            [
                "mat_xing_jie_qi_shi_jian"
            ]
        ],
        "boss": None,
        "npcs": []
    },
    {
        "id": "divine_hall",
        "name": "旧宫回廊",
        "lv": 93,
        "region": "失落王国",
        "chapter": 6,
        "area": "divine_gate",
        "area_name": "失落王城",
        "desc": "旧宫回廊，群星的墓地。旧宫贤者们在此守护着王国倾覆前的最后记忆。",
        "type": "野外",
        "shop": True,
        "healer": True,
        "hidden": False,
        "monsters": [
            [
                "m_astral_sage",
                "旧宫贤者",
                "caster",
                93,
                [
                    "ms_tian_fa",
                    "ms_bao_feng_xue",
                    "ms_shen_wei"
                ],
                [
                    "mat_xing_jie_fa_zhu"
                ]
            ],
            [
                "m_divine_warrior",
                "古王战灵",
                "dps",
                93,
                [
                    "ms_sheng_guang_zhan",
                    "ms_tian_fa",
                    "ms_shen_wei"
                ],
                [
                    "mat_shen_yu_zhan_hun"
                ]
            ]
        ],
        "elite": [
            "e_astral_judge",
            "旧宫裁决者",
            "elite",
            95,
            [
                "ms_tian_fa",
                "ms_shen_wei",
                "ms_wang_quan_zhi_li"
            ],
            [
                "mat_xing_jie_cai_jue_zhi_zhang"
            ]
        ],
        "boss": None,
        "npcs": [
            "npc_star_warden"
        ]
    },
    {
        "id": "divine_gate",
        "name": "失落王城之门",
        "lv": 95,
        "region": "失落王国",
        "chapter": 6,
        "area": "divine_gate",
        "area_name": "失落王城",
        "desc": "失落王城的大门，古老的石门刻满王国徽记。王城守望者手持长枪立于门前——门后，是旧日王国的战场。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_gate_guardian",
                "王城守卫",
                "tank",
                95,
                [
                    "ms_sheng_guang_zhan",
                    "ms_tian_fa",
                    "ms_dun_ji"
                ],
                [
                    "mat_men_fei_zhi_yao"
                ]
            ],
            [
                "m_astral_sage",
                "旧宫贤者",
                "caster",
                94,
                [
                    "ms_tian_fa",
                    "ms_bao_feng_xue",
                    "ms_shen_wei"
                ],
                [
                    "mat_xing_jie_fa_zhu"
                ]
            ]
        ],
        "elite": None,
        "boss": [
            "b_sky_warden",
            "王城守望者",
            "boss",
            96,
            [
                "ms_sheng_guang_zhan",
                "ms_tian_fa",
                "ms_shen_wei",
                "ms_wang_quan_zhi_li"
            ],
            [
                "mat_tian_qiong_zhi_guan"
            ]
        ],
        "npcs": []
    },
    {
        "id": "panth_court",
        "name": "先王庭院",
        "lv": 96,
        "region": "失落王国",
        "chapter": 6,
        "area": "pantheon",
        "area_name": "先王陵寝",
        "desc": "先王陵寝的庭院，先王的雕像沉默地矗立。古王残魂在庭院间游荡，暗影已经开始侵蚀这片旧地。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_divine_spirit",
                "古王残魂",
                "caster",
                96,
                [
                    "ms_tian_fa",
                    "ms_wang_quan_zhi_li",
                    "ms_shen_wei"
                ],
                [
                    "mat_shen_yu_jing_hua"
                ]
            ],
            [
                "m_chaos_servant",
                "暗影仆从",
                "dps",
                97,
                [
                    "ms_an_ying_qin_shi",
                    "ms_an_ying_she_xian"
                ],
                [
                    "mat_hun_dun_zhi_zha"
                ]
            ],
            [
                "m_god_echo",
                "先王残影",
                "tank",
                98,
                [
                    "ms_sheng_guang_zhan",
                    "ms_wang_quan_zhi_li"
                ],
                [
                    "mat_zhu_shen_yi_hui"
                ]
            ]
        ],
        "elite": [
            "e_god_messenger",
            "先王使者",
            "elite",
            99,
            [
                "ms_wang_quan_zhi_li",
                "ms_tian_fa",
                "ms_shen_wei",
                "ms_an_ying_qin_shi"
            ],
            [
                "mat_shi_zhe_zhi_jie"
            ]
        ],
        "boss": None,
        "npcs": [
            "npc_last_god"
        ]
    },
    {
        "id": "panth_hall",
        "name": "王座大殿",
        "lv": 98,
        "region": "失落王国",
        "chapter": 6,
        "area": "pantheon",
        "area_name": "先王陵寝",
        "desc": "王座大殿，先王铸造世界的殿堂。如今巫王盘踞于此，试图将整个大陆拖入永恒的黑暗。",
        "type": "核心",
        "shop": False,
        "healer": True,
        "hidden": False,
        "monsters": [
            [
                "m_creation_guard",
                "王座守卫",
                "tank",
                98,
                [
                    "ms_wang_quan_zhi_li",
                    "ms_sheng_guang_zhan",
                    "ms_dun_ji"
                ],
                [
                    "mat_chuang_shi_zhi_dun"
                ]
            ],
            [
                "m_god_echo",
                "先王残影",
                "tank",
                98,
                [
                    "ms_sheng_guang_zhan",
                    "ms_wang_quan_zhi_li"
                ],
                [
                    "mat_zhu_shen_yi_hui"
                ]
            ]
        ],
        "elite": None,
        "boss": [
            "b_chaos_lord",
            "巫王·莫里斯",
            "boss",
            100,
            [
                "ms_an_ying_qin_shi",
                "ms_an_ying_she_xian",
                "ms_wang_quan_zhi_li",
                "ms_an_ying_feng_bao",
                "灭世"
            ],
            [
                "mat_hun_dun_zhi_he"
            ]
        ],
        "npcs": []
    },
    {
        "id": "holy_city_gate",
        "name": "远境城门",
        "lv": 33,
        "region": "远境高地",
        "chapter": 4,
        "area": "holy",
        "area_name": "远境高原",
        "desc": "圣光王国的首都远境城，白色城墙高耸入云，城门前远境骑士列队巡逻。城门外的草甸上偶有野兽出没。",
        "type": "城镇外郊",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_radiant_wolf",
                "光耀狼",
                "speedster",
                32,
                [
                    "ms_si_yao",
                    "ms_hao_jiao"
                ],
                [
                    "mat_guang_yao_zhi_pi"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "holy_city_square",
        "name": "远境广场",
        "lv": 33,
        "region": "远境高地",
        "chapter": 4,
        "area": "holy",
        "area_name": "远境高原",
        "desc": "圣光王国的心脏，大教堂的钟声响彻全城。来自大陆各地的圣骑士与学者在此汇聚。",
        "type": "城镇区域",
        "shop": True,
        "healer": True,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_holy_king",
            "npc_holy_innkeeper"
        ]
    },
    {
        "id": "elf_city_gate",
        "name": "银月城门",
        "lv": 43,
        "region": "远境高地",
        "chapter": 4,
        "area": "elf_court",
        "area_name": "精灵王庭",
        "desc": "精灵王国首都银月城，城门由月光石雕琢而成，即便在白昼也泛着银辉。城外的森林依然低语。",
        "type": "城镇外郊",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_moon_panther",
                "月影豹",
                "speedster",
                42,
                [
                    "ms_zhao_ji",
                    "ms_hao_jiao"
                ],
                [
                    "mat_yue_ying_zhi_pi"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "elf_city_square",
        "name": "银月广场",
        "lv": 43,
        "region": "远境高地",
        "chapter": 4,
        "area": "elf_court",
        "area_name": "精灵王庭",
        "desc": "银月城的中心，生命之树在广场中央舒展枝叶。精灵工匠们在这里出售世代传承的技艺结晶。",
        "type": "城镇区域",
        "shop": True,
        "healer": True,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_elf_royal",
            "npc_elf_innkeeper"
        ]
    },
    {
        "id": "dragon_city_gate",
        "name": "龙喉堡城门",
        "lv": 53,
        "region": "远境高地",
        "chapter": 4,
        "area": "dragon_ridge",
        "area_name": "龙脊山脉",
        "desc": "龙裔王国在山巅开凿的要塞龙喉堡，城墙由熔岩冷却后的黑曜石筑成。门口的火盆昼夜不熄。",
        "type": "城镇外郊",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_dragonkin",
                "龙裔战士",
                "dps",
                53,
                [
                    "ms_pi_kan",
                    "ms_long_zhi_nu",
                    "ms_zhan_hou"
                ],
                [
                    "mat_long_yi_hui_ji"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "dragon_city_square",
        "name": "龙喉大厅",
        "lv": 53,
        "region": "远境高地",
        "chapter": 4,
        "area": "dragon_ridge",
        "area_name": "龙脊山脉",
        "desc": "龙裔的议事大厅，石柱上雕刻着龙族千年的战争史诗。矮人与龙裔的铁匠在这里锻造传奇兵器。",
        "type": "城镇区域",
        "shop": True,
        "healer": True,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_dragon_king",
            "npc_dragon_innkeeper"
        ]
    },
    {
        "id": "void_city_gate",
        "name": "虚空前哨大门",
        "lv": 63,
        "region": "旧战场",
        "chapter": 5,
        "area": "void_rift",
        "area_name": "裂隙谷地",
        "desc": "人类联军在裂隙谷地边缘建立的最后前哨，魔法屏障勉强挡住空间的扭曲。哨兵们面色凝重。",
        "type": "城镇外郊",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_void_minion",
                "废墟爪牙",
                "dps",
                63,
                [
                    "ms_zhao_ji",
                    "ms_xu_kong_zhan"
                ],
                [
                    "mat_xu_kong_zhi_zhao"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "void_city_square",
        "name": "前哨营地",
        "lv": 63,
        "region": "旧战场",
        "chapter": 5,
        "area": "void_rift",
        "area_name": "裂隙谷地",
        "desc": "前哨的核心营地，军需官与随军牧师在此为远征军提供补给。营火旁流传着关于战场中心的传说。",
        "type": "城镇区域",
        "shop": True,
        "healer": True,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_void_general",
            "npc_void_innkeeper"
        ]
    },
    {
        "id": "exile_camp_gate",
        "name": "悲怆营地入口",
        "lv": 73,
        "region": "旧战场",
        "chapter": 5,
        "area": "dark_temple",
        "area_name": "旧教团遗址",
        "desc": "从旧教团遗址逃出的流亡者建立的营地，用圣殿的碎石搭起简陋的围墙。这里是黑暗中的一盏孤灯。",
        "type": "城镇外郊",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_dark_acolyte",
                "黑袍修士",
                "caster",
                71,
                [
                    "ms_an_ying_jian",
                    "ms_ji_qu"
                ],
                [
                    "mat_hei_an_jing_juan"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "exile_camp_square",
        "name": "悲怆营火",
        "lv": 73,
        "region": "旧战场",
        "chapter": 5,
        "area": "dark_temple",
        "area_name": "旧教团遗址",
        "desc": "营地中央的营火，流亡者们围坐取暖。随军牧师在这里为伤者祈祷，商贩用残存的物资交换补给。",
        "type": "城镇区域",
        "shop": True,
        "healer": True,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_exile_leader",
            "npc_exile_innkeeper"
        ]
    },
    {
        "id": "iron_city_gate",
        "name": "铁壁城门",
        "lv": 83,
        "region": "旧战场",
        "chapter": 5,
        "area": "annihilation",
        "area_name": "白骨平原",
        "desc": "人类在白骨平原最后的堡垒铁壁城，三十米高的钢铁城墙是绝望中唯一的希望。城头炮火轰鸣。",
        "type": "城镇外郊",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_annih_soldier",
                "枯骨魔兵",
                "dps",
                81,
                [
                    "ms_zhong_ji",
                    "ms_an_ying_she_xian",
                    "ms_kuang_bao"
                ],
                [
                    "mat_yan_mie_sui_pian"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "iron_city_square",
        "name": "铁壁指挥所",
        "lv": 83,
        "region": "旧战场",
        "chapter": 5,
        "area": "annihilation",
        "area_name": "白骨平原",
        "desc": "铁壁城的指挥中枢，各大势力的联军代表在此共商对策。军需库里的每一件装备都弥足珍贵。",
        "type": "城镇区域",
        "shop": True,
        "healer": True,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_iron_marshal",
            "npc_iron_innkeeper"
        ]
    },
    {
        "id": "divine_city_gate",
        "name": "旧王城门",
        "lv": 93,
        "region": "失落王国",
        "chapter": 6,
        "area": "divine_gate",
        "area_name": "失落王城",
        "desc": "旧王城，悬浮在云海之上的白色巨城。古道守卫持戟而立，目光如星辰般冰冷。",
        "type": "城镇外郊",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_divine_warrior",
                "古王战灵",
                "dps",
                93,
                [
                    "ms_sheng_guang_zhan",
                    "ms_tian_fa",
                    "ms_shen_wei"
                ],
                [
                    "mat_shen_yu_zhan_hun"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "divine_city_square",
        "name": "天穹圣殿",
        "lv": 93,
        "region": "失落王国",
        "chapter": 6,
        "area": "divine_gate",
        "area_name": "失落王城",
        "desc": "旧王城的中心圣殿，光之柱直贯天际。先王遗留下的知识与神兵在这里等待凡人的继承。",
        "type": "城镇区域",
        "shop": True,
        "healer": True,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_divine_archon",
            "npc_divine_innkeeper"
        ]
    },
    {
        "id": "chaos_entry",
        "name": "陷落王都",
        "lv": 100,
        "region": "失落王国",
        "chapter": 6,
        "area": "chaos_depths",
        "area_name": "陷落王都",
        "desc": "巫王倒下之处，空间被撕开一道永久的裂隙。裂隙深处传来低沉的轰鸣——有什么东西还在苏醒。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": True,
        "monsters": [
            [
                "m_chaos_shade",
                "王都魔影",
                "speedster",
                100,
                [
                    "ms_an_ying_qin_shi",
                    "ms_an_ying_feng_bao"
                ],
                [
                    "mat_hun_dun_sui_pian"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    {
        "id": "chaos_depths",
        "name": "王都废墟",
        "lv": 100,
        "region": "失落王国",
        "chapter": 6,
        "area": "chaos_depths",
        "area_name": "陷落王都",
        "desc": "王都废墟，传说中王国的尽头。巫王之影悬浮在虚无之中——它自称是『第一次战争之前的古老意志』。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": True,
        "monsters": [
            [
                "m_chaos_avatar",
                "侵蚀化身",
                "dps",
                100,
                [
                    "ms_an_ying_qin_shi",
                    "ms_an_ying_she_xian",
                    "ms_tun_shi"
                ],
                [
                    "mat_hun_dun_sui_pian"
                ]
            ]
        ],
        "elite": None,
        "boss": [
            "b_chaos_transcendent",
            "巫王之影",
            "boss",
            100,
            [
                "ms_an_ying_qin_shi",
                "ms_an_ying_she_xian",
                "ms_tun_shi",
                "ms_wang_quan_zhi_li",
                "灭世",
                "ms_xu_kong_beng_ta"
            ],
            [
                "mat_chao_yue_zhi_he"
            ]
        ],
        "npcs": []
    }
]

# ========== 派生表 ==========
MAP_BY_ID = {
    "vila_gate": {
        "id": "vila_gate",
        "name": "维拉镇城门",
        "lv": 1,
        "region": "西境",
        "chapter": 1,
        "area": "vila",
        "area_name": "维拉镇",
        "desc": "维拉镇的东大门，商队与冒险者从这里进出。城门外的野地里偶尔有野兽出没。",
        "type": "城镇外郊",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_stray_dog",
                "野狗",
                "dps",
                1,
                [
                    "ms_si_yao"
                ],
                [
                    "mat_ye_gou_liao_ya"
                ]
            ],
            [
                "m_giant_rat",
                "巨型老鼠",
                "speedster",
                2,
                [
                    "ms_si_yao"
                ],
                [
                    "mat_shu_wei"
                ]
            ]
        ],
        "elite": [
            "e_bandit_leader",
            "山贼头目",
            "elite",
            4,
            [
                "ms_pi_kan",
                "ms_nu_hou"
            ],
            [
                "mat_shan_zei_hui_zhang"
            ]
        ],
        "boss": None,
        "npcs": []
    },
    "vila_street": {
        "id": "vila_street",
        "name": "维拉镇中央大街",
        "lv": 1,
        "region": "西境",
        "chapter": 1,
        "area": "vila",
        "area_name": "维拉镇",
        "desc": "石板铺就的主街，两侧商铺林立，叫卖声此起彼伏。铁匠铺的炉火昼夜不熄。",
        "type": "城镇区域",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_blacksmith"
        ]
    },
    "vila_square": {
        "id": "vila_square",
        "name": "维拉镇中心广场",
        "lv": 1,
        "region": "西境",
        "chapter": 1,
        "area": "vila",
        "area_name": "维拉镇",
        "desc": "城镇的心脏，喷泉旁竖着公告板，镇长府邸就在广场北侧。新来的冒险者都在这里报到。",
        "type": "城镇区域",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_mayor",
            "npc_bard"
        ]
    },
    "vila_tavern": {
        "id": "vila_tavern",
        "name": "维拉镇酒馆·醉熊",
        "lv": 1,
        "region": "西境",
        "chapter": 1,
        "area": "vila",
        "area_name": "维拉镇",
        "desc": "整个小镇最热闹的地方，麦酒与冒险故事一样管够。赏金猎人喜欢在这里物色搭档。",
        "type": "城镇区域",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_bartender",
            "npc_bounty"
        ]
    },
    "vila_inn": {
        "id": "vila_inn",
        "name": "维拉镇旅店·星夜",
        "lv": 1,
        "region": "西境",
        "chapter": 1,
        "area": "vila",
        "area_name": "维拉镇",
        "desc": "干净温暖的旅店，老板娘玛丽总是笑眯眯的。在这里住宿能恢复全部状态。",
        "type": "城镇区域",
        "shop": False,
        "healer": True,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_innkeeper"
        ]
    },
    "emerald_edge": {
        "id": "emerald_edge",
        "name": "翡翠森林边缘",
        "lv": 4,
        "region": "西境",
        "chapter": 1,
        "area": "emerald",
        "area_name": "翡翠森林",
        "desc": "森林的边缘地带，阳光还能透过树冠。林间传来狼嚎，深入请小心。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_forest_wolf",
                "森林狼",
                "dps",
                4,
                [
                    "ms_si_yao",
                    "ms_hao_jiao"
                ],
                [
                    "mat_lang_pi"
                ]
            ],
            [
                "m_venom_spider",
                "毒蜘蛛",
                "speedster",
                5,
                [
                    "ms_du_yao"
                ],
                [
                    "mat_zhi_zhu_du_nang"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "emerald_trail": {
        "id": "emerald_trail",
        "name": "翡翠林间小径",
        "lv": 5,
        "region": "西境",
        "chapter": 1,
        "area": "emerald",
        "area_name": "翡翠森林",
        "desc": "精灵走出来的小径，树木会说话，魔法的光芒在林间流淌。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_venom_spider",
                "毒蜘蛛",
                "speedster",
                5,
                [
                    "ms_du_yao"
                ],
                [
                    "mat_zhi_zhu_du_nang"
                ]
            ],
            [
                "m_greensprite",
                "绿妖精",
                "caster",
                6,
                [
                    "ms_mo_fa_fei_dan"
                ],
                [
                    "mat_yao_jing_zhi_chen"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "emerald_heart": {
        "id": "emerald_heart",
        "name": "翡翠森林之心",
        "lv": 6,
        "region": "西境",
        "chapter": 1,
        "area": "emerald",
        "area_name": "翡翠森林",
        "desc": "森林最古老的神木所在，精灵的圣域。守护这里的远古圣鹿不容侵犯。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_greensprite",
                "绿妖精",
                "caster",
                6,
                [
                    "ms_mo_fa_fei_dan"
                ],
                [
                    "mat_yao_jing_zhi_chen"
                ]
            ],
            [
                "m_forest_wolf",
                "森林狼",
                "dps",
                6,
                [
                    "ms_si_yao",
                    "ms_hao_jiao"
                ],
                [
                    "mat_lang_pi"
                ]
            ]
        ],
        "elite": [
            "e_forest_treant",
            "远古树人",
            "elite",
            7,
            [
                "ms_zhong_ji",
                "ms_zi_ran_zhu_fu"
            ],
            [
                "mat_yuan_gu_shu_pi"
            ]
        ],
        "boss": [
            "b_ancient_elk",
            "远古圣鹿",
            "boss",
            8,
            [
                "ms_sheng_guang_chong_feng",
                "ms_zi_ran_zhu_fu",
                "ms_jian_ta"
            ],
            [
                "mat_sheng_lu_jiao"
            ]
        ],
        "npcs": [
            "npc_druid"
        ]
    },
    "stonefist_camp": {
        "id": "stonefist_camp",
        "name": "石拳营地",
        "lv": 7,
        "region": "西境",
        "chapter": 1,
        "area": "stonefist",
        "area_name": "石拳丘陵",
        "desc": "矮人在丘陵脚下搭建的营地，篝火与铁砧声不断。矿洞方向常有地精的动静。",
        "type": "城镇区域",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_goblin_grunt",
                "地精步兵",
                "dps",
                7,
                [
                    "ms_pi_kan"
                ],
                [
                    "mat_di_jing_er_duo"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_dwarf_elder"
        ]
    },
    "stonefist_mine": {
        "id": "stonefist_mine",
        "name": "矿洞入口",
        "lv": 8,
        "region": "西境",
        "chapter": 1,
        "area": "stonefist",
        "area_name": "石拳丘陵",
        "desc": "矮人世代开采的矿脉洞口，如今被地精占领，洞内幽深黑暗。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_goblin_grunt",
                "地精步兵",
                "dps",
                7,
                [
                    "ms_pi_kan"
                ],
                [
                    "mat_di_jing_er_duo"
                ]
            ],
            [
                "m_mine_bat",
                "矿洞蝙蝠",
                "speedster",
                8,
                [
                    "ms_fu_chong"
                ],
                [
                    "mat_bian_fu_yi"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "stonefist_deep": {
        "id": "stonefist_deep",
        "name": "矿洞深处",
        "lv": 9,
        "region": "西境",
        "chapter": 1,
        "area": "stonefist",
        "area_name": "石拳丘陵",
        "desc": "矿洞最深处，巨大的蛇影在黑暗中游弋。地精萨满在这里举行诡异的仪式。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_tunnel_snake",
                "洞穴巨蛇",
                "tank",
                9,
                [
                    "ms_du_yao",
                    "ms_chan_rao"
                ],
                [
                    "mat_she_lin"
                ]
            ],
            [
                "m_mine_bat",
                "矿洞蝙蝠",
                "speedster",
                9,
                [
                    "ms_fu_chong"
                ],
                [
                    "mat_bian_fu_yi"
                ]
            ]
        ],
        "elite": [
            "e_goblin_shaman",
            "地精萨满",
            "elite",
            10,
            [
                "ms_an_ying_jian",
                "ms_zhao_huan"
            ],
            [
                "mat_sa_man_tu_teng"
            ]
        ],
        "boss": [
            "b_tunnel_king",
            "隧洞之王",
            "boss",
            11,
            [
                "ms_zhong_ji",
                "ms_nu_hou",
                "ms_chen_mo_jian_xiao",
                "ms_di_dong"
            ],
            [
                "mat_di_jing_wang_guan"
            ]
        ],
        "npcs": []
    },
    "gloom_edge": {
        "id": "gloom_edge",
        "name": "幽暗沼泽边缘",
        "lv": 10,
        "region": "腐土",
        "chapter": 2,
        "area": "gloom",
        "area_name": "幽暗沼泽",
        "desc": "沼泽的最外围，瘴气开始弥漫，脚下的泥土松软而危险。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_swamp_zombie",
                "沼泽僵尸",
                "tank",
                10,
                [
                    "ms_zhao_ji"
                ],
                [
                    "mat_jiang_shi_fu_rou"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "gloom_mire": {
        "id": "gloom_mire",
        "name": "泥沼深处",
        "lv": 11,
        "region": "腐土",
        "chapter": 2,
        "area": "gloom",
        "area_name": "幽暗沼泽",
        "desc": "越深入，瘴气越浓。腐尸爬行者在泥水中蠕动着，鬼魂的哀嚎此起彼伏。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_bog_ghost",
                "沼泽鬼魂",
                "caster",
                11,
                [
                    "ms_ji_qu",
                    "ms_ai_hao"
                ],
                [
                    "mat_gui_hun_jing_hua"
                ]
            ],
            [
                "m_corpse_crawler",
                "腐尸爬行者",
                "dps",
                12,
                [
                    "ms_zhao_ji",
                    "ms_du_yao"
                ],
                [
                    "mat_pa_xing_chong_ke"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "gloom_heart": {
        "id": "gloom_heart",
        "name": "沼泽之心",
        "lv": 12,
        "region": "腐土",
        "chapter": 2,
        "area": "gloom",
        "area_name": "幽暗沼泽",
        "desc": "亡灵天灾的腐化源头，骸骨术士的祭坛立于此地，腐朽领主盘踞其上。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_corpse_crawler",
                "腐尸爬行者",
                "dps",
                12,
                [
                    "ms_zhao_ji",
                    "ms_du_yao"
                ],
                [
                    "mat_pa_xing_chong_ke"
                ]
            ],
            [
                "m_swamp_zombie",
                "沼泽僵尸",
                "tank",
                12,
                [
                    "ms_zhao_ji"
                ],
                [
                    "mat_jiang_shi_fu_rou"
                ]
            ]
        ],
        "elite": [
            "e_bone_warlock",
            "骸骨术士",
            "elite",
            13,
            [
                "ms_an_ying_jian",
                "ms_zhao_hun",
                "ms_ji_qu"
            ],
            [
                "mat_shu_shi_he_xin"
            ]
        ],
        "boss": [
            "b_decay_lord",
            "腐朽领主",
            "boss",
            14,
            [
                "ms_zhao_ji",
                "ms_fu_xi",
                "ms_zhao_hun",
                "ms_kuang_bao"
            ],
            [
                "mat_fu_xiu_zhi_ren"
            ]
        ],
        "npcs": []
    },
    "redridge_field": {
        "id": "redridge_field",
        "name": "赤脊旷野",
        "lv": 13,
        "region": "腐土",
        "chapter": 2,
        "area": "redridge",
        "area_name": "赤脊荒原",
        "desc": "赤色岩石覆盖的旷野，兽人部落的巡逻队在此出没，座狼的嚎叫撕破寂静。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_orc_grunt",
                "兽人步兵",
                "dps",
                13,
                [
                    "ms_pi_kan",
                    "ms_nu_hou"
                ],
                [
                    "mat_shou_ren_liao_ya"
                ]
            ],
            [
                "m_warg",
                "座狼",
                "speedster",
                14,
                [
                    "ms_si_yao",
                    "ms_hao_jiao"
                ],
                [
                    "mat_zuo_lang_quan_chi"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "redridge_ridge": {
        "id": "redridge_ridge",
        "name": "赤脊山脊",
        "lv": 15,
        "region": "腐土",
        "chapter": 2,
        "area": "redridge",
        "area_name": "赤脊荒原",
        "desc": "陡峭的山脊上风声猎猎，鹰身女妖在天空中盘旋，随时准备俯冲。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_harpy",
                "鹰身女妖",
                "caster",
                15,
                [
                    "ms_fu_chong",
                    "ms_jian_xiao"
                ],
                [
                    "mat_nv_yao_zhi_yu"
                ]
            ],
            [
                "m_warg",
                "座狼",
                "speedster",
                15,
                [
                    "ms_si_yao",
                    "ms_hao_jiao"
                ],
                [
                    "mat_zuo_lang_quan_chi"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "redridge_camp": {
        "id": "redridge_camp",
        "name": "战歌营地",
        "lv": 16,
        "region": "腐土",
        "chapter": 2,
        "area": "redridge",
        "area_name": "赤脊荒原",
        "desc": "战歌部落的大营，旌旗猎猎，兽人狂战士在营地中央的图腾柱下磨刀。",
        "type": "核心",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_orc_grunt",
                "兽人步兵",
                "dps",
                16,
                [
                    "ms_pi_kan",
                    "ms_nu_hou"
                ],
                [
                    "mat_shou_ren_liao_ya"
                ]
            ],
            [
                "m_harpy",
                "鹰身女妖",
                "caster",
                16,
                [
                    "ms_fu_chong",
                    "ms_jian_xiao"
                ],
                [
                    "mat_nv_yao_zhi_yu"
                ]
            ]
        ],
        "elite": [
            "e_orc_berserker",
            "兽人狂战士",
            "elite",
            16,
            [
                "ms_pi_kan",
                "ms_kuang_bao",
                "ms_zhong_ji"
            ],
            [
                "mat_kuang_zhan_zhi_xin"
            ]
        ],
        "boss": [
            "b_warband_chief",
            "战歌部落酋长",
            "boss",
            17,
            [
                "ms_pi_kan",
                "ms_zhan_hou",
                "ms_zhong_ji",
                "ms_kuang_bao"
            ],
            [
                "mat_qiu_zhang_zhan_ren"
            ]
        ],
        "npcs": [
            "npc_orc_prisoner"
        ]
    },
    "blackrock_gate": {
        "id": "blackrock_gate",
        "name": "黑石城门",
        "lv": 16,
        "region": "腐土",
        "chapter": 2,
        "area": "blackrock",
        "area_name": "黑石城废墟",
        "desc": "曾是人类王国都城的东门，如今城门倒塌，骷髅卫兵在废墟间巡游。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_skeleton_guard",
                "骷髅卫兵",
                "tank",
                16,
                [
                    "ms_pi_kan",
                    "ms_dun_ji"
                ],
                [
                    "mat_gu_pian"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "blackrock_street": {
        "id": "blackrock_street",
        "name": "死城大街",
        "lv": 17,
        "region": "腐土",
        "chapter": 2,
        "area": "blackrock",
        "area_name": "黑石城废墟",
        "desc": "曾经繁华的主街，如今只剩下断壁残垣。食尸鬼在阴影中啃食着什么。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_ghoul",
                "食尸鬼",
                "dps",
                17,
                [
                    "ms_zhao_ji",
                    "ms_tun_shi"
                ],
                [
                    "mat_shi_shi_gui_zhi_zhao"
                ]
            ],
            [
                "m_spectre",
                "怨灵",
                "caster",
                18,
                [
                    "ms_ji_qu",
                    "ms_ai_hao",
                    "ms_fu_shen"
                ],
                [
                    "mat_ling_hun_sui_pian"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "blackrock_keep": {
        "id": "blackrock_keep",
        "name": "黑石王座",
        "lv": 18,
        "region": "腐土",
        "chapter": 2,
        "area": "blackrock",
        "area_name": "黑石城废墟",
        "desc": "旧王国的王宫大殿，巫妖宰相的寒冰王座矗立于此，死亡骑士侍立两侧。",
        "type": "核心",
        "shop": False,
        "healer": True,
        "hidden": False,
        "monsters": [
            [
                "m_skeleton_guard",
                "骷髅卫兵",
                "tank",
                18,
                [
                    "ms_pi_kan",
                    "ms_dun_ji"
                ],
                [
                    "mat_gu_pian"
                ]
            ],
            [
                "m_spectre",
                "怨灵",
                "caster",
                18,
                [
                    "ms_ji_qu",
                    "ms_ai_hao",
                    "ms_fu_shen"
                ],
                [
                    "mat_ling_hun_sui_pian"
                ]
            ]
        ],
        "elite": [
            "e_death_knight",
            "死亡骑士",
            "elite",
            19,
            [
                "ms_pi_kan",
                "ms_si_wang_zhi_wo",
                "ms_an_ying_jian",
                "ms_kuang_bao"
            ],
            [
                "mat_si_wang_qi_shi_zhi_ren"
            ]
        ],
        "boss": [
            "b_lich_vizier",
            "巫妖宰相",
            "boss",
            20,
            [
                "ms_an_ying_jian",
                "ms_zhao_hun",
                "ms_ji_qu",
                "ms_wu_yao_qi_she"
            ],
            [
                "mat_wu_yao_fa_zhang"
            ]
        ],
        "npcs": [
            "npc_ghost_knight"
        ]
    },
    "magma_gorge": {
        "id": "magma_gorge",
        "name": "熔岩峡谷",
        "lv": 19,
        "region": "魔渊",
        "chapter": 3,
        "area": "magma",
        "area_name": "熔岩裂谷",
        "desc": "深渊恶魔撕开大地的裂隙，岩浆在脚下奔涌，火元素从熔岩中升起。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_fire_elemental",
                "火元素",
                "caster",
                19,
                [
                    "ms_huo_qiu",
                    "ms_zhuo_shao"
                ],
                [
                    "mat_huo_yan_he_xin"
                ]
            ],
            [
                "m_imp",
                "小恶魔",
                "speedster",
                20,
                [
                    "ms_huo_qiu",
                    "ms_jian_xiao"
                ],
                [
                    "mat_e_mo_zhi_jiao"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "magma_heart": {
        "id": "magma_heart",
        "name": "熔岩核心",
        "lv": 21,
        "region": "魔渊",
        "chapter": 3,
        "area": "magma",
        "area_name": "熔岩裂谷",
        "desc": "裂谷的最深处，岩浆瀑布倾泻而下。熔岩暴君在此沉睡，火焰巨人看守着它的梦。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_lava_hound",
                "熔岩猎犬",
                "tank",
                21,
                [
                    "ms_si_yao",
                    "ms_zhuo_shao",
                    "ms_chong_zhuang"
                ],
                [
                    "mat_rong_yan_shi"
                ]
            ],
            [
                "m_imp",
                "小恶魔",
                "speedster",
                21,
                [
                    "ms_huo_qiu",
                    "ms_jian_xiao"
                ],
                [
                    "mat_e_mo_zhi_jiao"
                ]
            ]
        ],
        "elite": [
            "e_flame_giant",
            "火焰巨人",
            "elite",
            22,
            [
                "ms_zhong_ji",
                "ms_huo_qiu",
                "ms_zhuo_shao",
                "ms_lie_yan_zhen_ji"
            ],
            [
                "mat_ju_ren_yu_jin"
            ]
        ],
        "boss": [
            "b_magma_tyrant",
            "熔岩暴君",
            "boss",
            23,
            [
                "ms_huo_qiu",
                "ms_lie_yan_zhen_ji",
                "ms_zhuo_shao",
                "ms_yan_jiang_pen_fa"
            ],
            [
                "mat_rong_yan_zhi_jian"
            ]
        ],
        "npcs": []
    },
    "tundra_field": {
        "id": "tundra_field",
        "name": "冰封旷野",
        "lv": 22,
        "region": "魔渊",
        "chapter": 3,
        "area": "tundra",
        "area_name": "冰封苔原",
        "desc": "极北的冰雪世界，暴风雪中传来冰原狼的低吼，冰霜巨魔在雪丘间游荡。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_ice_wolf",
                "冰原狼",
                "dps",
                22,
                [
                    "ms_si_yao",
                    "ms_bing_yao"
                ],
                [
                    "mat_bing_yuan_mao_pi"
                ]
            ],
            [
                "m_frost_troll",
                "冰霜巨魔",
                "tank",
                23,
                [
                    "ms_zhong_ji",
                    "ms_zai_sheng",
                    "ms_bing_yao"
                ],
                [
                    "mat_ju_mo_xue_rou"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "tundra_cave": {
        "id": "tundra_cave",
        "name": "冰霜洞穴",
        "lv": 24,
        "region": "魔渊",
        "chapter": 3,
        "area": "tundra",
        "area_name": "冰封苔原",
        "desc": "冰川下的巨大洞穴，冰晶折射着幽蓝的光。霜裔亚龙就在这里筑巢。",
        "type": "核心",
        "shop": False,
        "healer": True,
        "hidden": False,
        "monsters": [
            [
                "m_snow_wraith",
                "雪魅",
                "caster",
                24,
                [
                    "ms_ji_qu",
                    "ms_bing_yao",
                    "ms_bao_feng_xue"
                ],
                [
                    "mat_xue_zhi_jing_hua"
                ]
            ],
            [
                "m_frost_troll",
                "冰霜巨魔",
                "tank",
                24,
                [
                    "ms_zhong_ji",
                    "ms_zai_sheng",
                    "ms_bing_yao"
                ],
                [
                    "mat_ju_mo_xue_rou"
                ]
            ]
        ],
        "elite": [
            "e_glacier_golem",
            "冰川魔像",
            "elite",
            25,
            [
                "ms_zhong_ji",
                "ms_bing_qiang",
                "ms_shuang_xi"
            ],
            [
                "mat_yong_heng_zhi_bing"
            ]
        ],
        "boss": [
            "b_frost_wyrm",
            "霜裔亚龙",
            "boss",
            26,
            [
                "ms_shuang_xi",
                "ms_bao_feng_xue",
                "ms_si_yao",
                "ms_long_zhi_nu"
            ],
            [
                "mat_shuang_long_zhi_ya"
            ]
        ],
        "npcs": []
    },
    "stormpeak_path": {
        "id": "stormpeak_path",
        "name": "风暴山道",
        "lv": 25,
        "region": "魔渊",
        "chapter": 3,
        "area": "stormpeak",
        "area_name": "风暴之巅",
        "desc": "通往山巅的陡峭山道，终年雷暴，雷电元素在云层中翻涌，巨鹰盘旋警戒。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_thunder_elemental",
                "雷电元素",
                "caster",
                25,
                [
                    "ms_shan_dian_jian",
                    "ms_lei_ji"
                ],
                [
                    "mat_lei_dian_he_xin"
                ]
            ],
            [
                "m_giant_eagle",
                "巨鹰",
                "speedster",
                26,
                [
                    "ms_fu_chong",
                    "ms_feng_ren"
                ],
                [
                    "mat_ju_ying_ling_yu"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "stormpeak_peak": {
        "id": "stormpeak_peak",
        "name": "风暴之巅",
        "lv": 27,
        "region": "魔渊",
        "chapter": 3,
        "area": "stormpeak",
        "area_name": "风暴之巅",
        "desc": "世界的屋脊，雷暴的中心。风暴巨人王手持雷霆之锤，君临此处。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_storm_serpent",
                "风暴巨蛇",
                "tank",
                27,
                [
                    "ms_shan_dian_jian",
                    "ms_chan_rao",
                    "ms_lei_ji"
                ],
                [
                    "mat_feng_bao_she_lin"
                ]
            ],
            [
                "m_giant_eagle",
                "巨鹰",
                "speedster",
                27,
                [
                    "ms_fu_chong",
                    "ms_feng_ren"
                ],
                [
                    "mat_ju_ying_ling_yu"
                ]
            ]
        ],
        "elite": [
            "e_sky_hunter",
            "苍穹猎手",
            "elite",
            28,
            [
                "ms_feng_ren",
                "ms_shan_dian_jian",
                "ms_feng_bao_zhao_huan"
            ],
            [
                "mat_cang_qiong_zhi_ren"
            ]
        ],
        "boss": [
            "b_storm_giant",
            "风暴巨人王",
            "boss",
            29,
            [
                "ms_lei_ji",
                "ms_feng_bao_zhao_huan",
                "ms_shan_dian_jian",
                "ms_bao_feng_zhi_nu"
            ],
            [
                "mat_lei_ting_zhi_chui"
            ]
        ],
        "npcs": [
            "npc_sky_hermit"
        ]
    },
    "shadow_gate": {
        "id": "shadow_gate",
        "name": "暗影城门",
        "lv": 28,
        "region": "魔渊",
        "chapter": 3,
        "area": "shadow_city",
        "area_name": "暗影之城",
        "desc": "深渊之门前的恶魔之城，城门由暗影恶魔把守，邪恶的气息扑面而来。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_shadow_demon",
                "暗影恶魔",
                "caster",
                28,
                [
                    "ms_an_ying_jian",
                    "ms_zhao_ji",
                    "ms_ji_qu"
                ],
                [
                    "mat_an_ying_sui_pian"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "shadow_street": {
        "id": "shadow_street",
        "name": "暗影大街",
        "lv": 29,
        "region": "魔渊",
        "chapter": 3,
        "area": "shadow_city",
        "area_name": "暗影之城",
        "desc": "恶魔的集市大街，灾厄小魔在屋檐间跳跃，虚空掠夺者盯上了每一个闯入者。",
        "type": "野外",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_doom_imp",
                "灾厄小魔",
                "speedster",
                29,
                [
                    "ms_huo_qiu",
                    "ms_an_ying_jian",
                    "ms_jian_xiao"
                ],
                [
                    "mat_zai_e_zhi_xin"
                ]
            ],
            [
                "m_void_reaver",
                "虚空掠夺者",
                "dps",
                30,
                [
                    "ms_zhao_ji",
                    "ms_xu_kong_zhan",
                    "ms_kuang_bao"
                ],
                [
                    "mat_xu_kong_sui_pian"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "shadow_keep": {
        "id": "shadow_keep",
        "name": "暗影王座",
        "lv": 30,
        "region": "魔渊",
        "chapter": 3,
        "area": "shadow_city",
        "area_name": "暗影之城",
        "desc": "暗影主教的黑曜石王座大厅，深渊领主们在此匍匐。这里是深渊之门最后的屏障。",
        "type": "核心",
        "shop": False,
        "healer": True,
        "hidden": False,
        "monsters": [
            [
                "m_void_reaver",
                "虚空掠夺者",
                "dps",
                30,
                [
                    "ms_zhao_ji",
                    "ms_xu_kong_zhan",
                    "ms_kuang_bao"
                ],
                [
                    "mat_xu_kong_sui_pian"
                ]
            ],
            [
                "m_shadow_demon",
                "暗影恶魔",
                "caster",
                30,
                [
                    "ms_an_ying_jian",
                    "ms_zhao_ji",
                    "ms_ji_qu"
                ],
                [
                    "mat_an_ying_sui_pian"
                ]
            ]
        ],
        "elite": [
            "e_pit_lord",
            "深渊领主",
            "elite",
            30,
            [
                "ms_zhong_ji",
                "ms_huo_qiu",
                "ms_xu_kong_zhan",
                "ms_di_yu_huo"
            ],
            [
                "mat_shen_yuan_hui_ji"
            ]
        ],
        "boss": [
            "b_shadow_archon",
            "暗影主教",
            "boss",
            30,
            [
                "ms_an_ying_jian",
                "ms_xu_kong_zhan",
                "ms_ji_qu",
                "ms_an_ying_feng_bao"
            ],
            [
                "mat_an_ying_zhi_guan"
            ]
        ],
        "npcs": []
    },
    "abyss_plain": {
        "id": "abyss_plain",
        "name": "深渊荒原",
        "lv": 30,
        "region": "魔渊",
        "chapter": 3,
        "area": "abyss_gate",
        "area_name": "深渊之门",
        "desc": "深渊之门前的荒原，大地龟裂，虚空之力扭曲着空间。恶魔大军在此列阵。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_abyss_guardian",
                "深渊守卫",
                "tank",
                30,
                [
                    "ms_pi_kan",
                    "ms_xu_kong_zhan",
                    "ms_dun_ji"
                ],
                [
                    "mat_shen_yuan_jing_gang"
                ]
            ],
            [
                "m_void_hound",
                "虚空猎犬",
                "speedster",
                30,
                [
                    "ms_si_yao",
                    "ms_xu_kong_zhan",
                    "ms_hao_jiao"
                ],
                [
                    "mat_xu_kong_liao_ya"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "abyss_gate": {
        "id": "abyss_gate",
        "name": "深渊之门",
        "lv": 30,
        "region": "魔渊",
        "chapter": 3,
        "area": "abyss_gate",
        "area_name": "深渊之门",
        "desc": "魔王所在的最终战场，魔王·阿兹莫丹立于深渊之门下，大陆的命运在此一决。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_demon_herald",
                "恶魔先驱",
                "caster",
                30,
                [
                    "ms_huo_qiu",
                    "ms_an_ying_jian",
                    "ms_di_yu_huo"
                ],
                [
                    "mat_xian_qu_hao_jiao"
                ]
            ],
            [
                "m_void_hound",
                "虚空猎犬",
                "speedster",
                30,
                [
                    "ms_si_yao",
                    "ms_xu_kong_zhan",
                    "ms_hao_jiao"
                ],
                [
                    "mat_xu_kong_liao_ya"
                ]
            ]
        ],
        "elite": None,
        "boss": [
            "b_dark_lord",
            "魔王·阿兹莫丹",
            "boss",
            30,
            [
                "ms_xu_kong_zhan",
                "ms_di_yu_huo",
                "ms_an_ying_feng_bao",
                "ms_hui_mie_zhi_ji"
            ],
            [
                "mat_hei_an_jun_zhu_zhi_ren"
            ]
        ],
        "npcs": []
    },
    "mithril_hall": {
        "id": "mithril_hall",
        "name": "秘银大厅",
        "lv": 26,
        "region": "魔渊",
        "chapter": 3,
        "area": "mithril",
        "area_name": "秘银遗迹",
        "desc": "上古矮人王的宝库大厅，秘银魔像沿着走廊巡视，符文骑士守卫着每一道门。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": True,
        "monsters": [
            [
                "m_mithril_golem",
                "秘银魔像",
                "tank",
                26,
                [
                    "ms_zhong_ji",
                    "ms_dun_ji"
                ],
                [
                    "mat_mi_yin_kuang_shi"
                ]
            ],
            [
                "m_runebound_knight",
                "符文骑士",
                "dps",
                28,
                [
                    "ms_pi_kan",
                    "ms_fu_wen_bao_fa",
                    "ms_dun_ji"
                ],
                [
                    "mat_fu_wen_sui_pian"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "mithril_vault": {
        "id": "mithril_vault",
        "name": "秘银宝库",
        "lv": 30,
        "region": "魔渊",
        "chapter": 3,
        "area": "mithril",
        "area_name": "秘银遗迹",
        "desc": "宝库的最深处，矮人王冠静静躺在王座上，宝藏守护者寸步不离。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": True,
        "monsters": [
            [
                "m_treasure_guardian",
                "宝藏守护者",
                "boss",
                30,
                [
                    "ms_zhong_ji",
                    "ms_xu_kong_zhan",
                    "ms_nu_hou"
                ],
                [
                    "mat_bao_cang_yao_shi"
                ]
            ]
        ],
        "elite": [
            "e_ancient_dwarf",
            "上古矮人王魂",
            "elite",
            30,
            [
                "ms_zhong_ji",
                "ms_fu_wen_bao_fa",
                "ms_zhan_hou",
                "ms_xian_zu_zhi_nu"
            ],
            [
                "mat_ai_ren_wang_zhi_jie"
            ]
        ],
        "boss": [
            "b_dwarf_king",
            "秘银之王",
            "boss",
            30,
            [
                "ms_zhong_ji",
                "ms_fu_wen_bao_fa",
                "ms_xian_zu_zhi_nu",
                "ms_mi_yin_zhen_ji"
            ],
            [
                "mat_mi_yin_wang_guan"
            ]
        ],
        "npcs": []
    },
    "holy_field": {
        "id": "holy_field",
        "name": "远境草甸",
        "lv": 31,
        "region": "远境高地",
        "chapter": 4,
        "area": "holy",
        "area_name": "远境高原",
        "desc": "远境高原的入口草甸，圣光透过云层洒下，却掩盖不住空气中弥漫的异样气息。光耀狼在草丛间游荡。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_holy_hawk",
                "远境猎鹰",
                "dps",
                31,
                [
                    "ms_fu_chong",
                    "ms_feng_ren"
                ],
                [
                    "mat_sheng_guang_yu_mao"
                ]
            ],
            [
                "m_radiant_wolf",
                "光耀狼",
                "speedster",
                32,
                [
                    "ms_si_yao",
                    "ms_hao_jiao"
                ],
                [
                    "mat_guang_yao_zhi_pi"
                ]
            ],
            [
                "m_holy_deer",
                "远境麋鹿",
                "tank",
                33,
                [
                    "ms_chong_zhuang",
                    "ms_zi_ran_zhu_fu"
                ],
                [
                    "mat_sheng_hui_lu_jiao"
                ]
            ]
        ],
        "elite": [
            "e_holy_knight",
            "远境骑士",
            "elite",
            34,
            [
                "ms_pi_kan",
                "ms_sheng_guang_zhan",
                "ms_dun_ji"
            ],
            [
                "mat_sheng_guang_hui_zhang"
            ]
        ],
        "boss": None,
        "npcs": []
    },
    "holy_altar": {
        "id": "holy_altar",
        "name": "远境祭坛",
        "lv": 34,
        "region": "远境高地",
        "chapter": 4,
        "area": "holy",
        "area_name": "远境高原",
        "desc": "古老的圣光祭坛，信徒们曾在此祈祷。如今祭坛被暗影侵蚀，教会修士们神色诡异地低声吟唱。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_temple_adept",
                "教会修士",
                "caster",
                34,
                [
                    "ms_mo_fa_fei_dan",
                    "ms_sheng_guang_zhan"
                ],
                [
                    "mat_sheng_guang_jie_jing"
                ]
            ],
            [
                "m_radiant_wolf",
                "光耀狼",
                "speedster",
                33,
                [
                    "ms_si_yao",
                    "ms_hao_jiao"
                ],
                [
                    "mat_guang_yao_zhi_pi"
                ]
            ]
        ],
        "elite": [
            "e_holy_knight_captain",
            "远境骑士长",
            "elite",
            36,
            [
                "ms_pi_kan",
                "ms_sheng_guang_zhan",
                "ms_zhan_hou"
            ],
            [
                "mat_sheng_qi_shi_jian"
            ]
        ],
        "boss": None,
        "npcs": [
            "npc_holy_cardinal"
        ]
    },
    "holy_temple": {
        "id": "holy_temple",
        "name": "远境大教堂",
        "lv": 38,
        "region": "远境高地",
        "chapter": 4,
        "area": "holy",
        "area_name": "远境高原",
        "desc": "远境大教堂的核心大殿，天使的雕像被暗影藤蔓缠绕。大主教说，赛拉斯大主教已经……堕落了。",
        "type": "核心",
        "shop": False,
        "healer": True,
        "hidden": False,
        "monsters": [
            [
                "m_holy_guard",
                "大教堂卫士",
                "tank",
                36,
                [
                    "ms_dun_ji",
                    "ms_sheng_guang_zhan"
                ],
                [
                    "mat_sheng_guang_dun_pai"
                ]
            ],
            [
                "m_seraph",
                "白翼教众",
                "caster",
                37,
                [
                    "ms_tian_fa",
                    "ms_sheng_guang_zhan"
                ],
                [
                    "mat_tian_shi_zhi_yu"
                ]
            ]
        ],
        "elite": [
            "e_seraph_captain",
            "白翼统领",
            "elite",
            37,
            [
                "ms_sheng_guang_zhan",
                "ms_tian_fa",
                "ms_shen_wei"
            ],
            [
                "mat_tian_shi_sheng_yin"
            ]
        ],
        "boss": [
            "b_archangel",
            "大主教·赛拉斯",
            "boss",
            38,
            [
                "ms_sheng_guang_zhan",
                "ms_tian_fa",
                "ms_shen_wei",
                "ms_sheng_guang_chong_feng"
            ],
            [
                "mat_tian_shi_sheng_yin"
            ]
        ],
        "npcs": []
    },
    "elf_forest": {
        "id": "elf_forest",
        "name": "精灵之森",
        "lv": 41,
        "region": "远境高地",
        "chapter": 4,
        "area": "elf_court",
        "area_name": "精灵王庭",
        "desc": "精灵王庭外围的原始森林，古树参天，月光透过叶隙洒下。森林在低语，精灵们已经很久没有歌唱了。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_elf_archer",
                "精灵弓手",
                "dps",
                41,
                [
                    "ms_feng_ren",
                    "ms_fu_chong"
                ],
                [
                    "mat_jing_ling_jian_shi"
                ]
            ],
            [
                "m_moon_panther",
                "月影豹",
                "speedster",
                42,
                [
                    "ms_zhao_ji",
                    "ms_hao_jiao"
                ],
                [
                    "mat_yue_ying_zhi_pi"
                ]
            ],
            [
                "m_forest_spirit",
                "林间鹿灵",
                "caster",
                43,
                [
                    "ms_zi_ran_zhu_fu",
                    "ms_mo_fa_fei_dan"
                ],
                [
                    "mat_sen_lin_zhi_ling"
                ]
            ]
        ],
        "elite": [
            "e_moon_guard",
            "月光守卫",
            "elite",
            44,
            [
                "ms_feng_ren",
                "ms_chan_rao",
                "ms_zi_ran_zhu_fu"
            ],
            [
                "mat_yue_zhi_ren"
            ]
        ],
        "boss": None,
        "npcs": []
    },
    "elf_courtyard": {
        "id": "elf_courtyard",
        "name": "月之庭院",
        "lv": 44,
        "region": "远境高地",
        "chapter": 4,
        "area": "elf_court",
        "area_name": "精灵王庭",
        "desc": "精灵王庭的月之庭院，银月泉水依旧流淌，但守护它的精灵法师们眼中只剩空洞。",
        "type": "野外",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_elf_mage",
                "精灵法师",
                "caster",
                44,
                [
                    "ms_huo_qiu",
                    "ms_shan_dian_jian"
                ],
                [
                    "mat_jing_ling_fa_zhu"
                ]
            ],
            [
                "m_jade_bird",
                "翠羽灵鸟",
                "speedster",
                45,
                [
                    "ms_fu_chong",
                    "ms_feng_ren"
                ],
                [
                    "mat_cui_yu"
                ]
            ]
        ],
        "elite": [
            "e_court_guard",
            "王庭禁卫",
            "elite",
            46,
            [
                "ms_pi_kan",
                "ms_feng_ren",
                "ms_dun_ji"
            ],
            [
                "mat_wang_ting_hui_zhang"
            ]
        ],
        "boss": None,
        "npcs": [
            "npc_elf_sage"
        ]
    },
    "elf_throne": {
        "id": "elf_throne",
        "name": "王庭深处",
        "lv": 48,
        "region": "远境高地",
        "chapter": 4,
        "area": "elf_court",
        "area_name": "精灵王庭",
        "desc": "精灵王庭的最深处，月神祭坛上，女王的身影被暗影笼罩。她手中的月之泪，已化为黑色。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_court_guard",
                "王庭禁卫",
                "tank",
                48,
                [
                    "ms_pi_kan",
                    "ms_feng_ren",
                    "ms_dun_ji"
                ],
                [
                    "mat_wang_ting_hui_zhang"
                ]
            ],
            [
                "m_elf_mage",
                "精灵法师",
                "caster",
                47,
                [
                    "ms_huo_qiu",
                    "ms_shan_dian_jian"
                ],
                [
                    "mat_jing_ling_fa_zhu"
                ]
            ]
        ],
        "elite": [
            "e_moon_priest",
            "月神祭司",
            "elite",
            49,
            [
                "ms_mo_fa_fei_dan",
                "ms_bao_feng_xue",
                "ms_zi_ran_zhu_fu"
            ],
            [
                "mat_yue_zhi_lei"
            ]
        ],
        "boss": [
            "b_elf_queen",
            "精灵女王·艾薇安",
            "boss",
            50,
            [
                "ms_feng_ren",
                "ms_bao_feng_xue",
                "ms_zi_ran_zhu_fu",
                "ms_tian_fa"
            ],
            [
                "mat_yue_shen_zhi_guan"
            ]
        ],
        "npcs": []
    },
    "dragon_path": {
        "id": "dragon_path",
        "name": "龙脊山道",
        "lv": 51,
        "region": "远境高地",
        "chapter": 4,
        "area": "dragon_ridge",
        "area_name": "龙脊山脉",
        "desc": "龙脊山脉的蜿蜒山道，灼热的气浪从山巅翻涌而下。龙裔战士在山道间巡逻，警惕地盯着每个闯入者。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_dragon_lizard",
                "龙鳞蜥蜴",
                "tank",
                51,
                [
                    "ms_si_yao",
                    "ms_long_zhi_nu"
                ],
                [
                    "mat_long_lin"
                ]
            ],
            [
                "m_cliff_wyvern",
                "岩脊飞龙",
                "speedster",
                52,
                [
                    "ms_fu_chong",
                    "ms_long_zhi_nu"
                ],
                [
                    "mat_fei_long_yi"
                ]
            ],
            [
                "m_dragonkin",
                "龙裔战士",
                "dps",
                53,
                [
                    "ms_pi_kan",
                    "ms_long_zhi_nu",
                    "ms_zhan_hou"
                ],
                [
                    "mat_long_yi_hui_ji"
                ]
            ]
        ],
        "elite": [
            "e_dragon_warrior",
            "龙脉战士长",
            "elite",
            54,
            [
                "ms_zhong_ji",
                "ms_long_zhi_nu",
                "ms_zhan_hou"
            ],
            [
                "mat_long_mai_zhan_ren"
            ]
        ],
        "boss": None,
        "npcs": []
    },
    "dragon_nest": {
        "id": "dragon_nest",
        "name": "龙巢之巅",
        "lv": 54,
        "region": "远境高地",
        "chapter": 4,
        "area": "dragon_ridge",
        "area_name": "龙脊山脉",
        "desc": "龙巢之巅，幼龙们在巢穴间嬉戏，却带着不属于幼龙的暴戾。贤者·岩语说，龙血正在被某种力量唤醒。",
        "type": "野外",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_ember_whelp",
                "赤炎幼龙",
                "caster",
                54,
                [
                    "ms_huo_qiu",
                    "ms_long_zhi_nu"
                ],
                [
                    "mat_long_yan_jing_hua"
                ]
            ],
            [
                "m_dragonkin",
                "龙裔战士",
                "dps",
                53,
                [
                    "ms_pi_kan",
                    "ms_long_zhi_nu",
                    "ms_zhan_hou"
                ],
                [
                    "mat_long_yi_hui_ji"
                ]
            ]
        ],
        "elite": [
            "e_dragon_guardian",
            "龙脉守护者",
            "elite",
            56,
            [
                "ms_long_zhi_nu",
                "ms_lie_yan_zhen_ji",
                "ms_zhan_hou"
            ],
            [
                "mat_long_mai_hu_fu"
            ]
        ],
        "boss": None,
        "npcs": [
            "npc_dragon_elder"
        ]
    },
    "dragon_shrine": {
        "id": "dragon_shrine",
        "name": "龙眠圣殿",
        "lv": 58,
        "region": "远境高地",
        "chapter": 4,
        "area": "dragon_ridge",
        "area_name": "龙脊山脉",
        "desc": "龙眠圣殿，龙族的圣地。古龙·奥瑞斯盘踞在王座上，龙眼中燃烧着不属于龙族的混沌之火。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_flame_wyvern",
                "赤炎飞龙",
                "dps",
                58,
                [
                    "ms_huo_qiu",
                    "ms_long_zhi_nu",
                    "ms_fu_chong"
                ],
                [
                    "mat_fei_long_lin"
                ]
            ],
            [
                "m_dragon_guardian",
                "龙脉守护者",
                "tank",
                57,
                [
                    "ms_long_zhi_nu",
                    "ms_lie_yan_zhen_ji",
                    "ms_zhan_hou"
                ],
                [
                    "mat_long_mai_hu_fu"
                ]
            ]
        ],
        "elite": [
            "e_dragon_wing",
            "龙翼亲卫",
            "elite",
            59,
            [
                "ms_long_zhi_nu",
                "ms_sheng_guang_chong_feng",
                "ms_zhan_hou"
            ],
            [
                "mat_long_yi_jian"
            ]
        ],
        "boss": [
            "b_dragon_king",
            "古龙·奥瑞斯",
            "boss",
            60,
            [
                "ms_long_zhi_nu",
                "ms_lie_yan_zhen_ji",
                "ms_kuang_bao",
                "ms_tun_shi"
            ],
            [
                "mat_long_wang_zhi_jiao"
            ]
        ],
        "npcs": []
    },
    "void_edge": {
        "id": "void_edge",
        "name": "裂隙谷口",
        "lv": 61,
        "region": "旧战场",
        "chapter": 5,
        "area": "void_rift",
        "area_name": "裂隙谷地",
        "desc": "裂隙谷地的边缘地带，空间在这里扭曲成漩涡。裂隙蠕虫在裂隙间蠕动，发出令人牙酸的嘶鸣。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_void_worm",
                "裂隙蠕虫",
                "speedster",
                61,
                [
                    "ms_si_yao",
                    "ms_xu_kong_zhan"
                ],
                [
                    "mat_xu_kong_zhan_ye"
                ]
            ],
            [
                "m_rift_wraith",
                "裂隙魔灵",
                "caster",
                62,
                [
                    "ms_an_ying_jian",
                    "ms_xu_kong_zhan"
                ],
                [
                    "mat_lie_xi_sui_pian"
                ]
            ],
            [
                "m_void_minion",
                "废墟爪牙",
                "dps",
                63,
                [
                    "ms_zhao_ji",
                    "ms_xu_kong_zhan"
                ],
                [
                    "mat_xu_kong_zhi_zhao"
                ]
            ]
        ],
        "elite": [
            "e_void_ripper",
            "裂隙撕裂者",
            "elite",
            64,
            [
                "ms_xu_kong_zhan",
                "ms_an_ying_feng_bao",
                "ms_tun_shi"
            ],
            [
                "mat_si_lie_zhe_he_xin"
            ]
        ],
        "boss": None,
        "npcs": []
    },
    "void_corridor": {
        "id": "void_corridor",
        "name": "古战场回廊",
        "lv": 64,
        "region": "旧战场",
        "chapter": 5,
        "area": "void_rift",
        "area_name": "裂隙谷地",
        "desc": "古战场回廊，无数破碎的世界在此重叠。谷口守望者悬浮在长廊两侧，空洞的眼眶注视着每一个过客。",
        "type": "野外",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_void_watcher",
                "谷口守望者",
                "tank",
                64,
                [
                    "ms_zhong_ji",
                    "ms_xu_kong_zhan",
                    "ms_dun_ji"
                ],
                [
                    "mat_xu_kong_hu_jia"
                ]
            ],
            [
                "m_rift_wraith",
                "裂隙魔灵",
                "caster",
                63,
                [
                    "ms_an_ying_jian",
                    "ms_xu_kong_zhan"
                ],
                [
                    "mat_lie_xi_sui_pian"
                ]
            ]
        ],
        "elite": [
            "e_void_lord",
            "裂隙领主",
            "elite",
            66,
            [
                "ms_xu_kong_zhan",
                "ms_xu_kong_beng_ta",
                "ms_an_ying_feng_bao"
            ],
            [
                "mat_lie_xi_ling_zhu_yin_ji"
            ]
        ],
        "boss": None,
        "npcs": [
            "npc_void_prophet"
        ]
    },
    "void_heart": {
        "id": "void_heart",
        "name": "战场中心",
        "lv": 68,
        "region": "旧战场",
        "chapter": 5,
        "area": "void_rift",
        "area_name": "裂隙谷地",
        "desc": "裂隙谷地的核心，一颗巨大的暗紫色心脏在虚空中跳动。裂隙巨像们守护着它——那是吞噬者的心脏。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_void_colossus",
                "裂隙巨像",
                "tank",
                68,
                [
                    "ms_zhong_ji",
                    "ms_xu_kong_beng_ta",
                    "ms_tun_shi"
                ],
                [
                    "mat_lie_xi_ju_xiang_he_xin"
                ]
            ],
            [
                "m_void_watcher",
                "谷口守望者",
                "tank",
                67,
                [
                    "ms_zhong_ji",
                    "ms_xu_kong_zhan",
                    "ms_dun_ji"
                ],
                [
                    "mat_xu_kong_hu_jia"
                ]
            ]
        ],
        "elite": [
            "e_void_overlord",
            "裂隙主宰",
            "elite",
            69,
            [
                "ms_xu_kong_beng_ta",
                "ms_an_ying_feng_bao",
                "ms_tun_shi"
            ],
            [
                "mat_lie_xi_zhu_zai_quan_zhang"
            ]
        ],
        "boss": [
            "b_void_devourer",
            "裂隙巨兽",
            "boss",
            70,
            [
                "ms_xu_kong_zhan",
                "ms_xu_kong_beng_ta",
                "ms_tun_shi",
                "ms_an_ying_feng_bao"
            ],
            [
                "mat_tun_shi_zhe_zhi_he"
            ]
        ],
        "npcs": []
    },
    "temple_hall": {
        "id": "temple_hall",
        "name": "旧教团大厅",
        "lv": 71,
        "region": "旧战场",
        "chapter": 5,
        "area": "dark_temple",
        "area_name": "旧教团遗址",
        "desc": "旧教团遗址的前厅，曾经供奉光明神的殿堂如今爬满暗影。黑袍修士们低声吟唱着亵渎的祷词。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_dark_acolyte",
                "黑袍修士",
                "caster",
                71,
                [
                    "ms_an_ying_jian",
                    "ms_ji_qu"
                ],
                [
                    "mat_hei_an_jing_juan"
                ]
            ],
            [
                "m_abyss_servant",
                "教团仆从",
                "dps",
                72,
                [
                    "ms_zhao_ji",
                    "ms_an_ying_jian"
                ],
                [
                    "mat_shen_yuan_zhi_chen"
                ]
            ],
            [
                "m_fallen_paladin",
                "堕落骑士",
                "tank",
                73,
                [
                    "ms_pi_kan",
                    "ms_an_ying_jian",
                    "ms_dun_ji"
                ],
                [
                    "mat_duo_luo_sheng_hui"
                ]
            ]
        ],
        "elite": [
            "e_inquisitor",
            "审判官",
            "elite",
            74,
            [
                "ms_an_ying_jian",
                "ms_si_wang_zhi_wo",
                "ms_an_ying_feng_bao"
            ],
            [
                "mat_shen_pan_guan_zhi_yin"
            ]
        ],
        "boss": None,
        "npcs": []
    },
    "temple_aisle": {
        "id": "temple_aisle",
        "name": "忏悔回廊",
        "lv": 74,
        "region": "旧战场",
        "chapter": 5,
        "area": "dark_temple",
        "area_name": "旧教团遗址",
        "desc": "忏悔回廊，两侧是无数忏悔室的残骸。被囚禁的灵魂在此徘徊，发出永无止境的哀叹。",
        "type": "野外",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_penitent_wraith",
                "忏悔亡灵",
                "caster",
                74,
                [
                    "ms_ai_hao",
                    "ms_an_ying_jian"
                ],
                [
                    "mat_chan_hui_zhi_lei"
                ]
            ],
            [
                "m_abyss_priest",
                "黑袍牧师",
                "caster",
                75,
                [
                    "ms_an_ying_jian",
                    "ms_ji_qu",
                    "ms_si_wang_zhi_wo"
                ],
                [
                    "mat_shen_yuan_fa_zhu"
                ]
            ]
        ],
        "elite": [
            "e_heresy_executor",
            "处刑修士",
            "elite",
            76,
            [
                "ms_zhong_ji",
                "ms_an_ying_jian",
                "ms_an_ying_feng_bao"
            ],
            [
                "mat_chu_xing_zhe_zhi_fu"
            ]
        ],
        "boss": None,
        "npcs": [
            "npc_fallen_priest"
        ]
    },
    "temple_altar": {
        "id": "temple_altar",
        "name": "旧教团祭坛",
        "lv": 78,
        "region": "旧战场",
        "chapter": 5,
        "area": "dark_temple",
        "area_name": "旧教团遗址",
        "desc": "旧教团祭坛，教团献祭的中心。祭坛之上，大祭司·克劳斯正在举行召唤仪式——他在召唤深渊真正的主人。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_abyss_ritualist",
                "教团祭祀",
                "caster",
                78,
                [
                    "ms_an_ying_jian",
                    "ms_di_yu_huo",
                    "ms_si_wang_zhi_wo"
                ],
                [
                    "mat_ji_si_zhi_huo"
                ]
            ],
            [
                "m_heresy_executor",
                "处刑修士",
                "dps",
                77,
                [
                    "ms_zhong_ji",
                    "ms_an_ying_jian",
                    "ms_an_ying_feng_bao"
                ],
                [
                    "mat_chu_xing_zhe_zhi_fu"
                ]
            ]
        ],
        "elite": [
            "e_archpriest",
            "教团大祭司",
            "elite",
            79,
            [
                "ms_di_yu_huo",
                "ms_an_ying_feng_bao",
                "ms_si_wang_zhi_wo"
            ],
            [
                "mat_da_ji_si_zhi_huan"
            ]
        ],
        "boss": [
            "b_abyss_pope",
            "大祭司·克劳斯",
            "boss",
            80,
            [
                "ms_di_yu_huo",
                "ms_an_ying_feng_bao",
                "ms_si_wang_zhi_wo",
                "ms_an_ying_qin_shi"
            ],
            [
                "mat_jiao_zong_quan_zhang"
            ]
        ],
        "npcs": []
    },
    "annih_front": {
        "id": "annih_front",
        "name": "白骨前线",
        "lv": 81,
        "region": "旧战场",
        "chapter": 5,
        "area": "annihilation",
        "area_name": "白骨平原",
        "desc": "白骨平原的前线阵地，大地被烧成焦黑。枯骨魔兵列成方阵，黑甲骑士的铁蹄震动着荒芜的地面。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_annih_soldier",
                "枯骨魔兵",
                "dps",
                81,
                [
                    "ms_zhong_ji",
                    "ms_an_ying_she_xian",
                    "ms_kuang_bao"
                ],
                [
                    "mat_yan_mie_sui_pian"
                ]
            ],
            [
                "m_doom_knight",
                "黑甲骑士",
                "tank",
                82,
                [
                    "ms_zhong_ji",
                    "ms_an_ying_she_xian",
                    "ms_dun_ji"
                ],
                [
                    "mat_zai_e_zhan_jia"
                ]
            ],
            [
                "m_soul_devourer",
                "噬魂怨灵",
                "caster",
                83,
                [
                    "ms_ji_qu",
                    "ms_an_ying_she_xian",
                    "ms_ai_hao"
                ],
                [
                    "mat_shi_hun_jie_jing"
                ]
            ]
        ],
        "elite": [
            "e_annih_vanguard",
            "枯骨先锋",
            "elite",
            84,
            [
                "ms_an_ying_she_xian",
                "ms_kuang_bao",
                "ms_an_ying_feng_bao"
            ],
            [
                "mat_xian_feng_zhan_qi"
            ]
        ],
        "boss": None,
        "npcs": []
    },
    "annih_field": {
        "id": "annih_field",
        "name": "白骨战场",
        "lv": 84,
        "region": "旧战场",
        "chapter": 5,
        "area": "annihilation",
        "area_name": "白骨平原",
        "desc": "白骨战场，尸骸遍野，破碎的旗帜在风中摇曳。枯骨魔将们在此督战，等待总攻的命令。",
        "type": "野外",
        "shop": True,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_annih_general",
                "枯骨魔将",
                "dps",
                84,
                [
                    "ms_an_ying_she_xian",
                    "ms_xu_kong_zhan",
                    "ms_kuang_bao"
                ],
                [
                    "mat_mo_jiang_zhi_ren"
                ]
            ],
            [
                "m_doom_knight",
                "黑甲骑士",
                "tank",
                83,
                [
                    "ms_zhong_ji",
                    "ms_an_ying_she_xian",
                    "ms_dun_ji"
                ],
                [
                    "mat_zai_e_zhan_jia"
                ]
            ]
        ],
        "elite": [
            "e_annih_lord",
            "枯骨领主",
            "elite",
            86,
            [
                "ms_an_ying_she_xian",
                "ms_xu_kong_beng_ta",
                "ms_kuang_bao"
            ],
            [
                "mat_ku_gu_ling_zhu_zhi_huan"
            ]
        ],
        "boss": None,
        "npcs": [
            "npc_annih_spy"
        ]
    },
    "annih_throne": {
        "id": "annih_throne",
        "name": "旧王陵寝",
        "lv": 88,
        "region": "旧战场",
        "chapter": 5,
        "area": "annihilation",
        "area_name": "白骨平原",
        "desc": "旧王陵寝，亡灵大军的指挥中心。白骨君王端坐于骸骨堆成的王座上，静静等待最终时刻。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_annih_guard",
                "枯骨禁卫",
                "tank",
                88,
                [
                    "ms_an_ying_she_xian",
                    "ms_dun_ji",
                    "ms_kuang_bao"
                ],
                [
                    "mat_jin_wei_kai_jia"
                ]
            ],
            [
                "m_annih_general",
                "枯骨魔将",
                "dps",
                87,
                [
                    "ms_an_ying_she_xian",
                    "ms_xu_kong_zhan",
                    "ms_kuang_bao"
                ],
                [
                    "mat_mo_jiang_zhi_ren"
                ]
            ]
        ],
        "elite": [
            "e_silent_guard",
            "旧王亲卫",
            "elite",
            89,
            [
                "ms_an_ying_she_xian",
                "ms_an_ying_feng_bao",
                "ms_tun_shi"
            ],
            [
                "mat_si_ji_zhi_ren"
            ]
        ],
        "boss": [
            "b_silent_king",
            "白骨君王",
            "boss",
            90,
            [
                "ms_an_ying_she_xian",
                "ms_xu_kong_beng_ta",
                "ms_tun_shi",
                "ms_an_ying_qin_shi"
            ],
            [
                "mat_si_ji_wang_guan"
            ]
        ],
        "npcs": []
    },
    "divine_path": {
        "id": "divine_path",
        "name": "王国古道",
        "lv": 91,
        "region": "失落王国",
        "chapter": 6,
        "area": "divine_gate",
        "area_name": "失落王城",
        "desc": "通往失落王国的古道，云海在脚下翻涌。古道守卫们驻守在阶梯两侧，目光望向天空的尽头。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_sky_guard",
                "古道守卫",
                "tank",
                91,
                [
                    "ms_sheng_guang_zhan",
                    "ms_tian_fa",
                    "ms_dun_ji"
                ],
                [
                    "mat_tian_qiong_hu_jia"
                ]
            ],
            [
                "m_astral_messenger",
                "旧宫使者",
                "caster",
                92,
                [
                    "ms_tian_fa",
                    "ms_sheng_guang_zhan",
                    "ms_mo_fa_fei_dan"
                ],
                [
                    "mat_xing_jie_zhi_chen"
                ]
            ],
            [
                "m_divine_warrior",
                "古王战灵",
                "dps",
                93,
                [
                    "ms_sheng_guang_zhan",
                    "ms_tian_fa",
                    "ms_shen_wei"
                ],
                [
                    "mat_shen_yu_zhan_hun"
                ]
            ]
        ],
        "elite": [
            "e_astral_knight",
            "王家骑士长",
            "elite",
            94,
            [
                "ms_sheng_guang_zhan",
                "ms_tian_fa",
                "ms_shen_wei",
                "ms_sheng_guang_chong_feng"
            ],
            [
                "mat_xing_jie_qi_shi_jian"
            ]
        ],
        "boss": None,
        "npcs": []
    },
    "divine_hall": {
        "id": "divine_hall",
        "name": "旧宫回廊",
        "lv": 93,
        "region": "失落王国",
        "chapter": 6,
        "area": "divine_gate",
        "area_name": "失落王城",
        "desc": "旧宫回廊，群星的墓地。旧宫贤者们在此守护着王国倾覆前的最后记忆。",
        "type": "野外",
        "shop": True,
        "healer": True,
        "hidden": False,
        "monsters": [
            [
                "m_astral_sage",
                "旧宫贤者",
                "caster",
                93,
                [
                    "ms_tian_fa",
                    "ms_bao_feng_xue",
                    "ms_shen_wei"
                ],
                [
                    "mat_xing_jie_fa_zhu"
                ]
            ],
            [
                "m_divine_warrior",
                "古王战灵",
                "dps",
                93,
                [
                    "ms_sheng_guang_zhan",
                    "ms_tian_fa",
                    "ms_shen_wei"
                ],
                [
                    "mat_shen_yu_zhan_hun"
                ]
            ]
        ],
        "elite": [
            "e_astral_judge",
            "旧宫裁决者",
            "elite",
            95,
            [
                "ms_tian_fa",
                "ms_shen_wei",
                "ms_wang_quan_zhi_li"
            ],
            [
                "mat_xing_jie_cai_jue_zhi_zhang"
            ]
        ],
        "boss": None,
        "npcs": [
            "npc_star_warden"
        ]
    },
    "divine_gate": {
        "id": "divine_gate",
        "name": "失落王城之门",
        "lv": 95,
        "region": "失落王国",
        "chapter": 6,
        "area": "divine_gate",
        "area_name": "失落王城",
        "desc": "失落王城的大门，古老的石门刻满王国徽记。王城守望者手持长枪立于门前——门后，是旧日王国的战场。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_gate_guardian",
                "王城守卫",
                "tank",
                95,
                [
                    "ms_sheng_guang_zhan",
                    "ms_tian_fa",
                    "ms_dun_ji"
                ],
                [
                    "mat_men_fei_zhi_yao"
                ]
            ],
            [
                "m_astral_sage",
                "旧宫贤者",
                "caster",
                94,
                [
                    "ms_tian_fa",
                    "ms_bao_feng_xue",
                    "ms_shen_wei"
                ],
                [
                    "mat_xing_jie_fa_zhu"
                ]
            ]
        ],
        "elite": None,
        "boss": [
            "b_sky_warden",
            "王城守望者",
            "boss",
            96,
            [
                "ms_sheng_guang_zhan",
                "ms_tian_fa",
                "ms_shen_wei",
                "ms_wang_quan_zhi_li"
            ],
            [
                "mat_tian_qiong_zhi_guan"
            ]
        ],
        "npcs": []
    },
    "panth_court": {
        "id": "panth_court",
        "name": "先王庭院",
        "lv": 96,
        "region": "失落王国",
        "chapter": 6,
        "area": "pantheon",
        "area_name": "先王陵寝",
        "desc": "先王陵寝的庭院，先王的雕像沉默地矗立。古王残魂在庭院间游荡，暗影已经开始侵蚀这片旧地。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_divine_spirit",
                "古王残魂",
                "caster",
                96,
                [
                    "ms_tian_fa",
                    "ms_wang_quan_zhi_li",
                    "ms_shen_wei"
                ],
                [
                    "mat_shen_yu_jing_hua"
                ]
            ],
            [
                "m_chaos_servant",
                "暗影仆从",
                "dps",
                97,
                [
                    "ms_an_ying_qin_shi",
                    "ms_an_ying_she_xian"
                ],
                [
                    "mat_hun_dun_zhi_zha"
                ]
            ],
            [
                "m_god_echo",
                "先王残影",
                "tank",
                98,
                [
                    "ms_sheng_guang_zhan",
                    "ms_wang_quan_zhi_li"
                ],
                [
                    "mat_zhu_shen_yi_hui"
                ]
            ]
        ],
        "elite": [
            "e_god_messenger",
            "先王使者",
            "elite",
            99,
            [
                "ms_wang_quan_zhi_li",
                "ms_tian_fa",
                "ms_shen_wei",
                "ms_an_ying_qin_shi"
            ],
            [
                "mat_shi_zhe_zhi_jie"
            ]
        ],
        "boss": None,
        "npcs": [
            "npc_last_god"
        ]
    },
    "panth_hall": {
        "id": "panth_hall",
        "name": "王座大殿",
        "lv": 98,
        "region": "失落王国",
        "chapter": 6,
        "area": "pantheon",
        "area_name": "先王陵寝",
        "desc": "王座大殿，先王铸造世界的殿堂。如今巫王盘踞于此，试图将整个大陆拖入永恒的黑暗。",
        "type": "核心",
        "shop": False,
        "healer": True,
        "hidden": False,
        "monsters": [
            [
                "m_creation_guard",
                "王座守卫",
                "tank",
                98,
                [
                    "ms_wang_quan_zhi_li",
                    "ms_sheng_guang_zhan",
                    "ms_dun_ji"
                ],
                [
                    "mat_chuang_shi_zhi_dun"
                ]
            ],
            [
                "m_god_echo",
                "先王残影",
                "tank",
                98,
                [
                    "ms_sheng_guang_zhan",
                    "ms_wang_quan_zhi_li"
                ],
                [
                    "mat_zhu_shen_yi_hui"
                ]
            ]
        ],
        "elite": None,
        "boss": [
            "b_chaos_lord",
            "巫王·莫里斯",
            "boss",
            100,
            [
                "ms_an_ying_qin_shi",
                "ms_an_ying_she_xian",
                "ms_wang_quan_zhi_li",
                "ms_an_ying_feng_bao",
                "灭世"
            ],
            [
                "mat_hun_dun_zhi_he"
            ]
        ],
        "npcs": []
    },
    "holy_city_gate": {
        "id": "holy_city_gate",
        "name": "远境城门",
        "lv": 33,
        "region": "远境高地",
        "chapter": 4,
        "area": "holy",
        "area_name": "远境高原",
        "desc": "圣光王国的首都远境城，白色城墙高耸入云，城门前远境骑士列队巡逻。城门外的草甸上偶有野兽出没。",
        "type": "城镇外郊",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_radiant_wolf",
                "光耀狼",
                "speedster",
                32,
                [
                    "ms_si_yao",
                    "ms_hao_jiao"
                ],
                [
                    "mat_guang_yao_zhi_pi"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "holy_city_square": {
        "id": "holy_city_square",
        "name": "远境广场",
        "lv": 33,
        "region": "远境高地",
        "chapter": 4,
        "area": "holy",
        "area_name": "远境高原",
        "desc": "圣光王国的心脏，大教堂的钟声响彻全城。来自大陆各地的圣骑士与学者在此汇聚。",
        "type": "城镇区域",
        "shop": True,
        "healer": True,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_holy_king",
            "npc_holy_innkeeper"
        ]
    },
    "elf_city_gate": {
        "id": "elf_city_gate",
        "name": "银月城门",
        "lv": 43,
        "region": "远境高地",
        "chapter": 4,
        "area": "elf_court",
        "area_name": "精灵王庭",
        "desc": "精灵王国首都银月城，城门由月光石雕琢而成，即便在白昼也泛着银辉。城外的森林依然低语。",
        "type": "城镇外郊",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_moon_panther",
                "月影豹",
                "speedster",
                42,
                [
                    "ms_zhao_ji",
                    "ms_hao_jiao"
                ],
                [
                    "mat_yue_ying_zhi_pi"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "elf_city_square": {
        "id": "elf_city_square",
        "name": "银月广场",
        "lv": 43,
        "region": "远境高地",
        "chapter": 4,
        "area": "elf_court",
        "area_name": "精灵王庭",
        "desc": "银月城的中心，生命之树在广场中央舒展枝叶。精灵工匠们在这里出售世代传承的技艺结晶。",
        "type": "城镇区域",
        "shop": True,
        "healer": True,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_elf_royal",
            "npc_elf_innkeeper"
        ]
    },
    "dragon_city_gate": {
        "id": "dragon_city_gate",
        "name": "龙喉堡城门",
        "lv": 53,
        "region": "远境高地",
        "chapter": 4,
        "area": "dragon_ridge",
        "area_name": "龙脊山脉",
        "desc": "龙裔王国在山巅开凿的要塞龙喉堡，城墙由熔岩冷却后的黑曜石筑成。门口的火盆昼夜不熄。",
        "type": "城镇外郊",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_dragonkin",
                "龙裔战士",
                "dps",
                53,
                [
                    "ms_pi_kan",
                    "ms_long_zhi_nu",
                    "ms_zhan_hou"
                ],
                [
                    "mat_long_yi_hui_ji"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "dragon_city_square": {
        "id": "dragon_city_square",
        "name": "龙喉大厅",
        "lv": 53,
        "region": "远境高地",
        "chapter": 4,
        "area": "dragon_ridge",
        "area_name": "龙脊山脉",
        "desc": "龙裔的议事大厅，石柱上雕刻着龙族千年的战争史诗。矮人与龙裔的铁匠在这里锻造传奇兵器。",
        "type": "城镇区域",
        "shop": True,
        "healer": True,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_dragon_king",
            "npc_dragon_innkeeper"
        ]
    },
    "void_city_gate": {
        "id": "void_city_gate",
        "name": "虚空前哨大门",
        "lv": 63,
        "region": "旧战场",
        "chapter": 5,
        "area": "void_rift",
        "area_name": "裂隙谷地",
        "desc": "人类联军在裂隙谷地边缘建立的最后前哨，魔法屏障勉强挡住空间的扭曲。哨兵们面色凝重。",
        "type": "城镇外郊",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_void_minion",
                "废墟爪牙",
                "dps",
                63,
                [
                    "ms_zhao_ji",
                    "ms_xu_kong_zhan"
                ],
                [
                    "mat_xu_kong_zhi_zhao"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "void_city_square": {
        "id": "void_city_square",
        "name": "前哨营地",
        "lv": 63,
        "region": "旧战场",
        "chapter": 5,
        "area": "void_rift",
        "area_name": "裂隙谷地",
        "desc": "前哨的核心营地，军需官与随军牧师在此为远征军提供补给。营火旁流传着关于战场中心的传说。",
        "type": "城镇区域",
        "shop": True,
        "healer": True,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_void_general",
            "npc_void_innkeeper"
        ]
    },
    "exile_camp_gate": {
        "id": "exile_camp_gate",
        "name": "悲怆营地入口",
        "lv": 73,
        "region": "旧战场",
        "chapter": 5,
        "area": "dark_temple",
        "area_name": "旧教团遗址",
        "desc": "从旧教团遗址逃出的流亡者建立的营地，用圣殿的碎石搭起简陋的围墙。这里是黑暗中的一盏孤灯。",
        "type": "城镇外郊",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_dark_acolyte",
                "黑袍修士",
                "caster",
                71,
                [
                    "ms_an_ying_jian",
                    "ms_ji_qu"
                ],
                [
                    "mat_hei_an_jing_juan"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "exile_camp_square": {
        "id": "exile_camp_square",
        "name": "悲怆营火",
        "lv": 73,
        "region": "旧战场",
        "chapter": 5,
        "area": "dark_temple",
        "area_name": "旧教团遗址",
        "desc": "营地中央的营火，流亡者们围坐取暖。随军牧师在这里为伤者祈祷，商贩用残存的物资交换补给。",
        "type": "城镇区域",
        "shop": True,
        "healer": True,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_exile_leader",
            "npc_exile_innkeeper"
        ]
    },
    "iron_city_gate": {
        "id": "iron_city_gate",
        "name": "铁壁城门",
        "lv": 83,
        "region": "旧战场",
        "chapter": 5,
        "area": "annihilation",
        "area_name": "白骨平原",
        "desc": "人类在白骨平原最后的堡垒铁壁城，三十米高的钢铁城墙是绝望中唯一的希望。城头炮火轰鸣。",
        "type": "城镇外郊",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_annih_soldier",
                "枯骨魔兵",
                "dps",
                81,
                [
                    "ms_zhong_ji",
                    "ms_an_ying_she_xian",
                    "ms_kuang_bao"
                ],
                [
                    "mat_yan_mie_sui_pian"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "iron_city_square": {
        "id": "iron_city_square",
        "name": "铁壁指挥所",
        "lv": 83,
        "region": "旧战场",
        "chapter": 5,
        "area": "annihilation",
        "area_name": "白骨平原",
        "desc": "铁壁城的指挥中枢，各大势力的联军代表在此共商对策。军需库里的每一件装备都弥足珍贵。",
        "type": "城镇区域",
        "shop": True,
        "healer": True,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_iron_marshal",
            "npc_iron_innkeeper"
        ]
    },
    "divine_city_gate": {
        "id": "divine_city_gate",
        "name": "旧王城门",
        "lv": 93,
        "region": "失落王国",
        "chapter": 6,
        "area": "divine_gate",
        "area_name": "失落王城",
        "desc": "旧王城，悬浮在云海之上的白色巨城。古道守卫持戟而立，目光如星辰般冰冷。",
        "type": "城镇外郊",
        "shop": False,
        "healer": False,
        "hidden": False,
        "monsters": [
            [
                "m_divine_warrior",
                "古王战灵",
                "dps",
                93,
                [
                    "ms_sheng_guang_zhan",
                    "ms_tian_fa",
                    "ms_shen_wei"
                ],
                [
                    "mat_shen_yu_zhan_hun"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "divine_city_square": {
        "id": "divine_city_square",
        "name": "天穹圣殿",
        "lv": 93,
        "region": "失落王国",
        "chapter": 6,
        "area": "divine_gate",
        "area_name": "失落王城",
        "desc": "旧王城的中心圣殿，光之柱直贯天际。先王遗留下的知识与神兵在这里等待凡人的继承。",
        "type": "城镇区域",
        "shop": True,
        "healer": True,
        "hidden": False,
        "monsters": [],
        "elite": None,
        "boss": None,
        "npcs": [
            "npc_divine_archon",
            "npc_divine_innkeeper"
        ]
    },
    "chaos_entry": {
        "id": "chaos_entry",
        "name": "陷落王都",
        "lv": 100,
        "region": "失落王国",
        "chapter": 6,
        "area": "chaos_depths",
        "area_name": "陷落王都",
        "desc": "巫王倒下之处，空间被撕开一道永久的裂隙。裂隙深处传来低沉的轰鸣——有什么东西还在苏醒。",
        "type": "野外",
        "shop": False,
        "healer": False,
        "hidden": True,
        "monsters": [
            [
                "m_chaos_shade",
                "王都魔影",
                "speedster",
                100,
                [
                    "ms_an_ying_qin_shi",
                    "ms_an_ying_feng_bao"
                ],
                [
                    "mat_hun_dun_sui_pian"
                ]
            ]
        ],
        "elite": None,
        "boss": None,
        "npcs": []
    },
    "chaos_depths": {
        "id": "chaos_depths",
        "name": "王都废墟",
        "lv": 100,
        "region": "失落王国",
        "chapter": 6,
        "area": "chaos_depths",
        "area_name": "陷落王都",
        "desc": "王都废墟，传说中王国的尽头。巫王之影悬浮在虚无之中——它自称是『第一次战争之前的古老意志』。",
        "type": "核心",
        "shop": False,
        "healer": False,
        "hidden": True,
        "monsters": [
            [
                "m_chaos_avatar",
                "侵蚀化身",
                "dps",
                100,
                [
                    "ms_an_ying_qin_shi",
                    "ms_an_ying_she_xian",
                    "ms_tun_shi"
                ],
                [
                    "mat_hun_dun_sui_pian"
                ]
            ]
        ],
        "elite": None,
        "boss": [
            "b_chaos_transcendent",
            "巫王之影",
            "boss",
            100,
            [
                "ms_an_ying_qin_shi",
                "ms_an_ying_she_xian",
                "ms_tun_shi",
                "ms_wang_quan_zhi_li",
                "灭世",
                "ms_xu_kong_beng_ta"
            ],
            [
                "mat_chao_yue_zhi_he"
            ]
        ],
        "npcs": []
    }
}

MAP_AREAS = {}

AREA_ENTRY = {
    "vila": "vila_gate",
    "emerald": "emerald_edge",
    "stonefist": "stonefist_camp",
    "gloom": "gloom_edge",
    "redridge": "redridge_field",
    "blackrock": "blackrock_gate",
    "magma": "magma_gorge",
    "tundra": "tundra_field",
    "stormpeak": "stormpeak_path",
    "shadow_city": "shadow_gate",
    "abyss_gate": "abyss_plain",
    "mithril": "mithril_hall",
    "holy": "holy_field",
    "elf_court": "elf_forest",
    "dragon_ridge": "dragon_path",
    "void_rift": "void_edge",
    "dark_temple": "temple_hall",
    "annihilation": "annih_front",
    "divine_gate": "divine_path",
    "pantheon": "panth_court",
    "chaos_depths": "chaos_entry"
}

MAP_CONNECTIONS = {
    "vila_gate": [
        "emerald_edge",
        "vila_square",
        "vila_street"
    ],
    "vila_street": [
        "vila_gate",
        "vila_square"
    ],
    "vila_square": [
        "vila_gate",
        "vila_inn",
        "vila_street",
        "vila_tavern"
    ],
    "vila_tavern": [
        "vila_inn",
        "vila_square"
    ],
    "vila_inn": [
        "vila_square",
        "vila_tavern"
    ],
    "emerald_edge": [
        "emerald_trail",
        "vila_gate"
    ],
    "emerald_trail": [
        "emerald_edge",
        "emerald_heart"
    ],
    "emerald_heart": [
        "emerald_trail",
        "stonefist_camp"
    ],
    "stonefist_camp": [
        "emerald_heart",
        "stonefist_mine"
    ],
    "stonefist_mine": [
        "stonefist_camp",
        "stonefist_deep"
    ],
    "stonefist_deep": [
        "gloom_edge",
        "stonefist_mine"
    ],
    "gloom_edge": [
        "gloom_mire",
        "stonefist_deep"
    ],
    "gloom_mire": [
        "gloom_edge",
        "gloom_heart"
    ],
    "gloom_heart": [
        "gloom_mire",
        "redridge_field"
    ],
    "redridge_field": [
        "gloom_heart",
        "redridge_ridge"
    ],
    "redridge_ridge": [
        "redridge_camp",
        "redridge_field"
    ],
    "redridge_camp": [
        "blackrock_gate",
        "redridge_ridge"
    ],
    "blackrock_gate": [
        "blackrock_street",
        "redridge_camp"
    ],
    "blackrock_street": [
        "blackrock_gate",
        "blackrock_keep"
    ],
    "blackrock_keep": [
        "blackrock_street",
        "magma_gorge"
    ],
    "magma_gorge": [
        "blackrock_keep",
        "magma_heart"
    ],
    "magma_heart": [
        "magma_gorge",
        "tundra_field"
    ],
    "tundra_field": [
        "magma_heart",
        "tundra_cave"
    ],
    "tundra_cave": [
        "stormpeak_path",
        "tundra_field"
    ],
    "stormpeak_path": [
        "stormpeak_peak",
        "tundra_cave"
    ],
    "stormpeak_peak": [
        "mithril_hall",
        "shadow_gate",
        "stormpeak_path"
    ],
    "shadow_gate": [
        "shadow_street",
        "stormpeak_peak"
    ],
    "shadow_street": [
        "shadow_gate",
        "shadow_keep"
    ],
    "shadow_keep": [
        "abyss_plain",
        "shadow_street"
    ],
    "abyss_plain": [
        "abyss_gate",
        "mithril_hall",
        "shadow_keep"
    ],
    "abyss_gate": [
        "abyss_plain"
    ],
    "mithril_hall": [
        "abyss_plain",
        "mithril_vault",
        "stormpeak_peak"
    ],
    "mithril_vault": [
        "holy_field",
        "mithril_hall"
    ],
    "holy_field": [
        "holy_city_gate",
        "mithril_vault"
    ],
    "holy_city_gate": [
        "holy_city_square",
        "holy_field"
    ],
    "holy_city_square": [
        "holy_altar",
        "holy_city_gate"
    ],
    "holy_altar": [
        "holy_city_square",
        "holy_temple"
    ],
    "holy_temple": [
        "elf_forest",
        "holy_altar"
    ],
    "elf_forest": [
        "elf_city_gate",
        "holy_temple"
    ],
    "elf_city_gate": [
        "elf_city_square",
        "elf_forest"
    ],
    "elf_city_square": [
        "elf_city_gate",
        "elf_courtyard"
    ],
    "elf_courtyard": [
        "elf_city_square",
        "elf_throne"
    ],
    "elf_throne": [
        "dragon_path",
        "elf_courtyard"
    ],
    "dragon_path": [
        "dragon_city_gate",
        "elf_throne"
    ],
    "dragon_city_gate": [
        "dragon_city_square",
        "dragon_path"
    ],
    "dragon_city_square": [
        "dragon_city_gate",
        "dragon_nest"
    ],
    "dragon_nest": [
        "dragon_city_square",
        "dragon_shrine"
    ],
    "dragon_shrine": [
        "dragon_nest",
        "void_edge"
    ],
    "void_edge": [
        "dragon_shrine",
        "void_city_gate"
    ],
    "void_city_gate": [
        "void_city_square",
        "void_edge"
    ],
    "void_city_square": [
        "void_city_gate",
        "void_corridor"
    ],
    "void_corridor": [
        "void_city_square",
        "void_heart"
    ],
    "void_heart": [
        "temple_hall",
        "void_corridor"
    ],
    "temple_hall": [
        "exile_camp_gate",
        "void_heart"
    ],
    "exile_camp_gate": [
        "exile_camp_square",
        "temple_hall"
    ],
    "exile_camp_square": [
        "exile_camp_gate",
        "temple_aisle"
    ],
    "temple_aisle": [
        "exile_camp_square",
        "temple_altar"
    ],
    "temple_altar": [
        "annih_front",
        "temple_aisle"
    ],
    "annih_front": [
        "iron_city_gate",
        "temple_altar"
    ],
    "iron_city_gate": [
        "annih_front",
        "iron_city_square"
    ],
    "iron_city_square": [
        "annih_field",
        "iron_city_gate"
    ],
    "annih_field": [
        "annih_throne",
        "iron_city_square"
    ],
    "annih_throne": [
        "annih_field",
        "divine_path"
    ],
    "divine_path": [
        "annih_throne",
        "divine_hall"
    ],
    "divine_hall": [
        "divine_city_gate",
        "divine_path"
    ],
    "divine_city_gate": [
        "divine_city_square",
        "divine_hall"
    ],
    "divine_city_square": [
        "divine_city_gate",
        "divine_gate"
    ],
    "divine_gate": [
        "chaos_entry",
        "divine_city_square",
        "panth_court"
    ],
    "panth_court": [
        "divine_gate",
        "panth_hall"
    ],
    "panth_hall": [
        "chaos_entry",
        "panth_court"
    ],
    "chaos_entry": [
        "chaos_depths",
        "divine_gate",
        "panth_hall"
    ],
    "chaos_depths": [
        "chaos_entry"
    ]
}

HIDDEN_MAP_UNLOCK = {
    "mithril_hall": {
        "level": 25,
        "quest": "q8"
    },
    "mithril_vault": {
        "level": 30,
        "quest": "q10"
    },
    "chaos_entry": {
        "level": 95,
        "quest": "q28"
    },
    "chaos_depths": {
        "level": 100,
        "quest": "q29"
    }
}

LEGACY_MAP_ALIAS = {
    "vila": "vila_gate",
    "维拉镇": "vila_gate",
    "emerald": "emerald_edge",
    "翡翠森林": "emerald_edge",
    "stonefist": "stonefist_camp",
    "石拳丘陵": "stonefist_camp",
    "gloom": "gloom_edge",
    "幽暗沼泽": "gloom_edge",
    "redridge": "redridge_field",
    "赤脊荒原": "redridge_field",
    "blackrock": "blackrock_gate",
    "黑石城废墟": "blackrock_gate",
    "magma": "magma_gorge",
    "熔岩裂谷": "magma_gorge",
    "tundra": "tundra_field",
    "冰封苔原": "tundra_field",
    "stormpeak": "stormpeak_path",
    "风暴之巅": "stormpeak_path",
    "shadow_city": "shadow_gate",
    "暗影之城": "shadow_gate",
    "abyss_gate": "abyss_plain",
    "深渊之门": "abyss_plain",
    "mithril": "mithril_hall",
    "秘银遗迹": "mithril_hall",
    "holy": "holy_field",
    "远境高原": "holy_field",
    "elf_court": "elf_forest",
    "精灵王庭": "elf_forest",
    "dragon_ridge": "dragon_path",
    "龙脊山脉": "dragon_path",
    "void_rift": "void_edge",
    "裂隙谷地": "void_edge",
    "dark_temple": "temple_hall",
    "旧教团遗址": "temple_hall",
    "annihilation": "annih_front",
    "白骨平原": "annih_front",
    "divine_gate": "divine_path",
    "失落王城": "divine_path",
    "pantheon": "panth_court",
    "先王陵寝": "panth_court",
    "chaos_depths": "chaos_entry",
    "陷落王都": "chaos_entry"
}

ENCY_MAP_MONSTERS = {}

ENCY_MONSTER_MAP = {}

ENCY_MATERIAL_SOURCE = {}
