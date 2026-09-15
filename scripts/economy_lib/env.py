# -*- coding: utf-8 -*-
"""economy_lib 环境引导（与 numeric_lib/env.py 同口径）

把 qqbot 根 + 插件目录加进 sys.path，GWEN_GAME_DB 默认测试库，
stdout UTF-8。import economy_lib 即完成（幂等）。
"""
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))        # scripts/economy_lib/
_SCRIPTS_DIR = os.path.dirname(_SCRIPT_DIR)                     # scripts/
_PLUGIN_DIR = os.path.dirname(_SCRIPTS_DIR)                     # dragonfall/
_TESTS_DIR = os.path.join(_PLUGIN_DIR, "tests")
_QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN_DIR)))  # qqbot/

for _p in (_PLUGIN_DIR, _SCRIPTS_DIR, _TESTS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ★ P5E-DELETE（2026-09-15，删壳批）：`economy_lib.core` 的取件口已从宿主壳
#   （`game.core.stats` / `game.core.drops` / `game.content`）改到**包内真源**
#   （`content.stats` / `content.drops` / `content.facade`）—— 终态唯一落点。
#   ⇒ 这里必须把「包目录」（`content` 的父目录 = `<插件>/framework/games/<包>/`）
#   与「引擎包目录」（`<插件>/framework`）摆进 sys.path，口径与
#   `tests/_engine_harness.py:44/54` 一致。**不写死包名**：取 `framework/games/*`
#   里声明表（`content/data/commands.json`）最大的那个（与全量 runner / 注册门禁同规则）。
_FW_DIR = os.path.join(_PLUGIN_DIR, "framework")
try:
    import json as _json
    _games = os.path.join(_FW_DIR, "games")
    _best, _best_n = "", -1
    for _name in sorted(os.listdir(_games)):
        _decl = os.path.join(_games, _name, "content", "data", "commands.json")
        if not os.path.isfile(_decl):
            continue
        with open(_decl, encoding="utf-8") as _fh:
            _n = len(_json.load(_fh) or {})
        if _n > _best_n:
            _best, _best_n = os.path.join(_games, _name), _n
    _PKG_DIR = _best
except Exception:                                               # noqa: BLE001
    _PKG_DIR = ""
for _p in (_PKG_DIR, _FW_DIR):
    if _p and os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("GWEN_GAME_DB", os.path.join(_TESTS_DIR, "test_game_data.db"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def setup_env():
    """显式调用入口（幂等）。"""
    return True
