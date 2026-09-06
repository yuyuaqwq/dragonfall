# v178 全副本 Boss 差异化机制落地计划（27 卡 + 5 新副本）

> 状态：设计稿 v0.1（2026-09-05 鱼鱼拍板：全量做、真扩展优先、5新副本全建）
> 前置：v177 actor-agnostic 引擎已就绪（40 门禁绿）；三路侦察报告已收（详见 workspace/boss_design/v178_侦察笔记.md）

## 一、任务全景
1. **22 现有副本 Boss**：把泛用 mech（enrage/summon/stacks）升级为 27 卡设计的专属身份技
2. **5 新副本完整建设**：锈潮船坞Lv25 / 烛影墓窟Lv29 / 雷鸣矿道Lv32 / 旋涡竞技场Lv46 / 黑潮歌剧院Lv50
3. **引擎公共扩展**（真做，非降级）：主 agent 先落地 10 项（E1-E10），配门禁测试
4. **策划案同步**：04_怪物图鉴 + 02_地图系统 + 数值章（design/new_world 独立 git 仓）

## 二、引擎公共扩展清单（主 agent 先做，按依赖排序）

### 断链修复（必须先修，否则 Boss 数据落地无效）
| 项 | 问题 | 修法 |
|---|---|---|
| E1 | inst 级 phases 对副本 Boss 无效（_boss_cfg 按 e.id 查不到 inst 配置，abyss_gate.phases 是死数据） | `_boss_cfg` 增加 inst_id 上下文查找（battle._st.inst_id 注入；从 e.id→INSTANCES 键映射表） |
| E2 | instance mech 覆盖吞掉 MONSTER_MODS 剧本（5 例实测：b_om_shadow/b_moro/b_eter/b_goblin_chief/b_king_odric） | instance.py:937-938 改为 inst mech + mods mech **去重合并**，非覆盖 |
| E3 | BOSS_PHASE_TEMPLATES/ult_every/exit/freq/counter 全是死字段（v138.1 四件套从未生效） | 实现 `_phase_ult_every`（每 N 刻大招）/`_phase_freq_mult`/`_phase_counter`/`exit_turns`/`exit_dmg` 消费点；补门禁 |

### 新原语（27 卡机制需要）
| 项 | 机制 | 落地 |
|---|---|---|
| E4 | 玩家侧 dot 通道（Boss 挂玩家毒/灼烧/流血/腐蚀） | 玩家 debuffs 容器 + _turn_start 玩家 dot 结算段 + dot_res/免疫 + 状态栏；复用 DOT_DEFS 公式 |
| E5 | 元素免疫/弱点表（蚀夜三形态/云怒/赫尔嘉圣光×1.3） | 怪物侧 `element_immune`/`element_weak`（_enemy_mitigate 玩家打怪 + _enemy_cast_done 怪打玩家两端） |
| E6 | 方向性防御（云怒风眼-80%/奥拉天象姿态） | 技能/姿态级防御减免字段（DEFEND_REDUCE 三处消费点改造：battle.py:2523/7717 + instance.py:3410） |
| E7 | chains 连招链 + first_move + 时间轴技能池轮换 | chains 消费（固定连招序列）+ first_move 实现 + 每 N 刻切技能池新机制（BOSS_MECHS 新 handler + e 存池状态） |
| E8 | 通用 minion 计数 API + 爪牙死亡回调 | `minion_count()` 方法（仿 _undead_count:3785）+ minion_death 触发器（月神守卫机关/轰鸣晶核） |
| E9 | 打断奖励/反噬钩子（歌澜虚脱/赫尔加反噬） | `_interrupt_charging`（battle.py:2047）被打断单位写标记/切换阶段 |
| E10 | build_monster 透传 shields/dmg_taken_mult 静态配置 | drops.py build_monster 透传（字段即能力） |

## 三、27 Boss 数据落地分组（子 agent 任务卡设计）

### 分组原则（防模板化，按核心题差异化红线）
按 boss-design-and-level-alignment.md §二：每子 agent ≤4 卡，任务卡写死每个 Boss 的核心题 + 组内差异化红线，agent 只补技能/数值配置。

| 组 | 副本 Boss（卡） | 核心题族 |
|---|---|---|
| A 新手教学 | 咕噜(打断+清召唤)、要塞幽灵(灵体)、独眼杰克(打断大读条) | 打断/灵体 |
| B 叠层管理 | 冰霜领主(冰寒)、克罗(诅咒)、轰鸣(充能/新)、雷霆君主(静电) | 叠层记账 |
| C 读招防反 | 试炼骑士长(防反)、马尔库斯(定罪处刑)、蓝歌(魅惑控场) | 读招/控制 |
| D 转火优先级 | 古王(王冠核心)、月神守卫(机关)、石炉(傀儡) | 转火清怪 |
| E 场地/时间轴 | 磐涡(旋涡/新)、赫尔嘉(光暗/新)、敖澜(水压)、摩罗(毒圈) | 场地节奏 |
| F 形态轮换 | 精灵王(月相)、蚀夜(元素免疫)、奥拉(天象) | 形态切换 |
| G 新副本建设 | 锈钳(破壳/新)、歌澜(咏唱/新) | 破甲/咏唱打断 |
| H 终局+剩余 | 奥姆(灵魂吸取)、赫尔加(献祭)、澜歌(潮汐)、蓝歌等余量 | 特殊 |

### 每子 agent 任务卡包含
1. Boss 卡全文引用（workspace/boss_design/卡_X.md）
2. 该 Boss 当前数据（instances.py 段 + monster_mods 条目 + 现状 skills）
3. 引擎原语速查（E1-E10 完成后：哪些字段可用）
4. 落点文件：monsters.py（新增 MONSTER_SKILLS 专属技能）/ monster_mods.py（b_* 机制）/ instances.py（mech/phases/minions 覆盖）
5. 验证：跑相关测试 + 数值门禁
6. 红线：禁碰引擎（主 agent 已做）、禁改其他 Boss、禁 commit

## 四、执行顺序
1. 主 agent 补引擎扩展 E1-E10（分批提交，每批跑门禁）
2. 引擎门禁测试：tests/test_numeric_boss_engine_*.py 新增
3. 派 27 Boss 数据子 agent（按分组，每人 3-5 卡）
4. 5 新副本骨架 + Boss 数据 + 周边内容（子 agent 或主 agent）
5. 全量回归 + 数值门禁 + 双仓提交

## 五、风险与兼容
- 旧 205 怪物技能零改动（新字段缺省不启用）
- instances mech 合并需兼容旧格式（老副本 mech 不变=零行为变化）
- E3 阶段四件套复活可能影响现有 phase Boss（abyss_gate 的 3 段 phase 从纯数值变真换招——需验证难度）
- 双仓提交：代码仓 dragonfall + 策划案仓 design/new_world（04 章同步）
