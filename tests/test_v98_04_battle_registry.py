# -*- coding: utf-8 -*-
"""v98.4 注册表验收测试：battle_conds / battle_mech

验收标准（设计文档）：
1. 扩展性：注册新条件/机制 → 战斗系统立即生效，无需改 battle.py
2. 安全降级：未知 key 不报错（条件=1.0 / 机制=无操作）
3. 全覆盖：技能/怪物/boss 数据用到的 key 全部有注册（数据驱动不落空）
4. 行为等价：注册表版与旧 elif 链语义一致（mval=0 守卫、is_crit 守卫等）

独立运行：python tests/test_v98_04_battle_registry.py
"""
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 统一走 conftest 的 qqbot 包路径（data.plugins.dragonfall.*），避免双路径双模块循环
from conftest import BT  # noqa: F401  Battle 类
from data.plugins.dragonfall.game.core import battle_conds as BC
from data.plugins.dragonfall.game.core import battle_mech as BM

Battle = BT.Battle

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


def make_battle(**kw):
    """造一个最小 Battle 实例（monster 型）"""
    enemy = kw.pop("enemy", {"name": "野狼", "hp": 100, "max_hp": 100, "atk": 20, "matk": 15, "def": 5, "mdef": 5, "spd": 10})
    b = Battle(btype="monster", enemy=enemy, player={"class_name": "cls_zhan_shi"})
    b.round = kw.pop("round", 1)
    b.e_buffs = kw.pop("e_buffs", {})
    b.p_buffs = kw.pop("p_buffs", {})
    b.mech_stacks = kw.pop("mech_stacks", {})
    b.shield = kw.pop("shield", 0)
    b.resources = kw.pop("resources", {})
    b._player_hit = kw.pop("player_hit", False)
    b._last_player = kw.pop("last_player", None)
    return b


player = {"hp": 100, "max_hp": 100}


# ============ 1. 条件注册表扩展性 ============
print("【1. 条件注册表扩展性】")
BEFORE = set(BC.COND_CHECKS.keys())


@BC.register("test_fake_cond")
def _c_test_fake(battle, player, cond):
    return True


check("注册新条件后 COND_CHECKS 含新 key", "test_fake_cond" in BC.COND_CHECKS)
b = make_battle(enemy={"name": "野狼", "hp": 100, "max_hp": 100, "atk": 20, "matk": 15, "def": 5, "mdef": 5, "spd": 10})
check("新条件立即生效（返回倍率）", b._cond_mult({"cond": {"type": "test_fake_cond", "mult": 1.6}}, player, 1) == 1.6)
# 清理测试注册
BC.COND_CHECKS.pop("test_fake_cond")
check("清理后恢复原状", BC.COND_CHECKS.keys() == BEFORE or set(BC.COND_CHECKS.keys()) - {"test_fake_cond"} == BEFORE)

# ============ 2. 条件安全降级 ============
print("【2. 条件安全降级】")
b = make_battle()
check("未知 cond type → 1.0", b._cond_mult({"cond": {"type": "not_a_real_type", "mult": 9.9}}, player, 1) == 1.0)
check("无 cond → 1.0", b._cond_mult({"dmg": 10}, player, 1) == 1.0)

# ============ 3. 条件行为抽样（对照旧语义） ============
print("【3. 条件行为抽样】")
b = make_battle(enemy={"name": "野狼", "hp": 30, "max_hp": 100, "atk": 20, "matk": 15, "def": 5, "mdef": 5, "spd": 10})
check("enemy_hp_low（30/100 < 40%）命中", b._cond_mult({"cond": {"type": "enemy_hp_low", "mult": 1.6}}, player, 1) == 1.6)
b = make_battle(enemy={"name": "野狼", "hp": 80, "max_hp": 100, "atk": 20, "matk": 15, "def": 5, "mdef": 5, "spd": 10})
check("enemy_hp_low（80/100 ≥ 40%）不命中", b._cond_mult({"cond": {"type": "enemy_hp_low", "mult": 1.6}}, player, 1) == 1.0)
b = make_battle(e_buffs={"freeze": 1})
check("enemy_frozen 命中", b._cond_mult({"cond": {"type": "enemy_frozen", "mult": 1.5}}, player, 1) == 1.5)
b = make_battle()
check("enemy_frozen 未冻结不命中", b._cond_mult({"cond": {"type": "enemy_frozen", "mult": 1.5}}, player, 1) == 1.0)
b = make_battle(mech_stacks={"poison": 5})
check("enemy_poison_stacks（5≥3）命中", b._cond_mult({"cond": {"type": "enemy_poison_stacks", "mult": 1.4}}, player, 1) == 1.4)
b = make_battle(shield=10)
check("player_shield 命中", b._cond_mult({"cond": {"type": "player_shield", "mult": 1.3}}, player, 1) == 1.3)
b = make_battle(resources={"rage": 5})
check("player_res_stacks（rage 5≥3）命中", b._cond_mult({"cond": {"type": "player_res_stacks", "res_key": "rage", "stacks": 3, "mult": 1.5}}, player, 1) == 1.5)
b = make_battle(p_buffs={"spd_up": 1})
check("player_spd_up 命中", b._cond_mult({"cond": {"type": "player_spd_up", "mult": 1.2}}, player, 1) == 1.2)
b = make_battle(player_hit=True)
check("player_untouched（已受击）不命中", b._cond_mult({"cond": {"type": "player_untouched", "mult": 1.8}}, player, 1) == 1.0)

# ============ 4. 机制注册表扩展性 ============
print("【4. 机制注册表扩展性】")
BEFORE_M = set(BM.MECH_EFFECTS.keys())


@BM.register(BM.MECH_EFFECTS, "test_fake_mech")
def _m_test_fake(battle, mval, p_mech, total, logs, skill_name, is_crit):
    p_mech["test_flag"] = mval
    logs.append("测试机制触发")


check("注册新机制后 MECH_EFFECTS 含新 key", "test_fake_mech" in BM.MECH_EFFECTS)
b = make_battle()
logs = []
b._apply_mech_effect("test_fake_mech", 3, {}, 100, logs, "测试技能")
check("新机制立即生效", logs == ["测试机制触发"])
BM.MECH_EFFECTS.pop("test_fake_mech")

# ============ 5. 机制安全降级 ============
print("【5. 机制安全降级】")
b = make_battle()
logs = []
b._apply_mech_effect("not_a_real_mech", 1, {}, 100, logs, "技能")
check("未知 mech → 无操作不报错", logs == [] and b.enemy["hp"] == 100)

# ============ 6. 机制行为抽样（守卫语义） ============
print("【6. 机制行为抽样】")
# mval=0 守卫：rage 叠层不触发
b = make_battle()
logs = []
p_mech = {}
b._apply_mech_effect("rage", 0, p_mech, 100, logs, "狂怒斩")
check("rage mval=0 不叠层", "rage" not in p_mech and logs == [])
# 正常叠层
b = make_battle()
logs = []
p_mech = {}
b._apply_mech_effect("rage", 2, p_mech, 100, logs, "狂怒斩")
check("rage mval=2 叠层", p_mech.get("rage", 0) >= 2 and len(logs) == 1)
# judge 非暴击不叠层
b = make_battle()
logs = []
p_mech = {}
b._apply_mech_effect("judge", 1, p_mech, 100, logs, "审判", False)
check("judge 非暴击不叠层", "judge" not in p_mech)
b = make_battle()
logs = []
p_mech = {}
b._apply_mech_effect("judge", 1, p_mech, 100, logs, "审判", True)
check("judge 暴击叠层", p_mech.get("judge", 0) >= 1)
# mark 挂 e_buffs
b = make_battle()
logs = []
p_mech = {}
b._apply_mech_effect("mark", 1, p_mech, 100, logs, "猎杀标记")
check("mark 挂 e_buffs", "mark" in b.e_buffs and p_mech.get("mark", 0) >= 1)
# shield_burst 扣血 + 清零
b = make_battle()
logs = []
p_mech = {"shield": 5}
b._apply_mech_effect("shield_burst", 0, p_mech, 100, logs, "圣盾爆发")
check("shield_burst 扣血", b.enemy["hp"] < 100 and p_mech["shield"] == 0)
# spellblade_surge 魔能不足
b = make_battle()
logs = []
p_mech = {"spellblade": 1}
b._apply_mech_effect("spellblade_surge", 0, p_mech, 100, logs, "魔力涌动")
check("spellblade_surge 魔能不足不消耗", p_mech["spellblade"] == 1 and "无法施展" in logs[0])
# spellblade_meteor 消耗 5 层
b = make_battle()
logs = []
p_mech = {"spellblade": 5}
random.seed(42)
b._apply_mech_effect("spellblade_meteor", 0, p_mech, 100, logs, "星陨斩")
check("spellblade_meteor 消耗 5 层", p_mech["spellblade"] == 0)

# ============ 7. Boss 机制 ============
print("【7. Boss 机制】")
b = make_battle(enemy={"name": "暗影魔王", "hp": 50, "max_hp": 100, "atk": 20, "matk": 15, "def": 5, "mdef": 5, "spd": 10, "mech": "enrage,shield"})
logs = []
b.round = 1
b._boss_mech(logs)
check("enrage（50/100 不狂暴）不触发", not b.enemy.get("enraged"))
check("shield 首回合触发", b.enemy.get("boss_shield") == 20 and "护盾" in logs[0])
b.enemy["hp"] = 20
b.round = 2
logs = []
b._boss_mech(logs)
check("enrage（20/100 < 30%）触发", b.enemy.get("enraged") is True and "狂暴" in logs[0])
check("shield 非首回合不重复", b.enemy.get("boss_shield") == 20)
# 未知 boss mech 安全跳过
b = make_battle(enemy={"name": "怪", "hp": 100, "max_hp": 100, "atk": 20, "matk": 15, "def": 5, "mdef": 5, "spd": 10, "mech": "not_a_mech"})
logs = []
b._boss_mech(logs)
check("未知 boss mech 安全跳过", logs == [])

# ============ 8. 怪物增益/控制 ============
print("【8. 怪物增益/控制】")
b = make_battle(enemy={"name": "狼王", "hp": 100, "max_hp": 100, "atk": 20, "matk": 15, "def": 5, "mdef": 5, "spd": 10})
logs = []
BM.MON_BUFF_EFFECTS["atk_up"](b, logs, "嗜血怒吼")
check("怪物 atk_up 增益", b.e_buffs.get("mon_atk_up") == 3 and "攻击力提升" in logs[0])
b = make_battle(enemy={"name": "狼王", "hp": 50, "max_hp": 100, "atk": 20, "matk": 15, "def": 5, "mdef": 5, "spd": 10})
logs = []
BM.MON_BUFF_EFFECTS["heal_self"](b, logs, "疗愈")
check("怪物 heal_self 恢复 15%", b.enemy["hp"] == 65 and "15 点" in logs[0])
b = make_battle()
logs = []
random.seed(1)
BM.MON_CTRL_EFFECTS["silence"](b, player, logs, 1)
check("怪物 silence 稳定 2 回合", b.p_buffs.get("silence") == 2)
b = make_battle()
logs = []
BM.MON_CTRL_EFFECTS["slow"](b, player, logs, 1)
check("怪物 slow 减速", b.p_buffs.get("spd_down") == 2)

# ============ 9. 全覆盖：数据 key 全部有注册 ============
print("【9. 数据覆盖检查】")
import re
skills = open(os.path.join("game", "data", "skills.py"), encoding="utf-8").read()
data_mech = set(re.findall(r'"mech"\s*:\s*"([^"]+)"', skills)) - {"spd_down"}  # spd_down 旧实现即无操作
missing = data_mech - set(BM.MECH_EFFECTS.keys())
check(f"技能 mech 全覆盖（数据 {len(data_mech)} 个）", not missing)

monsters = open(os.path.join("game", "data", "monsters.py"), encoding="utf-8").read()
mon_eff = set(re.findall(r'"effect"\s*:\s*"([^"]+)"', monsters)) - {"shield", "spd_up"}  # 旧实现即无操作
missing_eff = mon_eff - set(BM.MON_BUFF_EFFECTS.keys())
check(f"怪物 effect 全覆盖（数据 {len(mon_eff)} 个）", not missing_eff)

mon_mech = set(re.findall(r'"mech"\s*:\s*"([^"]+)"', monsters))
missing_ctrl = mon_mech - set(BM.MON_CTRL_EFFECTS.keys())
check(f"怪物控制 mech 全覆盖（数据 {len(mon_mech)} 个）", not missing_ctrl)

cond_types = set(re.findall(r'"type"\s*:\s*"([^"]+)"', skills))
cond_reg = set(BC.COND_CHECKS.keys())
missing_cond = cond_types - cond_reg
check(f"技能 cond type 全覆盖（数据 {len(cond_types)} 个）", not missing_cond)

# boss mech 组合拆解后覆盖
instances = open(os.path.join("game", "data", "instances.py"), encoding="utf-8").read()
ism = open(os.path.join("game", "data", "instance_stage_maps.py"), encoding="utf-8").read()
all_boss_mech = set()
for src in (instances, ism, monsters):
    for combo in re.findall(r'"mech"\s*:\s*"([^"]+)"', src):
        for single in combo.split(","):
            all_boss_mech.add(single.strip())
# 原代码无实现的 key（reflect 被动 / 控制类走怪物控制）：允许缺失
implied = all_boss_mech - {"reflect", "freeze", "silence", "slow", "stun"}
missing_boss = implied - set(BM.BOSS_MECHS.keys())
check(f"boss mech 全覆盖（数据 {len(implied)} 个需实现）", not missing_boss)

# ============ 4.5 条件 label 全覆盖（v101.2） ============
print("【4.5 条件 label】")
all_cond_types = set()
for src in (skills, monsters, instances, ism):
    for m in re.finditer(r'"cond"\s*:\s*\{[^}]*"type"\s*:\s*"([^"]+)"', src):
        all_cond_types.add(m.group(1))
missing_label = all_cond_types - set(BC.COND_LABELS.keys())
check(f"技能/怪物/boss 数据用到的条件 type 全部有 label（数据 {len(all_cond_types)} 种）", not missing_label)
check("label 是函数且可渲染", all(callable(v) for v in BC.COND_LABELS.values()))
fn = BC.COND_LABELS.get("enemy_hp_low")
check("label 渲染样例（敌方血量<40%）", fn and fn({"hp_pct": 0.4}) == "敌方血量<40%")

print()
print(f"结果: {PASS} 通过, {FAIL} 失败")
sys.exit(1 if FAIL else 0)
