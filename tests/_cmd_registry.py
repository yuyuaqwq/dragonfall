# -*- coding: utf-8 -*-
"""测试共享：命令正则 / 声明的统一扫描（**唯一实现**）。

背景
----
原先有**三份**各自实现的「扫 `game/commands/*.py` 的装饰器拿正则」逻辑：
`test_v87_command_matrix.py` / `test_v59_newline_cmd.py` / `test_v104_commands_system.py`。
三份 = 装饰器写法一变就要改三处（2026-09-11 引入 `@declared("key")` 时就是这样）。

统一到这里后，装饰器形态变化只改本文件。**三种来源全解析**：

* `@filter.regex(<字面量>)`      —— 逐字取字面量
* `@declared("<key>")`            —— 从 `game/data/command_specs.json` 取（声明是唯一真源）
* 两者都带 `priority=` 关键字       —— 一并带出

用法::

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _cmd_registry import pattern_map, patterns_with_meta, declared_usage

注意：本文件**不以 `test_` 开头**，不会被 `scripts/run_all_tests.py` 当测试跑。
"""
from __future__ import annotations

import ast
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(_HERE)
CMD_DIR = os.path.join(PLUGIN_DIR, "game", "commands")
SPEC_FILE = os.path.join(PLUGIN_DIR, "game", "data", "command_specs.json")

_FW = os.path.join(PLUGIN_DIR, "framework")
if _FW not in __import__("sys").path:
    __import__("sys").path.insert(0, _FW)


def _combine(patterns):
    """多条正则合成一条 —— 用框架实现（单一真源）；框架不可用 → 本地等价兜底。"""
    pats = [p for p in (patterns or ()) if p]
    if not pats:
        return ""
    if len(pats) == 1:
        return pats[0]
    try:
        from saintess_engine.command import combine_patterns
        return combine_patterns(pats)
    except Exception:                                        # noqa: BLE001
        return "|".join("(?:%s)" % p for p in pats)


def load_specs() -> dict:
    """声明表原始 dict（缺失/损坏 → 空 dict）。"""
    try:
        with open(SPEC_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def declared_patterns() -> dict:
    """`{声明key: 正则}`（来自声明表）。"""
    out = {}
    for k, v in load_specs().items():
        pats = v.get("patterns", v.get("pattern")) if isinstance(v, dict) else v
        if isinstance(pats, str):
            pats = [pats]
        c = _combine(pats or [])
        if c:
            out[str(k)] = c
    return out


def _iter_command_files():
    for fn in sorted(os.listdir(CMD_DIR)):
        if not fn.endswith(".py"):
            continue
        if fn.startswith("_"):        # _registry / _declared / _platform …数据/基建，非指令
            continue
        yield fn, os.path.join(CMD_DIR, fn)


def patterns_with_meta() -> dict:
    """`{方法名: (正则, priority, 文件)}`；两种装饰器写法都解析。

    `@declared("key")` 的 key 在声明表里找不到 → **跳过并记录**在 `MISSING`（fail-closed 可见，
    不静默产出空正则）。
    """
    declared = declared_patterns()
    found = {}
    for fn, path in _iter_command_files():
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                pat = None
                if (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)
                        and dec.func.attr == "regex" and dec.args
                        and isinstance(dec.args[0], ast.Constant)
                        and isinstance(dec.args[0].value, str)):
                    pat = dec.args[0].value
                    if pat in ("...", "…"):     # docstring 示例占位符
                        continue
                elif (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name)
                        and dec.func.id == "declared" and dec.args
                        and isinstance(dec.args[0], ast.Constant)
                        and isinstance(dec.args[0].value, str)):
                    key = dec.args[0].value
                    pat = declared.get(key)
                    if not pat:
                        MISSING.append((node.name, key, fn))
                        continue
                if pat is None:
                    continue
                prio = None
                for kw in dec.keywords:
                    if kw.arg == "priority" and isinstance(kw.value, ast.Constant):
                        prio = kw.value.value
                found[node.name] = (pat, prio, fn)
    return found


# `@declared("key")` 但声明表里没有该 key 的收集表（测试断言应为空）
MISSING = []


def pattern_map() -> dict:
    """`{方法名: 正则}`（最常用形态）。"""
    return {n: p for n, (p, _prio, _f) in patterns_with_meta().items()}


def declared_usage() -> dict:
    """`{方法名: 声明key}`（只含 `@declared` 写法）。"""
    found = {}
    for fn, path in _iter_command_files():
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name)
                        and dec.func.id == "declared" and dec.args
                        and isinstance(dec.args[0], ast.Constant)
                        and isinstance(dec.args[0].value, str)):
                    found[node.name] = dec.args[0].value
    return found
