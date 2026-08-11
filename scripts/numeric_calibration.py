# -*- coding: utf-8 -*-
"""数值校准工具（v101.24）：全副本 Boss 战轮数表

用法：
  python scripts/numeric_calibration.py

输出：每个副本 Boss 在 蓝装(主线可达) / 蓝装+9 / 紫装+9 三档位下的战斗轮数，
以及 Boss:普通怪 倍数。改数值（怪物模板/装备公式/强化表/hp_mult）后必跑，
对照 docs/NUMERIC_DESIGN.md 的舒适区（15-30 轮、Boss 4-8 倍普通怪）。

数值链路（详见 docs/NUMERIC_DESIGN.md）：
  monster_stats(lv, role) = base+growth×(lv-1) × boss系数(1+lv×0.06) × hp_stage_mult
  Boss HP(副本) = build_monster × [hp_mult + 0.65×(人数-min_players)]
  伤害 = atk²/(atk+def)，技能轮换 ×1.5，队伍人数 = min_players
"""
import sys, os

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
os.environ["GWEN_GAME_DB"] = os.path.join(PLUGIN_DIR, "test_game_data.db")

from data.plugins.dragonfall.game import content as C  # noqa: E402
from data.plugins.dragonfall.game import engine as E  # noqa: E402
from data.plugins.dragonfall.game.core import stats as ST  # noqa: E402


def make_gear(level, quality, enhance):
    gear = {}
    for slot in C.EQUIP_SLOT_BASE:
        s = ST.equip_stats(slot, level, quality)
        if enhance > 0:
            mult = C.ENHANCE_TABLE.get(enhance, {}).get("mult", 1.0)
            s = {k: int(v * mult) for k, v in s.items()}
        gear[slot] = {"stats": s, "enhance": enhance}
    return gear


def dmg(atk, def_):
    return max(1, atk * atk / (atk + def_))


def main():
    print("=== 全副本 Boss 战轮数表（队伍人数=min_players，技能轮换 ×1.5）===")
    print(f"{'副本':<22}{'lv':>3}{'BossHP':>9}{'Boss:普通怪':>10} | {'蓝装':>6} {'蓝+9':>6} {'紫+9':>6} | 判定")
    print("-" * 100)

    bad = []
    for iid, inst in sorted(C.INSTANCES.items(), key=lambda x: x[1].get("lv", 0)):
        lv = inst.get("lv", 0)
        boss_def = inst.get("boss") or (inst.get("stages") or [])[-1].get("boss")
        if not boss_def:
            continue
        m = C.build_monster(boss_def, {"id": iid, "name": iid, "area": "instance"})
        hpm = inst.get("hp_mult", 1.0)
        mn = inst.get("min_players", 1)
        boss_hp = int(m.get("max_hp", 0) * hpm)
        bdef = m.get("def", 0)

        # 普通怪基准（dps 同等级）
        norm = C.build_monster(("m_cal", "普通怪", "dps", boss_def[3], [], []),
                               {"id": "cal", "name": "cal", "area": "cal"})
        ratio = boss_hp / max(norm.get("max_hp", 1), 1)

        rounds = {}
        for label, q, enh in [("蓝装", "blue", 0), ("蓝+9", "blue", 9), ("紫+9", "purple", 9)]:
            gear = make_gear(lv, q, enh)
            st_w = E.player_final_stats("cls_zhan_shi", lv, gear, 0, None, 0, None, None)
            st_r = E.player_final_stats("cls_you_xia", lv, gear, 0, None, 0, None, None)
            avg = (dmg(st_w.get("atk", 0), bdef) + dmg(st_r.get("atk", 0), bdef)) / 2
            rounds[label] = boss_hp / max(avg * mn * 1.5, 1)

        flag = ""
        if rounds["蓝装"] > 80:
            flag = "🔴 主线卡"
        elif rounds["蓝+9"] > 40:
            flag = "🟡 毕业勉强"
        else:
            flag = "✅ 舒适"
        if flag != "✅":
            bad.append((iid, rounds))
        print(f"{iid:<22}{lv:>3}{boss_hp:>9,}{ratio:>9.1f}倍 | {rounds['蓝装']:>6.0f} {rounds['蓝+9']:>6.0f} {rounds['紫+9']:>6.0f} | {flag}")

    print()
    print(f"异常副本: {len(bad)}/{len(C.INSTANCES)}（目标 0，舒适区 = 蓝装 30-60 轮内 / 蓝+9 ≤40 轮）")
    print("校准锚点（docs/NUMERIC_DESIGN.md）：Boss 战 15-30 轮 = 舒适；Boss:普通怪 4-8 倍 = 合理")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
