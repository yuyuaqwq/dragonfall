# -*- coding: utf-8 -*-
"""v181.P2D-D5c 命中后置/治疗/增益副作用族等价探针（test_p2dd5c_status_sidefx.py）

验证挂点18 _skill_hit_settle（element_affinity / broken_extend 延长段 /
dirge_ctrl_up）、挂点19 _skill_heal（heal_overflow_shield）、挂点20 _skill_buff
（melody_duet）、挂点23 _turn_start（shaken_decay_half）从 battle.py 内联 for
迁移到 passive_procs 注册表族 flag_set_cond（ctx flag_kind 分派）后行为零变化
（OLD vs NEW 双实现差分）。

方法（方案 §7 OLD-vs-NEW 探针）：
1. OLD = 各挂点迁移前 for 循环体逐字复刻（30933c6^）。
2. NEW = 现引擎挂点路径（run_proc_family 分发）。
3. 差分矩阵（每 proc 学/不学 × 边界状态）：
   - element_affinity（挂点18）：mech=element_burst*（触发）vs 其它 mech（不触发）
     × 学/不学 → 断言 battle._elem_affinity_next 置位一致。
   - broken_extend 延长段（挂点18 shaken 触发内）：学/不学 × immune_turns 现值
     0/1/3 → 断言 shaken dict immune_turns 增量一致（+ps.extend）。
   - dirge_ctrl_up（挂点18 控制延长）：学/不学 × e_buffs 控制键 stun/freeze/
     silence/sleep/spd_down 现值 0/2 → 断言时长 +add 一致（首个有值键延长）。
   - melody_duet（挂点20）：学/不学 × melody 驻留 name 有/无 × stack 1/4 →
     断言 _melody_state().stack +add（cap MELODY_CFG.max_stack）。
   - heal_overflow_shield（挂点19）：学/不学 × 溢出 0/正 × target_ally None/队友
     → 断言 p_shields.overflow 值/self._add_shield 盾一致（×ps.pct）。
   - shaken_decay_half（挂点23）：学/不学 × e_buffs.shaken dict val 现值
     → 断言 val 回补 int(decay/2) 一致。
   副作用/日志两路逐项一致断言。

运行（与门禁同款 python）：
  python tests/test_p2dd5c_status_sidefx.py
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


def mk_enemy(hp=100000, def_=20, mdef=20, spd=10):
    return {"name": "测试怪", "hp": hp, "max_hp": hp,
            "atk": 50, "def": def_, "mdef": mdef, "spd": spd,
            "buffs": {}, "debuffs": {}}


def mk_battle(player, enemy=None):
    b = BT.Battle("monster", enemy or mk_enemy(), {}, copy.deepcopy(player))
    b._focus.setdefault("resources", {})
    b._focus.setdefault("stacks", {})
    b._focus.setdefault("buffs", {})
    b._focus.setdefault("eff", {})
    b._focus.setdefault("p_shields", {})
    b.enemy.setdefault("buffs", {})
    b.enemy.setdefault("debuffs", {})
    return b


PROC_OWNER = {
    "元素亲和": "cls_fa_shi", "破绽·极": "cls_wu_seng", "镇魂安魂": "cls_shi_ren",
    "二重唱": "cls_shi_ren", "圣光回响": "cls_mu_shi", "破绽感知": "cls_wu_seng",
}


def _ps_entry(cls_id, nm):
    """从 skills.py 拉单被动条目 (中文名, passive dict)。"""
    owner = PROC_OWNER.get(nm, cls_id)
    info = EG.skill_info(owner, nm)
    ps = (info or {}).get("passive") or {}
    assert ps.get("proc"), f"{nm} passive 无 proc"
    return nm, ps


def inject_proc(b, entries):
    pm = {"proc": entries, "stat": []}
    b._passive_map = lambda pl, _pm=pm: _pm
    return pm


# ============================================================
# OLD：各挂点迁移前 for 循环体逐字复刻（30933c6^）
# ============================================================
def OLD_element_affinity(b, mech):
    """OLD 挂点18 element_affinity 段（mech=element_burst* 前缀守卫由调用侧负责——直接复刻循环）。"""
    try:
        for _pn_ea, _ps_ea in b._proc_pm(b._focus)["proc"].get("element_affinity", []):
            b._elem_affinity_next = True
            break
    except Exception:
        pass
    return bool(getattr(b, "_elem_affinity_next", False))


def OLD_broken_extend(b, bs):
    """OLD 挂点18 broken_extend 延长段循环体（bs = e_buffs.shaken dict 引用）。"""
    try:
        for _pn_be, _ps_be in b._proc_pm(b._focus)["proc"].get("broken_extend", []):
            bs["immune_turns"] = int(bs.get("immune_turns", 0) or 0) + int(_ps_be.get("extend", 1) or 1)
            break
    except Exception:
        pass
    return bs


def OLD_dirge_ctrl_up(b, eb):
    """OLD 挂点18 dirge_ctrl_up 循环体（eb = e_buffs dict 引用）。"""
    try:
        for _pn_dg, _ps_dg in b._proc_pm(b._focus)["proc"].get("dirge_ctrl_up", []):
            for _ck_dg in ("stun", "freeze", "silence", "sleep", "spd_down"):
                if eb.get(_ck_dg):
                    eb[_ck_dg] = int(eb[_ck_dg]) + int(_ps_dg.get("add", 1) or 1)
                    break
            break
    except Exception:
        pass
    return eb


def OLD_melody_duet(b, mel):
    """OLD 挂点20 melody_duet 循环体（mel = _melody_state() 引用）。"""
    try:
        from data.plugins.dragonfall.game.core.battle_mech import MELODY_CFG as _MEL_CFG
        for _pn_md, _ps_md in b._proc_pm(b._focus)["proc"].get("melody_duet", []):
            if mel.get("name") and int(mel.get("stack", 0) or 0) > 0:
                mel["stack"] = min(int(_MEL_CFG.get("max_stack", 5) or 5),
                                   int(mel.get("stack", 0) or 0) + 1)
            break
    except Exception:
        pass
    return mel


def OLD_heal_overflow_shield(b, target_unit, hp_before, heal, target_ally, logs):
    """OLD 挂点19 heal_overflow_shield 段循环体（_heal_overflow_procs 双 proc 循环中该 proc 的迭代体）。"""
    _hpn, _hpdef = "heal_overflow_shield", 0.5
    for _pn, _ps in b._passive_map(b._focus)["proc"].get(_hpn, []):
        overflow = hp_before + heal - target_unit.get("max_hp", target_unit.get("hp", 0))
        if overflow > 0:
            shield_gain = int(overflow * float(_ps.get("pct", _hpdef)))
            if target_ally is not None:
                _sh = target_unit.setdefault("p_shields", {})
                _cur = _sh.get("overflow")
                if _cur:
                    _cur["value"] = _cur.get("value", 0) + shield_gain
                    _cur["turns"] = max(_cur.get("turns", 0), 2)
                else:
                    _sh["overflow"] = {"value": shield_gain, "turns": 2}
                logs.append(f"🛡️ {_pn}：治疗溢出转化为 {shield_gain} 点护盾！")
            else:
                b._add_shield("overflow", shield_gain, 2)
                logs.append(f"🛡️ {_pn}：治疗溢出转化为 {shield_gain} 点护盾！")
    return target_unit, logs


def OLD_shaken_decay_half(b, eb_sh, decay_full):
    """OLD 挂点23 shaken_decay_half 循环体（eb_sh = e_buffs.shaken dict 引用）。"""
    try:
        for _pn_dh, _ps_dh in b._proc_pm(b._focus)["proc"].get("shaken_decay_half", []):
            if isinstance(eb_sh, dict):
                _decay_full = float(decay_full or 0) or 1.7
                eb_sh["val"] = int(eb_sh.get("val", 0) or 0) + int(_decay_full / 2)
            break
    except Exception:
        pass
    return eb_sh


# ============================================================
# NEW：现引擎挂点路径（run_proc_family 分发）
# ============================================================
def NEW_flag(b, player, proc, flag_kind, ctx_extra):
    ctx = {"player": player, "ps": {}, "ps_name": "", "flag_kind": flag_kind}
    ctx.update(ctx_extra)
    PP.run_proc_family_pm(b, player, proc, ctx)
    return ctx


def test_element_affinity():
    print("\n== 1. element_affinity（挂点18 引爆后置位）OLD vs NEW ==")
    NM = "元素亲和"
    for learned in (False, True):
        p = mk_player("cls_fa_shi", [NM] if learned else [])
        pe = {"element_affinity": [_ps_entry("cls_fa_shi", NM)]} if learned else {}
        for mech in ("element_burst_fire", "ice_mark"):
            b_o = mk_battle(copy.deepcopy(p))
            if pe:
                inject_proc(b_o, pe)
            # OLD 段带外层 mech 前缀守卫（battle.py 挂点18：`if mech and mech.startswith(...)`）
            got_o = False
            if mech and mech.startswith("element_burst"):
                got_o = OLD_element_affinity(b_o, mech)
            b_n = mk_battle(copy.deepcopy(p))
            if pe:
                inject_proc(b_n, pe)
            if mech and mech.startswith("element_burst"):
                NEW_flag(b_n, b_n._focus, "element_affinity", "elem_affinity", {})
            got_n = bool(getattr(b_n, "_elem_affinity_next", False))
            check(f"学={learned} mech={mech}: OLD==NEW 置位 {got_o}=={got_n}",
                  got_o == got_n, f"OLD {got_o} NEW {got_n}")
            if learned and mech.startswith("element_burst"):
                check(f"  学={learned} 引爆置位 True", got_n is True, "")
            else:
                check(f"  学={learned} 非引爆/未学不置位 False", got_n is False, "")


def test_broken_extend():
    print("\n== 2. broken_extend 延长段（挂点18 shaken 触发内）OLD vs NEW ==")
    NM = "破绽·极"
    for learned in (False, True):
        pe = {"broken_extend": [_ps_entry("cls_wu_seng", NM)]} if learned else {}
        for imm0 in (0, 1, 3):
            p = mk_player("cls_wu_seng", [NM] if learned else [])
            b_o = mk_battle(copy.deepcopy(p))
            if pe:
                inject_proc(b_o, pe)
            sh_o = {"val": 0, "threshold": 15, "immune_turns": imm0, "trigger_count": 1}
            OLD_broken_extend(b_o, sh_o)
            b_n = mk_battle(copy.deepcopy(p))
            if pe:
                inject_proc(b_n, pe)
            sh_n = {"val": 0, "threshold": 15, "immune_turns": imm0, "trigger_count": 1}
            # 现引擎 broken_extend 族 = dmg_mult_cond（D3b 声明乘区段）；延长段 = 同族
            # mult_kind=broken_extend 分派（battle.py 挂点18 run_proc_family 走该分派）
            ctx = {"player": b_n._focus, "ps": {}, "ps_name": "",
                   "mult_kind": "broken_extend", "shaken": sh_n}
            PP.run_proc_family_pm(b_n, b_n._focus, "broken_extend", ctx)
            check(f"学={learned} immune_turns 现值{imm0}: OLD==NEW {sh_o['immune_turns']}=={sh_n['immune_turns']}",
                  sh_o == sh_n, f"OLD {sh_o} NEW {sh_n}")
            if learned:
                check(f"  学={learned}: immune_turns {imm0}→{imm0+1}",
                      sh_n["immune_turns"] == imm0 + 1, f"got {sh_n['immune_turns']}")
            # 乘区段不受延长段迁移影响（mult_kind=broken_break 原样——仅学到时触发）
            if learned:
                sh_m = {"val": 0, "threshold": 15, "immune_turns": 1, "trigger_count": 1}
                ctx_m = {"player": b_n._focus, "ps": {}, "ps_name": "",
                         "mult_kind": "broken_break", "shaken": sh_m, "mult": 1.0, "tags": []}
                PP.run_proc_family_pm(b_n, b_n._focus, "broken_extend", ctx_m)
                check(f"学={learned}: 乘区段 mult_kind=broken_break 仍触发 ×1.5",
                      abs(ctx_m.get("mult", 1.0) - 1.5) < 1e-9, f"got {ctx_m.get('mult')}")


def test_dirge_ctrl_up():
    print("\n== 3. dirge_ctrl_up（挂点18 控制延长）OLD vs NEW ==")
    NM = "镇魂安魂"
    for learned in (False, True):
        pe = {"dirge_ctrl_up": [_ps_entry("cls_shi_ren", NM)]} if learned else {}
        for pre in (0, 2):
            for key in ("stun", "freeze", "silence", "sleep", "spd_down"):
                p = mk_player("cls_shi_ren", [NM] if learned else [])
                eb0 = {k: (pre if k == key else 0) for k in ("stun", "freeze", "silence", "sleep", "spd_down")}
                if pre == 0:
                    eb0 = {}
                b_o = mk_battle(copy.deepcopy(p))
                if pe:
                    inject_proc(b_o, pe)
                eb_o = dict(eb0)
                OLD_dirge_ctrl_up(b_o, eb_o)
                b_n = mk_battle(copy.deepcopy(p))
                if pe:
                    inject_proc(b_n, pe)
                eb_n = dict(eb0)  # 从 OLD 前快照重建（防 OLD 突变污染 NEW 输入）
                logs_n = []
                NEW_flag(b_n, b_n._focus, "dirge_ctrl_up", "dirge_ctrl_up",
                         {"e_buffs": eb_n, "logs": logs_n})
                check(f"学={learned} {key}={pre}: OLD==NEW e_buffs {eb_o}=={eb_n}",
                      eb_o == eb_n, f"OLD {eb_o} NEW {eb_n}")
                if learned and pre > 0:
                    check(f"  学={learned} {key}: +1 生效", eb_n.get(key) == pre + 1,
                          f"got {eb_n.get(key)}")


def test_melody_duet():
    print("\n== 4. melody_duet（挂点20 吟唱 +add）OLD vs NEW ==")
    NM = "二重唱"
    from data.plugins.dragonfall.game.core.battle_mech import MELODY_CFG
    for learned in (False, True):
        pe = {"melody_duet": [_ps_entry("cls_shi_ren", NM)]} if learned else {}
        for has_name in (False, True):
            for stk0 in (1, 4):
                p = mk_player("cls_shi_ren", [NM] if learned else [])
                b_o = mk_battle(copy.deepcopy(p))
                if pe:
                    inject_proc(b_o, pe)
                mel_o = {"name": "测试旋律" if has_name else None, "stack": stk0,
                         "finale_ready": False}
                OLD_melody_duet(b_o, mel_o)
                b_n = mk_battle(copy.deepcopy(p))
                if pe:
                    inject_proc(b_n, pe)
                mel_n = {"name": "测试旋律" if has_name else None, "stack": stk0,
                         "finale_ready": False}
                logs_n = []
                NEW_flag(b_n, b_n._focus, "melody_duet", "melody_duet",
                         {"melody": mel_n, "max_stack": MELODY_CFG.get("max_stack", 5),
                          "logs": logs_n})
                check(f"学={learned} name={has_name} stack{stk0}: OLD==NEW {mel_o}=={mel_n}",
                      mel_o == mel_n, f"OLD {mel_o} NEW {mel_n}")
                if learned and has_name and stk0 > 0:
                    exp = min(MELODY_CFG.get("max_stack", 5), stk0 + 1)
                    check(f"  学={learned}: stack {stk0}→{exp}", mel_n["stack"] == exp,
                          f"got {mel_n['stack']}")
                    check(f"  学={learned}: 日志含二重唱", any("二重唱" in x for x in logs_n),
                          str(logs_n))


def test_heal_overflow_shield():
    print("\n== 5. heal_overflow_shield（挂点19 溢出转盾）OLD vs NEW ==")
    NM = "圣光回响"
    for learned in (False, True):
        pe = {"heal_overflow_shield": [_ps_entry("cls_mu_shi", NM)]} if learned else {}
        for ov_target in (0, 60, 200):
            for ally in (None, "ally"):
                p = mk_player("cls_mu_shi", [NM] if learned else [], hp=400)
                b_o = mk_battle(copy.deepcopy(p))
                if pe:
                    inject_proc(b_o, pe)
                b_n = mk_battle(copy.deepcopy(p))
                if pe:
                    inject_proc(b_n, pe)
                if ally is None:
                    # 自己：target = battle player（max_hp 已被 Battle.__init__ 重算为实时面板）
                    tgt_o = b_o._focus
                    tgt_n = b_n._focus
                    ally_o = None
                    ally_n = None
                else:
                    tgt_o = {"name": "队友", "hp": 300, "max_hp": 400, "buffs": {}, "p_shields": {}}
                    tgt_n = copy.deepcopy(tgt_o)
                    ally_o = tgt_o
                    ally_n = tgt_n
                tgt_o["hp"] = 300
                tgt_n["hp"] = 300
                hp_before = 300
                # 构造 heal 使真实溢出 = ov_target（max_hp 以目标实际 max_hp 计）
                heal_o = ov_target + int(tgt_o.get("max_hp", 400)) - hp_before
                heal_n = ov_target + int(tgt_n.get("max_hp", 400)) - hp_before
                logs_o, logs_n = [], []
                OLD_heal_overflow_shield(b_o, tgt_o, hp_before, heal_o, ally_o, logs_o)
                NEW_flag(b_n, b_n._focus, "heal_overflow_shield", "heal_overflow_shield",
                         {"target_unit": tgt_n, "hp_before": hp_before, "heal": heal_n,
                          "target_ally": ally_n, "overflow_shield_turns": 2,
                          "logs": logs_n})
                # 自己场景：OLD 原循环 _add_shield → player.shields.overflow（expire_at 时刻制）；
                # NEW handler 同 _add_shield → 同袋同值。队友场景 p_shields.overflow（turns 制）。
                if ally is None:
                    st_o = b_o._focus.setdefault("shields", {}).get("overflow")
                    st_n = b_n._focus.setdefault("shields", {}).get("overflow")
                    same = (st_o == st_n) and logs_o == logs_n
                else:
                    st_o = tgt_o.setdefault("p_shields", {}).get("overflow")
                    st_n = tgt_n.setdefault("p_shields", {}).get("overflow")
                    same = (st_o == st_n) and logs_o == logs_n
                check(f"学={learned} 溢出{ov_target} ally={ally}: OLD==NEW 盾 {st_o}=={st_n}",
                      same, f"OLD {st_o} {logs_o} NEW {st_n} {logs_n}")
                if learned and ov_target > 0:
                    exp_v = int(ov_target * 0.5)
                    got = (st_n or {}).get("value")
                    check(f"  学={learned} 溢出{ov_target}: 盾值 {exp_v}", got == exp_v,
                          f"got {st_n}")


def test_shaken_decay_half():
    print("\n== 6. shaken_decay_half（挂点23 破绽衰减回补）OLD vs NEW ==")
    NM = "破绽感知"
    for learned in (False, True):
        pe = {"shaken_decay_half": [_ps_entry("cls_wu_seng", NM)]} if learned else {}
        for val0 in (0, 10, 40):
            for decay in (1.7, 0.0):
                p = mk_player("cls_wu_seng", [NM] if learned else [])
                b_o = mk_battle(copy.deepcopy(p))
                if pe:
                    inject_proc(b_o, pe)
                sh_o = {"val": val0, "threshold": 15}
                OLD_shaken_decay_half(b_o, sh_o, decay)
                b_n = mk_battle(copy.deepcopy(p))
                if pe:
                    inject_proc(b_n, pe)
                sh_n = {"val": val0, "threshold": 15}
                NEW_flag(b_n, b_n._focus, "shaken_decay_half", "shaken_decay_half",
                         {"e_buffs_shaken": sh_n, "decay_full": decay})
                check(f"学={learned} val{val0} decay{decay}: OLD==NEW {sh_o}=={sh_n}",
                      sh_o == sh_n, f"OLD {sh_o} NEW {sh_n}")
                if learned:
                    d = float(decay or 0) or 1.7
                    exp = val0 + int(d / 2)
                    check(f"  学={learned}: val {val0}→{exp}", sh_n["val"] == exp,
                          f"got {sh_n['val']}")


def test_static():
    print("\n== 7. 静态：P2-D5c 声明 + 挂点改造痕迹 + 残留清零 + 计数 ==")
    for proc, fam in (("element_affinity", "flag_set_cond"),
                      ("dirge_ctrl_up", "flag_set_cond"),
                      ("melody_duet", "flag_set_cond"),
                      ("heal_overflow_shield", "flag_set_cond"),
                      ("shaken_decay_half", "flag_set_cond"),
                      ("broken_extend", "dmg_mult_cond")):  # broken_extend 已在 D3b 声明乘区族
        check(f"{proc} → {fam}", PP.PROC_FAMILIES.get(proc) == fam,
              f"got {PP.PROC_FAMILIES.get(proc)}")
    check("族执行器 flag_set_cond 已注册", "flag_set_cond" in PP.FAMILY_HANDLERS)
    pp_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "core",
                               "passive_procs.py"), encoding="utf-8").read()
    check("broken_extend 延长段分派进 dmg_mult_cond（mult_kind=broken_extend）",
          '_kind == "broken_extend"' in pp_src
          and 'immune_turns\"] = int(_sh2.get("immune_turns", 0) or 0) + _ext2' in pp_src)
    # broken_extend 只声明一次（dmg_mult_cond）；flag_set_cond 族内无 broken_extend 数值消费
    check("broken_extend 单声明（dmg_mult_cond）",
          pp_src.count('declare_proc("broken_extend"') == 1
          and PP.PROC_FAMILIES.get("broken_extend") == "dmg_mult_cond")
    battle = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "battle.py"),
                  encoding="utf-8").read()
    # 挂点18 区（_skill_hit_settle 方法体）走注册表
    seg18 = battle.split("    def _skill_hit_settle")[1]
    seg18 = seg18.split("    def _skill_passive_dmg_bonus")[0] if "    def _skill_passive_dmg_bonus" in seg18 else seg18
    check("挂点18 调 element_affinity/dirge_ctrl_up/broken_extend 分发",
          'flag_kind": "elem_affinity"' in seg18
          and 'flag_kind": "dirge_ctrl_up"' in seg18
          and 'flag_kind": "broken_extend"' in seg18)
    old_reads18 = [s for s in ('_ps_ea.get', '_ps_dg.get("add", 1)', '_ps_be.get("extend", 1)')
                   if s in seg18]
    check("挂点18 无 3 proc 旧直读残留", not old_reads18, str(old_reads18))
    # 挂点19 _skill_heal：heal_overflow_shield 走注册表；heal_shield 非 52 原位保留
    seg19 = battle.split("    def _skill_heal")[1]
    seg19 = seg19.split("    def _skill_buff")[0]
    check("挂点19 调 heal_overflow_shield 分发（flag_kind）",
          'flag_kind": "heal_overflow_shield"' in seg19)
    check("挂点19 heal_shield（非52）原位循环保留", '_ps.get("pct", _hpdef)' in seg19)
    # 挂点20 _skill_buff melody_duet 走注册表
    seg20 = battle.split("    def _skill_buff")[1]
    seg20 = seg20.split("    def _skill_hit_settle")[0]
    check("挂点20 调 melody_duet 分发（flag_kind）", 'flag_kind": "melody_duet"' in seg20)
    old_reads20 = [s for s in ('_ps_md.get', '_mel_md["stack"] = min')
                   if s in seg20]
    check("挂点20 无 melody_duet 旧直读残留", not old_reads20, str(old_reads20))
    # 挂点23 _turn_start shaken_decay_half 走注册表
    seg23 = battle.split("    def _turn_start")[1]
    seg23 = seg23.split("    def _dual_form")[0] if "    def _dual_form" in seg23 else seg23[:6000]
    check("挂点23 调 shaken_decay_half 分发（flag_kind）",
          'flag_kind": "shaken_decay_half"' in seg23)
    old_reads23 = [s for s in ('_ps_dh.get', '_eb_sh["val"] = int(')
                   if s in seg23]
    check("挂点23 无 shaken_decay_half 旧直读残留", not old_reads23, str(old_reads23))
    # 计数：6 proc 中 5 新声明（broken_extend 已 D3b 声明）→ 40+5=45 声明；族不变 17
    check("PROC_FAMILIES 含 45 声明", len(PP.PROC_FAMILIES) == 45, str(len(PP.PROC_FAMILIES)))
    check("FAMILY_HANDLERS 共 17 族", len(PP.FAMILY_HANDLERS) == 17, str(list(PP.FAMILY_HANDLERS)))
    # 零默认值：_ps 空 dict → 全 proc 不触发（纯置位型 element_affinity/shaken_decay_half
    # 学到即触发——零参 proc 无数值门槛，断言其副作用不依赖 _ps 数值字段）
    for proc, fk, extra in (("element_affinity", "elem_affinity", {}),
                            ("broken_extend", "broken_extend", {"shaken": {"immune_turns": 1}}),
                            ("dirge_ctrl_up", "dirge_ctrl_up",
                             {"e_buffs": {"stun": 2}}),
                            ("melody_duet", "melody_duet",
                             {"melody": {"name": "x", "stack": 2}, "max_stack": 5}),
                            ("heal_overflow_shield", "heal_overflow_shield",
                             {"target_unit": {"hp": 300, "max_hp": 400},
                              "hp_before": 300, "heal": 200, "target_ally": None,
                              "overflow_shield_turns": 2})):
        ctx = {"player": {}, "ps": {}, "ps_name": "x", "flag_kind": fk}
        ctx.update(extra)
        out = PP.run_proc_family(None, [proc], ctx)
        check(f"空 _ps {proc} → 不触发", out == [], str(out))
    # 零参置位型（shaken_decay_half）：学到即回补（无 _ps 数值依赖——原循环体零参）
    ctx_sh = {"player": {}, "ps": {"proc": "shaken_decay_half"}, "ps_name": "破绽感知",
              "flag_kind": "shaken_decay_half",
              "e_buffs_shaken": {"val": 10, "threshold": 15}, "decay_full": 1.7}
    out_sh = PP.run_proc_family(None, ["shaken_decay_half"], ctx_sh)
    check("shaken_decay_half 零参触发（学到即回补）",
          ctx_sh["e_buffs_shaken"]["val"] == 10 + int(1.7 / 2), str(ctx_sh["e_buffs_shaken"]))


def main():
    clean_db()
    test_element_affinity()
    test_broken_extend()
    test_dirge_ctrl_up()
    test_melody_duet()
    test_heal_overflow_shield()
    test_shaken_decay_half()
    test_static()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()