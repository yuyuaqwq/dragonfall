# -*- coding: utf-8 -*-
"""v175c 单人本 10 本平衡分析 —— 每 Boss 各职业 dps 流派击杀轮 + 相对排名。

单人本（min=1）是流派平衡的真实战场（单人可进、装备档标准）。
输出：每 Boss 击杀轮排序 + 最强/最弱差距 + 失衡标记。
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

from build_matrix.build_matrix import build_vs_boss, resolve_attr
from build_matrix.boss_matrix import boss_def_of, all_bosses
from build_matrix.schema import KNOWN_CLASSES
from build_matrix.boss22_scan import stage_for

# 职业短名
def short(cid):
    return {"cls_zhan_shi": "战士", "cls_fa_shi": "法师", "cls_you_xia": "游侠",
            "cls_mu_shi": "牧师", "cls_ci_ke": "刺客", "cls_wu_seng": "拳师",
            "cls_shi_ren": "诗人"}.get(cid, cid)


def main():
    print("== 单人本 10 本 × 全职业 dps 流派 击杀轮排序 ==")
    # 载入职业数据
    cls_data = {}
    for cid in KNOWN_CLASSES:
        fp = os.path.join(_BM_DIR, "..", "balance_data", f"{cid}.json")
        if os.path.exists(fp):
            with open(fp, encoding="utf-8") as f:
                cls_data[cid] = json.load(f)
    solo_bosses = [b for b in all_bosses() if b["min_players"] == 1]
    solo_bosses.sort(key=lambda x: x["inst_lv"])

    # 汇总失衡数据
    bad_gaps = []  # (boss, best, worst, ratio)
    for b in solo_bosses:
        iid, inst_lv = b["iid"], b["inst_lv"]
        plv, loadout = stage_for(inst_lv)
        rows = []
        for cid in KNOWN_CLASSES:
            jd = cls_data.get(cid)
            if not jd:
                continue
            cname = jd.get("class_name", cid)
            for bname, bdef in jd.get("builds", {}).items():
                if bdef.get("role") != "dps":
                    continue
                rec = jd.get("attr_presets", {}).get(bdef.get("attr_preset", ""), {})
                if not rec:
                    rec = {"str": "all"}
                attr = resolve_attr(rec, plv)
                boss_def = boss_def_of(iid)
                try:
                    r = build_vs_boss(cid, plv, loadout, attr, bdef["rotation"],
                                      boss_def, int(boss_def[3]), iid=iid, n_players=1)
                    kr = r["kill_rounds"]
                    if kr:
                        rows.append((f"{cname}·{bname}", kr))
                    else:
                        rows.append((f"{cname}·{bname}", 99999))  # 杀不死
                except Exception:
                    pass
        rows.sort(key=lambda x: x[1])
        print(f"\n{b['boss_name']} (Lv{inst_lv} 本 / Boss Lv{b['boss_lv']}) 玩家Lv{plv} {loadout}")
        for nm, kr in rows:
            flag = ""
            if kr == 99999:
                flag = "杀不死"
            elif kr > 150:
                flag = "🟡偏慢"
            elif kr < 40:
                flag = "🟢快"
            print(f"  {nm:<12} {kr if kr < 99999 else '—':<6} {flag}")
        if len(rows) >= 2:
            best = rows[0][1]
            worst = rows[-1][1]
            if best < 99999 and worst > best * 2.5:
                bad_gaps.append((b["boss_name"], rows[0][0], best, rows[-1][0], worst, round(worst / max(best, 1), 1)))

    print("\n== 失衡标记（最强/最弱击杀轮差 >2.5×）==")
    if bad_gaps:
        for boss, bnm, bkr, wnm, wkr, ratio in bad_gaps:
            print(f"  🔴 {boss}: 最强 {bnm}({bkr}轮) vs 最弱 {wnm}({wkr}轮) = {ratio}×")
    else:
        print("  ✅ 无 >2.5× 失衡")


if __name__ == "__main__":
    main()
