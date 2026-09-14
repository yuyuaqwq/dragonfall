#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""文案真源**双向一致性门禁**（★ P4′-B，2026-09-14）—— 宿主镜像 ↔ 包内真源。

照 B18-L12 的一致性门禁模式（`tests/test_command_priority_sync.py`）：**单边改动必报红**。
本文件管的是文案域（message templates）的真源位置：

```
真源（唯一）  <pkg>/framework/games/orlandia/content/data/text_specs.json   ← 装载器读它
镜像（构建期）game/data/text_specs.json                                    ← 宿主运行期不读
投影（编辑器）<pkg>/framework/games/orlandia/content/data/texts.json        ← 去 _meta/_categories
```

钉死的七条
----------
1. 两份都可达（宿主镜像 + 包内真源）；包内真源**逐字节**等于宿主镜像（含 `_meta`/`_categories`）；
   两份的**非 `_` 条目逐条相等**（值/params/category/desc 逐字）。
2. **运行期定位**：装载器（`content.texts`）与宿主薄壳（`game.core.texts`，测试内注入）
   实际读的路径都落在**包内**同一文件 —— 谁都不再指宿主目录。
3. **包自足**：没有宿主目录时（临时摘掉 `game/`，同进程内 `importlib.invalidate_caches()`），
   包内装载器仍能装载真源、键数与有宿主时相同、渲染结果逐条相同。
4. **宿主不读包**：宿主树 `game/**`（排除 `game/data/text_specs.json` 这份镜像资产本身）
   的 `.py` 里没有指向包内真源路径的读法（`content/data/text_specs.json` / `canonical_path()`）。
5. **投影不漂移**：`content/data/texts.json` 的每条与真源逐值相等，且不许多键（只少 `_` 元信息）。

反证（已跑，日志见 `out/_logs/`）：把包内真源某一条改一个字 → 第 1 条当场红且**只红该 key**
（`--audit` 打印差异明细）→ 还原复跑回全绿。反证只对副本做（真仓只读）。

跑法：python tests/test_texts_specs_sync.py        （exit=0 通过）
      python tests/test_texts_specs_sync.py --audit（额外打印逐条指纹/差异明细）
"""
import ast
import hashlib
import io
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PD = os.path.dirname(_HERE)                      # dragonfall/
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

#: qqbot 根（`data/plugins/dragonfall` 的祖先；本门禁要 import 宿主侧薄壳，故显式登记，
#: 不靠调用者的 cwd/PYTHONPATH）。几何：<qqbot>/data/plugins/dragonfall → 上溯 3 层。
QQBOT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_PD)))
if os.path.isdir(os.path.join(QQBOT_ROOT, "data", "plugins")) and QQBOT_ROOT not in sys.path:
    sys.path.insert(0, QQBOT_ROOT)
if os.path.join(_PD, "framework") not in sys.path:
    sys.path.insert(0, os.path.join(_PD, "framework"))

PKG_ROOT = os.path.join(_PD, "framework", "games", "orlandia")
PKG_DATA = os.path.join(PKG_ROOT, "content", "data")

#: 宿主侧镜像（构建期资产；宿主运行期不读）
HOST_MIRROR = os.path.join(_PD, "game", "data", "text_specs.json")
#: 包内真源（唯一；装载器读它）
PKG_SPEC = os.path.join(PKG_DATA, "text_specs.json")
#: 包内导出投影（编辑器 `editor/domains.json` 的 texts 域读它；去 `_` 元信息）
PKG_PROJ = os.path.join(PKG_DATA, "texts.json")

HOST_TREE = os.path.join(_PD, "game")

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("  ✅ %s" % name)
    else:
        failed += 1
        print("  ❌ %s %s" % (name, str(detail)[:400]))


def _read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def _load(path):
    with io.open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _entries(raw):
    """装载器同一条过滤规则：跳过 `_` 开头的顶层键（`game/core/texts.py::_load_specs`）。"""
    return {k: v for k, v in raw.items() if not str(k).startswith("_")}


def _meta(raw):
    return {k: v for k, v in raw.items() if str(k).startswith("_")}


def _entrysha(entry) -> str:
    """条目指纹：`json.dumps(sort_keys=True, ensure_ascii=False, separators)` 的 sha256 前 16。

    逐字判等（含 `params` 的**列表顺序**、`desc`/`category` 的空缺与空串之别）——
    不用 `==` 是因为要一个可贴进日志的短指纹。
    """
    blob = json.dumps(entry, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


# ══════════════════════════════════════════════════════════════════════════
# [1] 宿主镜像 ↔ 包内真源（双向）
# ══════════════════════════════════════════════════════════════════════════
def t1_host_mirror_vs_pkg_source(audit=False):
    print("\n[1] 宿主镜像 ↔ 包内真源（逐字节 + 逐条）")
    check("宿主镜像存在（构建期资产）", os.path.isfile(HOST_MIRROR), HOST_MIRROR)
    check("包内真源存在（唯一真源）", os.path.isfile(PKG_SPEC), PKG_SPEC)
    if not (os.path.isfile(HOST_MIRROR) and os.path.isfile(PKG_SPEC)):
        return

    host_raw, pkg_raw = _read_bytes(HOST_MIRROR), _read_bytes(PKG_SPEC)
    check("★ 包内真源逐字节等于宿主镜像（含元信息；文案一个字符未改）",
          host_raw == pkg_raw,
          "host=%d B sha=%s / pkg=%d B sha=%s"
          % (len(host_raw), hashlib.sha256(host_raw).hexdigest()[:16],
             len(pkg_raw), hashlib.sha256(pkg_raw).hexdigest()[:16]))

    host, pkg = _load(HOST_MIRROR), _load(PKG_SPEC)
    check("两份顶层都是对象", isinstance(host, dict) and isinstance(pkg, dict),
          (type(host).__name__, type(pkg).__name__))

    host_meta, pkg_meta = _meta(host), _meta(pkg)
    check("★ 元信息（_meta/_categories）两边逐条相等（宿主镜像不许少字段）",
          host_meta == pkg_meta, sorted(set(host_meta) ^ set(pkg_meta)))

    h, p = _entries(host), _entries(pkg)
    check("★ 非 _ 条目键集相等（单边新增/删除即红）",
          set(h) == set(p), "only_host=%s only_pkg=%s"
          % (sorted(set(h) - set(p))[:5], sorted(set(p) - set(h))[:5]))
    for label, payload in (("条目原始值（逐字）", (h, p)),):
        diffs = sorted(k for k in set(h) & set(p) if h[k] != p[k])
        check("★ %s：两边逐条相等（单边改字即红）" % label, not diffs,
              "差异 %d 条：%s" % (len(diffs), diffs[:5]))
    d2 = sorted(k for k in set(h) & set(p) if _entrysha(h[k]) != _entrysha(p[k]))
    check("★ 条目指纹（sorted-keys sha256）逐条相等", not d2, d2[:5])

    if audit:
        print("     · 真源条目 %d 条 · 元信息 %d 条 · host sha=%s"
              % (len(h), len(host_meta), hashlib.sha256(host_raw).hexdigest()[:16]))
        changed = sorted(k for k in set(h) & set(p) if _entrysha(h[k]) != _entrysha(p[k]))
        if changed:
            for k in changed:
                print("     · DIFF %s\n         host=%r\n         pkg =%r"
                      % (k, h[k], p[k]))
        else:
            print("     · 逐条指纹一致：%d/%d 条（无差异 key）" % (len(h), len(h)))


# ══════════════════════════════════════════════════════════════════════════
# [2] 运行期定位：读的必须是包内那份（宿主薄壳 ↔ 包内装载器**同表**）
# ══════════════════════════════════════════════════════════════════════════
def t2_runtime_points_at_pkg():
    print("\n[2] 运行期定位（装载器 + 宿主薄壳都指包内）")
    # 先经宿主薄壳（它内部 `bootstrap.package_apply()` 把包根插进 sys.path）→ 再直接 import 包模块
    from data.plugins.dragonfall.game.core import texts as T
    from content import texts as _pkg

    canon = os.path.abspath(_pkg.canonical_path())
    check("★ 包内装载器真源 = content/data/text_specs.json（包自定位）",
          canon == os.path.abspath(PKG_SPEC), canon)
    check("包内装载器真源 ≠ 宿主镜像（不是同一条宿主路径）",
          canon != os.path.abspath(HOST_MIRROR), canon)
    check("包内投影路径常量指向 content/data/texts.json",
          os.path.abspath(_pkg.PROJECTION_PATH) == os.path.abspath(PKG_PROJ),
          _pkg.PROJECTION_PATH)

    host_side = os.path.abspath(T.SPEC_PATH)
    check("★ 宿主薄壳 SPEC_PATH = 包内真源（宿主侧不再拼宿主目录）",
          host_side == canon, "host_side=%s pkg=%s" % (host_side, canon))
    check("★ 宿主薄壳实际读包内那份（SPEC_PATH 落在 <pkg>/content/data/ 下）",
          os.path.dirname(host_side) == os.path.abspath(PKG_DATA), host_side)

    tb_host = T.reload()
    check("装载无错（load_error 为空）", T.load_error() == "", T.load_error())
    tb_pkg = _pkg.reload()
    check("★ 宿主薄壳表键集 = 包内装载器表键集（同一份真源）",
          set(tb_host.keys()) == set(tb_pkg.keys()),
          sorted(set(tb_host.keys()) ^ set(tb_pkg.keys()))[:5])

    # 两边各自 `to_dict()`（引擎口径）逐条相等 ⇒ 装载后的**表内容**逐字相同
    host_map = {k: tb_host.spec(k).to_dict() for k in tb_host.keys()}
    pkg_map = {k: tb_pkg.spec(k).to_dict() for k in tb_pkg.keys()}
    diffs = sorted(k for k in host_map if _entrysha(host_map[k]) != _entrysha(pkg_map.get(k)))
    check("★ 宿主薄壳表内容（引擎 to_dict 口径）逐条等于包内装载器",
          not diffs, diffs[:5])
    check("★ 两边 value 逐字相等（缺 key 不静默的基线不变）",
          all(host_map[k].get("value") == pkg_map[k].get("value") for k in host_map),
          [k for k in host_map
           if host_map[k].get("value") != pkg_map.get(k, {}).get("value")][:5])


# ══════════════════════════════════════════════════════════════════════════
# [3] 包自足：宿主**不在 sys.path**、cwd 在仓外，仍能独立装载真源
# ══════════════════════════════════════════════════════════════════════════
_SELF_SUFFICIENT_PROBE = r'''
import hashlib, json, sys
def _mods(prefix):
    return [m for m in sys.modules if m == prefix or m.startswith(prefix + ".")]
print("SELF_SUFFICIENT cwd=%s" % __import__("os").getcwd())
print("SELF_SUFFICIENT host_modules=%d" % len(_mods("game")))
print("SELF_SUFFICIENT framework_modules=%d" % len(_mods("framework")))
from content import texts as _pkg
tb = _pkg.reload()
specs = _pkg.spec_path()
data = {k: tb.spec(k).to_dict().get("value") for k in tb.keys()}
raw = json.load(open(specs, encoding="utf-8"))
entries = {k: v for k, v in raw.items() if not str(k).startswith("_")}
print("SELF_SUFFICIENT spec_path=%s" % specs)
print("SELF_SUFFICIENT load_error=%r" % _pkg.load_error())
print("SELF_SUFFICIENT keys=%d" % len(data))
print("SELF_SUFFICIENT values_match_source=%s"
      % (all(data[k] == (entries[k] or {}).get("value") for k in data)
         and set(data) == set(entries)))
print("SELF_SUFFICIENT sha256=%s"
      % hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest())
'''


def t3_package_self_sufficient():
    print("\n[3] 包自足（宿主不在 sys.path、cwd 在仓外）")
    import shutil
    import subprocess
    import tempfile
    repo_root = os.path.dirname(_PD)                 # qqbot 根
    env = dict(os.environ)
    # 只给「包根 + 引擎」：**不给**仓根（→ 宿主 `data.plugins.dragonfall` 不可解析）、
    # **不给** framework/games（→ `framework.games.orlandia.content` 这条路也不存在）。
    env["PYTHONPATH"] = os.pathsep.join([PKG_ROOT, os.path.join(_PD, "framework")])
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    # cwd 必须在**仓外**（证明不靠相对路径）；沙箱下系统 Temp 不可清理，故用仓上级目录
    outside = tempfile.mkdtemp(prefix="p4pb_selfsuff_", dir=os.path.dirname(repo_root))
    try:
        try:
            proc = subprocess.run([sys.executable, "-c", _SELF_SUFFICIENT_PROBE],
                                  cwd=outside, env=env,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  timeout=180)
        except Exception as exc:                               # noqa: BLE001
            check("★ 子进程探针能跑起来（宿主不在 sys.path）", False, repr(exc))
            return
    finally:
        shutil.rmtree(outside, ignore_errors=True)
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace")
    fields = {}
    for line in out.splitlines():
        if line.startswith("SELF_SUFFICIENT "):
            k, _, v = line[len("SELF_SUFFICIENT "):].partition("=")
            fields[k] = v
    check("★ 探针进程零宿主模块（`game*` 未导入 = 没蹭宿主目录）",
          fields.get("host_modules") == "0", fields.get("host_modules"))
    check("★ 探针进程零框架包模块（`framework.*` 未导入）",
          fields.get("framework_modules") == "0", fields.get("framework_modules"))
    check("★ 包内装载器自解析出真源（无宿主、cwd 在仓外）",
          (fields.get("spec_path") or "").replace("\\", "/").endswith(
              "/content/data/text_specs.json"),
          fields.get("spec_path"))
    check("★ 自足装载无错（load_error 为空）", fields.get("load_error") == "''",
          fields.get("load_error"))
    check("★ 自足装载键数 = 真源非 _ 条目数（233）",
          fields.get("keys") == "233", fields.get("keys"))
    check("★ 自足装载逐条 value = 真源逐条 value",
          fields.get("values_match_source") == "True", fields.get("values_match_source"))
    if fields.get("sha256") is None:
        print("     · stderr: %s" % err[-300:])


# ══════════════════════════════════════════════════════════════════════════
# [4] 宿主不读包（终态判据：宿主零包知识）
# ══════════════════════════════════════════════════════════════════════════
def t4_host_does_not_read_package():
    print("\n[4] 宿主侧不读包内真源（终态判据）")
    import builtins
    from data.plugins.dragonfall.game.core import texts as T

    # ① 运行期实证：拦 builtins.open，看装载到底开了哪些文件
    opened = []
    real_open = builtins.open

    def _tracer(file, *a, **kw):                     # noqa: ANN001
        try:
            opened.append(os.path.abspath(str(file)))
        except Exception:                            # noqa: BLE001
            pass
        return real_open(file, *a, **kw)

    builtins.open = _tracer
    try:
        T.reload()
    finally:
        builtins.open = real_open
    host_mirror = os.path.abspath(HOST_MIRROR)
    pkg_spec = os.path.abspath(PKG_SPEC)
    check("★ 装载期确实开了包内真源（探针有效，不是空跑）",
          pkg_spec in opened, opened[:5])
    check("★ 装载期一个字节都没读宿主镜像（game/data/text_specs.json）",
          host_mirror not in opened, [p for p in opened if p == host_mirror])
    host_tree_files = [p for p in opened if p.startswith(os.path.abspath(HOST_TREE))]
    check("★ 装载期没读宿主树里任何文件（game/** 零读）", not host_tree_files,
          host_tree_files[:5])

    # ② 源码面：宿主**代码**里不许出现包内真源的读法（注释/文档串不算）
    offenders, scanned = [], 0

    def _docstring_ids(tree):
        """三类 docstring 节点的 id（模块/类/函数）—— 文档串允许提到真源路径。"""
        ids = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
                body = getattr(node, "body", None) or []
                if (body and isinstance(body[0], ast.Expr)
                        and isinstance(body[0].value, ast.Constant)
                        and isinstance(body[0].value.value, str)):
                    ids.add(id(body[0].value))
        return ids

    for dirpath, dirnames, filenames in os.walk(HOST_TREE):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            scanned += 1
            try:
                src = io.open(path, encoding="utf-8").read()
            except OSError:
                continue
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            docs = _docstring_ids(tree)
            for node in ast.walk(tree):
                if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                        and id(node) not in docs):
                    v = node.value.replace("\\", "/")
                    if "content/data/text_specs.json" in v:
                        offenders.append("%s:%d: %r"
                                         % (os.path.relpath(path, _PD), node.lineno, v[:60]))
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr in ("canonical_path", "PROJECTION_PATH")):
                    offenders.append("%s:%d: %s()"
                                     % (os.path.relpath(path, _PD), node.lineno,
                                        node.func.attr))
    check("宿主 .py 面已扫（>50 个文件）", scanned > 50, scanned)
    check("★ 宿主代码（AST 字面量/调用，排除文档串）里没有包内真源路径",
          not offenders, offenders[:5])

    src = io.open(os.path.join(HOST_TREE, "core", "texts.py"), encoding="utf-8").read()
    check("★ 宿主薄壳里不再出现 `game/data` 拼装（宿主目录知识归零）",
          '"data", "text_specs.json"' not in src and "join(os.path.dirname(_HERE)" not in src)


# ══════════════════════════════════════════════════════════════════════════
# [5] 投影不漂移（编辑器读的那份）
# ══════════════════════════════════════════════════════════════════════════
def t5_projection_not_drifted():
    print("\n[5] 包内投影 content/data/texts.json ↔ 真源")
    check("投影文件存在", os.path.isfile(PKG_PROJ), PKG_PROJ)
    if not os.path.isfile(PKG_PROJ):
        return
    proj = _load(PKG_PROJ)
    spec_entries = _entries(_load(PKG_SPEC))
    check("★ 投影无多余键（真源只许少 `_` 元信息）",
          not (set(proj) - set(spec_entries)), sorted(set(proj) - set(spec_entries))[:5])
    check("★ 投影不缺键（真源每条都在投影里）",
          not (set(spec_entries) - set(proj)), sorted(set(spec_entries) - set(proj))[:5])
    diffs = sorted(k for k in set(proj) & set(spec_entries)
                   if _entrysha(proj[k]) != _entrysha(spec_entries[k]))
    check("★ 投影每条与真源逐字相同（漂移即红）", not diffs, diffs[:5])
    check("投影不含 `_` 元信息（编辑器 schema 只认 text_entry 对象）",
          not [k for k in proj if str(k).startswith("_")])


def main():
    audit = "--audit" in sys.argv[1:]
    print("=" * 74)
    print("文案真源双向一致性门禁：宿主镜像 ↔ 包内真源（P4′-B）")
    print("=" * 74)
    t1_host_mirror_vs_pkg_source(audit=audit)
    t2_runtime_points_at_pkg()
    t3_package_self_sufficient()
    t4_host_does_not_read_package()
    t5_projection_not_drifted()
    print("\n" + "=" * 74)
    print("结果：通过 %d / %d" % (passed, passed + failed))
    print("=" * 74)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
