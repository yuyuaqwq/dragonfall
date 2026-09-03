# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年数据层 - refine_exclusive.py（v172 路B：重锻专属装备）

重锻独有 = 只靠『装备重锻』从旧装备派生、别处（图纸/Boss掉落/商店/铁匠铺货架/锻造）都得不到。
- 旧装备（源）= 职业锻造套（铁皮/学徒/布衣/猎手/轻影/行者 Lv10 蓝 → 精铁/符文/祝福/风行/夜行/石拳 Lv30 蓝），
  走既有 锻造 配方可得（玩家先锻造/商店获得，再拿去重锻）。
- 新装备（target）= source=重锻 名册装备（EQUIP_ROSTER，无锻造配方/无图纸），本表以 roster rid 为目标，
  与 EVOLVE_RECIPES(REFINE_RECIPES) 以 CRAFT_RECIPES 配方 key 为目标不同——重锻专属没有配方，
  命令层须走 generate_roster_equip(rid) 精确生成（不能 craft_recipe_make——它查 CRAFT_RECIPES 会查不到）。
  接口：economy.py（路 A 改名 refine_equip 时）查找重锻配方须并查 REFINE_RECIPES 与 REFINE_EXCLUSIVE_RECIPES
  两张表；命中 EXCLUSIVE 时 target 为 roster rid，用 C.generate_roster_equip(rid) 生成。
- mats：Boss 稀有素材（精华/兽材/传说）+ 常规材料，与现有 EVOLVE 链同量级。
- inherit: half（与既有链一致，投资不沉没但折半）。

merge_into()：供命令层/主 agent 一次性合并进 REFINE_RECIPES 查找池（不改本文件结构；
若路 A 直接在 economy.py 并查两表则无需调用本函数）。
"""
REFINE_EXCLUSIVE_RECIPES = {
    # ============ 战士（铁皮→壁垒 / 精铁→壁垒军团）============
    "铁皮长剑": {
        "target": "eq_bilei_zhanjian",          # 壁垒战剑 Lv31 紫（roster rid）
        "mats": {
            "mat_jing_tie_ding": 6,              # 精铁锭
            "mat_jin_he": 2,                     # 烬核（Boss 稀有素材）
            "mat_yan_long_lin": 1,               # 岩龙鳞
        },
        "gold": 320,
        "inherit": "half",
        "desc": "铁皮长剑叠上精铁甲片重锻，剑脊如城墙——壁垒战剑（重锻独有，继承一半强化/升级）",
    },
    "精铁战剑": {
        "target": "eq_bilei_juntuan_zhanjian",   # 壁垒军团战剑 Lv52 橙
        "mats": {
            "mat_hei_tie_ding": 8,               # 黑铁锭
            "mat_zhan_hun_zhi_chen": 1,          # 战魂之尘（Boss 稀有素材）
            "mat_jin_he_zhi_xin": 1,             # 烬核之心
        },
        "gold": 1200,
        "inherit": "half",
        "desc": "精铁战剑熔入烬核余火，烙上军团壁垒徽记——壁垒军团战剑（重锻独有，继承一半强化/升级）",
    },
    # ============ 法师（学徒→铭文法典 / 符文→铭刻法典）============
    "见习法杖": {
        "target": "eq_mingwen_fadian_zhizhang",  # 铭文法典之杖 Lv31 紫
        "mats": {
            "mat_yin_ling_si": 6,                # 银铃丝
            "mat_mo_yan_zhi_he": 2,              # 魔眼之核（Boss 稀有素材）
            "mat_sheng_guang_jie_jing": 1,       # 圣光结晶
        },
        "gold": 320,
        "inherit": "half",
        "desc": "学徒法杖的潦草魔文誊成整页铭文，字字生辉——铭文法典之杖（重锻独有，继承一半强化/升级）",
    },
    "符文法杖": {
        "target": "eq_mingke_fadian_zhizhang",   # 铭刻法典之杖 Lv52 橙
        "mats": {
            "mat_fu_wen_duan": 8,                # 符文绸
            "mat_ling_hun_sui_pian": 1,          # 灵魂碎片（Boss 稀有素材）
            "mat_yun_xing_he": 1,                # 陨星核
        },
        "gold": 1200,
        "inherit": "half",
        "desc": "符文法杖的符文逐一錾进银脊，如使徒印章——铭刻法典之杖（重锻独有，继承一半强化/升级）",
    },
    # ============ 牧师（布衣→贤者法典 / 祝福→辉光）============
    "布衣权杖": {
        "target": "eq_xianzhe_fadian_zhizhang",  # 贤者法典之杖 Lv31 紫
        "mats": {
            "mat_yin_ling_si": 6,                # 银铃丝
            "mat_moonlight_essence": 1,          # 月辉精魄（Boss 稀有素材）
            "mat_bai_lu_jiao": 1,                # 白鹿角
        },
        "gold": 320,
        "inherit": "half",
        "desc": "布衣权杖经贤者之手重铸，杖首圣辉凝成书页纹——贤者法典之杖（重锻独有，继承一半强化/升级）",
    },
    "祝福权杖": {
        "target": "eq_huiguang_shengzhang",      # 辉光圣杖 Lv52 橙
        "mats": {
            "mat_sheng_hui_rong": 8,             # 圣辉绒
            "mat_ye_dao_zhi_xin": 1,             # 夜祷之心（Boss 稀有素材）
            "mat_gu_long_lin": 1,                # 古龙鳞
        },
        "gold": 1200,
        "inherit": "half",
        "desc": "祝福权杖在圣辉泉水中浸炼七日，辉光流转——辉光圣杖（重锻独有，继承一半强化/升级）",
    },
    # ============ 游侠（猎手→巡猎 / 风行→远征）============
    "猎手短弓": {
        "target": "eq_xunlie_changgong",         # 巡猎长弓 Lv31 紫
        "mats": {
            "mat_qing_xiang_mu": 6,              # 青橡木
            "mat_feng_zhi_yu": 2,                # 风之羽（Boss 稀有素材）
            "mat_lie_huo_mu": 1,                 # 猎火木
        },
        "gold": 320,
        "inherit": "half",
        "desc": "猎手短弓换林线巡守者弓弦，箭路直追奔鹿——巡猎长弓（重锻独有，继承一半强化/升级）",
    },
    "风行长弓": {
        "target": "eq_yuanzheng_zhigong",        # 远征之弓 Lv52 橙
        "mats": {
            "mat_lie_feng_zhi_mu": 8,            # 猎风之木
            "mat_feng_bao_ying_yu": 1,           # 风暴鹰羽（Boss 稀有素材）
            "mat_tian_ying_yu": 1,               # 天鹰羽
        },
        "gold": 1200,
        "inherit": "half",
        "desc": "风行长弓弓胎经远征军匠师重校，弦响如号角——远征之弓（重锻独有，继承一半强化/升级）",
    },
    # ============ 刺客（轻影→夜行 / 夜行→暗夜）============
    "轻影匕首": {
        "target": "eq_yexing_duanren",           # 夜行短刃 Lv31 紫
        "mats": {
            "mat_ying_zhi_ge": 6,                # 硬皮革
            "mat_an_ying_jing_hua": 2,           # 暗影精华（Boss 稀有素材）
            "mat_jing_tie_ding": 1,              # 精铁锭
        },
        "gold": 320,
        "inherit": "half",
        "desc": "轻影匕首淬过月光重锻，刃身暗下时影子难寻——夜行短刃（重锻独有，继承一半强化/升级）",
    },
    "夜行匕首": {
        "target": "eq_anyezhi_ren",              # 暗夜之刃 Lv52 橙
        "mats": {
            "mat_ying_zhi_ge": 8,                # 硬皮革
            "mat_mu_ying_long_hun": 1,           # 暮影龙魂（Boss 稀有素材）
            "mat_shen_yuan_quan_ya": 1,          # 深渊犬牙
        },
        "gold": 1200,
        "inherit": "half",
        "desc": "夜行匕首在无星之夜重锻，出手只留一线暮影——暗夜之刃（重锻独有，继承一半强化/升级）",
    },
    # ============ 武僧（行者→镇岳 / 石拳→撼岳）============
    "行者拳套": {
        "target": "eq_zhenyue_quantao",          # 镇岳拳套 Lv31 紫
        "mats": {
            "mat_jing_tie_ding": 6,              # 精铁锭
            "mat_rong_yan_he_xin": 2,            # 熔岩核心（Boss 稀有素材）
            "mat_shi_cai": 1,                    # 石材
        },
        "gold": 320,
        "inherit": "half",
        "desc": "行者拳套缠上精铁链与山石之核，拳风如压山——镇岳拳套（重锻独有，继承一半强化/升级）",
    },
    "石拳拳套": {
        "target": "eq_hanyue_quan",              # 撼岳拳 Lv52 橙
        "mats": {
            "mat_hei_tie_ding": 8,               # 黑铁锭
            "mat_di_di_long_lin": 1,             # 地底龙鳞（Boss 稀有素材）
            "mat_gu_long_yi_jia": 1,             # 古龙裔甲
        },
        "gold": 1200,
        "inherit": "half",
        "desc": "石拳拳套以地脉精钢重铸，一拳山岳晃动——撼岳拳（重锻独有，继承一半强化/升级）",
    },
}


def merge_into(refine_recipes: dict) -> dict:
    """把 REFINE_EXCLUSIVE_RECIPES 并入既有重锻配方表（REFINE_RECIPES），返回新表。

    供命令层查找池合并用（不改动原表）：若路 A 已在 economy.py 直接并查两张表，
    则无需调用本函数。target 为名册 rid（无锻造配方）——命令层须以
    generate_roster_equip(rid) 生成，而不是 craft_recipe_make(配方 key)。
    """
    merged = dict(refine_recipes or {})
    for _src, _cfg in REFINE_EXCLUSIVE_RECIPES.items():
        merged.setdefault(_src, _cfg)
    return merged
