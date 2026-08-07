# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - equip_roster.py（阶段八装备重写，2026-08-06）

10 章装备名册落地（9 系列 × 区域主题）+ 20 章属性需求/传说专属。
- 每件装备：名称/部位/武器类型/品质/等级/系列/属性需求/专属效果/来源
- 固定词条见 affixes.py SERIES_FIXED_AFFIX（按名称索引）
- 品质倍率见 equipment.py QUALITY（白1.0/绿1.3/蓝1.6/紫1.8/橙2.0）
- 来源：商店/锻造/图纸/boss（Boss 图纸）/legend（传说：世界掉落/主线/隐藏支线/声望）

⚠️ 命名调整（与策划案差异，2026-08-06 落地说明）：
- 10 章 4.7 海神系列「珍珠项链」与 4.2 铁港系列重名 → 海神系列改名「海神项链」（与系列命名一致）
- 武器类型新增 spear（苍穹之枪）、shield（橡木盾），同步 equipment.py WEAPON_TYPES/FLAVOR/WT_CN
"""

EQUIP_ROSTER = {
    # ================= 南境·橡木系列（Lv.1-10，新手） =================
    "eq_tie_jian":        {"name": "铁剑", "slot": "weapon", "weapon_type": "sword", "quality": "white", "lv": 2,  "series": "橡木", "req": {"str": 5}, "source": "商店"},
    "eq_lie_gong":        {"name": "猎弓", "slot": "weapon", "weapon_type": "bow", "quality": "white", "lv": 2,  "series": "橡木", "req": {"agi": 5}, "source": "商店"},
    "eq_xue_tu_fa_zhang": {"name": "学徒法杖", "slot": "weapon", "weapon_type": "staff", "quality": "white", "lv": 2, "series": "橡木", "req": {"int": 5}, "source": "商店"},
    "eq_xiang_mu_duan_gun": {"name": "橡木短棍", "slot": "weapon", "weapon_type": "mace", "quality": "white", "lv": 2, "series": "橡木", "req": {"str": 3}, "source": "商店"},
    "eq_pi_jia":          {"name": "皮甲", "slot": "armor", "quality": "white", "lv": 3, "series": "橡木", "req": {"vit": 3}, "source": "商店"},
    "eq_jiu_pi_xue":      {"name": "旧皮靴", "slot": "boots", "quality": "white", "lv": 3, "series": "橡木", "req": {"agi": 3}, "source": "商店"},
    "eq_xiang_mu_dun":    {"name": "橡木盾", "slot": "weapon", "weapon_type": "shield", "quality": "blue", "lv": 6, "series": "橡木", "req": {"str": 8}, "source": "锻造"},
    "eq_lie_lu_gong":     {"name": "猎鹿弓", "slot": "weapon", "weapon_type": "bow", "quality": "blue", "lv": 6, "series": "橡木", "req": {"agi": 8}, "source": "锻造"},
    "eq_xue_tu_zhi_zhang": {"name": "学徒之杖", "slot": "weapon", "weapon_type": "staff", "quality": "blue", "lv": 6, "series": "橡木", "req": {"int": 8}, "source": "锻造"},
    "eq_bai_lu_pi_jia":   {"name": "白鹿皮甲", "slot": "armor", "quality": "blue", "lv": 8, "series": "橡木", "req": {"agi": 8}, "source": "锻造"},
    "eq_xiang_mu_hu_tui": {"name": "橡木护腿", "slot": "legs", "quality": "white", "lv": 3, "series": "橡木", "req": {"vit": 3}, "source": "商店"},
    # ================= 南境·铁港系列（Lv.12-28，海盗/水手风） =================
    "eq_wan_dao":         {"name": "弯刀", "slot": "weapon", "weapon_type": "sword", "quality": "blue", "lv": 14, "series": "铁港", "req": {"agi": 12}, "source": "锻造"},
    "eq_shui_shou_duan_ren": {"name": "水手短刃", "slot": "weapon", "weapon_type": "dagger", "quality": "blue", "lv": 12, "series": "铁港", "req": {"agi": 10}, "source": "锻造"},
    "eq_hai_feng_chang_gong": {"name": "海风长弓", "slot": "weapon", "weapon_type": "bow", "quality": "purple", "lv": 18, "series": "铁港", "req": {"agi": 20}, "source": "图纸"},
    "eq_chuan_zhang_mao": {"name": "船长帽", "slot": "helm", "quality": "blue", "lv": 14, "series": "铁港", "req": {"agi": 12}, "source": "锻造"},
    "eq_shui_shou_jia_ke": {"name": "水手夹克", "slot": "armor", "quality": "blue", "lv": 15, "series": "铁港", "req": {"agi": 15}, "source": "锻造"},
    "eq_hai_dao_xue":     {"name": "海盗靴", "slot": "boots", "quality": "blue", "lv": 14, "series": "铁港", "req": {"agi": 12}, "source": "锻造"},
    "eq_shui_shou_hu_tui": {"name": "水手护腿", "slot": "legs", "quality": "blue", "lv": 14, "series": "铁港", "req": {"agi": 12}, "source": "锻造"},
    "eq_zhen_zhu_xiang_lian": {"name": "珍珠项链", "slot": "necklace", "quality": "purple", "lv": 18, "series": "铁港", "req": {"agi": 18}, "source": "图纸"},
    "eq_mao_xing_jie_zhi": {"name": "锚形戒指", "slot": "ring", "quality": "purple", "lv": 20, "series": "铁港", "req": {"str": 15, "agi": 15}, "source": "图纸"},
    "eq_jin_gou_wan_dao": {"name": "金钩弯刀", "slot": "weapon", "weapon_type": "sword", "quality": "orange", "lv": 26, "series": "铁港", "req": {"agi": 25}, "legendary": "gold_hook", "source": "boss"},
    "eq_jie_ke_jin_gou":  {"name": "杰克的金钩", "slot": "weapon", "weapon_type": "dagger", "quality": "orange", "lv": 28, "series": "铁港", "req": {"agi": 28}, "legendary": "jack_hook", "source": "legend"},
    # ================= 中域·圣光系列（Lv.25-55，王国/教会风） =================
    "eq_sheng_guang_chang_jian": {"name": "圣光长剑", "slot": "weapon", "weapon_type": "sword", "quality": "blue", "lv": 28, "series": "圣光", "req": {"str": 25}, "source": "锻造"},
    "eq_chen_xi_fa_zhang": {"name": "晨曦法杖", "slot": "weapon", "weapon_type": "staff", "quality": "blue", "lv": 28, "series": "圣光", "req": {"int": 25}, "source": "锻造"},
    "eq_wang_du_chang_gong": {"name": "王都长弓", "slot": "weapon", "weapon_type": "bow", "quality": "purple", "lv": 32, "series": "圣光", "req": {"agi": 35}, "source": "图纸"},
    "eq_sheng_dian_zhan_chui": {"name": "圣殿战锤", "slot": "weapon", "weapon_type": "mace", "quality": "purple", "lv": 34, "series": "圣光", "req": {"str": 38}, "source": "图纸"},
    "eq_qi_shi_tou_kui":  {"name": "骑士头盔", "slot": "helm", "quality": "blue", "lv": 28, "series": "圣光", "req": {"str": 25}, "source": "锻造"},
    "eq_sheng_guang_xiong_jia": {"name": "圣光胸甲", "slot": "armor", "quality": "blue", "lv": 30, "series": "圣光", "req": {"str": 28}, "source": "锻造"},
    "eq_qi_shi_chang_xue": {"name": "骑士长靴", "slot": "boots", "quality": "blue", "lv": 28, "series": "圣光", "req": {"str": 22}, "source": "锻造"},
    "eq_sheng_guang_hu_tui": {"name": "圣光护腿", "slot": "legs", "quality": "blue", "lv": 30, "series": "圣光", "req": {"str": 28}, "source": "锻造"},
    "eq_sheng_guang_hu_fu": {"name": "圣光护符", "slot": "necklace", "quality": "purple", "lv": 32, "series": "圣光", "req": {"int": 30}, "source": "图纸"},
    "eq_wang_guo_hui_jie": {"name": "王国徽戒", "slot": "ring", "quality": "purple", "lv": 34, "series": "圣光", "req": {"int": 28, "str": 28}, "source": "图纸"},
    "eq_gu_wang_jian":    {"name": "古王剑", "slot": "weapon", "weapon_type": "sword", "quality": "orange", "lv": 42, "series": "圣光", "req": {"str": 45}, "legendary": "ancient_king", "source": "boss"},
    "eq_shen_pan_zhi_lian": {"name": "审判之链", "slot": "necklace", "quality": "orange", "lv": 40, "series": "圣光", "req": {"int": 38}, "legendary": "judgment_chain", "source": "boss"},
    # ================= 西境·月语系列（Lv.45-75，精灵风） =================
    "eq_yue_yu_chang_gong": {"name": "月语长弓", "slot": "weapon", "weapon_type": "bow", "quality": "purple", "lv": 52, "series": "月语", "req": {"agi": 55}, "source": "图纸"},
    "eq_yin_ye_fa_zhang": {"name": "银叶法杖", "slot": "weapon", "weapon_type": "staff", "quality": "purple", "lv": 52, "series": "月语", "req": {"int": 55}, "source": "图纸"},
    "eq_yue_guang_duan_ren": {"name": "月光短刃", "slot": "weapon", "weapon_type": "dagger", "quality": "purple", "lv": 50, "series": "月语", "req": {"agi": 50}, "source": "图纸"},
    "eq_yue_guan_tou_kui": {"name": "月冠头盔", "slot": "helm", "quality": "purple", "lv": 50, "series": "月语", "req": {"agi": 50}, "source": "图纸"},
    "eq_jing_ling_lian_jia": {"name": "精灵链甲", "slot": "armor", "quality": "purple", "lv": 55, "series": "月语", "req": {"agi": 55}, "source": "图纸"},
    "eq_yue_zhi_xue":     {"name": "月之靴", "slot": "boots", "quality": "purple", "lv": 50, "series": "月语", "req": {"agi": 50}, "source": "图纸"},
    "eq_yue_yu_hu_tui":   {"name": "月语护腿", "slot": "legs", "quality": "purple", "lv": 52, "series": "月语", "req": {"agi": 52}, "source": "图纸"},
    "eq_xing_yu_xiang_lian": {"name": "星语项链", "slot": "necklace", "quality": "purple", "lv": 52, "series": "月语", "req": {"int": 52}, "source": "图纸"},
    "eq_yue_hua_jie_zhi": {"name": "月华戒指", "slot": "ring", "quality": "purple", "lv": 50, "series": "月语", "req": {"agi": 50}, "source": "图纸"},
    "eq_chen_xi_zhi_guan": {"name": "晨曦之冠", "slot": "helm", "quality": "orange", "lv": 62, "series": "月语", "req": {"agi": 60}, "legendary": "dawn_crown", "source": "boss"},
    "eq_yue_shen_zhi_gong": {"name": "月神之弓", "slot": "weapon", "weapon_type": "bow", "quality": "orange", "lv": 70, "series": "月语", "req": {"agi": 65}, "legendary": "moon_bow", "source": "legend"},
    # ================= 北境·霜狼系列（Lv.60-85，北境/矮人风） =================
    "eq_shuang_lang_chang_jian": {"name": "霜狼长剑", "slot": "weapon", "weapon_type": "sword", "quality": "purple", "lv": 65, "series": "霜狼", "req": {"str": 65}, "source": "图纸"},
    "eq_tie_zhen_zhan_chui": {"name": "铁砧战锤", "slot": "weapon", "weapon_type": "mace", "quality": "purple", "lv": 68, "series": "霜狼", "req": {"str": 70}, "source": "图纸"},
    "eq_bei_feng_chang_gong": {"name": "北风长弓", "slot": "weapon", "weapon_type": "bow", "quality": "purple", "lv": 65, "series": "霜狼", "req": {"agi": 65}, "source": "图纸"},
    "eq_shuang_lang_tou_kui": {"name": "霜狼头盔", "slot": "helm", "quality": "purple", "lv": 60, "series": "霜狼", "req": {"str": 60}, "source": "图纸"},
    "eq_tie_zhen_xiong_jia": {"name": "铁砧胸甲", "slot": "armor", "quality": "purple", "lv": 66, "series": "霜狼", "req": {"str": 68}, "source": "图纸"},
    "eq_shuang_yuan_chang_xue": {"name": "霜原长靴", "slot": "boots", "quality": "purple", "lv": 60, "series": "霜狼", "req": {"str": 60}, "source": "图纸"},
    "eq_shuang_lang_hu_tui": {"name": "霜狼护腿", "slot": "legs", "quality": "purple", "lv": 62, "series": "霜狼", "req": {"str": 62}, "source": "图纸"},
    "eq_rong_lu_xiang_lian": {"name": "熔炉项链", "slot": "necklace", "quality": "purple", "lv": 62, "series": "霜狼", "req": {"str": 62}, "source": "图纸"},
    "eq_fu_wen_jie_zhi":  {"name": "符文戒指", "slot": "ring", "quality": "purple", "lv": 65, "series": "霜狼", "req": {"int": 60, "str": 60}, "source": "图纸"},
    "eq_he_er_jia_de_ji_qi": {"name": "赫尔加的祭器", "slot": "necklace", "quality": "orange", "lv": 72, "series": "霜狼", "req": {"str": 68}, "legendary": "helga_relic", "source": "boss"},
    "eq_da_di_zhi_xin":   {"name": "符文战锤·大地之心", "slot": "weapon", "weapon_type": "mace", "quality": "orange", "lv": 78, "series": "霜狼", "req": {"str": 75}, "legendary": "earth_heart", "source": "legend"},
    # ================= 东境·龙脊系列（Lv.80-100，龙裔风） =================
    "eq_long_ji_da_jian": {"name": "龙脊大剑", "slot": "weapon", "weapon_type": "sword", "quality": "purple", "lv": 85, "series": "龙脊", "req": {"str": 85}, "source": "图纸"},
    "eq_long_yu_fa_zhang": {"name": "龙语法杖", "slot": "weapon", "weapon_type": "staff", "quality": "purple", "lv": 85, "series": "龙脊", "req": {"int": 85}, "source": "图纸"},
    "eq_long_lin_tou_kui": {"name": "龙鳞头盔", "slot": "helm", "quality": "purple", "lv": 80, "series": "龙脊", "req": {"str": 80}, "source": "图纸"},
    "eq_long_lin_xiong_jia": {"name": "龙鳞胸甲", "slot": "armor", "quality": "purple", "lv": 85, "series": "龙脊", "req": {"str": 85}, "source": "图纸"},
    "eq_long_lin_hu_tui": {"name": "龙鳞护腿", "slot": "legs", "quality": "purple", "lv": 82, "series": "龙脊", "req": {"str": 82}, "source": "图纸"},
    "eq_long_zhao_shou_tao": {"name": "龙爪手套", "slot": "weapon", "weapon_type": "fist", "quality": "purple", "lv": 82, "series": "龙脊", "req": {"str": 75}, "source": "图纸"},
    "eq_long_yan_xiang_lian": {"name": "龙眼项链", "slot": "necklace", "quality": "purple", "lv": 80, "series": "龙脊", "req": {"str": 80}, "source": "图纸"},
    "eq_long_yu_sheng_jian": {"name": "龙语圣剑", "slot": "weapon", "weapon_type": "sword", "quality": "orange", "lv": 92, "series": "龙脊", "req": {"str": 95}, "legendary": "dragon_tongue", "source": "boss"},
    "eq_li_ming_zhi_guang": {"name": "黎明之光", "slot": "weapon", "weapon_type": "sword", "quality": "orange", "lv": 98, "series": "龙脊", "req": {"str": 90, "int": 90}, "legendary": "dawn_light", "source": "legend"},
    # ================= 外域·无尽海·海神系列（Lv.55-78，海风套进阶） =================
    "eq_hai_shen_san_cha_ji": {"name": "海神三叉戟", "slot": "weapon", "weapon_type": "mace", "quality": "purple", "lv": 58, "series": "海神", "req": {"str": 58, "agi": 58}, "source": "图纸"},
    "eq_chao_xi_fa_zhang": {"name": "潮汐法杖", "slot": "weapon", "weapon_type": "staff", "quality": "purple", "lv": 58, "series": "海神", "req": {"int": 60}, "source": "图纸"},
    "eq_zhen_zhu_tou_guan": {"name": "珍珠头冠", "slot": "helm", "quality": "purple", "lv": 55, "series": "海神", "req": {"agi": 55}, "source": "图纸"},
    "eq_long_lin_hai_jia": {"name": "龙鳞海甲", "slot": "armor", "quality": "purple", "lv": 60, "series": "海神", "req": {"agi": 60}, "source": "图纸"},
    "eq_hai_shen_chang_xue": {"name": "海神长靴", "slot": "boots", "quality": "purple", "lv": 55, "series": "海神", "req": {"agi": 55}, "source": "图纸"},
    "eq_hai_shen_hu_tui": {"name": "海神护腿", "slot": "legs", "quality": "purple", "lv": 58, "series": "海神", "req": {"agi": 58}, "source": "图纸"},
    "eq_hai_shen_xiang_lian": {"name": "海神项链", "slot": "necklace", "quality": "purple", "lv": 58, "series": "海神", "req": {"agi": 58}, "source": "图纸"},
    "eq_hai_shen_jie_zhi": {"name": "海神戒指", "slot": "ring", "quality": "purple", "lv": 60, "series": "海神", "req": {"agi": 60}, "source": "图纸"},
    "eq_lang_ge_zhi_lei": {"name": "澜歌之泪", "slot": "necklace", "quality": "orange", "lv": 68, "series": "海神", "req": {"int": 70}, "legendary": "lang_tear", "source": "boss"},
    "eq_ao_lan_zhi_zhu":  {"name": "敖澜之珠", "slot": "ring", "quality": "orange", "lv": 72, "series": "海神", "req": {"agi": 68}, "legendary": "ao_lan_pearl", "source": "boss"},
    # ================= 外域·幽暗地域·地底系列（Lv.65-90，地底套） =================
    "eq_shen_yuan_zhan_ren": {"name": "深渊战刃", "slot": "weapon", "weapon_type": "sword", "quality": "purple", "lv": 75, "series": "地底", "req": {"str": 75}, "source": "图纸"},
    "eq_rong_yan_fa_zhang": {"name": "熔岩法杖", "slot": "weapon", "weapon_type": "staff", "quality": "purple", "lv": 72, "series": "地底", "req": {"int": 72}, "source": "图纸"},
    "eq_shen_yuan_tou_kui": {"name": "深渊头盔", "slot": "helm", "quality": "purple", "lv": 70, "series": "地底", "req": {"str": 70}, "source": "图纸"},
    "eq_hei_yao_xiong_jia": {"name": "黑曜胸甲", "slot": "armor", "quality": "purple", "lv": 78, "series": "地底", "req": {"str": 78}, "source": "图纸"},
    "eq_di_di_chang_xue": {"name": "地底长靴", "slot": "boots", "quality": "purple", "lv": 70, "series": "地底", "req": {"str": 70}, "source": "图纸"},
    "eq_hei_yao_hu_tui":  {"name": "黑曜护腿", "slot": "legs", "quality": "purple", "lv": 75, "series": "地底", "req": {"str": 75}, "source": "图纸"},
    "eq_shen_yuan_xiang_lian": {"name": "深渊项链", "slot": "necklace", "quality": "purple", "lv": 75, "series": "地底", "req": {"str": 72}, "source": "图纸"},
    "eq_mo_luo_zhi_guan": {"name": "摩罗之冠", "slot": "helm", "quality": "orange", "lv": 85, "series": "地底", "req": {"str": 90}, "legendary": "moro_crown", "source": "boss"},
    # ================= 外域·风翼群岛·苍穹系列（Lv.85-100，苍穹套） =================
    "eq_cang_qiong_zhi_qiang": {"name": "苍穹之枪", "slot": "weapon", "weapon_type": "spear", "quality": "purple", "lv": 88, "series": "苍穹", "req": {"str": 88}, "source": "图纸"},
    "eq_xing_guang_fa_zhang": {"name": "星光法杖", "slot": "weapon", "weapon_type": "staff", "quality": "purple", "lv": 88, "series": "苍穹", "req": {"int": 88}, "source": "图纸"},
    "eq_cang_qiong_tou_kui": {"name": "苍穹头盔", "slot": "helm", "quality": "purple", "lv": 85, "series": "苍穹", "req": {"agi": 85}, "source": "图纸"},
    "eq_yun_wen_xiong_jia": {"name": "云纹胸甲", "slot": "armor", "quality": "purple", "lv": 88, "series": "苍穹", "req": {"agi": 88}, "source": "图纸"},
    "eq_xing_hui_chang_xue": {"name": "星辉长靴", "slot": "boots", "quality": "purple", "lv": 85, "series": "苍穹", "req": {"agi": 85}, "source": "图纸"},
    "eq_cang_qiong_hu_tui": {"name": "苍穹护腿", "slot": "legs", "quality": "purple", "lv": 86, "series": "苍穹", "req": {"agi": 86}, "source": "图纸"},
    "eq_cang_qiong_xiang_lian": {"name": "苍穹项链", "slot": "necklace", "quality": "purple", "lv": 88, "series": "苍穹", "req": {"int": 88}, "source": "图纸"},
    "eq_ao_la_sheng_yin": {"name": "奥拉圣印", "slot": "necklace", "quality": "orange", "lv": 95, "series": "苍穹", "req": {"int": 95}, "legendary": "aura_seal", "source": "boss"},
}

# 系列 → 系列名（套装主题名：10 章五节）
SERIES_SETS = {
    "橡木": "橡木套", "铁港": "海风套", "圣光": "圣光套", "月语": "月语套",
    "霜狼": "霜狼套", "龙脊": "龙脊套", "海神": "海神套", "地底": "地底套", "苍穹": "苍穹套",
}

# 名册查询辅助：按名称索引（锻造/掉落/商店通用）
EQUIP_ROSTER_BY_NAME = {}
for _rid, _r in EQUIP_ROSTER.items():
    EQUIP_ROSTER_BY_NAME.setdefault(_r["name"], []).append(_rid)
