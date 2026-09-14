# -*- coding: utf-8 -*-
"""域插件：世界·探索 + 副本数据线（批 B4，一个文件独占一路）。

三个域（本文件即是它们的证据与口径的唯一落点）
==============================================

① `subareas` —— 子区域内容域（628 条）
    真源：`game/data/subareas.py:4 SUBAREAS`（**import 后的运行时态**；包 import 期
    `game/data/_assembly.py:94-97` 把三张 `EXTRA_SUBAREAS`（= mesh_rooms_south/west_north/east_abyss
    的网状房间，id 自 `_4` 起）就地 extend 进同一批列表）→ 121 图 / **628 子区域**，
    子区域 id 全图唯一（实测 628/628，0 重复）。
    本域 = 每个子区域一条，键 = 子区域 id，条目 = 源 dict **原样**（浅拷贝）+ 注入 `map`（所在图 id）。
    与已进包的 `maps` 域的关系（**不重复造表**，这是本域最要紧的一条边界）：
        maps 域（`derive_maps`）条目 = `{name, topology, roles, nodes:[{id,name,role}], links?, gate?}`
        —— 只取「形状」，节点上只留 id/name/type 三个标量；子区域的
        `icon/desc/lv/npcs/monsters/elite/boss/funcs/shop/healer/hidden/reveal` **一个都没进包**。
        本域就导这些内容字段，两域字段集只交于 `id/name/type`（nodes[].role = 本域 type 的原样照抄）。
        所以：**maps 域管「图内形状」，subareas 域管「房间内容」，同源不同投影，无第二个定义点。**
    与 `pois` 域的关系：pois 域键 = `「地图id:子区域id」`（房间地址）→ POI 引用行；本域键 = 子区域 id。
        两域合起来才是一个房间（本域=房间本身，pois 域=房间上挂的交互点），键空间与语义都不同。

② `instance_investigation` —— 副本通关后调查点（90 条）
    真源：`game/data/instance_investigation.py:60 INVESTIGATION_POINTS`
    （key = 副本 id，与 `game/data/instances.py` 的 INSTANCES key 对齐；value = 调查点 dict 列表）
    → 22 本 / **90 个调查点**（模块尾部汇总常量 `INVESTIGATION_COUNT=90` 同值；
    文件头 docstring 写的「86 个」是旧数，实测 90 —— 本域以表为准）。
    本域 = 每个调查点一条，键 = 调查点 id（`inv_<副本短名>_<序号>`，实测 90/90 全局唯一），
    条目 = 源 dict **原样** + 注入 `instance`（所在副本 id）。
    与 `instances` 域的关系：instances 域 27 本的 stages/boss/waves **不含**调查点
    （`derive_instances` 的 docstring 明列 `INVESTIGATION_POINTS` 为「未导出（属别的域）」）
    → 本域是它在包内唯一的落点，零重叠。
    未导出（本域有意不碰）：模块级 `INVESTIGATE_COLLECT_SAMPLES`（5 条全游戏收藏样本）与
    三个概率常量 `INVESTIGATE_BP_CHANCE/RUNE_CHANCE/COLLECT_CHANCE`（0.25/0.15/0.03）——
    它们是**命令层缺省值**（不是逐点数据；90 个调查点里 0 个覆写这三个键），
    与条目形状不同，硬塞会让「一条 = 一个调查点」的契约失效。见报告缺口节。

③ `worlds` —— 世界（大陆·区域）级地图元数据（121 条）
    真源：`game/data/maps.py:3 MAPS`（import 后的运行时态；装配期只多注入 `subareas` 一个键，
    见 `_assembly.py:135`）→ **121 条**，id 唯一。
    本域 = 一图一条，键 = 图 id，条目 = MAPS 条目**原样**，**唯一剔除 `subareas`**
    （那是装配期注入的嵌套子区域列表，内容与 `subareas` 域的条目**是同一批对象**
     → 留着就是跨域重复一份内容；剔除后本域 0 字段与 subareas 域重叠）。
    为什么值得单开（maps 域 docstring 亲口留的缺口）：maps 域语义是「形状」，明确不导
    地图级元数据（`lv/region/chapter/area/area_name/desc/type/shop/healer/hidden` +
    世界层实体引用 `monsters/elite/boss/npcs` + 副本配置 `dungeon`）——
    「要导需另立域」。本域就是那个域：`region`（10 个境/大陆）→ `chapter` → `area` 的
    世界分层 + 地图说明文案 + 类型/等级/设施开关 + 27 张副本图的 `dungeon` 配置
    （`{no_exit, discovery_agro, boss_room, on_clear}`）。
    与 `instances` 域的关系：本域的 `dungeon` 是**地图侧**开图配置（no_exit/agro/boss_room），
    instances 域是副本内容（boss/waves/stages）—— 字段不同、消费端不同，不重复。
    实测：地图级 `monsters/elite/boss/npcs` 121/121 全为空（内容已全部下沉到子区域层，
    `_assembly.py:207` 起从 SUBAREAS 收集）→ 本域保留这几个空槽位是「形状原样」，
    不是没导（丢键会让编辑器把「空」和「没有这个概念」混淆）。

不导（本批经核实**已是包内另一份**，重复导 = 造第二个定义点；证据见报告）
==========================================================================
  * `game/data/dungeon_pois.py:22 DUNGEON_POI_MOUNTS`（55 键 / 66 POI）→ 已 100% 在
    `pois` 域（`pois.json` 里 `source="dungeon"` 55 行、POI dict 逐字段相同）。
  * `game/data/instance_stage_maps.py:17 INSTANCE_STAGE_MAPS`（22 本 / 66 层）+
    `:634 INSTANCE_STAGE_NPCS`（6 条）→ 已 100% 在 `instances` 域（`instances.json` 的
    `stages[].desc/pois/npcs/secret` 与源逐层逐值相同，实测 0 差异）。
  * `game/core/worlds.py`（286 行）→ **没有静态数据表**：全是运行时大陆实例生命周期
    （`instance_worlds` 字典 + create/destroy/persist/cleanup，主大陆常量 `"mainland"` 是
    代码里的字面量，不是表）。「大陆」这一层的**内容侧数据**只有 MAPS 的 `region` 字段，
    已随本域（worlds）进包 → 该模块无可搬运的条目。

保真纪律（三域共用）
====================
  * 条目**原样**：不补默认值（`hidden/reveal` 只在 198 条上有，不替其余 430 条补）、
    不改类型（`monsters/elite/boss` 是 6 元组，由宿主 `json_clean()` 统一往返成 list，
    正是落盘形状）、不展开任何引用串（`npcs`/`monsters`/`materials`/`boss_room` 一律留原文）。
  * 注入字段只有两个：subareas 的 `map`、instance_investigation 的 `instance`
    —— 与 `derive_pois` 注入 `map/subarea/source` 同法（把键里已有的信息摊平）。
  * 外层键一律 `sort_table()` 字典序（幂等）；条目内部字段顺序 = 源顺序。
  * 形状门禁：任何一条键/值形状不对都 **raise**（拒绝导出），不静默丢条目 ——
    包侧「少一条」的表现是编辑器静默少一页，最难查。

实测（2026-09-13，游戏仓 master 真跑）
=====================================
  * subareas 628 条（121 图全覆盖，0 图缺子区域，0 悬空/0 重复 id）
  * instance_investigation 90 条（22 本全覆盖，90/90 id 唯一，22/22 副本 key 命中 INSTANCES）
  * worlds 121 条（与 MAPS 全等；剔除 `subareas` 后无任何字段与 subareas 域重叠）
"""

import sys

from _helpers import import_game_data, sort_table, as_table


def _game_data(src_root):
    """import 游戏仓 `game.data` **包本身** —— 返回**装配后**的包命名空间。

    为什么不能只读 `game/data/<mod>.py` 模块：`game/data/_assembly.py:94-97` 在**包 import 期**
    把三张 `EXTRA_SUBAREAS`（网状房间，id 自 `_4` 起）就地 extend 进 `SUBAREAS`。
    走 `import_game_data("subareas")` 时 Python 会先执行 `game.data.__init__`（= 跑装配），
    因此 import 之后 `sys.modules["game.data"]` 就是宿主 `_import_data_package()` 的同一份
    命名空间（`SUBAREAS` 与子模块里是**同一个对象**，装配就地改的就是它）。
    """
    import_game_data("subareas", src_root)      # 触发 game.data.__init__ → _assembly 装配
    return sys.modules["game.data"]


# =============================================================================
# ① subareas —— 子区域内容（628 条）
# =============================================================================
def derive_subareas(src_root: str = None) -> dict:
    """子区域域：读装配后的 `SUBAREAS`，一条 = 一个子区域（键 = 子区域 id）。

    真源：`game/data/subareas.py:4 SUBAREAS`（+ 装配期 `_assembly.py:94-97` 并入的
    `_4` 起网状房间）→ 121 图 / 628 子区域。
    条目形状 = 源 dict 原样 + 注入 `map`（所在图 id）；字段（实测 628 条全量）：
        id/name/icon/desc/type/lv  (str/str/str/str/str/int，628/628)
        npcs    list[str]                 628/628（NPC id 引用串，未展开）
        monsters list[6 元组]             628/628（内联怪元组：id/名/role/lv/技能id表/掉落名表）
        elite   None | 6 元组             530 None / 98 有
        boss    None | 6 元组             599 None / 29 有
        funcs   list[str]                 628/628（能力词，11 个取值）
        shop/healer bool                  628/628
        hidden  bool                      只在 198 条上（其余 430 条**没有这个键**）
        reveal  None | str                只在 198 条上（148 None / 50 str，如 "explore:8"）
    形状门禁（任一不成立 → raise，拒绝导出）：
        * SUBAREAS 非空 dict；MAPS 非空 list；两者的 key 集合**必须相等**（0 例外）；
        * 每图的行是非空 list；每行是有非空 str `id`/`name` 的 dict；
        * 子区域 id **全局唯一**（编辑器按 id 引用；重名会静默丢一条）。
    """
    ns = _game_data(src_root)
    subareas = as_table(getattr(ns, "SUBAREAS", None), "game.data.SUBAREAS")
    maps = getattr(ns, "MAPS", None)
    if not isinstance(maps, list) or not maps:
        raise ValueError("game.data.MAPS 不是非空 list —— 源形状变了，拒绝导出")

    map_ids = []
    for m in maps:
        if not isinstance(m, dict):
            raise ValueError(f"MAPS 里有非 dict 条目：{m!r} —— 源形状变了，拒绝导出")
        mid = m.get("id")
        if not isinstance(mid, str) or not mid:
            raise ValueError(f"MAPS 条目缺 id（或不是非空 str）：{m!r}")
        map_ids.append(mid)

    if set(subareas) != set(map_ids):
        raise ValueError(
            f"SUBAREAS 与 MAPS 的图 id 集合不相等："
            f"只在这边 {sorted(set(subareas) - set(map_ids))[:10]} / "
            f"只在那边 {sorted(set(map_ids) - set(subareas))[:10]} —— 源形状变了，拒绝导出")

    out: dict = {}
    for mid in map_ids:
        rows = subareas[mid]
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"SUBAREAS[{mid!r}] 不是非空 list —— 源形状变了，拒绝导出")
        for sa in rows:
            if not isinstance(sa, dict) or not isinstance(sa.get("id"), str) or not sa["id"]:
                raise ValueError(f"SUBAREAS[{mid!r}] 里有非 dict / 缺 id 的子区域：{sa!r}")
            if not isinstance(sa.get("name"), str) or not sa["name"]:
                raise ValueError(f"SUBAREAS[{mid!r}]['{sa['id']}'] 缺 name —— 拒绝导出")
            sid = sa["id"]
            if sid in out:
                raise ValueError(
                    f"子区域 id 重复：{sid!r}（已属 {out[sid]['map']!r}，又来 {mid!r}）—— "
                    f"外层键会丢条目，请先决定归属再导出")
            entry = dict(sa)          # 浅拷贝：不让条目与 MAPS[mid]["subareas"] 里的对象别名
            entry["map"] = mid        # 导出期注入（源行里没有）：把键里已有的归属摊平
            out[sid] = entry
    return sort_table(out)


# =============================================================================
# ② instance_investigation —— 副本通关后调查点（90 条）
# =============================================================================
def derive_instance_investigation(src_root: str = None) -> dict:
    """副本调查点域：读 `INVESTIGATION_POINTS`，一条 = 一个调查点（键 = 调查点 id）。

    真源：`game/data/instance_investigation.py:60 INVESTIGATION_POINTS`
    —— `{副本 id: [调查点 dict, ...]}`（22 本 / 90 个；模块尾部 `INVESTIGATION_COUNT=90` 同值）。
    条目形状 = 源 dict 原样（实测 90 条全量只有 4 个键）+ 注入 `instance`（所在副本 id）：
        id str / name str / hint str / materials list[str]   —— 90/90 齐
        （文件头声明的可选键 `bp_chance`/`rune_chance`/`collect_chance`/`collect`
          在 90 条里**0 次出现**；缺省值在命令层常量，不在表里 → schema 备位但不补）
    形状门禁（任一不成立 → raise）：副本 id **必须**命中 INSTANCES（悬空 = 编辑器里点不进去）、
        行是非空 list、调查点 id 非空 str 且**全局唯一**、name/hint 非空 str、materials 非空 list[str]。
    """
    ns = _game_data(src_root)
    points = as_table(getattr(ns, "INVESTIGATION_POINTS", None),
                      "game.data.INVESTIGATION_POINTS")
    instances = getattr(ns, "INSTANCES", None)
    if not isinstance(instances, dict) or not instances:
        raise ValueError("game.data.INSTANCES 不是非空 dict —— 源形状变了，拒绝导出")

    out: dict = {}
    for iid in sorted(points):
        if iid not in instances:
            raise ValueError(
                f"调查点表的副本 id {iid!r} 不在 INSTANCES 里 —— 引用悬空"
                f"（文件头声明「必须与 INSTANCES key 一致」），拒绝导出")
        rows = points[iid]
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"INVESTIGATION_POINTS[{iid!r}] 不是非空 list —— 拒绝导出")
        for p in rows:
            if not isinstance(p, dict) or not isinstance(p.get("id"), str) or not p["id"]:
                raise ValueError(f"INVESTIGATION_POINTS[{iid!r}] 里有缺 id 的条目：{p!r}")
            if not isinstance(p.get("name"), str) or not p["name"]:
                raise ValueError(f"调查点 {p['id']!r} 缺 name —— 拒绝导出")
            if not isinstance(p.get("hint"), str) or not p["hint"]:
                raise ValueError(f"调查点 {p['id']!r} 缺 hint —— 拒绝导出")
            mats = p.get("materials")
            if not isinstance(mats, list) or not mats:
                raise ValueError(f"调查点 {p['id']!r} 的 materials 不是非空 list —— 拒绝导出")
            for x in mats:
                if not isinstance(x, str) or not x:
                    raise ValueError(f"调查点 {p['id']!r} 的 materials 里有非 str：{x!r}")
            pid = p["id"]
            if pid in out:
                raise ValueError(f"调查点 id 重复：{pid!r} —— 外层键会丢条目，拒绝导出")
            entry = dict(p)           # 浅拷贝
            entry["instance"] = iid   # 导出期注入（源行里没有）
            out[pid] = entry
    return sort_table(out)


# =============================================================================
# ③ worlds —— 世界（大陆·区域）级地图元数据（121 条）
# =============================================================================
def derive_worlds(src_root: str = None) -> dict:
    """世界域：读 `MAPS`，一条 = 一张图的**世界级元数据**（键 = 图 id）。

    真源：`game/data/maps.py:3 MAPS`（import 后运行时态）→ 121 条。
    条目 = MAPS 条目原样，**唯一剔除 `subareas`**（装配期注入的嵌套子区域列表，
    `_assembly.py:135`；其内容与 `subareas` 域条目为同一批对象 → 留着就是跨域重复）。
    字段（实测 121/121 全量）：
        id/name str · lv int · region str（10 个境）· chapter int · area str · area_name str
        desc str · type str（野外 68 / 副本 27 / 城镇区域 24 / 隐藏区域 2）
        shop bool（24 true）· healer bool（23 true）· hidden bool（2 true）
        monsters/elite/boss/npcs —— 121/121 全为空（内容已下沉子区域层，形状原样保留）
        dungeon dict —— **只在 27 张副本图上**，键恒为 {no_exit, discovery_agro, boss_room, on_clear}
    形状门禁（任一不成立 → raise）：
        * MAPS 非空 list、每图 id 非空 str 且唯一；
        * 每图必须有 `subareas`（装配期注入的标记）—— 没有说明 _assembly 变了，拒绝导出；
        * `dungeon` 若存在必须是非空 dict（不让形状漂移静默过）。
    """
    ns = _game_data(src_root)
    maps = getattr(ns, "MAPS", None)
    if not isinstance(maps, list) or not maps:
        raise ValueError("game.data.MAPS 不是非空 list —— 源形状变了，拒绝导出")

    out: dict = {}
    for m in maps:
        if not isinstance(m, dict):
            raise ValueError(f"MAPS 里有非 dict 条目：{m!r} —— 拒绝导出")
        mid = m.get("id")
        if not isinstance(mid, str) or not mid:
            raise ValueError(f"MAPS 条目缺 id（或不是非空 str）：{m!r}")
        if mid in out:
            raise ValueError(f"图 id 重复：{mid!r} —— 外层键会丢条目，拒绝导出")
        if "subareas" not in m:
            raise ValueError(
                f"MAPS[{mid!r}] 没有装配期注入的 `subareas` 键 —— `_assembly.py:135` 变了？"
                f"（本域剔除嵌套子区域的依据没了）拒绝导出")
        dun = m.get("dungeon")
        if dun is not None and (not isinstance(dun, dict) or not dun):
            raise ValueError(f"MAPS[{mid!r}].dungeon 不是非空 dict —— 源形状变了，拒绝导出")

        entry = {k: v for k, v in m.items() if k != "subareas"}
        out[mid] = entry
    return sort_table(out)


DOMAINS = {
    "subareas": derive_subareas,
    "instance_investigation": derive_instance_investigation,
    "worlds": derive_worlds,
}
