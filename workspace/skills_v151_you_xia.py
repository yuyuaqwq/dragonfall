# -*- coding: utf-8 -*-
"""
v151 游侠技能表 → 引擎字段格式（独立落地文件，主 agent 收尾统一合并进 skills.py）

翻译依据：
  - v151 设计原文：workspace/v151_skill_tables/you_xia.md（预算「精力」+ 挂账「标记」）
  - 字段映射：workspace/v151_field_mapping.md
  - 引擎现状（侦察，见 workspace/v151_engine_gap_report.md）：
      * mech_stacks 已有（战意 zhan_yi / 连段 lian_duan 已注册上限与白名单）
      * 敌身挂账：enemy.debuffs mark/poison/burn（cap 5）+ e_buffs["mark"] 计时
      * cond：enemy_marked / enemy_poison_stacks / speed_ratio / player_buffed 等现成
      * 召唤：summon 模板 vine_guard / treant 现成（限 2 / 1）
      * 电荷制：charge_cfg 现成（蓄力狙击沿用，v139 云海弓手三律）
      * 屏息窗口（breathe_*）/ vent_seg_bonus：引擎字段已定义但 battle.py 尚无消费点（差距项）
  - 本文件两 dict 名：PLAYER_SKILLS_you_xia（基础）+ BRANCH_SKILLS_you_xia（分支）
  - key 命名：sk_you_xia_<拼音>，全库无碰撞（已 grep 确认）
"""

# ============================================================
# 一、基础技能（Lv.1-26，两线共用 · 8 个）
# v151 表：疾风连射 / 瞄准射击 / 鹰眼锁定 / 风之疾走 / 猎网陷阱 /
#          致命狙击 / 闪避步 / 林语印记
# 翻译口径（对齐现有 skills.py 游侠段）：
#   - 精力预算档保留 res_cost={"energy": N}（引擎现有精力管线，vent 排气挂 core_resources）
#   - 标记 = mech "mark" + mech_val（enemy.debuffs mark 叠层，cap 5；e_buffs["mark"] 计时）
#   - 双段 = multi；AOE = aoe "all"；破防 = pierce；点名 = reach 3
#   - 增益 = effect 现成键（crit_up/spd_up/dodge_up/atk_up）
# ============================================================
PLAYER_SKILLS_you_xia = {
    "sk_you_xia_ji_feng_lian_she": {
        # 疾风连射（连射档 · 双段）
        "lv": 1, "mp": 5, "power": 0.6, "kind": "物理",
        "multi": 2,
        "res_cost": {"energy": 20},
        # 屏息窗口联动（引擎字段：低耗档 ≤25 段数 +1；消费点 battle.py 未接——差距项）
        "breathe_seg_bonus": 1,
        "desc": "弓弦颤动如风吟，两箭连珠破空而出——连续射击 2 次，每次造成 60% 物理伤害（连射档·低耗预算 20 精力）；凝神屏息窗口内段数＋1(3 段)",
        "name": "疾风连射",
    },
    "sk_you_xia_miao_zhun": {
        # 瞄准射击（连射档 · 单体）
        "lv": 6, "mp": 8, "power": 1.3, "kind": "物理",
        "res_cost": {"energy": 10},
        "desc": "凝神屏息，将呼吸与弓弦调成同频——蓄势一箭造成 130% 物理伤害（连射档·低耗预算 10 精力）",
        "name": "瞄准射击",
    },
    "sk_you_xia_ying_yan": {
        # 鹰眼锁定（增益 · 暴击+命中）
        "lv": 12, "mp": 0, "power": 0, "kind": "增益",
        "effect": "crit_up", "cd": 3,
        "res_cost": {"energy": 15},
        "desc": "瞳中映出鹰隼的金芒，猎物的一切破绽无所遁形——暴击率＋20%，持续 3 回合（鹰眼锁定·增益）",
        "name": "鹰眼锁定",
    },
    "sk_you_xia_feng_ji_zou": {
        # 风之疾走（增益 · 提速+位移泄压）
        "lv": 14, "mp": 0, "power": 0, "kind": "增益",
        "effect": "spd_up", "cd": 2,
        "res_cost": {"energy": 20},
        # 机动泄压（v139 引擎字段：位移从成本变收益，施放当回合精力 -15）
        "vent_energy": 15,
        "desc": "风元素缠绕足踝，身形化作林间掠影——速度＋40%，持续 3 回合（机动）；施放当回合精力-15(机动泄压)",
        "name": "风之疾走",
    },
    "sk_you_xia_lie_wang": {
        # 猎网陷阱（物理 · 减速陷阱）
        "lv": 18, "mp": 10, "power": 0.9, "kind": "物理",
        "mech": "spd_down", "mech_val": 1, "cd": 3,
        "res_cost": {"energy": 30},
        "desc": "在林间暗处布下猎网，猎物踏入便被缠住——造成 90% 物理伤害并使目标减速（猎网陷阱·补控制）",
        "name": "猎网陷阱",
    },
    "sk_you_xia_zhi_ming": {
        # 致命狙击（物理 · 对异常目标 ×1.3）
        "lv": 22, "mp": 18, "power": 2.0, "kind": "物理",
        "cd": 3,
        "res_cost": {"energy": 35},
        "cond": {"type": "enemy_debuff", "mult": 1.3, "label": "绝境之眼"},
        "desc": "鹰瞳锁定猎物最后一口气，箭矢循着死亡轨迹射出——造成 200% 物理伤害；目标身带异常时，绝境之眼睁开（伤害＋30%）",
        "name": "致命狙击",
    },
    "sk_you_xia_shan_bi": {
        # 闪避步（增益 · 闪避+30%）
        "lv": 24, "mp": 0, "power": 0, "kind": "增益",
        "effect": "dodge_up", "cd": 4,
        "res_cost": {"energy": 30},
        "desc": "身随风向斜踏一步，身形如烟——闪避率＋30%，持续 3 回合（闪避步·补生存）",
        "name": "闪避步",
    },
    "sk_you_xia_lin_yu_yin_ji": {
        # 林语印记（物理 · 挂标记 1 层，挂账核心）
        "lv": 20, "mp": 0, "power": 0.6, "kind": "物理",
        "mech": "mark", "mech_val": 1,
        "res_cost": {"energy": 20},
        "res_gain": {"energy": 10},
        # 屏息窗口联动：窗口内标记 1 层 → 2 层（引擎字段已定义，消费点 battle.py 未接——差距项）
        "breathe_mark_extra": 1,
        "desc": "吟诵林间古语，箭矢裹挟自然之力烙印猎物——造成 60% 物理伤害并施加 1 层猎杀标记（挂账，全队对标记目标增伤，叠满 +30%）；命中汲取 10 精力；凝神屏息窗口内标记叠 2 层",
        "name": "林语印记",
    },
}

# ============================================================
# 二、分支技能（BRANCH_SKILLS_you_xia）
# 结构按现有 skills.py 游侠段：1 = A线（攻线·林语者/自然行者/万木之灵），
#                             2 = B线（守线·风行者/疾风射手/疾风猎手）
# 分支 key 沿用现有中文线名（evolve_branches 强耦合，禁改）
# ============================================================
BRANCH_SKILLS_you_xia = {
    "cls_you_xia": {
        "name": "游侠",
        "branches": {
            # ============ A 线 · 林语（标记叠层 + 毒爆 + 召唤，团队集火） ============
            1: {
                "林语者": {
                    # 追猎（标记目标 ×1.3）
                    "追猎": {
                        "lv": 32, "mp": 10, "power": 1.2, "kind": "物理",
                        "cond": {"type": "enemy_marked", "mult": 1.3, "label": "猎杀本能"},
                        "res_cost": {"energy": 20},
                        "desc": "循着猎杀标记的气味穷追不舍，箭矢咬住猎物的背影——造成 120% 物理伤害；目标被标记时，猎杀本能苏醒（伤害＋30%）",
                        "name": "追猎",
                    },
                    # 淬毒箭矢（毒 2 层）
                    "淬毒箭矢": {
                        "lv": 40, "mp": 8, "power": 0.9, "kind": "物理",
                        "mech": "poison", "mech_val": 2,
                        "res_cost": {"energy": 20},
                        "desc": "箭簇浸过幽绿毒液，破空时带起一缕腥风——造成 90% 物理伤害并附加 2 层中毒（淬毒箭矢）",
                        "name": "淬毒箭矢",
                    },
                    # 藤蔓缠绕（毒 2 层 + 缠绕减速）
                    "藤蔓缠绕": {
                        "lv": 45, "mp": 12, "power": 1.0, "kind": "物理",
                        "mech": "poison", "mech_val": 2,
                        "cd": 2,
                        "res_cost": {"energy": 25},
                        "desc": "召唤林间藤蔓破土而出，缠上猎物的足踝并注入麻痹毒汁——造成 100% 物理伤害并叠加 2 层中毒（藤蔓缠绕·减速缠绕）",
                        "name": "藤蔓缠绕",
                    },
                    # 召唤藤蔓守卫（召唤挡刀）
                    "召唤藤蔓守卫": {
                        "lv": 52, "mp": 20, "power": 0, "kind": "增益",
                        "summon": "vine_guard", "cd": 4,
                        "res_cost": {"energy": 30},
                        "desc": "以林语唤醒沉睡的藤蔓，化为守卫并肩而战——召唤藤蔓守卫加入战斗（可叠加 2 只，自动攻击并挡刀）",
                        "name": "召唤藤蔓守卫",
                    },
                    # 毒爆术（3 层毒引爆，每层 +15%）
                    "毒爆术": {
                        "lv": 55, "mp": 15, "power": 1.5, "kind": "物理",
                        "mech": "poison_burst", "mech_val": 1,
                        "cd": 2,
                        "res_cost": {"energy": 35},
                        "cond": {"type": "enemy_poison_stacks", "stacks": 3, "mult": 1.15, "label": "毒素迸发"},
                        "desc": "以自然之力引燃猎物体内的毒素，令其由内而外迸发——造成 150% 物理伤害；目标毒层达到 3 层时引爆，每层追加 15% 伤害（毒爆术）",
                        "name": "毒爆术",
                    },
                },
                # ============ B 线 · 疾风（速度差 + 电荷蓄力 + 点名后排） ============
                "风行者": {
                    # 疾风射击（速度比 ≥1.5 ×1.3）
                    "疾风射击": {
                        "lv": 32, "mp": 8, "power": 1.0, "kind": "物理",
                        "cond": {"type": "speed_ratio", "ratio": 1.5, "mult": 1.3, "label": "疾风连击"},
                        "res_cost": {"energy": 20},
                        "desc": "借风势射出疾驰一箭，箭速快过猎物反应——造成 100% 物理伤害；速度比达到 1.5 倍以上时，疾风连击呼啸（伤害＋30%）",
                        "name": "疾风射击",
                    },
                    # 双重射击（双段）
                    "双重射击": {
                        "lv": 40, "mp": 12, "power": 0.8, "kind": "物理",
                        "multi": 2,
                        "res_cost": {"energy": 25},
                        "breathe_seg_bonus": 1,
                        "desc": "弓弦一颤两箭齐出，如双燕掠空——造成 80% 物理伤害×2（双重射击·双段）；凝神屏息窗口内段数＋1(3 段)",
                        "name": "双重射击",
                    },
                    # 风刃乱舞（三段 AOE）
                    "风刃乱舞": {
                        "lv": 50, "mp": 15, "power": 0.7, "kind": "物理",
                        "multi": 3, "aoe": "all", "cd": 2,
                        "res_cost": {"energy": 30},
                        "desc": "弓弦化作风刃席卷全场，割裂一切甲胄——造成 70% 物理伤害×3 的全体攻击（风刃乱舞·三段）",
                        "name": "风刃乱舞",
                    },
                    # 蓄力狙击（电荷 1/2/3 阶 + 点名后排）
                    "蓄力狙击": {
                        "lv": 55, "mp": 20, "power": 1.9, "kind": "物理",
                        "reach": 3, "pierce": True, "cd": 3,
                        "res_cost": {"energy": 40},
                        # 电荷制蓄力（v139 云海弓手三律翻译，battle_bars 现成）
                        "charge_cfg": {
                            "max": 3,
                            "charge_cost": 10,
                            "m_base": 0.7,
                            "m_step": 0.6,
                            "snipe_m_base": 0.7,
                            "interrupt_loss": 1,
                            "full_force": True,
                            "snipe_min": 1,
                            "snipe_reach": 3,
                        },
                        "desc": "电荷制蓄力狙击——「蓄力」动作(耗 10 精力)电荷+1 并立即出伤 0.7/1.3/1.9；受击电荷-1不清零；电荷=3 强制释放狙击（满阶 280% 破防、reach3 点名后排）",
                        "name": "蓄力狙击",
                    },
                    # 星轨锁定（锁敌 3 回合 ×1.2，无视站位——星语→疾风拆解）
                    "星轨锁定": {
                        "lv": 50, "mp": 15, "power": 0, "kind": "增益",
                        "effect": "star_lock", "cd": 4,
                        "res_cost": {"energy": 20},
                        "star_lock": {"min_marks": 2, "duration": 3, "cd": 4, "mark_extra": 1, "crit_mark_extra": 1},
                        "desc": "以星光锁定命定之敌——锁定指定目标(无视站位直击，3 回合，对锁定目标伤害×1.2)；门槛猎印≥2 才可施放(CD 4)",
                        "name": "星轨锁定",
                    },
                },
            },
            # ============ A 线 T2 · 自然行者（标记强化 + 毒系 + 团队） ============
            2: {
                "自然行者": {
                    # 自然之眼（被动 · 标记目标全队 +15%）
                    "自然之眼": {
                        "lv": 60, "mp": 0, "power": 0, "kind": "被动",
                        "passive": {"proc": "mark_dmg", "mult": 0.15},
                        "desc": "万物在自然之眼中皆有破绽——对标记目标的伤害＋15%（二转被动，标记强化）",
                        "name": "自然之眼",
                    },
                    # 追猎者（被动 · 标记叠层上限 +1）
                    "追猎者": {
                        "lv": 64, "mp": 0, "power": 0, "kind": "被动",
                        "passive": {"proc": "mark_extra", "chance": 0.15},
                        "desc": "箭矢与猎物之间仿佛牵起无形的线，越缠越紧——攻击时 15% 概率额外叠加 1 层标记（追猎者，被动）",
                        "name": "追猎者",
                    },
                    # 猎杀狂宴（标记 ×1.3 + 全队暴击）
                    "猎杀狂宴": {
                        "lv": 66, "mp": 20, "power": 1.3, "kind": "物理",
                        "cd": 3,
                        "cond": {"type": "enemy_marked", "mult": 1.3, "label": "狂宴"},
                        "team": "crit_all",
                        "res_cost": {"energy": 30},
                        "desc": "吹响猎杀盛宴的号角，全队的杀意一同高涨——造成 130% 物理伤害；目标被标记时伤害＋30%，并全队暴击强化 3 回合（猎杀狂宴）",
                        "name": "猎杀狂宴",
                    },
                    # 剧毒之心（被动 · 毒层 + 毒爆增伤）
                    "剧毒之心": {
                        "lv": 72, "mp": 0, "power": 0, "kind": "被动",
                        "passive": {"proc": "poison_dmg", "mult": 0.2},
                        "desc": "毒与自然在血脉中交融，毒液化作第二颗心脏——毒系技能伤害＋20%（剧毒之心，被动）",
                        "name": "剧毒之心",
                    },
                    # 穿心箭（标记满 ×1.3）
                    "穿心箭": {
                        "lv": 74, "mp": 18, "power": 1.8, "kind": "物理",
                        "pierce": True, "cd": 3,
                        "cond": {"type": "enemy_marked", "mult": 1.3, "label": "要害瞄准"},
                        "res_cost": {"energy": 35},
                        "desc": "箭矢穿透层层甲胄，直指心脏——造成 180% 破防物理伤害；目标被标记时，要害暴露无遗（伤害＋30%）",
                        "name": "穿心箭",
                    },
                    # 自然护佑（增益 · 全队闪避 +15%）
                    "自然护佑": {
                        "lv": 82, "mp": 0, "power": 0, "kind": "增益",
                        "effect": "dodge_up", "team": "dodge_all", "cd": 5,
                        "res_cost": {"energy": 40},
                        "desc": "林风环绕周身，为全队拂开袭来的利刃——全队闪避率＋15%，持续 3 回合（自然护佑·补生存）",
                        "name": "自然护佑",
                    },
                },
                # ============ B 线 T2 · 疾风射手（速度强化 + 点名） ============
                "疾风射手": {
                    # 疾风之心（被动 · 满弦暴击 +10%）
                    "疾风之心": {
                        "lv": 60, "mp": 0, "power": 0, "kind": "被动",
                        "passive": {"stat": "spd_crit", "mult": 0.1},
                        "desc": "疾风在血脉中奔流不息——每 10 点速度转化为 1% 暴击率（满弦暴击，被动）",
                        "name": "疾风之心",
                    },
                    # 急速射击（屏息段数 +1）
                    "急速射击": {
                        "lv": 66, "mp": 10, "power": 0.7, "kind": "物理",
                        "multi": 3, "cd": 2,
                        "res_cost": {"energy": 30},
                        "breathe_seg_bonus": 1,
                        "desc": "弓弦几乎失去踪影，箭雨连绵不绝——造成 70% 物理伤害×3；凝神屏息窗口内段数＋1(4 段)",
                        "name": "急速射击",
                    },
                    # 穿云箭（reach3 点名）
                    "穿云箭": {
                        "lv": 74, "mp": 20, "power": 2.0, "kind": "物理",
                        "pierce": True, "reach": 3, "cd": 3,
                        "res_cost": {"energy": 30},
                        "desc": "一箭穿云破雾，裹着风压直贯敌阵——造成 200% 破防物理伤害，点名后排（reach3）",
                        "name": "穿云箭",
                    },
                    # 风之屏障（增益 · 闪避 +40%）
                    "风之屏障": {
                        "lv": 70, "mp": 0, "power": 0, "kind": "增益",
                        "effect": "dodge_up", "cd": 5,
                        "res_cost": {"energy": 35},
                        "desc": "风织成无形的屏障护住周身——闪避率＋40%，持续 3 回合（风之屏障·补生存）",
                        "name": "风之屏障",
                    },
                    # 疾风步（增益 · 速度 +40%）
                    "疾风步": {
                        "lv": 80, "mp": 0, "power": 0, "kind": "增益",
                        "effect": "spd_up", "cd": 3,
                        "res_cost": {"energy": 25},
                        "desc": "踏风而行，步履轻如鸿羽——速度＋40%，持续 3 回合（疾风步·补机动）",
                        "name": "疾风步",
                    },
                    # 穿甲射击（破防 + 点名）
                    "穿甲射击": {
                        "lv": 84, "mp": 18, "power": 1.6, "kind": "物理",
                        "pierce": True, "reach": 3, "cd": 3,
                        "res_cost": {"energy": 35},
                        "desc": "箭簇打磨得足以撕裂重甲与龙鳞——造成 160% 破防物理伤害，点名后排（穿甲射击·补破防）",
                        "name": "穿甲射击",
                    },
                },
            },
            # ============ A 线 T3 · 万木之灵（终极连射 + 古树 + 毒清算） ============
            3: {
                "万木之灵": {
                    # 猎杀时刻（全队对标记增伤 +30%）
                    "猎杀时刻": {
                        "lv": 92, "mp": 0, "power": 0, "kind": "增益",
                        "effect": "crit_all", "team": "crit_all", "cd": 5,
                        "res_cost": {"energy": 40},
                        "cond": {"type": "enemy_marked", "mult": 1.3, "label": "猎杀时刻"},
                        "desc": "万物寂灭，唯余猎杀——全队对标记目标增伤＋30% 持续 3 回合（猎杀时刻·集火号令）",
                        "name": "猎杀时刻",
                    },
                    # 致命连射（四段）
                    "致命连射": {
                        "lv": 95, "mp": 25, "power": 0.7, "kind": "物理",
                        "multi": 4, "cd": 3,
                        "res_cost": {"energy": 35},
                        "breathe_seg_bonus": 1,
                        "desc": "四箭连珠，箭箭皆奔要害而去——造成 70% 物理伤害×4（致命连射·四段）；凝神屏息窗口内段数＋1(5 段)",
                        "name": "致命连射",
                    },
                    # 召唤古树守卫（古树 + 全队攻击 +30%）
                    "召唤古树守卫": {
                        "lv": 96, "mp": 40, "power": 0, "kind": "增益",
                        "summon": "treant", "effect": "atk_up", "team": "atk_all", "cd": 6,
                        "res_cost": {"energy": 40},
                        "desc": "唤醒沉睡千年的古树化作重装守卫，以庞大身躯为伙伴挡下刀锋——召唤古树守卫并令全队攻击＋30%，持续 3 回合",
                        "name": "召唤古树守卫",
                    },
                    # 死神之箭（标记满 + 毒层清算）
                    "死神之箭": {
                        "lv": 98, "mp": 40, "power": 2.8, "kind": "物理",
                        "pierce": True, "reach": 3, "cd": 5,
                        "res_cost": {"energy": 40},
                        "cond": {"type": "enemy_marked", "mult": 1.4, "label": "死神注视"},
                        "desc": "死神借弓弦睁开眼，一箭定生死——造成 280% 破防物理伤害；目标被标记时，死神注视之下伤害＋40%（死神之箭·毒层清算）",
                        "name": "死神之箭",
                    },
                },
                # ============ B 线 T3 · 疾风猎手（四段 + 满弦暴击 + 全队速度） ============
                "疾风猎手": {
                    # 风神降临（全队速度 +30%）
                    "风神降临": {
                        "lv": 92, "mp": 0, "power": 0, "kind": "增益",
                        "effect": "spd_up", "team": "spd_all", "cd": 6,
                        "res_cost": {"energy": 40},
                        "vent_energy": 15,
                        "desc": "风神之息灌入四肢百骸，全队身形快如流光——全队速度＋30%，持续 3 回合（风神降临·极速爆发）；施放当回合精力-15(机动泄压)",
                        "name": "风神降临",
                    },
                    # 风暴之舞（四段）
                    "风暴之舞": {
                        "lv": 95, "mp": 20, "power": 0.7, "kind": "物理",
                        "multi": 4, "cd": 4,
                        "res_cost": {"energy": 40},
                        "breathe_seg_bonus": 1,
                        "desc": "身随风暴起舞，箭矢如雨点般倾泻——造成 70% 物理伤害×4（风暴之舞·四段）；凝神屏息窗口内段数＋1(5 段)",
                        "name": "风暴之舞",
                    },
                    # 疾风骤雨（四段 + 满弦暴击）
                    "疾风骤雨": {
                        "lv": 98, "mp": 30, "power": 1.0, "kind": "物理",
                        "multi": 4, "cd": 5,
                        "res_cost": {"energy": 40},
                        "cond": {"type": "player_mech_stacks", "mech": "zhan_yi", "stacks": 1, "mult": 1.0, "label": "满弦暴击"},
                        "desc": "疾风化作骤雨，箭矢铺天盖地落下——造成 100% 物理伤害×4（疾风骤雨·终极连射，满弦暴击联动）",
                        "name": "疾风骤雨",
                    },
                },
            },
        },
    },
}
