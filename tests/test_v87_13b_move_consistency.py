# -*- coding: utf-8 -*-
"""v87.13b 验证：移动到达展示与『地图』展示一致（子区域级信息）"""
import sys, os, asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import FakeEvent, run, clean_db, Main, db

passed = failed = 0
def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

async def main():
    clean_db()
    db.init_db()
    m = Main(None)
    # 直接落库玩家（register 有群绑定逻辑，make_player 更稳）
    from conftest import make_player
    make_player("g1", "1001", "甲", "战士")
    p = db.get_player("g1", "1001")
    check("造玩家", p is not None)
    # 玩家初始位置 oak_town
    db.update_player("g1", "1001", cur_map="oak_town", cur_subarea="oak_town_1")

    # oak_town 的邻居：看 MAP_CONNECTIONS —— 橡木草地 oak_meadow 应该是邻居
    # 移动 6（橡木草地）→ 落点 oak_meadow_1 草地边缘
    ev = FakeEvent("g1", "1001", "移动 6")
    r1 = "".join(str(x) for x in await run(m.move, ev))
    p1 = db.get_player("g1", "1001")
    print("  [跨图移动6]", r1[:300].replace("\n", " | "))
    check("落点 oak_meadow_1", p1["cur_map"] == "oak_meadow" and p1["cur_subarea"] == "oak_meadow_1",
          f"{p1['cur_map']}:{p1['cur_subarea']}")
    check("移动展示含子区域描述", "草地边缘" in r1, r1[:150])
    # 场景应显示 oak_meadow_1 的元素（橡木草地界碑）
    check("移动展示含目标场景元素", "界碑" in r1 or "橡木草地" in r1, r1[:300])

    # 然后发『地图』对比
    ev = FakeEvent("g1", "1001", "地图")
    r2 = "".join(str(x) for x in await run(m.map_view, ev))
    print("  [地图@草地边缘]", r2[:300].replace("\n", " | "))
    check("地图展示含子区域描述", "草地边缘" in r2, r2[:150])
    check("地图展示含场景元素", "界碑" in r2 or "橡木草地" in r2, r2[:300])

    # 一致性：移动到达的场景行 ⊆ 地图展示的场景行（都显示草地边缘的 PROPS）
    # 提取"✨ 场景"后的行
    def scene_lines(text):
        out = []
        in_scene = False
        for ln in text.split("\n"):
            if "✨ 场景" in ln:
                in_scene = True
                continue
            if in_scene and ln.strip():
                if ln.strip().startswith(("🏪", "👥", "👤", "🐾", "📮", "📍", "💡", "输入")):
                    break
                out.append(ln.strip())
        return out
    s1 = scene_lines(r1)
    s2 = scene_lines(r2)
    print(f"  移动场景行: {s1}")
    print(f"  地图场景行: {s2}")
    check("移动与地图场景一致", set(s1) == set(s2), f"{s1} vs {s2}")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0

if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
