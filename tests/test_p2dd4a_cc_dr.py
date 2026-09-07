# -*- coding: utf-8 -*-
"""v181.P2D-D4a 受击减伤/免控族等价探针（test_p2dd4a_cc_dr.py）

验证挂点10 player_turn 免控段 + 挂点11 _mitigate_chain 条件减伤聚合段 6 proc
（tenacity / zhan_yi_full_reduce / core_full / core_reduce / core_last_stand /
core_overflow）从 battle.py 内联 for 迁移到 passive_procs 注册表族 cc_break_cost /
dr_cond（ctx cc_kind/dr_kind 分派）后行为零变化（OLD vs NEW 双实现差分）。

方法（方案 §7 OLD-vs-NEW 探针）：
1. OLD = 迁移前各挂点原逻辑副本（内联 for 逐字复刻 ef8e7b9^）。
2. NEW = 现引擎方法（→ run_proc_family）。
3. 差分矩阵：
   - tenacity：学/不学 × 战意 0/1/2/10 × 剩余次数 0/1/3（flag 走 battle 属性，
     含 setattr 预置模拟序列化恢复）× 触发后次数递减 + 战意扣减 + 日志
   - zhan_yi_full_reduce 免眩晕：学/不学 × 战意 9/10 × stun 有无
   - core_full 免控窗口：学/不学 × 磐核 0/5 × cc_immune 现值 0/1（max 语义）
   - zhan_yi_full_reduce/core_full/core_reduce/core_last_stand 减伤：
     学/不学 × 战意 9/10 × 磐核 0/3/5 × _core_last_stand_used False/True
   - core_overflow 转盾：学/不学 × 磐核 2/3 × dmg 边界 → 盾值/键/日志/刻数
   - 序列化 flag 恢复：battle 属性预置 _tenacity_left_n/_core_last_stand_used
     （等价 from_state 恢复）后行为与 OLD 一致

运行（与门禁同款 python）：
  python tests/test_p2dd4a_cc_dr.py
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
        "resources": {}, "stacks": {}, "buffs": {},
    }
    return out


def mk_enemy(def_=20, mdef=20, hp=100000, spd=10):
    return {"name": "测试怪", "hp": hp, "max_hp": hp,
            "atk": 50, "def": def_, "mdef": mdef, "spd": spd}


def mk_battle(player, enemy=None, keep_player_copy=False):
    """构造战斗玩家 dict 副本（默认深拷贝防 Battle 内 setdefault 污染 OLD 参考源）。"""
    b = BT.Battle("monster", enemy or mk_enemy(), {}, copy.deepcopy(player))
    b.player.setdefault("resources", {})
    b.player.setdefault("stacks", {})
    b.player.setdefault("buffs", {})
    b.player.setdefault("shields", {})
    b.player.setdefault("eff", {})
    return b


def _ps_of(b, player, proc):
    """取 pm 中某 proc 首条 passive dict（无 = None）。"""
    pm = b._proc_pm(player)
    lst = pm["proc"].get(proc) or []
    return lst[0] if lst else None


# ============================================================
# OLD：迁移前各挂点原逻辑副本（ef8e7b9^ 逐字复刻）
# ============================================================
def OLD_tenacity_break(b, player, logs):
    """迁移前 _tenacity_try_break 方法体原逻辑。"""
    try:
        _pm = b._proc_pm(player)
        if not _pm["proc"].get("tenacity"):
            return False
        _ps = _pm["proc"]["tenacity"][0][1]
        cost = int(_ps.get("cost", 2) or 2)
        if b._zhan_yi_n() < cost:
            return False
        if b._tenacity_left() <= 0:
            return False
        b._p_stacks()["zhan_yi"] = max(0, b._zhan_yi_n() - cost)
        b._tenacity_left_n = b._tenacity_left() - 1
        _pn = _pm["proc"]["tenacity"][0][0]
        logs.append(f"🛡️ {_pn}：消耗 {cost} 层战意挣脱控制！（剩余 {b._tenacity_left()} 次）")
        return True
    except Exception:
        return False


def OLD_stun_clear(b, player, logs):
    """迁移前挂点10 坚城之姿免眩晕循环体（含外层 `if stun` 守卫——原挂点骨架）。"""
    if "stun" not in b._p_buffs_bag():
        return
    try:
        for _pn_zy, _ps_zy in b._proc_pm(player)["proc"].get("zhan_yi_full_reduce", []):
            if b._zhan_yi_n() >= int(_ps_zy.get("stacks", 10) or 10):
                b._p_buffs_bag().pop("stun", None)
                logs.append(f"🛡️ {_pn_zy}：战意圆满，眩晕不侵！")
            break
    except Exception:
        pass


def OLD_cc_window(b, player):
    """迁移前挂点10 磐石之躯免控窗口循环体。"""
    try:
        for _pn_cf, _ps_cf in b._proc_pm(player)["proc"].get("core_full", []):
            if b._guard_core_n() >= int(_ps_cf.get("stacks", 5) or 5):
                b._p_buffs_bag()["cc_immune"] = max(int(b._p_buffs_bag().get("cc_immune", 0) or 0), 1)
            break
    except Exception:
        pass


def OLD_dr_segment(b, actor, dmg, logs):
    """迁移前挂点11 条件减伤聚合段（5 段循环体 + 汇总）逐字复刻（含 core_overflow 转盾副作用）。

    返回 (reduce_total, dr_pct)——挂点据此 dmg = max(1, dmg - reduce_total)。
    """
    try:
        _pm_dr = b._proc_pm(actor)
        _dr_pct = 0.0
        # 坚城之姿
        for _pn2, _ps2 in _pm_dr["proc"].get("zhan_yi_full_reduce", []):
            if b._zhan_yi_n() >= int(_ps2.get("stacks", 10) or 10):
                _dr_pct += float(_ps2.get("reduce", 0.10) or 0.10)
            break
        # 磐石之躯 / 大地之肤（磐核档）
        for _pn2, _ps2 in _pm_dr["proc"].get("core_full", []):
            if b._guard_core_n() >= int(_ps2.get("stacks", 5) or 5):
                _dr_pct += float(_ps2.get("reduce", 0.20) or 0.20)
            break
        for _pn2, _ps2 in _pm_dr["proc"].get("core_reduce", []):
            _gn = b._guard_core_n()
            if _gn > 0:
                _dr_pct += float(_ps2.get("per_core", 0.02) or 0.02) * _gn
            break
        # 不动如山：已触发后（hp<30%）减伤 40% 持续生效
        if getattr(b, "_core_last_stand_used", False):
            for _pn2, _ps2 in _pm_dr["proc"].get("core_last_stand", []):
                _dr_pct += float(_ps2.get("reduce", 0.40) or 0.40)
                break
        # 磐石之心：磐核 ≥3 → 溢出承伤转护盾（护盾 = 超过 hp 上限部分的伤害额 80%，3 刻）
        for _pn2, _ps2 in _pm_dr["proc"].get("core_overflow", []):
            if b._guard_core_n() >= int(_ps2.get("stacks", 3) or 3):
                _ov_sh = int(dmg * float(_ps2.get("shield_pct", 0.80) or 0.80))
                if _ov_sh > 0:
                    b._add_shield("core_overflow", _ov_sh, int(_ps2.get("turns", 3) or 3))
                    logs.append(f"🪨 磐石之心：磐核 {b._guard_core_n()} 枚，承伤转化 {_ov_sh} 点护盾！")
            break
        reduce_total = 0
        if _dr_pct > 0:
            reduce_total = int(dmg * min(_dr_pct, 0.9))
        if reduce_total:
            logs.append(f"🛡️ 被动减伤 {reduce_total} 点")
        return reduce_total
    except Exception:
        return 0


def run_new_mitigate_dr(b, actor, dmg, logs):
    """NEW：跑现引擎 _mitigate_chain 全链（含首触发生产段——未置位且 hp<30% 先补核）。

    用 actor=player dict，构造满足 actor 守卫的数据源。返回处理后 dmg（与 OLD_reduce 可比）。
    """
    # 保证 _mitigate_chain actor 守卫通过（有 class_name 即可）
    nd, _interrupted = b._mitigate_chain(actor, dmg, logs)
    return nd


# ============================================================
# 1. tenacity（战意挡控，3 次/场；flag _tenacity_left_n battle 属性序列化）
# ============================================================
def test_tenacity():
    print("\n== 1. tenacity（挂点10 _tenacity_try_break → cc_break_cost）OLD vs NEW ==")
    for learned in (False, True):
        p = mk_player("cls_zhan_shi", ["坚韧"] if learned else [])
        for zy in (0, 1, 2, 10):
            for left in (0, 1, 3):
                for preseed in (None, 2):
                    b_old = mk_battle(dict(p))
                    b_new = mk_battle(dict(p))
                    for b in (b_old, b_new):
                        b.player["stacks"]["zhan_yi"] = zy
                        if preseed is not None:
                            b._tenacity_left_n = preseed  # 模拟 from_state 恢复 flag
                    logs_o, logs_n = [], []
                    r_old = OLD_tenacity_break(b_old, b_old.player, logs_o)
                    r_new = b_new._tenacity_try_break(b_new.player, logs_n)
                    same = (r_old == r_new
                            and b_old._zhan_yi_n() == b_new._zhan_yi_n()
                            and getattr(b_old, "_tenacity_left_n", 3) == getattr(b_new, "_tenacity_left_n", 3)
                            and logs_o == logs_n)
                    check(f"学={learned} 战意{zy} 剩余{preseed if preseed is not None else '缺省'}"
                          f"→{getattr(b_old,'_tenacity_left_n',3)}: r={r_old}=={r_new} 战意/次数/logs 一致",
                          same, f"OLD {r_old}/{b_old._zhan_yi_n()}/{getattr(b_old,'_tenacity_left_n',3)}/{logs_o} "
                                f"NEW {r_new}/{b_new._zhan_yi_n()}/{getattr(b_new,'_tenacity_left_n',3)}/{logs_n}")
    # 耗尽边界：3 次连续触发后第 4 次不触发（flag 在 battle 属性递减，0 次不复活）
    p = mk_player("cls_zhan_shi", ["坚韧"])
    b = mk_battle(dict(p))
    hits = 0
    for _i in range(5):
        b.player["stacks"]["zhan_yi"] = 10
        b.player["buffs"]["stun"] = 1
        logs = []
        if b._tenacity_try_break(b.player, logs):
            hits += 1
        else:
            break
    check("耗尽边界：3 次触发后第 4 次不触发", hits == 3 and b._tenacity_left() == 0,
          f"hits={hits} 战意={b._zhan_yi_n()} 剩余={b._tenacity_left()}")


# ============================================================
# 2. zhan_yi_full_reduce 免眩晕（挂点10 stun_clear）
# ============================================================
def test_zy_full_stun_clear():
    print("\n== 2. zhan_yi_full_reduce 免眩晕（挂点10）OLD vs NEW ==")
    for learned in (False, True):
        p = mk_player("cls_zhan_shi", ["坚城之姿"] if learned else [])
        for zy in (9, 10):
            for has_stun in (False, True):
                b_old = mk_battle(dict(p))
                b_new = mk_battle(dict(p))
                for b in (b_old, b_new):
                    b.player["stacks"]["zhan_yi"] = zy
                    if has_stun:
                        b.player["buffs"]["stun"] = 1
                logs_o, logs_n = [], []
                OLD_stun_clear(b_old, b_old.player, logs_o)
                # NEW：复刻现挂点骨架（if stun + for + run + break）
                if "stun" in b_new._p_buffs_bag():
                    try:
                        for _pn_zy, _ps_zy in b_new._proc_pm(b_new.player)["proc"].get("zhan_yi_full_reduce", []):
                            _c = {"player": b_new.player, "ps": _ps_zy, "ps_name": _pn_zy,
                                  "cc_kind": "stun_clear", "logs": logs_n}
                            PP.run_proc_family(b_new, "zhan_yi_full_reduce", _c)
                            break
                    except Exception:
                        pass
                same = (("stun" in b_old._p_buffs_bag()) == ("stun" in b_new._p_buffs_bag())
                        and logs_o == logs_n)
                check(f"学={learned} 战意{zy} stun={has_stun}: stun 清除/日志一致",
                      same, f"{'stun' in b_old._p_buffs_bag()} vs {'stun' in b_new._p_buffs_bag()} / {logs_o} vs {logs_n}")


# ============================================================
# 3. core_full 免控窗口（挂点10 cc_window：max 语义）
# ============================================================
def test_core_full_cc_window():
    print("\n== 3. core_full 免控窗口（挂点10）OLD vs NEW ==")
    for learned in (False, True):
        p = mk_player("cls_wu_seng", ["磐石之躯"] if learned else [])
        for gc in (0, 5):
            for cc_cur in (0, 1, 7):
                b_old = mk_battle(dict(p))
                b_new = mk_battle(dict(p))
                for b in (b_old, b_new):
                    b.player["resources"]["guard_core"] = gc
                    if cc_cur:
                        b.player["buffs"]["cc_immune"] = cc_cur
                OLD_cc_window(b_old, b_old.player)
                try:
                    for _pn_cf, _ps_cf in b_new._proc_pm(b_new.player)["proc"].get("core_full", []):
                        _c = {"player": b_new.player, "ps": _ps_cf, "ps_name": _pn_cf,
                              "cc_kind": "cc_window"}
                        PP.run_proc_family(b_new, "core_full", _c)
                        break
                except Exception:
                    pass
                v_old = b_old._p_buffs_bag().get("cc_immune")
                v_new = b_new._p_buffs_bag().get("cc_immune")
                check(f"学={learned} 磐核{gc} cc现值{cc_cur}: {v_old}=={v_new}",
                      v_old == v_new, f"{v_old} vs {v_new}")


# ============================================================
# 4. 挂点11 减伤聚合 + 磐核溢出转盾（_mitigate_chain 全链差分）
# ============================================================
def test_mitigate_dr():
    print("\n== 4. 挂点11 _mitigate_chain 减伤聚合 + core_overflow 转盾 OLD vs NEW ==")
    # 组合矩阵：战士（坚城之姿）/ 拳师（磐石之躯+大地之肤+不动如山+磐石之心 单/全组合）
    combos = [
        ("cls_zhan_shi", [], "无被动"),
        ("cls_zhan_shi", ["坚城之姿"], "坚城之姿"),
        ("cls_wu_seng", [], "无被动"),
        ("cls_wu_seng", ["磐石之躯"], "磐石之躯"),
        ("cls_wu_seng", ["磐石之躯", "大地之肤"], "磐躯+大地"),
        ("cls_wu_seng", ["不动如山"], "不动如山(未触发)"),
        ("cls_wu_seng", ["磐石之心"], "磐石之心"),
        ("cls_wu_seng", ["磐石之躯", "大地之肤", "不动如山", "磐石之心"], "磐核全族"),
    ]
    for cls, sk, label in combos:
        p = mk_player(cls, sk)
        for zy in (9, 10):
            for gc in (0, 2, 3, 5):
                for ls_used in (False, True):
                    for dmg in (1, 100, 999):
                        # last_stand 常驻段只在已置位时生效——不学不动如山时置位无条目 = 无影响
                        b_old = mk_battle(dict(p), mk_enemy())
                        b_new = mk_battle(dict(p), mk_enemy())
                        for b in (b_old, b_new):
                            b.player["stacks"]["zhan_yi"] = zy
                            b.player["resources"]["guard_core"] = gc
                            if ls_used:
                                b._core_last_stand_used = True  # 模拟序列化恢复已触发
                        logs_o, logs_n = [], []
                        rt_old = OLD_dr_segment(b_old, b_old.player, dmg, logs_o)
                        # NEW：直接跑现引擎 _mitigate_chain 全链（守卫需 class_name+... 通过）
                        d_new, _inter = b_new._mitigate_chain(b_new.player, dmg, logs_n)
                        # OLD 端还原最终 dmg（聚合段外无其它减伤——actor 无 buffs/装备特效）
                        d_old = max(1, dmg - rt_old)
                        sh_old = dict(b_old.player.get("shields") or {})
                        sh_new = dict(b_new.player.get("shields") or {})
                        same = (d_old == d_new and sh_old == sh_new and logs_o == logs_n)
                        tag = f"[{label}] 战意{zy} 磐核{gc} 置位{ls_used} dmg{dmg}"
                        check(f"{tag}: dmg {d_old}=={d_new} 盾/日志一致",
                              same, f"OLD d={d_old} 盾{sh_old} logs{logs_o} | NEW d={d_new} 盾{sh_new} logs{logs_n}")
    # 磐核 3/4 层转盾边界特写：dmg 小到 int(dmg*0.8)==0 → 不转盾（ov_sh>0 守卫）
    p = mk_player("cls_wu_seng", ["磐石之心"])
    b = mk_battle(dict(p), mk_enemy())
    b.player["resources"]["guard_core"] = 3
    logs = []
    d1, _ = b._mitigate_chain(b.player, 1, logs)
    check("磐核3 dmg=1: int(1*0.8)=0 不转盾无日志", d1 == 1 and not logs,
          f"d={d1} logs={logs}")
    sh = b.player.get("shields") or {}
    check("磐核3 dmg=1: 无 shield 键", "core_overflow" not in sh, str(sh))


# ============================================================
# 5. 序列化 flag 恢复后行为（from_state 等价：battle 属性预置）
# ============================================================
def test_serialized_flags():
    print("\n== 5. 序列化 flag 恢复（_tenacity_left_n/_core_last_stand_used）行为 ==")
    # tenacity：恢复剩余 1 次 → 还能触发 1 次，之后停
    p = mk_player("cls_zhan_shi", ["坚韧"])
    b = mk_battle(dict(p))
    b._tenacity_left_n = 1  # from_state 'tenacity_left':1
    hits = 0
    for _i in range(3):
        b.player["stacks"]["zhan_yi"] = 10
        b.player["buffs"]["stun"] = 1
        if b._tenacity_try_break(b.player, []):
            hits += 1
        else:
            break
    check("恢复剩余1次 → 再触发 1 次即停", hits == 1 and b._tenacity_left() == 0, f"hits={hits}")
    # core_last_stand：恢复已触发 → 常驻 40% 减伤；未触发（hp≥30% 无首触发）→ 0
    p2 = mk_player("cls_wu_seng", ["不动如山"], hp=500)
    b2 = mk_battle(dict(p2), mk_enemy())
    b2._core_last_stand_used = True
    logs = []
    d2, _ = b2._mitigate_chain(b2.player, 1000, logs)
    # 真实引擎完整链：1000 - 40%（last_stand 常驻）= 600；日志含被动减伤 400 点
    check("置位恢复 → 常驻减伤生效 dmg 1000-400=600", d2 == 600 and any("被动减伤" in s and "400" in s for s in logs),
          f"d={d2} logs={logs}")
    # 不动如山未触发 + 高血量 → 无首触发生产、无常驻减伤（首触发生产段在 hp<30% 才补核）
    p3 = mk_player("cls_wu_seng", ["不动如山"], hp=500)
    b3 = mk_battle(dict(p3), mk_enemy())
    d3, _ = b3._mitigate_chain(b3.player, 1000, [])
    check("未置位 hp 100% → 无减伤 dmg 1000 原样", d3 == 1000 and not getattr(b3, "_core_last_stand_used", False),
          f"d={d3}")


# ============================================================
# 6. 静态：注册表声明族/映射 + 旧直读残留清零
# ============================================================
def test_static():
    print("\n== 6. 静态：P2-D4a 6 proc 声明 + 挂点改造痕迹 ==")
    for proc, fam in (("tenacity", "cc_break_cost"),
                      ("zhan_yi_full_reduce", "dr_cond"),
                      ("core_full", "dr_cond"),
                      ("core_reduce", "dr_cond"),
                      ("core_last_stand", "dr_cond"),
                      ("core_overflow", "dr_cond")):
        check(f"{proc} → {fam}", PP.PROC_FAMILIES.get(proc) == fam,
              f"got {PP.PROC_FAMILIES.get(proc)}")
    for fam in ("cc_break_cost", "dr_cond"):
        check(f"族执行器 {fam} 已注册", fam in PP.FAMILY_HANDLERS)
    battle = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "battle.py"),
                  encoding="utf-8").read()
    # 挂点10 免控三处走注册表
    check("挂点10 _tenacity_try_break 调 run_proc_family",
          '_run_proc_family(self, "tenacity"' in battle)
    check("挂点10 坚城免眩晕 cc_kind=stun_clear",
          '"cc_kind": "stun_clear"' in battle)
    check("挂点10 磐石免控 cc_kind=cc_window",
          '"cc_kind": "cc_window"' in battle)
    # 挂点11 减伤五段走注册表（dr_kind 分派 5 谓词）
    for dk in ("zy_full", "core_full", "per_core", "last_stand", "overflow_shield"):
        check(f"挂点11 dr_kind={dk}", f'"dr_kind": "{dk}"' in battle)
    # 旧直读残留清零：挂点10/11 区不再直读 _ps.get(stacks/reduce/per_core/shield_pct)
    m11 = battle.split("_pm_dr = self._proc_pm(actor)")[1].split("if reduce_total:")[0]
    old_reads = [s for s in ('_ps2.get("stacks"', '_ps2.get("reduce"', '_ps2.get("per_core"',
                            '_ps2.get("shield_pct"', "_ps_zy.get(\"stacks\"", "_ps_cf.get(\"stacks\"")
                  if s in m11]
    check("挂点11 聚合段无 5 proc 旧直读残留", not old_reads, str(old_reads))
    # 一次性 flag 序列化键仍保留（to_state/from_state 未动）
    check("to_state tenacity_left/core_last_stand_used 保留",
          '"tenacity_left": getattr' in battle and '"core_last_stand_used": getattr' in battle)
    # 首触发生产段（不动如山补磐核）未误碰——保留 getattr _core_last_stand_used 判定 + RES 补核
    check("首触发生产段保留（未置位补磐核）", battle.count('"_core_last_stand_used", False)') >= 2)


def main():
    clean_db()
    test_tenacity()
    test_zy_full_stun_clear()
    test_core_full_cc_window()
    test_mitigate_dr()
    test_serialized_flags()
    test_static()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
