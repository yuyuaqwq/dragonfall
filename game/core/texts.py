# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 内容层 - texts（文案表装载器，★ B13-L7 起 = 薄壳）

**真源已在包内**（★ P4′-B，2026-09-14）：`<pkg>/content/data/text_specs.json`
（对象 key 即文案标识；`_` 开头的是给人/编辑器看的元信息，不入表）。
本文件**不再持有任何宿主目录路径** —— `SPEC_PATH` 取自包内装载器（`_pkg.SPEC_PATH`）；
宿主那份 `game/data/text_specs.json` 退化为**构建期镜像**（门禁
`tests/test_text_specs_sync.py` 钉住两边逐字节相等），宿主运行期一个字节都不读它。

装载实现已进内容包：`content/texts.py`（**逐字端口**；真源 = 本文件旧版 96 行）。
本文件只做三件事：

  1. 加载包（`game.bootstrap.package_apply()`，幂等；失败大声抛）
  2. 注入：**包内声明文件路径的取件**（`bind_spec_path(source=lambda: SPEC_PATH)` —— 取件式，
     所以 `T.SPEC_PATH = 坏文件; T.reload()` 这条测试路径照旧生效）+ 宿主日志器
     （`log_setup.LOG`，按自己那棵树惰性解析）
  3. 同名单 re-export（6 个符号，名字/签名一字不变）

引擎仍是 `saintess_engine.text.TextTable`（纯计算、无 IO、无全局态）；语义不变：
`text()/static()` 缺 key → ERROR 日志 + 返回 key 本身；`reload()` 热重载；`audit()` 自检。

消费点零改动：`game/commands/{instance,instance_battle,instance_router,event_menu,misc,
weekly,world}.py`、`game/services/quests.py`、`tests/test_texts_table.py:60`。
（★ 引用「声明表门禁 `tests/test_texts_table.py`」—— 它的「声明 ↔ 调用点」AST 对账按
**宿主命令层文件**做，本薄壳不参与渲染，调用点一行未动。）
"""
from .. import bootstrap as _bootstrap

_bootstrap.package_apply()                                   # 包加载口（失败抛，不静默）
from content import texts as _pkg                            # noqa: E402

_HERE_PKG = __package__.rsplit(".", 1)[0]                    # "game" / "data.plugins.dragonfall.game"

# ── 声明文件路径：**包内**真源（唯一）—— 取值来自包内装载器本身（单一来源），
# 宿主侧不再出现任何宿主目录拼装。模块级常量保持可写（`T.SPEC_PATH = 坏文件`
# 的既有门禁路径照旧生效）。路径形状由门禁 `tests/test_texts_specs_sync.py` 钉死。
SPEC_PATH = _pkg.SPEC_PATH


class _LazyLog:
    """宿主 `log_setup.LOG` 的惰性句柄（按薄壳自己那棵树解析，import 期不触宿主）。"""

    def __getattr__(self, name):
        import importlib
        log = importlib.import_module(_HERE_PKG + ".log_setup").LOG
        return getattr(log, name)


_pkg.bind_spec_path(source=lambda: SPEC_PATH)                # 路径取件（测试会改 SPEC_PATH）
_pkg.bind_log(_LazyLog())

# ---- 同名单 re-export（真源符号名一字不变）----
table = _pkg.table
reload = _pkg.reload          # noqa: A001  (真源即 `reload`，保持符号名不变)
text = _pkg.text
static = _pkg.static
audit = _pkg.audit
load_error = _pkg.load_error
