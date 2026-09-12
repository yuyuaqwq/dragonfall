# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 内容层 - texts.py（文案表装载器，v185）

**唯一真源**：`game/data/text_specs.json`（对象 key 即文案标识；`_` 开头的是给人/编辑器看的
元信息，不入表）。本模块是全仓**唯一**读它的地方 —— 做法与 `commands/_declared.py` 读
`command_specs.json` 一致：声明文件在 data 层，装载 IO 放在消费侧。

因此：**文案只存在于 JSON 一处**，代码侧只传槽位（`text("k", **slots)`），
结构上不可能出现"同一句话两份"。

引擎：`saintess_engine.text.TextTable`（纯计算、无 IO、无全局态）。

缺 key 的语义刻意**不静默**：
  · `text()/static()` → 缺 key 时打 ERROR 日志并**返回 key 本身**
    （玩家截图 + 值班日志双可见；不像 strict 那样打断整条命令，也不静默退回某个旧串）
  · `reload()`  → 热重载（改完 JSON 不必重启）
  · `audit()`   → 自检汇总，供门禁与值班脚本用

用法：
    from ..core.texts import text as _text, static as _static
    return _text("weekly.locked", min_lv=50)
    lines = [_static("weekly.sep"), ...]        # 无槽位的
"""
import json
import os

from saintess_engine.text import TextTable

from ..log_setup import LOG

# ── 声明文件路径：game/data/text_specs.json ──
_HERE = os.path.dirname(os.path.abspath(__file__))          # game/core
SPEC_PATH = os.path.join(os.path.dirname(_HERE), "data", "text_specs.json")

_TABLE = None           # type: TextTable | None
_LOAD_ERROR = ""        # 最近一次装载失败原因（空 = 正常）


def _on_miss(key, slots):
    """缺 key：打 ERROR 日志（唯一日志入口），返回值 None → 引擎继续走 fallback 分支
    （本表未配 fallback ⇒ 最终把 key 本身返回给玩家，看得见）。"""
    LOG.error("文案缺 key：%s —— 请查 %s（槽位 %s）", key, SPEC_PATH, sorted(slots or {}))
    return None


def _load_specs() -> dict:
    """读声明文件（唯一 IO 点）。任何异常 → 空表 + ERROR 日志，绝不静默吞掉。"""
    global _LOAD_ERROR
    try:
        with open(SPEC_PATH, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception as exc:                        # 文件缺失/语法错
        _LOAD_ERROR = "%s: %s" % (type(exc).__name__, exc)
        LOG.error("文案表装载失败（%s）：%s", SPEC_PATH, _LOAD_ERROR)
        return {}
    if not isinstance(raw, dict):
        _LOAD_ERROR = "顶层不是对象"
        LOG.error("文案表格式错误：顶层应为对象（%s）", SPEC_PATH)
        return {}
    _LOAD_ERROR = ""
    return {k: v for k, v in raw.items() if not str(k).startswith("_")}


def table() -> TextTable:
    """文案表（懒建 + 缓存；此时内容层已就绪，无导入环）。"""
    global _TABLE
    if _TABLE is None:
        _TABLE = TextTable(_load_specs(), name="dragonfall-texts", on_miss=_on_miss)
    return _TABLE


def reload() -> TextTable:
    """热重载：丢掉缓存重新读文件（编辑器/测试改完 JSON 用）。"""
    global _TABLE
    _TABLE = None
    return table()


def text(key: str, **slots) -> str:
    """渲染带槽位的文案。"""
    return table().render(key, **slots)


def static(key: str) -> str:
    """渲染无槽位的文案（句壳固定）。"""
    return table().render(key)


def audit() -> dict:
    """自检汇总：{total, requested, missing, unused, problems}（门禁/值班用，只报告不抛）。"""
    return table().audit()


def load_error() -> str:
    """最近一次装载失败原因（空 = 正常）。"""
    return _LOAD_ERROR
