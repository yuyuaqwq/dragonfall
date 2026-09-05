# -*- coding: utf-8 -*-
"""v178.1 dot 事件驱动重构验证（actor 侧）：同一 _apply_dot/_tick_actor_dots 服务玩家与怪，
事件驱动下 _process_until 推进自动结算；旧兼容壳已删除（_tick_dots_of/_apply_player_dot/
_tick_player_dots 不存在）。"""
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

print("== v178.1 actor 对称 + 无兼容壳验证 ==")

# 1. 挂 dot：玩家/怪同一入口，排事件
player = mk_player()
mon = mk_mon(atk=300, matk=0)
b = BT.Battle("monster", mon)
b.player = player
b._apply_dot(player, mon, {"type": "poison", "n": 1}, [])
b._apply_dot(player, mon, {"type": "burn", "n": 1}, [])
b._apply_dot(mon, player, {"type": "bleed", "n": 1}, [])
check("玩家挂 2 毒", len((player.get("debuffs") or {})) == 2, str(player.get("debuffs")))
check("怪挂 1 毒", len((mon.get("debuffs") or {})) == 1, str(mon.get("debuffs")))
n_ev_p = sum(1 for _, _, e in b._events if e.get("type") == "dot_tick" and e.get("side") == "p")
n_ev_e = sum(1 for _, _, e in b._events if e.get("type") == "dot_tick" and e.get("side") == "e")
check("双方各排 1 个自己的 dot_tick(per-actor)", n_ev_p == 1 and n_ev_e == 1, f"p={n_ev_p} e={n_ev_e}")

# 2. 结算：同一结算器对玩家/怪都工作
# 先给玩家结算（burn 发作扣血）
player2 = mk_player()
mon2 = mk_mon(atk=100, matk=100)
b2 = BT.Battle("monster", mon2)
b2.player = player2
b2._apply_dot(player2, mon2, {"type": "burn", "n": 1}, [])
hp_b2 = player2["hp"]
b2._tick_actor_dots(player2, [])
check("结算玩家 burn 扣血", player2["hp"] < hp_b2, f"{hp_b2}→{player2['hp']}")

# 怪侧
mon3 = mk_mon()
player3 = mk_player()
player3["atk"] = 200
b3 = BT.Battle("monster", mon3)
b3.player = player3
b3._apply_dot(mon3, player3, {"type": "bleed", "n": 1}, [])
hp_m3 = mon3["hp"]
b3._tick_actor_dots(mon3, [])
check("结算怪 bleed 扣血", mon3["hp"] < hp_m3, f"{hp_m3}→{mon3['hp']}")

# 3. 事件驱动推进 → 双方 dot 自动结算（_process_until 触发 dot_tick）
player4 = mk_player()
mon4 = mk_mon(atk=150, matk=100)
mon4["hp"] = 8000
b4 = BT.Battle("monster", mon4)
b4.player = player4
player4["atk"] = 200
b4._apply_dot(player4, mon4, {"type": "poison", "n": 2}, [])   # 怪毒玩家
b4._apply_dot(mon4, player4, {"type": "burn", "n": 2}, [])     # 玩家毒怪
# 推进到两个事件都触发
for _ in range(6):
    _evs = [e for _, _, e in b4._events if e.get("type") == "dot_tick"]
    if not _evs:
        break
    b4._process_until(b4._now + 1.1, [], player4)
# 至少发生了一次双方结算（hp 都降了）
check("事件推进后玩家被毒扣血", player4["hp"] < 9999, f"玩家hp={player4['hp']}")
check("事件推进后怪被毒扣血", mon4["hp"] < 8000, f"怪hp={mon4['hp']}")

# 4. 旧壳确认已删除（重构不留兼容）
check("旧 _tick_dots_of 已删", not hasattr(BT.Battle, "_tick_dots_of"))
check("旧 _apply_player_dot 已删", not hasattr(BT.Battle, "_apply_player_dot"))
check("旧 _tick_player_dots 已删", not hasattr(BT.Battle, "_tick_player_dots"))

print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
