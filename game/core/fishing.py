# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心 - fishing.py（16 章品质垂钓 v2.0）—— B13-L5 **薄壳**（2026-09-14）

roll 流程（垂钓等级查五档权重表 → 过滤钓点禁出档位 → 选档位 → 档位内按品种权重选）的实现正文
（150 行，含 `roll_fish` / `_roll_fish_legacy` / `_quality_weights` / `roll_fish_size_weight` /
`roll_collect_fish`）已**逐字搬进内容包** `content/fishing.py`：
`FISHING_SPOTS` / `FISH_POOL` 改读包内域（`fishing_spots` / `fishing_pool`，对拍逐项相等）。
本文件只剩三件事：**加载包** · **模块别名**（`sys.modules[__name__] = 包内模块`） · **源码探针**。

为什么用「模块别名」而不是「一行转发桩」
----------------------------------------
`tests/test_v116_fishing_season.py:29-34` 用 `F.current_season = lambda now=None: season`
临时把季节钉死（`import data.plugins.dragonfall.game.core.fishing as F`），
`tests/test_v184_loot_tiers.py:414/449` 直接调 `F._quality_weights` / `F._roll_fish_legacy` ——
转发桩会让季节补丁**静默失效**（补丁打在壳的模块全局上，实现读自己的）。
别名之后 `game.core.fishing` 与 `content.fishing` **是同一个模块对象**：
`from .fishing import roll_fish, roll_collect_fish, roll_fish_size_weight`（`game/core/__init__.py:71`）
与聚合层 `C.roll_fish`（`tests/test_commands_fishing.py` 等 monkeypatch）取到的都是实现本体。

宿主源码级门禁（**判据只加强**）
--------------------------------
`tests/test_v184_loot_tiers.py:697-699` 按**本文件源码**查三个字符串：
必须含 `weights = FISH_TIERS.weights_at(prof_lv)` 与
`random.choices(FISH_QUALITY_ORDER, weights=weights, k=1)[0]`、不得含旧的档位权重表取法
（`FISH_QUALITY_WEIGHTS` + `[`，故本文件里该字面量**被刻意拆成两段拼接**，免得自己把自己扫红）。
本文件保留同字面量指针，并在 import 期**断言前两条确实还长在包内实现里、第三条确实不在**
—— 指针指向的实现若漂移，直接 import 失败（比「扫到壳上一句注释就过」强）。
"""
import inspect as _inspect
import sys as _sys

from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                  # 本进程唯一包加载口（幂等）

from content import fishing as _impl                         # noqa: E402  包内实现（真源）

# ---- 宿主源码级门禁指针（tests/test_v184_loot_tiers.py:697-699）----
_SRC_PROBES = (                                              # noqa: F841
    "weights = FISH_TIERS.weights_at(prof_lv)",
    "random.choices(FISH_QUALITY_ORDER, weights=weights, k=1)[0]",
)
# 禁用形（拼接写，别让本文件自己含该字面量 —— 门禁要的是「源码里没有它」）
_SRC_FORBIDDEN = "FISH_QUALITY" + "_WEIGHTS["                # noqa: F841
try:
    _IMPL_SRC = _inspect.getsource(_impl)
except OSError as _exc:                                      # pragma: no cover
    raise RuntimeError("fishing 薄壳：取不到包内实现源码，唯一真相源指针无法核验（%r）" % (_exc,))
for _needle in _SRC_PROBES:
    if _needle not in _IMPL_SRC:
        raise RuntimeError("fishing 薄壳：包内实现已漂移（源码里查不到 %r）" % (_needle,))
if _SRC_FORBIDDEN in _IMPL_SRC:
    raise RuntimeError("fishing 薄壳：包内实现重新自建档位权重表（出现 %r）" % (_SRC_FORBIDDEN,))

_sys.modules[__name__] = _impl                               # 模块别名：壳与实现同体
