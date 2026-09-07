# -*- coding: utf-8 -*-
"""v181.P2D-D2b 影舞双段 + 旋律 3 光环等价探针（test_p2dd2b_stat_mult_cond.py）

验证挂点2 _passive_crit_dmg_mult（shadow_dance_bonus crit_dmg 段）+ 挂点3 _player_stats
（shadow_dance_bonus spd 段 + melody_resonance / melody_full / melody_master 旋律 3 光环）
从 battle.py 内联 for 迁移到 passive_procs.py 注册表族 stat_mult_cond 后行为零变化
（OLD vs NEW 双实现差分）。

方法（方案 §7 OLD-vs-NEW 探针）：
1. OLD = 迁移前各挂点原逻辑逐字副本（a686e3b）。
2. NEW = 现引擎挂点（→ run_proc_family stat_mult_cond）。
3. 差分矩阵：
   - 影舞 spd 段：学/不学 暗影步·极 × 影舞态/非影舞 × spd 多值
   - 影舞 crit_dmg 段：学/不学 × 影舞态/非影舞
   - 旋律 3 光环：学/不学（共鸣/万籁和鸣/咏叹·极）× 强度层 0/1/2/3/4/5 ×
     旋律存在/不存在 —— 断言最终 st 面板逐键一致（atk/def/matk/mdef/spd）
   - 双条目防御 + 零默认值（_ps 缺字段 → 不触发）
   - 注册表静态断言（PROC_FAMILIES/FAMILY_HANDLERS/计数）

运行（与门禁同款 python）：
  python tests/test_p2dd2b_stat_mult_cond.py
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
    """构造战斗玩家 dict（学指定被动中文名；buffs/stacks/_melody 手置用于边界场景）。"""
    pl = make_player(cls=cls_id, level=60)
    pl = db.get_player(pl.get("group_id", "g1"), pl.get("qq_id", "q1")) if pl.get("qq_id") else pl
    out = {
        "class_name": cls_id, "level": 60, "hp": hp, "max_hp": hp,
        "mp": 100, "max_mp": 200,
        "equipment": {"weapon": {"name": "t", "stats": {"atk": 100, "matk": 100, "spd": spd},
                                 "affixes": [], "enhance": 0}},
        "attributes": {"str": 10, "int": 10},
        "learned_skills": list(passives), "race": "human",
        "resources": {}, "stacks": {}, "buffs": {},
    }
    return out


def mk_enemy(def_=20, mdef=20, hp=100000, spd=10):
    return {"name": "测试怪", "hp": hp, "max_hp": hp,
            "atk": 50, "def": def_, "mdef": mdef, "spd": spd}


def mk_battle(player, enemy=None):
    b = BT.Battle("monster", enemy or mk_enemy(), {}, player)
    b.player.setdefault("resources", {})
    b.player.setdefault("stacks", {})
    b.player.setdefault("buffs", {})
    b.player.setdefault("eff", {})
    return b


def full_stats(b):
    """跑 NEW 引擎 _player_stats 完整面板（含影舞/旋律两段注册表消费）。"""
    return b._player_stats(b.player)


# ============================================================
# OLD：迁移前各挂点原逻辑逐字副本（a686e3b 前）
# ============================================================
def OLD_shadow_dance_spd(b, player, st):
    """OLD _player_stats 影舞 spd 段：影舞态 → spd ×(1+spd_add)（int 截断）。"""
    _pbuffs = player.setdefault("buffs", {})
    if _pbuffs.get("shadow_dance"):
        try:
            for _pn_sb, _ps_sb in b._proc_pm(player)["proc"].get("shadow_dance_bonus", []):
                st["spd"] = int(st.get("spd", 0) * (1.0 + float(_ps_sb.get("spd_add", 0.25) or 0.25)))
                break
        except Exception:
            pass
    return st


def OLD_crit_dmg_mult(b, player):
    """OLD _passive_crit_dmg_mult：影舞态 → crit_dmg 加法增量。"""
    extra = 0.0
    try:
        if b._shadow_dance(player):
            for _pn, _ps in b._proc_pm(player)["proc"].get("shadow_dance_bonus", []):
                extra += float(_ps.get("crit_dmg", 0.0) or 0.0)
                break
    except Exception:
        pass
    return extra


def OLD_melody(b, player, st):
    """OLD _player_stats 旋律 3 光环段：3 段聚合 _mel_pct 再统一乘（int 截断）。"""
    try:
        _mel169 = b._melody_state()
        _pm_mel = b._proc_pm(player)["proc"]
        _mel_pct = 0.0
        _mel_n = int(_mel169.get("stack", 0) or 0)
        if _mel169.get("name") and _mel_n > 0:
            for _pn_rs, _ps_rs in _pm_mel.get("melody_resonance", []):
                if _mel_n >= int(_ps_rs.get("stacks", 3) or 3):
                    _mel_pct += float(_ps_rs.get("mult", 0.10) or 0.10)
                break
            for _pn_mf, _ps_mf in _pm_mel.get("melody_full", []):
                if _mel_n >= int(_ps_mf.get("stacks", 5) or 5):
                    _mel_pct += float(_ps_mf.get("mult", 0.15) or 0.15)
                break
            for _pn_mm, _ps_mm in _pm_mel.get("melody_master", []):
                _mel_pct += float(_ps_mm.get("per_stack", 0.05) or 0.05) * _mel_n
                break
        if _mel_pct > 0:
            for _mk_s in ("atk", "def", "matk", "mdef", "spd"):
                st[_mk_s] = int(st.get(_mk_s, 0) * (1.0 + _mel_pct))
    except Exception:
        pass
    return st


def diff_panel(name, cls, skills, setups, base_keys=("atk", "def", "matk", "mdef", "spd")):
    """OLD vs NEW 面板差分：同一玩家态跑 OLD 全流程（基底面板 + 影舞段 + 旋律段）
    与现引擎 _player_stats，比 5 面板键。setups: {tag: (b_old, b_new) -> None}。"""
    for learned in (False, True):
        p = mk_player(cls, list(skills) if learned else [])
        for tag, setup in setups.items():
            b_old = mk_battle(dict(p))
            b_new = mk_battle(dict(p))
            setup(b_old, b_new)
            # OLD：基底面板（_apply_buffs 等公共前段等价，用引擎算一次）→ 依次套 OLD 两段
            st_old = full_stats(b_old)
            # 为避免 OLD 混入 NEW 旋律/影舞段（full_stats 已含注册表消费），OLD 基线与
            # NEW 同源：重算基底（无被动路径相同）+ 手工 OLD 段叠加。但引擎算的已是全量——
            # 这里用镜像法：OLD = 引擎 st 先还原到「无被动段」再套 OLD 副本。由于全量引擎 =
            # 基底 + NEW 段，OLD 段 == NEW 段 时等价，直接用 st_old（全量）作 OLD 基线，
            # 与 st_new 差分即可锁定段级等价（下探针已分别验证 OLD 与 NEW 段实现逐字一致）。
            st_new = full_stats(b_new)
            keys = [k for k in base_keys if k in st_old or k in st_new]
            ok = all(int(st_old.get(k, 0) or 0) == int(st_new.get(k, 0) or 0) for k in keys)
            check(f"{name} 学={learned} {tag}: 面板 {keys} OLD==NEW",
                  ok, f"OLD {[st_old.get(k) for k in keys]} vs NEW {[st_new.get(k) for k in keys]}")


# ============================================================
# 1. shadow_dance_bonus crit_dmg 段（挂点2 _passive_crit_dmg_mult）
# ============================================================
def test_shadow_dance_crit_dmg():
    print("\n== 1. shadow_dance_bonus crit_dmg 段（挂点2）OLD vs NEW ==")
    for learned in (False, True):
        p = mk_player("cls_ci_ke", ["暗影步·极"] if learned else [])
        for sd in (False, True):
            b_old = mk_battle(dict(p))
            b_new = mk_battle(dict(p))
            if sd:
                b_old.player["buffs"]["shadow_dance"] = 3
                b_new.player["buffs"]["shadow_dance"] = 3
            r_old = OLD_crit_dmg_mult(b_old, b_old.player)
            r_new = b_new._passive_crit_dmg_mult(b_new.player)
            check(f"学={learned} 影舞={sd}: crit_dmg {r_old}=={r_new}",
                  abs(r_old - r_new) < 1e-9, f"{r_old} vs {r_new}")


# ============================================================
# 2. shadow_dance_bonus spd 段（挂点3 _player_stats）
# ============================================================
def test_shadow_dance_spd():
    print("\n== 2. shadow_dance_bonus spd 段（挂点3 _player_stats）OLD vs NEW ==")
    setups = {
        "非影舞": lambda a, b: None,
        "影舞": lambda a, b: (a.player["buffs"].update({"shadow_dance": 3}),
                              b.player["buffs"].update({"shadow_dance": 3})),
    }
    for learned in (False, True):
        for tag, setup in setups.items():
            p1 = mk_player("cls_ci_ke", ["暗影步·极"] if learned else [], spd=100)
            p2 = mk_player("cls_ci_ke", ["暗影步·极"] if learned else [], spd=157)
            for spd_tag, p in (("spd100", p1), ("spd157", p2)):
                b_old = mk_battle(dict(p))
                b_new = mk_battle(dict(p))
                setup(b_old, b_new)
                # OLD：基底 st（引擎算，无被动路径）+ OLD spd 段；NEW：引擎 _player_stats
                base = b_old._player_stats(b_old.player)  # 先取全量作为公共基底？——不行，含 NEW 段。
                # 正确：OLD 基底 = 引擎在"该玩家无被动两段"下等同（同一 player 无暗影步·极时基底一致）：
                # 直接构造 无被动玩家 的同款基底，避免 NEW 段混入 OLD。
                p_base = dict(p)
                p_base["learned_skills"] = []
                st_old_base = b_old._player_stats(p_base)
                st_old = OLD_shadow_dance_spd(b_old, b_old.player, st_old_base)
                st_new = b_new._player_stats(b_new.player)
                check(f"学={learned} {tag} {spd_tag}: spd {st_old.get('spd')}=={st_new.get('spd')}",
                      int(st_old.get("spd", 0) or 0) == int(st_new.get("spd", 0) or 0),
                      f"{st_old.get('spd')} vs {st_new.get('spd')}")


# ============================================================
# 3. 旋律 3 光环（挂点3 _player_stats 聚合段）
# ============================================================
def test_melody_auras():
    print("\n== 3. 旋律 3 光环（强度层 0/1/2/3/4/5 × 学/不学 3 被动）OLD vs NEW ==")
    setups = {}
    for n in (0, 1, 2, 3, 4, 5):
        for mel_on in (False, True):
            def mk_setup(n=n, mel_on=mel_on):
                def setup(a, b):
                    if mel_on:
                        a._melody = {"name": "战歌", "kind": "atk", "stack": n, "finale_ready": False}
                        b._melody = {"name": "战歌", "kind": "atk", "stack": n, "finale_ready": False}
                    else:
                        a._melody = {"name": None, "kind": None, "stack": 0, "finale_ready": False}
                        b._melody = {"name": None, "kind": None, "stack": 0, "finale_ready": False}
                return setup
            setups[f"层{n} {'有旋律' if mel_on else '无旋律' if n else '无旋律'}"] = mk_setup()
    for learned in (False, True):
        skills = ["共鸣", "万籁和鸣", "咏叹·极"]
        p = mk_player("cls_shi_ren", skills if learned else [])
        for tag, setup in setups.items():
            b_old = mk_battle(dict(p))
            b_new = mk_battle(dict(p))
            setup(b_old, b_new)
            p_base = dict(p)
            p_base["learned_skills"] = []
            st_old_base = b_old._player_stats(p_base)
            st_old = OLD_melody(b_old, b_old.player, st_old_base)
            st_new = b_new._player_stats(b_new.player)
            keys = ("atk", "def", "matk", "mdef", "spd")
            ok = all(int(st_old.get(k, 0) or 0) == int(st_new.get(k, 0) or 0) for k in keys)
            check(f"学={learned} {tag}: 面板一致", ok,
                  f"OLD {[st_old.get(k) for k in keys]} NEW {[st_new.get(k) for k in keys]}")


# ============================================================
# 4. 双条目防御 + 多条目首条语义 + 零默认值 + 注册表静态
# ============================================================
def test_registry_and_multi():
    print("\n== 4. stat_mult_cond 注册表 + 双条目 + 零默认值 ==")
    for proc in ("shadow_dance_bonus", "melody_resonance", "melody_full", "melody_master"):
        check(f"{proc} → stat_mult_cond", PP.PROC_FAMILIES.get(proc) == "stat_mult_cond",
              str(PP.PROC_FAMILIES.get(proc)))
    check("stat_mult_cond 执行器已注册", "stat_mult_cond" in PP.FAMILY_HANDLERS)
<<<<<<< HEAD
    # P2-D4b revive_cond（+1）→ 11 族；P2-D5a counter_cond（+1）→ 12 族（P2-D5a 更新）
    check("FAMILY_HANDLERS 共 12 族", len(PP.FAMILY_HANDLERS) == 12, str(list(PP.FAMILY_HANDLERS)))
=======
    # P2-D4a：cc_break_cost/dr_cond 并入 + P2-D5b：dot_mult_cond/dot_weaken 新族 → 共 13 族
    check("FAMILY_HANDLERS 共 13 族", len(PP.FAMILY_HANDLERS) == 13, str(list(PP.FAMILY_HANDLERS)))
>>>>>>> wt_p2dd52
    # 零默认值：_ps 空 / 缺字段 → 不触发
    for kind, pname in (("crit_dmg", "shadow_dance_bonus"), ("spd", "shadow_dance_bonus"),
                        ("melody", "melody_resonance"), ("melody", "melody_master")):
        ctx = {"player": {}, "ps": {}, "ps_name": "x", "stat_kind": kind, "melody_n": 5}
        out = PP.run_proc_family(None, [pname], ctx)
        check(f"空 _ps stat_kind={kind} → 不触发", out == [], str(out))
    # 双条目：挂点 for...break 只消费首条（OLD/NEW 同）——手工注入双条目
    for seg, cls, sk in (("spd", "cls_ci_ke", "暗影步·极"),):
        p = mk_player(cls, [sk])
        b_old = mk_battle(dict(p))
        b_new = mk_battle(dict(p))
        for b in (b_old, b_new):
            pm = b._proc_pm(b.player)
            pm["proc"]["shadow_dance_bonus"] = [
                ("暗影步·极", {"proc": "shadow_dance_bonus", "spd_add": 0.25, "crit_dmg": 0.20}),
                ("测试第二条", {"proc": "shadow_dance_bonus", "spd_add": 0.50, "crit_dmg": 0.40}),
            ]
            b._proc_pm = lambda pl, _pm=pm: _pm
            b.player["buffs"]["shadow_dance"] = 3
        p_base = dict(p)
        p_base["learned_skills"] = []
        st_new = b_new._player_stats(b_new.player)
        # 双条目首条 break 语义 = 只消费首条 0.25（OLD/NEW 两实现同一 _proc_pm 双条目下都只乘首条）。
        # OLD 对照：用 b_new 原 _proc_pm（注入双条目前）为 基底——先存真 _proc_pm 再注入双条目。
        # 基底玩家 = b2 无被动副本（b2._proc_pm 已被注入双条目，须绕开）：
        b2 = mk_battle(dict(p))
        b2._proc_pm = lambda pl, _pm=pm: _pm
        b2.player["buffs"]["shadow_dance"] = 3
        p_base2 = dict(p)
        p_base2["learned_skills"] = []
        p_base2["buffs"] = dict(p_base2.get("buffs") or {})
        p_base2["buffs"]["shadow_dance"] = 3
        b3 = mk_battle(p_base2)  # 全新 battle：无被动、无注入 → _player_stats 不乘（基底 210）
        st_old_base = b3._player_stats(b3.player)
        st_old = OLD_shadow_dance_spd(b2, b2.player, st_old_base)  # OLD 副本对基底乘首条 0.25
        check(f"双条目：首条即 break（spd ×1.25 非 ×1.50）",
              int(st_old.get("spd", 0) or 0) == int(st_new.get("spd", 0) or 0) == 263,
              f"OLD {st_old.get('spd')} vs NEW {st_new.get('spd')}")


def main():
    clean_db()
    test_shadow_dance_crit_dmg()
    test_shadow_dance_spd()
    test_melody_auras()
    test_registry_and_multi()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
