# -*- coding: utf-8 -*-
"""被动 proc 注册表全覆盖门禁（防「新增被动忘注册 → 静默空转」）。

背景（2026-09-11）：`game/core/passive_procs.py` 文件尾在 import 期就执行
`validate_proc_coverage()`（校验失败 → ImportError = 启动即红）。但**引用它的测试
全部在 `tests/_retired_old_engine/`（已退役，run_all 不跑）** → 门禁实际没人执行，
P15 新增的 `reflect_bar` 未登记也一路过关（全量 249 绿、门禁却红）。
本测试把这道启动校验纳入回归，让缺口当场暴露。

三件事：
  1. import 即校验：`validate_proc_coverage()` 不抛（等价「启动即红」那道门）
  2. 52 全覆盖口径：unaccounted 空（声明集 ⊆ 族 ∪ 缺口）/ extra 空（族 ⊄ 白名单）/
     dup 空（族 ∩ 缺口 = ∅）
  3. 白名单规模断言：skills.py 声明的 proc 数不掉（防数据被悄悄删）+ 已知缺口集合钉死
     （缺口减少 = 有人实装了 → 该来更新本测试并移除登记）

跑法：python tests/test_passive_proc_coverage.py
"""
import os
import sys

_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_PLUGIN_DIR)))
sys.path.insert(0, _QQBOT_DIR)
sys.path.insert(0, _PLUGIN_DIR)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = 0
FAIL = 0
FAILURES = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        FAILURES.append(f"{name} {detail}")
        print(f"  ❌ {name} {detail}")


# 已知缺口快照（2026-09-11）。⚠️ 此处**故意写死**：缺口减少 = 有人实装了某 proc，
# 那就该同步更新本集合（正向变化要人确认，防「悄悄从缺口表里删掉却没实装」）。
EXPECTED_GAPS = {
    # D 类真空转
    "faith_share", "finisher_up", "poison_burst_up", "poison_spread",
    # 引擎旧通道直读（挂点 7/8/9，已消费未注册表化）
    "arcane_constant", "lian_duan_soft", "shadow_dance_ease",  # ease = 原 shadow_dance_cd 改名（2026-09-11 改词裁定）
    # P15 走新装配路径（PASSIVE_PROC 表 + class_mech_proc）
    "reflect_bar",
}


def main():
    print("【被动 proc 注册表：启动校验门禁】")
    try:
        import game.content as _C                        # noqa: F401  先触发数据装配
        from game.core import passive_procs as PP       # import 期即跑校验
    except ImportError as e:
        check("import passive_procs（含启动全覆盖校验）", False, f"ImportError: {e}")
        print(f"\n{'-' * 46}\n通过 {PASS} / 失败 {FAIL}")
        return 1
    check("import passive_procs（含启动全覆盖校验）", True)

    print("【52 全覆盖口径】")
    rep = PP.validate_proc_coverage()
    check("validate_proc_coverage() 可调用（import 期未抛）", True)
    wl = sorted(getattr(PP, "_ALL_PASSIVE_PROCS", None) or [])
    fam = sorted(PP.PROC_FAMILIES)
    gaps = sorted(PP.KNOWN_GAPS)
    check(f"声明集全部有归属（unaccounted 0，白名单 {len(wl)} 条）",
          rep["unaccounted"] == 0, f"未收编未登记 {rep['unaccounted']} 条")
    check("族声明 ⊆ 白名单（extra 0：无凭空声明的族）",
          rep["extra_decl"] == 0, f"extra={rep['extra_decl']}")
    check("族 ∩ 缺口 = ∅（同一 proc 不能既实装又登记缺口）",
          not (set(fam) & set(gaps)), f"dup={sorted(set(fam) & set(gaps))}")
    check("已声明族均有执行器（_FAMILY_PENDING 空）",
          not getattr(PP, "_FAMILY_PENDING", None),
          f"缺执行器族={sorted(getattr(PP, '_FAMILY_PENDING', None) or [])}")

    print("【规模与缺口集合钉死（防悄悄增删）】")
    check(f"白名单规模 ≥ 52（实际 {len(wl)}）", len(wl) >= 52, f"实际 {len(wl)}")
    check(f"已收编族数 ≥ 45（实际 {len(fam)}）", len(fam) >= 45, f"实际 {len(fam)}")
    missing = EXPECTED_GAPS - set(gaps)
    check("缺口表含全部预期项（减少=有人实装，需同步更新本测试）",
          not missing, f"缺失={sorted(missing)}")
    newgaps = set(gaps) - EXPECTED_GAPS
    check("缺口表无新增未记录项（新增=新通道 proc 忘收编）",
          not newgaps, f"新增={sorted(newgaps)}")

    print(f"\n{'-' * 46}\n通过 {PASS} / 失败 {FAIL}")
    for f in FAILURES:
        print(f"  ❌ {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
