# v104 审计 Agent 提示词全集（24 模块）

> 配套 `docs/PRE_LAUNCH_PLAN_v104.md` 阶段 1。每个模块一份完整提示词，派发时按此文件逐字使用。
> 拼装方式：**公共框架**（第一部分）+ **模块卡**（对应 M 编号）= 该 agent 的完整提示词。
> 主 agent 派发时把两部分拼成一条 prompt 发给子 agent。

---

## 〇、公共框架（所有 24 个 agent 通用，拼在模块卡之前）

```
你是《剑与魔法》(dragonfall) 的【<模块名>】审计子 agent。任务是全量深度审计，不是抽查。
你只负责这一个模块，必须把这个模块的每个文件、每条数据、每条命令路径都过一遍，不许跳步。

## 铁律
1. 只查不改：禁止修改任何代码/数据/文档，禁止 git commit，禁止重启服务，禁止动 game/game_data.db
2. 禁止跑 scripts/run_all_tests.py 全量回归（其他 agent 并行会污染 test_game_data.db）
3. 允许：grep/读文件/跑单个测试文件（python tests/test_xxx.py）/写临时脚本到 scripts/tmp_<你的模块>_audit.py（审计完删除）
4. 测试 Python：C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe（必须用它，系统 python 缺依赖）
5. 插件根目录：C:\Users\yuyu\qqbot\data\plugins\dragonfall\
6. 策划案目录：C:\Users\yuyu\qqbot\design\new_world\（对照文档，只读）

## 审计维度（8 个维度全部要过，每个维度给出结论）
1. 代码设计：死代码/重复逻辑/魔法数字/硬编码/错误处理缺失/边界未覆盖/状态机漏洞/性能隐患
2. bug：功能失效、静默失败（返回 False 无提示）、状态不同步、数据损坏路径、异常抛出、并发/跨天/跨会话边界
3. 文案正确性：错别字、描述与实机行为不符（desc 造假）、术语不一致（垂钓≠钓鱼、锻造≠打造、挖掘≠采矿）、
   内部 ID/开发者术语泄漏（grep 黑名单：cls_/sk_/rec_/mat_/i_stone/毕业套/测试）
4. 内容完整连贯：引用断裂（掉落→材料→配方→商店→用途全链必须闭环）、等级断档、死功能（有定义无获取途径）、
   画饼（desc/source 承诺的渠道不存在）
5. 排版/信息完善：面板「标签：值」冒号格式、数值 + 两侧空格、每项单独一行、缺数值/缺来源/缺操作提示
6. 数值：倒挂（成本>售价/低等级>高等级）、概率总和≠100%、价格链脱节、成长曲线断裂、与 docs/NUMERIC_DESIGN.md 及策划案不符
7. 边界测试：空参数/越界序号/0 金币/残血/满背包/体力 0/跨天/重复操作/半角全角/免空格粘数字/连点——能实测的
   用单文件测试或临时脚本验证，不能实测的标注"静态判断"
8. 随机性/彩蛋：概率实现正确、显示的元素必须可触发（展示=可交互）、彩蛋可达性、日期哈希确定性

## 输出格式（严格按此）
## <模块名> 审计报告
### P0 严重（崩溃/主线卡死/数据损坏/全服级）
- `文件:行号` 问题 | 复现方式 | 期望行为
### P1 bug（功能错误/明显失衡/断链）
### P2 设计/体验（优化项/潜在风险/待确认）
### P3 文案/排版（错别字/格式/术语）
### 边界测试结果（逐条 ✅/❌/⚠️静态判断 + 一句话说明）
### 策划案对照缺口（design/new_world/ 对应章节：该有而没有/不一致/过时）
### 总结
- 本模块整体健康度（优/良/中/差）
- 上线前必改项数量（P0+P1）
- 一句话：本模块最值得修的一件事

## 质量要求
- 宁多勿漏：拿不准的进 P2 标"待确认"
- 每条必须带文件:行号 或 数据 key，不许空口说
- 先通读全部文件再写，不许只看一眼交差
- 验证过的标 ✅（写你怎么验的），没验的标 ⚠️（写为什么没验）
- 全模块统计：文件数/命令数/数据条数（如配方数/装备数/事件数）先报数，证明你摸完了
```

---

## M01 玩家系统

```
<公共框架>

## 模块卡 M01：玩家系统
### 范围
注册/属性面板/加点/升级/种族天赋/角色守卫/初始化/职业初始技能

### 文件清单（全部要读）
- game/commands/player.py
- game/data/classes.py
- game/data/races.py
- game/core/stats.py
- game/core/race_talent_display.py
- game/engine.py（属性计算/加点/升级经验部分）
- game/store/players.py
- game/db.py（players 表相关）

### 定制审计点
1. 注册流程：格式解析（注册 <名字> <性别> [种族]）、旧格式兼容、非法输入（空名/重名/无性别/种族不存在）、
   初始属性是否乘种族倍率（历史 bug：银月精灵 150/142 血量溢出）
2. 属性面板：生命/魔力当前值与上限一致性、4 维属性加点、战斗属性（攻/防/暴击/闪避/速度）计算全链路、
   PCT_STATS（crit/dodge）不被 int() 截断、来源展示（基础/装备/天赋/词条）总账 = 面板总值
3. 加点：负数/超上限/非法属性名/0 点/点满后继续加
4. 升级：exp_to_next 曲线（60*lv^1.45 超线性）、升级广播、属性成长、技能点发放、装备等级需求联动
5. 种族天赋：6 种族正负面全实现（人类成长-2%/精灵 HP-5% 等）、race_neg 负系数结算、同属性不叠加取高
6. 守卫：@require_player() 覆盖全部玩家指令、注册提示 REGISTER_HINT 唯一常量、无角色/战斗中/副业中拦截顺序
7. 存档：players 表字段完整性（level/exp/class_name/race/attributes/equipment/cur_map/cur_subarea…）、
   JSON 字段序列化/反序列化、迁移补列

### 边界场景（优先实测）
- 注册 0 长度名字/纯空格名字/超长名字（50 字）
- 加点负数：`加点 力量 -1`？非法值？
- 注册已存在角色名
- 新手初始金币/装备是否够活过 1-3 级
- 种族中文名 vs ID 输入（注册 银月精灵 还是 精灵？）

### 策划案对照
- design/new_world/08_种族.md（种族天赋表）、09_职业.md、07_成长玩法.md（成长曲线）
```

---

## M02 战斗引擎

```
<公共框架>

## 模块卡 M02：战斗引擎
### 范围
回合制战斗全流程：伤害计算/暴击/闪避/速度/先手/buff/DOT/护盾/叠层/连击/额外行动/被动/战斗日志/胜负结算

### 文件清单（全部要读）
- game/battle.py
- game/core/battle_conds.py
- game/core/battle_mech.py
- game/core/constants.py
- game/core/food_effects.py
- game/commands/combat.py（战斗指令部分：攻击/防御/技能/使用道具/逃跑/战斗日志）

### 定制审计点
1. 伤害公式：calc_damage 去随机口径、攻击-防御关系、variance 范围、暴击倍率、无视防御（pierce）、
   元素增伤/减伤（_affix_dmg_mult 链：词条→食物→药水倍率是否都生效）
2. 速度/先手：spd 计算、额外行动（连击/速度触发）是否结算 hot/被动、回合推进逻辑（历史 bug：round 双重递增）
3. 状态系统：buff 3 回合取高不叠层、hot 覆盖制、护盾（数值池/词条取高/符文加法）、DOT/冻结、
   mech_stacks 叠层上限（MECH_STACK_MAX）与战斗结束清层
4. 被控状态：眩晕/冻结时结算规则（hot 是否回、防御是否生效）、p_defending 状态写回（历史 bug：防御从未生效）
5. 战斗日志：全角/半角统一（＋ vs +）、日志完整性（每个动作都有对应日志）、Boss 特殊行动日志
6. 胜负结算：击杀经验/掉落/升级触发、战败回城（回城点正确）、同归于尽判定、战斗销毁路径
7. 战斗内使用道具：药水/食物回合数、tpl_mana 回显、战斗外使用与战斗内使用行为区分
8. 战斗状态持久化：battle_state 表读写、断线/超时恢复、副本内外战斗差异

### 边界场景（优先实测）
- 0 攻击打高防（伤害下限是否为 1）
- 满血时使用回血道具（是否浪费/报错）
- 战斗中使用不存在的道具序号
- 逃跑失败后还能继续操作
- 被眩晕时防御/使用道具（是否被正确拦截）
- 暴击/闪避概率极端值（100% 暴击是否必暴）

### 策划案对照
- design/new_world/12_技能v2.1.md、20_装备词条.md、16_品质垂钓.md（食物药水数值锚点）
```

---

## M03 技能系统

```
<公共框架>

## 模块卡 M03：技能系统
### 范围
技能数据/技能学习/升级/核心资源消耗/连招派生/条件触发/团队技能/CD/技能面板展示

### 文件清单（全部要读）
- game/data/skills.py
- game/data/skill_up.py
- game/data/core_resources.py
- game/data/builds.py
- game/commands/combat.py（技能施放/技能列表/技能学习）
- game/core/battle_conds.py（技能条件）
- game/engine.py（技能学习成本/伤害系数）

### 定制审计点
1. 技能表完整性：6 职业 × 基础 14 + 分支 20 对称性（21 章三转体系）、命名黑名单
   （灭世/弑神/虚空/血怒/屠戮/金身/气功等 0 命中）、团队技能每职业 ≥1
2. 技能三形态：基础/🔄派生/⚡条件 实现正确性（条件判定、触发时机、层数门槛）
3. 核心资源：CORE_RESOURCES 表、res_cost 消耗、终结技双耗、资源获取（回合恢复/攻击获取）、
   普通技能是否漏耗蓝（历史 bug：战士/刺客普通技免费无限放）
4. 技能升级：skill_up 表每技能独立 p/c/m/l 配置、覆盖率（无漏配）、升级效果实际生效
5. 技能学习：学习成本公式、等级门槛、前置技能、TUTOR_SKILLS 专属技能（隐藏职业）、
   技能点来源与上限、重复学习拦截
6. 连招/派生：mech 机制（连击 multi/处决/追击等）与 mech_val 对应数值、连击等效威力 = power×multi
7. 技能面板：列表分页、标签（<物理><狂暴>）、等级显示 [Lv.0/5]、描述与实机一致
8. 数值铁律：分支 tier1 Lv.32 等效 ≥ 基础 Lv.30×0.95、武器类型特色加成固定值而非百分比

### 边界场景（优先实测）
- 学习无技能点/等级不足技能
- 技能升级到满级后继续升级
- 施放无蓝技能（拦截提示）
- 隐藏职业技能学习入口
- 技能列表页码越界

### 策划案对照
- design/new_world/12_技能v2.1.md、21_转职体系.md、09_职业.md
```

---

## M04 组队系统

```
<公共框架>

## 模块卡 M04：组队系统
### 范围
组队创建/邀请/加入/退出/解散、队伍状态、组队战斗（野外+副本）、共享收益、挂机保护

### 文件清单（全部要读）
- game/commands/social.py（组队部分）
- game/store/social.py
- game/commands/instance.py（组队开本相关）
- game/commands/combat.py（组队战斗相关）
- game/engine.py（队伍加成/人数缩放）

### 定制审计点
1. 组队流程：创建/邀请/接受/拒绝/退出/踢人/解散全链路状态机（pending/active）、重复邀请、
   跨地图组队、离线成员处理
2. 队伍上限：max_players 校验、满员拦截、队长转移
3. 组队战斗：野外组队战斗是否生效（历史结论：仅副本生效——文案是否说清楚）、
   副本人数缩放（+50%/人 精英缩放）、Boss hp_mult 超员人系数
4. 挂机保护：INSTANCE_TIMEOUT 行动超时（120s→60s）、自动防御、超时后恢复、组队挂机卡死（历史 bug：O32）
5. 收益分配：经验/金币/掉落如何分、队长与队员差异、拾取归属
6. 队伍与副本：队伍构成校验（开本拦截报队伍构成）、队长开本/队员开本、离队后副本状态
7. 组队指令：邀请/同意/拒绝正则、免空格粘参数、队伍面板展示（成员/等级/职业/位置）

### 边界场景（优先实测）
- 自己邀请自己
- 满员队伍邀请
- 邀请不存在的玩家/离线玩家
- 队长退出后队伍是否解散/移交
- 战斗中退出队伍（状态残留？）

### 策划案对照
- design/new_world/07_成长玩法.md（组队）、11_国战公会.md（公会）
```

---

## M05 副本系统

```
<公共框架>

## 模块卡 M05：副本系统
### 范围
22 副本全流程：开本（人数/等级/队伍构成校验）、阶段推进、Boss 机制、通关/失败、战利品/停留搜刮/暗格、
超时/退出、副本内状态持久化

### 文件清单（全部要读）
- game/commands/instance.py
- game/data/instances.py
- game/data/instance_stage_maps.py
- game/store/battle_state.py
- game/battle.py（副本战斗集成）
- game/commands/world.py（副本入口相关）

### 定制审计点
1. 副本数据完整性：22 副本全配齐（id/名称/等级区间/人数配置/子区域/阶段地图/Boss/掉落）、
   策划案 22 副本 vs 代码实例数一致、每副本 Boss 存在且数值合理
2. 开本校验：min_level/max_players/min_players、队伍构成提示（历史 bug：O17 只报队友名）、
   0 血进本拦截（#393）、弹性副本单人开本逻辑（哥布林营地 min_players<=1 永远单人 bug）
3. 阶段推进：_find_stage_poi/守卫跨层兜底、通关判定（Boss 击杀/同归于尽）、失败=直接销毁+文案、
   通关停留搜刮（clear_battle 语义）、『离开副本』命令、30 分钟超时
4. Boss 机制：mech 多机制（shield/phase/stacks/reflect/召唤）、召唤实体（e_minions 挡刀+出手）、
   Boss 血条/日志显示、人数缩放 hp_mult
5. 战利品：通关金币 30%+材料（防通胀核算 0.26 只怪/人）、暗格 20%（首通 50%）、宝箱分层
   （图纸残页 50%/符文 30%/材料 20%）、首通判定顺序（set_achievement 前）
6. 副本内状态：战斗状态持久化（round/成员 HP/护盾/buff）、断线恢复、成员死亡处理、复活机制
7. 副本指令：『副本』列表/『副本 <名>』开启/『离开副本』/副本内移动/搜刮/暗格交互

### 边界场景（优先实测）
- 低等级开高等级副本（拦截）
- 1 人开 4 人本（拦截/提示）
- 副本内全体阵亡（销毁+回城）
- 通关后停留再打（已通关标记）
- 超时未操作（自动踢出/防御）
- 副本内使用传送/回城卷轴

### 策划案对照
- design/new_world/02_地图v3.md（22 副本清单）、04_怪物.md（Boss）、17_主线（副本卡点）
```

---

## M06 野外怪物与掉落

```
<公共框架>

## 模块卡 M06：野外怪物与掉落
### 范围
怪物数据/等级曲线/精英与 Boss/隐藏怪物/怪物修饰/掉落表/掉落概率/战利品

### 文件清单（全部要读）
- game/data/monsters.py
- game/data/hidden_monsters.py
- game/data/monster_mods.py
- game/core/monsters.py
- game/core/drops.py
- game/commands/combat.py（掉落结算/拾取）
- game/engine.py（怪物属性）

### 定制审计点
1. 怪物数据完整性：全部怪物 id/name/等级/属性/经验/掉落齐全、等级与所在地图匹配
   （野外怪等级校准：diff≤-3 已修，jitter ±1）、24 城 58 野每图有怪
2. 掉落表：掉落概率总和 ≤100%、掉落材料 resolve 中文名→mat_ ID（历史 bug：直接查表恒 False 静默消失）、
   掉落闭环（掉落物在材料表存在、能进配方/商店/用途）
3. 精英/Boss：精英按人数缩放 +50%/人、野外 Boss 数值（单挑可行性）、世界 Boss 掉落特殊物品
4. 隐藏怪物：hidden_monsters 触发条件（时间/地点/道具）、隐藏 Boss 强度
5. 怪物修饰：monster_mods 词缀（精英前缀/特殊能力）实现与显示一致
6. 战利品结算：loot_materials cap 防重复拾取、图纸掉落（学习后不重复掉）、宠物蛋掉落、
   金币掉落范围、拾取上限/背包满
7. 怪物属性公式：monster_stats(lv, role) 与 MONSTER_ROLE_BASE、build_monster 三层乘数链
   （Boss 系数×(1+lv×0.06) 膨胀）

### 边界场景（优先实测）
- 掉落概率总和超 100%（静态扫描）
- 怪物 0 经验/0 金币
- 图纸重复掉落
- 高级图低级怪（等级不匹配）
- 掉落物品进背包失败（满包）

### 策划案对照
- design/new_world/04_怪物.md（239 怪）、13_物品材料.md（5.7 掉落闭环全表）
```

---

## M07 装备系统

```
<公共框架>

## 模块卡 M07：装备系统
### 范围
装备名册/生成/属性/词条/套装/品质/部位/属性需求/装备/卸下/出售限制

### 文件清单（全部要读）
- game/data/equipment.py
- game/data/equip_roster.py
- game/data/affixes.py
- game/data/sets.py
- game/data/stat_templates.py
- game/core/affix.py
- game/core/affix_effects.py
- game/core/class_sets.py
- game/engine.py（装备属性折算）

### 定制审计点
1. 装备名册完整性：EQUIP_ROSTER 全量（6 职业×5 阶段命名表）、每件装备 lv/stats/price/slot 齐全、
   无重名/无断档（每等级段每部位有货）、装备 ID 与显示名一致
2. 品质体系：QUALITY 5 档全模块同源、品质决定词条数（白 0→橙 3+传说专属）、品质显示（✦ 前缀）
3. 词条系统：30 种词条效果链（流血/破甲/连击/处决/吸血/元素/贯穿/追猎/反击/格挡/反伤/护盾/闪避/坚韧/回春/冥想…）
   实现正确、SERIES_FIXED_AFFIX 系列词条（不是 AFFIXES 的坑）、词条属性折算 PCT_STATS 保留小数
4. 套装：SERIES_SETS/_SERIES_SET_BONUS 套装加成实装、套装部位完整（历史 bug：翡翠套 2/5 残缺）、
   套装显示（穿戴 X/5 件提示）
5. 属性需求：力量/智力/敏捷/耐力四维需求、不锁职业、需求不足时装备失败提示、零豁免铁律
6. 装备/卸下：属性变化显示（每项一行 + 两侧空格）、替换差值计算（old_stats 净变化）、
   已装备装备重复穿戴、出售限制（装备只能铁匠铺卖）
7. 装备生成：随机装备生成（等级区间/词条数/品质概率）、商店购买 vs 掉落 vs 锻造生成一致性
8. 装备价格：品质价格系数链（equip_stats 1.6→公式 1.6→SHOP_EQUIP_PRICE_MULT 3.0）、
   商店买入 vs 推导价一致性（v101.25e 修复后仍要验）

### 边界场景（优先实测）
- 属性需求不满足时穿戴（提示+不生效）
- 0 词条白装显示
- 装备重复穿戴（替换提示）
- 跨职业装备（法师拿战锤——属性够就能穿？）
- 各部位装备名（法师=法帽/长袍/法靴，不是头盔/胸甲）

### 策划案对照
- design/new_world/10_装备.md（名册+外域系列+9 套装）、20_装备词条.md、07 章 §6（定价）
```

---

## M08 物品与背包

```
<公共框架>

## 模块卡 M08：物品与背包
### 范围
物品模板/消耗品/材料/描述/背包管理/物品详情/使用/堆叠/丢弃/排序/筛选

### 文件清单（全部要读）
- game/data/items.py
- game/core/item_templates.py
- game/store/inventory.py
- game/commands/economy.py（背包/出售/物品详情部分）
- game/commands/misc.py（物品相关）
- game/content.py（物品注册）

### 定制审计点
1. 物品数据完整性：全部物品（材料/消耗品/食物/药水/图纸/任务道具）id/name/desc/price/effect 齐全、
   467 材料+122 装备 desc 注入（手写优先/模板兜底）、MATERIALS_BY_NAME 索引存在
2. 物品详情：『物品详情 <n>』显示（属性/词条/用途/来源）、按名查询用 MATERIALS_BY_NAME
   （历史 bug：MATERIALS.get(中文名) 恒 None）、消耗品渲染（hot/buff/affix 三种 payload）
3. 背包：背包容量（无上限？）、堆叠规则、排序（按类型/品质/等级）、筛选、背包满提示、
   出售（批量出售/精确名优先/歧义候选）、已拥有×N 标注
4. 消耗品使用：战斗内/战斗外行为差异、hot 覆盖制、药水百分比 heal、使用后数量扣减、0 数量使用拦截、
   任务道具不可使用/不可出售
5. 材料：分类（9 类关键词）、品质分级、用途标注（可用于 XX 配方）、出售回收率
6. 图纸：学习图纸（消耗/重复学习拦截）、图纸在锻造列表显示、图纸来源（掉落/商店）真实存在
7. 物品模板注入：item_templates 模板渲染（随机物品生成）、模板 list/dict 双形状坑

### 边界场景（优先实测）
- 使用数量为 0 的物品
- 物品详情越界序号
- 出售最后一个物品（背包空）
- 批量出售含任务道具
- 物品详情显示与实机效果不符（desc 造假抓包）

### 策划案对照
- design/new_world/13_物品材料.md
```

---

## M09 商店与配货

```
<公共框架>

## 模块卡 M09：商店与配货
### 范围
商店系统/子区域独立配货/价格/买卖/回购/图纸/荣誉商店/房产/商店已拥有标注

### 文件清单（全部要读）
- game/data/shop.py
- game/data/honor_shop.py
- game/data/housing.py
- game/commands/economy.py（商店部分）
- game/commands/world.py（商店入口/子区域商店关联）
- game/core/maps.py（子区域）

### 定制审计点
1. 子区域配货铁律：每个交易子区域显式配 SHOP_SUBAREA_ITEMS（subarea_id→货物）、
   无"统一供货+运行时过滤"、_sa_shop_kind 判定（herb 在 craft 前）、判定关键词保留
   （铁匠/锻造/军械/工坊/强化、酒馆/旅店/客栈、草药/炼金）、每个交易子区域都有货
2. 商店类型：每类商店卖对应商品（草药铺只卖药、酒馆只卖食物、集市卷轴杂物、铁匠装备材料）、
   错配扫描（强化坊挂武器=bug）
3. 价格：商店卖出价 vs 玩家买入价、品质系数、与制造价关系（制造 vs 购买哪个划算）、
   图纸价格、鱼饵/坐骑/宠物蛋价格
4. 购买流程：购买 <n> 序号、金币不足拦截、背包满、已拥有×N 标注（历史 bug：O41 重复购买）、
   装备购买后 desc 正确（历史 bug：非名册武器 desc 串随机名）
5. 出售流程：出售 <n>/批量出售、装备回收率（0.3→0.5）、防刷钱规则、出售地点限制（装备=铁匠铺）
6. 荣誉商店：honor_shop 物品/价格/兑换流程/荣誉获取与消耗平衡
7. 房产：housing 购买/升级/功能（与策划案 25 章对照）
8. 商店显示：货架列表（序号/名称/价格/需求等级标注）、翻页、空商店提示

### 边界场景（优先实测）
- 购买金币刚好不够（差 1 金）
- 购买已拥有装备（标注显示）
- 空商店访问
- 商店页码越界
- 荣誉不足兑换

### 策划案对照
- design/new_world/02_地图v3.md（城镇商店）、07_成长玩法.md（§6 经济）、25_房产.md
```

---

## M10 锻造打造

```
<公共框架>

## 模块卡 M10：锻造打造
### 范围
配方表/图纸学习/打造流程/材料消耗/等级门槛/产物质量/打造列表

### 文件清单（全部要读）
- game/data/craft.py
- game/core/craft.py
- game/commands/economy.py（打造/学习图纸部分）
- game/store/professions.py（锻造副业）

### 定制审计点
1. 配方完整性：全部配方（id/名称/等级/材料/产物）、材料都在材料表存在（resolve 中文→ID）、
   产物装备在名册存在、配方材料成本 vs 产物价值（40-90% 区间，不倒挂）
2. 图纸学习：图纸来源真实存在（掉落表/商店）、学习消耗、重复学习拦截、图纸显示（已学/未学）、
   图纸学习 vs 铁匠铺直接可学的提示一致性（历史 bug：O47）
3. 打造流程：打造 <n> 序号、材料不足拦截、副业等级门槛（COOKING_REQUIRED_LV 类死代码）、
   成功/失败（失败是否消耗材料）、产物品质随机、打造结果入包
4. 锻造等级：锻造经验获取（成功+1）、升级解锁配方、锻造 vs 商店购买性价比
5. 打造列表：分页（历史问题：烹饪列表不分页）、显示（序号/名称/材料/等级）、免空格粘页码
6. 材料链：配方材料消费（材料进配方不浪费）、材料获取途径标注（采集/掉落/商店）

### 边界场景（优先实测）
- 打造材料差 1 个
- 打造未学图纸的装备（拦截）
- 打造等级不足配方
- 打造列表页码越界
- 打造产物背包满

### 策划案对照
- design/new_world/19_副业详案.md（锻造）、13_物品材料.md
```

---

## M11 强化附魔符文

```
<公共框架>

## 模块卡 M11：强化附魔符文
### 范围
装备强化/附魔/符文刻印/淬火石材料链/成功率/费用/等级解锁

### 文件清单（全部要读）
- game/data/enhance.py
- game/data/enchant.py
- game/data/runes.py
- game/core/enchant.py
- game/core/runes.py
- game/commands/economy.py（强化/附魔/刻印部分）
- game/data/items.py（强化石/淬火石/星铁）

### 定制审计点
1. 强化：成功率阶梯（+N→+N+1 概率）、费用（跟等级曲线）、强化失败（是否降级/碎装备/保护机制）、
   强化石消耗（普通/精炼+25%/星铁必成）、强化经验（成功+1，按段位）、强化显示（+3 后缀）
2. 强化材料链：淬火石获取（挖掘矿石改名后）、强化石 vs 炼金强化石区分（同名双 key 坑：
   mat_qiang_hua_shi vs i_stone_upgrade）、材料价格合理
3. 附魔：附魔等级解锁（符文按附魔等级：lvl1/2/3→Lv2/4/6）、槽位（紫 3 槽 Lv.7/橙 3 槽 Lv.8）、
   大成功 10%（Lv.10）、体力消耗（10/次）、费用
4. 附魔成本核算：Lv.6=10.5 万金（历史爆炸值）是否已收敛、附魔 vs 强化性价比
5. 符文：符文数据（品质/效果/等级需求）、刻印流程、符文槽位校验（ring/necklace 等）、
   符文效果实装（BUFF_MULT 消费端）、符文掉落分层（普通只掉稀有，史诗/传说精英/Boss 专属）
6. 数值：强化费用曲线、成功率与费用平衡、满级彩蛋（Lv.10 成功率+5%）

### 边界场景（优先实测）
- 0 金强化
- 强化满级后再强化（拦截）
- 附魔无体力
- 刻印背包无符文
- 强化非装备物品

### 策划案对照
- design/new_world/19_副业详案.md（强化/附魔）、13_物品材料.md（强化石链）
```

---

## M12 经济与市场

```
<公共框架>

## 模块卡 M12：经济与市场
### 范围
金币/价格链/掉落变现/回收/摆摊市场/每日任务/经济循环/防通胀

### 文件清单（全部要读）
- game/commands/economy.py（经济部分：买卖/摆摊/每日任务/排行榜）
- game/store/connection.py
- game/engine.py（金币相关）
- game/data/items.py（价格）
- game/commands/social.py（市场/交易）

### 定制审计点
1. 经济循环：打怪→卖材料→买装备→变强→打更强的怪 闭环、金币产出（怪物金币/任务奖励/卖材料）vs
   消耗（装备/住宿/强化/附魔/传送）平衡、每日任务奖励（50 金 50 经验）vs 成本（历史：制造型全倒挂已修）
2. 价格链：物品价格 vs 制造价格 vs 商店价格一致性、材料价格（古代鱼骨 350→200 统一）、
   装备回收率、防刷钱（回收 ×0.5）、NPC 代工 vs 玩家代工差价（生活玩家被需要）
3. 摆摊/市场：摆摊流程（上架/价格/数量）、摊位费、市场浏览/购买、撤摊、摆摊物品不丢失、
   市场数据持久化（market 表）
4. 每日任务：抽取逻辑（已激活副业抽取）、任务奖励（金币+经验）、跨天刷新（_date 字段）、
   领取状态、完成条件判定、每日任务与副业等级联动
5. 排行榜：排行（等级/金币/成就/副业 8 条）、排行数据实时性、排行文案（历史 bug：6→8 条过时）
6. 反通胀：必掉=不值钱、稀缺品走生活渠道、掉率按一天刷几个反推（好刷→5%）、
   金币来源总量控制

### 边界场景（优先实测）
- 0 金币买任何东西
- 摆摊价格 0/负数/超上限
- 每日任务跨天（23:59 接 00:01 交）
- 市场购买自己摊位物品
- 排行榜空数据

### 策划案对照
- design/new_world/07_成长玩法.md（§6 经济体系）、13_物品材料.md、19_副业详案.md
```

---

## M13 副业框架

```
<公共框架>

## 模块卡 M13：副业框架
### 范围
8 副业总框架：激活/等级/经验/升级/每日任务/遗忘/双副业上限/副业面板

### 文件清单（全部要读）
- game/data/prof_config.py
- game/store/professions.py
- game/commands/economy.py（副业命令：选择/状态/遗忘）
- game/commands/base.py（no_prof_waiting 守卫）
- game/engine.py（副业经验）

### 定制审计点
1. 8 副业定义：采集/挖掘/垂钓/烹饪/炼金/锻造/强化/附魔 全配齐（id/名称/描述/激活条件/导师）、
   命名统一（垂钓不是钓鱼、锻造不是打造、挖掘不是采矿）、副业显示名 PROF_FIELDS 单一来源
2. 激活/遗忘：副业选择流程（拜师/直接选）、双副业上限（第 3 个副业拦截）、遗忘副业（清等待状态，
   历史 bug：遗留挖掘结算串台到采集）、遗忘后等级保留/清零
3. 副业等级：1-10 级经验曲线、升级条件、等级解锁内容（配方/地点/材料）、满级彩蛋
   （采集稀有翻倍/挖掘 50%/垂钓双鱼/烹饪完美/锻造 9 折/强化+5%）
4. 每日副业任务：按已激活副业抽取（历史 bug：8 选 1 不按激活过滤）、任务完成判定、
   奖励（50 金 50 经验——主奖励经验）、跨天刷新
5. 等待型副业：采集/挖掘/垂钓 等待流程（开始→等待→收获）、等待中操作拦截（no_prof_waiting）、
   等待时间、中途取消、收获物入包
6. 副业面板：显示（副业名/等级/经验/每日任务）、副业排行
7. 经验来源 vs 等级门槛（历史死锁审计模式）：强化/附魔成功+1 经验（不锁死）、
   每副业有经验来源且与门槛匹配

### 边界场景（优先实测）
- 等待型副业进行中做其他事（拦截）
- 遗忘副业时等待中（清状态）
- 副业经验满级后继续获取
- 每日任务领取重复
- 未激活副业使用对应指令

### 策划案对照
- design/new_world/19_副业详案.md（8 副业+导师进修+每日任务+排行）、14_成就.md
```

---

## M14 采集挖掘

```
<公共框架>

## 模块卡 M14：采集挖掘
### 范围
采集点/挖掘点/材料池/地图差异化/稀有产出/等待机制

### 文件清单（全部要读）
- game/data/gather.py
- game/data/gather_pools.py
- game/commands/economy.py（采集/挖掘命令）
- game/data/maps.py（采集点挂载）
- game/core/events.py（采集事件）

### 定制审计点
1. 采集点：全部采集点（id/地图/子区域/产出池/等级需求）、显示=可交互（探索看到的都能采）、
   采集点与地图匹配（野外/森林/河边有对应材料）
2. 挖掘点：矿点（MINE_SPOTS）、地图差异化（GATHER_MAP_POOLS 过滤矿石关键词——不同地图不同矿）、
   矿石种类（淬火石/铁/铜/银/金…）
3. 材料池：gather_pools 每池产出（材料/概率/数量）、池与材料表一致（resolve）、
   稀有产出（兔蛋 20%/缰绳 10% 满级翻倍）、垂钓联动（鱼饵材料）
4. 采集流程：采集开始→等待→收获、采集失败/成功判定、采集物数量（1-N）、采集经验
5. 材料用途：采集材料都有用途（配方/任务/商店），无死材料（历史：高级钓点 6 种死材料已修）
6. 采集地点指引：玩家如何知道去哪采（地图标注/提示）、采集点 desc

### 边界场景（优先实测）
- 体力 0 采集
- 采集点等级不足
- 采集收获背包满
- 采集等待中取消
- 无采集点地图采集

### 策划案对照
- design/new_world/19_副业详案.md（采集/挖掘）、13_物品材料.md
```

---

## M15 垂钓系统

```
<公共框架>

## 模块卡 M15：垂钓系统
### 范围
钓点/垂钓流程/品质五档/鱼种/收藏图鉴/鱼饵/垂钓等级

### 文件清单（全部要读）
- game/data/fishing.py
- game/core/fishing.py
- game/commands/economy.py（垂钓命令）
- game/data/items.py（鱼饵/鱼）
- game/core/drops.py（垂钓掉落）

### 定制审计点
1. 钓点：全部钓点（id/地图/子区域/等级/鱼池）、显示=可交互、钓点分布（海边/河/湖）
2. 垂钓流程：垂钓开始→等待→收获（钓到鱼/杂物/鱼饵/宝箱）、品质五档（白/绿/蓝/紫/橙）、
   品质概率权重（传说满级 1%）、等待时间、垂钓经验
3. 鱼种与收藏：FISH_COLLECT 收藏图鉴（roll_collect_fish 概率升序最稀有优先）、收集进度、
   收藏奖励、鱼可用于烹饪（银鳞鱼汤等配方）
4. 鱼饵：鱼饵商店上架（铁港商行+银溪集市）、鱼饵使用（提升品质/缩短等待）、鱼饵消耗
5. 满级彩蛋：Lv.10 一杆双鱼 15%、稀有品质翻倍
6. 品质体系：FISH_QUALITY_ORDER=QUALITY_ORDER 同源、品质显示（✦ 前缀）、
   鱼/杂物/宝箱分类、垂钓产出 vs 商店价值

### 边界场景（优先实测）
- 无鱼饵垂钓（能否钓）
- 体力 0 垂钓
- 垂钓等待中移动
- 图鉴全收集后继续钓
- 钓点等级不足

### 策划案对照
- design/new_world/16_品质垂钓.md、19_副业详案.md（垂钓）
```

---

## M16 烹饪炼金

```
<公共框架>

## 模块卡 M16：烹饪炼金
### 范围
烹饪（持续 buff 食物）/炼金（瞬时药水）/配方/效果实现/材料链/战斗内外使用

### 文件清单（全部要读）
- game/data/cooking.py
- game/data/alchemy.py
- game/core/food_effects.py
- game/core/item_templates.py（消耗品效果）
- game/commands/economy.py（烹饪/炼金命令）
- game/battle.py（hot/buff 消费端）
- game/commands/combat.py（战斗用药水）

### 定制审计点
1. 食物三线：恢复线 34（hot 每回合回血回蓝）/属性线 5（弱化药水 1/3）/词条线 17（临时词条）、
   infer_template 判定优先级（hot→food/effect+恢复→food_buff/affix+恢复→food_affix）、
   payload 协议（hot:/buff:/affix:，shield 特判）
2. 药水：28 种药水特殊效果+desc 真实性（desc 必须与 BUFF_MULT 实际一致——历史抓包：矮人烈酒
   desc +5%×3场 实际 +30%）、战斗内立即生效（本回合爆发/下次攻击/救命回血）、战斗外使用
3. 配方：烹饪 16 配方+炼金配方、材料链闭环（鱼→鱼汤、草药→药水）、配方成本≈售价 40-90%、
   材料倒挂不做（历史原则）
4. 效果实装：BUFF_MULT food_* 弱化键=药水 1/3、效果键映射（item_templates.py 不在 battle.py）、
   hot 两处结算（正常回合+被控分支）、额外行动不结算 hot、覆盖不叠加防刷
5. 数值锚点：hot 总量<同价药水、短战斗兑现率、占行动回合、资源池限制
6. 烹饪/炼金流程：制作（选择配方→消耗材料→产出）、成功/大成功（完美料理 10% 强度×1.5）、
   副业等级门槛、烹饪列表分页（历史问题）

### 边界场景（优先实测）
- 战斗内吃食物（是否允许/效果）
- hot 与药水同属性叠加（取高不叠）
- 材料差 1 制作
- 0 体力制作
- 效果描述与实际数值核对（逐条 desc vs 数据）

### 策划案对照
- design/new_world/19_副业详案.md（烹饪=持续/炼金=瞬时分工）、13_物品材料.md、16_品质垂钓.md
```

---

## M17 宠物坐骑

```
<公共框架>

## 模块卡 M17：宠物坐骑
### 范围
宠物池/宠物蛋/宠物技能/宠物品质/坐骑池/坐骑效果/购买获取

### 文件清单（全部要读）
- game/data/pets.py
- game/data/mounts.py
- game/core/pets.py
- game/core/mounts.py
- game/commands/social.py（宠物/坐骑命令）
- game/commands/combat.py（宠物参战）
- game/data/items.py（宠物蛋/缰绳）

### 定制审计点
1. 宠物完整性：14 宠物（id/名称/品质/技能/desc）、PET_POOL 与 PET_EGG_ROLL 掉落表一致、
   宠物技能效果（buff_atk→p_buffs[atk_up] 等映射正确、数值对齐实际 buff——crit_up 0.20 不是 0.10）
2. 宠物获取：蛋掉落（战斗/垂钓品质档/采集稀有/商店——反通胀：稀缺不走战斗）、
   孵化流程、宠物品质（QUALITY 5 档同源）、宠物重复获得（分解/放生/堆叠）
3. 宠物战斗：宠物参战（挂载/技能施放/死亡复活）、宠物 buff 与玩家 buff 关系、宠物经验
4. 坐骑：10 坐骑（id/名称/价格/效果）、mount_effects 7 字段消费点全实装
   （discount/elite_bonus/stamina_reduce/sell_bonus/collect_bonus/fish_bonus/exp_mult）、
   坐骑购买（price>0 自动进商店——验证都上架了）、坐骑召唤/骑乘
5. 效果叠加：坐骑折扣与商店折扣叠加规则、多个坐骑效果切换
6. 显示：宠物/坐骑面板（等级/经验/技能/品质）、战斗日志宠物行动、desc 来源真实

### 边界场景（优先实测）
- 骑乘坐骑再购买新坐骑
- 宠物死亡后战斗
- 坐骑效果叠加 bug（折扣显示）
- 宠物蛋开蛋（背包满）
- 坐骑商店缺货

### 策划案对照
- design/new_world/24_宠物与伙伴.md、13_物品材料.md（蛋/缰绳）
```

---

## M18 成就称号公会

```
<公共框架>

## 模块卡 M18：成就称号公会
### 范围
成就/领取/称号/签到/编年史/公会/势力声望

### 文件清单（全部要读）
- game/data/achievements.py
- game/data/titles.py
- game/data/guild.py
- game/data/factions.py
- game/core/achievements.py
- game/core/achievement_conds.py
- game/core/title_conds.py
- game/core/factions.py
- game/commands/misc.py（成就/称号/签到）
- game/commands/social.py（公会）
- game/data/__init__.py（成就索引）

### 定制审计点
1. 成就完整性：97 成就（id/名称/条件/奖励/desc）、条件实现（achievement_conds 每条件有对应判定）、
   奖励发放（金币/经验/称号）、解锁提示（claimed=0 待领取 + _reward_txt 显示）、『成就 领取』流程
2. 成就奖励：新手期 17 个 500→100、副本/转职 1000 保留、奖励经验走 check_player_level_up 正常结算、
   成就奖励与升级联动（历史 bug：静默发大额经验）
3. 称号：title_conds 条件、称号佩戴/卸下、称号加成实装（历史 bug：base.py r[0] 取元组→bonus 从未生效）、
   称号显示（面板/战斗）
4. 签到：每日签到（跨天判定 _date）、连续签到奖励、补签
5. 编年史：编年史记录（关键事件）、展示
6. 公会：guilds/guild_members 表、公会创建/加入/退出、公会功能（11 章策划案=延迟落地——
   若代码有公会功能必须全测，若无则是策划案未落地需标注）
7. 势力声望：factions 声望获取/消耗/商店/等级
8. 数据一致性：成就 ID 在事件/任务/战斗触发点存在（触发点 grep 确认每成就至少一个触发源）

### 边界场景（优先实测）
- 领取已领成就（重复领取拦截）
- 签到跨天（23:59/00:01）
- 称号佩戴无称号
- 公会重复创建
- 成就条件重复触发（只发一次）

### 策划案对照
- design/new_world/14_成就称号.md、11_国战公会.md（标注落地状态）、03_NPC（势力）
```

---

## M19 主线任务

```
<公共框架>

## 模块卡 M19：主线任务
### 范围
主线全链（70 任务/12 章）：接取/推进/交付/状态机/章节卡点/奖励/任务面板/对话树联动

### 文件清单（全部要读）
- game/data/quests.py（MAIN_QUESTS）
- game/store/quests.py
- game/commands/world.py（任务接取/交付/追踪/任务面板）
- game/core/dialogue.py（对话树任务选项）
- game/core/dialogue_conds.py（quest 条件）
- game/commands/talk_actions.py

### 定制审计点
1. 主线全链：MAIN_QUESTS 每任务（id/章节/名称/目标/奖励/giver/前置）、q1_1→qN_N 前置链完整无断、
   每章 5-6 任务、章节顺序正确、最终章可完成（无"接了不能交"）
2. 任务状态机：pending→active→ready→completed、接取/推进/交付三阶段、completed_main 记录、
   主线完成判定（main_quest=None 且 completed_main 非空）
3. 对话树联动：有对话树的主线 giver 必须有 quest_take 选项（历史 bug 3 处）、giver 校验
   （v101.23 铁律：qid 空=按当前主线动态判断且校验 giver==对话 NPC）、
   texts 条件变体（v101.23b）、quest_talk text_from: story 回退（v101.23d）
4. 任务目标：objective 类型（kill/talk/collect/explore）实现、目标进度计数（collect_count）、
   目标怪物/道具存在、任务叙事与目标一致（历史：野狗→史莱姆 8 处）
5. 奖励：金币（任务金币×5 后）经验 装备 道具、奖励发放（背包满）、奖励与主线等级匹配
   （任务奖励经验 vs exp_to_next——1 级 150 经验升 2 级是否合理）
6. 卡点检查：每章主线是否需要副本/等级门槛（副本卡主线=O43 类问题全查）、
   单人可完成性（主线副本人数配置 ≤1 或可单人开）
7. 任务面板：显示（当前主线/进行中/可接取/已完成）、done 过滤、师门考验追踪段
8. 主线奖励闭环：主线给的钱/装备能支持当前章节战斗（不卡进度）

### 边界场景（优先实测）
- 跳过前置直接交付（无前置任务）
- 重复交付（完成后再交）
- 任务道具重复拾取（cap_name 防重）
- 主线进行中接支线
- 任务目标击杀数超计数

### 策划案对照
- design/new_world/17_主线剧情扩容.md（70 任务+对话树）、05_主线.md
```

---

## M20 支线任务

```
<公共框架>

## 模块卡 M20：支线任务
### 范围
35+ 支线：接取/推进/交付/告示牌/隐藏任务链/奖励/与主线并行

### 文件清单（全部要读）
- game/data/quests.py（SIDE_QUESTS）
- game/store/quests.py（side 字段）
- game/commands/world.py（支线接取/交付/告示牌）
- game/commands/misc.py（告示牌）
- game/data/npcs.py（支线 giver）
- game/core/dialogue_conds.py（side_available）

### 定制审计点
1. 支线完整性：全部支线（id/名称/等级/目标/奖励/giver/前置）、giver NPC 存在且在同地图、
   接取入口真实（对话树 side_offer 选项/告示牌——历史 bug：4 NPC 缺入口）、
   支线等级与地图等级匹配（O52：雾潮航道怪 Lv.45 vs 任务 Lv.22）
2. 告示牌：告示牌内容（支线列表/接取）、告示牌在城镇存在、接取后移除/标记
3. 支线状态机：side 字段（pending/active/ready/completed）、支线完成记录、
   支线与主线并行（不冲突）
4. 隐藏任务链：H3-H12（12 隐藏链）触发条件（四层随机 chance/roam/cycle/unlock）、
   任务链 2-5 步跨地图、不显示任务栏（追踪缺失是否合理）
5. 支线奖励：金币/经验/装备/称号/图纸、奖励与支线难度匹配
6. 支线叙事：目标与文案一致、任务道具可获取
7. 支线入口可发现性：giver NPC 有对话入口、『对话』列表显示支线提示

### 边界场景（优先实测）
- 支线等级不足接取（min_level 过滤）
- 告示牌重复接取
- 支线 giver 不在场（时段 NPC）
- 隐藏任务链中途断链
- 支线完成后 giver 对话残留

### 策划案对照
- design/new_world/06_支线.md（35 支线）、18_野外NPC与隐藏任务.md（H3-H12）
```

---

## M21 对话树与 NPC

```
<公共框架>

## 模块卡 M21：对话树与 NPC
### 范围
对话树引擎/选项条件/多轮对话/NPC 数据/导师/酱油 NPC/隐藏 NPC/快捷对话/台词变体

### 文件清单（全部要读）
- game/data/dialogues.py
- game/data/npcs.py
- game/data/wild_npcs.py
- game/core/dialogue.py
- game/core/dialogue_conds.py
- game/core/hidden_cond.py
- game/commands/talk_actions.py
- game/commands/world.py（对话/找 NPC）
- game/commands/base.py（npc_quick_dialog）

### 定制审计点
1. 对话树结构：每树（root/节点/选项/next/action）、无死路（选项全可达）、无孤儿节点、
   22+ 对话树 NPC 全检查、quest_take 覆盖率（audit_dialog_quest_take.py 全量）
2. 条件系统：CONDITIONS 注册表（quest_done/quest_active/quest_pending/quest_ready/not_quest_done/
   apprentice/not_apprentice…）、每个条件实现正确、ctx 透传（npc_id 校验）、
   side_available 依赖 ctx.side_quests
3. 动作系统：talk_actions 注册表 14 动作（_apply_talk_action）、动作效果正确（给物品/加声望/解锁）、
   动作与 CONDITIONS 对称
4. 台词变体：texts=[{need,text}] 条件变体、多主线 NPC 变体覆盖（镇长 5/会长 16/abbess 6）、
   text_from: story 回退、陈旧台词审计（关键词扫描三分类）
5. NPC 数据：功能 NPC（funcs 非空）位置正确（老板在自家店）、酱油 NPC（funcs=[]）随机性四件套
   （roam/appear/period/lines）、功能 NPC 永不随机、『找』不在→指路提示
6. 导师体系：8 导师（三关拜师：理论答题→实践任务→授业考验）、apprentice 状态持久化、
   拜师后副业解锁、导师对话树完整
7. 隐藏 NPC：10 隐藏 NPC（chance/roam/cycle/unlock 四层随机）、保底机制（连续 7 次必出）、
   隐藏 NPC 对话/任务
8. 快捷对话：『对话 <名字/序号>』、裸数字优先级链（对话树>移动模式>物品模式>NPC 序号>快捷指令）、
   无 NPC 不 yield 放行
9. 显示=可触发：地图/子区域 NPC 列表与可对话一致、NPC 序号稳定

### 边界场景（优先实测）
- 对话空参/不存在的 NPC
- 对话条件不满足（选项隐藏正确性）
- 拜师重复（已拜再拜）
- 时段 NPC 不在时对话（提示）
- 对话树循环（无限对话）

### 策划案对照
- design/new_world/03_NPC群像.md、15_NPC对话.md、18_野外NPC.md、19_副业详案.md（导师）
```

---

## M22 地图移动

```
<公共框架>

## 模块卡 M22：地图移动
### 范围
24 城镇/58 野外/22 副本连接/子区域/城门/传送/住宿/道路/移动命令/地图面板

### 文件清单（全部要读）
- game/data/maps.py
- game/data/subareas.py
- game/data/roads.py
- game/data/portals.py
- game/core/maps.py
- game/core/portals.py
- game/commands/world.py（移动/前往/住宿/传送/地图）
- game/commands/player.py（回城）

### 定制审计点
1. 地图结构：24 城镇/58 野外/22 副本（MAPS 全量）、城镇星形（广场连所有、场所只连广场）、
   野外线性相邻、出城走城门(_gate)、进城落城门、地图连接表双向一致（A→B 则 B→A）
2. 子区域：347 子区域（id/名称/desc/场所类型/NPC/怪物/商店）、desc 无占位符（全量填充）、
   子区域与地图归属正确、出口匹配定居点规模（小村庄无城门、大城有城门）
3. 移动命令：『前往 <序号>』『移动』『返回』、移动模式（v101.17）、裸数字赶路、
   移动体力消耗、移动撞怪（18% 威慑线）、跨图移动限制
4. 传送：方碑传送（列表/价格/折扣标注 O26）、传送卷轴、回城、战败回城点正确
5. 住宿：旅店（住宿费曲线凑整 Lv.100=1000）、恢复效果、各城镇旅店存在（历史 bug：铁盾镇无旅店已修）
6. 地图面板：显示（地图名/子区域列表/NPC/怪物/采集点/商店）、显示=可交互、
   当前区域高亮、移动模式状态
7. 道路：roads 连接（野外→野外）、道路显示
8. 区域等级：地图怪物等级（min-max）、与玩家等级曲线匹配、新手村引导

### 边界场景（优先实测）
- 前往不存在的序号
- 移动体力 0
- 从城门进城（落点正确）
- 方碑折扣显示与实际扣费一致
- 住宿 0 金币

### 策划案对照
- design/new_world/02_地图v3.md（24 城 58 野 22 副本）、23_指令系统.md
```

---

## M23 探索事件彩蛋

```
<公共框架>

## 模块卡 M23：探索事件彩蛋
### 范围
探索/事件池/去重/POI/道具交互/天气时间季节/世界事件/彩蛋/规则引擎

### 文件清单（全部要读）
- game/data/events.py
- game/data/pois.py
- game/data/poi_pools.py
- game/data/props.py
- game/data/rules.py
- game/core/events.py
- game/core/event_templates.py
- game/core/world_event_templates.py
- game/core/rule_engine.py
- game/core/time_weather.py
- game/core/wild.py
- game/core/pois.py
- game/store/props_use.py
- game/commands/world.py（探索/交互）
- game/commands/combat.py（探索遇怪）

### 定制审计点
1. 探索流程：『探索』（消耗体力/等待/结果）、探索结果类型（遇怪/材料/事件/空）、
   空探索概率、探索经验
2. 事件池：事件完整性（30+ 事件）、事件概率、事件效果（金币/材料/战斗/陷阱）、
   事件去重（最近 3 次 exclude + event_state——历史 bug：O22 重复率高已修）、
   泛黄书页防重复（cap_name）
3. POI：探索风景点（pois/poi_pools）、POI 显示=可触发（交互 XX+序号）、
   POI 每日 1 次（props_use 表+effect dict）、POI 奖励
4. 道具交互：PROPS 『交互 <名称/序号>』、场所专属元素（铁匠铺→锻造台）、
   交互彩蛋每日 1 次、交互效果（材料/回血 15%）
5. 天气/时间/季节：time_weather（白天/夜晚/天气/季节）、对玩法影响（怪物/NPC/垂钓）、
   跨天判定（_is_time 23-5 深夜——测试确定性坑）
6. 世界事件：world_event 表/事件（世界 Boss/商队/瘟疫）、事件时间窗口、事件奖励
7. 彩蛋：探索彩蛋（EXPLORE_EGG_CHANCE 独立判定）、许愿命令、隐藏互动、彩蛋可达性
   （显示必须可触发）
8. 规则引擎：rules.py/rule_engine（条件规则）、每条规则实现与数据一致

### 边界场景（优先实测）
- 连续探索同一地点（去重生效）
- 交互未发现的元素（无提示）
- 深夜探索（时间判定）
- 事件效果与描述一致
- 彩蛋触发条件满足但未触发（保底）

### 策划案对照
- design/new_world/18_野外NPC与时间季节.md、02_地图v3.md（探索）、23_指令.md（交互）
```

---

## M24 命令框架与持久化

```
<公共框架>

## 模块卡 M24：命令框架与持久化
### 范围
命令注册/正则/装饰器/守卫/DB schema/迁移/状态持久化/数据完整性/主入口/GM 指令

### 文件清单（全部要读）
- game/main.py
- game/db.py
- game/content.py
- game/engine.py（全）
- game/commands/base.py
- game/commands/_registry.py
- game/commands/gm.py
- game/commands/misc.py
- game/store/（connection/players/inventory/quests/battle_state/stats/social/world/feedback/professions/props_use 全部）
- game/data/_assembly.py
- game/data/index.py
- game/core/index.py

### 定制审计点
1. 命令注册：@filter.regex 全部命令（113 条指令总表对照 23 章）、_registry.py 静态表与装饰器一致、
   命令正则冲突（互斥矩阵：test_v87_command_matrix）、免空格粘参数、半角全角（[0－9] 坑）
2. 守卫体系：@require_player()/@require_battle()/@no_prof_waiting() 覆盖、双功能 handler 不误挂守卫、
   守卫顺序（@filter.regex 最上→业务）、REGISTER_HINT 唯一常量
3. DB schema：players/inventory/quests/stats/achievements/battle_state/… 全表结构与代码访问一致、
   CREATE TABLE IF NOT EXISTS + ALTER 补列 5 处检查点、JSON 字段序列化/反序列化、
   update_player 白名单、get_player json.loads
4. 迁移：event_state 标记幂等迁移、迁移函数只跑一次、无历史迁移残留（_migrate_legacy 已删验证）
5. 状态持久化：battle_state 读写、event_state（talk_/prof_/mode_ 等 key）、跨会话恢复、
   脏数据清理（测试号残留）
6. 数据完整性：跨表引用（掉落→材料→配方→商店→用途）、build_index 索引覆盖（数据表都进索引）、
   resolve 中文名→ID、MATERIALS_BY_NAME、SET_RENAME/ITEM_RENAME 迁移映射
7. GM 指令：gm.py 全部（发物品/传送/窥探/伤害/经验/等级）、GM 白名单、GM 指令不泄漏玩家可见
8. 主入口：main.py 装配（Mixin 顺序）、插件加载、版本号、help 文本（指令总表 vs 实际命令差集）
9. 反馈系统：feedback 入库/查询/cron 报告链路

### 边界场景（优先实测）
- 命令矩阵无冲突（跑 test_v87_command_matrix.py）
- 无角色发任意指令（REGISTER_HINT）
- 战斗中发非战斗指令（拦截）
- 免空格命令（技能列表2 粘页码）
- 全角数字输入（１→1？）

### 策划案对照
- design/new_world/23_指令系统与交互设计.md（113 条指令总表）
```

---

## 派发说明（主 agent 用）

1. 每轮 6 个 agent 并行（delegate_task batch 6，toolsets=['terminal','file']），轮次按 PRE_LAUNCH_PLAN_v104.md
2. 每 agent 提示词 = 公共框架 + 模块卡全文（逐字粘贴，不许缩略）
3. context 额外补充：当前 git commit（b4fa5f9 之后的最新）、明确"只审计不改"
4. 汇报汇总：4 轮全部完成后把 24 份报告合入 `docs/AUDIT_FINDINGS_v104.md`（P0/P1/P2/P3 分级总表 + 边界结果 + 策划案缺口）
5. 防偷懒措施：每个 agent 要求先报模块统计数（文件数/数据条数），报告里每条问题必须带文件:行号，
   健康度评分；主 agent 抽查每轮 1-2 份报告验证（自己 grep 复现关键结论）
