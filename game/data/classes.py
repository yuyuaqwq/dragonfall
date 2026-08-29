# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - classes.py(v48 key 转 ID)

v112 职业体系重构（主题线制）：13 隐藏 → 6 隐藏线（每基础 1 条），
每线 = 主题 + 核心资源（core_resources.py）+ 线级被动 + 2-3 流派（evolve_branches[1]）。
v112 新增数据字段（数据驱动收敛，逻辑层只读数据）：
  aliases      转职短别名 → 流派索引（『转职 龙血』→ cls_dragon_oath 流派 1）
  lore         传承文案
  hint         未解锁线索
  tier_levels  隐藏线档位门槛（缺省 40/60/90）
  attack_text  普攻动作文案（battle.py 读取）
  tutor        (导师名, 地点)（转职指引/技能学习拦截提示）

v139 职业融合（云海猎团职业卡吸收，13 份方案 design/new_world/参考_云海猎团职业融合_v139_*.md）：
  mech 描述更新为「奥兰迪亚身份 + v139 融合机制」一句话（职业指南/战斗展示用）；
  新增职业级机制字段（说明性引用，值与 core_resources.py / battle_config.py 同名字段同构，
  由 battle.py 通用引擎机消费——dual_form 双形态 / focus 架设态 / vent 排气节流阀 /
  charge 电荷蓄力 / enemy_bar 挂敌身条 / combo 链值 / support 随附支援 / dirge 死歌 等）：
    cls_zhan_shi      dual_form（攻线狂战士狂暴）
    cls_fa_shi        focus（元素架设）
    cls_you_xia       vent + charge（凝神屏息 + 电荷蓄力）
    cls_mu_shi        support（守线圣辉支援）
    cls_ci_ke         finisher_threshold + combo（终结档位 + 链值滚雪球）
    cls_wu_seng       enemy_bar.shaken + guard_core（破绽挂敌身 + 磐核）
    cls_dragon_oath   dual_form（龙焰形态）
    cls_chronomancer  focus（时间凝滞）
    cls_wild_hunter   vent + star_lock（猎印排气 + 星轨锁定）
    cls_hymn          enemy_bar.curse/soul_mark + dirge（诅咒挂敌身 + 死歌）
    cls_shadow_blade  dual_form（影舞态）+ ambush_plan（伏击四预案）
    cls_wu_sheng      dual_form（蓄势/倾泻）+ enemy_bar.shaken（撼岳之势）
  原则：只加数据不改结构（desc/evolve 分支不动），旧字段无该键 = 默认不启用（引擎兼容旧数据）。
"""
CLASSES = {
    "cls_novice": {
        "desc": "刚踏上冒险之路的新人，还没有正式职业。去冒险者行会找接待员就职，或到各城寻找职业导师吧！",
        "icon": "🧭",
        "role": "见习",
        "attack_text": "挥剑攻击",
        "base": {
            "hp": 110,
            "mp": 50,
            "atk": 11,
            "def": 9,
            "matk": 9,
            "mdef": 9,
            "spd": 10,
            "crit": 0.05,
            "dodge": 0.03
        },
        "growth": {
            "hp": 14,
            "mp": 6,
            "atk": 1.3,
            "def": 1.1,
            "matk": 1.1,
            "mdef": 1.1,
            "spd": 1.0
        },
        "weapon_type": "sword",
        "name": "见习冒险者",
        "default_rank": 1,   # v2 站位层：前排
        "reach": 1,          # v2 攻击范围
        "rank_label": "前排",
    },
    "cls_zhan_shi": {
        "desc": "身穿重甲、手持巨剑的钢铁壁垒，正面硬刚一切敌人。",
        # v139（云海猎团职业融合·狂战士样板）：攻线狂战士「血怒双形态」——满怒入狂暴、
        # 双段输出+维持消耗+<4 强制回斧（怒尽回斧无惩罚）；守线盾卫士「防御即生产」——
        # 守护姿态受击自动反击 + 保底回怒 + 坚韧抗控。转职全链覆盖（基础 1-30 → 攻/守双线）。
        "mech": "怒气三路攒满10放背水一战；v139攻线入狂暴双形态，守线防御即生产。",  # v130.7 意见#19 / v139 融合
        "icon": "🛡️",
        "role": "坦克",
        "evolve": ["狂战士(30)", "狂战统领(60)", "战争领主(90)"],
        "evolve_branches": {
            # v139：攻线=狂战士（血怒双形态，狂暴精通/破势斩）；守线=盾卫士（防御即生产，守护姿态反击+坚韧）
            1: ["狂战士", "盾卫士"],
            2: ["狂战统领", "坚盾卫士"],
            3: ["战争领主", "坚城统帅"],
        },
        # v139（云海狂战士双形态翻译，样板定稿）：攻线狂战士狂暴形态——字段与
        # core_resources.py cls_zhan_shi.dual_form 同构（enter_requirement 10 / maintain_cost 1 /
        # hit_cost 1 / hit_cost_cap 1 / force_return 4 / form "fury"），由 battle.py 通用形态机消费；
        # 战前可设入狂暴 4 档预设（满怒/7怒/窗口/血线），守线 side 另有 tenacity 坚韧副资源
        "dual_form": {
            "enter_requirement": 10, "maintain_cost": 1, "hit_cost": 1,
            "hit_cost_cap": 1, "force_return": 4, "return_penalty": "none", "form": "fury",
        },
        "attack_text": "挥剑斩击",
        "tutor": ("老兵·格里姆", "白鹿城·白鹿广场"),
        "base": {
            "hp": 150,
            "mp": 40,
            "atk": 18,
            "def": 14,
            "matk": 6,
            "mdef": 10,
            "spd": 10,
            "crit": 0.05,
            "dodge": 0.03,
            "elem_res": 0.05,
            "shield_power": 0.05,
        },
        "growth": {
            "hp": 22,
            "mp": 3,
            "atk": 3.2,
            "def": 2.6,
            "matk": 0.5,
            "mdef": 1.2,
            "spd": 0.6
        },
        "weapon_type": "sword",
        "name": "战士",
        "default_rank": 1,   # v2 站位层：前排（坦克壁垒）
        "reach": 1,          # v2 攻击范围：近战
        "rank_label": "前排",
    },
    "cls_fa_shi": {
        "desc": "掌控元素之力的施法者，输出爆炸但身板脆弱。",
        # v139（云海机械师融合）：转职后攻线·元素/守线·奥秘可开「元素架设」专注施法模式——
        # +40% 施法增伤、受击 +20%、不能普攻/换系、打断不清零（只掉 1 层）、主动解除无损。
        # 基础法师（未转职）纯蓝不经营不变（v130.2 身份铁律）。
        "mech": "纯蓝施法者；转职解锁充能条 + v139元素架设(专注+40%增伤)。",  # v130.7 意见#19 / v139 融合
        "icon": "🔥",
        "role": "输出",
        # v130.2（鱼鱼拍板）：基础法师无核心资源 = 纯蓝施法者——技能全纯 mp，
        # 0 res_gain / 0 res_cost / 模型无 on_skill 渠道；element 充能条(0-5) 定义保留在
        # core_resources.py，随攻线·元素法师 / 守线·奥秘法师 转职首获（转职批次挂 res_gain 生效）。
        # v112.5（鱼鱼拍板）：基础法师两条初始线——元素（攻）+ 奥秘（守）；
        # 奥秘守线 = 奥术师与秘法族合并体（原隐藏奥秘线元素流降为基础守线）
        # v139：攻线=元素架设爆发（聚焦→满充能→湮灭）、守线=深度冥想驻留（低耗高频+叠层加速）
        "evolve": ["元素法师(30)", "元素术士(60)", "元素贤者(90)"],
        "evolve_branches": {
            1: ["元素法师", "奥秘法师"],
            2: ["元素术士", "奥秘术士"],
            3: ["元素贤者", "奥秘贤者"],
        },
        # v139（云海机械师架设态翻译）：元素架设 focus——字段与 core_resources.py cls_fa_shi.focus
        # 同构（enter_turn 1 / dmg_bonus 0.40 / taken_bonus 0.20 / interrupt 只掉 1 层 /
        # max_turns 3 / free_exit），由 battle.py 通用专注机消费；攻线开启技「元素聚焦」、
        # 守线开启技「深度冥想」（架设中每回合 arcane 自动 +1）
        "focus": {
            "enter_turn": 1, "dmg_bonus": 0.40, "taken_bonus": 0.20,
            "interrupt_charge_loss": 1, "max_turns": 3, "free_exit": True,
            "blocked": ["attack", "skill", "swap"],
        },
        "attack_text": "凝聚魔力轰出法球",
        "tutor": ("大法师·艾德琳", "白鹿城·白鹿广场"),
        "base": {
            "hp": 90,
            "mp": 120,
            "atk": 8,
            "def": 7,
            "matk": 22,
            "mdef": 14,
            "spd": 12,
            "crit": 0.08,
            "dodge": 0.05,
            "pene_magi": 0.10,
            "abyss_res": 0.05,
        },
        "growth": {
            "hp": 10,
            "mp": 10,
            "atk": 0.8,
            "def": 1.0,
            "matk": 3.8,
            "mdef": 1.8,
            "spd": 0.8
        },
        "weapon_type": "staff",
        "name": "法师",
        "default_rank": 2,   # v2 站位层：后排（施法者）
        "reach": 2,          # v2 攻击范围：远程
        "rank_label": "后排",
    },
    "cls_you_xia": {
        # v113（鱼鱼拍板）：攻线"猎魔人"主题名实不符（无猎魔内容），
        # 改为自然系"林语者"——狩猎印记保留 + 自然毒藤 + 植物召唤（机制下放自隐藏线自然/兽群流）
        # v139（云海游侠+弓手融合）：精力满 100 强制「凝神屏息」（节流阀）+ 电荷制蓄力三律
        # （边攒边打/打断-1阶不清零/满阶强制释放）+ 狙击指定后排（rank=3 瞄准权）。
        "desc": "敏捷的弓箭手，箭无虚发，暴击与闪避的艺术家。攻线觉醒自然之力，与万木为友。",
        # v130.7 意见#19 / v139 融合：精力三档预算身份保留，v139 满 100 强制屏息排气 + 电荷蓄力
        "mech": "每回合回30精力；v139满100凝神屏息，蓄力改电荷制(边攒边打)。",
        "icon": "🏹",
        "role": "输出",
        "evolve": ["林语者(30)", "自然行者(60)", "万木之灵(90)"],
        "evolve_branches": {
            # v139：攻线=林语者（标记叠层+毒 DOT+屏息爆发窗口）；守线=风行者（速度增伤+电荷蓄力狙击）
            1: ["林语者", "风行者"],
            2: ["自然行者", "疾风射手"],
            3: ["万木之灵", "疾风猎手"],
        },
        # v139（云海游侠节流阀翻译）：精力排气——VENT_CFG（battle_config.py）触发=100 强制屏息、
        # 闪避/机动泄压 -15、排气后低耗档段数 +1；字段说明性引用（核心数据在 battle_config.py VENT_CFG）
        "vent": {
            "trigger": 100, "auto": True, "reset": 0,
            "seg_bonus": 1, "low_cost_max": 25,
            "vent_on_dodge": 15, "vent_on_mobile": 15,
        },
        # v139（云海弓手蓄力三律翻译）：电荷制蓄力——RANGER_CHARGE_CFG（battle_config.py）
        # max 3 / 边攒边打出伤 0.7/1.3/1.9 / 打断-1阶 / 满 3 强制释放 / 狙击 reach=3
        "charge": {
            "max": 3, "gain_per_turn": 1, "dmg_per_stage": [0.7, 1.3, 1.9],
            "interrupt_penalty": 1, "force_release": True, "release_power": 2.8,
            "release_extra": {"pierce": True, "reach": 3},
        },
        "attack_text": "弯弓搭箭",
        "tutor": ("猎手·柯恩", "铁港城·港口广场"),
        "base": {
            "hp": 110,
            "mp": 60,
            "atk": 15,
            "def": 10,
            "matk": 8,
            "mdef": 9,
            "spd": 16,
            "crit": 0.15,
            "dodge": 0.12,
        },
        "growth": {
            "hp": 14,
            "mp": 5,
            "atk": 2.6,
            "def": 1.6,
            "matk": 0.8,
            "mdef": 1.0,
            "spd": 1.8
        },
        "weapon_type": "bow",
        "name": "游侠",
        "default_rank": 2,   # v2 站位层：后排（射手）
        "reach": 2,          # v2 攻击范围：远程
        "rank_label": "后排",
    },
    "cls_mu_shi": {
        "desc": "信仰圣光的神职者，能打能奶，队伍的灵魂。",
        # v139（云海吟游诗人+圣骑士融合）：攻线歌者=全队 100%/自身 55% 双行放大器
        # （共鸣短燃料+回声长驻留，谱曲节奏 mace/staff 分化）；守线神谕=治疗即支援的圣辉引擎
        # （治疗攒圣律 vow → 随附支援不占主行动，每回合至多 1 件）。
        "mech": "治疗攒信仰值满10放神迹；v139攻线歌者双资源，守线圣律随附支援。",  # v130.7 意见#19 / v139 融合
        "icon": "✨",
        "role": "治疗",
        # v112.3（鱼鱼拍板）：攻线"圣武士/审判骑士/裁决骑士"整体换为诗人路线——
        # 吟游诗人→灵魂歌者→黎明颂者（歌声递进：鼓舞→治愈→终极颂歌），
        # 独立隐藏职业"吟游诗人"删除并回归牧师攻线（回到 6 隐藏线结构）
        # v130.2（鱼鱼拍板）：攻线歌者转职后=双核心资源「共鸣 resonance(max10) + 回声 echo(max3)」——
        # 基础牧师仍单信仰值 faith；共鸣/回声定义已注册 core_resources.py（按资源 key 作注册键），
        # 需引擎批次 2 在 evolve_branches 攻线侧提供 分支级 resource_override 使 battle.py 能识别
        # 双资源；echo 建议落 mech_stacks 驻留叠层（战斗内不清零），回合起始全队恢复+增益续时另需引擎挂点。
        # v139：攻线歌者补双行算式+破晓长歌（EQ≈4.8）；守线神谕圣辉支援（圣律 vow 0-3，随附不占行动）
        "evolve": ["吟游诗人(30)", "灵魂歌者(60)", "黎明颂者(90)"],
        "evolve_branches": {
            1: ["吟游诗人", "神谕者"],
            2: ["灵魂歌者", "大主教"],
            3: ["黎明颂者", "圣光先知"],
        },
        # v139（云海圣骑士随附支援翻译）：守线圣辉支援——圣律 vow 0-3（core_resources.py 注册），
        # 治疗命中/受击攒圣律（每回合至多 1），消耗 1 圣律施放 1 件支援（不占主行动、主行动后结算）；
        # 攻线歌者共鸣/回声双资源见 core_resources.py 表尾段
        "support": {
            "res_key": "vow", "max": 3, "per_turn_cap": 1,
            "type": "post_action",  # 主行动结算后触发（随附）
        },
        "attack_text": "圣光冲击",
        "tutor": ("圣殿执事·莉亚", "白鹿城·白鹿广场"),
        "base": {
            "hp": 100,
            "mp": 110,
            "atk": 10,
            "def": 11,
            "matk": 16,
            "mdef": 16,
            "spd": 11,
            "crit": 0.06,
            "dodge": 0.06,
            "elem_res": 0.05,
            "heal_power": 0.10,
        },
        "growth": {
            "hp": 12,
            "mp": 9,
            "atk": 1.2,
            "def": 1.8,
            "matk": 2.6,
            "mdef": 2.4,
            "spd": 0.7
        },
        "weapon_type": "mace",
        "name": "牧师",
        "default_rank": 2,   # v2 站位层：后排（远程治疗+输出）
        "reach": 2,          # v2 攻击范围：远程
        "rank_label": "后排",
    },
    "cls_ci_ke": {
        "desc": "暗影中的利刃，出手必见血，暴击与闪避的极致。",
        # v139（云海盗贼+剑客融合）：段数三线投喂（攻线=连击点+连段链值 / 守线=毒层+破防），
        # 攻线链值滚雪球（影追追加段/终结+40%/暴击注入）+ 旋锋锁死（爆发覆盖率 60%）；
        # 全职业唯一判断消耗点=终结技，战前可设终结阈值档位（快刀/满刃/残血/满段）。
        "mech": "命中攒连击点满5爆发；v139多段投喂链值/毒层，终结阈值可配。",  # v130.7 意见#19 / v139 融合
        "icon": "🗡️",
        "role": "输出",
        "evolve": ["影舞者(30)", "暗影之刃(60)", "无影之刃(90)"],
        "evolve_branches": {
            # v139：攻线=影舞者（链值滚雪球+段数三线投喂）；守线=毒刃者（毒层伺服/引爆，主动放弃直破防）
            1: ["影舞者", "毒刃者"],
            2: ["暗影之刃", "淬毒师"],
            3: ["无影之刃", "蚀骨者"],
        },
        # v139（云海剑客战前阈值 DSL 翻译）：终结阈值档位——player.event_state["finisher_threshold"]
        # 战斗内只读；档位A 快刀(cp≥3) / B 满刃(cp=5) / C 残血(HP<40%+cp≥3) / D 满段(攻线链值≥8)
        "finisher_threshold": {
            "data_field": "player.event_state.finisher_threshold",
            "default": "满刃", "options": ["快刀", "满刃", "残血", "满段"],
        },
        # v139（云海盗贼段数三线投喂翻译）：攻线连段链值 combo——COMBO_CFG（battle_config.py）
        # cap 10 / 追加段 ≥5 / 终结每层 +5% / 暴击注入 ≥8 / 旋锋锁死 ≥8；只喂攻线（守线=毒层轴）
        "combo": {
            "cap": 10, "chase_at": 5, "chase_power": 0.5,
            "finish_min": 3, "per_layer": 0.05, "max_bonus": 0.40,
            "inject_at": 8, "spin_lock": 8,
        },
        "attack_text": "匕首突刺",
        "tutor": ("暗影渡鸦", "铁港城·港口广场"),
        "base": {
            "hp": 95,
            "mp": 70,
            "atk": 17,
            "def": 9,
            "matk": 7,
            "mdef": 8,
            "spd": 19,
            "crit": 0.2,
            "dodge": 0.18,
            "pene_phys": 0.10,
            "cdr": 0.05,
        },
        "growth": {
            "hp": 12,
            "mp": 5,
            "atk": 3.0,
            "def": 1.3,
            "matk": 0.6,
            "mdef": 0.9,
            "spd": 2.2
        },
        "weapon_type": "dagger",
        "name": "刺客",
        "default_rank": 1,   # v122f 站位层：前排（匕首近战，鱼鱼拍板：刺客哪有那么长手）
        "reach": 1,          # v122f 攻击范围：近战（原 2 错误，匕首近战系）
        "rank_label": "前排",
    },
    "cls_wu_seng": {
        "desc": "以拳入道的修行者，拳拳到肉，连击与反击的行家。",
        # v139（云海斗士×守卫融合）：攻线格斗士=「破绽积蓄」挂敌身（shaken，不吃异常免疫，
        # 打晕与破防共用一次命中，免疫巨兽唯一软解）；守线磐石行者=「磐核」承伤即收益
        # （挨打攒核/未挨打保底+1，攒满放线性倍率磐岩释能）。两线共用气+三连骨架。
        "mech": "出招攒气3/10气双档；v139攻线推敌破绽条，守线防御攒磐核。",  # v130.7 意见#19 / v139 融合
        "icon": "🥊",
        "role": "辅助",
        # v112 P0-3（鱼鱼拍板）：拳斗士→格斗士、武斗师→拳术师（与隐藏线"武僧"词族拉开）
        # v139：攻线=格斗士（shaken 挂敌身+三连打晕破防）；守线=磐石行者（磐核+守御姿态保底）
        "evolve": ["格斗士(30)", "拳术师(60)", "破晓者(90)"],
        "evolve_branches": {
            1: ["格斗士", "磐石行者"],
            2: ["拳术师", "铁壁行者"],
            3: ["破晓者", "磐岩壁垒"],
        },
        # v139（云海斗士晕眩积蓄挂敌身翻译）：破绽 shaken——ENEMY_BAR_CFG（battle_config.py）
        # max 50 / 每回合衰减 4 / 阈值 50×1.35 递增封顶 / 触发=敌方跳过下回合行动；
        # 只吃自身三律（阈值递增+免疫窗口+触发不续攒），不吃异常免疫/反弹
        "enemy_bar": {
            "shaken": {
                "max": 50, "decay_per_turn": 4,
                "threshold_base": 50, "threshold_inc": 1.35, "threshold_cap": 2.5,
                "auto_trigger": True, "immune_turns": 1, "trigger_effect": "skip_turn",
            },
        },
        # v139（云海守卫充能核翻译）：守线磐核 guard_core 0-5——GUARD_CORE_CFG（battle_config.py）
        # 守御姿态受击+1 / 未受击保底+1 / 技能命中+1；磐岩释能 M=1.0+0.7×核（线性刻意，早放高频 vs 攒满峰值）
        "guard_core": {
            "max": 5, "on_defend_hit": 1, "on_defend_idle": 1,
            "discharge_base": 1.0, "discharge_per_core": 0.7,
        },
        "attack_text": "挥拳轰击",
        "tutor": ("船帮武师·老陈", "铁港城·港口广场"),
        "base": {
            "hp": 135,
            "mp": 55,
            "atk": 15,
            "def": 12,
            "matk": 6,
            "mdef": 11,
            "spd": 14,
            "crit": 0.1,
            "dodge": 0.12,
        },
        "growth": {
            "hp": 18,
            "mp": 4,
            "atk": 2.8,
            "def": 2.0,
            "matk": 0.5,
            "mdef": 1.6,
            "spd": 1.4
        },
        "weapon_type": "fist",
        "name": "拳师",
        "default_rank": 1,   # v2 站位层：前排（近战格斗）
        "reach": 1,          # v2 攻击范围：近战
        "rank_label": "前排",
    },
    # ================= v112 隐藏线（主题线制，6 条 = 6 基础各 1 条） =================
    # 设计文档：design/new_world/09_职业体系.md
    # 流派 = evolve_branches[1]（觉醒选流派），T2/T3 = 各流派沿原职业名深化；
    # 解锁统一：Lv.40+ 专属任务链（每线 1 条）；档位门槛统一 40/60/90；血缘限制不变（src_base）
    "cls_dragon_oath": {
        # v113（鱼鱼拍板）：隐藏线收敛——只留「龙血」流派（真伤+灼烧），舍弃魔剑士/圣殿骑士缝合流
        # v139（云海狂战士×守卫融合）：龙血/龙焰双形态（自排爆发）+ 蓄能律保底（未受击也攒力）
        # + 内燃（免疫怪灼烧转真伤轴）+ 龙威咆哮嘲讽（修复坦克定位）。
        "desc": "继承古龙之血，以龙息与龙鳞屹立战场。隐藏职业，需完成龙骨之血任务链解锁(40 级)。",
        # v130.7 意见#19 / v139 融合：龙力每层 +10% 增伤保留；v139 龙血/龙焰双形态 + 蓄能律
        "mech": "行动/挨打/回合末攒龙力每层+10%；v139龙力≥8入龙焰真伤态。",  # v130.7 意见#19 / v139 融合
        "icon": "🐉",
        "role": "坦克",
        "evolve": ["龙血战士(40)", "龙裔斗士(60)", "龙魂战将(90)"],
        "evolve_branches": {
            1: ["龙血战士"],
            2: ["龙裔斗士"],
            3: ["龙魂战将"],
        },
        "aliases": {"龙血": 1, "龙裔": 1, "龙裔誓约": 1},  # F4 P1-1：职业名入别名表，交付提示『转职 龙裔誓约』不再死路
        # v139（云海狂战士双形态翻译）：龙焰形态——字段与 core_resources.py cls_dragon_oath.dual_form
        # 同构（enter_requirement 8 / maintain_cost 1 / hit_cost 1 / hit_cost_cap 1 /
        # force_return 4 / form "dragon_flame"），由 battle.py 通用形态机消费；战前可设入焰 4 档
        # （满力 10/储备 8/窗口 8+倒地/血线 8+HP<40%）；龙脉终曲仅龙焰形态可放（EQ 6.4 不动）
        "dual_form": {
            "enter_requirement": 8, "maintain_cost": 1, "hit_cost": 1,
            "hit_cost_cap": 1, "force_return": 4, "return_penalty": "none",
            "form": "dragon_flame", "flame_dmg_bonus": 0.20,
        },
        "lore": "狂战士血脉中的龙血悄然觉醒，龙息与龙鳞自此与身相随……",
        "hint": "🐉 线索：暮岭古道埋着屠龙者的铁与龙的血，寻访龙裔老兵·铁鳞。",
        "tier_levels": {1: 40, 2: 60, 3: 90},
        "attack_text": "龙威斩击",
        "tutor": ("龙裔老兵·铁鳞", "暮岭古道"),
        "base": {
            "hp": 150, "mp": 50, "atk": 18, "def": 14, "matk": 8, "mdef": 11,
            "spd": 10, "crit": 0.06, "dodge": 0.04,
            "elem_res": 0.10, "shield_power": 0.05, "cdr": 0.05,
        },
        "growth": {
            "hp": 23, "mp": 4, "atk": 3.2, "def": 2.6, "matk": 1.2,
            "mdef": 1.4, "spd": 0.7
        },
        "weapon_type": "sword",
        "name": "龙裔誓约",
        "default_rank": 1,   # v2 站位层：前排（坦克龙血近战流）
        "reach": 1,          # v2 攻击范围：近战
        "rank_label": "前排",
        "hidden": True,
        "src_base": "cls_zhan_shi",  # 渊源根基：战士
        "src_race": "dragonborn",    # v113 种族限制：龙裔血脉方可传承（鱼鱼拍板）
    },
    "cls_chronomancer": {
        # v112.5（鱼鱼拍板）：法师新增隐藏线——时咒法师
        # v113（鱼鱼拍板）：隐藏线收敛——只留「时停」流派，舍弃虚空/血咒遗产流（虚空吸蓝下放基础法师）
        # v139（云海机械师×弓手融合）：时间凝滞站桩蓄沙（架设态）+ 蓄力三律 + 时间侵蚀自动出伤
        "desc": "操控时间之流、凝固万物之刻的时咒师——时滞、凝时、时停。隐藏职业，需完成时光试炼任务链解锁(40 级)。",
        # v130.7 意见#19 / v139 融合：时之沙自动积沙保留；v139 时间凝滞站桩蓄沙（沙满强制核弹）
        "mech": "时之沙自动+1施法挨打也攒；v139时间凝滞站桩蓄沙。",  # v130.7 意见#19 / v139 融合
        "icon": "⏳",
        "role": "输出",
        "evolve": ["时咒法师(40)", "时律术士(60)", "时间领主(90)"],
        "evolve_branches": {
            1: ["时停"],
            2: ["时律术士"],
            3: ["时间领主"],
        },
        "aliases": {"时咒": 1, "时停": 1, "时间": 1, "时溯": 1, "时咒法师": 1},  # F4 P1-1：职业名入别名表
        # v139（云海机械师架设态翻译）：时间凝滞 stasis——字段与 core_resources.py
        # cls_chronomancer.stasis 同构（enter_turn 1 / enter_gain 1 / gain_per_turn 1 /
        # dmg_bonus 0.40 / taken_bonus 0.20 / interrupt_rate 0.30 / max_turns 3 /
        # erosion_power 0.60），由 battle.py 通用专注机消费；沙=5 时强制释放耗沙技（P3 满阶强制）
        "focus": {
            "enter_turn": 1, "enter_gain": 1, "gain_per_turn": 1,
            "dmg_bonus": 0.40, "taken_bonus": 0.20, "interrupt_rate": 0.30,
            "max_turns": 3, "erosion_power": 0.60,
        },
        "lore": "元素的进阶是奥秘，奥秘的尽头是时间本身——让世界为你停驻片刻……",
        "hint": "⏳ 线索：圣堂地窖的古老日晷从不在正午指向太阳，寻访时计贤者·艾瑟拉。",
        "tier_levels": {1: 40, 2: 60, 3: 90},
        "attack_text": "凝聚魔力轰出法球",
        "tutor": ("时计贤者·艾瑟拉", "白鹿城·白鹿圣堂"),
        "base": {
            "hp": 95, "mp": 125, "atk": 8, "def": 7, "matk": 24, "mdef": 15,
            "spd": 12, "crit": 0.08, "dodge": 0.05,
            "pene_magi": 0.15, "abyss_res": 0.10, "cdr": 0.05,
        },
        "growth": {
            "hp": 10, "mp": 10, "atk": 0.8, "def": 1.0, "matk": 4.1,
            "mdef": 1.8, "spd": 0.8
        },
        "weapon_type": "staff",
        "name": "时咒法师",
        "default_rank": 2,   # v2 站位层：后排（施法流）
        "reach": 2,          # v2 攻击范围：远程
        "rank_label": "后排",
        "hidden": True,
        "src_base": "cls_fa_shi",  # 渊源根基：法师
        "src_race": "human",       # v113 种族限制：人类血脉方可传承（魔法学院一脉）
    },
    "cls_wild_hunter": {
        # v113（鱼鱼拍板）：隐藏线收敛——只留「星运」流派（占星/命运），
        # 自然流（毒藤）与兽群流（召唤）机制下放基础游侠攻线；整线更名「星语者」避开"猎手"撞名
        # v139（云海游侠+弓手融合）：猎印满 5 强制「流星陨落」排气（节流阀）+ 星轨锁定指定目标
        # （点名权）+ 星光庇护保命口——「命定射手」。
        "desc": "以星为引、以运为刃的占星猎手——占卜命运，射落星辰。隐藏职业，需完成占星试炼任务链解锁(40 级)。",
        # v130.7 意见#19 / v139 融合：命中才攒猎印身份保留；v139 满 5 强制流星陨落排气 + 星轨锁定
        "mech": "命中才攒猎印暴击+1；v139满5强制排气，星轨锁定点后排。",  # v130.7 意见#19 / v139 融合
        "icon": "🔮",
        "role": "输出",
        "evolve": ["星语者(40)", "星相师(60)", "命运编织者(90)"],
        "evolve_branches": {
            1: ["星语者"],
            2: ["星相师"],
            3: ["命运编织者"],
        },
        "aliases": {"星运": 1, "占星": 1, "星语": 1},
        # v139（云海游侠节流阀翻译）：猎印排气——VENT_AT=5 满印下回合自动释放流星陨落、
        # 排气后首命中猎印+1（排气余烬）、可延迟 1 回合（深排等窗口）；星移步闪避泄压 -1 印
        "vent": {
            "trigger": 5, "auto": True, "reset": 0,
            "recovery_extra": 1, "max_delay": 1, "vent_on_dodge": 1,
        },
        # v139（云海弓手狙击权翻译）：星轨锁定——STAR_LOCK_MIN_MARKS=2 / COST=1 印 /
        # DURATION=3 回合 / CD=4；锁定目标无视站位直击，吃全系联动 ×1.2
        "star_lock": {
            "min_marks": 2, "cost": 1, "duration": 3, "cd": 4,
            "lock_mult": 1.2, "reach": 3,
        },
        "lore": "林语者之路仰望星象、聆听命运——星辰的命运，由占星者来书写……",
        "hint": "🔮 线索：星语湖的湖面映着同一片天，寻访观星台主·星澜。",
        "tier_levels": {1: 40, 2: 60, 3: 90},
        "attack_text": "弯弓搭箭",
        "tutor": ("观星台主·星澜", "星语湖"),
        "base": {
            "hp": 115, "mp": 65, "atk": 15, "def": 10, "matk": 9, "mdef": 10,
            "spd": 16, "crit": 0.15, "dodge": 0.12,
            "luck": 0.10, "summon_power": 0.10,
        },
        "growth": {
            "hp": 15, "mp": 5, "atk": 2.7, "def": 1.6, "matk": 0.9,
            "mdef": 1.0, "spd": 1.9
        },
        "weapon_type": "bow",
        "name": "星语者",
        "default_rank": 2,   # v2 站位层：后排（荒野猎手远程流）
        "reach": 2,          # v2 攻击范围：远程
        "rank_label": "后排",
        "hidden": True,
        "src_base": "cls_you_xia",  # 渊源根基：游侠
        "src_race": "elf",          # v113 种族限制：银月精灵血脉方可传承（星语湖观星台）
    },
    "cls_hymn": {
        # v112.1：圣歌流派拆出为独立诗人线（cls_bard），本线改名暗影神谕（单流派）；v112.2 诗人恢复牧师血缘
        # v139（云海吟游诗人+德鲁伊融合）：诅咒挂敌身（不可驱散）+ 死歌全队增益/自体 55% 双口径
        # + 骸骨洪流个人伤害出口——从纯生存召唤输出升级为诅咒集火放大器 + 亡灵死歌指挥。
        "desc": "行走于生死边界的亡者使徒——骷髅海铺场、死亡契约保命。隐藏职业，需完成亡者低语任务链解锁(40 级)。",
        # v130.7 意见#19 / v139 融合：悼咏四路攒 + 满溢转盾保留；v139 诅咒挂敌身 + 死歌三调
        "mech": "治疗/受击/暗蚀攒悼咏；v139诅咒挂敌身+死歌三调。",  # v130.7 意见#19 / v139 融合
        "icon": "💀",
        "role": "输出",
        "evolve": ["暗影祭司(40)", "亡魂引渡者(60)", "黯灵主教(90)"],
        "evolve_branches": {
            1: ["暗影祭司"],
            2: ["亡魂引渡者"],
            3: ["黯灵主教"],
        },
        "aliases": {"暗影": 1, "亡灵": 1, "神谕": 1, "暗影神谕": 1},  # F4 P1-1：职业名入别名表
        # v139（云海德鲁伊增益挂敌身翻译）：骨噬诅咒 curse——ENEMY_BAR_CFG（battle_config.py）
        # max 1 / 不可驱散（净化白名单不含 curse 键）/ 全队对目标伤害 +20% + 全队命中 +10%，
        # 持续 3 回合；灵魂标记 soul_mark 3 层每层 +6%（骷髅自动叠，随存活数衰减）
        "enemy_bar": {
            "curse": {
                "max": 1, "decay_per_turn": 0,
                "threshold_base": 1, "threshold_inc": 1.0, "threshold_cap": 1.0,
                "auto_trigger": True, "immune_turns": 0, "trigger_effect": "debuff",
                "team_dmg_bonus": 0.20, "team_hit_bonus": 0.10, "duration": 3,
            },
            "soul_mark": {"max": 3, "per_layer_dmg": 0.06, "decay_with_undead": True},
        },
        # v139（云海吟游诗人三谱翻译）：死歌 dirge 三调互斥（战死歌全队攻+25% / 守死歌全队减伤
        # 20%+回 5%HP / 疾死歌全队速+30%）；全队 100%/自身 55% 双行结算；余韵到期返 1 悼咏
        "dirge": {
            "war": {"team_atk": 0.25}, "guard": {"team_reduce": 0.20, "heal_pct": 0.05},
            "speed": {"team_spd": 0.30}, "self_factor": 0.55, "reprisal_gain": 1,
        },
        "lore": "神谕者之路坠入黑暗，亡者低语……骷髅海将为你而战。",
        "hint": "💀 线索：边境堡外的乱葬岗有骨头不该爬起来……能听懂亡者低语的人，才有资格执掌亡者。",
        "tier_levels": {1: 40, 2: 60, 3: 90},
        "attack_text": "凝聚幽光轰出暗影",
        "tutor": ("守墓人·枯骨", "边境堡·堡外荒野"),
        "base": {
            "hp": 115, "mp": 115, "atk": 10, "def": 12, "matk": 17, "mdef": 15,
            "spd": 10, "crit": 0.05, "dodge": 0.05,
            "abyss_res": 0.10, "phys_reduce": 0.05,
        },
        "growth": {
            "hp": 15, "mp": 8, "atk": 1.2, "def": 1.9, "matk": 2.8,
            "mdef": 2.2, "spd": 0.7
        },
        "weapon_type": "mace",
        "name": "暗影神谕",
        "default_rank": 2,   # v2 站位层：后排（暗影施法流）
        "reach": 2,          # v2 攻击范围：远程
        "rank_label": "后排",
        "hidden": True,
        "src_base": "cls_mu_shi",  # 渊源根基：牧师（神谕者线的堕落变奏）
        "src_race": "orc",         # v113 种族限制：兽人血脉方可传承（旧王陵的亡者低语）
    },
    "cls_shadow_blade": {
        # v113（鱼鱼拍板）：隐藏线收敛——只留「暗杀」流派（影步+潜行爆发），
        # 收割流派（斩杀）机制下放基础刺客攻线
        # v139（云海盗贼+剑客融合）：影舞态（满步自动进/锁死不累积/3 回合）+ 伏击四预案（战前阈值 DSL）
        "desc": "影即吾身——潜行、刺杀、一击必杀。隐藏职业，需完成暗影试炼任务链解锁(40 级)。",
        # v130.7 意见#19 / v139 融合：暴击/闪避才攒影步保留；v139 影舞态（满 5 自动进、锁死累积）
        "mech": "暴击/闪避攒影步，满5进影舞态(3回合锁死累积)，受击清空仅姿态外。",  # v130.7 意见#19 / v139 融合
        "icon": "🗡️",
        "role": "输出",
        "evolve": ["暮影行者(40)", "暮刃大师(60)", "暮影收割者(90)"],
        "evolve_branches": {
            1: ["暗杀"],
            2: ["暮刃大师"],
            3: ["暮影收割者"],
        },
        "aliases": {"暮影": 1, "影武": 1, "暗杀": 1, "暮影行者": 1},  # F4 P1-1：职业名入别名表
        # v139（云海盗贼旋锋态翻译）：影舞态 dance_form——字段与 core_resources.py
        # cls_shadow_blade.dance_form 同构（enter_requirement 5 / duration 3 / lock_accumulate True /
        # hit_clear False 姿态内 / stealth_mult_apply True），由 battle.py 通用形态机消费；
        # 满步自动进入（auto_enter True，战内零菜单），追加段不计影步/不计满步（防续杯）
        "dual_form": {
            "enter_requirement": 5, "duration": 3, "auto_enter": True,
            "lock_accumulate": True, "hit_clear": False, "stealth_mult_apply": True,
            "form": "shadow_dance",
        },
        # v139（云海剑客战前阈值 DSL 翻译）：伏击四预案——满步即入（默认）/ 等倒地窗口 /
        # 伏击蓄势（影步≥3 入潜行）/ 残血保命（HP≤40% 暗影分身）；托管按预案执行
        "ambush_plan": {
            "default": "满步即入", "options": ["满步即入", "等倒地窗口", "伏击蓄势", "残血保命"],
        },
        "lore": "影舞者之道的极致，暗影即身……",
        "hint": "🗡️ 线索：影豹从不在有月光的空地现身，寻访影刃宗师·夜枭。",
        "tier_levels": {1: 40, 2: 60, 3: 90},
        "attack_text": "匕首突刺",
        "tutor": ("影刃宗师·夜枭", "翡翠港·港口广场"),
        "base": {
            "hp": 100, "mp": 75, "atk": 19, "def": 9, "matk": 7, "mdef": 8,
            "spd": 20, "crit": 0.22, "dodge": 0.18,
            "pene_phys": 0.15, "crit_dmg": 0.20,
        },
        "growth": {
            "hp": 13, "mp": 5, "atk": 3.4, "def": 1.3, "matk": 0.6,
            "mdef": 0.9, "spd": 2.4
        },
        "weapon_type": "dagger",
        "name": "暮影行者",
        "default_rank": 1,   # v122f 站位层：前排（匕首近战，与基础刺客一致）
        "reach": 1,          # v122f 攻击范围：近战（刺客系匕首，原 2 错误）
        "rank_label": "前排",
        "hidden": True,
        "src_base": "cls_ci_ke",  # 渊源根基：刺客
        "src_race": "halfling",   # v113 种族限制：半身人血脉方可传承（行会暗影密档）
    },
    "cls_wu_sheng": {
        # v113（鱼鱼拍板）：隐藏线收敛——只留「武僧」流派（禅意+连击），
        # 大地流派（反击）机制下放基础拳师守线
        # v130.2（拍板）：档位展示名 苦修士/武僧→淬势者、大地武僧→锻势行者（T3 撼岳者不变）；
        #   evolve_branches 分支 key（武僧/大地武僧/撼岳者）与 skills.py BRANCH_SKILLS 键强耦合，
        #   属技能键引用面绝不动——旧名以 别名/路由 保留兼容，新名走 aliases 展示
        # v139（云海斗士+狂战士融合）：蓄势/倾泻双形态显式化（战前预案 4 档）+ 撼岳之势挂敌身
        "desc": "以武证道的拳师——禅意连击，拳破万法。隐藏职业，需完成淬势者试炼任务链解锁(40 级)。",
        # v130.7 意见#19 / v139 融合：禅意慢热高爆保留；v139 蓄势/倾泻双形态显式化 + 撼岳之势
        "mech": "出招/连击/挨打攒禅意每点+4%；v139双形态+撼岳条。",  # v130.7 意见#19 / v139 融合
        "icon": "🥊",
        "role": "输出",
        "evolve": ["淬势者(40)", "锻势行者(60)", "撼岳者(90)"],  # v130.2 档位展示名：T1 苦修士→淬势者、T2 大地武僧→锻势行者
        "evolve_branches": {
            # v130.2：分支 key 与 BRANCH_SKILLS 键耦合（技能授予/路由按 key 匹配），绝不动
            1: ["武僧"],
            2: ["大地武僧"],
            3: ["撼岳者"],
        },
        "aliases": {"苦修": 1, "武僧": 1, "苦修士": 1, "淬势": 1, "淬势者": 1, "锻势行者": 1},  # F4 P1-1：职业名入别名表；v130.2 新档位名入表，旧名保留兼容
        # v139（云海狂战士双形态翻译）：蓄势/倾泻双形态显式化——淬势者既有「攒→放」骨架
        # （2/3/5/10 四档倾泻，每意 +12% 威力），v139 正式命名 + 战前预案 4 档（满意即倾默认/
        # 等倒地窗口/攒到 5 档才放/残血搏命）；不新增资源，只把决策结构化
        "dual_form": {
            "form": "zen_burst", "tiers": [2, 3, 5, 10],
            "per_zen_power": 0.12, "return_penalty": "none",
            "preplan": ["满意即倾", "等倒地窗口", "攒到5档才放", "残血搏命"],
        },
        # v139（云海斗士晕眩积蓄挂敌身翻译）：撼岳之势——e.buffs["shaken"] 0-5 独立槽，
        # 连招命中即推（共用命中判定无额外 roll）、满 5 震慑 1 回合、阈值 ×1.3 递增封顶 3.0、
        # 每场触发上限 2 次；不吃异常免疫（免疫怪唯一软解）
        "enemy_bar": {
            "shaken": {
                "max": 5, "stun_turns": 1, "threshold_mult": 1.3,
                "threshold_cap": 3.0, "max_trigger": 2, "trigger_effect": "stun",
            },
        },
        "lore": "拳斗士之道的终点，以武证道……",
        "hint": "🥊 线索：拳不练千遍，打不赢一个贼——寻访铁砧要塞武僧·铁山。",
        "tier_levels": {1: 40, 2: 60, 3: 90},
        "attack_text": "挥拳轰击",
        "tutor": ("武僧·铁山", "铁砧要塞·铁砧堡闸门"),
        "base": {
            "hp": 140, "mp": 60, "atk": 16, "def": 12, "matk": 6, "mdef": 11,
            "spd": 14, "crit": 0.10, "dodge": 0.12,
        },
        "growth": {
            "hp": 19, "mp": 4, "atk": 3.0, "def": 2.1, "matk": 0.5,
            "mdef": 1.6, "spd": 1.5
        },
        "weapon_type": "fist",
        "name": "淬势者",  # v130.2（拍板）：苦修士→淬势者
        "default_rank": 1,   # v2 站位层：前排（淬势者近战流）
        "reach": 1,          # v2 攻击范围：近战
        "rank_label": "前排",
        "hidden": True,
        "src_base": "cls_wu_seng",  # 渊源根基：拳师
        "src_race": "dwarf",        # v113 种族限制：矮人血脉方可传承（铁砧要塞斗士一脉）
    }
}
