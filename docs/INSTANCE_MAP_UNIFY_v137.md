# v137 副本彻底重构：副本地图化 + 战斗引擎统一

> 2026-08-29 鱼鱼拍板：**彻底重构副本**，让副本与野外共用一套地图/探索/战斗机制。
> 本方案是唯一执行依据；实现先同步设计案（design/new_world/），再动代码。

## 一、设计意图（鱼鱼原话）

> "现在的副本我感觉不匹配我当时的设计，我希望和野外基本上是共用一套代码机制。
> 副本也是通过地图来查看当前位置，只是副本没有出去的路，探索完全一样使用移动之类的指令，
> 打怪同理，只是副本的话调查/探索/移动/交互极大概率会触发被怪物发现。"

**要点：**
1. 副本 = 封闭地图（无出口），其余机制与野外完全一致（地图/移动/探索/战斗）
2. 战斗引擎用同一套（BT.Battle），不许单独写副本战斗
3. 地图按区域设计，子区域名字不模板化，要贴合该副本区域氛围
4. 地图怪有数量上限：打完不再刷，可安心探索剩余子区域
5. 探索资源有上限：副本生成时（开本）创建好资源池，不可无限刷
6. 探索各自进行，遇怪合并进同一场战斗；移动由队长带队全体移动
7. 考虑加『加入战斗』指令（自由探索时队友遇怪可参战），需评估 CTB 支持
8. 野外组队：由格温决定是否顺势升级为同场战斗

## 二、现状侦察（2026-08-29）

| 维度 | 野外 | 副本（现状） | 差异 |
|------|------|-------------|------|
| 地图 | MAPS+SUBAREAS+SUBAREA_LINKS_INDEX 网状子区域（v115） | MAPS 有 22 张副本骨架图；SUBAREAS 每副本仅 1 个"入口"子区域；真实内容在 instances.py stages + instance_stage_maps.py | 副本不参与地图机制 |
| 移动 | world.py `移动/前往/地图/探索/调查` | instance.py `深入/调查/探索` 独立一套 | 两套命令 |
| 遇怪 | _travel_ambush 等级差概率 + 子区域 monsters 池 | _enter_stage_combat 按层推怪 | 两套生成 |
| 战斗 | BT.Battle("monster") 统一引擎（支持 enemies/allies 多对多） | instance.py 自写 ~2500 行轮流回合 CTB 状态机，BT 仅作单次结算借用 | 未统一 |

**关键结论：**
- BT.Battle 已支持 enemies（敌方阵列）+ allies（我方阵列），多对多能力已具备，只差把 instance 的多队列调度收编
- 副本的"层/stage"本质就是网状子区域（前厅→回廊→Boss房），可平移为 SUBAREAS 房间
- instance_stage_maps.py 的 POI 可直接挂到子区域

## 三、目标架构

### 3.1 数据层：副本 = 真地图

```
MAPS：22 张副本图已存在，保持 type=副本，补充 dungeon 修饰字段
SUBAREAS[inst_id]：stage 数个子区域（=层），子区域名贴合副本氛围（非模板）
SUBAREA_LINKS_INDEX[inst_id]：房间网状连通（无出口：入口房间不连野外）
instance_stage_maps 的 POI → 挂到对应子区域
instances.py 保留：Boss 定义 / 掉落 / 人数缩放 / 通关结算 / 入场钥匙
```

子区域命名规范（铁律：不模板化）：
- 哥布林营地：入口栅栏 → 篝火营地 → 酋长帐篷
- 海蚀洞窟：潮汐洞口 → 沉船滩涂 → 海盗巢穴
- 旧王陵：墓道 → 殉葬坑 → 主墓室
- 每个副本单独设计，贴合主题

### 3.2 玩法：dungeon 修饰符

```python
{
  "id": "goblin_camp", "type": "副本",
  "dungeon": {
    "no_exit": True,               # 无出口（不连野外）
    "discovery_agro": 0.85,        # 探索/移动/调查/交互 遇怪概率（85%）
    "boss_room": "goblin_camp_3",  # Boss 房
    "on_clear": "victory"          # 通关走副本结算
  }
}
```

- 移动/探索/调查/交互全部走 world.py 同一套，遇 dungeon 字段时：
  - 移动撞怪概率 = discovery_agro（0.85）而非野外 8~18%
  - **2026-08-30 设计口径注**：副本遇怪概率 = `dungeon.discovery_agro` 数据表配置（maps.py 每副本 0.85，代码默认值亦 0.85 在 core/encounter.py），固定高遇怪是**设计**——开本已校验等级（Lv 门槛），与野外等级差模型（8~18% 随 diff 浮动）互为设计差异，不是 bug。
  - 地图显示"副本内 · 无出口"；不显示传送/离开
  - 到达 Boss 房 + Boss 存活 → 触发 Boss 战
- 撤退 = 副本专属指令（保留现有『撤退』『离开副本』）

### 3.3 数量上限 + 资源上限（开本时生成）

```
开本（副本 <名字>）→ 生成 dungeon_instance 状态：
  - 每子区域怪物池数量上限（如 2-4 只），打完该子区域清空
  - 全副本资源池（宝箱/补给/遗骸 loot），总量固定，探索完即空
  - 资源池一次性创建（开本时），不可刷新（死亡重置除外——按策划案）
```

实现位置：新增 `dungeon_instance` 存档结构（db 层），存于玩家/队伍状态：
```python
{
  "inst_id": "goblin_camp",
  "rooms": {
    "goblin_camp_1": {"monsters_left": ["m_goblin_guard", "m_goblin_shaman"],
                       "pois_left": ["chest_1", "fire_1"]},
    "goblin_camp_2": {...},
    "goblin_camp_3": {"boss_alive": True}
  },
  "resources_pool": {"gold_left": 500, "mats_left": {"哥布林铁片": 3, "咕噜的皇冠": 1}},
  "leader": "qq_id", "members": [...], "created_at": ts
}
```

### 3.4 战斗：统一引擎 + 合并入战

**目标：副本战斗 = BT.Battle 一等公民（btype="instance"）**

1. **BT.Battle 收编多人 CTB**：把 instance.py 的 ct 队列/仇恨/人数缩放/自动防御/敌我多对多全部搬进 battle.py 的 instance 分支（现在 from_state 已能过 type=instance，但 __init__ 不认——补正式支持）
2. **野外组队 = 同场战斗**：野外组队打怪也走 BT.Battle allies/enemies 多对多（现在野外组队各打各的，统一后真·同场）——格温决定：**顺势统一**，理由：反正引擎要支持 instance 多对多，野外组队直接受益，一套代码两处用
3. **『加入战斗』指令**：
   - 副本内自由探索，一人遇怪进入战斗（battle 状态带 inst_id + room）
   - 队友在战斗外看到"XX 正在战斗中"→ 输入『加入战斗』并入同一场
   - CTB 支持性评估：BT.Battle 已支持 allies 动态数组（from_state 时传全部存活玩家）→ 入场玩家以 allies 追加，ct 播种 -spd，可落地
   - 野外组队同场战斗同样支持『加入战斗』（同队伍在附近时）

### 3.5 移动：队长带队

```
副本内：『移动 <方向/房间>』仅队长可执行，带队全体移动
  - 队员输入移动 → 提示"等待队长带队"
  - 队长移动 → 全队玩家 cur_subarea 同步更新，全队看到到达文案
  - 遇怪 → 全队合并进同一场战斗（队长触发）
野外组队：同样队长带队？→ 格温决定：野外维持现状（各走各的），
  副本内因为"封闭空间+合并战斗"需要队长带队，野外不加限制
```

## 四、执行计划（最大并发）

### Phase 0：设计案同步（主 agent）
- 更新 design/new_world/29_副本与组队系统.md（v137 章节：副本地图化定稿、数量/资源上限、加入战斗、队长带队）
- 写本方案文档 docs/INSTANCE_MAP_UNIFY_v137.md

### Phase 1：数据层（4 子 agent 并行）
- A1：22 副本 SUBAREAS 重写——每副本 2-4 个贴合主题的子区域（含 desc/怪/Boss 房），名字不模板化
- A2：SUBAREA_LINKS_INDEX 副本房间连通（无出口拓扑），含 Boss 房
- A3：instance_stage_maps POI → 子区域挂载 + dungeon 修饰字段进 MAPS
- A4：instances.py 瘦身对齐——Boss/掉落/缩放保留，stages 字段标记废弃（改从 SUBAREAS 读）

### Phase 2：引擎层（4 子 agent 并行）
- B1：BT.Battle btype="instance" 正式支持（多人 CTB 调度收编）
- B2：world.py 副本移动/探索/调查联动（dungeon 字段消费：discovery_agro/no_exit/Boss房）
- B3：dungeon_instance 存档结构 + 开本生成资源池 + 数量上限消耗
- B4：『加入战斗』指令 + 野外组队同场战斗（allies 动态并入）

### Phase 3：测试 + 收尾（主 agent）
- 全量测试 + 新增副本=地图断言 + 数值门禁 + 命令矩阵
- 更新 docs/ 架构文档
- 双仓库提交（dragonfall + design/new_world）

## 五、验收标准

1. 『副本 <名>』开本 → 进入副本第 1 子区域，显示环境/可前往/怪物（与野外到达同模板）
2. 『移动』在副本内可用（队长带队），无出口（不显示野外连接）
3. 『探索/调查』触发：高概率遇怪（discovery_agro）、POI 交互、资源拾取
4. 怪物有数量上限：打完不再刷；资源池有总量：探索完即空
5. 遇怪 → 进入 BT.Battle 战斗（btype=instance），CTB 行动顺序/仇恨/技能全生效
6. 队友可『加入战斗』并入同一场
7. 野外组队打怪 → 同场战斗（allies 多对多）
8. 通关/失败结算沿用（Boss 房击败 → victory；全灭 → 回城）
9. 原有副本测试全绿 + 新增断言

## 六、风险与对策

| 风险 | 对策 |
|------|------|
| 副本测试大面积红（25+ 副本测试） | 保留 instance.py 兼容层：老逻辑对无 dungeon 字段的副本不变；新逻辑只对 dungeon=True 生效。分批迁移 |
| BT.Battle 收编 CTB 改动大 | 先跑通"副本战斗 = BT.Battle instance 分支"的等价性测试（新旧输出对比），再删 instance.py 冗余 |
| SUBAREAS 重写影响百科/探索进度 | 百科从 SUBAREAS 构建，重写后重新跑 _build_ency 相关测试；探索进度 visited_subareas 表兼容旧 key（goblin_camp_1 等保留） |
| 『加入战斗』CTB 并发 | 入场以 allies 追加 + ct 播种 -spd；同 ct 玩家优先；上限防死循环（沿用 8 动 guard） |
