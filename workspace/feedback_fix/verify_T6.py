# -*- coding: utf-8 -*-
"""T6 意见#7（鱼鱼：技能升级之后描述不变）验证脚本。

改动：game/commands/player.py skill_detail 在『效果：desc』行后追加
『📈 Lv.X 当前效果：…』动态数值行（按 SKILL_UP 成长公式计算，仅已学会且可升级技能）。

验证：
  1. 升级前（Lv.1）详情含『📈 Lv.1 当前效果：伤害 100% · 条件 ×1.15』
  2. 升级后（Lv.2）详情含『📈 Lv.2 当前效果：伤害 112% · 条件 ×1.2』——与 Lv.1 数值可感知不同
  3. 详情『效果：』desc 静态原文保持不变（不混淆）
  4. 被动技能（战意高涨）详情不含『📈 Lv.』行
  5. 未学会技能详情不含『📈 Lv.』行

用法：python workspace/feedback_fix/verify_T6.py
"""
import sys, os
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\tests")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from conftest import C, E, db, clean_db, Main, FakeEvent, run

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

async def main():
    clean_db()
    m = Main(None)
    g, q = "g6", "t6user"
    await cmd(m, "register", g, q, "注册 战士 技能验证 男")
    db.update_player(g, q, level=30, gold=5000, skill_points=100)

    hk = E.skill_info("战士", "挥砍")
    print("  挥砍:", {k: hk.get(k) for k in ("power", "kind", "cond")}, "SKILL_UP:", C.SKILL_UP.get("挥砍"))

    print("【1. 升级前 Lv.1 详情】")
    await cmd(m, "skill_learn", g, q, "技能学习 挥砍")
    out = await cmd(m, "skill_detail", g, q, "技能详情 挥砍")
    print(out)
    check("1a 含当前等级效果行 Lv.1", "📈 Lv.1 当前效果：" in out, out)
    check("1b Lv.1 数值=伤害 100% · 条件 ×1.15",
          "📈 Lv.1 当前效果：伤害 100% · 条件 ×1.15" in out, out)
    check("1c desc 静态原文不变", "效果：基础斩击，100% 物理伤害。先手(速度高于目标)时伤害＋15%" in out, out)
    check("1d 详情仍含升级提示(下一级预览)",
          "💡 『技能升级 挥砍』" in out and "伤害 112%" in out, out)

    print("【2. 升级后 Lv.2 详情】")
    out = await cmd(m, "skill_upgrade", g, q, "技能升级 挥砍")
    check("2a 升级成功", "升级到 Lv.2" in out, out[:200])
    out = await cmd(m, "skill_detail", g, q, "技能详情 挥砍")
    print(out)
    check("2b 详情行变为 Lv.2", "📈 Lv.2 当前效果：" in out, out)
    check("2c Lv.2 数值=伤害 112% · 条件 ×1.2",
          "📈 Lv.2 当前效果：伤害 112% · 条件 ×1.2" in out, out)
    check("2d 升级前后数值可感知变化(100%→112%)",
          "📈 Lv.1 当前效果" not in out and "伤害 112%" in out, out)
    check("2e desc 静态原文仍然不变", "效果：基础斩击，100% 物理伤害。先手(速度高于目标)时伤害＋15%" in out, out)

    print("【3. 被动技能不显示当前等级行】")
    p = db.get_player(g, q)
    check("3a 战意高涨 SKILL_UP max=1(不可升级)", C.SKILL_UP.get("战意高涨", {}).get("max", 5) == 1,
          str(C.SKILL_UP.get("战意高涨")))
    await cmd(m, "skill_learn", g, q, "技能学习 战意高涨")
    out = await cmd(m, "skill_detail", g, q, "技能详情 战意高涨")
    check("3b 被动详情无📈行", "📈 Lv." not in out, out)
    check("3c 被动详情保留既有提示", "被动技能，无需升级" in out, out)

    print("【4. 未学会技能不显示当前等级行】")
    out = await cmd(m, "skill_detail", g, q, "技能详情 裂地斩")
    check("4a 未学会详情无📈行", "📈 Lv." not in out, out)

    print("【5. 升级前/后详情输出（证据）】")
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    import asyncio
    asyncio.new_event_loop().run_until_complete(main())