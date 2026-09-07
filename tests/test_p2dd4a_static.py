# -*- coding: utf-8 -*-
"""v181.P2D-D4a 静态等价佐证（test_p2dd4a_static.py）

本文件不跑引擎：断言 battle.py 挂点10 player_turn 免控段 + 挂点11 _mitigate_chain
条件减伤聚合段的 6 proc 迁移痕迹（P2-D4a 收），并确认：
- 挂点12 _post_hp_lethal 致死复活族（death_contract/berserk_revive/stance_immortal，
  D4b 收）未被误碰
- 首触发生产段（不动如山补磐核 3236/10569 区）与序列化键未被误碰
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BATTLE = os.path.join(HERE, "..", "game", "battle.py")
PROCS = os.path.join(HERE, "..", "game", "core", "passive_procs.py")

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def main():
    battle = open(BATTLE, encoding="utf-8").read()
    procs = open(PROCS, encoding="utf-8").read()
    print("== P2D-D4a 静态等价佐证（挂点10/11 改造痕迹 + 注册表 + 挂点12 未碰）==")
    # 注册表：6 proc 声明 + 2 族执行器
    for proc, fam in (("tenacity", "cc_break_cost"),
                      ("zhan_yi_full_reduce", "dr_cond"),
                      ("core_full", "dr_cond"),
                      ("core_reduce", "dr_cond"),
                      ("core_last_stand", "dr_cond"),
                      ("core_overflow", "dr_cond")):
        check(f"declare_proc {proc} → {fam}", f'declare_proc("{proc}", "{fam}")' in procs)
    check("cc_break_cost 执行器注册", '@register("cc_break_cost")' in procs)
    check("dr_cond 执行器注册", '@register("dr_cond")' in procs)
    # 挂点10：tenacity 骨架查表 + 双免控分派
    check("_tenacity_try_break 内调 run_proc_family tenacity",
          '_run_proc_family(self, "tenacity"' in battle)
    check("挂点10 stun_clear 免眩晕", '"cc_kind": "stun_clear"' in battle)
    check("挂点10 cc_window 免控窗口", '"cc_kind": "cc_window"' in battle)
    # 挂点11：5 段 dr_kind 分派
    for dk in ("zy_full", "core_full", "per_core", "last_stand", "overflow_shield"):
        check(f"挂点11 dr_kind={dk}", f'"dr_kind": "{dk}"' in battle)
    # 旧直读残留清零（挂点10/11 消费区不再 _ps.get 兜底读 stacks/reduce/per_core/shield_pct/cost）
    seg = battle.split("# ---- v169.7 条件减伤被动族（磐核/战意 持有档位） ----")[1]
    seg = seg.split("if reduce_total:")[0]
    old = re.findall(r'_ps\d*\.get\("(?:stacks|reduce|per_core|shield_pct|turns)"', seg)
    check("挂点11 聚合段无旧直读残留", not old, str(old))
    # 挂点10 免控区（3275-3300）：旧直读清零（stacks 兜底只在注册表，不在 battle 免控段）
    pt = battle.split("def player_turn")[1]
    pt = pt.split("def _player_charge_release")[0] if "def _player_charge_release" in pt else pt[:6000]
    old_cc = re.findall(r'_ps_(?:zy|cf)\.get\("stacks"', pt)
    check("挂点10 免控区无旧直读残留", not old_cc, str(old_cc))
    # 一次性 flag 序列化键保留
    check("to_state tenacity_left/core_last_stand_used 保留",
          '"tenacity_left": getattr' in battle and '"core_last_stand_used": getattr' in battle)
    check("from_state 恢复键保留",
          'b._tenacity_left_n = int(st.get("tenacity_left"' in battle
          and 'b._core_last_stand_used = bool(st.get("core_last_stand_used"' in battle)
    # 首触发生产段保留（挂点10 区 3236 + 挂点11 区 10569——未置位且 hp<ratio → 补磐核+置位）
    check("首触发生产段保留 2 处",
          battle.count('if not getattr(self, "_core_last_stand_used", False):') >= 2)
    check("生产段 RES 补核 + 日志串保留",
          '_p_res()["guard_core"] = max(self._guard_core_n()' in battle
          and "绝境不屈，获得" in battle)
    # 挂点12 _post_hp_lethal 致死复活族（D4b 收）未碰——三个 revive proc 消费点原样
    hp12 = battle.split("def _post_hp_lethal")[1] if "def _post_hp_lethal" in battle else ""
    if hp12:
        for nm in ("death_contract", "berserk_revive", "stance_immortal"):
            check(f"挂点12 {nm} 未迁（保留旧 for 消费）",
                  f'get("{nm}", []' in hp12 and f'run_proc_family(self, "{nm}"' not in hp12)
    check("挂点12 区存在（_post_hp_lethal 方法未删）", bool(hp12))
    # 其余 D4b 挂点12 声明未提前（passive_procs 无这 3 proc 声明）
    for nm in ("death_contract", "berserk_revive", "stance_immortal"):
        check(f"注册表未提前声明 {nm}", f'declare_proc("{nm}"' not in procs)
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
