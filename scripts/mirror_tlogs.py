#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""构建期镜像：包内 tlogs 声明表 → 宿主 `game/data/tlogs.json`（P4′-C 单源收口）。

单源口径（与 `tests/test_tlogs_single_source.py` 同一口径）
----------------------------------------------------------
    真源 = 包内 `content/data/tlogs.json`      ← 编辑器编辑的那一份（framework 仓）
    镜像 = 宿主 `game/data/tlogs.json`          ← 运行时 `game/tlog_setup.py:kinds()` 读的那一份

镜像**只能由本脚本从真源生成**，不许手改：手改 = 造第二真源（门禁 `tests/test_tlogs_single_source.py`
会对「单边改动」报红）。生成是确定性的：同一份真源 → 逐字节相同的镜像。

落盘规范（真源与镜像同款；与 framework `editor` 导出器同形）
    外层 kind 键**升序** · 条目内字段序**原样保留**（fields → desc → category）·
    `indent=2` · `ensure_ascii=False` · UTF-8 无 BOM · LF · 末尾换行

用法::

    python scripts/mirror_tlogs.py                  # 从真源重写镜像（默认仓内相对路径）
    python scripts/mirror_tlogs.py --check          # 只校验不写盘（exit=1 表示漂移）
    python scripts/mirror_tlogs.py --src A --dst B  # 显式路径（落地准备 / 沙盒演练用）

退出码：0 = 一致（--check）或写成功；1 = 漂移 / 真源不可用 / 规范不符。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(_HERE)

DEFAULT_SRC = os.path.join(PLUGIN_DIR, "framework", "games", "orlandia",
                           "content", "data", "tlogs.json")
DEFAULT_DST = os.path.join(PLUGIN_DIR, "game", "data", "tlogs.json")

MIN_KINDS = 1          # 空表 = 静默降级（编辑器 0 条 / 校验全不拦）→ 拒绝


def norm_eol(raw: bytes) -> bytes:
    """CRLF → LF（宿主仓 `core.autocrlf=true`，checkout 会把 LF 变 CRLF；比内容不比行尾）。"""
    return raw.replace(b"\r\n", b"\n")


def canonical_text(obj: dict) -> str:
    """规范落盘形：外层键升序 + 条目内字段序原样 + indent=2 + 末尾换行。"""
    if not isinstance(obj, dict):
        raise ValueError("tlogs 顶层必须是 object，实为 %s" % type(obj).__name__)
    if len(obj) < MIN_KINDS:
        raise ValueError("tlogs 真源是空表 —— 拒绝生成空镜像（空表 = 校验全不拦的静默降级）")
    return json.dumps({k: obj[k] for k in sorted(obj)}, ensure_ascii=False, indent=2) + "\n"


def read_source(path: str) -> tuple:
    """读真源 → `(raw_bytes, obj, canonical_text)`；不可读/坏 JSON/空表 → 抛。"""
    with open(path, "rb") as fh:
        raw = fh.read()
    if raw[:3] == b"\xef\xbb\xbf":
        raise ValueError("真源带 BOM：%s" % path)
    obj = json.loads(raw.decode("utf-8-sig"))
    text = canonical_text(obj)
    if norm_eol(raw) != text.encode("utf-8"):
        # 真源本身不是规范形 → 先把真源规范化（不静默：打印告警）
        print("⚠ 真源不是规范落盘形，按规范形生成镜像：%s" % path)
    return raw, obj, text


def md5(raw: bytes) -> str:
    return hashlib.md5(raw).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="tlogs 单源镜像生成/校验（P4′-C）")
    ap.add_argument("--src", default=DEFAULT_SRC, help="包内真源（默认 %s）" % DEFAULT_SRC)
    ap.add_argument("--dst", default=DEFAULT_DST, help="宿主镜像（默认 %s）" % DEFAULT_DST)
    ap.add_argument("--check", action="store_true", help="只校验，不写盘")
    args = ap.parse_args(argv)

    if not os.path.exists(args.src):
        print("❌ 真源不存在：%s" % args.src)
        return 1
    try:
        _raw, obj, text = read_source(args.src)
    except Exception as exc:                                     # noqa: BLE001
        print("❌ 真源不可用（%s）：%s" % (args.src, exc))
        return 1

    want = text.encode("utf-8")
    print("真源(包内) = %s" % args.src)
    print("  %d kind | %d B(LF) | md5 %s" % (len(obj), len(want), md5(want)))
    print("镜像(宿主) = %s" % args.dst)

    if args.check:
        if not os.path.exists(args.dst):
            print("❌ 镜像缺失 —— 单源断裂")
            return 1
        with open(args.dst, "rb") as fh:
            have = fh.read()
        same_bytes = norm_eol(have) == want
        try:
            same_obj = json.loads(have.decode("utf-8-sig")) == obj
        except Exception:                                        # noqa: BLE001
            same_obj = False
        print("  现状 %d B | md5 %s | 逐字节同 %s | 逐条同 %s"
              % (len(have), md5(have), same_bytes, same_obj))
        if not same_bytes or not same_obj:
            print("❌ 漂移：镜像 ≠ 真源（跑 `python scripts/mirror_tlogs.py` 重生成）")
            return 1
        print("✅ 一致（真源 = 镜像）")
        return 0

    old = None
    if os.path.exists(args.dst):
        with open(args.dst, "rb") as fh:
            old = fh.read()
        if norm_eol(old) == want:
            print("  已一致，无需重写 | md5 %s" % md5(old))
            return 0
    os.makedirs(os.path.dirname(args.dst), exist_ok=True)
    with open(args.dst, "wb") as fh:
        fh.write(want)
    print("  %s → %d B | md5 %s" % ("重写" if old is not None else "新建", len(want), md5(want)))
    print("✅ 镜像已从真源生成（单源）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
