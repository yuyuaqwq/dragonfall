# -*- coding: utf-8 -*-
"""v181.P2D-D6 tick 族收敛等价探针（test_p2dd6_tick_families.py）

验证 battle.py 顶部模块级 tick handler 的 4 个被动 proc 分支（focus_regen_summon /
arcane_intuition / undead_faith / faith_overload_heal）从模块级 tick handler 内联
for 迁移到 passive_procs 注册表族（tick_regen/tick_mech_charge/tick_faith）后
行为零变化（OLD vs NEW 双实现差分 + 触发边界矩阵 + 静态残留清零）。

方法（方案 §7 OLD-vs-NEW 探针，沿 test_p2dd4b_revive 先例）：
1. OLD = 迁移前 _th_passive_heal/_th_mech_charge/_th_faith_decay 三个 handler 的
   逐字副本（tests/ref_p2dd6_old_tick.py），注册进克隆 _TICK_HANDLERS 字典，
   用与 NEW 完全相同的调度顺序（_tick_regen 兼容壳按注册顺序跑全部族）驱动。
2. NEW = 现引擎 _tick_regen（handler 内 proc 分支已改查注册表族）。
3. 差分矩阵（每 proc 学/不学 × 触发边界）：
   - focus_regen_summon：召唤物在/不在 × 宠物-only × energy 0/满/缺资源袋
   - arcane_intuition：arcane 0/4（满 5 封顶）× focus 态 开/关 × 缺 stacks 袋
   - undead_faith：亡灵在场数 0/1/2（骷髅 + 亡灵名敌）× faith 0.5/5/9.5（过载边界）
     × faith_exhausted buff 0/1（虚弱期）——先产后衰顺序链
   - faith_overload_heal：信念 ≥max 过载路径 学/不学 × heal_up 乘算 × hp<max
     回血落地 + 无圣化置 faith_exhausted=6 + 有圣化免力竭
   - 通道开关名单（_regen_needed/_ensure_regen_effects）：proc 名是"卡片存在性"
     检查键——注册表化后 proc 名不变 → 名单逻辑不动（断言名单原样保留）
4. 静态：4 proc 声明族映射正确、族执行器已注册、KNOWN_GAPS 移除 4 个 E 类成员、
   battle.py tick handler 区不再直读 4 proc 旧字段（残留清零）、非 52 同族
   （turn_heal/team_regen/arcane_regen/spellblade_regen）原样留在 handler、
   tick 注册表（passive_heal/mech_charge/faith_decay → _TICK_HANDLERS）原样保留。

OLD 侧公平性：NEW 的 _tick_regen 兼容壳会依次跑注册顺序的全部 handler（含
core_regen 自然回资源——测试玩家职业核心资源 rd.regen>0 时 NEW 恒多一段）——
OLD 副本同样经克隆注册表 + 同一 _tick_regen 兼容壳驱动（handler 换成 OLD 版），
除目标 proc 分支的实现差异外调度路径逐位一致。

运行（与门禁同款 python）：
  python tests/test_p2dd6_tick_families.py
"""
import os
import sys
import copy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import C, db, clean_db  # noqa: E402
from data.plugins.dragonfall.game import engine as EG  # noqa: E402
from data.plugins.dragonfall.game import battle as BT  # noqa: E402
from data.plugins.dragonfall.game.core import passive_procs as PP  # noqa: E402
from tests import ref_p2dd6_old_tick as OLD  # noqa: E402

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def mk_player(cls_id, passives, hp=2000):
    """构造战斗玩家 dict（学指定被动中文名）。"""
    out = {
        "class_name": cls_id, "level": 60, "hp": hp, "max_hp": hp,
        "mp": 100, "max_mp": 200,
        "equipment": {"weapon": {"name": "t", "stats": {"atk": 100, "matk": 100, "spd": 100},
                                 "affixes": [], "enhance": 0}},
        "attributes": {"str": 10, "int": 10},
        "learned_skills": list(passives), "race": "human",
        "resources": {}, "stacks": {}, "buffs": {}, "eff": {},
        "v139_modes": {},
    }
    return out


def mk_enemy(name="测试怪", hp=100000, spd=10):
    return {"name": name, "hp": hp, "max_hp": hp,
            "atk": 50, "def": 20, "mdef": 20, "spd": spd}


def mk_skeleton(name="骷髅", hp=50, kind="summon", tid="skeleton"):
    return {"name": name, "tid": tid, "kind": kind, "hp": hp, "max_hp": hp,
            "side": "player", "buffs": {}}


def mk_battle(player, enemy=None):
    """构造战斗（b.player 与入参同引用——现引擎口径：Battle 持有玩家快照引用）。"""
    b = BT.Battle("monster", enemy or mk_enemy(), {}, player)
    b.player.setdefault("resources", {})
    b.player.setdefault("stacks", {})
    b.player.setdefault("buffs", {})
    b.player.setdefault("v139_modes", {})
    return b


def _snap_state(b):
    """NEW vs OLD 可比状态快照。"""
    r = b.player.setdefault("resources", {})
    s = b.player.setdefault("stacks", {})
    bu = b.player.setdefault("buffs", {})
    return (b.player.get("hp", 0),
            r.get("energy"),
            r.get("faith"),
            s.get("arcane"),
            bu.get("faith_exhausted"))


# ============================================================
# 工具：OLD handler 克隆注册表 + 同调度驱动
# ============================================================
_OLD_REG = {}


def _bind_ref():
    """OLD 副本模块级依赖绑定（E=engine；focus_active 相对导入在 tests 包下失效 → 注入真函数）。"""
    OLD.E = EG
    OLD._BATTLE_WARN = BT._battle_warn
    from data.plugins.dragonfall.game.core import battle_modes as _BM
    OLD._FOCUS_ACTIVE = _BM.focus_active
    # 组装克隆注册表（OLD handler 版）：与 battle.py 顶部注册顺序一致
    from data.plugins.dragonfall.game.core.tick_effects import TICK_HANDLERS as _TH
    _OLD_REG.clear()
    for k in ("set_heal", "set_holy", "rune_regen", "stardust_mana"):
        _OLD_REG[k] = _TH.get(k)
    _OLD_REG["passive_heal"] = OLD.OLD_th_passive_heal
    _OLD_REG["mech_charge"] = OLD.OLD_th_mech_charge
    _OLD_REG["core_regen"] = _TH.get("core_regen")
    _OLD_REG["faith_decay"] = OLD.OLD_th_faith_decay
    _OLD_REG["echo_heal"] = _TH.get("echo_heal")
    _OLD_REG["affix_food_we"] = _TH.get("affix_food_we")


def _old_tick_regen(b, player, logs):
    """OLD 版 _tick_regen 兼容壳：克隆注册表 + battle.py 同款注册顺序。"""
    try:
        if not player:
            return logs
    except Exception:
        return logs
    _log_out = []
    for _kind in ("set_heal", "set_holy", "rune_regen", "stardust_mana",
                  "passive_heal", "mech_charge", "core_regen",
                  "faith_decay", "echo_heal", "affix_food_we"):
        _fn = _OLD_REG.get(_kind)
        if not _fn:
            continue
        try:
            _h_logs, _ = _fn(b, player, {"kind": _kind, "data": {}}, _log_out)
            if _h_logs:
                _log_out += _h_logs
        except Exception:
            continue
    return _log_out


def _run_pair(seg, player, setup=None, enemy=None):
    """同玩家两份深拷贝 → OLD 克隆注册表 _tick_regen vs NEW 现引擎 _tick_regen。

    返回 (一致?, OLD态, NEW态, OLDlogs, NEWlogs)。除目标 handler 实现外调度路径一致
    （克隆注册表保留全部非目标 handler 为现引擎原版——NEW/OLD 两侧同族非 52 分支
    同实现，差分收敛到 4 个目标 proc 分支本体）。
    """
    p_o = copy.deepcopy(player)
    p_n = copy.deepcopy(player)
    b_o = mk_battle(p_o, None if enemy is None else copy.deepcopy(enemy))
    b_n = mk_battle(p_n, None if enemy is None else copy.deepcopy(enemy))
    if setup:
        setup(b_o)
        setup(b_n)
    old_logs = _old_tick_regen(b_o, b_o.player, [])
    old_st = _snap_state(b_o)
    new_logs = b_n._tick_regen(b_n.player, [])
    new_st = _snap_state(b_n)
    key = {"focus": "森之共鸣", "arcane": "奥术直觉",
           "undead": "亡灵祭仪", "faith_overload": "信念·圣化"}[seg]
    new_rel = [str(l) for l in new_logs if key in str(l) or "过载" in str(l)]
    old_rel = [str(l) for l in old_logs if key in str(l) or "过载" in str(l)]
    same = (old_st == new_st) and (sorted(old_rel) == sorted(new_rel))
    return same, old_st, new_st, old_rel, new_rel


# ============================================================
# 1. focus_regen_summon（森之共鸣 → tick_regen 族）
# ============================================================
def test_focus_regen_summon():
    print("\n== 1. focus_regen_summon（森之共鸣 → tick_regen 族）OLD vs NEW ==")
    for learned in (False, True):
        for comps_kind in ("summon", "pet", "none"):
            for energy in (0, 95, None):
                def setup(b, comps_kind=comps_kind, energy=energy):
                    if comps_kind == "summon":
                        b.companions = [mk_skeleton("骷髅")]
                    elif comps_kind == "pet":
                        b.companions = [mk_skeleton("宠物", kind="pet", tid="pet_x")]
                    if energy is not None:
                        b.player["resources"]["energy"] = energy
                same, st_o, st_n, lo, ln = _run_pair(
                    "focus", mk_player("cls_you_xia", ["森之共鸣"] if learned else []), setup)
                tag = f"学={learned} {comps_kind} energy={energy}"
                check(f"{tag}: 状态/logs 一致", same, f"OLD{st_o} NEW{st_n}\n OLDlogs={lo}\n NEWlogs={ln}")
    # 数值特写：同玩家 summon vs 无 summon 的 energy 差 = +5（两路一致；自然回能两侧同有）
    for eng in (50, 0):
        p_a = mk_player("cls_you_xia", ["森之共鸣"])
        p_b = mk_player("cls_you_xia", ["森之共鸣"])
        ba = mk_battle(p_a); bb = mk_battle(p_b)
        ba.player["resources"]["energy"] = eng; bb.player["resources"]["energy"] = eng
        ba.companions = [mk_skeleton("骷髅")]
        la = ba._tick_regen(ba.player, [])
        lb = bb._tick_regen(bb.player, [])
        check(f"energy {eng}：召唤在场比无召唤多回 +5（NEW 口径）",
              ba.player["resources"]["energy"] - bb.player["resources"]["energy"] == 5
              and any("森之共鸣" in str(x) for x in la)
              and not any("森之共鸣" in str(x) for x in lb),
              f"{ba.player['resources']} vs {bb.player['resources']}")


# ============================================================
# 2. arcane_intuition（奥术直觉 → tick_mech_charge 族）
# ============================================================
def test_arcane_intuition():
    print("\n== 2. arcane_intuition（奥术直觉 → tick_mech_charge 族）OLD vs NEW ==")
    for learned in (False, True):
        for arcane in (0, 4, 5):
            for focus in (False, True):
                def setup(b, arcane=arcane, focus=focus):
                    if arcane is not None:
                        b.player["stacks"]["arcane"] = arcane
                    if focus:
                        b.player.setdefault("v139_modes", {})["focus"] = {"active": True, "turns": 3}
                same, st_o, st_n, lo, ln = _run_pair(
                    "arcane", mk_player("cls_fa_shi", ["奥术直觉"] if learned else []), setup)
                tag = f"学={learned} arcane={arcane} focus={focus}"
                check(f"{tag}: 状态/logs 一致", same, f"OLD{st_o} NEW{st_n}\n OLDlogs={lo}\n NEWlogs={ln}")
                if learned and arcane is not None and arcane < 5:
                    exp = min(5, arcane + (2 if focus else 1))
                    check(f"  {tag}: arcane {arcane}→{exp}", st_n[3] == exp and st_o[3] == exp, f"{st_o} {st_n}")
    # 封顶：arcane=5 满 → 仍 5 无日志（new>old 判定）
    p = mk_player("cls_fa_shi", ["奥术直觉"])
    b = mk_battle(p)
    b.player["stacks"]["arcane"] = 5
    logs = b._tick_regen(b.player, [])
    check("arcane 满 5：不超上限无 +1 日志", b.player["stacks"]["arcane"] == 5
          and not any("奥术直觉" in str(l) for l in logs), f"{logs}")


# ============================================================
# 3. undead_faith（亡灵祭仪 → tick_faith 族）先产后衰顺序链
# ============================================================
def test_undead_faith():
    print("\n== 3. undead_faith（亡灵祭仪 → tick_faith 族）OLD vs NEW ==")
    for learned in (False, True):
        for n_skel in (0, 1, 2):
            for undead_enemy in (False, True):
                for faith in (0.5, 5.0, 9.5):
                    for exh in (None, 1):
                        def setup(b, n_skel=n_skel, undead_enemy=undead_enemy, faith=faith, exh=exh):
                            b.player["resources"]["faith"] = float(faith)
                            if n_skel:
                                b.companions = [mk_skeleton(f"骷髅{i}") for i in range(n_skel)]
                            if undead_enemy:
                                b.enemy["name"] = "亡灵法师"
                            if exh is not None:
                                b.player["buffs"]["faith_exhausted"] = exh
                        same, st_o, st_n, lo, ln = _run_pair(
                            "undead", mk_player("cls_mu_shi", ["亡灵祭仪"] if learned else []), setup)
                        tag = f"学={learned} 骷髅{n_skel} 亡灵敌={undead_enemy} faith={faith} exh={exh}"
                        check(f"{tag}: 状态/logs 一致", same,
                              f"OLD{st_o} NEW{st_n}\n OLDlogs={lo}\n NEWlogs={ln}")


# ============================================================
# 4. faith_overload_heal（信念·圣化 → tick_faith 族）
# ============================================================
def test_faith_overload_heal():
    print("\n== 4. faith_overload_heal（信念·圣化 → tick_faith 族）OLD vs NEW ==")
    for learned in (False, True):
        for faith in (10.0, 12.0):
            for hp_frac in (0.5, 1.0):
                def setup(b, faith=faith, hp_frac=hp_frac):
                    b.player["resources"]["faith"] = float(faith)
                    b.player["hp"] = int(b.player.get("max_hp", 2000) * hp_frac)
                same, st_o, st_n, lo, ln = _run_pair(
                    "faith_overload", mk_player("cls_mu_shi", ["信念·圣化"] if learned else []), setup)
                tag = f"学={learned} faith={faith} hp={hp_frac}"
                check(f"{tag}: 状态/logs 一致", same, f"OLD{st_o} NEW{st_n}\n OLDlogs={lo}\n NEWlogs={ln}")
                if learned:
                    check(f"  {tag}: 免力竭（无 faith_exhausted）", st_n[4] is None and st_o[4] is None, f"{st_o} {st_n}")
                else:
                    check(f"  {tag}: 力竭倒计时 5（6 置位后同刻 -1）", st_n[4] == 5 and st_o[4] == 5, f"{st_o} {st_n}")
    # 特写：圣化 30% 乘算 + 回血（学 vs 不学同 hp 起点回血量差 = 30%）
    p1 = mk_player("cls_mu_shi", ["信念·圣化"])
    p2 = mk_player("cls_mu_shi", [])
    b1 = mk_battle(p1)
    b2 = mk_battle(p2)
    mx1 = int(b1.player["max_hp"]); mx2 = int(b2.player["max_hp"])
    b1.player["resources"]["faith"] = 10.0; b2.player["resources"]["faith"] = 10.0
    b1.player["hp"] = int(mx1 * 0.5); b2.player["hp"] = int(mx2 * 0.5)
    b1._tick_regen(b1.player, []); b2._tick_regen(b2.player, [])
    check("圣化回血 > 无圣化回血（heal_up 30% 乘算）",
          b1.player["hp"] > b2.player["hp"], f"{b1.player['hp']} vs {b2.player['hp']}")


# ============================================================
# 5. 通道开关名单（_regen_needed/_ensure_regen_effects）不动
# ============================================================
def test_channel_list_untouched():
    print("\n== 5. 名单通道（卡片存在性检查）原样保留 ==")
    battle = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "battle.py"),
                  encoding="utf-8").read()
    for pk in ("turn_heal", "team_regen", "arcane_regen", "arcane_intuition",
               "focus_regen_summon", "undead_faith", "faith_overload_heal"):
        check(f"_regen_needed 名单含 {pk}", f'"{pk}"' in battle)
    # 挂卡/收卡语义（_ensure_regen_effects）：passive_heal ← 三被动；mech_charge ← 充能被动
    check("passive_heal 卡挂载名单保留（focus_regen_summon 在）",
          '_pm.get("turn_heal") or _pm.get("team_regen") or _pm.get("focus_regen_summon")' in battle)
    check("mech_charge 卡挂载名单保留（arcane_intuition 在）",
          '_pm.get("arcane_regen") or _pm.get("arcane_intuition")' in battle)
    check("tick 注册表 passive_heal/mech_charge/faith_decay 保留",
          all(f'("{k}", _th_{fn})' in battle for k, fn in
              (("passive_heal", "passive_heal"), ("mech_charge", "mech_charge"),
               ("faith_decay", "faith_decay"))))


# ============================================================
# 6. 静态：注册表族/声明 + 残留清零
# ============================================================
def test_static():
    print("\n== 6. 静态：P2-D6 4 proc 声明 + handler 残留清零 ==")
    for proc, fam in (("focus_regen_summon", "tick_regen"),
                      ("arcane_intuition", "tick_mech_charge"),
                      ("undead_faith", "tick_faith"),
                      ("faith_overload_heal", "tick_faith")):
        check(f"{proc} → {fam}", PP.PROC_FAMILIES.get(proc) == fam,
              f"got {PP.PROC_FAMILIES.get(proc)}")
    for fam in ("tick_regen", "tick_mech_charge", "tick_faith"):
        check(f"族执行器 {fam} 已注册", fam in PP.FAMILY_HANDLERS, fam)
    check("KNOWN_GAPS 移除 4 个 E 类成员",
          not ({"focus_regen_summon", "arcane_intuition", "undead_faith",
                "faith_overload_heal"} & PP.KNOWN_GAPS), str(PP.KNOWN_GAPS))
    battle = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "battle.py"),
                  encoding="utf-8").read()
    # 挂点区 = 三个 handler 定义体（_th_passive_heal/_th_mech_charge/_th_faith_decay）
    seg_start = battle.find("def _th_passive_heal")
    seg_end = battle.find("def _th_echo_heal")
    seg = battle[seg_start:seg_end]
    # 旧值读/内联计算残留清零（枚举骨架 .get(proc, []) 是迁移后 sanctioned 挂点模式——
    # 与 D4b 挂点12 保留 `proc"].get("death_contract", [])` 枚举同款，不在残留清单）
    old_reads = [s for s in ('_ps.get("gain", 5)', "_ps.get(\\\"gain\\\", 5)",
                             '_ps.get("per_undead", 0.15)', "_ps.get(\\\"per_undead\\\", 0.15)",
                             '_ps_fh.get("heal_up", 0.30)', "_ps_fh.get(\\\"heal_up\\\", 0.30)",
                             "_fa169(actor)", "_sr_gain", "_mech2", "_uf_gain = float(",
                             "_foheal = True")
                 if s in seg]
    check("挂点区无 4 proc 旧值读/内联计算残留", not old_reads, str(old_reads))
    # 枚举骨架（sanctioned：run_proc_family 逐条分发，max=1 下与原 break 等价）原样保留
    check("4 proc 枚举骨架保留（run_proc_family 分发用）",
          '_pm.get("focus_regen_summon", [])' in seg
          and '_pm["proc"].get("arcane_intuition", [])' in seg
          and 'battle._passive_map(actor)["proc"].get("undead_faith", [])' in seg
          and 'battle._proc_pm(actor)["proc"].get("faith_overload_heal", [])' in seg)
    # 非 52 同族（turn_heal/team_regen/arcane_regen）原样留在 handler
    check("非 52 同族留在 handler（turn_heal/team_regen/arcane_regen）",
          '_pm.get("turn_heal")' in seg and '_pm.get("team_regen")' in seg
          and '_pm["proc"].get("arcane_regen", [])' in seg)
    check("stat 通道 spellblade_regen 留在 handler", '"spellblade_regen"' in seg)


def main():
    clean_db()
    _bind_ref()
    test_focus_regen_summon()
    test_arcane_intuition()
    test_undead_faith()
    test_faith_overload_heal()
    test_channel_list_untouched()
    test_static()
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
