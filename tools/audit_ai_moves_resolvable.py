# -*- coding: utf-8 -*-
"""审计：配了 AI 选招的怪，其 AI 引用的技能能否真解析（三分类）。

背景（2026-09-11）：battle2/ai.py resolve_ai_move 原先只按 when 条件选 move、
不校验技能此刻可执行；ActCtx.__post_init__ 只从 actor["_skill_index"] 解析技能
（无全局兜底）→ 索引不到时 do_skill 拿到 info={} 直接 return []：**静默白耗一回合**。

分类口径（引擎在每次决策前 refresh_skill_index，故运行期追加的技能也算可解析）：
  OK-base   在 spawn 定义的 skills 里（开战即可解析）
  OK-phase  在 MONSTER_MODS.phases[].add_skills 或阶段模板 add_skills 里
            （转阶段后追加 → 刷新索引后可解析）
  DEAD      两处都没有 → AI 永远选不到可执行的招（真缺陷：AI 引用不存在的技能）

跑法：python tools/audit_ai_moves_resolvable.py  （DEAD 非空 → exit 1）
"""
import os
import sys
import ast

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(PLUGIN_DIR, "test_audit_ai.db"))
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)

from game.battle2 import config as _b2c  # noqa: E402
_b2c.load_game_defaults()
from game.battle2.ai import normalize_ai  # noqa: E402
from game.data.monster_mods import MONSTER_MODS  # noqa: E402
from game.data.monsters import MONSTER_SKILLS  # noqa: E402

SPAWN_FILES = ["game/data/subareas.py", "game/data/instances.py",
               "game/data/mesh_rooms_east_abyss.py", "game/data/mesh_rooms_south.py",
               "game/data/mesh_rooms_west_north.py", "game/data/hidden_monsters.py",
               "game/data/trial_tower.py", "game/data/wild_king_data.py"]


def collect_spawns():
    """内容里的 6 元组怪定义 → {mid: set(skills)}"""
    out = {}
    for fn in SPAWN_FILES:
        p = os.path.join(PLUGIN_DIR, fn)
        if not os.path.exists(p):
            continue
        tree = ast.parse(open(p, encoding="utf-8").read())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) == 6:
                try:
                    vals = [ast.literal_eval(e) for e in node.elts]
                except Exception:
                    continue
                mid, _name, role, lv, skills, drops = vals
                if isinstance(mid, str) and isinstance(skills, (list, tuple)) \
                        and isinstance(drops, (list, tuple)) and role in ("normal", "elite", "boss"):
                    out.setdefault(mid, set()).update(str(s) for s in skills)
    return out


def phase_skills_of(mod: dict) -> set:
    """mod.phases[].add_skills ∪ 阶段模板（phase_id → merge_phase_config）add_skills。"""
    got = set()
    merge = None
    try:
        from game.data.boss_phases import merge_phase_config as merge
    except Exception:
        merge = None
    for ph in (mod.get("phases") or []):
        if not isinstance(ph, dict):
            continue
        for s in (ph.get("add_skills") or []):
            got.add(str(s))
        _pid = ph.get("phase_id")
        if _pid and merge is not None:
            try:
                _m = merge(_pid, ph) or {}
                for s in (_m.get("add_skills") or []):
                    got.add(str(s))
            except Exception:
                pass
        # 多阶段 add（instances 里 phases 亦可能带 add_skills 列表）
    for key in ("openings", "on_interrupt"):
        _v = mod.get(key)
        if isinstance(_v, dict):
            for s in (_v.get("add_skills") or []):
                got.add(str(s))
    return got


def ai_skill_refs(mod: dict) -> list:
    """AI 声明引用到的技能 key（weights / moves[].then.skill）。"""
    ai = mod.get("ai")
    if not ai:
        return []
    out = []
    dummy = {"ai": ai}
    for mv in (normalize_ai(dummy) or {}).get("moves") or []:
        sk = ((mv.get("then") or {}).get("skill"))
        if sk:
            out.append(str(sk))
    return out


def main():
    spawns = collect_spawns()
    rows = []
    dead = []
    for mid, mod in sorted(MONSTER_MODS.items()):
        refs = ai_skill_refs(mod)
        if not refs:
            continue
        base = spawns.get(mid) or set()
        phs = phase_skills_of(mod)
        for sk in dict.fromkeys(refs):
            if sk not in MONSTER_SKILLS:
                cls = "DEAD"     # 怪技能表里根本没有这个 key
                why = "怪技能表无此 key"
            elif sk in base:
                cls = "OK-base"
                why = "spawn skills"
            elif sk in phs:
                cls = "OK-phase"
                why = "阶段 add_skills"
            else:
                cls = "DEAD"
                why = f"spawn/阶段均无（spawn={sorted(base)} phase={sorted(phs)}）"
            rows.append((mid, sk, cls))
            if cls == "DEAD":
                dead.append((mid, sk, why))
    n_ai = sum(1 for m in MONSTER_MODS.values() if m.get("ai"))
    print(f"配 AI 的怪 {n_ai} 只 | AI 引用技能 {len(rows)} 处")
    for cls in ("OK-base", "OK-phase", "DEAD"):
        sub = [r for r in rows if r[2] == cls]
        print(f"  {cls:9s} {len(sub):3d} 处")
    print()
    if dead:
        print(f"★★ DEAD {len(dead)} 处（AI 引用到永远不会持有的技能）：")
        for mid, sk, why in dead:
            print(f"   ❌ {mid:22s} {sk:26s} {why}")
    else:
        print("✅ 无 DEAD：所有 AI 引用的技能要么开战即持有、要么转阶段追加")
    return 0 if not dead else 1


if __name__ == "__main__":
    sys.exit(main())
