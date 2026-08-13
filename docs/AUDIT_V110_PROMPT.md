# dragonfall 全项目审计提示词（v110 审计 · deepseek harness）

鱼鱼 2026-08-14 发起：策划案仓库已迁入插件目录，要求用 deepseek harness 对《剑与魔法》(dragonfall) 做**全项目重新审计**（v109.3 之后的现状），查一切可疑问题——职业体系、属性机制、战斗结算、技能数据、数值平衡、世界观一致性、数据完整性、文档与代码对齐。

## 一、你是审计者

你是《剑与魔法》(dragonfall) 的维护者，先读插件根目录 AGENTS.md / DEVELOPMENT.md / dragonfall-game skill（若有）。审计结果要**严谨、可验证、拿代码证据**（鱼鱼数据准确性要求极高，不接受"看起来没问题"）。

## 二、仓库与运行环境（注意：策划案已迁址！）

- **代码仓库**：`C:\Users\yuyu\qqbot\data\plugins\dragonfall`（git，master；动工前 `git status` 确认干净）
- **策划案仓库**：`C:\Users\yuyu\qqbot\data\plugins\dragonfall\design\new_world`（**独立 git 仓库**，代码仓 .gitignore 已排除 design/；章节 01-31 + README + .gen/ 数据 + scripts/merge_docs.py）
- Python：`C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe`（`python tests/xxx.py` 单跑；**pytest 会 INTERNALERROR 不要用**）
- 全量回归：`python scripts/run_all_tests.py`（约 800s，124 文件；**run_all 有顺序污染假失败前科**——单跑甄别，拿不准连跑 5 次 + 抓失败详情）
- 关键文档：`docs/CLASS_TREE_V108_DESIGN.md`、`docs/HIDDEN_CLASSES_V107_DESIGN.md`、`docs/NUMERIC_DESIGN.md`、`docs/AUDIT_FINDINGS_v104.md`、`docs/AUDIT_V109_CLASSES_ATTRS.md`（**上一轮审计报告，本次要验证其修复未引入新问题**）
- 策划案对应章节：09_职业体系.md、12_技能体系.md、27_战斗规则引擎.md（其余章节按域对照）

## 三、背景（v107~v109.3 已上线内容，审计基线）

1. 伤害类型四层架构：普攻/dot/反伤/词条附加都声明类型；穿透（减防吃免伤）< pierce（无视防御吃免伤）< 真伤（绕过全减伤链、不触发吸血）
2. 19 职业（6 基础 + 13 隐藏）；职业树化 v108：隐藏职业=根基隐藏分支、修为继承（40/60/90 档）、血缘限制、『转职』统一路由
3. v109 大改：全职业改名（西幻化，如秘法法师/坚盾卫士/灵魂歌者）、斩杀线 35%、毒主题定调、拳师技能西幻化、占星运势/武圣连击/火之亲和/安眠曲睡眠/pierce 魔法分支/PVP 韧性对称、挡刀按召唤物 def 结算、毒 dot 5%/层、魔剑混合段法术吸血分账、面板 0 值隐藏、battle.py 技能名硬编码清零（数据驱动化）、别名转职按等级继承档位
4. v109.3 顺手根治：quest_deliver 彩蛋吞金币 bug（loot_gold 陈旧 player 覆盖 DB）
5. 历史教训：技能重名/歧义曾致 0 伤害事故；半死字段靠技能名硬编码曾"改名即断链"（已数据驱动化，验证是否彻底）

## 四、审计范围（10 个独立域，每个域出一个子报告）

| 域 | 范围 | 重点 |
|---|---|---|
| A 职业体系 | game/data/classes.py + 职业树文档 | 19 职业命名/档位名/定位/血缘映射；命名与世界观（西幻）冲突；近义名混淆；转职门槛与继承边界 |
| B 属性机制 | game/engine.py + 面板 | OPTIONAL_STATS 21 项：定义处→面板显示→战斗消费点三处一致；0 值不显示；属性来源链无死属性 |
| C 战斗伤害链 | game/battle.py + 策划案 27 章 | 穿透/pierce/真伤在每个减伤环节行为；真伤绕过全减伤链且不吸血；斩杀/吸血/反伤/暴击链路 |
| D 战斗机制 | game/battle_mech.py + battle.py | 毒爆/格挡反击/血魔法/召唤（挡刀按 def 结算+summon_power 加成）/睡眠/幸运一击/连击；每机制对照 27 章设计 |
| E 技能体系 | game/data/skills.py + skill_up.py + builds.py | SKILL_UP 全覆盖；技能名全局唯一性（resolve 歧义）；描述与实现一致性（数值/机制/文案）；被动注册与消费点 |
| F 数值平衡 | 裸装面板对比脚本 | 19 职业 Lv.40/60/90 面板对比；"隐藏职业面板略高但机制受限"哲学是否被破坏；成长曲线断裂；概率总和≠100% |
| G 数据完整性 | game/data/*.py + .gen/ + 数据库 | 引用完整性（技能/物品/怪物/地图/对话互相引用不悬空）；.gen 与代码数据同源；DB 表结构与迁移一致性 |
| H 世界观与策划案对齐 | 代码 vs design/new_world/*.md | 代码实现与策划案章节逐条对照；策划案该有而没有/不一致/过时；文档残留旧名（如圣辉骑士/牧师线） |
| I 命令与交互 | game/commands/*.py | 转职/面板/技能/重置命令文案与断链；别名解析；回执占位符；兜底文案可达性 |
| J 测试与回归 | tests/*.py + scripts/run_all_tests.py | 新测试质量（test_v109_2_*）；run_all 顺序污染点；假失败甄别；测试与实现脱节 |

## 五、并发要求（重点）

**允许并必须开很多并发子 agent 加快速度**——能开多少开多少（≥8 个，建议 10 域全并行）：

- 每个子 agent 独立负责一个域（上表 A-J），域间只读不写，互不干扰；共享大文件（battle.py/skills.py）可并行读
- 每个子 agent 自建**独立私有临时数据库**跑脚本验证（防共用测试库被并行 clean 互清导致假失败）
- 各域子 agent 输出独立子报告后，主 agent 汇总去重（跨域重复问题归主报告，注明两域交叉证据）
- 并行 patch 禁止——审计只读，一律不改代码

## 六、审计方法（按顺序）

1. `git status` 确认两仓库干净；读三份设计文档 + AUDIT_V109_CLASSES_ATTRS.md（上轮结论） + 对应策划案章节
2. 数据层脚本验证（python 单跑）：职业名/档位名唯一性、src_base 有效性、SKILL_UP 全覆盖、OPTIONAL_STATS 白名单、技能 resolve 歧义、血缘映射完整性、.gen 引用完整性
3. 机制层精读：battle.py 伤害链全路径（每类伤害过每道减伤）、battle_mech.py 各机制、engine.py 属性聚合
4. 数值层：Lv.40/60/90 裸装全职业对比脚本；技能 power/cd 分布；概率表求和
5. 每个疑点：先证据（文件:行号）→ 结论 → 建议；**不要直接改代码**，等鱼鱼拍板

## 七、交付物

1. 主审计报告：`docs/AUDIT_V110_FULL.md`（P0 致命/歧义、P1 明显缺陷、P2 优化、P3 建议；每条 `文件:行号:现象:影响:建议`）
2. 每域子报告：`docs/AUDIT_V110_<域>.md`（A-J 各一份，含验证脚本输出证据）
3. 命名/世界观问题完整清单与改名建议表（含引用面改动范围估算）——**只出清单与建议，改不改鱼鱼拍板**
4. 数值平衡对比表 + 机制验证结论表（每个机制：设计→实现→实测三列）
5. v109 修复项抽查结论：上一轮修的 P0/P1/P2/P3 是否真修复、有无引入回归

## 八、铁律

- 动工前两仓库 git status 干净；审计**只读**，零文件修改（连 docs 报告也不写——各 agent 把报告内容原样返回，由鱼鱼决定落盘）
- 出先证据后结论；拿不准的标记"待验证"并给出验证方法，不猜
- 命名/世界观/数值哲学问题：只列清单与建议，改不改由鱼鱼拍板
- 数据准确性：逐项核对求和/总额/概率总和；"看起来没问题"不算数
- 不要提交任何 git 变更；不要动 playtest 产物
