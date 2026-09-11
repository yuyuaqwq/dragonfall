# -*- coding: utf-8 -*-
"""C10 兼容层：为旧差分探针测试提供 git HEAD 旧 handler 的 WEAPON_EFFECTS 等价访问。

C10 删净旧 handler 后 WEAPON_EFFECTS 恒空——旧探针（C2/C3/C7/C9 等）的
`WEAPON_EFFECTS[key][event]` OLD 分支改经本函数取 git HEAD 旧实现（等价比对仍成立）。
未删旧 handler 的历史版本（迁移前基线）直接回退 WEAPON_EFFECTS 本身。
"""
import os
import types
import sys as _sys


def _load_old_weapon_effects():
    """git HEAD 的 game/core/weapon_effects.py → 独立模块 WEAPON_EFFECTS（含旧 handler）。"""
    import subprocess
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for cand in (root, os.path.dirname(root)):
        if os.path.isdir(os.path.join(cand, ".git")):
            root = cand
            break
    try:
        h = subprocess.run(["git", "-C", root, "show", "HEAD:game/core/weapon_effects.py"],
                           capture_output=True, text=True, timeout=60)
        if h.returncode != 0:
            raise RuntimeError(h.stderr[:300])
    except Exception:
        return None
    src = h.stdout
    # 相对 import 改写为绝对（独立模块 exec 无法走包相对链）；ACT_TICK 取当前常量值。
    from game.core.constants import ACT_TICK as _ACT
    src = src.replace("from .constants import ACT_TICK", f"ACT_TICK = {_ACT!r}")
    src = src.replace("from ..engine import calc_damage", "from game.engine import calc_damage")
    src = src.replace(
        "def effect_data(battle, player, key: str) -> dict:",
        "def effect_data(battle, player, key: str) -> dict:\n"
        "    from game.data.weapon_effect_data import WEAPON_EFFECT_DATA as _T\n"
        "    return dict(_T.get(key) or {})")
    mod = types.ModuleType("game.core._we_old_head_probe")
    mod.__package__ = "game.core"
    _sys.modules[mod.__name__] = mod
    ns = {"__name__": mod.__name__, "__package__": mod.__package__}
    code = compile(src, "weapon_effects_old_head.py", "exec")
    exec(code, ns)
    return ns


_OLD_WE = None
_OLD_WE_TRIED = False


def old_weapon_effects():
    """返回旧 WEAPON_EFFECTS 表（含旧 handler fn）；失败/无 git 时返回当前（可能空）。"""
    global _OLD_WE, _OLD_WE_TRIED
    if _OLD_WE_TRIED:
        return _OLD_WE
    _OLD_WE_TRIED = True
    try:
        ns = _load_old_weapon_effects()
        if ns is not None:
            _OLD_WE = ns["WEAPON_EFFECTS"]
    except Exception:
        _OLD_WE = None
    return _OLD_WE


def old_handler(key, event):
    """旧 handler fn（迁移后 = git HEAD 实现；迁移前 = 当前 WEAPON_EFFECTS 直查）。"""
    from game.core.weapon_effects import WEAPON_EFFECTS as _cur
    if _cur:
        return _cur[key][event]
    old = old_weapon_effects()
    if old is not None:
        return old[key][event]
    raise KeyError(f"{key}/{event}: 无旧 handler 可用（需 git HEAD 含旧实现）")
