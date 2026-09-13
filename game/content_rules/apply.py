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


def _pkg_apply():
    """包内 `content.apply` 模块（B8 真源；经 `game.bootstrap` 唯一加载口）。"""
    from .. import bootstrap
    return bootstrap.package_apply()


def __getattr__(name):
    """PEP 562 模块级转发：`LAST_ERRORS` 等**排障符号**的真源已归包 —— 不留第二份。

    留一份恒空的名字会让 D4 那类断言（失败步必须记进 LAST_ERRORS）变成**假绿**。
    """
    if name == "LAST_ERRORS":
        return getattr(_pkg_apply(), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def ensure_engine_configured() -> None:
    """引擎配置**一次性**装配（幂等）—— 旧 `saintess_engine.config.load_game_defaults()` 的实体。

    ★ B8 切消费端（2026-09-13）：实现已归内容包，本函数是**薄壳**，一行委托
    `bootstrap.load_engine_config()`（= 先引 `game.content` 保装载顺序，再加载包；包内
    `content/apply.install_engine()` 做 hook 面 + 规则表 + 动作注册）。旧实现三件事的去处：
      ① hook 面（公式/面板/技能查询/kind/mech_cfg）→ 包内 `content/apply.install_engine()`
      ② 规则表（EFFECT_ACTIONS / EFFECT_RULES）→ 包内 `content/mech/params.py`（`load_game_rules`）
      ③ 动作执行器注册（`battle_team_procs` / `battle_element_procs`，import 即注册）
         → 包内 `content/mech/{team,element}_procs.py`，由 `content/apply.py` 的 import 块列全
           （少 import 一族 = 那族动作在 `fire()` 里**静默跳过**，见该文件注释）
    """
    from .. import bootstrap
    bootstrap.load_engine_config()      # 不直调 package_apply()：那会绕过 §8-R1 的装载顺序


def apply_game_content(actor: dict, ctx: dict | None = None) -> dict:
    """**唯一**开战内容装配入口。★ B8 切消费端（2026-09-13）：实现已归包 —— 本函数是**薄壳**，
    一行委托包内 `content/apply.py:apply_game_content`（逐字端口，顺序契约 ①→⑥ 一步不少，
    含 ⑥ 食物效果 —— B8 补齐，见 `content/mech/food_proc.py`）。

    :param actor: saintess_engine 侧 actor（命令层从 player dict 经 battle_bridge 得来）
    :param ctx:   可选上下文字典：``aids``（食物 aid 列表）/ ``logs``（播报累加）
    :return: actor（原对象，就地装配）

    行为等价性：包内那份对同一 actor 与旧命令层并列调用
    （`equip_proc.apply_to_actor` → `class_mech_proc.apply_class_mech`）除幂等标记外逐字节相同
    （`tests/test_apply_game_content.py` E 组对拍）；⑥ 食物与真源 19/19 逐项相同
    （`overnight/_b8_verify_food.py`）。容错铁律（单步异常不阻断）、幂等标记 `_MARK`、
    `LAST_ERRORS` 都在包内那份里 —— 本模块经 `__getattr__` 转发排障符号，不留第二份。
    """
    return _pkg_apply().apply_game_content(actor, ctx)
