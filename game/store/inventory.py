# -*- coding: utf-8 -*-
import json
from .connection import _connect, _lock, atomic
from .. import content as C

"""奥兰迪亚·余烬纪年存储层 - inventory"""

# v126.2 个体属性 tags 上限：单物品最多保留 500 条个体标记（防 item_data 膨胀），
# 超出丢最旧（FIFO 语义：先钓的先卖，但囤积量级下截断最旧影响可忽略）
FISH_TAGS_MAX = 500


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

def add_item(group_id, qq_id, item_key, item_data: dict, count=1, tag: dict | None = None):
    """item_key: 唯一键(装备用 uuid 或 材料/消耗品用 id)；v46 自动转 ID 存储

    v126.2 tag：个体属性标记（鱼获重量/大小）——堆叠物品每件一个 tag 存 item_data["tags"]，
    与 count 同生共死（remove/sell 按 FIFO 截断），count 恒 >= len(tags)。
    """
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0 or count > 9999999:
        # F1 P1-3：数量非法（<=0 / 超大）直接拒绝，防负资产/内存膨胀
        return False
    item_key = _key_to_id(item_key, item_data)
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT count, item_data FROM inventory WHERE qq_id=? AND item_key=?",
                (qq_id, item_key),
            ).fetchone()
            if row and item_data.get("stackable", True):
                if tag:
                    # 堆叠 + 个体标记：读旧 data，append tag（上限 500 条，超出丢最旧）
                    _d = json.loads(row["item_data"])
                    _tags = _d.get("tags", []) or []
                    _tags.append(tag)
                    if len(_tags) > FISH_TAGS_MAX:
                        _tags = _tags[-FISH_TAGS_MAX:]
                    _d["tags"] = _tags
                    conn.execute(
                        "UPDATE inventory SET count=count+?, item_data=? WHERE qq_id=? AND item_key=?",
                        (count, json.dumps(_d, ensure_ascii=False), qq_id, item_key),
                    )
                else:
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
                if tag:
                    item_data = dict(item_data)
                    item_data["tags"] = [tag]
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
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0 or count > 9999999:
        # F1 P1-3：非法数量直接拒绝（<=0 会误删整堆或增库存；超大 count 有溢出/DoS 面）
        return False
    item_key = _key_to_id(item_key)
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT count, item_data FROM inventory WHERE qq_id=? AND item_key=?",
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
                # v126.2 同步截断 tags（FIFO：先扣的先删个体标记，保持 count >= len(tags)）
                _d = json.loads(row["item_data"])
                if _d.get("tags"):
                    _d["tags"] = _d["tags"][count:]
                    conn.execute(
                        "UPDATE inventory SET count=count-?, item_data=? WHERE qq_id=? AND item_key=?",
                        (count, json.dumps(_d, ensure_ascii=False), qq_id, item_key),
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


def update_item_data(group_id, qq_id, item_key, new_data: dict):
    """F1 P0-1：单条原子 UPDATE 覆盖某格 item_data（强化/附魔写回装备用）。

    比 remove_item+add_item 两步非原子替换更安全（后者中途崩会丢格/建重复格），
    且保留原格 count 与 rowid。装备所在格 key 为 uuid（get_inventory 原样返回），
    此处经 _key_to_id 归一化后仍命中同一格——key 语义与 remove/add 一致。
    命中返回 True，否则 False（该格不存在，不做写入）。
    """
    item_key = _key_to_id(item_key, new_data)
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute(
                "UPDATE inventory SET item_data=? WHERE qq_id=? AND item_key=?",
                (json.dumps(new_data, ensure_ascii=False), qq_id, item_key),
            )
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


def sell_item_atomic(group_id, qq_id, item_key, count, gold_gain):
    """F1 P0-2：原子出售单件（单事务：校验货存→加金币→扣包），替代 _sell_one 的两步独立 commit。

    返回 True 表示扣款发货成功；False 表示该格不存在/不足（命令层已有 rate/价格校验，
    此处仅防护并发 sold-out 造成的重复加钱）。item_key 由命令层按 get_inventory 语义给出。
    """
    item_key = _key_to_id(item_key)
    with atomic() as conn:
        row = conn.execute(
            "SELECT count, item_data FROM inventory WHERE qq_id=? AND item_key=?",
            (qq_id, item_key),
        ).fetchone()
        if not row:
            return False
        if row["count"] <= count:
            conn.execute("DELETE FROM inventory WHERE qq_id=? AND item_key=?", (qq_id, item_key))
        else:
            # v126.2 同步截断 tags（FIFO：先卖的先删个体标记）
            _d = json.loads(row["item_data"])
            if _d.get("tags"):
                _d["tags"] = _d["tags"][count:]
                conn.execute(
                    "UPDATE inventory SET count=count-?, item_data=? WHERE qq_id=? AND item_key=?",
                    (count, json.dumps(_d, ensure_ascii=False), qq_id, item_key),
                )
            else:
                conn.execute("UPDATE inventory SET count=count-? WHERE qq_id=? AND item_key=?",
                             (count, qq_id, item_key))
        conn.execute("UPDATE players SET gold=gold+? WHERE qq_id=?", (gold_gain, qq_id))
    return True


