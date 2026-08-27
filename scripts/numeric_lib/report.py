# -*- coding: utf-8 -*-
"""输出层：markdown 表格 / JSON / 双表 diff（工具集所有 CLI 统一从这里出）。

设计：所有数据先整理成 list[dict]（rows）→ md_table / to_json 互转；
diff_tables(before, after) 输出逐行 旧→新 变化，供方案预演对比。
"""
import json


def md_table(rows: list[dict], col_order: list[str] | None = None,
             col_names: dict | None = None) -> str:
    """rows → markdown 表格。列序 = col_order（缺省按首行 key 序）。
    col_names 可选：key → 中文表头。"""
    if not rows:
        return "_(空)_"
    cols = col_order or list(rows[0].keys())
    names = {c: col_names.get(c, c) for c in cols} if col_names else {c: c for c in cols}
    head = "| " + " | ".join(names[c] for c in cols) + " |"
    sep = "|" + "---|" * len(cols)
    body = []
    for r in rows:
        body.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
    return "\n".join([head, sep] + body)


def md_lines(title: str | None = None, rows: list[dict] | None = None,
             col_order: list[str] | None = None, col_names: dict | None = None) -> list[str]:
    """标题 + 表格（多变行友好）。"""
    lines = []
    if title:
        lines.append(title)
    if rows:
        lines.append(md_table(rows, col_order, col_names))
    return lines


def to_json(data, path: str | None = None) -> str:
    """JSON 序列化（ensure_ascii=False 中文可见）；path 给定则落盘并返回文本。"""
    text = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return text


def diff_tables(before: list[dict], after: list[dict], key_col: str = "iid",
                num_cols: list[str] | None = None) -> str:
    """双表对比：按 key_col 对齐，数值列输出 旧 → 新（绝对差%）。"""
    num_cols = num_cols or ["rounds", "boss_hp", "ratio"]
    bmap = {r[key_col]: r for r in before}
    rows = []
    for r in after:
        b = bmap.get(r[key_col], {})
        row = {key_col: r[key_col]}
        for c in r:
            if c == key_col:
                continue
            if c in num_cols and c in b:
                bv, av = b.get(c), r.get(c)
                try:
                    diff = (float(av) - float(bv)) / max(abs(float(bv)), 1e-9) * 100
                    row[c] = f"{bv} → {av} ({diff:+.0f}%)"
                except (TypeError, ValueError):
                    row[c] = f"{bv} → {av}"
            else:
                row[c] = r.get(c)
        rows.append(row)
    return md_table(rows)