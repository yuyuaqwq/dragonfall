# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 核心层 - instance_gate.py（v141 审计：副本钥匙判定抽公共）

副本准入的两处钥匙三路匹配 + 通关豁免判定（world.py 门禁 / instance.py 开本）
原为双份字符串级复制，抽到本文件统一——改匹配规则只改一处。

- find_instance_key_item：三路匹配背包条目
  data.name == key_item / it.key == key_item / ITEMS[key].name == key_item，
  count >= 1，返回背包条目（开本扣钥匙用同一条目）。
- instance_cleared_qq：查 inst_clear_<inst_key> 成就 progress >= 1（通关豁免）。

设计语义（与现状一致，勿改）：
- world.py 门禁（徒步进图）：任务放行层（main/side explore 目标）→ 钥匙 → 通关豁免，
  徒步进图**不扣钥匙**（只校验持有）。
- instance.py 开本（『副本 <名字>』）：钥匙 → 通关豁免，**有钥匙且未通关才扣钥匙**；
  已通关免钥匙（不放行是设计——开本走完整校验）。
"""
from __future__ import annotations

from typing import Optional


def find_instance_key_item(group_id: str, qq_id: str, key_item: str) -> Optional[dict]:
    """三路匹配背包钥匙条目：data.name == key_item / it.key == key_item /
    ITEMS[key].name == key_item，count >= 1。命中返回背包条目 dict
    （含 key/data/count，供开本扣钥匙），未命中返回 None。

    ITEMS 映射经内容层（game.content 聚合 data.ITEMS）读取——延迟导入避免
    core 与 data/_assembly 装配期循环导入（与 core 其它模块同铁律）。
    """
    if not key_item:
        return None
    from .. import db
    try:
        from .. import content as C  # 内容层（聚合 data.ITEMS）
        _items = getattr(C, "ITEMS", {}) or {}
    except Exception:
        _items = {}
    for it in (db.get_inventory(group_id, qq_id) or []):
        it_name = (it.get("data") or {}).get("name", "")
        if it_name == key_item or it.get("key") == key_item \
                or _items.get(it.get("key"), {}).get("name") == key_item:
            if (it.get("count") or 0) >= 1:
                return it
    return None


def instance_cleared_qq(group_id: str, qq_id: str, inst_key: str) -> bool:
    """玩家是否已通关某副本（inst_clear_<inst_key> 首通记录 progress >= 1）。

    与 instance.py 开本免钥匙 / world.py 门禁免钥匙同口径（成就表首通记录）。
    """
    if not inst_key:
        return False
    from .. import db
    return any(a.get("ach_key") == f"inst_clear_{inst_key}" and a.get("progress", 0) >= 1
               for a in (db.get_achievements(group_id, qq_id) or []))
