# -*- coding: utf-8 -*-
"""单一装配入口（S7）：`apply_game_content(actor)` —— 开战/进场内容装配的唯一收敛点。

规格：docs/ENGINE_CONTENT_SPLIT_PLAN.md §6.6（apply_game_content 收敛）+ §7 S7。

背景（S7 前的现状）
-------------------
开战处「并列调用」散落在命令层，共 4 处形态（命令层 6 个调用点 + 1 处内容侧自调用）：

    commands/combat.py:621-622    _open_battle 里 EP_apply(_a) + CM_apply(_a)
    commands/combat.py:2808/2851  PVP 路径同款两行
    commands/tower.py:151/156     塔层同款两行
    commands/battle_item_use.py:52   _b2config.load_game_defaults()
    services/class_mech_proc.py:2303/2309   apply_class_mech 内部串接 bar → cond

本模块把前四者收敛成**一个入口 + 一处顺序契约**：

    from .apply import apply_game_content
    apply_game_content(actor)                  # 开战装配（全部内容侧）
    ensure_engine_configured()                 # 引擎配置一次性装配（旧 load_game_defaults）

调用顺序契约（铁律，写死在 apply_game_content 里——命令层不得再自行排列）
--------------------------------------------------------------------------
    ① ensure_engine_configured()          引擎 hook + 规则表装配（幂等；先于一切内容装配）
                                          —— 等价旧 `saintess_engine.config.load_game_defaults()`
    ② equip_proc.apply_to_actor(actor)    装备/词条/武器特效 → triggers + bonus 分域（cap/cost）
                                          ⚠ 必须先于 ③：EP 的 bonus 分域是 ③ 职业资源渠道
                                            装配的输入（equip_proc 模块头「先于渠道装配」铁律）
    ③ class_mech_proc.apply_class_mech(actor)
                                          职业 mech 兑现（start_full / channels / 被动族 /
                                          磐核减伤 / 旋律 …）
                                          —— 其**内部**顺序为：bar_gain 注入 → mech 段 →
                                             apply_bar_procs → apply_cond_procs
                                             （即「bar_gain 须先于 mech 段」在此步内部满足）
    ④ bar_procs.apply_bar_procs(actor)    挂敌身条（BAR_INJECT_FIELDS → skill_hit 注入）
                                          幂等：同 key 不重复挂；③ 已挂时此处为空操作，
                                          显式保留以便该步可独立演进 / 单测直调
    ⑤ cond_procs.apply_cond_procs(actor)  技能条件乘区（info.cond → dmg_calc/heal_calc）
                                          幂等同上
    ⑥ food_proc.install_food_fx(actor, aids, logs)
                                          食物效果（仅当 ctx 传 aids 时执行；吃料理回合调用）

幂等的实现方式（与 plan §6.6 原文的差异，已实测论证）
----------------------------------------------------
plan §6.6 建议「由 apply.py 内部 `ctx["_applied_content"]` 标记保证幂等」。**实测后采用
actor 顶部标记键 `_content_applied`（本模块 `_MARK`）**，理由与被否方案如下：

  * ❌ 被否方案一「**不加标记**，靠各步自身幂等组合」：**实测证伪**。
    `battle_equip_proc.apply_to_actor` 的「事件型效果 → triggers」是
    `tr[ev].extend(effs)` **追加**语义（模块 docstring 自称幂等，仅对 bonus 分域成立）；
    对**带有效武器特效 / 事件型词条**的 actor 连调 2 次 → triggers 条目翻倍
    （见 `tests/test_apply_game_content.py` D 组，2 次装配后 actor 序列化长度 1828 → 2531）。
    仅 `cls_novice` 式白板 / 非事件装备恰好无差别 → 不能作为通用契约。
  * ❌ 被否方案二「`ctx` 标记」：调用方多数只有 actor（命令层 6 处），强制传 ctx 破坏单参签名。
  * ✅ 采用：actor 顶部 `_content_applied`。**副作用已知且已测试**：`serialize.to_state`
    会带上 actor 全量键 → 该标记（1 个 bool）会出现在战斗存档 / PVP 状态里
    （D3 组显式断言这一事实）。无任何数值/读取语义依赖它，S9 若要清掉需改引擎
    `serialize.py`（引擎改动，本步不做）。
  * 单次装配的**行为等价性**不受影响：E 组断言「新入口 vs 旧命令层并列调用」除该标记外
    **逐字节相同**（差异键集合 == {`_content_applied`}）。

  * 二次调用（幂等）时：`_content_applied` 命中 → 整链跳过 → 不追加、不翻倍。
  * 子步本身仍有「bar/cond 幂等（按 action+key 去重）」「bonus 分域覆盖写」性质，
    标记是**保险丝**而非唯一依赖。

方向性：本模块在**内容侧**（content_rules）——引擎 `framework/saintess_engine/` 不得 import 本模块
（门禁 `tests/test_engine_no_content.py`）；引擎只提供 `config` 挂载面。
"""
from __future__ import annotations

# 命令层旧调用点集合（供报告/S9 收口核对；不改行为）
LEGACY_CALL_SITES = (
    "game/commands/combat.py:621,622",
    "game/commands/combat.py:2808,2851",
    "game/commands/tower.py:151,156",
    "game/commands/battle_item_use.py:52",
    "game/services/class_mech_proc.py:2303,2309",
)

# 幂等标记键（落在 actor 顶部；见模块 docstring「幂等的实现方式」）
_MARK = "_content_applied"

# 最近一次装配的失败步（排障用；不写 actor、不进存档）
LAST_ERRORS: list = []
_MAX_ERRORS = 16


def ensure_engine_configured() -> None:
    """引擎配置**一次性**装配（幂等）——旧 `saintess_engine.config.load_game_defaults()` 的实体。

    = `game.bootstrap.load_engine_config()`：hook 面（公式/面板/技能查询/kind/mech_cfg）
      + 规则表（EFFECT_ACTIONS / EFFECT_RULES）。

    幂等：`mount()` 与 `load_game_rules()` 均为覆盖写，重复调用同一结果。

    另：**引擎动作执行器注册**也在本入口（import 即注册，2026-09-11）——
    `game/services/battle_team_procs.py` 提供团队/全队面幅与护盾/减伤/易伤/挡刀等
    内容侧动作，它们在技能施放时由引擎增益管线调起，必须先于任何战斗注册。
    放这里（而非开战装配）的原因：所有测试/入口都走 `ensure_engine_configured()`，
    注册面才完整。
    """
    from .. import bootstrap  # 惰性：装配期避免循环 import（见 game/bootstrap.py docstring）
    from ..services import battle_team_procs as _team_procs  # noqa: F401  (import 即注册)
    bootstrap.load_engine_config()


def apply_game_content(actor: dict, ctx: dict | None = None) -> dict:
    """**唯一**开战内容装配入口。顺序契约见模块 docstring（①…⑥）。幂等。

    :param actor: saintess_engine 侧 actor（命令层从 player dict 经 battle_bridge 得来）
    :param ctx:   可选上下文；仅识别 ``aids``（食物 aid 列表）与 ``logs``（播报累加）
    :return: actor（原对象，就地装配）

    容错铁律：每个子步独立 try/except —— 单步异常**不阻断**后续装配、不上抛
    （与旧命令层 `commands/combat.py` 的「装配异常不阻断开战」逐字一致，保证
    命令层改写为单行调用后行为不变）。失败项记入模块级 `LAST_ERRORS`（排障用；
    不写 actor、不进存档，故无状态副作用）。装配全部走完才落 `_content_applied` 标记。

    行为等价性：对同一 actor，本入口 == 旧命令层并列调用
    （`equip_proc.apply_to_actor` → `class_mech_proc.apply_class_mech`），
    除幂等标记外逐字节相同（`tests/test_apply_game_content.py` E 组对拍）。
    """
    if not actor:
        return actor
    if actor.get(_MARK):
        return actor  # 已装配（幂等保险丝；见模块 docstring「幂等的实现方式」）

    LAST_ERRORS.clear()

    def _step(name, fn, *args):
        try:
            fn(*args)
        except Exception as e:  # noqa: BLE001 —— 容错铁律（见 docstring）
            if len(LAST_ERRORS) < _MAX_ERRORS:
                LAST_ERRORS.append((name, repr(e)))

    # ① 引擎配置（幂等；先于一切内容装配）
    _step("ensure", ensure_engine_configured)

    # ② 装备/词条（bonus 分域必须先于 ③ 的渠道装配）
    from ..services.battle_equip_proc import apply_to_actor as _equip_apply
    _step("equip", _equip_apply, actor)

    # ③ 职业 mech 兑现（内部顺序：bar_gain → mech 段 → bar → cond）
    from ..services.class_mech_proc import apply_class_mech as _mech_apply
    _step("mech", _mech_apply, actor)

    # ④ 挂敌身条（幂等；③ 已挂时为空操作，显式保留以固定顺序契约）
    from ..services.battle_bar_procs import apply_bar_procs as _bar_apply
    _step("bar", _bar_apply, actor)

    # ⑤ 技能条件乘区（幂等同上）
    from ..services.battle_cond_procs import apply_cond_procs as _cond_apply
    _step("cond", _cond_apply, actor)

    # ⑥ 食物效果（可选：仅吃料理时装配）
    aids = (ctx or {}).get("aids")
    if aids:
        from ..services.battle_food_proc import install_food_fx as _food_apply
        _step("food", _food_apply, actor, list(aids), (ctx or {}).get("logs") or [])

    actor[_MARK] = True  # 幂等保险丝（装配全部走完才打；中途异常也不阻断 → 仍落标记）
    return actor
