#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""奥兰迪亚（游戏仓）→ 框架编辑器「游戏包」JSON 导出器（通用壳，已实现 items / classes / skills）。

方向只有一个：**游戏仓 Python 数据（真源）→ 框架仓 games/<id>/content/data/<域>.json**。
本脚本**只读**游戏仓数据（绝不写回 game/data/*.py），框架仓只写这些文件：

    <pkg>/game.json                      包清单（id/name/desc/engine/domains/created）
    <pkg>/content/data/items.json        物品域数据表 {物品key: 物品}
    <pkg>/content/data/classes.json      职业域数据表 {职业key: 职业}
    <pkg>/content/data/skills.json       技能域数据表 {技能key: 技能}（扁平化，见下）

用法：
    python scripts/export_game_package.py --domain items
    python scripts/export_game_package.py --domain classes
    python scripts/export_game_package.py --domain skills
    GWEN_FRAMEWORK_DIR=<框架仓> python scripts/export_game_package.py --domain items
    python scripts/export_game_package.py --domain items --check    # 只派生比对，不落盘

默认值：
    源   = 本脚本所在仓根（--src 覆盖）
    目标 = --out > $GWEN_FRAMEWORK_DIR > DEFAULT_FRAMEWORK_DIR（见下）

域注册表（**加一个域 = 加一个 derive_ 函数 + 在此注册一行**）：
    DERIVERS = {"items": derive_items, ...}
    PLANNED  = 已规划但未实现的域 —— 命中时**显式报错**「未实现」，不静默产出空表
    （空表会让编辑器显示「0 条」而不报错，是最难查的那种故障）

幂等保证：输出 = UTF-8 + LF + indent=2 + 末尾换行；外层按 key 字典序；game.json 的
`created` 保留已有值（首次落盘用 DEFAULT_CREATED，**不使用 time.time()**）→ 重复运行逐字节相同。

================================================================================
items 域语义核实（2026-09-12，证据在游戏仓 game/data/items.py，行号以当时的文件为准）
================================================================================
1) **合表后是 900 条，不是 1704 条。**  `ITEMS` 本身就是合表：
       items.py:3057  ITEMS = dict(MATERIALS)
       items.py:3058  ITEMS.update(CONSUMABLES)
       items.py:3061 / :3084 / :3105 / :3129 / :3226 / :3291  继续 ITEMS.update({...}) 追加
   实测：MATERIALS(598) 与 CONSUMABLES(206) 的**每个 key 都在 ITEMS 里，且是同一个 dict 对象
   （`ITEMS[k] is MATERIALS[k]`）**。所以「ITEMS 900 + MATERIALS 598 + CONSUMABLES 206 = 1704」
   是把同一批条目按表重复计了三次（重复计数量 598+206=804，900+804=1704）。
   → 导出 = 取 `ITEMS` 全量原样，**不再手工 merge 三张表**（手工 merge 会引入第二份定义，将来漂移）。

2) **price 必须是覆盖后的最终价，而导出的 ITEMS 已经就是最终价。**
   `MATERIAL_PRICE_OVERRIDE`（items.py:2589 定义，219 条）在 items.py:2813-2817 的 import 期循环里
   **就地**改写 MATERIALS：
       for _mid, _m in MATERIALS.items():
           if _mid in MATERIAL_PRICE_OVERRIDE:
               _m["price"] = MATERIAL_PRICE_OVERRIDE[_mid]     # ← 就地覆盖 MATERIALS
               if _m.get("type") not in _PRICE_SPECIAL_TYPES:
                   _m["quality"] = _mat_quality(_m["price"])   # ← 品质按新价重算
   而 `ITEMS = dict(MATERIALS)` 发生在 :3057（覆盖**之后**）→ 导出的 price 已经等于
   MATERIAL_PRICE_OVERRIDE 的值（实测 219/219 一致，门禁 tests/test_export_package_sync.py 锁死）。
   要点：导出器读的是 **import 之后的运行时表**，不是源码字面量；照字面量解析会导出**未覆盖的旧价**。

3) **`MATERIALS_BY_NAME` 不进包（纯按名索引，零新信息）。**
   items.py:3054  `MATERIALS_BY_NAME = {_m["name"]: _m for _m in MATERIALS.values()}`
   —— 值就是 MATERIALS 里**同一个 dict 对象**（按显示名建的索引），全仓无任何写入端
   （grep `MATERIALS_BY_NAME[...] =` → 0 命中）。消费端全部是「拿玩家背包里的中文名反查定义」：
       game/store/inventory.py:51                （_class_attrs：key 查不到时按名反查）
       game/commands/economy.py:334-335          （按名查，注释写明 key 是 mat_ ID）
       game/commands/economy.py:4365 / :5257     （批量出售 / 图鉴按名兜底）
       game/services/shop.py:185 / :215 / :253   （回收折价率按名判材料类型）
       game/data/__init__.py:158 / :192          （import 期 FISH_POOL/FISH_COLLECT 一致性校验）
   若把它也导出：每件材料在包里**重复一次**，且外层键变成中文 —— 违反
   schemas/item.schema.json `item_table.propertyNames` 的 `^[a-z][a-z0-9_]*$`。
   → 它是**运行期查询索引**，不是数据源；包里由 key 表 + `name` 字段即可等价表达。
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import sys

# ---------------- 常量 / 路径 ----------------
HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)                      # 游戏仓根（dragonfall/）

PACKAGE_ID = "orlandia"
DEFAULT_FRAMEWORK_DIR = "C:/Users/yuyu/framework-engine"
# created 固定值：**不要**改成 time.time()/time.strftime()，否则每次跑都变 → 破坏幂等
DEFAULT_CREATED = "2026-09-12"

# 清单里由导出器管辖的字段（其余已有字段原样保留，不吞编辑器/人工加的元数据）
# `domains` 不在常量里：它由 DERIVERS 派生（声明里的域 = 已实现的域，避免第二个手写列表）。
MANIFEST_MANAGED = {
    "id": PACKAGE_ID,
    "name": "奥兰迪亚·余烬纪年",
    "desc": "《奥兰迪亚·余烬纪年》内容侧数据导出包（QQ 机器人文字 RPG 内容仓 dragonfall 单向导出）",
    "engine": ">=0.1",
}
# 导出器**不再声明**的字段：曾写过 "entry": "content/apply.py"，但导出物里没有 content/apply.py
# （机制尚未移植，本包是纯数据包）→「声明了 entry 却没有该文件」= 坏包。
# 框架侧门禁 tests/test_editor_dist.py 现在守这条不变量；一旦将来移植机制入口，再把它加回来。
MANIFEST_DROPPED = ("entry",)

# ---------------- 域注册表 ----------------
# 一个域 = 一个 `derive_<域>() -> dict[key, entry]`；entry 原样进 JSON（不补默认值/不改类型）
PLANNED_DOMAINS = (
    "affixes", "maps", "drop_pools", "instances",
    "texts", "mech_cash",
)


# =============================================================================
# 派生（源 → 内存表）
# =============================================================================
def _import_module(mod_name: str, src_root: str = REPO_ROOT):
    """import 游戏仓 game/data/<mod>.py（走包导入，因为有 `from .fishing import ...` 这类相对导入）。"""
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    full = f"game.data.{mod_name}"
    if full in sys.modules:
        return sys.modules[full]
    return importlib.import_module(full)


def _import_items_module(src_root: str = REPO_ROOT):
    return _import_module("items", src_root)


def derive_items(src_root: str = REPO_ROOT) -> dict:
    """物品域：取 `ITEMS` 全量（合表 + 已含 price 覆盖/品质重算/desc 注入的**最终运行时态**）。

    依据见本文件顶部「items 域语义核实」1) 2)：ITEMS = MATERIALS ∪ CONSUMABLES ∪ 追加条目，
    且 ITEMS 在 MATERIAL_PRICE_OVERRIDE 就地覆盖之后才构造 → 无需（也不应）再套一次覆盖。
    """
    return dict(_import_items_module(src_root).ITEMS)


def derive_classes(src_root: str = REPO_ROOT) -> dict:
    """职业域：`CLASSES` 全量原样（8 条；框架 classes 域无 schema，形状由内容侧定）。

    字段含 desc / lore / aliases / evolve_branches / attack_text / tutor 等（见 classes.py 头注）。
    """
    return dict(_import_module("classes", src_root).CLASSES)


def derive_skills(src_root: str = REPO_ROOT) -> dict:
    """技能域：把「按职业分组的技能表」**扁平化**成「一条技能 = 一个 key」。

    为什么扁平：框架 skills 域的权威形状是 `x-primary: skill`（一条 = 一个技能，编辑器按条增删改，
    校验也只认这个 def）；而游戏侧 `PLAYER_SKILLS` 是 `{职业: {name, skills: {sk_*: 技能}}}` 的**嵌套**
    形态（框架 schema 里 player_skills / branch_skills / tutor_skills 三个 def 描述的就是这个源形态，
    留给将来的「职业技能树」视图用）。

    扁平化规则：源条目字段**原样保留**（不改类型、不补默认值），只额外写一个 `owner_class`（该技能
    所属职业的 key）—— 否则嵌套层级丢掉后，技能归属就没地方表达了。实测 7 职业 61 技能、键 0 冲突、
    按框架 skill def 逐条校验 0 失败（门禁 tests/test_export_package_sync.py 锁死）。
    未导出：BRANCH_SKILLS / TUTOR_SKILLS（职业进阶元数据，等有对应视图再导）。
    """
    tables = _import_module("skills", src_root)
    flat: dict = {}
    for cls_key, blob in sorted((tables.PLAYER_SKILLS or {}).items()):
        if not isinstance(blob, dict):
            raise ValueError(f"PLAYER_SKILLS[{cls_key}] 不是 dict —— 源形状变了，拒绝导出")
        for sk_key, sk in (blob.get("skills") or {}).items():
            if not isinstance(sk, dict):
                raise ValueError(f"{cls_key}.skills[{sk_key}] 不是 dict —— 源形状变了，拒绝导出")
            if sk_key in flat:
                raise ValueError(
                    f"技能 key '{sk_key}' 同时属于 {flat[sk_key]['owner_class']} 与 {cls_key} —— "
                    f"扁平化会丢条目，请先决定归属再导出"
                )
            entry = dict(sk)
            entry["owner_class"] = cls_key
            flat[sk_key] = entry
    return flat


def derive_monsters(src_root: str = REPO_ROOT) -> dict:
    """怪物域：取 `MONSTER_SKILLS` 全量原样（330 条；一条 = 一个怪技能）。

    为什么是 MONSTER_SKILLS：框架 `editor/packages.py:40` 的 monsters 域 primary =
    `monster_skill`（= `schemas/monster.schema.json:318` 的 `x-primary`），require name/kind/desc；
    编辑器按条目增删改、校验也只认这个 def。游戏侧与它同构的**扁平 {key: entry} 表只有**
    `game/data/monsters.py:3  MONSTER_SKILLS = {`（330 条，闭括号 :1639）。
    而「怪物名册」（id / 中文名 / role / lv / 技能 / 掉落）在游戏侧**不是一张表**：散落在
    subareas.py / instances.py / mesh_rooms_*.py 的 840 条六元组模板（355 个唯一 id，168 个 id
    的 lv 跨表不一致，10 个中文名对应两个 id）——那是 maps / instances 域的形态。

    运行时表 == 源码字面量（对本文件 AST 全扫描：`MONSTER_SKILLS` 只出现 1 次，0 处
    update/setdefault/pop/下标赋值）→ 与 items 域不同，本域**没有** import 期就地覆盖要跟。

    实测（2026-09-13）：330 条逐条过 `editor.validate.validate_entry("monsters", 条目)` 0 失败；
    整表过 `$defs/monster_skill_table` 0 失败；键 100% 匹配 `^[a-z][a-z0-9_]*$`；字典字面量
    重复键 0；无空值、无 tuple（全 JSON 原生类型）→ 落盘 85 792 B / 3 929 行，两次派生逐字节相同。
    条目内字段顺序保持源顺序（如 ms_ai_hao = kind / formula / power / desc / name）。

    未导出（同族的另三张表，形状与本域 primary 不符，见报告 §3.2）：
    MONSTER_MODS(140) / HIDDEN_MONSTERS(25) / ELITE_EQUIP_DROP(18)。
    """
    table = _import_module("monsters", src_root).MONSTER_SKILLS
    if not isinstance(table, dict) or not table:
        # 空表会让编辑器显示「0 条」而不报错 —— 宁可炸（与 PLANNED_DOMAINS 的立意一致）
        raise ValueError("MONSTER_SKILLS 不是非空 dict —— 源形状变了，拒绝导出")
    return dict(table)


def derive_tlogs(src_root: str = REPO_ROOT) -> dict:
    """流水声明域（tlogs）：读 `game/data/tlogs.json` 全量原样（18 条，`{kind: {fields, desc, category}}`）。

    为什么这一域**不像 items/classes/skills 那样 `_import_module`**：声明不是 `.py` 表，
    而是一张**数据文件**（JSON）。内容侧唯一读点是 `game/tlog_setup.py:44-56 kinds()`：
    `json.load(game/data/tlogs.json)` → `saintess_engine.tlog.KindTable` → 喂给
    `TLog(kinds=…)`，由 `KindTable.check_record()` 逐条比对「未声明 kind / 未声明字段 /
    缺声明字段」（`strict=True` 直接抛，默认只在 `on_undeclared` 上报）。
    也就是说：**这张表不是流水数据本身，而是「哪个 kind 该带哪些字段」的契约**，
    是发射端（`game/services/battle_tlog.py` 的 `EVENT_KINDS` 映射 + `game/reward.py` /
    `game/services/shop.py` / `game/commands/instance_router.py` 的直调点）与
    读端（`replay()` / `Reader` / 分析）之间的同一份口径。

    导出纪律（与 items/classes/skills 同构）：
    * 条目**原样**进包 —— 不注入 `kind`（框架 `schemas/tlog.schema.json` 的
      `$defs.tlog_entry.kind` 是可选的：「表形态里以对象 key 为准」，注入等于造第二个真源）、
      不补默认值、不改字段名（字段名与发射端一一对应，改一个名字就等于改语义）。
    * **不按调用点反推字段** —— 调用点与声明目前**确有漂移**（见下），但修的地方是
      游戏仓的声明或发射端，导出期「顺手改」会掩盖真问题。
      现状快照（2026-09-13 实测）：`shop.buy` 调用点发 `key/qty/discount`（声明写
      `item/qty/unit_price/gold_after`）、`instance.clear` 发 `iid/first_clear`（声明写
      `iid/rounds/deaths`）、`reward.py` 的 `drop.grant` 发 `exp/gold/items`（声明写
      `item/qty/source`）；另有 6 个 kind（quest.accept/quest.done/shop.sell/instance.enter/
      level.up/travel.move）**已登记未接线**（设计稿 `docs/REFACTOR_tlog_landing.md:152`
      明说「先登记词表、暂不埋点」）—— 这些都是**源侧事实**，导出照搬即可。
    * 源缺失/空表/形状不对 → `raise ValueError`，**绝不静默产空表**（空表会让编辑器显示
      「0 条」而不报错，是最难查的那种故障，见本文件顶部 items 域的同类纪律）。

    实测：18 条 / 0 键冲突 / 按框架 `tlog_entry` 逐条校验 0 失败 / 连跑两次逐字节相同。
    """
    path = os.path.join(src_root, "game", "data", "tlogs.json")
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except OSError as e:
        raise ValueError(f"流水声明源不可读：{path}（{e}）—— 拒绝导出空表") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"流水声明源不是合法 JSON：{path}（{e}）") from e
    if not isinstance(raw, dict):
        raise ValueError(f"流水声明源顶层不是 object：{type(raw).__name__}（{path}）")
    if not raw:
        raise ValueError(
            f"流水声明源是空表：{path} —— 拒绝导出（空表 = 编辑器显示 0 条且不报错）"
        )
    for kind, spec in raw.items():
        if not isinstance(spec, dict):
            raise ValueError(
                f"流水声明 {kind!r} 不是 object（{type(spec).__name__}）—— 源形状变了，拒绝导出"
            )
    return dict(raw)


def derive_commands(src_root: str = REPO_ROOT) -> dict:
    """指令域：取**指令声明表** `game/data/command_specs.json` 全量原样（194 条）。

    背景：指令表迁移 = 声明表单源
    ------------------------------
    2026-09-12（路线图 #9「指令表迁移收尾」，见游戏仓 `docs/COMMAND_DECL_MIGRATION.md`）之前，
    命令正则有**两处来源**：各文件里的 `@filter.regex(<字面量>)`（真实注册）＋
    `game/commands/_registry.py::_LITERAL_REGEX`（手工维护的镜像表，供停服 gate / 快捷转发 / 测试用）。
    两处互相同步 → 必然漂移，只能再配一个「表与装饰器 1:1」测试盯着。迁移把 ① 换成
    `@declared("key")`（正则从声明表取）、删掉 ② → **声明表是唯一真源**：
    现在 194/194 条指令全部来自 `game/data/command_specs.json`，命令层源码里 `@filter.regex` 为 **0**，
    `_registry.COMMAND_REGEX` 只是**同一份声明的派生**（`_declared_patterns()`）。

    为什么取声明表，而不是扫命令层源码
    ----------------------------------
    1. **声明表是超集**：它同时供「正则注册 / 帮助与目录（desc/category/order/visible）/
       有效表派生 / 漂移自检」。扫源码只能拿到正则，编辑器真正要编辑的元数据一个字都拿不到。
    2. **正则字面量已不在源码里**（源码只有 `@declared("key")`）→ 扫源码 = 重新发明一套解析器。
    3. **扫源码会复活已删除的第二来源**：迁移文档 §六.1 记着「读源码找正则的测试是迁移的绊脚石
       （踩了 3 次）」。导出器再扫一遍源码，等于把刚拆掉的漂移风险装回来。
    4. 真要「合并后的正则」也有现成、已被断言锁死的一条路（`_registry._combine_patterns` ≡ 框架
       `saintess_engine.command.combine_patterns`）—— **但导出不预合并**：框架 schema 的权威形状是
       `patterns` 数组（「首条为主，其余为别名」），预合并会毁掉这个结构。

    形状
    ----
    `{key: {"patterns": [...], "desc", "category", "usage", "guards"?, "order",
            "page_size"?, "visible"?, "extra"?}}`
    外层 key 就是指令 key（框架 `command.schema.json` 注明「表形态里以对象 key 为准，条目内可省略」），
    与 items/classes/skills **同构**：条目原样进 JSON，不补默认值、不改类型。

    实测（2026-09-13，本机）
    ------------------------
    * 194 条；每条恰好 1 条 pattern，194 条正则全部 `re.compile` 通过
    * `editor.validate.validate_entry("commands", 条目)` 逐条 **194 通过 / 0 失败**
      （反证探针：缺 patterns / 空 patterns / 空串 / page_size=-1 / guards 非数组 / key 非法 —— 全被拦）
    * 框架 `CommandRegistry.from_data(表).validate()` **0 问题**；`pattern_map()` 与游戏侧
      `_registry.COMMAND_REGEX` 194 条**逐字全等**
    * 两次导出（独立 tmp）`commands.json` 逐字节相同（幂等）

    未导出（有意）
    --------------
    * 守卫**实现**（`game/commands/base.py` 的 require_player / no_prof_waiting / require_battle）——
      声明只记守卫**名字**，框架不认语义。
    * 宿主注册 **priority**（`@declared("key", priority=N)` 的实参，4 条）—— 属宿主注册细节，不在声明表。
    * 有效表 `COMMAND_REGEX`（预合并正则）—— 派生自本表，导它 = 第二份定义。
    """
    path = os.path.join(src_root, "game", "data", "command_specs.json")
    if not os.path.exists(path):
        raise ValueError(f"指令声明表不存在：{path} —— 取不到真源，拒绝导空表")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except ValueError as exc:                     # JSON 坏了
        raise ValueError(f"指令声明表不是合法 JSON：{path}（{exc}）") from exc
    if not isinstance(data, dict) or not data:
        raise ValueError(f"指令声明表为空或不是对象：{path} —— 拒绝导空表")
    for key, entry in data.items():
        if not isinstance(entry, dict):
            raise ValueError(f"指令声明 {key!r} 不是对象 —— 源形状变了，拒绝导出")
        pats = entry.get("patterns")
        if (not isinstance(pats, list) or not pats
                or any(not isinstance(p, str) or not p for p in pats)):
            raise ValueError(
                f"指令声明 {key!r} 的 patterns 缺失/为空/含非字符串 —— "
                f"框架 command.schema.json 里 patterns 是必填非空字符串数组，拒绝导出")
    return dict(data)


def derive_passive_proc(src_root: str = REPO_ROOT) -> dict:
    """被动声明域：取 `battle_rules.PASSIVE_PROC` 全量原样（42 条 @ 2026-09-13）。

    ============================ 这张表是什么（边界） ============================
    `PASSIVE_PROC` 是**装配层的声明表**，不是引擎数据：引擎（saintess_engine）里
    **没有** `passive_proc` 这个挂载点（config._HOOKS 无此名，`config.mount(passive_proc=…)`
    按「未知名忽略」静默丢弃）；`saintess_engine` 全仓零处认识 `PASSIVE_PROC`。
    它的消费者是游戏侧装配器 `game/services/class_mech_proc.py:2035 apply_class_passives(actor)`：

        扫 actor.learned_skills 里 kind=被动 的技能 → 读该技能的 passive.proc
        → 查本表 PASSIVE_PROC[proc] → 合成条目 {type: cfg.action, judge: cfg.judge,
          **cfg 的非结构字段, **passive 参数, label: 技能名}
        → 挂 actor["triggers"][cfg.event]（聚合族 agg 先按 (event, agg) 暂存再归并单条；
          domain=cap → bonus.cap[cap_key] += add；domain=cost → bonus.cost 折扣；
          also[] → 同被动的第二条事件钩子；left_key/left_init → effects 计数器初始化）。

    ============================ 与引擎 hook 的关系 ============================
    引擎侧只有最后一段：`fire(event)` 遍历存活 actor 的 `triggers[event]` →
    `apply_effects` → 按条目的 `action` **直查 `ACTION_HANDLERS`（跳过名词翻译）**
    （`saintess_engine/battle/effect_triggers.py:65`、`battle/effects.py:95/155-180`）。
    即本表声明的是「**哪个事件 → 哪个动词 → 什么判据**」；`action` 的取值由内容侧
    注册机制决定（26 个动作的实现在 game/services/class_mech_proc.py（25）与
    game/services/battle_bar_procs.py:169（1），**不在本表、也不在本包**）。
    ⇒ 导出本域 = 搬运「声明」而非「行为」：包里必须另有 content/mech/actions.py
    （或移植上述两文件的动作）才谈得上可运行；否则引擎 fire() 查不到 handler →
    静默跳过（不错、不报）。

    ============================ 导出约定 ============================
    - 条目**原样**（浅拷贝）：不改类型、不补默认值、不预归并 agg、不解析 bar_field
      （那些都是装配期语义，写进包里就是第二份实现）。
    - 目标路径 = `content/rules/passive_proc.json`（本域 kind="rules"；落到 content/data/
      编辑器会读不到且**不报错** → 显示 0 条）。
    - 已知覆盖面缺口（导出后包里不可见，非本函数可解）：技能侧共 52 个 proc 名，
      本表只声明 42 个；另 10 个（death_contract / faith_overload_heal / faith_share /
      focus_regen_summon / melody_full / melody_master / melody_resonance /
      shadow_dance_ease / skeleton_cap / undead_faith）走旧注册表
      game/core/passive_procs.py PROC_FAMILIES/KNOWN_GAPS —— 「同域双真源」，
      且声明这些 proc 的 52 条被动技能在 BRANCH_SKILLS，也未进 skills 域（只导了 PLAYER_SKILLS）。
    """
    tables = _import_module("battle_rules", src_root)
    table = getattr(tables, "PASSIVE_PROC", None)
    if not isinstance(table, dict):
        raise ValueError(
            "battle_rules.PASSIVE_PROC 不是 dict（缺失或源形状变了）—— 拒绝导出"
        )
    out: dict = {}
    for k, v in table.items():
        if not isinstance(v, dict):
            raise ValueError(
                f"PASSIVE_PROC[{k!r}] 不是 dict（期望「一条声明 = 一个 dict」）—— 拒绝导出"
            )
        out[k] = dict(v)
    return out


def derive_effect_rules(src_root: str = REPO_ROOT) -> dict:
    """资源/状态声明域（effect_rules）：取 `battle_rules.EFFECT_RULES` 全量原样（85 条）。

    实证（2026-09-13 域研究，见 workspace/…/domain-research/effect_rules.md）：
    * 85/85 条逐条过 `VD.validate_entry("effect_rules", 条目)` **0 失败**；
    * 85 个 key 全部匹配 `effect_rules_table.propertyNames = ^[a-z][a-z0-9_]*$`；
    * 整表 0 个 tuple / 全 JSON 原生类型；两次派生逐字节相同。
    * 与 items 域不同：本表**没有** import 期就地覆盖要跟（取运行时表即字面量）。

    ⚠ 落点：本域在框架里 `kind="rules"` → 落 `content/rules/effect_rules.json`
      （由 `content_sub()` 问框架 DOMAINS 得到，别写死 data/）。
    ⚠ 可读性：72/85 条在源表里**本来就没有 `name`**（DOT / 控制 / 装备特效类设计上不需要中文名）
      → 编辑器列表标题会显示英文 key（rage / burn / stun…）。**不在这里替它们造 name**
      （造 = 第二份定义）；真要可读名，改的地方是游戏仓源表。
    """
    table = getattr(_import_module("battle_rules", src_root), "EFFECT_RULES", None)
    if not isinstance(table, dict) or not table:
        raise ValueError("battle_rules.EFFECT_RULES 不是非空 dict —— 源形状变了，拒绝导出")
    out: dict = {}
    for k, v in table.items():
        if not isinstance(v, dict):
            raise ValueError(f"EFFECT_RULES[{k!r}] 不是 dict（期望「一条声明 = 一个 dict」）—— 拒绝导出")
        out[k] = dict(v)
    return out


DERIVERS = {
    "classes": derive_classes,
    "commands": derive_commands,
    "effect_rules": derive_effect_rules,
    "items": derive_items,
    "monsters": derive_monsters,
    "passive_proc": derive_passive_proc,
    "skills": derive_skills,
    "tlogs": derive_tlogs,
}


# =============================================================================
# 写盘（幂等：UTF-8 / LF / indent=2 / 末尾换行 / 原子替换）
# =============================================================================
def write_json(path: str, obj) -> None:
    """与框架 editor/packages.py:write_json 同款落盘约定（唯一差别：本函数外层键可控序）。"""
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")
    os.replace(tmp, path)


def sort_table(table: dict) -> dict:
    """外层按 key 字典序（稳定排序 → 幂等）；**条目内部字段顺序保持源顺序原样**。"""
    return {k: table[k] for k in sorted(table)}


def _framework_dir(out_root: str) -> str:
    """定位框架仓：环境变量 > --out > 默认路径。注意 `--out` 可能只是「导出到哪」的临时目录
    （比如门禁测试用它导到 tmp 做逐字节比对），那里没有 `editor/` 包 —— 所以要有兜底候选，
    不能只看 --out。"""
    cands = [os.environ.get("GWEN_FRAMEWORK_DIR"), out_root, DEFAULT_FRAMEWORK_DIR]
    for c in cands:
        if c and os.path.isfile(os.path.join(os.path.abspath(c), "editor", "packages.py")):
            return os.path.abspath(c)
    raise ValueError(
        f"找不到框架仓（试过 GWEN_FRAMEWORK_DIR / --out / {DEFAULT_FRAMEWORK_DIR}）—— 拒绝猜落点"
    )


def content_sub(domain: str, out_root: str) -> str:
    """域数据落 `content/data/` 还是 `content/rules/` —— **问框架**，不硬编码第二份列表。

    为什么必须问：框架 `editor/packages.py` 的 DOMAINS 给每个域标了 kind（rules / data），
    `PK.domain_path()` 按它取路径（effect_rules / passive_proc 走 `content/rules/`）。
    导出器若写错边 → 文件在、清单也声明了、同步门禁也可能全绿，但编辑器读另一边
    → **显示 0 条且不报错**（最难查的那类故障，2026-09-13 由域研究实测发现）。
    """
    fw = _framework_dir(out_root)
    if fw not in sys.path:
        sys.path.insert(0, fw)
    try:
        from editor import packages as PK      # noqa: PLC0415
    except Exception as e:                     # noqa: BLE001
        raise ValueError(f"读框架域注册表失败（{fw}）：{e} —— 拒绝猜落点") from e
    cfg = PK.DOMAINS.get(domain) or {}
    if not cfg:
        raise ValueError(f"框架域注册表里没有域 {domain!r} —— 拒绝导出（编辑器不认）")
    return "rules" if cfg.get("kind") == "rules" else "data"


def json_clean(obj):
    """JSON 往返一次：让「派生表」与「落盘后读回来的文件」在做 --check 时可比。

    为什么必须：源表里带 tuple（实测 CLASSES 的 tutor = ('导师', '地点')，7 条），json 落盘成 list、
    读回来是 list ≠ tuple → --check 会误报「不一致」。往返之后 tuple→list（这正是文件里的形状），
    键序与嵌套形状都不变。
    """
    return json.loads(json.dumps(obj, ensure_ascii=False))


def build_manifest(existing: dict | None) -> dict:
    """清单 = 管辖字段（规范值）+ domains（由 DERIVERS 派生）+ created（保留已有，否则固定常量）
    + 其余已有字段（字典序，`MANIFEST_DROPPED` 里的字段不再保留）。"""
    old = existing if isinstance(existing, dict) else {}
    out = dict(MANIFEST_MANAGED)
    out["domains"] = sorted(DERIVERS)
    created = old.get("created")
    out["created"] = created if isinstance(created, str) and created.strip() else DEFAULT_CREATED
    for k in sorted(old):
        if k not in out and k not in MANIFEST_DROPPED:
            out[k] = old[k]
    return out


def _read_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def sha256_of(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# =============================================================================
# 导出
# =============================================================================
def export(domain: str, out_root: str, check_only: bool = False,
           src_root: str = REPO_ROOT) -> dict:
    """导出单个域。返回摘要 dict（含 sha256 / 条数 / 是否变化）。"""
    if domain in PLANNED_DOMAINS and domain not in DERIVERS:
        raise NotImplementedError(
            f"域 '{domain}' 的导出器尚未实现（本次仅实现 {sorted(DERIVERS)}）。"
            f"加一个域 = 在本文件 DERIVERS 里注册一个 derive_{domain}()，并把域名加进 "
            f"MANIFEST_MANAGED['domains']。"
        )
    if domain not in DERIVERS:
        raise NotImplementedError(
            f"未知域 '{domain}'。已实现：{sorted(DERIVERS)}；已规划未实现：{list(PLANNED_DOMAINS)}。"
        )

    table = json_clean(sort_table(DERIVERS[domain](src_root)))
    pkg_dir = os.path.join(out_root, "games", PACKAGE_ID)
    data_path = os.path.join(pkg_dir, "content", content_sub(domain, out_root), f"{domain}.json")
    man_path = os.path.join(pkg_dir, "game.json")

    n = len(table)
    n_with = sum(1 for v in table.values() if isinstance(v, dict))
    if n != n_with:
        raise ValueError(f"域 '{domain}' 有 {n - n_with} 条不是 dict —— 条目形状不对，拒绝导出")

    summary = {"domain": domain, "entries": n, "package_dir": pkg_dir,
               "data_path": data_path, "manifest_path": man_path,
               "changed": False, "check_only": check_only}

    if check_only:
        old = _read_json(data_path, None)
        summary["in_sync"] = (old == table)
        old_man = _read_json(man_path, None)
        summary["manifest_in_sync"] = (old_man == build_manifest(old_man))
        return summary

    old = _read_json(data_path, None)
    write_json(data_path, table)
    write_json(man_path, build_manifest(_read_json(man_path, None)))
    summary["changed"] = (old != table)
    summary["sha256"] = sha256_of(data_path)
    summary["bytes"] = os.path.getsize(data_path)
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="export_game_package.py",
        description="奥兰迪亚内容数据 → 框架编辑器游戏包 JSON（单向导出）",
    )
    ap.add_argument("--domain", default="items",
                    help=f"要导出的域（已实现：{sorted(DERIVERS)}；默认 items）")
    ap.add_argument("--src", default=REPO_ROOT, help="游戏仓根（默认=本脚本所在仓根）")
    ap.add_argument("--out", default=None,
                    help="框架仓根（默认 $GWEN_FRAMEWORK_DIR 或 " + DEFAULT_FRAMEWORK_DIR + "）")
    ap.add_argument("--check", action="store_true", help="只派生并比对，不落盘")
    args = ap.parse_args(argv)

    # 注意：REPO_ROOT 常量只作默认值；--src 只影响本次运行的 src_root 参数（模块本身不改常量）
    src_root = os.path.abspath(args.src)
    out_root = args.out or os.environ.get("GWEN_FRAMEWORK_DIR") or DEFAULT_FRAMEWORK_DIR

    try:
        s = export(args.domain, out_root, check_only=args.check, src_root=src_root)
    except NotImplementedError as e:
        print(f"❌ {e}")
        return 2

    if args.check:
        ok = s.get("in_sync") and s.get("manifest_in_sync")
        print(f"{'✅' if ok else '❌'} --check 域={s['domain']} 条数={s['entries']} "
              f"items.json{'一致' if s.get('in_sync') else '不一致'} "
              f"game.json{'一致' if s.get('manifest_in_sync') else '不一致'}")
        return 0 if ok else 1

    print(f"✅ 导出完成：域={s['domain']} 条数={s['entries']} "
          f"{'（内容有变化）' if s['changed'] else '（内容无变化）'}")
    print(f"   数据 → {s['data_path']}  ({s['bytes']} B, sha256={s['sha256'][:16]}…)")
    print(f"   清单 → {s['manifest_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
