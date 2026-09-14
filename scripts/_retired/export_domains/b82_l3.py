# -*- coding: utf-8 -*-
"""对话动作域（`talk_actions`）导出器 —— B8.2 线3（2026-09-13）。

本文件 = `export_game_package.py` 的**域插件**（契约见 `scripts/export_domains/README.md`）：
暴露 `DOMAINS = {域: 派生函数}` 即被宿主自动并入注册表 → 不必改那个 2,900 行的宿主文件。

================================================================================
真源认定（父任务点名要认的那张「对话动作表」）
================================================================================
`game/commands/talk_actions.py` 的 **`ACTIONS` 注册表** = 「一条 = 一个对话动作」的
**声明表**（键 = 对话树 `option.action` 里那个动作键），而每个键的**值是函数**（实现 = 逻辑）。
两者分家（B8.2 线3 薄壳化后）：

    · **声明（哪些键存在 + 注册序）** 仍只有一处：`game/commands/talk_actions.py` 的
      18 个 `@register("…")`（真源 = 游戏仓；本域按它出条目与键序）。
    · **实现（函数体）** 已搬进内容包 `content/talk_actions.py`（逐字端口）——函数体进不了
      JSON，故本域把实现投影成 `impl` 字段（包内模块.函数名）。

为什么不是 `game/data/` 某张表：对话动作**从来没有**数据表 —— 是注册表 + 函数
（与 `core/dialogue_conds.py:CONDITIONS`（对话条件）、`core/event_templates.py:TEMPLATES`
（事件模板）同构；本域与 `event_templates` 域取同一投影手法：一条 = 一个注册键 + 实现坐标）。

判定依据（为什么它算「表」而不是纯逻辑，值得开一个域）
------------------------------------------------------
`dialogues` 域（B3）里每个选项的 `action` dict 的**键**就是本域的键：
`game/data/dialogues.py` 实测 **294 个选项**带 `action`，其中 **18 个不同键**，
与注册表 18 个键**完全相等**（本函数做这条闭合校验，缺一个就 raise）。
⇒ 「动作键」是内容侧的**引用词汇**，没有本域它在编辑器里没有落点（点不开的引用）。

条目形状（一条 = 一个动作键）
----------------------------
    func : 注册函数名（实测恒为 `action_<键>`，仍从源读出，不靠命名约定）
    line : 该 `def` 的行号（1 基；便于人回查真源）
    async: 是否 `async def`（消费端 `world._apply_talk_action` 据此 await；同步版跳过）
    doc  : 规则说明 —— ① 壳内 docstring（有则用）；② 否则取**包内实现**的同位说明
           （函数 docstring，若无则取 `def` 上方连续 `#` 注释块，多行 `\\n` 连接）
    impl : 包内实现坐标 `<包内模块>.<函数名>`（由壳内 `return <alias>.<name>(…)` 反查；
           反查不到 → 空串，不猜）

自检（拒绝导出坏表）
--------------------
  1. 注册表非空、键非空唯一、`func` 非空、`line` > 0；
  2. 数据闭合：`dialogues` 域全部选项 `action` 键 ⊆ 本表键（否则 `check_action_keys`
     会在运行期告警/测试里 raise —— 数据笔误在导出期就红）；
  3. **包内注册表 == 壳内注册表**（键集**与键序**逐条相等）：两处都记 `ACTIONS`，
     漂移 = 玩家能点到但执行不了的选项（静默），所以在这里 raise；
  4. 实现反查（`impl`）在 18 条上必须全部命中（本批实测 18/18；改壳写法会让它空 → 红）。

为什么用 AST 而不是 import 这个命令模块
--------------------------------------
导入 `game.commands.talk_actions` 会拉起宿主链（`..db` 起 sqlite、`..bootstrap` 加载内容包、
`..log_setup` 起日志），导出器是**离线只读工具**（`--check` 要能逐字节复现）。AST 读的是
同一条声明（`@register` 装饰器），零副作用、零环境依赖。`game/data/dialogues.py` 走正常
`import_game_data`（纯数据模块，与其它域一致）。

实测（2026-09-13，本机；条数 = 导出后包内条数）
---------------------------------------------
    talk_actions  18 条（= `ACTIONS` 18 个注册键；`dialogues` 294 个选项引用其中 18 个键）
                  实现反查 18/18；doc 13/18 非空（空说明的 5 条 = `set_flag`/`open_shop`/
                  `hint`/`consume_item`/`unlock_prof` —— 源侧本来就没写说明，
                  导出期**不替它编文案**）
"""
import ast
import io
import os

from _helpers import REPO_ROOT, import_game_data, sort_table

__all__ = ["DOMAINS"]

# 壳（声明真源）/ 包内实现（坐标来源）
_SHELL_REL = os.path.join("game", "commands", "talk_actions.py")
_PKG_REL = os.path.join("content", "talk_actions.py")
_FW_DEFAULT = "C:/Users/yuyu/framework-engine"
_PKG_ID = "orlandia"


def _fw_dir() -> str:
    """框架（交付）仓根 —— 与 `export_game_package.py` 同口径。"""
    return os.path.abspath(os.environ.get("GWEN_FRAMEWORK_DIR") or _FW_DEFAULT)


def _read_src(path: str) -> str:
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def _registry(path: str, what: str):
    """AST 读 `@register("键")` 注册表 → [(键, 函数名, 行号, 是否 async, 转发目标或 None)]。

    转发目标 = 函数体里**唯一**一个 `return <X>.<name>(…)` 的属性名（`X` = 模块别名）。
    """
    tree = ast.parse(_read_src(path))
    out = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        key = None
        for dec in node.decorator_list:
            if (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name)
                    and dec.func.id == "register" and dec.args
                    and isinstance(dec.args[0], ast.Constant)
                    and isinstance(dec.args[0].value, str)):
                key = dec.args[0].value
        if key is None:
            continue
        target = None
        body = [n for n in node.body if not (isinstance(n, ast.Expr)
                                             and isinstance(n.value, ast.Constant))]
        if len(body) == 1 and isinstance(body[0], ast.Return):
            val = body[0].value
            if isinstance(val, ast.Await):                     # async 壳：await X.f(...)
                val = val.value
            if isinstance(val, ast.Call) and isinstance(val.func, ast.Attribute):
                target = val.func.attr
        if not key:
            raise ValueError("%s：%s 的 @register 键不是非空字符串 —— 拒绝导出" % (what, node.name))
        out.append((key, node.name, int(node.lineno), isinstance(node, ast.AsyncFunctionDef), target))
    if not out:
        raise ValueError("%s：读不到任何 @register(...) 注册 —— 源形状变了，拒绝导出" % what)
    return out


def _alias_modules(path: str) -> dict:
    """`from content import talk_actions as _TA` → {"_TA": "content.talk_actions"}。"""
    tree = ast.parse(_read_src(path))
    out = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            for a in node.names:
                if a.asname:
                    out[a.asname] = "%s.%s" % (node.module, a.name)
    return out


def _impl_notes(pkg_path: str) -> dict:
    """包内实现 → {函数名: 规则说明}（docstring 优先；否则 `def` 上方连续 `#` 注释块）。"""
    src = _read_src(pkg_path)
    tree = ast.parse(src)
    lines = src.splitlines()
    out = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        doc = ast.get_docstring(node, clean=True)
        if doc:
            out[node.name] = doc
            continue
        # 说明候选：① 函数体开头连续注释（本仓习惯：规则写在语句前）② `def` 上方连续注释
        note = _comment_block(lines, node.body[0].lineno - 2, up=True) or \
            _comment_block(lines, min([d.lineno for d in node.decorator_list]
                                      + [node.lineno]) - 2, up=True)
        if note:
            out[node.name] = note
    return out


def _comment_block(lines, idx: int, up: bool = True) -> str:
    """从 `idx`（0 基）向上取连续 `#` 注释行 → 归一化文本（去 `#`、去首尾空行）。"""
    buf = []
    i = idx
    while i >= 0:
        ln = lines[i].strip()
        if ln.startswith("#"):
            buf.append(ln.lstrip("#").strip())
            i -= 1
        elif not ln and buf:
            break
        elif not ln:
            i -= 1
        else:
            break
    return "\n".join(reversed(buf)).strip()


def _dialogue_action_keys(src_root: str) -> set:
    """`game/data/dialogues.py` 里全部选项 `action` 的键（递归走完整棵树）。"""
    mod = import_game_data("dialogues", src_root)
    tbl = getattr(mod, "DIALOGUES", None)
    if not isinstance(tbl, dict) or not tbl:
        raise ValueError("talk_actions：game/data/dialogues.py DIALOGUES 不是非空 dict —— 拒绝导出")
    keys = set()

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "action" and isinstance(v, dict):
                    keys.update(str(x) for x in v)
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(tbl)
    return keys


def derive_talk_actions(src_root: str = None) -> dict:
    """对话动作域（`talk_actions`）：`game/commands/talk_actions.py` 的 `ACTIONS` 注册表（18 条）。

    真源 / 形状 / 判定依据 / 自检 —— 全在**本模块文件头**（含为什么 AST 而不是 import）。
    条目 = `{func, line, async, doc, impl}`（见文件头「条目形状」）。
    """
    root = src_root or REPO_ROOT
    shell_path = os.path.join(root, _SHELL_REL)
    if not os.path.isfile(shell_path):
        raise ValueError("talk_actions：壳 %s 不在 —— 源形状变了，拒绝导出" % shell_path)
    reg = _registry(shell_path, "talk_actions 壳注册表")

    # 包内实现（坐标 + 说明）：交付仓那份
    pkg_path = os.path.join(_fw_dir(), "games", _PKG_ID, _PKG_REL)
    if not os.path.isfile(pkg_path):
        raise ValueError(
            "talk_actions：包内实现 %s 不在 —— 键的**实现坐标**没有落点（B8.2 线3 起实现正文"
            "在包内），拒绝导出（用 --out/GWEN_FRAMEWORK_DIR 指到含本次交付的框架仓）" % pkg_path)
    pkg_reg = _registry(pkg_path, "talk_actions 包内注册表")
    impl_notes = _impl_notes(pkg_path)
    alias = _alias_modules(shell_path)

    # ③ 包内注册表 == 壳内注册表（键集 + 键序；漂移 = 玩家点得到但执行不了的选项，静默）
    if [r[0] for r in pkg_reg] != [r[0] for r in reg]:
        raise ValueError(
            "talk_actions：壳注册表与包内注册表不一致（壳 %s / 包 %s）—— 两处都记 ACTIONS，"
            "漂移必须在这里红，拒绝导出" % ([r[0] for r in reg], [r[0] for r in pkg_reg]))

    # ② 数据闭合：dialogues 选项的 action 键 ⊆ 本表键
    used = _dialogue_action_keys(root)
    have = {r[0] for r in reg}
    unknown = sorted(used - have)
    if unknown:
        raise ValueError(
            "talk_actions：dialogues 里这些 action 键没有注册实现：%s —— 运行期 "
            "check_action_keys 会告警（测试环境直接 raise），拒绝导出" % (unknown,))

    out = {}
    for key, func, line, is_async, target in reg:
        entry = {
            "func": func,
            "line": int(line),
            "async": bool(is_async),
            "doc": "",
            "impl": "",
        }
        if target:
            # 壳内 docstring 优先；否则取包内实现的同位说明
            entry["doc"] = _doc_of(shell_path, func) or impl_notes.get(target, "")
            mod = alias.get(_impl_alias(shell_path, func), "")
            entry["impl"] = "%s.%s" % (mod, target) if mod else target
        else:
            entry["doc"] = _doc_of(shell_path, func)
        if not entry["func"] or entry["line"] <= 0:
            raise ValueError("talk_actions：%r 的 func/line 不对（%r/%r）—— 拒绝导出"
                             % (key, entry["func"], entry["line"]))
        if not entry["impl"]:
            raise ValueError("talk_actions：%r 的实现坐标反查不到（壳写法变了？）—— 拒绝导出" % key)
        out[key] = entry
    return sort_table(out)


def _doc_of(path: str, func: str) -> str:
    """读某个函数自己的 docstring（归一化；无则空串）。"""
    for node in ast.parse(_read_src(path)).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func:
            return ast.get_docstring(node, clean=True) or ""
    return ""


def _impl_alias(path: str, func: str) -> str:
    """读某函数体里 `return <别名>.name(…)` 的别名（用于把 `impl` 拼成模块全路径）。"""
    for node in ast.parse(_read_src(path)).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func:
            body = [n for n in node.body if not (isinstance(n, ast.Expr)
                                                 and isinstance(n.value, ast.Constant))]
            if len(body) == 1 and isinstance(body[0], ast.Return):
                val = body[0].value
                if isinstance(val, ast.Await):
                    val = val.value
                if isinstance(val, ast.Call) and isinstance(val.func, ast.Attribute) \
                        and isinstance(val.func.value, ast.Name):
                    return val.func.value.id
    return ""


DOMAINS = {
    "talk_actions": derive_talk_actions,
}
