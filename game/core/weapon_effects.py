# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心层 - weapon_effects.py（v140 波3.1：特效装备战斗消费引擎）
背景：v140 波1 数据层新增 70 件特效装备（equip_add_effects.py → equip_roster.py），
每件带 weapon_effect 字段（装备级特效注册 key）。本文件是消费端：
- WEAPON_EFFECTS 注册表：effect_key → (事件组, handler 函数)
- weapon_effect_ids(battle, player)：收集已装备特效 key（各槽位 weapon_effect 字段）
- proc(battle, player, event, ctx, logs)：统一分发（battle.py 各钩子调用）

触发时机（event）：
- battle_start  战斗开始（护盾/疾风/深渊屏障/蚀月）
- hit           攻击命中后（叠层/真伤/DOT/减速/追加攻击）
- skill_hit     技能命中后（溅射/铭文叠层/冻结/三相）
- skill_cast    技能释放后（不要求命中，施法计数）
- taken         受击时（护盾/反弹/反击/重伤/缓伤池）
- taken_after   受击后（下一次攻击强化标记）
- heal          治疗结算时（回复量加成/溢出转盾）
- turn_start    刻开始（回复/缓伤池结算/岁月流转）
- turn_end      刻结束（岁月流转叠层）
- enemy_act     敌人行动后（兰顿/冰脉减速）
- threshold     生命阈值（金身/磐石/不灭/苍穹/石像鬼之心）
- crit          暴击后（奥拉圣剑护盾/无终追击）
- kill          击杀后（暮裂潜行）
- passive       常驻被动判定（暮光处决/弑星/奥术苍穹/死亡之舞减伤）
- dot_taken     受击 DOT 结算后（死亡之舞缓伤）

约定（与 affix_effects.py 同风格）：
- handler 内部自查 weapon_effect_ids（并列 if 语义，多个特效可同时触发）
- 数值全部读数据 special 字段解析或代码内默认值（部分特效数值写在 special 文案，
  为可控实现，数值以本文档 handler 内 DEFAULT 为准——special 仅作展示）
- 每个 handler ~5-20 行，全部走 battle._deal_damage / _add_shield / _heal_player 等既有通道
- 战斗开始类特效在 Battle.__init__ 末尾调用 proc(battle, player, "battle_start", {}, [])
"""

import random

# v152：CD ready_at 换算用 ACT_TICK（1 刻 ≈ ACT_TICK 时刻；v181.P2B 起权威定义在
# core/constants.py —— 原顶层 from ..battle import ACT_TICK 系 core→battle 反向 import，已消除）
from .constants import ACT_TICK
# v180E 阶段4：武器特效参数权威表（数据层；延迟导入避免 data→core 循环）
_WE_DATA_TABLE = None


def _we_defaults(key: str) -> dict:
    """读参数权威表（延迟导入防循环）。"""
    global _WE_DATA_TABLE
    if _WE_DATA_TABLE is None:
        try:
            from ..data.weapon_effect_data import WEAPON_EFFECT_DATA
            _WE_DATA_TABLE = WEAPON_EFFECT_DATA
        except Exception:
            _WE_DATA_TABLE = {}
    return dict((_WE_DATA_TABLE or {}).get(key) or {})


def _we_family(key: str) -> str:
    """读数据表 family 字段（C1 标注的机制族；缺省空 = 未族化走旧 handler）。"""
    return str((_we_defaults(key) or {}).get("family") or "")

# ---------------------------------------------------------------- 读取器

def weapon_effect_ids(battle, player) -> list:
    """收集已装备特效 key（v140 装备级 weapon_effect 字段）。"""
    out = []
    for item in (player.get("equipment") or {}).values():
        if not item:
            continue
        we = item.get("weapon_effect")
        if we:
            out.append(we)
    return out


def effect_data(battle, player, key: str) -> dict:
    """武器特效 key 的参数（数值权威 = WEAPON_EFFECT_DATA 表 + 装备行 we_data 覆盖层）。

    数据驱动铁律（v180E 阶段4）：特效数值权威在数据层（game/data/weapon_effect_data.py
    WEAPON_EFFECT_DATA），handler 一律读参不再硬编码。装备实例若带 we_data（generate_
    roster_equip 从名册拷入）则覆盖表默认——支持同名特效个体化；否则用表权威值。
    表缺失 key → 空 dict（handler 用自身缺省兜底，兼容极端老档/测试手工 key）。
    """
    # 1) 装备实例 we_data 覆盖层
    for item in (player.get("equipment") or {}).values():
        if not item:
            continue
        if item.get("weapon_effect") == key:
            wd = item.get("we_data")
            if isinstance(wd, dict):
                merged = _we_defaults(key)
                merged.update(wd)
                return merged
    # 2) 数据层参数表权威默认
    return _we_defaults(key)


def has_effect(battle, player, key: str) -> bool:
    """当前玩家是否装备了指定特效（单查）。"""
    return key in weapon_effect_ids(battle, player)


def _pstats(battle, player) -> dict:
    """玩家实时面板（特效需要攻击/魔攻/速度等）。"""
    try:
        return battle._player_stats(player)
    except Exception:
        return {}


def _estats(battle) -> dict:
    """敌方实时面板。"""
    try:
        return battle._enemy_stats()
    except Exception:
        return {}


def _true_dmg(battle, base: int, logs, source: str = "✨"):
    """真实伤害（无视防御），直接扣血，不打醒睡眠。"""
    dmg = max(1, int(base))
    battle._deal_damage(dmg, logs, wake_sleep=False)
    logs.append(f"{source} 造成 {dmg} 点真实伤害！")
    return dmg


def _extra_phys(battle, atk_pct: float, logs, ignore_def: bool = False, source: str = "💥") -> int:
    """追加物理伤害：atk × atk_pct，可选择无视防御。"""
    st = _pstats(battle, battle.player)
    atk = int(st.get("atk", 0) or 0)
    if ignore_def:
        dmg = max(1, int(atk * atk_pct))
    else:
        est = _estats(battle)
        from ..engine import calc_damage
        dmg = max(1, calc_damage(int(atk * atk_pct), est.get("def", 0)))
    if dmg > 0:
        battle._deal_damage(dmg, logs)
        logs.append(f"{source} 追加 {dmg} 点伤害！")
    return dmg


def _extra_magi(battle, matk_pct: float, logs, source: str = "🔮") -> int:
    """追加奥术/魔法伤害：matk × matk_pct。"""
    st = _pstats(battle, battle.player)
    matk = int(st.get("matk", 0) or 0)
    est = _estats(battle)
    from ..engine import calc_damage
    dmg = max(1, calc_damage(int(matk * matk_pct), est.get("mdef", 0)))
    if dmg > 0:
        battle._deal_damage(dmg, logs)
        logs.append(f"{source} 溅射 {dmg} 点奥术伤害！")
    return dmg


def _slow_enemy(battle, turns: int, pct: float = 0.40, logs=None):
    """减速敌人：e_buffs spd_down + _spd_down_pct。"""
    battle._actor_buffs(battle._hit_tgt())["spd_down"] = max(battle._actor_buffs(battle._hit_tgt()).get("spd_down", 0), turns)
    battle._actor_buffs(battle._hit_tgt())["_spd_down_pct"] = max(float(battle._actor_buffs(battle._hit_tgt()).get("_spd_down_pct", 0) or 0), pct)
    if logs is not None:
        logs.append(f"❄️ 敌人减速 {int(pct * 100)}%（{turns} 刻）！")


def _freeze_enemy(battle, logs, turns: int = 1, boss_slow: int = 2, source: str = "❄️"):
    """冻结敌人（Boss 免疫退化减速）。"""
    e = battle.enemy or {}
    is_boss = bool(e.get("role") == "boss" or e.get("is_boss") or e.get("boss"))
    if is_boss:
        _slow_enemy(battle, boss_slow, 0.40, logs)
        logs.append(f"{source} Boss 免疫冻结，退化为减速！")
        return False
    battle._actor_buffs(battle._hit_tgt())["freeze"] = max(battle._actor_buffs(battle._hit_tgt()).get("freeze", 0), turns)
    logs.append(f"{source} 敌人被冻结 {turns} 刻！")
    return True


def _apply_dot(battle, key: str, stacks: int, pct: float, turns: int, logs, source: str = "🩸"):
    """给敌人挂 DOT（毒/灼烧/流血/败血），mult 统一 1.0。"""
    deb = battle.enemy.setdefault("debuffs", {})
    cur = deb.get(key) or {"n": 0, "mult": 1.0}
    cur["n"] = min(int(cur.get("n", 0) or 0) + stacks, stacks)
    cur["pct"] = pct
    cur["turns"] = max(int(cur.get("turns", 0) or 0), turns)
    deb[key] = cur
    logs.append(f"{source} 目标被施加 {key}！（{cur['n']} 层，每刻 {int(pct * 100)}% 最大生命，{turns} 刻）")


def _heal_player(battle, player, amount: int, logs, source: str = "💚"):
    """治疗玩家（clamp 到 max_hp，v180E 统一走 _heal_actor——吃 target 禁疗/受疗）。"""
    if amount <= 0:
        return 0
    before = player.get("hp", 0)
    battle._heal_actor(player, amount, logs)
    healed = player["hp"] - before
    if healed > 0:
        logs.append(f"{source} 回复 {healed} 点生命！")
    return healed


def _boss_enemy(e: dict) -> bool:
    """是否 Boss 级目标。"""
    return bool(e.get("role") == "boss" or e.get("is_boss") or e.get("boss"))


def _hp_ratio(battle, unit: dict | None = None) -> float:
    u = unit or battle.enemy or {}
    return float(u.get("hp", 0)) / max(1, u.get("max_hp", 1) or 1)


# ---------------------------------------------------------------- 注册表

WEAPON_EFFECTS = {}  # key → {event: fn}（同一特效可注册多个触发时机）


def register(event_or_key: str, event: str | None = None):
    """注册装饰器：支持两种用法——
    - @register("event")：key = fn.__name__ 去掉 _we_ 前缀
    - @register("key", "event")：显式指定注册 key（同装备 weapon_effect 值）
    同一 key 可注册多个事件（不同函数），proc 按事件分发。
    """
    def deco(fn):
        key = fn.__name__
        if key.startswith("_we_"):
            key = key[4:]
        ev = event_or_key if event is None else event
        if event is not None:
            key = event_or_key
        WEAPON_EFFECTS.setdefault(key, {})[ev] = fn
        return fn
    return deco


# ---- v181.P2C-C2：族执行器注册表（试点 3 族；其余 10 族 C3+ 逐批迁入） ----
# 设计（docs/REFACTOR_P2C_weapon_executors.md §4.1/§4.3 方案 A）：保留 WEAPON_EFFECTS
# 注册表（测试/快照兼容），proc() 分发器优先走族执行器（key→family 由数据表读）。
# 族执行器 = 参数化机制族（仿 affix_effects.SET_PROC_TYPES），数值全读 effect_data 表，
# 代码零默认值。首批：proc_dot/proc_reflect(纯反伤)/proc_heal(amp) 3 族 10 key。
_WE_EXECUTORS = None  # 延迟加载族执行器模块（防 data→core 装配期循环）


def _we_executors() -> dict:
    """延迟 import 族执行器注册表。"""
    global _WE_EXECUTORS
    if _WE_EXECUTORS is None:
        try:
            from ._we_executors import WE_EXECUTORS as _M
            _WE_EXECUTORS = _M
        except Exception:
            _WE_EXECUTORS = {}
    return _WE_EXECUTORS


# C2 族路由白名单：仅当 key 的 family 命中以下族（且执行器存在）才走族分发。
# 其余 family（proc_shield/proc_control/proc_stack/...）未迁移 → 走旧 handler（C3+ 逐批迁）。
# ⚠️ 白名单 = 安全阀：即使表 family 被误标，也绝不把未迁移族 key 导去不存在的执行器。
# ⚠️ C2 只迁移"族内同构子段"——proc_heal 只收 heal_amp 4 key（vital/holy/echo/novice_regen），
#    同 family 的 regen/回蓝 key（guard_regen/dawn_regen/undying_band/novice_dawn_mana）未迁
#    → 不进白名单仍走旧 handler（C4+ 收 regen/mp 段时再入）；proc_reflect 只收纯反伤 2 key
#    （thorn/retribution），带附赠的 iron_echo/dragon_spine_mail/ember_bulwark 同 family 未迁
#    → 同样不进白名单（C4 收附赠段）。proc_dot 4 key 全同构全迁。
# key→族精确路由表（C2 已迁移子段；key 未在此表 = 未迁移走旧 handler）。
_WE_EXEC_KEYS = {
    "smith_blaze_wound": "proc_dot",
    "rong_lu_yu_wen": "proc_dot",
    "ember_burn": "proc_dot",
    "blood_trace": "proc_dot",
    "thorn_armor": "proc_reflect",
    "retribution_ring": "proc_reflect",
    "vital_band": "proc_heal",
    "holy_radiance_mail": "proc_heal",
    "echo_band": "proc_heal",
    "novice_regen_heal": "proc_heal",
    # C5 proc_control 控制族 9 key（全量迁移，全走 e_buffs/_freeze_enemy 共享动作）
    "frost_ring": "proc_control",
    "holy_judgment_field": "proc_control",
    "everfrost_domain": "proc_control",
    "everfrost_scepter": "proc_control",
    "frost_crown": "proc_control",
    "holy_word_bind": "proc_control",
    "time_freeze": "proc_control",
    "randuin_weary": "proc_control",
    "ice_vein": "proc_control",
    # C3：proc_shield 护盾族 10 key（starlight_bulwark/eclipse_crown/sentinel_aegis/
    # deeprock_aegis/bedrock_crown/firmament_crown/gargoyle_heart/echo_bless/
    # atonement_shield/endless_radiance）——事件 battle_start/taken/threshold/skill_hit/heal
    "starlight_bulwark": "proc_shield",
    "eclipse_crown": "proc_shield",
    "sentinel_aegis": "proc_shield",
    "deeprock_aegis": "proc_shield",
    "bedrock_crown": "proc_shield",
    "firmament_crown": "proc_shield",
    "gargoyle_heart": "proc_shield",
    "echo_bless": "proc_shield",
    "atonement_shield": "proc_shield",
    "endless_radiance": "proc_shield",
    # C8：proc_passive_mult 被动乘区族 4 key（twilight_execute/star_slayer_edge/arcane_firmament/
    # combo_end——passive 消费段 + 双事件生产段 battle_start(奥术置标)/hit(连击置标)整体迁移；
    # 事件经分发器 event 形参传入执行器内区分：event=passive 走消费，battle_start/hit 走置标）
    "twilight_execute": "proc_passive_mult",
    "star_slayer_edge": "proc_passive_mult",
    "arcane_firmament": "proc_passive_mult",
    "combo_end": "proc_passive_mult",
    # C8：proc_stack 叠层族 7 key（rune_amp/sage_amp/eternal_codex/time_staff/thunder_weave/
    # wind_mark/novice_hunt_combo——生产段 skill_cast/hit/turn_start 叠层 + passive 乘区消费段
    # 整体迁移；wind_mark/novice_hunt_combo 无 passive 段，仅叠层写槽——面板/连击消费在
    # _player_stats/battle 直读点属 C6 后续收，槽键不变行为零变化）
    "rune_amp": "proc_stack",
    "sage_amp": "proc_stack",
    "eternal_codex": "proc_stack",
    "time_staff": "proc_stack",
    "thunder_weave": "proc_stack",
    "wind_mark": "proc_stack",
    "novice_hunt_combo": "proc_stack",
    # C4：proc_extra_dmg 直伤追击族 11 key（splash_magi 3 = afterglow_splash/spellblade_echo/
    # annihilation_echo；extra_phys = wind_split；extra_phys_pene = phantom_barrage；
    # extra_phys_oncrit = endless_blade；true_dmg_nth 3 = hunter_open/siren_fang/star_pierce；
    # curhp_dmg_heal = soul_eater；lifesteal = novice_lifesteal）——事件 hit/skill_hit 全量迁移，
    # mode 由数据表分发（_we_exec_extra_dmg），共享动作/计数槽键读表字段
    "afterglow_splash": "proc_extra_dmg",
    "spellblade_echo": "proc_extra_dmg",
    "annihilation_echo": "proc_extra_dmg",
    "wind_split": "proc_extra_dmg",
    "phantom_barrage": "proc_extra_dmg",
    "endless_blade": "proc_extra_dmg",
    "hunter_open": "proc_extra_dmg",
    "siren_fang": "proc_extra_dmg",
    "star_pierce": "proc_extra_dmg",
    "soul_eater": "proc_extra_dmg",
    "novice_lifesteal": "proc_extra_dmg",
    # C6：proc_buff 增益族 7 key（gale_step 家族 5 key 同 buff_key=gale_step 共享键 + 新手翠风
    # novice_wind_spd hit 自加速 + 深渊屏障 abyss_barrier battle_start maxhp 永久加成）——
    # 事件 battle_start（gale 5 + abyss）/ hit（novice_wind_spd）由分发器按注册事件集匹配；
    # 面板数值消费（_player_stats 直读 gale_step_pct/层数）C6 同批改走执行器查询 API
    "gale_step": "proc_buff",
    "swift_boots": "proc_buff",
    "deadman_stride": "proc_buff",
    "temple_stride": "proc_buff",
    "void_stride": "proc_buff",
    "novice_wind_spd": "proc_buff",
    "abyss_barrier": "proc_buff",
    # C7：proc_next_atk_mark 下次攻击标记族 5 key（trinity_rhythm/mountain_break/oath_blade/
    # novice_spark_followup/dusk_blade——skill_hit 置标/novice skill_cast 置 stacks/kill 潜行置标，
    # passive 消费段整体迁移；trinity/mountain/retort 的 ctx.attack 门 battle 恒不传=空转旧语义
    # 保留；oath/dusk passive 消费在 battle passive ctx 无 attack 键下本也不触发——真正消费 =
    # battle 直读标记键，C7 一并收编排层直读点）
    "trinity_rhythm": "proc_next_atk_mark",
    "mountain_break": "proc_next_atk_mark",
    "oath_blade": "proc_next_atk_mark",
    "novice_spark_followup": "proc_next_atk_mark",
    "dusk_blade": "proc_next_atk_mark",
    # C7：proc_retort_mark 反击标记族 4 key（gargoyle_retort/titan_retort/ranger_retort taken 置
    # we_retort max；guardian_will taken chance → e_buffs 弱化。retort passive 消费 ctx.attack 门
    # battle 恒不传=空转旧语义保留）
    "gargoyle_retort": "proc_retort_mark",
    "titan_retort": "proc_retort_mark",
    "ranger_retort": "proc_retort_mark",
    "guardian_will": "proc_retort_mark",
    # C9：proc_dr_revive 保命族 2 key（undying_will battle_start 登记 + threshold 免死回血；
    # death_dance_armor passive taken 减伤——battle 编排层 _post_hp_lethal 免死回拉 hp_pct
    # 消费点 C9 同批改读表 hp_pct/immune_key；旧 handler 保留不删 C10 清死代码）
    "undying_will": "proc_dr_revive",
    "death_dance_armor": "proc_dr_revive",
    # C9：proc_special 特殊族 3 key（death_dance battle_start 初始化池 + turn_start 结算 pay_pct——
    # 池填充 dmg×pool_pct 0.35 在 battle._post_hp_lethal 硬编码，C9 改读表 pool_pct/pool_key；
    # novice_first_turn_guard/dodge battle_start 置首刻标记——battle _mitigate_chain/_roll_dodge
    # 消费点 C9 改读表 mark_key/reduce_pct/dodge_pct）
    "death_dance": "proc_special",
    "novice_first_turn_guard": "proc_special",
    "novice_first_turn_dodge": "proc_special",
    # C10：收尾族 proc_aux 7 key（79=72+7 全量路由收官——旧 handler 死代码删除前先补齐）：
    # proc_heal regen 3 = guard_regen/dawn_regen/undying_band（turn_start 每刻回血——C2 白名单
    # 时点仅迁 heal_amp 段，regen 段留此收尾）；proc_heal mp 1 = novice_dawn_mana（skill_cast
    # 首次回蓝 used_key 门）；proc_reflect 带附赠 3 = iron_echo/dragon_spine_mail/ember_bulwark
    # （taken 反伤+回血/禁疗/叠灼烧——C2 只迁纯反伤 2 key，附赠段收尾补齐）
    "guard_regen": "proc_aux",
    "dawn_regen": "proc_aux",
    "undying_band": "proc_aux",
    "novice_dawn_mana": "proc_aux",
    "iron_echo": "proc_aux",
    "dragon_spine_mail": "proc_aux",
    "ember_bulwark": "proc_aux",
}
# C10：key → 注册事件集静态表（等价旧 @register 事件集——逐 key 由旧 handler AST 提取固化；
# 旧 handler 删净后 WEAPON_EFFECTS 恒空，分发器事件匹配改查本表。行为零变化）
_WE_KEY_EVENTS = {
    "smith_blaze_wound": ("hit",), "rong_lu_yu_wen": ("hit",), "ember_burn": ("skill_hit",),
    "blood_trace": ("hit",), "thorn_armor": ("taken",), "retribution_ring": ("taken",),
    "vital_band": ("heal",), "holy_radiance_mail": ("heal",), "echo_band": ("heal",),
    "novice_regen_heal": ("heal",), "frost_ring": ("hit",), "holy_judgment_field": ("hit",),
    "everfrost_domain": ("skill_hit",), "everfrost_scepter": ("skill_hit",),
    "frost_crown": ("taken",), "holy_word_bind": ("heal",), "time_freeze": ("threshold",),
    "randuin_weary": ("enemy_act",), "ice_vein": ("enemy_act",),
    "starlight_bulwark": ("battle_start",), "eclipse_crown": ("battle_start",),
    "sentinel_aegis": ("taken",), "deeprock_aegis": ("taken",),
    "bedrock_crown": ("threshold",), "firmament_crown": ("threshold",),
    "gargoyle_heart": ("threshold",), "echo_bless": ("heal",), "atonement_shield": ("heal",),
    "endless_radiance": ("skill_hit",),
    "twilight_execute": ("passive",), "star_slayer_edge": ("passive",),
    "arcane_firmament": ("battle_start", "passive"), "combo_end": ("hit", "passive"),
    "rune_amp": ("skill_cast", "passive"), "sage_amp": ("skill_cast", "passive"),
    "eternal_codex": ("skill_cast", "passive"), "time_staff": ("turn_start", "passive"),
    "thunder_weave": ("hit", "passive"), "wind_mark": ("hit",),
    "novice_hunt_combo": ("hit",),
    "afterglow_splash": ("skill_hit",), "spellblade_echo": ("skill_hit",),
    "annihilation_echo": ("skill_hit",), "wind_split": ("hit",),
    "phantom_barrage": ("hit",), "endless_blade": ("skill_hit",),
    "hunter_open": ("hit",), "siren_fang": ("hit",), "star_pierce": ("hit",),
    "soul_eater": ("hit",), "novice_lifesteal": ("hit",),
    "gale_step": ("battle_start",), "swift_boots": ("battle_start",),
    "deadman_stride": ("battle_start",), "temple_stride": ("battle_start",),
    "void_stride": ("battle_start",), "novice_wind_spd": ("hit",),
    "abyss_barrier": ("battle_start",),
    "trinity_rhythm": ("skill_hit", "passive"), "mountain_break": ("skill_hit", "passive"),
    "oath_blade": ("skill_hit", "passive"), "novice_spark_followup": ("skill_cast",),
    "dusk_blade": ("kill", "passive"),
    "gargoyle_retort": ("taken", "passive"), "titan_retort": ("taken", "passive"),
    "ranger_retort": ("taken", "passive"), "guardian_will": ("taken",),
    "undying_will": ("battle_start", "threshold"), "death_dance_armor": ("passive",),
    "death_dance": ("battle_start", "turn_start"),
    "novice_first_turn_guard": ("battle_start",), "novice_first_turn_dodge": ("battle_start",),
    # C10 proc_aux 收尾 7 key（事件同旧 handler 注册）
    "guard_regen": ("turn_start",), "dawn_regen": ("turn_start",),
    "undying_band": ("turn_start",), "novice_dawn_mana": ("skill_cast",),
    "iron_echo": ("taken",), "dragon_spine_mail": ("taken",), "ember_bulwark": ("taken",),
}
# 族默认事件表（key 未显式声明 event 时按族）：proc_dot 主事件 hit/skill_hit，
# proc_reflect→taken、proc_heal amp→heal。分发器按"key 注册事件集"匹配事件后再调执行器
# （与旧 proc 逐 key 同事件语义——只有该 key 注册了当前 event 才触发）。
def _we_key_event_family(key: str, event: str) -> str | None:
    """返回 key 在当前 event 下应走的执行器族；不匹配返回 None（走旧 handler）。

    语义 = 旧 WEAPON_EFFECTS[key][event] 存在性：族内 key 的事件集 = 原 handler 注册事件
    （proc_dot: hit/skill_hit 按 key；proc_reflect: taken；proc_heal amp: heal）。
    """
    fam = _WE_EXEC_KEYS.get(key)
    if not fam:
        return None
    # C10：旧 handler 删净后 WEAPON_EFFECTS 恒空，不能再当事件集来源——改查静态注册事件表
    # （等价旧 @register 事件集；C10 由 AST 逐 key 提取固化，行为零变化）。
    evset = _WE_KEY_EVENTS.get(key)
    if not evset or event not in evset:
        return None
    return fam


def proc(battle, player, event: str, ctx: dict | None = None, logs: list | None = None):
    """统一分发：遍历已装备特效，事件匹配则调用 handler。

    v181.P2C-C2：对已族化 key（key∈_WE_EXEC_KEYS 精确路由 + 当前事件在该 key 注册事件集内）
    走族执行器（纯事件内替换，行为零变化——执行器与旧 handler 逐语句等价）；
    未族化 key 保持旧 WEAPON_EFFECTS 逐 key 分发（C3+ 逐批迁）。
    ctx 可为 None（默认 {}）；logs 为 None 时内部建 list（battle_start 等无声场景）。
    """
    if logs is None:
        logs = []
    ctx = ctx or {}
    _execs = _we_executors()
    for key in weapon_effect_ids(battle, player):
        entry = WEAPON_EFFECTS.get(key)
        fn = None
        # v181.P2C-C2：key 命中 C2 精确路由 + 当前事件在该 key 注册事件集内 → 走族执行器
        fam = _we_key_event_family(key, event)
        if fam:
            _ex = _execs.get(fam)
            if _ex is not None:
                # 族执行器签名 (battle, player, ctx, logs, wd, key, event)；异常静默吞（同旧语义）。
                try:
                    wd = effect_data(battle, player, key)
                    _ex(battle, player, ctx, logs, wd, key, event)
                except Exception:
                    pass
                continue
        if not entry:
            continue
        fn = entry.get(event)
        if not fn:
            continue
        try:
            fn(battle, player, ctx, logs)
        except Exception:
            # 特效失败不影响战斗主流程（日志静默，主流程兜底）
            pass
    return logs


# ================================================================
# C10 收尾：旧 handler 死代码已删除（v181.P2C-C10）——79 key 全量路由进族执行器
# （_WE_EXEC_KEYS 72+7，含 C10 proc_aux 收尾族），旧 @register 注册体不再保留；
# WEAPON_EFFECTS 保持空 dict（测试快照兼容——proc() 族分发不依赖注册表内容）。
# ================================================================
