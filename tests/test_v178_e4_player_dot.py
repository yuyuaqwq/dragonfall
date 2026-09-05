# -*- coding: utf-8 -*-
"""v178 E4 验证：玩家侧 dot 通道（敌方给玩家挂毒/灼烧/流血/腐蚀）"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import conftest  # noqa: F401
except Exception:
    pass

from game import battle as BT
from game.data.monsters import MONSTER_SKILLS

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
            "learned_skills": [], "resources": {}, "buffs": {}, "def": 50, "mdef": 50, "spd": 10}

def mk_mon(atk=200, matk=180):
    return {"name": "测试Boss", "hp": 8000, "max_hp": 8000, "def": 60, "mdef": 60,
            "atk": atk, "matk": matk, "spd": 10, "lv": 40, "id": "m_test",
            "buffs": {}, "resources": {}, "stacks": {}, "charging": None,
            "skills": ["ms_ai_hao"]}

print("== E4 玩家侧 dot 验证 ==")

# 1. _apply_player_dot 挂灼烧
player = mk_player()
mon = mk_mon()
b = BT.Battle("monster", mon)
b.player = player
logs = []
b._apply_player_dot(player, mon, {"type": "burn", "n": 2, "mult": 1.0}, logs)
check("挂灼烧成功", (player.get("debuffs") or {}).get("burn", {}).get("n") == 2,
      str(player.get("debuffs")))
check("挂灼烧有日志", any("灼烧" in l for l in logs), str(logs))

# 2. 层数叠加
logs2 = []
b._apply_player_dot(player, mon, {"type": "burn", "n": 1}, logs2)
check("同型 dot 层数累加 n=3", (player.get("debuffs") or {}).get("burn", {}).get("n") == 3,
      str(player.get("debuffs")))

# 3. 非法类型拒绝
logs3 = []
b._apply_player_dot(player, mon, {"type": "lava", "n": 1}, logs3)
check("非法类型不挂", "lava" not in (player.get("debuffs") or {}), str(player.get("debuffs")))

# 4. _tick_player_dots 结算扣血
player2 = mk_player()
mon2 = mk_mon(atk=100, matk=0)
b2 = BT.Battle("monster", mon2)
b2.player = player2
logs4 = []
b2._apply_player_dot(player2, mon2, {"type": "poison", "n": 1, "mult": 1.0}, logs4)
hp_before = player2["hp"]
b2._tick_player_dots(player2, logs4)
# poison = atk×0.8 = 80 → 但走 _damage_actor 减伤链可能略低
check("毒发作扣血", player2["hp"] < hp_before, f"hp {hp_before}→{player2['hp']}")
check("毒发作有日志", any("中毒" in l for l in logs4), str(logs4))

# 5. dot 结算后层数归零消散
deb = player2.get("debuffs") or {}
check("毒结算后消散", "poison" not in deb, str(deb))

# 6. 多类型并行（灼烧+流血）
player3 = mk_player()
mon3 = mk_mon(atk=100, matk=200)
b3 = BT.Battle("monster", mon3)
b3.player = player3
logs6 = []
b3._apply_player_dot(player3, mon3, {"type": "burn", "n": 2}, logs6)
b3._apply_player_dot(player3, mon3, {"type": "bleed", "n": 1}, logs6)
deb3 = player3.get("debuffs") or {}
check("双 dot 并行", "burn" in deb3 and "bleed" in deb3, str(deb3))
hp_before3 = player3["hp"]
b3._tick_player_dots(player3, logs6)
check("双 dot 同时发作扣血", player3["hp"] < hp_before3, f"{hp_before3}→{player3['hp']}")

# 7. 无 debuffs → 零操作不崩
player4 = mk_player()
b4 = BT.Battle("monster", mk_mon())
b4.player = player4
logs7 = []
b4._tick_player_dots(player4, logs7)
check("无 dot 不崩", player4["hp"] == 9999)

# 8. 序列化兼容（副本玩家快照持久化：debuffs 在 player dict 上随快照保存）
check("容器在 player dict 上（可持久化）", isinstance(player.get("debuffs"), dict))

# 9. 完整链路：MONSTER_SKILLS 配 pdot 的技能经 _enemy_cast_done 命中给玩家挂毒
from game.data.monsters import MONSTER_SKILLS
player5 = mk_player()
mon5 = mk_mon(atk=200, matk=0)
b5 = BT.Battle("monster", mon5)
b5.player = player5
MONSTER_SKILLS["ms_test_poison"] = {"kind": "魔法", "power": 1.0,
                                    "pdot": {"type": "poison", "n": 2},
                                    "desc": "测试毒", "name": "毒雾测试"}
try:
    logs9, dmg9 = b5._enemy_cast_done(player5, mon5, {"kind": "skill", "skill": "ms_test_poison"})
    deb9 = player5.get("debuffs") or {}
    check("技能配 pdot 完整链路生效", deb9.get("poison", {}).get("n") == 2, str(deb9))
    check("强度快照=敌方 atk", deb9.get("poison", {}).get("atk") == 200, str(deb9))
    check("命中日志含中毒", any("中毒" in l for l in logs9), str(logs9[:2]))
finally:
    MONSTER_SKILLS.pop("ms_test_poison", None)

# 10. 净化清玩家 dot
from game.core.battle_mech import _sb_cleanse_p
player6 = mk_player()
mon6 = mk_mon(atk=100)
b6 = BT.Battle("monster", mon6)
b6.player = player6
b6._apply_player_dot(player6, mon6, {"type": "burn", "n": 2}, [])
b6._apply_player_dot(player6, mon6, {"type": "bleed", "n": 1}, [])
check("净化前有 2 dot", len((player6.get("debuffs") or {})) == 2, str(player6.get("debuffs")))
logs10 = []
_saved_ctx = b6._cast_ctx
b6._cast_ctx = None  # 净化目标 = player
_sb_cleanse_p(b6, player6, logs10, scope="all")
b6._cast_ctx = _saved_ctx
check("净化 all 清空玩家 dot", not (player6.get("debuffs") or {}), str(player6.get("debuffs")))
check("净化日志", any("净化" in l for l in logs10), str(logs10))

# 11. 净化 single 只清一个
player7 = mk_player()
b7 = BT.Battle("monster", mk_mon(atk=100))
b7.player = player7
b7._apply_player_dot(player7, mk_mon(atk=100), {"type": "burn", "n": 2}, [])
b7._apply_player_dot(player7, mk_mon(atk=100), {"type": "bleed", "n": 1}, [])
logs11 = []
_saved_ctx7 = b7._cast_ctx
b7._cast_ctx = None
_sb_cleanse_p(b7, player7, logs11, scope="single")
b7._cast_ctx = _saved_ctx7
check("净化 single 剩 1 dot", len((player7.get("debuffs") or {})) == 1, str(player7.get("debuffs")))

print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
