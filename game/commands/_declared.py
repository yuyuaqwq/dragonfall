# -*- coding: utf-8 -*-
"""指令声明装配 —— 把 `data/command_specs.json` 的声明接到宿主注册。

背景（为什么要有它）
--------------------
命令层的正则原先有两处来源：各文件里的 `@filter.regex(<字面量>)`（真实注册）＋
`_registry.COMMAND_REGEX`（手工维护的镜像表，供停服 gate / 快捷转发 / 测试用）。
两处互相同步 → 一定会漂移，只能再配一个「表与装饰器必须 1:1」的测试盯着。

本模块让**声明成为唯一真源**：

    from ._declared import declared

    @declared("weekly_cmd")          # ← 正则从声明表取
    @require_player()
    async def weekly_cmd(self, event): ...

声明表 `game/data/command_specs.json` 同时供：正则注册、帮助/目录（desc/category/order）、
静态表派生（`_registry.COMMAND_REGEX`）、漂移自检（`saintess_engine.command.CommandRegistry`）。
**同一个 key 只能有一个来源** —— 迁到声明表的 key，必须从 `_registry` 的字面量表里删掉。

可拔插
------
只用声明表的指令走 `@declared(key)`；其余指令继续用 `@filter.regex(<字面量>)` 一字不改。
两者由 `_registry` 合并成同一张有效表，调用方（gate / 快捷转发）零感知。**迁移可增量**。

fail-closed
-----------
声明表缺失/为空/正则非法/找不到 key → **抛错**（不静默降级）。设计约定见框架
`version.py` 的同名条款：静默降级会变成「配了不生效」这类最难查的故障。
"""
from __future__ import annotations

import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_SPEC_PATH = os.path.join(os.path.dirname(_HERE), "data", "command_specs.json")

_CACHE = None


def spec_path() -> str:
    """声明表路径（测试/工具用）。"""
    return _SPEC_PATH


def load_specs() -> dict:
    """读声明表（原始 dict）。文件缺失/为空/JSON 坏 → 抛（fail-closed）。"""
    if not os.path.exists(_SPEC_PATH):
        raise FileNotFoundError("指令声明表不存在：%s" % _SPEC_PATH)
    with open(_SPEC_PATH, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not data:
        raise ValueError("指令声明表为空或格式不对：%s" % _SPEC_PATH)
    return data


def registry():
    """框架 `CommandRegistry`（懒构建 + 缓存；声明有问题直接抛）。"""
    global _CACHE
    if _CACHE is None:
        from saintess_engine.command import CommandRegistry
        reg = CommandRegistry.from_data(load_specs(), name="dragonfall.commands")
        problems = reg.validate()
        if problems:
            raise ValueError("指令声明表有问题（%s）：%s" % (_SPEC_PATH, "；".join(problems)))
        _CACHE = reg
    return _CACHE


def declared(key, **kwargs):
    """把声明表里该 key 的正则接到宿主注册（等价 `@filter.regex(声明正则)`）。

    * 单条正则时**逐字**使用声明值（与字面量装饰器等价，静态表断言不被动到）
    * 多条正则（别名）时用 `CommandRegistry` 的合并串 `(?:a)|(?:b)`
    * 声明表里没有该 key → 抛 KeyError（fail-closed，别让指令静默消失）
    """
    spec = registry().get(key)
    if spec is None:
        raise KeyError(
            "指令声明表里没有 %r —— 请在 %s 里补声明，或改回 @filter.regex(<字面量>)"
            % (key, _SPEC_PATH))
    from ._platform import register_regex
    return register_regex(spec.combined(), **kwargs)


def declared_pattern_map() -> dict:
    """`{key: 合并正则}`（派生给 `_registry.COMMAND_REGEX` 用）。"""
    return registry().pattern_map()


def declared_keys() -> tuple:
    return registry().keys()


def catalog() -> dict:
    """帮助/目录用：`{分类: [声明, ...]}`（仅 visible，按 order）。"""
    out = {}
    for spec in registry().visible():
        out.setdefault(spec.category or "其他", []).append(spec)
    return out
