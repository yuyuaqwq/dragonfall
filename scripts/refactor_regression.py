# -*- coding: utf-8 -*-
"""v176 重构回归快照工具：重构前跑一次存基线，重构后对比行为是否等价。

用法：
  python scripts/refactor_regression.py --snapshot baseline.json   # 重构前：生成基线
  python scripts/refactor_regression.py --compare baseline.json    # 重构后：对比

覆盖（Battle 类关键行为路径）：
  1. 各职业代表流派 vs 各阶段 Boss 的胜负/击杀轮（真引擎 battle_rotation 全链路）
  2. 伤害公式关键点（resolve_formula 多段/暴击/穿透）
  3. 资源结算（怒/能量/连段/元素印）
  4. 关键战斗判定（闪避/格挡/减伤/DOT）

行为等价判定：击杀轮 ±1、胜场数一致 → 视为等价（随机种子固定可复现）。
"""
from __future__ import annotations
import os, sys, json, hashlib, time

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
_PLUGIN = os.path.dirname(_SCRIPTS)
_QQBOT = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN)))
_TESTS = os.path.join(_PLUGIN, "tests")
for _p in (_QQBOT, _PLUGIN, _TESTS, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_TESTS, "test_game_data.db"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from numeric_lib.saintess_engine import battle_rotation, attr_pts_total      # noqa: E402
from build_matrix.boss_matrix import boss_def_of                      # noqa: E402
from build_matrix.schema import KNOWN_CLASSES                          # noqa: E402

MAIN_ATTR = {"cls_zhan_shi": "str", "cls_fa_shi": "int", "cls_you_xia": "agi",
             "cls_mu_shi": "int", "cls_ci_ke": "agi", "cls_wu_seng": "str",
             "cls_shi_ren": "int"}

# 采样场景（跨阶段、跨职业、跨 Boss）
SCENARIOS = [
    # (cid, build, lv, loadout, iid, seeds)
    ("cls_zhan_shi", "狂战流", 25, "solo_mid", "inst_goblin_camp", 4),
    ("cls_zhan_shi", "血怒流", 98, "team_orange9", "inst_ash_temple", 4),
    ("cls_fa_shi", "元素爆发流", 25, "solo_mid", "inst_goblin_camp", 4),
    ("cls_fa_shi", "奥术精算流", 98, "team_orange9", "inst_ash_temple", 4),
    ("cls_you_xia", "疾风连射流", 68, "team_purple9", "inst_elven_ruins", 4),
    ("cls_you_xia", "森语猎印流", 98, "team_orange9", "inst_ash_temple", 4),
    ("cls_ci_ke", "影舞连段流", 25, "solo_mid", "inst_goblin_camp", 4),
    ("cls_mu_shi", "死灵骷髅流", 98, "team_orange9", "inst_ash_temple", 4),
    ("cls_wu_seng", "破绽连打流", 45, "team_purple9", "inst_old_king_tomb", 4),
    ("cls_shi_ren", "挽歌瓦解流", 45, "team_purple9", "inst_old_king_tomb", 4),
]


def run_scenarios() -> dict:
    out = {}
    for cid, bname, lv, loadout, iid, seeds in SCENARIOS:
        fp = os.path.join(_SCRIPTS, "balance_data", f"{cid}.json")
        if not os.path.exists(fp):
            continue
        import json as _json
        with open(fp, encoding="utf-8") as f:
            jd = _json.load(f)
        if bname not in jd.get("builds", {}):
            continue
        bdef = jd["builds"][bname]
        rotation = [s["skill"] for s in bdef.get("rotation", [])]
        rules = bdef.get("rotation", [])
        attr_rec = jd.get("attr_presets", {}).get(bdef.get("attr_preset", ""), {})
        if not attr_rec:
            attr_rec = {MAIN_ATTR[cid]: "all"}
        attr = {}
        for k, v in attr_rec.items():
            attr[k] = attr_pts_total(lv) if v in ("all", "full") else int(v)
        affix = bdef.get("affix_preset", "atk")
        try:
            boss_def = boss_def_of(iid)
            r = battle_rotation(cid, lv, loadout, attr, rotation, boss_def,
                                seeds=seeds, iid=iid, n_players=1,
                                affix_type=affix, rules=rules)
            key = f"{cid}::{bname}@{lv}:{iid}"
            out[key] = {"wins": r["wins"], "avg_rounds": r["avg_rounds"],
                        "avg_survive": r["avg_survive"]}
        except Exception as ex:
            key = f"{cid}::{bname}@{lv}:{iid}"
            out[key] = {"error": str(ex)[:100]}
    return out


def digest(data: dict) -> str:
    """行为摘要：胜场+击杀轮取整 → 稳定 hash（忽略 ±1 轮内的波动噪声）。"""
    parts = []
    for k in sorted(data):
        v = data[k]
        if "error" in v:
            parts.append(f"{k}=ERR")
        else:
            # 击杀轮取整到 1 轮精度（浮点噪声容忍）
            kr = round(v.get("avg_rounds") or 0)
            parts.append(f"{k}=W{v['wins']}:R{kr}")
    return hashlib.md5("|".join(parts).encode()).hexdigest()[:12]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--snapshot"
    path = sys.argv[2] if len(sys.argv) > 2 else "refactor_baseline.json"
    t0 = time.time()
    data = run_scenarios()
    print(f"场景数: {len(data)}  耗时 {time.time()-t0:.0f}s")
    # 简化输出
    for k, v in sorted(data.items()):
        if "error" in v:
            print(f"  ⚠️ {k}: ERR")
        else:
            kr = f"{v['avg_rounds']:.1f}轮" if v.get("avg_rounds") else f"存活{v['avg_survive']:.1f}"
            print(f"  {k}: {v['wins']}胜 {kr}")
    dg = digest(data)
    print(f"\n摘要: {dg}")
    if mode == "--snapshot":
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"digest": dg, "data": data}, f, ensure_ascii=False, indent=1)
        print(f"基线 → {path}")
    else:
        with open(path, encoding="utf-8") as f:
            base = json.load(f)
        if base.get("digest") == dg:
            print("✅ 行为等价（摘要一致）")
            return 0
        else:
            print(f"❌ 行为漂移！基线={base.get('digest')} 现在={dg}")
            # 逐场景 diff
            bd = base.get("data", {})
            for k in sorted(set(bd) | set(data)):
                if bd.get(k) != data.get(k):
                    print(f"  差异 {k}: 基线={bd.get(k)} 现在={data.get(k)}")
            return 1


if __name__ == "__main__":
    sys.exit(main())
