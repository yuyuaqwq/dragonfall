# -*- coding: utf-8 -*-
"""v177 actor-agnostic on_taken 受击钩子门禁（鱼鱼拍板：actor 字段即能力）

验证：
  1. build_monster 透传 on_taken 扩展字段（MONSTER_MODS 配了才生效，不配=旧行为）
  2. 怪物 on_taken.heal 受击回血（有 cd）
  3. 怪物 on_taken.atk_up 受击加攻（复仇，turns 刻内生效）
  4. 怪物 on_taken.shield 受击转盾（荆棘）
  5. 不配 on_taken 的怪 = 行为零变化（回归）
  6. dodge/block/phys_reduce 扩展字段透传生效

独立运行：python tests/test_numeric_actor_ontaken.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import conftest  # noqa: F401
except Exception:
    pass

from game import battle as BT
from game.core.drops import build_monster

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}: {detail}")


def mk_player():
    return {
        "class_name": "cls_zhan_shi", "level": 20, "name": "测试",
        "hp": 5000, "max_hp": 5000, "mp": 300, "max_mp": 300,
        "attributes": {}, "equipment": {}, "class_tier": 0,
        "learned_skills": [], "resources": {}, "buffs": {},
    }


def build_ontaken_monster(ontaken, extra=None):
    """走 build_monster 全链路：MONSTER_MODS 条目透传 on_taken → 怪物 dict"""
    mid = f"test_ot_{abs(hash(str(ontaken))) % 100000}"
    # monkeypatch MONSTER_MODS 临时条目
    from game.data.monster_mods import MONSTER_MODS
    MONSTER_MODS[mid] = dict(extra or {})
    MONSTER_MODS[mid]["on_taken"] = ontaken
    mdef = (mid, "受击测试怪", "boss", 20, ["ms_ai_hao"], [])
    mon = build_monster(mdef, {"area": "field", "name": "测试图", "id": "test_map"})
    del MONSTER_MODS[mid]
    return mon


print("== v177 actor on_taken 门禁 ==\n")

# 1. 透传字段存在
mon = build_ontaken_monster({"heal": {"pct": 0.05, "cd": 2}})
check("build_monster 透传 on_taken", mon.get("on_taken") is not None)
check("build_monster 透传 dodge=0 默认", mon.get("dodge") == 0.0)
mon2 = build_ontaken_monster({}, {"dodge": 0.25, "block": 0.2, "phys_reduce": 0.1})
check("build_monster 透传 dodge 配置", mon2.get("dodge") == 0.25, str(mon2.get("dodge")))
check("build_monster 透传 block 配置", mon2.get("block") == 0.2, str(mon2.get("block")))
check("build_monster 透传 phys_reduce 配置", mon2.get("phys_reduce") == 0.1, str(mon2.get("phys_reduce")))

# 2. on_taken.heal 受击回血
print("\n-- 受击回血 --")
player = mk_player()
mon = build_ontaken_monster({"heal": {"pct": 0.10, "cd": 2}})
mon["hp"] = 5000
mon["max_hp"] = 5000
b = BT.Battle("monster", mon)
b.player = player
logs = []
b._deal_damage(1000, logs)
# 回 10% = 500 → hp = 4000 + 500 = 4500（先扣 1000 再回 500）
check("受击回血 +500", mon["hp"] == 4500, f"hp={mon['hp']}")
check("受击回血有日志", any("受击回血" in l for l in logs), str(logs))

# 3. on_taken.atk_up 受击加攻
print("\n-- 受击加攻 --")
player = mk_player()
mon = build_ontaken_monster({"atk_up": {"pct": 0.20, "turns": 3}})
mon["hp"] = 5000
mon["max_hp"] = 5000
mon["atk"] = 100
mon["matk"] = 100
b = BT.Battle("monster", mon)
b.player = player
logs = []
b._deal_damage(100, logs)
check("受击激怒日志", any("激怒" in l for l in logs), str(logs))
est = b._enemy_stats()
check("加攻生效 atk=120", est["atk"] == 120, f"atk={est['atk']}")

# 4. on_taken.shield 受击转盾
print("\n-- 受击转盾 --")
player = mk_player()
mon = build_ontaken_monster({"shield": {"pct": 0.10}})
mon["hp"] = 5000
mon["max_hp"] = 5000
b = BT.Battle("monster", mon)
b.player = player
logs = []
b._deal_damage(100, logs)
check("受击凝甲日志", any("凝甲" in l or "护盾" in l for l in logs), str(logs))
check("target shields dict 已设", (mon.get("shields") or {}).get("on_taken", {}).get("value", 0) > 0, str(mon.get("shields")))

# 5. 不配 on_taken = 零变化（不报错不触发）
print("\n-- 无 on_taken 回归 --")
player = mk_player()
plain = {
    "name": "普通怪", "hp": 1000, "max_hp": 1000, "def": 10, "mdef": 10,
    "atk": 1, "spd": 10, "level": 20, "buffs": {},
}
b = BT.Battle("monster", plain)
b.player = player
logs = []
r = b._deal_damage(100, logs)
check("普通怪正常扣血", r == 100 and plain["hp"] == 900, f"r={r} hp={plain['hp']}")
check("无 on_taken 不误报", not any("受击回血" in l or "激怒" in l or "凝甲" in l for l in logs), str(logs))

print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
