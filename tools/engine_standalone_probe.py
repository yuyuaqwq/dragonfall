#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引擎可分发性探针：验证 `framework/battle2/` 能否**脱离奥兰迪亚**独立驱动一场战斗。

用途（S8 拆仓库 / 发给第三方前的门禁）：
  1. 把引擎包物理复制到临时目录（只读原仓库，全程不动任何源文件）
  2. 用一份**最小第三方内容**（自备声明表 + 少量 hook，不 import 奥兰迪亚任何模块）起战斗
  3. 断言：能 import / 能跑 / 产生真实伤害 / 双方都掉血
  4. 输出「拆仓库必改项」= 引擎包内指向 `game.*` 的绝对 import（改相对即可）

历史：2026-09-11 首次运行即发现真 bug —— 未挂 `skill_flat_fn` 时
`formulas.skill_flat_value` 会 `float(None)` **TypeError 崩掉首场战斗**（违背模块自身
docstring 与 plan §8-R8 的「中性兜底不炸」承诺）。已修（`_NEUTRAL_SKELETON`），
并有 `tests/test_engine_neutral_fallback.py` 锁死该契约。

用法：
    python tools/engine_standalone_probe.py            # 跑探测
    python tools/engine_standalone_probe.py --keep     # 保留临时目录（排查用）

退出码：0 = 可独立分发；非 0 = 有阻塞项（stderr 给原因）
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ENGINE = os.path.join(REPO, "framework", "battle2")
PY = sys.executable

# 第三方内容探针：只依赖搬出去的 battle2 + 自己的内容
PROBE_SRC = r'''# -*- coding: utf-8 -*-
"""最小第三方内容提供者（不 import 奥兰迪亚任何东西）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from battle2 import config as CFG, Battle, make_actor
from battle2 import formulas as ENGINE_FORMULAS   # 引擎自带通用公式

# ① 自备声明表
CFG.set_config("effect_rules", {
    "rage": {"name": "怒气", "cap": 10},
    "burn": {"name": "灼烧", "period": {"dir": "damage", "interval": 1.0,
                                        "pct_max_hp": 0.05}},
})
CFG.set_config("effect_actions", {"burn": [{"action": "apply"}]})


# ② 挂最小 hook
def panel_fn(battle, actor):
    """最简面板（真实游戏在这里做装备/等级/职业聚合）。"""
    return dict(actor)


CFG.mount(
    formulas=ENGINE_FORMULAS,
    panel_fn=panel_fn,
    skill_lookup=None,
    monster_skill_fn=lambda key: None,
    basic_skill_fn=lambda cls: None,
    basic_fallback={"name": "攻击", "kind": "物理", "exprs": ["atk*1.2"]},
    kinds={"phys": "物理", "magi": "魔法", "true": "真伤",
           "heal": "治疗", "buff": "增益"},
)

# ③ 起战斗
p = make_actor(uid="p1", name="勇者", side="player", kind="player",
               human_controlled=True, hp=100, max_hp=100, mp=20, max_mp=20,
               atk=30, matk=10, spd=10, crit=0.0, level=1,
               equipment={}, skills=[], learned_skills=[],
               **{"def": 5, "mdef": 5})
e = make_actor(uid="e1", name="史莱姆", side="enemy", kind="monster",
               hp=60, max_hp=60, atk=8, matk=1, spd=5, crit=0.0, level=1,
               **{"def": 2, "mdef": 2})

logs = []
b = Battle(btype="monster", sides={"player": [p], "enemy": [e]})
b.auto_run(logs, max_steps=40)

enemy_taken = 60 - e["hp"]
player_taken = 100 - p["hp"]
print("HP_PLAYER", p["hp"], "HP_ENEMY", e["hp"], "LOGS", len(logs))
print("ENEMY_TAKEN", enemy_taken, "PLAYER_TAKEN", player_taken)
for l in logs[:6]:
    print("  log:", str(l)[:110])
print("VERDICT", "PASS" if (enemy_taken > 0 and player_taken > 0) else
      f"PARTIAL(enemy_taken={enemy_taken}, player_taken={player_taken})")
'''

# 引擎包内指向 game.* 的绝对 import（拆仓库必改）
_ABS_GAME_IMPORT = re.compile(r"^\s*(?:from|import)\s+game(?:\.|\s|$)")


def scan_outside_imports(engine_dir: str) -> list[str]:
    out = []
    for root, _dirs, files in os.walk(engine_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
            fp = os.path.join(root, f)
            for i, line in enumerate(open(fp, encoding="utf-8").read().splitlines(), 1):
                if _ABS_GAME_IMPORT.match(line):
                    out.append(f"{os.path.relpath(fp, engine_dir)}:{i}: {line.strip()}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true", help="保留临时目录")
    args = ap.parse_args()

    if not os.path.isdir(SRC_ENGINE):
        print(f"[err] 找不到引擎目录：{SRC_ENGINE}", file=sys.stderr)
        return 2

    tmp = tempfile.mkdtemp(prefix="engine_standalone_")
    pkg = os.path.join(tmp, "enginepkg")
    os.makedirs(pkg)
    try:
        shutil.copytree(SRC_ENGINE, os.path.join(pkg, "battle2"),
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        n = sum(len(fs) for _, _, fs in os.walk(os.path.join(pkg, "battle2")))
        print(f"[1] 复制引擎包：{n} 个文件")

        open(os.path.join(pkg, "probe.py"), "w", encoding="utf-8").write(PROBE_SRC)

        env = dict(os.environ, PYTHONIOENCODING="utf-8", GWEN_TEST_MODE="1")
        # 清掉可能干扰的 env（避免指向原仓库）
        env.pop("GWEN_GAME_DB", None)
        r = subprocess.run([PY, "probe.py"], cwd=pkg, env=env, timeout=300,
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        print(f"[2] 独立运行 exit={r.returncode}")
        if r.stdout:
            for line in r.stdout.splitlines():
                print("     ", line)
        passed = "VERDICT PASS" in (r.stdout or "")
        if r.returncode != 0 or not passed:
            print("[3] ❌ 引擎尚不能独立驱动战斗", file=sys.stderr)
            if r.stderr:
                print(r.stderr[-2000:], file=sys.stderr)
        else:
            print("[3] ✅ 引擎可独立驱动战斗（真正可分发）")

        outs = scan_outside_imports(os.path.join(pkg, "battle2"))
        print(f"[4] 拆仓库必改项（引擎包内 game.* 绝对 import）：{len(outs)} 条")
        for o in outs:
            print("     ", o)

        return 0 if (r.returncode == 0 and passed) else 1
    finally:
        if args.keep:
            print(f"[5] 临时目录保留：{tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
