# -*- coding: utf-8 -*-
"""v178 E3 验证：阶段四件套复活（ult_every/freq_mult/exit_turns/exit_dmg 消费）"""
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

def mk_mon(extra=None):
    m = {"name": "测试Boss", "hp": 8000, "max_hp": 8000, "def": 60, "mdef": 60,
         "atk": 100, "matk": 80, "spd": 10, "lv": 40, "id": "m_test",
         "buffs": {}, "resources": {}, "stacks": {}, "charging": None,
         "skills": ["ms_ai_hao"], "mech": "phase"}
    if extra:
        m.update(extra)
    return m

def mk_player():
    return {"class_name": "cls_zhan_shi", "level": 40, "name": "测试", "hp": 9999, "max_hp": 9999,
            "mp": 500, "max_mp": 500, "attributes": {}, "equipment": {}, "class_tier": 0,
            "learned_skills": [], "resources": {}, "buffs": {}, "def": 50, "mdef": 50, "spd": 10}

print("== E3 阶段四件套复活验证 ==")

# 1. freq_mult 折入 spd（freq=0.5 → spd/0.5=×2）
mon = mk_mon()
mon["_phase_mod"] = {"atk_mult": 1.0, "def_add": 0, "spd_add": 0, "dmg_taken_mult": 1.0}
mon["_phase_freq_mult"] = 0.5
player = mk_player()
b = BT.Battle("monster", mon)
b._focus = player
est = b._enemy_stats()
check("freq_mult=0.5 → spd 折半行动慢一倍 (spd 10→20)", est["spd"] == 20, f"spd={est['spd']}")

# freq=2.0 → spd/2=5（行动快一倍）
mon2 = mk_mon()
mon2["_phase_mod"] = {"atk_mult": 1.0, "def_add": 0, "spd_add": 0, "dmg_taken_mult": 1.0}
mon2["_phase_freq_mult"] = 2.0
b2 = BT.Battle("monster", mon2)
b2._focus = player
est2 = b2._enemy_stats()
check("freq_mult=2.0 → spd 减半 (spd 10→5)", est2["spd"] == 5, f"spd={est2['spd']}")

# 无 freq_mult = 不变
mon3 = mk_mon()
mon3["_phase_mod"] = {"atk_mult": 1.0, "def_add": 0, "spd_add": 0, "dmg_taken_mult": 1.0}
b3 = BT.Battle("monster", mon3)
b3._focus = player
est3 = b3._enemy_stats()
check("无 freq_mult → spd 不变", est3["spd"] == 10, f"spd={est3['spd']}")

# 2. ult_every 消费：每 3 刻强制大招
import random
# 造一个带 ult 配置的怪（phase_count 已进入有 _phase_ult_every/_phase_ult_skills 的阶段）
mon4 = mk_mon()
mon4["_phase_ult_every"] = 3
mon4["_phase_ult_skills"] = ["ms_huo_yan_bao"]  # 假定技能在技能表
# 用真实技能 ms_jian_ta（践踏，charge 技能）——ult 大招施放逻辑走正常技能分支
from game.data.monsters import MONSTER_SKILLS
real_skill = [k for k in MONSTER_SKILLS if MONSTER_SKILLS[k].get("kind") != "增益"][:1]
mon4["_phase_ult_skills"] = real_skill
mon4["skills"] = list(set(mon4["skills"]) | set(real_skill))
b4 = BT.Battle("monster", mon4)
b4._focus = player
# 直接调 _enemy_turn 验证 ult 分支（r=3 时 tick_no=3 → 3%3==0）
b4._now = 2 * 1.0  # tick_no = int(now/ACT_TICK)+1; ACT_TICK=1 → tick=3
random.seed(42)
logs, dmg = b4._actor_auto_turn(player)
# 若 ult 触发，日志会有技能名（非普攻"挥爪"）
joined = " ".join(logs)
check("ult_every 触发（tick3 大招而非普攻）", "挥爪" not in joined and len(logs) > 0,
      f"logs={logs[:2]}")

# 3. exit_turns：进入阶段后超过 N 刻自动退出（_phase_exit 被消费）
mon5 = mk_mon()
mon5["_phase_exit"] = {"turns": 3, "dmg": None, "entered_at": 1}
mon5["_phase_mod"] = {"atk_mult": 1.3, "def_add": 10, "spd_add": 0, "dmg_taken_mult": 1.0}
b5 = BT.Battle("monster", mon5)
b5._focus = player
b5._now = 4 * 1.0  # tick = 5 → 5-1=4 >= 3 → 触发退出
logs5, _ = b5._actor_auto_turn(player)
check("exit_turns 触发退出", "_phase_exit" not in mon5 and "_phase_mod" not in mon5,
      f"exit={mon5.get('_phase_exit')} mod={mon5.get('_phase_mod')}")
check("exit 日志", any("气息回落" in l for l in logs5), str(logs5[:2]))

# 4. 未到 exit_turns 不退出
mon6 = mk_mon()
mon6["_phase_exit"] = {"turns": 10, "dmg": None, "entered_at": 1}
mon6["_phase_mod"] = {"atk_mult": 1.3, "def_add": 10, "spd_add": 0, "dmg_taken_mult": 1.0}
b6 = BT.Battle("monster", mon6)
b6._focus = player
b6._now = 2 * 1.0  # tick=3 → 3-1=2 < 10 → 不退出
logs6, _ = b6._actor_auto_turn(player)
check("未到 exit_turns 不退出", "_phase_exit" in mon6, "已退出?")

# 5. _phase_apply 写入 _phase_ult_skills（数据字段透传）
mon7 = mk_mon()
b7 = BT.Battle("monster", mon7)
b7._focus = player
b7._phase_apply(mon7, {"atk_mult": 1.0, "def_add": 0, "spd_add": 0, "dmg_taken_mult": 1.0,
                       "freq_mult": 0.5, "ult_every": 3, "ult_skills": ["ms_x"],
                       "exit_turns": 5, "exit_dmg": None, "counter": "打它"}, 1, [])
check("_phase_apply 写 ult_skills", mon7.get("_phase_ult_skills") == ["ms_x"], str(mon7.get("_phase_ult_skills")))
check("_phase_apply 写 freq_mult", mon7.get("_phase_freq_mult") == 0.5, str(mon7.get("_phase_freq_mult")))
check("_phase_apply 写 exit", mon7.get("_phase_exit", {}).get("turns") == 5, str(mon7.get("_phase_exit")))
check("_phase_apply 写 counter", mon7.get("_phase_counter") == "打它", str(mon7.get("_phase_counter")))

print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)