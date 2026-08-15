# -*- coding: utf-8 -*-
"""阶段五：核心资源系统验证脚本"""
import sys, os
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

def mk(cls, hp=100):
    return {'class_name': cls, 'level': 10, 'hp': hp, 'max_hp': 100, 'mp': 50, 'max_mp': 50,
            'atk': 20, 'def': 10, 'matk': 5, 'mdef': 5, 'spd': 10, 'crit': 0.05, 'dodge': 0.03,
            'equipment': {}, 'learned_skills': [], 'skill_levels': {}}

def mkmon(name='野猪'):
    return {'name': name, 'hp': 500, 'max_hp': 500, 'atk': 5, 'def': 0, 'matk': 0, 'mdef': 0, 'spd': 1, 'lv': 1, 'role': 'dps', 'skills': []}

print("【核心资源：初始化】")
p = mk('战士')
b = BT.Battle('monster', mkmon(), player=p)
check("战士怒气初始 0", b.resources.get('rage') == 0, str(b.resources))
pm = mk('法师')
bm = BT.Battle('monster', mkmon('史莱姆'), player=pm)
check("法师元素亲和默认火", bm.resources.get('element') == 'fire', str(bm.resources))
py = mk('游侠')
by = BT.Battle('monster', mkmon('狼'), player=py)
check("游侠精力初始满 100", by.resources.get('energy') == 100, str(by.resources))

print("【核心资源：获取】")
logs, done = b.player_turn('attack', None, p, enemy_act=False)
check("战士普攻 +1 怒气", b.resources.get('rage') == 1, str(b.resources))
b3 = BT.Battle('monster', mkmon(), player=mk('战士'))
# 屏蔽随机闪避，保证受击断言确定性（dodge≈0.03 否则 ~3% 概率闪避返回不 +怒气）
_orig_ps = b3._player_stats
def _ps_nododge(p_):
    s = _orig_ps(p_)
    s["dodge"] = 0.0
    return s
b3._player_stats = _ps_nododge
b3._damage_player(p, 10, [])
check("战士受击 +1 怒气", b3.resources.get('rage') == 1, str(b3.resources))
b4 = BT.Battle('monster', mkmon(), player=mk('战士'))
for _ in range(15):
    b4._resource_on_attack(p)
check("怒气上限 10", b4.resources.get('rage') == 10, str(b4.resources))

print("【核心资源：序列化往返】")
st = by.to_state()
b2 = BT.Battle.from_state(st)
check("resources 序列化往返", b2.resources == by.resources, str((b2.resources, by.resources)))

print("【核心资源：回合回复】")
logs = b2._turn_start(py)
check("精力已满不超上限", b2.resources.get('energy') == 100, str(b2.resources))
py2 = mk('游侠')
by2 = BT.Battle('monster', mkmon(), player=py2)
by2.resources['energy'] = 50
logs = by2._turn_start(py2)
check("精力每回合 +30", by2.resources.get('energy') == 80, str(by2.resources))
check("回复日志", any("精力回复" in x for x in logs), str(logs))

print("【核心资源：消耗】")
assert E.core_resource_spend('游侠', by2.resources, 20) is True
check("消耗 20 精力", by2.resources.get('energy') == 60, str(by2.resources))
assert E.core_resource_spend('游侠', by2.resources, 999) is False
check("不足不扣", by2.resources.get('energy') == 60, str(by2.resources))

print("【核心资源：显示标签】")
check("战士标签", "怒气" in b._resource_label(p), b._resource_label(p))
check("法师标签", "火系" in bm._resource_label(pm), bm._resource_label(pm))

print(f"\n结果: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
