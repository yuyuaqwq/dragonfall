# -*- coding: utf-8 -*-
"""v134.2 验证：百科查副本名显示完整进入条件（等级/人数/钥匙）"""
import sys, os, random
# 必须在 import 插件前设置私有库（绝对路径）
os.environ["GWEN_GAME_DB"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "smoke_v1342_baike.db"
)
os.environ["GWEN_TEST_MODE"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, E, BT, db, clean_db, Main, FakeEvent, run, make_player

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

def main():
    clean_db()
    make_player("g", "u1", "测试玩家", "战士")
    m = Main(None)

    async def _go():
        print("【1. 百科 哥布林营地（无钥匙副本）】")
        ev = FakeEvent("g", "u1", "百科 哥布林营地")
        got = await run(m.encyclopedia, ev)
        check("有返回", bool(got), repr(got)[:200])
        full = "\n".join(got)
        check("标题含哥布林营地", "哥布林营地" in full, full[:100])
        check("显示推荐等级 Lv.15+", "Lv.15+" in full, full[:200])
        check("显示人数 1-2 人", "1-2 人" in full, full[:200])
        check("显示无需钥匙", "无需钥匙" in full, full[:200])
        check("显示开启挑战提示", "开启挑战" in full, full[:200])
        print(full)
        print()

        print("【2. 百科 旧王陵（有钥匙副本，回归）】")
        keyed = [i for i in C.INSTANCES.values() if i.get("key_item")]
        print(f"  带钥匙副本数: {len(keyed)}")
        if keyed:
            ki = keyed[0]
            ev = FakeEvent("g", "u1", f"百科 {ki['name']}")
            got = await run(m.encyclopedia, ev)
            full = "\n".join(got)
            check("有返回", bool(got), repr(got)[:200])
            check(f"显示入场需要『{ki['key_item']}』", f"入场需要『{ki['key_item']}』" in full, full[:300])
            print(full)
        print()

    import asyncio
    asyncio.run(_go())

    print(f"结果: {passed} 通过, {failed} 失败")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
