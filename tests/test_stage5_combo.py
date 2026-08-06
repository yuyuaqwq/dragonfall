# -*- coding: utf-8 -*-
"""阶段五：拳师连招序列验证（12 章 7.1：拳→踢→掌三连）"""
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

def mk(cls='武僧', lv=10, mp=500):
    return {'class_name': cls, 'level': lv, 'hp': 300, 'max_hp': 300, 'mp': mp, 'max_mp': mp,
            'atk': 30, 'def': 10, 'matk': 5, 'mdef': 5, 'spd': 10, 'crit': 0.0, 'dodge': 0.0,
            'equipment': {}, 'learned_skills': [], 'skill_levels': {}}

def mkmon(name='木桩', hp=99999):
    return {'name': name, 'hp': hp, 'max_hp': hp, 'atk': 5, 'def': 0, 'matk': 0, 'mdef': 0, 'spd': 1, 'lv': 1, 'role': 'dps', 'skills': []}

print("【连招：基础推进】")
b = BT.Battle('monster', mkmon(), player=mk())
check("初始空序列", b.combo_seq == [], str(b.combo_seq))
check("拳 → 未三连", b._combo_push("拳") is False and b.combo_seq == ["拳"], str(b.combo_seq))
check("拳→踢", b._combo_push("踢") is False and b.combo_seq == ["拳", "踢"], str(b.combo_seq))
check("拳→踢→掌 三连触发", b._combo_push("掌") is True, str(b.combo_seq))
check("三连后清空", b.combo_seq == [], str(b.combo_seq))

print("【连招：顺序错乱重置】")
b2 = BT.Battle('monster', mkmon(), player=mk())
b2._combo_push("拳")
check("拳→拳 重置为拳", b2._combo_push("拳") is False and b2.combo_seq == ["拳"], str(b2.combo_seq))
b2._combo_push("掌")
check("拳→掌 顺序错清空", b2.combo_seq == [], str(b2.combo_seq))
b2._combo_push("踢")
check("踢起手不进序列", b2.combo_seq == [], str(b2.combo_seq))
b2._combo_push("拳")
b2._combo_push("踢")
check("进度标签", b2._combo_label() == "拳→踢→_", b2._combo_label())

print("【连招：非连招技能不重置】")
b3 = BT.Battle('monster', mkmon(), player=mk())
b3._combo_push("拳")
b3._combo_push("踢")
b3._combo_push("")  # 非连招技能
check("非连招不清空", b3.combo_seq == ["拳", "踢"], str(b3.combo_seq))

print("【连招：序列化往返】")
b3._combo_push("掌")
st = b3.to_state()
b4 = BT.Battle.from_state(st)
check("combo_seq 序列化", b4.combo_seq == b3.combo_seq, str((b4.combo_seq, b3.combo_seq)))

print("【连招：战斗内三连触发】")
sk = C.PLAYER_SKILLS["cls_wu_seng"]["skills"]
test_skill = None
for k, info in sk.items():
    if info.get("kind") in ("物理", "魔法") and info.get("mp", 0) <= 100:
        test_skill = k
        break
assert test_skill, "找不到拳师测试技能"
name = sk[test_skill]["name"]
sk[test_skill]["combo"] = "拳"
p = mk()
p["learned_skills"] = [name]
b5 = BT.Battle("monster", mkmon(), player=p)
hp0 = b5.enemy["hp"]
logs, _ = b5.player_turn("skill", name, p, enemy_act=False)
check("拳施放记录连招", b5.combo_seq == ["拳"], str(b5.combo_seq))
check("连招进度日志", any("连招" in x for x in logs), str(logs)[:200])

# 直接手动推进到三连（模拟踢+掌）
b5._combo_push("踢")
sk[test_skill]["combo"] = "掌"
hp1 = b5.enemy["hp"]
logs2, _ = b5.player_turn("skill", name, p, enemy_act=False)
check("三连触发日志", any("三连" in x for x in logs2), str(logs2)[:200])
check("三连追加伤害", b5.enemy["hp"] < hp1, f"{b5.enemy['hp']} vs {hp1}")
check("combo_ready 标记", b5.resources.get("combo_ready") == 1, str(b5.resources))

# 还原
sk[test_skill].pop("combo", None)

print(f"\n结果: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
