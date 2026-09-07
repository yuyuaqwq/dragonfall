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
    battle.e_buffs["spd_down"] = max(battle.e_buffs.get("spd_down", 0), turns)
    battle.e_buffs["_spd_down_pct"] = max(float(battle.e_buffs.get("_spd_down_pct", 0) or 0), pct)
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
    battle.e_buffs["freeze"] = max(battle.e_buffs.get("freeze", 0), turns)
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
    entry = WEAPON_EFFECTS.get(key)
    if not entry or event not in entry:
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
                # 族执行器签名 (battle, player, ctx, logs, wd, key)；异常静默吞（同旧语义）。
                try:
                    wd = effect_data(battle, player, key)
                    _ex(battle, player, ctx, logs, wd, key)
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
# 一、战斗开始特效（battle_start）
# ================================================================

@register("battle_start")
def _we_starlight_bulwark(battle, player, ctx, logs):
    """星辉壁垒（哨兵短剑）：开战 10% 最大生命护盾，每 5 刻刷新。"""
    wd = effect_data(battle, player, "starlight_bulwark")
    if not has_effect(battle, player, "starlight_bulwark"):
        return
    battle._add_shield("we_starlight", int(player.get("max_hp", 100) * float(wd.get("shield_hp_pct", 0.10))), 3)
    # v152 时刻制：we_starlight_next 存 ready_at（now + 5×ACT_TICK）
    player.setdefault('eff', {})["we_starlight_next"] = battle._now + int(wd.get("refresh_turns", 5)) * ACT_TICK
    logs.append("✨ 星辉壁垒：战斗开始获得 10% 最大生命护盾！")


@register("battle_start")
def _we_gale_step(battle, player, ctx, logs):
    """疾风步（疾风轻靴）：开战获得 1 层疾风（速度+15%，3 刻）。"""
    wd = effect_data(battle, player, "gale_step")
    if not has_effect(battle, player, "gale_step"):
        return
    player.setdefault('buffs', {})["gale_step"] = max(player.setdefault('buffs', {}).get("gale_step", 0), int(wd.get("turns", 3)))
    player.setdefault('eff', {})["gale_step_pct"] = max(float(player.setdefault('eff', {}).get("gale_step_pct", 0) or 0), float(wd.get("spd_pct", 0.15)))
    logs.append("🌪️ 疾风步：速度 +15%（3 刻）！")


@register("battle_start")
def _we_swift_boots(battle, player, ctx, logs):
    """迅捷如风（迅捷战靴）：开战获得 1 层疾风（速度+20%，3 刻）。"""
    wd = effect_data(battle, player, "swift_boots")
    if not has_effect(battle, player, "swift_boots"):
        return
    player.setdefault('buffs', {})["gale_step"] = max(player.setdefault('buffs', {}).get("gale_step", 0), int(wd.get("turns", 3)))
    player.setdefault('eff', {})["gale_step_pct"] = max(float(player.setdefault('eff', {}).get("gale_step_pct", 0) or 0), float(wd.get("spd_pct", 0.20)))
    logs.append("🌪️ 迅捷如风：速度 +20%（3 刻）！")


@register("battle_start")
def _we_abyss_barrier(battle, player, ctx, logs):
    """深渊屏障（深渊胸甲）：开战获得深渊屏障，最大生命+8%（持续整场）。"""
    wd = effect_data(battle, player, "abyss_barrier")
    if not has_effect(battle, player, "abyss_barrier"):
        return
    bonus = int(player.get("max_hp", 100) * float(wd.get("max_hp_pct", 0.08)))
    player["max_hp"] = player.get("max_hp", 100) + bonus
    player["hp"] = min(player["max_hp"], player.get("hp", 0) + bonus)
    logs.append(f"🌑 深渊屏障：最大生命 +{bonus}！（持续整场）")


@register("battle_start")
def _we_deadman_stride(battle, player, ctx, logs):
    """亡者疾行（亡者战靴）：开战获得 2 层疾风（速度+15%，4 刻）。"""
    wd = effect_data(battle, player, "deadman_stride")
    if not has_effect(battle, player, "deadman_stride"):
        return
    player.setdefault('buffs', {})["gale_step"] = max(player.setdefault('buffs', {}).get("gale_step", 0), int(wd.get("turns", 4)))
    player.setdefault('eff', {})["gale_step_pct"] = max(float(player.setdefault('eff', {}).get("gale_step_pct", 0) or 0), float(wd.get("spd_pct", 0.15)))
    logs.append("🌪️ 亡者疾行：速度 +15%（4 刻）！")


@register("battle_start")
def _we_temple_stride(battle, player, ctx, logs):
    """圣殿疾行（圣殿战靴）：开战获得 2 层疾风（速度+20%，4 刻）。"""
    wd = effect_data(battle, player, "temple_stride")
    if not has_effect(battle, player, "temple_stride"):
        return
    player.setdefault('buffs', {})["gale_step"] = max(player.setdefault('buffs', {}).get("gale_step", 0), int(wd.get("turns", 4)))
    player.setdefault('eff', {})["gale_step_pct"] = max(float(player.setdefault('eff', {}).get("gale_step_pct", 0) or 0), float(wd.get("spd_pct", 0.20)))
    logs.append("🌪️ 圣殿疾行：速度 +20%（4 刻）！")


@register("battle_start")
def _we_void_stride(battle, player, ctx, logs):
    """虚空疾行（虚空行者之靴）：开战获得 2 层疾风（速度+25%，4 刻）。"""
    wd = effect_data(battle, player, "void_stride")
    if not has_effect(battle, player, "void_stride"):
        return
    player.setdefault('buffs', {})["gale_step"] = max(player.setdefault('buffs', {}).get("gale_step", 0), int(wd.get("turns", 4)))
    player.setdefault('eff', {})["gale_step_pct"] = max(float(player.setdefault('eff', {}).get("gale_step_pct", 0) or 0), float(wd.get("spd_pct", 0.25)))
    logs.append("🌪️ 虚空疾行：速度 +25%（4 刻）！")


@register("battle_start")
def _we_eclipse_crown(battle, player, ctx, logs):
    """蚀月之蚀（蚀月之冠）：开战 15% 生命护盾，持盾时速度+10%，盾破后下一次攻击+15%。"""
    wd = effect_data(battle, player, "eclipse_crown")
    if not has_effect(battle, player, "eclipse_crown"):
        return
    battle._add_shield("we_eclipse", int(player.get("max_hp", 100) * float(wd.get("shield_hp_pct", 0.15))), 99)
    player.setdefault('eff', {})["we_eclipse_active"] = True
    logs.append("🌒 蚀月之蚀：获得 15% 最大生命护盾！")


@register("battle_start")
def _we_arcane_firmament(battle, player, ctx, logs):
    """奥术苍穹（奥术苍穹之冠）：魔攻+15%，技能伤害+10%（常驻被动，开战挂标记）。"""
    wd = effect_data(battle, player, "arcane_firmament")
    if not has_effect(battle, player, "arcane_firmament"):
        return
    player.setdefault('eff', {})["we_arcane_firmament"] = True  # 被动增伤由 passive 分发消费
    logs.append("✨ 奥术苍穹：魔攻 +15%，技能伤害 +10%！")


@register("battle_start")
def _we_undying_will(battle, player, ctx, logs):
    """不灭意志（不灭意志）：每场 1 次，生命低于 20% 时触发，本刻免疫致死伤害并回复 10% 生命。
    开战仅登记可用标记，阈值触发在 threshold 分发。"""
    if not has_effect(battle, player, "undying_will"):
        return
    player.setdefault('eff', {})["we_undying_used"] = False


# ================================================================
# 二、攻击命中后特效（hit）—— 普攻与技能命中共用
# ================================================================

@register("hit")
def _we_wind_mark(battle, player, ctx, logs):
    """风痕（风行短弓）：每次命中 +1 层（上限 4），每层速度 +2%。"""
    wd = effect_data(battle, player, "wind_mark")
    if not has_effect(battle, player, "wind_mark"):
        return
    n = min(int(wd.get("max_stack", 4)), int(player.setdefault('stacks', {}).get("wind_mark", 0) or 0) + 1)
    player.setdefault('stacks', {})["wind_mark"] = n
    logs.append(f"🌬️ 风痕叠加！({n}/4 层，每层速度 +2%)")


@register("hit")
def _we_hunter_open(battle, player, ctx, logs):
    """破绽（猎户铁匕）：每 3 次攻击后，下一次攻击附带 12% 攻击力真伤。"""
    wd = effect_data(battle, player, "hunter_open")
    if not has_effect(battle, player, "hunter_open"):
        return
    n = int(player.setdefault('stacks', {}).get("hunter_cnt", 0) or 0) + 1
    player.setdefault('stacks', {})["hunter_cnt"] = n
    if n >= int(wd.get("count", 3)):
        player.setdefault('stacks', {})["hunter_cnt"] = 0
        st = _pstats(battle, player)
        _true_dmg(battle, st.get("atk", 0) * float(wd.get("atk_pct", 0.12)), logs, source="🗡️ 破绽")


@register("hit")
def _we_smith_blaze_wound(battle, player, ctx, logs):
    """裂伤（锻火铁拳）：命中 20% 使目标 3 刻每刻损 1.5% 最大生命（精英/Boss 1%）。"""
    wd = effect_data(battle, player, "smith_blaze_wound")
    if not has_effect(battle, player, "smith_blaze_wound") or random.random() >= float(wd.get("chance", 0.20)):
        return
    pct = float(wd.get("dot_pct_boss", 0.01)) if _boss_enemy(battle.enemy or {}) else float(wd.get("dot_pct", 0.015))
    _apply_dot(battle, "blaze", 1, pct, int(wd.get("turns", 3)), logs, source="🔥 裂伤")


@register("hit")
def _we_rong_lu_yu_wen(battle, player, ctx, logs):
    """熔炉余温（石炉战锤）：命中 20% 使目标灼烧 3% 最大生命 × 2 刻（精英/Boss 1.5%）。"""
    wd = effect_data(battle, player, "rong_lu_yu_wen")
    if not has_effect(battle, player, "rong_lu_yu_wen") or random.random() >= float(wd.get("chance", 0.20)):
        return
    pct = float(wd.get("dot_pct_boss", 0.015)) if _boss_enemy(battle.enemy or {}) else float(wd.get("dot_pct", 0.03))
    _apply_dot(battle, "burn", 1, pct, int(wd.get("turns", 2)), logs, source="🔥 熔炉余温")


@register("hit")
def _we_frost_ring(battle, player, ctx, logs):
    """霜环（碎冰长弓）：命中 25% 减速 2 刻（速度-40%），已减速则冻结 1 刻。"""
    wd = effect_data(battle, player, "frost_ring")
    if not has_effect(battle, player, "frost_ring") or random.random() >= float(wd.get("chance", 0.25)):
        return
    if battle.e_buffs.get("spd_down"):
        _freeze_enemy(battle, logs, turns=int(wd.get("freeze_turns", 1)), boss_slow=int(wd.get("boss_slow", 2)), source="🧊 霜环")
    else:
        _slow_enemy(battle, int(wd.get("slow_turns", 2)), float(wd.get("slow_pct", 0.40)), logs)


@register("hit")
def _we_blood_trace(battle, player, ctx, logs):
    """败血（血痕双刺）：命中 25% 使目标 4 刻每刻损 2% 当前生命（Boss 1.5%）。"""
    wd = effect_data(battle, player, "blood_trace")
    if not has_effect(battle, player, "blood_trace") or random.random() >= float(wd.get("chance", 0.25)):
        return
    deb = battle.enemy.setdefault("debuffs", {})
    cur = deb.get("blood_trace") or {"n": 0, "mult": 1.0}
    cur["n"] = min(int(cur.get("n", 0) or 0) + 1, 1)
    cur["pct"] = float(wd.get("pct_boss", 0.015)) if _boss_enemy(battle.enemy or {}) else float(wd.get("pct", 0.02))
    cur["turns"] = int(wd.get("turns", 4))
    deb["blood_trace"] = cur
    logs.append("🩸 败血：目标 4 刻内每刻损失当前生命！（对败血目标 +10% 伤害）")


@register("hit")
def _we_wind_split(battle, player, ctx, logs):
    """裂风矢（裂风长弓）：命中 25% 追加一次 50% 攻击力的攻击，优先攻击召唤物。"""
    wd = effect_data(battle, player, "wind_split")
    if not has_effect(battle, player, "wind_split") or random.random() >= float(wd.get("chance", 0.25)):
        return
    _extra_phys(battle, float(wd.get("atk_pct", 0.50)), logs, source="🌪️ 裂风矢")


@register("hit")
def _we_holy_judgment_field(battle, player, ctx, logs):
    """圣裁领域（圣裁重锤）：命中 30% 使目标 2 刻减速 30% 并受治疗 -30%。"""
    wd = effect_data(battle, player, "holy_judgment_field")
    if not has_effect(battle, player, "holy_judgment_field") or random.random() >= float(wd.get("chance", 0.30)):
        return
    _slow_enemy(battle, int(wd.get("slow_turns", 2)), float(wd.get("slow_pct", 0.30)), logs)
    battle.e_buffs["heal_down"] = max(battle.e_buffs.get("heal_down", 0), int(wd.get("heal_down", 2)))
    logs.append("⚖️ 圣裁领域：目标受治疗 -30%（2 刻）！")


@register("hit")
def _we_thunder_weave(battle, player, ctx, logs):
    """雷纹连打（雷纹拳甲）：命中 +1 层雷纹（上限 5），每层 +2% 速度 +1% 攻击力，满层下次技能 +20%。"""
    wd = effect_data(battle, player, "thunder_weave")
    if not has_effect(battle, player, "thunder_weave"):
        return
    n = min(int(wd.get("max_stack", 5)), int(player.setdefault('stacks', {}).get("thunder_weave", 0) or 0) + 1)
    player.setdefault('stacks', {})["thunder_weave"] = n
    logs.append(f"⚡ 雷纹连打！({n}/5 层，每层速度+2% 攻击+1%)")
    if n >= int(wd.get("max_stack", 5)):
        player.setdefault('stacks', {})["thunder_weave"] = 0
        player.setdefault('eff', {})["we_thunder_charge"] = float(wd.get("charge_pct", 0.20))  # 下一次技能 +20%


@register("hit")
def _we_phantom_barrage(battle, player, ctx, logs):
    """幻影连射（幻影长弓）：命中 20% 追加 30% 攻击力幻影矢（无视 50% 防御），每 5 次攻击必触发。"""
    wd = effect_data(battle, player, "phantom_barrage")
    if not has_effect(battle, player, "phantom_barrage"):
        return
    n = int(player.setdefault('stacks', {}).get("phantom_cnt", 0) or 0) + 1
    player.setdefault('stacks', {})["phantom_cnt"] = n
    if random.random() < float(wd.get("chance", 0.20)) or n >= int(wd.get("guarantee", 5)):
        player.setdefault('stacks', {})["phantom_cnt"] = 0
        st = _pstats(battle, player)
        est = _estats(battle)
        from ..engine import calc_damage
        dmg = max(1, calc_damage(int(st.get("atk", 0) * float(wd.get("atk_pct", 0.30))), int(est.get("def", 0) * (1 - float(wd.get("pene_pct", 0.50))))))
        battle._deal_damage(dmg, logs)
        logs.append(f"🌪️ 幻影连射！无视 50% 防御造成 {dmg} 点伤害！")


@register("hit")
def _we_siren_fang(battle, player, ctx, logs):
    """海妖猎杀（海妖之牙）：每第 3 次攻击额外造成 40% 攻击力的无视防御伤害。"""
    wd = effect_data(battle, player, "siren_fang")
    if not has_effect(battle, player, "siren_fang"):
        return
    n = int(player.setdefault('stacks', {}).get("siren_cnt", 0) or 0) + 1
    player.setdefault('stacks', {})["siren_cnt"] = n
    if n >= int(wd.get("count", 3)):
        player.setdefault('stacks', {})["siren_cnt"] = 0
        st = _pstats(battle, player)
        _true_dmg(battle, st.get("atk", 0) * float(wd.get("atk_pct", 0.40)), logs, source="🧜 海妖猎杀")


@register("hit")
def _we_soul_eater(battle, player, ctx, logs):
    """破败之吻（噬魂短刃）：攻击附加目标当前生命 2% 伤害（上限=攻击力 100%），并回复等量生命。"""
    wd = effect_data(battle, player, "soul_eater")
    if not has_effect(battle, player, "soul_eater"):
        return
    e = battle.enemy or {}
    st = _pstats(battle, player)
    cap = max(1, int(st.get("atk", 0) or 0))
    bonus = min(cap, max(1, int(e.get("hp", 0) * float(wd.get("cur_hp_pct", 0.02)))))
    if bonus > 0:
        battle._deal_damage(bonus, logs, wake_sleep=False)
        healed = _heal_player(battle, player, bonus, logs, source="💜 破败之吻")
        logs.append(f"💜 破败之吻：额外 {bonus} 点伤害，回复 {healed} 点生命！")


@register("hit")
def _we_star_pierce(battle, player, ctx, logs):
    """穿星（星陨长弓）：每 4 次攻击后，下一次攻击附带真伤=20% 攻击力+目标已损生命 3%（上限 5%）。"""
    wd = effect_data(battle, player, "star_pierce")
    if not has_effect(battle, player, "star_pierce"):
        return
    n = int(player.setdefault('stacks', {}).get("star_cnt", 0) or 0) + 1
    player.setdefault('stacks', {})["star_cnt"] = n
    if n >= int(wd.get("count", 4)):
        player.setdefault('stacks', {})["star_cnt"] = 0
        st = _pstats(battle, player)
        e = battle.enemy or {}
        base = int(st.get("atk", 0) * float(wd.get("atk_pct", 0.20)))
        lost = int((e.get("max_hp", 0) - e.get("hp", 0)) * float(wd.get("lost_hp_pct", 0.03)))
        cap = int(e.get("max_hp", 1) * float(wd.get("cap_pct", 0.05)))
        bonus = base + min(lost, cap)
        _true_dmg(battle, bonus, logs, source="☄️ 穿星")


@register("hit")
def _we_combo_end(battle, player, ctx, logs):
    """连击终点（夜枭双匕）：本刻连段≥3 时，本次攻击暴伤 +40%（被动判定）。"""
    wd = effect_data(battle, player, "combo_end")
    if not has_effect(battle, player, "combo_end"):
        return
    if battle._combo_active(player):
        player.setdefault('eff', {})["we_combo_end"] = float(wd.get("crit_dmg", 0.40))


# ================================================================
# 三、技能命中后特效（skill_hit）—— 伤害类技能命中后触发
# ================================================================

@register("skill_hit")
def _we_afterglow_splash(battle, player, ctx, logs):
    """余波（见习辉光法杖）：技能命中后 30% 溅射 15% 攻击力奥术伤害。"""
    wd = effect_data(battle, player, "afterglow_splash")
    if not has_effect(battle, player, "afterglow_splash") or random.random() >= float(wd.get("chance", 0.30)):
        return
    _extra_magi(battle, float(wd.get("atk_pct", 0.15)), logs, source="🌅 余波")


@register("skill_hit")
def _we_spellblade_echo(battle, player, ctx, logs):
    """咒刃（回响之刃）：技能命中后追加 25% 攻击力法术溅射伤害。"""
    wd = effect_data(battle, player, "spellblade_echo")
    if not has_effect(battle, player, "spellblade_echo"):
        return
    _extra_magi(battle, float(wd.get("atk_pct", 0.25)), logs, source="🔮 咒刃")


@register("skill_hit")
def _we_annihilation_echo(battle, player, ctx, logs):
    """湮灭回响（湮灭法典法杖）：技能命中后 35% 溅射 30% 攻击力奥术伤害。"""
    wd = effect_data(battle, player, "annihilation_echo")
    if not has_effect(battle, player, "annihilation_echo") or random.random() >= float(wd.get("chance", 0.35)):
        return
    _extra_magi(battle, float(wd.get("atk_pct", 0.30)), logs, source="💥 湮灭回响")


@register("skill_hit")
def _we_ember_burn(battle, player, ctx, logs):
    """烬燃（灰烬拳套）：技能命中后 30% 使目标 3 刻每刻损 1.5% 最大生命（Boss 1%）。"""
    wd = effect_data(battle, player, "ember_burn")
    if not has_effect(battle, player, "ember_burn") or random.random() >= float(wd.get("chance", 0.30)):
        return
    pct = float(wd.get("dot_pct_boss", 0.01)) if _boss_enemy(battle.enemy or {}) else float(wd.get("dot_pct", 0.015))
    _apply_dot(battle, "ember", 1, pct, int(wd.get("turns", 3)), logs, source="🔥 烬燃")


@register("skill_hit")
def _we_everfrost_domain(battle, player, ctx, logs):
    """永冻领域（永霜秘杖）：冰系技能后 30% 使目标冻结 1 刻（Boss 减速 2 刻），冷却 3 刻。"""
    wd = effect_data(battle, player, "everfrost_domain")
    if not has_effect(battle, player, "everfrost_domain"):
        return
    if float(player.setdefault('eff', {}).get("we_everfrost_cd", 0) or 0) > battle._now:
        return
    if random.random() >= float(wd.get("chance", 0.30)):
        return
    _freeze_enemy(battle, logs, turns=int(wd.get("freeze_turns", 1)), boss_slow=int(wd.get("boss_slow", 2)), source="🧊 永冻领域")
    # v152 时刻制：CD 存 ready_at 绝对时刻（now + cd×ACT_TICK）
    player.setdefault('eff', {})["we_everfrost_cd"] = battle._now + int(wd.get("cd", 3)) * ACT_TICK


@register("skill_hit")
def _we_everfrost_scepter(battle, player, ctx, logs):
    """永霜禁锢（永霜权杖）：技能命中后 20% 冻结目标 1 刻（Boss 仅减速）。"""
    wd = effect_data(battle, player, "everfrost_scepter")
    if not has_effect(battle, player, "everfrost_scepter") or random.random() >= float(wd.get("chance", 0.20)):
        return
    _freeze_enemy(battle, logs, turns=int(wd.get("freeze_turns", 1)), boss_slow=int(wd.get("boss_slow", 2)), source="🧊 永霜禁锢")


@register("skill_hit")
def _we_trinity_rhythm(battle, player, ctx, logs):
    """三相律动（奔雷大剑）：技能后下一次普攻 +30% 伤害并附 15% 攻击力雷伤。"""
    wd = effect_data(battle, player, "trinity_rhythm")
    if not has_effect(battle, player, "trinity_rhythm"):
        return
    player.setdefault('eff', {})["we_trinity"] = float(wd.get("atk_pct", 0.30))
    player.setdefault('eff', {})["we_trinity_thunder"] = float(wd.get("thunder_pct", 0.15))


@register("skill_hit")
def _we_mountain_break(battle, player, ctx, logs):
    """破岳（破岳巨剑）：技能后下一次普攻 +25% 伤害，并附带 10% 攻击力物理溅射伤害。"""
    wd = effect_data(battle, player, "mountain_break")
    if not has_effect(battle, player, "mountain_break"):
        return
    player.setdefault('eff', {})["we_mountain"] = float(wd.get("atk_pct", 0.25))


@register("skill_hit")
def _we_oath_blade(battle, player, ctx, logs):
    """咒刃之誓（咒刃之誓）：释放技能后，下一次攻击伤害 +25%（每刻限 1 次）。"""
    wd = effect_data(battle, player, "oath_blade")
    if not has_effect(battle, player, "oath_blade"):
        return
    player.setdefault('eff', {})["we_oath"] = float(wd.get("atk_pct", 0.25))


@register("skill_hit")
def _we_endless_radiance(battle, player, ctx, logs):
    """无尽辉光（奥拉圣剑）：暴伤+25%（常驻），暴击时获得 5% 最大生命护盾（2 刻，冷却 3 刻）。"""
    wd = effect_data(battle, player, "endless_radiance")
    if not has_effect(battle, player, "endless_radiance"):
        return
    if ctx.get("is_crit") and float(player.setdefault('eff', {}).get("we_radiance_cd", 0) or 0) <= battle._now:
        battle._add_shield("we_radiance", int(player.get("max_hp", 100) * float(wd.get("shield_hp_pct", 0.05))), int(wd.get("shield_turns", 2)))
        # v152 时刻制：CD 存 ready_at 绝对时刻
        player.setdefault('eff', {})["we_radiance_cd"] = battle._now + int(wd.get("cd", 3)) * ACT_TICK
        logs.append("🌟 无尽辉光：暴击获得 5% 最大生命护盾！")


@register("skill_hit")
def _we_endless_blade(battle, player, ctx, logs):
    """无尽锋芒（无终之刃）：暴击后追加一次 20% 伤害的追击（每刻限 1 次）。"""
    wd = effect_data(battle, player, "endless_blade")
    if not has_effect(battle, player, "endless_blade"):
        return
    if not ctx.get("is_crit") or player.setdefault('eff', {}).get("we_blade_used"):
        return
    player.setdefault('eff', {})["we_blade_used"] = True
    _extra_phys(battle, float(wd.get("atk_pct", 0.20)), logs, source="⚔️ 无尽锋芒")


# ================================================================
# 四、技能释放后特效（skill_cast）—— 不要求命中，施法计数
# ================================================================

@register("rune_amp", "skill_cast")
def _we_rune_amp_cast(battle, player, ctx, logs):
    """铭文增幅：技能释放即叠层（含治疗/增益技能）。"""
    wd = effect_data(battle, player, "rune_amp")
    if not has_effect(battle, player, "rune_amp"):
        return
    n = min(int(wd.get("max_stack", 5)), int(player.setdefault('stacks', {}).get("rune_amp", 0) or 0) + 1)
    player.setdefault('stacks', {})["rune_amp"] = n
    logs.append(f"📜 铭文增幅！({n}/5 层，下一技能 +{int(n * float(wd.get('dmg_pct_per', 0.02)) * 100)}%)")


@register("sage_amp", "skill_cast")
def _we_sage_amp_cast(battle, player, ctx, logs):
    """秘典增幅：技能释放即计数（含治疗/增益技能）。"""
    wd = effect_data(battle, player, "sage_amp")
    if not has_effect(battle, player, "sage_amp"):
        return
    n = int(player.setdefault('stacks', {}).get("sage_amp", 0) or 0) + 1
    player.setdefault('stacks', {})["sage_amp"] = n
    if n >= int(wd.get("need", 2)):
        player.setdefault('stacks', {})["sage_amp"] = 0
        player.setdefault('eff', {})["we_sage_charge"] = float(wd.get("charge_pct", 0.25))


@register("eternal_codex", "skill_cast")
def _we_eternal_codex_cast(battle, player, ctx, logs):
    """永恒契约：每次施法积 1 层永恒（上限 8）。"""
    wd = effect_data(battle, player, "eternal_codex")
    if not has_effect(battle, player, "eternal_codex"):
        return
    _cap8 = int(wd.get("max_stack", 8))
    n = min(_cap8, int(player.setdefault('stacks', {}).get("eternal_codex", 0) or 0) + 1)
    player.setdefault('stacks', {})["eternal_codex"] = n
    logs.append(f"📖 永恒契约！({n}/{_cap8} 层，每层技能伤害 +{float(wd.get('dmg_pct_per', 0.015)) * 100:.1f}%)")


# ================================================================
# 五、受击时特效（taken）—— 被敌人攻击时触发（在减伤/护盾结算前调用）
# ================================================================

@register("taken")
def _we_sentinel_aegis(battle, player, ctx, logs):
    """哨兵壁垒（哨兵胸甲）：受击 15% 获得护盾（吸收 6+0.5×Lv 点伤害，3 刻），冷却 1 刻。"""
    wd = effect_data(battle, player, "sentinel_aegis")
    if not has_effect(battle, player, "sentinel_aegis"):
        return
    if float(player.setdefault('eff', {}).get("we_sentinel_cd", 0) or 0) > battle._now:
        return
    if random.random() >= float(wd.get("chance", 0.15)):
        return
    lv = int(player.get("level", 1) or 1)
    shield = int(float(wd.get("base", 6)) + float(wd.get("per_lv", 0.5)) * lv)
    battle._add_shield("we_sentinel", shield, int(wd.get("turns", 3)))
    # v152 时刻制：CD 存 ready_at 绝对时刻
    player.setdefault('eff', {})["we_sentinel_cd"] = battle._now + int(wd.get("cd", 1)) * ACT_TICK
    logs.append(f"🛡️ 哨兵壁垒：获得 {shield} 点护盾！（3 刻）")


@register("taken")
def _we_iron_echo(battle, player, ctx, logs):
    """铁壁回响（石心拳套）：受击 20% 反击 40% 伤害，并回复 2% 最大生命。"""
    wd = effect_data(battle, player, "iron_echo")
    if not has_effect(battle, player, "iron_echo") or random.random() >= float(wd.get("chance", 0.20)):
        return
    if battle.enemy.get("hp", 0) <= 0:
        return
    _extra_phys(battle, float(wd.get("reflect_pct", 0.40)), logs, source="🪨 铁壁回响")
    _heal_player(battle, player, int(player.get("max_hp", 100) * float(wd.get("heal_pct", 0.02))), logs, source="💚 铁壁回响")


@register("taken")
def _we_frost_crown(battle, player, ctx, logs):
    """寒霜凝视（寒霜之冠）：受击 10% 使敌人冻结 1 刻（每场最多 2 次）。"""
    wd = effect_data(battle, player, "frost_crown")
    if not has_effect(battle, player, "frost_crown"):
        return
    if int(player.setdefault('eff', {}).get("we_frost_crown_cnt", 0) or 0) >= int(wd.get("max_per_battle", 2)):
        return
    if random.random() >= float(wd.get("chance", 0.10)):
        return
    player.setdefault('eff', {})["we_frost_crown_cnt"] = int(player.setdefault('eff', {}).get("we_frost_crown_cnt", 0) or 0) + 1
    _freeze_enemy(battle, logs, turns=int(wd.get("freeze_turns", 1)), boss_slow=int(wd.get("boss_slow", 2)), source="🧊 寒霜凝视")


@register("taken")
def _we_thorn_armor(battle, player, ctx, logs):
    """荆棘缠绕（荆棘战甲）：受击反弹 15% 所受伤害。"""
    wd = effect_data(battle, player, "thorn_armor")
    if not has_effect(battle, player, "thorn_armor"):
        return
    dmg = int(ctx.get("dmg", 0) or 0)
    rd = max(1, int(dmg * float(wd.get("reflect_pct", 0.15))))
    if battle.enemy.get("hp", 0) > 0 and rd > 0:
        battle._deal_damage(rd, logs)
        logs.append(f"🌵 荆棘缠绕：反弹 {rd} 点伤害！")


@register("taken")
def _we_guardian_will(battle, player, ctx, logs):
    """卫士信念（圣堂卫士护腿）：受击 8% 使敌人下一次攻击伤害 -25%。"""
    wd = effect_data(battle, player, "guardian_will")
    if not has_effect(battle, player, "guardian_will") or random.random() >= float(wd.get("chance", 0.08)):
        return
    battle.e_buffs["mon_atk_down"] = max(battle.e_buffs.get("mon_atk_down", 0), 1)
    battle.e_buffs["_weaken_val"] = max(float(battle.e_buffs.get("_weaken_val", 0) or 0), float(wd.get("weaken", 0.25)))
    logs.append("🛡️ 卫士信念：敌人下一次攻击伤害 -25%！")


@register("taken")
def _we_deeprock_aegis(battle, player, ctx, logs):
    """深岩壁垒（深岩战盔）：受击 10% 获得护盾（吸收 8% 最大生命），冷却 2 刻。"""
    wd = effect_data(battle, player, "deeprock_aegis")
    if not has_effect(battle, player, "deeprock_aegis"):
        return
    if float(player.setdefault('eff', {}).get("we_deeprock_cd", 0) or 0) > battle._now:
        return
    if random.random() >= float(wd.get("chance", 0.10)):
        return
    battle._add_shield("we_deeprock", int(player.get("max_hp", 100) * float(wd.get("shield_pct", 0.08))), 3)
    # v152 时刻制：CD 存 ready_at 绝对时刻
    player.setdefault('eff', {})["we_deeprock_cd"] = battle._now + int(wd.get("cd", 2)) * ACT_TICK
    logs.append("🪨 深岩壁垒：获得护盾！（吸收 8% 最大生命）")


@register("taken")
def _we_gargoyle_retort(battle, player, ctx, logs):
    """石像反击（石像鬼胫甲）：受击后下一次攻击伤害 +30%（1 次）。"""
    wd = effect_data(battle, player, "gargoyle_retort")
    if not has_effect(battle, player, "gargoyle_retort"):
        return
    player.setdefault('eff', {})["we_retort"] = max(float(player.setdefault('eff', {}).get("we_retort", 0) or 0), float(wd.get("next_atk_pct", 0.30)))


@register("taken")
def _we_dragon_spine_mail(battle, player, ctx, logs):
    """龙脊反噬（龙脊鳞甲）：受击 15% 反弹 25% 伤害，并使其重伤（受治疗 -30%，2 刻）。"""
    wd = effect_data(battle, player, "dragon_spine_mail")
    if not has_effect(battle, player, "dragon_spine_mail") or random.random() >= float(wd.get("chance", 0.15)):
        return
    dmg = int(ctx.get("dmg", 0) or 0)
    rd = max(1, int(dmg * float(wd.get("reflect_pct", 0.25))))
    if battle.enemy.get("hp", 0) > 0 and rd > 0:
        battle._deal_damage(rd, logs)
        battle.e_buffs["heal_down"] = max(battle.e_buffs.get("heal_down", 0), int(wd.get("heal_down", 2)))
        logs.append(f"🐉 龙脊反噬：反弹 {rd} 点伤害，并施加重伤！")


@register("taken")
def _we_retribution_ring(battle, player, ctx, logs):
    """复仇之环（反伤之环）：受击 20% 反弹 30% 所受伤害。"""
    wd = effect_data(battle, player, "retribution_ring")
    if not has_effect(battle, player, "retribution_ring") or random.random() >= float(wd.get("chance", 0.20)):
        return
    dmg = int(ctx.get("dmg", 0) or 0)
    rd = max(1, int(dmg * float(wd.get("reflect_pct", 0.30))))
    if battle.enemy.get("hp", 0) > 0 and rd > 0:
        battle._deal_damage(rd, logs)
        logs.append(f"⚔️ 复仇之环：反弹 {rd} 点伤害！")


@register("taken")
def _we_ember_bulwark(battle, player, ctx, logs):
    """烬火燎原（烬火壁垒）：受击时对攻击者造成自身 5% 最大生命的伤害，并叠加 1 层灼烧（每刻限 1 次）。"""
    wd = effect_data(battle, player, "ember_bulwark")
    if not has_effect(battle, player, "ember_bulwark"):
        return
    if player.setdefault('eff', {}).get("we_ember_bulwark_used"):
        return
    player.setdefault('eff', {})["we_ember_bulwark_used"] = True
    dmg = max(1, int(player.get("max_hp", 100) * float(wd.get("max_hp_pct", 0.05))))
    if battle.enemy.get("hp", 0) > 0:
        battle._deal_damage(dmg, logs)
        deb = battle.enemy.setdefault("debuffs", {})
        cur = deb.get("burn") or {"n": 0, "mult": 1.0}
        cur["n"] = min(int(wd.get("burn_cap", 5)), int(cur.get("n", 0) or 0) + int(wd.get("burn_stack", 1)))
        cur["last_tick"] = max(1, int(battle._tick_no()))
        deb["burn"] = cur
        logs.append(f"🔥 烬火燎原：反伤 {dmg} 点并叠加灼烧！")


@register("taken")
def _we_titan_retort(battle, player, ctx, logs):
    """泰坦之怒（泰坦护腿）：受击后下一次攻击伤害 +40%（1 次）。"""
    wd = effect_data(battle, player, "titan_retort")
    if not has_effect(battle, player, "titan_retort"):
        return
    player.setdefault('eff', {})["we_retort"] = max(float(player.setdefault('eff', {}).get("we_retort", 0) or 0), float(wd.get("next_atk_pct", 0.40)))


@register("taken")
def _we_ranger_retort(battle, player, ctx, logs):
    """巡林反击（巡林者护腿）：受击后下一次攻击伤害 +20%（1 次）。"""
    wd = effect_data(battle, player, "ranger_retort")
    if not has_effect(battle, player, "ranger_retort"):
        return
    player.setdefault('eff', {})["we_retort"] = max(float(player.setdefault('eff', {}).get("we_retort", 0) or 0), float(wd.get("next_atk_pct", 0.20)))


# ================================================================
# 六、治疗时特效（heal）—— 治疗结算时触发（回复量加成/溢出转盾）
# ================================================================

@register("heal")
def _we_vital_band(battle, player, ctx, logs):
    """坚毅祝福（铁卫之戒）：治疗时回复量 +15%（仅在治疗加成阶段，溢出转盾阶段跳过）。"""
    wd = effect_data(battle, player, "vital_band")
    if not has_effect(battle, player, "vital_band"):
        return
    if ctx.get("overflow"):
        return
    heal = int(ctx.get("heal", 0) or 0)
    ctx["heal"] = int(heal * (1 + float(wd.get("heal_pct", 0.15))))


@register("heal")
def _we_holy_radiance_mail(battle, player, ctx, logs):
    """圣辉涌动（圣辉胸甲）：治疗时回复量 +20%（仅在治疗加成阶段，溢出转盾阶段跳过）。"""
    wd = effect_data(battle, player, "holy_radiance_mail")
    if not has_effect(battle, player, "holy_radiance_mail"):
        return
    if ctx.get("overflow"):
        return
    heal = int(ctx.get("heal", 0) or 0)
    ctx["heal"] = int(heal * (1 + float(wd.get("heal_pct", 0.20))))


@register("heal")
def _we_echo_band(battle, player, ctx, logs):
    """回响祝福（回响之戒）：治疗时回复量 +25%（仅在治疗加成阶段，溢出转盾阶段跳过）。"""
    wd = effect_data(battle, player, "echo_band")
    if not has_effect(battle, player, "echo_band"):
        return
    if ctx.get("overflow"):
        return
    heal = int(ctx.get("heal", 0) or 0)
    ctx["heal"] = int(heal * (1 + float(wd.get("heal_pct", 0.25))))


@register("heal")
def _we_echo_bless(battle, player, ctx, logs):
    """回响祝福（圣木权杖）：治疗溢出时 30% 转化为护盾（上限 10% 最大生命）。"""
    wd = effect_data(battle, player, "echo_bless")
    if not has_effect(battle, player, "echo_bless"):
        return
    overflow = int(ctx.get("overflow", 0) or 0)
    if overflow <= 0:
        return
    cap = int(player.get("max_hp", 100) * float(wd.get("cap_hp_pct", 0.10)))
    shield = min(cap, int(overflow * float(wd.get("overflow_pct", 0.30))))
    if shield > 0:
        battle._add_shield("we_echo_bless", shield, 3)
        logs.append(f"🌿 回响祝福：治疗溢出转化为 {shield} 点护盾！")


@register("heal")
def _we_atonement_shield(battle, player, ctx, logs):
    """赎罪之盾（赎罪圣杖）：治疗溢出转化为护盾（上限 15% 最大生命），持盾时受击伤害 -10%。"""
    wd = effect_data(battle, player, "atonement_shield")
    if not has_effect(battle, player, "atonement_shield"):
        return
    overflow = int(ctx.get("overflow", 0) or 0)
    if overflow <= 0:
        return
    cap = int(player.get("max_hp", 100) * float(wd.get("cap_hp_pct", 0.15)))
    shield = min(cap, overflow)
    if shield > 0:
        battle._add_shield("we_atonement", shield, 3)
        player.setdefault('eff', {})["we_atonement_active"] = True
        logs.append(f"⚖️ 赎罪之盾：治疗溢出转化为 {shield} 点护盾！")


@register("heal")
def _we_holy_word_bind(battle, player, ctx, logs):
    """圣言禁锢（圣辉权杖）：治疗技能后 20% 使敌人禁锢 1 刻（Boss 免疫，退化为减速）。
    在治疗加成阶段触发一次（不重复）。"""
    wd = effect_data(battle, player, "holy_word_bind")
    if not has_effect(battle, player, "holy_word_bind"):
        return
    if ctx.get("overflow"):
        return
    if random.random() >= float(wd.get("chance", 0.20)):
        return
    _freeze_enemy(battle, logs, turns=int(wd.get("freeze_turns", 1)), boss_slow=int(wd.get("boss_slow", 2)), source="✨ 圣言禁锢")


# ================================================================
# 七、刻开始特效（turn_start）
# ================================================================

@register("turn_start")
def _we_guard_regen(battle, player, ctx, logs):
    """铁卫意志（铁卫战盔）：每刻开始回复 2% 已损失生命。"""
    wd = effect_data(battle, player, "guard_regen")
    if not has_effect(battle, player, "guard_regen"):
        return
    missing = player.get("max_hp", 1) - player.get("hp", 0)
    if missing > 0:
        heal = max(1, int(missing * float(wd.get("pct", 0.02))))
        _heal_player(battle, player, heal, logs, source="🛡️ 铁卫意志")


@register("turn_start")
def _we_dawn_regen(battle, player, ctx, logs):
    """晨曦微光（晨曦护符）：每刻开始回复 2% 最大生命。"""
    wd = effect_data(battle, player, "dawn_regen")
    if not has_effect(battle, player, "dawn_regen"):
        return
    if player.get("hp", 0) < player.get("max_hp", 1):
        heal = max(1, int(player.get("max_hp", 1) * float(wd.get("pct", 0.02))))
        _heal_player(battle, player, heal, logs, source="🌅 晨曦微光")


@register("turn_start")
def _we_undying_band(battle, player, ctx, logs):
    """不灭微光（不灭之戒）：每刻开始回复 1.5% 最大生命。"""
    wd = effect_data(battle, player, "undying_band")
    if not has_effect(battle, player, "undying_band"):
        return
    if player.get("hp", 0) < player.get("max_hp", 1):
        heal = max(1, int(player.get("max_hp", 1) * float(wd.get("pct", 0.015))))
        _heal_player(battle, player, heal, logs, source="✨ 不灭微光")


@register("death_dance", "battle_start")
def _we_death_dance_start(battle, player, ctx, logs):
    """死亡之舞（死亡之舞）：开战初始化缓伤池。"""
    if not has_effect(battle, player, "death_dance"):
        return
    player.setdefault('eff', {})["we_death_pool"] = float(player.setdefault('eff', {}).get("we_death_pool", 0) or 0)


@register("turn_start")
def _we_death_dance(battle, player, ctx, logs):
    """死亡之舞（死亡之舞）：受击伤害的 35% 转为缓伤，每刻开始结算已积累缓伤的 10%（上限 10 刻）。"""
    wd = effect_data(battle, player, "death_dance")
    if not has_effect(battle, player, "death_dance"):
        return
    pool = float(player.setdefault('eff', {}).get("we_death_pool", 0) or 0)
    if pool <= 0:
        return
    pay = max(1, int(pool * float(wd.get("pay_pct", 0.10))))
    player["hp"] = max(0, player.get("hp", 0) - pay)
    player.setdefault('eff', {})["we_death_pool"] = max(0.0, pool - pay)
    logs.append(f"💀 死亡之舞：缓伤池结算，损失 {pay} 点生命！（剩余 {player.setdefault('eff', {})['we_death_pool']:.0f}）")


@register("turn_start")
def _we_time_staff(battle, player, ctx, logs):
    """岁月流转（岁月之杖）：每刻结束攻击 +1.5%、回复 1.5% 生命（上限 10 层 = +15%）。"""
    wd = effect_data(battle, player, "time_staff")
    if not has_effect(battle, player, "time_staff"):
        return
    n = min(int(wd.get("max_stack", 10)), int(player.setdefault('stacks', {}).get("time_staff", 0) or 0) + 1)
    player.setdefault('stacks', {})["time_staff"] = n
    if player.get("hp", 0) < player.get("max_hp", 1):
        heal = max(1, int(player.get("max_hp", 1) * float(wd.get("per_pct", 0.015))))
        _heal_player(battle, player, heal, logs, source="⏳ 岁月流转")
    logs.append(f"⏳ 岁月流转叠层！({n}/10 层，攻击 +{int(n * float(wd.get('per_pct', 0.015)) * 100)}%)")


# ================================================================
# 八、敌人行动后特效（enemy_act）—— 敌人行动完毕触发
# ================================================================

@register("enemy_act")
def _we_randuin_weary(battle, player, ctx, logs):
    """兰顿倦意（兰顿之戒）：敌人每次行动后，其速度 -6%（最多叠加 3 层）。"""
    wd = effect_data(battle, player, "randuin_weary")
    if not has_effect(battle, player, "randuin_weary"):
        return
    _ms = int(wd.get("max_stack", 3))
    _sp = float(wd.get("spd_down_pct", 0.06))
    n = min(_ms, int(battle.e_buffs.get("_randuin_stack", 0) or 0) + 1)
    battle.e_buffs["_randuin_stack"] = n
    # 速度-6%/层：乘算并入敌方速度面板（_enemy_stats 消费）
    battle.e_buffs["_spd_down_pct"] = max(float(battle.e_buffs.get("_spd_down_pct", 0) or 0), _sp * n)
    logs.append(f"🛡️ 兰顿倦意：敌人速度 -{int(_sp * 100 * n)}%（{n}/{_ms} 层）！")


@register("enemy_act")
def _we_ice_vein(battle, player, ctx, logs):
    """冰脉寒流（冰脉护腿）：敌人每次行动后，其速度 -8%（最多叠加 3 层）。"""
    wd = effect_data(battle, player, "ice_vein")
    if not has_effect(battle, player, "ice_vein"):
        return
    _ms = int(wd.get("max_stack", 3))
    _sp = float(wd.get("spd_down_pct", 0.08))
    n = min(_ms, int(battle.e_buffs.get("_ice_vein_stack", 0) or 0) + 1)
    battle.e_buffs["_ice_vein_stack"] = n
    battle.e_buffs["_spd_down_pct"] = max(float(battle.e_buffs.get("_spd_down_pct", 0) or 0), _sp * n)
    logs.append(f"❄️ 冰脉寒流：敌人速度 -{int(_sp * 100 * n)}%（{n}/{_ms} 层）！")


# ================================================================
# 九、生命阈值特效（threshold）—— 玩家血量降至阈值以下时触发（每场限次）
# ================================================================

@register("threshold")
def _we_time_freeze(battle, player, ctx, logs):
    """时光凝滞（时光沙漏）：每场 1 次，生命降至 30% 以下时触发，跳过敌人下一次行动。"""
    wd = effect_data(battle, player, "time_freeze")
    if not has_effect(battle, player, "time_freeze"):
        return
    if player.setdefault('eff', {}).get("we_time_freeze_used"):
        return
    ratio = float(player.get("hp", 0)) / max(1, player.get("max_hp", 1) or 1)
    if ratio >= float(wd.get("threshold", 0.30)):
        return
    player.setdefault('eff', {})["we_time_freeze_used"] = True
    battle.e_buffs["stun"] = max(battle.e_buffs.get("stun", 0), 1)
    logs.append("⏳ 时光凝滞！敌人被定身，跳过一次行动！")


@register("threshold")
def _we_bedrock_crown(battle, player, ctx, logs):
    """磐石守护（磐石王冠）：每场 1 次，生命低于 25% 时获得护盾（吸收 20% 最大生命，4 刻）。"""
    wd = effect_data(battle, player, "bedrock_crown")
    if not has_effect(battle, player, "bedrock_crown"):
        return
    if player.setdefault('eff', {}).get("we_bedrock_used"):
        return
    ratio = float(player.get("hp", 0)) / max(1, player.get("max_hp", 1) or 1)
    if ratio >= float(wd.get("threshold", 0.25)):
        return
    player.setdefault('eff', {})["we_bedrock_used"] = True
    shield = int(player.get("max_hp", 100) * float(wd.get("shield_hp_pct", 0.20)))
    battle._add_shield("we_bedrock", shield, int(wd.get("turns", 4)))
    logs.append(f"🪨 磐石守护：生命垂危，获得 {shield} 点护盾！（4 刻）")


@register("threshold")
def _we_firmament_crown(battle, player, ctx, logs):
    """苍穹庇护（苍穹之冠）：每场 2 次，生命低于 30% 时获得护盾（吸收 12% 最大生命，3 刻）。"""
    wd = effect_data(battle, player, "firmament_crown")
    if not has_effect(battle, player, "firmament_crown"):
        return
    if int(player.setdefault('eff', {}).get("we_firmament_cnt", 0) or 0) >= int(wd.get("per_battle", 2)):
        return
    ratio = float(player.get("hp", 0)) / max(1, player.get("max_hp", 1) or 1)
    if ratio >= float(wd.get("threshold", 0.30)):
        return
    player.setdefault('eff', {})["we_firmament_cnt"] = int(player.setdefault('eff', {}).get("we_firmament_cnt", 0) or 0) + 1
    shield = int(player.get("max_hp", 100) * float(wd.get("shield_hp_pct", 0.12)))
    battle._add_shield("we_firmament", shield, int(wd.get("turns", 3)))
    logs.append(f"🌌 苍穹庇护：获得 {shield} 点护盾！（{player.setdefault('eff', {})['we_firmament_cnt']}/2 次）")


@register("threshold")
def _we_gargoyle_heart(battle, player, ctx, logs):
    """石像鬼之心（石像鬼之心）：每场 1 次，生命低于 30% 时获得护盾（吸收 25% 最大生命）并回复。"""
    wd = effect_data(battle, player, "gargoyle_heart")
    if not has_effect(battle, player, "gargoyle_heart"):
        return
    if player.setdefault('eff', {}).get("we_gargoyle_used"):
        return
    ratio = float(player.get("hp", 0)) / max(1, player.get("max_hp", 1) or 1)
    if ratio >= float(wd.get("threshold", 0.30)):
        return
    player.setdefault('eff', {})["we_gargoyle_used"] = True
    shield = int(player.get("max_hp", 100) * float(wd.get("shield_hp_pct", 0.25)))
    battle._add_shield("we_gargoyle", shield, int(wd.get("turns", 4)))
    heal = int(player.get("max_hp", 100) * float(wd.get("heal_pct", 0.10)))
    _heal_player(battle, player, heal, logs, source="💎 石像鬼之心")
    logs.append(f"💎 石像鬼之心：获得 {shield} 点护盾并回复 {heal} 点生命！")


@register("undying_will", "threshold")
def _we_undying_will_t(battle, player, ctx, logs):
    """不灭意志（不灭意志）：每场 1 次，生命低于 20% 时触发，本刻免疫致死伤害并回复 10% 生命。"""
    wd = effect_data(battle, player, "undying_will")
    if not has_effect(battle, player, "undying_will"):
        return
    if player.setdefault('eff', {}).get("we_undying_used"):
        return
    ratio = float(player.get("hp", 0)) / max(1, player.get("max_hp", 1) or 1)
    if ratio >= float(wd.get("threshold", 0.20)):
        return
    player.setdefault('eff', {})["we_undying_used"] = True
    player.setdefault('eff', {})["we_undying_immune"] = True  # 本刻免疫致死（_damage_actor 消费）
    heal = int(player.get("max_hp", 100) * float(wd.get("heal_pct", 0.10)))
    _heal_player(battle, player, heal, logs, source="✨ 不灭意志")
    logs.append("✨ 不灭意志：免疫致死伤害！")


# ================================================================
# 十、击杀后特效（kill）
# ================================================================

@register("kill")
def _we_dusk_blade(battle, player, ctx, logs):
    """暮裂潜行（暮裂之刃）：击杀目标后进入潜行，下一次攻击伤害 +30% 且无视闪避（每场 1 次）。"""
    wd = effect_data(battle, player, "dusk_blade")
    if not has_effect(battle, player, "dusk_blade"):
        return
    if player.setdefault('eff', {}).get("we_dusk_used"):
        return
    player.setdefault('eff', {})["we_dusk_used"] = True
    player.setdefault('buffs', {})["stealth"] = max(player.setdefault('buffs', {}).get("stealth", 0), 1)
    player.setdefault('eff', {})["we_dusk_dmg"] = float(wd.get("next_atk_pct", 0.30))
    logs.append("🌒 暮裂潜行：击杀后遁入暗影，下一次攻击 +30% 且无视闪避！")


# ================================================================
# 十一、常驻被动特效（passive）—— 伤害倍率/减伤/暴伤等，在伤害结算时消费
# ================================================================

@register("passive")
def _we_twilight_execute(battle, player, ctx, logs):
    """暮光处决（暮光之刺）：对生命 <40% 的目标 +25% 伤害。"""
    wd = effect_data(battle, player, "twilight_execute")
    if not has_effect(battle, player, "twilight_execute"):
        return
    if _hp_ratio(battle) < float(wd.get("threshold", 0.40)):
        ctx["mult"] = ctx.get("mult", 1.0) * float(wd.get("dmg_mult", 1.25))
        ctx["tags"] = ctx.get("tags", []) + ["🌆暮光处决"]


@register("star_slayer_edge", "passive")
def _we_star_slayer_edge_p(battle, player, ctx, logs):
    """弑星（弑星巨刃）：对生命 >70% 的目标 +15% 伤害（暴伤 +30% 在暴伤消费点）。"""
    wd = effect_data(battle, player, "star_slayer_edge")
    if not has_effect(battle, player, "star_slayer_edge"):
        return
    if _hp_ratio(battle) > float(wd.get("threshold", 0.70)):
        ctx["mult"] = ctx.get("mult", 1.0) * float(wd.get("dmg_mult", 1.15))
        ctx["tags"] = ctx.get("tags", []) + ["⭐弑星"]


@register("arcane_firmament", "passive")
def _we_arcane_firmament_p(battle, player, ctx, logs):
    """奥术苍穹（奥术苍穹之冠）：技能伤害 +10%（魔攻 +15% 在 _player_stats 消费）。"""
    wd = effect_data(battle, player, "arcane_firmament")
    if not has_effect(battle, player, "arcane_firmament"):
        return
    if ctx.get("kind") == "魔法":
        ctx["mult"] = ctx.get("mult", 1.0) * (1 + float(wd.get("skill_dmg_pct", 0.10)))
        ctx["tags"] = ctx.get("tags", []) + ["✨奥术苍穹"]


@register("passive")
def _we_death_dance_armor(battle, player, ctx, logs):
    """亡者之舞（亡舞战铠）：受击伤害 -8%（常驻），被击杀时以 12% 生命复活（每场 1 次）。"""
    wd = effect_data(battle, player, "death_dance_armor")
    if not has_effect(battle, player, "death_dance_armor"):
        return
    if ctx.get("taken"):
        ctx["taken"] = max(1, int(ctx.get("taken", 0) * (1 - float(wd.get("taken_reduce_pct", 0.08)))))


@register("time_staff", "passive")
def _we_time_staff_p(battle, player, ctx, logs):
    """岁月流转（岁月之杖）：攻击 +1.5%/层（上限 10 层 = +15%）。"""
    wd = effect_data(battle, player, "time_staff")
    if not has_effect(battle, player, "time_staff"):
        return
    n = int(player.setdefault('stacks', {}).get("time_staff", 0) or 0)
    if n > 0:
        ctx["mult"] = ctx.get("mult", 1.0) * (1 + float(wd.get("per_pct", 0.015)) * n)
        ctx["tags"] = ctx.get("tags", []) + [f"⏳岁月x{1 + float(wd.get('per_pct', 0.015)) * n:.2f}"]


@register("eternal_codex", "passive")
def _we_eternal_codex_p(battle, player, ctx, logs):
    """永恒契约（永契法典）：每层永恒技能伤害 +1.5%（上限 8 层 = +12%）。"""
    wd = effect_data(battle, player, "eternal_codex")
    if not has_effect(battle, player, "eternal_codex"):
        return
    n = int(player.setdefault('stacks', {}).get("eternal_codex", 0) or 0)
    if n > 0:
        ctx["mult"] = ctx.get("mult", 1.0) * (1 + float(wd.get("per_pct", 0.015)) * n)
        ctx["tags"] = ctx.get("tags", []) + [f"📖永恒x{1 + float(wd.get('per_pct', 0.015)) * n:.2f}"]


@register("rune_amp", "passive")
def _we_rune_amp_p(battle, player, ctx, logs):
    """铭文增幅（秘法典籍之杖）：下一技能伤害 +2%/层（叠层消费后清空）。"""
    wd = effect_data(battle, player, "rune_amp")
    if not has_effect(battle, player, "rune_amp"):
        return
    n = int(player.setdefault('stacks', {}).get("rune_amp", 0) or 0)
    if n > 0:
        ctx["mult"] = ctx.get("mult", 1.0) * (1 + float(wd.get("per_pct", 0.02)) * n)
        ctx["tags"] = ctx.get("tags", []) + [f"📜铭文x{1 + float(wd.get('per_pct', 0.02)) * n:.2f}"]
        player.setdefault('stacks', {})["rune_amp"] = 0


@register("sage_amp", "passive")
def _we_sage_amp_p(battle, player, ctx, logs):
    """秘典增幅（大贤者秘典）：每 2 次技能后下一次技能伤害 +25%。"""
    wd = effect_data(battle, player, "sage_amp")
    if not has_effect(battle, player, "sage_amp"):
        return
    if player.setdefault('eff', {}).get("we_sage_charge"):
        ctx["mult"] = ctx.get("mult", 1.0) * float(player.setdefault('eff', {}).get("we_sage_charge", float(wd.get("charge_pct", 0.25))))
        ctx["tags"] = ctx.get("tags", []) + ["📚秘典x1.25"]
        player.setdefault('eff', {}).pop("we_sage_charge", None)


@register("thunder_weave", "passive")
def _we_thunder_weave_p(battle, player, ctx, logs):
    """雷纹连打（雷纹拳甲）：满层时下一次技能 +20%（叠层被动消费）。"""
    wd = effect_data(battle, player, "thunder_weave")
    if not has_effect(battle, player, "thunder_weave"):
        return
    if player.setdefault('eff', {}).get("we_thunder_charge"):
        ctx["mult"] = ctx.get("mult", 1.0) * float(player.setdefault('eff', {}).get("we_thunder_charge", float(wd.get("charge_pct", 0.20))))
        ctx["tags"] = ctx.get("tags", []) + ["⚡雷纹x1.20"]
        player.setdefault('eff', {}).pop("we_thunder_charge", None)


@register("trinity_rhythm", "passive")
def _we_trinity_p(battle, player, ctx, logs):
    """三相律动（奔雷大剑）：下一次普攻 +30% 伤害（普攻时消费）。"""
    wd = effect_data(battle, player, "trinity_rhythm")
    if not has_effect(battle, player, "trinity_rhythm"):
        return
    if ctx.get("attack") and player.setdefault('eff', {}).get("we_trinity"):
        ctx["mult"] = ctx.get("mult", 1.0) * float(player.setdefault('eff', {}).get("we_trinity", float(wd.get("atk_pct", 0.30))))
        ctx["tags"] = ctx.get("tags", []) + ["⚡三相x1.30"]
        player.setdefault('eff', {}).pop("we_trinity", None)


@register("mountain_break", "passive")
def _we_mountain_p(battle, player, ctx, logs):
    """破岳（破岳巨剑）：下一次普攻 +25% 伤害（普攻时消费）。"""
    wd = effect_data(battle, player, "mountain_break")
    if not has_effect(battle, player, "mountain_break"):
        return
    if ctx.get("attack") and player.setdefault('eff', {}).get("we_mountain"):
        ctx["mult"] = ctx.get("mult", 1.0) * float(player.setdefault('eff', {}).get("we_mountain", float(wd.get("atk_pct", 0.25))))
        ctx["tags"] = ctx.get("tags", []) + ["⛰️破岳x1.25"]
        player.setdefault('eff', {}).pop("we_mountain", None)


@register("oath_blade", "passive")
def _we_oath_p(battle, player, ctx, logs):
    """咒刃之誓（咒刃之誓）：下一次攻击伤害 +25%（每刻限 1 次）。"""
    wd = effect_data(battle, player, "oath_blade")
    if not has_effect(battle, player, "oath_blade"):
        return
    if player.setdefault('eff', {}).get("we_oath"):
        ctx["mult"] = ctx.get("mult", 1.0) * float(player.setdefault('eff', {}).get("we_oath", float(wd.get("atk_pct", 0.25))))
        ctx["tags"] = ctx.get("tags", []) + ["⚔️咒誓x1.25"]
        player.setdefault('eff', {}).pop("we_oath", None)


@register("gargoyle_retort", "passive")
@register("titan_retort", "passive")
@register("ranger_retort", "passive")
def _we_retort_p(battle, player, ctx, logs):
    """受击反击（石像反击/泰坦之怒/巡林反击）：受击后下一次攻击伤害 +%（1 次）。"""
    if not has_effect(battle, player, "gargoyle_retort") and not has_effect(battle, player, "titan_retort") \
            and not has_effect(battle, player, "ranger_retort"):
        return
    wd = effect_data(battle, player, "gargoyle_retort") or effect_data(battle, player, "titan_retort") or effect_data(battle, player, "ranger_retort")
    if ctx.get("attack") and player.setdefault('eff', {}).get("we_retort"):
        mult = float(player.setdefault('eff', {}).get("we_retort", float(wd.get("fallback_pct", 0.20))))
        ctx["mult"] = ctx.get("mult", 1.0) * (1 + mult)
        ctx["tags"] = ctx.get("tags", []) + [f"🛡️反击x{1 + mult:.2f}"]
        player.setdefault('eff', {}).pop("we_retort", None)


@register("dusk_blade", "passive")
def _we_dusk_p(battle, player, ctx, logs):
    """暮裂潜行（暮裂之刃）：潜行中下一次攻击 +30% 且无视闪避。"""
    wd = effect_data(battle, player, "dusk_blade")
    if not has_effect(battle, player, "dusk_blade"):
        return
    if player.setdefault('eff', {}).get("we_dusk_dmg"):
        ctx["mult"] = ctx.get("mult", 1.0) * float(player.setdefault('eff', {}).get("we_dusk_dmg", float(wd.get("atk_pct", 0.30))))
        ctx["tags"] = ctx.get("tags", []) + ["🌒暮裂x1.30"]
        player.setdefault('eff', {}).pop("we_dusk_dmg", None)


@register("combo_end", "passive")
def _we_combo_end_p(battle, player, ctx, logs):
    """连击终点（夜枭双匕）：连段≥3 时本次攻击暴伤 +40%。"""
    wd = effect_data(battle, player, "combo_end")
    if not has_effect(battle, player, "combo_end"):
        return
    if ctx.get("is_crit") and player.setdefault('eff', {}).get("we_combo_end"):
        ctx["crit_dmg"] = ctx.get("crit_dmg", 0) + float(wd.get("crit_dmg", 0.40))
        player.setdefault('eff', {}).pop("we_combo_end", None)


# ================================================================
# 十二、新手特效（novice_*，v140 波4：8 件新手紫装 Lv.10-15 特效消费端）
# 数据层 weapon_effect 已改为字符串 key（equip_add_novice.py），与现有特效同口径。
# 语义见 SA-1 任务卡 v140_sa1_novice_handlers.md；各消费点由主 agent 在 battle.py 接线：
#   - novice_spark_followup   → _player_attack 消费 mech_stacks["novice_spark"]（+10% 后清）
#   - novice_wind_spd         → _player_stats 消费 p_buffs["novice_wind_spd"]（spd×1.05）
#   - novice_first_turn_guard → _damage_actor 消费 p_eff["novice_guard_active"]（round≤1 ×0.90）
#   - novice_first_turn_dodge → 闪避判定消费 p_eff["novice_dodge_active"]（round≤1 闪避乘算 +5%）
# ================================================================

@register("hit")
def _we_novice_lifesteal(battle, player, ctx, logs):
    """吸血（学徒之血刃）：伤害的 5% 转化为生命回复（每击吸血，常驻）。
    hit 事件触发：ctx 有 dmg 用 dmg×pct，否则用面板 atk×pct 近似。"""
    wd = effect_data(battle, player, "novice_lifesteal")
    if not has_effect(battle, player, "novice_lifesteal"):
        return
    dmg = int(ctx.get("dmg", 0) or 0)
    if dmg <= 0:
        st = _pstats(battle, player)
        dmg = int(st.get("atk", 0) or 0)
    heal = int(dmg * float(wd.get("heal_pct", 0.05)))
    _heal_player(battle, player, heal, logs, source="🩸 吸血")


@register("battle_start")
def _we_novice_first_turn_guard(battle, player, ctx, logs):
    """守御（旅人之盾）：每场战斗首刻受击伤害 -10%。
    仅 battle_start 挂标记，减伤由 _damage_actor 消费（round≤1 时 ×0.90）。"""
    wd = effect_data(battle, player, "novice_first_turn_guard")
    if not has_effect(battle, player, "novice_first_turn_guard"):
        return
    player.setdefault('eff', {})["novice_guard_active"] = True
    logs.append("🛡️ 守御：首刻受击伤害 -10%！")


@register("skill_cast")
def _we_novice_spark_followup(battle, player, ctx, logs):
    """星火（星火法杖）：释放技能后，下次普攻伤害 +10%。
    仅挂 mech_stacks 标记，由 _player_attack 消费（读参数表 atk_pct 后清除）。"""
    wd = effect_data(battle, player, "novice_spark_followup")
    if not has_effect(battle, player, "novice_spark_followup"):
        return
    player.setdefault('stacks', {})["novice_spark"] = True
    logs.append("✨ 星火：下次普攻伤害 +10%！")


@register("hit")
def _we_novice_hunt_combo(battle, player, ctx, logs):
    """猎影（猎影之牙）：暴击后，本场战斗连击率 +8%。
    hit 事件里判 ctx["is_crit"]，每暴击 +1 层（上限 5 层 = +40%）。"""
    wd = effect_data(battle, player, "novice_hunt_combo")
    if not has_effect(battle, player, "novice_hunt_combo"):
        return
    if not ctx.get("is_crit"):
        return
    n = min(int(wd.get("max_stack", 5)), int(player.setdefault('stacks', {}).get("novice_combo", 0) or 0) + 1)
    player.setdefault('stacks', {})["novice_combo"] = n
    logs.append(f"🎯 猎影：暴击叠层！（{n}/5 层，每层连击率 +{int(float(wd.get('per_stack', 0.08)) * 100)}%）")


@register("heal")
def _we_novice_regen_heal(battle, player, ctx, logs):
    """庇护（旅人皮甲）：受到的治疗效果 +10%（常驻）。
    heal 事件消费：ctx["heal"] ×1.10（仅在治疗加成阶段，溢出转盾阶段跳过）。"""
    wd = effect_data(battle, player, "novice_regen_heal")
    if not has_effect(battle, player, "novice_regen_heal"):
        return
    if ctx.get("overflow"):
        return
    heal = int(ctx.get("heal", 0) or 0)
    ctx["heal"] = int(heal * (1 + float(wd.get("heal_pct", 0.10))))


@register("hit")
def _we_novice_wind_spd(battle, player, ctx, logs):
    """翠风（翠风之弓）：攻击命中后，自身速度 +5%（持续 2 刻）。
    hit 事件挂 p_buffs 计时，由 _player_stats 消费（spd×1.05）。"""
    wd = effect_data(battle, player, "novice_wind_spd")
    if not has_effect(battle, player, "novice_wind_spd"):
        return
    player.setdefault('buffs', {})["novice_wind_spd"] = max(int(player.setdefault('buffs', {}).get("novice_wind_spd", 0) or 0), int(wd.get("turns", 2)))
    logs.append("🌪️ 翠风：自身速度 +5%（2 刻）！")


@register("battle_start")
def _we_novice_first_turn_dodge(battle, player, ctx, logs):
    """远行（远行兜帽）：每场战斗首刻闪避率 +5%。
    仅 battle_start 挂标记，闪避加成由闪避判定消费（round≤1 时乘算 +5%）。"""
    wd = effect_data(battle, player, "novice_first_turn_dodge")
    if not has_effect(battle, player, "novice_first_turn_dodge"):
        return
    player.setdefault('eff', {})["novice_dodge_active"] = True
    logs.append("💨 远行：首刻闪避率 +5%！")


@register("skill_cast")
def _we_novice_dawn_mana(battle, player, ctx, logs):
    """晨星（晨星吊坠）：每场战斗首次释放技能时回复 10 点魔力。
    skill_cast 事件：novice_mana_used 标记防重复，mp clamp 到 max_mp。"""
    wd = effect_data(battle, player, "novice_dawn_mana")
    if not has_effect(battle, player, "novice_dawn_mana"):
        return
    if player.setdefault('eff', {}).get("novice_mana_used"):
        return
    player.setdefault('eff', {})["novice_mana_used"] = True
    player["mp"] = min(player.get("max_mp", 999), player.get("mp", 0) + int(wd.get("mp", 10)))
    logs.append("🌅 晨星：回复 10 点魔力！")




