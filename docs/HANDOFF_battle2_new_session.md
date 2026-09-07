# 新战斗引擎开发交接（battle2）——开新会话必读

> 2026-09-08 交接。鱼鱼拍板方向：
> 1. 按 REFACTOR_v181P4_FULL_PLAN.md 新建 battle2 引擎，**不执着跑整个游戏**
> 2. **只为新引擎写独立测试**（引擎自身的行为/数值测试，不碰全量回归）
> 3. 全部完工后，**一次性删旧 battle.py 换新引擎，再跑全量**
> 4. 顺带做掉 P3（玩家状态容器收尾）+ P5（battle 拆类）——已并入新设计

## 0. 分支与位置
- 分支：`wt_ebuffs`（worktree：`C:/Users/yuyu/AppData/Local/Temp/df_wt_ebuffs/w1`）
- **HEAD：`9a5627f`**（2026-09-08 晚，质量批次：分支覆盖 90.4%）
- 主仓（生产）：`C:/Users/yuyu/qqbot/data/plugins/dragonfall`（master 4b634d6，未动）
- 开发环境：直接在 w1 写（鱼鱼拍板不用沙盒）。测试独立临时 GWEN_GAME_DB。

## 1. 权威文档
| 文档 | 内容 |
|---|---|
| `docs/REFACTOR_v181P4_FULL_PLAN.md` | 主方案 v2（Part 1-8 全） |
| `docs/REFACTOR_v181P4_class_mech_decouple.md` | **职业机制与引擎解耦方案**（2026-09-08 鱼鱼拍板，见 §2） |
| `docs/ENGINE_ARCHITECTURE_v181P4.md` | 旧架构分析 |
| `tools/COVERAGE_battle2.md` | 覆盖率三层说明 + 豁免清单 |

## 2. 本会话重大架构决策（鱼鱼拍板，全部落地）

这些是**方案文档之外**的新决策，必须遵守：

1. **职业机制不进引擎**（鱼鱼："职业机制不应该依赖战斗系统，战斗系统提供通用接口"）
   - mech 三分类：A 通用状态已迁 / B 通用动作数据化 / **C 职业专属机制不迁**
   - C 类（血祭/卸负/旋律状态机/骷髅祭仪）留给上层职业模块（事件总线方案未做）
2. **actor 字段契约**：引擎白名单 + `ext` 扩展区
   - 职业状态写 `actor["ext"]`（引擎绝不读）；白名单外引擎不假设
3. **叠层不做进引擎**（鱼鱼："叠层这东西有必要做进引擎吗" → 不）
   - 统一 `actor["state"]` 容器（删 stacks/resources 双轨，零兼容）
   - `state_effects` 声明表：cap/stat_scale/dot/on=target 全数据驱动
4. **框架/配置分离**（鱼鱼："换一套配置就是新游戏"）
   - 引擎只有**动词执行器**：control/buff/shield/cleanse/state_add/state_spend
   - 游戏名词（眩晕/灼烧/战意）在 `game/data/battle2_rules.py` 配置层
   - battle2 经 `config.py` 挂载点查表，引擎零游戏知识
5. **不陪葬旧 bug**（鱼鱼："你确定你的新引擎没问题就行"）
   - 战吼 atk_up=10 刻（旧引擎漏传 info=3 刻是 bug，测试固化）
   - AOE 弃用 infer_atk 反推（数学不自洽），逐目标独立结算
   - 等级字段统一 `level`（删怪用 lv，零兼容）
6. **落地统一收口**：`landing.py` 的 deal_damage/heal_actor
   - 所有伤害/治疗必须走它（防绕过护盾/死亡判定）

## 3. 实施进度（N1-N5a 完成，全套 168/168 绿）

| 阶段 | 内容 | 状态 |
|---|---|---|
| N1 | battle2 骨架 + 普攻闭环（对拍 45/45） | ✅ 8d315a9 |
| N2a | 技能链（攻/疗/益 数值主线） | ✅ 9bfc620 |
| N2b | 多段 hits + AOE 逐目标独立结算 | ✅ ed2bc86 |
| N3a | effects 效果单表 + 命中接入 | ✅ 416b23b |
| - | actor 字段契约 ext 扩展区 | ✅ 717d09d |
| - | 状态底子：统一 state + 声明表折算 | ✅ 2d975c2 |
| - | landing 落地接口层 + level 统一 | ✅ ca38710 |
| - | 框架/配置分离 Step1（state 表迁配置） | ✅ b31f5a9 |
| - | 框架/配置分离 Step2（effects 动词化） | ✅ 41178e5 |
| N4 | CTB 调度 + 自动行动 + DOT 结算 | ✅ da129a5 |
| N5a | serialize 序列化（to_state/from_state） | ✅ 68110ae |
| - | 质量：函数级覆盖 100% + 补齐 38 项 | ✅ 777260a |
| - | 质量：分支覆盖 90.4% + 甄别文档 | ✅ 9a5627f |
| **N5b** | **命令层切换（combat.py 等接新引擎）** | ⬜ 下一步 |
| **N6** | **删旧 battle.py + 全量回归** | ⬜ |

### battle2 包结构（现状）
```
game/battle2/
├── __init__.py    导出 Battle/ActCtx/make_actor/actor_ext
├── actors.py      actor 模型/state 访问/ActCtx/ext
├── battle.py      Battle 主类（act/human_act/auto_run/to_state/from_state）
├── actions.py     行动结算（攻击/治疗/增益/多段/AOE）
├── effects.py     动词执行器（control/buff/shield/cleanse/state_add/spend）
├── landing.py     落地收口（deal_damage/heal_actor）
├── stats.py       面板（actor_stats + 声明折算）
├── schedule.py    CTB 推进（advance/auto 调度/DOT）
├── serialize.py   to_state/from_state（sides-only）
├── config.py      配置挂载点（load_game_rules）
└── state_effects.py  薄封装查 config 规则
游戏配置（引擎外）：game/data/battle2_rules.py
```

## 4. 测试
- 位置：`tests/test_battle2_*.py`（8 个文件，168 断言全绿）
- 跑法：`python tests/test_battle2_n1_attack.py` 等（w1 内）
- **覆盖率门禁（每改必跑）**：
  - `python tools/cov_func_battle2.py` — 函数级（0 未调用）
  - `python tools/cov_branch_battle2.py` — 行级 90.4%（其余防御代码豁免，见 tools/COVERAGE_battle2.md）
- Python：`C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe`

## 5. N5b 待办（命令层切换，还没开始）
- combat.py/instance.py/world.py/tower.py 的 `from game import battle as BT` → battle2
- 盘点命令层调用面（b.xxx 方法清单）→ battle2 提供同语义 API
- 旧档迁移（enemy/enemies 键 → sides）：serialize.migrate_old_state 未写（方案留了）
- 命令层模式：`b.to_state()` → `db.save_battle()`；恢复 `BT.Battle.from_state(st)`

## 6. 已知差异（新引擎 vs 旧引擎，切换时注意）
- human_act 出手后会**自动推进**到下一个决策点（旧引擎要命令层手动 advance）——命令层要适配
- actor 全 level（怪模板 lv 由 data_bridge 入口翻译，引擎不认 lv）
- shield 默认 on=caster（施法者给自己上盾）；对敌 shield 要显式 on=target

## 7. 会话重启接续
- 新会话开场：读本文档 + REFACTOR_v181P4_FULL_PLAN.md
- git log 看进度；继续 N5b 从命令层盘点开始
