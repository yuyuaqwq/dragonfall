# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年服务层 - battle_tlog.py（★ B10 线 L2 起 = **半边薄壳**）

**两条半边，归属不同**（`overnight/d3-tlog-port.md` §3 + 本批实测）：

  ① **采集半边**（`BattleTLog` / `EVENT_KINDS` / `REPRO_KEYS` / `_uid` / `_num` /
     `_rounds_of` / `_player_input`）—— **唯一真源已归内容包**
     `<pkg>/content/tlog_collect.py`；对拍：本文件旧版 `:12-242` ⇒ 包内 `:40-270`
     **逐字节相同**（sha256 `ff0d0e7f14ac72560404824e320b0b4892297e2c432eed811627641f177a05b3`
     / 10484 B / 231 行）→ 本文件改为**再导出**。
  ② **回放半边**（`find_battle` / `replay`，旧版 `:245-321`）—— **宿主独有语义，不进包**：
     它依赖**宿主重建链**（`game.services.battle_bridge` 的 `prepare_player_for_battle` /
     `build_sides` / `apply_battle_loadout`），包内 `tlog_collect.py` 明确未搬（见其头注
     §「未搬」）→ 逐字保留在本文件（sha256 `6ea2b5b259a1d111458a1b2b08ce270ee47baccfac25b63fa1b2e7ed3108fcf4`
     / 3770 B / 77 行）。

生产消费者（实测 `git grep`）：`game/services/battle_bridge.py:219`
`from .battle_tlog import BattleTLog`（生产，别线文件）+ `tests/test_v182_battle_tlog.py:28`
（`BT.BattleTLog` / `BT.replay`）—— **名字与签名一字不变，两处 import 点零改动**。
逐字节对拍证据：`overnight/B10-L2-team-element-tlog.md`（改前 ≡ 改后：sha256 + 字节数）。
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
from saintess_engine.tlog import Record                       # noqa: E402  ② 回放半边注解用

# ② 回放半边（宿主独有：依赖宿主重建链）—— 正文逐字保留，见文件头注

# ================================================================ 回放
def find_battle(records: Iterable[Record], tag: Optional[str] = None) -> list:
    """从一段流水里挑出一场战斗的全部记录（按写入顺序）。"""
    out = [r for r in records if str(r.kind).startswith("battle.")]
    if tag is not None:
        out = [r for r in out if r.has_tag(tag)]
    return out


def replay(records: Iterable[Record], *, seed: Optional[int] = None,
           build=None) -> dict:
    """按流水**重演**一场战斗，返回 `{result, rounds, p_acts, expected, matched}`。

    * 重建口径与生产同源：`prepare_player_for_battle` → `build_sides` →
      `apply_battle_loadout` → `Battle(sides=…)`（即 `battle_bridge` 的那一套）。
    * **`seed` 的语义 = 「重演起点」**：它必须在**重建完成之后、第一次行动之前**生效
      （重建本身会消耗随机：装备生成/阈值洗牌等）。所以这里先重建、再 `random.seed`，
      最后重演 —— 记录端也要在同一位置取种子（见 `BattleTLog.attach` 的 docstring）。
    * `build` 可覆盖重建（自定义场景/副本）；默认用记录里的 player/enemies。

    返回的 `matched` = 与记录里 `battle.end` 的 result/rounds/p_acts 是否逐项一致
    —— 这就是「能不能复现同一场」的判据。
    """
    rs = list(records)
    start = next((r for r in rs if r.kind == "battle.start"), None)
    end = next((r for r in rs if r.kind == "battle.end"), None)
    if start is None:
        raise ValueError("流水缺少 battle.start —— 无法重建（记录不完整）")

    from saintess_engine import Battle as B2
    from ..services.battle_bridge import (apply_battle_loadout, build_sides,
                                          prepare_player_for_battle)

    sd = start.fields.get("seed")
    use_seed = seed if seed is not None else sd

    if build is not None:
        btype, sides = build(start.fields)
    else:
        btype = str(start.fields.get("btype") or "monster")
        player = dict(start.fields.get("player") or {})
        enemies = [dict(e) for e in (start.fields.get("enemies") or [])]
        if not player or not enemies:
            raise ValueError("流水缺少重建输入（player/enemies）")
        prepare_player_for_battle(player, player.get("title_bonus"), None)
        sides = build_sides(player, enemies)
        for a in sides.get("player", []):
            apply_battle_loadout(a, player.get("title_bonus"))

    b = B2(btype, sides=sides)
    by_uid = {}
    for side in b.sides.values():
        for a in side:
            by_uid[_uid(a)] = a
    # ★ 重建完成后再设随机流起点（重建会消耗随机）—— 与记录端同一位置取种子
    if use_seed is not None:
        random.seed(int(use_seed))
    for r in rs:
        if r.kind != "battle.act":
            continue
        who = by_uid.get(str(r.fields.get("uid") or "")) or b.focus()
        if who is None:
            continue
        tgt = by_uid.get(str(r.fields.get("target_uid") or ""))
        b.human_act(str(r.fields.get("action") or "attack"),
                    (r.fields.get("skill") or None), who, tgt)

    got = {"result": str(b.result or ""), "rounds": _rounds_of(b),
           "p_acts": int(getattr(b, "_p_acts", 0) or 0)}
    exp = None
    if end is not None:
        exp = {"result": str(end.fields.get("result") or ""),
               "rounds": int(end.fields.get("rounds") or 0),
               "p_acts": int(end.fields.get("p_acts") or 0)}
    return {"result": got["result"], "rounds": got["rounds"], "p_acts": got["p_acts"],
            "expected": exp, "matched": (exp is not None and got == exp),
            "battle": b}
