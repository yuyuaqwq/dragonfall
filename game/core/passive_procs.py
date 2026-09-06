# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - passive_procs.py（v181.P2D-D1：被动 proc 注册表基建 + 试点族）

仿 battle_mech.MECH_EFFECTS / affix formula 注册表模式，把散在 battle.py 各挂点的
被动 proc 消费（v169.7 手工 for 循环）收敛为两层注册表：

    PROC_FAMILIES    {proc 名: 机制族名}           —— 数据语义映射（哪个 proc 属于哪个族）
    FAMILY_HANDLERS  {机制族名: handler}           —— 参数化通用执行器（读 skills.py passive dict 数值）

分发入口（battle.py 挂点调用，消灭散点 if）：
    run_proc_family(battle, proc_names, ctx)
    run_proc_family_pm(battle, player, proc_names, ctx)   —— 查 _proc_pm 聚合表（等价原 for...get(proc) 循环）

铁律（对齐 docs/REFACTOR_P2D_passive_proc_registry.md §4 / ARCHITECTURE_TARGET_STATE_v181.md 三层）：
- handler 只读 _ps（skills.py passive dict，P2D-D0 已回填数值 = 唯一权威），**代码零默认值**：
  缺字段 = 无此行为（等价格局铁律）。绝不允许 handler 内部 fallback 到旧引擎写死数值。
- 本文件只出现"机制族键 / proc 键"（52 proc 白名单内），不出现内容 display 名
  （职业/装备/技能中文名——display 名只进日志，由 ctx['ps_name'] 携带）。
- ctx 语义：**同一 dict 全程传递**（run_proc_family_pm 只覆盖 ps/ps_name/player 槽），
  handler 对 ctx 数值槽（mult/rate/cap/limit...）的改写对调用侧可见；调用侧在 run 后读回。
- 第一批试点族（P2-D1，方案 §6.2）：按"先细后粗"——族粒度 = 现有挂点代码直搬。

试点族（5 proc / 5 族）：
    dmg_mult_cond    条件 → 伤害乘区（速度比型）               speed_ratio_dmg（挂点4 _player_dmg_mult）
    lifesteal_add    每层战意 → 吸血率加算（cap 由挂点保留）    zhan_yi_lifesteal（挂点5 _settle_lifesteal）
    stack_cap_add    叠层上限放宽（基础 + Σadd，封顶挂点保留）  poison_cap_up / poison_cap（挂点17 _poison_cap）
    summon_cap_add   召唤同模板上限放宽（min(cap, base+add)）  skeleton_cap（挂点21 _summon_entity）
    on_kill_refill   击杀回满资源（energy/精力）               focus_full_on_kill（挂点22 _remove_unit）

P2-D2a 新增族（4 proc / 1 族，挂点1 _passive_crit_bonus 条件暴击）：
    crit_cond_add    资源/印记满层 → 暴击率 +add                zhan_yi_crit / arcane_wisdom /
                                                               focus_surplus_crit / element_core

P2-D2b 新增族（4 proc / 1 族 stat_mult_cond，挂点2 _passive_crit_dmg_mult + 挂点3 _player_stats）：
    stat_mult_cond   条件 → 面板数值 加/乘（影舞态暴伤加算 + 影舞态速度乘算 + 旋律 3 光环聚合）
                     shadow_dance_bonus（crit_dmg 段 = 挂点2 / spd 段 = 挂点3，双消费点由
                     ctx["stat_kind"] 参数化区分）/ melody_resonance / melody_full / melody_master
                     （后 3 段挂点先聚合再统一乘——handler 返回贡献值，不直接改写 st）

P2-D3a 新增族（3 proc / 2 族，挂点6 _skill_passive_dmg_bonus 技能被动伤害乘区，方案 §6.2/§2.3 挂点6）：
    dmg_mult_cond    条件 → 伤害乘区 1+mult（扩展原 speed_ratio_dmg 族：ctx["mult_kind"] 参数化
                     分派 arcane_mech / element_marks 条件谓词——参考 crit_cond_add ctx res_kind 模式）
                     arcane_resonance（mech ∈ MECH_PROC_GROUPS.arcane_dmg → ×(1+mult)）/
                     element_origin（三系印记 ≥layers → ×(1+mult)，读 battle._elem_marks）
                     语义 = 原挂点 for 循环体逐字直搬；mult 连乘进 ctx["mult"] 槽（引用槽改写读回），
                     返回新 mult（连乘多被动语义由挂点循环 ×= 保留——与迁移前逐段 *= 等价）。
    flag_set_cond    置位型标记族（新族，element_sync 副作用置 battle._elem_sync_bonus = True；
                     与 element_affinity/broken_extend 等 D5 段同族，本批先收 element_sync）
                     element_sync（元素系技能 + 连续同系 → 置 _elem_sync_bonus；供挂印分支消费）
                     无返回值（纯副作用）；ps 空 dict（无参数置位型，学到即生效）

P2-D3b 扩展族（5 proc / 0 新族，挂点14 _deal_damage 对敌标记/破绽/挽歌乘区，方案 §6.2/§2.3 挂点14）：
    dmg_mult_cond    ctx["mult_kind"] 再扩 5 谓词（读 attacker 被动 → 对 target 增伤乘区）：
                     hunt_mark（猎印 0.08 基础 + per_layer）/ soul_mark（魂标 0.06 基础 +
                     per_layer）/ shaken_bar（敌破绽条 val≥bar_at → ×(1+mult)）/
                     broken_break（破防免疫期 trigger_count/immune_turns>0 → ×(1+broken_mult)）/
                     dirge_debuffs（敌负面种数 min(per_debuff×n, cap)）
                     语义 = 原 5 段循环体逐字直搬；ctx 带 target 快照状态（debuffs 层数 /
                     shaken dict）+ tags 引用槽；命中 break 语义由挂点 run_proc_family 单条循环保留。
                     soul_mark_cap/broken_extend 双消费点：本批只收挂点14 乘区段（挂点16 cap 段 /
                     挂点18 延长段后续批次收，届时同 handler 同族 ctx 参数化分派）。
"""
from __future__ import annotations

# ============================================================
# 1. 注册表（两层）
# ============================================================

# proc 名 → 机制族（52 白名单内声明；未声明 = 无注册 = 不触发）
PROC_FAMILIES: dict = {}

# 机制族 → 参数化执行器（签名统一 handler(battle, ctx, ps, ps_name)）
FAMILY_HANDLERS: dict = {}

# 已声明族但执行器尚未派发（后续批次）——只做占位，防误注册成未知族
_FAMILY_PENDING: set = set()

# 启动校验已知缺口（52 中 D/E 类空转/无独立挂点，见方案 §3.4/§3.5；P2-D1 不注册）
KNOWN_GAPS: set = {
    # D 类真空转（0 引擎读取，skills.py 声明 + battle.py 注释 TODO）：
    "faith_share", "finisher_up", "poison_burst_up", "poison_spread",
    # E 类 tick 族成员（行为在模块级 tick handler 名单通道，无独立挂点；P2-D6 收）：
    "focus_regen_summon", "arcane_intuition", "undead_faith", "faith_overload_heal",
}

_REG_ORDER: list = []


def register(family: str):
    """装饰器：注册一个机制族执行器。重复注册同族 = 报错（防静默覆盖）。"""
    def deco(fn):
        if family in FAMILY_HANDLERS:
            raise RuntimeError(f"passive_procs 重复注册机制族: {family}")
        _REG_ORDER.append(("handler", family))
        FAMILY_HANDLERS[family] = fn
        _FAMILY_PENDING.discard(family)
        return fn
    return deco


def declare_proc(proc: str, family: str):
    """数据映射：声明 proc → 机制族。重复声明 = 报错（防覆盖，白名单防静默空转）。"""
    if not family:
        raise ValueError(f"passive_procs.declare_proc({proc!r}): family 不能为空")
    if proc in PROC_FAMILIES:
        raise RuntimeError(f"passive_procs 重复声明 proc: {proc} (已属 {PROC_FAMILIES[proc]!r})")
    PROC_FAMILIES[proc] = family
    if family not in FAMILY_HANDLERS:
        _FAMILY_PENDING.add(family)


# ============================================================
# 2. 分发
# ============================================================

def run_proc_family(battle, proc_names, ctx: dict):
    """挂点分发：按 proc 名逐个查族执行器。

    - 无注册（proc 未 declare / 族无执行器）= 不触发（配置缺字段 = 无此行为）。
    - 返回每个执行器的返回值列表（None 不计）；副作用/数值槽改写直接落在 battle/actor/ctx。
    - ctx 约定：{'player', 'ps'(=passive dict，数值唯一权威), 'ps_name'(display 名，只进日志),
      挂点私有字段（现成计算量/引用槽/快照/logs）}。handler 对 ctx 数值槽改写 → 调用侧读回。
    - 结算管线容错：handler 异常吞错留痕（与原挂点 except → _battle_warn → pass 语义一致）。
    """
    out = []
    if not proc_names:
        return out
    if isinstance(proc_names, str):
        proc_names = [proc_names]
    for _pname in proc_names:
        _fam = PROC_FAMILIES.get(_pname)
        if not _fam:
            continue  # 无注册 = 不触发
        _h = FAMILY_HANDLERS.get(_fam)
        if not _h:
            continue  # 族已声明但执行器未派（后续批次）→ 不触发
        try:
            _r = _h(battle, ctx, ctx.get("ps") or {}, ctx.get("ps_name") or _pname)
        except Exception as _e:
            _swallow(battle, f"passive_procs.run({_pname}/{_fam})", _e)
            continue
        if _r is not None:
            out.append(_r)
    return out


def _swallow(battle, site, exc):
    """结算管线吞错留痕（同 battle.py _battle_warn 语义：不抛错、不改行为）。"""
    try:
        _warn = getattr(battle, "_battle_warn", None)
        if callable(_warn):
            _warn(site, exc)
            return
    except Exception:
        pass
    try:
        import logging as _lg
        _lg.getLogger("dragonfall.battle").warning("[battle-swallow] %s: %r", site, exc)
    except Exception:
        pass


def run_proc_family_pm(battle, player, proc_names, ctx: dict):
    """聚合分发（挂点标准入口）：查 _proc_pm(player)['proc'][proc] 的 [(display名, passive dict), ...]
    逐条执行，等价原挂点 `for _pn,_ps in ...get(proc, [])` 循环体换成注册表调用。

    - ctx 全程同一 dict：逐条只覆盖 ps/ps_name（player 槽由调用侧预置或此处覆盖），
      handler 的数值槽改写（mult/rate/cap/limit...）直接可见 → 调用侧 run 后读回。
    - 遍历 proc 名 × 该名下全部条目：与 max=1 数据约束（同 proc 至多 1 条被动）下
      原 break 语义等价；毒层上限族（无 break、聚合全部条目）亦等价。
    """
    if isinstance(proc_names, str):
        proc_names = [proc_names]
    try:
        pm = battle._proc_pm(player)
        procs = pm.get("proc") if isinstance(pm, dict) else {}
    except Exception:
        procs = {}
    out = []
    if not isinstance(procs, dict):
        procs = {}
    ctx["player"] = player
    for _pname in proc_names:
        for _pn, _ps in procs.get(_pname, []):
            ctx["ps"] = _ps
            ctx["ps_name"] = _pn
            _r = run_proc_family(battle, [_pname], ctx)
            if _r:
                out.extend(_r)
    return out


# ============================================================
# 3. 试点族执行器（P2-D1：5 proc / 5 族，纯计算最独立、无双消费点）
#    每个 handler 逻辑 = 对应挂点迁移前的原 for 循环体逐字直搬（行为零变化）。
# ============================================================

# ---- 3.1 dmg_mult_cond（疾风·极 speed_ratio_dmg：挂点4 _player_dmg_mult）----
@register("dmg_mult_cond")
def _h_dmg_mult_cond(battle, ctx: dict, ps: dict, ps_name: str):
    """速度比 ≥ ratio → 伤害 ×(1+dmg_add)；奥术系/三系印记 → ×(1+mult)（条件伤害乘区族）。

    ctx 分派（mult_kind ∈ speed_ratio/arcane_mech/element_marks；缺省 speed_ratio 兼容挂点4）：
    - speed_ratio    速度比 ≥ ps.ratio → ×(1+ps.dmg_add)（疾风·极；原挂点4 _player_dmg_mult）
                     读 ctx.pst_spd/est_spd；敌方无速度键按 0 防御性跳过（原语义）；标签 💨疾风x… 原样保留
    - arcane_mech    mech ∈ MECH_PROC_GROUPS.arcane_dmg → ×(1+ps.mult)（奥术共鸣；原挂点6 循环体）
                     需 ctx["mech"]；多条目逐条累乘（原 for 无 break——逐条 *=，连乘语义保留）
    - element_marks  三系印记同时 ≥ps.layers → ×(1+ps.mult)（元素起源；原挂点6 循环体）
                     读 battle._elem_marks()（目标侧印记；try/except 吞错留痕原样保留）；
                     无技能元素/系别守卫（原循环体无 element 判定——三系印记齐即对任意结算伤害生效）；
                     首条命中即 break（原 `break` 无条件在循环尾——max=1 下等价，多条目防御
                     保留原"只判首条"语义）
    通用：数值缺字段（ratio/dmg_add/mult/layers ≤ 0）= 无此行为（零默认值铁律）；
    命中 → ctx["mult"] *= (1+增量)（引用槽改写读回）并返回新 mult；未命中返回 None。
    """
    _kind = ctx.get("mult_kind") or "speed_ratio"
    if _kind == "arcane_mech":
        # 挂点6 奥术共鸣 arcane_resonance：奥术系技能伤害 +15%（与奥术之心同 mech 口径叠加）
        _mult = float(ps.get("mult", 0.0) or 0.0)
        if _mult <= 0:
            return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 0.15）
        _mech = ctx.get("mech")
        if not _mech or _mech not in ("arcane",):
            return None  # 非奥术系技能 → 不触发（原 `mech in MECH_PROC_GROUPS.arcane_dmg` 判定）
        _nv = ctx["mult"] * (1.0 + _mult)
        ctx["mult"] = _nv
        return _nv
    if _kind == "element_marks":
        # 挂点6 元素起源 element_origin：三系印记同时 ≥layers → 结算伤害 ×(1+mult)（加算乘区）
        # （原循环体无元素系技能守卫——三系印记齐即乘，对任意结算伤害生效）
        _layers = int(ps.get("layers", 0) or 0)
        _mult = float(ps.get("mult", 0.0) or 0.0)
        if _layers <= 0 or _mult <= 0:
            return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 2/0.20）
        try:
            _mk_origin = battle._elem_marks()
            if _mk_origin and all(int(_mk_origin.get(_ek, 0) or 0) >= _layers
                                  for _ek in ("fire", "ice", "thunder")):
                _nv = ctx["mult"] * (1.0 + _mult)
                ctx["mult"] = _nv
                return _nv
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.element_origin", _sw_e)
            pass
        return None
    if _kind == "hunt_mark":
        # 挂点14 猎印 hunt_mark_up（自然之眼）——只负责被动额外加成段：
        # 原循环体 `_hm_pct += per_layer; break`（基础 0.08/层 乘区是无被动的固有
        # 标记语义，由挂点保留在 if _hm>0 块外——v180-C S3「标记基础谁打都吃」）。
        # 返回 per_layer 增量（调用侧并入基础）；首条 break 由挂点循环保留。
        _per = float(ps.get("per_layer", 0.0) or 0.0)
        if _per <= 0:
            return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 0.06）
        return _per
    if _kind == "soul_mark":
        # 挂点14 魂标 soul_mark_cap（灵魂锁链）乘区段——同猎印：只加被动额外 per_layer
        # （基础 0.06/层 由挂点保留）；cap 放宽段在挂点16 _apply_mech_effect（D4 收）
        _per = float(ps.get("per_layer", 0.0) or 0.0)
        if _per <= 0:
            return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 0.08）
        return _per
    if _kind == "shaken_bar":
        # 挂点14 气力之心 shaken_awareness：目标 buffs.shaken dict 且 val≥_ps.bar_at →
        # ×(1+_ps.mult)；标签固定 🧠破绽x1.2；首条 break（即使不满足也 break——只判首条）。
        # 守卫：shaken dict 存在性由调用侧 ctx["shaken"] 快照判（原 isinstance 外 if）
        _bar = int(ps.get("bar_at", 0) or 0)
        _mult = float(ps.get("mult", 0.0) or 0.0)
        if _bar <= 0 or _mult <= 0:
            return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 15/0.20）
        _sh = ctx.get("shaken")
        if not isinstance(_sh, dict):
            return None
        if int(_sh.get("val", 0) or 0) >= _bar:
            _nv = ctx["mult"] * (1.0 + _mult)
            ctx["mult"] = _nv
            _tags = ctx.setdefault("tags", [])
            if isinstance(_tags, list):
                _tags.append("🧠破绽x1.2")
            return _nv
        return None
    if _kind == "broken_break":
        # 挂点14 破绽·极 broken_extend 乘区段：目标 shaken dict 且 trigger_count>0 且
        # immune_turns>0（破防免疫期）→ ×(1+_ps.broken_mult)；标签 💢破防x…；首条 break。
        # 守卫（trigger_count/immune_turns>0）由调用侧 ctx["shaken"] 快照（原外层 if）——
        # handler 内再判一遍防御（调用侧守卫保留 + 此处兜底，双保险）
        _bm = float(ps.get("broken_mult", 0.0) or 0.0)
        if _bm <= 0:
            return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 0.50）
        _sh = ctx.get("shaken")
        if not isinstance(_sh, dict):
            return None
        if int(_sh.get("trigger_count", 0) or 0) > 0 and int(_sh.get("immune_turns", 0) or 0) > 0:
            _nv = ctx["mult"] * (1.0 + _bm)
            ctx["mult"] = _nv
            _tags = ctx.setdefault("tags", [])
            if isinstance(_tags, list):
                _tags.append(f"💢破防x{round(1 + _bm, 2)}")
            return _nv
        return None
    if _kind == "dirge_debuffs":
        # 挂点14 挽歌·极 dirge_debuff_dmg：读 battle._enemy_debuff_kind_count()（self.enemy
        # 口径——原循环体直读，非 target）→ pct=min(_ps.per_debuff×种数, _ps.cap)；pct>0 →
        # ×(1+pct)；标签 🎵挽歌x…；首条 break（无条件——只判首条）
        _per = float(ps.get("per_debuff", 0.0) or 0.0)
        _cap = float(ps.get("cap", 0.0) or 0.0)
        if _per <= 0 or _cap <= 0:
            return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 0.04/0.40）
        _kinds = 0
        try:
            if hasattr(battle, "_enemy_debuff_kind_count"):
                _kinds = int(battle._enemy_debuff_kind_count() or 0)
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.dirge_debuff_dmg", _sw_e)
            pass
        _pct_e = min(_per * _kinds, _cap)
        if _pct_e > 0:
            _nv = ctx["mult"] * (1.0 + _pct_e)
            ctx["mult"] = _nv
            _tags = ctx.setdefault("tags", [])
            if isinstance(_tags, list):
                _tags.append(f"🎵挽歌x{round(1 + _pct_e, 2)}")
            return _nv
        return None
    # ---- 挂点4 疾风·极 speed_ratio_dmg（缺省 mult_kind）----
    _ratio = float(ps.get("ratio", 0) or 0)
    _add = float(ps.get("dmg_add", 0) or 0)
    if _ratio <= 0 or _add <= 0:
        return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填）
    _pst_spd = float(ctx.get("pst_spd") or 0)
    _est_spd = float(ctx.get("est_spd") or 0)
    if _est_spd <= 0:
        return None  # 敌方无速度键 → 0 防御性跳过（原语义）
    if _pst_spd / _est_spd < _ratio:
        return None
    ctx["mult"] = ctx["mult"] * (1.0 + _add)
    _tags = ctx.setdefault("tags", [])
    if isinstance(_tags, list):
        _tags.append(f"💨疾风x{round(1 + _add, 2)}")
    return ctx["mult"]

# ---- 3.2 lifesteal_add（淬血 zhan_yi_lifesteal：挂点5 _settle_lifesteal）----
@register("lifesteal_add")
def _h_lifesteal_add(battle, ctx: dict, ps: dict, ps_name: str):
    """每层战意 → 吸血率 +per_layer（加算并入 rate；cap 30% 由挂点 min 保留）。

    ctx：zhan_yi_n（战意层数）、rate（引用槽，改写读回）。数值读 _ps：per_layer（D0 回填 0.015）。
    """
    _per = float(ps.get("per_layer", 0) or 0)
    if _per <= 0:
        return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填）
    _zy = int(ctx.get("zhan_yi_n") or 0)
    if _zy <= 0:
        return None
    ctx["rate"] = ctx["rate"] + _per * _zy
    return ctx["rate"]


# ---- 3.3 stack_cap_add（剧毒之心 poison_cap_up / 淬毒之心 poison_cap：挂点17 _poison_cap）----
@register("stack_cap_add")
def _h_stack_cap_add(battle, ctx: dict, ps: dict, ps_name: str):
    """叠层上限放宽：cap += add（缺字段按 0 不触发；封顶/下限由挂点保留）。

    ctx：cap（引用槽，改写读回）。数值读 _ps：add（D0 回填 3）。
    """
    _add = int(ps.get("add", 0) or 0)
    if _add <= 0:
        return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填）
    ctx["cap"] = ctx["cap"] + _add
    return ctx["cap"]


# ---- 3.4 summon_cap_add（骷髅海 skeleton_cap：挂点21 _summon_entity）----
@register("summon_cap_add")
def _h_summon_cap_add(battle, ctx: dict, ps: dict, ps_name: str):
    """召唤同模板上限放宽：limit = min(cap, 原limit + add)（缺字段按 0 不触发）。

    ctx：limit（引用槽，改写读回）。数值读 _ps：cap/add（D0 回填 5/2）。
    """
    _cap = int(ps.get("cap", 0) or 0)
    _add = int(ps.get("add", 0) or 0)
    if _cap <= 0 or _add <= 0:
        return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填）
    ctx["limit"] = min(_cap, ctx["limit"] + _add)
    return ctx["limit"]


# ---- 3.5 on_kill_refill（追风 focus_full_on_kill：挂点22 _remove_unit）----
@register("on_kill_refill")
def _h_on_kill_refill(battle, ctx: dict, ps: dict, ps_name: str):
    """击杀回满资源：energy = 上限（无参数族：有注册即触发 = 学到即生效；ps 可为空 dict）。

    ctx：res（= battle._p_res() 引用 dict，直接改写）、res_key（默认 energy）、
         res_max（挂点现成 _res_max 值）、pending_dmg_lines（日志池，存在才追加）。
    """
    _res = ctx.get("res") or {}
    _cur = _res.get(ctx.get("res_key") or "energy")
    if _cur is None:
        return None  # 该资源不存在 → 不触发（原语义：energy is None 跳过）
    _max_v = int(ctx.get("res_max") or 0)
    _old = int(_cur or 0)
    _res[ctx.get("res_key") or "energy"] = _max_v
    # v180G B7-fix：日志追加到 _pending_dmg_lines（战斗日志池，存在才追加）
    _kl = ctx.get("pending_dmg_lines")
    if isinstance(_kl, list):
        _kl.append(f"💨 {ctx.get('ps_name') or ps_name}：击杀！专注回满（{_old} → {_max_v}）")
    return _old


# ============================================================
# 4. crit_cond_add（P2-D2a：挂点1 _passive_crit_bonus 条件暴击 4 proc）
#    资源/印记满层 → 暴击率 +add（缺字段 = 无此行为，零默认值铁律）。
#    同族多 proc 参数化：ctx["res_kind"] 分派条件谓词（战意/奥术充能/精力快照/元素印记），
#    阈值与加成读 _ps（stacks/surplus/layers/add）——不新写 handler（方案 §4.2/§1.1 判定 2）。
# ============================================================
@register("crit_cond_add")
def _h_crit_cond_add(battle, ctx: dict, ps: dict, ps_name: str):
    """资源/印记满层 → 暴击率 +add（条件暴击族；逐字直搬 _passive_crit_bonus 原 4 for 循环体）。

    ctx 分派（res_kind ∈ zhan_yi/arcane/focus/element_mark）：
    - zhan_yi      战意层数 ≥ ps.stacks → +add（读 battle._zhan_yi_n()）
    - arcane       element_charge 满条（charge ≥ 资源上限）或 stacks.arcane ≥ ps.stacks → +add
                  （攻线满层门槛读数据 stacks——v181.C 原写死 5）
    - focus        施放前精力快照 _pre_cost_res ≥ ps.surplus → +add + 置位提示标记（需 ctx["info"]）
    - element_mark info.element 对应印记层 ≥ ps.layers → +add（需 ctx["info"]）
    数值读 _ps：stacks（zhan_yi/arcane）/ surplus（focus）/ layers（element_mark）+ add；
    缺字段（阈值或 add ≤ 0）= 无此行为（零默认值铁律；D0 已回填 8/0.15、5/0.20、40/0.20、3/0.20）。
    命中 → ctx["crit_add"] 累加并返回 add；未命中/缺条件返回 None。
    info 门槛等价：focus/element_mark 无 info 时直接返回 None（原挂点 `if info is not None:` 守卫
    包裹两循环——调用侧守卫保留 + 此处兜底，双保险）；zhan_yi/arcane 无 info 依赖。
    副作用保留：focus 命中置 battle._p_eff()["focus_surplus_proc"] = True
    （v169.7 修 #123 提示标记，_cast_eff() 6536 行消费提示行）。
    """
    _add = float(ps.get("add", 0.0) or 0.0)
    if _add <= 0:
        return None  # 缺字段 = 无此行为（零默认值铁律）
    _kind = ctx.get("res_kind")
    _hit = False
    if _kind == "zhan_yi":
        _need = int(ps.get("stacks", 0) or 0)
        if _need <= 0:
            return None
        try:
            _zy = battle._zhan_yi_n() if hasattr(battle, "_zhan_yi_n") else int(ctx.get("zhan_yi_n") or 0)
            _hit = int(_zy or 0) >= _need
        except Exception:
            _hit = False
    elif _kind == "arcane":
        _need = int(ps.get("stacks", 0) or 0)
        if _need <= 0:
            return None
        try:
            _res = battle._p_res() if hasattr(battle, "_p_res") else {}
            if (_res or {}).get("element_charge") is not None:
                # 守线·奥秘法师充能条：charge ≥ 该资源当前上限
                _hit = battle._elem_charge() >= battle._res_max(ctx.get("player") or battle.player or {}, "element")
            else:
                # 攻线 arcane 叠层 ≥ 满层门槛（读数据 stacks）
                _stk = battle._p_stacks() if hasattr(battle, "_p_stacks") else {}
                _hit = int((_stk or {}).get("arcane", 0) or 0) >= _need
        except Exception:
            _hit = False
    elif _kind == "focus":
        if ctx.get("info") is None:
            return None  # 非技能链直接调用（info 缺省 None）→ 不触发（原 `if info is not None:` 门槛）
        _need = int(ps.get("surplus", 0) or 0)
        if _need <= 0:
            return None
        try:
            _pres = getattr(battle, "_pre_cost_res", None)
            if isinstance(_pres, dict):
                _eng = int(_pres.get("energy", 0) or 0)
            else:
                _eng = int((battle._p_res() if hasattr(battle, "_p_res") else {}).get("energy", 0) or 0)
        except Exception:
            _eng = 0
        _hit = _eng >= _need
    elif _kind == "element_mark":
        if ctx.get("info") is None:
            return None  # 非技能链直接调用（info 缺省 None）→ 不触发（原 `if info is not None:` 门槛）
        _need = int(ps.get("layers", 0) or 0)
        if _need <= 0:
            return None
        try:
            _info = ctx.get("info") or {}
            _el = _info.get("element", "")
            if _el == "current":
                _el = (battle._p_res() if hasattr(battle, "_p_res") else {}).get("element", "fire")
            if _el:
                _mk = battle._elem_marks() if hasattr(battle, "_elem_marks") else {}
                _hit = int((_mk or {}).get(_el, 0) or 0) >= _need
        except Exception:
            _hit = False
    else:
        return None  # 未知 res_kind = 不触发（调用侧未配置该 proc 的条件谓词）
    if _hit:
        ctx["crit_add"] = ctx.get("crit_add", 0.0) + _add
        if _kind == "focus":
            # v169.7 修 #123 提示（意见 #123「没看到提示文本」）：置位后由 _cast_eff() 6536 行消费
            try:
                battle._p_eff()["focus_surplus_proc"] = True
            except Exception:
                pass
        return _add
    return None


# ============================================================
# 5. stat_mult_cond（P2-D2b：挂点2 _passive_crit_dmg_mult + 挂点3 _player_stats）
#    条件 → 面板数值 加/乘。本批 4 proc 一个族，ctx[\"stat_kind\"] 参数化分派：
#    - crit_dmg（挂点2）：影舞态 → crit_dmg 加法增量（返回数值，挂点加算并入 cdmg）
#    - spd（挂点3）：影舞态 → spd ×(1+spd_add)（返回增量比例，挂点读回后乘；int 截断在挂点）
#    - melody（挂点3）：旋律 3 光环聚合——3 段各返回贡献（共振 ≥stacks / 满层 ≥stacks /
#      每层 per_stack×n），挂点先累加 _mel_pct 再统一乘（保原"3 段聚合再统一乘"语义）
#    双消费点：shadow_dance_bonus 属 stat_kind=crit_dmg（挂点2）+ stat_kind=spd（挂点3），
#    族内参数化（proc 名同、ctx stat_kind 异）——参考 crit_cond_add 的 ctx res_kind 分派模式。
#    零默认值：spd_add/crit_dmg/mult/per_stack/stacks 缺字段 → 返回 None（不触发）。
# ============================================================
@register("stat_mult_cond")
def _h_stat_mult_cond(battle, ctx: dict, ps: dict, ps_name: str):
    """条件 → 面板数值 加/乘（逐字直搬 _player_stats 影舞 spd 段 / _passive_crit_dmg_mult
    原循环体 + 旋律 3 光环原 for 循环体；缺字段 = 无此行为，零默认值铁律）。"""
    _kind = ctx.get("stat_kind")
    if _kind == "crit_dmg":
        # 挂点2：影舞态 → 暴伤加法增量（读 _ps.crit_dmg）
        _add = float(ps.get("crit_dmg", 0.0) or 0.0)
        if _add <= 0:
            return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 0.20）
        return _add
    if _kind == "spd":
        # 挂点3 影舞 spd 段：影舞态（ctx[\"shadow_dance\"]=True 守卫由挂点保留）→ +spd_add 比例
        _add = float(ps.get("spd_add", 0.0) or 0.0)
        if _add <= 0:
            return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 0.25）
        return _add
    if _kind == "melody":
        # 挂点3 旋律 3 光环段：3 段聚合语义由挂点保留——本 handler 按 proc 各返回贡献
        # （共振/满层各自 stacks 门槛判定；咏叹·极 每层 per_stack×n），挂点累加后统一乘。
        _n = int(ctx.get("melody_n") or 0)  # 旋律强度层（挂点已守卫 name 非空且 n>0）
        _stk = int(ps.get("stacks", 0) or 0)
        _mult = float(ps.get("mult", 0.0) or 0.0)
        if _stk > 0 and _mult > 0 and _n >= _stk:
            return _mult  # 共鸣 stacks=3/mult=0.10；万籁和鸣 stacks=5/mult=0.15
        _per = float(ps.get("per_stack", 0.0) or 0.0)
        if _per > 0 and _n > 0:
            return _per * _n  # 咏叹·极 per_stack=0.05 × n
        return None  # 缺 stacks/mult/per_stack 或不达标 = 无此行为
    return None  # 未知 stat_kind = 不触发


# ============================================================
# 5b. flag_set_cond（P2-D3a：挂点6 _skill_passive_dmg_bonus element_sync 置位段）
#     条件命中 → 置 battle 标记（纯副作用族；后续批次 D5 收 element_affinity/broken_extend 等）
# ============================================================
@register("flag_set_cond")
def _h_flag_set_cond(battle, ctx: dict, ps: dict, ps_name: str):
    """条件命中 → 置位标记（原挂点6 element_sync 循环体逐字直搬；ps 空 dict = 无参数置位型）。

    ctx 分派（flag_kind）：
    - elem_sync    元素系技能（ctx["is_elem_skill"]，原 `element and E.ELEMENT_MARKS.get(element)`
                   前置门槛）且 battle._p_last_element() == ctx["element"]（连续同系）
                   → 置 battle._elem_sync_bonus = True（副作用；供挂印分支 6567 消费后清零）
                   读 _p_last_element 的 try/except 吞错留痕原样保留
    flag_set_cond 无参数族语义：有注册即触发（学到即生效），ps 可为空 dict——
    但保留零默认值铁律：缺 flag_kind / 条件不成立 = 不触发。
    """
    _kind = ctx.get("flag_kind")
    if _kind == "elem_sync":
        # 元素同调：连续两次同系施法，第二次挂印 +1 层（置 _elem_sync_bonus 标记）
        if not ctx.get("is_elem_skill"):
            return None  # 非元素系技能 → 不触发（原 `element and E.ELEMENT_MARKS.get(element)` 门槛）
        try:
            if battle._p_last_element() == ctx.get("element"):
                battle._elem_sync_bonus = True
                return True
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.element_sync", _sw_e)
            pass
        return None
    return None  # 未知 flag_kind = 不触发（调用侧未配置该 proc 的置位谓词）


# ============================================================
# 6. proc → 族 声明（P2-D1 试点 5 proc + P2-D2a crit_cond_add 4 proc +
#    P2-D2b stat_mult_cond 4 proc + P2-D3a dmg_mult_cond 扩展 2 + flag_set_cond 1；
#    其余 52 内 proc 由 P2-D2c~D7 批次按序声明）
# ============================================================
declare_proc("speed_ratio_dmg", "dmg_mult_cond")
declare_proc("arcane_resonance", "dmg_mult_cond")
declare_proc("element_origin", "dmg_mult_cond")
declare_proc("element_sync", "flag_set_cond")
# P2-D3b：挂点14 _deal_damage 对敌标记/破绽/挽歌 5 proc（dmg_mult_cond ctx mult_kind 分派
# hunt_mark/soul_mark/shaken_bar/broken_break/dirge_debuffs；乘区段语义直搬）——
# soul_mark_cap/broken_extend 的双消费点（挂点16 cap 段 / 挂点18 延长段）由后续批次收
declare_proc("hunt_mark_up", "dmg_mult_cond")
declare_proc("soul_mark_cap", "dmg_mult_cond")
declare_proc("shaken_awareness", "dmg_mult_cond")
declare_proc("broken_extend", "dmg_mult_cond")
declare_proc("dirge_debuff_dmg", "dmg_mult_cond")
declare_proc("zhan_yi_lifesteal", "lifesteal_add")
declare_proc("poison_cap_up", "stack_cap_add")
declare_proc("poison_cap", "stack_cap_add")
declare_proc("skeleton_cap", "summon_cap_add")
declare_proc("focus_full_on_kill", "on_kill_refill")
declare_proc("zhan_yi_crit", "crit_cond_add")
declare_proc("arcane_wisdom", "crit_cond_add")
declare_proc("focus_surplus_crit", "crit_cond_add")
declare_proc("element_core", "crit_cond_add")
declare_proc("shadow_dance_bonus", "stat_mult_cond")
declare_proc("melody_resonance", "stat_mult_cond")
declare_proc("melody_full", "stat_mult_cond")
declare_proc("melody_master", "stat_mult_cond")

