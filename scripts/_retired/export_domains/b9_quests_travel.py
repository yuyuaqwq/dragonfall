# -*- coding: utf-8 -*-
"""任务流 · 移动线（B9 L5）域插件 —— 本线新域的真源 → 包 JSON。

契约见 `scripts/export_domains/README.md`：本文件只**读真源、返回内存表**，落盘由宿主
（`scripts/export_game_package.py`：UTF-8 / LF / indent=2 / 原子替换 + `sort_table` 外层键字典序）统一做。
**不许 import `export_game_package`**（宿主会扫本目录 → 循环导入）。公用小工具走 `_helpers.py`。

================================================================================
域：`portals` 旅者方碑（11 条；键 = 地图 id）
================================================================================
真源：`game/data/portals.py:4 PORTALS`（**dict**，11 条；实测文件 16 行）

    条目形状：`{地图id: {"name": "橡木方碑", "icon": "🌅"}}` —— 只有两个字段，
    全 11 条都有（`name` str 非空 / `icon` str 非空）。

消费者（游戏侧；导出只搬运不改语义）：

    `game/services/travel.py:367 portal_arrive_note(group_id, qq_id, target)`
        —— 到达图 `tid in C.PORTALS` 且 `tid not in db.get_portals(qq_id)`（未激活）时输出
           `\\n\\n🌌 一座{icon}{name}矗立在此！『激活』可解锁传送点～`（头像字形 + 名字逐字拼进文案）。
    `game/commands/world.py`（『传送』/『激活』）与 `game/services/...` 的传送点面板同样读这张表。

映射口径
--------
  * 真源是 dict → 域也是 dict：**键原样**（= 地图 id，与 `worlds` / `maps` / `subareas` 域的键空间同源）。
  * 条目**原样**进 JSON：不补默认值、不改类型、不动字段顺序、不展开引用串。
  * 唯一注入：**无**（源条目已自带全部字段，且键就是它自己的地图 id ⇒ 不需要 `seq`/`order`）。
  * 外层键用 `sort_table()`（字典序 / 幂等）—— 消费者只按地图 id 取值，**不依赖顺序**
    （全仓 grep：`C.PORTALS` 的三个读点都是 `in` / `[tid]` / 遍历取 name+icon，无序号语义）。

形状门禁（任一不成立 → `raise`，拒绝导出）

  * 真源非空 dict；
  * 每键是非空 str；每值是 dict 且 `name` / `icon` 都是非空 str；
  * **源侧闭合**：每个方碑键必须能在 `MAPS` 里找到同名图 id
    （方碑挂在地图上，悬空键 = 玩家永远走不到的方碑 —— 静默失效，必须报出来）。

未进包（本线登记，见报告 §缺口）
--------------------------------
  * `HIDDEN_MAP_UNLOCK` / `LEGACY_MAP_ALIAS`（`game/data/maps.py:4343/4352` 两个常量模块）
    —— 按 B9 派工「`*_config.py` / 常量模块归 L7」的归属铁律，本线**不建域**；
    包内 `content/travel.py` 经注入的宿主内容聚合层读取（登记缺口）。
  * `TITLES`（`game/data/titles.py`）/ `FACTIONS` + `AREA_FACTION`（`game/data/factions.py`）
    —— 同上（`titles` 域已由别的线声明但**不是名册全量**；本线不碰别人的域）。
"""

from _helpers import import_game_data, sort_table  # noqa: F401

PORTALS_SRC = "game/data/portals.py:4 PORTALS"


def derive_portals(src_root: str = None) -> dict:
    """`portals` 域：`PORTALS`（11 条 dict）→ `{地图id: {name, icon}}`（原样 + 字典序外层键）。"""
    mod = import_game_data("portals", src_root) if src_root else import_game_data("portals")
    table = getattr(mod, "PORTALS", None)
    if not isinstance(table, dict):
        raise TypeError(f"portals：{PORTALS_SRC} 应为 dict（得到 {type(table).__name__}）—— 源形状变了")
    if not table:
        raise ValueError(f"portals：{PORTALS_SRC} 是空表 —— 拒绝导出"
                         f"（空表 = 编辑器显示 0 条且不报错）")

    # 源侧闭合：方碑必须挂在一张真实地图上
    maps = getattr(import_game_data("maps", src_root) if src_root else import_game_data("maps"),
                   "MAPS", None)
    if not isinstance(maps, list) or not maps:
        raise ValueError("portals：game/data/maps.py MAPS 不是非空 list —— 无法做方碑挂载校验，拒绝导出")
    map_ids = {m.get("id") for m in maps if isinstance(m, dict)}

    out: dict = {}
    for mid, ent in table.items():
        if not isinstance(mid, str) or not mid.strip():
            raise ValueError(f"portals：{PORTALS_SRC} 的键 {mid!r} 不是非空字符串 —— 拒绝导出")
        if not isinstance(ent, dict):
            raise ValueError(f"portals：{PORTALS_SRC}[{mid!r}] 不是 dict（{type(ent).__name__}）—— 拒绝导出")
        for f in ("name", "icon"):
            v = ent.get(f)
            if not isinstance(v, str) or not v.strip():
                raise ValueError(f"portals：{PORTALS_SRC}[{mid!r}].{f} 不是非空字符串（{v!r}）—— 拒绝导出")
        if mid not in map_ids:
            raise ValueError(f"portals：方碑 {mid!r} 在 MAPS 里找不到同名地图（悬空方碑 = 玩家走不到）"
                             f"—— 拒绝导出")
        out[mid] = dict(ent)          # 字段顺序原样

    if len(out) != len(table):
        raise ValueError(f"portals：条目数不符（源 {len(table)} / 出 {len(out)}）—— 拒绝导出")
    return sort_table(out)


DOMAINS = {
    "portals": derive_portals,
}
