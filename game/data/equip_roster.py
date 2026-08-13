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
    "eq_tie_jian":        {"name": "铁剑", "slot": "weapon", "weapon_type": "sword", "quality": "white", "lv": 2,  "series": "橡木", "source": "商店"},
    "eq_lie_gong":        {"name": "猎弓", "slot": "weapon", "weapon_type": "bow", "quality": "white", "lv": 2,  "series": "橡木", "source": "商店"},
    "eq_xue_tu_fa_zhang": {"name": "学徒法杖", "slot": "weapon", "weapon_type": "staff", "quality": "white", "lv": 2, "series": "橡木", "source": "商店"},
    "eq_xiang_mu_duan_gun": {"name": "橡木短棍", "slot": "weapon", "weapon_type": "mace", "quality": "white", "lv": 2, "series": "橡木", "source": "商店"},
    "eq_pi_jia":          {"name": "皮甲", "slot": "armor", "quality": "white", "lv": 3, "series": "橡木", "req": {"vit": 3}, "source": "商店"},
    "eq_jiu_pi_xue":      {"name": "旧皮靴", "slot": "boots", "quality": "white", "lv": 3, "series": "橡木", "req": {"agi": 3}, "source": "商店"},
    "eq_xiang_mu_dun":    {"name": "橡木盾", "slot": "weapon", "weapon_type": "shield", "quality": "blue", "lv": 6, "series": "橡木", "req": {"str": 8}, "source": "锻造"},
    "eq_lie_lu_gong":     {"name": "猎鹿弓", "slot": "weapon", "weapon_type": "bow", "quality": "blue", "lv": 6, "series": "橡木", "req": {"agi": 8}, "source": "锻造"},
    "eq_xue_tu_zhi_zhang": {"name": "学徒之杖", "slot": "weapon", "weapon_type": "staff", "quality": "blue", "lv": 6, "series": "橡木", "req": {"int": 8}, "source": "锻造"},
    "eq_bai_lu_pi_jia":   {"name": "白鹿皮甲", "slot": "armor", "quality": "blue", "lv": 8, "series": "橡木", "req": {"agi": 8}, "source": "锻造"},
    "eq_xiang_mu_hu_tui": {"name": "橡木护腿", "slot": "legs", "quality": "white", "lv": 3, "series": "橡木", "req": {"vit": 3}, "source": "商店"},
    # v93 商店装：毛皮帽 + 白装饰品（v95 去属性需求，新手期不卡职业）
    "eq_mao_pi_mao":      {"name": "毛皮帽", "slot": "helm", "quality": "white", "lv": 3, "series": "橡木", "source": "商店"},
    "eq_xiang_mu_jie_zhi": {"name": "橡木戒指", "slot": "ring", "quality": "white", "lv": 4, "series": "橡木", "source": "商店"},
    "eq_xiang_mu_xiang_lian": {"name": "橡木项链", "slot": "necklace", "quality": "white", "lv": 4, "series": "橡木", "source": "商店"},
    # #236: 拳师武器链——低等级拳套名册（力量型 req，商店可购）
    "eq_bu_quan_tao":    {"name": "布拳套", "slot": "weapon", "weapon_type": "fist", "quality": "white", "lv": 2, "series": "橡木", "source": "商店"},
    # v93 商店装：白鹿绿装套（v95 去属性需求）
    "eq_bai_lu_pi_mao":   {"name": "白鹿皮帽", "slot": "helm", "quality": "green", "lv": 6, "series": "白鹿", "source": "商店"},
    "eq_bai_lu_xiong_jia": {"name": "白鹿胸甲", "slot": "armor", "quality": "green", "lv": 7, "series": "白鹿", "source": "商店"},
    "eq_bai_lu_hu_tui":   {"name": "白鹿护腿", "slot": "legs", "quality": "green", "lv": 7, "series": "白鹿", "source": "商店"},
    "eq_bai_lu_pi_xue":   {"name": "白鹿皮靴", "slot": "boots", "quality": "green", "lv": 6, "series": "白鹿", "source": "商店"},
    "eq_bai_lu_zhi_jie":  {"name": "白鹿之戒", "slot": "ring", "quality": "green", "lv": 8, "series": "白鹿", "source": "商店"},
    "eq_bai_lu_diao_zhu": {"name": "白鹿吊坠", "slot": "necklace", "quality": "green", "lv": 8, "series": "白鹿", "source": "商店"},
    # v104 M20 P1：s3 支线「铁匠的传家宝」奖励（06 章 S3「汉斯的手工武器」，白鹿城铁匠汉斯亲手打造）
    "eq_han_si_shou_gong_wu_qi": {"name": "汉斯的手工武器", "slot": "weapon", "weapon_type": "sword", "quality": "blue", "lv": 8, "series": "白鹿", "req": {"str": 8}, "source": "支线"},
    "eq_pi_ge_quan_tao": {"name": "皮革拳套", "slot": "weapon", "weapon_type": "fist", "quality": "green", "lv": 6, "series": "白鹿", "req": {"str": 6}, "source": "商店"},  # #236: 拳师武器链
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
    "eq_tie_zhi_hu":      {"name": "铁指虎", "slot": "weapon", "weapon_type": "fist", "quality": "blue", "lv": 14, "series": "铁港", "req": {"str": 12}, "source": "商店"},  # #236: 拳师武器链
    "eq_jin_gou_wan_dao": {"name": "金钩弯刀", "slot": "weapon", "weapon_type": "sword", "quality": "orange", "lv": 26, "series": "铁港", "req": {"agi": 25}, "legendary": "gold_hook", "source": "boss"},
    "eq_jie_ke_jin_gou":  {"name": "杰克的金钩", "slot": "weapon", "weapon_type": "dagger", "quality": "orange", "lv": 28, "series": "铁港", "req": {"agi": 28}, "legendary": "jack_hook", "source": "legend"},
    # v104 修复（M06 P1/P2-7）：策划案 10 章 226 行『17 个 Boss 传说图纸装备』含咕噜的皇冠
    # （04 章 128 行 哥布林酋长·咕噜 传说图纸）此前名册+配方全无，此处补齐落地
    "eq_gu_lu_de_huang_guan": {"name": "咕噜的皇冠", "slot": "helm", "quality": "orange", "lv": 20, "series": "橡木", "req": {"str": 20}, "legendary": "goblin_crown", "source": "图纸"},
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
    # ================= v104 M07 修复 P1：中段补档（Lv.35-49 名册/商店/锻造三断，策划案 10 章 4.10 消除断档）=================
    # 圣光系列（中域 Lv.25-55）补 Lv.36-44 锻造蓝装：覆盖 armor 31-54/helm 29-49/boots 29-49/legs 31-51/武器 35-49 断档
    "eq_sheng_guang_zhan_kui": {"name": "圣光战盔", "slot": "helm", "quality": "blue", "lv": 38, "series": "圣光", "req": {"str": 32}, "source": "锻造"},
    "eq_sheng_guang_zhong_jia": {"name": "圣光重甲", "slot": "armor", "quality": "blue", "lv": 40, "series": "圣光", "req": {"str": 34}, "source": "锻造"},
    "eq_sheng_guang_zhong_xue": {"name": "圣光重靴", "slot": "boots", "quality": "blue", "lv": 38, "series": "圣光", "req": {"str": 30}, "source": "锻造"},
    "eq_sheng_guang_zhan_tui": {"name": "圣光战腿", "slot": "legs", "quality": "blue", "lv": 40, "series": "圣光", "req": {"str": 34}, "source": "锻造"},
    "eq_sheng_cai_chang_jian": {"name": "圣裁长剑", "slot": "weapon", "weapon_type": "sword", "quality": "blue", "lv": 42, "series": "圣光", "req": {"str": 38}, "source": "锻造"},
    "eq_sheng_guang_fa_zhang": {"name": "圣光法杖", "slot": "weapon", "weapon_type": "staff", "quality": "blue", "lv": 40, "series": "圣光", "req": {"int": 36}, "source": "锻造"},
    "eq_sheng_guang_lie_gong": {"name": "圣光猎弓", "slot": "weapon", "weapon_type": "bow", "quality": "blue", "lv": 38, "series": "圣光", "req": {"agi": 34}, "source": "锻造"},
    "eq_sheng_guang_zhan_chui": {"name": "圣光战锤", "slot": "weapon", "weapon_type": "mace", "quality": "blue", "lv": 44, "series": "圣光", "req": {"str": 40}, "source": "锻造"},
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
    # v104 修复（M06 P1-4）：暮影龙魂（世界 Boss/龙陨战魂·暮影掉落）此前无消费端，
    # 策划案 13 章 5.6『暮影龙魂→图纸·暮影之刃』，此处补齐装备+配方闭环
    "eq_mu_ying_zhi_ren": {"name": "暮影之刃", "slot": "weapon", "weapon_type": "dagger", "quality": "orange", "lv": 96, "series": "龙脊", "req": {"agi": 96}, "legendary": "mu_ying_blade", "source": "图纸"},
    # ================= v87 隐藏线：星尘套（H6 失落图书馆，Lv.55 紫）=================
    "eq_xing_chen_fa_zhang": {"name": "星尘法杖", "slot": "weapon", "weapon_type": "staff", "quality": "purple", "lv": 55, "series": "星尘", "req": {"int": 60}, "source": "图纸"},
    "eq_xing_chen_chang_pao": {"name": "星尘长袍", "slot": "armor", "quality": "purple", "lv": 55, "series": "星尘", "req": {"int": 55}, "source": "图纸"},
    "eq_xing_chen_zhi_jie": {"name": "星尘之戒", "slot": "ring", "quality": "purple", "lv": 55, "series": "星尘", "req": {"int": 40}, "source": "图纸"},
    "eq_xing_chen_zhui_shi": {"name": "星尘坠饰", "slot": "necklace", "quality": "purple", "lv": 55, "series": "星尘", "req": {"int": 45}, "source": "图纸"},
    "eq_xing_chen_hu_tui": {"name": "星尘护腿", "slot": "legs", "quality": "purple", "lv": 55, "series": "星尘", "req": {"int": 50}, "source": "图纸"},
    # ================= v87 隐藏线：灰烬守卫套（H7 灰烬回廊，Lv.85 橙）=================
    "eq_hui_jin_chang_jian": {"name": "灰烬长剑", "slot": "weapon", "weapon_type": "sword", "quality": "orange", "lv": 85, "series": "灰烬守卫", "req": {"str": 90}, "legendary": "ember_ward", "source": "boss"},
    "eq_hui_jin_kai_jia": {"name": "灰烬铠甲", "slot": "armor", "quality": "orange", "lv": 85, "series": "灰烬守卫", "req": {"str": 85}, "legendary": "ember_ward", "source": "boss"},
    "eq_hui_jin_zhi_kui": {"name": "灰烬之盔", "slot": "helm", "quality": "orange", "lv": 85, "series": "灰烬守卫", "req": {"str": 80}, "legendary": "ember_ward", "source": "boss"},
    "eq_hui_jin_zhi_dun": {"name": "灰烬之盾", "slot": "weapon", "weapon_type": "shield", "quality": "orange", "lv": 85, "series": "灰烬守卫", "req": {"str": 75}, "legendary": "ember_ward", "source": "boss"},
    "eq_hui_jin_hu_tui": {"name": "灰烬护腿", "slot": "legs", "quality": "orange", "lv": 85, "series": "灰烬守卫", "req": {"str": 82}, "legendary": "ember_ward", "source": "boss"},
    "eq_hui_jin_zhan_xue": {"name": "灰烬战靴", "slot": "boots", "quality": "orange", "lv": 85, "series": "灰烬守卫", "req": {"str": 78}, "legendary": "ember_ward", "source": "boss"},
    # ================= v87 隐藏线：传说·星陨之剑（隐藏线终点，Lv.100 橙·传说）=================
    "eq_starfall_sword": {"name": "星陨之剑", "slot": "weapon", "weapon_type": "sword", "quality": "orange", "lv": 100, "series": "星尘", "req": {"str": 100, "int": 100}, "legendary": "starfall", "source": "legend"},
    # ================= v101.25e 商店断层补档：锻造源中间档（Lv.18-26，银铃/翡翠/迷雾风格）=================
    "eq_yin_ling_duan_ren": {"name": "银铃短刃", "slot": "weapon", "weapon_type": "sword", "quality": "blue", "lv": 18, "series": "银铃", "req": {"agi": 16}, "source": "锻造"},
    "eq_yin_ling_hu_tui": {"name": "银铃护腿", "slot": "legs", "quality": "blue", "lv": 18, "series": "银铃", "req": {"agi": 16}, "source": "锻造"},
    "eq_fei_cui_pi_jia": {"name": "翡翠皮甲", "slot": "armor", "quality": "blue", "lv": 20, "series": "翡翠", "req": {"agi": 18}, "source": "锻造"},
    "eq_fei_cui_hu_tui": {"name": "翡翠护腿", "slot": "legs", "quality": "blue", "lv": 20, "series": "翡翠", "req": {"agi": 18}, "source": "锻造"},
    "eq_mi_wu_hu_tui": {"name": "迷雾护腿", "slot": "legs", "quality": "blue", "lv": 22, "series": "迷雾", "req": {"vit": 20}, "source": "锻造"},
    "eq_yin_ling_zhang": {"name": "银铃杖", "slot": "weapon", "weapon_type": "staff", "quality": "blue", "lv": 24, "series": "银铃", "req": {"int": 22}, "source": "锻造"},
    "eq_mi_wu_dou_mao": {"name": "迷雾兜帽", "slot": "helm", "quality": "blue", "lv": 26, "series": "迷雾", "req": {"int": 24}, "source": "锻造"},
    # ================= v101.30d playtest O44/O45 补齐：补档套残缺件数 + 游侠弓档（策划案 10 章 4.10）=================
    # 银铃套补 4 件（原有 短刃/护腿/杖 → 凑齐 6 件）
    "eq_yin_ling_tou_kui": {"name": "银铃头盔", "slot": "helm", "quality": "blue", "lv": 18, "series": "银铃", "req": {"agi": 16}, "source": "锻造"},
    "eq_yin_ling_xiong_jia": {"name": "银铃胸甲", "slot": "armor", "quality": "blue", "lv": 18, "series": "银铃", "req": {"agi": 16}, "source": "锻造"},
    "eq_yin_ling_zhan_xue": {"name": "银铃战靴", "slot": "boots", "quality": "blue", "lv": 18, "series": "银铃", "req": {"agi": 16}, "source": "锻造"},
    "eq_yin_ling_xiang_lian": {"name": "银铃项链", "slot": "necklace", "quality": "blue", "lv": 18, "series": "银铃", "req": {"agi": 16}, "source": "锻造"},
    # 翡翠套补 3 件（原有 皮甲/护腿 → 凑齐 5 件）
    "eq_fei_cui_tou_kui": {"name": "翡翠头盔", "slot": "helm", "quality": "blue", "lv": 20, "series": "翡翠", "req": {"agi": 18}, "source": "锻造"},
    "eq_fei_cui_zhan_xue": {"name": "翡翠战靴", "slot": "boots", "quality": "blue", "lv": 20, "series": "翡翠", "req": {"agi": 18}, "source": "锻造"},
    "eq_fei_cui_xiang_lian": {"name": "翡翠项链", "slot": "necklace", "quality": "blue", "lv": 20, "series": "翡翠", "req": {"agi": 18}, "source": "锻造"},
    # 迷雾套补 3 件（原有 护腿/兜帽 → 凑齐 5 件）
    "eq_mi_wu_xiong_jia": {"name": "迷雾胸甲", "slot": "armor", "quality": "blue", "lv": 22, "series": "迷雾", "req": {"vit": 20}, "source": "锻造"},
    "eq_mi_wu_zhan_xue": {"name": "迷雾战靴", "slot": "boots", "quality": "blue", "lv": 22, "series": "迷雾", "req": {"vit": 20}, "source": "锻造"},
    "eq_mi_wu_xiang_lian": {"name": "迷雾项链", "slot": "necklace", "quality": "blue", "lv": 24, "series": "迷雾", "req": {"vit": 22}, "source": "锻造"},
    # 游侠弓档补录（Lv.18→32 断档，playtest O44 实锤）
    "eq_lie_feng_chang_gong": {"name": "猎风长弓", "slot": "weapon", "weapon_type": "bow", "quality": "blue", "lv": 24, "series": "银铃", "req": {"agi": 24}, "source": "锻造"},
    "eq_ji_feng_chang_gong": {"name": "疾风长弓", "slot": "weapon", "weapon_type": "bow", "quality": "blue", "lv": 28, "series": "迷雾", "req": {"agi": 28}, "source": "锻造"},
    # ================= v104 M08 P1-5：SHOP_WEAPONS 9 件武器名补名册 =================
    # v101.28l #430 声称"补 Lv.18 进阶蓝装"但只改了 shop.py 没进名册 → 购买走随机兜底
    # generate_equip+覆盖名（economy.py _buy_weapon），属性需求随机、无固定词条。
    # 现补名册：req 对齐同级蓝装（银铃短刃 Lv.18 agi16 / 弯刀 Lv.14 agi12 递推），
    # source=商店（与 SHOP_WEAPONS 上架一致，不产图纸）。
    "eq_jing_tie_chang_jian": {"name": "精铁长剑", "slot": "weapon", "weapon_type": "sword", "quality": "blue", "lv": 18, "series": "白鹿", "req": {"str": 16}, "source": "商店"},
    "eq_ying_mu_zhan_gong": {"name": "硬木战弓", "slot": "weapon", "weapon_type": "bow", "quality": "blue", "lv": 18, "series": "白鹿", "req": {"agi": 16}, "source": "商店"},
    "eq_qi_yuan_fa_zhang": {"name": "祈愿法杖", "slot": "weapon", "weapon_type": "staff", "quality": "blue", "lv": 18, "series": "白鹿", "req": {"int": 16}, "source": "商店"},
    "eq_tie_tou_zhan_chui": {"name": "铁头战锤", "slot": "weapon", "weapon_type": "mace", "quality": "blue", "lv": 18, "series": "白鹿", "req": {"str": 16}, "source": "商店"},
    "eq_hou_pi_quan_tao": {"name": "厚皮拳套", "slot": "weapon", "weapon_type": "fist", "quality": "blue", "lv": 18, "series": "白鹿", "req": {"str": 16}, "source": "商店"},
    "eq_shui_shou_wan_dao": {"name": "水手弯刀", "slot": "weapon", "weapon_type": "sword", "quality": "blue", "lv": 22, "series": "铁港", "req": {"agi": 20}, "source": "商店"},
    "eq_yuan_yang_chang_gong": {"name": "远洋长弓", "slot": "weapon", "weapon_type": "bow", "quality": "blue", "lv": 22, "series": "铁港", "req": {"agi": 20}, "source": "商店"},
    "eq_tie_mao_zhan_chui": {"name": "铁锚战锤", "slot": "weapon", "weapon_type": "mace", "quality": "blue", "lv": 22, "series": "铁港", "req": {"str": 20}, "source": "商店"},
    "eq_tie_lian_quan_tao": {"name": "铁链拳套", "slot": "weapon", "weapon_type": "fist", "quality": "blue", "lv": 22, "series": "铁港", "req": {"str": 20}, "source": "商店"},
}

# 系列 → 系列名（套装主题名：10 章五节）
SERIES_SETS = {
    "橡木": "橡木套", "铁港": "海风套", "圣光": "圣光套", "月语": "月语套",
    "霜狼": "霜狼套", "龙脊": "龙脊套", "海神": "海神套", "地底": "地底套", "苍穹": "苍穹套",
    # v93 商店装：白鹿绿装套
    "白鹿": "白鹿套",
    # v101.25e 商店断层补档系列
    "银铃": "银铃套", "翡翠": "翡翠套", "迷雾": "迷雾套",
    # v87 隐藏线
    "星尘": "星尘套", "灰烬守卫": "灰烬守卫套",
}

# 名册查询辅助：按名称索引（锻造/掉落/商店通用）
# ================= 装备描述生成（v101.25g 鱼鱼：每个装备都要有描述） =================
# 系列主题 × 部位/武器类型模板；手写 desc 优先保留
_EQ_SERIES_THEME = {
    "橡木": "橡木镇匠人的朴实手艺，耐用又可靠",
    "白鹿": "白鹿之森猎人的精巧之作，轻便而灵动",
    "银铃": "银铃河畔工匠的细心打磨，线条干净利落",
    "翡翠": "翡翠森林的藤蔓缠绕纹样，带着自然的生机",
    "迷雾": "迷雾沼泽中锻造的神秘器物，蒙着一层水汽",
    "铁港": "铁港城船匠与铁匠的合作，透着海风的咸涩",
    "圣光": "圣光教会赐福的制式装备，纹着金色的圣徽",
    "月语": "月语精灵的月光工艺，优雅得不像凡物",
    "霜狼": "北境霜狼氏族的手笔，粗犷中带着寒气",
    "龙脊": "龙脊山脉矮人的重锤杰作，坚固得能扛住巨龙的吐息",
    "海神": "海神信徒的祭祀器物，浸泡过潮汐的低语",
    "地底": "地底矿脉深处出土的造物，沉静而厚重",
    "苍穹": "苍穹之上流云般轻盈的工艺，似乎随时会乘风而起",
    "星尘": "星尘降临之地的瑰丽造物，流转着点点星光",
    "灰烬守卫": "灰烬守卫的制式装备，淬炼过烈焰的余温",
}
_EQ_SLOT_DESC = {
    "weapon": {
        "sword": "{series}风格的长剑，剑脊笔直，护手朴素",
        "dagger": "{series}风格的短刃，轻巧锋利，适合贴身缠斗",
        "staff": "{series}风格的法杖，杖身刻着细密的魔纹",
        "bow": "{series}风格的长弓，弓臂弧度优美，弦声清越",
        "mace": "{series}风格的战锤，锤头沉重，一击足以破盾",
        "fist": "{series}风格的拳套，贴合拳面，攻防一体",
        "shield": "{series}风格的盾牌，盾面厚实，能挡下大部分攻击",
        "spear": "{series}风格的长枪，枪尖雪亮，横扫千军",
        "axe": "{series}风格的战斧，斧刃开得极利，势大力沉",
    },
    "helm": "{series}风格的头盔，护住要害，通风透气",
    "armor": "{series}风格的护甲，版型合体，活动自如",
    "legs": "{series}风格的护腿，膝盖处加厚，耐磨耐打",
    "boots": "{series}风格的靴子，鞋底防滑，走山路也稳当",
    "ring": "{series}风格的戒指，戒面光滑，指节处恰到好处",
    "necklace": "{series}风格的项链，链坠做工精细，贴身佩戴",
}


def _gen_eq_desc(e: dict) -> str:
    series = e.get("series", "冒险者")
    theme = _EQ_SERIES_THEME.get(series, f"{series}工匠的作品")
    slot = e.get("slot", "armor")
    if slot == "weapon":
        wt = e.get("weapon_type", "sword")
        sub = _EQ_SLOT_DESC["weapon"].get(wt, _EQ_SLOT_DESC["weapon"]["sword"])
        base = sub.format(series=series)
    else:
        base = _EQ_SLOT_DESC.get(slot, _EQ_SLOT_DESC["armor"]).format(series=series)
    extra = ""
    if e.get("source") == "boss":
        extra = "，据说是强者的战利品"
    elif e.get("source") == "legend":
        extra = "，传说中才有的名物"
    elif e.get("quality") == "orange":
        extra = "，绝非凡品"
    elif e.get("quality") == "purple":
        extra = "，做工考究"
    return f"{base}。{theme}{extra}。"


# ================= 装备 desc 注入（v101.25g，手写优先） =================
for _rid, _r in EQUIP_ROSTER.items():
    if not _r.get("desc"):
        _r["desc"] = _gen_eq_desc(_r)

EQUIP_ROSTER_BY_NAME = {}
for _rid, _r in EQUIP_ROSTER.items():
    EQUIP_ROSTER_BY_NAME.setdefault(_r["name"], []).append(_rid)
