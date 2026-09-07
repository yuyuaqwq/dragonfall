# -*- coding: utf-8 -*-
"""阶段五：元素反应系统验证（12 章 3.1：蒸发/超载/冻结/感电）"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, FakeEvent, run
from data.plugins.dragonfall.game import battle as BT

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

def mk(cls='法师', lv=10, mp=500):
    return {'class_name': cls, 'level': lv, 'hp': 300, 'max_hp': 300, 'mp': mp, 'max_mp': mp,
            'atk': 30, 'def': 10, 'matk': 30, 'mdef': 5, 'spd': 10, 'crit': 0.0, 'dodge': 0.0,
            'equipment': {}, 'learned_skills': [], 'skill_levels': {}}

def mkmon(name='史莱姆', hp=9999):
    return {'name': name, 'hp': hp, 'max_hp': hp, 'atk': 5, 'def': 0, 'matk': 0, 'mdef': 0, 'spd': 1, 'lv': 1, 'role': 'dps', 'skills': []}

print("【元素反应：纯函数判定】")
r = E.element_reaction("ice", {"fire_mark": 1})
check("冰系+火印=蒸发", r and r["name"] == "蒸发" and r["mult"] == 1.30, str(r))
r = E.element_reaction("fire", {"thunder_mark": 2})
check("火系+雷印=超载", r and r["name"] == "超载" and r["extra"] == "aoe", str(r))
r = E.element_reaction("water", {"ice_mark": 1})
check("水系+冰印=冻结", r and r["name"] == "冻结" and r["extra"] == "freeze", str(r))
r = E.element_reaction("thunder", {"thunder_mark": 3})
check("雷系+雷印=感电", r and r["name"] == "感电" and not r["clear"], str(r))
r = E.element_reaction("fire", {"fire_mark": 1})
check("火系+火印无反应", r is None, str(r))
r = E.element_reaction("ice", {})
check("无印记无反应", r is None, str(r))

print("【元素反应：印记挂载】")
marks = {}
E.element_mark_apply(marks, "fire", 1)
check("挂火印", marks.get("fire_mark") == 1, str(marks))
E.element_mark_apply(marks, "fire", 2, max_layers=3)
check("火印叠加", marks.get("fire_mark") == 3, str(marks))
E.element_mark_apply(marks, "fire", 5, max_layers=3)
check("火印上限 3", marks.get("fire_mark") == 3, str(marks))

print("【元素反应：战斗内蒸发增伤】")
# 临时给法师技能表加 element 字段
sk = C.PLAYER_SKILLS["cls_fa_shi"]["skills"]
test_skill = None
for k, info in sk.items():
    if info.get("kind") == "魔法" and info.get("mp", 0) <= 100:
        test_skill = k
        break
assert test_skill
name = sk[test_skill]["name"]
sk[test_skill]["element"] = "ice"  # 冰系
p = mk()
p["learned_skills"] = [name]
mon = mkmon(hp=99999)
b = BT.Battle("monster", mon, player=p)
# 先挂火印（敌方 e_buffs）
b._tgt_buffs()["fire_mark"] = 1
# 施放冰系技能 → 应触发蒸发（增伤 30%）
hp_before = mon["hp"]
logs, done = b.actor_turn("skill", name, p, enemy_act=False)
# v154 读条命中制：出招读条结束（cast_done）才结算命中——推进后生效
b._process_until(float(getattr(b, "p_ct", 0) or 0) + 0.001, logs, p)
dmg = hp_before - mon["hp"]
check("蒸发反应日志", any("蒸发" in x for x in logs), str(logs)[:200])
# 计算蒸发伤害 vs 无反应伤害（同参数独立战斗，固定随机种子避免暴击干扰）
# v180-B ①：战斗状态在 player dict——对比战斗需各自用全新 player（复用 p 会把 CD/状态泄漏进下一场）
random.seed(42)
p2 = mk()
p2["learned_skills"] = [name]
b2 = BT.Battle("monster", mkmon(hp=99999), player=p2)
hp0 = b2.enemy["hp"]
b2.actor_turn("skill", name, p2, enemy_act=False)
b2._process_until(float(getattr(b2, "p_ct", 0) or 0) + 0.001, [], p2)
dmg0 = hp0 - b2.enemy["hp"]
random.seed(42)
p_ev = mk()
p_ev["learned_skills"] = [name]
b_ev = BT.Battle("monster", mkmon(hp=99999), player=p_ev)
b_ev._tgt_buffs()["fire_mark"] = 1
hp_ev = b_ev.enemy["hp"]
b_ev.actor_turn("skill", name, p_ev, enemy_act=False)
b_ev._process_until(float(getattr(b_ev, "p_ct", 0) or 0) + 0.001, [], p_ev)
dmg_ev = hp_ev - b_ev.enemy["hp"]
check("蒸发增伤 30%", abs(dmg_ev / dmg0 - 1.3) < 0.08, f"蒸发={dmg_ev} 无={dmg0} 比={dmg_ev/dmg0:.3f}")
check("蒸发清除火印", "fire_mark" not in b._tgt_buffs(), str(b._tgt_buffs()))

print("【元素反应：战斗内超载】")
sk[test_skill]["element"] = "fire"  # 火系（超载=雷印+火）
p3p = mk()
p3p["learned_skills"] = [name]
b3 = BT.Battle("monster", mkmon(hp=99999), player=p3p)
b3._tgt_buffs()["thunder_mark"] = 1
hp_before3 = b3.enemy["hp"]
logs3, done3 = b3.actor_turn("skill", name, p3p, enemy_act=False)
b3._process_until(float(getattr(b3, "p_ct", 0) or 0) + 0.001, logs3, p3p)
check("超载日志", any("超载" in x for x in logs3), str(logs3)[:200])
check("超载清除雷印", "thunder_mark" not in b3._tgt_buffs(), str(b3._tgt_buffs()))

print("【元素反应：印记保留（感电）】")
p4p = mk()
p4p["learned_skills"] = [name]
b4 = BT.Battle("monster", mkmon(hp=99999), player=p4p)
b4._tgt_buffs()["thunder_mark"] = 2
sk[test_skill]["element"] = "thunder"  # 雷系
logs4, done4 = b4.actor_turn("skill", name, p4p, enemy_act=False)
b4._process_until(float(getattr(b4, "p_ct", 0) or 0) + 0.001, logs4, p4p)
check("感电日志", any("感电" in x for x in logs4), str(logs4)[:200])
check("感电连击 +1", any("连击 2" in x for x in logs4), str(logs4)[:200])
# 感电保留旧印记(2)，施放又挂 1 层 → 3；印记为层数标记不受 _end_round 回合递减
# （v121 CTB：旧 v61 靠速度优势回合推迟 _end_round 掩盖了印记误递减，CTB 下印记
#  已豁免回合递减——生命周期 = 触发反应清除或战斗结束）
check("感电保留雷印", b4._tgt_buffs().get("thunder_mark") == 3, str(b4._tgt_buffs()))

print("【元素反应：法师切换当前系】")
b5 = BT.Battle("monster", mkmon(), player=mk())
check("默认火系", b5._p_res().get("element") == "fire", str(b5._p_res()))
sk[test_skill]["element"] = "thunder"
b5._tgt_buffs().pop("thunder_mark", None)
p5 = mk()
p5["learned_skills"] = [name]
b5.actor_turn("skill", name, p5, enemy_act=False)
b5._process_until(float(getattr(b5, "p_ct", 0) or 0) + 0.001, [], p5)
check("施放后切雷系", b5._p_res().get("element") == "thunder", str(b5._p_res()))

# 还原
sk[test_skill].pop("element", None)

print(f"\n结果: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
