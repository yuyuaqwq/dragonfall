# -*- coding: utf-8 -*-
"""阶段五：技能冷却 CD 体系验证（12 章 1.4）"""
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

def mk(cls, lv=10, mp=500):
    return {'class_name': cls, 'level': lv, 'hp': 200, 'max_hp': 200, 'mp': mp, 'max_mp': mp,
            'atk': 30, 'def': 10, 'matk': 25, 'mdef': 5, 'spd': 10, 'crit': 0.05, 'dodge': 0.03,
            'equipment': {}, 'learned_skills': [], 'skill_levels': {}}

def mkmon(name='野猪'):
    return {'name': name, 'hp': 9999, 'max_hp': 9999, 'atk': 5, 'def': 0, 'matk': 0, 'mdef': 0, 'spd': 1, 'lv': 1, 'role': 'dps', 'skills': []}

print("【冷却：基础方法】")
b = BT.Battle('monster', mkmon(), player=mk('法师'))
check("初始无冷却", not b._skill_on_cd("火球术"), str(b.cooldown))
b._set_skill_cd("火球术", 3)
check("设置后冷却中", b._skill_on_cd("火球术"), str(b.cooldown))
check("剩余 3 回合", b._skill_cd_left("火球术") == 3, str(b.cooldown))
b._tick_cooldowns()
check("递减到 2", b._skill_cd_left("火球术") == 2, str(b.cooldown))
b._tick_cooldowns()
b._tick_cooldowns()
check("归零清除", not b._skill_on_cd("火球术") and "火球术" not in b.cooldown, str(b.cooldown))

print("【冷却：序列化往返】")
b._set_skill_cd("冰锥", 2)
st = b.to_state()
b2 = BT.Battle.from_state(st)
check("cooldown 序列化", b2.cooldown == b.cooldown, str((b2.cooldown, b.cooldown)))

print("【冷却：施放拦截】")
# 给技能表临时挂一个带 cd 的技能（直接改 content 表，测完还原）
import copy
sk_table = C.PLAYER_SKILLS["cls_fa_shi"]["skills"]
saved = copy.deepcopy(sk_table)
# 找一个攻击技能测试
target_key = None
target_info = None
for k, info in sk_table.items():
    if info.get("kind") in ("魔法", "物理") and info.get("mp", 0) <= 100:
        target_key = k
        target_info = info
        break
assert target_key, "找不到测试技能"
target_name = target_info.get("name", target_key)
# 临时加 cd=3
sk_table[target_key]["cd"] = 3

p = mk('法师')
p["learned_skills"] = [target_name]
b3 = BT.Battle('monster', mkmon(), player=p)
# 第一次施放成功
logs, done = b3.player_turn('skill', target_name, p, enemy_act=False)
check("首次施放成功", any("冷却" not in x and "造成" in x for x in logs), str(logs)[:150])
check("施放后进入冷却", b3._skill_on_cd(target_name), str(b3.cooldown))
# 立即再施放被拦
logs2, done2 = b3.player_turn('skill', target_name, p, enemy_act=False)
check("CD 中拦截", any("冷却" in x for x in logs2), str(logs2)[:150])
# 过 3 回合后再施放成功
b3._tick_cooldowns()
b3._tick_cooldowns()
b3._tick_cooldowns()
logs3, done3 = b3.player_turn('skill', target_name, p, enemy_act=False)
check("CD 结束后可再放", any("造成" in x for x in logs3), str(logs3)[:150])

# 还原技能表
sk_table[target_key].pop("cd", None)

print("【冷却：无 cd 技能不拦截】")
# 旧技能没有 cd 字段，不拦截
b4 = BT.Battle('monster', mkmon(), player=mk('战士'))
p2 = mk('战士')
p2["learned_skills"] = ["猛击"] if "猛击" in [v.get("name") for v in C.PLAYER_SKILLS["cls_zhan_shi"]["skills"].values()] else []
# 随便用一个旧技能（无 cd）
old_skill = None
for k, info in C.PLAYER_SKILLS["cls_zhan_shi"]["skills"].items():
    if info.get("kind") in ("物理", "魔法") and info.get("mp", 0) <= 100:
        old_skill = info.get("name", k)
        break
if old_skill:
    p2["learned_skills"] = [old_skill]
    logs4, done4 = b4.player_turn('skill', old_skill, p2, enemy_act=False)
    check("无 cd 技能不设冷却", not b4._skill_on_cd(old_skill), str(b4.cooldown))

print(f"\n结果: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
