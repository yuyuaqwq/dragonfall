# -*- coding: utf-8 -*-
"""Phase 6 片段：职业套装 A（战士/法师/牧师 3 职业 × 3 阶段 × 5 部位 = 45 件）

命名 100% 取自 workspace/phase6_frags/naming_plan.json 的 class_sets：
- cls_zhan_shi（铁皮/精铁/百炼，req=str，武器 sword）
- cls_fa_shi  （学徒/符文/秘法，req=int，武器 staff）
- cls_mu_shi  （布衣/祝福/圣堂，req=int，武器 mace）

阶段等级：Ⅰ=10（blue）、Ⅱ=30（blue）、Ⅲ=50（purple）；
req：武器 lv-0，防具 lv-2~4（头盔/胸甲 lv-2、护腿 lv-4、战靴 lv-4）。
词条：武器用 attack 类、防具用 defense 类（AFFIXES 已存在 104 种）。
素材组（CLASS_SET_STAGES 同款）：
  Ⅰ: mat_lang_pi×6 + mat_ye_zhu_pi×5 + mat_shan_zei_hui_zhang×3
  Ⅱ: mat_shu_shi_he_xin×4 + mat_shou_ren_liao_ya×6 + mat_zuo_lang_quan_chi×4
  Ⅲ: mat_sheng_guang_jie_jing×5 + mat_yue_ying_zhi_pi×5 + mat_long_yan_jing_hua×3
（武器 mats 数量 ×2；紫装带 blueprint）
新增素材 5 个（items.py 缺失确认）：野猪皮/山贼徽章/鼠狮核心/月影之皮/龙焰精华。
MAT_DROP_MAP 5 条（供主 agent 挂 subareas 掉落）。
CLASS_SET_BONUS 9 条（职业套装专用，供 _SERIES_SET_BONUS 构建）。
本片段为纯数据声明（MERGE），不直接修改任何源文件。
"""

# ============================================================
# 1. EQUIP_ROSTER —— 45 件职业套装名册条目
# ============================================================
EQUIP_ROSTER = {
    # ---------------- 战士 · Ⅰ 铁皮（blue Lv.10，str） ----------------
    "eq_tiepichangjian": {"name": "铁皮长剑", "slot": "weapon", "weapon_type": "sword", "quality": "blue", "lv": 10, "series": "铁皮", "req": {"str": 10}, "source": "锻造"},
    "eq_tiepitoukui":    {"name": "铁皮头盔", "slot": "helm", "quality": "blue", "lv": 8, "series": "铁皮", "req": {"str": 8}, "source": "锻造"},
    "eq_tiepixiongjia":  {"name": "铁皮胸甲", "slot": "armor", "quality": "blue", "lv": 8, "series": "铁皮", "req": {"str": 8}, "source": "锻造"},
    "eq_tiepihutui":     {"name": "铁皮护腿", "slot": "legs", "quality": "blue", "lv": 6, "series": "铁皮", "req": {"str": 8}, "source": "锻造"},
    "eq_tiepizhanxue":   {"name": "铁皮战靴", "slot": "boots", "quality": "blue", "lv": 6, "series": "铁皮", "req": {"str": 6}, "source": "锻造"},
    # ---------------- 战士 · Ⅱ 精铁（blue Lv.30，str） ----------------
    "eq_jingtiezhanjian": {"name": "精铁战剑", "slot": "weapon", "weapon_type": "sword", "quality": "blue", "lv": 30, "series": "精铁", "req": {"str": 28}, "source": "锻造"},
    "eq_jingtietoukui":   {"name": "精铁头盔", "slot": "helm", "quality": "blue", "lv": 28, "series": "精铁", "req": {"str": 26}, "source": "锻造"},
    "eq_jingtiexiongjia": {"name": "精铁胸甲", "slot": "armor", "quality": "blue", "lv": 28, "series": "精铁", "req": {"str": 26}, "source": "锻造"},
    "eq_jingtiehutui":    {"name": "精铁护腿", "slot": "legs", "quality": "blue", "lv": 26, "series": "精铁", "req": {"str": 26}, "source": "锻造"},
    "eq_jingtiezhanxue":  {"name": "精铁战靴", "slot": "boots", "quality": "blue", "lv": 26, "series": "精铁", "req": {"str": 24}, "source": "锻造"},
    # ---------------- 战士 · Ⅲ 百炼（purple Lv.50，str） ----------------
    "eq_bailianchangjian": {"name": "百炼长剑", "slot": "weapon", "weapon_type": "sword", "quality": "purple", "lv": 50, "series": "百炼", "req": {"str": 48}, "source": "锻造"},
    "eq_bailiantoukui":    {"name": "百炼头盔", "slot": "helm", "quality": "purple", "lv": 48, "series": "百炼", "req": {"str": 46}, "source": "锻造"},
    "eq_bailianxiongjia":  {"name": "百炼胸甲", "slot": "armor", "quality": "purple", "lv": 48, "series": "百炼", "req": {"str": 46}, "source": "锻造"},
    "eq_bailianhutui":     {"name": "百炼护腿", "slot": "legs", "quality": "purple", "lv": 46, "series": "百炼", "req": {"str": 46}, "source": "锻造"},
    "eq_bailianzhanxue":   {"name": "百炼战靴", "slot": "boots", "quality": "purple", "lv": 46, "series": "百炼", "req": {"str": 44}, "source": "锻造"},
    # ---------------- 法师 · Ⅰ 学徒（blue Lv.10，int） ----------------
    "eq_jianxifazhang": {"name": "见习法杖", "slot": "weapon", "weapon_type": "staff", "quality": "blue", "lv": 10, "series": "学徒", "req": {"int": 10}, "source": "锻造"},
    "eq_xuetufamao":    {"name": "学徒法帽", "slot": "helm", "quality": "blue", "lv": 8, "series": "学徒", "req": {"int": 8}, "source": "锻造"},
    "eq_xuetuchangpao": {"name": "学徒长袍", "slot": "armor", "quality": "blue", "lv": 8, "series": "学徒", "req": {"int": 8}, "source": "锻造"},
    "eq_xuetuhutui":    {"name": "学徒护腿", "slot": "legs", "quality": "blue", "lv": 6, "series": "学徒", "req": {"int": 8}, "source": "锻造"},
    "eq_xuetufaxue":    {"name": "学徒法靴", "slot": "boots", "quality": "blue", "lv": 6, "series": "学徒", "req": {"int": 6}, "source": "锻造"},
    # ---------------- 法师 · Ⅱ 符文（blue Lv.30，int） ----------------
    "eq_fuwenfazhang": {"name": "符文法杖", "slot": "weapon", "weapon_type": "staff", "quality": "blue", "lv": 30, "series": "符文", "req": {"int": 28}, "source": "锻造"},
    "eq_fuwenfamao":   {"name": "符文法帽", "slot": "helm", "quality": "blue", "lv": 28, "series": "符文", "req": {"int": 26}, "source": "锻造"},
    "eq_fuwenchangpao": {"name": "符文长袍", "slot": "armor", "quality": "blue", "lv": 28, "series": "符文", "req": {"int": 26}, "source": "锻造"},
    "eq_fuwenhutui":   {"name": "符文护腿", "slot": "legs", "quality": "blue", "lv": 26, "series": "符文", "req": {"int": 26}, "source": "锻造"},
    "eq_fuwenfaxue":   {"name": "符文法靴", "slot": "boots", "quality": "blue", "lv": 26, "series": "符文", "req": {"int": 24}, "source": "锻造"},
    # ---------------- 法师 · Ⅲ 秘法（purple Lv.50，int） ----------------
    "eq_mifafazhang": {"name": "秘法法杖", "slot": "weapon", "weapon_type": "staff", "quality": "purple", "lv": 50, "series": "秘法", "req": {"int": 48}, "source": "锻造"},
    "eq_mifafamao":   {"name": "秘法法帽", "slot": "helm", "quality": "purple", "lv": 48, "series": "秘法", "req": {"int": 46}, "source": "锻造"},
    "eq_mifachangpao": {"name": "秘法长袍", "slot": "armor", "quality": "purple", "lv": 48, "series": "秘法", "req": {"int": 46}, "source": "锻造"},
    "eq_mifahutui":   {"name": "秘法护腿", "slot": "legs", "quality": "purple", "lv": 46, "series": "秘法", "req": {"int": 46}, "source": "锻造"},
    "eq_mifafaxue":   {"name": "秘法法靴", "slot": "boots", "quality": "purple", "lv": 46, "series": "秘法", "req": {"int": 44}, "source": "锻造"},
    # ---------------- 牧师 · Ⅰ 布衣（blue Lv.10，int） ----------------
    "eq_buyiquanzhang": {"name": "布衣权杖", "slot": "weapon", "weapon_type": "mace", "quality": "blue", "lv": 10, "series": "布衣", "req": {"int": 10}, "source": "锻造"},
    "eq_buyishengguan": {"name": "布衣圣冠", "slot": "helm", "quality": "blue", "lv": 8, "series": "布衣", "req": {"int": 8}, "source": "锻造"},
    "eq_buyifayi":      {"name": "布衣法衣", "slot": "armor", "quality": "blue", "lv": 8, "series": "布衣", "req": {"int": 8}, "source": "锻造"},
    "eq_buyihutui":     {"name": "布衣护腿", "slot": "legs", "quality": "blue", "lv": 6, "series": "布衣", "req": {"int": 8}, "source": "锻造"},
    "eq_buyishengxue":  {"name": "布衣圣靴", "slot": "boots", "quality": "blue", "lv": 6, "series": "布衣", "req": {"int": 6}, "source": "锻造"},
    # ---------------- 牧师 · Ⅱ 祝福（blue Lv.30，int） ----------------
    "eq_zhufuquanzhang": {"name": "祝福权杖", "slot": "weapon", "weapon_type": "mace", "quality": "blue", "lv": 30, "series": "祝福", "req": {"int": 28}, "source": "锻造"},
    "eq_zhufushengguan": {"name": "祝福圣冠", "slot": "helm", "quality": "blue", "lv": 28, "series": "祝福", "req": {"int": 26}, "source": "锻造"},
    "eq_zhufufayi":      {"name": "祝福法衣", "slot": "armor", "quality": "blue", "lv": 28, "series": "祝福", "req": {"int": 26}, "source": "锻造"},
    "eq_zhufuhutui":     {"name": "祝福护腿", "slot": "legs", "quality": "blue", "lv": 26, "series": "祝福", "req": {"int": 26}, "source": "锻造"},
    "eq_zhufushengxue":  {"name": "祝福圣靴", "slot": "boots", "quality": "blue", "lv": 26, "series": "祝福", "req": {"int": 24}, "source": "锻造"},
    # ---------------- 牧师 · Ⅲ 圣堂（purple Lv.50，int） ----------------
    "eq_shengtangquanzhang": {"name": "圣堂权杖", "slot": "weapon", "weapon_type": "mace", "quality": "purple", "lv": 50, "series": "圣堂", "req": {"int": 48}, "source": "锻造"},
    "eq_shengtangshengguan": {"name": "圣堂圣冠", "slot": "helm", "quality": "purple", "lv": 48, "series": "圣堂", "req": {"int": 46}, "source": "锻造"},
    "eq_shengtangfayi":      {"name": "圣堂法衣", "slot": "armor", "quality": "purple", "lv": 48, "series": "圣堂", "req": {"int": 46}, "source": "锻造"},
    "eq_shengtanghutui":     {"name": "圣堂护腿", "slot": "legs", "quality": "purple", "lv": 46, "series": "圣堂", "req": {"int": 46}, "source": "锻造"},
    "eq_shengtangshengxue":  {"name": "圣堂圣靴", "slot": "boots", "quality": "purple", "lv": 46, "series": "圣堂", "req": {"int": 44}, "source": "锻造"},
}

# ============================================================
# 2. SERIES_FIXED_AFFIX —— 45 件装备固定词条（武器 attack 类 / 防具 defense 类）
# ============================================================
SERIES_FIXED_AFFIX = {
    # 战士·铁皮（蓝装 1 词条）
    "铁皮长剑": ["armor_break"], "铁皮头盔": ["tenacity"], "铁皮胸甲": ["dmg_reduce"],
    "铁皮护腿": ["block"], "铁皮战靴": ["tenacity"],
    # 战士·精铁（蓝装 1-2 词条）
    "精铁战剑": ["charge", "armor_break"], "精铁头盔": ["dmg_reduce", "tenacity"],
    "精铁胸甲": ["block", "dmg_reduce"], "精铁护腿": ["tenacity", "dmg_reduce"],
    "精铁战靴": ["swift", "tenacity"],
    # 战士·百炼（紫装 2-3 词条）
    "百炼长剑": ["execute", "charge", "armor_break"], "百炼头盔": ["tenacity", "hp_up", "dmg_reduce"],
    "百炼胸甲": ["dmg_reduce", "block", "thorns"], "百炼护腿": ["tenacity", "dmg_reduce", "hp_up"],
    "百炼战靴": ["swift", "tenacity", "dmg_reduce"],
    # 法师·学徒（蓝装 1 词条）
    "见习法杖": ["element_thunder"], "学徒法帽": ["meditate"], "学徒长袍": ["dodge"],
    "学徒护腿": ["meditate"], "学徒法靴": ["swift"],
    # 法师·符文（蓝装 1-2 词条）
    "符文法杖": ["element_thunder", "crit_up"], "符文法帽": ["meditate", "tenacity"],
    "符文长袍": ["dodge", "magic_ward"], "符文护腿": ["meditate", "magic_ward"],
    "符文法靴": ["swift", "meditate"],
    # 法师·秘法（紫装 2-3 词条）
    "秘法法杖": ["element_thunder", "pene_magi", "crit_up"], "秘法法帽": ["meditate", "tenacity", "magic_ward"],
    "秘法长袍": ["magic_ward", "dodge", "regen"], "秘法护腿": ["meditate", "magic_ward", "tenacity"],
    "秘法法靴": ["swift", "meditate", "dodge"],
    # 牧师·布衣（蓝装 1 词条）
    "布衣权杖": ["purify"], "布衣圣冠": ["holy_echo"], "布衣法衣": ["heal_power"],
    "布衣护腿": ["holy_echo"], "布衣圣靴": ["swift"],
    # 牧师·祝福（蓝装 1-2 词条）
    "祝福权杖": ["purify", "meditate"], "祝福圣冠": ["holy_echo", "tenacity"],
    "祝福法衣": ["holy_echo", "magic_ward"], "祝福护腿": ["heal_power", "tenacity"],
    "祝福圣靴": ["swift", "meditate"],
    # 牧师·圣堂（紫装 2-3 词条）
    "圣堂权杖": ["purify", "divine_radiance", "meditate"], "圣堂圣冠": ["holy_echo", "tenacity", "magic_ward"],
    "圣堂法衣": ["holy_echo", "magic_ward", "regen"], "圣堂护腿": ["heal_power", "tenacity", "magic_ward"],
    "圣堂圣靴": ["swift", "meditate", "holy_echo"],
}

# ============================================================
# 3. SERIES_SETS —— 系列 → 套装名（9 条）
# ============================================================
SERIES_SETS = {
    "铁皮": "铁皮套", "精铁": "精铁套", "百炼": "百炼套",
    "学徒": "学徒套", "符文": "符文套", "秘法": "秘法套",
    "布衣": "布衣套", "祝福": "祝福套", "圣堂": "圣堂套",
}

# ============================================================
# 4. EQ_SERIES_THEME —— 系列主题文案（9 条）
# ============================================================
EQ_SERIES_THEME = {
    "铁皮": "铁匠铺学徒的第一炉铁，铁皮粗粝却硬朗，是战士踏上征途的起点",
    "精铁": "反复锻打提纯的精铁甲具，刃口映着火光，是铁壁军团的制式战备",
    "百炼": "百炼成钢的战士重装，每一道锤痕都是磨砺，剑锋所向无所畏惧",
    "学徒": "法师塔入门学徒的制式法袍，袖口还沾着墨迹，魔纹里藏着第一缕元素之光",
    "符文": "刻满古老符文的法袍与法杖，符文亮起时元素应召而来，研习已入正途",
    "秘法": "秘法研习者的巅峰之作，魔力在纹路间流转，举手投足皆是奥术的低语",
    "布衣": "教会为新手牧师缝制的朴素布衣，圣徽朴素，却已承载第一缕信仰之光",
    "祝福": "浸过祝福之泉的圣衣与权杖，祷言回响之处，伤者得以愈合",
    "圣堂": "圣堂大主教的圣器之装，圣辉流转不息，信仰坚定者可聆听神谕",
}

# ============================================================
# 5. MATERIALS —— 新增素材 5 个（items.py 缺失确认）
# ============================================================
MATERIALS = {
    "mat_ye_zhu_pi": {"price": 10, "name": "野猪皮", "type": "兽材",
        "desc": "野猪岭野猪的厚皮，粗糙坚韧，鞣制后是新手护甲的内衬"},
    "mat_shan_zei_hui_zhang": {"price": 12, "name": "山贼徽章", "type": "兽材",
        "desc": "山贼头目分发的铁皮徽章，敲碎能熔出一点铁料，铁匠铺照单全收"},
    "mat_shu_shi_he_xin": {"price": 35, "name": "鼠狮核心", "type": "兽材",
        "desc": "鼠狮兽胸口凝聚的魔核，蕴藏着不安分的野性魔力"},
    "mat_yue_ying_zhi_pi": {"price": 65, "name": "月影之皮", "type": "兽材",
        "desc": "月影林影豹的毛皮，月光下泛着银辉，是上等的法袍衬里"},
    "mat_long_yan_jing_hua": {"price": 80, "name": "龙焰精华", "type": "元素",
        "desc": "龙脊山脉龙焰淬炼出的火系精华，握在掌心能感到灼热的脉动"},
}

# ============================================================
# 6. MAT_DROP_MAP —— 新素材 → 产出地图/怪物（供主 agent 挂 drops）
# ============================================================
MAT_DROP_MAP = {
    "mat_ye_zhu_pi": "橡木平原·溪边草地 野猪 / 野猪岭·山脚 野猪",
    "mat_shan_zei_hui_zhang": "金穗平原·麦田区 盗贼 / 平原深处 盗贼头目·黑鸦",
    "mat_shu_shi_he_xin": "旧王陵·墓道 鼠狮兽（旧王陵副本 Lv.35 系）",
    "mat_yue_ying_zhi_pi": "月影林·影径 月影兽 / 月影深处 荧光狐",
    "mat_long_yan_jing_hua": "龙脊山脉·山道 石龙 / 龙巢口 龙崽",
}

# ============================================================
# 7. CLASS_SET_BONUS —— 职业套装套装效果（9 系列，供 _SERIES_SET_BONUS 构建）
#    格式：{"阶段系列名": {"class": "cls_xxx", "icon": "emoji", "quality": "blue|purple",
#          "bonus_2": {属性: 值}, "bonus_4_stats": {属性: 值},
#          "bonus_4": {"effect": "特效id", "chance": 0.3, "desc": "描述"}}}
#    特效 id 沿用 battle/affix_effects 已消费的先例（pierce/thunder/regen）。
# ============================================================
CLASS_SET_BONUS = {
    # 战士（钢铁壁垒风）：2件 atk/def+8%，4件 def+10% + 30%破甲
    "铁皮": {"class": "cls_zhan_shi", "icon": "🛡️", "quality": "blue",
             "bonus_2": {"atk": 0.08, "def": 0.08}, "bonus_4_stats": {"def": 0.10},
             "bonus_4": {"effect": "pierce", "chance": 0.3, "desc": "攻击 30% 概率破甲(敌方防御减半 2 回合)"}},
    "精铁": {"class": "cls_zhan_shi", "icon": "🛡️", "quality": "blue",
             "bonus_2": {"atk": 0.08, "def": 0.08}, "bonus_4_stats": {"def": 0.10},
             "bonus_4": {"effect": "pierce", "chance": 0.3, "desc": "攻击 30% 概率破甲(敌方防御减半 2 回合)"}},
    "百炼": {"class": "cls_zhan_shi", "icon": "⚔️", "quality": "purple",
             "bonus_2": {"atk": 0.08, "def": 0.08}, "bonus_4_stats": {"def": 0.10},
             "bonus_4": {"effect": "pierce", "chance": 0.3, "desc": "攻击 30% 概率破甲(敌方防御减半 2 回合)"}},
    # 法师（秘法研习风）：2件 matk+8%/cdr+5%，4件 matk+10% + 25%雷击
    "学徒": {"class": "cls_fa_shi", "icon": "🔮", "quality": "blue",
             "bonus_2": {"matk": 0.08, "cdr": 0.05}, "bonus_4_stats": {"matk": 0.10},
             "bonus_4": {"effect": "thunder", "chance": 0.25, "desc": "攻击 25% 概率追加一次雷击(60% 攻击伤害)"}},
    "符文": {"class": "cls_fa_shi", "icon": "🔮", "quality": "blue",
             "bonus_2": {"matk": 0.08, "cdr": 0.05}, "bonus_4_stats": {"matk": 0.10},
             "bonus_4": {"effect": "thunder", "chance": 0.25, "desc": "攻击 25% 概率追加一次雷击(60% 攻击伤害)"}},
    "秘法": {"class": "cls_fa_shi", "icon": "✨", "quality": "purple",
             "bonus_2": {"matk": 0.08, "cdr": 0.05}, "bonus_4_stats": {"matk": 0.10},
             "bonus_4": {"effect": "thunder", "chance": 0.25, "desc": "攻击 25% 概率追加一次雷击(60% 攻击伤害)"}},
    # 牧师（神圣信仰风）：2件 heal_power+8%/mdef+5%，4件 mdef+10% + 每回合回血
    "布衣": {"class": "cls_mu_shi", "icon": "☀️", "quality": "blue",
             "bonus_2": {"heal_power": 0.08, "mdef": 0.05}, "bonus_4_stats": {"mdef": 0.10},
             "bonus_4": {"effect": "regen", "chance": 1.0, "desc": "每回合开始回复 5% 生命"}},
    "祝福": {"class": "cls_mu_shi", "icon": "☀️", "quality": "blue",
             "bonus_2": {"heal_power": 0.08, "mdef": 0.05}, "bonus_4_stats": {"mdef": 0.10},
             "bonus_4": {"effect": "regen", "chance": 1.0, "desc": "每回合开始回复 5% 生命"}},
    "圣堂": {"class": "cls_mu_shi", "icon": "⛪", "quality": "purple",
             "bonus_2": {"heal_power": 0.08, "mdef": 0.05}, "bonus_4_stats": {"mdef": 0.10},
             "bonus_4": {"effect": "regen", "chance": 1.0, "desc": "每回合开始回复 5% 生命"}},
}

# ============================================================
# 8. CRAFT_RECIPES —— 45 条锻造配方
#    gold：蓝装 lv×9、紫装 lv×11；mats 武器 ×2；紫装带 blueprint
# ============================================================
CRAFT_RECIPES = {
    # ---------------- 战士 · 铁皮（Ⅰ 素材组） ----------------
    "rec_tiepichangjian": {"slot": "weapon", "quality": "blue", "lv": 10, "weapon_type": "sword",
        "mats": {"mat_lang_pi": 12, "mat_ye_zhu_pi": 10, "mat_shan_zei_hui_zhang": 6},
        "gold": 90, "desc": "铁匠铺第一炉铁皮战剑，硬朗可靠", "name": "铁皮长剑", "roster_id": "eq_tiepichangjian"},
    "rec_tiepitoukui": {"slot": "helm", "quality": "blue", "lv": 8,
        "mats": {"mat_lang_pi": 6, "mat_ye_zhu_pi": 5, "mat_shan_zei_hui_zhang": 3},
        "gold": 72, "desc": "铁皮铆接的头盔，护住要害", "name": "铁皮头盔", "roster_id": "eq_tiepitoukui"},
    "rec_tiepixiongjia": {"slot": "armor", "quality": "blue", "lv": 8,
        "mats": {"mat_lang_pi": 6, "mat_ye_zhu_pi": 5, "mat_shan_zei_hui_zhang": 3},
        "gold": 72, "desc": "铁皮缝制的胸甲，硬朗耐打", "name": "铁皮胸甲", "roster_id": "eq_tiepixiongjia"},
    "rec_tiepihutui": {"slot": "legs", "quality": "blue", "lv": 6,
        "mats": {"mat_lang_pi": 6, "mat_ye_zhu_pi": 5, "mat_shan_zei_hui_zhang": 3},
        "gold": 54, "desc": "铁皮护腿，膝盖处加厚耐磨", "name": "铁皮护腿", "roster_id": "eq_tiepihutui"},
    "rec_tiepizhanxue": {"slot": "boots", "quality": "blue", "lv": 6,
        "mats": {"mat_lang_pi": 6, "mat_ye_zhu_pi": 5, "mat_shan_zei_hui_zhang": 3},
        "gold": 54, "desc": "铁皮战靴，鞋底防滑耐走", "name": "铁皮战靴", "roster_id": "eq_tiepizhanxue"},
    # ---------------- 战士 · 精铁（Ⅱ 素材组） ----------------
    "rec_jingtiezhanjian": {"slot": "weapon", "quality": "blue", "lv": 30, "weapon_type": "sword",
        "mats": {"mat_shu_shi_he_xin": 8, "mat_shou_ren_liao_ya": 12, "mat_zuo_lang_quan_chi": 8},
        "gold": 270, "desc": "反复锻打的精铁战剑，刃口映着火光", "name": "精铁战剑", "roster_id": "eq_jingtiezhanjian"},
    "rec_jingtietoukui": {"slot": "helm", "quality": "blue", "lv": 28,
        "mats": {"mat_shu_shi_he_xin": 4, "mat_shou_ren_liao_ya": 6, "mat_zuo_lang_quan_chi": 4},
        "gold": 252, "desc": "精铁头盔，铁壁军团的制式战盔", "name": "精铁头盔", "roster_id": "eq_jingtietoukui"},
    "rec_jingtiexiongjia": {"slot": "armor", "quality": "blue", "lv": 28,
        "mats": {"mat_shu_shi_he_xin": 4, "mat_shou_ren_liao_ya": 6, "mat_zuo_lang_quan_chi": 4},
        "gold": 252, "desc": "精铁胸甲，厚实可靠", "name": "精铁胸甲", "roster_id": "eq_jingtiexiongjia"},
    "rec_jingtiehutui": {"slot": "legs", "quality": "blue", "lv": 26,
        "mats": {"mat_shu_shi_he_xin": 4, "mat_shou_ren_liao_ya": 6, "mat_zuo_lang_quan_chi": 4},
        "gold": 234, "desc": "精铁护腿，久战不疲", "name": "精铁护腿", "roster_id": "eq_jingtiehutui"},
    "rec_jingtiezhanxue": {"slot": "boots", "quality": "blue", "lv": 26,
        "mats": {"mat_shu_shi_he_xin": 4, "mat_shou_ren_liao_ya": 6, "mat_zuo_lang_quan_chi": 4},
        "gold": 234, "desc": "精铁战靴，步履沉稳", "name": "精铁战靴", "roster_id": "eq_jingtiezhanxue"},
    # ---------------- 战士 · 百炼（Ⅲ 素材组，紫装） ----------------
    "rec_bailianchangjian": {"slot": "weapon", "quality": "purple", "lv": 50, "weapon_type": "sword",
        "mats": {"mat_sheng_guang_jie_jing": 10, "mat_yue_ying_zhi_pi": 10, "mat_long_yan_jing_hua": 6},
        "gold": 550, "desc": "百炼成钢的战士重剑", "name": "百炼长剑", "roster_id": "eq_bailianchangjian",
        "blueprint": "百炼长剑图纸"},
    "rec_bailiantoukui": {"slot": "helm", "quality": "purple", "lv": 48,
        "mats": {"mat_sheng_guang_jie_jing": 5, "mat_yue_ying_zhi_pi": 5, "mat_long_yan_jing_hua": 3},
        "gold": 528, "desc": "百炼头盔，剑锋所向无所畏惧", "name": "百炼头盔", "roster_id": "eq_bailiantoukui",
        "blueprint": "百炼头盔图纸"},
    "rec_bailianxiongjia": {"slot": "armor", "quality": "purple", "lv": 48,
        "mats": {"mat_sheng_guang_jie_jing": 5, "mat_yue_ying_zhi_pi": 5, "mat_long_yan_jing_hua": 3},
        "gold": 528, "desc": "百炼胸甲，每一道锤痕都是磨砺", "name": "百炼胸甲", "roster_id": "eq_bailianxiongjia",
        "blueprint": "百炼胸甲图纸"},
    "rec_bailianhutui": {"slot": "legs", "quality": "purple", "lv": 46,
        "mats": {"mat_sheng_guang_jie_jing": 5, "mat_yue_ying_zhi_pi": 5, "mat_long_yan_jing_hua": 3},
        "gold": 506, "desc": "百炼护腿，重装之下步履如磐", "name": "百炼护腿", "roster_id": "eq_bailianhutui",
        "blueprint": "百炼护腿图纸"},
    "rec_bailianzhanxue": {"slot": "boots", "quality": "purple", "lv": 46,
        "mats": {"mat_sheng_guang_jie_jing": 5, "mat_yue_ying_zhi_pi": 5, "mat_long_yan_jing_hua": 3},
        "gold": 506, "desc": "百炼战靴，踏遍山河", "name": "百炼战靴", "roster_id": "eq_bailianzhanxue",
        "blueprint": "百炼战靴图纸"},
    # ---------------- 法师 · 学徒（Ⅰ 素材组） ----------------
    "rec_jianxifazhang": {"slot": "weapon", "quality": "blue", "lv": 10, "weapon_type": "staff",
        "mats": {"mat_lang_pi": 12, "mat_ye_zhu_pi": 10, "mat_shan_zei_hui_zhang": 6},
        "gold": 90, "desc": "法师塔发下的见习法杖，杖身刻着入门魔纹", "name": "见习法杖", "roster_id": "eq_jianxifazhang"},
    "rec_xuetufamao": {"slot": "helm", "quality": "blue", "lv": 8,
        "mats": {"mat_lang_pi": 6, "mat_ye_zhu_pi": 5, "mat_shan_zei_hui_zhang": 3},
        "gold": 72, "desc": "学徒法帽，缀着第一枚元素徽章", "name": "学徒法帽", "roster_id": "eq_xuetufamao"},
    "rec_xuetuchangpao": {"slot": "armor", "quality": "blue", "lv": 8,
        "mats": {"mat_lang_pi": 6, "mat_ye_zhu_pi": 5, "mat_shan_zei_hui_zhang": 3},
        "gold": 72, "desc": "学徒长袍，袖口还沾着墨迹", "name": "学徒长袍", "roster_id": "eq_xuetuchangpao"},
    "rec_xuetuhutui": {"slot": "legs", "quality": "blue", "lv": 6,
        "mats": {"mat_lang_pi": 6, "mat_ye_zhu_pi": 5, "mat_shan_zei_hui_zhang": 3},
        "gold": 54, "desc": "学徒护腿，方便在塔里奔走", "name": "学徒护腿", "roster_id": "eq_xuetuhutui"},
    "rec_xuetufaxue": {"slot": "boots", "quality": "blue", "lv": 6,
        "mats": {"mat_lang_pi": 6, "mat_ye_zhu_pi": 5, "mat_shan_zei_hui_zhang": 3},
        "gold": 54, "desc": "学徒法靴，轻便跟脚", "name": "学徒法靴", "roster_id": "eq_xuetufaxue"},
    # ---------------- 法师 · 符文（Ⅱ 素材组） ----------------
    "rec_fuwenfazhang": {"slot": "weapon", "quality": "blue", "lv": 30, "weapon_type": "staff",
        "mats": {"mat_shu_shi_he_xin": 8, "mat_shou_ren_liao_ya": 12, "mat_zuo_lang_quan_chi": 8},
        "gold": 270, "desc": "刻满古老符文的法杖，元素应召而来", "name": "符文法杖", "roster_id": "eq_fuwenfazhang"},
    "rec_fuwenfamao": {"slot": "helm", "quality": "blue", "lv": 28,
        "mats": {"mat_shu_shi_he_xin": 4, "mat_shou_ren_liao_ya": 6, "mat_zuo_lang_quan_chi": 4},
        "gold": 252, "desc": "符文法帽，符文亮起时魔力汇聚", "name": "符文法帽", "roster_id": "eq_fuwenfamao"},
    "rec_fuwenchangpao": {"slot": "armor", "quality": "blue", "lv": 28,
        "mats": {"mat_shu_shi_he_xin": 4, "mat_shou_ren_liao_ya": 6, "mat_zuo_lang_quan_chi": 4},
        "gold": 252, "desc": "符文长袍，研习已入正途", "name": "符文长袍", "roster_id": "eq_fuwenchangpao"},
    "rec_fuwenhutui": {"slot": "legs", "quality": "blue", "lv": 26,
        "mats": {"mat_shu_shi_he_xin": 4, "mat_shou_ren_liao_ya": 6, "mat_zuo_lang_quan_chi": 4},
        "gold": 234, "desc": "符文护腿，纹路间魔力流转", "name": "符文护腿", "roster_id": "eq_fuwenhutui"},
    "rec_fuwenfaxue": {"slot": "boots", "quality": "blue", "lv": 26,
        "mats": {"mat_shu_shi_he_xin": 4, "mat_shou_ren_liao_ya": 6, "mat_zuo_lang_quan_chi": 4},
        "gold": 234, "desc": "符文法靴，步履轻盈", "name": "符文法靴", "roster_id": "eq_fuwenfaxue"},
    # ---------------- 法师 · 秘法（Ⅲ 素材组，紫装） ----------------
    "rec_mifafazhang": {"slot": "weapon", "quality": "purple", "lv": 50, "weapon_type": "staff",
        "mats": {"mat_sheng_guang_jie_jing": 10, "mat_yue_ying_zhi_pi": 10, "mat_long_yan_jing_hua": 6},
        "gold": 550, "desc": "秘法研习者的巅峰法杖", "name": "秘法法杖", "roster_id": "eq_mifafazhang",
        "blueprint": "秘法法杖图纸"},
    "rec_mifafamao": {"slot": "helm", "quality": "purple", "lv": 48,
        "mats": {"mat_sheng_guang_jie_jing": 5, "mat_yue_ying_zhi_pi": 5, "mat_long_yan_jing_hua": 3},
        "gold": 528, "desc": "秘法法帽，奥术的低语在耳边回响", "name": "秘法法帽", "roster_id": "eq_mifafamao",
        "blueprint": "秘法法帽图纸"},
    "rec_mifachangpao": {"slot": "armor", "quality": "purple", "lv": 48,
        "mats": {"mat_sheng_guang_jie_jing": 5, "mat_yue_ying_zhi_pi": 5, "mat_long_yan_jing_hua": 3},
        "gold": 528, "desc": "秘法长袍，魔力在纹路间流转", "name": "秘法长袍", "roster_id": "eq_mifachangpao",
        "blueprint": "秘法长袍图纸"},
    "rec_mifahutui": {"slot": "legs", "quality": "purple", "lv": 46,
        "mats": {"mat_sheng_guang_jie_jing": 5, "mat_yue_ying_zhi_pi": 5, "mat_long_yan_jing_hua": 3},
        "gold": 506, "desc": "秘法护腿，举手投足皆是奥术", "name": "秘法护腿", "roster_id": "eq_mifahutui",
        "blueprint": "秘法护腿图纸"},
    "rec_mifafaxue": {"slot": "boots", "quality": "purple", "lv": 46,
        "mats": {"mat_sheng_guang_jie_jing": 5, "mat_yue_ying_zhi_pi": 5, "mat_long_yan_jing_hua": 3},
        "gold": 506, "desc": "秘法法靴，踏着元素而行", "name": "秘法法靴", "roster_id": "eq_mifafaxue",
        "blueprint": "秘法法靴图纸"},
    # ---------------- 牧师 · 布衣（Ⅰ 素材组） ----------------
    "rec_buyiquanzhang": {"slot": "weapon", "quality": "blue", "lv": 10, "weapon_type": "mace",
        "mats": {"mat_lang_pi": 12, "mat_ye_zhu_pi": 10, "mat_shan_zei_hui_zhang": 6},
        "gold": 90, "desc": "教会为新手牧师祝福过的权杖", "name": "布衣权杖", "roster_id": "eq_buyiquanzhang"},
    "rec_buyishengguan": {"slot": "helm", "quality": "blue", "lv": 8,
        "mats": {"mat_lang_pi": 6, "mat_ye_zhu_pi": 5, "mat_shan_zei_hui_zhang": 3},
        "gold": 72, "desc": "布衣圣冠，圣徽朴素却郑重", "name": "布衣圣冠", "roster_id": "eq_buyishengguan"},
    "rec_buyifayi": {"slot": "armor", "quality": "blue", "lv": 8,
        "mats": {"mat_lang_pi": 6, "mat_ye_zhu_pi": 5, "mat_shan_zei_hui_zhang": 3},
        "gold": 72, "desc": "布衣法衣，承载着第一缕信仰之光", "name": "布衣法衣", "roster_id": "eq_buyifayi"},
    "rec_buyihutui": {"slot": "legs", "quality": "blue", "lv": 6,
        "mats": {"mat_lang_pi": 6, "mat_ye_zhu_pi": 5, "mat_shan_zei_hui_zhang": 3},
        "gold": 54, "desc": "布衣护腿，行走四方", "name": "布衣护腿", "roster_id": "eq_buyihutui"},
    "rec_buyishengxue": {"slot": "boots", "quality": "blue", "lv": 6,
        "mats": {"mat_lang_pi": 6, "mat_ye_zhu_pi": 5, "mat_shan_zei_hui_zhang": 3},
        "gold": 54, "desc": "布衣圣靴，传道之路始于足下", "name": "布衣圣靴", "roster_id": "eq_buyishengxue"},
    # ---------------- 牧师 · 祝福（Ⅱ 素材组） ----------------
    "rec_zhufuquanzhang": {"slot": "weapon", "quality": "blue", "lv": 30, "weapon_type": "mace",
        "mats": {"mat_shu_shi_he_xin": 8, "mat_shou_ren_liao_ya": 12, "mat_zuo_lang_quan_chi": 8},
        "gold": 270, "desc": "浸过祝福之泉的权杖，祷言回响", "name": "祝福权杖", "roster_id": "eq_zhufuquanzhang"},
    "rec_zhufushengguan": {"slot": "helm", "quality": "blue", "lv": 28,
        "mats": {"mat_shu_shi_he_xin": 4, "mat_shou_ren_liao_ya": 6, "mat_zuo_lang_quan_chi": 4},
        "gold": 252, "desc": "祝福圣冠，圣辉温润", "name": "祝福圣冠", "roster_id": "eq_zhufushengguan"},
    "rec_zhufufayi": {"slot": "armor", "quality": "blue", "lv": 28,
        "mats": {"mat_shu_shi_he_xin": 4, "mat_shou_ren_liao_ya": 6, "mat_zuo_lang_quan_chi": 4},
        "gold": 252, "desc": "祝福法衣，伤者得以愈合", "name": "祝福法衣", "roster_id": "eq_zhufufayi"},
    "rec_zhufuhutui": {"slot": "legs", "quality": "blue", "lv": 26,
        "mats": {"mat_shu_shi_he_xin": 4, "mat_shou_ren_liao_ya": 6, "mat_zuo_lang_quan_chi": 4},
        "gold": 234, "desc": "祝福护腿，步履带着圣光", "name": "祝福护腿", "roster_id": "eq_zhufuhutui"},
    "rec_zhufushengxue": {"slot": "boots", "quality": "blue", "lv": 26,
        "mats": {"mat_shu_shi_he_xin": 4, "mat_shou_ren_liao_ya": 6, "mat_zuo_lang_quan_chi": 4},
        "gold": 234, "desc": "祝福圣靴，行善路远", "name": "祝福圣靴", "roster_id": "eq_zhufushengxue"},
    # ---------------- 牧师 · 圣堂（Ⅲ 素材组，紫装） ----------------
    "rec_shengtangquanzhang": {"slot": "weapon", "quality": "purple", "lv": 50, "weapon_type": "mace",
        "mats": {"mat_sheng_guang_jie_jing": 10, "mat_yue_ying_zhi_pi": 10, "mat_long_yan_jing_hua": 6},
        "gold": 550, "desc": "圣堂大主教的圣器权杖", "name": "圣堂权杖", "roster_id": "eq_shengtangquanzhang",
        "blueprint": "圣堂权杖图纸"},
    "rec_shengtangshengguan": {"slot": "helm", "quality": "purple", "lv": 48,
        "mats": {"mat_sheng_guang_jie_jing": 5, "mat_yue_ying_zhi_pi": 5, "mat_long_yan_jing_hua": 3},
        "gold": 528, "desc": "圣堂圣冠，圣辉流转不息", "name": "圣堂圣冠", "roster_id": "eq_shengtangshengguan",
        "blueprint": "圣堂圣冠图纸"},
    "rec_shengtangfayi": {"slot": "armor", "quality": "purple", "lv": 48,
        "mats": {"mat_sheng_guang_jie_jing": 5, "mat_yue_ying_zhi_pi": 5, "mat_long_yan_jing_hua": 3},
        "gold": 528, "desc": "圣堂法衣，信仰坚定者可聆听神谕", "name": "圣堂法衣", "roster_id": "eq_shengtangfayi",
        "blueprint": "圣堂法衣图纸"},
    "rec_shengtanghutui": {"slot": "legs", "quality": "purple", "lv": 46,
        "mats": {"mat_sheng_guang_jie_jing": 5, "mat_yue_ying_zhi_pi": 5, "mat_long_yan_jing_hua": 3},
        "gold": 506, "desc": "圣堂护腿，圣恩垂临", "name": "圣堂护腿", "roster_id": "eq_shengtanghutui",
        "blueprint": "圣堂护腿图纸"},
    "rec_shengtangshengxue": {"slot": "boots", "quality": "purple", "lv": 46,
        "mats": {"mat_sheng_guang_jie_jing": 5, "mat_yue_ying_zhi_pi": 5, "mat_long_yan_jing_hua": 3},
        "gold": 506, "desc": "圣堂圣靴，踏光而行", "name": "圣堂圣靴", "roster_id": "eq_shengtangshengxue",
        "blueprint": "圣堂圣靴图纸"},
}

# ============================================================
# MERGE —— 主 agent 合并指令（纯数据声明）
# ============================================================
MERGE = {
    "EQUIP_ROSTER": EQUIP_ROSTER,
    "SERIES_FIXED_AFFIX": SERIES_FIXED_AFFIX,
    "SERIES_SETS": SERIES_SETS,
    "EQ_SERIES_THEME": EQ_SERIES_THEME,
    "MATERIALS": MATERIALS,
    "CRAFT_RECIPES": CRAFT_RECIPES,
    "MAT_DROP_MAP": MAT_DROP_MAP,
    "CLASS_SET_BONUS": CLASS_SET_BONUS,
}

# ============================================================
# 自检（仅 __main__ 运行，不污染导入）
# ============================================================
if __name__ == "__main__":
    import json
    import pathlib

    _base = pathlib.Path(__file__).resolve().parents[3]  # ../../../../（workspace/phase6_frags → 插件根）
    _np_path = pathlib.Path(__file__).resolve().parent / "naming_plan.json"
    _np = json.loads(_np_path.read_text(encoding="utf-8"))
    _cs = _np["class_sets"]
    _mine = set()
    for _cls in ("cls_zhan_shi", "cls_fa_shi", "cls_mu_shi"):
        for _st, _info in _cs[_cls].items():
            _mine.add(_info["w"])
            _mine.update(_info["parts"])

    print("EQUIP_ROSTER:", len(EQUIP_ROSTER))
    print("SERIES_FIXED_AFFIX:", len(SERIES_FIXED_AFFIX))
    print("SERIES_SETS:", len(SERIES_SETS))
    print("EQ_SERIES_THEME:", len(EQ_SERIES_THEME))
    print("MATERIALS:", len(MATERIALS))
    print("CRAFT_RECIPES:", len(CRAFT_RECIPES))
    print("MAT_DROP_MAP:", len(MAT_DROP_MAP))
    print("CLASS_SET_BONUS:", len(CLASS_SET_BONUS))

    _roster_names = {e["name"] for e in EQUIP_ROSTER.values()}
    assert len(EQUIP_ROSTER) == 45, "EQUIP_ROSTER 应为 45 条"
    assert len({e["name"] for e in EQUIP_ROSTER.values()}) == 45, "装备名重复"
    assert _roster_names == _mine, f"装备名与 naming_plan 不一致: {sorted(_mine ^ _roster_names)}"
    assert _roster_names.isdisjoint(_np["existing_names"]), "与 existing_names 撞名"
    assert set(SERIES_FIXED_AFFIX.keys()) == _roster_names, "SERIES_FIXED_AFFIX 名不匹配名册"
    assert set(CRAFT_RECIPES.keys()) == {f"rec_{eid.removeprefix('eq_')}" for eid in EQUIP_ROSTER.keys()}, "配方 id 不匹配"
    assert len(SERIES_SETS) == 9 and len(EQ_SERIES_THEME) == 9 and len(CLASS_SET_BONUS) == 9
    assert set(SERIES_SETS.keys()) == {"铁皮", "精铁", "百炼", "学徒", "符文", "秘法", "布衣", "祝福", "圣堂"}
    assert set(MAT_DROP_MAP.keys()) == set(MATERIALS.keys()), "MAT_DROP_MAP 与 MATERIALS 不匹配"
    for _eid, _e in EQUIP_ROSTER.items():
        _r = CRAFT_RECIPES["rec_" + _eid.removeprefix("eq_")]
        assert _r["roster_id"] == _eid, f"配方 roster_id 错: {_eid}"
        assert _r["name"] == _e["name"], f"配方名错: {_eid}"
    print("自检通过：45 名与 naming_plan 完全一致，配方/词条/套装/素材全匹配")
