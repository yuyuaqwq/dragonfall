# -*- coding: utf-8 -*-
"""《剑与魔法》数据层 - items.py（v48 全 key 转 ID）"""
ITEMS = {
    "i_treatment_potion": {
        "name": "治疗药水",
        "type": "消耗品",
        "desc": "恢复 200 点生命",
        "heal": 200,
        "price": 20
    },
    "i_mana_potion": {
        "name": "魔力药水",
        "type": "消耗品",
        "desc": "恢复 150 点魔力",
        "mana": 150,
        "price": 25
    },
    "i_great_treatment": {
        "name": "强效治疗药水",
        "type": "消耗品",
        "desc": "恢复 500 点生命",
        "heal": 500,
        "price": 60
    },
    "i_great_mana": {
        "name": "强效魔力药水",
        "type": "消耗品",
        "desc": "恢复 400 点魔力",
        "mana": 400,
        "price": 70
    },
    "i_scroll_escape": {
        "name": "回城卷轴",
        "type": "消耗品",
        "desc": "立即返回维拉镇",
        "price": 50,
        "effect": "return_vila"
    },
    "i_super_treatment": {
        "name": "超级治疗药水",
        "type": "消耗品",
        "desc": "恢复 1500 点生命",
        "heal": 1500,
        "price": 180
    },
    "i_super_mana": {
        "name": "超级魔力药水",
        "type": "消耗品",
        "desc": "恢复 1200 点魔力",
        "mana": 1200,
        "price": 200
    },
    # ---- 烹饪料理（副业产物，走『使用』指令）----
    "it_fish_soup": {
        "name": "鱼汤",
        "type": "消耗品",
        "desc": "鲜鱼慢炖的浓汤，恢复 120 点生命",
        "heal": 120,
        "price": 15
    },
    "it_herb_tea": {
        "name": "香草茶",
        "type": "消耗品",
        "desc": "香草泡的茶，恢复 80 点魔力",
        "mana": 80,
        "price": 10
    },
    "it_mushroom_stew": {
        "name": "蘑菇炖菜",
        "type": "消耗品",
        "desc": "林间蘑菇炖的杂烩，恢复 300 点生命",
        "heal": 300,
        "price": 30
    },
    "it_royal_salmon": {
        "name": "香煎帝王鲑",
        "type": "消耗品",
        "desc": "帝王鲑煎得金黄，恢复 600 点生命",
        "heal": 600,
        "price": 60
    },
    "it_berry_pie": {
        "name": "浆果派",
        "type": "消耗品",
        "desc": "甜香扑鼻，恢复 250 点生命和 150 点魔力",
        "heal": 250,
        "mana": 150,
        "price": 45
    },
    "it_elixir_soup": {
        "name": "秘制灵药汤",
        "type": "消耗品",
        "desc": "药效非凡，恢复 1000 点生命和 500 点魔力",
        "heal": 1000,
        "mana": 500,
        "price": 150
    },
    "it_dragon_banquet": {
        "name": "龙脊盛宴",
        "type": "消耗品",
        "desc": "传说级料理，恢复 2500 点生命和 1200 点魔力",
        "heal": 2500,
        "mana": 1200,
        "price": 400
    },
    "i_stone_upgrade": {
        "name": "强化石",
        "type": "材料",
        "desc": "炼金工坊合成的强化材料，蕴含着稳定的锻造之力",
        "price": 120
    },
    "i_stone_refine": {
        "name": "精炼强化石",
        "type": "材料",
        "desc": "更高品质的强化材料，蕴含炽热的锻造之力",
        "price": 300
    },
    "i_lucky_charm": {
        "name": "幸运护符",
        "type": "消耗品",
        "desc": "使用后 10 分钟内打怪金币 +50%、材料掉落 +1",
        "effect": "lucky",
        "price": 150
    },
    "i_atk_potion": {
        "name": "攻击药水",
        "type": "消耗品",
        "desc": "战斗中使用，攻击力 +30%（3 回合）",
        "effect": "buff_atk",
        "price": 80
    },
    "i_def_potion": {
        "name": "防御药水",
        "type": "消耗品",
        "desc": "战斗中使用，防御力 +45%（3 回合）",
        "effect": "buff_def",
        "price": 80
    },
    "i_spd_potion": {
        "name": "速度药水",
        "type": "消耗品",
        "desc": "战斗中使用，速度 +40%（3 回合）",
        "effect": "buff_spd",
        "price": 90
    },
    "i_crit_potion": {
        "name": "暴击药水",
        "type": "消耗品",
        "desc": "战斗中使用，暴击率 +20%（3 回合）",
        "effect": "buff_crit",
        "price": 100
    }
}

MATERIALS = {
    "mat_mu_xue_fen": {
        "price": 40,
        "name": "墓穴粉尘"
    },
    "mat_ye_gou_liao_ya": {
        "price": 3,
        "name": "野狗獠牙"
    },
    "mat_shu_wei": {
        "price": 4,
        "name": "鼠尾"
    },
    "mat_ye_zhu_pi": {
        "price": 6,
        "name": "野猪皮"
    },
    "mat_shan_zei_hui_zhang": {
        "price": 15,
        "name": "山贼徽章"
    },
    "mat_lang_pi": {
        "price": 8,
        "name": "狼皮"
    },
    "mat_zhi_zhu_du_nang": {
        "price": 9,
        "name": "蜘蛛毒囊"
    },
    "mat_yao_jing_zhi_chen": {
        "price": 14,
        "name": "妖精之尘"
    },
    "mat_yuan_gu_shu_pi": {
        "price": 20,
        "name": "远古树皮"
    },
    "mat_sheng_lu_jiao": {
        "price": 30,
        "name": "圣鹿角"
    },
    "mat_di_jing_er_duo": {
        "price": 10,
        "name": "地精耳朵"
    },
    "mat_bian_fu_yi": {
        "price": 11,
        "name": "蝙蝠翼"
    },
    "mat_she_lin": {
        "price": 13,
        "name": "蛇鳞"
    },
    "mat_sa_man_tu_teng": {
        "price": 22,
        "name": "萨满图腾"
    },
    "mat_jiang_shi_fu_rou": {
        "price": 12,
        "name": "僵尸腐肉"
    },
    "mat_gui_hun_jing_hua": {
        "price": 18,
        "name": "鬼魂精华"
    },
    "mat_pa_xing_chong_ke": {
        "price": 15,
        "name": "爬行虫壳"
    },
    "mat_shu_shi_he_xin": {
        "price": 28,
        "name": "术士核心"
    },
    "mat_shou_ren_liao_ya": {
        "price": 16,
        "name": "兽人獠牙"
    },
    "mat_zuo_lang_quan_chi": {
        "price": 18,
        "name": "座狼犬齿"
    },
    "mat_nv_yao_zhi_yu": {
        "price": 24,
        "name": "女妖之羽"
    },
    "mat_kuang_zhan_zhi_xin": {
        "price": 35,
        "name": "狂战之心"
    },
    "mat_gu_pian": {
        "price": 17,
        "name": "骨片"
    },
    "mat_shi_shi_gui_zhi_zhao": {
        "price": 19,
        "name": "食尸鬼之爪"
    },
    "mat_ling_hun_sui_pian": {
        "price": 26,
        "name": "灵魂碎片"
    },
    "mat_huo_yan_he_xin": {
        "price": 28,
        "name": "火焰核心"
    },
    "mat_e_mo_zhi_jiao": {
        "price": 30,
        "name": "恶魔之角"
    },
    "mat_rong_yan_shi": {
        "price": 32,
        "name": "熔岩石"
    },
    "mat_ju_ren_yu_jin": {
        "price": 45,
        "name": "巨人余烬"
    },
    "mat_bing_yuan_mao_pi": {
        "price": 30,
        "name": "冰原毛皮"
    },
    "mat_ju_mo_xue_rou": {
        "price": 33,
        "name": "巨魔血肉"
    },
    "mat_xue_zhi_jing_hua": {
        "price": 36,
        "name": "雪之精华"
    },
    "mat_yong_heng_zhi_bing": {
        "price": 50,
        "name": "永恒之冰"
    },
    "mat_lei_dian_he_xin": {
        "price": 38,
        "name": "雷电核心"
    },
    "mat_ju_ying_ling_yu": {
        "price": 40,
        "name": "巨鹰翎羽"
    },
    "mat_feng_bao_she_lin": {
        "price": 42,
        "name": "风暴蛇鳞"
    },
    "mat_an_ying_sui_pian": {
        "price": 45,
        "name": "暗影碎片"
    },
    "mat_zai_e_zhi_xin": {
        "price": 48,
        "name": "灾厄之心"
    },
    "mat_xu_kong_sui_pian": {
        "price": 52,
        "name": "虚空碎片"
    },
    "mat_shen_yuan_jing_gang": {
        "price": 55,
        "name": "深渊精钢"
    },
    "mat_xu_kong_liao_ya": {
        "price": 50,
        "name": "虚空獠牙"
    },
    "mat_xian_qu_hao_jiao": {
        "price": 55,
        "name": "先驱号角"
    },
    "mat_mi_yin_kuang_shi": {
        "price": 60,
        "name": "秘银矿石"
    },
    "mat_fu_wen_sui_pian": {
        "price": 55,
        "name": "符文碎片"
    },
    "mat_bao_cang_yao_shi": {
        "price": 65,
        "name": "宝藏钥匙"
    },
    "mat_chuan_shuo_jing_hua": {
        "price": 200,
        "name": "传说精华"
    },
    "mat_sheng_guang_yu_mao": {
        "price": 80,
        "name": "圣光羽毛"
    },
    "mat_guang_yao_zhi_pi": {
        "price": 85,
        "name": "光耀之皮"
    },
    "mat_sheng_hui_lu_jiao": {
        "price": 90,
        "name": "圣辉鹿角"
    },
    "mat_sheng_guang_hui_zhang": {
        "price": 95,
        "name": "圣光徽章"
    },
    "mat_sheng_guang_jie_jing": {
        "price": 100,
        "name": "圣光结晶"
    },
    "mat_sheng_qi_shi_jian": {
        "price": 110,
        "name": "圣骑士剑"
    },
    "mat_sheng_guang_dun_pai": {
        "price": 105,
        "name": "圣光盾牌"
    },
    "mat_tian_shi_zhi_yu": {
        "price": 130,
        "name": "天使之羽"
    },
    "mat_tian_shi_sheng_yin": {
        "price": 150,
        "name": "天使圣印"
    },
    "mat_jing_ling_jian_shi": {
        "price": 100,
        "name": "精灵箭矢"
    },
    "mat_yue_ying_zhi_pi": {
        "price": 105,
        "name": "月影之皮"
    },
    "mat_sen_lin_zhi_ling": {
        "price": 110,
        "name": "森林之灵"
    },
    "mat_yue_zhi_ren": {
        "price": 120,
        "name": "月之刃"
    },
    "mat_jing_ling_fa_zhu": {
        "price": 115,
        "name": "精灵法珠"
    },
    "mat_cui_yu": {
        "price": 110,
        "name": "翠羽"
    },
    "mat_wang_ting_hui_zhang": {
        "price": 125,
        "name": "王庭徽章"
    },
    "mat_yue_zhi_lei": {
        "price": 160,
        "name": "月之泪"
    },
    "mat_yue_shen_zhi_guan": {
        "price": 200,
        "name": "月神之冠"
    },
    "mat_long_lin": {
        "price": 130,
        "name": "龙鳞"
    },
    "mat_fei_long_yi": {
        "price": 135,
        "name": "飞龙翼"
    },
    "mat_long_yi_hui_ji": {
        "price": 140,
        "name": "龙裔徽记"
    },
    "mat_long_mai_zhan_ren": {
        "price": 155,
        "name": "龙脉战刃"
    },
    "mat_long_yan_jing_hua": {
        "price": 150,
        "name": "龙炎精华"
    },
    "mat_long_mai_hu_fu": {
        "price": 165,
        "name": "龙脉护符"
    },
    "mat_fei_long_lin": {
        "price": 145,
        "name": "飞龙鳞"
    },
    "mat_long_yi_jian": {
        "price": 180,
        "name": "龙翼剑"
    },
    "mat_long_wang_zhi_jiao": {
        "price": 250,
        "name": "龙王之角"
    },
    "mat_xu_kong_zhan_ye": {
        "price": 160,
        "name": "虚空粘液"
    },
    "mat_lie_xi_sui_pian": {
        "price": 165,
        "name": "裂隙碎片"
    },
    "mat_xu_kong_zhi_zhao": {
        "price": 170,
        "name": "虚空之爪"
    },
    "mat_si_lie_zhe_he_xin": {
        "price": 200,
        "name": "撕裂者核心"
    },
    "mat_xu_kong_hu_jia": {
        "price": 185,
        "name": "虚空护甲"
    },
    "mat_lie_xi_ling_zhu_yin_ji": {
        "price": 220,
        "name": "裂隙领主印记"
    },
    "mat_lie_xi_ju_xiang_he_xin": {
        "price": 230,
        "name": "裂隙巨像核心"
    },
    "mat_lie_xi_zhu_zai_quan_zhang": {
        "price": 260,
        "name": "裂隙主宰权杖"
    },
    "mat_tun_shi_zhe_zhi_he": {
        "price": 300,
        "name": "吞噬者之核"
    },
    "mat_hei_an_jing_juan": {
        "price": 190,
        "name": "黑暗经卷"
    },
    "mat_shen_yuan_zhi_chen": {
        "price": 195,
        "name": "深渊之尘"
    },
    "mat_duo_luo_sheng_hui": {
        "price": 200,
        "name": "堕落圣徽"
    },
    "mat_shen_pan_guan_zhi_yin": {
        "price": 240,
        "name": "审判官之印"
    },
    "mat_chan_hui_zhi_lei": {
        "price": 210,
        "name": "忏悔之泪"
    },
    "mat_shen_yuan_fa_zhu": {
        "price": 225,
        "name": "深渊法珠"
    },
    "mat_chu_xing_zhe_zhi_fu": {
        "price": 260,
        "name": "处刑者之斧"
    },
    "mat_ji_si_zhi_huo": {
        "price": 245,
        "name": "祭祀之火"
    },
    "mat_da_ji_si_zhi_huan": {
        "price": 290,
        "name": "大祭司之环"
    },
    "mat_jiao_zong_quan_zhang": {
        "price": 350,
        "name": "教宗权杖"
    },
    "mat_yan_mie_sui_pian": {
        "price": 240,
        "name": "湮灭碎片"
    },
    "mat_zai_e_zhan_jia": {
        "price": 255,
        "name": "灾厄战甲"
    },
    "mat_shi_hun_jie_jing": {
        "price": 260,
        "name": "噬魂结晶"
    },
    "mat_xian_feng_zhan_qi": {
        "price": 300,
        "name": "先锋战旗"
    },
    "mat_mo_jiang_zhi_ren": {
        "price": 290,
        "name": "魔将之刃"
    },
    "mat_ku_gu_ling_zhu_zhi_huan": {
        "price": 330,
        "name": "枯骨领主之环"
    },
    "mat_jin_wei_kai_jia": {
        "price": 310,
        "name": "禁卫铠甲"
    },
    "mat_si_ji_zhi_ren": {
        "price": 360,
        "name": "死寂之刃"
    },
    "mat_si_ji_wang_guan": {
        "price": 420,
        "name": "死寂王冠"
    },
    "mat_tian_qiong_hu_jia": {
        "price": 340,
        "name": "天穹护甲"
    },
    "mat_xing_jie_zhi_chen": {
        "price": 350,
        "name": "星界之尘"
    },
    "mat_shen_yu_zhan_hun": {
        "price": 360,
        "name": "神域战魂"
    },
    "mat_xing_jie_qi_shi_jian": {
        "price": 420,
        "name": "星界骑士剑"
    },
    "mat_xing_jie_fa_zhu": {
        "price": 400,
        "name": "星界法珠"
    },
    "mat_xing_jie_cai_jue_zhi_zhang": {
        "price": 460,
        "name": "星界裁决之杖"
    },
    "mat_men_fei_zhi_yao": {
        "price": 450,
        "name": "门扉之钥"
    },
    "mat_tian_qiong_zhi_guan": {
        "price": 520,
        "name": "天穹之冠"
    },
    "mat_shen_yu_jing_hua": {
        "price": 450,
        "name": "神域精华"
    },
    "mat_hun_dun_zhi_zha": {
        "price": 460,
        "name": "混沌之渣"
    },
    "mat_zhu_shen_yi_hui": {
        "price": 480,
        "name": "诸神遗辉"
    },
    "mat_shi_zhe_zhi_jie": {
        "price": 550,
        "name": "使者之戒"
    },
    "mat_chuang_shi_zhi_dun": {
        "price": 520,
        "name": "创世之盾"
    },
    "mat_hun_dun_zhi_he": {
        "price": 800,
        "name": "混沌之核"
    },
    "mat_hun_dun_sui_pian": {
        "price": 500,
        "name": "混沌碎片"
    },
    "mat_chao_yue_zhi_he": {
        "price": 2000,
        "name": "超越之核"
    },
    "mat_di_jing_wang_guan": {
        "price": 120,
        "name": "地精王冠"
    },
    "mat_fu_xiu_zhi_ren": {
        "price": 150,
        "name": "腐朽之刃"
    },
    "mat_qiu_zhang_zhan_ren": {
        "price": 200,
        "name": "酋长战刃"
    },
    "mat_si_wang_qi_shi_zhi_ren": {
        "price": 220,
        "name": "死亡骑士之刃"
    },
    "mat_wu_yao_fa_zhang": {
        "price": 260,
        "name": "巫妖法杖"
    },
    "mat_rong_yan_zhi_jian": {
        "price": 280,
        "name": "熔岩之剑"
    },
    "mat_shuang_long_zhi_ya": {
        "price": 300,
        "name": "霜龙之牙"
    },
    "mat_cang_qiong_zhi_ren": {
        "price": 260,
        "name": "苍穹之刃"
    },
    "mat_lei_ting_zhi_chui": {
        "price": 320,
        "name": "雷霆之锤"
    },
    "mat_shen_yuan_hui_ji": {
        "price": 300,
        "name": "深渊徽记"
    },
    "mat_an_ying_zhi_guan": {
        "price": 350,
        "name": "暗影之冠"
    },
    "mat_hei_an_jun_zhu_zhi_ren": {
        "price": 500,
        "name": "黑暗君主之刃"
    },
    "mat_ai_ren_wang_zhi_jie": {
        "price": 400,
        "name": "矮人王之戒"
    },
    "mat_mi_yin_wang_guan": {
        "price": 450,
        "name": "秘银王冠"
    },
    # ---- 植物采集材料（烹饪副业用，采集产出）----
    "mat_xiang_cao": {
        "price": 6,
        "name": "香草"
    },
    "mat_mo_gu": {
        "price": 9,
        "name": "蘑菇"
    },
    "mat_jiang_guo": {
        "price": 12,
        "name": "浆果"
    },
    "mat_feng_mi": {
        "price": 16,
        "name": "蜂蜜"
    },
    "mat_xiang_liao": {
        "price": 14,
        "name": "香料"
    },
    "mat_ling_zhi": {
        "price": 28,
        "name": "灵芝"
    }
}
