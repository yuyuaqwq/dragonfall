#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""奥兰迪亚 · 配置编辑器 — 数据读写层（MVP：技能域）

读
--
用 `ast` 解析 `game/data/skills.py` 里的 PLAYER_SKILLS / BRANCH_SKILLS / TUTOR_SKILLS
字面量。**绝不 import game 包**（避开循环导入、引擎副作用与并行重构期的不确定性）。

写（MVP 策略：JSON 工作副本）
------------------------------
改动写入 `editor/.workdir/skills.json`，**绝不触碰 game/data/skills.py**。
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
SKILLS_PY = os.path.join(ROOT, "game", "data", "skills.py")
CLASSES_PY = os.path.join(ROOT, "game", "data", "classes.py")
SCHEMA_DIR = os.path.join(ROOT, "schema")
SKILL_SCHEMA_JSON = os.path.join(SCHEMA_DIR, "skill.schema.json")
VALIDATE_PY = os.path.join(SCHEMA_DIR, "validate.py")

WORKDIR = os.path.join(EDITOR_DIR, ".workdir")
COPY_PATH = os.path.join(WORKDIR, "skills.json")

# 可编辑的表（顺序即 UI 分组顺序）
TABLES = ("PLAYER_SKILLS", "BRANCH_SKILLS", "TUTOR_SKILLS")
# key 组件分隔符（URL 非保留字符，中文由浏览器 percent-encode，服务端 unquote）
SEP = "~"

WRITE_MODE = "json_copy"
WRITE_NOTE = ("当前为「JSON 工作副本」写入模式：改动只落到 editor/.workdir/skills.json，"
              "不改动 game/data/skills.py。直接回写源码（保留注释/排版）需下一步讨论后实施。")


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


def load_skill_schema() -> dict:
    with open(SKILL_SCHEMA_JSON, "r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_skill(obj) -> dict:
    """返回 {'ok': bool, 'errors': [{'path':..,'message':..}, ...], 'engine': str}"""
    try:
        v = _load_validator()
    except Exception as exc:                                  # pragma: no cover
        return {"ok": False, "engine": "unavailable",
                "errors": [{"path": "$", "message": f"校验器不可用: {exc}"}]}
    doc = load_skill_schema()
    errors = v.validate_instance(obj, doc, "skill")
    return {"ok": not errors, "engine": "jsonschema" if v.HAS_JSONSCHEMA else "minimal",
            "errors": [{"path": p, "message": m} for p, m in errors]}


# ---------------------------------------------------------------------------- read
def parse_source_tables(path: str = SKILLS_PY) -> dict:
    """ast 抽 PLAYER_SKILLS / BRANCH_SKILLS / TUTOR_SKILLS 的字面量（只读源码，不 import）。"""
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    tree = ast.parse(src, filename=path)
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if isinstance(tgt, ast.Name) and tgt.id in TABLES:
                out[tgt.id] = ast.literal_eval(node.value)
    missing = [t for t in TABLES if t not in out]
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


def workcopy_exists() -> bool:
    return os.path.isfile(COPY_PATH)


def source_info() -> dict:
    return {"source": "workcopy" if workcopy_exists() else "python_source",
            "write_mode": WRITE_MODE,
            "note": WRITE_NOTE,
            "copy_path": os.path.relpath(COPY_PATH, ROOT).replace("\\", "/"),
            "source_path": os.path.relpath(SKILLS_PY, ROOT).replace("\\", "/"),
            "validator": validator_engine()}


def current_tables() -> dict:
    """工作副本存在 → 读副本；否则读 py 源码字面量。"""
    if workcopy_exists():
        with open(COPY_PATH, "r", encoding="utf-8") as fh:
            return _norm_keys(json.load(fh))
    return parse_source_tables()


# --------------------------------------------------------------------------- write
def write_copy(tables: dict) -> str:
    os.makedirs(WORKDIR, exist_ok=True)
    tmp = COPY_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(tables, fh, ensure_ascii=False, indent=2, sort_keys=False)
        fh.write("\n")
    os.replace(tmp, COPY_PATH)
    return COPY_PATH


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


def iter_entries(tables: dict):
    """展平成条目元信息列表（按表/职业/分支顺序）。"""
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


def _entry(table, cls_id, cls_name, sk_id, sk, group, branch_lv):
    if table == "BRANCH_SKILLS":
        key = make_key([table, cls_id, branch_lv, group, sk_id])
    else:
        key = make_key([table, cls_id, sk_id])
    return {"key": key, "table": table, "cls_id": cls_id, "cls_name": cls_name,
            "sk_id": sk_id, "group": group, "branch_lv": branch_lv,
            "name": sk.get("name", ""), "kind": sk.get("kind", ""), "lv": sk.get("lv")}


_SECTION_LABEL = {
    "PLAYER_SKILLS": "基础技能",
    "BRANCH_SKILLS": "分支技能",
    "TUTOR_SKILLS": "导师秘传",
}


def list_payload() -> dict:
    """GET /api/domain/skills 的响应体：按 表/职业/分支 分组。"""
    tables = current_tables()
    info = source_info()
    entries = iter_entries(tables)
    buckets = {}
    order = []
    for e in entries:
        gid = "|".join([e["table"], e["cls_id"], str(e["group"] or "")])
        if gid not in buckets:
            if e["table"] == "BRANCH_SKILLS":
                label = f"{e['cls_name']} · {_SECTION_LABEL[e['table']]}（{e['group']}）"
            elif e["table"] == "TUTOR_SKILLS":
                label = f"{e['cls_name']} · {_SECTION_LABEL[e['table']]}"
            else:
                label = f"{e['cls_name']} · {_SECTION_LABEL[e['table']]}"
            buckets[gid] = {"id": gid, "label": label, "table": e["table"],
                            "cls_id": e["cls_id"], "cls_name": e["cls_name"],
                            "section": e["table"], "entries": []}
            order.append(gid)
        buckets[gid]["entries"].append(
            {k: e[k] for k in ("key", "sk_id", "name", "kind", "lv", "group", "branch_lv")})
    return {"domain": "skills", "total": len(entries),
            "groups": [buckets[g] for g in order], **info}


def get_skill(key: str):
    """返回 (entry_meta, data_dict)；不存在 → (None, None)。"""
    tables = current_tables()
    data = _resolve(tables, key)
    meta = None
    for e in iter_entries(tables):
        if e["key"] == key:
            meta = e
            break
    return meta, data


def _walk_parent(tables: dict, key: str, create=False):
    """返回 (parent_container, leaf_id)，parent 是能直接赋值 leaf_id 的 dict。"""
    parts = split_key(key)
    table = parts[0]
    if table not in TABLES:
        raise KeyError(f"未知表 {table!r}")
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


def _resolve(tables: dict, key: str):
    try:
        parent, leaf = _walk_parent(tables, key)
    except KeyError:
        return None
    return parent.get(leaf)


def set_skill(key: str, data: dict) -> dict:
    """把 data 写入工作副本（不存在则从源码种子创建）。返回 {key, created, copy_path}。"""
    tables = current_tables()
    parent, leaf = _walk_parent(tables, key, create=True)
    created = leaf not in parent
    parent[leaf] = copy.deepcopy(data)
    write_copy(tables)
    return {"key": key, "created": created, "copy_path": COPY_PATH}


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


# ------------------------------------------------------------------------- selftest
def _selftest():                                                     # pragma: no cover
    tables = parse_source_tables()
    entries = iter_entries(tables)
    print(f"[selftest] 解析到 {len(entries)} 条技能；校验器引擎 = {validator_engine()}")
    bad = 0
    for e in entries:
        _m, d = get_skill(e["key"])
        res = validate_skill(d)
        if not res["ok"]:
            bad += 1
            print("  !! 现网技能未过 schema:", e["key"], res["errors"][:2])
    print(f"[selftest] 现网技能 schema 违规 {bad} 条（应为 0）")
    return 0 if bad == 0 else 1


if __name__ == "__main__":                                           # pragma: no cover
    raise SystemExit(_selftest())
