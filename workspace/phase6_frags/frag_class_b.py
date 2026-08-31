# -*- coding: utf-8 -*-
"""Phase 6 片段 - 职业套装 B（游侠 / 刺客 / 拳师，9 系列 × 5 部位 = 45 件）

系列划分（naming_plan.json class_sets.cls_you_xia / cls_ci_ke / cls_wu_seng 精确命名）：
- 游侠（req=agi，武器 bow）  : 猎手(Ⅰ) / 风行(Ⅱ) / 暗夜(Ⅲ)
- 刺客（req=agi，武器 dagger）: 轻影(Ⅰ) / 夜行(Ⅱ) / 阴影(Ⅲ)
- 拳师（req=str，武器 fist） : 行者(Ⅰ) / 石拳(Ⅱ) / 壁槌(Ⅲ)

阶段：Ⅰ=lv10 blue，Ⅱ=lv30 blue，Ⅲ=lv50 purple。
req：武器 = lv（本职业主属性），防具 = lv-2~4。
素材组与 frag_class_a 共享（Ⅰ：狼皮/野猪皮/山贼徽章；Ⅱ：噬石核心/兽人獠牙/座狼犬齿；
Ⅲ：圣光结晶/月影之皮/龙炎精华），MATERIALS 与 MAT_DROP_MAP 由 A 片段负责，本片段留空。
"""
from __future__ import annotations

# ============================================================
# 1. EQUIP_ROSTER —— 45 件（3 职业 × 3 阶段 × 5 部位）
# ============================================================
EQUIP_ROSTER = {
    # ========== 游侠（弓手） ==========
    # ---- 猎手（Ⅰ · lv10 · blue） ----
    "eq_lie_shou_duan_gong": {"name": "猎手短弓", "slot": "weapon", "weapon_type": "bow", "quality": "blue", "lv": 10, "series": "猎手", "req": {"agi": 10}, "source": "锻造"},
    "eq_lie_shou_pi_mao":    {"name": "猎手皮帽", "slot": "helm",   "quality": "blue", "lv": 10, "series": "猎手", "req": {"agi": 8},  "source": "锻造"},
    "eq_lie_shou_pi_jia":    {"name": "猎手皮甲", "slot": "armor",  "quality": "blue", "lv": 10, "series": "猎手", "req": {"agi": 8},  "source": "锻造"},
    "eq_lie_shou_hu_tui":    {"name": "猎手护腿", "slot": "legs",   "quality": "blue", "lv": 10, "series": "猎手", "req": {"agi": 7},  "source": "锻造"},
    "eq_lie_shou_chang_xue": {"name": "猎手长靴", "slot": "boots",  "quality": "blue", "lv": 10, "series": "猎手", "req": {"agi": 6},  "source": "锻造"},
    # ---- 风行（Ⅱ · lv30 · blue） ----
    "eq_lie_shou_chang_gong": {"name": "猎手长弓", "slot": "weapon", "weapon_type": "bow", "quality": "blue", "lv": 30, "series": "风行", "req": {"agi": 30}, "source": "锻造"},
    "eq_feng_xing_pi_mao":    {"name": "风行皮帽", "slot": "helm",   "quality": "blue", "lv": 30, "series": "风行", "req": {"agi": 28}, "source": "锻造"},
    "eq_feng_xing_pi_jia":    {"name": "风行皮甲", "slot": "armor",  "quality": "blue", "lv": 30, "series": "风行", "req": {"agi": 28}, "source": "锻造"},
    "eq_feng_xing_hu_tui":    {"name": "风行护腿", "slot": "legs",   "quality": "blue", "lv": 30, "series": "风行", "req": {"agi": 26}, "source": "锻造"},
    "eq_feng_xing_chang_xue": {"name": "风行长靴", "slot": "boots",  "quality": "blue", "lv": 30, "series": "风行", "req": {"agi": 26}, "source": "锻造"},
    # ---- 暗夜（Ⅲ · lv50 · purple） ----
    "eq_feng_xing_chang_gong": {"name": "风行长弓", "slot": "weapon", "weapon_type": "bow", "quality": "purple", "lv": 50, "series": "暗夜", "req": {"agi": 50}, "source": "锻造"},
    "eq_an_ye_pi_mao":         {"name": "暗夜皮帽", "slot": "helm",   "quality": "purple", "lv": 50, "series": "暗夜", "req": {"agi": 48}, "source": "锻造"},
    "eq_an_ye_pi_jia":         {"name": "暗夜皮甲", "slot": "armor",  "quality": "purple", "lv": 50, "series": "暗夜", "req": {"agi": 48}, "source": "锻造"},
    "eq_an_ye_hu_tui":         {"name": "暗夜护腿", "slot": "legs",   "quality": "purple", "lv": 50, "series": "暗夜", "req": {"agi": 46}, "source": "锻造"},
    "eq_an_ye_chang_xue":      {"name": "暗夜长靴", "slot": "boots",  "quality": "purple", "lv": 50, "series": "暗夜", "req": {"agi": 46}, "source": "锻造"},

    # ========== 刺客（匕首） ==========
    # ---- 轻影（Ⅰ · lv10 · blue） ----
    "eq_qing_ying_bi_shou": {"name": "轻影匕首", "slot": "weapon", "weapon_type": "dagger", "quality": "blue", "lv": 10, "series": "轻影", "req": {"agi": 10}, "source": "锻造"},
    "eq_qing_ying_mian_jin": {"name": "轻影面巾", "slot": "helm",   "quality": "blue", "lv": 10, "series": "轻影", "req": {"agi": 8},  "source": "锻造"},
    "eq_qing_ying_pi_yi":     {"name": "轻影皮衣", "slot": "armor",  "quality": "blue", "lv": 10, "series": "轻影", "req": {"agi": 8},  "source": "锻造"},
    "eq_qing_ying_hu_tui":    {"name": "轻影护腿", "slot": "legs",   "quality": "blue", "lv": 10, "series": "轻影", "req": {"agi": 7},  "source": "锻造"},
    "eq_qing_ying_qing_xue":  {"name": "轻影轻靴", "slot": "boots",  "quality": "blue", "lv": 10, "series": "轻影", "req": {"agi": 6},  "source": "锻造"},
    # ---- 夜行（Ⅱ · lv30 · blue） ----
    "eq_ye_xing_bi_shou": {"name": "夜行匕首", "slot": "weapon", "weapon_type": "dagger", "quality": "blue", "lv": 30, "series": "夜行", "req": {"agi": 30}, "source": "锻造"},
    "eq_ye_xing_mian_jin": {"name": "夜行面巾", "slot": "helm",   "quality": "blue", "lv": 30, "series": "夜行", "req": {"agi": 28}, "source": "锻造"},
    "eq_ye_xing_pi_yi":     {"name": "夜行皮衣", "slot": "armor",  "quality": "blue", "lv": 30, "series": "夜行", "req": {"agi": 28}, "source": "锻造"},
    "eq_ye_xing_hu_tui":    {"name": "夜行护腿", "slot": "legs",   "quality": "blue", "lv": 30, "series": "夜行", "req": {"agi": 26}, "source": "锻造"},
    "eq_ye_xing_qing_xue":  {"name": "夜行轻靴", "slot": "boots",  "quality": "blue", "lv": 30, "series": "夜行", "req": {"agi": 26}, "source": "锻造"},
    # ---- 阴影（Ⅲ · lv50 · purple） ----
    "eq_yin_ying_bi_shou": {"name": "阴影匕首", "slot": "weapon", "weapon_type": "dagger", "quality": "purple", "lv": 50, "series": "阴影", "req": {"agi": 50}, "source": "锻造"},
    "eq_yin_ying_mian_jin": {"name": "阴影面巾", "slot": "helm",   "quality": "purple", "lv": 50, "series": "阴影", "req": {"agi": 48}, "source": "锻造"},
    "eq_yin_ying_pi_yi":     {"name": "阴影皮衣", "slot": "armor",  "quality": "purple", "lv": 50, "series": "阴影", "req": {"agi": 48}, "source": "锻造"},
    "eq_yin_ying_hu_tui":    {"name": "阴影护腿", "slot": "legs",   "quality": "purple", "lv": 50, "series": "阴影", "req": {"agi": 46}, "source": "锻造"},
    "eq_yin_ying_qing_xue":  {"name": "阴影轻靴", "slot": "boots",  "quality": "purple", "lv": 50, "series": "阴影", "req": {"agi": 46}, "source": "锻造"},

    # ========== 拳师（拳套） ==========
    # ---- 行者（Ⅰ · lv10 · blue） ----
    "eq_xing_zhe_quan_tao": {"name": "行者拳套", "slot": "weapon", "weapon_type": "fist", "quality": "blue", "lv": 10, "series": "行者", "req": {"str": 10}, "source": "锻造"},
    "eq_xing_zhe_shu_fa_dai": {"name": "行者束发带", "slot": "helm",   "quality": "blue", "lv": 10, "series": "行者", "req": {"str": 8},  "source": "锻造"},
    "eq_xing_zhe_wu_dou_pao": {"name": "行者武斗袍", "slot": "armor",  "quality": "blue", "lv": 10, "series": "行者", "req": {"str": 8},  "source": "锻造"},
    "eq_xing_zhe_hu_tui":     {"name": "行者护腿", "slot": "legs",   "quality": "blue", "lv": 10, "series": "行者", "req": {"str": 7},  "source": "锻造"},
    "eq_xing_zhe_bu_xue":     {"name": "行者布靴", "slot": "boots",  "quality": "blue", "lv": 10, "series": "行者", "req": {"str": 6},  "source": "锻造"},
    # ---- 石拳（Ⅱ · lv30 · blue） ----
    "eq_shi_quan_quan_tao": {"name": "石拳拳套", "slot": "weapon", "weapon_type": "fist", "quality": "blue", "lv": 30, "series": "石拳", "req": {"str": 30}, "source": "锻造"},
    "eq_shi_quan_shu_fa_dai": {"name": "石拳束发带", "slot": "helm",   "quality": "blue", "lv": 30, "series": "石拳", "req": {"str": 28}, "source": "锻造"},
    "eq_shi_quan_wu_dou_pao": {"name": "石拳武斗袍", "slot": "armor",  "quality": "blue", "lv": 30, "series": "石拳", "req": {"str": 28}, "source": "锻造"},
    "eq_shi_quan_hu_tui":     {"name": "石拳护腿", "slot": "legs",   "quality": "blue", "lv": 30, "series": "石拳", "req": {"str": 26}, "source": "锻造"},
    "eq_shi_quan_bu_xue":     {"name": "石拳布靴", "slot": "boots",  "quality": "blue", "lv": 30, "series": "石拳", "req": {"str": 26}, "source": "锻造"},
    # ---- 壁槌（Ⅲ · lv50 · purple） ----
    "eq_bi_chui_quan_tao": {"name": "壁槌拳套", "slot": "weapon", "weapon_type": "fist", "quality": "purple", "lv": 50, "series": "壁槌", "req": {"str": 50}, "source": "锻造"},
    "eq_bi_chui_shu_fa_dai": {"name": "壁槌束发带", "slot": "helm",   "quality": "purple", "lv": 50, "series": "壁槌", "req": {"str": 48}, "source": "锻造"},
    "eq_bi_chui_wu_dou_pao": {"name": "壁槌武斗袍", "slot": "armor",  "quality": "purple", "lv": 50, "series": "壁槌", "req": {"str": 48}, "source": "锻造"},
    "eq_bi_chui_hu_tui":     {"name": "壁槌护腿", "slot": "legs",   "quality": "purple", "lv": 50, "series": "壁槌", "req": {"str": 46}, "source": "锻造"},
    "eq_bi_chui_bu_xue":     {"name": "壁槌布靴", "slot": "boots",  "quality": "purple", "lv": 50, "series": "壁槌", "req": {"str": 46}, "source": "锻造"},
}

# ============================================================
# 2. SERIES_FIXED_AFFIX —— 45 条（键 = 装备中文名，值 = AFFIXES 词条 id）
# 游侠：速度暴击向（swift/crit_up/precise/hunt）
# 刺客：暴击穿透向（crit_up/crit_dmg/combo/execute/pene_phys）
# 拳师：格挡反伤向（tenacity/block/counter/charge/lifesteal）
# 武器 = attack 类词条；防具 = defense 类词条（generate_roster_equip 按 kind 过滤）
# ============================================================
SERIES_FIXED_AFFIX = {
    # ---- 游侠 · 猎手（Ⅰ） ----
    "猎手短弓": ["precise"],
    "猎手皮帽": ["swift"],
    "猎手皮甲": ["swift"],
    "猎手护腿": ["swift"],
    "猎手长靴": ["swift"],
    # ---- 游侠 · 风行（Ⅱ） ----
    "猎手长弓": ["precise", "hunt"],
    "风行皮帽": ["swift"],
    "风行皮甲": ["swift", "dodge"],
    "风行护腿": ["swift"],
    "风行长靴": ["swift"],
    # ---- 游侠 · 暗夜（Ⅲ） ----
    "风行长弓": ["crit_up", "precise", "hunt"],
    "暗夜皮帽": ["swift", "dodge"],
    "暗夜皮甲": ["swift", "dodge"],
    "暗夜护腿": ["swift"],
    "暗夜长靴": ["swift"],
    # ---- 刺客 · 轻影（Ⅰ） ----
    "轻影匕首": ["combo"],
    "轻影面巾": ["dodge"],
    "轻影皮衣": ["dodge"],
    "轻影护腿": ["swift"],
    "轻影轻靴": ["swift"],
    # ---- 刺客 · 夜行（Ⅱ） ----
    "夜行匕首": ["crit_up", "combo"],
    "夜行面巾": ["dodge"],
    "夜行皮衣": ["dodge"],
    "夜行护腿": ["swift"],
    "夜行轻靴": ["swift"],
    # ---- 刺客 · 阴影（Ⅲ） ----
    "阴影匕首": ["crit_up", "combo", "pene_phys"],
    "阴影面巾": ["dodge", "swift"],
    "阴影皮衣": ["dodge", "swift"],
    "阴影护腿": ["swift"],
    "阴影轻靴": ["swift", "dodge"],
    # ---- 拳师 · 行者（Ⅰ） ----
    "行者拳套": ["charge"],
    "行者束发带": ["block"],
    "行者武斗袍": ["tenacity"],
    "行者护腿": ["block"],
    "行者布靴": ["tenacity"],
    # ---- 拳师 · 石拳（Ⅱ） ----
    "石拳拳套": ["charge", "counter"],
    "石拳束发带": ["block"],
    "石拳武斗袍": ["tenacity", "block"],
    "石拳护腿": ["block"],
    "石拳布靴": ["tenacity"],
    # ---- 拳师 · 壁槌（Ⅲ） ----
    "壁槌拳套": ["charge", "counter", "lifesteal"],
    "壁槌束发带": ["block", "tenacity"],
    "壁槌武斗袍": ["tenacity", "block"],
    "壁槌护腿": ["block"],
    "壁槌布靴": ["tenacity", "block"],
}

# ============================================================
# 3. SERIES_SETS —— 9 条（系列名 → 套装名）
# ============================================================
SERIES_SETS = {
    "猎手": "猎手套",
    "风行": "风行套",
    "暗夜": "暗夜套",
    "轻影": "轻影套",
    "夜行": "夜行套",
    "阴影": "阴影套",
    "行者": "行者套",
    "石拳": "石拳套",
    "壁槌": "壁槌套",
}

# ============================================================
# 4. EQ_SERIES_THEME —— 9 条（阶段系列描述文案）
# 游侠=风驰电掣风 / 刺客=暗影潜行风 / 拳师=拳拳到肉风
# ============================================================
EQ_SERIES_THEME = {
    "猎手": "猎手林间巡猎的轻弓皮甲，弦声破风，快如惊鹿",
    "风行": "风行者的疾驰战装，风从弓弦上流过，猎影转瞬即至",
    "暗夜": "暗夜猎手的潜行战具，箭矢无声，月色是最好的掩护",
    "轻影": "轻影刺客的贴身软甲，出手如影，只在呼吸间留下寒光",
    "夜行": "夜行者的暗刃装束，融于夜色，来去不留一丝痕迹",
    "阴影": "阴影之刃的终极武装，隐匿于光与影的缝隙，一击必杀",
    "行者": "行者的缠布武斗装，拳风朴实，一步一拳皆是千锤百炼",
    "石拳": "石拳武僧的硬功战袍，拳出如锤，崩山裂石",
    "壁槌": "壁槌武僧的镇山重甲，拳掌如壁，攻守之间气沉如山",
}

# ============================================================
# 5. MATERIALS —— 留空（与 frag_class_a 共享同一阶段素材组，
#    mat_ye_zhu_pi / mat_shan_zei_hui_zhang / mat_shu_shi_he_xin /
#    mat_yue_ying_zhi_pi / mat_long_yan_jing_hua 由 A 片段定义；
#    mat_lang_pi / mat_sheng_guang_jie_jing / mat_shou_ren_liao_ya /
#    mat_zuo_lang_quan_chi 已在 game/data/items.py 存在，无需重复）
# ============================================================
MATERIALS = {}

# ============================================================
# 6. CRAFT_RECIPES —— 45 条
# gold：蓝装 lv×9，紫装 lv×11；武器 mats ×2；紫装加 blueprint
# ============================================================
_MATS_I = {"mat_lang_pi": 6, "mat_ye_zhu_pi": 5, "mat_shan_zei_hui_zhang": 3}
_MATS_II = {"mat_shu_shi_he_xin": 4, "mat_shou_ren_liao_ya": 6, "mat_zuo_lang_quan_chi": 4}
_MATS_III = {"mat_sheng_guang_jie_jing": 5, "mat_yue_ying_zhi_pi": 5, "mat_long_yan_jing_hua": 3}


def _mats(base: dict, weapon: bool = False) -> dict:
    """武器 mats ×2（保留原 key 顺序）"""
    if not weapon:
        return dict(base)
    return {k: v * 2 for k, v in base.items()}


def _rec(rid: str, name: str, slot: str, quality: str, lv: int, mats: dict,
         gold: int, desc: str, weapon_type: str | None = None) -> dict:
    d = {
        "slot": slot,
        "quality": quality,
        "lv": lv,
        "mats": dict(mats),
        "gold": gold,
        "desc": desc,
        "name": name,
        "roster_id": rid,
    }
    if weapon_type:
        d["weapon_type"] = weapon_type
    if quality == "purple":
        d["blueprint"] = f"{name}图纸"
    return d


CRAFT_RECIPES = {
    # ---- 游侠 · 猎手（Ⅰ · lv10 · blue） ----
    "rec_lie_shou_duan_gong": _rec("eq_lie_shou_duan_gong", "猎手短弓", "weapon", "blue", 10, _mats(_MATS_I, True), 90, "猎手林间的制式短弓，轻快易拉", weapon_type="bow"),
    "rec_lie_shou_pi_mao":    _rec("eq_lie_shou_pi_mao",    "猎手皮帽", "helm",   "blue", 10, _mats(_MATS_I), 90, "猎手林间的制式皮帽，轻便透气"),
    "rec_lie_shou_pi_jia":    _rec("eq_lie_shou_pi_jia",    "猎手皮甲", "armor",  "blue", 10, _mats(_MATS_I), 90, "猎手林间的制式皮甲，贴身灵活"),
    "rec_lie_shou_hu_tui":    _rec("eq_lie_shou_hu_tui",    "猎手护腿", "legs",   "blue", 10, _mats(_MATS_I), 90, "猎手林间的制式护腿，膝部加厚"),
    "rec_lie_shou_chang_xue": _rec("eq_lie_shou_chang_xue", "猎手长靴", "boots",  "blue", 10, _mats(_MATS_I), 90, "猎手林间的制式长靴，抓地无声"),
    # ---- 游侠 · 风行（Ⅱ · lv30 · blue） ----
    "rec_lie_shou_chang_gong": _rec("eq_lie_shou_chang_gong", "猎手长弓", "weapon", "blue", 30, _mats(_MATS_II, True), 270, "风行猎手的长弓，弦声如风", weapon_type="bow"),
    "rec_feng_xing_pi_mao":    _rec("eq_feng_xing_pi_mao",    "风行皮帽", "helm",   "blue", 30, _mats(_MATS_II), 270, "风行者的皮帽，帽檐压风"),
    "rec_feng_xing_pi_jia":    _rec("eq_feng_xing_pi_jia",    "风行皮甲", "armor",  "blue", 30, _mats(_MATS_II), 270, "风行者的皮甲，风线裁切"),
    "rec_feng_xing_hu_tui":    _rec("eq_feng_xing_hu_tui",    "风行护腿", "legs",   "blue", 30, _mats(_MATS_II), 270, "风行者的护腿，步幅轻盈"),
    "rec_feng_xing_chang_xue": _rec("eq_feng_xing_chang_xue", "风行长靴", "boots",  "blue", 30, _mats(_MATS_II), 270, "风行者的长靴，踏风而行"),
    # ---- 游侠 · 暗夜（Ⅲ · lv50 · purple） ----
    "rec_feng_xing_chang_gong": _rec("eq_feng_xing_chang_gong", "风行长弓", "weapon", "purple", 50, _mats(_MATS_III, True), 550, "暗夜猎手的传奇长弓，月色淬弦", weapon_type="bow"),
    "rec_an_ye_pi_mao":         _rec("eq_an_ye_pi_mao",         "暗夜皮帽", "helm",   "purple", 50, _mats(_MATS_III), 550, "暗夜猎手的皮帽，隐于夜色"),
    "rec_an_ye_pi_jia":         _rec("eq_an_ye_pi_jia",         "暗夜皮甲", "armor",  "purple", 50, _mats(_MATS_III), 550, "暗夜猎手的皮甲，箭雨不沾身"),
    "rec_an_ye_hu_tui":         _rec("eq_an_ye_hu_tui",         "暗夜护腿", "legs",   "purple", 50, _mats(_MATS_III), 550, "暗夜猎手的护腿，潜行无声"),
    "rec_an_ye_chang_xue":      _rec("eq_an_ye_chang_xue",      "暗夜长靴", "boots",  "purple", 50, _mats(_MATS_III), 550, "暗夜猎手的长靴，落地无痕"),
    # ---- 刺客 · 轻影（Ⅰ · lv10 · blue） ----
    "rec_qing_ying_bi_shou":  _rec("eq_qing_ying_bi_shou",  "轻影匕首", "weapon", "blue", 10, _mats(_MATS_I, True), 90, "轻影刺客的制式匕首，刃薄如纸", weapon_type="dagger"),
    "rec_qing_ying_mian_jin": _rec("eq_qing_ying_mian_jin", "轻影面巾", "helm",   "blue", 10, _mats(_MATS_I), 90, "轻影刺客的面巾，遮住半张脸"),
    "rec_qing_ying_pi_yi":    _rec("eq_qing_ying_pi_yi",    "轻影皮衣", "armor",  "blue", 10, _mats(_MATS_I), 90, "轻影刺客的皮衣，贴身无缚"),
    "rec_qing_ying_hu_tui":   _rec("eq_qing_ying_hu_tui",   "轻影护腿", "legs",   "blue", 10, _mats(_MATS_I), 90, "轻影刺客的护腿，膝弯灵活"),
    "rec_qing_ying_qing_xue": _rec("eq_qing_ying_qing_xue", "轻影轻靴", "boots",  "blue", 10, _mats(_MATS_I), 90, "轻影刺客的轻靴，鞋底垫软布"),
    # ---- 刺客 · 夜行（Ⅱ · lv30 · blue） ----
    "rec_ye_xing_bi_shou":  _rec("eq_ye_xing_bi_shou",  "夜行匕首", "weapon", "blue", 30, _mats(_MATS_II, True), 270, "夜行者的淬毒匕首，刃口泛幽光", weapon_type="dagger"),
    "rec_ye_xing_mian_jin": _rec("eq_ye_xing_mian_jin", "夜行面巾", "helm",   "blue", 30, _mats(_MATS_II), 270, "夜行者的面巾，染过夜露"),
    "rec_ye_xing_pi_yi":    _rec("eq_ye_xing_pi_yi",    "夜行皮衣", "armor",  "blue", 30, _mats(_MATS_II), 270, "夜行者的皮衣，暗扣无声"),
    "rec_ye_xing_hu_tui":   _rec("eq_ye_xing_hu_tui",   "夜行护腿", "legs",   "blue", 30, _mats(_MATS_II), 270, "夜行者的护腿，蹲伏不响"),
    "rec_ye_xing_qing_xue": _rec("eq_ye_xing_qing_xue", "夜行轻靴", "boots",  "blue", 30, _mats(_MATS_II), 270, "夜行者的轻靴，踩过瓦片无声"),
    # ---- 刺客 · 阴影（Ⅲ · lv50 · purple） ----
    "rec_yin_ying_bi_shou":  _rec("eq_yin_ying_bi_shou",  "阴影匕首", "weapon", "purple", 50, _mats(_MATS_III, True), 550, "阴影之刃的传奇匕首，吞光噬影", weapon_type="dagger"),
    "rec_yin_ying_mian_jin": _rec("eq_yin_ying_mian_jin", "阴影面巾", "helm",   "purple", 50, _mats(_MATS_III), 550, "阴影之刃的面巾，融于暗处"),
    "rec_yin_ying_pi_yi":    _rec("eq_yin_ying_pi_yi",    "阴影皮衣", "armor",  "purple", 50, _mats(_MATS_III), 550, "阴影之刃的皮衣，刀锋难辨"),
    "rec_yin_ying_hu_tui":   _rec("eq_yin_ying_hu_tui",   "阴影护腿", "legs",   "purple", 50, _mats(_MATS_III), 550, "阴影之刃的护腿，潜影无声"),
    "rec_yin_ying_qing_xue": _rec("eq_yin_ying_qing_xue", "阴影轻靴", "boots",  "purple", 50, _mats(_MATS_III), 550, "阴影之刃的轻靴，影过无痕"),
    # ---- 拳师 · 行者（Ⅰ · lv10 · blue） ----
    "rec_xing_zhe_quan_tao":   _rec("eq_xing_zhe_quan_tao",   "行者拳套", "weapon", "blue", 10, _mats(_MATS_I, True), 90, "行者缠布的制式拳套，护指耐磨", weapon_type="fist"),
    "rec_xing_zhe_shu_fa_dai": _rec("eq_xing_zhe_shu_fa_dai", "行者束发带", "helm",   "blue", 10, _mats(_MATS_I), 90, "行者的束发带，勒紧额发不碍眼"),
    "rec_xing_zhe_wu_dou_pao": _rec("eq_xing_zhe_wu_dou_pao", "行者武斗袍", "armor",  "blue", 10, _mats(_MATS_I), 90, "行者的武斗袍，下摆开衩好踢腿"),
    "rec_xing_zhe_hu_tui":     _rec("eq_xing_zhe_hu_tui",     "行者护腿", "legs",   "blue", 10, _mats(_MATS_I), 90, "行者的护腿，绑腿扎实"),
    "rec_xing_zhe_bu_xue":     _rec("eq_xing_zhe_bu_xue",     "行者布靴", "boots",  "blue", 10, _mats(_MATS_I), 90, "行者的布靴，千层底耐磨"),
    # ---- 拳师 · 石拳（Ⅱ · lv30 · blue） ----
    "rec_shi_quan_quan_tao":   _rec("eq_shi_quan_quan_tao",   "石拳拳套", "weapon", "blue", 30, _mats(_MATS_II, True), 270, "石拳武僧的硬拳套，拳面镶石", weapon_type="fist"),
    "rec_shi_quan_shu_fa_dai": _rec("eq_shi_quan_shu_fa_dai", "石拳束发带", "helm",   "blue", 30, _mats(_MATS_II), 270, "石拳武僧的束发带，浸过药油"),
    "rec_shi_quan_wu_dou_pao": _rec("eq_shi_quan_wu_dou_pao", "石拳武斗袍", "armor",  "blue", 30, _mats(_MATS_II), 270, "石拳武僧的武斗袍，肩背加衬"),
    "rec_shi_quan_hu_tui":     _rec("eq_shi_quan_hu_tui",     "石拳护腿", "legs",   "blue", 30, _mats(_MATS_II), 270, "石拳武僧的护腿，膝甲厚实"),
    "rec_shi_quan_bu_xue":     _rec("eq_shi_quan_bu_xue",     "石拳布靴", "boots",  "blue", 30, _mats(_MATS_II), 270, "石拳武僧的布靴，踩地生根"),
    # ---- 拳师 · 壁槌（Ⅲ · lv50 · purple） ----
    "rec_bi_chui_quan_tao":   _rec("eq_bi_chui_quan_tao",   "壁槌拳套", "weapon", "purple", 50, _mats(_MATS_III, True), 550, "壁槌武僧的传奇拳套，拳如铁壁", weapon_type="fist"),
    "rec_bi_chui_shu_fa_dai": _rec("eq_bi_chui_shu_fa_dai", "壁槌束发带", "helm",   "purple", 50, _mats(_MATS_III), 550, "壁槌武僧的束发带，鎏金盘扣"),
    "rec_bi_chui_wu_dou_pao": _rec("eq_bi_chui_wu_dou_pao", "壁槌武斗袍", "armor",  "purple", 50, _mats(_MATS_III), 550, "壁槌武僧的武斗袍，镇山纹样"),
    "rec_bi_chui_hu_tui":     _rec("eq_bi_chui_hu_tui",     "壁槌护腿", "legs",   "purple", 50, _mats(_MATS_III), 550, "壁槌武僧的护腿，稳如磐石"),
    "rec_bi_chui_bu_xue":     _rec("eq_bi_chui_bu_xue",     "壁槌布靴", "boots",  "purple", 50, _mats(_MATS_III), 550, "壁槌武僧的布靴，一步一个坑"),
}

# ============================================================
# 7. MAT_DROP_MAP —— 留空（素材产出地由 frag_class_a 负责）
# ============================================================
MAT_DROP_MAP = {}

# ============================================================
# 8. CLASS_SET_BONUS —— 9 条职业套装效果（阶段系列 → 套装属性/特效）
# 引擎消费：set_bonus_2 聚合 bonus_2/bonus_4_stats（class 字段 → 非本职业 ×0.6）；
# bonus_4.effect 由 battle._set_attack_proc → SET_PROC_EFFECTS 消费
# （dodge_set 为属性型：engine 按 bonus_4.stats 结算，无需 SET_PROC_EFFECTS 注册）
# ============================================================
CLASS_SET_BONUS = {
    # ---- 游侠（风驰电掣：速度暴击 + 闪避） ----
    "猎手": {
        "class": "cls_you_xia", "icon": "🏹", "quality": "blue",
        "bonus_2": {"spd": 0.08, "crit": 0.03},
        "bonus_4_stats": {"spd": 0.08},
        "bonus_4": {"effect": "dodge_set", "stats": {"dodge": 0.10}, "chance": 1.0,
                    "desc": "闪避率＋10%"},
    },
    "风行": {
        "class": "cls_you_xia", "icon": "🏹", "quality": "blue",
        "bonus_2": {"spd": 0.08, "crit": 0.03},
        "bonus_4_stats": {"spd": 0.08},
        "bonus_4": {"effect": "dodge_set", "stats": {"dodge": 0.10}, "chance": 1.0,
                    "desc": "闪避率＋10%"},
    },
    "暗夜": {
        "class": "cls_you_xia", "icon": "🏹", "quality": "purple",
        "bonus_2": {"spd": 0.08, "crit": 0.03},
        "bonus_4_stats": {"spd": 0.08},
        "bonus_4": {"effect": "dodge_set", "stats": {"dodge": 0.10}, "chance": 1.0,
                    "desc": "闪避率＋10%"},
    },
    # ---- 刺客（暴击穿透：暴击 + 处决） ----
    "轻影": {
        "class": "cls_ci_ke", "icon": "🗡️", "quality": "blue",
        "bonus_2": {"crit": 0.05, "atk": 0.08},
        "bonus_4_stats": {"crit": 0.05},
        "bonus_4": {"effect": "execute", "chance": 1.0,
                    "desc": "对生命低于 30% 的敌人额外造成 25% 伤害"},
    },
    "夜行": {
        "class": "cls_ci_ke", "icon": "🗡️", "quality": "blue",
        "bonus_2": {"crit": 0.05, "atk": 0.08},
        "bonus_4_stats": {"crit": 0.05},
        "bonus_4": {"effect": "execute", "chance": 1.0,
                    "desc": "对生命低于 30% 的敌人额外造成 25% 伤害"},
    },
    "阴影": {
        "class": "cls_ci_ke", "icon": "🗡️", "quality": "purple",
        "bonus_2": {"crit": 0.05, "atk": 0.08},
        "bonus_4_stats": {"crit": 0.05},
        "bonus_4": {"effect": "execute", "chance": 1.0,
                    "desc": "对生命低于 30% 的敌人额外造成 25% 伤害"},
    },
    # ---- 拳师（拳拳到肉：攻防 + 吸血） ----
    "行者": {
        "class": "cls_wu_seng", "icon": "🥋", "quality": "blue",
        "bonus_2": {"atk": 0.08, "def": 0.05},
        "bonus_4_stats": {"hp": 0.10},
        "bonus_4": {"effect": "lifesteal_set", "chance": 0.3,
                    "desc": "攻击 30% 概率吸血 15% 伤害"},
    },
    "石拳": {
        "class": "cls_wu_seng", "icon": "🥋", "quality": "blue",
        "bonus_2": {"atk": 0.08, "def": 0.05},
        "bonus_4_stats": {"hp": 0.10},
        "bonus_4": {"effect": "lifesteal_set", "chance": 0.3,
                    "desc": "攻击 30% 概率吸血 15% 伤害"},
    },
    "壁槌": {
        "class": "cls_wu_seng", "icon": "🥋", "quality": "purple",
        "bonus_2": {"atk": 0.08, "def": 0.05},
        "bonus_4_stats": {"hp": 0.10},
        "bonus_4": {"effect": "lifesteal_set", "chance": 0.3,
                    "desc": "攻击 30% 概率吸血 15% 伤害"},
    },
}

# ============================================================
# MERGE 指令 —— 主 agent 合并进对应数据文件
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
# 自检（python frag_class_b.py 运行）
# ============================================================
if __name__ == "__main__":
    import json
    import pathlib
    import sys

    errors = []

    # 1. 结构检查
    required_keys = ["EQUIP_ROSTER", "SERIES_FIXED_AFFIX", "SERIES_SETS",
                     "EQ_SERIES_THEME", "MATERIALS", "CRAFT_RECIPES",
                     "MAT_DROP_MAP", "CLASS_SET_BONUS"]
    for k in required_keys:
        if k not in MERGE:
            errors.append(f"MERGE 缺少键: {k}")

    # 2. 数量检查
    counts = {k: len(MERGE.get(k, {})) for k in required_keys}
    if counts["EQUIP_ROSTER"] != 45:
        errors.append(f"EQUIP_ROSTER 应为 45 条，实际 {counts['EQUIP_ROSTER']}")
    if counts["SERIES_FIXED_AFFIX"] != 45:
        errors.append(f"SERIES_FIXED_AFFIX 应为 45 条，实际 {counts['SERIES_FIXED_AFFIX']}")
    if counts["CRAFT_RECIPES"] != 45:
        errors.append(f"CRAFT_RECIPES 应为 45 条，实际 {counts['CRAFT_RECIPES']}")
    if counts["SERIES_SETS"] != 9:
        errors.append(f"SERIES_SETS 应为 9 条，实际 {counts['SERIES_SETS']}")
    if counts["EQ_SERIES_THEME"] != 9:
        errors.append(f"EQ_SERIES_THEME 应为 9 条，实际 {counts['EQ_SERIES_THEME']}")
    if counts["CLASS_SET_BONUS"] != 9:
        errors.append(f"CLASS_SET_BONUS 应为 9 条，实际 {counts['CLASS_SET_BONUS']}")

    # 3. 与 naming_plan.json 一致性（防重名）
    plan_path = pathlib.Path(__file__).parent / "naming_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    expected = set()
    for cls_key, stages in plan["class_sets"].items():
        if cls_key not in ("cls_you_xia", "cls_ci_ke", "cls_wu_seng"):
            continue
        for stage in stages.values():
            expected.add(stage["w"])
            expected.update(stage["parts"])
    roster_names = {e["name"] for e in MERGE["EQUIP_ROSTER"].values()}
    if roster_names != expected:
        missing = expected - roster_names
        extra = roster_names - expected
        if missing:
            errors.append(f"名册缺少计划内名字: {sorted(missing)}")
        if extra:
            errors.append(f"名册出现计划外名字: {sorted(extra)}")
    if len(roster_names) != len(MERGE["EQUIP_ROSTER"]):
        errors.append("名册 name 存在重复")

    # 4. 配方 roster_id 与名册一一对应
    rec_ids = {r["roster_id"] for r in MERGE["CRAFT_RECIPES"].values()}
    if rec_ids != set(MERGE["EQUIP_ROSTER"]):
        errors.append("CRAFT_RECIPES 的 roster_id 与 EQUIP_ROSTER 不一致")

    # 5. 配方字段校验
    valid_slots = {"weapon", "helm", "armor", "legs", "boots"}
    for rid, r in MERGE["CRAFT_RECIPES"].items():
        if r["slot"] not in valid_slots:
            errors.append(f"{rid} slot 非法: {r['slot']}")
        if r["quality"] not in ("blue", "purple"):
            errors.append(f"{rid} quality 非法: {r['quality']}")
        if r["lv"] not in (10, 30, 50):
            errors.append(f"{rid} lv 非法: {r['lv']}")
        if r["slot"] == "weapon" and "weapon_type" not in r:
            errors.append(f"{rid} 武器配方缺少 weapon_type")
        expect_gold = r["lv"] * (11 if r["quality"] == "purple" else 9)
        if r["gold"] != expect_gold:
            errors.append(f"{rid} gold 应为 {expect_gold}，实际 {r['gold']}")
        if r["quality"] == "purple" and "blueprint" not in r:
            errors.append(f"{rid} 紫装缺少 blueprint")

    # 6. 词条存在性（读 AFFIXES 源码确认 id 已定义）
    affix_src = pathlib.Path(__file__).parent.parent.parent / "game" / "data" / "affixes.py"
    affix_text = affix_src.read_text(encoding="utf-8")
    known = {"swift", "crit_up", "crit_dmg", "combo", "execute", "pene_phys",
             "tenacity", "block", "counter", "charge", "lifesteal", "precise", "hunt", "dodge"}
    for name, affs in MERGE["SERIES_FIXED_AFFIX"].items():
        for a in affs:
            if a not in known:
                errors.append(f"{name} 词条 {a} 不在已知集合")
            if f'"{a}"' not in affix_text:
                errors.append(f"{name} 词条 {a} 未在 affixes.py 定义")

    # 7. 词条 kind 约束：武器用 attack，防具用 defense（dodge/swift 为 defense）
    attack_kind = {"crit_up", "crit_dmg", "combo", "execute", "pene_phys",
                   "precise", "hunt", "charge", "counter", "lifesteal"}
    defense_kind = {"tenacity", "block", "swift", "dodge"}
    slot_of = {e["name"]: e["slot"] for e in MERGE["EQUIP_ROSTER"].values()}
    for name, affs in MERGE["SERIES_FIXED_AFFIX"].items():
        slot = slot_of.get(name)
        if not slot:
            continue
        for a in affs:
            if slot == "weapon" and a in defense_kind:
                errors.append(f"{name}(weapon) 用了防御词条 {a}")
            if slot != "weapon" and a in attack_kind:
                errors.append(f"{name}({slot}) 用了攻击词条 {a}")

    # 8. 素材引用校验（本片段不应定义新素材；全部须为 A 片段/items.py 已有）
    mats_used = set()
    for r in MERGE["CRAFT_RECIPES"].values():
        mats_used.update(r["mats"].keys())
    mats_expected = {"mat_lang_pi", "mat_ye_zhu_pi", "mat_shan_zei_hui_zhang",
                     "mat_shu_shi_he_xin", "mat_shou_ren_liao_ya", "mat_zuo_lang_quan_chi",
                     "mat_sheng_guang_jie_jing", "mat_yue_ying_zhi_pi", "mat_long_yan_jing_hua"}
    if mats_used != mats_expected:
        errors.append(f"素材引用不匹配: {sorted(mats_used - mats_expected)} / {sorted(mats_expected - mats_used)}")
    if MERGE["MATERIALS"]:
        errors.append("MATERIALS 应留空（素材由 A 片段定义）")

    # 9. CLASS_SET_BONUS 校验
    for name, b in MERGE["CLASS_SET_BONUS"].items():
        if b["class"] not in ("cls_you_xia", "cls_ci_ke", "cls_wu_seng"):
            errors.append(f"{name} class 非法: {b['class']}")
        if name not in MERGE["SERIES_SETS"]:
            errors.append(f"{name} 不在 SERIES_SETS")
        if "bonus_2" not in b or "bonus_4_stats" not in b or "bonus_4" not in b:
            errors.append(f"{name} 套装 bonus 结构不完整")

    # 汇总
    print("== frag_class_b 自检 ==")
    for k in required_keys:
        print(f"  {k}: {counts[k]} 条")
    if errors:
        print("❌ 发现错误:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("✅ 全部通过：EQUIP_ROSTER 45 / SERIES_FIXED_AFFIX 45 / SERIES_SETS 9 / "
          "EQ_SERIES_THEME 9 / CLASS_SET_BONUS 9 / CRAFT_RECIPES 45，名字与 naming_plan 一致")
