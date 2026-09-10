# -*- coding: utf-8 -*-
"""引擎纯度门禁（S1）—— `game/battle2/**` 零「引擎 → 内容」import 边。

规格：docs/ENGINE_CONTENT_SPLIT_PLAN.md §3.2（15 条反向边）+ §7 S1 验证点。
本测试是防倒退的关键：引擎（game/battle2/）一旦再 import 内容层，
战斗引擎的可分发性（framework-engine submodule）即被破坏。

断言（AST 静态分析，不做运行时 import）：
  1. `game/battle2/**/*.py` 内零 import 边指向
       game.content / game.data / game.engine / game.core.constants
     （含相对导入按包名解析；含 `from X import name` 的 name 级候选）
  2. 零动态导入穿透：`importlib.import_module("game.*")` / `__import__("game.*")`
     （引擎不得用动态 import 绕开静态门禁）
  3. 反向边清单（§3.2 R1–R15）回归锚：`actions.py` 不再持有 kind 中文字面量
     模块常量（K_PHYS/K_MAGI/K_TRUE/K_HEAL/K_BUFF）与死 import

运行：python tests/test_engine_no_content.py（exit=0 全绿）
"""
import ast
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(_HERE)
ENGINE_DIR = os.path.join(PLUGIN_DIR, "game", "battle2")

# 禁止的边：引擎不得指向内容层（含其子模块）
# S1：game.content / game.data / game.engine / game.core.constants（15 条反向边）
# S3：game.core（通用件已归位 game/battle2/support/，引擎不再需要 core 任何模块）
FORBIDDEN = ("game.content", "game.data", "game.engine", "game.core")
# 禁止绕过静态门禁的动态导入前缀
DYNAMIC_FORBIDDEN = ("game.content", "game.data", "game.engine", "game.core",
                     "game.services", "game.commands", "game.store")

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name} {detail}")


def _pkg_of(path: str) -> str:
    """文件路径 → 其所属包名（PLUGIN_DIR 为 sys.path 根）。"""
    rel = os.path.relpath(path, PLUGIN_DIR).replace("\\", "/")
    parts = rel.split("/")[:-1]  # 去掉文件名
    return ".".join(parts)


def _resolve(module, level: int, pkg: str):
    """相对导入 → 绝对模块名（level=0 → 原样）。"""
    if not level:
        return module
    parts = pkg.split(".")
    # level=1 → 当前包；level=2 → 上一级…
    base = parts[: len(parts) - (level - 1)] if level > 1 else parts
    base = ".".join(base)
    return f"{base}.{module}" if module else base


def _is_forbidden(name: str, forbidden) -> bool:
    if not name:
        return False
    return any(name == f or name.startswith(f + ".") for f in forbidden)


def _iter_dynamic_imports(node):
    """AST 里 importlib.import_module("...") / __import__("...") 的字符串常量。"""
    if isinstance(node, ast.Call):
        fn = node.func
        fname = ""
        if isinstance(fn, ast.Attribute):
            fname = fn.attr
        elif isinstance(fn, ast.Name):
            fname = fn.id
        if fname in ("import_module", "__import__"):
            for a in node.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    yield a.value


# ---- S2 公开 API 面（§5）：内容层实际消费的符号清单（26 个，文档写 25）----
API_SYMBOLS = [
    "deal_damage", "state_def", "heal_actor", "Battle", "actor_alive",
    "act_apply", "cap_of", "actor_stats", "apply_effects", "now_of",
    "stats", "register_action", "config", "fire", "all_state_effects",
    "action_time", "initial_ct", "hostile_sides", "act_shield",
    "norm_stack", "effects", "heal_amount", "skill_pay_of", "make_actor",
    "get_effect_rules", "get_effect_actions",
]
# 私有 → 公开的 5 个符号（旧下划线名保别名：模块 → (公开名, 私有名)）
PROMOTED_ALIASES = [
    ("effects", "cap_of", "_cap_of"),
    ("effects", "norm_stack", "_norm_stack"),
    ("battle", "now_of", "_now_of"),
    ("actions", "heal_amount", "_heal_amount"),
    ("actions", "skill_pay_of", "_skill_pay_of"),
]


def _priv_refs_in_content():
    """内容层（game/ 除 battle2）里对 battle2 下划线私有符号的引用（S2 grep 断言）。"""
    import re
    bad = []
    pat = re.compile(r"battle2\.\w+\._\w+|from\s+(?:\.\.)?battle2\.\w+\s+import\s+_\w+")
    for root, dirs, files in os.walk(os.path.join(PLUGIN_DIR, "game")):
        if os.sep + "battle2" in root:
            continue
        for fn in sorted(files):
            if not fn.endswith(".py"):
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, PLUGIN_DIR).replace("\\", "/")
            for i, line in enumerate(open(p, encoding="utf-8").read().splitlines(), 1):
                if pat.search(line):
                    bad.append(f"{rel}:{i}: {line.strip()}")
    return bad


def scan():
    """返回 (边违规列表, 动态导入违规列表, 已扫描文件数)。"""
    edge_bad, dyn_bad, n_files = [], [], 0
    for root, _dirs, files in os.walk(ENGINE_DIR):
        for fn in sorted(files):
            if not fn.endswith(".py"):
                continue
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, PLUGIN_DIR).replace("\\", "/")
            n_files += 1
            src = open(path, encoding="utf-8").read()
            tree = ast.parse(src, filename=path)
            pkg = _pkg_of(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    mod = _resolve(node.module, node.level, pkg)
                    cands = [mod] + [f"{mod}.{a.name}" for a in node.names] if mod else []
                    for c in cands:
                        if _is_forbidden(c, FORBIDDEN):
                            edge_bad.append(f"{rel}:{node.lineno}: from {'.' * node.level}{node.module or ''} import ... → {c}")
                elif isinstance(node, ast.Import):
                    for a in node.names:
                        if _is_forbidden(a.name, FORBIDDEN):
                            edge_bad.append(f"{rel}:{node.lineno}: import {a.name}")
                for s in _iter_dynamic_imports(node):
                    if _is_forbidden(s, DYNAMIC_FORBIDDEN):
                        dyn_bad.append(f"{rel}:{node.lineno}: 动态导入 {s!r}")
    return edge_bad, dyn_bad, n_files


def main():
    print("== 引擎纯度门禁：game/battle2 零引擎→内容 import 边 ==")
    check("引擎目录存在", os.path.isdir(ENGINE_DIR), ENGINE_DIR)

    edge_bad, dyn_bad, n_files = scan()
    check("扫描到引擎 .py 文件（13+）", n_files >= 13, f"n={n_files}")
    check("零 引擎→内容 import 边（S1: content/data/engine/core.constants；S3: core）",
          not edge_bad, "\n      " + "\n      ".join(edge_bad))
    check("零 动态导入穿透（importlib/__import__ 指向 game.*）",
          not dyn_bad, "\n      " + "\n      ".join(dyn_bad))

    # ---- §3.2 R1/R2/R7/R14/R15 回归锚：actions.py 的旧反向边/字面量已清 ----
    act = os.path.join(ENGINE_DIR, "actions.py")
    src = open(act, encoding="utf-8").read()
    tree = ast.parse(src, filename=act)
    mod_consts = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    mod_consts.add(t.id)
    check("actions.py 无 kind 中文字面量常量（K_PHYS/K_MAGI/K_TRUE/K_HEAL/K_BUFF）",
          not ({"K_PHYS", "K_MAGI", "K_TRUE", "K_HEAL", "K_BUFF"} & mod_consts),
          f"残留={sorted({'K_PHYS','K_MAGI','K_TRUE','K_HEAL','K_BUFF'} & mod_consts)}")
    check("actions.py 模块级零 game.engine / game.content / game.core 导入",
          "from .. import engine" not in src and "from .. import content" not in src
          and "from ..core import constants" not in src)

    # ---- S1 注入面存在（内容侧装配契约）----
    cfg = os.path.join(ENGINE_DIR, "config.py")
    csrc = open(cfg, encoding="utf-8").read()
    for hook in ("formulas", "panel_fn", "skill_lookup", "monster_skill_fn",
                 "basic_skill_fn", "basic_fallback", "kinds"):
        check(f"config 注入面含 hook {hook!r}", f'"{hook}"' in csrc)
    check("config.load_game_defaults 保留（52 测试调用点的兼容 shim）",
          "def load_game_defaults" in csrc)

    # ---- S2 公开 API 面：包门面全量 re-export + 5 私有升公开保别名 ----
    if PLUGIN_DIR not in sys.path:
        sys.path.insert(0, PLUGIN_DIR)
    import game.battle2 as _B2  # noqa: E402
    missing = [s for s in API_SYMBOLS if not hasattr(_B2, s)]
    check(f"battle2 包门面 re-export §5 全量 {len(API_SYMBOLS)} 符号", not missing,
          f"missing={missing}")
    alias_bad = []
    for mod_name, pub, priv in PROMOTED_ALIASES:
        mod = getattr(_B2, mod_name, None)
        pub_ok = hasattr(_B2, pub) and mod is not None and hasattr(mod, pub)
        alias_ok = mod is not None and hasattr(mod, priv) and getattr(mod, priv) is getattr(mod, pub, None)
        if not (pub_ok and alias_ok):
            alias_bad.append(f"{mod_name}:{pub}/{priv}")
    check("5 私有符号已升公开且旧下划线名为同一对象别名", not alias_bad,
          f"bad={alias_bad}")
    check("存档兼容（§8-R11）：Battle.from_state / to_state 在 API 面内",
          hasattr(_B2.Battle, "from_state") and hasattr(_B2.Battle, "to_state")
          and hasattr(_B2, "from_state") and hasattr(_B2, "to_state"))

    # ---- S2 grep 断言：内容层（game/ 除 battle2）不再引用引擎下划线私有符号 ----
    priv_bad = _priv_refs_in_content()
    check("内容层零 battle2 下划线私有符号引用", not priv_bad,
          "\n      " + "\n      ".join(priv_bad))

    print(f"\n===== 结果：通过 {passed} / {passed + failed} =====")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
