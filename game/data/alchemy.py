# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - alchemy.py(v48 key 转 ID；v54 加副业等级限制 + 配方丰富)"""
ALCHEMY_RECIPES = {
    "al_zhi_liao_yao_shui": {
        "cost": {
            "mat_lang_pi": 1
        },
        "product": {
            "i_treatment_potion": 1
        },
        "min_lv": 1,
        "desc": "用兽皮与妖精之尘炼制的恢复药水",
        "name": "治疗药水"
    },
    "al_mo_li_yao_shui": {
        "cost": {
            "mat_shi_xi_lin": 1
        },
        "product": {
            "i_mana_potion": 1
        },
        "min_lv": 1,
        "desc": "恢复魔力",
        # v105R3 M16 P3-5：配方名与产物名统一（产物 i_mana_potion 为『魔法药水』）
        "name": "魔法药水"
    },
    "al_qiang_hua_shi": {
        "cost": {
            "mat_rong_yan_shi": 2,
            "mat_shen_yuan_jing_gang": 1
        },
        "product": {
            "i_stone_upgrade": 1
        },
        "min_lv": 2,
        "desc": "强化装备的必备材料",
        "name": "强化石"
    },
    "al_hui_cheng_juan_zhou": {
        "cost": {
            "mat_gui_hun_jing_hua": 3,
            "mat_yao_jing_zhi_chen": 1
        },
        "product": {
            "i_scroll_escape": 1
        },
        "min_lv": 2,
        # v105R3 M16 P2-9：实际回最近城镇（item_templates.tpl_return_vila nearest_town），
        # 新世界地图下不再写死橡木镇
        "desc": "瞬间回到最近城镇",
        "name": "回城卷轴"
    },
    "al_qiang_xiao_zhi_liao": {
        "cost": {
            "mat_sui_gu": 1,
            "mat_lang_pi": 1
        },
        "product": {
            "i_great_treatment": 1
        },
        "min_lv": 3,
        "desc": "用圣光羽毛炼制的强效恢复药水",
        "name": "强效治疗药水"
    },
    "al_qiang_xiao_mo_li": {
        "cost": {
            "mat_xue_zhi_jing_hua": 1,
            "mat_yao_jing_zhi_chen": 2
        },
        "product": {
            "i_great_mana": 1
        },
        "min_lv": 3,
        "desc": "用雪之精华炼制的强效魔力药水",
        # v105R3 M16 P3-5：配方名与产物名统一（产物 i_great_mana 为『强效魔法药水』）
        "name": "强效魔法药水"
    },
    "al_xing_yun_hu_fu": {
        # v105R3 M16 P2-1：成本 275/300=0.92 超 90% 上限 → 獠牙×1+暗影碎片×2=250/300=0.83
        "cost": {
            "mat_shou_ren_liao_ya": 1,
            "mat_an_ying_sui_pian": 2
        },
        "product": {
            "i_lucky_charm": 1
        },
        "min_lv": 3,
        "desc": "提升打怪金币与材料掉落(10 分钟)",
        "name": "幸运护符"
    },
    "al_jing_lian_qiang_hua_shi": {
        "cost": {
            "i_stone_upgrade": 2,
            "mat_huo_yan_he_xin": 1
        },
        "product": {
            "i_stone_refine": 1
        },
        "min_lv": 4,
        "desc": "高品质强化材料，强化成功率更高",
        "name": "精炼强化石"
    },
    # M10 P1-1 高级强化石断链修复：淬火石（挖掘产出）精炼 → 高级强化石（星尘法杖锻造核心材料），
    # 对齐物品 desc"淬火石精炼而成的高纯度矿石"；成本45金 ≤ 产物价80金，炼金转化合理
    "al_gao_ji_qiang_hua_shi": {
        "cost": {
            "mat_qiang_hua_shi": 3
        },
        "product": {
            "mat_gao_ji_qiang_hua_shi": 1
        },
        "min_lv": 4,
        "desc": "淬火石精炼而成的高纯度矿石，高级锻造的基石",
        "name": "高级强化石"
    },
    "al_gong_ji_yao_shui": {
        "cost": {
            "mat_shou_ren_liao_ya": 1,
            "mat_zhi_zhu_du_nang": 1
        },
        "product": {
            "i_atk_potion": 1
        },
        "min_lv": 4,
        "desc": "战斗中使用，攻击力 + 30%(3 回合)",
        "name": "攻击药水"
    },
    "al_fang_yu_yao_shui": {
        "cost": {
            "mat_zuo_lang_quan_chi": 2,
            "mat_rong_yan_shi": 1
        },
        "product": {
            "i_def_potion": 1
        },
        "min_lv": 4,
        "desc": "战斗中使用，防御力 + 45%(3 回合)",
        # v105R3 M16 P3-5：配方名与产物名统一（产物 i_def_potion 为『铁壁药剂』）
        "name": "铁壁药剂"
    },
    "al_chao_ji_zhi_liao_yao_shui": {
        "cost": {
            "mat_sheng_guang_yu_mao": 2,
            "mat_huo_yan_he_xin": 1
        },
        "product": {
            "i_super_treatment": 1
        },
        "min_lv": 5,
        "desc": "高级恢复药水",
        "name": "超级治疗药水"
    },
    "al_chao_ji_mo_li_yao_shui": {
        "cost": {
            "mat_xue_zhi_jing_hua": 2,
            "mat_ling_hun_sui_pian": 1
        },
        "product": {
            "i_super_mana": 1
        },
        "min_lv": 5,
        "desc": "高级魔力恢复",
        # v105R3 M16 P3-5：配方名与产物名统一（产物 i_super_mana 为『超级魔法药水』）
        "name": "超级魔法药水"
    },
    "al_su_du_yao_shui": {
        # v105R3 M16 P2-1：成本 100/100=1.00 零利润超 90% 上限 → 妖精之尘×1+狼皮×2=55/100=0.55
        "cost": {
            "mat_yao_jing_zhi_chen": 1,
            "mat_lang_pi": 2
        },
        "product": {
            "i_spd_potion": 1
        },
        "min_lv": 5,
        "desc": "战斗中使用，速度 + 40%(3 回合)",
        # v105R3 M16 P3-5：配方名与产物名统一（产物 i_spd_potion 为『疾风药剂』）
        "name": "疾风药剂"
    },
    "al_bao_ji_yao_shui": {
        # v105R3 M16 P2-1：成本 250/250=1.00 零利润超 90% 上限 → 暗影碎片×1+兽人獠牙×1=175/250=0.70
        "cost": {
            "mat_an_ying_sui_pian": 1,
            "mat_shou_ren_liao_ya": 1
        },
        "product": {
            "i_crit_potion": 1
        },
        "min_lv": 6,
        "desc": "战斗中使用，暴击率 + 20%(3 回合)",
        "name": "暴击药水"
    },
    # ---- 垂钓产业链（16 章 2.5：鲛人泪/龙涎香仅垂钓产出）----
    "al_jiao_ren_zhi_lei": {
        "cost": {
            "mat_jiao_ren_lei": 1
        },
        "product": {
            "i_mermaid_tear": 1
        },
        "min_lv": 3,
        # v105R3 M16 P2-7：实际 3 回合 buff（battle.py max(...,3)），desc 不再写「本回合」
        "desc": "战斗中使用，3 回合魔攻 + 30%",
        "name": "鲛人之泪"
    },
    "al_long_xian_yao_ji": {
        "cost": {
            "mat_long_xian_xiang": 1
        },
        "product": {
            "i_ambergris_draught": 1
        },
        "min_lv": 5,
        "desc": "战斗中使用，3 回合攻击 + 30%、防御 + 45%",
        "name": "龙涎药剂"
    },

    # ---- v102.3 生活技能差异化：稀有药水（限定材料链：采集/深矿→炼金） ----
    "al_yue_lu_jing_hua": {
        "cost": {"mat_moon_dew": 2, "mat_kong_ping": 1},
        "product": {"i_moon_dew_essence": 1},
        "min_lv": 4,
        "desc": "月露凝炼的精华，战斗中喝下后下一次攻击伤害大幅提升",
        "name": "月露精华"
    },
    "al_shen_yuan_yao_ji": {
        "cost": {"mat_deep_crystal": 1, "mat_kong_ping": 1},
        "product": {"i_abyss_crystal_potion": 1},
        "min_lv": 5,
        "desc": "深渊水晶研磨入药，战斗中喝下获得魔法抗性（3 回合魔法伤害减免 15%）",
        "name": "深渊药剂"
    },
    "al_xing_tie_qiang_hua_ji": {
        "cost": {"mat_star_iron": 1, "i_stone_upgrade": 1},
        "product": {"i_star_iron_agent": 1},
        "min_lv": 6,
        "desc": "星铁淬炼的强化剂，下一次强化装备必定成功",
        "name": "星铁强化剂"
    },

    # ---- v101.30 阶段四：高级钓点材料消费点（垂钓独占材料 → 炼金，材料成本×2~2.5 = 售价，复用已有 effect 键） ----
    "al_zhen_zhu_ming_mu": {
        "cost": {"mat_hu_zhen_zhu": 1, "mat_kong_ping": 1},
        "product": {"i_pearl_tonic": 1},
        "min_lv": 3,
        "desc": "湖珍珠磨粉调制的灵水，战斗中暴击率 + 15%(3 回合)",
        "name": "珍珠明目水"
    },
    "al_shen_yuan_hui_xiang": {
        "cost": {"mat_shen_yuan_zhen_zhu": 1, "mat_kong_ping": 1},
        "product": {"i_abyss_echo": 1},
        "min_lv": 5,
        "desc": "深渊珍珠研磨的暗色药水，战斗中魔攻 + 30%(3 回合)",
        "name": "深渊回响药剂"
    },
    "al_cai_hong_yao_ji": {
        "cost": {"mat_cai_hong_lu_zhu": 1, "mat_kong_ping": 1},
        "product": {"i_rainbow_elixir": 1},
        "min_lv": 6,
        "desc": "彩虹露珠调制的梦幻药剂，下一次攻击伤害 + 50%",
        "name": "彩虹药剂"
    },
    "al_lei_jing_yao_ji": {
        "cost": {"mat_lei_jing_sha": 1, "mat_kong_ping": 1},
        "product": {"i_thunder_elixir": 1},
        "min_lv": 6,
        "desc": "雷晶砂淬炼的药剂，战斗中攻击力 + 40%(3 回合)",
        "name": "雷晶药剂"
    },
    "al_long_gu_yao_ji": {
        "cost": {"mat_gu_dai_yu_gu": 1, "mat_kong_ping": 1},
        "product": {"i_dragonbone_elixir": 1},
        "min_lv": 7,
        "desc": "上古鱼骨熬成的猛药，战斗中攻击 + 40%、防御 + 45%(3 回合)",
        "name": "龙骨药剂"
    },

    # ---- v104 M15 鱼饵配方落地（v102.3 规划：炼金 月光草+空瓶→萤光鱼饵）----
    "al_ying_guang_yu_er": {
        "cost": {"mat_yue_guang_cao": 1, "mat_kong_ping": 1},
        "product": {"it_glow_bait": 1},
        "min_lv": 3,
        "desc": "月光草调制的荧光饵料，幽光引鱼——下次垂钓紫/橙档概率大幅提升(仅 1 次)",
        "name": "萤光鱼饵"
    },
}

