# -*- coding: utf-8 -*-
"""test_numeric_drop_unify —— 掉落系统统一门禁（v174）

防退化断言：
  1. DROP_POOLS 全量 0 断链 / 0 空池（audit_all）
  2. 四策略 roll 冒烟（weighted/fish/table/fixed 各抽得出）
  3. 采集/挖掘/垂钓/副本Boss 消费数据源一致性（老数据↔新池集合相等）
  4. expand_pool 权重展开等价旧逻辑

运行：python tests/test_numeric_drop_unify.py（exit=0 全绿；由 run_numeric_tests.py 自动纳入门禁）
"""
import os
import sys
import random

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PLUGIN_DIR = os.path.dirname(_SCRIPT_DIR)
for _p in (_PLUGIN_DIR,):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("GWEN_GAME_DB", os.path.join(_PLUGIN_DIR, "tests", "test_game_data.db"))

import game.content as C  # noqa: E402
from game.data.drop_pools import DROP_POOLS  # noqa: E402
from game.drop_engine import (  # noqa: E402
    roll, expand_pool, audit_all, _SimpleCtx, _resolve_item_ref,
)

passed, failed = 0, 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def main():
    print("【drop_unify：全量审计 0 断链】")
    rep = audit_all()
    issues = rep["issues"]
    check("DROP_POOLS 审计 0 问题", len(issues) == 0, f"发现 {len(issues)}: {issues[:3]}")
    check("池数 ≥ 500", rep["pool_count"] >= 500, f"实际 {rep['pool_count']}")
    check("条目数 ≥ 1300", rep["entry_count"] >= 1300, f"实际 {rep['entry_count']}")

    print("【drop_unify：四策略 roll 冒烟】")
    # weighted
    r = roll("gather:oak_plain", _SimpleCtx(map_id="oak_plain", player_level=5))
    check("weighted 采集出材料", len(r) >= 1 and r[0]["type"] == "item", f"{r}")
    # fish
    r = roll("fish:oak_plain", _SimpleCtx(map_id="oak_plain", prof_lv=3))
    check("fish 垂钓出鱼", len(r) >= 1 and r[0]["type"] == "fish", f"{r}")
    # table
    r = roll("chest:low", _SimpleCtx(player_level=20))
    check("table 宝箱出金", any(x["type"] == "gold" for x in r), f"{r}")
    # fixed
    r = roll("elite:狼王·灰影", _SimpleCtx(player_level=14))
    check("fixed 精英专属出装", any(x["type"] == "equip" for x in r), f"{r}")

    print("【drop_unify：数据源一致性（老数据 ↔ 新池）】")
    # 采集
    for mapid in ("oak_plain", "white_deer_forest", "hill_mine", "dragon_ridge"):
        old = {m for m, _w in C.GATHER_MAP_POOLS.get(mapid, []) for _ in range(_w)}
        new = set(expand_pool(f"gather:{mapid}"))
        check(f"gather:{mapid} 集合一致", old == new, f"old{len(old)} new{len(new)}")
    # 挖掘深池
    for mapid in ("hill_mine", "dragon_ridge"):
        old = {m for m, _w in C.MINING_DEEP_POOLS.get(mapid, []) for _ in range(_w)}
        new = set(expand_pool(f"mine:{mapid}"))
        check(f"mine:{mapid} 集合一致", old == new, f"old{len(old)} new{len(new)}")
    # 副本Boss 池主题装备
    for iid in ("inst_goblin_camp", "inst_sea_cave", "inst_sea_god_temple", "inst_frost_throne"):
        old_pool = set((C.INSTANCE_BOSS_EQUIP_DROP.get(iid) or {}).get("pool") or [])
        sub_key = f"inst_pool:{iid}"
        new_pool = set()
        if sub_key in DROP_POOLS:
            new_pool = {e["item"].replace("equip:", "") for e in DROP_POOLS[sub_key]["entries"]}
        check(f"boss:{iid} 主题池一致", old_pool == new_pool, f"old{len(old_pool)} new{len(new_pool)}")

    print("【drop_unify：expand_pool 权重展开】")
    # 展开数 = 权重和
    for mapid in ("oak_plain", "emerald_forest"):
        old_w = sum(w for _m, w in C.GATHER_MAP_POOLS.get(mapid, []))
        new_n = len(expand_pool(f"gather:{mapid}"))
        check(f"gather:{mapid} 权重展开数一致", old_w == new_n, f"old{old_w} new{new_n}")

    print("【drop_unify：引用解析】")
    r = _resolve_item_ref("equip:eq_hui_ying_lang_ya_ren", _SimpleCtx(player_level=14))
    check("equip: 引用解析成名册装", r and r["type"] == "equip", f"{r}")
    r = _resolve_item_ref("gold:10:50", _SimpleCtx())
    check("gold: 区间解析", r and r["type"] == "gold" and 10 <= r["count"] <= 50, f"{r}")

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
