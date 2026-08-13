# -*- coding: utf-8 -*-
import json
from .connection import _connect, _lock
from .. import content as C

"""《剑与魔法》存储层 - inventory"""
def _key_to_id(item_key, item_data=None):
    """v46：把「名字型」物品 key 转成稳定 ID（存档只存 ID）。


    规则：
      - 已有前缀 id（eq_/petegg_/mountrein_/rune_/it_/mat_英文/...）原样返回
      - mat_中文名 → mat_拼音；rec_中文名 → rec_拼音；fish_中文名 → fish_拼音
      - 纯中文名（装备/材料/消耗品/图纸）→ 查索引转 ID
    """
    if not item_key:
        return item_key
    # 已是纯 ID（含英文前缀）：mat_lang_pi / eq_xxx / i_treatment_potion 等
    if item_key.startswith(("eq_", "petegg_", "mountrein_", "rune_", "i_", "npc_", "m_")):
        return item_key
    # mat_ / rec_ / fish_ 前缀：后面已是英文拼音（无中文）→ 原样返回
    for pfx in ("mat_", "rec_", "fish_"):
        if item_key.startswith(pfx):
            rest = item_key[len(pfx):]
            if not any("\u4e00" <= ch <= "\u9fff" for ch in rest):
                return item_key
    # mat_ / rec_ / fish_ 前缀 + 中文 → 拼音 id
    for pfx, tbl in (("mat_", "materials"), ("rec_", "recipes"), ("fish_", "fish")):
        if item_key.startswith(pfx):
            cn = item_key[len(pfx):]
            rid = C.resolve(tbl, cn)
            if rid != cn:
                return f"{pfx}{rid}" if not rid.startswith(pfx) else rid
            return f"{pfx}{C.pinyin_id(cn)}"
    # 纯中文名 → 查索引（材料/配方/物品/鱼）
    for tbl in ("materials", "recipes", "items", "fish"):
        rid = C.resolve(tbl, item_key)
        if rid != item_key:
            return rid
    # 兜底：装备/图纸等直接给名字当 key 的，保持原样（外部 data 里有 name）
    return item_key

def add_item(group_id, qq_id, item_key, item_data: dict, count=1):
    """item_key: 唯一键(装备用 uuid 或 材料/消耗品用 id)；v46 自动转 ID 存储"""
    item_key = _key_to_id(item_key, item_data)
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT count FROM inventory WHERE qq_id=? AND item_key=?",
                (qq_id, item_key),
            ).fetchone()
            if row and item_data.get("stackable", True):
                conn.execute(
                    "UPDATE inventory SET count=count+? WHERE qq_id=? AND item_key=?",
                    (count, qq_id, item_key),
                )
            elif row:
                # v110 审计修复：同 key 已存在且不可堆叠（如重复 uuid 场景）——
                # 原裸 INSERT 撞主键抛 sqlite3.IntegrityError，公共函数应设防，退化累加
                conn.execute(
                    "UPDATE inventory SET count=count+? WHERE qq_id=? AND item_key=?",
                    (count, qq_id, item_key),
                )
            else:
                conn.execute(
                    "INSERT INTO inventory (qq_id, item_key, item_data, count) VALUES (?,?,?,?)",
                    (qq_id, item_key, json.dumps(item_data, ensure_ascii=False), count),
                )
            conn.commit()
        finally:
            conn.close()

def get_inventory(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT item_key, item_data, count FROM inventory WHERE qq_id=? ORDER BY rowid",
                (qq_id,),
            ).fetchall()
            out = []
            for r in rows:
                d = json.loads(r["item_data"])
                # v46：补显示名（旧档 name 可能缺失，用 id 反查或 key）
                # v104R3 M11 P2-9：兜底不再只认 mat_ 前缀——i_stone_upgrade 等非 mat_ 材料
                # 缺 name 时此前直接显示英文 key（黑名单 i_stone 泄漏）；按 materials→items 顺序
                # 反查，查不到才退回 key（display 未命中时原样返回）
                if not d.get("name"):
                    d["name"] = C.display("materials", r["item_key"])
                    if d["name"] == r["item_key"]:
                        d["name"] = C.display("items", r["item_key"])
                out.append({"key": r["item_key"], "data": d, "count": r["count"]})
            return out
        finally:
            conn.close()

def count_item(group_id, qq_id, name):
    """按物品名称/ID 统计背包中数量(材料类，key 为 mat_名称)"""
    kid = _key_to_id(name)
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT item_key, item_data, count FROM inventory WHERE qq_id=?",
                (qq_id,),
            ).fetchall()
            total = 0
            for r in rows:
                d = json.loads(r["item_data"])
                if d.get("name") == name or r["item_key"] == kid:
                    total += r["count"]
            return total
        finally:
            conn.close()

def remove_item(group_id, qq_id, item_key, count=1):
    item_key = _key_to_id(item_key)
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT count FROM inventory WHERE qq_id=? AND item_key=?",
                (qq_id, item_key),
            ).fetchone()
            if not row:
                return False
            if row["count"] <= count:
                conn.execute(
                    "DELETE FROM inventory WHERE qq_id=? AND item_key=?",
                    (qq_id, item_key),
                )
            else:
                conn.execute(
                    "UPDATE inventory SET count=count-? WHERE qq_id=? AND item_key=?",
                    (count, qq_id, item_key),
                )
            conn.commit()
            return True
        finally:
            conn.close()


