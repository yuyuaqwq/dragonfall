# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层 - battle_team_procs.py（★ B10 线 L2 起 = **薄壳**）

实现正文（20 个 `@register_action` 动词 + 全部模块级助手）**唯一真源已归内容包**：

    <pkg>/content/mech/team_procs.py      （P4/D2 逐字端口；真源 = 本文件旧版 788 行）
    对拍：真源动作区 `:44-788` ⇒ 包内 `:38-782` 逐字节相同
          （sha256 `1d11570e626ee06e99ac68a95684760dd1c0a75779c38b232368120c962155f7` / 30757 B / 745 行；
           唯一差异 = 模块散文头换成包内头注）

本文件只做两件事，**零实现**（无控制流、无数值、无文案字面量）：

  1. 加载内容包 —— `game.bootstrap.package_apply()` = 本进程唯一包加载口（幂等；失败**大声抛**）
  2. **同名单 re-export** —— 模块路径与符号名逐名不变；
     包内模块顶层的 `@register_action("…")` 装饰器在 import 时注册 ⇒
     `from game.services import battle_team_procs as TP  # import 即注册` 语义**完全不变**
     （`tests/test_v181_team_effects.py:45` / `tests/test_v181_element_and_field.py:45` 零改动）

宿主侧活消费者（实测 `git grep`）：只有上面两个测试的 `import 即注册`（无属性访问）。
逐字节对拍证据：`overnight/B10-L2-team-element-tlog.md`（改前 ≡ 改后：sha256 + 字节数）。
"""
from __future__ import annotations

from .. import bootstrap as _BST

_BST.package_apply()                                     # 唯一包加载口（包根进 sys.path + install_engine）
from content.mech.team_procs import (                    # noqa: E402  包内唯一真源
    PREFIX,
    # 模块级助手（与旧宿主实现同名同体）
    _now, _alive, _info, _side_of, team_of, _turns, _num, _res_stacks, _mount, _norm_pct,
    _stat_of, _shield_value, _alt_reduce, _reduce_of,
    # 20 个 @register_action 动词
    team_apply, team_shield, self_shield, team_taken_reduce, team_ss_reduce_apply,
    timed_vuln, timed_vuln_apply, team_dmg_aura, team_dmg_aura_apply, target_lock_mark,
    team_cc_immune, self_cc_immune, team_guard, guard_expire, guard_reflect,
    block_once, block_once_apply, block_reflect_hit, arcane_field, arcane_edge_apply,
)
# 旧宿主模块级名保真（引擎既有动词的 import，非本模块实现）
from saintess_engine.battle.effects import apply_effects, register_action  # noqa: E402,F401
