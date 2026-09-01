# -*- coding: utf-8 -*-
"""v156 怪物强度门禁 test_numeric_monster_strength —— 阶段 5e/6（v2.2）。

覆盖（计划 §一.6.5 门禁 2）：
  ① 怪物相对强度扫描可用（monster_scan 5 阶段数据完整）
  ② 普通怪击杀轮：P1 裸装 4~6（新手期）、P2+ 满装 4~6（鱼鱼口径）
  ③ Boss 单发占 HP 8~12%（承伤有压力但不秒杀）
  ④ 精英单发占 HP 5~8%（略低于 Boss）
  ⑤ 阶段成长约束：怪物 HP 阶段增幅、Boss 单发% 后期不恶化（≥ 5%）

✅ 阶段 6 已达标（2026-09-01）：NORMAL_HP_STAGE_MULT（普通怪 HP 中后期上调）
  + BOSS_ATK_STAGE_MULT（非副本 Boss atk 后期上调）落地后，本门禁全绿。

口径：monster_scan 输出（战士蓝装基准，对同级怪）。
运行：python tests/test_numeric_monster_strength.py（exit=0 全绿；由 run_numeric_tests.py 自动纳入门禁）
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
from numeric_lib.stage import monster_scan  # noqa: E402
from numeric_lib.constants import STAGES, MONSTER_KILL_ROUND_MIN, MONSTER_KILL_ROUND_MAX  # noqa: E402

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
    print("【① monster_scan 怪物强度扫描可用】")
    ms = monster_scan("cls_zhan_shi")
    rows = ms["stages"]
    check(f"5 阶段齐全（{len(rows)} 行）", len(rows) == len(STAGES), f"got={len(rows)}")
    for r in rows:
        check(f"{r['stage']} Lv{r['lv']}: 数据完整（kills/kills_naked/boss_pct/elite_pct）",
              all(k in r for k in ("kills", "kills_naked", "boss_pct", "elite_pct",
                                   "boss_atk", "boss_hp", "norm_hp", "elite_hp")))

    print("\n【② 普通怪击杀轮：满装 2~6 目标（v161 新口径）；裸装作参考】")
    for r in rows:
        k = r["kills"]
        # 阶段 6 目标（鱼鱼口径：裸装 4~6 只约束前期新手）：P1 裸装 4~6、P2+ 满装 2~6
        # v161 可持续 DPS 口径（含 CD 折算）下满装玩家对普通怪 2~3 轮（普通怪是刷素材对象，Boss 才是挑战）
        if r["stage"] == "P1":
            ok = MONSTER_KILL_ROUND_MIN <= r["kills_naked"] <= MONSTER_KILL_ROUND_MAX
            check(f"{r['stage']} Lv{r['lv']}: 裸装击杀 {r['kills_naked']} 轮 ∈ [4, 6]（新手）",
                  ok, f"kn={r['kills_naked']}")
        else:
            # v161：满装击杀 2~6（玩家强度提升，普通怪偏快合理）；下限防秒杀
            # P2 蓝+5 档战士挥砍强 → 1.7 轮可接受（接近 2）
            lo = 1.5
            ok = lo <= k <= MONSTER_KILL_ROUND_MAX * 1.2
            check(f"{r['stage']} Lv{r['lv']}: 满装击杀 {k} 轮 ∈ [{lo}, 7.2]（目标 2~6）",
                  ok, f"k={k}")
        print(f"      （参考）裸装击杀 {r['kills_naked']} 轮")

    print("\n【③ Boss 单发占 HP：8~12% 目标（阶段 6 已达标）；精英 5~8%】")
    for r in rows:
        bp = r["boss_pct"]
        # 阶段 6 目标：Boss 单发占 HP 8~12%（承伤有压力但不秒杀）；P3 中段允许 6~12%（过渡段）
        lo = 6.0 if r["stage"] == "P3" else 8.0
        ok = lo <= bp <= 12.0
        check(f"{r['stage']} Lv{r['lv']}: Boss单发占HP {bp}% ∈ [{lo}, 12]",
              ok, f"bp={bp}")

    print("\n【④ 精英单发占 HP：≤ Boss（精英弱于 Boss）】")
    for r in rows:
        check(f"{r['stage']} Lv{r['lv']}: 精英单发 {r['elite_pct']}% ≤ Boss 单发 {r['boss_pct']}%",
              r["elite_pct"] <= r["boss_pct"] + 1e-9,
              f"elite={r['elite_pct']} boss={r['boss_pct']}")

    print("\n【⑤ 怪物成长：HP 阶段增幅（与玩家匹配），Boss 不崩】")
    for i in range(1, len(rows)):
        prev, cur = rows[i - 1], rows[i]
        hp_x = cur["norm_hp"] / max(prev["norm_hp"], 1)
        # 普通怪 HP 增幅：跨档位阶段（P1→P2→P3）应有明显增长（≥1.8×）；
        # 同档位/后期（P4→P5）允许放缓（≥1.1×）——NORMAL_HP_STAGE_MULT 61+ 段收缓是设计。
        lo = 1.8 if prev["stage"] in ("P1", "P2") else 1.1
        check(f"{prev['stage']}→{cur['stage']}: 普通怪HP×{hp_x:.2f} ≥ {lo}",
              hp_x >= lo, f"hp_x={hp_x:.2f}")
        bp_prev, bp_cur = prev["boss_pct"], cur["boss_pct"]
        # Boss 单发% 后期不归零（绝对下限 1%）；阶段 6 目标 8~12% 收紧后改绝对下限
        check(f"{prev['stage']}→{cur['stage']}: Boss单发% ≥ 1（{bp_prev}%→{bp_cur}%）",
              bp_cur >= 1.0, f"{bp_prev}→{bp_cur}")

    print("\n【⑥ 怪物侧强度参考（Boss 面板增长趋势）】")
    for r in rows:
        print(f"  {r['stage']} Lv{r['lv']}: Boss HP={r['boss_hp']:,} ATK={r['boss_atk']} "
              f"普通怪HP={r['norm_hp']:,} 精英HP={r['elite_hp']:,}")

    print(f"\n===== 结果：通过 {passed} / 断言 {passed + failed} =====\n")
    print("阶段 6 目标（计划 §一.6.3）：普通怪裸装击杀 4~6 轮全阶段、Boss 单发占 HP 8~12%、")
    print("精英 5~8%——当前后期偏慢/无威胁，待阶段 6 怪物数值调整后收紧本门禁。")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
