# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - craft.py（v48 全 key 转 ID）"""
CRAFT_RECIPES = {
    "rec_tie_jian": {
        "slot": "weapon",
        "quality": "white",
        "lv": 3,
        "weapon_type": "sword",
        "mats": {
            "mat_ye_gou_liao_ya": 5,
            "mat_shu_wei": 3
        },
        "gold": 30,
        "desc": "新手铁匠的第一件作品",
        "name": "铁剑"
    },
    "rec_xue_tu_fa_zhang": {
        "slot": "weapon",
        "quality": "white",
        "lv": 3,
        "weapon_type": "staff",
        "mats": {
            "mat_shu_wei": 5,
            "mat_ye_gou_liao_ya": 3
        },
        "gold": 30,
        "desc": "初学者练习魔法用的法杖",
        "name": "学徒法杖"
    },
    "rec_lie_gong": {
        "slot": "weapon",
        "quality": "white",
        "lv": 3,
        "weapon_type": "bow",
        "mats": {
            "mat_ye_gou_liao_ya": 4,
            "mat_lang_pi": 2
        },
        "gold": 30,
        "desc": "用野狗筋和硬木做的弓",
        "name": "猎弓"
    },
    "rec_sheng_guang_quan_zhang": {
        "slot": "weapon",
        "quality": "white",
        "lv": 3,
        "weapon_type": "mace",
        "mats": {
            "mat_shu_wei": 4,
            "mat_lang_pi": 3
        },
        "gold": 30,
        "desc": "祝福过的新手权杖",
        "name": "圣光权杖"
    },
    "rec_lv_ren_xiong_jia": {
        "slot": "armor",
        "quality": "green",
        "lv": 4,
        "mats": {
            "mat_lang_pi": 5,
            "mat_ye_gou_liao_ya": 4
        },
        "gold": 50,
        "desc": "冒险者最常穿的皮甲",
        "name": "旅人胸甲"
    },
    "rec_lv_ren_hu_tui": {
        "slot": "legs",
        "quality": "green",
        "lv": 4,
        "mats": {
            "mat_ye_zhu_pi": 4,
            "mat_shu_wei": 4
        },
        "gold": 40,
        "desc": "耐磨的皮革护腿",
        "name": "旅人护腿"
    },
    "rec_lv_ren_zhi_xue": {
        "slot": "boots",
        "quality": "green",
        "lv": 4,
        "mats": {
            "mat_lang_pi": 3,
            "mat_ye_gou_liao_ya": 3
        },
        "gold": 35,
        "desc": "轻便的旅行靴",
        "name": "旅人之靴"
    },
    "rec_shan_zei_zhi_kui": {
        "slot": "helm",
        "quality": "blue",
        "lv": 5,
        "mats": {
            "mat_shan_zei_hui_zhang": 3,
            "mat_lang_pi": 4
        },
        "gold": 80,
        "desc": "用山贼头目的徽章熔铸而成",
        "name": "山贼之盔"
    },
    "rec_sheng_lu_zhi_dun": {
        "slot": "armor",
        "quality": "purple",
        "lv": 8,
        "mats": {
            "mat_sheng_lu_jiao": 2,
            "mat_yuan_gu_shu_pi": 4,
            "mat_lang_pi": 5
        },
        "gold": 200,
        "desc": "以远古圣鹿之角锻造的宝甲",
        "name": "圣鹿之盾"
    },
    "rec_jing_gang_jian": {
        "slot": "weapon",
        "quality": "green",
        "lv": 12,
        "weapon_type": "sword",
        "mats": {
            "mat_gu_pian": 6,
            "mat_jiang_shi_fu_rou": 4
        },
        "gold": 120,
        "desc": "黑石城铁匠的招牌货",
        "name": "精钢剑"
    },
    "rec_you_hun_fa_zhang": {
        "slot": "weapon",
        "quality": "green",
        "lv": 12,
        "weapon_type": "staff",
        "mats": {
            "mat_gui_hun_jing_hua": 5,
            "mat_ling_hun_sui_pian": 3
        },
        "gold": 120,
        "desc": "缠绕着亡灵气息的法杖",
        "name": "幽魂法杖"
    },
    "rec_lie_mo_gong": {
        "slot": "weapon",
        "quality": "green",
        "lv": 12,
        "weapon_type": "bow",
        "mats": {
            "mat_pa_xing_chong_ke": 5,
            "mat_shou_ren_liao_ya": 3
        },
        "gold": 120,
        "desc": "专门猎杀恶魔的弓",
        "name": "猎魔弓"
    },
    "rec_sheng_hai_quan_zhang": {
        "slot": "weapon",
        "quality": "green",
        "lv": 12,
        "weapon_type": "mace",
        "mats": {
            "mat_shi_shi_gui_zhi_zhao": 5,
            "mat_nv_yao_zhi_yu": 3
        },
        "gold": 120,
        "desc": "净化亡者的权杖",
        "name": "圣骸权杖"
    },
    "rec_hei_shi_zhan_jia": {
        "slot": "armor",
        "quality": "blue",
        "lv": 14,
        "mats": {
            "mat_shu_shi_he_xin": 3,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 300,
        "desc": "黑石城精工锻造的锁甲",
        "name": "黑石战甲"
    },
    "rec_huang_yuan_hu_tui": {
        "slot": "legs",
        "quality": "blue",
        "lv": 14,
        "mats": {
            "mat_kuang_zhan_zhi_xin": 2,
            "mat_zuo_lang_quan_chi": 6,
            "mat_gu_pian": 5
        },
        "gold": 260,
        "desc": "赤脊荒原兽人风格的护腿",
        "name": "荒原护腿"
    },
    "rec_fu_xiu_zhi_ren": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 15,
        "weapon_type": "sword",
        "mats": {
            "mat_fu_xiu_zhi_ren": 2,
            "mat_shu_shi_he_xin": 4,
            "mat_ling_hun_sui_pian": 6
        },
        "gold": 600,
        "desc": "从腐朽领主手中夺来的魔刃",
        "name": "腐朽之刃"
    },
    "rec_qiu_zhang_zhan_ren": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 18,
        "weapon_type": "sword",
        "mats": {
            "mat_qiu_zhang_zhan_ren": 2,
            "mat_kuang_zhan_zhi_xin": 4,
            "mat_shou_ren_liao_ya": 8
        },
        "gold": 800,
        "desc": "战歌部落酋长的荣耀之刃",
        "name": "酋长战刃"
    },
    "rec_wu_yao_fa_zhang": {
        "slot": "weapon",
        "quality": "orange",
        "lv": 20,
        "weapon_type": "staff",
        "mats": {
            "mat_wu_yao_fa_zhang": 3,
            "mat_gui_hun_jing_hua": 8,
            "mat_ling_hun_sui_pian": 8
        },
        "gold": 1500,
        "desc": "巫妖宰相的传说法杖",
        "name": "巫妖法杖"
    },
    "rec_han_shuang_zhi_jian": {
        "slot": "weapon",
        "quality": "blue",
        "lv": 24,
        "weapon_type": "sword",
        "mats": {
            "mat_bing_yuan_mao_pi": 6,
            "mat_ju_mo_xue_rou": 5
        },
        "gold": 500,
        "desc": "极北冰原锻造的利剑",
        "name": "寒霜之剑"
    },
    "rec_lie_yan_fa_zhang": {
        "slot": "weapon",
        "quality": "blue",
        "lv": 24,
        "weapon_type": "staff",
        "mats": {
            "mat_huo_yan_he_xin": 5,
            "mat_rong_yan_shi": 6
        },
        "gold": 500,
        "desc": "熔岩之心铸就的法杖",
        "name": "烈焰法杖"
    },
    "rec_feng_bao_zhi_gong": {
        "slot": "weapon",
        "quality": "blue",
        "lv": 24,
        "weapon_type": "bow",
        "mats": {
            "mat_ju_ying_ling_yu": 6,
            "mat_feng_bao_she_lin": 4
        },
        "gold": 500,
        "desc": "凝聚风暴之力的强弓",
        "name": "风暴之弓"
    },
    "rec_shen_yuan_quan_zhang": {
        "slot": "weapon",
        "quality": "blue",
        "lv": 24,
        "weapon_type": "mace",
        "mats": {
            "mat_an_ying_sui_pian": 6,
            "mat_shen_yuan_jing_gang": 4
        },
        "gold": 500,
        "desc": "浸染深渊气息的权杖",
        "name": "深渊权杖"
    },
    "rec_rong_yan_zhan_jia": {
        "slot": "armor",
        "quality": "purple",
        "lv": 26,
        "mats": {
            "mat_ju_ren_yu_jin": 4,
            "mat_rong_yan_shi": 8,
            "mat_huo_yan_he_xin": 6
        },
        "gold": 1200,
        "desc": "熔岩暴君座下的炽热战甲",
        "name": "熔岩战甲"
    },
    "rec_bing_shuang_zhi_dun": {
        "slot": "armor",
        "quality": "purple",
        "lv": 27,
        "mats": {
            "mat_yong_heng_zhi_bing": 4,
            "mat_bing_yuan_mao_pi": 8,
            "mat_ju_mo_xue_rou": 6
        },
        "gold": 1300,
        "desc": "冰川魔像的永恒之冰铸成",
        "name": "冰霜之盾"
    },
    "rec_lei_ting_zhi_chui": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 29,
        "weapon_type": "sword",
        "mats": {
            "mat_lei_ting_zhi_chui": 2,
            "mat_ju_ying_ling_yu": 8,
            "mat_feng_bao_she_lin": 6
        },
        "gold": 1800,
        "desc": "风暴巨人王的传说武器",
        "name": "雷霆之锤"
    },
    "rec_hei_an_jun_zhu_zhi_ren": {
        "slot": "weapon",
        "quality": "orange",
        "lv": 30,
        "weapon_type": "sword",
        "mats": {
            "mat_hei_an_jun_zhu_zhi_ren": 3,
            "mat_zai_e_zhi_xin": 6,
            "mat_shen_yuan_jing_gang": 8
        },
        "gold": 3000,
        "desc": "魔王·阿兹莫丹的黑暗神兵",
        "name": "黑暗君主之刃"
    },
    "rec_sheng_hui_zhi_jian": {
        "slot": "weapon",
        "quality": "blue",
        "lv": 36,
        "weapon_type": "sword",
        "mats": {
            "mat_sheng_guang_yu_mao": 6,
            "mat_guang_yao_zhi_pi": 5
        },
        "gold": 900,
        "desc": "远境教会的制式圣剑",
        "name": "圣辉之剑"
    },
    "rec_yue_ying_fa_zhang": {
        "slot": "weapon",
        "quality": "blue",
        "lv": 44,
        "weapon_type": "staff",
        "mats": {
            "mat_yue_ying_zhi_pi": 6,
            "mat_sen_lin_zhi_ling": 5
        },
        "gold": 1200,
        "desc": "精灵王庭秘传的月之法杖",
        "name": "月影法杖"
    },
    "rec_long_yi_zhang_gong": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 56,
        "weapon_type": "bow",
        "mats": {
            "mat_fei_long_yi": 5,
            "mat_long_lin": 6,
            "mat_long_yi_hui_ji": 4
        },
        "gold": 2600,
        "desc": "以飞龙之翼锻造的强弓",
        "name": "龙翼长弓"
    },
    "rec_yue_shen_quan_zhang": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 50,
        "weapon_type": "mace",
        "mats": {
            "mat_yue_zhi_lei": 3,
            "mat_jing_ling_fa_zhu": 6,
            "mat_wang_ting_hui_zhang": 4
        },
        "gold": 2400,
        "desc": "月神祭司的祝福权杖",
        "name": "月神权杖"
    },
    "rec_long_lin_zhan_jia": {
        "slot": "armor",
        "quality": "purple",
        "lv": 55,
        "mats": {
            "mat_long_lin": 6,
            "mat_fei_long_yi": 4,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 2800,
        "desc": "古龙之鳞缝制的战甲",
        "name": "龙鳞战甲"
    },
    "rec_yue_shen_zhi_guan": {
        "slot": "helm",
        "quality": "orange",
        "lv": 50,
        "mats": {
            "mat_yue_shen_zhi_guan": 3,
            "mat_yue_zhi_lei": 6,
            "mat_jing_ling_fa_zhu": 8
        },
        "gold": 4000,
        "desc": "精灵女王的月神王冠",
        "name": "月神之冠"
    },
    "rec_long_wang_zhi_jiao": {
        "slot": "helm",
        "quality": "orange",
        "lv": 60,
        "mats": {
            "mat_long_wang_zhi_jiao": 3,
            "mat_long_lin": 8,
            "mat_long_yan_jing_hua": 6
        },
        "gold": 5000,
        "desc": "古龙·奥瑞斯的龙角之冠",
        "name": "龙王之角"
    },
    "rec_lie_xi_zhi_ren": {
        "slot": "weapon",
        "quality": "blue",
        "lv": 66,
        "weapon_type": "sword",
        "mats": {
            "mat_xu_kong_zhi_zhao": 6,
            "mat_yan_mie_sui_pian": 5
        },
        "gold": 2000,
        "desc": "从裂隙中取出的利刃",
        "name": "裂隙之刃"
    },
    "rec_shi_hun_fa_zhang": {
        "slot": "weapon",
        "quality": "blue",
        "lv": 66,
        "weapon_type": "staff",
        "mats": {
            "mat_shi_hun_jie_jing": 6,
            "mat_shen_yuan_fa_zhu": 5
        },
        "gold": 2000,
        "desc": "吞噬灵魂的邪恶法杖",
        "name": "噬魂法杖"
    },
    "rec_shen_pan_zhi_gong": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 76,
        "weapon_type": "bow",
        "mats": {
            "mat_shen_pan_guan_zhi_yin": 3,
            "mat_chu_xing_zhe_zhi_fu": 5,
            "mat_jin_wei_kai_jia": 6
        },
        "gold": 4000,
        "desc": "审判官狩猎异端的圣弓",
        "name": "审判之弓"
    },
    "rec_jiao_zong_quan_zhang": {
        "slot": "weapon",
        "quality": "orange",
        "lv": 80,
        "weapon_type": "mace",
        "mats": {
            "mat_jiao_zong_quan_zhang": 3,
            "mat_da_ji_si_zhi_huan": 6,
            "mat_duo_luo_sheng_hui": 8
        },
        "gold": 8000,
        "desc": "大祭司·克劳斯的教宗权杖",
        "name": "教宗权杖"
    },
    "rec_tun_shi_zhe_zhi_he": {
        "slot": "necklace",
        "quality": "orange",
        "lv": 70,
        "mats": {
            "mat_tun_shi_zhe_zhi_he": 3,
            "mat_lie_xi_zhu_zai_quan_zhang": 5,
            "mat_xu_kong_hu_jia": 6
        },
        "gold": 7000,
        "desc": "裂隙巨兽的吞噬核心",
        "name": "吞噬者之核"
    },
    "rec_si_ji_wang_guan": {
        "slot": "helm",
        "quality": "orange",
        "lv": 90,
        "mats": {
            "mat_si_ji_wang_guan": 3,
            "mat_ku_gu_ling_zhu_zhi_huan": 6,
            "mat_si_ji_zhi_ren": 5
        },
        "gold": 10000,
        "desc": "白骨君王的死寂王冠",
        "name": "死寂王冠"
    },
    "rec_xing_jie_zhi_jian": {
        "slot": "weapon",
        "quality": "blue",
        "lv": 94,
        "weapon_type": "sword",
        "mats": {
            "mat_xing_jie_zhi_chen": 6,
            "mat_tian_qiong_hu_jia": 5
        },
        "gold": 4000,
        "desc": "星光淬炼的神兵",
        "name": "星界之剑"
    },
    "rec_hun_dun_fa_zhu": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 96,
        "weapon_type": "staff",
        "mats": {
            "mat_hun_dun_sui_pian": 6,
            "mat_hun_dun_zhi_zha": 5,
            "mat_xing_jie_fa_zhu": 4
        },
        "gold": 8000,
        "desc": "混沌初开的法珠",
        "name": "混沌法珠"
    },
    "rec_tian_qiong_zhi_gong": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 96,
        "weapon_type": "bow",
        "mats": {
            "mat_zhu_shen_yi_hui": 6,
            "mat_shen_yu_zhan_hun": 5,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 8000,
        "desc": "天穹之巅的神弓",
        "name": "天穹之弓"
    },
    "rec_shen_yu_quan_zhang": {
        "slot": "weapon",
        "quality": "orange",
        "lv": 98,
        "weapon_type": "mace",
        "mats": {
            "mat_men_fei_zhi_yao": 5,
            "mat_shen_yu_jing_hua": 8,
            "mat_zhu_shen_yi_hui": 6
        },
        "gold": 15000,
        "desc": "开启神域之门的权杖",
        "name": "神域权杖"
    },
    "rec_tian_qiong_zhi_guan": {
        "slot": "helm",
        "quality": "orange",
        "lv": 96,
        "mats": {
            "mat_tian_qiong_zhi_guan": 3,
            "mat_xing_jie_qi_shi_jian": 5,
            "mat_tian_qiong_hu_jia": 8
        },
        "gold": 12000,
        "desc": "王城守望者的天穹王冠",
        "name": "天穹之冠"
    },
    "rec_hun_dun_zhi_he": {
        "slot": "necklace",
        "quality": "orange",
        "lv": 100,
        "mats": {
            "mat_hun_dun_zhi_he": 3,
            "mat_hun_dun_sui_pian": 8,
            "mat_xing_jie_zhi_chen": 10
        },
        "gold": 20000,
        "desc": "巫王·莫里斯的力量之源",
        "name": "混沌之核"
    },
    "rec_tie_pi_tou_kui": {
        "slot": "helm",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "铁皮图纸",
        "class": "cls_zhan_shi",
        "set": "set_tie_pi",
        "desc": "铁皮套装·Ⅰ阶核心部件",
        "name": "铁皮头盔"
    },
    "rec_tie_pi_xiong_jia": {
        "slot": "armor",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "铁皮图纸",
        "class": "cls_zhan_shi",
        "set": "set_tie_pi",
        "desc": "铁皮套装·Ⅰ阶核心部件",
        "name": "铁皮胸甲"
    },
    "rec_tie_pi_hu_tui": {
        "slot": "legs",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "铁皮图纸",
        "class": "cls_zhan_shi",
        "set": "set_tie_pi",
        "desc": "铁皮套装·Ⅰ阶核心部件",
        "name": "铁皮护腿"
    },
    "rec_tie_pi_zhan_xue": {
        "slot": "boots",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "铁皮图纸",
        "class": "cls_zhan_shi",
        "set": "set_tie_pi",
        "desc": "铁皮套装·Ⅰ阶核心部件",
        "name": "铁皮战靴"
    },
    "rec_jing_tie_zhang_jian": {
        "slot": "weapon",
        "quality": "blue",
        "lv": 30,
        "weapon_type": "sword",
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "精铁图纸",
        "class": "cls_zhan_shi",
        "set": "set_jing_tie",
        "desc": "精铁套装·Ⅱ阶核心部件",
        "name": "精铁长剑"
    },
    "rec_jing_tie_tou_kui": {
        "slot": "helm",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "精铁图纸",
        "class": "cls_zhan_shi",
        "set": "set_jing_tie",
        "desc": "精铁套装·Ⅱ阶核心部件",
        "name": "精铁头盔"
    },
    "rec_jing_tie_xiong_jia": {
        "slot": "armor",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "精铁图纸",
        "class": "cls_zhan_shi",
        "set": "set_jing_tie",
        "desc": "精铁套装·Ⅱ阶核心部件",
        "name": "精铁胸甲"
    },
    "rec_jing_tie_hu_tui": {
        "slot": "legs",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "精铁图纸",
        "class": "cls_zhan_shi",
        "set": "set_jing_tie",
        "desc": "精铁套装·Ⅱ阶核心部件",
        "name": "精铁护腿"
    },
    "rec_jing_tie_zhan_xue": {
        "slot": "boots",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "精铁图纸",
        "class": "cls_zhan_shi",
        "set": "set_jing_tie",
        "desc": "精铁套装·Ⅱ阶核心部件",
        "name": "精铁战靴"
    },
    "rec_qi_shi_zhang_jian": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 50,
        "weapon_type": "sword",
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "骑士图纸",
        "class": "cls_zhan_shi",
        "set": "set_qi_shi",
        "desc": "骑士套装·Ⅲ阶核心部件",
        "name": "骑士长剑"
    },
    "rec_qi_shi_tou_kui": {
        "slot": "helm",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "骑士图纸",
        "class": "cls_zhan_shi",
        "set": "set_qi_shi",
        "desc": "骑士套装·Ⅲ阶核心部件",
        "name": "骑士头盔"
    },
    "rec_qi_shi_xiong_jia": {
        "slot": "armor",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "骑士图纸",
        "class": "cls_zhan_shi",
        "set": "set_qi_shi",
        "desc": "骑士套装·Ⅲ阶核心部件",
        "name": "骑士胸甲"
    },
    "rec_qi_shi_hu_tui": {
        "slot": "legs",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "骑士图纸",
        "class": "cls_zhan_shi",
        "set": "set_qi_shi",
        "desc": "骑士套装·Ⅲ阶核心部件",
        "name": "骑士护腿"
    },
    "rec_qi_shi_zhan_xue": {
        "slot": "boots",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "骑士图纸",
        "class": "cls_zhan_shi",
        "set": "set_qi_shi",
        "desc": "骑士套装·Ⅲ阶核心部件",
        "name": "骑士战靴"
    },
    "rec_shou_wang_zhe_zhi_jian": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 70,
        "weapon_type": "sword",
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "守望图纸",
        "class": "cls_zhan_shi",
        "set": "set_shou_wang",
        "desc": "守望套装·Ⅳ阶核心部件",
        "name": "守望者之剑"
    },
    "rec_shou_wang_tou_kui": {
        "slot": "helm",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "守望图纸",
        "class": "cls_zhan_shi",
        "set": "set_shou_wang",
        "desc": "守望套装·Ⅳ阶核心部件",
        "name": "守望头盔"
    },
    "rec_shou_wang_xiong_jia": {
        "slot": "armor",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "守望图纸",
        "class": "cls_zhan_shi",
        "set": "set_shou_wang",
        "desc": "守望套装·Ⅳ阶核心部件",
        "name": "守望胸甲"
    },
    "rec_shou_wang_hu_tui": {
        "slot": "legs",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "守望图纸",
        "class": "cls_zhan_shi",
        "set": "set_shou_wang",
        "desc": "守望套装·Ⅳ阶核心部件",
        "name": "守望护腿"
    },
    "rec_shou_wang_zhan_xue": {
        "slot": "boots",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "守望图纸",
        "class": "cls_zhan_shi",
        "set": "set_shou_wang",
        "desc": "守望套装·Ⅳ阶核心部件",
        "name": "守望战靴"
    },
    "rec_li_ming_sheng_jian": {
        "slot": "weapon",
        "quality": "orange",
        "lv": 90,
        "weapon_type": "sword",
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "黎明图纸",
        "class": "cls_zhan_shi",
        "set": "set_li_ming",
        "desc": "黎明套装·Ⅴ阶核心部件",
        "name": "黎明圣剑"
    },
    "rec_li_ming_tou_kui": {
        "slot": "helm",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "黎明图纸",
        "class": "cls_zhan_shi",
        "set": "set_li_ming",
        "desc": "黎明套装·Ⅴ阶核心部件",
        "name": "黎明头盔"
    },
    "rec_li_ming_xiong_jia": {
        "slot": "armor",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "黎明图纸",
        "class": "cls_zhan_shi",
        "set": "set_li_ming",
        "desc": "黎明套装·Ⅴ阶核心部件",
        "name": "黎明胸甲"
    },
    "rec_li_ming_hu_tui": {
        "slot": "legs",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "黎明图纸",
        "class": "cls_zhan_shi",
        "set": "set_li_ming",
        "desc": "黎明套装·Ⅴ阶核心部件",
        "name": "黎明护腿"
    },
    "rec_li_ming_zhan_xue": {
        "slot": "boots",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "黎明图纸",
        "class": "cls_zhan_shi",
        "set": "set_li_ming",
        "desc": "黎明套装·Ⅴ阶核心部件",
        "name": "黎明战靴"
    },
    "rec_jian_xi_fa_zhang": {
        "slot": "weapon",
        "quality": "blue",
        "lv": 10,
        "weapon_type": "staff",
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "学徒图纸",
        "class": "cls_fa_shi",
        "set": "set_xue_tu",
        "desc": "学徒套装·Ⅰ阶核心部件",
        "name": "见习法杖"
    },
    "rec_xue_tu_fa_mao": {
        "slot": "helm",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "学徒图纸",
        "class": "cls_fa_shi",
        "set": "set_xue_tu",
        "desc": "学徒套装·Ⅰ阶核心部件",
        "name": "学徒法帽"
    },
    "rec_xue_tu_zhang_pao": {
        "slot": "armor",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "学徒图纸",
        "class": "cls_fa_shi",
        "set": "set_xue_tu",
        "desc": "学徒套装·Ⅰ阶核心部件",
        "name": "学徒长袍"
    },
    "rec_xue_tu_hu_tui": {
        "slot": "legs",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "学徒图纸",
        "class": "cls_fa_shi",
        "set": "set_xue_tu",
        "desc": "学徒套装·Ⅰ阶核心部件",
        "name": "学徒护腿"
    },
    "rec_xue_tu_fa_xue": {
        "slot": "boots",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "学徒图纸",
        "class": "cls_fa_shi",
        "set": "set_xue_tu",
        "desc": "学徒套装·Ⅰ阶核心部件",
        "name": "学徒法靴"
    },
    "rec_fu_wen_fa_zhang": {
        "slot": "weapon",
        "quality": "blue",
        "lv": 30,
        "weapon_type": "staff",
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "符文图纸",
        "class": "cls_fa_shi",
        "set": "set_fu_wen",
        "desc": "符文套装·Ⅱ阶核心部件",
        "name": "符文法杖"
    },
    "rec_fu_wen_fa_mao": {
        "slot": "helm",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "符文图纸",
        "class": "cls_fa_shi",
        "set": "set_fu_wen",
        "desc": "符文套装·Ⅱ阶核心部件",
        "name": "符文法帽"
    },
    "rec_fu_wen_zhang_pao": {
        "slot": "armor",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "符文图纸",
        "class": "cls_fa_shi",
        "set": "set_fu_wen",
        "desc": "符文套装·Ⅱ阶核心部件",
        "name": "符文长袍"
    },
    "rec_fu_wen_hu_tui": {
        "slot": "legs",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "符文图纸",
        "class": "cls_fa_shi",
        "set": "set_fu_wen",
        "desc": "符文套装·Ⅱ阶核心部件",
        "name": "符文护腿"
    },
    "rec_fu_wen_fa_xue": {
        "slot": "boots",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "符文图纸",
        "class": "cls_fa_shi",
        "set": "set_fu_wen",
        "desc": "符文套装·Ⅱ阶核心部件",
        "name": "符文法靴"
    },
    "rec_mi_fa_fa_zhang": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 50,
        "weapon_type": "staff",
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "秘法图纸",
        "class": "cls_fa_shi",
        "set": "set_mi_fa",
        "desc": "秘法套装·Ⅲ阶核心部件",
        "name": "秘法法杖"
    },
    "rec_mi_fa_fa_mao": {
        "slot": "helm",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "秘法图纸",
        "class": "cls_fa_shi",
        "set": "set_mi_fa",
        "desc": "秘法套装·Ⅲ阶核心部件",
        "name": "秘法法帽"
    },
    "rec_mi_fa_zhang_pao": {
        "slot": "armor",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "秘法图纸",
        "class": "cls_fa_shi",
        "set": "set_mi_fa",
        "desc": "秘法套装·Ⅲ阶核心部件",
        "name": "秘法长袍"
    },
    "rec_mi_fa_hu_tui": {
        "slot": "legs",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "秘法图纸",
        "class": "cls_fa_shi",
        "set": "set_mi_fa",
        "desc": "秘法套装·Ⅲ阶核心部件",
        "name": "秘法护腿"
    },
    "rec_mi_fa_fa_xue": {
        "slot": "boots",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "秘法图纸",
        "class": "cls_fa_shi",
        "set": "set_mi_fa",
        "desc": "秘法套装·Ⅲ阶核心部件",
        "name": "秘法法靴"
    },
    "rec_xing_jie_fa_zhang": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 70,
        "weapon_type": "staff",
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "星界图纸",
        "class": "cls_fa_shi",
        "set": "set_xing_jie",
        "desc": "星界套装·Ⅳ阶核心部件",
        "name": "星界法杖"
    },
    "rec_xing_jie_fa_mao": {
        "slot": "helm",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "星界图纸",
        "class": "cls_fa_shi",
        "set": "set_xing_jie",
        "desc": "星界套装·Ⅳ阶核心部件",
        "name": "星界法帽"
    },
    "rec_xing_jie_zhang_pao": {
        "slot": "armor",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "星界图纸",
        "class": "cls_fa_shi",
        "set": "set_xing_jie",
        "desc": "星界套装·Ⅳ阶核心部件",
        "name": "星界长袍"
    },
    "rec_xing_jie_hu_tui": {
        "slot": "legs",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "星界图纸",
        "class": "cls_fa_shi",
        "set": "set_xing_jie",
        "desc": "星界套装·Ⅳ阶核心部件",
        "name": "星界护腿"
    },
    "rec_xing_jie_fa_xue": {
        "slot": "boots",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "星界图纸",
        "class": "cls_fa_shi",
        "set": "set_xing_jie",
        "desc": "星界套装·Ⅳ阶核心部件",
        "name": "星界法靴"
    },
    "rec_xing_chen_fa_zhang": {
        "slot": "weapon",
        "quality": "orange",
        "lv": 90,
        "weapon_type": "staff",
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "星辰图纸",
        "class": "cls_fa_shi",
        "set": "set_xing_chen",
        "desc": "星辰套装·Ⅴ阶核心部件",
        "name": "星辰法杖"
    },
    "rec_xing_chen_fa_mao": {
        "slot": "helm",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "星辰图纸",
        "class": "cls_fa_shi",
        "set": "set_xing_chen",
        "desc": "星辰套装·Ⅴ阶核心部件",
        "name": "星辰法帽"
    },
    "rec_xing_chen_zhang_pao": {
        "slot": "armor",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "星辰图纸",
        "class": "cls_fa_shi",
        "set": "set_xing_chen",
        "desc": "星辰套装·Ⅴ阶核心部件",
        "name": "星辰长袍"
    },
    "rec_xing_chen_hu_tui": {
        "slot": "legs",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "星辰图纸",
        "class": "cls_fa_shi",
        "set": "set_xing_chen",
        "desc": "星辰套装·Ⅴ阶核心部件",
        "name": "星辰护腿"
    },
    "rec_xing_chen_fa_xue": {
        "slot": "boots",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "星辰图纸",
        "class": "cls_fa_shi",
        "set": "set_xing_chen",
        "desc": "星辰套装·Ⅴ阶核心部件",
        "name": "星辰法靴"
    },
    "rec_lie_shou_pi_mao": {
        "slot": "helm",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "猎手图纸",
        "class": "cls_you_xia",
        "set": "set_lie_shou",
        "desc": "猎手套装·Ⅰ阶核心部件",
        "name": "猎手皮帽"
    },
    "rec_lie_shou_pi_jia": {
        "slot": "armor",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "猎手图纸",
        "class": "cls_you_xia",
        "set": "set_lie_shou",
        "desc": "猎手套装·Ⅰ阶核心部件",
        "name": "猎手皮甲"
    },
    "rec_lie_shou_hu_tui": {
        "slot": "legs",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "猎手图纸",
        "class": "cls_you_xia",
        "set": "set_lie_shou",
        "desc": "猎手套装·Ⅰ阶核心部件",
        "name": "猎手护腿"
    },
    "rec_lie_shou_zhang_xue": {
        "slot": "boots",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "猎手图纸",
        "class": "cls_you_xia",
        "set": "set_lie_shou",
        "desc": "猎手套装·Ⅰ阶核心部件",
        "name": "猎手长靴"
    },
    "rec_lie_shou_zhang_gong": {
        "slot": "weapon",
        "quality": "blue",
        "lv": 30,
        "weapon_type": "bow",
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "风行图纸",
        "class": "cls_you_xia",
        "set": "set_feng_xing",
        "desc": "风行套装·Ⅱ阶核心部件",
        "name": "猎手长弓"
    },
    "rec_feng_xing_pi_mao": {
        "slot": "helm",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "风行图纸",
        "class": "cls_you_xia",
        "set": "set_feng_xing",
        "desc": "风行套装·Ⅱ阶核心部件",
        "name": "风行皮帽"
    },
    "rec_feng_xing_pi_jia": {
        "slot": "armor",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "风行图纸",
        "class": "cls_you_xia",
        "set": "set_feng_xing",
        "desc": "风行套装·Ⅱ阶核心部件",
        "name": "风行皮甲"
    },
    "rec_feng_xing_hu_tui": {
        "slot": "legs",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "风行图纸",
        "class": "cls_you_xia",
        "set": "set_feng_xing",
        "desc": "风行套装·Ⅱ阶核心部件",
        "name": "风行护腿"
    },
    "rec_feng_xing_zhang_xue": {
        "slot": "boots",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "风行图纸",
        "class": "cls_you_xia",
        "set": "set_feng_xing",
        "desc": "风行套装·Ⅱ阶核心部件",
        "name": "风行长靴"
    },
    "rec_feng_xing_zhang_gong": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 50,
        "weapon_type": "bow",
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "暗夜图纸",
        "class": "cls_you_xia",
        "set": "set_an_ye",
        "desc": "暗夜套装·Ⅲ阶核心部件",
        "name": "风行长弓"
    },
    "rec_an_ye_pi_mao": {
        "slot": "helm",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "暗夜图纸",
        "class": "cls_you_xia",
        "set": "set_an_ye",
        "desc": "暗夜套装·Ⅲ阶核心部件",
        "name": "暗夜皮帽"
    },
    "rec_an_ye_pi_jia": {
        "slot": "armor",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "暗夜图纸",
        "class": "cls_you_xia",
        "set": "set_an_ye",
        "desc": "暗夜套装·Ⅲ阶核心部件",
        "name": "暗夜皮甲"
    },
    "rec_an_ye_hu_tui": {
        "slot": "legs",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "暗夜图纸",
        "class": "cls_you_xia",
        "set": "set_an_ye",
        "desc": "暗夜套装·Ⅲ阶核心部件",
        "name": "暗夜护腿"
    },
    "rec_an_ye_zhang_xue": {
        "slot": "boots",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "暗夜图纸",
        "class": "cls_you_xia",
        "set": "set_an_ye",
        "desc": "暗夜套装·Ⅲ阶核心部件",
        "name": "暗夜长靴"
    },
    "rec_ying_yan_zhi_gong": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 70,
        "weapon_type": "bow",
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "鹰眼图纸",
        "class": "cls_you_xia",
        "set": "set_ying_yan",
        "desc": "鹰眼套装·Ⅳ阶核心部件",
        "name": "鹰眼之弓"
    },
    "rec_ying_yan_pi_mao": {
        "slot": "helm",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "鹰眼图纸",
        "class": "cls_you_xia",
        "set": "set_ying_yan",
        "desc": "鹰眼套装·Ⅳ阶核心部件",
        "name": "鹰眼皮帽"
    },
    "rec_ying_yan_pi_jia": {
        "slot": "armor",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "鹰眼图纸",
        "class": "cls_you_xia",
        "set": "set_ying_yan",
        "desc": "鹰眼套装·Ⅳ阶核心部件",
        "name": "鹰眼皮甲"
    },
    "rec_ying_yan_hu_tui": {
        "slot": "legs",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "鹰眼图纸",
        "class": "cls_you_xia",
        "set": "set_ying_yan",
        "desc": "鹰眼套装·Ⅳ阶核心部件",
        "name": "鹰眼护腿"
    },
    "rec_ying_yan_zhang_xue": {
        "slot": "boots",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "鹰眼图纸",
        "class": "cls_you_xia",
        "set": "set_ying_yan",
        "desc": "鹰眼套装·Ⅳ阶核心部件",
        "name": "鹰眼长靴"
    },
    "rec_cang_qiong_zhi_gong": {
        "slot": "weapon",
        "quality": "orange",
        "lv": 90,
        "weapon_type": "bow",
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "苍穹图纸",
        "class": "cls_you_xia",
        "set": "set_cang_qiong",
        "desc": "苍穹套装·Ⅴ阶核心部件",
        "name": "苍穹之弓"
    },
    "rec_cang_qiong_pi_mao": {
        "slot": "helm",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "苍穹图纸",
        "class": "cls_you_xia",
        "set": "set_cang_qiong",
        "desc": "苍穹套装·Ⅴ阶核心部件",
        "name": "苍穹皮帽"
    },
    "rec_cang_qiong_pi_jia": {
        "slot": "armor",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "苍穹图纸",
        "class": "cls_you_xia",
        "set": "set_cang_qiong",
        "desc": "苍穹套装·Ⅴ阶核心部件",
        "name": "苍穹皮甲"
    },
    "rec_cang_qiong_hu_tui": {
        "slot": "legs",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "苍穹图纸",
        "class": "cls_you_xia",
        "set": "set_cang_qiong",
        "desc": "苍穹套装·Ⅴ阶核心部件",
        "name": "苍穹护腿"
    },
    "rec_cang_qiong_zhang_xue": {
        "slot": "boots",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "苍穹图纸",
        "class": "cls_you_xia",
        "set": "set_cang_qiong",
        "desc": "苍穹套装·Ⅴ阶核心部件",
        "name": "苍穹长靴"
    },
    "rec_bu_yi_sheng_guan": {
        "slot": "helm",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "布衣图纸",
        "class": "cls_mu_shi",
        "set": "set_bu_yi",
        "desc": "布衣套装·Ⅰ阶核心部件",
        "name": "布衣圣冠"
    },
    "rec_bu_yi_fa_yi": {
        "slot": "armor",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "布衣图纸",
        "class": "cls_mu_shi",
        "set": "set_bu_yi",
        "desc": "布衣套装·Ⅰ阶核心部件",
        "name": "布衣法衣"
    },
    "rec_bu_yi_hu_tui": {
        "slot": "legs",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "布衣图纸",
        "class": "cls_mu_shi",
        "set": "set_bu_yi",
        "desc": "布衣套装·Ⅰ阶核心部件",
        "name": "布衣护腿"
    },
    "rec_bu_yi_sheng_xue": {
        "slot": "boots",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "布衣图纸",
        "class": "cls_mu_shi",
        "set": "set_bu_yi",
        "desc": "布衣套装·Ⅰ阶核心部件",
        "name": "布衣圣靴"
    },
    "rec_zhu_fu_quan_zhang": {
        "slot": "weapon",
        "quality": "blue",
        "lv": 30,
        "weapon_type": "mace",
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "祝福图纸",
        "class": "cls_mu_shi",
        "set": "set_zhu_fu",
        "desc": "祝福套装·Ⅱ阶核心部件",
        "name": "祝福权杖"
    },
    "rec_zhu_fu_sheng_guan": {
        "slot": "helm",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "祝福图纸",
        "class": "cls_mu_shi",
        "set": "set_zhu_fu",
        "desc": "祝福套装·Ⅱ阶核心部件",
        "name": "祝福圣冠"
    },
    "rec_zhu_fu_fa_yi": {
        "slot": "armor",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "祝福图纸",
        "class": "cls_mu_shi",
        "set": "set_zhu_fu",
        "desc": "祝福套装·Ⅱ阶核心部件",
        "name": "祝福法衣"
    },
    "rec_zhu_fu_hu_tui": {
        "slot": "legs",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "祝福图纸",
        "class": "cls_mu_shi",
        "set": "set_zhu_fu",
        "desc": "祝福套装·Ⅱ阶核心部件",
        "name": "祝福护腿"
    },
    "rec_zhu_fu_sheng_xue": {
        "slot": "boots",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "祝福图纸",
        "class": "cls_mu_shi",
        "set": "set_zhu_fu",
        "desc": "祝福套装·Ⅱ阶核心部件",
        "name": "祝福圣靴"
    },
    "rec_sheng_tang_quan_zhang": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 50,
        "weapon_type": "mace",
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "圣堂图纸",
        "class": "cls_mu_shi",
        "set": "set_sheng_tang",
        "desc": "圣堂套装·Ⅲ阶核心部件",
        "name": "圣堂权杖"
    },
    "rec_sheng_tang_sheng_guan": {
        "slot": "helm",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "圣堂图纸",
        "class": "cls_mu_shi",
        "set": "set_sheng_tang",
        "desc": "圣堂套装·Ⅲ阶核心部件",
        "name": "圣堂圣冠"
    },
    "rec_sheng_tang_fa_yi": {
        "slot": "armor",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "圣堂图纸",
        "class": "cls_mu_shi",
        "set": "set_sheng_tang",
        "desc": "圣堂套装·Ⅲ阶核心部件",
        "name": "圣堂法衣"
    },
    "rec_sheng_tang_hu_tui": {
        "slot": "legs",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "圣堂图纸",
        "class": "cls_mu_shi",
        "set": "set_sheng_tang",
        "desc": "圣堂套装·Ⅲ阶核心部件",
        "name": "圣堂护腿"
    },
    "rec_sheng_tang_sheng_xue": {
        "slot": "boots",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "圣堂图纸",
        "class": "cls_mu_shi",
        "set": "set_sheng_tang",
        "desc": "圣堂套装·Ⅲ阶核心部件",
        "name": "圣堂圣靴"
    },
    "rec_shen_pan_zhi_zhang": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 70,
        "weapon_type": "mace",
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "审判图纸",
        "class": "cls_mu_shi",
        "set": "set_shen_pan",
        "desc": "审判套装·Ⅳ阶核心部件",
        "name": "审判之杖"
    },
    "rec_shen_pan_sheng_guan": {
        "slot": "helm",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "审判图纸",
        "class": "cls_mu_shi",
        "set": "set_shen_pan",
        "desc": "审判套装·Ⅳ阶核心部件",
        "name": "审判圣冠"
    },
    "rec_shen_pan_fa_yi": {
        "slot": "armor",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "审判图纸",
        "class": "cls_mu_shi",
        "set": "set_shen_pan",
        "desc": "审判套装·Ⅳ阶核心部件",
        "name": "审判法衣"
    },
    "rec_shen_pan_hu_tui": {
        "slot": "legs",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "审判图纸",
        "class": "cls_mu_shi",
        "set": "set_shen_pan",
        "desc": "审判套装·Ⅳ阶核心部件",
        "name": "审判护腿"
    },
    "rec_shen_pan_sheng_xue": {
        "slot": "boots",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "审判图纸",
        "class": "cls_mu_shi",
        "set": "set_shen_pan",
        "desc": "审判套装·Ⅳ阶核心部件",
        "name": "审判圣靴"
    },
    "rec_shen_en_quan_zhang": {
        "slot": "weapon",
        "quality": "orange",
        "lv": 90,
        "weapon_type": "mace",
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "神恩图纸",
        "class": "cls_mu_shi",
        "set": "set_shen_en",
        "desc": "神恩套装·Ⅴ阶核心部件",
        "name": "神恩权杖"
    },
    "rec_shen_en_sheng_guan": {
        "slot": "helm",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "神恩图纸",
        "class": "cls_mu_shi",
        "set": "set_shen_en",
        "desc": "神恩套装·Ⅴ阶核心部件",
        "name": "神恩圣冠"
    },
    "rec_shen_en_fa_yi": {
        "slot": "armor",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "神恩图纸",
        "class": "cls_mu_shi",
        "set": "set_shen_en",
        "desc": "神恩套装·Ⅴ阶核心部件",
        "name": "神恩法衣"
    },
    "rec_shen_en_hu_tui": {
        "slot": "legs",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "神恩图纸",
        "class": "cls_mu_shi",
        "set": "set_shen_en",
        "desc": "神恩套装·Ⅴ阶核心部件",
        "name": "神恩护腿"
    },
    "rec_shen_en_sheng_xue": {
        "slot": "boots",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "神恩图纸",
        "class": "cls_mu_shi",
        "set": "set_shen_en",
        "desc": "神恩套装·Ⅴ阶核心部件",
        "name": "神恩圣靴"
    },
    "rec_qing_ying_mian_jin": {
        "slot": "helm",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "轻影图纸",
        "class": "cls_ci_ke",
        "set": "set_qing_ying",
        "desc": "轻影套装·Ⅰ阶核心部件",
        "name": "轻影面巾"
    },
    "rec_qing_ying_pi_yi": {
        "slot": "armor",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "轻影图纸",
        "class": "cls_ci_ke",
        "set": "set_qing_ying",
        "desc": "轻影套装·Ⅰ阶核心部件",
        "name": "轻影皮衣"
    },
    "rec_qing_ying_hu_tui": {
        "slot": "legs",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "轻影图纸",
        "class": "cls_ci_ke",
        "set": "set_qing_ying",
        "desc": "轻影套装·Ⅰ阶核心部件",
        "name": "轻影护腿"
    },
    "rec_qing_ying_qing_xue": {
        "slot": "boots",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "轻影图纸",
        "class": "cls_ci_ke",
        "set": "set_qing_ying",
        "desc": "轻影套装·Ⅰ阶核心部件",
        "name": "轻影轻靴"
    },
    "rec_ye_xing_bi_shou": {
        "slot": "weapon",
        "quality": "blue",
        "lv": 30,
        "weapon_type": "dagger",
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "夜行图纸",
        "class": "cls_ci_ke",
        "set": "set_ye_xing",
        "desc": "夜行套装·Ⅱ阶核心部件",
        "name": "夜行匕首"
    },
    "rec_ye_xing_mian_jin": {
        "slot": "helm",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "夜行图纸",
        "class": "cls_ci_ke",
        "set": "set_ye_xing",
        "desc": "夜行套装·Ⅱ阶核心部件",
        "name": "夜行面巾"
    },
    "rec_ye_xing_pi_yi": {
        "slot": "armor",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "夜行图纸",
        "class": "cls_ci_ke",
        "set": "set_ye_xing",
        "desc": "夜行套装·Ⅱ阶核心部件",
        "name": "夜行皮衣"
    },
    "rec_ye_xing_hu_tui": {
        "slot": "legs",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "夜行图纸",
        "class": "cls_ci_ke",
        "set": "set_ye_xing",
        "desc": "夜行套装·Ⅱ阶核心部件",
        "name": "夜行护腿"
    },
    "rec_ye_xing_qing_xue": {
        "slot": "boots",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "夜行图纸",
        "class": "cls_ci_ke",
        "set": "set_ye_xing",
        "desc": "夜行套装·Ⅱ阶核心部件",
        "name": "夜行轻靴"
    },
    "rec_yin_ying_bi_shou": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 50,
        "weapon_type": "dagger",
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "阴影图纸",
        "class": "cls_ci_ke",
        "set": "set_yin_ying",
        "desc": "阴影套装·Ⅲ阶核心部件",
        "name": "阴影匕首"
    },
    "rec_yin_ying_mian_jin": {
        "slot": "helm",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "阴影图纸",
        "class": "cls_ci_ke",
        "set": "set_yin_ying",
        "desc": "阴影套装·Ⅲ阶核心部件",
        "name": "阴影面巾"
    },
    "rec_yin_ying_pi_yi": {
        "slot": "armor",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "阴影图纸",
        "class": "cls_ci_ke",
        "set": "set_yin_ying",
        "desc": "阴影套装·Ⅲ阶核心部件",
        "name": "阴影皮衣"
    },
    "rec_yin_ying_hu_tui": {
        "slot": "legs",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "阴影图纸",
        "class": "cls_ci_ke",
        "set": "set_yin_ying",
        "desc": "阴影套装·Ⅲ阶核心部件",
        "name": "阴影护腿"
    },
    "rec_yin_ying_qing_xue": {
        "slot": "boots",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "阴影图纸",
        "class": "cls_ci_ke",
        "set": "set_yin_ying",
        "desc": "阴影套装·Ⅲ阶核心部件",
        "name": "阴影轻靴"
    },
    "rec_huan_ying_zhi_bi": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 70,
        "weapon_type": "dagger",
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "幻影图纸",
        "class": "cls_ci_ke",
        "set": "set_huan_ying",
        "desc": "幻影套装·Ⅳ阶核心部件",
        "name": "幻影之匕"
    },
    "rec_huan_ying_mian_jin": {
        "slot": "helm",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "幻影图纸",
        "class": "cls_ci_ke",
        "set": "set_huan_ying",
        "desc": "幻影套装·Ⅳ阶核心部件",
        "name": "幻影面巾"
    },
    "rec_huan_ying_pi_yi": {
        "slot": "armor",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "幻影图纸",
        "class": "cls_ci_ke",
        "set": "set_huan_ying",
        "desc": "幻影套装·Ⅳ阶核心部件",
        "name": "幻影皮衣"
    },
    "rec_huan_ying_hu_tui": {
        "slot": "legs",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "幻影图纸",
        "class": "cls_ci_ke",
        "set": "set_huan_ying",
        "desc": "幻影套装·Ⅳ阶核心部件",
        "name": "幻影护腿"
    },
    "rec_huan_ying_qing_xue": {
        "slot": "boots",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "幻影图纸",
        "class": "cls_ci_ke",
        "set": "set_huan_ying",
        "desc": "幻影套装·Ⅳ阶核心部件",
        "name": "幻影轻靴"
    },
    "rec_wu_ye_zhi_ren": {
        "slot": "weapon",
        "quality": "orange",
        "lv": 90,
        "weapon_type": "dagger",
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "午夜图纸",
        "class": "cls_ci_ke",
        "set": "set_wu_ye",
        "desc": "午夜套装·Ⅴ阶核心部件",
        "name": "午夜之刃"
    },
    "rec_wu_ye_mian_jin": {
        "slot": "helm",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "午夜图纸",
        "class": "cls_ci_ke",
        "set": "set_wu_ye",
        "desc": "午夜套装·Ⅴ阶核心部件",
        "name": "午夜面巾"
    },
    "rec_wu_ye_pi_yi": {
        "slot": "armor",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "午夜图纸",
        "class": "cls_ci_ke",
        "set": "set_wu_ye",
        "desc": "午夜套装·Ⅴ阶核心部件",
        "name": "午夜皮衣"
    },
    "rec_wu_ye_hu_tui": {
        "slot": "legs",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "午夜图纸",
        "class": "cls_ci_ke",
        "set": "set_wu_ye",
        "desc": "午夜套装·Ⅴ阶核心部件",
        "name": "午夜护腿"
    },
    "rec_wu_ye_qing_xue": {
        "slot": "boots",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "午夜图纸",
        "class": "cls_ci_ke",
        "set": "set_wu_ye",
        "desc": "午夜套装·Ⅴ阶核心部件",
        "name": "午夜轻靴"
    },
    "rec_xing_zhe_tou_dai": {
        "slot": "helm",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "行者图纸",
        "class": "cls_wu_seng",
        "set": "set_xing_zhe",
        "desc": "行者套装·Ⅰ阶核心部件",
        "name": "行者头带"
    },
    "rec_xing_zhe_seng_pao": {
        "slot": "armor",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "行者图纸",
        "class": "cls_wu_seng",
        "set": "set_xing_zhe",
        "desc": "行者套装·Ⅰ阶核心部件",
        "name": "行者僧袍"
    },
    "rec_xing_zhe_hu_tui": {
        "slot": "legs",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "行者图纸",
        "class": "cls_wu_seng",
        "set": "set_xing_zhe",
        "desc": "行者套装·Ⅰ阶核心部件",
        "name": "行者护腿"
    },
    "rec_xing_zhe_bu_xue": {
        "slot": "boots",
        "quality": "blue",
        "lv": 10,
        "weapon_type": None,
        "mats": {
            "mat_lang_pi": 6,
            "mat_ye_zhu_pi": 5,
            "mat_shan_zei_hui_zhang": 3
        },
        "gold": 300,
        "blueprint": "行者图纸",
        "class": "cls_wu_seng",
        "set": "set_xing_zhe",
        "desc": "行者套装·Ⅰ阶核心部件",
        "name": "行者布靴"
    },
    "rec_tie_shou_quan_tao": {
        "slot": "weapon",
        "quality": "blue",
        "lv": 30,
        "weapon_type": "fist",
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "铁手图纸",
        "class": "cls_wu_seng",
        "set": "set_tie_shou",
        "desc": "铁手套装·Ⅱ阶核心部件",
        "name": "铁手拳套"
    },
    "rec_tie_shou_tou_dai": {
        "slot": "helm",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "铁手图纸",
        "class": "cls_wu_seng",
        "set": "set_tie_shou",
        "desc": "铁手套装·Ⅱ阶核心部件",
        "name": "铁手头带"
    },
    "rec_tie_shou_seng_pao": {
        "slot": "armor",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "铁手图纸",
        "class": "cls_wu_seng",
        "set": "set_tie_shou",
        "desc": "铁手套装·Ⅱ阶核心部件",
        "name": "铁手僧袍"
    },
    "rec_tie_shou_hu_tui": {
        "slot": "legs",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "铁手图纸",
        "class": "cls_wu_seng",
        "set": "set_tie_shou",
        "desc": "铁手套装·Ⅱ阶核心部件",
        "name": "铁手护腿"
    },
    "rec_tie_shou_bu_xue": {
        "slot": "boots",
        "quality": "blue",
        "lv": 30,
        "weapon_type": None,
        "mats": {
            "mat_shu_shi_he_xin": 4,
            "mat_shou_ren_liao_ya": 6,
            "mat_zuo_lang_quan_chi": 4
        },
        "gold": 1200,
        "blueprint": "铁手图纸",
        "class": "cls_wu_seng",
        "set": "set_tie_shou",
        "desc": "铁手套装·Ⅱ阶核心部件",
        "name": "铁手布靴"
    },
    "rec_hu_xiao_quan_tao": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 50,
        "weapon_type": "fist",
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "虎啸图纸",
        "class": "cls_wu_seng",
        "set": "set_hu_xiao",
        "desc": "虎啸套装·Ⅲ阶核心部件",
        "name": "虎啸拳套"
    },
    "rec_hu_xiao_tou_dai": {
        "slot": "helm",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "虎啸图纸",
        "class": "cls_wu_seng",
        "set": "set_hu_xiao",
        "desc": "虎啸套装·Ⅲ阶核心部件",
        "name": "虎啸头带"
    },
    "rec_hu_xiao_seng_pao": {
        "slot": "armor",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "虎啸图纸",
        "class": "cls_wu_seng",
        "set": "set_hu_xiao",
        "desc": "虎啸套装·Ⅲ阶核心部件",
        "name": "虎啸僧袍"
    },
    "rec_hu_xiao_hu_tui": {
        "slot": "legs",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "虎啸图纸",
        "class": "cls_wu_seng",
        "set": "set_hu_xiao",
        "desc": "虎啸套装·Ⅲ阶核心部件",
        "name": "虎啸护腿"
    },
    "rec_hu_xiao_bu_xue": {
        "slot": "boots",
        "quality": "purple",
        "lv": 50,
        "weapon_type": None,
        "mats": {
            "mat_sheng_guang_jie_jing": 5,
            "mat_yue_ying_zhi_pi": 5,
            "mat_long_yan_jing_hua": 3
        },
        "gold": 3000,
        "blueprint": "虎啸图纸",
        "class": "cls_wu_seng",
        "set": "set_hu_xiao",
        "desc": "虎啸套装·Ⅲ阶核心部件",
        "name": "虎啸布靴"
    },
    "rec_pan_shi_quan_tao": {
        "slot": "weapon",
        "quality": "purple",
        "lv": 70,
        "weapon_type": "fist",
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "磐石图纸",
        "class": "cls_wu_seng",
        "set": "set_pan_shi",
        "desc": "磐石套装·Ⅳ阶核心部件",
        "name": "磐石拳套"
    },
    "rec_pan_shi_tou_dai": {
        "slot": "helm",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "磐石图纸",
        "class": "cls_wu_seng",
        "set": "set_pan_shi",
        "desc": "磐石套装·Ⅳ阶核心部件",
        "name": "磐石头带"
    },
    "rec_pan_shi_seng_pao": {
        "slot": "armor",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "磐石图纸",
        "class": "cls_wu_seng",
        "set": "set_pan_shi",
        "desc": "磐石套装·Ⅳ阶核心部件",
        "name": "磐石僧袍"
    },
    "rec_pan_shi_hu_tui": {
        "slot": "legs",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "磐石图纸",
        "class": "cls_wu_seng",
        "set": "set_pan_shi",
        "desc": "磐石套装·Ⅳ阶核心部件",
        "name": "磐石护腿"
    },
    "rec_pan_shi_bu_xue": {
        "slot": "boots",
        "quality": "purple",
        "lv": 70,
        "weapon_type": None,
        "mats": {
            "mat_xu_kong_hu_jia": 5,
            "mat_lie_xi_ling_zhu_yin_ji": 4,
            "mat_long_yan_jing_hua": 4
        },
        "gold": 6500,
        "blueprint": "磐石图纸",
        "class": "cls_wu_seng",
        "set": "set_pan_shi",
        "desc": "磐石套装·Ⅳ阶核心部件",
        "name": "磐石布靴"
    },
    "rec_jin_shen_quan_tao": {
        "slot": "weapon",
        "quality": "orange",
        "lv": 90,
        "weapon_type": "fist",
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "金身图纸",
        "class": "cls_wu_seng",
        "set": "set_jin_shen",
        "desc": "金身套装·Ⅴ阶核心部件",
        "name": "金身拳套"
    },
    "rec_jin_shen_tou_dai": {
        "slot": "helm",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "金身图纸",
        "class": "cls_wu_seng",
        "set": "set_jin_shen",
        "desc": "金身套装·Ⅴ阶核心部件",
        "name": "金身头带"
    },
    "rec_jin_shen_seng_pao": {
        "slot": "armor",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "金身图纸",
        "class": "cls_wu_seng",
        "set": "set_jin_shen",
        "desc": "金身套装·Ⅴ阶核心部件",
        "name": "金身僧袍"
    },
    "rec_jin_shen_hu_tui": {
        "slot": "legs",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "金身图纸",
        "class": "cls_wu_seng",
        "set": "set_jin_shen",
        "desc": "金身套装·Ⅴ阶核心部件",
        "name": "金身护腿"
    },
    "rec_jin_shen_bu_xue": {
        "slot": "boots",
        "quality": "orange",
        "lv": 90,
        "weapon_type": None,
        "mats": {
            "mat_jiao_zong_quan_zhang": 5,
            "mat_si_ji_wang_guan": 4,
            "mat_tian_qiong_hu_jia": 4
        },
        "gold": 12000,
        "blueprint": "金身图纸",
        "class": "cls_wu_seng",
        "set": "set_jin_shen",
        "desc": "金身套装·Ⅴ阶核心部件",
        "name": "金身布靴"
    }
}

# 别名：配方名 → 别名列表（key 已转 rec ID，别名保留中文供输入匹配）
CRAFT_RECIPE_ALIASES = {
    "rec_tie_jian": [
        "铁剑",
        "新手剑"
    ],
    "rec_xue_tu_fa_zhang": [
        "学徒杖",
        "法杖"
    ],
    "rec_lie_gong": [
        "新手弓",
        "短弓"
    ],
    "rec_sheng_guang_quan_zhang": [
        "新手杖"
    ],
    "rec_lv_ren_xiong_jia": [
        "皮甲"
    ],
    "rec_lv_ren_hu_tui": [
        "皮裤"
    ],
    "rec_lv_ren_zhi_xue": [
        "皮靴"
    ],
    "rec_shan_zei_zhi_kui": [
        "山贼头盔"
    ],
    "rec_sheng_lu_zhi_dun": [
        "圣鹿甲"
    ],
    "rec_jing_gang_jian": [
        "钢剑"
    ],
    "rec_you_hun_fa_zhang": [
        "亡灵法杖"
    ],
    "rec_lie_mo_gong": [
        "魔弓"
    ],
    "rec_sheng_hai_quan_zhang": [
        "骸骨权杖"
    ],
    "rec_hei_shi_zhan_jia": [
        "锁甲"
    ],
    "rec_huang_yuan_hu_tui": [
        "兽人护腿"
    ],
    "rec_fu_xiu_zhi_ren": [
        "魔刃"
    ],
    "rec_qiu_zhang_zhan_ren": [
        "酋长剑"
    ],
    "rec_wu_yao_fa_zhang": [
        "传说法杖"
    ],
    "rec_han_shuang_zhi_jian": [
        "冰剑"
    ],
    "rec_lie_yan_fa_zhang": [
        "火杖"
    ],
    "rec_feng_bao_zhi_gong": [
        "雷弓"
    ],
    "rec_shen_yuan_quan_zhang": [
        "暗杖"
    ],
    "rec_rong_yan_zhan_jia": [
        "火甲"
    ],
    "rec_bing_shuang_zhi_dun": [
        "冰甲"
    ],
    "rec_lei_ting_zhi_chui": [
        "雷锤"
    ],
    "rec_hei_an_jun_zhu_zhi_ren": [
        "魔君之刃"
    ],
    "rec_sheng_hui_zhi_jian": [
        "圣剑"
    ],
    "rec_yue_ying_fa_zhang": [
        "月杖"
    ],
    "rec_long_yi_zhang_gong": [
        "龙弓"
    ],
    "rec_yue_shen_quan_zhang": [
        "月神杖"
    ],
    "rec_long_lin_zhan_jia": [
        "龙甲"
    ],
    "rec_yue_shen_zhi_guan": [
        "月冠"
    ],
    "rec_long_wang_zhi_jiao": [
        "龙角盔"
    ],
    "rec_lie_xi_zhi_ren": [
        "裂刃"
    ],
    "rec_shi_hun_fa_zhang": [
        "魂杖"
    ],
    "rec_shen_pan_zhi_gong": [
        "审判弓"
    ],
    "rec_jiao_zong_quan_zhang": [
        "教皇杖"
    ],
    "rec_tun_shi_zhe_zhi_he": [
        "吞噬核心"
    ],
    "rec_si_ji_wang_guan": [
        "死寂盔"
    ],
    "rec_xing_jie_zhi_jian": [
        "星剑"
    ],
    "rec_hun_dun_fa_zhu": [
        "混沌杖"
    ],
    "rec_tian_qiong_zhi_gong": [
        "天弓"
    ],
    "rec_shen_yu_quan_zhang": [
        "神杖"
    ],
    "rec_tian_qiong_zhi_guan": [
        "天穹盔"
    ],
    "rec_hun_dun_zhi_he": [
        "混沌核心"
    ]
}
