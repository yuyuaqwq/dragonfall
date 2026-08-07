# -*- coding: utf-8 -*-
"""commands 层：v65 NPC 多轮对话系统

验证：
  1. 对话树入口：找有树 NPC 显示选项
  2. 推进：对话 N 切换节点 / 分支
  3. 结束：对话 0 / 再见 / 告辞
  4. 会话生命周期：无会话提示 / 移动后惰性失效 / 重复找重置
  5. 条件选项：quest_pending 按主线状态显隐
  6. 动作：set_flag / open_shop / give_item / give_gold / hint
  7. 兼容：无对话树 NPC 走旧单轮台词
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


async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "w1", "注册 战士 旅人")
    db.update_player("g1", "w1", level=5, gold=1000, cur_map="oak_town", cur_subarea="oak_town_2")

    print("【v65 对话树：入口】")
    out = await cmd(m, "find_npc", "g1", "w1", "找 镇长")
    check("找镇长进入对话树", "1. 野狗是怎么回事？" in out and "0. 结束对话" in out, out[:200])
    check("quest_pending 显示任务选项", "我需要任务。" in out, out[:200])
    check("对话树保留功能提示", "接任务" in out or "任务" in out, out[:200])

    print("【v65 对话树：推进】")
    out = await cmd(m, "talk_choice", "g1", "w1", "对话 1")
    check("对话1推进到野狗分支", "那些畜生是入秋之后" in out, out[:200])
    out = await cmd(m, "talk_choice", "g1", "w1", "对话 1")
    check("对话1推进到誓言", "好样的！镇子西边的路口" in out and "包在我身上！" in out, out[:200])
    # set_flag pledged 已写入（选"我这就去解决它们！"时触发）
    flags = db.get_talk_flags("g1", "w1", "npc_mayor")
    check("set_flag 写入", "pledged" in flags, str(flags))
    out = await cmd(m, "talk_choice", "g1", "w1", "对话 1")
    check("包在我身上结束对话", "那就再会了" in out, out[:200])

    print("【v65 对话树：无会话时】")
    out = await cmd(m, "talk_choice", "g1", "w1", "对话 1")
    check("无会话提示", "没有正在进行的对话" in out, out[:120])

    print("【v65 对话树：重复找重置】")
    out = await cmd(m, "find_npc", "g1", "w1", "找 镇长")
    check("重新找回到 start", "1. 野狗是怎么回事？" in out, out[:200])
    # 镇长接取 q1 后（find_npc 自动接），quest_pending 选项隐藏
    out = await cmd(m, "talk_choice", "g1", "w1", "对话 2")
    check("对话2到镇子近况", "镇子还算太平" in out, out[:200])

    print("【v65 对话树：分支与结束】")
    out = await cmd(m, "talk_choice", "g1", "w1", "对话 1")
    check("town 分支可回野狗", "那些畜生是入秋之后" in out, out[:200])
    out = await cmd(m, "talk_choice", "g1", "w1", "对话 0")
    check("对话0结束", "那就再会了" in out, out[:120])
    out = await cmd(m, "talk_choice", "g1", "w1", "再见")
    check("结束词再见提示无会话", "没有正在进行的对话" in out, out[:120])

    print("【v65 对话树：结束词/无参渲染】")
    out = await cmd(m, "find_npc", "g1", "w1", "找 镇长")
    check("重新进入对话", "0. 结束对话" in out, out[:200])
    out = await cmd(m, "talk_choice", "g1", "w1", "对话")
    check("无参对话重渲染当前节点", "0. 结束对话" in out, out[:200])
    out = await cmd(m, "talk_choice", "g1", "w1", "告辞")
    check("告辞结束", "那就再会了" in out, out[:120])

    print("【v65 对话树：移动后惰性失效】")
    out = await cmd(m, "find_npc", "g1", "w1", "找 镇长")
    check("再次进入对话", "0. 结束对话" in out, out[:200])
    db.update_player("g1", "w1", cur_map="oak_meadow")  # 模拟移动走
    out = await cmd(m, "talk_choice", "g1", "w1", "对话 1")
    check("离开地图会话失效", "不在这里了" in out, out[:200])
    st = db.get_talk_state("g1", "w1")
    check("会话已清", st is None, str(st))

    print("【v65 对话树：条件显隐】")
    # 主线全部完成 → quest_pending 不再显示
    db.update_player("g1", "w1", cur_map="oak_town", cur_subarea="oak_town_2")
    db.save_quests("g1", "w1", {"main_quest": None, "main_status": "pending", "main_progress": {},
                                "daily": {}, "completed_main": ["q1"], "side": {}})
    out = await cmd(m, "find_npc", "g1", "w1", "找 镇长")
    check("主线完成后任务选项隐藏", "我需要任务。" not in out and "1. 野狗是怎么回事？" in out, out[:200])

    print("【v65 对话树：动作执行】")
    # 铁匠：open_shop 动作
    db.update_player("g1", "w1", cur_map="oak_town", cur_subarea="oak_town_3")
    out = await cmd(m, "find_npc", "g1", "w1", "找 铁匠")
    check("铁匠对话树", "1. 看看你的货。" in out, out[:200])
    out = await cmd(m, "talk_choice", "g1", "w1", "对话 1")
    check("open_shop 提示", "输入『商店』可以买东西" in out and "慢慢挑" in out, out[:200])
    # give_item / give_gold 动作（直接测 apply 方法）
    notices = m._apply_talk_action("g1", "w1", db.get_player("g1", "w1"), "npc_mayor",
                                   {"give_gold": 50, "give_exp": 30, "give_item": {"key": "狼皮", "count": 2}})
    p = db.get_player("g1", "w1")
    check("give_gold 生效", p["gold"] == 1050, str(p["gold"]))
    check("give_exp 生效", p["exp"] == 30, str(p["exp"]))
    check("give_item 通知", any("获得 狼皮 ×2" in n for n in notices), str(notices))
    check("give_item 入包", db.count_item("g1", "w1", "狼皮") == 2, str(db.count_item("g1", "w1", "狼皮")))
    # hint 动作
    notices = m._apply_talk_action("g1", "w1", db.get_player("g1", "w1"), "npc_mayor", {"hint": "输入『住宿』恢复满血"})
    check("hint 通知", any("住宿" in n for n in notices), str(notices))

    print("【v65 兼容：无对话树 NPC 走旧单轮】")
    db.update_player("g1", "w1", cur_map="dawn_city")
    out = await cmd(m, "find_npc", "g1", "w1", "找 旅店")
    check("旧单轮台词", "远道而来的冒险者" in out or "旅店" in out, out[:200])

    print("【v65 引擎：数据完整性】")
    # 所有对话树节点引用合法：next 要么是 __end__ 要么是存在的节点
    bad = []
    for npc_id, dlg in C.DIALOGUES.items():
        nodes = dlg.get("nodes", {})
        if dlg.get("start") not in nodes:
            bad.append(f"{npc_id}:start")
        for nid, nd in nodes.items():
            for opt in nd.get("options", []):
                nxt = opt.get("next", "__end__")
                if nxt != "__end__" and nxt not in nodes:
                    bad.append(f"{npc_id}:{nid}->{nxt}")
    check("对话树引用全部合法", len(bad) == 0, str(bad[:5]))
    # 有对话树的 NPC 都在 NPCS 里
    orphan = [nid for nid in C.DIALOGUES if nid not in C.NPCS]
    check("对话树 NPC 全部存在", len(orphan) == 0, str(orphan))

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    import asyncio
    sys.exit(0 if asyncio.run(main()) else 1)
