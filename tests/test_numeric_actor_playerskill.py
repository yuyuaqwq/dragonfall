# -*- coding: utf-8 -*-
"""v177 怪物引用玩家技能门禁（鱼鱼拍板：存储分离、解析一套——怪物能配玩家技能组）

验证：
  1. E.skill_by_key 全局查玩家技能（基础职业/分支/导师）
  2. 怪物 skills 直接放玩家技能 key → AI/结算能识别（_lookup_skill_info）
  3. 怪物施放玩家伤害技能（exprs）→ resolve_formula 正常结算
  4. 怪物施放玩家治疗技能（kind=治疗 + heal_formula）→ 自疗回血
  5. 旧怪物技能（MONSTER_SKILLS）查表零变化

独立运行：python tests/test_numeric_actor_playerskill.py
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
from game import engine as E
from game.data.skills import PLAYER_SKILLS

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


def mk_player(cls="cls_zhan_shi"):
    return {
        "class_name": cls, "level": 25, "name": "测试",
        "hp": 5000, "max_hp": 5000, "mp": 500, "max_mp": 500,
        "attributes": {}, "equipment": {}, "class_tier": 0,
        "learned_skills": [], "resources": {}, "buffs": {},
        "def": 50, "mdef": 50, "spd": 10,
    }


print("== v177 怪物引用玩家技能门禁 ==\n")

# 1. skill_by_key 全局查表
import random
info = E.skill_by_key("sk_hui_kan")
check("skill_by_key 查战士挥砍", info is not None and info.get("name") == "挥砍", str(info))
owner = E.skill_owner_cls("sk_hui_kan")
check("skill_owner_cls=战士", owner == "cls_zhan_shi", str(owner))

# 2. 怪物 skills 直接放玩家 key → _lookup_skill_info 识别
mon = {"name": "持剑魔像", "hp": 8000, "max_hp": 8000, "def": 60, "mdef": 60,
       "atk": 120, "matk": 100, "spd": 12, "lv": 20, "id": "m_sword",
       "buffs": {}, "resources": {}, "stacks": {}, "charging": None,
       "skills": ["sk_hui_kan"]}
player = mk_player("cls_fa_shi")
b = BT.Battle("monster", mon)
b.player = player
s = b._lookup_skill_info("sk_hui_kan")
check("_lookup_skill_info 查玩家技能", s.get("name") == "挥砍", str(s.get("name")))
s_old = b._lookup_skill_info("ms_ai_hao")
check("_lookup_skill_info 查怪物技能(旧表)", s_old.get("name") == "哀嚎", str(s_old.get("name")))

# 3. 怪物施放玩家伤害技能 → 有伤害（完整管线：伤害+mech+日志）
print("\n-- 怪物放玩家伤害技 --")
mon["hp"] = 8000
player["hp"] = 5000
random.seed(2)
hp0 = player["hp"]
logs, dmg = b._enemy_cast_done(player, mon, {"kind": "skill", "skill": "sk_hui_kan"})
dealt = hp0 - player["hp"]
# v180F：管线内部扣血返回 dmg=0——伤害断言改看真实 hp 扣减
check("挥砍造成伤害>0", dealt > 100, f"dealt={dealt}")
check("玩家被打掉血", player["hp"] < 5000, f"玩家hp={player['hp']}")
check("战意叠层(完整管线)", int((mon.get("stacks") or {}).get("zhan_yi", 0)) > 0, str(mon.get("stacks")))
check("伤害日志", any("伤害" in l for l in logs), str(logs[:2]))

# 4. 怪物施放玩家治疗技能 → 自疗
print("\n-- 怪物放玩家治疗技 --")
mu = PLAYER_SKILLS["cls_mu_shi"]["skills"]
heal_key = next((k for k, v in mu.items() if v.get("kind") == "治疗" and "heal_formula" in v), None)
check("找到牧师治疗技", heal_key is not None)
if heal_key:
    priest = {"name": "堕落祭司", "hp": 3000, "max_hp": 3000, "def": 60, "mdef": 70,
              "atk": 80, "matk": 150, "spd": 10, "lv": 25, "id": "m_priest",
              "buffs": {}, "resources": {}, "stacks": {}, "charging": None,
              "skills": [heal_key]}
    b2 = BT.Battle("monster", priest)
    b2.player = dict(player)
    priest["hp"] = 1000
    random.seed(3)
    logs2, dmg2 = b2._enemy_cast_done(player, priest, {"kind": "skill", "skill": heal_key})
    check("牧师怪治疗回血", priest["hp"] > 1000, f"hp={priest['hp']}")
    check("治疗无伤害", dmg2 == 0, f"dmg={dmg2}")
    check("治疗日志", any("治愈" in l or "回复" in l or "治疗" in l for l in logs2), str(logs2[:1]))

print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
