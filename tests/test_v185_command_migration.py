# -*- coding: utf-8 -*-
"""门禁：指令表迁移（路线图 #9）的**冻结比对** —— 迁移只能搬家，不能动命令面。

背景：路线图 #9「指令表迁移收尾」要把 `game/commands/_registry.py` 里手写维护的
`_LITERAL_REGEX`（与各文件 `@filter.regex(<字面量>)` 1:1 同步的镜像表）逐批搬进
`game/data/command_specs.json` 声明表，让声明成为**唯一真源**。

搬家的过程必须**零行为变化**：玩家发什么消息命中哪条指令，一个字都不能变。
本门禁把「迁移开始前」的有效表（`COMMAND_REGEX` 194 条）冻结在
`tests/_command_table_freeze.json`，迁移每一批之后都要求**逐字相等**。

断言：
  A. 冻结比对：当前有效表 == 快照（键集合 + 每条正则逐字）
  B. 无双源：`OVERLAP_KEYS` 为空（同 key 不能既在声明表又在字面量表）
  C. 有效表 = 声明派生 ∪ 字面量（条数对得上，且没有任何 key 在迁移中丢失）
  D. 比较器有牙（反证）：故意改一格 / 删一格 / 加一格 → 比对必须报红
  E. 进度可见：打印「已迁 / 未迁」条数（迁移收尾后 `_LITERAL_REGEX` 应为空）

跑法：python tests/test_v185_command_migration.py（exit=0 全绿）
"""
import hashlib
import importlib.util
import json
import os
import sys

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CMD_DIR = os.path.join(PLUGIN_DIR, "game", "commands")
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


def digest_of(table):
    blob = json.dumps({k: v for k, v in sorted(table.items())},
                      ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def diff_tables(old, new):
    """返回逐格差异列表（比较器本体，反证组直接调它）。"""
    return sorted((k, old.get(k), new.get(k))
                  for k in set(old) | set(new) if old.get(k) != new.get(k))


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


def test_B_no_dual_source():
    print("【B. 无双源：声明表与字面量表不重叠】")
    reg = load_registry_module()
    check("OVERLAP_KEYS 为空", reg.OVERLAP_KEYS == [], reg.OVERLAP_KEYS)
    check("有效表 = 声明派生 ∪ 字面量（条数对得上）",
          len(reg.COMMAND_REGEX) == len(reg._DECLARED_REGEX) + len(reg._LITERAL_REGEX),
          (len(reg.COMMAND_REGEX), len(reg._DECLARED_REGEX), len(reg._LITERAL_REGEX)))


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


def test_E_progress():
    print("【E. 迁移进度】")
    reg = load_registry_module()
    n_dec, n_lit = len(reg._DECLARED_REGEX), len(reg._LITERAL_REGEX)
    total = n_dec + n_lit
    print(f"  已迁（声明表）= {n_dec} / {total} 条；未迁（字面量表）= {n_lit} 条")
    check("声明派生非空（迁移确实接上了）", n_dec >= 7, n_dec)
    if n_lit == 0:
        print("  🎉 迁移收尾：字面量表已清空，声明表是唯一真源")


def main():
    test_A_frozen_table()
    test_B_no_dual_source()
    test_C_no_key_lost()
    test_D_comparator_has_teeth()
    test_E_progress()
    print(f"\n== 结果：通过 {PASS} / 共 {PASS + FAIL} ==")
    if FAILURES:
        for f in FAILURES:
            print("  FAIL:", f)
        sys.exit(1)
    print("全绿 ✅")


if __name__ == "__main__":
    main()
