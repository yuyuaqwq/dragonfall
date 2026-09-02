# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - shop.py（阶段四重写，2026-08-06）

商店体系（07 章 6.2 城镇特色 + 6.3 消耗品 + 13 章 2.1/2.2/3/4）：
- SHOP_SUBAREA_ITEMS：key = 子区域 ID（v101.25h 鱼鱼拍板：商店配货只挂子区域，不挂城镇）
- SHOP_WEAPONS：key = 城镇地图 ID，值 = (名字, 武器类型英文ID, 等级, 品质ID)
  武器名来自 10 章装备名册（商店可售的基础/进阶武器）
- SHOP_ITEMS（城镇级）已于 v101.28g 删除——商店要么关联 NPC 要么关联子区域，
  无"城镇级兜底配货"（鱼鱼拍板：这玩意直接删了）
"""

# v95.4 野外行商货物（游商·老马等 trade 型野外 NPC 在场时可用）
SHOP_WILD_TRADE = [
    "i_treat_s", "i_mana_s", "i_bread", "i_ale", "i_meat_skewer", "i_scroll_escape",
]

# ================= v101.25h 子区域独立配货（鱼鱼：草药铺不该卖吃的，按子区域配置） =================
# key = 子区域 ID，value = 该店专属货物（物品 ID 列表）。
# v101.28g：无城镇级兜底——所有 _at_shop 放行的子区域必须在此显式配货（47 处全覆盖审计）。
# 设计分工：药剂店(herb)→药水/药剂；酒馆旅店(tavern)→食物/饮品；集市商行(general)→卷轴/杂物/护符；
# 铁匠工坊(smith)→武器+锻造材料（is_smith 分支），可追加军需补给。
SHOP_SUBAREA_ITEMS = {
    "oak_town_5": ["i_treat_micro", "i_treat_light", "i_treat_s", "i_mana_s", "i_herb_juice", "i_bandage"],
    "oak_town_4": ["i_bread", "i_ale", "i_meat_skewer"],
    "oak_town_3": ["i_stone_upgrade"],
    "white_deer_6": ["i_treat_m", "i_mana_m", "i_treat_light", "i_herb_juice", "i_bandage", "i_salve_s", "i_salve_m", "i_antidote_pill", "i_flash_powder", "i_ironwall_salve"],
    "white_deer_5": ["i_ale", "i_meat_skewer", "i_stew", "i_deer_burger", "i_deer_cheese"],
    "white_deer_7": ["i_bread", "i_stew", "i_blessed_pastry", "i_mushroom_soup", "i_tree_honey", "i_fish_soup", "i_dragon_pepper"],
    "white_deer_8": ["i_stone_upgrade", "i_stone_refine"],
    "white_deer_3": ["i_stone_upgrade", "i_key_old_king"],
    "white_deer_4": ["i_holy_water", "i_holy_charm", "i_scroll_purify"],
    "ironharbor_5": ["i_ale", "i_dock_rum", "i_meat_skewer", "i_stew"],
    "ironharbor_6": ["i_scroll_escape", "i_stone_upgrade", "i_stone_refine", "it_glow_bait", "it_dough_bait", "it_blood_bait", "i_shuang_bei_jin_bi_fu", "i_fu_huo_yu_mao"],
    "ironharbor_8": ["i_meat_skewer", "i_stew", "i_scroll_teleport", "mat_yin_lin_yu", "mat_jin_li"],
    "ironharbor_4": ["i_scroll_teleport", "i_holy_charm", "i_stone_refine"],
    "ironharbor_9": ["i_stone_upgrade", "i_stone_refine", "i_stone_blessed"],
    "ironharbor_10": ["i_treat_s", "i_treat_m", "i_mana_s", "i_mana_m", "i_herb_juice", "i_bandage"],
    "silver_brook_3": ["i_bread", "i_ale", "i_meat_skewer"],
    "silver_brook_4": ["i_scroll_escape", "i_meat_skewer", "i_stew", "it_glow_bait", "it_dough_bait", "it_blood_bait"],
    "silver_brook_2": ["i_bread", "i_ale", "i_apple_wine"],
    "maple_village_4": ["i_bread", "i_ale", "i_scroll_escape", "i_elf_fruit"],
    "dawn_city_3": ["i_holy_water", "i_holy_charm", "i_scroll_purify", "i_key_crypt"],
    "dawn_city_5": ["i_treat_m", "i_treat_l", "i_mana_m", "i_mana_l", "i_str_potion", "i_def_potion", "i_spd_potion", "mat_kong_ping", "i_treat_strong", "i_moon_dew", "mat_mo_fa_fen_chen"],
    "ironshield_town_3": ["i_treat_m", "i_treat_l", "i_mana_m", "i_mana_l", "i_stew", "i_str_potion", "i_stone_upgrade", "i_key_trial"],
    "ironshield_town_2": ["i_treat_s", "i_mana_s", "i_bread", "i_ale"],
    "moon_gate_2": ["i_bread", "i_ale", "i_elf_fruit"],
    "moon_gate_3": ["i_scroll_escape", "i_meat_skewer", "i_elf_fruit"],
    "moon_court_3": ["i_bread", "i_ale", "i_elf_fruit", "i_treat_m", "i_mana_m", "i_key_moon"],
    "star_song_2": ["i_scroll_escape", "i_elf_fruit", "i_stew"],
    "star_song_3": ["i_bread", "i_ale", "i_elf_fruit"],
    "frost_horn_3": ["i_ale", "i_dwarf_liquor", "i_stew", "i_deer_burger"],
    "frost_horn_5": ["i_holy_water", "i_treat_holy"],
    "anvil_fort_2": ["i_dwarf_liquor", "i_stew", "i_elf_fruit", "i_treat_m"],
    "anvil_fort_3": ["i_dwarf_liquor", "i_stone_upgrade", "i_stone_refine", "i_stone_blessed"],
    "cold_ridge_1": ["i_treat_l", "i_mana_l", "i_treat_holy", "i_scroll_escape", "i_life_elixir", "i_salve_l", "i_holy_potion", "i_emergency_salve"],
    "cold_ridge_2": ["i_bread", "i_stew", "i_deer_burger"],
    "cold_ridge_3": ["i_treat_l", "i_mana_l", "i_scroll_escape", "i_stew"],
    "aurora_town_4": ["i_bread", "i_ale", "i_scroll_escape", "i_elf_fruit"],
    "dragon_pass_2": ["i_ale", "i_meat_skewer", "i_stew", "i_treat_m", "i_dragon_scale_potion"],
    "dragon_kin_3": ["i_ale", "i_meat_skewer", "i_elf_fruit"],
    "jade_port_2": ["i_scroll_teleport", "i_meat_skewer", "i_stew", "i_elf_fruit"],
    "jade_port_3": ["i_ale", "i_dwarf_liquor", "i_stew"],
    "shell_town_1": ["i_scroll_teleport", "i_meat_skewer", "i_stew", "i_treat_l"],
    "shell_town_2": ["i_meat_skewer", "i_stew", "i_scroll_teleport", "i_elf_fruit"],
    "shell_town_3": ["i_ale", "i_dwarf_liquor", "i_elf_fruit"],
    "nameless_harbor_2": ["i_dock_rum", "i_stew", "i_treat_l", "i_treat_holy", "mat_hai_shen_dao_wen"],
    "nameless_harbor_3": ["i_scroll_teleport", "i_meat_skewer", "i_stew", "i_dock_rum"],
    "pearl_city_2": ["i_treat_l", "i_mana_l", "i_treat_holy", "i_phoenix_tear"],
    "pearl_city_3": ["i_scroll_teleport", "i_holy_charm", "i_stone_refine", "i_stone_blessed"],
    "pearl_city_4": ["i_scroll_escape", "i_scroll_teleport", "i_holy_charm", "i_stone_upgrade"],
    "pearl_city_5": ["i_meat_skewer", "i_stew", "i_scroll_teleport"],
    "deep_tunnel_2": ["i_treat_l", "i_mana_l", "i_stew", "i_stone_upgrade"],
    "deep_tunnel_3": ["i_ale", "i_dwarf_liquor", "i_stew"],
    "under_market_1": ["i_scroll_escape", "i_stew", "i_meat_skewer", "i_key_gray_dwarf"],
    "under_market_2": ["i_scroll_teleport", "i_holy_charm", "i_stone_refine"],
    "under_market_3": ["i_ale", "i_dwarf_liquor", "i_stew"],
    "ember_camp_2": ["i_stew", "i_treat_l", "i_mana_l", "i_elf_fruit"],
    "ember_camp_1": ["i_treat_l", "i_mana_l", "i_treat_holy", "i_scroll_escape"],
    "ember_camp_4": ["i_treat_l", "i_mana_l", "i_treat_holy", "i_stew", "i_scroll_escape"],
    "wind_city_2": ["i_treat_l", "i_mana_l", "i_treat_holy", "i_life_spring", "i_phoenix_tear"],
}

SHOP_WEAPONS = {
    # 南境·橡木系列（10 章 4.1：白装新手武器）
    "oak_town": [
        ["铁剑", "sword", 2, "white"],
        ["猎弓", "bow", 2, "white"],
        ["学徒法杖", "staff", 2, "white"],
        ["橡木短棍", "mace", 2, "white"],
        ["布拳套", "fist", 2, "white"],  # #236: 拳师武器链
    ],
    "maple_village": [
        ["铁剑", "sword", 2, "white"],
        ["猎弓", "bow", 2, "white"],
        ["学徒法杖", "staff", 2, "white"],
    ],
    # 南境·白鹿城：进阶白装 + 蓝装
    "white_deer": [
        ["铁剑", "sword", 2, "white"],
        ["猎鹿弓", "bow", 6, "blue"],
        ["学徒之杖", "staff", 6, "blue"],
        ["橡木短棍", "mace", 2, "white"],
        ["皮革拳套", "fist", 6, "green"],  # #236: 拳师武器链
        # v101.28l #430：补 Lv.18 进阶蓝装（修复 Lv.17-27 南境武器断档）
        ["精铁长剑", "sword", 18, "blue"],
        ["硬木战弓", "bow", 18, "blue"],
        ["祈愿法杖", "staff", 18, "blue"],
        ["铁头战锤", "mace", 18, "blue"],
        ["厚皮拳套", "fist", 18, "blue"],
        # v101.30d #O44：游侠弓档补录 Lv.24（Lv.18→32 断档）
        ["猎风长弓", "bow", 24, "blue"],
    ],
    # 南境·铁港系列（10 章 4.2：海盗/水手风）
    "ironharbor": [
        ["弯刀", "sword", 14, "blue"],
        ["水手短刃", "dagger", 12, "blue"],
        ["海风长弓", "bow", 18, "purple"],
        ["铁指虎", "fist", 14, "blue"],  # #236: 拳师武器链
        # v101.28l #430：补 Lv.22 进阶蓝装（断档 Lv.17-27 上半段）
        ["水手弯刀", "sword", 22, "blue"],
        ["远洋长弓", "bow", 22, "blue"],
        # v104 M07 修复 P2：潮汐法杖(海神系列 Lv.58) 移出南境铁港(Lv.12-28) → 银铃杖 Lv.24 补杖档（铁港锻造坊配套银铃套）
        ["银铃杖", "staff", 24, "blue"],
        ["铁锚战锤", "mace", 22, "blue"],
        ["铁链拳套", "fist", 22, "blue"],
    ],
    "silver_brook": [
        ["弯刀", "sword", 14, "blue"],
        ["海风长弓", "bow", 18, "purple"],
    ],
    # 中域·圣光系列（10 章 4.3：王国/教会风）
    "dawn_city": [
        ["圣光长剑", "sword", 28, "blue"],
        ["晨曦法杖", "staff", 28, "blue"],
        ["王都长弓", "bow", 32, "purple"],
        ["圣殿战锤", "mace", 34, "purple"],
    ],
    "ironshield_town": [
        ["圣光长剑", "sword", 28, "blue"],
        ["晨曦法杖", "staff", 28, "blue"],
        # v101.30d #O44：游侠弓档补录 Lv.28（Lv.18→32 断档）
        ["疾风长弓", "bow", 28, "blue"],
    ],
    # 群岛（翡翠海）
    "jade_port": [
        # v104 M07 修复 P2：14-18 级南境武器错位进 Lv.35 翡翠港 → 换圣光系列 Lv.28-44（中域 Lv.25-55 段）
        ["圣光长剑", "sword", 28, "blue"],
        ["晨曦法杖", "staff", 28, "blue"],
        ["圣光猎弓", "bow", 38, "blue"],
        ["圣光战锤", "mace", 44, "blue"],
    ],
    "shell_town": [
        # v104 M07 修复 P2：12-18 级南境武器错位进 Lv.40 贝壳镇 → 换圣光系列 Lv.28-42（中域段）
        ["圣光长剑", "sword", 28, "blue"],
        ["圣光法杖", "staff", 40, "blue"],
        ["圣裁长剑", "sword", 42, "blue"],
    ],
    # 西境·月语系列（10 章 4.4：精灵风）
    "moon_gate": [
        ["月语长弓", "bow", 52, "purple"],
        ["银叶法杖", "staff", 52, "purple"],
        ["月光短刃", "dagger", 50, "purple"],
    ],
    "star_song": [
        ["月语长弓", "bow", 52, "purple"],
        ["银叶法杖", "staff", 52, "purple"],
    ],
    "moon_court": [
        ["月语长弓", "bow", 52, "purple"],
        ["银叶法杖", "staff", 52, "purple"],
        ["月光短刃", "dagger", 50, "purple"],
    ],
    # 无尽海
    "nameless_harbor": [
        # v104 M07 修复 P2：14-18 级南境武器错位进 Lv.55 无名港 → 换海神系列 Lv.58（无尽海 Lv.55-78 段）
        ["潮汐法杖", "staff", 58, "purple"],
        ["海神三叉戟", "mace", 58, "purple"],
    ],
    "pearl_city": [
        # v104 M07 修复 P2：18 级南境武器错位进 Lv.62 珍珠城 → 换海神三叉戟 Lv.58（无尽海段）
        ["海神三叉戟", "mace", 58, "purple"],
        ["银叶法杖", "staff", 52, "purple"],
    ],
    # 北境·霜狼系列（10 章 4.5：北境/矮人风）
    "frost_horn": [
        ["霜狼长剑", "sword", 65, "purple"],
        ["北风长弓", "bow", 65, "purple"],
        ["铁砧战锤", "mace", 68, "purple"],
    ],
    "anvil_fort": [
        ["铁砧战锤", "mace", 68, "purple"],
        ["霜狼长剑", "sword", 65, "purple"],
    ],
    "cold_ridge": [
        ["北风长弓", "bow", 65, "purple"],
        ["霜狼长剑", "sword", 65, "purple"],
    ],
    "aurora_town": [
        ["霜狼长剑", "sword", 65, "purple"],
        ["北风长弓", "bow", 65, "purple"],
    ],
    "deep_tunnel": [
        ["铁砧战锤", "mace", 68, "purple"],
    ],
    "under_market": [
        ["铁砧战锤", "mace", 68, "purple"],
        ["霜狼长剑", "sword", 65, "purple"],
    ],
    # 东境·龙脊系列（10 章 4.6：龙裔风）
    "dragon_pass": [
        ["龙脊大剑", "sword", 85, "purple"],
        ["龙语法杖", "staff", 85, "purple"],
    ],
    "dragon_kin": [
        ["龙脊大剑", "sword", 85, "purple"],
        ["龙语法杖", "staff", 85, "purple"],
    ],
    "ember_camp": [
        ["龙脊大剑", "sword", 85, "purple"],
        ["龙语法杖", "staff", 85, "purple"],
    ],
    "wind_city": [
        ["龙脊大剑", "sword", 85, "purple"],
        ["龙语法杖", "staff", 85, "purple"],
    ],
}

# v92 铁匠类商店材料：craft 场所（铁匠铺/锻造坊/军械/符文工坊等）卖武器+锻造材料+全套装备；
# v105 M09 P3-6：配货已 v101.25h 起挂子区域 SHOP_SUBAREA_ITEMS，军械铺可追加消耗品军需
#   （如坚盾军械铺 ironshield_town_3 配 6 种药水+炖菜，不再"不卖消耗品"）
# key = 城镇地图 ID（cur or area_id 回退），值 = 材料 ID 列表（MATERIALS 表）
SHOP_SMITH_MATERIALS = {
    # 南境（Lv.1-30）：橡木镇/白鹿城/铁港
    "oak_town": [           # 老铁铁匠铺
        "mat_tie_kuang_shi",  # 铁矿石 10
        "mat_shi_cai",        # 石材 5
        "mat_jing_tie",       # 精铁 30
        # v167 锻造基础料：粗铁/林语麻布/青橡木（v167_landing_spec 商店挂载表；杖/弓通用木料已由 青橡木 承接）
        "mat_cu_tie",         # 粗铁 5
        "mat_sen_lin_ya_ma_bu",  # 林语麻布 10
        "mat_qing_xiang_mu",  # 青橡木 10（原橡木杖杆/硬木弓胎合并料）
    ],
    "white_deer": [         # 鹿角铁匠铺
        "mat_tie_kuang_shi",  # 铁矿石 10
        "mat_jing_tie",       # 精铁 30
        "mat_mi_yin",         # 秘银 80
        # v167 锻造基础料：青铜/月光棉/精铁锭/林语麻布（v167_landing_spec 商店挂载表）
        "mat_qing_tong",      # 青铜 15
        "mat_yue_guang_mian",  # 月光棉 25
        "mat_jing_tie_ding",  # 精铁锭 45
        "mat_sen_lin_ya_ma_bu",  # 林语麻布 10
    ],
    "ironharbor": [         # 锻造坊
        # v101.25 #319：补铁矿石——挖掘拜师（矿工长巴尔金）要 5 铁矿石，
        # 玩家没挖掘技能挖不了矿（#318 闭环断裂），铁港城锻造坊直接卖矿解决死锁
        "mat_tie_kuang_shi",  # 铁矿石 10
        "mat_jing_tie",       # 精铁 30
        "mat_mi_yin",         # 秘银 80
        # v167 锻造基础料：银铃丝/韧皮革/猎火木/猎风之木/青铜（v167_landing_spec 商店挂载表）
        "mat_yin_ling_si",    # 银铃丝 45
        "mat_ren_pi_ge",      # 韧皮革 60
        "mat_lie_huo_mu",     # 猎火木 45
        "mat_lie_feng_zhi_mu",  # 猎风之木 80（原猎风弓胎合并料）
        "mat_qing_tong",      # 青铜 15
    ],
    # 中域（Lv.25-55）
    "ironshield_town": [    # 军械铺
        "mat_mi_yin",         # 秘银 80
        "mat_jing_jin",       # 精金
        # v167 锻造基础料：符文绸/硬皮革/钢锭（v167_landing_spec 商店挂载表）
        "mat_fu_wen_duan",    # 符文绸 95
        "mat_ying_zhi_ge",    # 硬皮革 95
        "mat_gang_tie_ding",  # 钢锭 95
    ],
    "dawn_city": [          # 炼金工坊（craft 但炼金除外走普通商店）
        # v167 锻造基础料：圣辉绒/影皮革/钢锭/灵木（v167_landing_spec 商店挂载表；灵木杖杆已并入通用木料 灵木）
        "mat_sheng_hui_rong",  # 圣辉绒 140
        "mat_ying_ying_ge",   # 影皮革 140
        "mat_gang_tie_ding",  # 钢锭 95
        "mat_ling_mu",        # 灵木 115（原灵木杖杆合并料）
    ],
    "anvil_fort": [         # 符文工坊
        "mat_jing_jin",       # 精金
        "mat_bing_jing",      # 冰晶
        # v167 锻造基础料：月华绸/精制革/黑铁锭（v167_landing_spec 商店挂载表）
        "mat_yue_hua_chou",   # 月华绸 190
        "mat_jing_zhi_ge",    # 精制革 190
        "mat_hei_tie_ding",   # 黑铁锭 160
    ],
}

# v93 铁匠类商店全套装备：key = 城镇地图 ID，值 = 装备名册 ID 列表（EQUIP_ROSTER）
SHOP_EQUIP = {
    "oak_town": [           # 橡木镇白装 6 件
        # v135 套装锻造专属：圣徽·誓约（新手保底 4 件）从商店下架，
        # 改为铁匠铺锻造获取（rec_shi_yue_* 配方）——锻造是凑齐套装的必经之路
        "eq_pi_jia",
        "eq_jiu_pi_xue",
        "eq_xiang_mu_hu_tui",
        "eq_mao_pi_mao",
        "eq_xiang_mu_jie_zhi",
        "eq_xiang_mu_xiang_lian",
    ],
    "white_deer": [         # 白鹿城绿装 6 件
        "eq_bai_lu_pi_mao",
        "eq_bai_lu_xiong_jia",
        "eq_bai_lu_hu_tui",
        "eq_bai_lu_pi_xue",
        "eq_bai_lu_zhi_jie",
        "eq_bai_lu_diao_zhu",
    ],
    # v135 套装锻造专属：银铃套 7 件从商店下架（原 ironharbor 铁港城锻造坊直售），
    # 改为锻造获取（rec_yin_ling_* 配方齐备，Lv.18-24）——锻造是凑齐套装的必经之路
    "ironharbor": [
        # v136 Phase6 审计 P1-4：渡口区域套过渡档（Lv20）商店直售
        "eq_du_kou_xiong_jia",
        "eq_du_kou_hu_tui",
        "eq_du_kou_zhi_xue",
    ],
    "jade_port": [          # 翡翠港·翡翠集市：翡翠套 5 件 + 巡林区域套过渡档（v136 审计 P1-4）
        "eq_fei_cui_pi_jia",
        "eq_fei_cui_hu_tui",
        "eq_fei_cui_tou_kui",
        "eq_fei_cui_zhan_xue",
        "eq_fei_cui_xiang_lian",
        "eq_xun_lin_xiong_jia",
        "eq_xun_lin_hu_tui",
        "eq_xun_lin_zhi_xue",
    ],
    "ironshield_town": [    # 铁盾镇军械铺：迷雾套 5 件
        "eq_mi_wu_hu_tui",
        "eq_mi_wu_dou_mao",
        "eq_mi_wu_xiong_jia",
        "eq_mi_wu_zhan_xue",
        "eq_mi_wu_xiang_lian",
    ],
}

# ================= 设施 kind 表（v125 设施判定数据下沉） =================
# key = 子区域 ID，value = 设施类别。base.py 的 _at_smith / _sa_shop_kind /
# _facility_hint 与 world.py 地图设施清单原用中文名关键词嗅探 + white_deer_8 特判，
# 现统一改读此表（由旧逻辑全量子区域枚举生成，行为逐项等价）：
#   smith   铁匠/锻造/军械/工坊/强化类（craft funcs 或旧关键词命中）
#   herb    草药/炼金类（alchemy funcs 或旧关键词命中，优先于 craft）
#   tavern  酒馆/旅店/客栈类（healer/heal funcs 或旧关键词命中）
#   cook    灶坊/烹饪/食铺/磨坊类（旧关键词命中）
#   general 集市/商行/码头/商店/杂货/补给/营地类（旧关键词命中）
#   misc    其他 shop=True 无关键词（拍卖行/渔港等）
#   enhance 强化坊（鹿角淬火坊 white_deer_8：强化/附魔可用但非铁匠铺，
#            _sa_shop_kind 消费端与 misc 等价——仅配货不挂武器）
# 未入表子区域由代码按 funcs 结构兜底（alchemy→herb / craft→smith / heal→tavern / shop→misc）
SUBAREA_KIND = {
    "anvil_fort_2": "tavern",
    "anvil_fort_3": "smith",
    "aurora_town_4": "tavern",
    "black_forest_4": "general",
    "cold_ridge_1": "general",
    "cold_ridge_2": "tavern",
    "cold_ridge_3": "general",
    "dawn_city_3": "tavern",
    "dawn_city_5": "herb",
    "deep_tunnel_2": "misc",
    "deep_tunnel_3": "tavern",
    "dragon_kin_3": "tavern",
    "dragon_pass_2": "tavern",
    "dwarf_long_gallery_5": "smith",
    "ember_camp_1": "general",
    "ember_camp_2": "tavern",
    "ember_camp_4": "general",
    "frost_horn_3": "tavern",
    "frost_horn_5": "tavern",
    "harbor_docks_1": "general",
    "ironharbor_4": "misc",
    "ironharbor_5": "tavern",
    "ironharbor_6": "general",
    "ironharbor_8": "general",
    "ironharbor_9": "smith",
    "ironharbor_10": "herb",
    "ironshield_town_2": "tavern",
    "ironshield_town_3": "smith",
    "jade_port_2": "general",
    "jade_port_3": "tavern",
    "jade_port_dock": "general",
    "maple_village_4": "tavern",
    "moon_court_3": "tavern",
    "moon_gate_2": "tavern",
    "moon_gate_3": "general",
    "nameless_harbor_2": "tavern",
    "nameless_harbor_3": "general",
    "oak_plain_5": "cook",
    "oak_town_3": "smith",
    "oak_town_4": "tavern",
    "oak_town_5": "herb",
    "pearl_city_2": "tavern",
    "pearl_city_3": "misc",
    "pearl_city_4": "general",
    "pearl_city_5": "misc",
    "shell_town_1": "general",
    "shell_town_2": "general",
    "shell_town_3": "tavern",
    "silver_brook_2": "cook",
    "silver_brook_3": "tavern",
    "silver_brook_4": "general",
    "star_song_2": "general",
    "star_song_3": "tavern",
    "under_market_1": "general",
    "under_market_2": "misc",
    "under_market_3": "tavern",
    "under_market_mouth": "general",
    "white_deer_3": "smith",
    "white_deer_4": "tavern",
    "white_deer_5": "tavern",
    "white_deer_6": "herb",
    "white_deer_7": "cook",
    "white_deer_8": "enhance",
    "wind_city_2": "tavern",
}
