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

## 3. 实施进度（N1-N5a 完成；N5b 前置地基完成，命令层改造待续）

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
| **N5b-0** | **盘点：命令层调用面（旧 dict 语义 vs battle2 sides-only 矛盾）** | ✅ dec4647 |
| **N5b-1** | **数据桥 battle2_bridge（player/怪 → actor 翻译）** | ✅ 64ab806 |
| **N5b-2** | **旧档迁移 migrate_old_state（enemies/enemy → sides）→ 已删（鱼鱼 2026-09-08 拍板：不留旧档迁移代码，旧格式档直接作废清档）** | ⛔ 83a213d 内容删除 |
| - | **fix：_after_act 用聚合 spd（真实玩家裸 spd=0 卡死 bug）** | ✅ 9fceee0 |
| - | **调用映射表施工图（combat 改造依据）** | ✅ a56d5e4 |
| **N5b-3** | **命令层数据流验证测试（DB 存/取 + 行动链 + 迁移）** | ✅ bfd3991 |
| **N5b-4** | **combat.py 等命令层 import 切换（真正改命令层）** | ⬜ 下一步 |
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

### N5b 前置产物（2026-09-08 深夜，鱼鱼睡觉自主推进）
- **game/services/battle2_bridge.py**（battle2 包外——鱼鱼红线引擎零改动）：
  - `player_to_actor(player)` → player actor（class 面板字段透传 + buffs/shields 同构）
  - `monster_to_actor(mon)` → enemy actor（lv→level；rank/reach/role/is_boss/掉落透传）
  - `build_sides(player, enemies, allies)` → sides dict
  - ~~旧档迁移~~（is_old_state / migrate_old_state 已删——鱼鱼拍板：**不做旧档兼容**，
    命令层只认 battle2 格式；旧格式存档（无 sides）→ 直接清档重开）
- **docs/N5B_命令层盘点.md**：9 文件依赖 + b.xxx 全景
- **docs/N5B_调用映射表.md**：施工图（combat.py/instance.py 逐项 b.xxx → battle2 等价）
- **tests/test_battle2_bridge.py**（49 断言）、**tests/test_battle2_cmdflow.py**（10 断言）
- 全套 231/231 绿（battle2 引擎 221 + cmdflow 10）

### ⚠️ 真实数据对拍发现并修复的引擎 bug（9fceee0）
- 真实玩家 actor 裸 spd/atk/def=0（面板由 stats.actor_stats 从 class/equip 聚合）。
  旧 `_after_act` 用裸 spd=0 算行动耗时 → sqrt(50/1)≈7s/次 → 玩家被怪碾压致死。
- 修复：`_after_act` 改用 `S.actor_spd(battle, actor)`（与 next_ct 同口径）。
- 教训：**battle2 测试全用 mk_player 显式塞聚合 spd → 真实数据 bug 测不到**。
  回归测试 N4.7（test_battle2_n4_schedule.py）固化裸 spd=0 形态。

### 对拍数值参考（裸装玩家，Lv10 vs Lv5 怪）
- 旧引擎 victory 剩 ~105-113 HP；新引擎 victory 剩 ~111-127 HP（✅ 同向）
- Lv5 裸装 vs Lv5：旧 victory(剩24) vs 新 defeat——低等级裸奔场景有差异，待数值精调
- Lv10 vs Lv12：双 defeat（✅ 同向）

## 4. 测试
- 位置：`tests/test_battle2_*.py`（9 个文件，231 断言全绿：引擎 221 + cmdflow 10）
- 跑法：`python tests/test_battle2_n1_attack.py` 等（w1 内）
- **覆盖率门禁（每改必跑）**：
  - `python tools/cov_func_battle2.py` — 函数级（0 未调用）
  - `python tools/cov_branch_battle2.py` — 行级 90.6%（其余防御代码豁免，见 tools/COVERAGE_battle2.md）
- Python：`C:/Users/yuyu/AppData/Roaming/uv/tools/astrbot/Scripts/python.exe`

## 5. N5b 待办（前置已完，剩命令层本体改造）

✅ 已完成（见 §3）：
- 盘点 9 文件 + b.xxx 全景（docs/N5B_命令层盘点.md）
- 数据桥 game/services/battle2_bridge.py（battle2 包外，引擎零改动）
- 旧档迁移代码删除（鱼鱼拍板：不留迁移代码，旧格式档作废清档）+ 命令层数据流验证
  （test_battle2_cmdflow.py 第 4 段已改为「旧格式无 sides → 清 DB 重开」）
- spd 聚合 bug 修复 + 回归

⬜ 下一步（N5b-4，施工图 docs/N5B_调用映射表.md）：
- combat.py 切换（按映射表逐处改）：
  - import：`from .. import battle as BT` → battle2 + bridge
  - 开战构造 → `b = B2.Battle(btype, sides=bridge.build_sides(player, group), title_bonus=tb, pet=...)`
  - 恢复：只认 battle2 格式（state 含 sides）→ 直用 `from_state`；无 sides 旧格式 → 清档重开
  - 行动：`b.actor_act(...)` → `b.human_act(...)`（签名一致）
  - 展示：`b.enemies` → `b.sides_of("enemy")`；`b._p_*` → `b.focus()` actor 字段
  - `b._focus = player` 不再需要（battle2 focus() 返回 sides player 首 actor）
  - 战斗级元数据（map/name/dot_res）→ migrate 的 meta 键 / battle_state 外壳
- instance.py（最复杂：副本状态机、BT._ct_initial_wait、battle._remove_unit 等）
- economy/player/tower/world 轻文件
- 每文件切换后跑测试验证

## 6. 已知差异（新引擎 vs 旧引擎，切换时注意）
- human_act 出手后会**自动推进**到下一个决策点（旧引擎要命令层手动 advance）——命令层要适配
- actor 全 level（怪模板 lv 由数据桥入口翻译，引擎不认 lv）
- shield 默认 on=caster（施法者给自己上盾）；对敌 shield 要显式 on=target
- **真实玩家 actor 裸 spd/atk/def=0**（面板聚合）——battle2 已修（9fceee0），
  命令层读玩家面板要用 stats.actor_stats 或 b.focus() 的字段，别读裸 spd
- battle2 不是 dict：`b.get/setdefault` 语义不存在——命令层展示/状态塞键要改走
  battle_state.state.meta / actor 字段（见 docs/N5B_调用映射表.md §4）

## 7. 会话重启接续
- 新会话开场：读本文档 + REFACTOR_v181P4_FULL_PLAN.md + docs/N5B_调用映射表.md
- git log 看进度；继续 N5b-4 从 combat.py 改造开始（施工图已备好）
- 会话接续口令：「继续 battle2，读 HANDOFF 接着 N5b-4」
