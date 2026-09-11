# -*- coding: utf-8 -*-
"""v181.P2D-D3a 静态等价佐证（test_p2dd3a_static.py）

本文件不跑引擎：断言 battle.py 挂点6 _skill_passive_dmg_bonus 的三段改造痕迹
（D3a 只动 arcane_resonance / element_origin / element_sync 3 proc），并确认：
- 挂点14 _deal_damage 的 5 段（hunt_mark_up/soul_mark_cap/shaken_awareness/
  broken_extend/dirge_debuff_dmg，D3b 收）未被误碰
- 其余 52 proc 挂点未被误碰
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
    print("== P2D-D3a 静态等价佐证（battle.py 挂点6 三段改造痕迹 + 注册表 + 挂点14 未碰）==")
    # 挂点6：3 段经注册表消费
    check("挂点6 arcane_resonance 段调 dmg_mult_cond",
          'mult_kind": "arcane_mech"' in battle)
    check("挂点6 element_origin 段调 dmg_mult_cond",
          'mult_kind": "element_marks"' in battle)
    check("挂点6 element_sync 段调 flag_set_cond",
          'flag_kind": "elem_sync"' in battle)
    # 旧直读残留：挂点6 3 proc 消费区（v169.7 奥术共鸣 → 连招技能伤害 前）不再直读 _ps
    d3a_region = battle.split("# v169.7 奥术共鸣 arcane_resonance：奥术技能伤害")[1]
    d3a_region = d3a_region.split("# 连招技能伤害（武技）")[0]
    old_reads = re.findall(r'_ps\.get\("(?:mult|layers)"', d3a_region)
    check("挂点6 无 3 proc 旧直读残留（mult/layers）", not old_reads, str(old_reads))
    check("挂点6 无 3 proc 旧 `passive_bonus *= (1 + float` 残留",
          "passive_bonus *= (1 + float(_ps.get(\"mult\", 0.0) or 0.0))" not in d3a_region)
    # 挂点14 _deal_damage（D3b 收）已迁移：5 段走 run_proc_family（mult_kind 分派）
    check("挂点14 5 proc 段消费注册表 mult_kind",
          all(f'mult_kind": "{mk}"' in battle
              for mk in ("hunt_mark", "soul_mark", "shaken_bar",
                         "broken_break", "dirge_debuffs")))
    check("挂点14 5 proc 有 run_proc_family 消费",
          battle.count('_run_proc_family(self, "hunt_mark_up"') > 0
          and battle.count('_run_proc_family(self, "dirge_debuff_dmg"') > 0)
    # 注册表
    check("passive_procs 声明 3 proc",
          all(f'declare_proc("{p}", "{f}")' in procs
              for p, f in (("arcane_resonance", "dmg_mult_cond"),
                           ("element_origin", "dmg_mult_cond"),
                           ("element_sync", "flag_set_cond"))))
    check("flag_set_cond 执行器注册", '@register("flag_set_cond")' in procs)
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
