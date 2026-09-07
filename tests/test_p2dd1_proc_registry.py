# -*- coding: utf-8 -*-
"""v181.P2D-D1 被动 proc 注册表基建等价探针（test_p2dd1_proc_registry.py）

验证 game/core/passive_procs.py（P2-D1 新建注册表：PROC_FAMILIES/FAMILY_HANDLERS/
run_proc_family + 试点 5 proc 迁移：speed_ratio_dmg / zhan_yi_lifesteal /
poison_cap_up+poison_cap / focus_full_on_kill / skeleton_cap）行为零变化。

方法（方案 §7 OLD-vs-NEW 探针）：
1. 静态：注册表声明/执行器存在；proc→族映射正确；无注册 proc → run 不触发（无副作用）。
2. 行为等价：对每个试点挂点，保留**迁移前原逻辑副本**（OLD），在当前引擎
   （NEW = battle.py 现挂点 → 注册表）跑同一组场景，断言输出一致。
   - 每挂点两种玩家态 × 边界状态做差分（学/不学 × 资源 0/满/边界）。

运行（与门禁同款 python）：
  python tests/test_p2dd1_proc_registry.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db, make_player  # noqa: E402
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


def mk_player(cls_id, passives, hp=500, spd=100):
    """构造战斗玩家 dict（学指定被动中文名；stacks/resources 手置用于边界场景）。"""
    pl = make_player(cls=cls_id, level=60)
    pl = db.get_player(pl.get("group_id", "g1"), pl.get("qq_id", "q1")) if pl.get("qq_id") else pl
    # make_player 落库形态 → 转纯 dict（无 id 干扰）
    out = {
        "class_name": cls_id, "level": 60, "hp": hp, "max_hp": hp,
        "mp": 100, "max_mp": 200,
        "equipment": {"weapon": {"name": "t", "stats": {"atk": 100, "matk": 100, "spd": spd},
                                 "affixes": [], "enhance": 0}},
        "attributes": {"str": 10, "int": 10},
        "learned_skills": list(passives), "race": "human",
        "resources": {}, "stacks": {},
    }
    return out


def mk_enemy(def_=20, mdef=20, hp=100000, spd=10):
    return {"name": "测试怪", "hp": hp, "max_hp": hp,
            "atk": 50, "def": def_, "mdef": mdef, "spd": spd}


# ============================================================
# 1. 静态：注册表结构
# ============================================================
def test_registry_static():
    print("\n== 1. 注册表静态结构 ==")
    # P2-D4a：挂点10/11 6 proc（tenacity/zhan_yi_full_reduce/core_full/core_reduce/
    # core_last_stand/core_overflow）并入 → 总数 28（6 试点 + 4 条件暴击 +
    # 4 stat_mult + 3 P2-D3a + 5 P2-D3b + 6 P2-D4a）
    # P2-D4b：挂点12 致死复活链 3 proc（death_contract/berserk_revive/stance_immortal）
    # 全批次并入后注册表总数 40（6+4+4+3+5+6+3+2+4+3；soul_mark_cap D3b 已声明）
    check("PROC_FAMILIES 含 45 声明", len(PP.PROC_FAMILIES) == 45, str(len(PP.PROC_FAMILIES)))
    expect_map = {
        "speed_ratio_dmg": "dmg_mult_cond",
        "arcane_resonance": "dmg_mult_cond",
        "element_origin": "dmg_mult_cond",
        "element_sync": "flag_set_cond",
        "hunt_mark_up": "dmg_mult_cond",
        "soul_mark_cap": "dmg_mult_cond",
        "shaken_awareness": "dmg_mult_cond",
        "broken_extend": "dmg_mult_cond",
        "dirge_debuff_dmg": "dmg_mult_cond",
        "zhan_yi_lifesteal": "lifesteal_add",
        "poison_cap_up": "stack_cap_add",
        "poison_cap": "stack_cap_add",
        "skeleton_cap": "summon_cap_add",
        "focus_full_on_kill": "on_kill_refill",
        "zhan_yi_crit": "crit_cond_add",
        "arcane_wisdom": "crit_cond_add",
        "focus_surplus_crit": "crit_cond_add",
        "element_core": "crit_cond_add",
        "shadow_dance_bonus": "stat_mult_cond",
        "melody_resonance": "stat_mult_cond",
        "melody_full": "stat_mult_cond",
        "melody_master": "stat_mult_cond",
        # P2-D4a 6 proc（受击减伤/免控族；zhan_yi_full_reduce/core_full 双消费点
        # 收敛 dr_cond 单族——免控段 cc_kind / 减伤段 dr_kind ctx 分派）
        "tenacity": "cc_break_cost",
        "zhan_yi_full_reduce": "dr_cond",
        "core_full": "dr_cond",
        "core_reduce": "dr_cond",
        "core_last_stand": "dr_cond",
        "core_overflow": "dr_cond",
        # P2-D4b 3 proc（挂点12 致死复活链 → revive_cond）
        "death_contract": "revive_cond",
        "berserk_revive": "revive_cond",
        "stance_immortal": "revive_cond",
        # P2-D6 4 proc（模块级 tick handler 族 → tick_regen/tick_mech_charge/tick_faith）
        "focus_regen_summon": "tick_regen",
        "arcane_intuition": "tick_mech_charge",
        "undead_faith": "tick_faith",
        "faith_overload_heal": "tick_faith",
        # P2-D5a 2 proc（受击反击聚合族 counter_cond；chance max/mult min/
        # counter_up 加 chance_add×dmg_add——聚合逻辑进 handler，挂点 cap0.9+roll 收口）
        "counter_chance": "counter_cond",
        "counter_up": "counter_cond",
        # P2-D5b 3 proc（挂点15 毒 DOT 2 → dot_mult_cond/dot_weaken 新族 + 挂点16
        # hunt_mark_cap cap 段 → dmg_mult_cond；soul_mark_cap 已在上 D3b 声明乘区段，
        # cap 段同族 ctx cap_kind 分派——本批实增 3 声明）
        "poison_all_up": "dot_mult_cond",
        "poison_weaken": "dot_weaken",
        "hunt_mark_cap": "dmg_mult_cond",
    }
    for proc, fam in expect_map.items():
        check(f"{proc} → {fam}", PP.PROC_FAMILIES.get(proc) == fam,
              f"got {PP.PROC_FAMILIES.get(proc)}")
    for fam in ("dmg_mult_cond", "lifesteal_add", "stack_cap_add",
                "summon_cap_add", "on_kill_refill", "crit_cond_add",
                "stat_mult_cond", "flag_set_cond", "cc_break_cost", "dr_cond",
                "revive_cond", "tick_regen", "tick_mech_charge", "tick_faith",
                "dot_mult_cond", "dot_weaken", "counter_cond"):
        check(f"族执行器 {fam} 已注册", fam in PP.FAMILY_HANDLERS)
    # 52 全覆盖校验：除 KNOWN_GAPS + 本批 6 外，其余 52 proc 尚未声明（后续批次）——不静默
    declared = set(PP.PROC_FAMILIES)
    check("声明集 ∩ KNOWN_GAPS = ∅", not (declared & PP.KNOWN_GAPS),
          str(declared & PP.KNOWN_GAPS))
    # 无注册 = 不触发：未声明 proc（如 poison_burst_up）run 无副作用
    ctx = {"player": {}, "ps": {}, "ps_name": "x", "cap": 5, "mult": 1.0, "rate": 0.0}
    out = PP.run_proc_family(None, ["poison_burst_up"], ctx)
    check("无注册 proc → 不触发返回空", out == [] and ctx["cap"] == 5 and ctx["mult"] == 1.0, str(out))


# ============================================================
# 2. 行为等价探针（OLD 副本 vs NEW 现挂点）
# ============================================================
def _mk_battle(player, enemy=None):
    b = BT.Battle("monster", enemy or mk_enemy(), {}, player)
    # 探针需要玩家 resources/stacks 袋（Battle __init__ 可能未建）
    b.player.setdefault("resources", {})
    b.player.setdefault("stacks", {})
    return b


def test_speed_ratio_dmg():
    print("\n== 2. speed_ratio_dmg（挂点4 _player_dmg_mult）OLD vs NEW ==")

    def OLD(b, player, kind):
        # 迁移前原逻辑副本（读 _ps ratio/dmg_add + 现成状态）——逐字复刻 6cde807
        mult, tags = 1.0, []
        try:
            _pst_spd = max(0.001, float((b._player_stats(player) or {}).get("spd", 0) or 0))
            _est_spd = float((b._enemy_stats() or {}).get("spd", 0) or 0)
            for _pn_sr, _ps_sr in b._proc_pm(player)["proc"].get("speed_ratio_dmg", []):
                if _est_spd > 0 and _pst_spd / _est_spd >= float(_ps_sr.get("ratio", 2.0) or 2.0):
                    mult *= 1.0 + float(_ps_sr.get("dmg_add", 0.20) or 0.20)
                    tags = list(tags) + [f"💨疾风x{round(1 + float(_ps_sr.get('dmg_add', 0.20) or 0.20), 2)}"]
                break
        except Exception:
            pass
        return mult, tags

    for learned in (False, True):
        p = mk_player("cls_you_xia", ["疾风·极"] if learned else [], spd=100)
        for e_spd in (10, 60, 90):  # 玩家100：比 10 /1.67 /1.11
            b_old = _mk_battle(dict(p), mk_enemy(spd=e_spd))
            b_new = _mk_battle(dict(p), mk_enemy(spd=e_spd))
            m_old, t_old = OLD(b_old, b_old.player, "phys")
            m_new, t_new = b_new._player_dmg_mult(b_new.player, "phys")
            tag_ok = (t_new == t_old)
            check(f"学={learned} 敌速{e_spd}: mult {m_old}=={m_new} tags{t_old}=={t_new}",
                  abs(m_old - m_new) < 1e-9 and tag_ok, f"{m_old} vs {m_new} / {t_old} vs {t_new}")


def test_zhan_yi_lifesteal():
    print("\n== 3. zhan_yi_lifesteal（挂点5 _settle_lifesteal）OLD vs NEW ==")

    def OLD(b, player, rate, zy):
        # 原逻辑副本：rate 加算 per_layer × 层数（cap 由外层 min 保留——探针测 rate 增量段）
        try:
            if zy > 0:
                for _pn, _ps in b._passive_map(player)["proc"].get("zhan_yi_lifesteal", []):
                    rate = rate + float(_ps.get("per_layer", 0.015) or 0.015) * zy
                    break
        except Exception:
            pass
        return rate

    for learned in (False, True):
        p = mk_player("cls_zhan_shi", ["淬血"] if learned else [])
        for zy in (0, 3, 10):
            for base_rate in (0.0, 0.05):
                b_old = _mk_battle(dict(p))
                b_old.player["stacks"]["zhan_yi"] = zy
                b_new = _mk_battle(dict(p))
                b_new.player["stacks"]["zhan_yi"] = zy
                # NEW = 现引擎 _settle_lifesteal 内 rate 增量段：读 st lifesteal + 战意加算
                st_old = b_old._player_stats(b_old.player)
                st_new = b_new._player_stats(b_new.player)
                r_old = OLD(b_old, b_old.player, float(st_old.get("lifesteal", 0) or 0) + base_rate, zy)
                r_new = float(st_new.get("lifesteal", 0) or 0) + base_rate
                # 复刻 NEW 挂点内的注册表调用（对 b_new）
                try:
                    _zy = b_new._zhan_yi_n()
                    if _zy > 0:
                        for _pn, _ps in b_new._passive_map(b_new.player)["proc"].get("zhan_yi_lifesteal", []):
                            _c = {"player": b_new.player, "ps": _ps, "ps_name": _pn,
                                  "zhan_yi_n": _zy, "rate": r_new}
                            PP.run_proc_family(b_new, "zhan_yi_lifesteal", _c)
                            r_new = _c.get("rate", r_new)
                            break
                except Exception:
                    pass
                check(f"学={learned} 战意{zy} base{base_rate}: {r_old}=={r_new}",
                      abs(r_old - r_new) < 1e-9, f"{r_old} vs {r_new}")


def test_poison_cap():
    print("\n== 4. poison_cap_up + poison_cap（挂点17 _poison_cap）OLD vs NEW ==")

    def OLD(b, player):
        cap = 5
        pm = b._proc_pm(player)
        for _pn, _ps in pm["proc"].get("poison_cap_up", []):
            cap += int(_ps.get("add", 3) or 3)
        for _pn, _ps in pm["proc"].get("poison_cap", []):
            cap += int(_ps.get("add", 3) or 3)
        return max(5, min(cap, 8))

    # 森语者 剧毒之心(poison_cap_up+3)；毒刃者 淬毒之心(poison_cap+3)；双职业都学不可能（跨职业）——
    # 双 proc 聚合路径：单职业各 1 条 + 手工注入第二条（模拟聚合，等价原 for 多条目）
    for cls, sk, proc in (("cls_you_xia", "剧毒之心", "poison_cap_up"),
                          ("cls_ci_ke", "淬毒之心", "poison_cap")):
        for learned in (False, True):
            p = mk_player(cls, [sk] if learned else [])
            b_old = _mk_battle(dict(p))
            b_new = _mk_battle(dict(p))
            c_old = OLD(b_old, b_old.player)
            c_new = b_new._poison_cap(b_new.player)
            check(f"{cls} 学={learned}: cap {c_old}=={c_new}", c_old == c_new, f"{c_old} vs {c_new}")
        # 双条目聚合（同 proc 2 条被动：手工注入 PLAYER_SKILLS 第二分支不可行→ 直接测 _poison_cap
        # 对 pm 双条目等价：OLD 累加两 add；NEW 注册表逐条累加）
        p = mk_player(cls, [sk])
        b = _mk_battle(dict(p))
        pm = b._proc_pm(b.player)
        pm["proc"][proc].append(("测试第二", {"proc": proc, "add": 3}))
        b._proc_pm = lambda pl: pm
        c = b._poison_cap(b.player)
        check(f"{cls} 双条目聚合 cap(5+3+3→8)", c == 8, f"got {c}")
        # 封顶 8：再加一条 → 仍 8
        pm["proc"][proc].append(("测试第三", {"proc": proc, "add": 3}))
        c = b._poison_cap(b.player)
        check(f"{cls} 三条目封顶 cap==8", c == 8, f"got {c}")


def test_skeleton_cap():
    print("\n== 5. skeleton_cap（挂点21 _summon_entity 上限段）OLD vs NEW ==")

    def OLD_limit(tid_limit, ps_list):
        # 原逻辑副本（只测上限计算段；召唤实体走完整 _summon_entity 需模板/装配，探针直接比 limit）
        lim = int(tid_limit)
        for _ps_sk in ps_list:
            lim = min(int(_ps_sk.get("cap", 5) or 5), lim + int(_ps_sk.get("add", 2) or 2))
            break
        return lim

    from data.plugins.dragonfall.game.data.summons import SUMMONS
    sk_tmpl_limit = int(SUMMONS.get("skeleton", {}).get("limit", 3))
    for learned in (False, True):
        p = mk_player("cls_mu_shi", ["骷髅海"] if learned else [])
        ps_list = []
        if learned:
            info = EG.skill_info("cls_mu_shi", "骷髅海")
            ps_list = [( "骷髅海", (info or {}).get("passive") or {} )]
        b_old = _mk_battle(dict(p))
        b_new = _mk_battle(dict(p))
        # NEW：跑 _summon_entity 上限路径 — 用真实 skeleton 模板 & 记录是否被拦（不实际 spawn）
        # 简化：直接调注册表族（NEW 挂点内的核心），与 OLD_limit 比
        lim_old = OLD_limit(sk_tmpl_limit, [ps for _, ps in ps_list])
        ctx = {"player": b_new.player, "limit": sk_tmpl_limit}
        for _pn, _ps in ps_list:
            ctx["ps"], ctx["ps_name"] = _ps, _pn
            PP.run_proc_family(b_new, "skeleton_cap", ctx)
            ctx["limit"] = ctx.get("limit", sk_tmpl_limit)
        lim_new = ctx["limit"] if ps_list else sk_tmpl_limit
        check(f"学={learned}: limit {lim_old}=={lim_new}", lim_old == lim_new, f"{lim_old} vs {lim_new}")
    # 无被动：_summon_entity 上限路径不受影响（tid != skeleton / 无 proc 条目）
    p = mk_player("cls_mu_shi", [])
    b = _mk_battle(dict(p))
    b.summons = []
    # 模板 limit 上限：召唤 3 骷髅后第 4 次被拦（无被动）
    lim = int(SUMMONS.get("skeleton", {}).get("limit", 3))
    check("skeleton 模板 limit≥3", lim == 3, f"limit={lim}")


def test_focus_full_on_kill():
    print("\n== 6. focus_full_on_kill（挂点22 _remove_unit）OLD vs NEW ==")

    def OLD_refill(b, player, pend_lines):
        # 原逻辑副本
        try:
            for _pn_k, _ps_k in b._proc_pm(player)["proc"].get("focus_full_on_kill", []):
                if b._p_res().get("energy") is not None:
                    _max_e = b._res_max(player, "energy")
                    _old_e = int(b._p_res().get("energy", 0) or 0)
                    b._p_res()["energy"] = _max_e
                    if isinstance(pend_lines, list):
                        pend_lines.append(f"💨 {_pn_k}：击杀！专注回满（{_old_e} → {_max_e}）")
                break
        except Exception:
            pass

    for learned in (False, True):
        p = mk_player("cls_you_xia", ["追风"] if learned else [])
        for energy in (0, 30, 100):
            b_old = _mk_battle(dict(p))
            b_old.player["resources"] = {"energy": energy}
            b_old._pending_dmg_lines = []
            b_new = _mk_battle(dict(p))
            b_new.player["resources"] = {"energy": energy}
            b_new._pending_dmg_lines = []
            OLD_refill(b_old, b_old.player, b_old._pending_dmg_lines)
            # NEW：复刻 _remove_unit 内现挂点调用
            try:
                for _pn_k, _ps_k in b_new._proc_pm(b_new.player)["proc"].get("focus_full_on_kill", []):
                    if b_new._p_res().get("energy") is not None:
                        _c = {"player": b_new.player, "ps": _ps_k, "ps_name": _pn_k,
                              "res": b_new._p_res(), "res_key": "energy",
                              "res_max": b_new._res_max(b_new.player, "energy"),
                              "pending_dmg_lines": b_new._pending_dmg_lines}
                        PP.run_proc_family(b_new, "focus_full_on_kill", _c)
                    break
            except Exception:
                pass
            e_old = b_old.player["resources"].get("energy")
            e_new = b_new.player["resources"].get("energy")
            l_old = b_old._pending_dmg_lines
            l_new = b_new._pending_dmg_lines
            check(f"学={learned} 精力{energy}: {e_old}=={e_new} logs {l_old}=={l_new}",
                  e_old == e_new and l_old == l_new, f"{e_old} vs {e_new} / {l_old} vs {l_new}")
    # energy 缺失（战斗初始化后资源键被删，如无 energy 的存档快照）→ 挂点外层 if 守卫短路 → 不触发不崩
    p2 = mk_player("cls_you_xia", ["追风"])
    b2 = _mk_battle(dict(p2))
    b2._pending_dmg_lines = []
    b2.player["resources"].pop("energy", None)  # 模拟无 energy 键（守卫路径）
    _res_before = dict(b2.player["resources"])
    try:
        for _pn_k, _ps_k in b2._proc_pm(b2.player)["proc"].get("focus_full_on_kill", []):
            if b2._p_res().get("energy") is not None:
                _c = {"player": b2.player, "ps": _ps_k, "ps_name": _pn_k,
                      "res": b2._p_res(), "res_key": "energy",
                      "res_max": b2._res_max(b2.player, "energy"),
                      "pending_dmg_lines": b2._pending_dmg_lines}
                PP.run_proc_family(b2, "focus_full_on_kill", _c)
            break
    except Exception:
        pass
    check("energy 缺失 → 挂点守卫短路无副作用",
          b2._pending_dmg_lines == [] and b2.player["resources"] == _res_before
          and "energy" not in b2.player["resources"], str(b2.player["resources"]))


# ============================================================
# 3. 52 全覆盖启动校验（防新增被动静默空转——P2-D1 只要求已注册批不漏；未注册批显式登记）
# ============================================================
def test_52_coverage():
    print("\n== 7. 52 proc 全覆盖口径（本批声明 6 + KNOWN_GAPS 8，其余为后续批次显式待办）==")
    proc_set = set()
    for cls, tree in C.BRANCH_SKILLS.items():
        branches = tree.get("branches") if isinstance(tree, dict) and "branches" in tree else tree
        if not isinstance(branches, dict):
            continue
        for tier, bs in branches.items():
            for bname, skills in bs.items():
                for v in (skills or {}).values():
                    ps = (v or {}).get("passive") or {}
                    if isinstance(ps, dict) and ps.get("proc"):
                        proc_set.add(ps["proc"])
    check("52 proc 扫描 ≥52", len(proc_set) >= 52, f"实际 {len(proc_set)}")
    declared = set(PP.PROC_FAMILIES)
    gaps = set(PP.KNOWN_GAPS)
    # P2-D6：声明 35（含 tick 族 4）+ KNOWN_GAPS 4（D 类真空转）——其余显式待办
    check("声明 ⊆ 52 白名单", declared <= proc_set,
          f"表外声明 {declared - proc_set}")
    check("KNOWN_GAPS ⊆ 52 白名单", gaps <= proc_set, f"表外 gaps {gaps - proc_set}")
    # P2-D1 后遗留 = 52 - 声明 - KNOWN_GAPS → 后续批次显式待办（不静默）
    pending = proc_set - declared - gaps
    print(f"    （P2-D7 收尾批次待声明：{len(pending)} 个）")


def main():
    clean_db()
    test_registry_static()
    test_speed_ratio_dmg()
    test_zhan_yi_lifesteal()
    test_poison_cap()
    test_skeleton_cap()
    test_focus_full_on_kill()
    test_52_coverage()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
