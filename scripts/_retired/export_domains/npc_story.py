# -*- coding: utf-8 -*-
"""NPC · 剧情线五域导出器（B3）：`dialogues` / `quests` / `events` / `event_templates` / `tips`。

本文件 = `export_game_package.py` 的**域插件**（契约见 `scripts/export_domains/README.md`）：
暴露 `DOMAINS = {域: 派生函数}` 即被宿主自动并入注册表 → **不必改那个 2,900 行的宿主文件**。

================================================================================
为什么这五个域在一条线上（NPC·剧情线）
================================================================================
它们互为引用的**两端**，缺一端另一端的引用串就是悬空：

    dialogues  键 = NPC id（`npc_mayor` …）—— 挂在哪个人身上（引擎按 npc_id 取：
               `core/dialogue.py:18 C.DIALOGUES.get(npc_id)`）
    quests     条目 = 任务（`giver` = **NPC id**、`next` = **任务 id**）—— npcs 域的
               `quest` 字段 / npcs 的 `condition.quest_done` 都指向这里
    events     条目 = 探索随机事件（`template` = 事件模板名、`maps` = 地图 id）
    event_templates  键 = 模板名 —— events 的 `template` 指向这里
    tips       键 = 指令面板分类（`accept` / `bag` …）—— 面板底部随机提示池

导出纪律（与其它域一致，逐条遵守）
----------------------------------
1. **只读真源**，一个字都不解释：引用串（任务 id / 地图 id / 物品名 / flag / 职业 key）
   原样保留，导出期不展开、不校验闭合（闭合情况写进报告，不在数据里改）。
2. 条目**原样**进 JSON：不补默认值、不改类型、不重排条目内字段；`None` 与空数组照原样。
   注入字段只有「折叠真源表带来的信息损失」那一个（见各函数 docstring）。
3. 源形状变了 → **raise**（绝不静默导出空表/半张表；这是本项目最怕的故障）。
4. 派生函数不写任何文件（落盘由宿主统一做：UTF-8/LF/indent=2/原子替换）。

⚠️ import 顺序（踩过的坑，见宿主 `derive_panel_rules` docstring）：要 `game.core.*` 的派生函数
必须**先** `import_game_data(...)`（走完 `game/data/__init__.py` 的装配链）再 import core，
否则会撞 `ImportError: cannot import name 'build_index' from partially initialized module
'game.core.index'`（循环导入，2026-09-13 实测）。

实测（2026-09-13，本机；逐域条数 = 导出后包内条数）
----------------------------------------------------
    dialogues        39 条（= `DIALOGUES` 39 棵对话树；708 节点 / 1,973 选项）
    quests          238 条（70 主线 + 144 支线 + 24 每日；三表键空间零交集）
    events          146 条（100 探索 + 46 彩蛋；id 两池零交集）
    event_templates  19 条（= `TEMPLATES` 19 个注册模板，与模块内 19 个 `tpl_*` 函数 1:1）
    tips             58 条（= 58 个指令面板分类；池内共 333 条提示语，逐条 ≤20 字）
"""
from _helpers import REPO_ROOT, as_table, import_game_core, import_game_data, sort_table

__all__ = ["DOMAINS"]


# =============================================================================
# ① dialogues —— NPC 多轮对话树
# =============================================================================
def derive_dialogues(src_root: str = None) -> dict:
    """对话域（`dialogues`）：`game/data/dialogues.py:24 DIALOGUES` 全量（39 棵对话树）。

    真源 / 形状
    -----------
        `dialogue` = `{"start": <节点 id>, "nodes": {<节点 id>: <节点>}}`（键 = NPC id）。
        节点 = `{"text" | "texts" | "text_from", "options": [...]}`：
          · `text`      默认台词
          · `texts`     条件变体 `[{"need": {...}, "text": ...}]`（按序取第一个满足的，
                        实测 223 条变体全覆盖 `{need, text}` 两键）
          · `text_from` 实测只有 `"story"` —— 无变体命中时从**当前主线任务的 story** 自动生成
                        台词（`core/dialogue.py:107 node_text`，含 giver 校验防串台）
        选项 = `{"text", "next"}` + 可选 `need`（条件）/ `action`（副作用）/ `fail_next`
               （动作失败跳到哪）/ `side_menu`（动态子菜单，实测 4 条，只有 `{after}`）。
        `next` = 本树节点 id 或哨兵 `"__end__"`（`core/dialogue.py:129 is_end`）。

    导出映射
    --------
        键 = `DIALOGUES` 的键（NPC id，实测 `npc_*` 38 个 + `w_*` 1 个）；
        条目**原样**（`start` + `nodes` 两键）；**不注入任何字段**（单表、无折叠损失）。
        外层按 NPC id 字典序（幂等），条目内节点/选项顺序**保持源顺序**（引擎按序判定，
        变体顺序、选项顺序都是语义）。

    自检（源形状 / 悬空跳转 —— 实测全部通过，故这些检查不是装饰）
    -----------------------------------------------------------
        · 顶层必须恰好 `{start, nodes}` 两键；`nodes` 非空
        · `start` 必须在 `nodes` 里（不在 → 引擎 `dialogue_node()` 静默回退 start，
          玩家看到的是别的开场白，这类故障最查不出来）
        · 每个节点至少有一个 `text / texts / text_from`（都没有 → `node_text()` 念默认
          `……` 占位符）
        · 每个选项有 `text` + `next`；`next` ∈ 本树节点 ∪ `{"__end__"}`（实测 1,973/1,973）
    """
    mod = import_game_data("dialogues", src_root or REPO_ROOT)
    tbl = as_table(getattr(mod, "DIALOGUES", None), "game/data/dialogues.py:24 DIALOGUES")

    out: dict = {}
    for npc_id, entry in tbl.items():
        if not isinstance(npc_id, str) or not npc_id:
            raise ValueError(f"dialogues：键不是非空 str：{npc_id!r} —— 源形状变了，拒绝导出")
        if not isinstance(entry, dict):
            raise ValueError(
                f"dialogues：{npc_id!r} 不是 dict（{type(entry).__name__}）—— 源形状变了，拒绝导出")
        if set(entry) != {"start", "nodes"}:
            raise ValueError(
                f"dialogues：{npc_id!r} 顶层字段是 {sorted(entry)}（期望 ['nodes', 'start']）"
                f"—— 源形状变了，拒绝导出")
        nodes = entry["nodes"]
        if not isinstance(nodes, dict) or not nodes:
            raise ValueError(f"dialogues：{npc_id!r}.nodes 不是非空 dict —— 拒绝导出（空树 = 编辑器 0 节点）")
        start = entry["start"]
        if start not in nodes:
            raise ValueError(
                f"dialogues：{npc_id!r} 的 start={start!r} 不在 nodes 里 —— "
                f"引擎 core/dialogue.py:24 会静默回退 start 节点，拒绝导出")
        for nid, node in nodes.items():
            if not isinstance(nid, str) or not isinstance(node, dict):
                raise ValueError(f"dialogues：{npc_id!r}.nodes[{nid!r}] 形状不对（需 str→dict）—— 拒绝导出")
            if not ({"text", "texts", "text_from"} & set(node)):
                raise ValueError(
                    f"dialogues：{npc_id!r}.nodes[{nid!r}] 既无 text / texts / text_from —— "
                    f"core/dialogue.py:107 node_text 会念默认占位符『……』，拒绝导出")
            opts = node.get("options") or []
            if not isinstance(opts, list):
                raise ValueError(f"dialogues：{npc_id!r}.nodes[{nid!r}].options 不是 list —— 拒绝导出")
            for i, opt in enumerate(opts):
                if not isinstance(opt, dict) or "text" not in opt or "next" not in opt:
                    raise ValueError(
                        f"dialogues：{npc_id!r}.nodes[{nid!r}].options[{i}] 缺 text/next"
                        f"（实为 {sorted(opt) if isinstance(opt, dict) else type(opt).__name__}）—— 拒绝导出")
                nxt = opt["next"]
                if nxt not in nodes and nxt != "__end__":
                    raise ValueError(
                        f"dialogues：{npc_id!r}.nodes[{nid!r}].options[{i}].next={nxt!r} "
                        f"既不是本树节点也不是哨兵 \"__end__\" —— 悬空跳转，拒绝导出")
        out[npc_id] = entry
    return sort_table(out)


# =============================================================================
# ② quests —— 主线 / 支线 / 每日
# =============================================================================
# (符号, 注入的 source, 该表是否有 id 键, 源位置)
_QUEST_TABLES = (
    ("MAIN_QUESTS", "main", True, "game/data/quests.py:3 MAIN_QUESTS"),
    ("SIDE_QUESTS", "side", True, "game/data/quests.py:939 SIDE_QUESTS"),
    ("DAILY_QUESTS", "daily", False, "game/data/quests.py:3325 DAILY_QUESTS"),
)


def derive_quests(src_root: str = None) -> dict:
    """任务域（`quests`）：`game/data/quests.py` 三张任务表**合成一张扁平表**（一条 = 一个任务）。

    ============================ 真源是哪三张表 ============================
        `game/data/quests.py:3     MAIN_QUESTS`    主线 70 条（12 章 × 5~6 条，id `q1_1` … `q12_6`）
        `game/data/quests.py:939   SIDE_QUESTS`    支线 144 条（id `s1` … `s121` + 公会告示 `hq5*`~`hq8*`）
        `game/data/quests.py:3325  DAILY_QUESTS`   每日 24 条（**没有 id**，见下）

        ★ 读的是 **import 之后的运行时表**（list 字面量本身，无 `update` 叠加）。

    ============================ 为什么合成一张表 ============================
    1. 三张表在引擎侧是**同一族**（同一形状的任务条目、同一套 objective/reward 语义），
       而「找一个任务」的通用写法是**按表扫 id**：`services/quests_flow.py:140
       next((q for q in C.MAIN_QUESTS if q["id"] == mid), None)`（20+ 处，主线扫 MAIN、
       支线扫 SIDE）—— 一张 keyed 表才是编辑器的域形态（一条一条改）。
    2. **键空间实测零交集**（`q*` / `s*`+`hq*` / 每日用名）：合并一条都不丢；真撞了本函数
       `raise`（绝不静默覆盖）。
    3. 折掉「来自哪张表」那一层 → 注入 `source`（`main` / `side` / `daily`），
       与 `derive_npcs` 折三张 NPC 表、`derive_skills` 折三张技能表同法。

    ============================ 键口径（★ 唯一一处不齐） ============================
        MAIN/SIDE：键 = `id`（80% 引用串的落点就是它）。
        DAILY   ：**源侧根本没有 `id`** —— 引擎认的是**名字**：
                  `services/quests.py:54 next((q for q in C.DAILY_QUESTS
                  if q.get("name") == (dq or {}).get("name")), None)`，
                  `services/quests.py:200` 也是按 name 过滤的池。
                  所以每日任务的键 = `name`（实测 24 个名字互不重复）—— **不造 id**
                  （造 `daily_1` 之类会在引擎按名匹配时对不上，那是替源侧决定标识）。
                  键里出现中文不是新事：包内 `skills.json`（238 个中文键）、`drop_pools.json`
                  ／`elite:<中文名>`（363 个）已是同款。

    ============================ 注入字段（只这一个） ============================
        source : "main" | "side" | "daily" —— 该条目来自哪张真源表（缺省不写别的）。
        源条目若已有同名键 → `raise`（实测 238 条零同名）。

    ============================ 留作引用、不展开 ============================
        giver             NPC id（实测 91 个不同值，**全部**落在本包 npcs 域 431 键里）
        next / chain      后续任务 id（同域内：`next` 实测 70 个非空值全部命中本域键，
                          另有 1 条 `q12_6.next = null`（终章、脚本链终点，原样保留不补默认值））
        map               地图 id（支线 144 条都有；实测全部落 maps 域）
        objective.*       `kill`/`collect`/`talk`/`explore`/`find`/`use`/`kill_any`/
                          `kill_elite`/`kill_boss` 等 —— 值是**怪物中文名 / NPC id / 地图 id /
                          物品名**（跨域引用，原样保留）
        reward_item       str 或 list（119 单值 / 4 列表=随机抽一个）、`eq:名称` 前缀（名册装备）、
                          `reward_pet` / `reward_mount` / `title` / `unlock` / `require_stats` /
                          `progress_text` / `deliver_text` / `board` / `branch` / `suggest_lv`
        unlock            解锁条件串（前缀语义在游戏侧，不解析）

    ============================ 本域**不**含哪些任务表 ============================
        `game/data/weekly_quests.py:22 WEEKLY_QUESTS`（12 条周常悬赏）与
        `game/data/quest_add_v140.py:22 QUEST_ADD`（12 条奖励**补丁**行）**不在本域**：
        前者是另一个文件/另一张面板（`commands/weekly.py`，形状与 DAILY 同构、同样无 id），
        后者是**叠加式补丁表**（键 = 已有任务 id，运行期二段合并发放，不是独立任务）——
        两个都写进报告 §缺口，等主 agent 定口径（本批不擅自扩域）。
    """
    mod = import_game_data("quests", src_root or REPO_ROOT)

    out: dict = {}
    for sym, source, has_id, where in _QUEST_TABLES:
        lst = getattr(mod, sym, None)
        if not isinstance(lst, list) or not lst:
            raise ValueError(f"quests：{where} 不是非空 list（{type(lst).__name__}）—— 源形状变了，拒绝导出"
                             f"（空表 = 编辑器显示 0 条且不报错）")
        for i, q in enumerate(lst):
            if not isinstance(q, dict):
                raise ValueError(f"quests：{where}[{i}] 不是 dict（{type(q).__name__}）—— 拒绝导出")
            if has_id:
                key = q.get("id")
            else:
                if "id" in q:
                    raise ValueError(
                        f"quests：{where}[{i}] 出现了 id={q['id']!r} —— 每日任务的键口径是 **name**"
                        f"（services/quests.py:54 按名匹配）；源侧加了 id 就该改本域键口径，拒绝导出")
                key = q.get("name")
            if not isinstance(key, str) or not key:
                raise ValueError(f"quests：{where}[{i}] 的键（{'id' if has_id else 'name'}）"
                                 f"不是非空 str：{key!r} —— 拒绝导出")
            if "source" in q:
                raise ValueError(f"quests：{where}[{i}]（键 {key!r}）已含字段 'source' —— "
                                 f"注入会覆盖源真值，拒绝导出")
            if key in out:
                raise ValueError(
                    f"quests：键 {key!r} 冲突（{out[key]['source']} 与 {source} 都声明了它）—— "
                    f"合并三张表会丢条目，请先在源侧决定归属再导出")
            entry = dict(q)
            entry["source"] = source
            out[key] = entry
    return sort_table(out)


# =============================================================================
# ③ events —— 探索随机事件
# =============================================================================
_EVENT_TABLES = (
    ("EXPLORE_EVENTS", "explore", "game/data/events.py:11 EXPLORE_EVENTS"),
    ("EXPLORE_EGG_EVENTS", "egg", "game/data/events.py:1459 EXPLORE_EGG_EVENTS"),
)


def derive_events(src_root: str = None) -> dict:
    """事件域（`events`）：`game/data/events.py` 两个事件池**合成一张扁平表**（一条 = 一个事件）。

    真源（v97.3 起「模板 + 参数 + 文案」全数据化）
    ---------------------------------------------
        `game/data/events.py:11    EXPLORE_EVENTS`      探索事件 100 条（遇怪前判定）
        `game/data/events.py:1459  EXPLORE_EGG_EVENTS`  彩蛋事件 46 条
                                                        （`EXPLORE_EGG_CHANCE = 0.005`
                                                         `:1458` 单独判定的低频池）
        同文件的三个派生常量（`EXPLORE_EGG_SUM` / `EVENT_WEIGHT_SUM` / `EXPLORE_EGG_CHANCE`）
        **不是表**（权重和 / 概率标量，是 `sum()` 与字面量）→ 不进本域。

    条目形状
    --------
        `{id, weight, name, desc, template, params}` + 可选 `maps`（该图才出）、
        `season`（限定季节）/ `season_boost`（偏好季节，权重 ×1.5）。
        实测键集：`maps` 57+24 条、`season_boost` 4 条、`season` 4 条、其余 7 键 146/146 全覆盖。
        `params` 是**模板参数原样**（键随 template 变：min/max/scale_lv/mats/header/…，含
        `{name}`/`{gold}` 之类播报占位符）—— 导出期一个字不解释。
        `maps` 实测 86 个不同地图值，全部落 maps 域；`template` 实测 16 个不同值，
        全部在 `game/core/event_templates.py TEMPLATES` 里注册（本函数交叉核对，缺一个就 raise）。

    导出映射
    --------
        键 = `id`（两池实测零交集，撞了 raise）；条目**原样** + 注入 `source`
        （`explore` / `egg`，折两个池带来的信息损失）。源条目已含 `source` → raise。

    消费点（导出只搬运，不改语义）：`core/events.py:34`（按 map/季节过滤后按 weight 抽）、
    `commands/event_menu.py:133`（彩蛋/探索池的展示档位）。
    """
    mod = import_game_data("events", src_root or REPO_ROOT)
    # 先走完 game.data 装配链，再 import core（否则撞循环导入，见模块头注）
    tpl_mod = import_game_core("event_templates", src_root or REPO_ROOT)
    templates = as_table(getattr(tpl_mod, "TEMPLATES", None),
                         "game/core/event_templates.py TEMPLATES")

    out: dict = {}
    for sym, source, where in _EVENT_TABLES:
        lst = getattr(mod, sym, None)
        if not isinstance(lst, list) or not lst:
            raise ValueError(f"events：{where} 不是非空 list（{type(lst).__name__}）—— 源形状变了，拒绝导出")
        for i, ev in enumerate(lst):
            if not isinstance(ev, dict):
                raise ValueError(f"events：{where}[{i}] 不是 dict（{type(ev).__name__}）—— 拒绝导出")
            key = ev.get("id")
            if not isinstance(key, str) or not key:
                raise ValueError(f"events：{where}[{i}] 的 id 不是非空 str：{key!r} —— 拒绝导出")
            if "source" in ev:
                raise ValueError(f"events：{where}[{i}]（id {key!r}）已含字段 'source' —— "
                                 f"注入会覆盖源真值，拒绝导出")
            if key in out:
                raise ValueError(f"events：id {key!r} 冲突（{out[key]['source']} 与 {source} 都声明了它）"
                                 f"—— 合并两个池会丢条目，请先在源侧决定归属再导出")
            if not isinstance(ev.get("params"), dict):
                raise ValueError(f"events：{where}[{i}]（id {key!r}）.params 不是 dict —— "
                                 f"引擎按 template 取参数（core/event_templates.py），拒绝导出")
            tpl = ev.get("template")
            if tpl not in templates:
                raise ValueError(
                    f"events：{where}[{i}]（id {key!r}）.template={tpl!r} 不在 "
                    f"core/event_templates.py TEMPLATES 里（共 {len(templates)} 个）—— "
                    f"运行时 execute_event_template 会走未知模板分支，拒绝导出")
            maps = ev.get("maps")
            if maps is not None and not (isinstance(maps, list)
                                         and all(isinstance(m, str) and m for m in maps)):
                raise ValueError(f"events：{where}[{i}]（id {key!r}）.maps 不是非空字符串 list —— 拒绝导出")
            entry = dict(ev)
            entry["source"] = source
            out[key] = entry
    return sort_table(out)


# =============================================================================
# ④ event_templates —— 事件模板注册表
# =============================================================================
def derive_event_templates(src_root: str = None) -> dict:
    """事件模板域（`event_templates`）：`game/core/event_templates.py` 的模板注册表（19 条）。

    真源 / 为什么它是「域」而不只是代码
    -----------------------------------
        `TEMPLATES = {模板名: 函数}`（`event_templates.py:19` 空字典 + `register()` 装饰器
        `:22` 逐个注册，实测 19 个键 ↔ 19 个 `tpl_*` 函数 **1:1**，无未注册的 `tpl_*`）。
        事件数据（`data/events.py`）只声明 `template` + `params` 两个字段，
        执行统一走 `execute_event_template` —— 即**模板名是内容侧的引用词汇**：
        `events` 域的 `template` 字段、`commands/event_menu.py` 的档位统计都指向这里。
        没有这张表，「模板名」就是没有落点的字符串 = 编辑器里点不开的引用。

    这一域导出什么（★ 与其它域的差别，写清楚）
    ------------------------------------------
        函数体**不能进 JSON** —— 所以本域导出的是**注册表投影**（一条 = 一个模板名）：
            `func` : Python 函数名（实测恒为 `"tpl_" + <模板名>`）
            `line` : 函数定义行号（`__code__.co_firstlineno`，对得上源文件，便于人回查）
            `doc`  : 函数 docstring（`inspect.getdoc()` 归一化后的整段；params 说明就在里面，
                     如 `loot_gold` 的 `params: min/max/scale_lv/header`）
        这三个字段**全部由真源算出**（不做任何人工摘要），故 `--check` 可逐字节复现；
        函数体/行为一个字都没搬（引擎代码仍只在游戏侧）。

    自检
    ----
        · `TEMPLATES` 非空 dict；键非空 str；值可调用
        · 每个值 → `func == "tpl_" + 键`（命名漂移 = 装饰器改名了，说明注册路径变了 → raise）
        · 模块里每个顶层 `tpl_*` 函数都必须在 `TEMPLATES` 里（未注册的 `tpl_*` = 死代码或
          漏注册，两种都该在源侧决定，导出期 raise 而不是静默少一条）
    """
    import_game_data("tips", src_root or REPO_ROOT)          # 先走装配（见模块头注）
    mod = import_game_core("event_templates", src_root or REPO_ROOT)
    templates = as_table(getattr(mod, "TEMPLATES", None),
                         "game/core/event_templates.py:19 TEMPLATES")

    out: dict = {}
    for name, fn in templates.items():
        if not isinstance(name, str) or not name:
            raise ValueError(f"event_templates：模板名不是非空 str：{name!r} —— 拒绝导出")
        if not callable(fn):
            raise ValueError(f"event_templates：{name!r} 的注册值不可调用（{type(fn).__name__}）"
                             f"—— register() 注册路径变了，拒绝导出")
        expect = "tpl_" + name
        if getattr(fn, "__name__", None) != expect:
            raise ValueError(
                f"event_templates：模板 {name!r} 注册的是 {getattr(fn, '__name__', None)!r}"
                f"（期望 {expect!r}）—— 命名漂移，拒绝导出")
        doc = fn.__doc__
        out[name] = {
            "func": fn.__name__,
            "line": int(fn.__code__.co_firstlineno),
            "doc": _normalize_doc(doc),
        }

    unreg = sorted(n for n in vars(mod)
                   if n.startswith("tpl_") and callable(getattr(mod, n))
                   and n[4:] not in templates)
    if unreg:
        raise ValueError(
            f"event_templates：模块里有 {len(unreg)} 个 tpl_* 函数没在 TEMPLATES 里注册：{unreg}"
            f"—— 死代码或漏注册（两种都该在源侧决定），拒绝导出")
    return sort_table(out)


def _normalize_doc(doc) -> str:
    """docstring → 归一化文本（等价 `inspect.getdoc`：剥公共缩进 + 去首尾空行）。

    自己实现而不是 `inspect.getdoc`：函数体里 import inspect 会与模块头注的 import 纪律
    混淆，而且这里只需要「确定性」这一条（--check 要能逐字节复现）。
    """
    if not isinstance(doc, str):
        return ""
    lines = doc.expandtabs().splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return ""
    pad = min((len(ln) - len(ln.lstrip()) for ln in lines[1:] if ln.strip()), default=0)
    body = [lines[0].strip()] + [ln[pad:].rstrip() for ln in lines[1:]]
    return "\n".join(body)


# =============================================================================
# ⑤ tips —— 指令面板随机提示库
# =============================================================================
def derive_tips(src_root: str = None) -> dict:
    """提示域（`tips`）：`game/data/tips.py:8 TIPS` 全量（58 个分类 / 池内 333 条提示语）。

    真源 / 形状
    -----------
        `TIPS = {分类: [提示语, …]}` —— **值是字符串列表，不是 dict**。
        分类 = 指令面板名（`accept` / `bag` / `battle` / `instance` / `weekly` 面板…），
        消费点 `core/item_templates.py:33`：`TIPS.get(cat) or TIPS.get("common")` 里随机抽 1 条
        （`common` 是兜底分类），面板底部引导文案即它。
        源文件头声明「每条 ≤20 字（不含 💡 前缀）」—— 导出期不校验字数（那是文案规范，
        不是导出条件；真实超长的要改文案，不该让导出炸）。

    ★ 为什么要包一层
    ----------------
        宿主 `export()` 要求**每条都是 dict**（非 dict → `ValueError: 条目形状不对`）。
        所以条目 = `{"lines": [<源列表原样，保序>]}` —— 与宿主 `derive_panel_rules` 把
        `PCT_STATS` 这类纯列表常量包成 `{"stats": [...]}` 是同一手法（源头是那条硬约束，
        不是本域自创的形状）；消费语义没变：池内顺序 = 源的抽取池顺序。

    导出映射
    --------
        键 = 分类（58 个，实测唯一）；条目 = `{"lines": [...]}`（**不补** count/label 之类
        派生字段 —— 面板显示名在游戏侧，不在数据里）。外层按分类字典序（幂等）。
    """
    mod = import_game_data("tips", src_root or REPO_ROOT)
    tbl = as_table(getattr(mod, "TIPS", None), "game/data/tips.py:8 TIPS")

    out: dict = {}
    for cat, pool in tbl.items():
        if not isinstance(cat, str) or not cat:
            raise ValueError(f"tips：分类键不是非空 str：{cat!r} —— 源形状变了，拒绝导出")
        if not isinstance(pool, list) or not pool:
            raise ValueError(f"tips：{cat!r} 不是非空 list（{type(pool).__name__}）—— "
                             f"空池 = 面板底部永远念兜底文案且不报错，拒绝导出")
        for i, line in enumerate(pool):
            if not isinstance(line, str) or not line:
                raise ValueError(f"tips：{cat!r}[{i}] 不是非空 str：{line!r} —— 拒绝导出")
        out[cat] = {"lines": list(pool)}
    return sort_table(out)


DOMAINS = {
    "dialogues": derive_dialogues,
    "quests": derive_quests,
    "events": derive_events,
    "event_templates": derive_event_templates,
    "tips": derive_tips,
}
