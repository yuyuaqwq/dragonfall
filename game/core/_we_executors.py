# -*- coding: utf-8 -*-
"""v181.P2C-C2 武器特效族执行器注册表（试点 3 族）——由 weapon_effects.py proc() 分发消费。

**读表参数、代码零默认值铁律**：所有数值来自 effect_data() 返回的 wd（weapon_effect_data
表权威 + 装备行 we_data 覆盖层）。缺字段 = 无此行为——**绝不补默认值**（C1 已核表值 =
handler 原硬编码值，diff=0，读表安全）。唯一例外：行为控制位（bool/事件存在性）由
wd 中字段存在性决定，handler 里"无条件执行"的族（如 heal_amp 不需要额外开关）直接执行。

签名约定：fn(battle, player, ctx, logs, wd, key) —— 与旧 _we_* handler 同 battle/player/
ctx/logs 对象，wd = effect_data(battle, player, key)，key = 触发装备特效 key（日志兜底用）。
"""

# ---------------------------------------------------------------- 依赖
import random

# ---------------------------------------------------------------- proc_dot（4 key）
# 命中后给敌方挂 DOT（maxhp% / curhp%）。事件 hit/skill_hit 由数据表 family 默认事件表
# 分发（见 weapon_effects.py proc()），执行器本身不关心事件。

def _we_exec_dot(battle, player, ctx, logs, wd, key):
    """DOT 执行器：chance 判定 → 目标 pct 判定（boss/精英 vs 普通）→ 写敌方 debuffs。

    覆盖 smith_blaze_wound/rong_lu_yu_wen/ember_burn（走 _apply_dot 共享动作）与
    blood_trace（当前生命%，直接写 debuffs + 原文案日志）。
    """
    # chance：缺字段（无 chance）= 不触发（无此行为铁律）
    if float(wd.get("chance") or 0) <= 0 or "chance" not in wd:
        return
    if random.random() >= float(wd["chance"]):
        return
    # 目标：battle.enemy（与旧 handler 一致；ctx 不携带目标）
    if not battle.enemy:
        return
    # 延迟取共享动作（weapon_effects 模块已完全加载后才可能调执行器——proc 延迟 import）
    from .weapon_effects import _apply_dot, _boss_enemy
    if key == "blood_trace":
        # 败血：当前生命%（pct_boss 对 Boss/精英），非 _apply_dot maxhp 语义（原 handler 直写）
        deb = battle.enemy.setdefault("debuffs", {})
        cur = deb.get("blood_trace") or {"n": 0, "mult": 1.0}
        cur["n"] = min(int(cur.get("n", 0) or 0) + 1, 1)
        cur["pct"] = float(wd["pct_boss"]) if _boss_enemy(battle.enemy) else float(wd["pct"])
        cur["turns"] = int(wd["turns"])
        deb["blood_trace"] = cur
        logs.append("🩸 败血：目标 4 刻内每刻损失当前生命！（对败血目标 +10% 伤害）")
        return
    # smith_blaze_wound/rong_lu_yu_wen/ember_burn：_apply_dot（maxhp%）
    pct = float(wd["dot_pct_boss"]) if _boss_enemy(battle.enemy) else float(wd["dot_pct"])
    _apply_dot(battle, wd["dot_key"], 1, pct, int(wd["turns"]), logs, source=_DOT_SOURCE[key])


# ---------------------------------------------------------------- proc_reflect（2 key）
# 纯反伤段（thorn_armor 无条件 / retribution_ring chance）——C2 只收这 2 key，
# iron_echo/dragon_spine_mail/ember_bulwark 带附赠（heal/heal_down/burn）留 C4 收。

def _we_exec_reflect(battle, player, ctx, logs, wd, key):
    """反伤执行器：chance（缺省=恒触发，thorn_armor 无 chance 字段）→ ctx.dmg×reflect_pct 反弹。

    覆盖 thorn_armor（无条件反 15%）/ retribution_ring（20% 反 30%）。
    """
    # 无条件（无 chance 字段）直接过；有 chance 字段则判定（缺 chance 视为无此行为？——
    # thorn_armor 表无 chance，= 无条件反伤；retribution_ring 有 chance=0.20）
    _ch = wd.get("chance")
    if _ch is not None:
        if float(_ch) <= 0 or random.random() >= float(_ch):
            return
    dmg = int(ctx.get("dmg", 0) or 0)
    rd = max(1, int(dmg * float(wd["reflect_pct"])))
    if battle.enemy and battle.enemy.get("hp", 0) > 0 and rd > 0:
        battle._deal_damage(rd, logs)
        logs.append(_REFLECT_LOG[key].format(rd=rd))


# ---------------------------------------------------------------- proc_heal amp（4 key）
# 治疗增强段：ctx.heal ×(1+heal_pct)。溢出段（ctx.overflow 真值）跳过——由 battle.py
# 两次 proc（无 overflow 的治疗加成阶段 → 有 overflow 的溢出转盾阶段）驱动。

def _we_exec_heal_amp(battle, player, ctx, logs, wd, key):
    """治疗增幅执行器：ctx.heal ×(1+heal_pct)。"""
    if ctx.get("overflow"):
        return
    heal = int(ctx.get("heal", 0) or 0)
    ctx["heal"] = int(heal * (1 + float(wd["heal_pct"])))


# ---------------------------------------------------------------- 注册表
# 族名 → 执行器。key→族 由数据表 family 字段路由（proc() 分发器读表）。
WE_EXECUTORS = {
    "proc_dot": _we_exec_dot,
    "proc_reflect": _we_exec_reflect,
    "proc_heal": _we_exec_heal_amp,
}

# 族内 key 专属文案/源（dot 触发源 / reflect 日志模板）——数据表未下沉文案时放这
# （C10 收尾可全量下沉 data.log 后删）。
_DOT_SOURCE = {
    "smith_blaze_wound": "🔥 裂伤",
    "rong_lu_yu_wen": "🔥 熔炉余温",
    "ember_burn": "🔥 烬燃",
}
_REFLECT_LOG = {
    "thorn_armor": "🌵 荆棘缠绕：反弹 {rd} 点伤害！",
    "retribution_ring": "⚔️ 复仇之环：反弹 {rd} 点伤害！",
}
