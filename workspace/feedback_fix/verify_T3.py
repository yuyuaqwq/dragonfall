# -*- coding: utf-8 -*-
"""T3 意见#4 副业引导：核实注册欢迎语含副业入口提示 + 『副业』指令不破坏"""
import sys, os
sys.path.insert(0, r"C:\Users\yuyu\qqbot\data\plugins\dragonfall\tests")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from conftest import FakeEvent, run, clean_db, Main, db

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
    m = Main(None)
    clean_db()
    print("【T3#1 旧格式注册（带职业）欢迎语含副业引导】")
    out = await cmd(m, "register", "g1", "q1", "注册 战士 格温 男")
    check("注册成功", "欢迎来到奥兰迪亚大陆" in out, out[:80])
    check("含🔨副业系统节", "🔨 副业系统" in out, out)
    check("含『副业』入口", "『副业』查看状态" in out, out)
    check("含导师位置", "草药师·艾琳" in out and "拜师" in out, out)

    print("【T3#2 新格式注册（见习冒险者）欢迎语含副业引导】")
    out = await cmd(m, "register", "g1", "q2", "注册 阿甘 男")
    check("注册成功见习", "见习冒险者" in out, out[:80])
    check("见习含🔨副业系统节", "🔨 副业系统" in out, out)
    check("见习含『副业』入口", "『副业』查看状态" in out, out)
    check("见习含导师位置", "草药师·艾琳" in out and "拜师" in out, out)

    print("【T3#3 『副业』指令可用（不破坏）】")
    out = await cmd(m, "profession_view", "g1", "q1", "副业")
    check("副业面板打开", "副业面板" in out, out[:120])
    check("未解锁引导仍在", "找对应导师拜师学习" in out, out[:200])

    print("【T3#4 副业动作拦截引导仍在（拜师流程未被破坏）】")
    out = await cmd(m, "gather", "g1", "q1", "采集")
    check("采集拦引导导师", "拜师" in out and "艾琳" in out, out[:200])

    print(f"\nT3 结果: {passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())