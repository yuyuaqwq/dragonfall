# -*- coding: utf-8 -*-
"""#252 盾击眩晕复现脚本 v2：精确复现三个真实吞眩晕路径"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
QQBOT = r"C:\Users\yuyu\qqbot"
PLUGIN = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall"
os.environ["GWEN_GAME_DB"] = os.path.join(PLUGIN, "test_game_data.db")
sys.path.insert(0, QQBOT)
sys.path.insert(0, PLUGIN)
from data.plugins.dragonfall.game import battle as BT
from data.plugins.dragonfall.game import content as C

def mk(cls="战士", lv=22, spd=30):
    return {'class_name': C.resolve("classes", cls), 'level': lv, 'hp': 2000, 'max_hp': 2000,
            'mp': 500, 'max_mp': 500, 'atk': 150, 'def': 50, 'matk': 60, 'mdef': 30,
            'spd': spd, 'crit': 0.05, 'dodge': 0.03, 'equipment': {},
            'learned_skills': ["盾击"], 'skill_levels': {}}

def mkmon(name="洞穴蝙蝠", hp=3000, spd=1):
    return {'name': name, 'hp': hp, 'max_hp': hp, 'atk': 17, 'def': 10, 'matk': 0, 'mdef': 10,
            'spd': spd, 'lv': 18, 'role': 'dps', 'skills': []}

# 强制 _m_stun 必触发
import data.plugins.dragonfall.game.core.battle_mech as BM
BM.random.random = lambda: 0.0

print("=== 路径1：副本路径（enemy_act=False，玩家无额外行动→_enemy_phase→_end_round 吞 stun）===")
p = mk(spd=5)  # 低速度确保无额外行动
b = BT.Battle("monster", mkmon(spd=1), player=p)
logs, _ = b.player_turn("skill", "盾击", p, enemy_act=False)
print(f"  player_turn 后 e_buffs={b.e_buffs}（stun 已触发但可能被吞）")
mlogs, dmg = b._enemy_turn(p)  # 副本 Boss 回合
logs += mlogs
skipped = any("无法行动" in x for x in logs)
print(f"  Boss 回合被眩晕跳过: {'✅ 生效' if skipped else '❌ 未生效（stun 被 _end_round 吞掉）'}")
print(f"  日志尾部: {logs[-3:]}")

print("\n=== 路径2：玩家被敌方眩晕（敌方施放眩晕→_end_round 吞 p_buffs）===")
p = mk(spd=5)
b = BT.Battle("monster", mkmon(spd=1), player=p)
b.p_buffs["stun"] = 1  # 敌方刚施放眩晕
# 敌方回合结束（施放眩晕的当回合，_enemy_phase 末尾会 _end_round）
b._end_round()
print(f"  敌方回合结束后 p_buffs={b.p_buffs}（stun 还在吗？）")
logs, _ = b.player_turn("attack", None, p, enemy_act=True)
stunned = any("你被眩晕" in x for x in logs)
print(f"  玩家被眩晕拦截: {'✅ 生效' if stunned else '❌ 未生效（被 _end_round 吞掉）'}")
print(f"  日志尾部: {logs[-2:]}")

print("\n=== 路径3：敌方先手变体（先手一击已打→玩家盾击→敌方无额外行动→stun 被吞→下回合不跳）===")
p = mk(spd=5)
b = BT.Battle("monster", mkmon(spd=1), player=p)
b.e_first = True
b.e_extra_left = 0
# 敌方先手一击（无 stun，正常打）
mlogs, dmg = b._enemy_turn(p)
print(f"  先手一击 dmg={dmg}")
# 玩家施放盾击（stun 触发）
logs, _ = b.player_turn("skill", "盾击", p, enemy_act=True)
print(f"  玩家行动后 e_buffs={b.e_buffs}（stun 是否被吞）")
# 下一回合敌方行动
mlogs, dmg = b._enemy_turn(p)
logs += mlogs
skipped3 = any("无法行动" in x for x in logs)
print(f"  下回合敌方被眩晕跳过: {'✅ 生效' if skipped3 else '❌ 未生效（stun 被吞）'}")
print(f"  日志尾部: {logs[-3:]}")
