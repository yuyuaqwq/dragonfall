# -*- coding: utf-8 -*-
"""v156 装备分系门禁 test_numeric_equip_split —— 武器/防具分系防退化（v2.0 §2.1/2.2）。

覆盖：
  1. 武器分系：物理武器（剑/匕/拳/弓）atk > matk；法系武器（法杖）matk > atk；盾防御向
  2. 防具分系：重甲 HP/def > 布甲；皮甲 spd > 重甲
  3. 向后兼容：不传 weapon_type/armor_family = 旧行为（36 调用点零破坏）
  4. 名册装备路径：generate_roster_equip 生成法杖 matk 高（职业匹配）

运行：python tests/test_numeric_equip_split.py（exit=0 全绿；由 run_numeric_tests.py 自动纳入门禁）
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
from data.plugins.dragonfall.game.core import stats as ST  # noqa: E402
from data.plugins.dragonfall.game.core.drops import generate_roster_equip  # noqa: E402

equip_stats = ST.equip_stats


def test_weapon_split():
    """武器分系：物理 atk 高、法系 matk 高、盾防御向"""
    for wt in ("sword", "dagger", "fist", "bow"):
        s = equip_stats("weapon", 24, "blue", weapon_type=wt)
        assert s["atk"] > s["matk"], f"{wt} 应物理 atk 高"
    s_staff = equip_stats("weapon", 24, "blue", weapon_type="staff")
    assert s_staff["matk"] > s_staff["atk"], "法杖应 matk 高"
    s_shield = equip_stats("weapon", 24, "blue", weapon_type="shield")
    assert s_shield["atk"] + s_shield["matk"] < 60, "盾应防御向（总值低）"
    print("  ✅ 武器分系")


def test_armor_split():
    """防具分系：重甲 HP/def 高、皮甲 spd 高"""
    heavy = equip_stats("armor", 24, "blue", armor_family="heavy")
    cloth = equip_stats("armor", 24, "blue", armor_family="cloth")
    leather = equip_stats("armor", 24, "blue", armor_family="leather")
    assert heavy["hp"] > leather["hp"] > cloth["hp"], "HP 应 重甲>皮甲>布甲"
    assert heavy["def"] > cloth["def"], "重甲 def 应高"
    boots_lea = equip_stats("boots", 24, "blue", armor_family="leather")
    boots_heavy = equip_stats("boots", 24, "blue", armor_family="heavy")
    assert boots_lea["spd"] > boots_heavy["spd"], "皮甲 spd 应高"
    print("  ✅ 防具分系")


def test_backward_compat():
    """向后兼容：不传参 = 旧行为"""
    s_old = equip_stats("weapon", 24, "blue")
    assert equip_stats("weapon", 24, "blue", weapon_type=None) == s_old, "weapon_type=None 应旧行为"
    assert equip_stats("armor", 24, "blue", armor_family=None) == equip_stats("armor", 24, "blue"), "armor_family=None 应旧行为"
    print("  ✅ 向后兼容")


def test_roster_equip():
    """名册装备：法杖 matk 高（职业匹配）"""
    eq = generate_roster_equip("eq_xue_tu_zhi_zhang")  # 学徒之杖（法系）
    assert eq["weapon_type"] == "staff", "学徒之杖应法杖"
    assert eq["stats"]["matk"] > eq["stats"]["atk"], "法杖 matk 应高"
    print("  ✅ 名册装备职业匹配")


if __name__ == "__main__":
    print("v156 装备分系门禁")
    test_weapon_split()
    test_armor_split()
    test_backward_compat()
    test_roster_equip()
    print("✅ 全部通过")
