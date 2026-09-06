# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - weapon_effect_data.py

武器特效参数表（v180E 阶段4：数值下沉数据层——数据驱动铁律，代码零硬编码）。

每个特效 key 一组参数，与 game/core/weapon_effects.py 的 handler 对应：
- handler 用 effect_data(battle, player, key) 读本表（经装备 we_data 覆盖层；
  装备行 we_data 存在时覆盖表默认，否则用本表权威值）
- 本表 = 参数权威默认（未来装备接入只需声明 weapon_effect: key 即自动按此表生效）
- 数值来源：v140 波3.1 handler 代码原硬编码值逐字提取（2026-09-07 盘点）

表结构：key -> {参数名: 值}。参数名见各 handler 读取处。
"""
# flake8: noqa

WEAPON_EFFECT_DATA = {
    # ---------- battle_start 开战 ----------
    "starlight_bulwark": {"shield_hp_pct": 0.10, "refresh_turns": 5},      # 星辉壁垒：10%生命盾/5刻刷新
    "gale_step": {"stacks": 1, "spd_pct": 0.15, "turns": 3},               # 疾风步：速度+15% 3刻
    "swift_boots": {"stacks": 1, "spd_pct": 0.20, "turns": 3},             # 迅捷如风：速度+20% 3刻
    "deadman_stride": {"stacks": 2, "spd_pct": 0.15, "turns": 4},          # 亡者疾行：速度+15% 4刻
    "temple_stride": {"stacks": 2, "spd_pct": 0.20, "turns": 4},           # 圣殿疾行：速度+20% 4刻
    "void_stride": {"stacks": 2, "spd_pct": 0.25, "turns": 4},             # 虚空疾行：速度+25% 4刻
    "abyss_barrier": {"max_hp_pct": 0.08},                                 # 深渊屏障：最大生命+8%
    "eclipse_crown": {"shield_hp_pct": 0.15, "spd_pct": 0.10, "next_atk_pct": 0.15},  # 蚀月之蚀
    "arcane_firmament": {"matk_pct": 0.15, "skill_dmg_pct": 0.10},         # 奥术苍穹
    "undying_will": {"hp_pct": 0.10, "threshold": 0.20},                   # 不灭意志：<20% 回10%

    # ---------- hit 命中 ----------
    "wind_mark": {"max_stack": 4, "spd_pct_per": 0.02},                    # 风痕：4层每层速+2%
    "hunter_open": {"count": 3, "atk_pct": 0.12},                          # 破绽：3次后12%真伤
    "smith_blaze_wound": {"chance": 0.20, "dot_pct": 0.015, "dot_pct_boss": 0.01, "turns": 3},  # 裂伤
    "rong_lu_yu_wen": {"chance": 0.20, "dot_pct": 0.03, "dot_pct_boss": 0.015, "turns": 2},  # 熔炉余温
    "frost_ring": {"chance": 0.25, "slow_turns": 2, "slow_pct": 0.40},     # 霜环
    "blood_trace": {"chance": 0.25, "pct": 0.02, "pct_boss": 0.015, "turns": 4},  # 败血
    "wind_split": {"chance": 0.25, "atk_pct": 0.50},                       # 裂风矢
    "holy_judgment_field": {"chance": 0.30, "slow_turns": 2, "slow_pct": 0.30, "heal_down": 2},  # 圣裁领域
    "thunder_weave": {"max_stack": 5, "spd_pct_per": 0.02, "atk_pct_per": 0.01, "charge_pct": 0.20},  # 雷纹连打
    "phantom_barrage": {"chance": 0.20, "atk_pct": 0.30, "pene_pct": 0.50, "guarantee": 5},  # 幻影连射
    "siren_fang": {"count": 3, "atk_pct": 0.40},                           # 海妖猎杀
    "soul_eater": {"cur_hp_pct": 0.02},                                    # 破败之吻：当前生命2%
    "star_pierce": {"count": 4, "atk_pct": 0.20, "lost_hp_pct": 0.03, "cap_pct": 0.05},  # 穿星
    "combo_end": {"combo_need": 3, "crit_dmg": 0.40},                      # 连击终点
    "novice_lifesteal": {"heal_pct": 0.05},                                # 吸血：伤害5%回血
    "novice_hunt_combo": {"per_stack": 0.08, "max_stack": 5},              # 猎影：暴击叠连击
    "novice_wind_spd": {"spd_pct": 0.05, "turns": 2},                      # 翠风：命中加速

    # ---------- skill_hit 技能命中 ----------
    "afterglow_splash": {"chance": 0.30, "atk_pct": 0.15},                 # 余波
    "spellblade_echo": {"atk_pct": 0.25},                                  # 咒刃
    "annihilation_echo": {"chance": 0.35, "atk_pct": 0.30},                # 湮灭回响
    "ember_burn": {"chance": 0.30, "dot_pct": 0.015, "dot_pct_boss": 0.01, "turns": 3},  # 烬燃
    "everfrost_domain": {"chance": 0.30, "freeze_turns": 1, "boss_slow": 2, "cd": 3},  # 永冻领域
    "everfrost_scepter": {"chance": 0.20, "freeze_turns": 1, "boss_slow": 2},  # 永霜禁锢
    "trinity_rhythm": {"atk_pct": 0.30, "thunder_pct": 0.15},              # 三相律动
    "mountain_break": {"atk_pct": 0.25},                                   # 破岳
    "oath_blade": {"atk_pct": 0.25},                                       # 咒刃之誓
    "endless_radiance": {"crit_dmg_pct": 0.25, "shield_hp_pct": 0.05, "shield_turns": 2, "cd": 3},  # 无尽辉光
    "endless_blade": {"atk_pct": 0.20},                                    # 无尽锋芒
    "rune_amp": {"max_stack": 5, "dmg_pct_per": 0.02},                     # 铭文增幅
    "sage_amp": {"need": 2, "charge_pct": 0.25},                           # 秘典增幅
    "eternal_codex": {"max_stack": 8, "dmg_pct_per": 0.015},               # 永恒契约

    # ---------- taken 受击 ----------
    "sentinel_aegis": {"chance": 0.15, "base": 6, "per_lv": 0.5, "turns": 3, "cd": 1},  # 哨兵壁垒
    "iron_echo": {"chance": 0.20, "reflect_pct": 0.40, "heal_pct": 0.02},  # 铁壁回响
    "frost_crown": {"chance": 0.10, "max_per_battle": 2, "freeze_turns": 1, "boss_slow": 2},  # 寒霜凝视
    "thorn_armor": {"reflect_pct": 0.15},                                  # 荆棘缠绕
    "guardian_will": {"chance": 0.08, "weaken": 0.25},                     # 卫士信念
    "deeprock_aegis": {"chance": 0.10, "shield_pct": 0.08, "cd": 2},       # 深岩壁垒
    "gargoyle_retort": {"next_atk_pct": 0.30},                             # 石像反击
    "titan_retort": {"next_atk_pct": 0.40},                                # 泰坦之怒
    "ranger_retort": {"next_atk_pct": 0.20},                               # 巡林反击
    "dragon_spine_mail": {"chance": 0.15, "reflect_pct": 0.25, "heal_down": 2},  # 龙脊反噬
    "retribution_ring": {"chance": 0.20, "reflect_pct": 0.30},             # 复仇之环
    "ember_bulwark": {"max_hp_pct": 0.05, "burn_stack": 1, "burn_cap": 5},  # 烬火燎原

    # ---------- heal 治疗 ----------
    "vital_band": {"heal_pct": 0.15},                                      # 坚毅祝福
    "holy_radiance_mail": {"heal_pct": 0.20},                              # 圣辉涌动
    "echo_band": {"heal_pct": 0.25},                                       # 回响祝福(戒)
    "echo_bless": {"overflow_pct": 0.30, "cap_hp_pct": 0.10},              # 回响祝福(杖)
    "atonement_shield": {"cap_hp_pct": 0.15},                              # 赎罪之盾
    "holy_word_bind": {"chance": 0.20, "freeze_turns": 1, "boss_slow": 2},  # 圣言禁锢
    "novice_regen_heal": {"heal_pct": 0.10},                               # 庇护：受疗+10%

    # ---------- turn_start 刻开始 ----------
    "guard_regen": {"pct": 0.02},                                          # 铁卫意志：已损2%
    "dawn_regen": {"pct": 0.02},                                           # 晨曦微光：最大2%
    "undying_band": {"pct": 0.015},                                        # 不灭微光：最大1.5%
    "death_dance": {"pool_pct": 0.35, "pay_pct": 0.10, "max_turns": 10},   # 死亡之舞
    "time_staff": {"per_pct": 0.015, "max_stack": 10},                     # 岁月流转

    # ---------- enemy_act 敌人行动后 ----------
    "randuin_weary": {"max_stack": 3, "spd_down_pct": 0.06},               # 兰顿倦意
    "ice_vein": {"max_stack": 3, "spd_down_pct": 0.08},                    # 冰脉寒流

    # ---------- threshold 生命阈值 ----------
    "time_freeze": {"threshold": 0.30, "per_battle": 1},                   # 时光凝滞
    "bedrock_crown": {"threshold": 0.25, "shield_hp_pct": 0.20, "turns": 4},  # 磐石守护
    "firmament_crown": {"threshold": 0.30, "shield_hp_pct": 0.12, "turns": 3, "per_battle": 2},  # 苍穹庇护
    "gargoyle_heart": {"threshold": 0.30, "shield_hp_pct": 0.25, "turns": 4, "heal_pct": 0.10},  # 石像鬼之心
    "undying_will_t": {"threshold": 0.20, "heal_pct": 0.10},               # 不灭意志(threshold 段)

    # ---------- kill 击杀 ----------
    "dusk_blade": {"next_atk_pct": 0.30},                                  # 暮裂潜行

    # ---------- passive 常驻 ----------
    "twilight_execute": {"threshold": 0.40, "dmg_mult": 1.25},             # 暮光处决
    "star_slayer_edge": {"threshold": 0.70, "dmg_mult": 1.15, "crit_dmg": 0.30},  # 弑星
    "arcane_firmament_p": {"skill_dmg_pct": 0.10},                         # 奥术苍穹(技能+10%)
    "death_dance_armor": {"taken_reduce_pct": 0.08, "revive_hp_pct": 0.12},  # 亡者之舞
    "time_staff_p": {"per_pct": 0.015, "max_stack": 10},                   # 岁月流转(攻击)
    "eternal_codex_p": {"per_pct": 0.015, "max_stack": 8},                 # 永恒契约(技能伤)
    "rune_amp_p": {"per_pct": 0.02},                                       # 铭文增幅(技能伤)
    "sage_amp_p": {"charge_pct": 0.25},                                    # 秘典增幅
    "thunder_weave_p": {"charge_pct": 0.20},                               # 雷纹连打(满层)
    "trinity_rhythm_p": {"atk_pct": 0.30},                                 # 三相律动(普攻)
    "mountain_break_p": {"atk_pct": 0.25},                                 # 破岳(普攻)
    "oath_blade_p": {"atk_pct": 0.25},                                     # 咒刃之誓
    "retort_p": {"fallback_pct": 0.20},                                    # 受击反击(缺省)
    "dusk_blade_p": {"atk_pct": 0.30},                                     # 暮裂潜行(攻击)
    "combo_end_p": {"crit_dmg": 0.40},                                     # 连击终点(暴伤)

    # ---------- novice 新手特效 ----------
    "novice_first_turn_guard": {"reduce_pct": 0.10},                       # 守御：首刻-10%
    "novice_spark_followup": {"atk_pct": 0.10},                            # 星火：下次普攻+10%
    "novice_first_turn_dodge": {"dodge_pct": 0.05},                        # 远行：首刻闪避+5%
    "novice_dawn_mana": {"mp": 10},                                        # 晨星：首次回10蓝
}
