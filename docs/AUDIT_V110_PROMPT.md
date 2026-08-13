# dragonfall 全项目全模块审计提示词（v110 审计 · deepseek harness）

鱼鱼 2026-08-14 发起：策划案仓库已迁入插件目录，要求用 deepseek harness 对《剑与魔法》(dragonfall) 做**全项目全模块审计**（v109.3 之后的现状）——不是只查职业/战斗，而是**所有模块**：数据层、机制层、命令层、存储层、测试、文档、策划案，一个不漏。

## 一、你是审计者

你是《剑与魔法》(dragonfall) 的维护者，先读插件根目录 AGENTS.md / DEVELOPMENT.md。审计结果要**严谨、可验证、拿代码证据**（鱼鱼数据准确性要求极高，不接受"看起来没问题"）。

## 二、仓库与运行环境（注意：策划案已迁址！）

- **代码仓库**：`C:\Users\yuyu\qqbot\data\plugins\dragonfall`（git，master；动工前 `git status` 确认干净）
- **策划案仓库**：`C:\Users\yuyu\qqbot\data\plugins\dragonfall\design\new_world`（**独立 git 仓库**，代码仓 .gitignore 已排除 design/；01-31 章 + README + .gen/ + scripts/merge_docs.py）
- Python：`C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe`（`python tests/xxx.py` 单跑；**pytest 会 INTERNALERROR 不要用**）
- 关键文档：`docs/CLASS_TREE_V108_DESIGN.md`、`docs/HIDDEN_CLASSES_V107_DESIGN.md`、`docs/NUMERIC_DESIGN.md`、`docs/AUDIT_FINDINGS_v104.md`、`docs/AUDIT_V109_CLASSES_ATTRS.md`（**上轮审计报告，验证其修复未引入新问题**）
- 代码规模：game/ 下 data（50+ 数据模块）、core（25+ 机制模块）、commands（9 文件 ~1.7 万行）、store（11 存储模块）、battle.py/engine.py/db.py/content.py；tests/ 128 个测试文件

## 三、背景（v107~v109.3 已上线，审计基线）

1. 伤害类型四层架构：普攻/dot/反伤/词条附加都声明类型；穿透 < pierce < 真伤（绕过全减伤链、不触发吸血）
2. 19 职业（6 基础 + 13 隐藏）；职业树化：修为继承（40/60/90 档）、血缘限制、『转职』统一路由
3. v109 大改：全职业西幻改名、斩杀线 35%、占星运势/武圣连击/火之亲和/安眠曲睡眠/pierce 魔法分支/PVP 韧性对称、挡刀按召唤物 def 结算、毒 dot 5%/层、魔剑法术吸血分账、面板 0 值隐藏、battle.py 技能名硬编码清零（数据驱动化）、别名转职按等级继承档位
4. v109.3 顺手根治：quest_deliver 彩蛋吞金币 bug（loot_gold 陈旧 player 覆盖 DB）
5. 历史教训：技能重名致 0 伤害事故；半死字段靠技能名硬编码曾"改名即断链"；run_all 顺序污染假失败；并行测试互清库；v104 审计"done 标了但实际没做"（判定必须 grep 证据）

## 四、审计范围（30 个独立域，每域一个子 agent、一份子报告）

| 域 | 模块（game/ 下） | 重点审计项 | 策划案对照 |
|---|---|---|---|
| D01 职业体系 | data/classes.py、commands/player.py 转职段 | 19 职业命名/档位名/定位/血缘映射/继承边界/转职门槛；近义名混淆；西幻世界观冲突 | 09_职业体系.md |
| D02 属性引擎 | engine.py 全量 | 每个属性：定义→面板显示→战斗消费点三处一致；0 值不显示；来源链无死属性；聚合顺序 | 07/27 章 |
| D03 战斗结算链 | battle.py 全量 | 四层伤害类型过每道减伤（防御/免伤/抗性/buff）；真伤绕过全链且不吸血；暴击/吸血/反伤/斩杀/dot 链路 | 27_战斗规则引擎.md |
| D04 战斗机制 | core/battle_mech.py、rule_engine.py | 毒爆/格挡反击/血魔法/召唤挡刀/睡眠/幸运一击/连击/灼烧/冰冻/眩晕等**全部**机制：设计→实现→实测 | 27 章 |
| D05 技能体系 | data/skills.py、skill_up.py、builds.py | SKILL_UP 全覆盖；技能名全局唯一（resolve 歧义）；描述与实现一致（数值/机制/文案）；被动注册与消费点；技能树/领悟链 | 12_技能体系.md |
| D06 装备词条套装 | data/equipment.py、equip_roster.py、affixes.py、core/affix.py、affix_effects.py、sets.py、runes.py、enchant.py、enhance.py、stat_templates.py、class_sets.py | 装备名册/词条池/套装效果/符文/附魔/强化/属性模板；词条描述与实际效果一致；折算与触发注册无双算 | 10_装备体系.md |
| D07 物品材料道具 | data/items.py、core_resources.py、props.py、store/props_use.py | 物品引用完整性（配方/掉落/商店/任务引用不悬空）；品质/堆叠/价格链；道具效果实现 | 13_物品与材料体系.md |
| D08 商店与经济 | data/shop.py、honor_shop.py、commands/economy.py、data/cmd_config.json 商店段 | 商店配货/价格链/子区域独立配货；买卖价差；经济循环（反通胀"必掉=不值钱"）；荣誉商店 | 30_交易与市场系统.md |
| D09 怪物与掉落 | data/monsters.py、monster_mods.py、hidden_monsters.py、core/monsters.py、core/drops.py | 怪物属性/技能/掉落表；Boss 机制（召唤真实体）；掉落率合理性（按一天刷几个反推）；概率总和=100% | 04_怪物图鉴.md |
| D10 地图世界 | data/maps.py、roads.py、portals.py、subareas.py、pois.py、poi_pools.py、instance_stage_maps.py、world.py、core/maps.py、pois.py、portals.py | 地图连接（城镇星形/野外线性/城门规则）；传送/道路闭环；POI 可触发；子区域怪物等级；定居点规模与出口匹配 | 02_地图系统.md |
| D11 副本组队 | data/instances.py、commands/instance.py、data/events.py | 副本配置/阶段/奖励；组队流程；入口/传送；难度哲学（不降数值升装备） | 29_副本与组队系统.md |
| D12 任务系统 | data/quests.py、store/quests.py、commands/world.py+misc.py 任务段 | 主线/支线/日常链完整（audit_dialog_quest_pending.py）；任务对话式接交；奖励与实际入账一致（防 loot_gold 类陈旧对象）；任务链断链 | 05/06 章 |
| D13 NPC 与对话 | data/npcs.py、wild_npcs.py、dialogues.py、core/dialogue.py、dialogue_conds.py、commands/talk_actions.py、events.py | NPC 随机性四件套（酱油）/功能 NPC 永不随机；对话树完整；选项条件可达；导师教学链；场景元素按场所匹配 | 03_NPC群像.md + 13_场景氛围.md |
| D14 副业体系 | data/gather.py、gather_pools.py、craft.py、cooking.py、alchemy.py、fishing.py、prof_config.py、store/professions.py | 采集/挖掘/锻造/烹饪/炼金/垂钓全链；配方/产出/疲劳；图纸稀缺走生活渠道不走战斗；掉率按日反推 | 19_副业体系详案.md |
| D15 宠物召唤 | data/pets.py、summons.py、core/pets.py | 宠物获取/成长/技能；召唤物（骷髅海数量流/兽王质量流）；挡刀/死亡契约；属性继承 | 24_宠物与伙伴系统.md |
| D16 坐骑 | data/mounts.py、core/mounts.py | 坐骑获取/速度/效果；与地图移动集成 | 31_坐骑系统.md |
| D17 家园 | data/housing.py | 房产购买/装修/功能；价格数值 | 25_房产与家园系统.md |
| D18 公会国战势力 | data/guild.py、factions.py、core/factions.py、commands/social.py 公会段 | 公会功能/权限/贡献；势力关系；国战流程与奖励 | 11_国战与公会.md |
| D19 成就称号 | data/achievements.py、titles.py、core/achievement_conds.py、achievements.py、title_bonus.py、title_conds.py | 成就条件可达性；称号效果实现；奖励入账；"done 但没做"检查 | 14_成就与称号.md |
| D20 PVP 红名荣誉 | commands/combat.py PVP 段、core/stats.py PVP 部分、data/honor_shop.py | PVP 快照完整性（18 项属性）；韧性对称；红名惩罚；荣誉获取与消费；跨服/同服 | 26_PVP与红名系统.md |
| D21 种族天赋 | data/races.py、core/race_talent_display.py、stat_templates.py 种族段 | 种族天赋实际生效；显示与效果一致；出生选择链 | 08_种族体系.md |
| D22 玩家成长存储 | store/players.py、stats.py、inventory.py、core/stats.py | 升级曲线/属性成长；经验获取；背包容量/堆叠；存档字段与迁移一致性；skill_levels/重置 | 07_成长与玩法.md |
| D23 数据库层 | db.py | 表结构/索引/迁移（改表 5 处检查：CREATE/ALTER/update_player 白名单/get_player 解析/迁移 defaults）；数据一致性约束 | — |
| D24 命令路由交互 | commands/_registry.py、base.py、cmd_config.json | 全部命令注册/别名/歧义；文案与兜底；裸数字快捷操作；回执占位符；『找』NPC 指路 | 23_指令系统与交互设计.md |
| D25 GM 与调试 | commands/gm.py、core/hidden_cond.py | GM 命令安全（权限/白名单/滥用面）；隐藏条件可达性 | — |
| D26 内容装配 | content.py、data/_assembly.py、index.py、core/world_event_templates.py、time_weather.py | 装配完整性（模块注册无遗漏）；世界事件/时间天气系统；索引一致性 | README.md |
| D27 战斗辅助机制 | core/battle_conds.py、food_effects.py、event_templates.py、class_sets.py | 战斗条件触发；食物/药水效果；事件模板；职业套装联动；**skill 名硬编码残留扫描**（改名即断链模式） | 12/27 章 |
| D28 测试质量 | tests/ 128 文件、scripts/run_all_tests.py | 测试与实现脱节；假失败/顺序污染点；新测试质量；"单跑全绿≠没问题"；断言有效性 | — |
| D29 文档一致性 | docs/ 全部 | docs 与代码现状脱节；旧名残留（圣辉骑士/牧师线/斗气）；v109 修复项抽查（是否真修复、有无回归） | 全章 |
| D30 策划案完整性 | design/new_world/ 01-31 | 策划案章节与代码实现逐条对照：该有而没有/不一致/过时；策划案内部自洽（章节互引不悬空）；.gen 数据与代码同源 | 全章 |

## 五、并发要求（重点）

**允许并必须开很多并发子 agent 加快速度**——能开多少开多少（建议 30 域全并行，一次拉满）：

- 每个子 agent 独立负责一个域（上表 D01-D30），域间只读不写、互不干扰；共享大文件（battle.py/skills.py/engine.py）可并行读
- **测试库隔离铁律**：每个子 agent 自建**独立私有临时数据库**跑脚本/单测验证（共用测试库被并行 clean 互清 = 假失败，已踩过）；**只有 D28 域可跑一次 run_all_tests.py（后台）**，其他域一律单跑自己域的 tests/ 文件
- 各域子 agent 输出独立子报告后，主 agent 汇总去重（跨域重复问题归主报告，注明两域交叉证据）
- **并行 patch 禁止**——审计只读，一律不改代码、不写文件（报告内容原样返回）

## 六、审计方法（每域通用）

1. 确认 git status 干净（只读）；读本域对应策划案章节 + 相关设计文档 + 上轮审计报告中本域结论
2. 数据层脚本验证（python 单跑，独立临时库）：唯一性/引用完整性/覆盖全量（SKILL_UP、OPTIONAL_STATS、resolve、映射表）
3. 机制层精读：本域每个机制走完整代码路径（定义→面板→消费点），拿文件:行号证据
4. 数值层：本域数值表核对（概率总和=100%、价格链、成长曲线、掉率反推）
5. 每个疑点：先证据（文件:行号）→ 结论 → 建议；**不要直接改代码**，等鱼鱼拍板

## 七、交付物

1. 主审计报告：`docs/AUDIT_V110_FULL.md`（P0 致命/歧义、P1 明显缺陷、P2 优化、P3 建议；每条 `文件:行号:现象:影响:建议`）
2. 每域子报告：`docs/AUDIT_V110_D<域号>.md`（D01-D30 各一份，含验证脚本输出证据）
3. 命名/世界观问题完整清单与改名建议表（含引用面改动范围估算）——**只出清单与建议，改不改鱼鱼拍板**
4. 数值平衡对比表（跨域汇总）+ 机制验证结论表（每个机制：设计→实现→实测三列）
5. v109 修复项抽查结论：上一轮修的 P0/P1/P2/P3 是否真修复、有无引入回归
6. 全模块覆盖确认表：30 域 × 检查项完成状态（防"漏域"）

## 八、铁律

- 动工前两仓库 git status 干净；审计**只读**，零文件修改（连 docs 报告也不写——各 agent 把报告内容原样返回，由鱼鱼决定落盘）
- 出先证据后结论；拿不准的标记"待验证"并给出验证方法，不猜
- 命名/世界观/数值哲学问题：只列清单与建议，改不改由鱼鱼拍板
- 数据准确性：逐项核对求和/总额/概率总和；"看起来没问题"不算数；"done"必须有代码证据（grep/运行输出）
- 不要提交任何 git 变更；不要动 playtest 产物
