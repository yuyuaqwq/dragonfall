# -*- coding: utf-8 -*-
"""宿主自留测试的**布局发现适配层**（T8 测试单源化）。

T8 之后宿主 `tests/` 只保留宿主专属件（平台桥接 / 平台注册 / 宿主壳 / 宿主工具 / 跑器自检），
内容侧测试真源唯一在包仓 `tests/`。原先散在各宿主测试里「硬算/硬编码」的三样东西收到这里
**一处**，避免每个文件各写一份（也避免再出现「读到另一棵树」的假绿）：

| 名字 | 含义 | 旧写法（为什么不能再用） |
|---|---|---|
| `PLUGIN_DIR` | 宿主插件根（`<plugin>/`） | 各文件自算 `dirname(dirname(__file__))` —— 定义本身还对，但配套发现缺失 |
| `QQBOT_DIR` | 含 `data/plugins/<本插件>` 的部署根 | 死算 `dirname³(PLUGIN_DIR)`：只在**部署布局**成立；本工作副本的 qqbot 名面在**兄弟目录** `<ws>/_run_home`（目录联接 → `<ws>/host`）⇒ 死算落到 `<ws>/..`，`import data.plugins.<pkg>` 当场失败 |
| `SHIM_DIR` | `shim_astrbot`（astrbot 行为等价替身） | 旧写法只认 `host/tests/shim_astrbot`；T8 后宿主侧不自留副本 ⇒ 回落到**包仓那份** tests 里的同名目录。**判定必须看「替身是否真的可 import」**（`astrbot/__init__.py` 在不在），只看 `isdir` 会被「目录还在、.py 已删」的空壳骗过 → 见 `find_shim_dir` 注 |
| `PKG_TESTS_DIR` | 内容侧真源的**部署面**（`<plugin>/framework/games/*/tests`） | 旧写法没有这个概念（当时真源在宿主） |

口径与 `pkg/tests/_paths.py`、`scripts/run_all_tests.py` 的发现式写法同精神：**发现 + 显式回落**，
不写死 `C:/Users/...`（本机真仓 `C:/Users/yuyu/qqbot`、`C:/Users/yuyu/framework-engine` 是**别的树**，
读到它们 = 假绿）。

只依赖标准库；导入本模块**无副作用**（不 sys.path、不改 env）。
"""
from __future__ import annotations

import os

HERE = os.path.dirname(os.path.abspath(__file__))
#: 宿主插件根（`<plugin>/`：本文件在 `<plugin>/tests/`）
PLUGIN_DIR = os.path.dirname(HERE)


def _samefile(a: str, b: str) -> bool:
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


def find_qqbot_dir() -> str:
    """含 `data/plugins/<本插件>` 的部署根；找不到 → `""`（调用方自己决定怎么报错）。"""
    env = (os.environ.get("GWEN_QQBOT_DIR") or "").strip()
    if env and os.path.isdir(env):
        return os.path.abspath(env)
    plugin_abs = os.path.abspath(PLUGIN_DIR)

    def _hit(root: str) -> bool:
        plugins = os.path.join(root, "data", "plugins")
        if not os.path.isdir(plugins):
            return False
        try:
            names = sorted(os.listdir(plugins))
        except OSError:
            return False
        return any(_samefile(os.path.join(plugins, n), plugin_abs)
                   for n in names if os.path.isdir(os.path.join(plugins, n)))

    home = os.path.dirname(plugin_abs)
    for _ in range(6):
        if _hit(home):
            return home
        try:
            children = sorted(os.listdir(home))
        except OSError:
            children = []
        for name in children:
            child = os.path.join(home, name)
            if os.path.isdir(child) and _hit(child):
                return child
        parent = os.path.dirname(home)
        if parent == home:
            break
        home = parent
    return ""


def find_pkg_tests_dirs() -> list:
    """内容侧真源的部署面：`<plugin>/framework/games/*/tests`（不写死包名）。"""
    games = os.path.join(PLUGIN_DIR, "framework", "games")
    out = []
    if not os.path.isdir(games):
        return out
    for name in sorted(os.listdir(games)):
        d = os.path.join(games, name, "tests")
        if os.path.isdir(d):
            out.append(d)
    return out


def shim_is_usable(shim_dir: str) -> bool:
    """`shim_dir` 是不是**真能替 astrbot** 的那份替身。

    判据 = `shim_dir/astrbot/__init__.py` 存在（替身是**纯 .py 源码树**，见
    `tests/shim_astrbot/README.md`）。

    ★ 为什么不能只判 `os.path.isdir`（实测回归，2026-09-15）：T8 的「宿主侧不再自留该副本」
      只删了 `.py`，**目录连同 `__pycache__` 里的陈旧 `.pyc` 留了下来**。`isdir` 于是照样命中，
      但这个目录**提供不出 `astrbot`**（`__pycache__/x.cpython-312.pyc` 不是可 import 的
      sourceless 落点）⇒ `import astrbot` 静默穿透到**真实 astrbot**；真实 astrbot 会 import
      `rich`，而 `rich/style.py:22` 在**模块级**抽一次 `random.getrandbits(24)`
      （`_id_generator = count(getrandbits(24))`）⇒ 全局随机流整体推后一格
      ⇒ B20 引擎门禁 C 段「逐字节对拍」的**随机提示语**逐条失真（实测 3/44：`地图` / `成就` / `百科`
      的 tips 池 5 选 1 抽到相邻项）。这与「包行为不一致」长得一模一样，却只是**替身没接上**。
    """
    return bool(shim_dir) and os.path.isfile(
        os.path.join(shim_dir, "astrbot", "__init__.py"))


def find_shim_dir() -> str:
    """`shim_astrbot` 目录：宿主自留的那份（若在**且可用**）优先，否则包仓那份（T8 单源）。"""
    local = os.path.join(HERE, "shim_astrbot")
    if shim_is_usable(local):
        return local
    for d in find_pkg_tests_dirs():
        shim = os.path.join(d, "shim_astrbot")
        if shim_is_usable(shim):
            return shim
    return ""


QQBOT_DIR = find_qqbot_dir()
SHIM_DIR = find_shim_dir()
PKG_TESTS_DIRS = find_pkg_tests_dirs()
PKG_TESTS_DIR = PKG_TESTS_DIRS[0] if PKG_TESTS_DIRS else ""

__all__ = ["HERE", "PLUGIN_DIR", "QQBOT_DIR", "SHIM_DIR",
           "PKG_TESTS_DIR", "PKG_TESTS_DIRS",
           "find_qqbot_dir", "find_shim_dir", "find_pkg_tests_dirs", "shim_is_usable"]
