# 新战斗引擎开发交接（battle2）——开新会话必读

> 2026-09-08 交接。鱼鱼拍板方向：
> 1. 按 REFACTOR_v181P4_FULL_PLAN.md 新建 battle2 引擎，**不执着跑整个游戏**
> 2. **只为新引擎写独立测试**（引擎自身的行为/数值测试，不碰全量回归）
> 3. 全部完工后，**一次性删旧 battle.py 换新引擎，再跑全量**
> 4. 顺带做掉 P3（玩家状态容器收尾）+ P5（battle 拆类）——已并入新设计

## 0. 分支与位置
- 分支：`wt_ebuffs`（worktree：`C:/Users/yuyu/AppData/Local/Temp/df_wt_ebuffs/w1`）
- HEAD：`57c3e61`（方案文档 + 交接定稿）
- 主仓（生产）：`C:/Users/yuyu/qqbot/data/plugins/dragonfall`（master 4b634d6，未动）
- **开发环境：直接在 w1 里写，不用沙盒**（鱼鱼 2026-09-08 拍板：不需要 df_wt_copy2e 沙盒，
  直接主环境开发）。新引擎的测试也在 w1 里写/跑（测试 DB 用独立临时库隔离，不碰真实库）。

## 1. 方案文档（权威，开工先读）
| 文档 | 内容 |
|---|---|
| `docs/REFACTOR_v181P4_FULL_PLAN.md` | **主方案 v2**：目标架构/字段定义/行动签名/效果系统/DB 存储/实施 N1-N6/落地细节/风险 |
| `docs/ENGINE_ARCHITECTURE_v181P4.md` | 架构分析：行动流程/作用对象模型/mech-effect 合并 |
| `docs/HANDLER_MANUAL_battle_mech.md` | 旧 battle_mech 122 handler 分类手册（迁移参考） |

## 2. 核心设计（一句话版）
- 引擎 = sides（actor 组）+ act_ctx（每次行动的 caster/target/scope）
- actor 全同构（无身份逻辑；class_name 只选面板公式，side 只分组）
- 行动入口：`human_act`（命令层）/`actor_auto`（自动 actor）/内部 `act(ctx)`
- 效果：单一 `EFFECT_HANDLERS` 表，handler 签名 `fn(battle, caster, target, params, logs)`
- mech/effect 双轨合并成技能 `effects: [{type, stacks, turns, pct...}]` 列表
- 数值公式**复用旧 engine.py**（不重写），只薄封装
- DB：battle_state 的 state JSON 换 sides-only（旧档一次性迁移）

## 3. 实施阶段（每阶段独立可用 + 自测）
| Phase | 内容 | 验收 |
|---|---|---|
| N1 | battle2 包骨架：actors.py 模型 + Battle 构造 + 普攻闭环 | 同场景新旧引擎伤害一致（对拍脚本） |
| N2 | actions.py 行动链：技能/治疗/增益/AOE/承伤 | kind 三类全通 + 数值对拍一致 |
| N3 | effects.py 效果系统 + 数据迁移 | dot/控制/buff/元素全通 + 数值一致 |
| N4 | schedule.py CTB 调度 + 自动行动 + 状态收尾 | 完整战斗能打完（胜负/逃跑） |
| N5 | serialize.py + 命令层切换 | 野外/副本/PVP 能玩 |
| N6 | 删旧 battle.py + 全量回归 | run_all_tests 全绿 + numeric 52/52 |

**关键**：N1-N4 只写引擎自己的测试（新引擎行为验证），不跑全量；N6 才全量。

## 4. battle2 包结构（目标）
```
game/battle2/
├── __init__.py        # 导出 Battle（from game.battle2 import Battle）
├── actors.py          # Actor 工厂/Sides/ActCtx/序列化
├── battle.py          # Battle 主类：构造/act/human_act/actor_auto/胜负
├── actions.py         # 行动结算：技能/普攻/伤害落地/承伤链/AOE
├── effects.py         # EFFECT_HANDLERS 单表 + handler + 执行
├── stats.py           # 面板（薄封装 engine.py，不重写公式）
├── schedule.py        # CTB：事件队列/时刻推进/自动调度
├── serialize.py       # to_state/from_state（sides-only）
└── data_bridge.py     # 读旧数据层适配（技能/词条/怪物表）
```
依赖：→ engine.py（数值，只读）/ data/ / core/formation.py / core/constants.py
**绝不 import 旧 game/battle.py、core/battle_mech.py handler**

## 5. 测试策略（引擎独立测试）
- 测试位置：`tests/test_battle2_*.py`（w1 里直接写直接跑；N6 删旧后自然进全量）
- 每阶段：对拍测试（同场景双引擎跑，数值差=0）+ 行为断言
- numeric_lib 的纯数值函数（player.py 等）可直接复用做对拍基准
- 参照旧测试怎么构造 battle/玩家/怪（tests/ 里 mk_player/mk_enemy 模式）
- 引擎纯逻辑测试尽量不依赖 DB（避免碰真实库）；确需 DB 用独立临时 GWEN_GAME_DB

## 6. 旧引擎已知现状（新引擎要避免的坑）
- battle.py 11000+ 行，v100+ 补丁叠加，隐式全局目标(self.enemy/_active_target)混乱
- 已做（本分支 commit）：e_buffs 删除、命名 actor 化（player_act→actor_act）、
  enemy property 改 sides 读、部分 core handler 改 _hit_tgt()
- **当前全量回归是红的**（旧引擎改造半途）——新会话不要管旧引擎红，专注 battle2
- 旧 battle.py 的 27 红测试等 N6 删旧时一并处理（很多会随旧引擎消失）

## 7. 开工第一步建议
1. 读 REFACTOR_v181P4_FULL_PLAN.md（尤其 Part 1/2/7）
2. 建 battle2/actors.py（模型）+ 一个最小 Battle（普攻）
3. 写对拍脚本：同构造旧 battle 普攻 vs 新 battle 普攻，伤害一致
4. 跑通 N1 验收再进 N2

## 8. 关键常量/路径速查
- Python：`C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe`
- 测试跑法：w1 里直接 `python tests/xxx.py`（引擎独立测试用独立临时 GWEN_GAME_DB，
  不碰真实库 game/game_data.db；新引擎纯逻辑测试可不依赖 DB）
- numeric 门禁：`python scripts/run_numeric_tests.py`（N6 才跑）
- 公式复用入口：game/engine.py 的 calc_damage/player_final_stats/skill_info/skill_flat_value
