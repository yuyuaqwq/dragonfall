# -*- coding: utf-8 -*-
"""v151 刺客技能表 → 引擎字段格式（独立落地文件，勿并入 game/data/skills.py）

源表：workspace/v151_skill_tables/ci_ke.md
字段映射：workspace/v151_field_mapping.md
任务卡：workspace/task_cards/skill_ci_ke.md

结构（与 game/data/skills.py 对齐）：
  PLAYER_SKILLS_ci_ke = { "cls_ci_ke": {"name": "刺客", "skills": {...}} }
  BRANCH_SKILLS_ci_ke = { "cls_ci_ke": {"name": "刺客", "branches": {1: {...}, 2: {...}}} }

分支 key：1 = A线·影舞（连段往「稳」长），2 = B线·毒刃（连段往「转」长）。
基础技能（Lv.1-26 两线共用）：刺击 / 双刃乱舞 / 潜行 / 暗杀 / 影袭 / 割裂 / 烟雾弹 / 疾影。

v151 连段机制（命中计数 lian_duan 0-10，miss/闪避归零）：
  - 引擎已挂载 lian_duan 于 MECH_STACK_MAX（cap 10）与 MECH_STACK_WHITELIST，
    但 battle.py 攻击技能命中投喂只对「攻线·影舞者」的 mech_stacks["combo"]（硬编码 key）
    生效——lian_duan 尚无 MECH_EFFECTS handler / 命中投喂消费点。
  - 本文件忠实落地 v151 数据（命中+1段 → mech "lian_duan" / mech_val），
    引擎不消费的部分见文件尾 ENGINE_UNSUPPORTED 注释清单，由主 agent 收尾接线。

字段说明：
  power = base（Lv.1 裸倍率）；满级eq ≈ base×1.40（desc 只写 Lv.1 裸倍率）。
  cond {"type": "player_mech_stacks", "mech": "lian_duan", "stacks": N, "mult": X}
       = 连段≥N 条件（battle_conds.py 已支持，读 mech_stacks[cond.mech]）。
  毒 = mech "poison" / mech_val 层数（目标级 debuffs，cap 5，已有）。
  腐蚀真伤 = mech "corros"（DOT_DEFS true_dmg 已有，但 MECH_EFFECTS 无 corros handler → 引擎不支持）。
  流血 = mech "bleed"（DOT_DEFS 已有，MECH_EFFECTS 无 bleed handler → 引擎不支持）。
  AOE = aoe "front"/"all"；破防 = pierce True；点名后排 = reach 3；减速 = mech "spd_down"。
"""

PLAYER_SKILLS_ci_ke = {
    "cls_ci_ke": {
        "name": "刺客",
        "skills": {
            # 刺击 Lv.1：命中 +1 段（连段计数）
            "sk_ci_ke_ci_ji": {
                "lv": 1, "mp": 3, "power": 0.8, "kind": "物理",
                "mech": "lian_duan", "mech_val": 1,
                "desc": "匕尖自袖中无声递出，直取要害——造成 80% 物理伤害并叠加 1 段连段（命中计数，未命中则连段归零）",
                "name": "刺击",
            },
            # 双刃乱舞 Lv.14：双段 +2 段
            "sk_ci_ke_shuang_ren_luan_wu": {
                "lv": 14, "mp": 8, "power": 0.7, "kind": "物理",
                "multi": 2,
                "mech": "lian_duan", "mech_val": 2,
                "desc": "双匕翻飞如蝶，连斩两记——每次造成 70% 物理伤害（共 2 次），命中叠加 2 段连段",
                "name": "双刃乱舞",
            },
            # 潜行 Lv.20：必暴，不涨段（增益）
            "sk_ci_ke_qian_xing": {
                "lv": 20, "mp": 0, "power": 0, "kind": "增益",
                "effect": "stealth", "cd": 3,
                "desc": "身形没入暗影，气息与杀意一同敛去——下次攻击必定暴击（不叠加连段）",
                "name": "潜行",
            },
            # 暗杀 Lv.24：满血必暴（增益/攻击）
            "sk_ci_ke_an_sha": {
                "lv": 24, "mp": 15, "power": 1.8, "kind": "物理",
                "cd": 3,
                "cond": {"type": "enemy_full_hp", "mult": 1.0, "label": "满血必暴"},
                "desc": "自阴影中现身的必杀一击——造成 180% 物理伤害；目标满血时必定暴击",
                "name": "暗杀",
            },
            # 影袭 Lv.10：+1 段
            "sk_ci_ke_ying_xi": {
                "lv": 10, "mp": 8, "power": 1.1, "kind": "物理",
                "mech": "lian_duan", "mech_val": 1,
                "desc": "顺着影子扑向猎物，匕刃与黑暗一同落下——造成 110% 物理伤害并叠加 1 段连段",
                "name": "影袭",
            },
            # 割裂 Lv.6：流血（补 DOT）——引擎 DOT_DEFS.bleed 已有，但 MECH_EFFECTS 无 bleed handler
            "sk_ci_ke_ge_lie": {
                "lv": 6, "mp": 5, "power": 0.9, "kind": "物理",
                "mech": "bleed", "mech_val": 2,
                "desc": "利刃划过血肉，留下一道深可见骨的伤口——造成 90% 物理伤害并附加 2 层流血",
                "name": "割裂",
            },
            # 烟雾弹 Lv.18：脱战+闪避（补生存）
            "sk_ci_ke_yan_wu_dan": {
                "lv": 18, "mp": 10, "power": 0, "kind": "增益",
                "effect": "dodge_up", "cd": 4,
                "desc": "掷出烟雾弹，身形隐入迷障脱战——闪避率大幅提升，持续 3 回合（生存）",
                "name": "烟雾弹",
            },
            # 疾影 Lv.22：速度+40%（补机动）
            "sk_ci_ke_ji_ying": {
                "lv": 22, "mp": 0, "power": 0, "kind": "增益",
                "effect": "spd_up", "cd": 3,
                "desc": "足尖点地，身影拖出残像掠向目标——速度＋40%，持续 3 回合（机动）",
                "name": "疾影",
            },
        },
    },
}

BRANCH_SKILLS_ci_ke = {
    "cls_ci_ke": {
        "name": "刺客",
        "branches": {
            # ============ A 线 · 影舞（连段往「稳」长：防断、越连越稳、滚雪球） ============
            1: {
                "影舞": {
                    # 影刃 Lv.32：+1 段，连段≥5 追加段
                    "sk_ci_ke_ying_ren": {
                        "lv": 32, "mp": 8, "power": 0.9, "kind": "物理",
                        "mech": "lian_duan", "mech_val": 1,
                        "cond": {"type": "player_mech_stacks", "mech": "lian_duan", "stacks": 5, "mult": 1.0, "label": "连段追加"},
                        "desc": "匕刃自影中探出，割向猎物——造成 90% 物理伤害并叠加 1 段连段；连段≥5 时追加 1 段攻击",
                        "name": "影刃",
                    },
                    # 幻影连刺 Lv.45：三段 +3 段
                    "sk_ci_ke_huan_ying_lian_ci": {
                        "lv": 45, "mp": 12, "power": 0.6, "kind": "物理",
                        "multi": 3, "cd": 2,
                        "mech": "lian_duan", "mech_val": 3,
                        "desc": "身影化作三道残像，匕尖如毒蛇连番噬咬——造成 60% 物理伤害×3，命中叠加 3 段连段",
                        "name": "幻影连刺",
                    },
                    # 链舞 Lv.52：每段终结增伤+8%（被动——引擎 passive proc combo_finisher_per_layer 无消费点）
                    "sk_ci_ke_lian_wu": {
                        "lv": 52, "mp": 0, "power": 0, "kind": "被动",
                        "passive": {"proc": "combo_finisher_per_layer", "mult": 0.08},
                        "desc": "链舞翩跹，越连越狠——连段每层终结技增伤 8%（被动，只放大连段终结一轴）",
                        "name": "链舞",
                    },
                    # 终结·处刑 Lv.55：吃连段（每段+10%）
                    "sk_ci_ke_zhong_jie_chu_xing": {
                        "lv": 55, "mp": 0, "power": 2.0, "kind": "物理",
                        "cd": 3,
                        "cond": {"type": "player_mech_stacks", "mech": "lian_duan", "stacks": 1, "mult": 1.0, "label": "连段终结"},
                        "mech_gain": {"lian_duan": 0},
                        "desc": "暗影中跃出的终焉之刃——造成 200% 物理伤害；连段每层使终结伤害＋10%（连段越高越致命）",
                        "name": "终结·处刑",
                    },
                    # 暗影步 Lv.50：满10段进影舞态：CD-1+受击不清段（增益）
                    "sk_ci_ke_an_ying_bu": {
                        "lv": 50, "mp": 0, "power": 0, "kind": "增益",
                        "effect": "shadow_realm", "cd": 3,
                        "cond": {"type": "player_mech_stacks", "mech": "lian_duan", "stacks": 10, "mult": 1.0, "label": "满段影舞"},
                        "desc": "连段满 10 段时踏入影舞态——冷却-1、受击不清空连段（影舞态，3 回合）",
                        "name": "暗影步",
                    },
                    # 影分身 Lv.46：闪避+30%（补生存）
                    "sk_ci_ke_ying_fen_shen": {
                        "lv": 46, "mp": 0, "power": 0, "kind": "增益",
                        "effect": "dodge_up", "cd": 4,
                        "desc": "幻化出多重残像分身惑敌——闪避率＋30%，持续 3 回合（生存）",
                        "name": "影分身",
                    },
                    # 暗影之心 Lv.60：断连只掉一半段（而非归零）——引擎无「半段保留」字段
                    "sk_ci_ke_an_ying_zhi_xin": {
                        "lv": 60, "mp": 0, "power": 0, "kind": "被动",
                        "passive": {"stat": "spd", "mult": 0.05},
                        "desc": "暗影之力在心脏中搏动，影舞更加从容——断连时只掉一半连段（而非归零）（被动；速度＋5% 落地）",
                        "name": "暗影之心",
                    },
                    # 暗影突袭 Lv.66：潜行×1.3
                    "sk_ci_ke_an_ying_tu_xi": {
                        "lv": 66, "mp": 12, "power": 1.4, "kind": "物理",
                        "cd": 2,
                        "mech": "lian_duan", "mech_val": 1,
                        "cond": {"type": "player_buffed", "mult": 1.3, "label": "潜行突袭"},
                        "desc": "自暗影中突进，刃光与身形同时闪现——造成 140% 物理伤害；潜行状态下伤害×1.3，命中叠加 1 段连段",
                        "name": "暗影突袭",
                    },
                    # 收割 Lv.70：残血×1.4
                    "sk_ci_ke_shou_ge": {
                        "lv": 70, "mp": 15, "power": 1.6, "kind": "物理",
                        "cd": 3,
                        "cond": {"type": "enemy_hp_low", "hp_pct": 0.5, "mult": 1.4, "label": "残血收割"},
                        "desc": "镰刃般的匕锋划过战场，收割垂死者的生命——造成 160% 物理伤害；目标生命低于 50% 时伤害×1.4",
                        "name": "收割",
                    },
                    # 幽影连刺 Lv.74：四段 +4 段
                    "sk_ci_ke_you_ying_lian_ci": {
                        "lv": 74, "mp": 15, "power": 0.5, "kind": "物理",
                        "multi": 4, "cd": 2,
                        "mech": "lian_duan", "mech_val": 4,
                        "desc": "幽影化作四道残像接连刺出——每次造成 50% 物理伤害（共 4 次），命中叠加 4 段连段",
                        "name": "幽影连刺",
                    },
                    # 影遁 Lv.78：强制潜行+免控（补生存）
                    "sk_ci_ke_ying_dun": {
                        "lv": 78, "mp": 0, "power": 0, "kind": "增益",
                        "effect": "stealth", "cd": 5,
                        "cc": "cleanse",
                        "desc": "化作暗影遁入虚空——强制进入潜行并清除自身控制（免控，生存）",
                        "name": "影遁",
                    },
                    # 暗影步·极 Lv.84：影舞态内速度+20%（被动）
                    "sk_ci_ke_an_ying_bu_ji": {
                        "lv": 84, "mp": 0, "power": 0, "kind": "被动",
                        "passive": {"stat": "spd", "mult": 0.20},
                        "desc": "影舞步法臻至化境——影舞态内速度＋20%（被动）",
                        "name": "暗影步·极",
                    },
                    # 影之国度 Lv.92：影舞态强化
                    "sk_ci_ke_ying_zhi_guo_du": {
                        "lv": 92, "mp": 0, "power": 0, "kind": "增益",
                        "effect": "shadow_realm", "cd": 5,
                        "desc": "撕裂现实踏入影之国度，万物皆在暗影掌控之中——影舞态强化：速度＋40%、暴击提升，持续 3 回合（三转奥义）",
                        "name": "影之国度",
                    },
                    # 幻影舞 Lv.95：四段+影舞态×1.25
                    "sk_ci_ke_huan_ying_wu": {
                        "lv": 95, "mp": 20, "power": 0.6, "kind": "物理",
                        "multi": 4, "cd": 4,
                        "mech": "lian_duan", "mech_val": 4,
                        "cond": {"type": "player_buffed", "mult": 1.25, "label": "影舞态强化"},
                        "desc": "身影在敌阵中翩然起舞，匕光织成夺命之网——造成 60% 物理伤害×4，命中叠加 4 段连段；影舞态内伤害×1.25",
                        "name": "幻影舞",
                    },
                    # 终结·暗影绞杀 Lv.98：满段+影舞态
                    "sk_ci_ke_zhong_jie_an_ying_jiao_sha": {
                        "lv": 98, "mp": 0, "power": 2.8, "kind": "物理",
                        "cd": 5,
                        "cond": {"type": "player_mech_stacks", "mech": "lian_duan", "stacks": 10, "mult": 1.0, "label": "满段绞杀"},
                        "mech_gain": {"lian_duan": 0},
                        "desc": "暗影化作绞索缠上咽喉，终结一切反抗——造成 280% 物理伤害；连段每层使终结伤害＋10%（满段+影舞态下威力倾泻）",
                        "name": "终结·暗影绞杀",
                    },
                },
            },
            # ============ B 线 · 毒刃（连段往「转」长：连段转毒层，持续毒爆） ============
            2: {
                "毒刃": {
                    # 淬毒 Lv.8：毒1层（本线专属基础）
                    "sk_ci_ke_cui_du": {
                        "lv": 8, "mp": 5, "power": 0.8, "kind": "物理",
                        "mech": "poison", "mech_val": 1,
                        "mech_gain": {"lian_duan": 0},
                        "desc": "匕尖在幽绿毒液中浸过，再吻上猎物的咽喉——造成 80% 物理伤害并附加 1 层中毒",
                        "name": "淬毒",
                    },
                    # 毒雾 Lv.16：AOE 毒1层（魔法）
                    "sk_ci_ke_du_wu": {
                        "lv": 16, "mp": 10, "power": 0.6, "kind": "魔法",
                        "mech": "poison", "mech_val": 1,
                        "aoe": "all",
                        "desc": "掷出毒囊炸开一片幽绿雾气，腐蚀全场敌人的血肉——造成 60% 全体魔法伤害并附加 1 层中毒",
                        "name": "毒雾",
                    },
                    # 死亡标记 Lv.20：目标易伤
                    "sk_ci_ke_si_wang_biao_ji": {
                        "lv": 20, "mp": 0, "power": 0, "kind": "增益",
                        "effect": "mark", "cd": 3,
                        "desc": "在猎物眉心烙下死亡的印记，令其成为众矢之的——目标受击伤害＋30%",
                        "name": "死亡标记",
                    },
                    # 毒刃 Lv.32：毒2层，连段转毒
                    "sk_ci_ke_du_ren": {
                        "lv": 32, "mp": 8, "power": 0.9, "kind": "物理",
                        "mech": "poison", "mech_val": 2,
                        "mech_gain": {"lian_duan": 0},
                        "desc": "刃锋淬满剧毒，划开血肉的同时种下毒种——造成 90% 物理伤害并叠加 2 层中毒（连段转毒层）",
                        "name": "毒刃",
                    },
                    # 双毒刃 Lv.45：毒3层
                    "sk_ci_ke_shuang_du_ren": {
                        "lv": 45, "mp": 12, "power": 0.8, "kind": "物理",
                        "multi": 2,
                        "mech": "poison", "mech_val": 3,
                        "desc": "双刃各淬异毒，交错斩出双重毒蚀——造成 80% 物理伤害×2并叠加 3 层中毒",
                        "name": "双毒刃",
                    },
                    # 蚀骨 Lv.52：毒爆+20%（被动——引擎 passive proc poison_burst_amp 无消费点）
                    "sk_ci_ke_shi_gu": {
                        "lv": 52, "mp": 0, "power": 0, "kind": "被动",
                        "passive": {"proc": "poison_burst_amp", "mult": 0.2},
                        "desc": "蚀骨蚀心，毒爆更烈——毒层引爆伤害＋20%（被动，只放大毒层引爆一轴）",
                        "name": "蚀骨",
                    },
                    # 毒爆 Lv.55：毒层引爆
                    "sk_ci_ke_du_bao": {
                        "lv": 55, "mp": 0, "power": 1.5, "kind": "物理",
                        "cd": 2,
                        "mech": "poison_burst", "mech_val": 1,
                        "cond": {"type": "enemy_poison_stacks", "stacks": 3, "mult": 1.0, "label": "毒层引爆"},
                        "desc": "将猎物体内积攒的剧毒尽数引燃，令其由内溃烂——造成 150% 物理伤害并引爆全部毒层（毒层≥3 可引爆）",
                        "name": "毒爆",
                    },
                    # 淬毒之刃 Lv.48：毒2层+连段转毒
                    "sk_ci_ke_cui_du_zhi_ren": {
                        "lv": 48, "mp": 8, "power": 0.9, "kind": "物理",
                        "mech": "poison", "mech_val": 2,
                        "mech_gain": {"lian_duan": 0},
                        "desc": "导师亲授的淬毒杀法，匕刃划过时毒液渗入伤口——造成 90% 物理伤害并叠加 2 层中毒（连段转毒层）",
                        "name": "淬毒之刃",
                    },
                    # 淬毒之心 Lv.60：毒层≥5 停投喂（伺服）——引擎无「毒层≥N 停投喂」字段
                    "sk_ci_ke_cui_du_zhi_xin": {
                        "lv": 60, "mp": 0, "power": 0, "kind": "被动",
                        "passive": {"proc": "poison_dmg", "mult": 0.10},
                        "desc": "毒液在血脉中日夜淬炼，毒性愈发猛烈——毒层伤害＋10%（被动，毒强化）",
                        "name": "淬毒之心",
                    },
                    # 毒雾·淬 Lv.66：AOE+腐蚀真伤（魔法）
                    "sk_ci_ke_du_wu_cui": {
                        "lv": 66, "mp": 15, "power": 0.7, "kind": "魔法",
                        "cd": 3,
                        "mech": "corros", "mech_val": 2,
                        "aoe": "all",
                        "desc": "掷出淬炼过的毒囊，幽绿雾气弥漫全场——造成 70% 全体魔法伤害并附加 2 层腐蚀（真伤）",
                        "name": "毒雾·淬",
                    },
                    # 淬毒刺杀 Lv.74：高防目标腐蚀反超
                    "sk_ci_ke_cui_du_ci_sha": {
                        "lv": 74, "mp": 15, "power": 1.6, "kind": "物理",
                        "cd": 3,
                        "mech": "corros", "mech_val": 3,
                        "pierce": True,
                        "desc": "匕刃在毒液中淬至极致，一击种下深重毒患——造成 160% 物理伤害（破防）并附加 3 层腐蚀；高防目标受腐蚀反超",
                        "name": "淬毒刺杀",
                    },
                    # 剧毒之触 Lv.70：毒层附带减速（被动）
                    "sk_ci_ke_ju_du_zhi_chu": {
                        "lv": 70, "mp": 0, "power": 0, "kind": "被动",
                        "passive": {"proc": "poison_dmg", "mult": 0.05},
                        "desc": "剧毒之触如影随形——毒层命中时附带减速（被动）",
                        "name": "剧毒之触",
                    },
                    # 腐蚀之刃 Lv.80：腐蚀真伤单体（魔法）
                    "sk_ci_ke_fu_shi_zhi_ren": {
                        "lv": 80, "mp": 18, "power": 1.5, "kind": "魔法",
                        "cd": 3,
                        "mech": "corros", "mech_val": 3,
                        "desc": "凝聚腐蚀之力为刃，噬咬高防之敌——造成 150% 魔法伤害并附加 3 层腐蚀（真伤，无视防御）",
                        "name": "腐蚀之刃",
                    },
                    # 毒雾·障 Lv.84：自身毒雾闪避（补生存）
                    "sk_ci_ke_du_wu_zhang": {
                        "lv": 84, "mp": 0, "power": 0, "kind": "增益",
                        "effect": "dodge_up", "cd": 5,
                        "desc": "周身毒雾弥漫成障，毒雾护体——闪避率大幅提升（生存）",
                        "name": "毒雾·障",
                    },
                    # 万毒归宗 Lv.92：全毒层增伤（被动）
                    "sk_ci_ke_wan_du_gui_zong": {
                        "lv": 92, "mp": 0, "power": 0, "kind": "被动",
                        "passive": {"proc": "poison_dmg", "mult": 0.20},
                        "desc": "万毒归一，全场敌人体内毒素同时崩解迸发——毒层增伤＋20%（被动，三转奥义）",
                        "name": "万毒归宗",
                    },
                    # 剧毒风暴 Lv.95：AOE+满毒清算（魔法）
                    "sk_ci_ke_ju_du_feng_bao": {
                        "lv": 95, "mp": 30, "power": 0.9, "kind": "魔法",
                        "cd": 4,
                        "mech": "poison", "mech_val": 4,
                        "aoe": "all",
                        "desc": "掀起剧毒风暴席卷全场，腐蚀每一寸血肉——造成 90% 全体魔法伤害并叠加 4 层中毒；目标满毒（5 层）时毒层清算",
                        "name": "剧毒风暴",
                    },
                    # 万毒噬心 Lv.98：腐蚀真伤顶点（魔法）
                    "sk_ci_ke_wan_du_shi_xin": {
                        "lv": 98, "mp": 40, "power": 2.5, "kind": "魔法",
                        "cd": 5,
                        "mech": "corros", "mech_val": 5,
                        "desc": "万种剧毒凝于匕尖，噬心蚀骨——造成 250% 魔法伤害并叠加 5 层腐蚀（真伤顶点，终极毒杀）",
                        "name": "万毒噬心",
                    },
                },
            },
        },
    },
}

# ============================================================
# v151 机制字段 → 引擎支持情况（主 agent 收尾接线清单）
# ============================================================
# [引擎不支持 / 待接线]
# 1. 连段命中投喂：攻击技能 mech="lian_duan" 无 MECH_EFFECTS handler；battle.py 命中投喂
#    只对攻线·影舞者（path=1）的 mech_stacks["combo"] 硬编码生效。基础/毒刃线 +1段 需引擎接线。
# 2. 终结技每段+10%（终结·处刑 / 终结·暗影绞杀）：引擎 combo_finisher_per_layer 仅套装
#    _set_eff 消费，被动 proc（链舞）与「连段×10%/层」无消费点。
# 3. 暗影之心「断连只掉一半段」：引擎 _combo_break 仅支持保留概率/归零，无「减半」。
# 4. 影舞态「CD-1+受击不清段」（暗影步）：引擎 shadow_realm 只加 spd+crit，CD-1 为暮影
#    dual_form 专属（core_resources.py），普通 增益 effect 不触发。
# 5. 毒层投喂停止（淬毒之心「毒层≥5 停投喂」/ mech_gain {"lian_duan": 0} 占位）：引擎无
#    poison_cap_stop / 投喂停止字段（v139 旧数据字段未接线）。
# 6. 腐蚀真伤 mech="corros"：DOT_DEFS 已定义（true_dmg 真伤轴），但 MECH_EFFECTS 无 corros
#    handler（玩家侧技能无法叠腐蚀层）。
# 7. 流血 mech="bleed"：DOT_DEFS 已定义，MECH_EFFECTS 无 bleed handler（玩家侧技能无法叠）。
# 8. 毒雾·障 / 烟雾弹 的「脱战」：引擎无脱战状态，dodge_up 近似落地。
# [引擎已支持（本文件直接可用）]
# - mech poison / poison_burst / spd_down / mark / stealth / shadow_realm / dodge_up / spd_up
# - cond player_mech_stacks（mech=lian_duan 读 mech_stacks）/ enemy_full_hp / enemy_hp_low /
#   enemy_poison_stacks / player_buffed
# - passive stat spd / proc poison_dmg / proc dodge_up
# - aoe all / pierce / multi / cd / lv / mp / power / kind / effect / team

ENGINE_UNSUPPORTED = [
    "lian_duan 命中投喂（攻击技能 +1段）",
    "终结技每段+10%（combo_finisher_per_layer 被动 proc）",
    "暗影之心 断连减半",
    "影舞态 CD-1+受击不清段（effect shadow_realm 不含 CD-1）",
    "毒层≥5 停投喂（poison_cap_stop）",
    "corros 腐蚀真伤叠层（MECH_EFFECTS 无 handler）",
    "bleed 流血叠层（MECH_EFFECTS 无 handler）",
    "脱战状态（烟雾弹/毒雾·障）",
]
