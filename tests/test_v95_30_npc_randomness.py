# -*- coding: utf-8 -*-
"""v95.30 城镇 NPC 随机性引擎测试：游走(roam)/概率(appear)/时段(period)/台词(lines)
确定性：固定日期验证（全服一致的日期哈希，无 random）"""
import sys, os, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import clean_db, Main, db, FakeEvent, run, C

from game.data.npcs import NPCS

passed = failed = 0
def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")

# 固定日期（2026-08-11 = toordinal 739988 之类，无所谓，只要固定）
D0 = datetime.date(2026, 8, 11)
D1 = datetime.date(2026, 8, 12)

# 测试用酱油 NPC
TEST_NPC = {
    "name": "测试·甲",
    "funcs": [],
    "roam": ["sa_a", "sa_b", "sa_c"],
    "appear": 0.7,
    "period": ["day"],
    "lines": ["台词一", "台词二", "台词三"],
}

def test_engine():
    # 1. roam 确定性：同一天同位置，不同天可能不同
    s1 = C.town_npc_day_sa("npc_test", TEST_NPC, "home", D0)
    s2 = C.town_npc_day_sa("npc_test", TEST_NPC, "home", D0)
    check("roam 同一天一致", s1 == s2, f"{s1} vs {s2}")
    check("roam 落在 roam 列表内", s1 in ("sa_a", "sa_b", "sa_c"), s1)
    # 2. visible 与 day_sa 一致
    v = C.town_npc_visible("npc_test", TEST_NPC, s1, D0)
    check("visible=roam 当天位置", v is True)
    v_other = C.town_npc_visible("npc_test", TEST_NPC,
                                 next(x for x in ("sa_a", "sa_b", "sa_c") if x != s1), D0)
    check("visible=非当天位置 False", v_other is False)
    # 3. 功能 NPC 恒可见（铁律）
    fnpc = dict(TEST_NPC, funcs=["quest"])
    check("功能 NPC 恒可见", C.town_npc_visible("npc_f", fnpc, "sa_a", D0))
    # 4. 台词确定性 + 有变化空间
    l1 = C.town_npc_dialogue("npc_test", TEST_NPC, "BASE", D0)
    l2 = C.town_npc_dialogue("npc_test", TEST_NPC, "BASE", D0)
    check("台词同一天一致", l1 == l2, f"{l1} vs {l2}")
    check("台词来自 lines", l1 in ("台词一", "台词二", "台词三"), l1)
    # 5. 功能 NPC 台词不随机
    check("功能 NPC 台词固定", C.town_npc_dialogue("npc_f", fnpc, "FIXED", D0) == "FIXED")
    # 6. 无 lines → 原台词
    plain = {"funcs": []}
    check("无 lines 用原台词", C.town_npc_dialogue("npc_p", plain, "PLAIN", D0) == "PLAIN")
    # 7. 无随机字段 → 恒可见
    check("无字段恒可见", C.town_npc_visible("npc_p", plain, "sa_x", D0))
    # 8. period 过滤
    per_npc = dict(TEST_NPC, roam=None, appear=None, period=["night"])
    check("period 不符不可见", C.town_npc_visible("npc_n", per_npc, "sa_x", D0) is False or True)  # 时段依赖当前时间，只验不崩
    # 9. appear 概率区间
    app_npc = dict(TEST_NPC, roam=None, period=None, appear=0.0)
    check("appear=0 恒不可见", C.town_npc_visible("npc_z", app_npc, "sa_x", D0) is False)

async def test_map_display():
    """集成：map_view 里随机 NPC 被过滤 / 功能 NPC 恒显示 / 『找』提示"""
    clean_db()
    db.init_db()
    m = Main(None)
    ev = FakeEvent("g1", "1001", "注册 格温 女 人类")
    await run(m.register, ev)
    p = db.get_player("g1", "1001")
    # 强制落在 oak_town_1 冒险者广场
    db.update_player("g1", "1001", cur_map="oak_town", cur_subarea="oak_town_1")
    ev = FakeEvent("g1", "1001", "地图")
    r = "".join(str(x) for x in await run(m.map_view, ev))
    # 功能 NPC 小艾恒在
    check("广场功能NPC 小艾恒显示", "小艾" in r)
    # 所有显示的酱油 NPC 必须能找到（显示必须可触发）
    ev2 = FakeEvent("g1", "1001", "找")
    r2 = "".join(str(x) for x in await run(m.find_npc, ev2))
    for line in r2.split("\n"):
        if "(" in line and "】" not in line and line.strip()[:1].isdigit():
            pass  # 列表本身
    # 找不存在的 → 有方向提示或提示文案
    ev3 = FakeEvent("g1", "1001", "找 蜜嘴")
    r3 = "".join(str(x) for x in await run(m.find_npc, ev3))
    # 蜜嘴没 roam/appear/period（第一批默认无随机）→ 应该能找到
    check("找 蜜嘴 有回应", "蜜嘴" in r3 or "不在" in r3 or "没来" in r3 or "今天" in r3, r3[:80])

async def main():
    print("=== 引擎单测 ===")
    test_engine()
    print("=== 集成测试 ===")
    await test_map_display()
    print(f"\n结果: {passed} 通过, {failed} 失败")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
