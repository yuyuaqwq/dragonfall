# -*- coding: utf-8 -*-
"""Phase 6 片段：散装（5 资料片 × 12 件 = 60 件）

命名 100% 取自 workspace/phase6_frags/naming_plan.json 的 scatter_plan
（每组 12 件，含：名字 / slot / quality / lv / stats 词条建议 / 系列名）。

铁律落实：
- 散装不挂套装：名册条目不写 set 字段，SERIES_SETS 保持空 dict（系列名不进套装体系，
  参照 game/data/equip_roster.py:233 注释：新系列不进 SERIES_SETS，避免误入旧套装体系/legs 约束）。
- 品质/等级严格按 scatter_plan：green 低配 / blue 中配 / purple 高配 / orange 毕业。
- source 统一「图纸」（散装经锻造获得，参照现有夜行披风 source=图纸；紫/橙配方带 blueprint）。
- 词条：把 scatter_plan 的 stats dict 翻译成 SERIES_FIXED_AFFIX 词条 id 组合
  （spd→swift、dodge→dodge、atk→crit_up、matk→crit_up、crit→crit_up、heal_power→heal_power、
   mdef→magic_ward、def→phys_ward、cdr→cdr、precise→precise、hp→hp_up、reflect→thorns、
   element_fire→element_fire、element_ice→element_ice、element_thunder→element_thunder；
   全部 id 已在 AFFIXES 104 种中确认存在）。
- 固定词条不做 kind 过滤（名册固定词条不参与随机池 kind 过滤，见 drops.py:259 fixed_affixes 直取），
  但为防御部位全部选用 defense 类词条，避免生成时随机补足词条与固定词条冲突。
- 素材只用现有通用素材（不新增 MATERIALS，MAT_DROP_MAP 空）：
  铁矿石 mat_tie_kuang_shi / 精铁 mat_jing_tie / 秘银 mat_mi_yin / 精金 mat_jing_jin /
  狼皮 mat_lang_pi / 兽肉 mat_shou_rou / 羽毛 mat_yu_mao / 布料(棉) mat_yan_yang_mao /
  布料(麻) mat_yan_xi_lin / 冰晶 mat_bing_jing / 水晶 mat_shui_jing /
  魔法粉尘 mat_mo_fa_fen_chen / 淬火石 mat_qiang_hua_shi / 石材 mat_shi_cai
  （以上均已在 game/data/items.py MATERIALS 中确认存在）。
- 配方 gold ≈ lv×9（蓝）/ lv×11（紫）/ lv×13（橙），防具 mats 3-8 个，橙装加 blueprint。

本片段为纯数据声明（MERGE），不直接修改任何源文件。
"""

# ============================================================
# 1. EQUIP_ROSTER —— 60 件散装名册条目（5 资料片 × 12 件）
# ============================================================
EQUIP_ROSTER = {
    # ---------------- 资料片一：晨曦谷地（绿/蓝 过渡装，lv 8-16） ----------------
    "eq_lie_feng_pi_feng": {"name": "猎风披风", "slot": "armor", "quality": "blue", "lv": 12, "series": "猎风", "req": {"agi": 10}, "source": "图纸"},
    "eq_lie_feng_hu_tui": {"name": "猎风护腿", "slot": "legs", "quality": "blue", "lv": 12, "series": "猎风", "req": {"agi": 10}, "source": "图纸"},
    "eq_lie_feng_zhi_xue": {"name": "猎风之靴", "slot": "boots", "quality": "blue", "lv": 14, "series": "猎风", "req": {"agi": 12}, "source": "图纸"},
    "eq_chen_lu_jie_zhi": {"name": "晨露戒指", "slot": "ring", "quality": "blue", "lv": 10, "series": "晨露", "req": {"vit": 8}, "source": "图纸"},
    "eq_chen_lu_xiang_lian": {"name": "晨露项链", "slot": "necklace", "quality": "blue", "lv": 12, "series": "晨露", "req": {"vit": 10}, "source": "图纸"},
    "eq_lie_hu_dou_mao": {"name": "猎户兜帽", "slot": "helm", "quality": "blue", "lv": 14, "series": "猎户", "req": {"agi": 12}, "source": "图纸"},
    "eq_lie_hu_jia_ke": {"name": "猎户夹克", "slot": "armor", "quality": "blue", "lv": 16, "series": "猎户", "req": {"agi": 14}, "source": "图纸"},
    "eq_lie_hu_chang_xue": {"name": "猎户长靴", "slot": "boots", "quality": "blue", "lv": 14, "series": "猎户", "req": {"agi": 12}, "source": "图纸"},
    "eq_xiang_mu_fu_ji": {"name": "橡木符记", "slot": "necklace", "quality": "green", "lv": 8, "series": "橡木符记", "req": {}, "source": "图纸"},
    "eq_bai_lu_hu_fu": {"name": "白鹿护符", "slot": "ring", "quality": "green", "lv": 10, "series": "白鹿护符", "req": {}, "source": "图纸"},
    "eq_chun_cao_shou_huan": {"name": "春草手环", "slot": "ring", "quality": "green", "lv": 12, "series": "春草", "req": {}, "source": "图纸"},
    "eq_ye_ying_xiong_zhen": {"name": "夜莺胸针", "slot": "necklace", "quality": "blue", "lv": 16, "series": "夜莺", "req": {"agi": 14}, "source": "图纸"},
    # ---------------- 资料片二：铁港海疆（绿/蓝/紫，lv 18-34） ----------------
    "eq_chao_xi_zhi_huan": {"name": "潮汐之环", "slot": "ring", "quality": "blue", "lv": 22, "series": "潮汐", "req": {"int": 18}, "source": "图纸"},
    "eq_chao_xi_diao_zhui": {"name": "潮汐吊坠", "slot": "necklace", "quality": "blue", "lv": 24, "series": "潮汐", "req": {"int": 20}, "source": "图纸"},
    "eq_mao_lian_hu_wan": {"name": "锚链护腕", "slot": "ring", "quality": "blue", "lv": 22, "series": "锚链", "req": {"str": 18}, "source": "图纸"},
    "eq_chuan_zhang_de_wang_yuan_jing": {"name": "船长的望远镜", "slot": "necklace", "quality": "purple", "lv": 30, "series": "船长", "req": {"agi": 26}, "source": "图纸"},
    "eq_hai_dao_yan_zhao": {"name": "海盗眼罩", "slot": "helm", "quality": "blue", "lv": 26, "series": "海盗", "req": {"agi": 22}, "source": "图纸"},
    "eq_hang_hai_dou_peng": {"name": "航海斗篷", "slot": "armor", "quality": "blue", "lv": 28, "series": "航海", "req": {"agi": 24}, "source": "图纸"},
    "eq_shen_yuan_zhi_mao": {"name": "深渊之锚", "slot": "ring", "quality": "purple", "lv": 32, "series": "深渊之锚", "req": {"str": 28}, "source": "图纸"},
    "eq_deng_ta_zhi_guang": {"name": "灯塔之光", "slot": "necklace", "quality": "blue", "lv": 26, "series": "灯塔", "req": {"vit": 22}, "source": "图纸"},
    "eq_shui_shou_jie_jie_zhi": {"name": "水手结戒指", "slot": "ring", "quality": "green", "lv": 18, "series": "水手结", "req": {}, "source": "图纸"},
    "eq_chao_xi_zhi_xue": {"name": "潮汐之靴", "slot": "boots", "quality": "blue", "lv": 24, "series": "潮汐", "req": {"int": 20}, "source": "图纸"},
    "eq_tie_gang_hui_zhang": {"name": "铁港徽章", "slot": "necklace", "quality": "purple", "lv": 34, "series": "铁港徽章", "req": {"str": 30}, "source": "图纸"},
    "eq_chen_xi_zhi_jie": {"name": "晨曦之戒", "slot": "ring", "quality": "blue", "lv": 20, "series": "晨曦", "req": {"vit": 16}, "source": "图纸"},
    # ---------------- 资料片三：熔火深渊（蓝/紫，lv 36-52） ----------------
    "eq_rong_yan_hu_shou": {"name": "熔岩护手", "slot": "armor", "quality": "purple", "lv": 45, "series": "熔岩", "req": {"str": 42}, "source": "图纸"},
    "eq_rong_yan_hu_tui": {"name": "熔岩护腿", "slot": "legs", "quality": "purple", "lv": 45, "series": "熔岩", "req": {"str": 42}, "source": "图纸"},
    "eq_rong_yan_zhi_xue": {"name": "熔岩之靴", "slot": "boots", "quality": "purple", "lv": 43, "series": "熔岩", "req": {"str": 40}, "source": "图纸"},
    "eq_yue_ying_dou_peng": {"name": "月影斗篷", "slot": "armor", "quality": "purple", "lv": 48, "series": "月影", "req": {"agi": 44}, "source": "图纸"},
    "eq_xing_hui_jie_zhi": {"name": "星辉戒指", "slot": "ring", "quality": "purple", "lv": 50, "series": "星辉", "req": {"int": 46}, "source": "图纸"},
    "eq_xing_hui_diao_zhui": {"name": "星辉吊坠", "slot": "necklace", "quality": "purple", "lv": 52, "series": "星辉", "req": {"int": 48}, "source": "图纸"},
    "eq_fei_cui_zhi_xin": {"name": "翡翠之心", "slot": "necklace", "quality": "blue", "lv": 40, "series": "翡翠之心", "req": {"vit": 34}, "source": "图纸"},
    "eq_fei_cui_hu_fu": {"name": "翡翠护符", "slot": "ring", "quality": "blue", "lv": 38, "series": "翡翠护符", "req": {"vit": 32}, "source": "图纸"},
    "eq_ji_feng_hu_shou": {"name": "疾风护手", "slot": "armor", "quality": "blue", "lv": 36, "series": "疾风", "req": {"agi": 32}, "source": "图纸"},
    "eq_ji_feng_zhi_xue": {"name": "疾风之靴", "slot": "boots", "quality": "blue", "lv": 36, "series": "疾风", "req": {"agi": 32}, "source": "图纸"},
    "eq_yue_yu_zhi_jie": {"name": "月语之戒", "slot": "ring", "quality": "purple", "lv": 50, "series": "月语", "req": {"agi": 46}, "source": "图纸"},
    "eq_jing_ling_pi_feng": {"name": "精灵披风", "slot": "armor", "quality": "blue", "lv": 42, "series": "精灵", "req": {"agi": 38}, "source": "图纸"},
    # ---------------- 资料片四：霜角北境（蓝/紫，lv 52-70） ----------------
    "eq_shuang_jiao_zhan_huan": {"name": "霜角战环", "slot": "ring", "quality": "purple", "lv": 60, "series": "霜角", "req": {"str": 56}, "source": "图纸"},
    "eq_shuang_jiao_diao_zhui": {"name": "霜角吊坠", "slot": "necklace", "quality": "purple", "lv": 62, "series": "霜角", "req": {"str": 58}, "source": "图纸"},
    "eq_shuang_jiao_pi_feng": {"name": "霜角披风", "slot": "armor", "quality": "purple", "lv": 60, "series": "霜角", "req": {"str": 56}, "source": "图纸"},
    "eq_han_shuang_zhi_jie": {"name": "寒霜之戒", "slot": "ring", "quality": "blue", "lv": 55, "series": "寒霜", "req": {"int": 50}, "source": "图纸"},
    "eq_bei_feng_hu_fu": {"name": "北风护符", "slot": "necklace", "quality": "blue", "lv": 58, "series": "北风", "req": {"agi": 52}, "source": "图纸"},
    "eq_long_lin_shou_huan": {"name": "龙鳞手环", "slot": "ring", "quality": "purple", "lv": 68, "series": "龙鳞", "req": {"str": 64}, "source": "图纸"},
    "eq_long_ji_hui_ji": {"name": "龙脊徽记", "slot": "necklace", "quality": "purple", "lv": 70, "series": "龙脊徽记", "req": {"str": 66}, "source": "图纸"},
    "eq_lie_shou_dou_peng": {"name": "猎手斗篷", "slot": "armor", "quality": "blue", "lv": 56, "series": "猎手", "req": {"agi": 50}, "source": "图纸"},
    "eq_lie_shou_zhi_xue": {"name": "猎手之靴", "slot": "boots", "quality": "blue", "lv": 54, "series": "猎手", "req": {"agi": 48}, "source": "图纸"},
    "eq_tie_bi_hu_fu": {"name": "铁壁护符", "slot": "ring", "quality": "blue", "lv": 52, "series": "铁壁", "req": {"str": 46}, "source": "图纸"},
    "eq_xing_huo_jie_zhi": {"name": "星火戒指", "slot": "ring", "quality": "purple", "lv": 64, "series": "星火", "req": {"int": 60}, "source": "图纸"},
    "eq_cang_lang_zhi_zhua": {"name": "苍狼之爪", "slot": "ring", "quality": "purple", "lv": 66, "series": "苍狼", "req": {"str": 62}, "source": "图纸"},
    # ---------------- 资料片五：苍穹之巅（紫/橙 毕业装，lv 75-92） ----------------
    "eq_feng_bao_zhi_yan": {"name": "风暴之眼", "slot": "ring", "quality": "purple", "lv": 80, "series": "风暴", "req": {"int": 76}, "source": "图纸"},
    "eq_feng_bao_diao_zhui": {"name": "风暴吊坠", "slot": "necklace", "quality": "purple", "lv": 82, "series": "风暴", "req": {"int": 78}, "source": "图纸"},
    "eq_cang_qiong_zhi_yi": {"name": "苍穹之翼", "slot": "armor", "quality": "orange", "lv": 88, "series": "苍穹之翼", "req": {"agi": 84}, "source": "图纸"},
    "eq_cang_qiong_zhi_xue": {"name": "苍穹之靴", "slot": "boots", "quality": "orange", "lv": 86, "series": "苍穹之翼", "req": {"agi": 82}, "source": "图纸"},
    "eq_long_yi_hu_fu": {"name": "龙翼护符", "slot": "necklace", "quality": "purple", "lv": 84, "series": "龙翼", "req": {"str": 80}, "source": "图纸"},
    "eq_long_yi_jie_zhi": {"name": "龙翼戒指", "slot": "ring", "quality": "purple", "lv": 84, "series": "龙翼", "req": {"str": 80}, "source": "图纸"},
    "eq_tian_qiong_zhi_guan": {"name": "天穹之冠", "slot": "helm", "quality": "purple", "lv": 86, "series": "天穹", "req": {"int": 82}, "source": "图纸"},
    "eq_xing_guang_xiang_lian": {"name": "星光项链", "slot": "necklace", "quality": "purple", "lv": 80, "series": "星光", "req": {"vit": 74}, "source": "图纸"},
    "eq_feng_shen_zhi_huan": {"name": "风神之环", "slot": "ring", "quality": "orange", "lv": 92, "series": "风神", "req": {"agi": 88}, "source": "图纸"},
    "eq_lei_guang_hui_zhang": {"name": "雷光徽章", "slot": "necklace", "quality": "purple", "lv": 88, "series": "雷光", "req": {"int": 84}, "source": "图纸"},
    "eq_mi_yin_shou_zhuo": {"name": "秘银手镯", "slot": "ring", "quality": "blue", "lv": 75, "series": "秘银", "req": {"str": 70}, "source": "图纸"},
    "eq_shou_wang_zhe_hu_fu": {"name": "守望者护符", "slot": "necklace", "quality": "purple", "lv": 78, "series": "守望者", "req": {"str": 72}, "source": "图纸"},
}

# ============================================================
# 2. SERIES_FIXED_AFFIX —— 60 条固定词条（装备名 → 词条 id 列表）
#    词条 id 全部已在 AFFIXES（104 种）确认存在；散装系列均用防御类词条
# ============================================================
SERIES_FIXED_AFFIX = {
    # ---------------- 资料片一：晨曦谷地 ----------------
    "猎风披风": ["swift", "dodge"],
    "猎风护腿": ["swift"],
    "猎风之靴": ["swift"],
    "晨露戒指": ["hp_up"],
    "晨露项链": ["heal_power"],
    "猎户兜帽": ["dodge", "precise"],
    "猎户夹克": ["crit_up", "dodge"],
    "猎户长靴": ["swift"],
    "橡木符记": ["crit_up", "magic_ward"],
    "白鹿护符": ["crit_up"],
    "春草手环": ["magic_ward"],
    "夜莺胸针": ["swift", "crit_up"],
    # ---------------- 资料片二：铁港海疆 ----------------
    "潮汐之环": ["crit_up", "cdr"],
    "潮汐吊坠": ["crit_up"],
    "锚链护腕": ["phys_ward"],
    "船长的望远镜": ["crit_up", "precise"],
    "海盗眼罩": ["crit_up"],
    "航海斗篷": ["swift", "dodge"],
    "深渊之锚": ["crit_up", "phys_ward"],
    "灯塔之光": ["heal_power"],
    "水手结戒指": ["swift"],
    "潮汐之靴": ["crit_up", "swift"],
    "铁港徽章": ["phys_ward", "hp_up"],
    "晨曦之戒": ["heal_power", "magic_ward"],
    # ---------------- 资料片三：熔火深渊 ----------------
    "熔岩护手": ["element_fire", "thorns"],
    "熔岩护腿": ["crit_up", "element_fire"],
    "熔岩之靴": ["element_fire"],
    "月影斗篷": ["dodge", "swift"],
    "星辉戒指": ["crit_up"],
    "星辉吊坠": ["cdr"],
    "翡翠之心": ["hp_up", "magic_ward"],
    "翡翠护符": ["magic_ward"],
    "疾风护手": ["swift"],
    "疾风之靴": ["swift"],
    "月语之戒": ["crit_up", "swift"],
    "精灵披风": ["dodge"],
    # ---------------- 资料片四：霜角北境 ----------------
    "霜角战环": ["crit_up", "element_ice"],
    "霜角吊坠": ["phys_ward", "element_ice"],
    "霜角披风": ["magic_ward", "dodge"],
    "寒霜之戒": ["crit_up", "element_ice"],
    "北风护符": ["swift"],
    "龙鳞手环": ["phys_ward"],
    "龙脊徽记": ["crit_up", "element_thunder"],
    "猎手斗篷": ["precise", "dodge"],
    "猎手之靴": ["swift"],
    "铁壁护符": ["phys_ward"],
    "星火戒指": ["crit_up"],
    "苍狼之爪": ["crit_up"],
    # ---------------- 资料片五：苍穹之巅 ----------------
    "风暴之眼": ["crit_up", "cdr"],
    "风暴吊坠": ["crit_up", "element_thunder"],
    "苍穹之翼": ["swift", "dodge"],
    "苍穹之靴": ["swift"],
    "龙翼护符": ["phys_ward", "hp_up"],
    "龙翼戒指": ["crit_up"],
    "天穹之冠": ["crit_up"],
    "星光项链": ["heal_power", "magic_ward"],
    "风神之环": ["swift", "crit_up"],
    "雷光徽章": ["crit_up", "element_thunder"],
    "秘银手镯": ["phys_ward", "magic_ward"],
    "守望者护符": ["crit_up", "phys_ward"],
}

# ============================================================
# 3. SERIES_SETS —— 空 dict（散装不进套装体系！）
# ============================================================
SERIES_SETS = {}

# ============================================================
# 4. EQ_SERIES_THEME —— 43 个散装系列的主题文案（独特风味）
# ============================================================
EQ_SERIES_THEME = {
    # ---------------- 资料片一：晨曦谷地 ----------------
    "猎风": "猎风谷的猎手工艺，轻若流风，追得上林间最疾的野鹿",
    "晨露": "晨曦谷地草叶间的露珠凝成的饰物，温润里透着清晨的凉意",
    "猎户": "晨曦谷猎户世代相传的装备，皮料揉得软熟，刀痕里藏着山林的智慧",
    "橡木符记": "橡木镇老林里刻下的符记，木纹沉稳，庇护远行者一路平安",
    "白鹿护符": "白鹿之森猎人磨制的护符，鹿角形状，带着林间的灵气",
    "春草": "南境春草编织的环饰，青翠欲滴，生机在指间流转",
    "夜莺": "夜莺歇脚处的饰物，暗夜里的一线清鸣，灵巧而温柔",
    # ---------------- 资料片二：铁港海疆 ----------------
    "潮汐": "铁港船匠以潮汐起落的节律打制的器物，浸过咸涩的海风",
    "锚链": "铁港锚链淬火锻出的环饰，沉甸甸的分量，是水手的定心石",
    "船长": "老船长执掌航线的器物，镜片里映着海图与星光",
    "海盗": "铁港外海海盗的蒙眼器物，遮住一只眼，却看得更远",
    "航海": "远洋帆索与帆布缝制的斗篷，沾着盐粒与信天翁的痕迹",
    "深渊之锚": "沉入无光海沟的旧锚，锈迹里缠着深海的呜咽",
    "灯塔": "铁港灯塔长明的暖光，为夜航者守住最后一线归途",
    "水手结": "水手们打了一辈子的绳结，牢靠得像老伙计的承诺",
    "铁港徽章": "铁港商会与港务局共同铸的徽章，铆着铁的硬气",
    "晨曦": "铁港清晨第一缕光淬过的器物，带着雾气与金箔的色泽",
    # ---------------- 资料片三：熔火深渊 ----------------
    "熔岩": "熔火深渊岩缝里捞出的器物，余温未散，红得像地心之血",
    "月影": "深渊上空月光投下的影子织成的斗篷，虚实难辨",
    "星辉": "熔火深渊顶上能望见的星子，被锻进了指环与吊坠",
    "翡翠之心": "深渊边缘翡翠藤结出的心形宝石，藏着地脉的呼吸",
    "翡翠护符": "翡翠森林深层的守护符记，光泽温润，灵气内敛",
    "疾风": "熔火深渊回廊里的穿堂风，快得抓不住影子",
    "月语": "月语精灵在深渊裂隙边的低语，清冷而悠远",
    "精灵": "月语精灵织造的轻羽披风，沾着星尘与霜露",
    # ---------------- 资料片四：霜角北境 ----------------
    "霜角": "霜角堡以北的冻土上拣出的器物，霜花结在纹路里",
    "寒霜": "北境长冬凝成的寒霜之息，冷冽而纯粹",
    "北风": "北风隘口的猎手护符，被朔风打磨得光滑圆润",
    "龙鳞": "霜角山脉古龙蜕下的鳞片，坚硬得能挡住霜刃",
    "龙脊徽记": "龙脊山脊的古老徽记，刻痕里残留着龙威",
    "猎手": "北境猎手的实用工艺，保暖耐磨，风雪无阻",
    "铁壁": "北境铁壁堡的守御器物，厚实得像冻土下的磐石",
    "星火": "极夜尽头的一粒星火，微弱却灼热",
    "苍狼": "霜角狼群之王的爪牙，凶悍里带着雪原的孤傲",
    # ---------------- 资料片五：苍穹之巅 ----------------
    "风暴": "苍穹之巅雷云深处的造物，握在手里能听见闷雷滚动",
    "苍穹之翼": "云海之巅以流云与天风铸成的羽翼，轻得仿佛能乘风而起",
    "龙翼": "古龙展翅掠过苍穹时落下的鳞羽，带着高空的寒意",
    "天穹": "天穹圣殿的冠冕器物，辉光如正午天光般纯粹",
    "星光": "苍穹之巅的星光凝成的项链，璀璨如新生的星辰",
    "风神": "风神行走天际时遗落的环饰，握紧它就能追上狂风",
    "雷光": "雷云裂隙间的电光凝成的徽章，指尖能感到细密的酥麻",
    "秘银": "天穹工匠以秘银锻造的器物，银光流转，轻韧无比",
    "守望者": "苍穹守望者的护符，凝视过云海尽头每一场日出",
}

# ============================================================
# 5. MATERIALS —— 空 dict（散装全部复用现有素材，不新增）
# ============================================================
MATERIALS = {}

# ============================================================
# 6. CRAFT_RECIPES —— 60 条锻造配方
#    gold ≈ lv×9（蓝）/ lv×11（紫）/ lv×13（橙）；防具 mats 3-8 个；紫/橙带 blueprint
# ============================================================
CRAFT_RECIPES = {
    # ---------------- 资料片一：晨曦谷地 ----------------
    "rec_lie_feng_pi_feng": {"slot": "armor", "quality": "blue", "lv": 12,
        "mats": {"mat_lang_pi": 4, "mat_yu_mao": 3}, "gold": 108, "desc": "猎风谷猎手以狼皮与飞羽缝制的轻披风",
        "name": "猎风披风", "roster_id": "eq_lie_feng_pi_feng"},
    "rec_lie_feng_hu_tui": {"slot": "legs", "quality": "blue", "lv": 12,
        "mats": {"mat_lang_pi": 3, "mat_yan_xi_lin": 2}, "gold": 108, "desc": "轻便的猎风护腿，膝盖处加衬耐磨",
        "name": "猎风护腿", "roster_id": "eq_lie_feng_hu_tui"},
    "rec_lie_feng_zhi_xue": {"slot": "boots", "quality": "blue", "lv": 14,
        "mats": {"mat_lang_pi": 3, "mat_yan_yang_mao": 2}, "gold": 126, "desc": "猎风之靴，鞋底软韧，追猎无声",
        "name": "猎风之靴", "roster_id": "eq_lie_feng_zhi_xue"},
    "rec_chen_lu_jie_zhi": {"slot": "ring", "quality": "blue", "lv": 10,
        "mats": {"mat_tie_kuang_shi": 3, "mat_shui_jing": 2}, "gold": 90, "desc": "晨露凝成的戒指，温润清透",
        "name": "晨露戒指", "roster_id": "eq_chen_lu_jie_zhi"},
    "rec_chen_lu_xiang_lian": {"slot": "necklace", "quality": "blue", "lv": 12,
        "mats": {"mat_shui_jing": 3, "mat_tie_kuang_shi": 2}, "gold": 108, "desc": "晨露项链，链坠圆润如朝露",
        "name": "晨露项链", "roster_id": "eq_chen_lu_xiang_lian"},
    "rec_lie_hu_dou_mao": {"slot": "helm", "quality": "blue", "lv": 14,
        "mats": {"mat_lang_pi": 3, "mat_yu_mao": 3}, "gold": 126, "desc": "猎户兜帽，帽檐压低能遮住半张脸",
        "name": "猎户兜帽", "roster_id": "eq_lie_hu_dou_mao"},
    "rec_lie_hu_jia_ke": {"slot": "armor", "quality": "blue", "lv": 16,
        "mats": {"mat_lang_pi": 5, "mat_yan_xi_lin": 3}, "gold": 144, "desc": "猎户夹克，皮料揉得软熟贴身",
        "name": "猎户夹克", "roster_id": "eq_lie_hu_jia_ke"},
    "rec_lie_hu_chang_xue": {"slot": "boots", "quality": "blue", "lv": 14,
        "mats": {"mat_lang_pi": 3, "mat_tie_kuang_shi": 2}, "gold": 126, "desc": "猎户长靴，翻山越岭的踏实伴侣",
        "name": "猎户长靴", "roster_id": "eq_lie_hu_chang_xue"},
    "rec_xiang_mu_fu_ji": {"slot": "necklace", "quality": "green", "lv": 8,
        "mats": {"mat_yan_yang_mao": 2, "mat_tie_kuang_shi": 1}, "gold": 72, "desc": "橡木镇老林里的护身符记",
        "name": "橡木符记", "roster_id": "eq_xiang_mu_fu_ji"},
    "rec_bai_lu_hu_fu": {"slot": "ring", "quality": "green", "lv": 10,
        "mats": {"mat_shi_cai": 2, "mat_yu_mao": 2}, "gold": 90, "desc": "白鹿之森猎人磨制的鹿角护符",
        "name": "白鹿护符", "roster_id": "eq_bai_lu_hu_fu"},
    "rec_chun_cao_shou_huan": {"slot": "ring", "quality": "green", "lv": 12,
        "mats": {"mat_yan_yang_mao": 3, "mat_shui_jing": 1}, "gold": 108, "desc": "春草编结的手环，生机盎然",
        "name": "春草手环", "roster_id": "eq_chun_cao_shou_huan"},
    "rec_ye_ying_xiong_zhen": {"slot": "necklace", "quality": "blue", "lv": 16,
        "mats": {"mat_yu_mao": 4, "mat_shui_jing": 2}, "gold": 144, "desc": "夜莺胸针，暗夜里的清鸣",
        "name": "夜莺胸针", "roster_id": "eq_ye_ying_xiong_zhen"},
    # ---------------- 资料片二：铁港海疆 ----------------
    "rec_chao_xi_zhi_huan": {"slot": "ring", "quality": "blue", "lv": 22,
        "mats": {"mat_tie_kuang_shi": 4, "mat_shui_jing": 2}, "gold": 198, "desc": "铁港船匠按潮汐节律打制的戒指",
        "name": "潮汐之环", "roster_id": "eq_chao_xi_zhi_huan"},
    "rec_chao_xi_diao_zhui": {"slot": "necklace", "quality": "blue", "lv": 24,
        "mats": {"mat_shui_jing": 4, "mat_tie_kuang_shi": 2}, "gold": 216, "desc": "潮汐吊坠，坠子如浪花凝成",
        "name": "潮汐吊坠", "roster_id": "eq_chao_xi_diao_zhui"},
    "rec_mao_lian_hu_wan": {"slot": "ring", "quality": "blue", "lv": 22,
        "mats": {"mat_tie_kuang_shi": 4, "mat_jing_tie": 2}, "gold": 198, "desc": "锚链环扣锻出的腕环，沉甸结实",
        "name": "锚链护腕", "roster_id": "eq_mao_lian_hu_wan"},
    "rec_chuan_zhang_de_wang_yuan_jing": {"slot": "necklace", "quality": "purple", "lv": 30,
        "mats": {"mat_shui_jing": 3, "mat_jing_tie": 3, "mat_mo_fa_fen_chen": 2}, "gold": 330, "desc": "老船长的黄铜望远镜，镜片里映着海图与星光",
        "name": "船长的望远镜", "roster_id": "eq_chuan_zhang_de_wang_yuan_jing", "blueprint": "船长的望远镜图纸"},
    "rec_hai_dao_yan_zhao": {"slot": "helm", "quality": "blue", "lv": 26,
        "mats": {"mat_lang_pi": 4, "mat_tie_kuang_shi": 2}, "gold": 234, "desc": "海盗眼罩，遮住一只眼，看得更远",
        "name": "海盗眼罩", "roster_id": "eq_hai_dao_yan_zhao"},
    "rec_hang_hai_dou_peng": {"slot": "armor", "quality": "blue", "lv": 28,
        "mats": {"mat_yan_xi_lin": 5, "mat_lang_pi": 3}, "gold": 252, "desc": "帆布与麻线缝制的航海斗篷，沾着盐粒",
        "name": "航海斗篷", "roster_id": "eq_hang_hai_dou_peng"},
    "rec_shen_yuan_zhi_mao": {"slot": "ring", "quality": "purple", "lv": 32,
        "mats": {"mat_jing_tie": 3, "mat_tie_kuang_shi": 3, "mat_shui_jing": 2}, "gold": 352, "desc": "沉入无光海沟的旧锚锻成的重环",
        "name": "深渊之锚", "roster_id": "eq_shen_yuan_zhi_mao", "blueprint": "深渊之锚图纸"},
    "rec_deng_ta_zhi_guang": {"slot": "necklace", "quality": "blue", "lv": 26,
        "mats": {"mat_shui_jing": 4, "mat_mo_fa_fen_chen": 2}, "gold": 234, "desc": "灯塔长明的暖光凝成的吊坠",
        "name": "灯塔之光", "roster_id": "eq_deng_ta_zhi_guang"},
    "rec_shui_shou_jie_jie_zhi": {"slot": "ring", "quality": "green", "lv": 18,
        "mats": {"mat_yan_xi_lin": 3, "mat_tie_kuang_shi": 1}, "gold": 162, "desc": "水手绳结模样的朴素戒指",
        "name": "水手结戒指", "roster_id": "eq_shui_shou_jie_jie_zhi"},
    "rec_chao_xi_zhi_xue": {"slot": "boots", "quality": "blue", "lv": 24,
        "mats": {"mat_lang_pi": 3, "mat_shui_jing": 2, "mat_tie_kuang_shi": 2}, "gold": 216, "desc": "潮汐之靴，踏浪而行",
        "name": "潮汐之靴", "roster_id": "eq_chao_xi_zhi_xue"},
    "rec_tie_gang_hui_zhang": {"slot": "necklace", "quality": "purple", "lv": 34,
        "mats": {"mat_jing_tie": 3, "mat_tie_kuang_shi": 3, "mat_qiang_hua_shi": 2}, "gold": 374, "desc": "铁港商会与港务局共铸的徽章",
        "name": "铁港徽章", "roster_id": "eq_tie_gang_hui_zhang", "blueprint": "铁港徽章图纸"},
    "rec_chen_xi_zhi_jie": {"slot": "ring", "quality": "blue", "lv": 20,
        "mats": {"mat_shui_jing": 3, "mat_tie_kuang_shi": 2, "mat_mo_fa_fen_chen": 1}, "gold": 180, "desc": "铁港清晨第一缕光淬过的戒指",
        "name": "晨曦之戒", "roster_id": "eq_chen_xi_zhi_jie"},
    # ---------------- 资料片三：熔火深渊 ----------------
    "rec_rong_yan_hu_shou": {"slot": "armor", "quality": "purple", "lv": 45,
        "mats": {"mat_jing_tie": 2, "mat_shi_cai": 3, "mat_qiang_hua_shi": 3}, "gold": 495, "desc": "熔火深渊岩缝里捞出的护手，余温未散",
        "name": "熔岩护手", "roster_id": "eq_rong_yan_hu_shou", "blueprint": "熔岩护手图纸"},
    "rec_rong_yan_hu_tui": {"slot": "legs", "quality": "purple", "lv": 45,
        "mats": {"mat_jing_tie": 3, "mat_shi_cai": 3, "mat_qiang_hua_shi": 2}, "gold": 495, "desc": "熔岩护腿，红得像地心之血",
        "name": "熔岩护腿", "roster_id": "eq_rong_yan_hu_tui", "blueprint": "熔岩护腿图纸"},
    "rec_rong_yan_zhi_xue": {"slot": "boots", "quality": "purple", "lv": 43,
        "mats": {"mat_jing_tie": 3, "mat_shi_cai": 3, "mat_qiang_hua_shi": 2}, "gold": 473, "desc": "熔岩之靴，鞋底烙着地火的纹路",
        "name": "熔岩之靴", "roster_id": "eq_rong_yan_zhi_xue", "blueprint": "熔岩之靴图纸"},
    "rec_yue_ying_dou_peng": {"slot": "armor", "quality": "purple", "lv": 48,
        "mats": {"mat_yan_xi_lin": 1, "mat_lang_pi": 4, "mat_mo_fa_fen_chen": 3}, "gold": 528, "desc": "月影织成的斗篷，虚实难辨",
        "name": "月影斗篷", "roster_id": "eq_yue_ying_dou_peng", "blueprint": "月影斗篷图纸"},
    "rec_xing_hui_jie_zhi": {"slot": "ring", "quality": "purple", "lv": 50,
        "mats": {"mat_shui_jing": 2, "mat_jing_tie": 3, "mat_mo_fa_fen_chen": 3}, "gold": 550, "desc": "星子被锻进指环，流转着微光",
        "name": "星辉戒指", "roster_id": "eq_xing_hui_jie_zhi", "blueprint": "星辉戒指图纸"},
    "rec_xing_hui_diao_zhui": {"slot": "necklace", "quality": "purple", "lv": 52,
        "mats": {"mat_shui_jing": 2, "mat_jing_tie": 3, "mat_mo_fa_fen_chen": 3}, "gold": 572, "desc": "星辉吊坠，坠如星屑凝成",
        "name": "星辉吊坠", "roster_id": "eq_xing_hui_diao_zhui", "blueprint": "星辉吊坠图纸"},
    "rec_fei_cui_zhi_xin": {"slot": "necklace", "quality": "blue", "lv": 40,
        "mats": {"mat_shui_jing": 4, "mat_mo_fa_fen_chen": 3}, "gold": 360, "desc": "翡翠藤结出的心形宝石吊坠",
        "name": "翡翠之心", "roster_id": "eq_fei_cui_zhi_xin"},
    "rec_fei_cui_hu_fu": {"slot": "ring", "quality": "blue", "lv": 38,
        "mats": {"mat_shui_jing": 4, "mat_mo_fa_fen_chen": 2}, "gold": 342, "desc": "翡翠森林深处的守护符记",
        "name": "翡翠护符", "roster_id": "eq_fei_cui_hu_fu"},
    "rec_ji_feng_hu_shou": {"slot": "armor", "quality": "blue", "lv": 36,
        "mats": {"mat_lang_pi": 5, "mat_yu_mao": 3}, "gold": 324, "desc": "疾风护手，快得抓不住影子",
        "name": "疾风护手", "roster_id": "eq_ji_feng_hu_shou"},
    "rec_ji_feng_zhi_xue": {"slot": "boots", "quality": "blue", "lv": 36,
        "mats": {"mat_lang_pi": 4, "mat_yu_mao": 3}, "gold": 324, "desc": "疾风之靴，踏风而行",
        "name": "疾风之靴", "roster_id": "eq_ji_feng_zhi_xue"},
    "rec_yue_yu_zhi_jie": {"slot": "ring", "quality": "purple", "lv": 50,
        "mats": {"mat_shui_jing": 2, "mat_jing_tie": 3, "mat_mo_fa_fen_chen": 3}, "gold": 550, "desc": "月语精灵在深渊裂隙边的低语凝成的戒指",
        "name": "月语之戒", "roster_id": "eq_yue_yu_zhi_jie", "blueprint": "月语之戒图纸"},
    "rec_jing_ling_pi_feng": {"slot": "armor", "quality": "blue", "lv": 42,
        "mats": {"mat_yan_xi_lin": 4, "mat_yu_mao": 4}, "gold": 378, "desc": "月语精灵织造的轻羽披风",
        "name": "精灵披风", "roster_id": "eq_jing_ling_pi_feng"},
    # ---------------- 资料片四：霜角北境 ----------------
    "rec_shuang_jiao_zhan_huan": {"slot": "ring", "quality": "purple", "lv": 60,
        "mats": {"mat_jing_tie": 1, "mat_bing_jing": 4, "mat_qiang_hua_shi": 3}, "gold": 660, "desc": "霜角堡以北冻土上拣出的战环",
        "name": "霜角战环", "roster_id": "eq_shuang_jiao_zhan_huan", "blueprint": "霜角战环图纸"},
    "rec_shuang_jiao_diao_zhui": {"slot": "necklace", "quality": "purple", "lv": 62,
        "mats": {"mat_jing_tie": 1, "mat_bing_jing": 4, "mat_qiang_hua_shi": 3}, "gold": 682, "desc": "霜角吊坠，霜花结在纹路里",
        "name": "霜角吊坠", "roster_id": "eq_shuang_jiao_diao_zhui", "blueprint": "霜角吊坠图纸"},
    "rec_shuang_jiao_pi_feng": {"slot": "armor", "quality": "purple", "lv": 60,
        "mats": {"mat_lang_pi": 1, "mat_yan_xi_lin": 4, "mat_bing_jing": 3}, "gold": 660, "desc": "霜角披风，北风也灌不透的厚实",
        "name": "霜角披风", "roster_id": "eq_shuang_jiao_pi_feng", "blueprint": "霜角披风图纸"},
    "rec_han_shuang_zhi_jie": {"slot": "ring", "quality": "blue", "lv": 55,
        "mats": {"mat_bing_jing": 3, "mat_shui_jing": 3, "mat_mo_fa_fen_chen": 2}, "gold": 495, "desc": "长冬凝成的寒霜之戒，冷冽纯粹",
        "name": "寒霜之戒", "roster_id": "eq_han_shuang_zhi_jie"},
    "rec_bei_feng_hu_fu": {"slot": "necklace", "quality": "blue", "lv": 58,
        "mats": {"mat_bing_jing": 3, "mat_lang_pi": 3, "mat_yu_mao": 2}, "gold": 522, "desc": "北风隘口的猎手护符，被朔风打磨得圆润",
        "name": "北风护符", "roster_id": "eq_bei_feng_hu_fu"},
    "rec_long_lin_shou_huan": {"slot": "ring", "quality": "purple", "lv": 68,
        "mats": {"mat_jing_tie": 1, "mat_bing_jing": 4, "mat_qiang_hua_shi": 3}, "gold": 748, "desc": "古龙蜕鳞锻成的手环，坚硬如霜刃",
        "name": "龙鳞手环", "roster_id": "eq_long_lin_shou_huan", "blueprint": "龙鳞手环图纸"},
    "rec_long_ji_hui_ji": {"slot": "necklace", "quality": "purple", "lv": 70,
        "mats": {"mat_jing_tie": 1, "mat_bing_jing": 4, "mat_mo_fa_fen_chen": 3}, "gold": 770, "desc": "龙脊山脊的古老徽记，刻痕里残留着龙威",
        "name": "龙脊徽记", "roster_id": "eq_long_ji_hui_ji", "blueprint": "龙脊徽记图纸"},
    "rec_lie_shou_dou_peng": {"slot": "armor", "quality": "blue", "lv": 56,
        "mats": {"mat_lang_pi": 4, "mat_yan_xi_lin": 4}, "gold": 504, "desc": "北境猎手的实用斗篷，风雪无阻",
        "name": "猎手斗篷", "roster_id": "eq_lie_shou_dou_peng"},
    "rec_lie_shou_zhi_xue": {"slot": "boots", "quality": "blue", "lv": 54,
        "mats": {"mat_lang_pi": 5, "mat_yan_yang_mao": 3}, "gold": 486, "desc": "猎手之靴，雪原上悄然无声",
        "name": "猎手之靴", "roster_id": "eq_lie_shou_zhi_xue"},
    "rec_tie_bi_hu_fu": {"slot": "ring", "quality": "blue", "lv": 52,
        "mats": {"mat_jing_tie": 4, "mat_tie_kuang_shi": 4}, "gold": 468, "desc": "铁壁堡的守御环饰，厚实如磐石",
        "name": "铁壁护符", "roster_id": "eq_tie_bi_hu_fu"},
    "rec_xing_huo_jie_zhi": {"slot": "ring", "quality": "purple", "lv": 64,
        "mats": {"mat_jing_tie": 1, "mat_bing_jing": 4, "mat_mo_fa_fen_chen": 3}, "gold": 704, "desc": "极夜尽头的一粒星火，微弱却灼热",
        "name": "星火戒指", "roster_id": "eq_xing_huo_jie_zhi", "blueprint": "星火戒指图纸"},
    "rec_cang_lang_zhi_zhua": {"slot": "ring", "quality": "purple", "lv": 66,
        "mats": {"mat_jing_tie": 1, "mat_lang_pi": 4, "mat_qiang_hua_shi": 3}, "gold": 726, "desc": "霜角狼王之爪锻成的戒指，凶悍孤傲",
        "name": "苍狼之爪", "roster_id": "eq_cang_lang_zhi_zhua", "blueprint": "苍狼之爪图纸"},
    # ---------------- 资料片五：苍穹之巅 ----------------
    "rec_feng_bao_zhi_yan": {"slot": "ring", "quality": "purple", "lv": 80,
        "mats": {"mat_mi_yin": 1, "mat_shui_jing": 3, "mat_mo_fa_fen_chen": 4}, "gold": 880, "desc": "雷云深处的造物，握在手里能听见闷雷滚动",
        "name": "风暴之眼", "roster_id": "eq_feng_bao_zhi_yan", "blueprint": "风暴之眼图纸"},
    "rec_feng_bao_diao_zhui": {"slot": "necklace", "quality": "purple", "lv": 82,
        "mats": {"mat_mi_yin": 1, "mat_shui_jing": 3, "mat_mo_fa_fen_chen": 4}, "gold": 902, "desc": "风暴吊坠，坠心锁着一道闪电",
        "name": "风暴吊坠", "roster_id": "eq_feng_bao_diao_zhui", "blueprint": "风暴吊坠图纸"},
    "rec_cang_qiong_zhi_yi": {"slot": "armor", "quality": "orange", "lv": 88,
        "mats": {"mat_jing_jin": 1, "mat_mi_yin": 2, "mat_yu_mao": 1, "mat_mo_fa_fen_chen": 4}, "gold": 1144, "desc": "云海之巅以流云与天风铸成的羽翼",
        "name": "苍穹之翼", "roster_id": "eq_cang_qiong_zhi_yi", "blueprint": "苍穹之翼图纸"},
    "rec_cang_qiong_zhi_xue": {"slot": "boots", "quality": "orange", "lv": 86,
        "mats": {"mat_jing_jin": 1, "mat_mi_yin": 3, "mat_yu_mao": 1, "mat_mo_fa_fen_chen": 3}, "gold": 1118, "desc": "苍穹之靴，轻得仿佛能乘风而起",
        "name": "苍穹之靴", "roster_id": "eq_cang_qiong_zhi_xue", "blueprint": "苍穹之靴图纸"},
    "rec_long_yi_hu_fu": {"slot": "necklace", "quality": "purple", "lv": 84,
        "mats": {"mat_mi_yin": 1, "mat_jing_tie": 4, "mat_bing_jing": 3}, "gold": 924, "desc": "古龙掠过苍穹时落下的鳞羽护符",
        "name": "龙翼护符", "roster_id": "eq_long_yi_hu_fu", "blueprint": "龙翼护符图纸"},
    "rec_long_yi_jie_zhi": {"slot": "ring", "quality": "purple", "lv": 84,
        "mats": {"mat_mi_yin": 1, "mat_jing_tie": 4, "mat_qiang_hua_shi": 3}, "gold": 924, "desc": "龙翼戒指，带着高空的寒意",
        "name": "龙翼戒指", "roster_id": "eq_long_yi_jie_zhi", "blueprint": "龙翼戒指图纸"},
    "rec_tian_qiong_zhi_guan": {"slot": "helm", "quality": "purple", "lv": 86,
        "mats": {"mat_mi_yin": 1, "mat_jing_tie": 3, "mat_shui_jing": 4}, "gold": 946, "desc": "天穹圣殿的冠冕，辉光如正午天光",
        "name": "天穹之冠", "roster_id": "eq_tian_qiong_zhi_guan", "blueprint": "天穹之冠图纸"},
    "rec_xing_guang_xiang_lian": {"slot": "necklace", "quality": "purple", "lv": 80,
        "mats": {"mat_mi_yin": 1, "mat_shui_jing": 3, "mat_mo_fa_fen_chen": 4}, "gold": 880, "desc": "苍穹之巅的星光凝成的项链",
        "name": "星光项链", "roster_id": "eq_xing_guang_xiang_lian", "blueprint": "星光项链图纸"},
    "rec_feng_shen_zhi_huan": {"slot": "ring", "quality": "orange", "lv": 92,
        "mats": {"mat_jing_jin": 1, "mat_mi_yin": 1, "mat_yu_mao": 2, "mat_mo_fa_fen_chen": 4}, "gold": 1196, "desc": "风神行走天际时遗落的环饰",
        "name": "风神之环", "roster_id": "eq_feng_shen_zhi_huan", "blueprint": "风神之环图纸"},
    "rec_lei_guang_hui_zhang": {"slot": "necklace", "quality": "purple", "lv": 88,
        "mats": {"mat_mi_yin": 1, "mat_shui_jing": 3, "mat_mo_fa_fen_chen": 4}, "gold": 968, "desc": "雷云裂隙间的电光凝成的徽章",
        "name": "雷光徽章", "roster_id": "eq_lei_guang_hui_zhang", "blueprint": "雷光徽章图纸"},
    "rec_mi_yin_shou_zhuo": {"slot": "ring", "quality": "blue", "lv": 75,
        "mats": {"mat_mi_yin": 2, "mat_jing_tie": 3, "mat_shui_jing": 3}, "gold": 675, "desc": "天穹工匠以秘银锻造的手镯，银光流转",
        "name": "秘银手镯", "roster_id": "eq_mi_yin_shou_zhuo"},
    "rec_shou_wang_zhe_hu_fu": {"slot": "necklace", "quality": "purple", "lv": 78,
        "mats": {"mat_mi_yin": 1, "mat_jing_tie": 4, "mat_mo_fa_fen_chen": 3}, "gold": 858, "desc": "苍穹守望者的护符，凝视过云海尽头的日出",
        "name": "守望者护符", "roster_id": "eq_shou_wang_zhe_hu_fu", "blueprint": "守望者护符图纸"},
}

# ============================================================
# 7. MAT_DROP_MAP —— 空 dict（散装用现有素材，掉落已由既有怪物/地图覆盖）
# ============================================================
MAT_DROP_MAP = {}

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
}

# ============================================================
# 自检（仅 __main__ 运行，不污染导入）
# ============================================================
if __name__ == "__main__":
    import json
    import pathlib

    _np_path = pathlib.Path(__file__).resolve().parent / "naming_plan.json"
    _np = json.loads(_np_path.read_text(encoding="utf-8"))
    _sp = _np["scatter_plan"]

    # 1) 从 naming_plan 提取散装规划（名字/部位/品质/等级/系列）
    _plan = {}  # name -> (slot, quality, lv, series)
    for _g in ("scatter_1", "scatter_2", "scatter_3", "scatter_4", "scatter_5"):
        for _it in _sp[_g]:
            _name, _slot, _q, _lv, _stats, _series = _it
            assert _name not in _plan, f"scatter_plan 内部重名: {_name}"
            _plan[_name] = (_slot, _q, _lv, _series)

    _roster_names = {e["name"] for e in EQUIP_ROSTER.values()}
    assert len(EQUIP_ROSTER) == 60, f"EQUIP_ROSTER 应为 60 条，实际 {len(EQUIP_ROSTER)}"
    assert len(_roster_names) == 60, "装备名重复"
    assert _roster_names == set(_plan.keys()), f"名册名与 scatter_plan 不一致: {sorted(set(_plan) ^ _roster_names)}"
    assert _roster_names.isdisjoint(set(_np["existing_names"])), "与 existing_names 撞名"

    # 2) 名册字段与规划逐项一致（name/slot/quality/lv/series）
    for _eid, _e in EQUIP_ROSTER.items():
        _slot, _q, _lv, _series = _plan[_e["name"]]
        assert _e["slot"] == _slot, f"{_e['name']} slot 不符"
        assert _e["quality"] == _q, f"{_e['name']} quality 不符"
        assert _e["lv"] == _lv, f"{_e['name']} lv 不符"
        assert _e["series"] == _series, f"{_e['name']} series 不符"
        assert "set" not in _e, f"散装不得带 set 字段: {_e['name']}"
        assert _e["source"] == "图纸", f"{_e['name']} source 应为图纸"
        assert _e["slot"] in ("helm", "armor", "legs", "boots", "ring", "necklace"), f"{_e['name']} slot 非法"

    # 3) SERIES_FIXED_AFFIX 与名册一一对应，词条 id 均须在 AFFIXES 存在
    assert set(SERIES_FIXED_AFFIX.keys()) == _roster_names, "SERIES_FIXED_AFFIX 名不匹配名册"
    import sys
    _root = pathlib.Path(__file__).resolve().parents[3]  # workspace/phase6_frags → 插件根
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from game.data import AFFIXES as _AFFIXES, MATERIALS as _MATS
    for _n, _ids in SERIES_FIXED_AFFIX.items():
        for _aid in _ids:
            assert _aid in _AFFIXES, f"词条 id 不存在: {_aid}（{_n}）"

    # 4) SERIES_SETS 必须为空（散装不进套装体系）
    assert SERIES_SETS == {}, "散装不得进 SERIES_SETS"
    for _s in set(_plan.values()):
        assert _s[3] not in _np["class_sets"], f"散装系列不得与职业套装系列冲突: {_s[3]}"

    # 5) CRAFT_RECIPES 60 条，roster_id/name 全对，gold 按品质档位，紫/橙必有 blueprint
    assert len(CRAFT_RECIPES) == 60, f"CRAFT_RECIPES 应为 60 条，实际 {len(CRAFT_RECIPES)}"
    assert set(CRAFT_RECIPES.keys()) == {f"rec_{eid.removeprefix('eq_')}" for eid in EQUIP_ROSTER.keys()}, "配方 id 不匹配"
    for _eid, _e in EQUIP_ROSTER.items():
        _r = CRAFT_RECIPES["rec_" + _eid.removeprefix("eq_")]
        assert _r["roster_id"] == _eid and _r["name"] == _e["name"], f"配方对应错: {_eid}"
        assert _r["slot"] == _e["slot"] and _r["quality"] == _e["quality"] and _r["lv"] == _e["lv"], f"配方属性不符: {_eid}"
        _mult = {"green": 9, "blue": 9, "purple": 11, "orange": 13}[_e["quality"]]
        assert _r["gold"] == _e["lv"] * _mult, f"gold 公式不符: {_eid} ({_r['gold']} vs {_e['lv']*_mult})"
        assert 3 <= sum(_r["mats"].values()) <= 8, f"防具 mats 数量应在 3-8: {_eid} ({sum(_r['mats'].values())})"
        for _mid in _r["mats"]:
            assert _mid in _MATS, f"素材 id 不存在: {_mid}（{_eid}）"
        if _e["quality"] in ("purple", "orange"):
            assert _r.get("blueprint"), f"紫/橙配方缺 blueprint: {_eid}"
        else:
            assert "blueprint" not in _r, f"蓝/绿配方不应有 blueprint: {_eid}"

    # 6) 素材/掉落为空
    assert MATERIALS == {} and MAT_DROP_MAP == {}, "散装不新增素材与掉落"

    # 7) EQ_SERIES_THEME 覆盖全部散装系列
    _series_set = {v[3] for v in _plan.values()}
    assert len(EQ_SERIES_THEME) == len(_series_set) == 43, f"EQ_SERIES_THEME 应为 43 条，实际 {len(EQ_SERIES_THEME)}"
    assert set(EQ_SERIES_THEME.keys()) == _series_set, "EQ_SERIES_THEME 系列不全"

    print("EQUIP_ROSTER:", len(EQUIP_ROSTER))
    print("SERIES_FIXED_AFFIX:", len(SERIES_FIXED_AFFIX))
    print("SERIES_SETS:", len(SERIES_SETS))
    print("EQ_SERIES_THEME:", len(EQ_SERIES_THEME))
    print("MATERIALS:", len(MATERIALS))
    print("CRAFT_RECIPES:", len(CRAFT_RECIPES))
    print("MAT_DROP_MAP:", len(MAT_DROP_MAP))
    print("自检通过：60 件散装与 scatter_plan 完全一致，词条/配方/素材全匹配，散装未进套装体系")
