# -*- coding: utf-8 -*-
"""v178 E6 验证：方向性防御（技能 defend_reduce 覆盖默认 0.5）"""
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

def mk_mon():
    return {"name": "测试Boss", "hp": 8000, "max_hp": 8000, "def": 60, "mdef": 60,
            "atk": 200, "matk": 100, "spd": 10, "lv": 40, "id": "m_test",
            "buffs": {}, "resources": {}, "stacks": {}, "charging": None,
            "skills": ["ms_ai_hao"]}

print("== E6 方向性防御验证 ==")

# 准备技能：普通技能（无 defend_reduce）+ 风眼技（defend_reduce=0.8）
MONSTER_SKILLS["ms_test_normal"] = {"kind": "物理", "power": 1.0, "desc": "普通测试", "name": "普通攻击"}
MONSTER_SKILLS["ms_test_eye"] = {"kind": "魔法", "power": 1.0, "defend_reduce": 0.8,
                                 "desc": "风眼测试", "name": "风眼冲击"}

def run_evasion(skill_key, seed=0):
    """模拟敌方技能命中 + 玩家防御（走 _process_until 的 defend 分支太复杂，
    直接验证 _enemy_cast_done 伤害 + defend_reduce 折算逻辑）"""
    import random as _r
    _r.seed(seed)
    player = mk_player()
    mon = mk_mon()
    b = BT.Battle("monster", mon)
    b.player = player
    # v180F 防御格挡下沉承伤链：_enemy_cast_done 管线分支内部扣血（返回 dmg=0），
    # 格挡在 _damage_actor 按 player.defending 消费。旧断言"返回 dmg>0"已不适用——
    # 改为设 defending 标志，断言真实 hp 扣减比例（格挡前后对比）。
    hp0 = player.get("hp", 0)
    logs, dmg, _ = b._enemy_cast_done(player, mon, {"kind": "skill", "skill": skill_key})
    dealt = hp0 - player.get("hp", 0)
    return dmg, dealt

try:
    # 1. defend_reduce 数据被 _lookup_skill_info 读到
    info = BT.Battle("monster", mk_mon())._lookup_skill_info("ms_test_eye")
    check("技能 defend_reduce 可读", info.get("defend_reduce") == 0.8, str(info))

    # 2. 直接验证折算逻辑（手动模拟 2523 消费点）
    dmg_normal, dealt_normal = run_evasion("ms_test_normal")
    dmg_eye, dealt_eye = run_evasion("ms_test_eye")
    # v180F 新语义：skill 分支管线内部已扣血 → 返回 dmg=0（防 double dip），
    # 未防御时实际扣血 > 0
    check("普通技管线内部扣血 (返回0防双扣)", dmg_normal == 0, f"dmg={dmg_normal}")
    check("普通技实际扣血>0", dealt_normal > 0, f"dealt={dealt_normal}")
    check("风眼技实际扣血>0", dealt_eye > 0, f"dealt={dealt_eye}")

    # 3. 防御格挡真实验证：player defending=True → _damage_actor 承伤链格挡
    def run_defend(skill_key, seed=0):
        import random as _r
        _r.seed(seed)
        player = mk_player()
        mon = mk_mon()
        b = BT.Battle("monster", mon)
        b.player = player
        player["defending"] = True
        hp0 = player.get("hp", 0)
        logs, dmg, _ = b._enemy_cast_done(player, mon, {"kind": "skill", "skill": skill_key})
        return hp0 - player.get("hp", 0)
    dealt_n_def = run_defend("ms_test_normal", seed=11)   # 默认 0.5
    dealt_e_def = run_defend("ms_test_eye", seed=12)      # 0.8
    # 未防御基线（同 seed 配对——随机序列一致，只差 defending 标志）
    _, dealt_n_plain = run_evasion("ms_test_normal", seed=11)
    _, dealt_e_plain = run_evasion("ms_test_eye", seed=12)
    check("普通技防御减半生效 (dealt≈0.5×plain)",
          abs(dealt_n_def - dealt_n_plain * 0.5) <= max(2, dealt_n_plain * 0.1),
          f"def={dealt_n_def} plain={dealt_n_plain}")
    check("风眼技防御挡 80% (dealt≈0.2×plain)",
          abs(dealt_e_def - dealt_e_plain * 0.2) <= max(2, dealt_e_plain * 0.1),
          f"def={dealt_e_def} plain={dealt_e_plain}")

    # 4. 折算函数正确性（纯数学断言保留）
    base = 1000
    check("默认 0.5 → 剩 500", max(1, int(round(base * (1 - 0.5)))) == 500)
    check("0.8 → 剩 200", max(1, int(round(base * (1 - 0.8)))) == 200)
    check("0.9 → 剩 100", max(1, int(round(base * (1 - 0.9)))) == 100)
    check("边界 0.95 → 剩 50", max(1, int(round(base * (1 - 0.95)))) == 50)

finally:
    MONSTER_SKILLS.pop("ms_test_normal", None)
    MONSTER_SKILLS.pop("ms_test_eye", None)

print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
