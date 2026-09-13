# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - dialogue（多轮对话引擎）★ B13-L3 起 = 薄壳

实现真源已进内容包：`content/dialogue.py`（`get_dialogue` / `dialogue_node` / `check_need` /
`visible_options` / `_story_to_line` / `node_text` / `is_end` 逐字端口；数据读口改造与缺口
全写在那边的头注里）。本文件只剩三件事：

  1. **加载包**：`bootstrap.package_apply()`（本进程唯一包加载口，幂等；失败大声抛）
  2. **同名单 re-export**：`game/core/__init__.py:46` 的 6 个 import 名 +
     `tests/test_v98_03_registry.py:44` 的 `check_need` 零改动
  3. `__getattr__` / `__dir__` 兜底

★ 顺带消掉一处**历史脆弱点**：改前本文件模块级 `from .. import content as C` ——
  `tests/test_v136_gem_drops.py:15` / `tests/test_v136_gems.py:20` 都在注释里记着
  「第一个 import 必须是 game.content，否则本文件会把残缺 content 缓存住（缺 gems 聚合符号）」。
  现在本文件模块级**不再 import 宿主 content**（对话树读包内 `dialogues` 域，
  日志走惰性宿主替身）⇒ 那条导入顺序铁律对 `game.core.dialogue` 不再适用
  （行为不变：仍是同一份对话数据 / 同一个 LOG）。

纯逻辑，不碰 DB/QQ。数据的宿主真源仍是 `game/data/dialogues.py`（B14 切读点时按 `dialogues` 域统一处置）。

改造前 131 行 → 现在 40 行。等价证据：`overnight/w1213_b13l3_snap.py`（D1–D10 共 15 例）
· `overnight/W-B13-L3-events-dialogue.md`。
"""
from .. import bootstrap as _bootstrap                          # noqa: F401

_bootstrap.package_apply()                                      # 本进程唯一包加载口（幂等）

from content import dialogue as _IMPL                           # noqa: E402  包内唯一实现

# ---- 同名单 re-export（真源符号名一字不变）----
get_dialogue = _IMPL.get_dialogue
dialogue_node = _IMPL.dialogue_node
check_need = _IMPL.check_need
visible_options = _IMPL.visible_options
is_end = _IMPL.is_end
node_text = _IMPL.node_text
_story_to_line = _IMPL._story_to_line
_STORY_PREFIX = _IMPL._STORY_PREFIX

# 包内实现里**不外露**的宿主替身 / 私有工具名（真源本模块也没有这些名字）
_HANDLES = frozenset(("C", "LOG", "bind_host", "_INJECTED", "_HOST_PKG", "_HOST_PKG_FALLBACK",
                      "_host_module", "_host_attr", "_LazyHostAttr", "_read_domain",
                      "_dialogues", "_main_quests", "_DIALOGUES", "_MAIN_QUESTS", "_HERE"))


def __getattr__(name):
    """未列名兜底：转发包内实现；宿主替身名一律不外露。"""
    if name in _HANDLES or name.startswith("__"):
        raise AttributeError("module %r has no attribute %r" % (__name__, name))
    return getattr(_IMPL, name)


def __dir__():
    return sorted((set(globals()) | set(dir(_IMPL))) - set(_HANDLES))
