# -*- coding: utf-8 -*-
"""v175c 真引擎全职业×多Boss抽验网格 —— 期望结论的真引擎仲裁。

选格：每职业 dps 流派（期望最强/最弱）× 3 档 Boss（低/中/高，等级匹配）。
判据：真引擎胜率/击杀轮是否印证期望排序（期望最强 → 真引擎也该强）。
Boss 用能打赢的等级匹配（碾压档），否则全 0 胜无法区分。
"""
from __future__ import annotations
import os, sys, json

_BM_DIR = os.path.dirname(os.path.abspath(__file__))           # scripts/build_matrix/
_SCRIPTS = os.path.dirname(_BM_DIR)                              # scripts/
_PLUGIN = os.path.dirname(_SCRIPTS)                              # dragonfall/
_QQBOT = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN)))
_TESTS = os.path.join(_PLUGIN, "tests")
for _p in (_QQBOT, _PLUGIN, _TESTS, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_TESTS, "test_game_data.db"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from numeric_lib.saintess_engine import battle_rotation, attr_pts_total
from build_matrix.boss_matrix import boss_def_of
from data.plugins.dragonfall.game.data import skills as SK

# (职业, Boss实例, 玩家lv, loadout) — 玩家等级比 Boss 高 ~15-20 级保证能打赢比击杀轮
PROBES = [
    # 职业, 最强/最弱流派名, Boss, 玩家lv, loadout, 加点key
    ("cls_zhan_shi", "狂战流", "inst_goblin_camp", 40, "solo_mid", "str"),
    ("cls_zhan_shi", "血怒流", "inst_goblin_camp", 40, "solo_mid", "str"),
    ("cls_fa_shi", "元素迸发流", "inst_goblin_camp", 40, "solo_mid", "int"),
    ("cls_fa_shi", "奥术精算流", "inst_goblin_camp", 40, "solo_mid", "int"),
    ("cls_ci_ke", "影遁收割流", "inst_goblin_camp", 40, "solo_mid", "agi"),
    ("cls_ci_ke", "毒刃腐蚀流", "inst_goblin_camp", 40, "solo_mid", "agi"),
    ("cls_wu_seng", "破绽连打流", "inst_goblin_camp", 40, "solo_mid", "str"),
    ("cls_mu_shi", "死灵骷髅流", "inst_goblin_camp", 40, "solo_mid", "int"),
    ("cls_you_xia", "疾风连射流", "inst_goblin_camp", 40, "solo_mid", "agi"),
    # 更高难本：海蚀(Lv22 Boss27) 用 Lv50 玩家
    ("cls_fa_shi", "元素迸发流", "inst_sea_cave", 50, "solo_mid", "int"),
    ("cls_fa_shi", "奥术精算流", "inst_sea_cave", 50, "solo_mid", "int"),
    ("cls_you_xia", "疾风连射流", "inst_sea_cave", 50, "solo_mid", "agi"),
    ("cls_ci_ke", "影遁收割流", "inst_sea_cave", 50, "solo_mid", "agi"),
]


def main():
    print("== 真引擎抽验网格：期望排序 vs 真引擎 ==", flush=True)
    for cid, bname, iid, lv, loadout, attr_key in PROBES:
        print(f"→ {cid} {bname} {iid} Lv{lv}...", flush=True)
        fp = os.path.join(_SCRIPTS, "balance_data", f"{cid}.json")
        if not os.path.exists(fp):
            print("  (no json)", flush=True)
            continue
        with open(fp, encoding="utf-8") as f:
            jd = json.load(f)
        if bname not in jd.get("builds", {}):
            print("  (no build)", flush=True)
            continue
        bdef = jd["builds"][bname]
        rotation = [s["skill"] for s in bdef["rotation"]]
        cname = jd.get("class_name", cid)
        pts = attr_pts_total(lv)
        attr = {attr_key: pts}
        boss_def = boss_def_of(iid)
        if not boss_def:
            print("  (no boss)", flush=True)
            continue
        r = battle_rotation(cid, lv, loadout, attr, rotation, boss_def,
                            seeds=6, iid=iid, n_players=1, max_turns=800)
        w = r["wins"]
        kr = f"{r['avg_rounds']}轮" if w else f"存活{r['avg_survive']}轮"
        print(f"  {cname}·{bname}: {w}/6胜 击杀{kr} (vs {boss_def[1]} Lv{boss_def[3]})", flush=True)


if __name__ == "__main__":
    main()
