# -*- coding: utf-8 -*-
"""v175c 真引擎全职业全流派网格 —— 最终平衡真相（召唤/机制流真引擎为准）。

每职业 ALL 流派（不只 dps）× 2 Boss 档。真引擎完整模拟召唤/机制。
输出每流派击杀轮（期望引擎低估的召唤流会显形为正常）。
"""
from __future__ import annotations
import os, sys, json

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

from numeric_lib.battle2 import battle_rotation, attr_pts_total
from build_matrix.boss_matrix import boss_def_of
from build_matrix.schema import KNOWN_CLASSES

MAIN_ATTR = {"cls_zhan_shi": "str", "cls_fa_shi": "int", "cls_you_xia": "agi",
             "cls_mu_shi": "int", "cls_ci_ke": "agi", "cls_wu_seng": "str",
             "cls_shi_ren": "int"}


def main():
    print("== 真引擎全流派网格（最终平衡真相，期望低估召唤流会显形）==", flush=True)
    # Boss 档：哥布林 Lv20（玩家50碾压比击杀轮）
    iid, lv, loadout = "inst_goblin_camp", 50, "solo_mid"
    pts = attr_pts_total(lv)
    boss_def = boss_def_of(iid)
    boss_name = boss_def[1]
    print(f"\n--- {boss_name} Lv{boss_def[3]}（玩家 Lv{lv} {loadout}）---", flush=True)
    results = []
    for cid in KNOWN_CLASSES:
        fp = os.path.join(_BM_DIR, "..", "balance_data", f"{cid}.json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            jd = json.load(f)
        cname = jd.get("class_name", cid)
        for bname, bdef in jd.get("builds", {}).items():
            rotation = [s["skill"] for s in bdef["rotation"]]
            role = bdef.get("role", "?")
            attr = {MAIN_ATTR[cid]: pts}
            r = battle_rotation(cid, lv, loadout, attr, rotation, boss_def,
                                seeds=4, iid=iid, n_players=1, max_turns=800)
            w = r["wins"]
            kr = r["avg_rounds"] if w else None
            results.append((cname, bname, role, w, kr))
    # 排序：先胜场数（4=全胜），再击杀轮
    results.sort(key=lambda x: (-x[3], x[4] if x[4] else 999))
    for cname, bname, role, w, kr in results:
        kr_s = f"{kr:.1f}轮" if kr else f"存活{r['avg_survive']:.1f}"
        print(f"  {cname}·{bname:<7} [{role:<7}] {w}/4胜 {kr_s}", flush=True)


if __name__ == "__main__":
    main()
