#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""宿主零游戏知识边界门禁（`ORLANDIA_终态执行计划.md` §6 ⑨ 的可执行版）。

原计划写的是 `overnight/check_host_boundary.py`，但该路径**从未落地**（宿主 `overnight/` 只有别线产物）。
本文件按项目惯例放进宿主 `scripts/`（与 `check_package_landings.py` / `check_domain_owner.py` 同处）。

六项判据（全部**只读**）：
  ① 宿主里禁包名与包内模块名（`orlandia` / `content.*`）—— 零包知识
  ② 宿主目录禁 SQL 字面量（CREATE TABLE / SELECT / INSERT / UPDATE / DELETE）
  ③ 宿主禁游戏业务词汇（业务分支的具体化：宿主代码里不得出现游戏域名/机制的字符串字面量）
  ④ 宿主除 `main.py` / `host/_platform.py` 外禁 import 平台 API（astrbot / aiocqhttp / …）
  ⑤ 包内模块禁 import 宿主（I2 反向依赖）
  ⑥ 宿主必须能加载任意包（同一份代码跑 orlandia 与 minimal-game 各一场）—— `--with-smoke` 时实跑

用法：
  python scripts/check_host_boundary.py            # ①~⑤（快，秒级）
  python scripts/check_host_boundary.py --with-smoke  # 再加 ⑥（跑两场，慢）
退出码：0 全绿 / 1 有违规
"""
from __future__ import annotations

import argparse
import ast
import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOST = os.path.dirname(HERE)

#: 宿主**交付面**（= §6 ① 的行数口径：顶层入口 + host/；工具面 schema/ tools/ scripts/ tests/ 不在内）
DELIVERY_TOP = ("main.py", "__init__.py")
DELIVERY_DIRS = ("host",)
#: 受 ① 约束但另有豁免面的目录（工具/验包器要按需 import 包）
TOOL_DIRS = ("schema", "tools", "scripts")

# ─────────── 白名单（每条都要有理由，别当止痛药用） ───────────
#: ① 允许出现的包名/包内名 —— 仅**注释与 docstring**里的历史说明
PKG_KNOWLEDGE_COMMENT_OK = {
    "host/shell.py",          # 「零包知识口径（本文件为何用 optional_submodule 而不是 import content.x）」
}
#: ② 允许含 SQL 的文件 —— 都是**平台面表**（不是游戏内容域）：tlog 日志 / identity_map 身份映射
SQL_ALLOW = {
    "host/tlog_db_sink.py",
    "host/_identity.py",
}
#: ④ 允许 import 平台 API 的文件
PLATFORM_API_ALLOW = {
    "main.py",
    "host/_platform.py",
    #  注册动作的**唯一落点**（P5C 结构性卡点 A 的解法）：把包内声明表接成平台 handler，
    #  必须碰平台注册表 —— 函数内惰性 `from astrbot.core.star.star_handler import ...`，
    #  且 try/except 包住（测试环境无 astrbot 时退化为本包平台面表）。
    "host/registration.py",
}
#: ③ 游戏业务词汇（宿主代码里出现即违规；含中英两式）
GAME_VOCAB = (
    # 中文域名词
    "副本", "装备", "技能", "怪物", "战斗", "掉落", "背包", "商店", "任务",
    "公会", "成就", "宠物", "坐骑", "附魔", "词条", "职业", "天赋", "符文",
    "药水", "经验值", "金币", "体力", "境界", "师门", "悬赏", "铁匠",
    # 英文标识（★ 2026-09-19 去掉过宽的 `instance` —— 它是通用英文词（for instance），
    #  且宿主里出现的形态是**契约面的可选钩子名** `_instance_battle_for`（按名探测能力口），
    #  不是游戏业务数据。中文侧「副本」已覆盖真正的业务语义。）
    "monster", "equip", "affix", "dungeon",
)
#: ③ 文件级豁免（**契约面**而非业务数据 —— 每条须写清理由）
VOCAB_FILE_ALLOW = {
    "host/tlog_setup.py": "流水接口 `attach_tlog(b, *, btype='monster', ...)`：接口表冻结的签名，"
                          "包内 `bridge.py` / `combat_cmds.py` 三处**同签名**；宿主只把它当标签"
                          "透传给引擎 sink，不识别语义 ⇒ 契约面，不是宿主藏业务数据。",
}
#: ⑤ 宿主侧模块前缀（包内模块出现即违 I2）
HOST_PREFIXES = ("game.", "game/", "data.plugins", "dragonfall")
#: 平台 API 模块前缀
PLATFORM_PREFIXES = ("astrbot", "aiocqhttp", "nonebot", "onebot", "cqhttp")

VIOL = []


def _rel(p):
    return os.path.relpath(p, HOST).replace("\\", "/")


def _delivery_files():
    out = []
    for f in DELIVERY_TOP:
        p = os.path.join(HOST, f)
        if os.path.isfile(p):
            out.append(p)
    for d in DELIVERY_DIRS:
        for dp, dn, fn in os.walk(os.path.join(HOST, d)):
            dn[:] = [x for x in dn if x not in ("__pycache__",)]
            out += [os.path.join(dp, f) for f in fn if f.endswith(".py")]
    return sorted(out)


def _strip_comments_and_docstrings(src):
    """返回 (代码行列表, docstring 文本) —— 用于把「注释/docstring 里的说明」与「真代码」分开。"""
    tree = ast.parse(src)
    docs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(node, "body", None)
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                docs.append(b[0].value.value)
    lines = []
    for l in src.split("\n"):
        s = l.strip()
        if s.startswith("#"):
            continue
        lines.append(l)
    return lines, "\n".join(docs)


def check_1_pkg_knowledge():
    print("\n=== ① 零包知识（宿主禁 `orlandia` / `content.*`）===")
    n = 0
    for p in _delivery_files():
        rel = _rel(p)
        src = io.open(p, encoding="utf-8", errors="replace").read()
        code, docs = _strip_comments_and_docstrings(src)
        for i, l in enumerate(code, 1):
            for pat in ("orlandia", "from content.", "import content"):
                if pat in l:
                    # 注释行已剔除 ⇒ 这里都是真代码；仅 docstring 说明可按文件豁免
                    if rel in PKG_KNOWLEDGE_COMMENT_OK and pat in docs:
                        continue
                    VIOL.append("① %s:%d `%s`（零包知识）" % (rel, i, pat))
                    print("  ❌ %s:%d %s" % (rel, i, l.strip()[:80]))
                    n += 1
    if not n:
        print("  ✅ 0")


def check_2_sql():
    print("\n=== ② 宿主禁 SQL 字面量 ===")
    rx = re.compile(r"\b(CREATE\s+TABLE|SELECT\s+.+\s+FROM|INSERT\s+INTO|UPDATE\s+.+\s+SET|DELETE\s+FROM)\b",
                    re.I)
    n = 0
    for p in _delivery_files():
        rel = _rel(p)
        if rel in SQL_ALLOW:
            continue
        src = io.open(p, encoding="utf-8", errors="replace").read()
        code, _ = _strip_comments_and_docstrings(src)
        for i, l in enumerate(code, 1):
            if rx.search(l):
                VIOL.append("② %s:%d SQL 字面量" % (rel, i))
                print("  ❌ %s:%d %s" % (rel, i, l.strip()[:80]))
                n += 1
    if not n:
        print("  ✅ 0（豁免：%s —— 平台面表 tlog / identity_map）" % " · ".join(sorted(SQL_ALLOW)))


def check_3_vocab():
    print("\n=== ③ 宿主禁游戏业务词汇（字符串字面量）===")
    n = 0
    for p in _delivery_files():
        rel = _rel(p)
        if rel in VOCAB_FILE_ALLOW:
            continue
        src = io.open(p, encoding="utf-8", errors="replace").read()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        #  docstring 是**说明文字**（讲「为什么这么设计」），不是玩家可见文案 ⇒ 不算违规。
        #  这一项要抓的是「宿主里藏游戏业务**数据**」，不是「不许提游戏」。
        doc_ids = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                b = getattr(node, "body", None)
                if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                        and isinstance(b[0].value.value, str):
                    doc_ids.add(id(b[0].value))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                    and id(node) not in doc_ids:
                v = node.value
                for w in GAME_VOCAB:
                    if w in v:
                        VIOL.append("③ %s:%d 含 `%s`" % (rel, node.lineno, w))
                        print("  ❌ %s:%d %r" % (rel, node.lineno, v[:70]))
                        n += 1
                        break
    if not n:
        print("  ✅ 0")


def check_4_platform_api():
    print("\n=== ④ 平台 API import（只许 main.py / host/_platform.py）===")
    n = 0
    for p in _delivery_files():
        rel = _rel(p)
        if rel in PLATFORM_API_ALLOW:
            continue
        src = io.open(p, encoding="utf-8", errors="replace").read()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module]
            for m in mods:
                if m.split(".")[0] in PLATFORM_PREFIXES:
                    VIOL.append("④ %s:%d `import %s`" % (rel, node.lineno, m))
                    print("  ❌ %s:%d import %s" % (rel, node.lineno, m))
                    n += 1
    if not n:
        print("  ✅ 0（豁免：%s）" % " · ".join(sorted(PLATFORM_API_ALLOW)))


def check_5_pkg_no_host():
    print("\n=== ⑤ 包内模块禁 import 宿主（I2）===")
    pkg = None
    for cand in (os.path.join(HOST, "framework", "games", "orlandia"),
                 os.environ.get("GWEN_PACKAGE_DIR", "")):
        if cand and os.path.isdir(os.path.join(cand, "content")):
            pkg = cand
            break
    if pkg is None:
        print("  ⚠️ 找不到包检出（跳过；设 GWEN_PACKAGE_DIR 或检查 framework/games/orlandia）")
        return
    n = 0
    for dp, dn, fn in os.walk(os.path.join(pkg, "content")):
        dn[:] = [x for x in dn if x not in ("__pycache__",)]
        for f in fn:
            if not f.endswith(".py"):
                continue
            p = os.path.join(dp, f)
            rel = _rel(p)
            src = io.open(p, encoding="utf-8", errors="replace").read()
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                mods = []
                if isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    mods = [node.module]
                for m in mods:
                    if any(m == pre or m.startswith(pre) for pre in HOST_PREFIXES):
                        VIOL.append("⑤ %s:%d `import %s`（包→宿主）" % (rel, node.lineno, m))
                        print("  ❌ %s:%d import %s" % (rel, node.lineno, m))
                        n += 1
    if not n:
        print("  ✅ 0（包 %s）" % pkg)


def check_6_smoke():
    """⑥ 宿主能加载任意包 —— **复用两侧既有测试，不重造**：
       · `orlandia`    → 包仓 `tests/test_v112_smoke_regression.py`（真跑一场，6 格）
       · `minimal-game` → 引擎 `tests/test_host_skeleton.py`（同一份宿主代码喂两个包，验「换包能跑」）

    ★ 子进程必须**显式**带 `GWEN_HOST_DIR`：包仓 `tests/_paths.py` 找不到宿主壳根时是
      **RuntimeError，不静默跳过**（2026-09-19 实测 = 一条假红：宿主就在本地，却报「平台驱动面缺失」）。
    """
    print("\n=== ⑥ 宿主能加载任意包（复用既有测试）===")
    pkg_dir = os.path.join(HOST, "framework", "games")
    pkgs = sorted(d for d in os.listdir(pkg_dir)
                  if os.path.isdir(os.path.join(pkg_dir, d)))
    print("  框架内包：%s" % ", ".join(pkgs))

    env = dict(os.environ)
    env["GWEN_HOST_DIR"] = HOST
    env.setdefault("GWEN_TEST_MODE", "1")
    env["PYTHONUTF8"] = "1"

    def _run(argv, cwd, label):
        r = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=600)
        lines = [l for l in ((r.stdout or "") + (r.stderr or "")).split("\n") if l.strip()]
        ok = r.returncode == 0
        print("  %s %s（%s）" % ("✅" if ok else "❌", label,
                                lines[-1].strip()[:70] if lines else ""))
        if not ok:                                  # 失败必须留证据，不然只知道「失败」
            for l in lines[-6:]:
                print("      | %s" % l.strip()[:110])
        return ok

    # (a) orlandia：跑包仓那份 smoke（内容侧测试真源 = 包仓 tests，T8 口径）
    pkg_repo = os.environ.get("GWEN_PACKAGE_DIR") or os.path.join(HOST, "framework", "games", "orlandia")
    smoke = os.path.join(pkg_repo, "tests", "test_v112_smoke_regression.py")
    if os.path.isfile(smoke):
        if not _run([sys.executable, smoke], pkg_repo, "`orlandia` smoke"):
            VIOL.append("⑥ orlandia 包 smoke 失败")
    else:
        print("  ⚠️ 找不到 %s（跳过 orlandia 侧）" % smoke)

    # (b) 两宿主一致性（引擎侧门禁，含 minimal-game）
    eng_tests = os.path.join(os.environ.get("GWEN_FRAMEWORK_DIR", ""), "tests")
    t = os.path.join(eng_tests, "test_host_skeleton.py")
    if os.path.isfile(t):
        if not _run([sys.executable, t], os.path.dirname(eng_tests), "两宿主一致性 / minimal-game"):
            VIOL.append("⑥ host_skeleton（两宿主一致性 / minimal-game）失败")
    else:
        print("  ⚠️ 找不到 %s（跳过引擎侧；设 GWEN_FRAMEWORK_DIR）" % t)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="同义（项目门禁惯例；本门禁自始只读）")
    ap.add_argument("--with-smoke", action="store_true", help="额外跑 ⑥（两场，慢）")
    a = ap.parse_args()

    print("=" * 74)
    print("宿主零游戏知识边界门禁（§6 ⑨）· 只读 · 宿主 = %s" % HOST)
    print("=" * 74)
    check_1_pkg_knowledge()
    check_2_sql()
    check_3_vocab()
    check_4_platform_api()
    check_5_pkg_no_host()
    if a.with_smoke:
        check_6_smoke()

    print("\n" + "-" * 74)
    if VIOL:
        print("❌ 共 %d 条违规：" % len(VIOL))
        for v in VIOL:
            print("   " + v)
        return 1
    print("✅ 边界六项全绿（①零包知识 ②无 SQL ③无游戏词汇 ④平台 API 受控 ⑤包不反依赖宿主%s）"
          % (" ⑥两包可装载" if a.with_smoke else " · ⑥未跑(--with-smoke)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
