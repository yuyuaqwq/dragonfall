# -*- coding: utf-8 -*-
"""临时验证脚本（DOT 重构 · Battle 层 _tick_dots）——由重构 agent A 编写，验证后删除。"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game import battle as BT

PASS = []
FAIL = []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"  ✓ {name}")
    else:
        FAIL.append(name)
        print(f"  ✗ {name}  {detail}")


def make_player():
    return {"class_name": "zhan_shi", "qq_id": 1, "max_hp": 1000, "hp": 1000,
            "max_mp": 500, "mp": 500, "atk": 100, "def": 50, "matk": 80, "mdef": 50,
            "spd": 10, "crit": 0.05, "equipment": {}, "skills": [],
            "skill_levels": {}, "learned_skills": []}


def enemy(hp, **kw):
    e = {"name": "靶子", "lv": 10, "hp": hp, "max_hp": hp,
         "atk": 1, "def": 1, "matk": 1, "mdef": 1, "spd": 1}
    e.update(kw)
    return e


def tick_n(b, player, n):
    """模拟单机每玩家行动结算 n 次 dot（每次前置 _dot_pending=True 还原闸门）。"""
    dmg_total = 0
    b.debuffs_history = []
    for _ in range(n):
        b._dot_pending = True
        logs = b._turn_start(player)
        b.debuffs_history.append((b.enemy.get("debuffs", {}).copy(),
                                  b.enemy.get("max_hp", 1) - b.enemy["hp"] - dmg_total))
        dmg_total = b.enemy.get("max_hp", 1) - b.enemy["hp"]
        if b.result == "victory":
            break
    return dmg_total, b.debuffs_history


print("=== 场景1：无抗性怪 5 层毒，5 回合总伤 75% 且逐层衰减消散 ===")
# dot=40 层，用尽量大的最大生命避免浮点截断影响；5 层每回合 5%、上限 75% 需敌人不死
pl = make_player()
b = BT.Battle("monster", enemy(hp=100000))
b.enemy["debuffs"] = {"poison": {"n": 5, "mult": 1.0}}
tot, hist = tick_n(b, pl, 5)
maxhp = 100000
# 逐层期望伤害：25%+20%+15%+10%+5% = 75% = 75000
exp_seq = [int(maxhp * 0.05 * n) for n in (5, 4, 3, 2, 1)]
got_seq = [d for _, d in hist]
check("5 回合总伤 = 75%", tot == int(maxhp * 0.75), f"tot={tot}")
check("逐层衰减 25/20/15/10/5%", got_seq == exp_seq, f"{got_seq} vs {exp_seq}")
check("第 5 回合后毒层消散", not b.enemy.get("debuffs", {}).get("poison"), f"{b.enemy.get('debuffs')}")

print("--- 场景1b：毒杀死敌人 → 死亡文案=毒发身亡 ---")
b1b = BT.Battle("monster", enemy(hp=40000))
b1b.enemy["debuffs"] = {"poison": {"n": 5, "mult": 2.0}}  # 两倍毒伤：25%×2+20%×2+15%×2 = 120% → 死亡
for _ in range(6):
    b1b._dot_pending = True
    logs1b = b1b._turn_start(pl)
    if b1b.result == "victory":
        break
check("毒杀死亡文案=毒发身亡", b1b.result == "victory" and any("毒发身亡" in x for x in logs1b),
      f"result={b1b.result}, hp={b1b.enemy.get('hp', 0)}")

print("=== 场景2：dot_res=0.9 怪 5 层毒，首回合伤害 = 25%×0.1 ===")
b2 = BT.Battle("monster", enemy(hp=100000, dot_res=0.9))
b2.enemy["debuffs"] = {"poison": {"n": 5, "mult": 1.0}}
b2._dot_pending = True
logs2 = b2._turn_start(pl)
first_dmg = 100000 - b2.enemy["hp"]
check("首回合 = 25%×0.1 = 2500", first_dmg == int(100000 * 0.05 * 5 * (1 - 0.9)),
      f"got {first_dmg}")

print("=== 场景3：灼烧走 fire 元素抗 / 毒不吃元素抗 ===")
b3 = BT.Battle("monster", enemy(hp=100000, elem_res=0.5))
b3.enemy["debuffs"] = {"burn": {"n": 1, "mult": 1.0}}
b3._dot_pending = True
b3._turn_start(pl)
burn_dmg = 100000 - b3.enemy["hp"]
check("灼烧吃火元素抗 50%：3%×0.5=1500", burn_dmg == int(100000 * 0.03 * 0.5), f"got {burn_dmg}")
b3b = BT.Battle("monster", enemy(hp=100000, elem_res=0.5))
b3b.enemy["debuffs"] = {"poison": {"n": 1, "mult": 1.0}}
b3b._dot_pending = True
b3b._turn_start(pl)
poison_dmg = 100000 - b3b.enemy["hp"]
check("毒不吃元素抗：5%×1=5000", poison_dmg == int(100000 * 0.05), f"got {poison_dmg}")

print("=== 场景4：护盾 boss（mech 含 shield、boss_shield>0）dot 伤害减半 ===")
b4 = BT.Battle("monster", enemy(hp=100000, mech="shield", boss_shield=99999))
b4.enemy["debuffs"] = {"poison": {"n": 1, "mult": 1.0}}
b4._dot_pending = True
b4._turn_start(pl)
dmg4 = 100000 - b4.enemy["hp"]
exp4 = int(100000 * 0.05 * 0.5)  # 护盾 -50%
check("护盾 boss dot 减半 = 2500", dmg4 == exp4, f"got {dmg4}, shield_left={b4.enemy.get('boss_shield')}")

print("=== 场景5：免疫 burn 的怪，burn 直接消散不结算 ===")
b5 = BT.Battle("monster", enemy(hp=100000, immune_dots=["burn"]))
b5.enemy["debuffs"] = {"burn": {"n": 3, "mult": 1.0}}
b5._dot_pending = True
logs5 = b5._turn_start(pl)
check("免疫烧灼不扣血", b5.enemy["hp"] == 100000, f"hp={b5.enemy['hp']}")
check("免疫层已移除", "burn" not in b5.enemy.get("debuffs", {}), f"{b5.enemy.get('debuffs')}")

print("=== 场景6：dot_res cap 0.95 ===")
b6 = BT.Battle("monster", enemy(hp=100000, dot_res=9.9))
b6.enemy["debuffs"] = {"poison": {"n": 1, "mult": 1.0}}
b6._dot_pending = True
b6._turn_start(pl)
dmg6 = 100000 - b6.enemy["hp"]
check("cap 0.95：5%×0.05=250", dmg6 == int(100000 * 0.05 * (1 - 0.95)), f"got {dmg6}")

print("=== 场景7：mult（叠毒者被动倍率）参与结算，读 debuffs 不重算 ===")
b7 = BT.Battle("monster", enemy(hp=100000))
b7.enemy["debuffs"] = {"poison": {"n": 2, "mult": 1.5}}
b7._dot_pending = True
b7._turn_start(pl)
dmg7 = 100000 - b7.enemy["hp"]
check("mult=1.5，2 层：5%×2×1.5=15000", dmg7 == int(100000 * 0.05 * 2 * 1.5), f"got {dmg7}")

print("=== 场景8：老存档迁移（from_state）===")
b8 = BT.Battle.from_state({
    "type": "monster",
    "enemy": {"name": "老怪", "hp": 1000, "max_hp": 1000, "atk": 1, "def": 1, "matk": 1, "mdef": 1, "spd": 1},
    "mech_stacks": {"poison": 3, "burn": 2, "dragon_mark": 4, "rage": 5},
    "resources": {}, "cooldown": {}, "combo_seq": [],
})
deb8 = b8.enemy.get("debuffs", {})
check("迁移 poison→debuffs", deb8.get("poison") == {"n": 3, "mult": 1.0}, f"{deb8}")
check("迁移 burn→debuffs", deb8.get("burn") == {"n": 2, "mult": 1.0}, f"{deb8}")
check("mech_stacks 已删敌方键", "poison" not in b8.mech_stacks and "burn" not in b8.mech_stacks,
      f"{b8.mech_stacks}")
check("玩家键 dragon_mark/rage 保留", b8.mech_stacks.get("dragon_mark") == 4 and b8.mech_stacks.get("rage") == 5,
      f"{b8.mech_stacks}")
check("dot_pending 默认 True", b8._dot_pending is True, str(b8._dot_pending))

print("=== 场景9：dot_pending 闸门——instance/worldboss 模式同帧不重复结算 ===")
# 用非 monster btype（如 worldboss）验证闸门：_turn_start 不复位，同帧二次调用不重复 tick
b9 = BT.Battle("worldboss", enemy(hp=100000))
b9.enemy["debuffs"] = {"poison": {"n": 2, "mult": 1.0}}
b9._dot_pending = True
# 第一次调用（模拟一次行动）：结算一次
before = b9.enemy["hp"]
b9._turn_start(pl)
dmg9a = before - b9.enemy["hp"]
# 同帧第二次调用（未经过 from_state/行动边界）：闸门已关，不应再结算
before = b9.enemy["hp"]
b9._turn_start(pl)
dmg9b = before - b9.enemy["hp"]
check("第一次行动结算 dot", dmg9a == int(100000 * 0.05 * 2), f"got {dmg9a}")
check("同帧第二次不重复结算", dmg9b == 0, f"got {dmg9b}")

print("=== 场景10：灼烧/流血死亡文案分型 ===")
# 灼烧致死
b10 = BT.Battle("monster", enemy(hp=50000))
b10.enemy["debuffs"] = {"burn": {"n": 5, "mult": 10.0}}  # 灼烧致死
for _ in range(8):
    b10._dot_pending = True
    lg = b10._turn_start(pl)
    if b10.result == "victory":
        break
check("灼烧致死文案", b10.result == "victory" and any("灼烧致死" in x for x in lg),
      f"result={b10.result}")
# 流血致死
b10b = BT.Battle("monster", enemy(hp=50000))
b10b.enemy["debuffs"] = {"bleed": {"n": 3, "mult": 10.0}}
for _ in range(8):
    b10b._dot_pending = True
    lg = b10b._turn_start(pl)
    if b10b.result == "victory":
        break
check("失血过多文案", b10b.result == "victory" and any("失血过多" in x for x in lg),
      f"result={b10b.result}")

print(f"\n===== 结果: {len(PASS)} 通过, {len(FAIL)} 失败 =====")
if FAIL:
    print("失败:", FAIL)
    sys.exit(1)
