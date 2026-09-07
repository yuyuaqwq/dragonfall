# -*- coding: utf-8 -*-
"""决定性验证：35 级真实玩家（蓝+0全乘区）vs 老王之墓 Boss —— 真实引擎击杀回合。
对照：numeric_lib solo_low=48.5 轮 vs _tmp_calib_v2=97 轮，用引擎裁决。
"""
import os, sys
_PD = os.getcwd()  # dragonfall/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(_PD))))  # qqbot/
sys.path.insert(0, os.path.join(_PD, "tests"))
sys.path.insert(0, _PD)
sys.path.insert(0, os.path.join(_PD, "scripts"))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PD, "tests", "test_game_data.db"))

import random
from data.plugins.dragonfall.game import content as C
from data.plugins.dragonfall.game import engine as E
from data.plugins.dragonfall.game import battle as BT
from numeric_lib.gear import gear_loadout
from numeric_lib.constants import cls_id

NO_REAL_ATTR = {"str": 9 + 3 * 34}   # 35级 111 点全力

inst = C.INSTANCES["inst_old_king_tomb"]
boss_def = inst.get("boss") or (inst.get("stages") or [])[-1].get("boss")
m = C.build_monster(boss_def, {"id": "inst_old_king_tomb", "name": "x", "area": "instance"})
hpm = inst.get("hp_mult", 1.0); mn = inst.get("min_players", 1)
boss_hp = int(m.get("max_hp", 0) * hpm)
print(f"老王 Boss: {m.get('name')} Lv{m.get('lv')} HP模板{m.get('max_hp')} ×hp_mult{hpm} = {boss_hp}")
gear = gear_loadout(35, "solo_low")

for use_skill in (False, True):
    wins = 0; rounds_sum = 0
    for seed in range(6):
        random.seed(seed)
        st = E.player_final_stats("战士", 35, gear, 1, NO_REAL_ATTR, 1)
        player = {
            "class_name": "战士", "level": 35, "class_tier": 1, "evolve_path": 1,
            "equipment": dict(gear), "attributes": dict(NO_REAL_ATTR),
            "learned_skills": ["破甲斩", "猛击"] if use_skill else [],
            "hp": st["max_hp"], "mp": st["max_mp"], "max_hp": st["max_hp"], "max_mp": st["max_mp"],
            "race": "human", "title_bonus": None,
        }
        b = BT.Battle(btype="instance", enemy=dict(m), player=player)
        turns = 0
        import copy
        skill_pool = ["破甲斩", "猛击"]
        while b.result is None and turns < 800:
            turns += 1
            prev = b.round
            if use_skill:
                sname = skill_pool[turns % 2]
                b.actor_turn("skill", sname, player)
                if b.round == prev and b.result is None:
                    b.actor_turn("attack", None, player)
            else:
                b.actor_turn("attack", None, player)
        if b.result == "victory":
            wins += 1
        rounds_sum += b.round
        if seed == 0:
            print(f"  [seed0] {b.result} round={b.round}")
    print(f"技能轴={use_skill}: 胜率 {wins}/6, 平均回合 {rounds_sum/6:.1f}")

print("\n对照: numeric_lib solo_low=48.5轮 | _tmp_calib_v2=97轮")