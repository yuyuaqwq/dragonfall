# -*- coding: utf-8 -*-
"""门禁：指令表单源化（路线图 #9 收尾后）—— 冻结比对 + 单源结构。

背景：命令正则原有两处来源（各文件 `@filter.regex(<字面量>)` + `_registry._LITERAL_REGEX`
手工镜像表），靠一个「表与装饰器 1:1」测试盯着。2026-09-12 把 194 条指令逐批搬进声明表
（`game/data/command_specs.json`）+ `@declared("key")`，镜像表已删除。

本门禁守两件事：
  一、**搬家只能搬家**：迁移开始前的有效表（`COMMAND_REGEX` 194 条）冻结在
      `tests/_command_table_freeze.json`（sha256 双锁），此后**逐字相等**。
  二、**单源结构**：有效表 == 声明表派生；镜像表 / 字面量装饰器都不复存在（防有人重新引入
      第二份正则）。将来若**有意**新增指令：只在声明表加声明 + `@declared("key")`，
      并显式更新冻结快照（否则本门禁按「凭空多出来的 key」报红）。

断言：
  A. 冻结比对：当前有效表 == 快照（键集合 + 每条正则逐字 + sha256）
  B. 单源结构：有效表键集 == 声明表键集；无 `_LITERAL_REGEX` / `OVERLAP_KEYS` 残留；
     命令层 AST 扫描零 `@filter.regex` 装饰器
  C. 没有任何 key 在迁移中丢失 / 凭空多出
  D. 比较器有牙（反证）：改一格 / 删一格 / 加一格 → 比对必须报红

跑法：python tests/test_v185_command_migration.py（exit=0 全绿）
"""
import ast
import hashlib
import importlib.util
import json
import os
import sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CMD_DIR = os.path.join(PLUGIN_DIR, "game", "commands")
SPEC_FILE = os.path.join(PLUGIN_DIR, "game", "data", "command_specs.json")
SNAP_FILE = os.path.join(PLUGIN_DIR, "tests", "_command_table_freeze.json")

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
    spec = importlib.util.spec_from_file_location(
        "_reg_freeze", os.path.join(CMD_DIR, "_registry.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_specs():
    with open(SPEC_FILE, encoding="utf-8") as f:
        return json.load(f)


def digest_of(table):
    blob = json.dumps({k: v for k, v in sorted(table.items())},
                      ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def diff_tables(old, new):
    """返回逐格差异列表（比较器本体，反证组直接调它）。"""
    return sorted((k, old.get(k), new.get(k))
                  for k in set(old) | set(new) if old.get(k) != new.get(k))


def regex_decorators():
    """AST 扫命令模块里的 `@<ns>.regex(...)` 装饰器（不看注释与文档串）。"""
    out = []
    for fn in sorted(os.listdir(CMD_DIR)):
        if not fn.endswith(".py"):
            continue
        with open(os.path.join(CMD_DIR, fn), encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)
                        and dec.func.attr == "regex"):
                    out.append(f"{fn}:{node.name}")
    return out


def test_A_frozen_table():
    print("【A. 冻结比对：有效指令表逐字不变】")
    reg = load_registry_module()
    snap = json.load(open(SNAP_FILE, encoding="utf-8"))
    old_table = snap["table"]
    now = dict(reg.COMMAND_REGEX)
    diff = diff_tables(old_table, now)
    check(f"有效表 {len(now)} 条 == 快照 {len(old_table)} 条（键集合一致）",
          set(old_table) == set(now),
          [k for k, _a, _b in diff][:5])
    check("每条正则逐字相等（迁移 = 搬家，不改命令面）", not diff, diff[:3])
    check("sha256 == 快照（%s）" % snap["sha256"][:12],
          digest_of(now) == snap["sha256"], digest_of(now))


def test_B_single_source():
    print("【B. 单源结构：有效表 = 声明表派生；镜像表与字面量装饰器都不存在】")
    reg = load_registry_module()
    specs = load_specs()
    check("有效表键集 == 声明表键集（不存在第二份来源）",
          set(reg.COMMAND_REGEX) == set(specs),
          sorted(set(reg.COMMAND_REGEX) ^ set(specs))[:5])
    check("字面量镜像表已退役（无 _LITERAL_REGEX / OVERLAP_KEYS）",
          not hasattr(reg, "_LITERAL_REGEX") and not hasattr(reg, "OVERLAP_KEYS"))
    left = regex_decorators()
    check("命令层零 @filter.regex 装饰器残留（AST 扫描，跳过注释/文档串）", not left, left[:5])


def test_C_no_key_lost():
    print("【C. 没有任何 key 在迁移中丢失】")
    reg = load_registry_module()
    snap = json.load(open(SNAP_FILE, encoding="utf-8"))
    missing = sorted(set(snap["table"]) - set(reg.COMMAND_REGEX))
    check("快照里的 key 全在有效表里", not missing, missing[:5])
    extra = sorted(set(reg.COMMAND_REGEX) - set(snap["table"]))
    check("没有凭空多出来的 key（新增指令须显式更新快照）", not extra, extra[:5])


def test_D_comparator_has_teeth():
    print("【D. 比较器有牙（反证）】")
    snap = json.load(open(SNAP_FILE, encoding="utf-8"))["table"]
    base = dict(snap)
    k0 = sorted(base)[0]

    changed = dict(base); changed[k0] = changed[k0] + "x"
    check("改一格 → 必报红", diff_tables(base, changed) != [])

    dropped = dict(base); dropped.pop(k0)
    check("删一格 → 必报红", diff_tables(base, dropped) != [])

    added = dict(base); added["__ghost__"] = "^x$"
    check("加一格 → 必报红", diff_tables(base, added) != [])

    check("原样 → 报绿（不假阳性）", diff_tables(base, dict(base)) == [])


def main():
    test_A_frozen_table()
    test_B_single_source()
    test_C_no_key_lost()
    test_D_comparator_has_teeth()
    if PASS and not FAIL:
        print(f"\n  单源已达成：{len(load_registry_module().COMMAND_REGEX)} 条指令全部来自声明表")
    print(f"\n== 结果：通过 {PASS} / 共 {PASS + FAIL} ==")
    if FAILURES:
        for f in FAILURES:
            print("  FAIL:", f)
        sys.exit(1)
    print("全绿 ✅")


if __name__ == "__main__":
    main()
