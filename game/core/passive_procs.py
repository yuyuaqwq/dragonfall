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
    """速度比 ≥ ratio → 伤害 ×(1+dmg_add)。

    ctx：pst_spd（玩家速度，≥0.001 现成值）、est_spd（敌方速度，>0 才判）、
         mult/tags（引用槽；改写调用侧读回）。数值读 _ps：ratio/dmg_add（D0 回填 2.0/0.20）。
    原挂点语义：敌方无速度键按 0 防御性跳过；标签 💨疾风x… 原样保留。
    """
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
# 5. proc → 族 声明（P2-D1 试点 5 proc + P2-D2a crit_cond_add 4 proc；
#    其余 52 内 proc 由 P2-D2b~D7 批次按序声明）
# ============================================================
declare_proc("speed_ratio_dmg", "dmg_mult_cond")
declare_proc("zhan_yi_lifesteal", "lifesteal_add")
declare_proc("poison_cap_up", "stack_cap_add")
declare_proc("poison_cap", "stack_cap_add")
declare_proc("skeleton_cap", "summon_cap_add")
declare_proc("focus_full_on_kill", "on_kill_refill")
declare_proc("zhan_yi_crit", "crit_cond_add")
declare_proc("arcane_wisdom", "crit_cond_add")
declare_proc("focus_surplus_crit", "crit_cond_add")
declare_proc("element_core", "crit_cond_add")
