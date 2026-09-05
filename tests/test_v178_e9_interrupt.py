# -*- coding: utf-8 -*-
"""v178 E9 验证：敌方蓄力打断奖励钩子（歌澜虚脱/赫尔加反噬/轰鸣断过载）"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import conftest  # noqa: F401
except Exception:
    pass

from game import battle as BT

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f"  ✅ {name}")
    else:
        FAIL += 1; print(f"  ❌ {name} {detail}")

def mk_player():
    return {"class_name": "cls_zhan_shi", "level": 40, "name": "测试", "hp": 9999, "max_hp": 9999,
            "mp": 500, "max_mp": 500, "attributes": {}, "equipment": {}, "class_tier": 0,
            "learned_skills": [], "resources": {}, "buffs": {}, "def": 50, "mdef": 50, "spd": 10,
            "level": 40}

def mk_boss(extra=None):
    m = {"name": "歌澜", "hp": 8000, "max_hp": 8000, "def": 60, "mdef": 60,
         "atk": 100, "matk": 150, "spd": 10, "lv": 50, "id": "b_test",
         "buffs": {}, "resources": {}, "stacks": {}, "charging": None, "is_boss": True,
         "skills": ["ms_ai_hao"], "mech": "phase",
         "charging": {"skill": "ms_ai_hao", "left": 2, "name": "谢幕曲"}}
    if extra:
        m.update(extra)
    return m

print("== E9 打断奖励钩子验证 ==")

# 1. vulnerable（歌澜破音虚脱：承伤×1.4 + 虚弱）
boss = mk_boss({"on_interrupt": {"effect": "vulnerable", "value": 1.4, "turns": 2}})
b = BT.Battle("instance", boss, enemies=[boss])
b.player = mk_player()
logs = []
b._interrupt_charging(boss, logs, "玩家")
check("蓄力被清空", boss.get("charging") is None)
check("承伤×1.4 写入", boss.get("_dmg_taken_mult") == 1.4, str(boss.get("_dmg_taken_mult")))
check("虚弱 atk_down", (boss.get("buffs") or {}).get("mon_atk_down") == 2, str(boss.get("buffs")))
check("有日志", any("破绽" in l for l in logs), str(logs))

# 2. stacks_set（轰鸣断过载：层回 3）
boss2 = mk_boss({"on_interrupt": {"effect": "stacks_set", "value": 3, "key": "charge"},
                 "stacks": {"charge": 5}, "mech_stacks_n": 5})
b2 = BT.Battle("instance", boss2, enemies=[boss2])
b2.player = mk_player()
logs2 = []
b2._interrupt_charging(boss2, logs2, "玩家")
check("层数回 3", (boss2.get("stacks") or {}).get("charge") == 3, str(boss2.get("stacks")))
check("mech_stacks_n 同步", boss2.get("mech_stacks_n") == 3, str(boss2.get("mech_stacks_n")))

# 3. freeze_self（咕噜号令打断僵直）
boss3 = mk_boss({"on_interrupt": {"effect": "freeze_self", "turns": 1}})
b3 = BT.Battle("instance", boss3, enemies=[boss3])
b3.player = mk_player()
logs3 = []
b3._interrupt_charging(boss3, logs3, "玩家")
check("自我冻结", (boss3.get("buffs") or {}).get("freeze") == 1, str(boss3.get("buffs")))

# 4. atk_down（打断惩罚）
boss4 = mk_boss({"on_interrupt": {"effect": "atk_down", "turns": 3}})
b4 = BT.Battle("instance", boss4, enemies=[boss4])
b4.player = mk_player()
logs4 = []
b4._interrupt_charging(boss4, logs4, "玩家")
check("atk_down 3刻", (boss4.get("buffs") or {}).get("mon_atk_down") == 3, str(boss4.get("buffs")))

# 5. 无 on_interrupt 配置 → 仅清蓄力（旧行为）
boss5 = mk_boss()
b5 = BT.Battle("instance", boss5, enemies=[boss5])
b5.player = mk_player()
logs5 = []
b5._interrupt_charging(boss5, logs5, "玩家")
check("无配置仅清蓄力", boss5.get("charging") is None and not boss5.get("_dmg_taken_mult"))

# 6. 玩家侧打断不触发 Boss 反噬（side=ally 走 MP 返还）
ally = {"name": "玩家", "side": "ally", "charging": {"skill": "x", "left": 1, "mp_spent": 10},
        "mp": 80, "max_mp": 100, "on_interrupt": {"effect": "vulnerable"}}
b6 = BT.Battle("monster", {"name": "怪", "hp": 10})
b6.player = mk_player()
logs6 = []
b6._interrupt_charging(ally, logs6, "怪")
check("玩家打断返还 MP", ally.get("mp") == 85, f"mp={ally.get('mp')}")
check("玩家不触发反噬", "破绽" not in " ".join(logs6), str(logs6))

# 7. _on_interrupt_effect 直接调用（无蓄力场景）
boss7 = mk_boss()
logs7 = []
ret = b._on_interrupt_effect(boss7, {"effect": "vulnerable", "value": 1.3, "turns": 1}, logs7)
check("直接调用 vulnerable", ret and boss7.get("_dmg_taken_mult") == 1.3)

print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
