# -*- coding: utf-8 -*-
"""门禁：`host/tlog_db_sink.py::SQLiteReader.read_records()` 不许把「真读不出来」压成「空表」。

缺陷本体（复刻实测，非推断）
------------------------------
`read_records()` 原实现是一个 `except Exception` 一把兜，**返回 `iter(())`**。
而它有两个消费方，其中一个是**引擎自己的留痕面**：

  · `saintess_engine/host/runtime.py:627` ——
        for record in self._tlog_sink.read_records():
            hook(record.to_dict())
        except Exception as e:
            out.stubs.append("tlog: 流水投递未完成（%r）…")
    这圈 try 的**全部意义**就是「投递炸了要记桩」。而读失败时 `read_records()`
    返回一个**不抛的空迭代器** ⇒ try 一路绿到底、`out.stubs` 零记录
    ⇒ **引擎既有的留痕面被彻底绕过**（实测：DB 读不出来 → 桩 0 条、无日志、无异常）。
  · `scripts/tlog_report.py::_DbSource` —— 流水分析脚本读出来是「0 条」，
    与「这个玩家这段时间一条都没有」**逐字相同**。

危害：流水是「发生过什么、能不能复现」的唯一证据面。读侧静默降级 ⇒
故障复现时拿到一份**看起来合规、实际根本没读到**的流水/报表。

判定
----
[1] ★ 只兜**真·数据库层**故障（sqlite3.Error，表还没建 / 库损坏 / 锁）⇒ 降级成空表
    **但必须记 `bad_reads`**（与 `JSONLSink.bad_lines` 同名对齐，别又变成无声降级）
[2] ★ 其它异常（装配缺陷 / 注入面取不到 / 编程错误）⇒ **必须抛**，不许静默
[3] 行内 JSON 坏 ⇒ 跳过该行 fields + 记 `bad_rows`（**不是**整表丢）
[4] 合法数据 → 真读出来，一条不少
[5] 静态：`except sqlite3.Error` 是唯一允许的宽兜；`except Exception` 不许出现在读表块
[6] ★ 两向反证：把那一支改回 bare except ⇒ 本门禁必须转红；还原后复绿

跑法
----
    python tests/test_tlog_reader_read_failure_not_downgraded.py
"""
from __future__ import annotations

import ast
import contextlib
import io
import os
import sqlite3
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
for _p in (_HERE, _REPO, r"C:\Users\yuyu\framework-engine",
            r"C:\Users\yuyu\framework-engine\extends"):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from _check import bind_check                                    # noqa: E402

FAILS: list = []
PASS = 0
FAIL = 0
check = bind_check(globals(), "PASS", "FAIL", "FAILS")

SINK_PY = os.path.join(_REPO, "host", "tlog_db_sink.py")


def _reader_with_store(store_obj):
    """把 `tlog_db_sink` 的取件口指到假 store，返回一个全新的 SQLiteReader。"""
    import host.store_factory as sf
    import host.tlog_db_sink as TDS
    sf.store = lambda: store_obj
    return TDS.SQLiteReader()


class _SqliteBoom:
    """数据库层故障（表还没建 / 库损坏 / 锁）—— 这一类**允许**降级。"""

    def __init__(self, exc):
        self._exc = exc

    def connect(self):
        raise self._exc

    @staticmethod
    def lock():
        return contextlib.nullcontext()


class _NonSqliteBoom:
    """**不是**数据库层的问题（装配缺陷 / 编程错误）—— 这一类必须抛。"""

    def __init__(self, exc):
        self._exc = exc

    def connect(self):
        raise self._exc

    @staticmethod
    def lock():
        return contextlib.nullcontext()


# ---------------------------------------------------------------- 行为向
print("── SQLiteReader.read_records()：真读不出来不许变「空表」")

_r1 = _reader_with_store(_SqliteBoom(sqlite3.OperationalError("no such table: tlog")))
_got1 = list(_r1.read_records())
check("表还没建（sqlite3.OperationalError）⇒ 降级成空表，**不抛**",
      _got1 == [], "返回了 %r" % (_got1,))
check("★ 降级必须**留痕**：bad_reads 记到那一条",
      len(_r1.bad_reads) == 1 and "OperationalError" in str(_r1.bad_reads[0]),
      "bad_reads = %r" % (_r1.bad_reads,))

_r2 = _reader_with_store(_SqliteBoom(sqlite3.DatabaseError("file is not a database")))
check("库损坏（sqlite3.DatabaseError）⇒ 同样降级成空表", list(_r2.read_records()) == [])
check("★ 库损坏也留痕", len(_r2.bad_reads) == 1, "bad_reads = %r" % (_r2.bad_reads,))

_r3 = _reader_with_store(_NonSqliteBoom(ZeroDivisionError("装配缺陷，不是数据库问题")))
_raised3 = None
try:
    list(_r3.read_records())
except Exception as exc:                       # noqa: BLE001
    _raised3 = type(exc).__name__
check("★ 非数据库层异常 ⇒ **必须抛**（这一类正是被压掉的那起）",
      _raised3 == "ZeroDivisionError", "raised = %r" % (_raised3,))
check("★ 抛的那一路不许同时伪造 bad_reads（那是「降级」才有的口径）",
      _r3.bad_reads == [], "bad_reads = %r" % (_r3.bad_reads,))

# ---- 行内 JSON 坏：跳过该行 fields、留痕、**其余行照读**（不是整表丢）
print("── 行内 JSON 坏：只坏那一格，不整表丢")


class _Rows:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _Conn:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, *a, **k):
        return _Rows(self._rows)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _GoodStore:
    def __init__(self, rows):
        self._rows = rows

    def connect(self):
        return _Conn(self._rows)

    @staticmethod
    def lock():
        return contextlib.nullcontext()


_ROWS = [
    (1.0, "battle.hit", "u1", "a,b", '{"dmg": 10}'),
    (2.0, "battle.crit", "u1", "", "{这格不是 JSON"),
    (3.0, "drop.grant", "u2", "x", '{"item": "铁屑", "n": 2}'),
]
_r4 = _reader_with_store(_GoodStore(_ROWS))
_recs4 = list(_r4.read_records())
check("坏掉的那一行仍在其余行之后读出来（三行都返回）",
      len(_recs4) == 3, "读到 %d 条" % len(_recs4))
_by_kind = {r.kind: r for r in _recs4}
check("★ 坏行只丢 **fields** 那一格（记录本体与 ts 还在）",
      "battle.crit" in _by_kind and _by_kind["battle.crit"].fields == {},
      "bad row = %r" % (_by_kind.get("battle.crit"),))
check("★ 坏行进 bad_rows 留痕", len(_r4.bad_rows) == 1 and _r4.bad_rows[0][0] == "battle.crit",
      "bad_rows = %r" % (_r4.bad_rows,))
check("好行的 fields 原样读出来",
      _by_kind["battle.hit"].fields.get("dmg") == 10
      and _by_kind["drop.grant"].fields.get("n") == 2,
      "hit=%r grant=%r" % (_by_kind["battle.hit"].fields, _by_kind["drop.grant"].fields))

# ---- 合法数据一条不少
print("── 合法数据：一条不少")
_r5 = _reader_with_store(_GoodStore([
    (float(i), "k%d" % i, "u", "", "{\"i\": %d}" % i) for i in range(50)]))
_recs5 = list(_r5.read_records())
check("50 条全读出来且顺序不变",
      len(_recs5) == 50 and _recs5[0].fields.get("i") == 0 and _recs5[49].fields.get("i") == 49,
      "读到 %d 条" % len(_recs5))
check("无坏行时 bad_rows / bad_reads 都是空（别无脑记账）",
      _r5.bad_rows == [] and _r5.bad_reads == [], "%r / %r" % (_r5.bad_rows, _r5.bad_reads))

# ---------------------------------------------------------------- 静态向
print("── 静态：读表块不许有 bare / 宽 except")
_src = io.open(SINK_PY, encoding="utf-8").read()
_tree = ast.parse(_src)
_cls = next(n for n in _tree.body if isinstance(n, ast.ClassDef) and n.name == "SQLiteReader")
_fn = next(n for n in _cls.body if isinstance(n, ast.FunctionDef) and n.name == "read_records")
_handlers = [n for n in ast.walk(_fn) if isinstance(n, ast.ExceptHandler)]
_wide = [ast.unparse(n.type) if n.type else "BARE" for n in _handlers
         if n.type is None or (isinstance(n.type, ast.Name) and n.type.id == "Exception")
         or (isinstance(n.type, ast.Tuple)
             and any(isinstance(e, ast.Name) and e.id == "Exception" for e in n.type.elts))]
check("read_records 里没有 bare except / except Exception",
      not _wide, "宽兜 = %r" % (_wide,))
_sqlite3_only = [ast.unparse(n.type) if n.type else "BARE" for n in _handlers]
check("★ 允许的兜只有收窄的那两类（sqlite3.Error / (TypeError, ValueError)）",
      set(_sqlite3_only) <= {"sqlite3.Error", "(TypeError, ValueError)"},
      "实到 = %r" % (_sqlite3_only,))

print()
print("=" * 64)
print("  通过 %d / 失败 %d" % (PASS, FAIL))
for f in FAILS:
    print("   ❌ " + f)
sys.exit(1 if FAIL else 0)
