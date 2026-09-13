# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年核心层 - index（★ B13-L7 起 = 薄壳）

逻辑真源已进内容包：`content/index.py`（**逐字端口**；真源 = 本文件旧版 56 行）。
本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()`，幂等；失败大声抛）
  2. 注入宿主句柄：`data`（`_INDEXES` 是宿主运行期建的**同一只字典** —— 包内 `build_index`
     写进去、`resolve/display` 读出来，对象身份不变）→ **按完整模块名注入自己那棵树**
     （同进程并存 `game.*` 与 `data.plugins.dragonfall.game.*` 两套模块树，plan §8-R2）
  3. 同名单 re-export（4 个符号）

消费点零改动：`game/core/__init__.py:45`、`game/core/class_sets.py:22`、`game/core/craft.py:5`、
`game/data/_assembly.py:9`（装配期按名字调 `build_index`）、`scripts/gen_stage8_craft.py:17`、
`tests/test_core_index.py:9`。

★ 顺带消掉一条既有循环导入脆弱点：旧实现模块级 `from ..data import _INDEXES` 会在
  「data 半初始化 → core.index」链上炸（脚本注释里记着 `ImportError: cannot import name
  'build_index' from partially initialized module 'game.core.index'`）；现在取件是**调用时**
  经注入句柄解析，import 期不碰宿主表。
"""
from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                   # 包加载口（失败抛，不静默）
from content import index as _pkg                            # noqa: E402

_HERE_PKG = __package__.rsplit(".", 1)[0]
_pkg.bind_host(data=_pkg.lazy_host_module(_HERE_PKG + ".data"))

# ---- 同名单 re-export（真源符号名一字不变）----
pinyin_id = _pkg.pinyin_id
build_index = _pkg.build_index
resolve = _pkg.resolve
display = _pkg.display
