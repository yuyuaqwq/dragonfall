# F1 副本入口设施化 - 数据层落地报告

> 审计/落地时间：2026-08-30 · 落地方式：数据层直改（只动 `game/data/instances.py` + `game/data/subareas.py`）
> 依据：任务卡 `workspace/audit_3q/F1.md`、审计报告 `R1_report.md` / `R2_report.md`、策划案 `design/new_world/02_地图系统_余烬纪元合并版.md:687-712`（22 副本入口挂载总表）

## 结论摘要

✅ **完成**：22 副本全部加 `entry` 字段（map + subarea 真实 id，全部指向真实存在的地图/子区域）；21 处主世界入口子区域 `funcs` 追加 `instance` 标记（深渊裂隙入口 `ash_temple_1` 原本就带 `funcs=["instance"]`，故 22 个入口子区域去重后 22 处全部含 `instance` 标记，其中本次新标记 21 处）。
- 脚本验证 **PASS**：22/22 entry 存在性（map 在 `MAP_BY_ID`、subarea 在 `SUBAREAS`）+ 22/22 入口子区域 funcs 含 instance。
- `python -m py_compile` 两个文件均通过。
- 未动命令层、未 commit、未跑全量回归。

## 22 副本 entry 映射表（策划案总表 → 代码真实 id）

| 副本 (inst key) | 入口位置（策划案） | entry.map | entry.subarea | 入口子区域名 |
|---|---|---|---|---|
| inst_goblin_camp | 迷雾沼泽·沼泽深处 | misty_swamp | misty_swamp_3 | 沼泽深处 |
| inst_sea_cave | 铁港码头·海堤 | harbor_docks | harbor_docks_3 | 海堤 |
| inst_old_king_tomb | 王陵古道·王陵前 | king_road | king_road_3 | 王陵前 |
| inst_secret_crypt | 晨曦大圣堂·圣堂地窟 | dawn_cathedral | dawn_cathedral_3 | 圣堂地窟 |
| inst_elven_ruins | 月冠王庭·月庭宫门 | moon_court | moon_court_gate | 月庭宫门 |
| inst_ash_temple | 烬山·火山口 | cinder_mountain | cinder_mountain_3 | 火山口 |
| inst_abyss_gate | 烬山祭坛（通关后） | ash_temple | ash_temple_1 | 灰烬门廊（副本入口房） |
| inst_dragon_tomb | 龙巢·巢穴深处 | dragon_roost | dragon_roost_3 | 巢穴深处 |
| inst_deer_fort | 山丘矿洞·矿洞深处 | hill_mine | hill_mine_3 | 矿洞深处 |
| inst_holy_trial | 王陵古道·古道中段 | king_road | king_road_2 | 古道中段 |
| inst_moon_temple | 月光林·林深处 | moon_glade | moon_glade_3 | 林深处 |
| inst_frost_throne | 永冬湖·湖心 | winter_lake | winter_lake_3 | 湖心 |
| inst_storm_throne | 风暴崖·风暴崖顶 | storm_cliff | storm_cliff_3 | 风暴崖顶 |
| inst_sunken_ship | 风暴海峡·海峡深处 | storm_strait | storm_strait_3 | 海峡深处 |
| inst_siren_nest | 海妖湾·海妖巢 | mermaid_bay | mermaid_bay_3 | 海妖巢 |
| inst_gray_dwarf | 地下湖·湖底 | deep_lake | deep_lake_3 | 湖底 |
| inst_under_dragon | 熔火深渊·深渊深处 | molten_abyss | molten_abyss_3 | 深渊深处 |
| inst_eye_of_storm | 雷暴高原·高原核心 | storm_plateau | storm_plateau_3 | 高原核心 |
| inst_sea_god_temple | 风暴之海·海眼 | storm_sea | storm_sea_3 | 海眼 |
| inst_deep_dragon_palace | 风暴之海·风暴区 | storm_sea | storm_sea_2 | 风暴区 |
| inst_abyss_throne | 深渊祭坛·祭坛核心 | abyss_altar | abyss_altar_3 | 祭坛核心 |
| inst_cloud_sanctum | 彩虹云谷·云谷深处 | rainbow_cloud | rainbow_cloud_3 | 云谷深处 |

> 说明：策划案写「月冠王庭」对应代码 map `moon_court`（入口子区域 `moon_court_gate` 月庭宫门，type=城镇出口）；「烬山祭坛（通关后）」对应副本图 `ash_temple` 的入口房 `ash_temple_1`（type=副本，funcs 原已含 instance）。其余 20 条均精确命中策划案「地图·子区域」名。

## 21 处入口子区域 funcs 标记（本次新增）

以下入口子区域 `funcs` 追加 `"instance"`（保留原 funcs）：

misty_swamp_3 / harbor_docks_3 / king_road_3 / dawn_cathedral_3 / moon_court_gate（funcs 原为空 → ["instance"]）/ cinder_mountain_3 / dragon_roost_3 / hill_mine_3 / king_road_2 / moon_glade_3 / winter_lake_3 / storm_cliff_3 / storm_strait_3 / mermaid_bay_3 / deep_lake_3 / molten_abyss_3 / storm_plateau_3 / storm_sea_3 / storm_sea_2 / abyss_altar_3 / rainbow_cloud_3

- `ash_temple_1`（深渊裂隙入口）本身 funcs 已含 `instance`，未重复追加 → 22 处入口子区域 funcs 全部含 instance，本次新增 21 处。
- 去重后唯一入口子区域 22 处（king_road 承载 2 副本、storm_sea 承载 2 副本；其余一一对应）——与任务卡「21 处」的差异来自 ash_temple_1 原本已标记，故「需新增标记」恰为 21 处。

## 验证结果（脚本实测）

```
INSTANCES: 22 | SUBAREAS maps: 116 | MAP_BY_ID: 116
entry 问题: 无
去重入口子区域数: 22
funcs 缺 instance: 无
== 22 副本 entry 全齐且指向真实存在(在 MAP_BY_ID + SUBAREAS): True
== 22 处入口子区域 funcs 均含 instance: True（21 处本次新增标记 + ash_temple_1 原有）
PASS
```

- `python -m py_compile game/data/instances.py game/data/subareas.py` → COMPILE OK
- `import game.data` 全量装配成功（SUBAREAS 聚合 116 图、INSTANCES 22 条）

## 改动文件

| 文件 | 改动 |
|---|---|
| `game/data/instances.py` | 22 副本各加 `"entry": {"map": ..., "subarea": ...}`（+22 行） |
| `game/data/subareas.py` | 21 处入口子区域 funcs 追加 `"instance"`（+43/-21 行，全部为 funcs 块内追加一行） |
| `game/data/_assembly.py` | 未动（纯 dict 字段无需注册；SUBAREAS 聚合层不排斥新 funcs 值，import 装配验证通过） |

## 铁律遵守

- ✅ 只改 `game/data/instances.py` + `game/data/subareas.py`，未动命令层/战斗逻辑
- ✅ 未 commit（留给主 agent 统一提交）；未跑全量回归
- ✅ 未创建临时副本/junction；工作区 = 插件根目录
- ⚠️ 注意：`game/commands/instance.py` / `game/commands/world.py` 存在**其他 agent（F2 命令层卡）**的未提交改动（entry 消费逻辑），非本次产生，未触碰

## 遗留提示

- 消费端（命令层）注意：entry 的 map/subarea 是「入口位置」；`ash_temple_1` 是副本图内部入口房，位置校验需按副本图处理（该副本入口在副本图内）。
- 验证脚本保留在 `workspace/audit_3q/_f1_verify2.py` / `_f1_verify3.py`（可复跑）。
