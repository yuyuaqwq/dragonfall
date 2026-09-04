# -*- coding: utf-8 -*-
"""v175e 全流派 affix_preset 真引擎校准扫描（满级 P5 vs 烬山）。

期望引擎 affix_scan 用"期望模型"扫词条 → 早期 preset 多是 crit/spd 拍脑袋。
真引擎校准：每 dps 流派扫 6 词条（atk/crit/spd/cdr/elem/pene），取击杀最快/胜率最高者。

用法：python scripts/build_matrix/affix_recalib.py [--json out.json]
"""
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

from numeric_lib.battle2 import battle_rotation, attr_pts_total  # noqa: E402
from build_matrix.boss_matrix import boss_def_of  # noqa: E402
from build_matrix.schema import KNOWN_CLASSES  # noqa: E402

MAIN_ATTR = {"cls_zhan_shi": "str", "cls_fa_shi": "int", "cls_you_xia": "agi",
             "cls_mu_shi": "int", "cls_ci_ke": "agi", "cls_wu_seng": "str",
             "cls_shi_ren": "int"}
AFFIXES = ("atk", "crit", "spd", "cdr", "elem", "pene")
AFFIX_CN = {"atk": "攻击", "crit": "暴击", "spd": "急速", "cdr": "减CD", "elem": "元素", "pene": "穿透"}


def main():
    lv = 98
    pts = attr_pts_total(lv)
    boss_def = boss_def_of("inst_ash_temple")
    seeds = 4
    t0 = time.time()
    out = {}
    print(f"== affix_preset 真引擎校准（Lv{lv} vs {boss_def[1]} seeds={seeds}）==", flush=True)
    for cid in KNOWN_CLASSES:
        fp = os.path.join(_BM_DIR, "..", "balance_data", f"{cid}.json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            jd = json.load(f)
        cname = jd.get("class_name", cid)
        for bname, bdef in jd.get("builds", {}).items():
            if bdef.get("role") != "dps":
                continue
            rotation = [s["skill"] for s in bdef.get("rotation", [])]
            rules = bdef.get("rotation", [])
            if not rotation:
                continue
            attr_rec = jd.get("attr_presets", {}).get(bdef.get("attr_preset", ""), {})
            if not attr_rec:
                attr_rec = {MAIN_ATTR[cid]: "all"}
            attr = {}
            for k, v in attr_rec.items():
                attr[k] = pts if v in ("all", "full") else int(v)
            results = {}
            for aff in AFFIXES:
                try:
                    r = battle_rotation(cid, lv, "team_orange9", attr, rotation, boss_def,
                                        seeds=seeds, rules=rules, affix_type=aff)
                    results[aff] = {"wins": r["wins"], "avg_rounds": r["avg_rounds"] if r["wins"] else None,
                                    "avg_survive": r["avg_survive"]}
                except Exception as ex:
                    results[aff] = {"error": str(ex)[:60]}
            # 选优：先胜率（全胜 > 非全胜），再击杀轮
            def score(aff):
                r = results.get(aff) or {}
                w = r.get("wins", 0)
                kr = r.get("avg_rounds")
                surv = r.get("avg_survive", 0)
                return (w, -kr if kr else -999, -surv)  # 胜率高优先，击杀轮短优先
            best = max(AFFIXES, key=score)
            out[f"{cname}·{bname}"] = {"current": bdef.get("affix_preset", "atk"),
                                        "best": best, "best_cn": AFFIX_CN[best],
                                        "results": {AFFIX_CN[a]: results[a] for a in AFFIXES}}
            cur = bdef.get("affix_preset", "atk")
            flag = "❌需改" if best != cur else "✅"
            cells = []
            for a in AFFIXES:
                r_ = results[a]
                if "error" in r_:
                    cells.append(f"{AFFIX_CN[a]}=err")
                elif r_.get("avg_rounds"):
                    cells.append(f"{AFFIX_CN[a]}={r_['avg_rounds']:.0f}轮")
                else:
                    cells.append(f"{AFFIX_CN[a]}={r_.get('wins',0)}胜")
            print(f"  {flag} {cname}·{bname}: 当前={AFFIX_CN.get(cur, cur)} 最优={AFFIX_CN[best]} [{(' '.join(cells))}]", flush=True)
    print(f"\n耗时 {time.time()-t0:.0f}s")
    json_out = None
    if "--json" in sys.argv:
        idx = sys.argv.index("--json")
        json_out = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
    if json_out:
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        print(f"JSON → {json_out}")


if __name__ == "__main__":
    main()
