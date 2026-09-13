# -*- coding: utf-8 -*-
"""saintess_engine 食物战斗效果装配层（game/services/battle_food_proc.py，N10-B7）。

saintess_engine 包外（引擎零知识——本模块 import 引擎/数据，引擎不 import 本模块）。
职责：把战斗内吃下的效果料理（foodfx:aid,...）→ actor["triggers"] 声明
（N8 事件总线消费）+ effects period 周期声明（schedule 时间驱动每刻跳），
使 17 种战斗料理效果在 saintess_engine 战斗中生效（N10-B7 缺口补完）。

架构对齐 docs/DESIGN_N10B7_food_effects.md + services/battle_equip_proc.py
（affix 迁移先例）：
- 命中/受击/乘区触发类 → actor["triggers"] = {事件: [效果 dict]}，效果 dict
  复用 we_* 扩展动作（we_affix_dot/defdown/bonus/element/counter/reflect/
  dmg_mult_cond/taken_mult_cond/extra_dmg）——名词执行器与 affix 词条同源，
  每动作全项目只写一次。
- 周期恢复类（regen/meditate/dawn_crown）→ actor["effects"][key] period 声明
  （schedule 周期段时间驱动每刻跳，对齐 battle_item_use hot: regen_hot 先例；
  **不是 turn_start 行动帧**——鱼鱼 2026-09-09 追问定稿：描述"每刻回复"=
  时间驱动 1 刻一跳，同旧引擎 tick 卡语义）。
- actor["food_effects"] 容器保留（吃重复去重/图鉴展示仍读它），挂 triggers 幂等。

数值权威 = game/data/food_effect_data.py FOOD_EFFECT_PARAMS（读表零默认值：
缺字段 = 无此行为，不复制硬编码）。安装入口 battle_item_use.translate foodfx
分支（吃料理唯一入口，_instance_router + _restore_battle 全覆盖）。

★ B10-L4 收口（2026-09-13）：本文件 = **委托薄壳**
--------------------------------------------------------
实现真源 = 包内 `games/orlandia/content/mech/food_proc.py`（B8 端口，逐字逐字搬自本文件；
唯一改动两处：读表口 → 包内 `content/data/food_effects.json`（导出器单向产出，19 条逐条相等）、
补 `import os` + `_HERE`）。逐函数对拍（`overnight/_b10_l4_recon.py`）：7 个同名函数里
5 个「去 docstring 后逐行相同」，2 个（`_food_params` 读表口 / `install_food_fx`）差异均为
已记录的端口改写；三入口（`food_trigger_decls` / `food_period_decl` / `install_food_fx`）
对拍逐字段相等（`overnight/_b10_l4_probe_BEFORE.txt`）⇒ 宿主那份是**纯冗余副本**。
生产路径早在 B8 就切到包内（`content/mech/item_use.py:191` → `content/mech/food_proc`），
宿主这份只剩测试消费者。

本文件只「再导出 + 一行委托」，名字 / 签名一字不变 —— 调用点零改动：

    tests/test_apply_game_content.py   FOOD.food_trigger_decls / FOOD.food_period_decl
    （`game/content_rules/apply.py` 只在 docstring 里引用本路径）

**唯一形态差异**：包内 `install_food_fx` 不调 `install_ext_actions()`（包内 we_* 动作是
`content/mech/equip.py` **import 期** `@register_action` 注册，`content/apply.py` 已把七族列全）
—— 本文件改委托后同样不再运行时注册，效果等价（包加载即注册；见 `overnight/b10_l4_snap.py`
G1「关键名都在」断言）。

等价证据：`overnight/b10_l4_snap.py`（改造前后逐字节快照）·
          `overnight/B10-L4-cond-food-wb-bridge.md`。
"""
from __future__ import annotations

_PKG = None          # 包内 `content.mech.food_proc` 模块缓存（惰性——import 期不碰包）


def _pkg():
    """包内 `content.mech.food_proc`（食物效果装配唯一实现源）：首调加载包，之后走缓存。

    包装载口 = `game/bootstrap.package_apply()`（本进程唯一，幂等）。失败**抛**、不静默降级
    （静默降级 = 吃了效果料理什么都不发生，比报错难查得多）。
    """
    global _PKG
    if _PKG is None:
        from .. import bootstrap as _bootstrap
        _bootstrap.package_apply()
        from content.mech import food_proc as _m
        _PKG = _m
    return _PKG


def food_trigger_decls(aid: str) -> dict:
    """food aid → {old_event: [效果 dict]}；未知 aid → {}（委托薄壳，实现见包内）。"""
    return _pkg().food_trigger_decls(aid)


def food_period_decl(aid: str):
    """周期恢复类 → effects 条目 period 声明（委托薄壳，实现见包内）。"""
    return _pkg().food_period_decl(aid)


def install_food_fx(actor: dict, aids: list, logs: list) -> None:
    """把吃下的料理 aid 列表装配进 actor（幂等）—— 委托薄壳，实现见包内。"""
    return _pkg().install_food_fx(actor, aids, logs)


# 模块级表 / 私有读表口：PEP 562 惰性再导出（import 期不碰包）
_LAZY = ("_EVENT_MAP", "_PERIOD_FOOD", "_map_event", "_chance_pct", "_fp", "_food_params")


def __getattr__(name):
    """PEP 562：转发到包内那份（表/读口同一对象 —— 双源已收口）。"""
    if name in _LAZY:
        return getattr(_pkg(), name)
    raise AttributeError("module %r has no attribute %r" % (__name__, name))


__all__ = ["food_trigger_decls", "food_period_decl", "install_food_fx"]
