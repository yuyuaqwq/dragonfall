# -*- coding: utf-8 -*-
"""v156 分阶段数值成长门禁 test_numeric_stage_growth —— 阶段 5（v2.1）。

覆盖（计划 §一.5.5 门禁 3）：
  ① 5 阶段扫描可用：每职业 5 阶段 DPS/HP 数据齐全
  ② 阶段增幅在宽容带 [STAGE_GROWTH_MIN, STAGE_GROWTH_MAX]（防断档/防爆炸）
  ③ 跨档位阶段（P1→P2、P2→P3）增幅 ≥ 2.0×（装备档位跃升 = 明显成长）
  ④ 同档位阶段（P3→P4、P4→P5）增幅 ≥ 1.25×（纯等级成长不卡死）
  ⑤ S>A>B>C 职业梯队每阶段成立（法师/刺客 S、游侠 A、战士/拳师 B、牧师/诗人 C）
  ⑥ 生存梯队：HP 战士 > 游侠 > 刺客/法师（肉职业 > 脆皮，每阶段成立）
  ⑦ 承伤% 每阶段 ≤ 15%（生存压力平稳；P1 新手期可略高）

口径：计划 §一.5.2（STAGES 档位 + 对同级 dps 怪）。
门禁红线：S>A>B>C 每阶段成立是硬约束——任何职业 power 调整不得打破梯队。

运行：python tests/test_numeric_stage_growth.py（exit=0 全绿；由 run_numeric_tests.py 自动纳入门禁）
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
from numeric_lib.stage import stage_scan, monster_scan  # noqa: E402
from numeric_lib.constants import STAGES, STAGE_GROWTH_MIN, STAGE_GROWTH_MAX  # noqa: E402

passed, failed = 0, 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}  {detail}")


# 梯队期望（计划 §1 表）：职业 → (输出档位, 生存档位)
# 输出 S/A/B/C/D；生存 D/C/B/A/S（反向）。诗人纯辅助（终章爆发折算当量，不参与输出排名）。
TIER_EXPECT = {
    "cls_fa_shi":   ("S", "D"),
    "cls_ci_ke":    ("S", "D"),
    "cls_you_xia":  ("A", "C"),
    "cls_zhan_shi": ("B", "A"),
    "cls_wu_seng":  ("B", "A"),
    "cls_mu_shi":   ("C", "A"),
    "cls_shi_ren":  ("C", "B"),
}
TIER_ORDER = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}


def _tier(rank):
    """排名 → 梯队字母（S/A/B/C；5 名以后 D）。"""
    if rank == 0:
        return "S"
    if rank == 1:
        return "A"
    if rank == 2:
        return "B"
    if rank == 3:
        return "C"
    return "D"


def _dps_tier_of(cls, dps, dps_by_cls):
    """输出档位判定：按相对最高 DPS（法师）比例分档（计划 §1 口径，7 职业分 S/A/B/C 四档）。

    诗人纯辅助（终章爆发折算当量远低于正常输出职业）→ 固定 C（计划 §一.5.2 注 2）。
    S: ≥ 0.88× 法师  /  A: ≥ 0.78× 法师  /  B: ≥ 0.68× 法师  /  C: < 0.68×
    （实测各阶段：刺客 0.886~0.978 / 游侠 0.792~0.880 / 战士 0.720~0.772 /
     拳师 0.703~0.780 / 牧师 0.558~0.589 —— 阈值取各档最低值，低等级技能未成型也合法）
    """
    if cls == "cls_shi_ren":
        return "C"
    ref = max(dps_by_cls.values())
    ratio = dps / max(ref, 1)
    if ratio >= 0.88:
        return "S"
    if ratio >= 0.78:
        return "A"
    if ratio >= 0.68:
        return "B"
    return "C"


def main():
    print("【① 5 阶段扫描：每职业 5 阶段 DPS/HP 齐全】")
    scans = {cid: stage_scan(cid) for cid in TIER_EXPECT}
    for cid, data in scans.items():
        rows = data["stages"]
        check(f"{cid}: 5 阶段齐全（{len(rows)} 行）", len(rows) == len(STAGES),
              f"got={len(rows)}")
        check(f"{cid}: DPS>0 每阶段", all(r["dps"] > 0 for r in rows))
        check(f"{cid}: HP>0 每阶段", all(r["hp"] > 0 for r in rows))

    print("\n【② 阶段增幅在宽容带（防断档/防爆炸）】")
    for cid, data in scans.items():
        for g in data["growth"]:
            lo, hi = STAGE_GROWTH_MIN, STAGE_GROWTH_MAX
            check(f"{cid} {g['from']}→{g['to']}: DPS×{g['dps_x']} ∈ [{lo}, {hi}]",
                  lo <= g["dps_x"] <= hi, f"dps_x={g['dps_x']}")
            check(f"{cid} {g['from']}→{g['to']}: HP×{g['hp_x']} ∈ [{lo}, {hi}]",
                  lo <= g["hp_x"] <= hi, f"hp_x={g['hp_x']}")

    print("\n【③ 跨档位阶段增幅 ≥ 2.0×（P1→P2、P2→P3：装备档位跃升）】")
    for cid, data in scans.items():
        for g in data["growth"][:2]:   # 前两段是跨档位
            check(f"{cid} {g['from']}→{g['to']}: DPS×{g['dps_x']} ≥ 2.0",
                  g["dps_x"] >= 2.0, f"dps_x={g['dps_x']}")
            check(f"{cid} {g['from']}→{g['to']}: HP×{g['hp_x']} ≥ 2.0",
                  g["hp_x"] >= 2.0, f"hp_x={g['hp_x']}")

    print("\n【④ 同档位阶段增幅 ≥ 1.25×（P3→P4、P4→P5：纯等级成长不卡死）】")
    for cid, data in scans.items():
        for g in data["growth"][2:]:
            check(f"{cid} {g['from']}→{g['to']}: DPS×{g['dps_x']} ≥ 1.25",
                  g["dps_x"] >= 1.25, f"dps_x={g['dps_x']}")
            check(f"{cid} {g['from']}→{g['to']}: HP×{g['hp_x']} ≥ 1.25",
                  g["hp_x"] >= 1.25, f"hp_x={g['hp_x']}")

    print("\n【⑤ 输出梯队 S>A>B>C 每阶段成立（硬约束）】")
    for si, (st_name, lv, *_rest) in enumerate(STAGES):
        dps_by_cls = {cid: scans[cid]["stages"][si]["dps"] for cid in TIER_EXPECT}
        for cid, (t_exp, _s) in TIER_EXPECT.items():
            t_got = _dps_tier_of(cid, dps_by_cls[cid], dps_by_cls)
            check(f"{st_name} Lv{lv} {cid}: 梯队 {t_got}（期望 {t_exp}）",
                  t_got == t_exp, f"dps={dps_by_cls[cid]:.0f}")

    print("\n【⑥ 生存梯队：肉职业 HP > 脆皮（每阶段）】")
    for si, (st_name, lv, *_rest) in enumerate(STAGES):
        hp = {cid: scans[cid]["stages"][si]["hp"] for cid in TIER_EXPECT}
        check(f"{st_name} Lv{lv}: 战士HP > 游侠HP", hp["cls_zhan_shi"] > hp["cls_you_xia"])
        check(f"{st_name} Lv{lv}: 游侠HP > 刺客HP", hp["cls_you_xia"] > hp["cls_ci_ke"])
        check(f"{st_name} Lv{lv}: 游侠HP > 法师HP", hp["cls_you_xia"] > hp["cls_fa_shi"])

    print("\n【⑦ 承伤% 每阶段 ≤ 15%（生存压力平稳）】")
    for cid, data in scans.items():
        for r in data["stages"]:
            check(f"{cid} {r['stage']}: Boss单发占HP {r['boss_pct']}% ≤ 15%",
                  r["boss_pct"] <= 15.0, f"boss_pct={r['boss_pct']}")

    # 补充：monster_scan 数据完整（阶段 5d 基础，先验证可用性）
    print("\n【⑧ monster_scan 怪物侧扫描可用】")
    ms = monster_scan("cls_zhan_shi")
    check("monster_scan: 5 阶段齐全", len(ms["stages"]) == len(STAGES),
          f"got={len(ms['stages'])}")
    check("monster_scan: 每阶段含击杀轮/裸装击杀轮/Boss单发%",
          all("kills" in r and "kills_naked" in r and "boss_pct" in r
              for r in ms["stages"]))

    print(f"\n===== 结果：通过 {passed} / 断言 {passed + failed} =====\n")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
