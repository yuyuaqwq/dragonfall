# -*- coding: utf-8 -*-
"""审计：配了 AI 选招 / 连招链的怪，其引用的技能能否真解析（三分类）。

背景（2026-09-11）：saintess_engine/ai.py resolve_ai_move 原先只按 when 条件选 move、
不校验技能此刻可执行；ActCtx.__post_init__ 只从 actor["_skill_index"] 解析技能
（无全局兜底）→ 索引不到时 do_skill 拿到 info={} 直接 return []：**静默白耗一回合**。
chain（boss_script._check_chains）同样把技能写进 actor["auto_act"] 走 ActCtx 解析，
故连招链引用的技能同样必须真持有。

分类口径（引擎在每次决策前 refresh_skill_index，故运行期追加的技能也算可解析）：
  OK-base   开战即持有（spawn 6 元组 skills）
  OK-phase  阶段 add_skills 里（转阶段追加 → 刷新索引后可解析）
  DEAD      两处都没有 → AI/链永远选不到可执行的招（真缺陷：引用不存在的技能）

「持有」通道（对齐 game/commands/boss_script.py:boss_script_cfg 的引擎口径 ——
MONSTER_MODS 基准 + INSTANCES 副本整体覆盖，v178 E1/E2）：
  ① spawn 6 元组 skills（含 subareas/instances/mesh/hidden/trial/wildking）
  ② MONSTER_MODS[id].phases[].add_skills ＋ 阶段模板 merge_phase_config
  ③ INSTANCES[inst].phases[].add_skills ＋ 阶段模板（**副本内联为权威**）
  ④ MONSTER_MODS/INSTANCES 的 openings / on_interrupt add_skills
「引用」通道：
  ① ai.weights → moves[].then.skill（旧格式归一）
  ② chains[].seq（连招链，经 auto_act 走同一 ActCtx 解析）

跑法：python tools/audit_ai_moves_resolvable.py  （DEAD 非空 → exit 1）
"""
import os
import sys
import ast

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PLUGIN_DIR, "framework"))  # 引擎框架包（S8 物理分离：framework/ 为引擎 submodule）
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(PLUGIN_DIR, "test_audit_ai.db"))
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)

from saintess_engine import config as _b2c  # noqa: E402
from game.content_rules.apply import ensure_engine_configured as _eng_cfg; _eng_cfg()
from saintess_engine.battle.ai import normalize_ai  # noqa: E402
from game.data.monster_mods import MONSTER_MODS  # noqa: E402
from game.data.monsters import MONSTER_SKILLS  # noqa: E402

try:
    from game.data.instances import INSTANCES  # noqa: E402
except Exception:                                             # pragma: no cover
    INSTANCES = {}

SPAWN_FILES = ["game/data/subareas.py", "game/data/instances.py",
               "game/data/mesh_rooms_east_abyss.py", "game/data/mesh_rooms_south.py",
               "game/data/mesh_rooms_west_north.py", "game/data/hidden_monsters.py",
               "game/data/trial_tower.py", "game/data/wild_king_data.py"]


def _tuples_in(node):
    """node 树里全部 6 元组（怪定义）。"""
    out = []
    for n in ast.walk(node):
        if isinstance(n, (ast.Tuple, ast.List)) and len(n.elts) == 6:
            try:
                out.append([ast.literal_eval(e) for e in n.elts])
            except Exception:
                continue
    return out


def _tuples_in_data(obj):
    """普通 Python 数据（dict/list）里全部 6 元组怪定义（INSTANCES 用）。"""
    out = []
    if isinstance(obj, (list, tuple)):
        if len(obj) == 6 and isinstance(obj[0], str) and isinstance(obj[4], (list, tuple)):
            out.append(list(obj))
        for x in obj:
            out.extend(_tuples_in_data(x))
    elif isinstance(obj, dict):
        for x in obj.values():
            out.extend(_tuples_in_data(x))
    return out


def collect_spawns():
    """内容里的 6 元组怪定义 → {mid: set(skills)}"""
    out = {}
    for fn in SPAWN_FILES:
        p = os.path.join(PLUGIN_DIR, fn)
        if not os.path.exists(p):
            continue
        tree = ast.parse(open(p, encoding="utf-8").read())
        for vals in _tuples_in(tree):
            mid, _name, role, lv, skills, drops = vals
            if isinstance(mid, str) and isinstance(skills, (list, tuple)) \
                    and isinstance(drops, (list, tuple)) and role in ("normal", "elite", "boss"):
                out.setdefault(mid, set()).update(str(s) for s in skills)
    return out


def insts_of(mid):
    """哪些 INSTANCES 条目内联了该 boss（引擎按 _inst_id 取副本层 phases/chains）。"""
    got = []
    for iid, inst in (INSTANCES or {}).items():
        if not isinstance(inst, dict):
            continue
        for vals in _tuples_in_data(inst):
            if isinstance(vals[0], str) and vals[0] == mid:
                got.append(inst)
                break
    return got


def _merge_adds(entry, got):
    """单个 phases 条目的 add_skills（＋阶段模板 merge_phase_config）。"""
    if not isinstance(entry, dict):
        return
    for s in (entry.get("add_skills") or []):
        got.add(str(s))
    _pid = entry.get("phase_id")
    if _pid:
        try:
            from game.data.boss_phases import merge_phase_config as merge
            _m = merge(_pid, entry) or {}
            for s in (_m.get("add_skills") or []):
                got.add(str(s))
        except Exception:
            pass


def held_skills_of(mid, mod):
    """该怪在整场战斗中能持有的技能全集（spawn ∪ 各层 phases/opening/on_interrupt）。"""
    got = set()
    for src in [mod] + insts_of(mid):
        for ph in (src.get("phases") or []):
            _merge_adds(ph, got)
        for key in ("opening", "on_interrupt"):
            _v = src.get(key)
            if isinstance(_v, dict):
                for s in (_v.get("add_skills") or []):
                    got.add(str(s))
    return got


def chain_refs_of(mid, mod):
    """连招链引用的技能（mod.chains ∪ 副本 chains）。"""
    out = []
    for src in [mod] + insts_of(mid):
        for ch in (src.get("chains") or []):
            if isinstance(ch, dict):
                out.extend(str(s) for s in (ch.get("seq") or []) if s)
    return out


def ai_skill_refs(mod):
    """AI 声明引用到的技能 key（weights → moves[].then.skill）。"""
    ai = mod.get("ai")
    if not ai:
        return []
    out = []
    for mv in (normalize_ai({"ai": ai}) or {}).get("moves") or []:
        sk = ((mv.get("then") or {}).get("skill"))
        if sk:
            out.append(str(sk))
    return out


def main():
    spawns = collect_spawns()
    rows = []
    dead = []
    n_ai = n_chain = 0
    for mid, mod in sorted(MONSTER_MODS.items()):
        refs = ai_skill_refs(mod)
        chains = chain_refs_of(mid, mod)
        if refs:
            n_ai += 1
        if chains:
            n_chain += 1
        if not refs and not chains:
            continue
        base = spawns.get(mid) or set()
        phs = held_skills_of(mid, mod)
        for sk in dict.fromkeys(refs + chains):
            src_tag = "ai" if sk in refs else "chain"
            if sk not in MONSTER_SKILLS:
                cls, why = "DEAD", "怪技能表无此 key"
            elif sk in base:
                cls, why = "OK-base", "spawn skills"
            elif sk in phs:
                cls, why = "OK-phase", "阶段 add_skills"
            else:
                cls, why = "DEAD", (f"spawn/阶段均无（spawn={sorted(base)} "
                                    f"phase={sorted(phs)}）")
            rows.append((mid, sk, cls, src_tag))
            if cls == "DEAD":
                dead.append((mid, sk, src_tag, why))
    print(f"配 AI 的怪 {n_ai} 只 | 配 chains 的怪 {n_chain} 只 | 引用技能 {len(rows)} 处")
    for cls in ("OK-base", "OK-phase", "DEAD"):
        sub = [r for r in rows if r[2] == cls]
        print(f"  {cls:9s} {len(sub):3d} 处")
    print()
    if dead:
        print(f"★★ DEAD {len(dead)} 处（引用到永远不会持有的技能）：")
        for mid, sk, src_tag, why in dead:
            print(f"   ❌ {mid:22s} {sk:26s} [{src_tag}] {why}")
    else:
        print("✅ 无 DEAD：AI/连招链引用的技能要么开战即持有、要么转阶段追加")
    return 0 if not dead else 1


if __name__ == "__main__":
    sys.exit(main())
