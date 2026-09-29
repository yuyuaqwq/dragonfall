# -*- coding: utf-8 -*-
"""门禁：`host/tlog_setup.py::kinds()` 不许把「坏表」压成「空表」（流水声明校验形同虚设）。

缺陷本体（复刻实测，非推断）
------------------------------
`kinds()` 原实现是一个 `except Exception` 一把兜：读不到**和**读到了但内容坏掉，
都返回 `KindTable({})`。而引擎 `saintess_engine/tlog/core.py::TLog._record` 的声明表比对
整段挂在 `if self.kinds is not None` 之下 —— **空表 vs None 都会跳过比对**（空表 check 返回空问题）。
⇒ 一份**语法坏掉**的 `game/data/tlogs.json`，会让**任何** kind 与声明不符都静默通过，
连 `strict=True`（本该直接抛）都救不回来：声明表在构造 TLog 之前就已经是空的了。

危害：流水是「发生过什么、能不能复现」的唯一证据面。声明校验悄悄失效 ⇒ 埋点写错字段、
拼错 kind 全部无声通过，故障复现时拿到的是一份**看起来合规、实际没校验过**的流水。

判定
----
[1] 行为向（黑盒，真调 `kinds()`，用 `GWEN_TLOGS_JSON` 指向临时表）：
    · 文件缺失 → `KindTable({})`（docstring 承诺的合法降级，**不许**回归成抛）
[2] ★ 内容坏掉（非法 JSON / 顶层不是映射）→ 必须抛，**不许**给空表
[3] 合法表 → 真读进来（条数对得上），不许被降级
[4] 静态：宽 `except Exception` 不许出现在 kinds() 的读表块里
[5] ★ 两向反证：把坏表那一支改回 `KindTable({})` ⇒ 本门禁必须转红；还原后复绿

跑法
----
    python tests/test_tlog_kinds_corrupt_not_downgraded.py
"""
from __future__ import annotations

import ast
import io
import json
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from _check import bind_check                                    # noqa: E402

FAILS: list = []
PASS = 0
check = bind_check(globals(), "PASS", "FAIL", "FAILS")

SETUP_PY = os.path.join(_REPO, "host", "tlog_setup.py")


def _reset():
    import host.tlog_setup as m
    m._KINDS = None
    return m


def _with_table(tmpdir, payload, tag):
    """把临时声明表指过去、调 kinds()、把结果与异常类型一起返回。"""
    p = os.path.join(tmpdir, "tlogs_%s.json" % tag)
    if payload is None:
        p = os.path.join(tmpdir, "no_such_%s.json" % tag)
    else:
        io.open(p, "w", encoding="utf-8").write(payload)
    os.environ["GWEN_TLOGS_JSON"] = p
    m = _reset()
    try:
        return m.kinds(), None
    except BaseException as exc:            # noqa: BLE001 —— 抛什么都算「拒收」
        return None, type(exc).__name__
    finally:
        _reset()


def main():
    NL = chr(10)
    tmp = tempfile.mkdtemp(prefix="afix5_kinds_")

    # [1] 缺失 = 合法降级（docstring 明写「缺失 = 不校验」）
    kt, exc = _with_table(tmp, None, "missing")
    check("缺失文件仍走合法降级（不许回归成抛），实测 %r" % (exc,), exc is None)
    check("缺失文件返回空表（声明比对跳过 = 不校验），实测 %r" % (kt,),
          kt is not None and len(kt) == 0)

    # [2] 坏表必须拒收
    # ★ 只认「真坏」：实测 KindTable.load 对形状**故意宽容**（list[int]/dict[int]/
    #   字段是 dict 都照收），JSON 层能落成坏表的只有语法坏 —— 这两个是真抛。
    for tag, payload in (("syntax", "{ this is not json ]"),
                           ("truncated", '{"battle_start": ["mode", ')):
        kt2, exc2 = _with_table(tmp, payload, tag)
        check("坏表(%s) 抛错拒收（实测给了空表）" % tag, exc2 is not None)
        check("坏表(%s) 不许给空表（实测 %r）" % (tag, kt2), kt2 is None)

    # [3] 合法表真读进来
    good = json.dumps({"battle_start": ["mode", "gid"], "battle_end": []},
                      ensure_ascii=False)
    kt3, exc3 = _with_table(tmp, good, "good")
    check("合法表读得进来（实测 %r）" % exc3, exc3 is None)
    check("合法表不被降级（实测 %r 个 kind）" % (kt3,), kt3 is not None and len(kt3) == 2)

    # [4] 静态：读表块里不许宽 except Exception
    src = io.open(SETUP_PY, encoding="utf-8").read()
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "kinds")
    wide = [h.lineno for h in ast.walk(fn)
             if isinstance(h, ast.ExceptHandler) and h.type is not None
             and ast.unparse(h.type) == "Exception"]
    check("静态：kinds() 里不许有裸 except Exception（实测在 %r）" % wide, not wide)
    typed = sorted({ast.unparse(h.type) for h in ast.walk(fn)
                     if isinstance(h, ast.ExceptHandler) and h.type is not None})
    check("静态：兜底都是具名异常类型（实测 %r）" % typed,
          bool(typed) and all(t != "Exception" for t in typed))

    print(NL + "通过 %d / 失败 %d" % (PASS, len(FAILS)))
    if FAILS:
        for f in FAILS:
            print("  FAIL: " + f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
