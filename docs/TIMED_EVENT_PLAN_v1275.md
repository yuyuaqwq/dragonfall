# v127.5 通用倒计时事件系统（TimedEvent Engine）

> 状态：方案待鱼鱼确认后开工
> 关联：限时野外NPC（v127.5）+ 未来一切"限时存在/限时有效"内容
> 铁律：数据驱动、通用引擎、任意玩家指令触发惰性更新（不误伤日常闲聊）

---

## 1. 背景与动机

鱼鱼反馈：野外NPC偶遇（奇遇）存在"地图上看不到却能对话"的不自洽。确认方案——
**限时NPC**：偶遇触发后进入"在场限时"状态，倒计时内地图可见 + 可对话；
倒计时结束，显示与对话**同时消失**（两处强制一致）。

进一步：这个机制不是野外NPC专属，而是"限时存在/限时有效"这一类需求的
**通用样板**。未来可挂载：
- 限时NPC（本版本第一个实例）
- 限时任务/限时悬赏（过期回收）
- 限时商店/限时折扣（过期撤摊）
- 限时Buff/保护期（过期清状态）
- 流星许愿窗口、限时奇遇演出…

因此设计为**通用倒计时事件引擎**，野外NPC只是第一个事件类型。

---

## 2. 架构

### 2.1 数据模型（存储：event_state，零 DDL 迁移）

```
event_state key = timed_events:{qq_id}
value = JSON  dict，一个玩家可同时挂多个独立倒计时事件：

{
  "wild:w_old_trader": {
      "type": "wild_npc",          # 事件类型（驱动渲染/过期回调）
      "data": {"map": "oak_plain"}, # 类型私有数据（限时NPC绑地图）
      "expire": 1752230000          # Unix 过期时间戳（挂载时算好）
  },
  "wild:w_forest_girl": {
      "type": "wild_npc",
      "data": {"map": "white_deer_forest"},
      "expire": 1752233600
  }
}
```

- **key 规则**：`{type}:{子键}`（如 `wild:w_old_trader`），同类型可多开
- 按玩家（qq_id）隔离：各人偶遇各自倒计时，互不影响（符合"每个玩家自己的奇遇"）
- 不建新表、不加字段：直接复用 `event_state` KV，避免 DB 迁移

### 2.2 模块：`game/core/timed_events.py`（新）

```python
TIMED_EVENT_TYPES = {}  # 事件类型注册表：type → {duration默认, on_expire回调, ...}

def register_timed(type_key, duration=None, on_expire=None):
    """注册/覆盖事件类型（数据驱动：新事件 = 注册一行 + 各自读写封装）"""

def set_timed(group_id, qq_id, key, type_key, data=None, duration=None) -> int:
    """挂载/重置一个倒计时事件，返回 expire 时间戳。同 key 重复挂 = 顶替刷新"""

def get_timed(group_id, qq_id, key) -> dict | None:
    """读单个事件（未过期返回 {type, data, expire, remain}，过期惰性清理返回 None）"""

def refresh_timed(group_id, qq_id) -> None:
    """惰性全量刷新：扫该玩家所有事件，过期的执行 on_expire 回调 + 物理删除"""

def _load(group_id, qq_id) -> dict
def _save(group_id, qq_id, data) -> None
```

- 位置：`game/core/`（与 wild.py / achievement 等同级，纯核心无 astrbot 依赖）
- `on_expire` 回调注册在类型表：过期时的"清理动作"（如限时NPC过期的会话作废、
  限时商店撤摊、限时任务标记超时）由具体类型声明，引擎只负责时序

### 2.3 挂载点：任意玩家指令触发刷新（关键设计）

**入口：`base.py _maint_gate`（priority=100 最早 handler，所有游戏指令必经）**

```python
async def _maint_gate(self, event):
    group_id, qq_id = self._uid(event)
    # v127.5 通用倒计时引擎：任意玩家指令进入先刷一次（惰性清理过期事件）
    try:
        timed_events.refresh_timed(group_id, qq_id)
    except Exception:
        pass  # 刷新失败不影响指令主流程（留痕）
    ...  # 原有停服拦截逻辑不变
```

**为什么是这里**：
- `_maint_gate` 带 `@filter.regex(空前缀)` + `@filter.custom_filter(_GameCmdFilter)` +
  `priority=100`：**只有游戏指令**会执行它 → 玩家发任何游戏指令都先刷一次倒计时
- 日常闲聊不是游戏指令 → 不进 `_GameCmdFilter` → 不触发刷新，零误伤、零开销
- 它是异步 handler，DB 同步调用没问题（event_state 本身就是同步 sqlite）
- GM 指令（gm_ 前缀）也走 custom filter？——gm_ 是否过 `_GameCmdFilter` 需验证，
  若不过则 GM 指令不刷（无害：GM 是管理号，无玩家倒计时）

**惰性正确性证明**：
- 显示出口（地图/对话/列表）+ 查找出口（找NPC/对话中）**全部走 `get_timed`**，
  过期即不可见/不可找 → 不存在"过期还看得见"的窗口
- 未经任何出口触碰的过期事件：下一条玩家指令触发 `refresh_timed` 物理清理；
  若无后续指令，残留仅一条 event_state 行，无害，且下次 `set_timed` 同 key 顶替
- 新偶遇 = `set_timed` 顶替旧 key，不会读到旧残留

---

## 3. 限时NPC = 第一个事件类型

### 3.1 数据

```
wild_npcs.py WILD_NPCS 每 NPC 可选加 "duration": N  # 分钟，缺省 TIMED_EVENT_TYPES["wild_npc"] 默认 60
```

### 3.2 偶遇触发（wild.py roll_wild_encounter 命中后）

```python
# 偶遇命中 → 挂限时事件（不直接用独立 wild_present key，走通用引擎）
timed_events.set_timed(group_id, qq_id, f"wild:{nid}", "wild_npc",
                       data={"map": map_id}, duration=分钟)
```

### 3.3 显示出口（地图/位置/裸对话/子区域）

- `map_view` / `_subarea_body`：查 `get_timed(qq, "wild:<nid>")` 且 `data.map == 当前图`
  → 追加行 `🧭 {icon}{name} ⏳剩{n}分`（在场NPC区块）
- `_start_talk_list`（裸对话）：在场NPC并入列表（带倒计时）
- 过期 → `get_timed` 返回 None → 不再显示（天然一致）

### 3.4 查找出口（对话）

- `find_npc`：名字/序号先查在场限时NPC（`get_timed`）→ 命中即找到
- `_find_wild_npc`：加在场判定（原"条件满足即无条件找到"改为仅在场可找；
  不在场 → 走 `_wild_unseen_hint` → "今天没遇到，多『探索』试试"）
- `talk_choice` 对话中：会话续秒前查 `get_timed`，过期 → "已经离开了"清会话
  （复用现有 npc_map_id 地图失效模式同一位置）

### 3.5 过期回调（on_expire）

```python
TIMED_EVENT_TYPES["wild_npc"] = {
    "duration": 60,        # 默认 60 分钟
    "on_expire": _wild_npc_expire,  # 清对应 talk_state（若有进行中对话）
}
```

---

## 3A. prof_wait（垂钓/采集/挖掘等待型副业）收编进引擎

鱼鱼拍板：已有需要计时的机制（垂钓/采集等）统一走懒计时方案。
现状：`economy.py _prof_wait_*` 用 `prof_wait_{qq}` 存 `{finish,type,extra}` +
`asyncio.sleep` 延迟推送（进程重启丢推送）。

### 收编目标（对外接口零改动，调用方不感知）

| 现状函数 | 收编后 | 说明 |
|---|---|---|
| `_prof_wait_key` | `timed_events` 内部 key `prof_wait:{qq}` | 单事件（等待型副业互斥，同一玩家一次只挂一个） |
| `_prof_wait_state` | `get_timed` → 返回 `{finish,type,…extra}` 兼容形状 | 调用方（no_prof_waiting/flow/settle/instance 队检）零改动 |
| `_prof_wait_begin` | `set_timed(..., "prof_wait", data={type,extra}, duration_sec=wait)` | 保留延迟推送(尽力而为) + 懒结算兜底 |
| `_prof_wait_clear` | `remove_timed` | 引擎新接口 |
| `_prof_delayed_push` | 保留 | asyncio 推送仍靠它，懒计时兜底进程重启丢失 |

关键：`_maint_gate` 挂 refresh 后，垂钓到点 → 玩家下一条游戏指令触发惰性结算
（`_prof_settle` 入包+推送），进程重启丢推送问题一并解决。

### 收编范围（冷却类哪些一并收编）

| 机制 | 位置 | v127.5 是否收编 |
|---|---|---|
| prof_wait（垂钓/采集/挖掘） | economy.py | ✅ 本次 |
| 城镇POI 60s 冷却 / 精英提示 10min 冷却 | combat.py | ⏳ 二期（同文件与限时NPC接入冲突，拆批做） |
| PVP袭击 2min / 灰名 10min | combat.py | ⏳ 二期 |
| 红名/幸运/体力回复 | player 字段 | ❌ 数值持久字段，非倒计时事件，不动 |
| 技能冷却（回合制）/世界事件展示倒计时 | battle.py/social.py | ❌ 回合制/展示型，不适用 |



## 4. 与现状的差异（行为变更清单）

| 场景 | 现状 | v127.5 后 |
|---|---|---|
| 偶遇老马后发『对话 老马』 | 无条件找到 | 在场（60min内）找到 |
| 偶遇前发『对话 老马』 | 无条件找到 | 提示"今天没遇到，探索试试" |
| 地图/位置看老马 | 看不到 | 在场可见 + ⏳倒计时 |
| 裸『对话』列表 | 无野外NPC | 在场野外NPC并入（带倒计时） |
| 偶遇后去其他图再回来 | 一直在 | 未过期还在（绑 map），过期消失 |
| 任务giver（采药女等） | 任务/交付随时 | 在场期可接可交，过期等下次偶遇（鱼鱼拍板） |

---

## 5. 通用扩展示例（未来挂载）

```python
# 限时商店：野外商人不来了就撤摊
timed_events.register_timed("wild_shop", duration=30, on_expire=撤摊)
# 挂载
timed_events.set_timed(gid, qq, "shop:老马", "wild_shop", data={"shop": ...})
# 显示
shop_view 查 get_timed(...) → 在场显示"🛒 行商货摊 ⏳剩X分"
```

新增一个倒计时需求 = `register_timed` 一行 + 各自渲染/读写封装，引擎零改动。

---

## 6. 待验证风险

1. **GM 指令是否过 `_GameCmdFilter`**：gm_ 前缀走不走 custom_filter？若不过，
   GM 指令不触发刷新（无害）。开工时用现有测试框架验证 handler filter 链。
2. **_maint_gate 停服分支**：停服时非 GM 直接被拦 return，刷新放拦截前
   （上面伪代码已保证刷新在拦截之前执行 → 停服也会清，无害）。
3. **同图多个野外NPC**：dict 多开互不覆盖（如橡木平原老马+其他），各自倒计时。
4. **快捷指令/翻页快捷键**：它们是否过 `_maint_gate`？—— 它们是游戏指令
   （shortcut_trigger/page_flip 带 _GameCmdFilter 自定义逻辑），应会触发刷新，
   开工时验证。

---

## 7. 测试计划（tests/test_v1275_timed_events.py）

1. **通用引擎**：set → get（未过期）；set → 过期 → get None；refresh 物理清理
2. **限时NPC 全链路**：偶遇（用固定时间/短路 random）→ 地图可见带倒计时 →
   『对话 名字』找到 → 裸『对话』列表含它 → 改地图丢失 → 回图仍在 → 过期后
   地图/对话同时不可见不可找 → 重新偶遇恢复
3. **任务 giver 限时**：采药女在场可接取/交付；过期后再触发可交（鱼鱼拍板语义）
4. **惰性正确性**：过期残留未被清理时，任何出口都不可见（不读旧状态）
5. **挂载点回归**：任意游戏指令后刷新执行（mock refresh 计数）；闲聊不触发

---

## 8. 文件改动清单

| 文件 | 改动 |
|---|---|
| `game/core/timed_events.py` | **新增** 通用引擎（register/set/get/refresh） |
| `game/core/__init__.py` | 导出 timed_events |
| `game/core/wild.py` | roll 命中挂事件；wild_npc_findable 语义微调 |
| `game/commands/base.py` | `_maint_gate` 挂 refresh_timed（任意指令触发） |
| `game/commands/world.py` | map_view/_subarea_body/_start_talk_list/find_npc/talk_choice 接入 |
| `game/data/wild_npcs.py` | 可选 duration 字段 |
| `game/commands/combat.py` | 偶遇文案加 ⏳ 剩余提示 |
| `tests/test_v1275_timed_events.py` | **新增** |
| `design/new_world/23_指令系统与交互设计.md` | 同步倒计时/限时规则 |
| `docs/LIMITED_NPC_PLAN_v1275.md` | 本文档 |
