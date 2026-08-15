# v115 审计报告 · 审计 3（策划一致性）

- **方案**：`design\new_world\33_网状子区域与探索扩容方案_v115.md`（§2 网状 / §3 今日奇遇 / §4 事件扩容 / §5 POI 扩容 / §6 探索见闻）
- **审计时间**：会话内逐条核对 + 指令级冒烟（`scripts\tmp_v115_smoke.py`）
- **运行环境**：`Python312` + conftest 隔离库（`GWEN_GAME_DB` 指向临时库，未触碰 `game_data.db`）
- **数据完整性审计**：`python scripts\audit_mesh.py` → **0 失败 / 0 警告，全部通过**（A1-A8 拓扑、B 装配、C POI、D 事件模板/maps、E 奇遇 effects、F reveal 格式）
- **实现文件（v115 新增/改动）**：均为 8 个实现 agent 交付物；本审计**未修改**实现。

> ⚠️ 审计期间发现 `game/core/__init__.py` 为**并发在线编辑状态**：会话开始时读到的版本（§2.4 从 maps 仅导出 3 个函数）与审计后段/冒烟运行时读到的版本（已补齐 subarea_depth/is_hidden_room/reveal_met/reveal_progress/bump_explore_count 导出）**不一致**。冒烟按运行时最新状态（全部导出、功能可用）记结论；若协调人需回溯历史版本，以最新已提交版为准。

---

## 一、逐条核对表

图例：✅ 符合 | ⚠️ 部分符合/文档与实现口径差异 | ❌ 不符合/缺陷

### §2 网状子区域房间

| # | 文档条款 | 状态 | 证据与说明 |
|---|---------|------|-----------|
| 2.1a | 存在 `EXTRA_SUBAREAS` | ✅ | `game/data/mesh_rooms_{south,west_north,east_abyss}.py` 均定义，`_assembly.py:19-32` 导入 |
| 2.1b | 存在 `SUBAREA_LINKS` | ✅ | 三个区域文件均定义，`_assembly.py:33-46` 并入 `SUBAREA_LINKS_INDEX` |
| 2.1c | 存在 `MESH_POI_MOUNTS` | ✅ | 三个区域文件均定义，`_assembly.py:92-94` 并入 `SUBAREA_POIS` |
| 2.1d | 装配：EXTRA 扩展 SUBAREAS / 建 LINKS_INDEX / 重建 SUBAREA_INDEX·BY_MAP | ✅ | `_assembly.py:79-81` 合并 EXTRA；`83-89` 建 LINKS_INDEX；`102-112` 重建索引；`116-117` 重建 MAP_BY_ID |
| 2.1e | 新房间 dict 同构 + `hidden`/`reveal` 可选字段 | ✅ | 抽查 oak_plain/white_deer_forest 等，字段齐全；隐藏房带 `hidden:True` + `reveal:"explore:N"` |
| 2.2-1 | **入口唯一**（入口 `_1` 为枢纽，map_exit/map_entry 不变） | ✅ | `subarea_links` 网状分支以 `_1` 为入口；`map_exit_subarea`/`map_entry_subarea` 未改（core/maps.py:108-144） |
| 2.2-2 | **连通性**（全图从 `_1` BFS 可达，隐藏除外） | ✅ | `audit_mesh.py` A4 通过（70 图 0 不可达） |
| 2.2-3 | **网状特征**（每图 ≥1 岔路或环/捷径；允许 1 死胡同） | ✅ | `audit_mesh.py` A6 通过（无岔路则必有环）；A5 通过（可见死胡同 ≤1，且非入口） |
| 2.2-4 | **等级曲线**（相邻可达等级差 ≤15；入口最低、越深越高） | ✅ | `audit_mesh.py` A7 通过（0 超差） |
| 2.2-5 | **回程保证**（除死胡同时每房 ≥2 连接；死胡同 1 连接且非入口） | ✅ | `audit_mesh.py` A5 通过 |
| 2.2-6 | **隐藏房间**（每图 ≤1；reveal explore:N 取 5-15；隐藏房 1 精英或稀有 POI） | ⚠️ | 数量/格式：`audit_mesh.py` A8 通过（≤1 且必有 reveal，F1 格式合法）。**协议偏差**：`subarea_links()` 核心 API 未做 `seen_hidden` 过滤（设计 2.4 原型里有该形参），改为「核心返回含隐藏房、命令层过滤」——功能等价的实现取舍，但签名与文档不一致。 |
| 2.2-7 | **旧房间 id 不变**（`_1.._3` 只改连接不改 id/怪物） | ✅ | oak_plain_1/2/3 在 `subareas.py:139+` 原样保留，经 SUBAREA_LINKS 连入网状（mesh_rooms_south.py:1319-1325） |
| 2.3 | **扩容规格**：野外 3→5-7、走廊 2→3-4、城镇/副本未动 | ✅ | `audit_mesh.py` B3 通过（城镇无 hidden/迁移）；抽查：oak_plain 6、emerald_forest 6、silver_wind_road 4、lost_library 3；迁移图 70 张、新房间（≥_4）共 **218** 个（文档预期≈+200） |
| 2.4 | **core 接口**：subarea_links/subarea_depth/is_hidden_room/reveal_met/reveal_progress/bump_explore_count | ✅ | core/maps.py:54-234 全部实现；核心导出见 `game/core/__init__.py:77-81`；冒烟 ① 11 个接口 `hasattr` 全 True 且可调用 |
| 2.5a | 地图面板：深度标记（🟢🟡🟠🔴💀）+ 隐藏未揭示 `🔒？？？` | ✅ | world.py:536-573；冒烟 ③④ 实测 oak_plain 面板有位置标记，emerald_forest 未揭示时面板出现 🔒 |
| 2.5b | 『前往』不返回未揭示隐藏房；输隐藏房名提示"有东西挡着（还差 N 次）" | ✅ | world.py:868-883；冒烟 ④ 未揭示『前往 6』被阻止（位置不变）✅；但提示文案走"序号无效"分支而非 reveal 引导文案（见差异 D-2） |
| 2.5c | 到达 `_subarea_arrive` 追加探索见闻记录 + 首访奖励 | ✅ | world.py:1195-1225 调 `C.exploration_record_visit`；冒烟 ② 首访后 `visited_subareas` 计数 +1 ✅、文本含位置/描述 ✅ |
| 2.5d | `_move_blocked_msg` 自动适配网状 | ✅ | world.py:695-725 用 `subarea_links` 结果拼提示 |

### §3 今日奇遇

| # | 文档条款 | 状态 | 证据 |
|---|---------|------|------|
| 3.1 | `DAILY_MAP_EVENTS` ≥20 图 × 2-3 变体 | ✅ | `data/daily_events.py` 20 张野外图，每图 2-3 变体；脚本统计 **20 图 ≥20** |
| 3.2 | effects 键：encounter_rate/event_chance/elite_chance/loot_mult/mats | ✅ | `audit_mesh.py` E2 白名单通过；combat.py explore 消费全部键（见下） |
| 3.3a | core `today_map_event` / `today_event_effects`（日期哈希全服一致） | ✅ | `core/daily_events.py:21-51`；冒烟 ① 均已导出 |
| 3.3b | explore() 遇怪率/事件率/精英/掉落/材料倾向挂点 | ✅ | combat.py:137(loot/effects)、175-176(事件率)、186(遇怪率)、275(elite)、678-683(loot_mult/pref_mats 注入 EventContext) |
| 3.3c | 地图面板底部显示今日奇遇行 | ✅ | world.py:585-598；冒烟 ③ 面板含"今日奇遇" ✅ |
| 3.4 | 探索事件材料倾向 mats 优先抽取 | ✅ | combat.py _handle_explore_event 注入 `pref_mats`（EventContext 支持），见差异 D-3 |

### §4 事件扩容

| # | 文档条款 | 状态 | 证据 |
|---|---------|------|------|
| 4.1 | EXPLORE_EVENTS 30→50（区域主题15 + 通用5） | ✅ | 脚本：**总数 50**；带 maps 区域主题 **15**（南3/中3/西3/北3/东2/外1），通用新增 5 |
| 4.2 | 新模板 +4：region_lore/stamina_gift/shrine_bless/rare_find | ✅ | core/event_templates.py:422/440/462/476 全部 `@register`；`audit_mesh.py` D1 通过 |
| 4.3 | 彩蛋 +6（区域4 + 全局2） | ✅ | 6 个新彩蛋 id 全部存在（egg_jumping_scarecrow/dove_messenger/sleigh_ghost/dragon_shadow/lost_mimic_cub/sunrise_gold）；EXPLORE_EGG_EVENTS 30→36 |
| 4.4 | 新事件 maps 均在 MAPS、id 唯一 | ✅ | `audit_mesh.py` D2/D3 通过 |

### §5 POI 扩容

| # | 文档条款 | 状态 | 证据 |
|---|---------|------|------|
| 5.1 | +7 类型，id/图标/effect 与文档一致 | ✅ | data/pois.py:69-103 定义 7 个：merchant_camp/merchant、ancient_altar/buff、bird_nest/herb、ice_sculpture/sight、dragon_bone/loot、shipwreck/loot、traveler_grave/note；**POIS 共 17**（10+7） |
| 5.2a | 每新房间 ≥1 POI；每迁移图 ≥1 新 POI | ✅ | MESH_POI_MOUNTS 合并后新房间(≥_4)挂载 **194 条**，覆盖三域（south/west_north/east_abyss）；`audit_mesh.py` C1/C2 通过 |
| 5.2b | 新 effect 分支：merchant/buff/note(grave_)/loot/herb/sight | ✅ | combat.py _handle_poi:778(merchant)、767(buff)、854-863(grave_ flag)、809(loot)、797(herb)、870(sight) |
| 5.3 | PROPS 补充（可选，非强制） | ✅ | 非硬性条款；各新房间场景元素经地图场景显示（冒烟 ② 面板见"✨ 场景"） |

### §6 探索见闻/探索进度

| # | 文档条款 | 状态 | 证据 |
|---|---------|------|------|
| 6.1 | `visited_subareas` 建表 | ✅ | store/connection.py:136-141 表结构（qq_id/map_id/sa_id/first_at，主键三列） |
| 6.1 | store 函数 add/get/count_visited_subareas | ✅ | store/world.py:96-133；导出见 store/__init__.py:59；冒烟 ② 计数 +1 ✅ |
| 6.2a | core/exploration.py：record_visit/region_progress/overall_progress | ✅ | core/exploration.py 完整实现；冒烟 ① 导出 ✅、⑤ region_progress/overall_progress 数值正确 ✅ |
| 6.2b | 首访奖励数值 exp=图等级×8 / gold=图等级×3 | ✅ | core/exploration.py:63-72（`lv*8` / `lv*3`）；隐藏房 +1 材料（76-86） |
| 6.2c | 到达处挂点（同图 `_subarea_arrive` + 跨图到达） | ✅ | world.py:1210（同图）与 1438（跨图）均调 `C.exploration_record_visit` |
| 6.3 | **『探索进度』指令 + 注册** | ❌ | `game/commands/exploration.py` 已写，`commands/__init__.py` 已 import；但 **Main(main.py:265-275) 未继承 `ExplorationCmds`**，且 **`game/commands/_registry.py` 未登记 `explore_progress`** → 运行时 `Main.explore_progress` 不存在，指令不可达（见差异 D-1） |
| 6.3 | 全大陆进度/每域进度/隐藏统计渲染 | ✅ | commands/exploration.py 渲染完整（region 行 + 全大陆 pct + tip）；冒烟 ⑤ 直接驱动 mixin 面板非空、含区域行+全大陆进度 ✅（绕过 Main 装配） |
| 6.4 | `region` 字段存在（region_progress 聚合依赖） | ✅ | 脚本：116/116 张 MAPS 均含 `region` 字段 |

---

## 二、指令级冒烟结果（`scripts\tmp_v115_smoke.py`）

| 场景 | 结果 | 说明 |
|------|------|------|
| ① 11 个 core 接口导出/可调用 | ✅ 11/11 | subarea_links/depth/is_hidden_room/reveal_met/reveal_progress/bump/today_*/exploration_record_visit/region_progress/overall_progress 全部 `hasattr=True` 且真函数 |
| ② 前往 oak_plain_4 | ⚠️ 部分 | 「前往 乱石岗」(按名) 到达 oak_plain_4、提示含位置/描述、`visited_subareas` 计数 +1 ✅；但文档假设的「前往 4」从 oak_plain_1 落到 **白鹿之森**（序号含跨图邻居，见差异 D-2） |
| ③ 地图面板深度/今日奇遇 | ✅ 3/3 | 含『可前往』、『今日奇遇』行、位置/深度标记 |
| ④ 隐藏房揭示流(emerald_forest_6) | ✅ 核心机制全通 | 未揭示显示 🔒、前往被阻止；bump×8 后 reveal_met=True、🔒消失、可前往隐藏房到达 emerald_forest_6。提示文案走"序号无效"分支（差异 D-2） |
| ⑤ 探索进度/见闻 | ⚠️ | 核心 `region_progress`/`overall_progress`、mixin 面板渲染均 ✅；但 **Main 未装配** → 生产指令不可达（差异 D-1） |

**冒烟结论**：网状地图/移动/隐藏揭示/首访奖励/今日奇遇/见闻数值等**核心机制全部可用**；仅剩「指令注册装配」与「序号语义/文案」两类差异。

---

## 三、差异清单（文档 vs 实现，建议处理方）

| # | 文档条款 | 实现现状 | 建议处理方 |
|---|---------|---------|-----------|
| **D-1** | §6.3 注册『探索进度』指令 + `Main` 装配 + `_registry` 登记 | ❌ **必须修**：`Main`(main.py:265-275) 未继承 `ExplorationCmds`；`game/commands/_registry.py` 无 `explore_progress`（启动 WARNING：`表多 1 键 ['explore_progress']`）。生产环境『探索进度』**不可达**。 | **实现需修**（协调人派修复，改 main.py 继承列表 + _registry.py 补条目；commands/__init__.py 已就绪） |
| **D-2** | §2.5b 隐藏房提示"似乎有什么东西挡着……（还差 N 次探索）" + 冒烟假设「前往 4 → oak_plain_4」 | 隐藏房防前往**功能正常**，但：① 移动序号从「当前房可前往列表」起算并按出口时并入跨图邻居编号，「前往 4」从 oak_plain_1（仅 2 个可前往）落到跨图白鹿之森，非 oak_plain_4——**文档无明确"跨图邻居占序号"口径**；② 隐藏房被拦时提示走「序号无效！可前往 N 处」而非 reveal 引导文案（因面板先不编号隐藏房）。 | 建议**文档同步阶段说明**：序号含跨图邻居的编号口径需写进 §2.5/23 章（玩家用名称更稳妥）；reveal 引导文案（还差 N 次）仅当玩家「按名」输隐藏房名时命中，序号路径无此引导——可接受，但若产品期望一律引导可再调。 |
| **D-3** | §2.4 `subarea_links(map_id, sa_id, seen_hidden=None)` 原型含 `seen_hidden` | 实现去掉 `seen_hidden` 形参，改「核心返回含隐藏房、命令层 `_visible_sas` 过滤」——功能等价、契约（G 用 `C.is_hidden_room`/`C.reveal_met`）成立。 | **文档同步阶段**：§2.4 接口签名按实现更新（行为描述不变）；不影响功能。 |
| **D-4** | 冒烟任务假设：oak_plain 有隐藏房 oak_plain_6 | 实现中 **oak_plain 无隐藏房**（_4/_5/_6 均 `hidden:False`；该图死胡同 _6 为精英房）。真正的隐藏房示例为 `emerald_forest_6`(explore:8) 等。文档 §2.1 示例把 oak_plain 画成含隐藏房，但 §2.3 未强制 oak_plain 必须有隐藏房。 | **文档同步阶段**：§2.1 示例若意图 oak_plain 含隐藏房，与数据不符；否则无碍（隐藏房为可选扩容）。 |

**无差异项（核对全部 ✅）**：数据模型与装配、拓扑 7 条、扩容规格、core 接口、今日奇遇、事件/彩蛋/模板扩容、POI +7 与挂载、见闻表/首访奖励数值/region 聚合。

---

## 四、结论

- **数据与核心逻辑层：全部通过**（audit_mesh 0 失败；冒烟核心机制全通）。
- **唯一硬缺陷**：**D-1** —— 『探索进度』指令未完成生产装配（Main 未继承 + _registry 未登记），玩家实际用不了。这是 §6.3 的明确交付要求，**必须由实现修复**。
- **其余均为文档口径差异（D-2/D-3/D-4）**，建议由文档 agent 在 v115 文档同步阶段合理更新，不改实现。
