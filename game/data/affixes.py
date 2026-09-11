# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - affixes.py（阶段八装备重写，2026-08-06）

20 章装备特色词条系统落地：
- AFFIXES：76 种特色词条（攻击 37 + 防御 39，含 v130.2 资源联动词条 31 种），词条决定装备"性格"
- AFFIX_POOL_BY_QUALITY：随机词条池按品质（20 章 4.2）
- LEGENDARY_EFFECTS：传说专属效果（橙装 1 件 1 个，20 章 2.3）

词条字段：
- name      显示名
- kind      attack/defense（武器/防具类，决定随机池归属与显示分组）
- trigger   触发时机：stat（常驻属性）/on_hit（攻击命中后）/on_taken（受击时）
            /turn_start（刻开始）/battle_start（战斗开始）/passive（被动判定）
- chance    触发概率（缺省 100% 恒触发；仅随机概率词条需显式 chance，如 armor_break/pierce）
- effect    效果参数（由 core/affix.py 或 battle.py 解释）
- desc      玩家可见描述（显示在装备详情/词条表）
"""

AFFIXES = {
    # ================= 武器攻击词条（18） =================
    "bleed": {
        "name": "流血", "kind": "attack", "trigger": "on_hit", "chance": 0.20,
        "effect": {"dot_pct": 0.05, "stacks": 3},
        "desc": "攻击 20% 使目标流血(每刻 5% 生命，3 刻)",
    },
    "armor_break": {
        "name": "破甲", "kind": "attack", "trigger": "on_hit", "chance": 0.25,
        "effect": {"debuff": "def", "pct": 0.15, "turns": 2},
        "desc": "攻击 25% 降低目标防御 15%(2 刻)",
    },
    "combo": {
        "name": "连击", "kind": "attack", "trigger": "on_hit", "chance": 0.15,
        "effect": {"extra_atk": 0.50},
        "desc": "攻击 15% 追加一次 50% 伤害",
    },
    "execute": {
        "name": "处决", "kind": "attack", "trigger": "passive",
        "effect": {"dmg_mult": 1.30, "execute_threshold": 0.30, "tag": "💀处决"},
        "desc": "对生命 <30% 的目标＋30% 伤害",
    },
    "lifesteal": {
        "name": "吸血", "kind": "attack", "trigger": "stat",
        "effect": {"lifesteal": 0.08},
        "desc": "吸血 +8%（伤害回血，面板可见）",
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
        "effect": {"element": "fire", "pct": 0.05},
        "desc": "攻击附加 5% 火属性伤害",
    },
    "element_ice": {
        "name": "元素·冰", "kind": "attack", "trigger": "on_hit",
        "effect": {"element": "ice", "pct": 0.05, "slow": 0.10, "slow_turns": 2},
        "desc": "攻击附加 5% 冰属性伤害 + 减速（敌速减半）",
    },
    "element_thunder": {
        "name": "元素·雷", "kind": "attack", "trigger": "on_hit", "chance": 0.15,
        "effect": {"element": "thunder", "pct": 0.05, "thunder_bonus": 0.20},
        "desc": "攻击附加 5% 雷属性伤害，15% 概率追加 20% 雷伤",
    },
    "precise": {
        "name": "精准", "kind": "attack", "trigger": "stat",
        "effect": {"precise": 0.10, "dmg_mult": 1.10, "tag": "🎯精准"},
        "desc": "命中＋10%（无视闪避），伤害＋10%",
    },
    "pierce": {
        "name": "贯穿", "kind": "attack", "trigger": "on_hit", "chance": 0.20,
        "effect": {"atk_pct": 0.60},
        "desc": "攻击 20% 无视防御",
    },
    "pene_phys": {
        "name": "穿甲", "kind": "attack", "trigger": "stat",
        "effect": {"pene_phys": 0.05},
        "desc": "物穿＋5%（无视物理防御）",
    },
    "pene_magi": {
        "name": "法穿", "kind": "attack", "trigger": "stat",
        "effect": {"pene_magi": 0.05},
        "desc": "法穿＋5%（无视魔法防御）",
    },
    "pene_flat": {
        "name": "破甲刃", "kind": "attack", "trigger": "stat",
        "effect": {"pene_flat": 0.5},
        "desc": "固定物穿 2+装备等级×0.5 点",
    },
    "pene_mflat": {
        "name": "破法刃", "kind": "attack", "trigger": "stat",
        "effect": {"pene_mflat": 0.5},
        "desc": "固定法穿 2+装备等级×0.5 点",
    },
    "hunt": {
        "name": "追猎", "kind": "attack", "trigger": "passive",
        "effect": {"dmg_mult": 1.20, "enemy_marked": True, "tag": "🎯追猎"},
        "desc": "对标记/被集火目标＋20% 伤害",
    },
    "charge": {
        "name": "蓄力", "kind": "attack", "trigger": "on_hit", "chance": 0.10,
        "effect": {"dmg_pct": 0.50},
        "desc": "攻击 10% 造成 150% 伤害",
    },
    "counter": {
        "name": "反击", "kind": "attack", "trigger": "on_taken", "chance": 0.20,
        "effect": {"pct": 0.60},
        "desc": "受击后 20% 反击 60% 伤害",
    },
    "break_magic": {
        "name": "破魔", "kind": "attack", "trigger": "passive",
        "effect": {"dmg_mult": 1.25, "enemy_role": "caster", "tag": "🔮破魔"},
        "desc": "对魔法系敌人(法师/治疗型/会用魔法技的怪)＋25% 伤害",
    },
    "purify": {
        "name": "净化", "kind": "attack", "trigger": "on_hit", "chance": 0.15,
        "effect": {"purge": 1, "holy_weaken": 0.10},
        "desc": "攻击 15% 驱散目标 1 层增益，成功时敌人攻击－10%(1 刻)",
    },
    "dragon_aw": {
        "name": "龙威", "kind": "attack", "trigger": "passive",
        "effect": {"dmg_mult": 1.25, "enemy_contains": ["龙"], "tag": "🐉龙威"},
        "desc": "对龙系敌人＋25% 伤害",
    },
    # ================= 防具防御词条（12） =================
    "block": {
        "name": "格挡", "kind": "defense", "trigger": "stat",
        "effect": {"block": 0.15},
        "desc": "格挡率 +15%（格挡时减伤 50%）",
    },
    "thorns": {
        "name": "反伤", "kind": "defense", "trigger": "stat",
        "effect": {"thorns": 0.10},
        "desc": "反伤 +10%（受击反弹伤害，面板可见）",
    },
    "dmg_reduce": {
        "name": "减伤", "kind": "defense", "trigger": "stat",
        "effect": {"dmg_reduce": 0.03},
        "desc": "受击伤害－3%",
    },
    "phys_ward": {
        "name": "铁壁", "kind": "defense", "trigger": "stat",
        "effect": {"phys_reduce": 0.05},
        "desc": "物理免伤 +5%",
    },
    "magic_ward": {
        "name": "魔抗", "kind": "defense", "trigger": "stat",
        "effect": {"magic_reduce": 0.05},
        "desc": "魔法免伤 +5%",
    },
    "thirst_phys": {  # v106.4 攻击类被动词条（kind=attack），按吸血主题排在防具区便于阅读
        "name": "渴血", "kind": "attack", "trigger": "stat",
        "effect": {"lifesteal_phys": 0.08},
        "desc": "物理吸血 +8%（仅物理攻击回血）",
    },
    "thirst_magi": {
        "name": "吸魂", "kind": "attack", "trigger": "stat",
        "effect": {"lifesteal_magi": 0.08},
        "desc": "法术吸血 +8%（仅魔法攻击回血）",
    },
    "shield": {
        "name": "护盾", "kind": "defense", "trigger": "battle_start",
        "effect": {"shield_hp_pct": 0.10, "turns": 3},
        "desc": "战斗开始获得 10% 生命护盾",
    },
    "dodge": {
        "name": "闪避", "kind": "defense", "trigger": "stat",
        "effect": {"dodge": 0.05},
        "desc": "闪避率＋5%",
    },
    # v110 审计修复：原键 "tenacity" 与下方 v106「韧性」stat 词条冲突（dict 后键覆盖前键，
    # 12 件固定词条装备隐性双吃 CC 免疫+韧性 stat）——拆分 key：本词条改名 tenacity_cc
    #（受击 20% 免疫控制，仅由 affix_effects._t_tenacity_cc 消费）
    "tenacity_cc": {
        "name": "坚韧", "kind": "defense", "trigger": "on_taken", "chance": 0.20,
        "effect": {"immune_cc": 1, "heal_pct": 0.03},
        "desc": "受击 20% 免疫眩晕/减速，成功时回复 3% 生命",
    },
    "regen": {
        "name": "回春", "kind": "defense", "trigger": "turn_start",
        "effect": {"pct": 0.01},
        "desc": "每刻回复 1% 生命",
    },
    "meditate": {
        "name": "冥想", "kind": "defense", "trigger": "turn_start",
        "effect": {"pct": 0.01},
        "desc": "每刻回复 1% 魔力",
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
    "tenacity": {
        "name": "韧性", "kind": "defense", "trigger": "stat",
        "effect": {"tenacity": 0.05},
        "desc": "被暴击率－5%",
    },
    "luck": {
        "name": "幸运", "kind": "defense", "trigger": "stat",
        "effect": {"luck": 0.05},
        "desc": "掉落收益＋5%",
    },
    "cdr": {
        "name": "轻灵", "kind": "defense", "trigger": "stat",
        "effect": {"cdr": 0.05},
        "desc": "冷却缩减＋5%",
    },
    "exp_bonus": {
        "name": "求知", "kind": "defense", "trigger": "stat",
        "effect": {"exp_bonus": 0.05},
        "desc": "战斗经验＋5%",
    },
    "gold_bonus": {
        "name": "聚宝", "kind": "defense", "trigger": "stat",
        "effect": {"gold_bonus": 0.05},
        "desc": "金币收益＋5%",
    },
    "heal_power": {
        "name": "圣愈", "kind": "defense", "trigger": "stat",
        "effect": {"heal_power": 0.05},
        "desc": "治疗强度＋5%",
    },
    "shield_power": {
        "name": "坚盾", "kind": "defense", "trigger": "stat",
        "effect": {"shield_power": 0.05},
        "desc": "护盾强度＋5%",
    },
    # ================= v130.2 装备-资源联动词条（六职业线，设计稿 §6 落地） =================
    # 说明：字段与既有 affix 结构对齐（name/kind/trigger/effect/desc/chance），
    # 额外附 "qualities"（品质分布：blue=精良/稀有 紫=史诗 orange=传说，对应 AFFIX_POOL_BY_QUALITY）
    # 与 "tiers"（数值档位按品质的取值表，供批 2 引擎按品质取档）、"unique"（唯一主词条，禁跨件叠加）、
    # "line"（归属职业线/攻守）。effect 内 res 使用资源 key（rage/element/energy/faith/cp/chi——key 语义
    # 与 cap 单源 EFFECT_RULES，desc/展示见 job_guide 展示表；原 core_resources.py 已随 v181.M-R2c 退役）。
    #
    # ⚠️ saintess_engine 装配落地状态（R4 / docs/REFACTOR_v181P4_N9_7_affix_migration.md）：
    # - ✅ 已装配（翻译器在 game/services/battle_equip_proc.py N9.7e）：effect 含
    #   res+gain+on 的事件 gain 型 10 条（war_spirit/warcry_echo/blood_bath/arcana_flux/
    #   crit_charge/holy_echo/crit_return/pious_charm/rock_rest/opening_stance——
    #   对应 events → actor.triggers 叠 we_affix_res_gain 层，cap clamp 查
    #   EFFECT_RULES[res].cap）+ boiling_blood（怒气满全减伤，taken_calc state_full）。
    # - ⛔/✅ 落地状态（v181.M-R2e 方案 A 已装 cap 动态机制；v181.M-bonus 统一 bonus 容器）：
    #   · ✅ 上限型 effect {res, max_bonus}：rage_forge/divine_radiance/holy_heart/
    #     rhythm_badge/chi_limit/full_pack——装配写 actor["bonus"]["cap"]（battle_equip_proc
    #     _apply_cap_bonus，覆盖写幂等），引擎 _cap_of 收敛点（effects 叠层 clamp /
    #     schedule period gain / 渠道 gain clamp）读动态 cap = EFFECT_RULES 基准 + 增量；
    #   · ✅ cost_reduce 型 v181.M-bonus 已装：energy_blade（{res, cost_reduce}，
    #     精力消耗折扣）+ arcane_focus（mp_cost_reduce 0.10 元素/奥术判据）+
    #     sigil_blessing（mp_cost_reduce 5/10 神迹技判据）→ 装配写 actor["bonus"]["cost"]
    #     （_apply_cost_bonus 分域覆盖写），引擎 actions._skill_pay_of 折算（预检/扣费
    #     同源、floor 取整、保底 1）；
    #   · ✅ finisher（终结技伤害乘区 finisher_dmg tiers）v181.M-bonus 已装（dmg_calc
    #     mech_any 谓词 + _af_finisher 翻译器）；
    #   · ⛔ cond 修正型 ember_brand（{res, gain, cond: hp_lt_30}，
    #     effect 无 on 时机）——「怒气获取时额外 +1」需资源获取事件钩子（装配层无对应事件位）；
    #   · combo_recover（on: combo_skill）——拳师「连招技」无技能标记事件判据，
    #     需词条级 kind/tag 语义核对；
    #   · ⛔ regen 型 energy_tide/swift_tailwind 与 purify → v181.M-affixtail 已装
    #     （energy_tide/swift_tailwind：turn_start 回能 we_affix_res_gain，swift_tailwind
    #     cond energy_ge_80 → cond_key/cond_ge 参数；purify：命中驱散 we_affix_purify，
    #     增益判定 = 面板 op mul>1/add>0 / stat_scale 正层 / 自愈回能 period，
    #     成功附加圣洁敌攻 -10% 1 刻——见 docs/REFACTOR_v181P4_N9_7_affix_migration.md
    #     §5 收尾批；we_affix_res_gain cap clamp 同批收敛 _cap_of（上限词条抬 cap 可攒满））。
    # ================= 战士（怒气 rage ）=================
    "war_spirit": {
        "name": "战意", "kind": "attack", "trigger": "passive",
        "effect": {"res": "rage", "gain": 1, "on": ["on_attack", "on_skill"]},
        "qualities": ["blue", "purple"], "line": "战士·通用基础",
        "desc": "攻击/技能触发怒气时 怒气获取额外 +1",
    },
    "rage_forge": {
        "name": "怒火熔铸", "kind": "defense", "trigger": "stat",
        "effect": {"res": "rage", "max_bonus": 2},
        "qualities": ["purple", "orange"], "unique": True, "line": "战士·通用基础",
        "desc": "怒气上限 +2 (10 → 12，配合满怒档)",
    },
    "warcry_echo": {
        "name": "战吼回响", "kind": "defense", "trigger": "passive",
        "effect": {"res": "rage", "gain": 1, "on": "buff_skill"},
        "qualities": ["purple"], "line": "战士·通用基础",
        "desc": "释放增益技能后 怒气 +1",
    },
    "blood_bath": {
        "name": "浴血", "kind": "defense", "trigger": "on_taken",
        "effect": {"res": "rage", "gain": 1, "on": "on_taken"},
        "qualities": ["purple"], "line": "战士·攻线",
        "desc": "受击时 怒气 +1 (与血债怒火叠加)",
    },
    "ember_brand": {
        "name": "残血灼薪", "kind": "attack", "trigger": "passive",
        "effect": {"res": "rage", "gain": 1, "cond": "hp_lt_30"},
        "qualities": ["blue"], "line": "战士·攻线",
        "desc": "生命 <30% 时 怒气获取 +1",
    },
    "boiling_blood": {
        "name": "沸血浇筑", "kind": "defense", "trigger": "passive",
        "effect": {"dmg_reduce": 0.08, "cond": "rage_full"},
        "qualities": ["orange"], "line": "战士·攻线沸血体系",
        "desc": "怒气全满时 全减伤 +8% (沸血战体)",
    },
    # ================= 法师（元素亲和充能条 element；基础纯蓝，攻线限定词条标注转职生效） =================
    "arcana_flux": {
        "name": "充能汲引", "kind": "attack", "trigger": "passive",
        "effect": {"res": "element", "gain": 1, "on": "on_cast"},
        "qualities": ["blue"], "line": "法师·基础/转职通用",
        "desc": "元素/奥术技能施放 充能获取 +1 (额外)",
    },
    "arcane_focus": {
        "name": "凝神塑能", "kind": "defense", "trigger": "stat",
        "effect": {"mp_cost_reduce": 0.10},
        "qualities": ["blue"], "line": "法师·基础即受益",
        "desc": "元素/奥术技能 魔力消耗 -10% (续航向，基础即受益)",
    },
    "sigil_engrave": {
        "name": "印记铭刻", "kind": "attack", "trigger": "stat",
        "effect": {"max_sigil": 1, "cond": "element_mage", "max_total": 1},
        "qualities": ["blue", "purple"], "line": "法师·攻线限定",
        "desc": "元素印记上限 +1 (每系 3 → 4，元素法师转职后生效)",
    },
    "reaction_catalyst": {
        "name": "反应催化", "kind": "attack", "trigger": "stat",
        "effect": {"reaction_dmg": 0.15, "cond": "element_mage"},
        "qualities": ["purple"], "line": "法师·攻线限定",
        "desc": "元素反应伤害 +15% (元素法师转职后生效)",
    },
    # ================= 游侠（精力 energy） =================
    "energy_blade": {
        "name": "精力刀刃", "kind": "attack", "trigger": "stat",
        "effect": {"res": "energy", "cost_reduce": 0.05, "tiers": {"blue": 0.05, "purple": 0.08, "orange": 0.12}},
        "qualities": ["blue", "purple"], "line": "游侠·通用",
        "desc": "精力消耗 -5% (史诗 -8%，传说 -12%)",
    },
    "energy_tide": {
        "name": "精力潮汐", "kind": "defense", "trigger": "turn_start",
        "effect": {"res": "energy", "regen": 5, "tiers": {"purple": 5, "orange": 10}},
        "qualities": ["purple", "orange"], "line": "游侠·通用",
        "desc": "每刻 精力回复 +5 (传说 +10)",
    },
    "full_pack": {
        "name": "盈满背囊", "kind": "defense", "trigger": "stat",
        "effect": {"res": "energy", "max_bonus": 10, "tiers": {"purple": 10, "orange": 20}},
        "qualities": ["purple", "orange"], "line": "游侠·通用",
        "desc": "精力上限 +10 (史诗 +10，传说 +20)",
    },
    "crit_charge": {
        "name": "暴击蓄能", "kind": "attack", "trigger": "passive",
        "effect": {"res": "energy", "gain": 3, "on": "on_crit"},
        "qualities": ["purple", "orange"], "line": "游侠·转职后兑现",
        "desc": "暴击命中时 精力回复 +3",
    },
    "swift_tailwind": {
        "name": "疾风余韵", "kind": "defense", "trigger": "turn_start",
        "effect": {"res": "energy", "regen": 10, "cond": "energy_ge_80"},
        "qualities": ["orange"], "line": "游侠·守线满弦兑现",
        "desc": "刻结束时，若精力 ≥ 80，下刻 精力回复 +10",
    },
    # ================= 牧师（信仰 faith） =================
    "holy_echo": {
        "name": "圣辉回响", "kind": "defense", "trigger": "passive",
        "effect": {"res": "faith", "gain": 1, "on": "on_heal", "tiers": {"blue": 1, "purple": 2}},
        "qualities": ["blue", "purple"], "line": "牧师·通用",
        "desc": "治疗命中时 信仰 +1 (史诗 +2)",
    },
    "divine_radiance": {
        "name": "神赐容光", "kind": "defense", "trigger": "stat",
        "effect": {"res": "faith", "max_bonus": 1},
        "qualities": ["purple"], "line": "牧师·通用",
        "desc": "信仰上限 +1",
    },
    "holy_heart": {
        "name": "圣光之心", "kind": "defense", "trigger": "stat",
        "effect": {"res": "faith", "max_bonus": 2},
        "qualities": ["orange"], "unique": True, "line": "牧师·通用",
        "desc": "信仰上限 +2 (唯一主词条)",
    },
    "sigil_blessing": {
        "name": "圣徽之佑", "kind": "defense", "trigger": "stat",
        "effect": {"mp_cost_reduce": 5, "on": "miracle", "tiers": {"blue": 5, "purple": 10}},
        "qualities": ["blue", "purple"], "line": "牧师·神迹技",
        "desc": "神迹技 魔力消耗 -5 (史诗 -10)",
    },
    "pious_charm": {
        "name": "虔诚护符", "kind": "defense", "trigger": "on_taken",
        "effect": {"res": "faith", "gain": 1, "on": "on_taken"},
        "qualities": ["blue"], "unique": True, "line": "牧师·通用",
        "desc": "受击时 信仰 +1 (唯一词条)",
    },
    # ================= 刺客（连击点 cp；暴击回点/连段 毒/攻线向） =================
    "crit_return": {
        "name": "暴击回点", "kind": "attack", "trigger": "passive",
        "effect": {"res": "cp", "gain": 1, "on": "on_crit", "chance": 0.15,
                   "tiers": {"blue": 0.15, "purple": 0.25, "orange": 0.40}},
        "qualities": ["blue", "purple"], "line": "刺客·毒线/影步线向",
        "desc": "暴击时 15% 概率额外获得 1 连击点 (史诗 25%，传说 40%)",
    },
    "finisher": {
        "name": "终结之技", "kind": "attack", "trigger": "passive",
        "effect": {"finisher_dmg": 0.10, "tiers": {"blue": 0.10, "purple": 0.15, "orange": 0.20}},
        "qualities": ["blue", "purple"], "line": "刺客·通用",
        "desc": "终结技伤害 +10% (史诗 +15%，传说 +20%)",
    },
    "combo_ward": {
        "name": "连段护持", "kind": "defense", "trigger": "on_taken",
        "effect": {"combo_keep_chance": 0.15, "tiers": {"purple": 0.15, "orange": 0.30}, "cond": "攻线限定"},
        "qualities": ["purple", "orange"], "line": "刺客·攻线限定",
        "desc": "受击时 15% 概率连击不因受击回退 (史诗 30%；攻线限定)",
    },
    "combo_edge": {
        "name": "连段之锋", "kind": "attack", "trigger": "stat",
        "effect": {"combo_threshold_reduce": 1, "cond": "攻线限定"},
        "qualities": ["purple"], "line": "刺客·攻线限定",
        "desc": "连段生效阈值 -1 (combo ≥ 3 → ≥ 2；攻线限定)",
    },
    "rhythm_badge": {
        "name": "节奏之徽", "kind": "defense", "trigger": "stat",
        "effect": {"res": "cp", "max_bonus": 1, "max_total": 2},
        "qualities": ["purple", "orange"], "unique": True, "line": "刺客·收藏主词条",
        "desc": "连击点上限 +1 (最多 +2)",
    },
    # ================= 拳师（气 chi；命名西幻化，苦修 line 锁系数不上浮） =================
    "combo_recover": {
        "name": "连段回收", "kind": "attack", "trigger": "passive",
        "effect": {"res": "chi", "gain": 1, "on": "combo_skill"},
        "qualities": ["blue"], "line": "拳师·通用基础连段",
        "desc": "连招技额外 +1 气",
    },
    "chi_limit": {
        "name": "气量强化", "kind": "defense", "trigger": "stat",
        "effect": {"res": "chi", "max_bonus": 2},
        "qualities": ["purple", "orange"], "unique": True, "line": "拳师·攻线/爆发流",
        "desc": "气上限 +2 (至 12)",
    },
    "rock_rest": {
        "name": "磐息", "kind": "defense", "trigger": "on_taken",
        "effect": {"res": "chi", "gain": 1, "on": "on_taken"},
        "qualities": ["blue"], "line": "拳师·守线专属",
        "desc": "受击时额外 +1 气 (配合守线反震/柱势)",
    },
    "burst_break": {
        "name": "爆发贯体", "kind": "attack", "trigger": "stat",
        "effect": {"chi_skill_phys": 0.10},
        "qualities": ["purple"], "line": "拳师·通用倾泻流",
        "desc": "气力技物理伤害 +10%",
    },
    "opening_stance": {
        "name": "起手之势", "kind": "defense", "trigger": "battle_start",
        "effect": {"res": "chi", "gain": 1, "on": "battle_start"},
        "qualities": ["blue"], "line": "拳师·通用开局节奏",
        "desc": "战斗开始时 +1 气",
    },
    "momentum_mastery": {
        "name": "蓄势精通", "kind": "attack", "trigger": "stat",
        "effect": {"momentum_per_chi": 0.04, "base": 0.03, "cond": "攻线蓄势"},
        "qualities": ["blue", "purple"], "line": "拳师·攻线专属",
        "desc": "攻线每 1 气提升的物理伤害 +3% → +4% (蓄势 Momentum 系数；苦修锁 4% 不上浮)",
    },
}

# ================= v130.2d 六词条机制恢复（印记铭刻/反应催化/疾风余韵/连段护持/连段之锋/蓄势精通） ================
# 机制已在 battle.py 全部接线（v130.2d）；AFFIX_DELISTED_V130_2C 集合移除（剩 0 个），六词条重回掉落池，
# 存量装备（此前已掉落/已装备）与新掉落装备一同按 battle.py 挂点自动生效。

# 随机词条池按品质（20 章 4.2：蓝 → 攻击 7 + 防具 7；紫 → 攻击 17 + 防具 9；橙 → 全部）
AFFIX_POOL_BY_QUALITY = {
    "blue": [
        "bleed", "armor_break", "combo", "crit_up", "precise", "charge", "counter", "meditate",
        "block", "dodge", "dmg_reduce", "swift", "hp_up", "regen",
        "cdr", "exp_bonus", "gold_bonus",  # v106.1 轻灵/求知/聚宝
        "heal_power", "shield_power",  # v106.2 圣愈/坚盾
        # v130.2 资源联动词条（基础/稀有档：战意 残血灼薪 充能汲引 凝神塑能 精力刀刃
        # 圣辉回响 圣徽之佑 虔诚护符 暴击回点 终结之技 连段回收 磐息 起手之势）
        "war_spirit", "ember_brand", "arcana_flux", "arcane_focus", "energy_blade",
        "holy_echo", "sigil_blessing", "pious_charm", "crit_return", "finisher",
        "combo_recover", "rock_rest", "opening_stance",
        # v130.2d 机制恢复（印记铭刻/蓄势精通，蓝档）
        "sigil_engrave", "momentum_mastery",
    ],
    "purple": [
        "bleed", "armor_break", "combo", "execute", "lifesteal", "crit_up", "crit_dmg",
        "element_fire", "element_ice", "element_thunder", "precise", "pierce", "hunt", "charge",
        "counter", "break_magic", "purify",
        "pene_phys", "pene_magi", "pene_flat", "pene_mflat",  # v106 穿透词条
        "block", "thorns", "dmg_reduce", "shield", "dodge", "tenacity", "regen", "meditate",
        "swift", "luck",  # v106 韧性/幸运
        "cdr", "exp_bonus", "gold_bonus",  # v106.1 轻灵/求知/聚宝
        "heal_power", "shield_power",  # v106.2 圣愈/坚盾
        "phys_ward", "magic_ward", "thirst_phys", "thirst_magi",  # v106.4 铁壁/魔抗/渴血/吸魂
        # v130.2 资源联动词条（史诗档：战意 怒火熔铸 战吼回响 浴血 精力刀刃 精力潮汐
        # 盈满背囊 暴击蓄能 圣辉回响 神赐容光 圣徽之佑 暴击回点 终结之技 节奏之徽
        # 气量强化 爆发贯体）
        "war_spirit", "rage_forge", "warcry_echo", "blood_bath",
        "energy_blade", "energy_tide", "full_pack", "crit_charge",
        "holy_echo", "divine_radiance", "sigil_blessing",
        "crit_return", "finisher", "rhythm_badge",
        "chi_limit", "burst_break",
        # v130.2d 机制恢复（印记铭刻/反应催化/连段护持/连段之锋/蓄势精通，紫档）
        "sigil_engrave", "reaction_catalyst", "combo_ward", "combo_edge", "momentum_mastery",
    ],
    "orange": sorted(AFFIXES.keys()),
}

# 词条类型（装备显示/随机池按部位过滤用）
AFFIX_KIND = {"attack": "武器", "defense": "防具"}

# 锻造词条倾向池（20 章 4.3：『锻造 <装备> <词条倾向>』指定词条类型）
AFFIX_AFFINITY_POOLS = {
    "攻击": ["bleed", "armor_break", "combo", "execute", "lifesteal", "crit_up",
             "crit_dmg", "precise", "charge", "pierce", "hunt", "break_magic",
             "purify", "dragon_aw", "pene_phys", "pene_magi", "pene_flat", "pene_mflat"],  # v106 穿透词条进攻击倾向
    "防御": ["block", "thorns", "dmg_reduce", "shield", "dodge", "tenacity",
             "regen", "meditate", "swift", "hp_up", "elem_resist", "abyss_resist", "luck",
             "cdr", "exp_bonus", "gold_bonus",
             "heal_power", "shield_power"],  # v106 韧性/幸运 + v106.1 轻灵/求知/聚宝 + v106.2 圣愈/坚盾
    "元素": ["element_fire", "element_ice", "element_thunder", "elem_resist"],
    "机动": ["swift", "precise", "combo", "charge", "pierce", "hunt", "dodge"],
}
AFFIX_AFFINITY_CN = {  # 玩家输入别名
    "攻击": "攻击", "输出": "攻击",
    "防御": "防御", "防": "防御", "生存": "防御",
    "元素": "元素", "元素伤害": "元素",
    "机动": "机动", "速度": "机动", "灵活": "机动",
    "穿透": "攻击", "破甲": "攻击",  # v106 别名：穿透/破甲归攻击倾向
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
        "effect": {"dmg_mult": 1.80, "execute_threshold": 0.30, "tag": "💀处决狂潮"},
        "desc": "对生命 <30% 的目标额外＋80% 伤害",
    },
    "ancient_king": {  # 古王剑：处决强化（v110 斩杀线统一 30%，与 execute 一致）
        "name": "王权处决", "kind": "attack", "trigger": "passive",
        "effect": {"dmg_mult": 1.35, "execute_threshold": 0.30, "tag": "👑王权处决"},
        "desc": "对生命 <30% 的目标＋35% 伤害",
    },
    "judgment_chain": {  # 审判之链：净化强化
        "name": "审判之链", "kind": "attack", "trigger": "on_hit", "chance": 0.25,
        "effect": {"purge": 2},
        "desc": "攻击 25% 驱散目标 2 层增益",
    },
    "dawn_crown": {  # 晨曦之冠：回春强化
        "name": "晨曦祝福", "kind": "defense", "trigger": "turn_start",
        "effect": {"pct": 0.02},
        "desc": "每刻回复 2% 生命",
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
        "name": "大地护佑", "kind": "defense", "trigger": "stat",
        "effect": {"dmg_reduce": 0.05, "hp_pct": 0.05},
        "desc": "受击伤害－5%，最大生命＋5%",
    },
    "dragon_tongue": {  # 龙语圣剑：攻击叠印记
        "name": "龙语印记", "kind": "attack", "trigger": "on_hit",
        "effect": {"mark_pct": 0.02, "max_mark": 5},
        "desc": "攻击叠加龙语印记(每层＋2% 伤害，上限 5 层)",
    },
    "dawn_light": {  # 黎明之光：深渊特攻
        "name": "黎明破晓", "kind": "attack", "trigger": "passive",
        "effect": {"dmg_mult": 1.50, "enemy_contains": ["深渊"], "tag": "🌅黎明破晓"},
        "desc": "对深渊系敌人＋50% 伤害",
    },
    "moro_crown": {  # 摩罗之冠：受击腐蚀
        "name": "深渊腐蚀", "kind": "defense", "trigger": "on_taken", "chance": 0.15,
        "effect": {"pct": 0.10, "turns": 2},
        "desc": "受击 15% 使敌人攻击－10%(2 刻)",
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
        "effect": {"pct": 0.50},
        "desc": "受击 20% 概率触发灰烬壁垒：反弹 50% 伤害",
    },
    "goblin_crown": {  # v104 修复（M06 P2-7）：咕噜的皇冠——哥布林王的威仪
        "name": "咕噜王的威仪", "kind": "defense", "trigger": "stat",
        "effect": {"hp_pct": 0.06},
        "desc": "最大生命＋6%",
    },
    "mu_ying_blade": {  # v104 修复（M06 P1-4）：暮影之刃——暮色中取人性命
        "name": "暮影", "kind": "attack", "trigger": "stat",
        "effect": {"crit": 0.08},
        "desc": "暴击率＋8%",
    },
    "jin_he_heart": {  # v104 M20 P2：烬核之心（岩浆王·烬核）——核心熔铸的灼热法杖
        "name": "烬核余温", "kind": "attack", "trigger": "stat",
        "effect": {"crit_dmg": 0.25},
        "desc": "暴击伤害＋25%",
    },
    "mu_ying_soul": {  # v104 M20 P2：暮影龙魂（龙陨战魂·暮影）——古龙残魂凝成的大剑
        "name": "龙魂低吟", "kind": "attack", "trigger": "stat",
        "effect": {"crit": 0.08},
        "desc": "暴击率＋8%",
    },
    "silver_bell_rod": {  # v124 垂钓线终奖：传说钓竿·银铃之竿——愿者上钩
        "name": "愿者上钩", "kind": "attack", "trigger": "stat",
        "effect": {"luck": 0.10},
        "desc": "垂钓者的眷顾：掉落收益＋10%",
    },
    "rong_lu_heart": {  # v124 H8：熔炉之心——大地的心跳（矮人先祖炉传说武器）
        "name": "大地心跳", "kind": "attack", "trigger": "stat",
        "effect": {"crit": 0.06, "hp_pct": 0.08},
        "desc": "暴击率＋6%，最大生命＋8%",
    },
    # ================= v130.2c 资源联动套装传说专属（6 件橙装，stat 型——并入/战斗消费均走既有通用路径） =================
    "element_apostle_wand": {  # 元素使徒法杖：元素共鸣
        "name": "元素共鸣", "kind": "attack", "trigger": "stat",
        "effect": {"thunder_dmg": 0.15, "ice_dmg": 0.15},
        "desc": "雷/冰属性伤害＋15%",
    },
    "element_apostle_crown": {  # 元素使徒之冠：使徒荣光
        "name": "使徒荣光", "kind": "defense", "trigger": "stat",
        "effect": {"hp_pct": 0.06},
        "desc": "最大生命＋6%",
    },
    "element_apostle_robe": {  # 元素使徒长袍：使徒庇护
        "name": "使徒庇护", "kind": "defense", "trigger": "stat",
        "effect": {"dmg_reduce": 0.05},
        "desc": "受击伤害－5%",
    },
    "element_apostle_pendant": {  # 元素使徒坠饰：使徒之印
        "name": "使徒之印", "kind": "attack", "trigger": "stat",
        "effect": {"crit_dmg": 0.20},
        "desc": "暴击伤害＋20%",
    },
    "time_lord_scepter": {  # 时之领主秘仪：时之低语
        "name": "时之低语", "kind": "attack", "trigger": "stat",
        "effect": {"cdr": 0.08},
        "desc": "冷却缩减＋8%",
    },
    "time_lord_ring": {  # 时之领主时戒：时光流转
        "name": "时光流转", "kind": "attack", "trigger": "stat",
        "effect": {"crit_dmg": 0.18},
        "desc": "暴击伤害＋18%",
    },
    "chu_huo": {  # v140 灰烬圣剑·初火（Lv95 终章任务传说剑）：初火余烬
        "name": "初火余烬", "kind": "attack", "trigger": "on_hit", "chance": 0.20,
        "effect": {"element": "fire", "pct": 0.08, "burn_pct": 0.015, "burn_turns": 3},
        "desc": "攻击附加 8% 火属性伤害，20% 概率使目标灼烧（每刻损 1.5% 最大生命，3 刻）",
    },
    # ================= D2 基础效果库扩充（D2_design.md：24 个 = 7 完整 + 17 名字补全） =================
    "dragon_scale": {  # D2 龙鳞庇护：全元素抗性+15%、深渊抗性+5%，代价最大生命-10%
        "name": "龙鳞庇护", "kind": "defense", "trigger": "stat",
        "effect": {"elem_res": 0.15, "abyss_res": 0.05, "hp_pct": -0.10},
        "desc": "全元素抗性＋15%、深渊抗性＋5%，代价最大生命－10%",
    },
    "obsidian_aegis": {  # D2 黑曜壁垒：受击10%获得8%最大生命护盾
        "name": "黑曜壁垒", "kind": "defense", "trigger": "on_taken", "chance": 0.10,
        "effect": {"pct": 0.08, "turns": 3},
        "desc": "受击 10% 获得 8% 最大生命护盾（3 刻）",
    },
    "iron_bastion": {  # D2 铁壁意志：受击20%使敌人下一次攻击-25%
        "name": "铁壁意志", "kind": "defense", "trigger": "on_taken", "chance": 0.20,
        "effect": {"pct": 0.25},
        "desc": "受击 20% 使敌人下一次攻击－25%",
    },
    "steady_core": {  # D2 磐石之心：受击15%免疫眩晕/减速且回3%生命
        "name": "磐石之心", "kind": "defense", "trigger": "on_taken", "chance": 0.15,
        "effect": {"cc_resist": 0.5, "heal_pct": 0.03},
        "desc": "受击 15% 免疫眩晕/减速且回复 3% 最大生命",
    },
    "life_spring": {  # D2 生命泉涌：每刻回3%最大生命
        "name": "生命泉涌", "kind": "defense", "trigger": "turn_start",
        "effect": {"pct": 0.03},
        "desc": "每刻回复 3% 最大生命",
    },
    "arcane_ward": {  # D2 奥术屏障：战斗开始15%最大生命护盾3 刻
        "name": "奥术屏障", "kind": "defense", "trigger": "battle_start",
        "effect": {"shield_hp_pct": 0.15, "turns": 3},
        "desc": "战斗开始获得 15% 最大生命护盾（3 刻）",
    },
    "grim_ward": {  # D2 亡者守护：生命>50%时受击-7%
        "name": "亡者守护", "kind": "defense", "trigger": "passive",
        "effect": {"dmg_taken_mult": 0.93, "cond": "hp_gt_50"},
        "desc": "生命 >50% 时受击伤害－7%",
    },
    "storm_herald": {  # D2 风暴使者：雷伤+15%，元素抗性+5%
        "name": "风暴使者", "kind": "attack", "trigger": "stat",
        "effect": {"thunder_dmg": 0.15, "elem_res": 0.05},
        "desc": "雷属性伤害＋15%，元素抗性＋5%",
    },
    "frost_veil": {  # D2 霜结之纱：冰伤+20%，速度+5%
        "name": "霜结之纱", "kind": "attack", "trigger": "stat",
        "effect": {"ice_dmg": 0.20, "spd_pct": 0.05},
        "desc": "冰属性伤害＋20%，速度＋5%",
    },
    "crimson_fang": {  # D2 猩红獠牙：吸血+10%，代价暴伤-10%
        "name": "猩红獠牙", "kind": "attack", "trigger": "stat",
        "effect": {"lifesteal": 0.10, "crit_dmg": -0.10},
        "desc": "吸血＋10%，代价暴击伤害－10%",
    },
    "soul_devourer": {  # D2 噬魂者：攻击15%将6%伤害转生命
        "name": "噬魂者", "kind": "attack", "trigger": "on_hit", "chance": 0.15,
        "effect": {"heal_pct": 0.06},
        "desc": "攻击 15% 将 6% 伤害转为生命",
    },
    "executioner": {  # D2 处刑者：低血处决强化（斩杀线 30%）
        "name": "处刑者", "kind": "attack", "trigger": "passive",
        "effect": {"dmg_mult": 1.40, "execute_threshold": 0.30, "tag": "⚔️处刑者"},
        "desc": "对生命 <30% 的目标＋40% 伤害",
    },
    "sun_blaze": {  # D2 烈日迸发：攻击15%概率80%额外火伤
        "name": "烈日迸发", "kind": "attack", "trigger": "on_hit", "chance": 0.15,
        "effect": {"element": "fire", "pct": 0.80},
        "desc": "攻击 15% 概率造成 80% 额外火属性伤害",
    },
    "chain_overload": {  # D2 连锁过载：攻击15%追加60%雷伤
        "name": "连锁过载", "kind": "attack", "trigger": "on_hit", "chance": 0.15,
        "effect": {"extra_atk": 0.60, "element": "thunder"},
        "desc": "攻击 15% 概率连锁过载：追加 60% 雷属性伤害",
    },
    "mark_hunt": {  # D2 猎杀印记：对标记目标增伤（被动）
        "name": "猎杀印记", "kind": "attack", "trigger": "passive",
        "effect": {"dmg_mult": 1.25, "enemy_marked": True, "tag": "🎯猎杀印记"},
        "desc": "对标记/被集火目标＋25% 伤害",
    },
    "giant_slayer": {  # D2 巨人屠戮：对巨人系增伤
        "name": "巨人屠戮", "kind": "attack", "trigger": "passive",
        "effect": {"dmg_mult": 1.25, "enemy_contains": ["巨人"], "tag": "🗿巨人屠戮"},
        "desc": "对巨人系敌人＋25% 伤害",
    },
    "memory_tear": {  # D2 记忆撕裂：攻击15%沉默目标1 刻
        "name": "记忆撕裂", "kind": "attack", "trigger": "on_hit", "chance": 0.15,
        "effect": {"silence": 1},
        "desc": "攻击 15% 撕裂目标记忆，使其沉默 1 刻",
    },
    "war_cry": {  # D2 战吼：战斗开始攻击强化
        "name": "战吼", "kind": "attack", "trigger": "battle_start",
        "effect": {"atk_up": 2, "tag": "📣战吼"},
        "desc": "战斗开始战吼：攻击大幅提升（2 刻）",
    },
    "top_hunter": {  # D2 猎首者：对精英敌人增伤
        "name": "猎首者", "kind": "attack", "trigger": "passive",
        "effect": {"dmg_mult": 1.15, "enemy_role": "elite", "tag": "🏹猎首者"},
        "desc": "对精英敌人＋15% 伤害",
    },
    "mortal_wound": {  # D2 致伤重击：攻击20%使目标受治疗-30%（heal_down 层=10%/刻，3层=30%）
        "name": "致伤重击", "kind": "attack", "trigger": "on_hit", "chance": 0.20,
        "effect": {"heal_down": 3},
        "desc": "攻击 20% 使目标重伤：受治疗－30%（3 刻）",
    },
    "arcane_echo": {  # D2 秘法回响：施放技能15%下次技能伤害+15%
        "name": "秘法回响", "kind": "attack", "trigger": "on_hit", "chance": 0.15,
        "effect": {"next_skill_dmg": 0.15},
        "desc": "施放技能 15% 概率使下次技能伤害＋15%",
    },
    "siphon": {  # D2 汲魂：攻击20%驱散1层增益并回3%生命
        "name": "汲魂", "kind": "attack", "trigger": "on_hit", "chance": 0.20,
        "effect": {"purge": 1, "heal_pct": 0.03},
        "desc": "攻击 20% 驱散目标 1 层增益并回复 3% 最大生命",
    },
    "summon_pact": {  # D2 召唤契约：攻击20%召唤契约生物助战
        "name": "召唤契约", "kind": "attack", "trigger": "on_hit", "chance": 0.20,
        "effect": {"summon": 1},
        "desc": "攻击 20% 概率召唤契约生物助战",
    },
    "last_breath": {  # D2 最后喘息：致命伤害时以20%生命存活（每场1次）
        "name": "最后喘息", "kind": "defense", "trigger": "passive",
        "effect": {"revive": True, "revive_hp": 0.20, "tag": "🌙最后喘息"},
        "desc": "每场 1 次：受到致命伤害时以 20% 最大生命存活",
    },
    # ================= D3-A 前期新效果（D3_A_report.md 新效果清单） =================
    "oath_sword": {  # D3-A 王都誓约之剑：暴击时回复2%最大生命
        "name": "誓约之刃", "kind": "attack", "trigger": "on_hit", "chance": 1.0,
        "effect": {"heal_pct": 0.02, "on_crit": True},
        "desc": "暴击时回复 2% 最大生命",
    },
    "dawn_grace": {  # D3-A 珍珠项链：最大生命+4%
        "name": "晨光恩泽", "kind": "defense", "trigger": "stat",
        "effect": {"hp_pct": 0.04},
        "desc": "最大生命＋4%",
    },
    "sea_breeze": {  # D3-A 海风长弓：闪避率+3%
        "name": "海风祝福", "kind": "defense", "trigger": "stat",
        "effect": {"dodge": 0.03},
        "desc": "闪避率＋3%",
    },
    "lighthouse_ward": {  # D3-A 灯塔之光：受击伤害-3%
        "name": "灯塔守望", "kind": "defense", "trigger": "stat",
        "effect": {"dmg_reduce": 0.03},
        "desc": "受击伤害－3%",
    },
    "morning_dew": {  # D3-A 晨露戒指：每刻回复1%魔力
        "name": "晨露滋养", "kind": "defense", "trigger": "turn_start",
        "effect": {"pct": 0.01},
        "desc": "每刻回复 1% 魔力",
    },
    # ================= D3-B 中期新效果（D3_B_report.md 第三节 12 个） =================
    "kingdom_lion_heart": {  # D3-B 试炼徽章：生命>70%伤害+8%
        "name": "王狮之心", "kind": "attack", "trigger": "passive",
        "effect": {"dmg_mult": 1.08, "cond": "hp_gt_70", "tag": "🦁王狮之心"},
        "desc": "生命 >70% 时伤害＋8%",
    },
    "blood_oath_echo": {  # D3-B 血誓战剑：受击20%回2%生命+下次攻击+10%
        "name": "血誓回响", "kind": "defense", "trigger": "on_taken", "chance": 0.20,
        "effect": {"heal_pct": 0.02, "atk_up": 0.10},
        "desc": "受击 20%：回复 2% 最大生命，下次攻击＋10%",
    },
    "sanctum_light": {  # D3-B 圣殿战锤：命中15%敌人攻击-8%（v180E 字段改引擎标准键 mon_atk_down）
        "name": "圣殿辉光", "kind": "attack", "trigger": "on_hit", "chance": 0.15,
        "effect": {"mon_atk_down_pct": 0.08, "turns": 1},
        "desc": "攻击命中 15%：敌人攻击－8%（1 刻）",
    },
    "ember_furnace": {  # D3-B 熔岩护手：命中20%灼烧1%×2 刻
        "name": "熔炉余烬", "kind": "attack", "trigger": "on_hit", "chance": 0.20,
        "effect": {"burn_pct": 0.01, "burn_turns": 2},
        "desc": "攻击命中 20%：灼烧 1% 最大生命×2 刻",
    },
    "surge_ready": {  # D3-B 蓄势拳套：战斗开始下一次攻击+15%
        "name": "蓄势待发", "kind": "attack", "trigger": "battle_start",
        "effect": {"next_atk_up": 0.15},
        "desc": "战斗开始：下一次攻击＋15%",
    },
    "night_watch": {  # D3-B 长夜徽记：受击5%回1%生命
        "name": "长夜守望", "kind": "defense", "trigger": "on_taken", "chance": 0.05,
        "effect": {"heal_pct": 0.01},
        "desc": "受击 5%：回复 1% 最大生命",
    },
    "beast_ward": {  # D3-B 裂鬃獠牙：反伤+5%
        "name": "兽性庇护", "kind": "defense", "trigger": "stat",
        "effect": {"thorns": 0.05},
        "desc": "反伤＋5%",
    },
    "captain_insight": {  # D3-B 船长的望远镜：幸运+6%
        "name": "船长洞察", "kind": "attack", "trigger": "stat",
        "effect": {"luck": 0.06},
        "desc": "幸运＋6%",
    },
    "abyss_anchor": {  # D3-B 深渊之锚：深渊抗+8%元素抗+6%
        "name": "深渊锚护", "kind": "defense", "trigger": "stat",
        "effect": {"abyss_res": 0.08, "elem_res": 0.06},
        "desc": "深渊抗性＋8%，元素抗性＋6%",
    },
    "moon_shadow": {  # D3-B 月影斗篷：闪避+4%
        "name": "月影庇护", "kind": "defense", "trigger": "stat",
        "effect": {"dodge": 0.04},
        "desc": "闪避＋4%",
    },
    "ranger_precision": {  # D3-B 巡林长弓：精准+6%
        "name": "巡林精准", "kind": "attack", "trigger": "stat",
        "effect": {"precise": 0.06},
        "desc": "精准＋6%",
    },
    "jade_wealth": {  # D3-B 翡翠之心：金币收益+5%
        "name": "翡翠生财", "kind": "attack", "trigger": "stat",
        "effect": {"gold_bonus": 0.05},
        "desc": "金币收益＋5%",
    },
    # ================= D3-C 后期新效果（D3_C_report.md 第二节 6 个） =================
    "blazing_sun": {  # D3-C 铁砧战锤：附加8%火伤+15%灼烧
        "name": "烈日灼烧", "kind": "attack", "trigger": "on_hit", "chance": 0.15,
        "effect": {"element": "fire", "pct": 0.08, "burn_pct": 0.015, "burn_turns": 3},
        "desc": "攻击附加 8% 火属性伤害，15% 概率使目标灼烧（每刻损 1.5% 最大生命，3 刻）",
    },
    "deep_frost": {  # D3-C 银叶法杖：附加8%冰伤+减速20%2 刻
        "name": "深寒", "kind": "attack", "trigger": "on_hit", "chance": 0.20,
        "effect": {"element": "ice", "pct": 0.08, "slow": 0.20, "slow_turns": 2},
        "desc": "攻击附加 8% 冰属性伤害并减速目标（速度－20%，2 刻）",
    },
    "thunder_mark": {  # D3-C 雷鸣龙鳞：攻击20%叠雷鸣印记
        "name": "雷鸣印记", "kind": "attack", "trigger": "on_hit", "chance": 0.20,
        "effect": {"mark_pct": 0.02, "max_mark": 5},
        "desc": "攻击 20% 叠加雷鸣印记（每层＋2% 伤害，上限 5 层）",
    },
    "wolf_howl": {  # D3-C 霜狼长剑：战斗开始本场伤害+10%
        "name": "狼嚎", "kind": "attack", "trigger": "battle_start",
        "effect": {"cond": "battle_start", "dmg_mult": 1.10, "tag": "🐺狼嚎"},
        "desc": "战斗开始时嚎叫：本场战斗伤害＋10%",
    },
    "night_prayer": {  # D3-C 夜祷兜帽：每刻回3%最大生命
        "name": "夜祷", "kind": "defense", "trigger": "turn_start",
        "effect": {"pct": 0.03},
        "desc": "每刻回复 3% 最大生命",
    },
    "crimson_tide": {  # D3-C 海神戒指：吸血+10%代价暴伤-10%
        "name": "猩红潮汐", "kind": "attack", "trigger": "stat",
        "effect": {"lifesteal": 0.10, "crit_dmg": -0.10},
        "desc": "吸血＋10%，代价暴击伤害－10%",
    },
    # ================= D3-D 末期新效果（D3_D_report.md 第二节 6 个） =================
    "xing_hui_zhi_guan": {  # D3-D 星辉之冠：暴伤+15%闪避+5%
        "name": "星辉守护", "kind": "defense", "trigger": "stat",
        "effect": {"crit_dmg": 0.15, "dodge": 0.05},
        "desc": "暴击伤害＋15%、闪避＋5%",
    },
    "xing_he_fa_zhang": {  # D3-D 星河法杖：冰伤+20%暴击+5%
        "name": "冰嚎", "kind": "attack", "trigger": "stat",
        "effect": {"ice_dmg": 0.20, "crit": 0.05},
        "desc": "冰属性伤害＋20%、暴击率＋5%",
    },
    "shuang_lang_zhi_wang_ya": {  # D3-D 霜狼之王牙：全元素抗+10%韧性+5%
        "name": "霜墙防线", "kind": "defense", "trigger": "stat",
        "effect": {"elem_resist": 0.10, "tenacity": 0.05},
        "desc": "全元素抗性＋10%、韧性＋5%——以寒霜筑起无形防线",
    },
    "bing_hao_zhan_ren": {  # D3-D 冰嚎战刃：冰伤+15%韧性+5%
        "name": "永冻之心", "kind": "defense", "trigger": "stat",
        "effect": {"ice_dmg": 0.15, "tenacity": 0.05},
        "desc": "冰属性伤害＋15%、韧性＋5%",
    },
    "frozen_heart": {  # D3-D 永冻之心：深渊抗+10%最大生命+5%
        "name": "深渊守望", "kind": "defense", "trigger": "stat",
        "effect": {"abyss_resist": 0.10, "hp_pct": 0.05},
        "desc": "深渊抗性＋10%、最大生命＋5%",
    },
    "death_wall": {  # D3-D 死亡防线：韧性+8%代价最大生命-5%
        "name": "死亡防线", "kind": "defense", "trigger": "stat",
        "effect": {"tenacity": 0.08, "hp_pct": -0.05},
        "desc": "韧性＋8%，代价最大生命－5%——以血肉为墙",
    },
    # ================= D3-E 终局新效果（D3_E_report.md 第二节 6 个） =================
    "night_eater_mask": {  # D3-E 蚀夜之面：暗夜闪避+8%
        "name": "蚀夜", "kind": "defense", "trigger": "stat",
        "effect": {"dodge": 0.08},
        "desc": "暗夜闪避＋8%",
    },
    "storm_crown": {  # D3-E 风暴之冠：雷属性伤害+20%
        "name": "风暴之冠", "kind": "attack", "trigger": "stat",
        "effect": {"thunder_dmg": 0.20},
        "desc": "雷属性伤害＋20%",
    },
    "cloud_rage_core": {  # D3-E 云怒之核：雷属性伤害+20%
        "name": "云怒雷核", "kind": "attack", "trigger": "stat",
        "effect": {"thunder_dmg": 0.20},
        "desc": "雷属性伤害＋20%",
    },
    "star_destruction": {  # D3-E 黑渊之眼：对深渊系+30%伤害
        "name": "星陨湮灭", "kind": "attack", "trigger": "passive",
        "effect": {"dmg_mult": 1.30, "enemy_contains": ["深渊"], "tag": "☄️星陨湮灭"},
        "desc": "对深渊系敌人＋30% 伤害",
    },
    "dragon_annihilation": {  # D3-E 深渊骑枪：对龙系+25%伤害
        "name": "灭龙", "kind": "attack", "trigger": "passive",
        "effect": {"dmg_mult": 1.25, "enemy_contains": ["龙"], "tag": "🐉灭龙"},
        "desc": "对龙系敌人＋25% 伤害",
    },
    "divine_execution": {  # D3-E 辰光法杖：对生命<30%目标+60%伤害
        "name": "神罚处决", "kind": "attack", "trigger": "passive",
        "effect": {"dmg_mult": 1.60, "execute_threshold": 0.30, "tag": "⚡神罚处决"},
        "desc": "对生命 <30% 的目标额外＋60% 伤害",
    },
    # ===== v169 职业断档补档橙装专属（4 件，2026-09-03） =====
    "holy_edict": {  # 圣谕权杖：治疗强化+溢盾
        "name": "圣谕回响", "kind": "defense", "trigger": "stat",
        "effect": {"heal_power": 0.15, "shield_hp_pct": 0.12},
        "desc": "治疗量＋15%，治疗溢出 15% 转化为护盾（上限 12% 最大生命）",
    },
    "star_shatter": {  # 碎星拳套：破甲重拳
        "name": "碎星拳劲", "kind": "attack", "trigger": "on_hit", "chance": 0.25,
        "effect": {"dmg_mult": 1.50, "ignore_def": 0.30, "debuff": "def", "pct": 0.15, "turns": 2, "tag": "💥碎星拳劲"},
        "desc": "攻击 25% 造成 150% 伤害的破甲重拳（无视 30% 防御），并降低目标防御 15%（2 刻）",
    },
    "dark_star_gauntlet": {  # 暗星拳甲：叠层爆发（攻击计数叠层，满层下一次攻击爆发并清空）
        "name": "暗星连打", "kind": "attack", "trigger": "on_hit",
        "effect": {"mark_pct": 0.03, "max_mark": 4, "next_atk_mult": 1.20, "tag": "🌑暗星连打"},
        "desc": "攻击命中叠 1 层暗星（上限 4 层，每层伤害 +3%），叠满后下一次攻击额外 +120% 伤害并清空",
    },
    "gale_dirge": {  # 疾风挽歌：连矢追猎
        "name": "挽歌连矢", "kind": "attack", "trigger": "on_hit", "chance": 0.25,
        "effect": {"extra_atk": 0.50, "enemy_contains": ["召唤"], "tag": "🌪️挽歌连矢"},
        "desc": "攻击命中 25% 追加一支 50% 伤害的疾风矢（优先攻击召唤物）",
    },
    "shadow_raid": {  # 影袭之刃：暴击追击回血
        "name": "影袭连刺", "kind": "attack", "trigger": "on_crit", "chance": 0.50,
        "effect": {"extra_atk": 0.40, "lifesteal": 0.02, "tag": "🗡️影袭连刺"},
        "desc": "暴击后 50% 概率追加一次 40% 伤害的追击，并回复 2% 最大生命",
    },
}

# 系列固定词条（20 章 3.x；橙装固定词条 + 专属见 EQUIP_ROSTER）
# 值 = 词条 ID 列表，装备生成时作为"固定词条"（不参与随机）
SERIES_FIXED_AFFIX = {
    # 橡木（新手无固定词条，纯基础）
    "铁剑": [], "猎弓": [], "学徒法杖": [], "橡木短棍": [],
    "皮甲": [], "旧皮靴": [], "橡木护腿": [],
    # v105 M07 P3-5：白鹿皮甲改名橡木皮甲（名字与橡木套归属一致，消除误导）
    "橡木盾": ["block"], "猎鹿弓": ["precise"], "学徒之杖": ["meditate"], "橡木皮甲": ["dodge"],
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
    # v104 修复（M06 P2-7）：咕噜的皇冠（哥布林酋长传说图纸装备）
    "咕噜的皇冠": ["tenacity"],
    # v168 副本 Boss 掉落池新增主题装固定词条（咕噜/幽灵/海盗系）
    "咕噜金戒": ["crit_up", "meditate"], "哥布林军刀": ["combo", "swift"], "咕噜战徽": ["hp_up", "tenacity"],
    "幽灵军旗": ["lifesteal", "pierce"], "骑士残甲": ["dmg_reduce", "shield"], "要塞石章": ["tenacity", "dmg_reduce"],
    "杰克的金币袋": ["dodge", "swift"], "锈锚护手": ["block", "tenacity"],
    # 圣光
    "圣光长剑": ["armor_break"], "晨曦法杖": ["meditate"],
    "王都长弓": ["pierce", "precise"], "圣殿战锤": ["charge", "execute"],
    "骑士头盔": ["dmg_reduce"], "圣光胸甲": ["shield"], "骑士长靴": ["tenacity"],
    "圣光护腿": ["dmg_reduce"],
    "圣光护符": ["purify", "meditate"], "王国徽戒": ["crit_up", "break_magic"],
    # v104 M07 修复 P1：Lv.35-49 断档补档（圣光系列锻造蓝装，词条与 28-34 级圣光同主题）
    "圣光战盔": ["dmg_reduce"], "圣光重甲": ["shield"], "圣光重靴": ["tenacity"],
    "圣光战腿": ["dmg_reduce"], "圣裁长剑": ["armor_break"], "圣光法杖": ["meditate"],
    "圣光猎弓": ["precise"], "圣光战锤": ["charge"],
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
    # v101.30d playtest O44/O45 补齐件数词条（与同套风格一致）
    "银铃头盔": ["swift"], "银铃胸甲": ["swift", "dodge"], "银铃战靴": ["swift"], "银铃项链": ["swift"],
    "翡翠头盔": ["dodge"], "翡翠战靴": ["dodge"], "翡翠项链": ["dodge"],
    "迷雾胸甲": ["swift", "dodge"], "迷雾战靴": ["swift"], "迷雾项链": ["swift"],
    "猎风长弓": ["precise", "swift"], "疾风长弓": ["precise", "pierce"],
    # v104 M08 P1-5：SHOP_WEAPONS 9 件补录名册的固定词条（对齐同系列/同武器类型风格：
    # 白鹿=敏捷闪避风、铁港=海风暴击风；蓝装 1 词条）
    "精铁长剑": ["crit_up"], "硬木战弓": ["precise"], "祈愿法杖": ["meditate"],
    "铁头战锤": ["charge"], "厚皮拳套": ["combo"],
    "水手弯刀": ["crit_up"], "远洋长弓": ["precise"], "铁锚战锤": ["charge"],
    "铁链拳套": ["combo"],
    # v104 M20 P1：支线奖励「汉斯的手工武器」（白鹿蓝装剑，对齐精铁长剑风格）
    "汉斯的手工武器": ["crit_up"],
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
    # v104 修复（M06 P1-4）：暮影之刃（暮影龙魂图纸装备，匕首风格）
    "暮影之刃": ["crit_up", "combo"],
    # v104 M20 P2：7 张支线奖励图纸装备固定词条（Boss 主题，s27/s33 复用现有澜歌之泪/奥拉圣印词条）
    "裂鬃獠牙": ["combo", "armor_break"],      # 连击/破甲（野猪王·裂鬃）
    "铁牙狼皮": ["dodge", "swift"],            # 闪避/敏捷（丘陵狼王·铁牙）
    "雷鸣龙鳞": ["thorns", "block"],           # 反伤/格挡（风暴海龙·雷鸣）
    "烬核之心": ["element_fire", "combo"],     # 灼烧/连击（岩浆王·烬核）
    "暮影龙魂": ["lifesteal", "combo"],        # 吸血/连击（龙陨战魂·暮影）
    # v124 支线奖励装备固定词条（复用现有词条 ID）
    "白桦的护符": ["precise", "crit_up"],       # 精准/暴击强化（s18 善结局：精准+10%、暴击+5%）
    "长夜徽记": ["tenacity"],                   # 韧性（s51 长夜节，长夜守候的坚毅）
    "传说钓竿·银铃之竿": ["luck", "meditate"],  # 幸运/冥想（垂钓者的耐心与眷顾）
    "守夜者徽章": ["tenacity", "dmg_reduce"],   # 韧性/减伤（s84 老兵不屈）
    "松木护符": ["regen"],                      # 回春（s121 守林人护符，林间生机）
    "猫眼石胸针": ["swift"],                    # 迅捷（s78 侦探线，速度+5%）
    # v124 支线图纸装备固定词条（H5 夜行披风 / H8 熔炉之心）
    "夜行披风": ["dodge", "swift"],             # 闪避/迅捷（夜行者的隐秘身法）
    "熔炉之心": ["element_fire", "charge"],     # 灼烧/冲锋（先祖炉熔铸的大地之力）
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
    # ================= v130.2c 资源联动套装固定词条（41 件，对齐同级名册风格） =================
    # 血誓战团（战士·通用基础）
    "血誓战剑": ["crit_up", "charge"], "血誓战甲": ["dmg_reduce", "block"],
    # 余烬军团徽章（战士·攻线）
    "余烬军团战剑": ["execute", "crit_up"], "余烬军团战盔": ["tenacity", "hp_up"],
    "余烬军团胸甲": ["dmg_reduce", "thorns"], "余烬军团战靴": ["swift", "tenacity"],
    # 元素使徒（法师·基础/转职通用）
    "元素使徒法杖": ["element_fire", "element_ice", "meditate"],
    "元素使徒之冠": ["meditate", "magic_ward", "tenacity"],
    "元素使徒长袍": ["magic_ward", "dmg_reduce", "regen"],
    "元素使徒坠饰": ["crit_up", "meditate", "element_thunder"],
    # 时之领主（法师·隐藏线 时咒）
    "时之领主秘仪": ["meditate", "cdr", "element_thunder"],
    "时之领主时戒": ["crit_up", "cdr", "meditate"],
    # 巡林长披风（游侠·散件配套）
    "巡林长披风": ["dodge", "swift"], "巡林长弓": ["precise", "hunt"],
    # 猎首远征队徽记（游侠·攻线）
    "猎首长弓": ["hunt", "crit_up"], "猎首皮帽": ["precise", "swift"],
    "猎首皮甲": ["dodge", "swift"], "猎首长靴": ["swift", "precise"],
    # 圣典·日冕（牧师·平稳/爆发流）
    # v130.2d R2：日冕权杖为紫装，原固定词条 holy_heart（橙）品质外溢 → 换 purple 档 divine_radiance
    "日冕权杖": ["divine_radiance", "meditate"], "日冕圣冠": ["holy_echo", "tenacity"],
    "日冕法衣": ["holy_echo", "magic_ward"], "日冕圣靴": ["swift", "meditate"],
    # 暗夜圣典（牧师·暗影神谕 悼咏）
    "夜祷权杖": ["purify", "meditate"], "夜祷兜帽": ["tenacity", "dodge"],
    "夜祷法衣": ["magic_ward", "dodge"], "夜祷之戒": ["meditate", "tenacity"],
    # 圣徽·誓约（牧师·新手保底）
    # v130.2d R2：誓约权杖为蓝装，原固定词条 holy_heart（橙）品质外溢 → 换 blue 档 pious_charm（受击回信仰，契合 bonus_2）
    "誓约权杖": ["pious_charm", "meditate"], "誓约圣冠": ["holy_echo", "tenacity"],
    "誓约法衣": ["holy_echo", "magic_ward"], "誓约圣靴": ["swift", "meditate"],
    # 夜幕合契·影纱（刺客·轻甲/武器 5 件套）
    "影纱之刃": ["crit_up", "combo"], "影纱面巾": ["dodge", "swift"],
    "影纱皮衣": ["dodge", "crit_up"], "影纱护腿": ["dodge", "combo"],
    "影纱轻靴": ["swift", "crit_up"],
    # 蓄势涌动（拳师·通用）
    "蓄势拳套": ["charge", "crit_up"], "蓄势束带": ["tenacity", "hp_up"],
    # 势不可挡（拳师·通用）
    "破竹拳套": ["charge", "armor_break"], "破竹武袍": ["dmg_reduce", "block"],
    "破竹护腿": ["tenacity", "dmg_reduce"], "破竹布靴": ["swift", "tenacity"],

    # ===== v136 Phase6 合并: SERIES_FIXED_AFFIX (180 条) =====
    '铁皮长剑': ['armor_break'],
    '铁皮头盔': ['tenacity'],
    '铁皮胸甲': ['dmg_reduce'],
    '铁皮护腿': ['block'],
    '铁皮战靴': ['tenacity'],
    '精铁战剑': ['charge', 'armor_break'],
    '精铁头盔': ['dmg_reduce', 'tenacity'],
    '精铁胸甲': ['block', 'dmg_reduce'],
    '精铁护腿': ['tenacity', 'dmg_reduce'],
    '精铁战靴': ['swift', 'tenacity'],
    '百炼长剑': ['execute', 'charge', 'armor_break'],
    '百炼头盔': ['tenacity', 'hp_up', 'dmg_reduce'],
    '百炼胸甲': ['dmg_reduce', 'block', 'thorns'],
    '百炼护腿': ['tenacity', 'dmg_reduce', 'hp_up'],
    '百炼战靴': ['swift', 'tenacity', 'dmg_reduce'],
    '见习法杖': ['element_thunder'],
    '学徒法帽': ['meditate'],
    '学徒长袍': ['dodge'],
    '学徒护腿': ['meditate'],
    '学徒法靴': ['swift'],
    '符文法杖': ['element_thunder', 'crit_up'],
    '符文法帽': ['meditate', 'tenacity'],
    '符文长袍': ['dodge', 'magic_ward'],
    '符文护腿': ['meditate', 'magic_ward'],
    '符文法靴': ['swift', 'meditate'],
    '秘法法杖': ['element_thunder', 'pene_magi', 'crit_up'],
    '秘法法帽': ['meditate', 'tenacity', 'magic_ward'],
    '秘法长袍': ['magic_ward', 'dodge', 'regen'],
    '秘法护腿': ['meditate', 'magic_ward', 'tenacity'],
    '秘法法靴': ['swift', 'meditate', 'dodge'],
    '布衣权杖': ['purify'],
    '布衣圣冠': ['holy_echo'],
    '布衣法衣': ['heal_power'],
    '布衣护腿': ['holy_echo'],
    '布衣圣靴': ['swift'],
    '祝福权杖': ['purify', 'meditate'],
    '祝福圣冠': ['holy_echo', 'tenacity'],
    '祝福法衣': ['holy_echo', 'magic_ward'],
    '祝福护腿': ['heal_power', 'tenacity'],
    '祝福圣靴': ['swift', 'meditate'],
    '圣堂权杖': ['purify', 'divine_radiance', 'meditate'],
    '圣堂圣冠': ['holy_echo', 'tenacity', 'magic_ward'],
    '圣堂法衣': ['holy_echo', 'magic_ward', 'regen'],
    '圣堂护腿': ['heal_power', 'tenacity', 'magic_ward'],
    '圣堂圣靴': ['swift', 'meditate', 'holy_echo'],
    '猎手短弓': ['precise'],
    '猎手皮帽': ['swift'],
    '猎手皮甲': ['swift'],
    '猎手护腿': ['swift'],
    '猎手长靴': ['swift'],
    '风行长弓': ['precise', 'hunt'],
    '风行皮帽': ['swift'],
    '风行皮甲': ['swift', 'dodge'],
    '风行护腿': ['swift'],
    '风行长靴': ['swift'],
    '暗夜长弓': ['crit_up', 'precise', 'hunt'],
    '暗夜皮帽': ['swift', 'dodge'],
    '暗夜皮甲': ['swift', 'dodge'],
    '暗夜护腿': ['swift', 'crit_up'],
    '暗夜长靴': ['swift', 'dodge'],
    '轻影匕首': ['combo'],
    '轻影面巾': ['dodge'],
    '轻影皮衣': ['dodge'],
    '轻影护腿': ['swift'],
    '轻影轻靴': ['swift'],
    '夜行匕首': ['crit_up', 'combo'],
    '夜行面巾': ['dodge'],
    '夜行皮衣': ['dodge'],
    '夜行护腿': ['swift'],
    '夜行轻靴': ['swift'],
    '阴影匕首': ['crit_up', 'combo', 'pene_phys'],
    '阴影面巾': ['dodge', 'swift'],
    '阴影皮衣': ['dodge', 'swift'],
    '阴影护腿': ['swift', 'dodge'],
    '阴影轻靴': ['swift', 'dodge'],
    '行者拳套': ['charge'],
    '行者束发带': ['block'],
    '行者武斗袍': ['tenacity'],
    '行者护腿': ['block'],
    '行者布靴': ['tenacity'],
    '石拳拳套': ['charge', 'counter'],
    '石拳束发带': ['block'],
    '石拳武斗袍': ['tenacity', 'block'],
    '石拳护腿': ['block'],
    '石拳布靴': ['tenacity'],
    '壁槌拳套': ['charge', 'counter', 'lifesteal'],
    '壁槌束发带': ['block', 'tenacity'],
    '壁槌武斗袍': ['tenacity', 'block'],
    '壁槌护腿': ['block', 'tenacity'],
    '壁槌布靴': ['tenacity', 'block'],
    '护林胸甲': ['dmg_reduce'],
    '护林护腿': ['block'],
    '护林之靴': ['tenacity'],
    '精制护林胸甲': ['dmg_reduce', 'block'],
    '精制护林护腿': ['block', 'tenacity'],
    '精制护林之靴': ['tenacity', 'dmg_reduce'],
    '渡口胸甲': ['dodge'],
    '渡口护腿': ['swift'],
    '渡口之靴': ['swift'],
    '精制渡口胸甲': ['dodge', 'swift'],
    '精制渡口护腿': ['swift', 'dodge'],
    '精制渡口之靴': ['swift', 'swift'],
    '巡林胸甲': ['dodge'],
    '巡林护腿': ['swift'],
    '巡林之靴': ['swift'],
    '精制巡林胸甲': ['dodge', 'swift'],
    '精制巡林护腿': ['swift', 'dodge'],
    '精制巡林之靴': ['swift', 'precise'],
    '霜猎胸甲': ['element_ice', 'tenacity'],
    '霜猎护腿': ['element_ice', 'precise'],
    '霜猎之靴': ['swift', 'hunt'],
    '精制霜猎胸甲': ['element_ice', 'tenacity', 'dmg_reduce'],
    '精制霜猎护腿': ['element_ice', 'precise', 'tenacity'],
    '精制霜猎之靴': ['swift', 'hunt', 'element_ice'],
    '龙裔胸甲': ['dragon_aw', 'dmg_reduce'],
    '龙裔护腿': ['dragon_aw', 'block'],
    '龙裔之靴': ['dragon_aw', 'swift'],
    '精制龙裔胸甲': ['dragon_aw', 'dmg_reduce', 'block'],
    '精制龙裔护腿': ['dragon_aw', 'block', 'tenacity'],
    '精制龙裔之靴': ['dragon_aw', 'swift', 'hunt'],
    '猎风披风': ['swift', 'dodge'],
    '猎风护腿': ['swift'],
    '猎风之靴': ['swift'],
    '晨露戒指': ['hp_up'],
    '晨露项链': ['heal_power'],
    '猎户兜帽': ['dodge', 'precise'],
    '猎户夹克': ['crit_up', 'dodge'],
    '猎户长靴': ['swift'],
    '橡木符记': ['crit_up', 'magic_ward'],
    '白鹿护符': ['crit_up'],
    '春草手环': ['magic_ward'],
    '夜莺胸针': ['swift', 'crit_up'],
    '潮汐之环': ['crit_up', 'cdr'],
    '潮汐吊坠': ['crit_up'],
    '锚链护腕': ['phys_ward'],
    '船长的望远镜': ['crit_up', 'precise'],
    '海盗眼罩': ['crit_up'],
    '航海斗篷': ['swift', 'dodge'],
    '深渊之锚': ['crit_up', 'phys_ward'],
    '灯塔之光': ['heal_power'],
    '水手结戒指': ['swift'],
    '潮汐之靴': ['crit_up', 'swift'],
    '铁港徽章': ['phys_ward', 'hp_up'],
    '晨曦之戒': ['heal_power', 'magic_ward'],
    '熔岩护手': ['element_fire', 'thorns'],
    '熔岩护腿': ['crit_up', 'element_fire'],
    '熔岩之靴': ['element_fire', 'tenacity'],
    '月影斗篷': ['dodge', 'swift'],
    '星辉戒指': ['crit_up', 'cdr'],
    '星辉吊坠': ['cdr', 'crit_up'],
    '翡翠之心': ['hp_up', 'magic_ward'],
    '翡翠护符': ['magic_ward'],
    '疾风护手': ['swift'],
    '疾风之靴': ['swift'],
    '月语之戒': ['crit_up', 'swift'],
    '精灵披风': ['dodge'],
    '霜角战环': ['crit_up', 'element_ice'],
    '霜角吊坠': ['phys_ward', 'element_ice'],
    '霜角披风': ['magic_ward', 'dodge'],
    '寒霜之戒': ['crit_up', 'element_ice'],
    '北风护符': ['swift'],
    '龙鳞手环': ['phys_ward', 'tenacity'],
    '龙脊徽记': ['crit_up', 'element_thunder'],
    '猎手斗篷': ['precise', 'dodge'],
    '猎手之靴': ['swift'],
    '铁壁护符': ['phys_ward'],
    '星火戒指': ['crit_up', 'element_fire'],
    '苍狼之爪': ['crit_up', 'crit_dmg'],
    '风暴之眼': ['crit_up', 'cdr'],
    '风暴吊坠': ['crit_up', 'element_thunder'],
    '苍穹之翼': ['swift', 'dodge'],
    '苍穹之靴': ['swift', 'precise'],
    '龙翼护符': ['phys_ward', 'hp_up'],
    '龙翼戒指': ['crit_up', 'crit_dmg'],
    '天穹之冠': ['crit_up', 'crit_dmg'],
    '星光项链': ['heal_power', 'magic_ward'],
    '风神之环': ['swift', 'crit_up'],
    '雷光徽章': ['crit_up', 'element_thunder'],
    '秘银手镯': ['phys_ward', 'magic_ward'],
    '守望者护符': ['crit_up', 'phys_ward'],
    '亡者战靴': ['swift'],
    '亡舞战铠': ['dmg_reduce', 'thorns'],
    '兰顿之戒': ['tenacity_cc'],
    '冰脉护腿': ['tenacity_cc'],
    '咒刃之誓': ['crit_up', 'combo'],
    '噬魂短刃': ['lifesteal'],
    '圣殿战靴': ['swift'],
    '圣裁重锤': ['charge', 'execute'],
    '无终之刃': ['crit_up', 'combo'],
    '星陨长弓': ['pierce', 'precise'],
    '晨曦护符': ['regen'],
    '暮光之刺': ['execute'],
    '暮裂之刃': ['crit_up', 'combo'],
    '死亡之舞': ['dmg_reduce'],
    '永契法典': ['meditate'],
    '永霜秘杖': ['element_ice', 'meditate'],
    '永霜权杖': ['element_ice', 'meditate'],
    '泰坦护腿': ['tenacity', 'dmg_reduce'],
    '海妖之牙': ['pene_phys'],
    '深渊胸甲': ['dmg_reduce'],
    '湮灭法典法杖': ['meditate'],
    '灰烬拳套': ['element_fire', 'combo'],
    '熔岩重剑': ['element_fire'],
    '烬火壁垒': ['thorns'],
    '石像鬼胫甲': ['tenacity'],
    '石像鬼之心': ['shield'],
    '石心拳套': ['counter'],
    '破岳巨剑': ['armor_break'],
    '碎冰长弓': ['element_ice', 'precise'],
    '磐石王冠': ['dmg_reduce'],
    '秘光吊坠': ['meditate'],
    '秘法典籍之杖': ['meditate'],
    '巨鳄鳞甲': ['dmg_reduce'],
    '古树枝杖': ['regen'],
    '荆棘战甲': ['thorns'],
    '虚空行者之靴': ['swift'],
    '蚀月之冠': ['dmg_reduce'],
    '血潮短刃': ['bleed'],
    '血痕双刺': ['bleed'],
    '裂风长弓': ['pierce', 'precise'],
    '裂鬃战盔': ['tenacity'],
    '赎罪圣杖': ['purify', 'meditate'],
    '要塞幽灵之盔': ['swift'],
    '骸王骨面': ['swift'],
    '克罗的罗盘': ['crit_up', 'swift'],
    '铁港战刃': ['crit_up'],
    '铁港圆盾': ['block'],
    '铁牙战盔': ['block'],
    '巨魔獠牙坠': ['crit_up', 'swift'],
    '灰影狼牙刃': ['combo'],
    '铸火头盔': ['thorns'],
    '雷纹拳甲': ['element_thunder', 'combo'],
    '雷霆指环': ['element_thunder', 'crit_up'],
    '霜语法杖': ['element_ice', 'meditate'],
    '风行短弓': ['precise', 'hunt'],
    '逐风长弓': ['precise', 'hunt'],

    # ===== v140 波2 批量补全固定词条（SA-2，179 件蓝紫橙） =====
    '学徒之血刃': ['lifesteal'],
    '旅人之盾': ['block'],
    '旅人皮甲': ['dmg_reduce'],
    '星火法杖': ['element_fire'],
    '猎影之牙': ['combo'],
    '翠风之弓': ['swift'],
    '远行兜帽': ['dodge'],
    '晨星吊坠': ['meditate'],
    '王都誓约之剑': ['lifesteal'],
    '圣光之握': ['heal_power'],
    '圣光审判之刃': ['armor_break'],
    '圣光庇护之盾': ['block'],
    '圣光祝福指环': ['crit_up'],
    '圣光祈祷法杖': ['meditate'],
    '圣光追猎长弓': ['precise'],
    '圣光殉道者胸甲': ['shield'],
    '圣光哨兵头盔': ['dmg_reduce'],
    '圣光远征护腿': ['dmg_reduce'],
    '圣光巡礼战靴': ['tenacity'],
    '晨曦圣剑': ['crit_up'],
    '曙光壁垒': ['block'],
    '马尔库斯的法冠': ['dmg_reduce'],
    '试炼徽章': ['purify'],
    '圣辉法衣': ['shield'],
    '月语刺客匕首': ['crit_up', 'combo'],
    '月语银月长弓': ['crit_up', 'precise'],
    '月语秘仪法杖': ['element_ice', 'meditate'],
    '月语影袭胸甲': ['dodge', 'swift'],
    '月语夜枭头盔': ['swift'],
    '月语风行者之靴': ['swift'],
    '月语月影护腿': ['swift'],
    '月语辉月项链': ['element_ice', 'meditate'],
    '月语月华之戒': ['crit_up', 'element_ice'],
    '银鬃月刃': ['crit_up', 'combo'],
    '月神之戒': ['crit_up', 'element_ice'],
    '月辉之戒': ['crit_up', 'element_ice'],
    '岚歌羽靴': ['swift'],
    '铁壁战甲': ['dmg_reduce'],
    '铁壁军团剑': ['armor_break'],
    '铁壁壁垒之盾': ['block'],
    '铁壁卫戍头盔': ['dmg_reduce'],
    '铁壁重装战靴': ['tenacity'],
    '铁壁军团腿甲': ['dmg_reduce'],
    '铁壁胸甲': ['dmg_reduce'],
    '霜狼战刃': ['element_ice', 'armor_break'],
    '霜狼猎弓': ['pierce', 'precise'],
    '霜狼冰甲': ['dmg_reduce', 'block'],
    '霜狼雪靴': ['tenacity'],
    '霜狼腿甲': ['tenacity'],
    '霜狼之王牙': ['element_ice'],
    '冰嚎战刃': ['element_ice'],
    '永冻之心': ['element_ice'],
    '霜巨魔战锤': ['element_ice'],
    '霜牙冰刃': ['element_ice'],
    '海神之盾': ['block'],
    '海神波纹甲': ['dodge', 'dmg_reduce'],
    '海神珍珠链': ['element_ice', 'lifesteal'],
    '怒涛三叉戟': ['element_ice', 'pierce'],
    '镇海之盾': ['block'],
    '蓝歌之冠': ['swift'],
    '红棘珊瑚戒': ['element_ice', 'crit_up'],
    '潮汐三叉戟': ['element_ice', 'pierce'],
    '星辉法杖': ['element_thunder', 'meditate'],
    '星辉长袍': ['dodge', 'swift'],
    '星辉法冠': ['swift'],
    '星辉之冠': ['element_thunder', 'crit_up'],
    '星河法杖': ['element_thunder', 'meditate'],
    '猎羽长弓': ['pierce', 'charge'],
    '惊雷战弓': ['element_thunder', 'meditate'],
    '裂空战弓': ['element_thunder', 'crit_up'],
    '幽影短刃': ['dodge', 'combo'],
    '淬毒寒刃': ['bleed'],
    '苍穹护甲': ['dodge', 'swift'],
    '星尘之靴': ['swift'],
    '苍穹之冠': ['swift'],
    '风暴之冠': ['element_thunder', 'crit_up'],
    '云怒之核': ['element_thunder', 'crit_up'],
    '雷霆护肩': ['element_thunder', 'crit_up'],
    '辰光法杖': ['element_thunder', 'meditate'],
    '石龙拳套': ['charge'],
    '撼岳拳套': ['counter'],
    '龙脊鳞甲': ['block', 'dmg_reduce'],
    '圣辉权杖': ['purify', 'meditate'],
    '圣辉胸甲': ['heal_power'],
    '回响之刃': ['combo'],
    '回响之戒': ['heal_power'],
    '哨兵短剑': ['block'],
    '哨兵胸甲': ['block'],
    '见习辉光法杖': ['meditate'],
    '猎户铁匕': ['crit_up', 'combo'],
    '锻火铁拳': ['element_fire', 'combo'],
    '圣木权杖': ['purify', 'meditate'],
    '铁卫战盔': ['dmg_reduce'],
    '铁卫之戒': ['heal_power'],
    '巡林者护腿': ['swift'],
    '疾风轻靴': ['swift'],
    '圣堂卫士护腿': ['dmg_reduce'],
    '迅捷战靴': ['swift'],
    '深岩战盔': ['dmg_reduce'],
    '不灭之戒': ['regen'],
    '不灭意志': ['regen'],
    '反伤之环': ['thorns'],
    '麦酒的祝福': ['heal_power'],
    '誓约之杖·初芽': ['meditate'],
    '誓约长剑·初心': ['charge', 'crit_up'],
    '誓约长弓·新绿': ['precise', 'swift'],
    '誓约权杖·初沐': ['pious_charm', 'meditate'],
    '誓约匕首·初影': ['crit_up', 'combo'],
    '誓约拳套·初锋': ['combo', 'charge'],
    '圣女的遗赠': ['purify', 'meditate'],
    '月冠的守望': ['dodge', 'swift'],
    '烬山守望者之徽': ['thorns'],
    '灰烬圣剑·初火': ['element_fire', 'armor_break'],
    '石炉战锤': ['element_fire'],
    '黑渊之眼': ['thorns', 'tenacity'],
    '深渊骑枪': ['pierce', 'charge'],
    '夜枭双匕': ['crit_up', 'combo'],
    '大贤者秘典': ['meditate'],
    '奔雷大剑': ['element_thunder', 'charge'],
    '奥拉圣剑': ['crit_up', 'crit_dmg'],
    '奥术苍穹之冠': ['element_thunder', 'meditate'],
    '寒霜之冠': ['crit_up', 'element_ice'],
    '岁月之杖': ['regen', 'meditate'],
    '幻影长弓': ['crit_up', 'precise'],
    '弑星巨刃': ['crit_up', 'crit_dmg'],
    '蚀夜之面': ['dodge', 'swift'],
    '黑鸦面巾': ['dodge', 'swift'],
    '时光沙漏': ['meditate', 'cdr'],
    '龙鳞庇护之坠': ['elem_resist', 'hp_up'],


    # ===== v140 波2 后期段职业武器补位（equip_add_fist_archer.py）固定词条 =====
    # 拳套三档：特效主题对齐（连击/反击/破甲），蓝装档位
    '岩拳·裂脊': ['combo', 'crit_up'],        # 岩拳之怒：每 3 次攻击后下一次攻击 +30%
    '铁脊拳套': ['counter', 'tenacity'],       # 铁脊反击：受击 15% 反击 50% 伤害
    '碎岳拳': ['armor_break', 'charge'],       # 碎岳之势：攻击 25% 破甲 15%（2 刻）
    # 游侠蓝弓：元素/迅捷主题
    '霜羽长弓': ['element_ice', 'precise'],    # 霜羽之矢：攻击附加 5% 冰伤 + 减速
    '疾风猎弓': ['swift', 'hunt'],             # 疾风追猎：命中叠自身速度

    # ===== v169 职业断档补档固定词条（12 件，2026-09-03） =====
    # P0 牧师 92 权杖（圣光/治疗）
    '圣谕权杖': ['purify', 'meditate'],
    # P0 拳师 90/96 拳套（冲锋/破甲）
    '碎星拳套': ['charge', 'armor_break'],
    '暗星拳甲': ['charge', 'crit_up'],
    # P0 游侠 75 弓（精准/贯穿）
    '疾风挽歌': ['precise', 'pierce'],
    # P0 智系 91+ 大贤者系（冥想/魔抗/回春）
    '大贤者法冠': ['meditate', 'magic_ward'],
    '大贤者圣衣': ['magic_ward', 'regen'],
    '大贤者护腿': ['meditate', 'dodge'],
    # P1 刺客 65 匕首（暴击/连击）
    '影袭之刃': ['crit_up', 'combo'],
    # P1 新手蓝武器（冥想/净化，牧师新手法器）
    '晨光法杖': ['meditate'],
    '曙光权杖': ['purify', 'meditate'],
    # P1 敏系 91+ 防具（闪避/迅捷）
    '逐风皮甲': ['dodge', 'swift'],
    '云端护腿': ['swift', 'dodge'],

    # ===== v172 路B：重锻专属装备固定词条（24 件，2026-09-03）=====
    # source=重锻 装备（仅『装备重锻』可得）；词条对齐同系锻造职业套风格——
    # 武器随源套（战士处决/破甲、法师雷/法穿、牧师净化/圣愈、游侠精准/追猎、刺客暴击/连击、武僧蓄力/反击），
    # 防具随源套族（重甲 dmg_reduce/block/tenacity、布甲 magic_ward/meditate、皮甲 swift/dodge、武袍 block/tenacity）。
    # ---- 重锻武器 Lv.31 紫 ----
    '壁垒战剑': ['execute', 'armor_break'],
    '铭文法典之杖': ['element_thunder', 'pene_magi'],
    '贤者法典之杖': ['purify', 'heal_power'],
    '巡猎长弓': ['precise', 'hunt'],
    '夜行短刃': ['crit_up', 'combo'],
    '镇岳拳套': ['charge', 'counter'],
    # ---- 重锻武器 Lv.52 橙 ----
    '壁垒军团战剑': ['execute', 'charge', 'armor_break'],
    '铭刻法典之杖': ['element_thunder', 'pene_magi', 'crit_up'],
    '辉光圣杖': ['purify', 'divine_radiance', 'heal_power'],
    '远征之弓': ['crit_up', 'precise', 'hunt'],
    '暗夜之刃': ['crit_up', 'combo', 'pene_phys'],
    '撼岳拳': ['charge', 'counter', 'lifesteal'],
    # ---- 重锻防具 Lv.33 紫 ----
    '壁垒肩甲': ['dmg_reduce', 'tenacity'],
    '铭文法袍': ['meditate', 'magic_ward'],
    '贤者法衣': ['heal_power', 'tenacity'],
    '巡猎皮甲': ['swift', 'dodge'],
    '幽夜皮衣': ['dodge', 'swift'],
    '磐岳武袍': ['block', 'tenacity'],
    # ---- 重锻防具 Lv.53 橙 ----
    '壁垒守御胸甲': ['dmg_reduce', 'block', 'hp_up'],
    '铭刻法袍': ['magic_ward', 'regen', 'tenacity'],
    '辉光圣衣': ['holy_echo', 'magic_ward', 'regen'],
    '远征皮甲': ['swift', 'dodge', 'crit_up'],
    '夜影皮衣': ['dodge', 'swift', 'tenacity'],
    '不动武袍': ['tenacity', 'block', 'dmg_reduce'],
}

# ================= v130.2d R2：v130.2 资源联动套装登记块（死数据）已删除 =================
# 该登记块（原 813-900 行）零消费，效果 100% 迁入 game/data/sets.py（v130.2c 全量落地），
# 本文件不再保留套装定义副本，防止双处漂移。
