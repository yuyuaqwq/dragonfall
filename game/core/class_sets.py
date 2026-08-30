# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - class_sets.py（阶段八重写，2026-08-06）

10 章五节名册套装注册：9 系列 5 件套（头盔/胸甲/护腿/鞋子/项链）。
- bonus_2：2 件属性百分比（引擎 set_bonus_2 消费）
- bonus_4_stats：4 件属性百分比（engine.set_bonus_2 叠加，>=4 件生效）
- bonus_4.effect：4 件特效（战斗触发型，保留旧结构兼容）
- bonus_5：5 件效果（v104 起战斗落地：battle 对敌增伤/元素增伤、battle_mech 抗寒）
- 治疗加成（圣光套 2 件）由 battle 治疗段消费（bonus_2.heal 字段）

⚠️ 旧世界毕业套（CLASS_SET_THEMES 6 职业×5 阶段）已废弃：不再动态合并进 CRAFT_RECIPES，
锻造配方 = 10 章名册（craft.py）。旧 SETS 42 条仍残留在 data/sets.py（兼容旧档 set 字段，
待确认后清理）；名册套装由 _assembly 调 _build_class_sets 注册/覆盖同名 key，不删除旧数据。
"""

from ..data import CRAFT_RECIPES, SERIES_SETS, SETS, WT_CN
from ..core.index import pinyin_id

# 10 章五节套装效果表（5 件特效 v104 起战斗落地：battle.py 对敌/元素增伤、battle_mech.py 抗寒）
_SERIES_SET_BONUS = {
    "橡木": {
        "icon": "🌳", "quality": "white",
        "bonus_2": {"atk": 0.05, "bonus_5": {"desc": "橡木猎牙：对野兽系敌人伤害 +10%"}, "bonus_5_cond": {"enemy_contains": ["狼", "猪", "兔", "鹿", "熊", "牛", "羊", "狐", "虎", "豹"], "dmg_mult": 1.10, "tag": "🌳橡木猎牙"}},
        "bonus_4_stats": {"hp": 0.10},
        "bonus_5": {"crit": 0.05, "desc": "暴击＋5%"},
    },
    "铁港": {
        "icon": "⚓", "quality": "blue",
        "bonus_2": {"spd": 0.10, "bonus_5": {"desc": "海风斩浪：对水手海盗系敌人伤害 +10%"}, "bonus_5_cond": {"enemy_contains": ["水手", "海盗", "水鬼", "溺亡"], "dmg_mult": 1.10, "tag": "⚓海风斩浪"}},
        "bonus_4_stats": {"atk": 0.08},
        "bonus_5": {"dodge": 0.05, "desc": "闪避＋5%"},
    },
    "圣光": {
        "icon": "✨", "quality": "blue",
        # v110 审计修复：bonus_2 键原为 "heal"（heal ∉ STAT_NAMES）→ engine 属性结算
        # KeyError 崩溃（穿 2 件圣光套必现）。heal_power ∈ PCT_STATS（cap 0.5）且
        # battle.py 治疗段消费（×（1+heal_power））——"治疗+10%"设计经属性体系达成，
        # 与旧 CLASS_SET 圣徽圣愈/晨光圣愈（sets.py 均用 heal_power）同构。
        "bonus_2": {"heal_power": 0.10},
        "bonus_4_stats": {"def": 0.08},
        "bonus_5": {"desc": "圣光增伤＋10%（对暗影/亡灵系敌人）"},
        # v126 数值下沉：5 件对敌增伤条件（敌方名字关键词）从数据声明，battle 查表消费
        "bonus_5_cond": {"enemy_contains": ["暗", "影", "亡", "鬼", "骨", "骷髅"],
                         "dmg_mult": 1.10, "tag": "✨圣光克暗"},
    },
    "月语": {
        "icon": "🌙", "quality": "purple",
        "bonus_2": {"crit": 0.08},
        "bonus_4_stats": {"spd": 0.10},   # 敏捷 +10% ≈ 速度 +10%
        "bonus_5": {"desc": "冰系增伤＋10%（月语/海神套，冰系技能）"},
    },
    "霜狼": {
        "icon": "🐺", "quality": "purple",
        "bonus_2": {"def": 0.10},
        "bonus_4_stats": {"atk": 0.08},
        "bonus_5": {"desc": "抗寒：免疫减速"},
    },
    "龙脊": {
        "icon": "🐉", "quality": "purple",
        "bonus_2": {"mdef": 0.10},   # 魔抗 +10%
        "bonus_4_stats": {"atk": 0.08},
        "bonus_5": {"desc": "龙息增伤＋10%（对龙系敌人）"},
        "bonus_5_cond": {"enemy_contains": ["龙"],
                         "dmg_mult": 1.10, "tag": "🐉龙息追猎"},
    },
    "海神": {
        "icon": "🌊", "quality": "purple",
        "bonus_2": {"mdef": 0.10},   # 水抗 +10% ≈ 魔抗 +10%
        "bonus_4_stats": {"atk": 0.08},
        "bonus_5": {"desc": "冰系增伤＋10%（月语/海神套，冰系技能）"},
    },
    "地底": {
        "icon": "🕳️", "quality": "purple",
        "bonus_2": {"mdef": 0.10},   # 暗抗 +10% ≈ 魔抗 +10%
        "bonus_4_stats": {"def": 0.08},
        "bonus_5": {"desc": "深渊增伤＋10%（对深渊系敌人）"},
        "bonus_5_cond": {"enemy_contains": ["深渊"],
                         "dmg_mult": 1.10, "tag": "🕳️深渊共鸣"},
    },
    "苍穹": {
        "icon": "☁️", "quality": "purple",
        "bonus_2": {"mdef": 0.10},   # 风抗 +10% ≈ 魔抗 +10%
        "bonus_4_stats": {"crit": 0.08},
        "bonus_5": {"desc": "雷系增伤＋10%（雷系技能）"},
    },
    # v93 商店装：白鹿绿装套（敏捷/闪避风格）
    "白鹿": {
        "icon": "🦌", "quality": "green",
        "bonus_2": {"dodge": 0.05, "bonus_5": {"desc": "白鹿逐迹：对林间毒物野兽伤害 +10%"}, "bonus_5_cond": {"enemy_contains": ["野狗", "毒蛇", "马蜂", "蜘蛛", "野兔"], "dmg_mult": 1.10, "tag": "🦌白鹿逐迹"}},
        "bonus_4_stats": {"spd": 0.08},
        "bonus_5": {"crit": 0.03, "desc": "暴击＋3%"},
    },
    # v101.25e 商店断层补档：银铃/翡翠/迷雾蓝装套（敏捷/闪避风格）
    "银铃": {
        "icon": "🔔", "quality": "blue",
        "bonus_2": {"spd": 0.10, "bonus_5": {"desc": "银铃潮音：对水族敌人伤害 +10%"}, "bonus_5_cond": {"enemy_contains": ["鲛人", "湖妖", "河龙", "漩涡", "水灵", "水母"], "dmg_mult": 1.10, "tag": "🔔银铃潮音"}},
        "bonus_4_stats": {"atk": 0.08},
        "bonus_5": {"dodge": 0.05, "desc": "闪避＋5%"},
    },
    "翡翠": {
        "icon": "💎", "quality": "blue",
        "bonus_2": {"dodge": 0.08, "bonus_5": {"desc": "翡翠森语：对林地魔物伤害 +10%"}, "bonus_5_cond": {"enemy_contains": ["树人", "哥布林", "古树", "藤蔓", "精灵兽"], "dmg_mult": 1.10, "tag": "💎翡翠森语"}},
        "bonus_4_stats": {"spd": 0.10},
        "bonus_5": {"crit": 0.05, "desc": "暴击＋5%"},
    },
    "迷雾": {
        "icon": "🌫️", "quality": "blue",
        "bonus_2": {"dodge": 0.08},
        "bonus_4_stats": {"mdef": 0.08},
        "bonus_5": {"desc": "迷雾增伤＋10%（对沼泽/毒腐系敌人）"},
        "bonus_5_cond": {"enemy_contains": ["沼泽", "毒", "腐", "瘴"],
                         "dmg_mult": 1.10, "tag": "🌫️迷雾侵染"},
    },
    # v87 隐藏线（10 章 10.1/10.2）
    "星尘": {
        "icon": "✨", "quality": "purple",
        "bonus_2": {"atk": 0.05, "matk": 0.05, "def": 0.05, "spd": 0.05},
        "bonus_4_stats": {"matk": 0.08},
        "bonus_5": {"desc": "星尘祝福：夜间(19:00-06:00)每回合回蓝 5%"},
    },
    "灰烬守卫": {
        "icon": "🔥", "quality": "orange",
        "bonus_2": {"mdef": 0.10},
        "bonus_4_stats": {"def": 0.08},
        "bonus_5": {"desc": "灰烬祝福：生命低于 30% 时攻击＋20%"},
        "bonus_5_cond": {"player_hp_below": 0.30,
                         "dmg_mult": 1.20, "tag": "🔥灰烬之怒"},
    },

    # ===== v136 Phase6 合并: CLASS_SET_BONUS (18 条) =====
    '铁皮': {'class': 'cls_zhan_shi', 'icon': '🛡️', 'quality': 'blue', 'bonus_2': {'atk': 0.08, 'def': 0.08}, 'bonus_4_stats': {'def': 0.1}, 'bonus_4': {'effect': 'tie_pi_harden', 'chance': 0.3, 'params': {'type': 'taken_def_up_stack', 'chance': 0.30, 'def_pct': 0.15, 'turns': 2, 'max_stacks': 2, 'tag': '🛡️', 'name': '铁皮厚盾'}, 'desc': '受击 30% 概率防御 +15%（2 回合，可叠 2 层）'}}, 'bonus_5_cond': {'enemy_contains': ["魔像", "甲虫", "龙虾", "巨龟", "石龙", "石蜥"], 'dmg_mult': 1.10, 'tag': '🛡️铁皮破甲'},
    '精铁': {'class': 'cls_zhan_shi', 'icon': '🛡️', 'quality': 'blue', 'bonus_2': {'atk': 0.08, 'def': 0.08}, 'bonus_4_stats': {'def': 0.1}, 'bonus_4': {'effect': 'jing_tie_edge', 'chance': 0.4, 'params': {'type': "proc_flat_dmg", "chance": 0.4, "stat": "atk", "pct": 0.15, "dmg_type": "true", "tag": "⚔️", "name": "精铁锋刃"}, 'desc': '攻击命中 40% 概率本次攻击无视 15% 防御'}}, 'bonus_5_cond': {'enemy_contains': ["骑士", "守卫", "弓手", "哨兵", "卫兵", "士兵"], 'dmg_mult': 1.10, 'tag': '⚔️精铁克兵'},
    '百炼': {'class': 'cls_zhan_shi', 'icon': '⚔️', 'quality': 'purple', 'bonus_2': {'atk': 0.08, 'def': 0.08}, 'bonus_4_stats': {'def': 0.1}, 'bonus_4': {'effect': 'bai_lian_forge', 'params': {'type': "proc_buff", "chance": 1.0, "buff_key": "bai_lian_lv", "buff_mode": "stack", "buff_max": 10, "tag": "🔨", "name": "百炼"}, 'desc': '每次攻击命中叠 1 层百炼（自身攻击 +2%，上限 10 层）'}}, 'bonus_5_cond': {'enemy_contains': ["巨魔", "兽人", "食人魔", "矮人"], 'dmg_mult': 1.10, 'tag': '🔨百炼克蛮'},
    '学徒': {'class': 'cls_fa_shi', 'icon': '🔮', 'quality': 'blue', 'bonus_2': {'matk': 0.08, 'cdr': 0.05}, 'bonus_4_stats': {'matk': 0.1}, 'bonus_4': {'effect': 'xue_tu_surge', 'params': {'type': "proc_buff", "chance": 1.0, "buff_key": "xue_tu_surge_lv", "buff_mode": "stack", "buff_max": 3, "tag": "⚡", "name": "蓄能"}, 'desc': '每次攻击命中叠 1 层蓄能（下次雷击伤害 +10%，上限 3 层）'}}, 'bonus_5_cond': {'enemy_contains': ["元素", "风灵", "星灵", "幽灵", "幽魂", "怨灵", "灵体"], 'dmg_mult': 1.10, 'tag': '🔮学徒驱灵'},
    '符文': {'class': 'cls_fa_shi', 'icon': '🔮', 'quality': 'blue', 'bonus_2': {'matk': 0.08, 'cdr': 0.05}, 'bonus_4_stats': {'matk': 0.1}, 'bonus_4': {'effect': 'fu_wen_annihilate', 'chance': 0.3, 'params': {'type': "proc_thunder_burst", "chance": 0.3, "stat": "matk", "max_mark": 3, "burst_pct": 0.9, "edef": "mdef", "tag": "📜", "name": "符文爆印"}, 'desc': '攻击命中 30% 概率叠 1 层雷印记；印记 ≥3 时引爆造成 90% 魔攻雷伤并清印'}}, 'bonus_5_cond': {'enemy_contains': ["傀儡", "机械", "石像", "图腾", "机关"], 'dmg_mult': 1.10, 'tag': '📜符文破构'},
    '秘法': {'class': 'cls_fa_shi', 'icon': '✨', 'quality': 'purple', 'bonus_2': {'matk': 0.08, 'cdr': 0.05}, 'bonus_4_stats': {'matk': 0.1}, 'bonus_4': {'effect': 'mi_fa_condense', 'chance': 0.25, 'params': {'type': "proc_mp_on_dmg", "chance": 0.25, "stat": "matk", "pct": 0.4, "mp_pct": 0.15, "edef": "mdef", "dmg_type": "magic", "tag": "✨", "name": "秘术回响"}, 'desc': '攻击命中 25% 概率追加 40% 魔攻雷击并回复该次伤害 15% 的魔力'}}, 'bonus_5_cond': {'enemy_contains': ["恶魔", "堕落", "邪教", "黑暗", "腐朽"], 'dmg_mult': 1.10, 'tag': '✨秘法伏魔'},
    '布衣': {'class': 'cls_mu_shi', 'icon': '☀️', 'quality': 'blue', 'bonus_2': {'heal_power': 0.08, 'mdef': 0.05, 'hp': 0.05}, 'bonus_4_stats': {'mdef': 0.1}, 'bonus_4': {'effect': 'cloth_heal_overflow', 'desc': '治疗技能治疗量 +8%；治疗溢出时溢出量 50% 转化为护盾'}}, 'bonus_5_cond': {'enemy_contains': ["祭司", "萨满", "巫师", "术士", "法师", "神官"], 'dmg_mult': 1.10, 'tag': '☀️布衣圣言'},
    '祝福': {'class': 'cls_mu_shi', 'icon': '☀️', 'quality': 'blue', 'bonus_2': {'heal_power': 0.10, 'mdef': 0.05}, 'bonus_4_stats': {'mdef': 0.1}, 'bonus_4': {'effect': 'bless_ward_shield', 'chance': 0.25, 'params': {'type': 'taken_shield', 'chance': 0.25, 'shield_pct': 0.08, 'shield_turns': 3, 'tag': '☀️', 'name': '圣徽守护'}, 'desc': '被攻击命中 25% 概率获得 8% 最大生命护盾（3 回合）'}}, 'bonus_5_cond': {'enemy_contains': ["蝙蝠", "蠕虫", "水蛭", "巨蝎", "蜈蚣"], 'dmg_mult': 1.10, 'tag': '☀️祝福护洁'},
    '圣堂': {'class': 'cls_mu_shi', 'icon': '⛪', 'quality': 'purple', 'bonus_2': {'heal_power': 0.08, 'mdef': 0.08}, 'bonus_4_stats': {'mdef': 0.1}, 'bonus_4': {'effect': 'holy_bastion_def', 'params': {'type': 'taken_dmg_reduce_flat', 'reduce_pct': 0.05, 'tag': '⛪', 'name': '圣堂壁垒'}, 'desc': '受击伤害 -5%（圣堂壁垒）'}}, 'bonus_5_cond': {'enemy_contains': ["血祭", "暗影", "腐化", "异端", "亵渎"], 'dmg_mult': 1.10, 'tag': '⛪圣堂裁罪'},
    '猎手': {'class': 'cls_you_xia', 'icon': '🏹', 'quality': 'blue', 'bonus_2': {'spd': 0.06, 'crit': 0.04}, 'bonus_4_stats': {'spd': 0.08}, 'bonus_4': {'effect': 'hunt_pack', 'chance': 0.3, 'params': {'type': "proc_flat_dmg", "chance": 0.3, "stat": "atk", "pct": 0.5, "pct_alt": 0.6, "cond_hp_lt": 0.5, "tag": "🏹", "name": "狩猎本能"}, 'desc': '攻击命中 30% 概率追加 50% 攻击力追击（对生命 <50% 敌人 +20%）'}}, 'bonus_5_cond': {'enemy_contains': ["狼王", "王·", "领主", "酋长", "魔王", "龙王"], 'dmg_mult': 1.10, 'tag': '🏹猎手枭首'},
    '风行': {'class': 'cls_you_xia', 'icon': '🏹', 'quality': 'blue', 'bonus_2': {'spd': 0.10}, 'bonus_4_stats': {'spd': 0.08}, 'bonus_4': {'stats': {'spd': 0.06, 'dodge': 0.04}, 'desc': '速度 +6%、闪避 +4%（风行加护）'}}, 'bonus_5_cond': {'enemy_contains': ["鹰", "雷鸟", "鸦", "鸥", "雕", "隼", "鹦鹉"], 'dmg_mult': 1.10, 'tag': '🌪️风行逐空'},
    '暗夜': {'class': 'cls_you_xia', 'icon': '🏹', 'quality': 'purple', 'bonus_2': {'crit': 0.04, 'dodge': 0.03}, 'bonus_4_stats': {'spd': 0.08}, 'bonus_4': {'effect': 'shadow_track', 'chance': 0.3, 'params': {'type': "proc_mark", "chance": 0.3, "max_mark": 5, "mark_desc": "暗影标记", "tag": "🌑", "name": "暗影追踪"}, 'desc': '攻击命中 30% 概率叠 1 层暗影标记；对带标记目标每层额外 +5% 伤害'}}, 'bonus_5_cond': {'enemy_contains': ["月狼", "月熊", "影豹", "月影", "荧光狐", "极光狐"], 'dmg_mult': 1.10, 'tag': '🌑暗夜噬影'},
    '轻影': {'class': 'cls_ci_ke', 'icon': '🗡️', 'quality': 'blue', 'bonus_2': {'crit': 0.05, 'atk': 0.08, 'spd': 0.03}, 'bonus_4_stats': {'crit': 0.05}, 'bonus_4': {'effect': 'shadow_combo_cp', 'chance': 0.3, 'params': {'type': "proc_res_gain", "chance": 0.3, "res_key": "cp", "amount": 1, "tag": "🗡️", "name": "轻影连击"}, 'desc': '攻击命中 30% 概率额外获得 1 连击点'}}, 'bonus_5_cond': {'enemy_contains': ["史莱姆", "软泥", "黏液", "孢子"], 'dmg_mult': 1.10, 'tag': '🗡️轻影掠刃'},
    '夜行': {'class': 'cls_ci_ke', 'icon': '🗡️', 'quality': 'blue', 'bonus_2': {'crit': 0.06, 'atk': 0.08}, 'bonus_4_stats': {'crit': 0.05}, 'bonus_4': {'effect': 'night_stealth_exec', 'chance': 0.3, 'params': {'type': "proc_stealth", "chance": 0.3, "hp_lt": 0.3, "buff_key": "stealth", "tag": "🌙", "name": "夜行潜行"}, 'desc': '对生命低于 30% 的敌人，攻击命中 30% 概率下一次攻击必定暴击'}}, 'bonus_5_cond': {'enemy_contains': ["副官", "大副", "头目", "队长", "将军", "哨探"], 'dmg_mult': 1.10, 'tag': '🌙夜行袭营'},
    '阴影': {'class': 'cls_ci_ke', 'icon': '🗡️', 'quality': 'purple', 'bonus_2': {'crit': 0.05, 'atk': 0.08, 'crit_dmg': 0.05}, 'bonus_4_stats': {'crit': 0.05}, 'bonus_4': {'effect': 'shadow_erode_poison', 'chance': 0.3, 'params': {'type': "proc_mark", "chance": 0.3, "max_mark": 5, "mark_key": "poison", "tag": "☠️", "name": "阴影侵蚀"}, 'desc': '攻击命中 30% 概率叠 1 层毒（上限 5）'}}, 'bonus_5_cond': {'enemy_contains': ["战魂", "残骸", "幽魂", "纸墨", "守墓"], 'dmg_mult': 1.10, 'tag': '🌒阴影缠魂'},
    '行者': {'class': 'cls_wu_seng', 'icon': '🥋', 'quality': 'blue', 'bonus_2': {'spd': 0.10, 'atk': 0.05}, 'bonus_4_stats': {'hp': 0.1}, 'bonus_4': {'effect': 'xing_zhe_flow', 'params': {'type': "proc_lifesteal", "chance": 1.0, "lifesteal_pct": 0.06, "tag": "🩸", "name": "行者游血"}, 'desc': '攻击命中 100% 吸血 6% 伤害'}}, 'bonus_5_cond': {'enemy_contains': ["盗贼", "劫掠", "土匪", "强盗"], 'dmg_mult': 1.10, 'tag': '🥋行者制暴'},
    '石拳': {'class': 'cls_wu_seng', 'icon': '🥋', 'quality': 'blue', 'bonus_2': {'def': 0.10, 'atk': 0.05}, 'bonus_4_stats': {'hp': 0.1}, 'bonus_4': {'effect': 'shi_quan_retort', 'chance': 0.15, 'params': {'type': 'taken_counter', 'chance': 0.15, 'atk_pct': 0.30, 'tag': '🥊', 'name': '石拳反打'}, 'desc': '受击 15% 概率以 30% 攻击力立即反击'}}, 'bonus_5_cond': {'enemy_contains': ["巨龟", "猛犸", "剑齿虎", "巨熊", "巨鳄"], 'dmg_mult': 1.10, 'tag': '🥊石拳裂甲'},
    '壁槌': {'class': 'cls_wu_seng', 'icon': '🥋', 'quality': 'purple', 'bonus_2': {'def': 0.08, 'block': 0.06}, 'bonus_4_stats': {'hp': 0.1}, 'bonus_4': {'effect': 'bi_chui_wall', 'params': {'type': 'taken_block_reflect', 'reflect_pct': 0.30, 'tag': '🧱', 'name': '壁槌反震'}, 'desc': '格挡成功时反弹 30% 本次伤害'}}, 'bonus_5_cond': {'enemy_contains': ["冰元素", "霜巨魔", "霜语", "雪原猛犸", "冰牙", "寒冰"], 'dmg_mult': 1.10, 'tag': '🔨壁槌破冰'},
    # ===== v136 Phase6 区域套（5 资料片通用，无 class 字段=不打职业折扣）=====
    '护林': {'icon': '🌳', 'quality': 'white', 'bonus_2': {'def': 0.05}, 'bonus_3_stats': {'hp': 0.08}, 'bonus_3': {'effect': 'ranger_regen_wild', 'chance': 0.4, 'params': {'type': "proc_heal_hp", "chance": 0.4, "heal_pct": 0.05, "tag": "🌳", "name": "护林再生"}, 'desc': '攻击命中 40% 概率回复 5% 最大生命'}}, 'bonus_5_cond': {'enemy_contains': ["火", "熔岩", "岩浆", "烬", "炎"], 'dmg_mult': 1.10, 'tag': '🌳护林克炎'},
    '渡口': {'icon': '⛵', 'quality': 'blue', 'bonus_2': {'spd': 0.06}, 'bonus_3_stats': {'mdef': 0.06}, 'bonus_3': {'effect': 'ferry_repel', 'chance': 0.25, 'params': {'type': 'taken_counter', 'chance': 0.25, 'atk_pct': 0.40, 'once_per_round': True, 'tag': '🌊', 'name': '渡口回潮'}, 'desc': '被攻击命中后 25% 概率反击 40% 攻击力（每回合最多 1 次）'}}, 'bonus_5_cond': {'enemy_contains': ["章鱼", "乌贼", "海蟹", "鲨", "鲸", "雷鳗", "水母"], 'dmg_mult': 1.10, 'tag': '⛵渡口守潮'},
    '巡林': {'icon': '🌲', 'quality': 'blue', 'bonus_2': {'spd': 0.04, 'dodge': 0.03}, 'bonus_3_stats': {'spd': 0.05}, 'bonus_3': {'effect': 'ranger_net', 'chance': 0.3, 'params': {'type': "proc_slow", "chance": 0.3, "slow_pct": 0.15, "slow_turns": 2, "tag": "🕸️", "name": "巡林罗网"}, 'desc': '攻击命中 30% 概率使敌方速度 -15%（2 回合）'}}, 'bonus_5_cond': {'enemy_contains': ["精灵", "仙灵", "妖精", "花妖"], 'dmg_mult': 1.10, 'tag': '🌲巡林逐灵'},
    '霜猎': {'icon': '🐺', 'quality': 'purple', 'bonus_2': {'crit': 0.05, 'atk': 0.03}, 'bonus_3_stats': {'atk': 0.05}, 'bonus_3': {'effect': 'frost_hunt_freeze', 'chance': 0.2, 'params': {'type': "proc_freeze", "chance": 0.2, "freeze_turns": 1, "tag": "🧊", "name": "霜猎冰冻"}, 'desc': '攻击命中 20% 概率冻结敌人 1 回合（Boss 退化为减速 40%）'}}, 'bonus_5_cond': {'enemy_contains': ["雪狼", "冰狼", "极地", "冰川", "雪兔"], 'dmg_mult': 1.10, 'tag': '🏹霜猎夺心'},
    '龙裔': {'icon': '🐉', 'quality': 'purple', 'bonus_2': {'mdef': 0.05}, 'bonus_3_stats': {'atk': 0.06}, 'bonus_3': {'effect': 'long_yi_dread', 'chance': 0.3, 'params': {'type': "proc_mon_atk_down", "chance": 0.3, "atk_down_pct": 0.15, "turns": 2, "tag": "🐉", "name": "龙威压制"}, 'desc': '攻击命中 30% 概率使敌人攻击 -15%（2 回合）'}}, 'bonus_5_cond': {'enemy_contains': ["风暴", "雷霆", "雷暴", "天鹰"], 'dmg_mult': 1.10, 'tag': '🐉龙裔镇风'},
}


def _build_class_sets():
    """注册 10 章名册套装到 SETS(幂等：key 唯一，重复运行覆盖同名)。"""
    for series, set_name in SERIES_SETS.items():
        b = _SERIES_SET_BONUS[series]
        set_id = f"set_{pinyin_id(set_name)}"
        entry = {
            "quality": b["quality"],
            "icon": b["icon"],
            "bonus_2": dict(b["bonus_2"]),
            "name": set_name,
        }
        # v136 Phase6：职业套装归属（本职业 100% / 非本职业 60% 职业折扣）
        if b.get("class"):
            entry["class"] = b["class"]
        if b.get("bonus_4_stats"):
            entry["bonus_4_stats"] = dict(b["bonus_4_stats"])
        if b.get("bonus_4"):
            entry["bonus_4"] = dict(b["bonus_4"])
        if b.get("bonus_3"):
            entry["bonus_3"] = dict(b["bonus_3"])
        if b.get("bonus_3_stats"):
            entry["bonus_3_stats"] = dict(b["bonus_3_stats"])
        if b.get("bonus_5"):
            entry["bonus_5"] = dict(b["bonus_5"])
        if b.get("bonus_5_cond"):
            # v126 数值下沉：5 件战斗条件（enemy_contains/player_hp_below/dmg_mult/tag）随套装注册
            entry["bonus_5_cond"] = dict(b["bonus_5_cond"])
        SETS[set_id] = entry
