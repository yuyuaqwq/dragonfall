# -*- coding: utf-8 -*-
"""域插件共享助手（`scripts/export_domains/*.py` 用）。

⚠️ 为什么单独一个文件：域插件**不许 import `export_game_package`**（那是宿主，导入它会触发
本目录的插件扫描 → 循环导入）。所以把「宿主里那几个公用小工具」在这里给一份**同一语义**的实现。

改动本文件等于改所有域插件的行为 → 只加不改（要改口径请连同受影响域一起验）。
"""
import importlib
import os
import sys

# 游戏仓根（scripts/export_domains/ → scripts/ → 仓根）
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def import_game_data(mod_name: str, src_root: str = REPO_ROOT):
    """import 游戏仓 `game/data/<mod>.py`（走包导入：源表之间有 `from .x import y` 相对导入）。"""
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    full = f"game.data.{mod_name}"
    if full in sys.modules:
        return sys.modules[full]
    return importlib.import_module(full)


def import_game_core(mod_name: str, src_root: str = REPO_ROOT):
    """import 游戏仓 `game/core/<mod>.py`（同上）。"""
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    full = f"game.core.{mod_name}"
    if full in sys.modules:
        return sys.modules[full]
    return importlib.import_module(full)


def sort_table(table: dict) -> dict:
    """外层按 key 字典序（稳定 → 幂等）；**条目内部字段顺序保持源顺序原样**。"""
    return {k: table[k] for k in sorted(table)}


def as_table(obj, name: str) -> dict:
    """取真源表并断言是 dict —— 静默取到 None 会让整个域变成空表而不报错。"""
    if not isinstance(obj, dict):
        raise TypeError(f"真源 {name} 应为 dict（得到 {type(obj).__name__}）—— 拒绝导出空表")
    return obj
