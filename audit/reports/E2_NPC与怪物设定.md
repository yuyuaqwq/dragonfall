# E2 NPC与怪物设定 — 子审计报告

## 0. 审计范围（文件清单 / 行数 / 未覆盖原因）

| 文件 | 行数 | 说明 |
|------|------|------|
| design/new_world/03_NPC群像.md | 1201 | 城镇NPC/野外NPC/隐藏NPC/对话树设计 |
| design/new_world/04_怪物图鉴.md | 904 | 怪物/Boss/世界Boss/隐藏怪设计 |
| game/data/npcs.py | 2848 | 城镇NPC数据表（含酱油NPC补全） |
| game/data/monsters.py | 1303 | 仅 MONSTER_SKILLS 技能定义表 |
| game/data/hidden_monsters.py | 218 | 隐藏怪表（25只） |
| game/data/wild_npcs.py | 416 | 野外NPC(32)/隐藏NPC(13) |
| design/new_world/.gen/monsters.json | 3975 | 设计快照（中文名技能/掉落） |
| design/new_world/.gen/monsters_final.json | 3975 | 设计快照（已映射 ms_ 技能ID） |
| design/new_world/.gen/npcs.json | 476 | 设计快照（含设计级 func 中文描述） |

**未覆盖原因**：怪物实际刷新表不在此批清单内（分布在 maps.py 地图 monsters 列表、mesh_rooms_*.py、subareas.py、instances.py），仅作佐证交叉核对；战斗引擎 battle.py、对话引擎、图鉴/百科命令只作判定逻辑参考，未精读全量。

**关键结构澄清**：`monsters.py` **不含 MONSTERS 主表**，仅含技能字典 `MONSTER_SKILLS`（205 个）；怪物数据实际挂在 maps.py / mesh_rooms_*.py / subareas.py / instances.py 的 `monsters` 列表与 `elite/boss` 条目中。本报告对怪物的"实现侧"结论因此需结合这些外部文件证据。

## 1. S级

**无 S 级发现。** 依据：技能引用完整性校验通过（`monsters_final.json` 引用 194 个技能 ID 全部在 `MONSTER_SKILLS` 有定义，无悬空引用）；已落地副本 Boss（b_cardinal Lv.94 / b_goblin_chief Lv.20 等）等级与设计文档一致；世界 Boss 池 6 只实现与 04 章实现口径注记吻合，未发现会导致崩溃/数据损坏/刷资源/规则失效的缺陷。

## 2. A级

| # | 位置(文件:行) | 描述 | 影响 | 建议 |
|---|---------------|------|------|------|
| A1 | game/data/hidden_monsters.py:86-93；game/data/mesh_rooms_south.py:828；game/data/subareas.py:2395 | **怪物 ID 冲突：`e_abbey_guardian` 一 ID 两怪**。隐藏怪表 `e_abbey_guardian`=圣堂武僧（cond any，maps dawn_cathedral/white_abbey，Lv.地图+5）；mesh_rooms_south.py 同 ID=修道院守护者（elite 43）；设计文档 04 §4.3 也用 `e_abbey_guardian`=修道院守护者，§16 又用 `e_abbey_guardian`=圣堂武僧——设计文档自身也撞车。 | 运行时虽各自查表（隐藏怪走 HIDDEN_MONSTERS、普通怪走地图 monsters 列表）暂不直接串数据，但该 ID 一旦被任何全局"按 ID 查怪/图鉴/百科/怪物mods"逻辑引用即歧义；图鉴击杀归属可能错记到同 ID 另一怪。属隐藏怪与普通精英共享 ID 的**规则性隐患**。 | 为隐藏怪改用独立命名空间（如 `h_abbey_guardian`）或与普通精英拆分 ID；同步修正设计文档 04 §4.3 与 §16。 |
| A2 | design/new_world/.gen/monsters_final.json（全表）；design/new_world/04_怪物图鉴.md §11.3/§11.5.2、§3.5/§12.6、§11.3 | **怪物 ID 重复定义（281 个不同 ID 中 2 个重复）**：`m_sea_serpent`（风暴海峡 tank Lv.52 vs 龙鲸海域 speedster Lv.64 两处不同档案）、`m_magma_worm`（熔火深渊 dps Lv.78 vs 熔岩河床 dps Lv.86 两处）。均为同一怪物名跨区域重复建档，属性名冲突。 | 若实现按 ID 建唯一索引会后者覆盖前者；当前实现按"地图 monsters 列表"各自内联则形态尚一致（同种怪等级递进属正常复用），但数据模型上同 ID 两档案是隐患，也造成图鉴/掉落口径不清。 | 同一 iD 只保留一处权威档案，跨区域等级递进用`lv_off`或别名 ID 表达；在设计文档同步收敛。 |

## 3. B级

| # | 位置(文件:行) | 描述 | 影响 | 建议 |
|---|---------------|------|------|------|
| B1 | game/data/npcs.py:122-124 (npc_oak_elder)、:401-409 (npc_frost_blade)、:513-520 (npc_fallen_chief)、:254-262 (npc_garrison) 等 | v105 M21 P1-5 已删"quest 死 func"（无任务 giver），但 **design/03 §八 功能与分布表仍标这几名 NPC 为 quest**（如老橡 quest、艾德温 quest/daily、裂颅 战斗）。文档未随实现迭代同步。 | 实现无死 func（正确），仅 03 章 §八 参考表过时，属文档-实现偏差（已注明为故意迭代的清理，但纠偏文档漏更新）。 | 更新 03 §八 表，标注 quest 已删或改列"纯展示/战斗"NPC。 |
| B2 | game/data/npcs.py:2626-2632 (npc_wind_guard2)、:2635-2641 (npc_elf_poet2)；game/data/wild_npcs.py:138-145 (w_elf_poet) | 命名"XX2"后缀（npc_wind_guard2/npc_elf_poet2）为规避重复而追加编号，缺语义化名字；且 w_elf_poet 与 npc_elf_poet2 均含"精灵诗人"概念、星歌/月冠两处重复感。 | 命名统一性瑕疵，玩家区分两条"精灵诗人"时困惑。 | 将后缀改为含义化（守门人·展翼/诗者·月弦）；评估 w_elf_poet 与 npc_elf_poet2 去重。 |
| B3 | game/data/npcs.py:16-19 (npc_blacksmith funcs shop/craft) 与 03 §八 | 部分 NPC funcs 与 03 §八表有差：如 npc_innkeeper 实现多出 `quest`（设计 §八 仅 heal/lore）、npc_doctor 多出 `quest`、npc_auctioneer 多出 `quest`、npc_blacksmith2(汉斯) 多出 `quest`。 | 玩家对无任务 NPC 却显示 quest 入口，属提示断链小瑕疵。 | 核对 funcs 是否真有对应任务 giver，多余 quest func 应收敛。 |
| B4 | design/new_world/04_怪物图鉴.md §八（Lv.575-582）与 §十四（Lv.857-860） | 世界 Boss 表 §八 与 §十四 重复列出海蛇王·深渊之鳞/地底恶魔·黑炎/风暴龙王·裂空；且 §八 头两行"腐牙兽人酋长·裂颅""恶魔将军·贝利尔"已按注记未实装，但表头仍保留。 | 文档内部重复与残留未实装行，易误读世界 Boss 清单。 | 合并 §八/§十四为单一世界 Boss 表，移除未实装 2 行或改"暂缓"。 |
| B5 | design/new_world/04_怪物图鉴.md §八 末行 "古龙·奥姆之影 全属性大幅提升"；game/data/world.py:40 mech="enrage" | 设计文档世界Boss机制文字（"全属性大幅提升"）与实现 mech="enrage"（狂暴攻击+35%）语义不完全一致。 | 数值-设计轻偏差，不算失衡但文案不统一。 | 统一 04 章机制描述与 world.py mech。 |
| B6 | game/data/wild_npcs.py:2-4 (docstring "28 个野外") | docstring 写 28，实际 WILD_NPCS 为 32 个（与设计 03 §二"32个"一致）。 | 文档字符串过时，易误导维护者。 | docstring 改 32。 |

## 4. C级

| # | 位置(文件:行) | 描述 | 影响 | 建议 |
|---|---------------|------|------|------|
| C1 | game/data/npcs.py:1165-1170 | npc_emerald_hunter 的 lore/dialogue 提及古树空地石碑"它还在睡"，与主线 lore (npc_druid_oakheart/npc_eter) 可互证；散见 lore 逐 NPC 内联而非集中化，维护成本高。 | 纯维护性建议。 | 考虑 lore 集中到单独字典便于统一校审。 |
| C2 | design/new_world/03_NPC群像.md §11（第一批对话树）| 设计列出首批 6 名 NPC 对话树（老约翰/圣女/莎拉等），status 标注在 dialogue_conds.py 未实装 talked_count 条件（03 章 768 行自注）——对话树主结构未精读验证，仅记录其"分期实装"声明。 | 对话树深度(8层圣女线等)与当前单轮 `_npc_dialogue` 体验差距大，属已知迭代路径。 | 保持节奏，待 E3对话引擎子 Agent 复核。 |
| C3 | design/new_world/.gen/npcs.json | 设计快照 funcs 含设计级中文描述（"等级认证""战斗引导""隐藏线索）""船坞""情报"等），与实现 funcs 枚举（quest/shop/heal/lore/rune/enchant/apprentice/tutor/portal/auction/daily）命名体系不同。 | .gen 为设计产物非运行时，不直接危害；但两套 func 词表易混淆。 | 设计侧统一功能词表或注明映射。 |
| C4 | design/new_world/04_怪物图鉴.md §11.5.2 与 §3.10 | 设计文档 04 §11.5.2 龙鲸海域 m_sea_serpent 与 §16 隐藏怪 e_sea_serpent（设计）同名"海蛇"；实现 hidden_monsters.py e_sea_serpent=海蛇精英。多层级"海蛇"名重复。 | 图鉴条目名重复，玩家难区分普通海蛇 vs 隐藏精英海蛇。 | 隐藏精英改名（如"渊海海蛇"）提升辨识。 |

## 5. 亮点

1. **技能引用完整性极高**：`monsters_final.json` 引用的 194 个技能 ID 全部在 `MONSTER_SKILLS` 有定义，零悬空引用；副本精英此前缺失的 6 个技能 ID（`ms_kuang_bao`/`ms_you_ling`/`ms_zhen_ji`/`ms_an_ying`/`ms_xu_kong`/`ms_hai_yao`）已在 monsters.py:1259-1303 注释里补齐，体现对"定义-消费"闭环的自觉修复。
2. **实现侧主动清理死 func 且注明版本根因**：npcs.py 多处 `# v105 M21 P1-5：无任务 giver → 删 quest 死 func` 以注释保留决策依据（如 npc_oak_elder/npc_garrison），实现了"显示=可触发"的断链修复，工程纪律清晰。
3. **隐藏怪/隐藏NPC规模与设计一致**：隐藏怪实现 25 只与 04 章§十六口径吻合；隐藏 NPC 13 只（10 基础+3 隐藏线）与设计相合，且 unlock 条件经 v104 修正（如 h_abyss_whisper 由近乎锁死的 flag 改为可达成的主线 q10_6），避免"永久锁死"。

## 6. 相邻切面核对结论（交叉核对矩阵 4.1 相关行：E1↔E2 世界观名词与 NPC/怪物设定统一）

- **E1 世界观名词 ↔ E2 NPC/怪物命名统一性**：核心身份一致——`蚀夜`（封印守护者，npc_eter，03 章★核心）、`英雄王艾德里克`长期埋坑（npc_bard/npc_pilgrim 台词互证）、`圣光教会第37代圣女艾莉丝`（npc_saintess title）与主线一致、`奥古斯都`枢机主教（npc_cardinal 与 subareas 圣堂地窟 b_cardinal Lv.94 一致）。未发现世界观名词被 NPC/怪物设定推翻。
- **E1↔E2 待转达**：`e_abbey_guardian` 一 ID 二怪（隐藏怪圣堂武僧 vs 普通精英修道院守护者）涉及图鉴/百科按名或按 ID 归属，建议 E1 世界观名词侧留意"修道院守护者/圣堂武僧"是否同一概念被两处命名。另 `英雄王艾德里克`"走进烬山没再出来"（03 §7.2/§2.4 w_pilgrim）与"龙王"世界Boss（古龙·奥姆之影）是否同源待 E1 侧确认。

## 7. 待组长裁决

- **裁决1**：怪物 ID 冲突 `e_abbey_guardian`/`m_sea_serpent`/`m_magma_worm` 是否提升优先级处理——当前运行时因"隐藏怪独立查表 + 普通怪按地图内联"未发生数据串写，但按 ID 全局引用有歧义，需定统一 ID 命名策略（隐藏怪 `h_` 前缀 vs 地图内联允许复用名）。
- **裁决2**：设计文档 03 §八 副本功能表（quest 标了已删 NPC 等）与实现迭代的偏差，是否列入本轮文档同步批次（涉及 B1/B3 多处）。
- **裁决3**：NPC 功能 funcs 词表设计中文（.gen/npcs.json）与实现枚举（npcs.py）两套体系的历史原因，是否推进统一，避免后续 Agent 误读。

## 8. 切面健康度 + 一句话评语

**健康度：85/100**

**评语**：NPC与怪物体系规模饱满、技能引用零悬空、死 func 清理与解锁条件修正体现了持续的工程自律；主要风险集中在怪物 ID 跨表复用（一 ID 二怪）与设计文档表未随实现迭代同步，属可收敛的命名与文档一致性缺陷，不影响当前运行正确性。
