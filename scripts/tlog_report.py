# -*- coding: utf-8 -*-
"""流水分析脚本 —— 出「某玩家某段流水」的汇总（markdown）。

用框架同一个读口（`saintess_engine.tlog.Reader` / `Replay`），所以**筛选口径与回放一致**：
kind 支持 `battle.` 前缀匹配整族，时间窗左闭右开。

用法::

    python scripts/tlog_report.py --file data/tlog.jsonl --actor 1454832774 --since 2026-09-12
    python scripts/tlog_report.py --file data/tlog.jsonl --kind battle. --limit 40
    python scripts/tlog_report.py --db --actor 1454832774            # 读 SQLite 出口（需已启用）

退出码：0 = 正常（无记录也算 0）；1 = 参数/读取错误。
"""
import argparse
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_PD = os.path.dirname(_HERE)
for _p in (_PD, _HERE, os.path.join(_PD, "tests"), os.path.join(_PD, "framework"),
           os.path.dirname(os.path.dirname(_PD))):
    sys.path.insert(0, _p)

from saintess_engine.tlog import JSONLSink, Reader, Replay  # noqa: E402


def _ts(v):
    """把 `YYYY-MM-DD[ HH:MM[:SS]]` 或秒数转成时间戳。"""
    if v in (None, ""):
        return None
    s = str(v).strip()
    try:
        return float(s)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return time.mktime(time.strptime(s, fmt))
        except ValueError:
            continue
    raise SystemExit(f"❌ 无法解析时间：{v!r}（用 YYYY-MM-DD[ HH:MM[:SS]] 或秒数）")


class _DbSource:
    """SQLite 出口的只读源（`saintess_engine.tlog.Reader` 适配）。"""

    def read_records(self):
        from game.services.tlog_db_sink import SQLiteReader
        return SQLiteReader().read_records()


def _fmt_fields(fields, width=90):
    parts = []
    for k, v in (fields or {}).items():
        s = str(v)
        if len(s) > 40:
            s = s[:37] + "…"
        parts.append(f"{k}={s}")
    out = " ".join(parts)
    return out if len(out) <= width else out[:width - 1] + "…"


def main(argv=None):
    ap = argparse.ArgumentParser(description="流水分析（某玩家某段流水）")
    ap.add_argument("--file", default=os.path.join(_PD, "data", "tlog.jsonl"),
                    help="JSONL 流水文件（默认 data/tlog.jsonl）")
    ap.add_argument("--db", action="store_true", help="改读 SQLite 出口（tlog 表）")
    ap.add_argument("--actor", default=None, help="只看某主体")
    ap.add_argument("--kind", default=None, help="kind 或前缀（battle. 匹配整族）")
    ap.add_argument("--tag", default=None, help="只看带该标签的记录")
    ap.add_argument("--since", default=None, help="起点（含）")
    ap.add_argument("--until", default=None, help="终点（不含）")
    ap.add_argument("--limit", type=int, default=30, help="明细最多打几条（默认 30）")
    args = ap.parse_args(argv)

    src = _DbSource() if args.db else JSONLSink(args.file)
    rd = Reader([src])
    flt = dict(kind=args.kind, actor=args.actor, tag=args.tag,
               since=_ts(args.since), until=_ts(args.until))
    rows = list(rd.iter_records(**flt))
    rp = Replay(rows, name="report")
    sm = rp.summary()

    print(f"# 流水报告（{os.path.basename(args.file) if not args.db else 'tlog 表'}）\n")
    print(f"- 记录数：**{sm['count']}**")
    if sm["count"]:
        t0, t1 = sm["span"]
        print(f"- 时间跨度：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t0))} → "
              f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t1))}")
        print(f"- 主体：{', '.join(sm['actors'][:10]) or '（无）'}")
        print(f"- 筛选：kind={args.kind or '全部'} · actor={args.actor or '全部'} · "
              f"tag={args.tag or '全部'}")
        print("\n## 按 kind 分布\n")
        print("| kind | 条数 |")
        print("|---|---|")
        for k, n in sorted(sm["per_kind"].items(), key=lambda kv: -kv[1]):
            print(f"| `{k}` | {n} |")
        print(f"\n## 明细（最近 {min(args.limit, sm['count'])} 条）\n")
        print("| 时间 | kind | 主体 | 字段 |")
        print("|---|---|---|---|")
        for r in rows[-args.limit:]:
            t = time.strftime("%m-%d %H:%M:%S", time.localtime(r.ts))
            print(f"| {t} | `{r.kind}` | {r.actor or '-'} | {_fmt_fields(r.fields)} |")
    else:
        print(f"\n（没有匹配记录；文件 `{args.file}` 存在 = {os.path.exists(args.file)}"
              f"，或改用 `--db` 读库）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
