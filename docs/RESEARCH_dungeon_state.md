# RESEARCH：dungeon_instance 存档结构（怪物数量上限 + 探索资源池上限）

> 版本：v1（2026-08-29）｜关联：v137 副本彻底重构（docs/INSTANCE_MAP_UNIFY_v137.md §3.3）
> 补充说明：原子 agent（task-2）研究中途因上游 524 错误中断未产出文档，本文档由主 agent 基于其研究轨迹 + 现状代码分析补全。
> 结论先行：dungeon_instance 状态**并入现有副本 battle state（st）**，不新增独立表——最省事且不破坏现有 25+ 副本测试（它们全读 st）。

---

## 一、设计目标

鱼鱼 v137 要求（§3.3）：
1. **怪物数量上限**：每子区域怪物池数量上限（2-4 只按副本规模），打完该子区域清空不再刷，可安心探索其他子区域
2. **探索资源上限**：全副本资源池总量固定（宝箱/补给/遗骸 loot），开本时创建，探索完即空

---

## 二、存储决策：并入 battle state（st），不新增表

### 2.1 候选方案对比

| 方案 | 存储位置 | 优点 | 缺点 |
|---|---|---|---|
| A：并入现有 st | battle_state 表，type=instance，存队长名下 | **零新表**；现有 `_instance_battle_for`/`db.save_battle` 全复用；25+ 测试读 st 结构不变（加字段不影响） | st 变大（但 22 副本 × 每副本 2-4 房间数据量很小，JSON 体积可接受） |
| B：新表 dungeon_instances | 独立表 key=队伍/队长 | 状态隔离清晰 | 新表+新读写层；`_instance_battle_for` 要改；测试要适配；**重构量翻倍** |
| C：挂玩家 cur_map | 玩家行 | 简单 | 队伍共享状态无处放；多人副本各持一份会漂移；**不可行** |

**推荐：方案 A（并入 st）**。理由：
- 副本状态本来就是 `st`（含 members/players/alive/敌人/进度），怪物池/资源池是"进度"的延伸，语义同源
- 现有 `db.save_battle(group_id, st["leader"], st)` 一处写回，加 `rooms`/`resources_pool` 两个 key 即可
- 现有 7 个副本测试全部读 `battle["state"]` 的 st 结构，新增 key 不破坏旧断言（除非它们断言"无这些 key"——不会）

### 2.2 生命周期

```
开本（副本 <名>，_instance_start 校验通过）
  └─ 生成 dungeon_instance 状态（并入 st）：
       rooms: 每子区域怪物池（从 SUBAREAS[inst_id] 的 monsters/elite/boss 生成，数量上限）
       resources_pool: 全副本资源总量（从原 instance_stage_maps POI loot + 副本奖励配置汇总）
  └─ 落点第 1 子区域（cur_subarea = inst_id_1）
  └─ 锁全队 + save_battle(队长名下)

探索/调查/移动（world.py 统一路径，dungeon 修饰符消费）
  ├─ 遇怪判定：discovery_agro(0.85) 命中 + rooms[cur_room].monsters_left 非空
  │    └─ 弹出 1 只 → 构建敌方阵列 → 进战斗（BT.Battle instance 分支）
  │    └─ monsters_left 空 → 不再遇怪（可安心探索）
  ├─ POI 交互：rooms[cur_room].pois_left 命中 → 消耗 loot（gold/materials 从 resources_pool 扣）
  │    └─ resources_pool 耗尽 → POI 显示"已被搜刮一空"
  └─ 移动（队长带队）：cur_subarea 全体同步；目标房间 monsters_left/pois_left 状态保留

通关（Boss 房击败 → _instance_victory）
  └─ 奖励结算（沿用）+ 战利品堆/暗格/密室宝箱（沿用，从 resources_pool 剩余扣）
  └─ 停留 30 分钟自动传出 / 『离开副本』主动传出 → 清 battle

失败（全灭 → _instance_defeat）
  └─ 全队回城 + 清 battle（进度重置）
  └─ 决策：死亡重置 = 进度清零，下次开本**重新生成**怪物池+资源池（策划案"POI 全部还原"语义）
```

### 2.3 数据结构（v137 目标）

```python
# st 新增两个 key（其余不变）
st["rooms"] = {
    "goblin_camp_1": {
        "monsters_left": [                          # 该房间剩余怪物池（战斗构建源）
            ["m_goblin_guard", "哥布林守卫", "tank", 15, ["ms_dun_ji"], ["哥布林铁片"]],
            ["m_goblin_shaman", "哥布林萨满", "healer", 16, ["ms_zhi_liao", "ms_du_wu"], ["萨满图腾"]],
        ],
        "pois_left": ["chest_1", "fire_1"],          # 该房间剩余可交互 POI id
        "boss_alive": False,                          # 仅 Boss 房 True
    },
    "goblin_camp_2": { "monsters_left": [...], "pois_left": [...], "boss_alive": False },
    "goblin_camp_3": { "monsters_left": [], "pois_left": [], "boss_alive": True },
}
st["resources_pool"] = {
    "gold_left": 500,                                 # 全副本剩余金币总量
    "mats_left": {"哥布林铁片": 3, "咕噜的皇冠": 1},  # 全副本剩余材料总量
    "equip_left": ["eq_goblin_blade"],                # 全副本剩余装备（可选）
}

# 开本时从哪生成：
#   1) rooms：SUBAREAS[inst_id] 每房间的 monsters/elite/boss 槽 → 转成 monsters_left 列表
#      数量上限：普通怪 ≤ 每房间配置数（现状 stages 每层 1-3 只 → 直接取），
#      elite/boss 固定 1 只。**不加新上限**——现状配置就是设计上限（打完即空）
#   2) resources_pool：原 instance_stage_maps 各层 POI loot（gold/materials）
#      + INSTANCES[inst_id] 的 gold/exp/materials（通关奖励部分不走池，池只含探索拾取）
#      + Boss 掉落（mat_count 数量上限，Boss 只掉 1 次，不进池）
```

### 2.4 数量上限语义（关键设计）

- **怪物数量 = 现状配置数**：每个房间的 monsters 列表长度就是上限（1-3 只普通怪 + 0-1 elite + 0-1 boss），打完即空，不再刷。
- **为什么不再加"生成上限"**：现状 stages 每层怪本来就不刷新（打一次少一次，层肃清后进下层）。地图化后"数量上限"自然成立——每个房间的怪池是开本时固定的，消耗完就没了。**不需要额外的随机生成器**。
- **Boss 只 1 只**：boss_alive 标记，击败后 False，不再出。
- **资源池上限**：loot 总量开本时汇总，探索拾取扣减，扣完即空。**防刷**——同一副本内不能反复刷宝箱（现状"一次消费"已保证，池化后更彻底）。

---

## 三、探索/调查/移动的消费链路（world.py 统一路径）

### 3.1 遇怪（discovery_agro）

```
玩家在副本子区域 cur_room：
  探索/移动/调查/交互 触发
  ├─ if rooms[cur_room].monsters_left 空 → 不遇怪（文案"这里已被肃清"）
  ├─ if random < discovery_agro(0.85):
  │    monster_def = rooms[cur_room].monsters_left.pop(0)   # 消耗 1 只
  │    → C.build_monster + build_monster_group → BT.Battle(btype="instance", enemies=阵列, allies=队伍快照)
  │    → save_battle + 锁全队
  └─ else: 无事 / POI / 陷阱（小概率）
```

### 3.2 POI 交互（资源池消耗）

```
调查 <POI名>：
  ├─ if poi_id in rooms[cur_room].pois_left:
  │    poi = SUBAREAS[inst_id] 房间 pois 中查（或 SUBAREA_POIS 挂载）
  │    loot = poi["loot"]（gold/materials）
  │    → 从 resources_pool 扣减（gold_left -= n，mats_left 同名 -1）
  │    → 发放入包
  │    → rooms[cur_room].pois_left.remove(poi_id)
  │    → 文案："你打开了宝箱，获得金币 ×50！"
  └─ else: "这里已经空空如也。"
```

### 3.3 移动（队长带队）

```
移动 <房间>（仅队长）：
  ├─ 校验：目标房间在 SUBAREA_LINKS_INDEX[inst_id] 连通表内
  ├─ 全队 cur_subarea 同步更新（db.update_player 每个成员）
  ├─ 遇怪判定（3.1）→ 进战斗 or 到达文案
  └─ 队员输入移动 → 提示"等待队长带队～"
```

---

## 四、对现有测试的影响（minimal 侵入原则）

现有 7 个副本测试读 `st` 的 key：`type/inst_id/leader/members/alive/players/boss/enemy/round/turn/stage_idx/stage_pending/stage_cleared/inst_stages/mode/stage_pois/...`。

**方案 A（并入 st）** 下：
- 新增 `rooms`/`resources_pool` 两个 key → **不破坏任何旧断言**（除非断言 `set(st.keys()) == {...}` 精确相等——检查过没有）
- 但 `stage_pending`/`stage_idx`/`inst_stages`/`stage_pois` 等**旧 key 仍在**（v137 过渡期保留，映射到新结构）→ 测试全绿
- 真正红的测试是**命令行为变化**（『深入』废弃→『移动』、探索走 world 路径）——那是波次 3 命令层改造后的事，测试跟着改（详见 RESEARCH_test_impact.md）

**结论：dungeon 存档本身零破坏；行为变化在命令层。**

---

## 五、边界情况

| 场景 | 处理 |
|---|---|
| 开本时生成 rooms | 从 SUBAREAS[inst_id] 读房间，每房间 monsters/elite/boss 转 monsters_left；pois 转 pois_left |
| 资源池不足 | 发放入包前检查扣减够不够；不够则只发剩余 + 文案提示 |
| 全灭重置 | 进度清零；下次开本重新生成（怪物池+资源池满血复活） |
| 撤退保留 | retreated 标记下 rooms/resources_pool 保留（下次恢复继续） |
| 通关停留 | Boss 房战利品堆/暗格从 resources_pool 剩余扣；30 分钟自动传出 |
| 多人副本 | 怪物池/资源池共享（存队长 st）；各成员探索消费同一池 → 竞争由 SQLite 锁保护 |
| 加入战斗 | 新成员并入 st（见 RESEARCH_join_battle.md），rooms/resources_pool 不变 |

---

## 六、实施要点（供波次 2/3 落地）

1. `_instance_build_state`（instance.py:945）新增 rooms/resources_pool 生成逻辑（读 SUBAREAS[inst_id]）
2. `_instance_explore` 改为消费 rooms[cur_room].monsters_left（discovery_agro 判定）
   - **2026-08-30 设计口径注**：副本遇怪概率 = `dungeon.discovery_agro` 数据表配置（maps.py 0.85；代码默认 0.85 在 core/encounter.py），固定高遇怪是**设计**——开本已校验等级，与野外等级差模型互为设计差异。
3. `instance_investigate` 改为消费 pois_left + resources_pool
4. world.py `移动` 加副本分支（队长带队 + 房间连通 + 遇怪）
5. 测试：新增"数量上限"断言（打完不刷）+ "资源池"断言（探索完即空）
