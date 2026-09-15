# -*- coding: utf-8 -*-
"""门禁：指令**声明驱动**接入（游戏侧，2026-09-11）。

背景：命令正则原先有两处来源（各文件 `@filter.regex(<字面量>)` + 手工维护的
`_registry.COMMAND_REGEX` 镜像表），靠「表与装饰器 1:1」测试盯着。本批把一部分指令
迁到**声明表**（`game/data/command_specs.json`），让声明成为唯一真源。

本门禁锁住迁移后的不变量：
  1. **单源**：有效表键集 == 声明表键集（字面量镜像表 `_LITERAL_REGEX` / `OVERLAP_KEYS`
     已随 2026-09-12 路线图 #9 迁移收尾退役）
  2. **派生保真**：声明 → 有效表 的正则与声明值一致；`@declared` 注册的正则 == 有效表该 key
  3. **两处 combine 同语义**：`_registry._combine_patterns` ≡ 框架 `combine_patterns`
     （本表为可独立加载而有意复制了 5 行逻辑 —— 用断言锁死，防两边漂移）
  4. **漂移自检双向干净**：声明表 ↔ 代码里 `@declared` 的实际使用
     （有声明没用 = 死声明；用了没声明 = 漏登记）
  5. **编辑器可编辑**：声明表能被框架 schema 校验通过（用编辑器真能改）
  6. **帮助/目录可用**：`catalog()` 按分类返回可见声明（声明里的 desc/category/order 有消费者）

跑法：python tests/test_v181_command_declaration.py（exit=0 全绿）
"""
import ast
import importlib.util
import json
import os
import sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PLUGIN_DIR, "framework"))
QQBOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
os.environ.setdefault("GWEN_GAME_DB", os.path.join(PLUGIN_DIR, "test_cmd_decl.db"))
os.environ.setdefault("GWEN_TEST_MODE", "1")
sys.path.insert(0, QQBOT_DIR)
sys.path.insert(0, PLUGIN_DIR)
_shim = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shim_astrbot")
if os.path.isdir(_shim) and _shim not in sys.path:
    sys.path.insert(0, _shim)

from saintess_engine.command import combine_patterns   # noqa: E402

CMD_DIR = os.path.join(PLUGIN_DIR, "game", "commands")
SPEC_FILE = os.path.join(PLUGIN_DIR, "game", "data", "command_specs.json")

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
        FAILURES.append(f"{name}: {detail}")
        print(f"  ❌ {name} {detail}")


def load_registry_module():
    spec = importlib.util.spec_from_file_location("_reg_decl", os.path.join(CMD_DIR, "_registry.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_PKG_SPEC = os.path.join(
    PLUGIN_DIR, "framework", "games", "orlandia", "content", "data", "commands.json")


def _pkg_registry():
    """包内真源声明表构建的框架注册表（旧宿主 `_declared.registry()` 的终态等价物）。"""
    from saintess_engine.command import CommandRegistry
    with open(_PKG_SPEC, encoding="utf-8") as f:
        data = json.load(f)
    return CommandRegistry.from_data(data, name="orlandia.commands")


def _pkg_catalog():
    """`{分类: [声明, ...]}`（仅 visible，按 order）——旧 `_declared.catalog()` 的终态等价物。"""
    reg = _pkg_registry()
    out = {}
    for spec in reg.visible():
        out.setdefault(spec.category or "其他", []).append(spec)
    return out


def scan_declared_usages():
    """AST 扫 `@declared("key")` → {方法名: key}。"""
    found = {}
    for fn in sorted(os.listdir(CMD_DIR)):
        if not fn.endswith(".py") or fn.startswith("_"):
            continue
        with open(os.path.join(CMD_DIR, fn), encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name)
                        and dec.func.id == "declared" and dec.args
                        and isinstance(dec.args[0], ast.Constant)
                        and isinstance(dec.args[0].value, str)):
                    found[node.name] = dec.args[0].value
    return found


# ============================================================

def test_1_single_source():
    print("【1. 单源：有效表完全由声明表派生】")
    reg = load_registry_module()
    with open(SPEC_FILE, encoding="utf-8") as f:
        specs = json.load(f)
    check("声明表非空（本批已迁入至少 7 条）", len(specs) >= 7, len(specs))
    check("有效表键集 == 声明表键集（不存在第二份来源）",
          set(reg.COMMAND_REGEX) == set(specs),
          sorted(set(reg.COMMAND_REGEX) ^ set(specs))[:5])
    check("字面量镜像表已退役（无 _LITERAL_REGEX / OVERLAP_KEYS）",
          not hasattr(reg, "_LITERAL_REGEX") and not hasattr(reg, "OVERLAP_KEYS"))


def test_2_derivation_faithful():
    print("【2. 派生保真：声明 → 有效表 → @declared 注册】")
    reg = load_registry_module()
    with open(SPEC_FILE, encoding="utf-8") as f:
        specs = json.load(f)
    bad = []
    for k, v in specs.items():
        want = combine_patterns(v.get("patterns") or [])
        if reg.COMMAND_REGEX.get(k) != want:
            bad.append((k, reg.COMMAND_REGEX.get(k), want))
    check(f"有效表 {len(specs)} 条声明与声明值逐字一致", not bad, bad[:2])

    # ★ 终态：`@declared` 用的正则 = 从**包内真源**直接构建的框架注册表逐 key 合并串
    #   （旧宿主 `_declared.registry()` 已删；引擎 `CommandRegistry.from_data` 是同一实现）。
    D = _pkg_registry()
    bad2 = [(k, D.get(k).combined(), reg.COMMAND_REGEX.get(k))
            for k in specs if D.get(k).combined() != reg.COMMAND_REGEX.get(k)]
    check("`@declared` 注册用的正则 == 有效表该 key", not bad2, bad2[:2])
    check("声明表通过 CommandRegistry.validate（无空正则/非法正则/共用正则）",
          _pkg_registry().validate() == [], _pkg_registry().validate())


def test_3_combine_semantics():
    print("【3. 两处 combine 同语义（有意复制的 5 行逻辑 → 断言锁死）】")
    reg = load_registry_module()
    cases = [([], ""), (["^a$"], "^a$"), (["^a$", "^b$"], "(?:^a$)|(?:^b$)"),
             (["^a$", "", "^b$"], "(?:^a$)|(?:^b$)"), (["x"], "x")]
    bad = [(c, reg._combine_patterns(c), combine_patterns(c))
           for c, _w in cases if reg._combine_patterns(c) != combine_patterns(c)]
    check("_registry._combine_patterns ≡ 框架 combine_patterns（5 例）", not bad, bad)
    check("空输入两边都给空串",
          reg._combine_patterns([]) == "" and combine_patterns([]) == "")


def test_4_drift_both_ways():
    print("【4. 漂移自检双向干净：声明表 ↔ @declared 实际使用】")
    D = _pkg_registry()
    used = scan_declared_usages()
    check("扫到 @declared 使用点（非空即证明迁移真的接上了）", len(used) > 0, used)
    check("方法名与声明的 key 一致（@declared(\"key\") 的 key 就是方法名惯例）",
          all(method == key for method, key in used.items()),
          {m: k for m, k in used.items() if m != k})
    au = D.audit_handlers(list(used.values()))
    check("无「用了没声明」（missing_spec 为空）", au["missing_spec"] == [], au)
    check("无「声明了没用」（missing_handler 为空）", au["missing_handler"] == [], au)
    check("audit 总体 ok", au["ok"] is True, au)
    _cat = _pkg_catalog()
    check("catalog 按分类给可见声明（desc/category/order 有消费者）",
          bool(_cat) and all(
              [s.key for s in v] == sorted([s.key for s in v], key=lambda k: D.get(k).order)
              for v in _cat.values()),
          {k: [s.key for s in v] for k, v in _cat.items()})


def test_5_editor_editable():
    print("【5. 编辑器可编辑：声明表过框架 schema 校验】")
    try:
        sys.path.insert(0, os.path.join(PLUGIN_DIR, "framework", "editor"))
        import editor.packages as PK
        import editor.validate as V
    except Exception as e:                                   # noqa: BLE001
        check("编辑器模块可导入（框架 submodule 已在位）", False, repr(e))
        return
    with open(SPEC_FILE, encoding="utf-8") as f:
        specs = json.load(f)
    bad = []
    for k, v in specs.items():
        errs = V.validate_entry("commands", v)
        if errs:
            bad.append((k, errs))
    check(f"声明表 {len(specs)} 条全部通过 `commands` schema", not bad, bad[:2])
    check("域 `commands` 已注册（编辑器 tab 可见）", "commands" in PK.DOMAINS, list(PK.DOMAINS))
    check("域 schema 文件存在", os.path.exists(
        os.path.join(PLUGIN_DIR, "framework", "schemas",
                     PK.DOMAINS["commands"]["schema"])))


def main():
    test_1_single_source()
    test_2_derivation_faithful()
    test_3_combine_semantics()
    test_4_drift_both_ways()
    test_5_editor_editable()
    print(f"\n== 结果：通过 {PASS} / 共 {PASS + FAIL} ==")
    if FAILURES:
        for f in FAILURES:
            print("  FAIL:", f)
        sys.exit(1)
    print("全绿 ✅")


if __name__ == "__main__":
    main()
