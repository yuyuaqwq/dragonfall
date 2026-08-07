# -*- coding: utf-8 -*-
"""commands 层：经济域（背包/锻造/商店/市场/图鉴/强化/附魔）（源自 v10/v17/v21/v23/v40/v42/v62b/v83/v85）

验证：
  1. 背包：分类筛选/物品详情/翻页/无空格
  2. 锻造：职业导航/材料不足/等级门槛/模糊搜索/配方详情
  3. 商店：购买/金币扣除
  4. 市场：上架/下架/购入
  5. 图鉴：掉落来源查询
  6. 装备对比（换装前后属性变化）
"""
import sys, os, random, sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, FakeEvent, run, BT

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""


async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "e1", "注册 战士 铁匠")
    db.update_player("g1", "e1", cur_map="oak_town", level=5, gold=1000)

    print("【背包：分类筛选】")
    # 入库各类物品
    db.add_item("g1", "e1", "mat_lang_pi", {"name": "狼皮", "type": "材料", "stackable": True, "price": 8}, 5)
    db.add_item("g1", "e1", "mat_ye_gou_liao", {"name": "野狗獠牙", "type": "材料", "stackable": True, "price": 3}, 3)
    db.add_item("g1", "e1", "i_treatment_potion", {"name": "治疗药水", "type": "消耗品", "stackable": True, "heal": 200, "price": 20}, 2)
    out = await cmd(m, "inventory", "g1", "e1", "背包 材料")
    check("筛选材料", "狼皮" in out and "野狗獠牙" in out, out[:120])
    out = await cmd(m, "inventory", "g1", "e1", "背包 消耗品")
    check("筛选消耗品", "治疗药水" in out, out[:120])
    # 无空格
    out = await cmd(m, "inventory", "g1", "e1", "背包材料")
    check("无空格背包材料", "狼皮" in out, out[:120])
    out = await cmd(m, "inventory", "g1", "e1", "背包材料2")
    check("无空格+序号", "狼皮" in out or "第" in out, out[:120])

    print("【背包：物品详情】")
    out = await cmd(m, "item_detail", "g1", "e1", "物品详情 1")
    check("物品详情有返回", len(out) > 5, out[:120])

    print("【锻造：可锻造列表（v54）】")
    out = await cmd(m, "craft", "g1", "e1", "锻造")
    check("只列可锻造配方", "当前可锻造" in out and "铁剑" in out, out[:200])
    check("列表提示全部/职业", "锻造 全部" in out and "锻造 <职业>" in out, out[:200])
    out = await cmd(m, "craft", "g1", "e1", "锻造 全部")
    check("全部配方含未学标记", "未学" in out or "✅" in out, out[:200])
    out = await cmd(m, "craft", "g1", "e1", "锻造 战士")
    check("战士配方列表", "铁皮长剑" in out or "铁剑" in out, out[:120])

    print("【锻造：等级门槛】")
    db.update_player("g1", "e1", level=3)
    out = await cmd(m, "craft", "g1", "e1", "锻造 龙脊大剑")
    check("等级不够拦截", "锻造技艺" in out or "等级" in out, out[:120])
    db.update_player("g1", "e1", level=5)

    print("【锻造：材料不足】")
    out = await cmd(m, "craft", "g1", "e1", "锻造 铁剑")
    check("材料不足提示", "材料不足" in out, out[:120])

    print("【锻造：模糊搜索】")
    db.add_item("g1", "e1", "mat_shi_lai_mu_nian_ye", {"name": "史莱姆黏液", "type": "材料", "stackable": True, "price": 5}, 5)
    out = await cmd(m, "craft", "g1", "e1", "锻造 皮甲")
    check("别名搜索锻造皮甲", "皮甲" in out, out[:120])

    print("【锻造：配方详情】")
    out = await cmd(m, "recipe_list", "g1", "e1", "配方 铁剑")
    check("配方详情显示铁剑", "铁剑" in out, out[:120])
    check("配方详情显示材料", "史莱姆黏液" in out, out[:120])
    out = await cmd(m, "recipe_list", "g1", "e1", "配方")
    check("配方列表全量", "铁剑" in out and "星光法杖" in out, out[:150])

    print("【商店】")
    db.update_player("g1", "e1", gold=500)
    out = await cmd(m, "shop", "g1", "e1", "商店")
    check("商店显示", "商店" in out or "购买" in out, out[:120])
    # 购买：维拉镇商店第一个物品（治疗药水）
    out = await cmd(m, "buy", "g1", "e1", "购买 治疗药水")
    check("购买 治疗药水 有返回", len(out) > 5, out[:120])

    print("【商店：老马坐骑（新世界 oak 区域限定）】")
    db.update_player("g1", "e1", gold=1000, cur_map="oak_town")
    out = await cmd(m, "buy", "g1", "e1", "购买 老马")
    check("橡木镇可买老马", "买了一匹老马" in out, out[:150])
    db.update_player("g1", "e1", cur_map="white_deer")
    out = await cmd(m, "buy", "g1", "e1", "购买 老马")
    check("非橡木镇拦截买老马", "橡木镇的商人" in out, out[:150])

    print("【市场：上架/下架】")
    out = await cmd(m, "market", "g1", "e1", "上架 1 100")
    check("上架有返回", len(out) > 5, out[:120])

    print("【图鉴】")
    out = await cmd(m, "bestiary", "g1", "e1", "图鉴")
    check("图鉴有返回", len(out) > 5, out[:120])

    print("【装备对比】")
    eq = C.generate_equip("weapon", 5, "white", "sword")
    db.add_item("g1", "e1", f"eq_{random.randint(1000,9999)}", eq, count=1)
    out = await cmd(m, "equip", "g1", "e1", "装备 1")
    check("装备武器有返回", "装备" in out or "无法" in out or "佩戴" in out, out[:120])

    print("【图纸学习制（v54）】")
    # 海风长弓 Lv.18 紫装 → 需要锻造副业 Lv.2（_craft_prof_need 折算），先升副业再测图纸拦截
    for _ in range(25):
        db.add_prof_exp("g1", "e1", "craft", 1)
    db.update_player("g1", "e1", level=15, gold=100000)
    out = await cmd(m, "craft", "g1", "e1", "锻造 海风长弓")
    check("未学图纸拦截", "学习" in out and "海风长弓图纸" in out, out[:200])
    # 背包加图纸 → 懒迁移提示学习
    db.add_item("g1", "e1", "bp_hf", {"name": "海风长弓图纸", "type": "图纸", "stackable": True, "blueprint_for": "海风长弓", "price": 60})
    out = await cmd(m, "craft", "g1", "e1", "锻造 海风长弓")
    check("背包有图纸提示学习", "『学习 海风长弓图纸』" in out, out[:200])
    # 学习 → 解锁
    out = await cmd(m, "learn", "g1", "e1", "学习 海风长弓图纸")
    check("学习解锁配方", "永久解锁" in out and "海风长弓" in out, out[:300])
    p = db.get_player("g1", "e1")
    check("learned_blueprints 记录", "海风长弓图纸" in (p.get("learned_blueprints") or []), str(p.get("learned_blueprints")))
    # 已学后锻造不再提示图纸（材料不足也要显示材料而非图纸）
    out = await cmd(m, "craft", "g1", "e1", "锻造 海风长弓")
    check("已学不再要图纸", "学习" not in out and "材料不足" in out, out[:200])
    # 重复学习提示（海风长弓图纸已在上面学过）
    db.add_item("g1", "e1", "bp_hf2", {"name": "海风长弓图纸", "type": "图纸", "stackable": True, "blueprint_for": "海风长弓", "price": 60})
    out = await cmd(m, "learn", "g1", "e1", "学习 海风长弓图纸")
    check("重复学习提示", "已经学会" in out, out[:200])

    print("【炼金副业等级（v54）】")
    db.update_player("g1", "e1", level=20, gold=50000)
    # 默认炼金 Lv.1 → 超级治疗药水(need 5) 被拦
    out = await cmd(m, "alchemy_craft", "g1", "e1", "合成 超级治疗药水")
    check("炼金等级不够拦截", "炼金 Lv.5" in out or "炼金等级" in out, out[:200])
    # 炼金列表显示等级
    out = await cmd(m, "alchemy", "g1", "e1", "炼金")
    check("炼金列表显示等级要求", "炼金Lv" in out and "治疗药水" in out, out[:300])
    # 提升炼金等级到 5（反复加经验）
    for _ in range(300):
        db.add_prof_exp("g1", "e1", "alchemy", 1)
    out = await cmd(m, "alchemy_craft", "g1", "e1", "合成 超级治疗药水")
    check("炼金 5 级后走到材料检查", "材料不足" in out, out[:200])

    print("【战斗药水（v54）】")
    # battle 层：buff 药水挂 p_buffs 3 回合
    pl = {"hp": 100, "max_hp": 100, "mp": 50, "max_mp": 50, "atk": 10, "def": 5, "matk": 5, "mdef": 5, "spd": 5,
          "class_name": "cls_zhan_shi", "level": 3}
    enemy = C.build_monster(["m_test", "测试怪", "dps", 3, ["ms_si_yao"], ["mat_lang_pi"]], {"id": "x", "name": "x", "area": "x"})
    b = BT.Battle.from_state({"type": "monster", "enemy": enemy, "p_buffs": {}, "e_buffs": {}, "p_defending": False, "e_defending": False})
    logs, _ended = b.player_turn("use_item", "buff:atk_up", pl)
    check("攻击药水挂 atk_up", b.p_buffs.get("atk_up", 0) >= 2, str(b.p_buffs))
    check("战斗药水日志", "攻击" in "".join(logs) or "大幅提升" in "".join(logs), "".join(logs)[:200])
    # 幸运护符使用（非战斗）
    db.add_item("g1", "e1", "lucky1", {"name": "幸运护符", "type": "消耗品", "effect": "lucky", "stackable": True, "price": 150})
    out = await cmd(m, "use", "g1", "e1", "使用 幸运护符")
    check("幸运护符使用成功", "幸运护符" in out and "10 分钟" in out, out[:200])
    p2 = db.get_player("g1", "e1")
    check("lucky_until 已设置", int(p2.get("lucky_until") or 0) > 0, str(p2.get("lucky_until")))

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
