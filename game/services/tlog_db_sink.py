# -*- coding: utf-8 -*-
"""流水的 SQLite 出口（**可选**）—— 表结构与索引见 `docs/REFACTOR_tlog_landing.md` §五。

默认出口是 `JSONLSink`（落文件、可 grep、零 DB 风险）；要按玩家/时间段做**查询**时换这个：

    from game import tlog_setup
    from game.services.tlog_db_sink import SQLiteSink
    tlog_setup.enable(sinks=[SQLiteSink()])

* 表 `tlog` 是**旁路表**：不进存档路径（`battle_state` 等不受影响），可独立清理/归档。
* 写入走既有 store 连接与事务（批量 `executemany`），异常只报不抛（流水不该影响主流程）。
* `SQLiteSink.read_records()` / `SQLiteReader` 让 `saintess_engine.tlog.Reader` 直接读库
  （筛选口径与 JSONL 完全一致）。
"""
from __future__ import annotations

import json
import time
from typing import Iterable, Iterator, Optional

from saintess_engine.tlog import Record

__all__ = ["TABLE_SQL", "INDEX_SQL", "SQLiteSink", "SQLiteReader", "ensure_table"]

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
    from ..store import connection as _c
    return _c._connect()


def _lock():
    from ..store import connection as _c
    return _c._lock


def _atomic():
    from ..store import connection as _c
    return _c.atomic()


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
    """只读口（`saintess_engine.tlog.Reader` 的适配源）。"""

    def read_records(self) -> Iterator[Record]:
        try:
            with _lock():
                c = _conn()
                rows = c.execute(
                    "SELECT ts, kind, actor, tags, fields FROM tlog ORDER BY ts, id").fetchall()
        except Exception:                                         # noqa: BLE001
            return iter(())
        out = []
        for ts, kind, actor, tags, fields in rows or ():
            try:
                f = json.loads(fields or "{}")
            except Exception:                                     # noqa: BLE001
                f = {}
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
