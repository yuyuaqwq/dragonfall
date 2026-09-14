# -*- coding: utf-8 -*-
"""周常 · 修炼塔线（B8.2 线1）域插件 —— `weekly_quests` 域的真源 → 包 JSON。

契约见 `scripts/export_domains/README.md`：本文件只**读真源、返回内存表**，落盘由宿主
（`scripts/export_game_package.py`：UTF-8 / LF / indent=2 / 原子替换 + `sort_table` 外层键字典序）统一做。
**不许 import `export_game_package`**（宿主会扫本目录 → 循环导入）。公用小工具走 `_helpers.py`。

================================================================================
域 1：`weekly_quests` 周常悬赏池 —— 12 条（键 = 悬赏名）
================================================================================
真源（2026-09-13 实测，行号以当时文件为准）：
    `game/data/weekly_quests.py:22  WEEKLY_QUESTS`         **list**，12 条（表长实测 12 / 文件 155 行）
    `game/data/weekly_quests.py:152 WEEKLY_PICK = 3`       常量：每周自动发布条数
    `game/data/weekly_quests.py:155 WEEKLY_MIN_LV = 50`    常量：悬赏板解锁等级

消费者（游戏侧；导出只搬运不改语义）：
    `game/commands/weekly.py:49 _assign_week(player)`  —— 按等级过滤后**取列表前 3 条**
        （注释写明「池内顺序取前 3（同周全员一致）」→ **列表插入序 = 玩家可见的玩法语义**）
    `game/commands/weekly.py:135 weekly_list`          —— `list(C.WEEKLY_QUESTS)` 按插入序分页（4 条/页）
    `game/services/weekly_progress.py`（本线已下沉 `content/flow/weekly_progress.py`）

映射口径
    * **形状：真源是 list、包域是 dict** → 键取条目的 `name`（悬赏名，实测 12/12 互异，
      且它就是游戏侧任务 dict 的键 `tasks[q["name"]]` —— 身份即名字，不另造 id）。
    * 条目**原样**进 JSON（不改类型、不补默认值、不动字段顺序、不展开引用串）。
      字段 census（12 条实测）：`name/desc/objective/reward_exp/reward_gold/min_lv/band/flavor` 全 12 条有；
      `objective` = `{kill_any|kill_elite|kill_boss: int}`（实测三键共 12 条，取值 2~45）；
      `band` 两个取值（Lv50-69 / Lv70+）；叶类型全 JSON 原生（str/int/dict）。
    * **唯一注入：`seq`**（1 基下标 = 在 `WEEKLY_QUESTS` 里的位置）。
      为什么必须注入：JSON 域的外层键由导出器**按字典序**排（宿主落盘约定），
      而消费者（`_assign_week` 取前 3 / `weekly_list` 分页）读的是**源列表插入序** ——
      不编码顺序 = 玩家看到的悬赏发布顺序与分页顺序漂移（渲染文案逐字变化）。
      守卫三条：① `name` 非空且 12/12 互异；② 条目里本来没有 `seq`（注入不许覆盖源真值）；
      ③ `seq` = 1..N 连续整数（导出期自证）。
    * 空/坏表 → `raise`（空表在编辑器里 = 「0 条」且不报错，是本项目最怕的静默失效）。

未进包（本域装不下，见报告 §遗留）
    `WEEKLY_PICK` / `WEEKLY_MIN_LV` 两个**常量**（不是条目形状）。当前落点：
    包内 `content/flow/weekly_progress.py` 的同名模块常量（逐字同值 + 真源行号），
    待「周常常量域」这类配置域归口（域名由 B8.2 主 agent 定）。
================================================================================
域 2（**未建**）：修炼塔塔表 `TRIAL_FLOORS`
================================================================================
真源：`game/data/trial_tower.py:112 TRIAL_FLOORS`（30 条；字段实测
    `floor/name/guard/lv/role/skills/hp_mult/atk_mult/reward_exp/reward_gold/desc`）
    + `:24 TRIAL_DAILY_LIMIT=3` / `:27 TRIAL_MIN_LV=70` / `:30 TRIAL_MAX_FLOOR=30`。
**本线不新建域**（域名归主 agent）→ 暂以**逐字端口**落在包内
`content/flow/tower_data.py`（真源整文件搬入，行号对照见该文件头）。
需要新域时：1 域 / 30 条 / 键 = `floor`（int → JSON 后为字符串，消费端要还原 int）。
"""

from _helpers import import_game_data, sort_table, as_table  # noqa: F401

# 真源位置（写进报错文案，便于定位「形状变了」时是哪个文件哪张表）
WEEKLY_SRC = "game/data/weekly_quests.py:22 WEEKLY_QUESTS"
WEEKLY_PICK_SRC = "game/data/weekly_quests.py:152 WEEKLY_PICK"
WEEKLY_MIN_LV_SRC = "game/data/weekly_quests.py:155 WEEKLY_MIN_LV"

SEQ_FIELD = "seq"          # 唯一注入字段（源列表插入序 = 玩法语义，见文件头）


def derive_weekly_quests(src_root: str = None) -> dict:
    """`weekly_quests` 域：`WEEKLY_QUESTS`（list，12 条）→ `{悬赏名: 条目+seq}`。

    真源是 **list**（不是 dict）—— 这是本线与 items/npcs 等字典域的唯一形状差异，
    处理见文件头「映射口径」：键 = `name`，唯一注入 = `seq`（1 基插入序）。
    """
    mod = import_game_data("weekly_quests", src_root) if src_root else import_game_data("weekly_quests")
    quests = getattr(mod, "WEEKLY_QUESTS", None)
    if not isinstance(quests, list):
        raise TypeError(f"weekly_quests：{WEEKLY_SRC} 应为 list（得到 {type(quests).__name__}）—— 源形状变了")
    if not quests:
        raise ValueError(f"weekly_quests：{WEEKLY_SRC} 是空表 —— 拒绝导出"
                         f"（空表 = 编辑器显示 0 条且不报错）")

    out: dict = {}
    for i, q in enumerate(quests, 1):
        if not isinstance(q, dict):
            raise ValueError(f"weekly_quests：{WEEKLY_SRC}[{i - 1}] 不是 dict（{type(q).__name__}）—— 拒绝导出")
        name = q.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"weekly_quests：{WEEKLY_SRC}[{i - 1}] 的 name 不是非空字符串（{name!r}）—— 拒绝导出")
        if name in out:
            raise ValueError(f"weekly_quests：悬赏名重复 {name!r}（键 = name，重名会静默吞一条）—— 拒绝导出")
        if SEQ_FIELD in q:
            raise ValueError(f"weekly_quests：源条目 {name!r} 已含字段 {SEQ_FIELD!r} —— 注入不许覆盖源真值")
        for f in ("desc", "band"):
            v = q.get(f)
            if not isinstance(v, str) or not v.strip():
                raise ValueError(f"weekly_quests：{WEEKLY_SRC}[{name!r}].{f} 不是非空字符串（{v!r}）")
        for f in ("reward_exp", "reward_gold", "min_lv"):
            v = q.get(f)
            if isinstance(v, bool) or not isinstance(v, int):
                raise ValueError(f"weekly_quests：{WEEKLY_SRC}[{name!r}].{f} 不是 int（{v!r}）")
        obj = q.get("objective")
        if not isinstance(obj, dict) or not obj:
            raise ValueError(f"weekly_quests：{WEEKLY_SRC}[{name!r}].objective 不是非空 dict（{obj!r}）")
        for k, v in obj.items():
            if not isinstance(k, str) or not k:
                raise ValueError(f"weekly_quests：{WEEKLY_SRC}[{name!r}].objective 的键 {k!r} 不是非空字符串")
            if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
                raise ValueError(f"weekly_quests：{WEEKLY_SRC}[{name!r}].objective[{k!r}] "
                                 f"不是正 int（{v!r}）—— 消费端按「第一个正 int」取达标数")
        entry = dict(q)                      # 字段顺序原样
        entry[SEQ_FIELD] = i                 # 唯一注入：源列表插入序（见文件头）
        out[name] = entry

    # 自证：注入的下标必须恰好是 1..N 连续整数（防上面循环被改动后静默错位）
    seqs = sorted(e[SEQ_FIELD] for e in out.values())
    if seqs != list(range(1, len(out) + 1)):
        raise ValueError(f"weekly_quests：注入的 {SEQ_FIELD} 不是 1..{len(out)} 连续整数（{seqs}）—— 拒绝导出")
    return sort_table(out)


DOMAINS = {
    "weekly_quests": derive_weekly_quests,
}
