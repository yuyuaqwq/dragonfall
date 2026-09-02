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
