# -*- coding: utf-8 -*-
"""PATCHAUDIT ④ 常驻哨兵：宿主壳改写「静默 no-op」扫描（tests/test_patch_surface.py）。

## 为什么需要它

B1/B2 把大量实现从宿主壳搬进内容包。实现的**命名空间变了**，但测试里"改写宿主属性来控制
行为"的写法没变。两类壳必须分清：

  · **别名壳**（`_sys.modules[__name__] = 包内实现模块`）
      → 宿主模块名与包内实现是**同一个模块对象** ⇒ 改写宿主属性 == 改实现 ⇒ **有效**
  · **拷贝壳**（`X = _pkg.X` / `from content.x import y`）
      → 宿主模块命名空间与包内实现是**两份** ⇒ 改宿主命名空间，包内实现读自己的全局
      ⇒ **静默 no-op**（不报错、只是不受控）—— 最坏的一类，因为测试会"假绿/夜间偶红"

本哨兵扫 `tests/**`（含 conftest），把每条对**宿主名字**的改写逐条判定：
  · 有效（别名壳 / 宿主自带实现 / 惰性桥）→ 放行
  · **静默 no-op** → 报红，unless 在 `WHITELIST` 里显式登记（必须写理由）
  · 新增的未登记命中 → 报红（防"新写一个失效改写"悄悄进来）

## 有牙自证

`--self-test` / 模块级 `_self_test()`：在**内存副本**里注入一条已知失效改写
（`game.core.rule_engine._is_time = …`，实现已在包内且桥不自指到宿主）→ 必须报红；
再注入一条已知有效改写（`game.core.wild.current_period = …`，别名壳）→ 必须不报红。

用法：
    python tests/test_patch_surface.py            # 正常门禁（exit=0 通过）
    python tests/test_patch_surface.py --self-test  # 反证自检（必须自己报红一次）
"""
from __future__ import annotations

import ast
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(HERE)
HOST_PREFIX = "data.plugins.dragonfall."
PROBE_VALUE = object()


def _bootstrap_paths() -> None:
    """按 conftest 的口径摆好 sys.path 并装配内容包（否则 `import game.*` 解析不到）。"""
    qqbot = os.path.dirname(os.path.dirname(os.path.dirname(PLUGIN_DIR)))
    for p in (HERE, qqbot, PLUGIN_DIR, os.path.join(PLUGIN_DIR, "framework")):
        if p not in sys.path:
            sys.path.insert(0, p)
    os.environ.setdefault("GWEN_TEST_MODE", "1")
    if os.path.isdir(os.path.join(HERE, "shim_astrbot")):
        sh = os.path.join(HERE, "shim_astrbot")
        if sh not in sys.path:
            sys.path.insert(0, sh)
    try:
        from data.plugins.dragonfall.game import bootstrap as _bst  # noqa: PLC0415
        _bst.package_apply()
    except Exception:                               # noqa: BLE001
        try:
            from game import bootstrap as _bst2        # noqa: PLC0415
            _bst2.package_apply()
        except Exception:                           # noqa: BLE001
            pass


_bootstrap_paths()

# ---------------------------------------------------------------- 显式白名单
# 每条：key = "<相对 tests 的文件>:<目标模块>::<目标名>"（目标模块已归一去掉 data.plugins.dragonfall.）
# value = 理由（必填，空理由视为未登记）
WHITELIST: dict[str, str] = {
    # 留空 = 当前仓零豁免。新增豁免必须写明「为什么这条改写对已进包单元是安全的」。
}


def _norm(mod: str) -> str:
    return mod[len(HOST_PREFIX):] if mod.startswith(HOST_PREFIX) else mod


def _is_host_module(dotted: str) -> bool:
    return bool(dotted) and (dotted == "game" or dotted.startswith("game.")
                             or dotted.startswith("data.plugins.dragonfall"))


def _dotted(node) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


class _Aliases(ast.NodeVisitor):
    def __init__(self):
        self.a: dict[str, str] = {}

    def visit_Import(self, node):
        for n in node.names:
            self.a[n.asname or n.name.split(".")[0]] = n.name if n.asname else n.name.split(".")[0]

    def visit_ImportFrom(self, node):
        m = ("." * node.level) + (node.module or "")
        for n in node.names:
            self.a[n.asname or n.name] = f"{m}.{n.name}"


class _Scan(ast.NodeVisitor):
    """收集「对宿主名字的改写」：monkeypatch.setattr / setattr / 直接赋值 模块.属性。"""

    def __init__(self, rel: str, aliases: dict, src: str):
        self.rel, self.a, self.src = rel, aliases, src
        self.hits: list[dict] = []

    def _resolve(self, node) -> str | None:
        d = _dotted(node)
        if d is None:
            return None
        head, _, rest = d.partition(".")
        base = self.a.get(head)
        return (base + ("." + rest if rest else "")) if base else d

    def visit_Call(self, node):
        fn = _dotted(node.func)
        if fn in ("monkeypatch.setattr", "setattr") and len(node.args) >= 3:
            tgt, nm = node.args[0], node.args[1]
            if isinstance(tgt, ast.Constant) and isinstance(tgt.value, str):
                mod = tgt.value
                name = nm.value if isinstance(nm, ast.Constant) else None
            else:
                mod = self._resolve(tgt)
                name = nm.value if isinstance(nm, ast.Constant) else None
            if mod and _is_host_module(mod):
                self.hits.append({"rel": self.rel, "line": node.lineno,
                                  "module": _norm(mod), "name": name,
                                  "src": self.src.splitlines()[node.lineno - 1].strip()})
        self.generic_visit(node)

    def _assign(self, target, node):
        if not isinstance(target, ast.Attribute):
            return
        mod = self._resolve(target.value)
        if mod and _is_host_module(mod):
            self.hits.append({"rel": self.rel, "line": node.lineno,
                              "module": _norm(mod), "name": target.attr,
                              "src": self.src.splitlines()[node.lineno - 1].strip()})

    def visit_Assign(self, node):
        for t in node.targets:
            self._assign(t, node)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        self._assign(node.target, node)
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        self._assign(node.target, node)
        self.generic_visit(node)


def scan_tree(tests_dir: str) -> list[dict]:
    hits = []
    for r, dirs, files in os.walk(tests_dir):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".pytest_cache",
                                                "shim_astrbot", ".run_all_workers")
                   and not d.startswith(".run_all_workers")]
        for f in sorted(files):
            if not f.endswith(".py"):
                continue
            p = os.path.join(r, f)
            rel = os.path.relpath(p, tests_dir).replace("\\", "/")
            try:
                src = open(p, encoding="utf-8-sig").read()
                tree = ast.parse(src, filename=p)
            except (OSError, SyntaxError):
                continue
            al = _Aliases()
            al.visit(tree)
            sc = _Scan(rel, al.a, src)
            sc.visit(tree)
            hits += sc.hits
    return hits


# ---------------------------------------------------------------- 判定
def _module(dotted: str):
    """解析模块：先试原样，再试带插件前缀；最后在已加载 sys.modules 里按后缀找。"""
    tried = []
    for cand in (dotted, HOST_PREFIX + dotted):
        tried.append(cand)
        try:
            return importlib.import_module(cand), None
        except Exception as e:                      # noqa: BLE001
            err = f"{type(e).__name__}: {e}"
    suf = "." + dotted
    for nm, m in list(sys.modules.items()):
        if nm == dotted or nm.endswith(suf):
            return m, None
    return None, err


def classify(hit: dict) -> tuple[str, str]:
    """返回 (verdict, evidence)。

    verdict ∈ {"effective_alias", "effective_host_native", "effective_bridge",
               "dead_noop", "unknown"}
    """
    mod_name = hit["module"]
    name = hit["name"]
    # 类形态 game.commands.instance.InstanceCmds → 拆出模块与类名
    cls = None
    m, err = _module(mod_name)
    if m is None and "." in mod_name:
        head, _, tail = mod_name.rpartition(".")
        m2, err2 = _module(head)
        if m2 is not None:
            cls = tail
            m, err, mod_name = m2, None, head
        else:
            return "unknown", f"import 失败 {mod_name}: {err}"
    if m is None:
        return "unknown", f"import 失败 {mod_name}: {err}"

    real = getattr(m, "__name__", mod_name)
    f = getattr(m, "__file__", "") or ""
    in_pkg = os.path.normcase(os.path.join(PLUGIN_DIR, "framework", "games", "orlandia")) \
        in os.path.normcase(os.path.abspath(f))

    # 1) 别名壳：宿主模块被自替换成包内实现模块 ⇒ 同一对象 ⇒ 有效
    if real != mod_name or in_pkg:
        return "effective_alias", f"宿主名 == 包内实现模块对象（__name__={real}）"

    if cls is not None:
        # 类改写：宿主壳自己定义的类 = 宿主自带实现 ⇒ 有效；否则存疑交人工
        if getattr(m, cls, None) is not None:
            return "effective_host_native", f"{mod_name}.{cls} 由宿主壳定义"
        return "unknown", f"{mod_name} 无类 {cls}"

    if name is None:
        return "unknown", "动态属性名（非字面量）无法静态判定"

    # 2) 未进包（宿主就是实现本体）⇒ 有效
    pkg_tail = mod_name.split(".")[-1]
    pkg_candidates = [f"content.{pkg_tail}"]
    pkg_impl = None
    for c in pkg_candidates:
        pmm, _ = _module(c)
        if pmm is not None:
            pkg_impl = (c, pmm)
            break
    if pkg_impl is None:
        return "effective_host_native", f"包内无同名实现（{pkg_candidates}）⇒ 宿主即实现"

    # 3) 进了包：看包内实现有没有「经宿主命名空间取件」的读点
    cname, cpkg = pkg_impl
    # 3a) 包内模块里直接对宿主模块的取件（`import game.x` / `game.x.name` / importlib 拉宿主）
    try:
        csrc = open(cpkg.__file__, encoding="utf-8").read()
    except OSError:
        csrc = ""
    host_refs = [ln for ln in csrc.splitlines()
                 if ("import game" in ln or "from game" in ln
                     or "data.plugins.dragonfall" in ln)]
    # 3b) 惰性桥函数（_src/_host_attr/取件 lambda）也吃宿主命名空间
    has_lazy_bridge = ("_HOST_ATTR" in csrc or "_src(" in csrc or "_host_attr" in csrc
                       or "bind_spec_path" in csrc or "_HostMod" in csrc
                       or "_HostAttr" in csrc)
    # 3c) 宿主壳是否把取件绑成「调用时求值」的 lambda（如 texts.bind_spec_path）
    host_src = ""
    if f and os.path.exists(f):
        try:
            host_src = open(f, encoding="utf-8").read()
        except OSError:
            pass
    host_call_time = ("lambda: " + name) in host_src or ("source=lambda" in host_src)

    if has_lazy_bridge or host_call_time:
        return "effective_bridge", "包内实现经惰性桥/调用时取件读宿主命名空间"
    if host_refs:
        return "effective_bridge", f"包内实现有宿主取件行（{host_refs[0].strip()[:60]}）"

    # 4) 既进了包、包内又自持该名字 ⇒ 宿主改写是静默 no-op
    #    双重确认：包内实现里确实有这个全局名（否则是"名字只存在于宿主"的另一类）
    if name in vars(cpkg) or any(name in ln for ln in csrc.splitlines()):
        return "dead_noop", (f"实现已进包 {cname}，包内自持 `{name}`，"
                             f"宿主壳改写只在宿主命名空间 ⇒ 静默 no-op")
    return "effective_host_native", f"包内 {cname} 无 `{name}` 读点（宿主自用）"


def run(tests_dir: str, verbose: bool = True) -> tuple[int, list[dict], list[dict]]:
    hits = scan_tree(tests_dir)
    bad, unlisted = [], []
    for h in hits:
        key = f"{h['rel']}:{h['module']}::{h['name']}"
        verdict, ev = classify(h)
        h["verdict"], h["evidence"], h["key"] = verdict, ev, key
        if verdict == "dead_noop":
            if key in WHITELIST and WHITELIST[key].strip():
                h["whitelisted"] = True
            else:
                bad.append(h)
        elif verdict == "unknown":
            unlisted.append(h)
    if verbose:
        print(f"扫描 tests/：命中宿主壳改写 {len(hits)} 条")
        from collections import Counter
        print("判定分布:", dict(Counter(h["verdict"] for h in hits)))
        for h in hits:
            print(f"  [{h['verdict']:>22}] {h['key']}  @{h['rel']}:{h['line']}")
            print(f"        {h['evidence']}")
        print()
    return len(hits), bad, unlisted


# ---------------------------------------------------------------- 有牙自证
def _self_test(tests_dir: str) -> int:
    """反证：合成一条已知失效改写 + 一条已知有效改写，验证判定正确。"""
    print("=" * 74)
    print("PATCHAUDIT 哨兵自检（有牙反证 / 不误报）")
    print("=" * 74)
    fails = 0
    # 已知失效：rule_engine 实现在包内且不自指宿主
    dead = {"rel": "<synth>", "line": 0, "module": "game.core.rule_engine",
            "name": "_is_time", "src": "RE._is_time = lambda span: span == 'day'"}
    v, ev = classify(dead)
    ok = (v == "dead_noop")
    print(f"  {'✅' if ok else '❌'} 合成失效改写（rule_engine._is_time）→ {v}  {ev}")
    fails += 0 if ok else 1
    # 已知有效：wild 是别名壳
    live = {"rel": "<synth>", "line": 0, "module": "game.core.wild",
            "name": "current_period", "src": "W.current_period = lambda: 'day'"}
    v2, ev2 = classify(live)
    ok2 = (v2 == "effective_alias")
    print(f"  {'✅' if ok2 else '❌'} 合成有效改写（wild.current_period）→ {v2}  {ev2}")
    fails += 0 if ok2 else 1
    # 不误报：宿主自带实现（bootstrap.package_apply）
    nat = {"rel": "<synth>", "line": 0, "module": "game.bootstrap",
           "name": "package_apply", "src": "BST.package_apply = f"}
    v3, ev3 = classify(nat)
    ok3 = (v3 != "dead_noop")
    print(f"  {'✅' if ok3 else '❌'} 宿主自带实现（bootstrap.package_apply）→ {v3}  {ev3}")
    fails += 0 if ok3 else 1
    print(f"\n自检结果: {'通过' if not fails else f'{fails} 项失败'}")
    return 0 if not fails else 1


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    print("=" * 74)
    print("PATCHAUDIT 哨兵：测试对「已进包宿主壳」的改写是否还有效")
    print("=" * 74)
    tests_dir = HERE
    total, bad, unlisted = run(tests_dir)

    if "--self-test" in argv:
        return _self_test(tests_dir)

    print("=" * 74)
    if bad or unlisted:
        if bad:
            print(f"❌ 失效改写（静默 no-op）{len(bad)} 条：")
            for h in bad:
                print(f"    {h['key']}  @{h['rel']}:{h['line']}")
                print(f"      {h['evidence']}")
                print(f"      源码: {h['src']}")
            print("    → 改测试：把改写打到**包内那个名字**（或走包内既有约定）；"
                  "确需保留请登记 WHITELIST 并写明理由。")
        if unlisted:
            print(f"⚠️ 无法静态判定 {len(unlisted)} 条（需人工确认/登记）：")
            for h in unlisted:
                print(f"    {h['key']}  @{h['rel']}:{h['line']}  {h['evidence']}")
        return 1
    print(f"✅ 哨兵通过：{total} 条宿主壳改写全部有效（或已登记豁免 {len(WHITELIST)} 条）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
