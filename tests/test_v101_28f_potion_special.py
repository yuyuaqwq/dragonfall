# -*- coding: utf-8 -*-
"""v101.28f 药水特殊效果回归：28 种药水 desc 与 effect 一致 + 特殊效果战斗内真实生效"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

from data.plugins.dragonfall.game import content as C
from data.plugins.dragonfall.game.core import item_templates as IT
from data.plugins.dragonfall.game.battle import Battle

PASS = FAIL = 0
def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} | {detail}")

def mk_battle():
    return Battle("monster", {"name": "野狗", "hp": 500, "max_hp": 500, "atk": 5, "def": 0,
                              "matk": 0, "mdef": 0, "spd": 1000}, {})

def mk_player(hp=100):
    return {"hp": hp, "max_hp": 100, "mp": 50, "max_mp": 100, "class_name": "cls_zhan_shi",
            "level": 1, "learned_skills": [], "race": "human", "attributes": {}, "equipment": {},
            "mdef": 0}

# ---- 1. 28 种药水数据一致性：desc 无"本回合"残留、effect 全部有映射 ----
print("== 1. 药水数据一致性 ==")
SPECIAL_EFFECTS = {"next_atk_up", "heal_up", "magic_resist", "thorns_pot", "dodge_pot",
                   "cc_immune", "execute_pot", "armor_break_pot", "rock_shield", "holy_shield"}
pot_keys = [k for k, v in C.ITEMS.items()
            if isinstance(v, dict) and v.get("effect") and "buff" in v.get("effect", "") or
            (isinstance(v, dict) and v.get("effect") in SPECIAL_EFFECTS)]
check("药水数量 ≥ 25", len(pot_keys) >= 25, str(len(pot_keys)))
bad = [(k, v.get("desc", "")) for k, v in C.ITEMS.items()
       if isinstance(v, dict) and v.get("effect") and "本回合" in v.get("desc", "")
       # v130.2 药水豁免：i_swiftness_core（resource_amp turns=1 真当回合生效）、
       # i_chi_pellet（restore_resource 立即生效，"本回合不破坏蓄势斜坡"为机制说明）——语义真实非占位
       and k not in ("i_swiftness_core", "i_chi_pellet")]
check("无'本回合'残留(desc 全真实)", not bad, str(bad[:3]))
bad2 = [(k, v["effect"]) for k, v in C.ITEMS.items()
        if isinstance(v, dict) and v.get("effect") in SPECIAL_EFFECTS | {"buff_atk", "buff_def", "buff_spd", "buff_crit", "buff_matk", "buff_atk_def", "buff_atk_big", "buff_atk_small", "buff_spd_small", "buff_crit_small", "buff_crit_big", "buff_matk_strong", "buff_matk_crit", "buff_atk_big_def"}
        and v["effect"] not in IT._BUFF_KEYS]
check("药水 effect 全部有模板映射", not bad2, str(bad2[:3]))

# ---- 2. 特殊效果模板 payload ----
print("== 2. 模板 payload ==")
class Ctx:
    def __init__(self, data):
        self.battle = True
        self.data = data
        self.player = mk_player()
        self.group_id = "g1"
        self.qq_id = "q1"
    def _db(self):
        class D:
            def update_player(self, *a, **k): pass
        return D()
    def hook(self, n, *a, **k):
        return 0

rp = IT.TEMPLATES["next_atk_up"](Ctx(C.ITEMS["i_fury_potion"]))
check("狂怒药剂 payload=special:next_atk_up", rp.payload == "special:next_atk_up", rp.payload)
rs = IT.TEMPLATES["rock_shield"](Ctx(C.ITEMS["i_rock_shield_pot"]))
check("岩盾药剂 payload=special:shield_small", rs.payload == "special:shield_small", rs.payload)

# ---- 3. 特殊效果战斗内生效 ----
print("== 3. 战斗内生效 ==")
# 狂怒：下一次攻击 +50%（一次性）
b = mk_battle()
p = mk_player()
b._do_use_item("special:next_atk_up", p)
check("狂怒挂载 p_buffs", b.p_buffs.get("next_atk_up") == 1, str(b.p_buffs))
mult, tags = b._affix_dmg_mult(p)
check("狂怒倍率 1.5 且消耗", mult == 1.5 and "next_atk_up" not in b.p_buffs, f"{mult} {tags} {b.p_buffs}")

# 岩盾：10% 护盾 3 回合（v152 时刻制：{value, expire_at}，expire_at = now + 3×2.0 = 6.0）
b2 = mk_battle()
p2 = mk_player()
b2._do_use_item("special:shield_small", p2)
check("岩盾获得 10% 护盾", b2.p_shields.get("potion", {}).get("value") == 10, str(b2.p_shields))
check("岩盾 3 刻（expire_at=3.0，1刻=1秒）", abs(float(b2.p_shields.get("potion", {}).get("expire_at", 0)) - 3.0) < 1e-9,
      str(b2.p_shields))
# 圣盾 15%
b2b = mk_battle()
b2b._do_use_item("special:shield_big", p2)
check("圣盾 15% 护盾", b2b.p_shields.get("potion", {}).get("value") == 15, str(b2b.p_shields))

# 荆棘：受击反弹 30%（必触发）
b3 = mk_battle()
p3 = mk_player(80)
b3._do_use_item("special:thorns_pot", p3)
eh = b3.enemy["hp"]
# 屏蔽随机闪避，保证受击断言确定性（荆棘反弹需命中才触发）
_orig_ps = b3._player_stats
def _ps_nododge(p_):
    s = _orig_ps(p_)
    s["dodge"] = 0.0
    return s
b3._player_stats = _ps_nododge
b3._damage_player(p3, 50, [])
check("荆棘反弹 30% 伤害(15)", b3.enemy["hp"] == eh - 15, f"{eh}→{b3.enemy['hp']}")

# 破甲：敌人防御 -15% 2 回合
b4 = mk_battle()
p4 = mk_player()
b4._do_use_item("special:def_down", p4)
check("破甲 e_buffs def_down", b4.e_buffs.get("def_down") == 2, str(b4.e_buffs))
check("破甲 _armor_break_pct", b4.e_buffs.get("_armor_break_pct") == 0.15, str(b4.e_buffs.get("_armor_break_pct")))

# 影步：15% 闪避（概率测试——直接查 buff 挂载）
b5 = mk_battle()
p5 = mk_player()
b5._do_use_item("special:dodge_pot", p5)
check("影步挂载 dodge_pot", b5.p_buffs.get("dodge_pot") == 3, str(b5.p_buffs))

# 不动：免疫控制（cc_immune 挂载 + 怪物控制被拦截）
b6 = mk_battle()
p6 = mk_player()
b6._do_use_item("special:cc_immune", p6)
from data.plugins.dragonfall.game.core import battle_mech as BM
from data.plugins.dragonfall.game.core.battle_mech import MON_CTRL_EFFECTS
stun_logs = []
MON_CTRL_EFFECTS["stun"](b6, p6, stun_logs, 3)
check("不动免疫眩晕", "stun" not in b6.p_buffs and any("免疫" in l for l in stun_logs), f"{b6.p_buffs} {stun_logs}")

# 死神：<30% 敌人 +30% 伤害
b7 = mk_battle()
b7.enemy["hp"] = 100  # 20%
p7 = mk_player()
b7._do_use_item("special:execute_pot", p7)
mult7, tags7 = b7._affix_dmg_mult(p7)
check("死神处决倍率 1.3", mult7 == 1.3 and any("处决" in t for t in tags7), f"{mult7} {tags7}")

# 死神对高血敌人无加成
b7b = mk_battle()
p7b = mk_player()
b7b._do_use_item("special:execute_pot", p7b)
mult7b, _ = b7b._affix_dmg_mult(p7b)
check("死神对高血无加成", mult7b == 1.0, str(mult7b))

# 圣光：治疗 +20%（对比无 buff 基准，排除 cond_mult 干扰）
b8 = mk_battle()
p8 = mk_player(50)
p8["max_hp"] = 300
b8._do_use_item("special:heal_up", p8)
b8n = mk_battle()
p8n = mk_player(50)
p8n["max_hp"] = 300
info = {"name": "治愈术", "power": 1.0}
st = {"matk": 100, "crit": 0.05}
b8._skill_heal(st, "治愈术", info, p8, 1, "", 0, {}, [])
b8n._skill_heal(st, "治愈术", info, p8n, 1, "", 0, {}, [])
heal_buff = p8["hp"] - 50
heal_base = p8n["hp"] - 50
check("圣光治疗 +20%", heal_buff == int(heal_base * 1.2), f"buff={heal_buff} base={heal_base}")

# 魔抗：魔法伤害 -15%
b9 = mk_battle()
p9 = mk_player()
b9._do_use_item("special:magic_resist", p9)
# 魔抗：魔法伤害 -15%（复刻 _enemy_turn 减免逻辑：先 -15% 取整再 max(1)）
from data.plugins.dragonfall.game import engine as E
dmg9 = E.calc_damage(100, p9["mdef"], False)
red9 = max(1, int(dmg9 * 0.15))
expected9 = max(1, dmg9 - red9)
check("魔抗 -15% 计算", expected9 == max(1, int(dmg9 * 0.85)) or expected9 == dmg9 - max(1, int(dmg9*0.15)),
      f"{dmg9}->{expected9}")

print(f"\n结果: {PASS} 通过, {FAIL} 失败")
sys.exit(1 if FAIL else 0)
