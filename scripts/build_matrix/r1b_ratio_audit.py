# -*- coding: utf-8 -*-
"""v175 R1b ratio 倒挂全量审计：列出所有"后期(高学Lv) ratio < 前期(低学Lv)"的输出技。

发现（v175 R1 复核）：全职业（法师除外）转职技 exprs ratio 系统性低于基础技——
  战士 早期 ratio 中位 1.2 vs 后期 0.53
  刺客 1.2 vs 0.57 / 拳师 0.9 vs 0.65 / 游侠 1.3 vs 0.2-0.6
  法师例外（1.6 vs 1.71 正常）——当初校准过

这就是"0CD 碾压 CD 高阶技"的真正病根：高阶技单发倍率比基础技还低，CD 技更吃亏。
（r1_scan 的"DPS 红线"会误伤——不是 0CD 太强，是后期 ratio 填错）

本工具输出：每职业 每技能(学Lv, CD, ratio) 按学Lv 排序，标出 ratio 低于"该职业前 10 级内基础技中位"的技能。
用法：python scripts/build_matrix/r1b_ratio_audit.py
"""
from __future__ import annotations
import os, sys, re, json

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


def ratio_of(info):
    exprs = info.get("exprs") or []
    if not exprs:
        return None
    m = re.search(r"(atk|matk)\*([\d.]+)", str(exprs[0]))
    return float(m.group(2)) if m else None


def all_dmg(cid):
    """该职业全部输出技 (name, lv, cd, ratio, kind, desc_snippet)。"""
    out = []
    seen = set()
    for info in SK.PLAYER_SKILLS.get(cid, {}).get("skills", {}).values():
        kind = str(info.get("kind", ""))
        if kind.startswith("物理") or kind.startswith("魔法") or kind == "真伤":
            r = ratio_of(info)
            if r is not None:
                seen.add(info["name"])
                out.append({"name": info["name"], "lv": int(info.get("lv", 1) or 1),
                            "cd": float(info.get("cd", 0) or 0), "ratio": r,
                            "kind": kind, "src": "base",
                            "desc": str(info.get("desc", ""))[:40]})
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
                kind = str(info.get("kind", ""))
                if kind.startswith("物理") or kind.startswith("魔法") or kind == "真伤":
                    r = ratio_of(info)
                    nm = info.get("name", "")
                    if r is not None and nm not in seen:
                        seen.add(nm)
                        out.append({"name": nm, "lv": int(info.get("lv", 1) or 1),
                                    "cd": float(info.get("cd", 0) or 0), "ratio": r,
                                    "kind": kind, "src": f"tier{tier}:{line}",
                                    "desc": str(info.get("desc", ""))[:40]})
    out.sort(key=lambda x: x["lv"])
    return out


def main():
    print("== v175 R1b ratio 倒挂审计（后期技 ratio vs 前10级基础技中位）==")
    for cid in ("cls_zhan_shi", "cls_fa_shi", "cls_you_xia", "cls_ci_ke",
                "cls_wu_seng", "cls_mu_shi", "cls_shi_ren"):
        cname = SK.PLAYER_SKILLS.get(cid, {}).get("name", cid)
        rows = all_dmg(cid)
        if not rows:
            continue
        base10 = [r for r in rows if r["lv"] <= 10]
        if not base10:
            continue
        import statistics
        base_med = statistics.median(r["ratio"] for r in base10)
        print(f"\n--- {cname}（基础技≤Lv10 ratio 中位={base_med:.2f}）---")
        low = []
        for r in rows:
            # 标记：学Lv>20 且 ratio < 基础中位（后期技不该弱于基础）
            if r["lv"] > 20 and r["ratio"] < base_med * 0.85:
                low.append(r)
        if not low:
            print("  ✅ 无倒挂（后期技 ratio 均 ≥ 基础技）")
            continue
        print(f"  {'技能':<8}{'学Lv':<6}{'CD':<6}{'ratio':<8}{'来源'}")
        for r in low:
            flag = "🔴" if r["ratio"] < base_med * 0.5 else "🟠"
            print(f"  {flag} {r['name']:<8}{r['lv']:<6}{r['cd']:<6.0f}{r['ratio']:<8.2f}{r['src']}")


if __name__ == "__main__":
    main()
