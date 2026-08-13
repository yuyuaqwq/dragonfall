#!/usr/bin/env python3
"""v107 隐藏职业解锁链测试（2026-08-13 鱼鱼拍板）

覆盖：
1. 未解锁：『转职 兽王』提示传承未敞开
2. 已解锁但 <40 级：提示等级不足
3. 已解锁 + 40 级：转职成功（class_name/技能初始化/属性重算）
4. 已是该职业：提示已是
5. 『注册』隐藏职业被拦截
6. 通用路由：多职业名别名解析
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
        print(f"  ❌ {name} {str(detail).encode('utf-8', 'replace').decode('utf-8', 'replace')[:300]}")


async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""


async def main():
    clean_db()
    m = Main(None)
    await cmd(m, "register", "g1", "w1", "注册 战士 旅人 男")
    db.update_player("g1", "w1", level=35, gold=1000, cur_map="oak_town", cur_subarea="oak_town_5")

    print("【1. 未解锁拦截】")
    out = await cmd(m, "evolve", "g1", "w1", "转职 兽王")
    check("未解锁提示传承未敞开", "传承还未向你敞开" in out, out[:200])
    check("未解锁含职业线索", "兽王" in out or "万兽" in out, out[:200])

    print("【2. 已解锁但等级不足】")
    db.update_player("g1", "w1", hidden_class_unlock=["cls_beast_king"])
    out = await cmd(m, "evolve", "g1", "w1", "转职 兽王")
    check("等级不足提示", "40 级" in out, out[:200])

    print("【3. 40 级转职成功】")
    db.update_player("g1", "w1", level=40)
    out = await cmd(m, "evolve", "g1", "w1", "转职 兽王")
    check("转职成功文案", "传承完成" in out and "兽王" in out, out[:300])
    p = db.get_player("g1", "w1")
    check("职业切换", p["class_name"] == "cls_beast_king", str(p["class_name"]))
    check("技能初始化", len(p.get("learned_skills", [])) >= 1,
          str(p.get("learned_skills")))
    check("驯兽召唤已学", "驯兽召唤" in [C.display("skills", s) for s in p.get("learned_skills", [])],
          str(p.get("learned_skills")))
    check("属性重算", p.get("max_hp", 0) > 100, str(p.get("max_hp")))

    print("【4. 已是该职业】")
    out = await cmd(m, "evolve", "g1", "w1", "转职 兽王")
    check("已是提示", "你已是兽王" in out, out[:200])

    print("【5. 注册拦截】")
    out = await cmd(m, "register", "g1", "w2", "注册 亡灵术士 巫妖 男")
    check("隐藏职业不可注册", "隐藏职业" in out, out[:200])
    await cmd(m, "register", "g1", "w6", "注册 战士 路人 男")
    out2 = await cmd(m, "register", "g1", "w7", "注册 血法师 血影 女")
    check("血法师也不可注册", "隐藏职业" in out2, out2[:200])

    print("【6. 通用路由 + 别名】")
    # 亡灵术士全流程（w3 先注册普通职业）
    await cmd(m, "register", "g1", "w3", "注册 牧师 巫妖 男")
    db.update_player("g1", "w3", level=40, hidden_class_unlock=["cls_necromancer"])
    out = await cmd(m, "evolve", "g1", "w3", "转职 亡灵术士")
    check("亡灵术士转职", "传承完成" in out and "亡灵术士" in out, out[:200])
    p3 = db.get_player("g1", "w3")
    check("亡灵职业切换", p3["class_name"] == "cls_necromancer", str(p3["class_name"]))
    check("召唤骷髅已学", "召唤骷髅" in [C.display("skills", s) for s in p3.get("learned_skills", [])],
          str(p3.get("learned_skills")))
    # 别名：『转职 龙血』
    await cmd(m, "register", "g1", "w4", "注册 战士 龙裔 男")
    db.update_player("g1", "w4", level=40, hidden_class_unlock=["cls_dragon_warrior"])
    out = await cmd(m, "evolve", "g1", "w4", "转职 龙血")
    check("别名『龙血』路由", "传承完成" in out and "龙血战士" in out, out[:200])
    # 别名：『转职 亡灵』
    out = await cmd(m, "evolve", "g1", "w3", "转职 亡灵")
    check("别名『亡灵』路由到已是", "你已是亡灵术士" in out, out[:200])
    # 未知职业名不误伤
    await cmd(m, "register", "g1", "w5", "注册 战士 无名 男")
    db.update_player("g1", "w5", level=40)
    out = await cmd(m, "evolve", "g1", "w5", "转职 龙血")
    check("未解锁龙血拦截", "传承还未向你敞开" in out, out[:200])

    print()
    print(f"===== v107 隐藏职业解锁链测试: {passed} passed, {failed} failed =====")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
