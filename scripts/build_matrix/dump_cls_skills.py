# -*- coding: utf-8 -*-
"""v175 dump 职业全技能字段 → JSON（职业 agent 工作母机）。

用法：
  python scripts/build_matrix/dump_cls_skills.py <cls_id> [out_path]
默认 out_path = scripts/balance_data/_dump_<cls_id>_skills.json（临时，勿提交）

输出每技能关键字段：lv/mp/cast/cd/kind/mech/mech_val/effect/res_cost/cond/
buff_turns/passive/desc/heal_formula/power/exprs/_src(base 或 tierX:线名)
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

FIELDS = ("lv", "mp", "cast", "cd", "kind", "mech", "mech_val", "effect",
          "res_cost", "cond", "buff_turns", "passive", "desc",
          "heal_formula", "power", "exprs", "hits", "aoe", "pierce",
          "res_gain", "shaken_gain", "melody", "summon", "finale", "faith")


def dump(cls_id: str) -> dict:
    from data.plugins.dragonfall.game.data import skills as SK
    out = {}
    cdef = SK.PLAYER_SKILLS.get(cls_id, {})
    for skid, info in cdef.get("skills", {}).items():
        nm = info.get("name", skid)
        row = {k: info.get(k) for k in FIELDS}
        row["_src"] = "base"
        row["_skid"] = skid
        out[nm] = row
    br = SK.BRANCH_SKILLS.get(cls_id, {}).get("branches", {})
    for tier, tdef in br.items():
        if not isinstance(tdef, dict):
            continue
        for line, skills in tdef.items():
            if not isinstance(skills, dict):
                continue
            for sk, info in skills.items():
                if not isinstance(info, dict):
                    continue
                nm = info.get("name", sk)
                if nm in out:
                    continue  # base 优先
                row = {k: info.get(k) for k in FIELDS}
                row["_src"] = f"tier{tier}:{line}"
                row["_skid"] = sk
                out[nm] = row
    return out


def main():
    cls_id = sys.argv[1] if len(sys.argv) > 1 else "cls_zhan_shi"
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(_BM_DIR), "balance_data", f"_dump_{cls_id}_skills.json")
    data = dump(cls_id)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    n_dmg = sum(1 for r in data.values() if str(r.get("kind", "")).startswith(("物理", "魔法")))
    n_gain = sum(1 for r in data.values() if str(r.get("kind", "")) == "增益")
    n_heal = sum(1 for r in data.values() if str(r.get("kind", "")) == "治疗")
    print(f"dumped {cls_id}: {len(data)} 技能 ({n_dmg} 输出 / {n_gain} 增益 / {n_heal} 治疗) → {out_path}")


if __name__ == "__main__":
    main()
