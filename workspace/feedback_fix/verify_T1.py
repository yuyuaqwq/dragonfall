# -*- coding: utf-8 -*-
"""T1 意见#2（zerc：『购买物品*数量』）：星号批量购买 + 数量校验显式报错。

用法：python workspace/feedback_fix/verify_T1.py
覆盖：
  1. 单件购买不受影响（购买 <名称> → ×1 回显，扣 1 倍价）
  2. 星号批量：『购买 治疗药水(小)*5』 → ×5 回显 / 背包 5 瓶 / 扣 5 倍价
  3. 空格批量回归（v95.25 #127 既有行为）：『购买 治疗药水(中) 4』 → ×4
  4. 序号+星号：『购买 1*3』 → ×3（white_deer_6 序号1=治疗药水(小)，堆叠合并 +3）
  5. 数量 0 / 负数（空格与星号两种写法）→ 友好报错，不扣钱不入包
  6. 非数字（治疗药水*abc / 尾部空 *）→ 数量格式不对
  7. 超上限（*1000 > buy_qty_max=999）→ 单次最多 999 提示
  8. 金币不足 → 报错，金币不为负、不入包
  9. 『购买 *5』无商品名 → 格式提示，防空名静默买第一件
  10. 武器带数量 → 只能单件提示（单件商品保护未被破坏），不扣钱
"""
import sys, os
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\tests")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from conftest import C, db, clean_db, Main, FakeEvent, run

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {str(detail)[:300]}")

async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""

def item_id(name):
    for iid, it in C.ITEMS.items():
        if it.get("name") == name:
            return iid
    return None

def inv_count(g, q, name):
    return sum(i["count"] for i in db.get_inventory(g, q)
               if i["data"].get("name") == name)

async def main():
    clean_db()
    m = Main(None)
    g, q = "g1", "buyer1"
    await cmd(m, "register", g, q, "注册 战士 批量买家 男")
    db.update_player(g, q, gold=50000, cur_map="white_deer", cur_subarea="white_deer_6")

    iid_small = item_id("治疗药水(小)")
    iid_mid = item_id("治疗药水(中)")
    price_small = int(C.ITEMS[iid_small]["price"])
    price_mid = int(C.ITEMS[iid_mid]["price"])
    print(f"  价格: 小={price_small} 中={price_mid}  buy_qty_max={C.ECON_CONFIG['buy_qty_max']}")

    print("【1. 单件购买不受影响】")
    out = await cmd(m, "buy", g, q, "购买 治疗药水(小)")
    check("1a 回显 ×1", "×1" in out, out[:200])
    check("1b 背包 1 瓶", inv_count(g, q, "治疗药水(小)") == 1, inv_count(g, q, "治疗药水(小)"))
    p = db.get_player(g, q)
    check("1c 扣 1 倍价", p["gold"] == 50000 - price_small, f"gold={p['gold']}")

    print("【2. 星号批量 购买 治疗药水(小)*5】")
    out = await cmd(m, "buy", g, q, "购买 治疗药水(小)*5")
    check("2a 回显 ×5", "×5" in out, out[:200])
    check("2b 背包累计 6 瓶", inv_count(g, q, "治疗药水(小)") == 6, inv_count(g, q, "治疗药水(小)"))
    p = db.get_player(g, q)
    check("2c 累计扣 6 倍价", p["gold"] == 50000 - 6 * price_small, f"gold={p['gold']}")

    print("【3. 空格批量回归 购买 治疗药水(中) 4】")
    out = await cmd(m, "buy", g, q, "购买 治疗药水(中) 4")
    check("3a 回显 ×4", "×4" in out, out[:200])
    check("3b 背包 4 瓶", inv_count(g, q, "治疗药水(中)") == 4, inv_count(g, q, "治疗药水(中)"))
    p = db.get_player(g, q)
    check("3c 扣 4 倍价", p["gold"] == 50000 - 6 * price_small - 4 * price_mid, f"gold={p['gold']}")

    print("【4. 序号+星号 购买 1*3】")
    # white_deer_6 配货第 1 件 = 治疗药水(小)，与已有 6 瓶堆叠合并（可堆叠物品 count+=3）
    small_before = inv_count(g, q, "治疗药水(小)")
    out = await cmd(m, "buy", g, q, "购买 1*3")
    check("4a 回显 ×3", "×3" in out, out[:200])
    small_after = inv_count(g, q, "治疗药水(小)")
    check("4b 序号商品 +3（堆叠合并）", small_after - small_before == 3,
          f"{small_before} -> {small_after}")
    p = db.get_player(g, q)
    check("4c 序号商品扣 3 倍价", p["gold"] == 50000 - 6 * price_small - 4 * price_mid - 3 * price_small,
          f"gold={p['gold']}")

    print("【5. 数量 0 / 负数 → 友好报错】")
    gold_before = db.get_player(g, q)["gold"]
    small_baseline = inv_count(g, q, "治疗药水(小)")  # = 9（6 + 序号1×3 堆叠合并）
    out = await cmd(m, "buy", g, q, "购买 治疗药水(小)*0")
    check("5a *0 提示至少 1 个", "数量至少 1 个" in out, out[:200])
    out = await cmd(m, "buy", g, q, "购买 治疗药水(小) 0")
    check("5b 空格 0 提示至少 1 个", "数量至少 1 个" in out, out[:200])
    out = await cmd(m, "buy", g, q, "购买 治疗药水(小)*-3")
    check("5c *负 提示至少 1 个", "数量至少 1 个" in out, out[:200])
    out = await cmd(m, "buy", g, q, "购买 治疗药水(小) -3")
    check("5d 空格负数 提示至少 1 个", "数量至少 1 个" in out, out[:200])
    p = db.get_player(g, q)
    check("5e 均未扣钱", p["gold"] == gold_before, f"gold={p['gold']}")
    check("5f 背包未变", inv_count(g, q, "治疗药水(小)") == small_baseline,
          inv_count(g, q, "治疗药水(小)"))

    print("【6. 非数字 → 数量格式不对】")
    out = await cmd(m, "buy", g, q, "购买 治疗药水(小)*abc")
    check("6a *abc 格式不对", "数量格式不对" in out, out[:200])
    out = await cmd(m, "buy", g, q, "购买 治疗药水(小)*")
    check("6b 尾部空 * 格式不对", "数量格式不对" in out, out[:200])
    p = db.get_player(g, q)
    check("6c 未扣钱", p["gold"] == gold_before, f"gold={p['gold']}")

    print("【7. 超上限 → 提示分批】")
    out = await cmd(m, "buy", g, q, "购买 治疗药水(小)*1000")
    check("7a 提示单次最多 999", f"单次最多购买 {C.ECON_CONFIG['buy_qty_max']} 个" in out, out[:200])
    p = db.get_player(g, q)
    check("7b 未扣钱", p["gold"] == gold_before, f"gold={p['gold']}")
    check("7c 背包未变", inv_count(g, q, "治疗药水(小)") == small_baseline,
          inv_count(g, q, "治疗药水(小)"))

    print("【8. 金币不足 → 友好报错且不扣负数】")
    q2 = "buyer2"
    await cmd(m, "register", g, q2, "注册 战士 穷人 男")
    db.update_player(g, q2, gold=10, cur_map="white_deer", cur_subarea="white_deer_6")
    out = await cmd(m, "buy", g, q2, "购买 治疗药水(小)*100")
    check("8a 提示金币不足", "金币不足" in out, out[:200])
    p2 = db.get_player(g, q2)
    check("8b 金币不为负", p2["gold"] == 10, f"gold={p2['gold']}")
    check("8c 未入包", inv_count(g, q2, "治疗药水(小)") == 0, inv_count(g, q2, "治疗药水(小)"))

    print("【9. 购买 *5 无商品名 → 格式提示（防空名静默买第一件）】")
    before9 = set((i["data"].get("name"), i["count"]) for i in db.get_inventory(g, q))
    out = await cmd(m, "buy", g, q, "购买 *5")
    check("9a 回显格式提示", "格式：购买 <商品名/序号>" in out, out[:200])
    after9 = set((i["data"].get("name"), i["count"]) for i in db.get_inventory(g, q))
    check("9b 背包无新增", after9 == before9, str(after9 - before9))

    print("【10. 武器带数量 → 单件保护不破坏】")
    q3 = "buyer3"
    await cmd(m, "register", g, q3, "注册 战士 铁匠客 男")
    # 橡木镇·老铁铁匠铺（oak_town_3，funcs: shop+craft，is_smith 店铺）
    db.update_player(g, q3, gold=50000, cur_map="oak_town", cur_subarea="oak_town_3")
    wname = C.SHOP_WEAPONS.get("oak_town", [None])[0][0]
    out = await cmd(m, "buy", g, q3, f"购买 {wname}*2")
    check("10a 单件提示", "只能单件购买" in out, out[:200])
    p3 = db.get_player(g, q3)
    check("10b 未扣钱", p3["gold"] == 50000, f"gold={p3['gold']}")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    import asyncio
    asyncio.new_event_loop().run_until_complete(main())