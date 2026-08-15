# -*- coding: utf-8 -*-

from pypinyin import lazy_pinyin

from ..data import _INDEXES


"""奥兰迪亚·余烬纪年数据层 - index.py"""
def pinyin_id(name: str) -> str:
    """中文名 → 拼音 id：狼皮 → lang_pi；保留字母/数字"""
    parts = []
    for ch in name:
        if '\u4e00' <= ch <= '\u9fff':
            parts.append(lazy_pinyin(ch)[0])
        elif ch.isalnum() or ch == '_':
            parts.append(ch.lower())
    return "_".join(parts)

def build_index(table_name: str, table: dict, prefix: str = "", name_field: str = None):
    """从表构建 名字↔id 双向索引。

    table: 内容表（key 即显示名，或 value[name_field] 为显示名）
    prefix: id 前缀（如 mat_ / sk_ / rec_），无则直接用 pinyin_id
    name_field: 若 value 是 dict 且含该字段，用 value[name_field] 做显示名；
                否则 key 本身即显示名。

    v48：若 key 已是 ID（不含中文）→ 直接用 key 作为 id，不再从名字重新生成
    （旧版会把 i_treatment_potion 这类 ID key 再转一次，产生 it_i___t... 畸形 ID）
    """
    n2i, i2n = {}, {}
    for k, v in table.items():
        if name_field and isinstance(v, dict) and v.get(name_field):
            nm = v[name_field]
        else:
            nm = k
        if not any('\u4e00' <= ch <= '\u9fff' for ch in str(k)):
            eid = k  # v48：key 已是 ID，直接采用
        else:
            eid = f"{prefix}{pinyin_id(nm)}" if prefix else pinyin_id(nm)
        # 冲突时 id 保持稳定：若已存在同名 id，追加后缀
        if eid in i2n and i2n[eid] != nm:
            eid = f"{eid}_{len(i2n) + 1}"
        n2i[nm] = eid
        i2n[eid] = nm
    _INDEXES[table_name] = {"name_to_id": n2i, "id_to_name": i2n}

def resolve(table_name: str, name_or_id: str):
    """统一解析：输入名字或 id，都返回 id(找不到原样返回)"""
    idx = _INDEXES.get(table_name, {}).get("name_to_id", {})
    return idx.get(name_or_id, name_or_id)

def display(table_name: str, entity_id: str):
    """id → 显示名(找不到原样返回)"""
    idx = _INDEXES.get(table_name, {}).get("id_to_name", {})
    return idx.get(entity_id, entity_id)

