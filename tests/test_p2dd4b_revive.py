# -*- coding: utf-8 -*-
"""v181.P2D-D4b 致死复活族等价探针（test_p2dd4b_revive.py）

验证挂点12 _post_hp_lethal 致死复活链 3 proc（death_contract / berserk_revive /
stance_immortal）从 battle.py 内联 for 迁移到 passive_procs 注册表族 revive_cond
（ctx revive_kind 分派 death_pact_cond/berserk/stance）后行为零变化
（OLD vs NEW 双实现差分 + 顺序链 + 一次性 flag 序列化）。

方法（方案 §7 OLD-vs-NEW 探针）：
1. OLD = 迁移前 _post_hp_lethal 致死复活链 3 for 循环体逐字复刻（4713029^）。
2. NEW = 现引擎 _post_hp_lethal（武器特效/不死鸟段在构造 actor 下惰性，3 段走注册表）。
3. 差分矩阵（每 proc 致死场景，学/不学 × 条件边界 × 每场 flag 已用/未用）：
   - death_contract：信念 4/5/6 × 存活骷髅 0/1/2 × flag 预置 True/False
     （复活 hp=max_hp×0.20；无骷髅仅日志不消耗契约；flag 已用 → 不触发）
   - berserk_revive：狂暴态（v139_modes dual_form alt）× flag × 战意清空语义
   - stance_immortal：守护姿态（buffs.stance_guard）× flag × 姿态移除 + 战意清空
   - 顺序链：合成三 proc 同挂（dc 先于 berserk 先于 stance——谁先触发谁生效；
     dc 失败（无骷髅）→ berserk 接棒；非狂暴 → stance 接棒）
   - 序列化 flag 恢复：battle 属性预置 _death_pact_used/_berserk_revive_used/
     _stance_immortal_used（等价 from_state 恢复）后同场二次致死不触发
   - 同一场战斗两次致死：第二次（flag 已置）不复活，hp 保持 0

致死场景说明：_post_hp_lethal 在扣血后调用（actor.hp 已 ≤0 才进复活链）——探针把 hp
直接置 0（模拟扣血后致死态），dmg 参数仅为挂点签名（复活段不消费 dmg）。
Battle.__init__ 会把 player.max_hp 重算为实时面板值（mk_player 初值 500 仅占位）——
探针一律不硬编码复活数值，断言两路状态一致 + 关键语义（>0 复活/0 未复活 + 骷髅牺牲/
宠物留场/姿态移除/战意清空 + flag 置位），绝对数值由特写场景动态取 b.player.max_hp 锁定。

运行（与门禁同款 python）：
  python tests/test_p2dd4b_revive.py
"""
import os
import sys
import copy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db  # noqa: E402
from data.plugins.dragonfall.game import engine as EG  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402
from data.plugins.dragonfall.game.core import passive_procs as PP  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def mk_player(cls_id, passives, hp=500):
    """构造战斗玩家 dict（学指定被动中文名）。"""
    out = {
        "class_name": cls_id, "level": 60, "hp": hp, "max_hp": hp,
        "mp": 100, "max_mp": 200,
        "equipment": {"weapon": {"name": "t", "stats": {"atk": 100, "matk": 100, "spd": 100},
                                 "affixes": [], "enhance": 0}},
        "attributes": {"str": 10, "int": 10},
        "learned_skills": list(passives), "race": "human",
        "resources": {}, "stacks": {}, "buffs": {}, "eff": {},
    }
    return out


def mk_enemy(def_=20, mdef=20, hp=100000, spd=10):
    return {"name": "测试怪", "hp": hp, "max_hp": hp,
            "atk": 50, "def": def_, "mdef": mdef, "spd": spd}


def mk_battle(player, enemy=None):
    """构造战斗（深拷贝防 Battle 内 setdefault 污染 OLD 参考源）。"""
    b = BT.Battle("monster", enemy or mk_enemy(), {}, copy.deepcopy(player))
    b.player.setdefault("resources", {})
    b.player.setdefault("stacks", {})
    b.player.setdefault("buffs", {})
    b.player.setdefault("shields", {})
    b.player.setdefault("eff", {})
    b.player.setdefault("v139_modes", {})
    return b


def mk_skeleton(name="骷髅", hp=50, kind="summon", tid="skeleton"):
    return {"name": name, "tid": tid, "kind": kind, "hp": hp, "max_hp": hp,
            "side": "player", "buffs": {}}


def _state_of(b, actor):
    """NEW vs OLD 可比状态快照。"""
    return (actor.get("hp", 0),
            bool(getattr(b, "_death_pact_used", False)),
            bool(getattr(b, "_berserk_revive_used", False)),
            bool(getattr(b, "_stance_immortal_used", False)),
            [(c.get("name"), c.get("tid"), c.get("hp", 0)) for c in (b.companions or [])],
            (actor.setdefault("stacks", {})).get("zhan_yi", None),
            "stance_guard" in (actor.setdefault("buffs", {})),
            (actor.setdefault("resources", {})).get("faith", None))


# ============================================================
# OLD：迁移前 _post_hp_lethal 致死复活链 3 段（4713029^ 逐字复刻，含 v107 death_pact 旧段）
# ============================================================
def OLD_lethal(b, actor, dmg, logs):
    """迁移前 _post_hp_lethal 三段逐字复刻（不含武器特效/不死鸟——构造 actor 惰性）。"""
    B = actor.setdefault("buffs", {})
    RES = actor.setdefault("resources", {})
    MS = actor.setdefault("stacks", {})
    # ---- v107 死亡契约（暗影祭司旧段，proc death_pact）----
    if actor["hp"] <= 0 and b.summons and not b._death_pact_used:
        for _pn, _ps in b._passive_map(actor)["proc"].get("death_pact", []):
            b._death_pact_used = True
            _sacrifice_pool = [c for c in b.companions if c.get("kind") == "summon"]
            fallen = _sacrifice_pool.pop() if _sacrifice_pool else None
            if fallen is None:
                b._death_pact_used = False
                break
            b.companions.remove(fallen)
            actor["hp"] = max(1, int(actor.get("max_hp", actor["hp"]) * 0.20))
            logs.append(f"💀 死亡契约！{fallen.get('name', '亡灵')} 替你承受了致命一击，你以 {actor['hp']} HP 站起！")
            break
    # ---- v169.7 死亡契约（牧师死灵线，proc death_contract）----
    if actor["hp"] <= 0 and not b._death_pact_used:
        try:
            _faith_v = float(RES.get("faith", 0) or 0)
            _skels = [s for s in b.summons if s.get("tid") == "skeleton" and s.get("hp", 0) > 0]
            for _pn, _ps in b._passive_map(actor)["proc"].get("death_contract", []):
                if _faith_v < float(_ps.get("faith_req", 5) or 5):
                    continue
                if not _skels:
                    logs.append("💀 死亡契约：信念已足但没有骷髅代受致命一击！")
                    continue
                b._death_pact_used = True
                fallen = _skels.pop()
                b.companions.remove(fallen)
                actor["hp"] = max(1, int(actor.get("max_hp", actor["hp"]) * float(_ps.get("hp_pct", 0.20) or 0.20)))
                logs.append(f"💀 死亡契约：信念 {_faith_v:.0f} 引动契约，{fallen.get('name', '骷髅')} 代受致命伤，你以 {actor['hp']} HP 站起！")
                break
        except Exception:
            pass
    # ---- v169.7 血怒·不灭（proc berserk_revive）----
    if actor["hp"] <= 0 and not getattr(b, "_berserk_revive_used", False):
        try:
            from data.plugins.dragonfall.game.core.battle_modes import dual_form_active as _dfa169
            if _dfa169(actor):
                for _pn, _ps in b._passive_map(actor)["proc"].get("berserk_revive", []):
                    b._berserk_revive_used = True
                    MS["zhan_yi"] = 0
                    actor["hp"] = max(1, int(actor.get("max_hp", actor.get("hp", 1)) * float(_ps.get("hp_pct", 0.30) or 0.30)))
                    logs.append(f"🔥 血怒·不灭！狂暴意志撑住了致命一击，你以 {actor['hp']} HP 站起（战意已清空）！")
                    break
        except Exception:
            pass
    # ---- v169.7 铁誓·不动（proc stance_immortal）----
    if actor["hp"] <= 0 and not getattr(b, "_stance_immortal_used", False) and B.get("stance_guard"):
        try:
            for _pn, _ps in b._passive_map(actor)["proc"].get("stance_immortal", []):
                b._stance_immortal_used = True
                B.pop("stance_guard", None)
                MS["zhan_yi"] = 0
                actor["hp"] = max(1, int(actor.get("max_hp", actor.get("hp", 1)) * float(_ps.get("hp_pct", 1.0) or 1.0)))
                logs.append(f"🛡️ 铁誓·不动！守护姿态替你挡下致命一击（战意已清空）！")
                break
        except Exception:
            pass
    return actor


def _run_lethal_pair(player, setup, dmg=99999):
    """同一 setup 跑 OLD 链副本 vs NEW _post_hp_lethal 全链，返回 (同否, OLD状态, NEW状态)。

    setup 内把 actor 置致死态 hp<=0（_post_hp_lethal 在扣血后调用）。
    """
    b_old = mk_battle(dict(player), mk_enemy())
    b_new = mk_battle(dict(player), mk_enemy())
    for b in (b_old, b_new):
        setup(b)
        b.player["hp"] = 0  # 致死态（扣血后 hp 已 ≤0 才进复活链）
    logs_o, logs_n = [], []
    OLD_lethal(b_old, b_old.player, dmg, logs_o)
    b_new._post_hp_lethal(b_new.player, dmg, logs_n)
    same = (_state_of(b_old, b_old.player) == _state_of(b_new, b_new.player)
            and logs_o == logs_n)
    return same, (_state_of(b_old, b_old.player), logs_o), (_state_of(b_new, b_new.player), logs_n)


def _inject(b, proc_keys):
    """合成 pm：把指定 proc 条目全注入玩家 pm（跨职业同挂——顺序链探针用）。

    OLD（_passive_map）/NEW（_passive_map）都走合成 pm 才是公平对比——挂点12 的 for
    遍历用 _passive_map；_proc_pm 同换防其它消费（hp 重算等不涉及）。
    proc_keys 传 proc 键（death_contract/berserk_revive/stance_immortal）。
    """
    pm = b._proc_pm(b.player)
    base = dict(pm)
    base.setdefault("proc", {})
    for pn in proc_keys:
        if pn in base["proc"] and base["proc"][pn]:
            continue
        if pn == "death_contract":
            base["proc"][pn] = [("死亡契约", {"proc": "death_contract", "faith_req": 5, "hp_pct": 0.20})]
        elif pn == "berserk_revive":
            base["proc"][pn] = [("血怒·不灭", {"proc": "berserk_revive", "hp_pct": 0.30})]
        elif pn == "stance_immortal":
            base["proc"][pn] = [("铁誓·不动", {"proc": "stance_immortal", "hp_pct": 1.0})]
    b._proc_pm = lambda pl: base
    b._passive_map = lambda pl: base
    return b


# ============================================================
# 1. death_contract（信念≥5 牺牲骷髅复活 20%；flag 共享 _death_pact_used）
# ============================================================
def test_death_contract():
    print("\n== 1. death_contract（挂点12 → revive_cond death_pact_cond）OLD vs NEW ==")
    for learned in (False, True):
        for faith in (4, 5, 6):
            for n_skel in (0, 1, 2):
                for flag in (False, True):
                    p = mk_player("cls_mu_shi", ["死亡契约"] if learned else [])
                    comps = [mk_skeleton(f"骷髅{i}", hp=50) for i in range(n_skel)]
                    # 宠物（kind=pet）绝不作为祭品（v180-C S3）
                    comps.append(mk_skeleton("宠物", hp=200, kind="pet", tid="pet_tiger"))
                    def setup(b, comps=comps, faith=faith, flag=flag):
                        b.player["resources"]["faith"] = faith
                        b.companions = [dict(c) for c in comps]
                        if flag:
                            b._death_pact_used = True  # 模拟 from_state 恢复已用
                    same, st_o, st_n = _run_lethal_pair(p, setup)
                    tag = f"学={learned} 信念{faith} 骷髅{n_skel} flag已用={flag}"
                    check(f"{tag}: 状态/logs 一致",
                          same, f"OLD{st_o} NEW{st_n}")
                    if learned and faith >= 5 and not flag and n_skel >= 1:
                        # 复活 hp>0（两路一致）；牺牲 1 骷髅（n_skel-1 骷髅剩 + 宠物必留场）
                        check(f"  {tag}: 复活+牺牲1骷髅+宠物留",
                              st_o[0][0] == st_n[0][0] and st_o[0][0] > 0
                              and len(st_o[0][4]) == n_skel and len(st_n[0][4]) == n_skel
                              and st_o[0][4][-1][1] == "pet_tiger"
                              and st_n[0][4][-1][1] == "pet_tiger",
                              f"OLD hp={st_o[0][0]} comps={st_o[0][4]} NEW hp={st_n[0][0]} comps={st_n[0][4]}")
    # 特写断言（独立构造 NEW 验复活数值/牺牲对象/宠物留场）——数值以 battle 重算 max_hp 为口径
    p = mk_player("cls_mu_shi", ["死亡契约"])
    b = mk_battle(dict(p), mk_enemy())
    _maxhp = int(b.player["max_hp"])
    b.player["resources"]["faith"] = 5
    b.companions = [mk_skeleton("骷髅A"), mk_skeleton("骷髅B", kind="pet", tid="pet_x")]
    b.player["hp"] = 0
    logs = []
    b._post_hp_lethal(b.player, 99999, logs)
    comps_after = b.companions
    check(f"复活 hp = max_hp×0.20 = {max(1, int(_maxhp*0.20))}", b.player["hp"] == max(1, int(_maxhp * 0.20)),
          f"hp={b.player['hp']} max_hp={_maxhp}")
    check("牺牲尾骷髅（骷髅A）离场，宠物留场",
          len(comps_after) == 1 and comps_after[0]["tid"] == "pet_x"
          and comps_after[0]["kind"] == "pet", str(comps_after))
    check("flag _death_pact_used 置位", getattr(b, "_death_pact_used", False) is True)
    check("复活日志含 死亡契约", any("死亡契约" in s and "站起" in s for s in logs), str(logs))
    # 无骷髅：信念已足 → 日志提示，不消耗契约、不复活（后续链无接棒 → hp 保持 0）
    b2 = mk_battle(dict(p), mk_enemy())
    b2.player["resources"]["faith"] = 5
    b2.player["hp"] = 0
    logs2 = []
    b2._post_hp_lethal(b2.player, 99999, logs2)
    check("无骷髅 → 不复活 hp=0 + 提示日志 + 不消耗契约",
          b2.player["hp"] == 0 and not getattr(b2, "_death_pact_used", False)
          and any("没有骷髅" in s for s in logs2), f"hp={b2.player['hp']} flag={getattr(b2,'_death_pact_used',False)} logs={logs2}")
    # 信念不足：无日志、不复活
    b3 = mk_battle(dict(p), mk_enemy())
    b3.player["resources"]["faith"] = 4
    b3.companions = [mk_skeleton("骷髅A")]
    b3.player["hp"] = 0
    logs3 = []
    b3._post_hp_lethal(b3.player, 99999, logs3)
    check("信念4 <5 → 不触发 hp=0 无日志", b3.player["hp"] == 0 and not logs3,
          f"hp={b3.player['hp']} logs={logs3}")
    # 同场二次致死：flag 已置 → 不复活
    b4 = mk_battle(dict(p), mk_enemy())
    b4.player["resources"]["faith"] = 5
    b4.companions = [mk_skeleton("骷髅A")]
    b4.player["hp"] = 0
    b4._post_hp_lethal(b4.player, 99999, [])
    b4.player["hp"] = 0
    logs4 = []
    b4._post_hp_lethal(b4.player, 99999, logs4)
    check("同场二次致死（flag 已用）→ 不复活 hp=0 无日志", b4.player["hp"] == 0 and not logs4,
          f"hp={b4.player['hp']} logs={logs4}")
    # 未学被动：无 proc 条目 → 不触发（死亡契约 proc 无条目段空转）
    p0 = mk_player("cls_mu_shi", [])
    b0 = mk_battle(dict(p0), mk_enemy())
    b0.player["resources"]["faith"] = 5
    b0.companions = [mk_skeleton("骷髅A")]
    b0.player["hp"] = 0
    logs0 = []
    b0._post_hp_lethal(b0.player, 99999, logs0)
    check("未学死亡契约 → 不触发 hp=0 无日志", b0.player["hp"] == 0 and not logs0,
          f"hp={b0.player['hp']} logs={logs0}")


# ============================================================
# 2. berserk_revive（狂暴态首次致死 30% 复活 + 清空战意）
# ============================================================
def test_berserk_revive():
    print("\n== 2. berserk_revive（挂点12 → revive_cond berserk）OLD vs NEW ==")
    for learned in (False, True):
        for alt in (False, True):
            for zy in (0, 5, 10):
                for flag in (False, True):
                    p = mk_player("cls_zhan_shi", ["血怒·不灭"] if learned else [])
                    def setup(b, alt=alt, zy=zy, flag=flag):
                        b.player["stacks"]["zhan_yi"] = zy
                        if alt:
                            b.player["v139_modes"] = {"dual_form": {"form": "alt", "turns_left": 5}}
                        if flag:
                            b._berserk_revive_used = True
                    same, st_o, st_n = _run_lethal_pair(p, setup)
                    tag = f"学={learned} 狂暴={alt} 战意{zy} flag已用={flag}"
                    check(f"{tag}: 状态/logs 一致", same, f"OLD{st_o} NEW{st_n}")
    # 特写：狂暴首次致死 → 30% 复活 + 战意清 0 + flag 置位
    p = mk_player("cls_zhan_shi", ["血怒·不灭"])
    b = mk_battle(dict(p), mk_enemy())
    _maxhp = int(b.player["max_hp"])
    b.player["stacks"]["zhan_yi"] = 7
    b.player["v139_modes"] = {"dual_form": {"form": "alt"}}
    b.player["hp"] = 0
    logs = []
    b._post_hp_lethal(b.player, 99999, logs)
    check(f"狂暴致死 → 复活 hp = max_hp×0.30 = {max(1,int(_maxhp*0.30))}",
          b.player["hp"] == max(1, int(_maxhp * 0.30)), f"hp={b.player['hp']} max_hp={_maxhp}")
    check("战意清空 zhan_yi==0", b.player["stacks"]["zhan_yi"] == 0, str(b.player["stacks"]))
    check("flag _berserk_revive_used 置位", getattr(b, "_berserk_revive_used", False) is True)
    check("日志含 血怒·不灭", any("血怒·不灭" in s for s in logs), str(logs))
    # 非狂暴态致死：不触发（无接棒）hp=0 无日志
    b2 = mk_battle(dict(p), mk_enemy())
    b2.player["stacks"]["zhan_yi"] = 7
    b2.player["hp"] = 0
    logs2 = []
    b2._post_hp_lethal(b2.player, 99999, logs2)
    check("非狂暴 → 不触发 hp=0 无日志", b2.player["hp"] == 0 and not logs2,
          f"hp={b2.player['hp']} logs={logs2}")
    # 同场二次致死（flag 已用）→ 不触发
    b3 = mk_battle(dict(p), mk_enemy())
    b3.player["stacks"]["zhan_yi"] = 10
    b3.player["v139_modes"] = {"dual_form": {"form": "alt"}}
    b3.player["hp"] = 0
    b3._post_hp_lethal(b3.player, 99999, [])
    b3.player["hp"] = 0
    logs3 = []
    b3._post_hp_lethal(b3.player, 99999, logs3)
    check("二次致死（flag 已用）→ 不复活 hp=0", b3.player["hp"] == 0 and not logs3,
          f"hp={b3.player['hp']} logs={logs3}")


# ============================================================
# 3. stance_immortal（守护姿态首次致命免疫回满 + 清姿态清战意）
# ============================================================
def test_stance_immortal():
    print("\n== 3. stance_immortal（挂点12 → revive_cond stance）OLD vs NEW ==")
    for learned in (False, True):
        for guard in (False, True):
            for zy in (0, 5, 10):
                for flag in (False, True):
                    p = mk_player("cls_zhan_shi", ["铁誓·不动"] if learned else [])
                    def setup(b, guard=guard, zy=zy, flag=flag):
                        b.player["stacks"]["zhan_yi"] = zy
                        if guard:
                            b.player["buffs"]["stance_guard"] = 1
                        if flag:
                            b._stance_immortal_used = True
                    same, st_o, st_n = _run_lethal_pair(p, setup)
                    tag = f"学={learned} 守护={guard} 战意{zy} flag已用={flag}"
                    check(f"{tag}: 状态/logs 一致", same, f"OLD{st_o} NEW{st_n}")
    # 特写：守护姿态致死 → 回满 max_hp + 姿态移除 + 战意清 0 + flag 置位
    p = mk_player("cls_zhan_shi", ["铁誓·不动"])
    b = mk_battle(dict(p), mk_enemy())
    _maxhp = int(b.player["max_hp"])
    b.player["stacks"]["zhan_yi"] = 7
    b.player["buffs"]["stance_guard"] = 1
    b.player["hp"] = 0
    logs = []
    b._post_hp_lethal(b.player, 99999, logs)
    check(f"守护致死 → 回满 hp = max_hp = {_maxhp}", b.player["hp"] == _maxhp,
          f"hp={b.player['hp']} max_hp={_maxhp}")
    check("姿态 stance_guard 移除", "stance_guard" not in b.player["buffs"], str(b.player["buffs"]))
    check("战意清空 zhan_yi==0", b.player["stacks"]["zhan_yi"] == 0, str(b.player["stacks"]))
    check("flag _stance_immortal_used 置位", getattr(b, "_stance_immortal_used", False) is True)
    check("日志含 铁誓·不动", any("铁誓·不动" in s for s in logs), str(logs))
    # 无守护姿态：不触发 hp=0
    b2 = mk_battle(dict(p), mk_enemy())
    b2.player["stacks"]["zhan_yi"] = 7
    b2.player["hp"] = 0
    logs2 = []
    b2._post_hp_lethal(b2.player, 99999, logs2)
    check("无守护姿态 → 不触发 hp=0 无日志", b2.player["hp"] == 0 and not logs2,
          f"hp={b2.player['hp']} logs={logs2}")
    # 同场二次致死（flag 已用 + 姿态已移除）→ 不触发
    b3 = mk_battle(dict(p), mk_enemy())
    b3.player["stacks"]["zhan_yi"] = 10
    b3.player["buffs"]["stance_guard"] = 1
    b3.player["hp"] = 0
    b3._post_hp_lethal(b3.player, 99999, [])
    b3.player["hp"] = 0
    logs3 = []
    b3._post_hp_lethal(b3.player, 99999, logs3)
    check("二次致死（flag 已用）→ 不复活 hp=0", b3.player["hp"] == 0 and not logs3,
          f"hp={b3.player['hp']} logs={logs3}")


# ============================================================
# 4. 顺序链（合成同挂：死亡契约先于血怒先于铁誓——谁先触发谁生效）
# ============================================================
def test_chain_order():
    print("\n== 4. 致死复活链顺序（dc → berserk → stance）OLD vs NEW ==")
    # 合成三 proc 同挂（跨职业数据不可能真实出现——探针验证顺序语义与迁移一致）
    # 跨职业被动名不在本职业表 → _passive_map 查不到 → 手工注入 pm（_inject），
    # OLD/NEW 都走同一注入 pm（_passive_map 已换）——两路公平对比。
    def mk_chain():
        p = mk_player("cls_zhan_shi", [])
        return p
    # 场景 A：dc 满条件（信念5+骷髅）→ dc 先触发复活，后续两段不接棒
    # 每组合只注入该组合"已学"的 proc（dc/br/st 三键按 flag 决定）
    for combo in ((1, 0, 0), (1, 1, 1), (0, 1, 1), (1, 1, 0)):
        b_old = mk_battle(dict(mk_chain()), mk_enemy())
        b_new = mk_battle(dict(mk_chain()), mk_enemy())
        _keys = [k for k, l in (("death_contract", combo[0]),
                                ("berserk_revive", combo[1]),
                                ("stance_immortal", combo[2])) if l]
        for b in (b_old, b_new):
            _inject(b, _keys)
            b.player["resources"]["faith"] = 5
            b.companions = [mk_skeleton("骷髅A")]
            b.player["v139_modes"] = {"dual_form": {"form": "alt"}}  # 狂暴接棒条件
            b.player["buffs"]["stance_guard"] = 1                    # 铁誓接棒条件
            b.player["stacks"]["zhan_yi"] = 9
            b.player["hp"] = 0
        logs_o, logs_n = [], []
        OLD_lethal(b_old, b_old.player, 99999, logs_o)
        b_new._post_hp_lethal(b_new.player, 99999, logs_n)
        same = (_state_of(b_old, b_old.player) == _state_of(b_new, b_new.player)
                and logs_o == logs_n)
        # 已注入的键集（_keys）即组合里"已学"的
        exp_hp = 0
        if combo[0]:
            exp_hp = max(1, int(b_old.player.get("max_hp", 1) * 0.20))
        elif combo[1]:
            exp_hp = max(1, int(b_old.player.get("max_hp", 1) * 0.30))
        elif combo[2]:
            exp_hp = b_old.player.get("max_hp", 1)
        exp_comp = 0 if combo[0] else (1 if combo[1] else 1)
        check(f"组合dc={combo[0]} br={combo[1]} st={combo[2]}: 状态/logs 一致",
              same, f"OLD{_state_of(b_old,b_old.player)}/{logs_o} NEW{_state_of(b_new,b_new.player)}/{logs_n}")
        check(f"  复活 hp={exp_hp} 骷髅剩{exp_comp}",
              b_old.player["hp"] == b_new.player["hp"] == exp_hp
              and len(b_old.companions) == len(b_new.companions) == exp_comp,
              f"OLD hp={b_old.player['hp']} comps={len(b_old.companions)} NEW hp={b_new.player['hp']} comps={len(b_new.companions)}")
    # 场景 B：dc 无骷髅（信念足但无代受）→ dc 日志不复活 → berserk 接棒（狂暴）→ 复活 30%
    b_old = mk_battle(dict(mk_chain()), mk_enemy())
    b_new = mk_battle(dict(mk_chain()), mk_enemy())
    for b in (b_old, b_new):
        _inject(b, ["death_contract", "berserk_revive", "stance_immortal"])
        b.player["resources"]["faith"] = 5
        b.player["v139_modes"] = {"dual_form": {"form": "alt"}}
        b.player["buffs"]["stance_guard"] = 1
        b.player["stacks"]["zhan_yi"] = 9
        b.player["hp"] = 0
    logs_o, logs_n = [], []
    OLD_lethal(b_old, b_old.player, 99999, logs_o)
    b_new._post_hp_lethal(b_new.player, 99999, logs_n)
    _mhp = int(b_new.player["max_hp"])
    check("dc无骷髅→berserk接棒复活30% + dc日志 + 未耗契约",
          _state_of(b_old, b_old.player) == _state_of(b_new, b_new.player)
          and b_new.player["hp"] == max(1, int(_mhp * 0.30))
          and not getattr(b_new, "_death_pact_used", False)
          and getattr(b_new, "_berserk_revive_used", False)
          and any("没有骷髅" in s for s in logs_n),
          f"OLD{_state_of(b_old,b_old.player)}/{logs_o} NEW{_state_of(b_new,b_new.player)}/{logs_n}")
    # 场景 C：dc 信念不足 + 非狂暴（berserk 不接）→ stance 接棒（守护）→ 回满清姿态清战意
    b_old = mk_battle(dict(mk_chain()), mk_enemy())
    b_new = mk_battle(dict(mk_chain()), mk_enemy())
    for b in (b_old, b_new):
        _inject(b, ["death_contract", "berserk_revive", "stance_immortal"])
        b.player["resources"]["faith"] = 4
        b.player["buffs"]["stance_guard"] = 1
        b.player["stacks"]["zhan_yi"] = 9
        b.player["hp"] = 0
    logs_o, logs_n = [], []
    OLD_lethal(b_old, b_old.player, 99999, logs_o)
    b_new._post_hp_lethal(b_new.player, 99999, logs_n)
    _mhp2 = int(b_new.player["max_hp"])
    check("dc信念不足+非狂暴→stance接棒回满清姿态清战意",
          _state_of(b_old, b_old.player) == _state_of(b_new, b_new.player)
          and b_new.player["hp"] == _mhp2
          and "stance_guard" not in b_new.player["buffs"]
          and b_new.player["stacks"]["zhan_yi"] == 0
          and getattr(b_new, "_stance_immortal_used", False),
          f"OLD{_state_of(b_old,b_old.player)}/{logs_o} NEW{_state_of(b_new,b_new.player)}/{logs_n}")
    # 场景 D：dc 信念不足 + 非狂暴 + 无守护 → 全链不触发 hp=0 无日志
    b = mk_battle(dict(mk_chain()), mk_enemy())
    _inject(b, ["death_contract", "berserk_revive", "stance_immortal"])
    b.player["resources"]["faith"] = 4
    b.player["stacks"]["zhan_yi"] = 9
    b.player["hp"] = 0
    logs = []
    b._post_hp_lethal(b.player, 99999, logs)
    check("全链条件不满足 → hp=0 无日志 无 flag",
          b.player["hp"] == 0 and not logs
          and not getattr(b, "_death_pact_used", False)
          and not getattr(b, "_berserk_revive_used", False)
          and not getattr(b, "_stance_immortal_used", False),
          f"hp={b.player['hp']} logs={logs}")


# ============================================================
# 5. 序列化 flag 恢复（from_state 等价：battle 属性预置）后行为
# ============================================================
def test_serialized_flags():
    print("\n== 5. 序列化 flag 恢复后二次致死不触发（OLD/NEW 一致）==")
    cases = [
        ("死亡契约", "cls_mu_shi", "_death_pact_used", {"faith": 5}, [mk_skeleton("骷髅A")]),
        ("血怒·不灭", "cls_zhan_shi", "_berserk_revive_used", {}, []),
        ("铁誓·不动", "cls_zhan_shi", "_stance_immortal_used", {}, []),
    ]
    for sk_name, cls, attr, res, comps in cases:
        p = mk_player(cls, [sk_name])
        b_old = mk_battle(dict(p), mk_enemy())
        b_new = mk_battle(dict(p), mk_enemy())
        for b in (b_old, b_new):
            b.player["resources"].update(res)
            if comps:
                b.companions = [dict(c) for c in comps]
            if attr == "_berserk_revive_used":
                b.player["v139_modes"] = {"dual_form": {"form": "alt"}}
            if attr == "_stance_immortal_used":
                b.player["buffs"]["stance_guard"] = 1
            setattr(b, attr, True)  # 模拟 from_state 恢复已用
            b.player["hp"] = 0
        logs_o, logs_n = [], []
        OLD_lethal(b_old, b_old.player, 99999, logs_o)
        b_new._post_hp_lethal(b_new.player, 99999, logs_n)
        check(f"{sk_name} 恢复 flag 已用 → 致死不触发 hp=0 无日志",
              _state_of(b_old, b_old.player) == _state_of(b_new, b_new.player)
              and b_new.player["hp"] == 0 and not logs_n,
              f"OLD{_state_of(b_old,b_old.player)} NEW{_state_of(b_new,b_new.player)} logs={logs_n}")
    # 序列化键保留（to_state/from_state 未动——方案 §6.1 风险 4）
    battle = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "battle.py"),
                  encoding="utf-8").read()
    for k in ('"death_pact_used": getattr', '"berserk_revive_used": getattr',
              '"stance_immortal_used": getattr'):
        check(f"to_state {k.split(':')[0]} 保留", k in battle)
    check("from_state 恢复三 flag", "b._death_pact_used = bool(st.get(" in battle
          and "b._berserk_revive_used = bool(st.get(" in battle
          and "b._stance_immortal_used = bool(st.get(" in battle)


# ============================================================
# 6. 静态：注册表声明族/映射 + 挂点12 改造痕迹 + 旧直读残留清零
# ============================================================
def test_static():
    print("\n== 6. 静态：P2-D4b 3 proc 声明 + 挂点12 改造痕迹 ==")
    for proc, fam in (("death_contract", "revive_cond"),
                      ("berserk_revive", "revive_cond"),
                      ("stance_immortal", "revive_cond")):
        check(f"{proc} → {fam}", PP.PROC_FAMILIES.get(proc) == fam,
              f"got {PP.PROC_FAMILIES.get(proc)}")
    check("族执行器 revive_cond 已注册", "revive_cond" in PP.FAMILY_HANDLERS)
    # P2-D5a：挂点13 反击 2 proc（counter_chance/counter_up）并入 counter_cond → 总数 33
    check("PROC_FAMILIES 含 33 声明", len(PP.PROC_FAMILIES) == 33, str(len(PP.PROC_FAMILIES)))
    battle = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "battle.py"),
                  encoding="utf-8").read()
    for rk in ("death_pact_cond", "berserk", "stance"):
        check(f"挂点12 revive_kind={rk}", f'"revive_kind": "{rk}"' in battle)
    # 挂点12 区（_post_hp_lethal 方法体）不再直读三 proc 的旧字段（_ps.get / 直写 flag）
    seg = battle.split("    def _post_hp_lethal")[1].split("    def _on_taken_rewards")[0]
    old_reads = [s for s in ('_ps.get("faith_req"', "_ps.get(\"hp_pct\"", "_skels.pop()",
                             'self._berserk_revive_used = True', 'self._stance_immortal_used = True',
                             "B.pop(\"stance_guard\"", "MS[\"zhan_yi\"] = 0")
                 if s in seg]
    check("挂点12 无 3 proc 旧直读残留", not old_reads, str(old_reads))
    # v107 death_pact（非 52 白名单旧段）原样保留（self._death_pact_used 直写仍在该段）
    check("v107 death_pact 旧段保留（不迁移不注册）",
          '"death_pact"' in seg and "self._death_pact_used = True" in seg)
    check("52 声明集无表外（death_pact 未注册）", "death_pact" not in PP.PROC_FAMILIES)
    # berserk 狂暴判定留在骨架（dual_form_active 导入 + if 守卫）
    check("berserk 狂暴守卫留在骨架", "dual_form_active as _dfa169" in seg
          and "_dfa169(actor)" in seg)
    check("stance 守护姿态守卫留在骨架", 'B.get("stance_guard")' in seg)


def main():
    clean_db()
    test_death_contract()
    test_berserk_revive()
    test_stance_immortal()
    test_chain_order()
    test_serialized_flags()
    test_static()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
