# -*- coding: utf-8 -*-
"""v175 R1 违规清单扫描：找出所有 CD>0 但 DPS 低于同职业 0CD 技×0.5 的输出技。

判据（BALANCE_R1_FIX_PLAN §2 模型）：
  CD 技值得用 ⟺ d1 ≥ 0.5 × d0 × c / t0（0.5 = 保守系数，含机制/操作容错）
  简化实现：CD>0 输出技的"等效 DPS（含 CD 周期）" ≥ 同职业最强 0CD 技 DPS × 0.5

输出：每职业违规 CD 技列表（当前值/需要达到值/差距倍数）
用法：python scripts/build_matrix/r1_scan.py
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

from data.plugins.dragonfall.game.data import skills as SK
from build_matrix.skill_scan import skill_efficiency_row, monster_defense
from numeric_lib.player import build_player

# 红线系数（R1 方案 D，待鱼鱼拍板 0.5 还是 0.6）
RATIO_FLOOR = 0.5
LV = 75  # 用高阶档看全技能（含转职技）


def all_skills_at(cid: str, lv: int) -> list:
    """该等级可学全部技能 info（base+branch）。"""
    out = []
    seen = set()
    cdef = SK.PLAYER_SKILLS.get(cid, {})
    for info in cdef.get("skills", {}).values():
        if int(info.get("lv", 99) or 99) <= lv and info["name"] not in seen:
            seen.add(info["name"])
            out.append(info)
    br = SK.BRANCH_SKILLS.get(cid, {}).get("branches", {}) or {}
    for tier, tdef in br.items():
        if not isinstance(tdef, dict):
            continue
        for line, skills in tdef.items():
            if not isinstance(skills, dict):
                continue
            for info in skills.values():
                if not isinstance(info, dict):
                    continue
                if int(info.get("lv", 99) or 99) <= lv and info["name"] not in seen:
                    seen.add(info["name"])
                    out.append(info)
    return out


def main():
    print(f"== v175 R1 CD 技违规清单（Lv{LV}，红线=CD技DPS ≥ 0CD技×{RATIO_FLOOR}）==")
    edef, mdef = monster_defense("dps", LV)
    total_bad = 0
    for cid in ("cls_zhan_shi", "cls_fa_shi", "cls_you_xia", "cls_mu_shi",
                "cls_ci_ke", "cls_wu_seng", "cls_shi_ren"):
        cname = SK.PLAYER_SKILLS.get(cid, {}).get("name", cid)
        st = build_player(cid, LV, {}, None, attr=None)
        rows = []
        for info in all_skills_at(cid, LV):
            kind = str(info.get("kind", ""))
            if not (kind.startswith("物理") or kind.startswith("魔法") or kind == "真伤"):
                continue
            r = skill_efficiency_row(cid, info.get("name", "?"), info, st, LV, edef, mdef)
            rows.append(r)
        # 同职业最强 0CD 技 DPS
        best_0cd = max((r["dps"] for r in rows if r["cd"] <= 0 and r["dps"] > 0), default=1.0)
        # CD 技违规：DPS < 0CD×0.5（CD 技 dps 已按 cd 周期折算，直接比）
        bads = []
        for r in rows:
            if r["cd"] > 0 and r["dps"] > 0:
                floor = best_0cd * RATIO_FLOOR
                if r["dps"] < floor:
                    need_mult = floor / max(r["dps"], 1)
                    bads.append((r["name"], r["lv"], r["cd"], r["dps"], round(need_mult, 1), r["mp"]))
        print(f"\n--- {cname}（最强0CD={best_0cd:.0f} DPS，红线={best_0cd*RATIO_FLOOR:.0f}）---")
        if bads:
            print(f"  {'技能':<8}{'学Lv':<5}{'CD':<5}{'当前DPS':<10}{'需×':<6}{'mp'}")
            for nm, lv, cd, dps, need_mult, mp in sorted(bads, key=lambda x: -x[4]):
                flag = "🔴" if need_mult > 3 else "🟠" if need_mult > 1.5 else "🟡"
                print(f"  {flag} {nm:<8}{lv:<5}{cd:<5}{dps:<10.0f}{need_mult:<6.1f}{mp}")
            total_bad += len(bads)
        else:
            print("  ✅ 无违规")
    print(f"\n== 总违规 CD 技: {total_bad} ==")


if __name__ == "__main__":
    main()
