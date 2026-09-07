# -*- coding: utf-8 -*-
"""验证：_tmp_calib_v2 的战士循环模型 vs 实机 Battle 引擎（每职业技能循环实测误差）"""
import sys, os, random, statistics

PLUGIN_DIR = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall"
QQBOT_DIR = r"C:\Users\yuyu\qqbot"
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
os.environ["GWEN_GAME_DB"] = os.path.join(PLUGIN_DIR, "test_game_data.db")

from data.plugins.dragonfall.game import content as C
from data.plugins.dragonfall.game import engine as E
from data.plugins.dragonfall.game import battle as BT
sys.path.insert(0, PLUGIN_DIR + r"\scripts")
from _tmp_calib_v2 import (make_gear, player_stats, rotation_dmg, basic_hit, crit_mult,
                           per_round_dmg, CLASSES, ROTATIONS, ENCHANT_CRIT)

LV = 60
gear = make_gear(LV, "blue", 0)

# 参照副本 boss（月神神殿 Lv60）
inst = C.INSTANCES["inst_moon_temple"]
boss_def = inst.get("boss") or (inst.get("stages") or [])[-1].get("boss")
boss_m = C.build_monster(boss_def, {"id": "inst_moon_temple", "name": "inst_moon_temple", "area": "instance"})
bdef, bmdef = boss_m.get("def", 0), boss_m.get("mdef", 0)

ROT_SEQ = {
    "cls_zhan_shi": ["破甲斩", "猛击"],
    "cls_you_xia": ["瞄准射击"],
    "cls_fa_shi": ["元素弹幕"],
    "cls_mu_shi": ["惩戒"],
    "cls_ci_ke": ["双刃乱舞"],
}

for name, cid, kind, _ in CLASSES:
    st = player_stats(cid, LV, gear, True, 0.0)
    model_rot = rotation_dmg(st, bdef, bmdef, cid)          # 模型：技能轴(无暴击期望)
    model_ev = model_rot * crit_mult(st)                     # +暴击期望
    seq = ROT_SEQ[cid]
    dmg_log = []
    for run in range(3):
        random.seed(run * 100 + 7)
        enemy = dict(boss_m)
        enemy["max_hp"] = enemy["hp"] = 10**9
        p = {
            "class_name": cid, "level": LV, "equipment": gear,
            "class_tier": 2, "attributes": {"str": 186} if kind == "phys" else {"int": 186},
            "evolve_path": 1, "race": None,
            "learned_skills": [k[0] for k in ROTATIONS[cid]],
            "hp": 10**6, "mp": 10**6, "max_hp": 10**6, "max_mp": 10**6,
            "name": name, "skill_levels": {},
        }
        b = BT.Battle("monster", enemy, {}, player=p, enemies=[enemy])
        n = 24
        total = 0
        logs, done = b.actor_turn("skill", seq[0], p, enemy_act=False)
        total += (10**9) - b.enemies[0]["hp"]
        for i in range(1, n):
            sk = seq[i % len(seq)]
            p["mp"] = p["max_mp"]  # 关闭蓝耗，验证纯伤害口径
            before = b.enemies[0]["hp"]
            logs, done = b.actor_turn("skill", sk, p, enemy_act=False)
            total += before - b.enemies[0]["hp"]
        dmg_log.append(total / n)
    emp = statistics.mean(dmg_log)
    print(f"{name:<4} 实测每轮 {emp:7.0f}   模型技能轴 {model_rot:7.0f}   模型含暴击 {model_ev:7.0f}   误差 {(emp-model_ev)/model_ev*100:+.1f}%")