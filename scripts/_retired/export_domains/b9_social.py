# -*- coding: utf-8 -*-
"""B9 线 L3（社交/公会）域插件 —— `titles`（称号表）+ `guild`（公会数据表）真源 → 包 JSON。

契约见 `scripts/export_domains/README.md`：本文件只**读真源、返回内存表**，落盘由宿主
（`scripts/export_game_package.py`：UTF-8 / LF / indent=2 / 原子替换 + `sort_table` 外层键字典序）统一做。
**不许 import `export_game_package`**（宿主会扫本目录 → 循环导入）。公用小工具走 `_helpers.py`。

================================================================================
域：`titles` 称号表 —— 真源 `game/data/titles.py:3 TITLES`（list，实测 **68** 条）
================================================================================
| 消费侧（**只读真源，不改**） | 用法 |
|---|---|
| `game/commands/economy.py:5051/5105/5138` | `for i, t in enumerate(C.TITLES)` + `C.TITLES[i]` —— **按下标**取称号（成就面板「已获称号」行） |
| `game/core/stat_bonus.py:98/108/115` | 同款按下标遍历 + `t.get("bonus")` 累加 + 同名去重 |
| `game/reward.py:99/101` | 按 `id` / `name` 反查称号条目（发奖提示） |
| `game/data/collection_book.py` | 满套称号名引用（字符串引用，不展开） |

⭐ **顺序不变式**：真源是 **list**，消费侧**按下标**取（`C.TITLES[i]`）→ 下标即语义。
包域是 dict（外层键字典序落盘），顺序没处存 → 导出期给每条注入 `seq`（1 基下标 = 真源插入序），
读侧按 `seq` 还原。没有 `seq` = 称号顺序漂移 = 逐字节不等价。

映射口径：一条 = 一个称号，键 = `id`；条目字段**原样**（`id`/`name`/`desc`/`bonus`/`effect` 有就有、
没有就没有，**不补默认值**）+ 导出期注入的 `seq`。`bonus` 里的 `crit` 是小数（如 0.02），原样落盘。

================================================================================
域：`guild` 公会数据表 —— 真源 `game/data/guild.py`（4 张表）
================================================================================
| 真源 | 行 | 本域落点 |
|---|---:|---|
| `:23 GUILD_ROLES` | 23-28 | `roles.map`（`{role: [职位名, 图标]}`，**原样**：真源是 tuple，JSON 只能是 list） |
| `:30 GUILD_APPOINTABLE` | 30 | `roles.appointable`（会长可任命的 role 列表） |
| `:35 GUILD_SHOP_ITEMS` | 35-88 | `shop_items`（**键 = 商品编号（int → JSON 字符串键）**；6 条） |
| `:91 GUILD_SKILLS` | 91-113 | `skills`（键 = 技能 key；3 条） |
| `:4 GUILD_CONFIG` | 4-21 | **不进包**（数值配置归 L7 的 `*_config` 面；由宿主 `bind_host(config=…)` 注入给包内模块） |

消费侧（**只读真源，不改**）：`game/commands/social.py`（公会面板/商店/技能/任命，B9-L3 起改读
包内 `content/social_guild.py`）；`tests/test_v116_guild_shop.py:55`（`_G.GUILD_ROLES.get("leader")[1]`）。

⚠️ 已知坑：`shop_items` 的键真源是 **int**（1..6），JSON 只有字符串键 → 包内
`content/social_guild.py` 读时**还原 int**（与 `ENHANCE_TABLE` 同族；不还原 = `get(编号)` 恒 None
= 「公会商店 <编号>」全部报「没有第 N 件商品」）。

留作引用 / 未进包（见 B9-L3 报告 §缺口）
    `GUILD_CONFIG`（14 个数值键）→ 常量/配置模块归 L7，本域不搬；包内模块按注入值用。
    `game/services/guild.py` 的编排逻辑 → 已进包（`content/social_guild.py`），不是数据域的事。
"""
from _helpers import import_game_data, sort_table, as_table

TITLES_SRC = "game/data/titles.py:3 TITLES"
GUILD_SRC = "game/data/guild.py"


def derive_titles(src_root: str = None) -> dict:
    """`titles` 域：`TITLES`（list）→ `{id: 条目}`，每条注入 `seq`（1 基 = 真源插入序）。

    顺序是语义（消费侧按下标取），见模块 docstring。空表 / 非 dict 条目 / id 缺失或重复 → raise。
    """
    mod = import_game_data("titles", src_root) if src_root else import_game_data("titles")
    lst = getattr(mod, "TITLES", None)
    if not isinstance(lst, list) or not lst:
        raise ValueError(f"titles：{TITLES_SRC} 不是非空 list（得到 {type(lst).__name__}）—— 拒绝导出")
    out: dict = {}
    for i, ent in enumerate(lst, 1):
        if not isinstance(ent, dict):
            raise ValueError(f"titles：{TITLES_SRC}[{i - 1}] 不是 dict（{type(ent).__name__}）")
        tid = ent.get("id")
        if not isinstance(tid, str) or not tid:
            raise ValueError(f"titles：{TITLES_SRC}[{i - 1}] 缺 id —— 拒绝导出（键空间要稳）")
        if tid in out:
            raise ValueError(f"titles：id {tid!r} 重复（第 {out[tid]['seq']} / {i} 条）—— 拒绝导出")
        row = dict(ent)
        row["seq"] = i                      # 源列表序（消费侧按下标取，丢序 = 逐字节不等价）
        out[tid] = row
    return sort_table(out)


def derive_guild(src_root: str = None) -> dict:
    """`guild` 域：公会四表 → `{roles: {map, appointable}, shop_items, skills}`（原样搬运）。

    条目字段**一个不改**（不补默认值、不改类型）；`shop_items` 的 int 键由落盘器 json 往返成字符串键
    （包内读时还原 int，见模块 docstring ⚠️）。空表 → raise（空表在编辑器里 = 0 条且不报错，静默失效）。
    """
    mod = import_game_data("guild", src_root) if src_root else import_game_data("guild")
    roles = as_table(getattr(mod, "GUILD_ROLES", None), f"{GUILD_SRC}:23 GUILD_ROLES")
    appointable = getattr(mod, "GUILD_APPOINTABLE", None)
    shop = as_table(getattr(mod, "GUILD_SHOP_ITEMS", None), f"{GUILD_SRC}:35 GUILD_SHOP_ITEMS")
    skills = as_table(getattr(mod, "GUILD_SKILLS", None), f"{GUILD_SRC}:91 GUILD_SKILLS")
    for name, tbl in (("GUILD_ROLES", roles), ("GUILD_SHOP_ITEMS", shop), ("GUILD_SKILLS", skills)):
        if not tbl:
            raise ValueError(f"guild：{GUILD_SRC} {name} 是空表 —— 源形状变了/表被删，拒绝导出")
    if not isinstance(appointable, (list, tuple)) or not appointable:
        raise ValueError(f"guild：{GUILD_SRC}:30 GUILD_APPOINTABLE 不是非空 list/tuple —— 拒绝导出")

    role_map: dict = {}
    for role, val in roles.items():
        if not isinstance(val, (list, tuple)) or len(val) != 2:
            raise ValueError(f"guild：GUILD_ROLES[{role!r}] 不是 [职位名, 图标]（得到 {val!r}）"
                             " —— 源形状变了，拒绝导出")
        role_map[role] = list(val)           # tuple → list（JSON 只有 list；读侧解包语义不变）

    shop_out: dict = {}
    for num, ent in shop.items():
        if not isinstance(ent, dict):
            raise ValueError(f"guild：GUILD_SHOP_ITEMS[{num!r}] 不是 dict（{type(ent).__name__}）")
        shop_out[num] = ent                  # 键原样（int；落盘器 json 往返成字符串键）

    # B14-3（2026-09-14）：`GUILD_CONFIG`（11 个数值键，`game/data/guild.py:3`）进本域 ——
    # 它是「公会数值配置」，而本域是本模块**唯一**的公会域（一条 = 一组数据表）。
    # ⚠ 本域 `$defs.guild_table` **不写 required** ⇒ 新增一行 `config` 不会触发「每条都要有
    #   实体字段」的校验（`guild.schema.json` 的 propertyNames 同步放行 `config`）。
    # 真实消费方：包内 `content/social_guild.py`（公会经验加成）/ `content/settlement.py`
    # （结算时的公会加成），过去由宿主 `bind_host(config=C.GUILD_CONFIG)` 注入 → 现改为读本域。
    cfg = getattr(mod, "GUILD_CONFIG", None)
    if not isinstance(cfg, dict) or not cfg:
        raise ValueError(f"guild：{GUILD_SRC}:3 GUILD_CONFIG 不是非空 dict —— 源形状变了，拒绝导出")

    return {"roles": {"map": role_map, "appointable": list(appointable)},
            "shop_items": shop_out,
            "skills": skills,
            "config": cfg}


DOMAINS = {
    "titles": derive_titles,
    "guild": derive_guild,
}
