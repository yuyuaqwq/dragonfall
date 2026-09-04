# -*- coding: utf-8 -*-
"""v175 R 系列自动修复：CD 技 ratio 上调到"值得用"曲线。

规则（v175 R1 模型，鱼鱼 2026-09-05 授权格温落地）：
  0CD 填充技 DPS = d0/t0（d0=单发, t0=行动间隔）
  CD 技值得用 ⟺ d1 ≥ 0.6 × d0 × c / t0（c=CD 秒）
  但完全按此会上调过猛（CD 技单发可能到 0CD 的 10 倍+）——需结合峰值红线收敛。

实际采用的分档目标（平衡"值得用"与"不碾压"）：
  参考法师健康曲线（唯一正常职业，曾校准）：基础 1.0-1.7 → t1 1.5-1.9 → t2 1.8-2.1 → t3 2.0-2.5
  对每职业：同位置 CD 技 ratio 提到 ≥ 同档基础技 ratio 的 1.4-1.8 倍（CD 给单发优势）
  多段技(hits>=2)：ratio 是每段值，等效 = ratio×hits，按等效对齐
  条件技（cond 带 mult）：基础 ratio 可低些（条件触发补），按等效对齐
  真伤技：无视防御自带优势，上调幅度减半

输出：待改清单 JSON（技能名/旧ratio/新ratio/来源行），供 apply 脚本精确 patch。
只改 exprs 里 atk*/matk* 系数 + 同步 desc 百分比文案（power 旧字段不动，已不参与计算）。

用法：python scripts/build_matrix/r1_fix_gen.py [--dry]
"""
from __future__ import annotations
import os, sys, json, re

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

# 目标基础倍率表（每职业基础技中位 ratio，作为同档参照）
# 修复目标：CD 技 ratio 提到 ≥ 该职业基础技中位 × RATIO_TARGET（CD>0 的单发优势倍数）
RATIO_TARGET = 1.6   # CD 技单发 = 基础技的 1.6 倍（含机制/暴击期望折让）
FIX_CD_MIN = 4.0     # CD<4 的不算 CD 技（微CD不修）


def ratio_of_expr(expr: str):
    """exprs 单条里的 (atk|matk)*X 系数。"""
    m = re.search(r"(atk|matk)\*([\d.]+)", expr)
    if m:
        return m.group(1), float(m.group(2))
    return None, None


def all_dmg(cid):
    """(技能名, 学lv, cd, ratio, hits, kind, cond_mult, expr, src_id)。"""
    out = []
    seen = set()

    def add(info, src_id):
        nm = info.get("name", "")
        if nm in seen:
            return
        kind = str(info.get("kind", ""))
        if not (kind.startswith(("物理", "魔法")) or kind == "真伤"):
            return
        exprs = info.get("exprs") or []
        if not exprs:
            return
        stat, ratio = ratio_of_expr(str(exprs[0]))
        if ratio is None:
            return
        seen.add(nm)
        # cond 带倍率？粗取 desc/cond 里的 x1.3/x1.4/x1.5
        cond_mult = 1.0
        cond = str(info.get("cond") or "")
        m = re.search(r"[x×](1\.\d+)", cond + str(info.get("desc", "")))
        if m:
            cond_mult = float(m.group(1))
        out.append({
            "name": nm, "lv": int(info.get("lv", 1) or 1),
            "cd": float(info.get("cd", 0) or 0),
            "hits": int(info.get("hits", 1) or 1),
            "kind": kind, "ratio": ratio, "stat": stat,
            "cond_mult": cond_mult, "expr": str(exprs[0]),
            "src": src_id, "mp": float(info.get("mp", 0) or 0),
        })

    for info in SK.PLAYER_SKILLS.get(cid, {}).get("skills", {}).values():
        add(info, "base")
    br = SK.BRANCH_SKILLS.get(cid, {}).get("branches", {}) or {}
    for tier, tdef in br.items():
        if not isinstance(tdef, dict):
            continue
        for line, skills in tdef.items():
            if not isinstance(skills, dict):
                continue
            for info in skills.values():
                if isinstance(info, dict):
                    add(info, f"tier{tier}:{line}")
    return out


def gen_fixes(cid, base_ratio_ref):
    """生成该职业修复清单：转职线 CD 技 ratio < 基础参照×0.9 → 上调到基础参照水平。
    v175c 修正：只修转职线技（src 含 tier）——基础 CD 技（猛击/雷击等）是现有门禁基线，
    且法师元素等健康 CD 技（织焰 1.767 > 参照 1.5）不该动。目标 = 基础参照 × 1.2（CD 单发略优）。
    """
    rows = all_dmg(cid)
    fixes = []
    for r in rows:
        if r["src"] == "base":
            continue  # 基础技能不动（门禁基线）
        if r["cd"] < FIX_CD_MIN:
            continue
        # 等效单发（多段×hits，条件×mult）
        eff = r["ratio"] * r["hits"] * r["cond_mult"]
        if eff >= base_ratio_ref * 0.9:
            continue  # 已够（等效 ≥ 基础参照 90%）
        # 上调目标：等效达到基础参照的 1.2 倍（CD 技单发略优但不碾压）
        target_eff = base_ratio_ref * 1.2
        new_ratio = round(target_eff / (r["hits"] * r["cond_mult"]), 2)
        # 真伤穿防优势，补一半
        if r["kind"] == "真伤":
            new_ratio = round(target_eff * 0.75 / (r["hits"] * r["cond_mult"]), 2)
        fixes.append({
            "name": r["name"], "cd": r["cd"], "lv": r["lv"],
            "old_ratio": r["ratio"], "new_ratio": max(new_ratio, r["ratio"] + 0.2),
            "hits": r["hits"], "cond_mult": r["cond_mult"],
            "kind": r["kind"], "stat": r["stat"], "src": r["src"],
            "expr": r["expr"], "mp": r["mp"],
        })
    return fixes


def main():
    dry = "--dry" in sys.argv
    out_json = None
    if "--json" in sys.argv:
        idx = sys.argv.index("--json")
        out_json = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
    # 各职业基础技 ratio 参照（取前 3 个低学lv基础输出技中位）
    refs = {}
    for cid in ("cls_zhan_shi", "cls_fa_shi", "cls_you_xia", "cls_mu_shi",
                "cls_ci_ke", "cls_wu_seng", "cls_shi_ren"):
        rows = all_dmg(cid)
        basics = sorted([r for r in rows if r["lv"] <= 12 and r["cd"] == 0],
                        key=lambda x: x["lv"])[:3]
        if basics:
            ratios = [r["ratio"] for r in basics]
            refs[cid] = sum(ratios) / len(ratios)
            print(f"{cid}: 基础技参照 ratio ≈ {refs[cid]:.2f} "
                  f"({[r['name'] for r in basics]})")

    total = 0
    all_fixes = {}
    for cid in ("cls_zhan_shi", "cls_fa_shi", "cls_you_xia", "cls_mu_shi",
                "cls_ci_ke", "cls_wu_seng", "cls_shi_ren"):
        base_ref = refs.get(cid, 1.0)
        fixes = gen_fixes(cid, base_ref)
        all_fixes[cid] = fixes
        if not fixes:
            print(f"\n{cid}: ✅ 无需修复")
            continue
        print(f"\n{cid}: {len(fixes)} 个 CD 技需上调（基础参照 {base_ref:.2f}，目标≈{base_ref*1.2:.2f}）")
        for f in fixes:
            print(f"  {f['name']:<8} CD{f['cd']:<4.0f} ratio {f['old_ratio']}→{f['new_ratio']} "
                  f"(hits{f['hits']} cond{f['cond_mult']}) [{f['src']}]")
        total += len(fixes)
    print(f"\n== 总计 {total} 个技能待修 ==")
    if out_json:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(all_fixes, f, ensure_ascii=False, indent=1)
        print(f"修复清单 → {out_json}")


if __name__ == "__main__":
    main()
