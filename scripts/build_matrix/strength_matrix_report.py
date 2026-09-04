# -*- coding: utf-8 -*-
"""v175e 全职业流派强度矩阵报告生成器 v2（真引擎 × 相对强度口径）。

设计（吸取 v1 教训）：
- 真实副本 Boss（boss_def_of）但**不叠 hp_mult**——单人刷本本就难，叠血必 0 胜无区分度；
  裸 Boss 面板是"同条件相对强度"公平擂台（谁快谁慢一目了然）。
- 玩家等级 = Boss lv + 5（真实刷本节奏：高 Boss 5 级左右）
- 装备 = 对应阶段标准档（solo_mid / team_purple9 / team_orange9 按 Boss 阶段）
- 全职业×全流派 × 5 个代表 Boss（P1-P5 单人本），seeds 可配
- 输出：每 Boss 击杀轮/胜率排序表 + 全职业汇总

用法：
  python scripts/build_matrix/strength_matrix_report.py [--json out] [--seeds 4]
"""
from __future__ import annotations
import os, sys, json, time

_BM_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS = os.path.dirname(_BM_DIR)
_PLUGIN = os.path.dirname(_SCRIPTS)
_QQBOT = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN)))
_TESTS = os.path.join(_PLUGIN, "tests")
for _p in (_QQBOT, _PLUGIN, _TESTS, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_TESTS, "test_game_data.db"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from numeric_lib.battle2 import battle_rotation, attr_pts_total      # noqa: E402
from build_matrix.boss_matrix import boss_def_of                      # noqa: E402
from build_matrix.schema import KNOWN_CLASSES                          # noqa: E402

# 阶段代表 Boss（单人本）：Boss lv → 玩家 lv = boss_lv + 5（碾压 5 级）
# 装备档按阶段：P1/P2 solo_mid，P3/P4 team_purple9，P5 team_orange9
STAGE_TARGET = [
    ("P1", "inst_goblin_camp",    20, "solo_mid"),       # 哥布林 Lv20
    ("P2", "inst_sea_cave",       27, "solo_mid"),       # 海盗王 Lv27
    ("P3", "inst_old_king_tomb",  40, "team_purple9"),   # 古王 Lv40
    ("P4", "inst_elven_ruins",    63, "team_purple9"),   # 精灵王 Lv63
    ("P5", "inst_ash_temple",     87, "team_orange9"),   # 恶魔祭司 Lv87
]

MAIN_ATTR = {"cls_zhan_shi": "str", "cls_fa_shi": "int", "cls_you_xia": "agi",
             "cls_mu_shi": "int", "cls_ci_ke": "agi", "cls_wu_seng": "str",
             "cls_shi_ren": "int"}


def main():
    seeds = 4
    if "--seeds" in sys.argv:
        seeds = int(sys.argv[sys.argv.index("--seeds") + 1])
    t0 = time.time()
    report = {"generated": time.strftime("%Y-%m-%d %H:%M"), "seeds": seeds,
              "method": "真引擎 battle_rotation，Boss 裸面板（不叠hp_mult），玩家=Boss lv+5",
              "stages": {}, "classes": {}}

    # 全职业全流派跑 5 阶段
    for cid in KNOWN_CLASSES:
        fp = os.path.join(_BM_DIR, "..", "balance_data", f"{cid}.json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            jd = json.load(f)
        cname = jd.get("class_name", cid)
        report["classes"][cid] = {"name": cname, "builds": {}}
        for bname, bdef in jd.get("builds", {}).items():
            rotation = [s["skill"] for s in bdef.get("rotation", [])]
            if not rotation:
                continue
            role = bdef.get("role", "?")
            affix = bdef.get("affix_preset", "atk")
            # 加点：推荐 attr_preset
            attr_rec = jd.get("attr_presets", {}).get(bdef.get("attr_preset", ""), {})
            if not attr_rec:
                attr_rec = {MAIN_ATTR[cid]: "all"}
            bres = {"role": role, "affix_preset": affix, "stages": {}}
            for stage, iid, boss_lv, loadout in STAGE_TARGET:
                plv = boss_lv + 5
                attr = {}
                for k, v in attr_rec.items():
                    attr[k] = attr_pts_total(plv) if v in ("all", "full") else int(v)
                boss_def = boss_def_of(iid)
                try:
                    r = battle_rotation(cid, plv, loadout, attr, rotation, boss_def,
                                        seeds=seeds, n_players=1, affix_type=affix)
                    bres["stages"][stage] = {
                        "boss": boss_def[1], "boss_lv": boss_lv, "player_lv": plv,
                        "wins": r["wins"], "seeds": seeds,
                        "avg_rounds": r["avg_rounds"] if r["wins"] else None,
                        "avg_survive": r["avg_survive"],
                        "win_rate": round(r["wins"] / seeds, 2),
                    }
                except Exception as ex:
                    bres["stages"][stage] = {"error": str(ex)[:80]}
            report["classes"][cid]["builds"][bname] = bres

    # 阶段汇总排序
    for stage, iid, boss_lv, loadout in STAGE_TARGET:
        boss_def = boss_def_of(iid)
        rows = []
        for cid, cinfo in report["classes"].items():
            for bname, binfo in cinfo["builds"].items():
                s = binfo.get("stages", {}).get(stage, {})
                if "win_rate" not in s:
                    continue
                rows.append({
                    "class": cinfo["name"], "cid": cid, "build": bname,
                    "role": binfo["role"], "affix": binfo["affix_preset"],
                    "win_rate": s["win_rate"], "avg_rounds": s["avg_rounds"],
                    "avg_survive": s["avg_survive"],
                })
        rows.sort(key=lambda x: (-x["win_rate"], x["avg_rounds"] if x["avg_rounds"] else 999))
        report["stages"][stage] = {"boss": boss_def[1], "boss_lv": boss_lv, "rows": rows}

    # 控制台输出
    print(f"===== 全职业流派强度矩阵（seeds={seeds}，耗时 {time.time()-t0:.0f}s）=====", flush=True)
    for stage, iid, boss_lv, loadout in STAGE_TARGET:
        st = report["stages"][stage]
        print(f"\n【{stage}】{st['boss']} Lv{boss_lv}（玩家 Lv{boss_lv+5} {loadout}）", flush=True)
        for row in st["rows"]:
            if row["avg_rounds"]:
                kr = f"{row['avg_rounds']:.1f}轮"
            else:
                kr = f"存活{row['avg_survive']:.1f}"
            print(f"  {row['class']}·{row['build']:<7} [{row['role']:<4}] "
                  f"{row['win_rate']:.0%} {kr}", flush=True)

    json_out = None
    if "--json" in sys.argv:
        idx = sys.argv.index("--json")
        json_out = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
    if json_out:
        os.makedirs(os.path.dirname(json_out), exist_ok=True)
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=1)
        print(f"\nJSON → {json_out}", flush=True)
    return report


if __name__ == "__main__":
    main()
