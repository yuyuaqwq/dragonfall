# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - alchemy.py(v48 key 转 ID；v54 加副业等级限制 + 配方丰富)"""
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
        # v110 审计修复：配方名与产物 i_great_treatment 对齐（v110.11 产物已改名
        # 「高效治疗药水」40% 档；商店另有 i_treat_strong「强效治疗药水」50% 档——
        # 原配方名沿用旧名造成"做出高效却显示强效"的误导）
        "name": "高效治疗药水"
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
    # v113.3 祝福符石：星铁与强化石淬炼的幸运向强化材料（成功率 +15%，可叠加精炼强化石）
    "al_zhu_fu_fu_shi": {
        "cost": {"mat_star_iron": 1, "i_stone_upgrade": 1},
        "product": {"i_stone_blessed": 1},
        "min_lv": 4,
        "desc": "星铁与强化石淬炼的祝福符石，强化成功率更高",
        "name": "祝福符石"
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
    # ---- v116 通用材料提纯（19 章 2.5『转的乐趣』：3 份同档低质材料 → 1 份高一档材料） ----
    # 提纯 = 消耗冗余绿/蓝材料的出口；产物价 ≤ 材料成本价×0.9（防刷金，与淬火石精炼同口径）。
    # 档位对齐 MATERIALS quality 五档：绿→蓝 / 蓝→紫，垂钓水产材料同族提炼。
    # 生态：『合成 <配方名>』照常可用，或『炼金 提纯』仅列出提纯配方。
    "al_purify_jing_xu_cao": {
        "cost": {
            "mat_jing_xu_cao": 3
        },
        "product": {
            "mat_zhen_zhu_bei": 1
        },
        "min_lv": 2,
        "purify": True,
        "desc": "鲸须草浓缩提纯为珍珠贝（绿→蓝），消耗冗余绿材料的出口",
        "name": "鲸须草提纯"
    },
    "al_purify_hai_zao": {
        "cost": {
            "mat_hai_zao": 3
        },
        "product": {
            "mat_shen_mi_lin_pian": 1
        },
        "min_lv": 2,
        "purify": True,
        "desc": "海藻浓缩提纯为神秘鳞片（绿→蓝），消耗冗余绿材料的出口",
        "name": "海藻提纯"
    },
    "al_purify_zhen_zhu_bei": {
        "cost": {
            "mat_zhen_zhu_bei": 3
        },
        "product": {
            "mat_lei_jing_sha": 1
        },
        "min_lv": 5,
        "purify": True,
        "desc": "珍珠贝浓缩提纯为雷晶砂（蓝→紫），消耗冗余蓝材料的出口",
        "name": "珍珠贝提纯"
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
        "desc": "战斗中使用，抵挡 3 次受击防御 + 45%",
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

    # ---- v117 副本材料·炼金配方（方案 C）----
    # 18 种完全闲置的副本材料（只能卖钱）接入炼金：补强强化石链 + 高阶/低阶药剂。
    # 防刷金铁律（与 v116 提纯同口径）：产物售价 ≤ 材料成本价合计 ×0.9；
    # min_lv 与主材料稀有度匹配（橙 6-8 / 紫 4-6 / 蓝 3-5 / 绿 1-3）。
    "al_jin_he_qiang_hua": {
        "cost": {"mat_jin_he": 4, "mat_shen_yuan_zhen_zhu": 5},
        "product": {"i_stone_upgrade": 1},
        "min_lv": 4,
        "desc": "烬核与深渊珍珠淬炼的强化石，强化装备失败不掉级（副本材料补链）",
        "name": "烬核强化石"
    },
    "al_long_gong_jing_lian": {
        "cost": {
            "mat_long_gong_zhu": 1,
            "mat_hei_yuan_zhi_yan": 1,
            "mat_long_yu_chuan_cheng": 1,
            "mat_yong_dong_zhi_he": 1,
            "mat_shen_yuan_zhen_zhu": 8,
        },
        "product": {"i_stone_refine": 1},
        "min_lv": 6,
        "desc": "龙宫珠与黑渊之眼等珍材精炼而成的高品质强化石，强化成功率更高",
        "name": "龙宫精炼强化石"
    },
    "al_feng_bao_lei_yao": {
        "cost": {"mat_feng_bao_zhi_he": 1},
        "product": {"i_thunder_elixir": 1},
        "min_lv": 6,
        "desc": "风暴之核淬炼的雷晶药剂，战斗中攻击力 + 40%(3 回合)",
        "name": "风暴雷晶药剂"
    },
    "al_yun_nu_bao_ji": {
        "cost": {"mat_yun_nu_zhi_he": 1, "mat_shen_yuan_zhen_zhu": 2},
        "product": {"i_crit_potion": 1},
        "min_lv": 6,
        "desc": "云怒之核调制，战斗中暴击率 + 20%(3 回合)",
        "name": "云怒暴击药水"
    },
    "al_long_lin_tie_bi": {
        "cost": {"mat_di_di_long_lin": 10, "mat_shen_yuan_zhen_zhu": 1},
        "product": {"i_def_potion": 1},
        "min_lv": 5,
        "desc": "地底龙鳞炼就的铁壁药剂，战斗中抵挡 3 次受击防御 + 45%",
        "name": "龙鳞铁壁药剂"
    },
    "al_ji_qi_shen_yuan": {
        "cost": {"mat_he_er_jia_de_ji_qi": 8, "mat_sheng_guang_sheng_hui": 1},
        "product": {"i_abyss_crystal_potion": 1},
        "min_lv": 5,
        "desc": "赫尔加祭器研磨入药，战斗中魔法伤害减免 15%(3 回合)",
        "name": "祭器深渊药剂"
    },
    "al_shi_lu_qiang_hua": {
        "cost": {
            "mat_shi_lu_zhi_chui": 4,
            "mat_yao_sai_can_pian": 3,
            "mat_hui_ai_ren_hui_ji": 2,
            "mat_you_ling_chuan_piao": 1,
        },
        "product": {"i_stone_upgrade": 1},
        "min_lv": 5,
        "desc": "石炉之锤与要塞残片捶打淬炼的强化石，强化失败不掉级",
        "name": "石炉强化石"
    },
    "al_shi_lian_ji_feng": {
        "cost": {"mat_shi_lian_hui_ji": 1, "mat_ke_luo_de_luo_pan": 1, "mat_ma_er_ku_si_de_fa_guan": 1},
        "product": {"i_spd_potion": 1},
        "min_lv": 4,
        "desc": "试炼徽记与古贤遗物调制的疾风药剂，战斗中速度 + 40%(3 回合)",
        "name": "试炼疾风药剂"
    },
    "al_lan_ge_ming_mu": {
        "cost": {"mat_lan_ge_zhi_guan": 1, "mat_shen_yuan_zhen_zhu": 1},
        "product": {"i_pearl_tonic": 1},
        "min_lv": 4,
        "desc": "蓝歌之冠磨粉调制的灵水，战斗中暴击率 + 15%(3 回合)",
        "name": "蓝歌明目水"
    },

    # ---- v117 副本材料·符文匣配方（方案 D：副本材料 → 符文，配合 item_templates.open_rune_chest）----
    "al_hei_yuan_fu_wen_xiang": {
        "cost": {"mat_hei_yuan_zhi_yan": 1, "mat_shen_yuan_zhen_zhu": 3},
        "product": {"i_hei_yuan_fu_wen_xiang": 1},
        "min_lv": 6,
        "desc": "黑渊之眼封存的符文匣，打开获得随机稀有符文",
        "name": "黑渊符文匣"
    },
    "al_long_gong_fu_wen_xiang": {
        "cost": {"mat_long_gong_zhu": 1, "mat_shen_yuan_zhen_zhu": 1},
        "product": {"i_long_gong_fu_wen_xiang": 1},
        "min_lv": 7,
        "desc": "龙宫珠封存的符文匣，打开获得随机稀有符文",
        "name": "龙宫符文匣"
    },
    # ================= v124 支线奖励：S49/H6 炼金配方（图纸学习制，blueprint=图纸名） =================
    # 月光安神剂：成本 80×2+40×1+120×1=320；产物价 60（卖店按 ≤0.9×成本注入封顶）
    "al_yue_guang_an_shen_ji": {
        "cost": {"mat_yue_guang_cao": 2, "mat_zhao_ze_hua": 1, "mat_yue_guang_lan_mi": 1},
        "product": {"i_yue_guang_an_shen_ji": 1},
        "min_lv": 3,
        "desc": "月光兰蜜调和的安神药水，回复 40% HP + 20% MP(S49 配方图纸)",
        "name": "月光安神剂",
        "blueprint": "配方·月光安神剂",
    },
    # 白石圣灰药剂：成本 150×2+8×1+5×1=313；产物价 100（卖店按 ≤0.9×成本注入封顶）
    "al_bai_shi_sheng_hui_yao_ji": {
        "cost": {"mat_white_ash": 2, "mat_cao_yao": 1, "mat_kong_ping": 1},
        "product": {"i_bai_shi_sheng_hui_yao_ji": 1},
        "min_lv": 4,
        "desc": "白石圣灰调成的圣光药剂——战斗中驱散全队负面(H6 唯一来源)",
        "name": "白石圣灰药剂",
        "blueprint": "隐藏配方·白石圣灰药剂",
    },
}

