# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - alchemy.py（v48 key 转 ID；v54 加副业等级限制 + 配方丰富）"""
ALCHEMY_RECIPES = {
    "al_zhi_liao_yao_shui": {
        "cost": {
            "mat_lang_pi": 2,
            "mat_yao_jing_zhi_chen": 1
        },
        "product": {
            "i_treatment_potion": 1
        },
        "need_prof_lv": 1,
        "desc": "用兽皮与妖精之尘炼制的恢复药水",
        "name": "治疗药水"
    },
    "al_mo_li_yao_shui": {
        "cost": {
            "mat_yao_jing_zhi_chen": 2,
            "mat_zhi_zhu_du_nang": 1
        },
        "product": {
            "i_mana_potion": 1
        },
        "need_prof_lv": 1,
        "desc": "恢复魔力",
        "name": "魔力药水"
    },
    "al_qiang_hua_shi": {
        "cost": {
            "mat_rong_yan_shi": 2,
            "mat_shen_yuan_jing_gang": 1
        },
        "product": {
            "i_stone_upgrade": 1
        },
        "need_prof_lv": 2,
        "desc": "强化装备的必备材料",
        "name": "强化石"
    },
    "al_hui_cheng_juan_zhou": {
        "cost": {
            "mat_gui_hun_jing_hua": 1,
            "mat_yao_jing_zhi_chen": 1
        },
        "product": {
            "i_scroll_escape": 1
        },
        "need_prof_lv": 2,
        "desc": "瞬间回到橡木镇",
        "name": "回城卷轴"
    },
    "al_qiang_xiao_zhi_liao": {
        "cost": {
            "mat_sheng_guang_yu_mao": 1,
            "mat_yao_jing_zhi_chen": 2
        },
        "product": {
            "i_great_treatment": 1
        },
        "need_prof_lv": 3,
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
        "need_prof_lv": 3,
        "desc": "用雪之精华炼制的强效魔力药水",
        "name": "强效魔力药水"
    },
    "al_xing_yun_hu_fu": {
        "cost": {
            "mat_shou_ren_liao_ya": 2,
            "mat_an_ying_sui_pian": 1
        },
        "product": {
            "i_lucky_charm": 1
        },
        "need_prof_lv": 3,
        "desc": "提升打怪金币与材料掉落（10 分钟）",
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
        "need_prof_lv": 4,
        "desc": "高品质强化材料，强化成功率更高",
        "name": "精炼强化石"
    },
    "al_gong_ji_yao_shui": {
        "cost": {
            "mat_shou_ren_liao_ya": 2,
            "mat_huo_yan_he_xin": 1
        },
        "product": {
            "i_atk_potion": 1
        },
        "need_prof_lv": 4,
        "desc": "战斗中使用，攻击力 +30%（3 回合）",
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
        "need_prof_lv": 4,
        "desc": "战斗中使用，防御力 +45%（3 回合）",
        "name": "防御药水"
    },
    "al_chao_ji_zhi_liao_yao_shui": {
        "cost": {
            "mat_sheng_guang_yu_mao": 2,
            "mat_huo_yan_he_xin": 1
        },
        "product": {
            "i_super_treatment": 1
        },
        "need_prof_lv": 5,
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
        "need_prof_lv": 5,
        "desc": "高级魔力恢复",
        "name": "超级魔力药水"
    },
    "al_su_du_yao_shui": {
        "cost": {
            "mat_yao_jing_zhi_chen": 2,
            "mat_lang_pi": 2
        },
        "product": {
            "i_spd_potion": 1
        },
        "need_prof_lv": 5,
        "desc": "战斗中使用，速度 +40%（3 回合）",
        "name": "速度药水"
    },
    "al_bao_ji_yao_shui": {
        "cost": {
            "mat_an_ying_sui_pian": 2,
            "mat_shou_ren_liao_ya": 1
        },
        "product": {
            "i_crit_potion": 1
        },
        "need_prof_lv": 6,
        "desc": "战斗中使用，暴击率 +20%（3 回合）",
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
        "need_prof_lv": 3,
        "desc": "战斗中使用，本回合魔攻 +30%",
        "name": "鲛人之泪"
    },
    "al_long_xian_yao_ji": {
        "cost": {
            "mat_long_xian_xiang": 1
        },
        "product": {
            "i_ambergris_draught": 1
        },
        "need_prof_lv": 5,
        "desc": "战斗中使用，本回合攻击 +30%、防御 +20%",
        "name": "龙涎药剂"
    },
}
