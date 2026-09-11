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
    dmg_mult_cond    条件 → 伤害乘区（速度比型）               speed_ratio_dmg（挂点4 _actor_dmg_mult）
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

P2-D4a 新增族（6 proc / 3 族，方案 §6.2/§2.3 挂点10 player_turn + 挂点11 _mitigate_chain）：
    cc_break_cost    战意挡控（3 次/场，_tenacity_try_break 骨架迁表）        tenacity
    cc_immune_cond   条件免控（挂点10 免眩晕/免控窗口兜底）                  zhan_yi_full_reduce / core_full
    dr_cond          条件减伤（挂点11 _mitigate_chain 聚合段）               zhan_yi_full_reduce / core_full /
                     core_reduce / core_last_stand(已触发常驻段) / core_overflow(溢出转盾段)
    挂点 10/11 是**最高风险批次**：多 if 严格先后（坚韧先于坚城免眩晕先于磐石免控）逐字保留、
    一次性 flag（_tenacity_left_n/_core_last_stand_used）随战斗序列化——handler 读写一律走
    battle 属性（getattr/setattr），不落 actor dict 局部；磐核溢出转盾（core_overflow）段
    只做"承伤转化"判定与 _add_shield 副作用（键 core_overflow），挂点保留 _dr_pct 聚合计减。

P2-D4b 新增族（3 proc / 1 族 revive_cond，挂点12 _post_hp_lethal 致死复活链，方案
§6.2 P2-D4/§2.3 挂点12/§3.2 映射表）：
    revive_cond      致死复活（一次性 flag 族）        death_contract / berserk_revive /
                                                      stance_immortal
    挂点12 是**最高风险批次之二**：三条复活 if 严格先后（死亡契约先于血怒先于铁誓，谁先
    触发谁生效——不死鸟 phoenix_revive 更靠前，复活后 hp>0 后续块自然短路）逐字保留、
    顺序不许重排；一次性 flag（_death_pact_used/_berserk_revive_used/_stance_immortal_used）
    随战斗序列化（to_state/from_state battle.py 1259-1264/1550-1554）——handler 读写一律
    battle 属性（getattr/setattr），不落 actor dict 局部；_death_pact_used 与 v107 暗影
    祭司旧死亡契约（proc death_pact 非 52 白名单）共享——旧通道保留不迁移（不注册），
    两条链仍消费同一致死钩子与 flag。ctx revive_kind 分派三段：death_pact_cond（死亡契约
    信念≥faith_req 且存活骷髅在场 → 牺牲尾骷髅复活 hp_pct）/ berserk（血怒·不灭 狂暴态
    → 清空战意复活 hp_pct）/ stance（铁誓·不动 守护姿态 → 免疫致命 1 次清空战意回满 hp_pct）。
    数值读 _ps：faith_req/hp_pct（D0 已回填 5/0.20、0.30、1.0）；缺字段 = 无此行为（零默认
    值铁律）。语义 = 原 3 段循环体逐字直搬：命中（复活成功）→ 返回 True（调用侧 break），
    未命中（信念不足/无骷髅）→ 返回 None（调用侧 continue/循环尾——等价格局下与 max=1 单
    条目原语义等价）。形态判定（dual_form_active 狂暴）与守护姿态 buff 守卫留在 battle 骨架。

P2-D6 新增族（4 proc / 3 族，battle.py 顶部模块级 tick handler 区——_th_passive_heal/
_th_mech_charge/_th_faith_decay，方案 §6.2 P2-D6/§2.3 挂点24/§3.2 映射表 176-179）：
    tick_regen        每刻被动回复族（召唤物在场回 energy）     focus_regen_summon
    tick_mech_charge  每刻奥术充能族（focus 态 +focus_gain）    arcane_intuition
    tick_faith        信念每刻族（亡灵在场回 faith + 过载回血×） undead_faith /
                                                               faith_overload_heal
    模块级 handler（签名 (battle, actor, eff, logs)）不是 Battle 方法：外层 tick 包装
    （被动回复族 turn_heal/team_regen / 奥术·魔剑充能族 arcane_regen+stat 通道
    spellblade_regen / 信念衰减状态机）留在 battle.py 骨架原样（非 52 同族不迁移），
    4 proc 分支 for 循环体直搬进族 handler（ctx faith_kind/mech 分派）；骨架调
    run_proc_family 逐条执行（max=1 下与原 break 等价）。数值读 _ps：gain（5）/
    gain+focus_gain（1+1）/ per_undead（0.15）/ heal_up（0.30）——D0 已回填；
    缺字段 = 无此行为（零默认值铁律）。mech_stack_gain/focus_active 由骨架 ctx 注入
    （core 层避免直接 import engine/battle_modes——battle.py 顶部已有 import 别名）。
    名单通道（_regen_needed/_ensure_regen_effects）：proc 名是"卡片存在性"检查键
    （查 _pm[proc] 非空）——注册表化后 proc 名不变 → 名单不动。
    KNOWN_GAPS 移除 4 个 E 类成员（tick 族已收编）；剩 D 类 4 个真空转。
P2-D5a 新增族（2 proc / 1 族 counter_cond，挂点13 _retaliations_and_buffs 受击反击
聚合段，方案 §6.2 P2-D5/§2.3 挂点13/§3.2 映射表 counter_chance/counter_up）：
    counter_cond     受击反击聚合族（聚合）            counter_chance / counter_up
    聚合语义（原挂点 10776-10800 双 for 循环逐字直搬）：
      - chance = max(所有 counter_chance.chance)；mult = min(所有 counter_chance.mult)
        （以守为攻 35% 概率 ×80% 普攻；多条目防御性 max/min——原 for 无 break 全聚）
      - 存在 counter_up 条目 → 只取首条（原 `break` 在循环尾——max=1 下等价）：
        chance += chance_add；mult *= (1.0 + dmg_add)（反击之王 +25% 概率 / 伤害 ×1.50；
        两被动皆学 = 0.60 概率 ×1.20 普攻）
      - 聚合结果（ctx 引用槽 chance/mult）由挂点逐条 run 后读回；cap min(chance, 0.9)
        与 roll（random.random() < chance → _phys_retort + _hit_back + 日志 + 反击回气
        气+2）是聚合结果的**一次性消费**，留在挂点骨架（原代码即聚合完才 roll 一次——
        逐条目 handler 无法预知后续条目，roll 天然属聚合收口点 = 调用侧）。
    本 handler = 单条目聚合贡献器：每次调用把一个 proc 条目的数值聚合进 ctx 槽
    （chance/mult 跨调用全程传递，同 ctx 数值槽铁律），返回 None。proc 角色读
    ps["proc"]（passive dict 自带键，数据权威非内容名）：counter_chance → max/min；
    counter_up → += chance_add / *= (1+dmg_add)。数值读 _ps 零默认：chance/mult 或
    chance_add/dmg_add 缺字段/≤0 = 该条目不聚合（无此行为；D0 已回填 0.35/0.80、0.25/0.50）。
    挂点13 if 骨架（_rtgt 存活守卫 + _cc_list or _cu_list 才进）+ 日志串/顺序逐字保留。
P2-D5b 新增族（4 proc / 2 新族 + 1 扩族，挂点15 _tick_actor_dots + 挂点16 _apply_mech_effect
cap 段，方案 §6.2 P2-D5/§2.3 挂点15/16/§3.2 映射表）：
    dot_mult_cond    毒 DOT 乘区（挂点15：poison_all_up 万毒归宗 mult 0.35——毒层伤害 ×(1+mult)；
                     毒 tick 结算只对 k==poison 且 caster 玩家生效——守卫由挂点骨架保留
                     `if k == \"poison\" and _caster_is_player`，handler 返回新乘数给调用侧
                     引用槽改写读回；首条 break 语义 = run_proc_family_pm 逐条（max=1）等价）
    dot_weaken       毒层 → 目标减速降防（挂点15：poison_weaken 剧毒之触 layers 5 /
                     spd_down 2 / def_down 2——毒层 ≥ps.layers 时给目标 e.buffs 写
                     spd_down/def_down = max(现值, ps 值) 与 _weaken_spd_pct 0.30 /
                     _weaken_def_pct 0.20（**写死百分值非零默认值**：0.30/0.20 是减速降防
                     幅度的固有引擎语义——desc「减速 30%、降防 20%」由这两键消费，引擎侧
                     无对应 _ps 键可读，属引擎固有常量，非 proc 数值配置；spd_down/def_down
                     才是被动数值读 _ps） + 固定日志 ☠️剧毒之触：毒层 ≥5，敌人减速降防！
                     守卫：caster 玩家毒怪（`_caster_is_player and not _tgt_is_side_player`）+
                     层数门槛（n ≥ ps.layers 且条目存在才写 buff——原代码先判 list 非空
                     再判 n ≥ 首条 layers）留在挂点骨架；target buffs dict 由 ctx[\"tgt_buffs\"]
                     引用槽传入（调用侧 e.setdefault(\"buffs\", {})——与挂点侧逐字等价）
    dmg_mult_cond    ctx mult_kind 再扩 cap_kind 段（挂点16 _apply_mech_effect cap 段：
                     hunt_mark_cap/soul_mark_cap **双消费点 cap 段**——同 proc 已有挂点14
                     乘区段声明，一 proc 一族约束下 cap 段语义进同族新 ctx 分派 cap_kind：
                     hunt_mark/soul_mark——与 D2b shadow_dance_bonus stat_kind、
                     D3b soul_mark_cap 乘区段同模式）：
                     读 _ps.add（D0 回填 2）；add>0 才触发（零默认值铁律——缺字段 = cap
                     不放宽 = 原 3/5 上限）；**返回 base + add**（调用侧 min(返回, 叠加后
                     层数)——等价原 `min(3 + _extra_cap, ...)` 语义，base=3 是标记固有上限
                     （battle_mech 默认 cap 3 经 info.mark_cap 传入），非 proc 数值；
                     调用侧骨架保留 mech 判定（hunt_mark/soul_mark）+ mval>0 + 层数叠加
                     条件（_old + _mv > _now 才补层）
    poison_cap 挂点16 段不重复迁：D1 已把 poison_cap_up/poison_cap 整体迁 stack_cap_add
    族（挂点17 _poison_cap 本体族化）；挂点16 的 poison 段只调 _poison_cap() 读放宽后的
    上限（>5 才补层），非独立消费——本批只做 hunt_mark_cap/soul_mark_cap 两 cap 段。
"""
from __future__ import annotations

import os
import re

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
    # P2-D7 收尾补登 3 个"引擎旧通道直读"缺口（挂点7/8/9 未迁注册表，见下注释）
    "arcane_constant", "lian_duan_soft", "shadow_dance_cd",
    # （E 类 tick 族成员 focus_regen_summon/arcane_intuition/undead_faith/
    #   faith_overload_heal 已由 P2-D6 收编进 tick_regen/tick_mech_charge/tick_faith 族；
    #   P2-D7 收尾记录另 3 个"引擎旧通道"名单：arcane_constant/lian_duan_soft/
    #   shadow_dance_cd（挂点 7/8/9：_do_actor_skill MP 段/_combo_break/_set_skill_cd）
    #   消费点在 battle.py 仍是旧式 for 直读（非 run_proc_family 分发）——三挂点均为
    #   引擎旧 proc 通道（v169.7 数据驱动前身），P2 未迁入注册表（§5 挂点7/8/9 卡），
    #   数据/行为已完整（D0 回填），登记为"已消费但未注册表化"缺口——非静默空转，
    #   与 D 类真空转性质不同，统一收进 KNOWN_GAPS 启动校验豁免表（校验只问
    #   "不静默"，不强制每条都走注册表；引擎遗留旧通道列入缺口表防误删））
    # P2-D7 启动校验豁免 = D 类 4（真空转）+ 3（旧通道直读）7 个；
    # 45 声明已全覆盖 52-7；校验在文件尾 validate_proc_coverage()（ImportError 即红）
    #
    # P15 补登（2026-09-11）：reflection/破绽族走**第三条实现路径**——
    #   `PASSIVE_PROC` 表（game/data/battle2_rules.py）+ 装配层
    #   `class_mech_proc.apply_class_passives` 挂 actor.triggers（含 bar_field 解析段），
    #   **不经** passive_procs 的族执行器。功能已实装且有测试
    #   （tests/test_battle2_bar_procs.py 57 断言），非静默空转。
    #   ⚠️ 架构债：本表校验口径只认「PROC_FAMILIES 族执行器」这条旧路径，
    #   走新装配路径的 proc 必须逐条登记到这里才能过校验——新增此类 proc 时别忘了。
    "reflect_bar",
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

# ---- 3.1 dmg_mult_cond（疾风·极 speed_ratio_dmg：挂点4 _actor_dmg_mult）----
@register("dmg_mult_cond")
def _h_dmg_mult_cond(battle, ctx: dict, ps: dict, ps_name: str):
    """速度比 ≥ ratio → 伤害 ×(1+dmg_add)；奥术系/三系印记 → ×(1+mult)（条件伤害乘区族）。

    ctx 分派（mult_kind ∈ speed_ratio/arcane_mech/element_marks；缺省 speed_ratio 兼容挂点4）：
    - speed_ratio    速度比 ≥ ps.ratio → ×(1+ps.dmg_add)（疾风·极；原挂点4 _actor_dmg_mult）
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
    if _kind == "broken_extend":
        # 挂点18 破绽·极 broken_extend **延长段**（双消费点之二：乘区段 mult_kind=broken_break
        # 已在 D3b 收编本族）：目标 shaken dict（bar_trigger 后免疫窗口）→ immune_turns
        # +ps.extend。ctx["shaken"] = e_buffs["shaken"] dict 引用，副作用直落。
        # 读 _ps：extend；缺字段（≤ 0）= 无此行为（零默认值铁律；D0 回填 1）。
        _ext2 = int(ps.get("extend", 0) or 0)
        if _ext2 <= 0:
            return None  # 缺字段 = 无此行为
        _sh2 = ctx.get("shaken")
        if not isinstance(_sh2, dict):
            return None  # 无 shaken dict → 不触发（调用侧守卫已保证，双保险）
        try:
            _sh2["immune_turns"] = int(_sh2.get("immune_turns", 0) or 0) + _ext2
            return True
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.broken_extend", _sw_e)
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
    if _kind == "cap_kind":
        # 挂点16 _apply_mech_effect cap 段（hunt_mark_cap/soul_mark_cap **双消费点 cap 段**——
        # 同 proc 挂点14 乘区段已声明；一 proc 一族下 cap 段语义进本族新 ctx 分派
        # mult_kind=cap_kind + ctx cap_kind=hunt_mark/soul_mark——同 D2b stat_kind/
        # D3b soul_mark cap 段模式）
        _add = int(ps.get("add", 0) or 0)
        if _add <= 0:
            return None  # 缺字段 = cap 不放宽 = 原 3/5 上限（零默认值铁律；D0 回填 2）
        _kk = ctx.get("cap_kind")
        if _kk not in ("hunt_mark", "soul_mark"):
            return None
        # 返回 base+add（base=3 标记固有上限，非 proc 数值——battle_mech 默认 cap 3 经
        # info.mark_cap 传入）；调用侧 min(返回, 叠加后层数) = 原 `min(3+_extra_cap,...)`
        return 3 + _add
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
# 3b. dot_mult_cond / dot_weaken（P2-D5b：挂点15 _tick_actor_dots 毒 DOT 族）
#     毒 tick 乘区 + 毒层 → 目标减速降防。守卫（k==poison、caster 玩家、目标非玩家、
#     层数门槛）由挂点骨架保留；handler 只做数值/副作用。
# ============================================================
@register("dot_mult_cond")
def _h_dot_mult_cond(battle, ctx: dict, ps: dict, ps_name: str):
    """毒 DOT 伤害 ×(1+mult)（万毒归宗 poison_all_up；原挂点15 循环体逐字直搬）。

    ctx：mult（引用槽——当前 DOT 乘数，改写读回）。数值读 _ps：mult（D0 回填 0.35）；
    缺字段（mult ≤ 0）= 无此行为（零默认值铁律）。命中 → ctx[\"mult\"] *= 1+mult 并返回
    新值；首条 break 语义 = run_proc_family_pm 逐条（max=1 数据）等价。守卫
    （k==\"poison\" and _caster_is_player）由调用侧骨架保留。
    """
    _mult = float(ps.get("mult", 0.0) or 0.0)
    if _mult <= 0:
        return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 0.35）
    _nv = ctx["mult"] * (1.0 + _mult)
    ctx["mult"] = _nv
    return _nv


@register("dot_weaken")
def _h_dot_weaken(battle, ctx: dict, ps: dict, ps_name: str):
    """毒层 ≥ps.layers → 目标减速降防（剧毒之触 poison_weaken；原挂点15 循环体直搬）。

    守卫（_caster_is_player and not _tgt_is_side_player + 条目存在 + n ≥ 首条 layers）由调用侧
    骨架保留（原代码先判 list 非空再判 n ≥ 首条 layers——两判全在挂点，handler 不重判）。
    数值读 _ps：layers/spd_down/def_down（D0 回填 5/2/2）；缺字段（layers ≤0）=
    无此行为（零默认值铁律）。副作用写 ctx[\"tgt_buffs\"]（调用侧 e.setdefault(\"buffs\",{})
    引用槽——原 e.setdefault 在循环体内，每条目重取同 dict；调用侧取一次传入等价）：
    spd_down/def_down = max(现值, ps 值) + _weaken_spd_pct = max(现值, 0.30) /
    _weaken_def_pct = max(现值, 0.20)（**0.30/0.20 写死非零默认值**：减速降防幅度的引擎
    固有常量——desc「减速 30%、降防 20%」由这两键消费，无对应 _ps 键可读，非 proc 数值
    配置；spd_down/def_down 才是被动数值读 _ps）+ 固定日志 ☠️剧毒之触：毒层 ≥5，敌人
    减速降防！首条 break 语义 = run_proc_family_pm 逐条（max=1）等价。
    """
    _layers = int(ps.get("layers", 0) or 0)
    if _layers <= 0:
        return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 5）
    _sd = int(ps.get("spd_down", 0) or 0)
    _dd = int(ps.get("def_down", 0) or 0)
    if _sd <= 0 or _dd <= 0:
        return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 2/2）
    _tgt_b = ctx.get("tgt_buffs")
    if not isinstance(_tgt_b, dict):
        return None
    _tgt_b["spd_down"] = max(int(_tgt_b.get("spd_down", 0) or 0), _sd)
    _tgt_b["def_down"] = max(int(_tgt_b.get("def_down", 0) or 0), _dd)
    # v169.7 写死百分比键：减速 30%/降防 20% 幅度（引擎固有常量，随触发固化——原语义）
    _tgt_b["_weaken_spd_pct"] = max(float(_tgt_b.get("_weaken_spd_pct", 0) or 0), 0.30)
    _tgt_b["_weaken_def_pct"] = max(float(_tgt_b.get("_weaken_def_pct", 0) or 0), 0.20)
    _lg = ctx.get("logs")
    if isinstance(_lg, list):
        _lg.append("☠️ 剧毒之触：毒层 ≥5，敌人减速降防！")
    return True


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
                _hit = battle._elem_charge() >= battle._res_max(ctx.get("player") or battle._focus or {}, "element")
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
    if _kind == "elem_affinity":
        # 元素亲和 element_affinity（挂点18 _skill_hit_settle 引爆后置位段）：
        # 引爆结算（mech=element_burst*）后置位下次挂印 +1 标记——已学被动才置位。
        # 原循环体：`for...: self._elem_affinity_next = True; break`（ps 空 dict 纯置位型，
        # 学到即置位——无参数读取）；置位供挂印分支 6582 消费后清零（battle 属性随序列化）。
        # 读 _ps：零参数——但保留零默认值铁律：无 flag_kind/无 mech 前缀门槛 = 不触发。
        if battle is None:
            return None  # 无 battle 实例 = 无标记可置（探针/静态路径防御）
        try:
            battle._elem_affinity_next = True
            return True
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.element_affinity", _sw_e)
            pass
        return None
    if _kind == "broken_extend":
        # 破绽·极 broken_extend 延长段（挂点18 _skill_hit_settle shaken 触发免疫窗口段）：
        # 目标 shaken dict（_bs）免疫窗口 +ps.extend 刻（原循环体逐字直搬；首条 break——原
        # 循环尾 break，max=1 数据下 run_proc_family_pm 逐条分发只到首条即等效）。
        # 双消费点：乘区段（broken_mult，挂点14 mult_kind=broken_break）已由 D3b 收编同族
        # 不同 ctx 分派——本段只做延长副作用。ctx["shaken"] = 调用侧 bar_trigger 后的
        # e_buffs["shaken"] dict 引用（副作用直接落在该 dict）；日志 🥋破绽·极 原样保留。
        # 读 _ps：extend；缺字段（≤ 0）= 无此行为（零默认值铁律；D0 回填 1）。
        _ext = int(ps.get("extend", 0) or 0)
        if _ext <= 0:
            return None  # 缺字段 = 无此行为
        _bs = ctx.get("shaken")
        if not isinstance(_bs, dict):
            return None  # 无 shaken dict → 不触发（调用侧守卫已保证，双保险）
        try:
            _bs["immune_turns"] = int(_bs.get("immune_turns", 0) or 0) + _ext
            return True
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.broken_extend", _sw_e)
            pass
        return None
    if _kind == "dirge_ctrl_up":
        # 镇魂安魂 dirge_ctrl_up（挂点18 _skill_hit_settle 控制延长段）：挽歌系控制
        # （mech/cc/mech2 ∈ stun/freeze/silence/sleep/spd_down）对敌施加后 e_buffs
        # 控制键时长 +ps.add 刻（1.5 向下取整——半刻引擎不支持）。
        # 原循环体逐字直搬：遍历控制键找首个带时长键 → 加 add 刻 + 日志 + break；外层
        # for...break（首条 proc）。ctx["e_buffs"] = 调用侧 _tgt_buffs() 引用（副作用落
        # 该 dict）；日志串与原文逐字一致（原文硬编码 "+1 刻！"，data add=1 渲染同文）。
        # 读 _ps：add；缺字段（≤ 0）= 无此行为（零默认值铁律；D0 回填 1）。
        _add = int(ps.get("add", 0) or 0)
        if _add <= 0:
            return None
        _eb = ctx.get("e_buffs")
        if not isinstance(_eb, dict):
            return None
        try:
            for _ck in ("stun", "freeze", "silence", "sleep", "spd_down"):
                if _eb.get(_ck):
                    _eb[_ck] = int(_eb[_ck]) + _add
                    _lg = ctx.get("logs")
                    if isinstance(_lg, list):
                        _lg.append(f"🎵 {ps_name}：挽歌延长【{_ck}】控制 +1 刻！")
                    return True
            return None
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.dirge_ctrl_up", _sw_e)
            pass
        return None
    if _kind == "melody_duet":
        # 二重唱 melody_duet（挂点20 _skill_buff 吟唱段）：吟唱（外层 `if mech ==
        # "melody_chant":` 骨架守卫）→ 旋律强度 +ps.add（cap MELODY_CFG.max_stack）。
        # 原循环体（battle.py 6265-6277 迁移前副本）逐字直搬：guard = melody.name 非空
        # 且 stack > 0 才 +add；ctx["melody"] = 调用侧 _melody_state() 引用（副作用直接
        # 落该 dict——_melody 随战斗序列化）；ctx["max_stack"] = MELODY_CFG.max_stack
        # （核心常量族 battle_mech，调用侧取）；日志串与原文逐字一致（原文硬编码
        # "额外 +1！"与 "/5"——data add=1/max_stack=5 渲染同文）。
        # 读 _ps：add；缺字段（≤ 0）= 无此行为（零默认值铁律；D0 回填 1）。
        _add_md = int(ps.get("add", 0) or 0)
        if _add_md <= 0:
            return None
        _mel_md = ctx.get("melody")
        if not isinstance(_mel_md, dict):
            return None
        if not _mel_md.get("name") or int(_mel_md.get("stack", 0) or 0) <= 0:
            return None  # 原守卫：无旋律驻留/强度 0 → 不触发
        try:
            _cap_md = int(ctx.get("max_stack") or 5)
            _mel_md["stack"] = min(_cap_md, int(_mel_md.get("stack", 0) or 0) + _add_md)
            _lg = ctx.get("logs")
            if isinstance(_lg, list):
                _lg.append(f"🎶 {ps_name}：二重唱，旋律强度额外 +1！（{_mel_md['stack']}/5）")
            return True
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.melody_duet", _sw_e)
            pass
        return None
    if _kind == "heal_overflow_shield":
        # 圣光回响 heal_overflow_shield（挂点19 _skill_heal 治疗溢出转盾段）：
        # 真实溢出 = hp_before + heal − max_hp（heal 已 clamp 前修正量）；溢出 > 0 →
        # 盾 = int(溢出 ×ps.pct)（1 次/条），落 target_ally 侧 p_shields.overflow 或
        # self._add_shield("overflow", ...)（v122 队友语义）。原循环（挂点19 段逐字直搬）：
        # `for _pn,_ps in _passive_map(player)["proc"].get("heal_overflow_shield", [])` ——
        # heal_shield（庇护之光，非 52）同族异名保留在调用侧骨架（本批不迁）。
        # ctx["target_unit"]（被治疗者 dict 引用）、ctx["hp_before"]、ctx["heal"]、
        # ctx["target_ally"]（None=自己）、ctx["overflow_shield_turns"]（2，battle.py
        # 本地语义 = 原循环内写死 2）。日志 🛡️圣光回响… 原样保留。
        # 读 _ps：pct；缺字段（≤ 0）= 无此行为（零默认值铁律；D0 回填 0.5）。
        _pct_hos = float(ps.get("pct", 0.0) or 0.0)
        if _pct_hos <= 0:
            return None
        try:
            _tu_hos = ctx.get("target_unit")
            if _tu_hos is None:
                return None
            # 自己场景 _add_shield 落 player.shields（_p_shields_bag = actor.shields）；
            # 队友场景落 target_unit.p_shields——两路取 shields 袋口径一致（v101.28d 同源）
            _tu_hos.setdefault("shields", {})  # 保证 shields 袋存在（_add_shield 内 _p_shields_bag 读写）
            _ov_hos = int(ctx.get("hp_before") or 0) + int(ctx.get("heal") or 0) \
                - int(_tu_hos.get("max_hp", _tu_hos.get("hp", 0)) or 0)
            if _ov_hos <= 0:
                return None  # 无真实溢出 → 不触发
            _sh_gain = int(_ov_hos * _pct_hos)
            _tt = int(ctx.get("overflow_shield_turns") or 2)
            if ctx.get("target_ally") is not None:
                _sh_hos = _tu_hos.setdefault("p_shields", {})
                _cur_hos = _sh_hos.get("overflow")
                if _cur_hos:
                    _cur_hos["value"] = _cur_hos.get("value", 0) + _sh_gain
                    _cur_hos["turns"] = max(_cur_hos.get("turns", 0), _tt)
                else:
                    _sh_hos["overflow"] = {"value": _sh_gain, "turns": _tt}
            else:
                battle._add_shield("overflow", _sh_gain, _tt)
            _lg = ctx.get("logs")
            if isinstance(_lg, list):
                _lg.append(f"🛡️ {ps_name}：治疗溢出转化为 {_sh_gain} 点护盾！")
            return True
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.heal_overflow_shield", _sw_e)
            pass
        return None
    if _kind == "shaken_decay_half":
        # 破绽感知 shaken_decay_half（挂点23 _turn_start 破绽条衰减回补段）：turn_start_bars
        # 已按 bar 配置衰减 _bd.decay_per_turn（缺省 1.7），这里把半衰量回补（净效果 −0.85）。
        # 原循环体逐字直搬：e_buffs.shaken dict（val 键）→ val += int(decay_full / 2)；
        # 首条 break。ctx["e_buffs_shaken"] = 调用侧 self.e_buffs.get("shaken") dict 引用
        # （副作用直接落该 dict——e_buffs = enemy.buffs 代理，随战斗序列化）；
        # ctx["decay_full"] = 调用侧 bar_def 快照 _bd.decay_per_turn（缺省 1.7，原语义）。
        # 读 _ps：零参数（纯副作用型）——学到即回补；保留防御：shaken dict 缺失 = 不触发。
        # ps 零默认值铁律：add/pct 类数值 proc 缺字段=无此行为；本 proc 为纯置位型无参数
        # 消费（学到即回补）——沿用族内既有零参模式（elem_affinity：置位不读 _ps 数值）。
        _eb_shd = ctx.get("e_buffs_shaken")
        if not isinstance(_eb_shd, dict):
            return None
        try:
            _decay_full2 = float(ctx.get("decay_full") or 0) or 1.7
            _eb_shd["val"] = int(_eb_shd.get("val", 0) or 0) + int(_decay_full2 / 2)
            return True
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.shaken_decay_half", _sw_e)
            pass
        return None
    return None  # 未知 flag_kind = 不触发（调用侧未配置该 proc 的置位谓词）


# ============================================================
# 7c.2.1 melody_duet（P2-D5c：挂点20 _skill_buff 诗人吟唱段；flag_set_cond ctx flag_kind=melody_duet）
#     二重唱 melody_duet：吟唱（mech=melody_chant）→ 旋律强度 +ps.add（cap MELODY_CFG）。
#     原循环体（battle.py 6265-6277 迁移前副本）逐字直搬：外层 `if mech == "melody_chant":`
#     + try/except 骨架保留在调用侧；本 handler 只做单个 proc 条目的数值副作用。
#     ctx["melody"] = 调用侧 _melody_state() 引用（副作用直接落该 dict——_melody 随战斗序列化）；
#     ctx["max_stack"] = MELODY_CFG.max_stack（核心常量，调用侧取——battle_mech 常量族）。
#     guard：melody.name 非空 且 stack > 0 才 +add（原守卫）；日志 🎶二重唱… 原样保留。
#     读 _ps：add；缺字段（≤ 0）= 无此行为（零默认值铁律；D0 回填 1）。
#     注册表一 proc 一族（declare_proc 防重复）：melody_duet 走本族已注册的 flag_set_cond
#     分发表——族分派函数在 _h_flag_set_cond 内按 flag_kind 完整分发（melody_duet 分支加
#     在族主 handler 内，见上方 5b 区块）。本注释区为语义登记；无独立 handler。
# ============================================================
# 7. cc_break_cost / dr_cond（P2-D4a：挂点10 player_turn + 挂点11 _mitigate_chain）
#    受击减伤/免控族——本批风险最高（顺序语义 + 一次性 flag + 磐核溢出转盾）。
#    挂点多 if 严格先后（坚韧→坚城免眩晕→磐石免控 / 磐石族减伤顺序）由 battle.py 骨架保留；
#    handler 只做"单个 proc 的条件判定 + 副作用/返回值"，flag 读写一律 battle 属性
#    （getattr/setattr——_tenacity_left_n/_core_last_stand_used 随 to_state/from_state 序列化，
#    绝不可落 actor dict 局部）；ps 零默认值铁律（缺字段 = 无此行为）。
#    族粒度说明：zhan_yi_full_reduce/core_full 双消费点（挂点10 免控 + 挂点11 减伤）——
#    注册表一 proc 一族的约束下（declare_proc 防重复），双语义收敛进 dr_cond 单 handler，
#    ctx cc_kind（挂点10 免控）/dr_kind（挂点11 减伤）分派（同 D2b shadow_dance_bonus
#    stat_kind 模式；方案 §4.2 注"族粒度可收敛"+§6.1 双消费点参数化）。
# ============================================================

# ---- 7.1 cc_break_cost（坚韧 tenacity：战意挡控，3 次/场）----
@register("cc_break_cost")
def _h_cc_break_cost(battle, ctx: dict, ps: dict, ps_name: str):
    """战意 ≥ps.cost（默认 2）且剩余次数 >0 → 扣战意 + 次数-1，返回 True（被控照常行动）。

    语义 = 原 _tenacity_try_break 方法体逐字直搬（battle.py 4963-4983）——调用侧（battle.py
    挂点10 player_turn）保留外层骨架：`if (被控) and self._tenacity_try_break(player, logs)`，
    方法内部改查本族（原方法体 try/except 吞错留痕语义由 run_proc_family 保留）。
    一次性次数 _tenacity_left_n：随战斗序列化（to_state 'tenacity_left' / from_state 恢复）——
    读写一律走 battle 属性（getattr(battle, "_tenacity_left_n", 3)/setattr），不落 actor dict。
    数值读 _ps：cost（D0 回填 2）；缺字段（cost ≤ 0）= 无此行为（零默认值铁律）。
    ctx：logs（list，存在才追加）；读 battle._zhan_yi_n()/_p_stacks() 战意扣减。
    """
    _cost = int(ps.get("cost", 0) or 0)
    if _cost <= 0:
        return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 2）
    try:
        if battle._zhan_yi_n() < _cost:
            return None
        _left = int(getattr(battle, "_tenacity_left_n", 3))
        if _left <= 0:
            return None
        # 消耗战意 + 次数（原 _tenacity_try_break 顺序：先扣战意再次数-1）
        battle._p_stacks()["zhan_yi"] = max(0, battle._zhan_yi_n() - _cost)
        setattr(battle, "_tenacity_left_n", _left - 1)
        _lg = ctx.get("logs")
        if isinstance(_lg, list):
            _lg.append(f"🛡️ {ps_name}：消耗 {_cost} 层战意挣脱控制！（剩余 {int(getattr(battle, '_tenacity_left_n', 0))} 次）")
        return True
    except Exception as _sw_e:
        _swallow(battle, "passive_procs.tenacity", _sw_e)
        return None


# ---- 7.2 dr_cond（挂点11 _mitigate_chain 条件减伤聚合 + 挂点10 免控兜底）----
@register("dr_cond")
def _h_dr_cond(battle, ctx: dict, ps: dict, ps_name: str):
    """受击减伤/免控族（_mitigate_chain 磐核/战意持有档位聚合 + player_turn 免控兜底，
    ctx cc_kind/dr_kind 双分派——两 proc 双消费点同 handler 参数化）：

    免控段（挂点10 player_turn，cc_kind）：
    - stun_clear（zhan_yi_full_reduce）：战意 ≥ps.stacks → 移除 stun + 日志
    - cc_window（core_full）：磐核 ≥ps.stacks → p_buffs.cc_immune = max(现值, 1)
    减伤段（挂点11 _mitigate_chain，dr_kind，返回值累进挂点 _dr_pct）：
    - zy_full（zhan_yi_full_reduce 减伤段）：战意 ≥ps.stacks → 返回 reduce（+10%）
    - core_full（core_full 减伤段）：磐核 ≥ps.stacks → 返回 reduce（+20%）
    - per_core（core_reduce）：磐核 >0 → 返回 per_core × 磐核数（每枚 +2%）
    - last_stand（core_last_stand 已触发常驻段）：_core_last_stand_used 已置位 → 返回 reduce（+40%）
    - overflow_shield（core_overflow）：磐核 ≥ps.stacks → 溢出承伤转盾（_add_shield
      键 'core_overflow'，值 = dmg × shield_pct，turns 刻）——纯副作用，无返回值
    语义 = 原挂点10 两 for 循环体 + 挂点11 五段循环体逐字直搬（break 在循环尾，调用侧
    保留 for 骨架）；返回值由挂点 _dr_pct 累加（免控段/转盾段无返回值——只副作用）。
    一次性 flag：last_stand 段读 getattr(battle, "_core_last_stand_used", False)——
    该字段随 to_state/from_state 序列化（battle.py 1265/1555），读写走 battle 属性。
    数值读 _ps：stacks/reduce/per_core/shield_pct/turns（D0 已回填 10/0.10、5/0.20、
    0.02、0.40、3/0.80/3）；缺字段 = 无此行为（零默认值铁律）。
    ctx：logs（list，存在才追加）、dmg（int，转盾段用）；读 battle._zhan_yi_n()/
    _guard_core_n()；_add_shield 副作用走 battle（actor 为玩家/怪通用——原代码 RES/self
    副作用即 battle 口径，等价）。
    """
    _kind = ctx.get("cc_kind")
    if _kind == "stun_clear":
        # 坚城之姿免眩晕（挂点10）：战意满 → 移除 stun + 日志（原循环体直搬）
        _need = int(ps.get("stacks", 0) or 0)
        if _need <= 0:
            return None
        try:
            if battle._zhan_yi_n() >= _need:
                battle._p_buffs_bag().pop("stun", None)
                _lg = ctx.get("logs")
                if isinstance(_lg, list):
                    _lg.append(f"🛡️ {ps_name}：战意圆满，眩晕不侵！")
                return True
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.zhan_yi_full_reduce", _sw_e)
            pass
        return None
    if _kind == "cc_window":
        # 磐石之躯免控免疫窗口（挂点10）：磐核满 → cc_immune = max(现值, 1)
        _need = int(ps.get("stacks", 0) or 0)
        if _need <= 0:
            return None
        try:
            if battle._guard_core_n() >= _need:
                battle._p_buffs_bag()["cc_immune"] = max(int(battle._p_buffs_bag().get("cc_immune", 0) or 0), 1)
                return True
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.core_full", _sw_e)
            pass
        return None
    _kind = ctx.get("dr_kind")
    if _kind == "zy_full":
        _need = int(ps.get("stacks", 0) or 0)
        _red = float(ps.get("reduce", 0.0) or 0.0)
        if _need <= 0 or _red <= 0:
            return None
        try:
            if battle._zhan_yi_n() >= _need:
                return _red
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.zhan_yi_full_reduce", _sw_e)
            pass
        return None
    if _kind == "core_full":
        _need = int(ps.get("stacks", 0) or 0)
        _red = float(ps.get("reduce", 0.0) or 0.0)
        if _need <= 0 or _red <= 0:
            return None
        try:
            if battle._guard_core_n() >= _need:
                return _red
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.core_full", _sw_e)
            pass
        return None
    if _kind == "per_core":
        _per = float(ps.get("per_core", 0.0) or 0.0)
        if _per <= 0:
            return None
        try:
            _gn = battle._guard_core_n()
            if _gn > 0:
                return _per * _gn
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.core_reduce", _sw_e)
            pass
        return None
    if _kind == "last_stand":
        _red = float(ps.get("reduce", 0.0) or 0.0)
        if _red <= 0:
            return None
        try:
            if getattr(battle, "_core_last_stand_used", False):
                return _red
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.core_last_stand", _sw_e)
            pass
        return None
    if _kind == "overflow_shield":
        # 磐核 ≥ps.stacks → 溢出承伤转护盾（护盾 = 伤害额 ×shield_pct，turns 刻）——纯副作用
        _need = int(ps.get("stacks", 0) or 0)
        _spct = float(ps.get("shield_pct", 0.0) or 0.0)
        if _need <= 0 or _spct <= 0:
            return None
        try:
            if battle._guard_core_n() >= _need:
                _dmg_v = int(ctx.get("dmg") or 0)
                _ov_sh = int(_dmg_v * _spct)
                if _ov_sh > 0:
                    battle._add_shield("core_overflow", _ov_sh, int(ps.get("turns", 0) or 0))
                    _lg = ctx.get("logs")
                    if isinstance(_lg, list):
                        _lg.append(f"🪨 磐石之心：磐核 {battle._guard_core_n()} 枚，承伤转化 {_ov_sh} 点护盾！")
                return True
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.core_overflow", _sw_e)
            pass
        return None
    return None  # 未知 cc_kind/dr_kind = 不触发


# ============================================================
# 7b. revive_cond（P2-D4b：挂点12 _post_hp_lethal 致死复活链 3 proc）
#     一次性 flag（_death_pact_used/_berserk_revive_used/_stance_immortal_used）随战斗
#     序列化（to_state/from_state battle.py 1259-1264/1550-1554）——handler 读写一律
#     battle 属性（getattr/setattr），不落 actor dict 局部。ctx revive_kind 分派三段，
#     语义 = 原挂点 3 for 循环体逐字直搬（battle.py 10941-10988 迁移前副本）：
#     - death_pact_cond（death_contract 死亡契约）：信念 ≥faith_req 且存活骷髅在场 →
#       牺牲 1 只骷髅（尾骷髅，等价原 pop 语义）→ 置 _death_pact_used + 回 hp_pct HP；
#       无骷髅 → 仅日志（信念已足但无骷髅可代受），不消耗契约、返回 None
#       （原 continue 语义——未复活则继续查后续 proc 条目）
#     - berserk（berserk_revive 血怒·不灭）：狂暴态（骨架守卫 dual_form_active 在调用侧）
#       → 置 _berserk_revive_used + 清空战意 + 回 hp_pct HP
#     - stance（stance_immortal 铁誓·不动）：守护姿态（骨架守卫 B.stance_guard 在调用侧）
#       → 置 _stance_immortal_used + 移除 stance_guard + 清空战意 + 回满（hp_pct=1.0 满血）
#     挂点保留 if 骨架（actor.hp<=0 + flag + 形态/buff 守卫）与顺序链（契约先于血怒先于
#     铁誓）；handler 返回 True（复活成功 → 调用侧 break）或 None（未复活 → 循环尾）。
#     数值读 _ps：faith_req/hp_pct（D0 已回填 5/0.20、0.30、1.0）；缺字段（faith_req ≤0
#     或 hp_pct ≤0）= 无此行为（零默认值铁律）。flag 读写 battle 属性；companions/summons
#     增删走 battle（随从容器权威在 battle.companions）。_death_pact_used 与 v107 旧死亡
#     契约（proc death_pact 非 52）共享同一 flag 与致死钩子——旧通道保留（不注册不迁移）。
# ============================================================
@register("revive_cond")
def _h_revive_cond(battle, ctx: dict, ps: dict, ps_name: str):
    """致死复活族（一次性 flag 战斗属性序列化；三段 ctx revive_kind 分派）。"""
    _kind = ctx.get("revive_kind")
    _actor = ctx.get("actor")
    if _actor is None:
        return None
    if _kind == "death_pact_cond":
        # 死亡契约（牧师死灵线，proc death_contract）：信念 ≥faith_req 且存活骷髅在场
        _req = float(ps.get("faith_req", 0.0) or 0.0)
        _pct = float(ps.get("hp_pct", 0.0) or 0.0)
        if _req <= 0 or _pct <= 0:
            return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 5/0.20）
        try:
            _faith_v = float((_actor.setdefault("resources", {})).get("faith", 0) or 0)
            if _faith_v < _req:
                return None  # 信念不足 → 原 continue（不消耗、继续查后续条目）
            # 存活骷髅 = summons（kind=summon 视图）里 tid=skeleton 且 hp>0（原口径）
            _skels = [s for s in (battle.summons or [])
                      if s.get("tid") == "skeleton" and s.get("hp", 0) > 0]
            if not _skels:
                _lg = ctx.get("logs")
                if isinstance(_lg, list):
                    _lg.append("💀 死亡契约：信念已足但没有骷髅代受致命一击！")
                return None  # 原 continue——无骷髅可代受不消耗契约
            setattr(battle, "_death_pact_used", True)
            fallen = _skels.pop()  # 尾骷髅优先（等价原 pop 语义）
            (getattr(battle, "companions", None) or []).remove(fallen)
            _hp_new = max(1, int(_actor.get("max_hp", _actor.get("hp", 1))
                                 * _pct))
            _actor["hp"] = _hp_new
            _lg = ctx.get("logs")
            if isinstance(_lg, list):
                _lg.append(f"💀 死亡契约：信念 {_faith_v:.0f} 引动契约，"
                           f"{fallen.get('name', '骷髅')} 代受致命伤，"
                           f"你以 {_actor['hp']} HP 站起！")
            return True
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.death_contract", _sw_e)
            return None
    if _kind == "berserk":
        # 血怒·不灭（战士攻线·狂暴）：狂暴中首次致死 → 清空战意复活（每场 1 次）
        _pct = float(ps.get("hp_pct", 0.0) or 0.0)
        if _pct <= 0:
            return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 0.30）
        try:
            setattr(battle, "_berserk_revive_used", True)
            # 清空战意（血怒·不灭承诺「清空战意复活」）
            try:
                _actor.setdefault("stacks", {})["zhan_yi"] = 0
            except Exception:
                pass
            _hp_new = max(1, int(_actor.get("max_hp", _actor.get("hp", 1)) * _pct))
            _actor["hp"] = _hp_new
            _lg = ctx.get("logs")
            if isinstance(_lg, list):
                _lg.append(f"🔥 血怒·不灭！狂暴意志撑住了致命一击，你以 {_actor['hp']} HP 站起（战意已清空）！")
            return True
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.berserk_revive", _sw_e)
            return None
    if _kind == "stance":
        # 铁誓·不动（战士守线·守护姿态）：守护姿态下首次致命伤害免疫，随后清空全部战意
        _pct = float(ps.get("hp_pct", 0.0) or 0.0)
        if _pct <= 0:
            return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 1.0）
        try:
            setattr(battle, "_stance_immortal_used", True)
            try:
                _actor.setdefault("buffs", {}).pop("stance_guard", None)
            except Exception:
                pass
            try:
                _actor.setdefault("stacks", {})["zhan_yi"] = 0
            except Exception:
                pass
            _hp_new = max(1, int(_actor.get("max_hp", _actor.get("hp", 1)) * _pct))
            _actor["hp"] = _hp_new
            _lg = ctx.get("logs")
            if isinstance(_lg, list):
                _lg.append(f"🛡️ 铁誓·不动！守护姿态替你挡下致命一击（战意已清空）！")
            return True
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.stance_immortal", _sw_e)
            return None
    return None  # 未知 revive_kind = 不触发


# ============================================================
# 7c. tick 族（P2-D6：battle.py 顶部模块级 tick handler 内 4 proc 分支
#      focus_regen_summon/arcane_intuition/undead_faith/faith_overload_heal）
#      收敛为 3 个注册表族——tick_regen/tick_mech_charge/tick_faith。
#      模块级 handler 签名 (battle, actor, eff, logs) 与类方法不同：外层 tick
#      包装（被动回复族 / 奥术·魔剑充能族 / 信念衰减状态机 + 非 52 同族分支）
#      留在 battle.py 骨架原样；本族 handler 只做"该 proc 的数值/副作用"——
#      battle.py 骨架循环体改为：for 循环体直搬进 handler，骨架调
#      run_proc_family 查本族（与其余 11 族同机制）。
#      语义 = 原 4 for 循环体逐字直搬（含内层 try/except 吞错留痕）；ctx 带
#      logs（list，存在才追加）、crd_f（核心资源定义引用槽）；读 battle 现成
#      helpers（summons/_undead_count/_res_gain/focus_active）；数值读 _ps 零
#      默认值铁律（缺字段 = 无此行为）：gain（D0 回填 5）、gain/focus_gain
#      （D0 回填 1/1）、per_undead（D0 回填 0.15）、heal_up（D0 回填 0.30）。
#      返回值 None（副作用族——挂点不需要读回；原循环返回值未消费）。
#      注意 faith 段：undead_faith 置位 buffs.faith_exhausted 属后续状态机段
#      （在骨架）；本 handler 只做亡灵回 faith 与圣化乘算。
# ============================================================
@register("tick_regen")
def _h_tick_regen(battle, ctx: dict, ps: dict, ps_name: str):
    """每刻被动回复族（森之共鸣 focus_regen_summon：召唤物在场每刻回 energy +gain）。

    语义 = 原 _th_passive_heal 内 focus_regen_summon for 循环体逐字直搬
    （battle.py 294-332 迁移前副本；外层 try `if battle.summons:` 守卫由骨架保留）。
    读 _ps：gain；缺字段（gain ≤ 0）= 无此行为（零默认值铁律；D0 回填 5）。
    ctx：logs（list，存在才追加）；读 battle.summons/battle._res_gain(actor,...)。
    返回 None（副作用在 actor 资源袋 + ctx logs；原循环返回值未消费）。
    """
    _gain = int(ps.get("gain", 0) or 0)
    if _gain <= 0:
        return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 5）
    try:
        _actor = ctx.get("actor")
        if not _actor or not battle.summons:
            return None  # 召唤物不在场 → 不触发（原外层 if 守卫；骨架保留双保险）
        _sr_old = int(_actor.setdefault('resources', {}).get("energy", 0) or 0)
        _sr_new = battle._res_gain(_actor, "energy", _gain)
        _lg = ctx.get("logs")
        if _sr_new > _sr_old:
            if isinstance(_lg, list):
                _lg.append(f"🌳 {ps_name}：召唤物在场，专注充能 +{_gain}（{_sr_new}）")
        return None
    except Exception as _sw_e:
        _swallow(battle, "passive_procs.focus_regen_summon", _sw_e)
        return None


# ---- 7c.2 tick_mech_charge（奥术直觉 arcane_intuition：每刻奥术充能 +gain，focus 时 +focus_gain）----
@register("tick_mech_charge")
def _h_tick_mech_charge(battle, ctx: dict, ps: dict, ps_name: str):
    """每刻充能族（奥术直觉 arcane_intuition：奥术充能每刻 +gain，focus 态 +focus_gain）。

    语义 = 原 _th_mech_charge 内 arcane_intuition for 循环体逐字直搬
    （battle.py 334-373 迁移前副本；外层 mech 判定/stat 通道/非 52 arcane_regen
    分支由骨架保留）。读 _ps：gain/focus_gain/mech；缺字段（gain ≤ 0）= 无此行为
    （零默认值铁律；D0 回填 1/1，mech 缺省 arcane——ps 未显式声明时读 mech or
    "arcane" 的等价由骨架 ctx["mech"] 默认表达）。ctx：mech（缺省 "arcane"）、
    logs；读 battle._passive_map 消费经 run_proc_family（调用侧 for 骨架已取条目，
    handler 不再查表——ps/ps_name 由分发注入）；focus_active 经 ctx["focus_active"]
    注入（battle_modes 纯函数，骨架预置）。
    返回 None（副作用在 actor stacks + ctx logs）。
    """
    _gain = int(ps.get("gain", 0) or 0)
    if _gain <= 0:
        return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 1）
    try:
        _actor = ctx.get("actor")
        _mech = ctx.get("mech") or ps.get("mech") or "arcane"
        _gain2 = _gain
        _fa = ctx.get("focus_active")
        try:
            if callable(_fa) and _fa(_actor):
                _gain2 += int(ps.get("focus_gain", 0) or 0)
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.arcane_intuition", _sw_e)
            pass
        _before2 = int(_actor.setdefault('stacks', {}).get(_mech, 0) or 0)
        _actor.setdefault('stacks', {})[_mech] = ctx["mech_stack_gain"](_mech, _actor.setdefault('stacks', {}), _gain2)
        _lg = ctx.get("logs")
        if int(_actor.setdefault('stacks', {}).get(_mech, 0) or 0) > _before2:
            if isinstance(_lg, list):
                _lg.append(f"📖 {ps_name}：每刻充能自动+{_gain2}(当前 {_actor.setdefault('stacks', {})[_mech]} 层)")
        return None
    except Exception as _sw_e:
        _swallow(battle, "passive_procs.arcane_intuition", _sw_e)
        return None


# ---- 7c.3 tick_faith（亡灵祭仪 undead_faith + 信念·圣化 faith_overload_heal）----
@register("tick_faith")
def _h_tick_faith(battle, ctx: dict, ps: dict, ps_name: str):
    """信念每刻族（亡灵祭仪 undead_faith：亡灵在场每刻回 faith per_undead；
    信念·圣化 faith_overload_heal：过载回血 ×(1+heal_up)）——ctx faith_kind 双分派。

    语义 = 原 _th_faith_decay 内两 for 循环体逐字直搬（battle.py 404-457 迁移前
    副本；外层信念职业/decay 通道守卫与先产后衰状态机由骨架保留——本 handler 只
    做单个 proc 的数值/副作用，顺序链在骨架）。
    读 _ps：per_undead（D0 回填 0.15）/ heal_up（D0 回填 0.30）；缺字段（≤ 0）=
    无此行为（零默认值铁律）。
    ctx 分派：
    - faith_kind="undead"：battle._undead_count()>0 且 actor buffs 无
      faith_exhausted → faith += per_undead×n（上限 crd_f.max，ctx["crd_f"] 引用）；
      日志含 n 与 +gain。
    - faith_kind="overload"：ov_heal 引用槽 ×(1+heal_up) 改写读回；置 ctx
      ["foheal"]=True（骨架据 foheal 走圣化免力竭/无力竭分支）——原循环体置
      _foheal 的副作用等价由 ctx 槽承载。
    返回 None（副作用在 actor resources/buffs + ctx 槽 + logs）。
    """
    _kind = ctx.get("faith_kind")
    _actor = ctx.get("actor")
    if not _actor:
        return None
    if _kind == "undead":
        _per = float(ps.get("per_undead", 0.0) or 0.0)
        if _per <= 0:
            return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 0.15）
        try:
            _uf_n = battle._undead_count() if hasattr(battle, "_undead_count") else 0
            if _uf_n > 0 and not _actor.setdefault('buffs', {}).get("faith_exhausted"):
                _uf_gain = _per * _uf_n
                _crd = ctx.get("crd_f") or {}
                _f0 = float(_actor.setdefault('resources', {}).get("faith", 0) or 0)
                _actor.setdefault('resources', {})["faith"] = min(
                    float(_crd.get("max", 10) or 10), _f0 + _uf_gain)
                _lg = ctx.get("logs")
                if isinstance(_lg, list):
                    _lg.append(f"🕯️ {ps_name}：{_uf_n} 只亡灵在场，信念 +{_uf_gain:.2f}"
                               f"（{_actor.setdefault('resources', {})['faith']:.2f}）")
            return None
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.undead_faith", _sw_e)
            return None
    if _kind == "overload":
        _up = float(ps.get("heal_up", 0.0) or 0.0)
        if _up <= 0:
            return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 0.30）
        try:
            _ov = int(ctx.get("ov_heal") or 0)
            _ov = int(_ov * (1.0 + _up))
            ctx["ov_heal"] = _ov
            ctx["foheal"] = True
            return None
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.faith_overload_heal", _sw_e)
            return None
    return None  # 未知 faith_kind = 不触发
# 7c. counter_cond（P2-D5a：挂点13 _retaliations_and_buffs 受击反击聚合段 2 proc）
#     聚合语义（原挂点 10776-10800 双 for 循环逐字直搬，行为零变化）：
#     - counter_chance（以守为攻 磐石行者）：chance = max(所有条目 chance 0.35)；
#       mult = min(所有条目 mult 0.80)（80% 普攻）——原 for 无 break，全条目聚合
#     - counter_up（反击之王 磐石行者）：只取首条（原 `break` 在循环尾——max=1 数据
#       约束下等价）：chance += chance_add(0.25)；mult *= 1.0 + dmg_add(0.50)
#       （两被动皆学 = 0.60 概率 ×1.20 普攻）
#     本 handler = 单条目聚合贡献器：把某 proc 条目的数值聚合进 ctx 引用槽
#     （chance/mult 跨调用全程传递，ctx 数值槽铁律——与 poison_cap 累加同款），返回
#     None。proc 角色读 ps["proc"]（passive dict 自带键 = 数据权威，非内容名）。
#     数值读 _ps 零默认：chance/mult 或 chance_add/dmg_add 缺字段/≤0 = 该条目不聚合
#     （无此行为铁律；D0 已回填 0.35/0.80、0.25/0.50）。
#     cap min(chance, 0.9) + roll（random.random() < chance → _phys_retort/_hit_back/
#     日志/反击回气 +2）是聚合结果的**一次性消费**，留在挂点骨架（原代码聚合完才 roll
#     一次——逐条目 handler 无法预知后续条目，roll 天然属聚合收口点 = 调用侧）。
#     ctx：actor（被动方）、logs、rtgt（反击目标 = 攻击者，缺省 None）、chance/mult 槽。
#     挂点13 if 骨架（_rtgt 存活守卫 + 有 counter_chance/counter_up 条目才进）保留。
# ============================================================
@register("counter_cond")
def _h_counter_cond(battle, ctx: dict, ps: dict, ps_name: str):
    """受击反击聚合族：单条目聚合贡献（counter_chance max/min + counter_up 加乘），返回 None。"""
    _role = ps.get("proc")
    _actor = ctx.get("actor")
    if _actor is None:
        return None  # 无被动方 = 不聚合（挂点守卫已保证，双保险）
    if _role == "counter_chance":
        # 以守为攻：chance max（概率取最大）、mult min（伤害取最小 = 80% 普攻档）
        _ch = float(ps.get("chance", 0.0) or 0.0)
        _mu = float(ps.get("mult", 0.0) or 0.0)
        if _ch <= 0 or _mu <= 0:
            return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 0.35/0.80）
        try:
            ctx["chance"] = max(float(ctx.get("chance", 0.0) or 0.0), _ch)
            ctx["mult"] = min(float(ctx.get("mult", 1.0) or 1.0), _mu)
            return None
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.counter_chance", _sw_e)
            return None
    if _role == "counter_up":
        # 反击之王：+chance_add 概率、伤害 ×(1+dmg_add)（只首条——挂点循环尾 break）
        _ca = float(ps.get("chance_add", 0.0) or 0.0)
        _da = float(ps.get("dmg_add", 0.0) or 0.0)
        if _ca <= 0 or _da <= 0:
            return None  # 缺字段 = 无此行为（零默认值铁律；D0 已回填 0.25/0.50）
        try:
            ctx["chance"] = float(ctx.get("chance", 0.0) or 0.0) + _ca
            ctx["mult"] = float(ctx.get("mult", 1.0) or 1.0) * (1.0 + _da)
            return None
        except Exception as _sw_e:
            _swallow(battle, "passive_procs.counter_up", _sw_e)
            return None
    return None  # 未知 proc 角色 = 不聚合


# ============================================================
# 8. proc → 族 声明（P2-D1 试点 5 proc + P2-D2a crit_cond_add 4 proc +
#    P2-D2b stat_mult_cond 4 proc + P2-D3a dmg_mult_cond 扩展 2 + flag_set_cond 1 +
#    P2-D3b 5 proc；P2-D4a 6 proc（tenacity/zhan_yi_full_reduce/core_full/core_reduce/
#    core_last_stand/core_overflow——挂点10/11 受击减伤/免控族）；
#    其余 52 内 proc 由后续批次按序声明）
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
# P2-D4a：挂点10 player_turn + 挂点11 _mitigate_chain 受击减伤/免控族 6 proc
# （tenacity 坚韧 3 次/场挡控 → cc_break_cost；zhan_yi_full_reduce 坚城之姿 战意满减伤/免眩晕
#   → dr_cond(zy_full)+cc_immune_cond(stun_clear)；core_full 磐石之躯 磐核满减伤/免控窗口
#   → dr_cond(core_full)+cc_immune_cond(cc_window)；core_reduce 大地之肤 每磐核减伤
#   → dr_cond(per_core)；core_last_stand 不动如山 已触发常驻减伤 → dr_cond(last_stand)；
#   core_overflow 磐石之心 溢出转盾 → dr_cond(overflow_shield)——一次性 flag
#   _core_last_stand_used 首触发生产段在挂点12 区（3236/10569 不动如山补磐核）本批不迁）
declare_proc("tenacity", "cc_break_cost")
declare_proc("zhan_yi_full_reduce", "dr_cond")
declare_proc("core_full", "dr_cond")
declare_proc("core_reduce", "dr_cond")
declare_proc("core_last_stand", "dr_cond")
declare_proc("core_overflow", "dr_cond")
# P2-D4b：挂点12 _post_hp_lethal 致死复活链 3 proc → revive_cond 族（一次性 flag 族；
# death_contract 牧师死灵线信念≥5 牺牲骷髅复活 / berserk_revive 狂暴态首次致死清战意复活 /
# stance_immortal 守护姿态首次致命免疫清战意回满——三条 if 严格先后由 battle 骨架保留；
# flag _death_pact_used/_berserk_revive_used/_stance_immortal_used 随战斗序列化走 battle 属性）
declare_proc("death_contract", "revive_cond")
declare_proc("berserk_revive", "revive_cond")
declare_proc("stance_immortal", "revive_cond")
# P2-D6：挂点24 模块级 tick handler 区 4 proc → tick 族（tick_regen/
# tick_mech_charge/tick_faith；E 类 KNOWN_GAPS 成员收编，注册表 31 → 35）
# focus_regen_summon 森之共鸣 召唤物在场每刻回 energy +5（_th_passive_heal 分支）
# arcane_intuition 奥术直觉 每刻充能 +1 focus 时 +1（_th_mech_charge 分支）
# undead_faith 亡灵祭仪 亡灵每刻回 faith 0.15×n / faith_overload_heal 信念·圣化
# 过载回血 ×1.30（_th_faith_decay 两分支——同族 ctx faith_kind 分派）
declare_proc("focus_regen_summon", "tick_regen")
declare_proc("arcane_intuition", "tick_mech_charge")
declare_proc("undead_faith", "tick_faith")
declare_proc("faith_overload_heal", "tick_faith")
# P2-D5a：挂点13 _retaliations_and_buffs 受击反击聚合段 2 proc → counter_cond 族
# （以守为攻 counter_chance 35%×80% / 反击之王 counter_up +25%×+50%；chance max、mult min、
#   counter_up 加乘；cap 0.9 + roll + 反击回气 收口在挂点骨架——聚合结果一次性消费）
declare_proc("counter_chance", "counter_cond")
declare_proc("counter_up", "counter_cond")
# P2-D5b：挂点15 _tick_actor_dots 毒 DOT 族 2 proc（poison_all_up 万毒归宗 DOT ×(1+mult) →
# dot_mult_cond；poison_weaken 剧毒之触 毒层≥5 减速降防 → dot_weaken）+
# 挂点16 _apply_mech_effect cap 段 2 proc（hunt_mark_cap 追猎者 / soul_mark_cap 灵魂锁链
# cap 放宽 +add → dmg_mult_cond ctx cap_kind 分派——soul_mark_cap 双消费点：挂点14 乘区段
# mult_kind=soul_mark 已声明（D3b），cap 段本批同族新 ctx 分派；hunt_mark_cap 单消费点 cap 段）
declare_proc("poison_all_up", "dot_mult_cond")
declare_proc("poison_weaken", "dot_weaken")
declare_proc("hunt_mark_cap", "dmg_mult_cond")
# soul_mark_cap → dmg_mult_cond 已在 P2-D3b 声明（乘区段）；cap 段同族 ctx cap_kind 分派
# cc_immune 无独立族声明——zhan_yi_full_reduce/core_full 双消费点（挂点10 免控 + 挂点11
# 减伤）由同一 dr_cond 族 ctx cc_kind/dr_kind 分派（declare_proc 防重复：一 proc 一族）
# P2-D5c：挂点18/19/20/23 命中后置/治疗/增益副作用族 6 proc → flag_set_cond 族 ctx
# flag_kind 分派（挂点18 element_affinity 引爆置位 / broken_extend 延长段 / dirge_ctrl_up
# 挽歌控制延长；挂点19 heal_overflow_shield 溢出转盾；挂点20 melody_duet 吟唱 +add；
# 挂点23 shaken_decay_half 破绽衰减回补——broken_extend 双消费点：乘区段已 D3b 声明
# dmg_mult_cond（mult_kind=broken_break），延长段本批同族 flag_kind=broken_extend）
declare_proc("element_affinity", "flag_set_cond")
declare_proc("dirge_ctrl_up", "flag_set_cond")
declare_proc("melody_duet", "flag_set_cond")
declare_proc("heal_overflow_shield", "flag_set_cond")
declare_proc("shaken_decay_half", "flag_set_cond")
# broken_extend → dmg_mult_cond 已在 P2-D3b 声明（挂点14 乘区段）；延长段走同族新 ctx
# flag_kind=broken_extend 分派（declare_proc 防重复——不再重复声明）


# ============================================================
# 9. P2-D7 收尾：52 proc 全覆盖启动校验（方案 §6.2 P2-D7 / §7.2）
# ============================================================
# 防未来新增被动 proc 忘注册（静默空转）：
#   52 白名单 = skills.py 数据层全部 passive.proc 键（引擎唯一权威源，逐条 import 前
#   静态扫描）；每个 proc 必须二选一：
#     - 已在 PROC_FAMILIES 声明（含 FAMILY_HANDLERS 执行器就位），或
#     - 显式列入 KNOWN_GAPS（设计文档登记的已知缺口：D 类 4 真空转 faith_share/
#       finisher_up/poison_burst_up/poison_spread——单人不触发/数据缺陷/依赖在
#   battle_mech 文件所有权外，登记不静默；另有 3 个"引擎旧通道直读"缺口
#   arcane_constant/lian_duan_soft/shadow_dance_cd（挂点7/8/9 未迁注册表，
#   行为在 battle.py 旧 for 通道完整，登记不静默——见上 KNOWN_GAPS 注释）。
#   校验失败 → ImportError（import passive_procs 即失败 = 启动即红），防新增 proc
#   忘注册静默空转；同时也拦：声明表外名字、声明族缺执行器、KNOWN_GAPS 与声明
#   重复登记（需先想清楚到底走哪条）。
#   注意：本校验不 import engine/content（避免循环依赖/拖慢 import）——skills.py
#   是纯数据文件，用轻量 re 扫描其被动 proc 键即可拿到权威白名单。skills.py 行号
#   见 docs/REFACTOR_P2D_passive_proc_registry.md 附录 A。
_ALL_PASSIVE_PROCS = None


def validate_proc_coverage() -> dict:
    """52 全覆盖校验：返回 {whitelist, declared, gaps, unaccounted, extra_decl}。

    每个 52 白名单 proc 必须 ∈ PROC_FAMILIES（已收编）或 ∈ KNOWN_GAPS（登记缺口）；
    不满足 → ImportError。同时断言：声明集 ∩ KNOWN_GAPS = ∅、声明集 ⊆ 52、
    已声明族均有执行器（_FAMILY_PENDING 为空 = P2 全批完成后执行器全就位）。
    """
    global _ALL_PASSIVE_PROCS
    if _ALL_PASSIVE_PROCS is None:
        # 静态扫描 skills.py（纯数据，无 import）：抓 passive 块内的 proc 键
        _skill_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "..", "data", "skills.py")
        try:
            with open(_skill_path, encoding="utf-8") as _f:
                _sk_text = _f.read()
            _found = set(re.findall(r'["\']proc["\']\s*:\s*["\']([a-z_0-9]+)["\']', _sk_text))
        except OSError:
            # 数据文件缺失 → 无权威源可校验：宁可放过（等真实启动报缺文件），
            # 也不在 import 期抛误导性错（工程上 skills.py 永远存在）。
            _found = set()
        _ALL_PASSIVE_PROCS = _found
    _wl = _ALL_PASSIVE_PROCS
    _declared = set(PROC_FAMILIES)
    _gaps = set(KNOWN_GAPS)
    _unaccounted = sorted(_wl - _declared - _gaps)
    _extra = sorted(_declared - _wl)
    _dup = sorted(_declared & _gaps)
    if _unaccounted:
        raise ImportError(
            "passive_procs 52 全覆盖校验失败：以下 proc 未声明也未登记 KNOWN_GAPS，"
            f"未来新增被动忘注册会静默空转 —— 请 declare_proc 收编或登记缺口: "
            f"{_unaccounted}")
    if _extra:
        raise ImportError(
            f"passive_procs 声明了 52 白名单外的 proc（skills.py 无此被动）: {_extra} "
            "—— 声明表必须 ⊆ 52 白名单")
    if _dup:
        raise ImportError(
            f"passive_procs 声明与 KNOWN_GAPS 重复登记（需二选一）: {_dup}")
    if _FAMILY_PENDING:
        raise ImportError(
            f"passive_procs 有声明族缺执行器（P2 全批完成后应清零）: "
            f"{sorted(_FAMILY_PENDING)}")
    return {"whitelist": len(_wl), "declared": len(_declared),
            "gaps": len(_gaps), "unaccounted": len(_unaccounted),
            "extra_decl": len(_extra)}


# 模块 import 尾部即校验：52 全覆盖 or 已知缺口表不满足 = import 失败（启动即红）。
# 防未来 skills.py 新增 passive.proc 忘注册 —— 无注册 = 无触发 = 静默空转。
validate_proc_coverage()

