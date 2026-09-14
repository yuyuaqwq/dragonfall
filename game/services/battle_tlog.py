# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层 - battle_tlog.py（★ B12B13 线2 起 = **全薄壳**）

**两条半边都已归内容包**（`overnight/d3-tlog-port.md` §3 + B10-L2 + 本批实测）：

  ① **采集半边**（`BattleTLog` / `EVENT_KINDS` / `REPRO_KEYS` / `_uid` / `_num` /
     `_rounds_of` / `_player_input`）—— `<pkg>/content/tlog_collect.py`（B10-L2 收口；
     对拍 sha256 `ff0d0e7f14ac72560404824e320b0b4892297e2c432eed811627641f177a05b3` / 10484 B / 231 行）。
  ② **回放半边**（`find_battle` / `replay`，旧版 `:245-321`）—— 本批（B12B13 线2）收口到
     `<pkg>/content/tlog_replay.py`。B10-L2 的留宿理由「依赖宿主重建链」已消失：
     `battle_bridge` 的唯一实现（含回写半边 `sync_player_from_actor` / `_BACK_SYNC_*`）已归包
     `<pkg>/content/bridge.py`（实测确认），回放半边改走包内 `_host_attr("services.battle_bridge", …)`
     取宿主**薄壳**同名函数 —— event_state 仍是宿主 DB 视图，语义一字不变。

本文件只做两件事，**零实现**（无控制流、无数值、无文案字面量）：

  1. 加载包 —— `game.bootstrap.package_apply()` = 本进程唯一包加载口（幂等；失败**大声抛**）
  2. **同名单 re-export** —— 模块路径与符号名逐名不变（含内省用的 `Record` / `random` / `typing` 面）：
       生产消费者 `game/services/battle_bridge.py:218`（`from .battle_tlog import BattleTLog`）
       测试       `tests/test_v182_battle_tlog.py:28`（`BT.BattleTLog` / `BT.replay` / `BT.find_battle`）
       —— 两处 import 点、名字与签名一字不变。

逐字节等价证据：`overnight/W-B12B13-L2.md`（快照 sha256 改前 ≡ 改后 + 反证）。
"""
from __future__ import annotations

import random
from typing import Iterable, Optional

from .. import bootstrap as _BST

_BST.package_apply()                                          # 唯一包加载口
from content.tlog_collect import (                            # noqa: E402  ① 采集半边（唯一真源）
    BattleTLog, EVENT_KINDS, REPRO_KEYS,
    _uid, _num, _rounds_of, _player_input,
)
from content.tlog_replay import find_battle, replay           # noqa: E402  ② 回放半边（唯一真源）
from saintess_engine.tlog import Record                       # noqa: E402  注解用（同义再导出）
