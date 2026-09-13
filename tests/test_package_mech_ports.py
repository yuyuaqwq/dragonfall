#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""门禁：P4「逐字端口」保真 —— 包内 `content/mech/*.py` vs 游戏仓真源（双源漂移哨兵）。

跑法（系统 python 即可）：
    cd dragonfall && python tests/test_package_mech_ports.py
退出码：0 = 全绿；1 = 有红（红行点名族 / 文件 / 差异内容）。

框架仓路径：默认 `C:/Users/yuyu/framework-engine`，可用环境变量 `GWEN_FRAMEWORK_DIR` 覆盖
（与同目录 `test_export_package_sync.py` 同口径）。

为什么要有这道门禁（背景）
--------------------------
P4-D2 把游戏仓的机制代码**逐字**搬进了框架侧游戏包 `games/orlandia/content/mech/*.py`。
搬完之后两边是**双源**：真源改了、包没跟着改，运行时没有任何人会报警。本门禁就是那个哨兵。

本门禁锁什么（四类断言）
------------------------
1. **端口文件必须真存在** —— 缺文件 = 红行点名族 + 期望路径（不是「找不到就跳过」）。
2. **`@register_action("名字")` 集合逐名相等** —— 真源 AST 扫出的名字集合 == 包内端口文件的名字
   集合（两个方向都查：真源有包内无 → 漏搬；包内有真源无 → 私自加动词）。真源里没有
   `register_action` 的**装配器**端口（equip）改断言装配函数名存在（`install_ext_actions` /
   `apply_to_actor`），另 `apply_bar_procs` / `apply_cond_procs` / `apply_element_procs` /
   `apply_class_mech` / `apply_class_passives` 也逐个点名要求两端都在。
3. **参数表 deep-equal** —— `MECH_CASH` / `MECH_CFG` / `BAR_INJECT_FIELDS` / `BAR_STATE_PREFIX`
   / `REACTION_TABLE` / `ELEMENT_REACTIONS` / `WEAPON_EFFECT_DATA` / kinds 常量（`SkillKind`
   成员 + `K_*` + `_KIND_META` + `_DMG_KINDS`）从**两边源码静态读出**后逐值比较。
4. **漂移反证（防「门禁永远绿」）** —— 在 tmp 里复制一份端口目录，造 4 种「装坏」的假想端口
   （改动作名 / 删文件 / 改表值 / 改标量），断言门禁在副本上**必须报红**；随后再断言真仓
   **依然全绿**（证明前面只动了副本，没污染真源/真包）。

实现纪律（为什么不用 import）
------------------------------
真源模块**绝不 import**（会拉起 astrbot / sqlite 一整套宿主副作用，且慢）。表值用
「同文件模块级名字解析 + 静态字面量求值」读出来：`ast` 解析 → 模块级 `Assign/AnnAssign`
建名字表 → 递归折叠 `Constant/List/Tuple/Set/Dict(含 **spread)/UnaryOp/Name`。折不动
（函数调用、属性取值等）的节点退化为**源码文本**（`«expr»…`）参与比较 —— 仍能发现漂移。
本批 12 张表无需任何退化；只有 `K_*` 因真源写法是 `SkillKind.X.value` 先退化为文本，随后
**代入 SkillKind 成员求值**再比真值（求不动才退回文本比较），并另单独逐值比较枚举成员。

只读两仓；唯一写操作 = 在 `tempfile.mkdtemp()` 的副本上装坏（跑完删掉）。禁 git 操作。
"""
from __future__ import annotations

import ast
import os
import re
import shutil
import sys
import tempfile
import time

sys.dont_write_bytecode = True
try:                                                            # 中文断言消息
    sys.stdout.reconfigure(encoding="utf-8")                    # type: ignore[attr-defined]
except Exception:                                               # noqa: BLE001
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)                               # dragonfall/
DEFAULT_FRAMEWORK_DIR = "C:/Users/yuyu/framework-engine"
FW_ROOT = os.path.abspath(os.environ.get("GWEN_FRAMEWORK_DIR") or DEFAULT_FRAMEWORK_DIR)
PKG_ID = "orlandia"
PKG_ROOT = os.path.join(FW_ROOT, "games", PKG_ID)               # <pkg_root>/content/mech/*.py
MECH_REL = "content/mech"
EXPR = "«expr»"
MAX_DIFF = 3                                                    # 每条红行最多贴几处差异

# ---------------------------------------------------------------------------
# 端口清单表（真源 → 包内端口；行号 = 2026-09-13 实测）
# ---------------------------------------------------------------------------
# 族            真源文件（游戏仓）                              真源行号                          包内端口
# ------------  --------------------------------------------  --------------------------------  ---------------------------
# class_mech    game/services/class_mech_proc.py               :100-1809（39 动作 / 全 2446 行）  content/mech/class_mech.py
# equip         game/services/battle_equip_proc.py             :1083 install_ext_actions,        content/mech/equip.py
#                                                              :1133 apply_to_actor（0 动作）
# we_procs      game/services/battle_we_procs.py               :99-1436（27 动作 / 全 1484 行）  content/mech/we_procs.py
# team_procs    game/services/battle_team_procs.py             :172-768（20 动作 / 全 788 行）   content/mech/team_procs.py
# bar_procs     game/services/battle_bar_procs.py              :94-169（4 动作）:203 apply_bar   content/mech/bar_procs.py
# cond_procs    game/services/battle_cond_procs.py             :120（1 动作）:156 apply_cond       content/mech/cond_procs.py
# element_procs game/services/battle_element_procs.py          :133-272（4 动作）:296 apply_elem   content/mech/element_procs.py
# worldboss     game/services/battle_worldboss_procs.py        :27-48（1 动作；apply 未搬 :51-75） content/mech/worldboss.py
# kinds         game/data/kinds.py                             :1-120（SkillKind/K_*/_KIND_META） content/mech/kinds.py
# class_data    game/data/battle_rules.py + battle_config.py    :624 MECH_CASH / :455 MECH_CFG      content/mech/class_data.py
# element_data  game/data/battle_config.py                     :80-90 ELEMENT_REACTIONS,         content/mech/element_data.py
#                                                              :147-152 REACTION_TABLE, :142/:154
# we_data       game/data/weapon_effect_data.py + core/const   :27 WEAPON_EFFECT_DATA,           content/mech/we_data.py
#                                                              game/core/constants.py:156 ACT_TICK
# params        game/data/battle_rules.py                      :742 BAR_INJECT_FIELDS,           content/mech/params.py
#                                                              :749 BAR_STATE_PREFIX
PORTS = [
    # (族, 真源文件（单文件端口；多文件的数据端口用 None）, 真源行号说明, 包内端口文件, 装配器函数名, 动作集合是否比)
    ("class_mech", "game/services/class_mech_proc.py",
     ":100-1809（39 个动作装饰器；全文件 :1-2446）", "content/mech/class_mech.py",
     ("apply_class_mech", "apply_class_passives", "apply_class_channels"), True),
    ("equip", "game/services/battle_equip_proc.py",
     ":1083 install_ext_actions / :1133 apply_to_actor（全文件 :1-1174，0 个动作）", "content/mech/equip.py",
     ("install_ext_actions", "apply_to_actor"), True),
    ("we_procs", "game/services/battle_we_procs.py",
     ":99-1436（27 个动作；全文件 :1-1484）", "content/mech/we_procs.py", (), True),
    ("team_procs", "game/services/battle_team_procs.py",
     ":172-768（20 个动作；全文件 :1-788）", "content/mech/team_procs.py", (), True),
    ("bar_procs", "game/services/battle_bar_procs.py",
     ":94-169（4 个动作）；:203 apply_bar_procs（全文件 :1-244）", "content/mech/bar_procs.py",
     ("apply_bar_procs",), True),
    ("cond_procs", "game/services/battle_cond_procs.py",
     ":120（1 个动作）；:156 apply_cond_procs（全文件 :1-180）", "content/mech/cond_procs.py",
     ("apply_cond_procs",), True),
    ("element_procs", "game/services/battle_element_procs.py",
     ":133-272（4 个动作）；:296 apply_element_procs（全文件 :1-341）", "content/mech/element_procs.py",
     ("apply_element_procs",), True),
    ("worldboss", "game/services/battle_worldboss_procs.py",
     ":27-48（1 个动作 wb_gm_dmg_mult；apply_gm_dmg_mult :51-75 未搬，见文件头）",
     "content/mech/worldboss.py", (), True),
    ("kinds", "game/data/kinds.py", ":1-120（SkillKind / K_* / _KIND_META）",
     "content/mech/kinds.py", (), False),
    ("class_data", None, ":624 MECH_CASH / :455 MECH_CFG", "content/mech/class_data.py", (), False),
    ("element_data", None, ":80-90 ELEMENT_REACTIONS / :147-152 REACTION_TABLE / :142 / :154",
     "content/mech/element_data.py", (), False),
    ("we_data", None, ":27 WEAPON_EFFECT_DATA / game/core/constants.py:156 ACT_TICK",
     "content/mech/we_data.py", (), False),
    ("params", None, ":742 BAR_INJECT_FIELDS / :749 BAR_STATE_PREFIX", "content/mech/params.py", (), False),
]

# 参数表 deep-equal：(表名, 真源文件, 真源行号, 包内端口, 包内变量名)
TABLES = [
    ("MECH_CASH", "game/data/battle_rules.py", ":624", "content/mech/class_data.py", "MECH_CASH"),
    ("MECH_CFG", "game/data/battle_config.py", ":455", "content/mech/class_data.py", "MECH_CFG"),
    ("BAR_INJECT_FIELDS", "game/data/battle_rules.py", ":742", "content/mech/params.py", "BAR_INJECT_FIELDS"),
    ("BAR_STATE_PREFIX", "game/data/battle_rules.py", ":749", "content/mech/params.py", "BAR_STATE_PREFIX"),
    ("REACTION_TABLE", "game/data/battle_config.py", ":147", "content/mech/element_data.py", "REACTION_TABLE"),
    ("ELEMENT_REACTIONS", "game/data/battle_config.py", ":80", "content/mech/element_data.py", "ELEMENT_REACTIONS"),
    ("ELEMENT_MARKS_MAX", "game/data/battle_config.py", ":142", "content/mech/element_data.py", "ELEMENT_MARKS_MAX"),
    ("ELEMENT_SAME_CAST_EXTRA_CHARGE", "game/data/battle_config.py", ":154",
     "content/mech/element_data.py", "ELEMENT_SAME_CAST_EXTRA_CHARGE"),
    ("WEAPON_EFFECT_DATA", "game/data/weapon_effect_data.py", ":27", "content/mech/we_data.py", "WEAPON_EFFECT_DATA"),
    ("ACT_TICK", "game/core/constants.py", ":156", "content/mech/we_data.py", "ACT_TICK"),
    ("K_PHYS", "game/data/kinds.py", ":56", "content/mech/kinds.py", "K_PHYS"),
    ("K_MAGI", "game/data/kinds.py", ":57", "content/mech/kinds.py", "K_MAGI"),
    ("K_HEAL", "game/data/kinds.py", ":58", "content/mech/kinds.py", "K_HEAL"),
    ("K_BUFF", "game/data/kinds.py", ":59", "content/mech/kinds.py", "K_BUFF"),
    ("K_PASSIVE", "game/data/kinds.py", ":60", "content/mech/kinds.py", "K_PASSIVE"),
    ("K_SUMMON", "game/data/kinds.py", ":61", "content/mech/kinds.py", "K_SUMMON"),
    ("K_TRUE", "game/data/kinds.py", ":62", "content/mech/kinds.py", "K_TRUE"),
    ("K_TAUNT", "game/data/kinds.py", ":63", "content/mech/kinds.py", "K_TAUNT"),
    ("_KIND_META", "game/data/kinds.py", ":66", "content/mech/kinds.py", "_KIND_META"),
    ("_DMG_KINDS", "game/data/kinds.py", ":78", "content/mech/kinds.py", "_DMG_KINDS"),
]

# 真源里非字面量（`SkillKind.X.value`）→ 先把成员代进去求值再比；求不动才退化为文本比较
EXPR_TABLES = {"K_PHYS", "K_MAGI", "K_HEAL", "K_BUFF", "K_PASSIVE", "K_SUMMON", "K_TRUE", "K_TAUNT"}
SKILL_KIND = ("game/data/kinds.py", "content/mech/kinds.py", "SkillKind")

# 双源收敛后的「再导出」接线：这些名字必须仍从单源（params.py）再导出（防第二个副本长回来）
REEXPORTS = [
    ("content/mech/class_data.py", "BAR_INJECT_FIELDS", "params"),
    ("content/mech/class_data.py", "BAR_STATE_PREFIX", "params"),
    ("content/mech/element_data.py", "BAR_INJECT_FIELDS", "params"),
]


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------
def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _p(*parts: str) -> str:
    return os.path.join(*[p.replace("/", os.sep) for p in parts])


def _is_reg(fn) -> bool:
    return ((isinstance(fn, ast.Name) and fn.id == "register_action")
            or (isinstance(fn, ast.Attribute) and fn.attr == "register_action"))


class ModView:
    """一个 .py 的静态视图：模块级赋值 + 顶层 def/class + @register_action 名字。永不 import。"""

    def __init__(self, path: str):
        self.path = path
        self.tree = ast.parse(_read(path), filename=path)
        self.assigns: dict = {}
        self.defs: set = set()
        self.actions: list = []
        self.nonliteral: list = []
        for node in self.tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.defs.add(node.name)
            tgts = []
            if isinstance(node, ast.Assign):
                tgts = node.targets
            elif isinstance(node, ast.AnnAssign):
                tgts = [node.target]
            for t in tgts:
                if isinstance(t, ast.Name):
                    self.assigns[t.id] = node.value
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and _is_reg(node.func):
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    self.actions.append(node.args[0].value)
                else:
                    self.nonliteral.append(node.lineno)
        self.actions = sorted(set(self.actions))

    # ---- 静态求值 ----
    def value(self, name: str):
        if name not in self.assigns:
            return "«missing»"
        return self._conv(self.assigns[name], 0)

    def _conv(self, node, depth: int):
        if depth > 12:
            return EXPR + "<深>"
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, (ast.List, ast.Tuple)):
            items = [self._conv(e, depth) for e in node.elts]
            return items if isinstance(node, ast.List) else tuple(items)
        if isinstance(node, ast.Set):
            return frozenset(self._conv(e, depth) for e in node.elts)
        if isinstance(node, ast.Dict):
            out = {}
            for k, v in zip(node.keys, node.values):
                if k is None:                                   # **spread（同文件名字表能折就折）
                    spread = self._conv(v, depth + 1)
                    if isinstance(spread, dict):
                        out.update(spread)
                        continue
                    out[EXPR + "spread:" + ast.unparse(v)] = EXPR
                    continue
                out[self._conv(k, depth + 1)] = self._conv(v, depth + 1)
            return out
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            v = self._conv(node.operand, depth + 1)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return -v if isinstance(node.op, ast.USub) else v
            return EXPR + ast.unparse(node)
        if isinstance(node, ast.Name) and node.id in self.assigns:
            return self._conv(self.assigns[node.id], depth + 1)
        return EXPR + ast.unparse(node)                          # 退化：源码文本比较

    def enum_members(self, cls: str) -> dict:
        for node in self.tree.body:
            if isinstance(node, ast.ClassDef) and node.name == cls:
                out = {}
                for st in node.body:
                    if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name):
                        out[st.targets[0].id] = self._conv(st.value, 0)
                return out
        return {}

    def imports_from(self, module_tail: str) -> list:
        out = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[-1] == module_tail:
                out.extend(a.name for a in node.names)
        return out


_ENUM_REF = re.compile(r"^SkillKind\.(\w+)(?:\.value)?$")


def _resolve(view: ModView, val):
    """把退化成文本的值再救一次：`«expr»SkillKind.PHYS.value` → 枚举成员的真值。"""
    if isinstance(val, str) and val.startswith(EXPR):
        m = _ENUM_REF.match(val[len(EXPR):].strip())
        if m:
            mem = view.enum_members("SkillKind")
            if m.group(1) in mem:
                return mem[m.group(1)]
    return val


def _diff(a, b, path: str = "¥", out=None, limit: int = MAX_DIFF) -> list:
    """浅层结构化差异文案（最多 limit 条），用于红行定位。"""
    if out is None:
        out = []
    if len(out) >= limit:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) - set(b), key=repr):
            out.append("%s 真源有键 %r 而包内无" % (path, k))
            if len(out) >= limit:
                return out
        for k in sorted(set(b) - set(a), key=repr):
            out.append("%s 包内多出键 %r（真源没有）" % (path, k))
            if len(out) >= limit:
                return out
        for k in sorted(set(a) & set(b), key=repr):
            if a[k] != b[k]:
                _diff(a[k], b[k], "%s%r." % (path, k), out, limit)
        return out
    if a != b:
        out.append("%s 真源=%r 包内=%r" % (path, a if not hasattr(a, "__len__") else str(a)[:120],
                                          b if not hasattr(b, "__len__") else str(b)[:120]))
    return out


class Rep:
    def __init__(self, quiet: bool = False):
        self.passed = 0
        self.failed = 0
        self.violations: list = []
        self.quiet = quiet

    def check(self, name: str, cond: bool, detail: str = "") -> bool:
        if cond:
            self.passed += 1
            if not self.quiet:
                print("  ✅ %s" % name)
        else:
            self.failed += 1
            msg = "%s %s" % (name, detail)
            self.violations.append(msg.strip())
            if not self.quiet:
                print("  ❌ %s" % msg.strip())
        return bool(cond)


# ---------------------------------------------------------------------------
# 四类断言
# ---------------------------------------------------------------------------
# 参数表单源审计（2026-09-13 新增 —— 对应当天修的一个真 bug）
# ---------------------------------------------------------------------------
# 实测踩过：`MECH_CFG` 在包内**三份**（class_data 全量 = 等于真源 / element_data 只 element 一档 /
#   params 只 enemy_bar 一档**且截断**：真源 ENEMY_BAR_CFG 是 {curse, shaken}，它只抄了 shaken）。
#   而 params 那份挂在引擎 hook `mech_cfg_fn` 上 → `config.mech_cfg("enemy_bar")` 拿到的配置**缺 curse**
#   （静默少一档），走 class_data 的装配层却拿到完整的 —— 同一机制名、两条入口、两套值。
# `MECH_CASH` 同理：class_data 9 条 / params 空 `{}`。
# ⇒ 判据：每张参数表在包内**最多一处"字面量定义"**（赋值右侧直接是 dict/list/常量）。
#   再导出（`from x import Y`）与派生值（`Y = f(...)`）**不算**第二份定义 —— 那正是我们要的形状。
SINGLE_SOURCE_TABLES = ("MECH_CFG", "MECH_CASH", "BAR_INJECT_FIELDS", "BAR_STATE_PREFIX",
                        "WEAPON_EFFECT_DATA", "REACTION_TABLE", "ELEMENT_REACTIONS",
                        "ELEMENT_MARKS_MAX", "FORMULA_SKELETON", "SKILL_FLAT", "ACT_TICK")


def single_source_audit(pkg_root: str, rep: Rep) -> None:
    """每张参数表在包内最多一处字面量定义（同表多份 = 值碰巧一致 → 改一处就漂）。"""
    mech = _p(pkg_root, MECH_REL)
    hits: dict = {t: [] for t in SINGLE_SOURCE_TABLES}
    for fn in sorted(os.listdir(mech)):
        if not fn.endswith(".py"):
            continue
        try:
            tree = ast.parse(_read(os.path.join(mech, fn)))
        except SyntaxError:
            continue
        for node in tree.body:                       # 只看**模块顶层**赋值（函数内的临时量不算）
            tgt = None
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                tgt = node.targets[0]
            elif isinstance(node, ast.AnnAssign):    # `X: dict = {...}` 也算定义（实测 params 用过这写法）
                tgt = node.target
            if not isinstance(tgt, ast.Name) or tgt.id not in hits:
                continue
            if isinstance(node.value, (ast.Dict, ast.List, ast.Tuple, ast.Constant)):
                hits[tgt.id].append("%s:%d" % (fn, node.lineno))
    dup = {t: v for t, v in hits.items() if len(v) > 1}
    rep.check("每张参数表在包内最多一处字面量定义（共查 %d 张）" % len(SINGLE_SOURCE_TABLES),
              not dup, "同表多份定义（值碰巧一致也会漂）：%s" % dup)
    rep.check("单源检查不是空转（至少定位到 1 张表的定义处）",
              any(hits.values()), {t: v for t, v in hits.items() if v})


def audit(pkg_root: str, game_root: str, rep: Rep) -> None:
    """把 <pkg_root>/content/mech 当端口，对 game_root 真源跑四类断言（只读）。"""
    def head(msg: str) -> None:
        if not rep.quiet:
            print(msg)

    # ---- ① 端口文件存在 ----
    head("\n【1】端口文件存在（缺文件 = 点名红，绝不静默跳过）")
    for fam, _src, span, prel, _asm, _cmp in PORTS:
        path = _p(pkg_root, prel)
        rep.check("族 %-13s 端口存在 %s（真源 %s）" % (fam, prel, span),
                  os.path.isfile(path), "缺文件：%s" % path)

    # ---- ② @register_action 集合逐名相等 + 装配器名 ----
    head("\n【2】@register_action 集合逐名相等（+ 装配器函数名）")
    for fam, src, span, prel, asm, cmp_actions in PORTS:
        ppath = _p(pkg_root, prel)
        if not os.path.isfile(ppath):
            continue                                            # ① 已红，不重复报
        try:
            pv = ModView(ppath)
        except SyntaxError as e:
            rep.check("族 %s 端口可解析" % fam, False, "语法错：%r" % (e,))
            continue
        rep.check("族 %-13s 端口内 register_action 全是字面量（门禁看得全）" % fam,
                  not pv.nonliteral, "非字面量调用在行 %s" % pv.nonliteral)
        if not cmp_actions:
            continue
        gpath = _p(game_root, src)
        if not os.path.isfile(gpath):
            rep.check("族 %s 真源存在 %s" % (fam, src), False, "真源文件缺失：%s" % gpath)
            continue
        gset, pset = set(ModView(gpath).actions), set(pv.actions)
        only_g, only_p = sorted(gset - pset), sorted(pset - gset)
        rep.check("族 %-13s @register_action 集合逐名相等（真源 %d / 包内 %d）" % (fam, len(gset), len(pset)),
                  gset == pset,
                  "真源有包内无(漏搬)：%s；包内有真源无(私加)：%s" % (only_g, only_p))
        if asm:
            gdefs = ModView(gpath).defs
            miss_g = [n for n in asm if n not in gdefs]
            miss_p = [n for n in asm if n not in pv.defs]
            rep.check("族 %-13s 装配器 %s 两端都在" % (fam, "/".join(asm)),
                      not miss_g and not miss_p,
                      "真源缺：%s；包内缺：%s" % (miss_g, miss_p))

    # ---- ③ 参数表 deep-equal ----
    head("\n【3】参数表 deep-equal（两边源码静态读出，不 import 游戏仓模块）")
    for name, src, sline, prel, var in TABLES:
        gpath, ppath = _p(game_root, src), _p(pkg_root, prel)
        if not os.path.isfile(gpath):
            rep.check("表 %-30s 真源存在 %s%s" % (name, src, sline), False, "真源文件缺失：%s" % gpath)
            continue
        if not os.path.isfile(ppath):
            rep.check("表 %-30s 端口存在 %s" % (name, prel), False, "端口文件缺失：%s" % ppath)
            continue
        try:
            gv, pv = ModView(gpath), ModView(ppath)
            a, b = gv.value(var), pv.value(var)
            a_r, b_r = _resolve(gv, a), _resolve(pv, b)
            if not (isinstance(a_r, str) and a_r.startswith(EXPR)) and \
               not (isinstance(b_r, str) and b_r.startswith(EXPR)):
                a, b = a_r, b_r                                  # 两边都求值成功 → 比真值
        except SyntaxError as e:
            rep.check("表 %s 可静态读出" % name, False, "语法错：%r" % (e,))
            continue
        extra = "（真源写法非字面量 → 代入 SkillKind 成员求值后比较）" if name in EXPR_TABLES else ""
        if a == "«missing»" or b == "«missing»":
            rep.check("表 %-30s 两边都取到 %s%s%s" % (name, var, sline, extra), False,
                      "取不到：真源=%r 包内=%r" % (a, b))
            continue
        diffs = _diff(a, b)
        rep.check("表 %-30s == 真源 %s%s（真源 %s 项 / 包内 %s 项）"
                  % (name, src.split("/")[-1] + sline, extra,
                     len(a) if hasattr(a, "__len__") else 1,
                     len(b) if hasattr(b, "__len__") else 1),
                  not diffs, "；".join(diffs))

    # ---- ③b SkillKind 枚举成员（K_* 走文本比较时，值比较在这里兜底）----
    gk, pk, cls = SKILL_KIND
    try:
        gm = ModView(_p(game_root, gk)).enum_members(cls)
        pm = ModView(_p(pkg_root, pk)).enum_members(cls)
    except (OSError, SyntaxError) as e:
        rep.check("SkillKind 枚举可读", False, "%r" % (e,))
        gm = pm = {}
    if gm and pm:
        rep.check("SkillKind 枚举成员逐值相等（真源 %d / 包内 %d）：%s"
                  % (len(gm), len(pm), ",".join(sorted(gm))),
                  gm == pm, "；".join(_diff(gm, pm)))

    # ---- ③c 再导出接线（双源收敛不许长回第二个副本）----
    head("\n【4】单源再导出接线（BAR_* 唯一真源在 params.py）")
    for prel, nm, srcmod in REEXPORTS:
        ppath = _p(pkg_root, prel)
        ok = os.path.isfile(ppath) and nm in ModView(ppath).imports_from(srcmod)
        rep.check("%s 里 %s 仍从 .%s 再导出" % (prel, nm, srcmod), ok,
                  "未见 `from .%s import %s`（双源长回来了？）" % (srcmod, nm))
    pparams = _p(pkg_root, "content/mech/params.py")
    if os.path.isfile(pparams):
        pv = ModView(pparams)
        rep.check("params.py 是 BAR_* 的字面量单源（本文件自带定义，非再导出）",
                  "BAR_INJECT_FIELDS" in pv.assigns and "BAR_STATE_PREFIX" in pv.assigns,
                  "params.py 里没有 BAR_* 的模块级赋值")

    # ---- ⑤ 参数表单源（同表多份 = 值碰巧一致也会漂；2026-09-13 新增）----
    head("\n【5】参数表单源（每张表最多一处字面量定义；MECH_CFG 曾散成三份且一份截断）")
    single_source_audit(pkg_root, rep)


# ---------------------------------------------------------------------------
# ④ 漂移反证：在 tmp 副本上「装坏」，门禁必须报红
# ---------------------------------------------------------------------------
def _copy_pkg(pkg_root: str, tmp_root: str) -> None:
    shutil.copytree(_p(pkg_root, MECH_REL), _p(tmp_root, MECH_REL),
                    ignore=shutil.ignore_patterns("__pycache__"))


def _mutate(path: str, old: str, new: str) -> bool:
    txt = _read(path)
    if old not in txt:
        return False
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(txt.replace(old, new, 1))
    return True


def drift_reversal(pkg_root: str, game_root: str, rep: Rep, tmp_root: str) -> None:
    """造 5 份「装坏后」的副本 → 每份都必须在门禁下报红（防门禁永远绿）。"""
    print("\n【6】漂移反证（tmp 副本上装坏 → 门禁必须红；真仓不受影响）")
    cases = [
        ("M1 改动作名", "class_mech.py", '@register_action("passive_counter")',
         '@register_action("passive_counter_renamed")', "passive_counter"),
        ("M2 删端口文件", None, None, None, "worldboss.py"),
        ("M3 改参数表值", "class_data.py", "'crit_at': 4,", "'crit_at': 5,", "MECH_CASH"),
        ("M4 改标量表", "params.py", 'BAR_STATE_PREFIX = "bar:"', 'BAR_STATE_PREFIX = "barX:"',
         "BAR_STATE_PREFIX"),
        # M5：把"同表多份"长回来（在另一个文件里再写一份 MECH_CFG 字面量）→ 单源审计必须报红
        ("M5 双源长回来", "element_data.py", "ELEMENT_SAME_CAST_EXTRA_CHARGE = 1",
         'ELEMENT_SAME_CAST_EXTRA_CHARGE = 1\nMECH_CFG = {"element": {}}', "MECH_CFG"),
    ]
    for tag, fname, old, new, must_mention in cases:
        sub = os.path.join(tmp_root, tag.split()[0])
        os.makedirs(sub, exist_ok=True)
        _copy_pkg(pkg_root, sub)
        mech = _p(sub, MECH_REL)
        if fname is None:
            os.remove(os.path.join(mech, must_mention))
            mutated = True
        else:
            mutated = _mutate(os.path.join(mech, fname), old, new)
        if not mutated:
            rep.check("反证 %s：装坏生效（哨兵字串命中）" % tag, False,
                      "副本里没找到 %r —— 真源/包内写法变了，请更新本门禁的哨兵串" % (old or fname))
            continue
        quiet = Rep(quiet=True)
        audit(sub, game_root, quiet)
        hit = [v for v in quiet.violations if must_mention in v]
        rep.check("反证 %s：门禁在副本上报红且点名 %r（共 %d 条红）"
                  % (tag, must_mention, len(quiet.violations)), bool(hit),
                  "未报红 = 门禁是死的！" if not quiet.violations
                  else "红了 %d 条但没点名 %r：%s" % (len(quiet.violations), must_mention, quiet.violations[:2]))

    recheck = Rep(quiet=True)
    audit(pkg_root, game_root, recheck)
    rep.check("反证收尾：前面 5 次装坏只动了 tmp 副本，真仓/真包依然全绿",
              recheck.failed == 0, "真仓被污染了！%s" % recheck.violations[:2])


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 第三类：事件名反静默失效（2026-09-13 新增）
# ---------------------------------------------------------------------------
# 为什么：引擎 `fire()` 对**不在 EVENTS 全集**的事件名**静默 return**（effect_triggers.py 的
#   `if not event or event not in EVENTS: return`）→ "翻译器/数据写了个死名" = 触发器装上了
#   却永不触发、且**没有任何痕迹**（2026-09-13 缺口定性查出的第 4 条，属最难查的一类）。
#   端口侧已补运行时告警（`equip._UNKNOWN_EVENTS` + `map_event` 未知名 logging.warning）——
#   本类守那套机制**在位**（被删/被绕开都会红）+ 数据侧的名字**必须可解析**。
KNOWN_NON_EVENT_MARKERS = ("passive",)   # 常驻型标记：不是引擎事件，也不该被 fire 到（设计如此）


def dead_event_audit(pkg_root: str, game_root: str, rep: Rep) -> None:
    """事件名反静默失效（源码/数据口径，不 import —— 与前两类一致）。"""
    if not rep.quiet:
        print("\n【7】事件名反静默失效（死名 = 触发器装了却永不生效）")

    eng = _p(FW_ROOT, "saintess_engine", "battle", "effect_triggers.py")
    events: set = set()
    try:
        for n in ast.walk(ast.parse(_read(eng))):
            if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "EVENTS":
                events = set(ast.literal_eval(n.value))
    except Exception as e:                                       # noqa: BLE001
        rep.check("读得到引擎 EVENTS 全集（%s）" % eng, False, repr(e))
        return
    rep.check("引擎事件全集非空（%d 个事件）" % len(events), len(events) >= 20, sorted(events))

    # ---- 机制在位 ----
    eq = _p(pkg_root, "content", "mech", "equip.py")
    src = _read(eq)
    rep.check("端口 equip.py 保留未知名告警机制（_UNKNOWN_EVENTS + _known_engine_events）",
              "_UNKNOWN_EVENTS" in src and "def _known_engine_events" in src,
              "机制被删/被绕过 —— fire() 会静默吞掉死名")
    ev_map: dict = {}
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "_EVENT_MAP":
            ev_map = ast.literal_eval(n.value)
    rep.check("_EVENT_MAP 有 dot_taken → dot_tick（对齐 N9 迁移表）",
              tuple(ev_map.get("dot_taken") or ()) == ("dot_tick",), ev_map.get("dot_taken"))
    bad_map = {k: [v for v in vs if v not in events] for k, vs in ev_map.items()
               if any(v not in events for v in vs)}
    rep.check("_EVENT_MAP 每个展开目标都在引擎事件全集里", not bad_map, bad_map)

    # ---- 数据侧：包内武器特效表的事件名必须可解析 ----
    we = _p(pkg_root, "content", "mech", "we_data.py")
    data_events: set = set()
    for n in ast.walk(ast.parse(_read(we))):
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "WEAPON_EFFECT_DATA":
            for _k, v in ast.literal_eval(n.value).items():
                e = v.get("event") if isinstance(v, dict) else None
                for x in (e if isinstance(e, (list, tuple)) else [e]):
                    if x:
                        data_events.add(str(x))
    dead = sorted(x for x in data_events
                  if x not in events and x not in ev_map and x not in KNOWN_NON_EVENT_MARKERS)
    rep.check("武器特效数据的 %d 个 event 名全部可解析（引擎全集 ∪ _EVENT_MAP ∪ 非事件标记）"
              % len(data_events), not dead, "死名（会被 fire 静默吞掉）：%s" % dead)
    rep.check("武器特效数据里确实有走 _EVENT_MAP 的旧名（别把断层测成空转）",
              any(x in ev_map for x in data_events), sorted(data_events))


def main() -> int:
    t0 = time.time()
    print("=== P4「逐字端口」保真门禁（包内 mech vs 游戏仓真源）===")
    print("    真源 = %s" % REPO_ROOT)
    print("    框架 = %s" % FW_ROOT)
    print("    端口 = %s" % _p(PKG_ROOT, MECH_REL))
    if not os.path.isdir(_p(PKG_ROOT, MECH_REL)):
        print("❌ 端口目录不存在：%s（可用 GWEN_FRAMEWORK_DIR 覆盖框架仓路径）" % _p(PKG_ROOT, MECH_REL))
        return 1

    rep = Rep()
    audit(PKG_ROOT, REPO_ROOT, rep)
    dead_event_audit(PKG_ROOT, REPO_ROOT, rep)
    tmp_root = tempfile.mkdtemp(prefix="mech_port_drift_")
    try:
        drift_reversal(PKG_ROOT, REPO_ROOT, rep, tmp_root)
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    print("\n=== 汇总：%d 通过 / %d 失败（%.1fs）===" % (rep.passed, rep.failed, time.time() - t0))
    if rep.failed:
        print("修法：包内端口是**逐字搬运物**——真源改了就得跟着改（或把该表/动作的归属重新拍板）；"
              "别改本门禁来消红，除非端口清单表本身写错了（文件/行号以本文件头部表为准）。")
    return 1 if rep.failed else 0


if __name__ == "__main__":
    sys.exit(main())
