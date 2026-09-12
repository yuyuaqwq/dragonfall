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
    "monsters", "affixes", "maps", "drop_pools",
    "instances", "effect_rules", "passive_proc", "commands", "texts", "tlogs",
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


DERIVERS = {
    "items": derive_items,
    "classes": derive_classes,
    "skills": derive_skills,
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


def content_sub(domain: str, out_root: str) -> str:
    """域数据落 `content/data/` 还是 `content/rules/` —— **问框架**，不硬编码第二份列表。

    为什么必须问：框架 `editor/packages.py` 的 DOMAINS 给每个域标了 kind（rules / data），
    `PK.domain_path()` 按它取路径（effect_rules / passive_proc 走 `content/rules/`）。
    导出器若写错边 → 文件在、清单也声明了、同步门禁也可能全绿，但编辑器读另一边
    → **显示 0 条且不报错**（最难查的那类故障，2026-09-13 由域研究实测发现）。
    """
    fw = os.path.abspath(out_root)
    if fw not in sys.path:
        sys.path.insert(0, fw)
    try:
        from editor import packages as PK      # noqa: PLC0415
    except Exception as e:                     # noqa: BLE001
        raise ValueError(
            f"读框架域注册表失败（{fw}）：{e} —— 拒绝猜落点，请确认 --out 指向框架仓"
        ) from e
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
