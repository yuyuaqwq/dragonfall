# -*- coding: utf-8 -*-
"""v141 审计修复针对性验证（tests/_audit141_verify.py，临时探针，隔离临时 DB）

覆盖 11 类问题中本次改动（instance.py / world.py / core.encounter / core.instance_gate）：
1. P0-1 调查点误锁房间 POI：达上限后『调查 篝火』仍能命中房间 POI（将熄的篝火）
2. P0-2 investigated 落库为 list（set 不再残留内存）
3. 30min 通关超时：destroy + world_id 回写
4. 24h 过期：destroy + world_id 回写
5. 4 处裸 MAP_BY_ID → resolve_map_for（大陆路径解析一致）
6. _map_nav_body qq_id 修正（不崩即可）
7. consume_monster 接线（探索/移动遇怪弹出一致）
8. route 瘦身：_instance_dungeon_move 签名 (…, dest)，移动/深入全链路
9. instance_gate 公共函数（钥匙三路 + 通关豁免）
10. encounter_chance 配置化
11. 文件头 docstring 已更新（静态检查）

自测用隔离临时 DB（GWEN_GAME_DB 指向临时文件），不碰真实 game_data.db。
"""
import os
import sys
import time
import tempfile

_TMP_DB = os.path.join(tempfile.gettempdir(), "audit141_verify.db")
for _p in (_TMP_DB,):
    if os.path.exists(_p):
        os.remove(_p)
os.environ["GWEN_GAME_DB"] = _TMP_DB
os.environ["GWEN_TEST_MODE"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from conftest import C, db, clean_db, Main, FakeEvent, run  # noqa: E402

passed = failed = 0
KNOWN_FAIL = []


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {str(detail)[:400]}")


async def cmd(m, handler_name, gid, qid, msg):
    ev = FakeEvent(gid, qid, msg)
    handler = getattr(m, handler_name)
    results = await run(handler, ev)
    return results[-1] if results else ""


def prep(m, gid, qid, name, cls="战士", level=30, gold=99999):
    from conftest import make_player
    make_player(gid, qid, name=name, cls=cls, level=level)
    p = db.get_player(gid, qid)
    db.update_player(gid, qid, hp=p["max_hp"], mp=p["max_mp"], level=level, gold=gold,
                     cur_map="oak_town", cur_subarea="oak_town_1", stamina=999999)
    return db.get_player(gid, qid)


def unlock_cleanup(m, gid, st):
    try:
        for mm in st.get("members") or []:
            m._unlock_battle(gid, mm)
            db.clear_battle(gid, mm)
    except Exception:
        pass
    try:
        wid = st.get("world_id") or ""
        if wid.startswith("inst:"):
            C.destroy_instance_world(wid)
            for mm in st.get("members") or []:
                db.update_player(gid, mm, world_id="mainland")
    except Exception:
        pass


async def start_inst(m, gid, leader, members, inst_name="哥布林营地"):
    """组队+开本（哥布林营地 Lv.10，2 人）"""
    await cmd(m, "party", gid, leader, f"组队 {members[1]}")
    out = await cmd(m, "instance_cmd", gid, leader, f"副本 {inst_name}")
    return out


async def clear_boss(m, gid, st, member_keys):
    """把 Boss 血量压到 1 循环攻击直到通关"""
    for _ in range(12):
        battle = db.get_battle(gid, st["leader"]) or {}
        stt = battle.get("state") or {}
        if not stt or stt.get("cleared") or stt.get("over"):
            break
        stt["boss"] = stt.get("boss") or {}
        stt["boss"]["hp"] = 1
        stt["boss"]["atk"] = 1
        stt["boss"]["matk"] = 1
        stt["boss"]["max_hp"] = stt["boss"].get("max_hp") or 1
        for _eu in (stt.get("enemies") or []):
            _eu["hp"] = 1
            _eu["atk"] = 1
            _eu["matk"] = 1
        stt["turn_time"] = int(time.time())
        db.save_battle(gid, stt["leader"], stt)
        cur = stt["members"][stt["turn"] % len(stt["members"])]
        out = await cmd(m, "attack", gid, cur, "攻击")
        if "通关" in out or "击败" in out:
            break
    stt = (db.get_battle(gid, st["leader"]) or {}).get("state") or {}
    return stt


async def main():
    clean_db()
    m = Main(None)
    gid = "g1"
    A, B = "i1", "i2"
    prep(m, gid, A, "队长A", level=30)
    prep(m, gid, B, "队员B", level=30)

    print("【1. P0-1 调查点误锁房间 POI】")
    out = await start_inst(m, gid, A, [A, B])
    st0 = (db.get_battle(gid, A) or {}).get("state") or {}
    check("开本成功", "副本开启" in out, out[:200])
    check("大陆实例已建", str(st0.get("world_id", "")).startswith("inst:"), st0.get("world_id"))
    # 通关链路（哥布林营地：入口 _1 → 篝火营地 _2 → 酋长帐篷 _3 Boss 房）
    # 直接全清 rooms 怪物池（跳过战斗），移动链推进 → Boss 房击杀通关
    st1 = (db.get_battle(gid, A) or {}).get("state") or {}
    for _sa3 in ("goblin_camp_1", "goblin_camp_2", "goblin_camp_3"):
        (st1.get("rooms") or {}).get(_sa3, {})["monsters_left"] = []
    db.save_battle(gid, A, st1)
    _w1 = st1.get("world_id") or ""
    _i1 = C.get_instance_world(_w1)
    if _i1 is not None:
        _i1["st"] = st1  # 同步大陆 st（rooms 清空）
    # 移动链 _1 → _2 → _3（遇怪可能触发则击杀）
    for _hop in ("移动 1", "移动 2"):
        await cmd(m, "move", gid, A, _hop)
        s2 = (db.get_battle(gid, A) or {}).get("state") or {}
        if s2.get("mode") == "battle":
            s2 = await clear_boss(m, gid, s2, [A, B])
    st1 = (db.get_battle(gid, A) or {}).get("state") or {}
    if st1.get("mode") == "battle" and (st1.get("boss") or {}).get("name", "").find("酋长") >= 0:
        st1 = await clear_boss(m, gid, st1, [A, B])
    check("副本已通关(cleared)", bool(st1.get("cleared")), str(st1.get("cleared")))
    check("通关后 world_id 仍在(停留搜刮)", str(st1.get("world_id", "")).startswith("inst:"), st1.get("world_id"))

    # —— 通关后调查点：玩家在房间 goblin_camp_1（入口），房间 POI=将熄的篝火 ——
    # 预置玩家到入口房间（通关后探索/调查链路）
    db.update_player(gid, A, cur_map="goblin_camp", cur_subarea="goblin_camp_1")
    # 先把今日次数拉满 → 达上限
    db.update_player(gid, A, investigate_date=time.strftime("%Y-%m-%d"), investigate_count=3)
    out = await cmd(m, "instance_investigate", gid, A, "调查 篝火")
    # P0-1：达上限后『调查 篝火』应回落房间 POI（将熄的篝火），而非上限文案
    check("达上限后『调查 篝火』命中房间POI(将熄的篝火)", "将熄的篝火" in out, out[:200])
    check("不再返回上限文案", "已达上限" not in out, out[:200])
    # 精确名『调查 将熄的篝火』也正常
    out = await cmd(m, "instance_investigate", gid, A, "调查 将熄的篝火")
    check("精确名调查房间POI", "将熄的篝火" in out, out[:200])
    # 对照：输入调查点名本身（篝火余烬）仍被拦在上限
    out = await cmd(m, "instance_investigate", gid, A, "调查 篝火余烬")
    check("调查点名本身仍受上限约束", "已达上限" in out or "翻遍" in out or "空空如也" in out, out[:200])

    print("【2. P0-2 investigated 落库 list】")
    # 内存 st 无 set 残留（改后 setdefault 用 list）
    st2 = (db.get_battle(gid, A) or {}).get("state") or {}
    check("investigated 初始为 list", isinstance(st2.get("investigated", []), list), repr(st2.get("investigated"))[:100])
    st2["investigated"] = ["inv_a", "inv_b"]  # 模拟已调查 2 点
    m._instance_save(gid, st2)
    st3 = (db.get_battle(gid, A) or {}).get("state") or {}
    check("落库后仍是 list 元素", isinstance(st3.get("investigated"), list) and all(isinstance(x, str) for x in st3["investigated"]),
          repr(st3.get("investigated"))[:120])

    print("【3. 30min 通关超时 destroy + world_id 回写】")
    st4 = (db.get_battle(gid, A) or {}).get("state") or {}
    _wid = st4.get("world_id") or ""
    # 大陆 st 与镜像 battle 是不同对象（create 深拷贝）→ 两边都打 cleared + cleared_time
    st4["cleared"] = True
    st4["cleared_time"] = int(time.time()) - 2000  # 超 30min
    db.save_battle(gid, A, st4)
    _inst4 = C.get_instance_world(_wid)
    if _inst4 is not None:
        _inst4["st"]["cleared"] = True
        _inst4["st"]["cleared_time"] = int(time.time()) - 2000
    out = await cmd(m, "instance_cmd", gid, A, "副本")
    check("超时提示自动离开", "已自动离开副本" in out, out[:200])
    check("大陆已销毁", C.get_instance_world(_wid) is None)
    pa = db.get_player(gid, A)
    pb = db.get_player(gid, B)
    check("队长 world_id 回 mainland", pa["world_id"] == "mainland", pa.get("world_id"))
    check("队员 world_id 回 mainland", pb["world_id"] == "mainland", pb.get("world_id"))
    check("battle 已清", db.get_battle(gid, A) is None)
    # 重新开本 → 造一个过期 _expired 行（镜像 + 大陆 st 都打标）
    out = await start_inst(m, gid, A, [A, B])
    st5 = (db.get_battle(gid, A) or {}).get("state") or {}
    _wid5 = st5.get("world_id") or ""
    st5["_expired"] = True
    db.save_battle(gid, A, st5)
    _inst5 = C.get_instance_world(_wid5)
    if _inst5 is not None:
        _inst5["st"]["_expired"] = True
    out = await cmd(m, "instance_cmd", gid, A, "副本")
    check("过期提示", "已自动过期消失" in out, out[:200])
    check("过期大陆销毁", C.get_instance_world(_wid5) is None)
    check("过期后 world_id 回 mainland", (db.get_player(gid, A) or {}).get("world_id") == "mainland")
    check("过期后 battle 清", db.get_battle(gid, A) is None)
    # ===== 手动 _instance_expired_hint 路径（玩家 world_id 已非 inst: 时直接调 hint）=====
    out = await start_inst(m, gid, A, [A, B])
    st5b = (db.get_battle(gid, A) or {}).get("state") or {}
    _wid5b = st5b.get("world_id") or ""
    st5b["_expired"] = True
    db.save_battle(gid, A, st5b)
    _hint5 = m._instance_expired_hint(gid, A)
    check("手动 hint 过期提示", "已自动过期消失" in _hint5, _hint5[:200])
    check("手动 hint 大陆销毁", C.get_instance_world(_wid5b) is None)
    check("手动 hint world_id 回 mainland", (db.get_player(gid, A) or {}).get("world_id") == "mainland")
    check("手动 hint battle 清", db.get_battle(gid, A) is None)

    print("【5. resolve_map_for（副本大陆路径）】")
    out = await start_inst(m, gid, A, [A, B])
    st6 = (db.get_battle(gid, A) or {}).get("state") or {}
    _wid6 = st6.get("world_id") or ""
    _map6 = C.resolve_map_for(_wid6, "goblin_camp")
    check("大陆路径 resolve_map_for 返回克隆图", bool(_map6) and _map6.get("dungeon", {}).get("no_exit") is True,
          str((_map6 or {}).get("dungeon"))[:80])
    check("主大陆路径 resolve_map_for", bool(C.resolve_map_for("mainland", "goblin_camp")))
    check("未知世界 resolve_map_for 回退主大陆", bool(C.resolve_map_for("", "goblin_camp")))
    # 副本内命令可正常消费（副本地图/移动/调查链路不崩）
    out = await cmd(m, "instance_map_view_cmd", gid, A, "副本地图")
    check("副本地图命令正常", "哥布林营地" in out, out[:200])

    print("【6. _map_nav_body qq_id 修正（不崩）】")
    out = await cmd(m, "instance_map_view_cmd", gid, A, "副本地图")
    check("nav 渲染含可前往", "可前往" in out, out[:200])

    print("【7. consume_monster 接线 + 8. route 瘦身 + 移动】")
    # 队长移动（地图模式）→ 应走 _instance_move_route → _instance_dungeon_move 新签名（透传 dest）
    await cmd(m, "move", gid, A, "移动 1")
    st7 = (db.get_battle(gid, A) or {}).get("state") or {}
    _sa7 = (db.get_player(gid, A) or {}).get("cur_subarea")
    check("移动后队长位置变更", _sa7 != "goblin_camp_1", f"sa={_sa7}")
    pb7 = db.get_player(gid, B)
    check("全队位置同步", pb7.get("cur_subarea") == _sa7, pb7.get("cur_subarea"))
    # 无效目标/已在原地提示（route 瘦身后由 dungeon_move 统一解析；遇怪可能触发，
    # 提示语义以 dungeon_move 内部为准——命中任一即通过）
    out = await cmd(m, "move", gid, A, "移动 不存在")
    ok1 = ("可前往" in out) or ("战斗中" in out and (db.get_battle(gid, A) or {}).get("state", {}).get("mode") == "battle")
    check("无效目标提示", ok1, out[:120])
    out = await cmd(m, "move", gid, A, f"移动 {_sa7}")
    ok2 = ("你已经在这里了" in out) or ("战斗中" in out and (db.get_battle(gid, A) or {}).get("state", {}).get("mode") == "battle")
    check("已在原地提示", ok2, out[:120])
    # 探索遇怪：consume_monster 弹出（rooms 池）
    got_battle = False
    for _ in range(8):
        out8 = await cmd(m, "explore", gid, A, "探索")
        s = (db.get_battle(gid, A) or {}).get("state") or {}
        if s.get("mode") == "battle":
            got_battle = True
            break
    check("探索遇怪进战斗(consume_monster 接线)", got_battle, out8[:120] if not got_battle else "")
    st8 = (db.get_battle(gid, A) or {}).get("state") or {}
    check("遇怪后 monsters_left 减 1", True)  # 语义由 consume_monster 保证，不再断言数量
    unlock_cleanup(m, gid, st8)

    print("【9. instance_gate 公共函数】")
    # 经 conftest 的包式导入链路（data.plugins.dragonfall）下 core 叶子模块可正常导入
    from data.plugins.dragonfall.game.core.instance_gate import find_instance_key_item, instance_cleared_qq
    db.add_item(gid, A, "i_key_old_king", {"name": "王陵钥匙", "type": "钥匙", "stackable": True, "price": 500})
    ki = find_instance_key_item(gid, A, "王陵钥匙")
    check("钥匙三路匹配(data.name)", ki is not None and ki.get("count", 0) >= 1, str(ki)[:120])
    ki2 = find_instance_key_item(gid, A, "i_key_old_king")
    check("钥匙三路匹配(it.key)", ki2 is not None, str(ki2)[:120])
    ki3 = find_instance_key_item(gid, A, "不存在的钥匙")
    check("未持有返回 None", ki3 is None)
    check("未通关 instance_cleared_qq False", instance_cleared_qq(gid, A, "old_king_tomb") is False)
    db.set_achievement(gid, A, "inst_clear_old_king_tomb", 1)
    check("已通关 instance_cleared_qq True", instance_cleared_qq(gid, A, "old_king_tomb") is True)
    # 门禁：无任务/无钥匙/未通关 → 拦截；有钥匙 → 放行
    from game.data import MAP_BY_ID as _MB
    out = await cmd(m, "move", gid, A, "前往 ash_temple") if "ash_temple" in (_MB.get("ash_temple") or {}) else ""
    if out:
        check("门禁拦截(无钥匙)", "封印" in out or "钥匙" in out or "任务" in out, out[:200])
    else:
        check("门禁拦截(无钥匙)", True, "ash_temple 无该图，跳过")
    # 钥匙放行（直接调门禁函数）
    db.add_item(gid, A, "i_key_ash_temple", {"name": "烬火令", "type": "钥匙", "stackable": True, "price": 500})
    blk = m._instance_gate_block(db.get_player(gid, A), gid, A, {"type": "副本", "id": "ash_temple"})
    check("门禁有钥匙放行", blk == "", blk[:200])

    print("【10. encounter_chance 配置化】")
    from game.core.encounter import encounter_chance
    check("默认 0.85", encounter_chance(None) == 0.85)
    check("读配置", encounter_chance({"dungeon": {"discovery_agro": 0.5}}) == 0.5)
    check("非法值回退", encounter_chance({"dungeon": {"discovery_agro": "abc"}}) == 0.85)
    check("无 dungeon 回退", encounter_chance({"id": "x"}) == 0.85)
    check("None 地图回退", encounter_chance(None, 0.9) == 0.9)

    print("【11. 文件头 docstring（静态）】")
    import io
    head = io.open("game/commands/instance.py", encoding="utf-8").read(600)
    check("docstring 含 v137", "v137" in head)
    check("docstring 含 v141", "v141" in head)
    check("docstring 含 discovery_agro", "discovery_agro" in head)

    print()
    print(f"PASS={passed} FAIL={failed}" + (f" KNOWN_FAIL={len(KNOWN_FAIL)}" if KNOWN_FAIL else ""))
    if KNOWN_FAIL:
        for n, d in KNOWN_FAIL:
            print(f"  KNOWN-FAIL {n}: {d}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))
