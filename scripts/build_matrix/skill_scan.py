# -*- coding: utf-8 -*-
"""v175 全技能效率扫描器 —— 职业平衡矩阵的"工作母机"。

对任意职业的 PLAYER_SKILLS 全表，逐技能算效率指标，供：
  1. 职业 agent 写效率表 JSON 时对齐口径
  2. 门禁 test_numeric_skill_efficiency.py 直接调用
  3. 期望引擎 build_matrix 读效率表做流派循环评估

口径（与 numeric_lib.player 同源，真实引擎实算）：
  - 面板：player_final_stats（职业/等级/装备/加点/tier）
  - 单发期望：skill_expr_preview 代入面板（v174 exprs / heal_formula 统一口径）
    无 exprs 的增益/治疗按 effect/kind 分类返回 0 或治疗量
  - 出手频率：cast × (SPD_REF/spd)^0.5（numeric_lib.player._interval 同款）
  - 循环周期：cd>0 时 = cd + cast（技能 CD 期间普攻填充由期望引擎算，这里只报原始量）
  - 技能等级：SKILL_UP 实读 max，按阶段档位实算（lv_in_stage 由调用方给）

使用：
  from build_matrix.skill_scan import skill_efficiency_table
  rows = skill_efficiency_table("cls_zhan_shi", stage_lv=45, gear=..., attr=...)
"""
from __future__ import annotations
import os, sys

# ---- 路径引导（与 numeric_lib/env.py 同源，可在 tests/ 下独立跑）----
_BM_DIR = os.path.dirname(os.path.abspath(__file__))                    # scripts/build_matrix/
_SCRIPTS = os.path.dirname(_BM_DIR)                                      # scripts/
_PLUGIN = os.path.dirname(_SCRIPTS)                                      # dragonfall/
_QQBOT = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN)))      # qqbot/
_TESTS = os.path.join(_PLUGIN, "tests")
for _p in (_QQBOT, _PLUGIN, _TESTS, _SCRIPTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_TESTS, "test_game_data.db"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from saintess_engine.formulas import calc_damage, skill_expr_preview, skill_max_level
from game.content_rules.panel import player_final_stats
from data.plugins.dragonfall.game.data import skills as SK     # noqa: E402
from data.plugins.dragonfall.game.data import skill_up as SU   # noqa: E402

try:
    from numeric_lib.constants import SPD_REF, cls_name       # noqa: E402
    from numeric_lib.player import build_player               # noqa: E402
    _HAS_NUMLIB = True
except Exception:  # 极简模式：无 numeric_lib 也能算面板相关量（测试环境兜底）
    SPD_REF = 50.0
    _HAS_NUMLIB = False


def spd_factor(spd: float) -> float:
    """出手速度折算系数 = sqrt(SPD_REF / spd)，与 numeric_lib._interval 同款。"""
    import math
    return math.sqrt(SPD_REF / max(float(spd or 0), 1.0))


def stage_skill_lv(info: dict, player_lv: int) -> int:
    """技能在 stage 的可学等级：技能学习等级 lv<=player_lv 才可用；成长等级取 min(可学后+若干, max)。

    v175 口径（鱼鱼拍板按阶段真实等级）：技能成长按玩家当前阶段能投入的技能等级算。
    简化模型：技能成长等级 = min(SKILL_UP.max, 1 + (player_lv - 技能lv)//3)。
    （近似玩家转职后有 1 级技能 + 每 3 级升 1 级；具体由期望引擎 skill_lv_policy 覆盖。）
    """
    max_lv = skill_max_level(info)
    learn_lv = int(info.get("lv", 1) or 1)
    if player_lv < learn_lv:
        return 0  # 未解锁
    # 默认成长曲线：学得时 1 级，此后每 4 级 +1，封顶 max
    grow = 1 + max(0, (player_lv - learn_lv) // 4)
    return min(grow, max_lv)


def skill_class(info: dict) -> str:
    """技能定位分类（v175 统一口径）：
    - kind 物理/魔法/魔法·X → damage（输出）
    - kind 治疗 → heal
    - kind 增益 → 按 effect 细分 buff / aura / guard
    - 带 cond/控制/减伤 effect → control/guard
    """
    kind = str(info.get("kind", ""))
    if kind.startswith("物理") or kind.startswith("魔法") or kind == "真伤":
        return "damage"
    if kind == "治疗":
        return "heal"
    if kind == "增益":
        eff = str(info.get("effect", ""))
        if eff in ("atk_all", "matk_all", "spd_all", "crit_hit_buff", "dodge_buff", "spd_buff"):
            return "aura"
        if eff in ("shield_self", "reduce", "cc_immune", "cleanse", "stealth", "disengage_dodge"):
            return "guard"
        return "buff"
    return "other"


def _dmg_expr_value(info: dict, st: dict, skill_lv: int) -> float:
    """技能单发期望（exprs / heal_formula 同口径；输出=伤害期望，治疗=0 返回由调用方定）。"""
    _st = dict(st)
    _st["_player_lv"] = int(st.get("level", st.get("_player_lv", 1)) or 1)
    _st["_skill_lv"] = max(1, skill_lv)
    return float(skill_expr_preview(info, skill_lv, _st) or 0.0)


def skill_efficiency_row(cls: str, skid: str, info: dict, st: dict,
                         player_lv: int, edef: int, mdef: int) -> dict:
    """单个技能的效率行（期望引擎/效率表共用）。"""
    skill_lv = stage_skill_lv(info, player_lv)
    cls_lv = stage_skill_lv(info, player_lv)
    raw = _dmg_expr_value(info, st, skill_lv)
    # 过防（exprs 里通常不含防御，需按伤害类型扣防）
    kind = str(info.get("kind", ""))
    phys = kind.startswith("物理")
    dmg_type = "phys" if phys else "magi"
    defv = edef if phys else mdef
    # calc_damage 需要整数 base；raw 可能含 max_hp 等非攻加成
    try:
        base = int(raw)
    except Exception:
        base = int(raw or 0)
    if base > 0 and skill_class(info) == "damage":
        if info.get("pierce") or kind == "真伤":
            dmg = calc_damage(base, 0, pierce=True, dmg_type=dmg_type, variance=0.0)
        else:
            dmg = calc_damage(base, int(defv), variance=0.0, dmg_type=dmg_type)
    else:
        dmg = 0.0
    hits = int(info.get("hits", 1) or 1)
    dmg *= hits
    _cast_raw = info.get("cast")
    _cd_raw = info.get("cd")
    _mp_raw = info.get("mp")
    cast = float(_cast_raw) if _cast_raw not in (None, "", "None") else 1.0
    cd = float(_cd_raw) if _cd_raw not in (None, "", "None") else 0.0
    mp = float(_mp_raw) if _mp_raw not in (None, "", "None") else 0.0
    spd = float(st.get("spd", 50) or 50)
    interval = max((cast + 0.0) * spd_factor(spd), 0.001)
    # 单发效率 / DPS（cd=0 技能按 interval，cd>0 按 cd 周期给理论 DPS 上限）
    cycle = max(cd, 0.0) + cast if cd > 0 else interval
    return {
        "skid": skid,
        "name": info.get("name", skid),
        "lv": int(info.get("lv", 1) or 1),
        "skill_lv": skill_lv,
        "kind": kind,
        "cls": skill_class(info),
        "phys": phys,
        "mp": mp,
        "cast": cast,
        "cd": cd,
        "hits": hits,
        "pierce": bool(info.get("pierce")),
        "raw_expr": raw,
        "dmg": round(dmg, 1),
        "interval": round(interval, 3),
        "cycle": round(cycle, 3),
        "dps": round(dmg / max(cycle, 0.001), 2) if skill_class(info) == "damage" else 0.0,
        "dpe": round(dmg / max(mp, 1.0), 2) if (skill_class(info) == "damage" and mp > 0) else 0.0,
        "mech": info.get("mech") or "",
        "effect": info.get("effect") or "",
        "res_cost": info.get("res_cost") or "",
        "cond": info.get("cond") or "",
        "buff_turns": info.get("buff_turns") or "",
        "aoe": bool(info.get("aoe")),
        "desc": info.get("desc", "")[:80],
    }


def skill_efficiency_table(cls: str, player_lv: int = 45, gear: dict | None = None,
                           attr: dict | None = None, edef: int = 200, mdef: int = 180,
                           opts=None) -> list[dict]:
    """职业全技能效率表（按学习等级排序）。返回 list[效率行]。"""
    cdef = SK.PLAYER_SKILLS.get(cls, {})
    skills = cdef.get("skills", {})
    if _HAS_NUMLIB:
        st = build_player(cls, player_lv, gear, opts, attr=attr)
    else:
        # 兜底：engine 裸面板
        st = player_final_stats(cls, player_lv, gear or {}, 0, attr or {}, 0)
    rows = []
    for skid, info in skills.items():
        r = skill_efficiency_row(cls, skid, info, st, player_lv, edef, mdef)
        rows.append(r)
    rows.sort(key=lambda r: r["lv"])
    return rows


def monster_defense(role: str = "dps", lv: int = 45) -> tuple[int, int]:
    """该等级真实怪的 (edef, mdef)——与 stage.py 同源（build_monster 真实模板）。"""
    try:
        from numeric_lib.monster import build as _mb
        m = _mb(role, lv)
        return int(m.get("def", 0) or 0), int(m.get("mdef", 0) or 0)
    except Exception:
        return 200, 180  # 兜底


def main():
    """CLI：python scripts/build_matrix/skill_scan.py [cls] [lv]
    默认对 Lv45 玩家、同 45 级 dps 怪防御（真实面板）。"""
    import json
    cls = sys.argv[1] if len(sys.argv) > 1 else "cls_zhan_shi"
    lv = int(sys.argv[2]) if len(sys.argv) > 2 else 45
    edef, mdef = monster_defense("dps", lv)
    rows = skill_efficiency_table(cls, player_lv=lv, edef=edef, mdef=mdef)
    print(f"== {cls_name(cls) if _HAS_NUMLIB else cls} 技能效率表 @ Lv{lv} "
          f"(对 dps 怪 edef={edef} mdef={mdef}) ==")
    print(f"{'技能':<8}{'学Lv':<5}{'技Lv':<5}{'type':<8}{'mp':<5}{'cast':<6}{'cd':<5}{'单发':<9}{'周期':<7}{'DPS':<8}{'DPE':<7}备注")
    for r in rows:
        note = ""
        if r["cls"] == "heal":
            note = "治疗"
        elif r["cls"] == "damage":
            note = f"mech={r['mech']}" if r["mech"] else ""
        else:
            note = f"[{r['cls']}] {r['effect']}"
        print(f"{r['name']:<8}{r['lv']:<5}{r['skill_lv']:<5}{r['kind']:<8}{r['mp']:<5.0f}"
              f"{r['cast']:<6.2f}{r['cd']:<5.0f}{r['dmg']:<9.1f}{r['cycle']:<7.2f}{r['dps']:<8.2f}"
              f"{r['dpe']:<7.2f}{note}")


if __name__ == "__main__":
    main()
