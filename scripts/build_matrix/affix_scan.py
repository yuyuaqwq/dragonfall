# -*- coding: utf-8 -*-
"""v175e 词条乘区流派扫描 —— 全职业 × 流派 × 6 乘区配装最优倾向。

覆盖（鱼鱼需求：暴击法师/急速游侠等乘区玩法）：
  每职业每流派跑 6 种词条乘区（atk 基准/crit 暴击/spd 急速/pene 穿透/lifesteal 吸血/elem 元素），
  对同级 Boss 算期望 DPS，找该流派最优乘区 + 乘区间差距。

口径：build_matrix（期望引擎，v175e 含暴击/穿透/全伤乘区）
输出：每流派 6 乘区 DPS 表 + 最优乘区 + 是否乘区差异有意义（>5%）
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

from build_matrix.build_matrix import rotation_dps, resolve_attr, boss_instance_panel
from build_matrix.schema import KNOWN_CLASSES

AFFIXES = ("atk", "crit", "spd", "pene", "elem", "cdr")
AFFIX_LABEL = {"atk": "攻击", "crit": "暴击", "spd": "急速", "pene": "穿透", "elem": "元素", "cdr": "减CD"}
# 注：lifesteal 吸血是生存向（不加输出），单独评估不在此输出对比
LV = 75
LOADOUT = "team_purple9"


def main():
    print(f"== v175e 词条乘区流派扫描（Lv{LV} {LOADOUT}，期望引擎）==")
    rows_out = []
    for cid in KNOWN_CLASSES:
        fp = os.path.join(_BM_DIR, "..", "balance_data", f"{cid}.json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            jd = json.load(f)
        cname = jd.get("class_name", cid)
        # 目标：该阶段单人 Boss
        from build_matrix.boss_matrix import all_bosses
        boss = [b for b in all_bosses() if b["inst_lv"] <= 65][-1]  # 精灵废墟 Lv58
        bp = boss_instance_panel(boss["iid"], 1)
        tgt = {"role": "boss", "lv": boss["boss_lv"], "max_hp": bp["max_hp"],
               "def": bp["def"], "mdef": bp["mdef"], "hp": bp["max_hp"]}
        print(f"\n--- {cname}（vs {boss['boss_name']} Lv{boss['boss_lv']}）---")
        for bname, bdef in jd.get("builds", {}).items():
            if bdef.get("role") != "dps":
                continue
            rotation = bdef.get("rotation", [])
            rec = jd.get("attr_presets", {}).get(bdef.get("attr_preset", ""), {})
            if not rec:
                rec = {"str": "all"}
            attr = resolve_attr(rec, LV)
            dps_by = {}
            for at in AFFIXES:
                try:
                    r = rotation_dps(cid, LV, LOADOUT, attr, rotation,
                                     fight_len=60.0, target=tgt, affix_type=at)
                    dps_by[at] = r["dps"]
                except Exception as ex:
                    dps_by[at] = 0.0
            base = dps_by.get("atk", 1.0)
            best_at = max(AFFIXES, key=lambda x: dps_by[x])
            best_dps = dps_by[best_at]
            gap = best_dps / max(base, 1.0)
            flag = "✅" if gap > 1.05 else ("➖" if gap > 1.0 else "⚠️")
            cells = " ".join(f"{AFFIX_LABEL[a]}:{dps_by[a]:.0f}" for a in AFFIXES)
            print(f"  {flag} {bname:<7} [{cells}] 最优={AFFIX_LABEL[best_at]} 收益{best_dps/base:.2f}×")
            rows_out.append({
                "class": cname, "build": bname,
                "dps_by_affix": {AFFIX_LABEL[a]: round(dps_by[a]) for a in AFFIXES},
                "best_affix": AFFIX_LABEL[best_at], "gap": round(gap, 2),
            })
    print("\n== 乘区最优倾向汇总 ==")
    for r in rows_out:
        print(f"  {r['class']}·{r['build']}: 最优 {r['best_affix']} ({r['gap']:.2f}×)")


if __name__ == "__main__":
    main()
