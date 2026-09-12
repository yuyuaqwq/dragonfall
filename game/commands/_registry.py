# -*- coding: utf-8 -*-
"""命令正则有效表（**唯一来源：指令声明表**，派生）。

命令正则的**唯一真源**是 `game/data/command_specs.json`：命令层用 `@declared("key")`
（等价于旧的 `@filter.regex(<字面量>)`）从声明取正则注册，本表由 `_declared_patterns()`
从**同一份声明**派生：

    COMMAND_REGEX = {key: 合并正则}        # 多条 pattern（别名）→ (?:a)|(?:b)

2026-09-12（路线图 #9「指令表迁移收尾」）：194 条指令全部迁入声明表，原先手工维护的
`_LITERAL_REGEX` 镜像表（与装饰器 1:1 同步的那张，曾靠一个同步测试盯着）**已删除** ——
此后不存在第二份正则，「表与装饰器漂移」在结构上不可能发生。
新增指令：**只在声明表加声明 + `@declared("key")`**，不要在这里补条目。

用途：测试环境/注册表缺失时的快捷指令校验、`_GameCmdFilter` 停服 gate 拦截、
快捷转发回退（`base.py _static_handlers`）。真实 AstrBot 运行以全局注册表
（star_handlers_registry）为准，本表仅供上述回退场景。

门禁：
  * `tests/test_v185_command_migration.py` —— 冻结比对（有效表逐字不变）+ 单源结构断言
  * `tests/test_v87_command_matrix.py` —— 有效表键集 == 装饰器集（逐条相等）+ 互斥矩阵
  * `tests/test_v181_command_declaration.py` —— 派生保真 / 漂移双向干净 / 编辑器可编辑

⚠️ 本文件保持**标准库 only**：测试与工具用 importlib 直载本模块，不能出现包内相对导入。
"""

# ============================================================
# 派生：声明表 → 有效表
# ============================================================


def _combine_patterns(patterns):
    """多条正则合成一条（与框架 `command.combine_patterns` **同语义**）。

    此处不 import 框架，是为了让本表能被独立加载（测试直载 / 工具脚本）。
    两边一致性由 `tests/test_v181_command_declaration.py` 断言锁死（防漂移）。
    """
    pats = [p for p in (patterns or ()) if p]
    if not pats:
        return ""
    if len(pats) == 1:
        return pats[0]
    return "|".join("(?:%s)" % p for p in pats)


def _declared_patterns():
    """读指令声明表派生 `{key: 正则}`。

    文件缺失/损坏 → 返回空表（本表仍可用；真正注册用的 `@declared` 会 fail-closed 抛错，
    所以坏掉不会被静默忽略）。
    """
    import json
    import os
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "data", "command_specs.json")
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    out = {}
    for k, v in (data or {}).items():
        pats = v.get("patterns", v.get("pattern")) if isinstance(v, dict) else v
        if isinstance(pats, str):
            pats = [pats]
        combined = _combine_patterns(pats)
        if combined:
            out[str(k)] = combined
    return out


# 有效表（调用方零改动：`COMMAND_REGEX` 名字与形状不变）
COMMAND_REGEX = _declared_patterns()
