# -*- coding: utf-8 -*-
"""环境引导：路径 / GWEN_GAME_DB / stdout 编码（所有 numeric_lib 模块与 CLI 共用）。

与 tests/numeric_sim.py 同口径：GWEN_GAME_DB 默认 tests/test_game_data.db
（尊重调用方预置的私有库，用 setdefault 不覆盖）。
"""
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))        # scripts/numeric_lib/
_SCRIPTS_DIR = os.path.dirname(_SCRIPT_DIR)                     # scripts/
_PLUGIN_DIR = os.path.dirname(_SCRIPTS_DIR)                     # dragonfall/
_TESTS_DIR = os.path.join(_PLUGIN_DIR, "tests")
_QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN_DIR)))  # qqbot/

for _p in (_QQBOT_DIR, _PLUGIN_DIR, _TESTS_DIR, _SCRIPTS_DIR):
    if _p not in sys.path:
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
    """显式调用入口（幂等）：import numeric_lib 后无需调用，环境已就绪。"""
    return True