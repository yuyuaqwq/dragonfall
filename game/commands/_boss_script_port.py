# -*- coding: utf-8 -*-
"""Boss 剧本导演 · 宿主适配器（★ B8.2 线5，2026-09-13）。

背景
----
Boss 剧本导演的**代码**已归内容包：`<pkg>/content/flow/boss_script.py`（逐字端口，820 行）；
宿主副本 `game/commands/boss_script.py`（737 行）**已移出仓** →
`C:/Users/yuyu/AppData/Local/hermes/workspace/_retired/20260913_b82/game/commands/boss_script.py`。

端口把三处「宿主耦合」改成**调用方传参**（见端口文件头 ②）：

| 旧副本读什么（宿主） | 端口参数 | 不传时端口行为 |
|---|---|---|
| `C.MONSTER_MODS` / `C.INSTANCES`（内容聚合层） | `data=` | 包内 `monster_roster.json[*].mods` / `instances.json`（与真源逐项相等） |
| `..data.boss_phases.merge_phase_config`（阶段模板） | `phase_templates=` | `None` → 阶段模板不合并（**atk 乘区/换招/净化会退化**，与旧副本 import 成功的行为不同） |
| `C.build_monster`（援军构造，未进包） | `build_monster=` | `None` → 旧副本自带的 Boss×0.2 兜底（**援军变木桩**） |

本模块就是这三样的**宿主实现**：把宿主自己的聚合层 / 包内 boss_phases 域合并函数 /
宿主怪物构造器绑成一个与旧副本同形的接口，交给包内编排注入
（`game/commands/instance_battle.py:_script_api()`）。

用法
----
    from ._boss_script_port import script_api
    BS = script_api()                    # 形如旧 `game.commands.boss_script` 模块
    BS.boss_script_cfg(st, actor)        # data= 已绑好
    BS.make_script_hook(st)              # data=/phase_templates=/build_monster= 已绑好
    BS.make_script_event(st)
    BS._new_script_state() / BS._check_vuln_expire(...) / 任何私有符号 —— 原样透传

⚠️ 行为等价性：三样都按宿主真源给 → 与移出前的旧副本**逐项一致**（端到端对照见
`overnight/b82_L5_jobguide_boss.md`）。
"""
from __future__ import annotations

# 端口里「要注入宿主耦合」的工厂函数（其余符号原样透传）
_BOUND_FACTORIES = ("make_script_hook", "make_script_event")


def _deps() -> dict:
    """宿主三样耦合（每次取都活读聚合层，与旧副本的调用期读 `C.*` 同口径）。"""
    from .. import content as C
    from content.tables import merge_phase_config        # 包内 boss_phases 域（B8.2 线5 导出）
    return {"data": {"MONSTER_MODS": C.MONSTER_MODS, "INSTANCES": C.INSTANCES},
            "phase_templates": merge_phase_config,
            "build_monster": getattr(C, "build_monster", None)}


class _ScriptApi:
    """与旧 `game.commands.boss_script` 同形的门面（属性访问透传到包内端口）。"""

    def __init__(self):
        from content.flow import boss_script as _BS
        object.__setattr__(self, "_bs", _BS)

    def __getattr__(self, name):
        # 用 object.__getattribute__ 取 _bs，避免 __init__ 半程访问触发递归
        bs = object.__getattribute__(self, "_bs")
        fn = getattr(bs, name)
        if not callable(fn):
            return fn
        if name in _BOUND_FACTORIES:
            def _factory(st, **kw):
                d = _deps()
                d.update(kw)                  # 调用方显式传参优先
                return fn(st, **d)
            return _factory
        if name == "boss_script_cfg":
            def _cfg(st, actor, data=None):
                return fn(st, actor, data if data is not None else _deps()["data"])
            return _cfg
        return fn


def script_api() -> "_ScriptApi":
    """包内编排要的 `script_api`（宿主口）—— 见模块头。"""
    return _ScriptApi()
