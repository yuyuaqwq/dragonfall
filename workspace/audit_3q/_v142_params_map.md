# v142 数据下沉映射表 — 供子 agent 参考（勿修改）
# 格式: effect 名 → params（从 affix_effects.py 旧 handler 提取，数值保持原样）

# ============ 攻击命中型（SET_PROC，走 _execute_set_proc） ============

# ---- 物理/魔法附加伤害（proc_flat_dmg） ----
"gale_double":        {"type": "proc_flat_dmg", "chance": 0.25, "stat": "atk", "pct": 0.50, "tag": "🌪️", "name": "风行连射"}
"shadow_combo_double":{"type": "proc_flat_dmg", "chance": 0.25, "stat": "atk", "pct": 0.40, "tag": "🗡️", "name": "轻影连刺"}
"phantom_echo":       {"type": "proc_flat_dmg", "chance": 0.20, "stat": "atk", "pct": 0.60, "pct_alt": 0.35, "cond_crit": true, "tag": "👻", "name": "幻影分身"}  # 暴击时 chance 0.35，见 _last_crit
"sky_chain":          {"type": "proc_flat_dmg", "chance": 0.25, "stat": "atk", "pct": 0.60, "pct_alt": 0.75, "cond_mark": true, "tag": "☄️", "name": "苍穹连星"}
"hunt_pack":          {"type": "proc_flat_dmg", "chance": 0.30, "stat": "atk", "pct": 0.50, "pct_alt": 0.60, "cond_hp_lt": 0.50, "tag": "🏹", "name": "狩猎本能"}
"iron_execute_rampage":{"type": "proc_flat_dmg", "chance": 0.30, "stat": "atk", "pct": 0.50, "cond_hp_lt": 0.40, "tag": "💀", "name": "黑铁斩杀"}
"qi_shi_charge":      {"type": "proc_flat_dmg", "chance": 0.18, "stat": "atk", "pct": 1.00, "once_per_round": true, "tag": "🐎", "name": "骑士冲锋"}
"lei_ting_chain":     {"type": "proc_flat_dmg", "chance": 0.25, "stat": "matk", "pct": 0.50, "pct_alt": 0.75, "cond_thunder_mark": true, "edef": "mdef", "dmg_type": "magic", "tag": "⚡", "name": "连环雷"}
"mi_fa_arcane_bolt":  {"type": "proc_flat_dmg", "chance": 0.20, "stat": "matk", "pct": 0.80, "edef": "mdef", "dmg_type": "magic", "tag": "✨", "name": "秘术重雷"}
"xing_jie_starfall":  {"type": "proc_flat_dmg", "chance": 0.15, "stat": "matk", "pct": 0.80, "edef": "mdef", "dmg_type": "magic", "tag": "☄️", "name": "星坠"}
"xing_chen_starstrike":{"type": "proc_flat_dmg", "chance": 0.25, "stat": "matk", "pct": 0.75, "edef": "mdef", "dmg_type": "magic", "tag": "🌟", "name": "星辰轰击", "cond_thunder_full": true}  # 雷印满3必触发
"mi_fa_condense":     {"type": "proc_mp_on_dmg", "chance": 0.25, "stat": "matk", "pct": 0.40, "mp_pct": 0.15, "edef": "mdef", "dmg_type": "magic", "tag": "✨", "name": "秘术回响"}
"fu_wen_glyph_bolt":  {"type": "proc_flat_dmg", "chance": 0.30, "stat": "matk", "pct": 0.45, "pct_alt": 0.75, "cond_thunder_ge2": true, "consume_thunder": true, "edef": "mdef", "dmg_type": "magic", "tag": "📜", "name": "符文雷刻"}
"fu_wen_annihilate":  {"type": "proc_thunder_burst", "chance": 0.30, "stat": "matk", "max_mark": 3, "burst_pct": 0.90, "edef": "mdef", "tag": "📜", "name": "符文爆印"}

# ---- 处决型（proc_execute） ----
"midnight_assassinate":{"type": "proc_execute", "chance": 0.35, "stat": "atk", "pct": 0.40, "hp_lt": 0.30, "true_dmg": true, "tag": "🗡️", "name": "午夜暗杀"}
"night_backstab":     {"type": "proc_execute", "stat": "atk", "pct": 0.25, "hp_full": true, "chance": 0.20, "pct2": 0.05, "hp_pct_dmg": true, "tag": "🌙", "name": "夜行背刺"}  # 满血+25%增伤；否则20%概率5%max_hp真伤

# ---- 标记型（proc_mark） ----
"travel_mark":        {"type": "proc_mark", "chance": 0.30, "max_mark": 5, "mark_desc": "每层 +20% 伤害", "tag": "🎒", "name": "旅人标记"}
"shadow_track":       {"type": "proc_mark", "chance": 0.30, "max_mark": 5, "mark_desc": "暗影标记", "tag": "🌑", "name": "暗影追踪"}
"shadow_etch_vuln":   {"type": "proc_mark", "chance": 0.30, "max_mark": 5, "mark_desc": "每层 +15% 受伤害", "tag": "🌒", "name": "阴影蚀刻"}
"hunter_mark_bonus":  {"type": "proc_mark_or_dmg", "chance": 0.40, "max_mark": 5, "dmg_pct": 0.15, "tag": "🏹", "name": "猎手印记"}  # 有标记→追加15%伤害；否则叠1层
"xue_tu_spark":       {"type": "proc_mark", "chance": 0.40, "max_mark": 3, "mark_key": "element_marks", "tag": "⚡", "name": "蓄雷"}
"shadow_erode_poison":{"type": "proc_mark", "chance": 0.30, "max_mark": 5, "mark_key": "poison", "tag": "☠️", "name": "阴影侵蚀"}

# ---- 灼烧/冰冻/暗蚀型 ----
"burn":               {"type": "proc_burn", "chance": 0.30, "burn_pct": 0.05, "burn_turns": 2, "max_stacks": 5, "tag": "🔥", "name": "烈焰之力"}
"hei_zhao_erode":     {"type": "proc_erode", "chance": 0.30, "max_stacks": 2, "pct": 1, "tag": "🌑", "name": "暗蚀"}
"frost_hunt_freeze":  {"type": "proc_freeze", "chance": 0.20, "freeze_turns": 1, "tag": "🧊", "name": "霜猎冰冻"}

# ---- 减速/破甲/敌方降攻型 ----
"frost":              {"type": "proc_slow", "chance": 0.30, "slow_pct": 0.15, "slow_turns": 2, "tag": "❄️", "name": "寒霜之力"}
"pierce":             {"type": "proc_armor_break", "chance": 0.30, "break_pct": 0.15, "break_turns": 2, "tag": "⚔️", "name": "破甲之力"}
"ranger_net":         {"type": "proc_slow", "chance": 0.30, "slow_pct": 0.15, "slow_turns": 2, "tag": "🕸️", "name": "巡林罗网"}
"silver_knight_lance": {"type": "proc_armor_break", "chance": 0.30, "break_pct": 0.15, "break_turns": 2, "bonus_atk_pct": 0.30, "tag": "🐎", "name": "白银冲锋"}
"li_ming_dawnbreak":  {"type": "proc_anti_heal", "chance": 0.30, "break_pct": 0.15, "break_turns": 2, "anti_heal_pct": 0.30, "tag": "🌅", "name": "黎明破晓"}
"jing_tie_refine":    {"type": "proc_armor_stack", "chance": 0.50, "max_stacks": 3, "break_pct": 0.05, "break_turns": 2, "tag": "⚒️", "name": "精淬"}
"long_yi_dread":      {"type": "proc_mon_atk_down", "chance": 0.30, "atk_down_pct": 0.15, "turns": 2, "tag": "🐉", "name": "龙威压制"}

# ---- 吸血/回血/回蓝型 ----
"lifesteal_set":      {"type": "proc_lifesteal", "chance": 0.30, "lifesteal_pct": 0.15, "tag": "🌑", "name": "深渊之力"}
"cloth_regen_battle": {"type": "proc_heal_hp", "chance": 0.30, "heal_pct": 0.08, "tag": "☀️", "name": "布衣愈合"}
"bless_chant_mp":     {"type": "proc_heal_mp", "chance": 0.35, "heal_pct": 0.05, "tag": "🎵", "name": "祝福咏叹"}
"judge_purify_heal":  {"type": "proc_purify_heal", "chance": 0.25, "heal_pct": 0.04, "tag": "⚖️", "name": "审判净化"}
"ranger_regen_wild":  {"type": "proc_heal_hp", "chance": 0.40, "heal_pct": 0.05, "tag": "🌳", "name": "护林再生"}
"xing_zhe_flow":      {"type": "proc_lifesteal", "chance": 1.0, "lifesteal_pct": 0.06, "tag": "🩸", "name": "行者游血"}
"xing_zhe_hunt":      {"type": "proc_lifesteal", "chance": 0.40, "lifesteal_pct": 0.12, "tag": "🩸", "name": "猎血"}

# ---- Buff 型 ----
"eagle_vision":       {"type": "proc_buff", "chance": 0.35, "buff_key": "eagle_vision", "buff_val": true, "tag": "🦅", "name": "鹰眼锐视"}
"shadow_combo_cp":    {"type": "proc_res_gain", "chance": 0.30, "res_key": "cp", "amount": 1, "tag": "🗡️", "name": "轻影连击"}
"bai_lian_forge":     {"type": "proc_buff", "chance": 1.0, "buff_key": "bai_lian_lv", "buff_mode": "stack", "buff_max": 10, "tag": "🔨", "name": "百炼"}
"xue_tu_surge":       {"type": "proc_buff", "chance": 1.0, "buff_key": "xue_tu_surge_lv", "buff_mode": "stack", "buff_max": 3, "tag": "⚡", "name": "蓄能"}
"night_stealth_exec": {"type": "proc_stealth", "chance": 0.30, "hp_lt": 0.30, "buff_key": "stealth", "tag": "🌙", "name": "夜行潜行"}

# ---- 处决/必暴 ----
"execute":            {"type": "proc_execute", "chance": 1.0, "hp_lt": 0.30, "dmg_pct": 0.25, "pct_of_dmg": true, "tag": "💀", "name": "灭世之力"}  # 敌方<30%血时追加25%本次伤害

# ---- 雷印体系（proc_thunder_burst 已覆盖 fu_wen_annihilate） ----

# ============ 受击直连型（battle.py → 数据驱动 TAKEN） ============
# 这些是受击触发，走 TAKEN_EFFECTS（补 params 后由 _affix_on_taken 消费）
"tie_pi_bulwark":     {"type": "taken_shield", "chance": 0.20, "shield_pct": 0.05, "shield_turns": 1, "tag": "🛡️", "name": "铁皮护体"}
"tie_pi_harden":      {"type": "taken_def_up_stack", "chance": 0.30, "def_pct": 0.15, "turns": 2, "max_stacks": 2, "tag": "🛡️", "name": "铁皮厚盾"}
"shou_wang_ward":     {"type": "taken_dmg_cut", "chance": 0.25, "cut_pct": 0.50, "tag": "🛡️", "name": "守望开盾"}
"ferry_repel":        {"type": "taken_counter", "chance": 0.25, "atk_pct": 0.40, "once_per_round": true, "tag": "🌊", "name": "渡口回潮"}
"tie_shou_blood":     {"type": "taken_heal", "chance": 0.30, "heal_pct": 0.03, "tag": "🩸", "name": "拳心回流"}
