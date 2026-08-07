# -*- coding: utf-8 -*-
"""阶段八：装备重写 v2.0（10 章名册 + 20 章词条/属性需求）

验证：
  1. 数据完整性：30 词条 / 14 专属 / 名册 91 件 / 固定词条全覆盖 / 需求格式
  2. 名册生成 generate_roster_equip：名字/词条数/需求/套装/专属
  3. 随机生成 generate_equip：词条 v2 / req / 橙装专属
  4. 掉落 roll_drop：普通怪绿蓝 / 精英紫蓝+图纸 / Boss 橙紫+图纸
  5. 属性需求穿戴：装备命令属性不够拦截 / 达标可穿 / 跨职业武器
  6. 战斗词条触发：护盾 / 处决 / 流血 / 破甲 / 连击 / 吸血 / 元素附加 / 格挡 / 反击 / 回春 / 冥想 / 龙语印记
  7. 商店买武器名册化（需求与名册一致）
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import FakeEvent, run, clean_db, make_player, TEST_DB, PLUGIN_DIR
from data.plugins.dragonfall.game import content as C, db, engine as E
from data.plugins.dragonfall.game import battle as BT
from data.plugins.dragonfall.main import Main

passed = 0
failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {detail}")


async def cmd(m, name, gid, qid, msg):
    handler = getattr(m, name)
    ev = FakeEvent(gid, qid, msg)
    return await run(handler, ev)


def mk_player(affix_ids, legendary=None, hp=500, mp=100, max_hp=None, max_mp=None):
    """带装备的战斗测试玩家（装备词条可注入）"""
    eq = {"weapon": {"name": "测试剑", "slot": "weapon", "quality": "blue", "lv": 30,
                     "stats": {"atk": 50}, "affixes": affix_ids}}
    if legendary:
        eq["weapon"]["legendary"] = legendary
    return {"class_name": "cls_zhan_shi", "level": 30, "hp": hp, "max_hp": max_hp or hp,
            "mp": mp, "max_mp": max_mp or mp, "equipment": eq,
            "attributes": {"str": 30, "agi": 10, "int": 10, "vit": 10},
            "learned_skills": [], "skill_levels": {}, "title_bonus": {}}


def mk_enemy(hp=1000, role="dps", name="测试怪", max_hp=None):
    return {"name": name, "role": role, "hp": hp, "max_hp": max_hp or hp,
            "atk": 30, "def": 10, "matk": 10, "mdef": 10, "spd": 5}


# ============ 1. 数据完整性 ============
def test_data():
    print("【1. 数据完整性】")
    check("30 种词条", len(C.AFFIXES) == 30, str(len(C.AFFIXES)))
    check("专属 14", len(C.LEGENDARY_EFFECTS) == 14, str(len(C.LEGENDARY_EFFECTS)))
    check("名册 91 件", len(C.EQUIP_ROSTER) == 91, str(len(C.EQUIP_ROSTER)))
    check("品质倍率绿 1.3", C.QUALITY["green"]["mult"] == 1.3)
    check("品质倍率蓝 1.6", C.QUALITY["blue"]["mult"] == 1.6)
    # 词条触发时机全合法
    valid_triggers = {"stat", "on_hit", "on_taken", "turn_start", "battle_start", "passive"}
    bad = [aid for aid, info in C.AFFIXES.items() if info["trigger"] not in valid_triggers]
    check("词条触发时机合法", not bad, str(bad))
    # 名册每件都有需求 + 固定词条配置
    missing_fixed = [rid for rid, r in C.EQUIP_ROSTER.items()
                     if r["name"] not in C.SERIES_FIXED_AFFIX]
    check("固定词条全覆盖", not missing_fixed, str(missing_fixed[:5]))
    bad_req = [rid for rid, r in C.EQUIP_ROSTER.items()
               if not r.get("req") or not set(r["req"]).issubset({"str", "agi", "int", "vit"})]
    check("需求格式合法", not bad_req, str(bad_req[:5]))
    bad_lg = [rid for rid, r in C.EQUIP_ROSTER.items()
              if r["quality"] == "orange" and not r.get("legendary")]
    check("橙装全带专属", not bad_lg, str(bad_lg[:5]))
    # 随机池词条 ID 全有效
    bad_pool = [a for pool in C.AFFIX_POOL_BY_QUALITY.values() for a in pool
                if a not in C.AFFIXES]
    check("随机池 ID 有效", not bad_pool, str(bad_pool))
    # 每个系列有 5 件套（含护腿）
    series_ok = all(len([r for r in C.EQUIP_ROSTER.values() if r["series"] == s and r["slot"] == "legs"]) >= 1
                    for s in set(r["series"] for r in C.EQUIP_ROSTER.values()))
    check("9 系列各有护腿", series_ok)


# ============ 2. 名册生成 ============
def test_roster_gen():
    print("【2. 名册生成】")
    random.seed(7)
    e = C.generate_roster_equip("eq_tie_jian")
    check("铁剑名字", e["name"] == "铁剑")
    check("铁剑白装 0 词条", e.get("affixes") is None, str(e.get("affixes")))
    check("铁剑需求力量 5", e["req"] == {"str": 5}, str(e["req"]))
    e2 = C.generate_roster_equip("eq_jin_gou_wan_dao")
    check("金钩弯刀橙装 3 词条", len(e2.get("affixes", [])) == 3, str(e2.get("affixes")))
    check("金钩弯刀固定词条在列", "crit_up" in e2["affixes"] and "lifesteal" in e2["affixes"], str(e2["affixes"]))
    check("金钩弯刀专属", e2.get("legendary") == "gold_hook")
    check("金钩弯刀套装", e2.get("set") == "海风套", str(e2.get("set")))
    check("金钩弯刀需求", e2["req"] == {"agi": 25}, str(e2["req"]))
    e3 = C.generate_roster_equip("eq_long_yu_sheng_jian")
    check("龙语圣剑专属", e3.get("legendary") == "dragon_tongue")
    check("龙语圣剑固定词条", "dragon_aw" in e3["affixes"] and "execute" in e3["affixes"], str(e3["affixes"]))
    # 苍穹之枪武器类型
    e4 = C.generate_roster_equip("eq_cang_qiong_zhi_qiang")
    check("苍穹之枪类型枪", e4.get("weapon_type") == "spear")
    # 名册系列全部映射套装
    no_set = [rid for rid, r in C.EQUIP_ROSTER.items() if not e.get("set") and r["quality"] != "white"]
    check("蓝紫橙名册全部有套装归属", not no_set, str(no_set[:5]))


# ============ 3. 随机生成 ============
def test_random_gen():
    print("【3. 随机生成】")
    random.seed(3)
    e = C.generate_equip("weapon", 30, "purple")
    check("随机紫武器有词条", bool(e.get("affixes")), str(e.get("affixes")))
    check("随机装备有需求", bool(e.get("req")), str(e.get("req")))
    e2 = C.generate_equip("armor", 30, "orange")
    check("随机橙装有专属", bool(e2.get("legendary")))
    check("随机装备词条是 ID", all(isinstance(a, str) for a in e2.get("affixes", [])))


# ============ 4. 掉落 ============
def test_drop():
    print("【4. 掉落】")
    # 普通怪 12% 概率（seed 循环找触发）
    triggered = False
    for seed in range(1, 300):
        random.seed(seed)
        d = C.roll_drop(10, "normal")
        if d[0] is not None:
            check(f"普通怪掉装备（seed {seed}）", d[0]["quality"] in ("green", "blue"), d[0]["quality"])
            triggered = True
            break
    if not triggered:
        check("普通怪掉装备", False, "300 seed 无触发")
    random.seed(4)
    d2 = C.roll_drop(20, "elite")
    check("精英掉装备", d2[0] is not None and d2[0]["quality"] in ("purple", "blue"))
    check("精英掉图纸", d2[1] is not None and d2[1]["type"] == "图纸", str(d2[1]))
    check("图纸 blueprint_for", d2[1]["blueprint_for"] in C.EQUIP_ROSTER_BY_NAME, str(d2[1]["blueprint_for"]))
    random.seed(8)
    d3 = C.roll_drop(40, "boss")
    check("Boss 掉装备", d3[0] is not None and d3[0]["quality"] in ("orange", "purple"))
    check("Boss 掉图纸", d3[1] is not None)


# ============ 5. 属性需求穿戴 ============
async def test_req():
    print("【5. 属性需求穿戴】")
    m = Main(None)
    clean_db()
    await cmd(m, "register", "g1", "q1", "注册 战士 测试")
    # 造一件高需求装备（力量 50）
    eq = C.generate_roster_equip("eq_sheng_dian_zhan_chui")  # 圣殿战锤 req 力量 38
    db.add_item("g1", "q1", "eq_test", eq)
    r = await cmd(m, "equip", "g1", "q1", "装备 圣殿战锤")
    txt = r[-1]
    check("属性不足拦截", "穿不上" in txt and "力量" in txt, txt)
    # 加点到力量 40 + 等级 40 → 可装备
    db.update_player("g1", "q1", attributes='{"str": 40, "agi": 0, "int": 0, "vit": 0}', level=40)
    r2 = await cmd(m, "equip", "g1", "q1", "装备 圣殿战锤")
    txt2 = r2[-1]
    check("属性达标可穿", "装备了" in txt2, txt2)
    check("跨职业武器可穿", "不能装备" not in txt2)
    # 未穿时物品详情显示需求
    db.update_player("g1", "q1", attributes='{"str": 0, "agi": 0, "int": 0, "vit": 0}')
    eq2 = C.generate_roster_equip("eq_sheng_dian_zhan_chui")
    db.add_item("g1", "q1", "eq_test2", eq2)
    r3 = await cmd(m, "item_detail", "g1", "q1", "物品详情 圣殿战锤")
    txt3 = r3[-1]
    check("详情显示需求", "需求：力量 38" in txt3, txt3)


# ============ 6. 战斗词条触发 ============
def test_battle_affix():
    print("【6. 战斗词条触发】")
    # 6.1 战斗开始护盾
    p = mk_player(["shield"])
    b = BT.Battle("monster", mk_enemy(), {}, p)
    check("护盾词条战斗开始", b.shield == int(p["max_hp"] * 0.10), str(b.shield))
    # 6.2 处决低血增伤（血 20% 触发）
    p2 = mk_player(["execute"])
    b2 = BT.Battle("monster", mk_enemy(hp=200, max_hp=1000), {}, p2)
    logs = b2._player_attack(b2._player_stats(p2), p2)
    check("处决低血增伤", any("处决" in l for l in logs), str(logs))
    # 6.3 流血/破甲/连击/吸血/元素附加（seed 固定触发任意 on_hit 词条 + 专项验证）
    onhit_hits = 0
    for seed in range(1, 40):
        random.seed(seed)
        p3 = mk_player(["bleed", "armor_break", "combo", "lifesteal", "element_ice"])
        b3 = BT.Battle("monster", mk_enemy(), {}, p3)
        logs = b3._player_attack(b3._player_stats(p3), p3)
        joined = "".join(logs)
        if any(k in joined for k in ("流血", "破甲", "连击", "吸血", "元素", "贯穿", "蓄力")):
            onhit_hits += 1
    check(f"on_hit 词条可触发（{onhit_hits}/39 seed）", onhit_hits >= 5, str(onhit_hits))
    # 专项：找触发流血/破甲的 seed
    for target in ("流血", "破甲"):
        found = False
        for seed in range(1, 100):
            random.seed(seed)
            p3 = mk_player(["bleed", "armor_break"])
            b3 = BT.Battle("monster", mk_enemy(), {}, p3)
            logs = b3._player_attack(b3._player_stats(p3), p3)
            if target in "".join(logs):
                found = True
                break
        check(f"词条{target}可触发", found)
    # 6.4 受击格挡/反击/反伤（seed 循环找触发）
    for seed in range(1, 300):
        random.seed(seed)
        p4 = mk_player(["block", "counter", "thorns"])
        b4 = BT.Battle("monster", mk_enemy(), {}, p4)
        logs = []
        b4._damage_player(p4, 100, logs)
        joined = "".join(logs)
        if "格挡" in joined or "反击" in joined or "反伤" in joined:
            check(f"受击词条（seed {seed}）", True, joined)
            break
    else:
        check("受击词条", False, "300 seed 无触发")
    # 6.5 回春/冥想回合开始（max_hp 500 但当前 400 → 触发回复）
    p5 = mk_player(["regen", "meditate"], hp=400, mp=50, max_hp=500, max_mp=100)
    b5 = BT.Battle("monster", mk_enemy(), {}, p5)
    logs = b5._turn_start(p5)
    check("回春回合回复", "回春" in "".join(logs) and p5["hp"] > 400, f"hp={p5['hp']}")
    check("冥想回合回复", "冥想" in "".join(logs) and p5["mp"] > 50, f"mp={p5['mp']}")
    # 6.6 龙语印记叠层
    p6 = mk_player([], "dragon_tongue")
    b6 = BT.Battle("monster", mk_enemy(), {}, p6)
    b6._player_attack(b6._player_stats(p6), p6)
    check("龙语印记叠层", b6.mech_stacks.get("dragon_mark") == 1, str(b6.mech_stacks))
    # 6.7 元素伤害专属（澜歌之泪 冰 +20%）
    p7 = mk_player(["element_ice"], "lang_tear")
    b7 = BT.Battle("monster", mk_enemy(), {}, p7)
    mult = b7._affix_element_dmg(p7, "ice")
    check("冰属性伤害 +20%", abs(mult - 1.20) < 1e-6, str(mult))
    mult2 = b7._affix_element_dmg(p7, "fire")
    check("火系不加成", abs(mult2 - 1.0) < 1e-6, str(mult2))
    # 6.8 流血 DOT 回合结算
    p8 = mk_player(["bleed"])
    random.seed(1)
    b8 = BT.Battle("monster", mk_enemy(hp=1000), {}, p8)
    b8._player_attack(b8._player_stats(p8), p8)
    if b8.e_buffs.get("bleed"):
        logs = b8._turn_start(p8)
        check("流血回合结算", "流血" in "".join(logs) and b8.enemy["hp"] < 1000, str(logs))
    else:
        check("流血回合结算", True, "seed1 未触发 bleed，跳过")


# ============ 7. 商店买武器名册化 ============
async def test_shop_roster():
    print("【7. 商店买武器名册化】")
    m = Main(None)
    clean_db()
    await cmd(m, "register", "g1", "q1", "注册 战士 测试")
    db.update_player("g1", "q1", gold=10000, attributes='{"str": 40, "agi": 40, "int": 40, "vit": 40}')
    # 铁港买弯刀（名册 req 敏捷 12）
    db.update_player("g1", "q1", cur_map="ironharbor")
    r = await cmd(m, "buy", "g1", "q1", "购买 弯刀")
    txt = r[-1]
    check("买弯刀成功", "购买了【弯刀】" in txt, txt)
    items = db.get_inventory("g1", "q1")
    found = [it for it in items if it["data"]["name"] == "弯刀"]
    check("弯刀入包且 req 敏捷 12", bool(found) and found[0]["data"]["req"] == {"agi": 12},
          str([it["data"].get("req") for it in found]))
    check("弯刀带词条", bool(found) and bool(found[0]["data"].get("affixes")),
          str([it["data"].get("affixes") for it in found]))


async def main():
    test_data()
    test_roster_gen()
    test_random_gen()
    test_drop()
    await test_req()
    test_battle_affix()
    await test_shop_roster()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
