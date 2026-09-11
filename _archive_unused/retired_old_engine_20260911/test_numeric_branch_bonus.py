# -*- coding: utf-8 -*-
"""v156 转职分支差异化门禁 test_numeric_branch_bonus —— 职业×分支属性成长防退化（v2.0 §3）。

覆盖：
  1. 战士：攻线（狂战士）atk > 守线（盾卫士），守线 hp/def > 攻线（定位交换）
  2. 法师：攻线（元素使）matk > 守线（奥术学者），守线 mp > 攻线
  3. 刺客：攻线（影舞者）crit 加成（加法 +4%）
  4. 未配置职业回退通用档（见习 atk×1.06）

运行：python tests/test_numeric_branch_bonus.py（exit=0 全绿；由 run_numeric_tests.py 自动纳入门禁）
"""
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))          # tests/
_PLUGIN_DIR = os.path.dirname(_SCRIPT_DIR)                        # dragonfall/
_SCRIPTS_DIR = os.path.join(_PLUGIN_DIR, "scripts")
for _p in (_SCRIPTS_DIR, _PLUGIN_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PLUGIN_DIR, "tests", "test_game_data.db"))

from numeric_lib.env import setup_env  # noqa: E402,F401
setup_env()
from data.plugins.dragonfall.game import engine as E  # noqa: E402


def panel(cls, lv, evolve_path):
    return E.player_base_stats(cls, lv, tier=2, evolve_path=evolve_path)


def test_warrior():
    z1, z2 = panel("战士", 60, 1), panel("战士", 60, 2)
    assert z1["atk"] > z2["atk"], "狂战士 atk 应更高"
    assert z2["def"] > z1["def"], "盾卫士 def 应更高"
    assert z2["hp"] > z1["hp"], "盾卫士 hp 应更高"
    print("  ✅ 战士攻守线")


def test_mage():
    f1, f2 = panel("法师", 60, 1), panel("法师", 60, 2)
    assert f1["matk"] > f2["matk"], "元素使 matk 应更高"
    assert f2["mp"] > f1["mp"], "奥术学者 mp 应更高"
    assert f2["hp"] > f1["hp"], "奥术学者 hp 应更高"
    print("  ✅ 法师攻守线")


def test_assassin_crit():
    c1 = panel("刺客", 60, 1)
    assert c1.get("crit", 0) > 0.20, "影舞者 crit 应 > 基础 20%"
    print("  ✅ 刺客 crit 加法")


def test_fallback():
    nov = panel("见习", 60, 1)
    nov0 = panel("见习", 60, 0)
    assert nov["atk"] > nov0["atk"], "未配置职业应回退通用档 atk×1.06"
    print("  ✅ 通用档回退")


if __name__ == "__main__":
    print("v156 转职分支差异化门禁")
    test_warrior()
    test_mage()
    test_assassin_crit()
    test_fallback()
    print("✅ 全部通过")
