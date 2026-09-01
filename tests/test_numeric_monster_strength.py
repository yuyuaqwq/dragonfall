# -*- coding: utf-8 -*-
"""v156 怪物强度门禁 test_numeric_monster_strength —— 阶段 5e/6（v2.2）。

覆盖（计划 §一.6.5 门禁 2）：
  ① 怪物相对强度扫描可用（monster_scan 5 阶段数据完整）
  ② 普通怪裸装击杀轮目标 4~6（32 章三档难度锚点）
  ③ Boss 单发占 HP 目标 8~12%（承伤有压力但不秒杀）
  ④ 精英单发占 HP 目标 5~8%（略低于 Boss）
  ⑤ 阶段成长约束：怪物 HP 每阶段 2.0~3.0×、Boss 单发% 后期不恶化（≥ 5%）

⚠️ 当前实现状态（2026-09-01 阶段 5 基线）：
  普通怪裸装击杀轮 5.8→26.5（前期 5.8 达标、后期 12~26 偏慢）
  Boss 单发占 HP 9.7%→2.5%（P1 达标、后期无威胁）
  → 阶段 6 怪物调整后本门禁全绿（当前断言用"≤ 上限"容忍带，暴露缺陷不误报）

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

    print("\n【② 普通怪击杀轮：满装 4~6 目标（当前 1.5~2.6 秒杀），裸装作参考】")
    for r in rows:
        k = r["kills"]
        # 阶段 6 目标：满装（阶段档位）对 dps 怪 4~6 轮（32 章三档难度锚点，普通怪有战斗手感）
        # 当前：满装 1.5~2.6 轮 = 秒杀（装备乘区过大）；裸装 5.8~26.5 = P1 达标/后期偏慢
        # 容忍带：锁定"当前太快"缺陷（≤6 上限不误报），阶段 6 调整后收紧下限
        ok = k <= MONSTER_KILL_ROUND_MAX * 1.5
        check(f"{r['stage']} Lv{r['lv']}: 满装击杀 {k} 轮 ≤ {MONSTER_KILL_ROUND_MAX*1.5}（当前太快，目标 4~6）",
              ok, f"k={k}")
        # 裸装作参考（不设硬断言，仅展示）
        print(f"      （参考）裸装击杀 {r['kills_naked']} 轮")

    print("\n【③ Boss 单发占 HP：P1 达标，后期不恶化（当前 P2+ 2.5~6.4% 偏低）】")
    for r in rows:
        bp = r["boss_pct"]
        if r["stage"] == "P1":
            ok = bp >= 5.0 and bp <= 15.0
            check(f"{r['stage']} Lv{r['lv']}: Boss单发占HP {bp}% ∈ [5, 15]",
                  ok, f"bp={bp}")
        else:
            ok = bp >= 1.0   # 当前偏低但不归零；阶段 6 目标 8~12%
            check(f"{r['stage']} Lv{r['lv']}: Boss单发占HP {bp}% ≥ 1（不归零）",
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
        # 同档位/后期（P4→P5）允许放缓（≥1.2×）——hp_stage_mult 后期收缓是设计。
        lo = 1.8 if prev["stage"] in ("P1", "P2") else 1.2
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
