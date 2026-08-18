# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 core 层 — timed_events.py（v127.5 通用倒计时事件引擎）

把一切"限时存在 / 限时有效 / 到时触发"的玩家状态统一挂到懒计时引擎，
由任意玩家指令（_maint_gate 挂 refresh）惰性刷新，无后台定时器。

设计铁律：
- 数据驱动：新倒计时事件类型 = register_timed() + 各自读写封装，引擎零改动
- 懒计时：不跑定时器；读前 get_timed 校验 + 任意指令 refresh 物理清理
- 一致性：显示出口 + 查找出口都必须走 get_timed → 过期即不可见/不可找，
  不存在"过期还看得见"的窗口
- 存储：复用 event_state KV（一个玩家一个 key，内部 dict 多事件互不覆盖）
  key = timed_events:{qq_id}，value = JSON {"<type>:<sub>": {"type","data","expire"}}
- 纯核心：不碰 DB 以外 IO；延迟 import db 防 data/_assembly 循环

=== 用法示例 ===

# 1. 注册事件类型（模块加载时一次）
register_timed("wild_npc", duration_sec=3600)   # 默认 60 分钟，可按 NPC 覆盖

# 2. 挂载/刷新一个事件（偶遇命中时）
expire = set_timed(group_id, qq_id, key="wild:w_old_trader",
                   type_key="wild_npc", data={"map": map_id})

# 3. 读取（显示/查找出口）——过期自动惰性清除返回 None
ev = get_timed(group_id, qq_id, key="wild:w_old_trader")
if ev:  # {"type","data","expire","remain"}
    ...

# 4. 删除（主动结束事件）
remove_timed(group_id, qq_id, key="wild:w_old_trader")

# 5. 强制刷新（挂 _maint_gate，任意玩家指令触发）
refresh_timed(group_id, qq_id)

# 6. 过期回调注册（可选）：on_expire(type_key)(group_id, qq_id, data) -> None
#    引擎在过期时调用，用于清状态（如对话会话作废）
"""
import json
import time

# 事件类型注册表：type_key -> {"duration_sec": int, "on_expire": callable|None}
_EVENT_TYPES: dict = {}

# 玩家事件存储 key 模板（按玩家全局，跨群共享——倒计时只属于玩家本人）
_PLAYER_KEY = "timed_events_{qq_id}"


def register_timed(type_key: str, duration_sec: int | None = None,
                   on_expire=None) -> None:
    """注册/覆盖一个倒计时事件类型。duration_sec 默认秒数（set_timed 未传时用）。"""
    _EVENT_TYPES[type_key] = {
        "duration_sec": duration_sec,
        "on_expire": on_expire,
    }


def _load(group_id: str, qq_id: str) -> dict:
    from .. import db  # noqa: E402（延迟导入防 data/_assembly 循环）
    raw = db.get_event_state(_PLAYER_KEY.format(qq_id=qq_id))
    if not raw:
        return {}
    try:
        d = json.loads(raw)
        return d if isinstance(d, dict) else {}
    except (ValueError, TypeError):
        return {}


def _save(group_id: str, qq_id: str, data: dict) -> None:
    from .. import db  # noqa: E402
    db.set_event_state(_PLAYER_KEY.format(qq_id=qq_id),
                       json.dumps(data, ensure_ascii=False))


def set_timed(group_id: str, qq_id: str, key: str, type_key: str,
              data: dict | None = None,
              duration_sec: int | None = None) -> int:
    """挂载/刷新一个倒计时事件，返回 expire 时间戳。

    - 同 key 重复挂载 = 顶替刷新（新 expire）
    - 默认时长取类型注册值；未注册类型默认 60s（防御，正常都会 register）
    """
    cfg = _EVENT_TYPES.get(type_key, {})
    dur = duration_sec if duration_sec is not None else cfg.get("duration_sec", 60)
    expire = int(time.time()) + max(1, int(dur))
    events = _load(group_id, qq_id)
    events[key] = {
        "type": type_key,
        "data": data or {},
        "expire": expire,
    }
    _save(group_id, qq_id, events)
    return expire


def get_timed(group_id: str, qq_id: str, key: str) -> dict | None:
    """读取单个事件：未过期返回 {type,data,expire,remain}；过期惰性清除返回 None。

    所有显示/查找出口都必须走这里 → 过期即不可见（惰性正确性核心）
    """
    events = _load(group_id, qq_id)
    ev = events.get(key)
    if not ev:
        return None
    now = int(time.time())
    if now >= ev.get("expire", 0):
        events.pop(key, None)
        _save(group_id, qq_id, events) if events else _remove_whole(group_id, qq_id)
        return None
    return {"type": ev.get("type"), "data": ev.get("data", {}),
            "expire": ev["expire"], "remain": ev["expire"] - now}


def remove_timed(group_id: str, qq_id: str, key: str) -> bool:
    """主动删除一个事件（返回是否删掉了）"""
    events = _load(group_id, qq_id)
    if key not in events:
        return False
    events.pop(key, None)
    if events:
        _save(group_id, qq_id, events)
    else:
        _remove_whole(group_id, qq_id)
    return True


def _remove_whole(group_id: str, qq_id: str) -> None:
    from .. import db  # noqa: E402
    db.delete_event_state(_PLAYER_KEY.format(qq_id=qq_id))


def list_timed(group_id: str, qq_id: str, type_key: str | None = None,
               data_match: dict | None = None) -> list:
    """列出未过期事件（可选按 type / data 过滤），顺带惰性清除过期项。

    data_match：data 子集匹配（如 {"map": "oak_plain"} → 只留在该图的事件）
    返回 [{"key","type","data","expire","remain"}, ...]
    """
    events = _load(group_id, qq_id)
    now = int(time.time())
    expired = [k for k, ev in events.items()
               if now >= ev.get("expire", 0)]
    for k in expired:
        events.pop(k, None)
    if expired:
        if events:
            _save(group_id, qq_id, events)
        else:
            _remove_whole(group_id, qq_id)
    out = []
    for k, ev in events.items():
        if type_key is not None and ev.get("type") != type_key:
            continue
        if data_match and not all(ev.get("data", {}).get(dk) == dv
                                  for dk, dv in data_match.items()):
            continue
        out.append({"key": k, "type": ev.get("type"),
                    "data": ev.get("data", {}), "expire": ev["expire"],
                    "remain": ev["expire"] - now})
    return out


def refresh_timed(group_id: str, qq_id: str) -> int:
    """惰性全量刷新：扫该玩家所有事件，过期的执行 on_expire 回调 + 物理删除。

    返回清理的过期事件数（供测试断言）。
    - on_expire(type_key)(group_id, qq_id, data)：清理副作用（如会话作废）
    - 无回调的过期事件仅物理删除（静默）
    """
    events = _load(group_id, qq_id)
    now = int(time.time())
    expired = {k: ev for k, ev in events.items()
               if now >= ev.get("expire", 0)}
    if not expired:
        return 0
    for k, ev in expired.items():
        events.pop(k, None)
    if events:
        _save(group_id, qq_id, events)
    else:
        _remove_whole(group_id, qq_id)
    for k, ev in expired.items():
        type_key = ev.get("type")
        cfg = _EVENT_TYPES.get(type_key, {})
        cb = cfg.get("on_expire")
        if cb:
            try:
                cb(group_id, qq_id, ev.get("data", {}))
            except Exception:
                import logging
                logging.getLogger("dragonfall").warning(
                    f"[timed_events] on_expire 回调失败 {type_key}", exc_info=True)
    return len(expired)
