# -*- coding: utf-8 -*-
"""v156 阶段 3·技能经济：mp_budget 空蓝轮数单测。

覆盖：
  1. 法系（法师）空蓝轮数 < 战士（法系耗蓝快）
  2. 同一职业满装（gear）空蓝轮 ≥ 裸装（满装不劣于裸装；装备无 MP 属性 → max_mp 恒等）
  3. rotation 参数可覆盖默认 ROTATIONS
  4. per_round_mp <= mp_regen 时 empty_rounds == float('inf')

运行：python tests/test_numeric_mp_budget.py（exit=0 全绿；由 run_numeric_tests.py 自动纳入门禁）
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
from numeric_lib.player import mp_budget  # noqa: E402
from numeric_lib.gear import gear_loadout  # noqa: E402

passed, failed = 0, 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}  {detail}")


def main():
    print("【1/4 重耗蓝职业空蓝轮更小（拳师崩拳18mp vs 战士嗜血斩10mp）】")
    b_qs = mp_budget("拳师", 24, None)
    b_zs = mp_budget("战士", 24, None)
    print(f"  拳师: max_mp={b_qs['max_mp']:.0f} 每轮耗蓝={b_qs['per_round_mp']:.1f} 空蓝轮={b_qs['empty_rounds']:.1f}")
    print(f"  战士: max_mp={b_zs['max_mp']:.0f} 每轮耗蓝={b_zs['per_round_mp']:.1f} 空蓝轮={b_zs['empty_rounds']:.1f}")
    check("拳师每轮耗蓝 > 战士（崩拳18mp 嗜血斩10mp）",
          b_qs["per_round_mp"] > b_zs["per_round_mp"],
          f"qs={b_qs['per_round_mp']} zs={b_zs['per_round_mp']}")
    check("拳师空蓝轮 < 战士", b_qs["empty_rounds"] < b_zs["empty_rounds"],
          f"qs={b_qs['empty_rounds']} zs={b_zs['empty_rounds']}")

    print("【2/4 满装 vs 裸装：满装空蓝轮 ≥ 裸装（装备无 MP 属性，max_mp 恒等）】")
    gear = gear_loadout(24, "solo_mid")
    b_naked = mp_budget("战士", 24, None)
    b_gear = mp_budget("战士", 24, gear)
    print(f"  裸装: max_mp={b_naked['max_mp']:.0f} 空蓝轮={b_naked['empty_rounds']:.1f}")
    print(f"  满装: max_mp={b_gear['max_mp']:.0f} 空蓝轮={b_gear['empty_rounds']:.1f}")
    check("满装 max_mp ≥ 裸装（装备无 MP 属性 → 恒等）", b_gear["max_mp"] >= b_naked["max_mp"],
          f"gear={b_gear['max_mp']} naked={b_naked['max_mp']}")
    check("满装空蓝轮 ≥ 裸装", b_gear["empty_rounds"] >= b_naked["empty_rounds"],
          f"gear={b_gear['empty_rounds']} naked={b_naked['empty_rounds']}")

    print("【3/4 rotation 覆盖默认 ROTATIONS】")
    b_def = mp_budget("战士", 24, None)
    b_rot = mp_budget("战士", 24, None, rotation=[("怒斩", 1.0)])
    print(f"  默认: per_round_mp={b_def['per_round_mp']:.1f} 空蓝轮={b_def['empty_rounds']:.1f}")
    print(f"  覆盖: per_round_mp={b_rot['per_round_mp']:.1f} 空蓝轮={b_rot['empty_rounds']:.1f}")
    check("覆盖轴每轮耗蓝 < 默认（怒斩8mp < 嗜血斩10mp）", b_rot["per_round_mp"] < b_def["per_round_mp"],
          f"rot={b_rot['per_round_mp']} def={b_def['per_round_mp']}")
    check("覆盖轴空蓝轮 > 默认", b_rot["empty_rounds"] > b_def["empty_rounds"],
          f"rot={b_rot['empty_rounds']} def={b_def['empty_rounds']}")
    check("覆盖轴 max_mp 不变（同一职业同一面板）", b_rot["max_mp"] == b_def["max_mp"])

    print("【4/4 per_round_mp <= mp_regen → empty_rounds == inf】")
    # 0 耗蓝轴：跨职业技能名查不到 → 跳过 → per_round_mp=0 → 恒 inf
    b_inf = mp_budget("法师", 24, None, rotation=[("挥砍", 1.0)])
    check("无 MP 技能轴 → empty_rounds == inf",
          b_inf["empty_rounds"] == float("inf"),
          f"per_round_mp={b_inf['per_round_mp']} mp_regen={b_inf['mp_regen']} empty={b_inf['empty_rounds']}")
    check("无 MP 技能轴 per_round_mp == 0", b_inf["per_round_mp"] == 0.0,
          f"per_round_mp={b_inf['per_round_mp']}")

    print("\n" + "=" * 50)
    print(f"mp_budget 单测: ✅ {passed} / ❌ {failed}")
    if failed:
        print("→ 技能经济门禁未通过（空蓝轮数口径异常，勿提交）")
        return 1
    print("→ 技能经济门禁通过 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
