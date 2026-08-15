# -*- coding: utf-8 -*-
"""真实引擎 Boss 轮数模拟（只读：仅内存战斗，库指向 test_game_data.db）。
对照 numeric_calibration.py 的简化模型，给"boss 数值是否还高"一个真实引擎答案。"""
import sys, os
PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PLUGIN_DIR)
os.environ["GWEN_GAME_DB"] = os.path.join(PLUGIN_DIR, "test_game_data.db")

from game import battle as BT
from game.core import stats as ST
from game.data import EQUIP_SLOT_BASE, QUALITY

def make_player(lv, quality="blue", enhance=0):
    gear = {}
    for slot in EQUIP_SLOT_BASE:
        s = ST.equip_stats(slot, lv, quality)
        if enhance > 0:
            mult = {1: 1.05, 2: 1.10, 3: 1.15, 4: 1.20, 5: 1.26, 6: 1.32, 7: 1.38, 8: 1.45, 9: 1.52}.get(enhance, 1.0)
            s = {k: int(v * mult) for k, v in s.items()}
        gear[slot] = {"stats": s, "enhance": enhance}
    return {"class_name": "cls_zhan_shi", "level": lv, "hp": 500 + lv * 40, "max_hp": 500 + lv * 40,
            "mp": 500, "max_mp": 500, "equipment": gear, "skills": [], "skill_levels": {},
            "learned_skills": [], "attributes": None, "race": "human"}

def rounds_to_kill(lv, quality="blue", enhance=0, skill_rot=False):
    enemy = ST.monster_stats(lv, "boss")
    enemy.update({"name": "校准Boss", "max_hp": enemy["hp"], "lv": lv, "role": "boss"})
    pl = make_player(lv, quality, enhance)
    b = BT.Battle("monster", enemy, player=pl)
    rounds = 0
    while b.result is None and rounds < 600:
        if skill_rot:
            b.player_turn("skill", "猛击", pl, enemy_act=False)
        else:
            b.player_turn("attack", None, pl, enemy_act=False)
        rounds += 1
        if rounds % 100 == 0 and b.result is None and enemy["hp"] < 0:
            break
    return rounds, enemy["hp"], b.result

print("=== 真实引擎轮数（战士 蓝装 自动攻击，对比校准工具简化模型）===")
print(f"{'lv':>3} {'BossHP':>8} | {'真实引擎(普攻)':>10} {'校准工具(蓝装)':>10} | {'真实/工具':>6}")
for lv in (15, 22, 35, 42, 52, 60, 70, 82, 90):
    hp = ST.monster_stats(lv, "boss")["hp"]
    r, eh, res = rounds_to_kill(lv)
    # 校准工具没有逐 lv 输出，只有副本表；这里取近似：真实轮数直接展示
    print(f"{lv:>3} {hp:>8,} | {r:>10} | {'(见副本表)':>10} | {r:>6}")
print()
print("=== 蓝+9 与技能轮换（猛击）对比（lv35/60/90）===")
for lv in (35, 60, 90):
    r0, _, _ = rounds_to_kill(lv)
    r9, _, _ = rounds_to_kill(lv, quality="blue", enhance=9)
    rs, _, _ = rounds_to_kill(lv, skill_rot=True)
    print(f"lv{lv}: 普攻={r0}轮  蓝+9普攻={r9}轮  普攻+猛击轮换={rs}轮")
