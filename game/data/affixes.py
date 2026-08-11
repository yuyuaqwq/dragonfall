# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - affixes.py（阶段八装备重写，2026-08-06）

20 章装备特色词条系统落地：
- AFFIXES：30 种特色词条（武器攻击 18 + 防具防御 12），词条决定装备"性格"
- AFFIX_POOL_BY_QUALITY：随机词条池按品质（20 章 4.2）
- LEGENDARY_EFFECTS：传说专属效果（橙装 1 件 1 个，20 章 2.3）

词条字段：
- name      显示名
- kind      attack/defense（武器/防具类，决定随机池归属与显示分组）
- trigger   触发时机：stat（常驻属性）/on_hit（攻击命中后）/on_taken（受击时）
            /turn_start（回合开始）/battle_start（战斗开始）/passive（被动判定）
- chance    触发概率（无 = 100%）
- effect    效果参数（由 core/affix.py 或 battle.py 解释）
- desc      玩家可见描述（显示在装备详情/词条表）
"""

AFFIXES = {
    # ================= 武器攻击词条（18） =================
    "bleed": {
        "name": "流血", "kind": "attack", "trigger": "on_hit", "chance": 0.20,
        "effect": {"dot_pct": 0.05, "turns": 3},
        "desc": "攻击 20% 使目标流血(每回合 5% 生命，3 回合)",
    },
    "armor_break": {
        "name": "破甲", "kind": "attack", "trigger": "on_hit", "chance": 0.25,
        "effect": {"debuff": "def", "pct": 0.15, "turns": 2},
        "desc": "攻击 25% 降低目标防御 15%(2 回合)",
    },
    "combo": {
        "name": "连击", "kind": "attack", "trigger": "on_hit", "chance": 0.15,
        "effect": {"extra_atk": 0.50},
        "desc": "攻击 15% 追加一次 50% 伤害",
    },
    "execute": {
        "name": "处决", "kind": "attack", "trigger": "passive",
        "effect": {"hp_pct": 0.30, "dmg_pct": 0.30},
        "desc": "对生命 <30% 的目标＋30% 伤害",
    },
    "lifesteal": {
        "name": "吸血", "kind": "attack", "trigger": "on_hit",
    "chance": 1.0,
        "effect": {"lifesteal": 0.08},
        "desc": "攻击伤害的 8% 转化为生命",
    },
    "crit_up": {
        "name": "暴击强化", "kind": "attack", "trigger": "stat",
        "effect": {"crit": 0.05},
        "desc": "暴击率＋5%",
    },
    "crit_dmg": {
        "name": "暴击伤害", "kind": "attack", "trigger": "stat",
        "effect": {"crit_dmg": 0.20},
        "desc": "暴击伤害＋20%",
    },
    "element_fire": {
        "name": "元素·火", "kind": "attack", "trigger": "on_hit",
    "chance": 1.0,
        "effect": {"element": "fire", "pct": 0.05},
        "desc": "攻击附加 5% 火属性伤害",
    },
    "element_ice": {
        "name": "元素·冰", "kind": "attack", "trigger": "on_hit",
    "chance": 1.0,
        "effect": {"element": "ice", "pct": 0.05, "slow": 0.10},
        "desc": "攻击附加 5% 冰属性伤害 + 减速 10%",
    },
    "element_thunder": {
        "name": "元素·雷", "kind": "attack", "trigger": "on_hit",
    "chance": 1.0,
        "effect": {"element": "thunder", "pct": 0.05},
        "desc": "攻击附加 5% 雷属性伤害",
    },
    "precise": {
        "name": "精准", "kind": "attack", "trigger": "stat",
        "effect": {"precise": 0.10},
        "desc": "命中＋10%，无视闪避",
    },
    "pierce": {
        "name": "贯穿", "kind": "attack", "trigger": "on_hit", "chance": 0.20,
        "effect": {"pierce": 1.0},
        "desc": "攻击 20% 无视防御",
    },
    "hunt": {
        "name": "追猎", "kind": "attack", "trigger": "passive",
        "effect": {"marked_dmg": 0.20},
        "desc": "对标记目标＋20% 伤害",
    },
    "charge": {
        "name": "蓄力", "kind": "attack", "trigger": "on_hit", "chance": 0.10,
        "effect": {"dmg_pct": 1.50},
        "desc": "攻击 10% 造成 150% 伤害",
    },
    "counter": {
        "name": "反击", "kind": "attack", "trigger": "on_taken", "chance": 0.20,
        "effect": {"counter": 0.60},
        "desc": "受击后 20% 反击 60% 伤害",
    },
    "break_magic": {
        "name": "破魔", "kind": "attack", "trigger": "passive",
        "effect": {"vs_caster": 0.25},
        "desc": "对魔法系敌人＋25% 伤害",
    },
    "purify": {
        "name": "净化", "kind": "attack", "trigger": "on_hit", "chance": 0.15,
        "effect": {"purge": 1},
        "desc": "攻击 15% 驱散目标 1 层增益",
    },
    "dragon_aw": {
        "name": "龙威", "kind": "attack", "trigger": "passive",
        "effect": {"vs_dragon": 0.25},
        "desc": "对龙系敌人＋25% 伤害",
    },
    # ================= 防具防御词条（12） =================
    "block": {
        "name": "格挡", "kind": "defense", "trigger": "on_taken", "chance": 0.15,
        "effect": {"block": 0.50},
        "desc": "受击 15% 减伤 50%",
    },
    "thorns": {
        "name": "反伤", "kind": "defense", "trigger": "on_taken", "chance": 0.10,
        "effect": {"thorns": 0.30},
        "desc": "受击 10% 反弹 30% 伤害",
    },
    "dmg_reduce": {
        "name": "减伤", "kind": "defense", "trigger": "stat",
    "chance": 1.0,
        "effect": {"dmg_reduce": 0.03},
        "desc": "受击伤害－3%",
    },
    "shield": {
        "name": "护盾", "kind": "defense", "trigger": "battle_start",
        "effect": {"shield_hp_pct": 0.10},
        "desc": "战斗开始获得 10% 生命护盾",
    },
    "dodge": {
        "name": "闪避", "kind": "defense", "trigger": "stat",
        "effect": {"dodge": 0.05},
        "desc": "闪避率＋5%",
    },
    "tenacity": {
        "name": "坚韧", "kind": "defense", "trigger": "on_taken", "chance": 0.20,
        "effect": {"immune_cc": 1},
        "desc": "受击 20% 免疫眩晕/减速",
    },
    "regen": {
        "name": "回春", "kind": "defense", "trigger": "turn_start",
    "chance": 1.0,
        "effect": {"regen_hp_pct": 0.01},
        "desc": "每回合回复 1% 生命",
    },
    "meditate": {
        "name": "冥想", "kind": "defense", "trigger": "turn_start",
    "chance": 1.0,
        "effect": {"regen_mp_pct": 0.01},
        "desc": "每回合回复 1% 魔力",
    },
    "swift": {
        "name": "迅捷", "kind": "defense", "trigger": "stat",
        "effect": {"spd_pct": 0.05},
        "desc": "速度＋5%",
    },
    "elem_resist": {
        "name": "元素抗性", "kind": "defense", "trigger": "stat",
        "effect": {"elem_resist": 0.08},
        "desc": "火/冰/雷抗性＋8%",
    },
    "abyss_resist": {
        "name": "深渊抗性", "kind": "defense", "trigger": "stat",
        "effect": {"abyss_resist": 0.10},
        "desc": "暗影伤害－10%",
    },
    "hp_up": {
        "name": "生命强化", "kind": "defense", "trigger": "stat",
        "effect": {"hp_pct": 0.05},
        "desc": "最大生命＋5%",
    },
}

# 随机词条池按品质（20 章 4.2：蓝 → 攻击 8 + 防具 6；紫 → 攻击 12 + 防具 9；橙 → 全部）
AFFIX_POOL_BY_QUALITY = {
    "blue": [
        "bleed", "armor_break", "combo", "crit_up", "precise", "charge", "counter", "meditate",
        "block", "dodge", "dmg_reduce", "swift", "hp_up", "regen",
    ],
    "purple": [
        "bleed", "armor_break", "combo", "execute", "lifesteal", "crit_up", "crit_dmg",
        "element_fire", "element_ice", "element_thunder", "precise", "pierce", "hunt", "charge",
        "counter", "break_magic", "purify",
        "block", "thorns", "dmg_reduce", "shield", "dodge", "tenacity", "regen", "meditate",
        "swift",
    ],
    "orange": sorted(AFFIXES.keys()),
}

# 词条类型（装备显示/随机池按部位过滤用）
AFFIX_KIND = {"attack": "武器", "defense": "防具"}

# 锻造词条倾向池（20 章 4.3：『锻造 <装备> <词条倾向>』指定词条类型）
AFFIX_AFFINITY_POOLS = {
    "攻击": ["bleed", "armor_break", "combo", "execute", "lifesteal", "crit_up",
             "crit_dmg", "precise", "charge", "pierce", "hunt", "break_magic",
             "purify", "dragon_aw"],
    "防御": ["block", "thorns", "dmg_reduce", "shield", "dodge", "tenacity",
             "regen", "meditate", "swift", "hp_up", "elem_resist", "abyss_resist"],
    "元素": ["element_fire", "element_ice", "element_thunder", "elem_resist"],
    "机动": ["swift", "precise", "combo", "charge", "pierce", "hunt", "dodge"],
}
AFFIX_AFFINITY_CN = {  # 玩家输入别名
    "攻击": "攻击", "输出": "攻击",
    "防御": "防御", "防": "防御", "生存": "防御",
    "元素": "元素", "元素伤害": "元素",
    "机动": "机动", "速度": "机动", "灵活": "机动",
}

# 传说专属效果（20 章 2.3：每件传说 1 个专属。20 章已配 + 名册补齐）
# 结构与 AFFIXES 一致，battle 触发逻辑共用；显示时标注「专属」
LEGENDARY_EFFECTS = {
    "gold_hook": {  # 金钩弯刀：暴击伤害 +30%
        "name": "金钩锋锐", "kind": "attack", "trigger": "stat",
        "effect": {"crit_dmg": 0.30},
        "desc": "暴击伤害＋30%",
    },
    "jack_hook": {  # 杰克的金钩：对低血目标处决大幅强化
        "name": "处决狂潮", "kind": "attack", "trigger": "passive",
        "effect": {"hp_pct": 0.30, "dmg_pct": 0.80},
        "desc": "对生命 <30% 的目标额外＋80% 伤害",
    },
    "ancient_king": {  # 古王剑：处决强化
        "name": "王权处决", "kind": "attack", "trigger": "passive",
        "effect": {"hp_pct": 0.35, "dmg_pct": 0.35},
        "desc": "对生命 <35% 的目标＋35% 伤害",
    },
    "judgment_chain": {  # 审判之链：净化强化
        "name": "审判之链", "kind": "attack", "trigger": "on_hit", "chance": 0.25,
        "effect": {"purge": 2},
        "desc": "攻击 25% 驱散目标 2 层增益",
    },
    "dawn_crown": {  # 晨曦之冠：回春强化
    "chance": 1.0,
        "name": "晨曦祝福", "kind": "defense", "trigger": "turn_start",
        "effect": {"regen_hp_pct": 0.02},
        "desc": "每回合回复 2% 生命",
    },
    "moon_bow": {  # 月神之弓：暴击大幅强化
        "name": "月神眷顾", "kind": "attack", "trigger": "stat",
        "effect": {"crit": 0.10},
        "desc": "暴击率＋10%",
    },
    "helga_relic": {  # 赫尔加的祭器：冰系强化
        "name": "霜语", "kind": "attack", "trigger": "stat",
        "effect": {"ice_dmg": 0.15},
        "desc": "冰属性伤害＋15%",
    },
    "earth_heart": {  # 符文战锤·大地之心：减伤+生命
    "chance": 1.0,
        "name": "大地护佑", "kind": "defense", "trigger": "stat",
        "effect": {"dmg_reduce": 0.05, "hp_pct": 0.05},
        "desc": "受击伤害－5%，最大生命＋5%",
    },
    "dragon_tongue": {  # 龙语圣剑：攻击叠印记
    "chance": 1.0,
        "name": "龙语印记", "kind": "attack", "trigger": "on_hit",
        "effect": {"dragon_mark": 0.02, "max_mark": 5},
        "desc": "攻击叠加龙语印记(每层＋2% 伤害，上限 5 层)",
    },
    "dawn_light": {  # 黎明之光：深渊特攻
        "name": "黎明破晓", "kind": "attack", "trigger": "passive",
        "effect": {"vs_abyss": 0.50},
        "desc": "对深渊系敌人＋50% 伤害",
    },
    "moro_crown": {  # 摩罗之冠：受击腐蚀
        "name": "深渊腐蚀", "kind": "defense", "trigger": "on_taken", "chance": 0.15,
        "effect": {"corrupt": 0.10, "turns": 2},
        "desc": "受击 15% 使敌人攻击－10%(2 回合)",
    },
    "aura_seal": {  # 奥拉圣印：雷系强化
        "name": "风暴之印", "kind": "attack", "trigger": "stat",
        "effect": {"thunder_dmg": 0.20},
        "desc": "雷属性伤害＋20%",
    },
    "lang_tear": {  # 澜歌之泪：水系强化（游戏元素池冰系承载）
        "name": "澜歌", "kind": "attack", "trigger": "stat",
        "effect": {"ice_dmg": 0.20},
        "desc": "冰属性伤害＋20%",
    },
    "ao_lan_pearl": {  # 敖澜之珠：水系强化
        "name": "海渊之珠", "kind": "attack", "trigger": "stat",
        "effect": {"ice_dmg": 0.20},
        "desc": "冰属性伤害＋20%",
    },
    "starfall": {  # v87 星陨之剑：攻击 10% 概率全屏星陨 200% 伤害
        "name": "星陨", "kind": "attack", "trigger": "on_hit", "chance": 0.10,
        "effect": {"mult": 2.0, "aoe": True},
        "desc": "攻击 10% 概率触发星陨：全体 200% 伤害",
    },
    "ember_ward": {  # v87 灰烬守卫套：受击 20% 反弹 50% 伤害（重装反伤）
        "name": "灰烬壁垒", "kind": "defense", "trigger": "on_taken", "chance": 0.20,
        "effect": {"reflect_pct": 0.50},
        "desc": "受击 20% 概率触发灰烬壁垒：反弹 50% 伤害",
    },
}

# 系列固定词条（20 章 3.x；橙装固定词条 + 专属见 EQUIP_ROSTER）
# 值 = 词条 ID 列表，装备生成时作为"固定词条"（不参与随机）
SERIES_FIXED_AFFIX = {
    # 橡木（新手无固定词条，纯基础）
    "铁剑": [], "猎弓": [], "学徒法杖": [], "橡木短棍": [],
    "皮甲": [], "旧皮靴": [], "橡木护腿": [],
    "橡木盾": ["block"], "猎鹿弓": ["precise"], "学徒之杖": ["meditate"], "白鹿皮甲": ["dodge"],
    # v93 商店装：白装无固定词条
    "毛皮帽": [], "橡木戒指": [], "橡木项链": [],
    # #236 拳师武器链：布拳套(橡木白装无词条) / 皮革拳套+铁指虎(连击，贴拳套风格)
    "布拳套": [], "皮革拳套": ["combo"], "铁指虎": ["combo"],
    # v93 商店装：白鹿绿装套（敏捷/闪避风格）
    "白鹿皮帽": ["dodge"], "白鹿胸甲": ["dodge"], "白鹿护腿": ["dodge"],
    "白鹿皮靴": ["swift"], "白鹿之戒": ["crit_up"], "白鹿吊坠": ["crit_up"],
    # 铁港
    "弯刀": ["crit_up"], "水手短刃": ["combo"], "海风长弓": ["precise", "hunt"],
    "船长帽": ["swift"], "水手夹克": ["dodge"], "海盗靴": ["swift"],
    "水手护腿": ["swift"],
    "珍珠项链": ["crit_up", "swift"], "锚形戒指": ["lifesteal", "crit_dmg"],
    "金钩弯刀": ["crit_up", "lifesteal"], "杰克的金钩": ["execute", "lifesteal"],
    # 圣光
    "圣光长剑": ["armor_break"], "晨曦法杖": ["meditate"],
    "王都长弓": ["pierce", "precise"], "圣殿战锤": ["charge", "execute"],
    "骑士头盔": ["dmg_reduce"], "圣光胸甲": ["shield"], "骑士长靴": ["tenacity"],
    "圣光护腿": ["dmg_reduce"],
    "圣光护符": ["purify", "meditate"], "王国徽戒": ["crit_up", "break_magic"],
    "古王剑": ["execute"], "审判之链": ["purify"],
    # 月语
    "月语长弓": ["hunt", "precise"], "银叶法杖": ["element_ice", "meditate"],
    "月光短刃": ["crit_up", "combo"], "月冠头盔": ["swift"],
    "精灵链甲": ["dodge", "swift"], "月之靴": ["swift"], "月语护腿": ["swift"],
    "星语项链": ["element_ice", "meditate"], "月华戒指": ["crit_up", "element_ice"],
    "晨曦之冠": ["swift"], "月神之弓": ["crit_up", "precise"],
    # 霜狼
    "霜狼长剑": ["element_ice", "armor_break"], "铁砧战锤": ["charge", "execute"],
    "北风长弓": ["pierce", "precise"], "霜狼头盔": ["tenacity"],
    "铁砧胸甲": ["dmg_reduce", "block"], "霜原长靴": ["tenacity"], "霜狼护腿": ["tenacity"],
    "熔炉项链": ["element_fire", "charge"], "符文戒指": ["element_thunder", "crit_up"],
    "赫尔加的祭器": ["element_ice"], "符文战锤·大地之心": ["dmg_reduce"],
    # 龙脊
    "龙脊大剑": ["execute", "charge"], "龙语法杖": ["dragon_aw", "meditate"],
    "龙鳞头盔": ["tenacity"], "龙鳞胸甲": ["block", "dmg_reduce"], "龙鳞护腿": ["dmg_reduce"],
    "龙爪手套": ["combo", "counter"], "龙眼项链": ["dragon_aw", "crit_up"],
    "龙语圣剑": ["dragon_aw", "execute"], "黎明之光": ["break_magic", "execute"],
    # v101.25e 商店断层补档：银铃/翡翠/迷雾中间档（敏捷/闪避风格，蓝装）
    "银铃短刃": ["combo", "swift"], "银铃护腿": ["swift"], "银铃杖": ["meditate"],
    "翡翠皮甲": ["dodge"], "翡翠护腿": ["dodge"],
    "迷雾护腿": ["swift"], "迷雾兜帽": ["swift"],
    # 海神
    "海神三叉戟": ["element_ice", "pierce"], "潮汐法杖": ["element_ice", "meditate"],
    "珍珠头冠": ["swift"], "龙鳞海甲": ["dodge", "dmg_reduce"], "海神长靴": ["swift"],
    "海神护腿": ["swift"],
    "海神项链": ["swift", "meditate"], "海神戒指": ["element_ice", "crit_up"],
    "澜歌之泪": ["element_ice", "lifesteal"], "敖澜之珠": ["element_ice", "meditate"],
    # 地底
    "深渊战刃": ["armor_break", "execute"], "熔岩法杖": ["element_fire", "charge"],
    "深渊头盔": ["tenacity"], "黑曜胸甲": ["dmg_reduce", "thorns"], "地底长靴": ["tenacity"],
    "黑曜护腿": ["dmg_reduce"],
    "深渊项链": ["thorns", "tenacity"], "摩罗之冠": ["thorns", "dmg_reduce"],
    # 苍穹
    "苍穹之枪": ["pierce", "charge"], "星光法杖": ["element_thunder", "meditate"],
    "苍穹头盔": ["swift"], "云纹胸甲": ["dodge", "swift"], "星辉长靴": ["swift"],
    "苍穹护腿": ["swift"],
    "苍穹项链": ["element_thunder", "crit_up"], "奥拉圣印": ["element_thunder", "crit_up"],
    # v87 隐藏线：星尘（法系星空）
    "星尘法杖": ["element_thunder", "meditate"], "星尘长袍": ["dodge", "meditate"],
    "星尘之戒": ["crit_up", "element_thunder"], "星尘坠饰": ["crit_dmg", "meditate"],
    "星尘护腿": ["dodge"],
    # v87 隐藏线：灰烬守卫（重装防御）
    "灰烬长剑": ["execute", "charge"], "灰烬铠甲": ["dmg_reduce", "block"],
    "灰烬之盔": ["tenacity"], "灰烬之盾": ["block", "thorns"], "灰烬护腿": ["dmg_reduce"],
    "灰烬战靴": ["tenacity", "block"],
    # v87 隐藏线：传说·星陨之剑
    "星陨之剑": ["crit_up", "element_thunder"],
}
