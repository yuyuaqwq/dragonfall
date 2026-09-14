# -*- coding: utf-8 -*-
"""世界 Boss 内容装配层 battle_worldboss_procs —— **B2-W2 薄壳指向**（2026-09-14）

真源（**唯一实现**）= 内容包 `content/mech/worldboss.py`（B10-L4 起：动作 `wb_gm_dmg_mult`
**+** 装配入口 `apply_gm_dmg_mult` 同处一个模块；未搬项与边界见那边的头注）。本文件现在只剩
「加载包 + 按名指向」两件事（照**已有先例** `game/core/wild_king.py` 的写法，本波**不删壳**）：

    `game.services.battle_worldboss_procs.{wb_gm_dmg_mult,apply_gm_dmg_mult}` 现在**就是**包内
    同名对象（`is` 身份，不是第二份转发实现）⇒ 名字 / 签名 / 语义 / 返回一字不变，调用点零改动：

        game/commands/combat.py        WBP.apply_gm_dmg_mult(actor, mult)      （生产）
        tests/test_v181_worldboss_gm_dmg.py                                  （两名字直呼）

★ 为什么这里用「静态再导出 + 一行 import」而不是 `sys.modules` 整体替换
（与 `game/core/drops.py` 等处不同）：宿主门禁 `tests/test_package_mech_ports.py:197-227/740-762`
对**本文件路径**做 AST 判据 —— `is_shell_file()`（0 个 `@register_action` + 命中
`SHELL_MARK = ^\\s*from\\s+content(?:\\.\\w+)*\\s+import\\s` + <400 行）与
`shell_exports()`（薄壳对外名字面 ⊇ 端口动作函数名）。静态再导出是这些判据唯一认可的形态
（要满足它就必须让 `from content… import` 与名字面**在本文件里真实存在**）。
动作注册真源只有包内一份（`content/apply.py` import 即注册；宿主进程的包加载口 =
`game.bootstrap.package_apply()`），故本文件**不再** `@register_action`。
"""
from .. import bootstrap as _bootstrap                          # noqa: E402

_bootstrap.package_apply()                                      # 本进程唯一包加载口（幂等；失败抛）

from content.mech.worldboss import apply_gm_dmg_mult, wb_gm_dmg_mult  # noqa: E402,F401

__all__ = ["wb_gm_dmg_mult", "apply_gm_dmg_mult"]
