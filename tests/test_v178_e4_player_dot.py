# -*- coding: utf-8 -*-
"""v178.1 dot 事件驱动重构验证：dot = actor 通用能力（玩家/怪同一 _apply_dot + _tick_actor_dots），
事件驱动：挂 dot 排 dot_tick，_process_until 推进时到点自动结算 + 重排，玩家/怪零身份分支。"""
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

def mk_mon(atk=200, matk=180):
    return {"name": "测试Boss", "hp": 8000, "max_hp": 8000, "def": 60, "mdef": 60,
            "atk": atk, "matk": matk, "spd": 10, "lv": 40, "id": "m_test",
            "buffs": {}, "resources": {}, "stacks": {}, "charging": None,
            "skills": ["ms_ai_hao"]}

print("== v178.1 dot 事件驱动重构验证 ==")

# 1. 同一个 _apply_dot 给玩家挂（怪打玩家）——挂 dot 排 dot_tick 事件
player = mk_player()
mon = mk_mon(atk=300, matk=0)
b = BT.Battle("monster", mon)
b.player = player
logs = []
b._apply_dot(player, mon, {"type": "poison", "n": 2}, logs)
deb_p = player.get("debuffs") or {}
check("通用 _apply_dot 给玩家挂毒", deb_p.get("poison", {}).get("n") == 2, str(deb_p))
check("强度快照=怪的 atk", deb_p.get("poison", {}).get("atk") == 300, str(deb_p.get("poison")))
check("日志说'你'", any("你中了" in l for l in logs), str(logs))
check("挂毒排了 dot_tick 事件", any(e.get("type") == "dot_tick" for _, _, e in b._events), str(b._events))

# 2. 同一个 _apply_dot 给怪挂（玩家毒技打怪——source=玩家）
player2 = mk_player()
mon2 = mk_mon()
b2 = BT.Battle("monster", mon2)
b2.player = player2
logs2 = []
b2._apply_dot(mon2, player2, {"type": "burn", "n": 1}, logs2)
deb_m = mon2.get("debuffs") or {}
check("通用 _apply_dot 给怪挂灼烧", deb_m.get("burn", {}).get("n") == 1, str(deb_m))
check("日志说怪物名", any("测试Boss" in l for l in logs2), str(logs2))

# 3. _tick_actor_dots 结算玩家（扣血走 _damage_actor）——同一结算器
player3 = mk_player()
mon3 = mk_mon(atk=100, matk=0)
b3 = BT.Battle("monster", mon3)
b3.player = player3
logs3 = []
b3._apply_dot(player3, mon3, {"type": "poison", "n": 1}, logs3)
hp_before = player3["hp"]
b3._tick_actor_dots(player3, logs3)
check("统一结算器结算玩家 dot 扣血", player3["hp"] < hp_before, f"{hp_before}→{player3['hp']}")

# 4. _tick_actor_dots 结算怪（同一入口结算怪身上的毒——玩家毒怪）
player4 = mk_player()
mon4 = mk_mon()
mon4["hp"] = 8000
b4 = BT.Battle("monster", mon4)
b4.player = player4
logs4 = []
player4["atk"] = 200
b4._apply_dot(mon4, player4, {"type": "poison", "n": 1}, logs4)
hp_before4 = mon4["hp"]
b4._tick_actor_dots(mon4, logs4)
check("统一结算器结算怪 dot 扣血", mon4["hp"] < hp_before4, f"{hp_before4}→{mon4['hp']}")

# 5. 无 debuffs 的 actor → 零操作不崩
player5 = mk_player()
b5 = BT.Battle("monster", mk_mon())
b5.player = player5
logs5 = []
b5._tick_actor_dots(player5, logs5)
check("空 actor 不崩", player5["hp"] == 9999)

# 6. 层数叠加（同型 dot 再挂 n 累加，不重复排事件）
player6 = mk_player()
mon6 = mk_mon(atk=100, matk=0)
b6 = BT.Battle("monster", mon6)
b6.player = player6
logs6 = []
b6._apply_dot(player6, mon6, {"type": "burn", "n": 2}, logs6)
b6._apply_dot(player6, mon6, {"type": "burn", "n": 1}, logs6)
check("同型 dot 层数累加 n=3", (player6.get("debuffs") or {}).get("burn", {}).get("n") == 3,
      str(player6.get("debuffs")))
n_ev6 = sum(1 for _, _, e in b6._events if e.get("type") == "dot_tick")
check("层数叠加不重复排事件(仍 1 个)", n_ev6 == 1, f"{n_ev6} 个 dot_tick")

# 7. 非法类型拒绝
logs7 = []
b6._apply_dot(player6, mon6, {"type": "lava", "n": 1}, logs7)
check("非法类型不挂", "lava" not in (player6.get("debuffs") or {}), str(player6.get("debuffs")))

# 8. 事件驱动：挂玩家毒 → _process_until 推进 → dot_tick 到点自动结算 + 重排
player8 = mk_player()
mon8 = mk_mon(atk=100, matk=0)
b8 = BT.Battle("monster", mon8)
b8.player = player8
logs8 = []
b8._apply_dot(player8, mon8, {"type": "poison", "n": 3}, logs8)
hp_before8 = player8["hp"]
# 推进 3 刻（每次 1 刻，触发 3 次 dot_tick：3 层毒 → 3 次结算 3 次重排，最后 0 层停止）
for _ in range(4):
    _evs = [e for _, _, e in b8._events if e.get("type") == "dot_tick"]
    if not _evs:
        break
    b8._process_until(b8._now + 1.1, logs8, player8)
check("事件驱动毒自动发作扣血", player8["hp"] < hp_before8, f"{hp_before8}→{player8['hp']}")
check("事件驱动后 dot 消散", not (player8.get("debuffs") or {}), str(player8.get("debuffs")))
n_ev8 = sum(1 for _, _, e in b8._events if e.get("type") == "dot_tick")
check("dot 清空后不再重排", n_ev8 == 0, f"{n_ev8} 个 dot_tick")

# 9. 事件驱动：玩家毒怪 → 结算扣怪血（同一事件机制，actor 无关）
player9 = mk_player()
mon9 = mk_mon()
mon9["hp"] = 8000
b9 = BT.Battle("monster", mon9)
b9.player = player9
logs9 = []
player9["atk"] = 200
b9._apply_dot(mon9, player9, {"type": "poison", "n": 2}, logs9)
hp_before9 = mon9["hp"]
for _ in range(3):
    _evs = [e for _, _, e in b9._events if e.get("type") == "dot_tick"]
    if not _evs:
        break
    b9._process_until(b9._now + 1.1, logs9, player9)
check("事件驱动怪毒发作扣血", mon9["hp"] < hp_before9, f"{hp_before9}→{mon9['hp']}")

# 10. 净化：清掉 dot 后 dot_tick 不再重排（净化 = 对任意 actor debuffs 操作）
player10 = mk_player()
mon10 = mk_mon(atk=100)
b10 = BT.Battle("monster", mon10)
b10.player = player10
b10._apply_dot(player10, mon10, {"type": "burn", "n": 2}, [])
b10._apply_dot(player10, mon10, {"type": "bleed", "n": 1}, [])
check("净化前有 2 dot", len((player10.get("debuffs") or {})) == 2, str(player10.get("debuffs")))
from game.core.battle_mech import _sb_cleanse_p
logs10 = []
_saved_ctx = b10._cast_ctx
b10._cast_ctx = None  # 净化目标 = player
_sb_cleanse_p(b10, player10, logs10, scope="all")
b10._cast_ctx = _saved_ctx
check("净化 all 清空玩家 dot", not (player10.get("debuffs") or {}), str(player10.get("debuffs")))
check("净化日志", any("净化" in l for l in logs10), str(logs10))
# 清空后事件不重排（手动推一格，若事件触发但无 debuffs → 不再排）
for _ in range(2):
    _evs = [e for _, _, e in b10._events if e.get("type") == "dot_tick"]
    if not _evs:
        break
    b10._process_until(b10._now + 1.1, logs10, player10)
n_ev10 = sum(1 for _, _, e in b10._events if e.get("type") == "dot_tick")
check("净化后 dot_tick 不再排", n_ev10 == 0, f"{n_ev10} 个 dot_tick")

# 11. 完整链路：MONSTER_SKILLS 配 pdot 的技能经 _enemy_cast_done 命中给玩家挂毒
from game.data.monsters import MONSTER_SKILLS
player11 = mk_player()
mon11 = mk_mon(atk=200, matk=0)
b11 = BT.Battle("monster", mon11)
b11.player = player11
MONSTER_SKILLS["ms_test_poison"] = {"kind": "魔法", "power": 1.0,
                                    "pdot": {"type": "poison", "n": 2},
                                    "desc": "测试毒", "name": "毒雾测试"}
try:
    logs11, dmg11 = b11._enemy_cast_done(player11, mon11, {"kind": "skill", "skill": "ms_test_poison"})
    deb11 = player11.get("debuffs") or {}
    check("技能配 pdot 完整链路生效", deb11.get("poison", {}).get("n") == 2, str(deb11))
    check("强度快照=敌方 atk", deb11.get("poison", {}).get("atk") == 200, str(deb11))
    check("命中日志含中毒", any("中毒" in l for l in logs11), str(logs11[:2]))
finally:
    MONSTER_SKILLS.pop("ms_test_poison", None)

print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
