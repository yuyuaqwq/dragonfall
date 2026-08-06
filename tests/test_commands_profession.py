# -*- coding: utf-8 -*-
"""commands 层：v67 副业体系改造（双副业上限 + 强化/附魔归位 + 代工补偿）

验证：
  1. 副业面板：激活位显示 0/2 + 🔒 标记
  2. 首次动作自动激活（1/2 → 2/2 → 第3条被拦）
  3. 遗忘副业：位空出 + 等级清零
  4. 严格上限：位置满时已有等级也拦截；遗忘后自动激活
  5. 强化归位打造：+N 需要打造 Lv.N
  6. 附魔归位炼金：需要炼金 Lv.2
  7. 代工：无副业要求 + 3 倍金币
  8. 打造副业不足提示引流代工
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


def reset_profs(gid, qid):
    for k in ("gather", "mining", "fishing", "alchemy", "craft", "cooking"):
        db.forget_prof(gid, qid, k)


def add_mats(gid, qid, count=10):
    db.add_item(gid, qid, "mat_ye_gou_liao_ya", {"name": "野狗獠牙", "type": "材料", "stackable": True}, count)
    db.add_item(gid, qid, "mat_shu_wei", {"name": "鼠尾", "type": "材料", "stackable": True}, count)


def add_equip(gid, qid, name="铁剑"):
    db.add_item(gid, qid, f"eq_t_{qid}_{name}", {"name": name, "type": "武器", "slot": "weapon",
                                                 "quality": "white", "lv": 3, "atk": 12, "stackable": False}, 1)


async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "w1", "注册 战士 旅人")
    db.update_player("g1", "w1", level=20, gold=5000, cur_map="vila_gate")

    print("【v67 双副业：面板】")
    out = await cmd(m, "profession_view", "g1", "w1", "副业")
    check("面板显示已激活 0/2", "0/2" in out, out[:120])
    check("未激活标🔒", "🔒" in out, out[:200])

    print("【v67 双副业：自动激活】")
    out = await cmd(m, "gather", "g1", "w1", "采集")
    check("采集自动激活", "选择了「采集」" in out and "1/2" in out, out[:200])
    check("采集进行中", "开始采集" in out, out[:200])
    m._prof_wait_clear("g1", "w1")
    db.update_player("g1", "w1", cur_map="stonefist_mine")
    out = await cmd(m, "mining", "g1", "w1", "挖掘")
    check("挖掘自动激活2/2", "选择了「挖掘」" in out and "2/2" in out, out[:200])
    m._prof_wait_clear("g1", "w1")
    db.update_player("g1", "w1", cur_map="vila_gate")
    out = await cmd(m, "fishing", "g1", "w1", "垂钓")
    check("第三条被拦", "副业位已满" in out and "遗忘副业" in out, out[:200])

    print("【v67 双副业：遗忘】")
    out = await cmd(m, "prof_forget", "g1", "w1", "遗忘副业 采集")
    check("遗忘成功位空出", "遗忘了「采集」" in out and "1/2" in out, out[:200])
    check("采集等级清零", db.get_prof_level("g1", "w1", "gather") == 1, str(db.get_prof_level("g1", "w1", "gather")))
    out = await cmd(m, "fishing", "g1", "w1", "垂钓")
    check("遗忘后可再激活", "选择了「垂钓」" in out, out[:200])
    m._prof_wait_clear("g1", "w1")
    out = await cmd(m, "prof_forget", "g1", "w1", "遗忘副业 不存在")
    check("不存在副业提示", "没有「不存在」这个副业" in out or "没有" in out, out[:120])

    print("【v67 双副业：严格上限+老玩家兼容】")
    # 位置满（mining+fishing）时，有等级的 cooking 也要遗忘才能用
    db.add_prof_exp("g1", "w1", "cooking", 300)
    out = await cmd(m, "cooking", "g1", "w1", "烹饪 鱼汤")
    check("位置满时有等级也拦", "副业位已满" in out, out[:200])
    await cmd(m, "prof_forget", "g1", "w1", "遗忘副业 挖掘")
    out = await cmd(m, "cooking", "g1", "w1", "烹饪 鱼汤")
    check("遗忘后老玩家自动激活", "cooking" in db.get_activated_profs("g1", "w1"), str(db.get_activated_profs("g1", "w1")))

    print("【v67 强化归位打造】")
    reset_profs("g1", "w1")
    db.update_player("g1", "w1", cur_map="vila_street", gold=5000)
    add_equip("g1", "w1", "试炼剑")
    out = await cmd(m, "enhance", "g1", "w1", "强化 试炼剑")
    check("+1 强化成功（打造自动激活Lv.1）", "强化成功" in out and "+1" in out, out[:200])
    out = await cmd(m, "enhance", "g1", "w1", "强化 试炼剑")
    check("+2 需要打造Lv.2拦截", "需要打造副业 Lv.2" in out, out[:200])
    db.add_prof_exp("g1", "w1", "craft", 30)  # Lv.2
    out = await cmd(m, "enhance", "g1", "w1", "强化 试炼剑")
    check("打造Lv.2后+2可强化", "强化成功" in out or "强化失败" in out or "降级" in out, out[:200])

    print("【v67 附魔归位炼金】")
    reset_profs("g1", "w1")
    out = await cmd(m, "enchant", "g1", "w1", "附魔")
    check("无参附魔先给格式（不被炼金拦）", "附魔哪件装备" in out, out[:200])
    out = await cmd(m, "enchant", "g1", "w1", "附魔 试炼剑 攻击")
    check("炼金Lv.1附魔被拦", "需要炼金副业 Lv.2" in out, out[:200])
    db.add_prof_exp("g1", "w1", "alchemy", 30)  # Lv.2
    out = await cmd(m, "enchant", "g1", "w1", "附魔 试炼剑 攻击")
    check("炼金Lv.2后通过门槛", "需要炼金副业 Lv.2" not in out, out[:200])

    print("【v67 代工补偿】")
    reset_profs("g1", "w1")
    db.update_player("g1", "w1", gold=5000)
    add_mats("g1", "w1", count=6)  # 6 份：第一次代工消耗 5+3，剩 1 獠牙 → 第二次拦
    out = await cmd(m, "craft_commission", "g1", "w1", "代工 铁剑")
    check("代工成功", "代工完成" in out and "铁剑" in out and "90 金币" in out, out[:200])
    check("打造未激活", "craft" not in db.get_activated_profs("g1", "w1"), str(db.get_activated_profs("g1", "w1")))
    check("金币扣3倍", db.get_player("g1", "w1")["gold"] == 4910, str(db.get_player("g1", "w1")["gold"]))
    check("装备入包", db.count_item("g1", "w1", "铁剑") >= 1, "")
    out = await cmd(m, "craft_commission", "g1", "w1", "代工 铁剑")
    check("材料不足拦截", "材料不足" in out, out[:200])
    out = await cmd(m, "craft_commission", "g1", "w1", "代工")
    check("无参提示格式", "格式：代工" in out, out[:120])

    print("【v67 打造引流】")
    add_mats("g1", "w1", count=10)
    out = await cmd(m, "craft", "g1", "w1", "打造 铁剑")
    check("打造未激活自动激活", "选择了「打造」" in out, out[:200])
    db.update_player("g1", "w1", level=35, gold=5000)
    add_mats("g1", "w1", count=10)
    out = await cmd(m, "craft", "g1", "w1", "打造 雷霆之锤")
    check("高等级配方提示引流代工", "代工" in out, out[:200])

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
