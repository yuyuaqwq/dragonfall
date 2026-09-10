# -*- coding: utf-8 -*-
"""P0 取证探针：技能冷却是否被强制？

问题：`battle2/actions.py:_skill_usable` docstring 声称做「学习/蓝/核心资源/冷却」四查，
      但函数体只查 res_cost；全仓库唯一读 `actor["cooldown"]` 的地方是 AI 的 cd_ok 谓词。

判据（本探针）：玩家连续两次施放同一个带 cd 的技能——
  若冷却生效 → 第二次应被拒绝（日志含「冷却」/「未就绪」且无伤害）
  若无冷却   → 第二次照常打出伤害

跑法：python tools/probe_cooldown_enforcement.py
"""
import os
import sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(PLUGIN_DIR, "test_probe_cd.db"))
os.environ.setdefault("GWEN_TEST_MODE", "1")
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)

from game.battle2 import config as _b2c
_b2c.load_game_defaults()
from game.battle2 import Battle as B2, make_actor
from game.data.skills import PLAYER_SKILLS

SKILL = "旋风斩"          # 战士技能，skills.py 声明 'cd': 12（刻）
cd_declared = None
for _cls, _box in PLAYER_SKILLS.items():
    for _k, _v in ((_box or {}).get("skills") or {}).items():
        if isinstance(_v, dict) and _v.get("name") == SKILL:
            cd_declared = _v.get("cd")
print(f"技能『{SKILL}』声明 cd = {cd_declared} 刻")


def mk_warrior():
    a = make_actor(uid="p_1", name="战士", side="player", kind="player",
                   human_controlled=True, class_name="cls_zhan_shi", level=30,
                   learned_skills=[SKILL], skills=[SKILL],
                   atk=200, matk=30, spd=80, hp=3000, max_hp=3000, mp=3000, max_mp=3000)
    a["effects"] = {}
    a["bonus"] = {"panel": {}, "cap": {}, "cost": {}}
    return a


def mk_dummy():
    e = make_actor(uid="e_1", name="木桩", side="enemy", kind="monster",
                   atk=1, matk=1, spd=1, hp=9999999, max_hp=9999999)
    e["effects"] = {}
    e["dodge"] = 0.0
    return e


a = mk_warrior()
e = mk_dummy()
b = B2("monster", sides={"player": [a], "enemy": [e]}, title_bonus={})

print("\n=== 第 1 次施放 ===")
logs1, _, _ = b.human_act("skill", SKILL, a)
d1 = [l for l in logs1 if "受到" in l and "伤害" in l]
print("\n".join(logs1[:8]))
print("→ 冷却表 after 1st:", a.get("cooldown"))

print("\n=== 第 2 次施放（**紧接**，同一 actor，声明 cd=%s 刻）===" % cd_declared)
logs2, _, _ = b.human_act("skill", SKILL, a)
d2 = [l for l in logs2 if "受到" in l and "伤害" in l]
print("\n".join(logs2[:8]))
print("→ 冷却表 after 2nd:", a.get("cooldown"))

print("\n" + "=" * 60)
if d1 and d2:
    print("❗ 结论：冷却【未生效】——连续两次都打出伤害")
    print(f"   第1次: {d1[0][:80]}")
    print(f"   第2次: {d2[0][:80]}")
    sys.exit(1)
elif d1 and not d2:
    print("✅ 结论：冷却【生效】——第二次被拒绝")
    sys.exit(0)
else:
    print("⚠️ 意外：第 1 次就没有伤害，探针无效（需换技能/参数）")
    print("   logs1 =", logs1)
    sys.exit(2)
