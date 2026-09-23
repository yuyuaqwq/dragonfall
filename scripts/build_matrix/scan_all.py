# -*- coding: utf-8 -*-
"""v175 全矩阵基线扫描 CLI —— 跑全职业×流派×5阶段×加点 → JSON/表格。

用法：
  python scripts/build_matrix/scan_all.py                     # 全矩阵（7×3×5×~4 ≈ 400 格）
  python scripts/build_matrix/scan_all.py --json out.json     # 落盘 JSON
  python scripts/build_matrix/scan_all.py --fast              # 每流派只跑推荐加点（~100 格）
"""
from __future__ import annotations
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

from build_matrix.build_matrix import (
    rotation_dps, build_panel, resolve_attr, STAGE_CFG,
)
from build_matrix.schema import KNOWN_CLASSES
from numeric_lib.monster import build as _mb


def scan_one(cid: str, bname: str, bdef: dict, stage_cfg, attr_name: str,
             attr_preset: dict) -> dict:
    """单格：流派×阶段×加点 → 对同级 boss 击杀/生存。"""
    stage_name, lv, loadout = stage_cfg
    attr = resolve_attr(attr_preset, lv)
    rotation = bdef.get("rotation", [])
    if not rotation:
        return {"error": "no rotation"}
    m = _mb("boss", lv)
    tgt = {"role": "boss", "lv": lv, "max_hp": m.get("max_hp", 5000),
           "def": m.get("def", 0), "mdef": m.get("mdef", 0),
           "hp": m.get("max_hp", 5000)}
    try:
        r = rotation_dps(cid, lv, loadout, attr, rotation, fight_len=60.0, target=tgt)
        st = build_panel(cid, lv, loadout, attr)
    except Exception as ex:
        return {"error": str(ex)}
    # 承伤（同 build_vs_boss 口径：Boss 单发 ×1.35 enraged 保守）
    from ext_combat.battle.formulas import calc_damage
    boss_atk = float(m.get("atk", 0)) * 1.35
    boss_matk = float(m.get("matk", 0)) * 1.35
    d_phys = calc_damage(int(boss_atk), int(st.get("def", 0)), variance=0.0, dmg_type="phys")
    d_magi = calc_damage(int(boss_matk), int(st.get("mdef", 0)), variance=0.0, dmg_type="magi")
    boss_hit = max(d_phys, d_magi)
    survive = float(st.get("max_hp", 1000)) / max(boss_hit, 1.0) if boss_hit > 0 else 999.0
    kr = r["kill_rounds"]
    # 判定（期望模型快速标注；真引擎仲裁为准）
    if kr is None:
        verdict = "杀不死"
    elif survive < kr * 0.9:
        verdict = "先死"
    elif kr > 80:
        verdict = "拖太久"
    else:
        verdict = "可过"
    return {
        "stage": stage_name, "lv": lv, "loadout": loadout,
        "attr": attr_name, "attr_pts": attr,
        "hp": st.get("max_hp", 0), "atk": st.get("atk", 0), "matk": st.get("matk", 0),
        "spd": st.get("spd", 0), "mp": st.get("max_mp", 0),
        "dps": round(r["dps"], 1),
        "kill_rounds": kr, "survive_rounds": round(survive, 1),
        "empty_mp_rounds": r["empty_mp_rounds"],
        "boss_hp": m.get("max_hp", 0), "boss_hit": round(boss_hit, 1),
        "verdict": verdict,
    }


def scan_all(fast: bool = False) -> dict:
    out = {}
    bal_dir = os.path.join(_BM_DIR, "..", "balance_data")
    for fn in sorted(os.listdir(bal_dir)):
        if not fn.startswith("cls_") or not fn.endswith(".json"):
            continue
        cid = fn[:-5]
        with open(os.path.join(bal_dir, fn), encoding="utf-8") as f:
            jd = json.load(f)
        cname = jd.get("class_name", cid)
        builds_out = {}
        for bname, bdef in jd.get("builds", {}).items():
            attr_presets = jd.get("attr_presets", {})
            rec_name = bdef.get("attr_preset", "")
            # 加点组合：推荐 + 全预设（fast 只跑推荐）
            if fast:
                preset_items = [(rec_name, attr_presets[rec_name])] if rec_name in attr_presets else []
            else:
                preset_items = list(attr_presets.items())
                # 推荐放第一
                if rec_name in attr_presets:
                    preset_items = [(rec_name, attr_presets[rec_name])] + \
                                   [x for x in preset_items if x[0] != rec_name]
            stages_out = {}
            for stage_cfg in STAGE_CFG:
                stage_name = stage_cfg[0]
                attrs_out = {}
                for aname, apreset in preset_items:
                    attrs_out[aname] = scan_one(cid, bname, bdef, stage_cfg, aname, apreset)
                stages_out[stage_name] = attrs_out
            builds_out[bname] = stages_out
        out[cid] = {"name": cname, "builds": builds_out}
    return out


def fmt_table(data: dict) -> str:
    """控制台表格：每职业每流派 5 阶段 → 推荐加点击杀轮。"""
    lines = []
    for cid, cinfo in data.items():
        for bname, bstages in cinfo["builds"].items():
            cells = []
            for stage in ("P1", "P2", "P3", "P4", "P5"):
                s = bstages.get(stage, {})
                rec = None
                # 取第一个非 error
                for aname, row in s.items():
                    if "kill_rounds" in row:
                        rec = row
                        break
                if rec and rec["kill_rounds"]:
                    cells.append(f"{stage}:{rec['kill_rounds']}轮")
                elif rec:
                    cells.append(f"{stage}:{rec['verdict']}")
                else:
                    cells.append(f"{stage}:err")
            lines.append(f"{cinfo['name']:<4}|{bname:<7}| " + " | ".join(cells))
    return "\n".join(lines)


if __name__ == "__main__":
    fast = "--fast" in sys.argv
    json_out = None
    if "--json" in sys.argv:
        idx = sys.argv.index("--json")
        json_out = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
    t0 = time.time()
    data = scan_all(fast=fast)
    print(f"== 全矩阵扫描 {'(fast 推荐加点)' if fast else '(全加点)'} 耗时 {time.time()-t0:.0f}s ==")
    print(fmt_table(data))
    if json_out:
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1, default=str)
        print(f"\nJSON → {json_out}")
