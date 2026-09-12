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
    "mech_cash",
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


def derive_affixes(src_root: str = REPO_ROOT) -> dict:
    """词条域：取 `AFFIXES` 全量原样（76 条 = 攻击 37 + 防御 39）。

    为什么是 AFFIXES（而且**只有** AFFIXES）：框架 `editor/packages.py:42` 的 affixes 域 primary =
    `affix`（= `schemas/affix.schema.json:165` 的 `x-primary`），要求 name/kind/trigger/effect/desc；
    框架 schema 的两个表级标题直接点名源表 —— `$defs/affix`「词条（**AFFIXES** 一条）」、
    `$defs/affix_table`「**AFFIXES** 整表」（`schemas/affix.schema.json:8,96`）。游戏仓**自带的**编辑器
    （`editor/data_io.py:53-62`）同样是 `tables=("AFFIXES",)` 的扁平域。→ 一门一表，不做任何合并。

    运行时表 == 源码字面量（与 items 域**不同**，本域没有 import 期覆盖要跟）：`game/data/affixes.py`
    全文无 import 语句，`AFFIXES` 在文件里只作为定义出现一次，全仓 `AFFIXES.update` 0 命中。
    仍然走 import（而不是 AST 解析）以与其他域同构，将来真有 import 期补丁也能自动跟上。

    实测（2026-09-13，jsonschema 4.26 + framework/schemas/affix.schema.json $defs.affix）：
    76 条逐条 validate_entry 0 失败；整表过 `$defs/affix_table`（propertyNames）0 失败；
    键 76/76 匹配 `^[a-z][a-z0-9_]*$`；必填五件套 76/76；trigger/kind 全部落在 schema 枚举内；
    无 tuple/非 JSON 原生类型 → 落盘 19 689 B，两次派生**逐字节相同**（sha256 见报告 §6）。
    条目内字段顺序保持源顺序（如首条 `abyss_resist` = name/kind/trigger/effect/desc）。

    未导出（都不是「一条词条」，各有归属，详见报告 §3.2-§3.4）：
      - `LEGENDARY_EFFECTS`（93，affixes.py:548-1022）：传说专属（一件橙装挂 1 个，装备的 `legendary`
        字段引用它），形状同词条但**语义不同**；还含 1 条越界数据（`shadow_raid.trigger="on_crit"`
        不在框架 trigger 枚举 → 逐条校验会红 1 条）。要导就**另开一个域**，别并进来。
      - `SERIES_FIXED_AFFIX`（622，affixes.py:1026-1612）：外层键是**中文装备名**（违反 affix_table 的
        `propertyNames`），值是词条 id 列表 → 属装备/名册域。
      - `AFFIX_POOL_BY_QUALITY` / `AFFIX_KIND` / `AFFIX_AFFINITY_POOLS` / `AFFIX_AFFINITY_CN`
        （affixes.py:485/524/527/538）：随机池/显示名/锻造倾向/输入别名，是**配套索引**不是条目本体；
        框架 schema 里为前两者留了同名 $defs（留给将来的「词条池」视图）。
    """
    table = _import_module("affixes", src_root).AFFIXES
    if not isinstance(table, dict) or not table:
        # 空表会让编辑器显示「0 条」而不报错 —— 宁可炸（与 PLANNED_DOMAINS 的立意一致）
        raise ValueError("AFFIXES 不是非空 dict —— 源形状变了，拒绝导出")
    flat: dict = {}
    for af_key, af in table.items():
        if not isinstance(af, dict):
            raise ValueError(
                f"AFFIXES[{af_key}] 不是 dict（{type(af).__name__}）—— 源形状变了，拒绝导出"
            )
        missing = [f for f in ("name", "kind", "trigger", "effect", "desc") if f not in af]
        if missing:
            # 框架 required 缺字段 = 形状异常：在派生处炸掉，而不是把一个编辑器会标红的条目发进包
            raise ValueError(
                f"AFFIXES[{af_key}] 缺必填字段 {missing} —— affix.schema.json $defs.affix "
                f"要求 name/kind/trigger/effect/desc，拒绝导出"
            )
        flat[af_key] = dict(af)
    return flat


def derive_drop_pools(src_root: str = REPO_ROOT) -> dict:
    """掉落池域：取 `DROP_POOLS` 全量原样（596 池；池 key 原样保留，含 `boss:` / `mon:` 等前缀与中文名）。

    为什么是整表原样、不做任何扁平化/改写：

    1) **池 key 本身就是引用语法**。`boss:inst_x` / `inst_pool:inst_x` / `mon:丘陵狼` /
       `elite:丘陵狼王·铁牙` 等 key 前缀是内容侧词汇表（`game/drop_engine.py:171` 的
       `_INLINE_PREFIXES`、`:174 _SPECIAL_REFS`、`:177 _POOL_KEY_PREFIXES`），`rolls[].pool` 里
       既有**子池 key**（本表内 `inst_pool:*` 等，114 行）也有**内容侧引用串**
       （`equip:eq_x` / `gold:a:b` / `gold_pct:30` / `item:mat_x` / `petegg:*` / `rune:blue` /
       `bp` / `gem` / `equip_drop_mix`，175 行）。框架 schema 明写「引用写法由内容侧定、引擎不解析」
       （schemas/drop_pools.schema.json 的 pool_entry.item / pool_roll.pool 描述）→ 导出器
       **只搬运不翻译**；改写任何 ref 都会在框架侧长出第二份词汇表。

    2) **源是纯数据模块，无 import 期改写**。`game/data/drop_pools.py` 无任何 import、无第二个
       顶层赋值（全文只有 `DROP_POOLS = {...}` 一处），也没有任何模块在 import 期写它
       （全仓 `DROP_POOLS[` 只出现在 tests 的读取里）→ 不像 items 域要担心「覆盖前/后」的取值时机，
       直接读运行时表即可。

    形状门禁（源形状变了就拒绝导出，而不是静默产出坏包）：
      · DROP_POOLS 必须是 dict；key 必须是非空 str；每条 value 必须是 dict。
      · type 必须是非空 str（框架**不设枚举**：内容侧可注册自己的策略名，`fish` 就是本游戏自注册的）。
      · type ∈ {weighted, fixed, fish} → 必须有非空 `entries`，每项含非空 str 的 `item`。
      · type ∈ {table, table_choice} → 必须有非空 `rolls`，每项含非空 str 的 `pool`。
      · 未知 type：只做结构检查（有 entries 就查 entries、有 rolls 就查 rolls），不拦 ——
        拦了就把内容侧的策略扩展挡在门外。

    实测（2026-09-13，真跑）：596 池 / 1435 条目 / 289 行 roll，`validate_entry("drop_pools", …)`
    逐条 **0 失败**；框架 `LootTable.audit()` 在**声明了内容侧词汇表**后 **0 问题**，与游戏仓
    `drop_engine.audit_all()` 的「596 池 / 1435 条目 / 0 问题」一致；JSON 往返零漂移 → `--check` 绿。
    """
    tables = _import_module("drop_pools", src_root)
    pools = getattr(tables, "DROP_POOLS", None)
    if not isinstance(pools, dict):
        raise ValueError("DROP_POOLS 不是 dict —— 源形状变了，拒绝导出")

    uses_entries = ("weighted", "fixed", "fish")
    uses_rolls = ("table", "table_choice")

    out: dict = {}
    for key, pool in pools.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"池 key 不是非空字符串: {key!r} —— 源形状变了，拒绝导出")
        if not isinstance(pool, dict):
            raise ValueError(
                f"DROP_POOLS[{key}] 不是 dict（{type(pool).__name__}）—— 源形状变了，拒绝导出")
        ptype = pool.get("type")
        if not isinstance(ptype, str) or not ptype.strip():
            raise ValueError(f"DROP_POOLS[{key}] 缺 type（策略名）—— 源形状变了，拒绝导出")
        ptype = ptype.strip()

        if "entries" in pool or ptype in uses_entries:
            entries = pool.get("entries")
            if not isinstance(entries, list) or (ptype in uses_entries and not entries):
                raise ValueError(
                    f"DROP_POOLS[{key}]（type={ptype}）entries 缺失/为空 —— 拒绝导出（空池会让编辑器"
                    f"显示 0 条而不报错）")
            for i, e in enumerate(entries):
                if not isinstance(e, dict) or not isinstance(e.get("item"), str) or not e["item"].strip():
                    raise ValueError(
                        f"DROP_POOLS[{key}].entries[{i}] 缺 item —— 源形状变了，拒绝导出")

        if "rolls" in pool or ptype in uses_rolls:
            rolls = pool.get("rolls")
            if not isinstance(rolls, list) or (ptype in uses_rolls and not rolls):
                raise ValueError(
                    f"DROP_POOLS[{key}]（type={ptype}）rolls 缺失/为空 —— 拒绝导出")
            for i, rc in enumerate(rolls):
                if not isinstance(rc, dict) or not isinstance(rc.get("pool"), str) or not rc["pool"].strip():
                    raise ValueError(
                        f"DROP_POOLS[{key}].rolls[{i}] 缺 pool —— 源形状变了，拒绝导出")

        out[key] = pool          # 条目原样进 JSON：不补默认值 / 不改类型 / 不重写 ref
    return out


def _import_game_module(full_name: str, src_root: str = REPO_ROOT):
    """按**全名**import 游戏仓模块（`_import_module` 只管 `game.data.*`，本函数给 `game.core.*` 用）。

    与 `_import_module` 同一条纪律：拿到的是 **import 之后的运行时模块**（装配期派生表都在里面），
    不是源码字面量解析的结果。
    """
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    if full_name in sys.modules:
        return sys.modules[full_name]
    return importlib.import_module(full_name)


def _import_data_package(src_root: str = REPO_ROOT):
    """import 游戏仓 `game.data` **包本身** —— 装配期算出的派生表挂在包命名空间上
    （`SUBAREAS` / `SUBAREA_LINKS_INDEX`，见 game/data/__init__.py:247）。"""
    return _import_game_module("game.data", src_root)


def _subarea_role_values(src_root: str = REPO_ROOT) -> dict:
    """角色名 → 取值：**从常量取**（game/core/constants.py:64-66 的 SUB_TYPE_*），不写字面量 ——
    游戏改「哪个 type 算哪个角色」时导出物自动跟随，不产生第二份定义。"""
    c = _import_game_module("game.core.constants", src_root)
    return {"hub": c.SUB_TYPE_TOWN, "through": c.SUB_TYPE_STREET, "exit": c.SUB_TYPE_GATE}


def derive_maps(src_root: str = REPO_ROOT) -> dict:
    """地图域（空间形状）：**一图一条 = 「节点表 + 拓扑」**，形状与游戏运行期 `core/maps.py:38 map_space()` 同源同形。

    真源（全部取 import 后的运行时态，本域唯一真源）
    ------------------------------------------------
        game/data/subareas.py:4        SUBAREAS             121 图 / 628 子区域（列表顺序 = 声明序 / 默认入口）
        game/data/_assembly.py:101     SUBAREA_LINKS_INDEX  97 图的显式网状连通表
                                      （4 张表合并：mesh_rooms_south.py:1338 / mesh_rooms_west_north.py:484 /
                                        mesh_rooms_east_abyss.py:19,:1933 / dungeon_links.py:20）
        game/data/maps.py:3            MAPS                 121 条；**只取它的 name**（显示名）
        game/core/constants.py:64-66   SUB_TYPE_TOWN/STREET/GATE  角色取值（城镇 / 城镇街道 / 城镇出口）

    条目形状（= schemas/maps.schema.json 的 `$defs.map`，primary）
    -----------------------------------------------------------
        {name, topology, roles, nodes:[{id, name, role}], links?, gate?}

      * `nodes`  = 该图的子区域，**声明序原样**（链/星形图的顺序本身就是作者给的由近及远，首节点 = 入口）；
                   `id` 取子区域 id、`name` 取子区域 name。
      * `role`   = 子区域 `type` **原样**（不翻译、不丢取值）—— 「角色取值由内容侧定义」，
                   引擎零知识；编辑器配色按取值分色，因此「野外 / 副本 / 隐藏区域」不被塌成「无角色」。
                   （子区域没有 type 时不写 role 键：schema 里 role 可选。）
      * `roles`  = 角色名 → 取值（hub/through/exit ← 城镇/城镇街道/城镇出口）= `core/maps.py:31` 的
                   `_ROLE_BY_TYPE` 的逆映射，取值取自 `core/constants.py` 的常量。
      * 有显式连通表 → `links` + `topology="mesh"`（**给连通表就不派生**：引擎/编辑器一律以它为准）。
        没有 → `topology` 按运行期同一口径派生：首节点是枢纽角色 = `star`，否则 `chain`。
      * `gate`   = **只在运行期需要覆盖时写**（首节点是枢纽角色却没有出口角色节点 → 取 id 以 `_gate` 结尾者，
                   与 `core/maps.py:51-54` 同一条兜底）。实测 121 图**一张都不需要** → 一律不写；
                   其余情况让引擎/编辑器按角色规则推（少一份冗余 = 少一个漂移点）。

    只读、不改类型、不重算：除 `role`（= type 原文照抄）与 `topology/roles` 是形状映射外，条目里没有别的
    生成字段；没有 tuple（`links` 取列表，`nodes` 只取 id/name/type 三个标量）→ 落盘往返不含隐式类型变化。

    未导出（都是**有意**的，写在这里防后人「顺手补上」）
    --------------------------------------------------
      * `MAP_CONNECTIONS`（maps.py:4224，116 键）—— **跨图**连接是另一层：引擎 `space` 有意不做跨图连边
        （见 docs/engine-wiki/reference/space.md「有意不做」），参考实现把它放在内容侧；要进包得先给
        space 一个「图与图」的层（框架决策，不是导出器决策）。
      * `HIDDEN_MAP_UNLOCK`(maps.py:4343) / `LEGACY_MAP_ALIAS`(maps.py:4352) —— 准入条件与旧名别名，
        都不是空间形状。
      * 子区域的 desc / npcs / monsters / elite / boss / lv / shop / healer / hidden / reveal —— 属文案 / 怪物 /
        掉落等别的域；塞进本域 = 在包里造它们的第二份定义，且编辑器空间视图只读 id/role/name（多带的字段是死重）。
      * 地图级元数据（MAPS 的 lv / region / chapter / area / type / desc / shop / healer）—— 本域语义是形状，
        不是「地图表」；要导需另立域或扩 schema（见报告风险节）。

    实测（2026-09-13，游戏仓 master 真跑）
    -------------------------------------
      * 121 条全过 `editor.validate.validate_entry("maps", 条目)`（0 失败）；
      * 121 条喂 `editor/space_view.py`（引擎同一份 Space）→ 邻接 / 深度 / gate / audit 与游戏运行期
        `core/maps.map_space(mid)` **逐格一致，0 差异**；`audit()` 全绿（0 悬空 / 0 不对称 / 0 孤立 / 0 不可达）；
      * 落盘 maps.json 139,083 B，重复运行逐字节相同（幂等）；`game.json.domains` 自动含 maps。
    """
    pkg = _import_data_package(src_root)
    maps_mod = _import_module("maps", src_root)
    roles = _subarea_role_values(src_root)

    maps = getattr(maps_mod, "MAPS", None)
    subareas = getattr(pkg, "SUBAREAS", None)
    mesh_index = getattr(pkg, "SUBAREA_LINKS_INDEX", None) or {}
    if not isinstance(maps, list):
        raise ValueError("MAPS 不是 list —— 源形状变了，拒绝导出")
    if not isinstance(subareas, dict):
        raise ValueError("SUBAREAS 不是 dict —— 源形状变了，拒绝导出")
    if not isinstance(mesh_index, dict):
        raise ValueError("SUBAREA_LINKS_INDEX 不是 dict —— 源形状变了，拒绝导出")

    no_sub = [m.get("id") for m in maps if not subareas.get(m.get("id"))]
    if no_sub:
        raise ValueError(
            f"这些图在 SUBAREAS 里没有子区域：{no_sub} —— 框架一条 = 一张图（至少一个节点），"
            f"静默丢条目会变成编辑器里「少了一张图」且没人发现，故拒绝导出"
        )

    flat: dict = {}
    for m in maps:
        mid = m.get("id")
        if not isinstance(mid, str) or not mid:
            raise ValueError(f"图的 id 非法：{m!r}")
        if mid in flat:
            raise ValueError(f"图 id 重复：'{mid}' —— 外层 key 会丢条目，请先决定归属再导出")
        src_nodes = subareas[mid]
        if not isinstance(src_nodes, list):
            raise ValueError(f"SUBAREAS['{mid}'] 不是 list —— 源形状变了，拒绝导出")

        nodes, seen = [], set()
        for sa in src_nodes:
            if not isinstance(sa, dict) or not sa.get("id"):
                raise ValueError(f"SUBAREAS['{mid}'] 里有非 dict / 没有 id 的子区域：{sa!r}")
            sid = sa["id"]
            if not isinstance(sid, str):
                raise ValueError(f"SUBAREAS['{mid}'] 子区域 id 不是字符串：{sid!r}")
            if sid in seen:
                raise ValueError(f"SUBAREAS['{mid}'] 子区域 id 重复：'{sid}'（编辑器按 id 引用节点）")
            seen.add(sid)
            node = {"id": sid, "name": sa.get("name")}
            if sa.get("type"):
                node["role"] = sa["type"]
            nodes.append(node)

        entry = {"name": m.get("name") or mid, "roles": dict(roles), "nodes": nodes}
        mesh = mesh_index.get(mid)
        if mesh is not None:
            if not isinstance(mesh, dict):
                raise ValueError(f"SUBAREA_LINKS_INDEX['{mid}'] 不是 dict —— 源形状变了，拒绝导出")
            for src, dsts in mesh.items():
                if not isinstance(dsts, list):
                    raise ValueError(f"SUBAREA_LINKS_INDEX['{mid}']['{src}'] 不是 list")
            entry["topology"] = "mesh"
            entry["links"] = {k: list(v) for k, v in mesh.items()}
        else:
            entry["topology"] = "star" if nodes[0].get("role") == roles["hub"] else "chain"

        gate = None
        if nodes[0].get("role") == roles["hub"] and not any(n.get("role") == roles["exit"] for n in nodes):
            gate = next((n["id"] for n in nodes if str(n["id"]).endswith("_gate")), None)
        if gate:
            entry["gate"] = gate
        flat[mid] = entry
    return flat


def derive_texts(src_root: str = REPO_ROOT) -> dict:
    """文案域：读 `game/data/text_specs.json` 全量（**唯一真源是 JSON 声明文件，不是 py 表**）。

    为什么不走 `_import_module`（本文件其它 derive_* 的通用手法）：
      ① 真源是 JSON：`game/core/texts.py` 只是它的装载器 ——
         `SPEC_PATH = <repo>/game/data/text_specs.json`（game/core/texts.py:33），
         `_load_specs()` 里唯一的过滤规则是「跳过 `_` 开头的顶层键」（game/core/texts.py:46-61）。
         本函数读**同一个文件**、用**同一条过滤规则**，不引入第二份定义。
      ② 走装载器会破坏「entry 原样」契约：`TextTable.load()` 会把每条过 `TextSpec.from_dict`，
         再 `to_dict()` 导出时会丢空 desc/category，并给没写 params 的条目**自动补** `params`
         （实测 233 条里 68 条会因此多出一个 params 字段 → 与真源不再逐值相同）。
      ③ 装载器的 import 链要引擎（`saintess_engine.text` + `game/log_setup.py`），而且实测在当前
         布局下 `import game.core.texts` 会撞循环导入（`game/core/__init__.py:45` → `game/core/index.py`）
         —— 导出器不该依赖运行时装配。

    过滤规则（与装载器逐字一致）：顶层 `_meta` / `_categories` 是给人/编辑器看的元信息，**不进包**。
    实测不过滤的后果：`validate_entry('texts', _meta)` → `(根): 'value' is a required property`
    —— 2 条元信息会变成 2 条校验失败（编辑器标红）。

    形状断言（形状一变就 raise，绝不静默产空表/半表）：
      · 顶层必须是对象；
      · 每条必须是对象 —— 编辑器只认对象形态，`{key: "模板串"}` 简写形态在编辑器里
        会报 `is not of type 'object'`（`schemas/text.schema.json` 的 text_entry 要求 object + value）；
      · 每条必须有非空 `value`（schema：required + minLength=1）。
    实测：233 条、键与真源一一对应、逐值零差异、逐条 validate_entry 零失败（见本文件顶部口径）。
    """
    spec_path = os.path.join(src_root, "game", "data", "text_specs.json")
    try:
        with open(spec_path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except OSError as exc:
        raise ValueError(
            f"文案声明文件读不到：{spec_path}（{type(exc).__name__}: {exc}）"
        ) from exc
    except ValueError as exc:                     # json.JSONDecodeError 是 ValueError 子类
        raise ValueError(f"文案声明文件不是合法 JSON：{spec_path}（{exc}）") from exc
    if not isinstance(raw, dict):
        raise ValueError(
            f"文案声明文件顶层不是对象（实为 {type(raw).__name__}）：{spec_path} —— 源形状变了，拒绝导出"
        )
    out: dict = {}
    for key, entry in raw.items():
        key = str(key)
        if key.startswith("_"):
            # _meta / _categories：与装载体同一过滤规则（game/core/texts.py:_load_specs）
            continue
        if not isinstance(entry, dict):
            raise ValueError(
                f"文案 {key!r} 不是对象（实为 {type(entry).__name__}）—— 编辑器只认对象形态，拒绝导出"
            )
        if not str(entry.get("value") or ""):
            raise ValueError(f"文案 {key!r} 缺 value 或模板为空 —— 拒绝导出（schema：required + minLength≥1）")
        out[key] = entry
    return out


def derive_instances(src_root: str = REPO_ROOT) -> dict:
    """副本域：取 `INSTANCES` 运行时表，把游戏侧**内联怪元组**投影成框架要求的**引用字符串**。

    真源（2026-09-13 核实，行号以当时文件为准）：
      game/data/instances.py:44        INSTANCES = {...}  → **27 条**（不是 docstring 里写的 22：
                                       新增 inst_rust_dock / inst_candle_crypt / inst_thunder_mine /
                                       inst_whirl_arena / inst_blacktide_opera）。每本固定 3 层 = 81 层，
                                       层内怪槽位 121 个，全部能在 _INDEXES["monsters"] 里反查到。
      game/data/instances.py:3686      INSTANCE_BOSS_EQUIP_DROP（27 条，key 与 INSTANCES 完全对齐）
      game/data/_assembly.py:150-165   装配期把 INSTANCE_STAGE_MAPS（22 本）就地
                                       `_stages[_idx].update(_emap)` 进 stages → 运行时层内多出
                                       `desc`（66 层）/`pois`（65 层 · 共 66 个 POI）/`npcs`（6 层，每层 1 个）/
                                       `secret`（4 层）。**所以必须取 import 后的运行时表**：
                                       照 instances.py 字面量解析会导出缺 desc/pois/npcs/secret 的层。

    为什么要投影（本域与 items/classes/skills 最大的不同）：
      框架 schemas/instances.schema.json 的 `instance` def 把怪/Boss/POI/secret/终局 Boss 声明成
      **内容侧引用字符串**（框架零枚举），而游戏侧存的是**内联战斗元组**
      （6 元组 = (id, 名, role, lv, [技能 id], [掉落名])）：
        顶层 boss        : 6 元组（27/27）
        层内 monsters    : [6 元组, ...]（43 层）或 []（21 层）
        层内 elite/boss  : **扁平** 6 元组，单怪不套外层数组（各 27 层），其余 20 层显式 None
        层内 pois        : [{"id","type","name","hint","loot"...}]（65 层）
        层内 secret      : {"cond": {...}, "pois": [POI...]} —— 是**对象**，不是字符串（4 层）
      逐条真跑 `editor.validate.validate_entry("instances", 原样条目)` = **0/27 通过**
      （每条 11-17 个错误；路径聚合：boss×27、stages[i].elite[i]×81、stages[i].boss[i]×81、
      stages[i].monsters[i]×67、stages[i].pois[i]×66、stages[i].boss(None)×20、
      stages[i].elite(None)×20、stages[i].secret×4）。
      本函数按下面 6 条规则投影后 = **27/27 通过**，且投影只「取引用」，
      **原值原样挂在 `<槽位>_data` 额外键**下（schema 三处 additionalProperties: true 放行）→ 零信息丢失。

    投影规则（只动这 6+1 个槽位，其余字段 byte 级原样）：
      顶层 boss    : 6 元组 → b[0]；原元组 → `boss_data`
      层 monsters  : [t → t[0]]；有内联时原值 → `monsters_data`（空列表保持空列表）
      层 elite     : 扁平 6 元组 → [t[0]]；条目列表 → [t[0]...]；None → 删键；原值 → `elite_data`
      层 boss      : 同 elite（原值 → `boss_data`）
      层 pois      : 字典列表 → [id,...]；原列表 → `poi_data`
      层 secret    : 对象 → 第一个藏宝 POI 的 id（无则 cond.poi）；原对象 → `secret_data`
      层 npcs      : 6 层都恰好 1 个 id → 顺手填框架的单数 `npc`（string）槽位；`npcs` 列表原样保留
      顶层         : INSTANCE_BOSS_EQUIP_DROP[key] → `boss_equip_drop`（独立表、只此一处、
                     框架无对应域，不挂 = 丢数据；其 `eq_*` 落在 EQUIP_ROSTER，不在 ITEMS 里 →
                     在新域导出前是**跨域悬空引用**）

    未导出（属别的域）：SUBAREA_LINKS（dungeon_links.py，27 张副本地图房间连通表，key = 副本 key 去掉
    `inst_` 前缀）、DUNGEON_POI_MOUNTS（dungeon_pois.py，55 键 / 66 POI，已按 id 前缀去重）、
    INSTANCE_STAGE_MAPS（已装配进 stages）、INVESTIGATION_POINTS（instance_investigation.py，22 本 90 点）、
    MINION / phases / mech / chains / on_interrupt 等战斗脚本字段（额外键原样随条目进包）。
    """
    tables = _import_module("instances", src_root)
    raw = getattr(tables, "INSTANCES", None)
    if not isinstance(raw, dict):
        raise ValueError("game.data.instances.INSTANCES 不是 dict —— 源形状变了，拒绝导出")
    drops = getattr(tables, "INSTANCE_BOSS_EQUIP_DROP", None)

    def _key_of(t, where):
        """6 元组（或条目列表的元素）→ 第一元素（怪 id）。形状不对就拒绝导出。"""
        if not isinstance(t, (list, tuple)) or not t:
            raise ValueError(f"{where}: 怪元组 {t!r} 不是非空列表 —— 源形状变了，拒绝导出")
        first = t[0]
        if not isinstance(first, str) or not first:
            raise ValueError(f"{where}: 怪元组首元素不是 id 字符串：{t!r}")
        return first

    out: dict = {}
    for inst_key in sorted(raw):
        entry = raw[inst_key]
        if not isinstance(entry, dict):
            raise ValueError(f"INSTANCES[{inst_key}] 不是 dict —— 源形状变了，拒绝导出")
        item = dict(entry)

        boss = item.get("boss")
        if isinstance(boss, (list, tuple)):
            if not boss:
                raise ValueError(f"{inst_key}.boss 是空列表 —— 不设终局 Boss 请删掉这个键")
            item["boss"] = _key_of(boss, f"{inst_key}.boss")
            item["boss_data"] = boss
        elif boss is not None:
            raise ValueError(f"{inst_key}.boss 既不是 6 元组也不是 None：{type(boss).__name__}")

        stages = item.get("stages")
        if not isinstance(stages, list) or not stages:
            raise ValueError(f"{inst_key}.stages 不是非空列表 —— 源形状变了，拒绝导出")
        new_stages = []
        for idx, stage in enumerate(stages):
            if not isinstance(stage, dict):
                raise ValueError(f"{inst_key}.stages[{idx}] 不是 dict —— 源形状变了，拒绝导出")
            ns = dict(stage)
            where = f"{inst_key}.stages[{idx}]"

            slot = stage.get("monsters")
            if slot is not None:
                if not isinstance(slot, list):
                    raise ValueError(f"{where}.monsters 不是列表：{type(slot).__name__}")
                if slot and isinstance(slot[0], (list, tuple)):
                    ns["monsters"] = [_key_of(t, where + ".monsters") for t in slot]
                    ns["monsters_data"] = slot
                else:
                    ns["monsters"] = [_key_of(t, where + ".monsters") for t in slot]

            for f in ("elite", "boss"):
                slot = stage.get(f)
                if slot is None:
                    ns.pop(f, None)          # 框架声明是 array，显式 None 会被判 "None is not of type 'array'"
                    continue
                if not isinstance(slot, list):
                    raise ValueError(f"{where}.{f} 不是列表：{type(slot).__name__}")
                if slot and isinstance(slot[0], (list, tuple)):     # 条目列表：[6 元组, ...]
                    ns[f] = [_key_of(t, where + "." + f) for t in slot]
                    ns[f + "_data"] = slot
                else:                                              # 扁平 6 元组：单怪
                    ns[f] = [_key_of(slot, where + "." + f)]
                    ns[f + "_data"] = slot

            pois = stage.get("pois")
            if pois is not None:
                if not isinstance(pois, list):
                    raise ValueError(f"{where}.pois 不是列表：{type(pois).__name__}")
                ns["pois"] = [p["id"] if isinstance(p, dict) else p for p in pois]
                ns["poi_data"] = pois

            sec = stage.get("secret")
            if sec is not None:
                if isinstance(sec, dict):
                    ids = [p.get("id") for p in (sec.get("pois") or [])
                           if isinstance(p, dict) and p.get("id")]
                    ns["secret"] = ids[0] if ids else str((sec.get("cond") or {}).get("poi") or "secret")
                    ns["secret_data"] = sec
                else:
                    ns["secret"] = str(sec)

            npcs = stage.get("npcs")
            if isinstance(npcs, list) and len(npcs) == 1 and isinstance(npcs[0], str):
                ns["npc"] = npcs[0]          # 框架单数槽位（string）；npcs 列表原样留着

            new_stages.append(ns)
        item["stages"] = new_stages

        d = drops.get(inst_key) if isinstance(drops, dict) else None
        if isinstance(d, dict):
            item["boss_equip_drop"] = d

        out[inst_key] = item
    return out


DERIVERS = {
    "affixes": derive_affixes,
    "classes": derive_classes,
    "commands": derive_commands,
    "drop_pools": derive_drop_pools,
    "effect_rules": derive_effect_rules,
    "instances": derive_instances,
    "items": derive_items,
    "maps": derive_maps,
    "monsters": derive_monsters,
    "passive_proc": derive_passive_proc,
    "skills": derive_skills,
    "texts": derive_texts,
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
