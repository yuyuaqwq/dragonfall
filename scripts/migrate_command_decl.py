# -*- coding: utf-8 -*-
"""指令表迁移（路线图 #9）—— 一批一次：`@filter.regex(<字面量>)` → `@declared("<key>")`。

用法：
    python scripts/migrate_command_decl.py _decl_batch1.json            # 实跑
    python scripts/migrate_command_decl.py _decl_batch1.json --dry-run  # 只看要改什么

做四件事（每一步都有自检，任何不一致直接抛错，不做「差不多」）：
  1. 核对：模块里该方法的 `@filter.regex` 字面量 == `_registry._LITERAL_REGEX` 同 key 的值
  2. 换装饰器：`@filter.regex(r"...", **kw)` → `@declared("<key>", **kw)`（正则**逐字**来自字面表）
  3. 补 import：`from ._declared import declared`（缺则加，位置对齐既有已迁文件）
  4. 删字面表条目（连同紧贴其上的、仅属于该 key 的注释；注释原文打印出来，便于人工核对没丢东西）
  5. 追加声明到 `game/data/command_specs.json`（patterns/desc/category/usage/guards/order[/page_size][/extra]）

守卫名由**装饰器链**派生（`require_player` → "player"、`require_battle` → "battle"），不手填。
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import re
import sys

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CMD_DIR = os.path.join(PLUGIN, "game", "commands")
REGISTRY = os.path.join(CMD_DIR, "_registry.py")
SPEC = os.path.join(PLUGIN, "game", "data", "command_specs.json")

DRY = "--dry-run" in sys.argv


def load_registry():
    spec = importlib.util.spec_from_file_location("_reg_mig", REGISTRY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def guards_of(src, node):
    out = []
    for dec in node.decorator_list:
        f = dec.func if isinstance(dec, ast.Call) else dec
        name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
        if name == "require_player":
            out.append("player")
        elif name == "require_battle":
            out.append("battle")
    return out


def main(batch_path):
    batch = json.load(open(os.path.join(PLUGIN, batch_path), encoding="utf-8"))
    fname = batch["file"]
    path = os.path.join(CMD_DIR, fname)
    src = open(path, encoding="utf-8", newline="").read()
    reg = load_registry()
    literal = dict(reg._LITERAL_REGEX)
    lines = src.splitlines(keepends=True)

    tree = ast.parse(src)
    edits = []          # (lineno, new_text)
    added = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        key = node.name
        if key not in batch["items"]:
            continue
        dec_rx = None
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) \
                    and dec.func.attr == "regex":
                seg = ast.get_source_segment(src, dec)
                dec_rx = (dec, seg)
        if dec_rx is None:
            raise SystemExit(f"✗ {fname}:{key} 没有 @filter.regex —— 已迁过？")
        dec, seg = dec_rx
        pat = dec.args[0].value
        if literal.get(key) != pat:
            raise SystemExit(f"✗ {fname}:{key} 装饰器字面量与字面表不等：\n  装饰器 {pat!r}\n  字面表 {literal.get(key)!r}")
        kwargs = ", ".join(f"{kw.arg}={ast.get_source_segment(src, kw.value)}"
                           for kw in dec.keywords)
        indent = lines[dec.lineno - 1][:len(lines[dec.lineno - 1]) - len(lines[dec.lineno - 1].lstrip())]
        newline_char = "\r\n" if lines[dec.lineno - 1].endswith("\r\n") else "\n"
        new = f'{indent}@declared("{key}"{", " + kwargs if kwargs else ""}){newline_char}'
        edits.append((dec.lineno, new))
        item = batch["items"][key]
        entry = {"patterns": [pat]}
        for fld in ("desc", "category", "usage"):
            if item.get(fld):
                entry[fld] = item[fld]
        g = guards_of(src, node)
        if g:
            entry["guards"] = g
        if item.get("order") is not None:
            entry["order"] = item["order"]
        if item.get("visible") is not None:
            entry["visible"] = item["visible"]
        if item.get("page_size") is not None:
            entry["page_size"] = item["page_size"]
        if item.get("note"):
            entry["extra"] = {"note": item["note"]}
        added[key] = entry

    missing = set(batch["items"]) - set(added)
    if missing:
        raise SystemExit(f"✗ 批里这些 key 在本文件里没找到：{sorted(missing)}")

    # ---- 2. 换装饰器 ----
    edits.sort()
    for lineno, new in edits:
        lines[lineno - 1] = new
    new_src = "".join(lines)

    # ---- 3. 补 import ----
    if "from ._declared import declared" not in new_src:
        # 锚点：**最后一条** `from ._platform import ...` 单行 import（同一模块可能分几行写）
        ms = list(re.finditer(r"^from \._platform import [^\n]*\n", new_src, re.M))
        anchor = ms[-1].end() if ms else 0
        ins = "\nfrom ._declared import declared\n"
        new_src = new_src[:anchor] + ins + new_src[anchor:]
        print(f"  + {fname}: 补 import `from ._declared import declared`")
    else:
        print(f"  = {fname}: import 已就位")

    # ---- 3b. 全部迁完则摘掉不再使用的 `filter` 导入（只看代码，注释里的提及不算）----
    code_only = re.sub(r"#[^\n]*", "", new_src)
    if "filter." not in code_only:
        m = re.search(r"^from \._platform import ([^\n]*)\n", new_src, re.M)
        if m and "filter" in [x.strip() for x in m.group(1).split(",")]:
            names = [x.strip() for x in m.group(1).split(",") if x.strip() != "filter"]
            new_src = (new_src[:m.start()]
                       + "from ._platform import " + ", ".join(names) + "\n"
                       + new_src[m.end():])
            print(f"  - {fname}: 摘掉不再使用的 `filter` 导入")

    if not DRY:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new_src)

    # ---- 4. 删字面表条目（连同紧贴其上的、仅属于该 key 的注释）----
    reg_lines = open(REGISTRY, encoding="utf-8", newline="").read().splitlines(keepends=True)
    # 表头注释块（紧跟 `_LITERAL_REGEX = {` 的那些注释行）：表级纪律，**永不删除**
    header_lines = set()
    for _i, _ln in enumerate(reg_lines):
        if _ln.startswith("_LITERAL_REGEX"):
            _j = _i + 1
            while _j < len(reg_lines) and reg_lines[_j].strip().startswith("#"):
                header_lines.add(reg_lines[_j])
                _j += 1
            break
    keep = []
    removed_keys, removed_notes = [], []
    seen_first_key = False
    i = 0
    while i < len(reg_lines):
        ln = reg_lines[i]
        m = re.match(r'^\s{4}"([A-Za-z_][A-Za-z0-9_]*)":\s*r?[\'"]', ln)
        if m and m.group(1) in added:
            key = m.group(1)
            # 往上回看注释块
            j = len(keep) - 1
            block = []
            while j >= 0 and keep[j].strip().startswith("#"):
                block.insert(0, keep[j])
                j -= 1
            block = [b for b in block if b not in header_lines]   # 表头保留
            note_txt = "".join(block)
            if not seen_first_key:      # 紧跟表头的第一个 key：其上只有表头
                block = []
            if block:
                del keep[len(keep) - len(block):]
                removed_notes.append((key, note_txt))
            removed_keys.append(key)
            seen_first_key = True
            i += 1
            continue
        if m:
            seen_first_key = True
        keep.append(ln)
        i += 1

    print(f"  - _registry._LITERAL_REGEX: 删 {len(removed_keys)} 条 → {sorted(removed_keys)}")
    if removed_notes:
        print(f"  - 同时删掉的注释块 {len(removed_notes)} 段（逐段核对是否已进 extra.note）：")
        for key, txt in removed_notes:
            print(f"      [{key}] {txt.strip()[:150]}")
    if not DRY:
        with open(REGISTRY, "w", encoding="utf-8", newline="") as f:
            f.write("".join(keep))

    # ---- 5. 追加声明 ----
    spec = json.load(open(SPEC, encoding="utf-8"))
    dup = set(spec) & set(added)
    if dup:
        raise SystemExit(f"✗ 声明表里已有：{sorted(dup)}")
    spec.update(added)
    if not DRY:
        with open(SPEC, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
    print(f"  + command_specs.json: 追加 {len(added)} 条 → 共 {len(spec)} 条")
    print(f"\n{'[dry-run] ' if DRY else ''}OK：{fname} 迁入 {len(added)} 条")
    return 0


if __name__ == "__main__":
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not argv:
        raise SystemExit(__doc__)
    sys.exit(main(argv[0]))
