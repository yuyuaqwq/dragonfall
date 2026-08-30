# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - drop_add_v140.py（v140 波1：装备掉落数据，第四批方案）

打破 v93/v94『怪不掉装备』铁律的落地数据（2026-08-30）。
本文件纯数据、无逻辑；消费方为 v140 掉落逻辑（drops.py/instance.py 后续接线）。

包含三张表（另提供聚合导出 DROP_ADD）：
1. BOSS_EQUIP_DROP    副本 Boss 专属成品装备表：22 副本 Boss → 专属装备 id + 掉率 + 保底次数
   （与图纸体系解耦：成品=白板下限，图纸首功必掉 100% 确定性分流，互不冲突）
2. ELITE_EQUIP_DROP   野外精英专属紫装表：18 精英 → 专属装备 id（掉率统一 2%，保底 20 杀）
3. CHEST_EQUIP_RATE   宝箱开装备概率表：宝箱类型 → 白/绿/蓝/紫/橙 各品质开出概率

掉率分档（方案 4.1）：5%（新手）/ 8%（前期）/ 10%（中期·后期）/ 12%（大后期）
保底分档：20 / 15 / 12 杀必掉。
"""

# ================= 1. 副本 Boss 专属装备表（22 条） =================
# 结构：{副本id: {"equip": 装备id, "rate": 掉率, "pity": 保底击杀数}}
# 装备名 = Boss 身份物（与材料同名但 type=装备）；eq_* 拼音 id（西幻命名）。
BOSS_EQUIP_DROP = {
    # ---- 主线 8 ----
    "inst_goblin_camp":     {"equip": "eq_gu_lu_de_huang_guan",   "rate": 0.05, "pity": 20},  # 哥布林酋长·咕噜 → 咕噜的皇冠（头盔·橙·20）
    "inst_sea_cave":        {"equip": "eq_jin_gou_wan_dao",       "rate": 0.08, "pity": 15},  # 海盗王·独眼杰克 → 金钩弯刀（剑·橙·26）
    "inst_old_king_tomb":   {"equip": "eq_gu_wang_jian",          "rate": 0.08, "pity": 15},  # 古王·奥德里克 → 古王剑（剑·橙·42）
    "inst_secret_crypt":    {"equip": "eq_ma_er_ku_si_de_fa_guan","rate": 0.10, "pity": 12},  # 审判长·马尔库斯 → 马尔库斯的法冠（头盔·橙·52）
    "inst_elven_ruins":     {"equip": "eq_chen_xi_zhi_guan",      "rate": 0.10, "pity": 12},  # 远古精灵王·晨曦 → 晨曦之冠（头盔·橙·62）
    "inst_ash_temple":      {"equip": "eq_he_er_jia_de_ji_qi",    "rate": 0.10, "pity": 12},  # 恶魔祭司·赫尔加 → 赫尔加的祭器（项链·橙·88）
    "inst_abyss_gate":      {"equip": "eq_shi_ye_zhi_mian",       "rate": 0.10, "pity": 12},  # 蚀夜(真相形态) → 蚀夜之面（头盔·橙·98）
    "inst_dragon_tomb":     {"equip": "eq_long_yu_sheng_jian",    "rate": 0.10, "pity": 12},  # 古龙·奥姆之影 → 龙语圣剑（剑·橙·92）
    # ---- 区域支线 5 ----
    "inst_deer_fort":       {"equip": "eq_yao_sai_you_ling_zhi_kui", "rate": 0.08, "pity": 15},  # 要塞幽灵 → 要塞幽灵之盔（头盔·紫）
    "inst_holy_trial":      {"equip": "eq_shi_lian_hui_zhang",    "rate": 0.08, "pity": 15},  # 试炼骑士长 → 试炼徽章（项链·紫）
    "inst_moon_temple":     {"equip": "eq_yue_hui_zhi_jie",       "rate": 0.08, "pity": 15},  # 月神守卫 → 月辉之戒（戒指·紫）
    "inst_frost_throne":    {"equip": "eq_yong_dong_zhi_xin",     "rate": 0.10, "pity": 12},  # 冰霜领主 → 永冻之心（项链·橙）
    "inst_storm_throne":    {"equip": "eq_feng_bao_zhi_guan",     "rate": 0.10, "pity": 12},  # 雷霆君主 → 风暴之冠（头盔·橙）
    # ---- 外域 6 ----
    "inst_sunken_ship":     {"equip": "eq_ke_luo_de_luo_pan",     "rate": 0.10, "pity": 12},  # 幽灵船长·克罗 → 克罗的罗盘（饰品·橙）
    "inst_siren_nest":      {"equip": "eq_lan_ge_zhi_guan",       "rate": 0.10, "pity": 12},  # 海妖女王·蓝歌 → 蓝歌之冠（头盔·橙）
    "inst_sea_god_temple":  {"equip": "eq_lang_ge_zhi_lei",       "rate": 0.10, "pity": 12},  # 海神祭司·澜歌 → 澜歌之泪（项链·橙·68）
    "inst_deep_dragon_palace": {"equip": "eq_ao_lan_zhi_zhu",     "rate": 0.10, "pity": 12},  # 深海龙王·敖澜 → 敖澜之珠（戒指·橙·72）
    "inst_gray_dwarf":      {"equip": "eq_shi_lu_zhan_chui",      "rate": 0.10, "pity": 12},  # 灰矮人领主·石炉 → 石炉战锤（战锤·橙）
    "inst_under_dragon":    {"equip": "eq_hei_yuan_zhi_yan",      "rate": 0.10, "pity": 12},  # 地底古龙·黑渊 → 黑渊之眼（项链·橙）
    # ---- 扩展 3 ----
    "inst_eye_of_storm":    {"equip": "eq_yun_nu_zhi_he",         "rate": 0.12, "pity": 12},  # 风暴之主·云怒 → 云怒之核（戒指·橙）
    "inst_abyss_throne":    {"equip": "eq_mo_luo_zhi_guan",       "rate": 0.10, "pity": 12},  # 深渊领主·摩罗 → 摩罗之冠（头盔·橙·85）
    "inst_cloud_sanctum":   {"equip": "eq_ao_la_sheng_yin",       "rate": 0.12, "pity": 12},  # 云中圣者·奥拉 → 奥拉圣印（项链·橙·95）
}

# ================= 2. 野外精英专属紫装表（18 条） =================
# 结构：{精英名: 装备id}；掉率统一 2% + 保底 20 杀（方案 4.2）。
# 优先补防具/饰品（名册紫/橙原以武器为主）；装备等级≈精英等级。
ELITE_EQUIP_DROP = {
    "峡谷巨魔":     "eq_ju_mo_liao_ya_zhui",     # Lv.8  巨魔獠牙坠（项链·紫）
    "野猪王·裂鬃":  "eq_lie_zong_zhan_kui",      # Lv.10 裂鬃战盔（头盔·紫）
    "狼王·灰影":    "eq_hui_ying_lang_ya_ren",   # Lv.14 灰影狼牙刃（短刃·紫）
    "沼泽巨鳄":     "eq_ju_e_lin_jia",           # Lv.18 巨鳄鳞甲（护甲·紫）
    "丘陵狼王·铁牙": "eq_tie_ya_zhan_kui",        # Lv.34 铁牙战盔（头盔·紫）
    "盗贼头目·黑鸦": "eq_hei_ya_mian_jin",        # Lv.38 黑鸦面巾（头盔·紫）
    "珊瑚礁主·红棘": "eq_hong_ji_shan_hu_jie",    # Lv.42 红棘珊瑚戒（戒指·紫）
    "海妖领主·潮汐": "eq_chao_xi_san_cha_ji",     # Lv.52 潮汐三叉戟（长枪·紫）
    "月狼王·银鬃":  "eq_yin_zong_yue_ren",       # Lv.56 银鬃月刃（短刃·紫）
    "风语王·岚歌":  "eq_lan_ge_yu_xue",          # Lv.58 岚歌羽靴（靴子·紫）
    "古树领主":     "eq_gu_shu_zhi_zhang",       # Lv.70 古树枝杖（法杖·紫）
    "霜巨魔王":     "eq_shuang_ju_mo_zhan_chui",  # Lv.72 霜巨魔战锤（战锤·紫）
    "熔岩领主":     "eq_rong_yan_zhong_jian",    # Lv.76 熔岩重剑（长剑·紫）
    "冰川龙·霜牙":  "eq_shuang_ya_bing_ren",      # Lv.84 霜牙冰刃（短刃·紫）
    "骨龙领主·骸王": "eq_hai_wang_gu_mian",       # Lv.92 骸王骨面（头盔·紫）
    "深渊骑士":     "eq_shen_yuan_ji_qiang",     # Lv.94 深渊骑枪（长枪·紫）
    "雷暴领主·雷霆": "eq_lei_ting_hu_jian",       # Lv.96 雷霆护肩（护甲·紫）
    "星龙·辰光":    "eq_chen_guang_fa_zhang",    # Lv.98 辰光法杖（法杖·紫）
}

# ================= 3. 宝箱开装备概率表（13 条） =================
# 结构：{宝箱类型: {"white": 白, "green": 绿, "blue": 蓝, "purple": 紫, "orange": 橙}}
# 未列出品质概率=0；装备等级=玩家等级±3 就近从名册抽取（方案 4.3/4.6）。
CHEST_EQUIP_RATE = {
    # ---- 副本房间宝箱（低/中/高级图；与金币材料互斥）----
    "room_low":   {"white": 0.30, "green": 0.10, "blue": 0.050, "purple": 0.0, "orange": 0.0},   # 木箱/铁箱/新手箱（Lv.1-20）
    "room_mid":   {"white": 0.20, "green": 0.20, "blue": 0.065, "purple": 0.0, "orange": 0.0},   # 白银箱/黄金箱（Lv.21-50）
    "room_high":  {"white": 0.10, "green": 0.25, "blue": 0.080, "purple": 0.0, "orange": 0.0},   # 秘银箱+（Lv.51+）
    # ---- 密室暗格宝箱（未中走原表）----
    "secret_normal": {"white": 0.0, "green": 0.0, "blue": 0.0, "purple": 0.10, "orange": 0.0},   # 普通密室：紫装 10%
    "secret_final":  {"white": 0.0, "green": 0.0, "blue": 0.0, "purple": 0.15, "orange": 0.0},   # 终局密室：紫装 15%
    # ---- 野外/事件箱 ----
    "poi_suspicious_package": {"white": 0.0, "green": 0.0, "blue": 0.03, "purple": 0.0, "orange": 0.0},  # 可疑包裹 POI：蓝装 3%（图纸 25%→22%）
    "event_treasure":         {"white": 0.0, "green": 0.0, "blue": 0.04, "purple": 0.0, "orange": 0.0},  # 探索事件 treasure：蓝装 4%
    "mystery_chest":          {"white": 0.0, "green": 0.0, "blue": 0.0, "purple": 0.06, "orange": 0.0},  # 彩蛋 mystery_chest：紫装 6%
    "trader_camp":            {"white": 0.0, "green": 0.02, "blue": 0.0, "purple": 0.0, "orange": 0.0},  # 行商营地：绿装 2%
    # ---- 垂钓档（宝物箱补 20% 白绿，7:3）----
    "fish_blue":   {"white": 0.14, "green": 0.06, "blue": 0.03, "purple": 0.0, "orange": 0.0},   # 垂钓·蓝档：蓝装 3%
    "fish_purple": {"white": 0.0, "green": 0.0, "blue": 0.0, "purple": 0.08, "orange": 0.0},     # 垂钓·紫档：紫装 8%
    "fish_gold":   {"white": 0.0, "green": 0.0, "blue": 0.0, "purple": 0.0, "orange": 0.05},     # 垂钓·金档：橙装 5%
    # ---- 传说宝箱（四来源：野王宝箱升级/隐藏任务/地图隐藏房/垂钓彩蛋）----
    # "gold": 0.10 为金档奖励档（金币/稀有材料，非装备品质），装备品质仅计入蓝/紫/橙
    "legend_chest": {"white": 0.0, "green": 0.0, "blue": 0.50, "purple": 0.25, "orange": 0.05, "gold": 0.10},
}

# ================= 聚合导出（v140 掉落逻辑统一入口） =================
DROP_ADD = {
    "BOSS_EQUIP_DROP":  BOSS_EQUIP_DROP,    # 22 副本 Boss → 专属装备
    "ELITE_EQUIP_DROP": ELITE_EQUIP_DROP,   # 18 野外精英 → 专属紫装
    "CHEST_EQUIP_RATE": CHEST_EQUIP_RATE,   # 13 宝箱类型 → 品质概率
}
