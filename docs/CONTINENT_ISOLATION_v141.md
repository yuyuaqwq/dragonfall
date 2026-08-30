# 大陆隔离架构重构方案（v141 提案 · 完整版）

> 2026-08-30 鱼鱼拍板方向：**位置用结构体传递，新增大陆 id 只是结构体加一个字段**。
> 地图资源挂载在指定大陆下，副本 = 动态创建/销毁的独立大陆实例，代码完全复用，不关心队伍。
> 本文档是提案，未拍板落地；落地前先同步 design/new_world/ 再动代码。
> 文档状态：✅ 已存档 docs/；⏳ 待鱼鱼拍板。

---

## 〇、一句话方案

**把"玩家位置"从两个裸字符串（cur_map / cur_subarea）升级为一个结构体（world_id + map_id + subarea_id），副本 = 动态创建/销毁的独立大陆实例。** 大陆 id 只是结构体一个字段，地图资源挂载在指定大陆下，代码完全复用，队伍问题自然消失。

---

## 一、为什么做（现状问题清单）

### 1.1 现状数据流

```
player.cur_map     = "goblin_camp"        # 裸字符串
player.cur_subarea = "goblin_camp_1"      # 裸字符串
```

- **89+ 处**直接访问这两个字段（world/combat/economy/instance/gm 等命令层）
- 地图表（MAPS/SUBAREAS）是**全局唯一**的，副本才靠 battle_state 状态机硬撑隔离
- 副本状态 = `battle_state` 表按**队长 qq_id** 存一份 JSON 快照 + 一堆反查补丁兜底

### 1.2 问题清单（2026-08-30 代码侦察）

| # | 问题 | 根因 |
|---|------|------|
| 1 | 撤退后打普通怪 → `save_battle` ON CONFLICT(qq_id) **覆盖副本进度** | 状态挂队长个人行 |
| 2 | 队员副本中退队 → 删行成功但 cur_map 残留在副本图 → **卡图** | 位置与状态两处存 |
| 3 | 队长副本中退队 → party 行删光，副本状态**僵尸化**、结算空转 | 状态挂队长，队长会变 |
| 4 | 位置（cur_map）与副本状态（battle_state）两处存，同步靠约定，**漏同步即错位** | 无唯一真相源 |
| 5 | 未来加"平行世界/大陆"（海底/天空/活动大陆）**无结构支撑** | 无 world 概念 |

---

## 二、目标架构

### 2.1 位置结构体（核心中的核心）

```python
# game/core/position.py
class Position:
    """玩家位置。大陆 id + 地图 id + 子区域 id 三元组。"""
    __slots__ = ("world_id", "map_id", "subarea_id")

    def __init__(self, world_id: str, map_id: str, subarea_id: str = ""):
        self.world_id = world_id
        self.map_id = map_id
        self.subarea_id = subarea_id

    @classmethod
    def from_player(cls, player: dict) -> "Position":
        """从玩家存档解析位置。world_id 缺省 = 主大陆（兼容旧存档）。"""
        w = player.get("world_id") or "mainland"
        return cls(w, player.get("cur_map", ""), player.get("cur_subarea", ""))

    def key(self) -> str:
        """落库键：'mainland:goblin_camp:goblin_camp_1'"""
        return f"{self.world_id}:{self.map_id}:{self.subarea_id}"

    def to_db(self) -> tuple:
        """(cur_map, cur_subarea, world_id) —— 兼容现状 update_player 调用"""
        return self.map_id, self.subarea_id, self.world_id

    def is_instance(self) -> bool:
        """是否在副本大陆实例里"""
        return self.world_id.startswith("inst:")

    def resolve_map(self):
        """按世界解析地图 dict——唯一入口，替换全游戏 C.MAP_BY_ID.get(map_id)"""
        if self.is_instance():
            return instance_worlds.get(self.world_id, {}).get("maps", {}).get(self.map_id)
        return C.MAP_BY_ID.get(self.map_id)

    def __repr__(self):
        return f"<Position {self.world_id}:{self.map_id}:{self.subarea_id}>"
```

### 2.2 存储：players 表加 world_id 列（零迁移）

```sql
ALTER TABLE players ADD COLUMN world_id TEXT DEFAULT 'mainland';
```

- `cur_map` / `cur_subarea` 保持原列（值不变：主大陆 = 裸 map_id；实例大陆 = 同 map_id）
- `world_id` = `"mainland"`（主大陆）或 `"inst:<uuid>"`（副本实例大陆）
- **旧存档 world_id 缺省 = 'mainland' → 零迁移成本，旧行为完全不变**

### 2.3 大陆（world）抽象

```python
# game/core/worlds.py
from .position import Position

# 静态大陆：主大陆 = 全游戏地图共享
WORLDS = {
    "mainland": {
        "name": "奥兰迪亚大陆",
        "maps": MAP_BY_ID,          # 静态共享引用
        "is_instance": False,
    },
}

# 动态副本大陆（内存态 + 落库 event_state 防重启丢失）
instance_worlds = {}   # world_id -> {
                       #   "name": "哥布林营地副本",
                       #   "maps": {map_id: map_def},     # 克隆的副本图
                       #   "subareas": {map_id: [sa...]}, # 克隆的子区域
                       #   "created_at": ts,
                       #   "leader": qq_id,              # 仅展示/带队，不承载状态
                       #   "members": [qq_id...],        # 进本快照（展示用）
                       #   "rooms": {...},               # 怪池/资源池
                       #   "resources_pool": {...},      # 奖励总量
                       # }

def create_instance_world(inst_id, members, boss, now) -> str:
    """开本：克隆副本地图为独立大陆。返回 world_id 'inst:<uuid>'。"""
    world_id = f"inst:{uuid4().hex[:12]}"
    map_id = inst_id[5:] if inst_id.startswith("inst_") else inst_id
    # 克隆 = 现状 _instance_build_state 的 rooms/resources_pool 逻辑搬到此处
    instance_worlds[world_id] = {
        "name": INSTANCES[inst_id]["name"],
        "maps": {map_id: deepcopy(MAP_BY_ID[map_id])},
        "subareas": {map_id: deepcopy(SUBAREAS[map_id])},
        "created_at": now,
        "leader": str(members[0]),
        "members": [str(m) for m in members],
        "rooms": _build_rooms(map_id),
        "resources_pool": _build_pool(inst_id, map_id),
    }
    # 落库 event_state：instance_world_{world_id} = json
    return world_id

def destroy_instance_world(world_id):
    """退本/失败/超时/过期：销毁大陆实例。通关不销毁（停留搜刮属设计，『离开副本』才销毁）。"""
    instance_worlds.pop(world_id, None)
    db.delete_event_state(f"instance_world_{world_id}")
```

### 2.4 副本 = 动态大陆（核心简化）

```
『副本 <名字>』
  → world_id = create_instance_world(inst_id, members, boss)
      ├── 克隆该副本 MAPS/SUBAREAS → instance_worlds[world_id]
      ├── 全队 player.world_id = world_id
      │       player.cur_map / cur_subarea = 入口（同现状）
      └── 副本进度（rooms / resources_pool）挂在大陆实例上

『撤退』
  → 保留大陆实例（进度保留），world_id 不动

『通关/失败/离开』
  → 通关：**保留大陆实例**（停留搜刮属设计，world_id 不动；主动『离开副本』才 destroy → 全员回 mainland）
  → 失败：destroy_instance_world(world_id) + 全队回城（world_id 回 "mainland"）
  → 离开（『离开副本』/30min 通关超时）：destroy_instance_world(world_id) → 全员 world_id 回 "mainland"
```

**队伍问题彻底消失：**

| 场景 | 现状（battle_state 挂队长） | 大陆隔离后 |
|------|---------------------------|-----------|
| 队员退队 | 卡副本图 | 只影响个人，副本大陆还在 |
| 队长退队 | 状态僵尸化、结算空转 | leader 只是展示字段，副本照常 |
| 撤退后打怪 | save_battle 覆盖进度 | 进度在大陆实例上，碰不到 |
| 多队伍同本 | 靠补丁不冲突 | 各自 `inst:<uuid>` 天然隔离 |
| 换队 | 结算按当前队伍过滤（补丁） | 新队伍新 `inst:<uuid>`，旧副本自动过期回收 |

---

## 三、访问入口收口（改动大头，分三阶段）

现状 **389 处** `C.MAP_BY_ID.get(map_id)` / `SUBAREAS.get(map_id)` / `map_entry_subarea(map_id)` + **87 处**队伍/副本反查。

**策略：不一次性改 389 处，用适配层分阶段收口。野外玩家零差异，副本玩家走新逻辑。**

### Phase 1：新增适配层（零行为变更）

```python
# game/core/position.py 或 maps.py 新增：
def cur_map_obj(player) -> dict:
    """按玩家位置解析当前地图 dict（唯一入口）。"""
    return Position.from_player(player).resolve_map()

def cur_subareas(player) -> list:
    """当前地图的子区域列表（按世界解析）。"""
    pos = Position.from_player(player)
    if pos.is_instance():
        return instance_worlds[pos.world_id]["subareas"].get(pos.map_id, [])
    return C.SUBAREAS.get(pos.map_id, [])
```

命令层新增代码统一走新入口；旧代码不动（读到的还是主大陆结果，因为默认 world=mainland）。

### Phase 2：热路径优先替换（world/combat 移动/战斗）

把移动/探索/战斗的 `cur_map` 解析换新入口——**只有进副本的玩家 world_id != mainland**，普通玩家行为零变化。

> **2026-08-30 审计更新**：Phase 2 **未落地**——`Position` 结构体与 `resolve_map` 已导出但命令层 0 调用（`worlds.py` 的 `update_instance_world`/`get_instance_st`/`list_instance_worlds`/`resolve_map_for` 亦 0 消费）。现状副本内地图解析仍是 instance.py/world.py 各自读克隆大陆 + 全局静态图回退（v141 已修副本移动 4 处裸 `MAP_BY_ID` → 大陆感知）。Phase 3 的 87 处反查删除亦未执行（`_instance_battle_for` 等仍在用）。热路径收口列为**后续工作**。

### Phase 3：全部收口 + 删补丁

- `_instance_battle_for` / `_instance_current_members` / `retreated` 相关 **87 处反查逐步删除**（副本状态不再挂队长）
- `update_player` 里"cur_map 变自动补 cur_subarea"的隐式约定删除（改由 Position 显式管理）

---

## 四、副本生命周期

```
开本:  create_instance_world → 全队 world_id = inst:<uuid>
探索:  world.py 移动/探索走副本分支（`_instance_move_route`/`_instance_dungeon_move`/`_instance_explore`，
       大陆感知：优先读克隆大陆 `instance_worlds[world_id].maps`，回退全局静态图）
       — 副本大陆的 no_exit/discovery_agro/boss_room 从克隆的 map def 读
       （注：Position.resolve_map() 唯一入口尚未全面接管，见 §三 Phase 2 审计更新）
战斗:  BT.Battle 照旧（btype=instance 瞬态结算器，enemies/allies 多对多）
       — 战斗状态仍存 battle_state（战斗本身是瞬间的），
         但副本进度（rooms/resources_pool）挂大陆实例
撤退:  保留大陆实例（进度保留），world_id 不动
通关:  保留大陆实例（进度保留，world_id 不动）——**属设计**：通关后停留搜刮
       （战利品堆/暗格/密室宝箱/调查点，v101.27 #390），玩家主动『离开副本』才
       destroy_instance_world → 全员回 mainland（instance.py ~622-646）
失败:  全灭 → 回城 + destroy_instance_world（大陆销毁，进度作废）
超时:  通关停留超 30 分钟 → 自动解除战斗锁/清 battle（不传送、不销毁大陆，
       玩家 cur_map 本就未占副本位置；沿用『离开副本』口径）
过期:  24h 无活动 → 惰性回收（BATTLE_STALE_SEC 打标 + cleanup_stale_instances 兜底销毁）
```

> **2026-08-30 审计更正（与 v141 原稿差异）**：原稿"通关 → destroy_instance_world → 全员回 mainland"**与实现不符**——通关**保留大陆属设计**（停搜刮，主动『离开副本』才销毁回 mainland）；超时/过期路径才销毁/回收大陆。30min 超时与 24h 过期此前缺失 destroy_instance_world 接线，已列入修复（补 destroy + world_id 回写、cleanup_stale_instances 接线 base.py `_maint_gate` + main.py 启动）。

---

## 五、迁移与测试清单

### 迁移
- [ ] `players` 表加 `world_id` 列（ALTER TABLE，默认 mainland，零迁移）
- [ ] 旧存档回归：world_id 缺省 → mainland，所有旧行为不变

### 新增代码
- [ ] `Position` 结构体 + 单测（from_player/key/to_db/is_instance/resolve_map）
- [ ] `worlds.py` 的 `WORLDS` / `create_instance_world` / `destroy_instance_world` + 单测
- [ ] 适配层 `cur_map_obj` / `cur_subareas` 替换热路径

### 行为验证
- [ ] 副本开本/撤退/通关/失败/过期全链路改走大陆实例
- [ ] 队伍重组用例：副本中退队 / 队长退队 / 换队 → 不卡图、不僵尸、可继续
- [ ] 多队伍同本并发用例（A 队打 Boss，B 队刚进入口，互不影响）
- [ ] 全量测试绿 + 数值门禁（run_numeric_tests.py）
- [ ] 双仓库提交（dragonfall + design/new_world）

---

## 六、风险与对策

| 风险 | 对策 |
|------|------|
| 389 处访问收口遗漏 → 副本内查错地图 | 适配层 + Phase 2 热路径优先；副本内只走新入口，野外走旧入口零差异 |
| 副本大陆克隆与现状行为漂移 | 克隆逻辑 = 现状 `_instance_build_state` 搬运，等价性测试（新旧输出对比） |
| 动态大陆内存增长（inst 只增不删） | 生命周期强制销毁 + 过期回收（**已接线落地**：30min 通关超时补 destroy + world_id 回写、24h 过期补 destroy、`cleanup_stale_instances` 挂 base.py `_maint_gate` 懒清理 + main.py 启动兜底 + worlds.py event_state 键扫描清 DB 残留）；world_id 落库可查 |
| 与 v140 资源渠道波 2-4 冲突 | 独立版本窗口做，不夹在资源迭代里 |
| 副本战斗状态仍挂 battle_state | 战斗是瞬时状态（几回合），副本**进度**才是持久状态（挂大陆）——战斗行过期回收逻辑保留即可 |

---

## 七、为什么"结构体"是关键（设计论证）

鱼鱼说得对：**不是"加一个字段"这么简单，而是"位置应该用结构体传递"**。

- 现状：`cur_map` / `cur_subarea` 是**裸字符串**，散落 89+ 处，每个调用点自己拼逻辑
- 改后：`Position` 结构体是**唯一真相源**，所有逻辑从 `Position` 出发
  - 新增字段（world_id）→ 只在 `Position` 一处加
  - 新增行为（大陆感知）→ 只在 `resolve_map()` 一处加
  - 所有调用点**不用改**，因为入口统一了

**这是从"数据驱动"升级到"类型驱动"**——和 v137 把副本从"独立逻辑"收编为"真地图"是同一个方向：让结构说话，而不是让散落的字符串约定说话。
