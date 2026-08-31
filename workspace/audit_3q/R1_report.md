# R1 副本入口审查报告

> 任务：审查 dragonfall 副本（instance）的**入口机制**，回答"副本是不是虚空进入、能否设施化到子区域"。
> 铁律遵守：只查不改、无 git commit、无全量回归、报告每条发现带 `文件:行号` 证据。收尾验证 git status 无 tracked 改动 ✓。

## 覆盖范围（摸了哪些文件）

| 文件 | 规模 | 重点 |
|---|---|---|
| `game/commands/instance.py` | 3497 行 | instance_cmd L240-357、_instance_start L1749-2003、_instance_build_state L1479-1661、_instance_list L1166-1193、撤退 L608-643、离开 L650-678、_instance_move_route L686-710、_instance_defeat L3467-3497、_inst_map_id L44-54 |
| `game/core/maps.py` | 256 行 | map_entry_subarea L149-166、map_exit_subarea L130-146、subarea_links L72-127、网状函数 L169-256 |
| `game/data/instances.py` | 1911 行 | INSTANCES 22 副本字段扫描（无入口字段） |
| `game/data/subareas.py` | 12672 行 | 87 处 `type="副本"` 子区域、funcs 标记扫描 |
| `game/data/maps.py` | 4246 行 | MAPS/MAP_CONNECTIONS 定义（L4104 起） |
| `game/data/_assembly.py` | 278 行 | SUBAREAS 装配 L129-145、INSTANCE_STAGE_MAPS 装配 L147-162 |
| `game/core/worlds.py` | 286 行 | create_instance_world L89-132、destroy L134-142 |
| `game/core/encounter.py` | ~40 行 | encounter_chance 副本遇怪概率 |
| `game/commands/world.py` | 5085 行 | move L1274+、_instance_gate_block L1223-1268、_map_nav_body L812-920、_instance_dungeon_move L1655-1783 |
| `game/commands/combat.py` | 3150 行 | explore 路由 L71+、_main_kill_target_on_map L428+ |
| `game/commands/base.py` | 645 行 | _spend_stamina L607-617 |
| `game/core/constants.py` | | MAP_TYPE_INSTANCE = "副本" L58 |
| `game/data/tips.py` | 463 行 | instance 提示库 L235-246 |
| `design/new_world/02_地图系统_余烬纪元合并版.md` | 1140 行 | §七 副本入口挂载表 L687-724、设施子区域绑定铁律 L278-294 |
| `design/new_world/29_副本与组队系统.md` | 631 行 | §三 副本入口与开本规则 L42-70、§十三 副本地图化 L388-556、§十四 v137 重构 L560+ |
| `design/new_world/33_网状子区域与探索扩容方案_v115.md` | 321 行 | §2.3 副本不迁移 L87 |
| `design/new_world/02_地图系统.md` | 853 行 | 世界全图（旧版） |
| `docs/CONTINENT_ISOLATION_v141.md` | | 大陆隔离背景 |

数据统计（运行时验证）：
- 22 个副本图（type=副本）全部带 `dungeon: {no_exit: True, discovery_agro: 0.85, boss_room: <末房>, on_clear: victory}`，全部在 SUBAREA_LINKS_INDEX（92 图索引含全部 22 副本）。
- 22 副本全部在 MAP_CONNECTIONS 中与主世界图双向互连（如 `goblin_camp ↔ misty_swamp`）。
- INSTANCES 22 副本 key 全部 `inst_xxx`；副本图 id 全部 `xxx`（无 inst_ 前缀）；`_inst_map_id`（instance.py L44-54）负责互转。
- 副本图入口房间（subareas[0]）全部 `funcs=["instance"]`（87 处 type=副本 子区域全覆盖）；**主世界子区域无一处 funcs 含 instance**（含策划案"入口位置"对应的 21 个子区域）。

## 结论摘要

### 一、现状：是"虚空进入"，但有四层"半成品入口"残留

**直接回答：是虚空进入。** 玩家在**任何地点**（不限位置、不限地图）输入『副本 <名字>』即可开本，开本全链路（instance_cmd L240-357 → _instance_start L1749-2003）**没有任何位置/地图/子区域前提校验**——只检查：名字匹配（L1751-1757）、组队人数（L1759-1788）、全队等级（L1795-1799）、0 血（L1801-1805）、战斗状态（L1806-1814）、副业等待（L1818-1825）、入场钥匙（L1829-1851）、体力 20（L1853-1856）。开本后直接把全队 `cur_map` 写成副本图 id、`cur_subarea` 写成副本入口房间（L1935-1947），如同瞬移，玩家"上一秒在铁港城广场、下一秒已在哥布林营地入口栅栏"，没有任何"走到门口"的步骤。

但"虚空"的程度被四处半成品机制削弱（这些恰好是设施化的现成抓手）：

1. **徒步进图门禁已存在但未接通开本**：world.py `_instance_gate_block`（L1223-1268）在『前往/移动』时拦截"徒步直入副本图"，但有三个放行档（主线/支线 explore 任务目标 == 副本图、持有 key_item、已通关）——放行后走普通跨图移动落点 `map_entry_subarea`（L1492）**只改 cur_map/cur_subarea（L1516-1517）**，**不创建大陆实例、不上锁、不开本**（create_instance_world 全仓库唯一调用点 = instance.py L1937）。即：徒步进入副本图 = 空转（能逛房间但无 rooms 存档不遇怪、无战斗、无收益），且副本图 `no_exit` 只影响副本内移动，MAP_CONNECTIONS 出边仍在（可原路走回）。这条路径是"走到门口→进图"的雏形，但不是"走到门口→开本"。

2. **地图上副本图作为"可前往邻居"显示**：`_map_nav_body`（world.py L835-899）把 MAP_CONNECTIONS 邻居（含副本图）列进"可前往"，玩家在迷雾沼泽能看到"哥布林营地"并可『前往 N』——点了被门禁拦（L1470-1475），拦不住时进空转态。即"入口位置"在地图上**有显示、有路径**，但没有"进入副本"语义。

3. **策划案有明确的入口位置表，数据层未落地**：02 章合并版 §七（L687-724）给出全部 22 副本的"入口位置 子区域"（哥布林营地→迷雾沼泽·沼泽深处、海蚀洞窟→铁港码头·海堤……），且这些主世界子区域**全部实际存在**（运行时核对 21/22 命中，唯一例外 elven_ruins 策划写"月冠王庭·月庭宫门"、实际是 moonshadow_wood 的 moon_court_gate，均存在）。但这些入口位置子区域**没有任何副本入口标记**（funcs 全为 `['explore']` 或空，无 `instance`，无 type=副本，无 POI/门），开本流程也完全不读它们。**策划与实现脱节。**

4. **副本地图化后副本内部已是"地图"，入口房间带 funcs=instance**：22 副本图 subareas[0]（入口房间：入口栅栏/潮汐洞口/破败城门……）全部 `funcs=["instance"]`（subareas.py L815 等 87 处），但消费端 `funcs` 检查（world.py L130/2925-3415、base.py L317-425）**只认 quest/shop/craft/heal/trade/daily/lore/teach/ency/alchemy 等，没有 'instance' 分支**——副本内 funcs=instance 目前是死标记，任何命令层不消费。副本入口房间的语义是"开本落点"，不是"进入入口"。

### 二、设施化可行性：可行，且"挂子区域"是策划既定的架构铁律

- **架构层完全支持**：v87.17 设施子区域绑定铁律（02 章合并版 L278-294）明确"所有功能性设施必须挂在具体子区域，禁止地图级设施"——副本入口作为设施挂子区域是**设计语言内**的事，非新概念。子区域 dict 已有 funcs/shop/healer/craft 等挂载机制（base.py L317-425 消费），加一个 `instance` 分支天然。
- **数据层有明确挂点**：策划案 §七 的 21 个入口位置子区域全部存在（misty_swamp_3 沼泽深处、harbor_docks_3 海堤、king_road_3 王陵前、dawn_cathedral_3 圣堂地窟……），只需给这些子区域加标记（如 funcs 含 `instance` 或新字段 `instance_entry: inst_xxx`）。
- **"走到门口→进入"路径已有 60% 骨架**：地图面板显示副本邻居（world.py L835-899）→『前往』命中 _instance_gate_block 三档放行（L1223-1268）→落点 map_entry_subarea（L1492）。缺的是最后一步：放行后**拉起开本流程**（校验+锁队+扣体力+create_instance_world+大陆实例）。
- **副本数据的两套 id 已被 _inst_map_id 收口**（instance.py L44-54），设施挂载只需记副本图 id（goblin_camp）或 inst_ 前缀 key 均可，互转现成。
- **v137/v141 的"副本 = 封闭地图 + 大陆实例"模型天然支持设施化**：开本 = 从入口位置进入副本图（克隆为大陆实例 inst:<uuid>，worlds.py L89-132），与现状唯一差别是"入口位置校验"前置。
- 33 章网状子区域方案（L87）明确"城镇/副本/副本 stage 不迁移、副本走开本流程"——**副本图本身不该动**，设施化应落在**主世界入口位置子区域**上，不是副本图内。

### 三、设施化改动面（要动的代码）

| # | 改动 | 位置 | 说明 |
|---|---|---|---|
| 1 | INSTANCES 每副本加入口字段 | `game/data/instances.py`（22 条） | 如 `"entry": {"map": "misty_swamp", "subarea": "misty_swamp_3"}` 或直接引用策划 §七 表 |
| 2 | 入口子区域加标记 | `game/data/subareas.py`（21 处） | funcs 加 `instance`（或新字段 `instance_entry`），与副本 desc/列表联动显示 |
| 3 | 开本位置校验 | `game/commands/instance.py` _instance_start L1749 前置 | 『副本 <名字>』要求玩家 cur_map/cur_subarea == 入口位置（或放行：已通关免位置/任务内免位置/队内任意成员在入口）；不满足给"去 迷雾沼泽·沼泽深处"引导 |
| 4 | 徒步入口接通开本 | `game/commands/world.py` move L1470-1488 + _instance_gate_block L1223 | 三档放行后不再走普通移动，改为拉起 _instance_start（队长）/提示组队（队员）；或保留"进图空转"改为"进图=进入副本入口房间，提示『副本 <名>』开本" |
| 5 | funcs=instance 消费 | `game/commands/world.py` _map_facilities/子区域面板、base.py 设施判定 | 入口位置子区域面板显示"🏰 此处是【哥布林营地】入口（『副本 哥布林营地』进入）" |
| 6 | 副本列表显示入口 | `game/commands/instance.py` _instance_list L1166-1193 | 每行可加"📍 入口：迷雾沼泽·沼泽深处" |
| 7 | 失败回城/离开落点可选优化 | `instance.py` _instance_defeat L3467+、instance_leave L650 | 现状回 BFS 最近城镇（L3484），设施化后可回"入口位置子区域"（更贴"进门"语义） |

关键风险提示：`_instance_gate_block` 的三档放行（任务/钥匙/已通关）若直接接开本，需注意**钥匙语义**——徒步进图不扣钥匙（L1236 注释），开本才扣（L1848-1849），两套校验不可合并；以及主线击杀目标只挂副本图（combat.py L428+ _main_kill_target_on_map）的任务内放行路径（q3_3/q6_2/q9_4/q10_1/q12_1/q12_2）需要保持"单人可进图打主线怪"能力，设施化不能把这条堵死。

## 证据清单

1. **开本无位置校验（虚空进入核心证据）**：`game/commands/instance.py:1749-1856` —— _instance_start 全链路校验 = 名字(L1751-1757)/组队(L1759-1788)/等级(L1795-1799)/0血(L1801-1805)/战斗(L1806-1814)/副业(L1818-1825)/钥匙(L1829-1851)/体力(L1853-1856)，**无任何 cur_map/cur_subarea/位置判定**（grep 验证：_instance_start 段内 cur_map 仅出现在 L1934-1946 的"开本后写位置"，无前置检查）。
2. **开本瞬移落点**：`game/commands/instance.py:1935-1947` —— `_map_id = kid[5:]...; _entry_sa = C.map_entry_subarea(_map_id); db.update_player(group_id, m, cur_map=_map_id, cur_subarea=_entry_sa, world_id=_world_id)`，全队位置直接写成副本入口房间。
3. **入口命令本身不查位置**：`game/commands/instance.py:236-357` —— `instance_cmd` 正则 `副本(?!地图)` 任意位置触发，L293-296 无参列列表，L356 转 _instance_start；L301-355 只处理"已撤退进度恢复"，恢复路径同样无位置校验（L312 直接 `db.update_player(cur_map=_mid, cur_subarea=_entry_sa)` 把玩家拉回副本）。
4. **体力消耗无位置语义**：`game/commands/base.py:607-617` —— _spend_stamina 只查体力数值；instance.py:1853 `_spend_stamina(group_id, qq_id, 20, player, "进入副本")` 队长扣 20 体力，与位置无关。
5. **INSTANCES 无入口字段**：`game/data/instances.py:17-118`（哥布林营地样例）——字段全集 `[atk_mult, blueprint, boss, boss_line, desc, exp, gold, hp_mult, icon, intro, lv, mat_count, materials, max_players, mech, min_players, minions, name, outro, stages]`，**无 entry/entrance/map_id/subarea/location/入口/位置 任何字段**（运行时全表扫描 22 条零命中）。
6. **副本图是"地图"且连主世界**：`game/data/maps.py:4104+` MAP_CONNECTIONS —— `goblin_camp: ["misty_swamp"]`、`misty_swamp` 邻居含 `goblin_camp`（双向）；22 副本图全部与主世界图互连（运行时验证），type 全为"副本"（constants.py:58 MAP_TYPE_INSTANCE="副本"）。
7. **徒步进图门禁三档放行**：`game/commands/world.py:1223-1268` —— _instance_gate_block：①任务内 explore 目标==副本图放行(L1246-1256) ②持有 key_item 放行(L1257-1261) ③已通关放行(L1262-1265)；L1236 注释明确"徒步进图不扣钥匙"。
8. **徒步进图不接通开本**：`game/commands/world.py:1470-1488, 1516-1517` —— move 中 _instance_gate_block 命中即拦（L1472-1475）；放行后落点只 `db.update_player(cur_map, cur_subarea)`（L1516-1517），无 create_instance_world/无 _lock_battle；create_instance_world 全仓库唯一调用 = instance.py:1937（search_files 验证）。
9. **副本入口房间 funcs=instance 是死标记**：`game/data/subareas.py:815`（goblin_camp_1 入口栅栏 funcs=["instance"]，87 处同款）——消费端 world.py L130/2925-3415、base.py L317-425 的 funcs 分支只认 quest/shop/craft/heal/trade/daily/lore/teach/ency/alchemy，**无 instance 分支**（grep 验证）；主世界子区域 funcs 含 instance 的 = 0 处。
10. **策划案入口表未落地**：`design/new_world/02_地图系统_余烬纪元合并版.md:687-712` —— 22 副本"入口位置"表；运行时核对：入口位置子区域全部存在（21/22 精确命中，elven_ruins 差异为 moonshadow_wood 内 moon_court_gate，存在），但**无任何副本入口标记**（funcs 全 ['explore'] 或空，type 全野外，无 POI/门）。
11. **设施子区域铁律（设施化的设计背书）**：`design/new_world/02_地图系统_余烬纪元合并版.md:278-294` —— "所有功能性设施必须挂在具体子区域，禁止地图级设施"；`design/new_world/29_副本与组队系统.md:42-70` —— 开本规则表同样无位置条件。
12. **副本图不该动（33 章明确）**：`design/new_world/33_网状子区域与探索扩容方案_v115.md:87` —— "城镇/副本/副本 stage 不动……副本走开本流程"；设施化应落在主世界入口位置子区域。
13. **副本地图化 = 封闭地图模型（设施化兼容）**：`design/new_world/29_副本与组队系统.md:560-588`（v137 设计：副本=封闭地图 no_exit）与 `game/core/worlds.py:89-132`（create_instance_world 克隆副本地图为独立大陆 inst:<uuid>）——开本 = 进入封闭副本大陆，天然可解释为"从入口走进副本"。
14. **开本不占地图位置（现状语义注释）**：`game/commands/instance.py:282-283, 3481-3482` —— 注释自认"开本不占地图位置""cur_map 仍是开本前所在图"（失败回城按开本前位置 BFS 最近城镇，combat.py:2175-2194 _nearest_town）——这正是"虚空进入"的运维残留证据。

## 影响面评估

- **数据**：`game/data/instances.py` 22 条加 entry 字段；`game/data/subareas.py` 21 处入口位置子区域加标记；`game/data/tips.py` instance 提示库可加"去入口"引导。
- **命令层**：`game/commands/instance.py` _instance_start 前置位置校验 + _instance_list 显示入口；`game/commands/world.py` _instance_gate_block/move 三档放行后接开本（或改为"进入口房间→引导开本"）+ funcs=instance 消费；`game/commands/base.py` 设施判定分支。
- **兼容性红线**：①徒步进图不扣钥匙 vs 开本扣钥匙（world.py:1236 vs instance.py:1848-1849）不可合并；②主线击杀目标只挂副本图（combat.py:428+，q3_3/q6_2/q9_4/q10_1/q12_1/q12_2）需保留"任务内单人可进图"路径；③撤退恢复（instance.py:301-355）与 24h 过期回收路径同步加位置校验，避免旧玩家存档（cur_map 已在副本图）被新校验卡死——需对"已在副本图内的存量玩家"做豁免。
- **测试**：设施化后需新增/更新 `tests/test_instance*.py` 的入口校验用例（位置不符拦截、入口位置开本放行、徒步进图拉起开本、任务内豁免）；**注意铁律：只跑单个测试文件，禁全量回归**。

## 收尾验证

- git status：74 个 untracked（全部为既有测试探针/文档，非本次产生），**无 tracked 改动** ✓
- 本次未创建任何临时脚本（纯读 + 内存 Python 验证）✓
- 报告写入 `workspace/audit_3q/R1_report.md` ✓
