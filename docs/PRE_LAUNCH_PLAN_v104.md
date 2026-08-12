# v104 上线前全量审计 + 重练级计划（2026-08-12 鱼鱼拍板）

> 临时设计文档：分阶段完成上线前收尾。目标 = 不是"每次问都查出一堆 bug"，而是**系统性全量审计一次，把绝大多数 bug/断链/数值问题干掉再上线**。

## 阶段总览

| 阶段 | 内容 | 产出 | 完成判据 |
|---|---|---|---|
| 0 | 准备（删档已执行✅ / 重置 playtest 状态 / 建记忆机制） | 干净环境 | 全库 0 行 + state 重置 |
| 1 | **6 子 agent 并行全量审计**（只查不改） | 分级问题清单 P0-P3 | 6 份报告合入审计总表 |
| 2 | 分批复修（P0/P1 优先，P2/P3 攒批） | 修复 commit 系列 | 每批：测试绿 + 策划案同步 + 提交 |
| 3 | 测试覆盖率补强（目标尽可能 100%） | 补测 commit | 覆盖率报告 + 全量回归绿 |
| 4 | 上线前终检（删档确认 + 全量回归 + 边界抽查） | 终检报告 | 全部通过 |
| 5 | **6 角色重练级**（新 playtest 循环，带持久记忆） | 新角色练级实录 | 6 角色从 1 级推进 |

## 阶段 1：审计分工（4 轮 × 6 agent = 24 模块全覆盖）

> 鱼鱼拍板（2026-08-12）：**分多轮子 agent 审计**，一轮 6 个并行（max_concurrent_children=6），
> 全部模块拆细列出，每个模块独立完整提示词（见 `docs/AUDIT_AGENTS_v104.md`）。
> 每轮结束：主 agent 汇总报告 → 合入审计总表 → 再启动下一轮。4 轮全部完成后进入阶段 2 修复。

### 轮次安排

**第 1 轮：玩家与战斗**
- M01 玩家系统 | M02 战斗引擎 | M03 技能系统 | M04 组队系统 | M05 副本系统 | M06 野外怪物与掉落

**第 2 轮：装备物品与经济**
- M07 装备系统 | M08 物品与背包 | M09 商店与配货 | M10 锻造打造 | M11 强化附魔符文 | M12 经济与市场

**第 3 轮：生活副业与内容**
- M13 副业框架 | M14 采集挖掘 | M15 垂钓系统 | M16 烹饪炼金 | M17 宠物坐骑 | M18 成就称号公会

**第 4 轮：世界叙事与框架**
- M19 主线任务 | M20 支线任务 | M21 对话树与NPC | M22 地图移动 | M23 探索事件彩蛋 | M24 命令框架与持久化

### 模块与文件对照（完整清单）

| # | 模块 | 覆盖文件 |
|---|---|---|
| M01 | 玩家系统 | commands/player.py, data/classes.py, data/races.py, core/stats.py, core/race_talent_display.py, engine.py(属性/加点/升级部分), store/players.py |
| M02 | 战斗引擎 | game/battle.py, core/battle_conds.py, core/battle_mech.py, core/constants.py, commands/combat.py(战斗部分) |
| M03 | 技能系统 | data/skills.py, data/skill_up.py, data/core_resources.py, data/builds.py, combat.py(技能施放) |
| M04 | 组队系统 | commands/social.py(组队), store/social.py, 队伍/邀请/共享逻辑 |
| M05 | 副本系统 | commands/instance.py, data/instances.py, data/instance_stage_maps.py, store/battle_state.py, 副本战利品/停留/暗格 |
| M06 | 野外怪物与掉落 | data/monsters.py, data/hidden_monsters.py, data/monster_mods.py, core/monsters.py, core/drops.py, 野外刷怪逻辑 |
| M07 | 装备系统 | data/equipment.py, data/equip_roster.py, data/affixes.py, data/sets.py, data/stat_templates.py, core/affix.py, core/affix_effects.py, core/class_sets.py |
| M08 | 物品与背包 | data/items.py, core/item_templates.py, store/inventory.py, 背包/物品详情/使用命令 |
| M09 | 商店与配货 | data/shop.py, data/honor_shop.py, data/housing.py, economy.py(商店部分), 子区域配货 SHOP_SUBAREA_ITEMS |
| M10 | 锻造打造 | data/craft.py, core/craft.py, 图纸/学习/打造命令 |
| M11 | 强化附魔符文 | data/enhance.py, data/enchant.py, data/runes.py, core/enchant.py, core/runes.py, 强化/附魔/刻印命令 |
| M12 | 经济与市场 | commands/economy.py(经济部分), store/connection.py, 摆摊/市场/价格链/回收/每日任务 |
| M13 | 副业框架 | data/prof_config.py, store/professions.py, economy.py(副业命令), 8 副业激活/等级/每日任务/遗忘 |
| M14 | 采集挖掘 | data/gather.py, data/gather_pools.py, 采集/挖掘/矿点/材料池 |
| M15 | 垂钓系统 | data/fishing.py, core/fishing.py, 钓点/品质/收藏/饵料 |
| M16 | 烹饪炼金 | data/cooking.py, data/alchemy.py, core/food_effects.py, 食物/药水/配方/hot/buff |
| M17 | 宠物坐骑 | data/pets.py, data/mounts.py, core/pets.py, core/mounts.py, 宠物/蛋/技能/坐骑效果 |
| M18 | 成就称号公会 | data/achievements.py, data/titles.py, data/guild.py, data/factions.py, core/achievements.py, core/achievement_conds.py, core/title_conds.py, core/factions.py, 签到/编年史 |
| M19 | 主线任务 | data/quests.py(MAIN), store/quests.py, world.py(任务接取/交付/追踪) |
| M20 | 支线任务 | data/quests.py(SIDE), 告示牌/支线接取/交付 |
| M21 | 对话树与NPC | data/dialogues.py, data/npcs.py, data/wild_npcs.py, core/dialogue.py, core/dialogue_conds.py, core/hidden_cond.py, commands/talk_actions.py |
| M22 | 地图移动 | data/maps.py, data/subareas.py, data/roads.py, data/portals.py, core/maps.py, core/portals.py, world.py(移动/前往/城门/住宿/传送) |
| M23 | 探索事件彩蛋 | data/events.py, data/pois.py, data/poi_pools.py, data/props.py, data/rules.py, core/events.py, core/event_templates.py, core/world_event_templates.py, core/rule_engine.py, core/time_weather.py, core/wild.py, core/pois.py, store/props_use.py |
| M24 | 命令框架与持久化 | main.py, db.py, content.py, engine.py(全), commands/base.py, commands/_registry.py, commands/gm.py, commands/misc.py, store/(connection/players/inventory/quests/battle_state/stats/social/world/feedback/professions/props_use), data/_assembly.py, data/index.py, core/index.py |

> 完整 24 份独立提示词（公共框架 + 每模块定制审计点/边界场景/策划案对照）见 `docs/AUDIT_AGENTS_v104.md`。

### 审计维度（每个 agent 都要过）

1. **代码设计问题**：死代码/重复代码/魔法数字/硬编码/错误处理缺失/边界未覆盖/性能隐患/状态机漏洞
2. **bug**：功能失效、静默失败、状态不同步、数据损坏路径、异常抛出、并发/跨天/跨会话边界
3. **文案正确性**：错别字、描述与实机不符（desc 造假）、术语不一致、开发者术语/内部 ID 泄漏
4. **内容完整连贯**：引用断裂（掉落→材料→配方→商店全链）、断档（武器/装备等级断层）、死功能（有定义无获取途径）、获取途径画饼
5. **排版/信息完善**：面板格式（冒号/空格/每项一行）、信息缺失（缺数值/缺来源/缺提示）
6. **数值**：倒挂、失衡、成长曲线断裂、概率总和、价格链脱节（与 docs/NUMERIC_DESIGN.md、策划案对照）
7. **边界测试**：空参/越界序号/0 金币/残血/满背包/体力 0/跨天/重复操作/半角全角/免空格粘数字
8. **随机性/彩蛋**：概率实现正确、显示必须可触发、彩蛋可达

### 输出格式（每个 agent 统一）

```
## <模块> 审计报告
### P0 严重（崩溃/主线卡死/数据损坏）
- [文件:行号] 问题描述 | 复现方式 | 期望行为
### P1 bug
### P2 设计/体验问题
### P3 文案/排版
### 边界测试结果（逐条 ✅/❌）
### 策划案对照缺口（design/new_world/ 哪章该有而没有/不一致）
```

分级定义：
- **P0**：崩溃、主线/核心流程卡死、数据损坏、全服级 bug → 上线前必须修
- **P1**：功能 bug、明显失衡、断链 → 上线前应修
- **P2**：设计/体验优化、潜在风险 → 攒批修
- **P3**：文案/排版/小瑕疵 → 攒批修

## 阶段 5：重练级 6 角色配置（种族×职业全覆盖）

| ident | 角色名 | 种族 | 职业 | 定位 |
|---|---|---|---|---|
| main | 洛恩 | 人类 | 战士 | 主力推主线，坦克前排 |
| gm_alt1 | 艾莉娅 | 银月精灵 | 游侠 | 速度流，野外探索/采集 |
| gm_alt2 | 布罗尔 | 矮人 | 拳师 | 高防近战，锻造/挖掘 |
| gm_alt3 | 萨卡 | 兽人 | 牧师 | 治疗辅助，炼金/烹饪 |
| gm_alt4 | 妮可 | 半身人 | 刺客 | 高暴击，垂钓/探索 |
| gm_alt5 | 奥古斯都 | 龙裔 | 法师 | 高输出，附魔/符文 |

- 注册格式：`注册 <名字> <性别> <种族>`（性别：洛恩男/艾莉娅女/布罗尔男/萨卡女/妮可女/奥古斯都男）
- 6 职业全覆盖 = 各职业特色/技能/转职都有人实测；6 种族全覆盖 = 种族天赋正负面都有人实测

## 角色记忆持久化机制（鱼鱼要求：可压缩但不能每轮全遗忘）

- 文件：`scripts/playtest_memory_<ident>.md`（每角色一份）
- 结构（≤2000 字，超限强制压缩）：
  ```
  # <角色名> 记忆 v<N>
  ## 角色卡
  等级/经验/位置/金币/装备/技能/副业/任务进度（当前主线/支线）
  ## 冒险回忆（压缩版）
  关键事件、人物关系、世界观发现、去过的地方、踩过的坑
  ## 目标
  当前短目标 / 中期目标
  ## 最近 3 轮动态
  每轮追加 1-2 行，超过 3 轮合并进"冒险回忆"
  ```
- 主循环流程：第 1 步读全部记忆 → 派 agent 时注入各自记忆 → agent 汇报附带"记忆更新" → 主 agent 写回记忆文件（压缩）
- 删档/新角色：首轮创建空记忆文件，注册后写入角色卡

## 铁律（贯穿全程）

1. **策划案同步 = 与 git 提交同级别**：任何设计/数值/新内容改动，先同步 `C:\Users\yuyu\qqbot\design\new_world\` 对应章节（独立 git 仓库），顺序：策划案→代码→测试→双仓库提交；纯 bug/文案可不同步
2. **审计 agent 只查不改**：避免并发改码冲突；问题统一进清单，阶段 2 分批复修
3. **每批修复完跑相关测试 + 提交再动下一批**（git 铁律：替换前确认工作区干净）
4. **全量回归期间禁止并行跑测试/脚本**（test_game_data.db 污染）
5. **修完必须回写审计清单状态**（✅已修/❌打回），最后终检时清单全清
6. 输出/汇报用中文，格温口吻

## 审计 Agent 提示词模板（阶段 1 派发用，按模块替换 <模块> <文件清单>）

```
你是《剑与魔法》(dragonfall) 的【<模块>】审计子 agent。任务是**全量深度审计**，不是抽查。
只查不改：禁止修改任何代码/数据/文档，禁止提交 git，禁止重启服务。发现问题记录在报告里。

## 环境
- 插件根目录：C:\Users\yuyu\qqbot\data\plugins\dragonfall\
- 测试 Python：C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe（必须用它，系统 python 缺依赖）
- 只读验证允许：grep/读文件/跑单文件测试（python tests/test_xxx.py，跑完可能动 test_game_data.db，允许）/写临时脚本到 /tmp 或你自己目录（跑完删）
- ⚠️ 禁止跑 scripts/run_all_tests.py 全量（会与其他 agent 冲突）；禁止改 game/game_data.db

## 审计范围
<模块>，核心文件：
<文件清单>

## 审计维度（全部要过，逐条给结论）
1. 代码设计：死代码/重复/魔法数字/硬编码/错误处理缺失/边界未覆盖/状态机漏洞/资源泄漏
2. bug：功能失效、静默失败、状态不同步、数据损坏路径、异常、并发/跨天/跨会话边界、数值溢出
3. 文案：错别字、描述与实机不符、术语不一致、内部 ID/开发者术语泄漏（grep: cls_/sk_/rec_/mat_/毕业套）
4. 内容连贯：引用断裂（掉落→材料→配方→商店→用途全链）、等级断档、死功能（有定义无获取途径）、画饼（desc/source 说的渠道不存在）
5. 排版/信息：面板格式（「标签：值」冒号、数值 + 两侧空格、每项一行）、缺数值/缺来源/缺提示
6. 数值：倒挂、失衡、概率总和≠100%、价格链脱节、成长曲线断裂——对照 docs/NUMERIC_DESIGN.md 和 C:\Users\yuyu\qqbot\design\new_world\ 对应章节
7. 边界测试：空参/越界序号/0金币/残血/满背包/体力0/跨天/重复操作/半角全角/免空格粘数字/重复点击——能实测的用单文件测试或小脚本验证，不能实测的标注"静态判断"
8. 随机性/彩蛋：概率实现正确、显示必须可触发（展示的元素都能互动）、彩蛋可达性

## 输出格式（严格按此）
## <模块> 审计报告
### P0 严重（崩溃/主线卡死/数据损坏）
- `文件:行号` 问题描述 | 复现方式 | 期望行为
### P1 bug（功能错误/明显失衡/断链）
### P2 设计/体验（优化项/潜在风险）
### P3 文案/排版（错别字/格式）
### 边界测试结果（每条 ✅/❌/⚠️静态判断 + 一句话）
### 策划案对照缺口（design/new_world/ 哪章该有而没有/不一致）

## 质量要求
- 宁多勿漏：拿不准的进 P2 并标注"待确认"
- 每条必须带文件:行号 或 数据 key，不许空口说
- 先通读全部文件再写报告，不许只看一眼就交差
- 验证过的结论标 ✅（写你怎么验的），没验的标 ⚠️（写为什么没验）
- 最后给一句话总结：本模块整体健康度（优/良/中/差）+ 上线前必改项数量
```

## 阶段 5 练级 Agent 提示词模板（每角色一份，注入各自记忆）

```
你是《剑与魔法》的玩家【<角色名>】（<种族>·<职业>），在这个 QQ 文字 RPG 世界里真实生活。
你有自己的记忆（见下方"你的记忆"），你记得过去的冒险，角色在成长。用真实玩家的方式游玩，
不要功利性刷验证，不要脚本化操作。

## 你的记忆（每轮开始注入，这是你唯一的记忆来源）
<playtest_memory_<ident>.md 全文>

## 环境
- 工作目录：C:\Users\yuyu\qqbot\data\plugins\dragonfall\scripts
- 操作方式：`python loopback_client.py <ident> <游戏指令>`（发指令等回复 2-5s）；`python loopback_client.py <ident> --tail 5` 看最近输出；`<ident> --clear` 清空
- ⚠️ 每步操作之间先看回复再决定下一步（像真人一样思考），禁止一次性连发多条指令
- 游戏指令速查：角色/属性/背包/技能/任务/地图/前往 <序号>/探索/攻击/防御/商店/购买 <n>/出售 <n>/装备 <n>/加点 <属性>/技能学习 <名称>/锻造 <n>/学习图纸/住宿/找 <NPC>/对话 <序号>/垂钓/采集/挖掘/炼金/烹饪/强化/附魔

## 你的游戏风格（人设）
<角色人设：如 洛恩=稳重可靠的战士，钱先花在盾和剑上；艾莉娅=精灵游侠，喜欢探索野外和采集；……>

## 本轮要做的事（优先级从高到低）
1. 继续你的目标（见记忆"目标"），推进等级/主线/支线
2. 像真人玩家：打怪掉落→卖材料→买装备→做装备→升级加点→学技能→探索新地图→找 NPC 聊天→试副业
3. 体验所有能体验的：新地图、新副本、新副业、新技能、商店货架、任务对话
4. 发现异常（bug/文案/数值不合理/卡死/边界问题）→ 记录：指令+现象+期望，不改代码
5. 体力低就回城住宿/吃食物，残血不硬刚（真人逻辑）

## 汇报格式（中文）
1. 本轮经历（3-5 句，像冒险日志）
2. 进度快照：等级/经验%/位置/金币/当前装备/技能/副业/任务
3. 发现的问题（指令/现象/期望，没有就写"无"）
4. 记忆更新建议（给主 agent 的压缩版：新增的关键事件/变化/教训，≤150 字）
```

## 主循环 Prompt 优化要点（相对旧版 4365febe407f）

1. 第 1 步增加：读 6 个 playtest_memory_<ident>.md，若角色未注册（库空/首次）先批量注册 6 新角色（注册 <名字> <性别> <种族>）
2. 派 agent 时：注入各自记忆全文 + 角色人设 + 审计清单未验证项（把阶段 1 的问题当验证线索）
3. 第 3 步审阅：agent 汇报的"记忆更新建议"合并写回记忆文件（压缩到 ≤2000 字）
4. 修 bug 流程不变（紧急当场修/非紧急攒批），但**改完必须回写审计清单状态**
5. 每轮边界专项：从"边界测试清单"轮换 2-3 项实测（如本轮测空参/下轮测跨天）
6. 上线前 playtest 目标 = 全 6 角色把主线推到当前最新进度 + 全部支线/副本/副业至少各体验一次

## 阶段 3 覆盖率补强思路

- 现有测试体系：tests/ 四层（data/core/store/commands）+ test_vXX 回归
- 补测方向（审计后按缺口定）：命令矩阵全覆盖、边界参数、对话树全 NPC 可达性、副本全 22 个、副业全 8 个升级路径、装备全名册加载
- 目标：能覆盖的尽可能 100%（静态数据 + 命令 + 核心引擎），不可测的（QQ 平台交互）文档化
