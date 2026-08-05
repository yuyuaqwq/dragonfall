# -*- coding: utf-8 -*-
"""commands 层：v66 摆摊系统

验证：
  1. 摆摊：支摊/替换旧摊/背包扣除
  2. 收摊：物品退回/无摊提示
  3. 查看：本地摊位列表/指定玩家摊位
  4. 购入：同地图当面买/异地拦截/群市场兼容
  5. 地图：此地玩家列表 + 🏪摆摊标记
  6. 摊位惰性跟随（移动后摊位跟着人走）
"""
import sys, os, sqlite3, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, db, clean_db, Main, FakeEvent, run

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


_sword_seq = [0]
def add_sword(gid, qid, name="铁剑"):
    _sword_seq[0] += 1
    db.add_item(gid, qid, f"eq_sword_{qid}_{_sword_seq[0]}", {"name": name, "type": "武器", "stackable": False}, 1)


async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "w1", "注册 战士 旅人")
    await cmd(m, "register", "g1", "w2", "注册 法师 米娅")
    db.update_player("g1", "w1", level=5, gold=1000, cur_map="vila_square")
    db.update_player("g1", "w2", level=5, gold=2000, cur_map="vila_square")

    print("【v66 摆摊：支摊】")
    add_sword("g1", "w1")
    out = await cmd(m, "stall", "g1", "w1", "摆摊 铁剑 500")
    check("摆摊成功", "支起了摊位" in out and "铁剑" in out, out[:200])
    check("背包扣除", db.count_item("g1", "w1", "铁剑") == 0, "")
    out = await cmd(m, "stall_view", "g1", "w1", "摊位")
    check("本地摊位可见", "铁剑" in out and "500 金币" in out, out[:200])
    out = await cmd(m, "stall_view", "g1", "w1", "摊位 旅人")
    check("查看指定玩家摊位", "铁剑" in out and "旅人" in out, out[:200])

    print("【v66 摆摊：无物品/格式】")
    out = await cmd(m, "stall", "g1", "w1", "摆摊 铁剑 500")
    check("背包无物拦截", "背包里没有" in out, out[:120])
    out = await cmd(m, "stall", "g1", "w1", "摆摊 铁剑")
    check("格式错误提示", "格式：摆摊" in out, out[:120])

    print("【v66 摆摊：地图玩家列表】")
    out = await cmd(m, "map_view", "g1", "w1", "地图")
    check("此地玩家显示", "此地的玩家" in out and "米娅" in out, out[:200])
    check("摆摊标记", "摆摊中" in out, out[:200])

    print("【v66 摆摊：购入】")
    stalls = db.market_list("g1", "vila_square")
    check("摊位入库", len(stalls) == 1, str(len(stalls)))
    mid = stalls[0]["id"]
    out = await cmd(m, "market_buy", "g1", "w2", f"购入 {mid}")
    check("当面购入成功", "购入成功" in out and "铁剑" in out, out[:200])
    check("买家背包有货", db.count_item("g1", "w2", "铁剑") == 1, "")
    check("卖家收款", db.get_player("g1", "w1")["gold"] == 1500, str(db.get_player("g1", "w1")["gold"]))
    check("摊位已清", len(db.market_list("g1", "vila_square")) == 0, "")

    print("【v66 摆摊：异地拦截】")
    add_sword("g1", "w1", "精铁长剑")
    await cmd(m, "stall", "g1", "w1", "摆摊 精铁长剑 800")
    db.update_player("g1", "w2", cur_map="vila_gate")  # w2 离开
    stalls = db.market_list("g1", "vila_square")
    mid = stalls[0]["id"]
    out = await cmd(m, "market_buy", "g1", "w2", f"购入 {mid}")
    check("异地买摊位货被拦", "当面购入" in out, out[:200])
    db.update_player("g1", "w2", cur_map="vila_square")
    out = await cmd(m, "market_buy", "g1", "w2", f"购入 {mid}")
    check("回到原地可买", "购入成功" in out, out[:200])

    print("【v66 摆摊：收摊】")
    add_sword("g1", "w1", "青铜短剑")
    await cmd(m, "stall", "g1", "w1", "摆摊 青铜短剑 300")
    out = await cmd(m, "stall_close", "g1", "w1", "收摊")
    check("收摊成功", "青铜短剑" in out and "退回背包" in out, out[:200])
    check("物品退回", db.count_item("g1", "w1", "青铜短剑") == 1, "")
    out = await cmd(m, "stall_close", "g1", "w1", "收摊")
    check("无摊收摊提示", "没有摊位" in out, out[:120])

    print("【v66 摆摊：替换旧摊】")
    add_sword("g1", "w1", "狼牙棒")
    add_sword("g1", "w1", "铁皮盾")
    await cmd(m, "stall", "g1", "w1", "摆摊 狼牙棒 400")
    out = await cmd(m, "stall", "g1", "w1", "摆摊 铁皮盾 600")
    check("旧摊自动收", "旧摊位已收摊" in out, out[:200])
    check("旧物退回", db.count_item("g1", "w1", "狼牙棒") == 1, "")
    stalls = db.market_list("g1", "vila_square")
    check("新摊只有一件", len(stalls) == 1 and stalls[0]["item_data"].get("name") == "铁皮盾", str(stalls))

    print("【v66 摆摊：摊位惰性跟随】")
    await cmd(m, "stall", "g1", "w1", "摆摊 铁皮盾 600")  # 重新摆
    db.update_player("g1", "w1", cur_map="vila_street")  # 卖家移动
    out = await cmd(m, "stall_view", "g1", "w1", "摊位 旅人")
    check("摊位跟随到新位置", "维拉镇中央大街" in out or "vila_street" in out or "铁皮盾" in out, out[:200])
    stalls = db.market_list("g1", "vila_street")
    check("新地图可见摊位", len(stalls) == 1, str([s["map_id"] for s in stalls]))
    # 群市场兼容：上架/购入不受影响（用背包里有的狼牙棒）
    out = await cmd(m, "market_sell", "g1", "w1", "上架 狼牙棒 500")
    check("群市场上架正常", "已上架" in out, out[:200])
    out = await cmd(m, "market", "g1", "w2", "市场")
    check("群市场列表正常", "群友市场" in out and "狼牙棒" in out, out[:200])

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
