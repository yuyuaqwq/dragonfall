# -*- coding: utf-8 -*-
"""v175d 真引擎平衡体检 —— 全流派 × 多 Boss 自动网格（最终闸门）。

用法：python scripts/build_matrix/real_audit.py [--boss 哥布林,海蚀,老王] [--json out.json]
每 Boss × 每流派 seeds 场，输出击杀轮排序 + 梯队 + 失衡标记。
成为数值调整的最终参照（期望引擎只做粗筛；召唤/机制流必须真引擎）。
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

from numeric_lib.saintess_engine import battle_rotation, attr_pts_total
from build_matrix.boss_matrix import boss_def_of
from build_matrix.schema import KNOWN_CLASSES

MAIN_ATTR = {"cls_zhan_shi": "str", "cls_fa_shi": "int", "cls_you_xia": "agi",
             "cls_mu_shi": "int", "cls_ci_ke": "agi", "cls_wu_seng": "str",
             "cls_shi_ren": "int"}

# 默认 Boss 档：每档选一个能打赢的等级匹配
# (iid, 玩家lv, loadout) —— 玩家比 Boss 高 20-25 级保证能打赢比击杀轮
BOSS_PROBES = [
    ("inst_goblin_camp", 50, "solo_mid"),     # Boss Lv20
    ("inst_sea_cave", 60, "team_purple9"),    # Boss Lv27
    ("inst_old_king_tomb", 70, "team_purple9"),  # Boss Lv40
    ("inst_moon_temple", 90, "team_orange9"), # Boss Lv65
]


def audit_boss(iid, plv, loadout, seeds=4) -> list:
    """单 Boss 全流派审计，返回排序行。"""
    boss_def = boss_def_of(iid)
    if not boss_def:
        return []
    rows = []
    for cid in KNOWN_CLASSES:
        fp = os.path.join(_BM_DIR, "..", "balance_data", f"{cid}.json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            jd = json.load(f)
        cname = jd.get("class_name", cid)
        pts = attr_pts_total(plv)
        attr = {MAIN_ATTR[cid]: pts}
        for bname, bdef in jd.get("builds", {}).items():
            rotation = [s["skill"] for s in bdef["rotation"]]
            r = battle_rotation(cid, plv, loadout, attr, rotation, boss_def,
                                seeds=seeds, iid=iid, n_players=1, max_turns=800)
            w = r["wins"]
            rows.append({
                "class": cname, "build": bname, "role": bdef.get("role", "?"),
                "wins": w, "seeds": seeds,
                "kill_rounds": r["avg_rounds"] if w else None,
                "survive": r["avg_survive"] if not w else 0,
            })
    # 排序：胜场优先，击杀轮次之
    rows.sort(key=lambda x: (-x["wins"], x["kill_rounds"] if x["kill_rounds"] else 999))
    return rows


def fmt_rows(rows) -> str:
    lines = []
    for r in rows:
        if r["wins"] > 0:
            lines.append(f"  {r['class']}·{r['build']:<7} [{r['role']:<7}] {r['wins']}/{r['seeds']}胜 {r['kill_rounds']:.1f}轮")
        else:
            lines.append(f"  {r['class']}·{r['build']:<7} [{r['role']:<7}] {r['wins']}/{r['seeds']}胜 存活{r['survive']:.1f}轮")
    return "\n".join(lines)


def main():
    t0 = time.time()
    out_json = None
    if "--json" in sys.argv:
        idx = sys.argv.index("--json")
        out_json = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
    print("== 真引擎平衡体检（全流派 × 多 Boss）==", flush=True)
    all_data = {}
    for iid, plv, loadout in BOSS_PROBES:
        boss_def = boss_def_of(iid)
        bname = boss_def[1] if boss_def else iid
        print(f"\n--- {bname} (玩家 Lv{plv} {loadout}) ---", flush=True)
        rows = audit_boss(iid, plv, loadout)
        print(fmt_rows(rows), flush=True)
        all_data[iid] = {"boss": bname, "player_lv": plv, "loadout": loadout, "rows": rows}
    print(f"\n== 总耗时 {time.time()-t0:.0f}s ==")
    if out_json:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
