# 副本/野外合并审计 — 两轮汇总（2026-08-30）

> 10 个只读审计 agent（第一轮 4 个 + 第二轮 6 个）+ 主 agent 自查交叉验证。
> git HEAD=c0ac0fc（v141 大陆隔离），全量 225/225 绿。审计全程只读，未改任何代码。

## 一、核心结论：副本与野外"合并了，但没真合并"

鱼鱼的直觉是对的。v137 副本地图化 + v141 大陆隔离的**主链路成立**（无 P0 崩溃级 bug），
但**战斗引擎是"假合并"**——v137 宣称"收编进 battle.py"，实际是**代码平移了没接线**，
副本战斗仍走 instance.py 手写的老 CTB。这是"感觉不是一套"的根因。

## 二、按模块判定（统一 / 双轨 / 未覆盖）

| 模块 | 判定 | 证据 |
|------|------|------|
| 移动入口 | ✅ 部分统一 | world.move 顶部路由 _instance_move_route；落点复用 _subarea_arrive |
| 移动解析 | ⚠️ 三段重复 | route(instance.py:671-698) ≡ dungeon_move(world.py:1689-1715) ≡ move 同图分支(1317-1365)，逐字相同 24/28 行，一次移动解析 2 遍 |
| 遇怪 | ⚠️ 双轨 | 野外 _travel_ambush 等级差概率 vs 副本 discovery_agro 0.85 固定；**0.85 是设计意图**（开本已校验等级），但两份实现 + 池消费各写各的 |
| 战斗引擎 | ❌ 假合并 | battle.py `_inst_*` 9 方法**全项目 0 调用**（死闭包）；instance.py `_instance_*` 10 方法全在用。同一逻辑两份实现，只有命令层那份活着 |
| 探索/调查 | ⚠️ 部分统一 | 探索入口统一；调查是副本专属（野外无）；通关后调查点 vs 房间 POI 双通道有状态冲突 |
| 门禁 | ✅ 基本覆盖 | 徒步跨图有 _instance_gate_block（任务/钥匙/首通三档）；传送走 PORTALS（无副本方碑）天然拦截；漏网仅 GM 传送（白名单） |
| 显示 | ✅ 统一 | 副本地图视图复用 _map_nav_body/_map_blocks |
| 大陆隔离 | ✅ 主闭环成立 | world_id 写入 6 点齐全，离开/失败/退队/自愈都写回 mainland |
| 大陆回收 | ⚠️ 三处缺失 | 30min 超时不清大陆、24h 过期不销毁、cleanup_stale_instances 无人调 |

## 三、P0/P1/P2/P3 完整清单（两轮合并去重）

### P0（玩家可触达真 bug）：2 个
1. **通关后调查点每日上限/已翻回报非 None 吞掉房间 POI**（instance.py:2965-2966 + 503-507）：
   达上限后『调查 篝火』先命中调查点"篝火余烬"（包含匹配 2954），返回"已达上限"被 505-507
   直接消费，本可调查的房间 POI（如"将熄的篝火"）被误锁。违反注释"仅点名称命中"的意图。
2. **investigated set 内存残留 → default=str 落库成字符串 → 恢复后字符集合 → 调查点重复刷奖**
   （instance.py:2968-2980 + worlds.py:138）：reward 为空提前 return 不落库 → 内存 st 残留 set →
   下次 _instance_save 经 default=str 变字符串 → 重启恢复 set(str) 拆成字符集合 → 重复发奖
   （受每日 3 次上限约束）。触发条件窄但真实可达。

### P1（双轨并存/半落地，暂不崩）：9 个
1. **battle.py `_inst_*` 假收编**（battle.py:1757-1927）：9 方法全 0 调用；v137 宣称"收编"实未落地；
   文档 RESEARCH_battle_unify.md:337-344 宣称架构已落地，实际是"瞬态 Battle 结算器 + 命令层调度"。
2. **老 CTB 时钟三处口径不一**：_instance_act 行动后走引擎绝对时钟（b.p_ct），但播种(905/942)与
   调度比较(me<mp 相对)仍是 v121 相对时钟，join_battle 播种(180-190)混用 → 时钟混用隐患。
3. **副本移动解析三段重复**（见上表）：一次移动解析 2 遍 + 队长校验 2 遍；_instance_dungeon_move
   的 target 参数是死参数（三处调用传参全未用）。
4. **钥匙判定双实现**（world.py:1254-1263 vs instance.py:1795-1802）：字符串级复制，改一处漏改另一处
   即门禁/开本分裂；且门禁不扣钥匙 vs 开本扣 1 行为不对称。
5. **遇怪/池消费双实现**（world.py:1724-1747 vs instance.py:740-772）：rooms 池 pop 逻辑各写一份，
   池语义改动需双处同步；consume_monster/consume_poi_loot（instance.py:1636/1655）是死代码没接线。
6. **30min 通关超时不清大陆/不回写 world_id**（instance.py:253-265）：队友 world_id 悬空 + 大陆延迟销毁。
7. **24h 过期只打标不清大陆**（battle_state.py:85-98 + instance.py:1111-1128）：弃坑副本 inst:<uuid>
   永久驻留（内存 + event_state 键 + 玩家 world_id 三重泄漏）。
8. **cleanup_stale_instances 无调用方**（worlds.py:169-183）：大陆实例只增不删。
9. **副本内 4 处裸 MAP_BY_ID 查询**（instance.py:369/521/730/1313）：读全局静态图而非大陆克隆，
   当前同源数据一致不崩，但违背 resolve_map 唯一入口契约，未来克隆图动态化即错位。

### P2（死代码/维护负担）：8 个
1. battle.py `_inst_next_actor`/`_inst_enemy_phase`/`_inst_auto_defend`/`_inst_reset_cts` 死代码（无调用方）。
2. battle.py:254-277 instance 构造分支依赖 self._st/self._active_keys，但 from_state 从不传 st → 断链
   （靠 instance.py:2102-2132 显式传参救命）——_inst_* 无法工作的机制性根因。
3. consume_monster/consume_poi_loot（instance.py:1636/1655）死代码（零调用方）。
4. _stage_virtual_map（instance.py:1272）+ 旧 stages 路径（778-819/540-552）仅无 rooms 老存档可达，
   22 本全带 rooms，实际不可达（兼容层）。
5. worlds.py 的 update_instance_world/get_instance_st/list_instance_worlds/resolve_map_for 导出但 0 消费。
6. instance.py:1539-1544"无 stages 老副本直开 Boss"分支不可达（数据层 22 本全 stages）。
7. world.py:258/259/601/949/1104 硬下标 C.MAP_BY_ID[...]（非 .get）——601/949 有拦截安全，1104 无。
8. core/maps.py subarea_links/pois 查全局，大陆克隆 subareas 是死数据（无命令层消费）。

### P3（文档/实现不一致）：10 个
1. RESEARCH_battle_unify.md:337-344 宣称收编已落地（实际没有）。
2. COMBAT_ENRICH_v138.md:195 超时自动防御指向 _inst_auto_defend（实际是 _instance_auto_defend_player）。
3. CONTINENT_ISOLATION_v141.md:220-222 "通关→destroy→全员回 mainland"与实现不符（通关保留大陆属设计，
   超时/过期路径未按文档销毁）。
4. 同文档:222 "过期 24h 惰性回收"无对应实现。
5. 同文档:199-203 "Phase 2 热路径替换"未落地（Position 结构体导出后命令层 0 调用）。
6. battle.py:225 注释将 instance 列为已收编 btype（实际主循环不认识 instance）。
7. instance.py:46-48 文件头 docstring 是 v101 老回合描述，与现状不符。
8. world.py:1476-1478 注释"副本分支保留兼容"（实际 route 恒先命中，分支不可达）。
9. instance.py:1318 _map_nav_body qq_id 误传 group_id（副本无隐藏房间故无实害）。
10. instance_investigation.py:35 注释"不构成新产出"与房间 POI loot（宝箱 gold 50-200）口径不同源。

## 四、修复方案（按优先级，等鱼鱼拍板）

### 第一批：P0 必修（玩家可触达 bug）
1. **调查点误锁房间 POI**：_instance_investigate_cleared 达上限/已翻时返回 None（回落第②③层）+
   名称匹配优先级改为"房间 POI 精确名 > 调查点包含匹配"。
2. **investigated set 序列化**：instance.py:2968 初始化直接用 list；worlds.py:138 改显式 _json_ready
   清洗（复用 battle_state 的）；_restore_from_db 恢复后校验 str → literal_eval/重置空 list。

### 第二批：P1 收尾缺失（资源泄漏/闭环，低风险可修）
3. **30min 超时补 destroy + world_id 回写**：instance.py:254-265 补两行（与 instance_leave 同构）。
4. **24h 过期补 destroy**：instance.py:1126 清 battle 后补 destroy；battle_state.py:91-98 打标处也补
   （store 层兜底更稳）。
5. **cleanup_stale_instances 接线**：base.py _maint_gate 追加懒清理 + main.py 启动兜底 +
   worlds.py 补 event_state 键扫描（清 DB 残留）。

### 第三批：P1/P2 统一重构（中风险，需鱼鱼拍板）
6. **战斗引擎收口**（二选一）：
   - A. 删 battle.py `_inst_*` 死代码 + 文档改"瞬态结算器"口径（承认现状，消除冗余，低风险）
   - B. 真收编：instance.py 切到 battle.py `_inst_*`（v137 原计划，需改 _instance_act 主循环，高风险）
7. **移动解析抽公共函数**：resolve_target_sa(sas, links, cur_sa_id, dest, visible_ids, blocked_cb)，
   dungeon_move 与 move 同图分支共用；route 瘦身透传 dest；删死参数 target。
8. **钥匙判定抽公共函数**：_instance_key_entry + _instance_cleared_qq，门禁与开本共用。
9. **遇怪/池消费收口**：consume_monster/consume_poi_loot 接线（两处 pop 改调），概率保持 0.85。
10. **A 类 4 处裸查询**改 resolve_map_for。

### 第四批：P2 清理（顺手）
- 删 _inst_* 死方法（若选方案 A）/ 删 consume_* 死代码 / 删不可达分支 / world.py 硬下标改 .get /
  克隆 subareas 死数据标记。

## 五、待鱼鱼拍板
1. 战斗引擎：**删死代码（A）还是真收编（B）？** 建议 A（承认现状，低风险；B 是 v137 原计划但动核心，需测试护航）
2. 副本固定 0.85 遇怪：确认是设计（建议保留 + 注释说明）
3. 门禁不扣钥匙 vs 开本扣 1：确认是设计（建议文档言明）
4. P2 清理范围：全清还是只清高价值的？
