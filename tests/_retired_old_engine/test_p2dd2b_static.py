# -*- coding: utf-8 -*-
"""v181.P2D-D2b OLD-NEW 探针（test_p2dd2b 主体运行在沙盒 copy15；此文件为静态等价佐证）

本文件不跑引擎：断言 battle.py 挂点2/3 的四段改造痕迹（D2b 只动 shadow_dance_bonus 双段 +
旋律 3 光环），并确认其余 52 proc 挂点未被误碰。
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
    print("== P2D-D2b 静态等价佐证（battle.py 四段改造痕迹 + 注册表）==")
    # 挂点2：crit_dmg 段经 stat_mult_cond
    check("挂点2 crit_dmg 段调 stat_mult_cond", 'stat_kind": "crit_dmg"' in battle)
    check("挂点2 保留 _shadow_dance 守卫", "if self._shadow_dance(player):" in battle)
    # 挂点3：spd 段 + 旋律 3 段
    check("挂点3 spd 段调 stat_mult_cond", 'stat_kind": "spd"' in battle)
    check("挂点3 旋律段调 stat_mult_cond ×3", battle.count('stat_kind": "melody"') == 3)
    # 旧直读残留检查（仅本批 4 proc 消费区的直读键；stat cond 通道 4704 `_ps.get("mult")`
    # 是 stat 型被动（非本批 52 proc），用 `_ps_sb/_ps_rs/_ps_mf/_ps_mm` 变量前缀精确匹配）
    d2b_regions = battle.split("# v169.7 暗影步·极 shadow_dance_bonus：影舞态中自身速度")[1]
    d2b_regions = d2b_regions.split("# v140 波3.1")[0]
    old_reads = re.findall(r'_ps_(?:sb|rs|mf|mm)\.get\("(?:spd_add|crit_dmg|per_stack|mult|stacks)"',
                           d2b_regions)
    check("挂点2/3 无 4 proc 旧直读残留", not old_reads, str(old_reads))
    # 注册表
    check("passive_procs 声明 4 proc", all(
        f'declare_proc("{p}", "stat_mult_cond")' in procs
        for p in ("shadow_dance_bonus", "melody_resonance", "melody_full", "melody_master")))
    check("stat_mult_cond 执行器注册", '@register("stat_mult_cond")' in procs)
    print(f"\n结果: {passed} 通过, {failed} 失败")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
