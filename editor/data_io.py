#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""奥兰迪亚 · 配置编辑器 — 数据读写层（多域：skills / affixes）

域模型（怎么加一个新域见 editor/README.md「新增一个域」）
----------------------------------------------------------
`DOMAIN_DEFS` 一张表描述每个域：schema 文件 / 主 def / py 源文件 / 顶层表名 / 工作副本名
/ 列表分组策略。读写/校验/列表全部由域定义驱动 —— 加域 = 往表里加一条，不改函数。

读
--
用 `ast` 解析 `game/data/*.py` 里的顶层表字面量。**绝不 import game 包**（避开循环导入、
引擎装配副作用与并行重构期的不确定性）。

写（策略：JSON 工作副本）
--------------------------
改动写入 `editor/.workdir/<域>.json`，**绝不触碰 game/data/*.py**。
理由：整表回写 py 源码会丢注释与手工排版（skills.py 里有大量 `# v162:` 这类注释），
定点 AST 回写留到与主工程讨论后（见 EDITOR_SPEC.md「回写 py 源码是最大风险点」）。

校验
----
复用 `schema/validate.py` 的 `validate_instance`（有 jsonschema 时用它；没有则内置最小校验器，
两条路径判定一致 —— tests/test_schema_validate.py 已锁死）。编辑器自身不引入任何第三方依赖。
"""
from __future__ import annotations

import ast
import copy
import importlib.util
import json
import os

# --------------------------------------------------------------------------- paths
EDITOR_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(EDITOR_DIR)                       # dragonfall/
SCHEMA_DIR = os.path.join(ROOT, "schema")
VALIDATE_PY = os.path.join(SCHEMA_DIR, "validate.py")
WORKDIR = os.path.join(EDITOR_DIR, ".workdir")

# 域定义（顺序 = UI 顺序）。加新域：这里加一条 + README 写步骤。
DOMAIN_DEFS = {
    "skills": {
        "label": "技能（skills.py）",
        "schema": "skill.schema.json",
        "primary": "skill",
        "source": "game/data/skills.py",
        "tables": ("PLAYER_SKILLS", "BRANCH_SKILLS", "TUTOR_SKILLS"),
        "copy": "skills.json",
        "flat": False,          # 三层嵌套表（表→职业→分支→技能）
        "group": "class",       # 列表分组：按 表/职业/分支
    },
    "affixes": {
        "label": "词条（affixes.py）",
        "schema": "affix.schema.json",
        "primary": "affix",
        "source": "game/data/affixes.py",
        "tables": ("AFFIXES",),
        "copy": "affixes.json",
        "flat": True,           # 扁平表（id → 条目）
        "group": "kind",        # 列表分组：按 kind（attack 武器 / defense 防具）
    },
}
DOMAINS = tuple(DOMAIN_DEFS)                             # UI 顺序

# key 组件分隔符（URL 非保留字符，中文由浏览器 percent-encode，服务端 unquote）
SEP = "~"

# 兼容别名（旧代码/自检脚本按技能域语义引用）
TABLES = DOMAIN_DEFS["skills"]["tables"]
COPY_PATH = os.path.join(WORKDIR, DOMAIN_DEFS["skills"]["copy"])
CLASSES_PY = os.path.join(ROOT, "game", "data", "classes.py")

WRITE_MODE = "json_copy"
WRITE_NOTE = ("当前为「JSON 工作副本」写入模式：改动只落到 editor/.workdir/<域>.json，"
              "不改动 game/data/*.py。直接回写源码（保留注释/排版）需下一步讨论后实施。")

AFFIX_KIND_CN = {"attack": "武器", "defense": "防具"}


def domain_def(domain: str) -> dict:
    d = DOMAIN_DEFS.get(domain)
    if d is None:
        raise KeyError(f"未知域 {domain!r}（可用：{', '.join(DOMAINS)}）")
    return d


def _copy_path(domain: str) -> str:
    return os.path.join(WORKDIR, domain_def(domain)["copy"])


def _source_path(domain: str) -> str:
    return os.path.join(ROOT, domain_def(domain)["source"])


# ------------------------------------------------------------------------ validate
_validator = None


def _load_validator():
    """按文件路径加载 schema/validate.py，避免污染 sys.path / import 到 game 包。"""
    global _validator
    if _validator is None:
        spec = importlib.util.spec_from_file_location("df_schema_validate", VALIDATE_PY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _validator = mod
    return _validator


def validator_engine() -> str:
    try:
        return "jsonschema" if _load_validator().HAS_JSONSCHEMA else "minimal"
    except Exception:
        return "unavailable"


def load_schema(domain: str = "skills") -> dict:
    with open(os.path.join(SCHEMA_DIR, domain_def(domain)["schema"]), "r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_entry(domain: str, obj) -> dict:
    """返回 {'ok': bool, 'errors': [{'path':..,'message':..}, ...], 'engine': str}"""
    try:
        v = _load_validator()
    except Exception as exc:                                  # pragma: no cover
        return {"ok": False, "engine": "unavailable",
                "errors": [{"path": "$", "message": f"校验器不可用: {exc}"}]}
    doc = load_schema(domain)
    errors = v.validate_instance(obj, doc, domain_def(domain)["primary"])
    return {"ok": not errors, "engine": "jsonschema" if v.HAS_JSONSCHEMA else "minimal",
            "errors": [{"path": p, "message": m} for p, m in errors]}


# ---------------------------------------------------------------------------- read
def parse_source_tables(path: str = None, tables=None, domain: str = "skills") -> dict:
    """ast 抽顶层表字面量（只读源码，不 import）。默认技能域（向后兼容）。"""
    if path is None:
        path = _source_path(domain)
    if tables is None:
        tables = domain_def(domain)["tables"]
    tables = tuple(tables)
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    tree = ast.parse(src, filename=path)
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if isinstance(tgt, ast.Name) and tgt.id in tables:
                out[tgt.id] = ast.literal_eval(node.value)
    missing = [t for t in tables if t not in out]
    if missing:
        raise ValueError(f"{path}: 未找到顶层赋值 {missing}")
    return _norm_keys(out)


def _norm_keys(obj):
    """递归把 dict 的键统一成 str（JSON 无 int 键；BRANCH_SKILLS 的 branches 用 int lv 作键）。"""
    if isinstance(obj, dict):
        return {str(k): _norm_keys(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_norm_keys(v) for v in obj]
    return obj


def workcopy_exists(domain: str = "skills") -> bool:
    return os.path.isfile(_copy_path(domain))


def source_info(domain: str = "skills") -> dict:
    cp = _copy_path(domain)
    return {"domain": domain,
            "source": "workcopy" if workcopy_exists(domain) else "python_source",
            "write_mode": WRITE_MODE,
            "note": WRITE_NOTE,
            "copy_path": os.path.relpath(cp, ROOT).replace("\\", "/"),
            "source_path": os.path.relpath(_source_path(domain), ROOT).replace("\\", "/"),
            "validator": validator_engine()}


def current_tables(domain: str = "skills") -> dict:
    """工作副本存在 → 读副本；否则读 py 源码字面量。"""
    if workcopy_exists(domain):
        with open(_copy_path(domain), "r", encoding="utf-8") as fh:
            return _norm_keys(json.load(fh))
    return parse_source_tables(domain=domain)


# --------------------------------------------------------------------------- write
def write_copy(tables: dict, domain: str = "skills") -> str:
    cp = _copy_path(domain)
    os.makedirs(WORKDIR, exist_ok=True)
    tmp = cp + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(tables, fh, ensure_ascii=False, indent=2, sort_keys=False)
        fh.write("\n")
    os.replace(tmp, cp)
    return cp


# ------------------------------------------------------------------------ key path
def make_key(parts) -> str:
    for p in parts:
        if SEP in str(p):
            raise ValueError(f"key 组件不能含 {SEP!r}: {p!r}")
    return SEP.join(str(p) for p in parts)


def split_key(key: str):
    return key.split(SEP)


def _cls_name(cd: dict) -> str:
    return str(cd.get("name") or "")


def load_class_names() -> dict:
    """只读 ast 抽 game/data/classes.py 的 CLASSES 名字（不 import game）。失败则空表。"""
    try:
        with open(CLASSES_PY, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=CLASSES_PY)
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == "CLASSES":
                        d = ast.literal_eval(node.value)
                        return {k: str(v.get("name") or "") for k, v in d.items()}
    except Exception:
        pass
    return {}


_SECTION_LABEL = {
    "PLAYER_SKILLS": "基础技能",
    "BRANCH_SKILLS": "分支技能",
    "TUTOR_SKILLS": "导师秘传",
    "AFFIXES": "词条",
}


def iter_entries(tables: dict, domain: str = "skills"):
    """展平成条目元信息列表。域定义驱动：flat 域 → 单层；其余 → 三层（技能专用形状）。"""
    if domain_def(domain)["flat"]:
        return _iter_flat(tables, domain)
    return _iter_skills(tables)


def _iter_skills(tables: dict):
    class_names = load_class_names()
    out = []

    def cname(cls_id, cd):
        return _cls_name(cd) or class_names.get(cls_id, "") or cls_id

    for cls_id, cd in (tables.get("PLAYER_SKILLS") or {}).items():
        for sk_id, sk in (cd.get("skills") or {}).items():
            out.append(_entry("PLAYER_SKILLS", cls_id, cname(cls_id, cd), sk_id, sk, None, None))
    for cls_id, cd in (tables.get("BRANCH_SKILLS") or {}).items():
        for lv, branches in (cd.get("branches") or {}).items():
            for bname, skills in (branches or {}).items():
                for sk_id, sk in (skills or {}).items():
                    out.append(_entry("BRANCH_SKILLS", cls_id, cname(cls_id, cd), sk_id, sk, bname, lv))
    for cls_id, skills in (tables.get("TUTOR_SKILLS") or {}).items():
        for sk_id, sk in (skills or {}).items():
            out.append(_entry("TUTOR_SKILLS", cls_id, cname(cls_id, skills), sk_id, sk, None, None))
    return out


def _iter_flat(tables: dict, domain: str):
    table = domain_def(domain)["tables"][0]
    out = []
    for eid, data in (tables.get(table) or {}).items():
        if not isinstance(data, dict):
            continue
        e = _entry(table, None, None, eid, data, data.get("kind"), None)
        e["group"] = data.get("kind")
        e["trigger"] = data.get("trigger")
        out.append(e)
    return out


def _entry(table, cls_id, cls_name, eid, data, group, branch_lv):
    if table == "BRANCH_SKILLS":
        key = make_key([table, cls_id, branch_lv, group, eid])
    elif cls_id is None:
        key = make_key([table, eid])                      # 扁平域：表~id
    else:
        key = make_key([table, cls_id, eid])
    e = {"key": key, "id": eid, "table": table, "cls_id": cls_id, "cls_name": cls_name,
         "group": group, "branch_lv": branch_lv,
         "name": data.get("name", ""), "kind": data.get("kind", ""), "lv": data.get("lv")}
    if table in ("PLAYER_SKILLS", "BRANCH_SKILLS", "TUTOR_SKILLS"):
        e["sk_id"] = eid                                    # 兼容旧前端字段名
    return e


def list_payload(domain: str = "skills") -> dict:
    """GET /api/domain/<domain> 的响应体：分组 + 元信息。"""
    dd = domain_def(domain)
    tables = current_tables(domain)
    info = source_info(domain)
    entries = iter_entries(tables, domain)
    buckets, order = {}, []
    for e in entries:
        gid, label = _group_of(e, domain)
        if gid not in buckets:
            buckets[gid] = {"id": gid, "label": label, "table": e["table"],
                            "cls_id": e["cls_id"], "cls_name": e["cls_name"],
                            "section": e["table"], "entries": []}
            order.append(gid)
        item = {k: e.get(k) for k in ("key", "id", "sk_id", "name", "kind", "lv",
                                      "group", "branch_lv", "trigger")}
        buckets[gid]["entries"].append(item)
    return {"domain": domain, "primary": dd["primary"], "label": dd["label"],
            "flat": dd["flat"], "total": len(entries),
            "groups": [buckets[g] for g in order], **info}


def _group_of(e: dict, domain: str):
    """域定义驱动的列表分组 → (gid, 显示 label)。"""
    mode = domain_def(domain)["group"]
    if mode == "kind":
        k = str(e.get("group") or e.get("kind") or "")
        cn = AFFIX_KIND_CN.get(k, k)
        return f"{e['table']}|{k}", f"{_SECTION_LABEL.get(e['table'], e['table'])} · {cn}（{k}）"
    if e["table"] == "BRANCH_SKILLS":
        return ("|".join([e["table"], e["cls_id"], str(e["group"] or "")]),
                f"{e['cls_name']} · {_SECTION_LABEL[e['table']]}（{e['group']}）")
    return ("|".join([e["table"], e["cls_id"], ""]),
            f"{e['cls_name']} · {_SECTION_LABEL.get(e['table'], e['table'])}")


# ------------------------------------------------------------------------ get / set
def get_entry(domain: str, key: str):
    """返回 (entry_meta, data_dict)；不存在 → (None, None)。"""
    tables = current_tables(domain)
    data = _resolve(tables, key, domain)
    meta = None
    for e in iter_entries(tables, domain):
        if e["key"] == key:
            meta = e
            break
    return meta, data


def _walk_parent(tables: dict, key: str, domain: str, create=False):
    """返回 (parent_container, leaf_id)，parent 是能直接赋值 leaf_id 的 dict。"""
    dd = domain_def(domain)
    parts = split_key(key)
    table = parts[0]
    if table not in dd["tables"]:
        raise KeyError(f"未知表 {table!r}（域 {domain} 的可编辑表：{dd['tables']}）")
    if dd["flat"]:
        if len(parts) != 2:
            raise KeyError(f"{table} key 形状应为 表~id: {key!r}")
        _, eid = parts
        root = tables.setdefault(table, {}) if create else tables.get(table, {})
        return root, eid
    if table == "PLAYER_SKILLS":
        if len(parts) != 3:
            raise KeyError(f"PLAYER_SKILLS key 形状应为 表~职业~技能: {key!r}")
        _, cls_id, sk_id = parts
        root = tables.setdefault(table, {}) if create else tables.get(table, {})
        cd = root.setdefault(cls_id, {"name": "", "skills": {}}) if create else (root or {}).get(cls_id, {})
        skills = cd.setdefault("skills", {}) if create else (cd.get("skills") or {})
        return skills, sk_id
    if table == "TUTOR_SKILLS":
        if len(parts) != 3:
            raise KeyError(f"TUTOR_SKILLS key 形状应为 表~职业~技能: {key!r}")
        _, cls_id, sk_id = parts
        root = tables.setdefault(table, {}) if create else tables.get(table, {})
        skills = root.setdefault(cls_id, {}) if create else (root or {}).get(cls_id, {})
        return skills, sk_id
    # BRANCH_SKILLS: 表~职业~lv~分支名~技能
    if len(parts) != 5:
        raise KeyError(f"BRANCH_SKILLS key 形状应为 表~职业~lv~分支~技能: {key!r}")
    _, cls_id, lv, bname, sk_id = parts
    root = tables.setdefault(table, {}) if create else tables.get(table, {})
    cd = root.setdefault(cls_id, {"name": "", "branches": {}}) if create else (root or {}).get(cls_id, {})
    branches = cd.setdefault("branches", {}) if create else (cd.get("branches") or {})
    level = branches.setdefault(lv, {}) if create else (branches.get(lv) or {})
    skills = level.setdefault(bname, {}) if create else (level.get(bname) or {})
    return skills, sk_id


def _resolve(tables: dict, key: str, domain: str = "skills"):
    try:
        parent, leaf = _walk_parent(tables, key, domain)
    except KeyError:
        return None
    return parent.get(leaf)


def set_entry(domain: str, key: str, data: dict) -> dict:
    """把 data 写入工作副本（不存在则从源码种子创建）。返回 {key, created, copy_path}。"""
    tables = current_tables(domain)
    parent, leaf = _walk_parent(tables, key, domain, create=True)
    created = leaf not in parent
    parent[leaf] = copy.deepcopy(data)
    write_copy(tables, domain)
    return {"key": key, "created": created, "copy_path": _copy_path(domain)}


# ---------------------------------------------------------------------------- diff
def diff_values(before, after, path="") -> list:
    """字段级深比较：返回 [{'path','before','after'}, ...]。"""
    out = []
    if isinstance(before, dict) and isinstance(after, dict):
        for k in sorted(set(before) | set(after), key=str):
            sub = f"{path}.{k}" if path else str(k)
            if k not in before:
                out.append({"path": sub, "before": None, "after": after[k]})
            elif k not in after:
                out.append({"path": sub, "before": before[k], "after": None})
            else:
                out += diff_values(before[k], after[k], sub)
    elif isinstance(before, list) and isinstance(after, list):
        if len(before) != len(after):
            out.append({"path": path, "before": before, "after": after})
        else:
            for i, (b, a) in enumerate(zip(before, after)):
                out += diff_values(b, a, f"{path}[{i}]")
    else:
        if before != after:
            out.append({"path": path, "before": before, "after": after})
    return out


# ------------------------------------------------------- 兼容别名（技能域语义）
def load_skill_schema() -> dict:
    return load_schema("skills")


def validate_skill(obj) -> dict:
    return validate_entry("skills", obj)


def get_skill(key: str):
    return get_entry("skills", key)


def set_skill(key: str, data: dict) -> dict:
    return set_entry("skills", key, data)


# ------------------------------------------------------------------------- selftest
def _selftest():                                                     # pragma: no cover
    bad = 0
    for domain in DOMAINS:
        try:
            tables = parse_source_tables(domain=domain)
        except Exception as exc:
            print(f"[selftest] {domain}: 解析失败 {exc}")
            bad += 1
            continue
        entries = iter_entries(tables, domain)
        print(f"[selftest] {domain}: {len(entries)} 条；校验器 = {validator_engine()}")
        for e in entries:
            _m, d = get_entry(domain, e["key"])
            res = validate_entry(domain, d)
            if not res["ok"]:
                bad += 1
                print("  !! 现网条目未过 schema:", domain, e["key"], res["errors"][:2])
    print(f"[selftest] 违规 {bad} 条（应为 0）")
    return 0 if bad == 0 else 1


if __name__ == "__main__":                                           # pragma: no cover
    raise SystemExit(_selftest())
