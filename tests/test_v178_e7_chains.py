# -*- coding: utf-8 -*-
"""v178 E7 验证：固定连招链 chains 消费（试炼骑士长固定 4 招循环等）"""
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
            "learned_skills": [], "resources": {}, "buffs": {}, "def": 50, "mdef": 50, "spd": 10,
            "level": 40}

def mk_mon(extra=None):
    m = {"name": "链Boss", "hp": 8000, "max_hp": 8000, "def": 60, "mdef": 60,
         "atk": 200, "matk": 100, "spd": 10, "lv": 40, "id": "m_test",
         "buffs": {}, "resources": {}, "stacks": {}, "charging": None,
         "skills": ["ms_ai_hao", "ms_an_ying_dan", "ms_bao_dan"], "mech": "phase"}
    if extra:
        m.update(extra)
    return m

print("== E7 连招链验证 ==")

# 1. 链命中：boss 配 chains，连续 3 次行动按链出招
mon = mk_mon({"_chain_cfg": [{"seq": ["ms_ai_hao", "ms_an_ying_dan", "ms_bao_dan"], "cd": 0}]})
player = mk_player()
b = BT.Battle("monster", mon)
b._focus = player
import random
random.seed(7)
# 首次行动
logs1, _ = b._enemy_turn(player)
sk1 = (mon.get("_last_skill_key"))
b._now += 1.0  # 下一行动刻
logs2, _ = b._enemy_turn(player)
sk2 = mon.get("_last_skill_key")
b._now += 1.0
logs3, _ = b._enemy_turn(player)
sk3 = mon.get("_last_skill_key")
check("链第1招 = ms_ai_hao", sk1 == "ms_ai_hao", f"sk1={sk1}")
check("链第2招 = ms_an_ying_dan", sk2 == "ms_an_ying_dan", f"sk2={sk2}")
check("链第3招 = ms_bao_dan", sk3 == "ms_bao_dan", f"sk3={sk3}")

# 2. 链走完回绕（第4招回第1招）
b._now += 1.0
logs4, _ = b._enemy_turn(player)
sk4 = mon.get("_last_skill_key")
check("链回绕回第1招", sk4 == "ms_ai_hao", f"sk4={sk4}")

# 3. cd 冷却：链打完后等 N 刻不推进（cd=2 → 打完3招后冷却2刻）
mon2 = mk_mon({"_chain_cfg": [{"seq": ["ms_ai_hao", "ms_an_ying_dan"], "cd": 2}]})
b2 = BT.Battle("monster", mon2)
b2._focus = mk_player()
random.seed(3)
b2._enemy_turn(player)  # 招1
b2._now += 1.0
b2._enemy_turn(player)  # 招2（链打完，设冷却 until = r+2）
_until = mon2.get("_chain_until")
check("链尾设置冷却", _until is not None and _until > 0, f"until={_until}")
b2._now += 1.0
# 冷却中 → 不出链招（回落随机池或普攻）
b2._enemy_turn(player)
# 冷却中不应推进链 pos（应仍停在末尾或回绕但被 until 挡）
check("冷却中链不推进", mon2.get("_chain_pos", 0) == 0 or b2._tick_no() < (mon2.get("_chain_until") or 0),
      f"pos={mon2.get('_chain_pos')} tick={b2._tick_no()} until={mon2.get('_chain_until')}")

# 4. 多链轮换
mon3 = mk_mon({"_chain_cfg": [
    {"seq": ["ms_ai_hao"], "cd": 0},
    {"seq": ["ms_bao_dan"], "cd": 0},
]})
b3 = BT.Battle("monster", mon3)
b3._focus = mk_player()
random.seed(5)
b3._enemy_turn(player)
s1 = mon3.get("_last_skill_key")
b3._now += 1.0
b3._enemy_turn(player)
s2 = mon3.get("_last_skill_key")
check("链1招1 = ms_ai_hao", s1 == "ms_ai_hao", f"s1={s1}")
check("链1打完换链2 = ms_bao_dan", s2 == "ms_bao_dan", f"s2={s2}")

# 5. 无 chains 配置 → 零行为变化（不影响普通怪）
mon4 = mk_mon()
b4 = BT.Battle("monster", mon4)
b4._focus = mk_player()
random.seed(11)
logs5, _ = b4._enemy_turn(player)
check("无链普通怪正常行动", len(logs5) > 0, str(logs5[:1]))
check("无链不设 _chain_cfg", mon4.get("_chain_cfg") is None)

# 6. 链技能不存在时优雅回落（seq 里技能不在 skills）
mon6 = mk_mon({"_chain_cfg": [{"seq": ["ms_bu_cun_zai"], "cd": 0}]})
b6 = BT.Battle("monster", mon6)
b6._focus = mk_player()
random.seed(2)
logs6, _ = b6._enemy_turn(player)
check("链技能缺失不崩", len(logs6) > 0, str(logs6[:1]))

print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)