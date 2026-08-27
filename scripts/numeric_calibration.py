# -*- coding: utf-8 -*-
"""数值校准工具（v131 升级）：全副本 Boss 战轮数表 —— 真实玩家模型。

v131 重大修正（2026-08-27）：原模型"残疾"——无自由属性点/无tier/无词条/无附魔/无药水/
技能仅 ×1.5 粗估，导致 Boss 结论 110~315 轮是假象（真实玩家每轮输出 5~6 倍）。
现全部走 scripts/numeric_lib（真实玩家模型，多维度乘区，见 docs/NUMERIC_TOOLKIT.md）。

用法：
  python scripts/numeric_calibration.py                     # 默认 team_mid（4人 蓝+5，策划案校准档）
  python scripts/numeric_calibration.py --loadout solo_low  # 单刷 蓝+0（低配）
  python scripts/numeric_calibration.py --loadout legacy    # 旧残疾模型（对照，应≈升级前输出）
  python scripts/numeric_calibration.py --loadout team_max  # 4人 蓝+9（毕业档，查过速）

输出：每个副本 Boss 在给定档位下的战斗轮数 + Boss:普通怪倍数。
舒适区：15-30 轮（策划案 32 章五，蓝装+3~+5 档位口径）；Boss:普通怪 4-8 倍。
改动数值（怪物模板/装备公式/强化表/hp_mult）后必跑，对照回写 32 章。
"""
import sys, os

_SDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SDIR)

from numeric_lib.env import setup_env  # noqa: E402,F401
from numeric_lib.constants import LOADOUTS  # noqa: E402
from numeric_lib.team import team_matrix  # noqa: E402
from numeric_lib.report import md_table  # noqa: E402


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="全副本 Boss 战轮数表（真实玩家模型）")
    p.add_argument("--loadout", choices=list(LOADOUTS), default="team_mid",
                   help="玩家档位（默认 team_mid=4人蓝+5，策划案校准档）")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    rows = team_matrix(loadout=args.loadout)
    if args.json:
        import json
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    print(f"=== 全副本 Boss 战轮数表（真实玩家模型，档位: {LOADOUTS[args.loadout]['label']}）===")
    print(md_table(rows, ["iid", "lv", "boss_lv", "boss_hp", "ratio", "rounds", "survive", "flag"],
                   {"iid": "副本", "lv": "本Lv", "boss_lv": "BossLv", "boss_hp": "BossHP",
                    "ratio": "Boss:普通怪", "rounds": "击杀轮", "survive": "承伤轮", "flag": "判定"}))
    bad = [r for r in rows if r["flag"] == "🔴"]
    fast = [r for r in rows if r["flag"] == "⚠️"]
    print()
    print(f"异常: {len(bad)}/{len(rows)}（🔴=打不过或>60轮；⚠️=<15轮过速；承伤轮<击杀轮=先死；"
          f"舒适区 15-30 轮，Boss:普通怪 4-8 倍锚点见 32 章五）")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())