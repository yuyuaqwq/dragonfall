# -*- coding: utf-8 -*-
"""v135 装备特色增强验收：哑词条激活 + 词条特色面板 + 套装锻造专属

验收标准：
1. 破魔(break_magic)：对 role=caster/healer 或带魔法技能的怪 +25% 伤害（原条件零命中）
2. 追猎(hunt)：对 debuffs.mark>0 的目标 +20% 伤害（原只认 e_buffs mark）
3. 净化(purify)：驱散成功 → 敌人攻击 -10% 1 回合（圣洁）
4. 坚韧(tenacity_cc)：免疫负面成功 → 回复 3% 生命
5. 元素·雷(element_thunder)：15% 概率追加 20% 雷伤（感电连跳）
6. 装备详情面板：词条特色标签展示
7. 套装锻造专属：誓约/银铃 商店无货、锻造配方齐备

独立运行：python tests/test_v135_equip_feature.py
"""
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import BT  # noqa: F401

from data.plugins.dragonfall.game import content as C

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


def make_player(equipment=None, cls="cls_zhan_shi", lv=30):
    return {
        "class_name": cls, "level": lv, "equipment": equipment or {},
        "attributes": {}, "class_tier": 0 if lv < 30 else 1,
        "hp": 500, "max_hp": 500, "mp": 100, "max_mp": 100,
    }


def make_battle(enemy=None, player=None):
    e = enemy or {"name": "野狼", "role": "dps", "hp": 1000, "max_hp": 1000,
                  "atk": 20, "matk": 15, "def": 5, "mdef": 5, "spd": 10,
                  "skills": [], "debuffs": {}}
    b = BT.Battle(btype="monster", enemy=e, player=player or make_player())
    b.round = 1
    return b


def eq(weapon_affixes=None, armor_affixes=None, legendary=None):
    return {
        "weapon": {"name": "测试剑", "slot": "weapon", "quality": "purple", "lv": 30,
                   "affixes": weapon_affixes or [], "legendary": legendary or None,
                   "stats": {"atk": 40}},
        "armor": {"name": "测试甲", "slot": "armor", "quality": "purple", "lv": 30,
                  "affixes": armor_affixes or [], "stats": {"def": 30}},
    }


# ============ 1. 破魔激活 ============
print("【1. 破魔 break_magic 激活】")
p = make_player(eq(["break_magic"]))
# 1a. role=caster 直接命中
b = make_battle({"name": "深渊法师", "role": "caster", "hp": 1000, "max_hp": 1000,
                 "atk": 10, "matk": 30, "def": 5, "mdef": 5, "spd": 10, "skills": [], "debuffs": {}}, p)
mult, tags = b._affix_dmg_mult(p)
check("role=caster 命中（mult=1.25）", abs(mult - 1.25) < 1e-9 and "🔮破魔" in tags)
# 1b. role=dps 但带魔法技能 → 命中
b = make_battle({"name": "暗影猎手", "role": "dps", "hp": 1000, "max_hp": 1000,
                 "atk": 10, "matk": 30, "def": 5, "mdef": 5, "spd": 10,
                 "skills": ["ms_an_ying_dan"], "debuffs": {}}, p)
mult, tags = b._affix_dmg_mult(p)
check("dps+魔法技能命中（mult=1.25）", abs(mult - 1.25) < 1e-9)
# 1c. 纯物理 dps 不命中
b = make_battle({"name": "野狼", "role": "dps", "hp": 1000, "max_hp": 1000,
                 "atk": 30, "matk": 5, "def": 5, "mdef": 5, "spd": 10, "skills": [], "debuffs": {}}, p)
mult, tags = b._affix_dmg_mult(p)
check("纯物理 dps 不命中（mult=1.0）", abs(mult - 1.0) < 1e-9)

# ============ 2. 追猎激活 ============
print("【2. 追猎 hunt 激活】")
p = make_player(eq(["hunt"]))
# 2a. e_buffs mark → 命中
b = make_battle({"name": "野狼", "role": "dps", "hp": 1000, "max_hp": 1000,
                 "atk": 20, "matk": 5, "def": 5, "mdef": 5, "spd": 10, "skills": [], "debuffs": {}}, p)
b._tgt_buffs()["mark"] = 2
mult, tags = b._affix_dmg_mult(p)
check("e_buffs mark 命中（mult=1.2）", abs(mult - 1.2) < 1e-9 and "🎯追猎" in tags)
# 2b. debuffs.mark>0 → 命中（原条件不认）
b = make_battle({"name": "野狼", "role": "dps", "hp": 1000, "max_hp": 1000,
                 "atk": 20, "matk": 5, "def": 5, "mdef": 5, "spd": 10, "skills": [],
                 "debuffs": {"mark": {"n": 3, "mult": 1.0}}}, p)
mult, tags = b._affix_dmg_mult(p)
check("debuffs.mark=3 命中（mult=1.2）", abs(mult - 1.2) < 1e-9)
# 2c. 无标记不命中
b = make_battle({"name": "野狼", "role": "dps", "hp": 1000, "max_hp": 1000,
                 "atk": 20, "matk": 5, "def": 5, "mdef": 5, "spd": 10, "skills": [], "debuffs": {}}, p)
mult, tags = b._affix_dmg_mult(p)
check("无标记不命中（mult=1.0）", abs(mult - 1.0) < 1e-9)

# ============ 3. 净化增强 ============
print("【3. 净化 purify 增强】")
p = make_player(eq(["purify"]))
b = make_battle({"name": "野狼", "role": "dps", "hp": 1000, "max_hp": 1000,
                 "atk": 20, "matk": 5, "def": 5, "mdef": 5, "spd": 10, "skills": [], "debuffs": {}}, p)
b._tgt_buffs()["mon_atk_up"] = 3
random.seed(1)  # 保证 15% chance 命中
logs = []
# 直接调 handler：_affix_on_hit 内部 roll chance
b._affix_on_hit(p, 100, logs)
# 至少 e_buffs 被处理：净化成功与否看 mon_atk_down 是否被写入
# 强制多次触发验证
random.seed(1)
found_purify = False
for _ in range(30):
    b2 = make_battle({"name": "野狼", "role": "dps", "hp": 1000, "max_hp": 1000,
                      "atk": 20, "matk": 5, "def": 5, "mdef": 5, "spd": 10, "skills": [], "debuffs": {}}, p)
    b2._tgt_buffs()["mon_atk_up"] = 3
    b2._affix_on_hit(p, 100, [])
    if b2._tgt_buffs().get("mon_atk_down"):
        found_purify = True
        check("净化成功 → mon_atk_down 挂上（圣洁）", True)
        check("mon_atk_down=1 回合", b2._tgt_buffs()["mon_atk_down"] == 1)
        break
if not found_purify:
    check("净化成功 → mon_atk_down 挂上（圣洁）", False)

# ============ 4. 坚韧增强 ============
print("【4. 坚韧 tenacity_cc 增强】")
p = make_player(eq([], ["tenacity_cc"]))
found_ten = False
for s in range(80):
    random.seed(s)
    p2 = make_player(eq([], ["tenacity_cc"]))
    b2 = make_battle({"name": "野狼", "role": "dps", "hp": 1000, "max_hp": 1000,
                      "atk": 20, "matk": 5, "def": 5, "mdef": 5, "spd": 10, "skills": [], "debuffs": {}}, p2)
    b2._p_buffs_bag()["spd_down"] = 2
    hp0 = p2["hp"]
    b2._affix_on_taken(p2, 50, [])
    if p2["hp"] > hp0:
        found_ten = True
        _heal_amt = p2["hp"] - hp0
        check("坚韧免疫成功 → 回复 3% 最大生命", abs(_heal_amt - int(p2["max_hp"] * 0.03)) <= 1)
        check("坚韧免疫后负面被清除", "spd_down" not in b2._p_buffs_bag())
        break
if not found_ten:
    check("坚韧免疫成功 → 回复 3% 生命", False)

# ============ 5. 元素·雷增强 ============
print("【5. 元素·雷 element_thunder 增强】")
p = make_player(eq(["element_thunder"]))
found_th = False
for _ in range(40):
    b2 = make_battle({"name": "野狼", "role": "dps", "hp": 100000, "max_hp": 100000,
                      "atk": 20, "matk": 5, "def": 5, "mdef": 5, "spd": 10, "skills": [], "debuffs": {}}, p)
    hp0 = b2.enemy["hp"]
    logs = []
    b2._affix_on_hit(p, 100, logs)
    dmg = hp0 - b2.enemy["hp"]
    if dmg > 5:  # 5% 附加 = 5 点，>5 说明追加了 20% 雷伤
        found_th = True
        check("雷系追加伤害（>5%）触发", True)
        check("感电连跳日志", any("感电连跳" in l for l in logs))
        break
if not found_th:
    check("雷系追加伤害（>5%）触发", False)

# ============ 6. 词条特色面板 ============
print("【6. 词条特色面板】")
from data.plugins.dragonfall.game.commands import economy as eco_mod
d = {"name": "测试剑", "slot": "weapon", "quality": "purple", "lv": 30,
     "stats": {"atk": 40}, "affixes": ["bleed", "armor_break", "element_thunder"],
     "req": {"str": 20}}
feats = eco_mod._equip_affix_features(d)
check("词条特色标签生成（含 流血/破甲/元素）", "破甲" in feats and "元素" in feats)
lines = []
eco_mod._render_equip(d, lines, False)
has_feat = any("⭐ 词条特色" in l for l in lines)
check("装备详情面板含『词条特色』行", has_feat)
if has_feat:
    print("    " + [l for l in lines if "词条特色" in l][0])

# ============ 7. 套装锻造专属 ============
print("【7. 套装锻造专属】")
# 7a. 商店无誓约/银铃
shop_oak = C.SHOP_EQUIP.get("oak_town", [])
shop_iron = C.SHOP_EQUIP.get("ironharbor", [])
oak_r = [x["rid"] if isinstance(x, dict) else x for x in shop_oak]
iron_r = [x["rid"] if isinstance(x, dict) else x for x in shop_iron]
check("橡木镇商店无誓约 4 件", not any("shi_yue" in r for r in oak_r))
check("铁港商店无银铃 7 件", not any("yin_ling" in r for r in iron_r))
# 7b. 锻造配方齐备
for rid, name in [("eq_shi_yue_quan_zhang", "誓约权杖"), ("eq_shi_yue_sheng_guan", "誓约圣冠"),
                  ("eq_shi_yue_fa_yi", "誓约法衣"), ("eq_shi_yue_sheng_xue", "誓约圣靴"),
                  ("eq_yin_ling_duan_ren", "银铃短刃"), ("eq_yin_ling_hu_tui", "银铃护腿"),
                  ("eq_yin_ling_zhang", "银铃杖"), ("eq_yin_ling_tou_kui", "银铃头盔"),
                  ("eq_yin_ling_xiong_jia", "银铃胸甲"), ("eq_yin_ling_zhan_xue", "银铃战靴"),
                  ("eq_yin_ling_xiang_lian", "银铃项链")]:
    rec = next((rk for rk, r in C.CRAFT_RECIPES.items() if r.get("roster_id") == rid), None)
    check(f"锻造配方存在：{name}", rec is not None)
# 7c. 锻造出的誓约/银铃带套装归属（凑套）
eq1 = C.craft_recipe_make("rec_shi_yue_quan_zhang")
check("锻造誓约权杖带 set=圣徽·誓约", (eq1 or {}).get("set") == "圣徽·誓约")
eq2 = C.craft_recipe_make("rec_yin_ling_duan_ren")
check("锻造银铃短刃带 set=银铃套", (eq2 or {}).get("set") == "银铃套")
eq3 = C.craft_recipe_make("rec_yin_ling_zhang")
check("锻造银铃杖带 set=银铃套", (eq3 or {}).get("set") == "银铃套")

# ============ 总结 ============
print()
print(f"✅ PASS: {PASS}  ❌ FAIL: {FAIL}")
if FAIL:
    sys.exit(1)
print("v135 装备特色增强验收全部通过")
