# -*- coding: utf-8 -*-
"""装备加成层扩展测试（v156 数值模型阶段 2：升级 / 幸运宝石 / 套装）。

覆盖：
  1. make_gear 无 upgrade 乘区：升级是真等级化（lv 提升经 equip_stats 重算），
     make_gear upgrade 参数语义改为"装备 lv = level + upgrade"（模拟真等级化养成）
  2. make_gear gem_tier 生效：面板属性增加（sockets 原石走引擎原石段）
  3. gear_loadout 新档位字段：team_max_full 返回 upgrade/gem_tier/set_bonus
  4. AFFIX_CLASS_LINES 按职业线存在且不重叠（31 条资源联动词条全覆盖）

运行：python tests/test_numeric_gear_full.py（exit=0 全绿；由 run_numeric_tests.py 自动纳入门禁）
"""
import os
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))          # tests/
_PLUGIN_DIR = os.path.dirname(_SCRIPT_DIR)                        # dragonfall/
_SCRIPTS_DIR = os.path.join(_PLUGIN_DIR, "scripts")
for _p in (_SCRIPTS_DIR, _PLUGIN_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PLUGIN_DIR, "tests", "test_game_data.db"))

from numeric_lib.env import setup_env  # noqa: E402,F401
from numeric_lib.gear import make_gear, gear_loadout  # noqa: E402
from numeric_lib.constants import AFFIX_CLASS_LINES, AFFIX_LINE_WEIGHT, LOADOUTS  # noqa: E402
from data.plugins.dragonfall.game import content as C  # noqa: E402
from data.plugins.dragonfall.game import engine as E  # noqa: E402

passed, failed = 0, 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}  {detail}")


def panel_atk(gear: dict, cls: str = "cls_zhan_shi", lv: int = 30) -> float:
    """真实引擎面板 atk（无属性点、无转职，纯装备差）。"""
    return E.player_final_stats(cls, lv, gear, 0, {})["atk"]


def panel_matk(gear: dict, cls: str = "cls_fa_shi", lv: int = 30) -> float:
    """真实引擎面板 matk（无属性点、无转职，纯装备差；原石 stat 随机取 atk/matk/def）。"""
    return E.player_final_stats(cls, lv, gear, 0, {})["matk"]
def main():
    print("【1/4 真等级化生效：make_gear upgrade=lv+10 面板 > upgrade=0】")
    g0 = make_gear(30, "blue", 0, upgrade=0)
    g10 = make_gear(30, "blue", 0, upgrade=10)
    base = panel_atk({}, "cls_zhan_shi", 30)   # 基础 atk（无装备）
    a0, a10 = panel_atk(g0), panel_atk(g10)
    check("真等级化 upgrade=10(装备lv40) 面板 atk > upgrade=0(装备lv30)",
          a10 > a0, f"up={a0} up10={a10}")
    # 纯装备差口径（去掉基础 atk）：升级 = 真 lv 提升 → 面板随 equip_stats 公式自然增长
    g_only0, g_only10 = a0 - base, a10 - base
    check("真等级化 upgrade=10 装备差 > upgrade=0 装备差（lv 30→40 属性自然增长）",
          g_only10 > g_only0, f"d0={g_only0} d10={g_only10}")
    w10 = g10["weapon"]
    check("gear 条目带 upgrade 字段", w10.get("upgrade") == 10, f"got={w10.get('upgrade')}")

    print("【2/4 幸运宝石生效：gem_tier=10 面板 > gem_tier=0】")
    gg0 = make_gear(30, "orange", 0, gem_tier=0)
    gg6 = make_gear(30, "orange", 0, gem_tier=6)
    gg10 = make_gear(30, "orange", 0, gem_tier=10)
    # 原石 stat 随机取 atk/matk/def：用 panel_matk 验证（战士 atk 侧可能随到 matk）
    b0, b6, b10 = panel_matk(gg0), panel_matk(gg6), panel_matk(gg10)
    check("gem_tier=6 面板 matk > gem_tier=0（单孔原石加成生效）", b6 > b0,
          f"t0={b0} t6={b6}")
    check("gem_tier=10 面板 matk > gem_tier=6（高阶宝石更强）", b10 > b6,
          f"t6={b6} t10={b10}")
    sock = gg10["weapon"].get("sockets")
    check("gear 条目带 sockets（引擎原石段消费）", bool(sock) and "S1" in sock,
          f"got={sock}")

    print("【3/4 gear_loadout 新档位字段】")
    lv = 30
    for name, key in [("solo_mid_upgrade", "upgrade"),
                      ("team_max_full", "upgrade"),
                      ("team_max_full", "gem_tier"),
                      ("team_max_full", "set_bonus")]:
        cfg = LOADOUTS[name]
        g = gear_loadout(lv, name)
        check(f"{name} 配置含 {key}", key in cfg, f"cfg={cfg}")
        if g:
            any_item = next(iter(g.values()))
            check(f"{name} gear 条目含 {key} 字段", key in any_item,
                  f"got keys={sorted(any_item.keys())}")
            if key == "set_bonus":
                check(f"{name} 套装已激活（2 件同套 → 面板 atk 更高）",
                      panel_atk(g) > panel_atk(gear_loadout(lv, "team_orange9")),
                      f"set={panel_atk(g)} no_set={panel_atk(gear_loadout(lv, 'team_orange9'))}")
    g_full = gear_loadout(lv, "team_max_full")
    check("team_max_full 全槽位", len(g_full) == len(C.EQUIP_SLOT_BASE),
          f"n={len(g_full)}")
    check("team_max_full upgrade=10 且 gem_tier=6 且 set_bonus=True",
          all(it.get("upgrade") == 10 and it.get("gem_tier") == 6 and it.get("set_bonus")
              for it in g_full.values()),
          str({s: (it.get("upgrade"), it.get("gem_tier"), it.get("set_bonus"))
               for s, it in g_full.items()}))

    print("【4/4 AFFIX_CLASS_LINES 按职业线存在且不重叠】")
    check("六职业线均在 AFFIX_CLASS_LINES",
          set(AFFIX_CLASS_LINES) == {"战士", "法师", "游侠", "牧师", "刺客", "拳师"},
          f"got={sorted(AFFIX_CLASS_LINES)}")
    all_names = []
    for cls, names in AFFIX_CLASS_LINES.items():
        check(f"{cls} 分系非空", len(names) > 0, f"names={names}")
        all_names.extend(names)
    dup = {n for n in all_names if all_names.count(n) > 1}
    check("分系词条不重叠（无跨职业重复）", not dup, f"dup={dup}")
    # 与权威数据 affixes.py 校验：所有分系词条名都存在（31 条资源联动词条）
    affix_names = {v.get("name") for v in C.AFFIXES.values()}
    missing = [n for n in all_names if n not in affix_names]
    check("分系词条全部存在于 affixes.py 权威数据", not missing, f"missing={missing}")
    check("分系词条总数 = 31（v130.2 资源联动词条）", len(all_names) == 31,
          f"n={len(all_names)}")
    check("AFFIX_LINE_WEIGHT 六职业权重 0.6",
          all(abs(AFFIX_LINE_WEIGHT[c] - 0.6) < 1e-9 for c in AFFIX_CLASS_LINES),
          str(AFFIX_LINE_WEIGHT))

    print(f"\n===== 结果：通过 {passed} / 断言 {passed + failed} =====")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
