#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 — 数据域 Schema 校验器（配置编辑器前置，路线图 2.1）

用法
----
    python schema/validate.py                 # 全量校验；有违规 → exit 1，全绿 → exit 0
    python schema/validate.py --domain skills # 只验一个域
    python schema/validate.py --json          # 机器可读结果（stdout 仅 JSON）
    python schema/validate.py --quiet         # 只打印汇总行
    python schema/validate.py --strict-unknown  # 未在 schema 中声明的字段也算违规

设计
----
* 校验引擎优先用第三方 `jsonschema`（draft 2020-12）；不可用时退化为内置最小校验器
  （支持本仓 schema 实际用到的关键字子集：type/enum/const/required/properties/
  additionalProperties/propertyNames/items/prefixItems/anyOf/oneOf/allOf/$ref/
  minimum/maximum/exclusiveMinimum/minLength/minItems/maxItems/minProperties/pattern）。
  两条路径对现网数据的判定结果一致（tests/test_schema_validate.py 锁死）。
* 「违规 (= errors)」决定 exit code；「提醒 (= warnings)」只进报告不拦门禁。
  跨表引用完整性：闭合集（词条池→词条、怪技能→技能表、掉落名→物品名、名册图纸→名册 id）
  记为 error，需要人工判断的（被动 proc 双注册表、机制名归属）记为 warning。
* 取数 = **包内域/门面**（`framework/games/orlandia/content/**`）；不 import 引擎业务
  （`game/core`、`game/battle2`）。★ PFIX P4：`90fc06b` 删掉宿主 `game/data/**` 后，
  原来的 `game.data.*` 取数口已改为包内门面（`_import_data()` 段有逐名对账说明）。
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys

try:  # pragma: no cover - 环境相关
    import jsonschema
    from jsonschema import Draft202012Validator
    HAS_JSONSCHEMA = True
except Exception:  # pragma: no cover
    jsonschema = None
    Draft202012Validator = None
    HAS_JSONSCHEMA = False

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(ROOT, "schema")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DRAFT = "https://json-schema.org/draft/2020-12/schema"
ALL_DOMAINS = ("skills", "monsters", "affixes", "items", "effect_rules", "passive_proc")


# --------------------------------------------------------------------------- io
def load_schema(name: str) -> dict:
    with open(os.path.join(SCHEMA_DIR, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_target(doc: dict, def_name: str) -> dict:
    """把 doc 里的某个 $def 提升成可独立校验的 schema（$ref 仍指向同一 doc 的 $defs）。"""
    return {"$schema": DRAFT, "$defs": doc["$defs"], "allOf": [{"$ref": "#/$defs/" + def_name}]}


# ------------------------------------------------------------------ minimal engine
def _min_validate(inst, schema, defs, path=""):
    """内置最小校验器，返回 [(json_path, message), ...]。"""
    errs = []
    if not isinstance(schema, dict):
        return errs

    if "$ref" in schema:
        ref = schema["$ref"]
        m = re.match(r"^#/\$defs/(.+)$", ref)
        if m and m.group(1) in defs:
            return _min_validate(inst, defs[m.group(1)], defs, path)
        return [(path, f"无法解析 $ref {ref}")]

    for key in ("allOf",):
        if key in schema:
            for sub in schema[key]:
                errs += _min_validate(inst, sub, defs, path)
    if "anyOf" in schema:
        if not any(not _min_validate(inst, sub, defs, path) for sub in schema["anyOf"]):
            errs.append((path, "不满足 anyOf 中任一分支"))
    if "oneOf" in schema:
        hits = sum(1 for sub in schema["oneOf"] if not _min_validate(inst, sub, defs, path))
        if hits == 0:
            errs.append((path, "不满足 oneOf 中任一分支"))
        elif hits > 1:
            errs.append((path, f"同时满足 oneOf 中 {hits} 个分支"))

    if "enum" in schema and inst not in schema["enum"]:
        errs.append((path, f"取值 {inst!r} 不在枚举 {schema['enum']!r} 内"))
    if "const" in schema and inst != schema["const"]:
        errs.append((path, f"取值 {inst!r} != const {schema['const']!r}"))

    t = schema.get("type")
    if t is not None:
        types = t if isinstance(t, list) else [t]
        ok = False
        for tt in types:
            if tt == "object" and isinstance(inst, dict):
                ok = True
            elif tt == "array" and isinstance(inst, list):
                ok = True
            elif tt == "string" and isinstance(inst, str):
                ok = True
            elif tt == "boolean" and isinstance(inst, bool):
                ok = True
            elif tt == "integer" and isinstance(inst, int) and not isinstance(inst, bool):
                ok = True
            elif tt == "number" and isinstance(inst, (int, float)) and not isinstance(inst, bool):
                ok = True
            elif tt == "null" and inst is None:
                ok = True
        if not ok:
            errs.append((path, f"类型应为 {t}，实际 {type(inst).__name__}"))
            return errs

    if isinstance(inst, str):
        if "minLength" in schema and len(inst) < schema["minLength"]:
            errs.append((path, f"字符串长度 {len(inst)} < minLength {schema['minLength']}"))
        if "pattern" in schema and not re.search(schema["pattern"], inst):
            errs.append((path, f"字符串 {inst!r} 不匹配 pattern {schema['pattern']!r}"))

    if isinstance(inst, (int, float)) and not isinstance(inst, bool):
        if "minimum" in schema and inst < schema["minimum"]:
            errs.append((path, f"数值 {inst} < minimum {schema['minimum']}"))
        if "maximum" in schema and inst > schema["maximum"]:
            errs.append((path, f"数值 {inst} > maximum {schema['maximum']}"))
        if "exclusiveMinimum" in schema and inst <= schema["exclusiveMinimum"]:
            errs.append((path, f"数值 {inst} <= exclusiveMinimum {schema['exclusiveMinimum']}"))

    if isinstance(inst, list):
        if "minItems" in schema and len(inst) < schema["minItems"]:
            errs.append((path, f"数组长度 {len(inst)} < minItems {schema['minItems']}"))
        if "maxItems" in schema and len(inst) > schema["maxItems"]:
            errs.append((path, f"数组长度 {len(inst)} > maxItems {schema['maxItems']}"))
        pi = schema.get("prefixItems") or []
        for i, sub in enumerate(pi):
            if i < len(inst):
                errs += _min_validate(inst[i], sub, defs, f"{path}[{i}]")
        items = schema.get("items")
        if items is False and len(inst) > len(pi):
            errs.append((path, f"数组长度 {len(inst)} > prefixItems {len(pi)}（items:false）"))
        elif isinstance(items, dict):
            for i, v in enumerate(inst):
                if i >= len(pi):
                    errs += _min_validate(v, items, defs, f"{path}[{i}]")

    if isinstance(inst, dict):
        if "minProperties" in schema and len(inst) < schema["minProperties"]:
            errs.append((path, f"对象属性数 {len(inst)} < minProperties {schema['minProperties']}"))
        for req in schema.get("required", []):
            if req not in inst:
                errs.append((path, f"缺少必填字段 {req!r}"))
        pn = schema.get("propertyNames")
        if pn:
            for k in inst:
                if _min_validate(k, pn, defs, path):
                    errs.append((f"{path}.<key>", f"键名 {k!r} 不满足 propertyNames"))
        props = schema.get("properties") or {}
        for k, v in inst.items():
            if k in props:
                errs += _min_validate(v, props[k], defs, f"{path}.{k}")
        ap = schema.get("additionalProperties", True)
        for k, v in inst.items():
            if k in props:
                continue
            if ap is False:
                errs.append((f"{path}.{k}", f"不允许的额外字段 {k!r}"))
            elif isinstance(ap, dict):
                errs += _min_validate(v, ap, defs, f"{path}.{k}")
    return errs


def validate_instance(instance, doc: dict, def_name: str):
    """返回 [(json_path, message), ...]。"""
    target = build_target(doc, def_name)
    if HAS_JSONSCHEMA:
        v = Draft202012Validator(target)
        out = []
        for e in sorted(v.iter_errors(instance), key=lambda x: list(x.path)):
            out.append(("$" + "".join(f".{p}" if not isinstance(p, int) else f"[{p}]" for p in e.path),
                        e.message))
        return out
    return _min_validate(instance, target, doc["$defs"])


# ------------------------------------------------------------------- data import
# ★ PFIX P4（2026-09-15）：取数口从「宿主 `game.data.**`」改成「**包内域/门面**」。
#   `90fc06b`（B14 开关：删宿主 game/data 87 文件）之后，原 `_import_data()` 的
#   `import game.data.skills` 等一律 ModuleNotFoundError ⇒ `validate_all()` 走
#   `import_error` 分支早退（门禁假红、五个域一条都没验）。本段只换**取值来源**，
#   校验/跨表/基线口径一字未改；逐名对账（legacy 名 → 包内家）见 `out/W-PFIX.md §P4`。
class _Domain:
    """`game.data.<X>` 的替身：只暴露同名属性（值 = 包内域/门面）。"""

    def __init__(self, legacy: str, **attrs):
        self.__dict__.update(attrs)
        self._legacy = legacy

    def __repr__(self):
        return "<pkg-domain shim %s (%d attrs)>" % (
            self._legacy, len(self.__dict__) - 1)


_PKG_DIR = os.path.join(ROOT, "framework", "games", "orlandia")   # 内容包根（`content`）
_ENGINE_DIR = os.path.join(ROOT, "framework")                      # 引擎根（`saintess_engine`）
# ★ 2026-09-24：扩展包搜索根（`<引擎根>/extends/ext_*`）—— 搬迁后 `content/**` 会
#   `import ext_combat` 等；缺这一根 ⇒ 本脚本报「数据模块导入失败: No module named 'ext_combat'」。
_EXT_DIR = os.path.join(_ENGINE_DIR, "extends")
for _p in (_PKG_DIR, _ENGINE_DIR, _EXT_DIR):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)


def _read_content_json(*parts):
    """读包内 `content/<parts>` JSON（缺文件 / 坏 JSON → `{}`，不抛；与 `content/tables.py` 同款）。"""
    try:
        with open(os.path.join(_PKG_DIR, "content", *parts), encoding="utf-8") as f:
            return json.load(f) or {}
    except (OSError, ValueError):
        return {}


def _import_data():
    """返回 10 个 legacy `game.data.<X>` 名的替身（属性取包内域/门面）。"""
    from content import (catalog_b143, catalog_core, catalog_items, catalog_quests,
                         catalog_rules, catalog_space)
    from content.mech import class_data as _mcd
    from content.mech import params as _mp
    return {
        "game.data.skills": _Domain(
            "skills",
            PLAYER_SKILLS=catalog_core.PLAYER_SKILLS,
            BRANCH_SKILLS=catalog_core.BRANCH_SKILLS,
            TUTOR_SKILLS=catalog_core.TUTOR_SKILLS),
        "game.data.subareas": _Domain("subareas", SUBAREAS=catalog_space.SUBAREAS),
        "game.data.instances": _Domain("instances", INSTANCES=catalog_space.INSTANCES),
        "game.data.monsters": _Domain(
            "monsters",
            MONSTER_SKILLS=catalog_quests.MONSTER_SKILLS,
            ELITE_EQUIP_DROP=catalog_quests.ELITE_EQUIP_DROP),
        "game.data.hidden_monsters": _Domain(
            "hidden_monsters", HIDDEN_MONSTERS=catalog_b143.HIDDEN_MONSTERS),
        "game.data.affixes": _Domain(
            "affixes",
            AFFIXES=catalog_items.AFFIXES,
            AFFIX_POOL_BY_QUALITY=catalog_b143.AFFIX_POOL_BY_QUALITY,
            # `AFFIX_KIND`：包内**无**该表（`content/catalog_legacy.py:GAPS` 登记；
            # 宿主原表 `game/data/affixes.py:AFFIX_KIND` 随 `90fc06b` 删除）——
            # 读包内同名 JSON（不存在 ⇒ 空表：不报错，也不假装验过）。缺口已登记。
            AFFIX_KIND=_read_content_json("rules", "affix_kind.json"),
            AFFIX_AFFINITY_POOLS=catalog_rules.AFFIX_AFFINITY_POOLS),
        "game.data.items": _Domain("items", ITEMS=catalog_items.ITEMS),
        "game.data.equip_roster": _Domain(
            "equip_roster",
            EQUIP_ROSTER=catalog_items.EQUIP_ROSTER,
            EQUIP_ROSTER_BY_NAME=catalog_items.EQUIP_ROSTER_BY_NAME),
        "game.data.battle_rules": _Domain(
            "battle_rules",
            # `PASSIVE_PROC` 真源 = 包内 `content/rules/passive_proc.json`
            # （与 `content/mech/class_mech.py::_passive_proc_rules()` 同源同读法）
            PASSIVE_PROC=_read_content_json("rules", "passive_proc.json"),
            EFFECT_RULES=catalog_rules.EFFECT_RULES,
            MECH_CASH=_mcd.MECH_CASH,
            EFFECT_ACTIONS=_mp.EFFECT_ACTIONS),
        "game.data.classes": _Domain("classes", CLASSES=catalog_core.CLASSES),
    }


# --------------------------------------------------------------------- collectors
def _iter_skills(M):
    for cid, cd in M["game.data.skills"].PLAYER_SKILLS.items():
        for sid, sk in cd.get("skills", {}).items():
            yield f"PLAYER_SKILLS/{cid}/{sid}", sk
    for cid, cd in M["game.data.skills"].BRANCH_SKILLS.items():
        for lv, branches in cd.get("branches", {}).items():
            for bname, skills in branches.items():
                for sid, sk in skills.items():
                    yield f"BRANCH_SKILLS/{cid}/{bname}/{sid}", sk
    for cid, cd in M["game.data.skills"].TUTOR_SKILLS.items():
        for sid, sk in cd.items():
            yield f"TUTOR_SKILLS/{cid}/{sid}", sk


def _iter_monster_templates(M):
    for sid, subareas in M["game.data.subareas"].SUBAREAS.items():
        for sa in subareas:
            base = sa.get("id")
            for t in sa.get("monsters") or []:
                yield f"SUBAREAS/{base}", t
            for key in ("elite", "boss"):
                v = sa.get(key)
                if isinstance(v, (list, tuple)) and v and not isinstance(v[0], (list, tuple)):
                    yield f"SUBAREAS/{base}.{key}", v
                elif isinstance(v, (list, tuple)):
                    for t in v:
                        yield f"SUBAREAS/{base}.{key}", t
    for iid, inst in M["game.data.instances"].INSTANCES.items():
        if not isinstance(inst, dict):
            continue
        b = inst.get("boss")
        if isinstance(b, (list, tuple)) and b and not isinstance(b[0], (list, tuple)):
            yield f"INSTANCES/{iid}.boss", b
        for stage in inst.get("stages") or []:
            if not isinstance(stage, dict):
                continue
            tag = f"INSTANCES/{iid}/{stage.get('name') or stage.get('id')}"
            for t in stage.get("monsters") or []:
                yield tag, t
            sb = stage.get("boss")
            if isinstance(sb, (list, tuple)) and sb and not isinstance(sb[0], (list, tuple)):
                yield tag + ".boss", sb
        for mn in inst.get("minions") or []:
            if isinstance(mn, dict) and isinstance(mn.get("monster"), (list, tuple)):
                yield f"INSTANCES/{iid}.minions", mn["monster"]


def _item_names(M):
    return {v["name"] for v in M["game.data.items"].ITEMS.values()}


# ------------------------------------------------------------------------ schemas
def _coverage(entries):
    total = len(entries)
    fields = collections.defaultdict(collections.Counter)
    for _label, obj in entries:
        if isinstance(obj, dict):
            for k, v in obj.items():
                fields[k][type(v).__name__] += 1
    out = {}
    for f, c in sorted(fields.items(), key=lambda x: (-sum(x[1].values()), x[0])):
        n = sum(c.values())
        out[f] = {"presence": n, "cover": round(n / total, 4) if total else 1.0,
                  "types": dict(c)}
    return out


def _unknown_fields(entries, props):
    counter = collections.Counter()
    for _label, obj in entries:
        if isinstance(obj, dict):
            for k in obj:
                if k not in props:
                    counter[k] += 1
    return dict(counter)


# -------------------------------------------------------------------- domain runs
def _run_domain(domain, docs, M, strict_unknown):
    """返回 (entry_count, errors, warnings, coverage, extra)"""
    errors, warnings = [], []
    coverage, extra = {}, {}

    def err(entry, field, problem, value=None):
        errors.append({"domain": domain, "entry": entry, "field": field,
                       "problem": problem, "value": value})

    def warn(entry, field, problem, value=None):
        warnings.append({"domain": domain, "entry": entry, "field": field,
                         "problem": problem, "value": value})

    # ---------------- skills
    if domain == "skills":
        entries = list(_iter_skills(M))
        doc = docs["skill.schema.json"]
        coverage = _coverage(entries)
        props = doc["$defs"]["skill"]["properties"]
        for label, obj in entries:
            for p, msg in validate_instance(obj, doc, "skill"):
                err(label, p, msg)
            if strict_unknown:
                for k in obj:
                    if k not in props:
                        err(label, k, "字段未在 skill.schema 声明")
        # containers
        for def_name, table in (("player_skills", M["game.data.skills"].PLAYER_SKILLS),
                                ("branch_skills", M["game.data.skills"].BRANCH_SKILLS),
                                ("tutor_skills", M["game.data.skills"].TUTOR_SKILLS)):
            for p, msg in validate_instance(table, doc, def_name):
                err(f"<container:{def_name}>", p, msg)
        # 跨表：res_cost key 已在 schema 覆盖；被动 proc 归属为提醒
        passives = [(lbl, o["passive"]) for lbl, o in entries if isinstance(o.get("passive"), dict)]
        declared = set(M["game.data.battle_rules"].PASSIVE_PROC)
        miss = collections.Counter()
        for lbl, ps in passives:
            proc = ps.get("proc")
            if proc and proc not in declared:
                miss[proc] += 1
        for proc, n in sorted(miss.items()):
            warn(f"<passive.proc ×{n}>", "passive.proc",
                 f"proc {proc!r} 未在 saintess_engine PASSIVE_PROC 声明（可能在 core/passive_procs 注册，迁移期双表并存）",
                 proc)
        extra["passive_proc_missing"] = dict(miss)
        mechs = collections.Counter(o["mech"] for _l, o in entries if o.get("mech"))
        declared_mech = set(M["game.data.battle_rules"].EFFECT_RULES) | set(M["game.data.battle_rules"].MECH_CASH)
        undecl = {m: n for m, n in mechs.items() if m not in declared_mech}
        if undecl:
            warn(f"<mech ×{len(undecl)}>", "mech",
                 f"{len(undecl)} 个 mech 未在 EFFECT_RULES/MECH_CASH 声明: {sorted(undecl)}", undecl)
        extra["mech_undeclared"] = undecl
        effs = {o["effect"] for _l, o in entries if o.get("effect")}
        ea = set(M["game.data.battle_rules"].EFFECT_ACTIONS)
        if effs - ea:
            warn(f"<effect ×{len(effs - ea)}>", "effect",
                 f"{len(effs - ea)} 个 effect 未在 EFFECT_ACTIONS 声明: {sorted(effs - ea)}")
        extra["effect_undeclared"] = sorted(effs - ea)
        n_none = sum(1 for _l, o in entries if o.get("cast") == "None")
        if n_none:
            warn("<cast='None'>", "cast", f"{n_none} 条技能 cast 用历史哨兵字符串 'None'（非数值）", n_none)
        bad_passive_cast = [(l, o.get("name")) for l, o in entries
                            if o.get("kind") == "被动" and isinstance(o.get("cast"), (int, float))]
        for l, nm in bad_passive_cast:
            warn(l, "cast", f"kind=被动 但 cast 是数值 {nm!r}（其余被动均 cast='None'）")
        extra["cast_none"] = n_none
        return len(entries), errors, warnings, coverage, extra

    # ---------------- monsters
    if domain == "monsters":
        doc = docs["monster.schema.json"]
        mskills = list(M["game.data.monsters"].MONSTER_SKILLS.items())
        coverage = _coverage(mskills)
        props = doc["$defs"]["monster_skill"]["properties"]
        for sid, sk in mskills:
            for p, msg in validate_instance(sk, doc, "monster_skill"):
                err(f"MONSTER_SKILLS/{sid}", p, msg)
            if strict_unknown:
                for k in sk:
                    if k not in props:
                        err(f"MONSTER_SKILLS/{sid}", k, "字段未在 monster_skill.schema 声明")
        for p, msg in validate_instance(M["game.data.monsters"].MONSTER_SKILLS, doc, "monster_skill_table"):
            err("<container:MONSTER_SKILLS>", p, msg)
        templates = list(_iter_monster_templates(M))
        skill_ids = set(M["game.data.monsters"].MONSTER_SKILLS)
        names = _item_names(M)
        for lbl, t in templates:
            for p, msg in validate_instance(t, doc, "monster_template"):
                err(lbl, p, msg)
            if isinstance(t, (list, tuple)) and len(t) == 6:
                for s in t[4] or []:
                    if s not in skill_ids:
                        err(lbl, "skills", f"引用了不存在的怪物技能 {s!r}", s)
                for d in t[5] or []:
                    if d not in names:
                        err(lbl, "drops", f"掉落物名 {d!r} 不在 ITEMS 中", d)
        hidden = list(M["game.data.hidden_monsters"].HIDDEN_MONSTERS.items())
        for hid, hm in hidden:
            for p, msg in validate_instance(hm, doc, "hidden_monster"):
                err(f"HIDDEN_MONSTERS/{hid}", p, msg)
            for s in hm.get("skills") or []:
                if s not in skill_ids:
                    err(f"HIDDEN_MONSTERS/{hid}", "skills", f"引用了不存在的怪物技能 {s!r}", s)
            for d in hm.get("drops") or []:
                if d not in names:
                    err(f"HIDDEN_MONSTERS/{hid}", "drops", f"掉落物名 {d!r} 不在 ITEMS 中", d)
        ed = M["game.data.monsters"].ELITE_EQUIP_DROP
        for p, msg in validate_instance(ed, doc, "elite_equip_drop"):
            err("<ELITE_EQUIP_DROP>", p, msg)
        roster = set(M["game.data.equip_roster"].EQUIP_ROSTER)
        for k, v in ed.items():
            if v not in roster:
                err("<ELITE_EQUIP_DROP>", k, f"装备 id {v!r} 不在 EQUIP_ROSTER 中", v)
        coverage["<monster_template>"] = {"presence": len(templates), "cover": 1.0,
                                          "types": {"array": len(templates)}}
        return len(mskills) + len(templates) + len(hidden), errors, warnings, coverage, extra

    # ---------------- affixes
    if domain == "affixes":
        doc = docs["affix.schema.json"]
        entries = list(M["game.data.affixes"].AFFIXES.items())
        coverage = _coverage(entries)
        props = doc["$defs"]["affix"]["properties"]
        for k, v in entries:
            for p, msg in validate_instance(v, doc, "affix"):
                err(f"AFFIXES/{k}", p, msg)
            if strict_unknown:
                for f in v:
                    if f not in props:
                        err(f"AFFIXES/{k}", f, "字段未在 affix.schema 声明")
        for p, msg in validate_instance(M["game.data.affixes"].AFFIXES, doc, "affix_table"):
            err("<container:AFFIXES>", p, msg)
        for p, msg in validate_instance(M["game.data.affixes"].AFFIX_POOL_BY_QUALITY, doc,
                                        "affix_pool_by_quality"):
            err("<AFFIX_POOL_BY_QUALITY>", p, msg)
        for p, msg in validate_instance(M["game.data.affixes"].AFFIX_KIND, doc, "affix_kind"):
            err("<AFFIX_KIND>", p, msg)
        ids = set(M["game.data.affixes"].AFFIXES)
        for q, pool in M["game.data.affixes"].AFFIX_POOL_BY_QUALITY.items():
            for a in pool:
                if a not in ids:
                    err(f"AFFIX_POOL_BY_QUALITY/{q}", a, "词条池引用了不存在的词条 id", a)
        aff = getattr(M["game.data.affixes"], "AFFIX_AFFINITY_POOLS", {})
        for name, pools in aff.items():
            seq = pools.values() if isinstance(pools, dict) else (pools,)
            for pool in seq:
                if isinstance(pool, list):
                    for a in pool:
                        if a not in ids:
                            err(f"AFFIX_AFFINITY_POOLS/{name}", a, "流派池引用了不存在的词条 id", a)
        ons = collections.Counter(type(v["effect"].get("on")).__name__
                                  for _k, v in entries
                                  if isinstance(v.get("effect"), dict) and "on" in v["effect"])
        if len(ons) > 1:
            warn("<affix effect.on>", "effect.on", f"形态不统一: {dict(ons)}")
        return len(entries), errors, warnings, coverage, extra

    # ---------------- items
    if domain == "items":
        doc = docs["item.schema.json"]
        entries = list(M["game.data.items"].ITEMS.items())
        coverage = _coverage(entries)
        props = doc["$defs"]["item"]["properties"]
        for k, v in entries:
            for p, msg in validate_instance(v, doc, "item"):
                err(f"ITEMS/{k}", p, msg)
            if strict_unknown:
                for f in v:
                    if f not in props:
                        err(f"ITEMS/{k}", f, "字段未在 item.schema 声明")
        for p, msg in validate_instance(M["game.data.items"].ITEMS, doc, "item_table"):
            err("<container:ITEMS>", p, msg)
        roster = M["game.data.equip_roster"].EQUIP_ROSTER_BY_NAME
        for k, v in entries:
            bp, rid = v.get("blueprint_for"), v.get("roster_id")
            if bp and not rid and bp in roster:
                err(f"ITEMS/{k}", "roster_id",
                    f"blueprint_for={bp!r} 指向名册装备（{roster[bp]}）但缺 roster_id → 学习图纸无法 resolve")
            if rid and not bp:
                err(f"ITEMS/{k}", "blueprint_for", f"有 roster_id={rid!r} 但缺 blueprint_for（配对字段）")
        no_type = [k for k, v in entries if "type" not in v]
        if no_type:
            warn(f"<缺 type ×{len(no_type)}>", "type", f"{len(no_type)} 条物品没有 type 字段", len(no_type))
        hets = collections.Counter()
        for _k, v in entries:
            ed = v.get("effect_data")
            if isinstance(ed, dict):
                for f, val in ed.items():
                    hets[f + ":" + type(val).__name__] += 1
        mixed = sorted({f.split(":")[0] for f in hets
                        if len({x.split(":")[1] for x in hets if x.split(":")[0] == f.split(":")[0]}) > 1})
        for f in mixed:
            tset = sorted({x.split(":")[1] for x in hets if x.split(":")[0] == f})
            warn("<effect_data 类型>", "effect_data." + f, f"同一键在不同物品里类型不一: {tset}")
        extra["no_type"] = len(no_type)
        return len(entries), errors, warnings, coverage, extra

    # ---------------- effect_rules
    if domain == "effect_rules":
        doc = docs["effect_rules.schema.json"]
        B = M["game.data.battle_rules"]
        entries = list(B.EFFECT_RULES.items())
        coverage = _coverage(entries)
        for k, v in entries:
            for p, msg in validate_instance(v, doc, "effect_rule"):
                err(f"EFFECT_RULES/{k}", p, msg)
        for p, msg in validate_instance(B.EFFECT_RULES, doc, "effect_rules_table"):
            err("<container:EFFECT_RULES>", p, msg)
        for p, msg in validate_instance(B.EFFECT_ACTIONS, doc, "effect_actions"):
            err("<EFFECT_ACTIONS>", p, msg)
        for p, msg in validate_instance(B.MECH_CASH, doc, "mech_cash"):
            err("<MECH_CASH>", p, msg)
        keys = set(B.EFFECT_RULES)
        for mk, mv in B.MECH_CASH.items():
            kk = mv.get("key")
            for x in ([kk] if isinstance(kk, str) else (kk or [])):
                if x not in keys:
                    err(f"MECH_CASH/{mk}", "key", f"引用了 EFFECT_RULES 未声明的状态 {x!r}", x)
            up = mv.get("upgrade")
            if isinstance(up, dict) and up.get("proc") and up["proc"] not in B.PASSIVE_PROC:
                warn(f"MECH_CASH/{mk}", "upgrade.proc",
                     f"proc {up['proc']!r} 未在 PASSIVE_PROC 声明")
        classes = set(M["game.data.classes"].CLASSES)
        for k, v in entries:
            for c in v.get("start_classes") or []:
                if c not in classes:
                    err(f"EFFECT_RULES/{k}", "start_classes", f"未知职业 id {c!r}", c)
        return len(entries), errors, warnings, coverage, extra

    # ---------------- passive_proc
    if domain == "passive_proc":
        doc = docs["passive_proc.schema.json"]
        B = M["game.data.battle_rules"]
        entries = list(B.PASSIVE_PROC.items())
        coverage = _coverage(entries)
        for k, v in entries:
            for p, msg in validate_instance(v, doc, "passive_proc"):
                err(f"PASSIVE_PROC/{k}", p, msg)
        for p, msg in validate_instance(B.PASSIVE_PROC, doc, "passive_proc_table"):
            err("<container:PASSIVE_PROC>", p, msg)
        return len(entries), errors, warnings, coverage, extra

    raise ValueError(f"未知域 {domain!r}")


# ------------------------------------------------------------------------- public
def validate_all(domain=None, strict_unknown=False):
    """校验数据域。返回 {'ok', 'exit_code', 'engine', 'domains', 'totals'}"""
    docs = {
        "skill.schema.json": load_schema("skill.schema.json"),
        "monster.schema.json": load_schema("monster.schema.json"),
        "affix.schema.json": load_schema("affix.schema.json"),
        "item.schema.json": load_schema("item.schema.json"),
        "effect_rules.schema.json": load_schema("effect_rules.schema.json"),
        "passive_proc.schema.json": load_schema("passive_proc.schema.json"),
    }
    domains = [domain] if domain else list(ALL_DOMAINS)
    result = {"engine": "jsonschema" if HAS_JSONSCHEMA else "minimal",
              "schema_dir": SCHEMA_DIR, "domains": {}, "totals": {}}
    try:
        M = _import_data()
    except Exception as exc:  # pragma: no cover - 数据模块 import 失败要显式报
        result["ok"] = False
        result["exit_code"] = 1
        result["import_error"] = f"{type(exc).__name__}: {exc}"
        result["totals"] = {"entries": 0, "errors": 1, "warnings": 0}
        return result

    tot_e = tot_w = tot_n = 0
    for d in domains:
        n, errors, warnings, coverage, extra = _run_domain(d, docs, M, strict_unknown)
        result["domains"][d] = {"entries": n, "errors": errors, "warnings": warnings,
                                "field_coverage": coverage, "extra": extra}
        tot_e += len(errors)
        tot_w += len(warnings)
        tot_n += n
    result["totals"] = {"entries": tot_n, "errors": tot_e, "warnings": tot_w}
    result["ok"] = tot_e == 0
    result["exit_code"] = 0 if tot_e == 0 else 1
    result["res_unknown_fields"] = _res_unknown(docs, M)
    return result


def _res_unknown(docs, M):
    """schema 未声明字段的全局盘点（报告用）。"""
    out = {}
    groups = {
        "skills": (docs["skill.schema.json"], "skill", _iter_skills(M)),
        "items": (docs["item.schema.json"], "item", M["game.data.items"].ITEMS.items()),
        "affixes": (docs["affix.schema.json"], "affix", M["game.data.affixes"].AFFIXES.items()),
        "monster_skills": (docs["monster.schema.json"], "monster_skill",
                           M["game.data.monsters"].MONSTER_SKILLS.items()),
    }
    for name, (doc, def_name, entries) in groups.items():
        props = doc["$defs"][def_name]["properties"]
        out[name] = _unknown_fields(list(entries), props)
    return out


# ---------------------------------------------------------------------------- cli
def _fmt(res, quiet=False):
    lines = []
    lines.append(f"引擎: {res['engine']}  |  schema 目录: {res['schema_dir']}")
    if "import_error" in res:
        lines.append(f"!! 数据模块导入失败: {res['import_error']}")
        return "\n".join(lines)
    lines.append("")
    lines.append(f"{'域':<14}{'条目':>7}{'违规':>7}{'提醒':>7}")
    for d, info in res["domains"].items():
        lines.append(f"{d:<14}{info['entries']:>7}{len(info['errors']):>7}{len(info['warnings']):>7}")
    t = res["totals"]
    lines.append(f"{'合计':<14}{t['entries']:>7}{t['errors']:>7}{t['warnings']:>7}")
    if quiet:
        return "\n".join(lines)
    for d, info in res["domains"].items():
        if info["errors"]:
            lines.append("")
            lines.append(f"===== 违规明细 [{d}] ({len(info['errors'])}) =====")
            for e in info["errors"][:200]:
                lines.append(f"  - {e['entry']} :: {e['field']} :: {e['problem']}")
            if len(info["errors"]) > 200:
                lines.append(f"  ... 其余 {len(info['errors']) - 200} 条略（见 --json）")
    for d, info in res["domains"].items():
        if info["warnings"]:
            lines.append("")
            lines.append(f"===== 提醒 [{d}] ({len(info['warnings'])}) =====")
            for w in info["warnings"][:80]:
                lines.append(f"  ~ {w['entry']} :: {w['field']} :: {w['problem']}")
            if len(info["warnings"]) > 80:
                lines.append(f"  ... 其余 {len(info['warnings']) - 80} 条略（见 --json）")
    lines.append("")
    lines.append(f"结论: {'全绿 ✅' if res['ok'] else '发现违规 ❌'} (exit {res['exit_code']})")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="dragonfall 数据域 schema 校验器")
    ap.add_argument("--domain", choices=list(ALL_DOMAINS), default=None)
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--quiet", action="store_true", help="只打印汇总")
    ap.add_argument("--strict-unknown", action="store_true", help="未声明字段也算违规")
    args = ap.parse_args(argv)
    res = validate_all(domain=args.domain, strict_unknown=args.strict_unknown)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2, default=str))
    else:
        print(_fmt(res, quiet=args.quiet))
    return res["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
