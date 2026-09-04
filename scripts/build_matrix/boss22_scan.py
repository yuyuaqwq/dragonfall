# -*- coding: utf-8 -*-
"""v175c 22 本全 Boss 期望全扫 —— 每职业 dps 流派 × 全部 22 副本 Boss。

鱼鱼拍板（2026-09-04）：22 本全 Boss 全扫（工作量×4，最彻底）。
口径：
  - 每职业每 Boss：玩家等级 = 副本推荐等级附近（进本级用推荐等级，跨级挑战用高等级）
  - 单人本（min=1）：单人打，装备 = 对应阶段档
  - 多人本（min≥2）：单人进不去——用"队伍档"但玩家按单角色算输出（相对排名），
    标注 [多人本]；真正队伍验证走 team_comp 既有门禁
  - 期望引擎（秒级）全扫 → JSON 落盘，供报告/门禁

用法：python scripts/build_matrix/boss22_scan.py [--json out.json]
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
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from build_matrix.build_matrix import build_vs_boss, resolve_attr
from build_matrix.boss_matrix import boss_def_of, all_bosses
from build_matrix.schema import KNOWN_CLASSES
from data.plugins.dragonfall.game import content as C

# 副本等级 → 玩家等级/装备档（阶段匹配）
def stage_for(inst_lv: int):
    """副本等级 → (玩家等级, 装备档)。玩家略高于副本（主线推进正常节奏）。"""
    if inst_lv <= 20:
        return 24, "solo_mid"        # P2 档
    elif inst_lv <= 40:
        return 45, "team_purple9"     # P3 档
    elif inst_lv <= 65:
        return 60, "team_purple9"     # P3.5 转职后
    elif inst_lv <= 85:
        return 75, "team_purple9"     # P4 档
    else:
        return 95, "team_orange9"     # P5 档


def scan_all() -> dict:
    out = {}
    bosses = all_bosses()
    for cid in KNOWN_CLASSES:
        fp = os.path.join(_BM_DIR, "..", "balance_data", f"{cid}.json")
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as f:
            jd = json.load(f)
        cname = jd.get("class_name", cid)
        cls_out = {}
        for bname, bdef in jd.get("builds", {}).items():
            if bdef.get("role") != "dps":
                continue  # 全扫聚焦 dps 流派（heal/tank 定位另论）
            rotation = bdef.get("rotation", [])
            rec_name = bdef.get("attr_preset", "")
            apresets = jd.get("attr_presets", {})
            rec_preset = apresets.get(rec_name, {"str": "all"})
            boss_rows = {}
            for b in bosses:
                iid, inst_lv, mn = b["iid"], b["inst_lv"], b["min_players"]
                plv, loadout = stage_for(inst_lv)
                attr = resolve_attr(rec_preset, plv)
                boss_def = boss_def_of(iid)
                if not boss_def:
                    continue
                is_solo = mn == 1
                try:
                    r = build_vs_boss(cid, plv, loadout, attr, rotation, boss_def,
                                      int(boss_def[3]), iid=iid, n_players=1)
                    kr = r["kill_rounds"]
                    boss_rows[iid] = {
                        "inst_lv": inst_lv, "boss_lv": int(boss_def[3]),
                        "boss_name": b["boss_name"], "min_players": mn,
                        "mode": "solo" if is_solo else "multi(队伍档)",
                        "player_lv": plv, "loadout": loadout,
                        "kill_rounds": kr, "survive_rounds": r["survive_rounds"],
                        "verdict": r["verdict"],
                    }
                except Exception as ex:
                    boss_rows[iid] = {"error": str(ex)}
            cls_out[bname] = boss_rows
        out[cid] = {"name": cname, "builds": cls_out}
    return out


def fmt_table(data: dict) -> str:
    """控制台：每 Boss 列出各职业 dps 流派击杀轮（有值才显示）。"""
    lines = []
    bosses = all_bosses()
    for b in bosses:
        iid = b["iid"]
        mn = b["min_players"]
        mode = "单" if mn == 1 else f"多{mn}"
        cells = []
        for cid, cinfo in data.items():
            for bname, brows in cinfo["builds"].items():
                row = brows.get(iid)
                if row and row.get("kill_rounds"):
                    cells.append(f"{cinfo['name'][:2]}:{row['kill_rounds']}")
                elif row and row.get("kill_rounds") is None:
                    cells.append(f"{cinfo['name'][:2]}:×")
        lines.append(f"{iid:<22} Lv{b['inst_lv']:<3}[{mode}] {' '.join(cells)}")
    return "\n".join(lines)


if __name__ == "__main__":
    json_out = None
    if "--json" in sys.argv:
        idx = sys.argv.index("--json")
        json_out = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
    t0 = time.time()
    data = scan_all()
    print(f"== 22 本全 Boss 期望全扫（耗时 {time.time()-t0:.0f}s）==")
    print(fmt_table(data))
    if json_out:
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1, default=str)
        print(f"\nJSON → {json_out}")
