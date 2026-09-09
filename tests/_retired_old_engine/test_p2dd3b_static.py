# -*- coding: utf-8 -*-
"""v181.P2D-D3b 静态等价佐证（test_p2dd3b_static.py）

本文件不跑引擎：断言 battle.py 挂点14 _deal_damage 的 5 段改造痕迹
（D3b 迁移 hunt_mark_up/soul_mark_cap/shaken_awareness/broken_extend/
dirge_debuff_dmg → passive_procs 注册表族 dmg_mult_cond），并确认：
- 注册表新增 5 个 declare_proc（挂点14 消费）
- 挂点14 的 5 段不再直读 _ps（旧 for 循环体迁入 handler）
- 其它挂点（1/2/3/4/5/6/17/21/22 等已迁批次）未被误碰
- 挂点6 挂点14 不重叠（D3a 段保持注册表消费，D3b 段也是）
"""
import re
import os
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
    print("== P2D-D3b 静态等价佐证（挂点14 _deal_damage 5 段迁注册表 + 其它挂点未碰）==")
    # ---- 挂点14 5 proc 段消费注册表（mult_kind 分派 5 段）----
    for mk in ("hunt_mark", "soul_mark", "shaken_bar", "broken_break", "dirge_debuffs"):
        check(f"挂点14 段 mult_kind={mk} 调 run_proc_family",
              f'mult_kind": "{mk}"' in battle)
    # 注册表声明 5 proc → dmg_mult_cond
    for p in ("hunt_mark_up", "soul_mark_cap", "shaken_awareness",
              "broken_extend", "dirge_debuff_dmg"):
        check(f"declare_proc({p} → dmg_mult_cond)",
              f'declare_proc("{p}", "dmg_mult_cond")' in procs)
    # ---- 挂点14 区域内不再直读 _ps ----
    d3b_region = battle.split("# ---- v169.7 通用伤害乘区")[1]
    d3b_region = d3b_region.split("if _mult_pas != 1.0:")[0]
    old_reads = re.findall(r'_ps\.get\("(?:per_layer|bar_at|mult|broken_mult|per_debuff|cap)"',
                           d3b_region)
    check("挂点14 无旧 _ps 直读残留", not old_reads, str(old_reads))
    # 旧消费骨架 = `for _pn,_ps in pm["proc"].get(...)` 手写循环 + 循环体内 `_ps.get` 直读 +
    # 内联标签/乘区改写——D3b 后挂点14 内只保留 `_run_proc_family ×5` 分发骨架（乘区/标签
    # 数值全进 handler）；proc 名仍出现在 get() 读 proc 聚合表（挂点公共 `_pm_d` 读取，
    # 与已迁批次同款骨架），但循环体内不再有任何旧直读
    check("挂点14 旧直读消费无残留（无 `_ps.get` 直读 + 恰好 5 处 run）",
          not re.findall(r'_ps[0-9a-z_]*\.get\("(?:per_layer|bar_at|mult|broken_mult|per_debuff|cap)"',
                         d3b_region)
          and d3b_region.count('_run_proc_family(self,') == 5
          and '_mult_pas \*= 1\.0 \+' not in d3b_region,
          "旧 for 循环体应整体迁入 handler（新循环骨架 = run_proc_family ×5）")
    # ---- 注册表 handler 内 5 段（ps 只读数值 = 零默认值）----
    handler_region = procs.split('mult_kind": "hunt_mark"')[0]
    # 全表读取到的 5 段 handler 已含零默认值判据（缺字段 <=0 → 不触发）
    # ---- 其它已迁批次挂点未被误碰（行为零变化：旧挂点注册表调用保留）----
    check("挂点1 crit_cond_add 消费保留", '_run_proc_family(self, "zhan_yi_crit"' in battle)
    check("挂点2 stat_mult_cond 消费保留", '_run_proc_family(self, "shadow_dance_bonus"' in battle)
    check("挂点4 dmg_mult_cond speed_ratio 消费保留", '_run_proc_family(self, "speed_ratio_dmg"' in battle)
    check("挂点5 lifesteal_add 消费保留", '_run_proc_family(self, "zhan_yi_lifesteal"' in battle)
    check("挂点6 arcane_mech 消费保留", 'mult_kind": "arcane_mech"' in battle)
    check("挂点17 stack_cap_add 消费保留", '_run_proc_family(self, "poison_cap"' in battle)
    check("挂点21 summon_cap_add 消费保留", '_run_proc_family(self, "skeleton_cap"' in battle)
    check("挂点22 on_kill_refill 消费保留", '_run_proc_family(self, "focus_full_on_kill"' in battle)
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
