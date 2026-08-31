# -*- coding: utf-8 -*-
"""
v151 拳师技能表 → 引擎字段格式（独立翻译文件，未并入 game/data/skills.py）
================================================================================
数据源：
  - v151 技能表原文 : workspace/v151_skill_tables/quan_shi.md
  - 字段映射        : workspace/v151_field_mapping.md
  - 任务卡          : workspace/task_cards/skill_quan_shi.md

引擎字段口径（已按 game/battle.py + game/core/battle_mech.py + battle_conds.py 核实）：
  - base（Lv.1 裸倍率）→ power
  - lv / mp / cd / kind（物理/魔法/治疗/增益/被动/真伤/嘲讽）→ 同名字段
  - 推条+N（拳师破绽 = 敌身 enemy_bar "shaken"，全队共享）→ shaken_gain: N
      * 引擎在 _player_skill 每次施放注入一次（battle.py:4015 消费 info.shaken_gain）
      * 多段技能（multi>1）引擎仍按单次施放注入一次 → shaken_gain 写"单次施放总推条"
  - 破防 → pierce: True
  - 眩晕 → mech: "stun" + mech_chance（固定概率，MECH_EFFECTS stun 支持 mech_chance 覆写）
  - 防御强化 → effect: "def_up"（TEAM_BUFF_KEYS 兜底，p_buffs 记回合数）
  - 全队护盾 → effect: "shield_all" + team: "shield_all"
  - 全队减伤 → effect: "reduce_all" + reduce_all: 0.xx + team: "reduce_all"
  - 被动反击 → passive: {"proc": "counter_attack", "chance": 0.30}
  - 被动反震 → passive: {"proc": "reflect", "mult": 0.3, "chance": 0.30}
  - 被动受击减伤 → passive: {"proc": "dmg_taken", "reduce": 0.xx}
  - 破绽满（被震慑）条件 → cond: {"type": "enemy_shaken_gt", "mult": X, "label": "..."}
      * battle_conds._c_enemy_shaken_gt 判定 = 敌方 shaken 条触发过且处于免疫窗口（= 被震慑中）
      * v151 表中"破绽满×N / 破绽封顶×N"即此语义
  - 磐核（guard_core）字段为数据化挂账：res_cost/consume_all/discharge/guard_core_gain
      * 引擎无消费端（battle.py 无 guard_core 读取）→ 保留数据 + 标 engine_unsupported

引擎不支持（已列 engine_unsupported，主 agent 收尾处理）：
  1. 冥想「回蓝 + 清自身 1 减益」——引擎无 mp 恢复 / 玩家自身净化 effect
  2. 冲拳「位移至前排」——引擎无玩家站位位移机制
  3. 铁山靠「格挡 1 次」——引擎无 block_up buff effect（block 仅装备属性）
  4. 气力爆发「破绽层数增伤」——引擎 shaken 条件为布尔（被震慑），无按层增伤
  5. 裂岳连击「破绽档位倾泻」——同上，无档位倾泻
  6. 气力之心「持有破绽增伤」被动——无 enemy-shaken 被动条件
  7. 破绽感知「破绽衰减减半」——破绽条衰减在 classes.py enemy_bar 配置，无技能级字段
  8. 守御姿态「受击转磐核」/ 磐核相关 —— guard_core 引擎未消费（数据化挂账）
  9. 大地之肤「磐核同时减伤」——无磐核联动被动
  10. 磐岩甲「磐核转护盾」——无磐核→护盾 effect
  11. 磐石之躯「减伤+反震」双效果被动——引擎被动单 proc，只落地减伤部分
  12. 气力万法「满磐核×0.7」——无磐核层数条件（res_cost guard_core 数据化）

结构：
  PLAYER_SKILLS_quan_shi : 拳师基础技能（Lv.1-26 两线共用，8 个）
  BRANCH_SKILLS_quan_shi : 拳师两条线（A线·破绽=攻线格斗士系；B线·磐核=守线磐石行者系）
    分支 key 沿用既有数字 1/2/3（evolve_branches 强耦合，classes.py:364）：
      1 = T1（Lv.30-58）  2 = T2（Lv.58-88）  3 = T3（Lv.90-98）
"""
# 本文件为独立翻译产物，仅做数据声明；不修改 game/data/skills.py，不执行任何合并。
# 新技能 key 全部使用 sk_qs_ 前缀（qs = quan_shi 拳师），避免与既有 sk_ 撞车（已 grep 确认无 sk_qs_*）。

PLAYER_SKILLS_quan_shi = {
    "cls_wu_seng": {
        "name": "拳师",
        "skills": {
            "sk_qs_zhi_quan": {
                "lv": 1, "mp": 3, "power": 0.8, "kind": "物理",
                "combo": "拳",
                # v151 推条+1：拳师破绽（敌身 shaken 条）推 1
                "shaken_gain": 1,
                "desc": "一记笔直的拳锋破空而出——造成 80% 物理伤害(连招【拳】)，命中推破绽+1",
                "name": "直拳",
            },
            "sk_qs_ce_ti": {
                "lv": 6, "mp": 5, "power": 1.0, "kind": "物理",
                "combo": "踢",
                "shaken_gain": 1,
                "desc": "侧身一记凌厉踢击——造成 100% 物理伤害(连招【踢】)，命中推破绽+1",
                "name": "侧踢",
            },
            "sk_qs_gang_quan": {
                "lv": 12, "mp": 8, "power": 1.3, "kind": "物理",
                "combo": "掌",
                "shaken_gain": 1,
                "desc": "拳掌如铁，蓄势待发——造成 130% 物理伤害(连招【掌】)，命中推破绽+1",
                "name": "钢拳",
            },
            "sk_qs_lian_zhao_san_lian": {
                "lv": 18, "mp": 10, "power": 0.7, "kind": "物理",
                "combo": "拳", "multi": 3, "cd": 2,
                # v151 三段+推条3：单次施放引擎注入一次，写总推条 3
                "shaken_gain": 3,
                "desc": "拳、踢、掌三段连环如行云流水——连续攻击 3 次(每次 70% 伤害)，命中推破绽+3",
                "name": "连招三连",
            },
            "sk_qs_zhen_di_ji": {
                "lv": 22, "mp": 10, "power": 1.1, "kind": "物理",
                "cd": 3,
                # v151 30% 眩晕：mech stun + mech_chance 固定概率（MECH_EFFECTS stun 支持）
                "mech": "stun", "mech_chance": 0.30,
                "desc": "重腿砸地，震波轰然扩散——造成 110% 物理伤害，30% 概率震晕目标 1 回合",
                "name": "震地击",
            },
            "sk_qs_tong_qiang": {
                "lv": 8, "mp": 5, "power": 0, "kind": "增益",
                "effect": "def_up", "cd": 3,
                "desc": "周身气劲凝为壁垒，坚不可摧——防御＋45% 持续 2 回合(补生存)",
                "name": "铜墙",
            },
            "sk_qs_chong_quan": {
                "lv": 16, "mp": 8, "power": 1.1, "kind": "物理",
                "combo": "拳",
                # v151 位移至前排（补机动）——引擎无玩家站位位移机制（见 engine_unsupported 2）
                "desc": "沉肩发力，拳势如弩箭离弦——造成 110% 物理伤害(连招【拳】)；拳势破空位移至前排(机动，引擎暂未落地站位位移)",
                "name": "冲拳",
            },
            "sk_qs_ming_xiang": {
                "lv": 24, "mp": 0, "power": 0, "kind": "增益",
                "cd": 4,
                # v151 回蓝+清1减益——引擎无 mp 恢复 / 玩家自身净化（见 engine_unsupported 1）
                "desc": "敛息凝神，引导气力温养周身——回复魔力并清除自身 1 个减益(续航；回蓝/净化引擎待落地)",
                "name": "冥想",
            },
        },
    },
}

BRANCH_SKILLS_quan_shi = {
    "cls_wu_seng": {
        "name": "拳师",
        "branches": {
            # ================= 分支 1 = T1（Lv.30-58） =================
            1: {
                # ---- A 线 · 破绽（破绽往"控"长）----
                "格斗士": {
                    "sk_qs_ji_feng_quan": {
                        "lv": 32, "mp": 8, "power": 0.9, "kind": "物理",
                        "combo": "拳",
                        "shaken_gain": 2,
                        "desc": "拳速如疾风掠影——造成 90% 物理伤害(连招【拳】)，命中推破绽+2",
                        "name": "疾风拳",
                    },
                    "sk_qs_xuan_feng_ti": {
                        "lv": 45, "mp": 12, "power": 1.0, "kind": "物理",
                        "combo": "踢", "pierce": True,
                        "shaken_gain": 2,
                        "desc": "身体旋起如风暴之眼——造成 100% 破防物理伤害(连招【踢】)，命中推破绽+2",
                        "name": "旋风踢",
                    },
                    "sk_qs_sui_lu_shi": {
                        "lv": 52, "mp": 15, "power": 1.4, "kind": "物理",
                        "combo": "拳", "cd": 2,
                        # 破绽满×1.35：目标被破绽震慑时伤害 ×1.35
                        "cond": {"type": "enemy_shaken_gt", "mult": 1.35, "label": "破绽震慑"},
                        "desc": "重拳直取颅骨，撼动敌人心神——造成 140% 物理伤害(拳连招)；敌人破绽满被震慑时伤害×1.35",
                        "name": "碎颅势",
                    },
                    "sk_qs_qi_li_bao_fa": {
                        "lv": 55, "mp": 0, "power": 1.8, "kind": "物理",
                        "cd": 3,
                        # v151 破绽层数增伤——引擎无按层增伤（布尔条件近似，见 engine_unsupported 4）
                        "cond": {"type": "enemy_shaken_gt", "mult": 1.5, "label": "破绽层数"},
                        "desc": "气力轰然爆发，灌注全身——造成 180% 物理伤害；破绽层数越高伤害越高(按层增伤引擎暂未落地，破绽满时伤害×1.5)",
                        "name": "气力爆发",
                    },
                    "sk_qs_beng_quan": {
                        "lv": 48, "mp": 12, "power": 1.2, "kind": "物理",
                        "combo": "拳", "cd": 2,
                        "shaken_gain": 3,
                        "desc": "拳风裹挟气力，直撼骨节——造成 120% 物理伤害(连招【拳】)，命中推破绽+3(补推条效率)",
                        "name": "崩拳",
                    },
                    "sk_qs_tie_shan_kao": {
                        "lv": 50, "mp": 0, "power": 0, "kind": "增益",
                        "effect": "def_up", "cd": 4,
                        # v151 格挡1次——引擎无 block_up buff（见 engine_unsupported 3）
                        "desc": "沉肩横身，铁山般靠向敌阵——格挡 1 次攻击(补生存；格挡效果引擎暂未落地，先以防御强化代替)",
                        "name": "铁山靠",
                    },
                },
                # ---- B 线 · 磐核（破绽往"防"长）----
                "磐石行者": {
                    "sk_qs_tie_bi_quan": {
                        "lv": 32, "mp": 8, "power": 0.9, "kind": "物理",
                        "combo": "拳",
                        "effect": "def_up",
                        "desc": "拳出如铁壁横移——造成 90% 物理伤害(连招【拳】)并进入防御姿态(防御强化)",
                        "name": "铁壁拳",
                    },
                    "sk_qs_shou_yu_zi_tai": {
                        "lv": 38, "mp": 0, "power": 0, "kind": "被动",
                        # v151 受击转磐核（敌人破绽转己方护盾）——guard_core 数据化挂账，引擎未消费（见 engine_unsupported 8）
                        "passive": {"proc": "guard_stance", "defend_hit_core": 1},
                        "desc": "以拳卸力，守御如磐——受击时将敌人破绽转为自身磐核(磐核引擎暂未落地，数据化挂账)",
                        "name": "守御姿态",
                    },
                    "sk_qs_pan_yan_shi_neng": {
                        "lv": 50, "mp": 0, "power": 1.0, "kind": "物理",
                        "combo": "拳", "cd": 2,
                        # 磐核线性倾泻 M = 1.0 + 0.7×核数：guard_core 数据化（res_cost/consume_all/discharge 引擎未消费）
                        "res_cost": {"guard_core": 1},
                        "consume_all": {"key": "guard_core"},
                        "discharge": {"base": 1.0, "per_core": 0.7},
                        "desc": "引磐核之力凝于一击——清空全部磐核释放，倍率 M = 1.0 + 0.7×核数(3 核 3.10 / 5 核 4.50；磐核引擎暂未落地)",
                        "name": "磐岩释能",
                    },
                    "sk_qs_fan_zhen": {
                        "lv": 52, "mp": 0, "power": 0, "kind": "被动",
                        "passive": {"proc": "reflect", "mult": 0.3, "chance": 0.30},
                        "desc": "以彼之力还施彼身——受到伤害时 30% 概率反弹 30% 伤害",
                        "name": "反震",
                    },
                    "sk_qs_yi_shou_wei_gong": {
                        "lv": 55, "mp": 0, "power": 0, "kind": "被动",
                        "passive": {"proc": "counter_attack", "chance": 0.30},
                        "desc": "守势之中暗藏杀机——受击时 30% 概率立即以普攻反击",
                        "name": "以守为攻",
                    },
                    "sk_qs_hou_tu": {
                        "lv": 46, "mp": 0, "power": 0, "kind": "增益",
                        # v151 减伤+30%（补生存）：reduce_all 为全队减伤 effect，单人=自身生效
                        "effect": "reduce_all", "reduce_all": 0.30, "cd": 4,
                        "desc": "气血盈满时身如大地——减伤＋30% 持续 2 回合(补生存)",
                        "name": "厚土",
                    },
                },
            },
            # ================= 分支 2 = T2（Lv.58-88） =================
            2: {
                # ---- A 线 · 破绽 ----
                "拳术师": {
                    "sk_qs_qi_li_zhi_xin": {
                        "lv": 60, "mp": 0, "power": 0, "kind": "被动",
                        # v151 持有破绽增伤——引擎无 enemy-shaken 被动条件（见 engine_unsupported 6）
                        "passive": {},
                        "desc": "气力在心底凝成泉眼——持有破绽时伤害提升(持有破绽增伤被动引擎暂未落地)",
                        "name": "气力之心",
                    },
                    "sk_qs_lian_huan_quan": {
                        "lv": 66, "mp": 12, "power": 0.6, "kind": "物理",
                        "combo": "拳", "multi": 4, "cd": 2,
                        "shaken_gain": 4,
                        "desc": "拳影连环不绝——连续出拳 4 次(每次 60% 伤害)，命中推破绽+4",
                        "name": "连环拳",
                    },
                    "sk_qs_qi_li_lie_kong": {
                        "lv": 74, "mp": 18, "power": 1.6, "kind": "物理",
                        "combo": "拳", "cd": 3,
                        # 破绽×1.35：目标被破绽震慑时伤害 ×1.35
                        "cond": {"type": "enemy_shaken_gt", "mult": 1.35, "label": "破绽震慑"},
                        "desc": "一拳击出，气浪撕裂长空——造成 160% 物理伤害(拳连招)；敌人破绽满被震慑时伤害×1.35",
                        "name": "气力裂空",
                    },
                    "sk_qs_lie_yue_lian_ji": {
                        "lv": 70, "mp": 20, "power": 1.5, "kind": "物理",
                        "combo": "拳", "cd": 3,
                        # v151 破绽档位倾泻——引擎无档位倾泻（布尔条件近似，见 engine_unsupported 5）
                        "cond": {"type": "enemy_shaken_gt", "mult": 1.5, "label": "破绽倾泻"},
                        "desc": "拳劲足以裂开山岳——造成 150% 物理伤害(拳连招)；按破绽档位倾泻伤害(档位倾泻引擎暂未落地，破绽满时伤害×1.5)",
                        "name": "裂岳连击",
                    },
                    "sk_qs_po_zhan_gan_zhi": {
                        "lv": 78, "mp": 0, "power": 0, "kind": "被动",
                        # v151 破绽衰减减半——破绽条衰减在 classes.py enemy_bar 配置（见 engine_unsupported 7）
                        "passive": {},
                        "desc": "对破绽流转的敏锐感知——敌人破绽每回合自然衰减减半(衰减配置在职业级 enemy_bar，引擎暂未落地技能级覆盖)",
                        "name": "破绽感知",
                    },
                    "sk_qs_zhen_she_quan": {
                        "lv": 84, "mp": 18, "power": 1.7, "kind": "物理",
                        "combo": "拳", "cd": 3,
                        # v151 破绽满触发震慑（补控制）：目标被震慑时伤害提升 + 独立眩晕判定
                        "mech": "stun", "mech_chance": 0.35,
                        "cond": {"type": "enemy_shaken_gt", "mult": 1.2, "label": "破绽震慑"},
                        "desc": "撼动心神的一拳——造成 170% 物理伤害(拳连招)，35% 概率震慑目标；敌人破绽满被震慑时伤害×1.2",
                        "name": "震慑拳",
                    },
                },
                # ---- B 线 · 磐核 ----
                "铁壁行者": {
                    "sk_qs_pan_shi_zhi_xin": {
                        "lv": 60, "mp": 0, "power": 0, "kind": "被动",
                        # v151 满溢转盾——引擎无磐核联动（数据化挂账，见 engine_unsupported 8）
                        "passive": {"proc": "dmg_taken", "reduce": 0.05},
                        "desc": "心如磐石，不动如山——受到伤害再减 5%；磐核满溢转护盾(磐核引擎暂未落地)",
                        "name": "磐石之心",
                    },
                    "sk_qs_fan_ji_zhi_wang": {
                        "lv": 66, "mp": 0, "power": 0, "kind": "被动",
                        "passive": {"proc": "counter_attack", "chance": 0.40},
                        "desc": "以守为攻的极致——受击时 40% 概率立即以普攻反击(反击概率提升)",
                        "name": "反击之王",
                    },
                    "sk_qs_pan_he_bao_fa": {
                        "lv": 70, "mp": 0, "power": 1.5, "kind": "物理",
                        "combo": "拳", "cd": 3,
                        # 磐核数×0.7：guard_core 数据化（res_cost 引擎未消费）
                        "res_cost": {"guard_core": 3},
                        "desc": "磐核凝为一点轰然迸发——清空 3 核造成 150% 物理伤害(磐核数×0.7 倾泻；磐核引擎暂未落地)",
                        "name": "磐核爆发",
                    },
                    "sk_qs_qi_li_shou_yu": {
                        "lv": 74, "mp": 0, "power": 0, "kind": "增益",
                        "effect": "shield_all", "team": "shield_all", "cd": 4,
                        "desc": "气力化作守护之墙——为全队张开生命值 20% 的护盾(全队护盾)",
                        "name": "气力守御",
                    },
                    "sk_qs_da_di_zhi_fu": {
                        "lv": 78, "mp": 0, "power": 0, "kind": "被动",
                        # v151 磐核同时减伤——无磐核联动被动（见 engine_unsupported 9）
                        "passive": {},
                        "desc": "大地之力渗入躯体——持有磐核时同时获得减伤(磐核联动减伤引擎暂未落地)",
                        "name": "大地之肤",
                    },
                    "sk_qs_pan_yan_jia": {
                        "lv": 84, "mp": 0, "power": 0, "kind": "增益",
                        "effect": "shield_all", "cd": 5,
                        # v151 磐核转护盾（补生存）——无磐核→护盾 effect（见 engine_unsupported 10）
                        "desc": "磐岩之力凝成护甲——将磐核转化为护盾(补生存；磐核转盾引擎暂未落地，先以全队护盾代替)",
                        "name": "磐岩甲",
                    },
                },
            },
            # ================= 分支 3 = T3（Lv.90-98） =================
            3: {
                # ---- A 线 · 破绽（淬势→破绽 机制并入本线：撼岳·终焉） ----
                "破晓者": {
                    "sk_qs_qi_li_tong_tian": {
                        "lv": 92, "mp": 30, "power": 2.4, "kind": "物理",
                        "combo": "拳", "cd": 4,
                        # 破绽增伤：目标被破绽震慑时伤害 ×1.35
                        "cond": {"type": "enemy_shaken_gt", "mult": 1.35, "label": "破绽震慑"},
                        "desc": "气机直冲云霄，一拳轰出——造成 240% 物理伤害(拳连招)；敌人破绽满被震慑时伤害×1.35",
                        "name": "气力通天",
                    },
                    "sk_qs_wu_ying_lian_da": {
                        "lv": 95, "mp": 20, "power": 0.7, "kind": "物理",
                        "combo": "拳", "multi": 4, "cd": 3,
                        "shaken_gain": 4,
                        "desc": "拳影快到无形——连续攻击 4 次(每次 70% 伤害)，命中推破绽+4",
                        "name": "无影连打",
                    },
                    "sk_qs_qi_li_tian_di": {
                        "lv": 96, "mp": 40, "power": 2.8, "kind": "物理",
                        "combo": "拳", "cd": 5,
                        # 破绽封顶×2.5：目标被破绽震慑时伤害 ×2.5
                        "cond": {"type": "enemy_shaken_gt", "mult": 2.5, "label": "破绽封顶"},
                        "desc": "气力贯通天地，一拳定乾坤——造成 280% 物理伤害(拳连招)；敌人破绽封顶被震慑时伤害×2.5",
                        "name": "气力天地",
                    },
                    "sk_qs_han_yue_zhong_yan": {
                        "lv": 98, "mp": 0, "power": 3.0, "kind": "物理",
                        "combo": "拳", "cd": 6,
                        # v151 满破绽震慑 1 回合（硬控）：mech stun 必中 + 破绽满条件（淬势·撼岳·终焉 并入本线）
                        "mech": "stun", "mech_chance": 1.0,
                        "cond": {"type": "enemy_shaken_gt", "mult": 1.0, "label": "满破绽震慑"},
                        "desc": "撼动山岳的终焉之拳——造成 300% 物理伤害(拳连招)；敌人破绽满时必定震慑 1 回合(硬控；淬势撼岳并入破绽线)",
                        "name": "撼岳·终焉",
                    },
                },
                # ---- B 线 · 磐核 ----
                "磐岩壁垒": {
                    "sk_qs_pan_shi_zhi_qu": {
                        "lv": 92, "mp": 0, "power": 0, "kind": "被动",
                        # v151 减伤+反震——引擎被动单 proc，只落地减伤部分（见 engine_unsupported 11）
                        "passive": {"proc": "dmg_taken", "reduce": 0.20},
                        "desc": "绝境之中身化磐石——减伤 20%，受击时反震(反震部分引擎暂未落地，先落地减伤)",
                        "name": "磐石之躯",
                    },
                    "sk_qs_da_di_shou_hu": {
                        "lv": 95, "mp": 0, "power": 0, "kind": "增益",
                        "effect": "reduce_all", "reduce_all": 0.30, "team": "reduce_all", "cd": 6,
                        "desc": "大地之力加护全队——全队减伤 30% 持续 3 回合(随等级提升至 50%)",
                        "name": "大地守护",
                    },
                    "sk_qs_qi_li_wan_fa": {
                        "lv": 98, "mp": 0, "power": 3.2, "kind": "物理",
                        "combo": "拳", "cd": 5,
                        # v151 满磐核×0.7——无磐核层数条件（res_cost guard_core 数据化，见 engine_unsupported 12）
                        "res_cost": {"guard_core": 5},
                        "desc": "气力流转，融贯万法——造成 320% 物理伤害(拳连招)；满磐核时威力×0.7 追加(磐核引擎暂未落地，数据化挂账)",
                        "name": "气力万法",
                    },
                },
            },
        },
    },
}

# 供主 agent 收尾：v151 机制字段引擎不支持清单（key → 机制 → 说明）
ENGINE_UNSUPPORTED_quan_shi = {
    "sk_qs_ming_xiang": ["回蓝", "清自身 1 减益"],
    "sk_qs_chong_quan": ["位移至前排"],
    "sk_qs_tie_shan_kao": ["格挡 1 次"],
    "sk_qs_qi_li_bao_fa": ["破绽层数增伤（按层）"],
    "sk_qs_lie_yue_lian_ji": ["破绽档位倾泻"],
    "sk_qs_qi_li_zhi_xin": ["持有破绽增伤（被动）"],
    "sk_qs_po_zhan_gan_zhi": ["破绽衰减减半"],
    "sk_qs_shou_yu_zi_tai": ["受击转磐核"],
    "sk_qs_pan_yan_shi_neng": ["磐核倾泻 discharge"],
    "sk_qs_pan_shi_zhi_xin": ["磐核满溢转盾"],
    "sk_qs_pan_he_bao_fa": ["磐核数×0.7 倾泻"],
    "sk_qs_da_di_zhi_fu": ["磐核联动减伤"],
    "sk_qs_pan_yan_jia": ["磐核转护盾"],
    "sk_qs_pan_shi_zhi_qu": ["减伤+反震（双效果被动）"],
    "sk_qs_qi_li_wan_fa": ["满磐核×0.7 条件"],
}
