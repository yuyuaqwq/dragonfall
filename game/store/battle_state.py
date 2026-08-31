# -*- coding: utf-8 -*-
import json
import time
from .connection import _connect, _lock

"""奥兰迪亚·余烬纪年存储层 - battle_state"""
# v104 M02 P2：普通战斗 24h 无活动自动回收（battle_state 永久残留泄漏；PVP 另有 5 分钟超时在 combat.py）
BATTLE_STALE_SEC = 24 * 3600


def _json_ready(obj):
    """v116 兜底：把 state 里可能残留的 Python set（如 phase BOSS 的 _phase_warned）
    递归深转成 list，保证 json.dumps 序列化不再抛 TypeError；其余类型原样返回。"""
    if isinstance(obj, set):
        return [_json_ready(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _json_ready(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_ready(x) for x in obj]
    return obj


def _monster_display_name(state):
    """I0-B8：monster 列展示宿主昵称——多对多阵列优先取 enemies[0]（阵列压缩换位后的实际首单位），
    无 enemies 时回落单怪 enemy 名。"""
    enemies = state.get("enemies")
    if isinstance(enemies, list) and enemies:
        return enemies[0].get("name", "") or ""
    return (state.get("enemy") or {}).get("name", "") or ""


def save_battle(group_id, qq_id, state: dict):
    """保存完整战斗上下文（v9：含 type/round/buffs/enemy 等）


    兼容旧调用：若传入的是裸怪物 dict，自动包装为 v9 状态。
    v94.1：续存时自动继承旧 state 的 stamina_charged 标记（b.to_state() 不含该字段，
    否则战斗内第二击会重复扣体力）。
    """
    if "type" not in state:
        state = {
            # v152 时刻制：round 删除，now = 战斗绝对时刻
            "type": "monster", "now": 0.0,
            "enemy": state, "p_buffs": {}, "e_buffs": {},
            "p_defending": False, "e_defending": False,
        }
    with _lock:
        conn = _connect()
        try:
            old = conn.execute(
                "SELECT state FROM battle_state WHERE qq_id=?", (qq_id,)
            ).fetchone()
            if old and state.get("stamina_charged") is None:
                try:
                    old_state = json.loads(old["state"])
                    if old_state.get("stamina_charged"):
                        state["stamina_charged"] = True
                except (ValueError, TypeError):
                    pass
            conn.execute(
                # I0-B8：monster 列存展示主目标昵称——多对多阵列（state.enemies）压缩换位后首单位
                # 可能非原主目标，故优先取 enemies[0]，单怪回落 enemy 名；旧档遗留敌名仍可显示。
                # A0-A1：写入前经 _json_ready 清洗残留 set（phase BOSS 旧档 _phase_warned），
                # 避免 json.dumps 抛 TypeError 致存档崩溃。
                "INSERT INTO battle_state (qq_id, monster, state, updated_at) VALUES (?,?,?,?) "
                "ON CONFLICT(qq_id) DO UPDATE SET monster=excluded.monster, state=excluded.state, updated_at=excluded.updated_at",
                (qq_id, _monster_display_name(state), json.dumps(_json_ready(state), ensure_ascii=False), int(time.time())),
            )
            conn.commit()
        finally:
            conn.close()

def get_battle(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT monster, state, updated_at FROM battle_state WHERE qq_id=?",
                (qq_id,),
            ).fetchone()
            if not row:
                return None
            # v104 M02 P2：超 24h 无活动的战斗记录回收（普通战斗此前永久保留；
            # 表无 created_at 列，用 updated_at 判定更合理——战斗长时间无操作即视为废弃）
            updated = row["updated_at"] or 0
            if updated and time.time() - updated > BATTLE_STALE_SEC:
                state = json.loads(row["state"])
                # v104 M04 P2：副本战斗行不静默删除——保留行并打 _expired 标记，
                # 由命令层（instance.py _instance_expired_hint）给出"副本已过期"提示后清理；
                # 本函数仍返回 None，战斗路由（_in_battle 等）不会把过期副本当战斗中。
                # 普通战斗维持原行为：直接回收。
                if state.get("type") == "instance":
                    state["_expired"] = True
                    conn.execute(
                        "UPDATE battle_state SET state=? WHERE qq_id=?",
                        (json.dumps(state, ensure_ascii=False), qq_id),
                    )
                    conn.commit()
                    # v141 兜底（P0-3，2026-08-30 审计）：instance 行超 BATTLE_STALE_SEC
                    # 只打 _expired 标记不销毁大陆 → 大陆实例泄漏（内存 + event_state 键）。
                    # 命令层（instance.py）会补 30min 超时销毁；这里做 24h 过期兜底：
                    # state 里带 world_id 且为 inst: 前缀 → 直接销毁大陆实例（幂等）。
                    # 正常 instance 战斗（未过期）不碰；非 inst: 前缀（异常数据）不碰。
                    try:
                        _wid = state.get("world_id") or ""
                        if isinstance(_wid, str) and _wid.startswith("inst:"):
                            from ..core.worlds import destroy_instance_world as _diw
                            _diw(_wid)
                    except Exception:
                        pass
                    return None
                conn.execute("DELETE FROM battle_state WHERE qq_id=?", (qq_id,))
                conn.commit()
                return None
            state = json.loads(row["state"])
            # 兼容 v9 之前的旧数据（state 字段直接是裸怪物 dict）
            if "type" not in state:
                state = {
                    "type": "monster", "now": 0.0,
                    "enemy": state, "p_buffs": {}, "e_buffs": {},
                    "p_defending": False, "e_defending": False,
                }
            return {"state": state, "monster": state.get("enemy", {}), "name": row["monster"], "updated_at": row["updated_at"]}
        finally:
            conn.close()

def get_battle_raw(group_id, qq_id):
    """读取 battle 行原始状态（不做 24h 过期回收/打标），供过期提示检测用。"""
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT monster, state, updated_at FROM battle_state WHERE qq_id=?",
                (qq_id,),
            ).fetchone()
            if not row:
                return None
            state = json.loads(row["state"])
            if "type" not in state:
                state = {
                    "type": "monster", "now": 0.0,
                    "enemy": state, "p_buffs": {}, "e_buffs": {},
                    "p_defending": False, "e_defending": False,
                }
            return {"state": state, "monster": state.get("enemy", {}), "name": row["monster"], "updated_at": row["updated_at"]}
        finally:
            conn.close()

def clear_battle(group_id, qq_id):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "DELETE FROM battle_state WHERE qq_id=?", (qq_id,)
            )
            conn.commit()
        finally:
            conn.close()


