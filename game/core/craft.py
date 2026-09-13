# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心 - craft.py（v48：输入中文名 → resolve 转 ID 查表；装备名 display 转中文）
—— B13-L5 **薄壳**（2026-09-14）

实现正文（67 行：`craft_recipe_make` / `craft_recipe_search` / `craft_recipes_by_material`）
已**逐字搬进内容包** `content/craft.py`。本文件只剩两件事：**加载包** · **模块别名**
（`sys.modules[__name__] = 包内模块`）。

⚠️ 本模块的三张表**故意没切包内域**（逐字搬时只换「宿主取件」，见包内头注的对照表）：
`CRAFT_RECIPES`（426 条）在包内 `craft` 域里是**字典序**（导出契约 `sort_table`），
宿主真源是**源插入序** —— 迭代序会外泄到行为（`craft_recipe_search` 子串兜底取首次命中、
`craft_recipes_by_material` 的 `sort(key=lv)` 稳定排序并列项），实测 1325 条探针里
**检索 41 条 / 材料联想 87 条输出不同**（`overnight/w1213_l5_craft_order.py`）→ 本线不切，
登记缺口（B14 若不切回 / 不补 `seq` 注入，切点会改行为）。`MATERIALS` / `resolve` / `display`
同理（无同名域 / 属 B13-L7 线在搬）。

别名之后 `game.core.craft` 与 `content.craft` **是同一个模块对象**：
`from .craft import craft_recipe_make, craft_recipe_search, craft_recipes_by_material`
（`game/core/__init__.py:94-96`）与聚合层 `C.craft_recipe_make`（`tests/test_v60_craft_enhance_index.py` 等）
取到的都是包内实现本体，名字/签名/语义零变化。
"""
import sys as _sys

from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                  # 本进程唯一包加载口（幂等）

from content import craft as _impl                           # noqa: E402  包内实现（真源）

_sys.modules[__name__] = _impl                               # 模块别名：壳与实现同体
