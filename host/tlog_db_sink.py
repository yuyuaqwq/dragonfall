# -*- coding: utf-8 -*-
"""流水的 SQLite 出口（**平台件** · P5C：原 `game/services/tlog_db_sink.py` 迁入宿主）。

默认出口是 `JSONLSink`（落文件、可 grep、零 DB 风险）；要按玩家/时间段做**查询**时换这个：

    from host import tlog_setup
    from host.tlog_db_sink import SQLiteSink
    tlog_setup.enable(sinks=[SQLiteSink()])

* 表 `tlog` 是**旁路表**：不进存档路径（`battle_state` 等不受影响），可独立清理/归档。
* 写入走既有 store（包内存档半边 = 同一只库、同一把锁），异常只报不抛（流水不该影响主流程）。
* `SQLiteSink.read_records()` / `SQLiteReader` 让 `saintess_engine.tlog.Reader` 直接读库
  （筛选口径与 JSONL 完全一致）。

与源件（`game/services/tlog_db_sink.py`）的差异**只有取件口**：原文件经
`game/store/connection.py` 的 `_connect()` / `_lock` / `atomic()`；本文件走宿主
`host/store_factory.py` 的存档口（`store().connect()` / `store().lock()`）——**同一只库、同一把锁**
（`content/persistence/handles` 是同一实现）。本文件**零包知识**：不写包名、不写 `content.*`。
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from typing import Iterable, Iterator

from saintess_engine.tlog import Record

from . import store_factory as _sf

__all__ = ["TABLE_SQL", "INDEX_SQL", "SQLiteSink", "SQLiteReader", "ensure_table", "make"]

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS tlog (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      REAL    NOT NULL,
    kind    TEXT    NOT NULL,
    actor   TEXT    NOT NULL DEFAULT '',
    tags    TEXT    NOT NULL DEFAULT '',
    fields  TEXT    NOT NULL DEFAULT '{}'
);
"""

INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_tlog_actor_ts ON tlog(actor, ts);",
    "CREATE INDEX IF NOT EXISTS idx_tlog_kind_ts  ON tlog(kind, ts);",
)


def _conn():
    return _sf.store().connect()


def _lock():
    return _sf.store().lock()


@contextmanager
def _atomic():
    """事务 + 锁（≡ 原 `game/store/connection.py::atomic()` 的取件口径）。"""
    store = _sf.store()
    with store.lock():
        conn = store.connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def ensure_table() -> None:
    """建表 + 建索引（幂等）。"""
    with _lock():
        c = _conn()
        c.execute(TABLE_SQL)
        for sql in INDEX_SQL:
            c.execute(sql)
        c.commit()


def _row_of(record: Record) -> tuple:
    return (float(record.ts), str(record.kind), str(record.actor or ""),
            ",".join(str(t) for t in record.tags), json.dumps(record.fields, ensure_ascii=False))


class SQLiteSink:
    """把记录批量写进 `tlog` 表。`batch` = 每多少条提交一次（默认 50）。"""

    def __init__(self, *, batch: int = 50, ensure: bool = True) -> None:
        self.batch = max(1, int(batch))
        self._buf: list = []
        self.written = 0
        self.errors = 0
        if ensure:
            try:
                ensure_table()
            except Exception:                                     # noqa: BLE001
                self.errors += 1

    def write(self, records: Iterable[Record]) -> None:
        for r in records:
            self._buf.append(_row_of(r))
        if len(self._buf) >= self.batch:
            self.flush()

    def flush(self) -> None:
        if not self._buf:
            return
        rows, self._buf = self._buf, []
        try:
            with _lock():
                c = _conn()
                c.executemany(
                    "INSERT INTO tlog (ts, kind, actor, tags, fields) VALUES (?, ?, ?, ?, ?)",
                    rows)
                c.commit()
            self.written += len(rows)
        except Exception:                                         # noqa: BLE001
            self.errors += 1                                      # 丢一批不抛：流水不影响主流程
            self._buf = rows + self._buf

    def close(self) -> None:
        self.flush()

    def read_records(self) -> Iterator[Record]:
        return SQLiteReader().read_records()

    def clear(self) -> int:
        """清空流水表（归档/测试用），返回删除行数。"""
        try:
            with _lock():
                c = _conn()
                n = int(c.execute("SELECT COUNT(*) FROM tlog").fetchone()[0])
                c.execute("DELETE FROM tlog")
                c.commit()
            return n
        except Exception:                                         # noqa: BLE001
            return 0


class SQLiteReader:
    """只读口（`saintess_engine.tlog.Reader` 的适配源）。

    ★ 两个 bad 口与可读出口的既有约定同名对齐（见 `JSONLSink.bad_lines`）：
      · `bad_rows` = **读到了行、但那一格的 JSON 坏** ⇒ 跳过该行的 fields（记录留痕）
      · `bad_reads` = **整表读不出来**（sqlite3.Error）⇒ 降级成空表 + 记一条（记录留痕）
    """

    def __init__(self) -> None:
        self.bad_rows: list = []
        self.bad_reads: list = []

    def read_records(self) -> Iterator[Record]:
        try:
            with _lock():
                c = _conn()
                rows = c.execute(
                    "SELECT ts, kind, actor, tags, fields FROM tlog ORDER BY ts, id").fetchall()
        except sqlite3.Error as exc:
            # ★ 晚到批（第四十一轮 · 与 tlog_setup.kinds() 同一个病）：**只有真读不到**才降级成空表。
            #   原实现一个 except Exception 把「表还没建」（sqlite3.OperationalError）
            #   与「读炸了」（库损坏 / 文件锁 / 权限 / 字段对不上）压成同一个空迭代器
            #   ⇒ 引擎 saintess_engine/host/runtime.py:627 那圈 try **抓不到**（它根本不抛），
            #   「out.stubs」零记录 ⇒ 「本场流水投递未完成」这个既有的留痕面被完全绕过。
            #   口径与可读出口的既有约定同一条（JSONLSink.read_records）：
            #   **坏行跳过并记 bad_lines**，但**整表读不出来 = 真故障，要抛**。
            self.bad_reads.append(("sqlite:", "%s: %s" % (type(exc).__name__, exc)))
            return iter(())
        out = []
        for ts, kind, actor, tags, fields in rows or ():
            try:
                f = json.loads(fields or "{}")
            except (TypeError, ValueError):                        # ★ 收窄：只兜「这一格的 JSON 坏」
                f = {}                                            #   其它异常照旧往上抛
                self.bad_rows.append((kind, str(fields)[:120]))
            out.append(Record(kind=kind, ts=float(ts), actor=actor or "",
                              fields=f if isinstance(f, dict) else {},
                              tags=tuple(t for t in str(tags or "").split(",") if t)))
        return iter(out)


def make(kind: str = "jsonl", **kw):
    """出口工厂：`kind="jsonl"|"db"`（配置里给名字即可）。"""
    if str(kind).lower() in ("db", "sqlite", "sql"):
        return SQLiteSink(**kw)
    from saintess_engine.tlog import JSONLSink
    return JSONLSink(kw.pop("path", "data/tlog.jsonl"), **kw)
