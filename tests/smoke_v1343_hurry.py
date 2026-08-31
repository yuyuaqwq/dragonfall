# -*- coding: utf-8 -*-
"""v134.3 赶路模式精简冒烟：move_mode 开启时『地图』/到达视图只显示可前往，
带 hurry_type 参数才显示对应类型。"""
import sys, os, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, r"C:\Users\yuyu\AppData\Roaming\uv\tools\astrbot\Lib\site-packages")

os.environ["GWEN_GAME_DB"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "smoke_v1343_hurry.db")
os.environ["GWEN_TEST_MODE"] = "1"

from conftest import C, E, BT, db, clean_db, Main, FakeEvent, run, make_player

async def _go():
    m = Main()
    G, Q = "g1", "u1"
    clean_db()
    p = make_player(G, Q, "测试玩家", "战士")
    # 把玩家放到白鹿城
    db.update_player(G, Q, cur_map="white_deer", cur_subarea="white_deer_1")

    # ---- ① 未开赶路模式：地图全量 ----
    r = await run(m.map_view, FakeEvent(G, Q, "地图"))
    full_has = "🏪 此地设施" in r[0] and "可探索触发" in r[0]
    print(f"① 未开赶路模式 全量区块: {full_has}")
    print("   [输出预览]", repr(r[:200]))

    # ---- ② 开启赶路模式（无参）：地图只显示可前往 ----
    db.set_event_state(f"move_mode:{Q}", "1")
    db.set_event_state(f"hurry_type:{Q}", "")
    r = await run(m.map_view, FakeEvent(G, Q, "地图"))
    has_nav = "📮 可前往" in r[0] or "●1." in r[0]
    has_fac = "🏪 此地设施" in r[0]
    has_npc = "👥 这里的 NPC" in r[0]
    has_hint = "赶路模式中" in r[0]
    print(f"② 赶路模式地图 有可前往: {has_nav}, 无设施: {not has_fac}, 无NPC: {not has_npc}, 有提示: {has_hint}")
    print("   [输出预览]", repr(r[:200]))

    # ---- ③ 赶路模式 + 带参数（NPC）：显示 NPC 类型 ----
    db.set_event_state(f"hurry_type:{Q}", "npc")
    r = await run(m.map_view, FakeEvent(G, Q, "地图"))
    has_npc2 = "NPC" in r[0]
    has_fac2 = "🏪 此地设施" in r[0]
    print(f"③ 带参NPC 有NPC区: {has_npc2}, 无设施: {not has_fac2}")
    print("   [输出预览]", repr(r[:250]))

    # ---- ④ 移动落点（_subarea_arrive）：赶路模式只显示可前往 ----
    db.set_event_state(f"hurry_type:{Q}", "")
    sa = None
    for s in (C.MAP_BY_ID["white_deer"].get("subareas") or []):
        if s["id"] == "white_deer_2":
            sa = s
            break
    if sa:
        out = m._subarea_arrive(p, C.MAP_BY_ID["white_deer"], sa, G, Q)
        has_nav4 = "可前往" in out or "●" in out
        has_fac4 = "🏪 此地设施" in out
        has_npc4 = "👥 这里的 NPC" in out
        print(f"④ 到达视图 有可前往: {has_nav4}, 无设施: {not has_fac4}, 无NPC: {not has_npc4}")

    # ---- ⑤ 关闭赶路模式：地图恢复全量 ----
    db.set_event_state(f"move_mode:{Q}", "")
    db.set_event_state(f"hurry_type:{Q}", "")
    r = await run(m.map_view, FakeEvent(G, Q, "地图"))
    full_has5 = "🏪 此地设施" in r[0] and "👥 这里的 NPC" in r[0]
    print(f"⑤ 关闭赶路 恢复全量: {full_has5}")

    # 清理
    try:
        os.remove(os.path.join(os.path.dirname(os.path.abspath(__file__)), "smoke_v1343_hurry.db"))
    except OSError:
        pass

asyncio.run(_go())
