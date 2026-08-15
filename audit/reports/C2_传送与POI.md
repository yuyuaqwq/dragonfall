# C2 传送与POI — 子审计报告

**审计批次/切面**：Dragonfall 全项目深度审计 批次1 · C2 传送与POI
**方法**：只读静态审计（read / glob / grep）；未运行游戏、未执行任何脚本/写库。

---

## 0. 审计范围

| 文件 | 相对项目根 | 行数 | 说明 |
|---|---|---|---|
| game/core/portals.py | ✓ 存在（6 行） | portal_cost 传送费用 |
| game/core/pois.py | ✓ 存在（49 行） | POI 触发/效果纯逻辑 |
| game/data/portals.py | ✓ 存在（16 行） | 11 座方碑 |
| game/data/pois.py | ✓ 存在（383 行） | POIS 定义 / SUBAREA_POIS / 文案池 |
| game/data/poi_pools.py | ✓ 存在（18 行） | 材料池 |
| game/data/instance_stage_maps.py | ✓ 存在（678 行） | 副本层小地图 POI |
| scripts/v8716_settlement_exits.py | ✓ 存在（217 行） | 定居点出口重命名迁移脚本 |
| scripts/v8716_settlement_exits2.py | ✓ 存在（92 行） | 第二轮守卫改职 + props 修复 |
| scripts/demo_route.py | ✓ 存在（41 行） | 路线连通 BFS 演示 |

**未覆盖原因**：占满；本批仅覆盖上表清单。交叉文件（maps.py / subareas.py / mesh_rooms_*.py / world.py / combat.py / instance.py / _assembly.py / core/maps.py）仅作为被引用方做了**定向 grep/read**，未全量审计（分属 C1/A 等切面）。

**依赖核对（静态）**：
- SUBAREA_POIS 使用到的全部子区域 id 均已在 `game/data/subareas.py` 中定义（entry/grep 验证，无悬空 key）。
- POIS 17 类 effect 均在 `game/commands/combat.py::_handle_poi`（743-885）和 `_handle_inst_poi`（887-1000）实现分支；无定义了不实现、也无实现不见定义的 effect。
- poi_pools.py 三个池内材料名全部命中 `MATERIALS` 注册名（items.py verify），无孤儿名。

---

## 1. S级

| # | 位置(文件:行) | 描述 | 影响 | 建议 |
|---|---|---|---|---|
| — | — | 未发现 S 级问题。传送计费、派碑激活/传送、POI 每日重置、副本 POI 机关/秘密语义均无崩溃/卡死/刷资源路径。 | — | — |

## 2. A级

| # | 位置(文件:行) | 描述 | 影响 | 建议 |
|---|---|---|---|---|
| — | — | 未发现 A 级问题（详见 §7 两个待裁决边界判断）。 | — | — |

## 3. B级

| # | 位置(文件:行) | 描述 | 影响 | 建议 |
|---|---|---|---|---|
| 1 | game/data/pois.py:128 与 :337 | `oak_plain:oak_plain_3` 被定义两次：L128 `["campfire","herb_patch","scenic_view"]`，v115 块 L337 `["merchant_camp","herb_patch","scenic_view"]`。Python dict 后写覆盖，最终**静默丢掉 `campfire`**。 | 该子区域不再有篝火 POI（图内其他子区域仍有），属静默数据回归，易被后续维护误解。 | v115 块手写"叠加"逻辑不可靠：将旧条目删掉再全量写，或改为在 `_assembly.py` 用 extend 追加并各自去重，避免重复 key。 |
| 2 | game/data/pois.py:113-359 | SUBAREA_POIS 存在 **16+ 组重复 key**（基础块 + v115 块重复定义，如 oak_plain_2/3、gold_plain_2/3、frost_field_1/2、permafrost_field_2、dragon_ridge_1、bone_wild_2、storm_sea_2、misty_swamp_1、molten_abyss_1、deep_lake_2 等）。本次除 oak_plain_3 外其余 v115 块均为超集，但靠人眼保证"后块是超集"极脆弱。 | 维护/可读性差：重复 key 默认后者胜出，任何一方漏项即产生未注意的 POI 消失。 | 统一为每个子区域只保留一条定义；合并用装配时 extend + 集合去重。 |

## 4. C级

| # | 位置(文件:行) | 描述 | 影响 | 建议 |
|---|---|---|---|---|
| 1 | game/commands/combat.py:81-82 | 城镇探索冷却 key 注释写"每小时可白嫖约 9 次"，但实际 CD 为 60 秒（约 60 次/时），数值举例与实现不符。 | 注释误导，非功能 bug。 | 校正注释。 |
| 2 | design/new_world/02_地图系统…md §10 (L888) 声明"每野外子区域 1-2 个 POI"，但多子区域实挂 3-4 个（如 pois.py:357 misty_swamp_1 = 4 个）。 | 设计与实现轻微偏差。 | 属 v115 有意放宽；建议文档同步"死胡同/隐藏房可 ≥2"。 |
| 3 | game/core/maps.py:108-124 map_exit_subarea / :127-144 map_entry_subarea | 城镇仅返回**首个** `type=="城镇出口"` 子区域；若一城未来有多个 GATE 子区域，只认第一个。 | 当前各城均单出口，无影响；属未来扩展隐患。 | 无需处理，记录即可。 |
| 4 | game/data/poi_pools.py WISH_POOL | 流星愿望池与营地/草药池共用 `C.resolve`+`in MATERIALS` 静默掉包（id 不合法时奖励空）。当前已验证无孤儿名。 | 低风险健壮性。 | 保留脚本校验或注释强调注册名契约（已有）。 |
| 5 | game/data/portals.py | `portal_cost(image)` 无上限，高图（lv≈90）达 500 金币；无等级门槛，低等级玩家可付费直达高图被秒。 | 属既有设计（付费反滥用），非缺陷，但极端情况体验偏陡。 | 可考虑加"地图等级-玩家等级"门限（可选）。 |

## 5. 亮点

1. **副本 POI 分层状态机严谨**（instance.py:773-799 _stage_poi_state / _poi_used / _any_poi_used + instance_stage_maps.py）：`poi_unlocks` 跨层语义（如 `rune_2 effect.unlock rune_1` 与 `mech_1 need.poi_read rune_1`）实现了"读碑→解锁机关→绕精英"的玩家协商式推进，且 R3 修复后 POI id 实例内唯一，杜绝了跨层撞 id 引发的机关误解锁。机关/陷阱/宝箱/篝火/隐藏房（secret.cond via _any_poi_used）交互闭环清晰，`heal_pct`/`boss_buff` 等配置均被消费而非死配置。
2. **传送/回城区分与子区域落点设计自洽**：`portal_travel` 落地目标图 `subareas[0]`（广场）与 `map_entry_subarea`（城镇 GATE）分离，并显式注释"传送/回家=城内直达走广场、步行=走城门"（core/maps.py:132、item_templates.py:395）；`portal_activate` 要求玩家亲临首个子区域才能激活（world.py:1376-1384），杜绝"站城外开传送点"。费用/坐骑折扣在 view 与 travel 两处一致。
3. **反刷机制完备**：POI 每日重置（_poi_daily_used，按 图:子区域:poi 每日一次）、城镇探索 60s 冷却、`traveler_grave` 见闻 flag（grave_{map}_{qid}）区分首次/重复——避免高价值 POI（merchant_camp/loot_pile 出图纸）被高频刷取。
4. **定居点出口规范化完整落地**（v8716）：14 个无城墙定居点的"出口子区域"已按 `type="城镇出口"` 重命名并配 `城镇街道` 链，`map_exit_subarea/map_entry_subarea` 改为按 type 识别（core/maps.py:119-140），弃用 `_gate` 后缀猜测，与设计文档 §5 铁律吻合。

## 6. 相邻切面核对结论

交叉核对矩阵 4.1：

- **C1↔C2｜子区域-道路-传送门三角连通**：✅ 通过。
  - 逐一核对了 11 座方碑地图 + 14 个重命名出口地图的 `MAP_CONNECTIONS` 双向对称性（maps.py:4071-4188），全部成对（如 oak_town↔oak_plain/maple_village、silver_brook↔silver_valley/windmill_plain、aurora_town↔permafrost_field/frostwhisper_canyon 等），无单向断层。
  - 出口子区域均带 `type="城镇出口"`，`map_exit_subarea/map_entry_subarea` 可按该 type 正确返回（core/maps.py:108-144），玩家能走进/走出；镇郊→街道→广场链（v8716 脚本生成）与 `_subarea_links` 的 STREET/GATE 分支（core/maps.py:87-97）配套。
  - `demo_route.py` BFS 走 `MAP_CONNECTIONS` 验证 oak_town→white_deer / →dawn_city / white_deer→ironharbor 均有路径所列目标均可达。
- 提示 C1（道路/连接切面）：重点复查 `region 细分字段` 与跨区对称层（我仅核对到 MAP_CONNECTIONS 层面）。

## 7. 待组长裁决

1. **pois.py 重复 key 治理优先级**：是否要求统一去重（本批仅 1 处真实掉项 oak_plain_3 的 campfire，其余为超集）。若接受"后块覆盖"为既定模式，可降级为 C；若要求干净数据，请立项整改。**建议：≥B**。
2. **`portal_cost` 高图付费直达（无等级门槛）**：是否属于"低等级花金币进高图被秒"的体验问题。当前设计符合"付费反滥用"原意，倾向不处理；若鱼鱼认为有体验陡崖，可配置 lv 门限。

## 8. 切面健康度

**健康度：86 / 100**

无 S/A 级硬伤，传送体验自洽、副本 POI 状态机与反刷机制扎实；扣分主要在 SUBAREA_POIS 重复 key 造成的静默维护隐患（1 处已丢失 campfire）与少量文档同步偏差。
