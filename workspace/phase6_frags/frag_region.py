# -*- coding: utf-8 -*-
"""Phase 6 区域套片段（主 agent 修复版 2026-08-29）

5 资料片区域套 × 过渡/毕业 双档 × 3 件 = 30 件。
- 过渡档：原名（护林胸甲等），source=商店
- 毕业档：精制前缀（精制护林胸甲等），source=锻造/图纸
- 猎手系列在 task-3 已改名「霜猎」（与散装猎手系列区分）
"""

MERGE = {
    "EQUIP_ROSTER": {
        # ===== 一·橡木白鹿 护林套（过渡 Lv5 白 / 毕业 Lv15 蓝）=====
        "eq_hu_lin_xiong_jia": {"name": "护林胸甲", "slot": "armor", "quality": "white", "lv": 5, "series": "护林", "req": {"vit": 3}, "source": "商店"},
        "eq_hu_lin_hu_tui": {"name": "护林护腿", "slot": "legs", "quality": "white", "lv": 5, "series": "护林", "req": {"vit": 3}, "source": "商店"},
        "eq_hu_lin_zhi_xue": {"name": "护林之靴", "slot": "boots", "quality": "white", "lv": 5, "series": "护林", "req": {"vit": 3}, "source": "商店"},
        "eq_hu_lin_bai_lu_xiong_jia": {"name": "精制护林胸甲", "slot": "armor", "quality": "blue", "lv": 15, "series": "护林", "req": {"vit": 8}, "source": "锻造"},
        "eq_hu_lin_bai_lu_hu_tui": {"name": "精制护林护腿", "slot": "legs", "quality": "blue", "lv": 15, "series": "护林", "req": {"vit": 8}, "source": "锻造"},
        "eq_hu_lin_bai_lu_zhi_xue": {"name": "精制护林之靴", "slot": "boots", "quality": "blue", "lv": 15, "series": "护林", "req": {"vit": 8}, "source": "锻造"},
        # ===== 二·铁港晨曦 渡口套（过渡 Lv20 蓝 / 毕业 Lv32 紫）=====
        "eq_du_kou_xiong_jia": {"name": "渡口胸甲", "slot": "armor", "quality": "blue", "lv": 20, "series": "渡口", "req": {"agi": 18}, "source": "商店"},
        "eq_du_kou_hu_tui": {"name": "渡口护腿", "slot": "legs", "quality": "blue", "lv": 20, "series": "渡口", "req": {"agi": 18}, "source": "商店"},
        "eq_du_kou_zhi_xue": {"name": "渡口之靴", "slot": "boots", "quality": "blue", "lv": 20, "series": "渡口", "req": {"agi": 18}, "source": "商店"},
        "eq_du_kou_chen_xi_xiong_jia": {"name": "精制渡口胸甲", "slot": "armor", "quality": "purple", "lv": 32, "series": "渡口", "req": {"agi": 28}, "source": "图纸"},
        "eq_du_kou_chen_xi_hu_tui": {"name": "精制渡口护腿", "slot": "legs", "quality": "purple", "lv": 32, "series": "渡口", "req": {"agi": 28}, "source": "图纸"},
        "eq_du_kou_chen_xi_zhi_xue": {"name": "精制渡口之靴", "slot": "boots", "quality": "purple", "lv": 32, "series": "渡口", "req": {"agi": 28}, "source": "图纸"},
        # ===== 三·翡翠月语 巡林套（过渡 Lv40 蓝 / 毕业 Lv55 紫）=====
        "eq_xun_lin_xiong_jia": {"name": "巡林胸甲", "slot": "armor", "quality": "blue", "lv": 40, "series": "巡林", "req": {"agi": 38}, "source": "商店"},
        "eq_xun_lin_hu_tui": {"name": "巡林护腿", "slot": "legs", "quality": "blue", "lv": 40, "series": "巡林", "req": {"agi": 38}, "source": "商店"},
        "eq_xun_lin_zhi_xue": {"name": "巡林之靴", "slot": "boots", "quality": "blue", "lv": 40, "series": "巡林", "req": {"agi": 38}, "source": "商店"},
        "eq_xun_lin_yue_yu_xiong_jia": {"name": "精制巡林胸甲", "slot": "armor", "quality": "purple", "lv": 55, "series": "巡林", "req": {"agi": 50}, "source": "图纸"},
        "eq_xun_lin_yue_yu_hu_tui": {"name": "精制巡林护腿", "slot": "legs", "quality": "purple", "lv": 55, "series": "巡林", "req": {"agi": 50}, "source": "图纸"},
        "eq_xun_lin_yue_yu_zhi_xue": {"name": "精制巡林之靴", "slot": "boots", "quality": "purple", "lv": 55, "series": "巡林", "req": {"agi": 50}, "source": "图纸"},
        # ===== 四·霜角龙脊 霜猎套（过渡 Lv62 紫 / 毕业 Lv78 紫）=====
        "eq_shuang_lie_xiong_jia": {"name": "霜猎胸甲", "slot": "armor", "quality": "purple", "lv": 62, "series": "霜猎", "req": {"str": 60}, "source": "商店"},
        "eq_shuang_lie_hu_tui": {"name": "霜猎护腿", "slot": "legs", "quality": "purple", "lv": 62, "series": "霜猎", "req": {"str": 60}, "source": "商店"},
        "eq_shuang_lie_zhi_xue": {"name": "霜猎之靴", "slot": "boots", "quality": "purple", "lv": 62, "series": "霜猎", "req": {"str": 60}, "source": "商店"},
        "eq_shuang_lie_long_ji_xiong_jia": {"name": "精制霜猎胸甲", "slot": "armor", "quality": "purple", "lv": 78, "series": "霜猎", "req": {"str": 72}, "source": "图纸"},
        "eq_shuang_lie_long_ji_hu_tui": {"name": "精制霜猎护腿", "slot": "legs", "quality": "purple", "lv": 78, "series": "霜猎", "req": {"str": 72}, "source": "图纸"},
        "eq_shuang_lie_long_ji_zhi_xue": {"name": "精制霜猎之靴", "slot": "boots", "quality": "purple", "lv": 78, "series": "霜猎", "req": {"str": 72}, "source": "图纸"},
        # ===== 五·龙脊风翼 龙裔套（过渡 Lv82 紫 / 毕业 Lv95 橙）=====
        "eq_long_yi_xiong_jia": {"name": "龙裔胸甲", "slot": "armor", "quality": "purple", "lv": 82, "series": "龙裔", "req": {"str": 80}, "source": "商店"},
        "eq_long_yi_hu_tui": {"name": "龙裔护腿", "slot": "legs", "quality": "purple", "lv": 82, "series": "龙裔", "req": {"str": 80}, "source": "商店"},
        "eq_long_yi_zhi_xue": {"name": "龙裔之靴", "slot": "boots", "quality": "purple", "lv": 82, "series": "龙裔", "req": {"str": 80}, "source": "商店"},
        "eq_long_yi_feng_yi_xiong_jia": {"name": "精制龙裔胸甲", "slot": "armor", "quality": "orange", "lv": 95, "series": "龙裔", "req": {"str": 90}, "source": "图纸"},
        "eq_long_yi_feng_yi_hu_tui": {"name": "精制龙裔护腿", "slot": "legs", "quality": "orange", "lv": 95, "series": "龙裔", "req": {"str": 90}, "source": "图纸"},
        "eq_long_yi_feng_yi_zhi_xue": {"name": "精制龙裔之靴", "slot": "boots", "quality": "orange", "lv": 95, "series": "龙裔", "req": {"str": 90}, "source": "图纸"},
    },
    "SERIES_FIXED_AFFIX": {
        # 护林=防御自然向
        "护林胸甲": ["dmg_reduce"], "护林护腿": ["block"], "护林之靴": ["tenacity"],
        "精制护林胸甲": ["dmg_reduce", "block"], "精制护林护腿": ["block", "tenacity"], "精制护林之靴": ["tenacity", "dmg_reduce"],
        # 渡口=航海迅捷向
        "渡口胸甲": ["dodge"], "渡口护腿": ["swift"], "渡口之靴": ["swift"],
        "精制渡口胸甲": ["dodge", "swift"], "精制渡口护腿": ["swift", "dodge"], "精制渡口之靴": ["swift", "swift"],
        # 巡林=灵巧闪避向
        "巡林胸甲": ["dodge"], "巡林护腿": ["swift"], "巡林之靴": ["swift"],
        "精制巡林胸甲": ["dodge", "swift"], "精制巡林护腿": ["swift", "dodge"], "精制巡林之靴": ["swift", "precise"],
        # 霜猎=冰雪猎杀向（改名猎手→霜猎）
        "霜猎胸甲": ["element_ice", "tenacity"], "霜猎护腿": ["element_ice", "precise"], "霜猎之靴": ["swift", "hunt"],
        "精制霜猎胸甲": ["element_ice", "tenacity", "dmg_reduce"], "精制霜猎护腿": ["element_ice", "precise", "tenacity"], "精制霜猎之靴": ["swift", "hunt", "element_ice"],
        # 龙裔=龙威攻防向
        "龙裔胸甲": ["dragon_aw", "dmg_reduce"], "龙裔护腿": ["dragon_aw", "block"], "龙裔之靴": ["dragon_aw", "swift"],
        "精制龙裔胸甲": ["dragon_aw", "dmg_reduce", "block"], "精制龙裔护腿": ["dragon_aw", "block", "tenacity"], "精制龙裔之靴": ["dragon_aw", "swift", "hunt"],
    },
    "SERIES_SETS": {
        "护林": "护林套", "渡口": "渡口套", "巡林": "巡林套", "霜猎": "霜猎套", "龙裔": "龙裔套",
    },
    "EQ_SERIES_THEME": {
        "护林": "橡木白鹿的护林人装备，朴素耐用，沾着晨露与松针的气息",
        "渡口": "铁港晨曦渡口的行船装备，带着江风与潮水的咸涩",
        "巡林": "翡翠月语森林巡林者的轻装，灵巧如林间跃动的光斑",
        "霜猎": "霜角龙脊的猎手行装，抵御北境风雪，枪尖凝着寒霜",
        "龙裔": "龙脊风翼的龙裔武备，烙着龙焰纹章，重逾千钧",
    },
    "MATERIALS": {},
    "CRAFT_RECIPES": {
        # 毕业档 15 件（紫/橙带图纸）
        "rec_hu_lin_bai_lu_xiong_jia": {"slot": "armor", "quality": "blue", "lv": 15, "mats": {"mat_lang_pi": 5, "mat_ye_zhu_pi": 3}, "gold": 135, "desc": "橡木白鹿护林人精制的胸甲，结实耐用", "name": "精制护林胸甲", "roster_id": "eq_hu_lin_bai_lu_xiong_jia"},
        "rec_hu_lin_bai_lu_hu_tui": {"slot": "legs", "quality": "blue", "lv": 15, "mats": {"mat_lang_pi": 4, "mat_ye_zhu_pi": 3}, "gold": 135, "desc": "橡木白鹿护林人精制的护腿", "name": "精制护林护腿", "roster_id": "eq_hu_lin_bai_lu_hu_tui"},
        "rec_hu_lin_bai_lu_zhi_xue": {"slot": "boots", "quality": "blue", "lv": 15, "mats": {"mat_lang_pi": 3, "mat_ye_zhu_pi": 3}, "gold": 135, "desc": "橡木白鹿护林人精制的靴子", "name": "精制护林之靴", "roster_id": "eq_hu_lin_bai_lu_zhi_xue"},
        "rec_du_kou_chen_xi_xiong_jia": {"slot": "armor", "quality": "purple", "lv": 32, "mats": {"mat_tie_kuang_shi": 6, "mat_lang_pi": 4}, "gold": 352, "desc": "铁港晨曦渡口工匠的杰作", "name": "精制渡口胸甲", "roster_id": "eq_du_kou_chen_xi_xiong_jia", "blueprint": "精制渡口胸甲图纸"},
        "rec_du_kou_chen_xi_hu_tui": {"slot": "legs", "quality": "purple", "lv": 32, "mats": {"mat_tie_kuang_shi": 5, "mat_lang_pi": 3}, "gold": 352, "desc": "铁港晨曦渡口工匠的杰作", "name": "精制渡口护腿", "roster_id": "eq_du_kou_chen_xi_hu_tui", "blueprint": "精制渡口护腿图纸"},
        "rec_du_kou_chen_xi_zhi_xue": {"slot": "boots", "quality": "purple", "lv": 32, "mats": {"mat_tie_kuang_shi": 4, "mat_lang_pi": 3}, "gold": 352, "desc": "铁港晨曦渡口工匠的杰作", "name": "精制渡口之靴", "roster_id": "eq_du_kou_chen_xi_zhi_xue", "blueprint": "精制渡口之靴图纸"},
        "rec_xun_lin_yue_yu_xiong_jia": {"slot": "armor", "quality": "purple", "lv": 55, "mats": {"mat_tie_kuang_shi": 7, "mat_yue_guang_cao": 4}, "gold": 605, "desc": "翡翠月语巡林者的精制轻甲", "name": "精制巡林胸甲", "roster_id": "eq_xun_lin_yue_yu_xiong_jia", "blueprint": "精制巡林胸甲图纸"},
        "rec_xun_lin_yue_yu_hu_tui": {"slot": "legs", "quality": "purple", "lv": 55, "mats": {"mat_tie_kuang_shi": 6, "mat_yue_guang_cao": 3}, "gold": 605, "desc": "翡翠月语巡林者的精制护腿", "name": "精制巡林护腿", "roster_id": "eq_xun_lin_yue_yu_hu_tui", "blueprint": "精制巡林护腿图纸"},
        "rec_xun_lin_yue_yu_zhi_xue": {"slot": "boots", "quality": "purple", "lv": 55, "mats": {"mat_tie_kuang_shi": 5, "mat_yue_guang_cao": 3}, "gold": 605, "desc": "翡翠月语巡林者的精制靴子", "name": "精制巡林之靴", "roster_id": "eq_xun_lin_yue_yu_zhi_xue", "blueprint": "精制巡林之靴图纸"},
        "rec_shuang_lie_long_ji_xiong_jia": {"slot": "armor", "quality": "purple", "lv": 78, "mats": {"mat_tie_kuang_shi": 8, "mat_shuang_ju_mo_xue": 4}, "gold": 858, "desc": "霜角龙脊猎手的精制胸甲", "name": "精制霜猎胸甲", "roster_id": "eq_shuang_lie_long_ji_xiong_jia", "blueprint": "精制霜猎胸甲图纸"},
        "rec_shuang_lie_long_ji_hu_tui": {"slot": "legs", "quality": "purple", "lv": 78, "mats": {"mat_tie_kuang_shi": 7, "mat_shuang_ju_mo_xue": 3}, "gold": 858, "desc": "霜角龙脊猎手的精制护腿", "name": "精制霜猎护腿", "roster_id": "eq_shuang_lie_long_ji_hu_tui", "blueprint": "精制霜猎护腿图纸"},
        "rec_shuang_lie_long_ji_zhi_xue": {"slot": "boots", "quality": "purple", "lv": 78, "mats": {"mat_tie_kuang_shi": 6, "mat_shuang_ju_mo_xue": 3}, "gold": 858, "desc": "霜角龙脊猎手的精制靴子", "name": "精制霜猎之靴", "roster_id": "eq_shuang_lie_long_ji_zhi_xue", "blueprint": "精制霜猎之靴图纸"},
        "rec_long_yi_feng_yi_xiong_jia": {"slot": "armor", "quality": "orange", "lv": 95, "mats": {"mat_long_lin": 4, "mat_tie_kuang_shi": 10}, "gold": 1235, "desc": "龙脊风翼的龙裔秘制胸甲", "name": "精制龙裔胸甲", "roster_id": "eq_long_yi_feng_yi_xiong_jia", "blueprint": "精制龙裔胸甲图纸"},
        "rec_long_yi_feng_yi_hu_tui": {"slot": "legs", "quality": "orange", "lv": 95, "mats": {"mat_long_lin": 3, "mat_tie_kuang_shi": 9}, "gold": 1235, "desc": "龙脊风翼的龙裔秘制护腿", "name": "精制龙裔护腿", "roster_id": "eq_long_yi_feng_yi_hu_tui", "blueprint": "精制龙裔护腿图纸"},
        "rec_long_yi_feng_yi_zhi_xue": {"slot": "boots", "quality": "orange", "lv": 95, "mats": {"mat_long_lin": 3, "mat_tie_kuang_shi": 8}, "gold": 1235, "desc": "龙脊风翼的龙裔秘制靴子", "name": "精制龙裔之靴", "roster_id": "eq_long_yi_feng_yi_zhi_xue", "blueprint": "精制龙裔之靴图纸"},
    },
    "MAT_DROP_MAP": {},
}
