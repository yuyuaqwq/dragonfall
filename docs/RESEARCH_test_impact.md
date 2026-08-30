# 副本地图化重构：测试影响面分析与迁移方案

> 关联方案：`docs/INSTANCE_MAP_UNIFY_v137.md`（v137 副本彻底重构：副本地图化 + 战斗引擎统一）
> 本文档只做**影响面分析与迁移设计，不改任何代码**。数据截至 2026-08-29。

---

## 0. 结论速览

| 项 | 值 |
|---|---|
| 扫描范围 | `tests/` 全部 py（229+ 文件，实 284 项含 db/txt） |
| 直接涉及副本的测试 | **8 个**（任务给定清单全部命中） |
| 重构后必红的测试 | **7 个**（`test_commands_instance` / `test_instance_map` / `test_v104_instance_party_pet` / `test_v95_76` / `test_v95_77` / `test_v98_05` / `test_v101_27_clear_loot`） |
| 重构后仍绿但需复核 | 2 个（`test_v116_instance_key_free` / `smoke_v1342_baike_instance`，依赖开本/百科文案，需确认新模板保留关键词） |
| 受牵连的非副本测试 | **10+ 个**（命令矩阵 / 帮助 / 停服 gate / tips / 数据注册表 / 任务击杀目标 / 采集 / 探索进度 / 世界 Boss / 副本图门禁） |
| 新增断言建议 | 6 大项 18 条（见 §5） |
| 迁移顺序 | 先保底（纯数据/命令框架）→ 再行为（开本/移动/战斗）→ 最后新功能（加入战斗/资源池） |

---

## 1. 现状结构依赖全景（重构前必读）

### 1.1 副本数据的三源结构（将被合并）

| 数据源 | 现状内容 | 重构后去向 |
|---|---|---|
| `game/data/instances.py`（1911 行，22 副本） | `stages`（层：name/monsters/elite/boss）+ boss 6 元组 + hp_mult/atk_mult/mech/gold/exp/materials/key_item/min_players/max_players | **`stages` 字段标记废弃**（改从 SUBAREAS 读）；Boss/掉落/缩放/钥匙/人数保留 |
| `game/data/instance_stage_maps.py`（678 行） | `INSTANCE_STAGE_MAPS`（每层 desc/pois/secret/npcs）+ `INSTANCE_STAGE_NPCS`（6 个层内 NPC，装配进 HIDDEN_NPCS） | **POI/desc/secret 迁移到 SUBAREAS 对应子区域**；NPC 随子区域 npcs 字段走 |
| `game/data/subareas.py`（11182 行） | 世界地图子区域；**副本图目前每张只有 1 个"入口"子区域**（如 `goblin_camp_1`，monsters 有怪、boss 有定义、funcs=["instance"]） | **副本图重写为 2-4 个贴合主题的子区域 + LINKS 网状连通（无出口）** |

### 1.2 装配链（`game/data/_assembly.py`，252 行）

```
SUBAREAS + EXTRA_SUBAREAS(3 块 mesh)          → SUBAREAS（合并）
SUBAREA_LINKS(3 块 mesh)                      → SUBAREA_LINKS_INDEX
MESH_POI_MOUNTS(3 块 mesh) + SUBAREA_POIS     → SUBAREA_POIS（并集）
MAPS 注入 subareas → SUBAREA_BY_MAP / SUBAREA_INDEX → 重建 MAP_BY_ID
INSTANCE_STAGE_MAPS merge 进 INSTANCES[..]["stages"]（v87.2 装配）
INSTANCE_STAGE_NPCS → HIDDEN_NPCS（层内 NPC 可『找』）
INSTANCES stages 的 monsters/elite/boss → _INDEXES["monsters"]（v104 M24）
```

重构后：INSTANCE_STAGE_MAPS 合并逻辑**删除**，改为 SUBAREAS 直接带 desc/pois；怪物索引收集源从 `instances.py stages` 改为 `SUBAREAS`（monsters/elite/boss 槽），`_collect_monster_entries` 的收集源需跟着换（影响 `_INDEXES["monsters"]`，百科/图鉴/`test_v98_04_battle_registry` 直接踩）。

### 1.3 运行时状态结构（`st`，`_instance_build_state` 产出，instance.py:945）

```
type=instance / inst_id / leader / members / alive / players{}
boss / enemy / enemies[]（v2 敌方阵列）/ round / turn / turn_time / threat{}
mode: "map"（地图模式）| "battle"（战斗中）
stage_idx / stage_pending[] / stage_cleared / inst_stages[]（= stages 深拷贝进状态）
stage_pois{} / stage_secret_found / stage_secret_cleared / poi_unlocks{}
skip_elite_next / skip_wave_next / boss_buff_next
p_buffs / p_hot / p_food_effects / e_buffs / p_defending / mech_stacks
round_acted[] / dot_pending / contribution / over
```

**重构后这些 key 全部变**：`inst_stages`→`rooms`（SUBAREAS 房间）、`stage_idx`→`cur_room`、`stage_pending`→`rooms[room]["monsters_left"]`、`stage_pois`→`rooms[room]["pois_left"]`、`mode` 语义并入 `dungeon` 修饰符（地图模式=常态，无独立 mode），战斗状态由 BT.Battle `btype="instance"` 承载。

### 1.4 命令层现状（将被改造的入口）

| 命令 | handler | 现状 | 重构后 |
|---|---|---|---|
| 『副本 <名>』开本 | `instance_cmd` → `_instance_start` → `_instance_build_state` | 校验+建 state+锁全队 | 校验+生成 dungeon_instance+落点第 1 子区域+锁全队（同野外到达模板） |
| 『深入』 | `instance_advance` | 层推进 | **废弃**（改『移动』） |
| 『探索』 | `combat.explore` → `_instance_explore`（mode=map 分支） | 副本内探索遇怪/陷阱/无事 | 走 world 探索统一路径 + discovery_agro |
| 『调查』 | `instance_investigate` | 层 POI 交互 | 并入 world `交互/调查` POI 管线（POI 挂子区域） |
| 『撤退』 | `instance_retreat` | 保留进度 | 保留（副本专属） |
| 『离开副本』 | `instance_leave` | 清 battle | 保留（清 dungeon_instance） |
| 『副本地图』 | `instance_map_view_cmd` | 层小地图 | 并入『地图』（副本=地图，无出口） |
| 『移动』 | `world.move` | 副本图门禁（_instance_gate_block） | 副本内移动=队长带队，discovery_agro 遇怪，无出口 |

### 1.5 战斗现状：副本自写 ~2500 行状态机

`game/commands/instance.py`（2518 行）自写 CTB 轮流回合：`_instance_act`（1986）/`_instance_enemy_ct_acts`（2567）/`_instance_next_actor`（2527）/`_instance_apply_enemy_act_ct`（2541，单怪临时 `BT.Battle("instance", unit, enemies=[unit])` 仅借 `_enemy_stats` 算 buffed spd）/`_instance_kill_reward`/`_instance_victory`/`_instance_defeat`。`game/battle.py` 的 `Battle.__init__` 支持 `btype="instance"`（225 行，瞬态 Battle 结算器：enemies/allies 引用直传 + allies ct 广播，**不含调度**——调度/敌方阶段/超时/换层全在命令层 instance.py）。

重构后：~~BT.Battle 正式支持 `btype="instance"`，多人 CTB 调度收编进 battle.py，instance.py 瘦身只留开本/结算/钥匙/人数~~——**2026-08-30 审计更正：收编未落地且已废弃**。现状即最终架构：**瞬态 Battle 结算器（player_turn）+ 命令层 CTB 调度（instance.py `_instance_*` 前缀方法）**；battle.py 不再有 `_inst_*` 调度方法。

---

## 2. 直接副本测试逐一分析（8 个）

### 2.1 `test_commands_instance.py`（689 行，v49 组队副本主测试）——**必红**

| 用例段 | 测什么 | 依赖现状 | 重构后状态 |
|---|---|---|---|
| 副本列表 | `instance_cmd("副本")` 显示"旧王陵" | `_instance_list`（读取 INSTANCES） | 列表保留（从 INSTANCES 读，Boss 行在），**大概率仍绿**；但若列表模板改"副本=地图入口"需复核 |
| 未组队开本拦截 | 提示"组队" | `_instance_start` 人数校验 | 校验保留，绿 |
| 组队开本（地图模式） | 副本开启 + mode=map + boss=None + stage_pending≥2 | `_instance_build_state` 的 mode/stage_pending/inst_stages | **红**：`stage_pending`→`rooms[room].monsters_left`；`inst_stages` 没了；`mode` 并入 dungeon |
| 状态存队长名下 | battle.type==instance | 存 battle_state 表 | 若改存 dungeon_instance 表（独立存档），`db.get_battle` 可能拿不到 → **红** |
| 成员 2 人/行动序按速度 | st["members"] 按 spd 降序 | `_instance_start` 排序 | 保留（BT 收编后由引擎播种），绿 |
| 探索触发第一场战斗 | `enter_combat` 循环『探索』直到 db.get_battle | `combat.explore` 的 mode=map 分支 → `_instance_explore` | **红**：探索走 world 统一路径 + discovery_agro，遇怪判定从"pending.pop"变"子区域怪物池消耗"；`db.get_battle` 若被 dungeon_instance 替代则直接崩 |
| 轮流回合 / CTB 判定 | `st["turn"]`、`_next_player_key` | `st["turn"]/ct/alive` | **红**：战斗状态在 BT.Battle 实例内，st 结构变化（turn 可能不再是成员索引） |
| 超时自动防御 | 改 `turn_time`/ct 触发自动防御 | `_instance_act` 超时分支 | **红**：收编进 BT 后触发路径/字段变 |
| 分层推进通关 | 打怪→肃清→『深入』→层 2→『深入』→层 3 Boss | `instance_advance` 深入 + `stage_idx` | **红**：『深入』废弃 → 改『移动』到 Boss 房；`stage_idx` 没了 |
| Boss 血量 2.5 倍 | `hp_mult + 0.65×(2-min)` | `_enter_stage_combat` 缩放 | 公式保留（数据层），但入口从 `_enter_stage_combat` 移到 BT instance 分支 → 断言写法要改 |
| 通关结算 / 首通成就 | "通关"文案 + inst_clear_* 成就 + cleared 状态 | `_instance_victory` | 结算保留（v137 验收 8），文案模板若变需复核；`cleared`/loot_pile 字段若挪 dungeon_instance 会红 |
| 3 人队 / 团队技能广播 | p_buffs 广播 | `_apply_team_effect` | 收编 BT 后广播逻辑在引擎内，st 字段仍保留则绿；需验证 |
| 全灭失败 | 全灭→回城 HP0 | `_instance_defeat` | 结算保留，绿（回城落点模板若改需复核） |
| 人数配置 / 单人副本 | 单人免组队 / Boss 血量 1.6 倍 | min_players/max_players | 保留，绿 |
| 4 人副本拦截/开本 | 深海龙宫 | 人数校验 | 保留，绿 |
| 入场钥匙 | 军旗碎片拦截/消耗 | key_item 校验 | 保留，绿 |
| 首通免钥匙 | 首通后免钥匙开本 | inst_clear_* 成就 | 保留，绿 |

> **2026-08-30 设计口径注（钥匙）**：**徒步进副本图（门禁）不扣钥匙、『副本 <名>』开本才扣 1 个，属设计**——门禁 `_instance_gate_block`（world.py）只做任务/钥匙/首通三档放行校验不消耗（任务与钥匙两路放行）；开本 `_instance_start`（instance.py ~1795-1815）才消耗钥匙（首通前，已通关免钥匙）。判定逻辑两处同源（字符串级复制），修复将抽公共函数（core/instance_gate.py）。

**结论**：本文件是重灾区——地图模式开本断言、探索进战、深入推进、通关状态、战斗回合五处全踩新结构。**建议重写为主**：开本断言改为"落第 1 子区域+可前往列表"，推进改『移动』，战斗断言改为对 BT instance 分支的等价性断言。

### 2.2 `test_instance_map.py`（299 行，v87.2 副本地图化）——**必红（部分转型为"新结构验收"）**

| 用例段 | 依赖现状 | 重构后状态 |
|---|---|---|
| 数据完整性：66 层 desc/POI/NPC/secret | 遍历 `INSTANCES[..]["stages"]`（装配后） | **红**：stages 废弃 → 改遍历 SUBAREAS[inst_id] 房间；66 层总数会变（每副本 2-4 房间，总数≈22×3≈66 需重标定） |
| 6 个层内 NPC 注册 | `INSTANCE_STAGE_NPCS` → HIDDEN_NPCS | 迁移后仍在（NPC 挂子区域 npcs），绿 |
| 哥布林营地开本 map 模式 | mode=map/boss=None/stage_pending==2 | **红**：字段换 rooms/monsters_left |
| 调查宝箱/篝火 | `instance_investigate` + `stage_pois` | **红**：调查并入 world POI 管线；`stage_pois["0"]` → rooms[room].pois_left |
| 副本地图指令 | `instance_map_view_cmd` | **红**：并入『地图』（副本=地图） |
| 探索遇怪 | `explore` → `_instance_explore` pending.pop | **红**：走 discovery_agro 怪物池 |
| 撤退保留进度 | `instance_retreat` + retreated 标记 | 保留（副本专属），绿 |
| 海蚀洞窟隐藏房间 | secret cond=corpse_1 → stage_secret_found → 珠宝盒 | **红**：secret/cond 迁到子区域后字段/路径变（但 POI 数据本身迁移保留，可改断言） |
| 石碑线索/机关数据级 | `INSTANCES[..]["stages"][i]["pois"]` | **红**：改读 SUBAREAS[inst_id][i]["pois"] |
| 层内 NPC 查找 | `_stage_npcs` + 『找 试炼老兵』 | **红**：`_stage_npcs` 基于 inst_stages → 改子区域 npcs 字段 |

**结论**：本文件一半是数据完整性断言（可直接改为对 SUBAREAS 房间的验收），一半是命令行为断言（全换）。**迁移后它应改造成"副本=地图新结构验收测试"**——这正是新增断言的主战场（§5）。

### 2.3 `test_v104_instance_party_pet.py`（309 行）——**必红**

| 用例 | 依赖现状 | 重构后状态 |
|---|---|---|
| 退队白拿收益修复 | open_instance（组队+开本+探索进战）→ jump_to_final_boss（直接改 st: stage_idx/inst_stages/stage_pending/mode/boss/enemies） | **红**：`jump_to_final_boss` 直接操作 `st["inst_stages"]`、`stage_idx`、`stage_pending`——字段全没。改法：构造 dungeon_instance 状态直接落到 Boss 房，或打新命令快速推进 |
| 退队者不被 Boss 打 | st["threat"]/players/alive | 战斗收编 BT 后 threat 语义保留（BT 引擎内），需改断言入口 |
| 全灭不误杀退队者 | `_instance_defeat` 回城 | 保留，绿 |
| retreated 恢复校验 | 撤退→恢复→退队→恢复被拒 | 保留（撤退=副本专属），但"恢复"走开本路径需复核 `_instance_start` 的 retreated 分支 |
| 超时文案 60 秒 | `INSTANCE_TIMEOUT == 60` + 源码 grep "超时 60 秒" | **红（源码 grep 类）**：instance.py 瘦身后模板/常量位置可能挪 BT；grep 路径可能失效 |
| 副本不携带宠物 | open_instance + 战斗不扣饱食度 | 战斗收编 BT 后"不传 pet"约定需保留，断言可复用（绿的前提是设计不变） |
| 宠物面板/蛋定价 | 与副本无关 | 绿 |

**结论**：核心红点是 `jump_to_final_boss`（手拼 st 结构）和 open_instance（探索进战）。迁移方案：给一个 `_dungeon_jump(st, room)` helper 直落 Boss 房，其余用例逻辑几乎不动。

### 2.4 `test_v95_76_instance_hp_sync.py`（115 行）——**必红**

| 用例 | 依赖现状 | 重构后状态 |
|---|---|---|
| 开本+探索进战 | 旧王陵 2 人队 + enter_combat | 红（同上探索路径） |
| 行动后 DB hp 同步 | `st["players"][leader]` 快照 vs DB | 战斗收编 BT 后快照仍存在（BT instance 分支持有 players），但 `_sync_players_db` 调用点从 `_instance_act` 移到 BT 结算 → **断言入口变**，需改走新命令触发 |
| 层肃清后治疗判定 | st["boss"]=None + mode=map + 使用药水 | **红**：boss=None 表达换成"该房间怪物已清空"；地图模式=常态 |

**结论**：语义（DB 与快照同步）是重构后**必须保留**的行为（v137 验收隐含），测试改为走新命令路径即可，红在"路径"不在"语义"。

### 2.5 `test_v95_77_instance_kill_reward.py`（96 行）——**必红**

| 用例 | 依赖现状 | 重构后状态 |
|---|---|---|
| 切怪分支击杀奖励 | 开本+探索进战 → attack 杀第 1 只 → "经验 +"/"拾取材料" | 红：遇怪改 discovery_agro 怪物池；`stage_pending` 切怪逻辑换 rooms.monsters_left 消耗；击杀奖励链路保留（`_instance_kill_reward` → BT 击杀回调） |
| 层肃清分支 | 杀第 2 只 → "肃清" | 红：肃清表达=房间怪物清空 |
| 经验落库/击杀统计 | stats.kills 递增 | 保留，绿 |

**结论**：行为语义（副本击杀给经验/材料/统计）保留，迁移=换触发路径。

### 2.6 `test_v98_05_instance_state_persist.py`（108 行）——**必红**

| 用例 | 依赖现状 | 重构后状态 |
|---|---|---|
| 单人开本 | 哥布林营地单开 + st["type"]=="instance" | 红：存档若迁 dungeon_instance 表则 `db.get_battle` 拿不到 |
| enemies 阵列持久化 | 注入 e_test_minion 到 st["enemies"] → attack → 援军被攻击/round 写回 | **红**：`st["enemies"]` 归 BT 引擎管理（btype=instance 内部阵列）；测试注入点从 st 变成 BT 实例字段或 from_state 构造 |
| resources 持久化 | st["resources"]["i1"]["energy"] 跨回合累积 | 红：resources 在 BT instance 分支内持久化（现状已从 st 透传进 from_state），断言对象变 |

**结论**：本测试验证的是"BT 引擎内状态持久化"——**重构后它应改为直接对 BT.Battle instance 分支做单测**（不再走完整开本），反而更聚焦。属于"最后迁移、顺带转型"的一批。

### 2.7 `test_v116_instance_key_free.py`（78 行）——**大概率绿，需复核**

| 用例 | 依赖现状 | 重构后状态 |
|---|---|---|
| 无钥匙被封印拦截 | "军旗碎片"+"封印"文案 + 未开本 | 开本校验保留 → 绿（若文案模板不变） |
| 有钥匙消耗 | 开本成功+钥匙扣减+无"免钥匙" | 绿 |
| 已通关免钥匙 | inst_clear_* 成就 → 免钥匙文案 | 绿（成就体系不动） |

**结论**：全部走开本校验路径，与 stages/战斗无关。**唯一风险**：开本成功文案从"副本开启"模板变为"落第 1 子区域"模板，本文件只断言"副本开启 in out"→ 若新模板保留"副本开启"字样则绿。**建议保留关键词"副本开启"**（v137 验收 1 的模板可含）。

### 2.8 `smoke_v1342_baike_instance.py`（61 行）——**大概率绿，需复核**

| 用例 | 依赖现状 | 重构后状态 |
|---|---|---|
| 百科 哥布林营地 | Lv.15+ / 1-2 人 / 无需钥匙 / 开启挑战 | 百科从 INSTANCES 构建入场条件（等级/人数/钥匙）——数据保留 → 绿 |
| 百科 旧王陵 | 入场需要『王陵钥匙』 | 绿 |

**结论**：百科的副本入口信息源是 INSTANCES 顶层字段（lv/min_players/key_item），与 stages 无关 → 绿。**唯一风险**：`game/core/maps.py _build_ency` 从 SUBAREAS 构建怪物百科——副本怪若从 stages 迁到 SUBAREAS，百科"副本怪在哪"条目会变（见 §4.4），但本文件不查怪物 → 绿。

---

## 3. 受牵连的非副本测试（10+ 个）

### 3.1 命令框架/静态类（改 instance.py/world.py 后必查）

| 测试 | 牵连点 | 影响 |
|---|---|---|
| `test_v87_command_matrix.py` | 注册表互斥矩阵，代表输入含 `instance_cmd:"副本"` `instance_advance:"深入"` `instance_map_view_cmd:"副本地图"` `instance_investigate:"调查 房间"` `instance_retreat:"撤退"` `instance_leave:"离开副本"` | **红**：『深入』handler 若删除，矩阵缺键崩；『副本地图』并入『地图』后代表输入冲突（"副本地图"与"地图"前缀）需改矩阵 |
| `test_v104_commands_system.py` | ①『副本地图』双 handler 单回复（期望命中恰 1 个 handler=instance_map_view_cmd）；⑤停服 gate 含"离开副本"；⑦帮助补全含"副本地图" | **红**：副本地图 handler 若并入 map_view，期望命中集变；帮助文案若改"副本=地图"需同步 |
| `test_v127_tips.py` | AST 扫描 `instance.py _instance_map_view` 多 tip 白名单 | **红**：`_instance_map_view` 若删除/改名，白名单条目失效（AST 扫描不崩但检查"每面板 1 条"的豁免集引用旧函数名） |
| `test_v1252_audit_closure.py` | 扫描 `INSTANCE_STAGE_MAPS` 的 POI type（chest/campfire/...）→ POI_EFFECTS 注册表；`INSTANCES` mech 全合法 | **红**：INSTANCE_STAGE_MAPS 文件若删除 → import 崩；需改为扫描 SUBAREAS 内联 POI |
| `test_v98_04_battle_registry.py` | 源码 grep `instances.py`/`instance_stage_maps.py` 的 mech/cond → BOSS_MECHS/COND_LABELS 全覆盖 | **红**：文件若删/瘦身，grep 源没了；需改为 grep SUBAREAS + instances.py 保留字段 |
| `test_v83_boss_mech.py` | `C.INSTANCES` 22 副本 mech 全合法 + 组合机制数≥10 | 绿（INSTANCES 保留 mech） |
| `test_v116_boss_trigger_phase.py` | `C.INSTANCES["inst_abyss_gate"]["phases"]` | 绿（顶层字段保留） |

### 3.2 世界/地图/探索类（SUBAREAS 副本重写后）

| 测试 | 牵连点 | 影响 |
|---|---|---|
| `test_v87_14_spatial_links.py` | oak_plain 网状拓扑 + 镇郊进出 + 进城落镇郊 | **大概率绿**：只动 oak_plain/oak_town，副本图不参与；唯一风险是副本图 SUBAREAS 重写后 `MAP_CONNECTIONS` 若被改 |
| `test_v87_13_map_display.py` | oak_town 地图面板/移动 | 绿 |
| `test_v104_explore_map.py` | ⑦ deep_tunnel 商店、⑧ HIDDEN_MAP_UNLOCK、⑨ 回城卷轴落 subareas[0]、⑩ 战败回就近城镇 | ⑧：HIDDEN_MAP_UNLOCK 若含副本图目标（ash_temple 等）且副本图重写 → 检查目标图仍在 MAPS（绿）；⑨⑩ 落点 `subareas[0]` 语义若副本图参与 BFS（回城卷轴在副本内用？）需复核——现状副本内禁道具？**低风险，需复核** |
| `test_v97_02_gather_map_bind.py` | `_gather_roll(15,1,"goblin_camp")` 副本地图等级回退 | **绿**：`_gather_roll` 按地图 id/lv 回退，副本图 SUBAREAS 重写不改变地图 lv；但采集在副本内是否允许需设计确认（副本=封闭地图，v137 未提采集） |
| `test_v1307_zone_risk.py` | `C.MAP_BY_ID["goblin_camp"]` 副本图 + `_travel_ambush` 副本分支（diff≥5 仍 0.30）+ 副本图探索 | **红**：`_travel_ambush` 对副本图走"副本分支"（有主线目标才撞怪）——重构后副本内移动撞怪概率 = discovery_agro(0.85)，不再是 0.30 不撞 → 断言"副本无群上下文跳过(不撞)"直接失效 |
| `test_commands_world.py` | ⑤ 垂钓等待中"副本"命令被互斥拦 | 绿（互斥装饰器不变） |
| `test_commands_feedback_features.py` | ⑥ 副本仇恨：开本旧王陵+探索进战+threat 断言 | **红**：开本/探索路径全换；threat 语义保留（BT 引擎），需改触发路径 |
| `test_v104_npc_dialogue.py` | `quest_done:inst_secret_crypt` 兼容 battle_state cleared 标记 | **红（若存档表变）**：`db.save_battle(GID,QID,{"type":"instance","inst_id":"inst_secret_crypt","cleared":True})`——若 cleared 标记迁 dungeon_instance 表，`unlock_met` 的兼容读取要同步改；**建议保留 battle_state 兼容读** |
| `test_v95_75_item_use_fix.py` | `db.save_battle` 造 type=instance 状态测道具拦截/层肃清后使用 | **红（若 battle_state 结构变）**：手拼 `{"type":"instance","round":0,"boss":mon}`——boss 键若不再是一等公民（改 BT 阵列），手拼状态失效；需按新结构造状态 |
| `test_dot_refactor.py` | ⑨ 副本 dot_pending + poison_all 共享（手拼 st 测 `st["boss"]["debuffs"]`） | **红**：`poison_all` 逻辑收编 BT 后 `st["boss"]["debuffs"]` 位置变（引擎内），手拼 st 断言失效 |
| `test_v99_05_achievement_conds.py` | `inst_id` cond / `inst_clears` stats | 绿（纯 cond 函数单测） |
| `test_legacy_schema_migration.py` | stats 补列含 inst_clears | 绿 |

### 3.3 任务系统（kill 目标挂副本）

扫描 `game/data/quests.py`：`"kill"` 目标与副本怪（instances stages 怪名）交集 6 个：**云中圣者·奥拉、古王·奥德里克、恶魔祭司·赫尔加、海盗王·独眼杰克、海神祭司·澜歌、蚀夜(真相形态)**——对应主线 q3_3/q6_2/q12_* 等。

| 牵连点 | 影响 |
|---|---|
| 主线击杀任务（q3_3 海盗王、q6_2 古王等） | 副本怪迁 SUBAREAS 后，怪 id/名不变 → combat 按怪名计数逻辑不变；**但遇怪入口从 `_instance_explore` 换 discovery_agro，主线单人推进需验证**（v105 M19 已放行"主线击杀目标在副本图时探索可遇怪"——重构后副本=地图，探索/移动都走 world 统一路径，此豁免逻辑要跟着平移） |
| `combat.py:127` `_main_kill_target_on_map` 判断 | 副本图探索放行主线目标——重构后副本内探索=常态，该分支语义变化，需重验 |
| `test_v107_unlock_quests.py` / `test_v124_new_quest_monsters.py` | 任务 NPC/怪物挂载 SUBAREAS——**若副本任务怪（潮汐祭司 quest=s_tide_shells 等）迁进副本 SUBAREAS 房间，这两测试的挂载断言若涉及副本图要复核**（当前未涉及副本图，绿） |

---

## 4. 重构后"会红"的根因归类

| 根因 | 影响的测试 | 修复方向 |
|---|---|---|
| ① `st["stages"]/inst_stages/stage_idx/stage_pending/stage_pois` 字段消失 | test_commands_instance、test_instance_map、v104_party_pet、v98_05、v101_27_clear_loot、v95_77、v95_76 | 断言改读 `dungeon_instance.rooms[cur_room]` |
| ② 『深入』命令废弃、副本内走『移动』 | test_commands_instance、test_instance_map | 推进断言改『移动 <房间>』+ 队长带队 |
| ③ 探索进战从 `_instance_explore`(pending.pop) 换 discovery_agro 怪物池 | test_commands_instance、test_instance_map、v95_76、v95_77、v104_party_pet、feedback_features | 遇怪断言改"子区域怪物池消耗 + 战斗合并" |
| ④ 战斗状态收编 BT.Battle btype=instance | v98_05、v95_76、v95_77、ctb_audit、dot_refactor、v95_75 | 战斗断言改对 BT 实例/from_state 直接单测 |
| ⑤ 存档表 battle_state → dungeon_instance（若独立表） | v98_05、v104_npc_dialogue、v95_75、test_commands_instance("get_battle") | 兼容层：get_battle 保留对 dungeon_instance 的读取；或测试改查新表 |
| ⑥ INSTANCE_STAGE_MAPS / stages 源文件删除 | test_instance_map(数据段)、test_v1252_audit_closure、test_v98_04_battle_registry | 扫描源改 SUBAREAS 内联 POI/怪 |
| ⑦ 命令注册表/帮助/tips 静态断言 | v87_command_matrix、v104_commands_system、v127_tips | 同步更新代表输入与白名单 |
| ⑧ 副本图移动撞怪概率变 0.85 | test_v1307_zone_risk | 断言改 discovery_agro |

---

## 5. 新增断言清单（v137 验收 → 测试断言）

### 5.1 副本=地图（开本进第 1 子区域）
1. `『副本 哥布林营地』`开本 → 玩家 `cur_map=goblin_camp`、`cur_subarea=goblin_camp_1`（第 1 子区域，非模板名如"入口栅栏"）
2. 开本输出含该子区域 desc + 可前往列表（与野外到达模板同源：`_subarea_arrive` 区块）
3. 副本图 `dungeon.no_exit=True` → 『地图』不显示野外连接/传送
4. `SUBAREAS[inst_id]` 房间数 = 设计值（如哥布林 3 房），房间名全部贴合主题（非"第 1 层/第 2 层"模板）
5. `SUBAREA_LINKS_INDEX[inst_id]` 拓扑：入口→中间房→Boss 房可达，且无任何房间连野外

### 5.2 数量上限（打完不刷）
6. 开本时 `dungeon_instance.rooms[room].monsters_left` = 设计上限（如 2-4）
7. 清空某房间怪物后重复『探索』该房间 → 不再遇怪（"这里没有敌人"），怪物计数不增
8. 全副本怪物总数上限：打完所有房间怪物 → 无可刷（不因反复进出房间刷新）

### 5.3 资源池（总量固定）
9. `resources_pool` 开本创建，gold/mats 总量固定
10. 宝箱/补给/遗骸 loot 从资源池扣减：取完 `pois_left` 清空，重复『调查』→ "已经被处理过了"
11. 资源池耗尽后同房间再次探索 → 无新宝箱（不无限刷）

### 5.4 加入战斗（合并同场）
12. 玩家 A 在副本房间遇怪进战（battle 带 inst_id+room）→ 队友 B 输入『加入战斗』→ B 并入同一场（allies 追加，B 在 members/alive）
13. 加入后 CTB 行动序正确（B ct 播种 -spd，与现存单位同规则）
14. 战斗中 B 阵亡 → 不影响 A 继续；全灭判定覆盖合并后全员

### 5.5 队长带队
15. 副本内队员『移动』→ 提示"等待队长带队"，位置不变
16. 队长『移动 <房间>』→ 全队 `cur_subarea` 同步更新，全队收到到达文案
17. 队长移动触发遇怪 → 全队合并进同一场战斗（队长触发，全员参战）

### 5.6 统一引擎战斗
18. 副本战斗 `BT.Battle(btype="instance")`：CTB 行动序/仇恨/技能/超时自动防御/人数缩放全生效（可对 BT 实例直测）
19. 等价性：同一队伍配置下，副本战斗输出与旧 `_instance_act` 行为等价（新旧对比跑分）

### 5.7 主线/探索联动
20. 副本内探索/移动触发主线击杀目标（q3_3 海盗王等）→ 任务计数正常（`_main_kill_target_on_map` 豁免平移后验证）
21. 副本子区域 visited_subareas 记录（进副本房间记录探索进度，key 兼容旧 `goblin_camp_1`）

---

## 6. 分批迁移建议

### 第 1 批：保底（改数据/静态层后立刻跑，不依赖新玩法）
| 测试 | 动作 | 理由 |
|---|---|---|
| `smoke_v1342_baike_instance.py` | 只复核（百科入口条件数据保留） | 百科数据源不变 |
| `test_v116_instance_key_free.py` | 只复核（开本模板保留"副本开启"关键词） | 开本校验路径不变 |
| `test_v1252_audit_closure.py` | 改扫描源：INSTANCE_STAGE_MAPS → SUBAREAS 内联 POI | 数据层 Phase 1 完成即修 |
| `test_v98_04_battle_registry.py` | 改 grep 源：instances.py stages → SUBAREAS + instances.py 保留字段 | 同上 |
| `test_v83_boss_mech.py` / `test_v116_boss_trigger_phase.py` | 只复核（INSTANCES 顶层字段保留） | 数据保留 |
| `test_v87_command_matrix.py` / `test_v104_commands_system.py` / `test_v127_tips.py` | 同步命令注册表/代表输入/白名单（『深入』删除、『副本地图』并入『地图』） | 命令层瘦身即修 |
| `test_v87_14_spatial_links.py` / `test_v87_13_map_display.py` / `_smoke_map_newline.py` | 只复核（不涉副本图） | 世界地图不动 |

### 第 2 批：行为主路径（副本=地图玩法落地后）
| 测试 | 动作 |
|---|---|
| `test_commands_instance.py` | **重写**：开本=落第 1 子区域断言、推进=『移动』、战斗=BT instance 等价断言；人数/钥匙/成就/全灭/团队技能用例保留逻辑改入口 |
| `test_instance_map.py` | **转型为"副本=地图新结构验收"**：数据段改遍历 SUBAREAS；POI/secret/NPC 改子区域断言；探索/调查/移动改新命令 |
| `test_v104_instance_party_pet.py` | 改 `jump_to_final_boss` → `_dungeon_jump`（直落 Boss 房）；open_instance 改新开本+新遇怪 |
| `test_v95_76_instance_hp_sync.py` | 换触发路径（新命令进战/肃清），语义断言保留 |
| `test_v95_77_instance_kill_reward.py` | 换触发路径，击杀奖励断言保留 |
| `test_v101_27_clear_loot.py` | 手拼 st → 按 dungeon_instance 结构造状态；调查/副本地图改新入口 |
| `test_commands_feedback_features.py` | 副本仇恨用例换开本/遇怪路径 |
| `test_v1307_zone_risk.py` | 副本分支断言改 discovery_agro（0.85） |
| `test_v104_npc_dialogue.py` / `test_v95_75_item_use_fix.py` / `test_dot_refactor.py` | 手拼 type=instance 状态 → 按新结构造；battle_state 兼容读建议保留 |

### 第 3 批：新功能（加入战斗/资源池/队长带队落地后）
| 测试 | 动作 |
|---|---|
| `test_v98_05_instance_state_persist.py` | **转型为 BT.Battle(btype="instance") 直接单测**：enemies/round/resources 持久化断言对象改为引擎实例 |
| `test_ctb_audit.py` | ⑥⑦⑧ 副本 ct 断言：`_instance_apply_enemy_act_ct`/`_instance_reset_player_cts` 收编 BT 后改对引擎方法直测 |
| 新增 `test_dungeon_map.py` | §5.1 副本=地图断言（开本落点/无出口/房间拓扑） |
| 新增 `test_dungeon_limit.py` | §5.2/5.3 数量上限+资源池 |
| 新增 `test_join_battle.py` | §5.4 加入战斗 |
| 新增 `test_leader_move.py` | §5.5 队长带队 |
| 新增 `test_instance_bt_equiv.py` | §5.6 等价性 + 引擎直测 |

### 关键保留原则（让迁移成本最小化）
1. **开本模板保留"副本开启"字样**（test_v116 依赖），同时新增"已进入第 1 子区域"信息
2. **battle_state 兼容读保留**：`get_battle` 对 dungeon_instance 状态兼容返回（test_v104_npc_dialogue / v95_75 / v98_05 手拼状态不炸）
3. **怪 id/名不变**（SUBAREAS 怪物槽直接复用 instances stages 的 m_*/e_*/b_* 定义）→ 任务击杀/百科/图鉴索引全绿
4. **副本专属指令保留**：『撤退』『离开副本』（v137 明确保留）→ retreated 恢复用例逻辑不动
5. **探索进度 key 兼容**：副本房间 visited_subareas 沿用旧子区域 id（goblin_camp_1 保留）→ 探索进度/见闻不受影响

---

## 7. 风险备注

- `test_numeric_toolkit.py` 用 `inst_goblin_camp`/`inst_old_king_tomb` 的 `rounds` 数值锚点（boss_hp 按 hp_mult 计算）——**数据层保留 hp_mult/Boss 定义则绿**；若重构改缩放公式需重标定。
- 副本图门禁 `_instance_gate_block`（world.py:1189）：副本=封闭地图后，徒步进副本图的行为语义变化——`test_commands_world.py` 未直接测，但玩家可"进入副本图外区域"（BOSS 讨伐用例 f3 用 `cur_map="old_king_tomb"` 测『讨伐』）——**副本图 cur_map 仍可被世界事件/讨伐引用，SUBAREAS 重写不能删地图骨架**。
- 22 副本 × 2-4 房间后 `test_instance_map.py` 的"66 层 desc"断言总数需重标定（§2.2）。
