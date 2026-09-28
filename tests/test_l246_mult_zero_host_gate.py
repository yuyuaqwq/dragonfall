# -*- coding: utf-8 -*-
"""门禁：宿主自有码的**段乘区**回落只认 `None`（审计 L246 同族 · 覆盖面缺口第三面）。

跑法
----
    python tests/test_l246_mult_zero_host_gate.py

背景：L246 族（`x.get("mult", 1.0) or 1.0` 把合法 0.0 吞成默认值）已在三处收口并各配门禁：
    · 引擎自有子树        → `framework-engine/tests/test_l246_formula_mult_zero_gate.py`（扫 >=180 文件）
    · orlandia 包         → `games/orlandia/tests/test_l246_mult_zero_whole_tree_gate.py`（扫 >=150 文件）
    · ★ 宿主自有码 / aetheran 包 —— ★ 本门禁 + 姊妹门禁各管一面（这两面此前**无常驻判据**）
前三轮门禁的扫描根一次比一次宽，但「扫到多少」是我今天扫出来的，不是判据保证的
⇒ 本门禁的价值是**把「这两面干净」从一次性结论变成常驻断言**。

★ 为什么宿主这一面要单独一支（Step 0k「先枚举全部读口」的同族）
    宿主仓 `framework/` 是**子模块检出**（引擎 + 三份包各一份），归各包/引擎的门禁管；
    本门禁**只扫宿主自有码**，故意不扫 `framework/` —— 否则「扫到 158」会给人
    「整仓都扫了」的错觉，而那 158 个文件其实连 `framework/` 一个都没进。

判定
----
[1] 静态：宿主自有码零处 `get(乘区键, 非零默认) or 非零常量`（AST 判，剔 docstring）
[2] ★ 右值也必须非零才算「吞 0」——`x or 0` 保留 0，不属本族（照抄包仓那份同一判据）
[3] 乘法读点与布尔谓词**分族**：键名白名单只收乘区键，布尔谓词形态（`or` 后跟集合/比较）
    本就不在白名单内，天然不进本族
[4] 覆盖面自证：扫到 >=150 个 .py（实测 158），**解析零失败**（解析失败会被误读成「干净」）
[5] 行为向（黑盒，不依赖被测源码）：`0.0` / `0` 不被吞 / 缺键与显式 None 才回落
[6] ★ 两向反证：临时改写一份副本里的该形态 ⇒ 本门禁必须转红；还原后复绿
"""
from __future__ import annotations

import ast
import io
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from _check import bind_check                                    # noqa: E402

FAILS: list = []
PASS = 0
check = bind_check(globals(), "PASS", "FAIL", "FAILS")

#: 乘区键白名单（与包仓 / 引擎那份**逐字一致** —— 口径不许三处各写一份）
MULT_KEYS = ("mult", "atk_mult", "hp_mult", "pct", "factor", "rate", "ratio", "scale")

#: ★ `framework` 是子模块检出（引擎 + 各包），归各仓门禁；这里**故意不扫**。
SKIP_DIRS = {"__pycache__", ".git", "data", "tests", "framework", "plugins"}
MIN_SCANNED = 150


def _doc_lines(tree):
    """docstring 整段行号（判据只对**产品码**生效，注释里提一嘴不算命中）。"""
    bad = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if ast.get_docstring(node, clean=False) is None:
                continue
            first = node.body[0]
            bad.update(range(first.lineno, (first.end_lineno or first.lineno) + 1))
    return bad


def _scan(root, rel_base=""):
    """扫一棵子树，返回 (命中列表, 已扫文件数, 解析失败列表)。"""
    hits, scanned, failed = [], 0, []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in sorted(files):
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace("\\", "/")
            src = io.open(path, encoding="utf-8").read()
            try:
                tree = ast.parse(src)
            except SyntaxError as exc:
                failed.append("%s: %s" % (rel, exc))
                continue
            scanned += 1
            bad = _doc_lines(tree)
            for node in ast.walk(tree):
                if not (isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or)
                        and len(node.values) == 2):
                    continue
                if node.lineno in bad:
                    continue
                lhs = node.values[0]
                if not (isinstance(lhs, ast.Call) and isinstance(lhs.func, ast.Attribute)
                        and lhs.func.attr == "get" and lhs.args
                        and isinstance(lhs.args[0], ast.Constant)):
                    continue
                if lhs.args[0].value not in MULT_KEYS or len(lhs.args) < 2:
                    continue
                try:
                    default = float(lhs.args[1].value)
                except (AttributeError, IndexError, TypeError, ValueError):
                    continue
                if default == 0.0:
                    continue
                # ★ 右值也必须非零：`x or 0` 保留 0（把 None 归一到 0），不是本族。
                try:
                    rhs = float(node.values[1].value)
                except (AttributeError, TypeError, ValueError):
                    rhs = None
                if rhs == 0.0:
                    continue
                hits.append("%s%s:%s" % (rel_base, rel, node.lineno))
    return hits, scanned, failed


def test_static_host_own_code():
    hits, scanned, failed = _scan(_REPO)
    check("宿主自有码全部可解析（解析失败会被误读成「干净」）", not failed,
          "解析失败 %s" % failed)
    check("宿主自有码扫到 >=%d 个 .py（覆盖面证明）" % MIN_SCANNED, scanned >= MIN_SCANNED,
          "只扫了 %s 个" % scanned)
    check("宿主自有码零处 get(乘区键, 非零) or 非零常量", not hits, "命中 %s" % hits)


def test_behavior_none_only_fallback():
    """黑盒跑「只认 None」的正确写法：合法 0 保住，缺键/None 才回落。"""
    def read(raw, default):
        v = raw.get("mult")
        return default if v is None else float(v)

    check("mult=0.0 保住 0.0（不被 or 吞成默认）", read({"mult": 0.0}, 1.0) == 0.0)
    check("mult=0 保住 0.0", read({"mult": 0}, 1.0) == 0.0)
    for m, exp in ((0.5, 0.5), (1.0, 1.0), (2.0, 2.0), (1.3, 1.3)):
        check("mult=%s 逐值不变" % m, abs(read({"mult": m}, 1.0) - exp) < 1e-9,
              "got=%s" % read({"mult": m}, 1.0))
    check("缺键回落默认值", read({}, 1.0) == 1.0)
    check("显式 None 回落默认值", read({"mult": None}, 1.0) == 1.0)


def test_counterproof_or_form_is_caught():
    """两向反证：给判据喂一份**真有本族形态**的副本 ⇒ 必须被扫出来（证明它有牙）。

    不改被测源码、不写仓内文件 —— 复制一棵小树到 tempdir 再扫。
    """
    import shutil
    import tempfile

    tmp = tempfile.mkdtemp(prefix="l246_host_counterproof_")
    try:
        os.makedirs(os.path.join(tmp, "sub"))
        with io.open(os.path.join(tmp, "sub", "bad.py"), "w", encoding="utf-8") as fh:
            fh.write("# -*- coding: utf-8 -*-\n"
                     "def f(d):\n"
                     "    return d.get('mult', 1.0) or 1.0\n")
        with io.open(os.path.join(tmp, "sub", "doc_only.py"), "w", encoding="utf-8") as fh:
            fh.write("# -*- coding: utf-8 -*-\n"
                     "def g(d):\n"
                     "    '''示例：d.get(\"mult\", 1.0) or 1.0 —— 只在文档里出现。'''\n"
                     "    return 1.0\n")
        with io.open(os.path.join(tmp, "sub", "or_zero_ok.py"), "w", encoding="utf-8") as fh:
            fh.write("# -*- coding: utf-8 -*-\n"
                     "def h(d):\n"
                     "    return d.get('pct', 0) or 0\n")
        hits, scanned, failed = _scan(tmp)
        # 不断言行号字面值（改副本的行号会随注释行漂移）—— 断言「命中哪一文件 + 恰好一处」
        check("反证：副本里的本族形态被扫出来（恰好一处、落在 bad.py）",
              len(hits) == 1 and hits[0].startswith("sub/bad.py:"), "got=%s" % hits)
        check("反证：docstring 里的同形不误报", "doc_only.py" not in "".join(hits))
        check("反证：x or 0（保留 0）不误报", "or_zero_ok.py" not in "".join(hits))
        check("反证：副本三文件全部可解析", not failed and scanned == 3,
              "scanned=%s failed=%s" % (scanned, failed))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    test_static_host_own_code()
    test_behavior_none_only_fallback()
    test_counterproof_or_form_is_caught()
    print("\nPASS=%d FAIL=%d" % (PASS, len(FAILS)))
    for f in FAILS:
        print("  FAIL:", f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
