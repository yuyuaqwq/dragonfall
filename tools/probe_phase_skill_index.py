# -*- coding: utf-8 -*-
"""探针：Boss 转阶段换招后，引擎是否自动重建 _skill_index（auto_act 能否解析）。

背景（2026-09-11）：boss_script._check_phases 把阶段 add_skills 幂等 append 进
actor["skills"]（L217-219），而引擎 _skill_index 原先只在 Battle 构造期 + add_actor
建一次 → 阶段新招不在索引。ActCtx.__post_init__ 只从 _skill_index 取 info，取不到
时 info={} → do_skill 直接 return []：**转阶段后 Boss 的 auto_act 主技能静默空放**。

修复：Battle.refresh_skill_index(actor) —— 引擎在每次行动决策前（human_act /
actor_auto 构造 ActCtx 之前）幂等补齐索引，索引一致性归引擎。

走真实路径：b.actor_auto(actor)（引擎内部 = script_hook 转阶段 → 刷新索引 → 出招）。

跑法：python tools/probe_phase_skill_index.py
"""
import os
import sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PLUGIN_DIR, "framework"))  # 引擎框架包（S8 物理分离：framework/ 为引擎 submodule）
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(PLUGIN_DIR, "test_probe_phase.db"))
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)

from saintess_engine import config as _b2c  # noqa: E402
from game.content_rules.apply import ensure_engine_configured as _eng_cfg; _eng_cfg()
from saintess_engine import Battle as B2, ActCtx  # noqa: E402
from saintess_engine.battle.ai import _skill_castable  # noqa: E402
from game.core.drops import build_monster  # noqa: E402
from game.services.battle2_bridge import monster_to_actor  # noqa: E402
from game.data.maps import MAP_BY_ID  # noqa: E402
from game.data.monster_mods import MONSTER_MODS  # noqa: E402
from game.commands.boss_script import make_script_hook  # noqa: E402

MID = "b_gray_lord"
mod = MONSTER_MODS.get(MID) or {}
BASE_SKILLS = ["ms_zhan_chui_lord", "ms_zhao_huan_gong_cheng_shou"]  # 与 instances/subareas boss 元组一致
DEF = (MID, mod.get("name", MID), "boss", 45, list(BASE_SKILLS), [])
MAP_OBJ = next(iter(MAP_BY_ID.values()))

mon = build_monster(DEF, MAP_OBJ)
mon["mech"] = mod.get("mech")
mon["phases"] = mod.get("phases")
mon["ai"] = mod.get("ai")
mon["auto_act"] = None
actor = monster_to_actor(mon)
player = {"uid": "p1", "name": "木桩", "side": "player", "kind": "player",
          "hp": 999999, "max_hp": 999999, "atk": 10, "def": 0, "matk": 10, "mdef": 0,
          "spd": 1, "crit": 0, "ct": 0.0, "skills": []}
b = B2("probe", sides={"player": [player], "enemy": [actor]}, title_bonus={})
st = {"boss_script": None}
b.script_hook = make_script_hook(st)

print(f"构造后 _skill_index = {sorted((actor.get('_skill_index') or {}).keys())}")
print(f"声明 phases = {[(p.get('min'), p.get('add_skills')) for p in (mod.get('phases') or [])]}\n")

fails = []
for hp_ratio in (0.45, 0.25, 0.05):
    actor["hp"] = int(actor["max_hp"] * hp_ratio)
    for frame in (1, 2):
        idx_before = set((actor.get("_skill_index") or {}).keys())
        logs, ended = b.actor_auto(actor)
        idx_after = set((actor.get("_skill_index") or {}).keys())
        idx_after_map = actor.get("_skill_index") or {}
        gained = idx_after - idx_before
        fired = [s for s in (gained or [])
                 if any((s in lg) or ((idx_after_map.get(s) or {}).get("name", "\0") in lg) for lg in logs)]
        print(f"--- hp {hp_ratio:.0%} 帧{frame}：索引 +{sorted(gained) or '无'}"
              f" | 出招 {' / '.join(lg for lg in logs if lg.strip())[:110] or '(无)'}")
        if gained:
            print(f"      ★ 新招已进索引：{sorted(gained)} → 可解析"
                  f"（_skill_castable={ [_skill_castable(b, actor, s) for s in sorted(gained)] }）")

print(f"\n转阶段后 actor['skills']  = {actor.get('skills')}")
print(f"转阶段后 auto_act        = {actor.get('auto_act')}")
idx = actor.get("_skill_index") or {}
phase_skills = [s for s in (actor.get("skills") or []) if s not in BASE_SKILLS]
missing = [s for s in phase_skills if s not in idx]
print(f"阶段新招 {len(phase_skills)} 个 = {phase_skills}")
print(f"其中仍不在索引 = {len(missing)} 个 = {missing}")
print()
if missing:
    print("★★ 结论：阶段新招未进索引 → 转阶段后主技能静默空放（修复未生效）")
    for s in missing:
        print(f"   ActCtx(skill_name={s!r}).info = {ActCtx(caster=actor, action='skill', skill_name=s).info!r}")
    sys.exit(1)
print("✅ 结论：阶段新招全部进索引 → auto_act 主技能可解析（引擎自愈索引生效）")
