# -*- coding: utf-8 -*-
"""5c 端到端验收：真实副本流程 Boss 战触发剧本导演（哥布林营地·咕噜）。

覆盖（验证导演在真实命令层链路工作，非单测）：
1. 开本 → 清房 → 移动 → Boss 房 → Boss 战（玩家真实操作 attack）
2. Boss 首帧 opening 触发（phase_open：掠夺号令演出 + bs.flags._open_played）
3. Boss 掉血 <60% → phase_count=1（咕噜抄起酒桌）+ add_skills 换招
4. Boss 掉血 <40% → phase_count=2（酒疯 atk ×1.7——merge normal 模板）
5. 导演状态 st["boss_script"] 在真实副本 st 持久化（大陆权威）

跑法：python tests/test_boss_script_e2e.py（沙箱 data/plugins 父链下）
"""
import sys, os, time, asyncio, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, make_player, Main, FakeEvent, run

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


async def enter_combat(m, gid, qid):
    for _ in range(8):
        out = await cmd(m, "explore", gid, qid, "探索")
        battle = db.get_battle(gid, qid)
        if battle and (battle["state"].get("enemies") or battle["state"].get("boss")):
            return out
    return out


def _authoritative_st(m, gid, qid, battle):
    st = battle["state"]
    _wid = st.get("world_id") or ""
    if str(_wid).startswith("inst:"):
        try:
            _live = C.get_instance_st(_wid)
            if _live is not None:
                return _live
        except Exception:
            pass
    return st


def _set_minions_hp1(st):
    """只压存活爪牙血（死爪牙不复活；Boss 保持真实血量——验证转阶段需 Boss 掉血）。"""
    _bsides = (st.get("battle") or {}).get("sides") or {}
    for _a in (_bsides.get("enemy") or []):
        if _a.get("is_minion") and int(_a.get("hp", 0) or 0) > 0:
            _a["hp"] = 1
            _a["atk"] = 1
            _a["matk"] = 1
    for _eu in (st.get("enemies") or []):
        if _eu.get("is_minion") and int(_eu.get("hp", 0) or 0) > 0:
            _eu["hp"] = 1
            _eu["atk"] = 1
            _eu["matk"] = 1


async def boss_attack_rounds(m, gid, qid, st, max_rounds=40):
    """攻击循环直到 Boss 转阶段（phase_count 目标）或轮次耗尽。返回输出。"""
    from game.commands import instance_battle as _IB
    out = ""
    target_phase = int((st.get("boss_script") or {}).get("phase_count", 0) or 0)
    for _ in range(max_rounds):
        battle = db.get_battle(gid, qid)
        if not battle:
            break
        st = _authoritative_st(m, gid, qid, battle)
        if st.get("over") or st.get("cleared"):
            break
        _set_minions_hp1(st)
        st["turn_time"] = int(time.time())
        try:
            _wid = st.get("world_id") or ""
            if str(_wid).startswith("inst:"):
                db.save_battle(gid, qid, st)
        except Exception:
            pass
        db.save_battle(gid, qid, st)
        cur = st["members"][0]
        try:
            nxt = _IB.next_actor_key(st)
            if nxt:
                cur = nxt
        except Exception:
            pass
        out += "\n" + (await cmd(m, "attack", gid, cur, "攻击"))
        st2 = _authoritative_st(m, gid, qid, db.get_battle(gid, qid)) if db.get_battle(gid, qid) else st
        pc = int((st2.get("boss_script") or {}).get("phase_count", 0) or 0)
        if pc > target_phase:
            break
    return out


def _set_boss_hp(st, ratio):
    """压 Boss 本体血（sides actors + boss/enemies 视图三路）到 max×ratio。"""
    _bsides = (st.get("battle") or {}).get("sides") or {}
    for _a in (_bsides.get("enemy") or []):
        if _a.get("is_boss") and int(_a.get("hp", 0) or 0) > 0:
            _a["hp"] = max(1, int(int(_a.get("max_hp", 1)) * ratio))
    if isinstance(st.get("boss"), dict) and st["boss"].get("hp"):
        st["boss"]["hp"] = max(1, int(int(st["boss"].get("max_hp", 1)) * ratio))
    for _eu in (st.get("enemies") or []):
        if _eu.get("is_boss") and int(_eu.get("hp", 0) or 0) > 0:
            _eu["hp"] = max(1, int(int(_eu.get("max_hp", 1)) * ratio))


def _boss_actor(st):
    """sides enemy 里的 Boss 本体 actor（导演改动落在 actors，视图键不同步）。"""
    for _a in ((st.get("battle") or {}).get("sides") or {}).get("enemy") or []:
        if _a.get("is_boss"):
            return _a
    return {}


async def boss_drive(m, gid, qid, hp_ratio, target_pc, max_rounds=15):
    """压 Boss 血到 ratio → 玩家 attack 驱动直到 phase_count>=target_pc。返回输出+st。"""
    from game.commands import instance_battle as _IB
    out = ""
    for _ in range(max_rounds):
        battle = db.get_battle(gid, qid)
        if not battle:
            break
        st = _authoritative_st(m, gid, qid, battle)
        if st.get("over") or st.get("cleared"):
            break
        _set_minions_hp1(st)
        _set_boss_hp(st, hp_ratio)
        st["turn_time"] = int(time.time())
        try:
            _wid = st.get("world_id") or ""
            if str(_wid).startswith("inst:"):
                db.save_battle(gid, qid, st)
        except Exception:
            pass
        db.save_battle(gid, qid, st)
        cur = st["members"][0]
        try:
            nxt = _IB.next_actor_key(st)
            if nxt:
                cur = nxt
        except Exception:
            pass
        out += "\n" + (await cmd(m, "attack", gid, cur, "攻击"))
        saintess_engine = db.get_battle(gid, qid)
        if not saintess_engine:
            break
        st = _authoritative_st(m, gid, qid, saintess_engine)
        if int((st.get("boss_script") or {}).get("phase_count", 0) or 0) >= target_pc:
            break
    return out, st


async def main():
    clean_db()
    m = Main(None)

    print("【1. 开本 → 清房 → Boss 房】")
    make_player("g1", "q1", cls="战士", level=40)
    p = db.get_player("g1", "q1")
    # 满血高面板：玩家扛 Boss 反击（副本开本会按 DB max_hp 钳制 → max_hp 一起提）
    db.update_player("g1", "q1", hp=999999, mp=p["max_mp"], level=40, gold=5000,
                     max_hp=999999, cur_map="misty_swamp", cur_subarea="misty_swamp_3")
    out = await cmd(m, "instance_cmd", "g1", "q1", "副本 哥布林营地")
    check("开本成功", "副本开启" in out, out[:150])

    # 清房1
    out = await enter_combat(m, "g1", "q1")
    battle = db.get_battle("g1", "q1")
    if battle:
        st = _authoritative_st(m, "g1", "q1", battle)
        from game.commands import instance_battle as _IB
        # 一刀清（压全敌血 1）
        for _ in range(10):
            battle = db.get_battle("g1", "q1")
            if not battle or battle["state"].get("cleared") or battle["state"].get("over"):
                break
            st = _authoritative_st(m, "g1", "q1", battle)
            _bsides = (st.get("battle") or {}).get("sides") or {}
            for _a in (_bsides.get("enemy") or []):
                _a["hp"] = 1
                _a["atk"] = 1
            for _eu in (st.get("enemies") or []):
                _eu["hp"] = 1
            st["turn_time"] = int(time.time())
            db.save_battle("g1", "q1", st)
            cur = st["members"][0]
            try:
                nxt = _IB.next_actor_key(st)
                if nxt:
                    cur = nxt
            except Exception:
                pass
            await cmd(m, "attack", "g1", cur, "攻击")

    # 房2 → Boss 房
    await cmd(m, "move", "g1", "q1", "移动 篝火营地")
    await enter_combat(m, "g1", "q1")
    battle = db.get_battle("g1", "q1")
    if battle:
        st = _authoritative_st(m, "g1", "q1", battle)
        for _ in range(12):
            battle = db.get_battle("g1", "q1")
            if not battle or battle["state"].get("cleared") or battle["state"].get("over"):
                break
            st = _authoritative_st(m, "g1", "q1", battle)
            _bsides = (st.get("battle") or {}).get("sides") or {}
            for _a in (_bsides.get("enemy") or []):
                _a["hp"] = 1
                _a["atk"] = 1
            for _eu in (st.get("enemies") or []):
                _eu["hp"] = 1
            st["turn_time"] = int(time.time())
            db.save_battle("g1", "q1", st)
            from game.commands import instance_battle as _IB
            cur = st["members"][0]
            try:
                nxt = _IB.next_actor_key(st)
                if nxt:
                    cur = nxt
            except Exception:
                pass
            await cmd(m, "attack", "g1", cur, "攻击")
    out = await cmd(m, "move", "g1", "q1", "移动 酋长帐篷")
    check("移动到 Boss 房", "酋长帐篷" in out or "咕噜" in out, out[:200])

    print("【2. Boss 战：首帧 opening + 转阶段】")
    out = await enter_combat(m, "g1", "q1")
    battle = db.get_battle("g1", "q1")
    check("Boss 战触发", battle is not None, "")
    if not battle:
        print("BOSS 战未触发，中止")
        return
    st = _authoritative_st(m, "g1", "q1", battle)
    boss_name = (st.get("boss") or {}).get("name", "")
    check("咕噜登场", "咕噜" in boss_name, boss_name)
    check("开怪爪牙在场（minions 展开）",
          any(u.get("is_minion") for u in (st.get("enemies") or [])),
          str([u.get("name") for u in (st.get("enemies") or [])]))

    # 打 Boss：压血驱动转阶段（opening 已触发；60% 下进阶段 2、40% 下进酒疯）
    out2, st = await boss_drive(m, "g1", "q1", 0.55, 1, max_rounds=15)
    battle = db.get_battle("g1", "q1")
    st = _authoritative_st(m, "g1", "q1", battle) if battle else st
    bs = st.get("boss_script") or {}
    boss = (st.get("boss") or {})
    mh = int(boss.get("max_hp", 1) or 1)
    hp = int(boss.get("hp", 0) or 0)
    check("导演状态已在副本 st（boss_script）", isinstance(bs, dict) and len(bs) > 0,
          str(bs)[:200])
    check("opening once 标记（_open_played）",
          bool((bs.get("flags") or {}).get("_open_played")), str(bs.get("flags"))[:120])
    check("opening 演出输出（气势拉满）", "气势瞬间拉满" in (out2 or out), (out2 or out)[-400:])
    check("Boss 掉血 <60%", mh > 0 and hp / mh < 0.60, f"hp={hp}/{mh}")
    check("触发阶段 2（phase_count>=1）", int(bs.get("phase_count", 0) or 0) >= 1,
          f"phase_count={bs.get('phase_count')}")
    check("阶段演出在输出（抄起酒桌）", "酒桌" in (out2 or out), (out2 or out)[-600:])
    check("Boss 换招（sides actor auto_act 技能）",
          bool(_boss_actor(st).get("auto_act", {}).get("act", {}).get("skill")),
          str(_boss_actor(st).get("auto_act")))
    print("  -- 阶段 2 后 Boss hp:", f"{hp}/{mh}", "| phase_count:", bs.get("phase_count"),
          "| auto_act:", (_boss_actor(st).get("auto_act") or {}).get("act", {}).get("skill"))

    # 40% 下 → 酒疯（merge normal 模板 atk ×1.7）
    out3, st = await boss_drive(m, "g1", "q1", 0.35, 2, max_rounds=15)
    battle = db.get_battle("g1", "q1")
    st = _authoritative_st(m, "g1", "q1", battle) if battle else st
    bs = st.get("boss_script") or {}
    boss = (st.get("boss") or {})
    check("触发酒疯（phase_count>=2）", int(bs.get("phase_count", 0) or 0) >= 2,
          f"phase_count={bs.get('phase_count')}")
    check("酒疯演出在输出（酒疯/双目赤红）",
          "酒疯" in (out3 or "") or "双目赤红" in (out3 or ""), (out3 or out)[-600:])
    ef = _boss_actor(st).get("effects") or {}
    _am = float((ef.get("boss_phase_atk") or {}).get("mult", 0) or 0)
    check("酒疯 atk 乘区 ×1.7（sides actor effects）", abs(_am - 1.7) < 0.001, f"atk_mult={_am}")
    print("  -- 酒疯后 Boss hp:", f"{int(boss.get('hp', 0))}/{int(boss.get('max_hp', 1))}",
          "| phase_count:", bs.get("phase_count"),
          "| atk_mult:", (ef.get("boss_phase_atk") or {}).get("mult"))
    # 清理（防止影响同库其他测试）
    for q in ("q1",):
        m._unlock_battle("g1", q)
        db.clear_battle("g1", q)

    print(f"\n======== 结果: {passed} 通过 / {failed} 失败 ========")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    asyncio.run(main())
