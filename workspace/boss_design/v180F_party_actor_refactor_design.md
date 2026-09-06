# v180F 玩家侧 party actor 化重构设计（定稿草案 v1.0）

> 状态：侦察完成（4 子 agent 报告已落盘 workspace/boss_design/v180F_recon/recon_0~3.md）
> 鱼鱼 2026-09-07 拍板：单独立项 + **彻底重构**（构造签名直接改 party，测试一并迁移）
> 哲学锚点：**战斗引擎必须完全 actor 化——玩家/怪物/随从同一套代码，按 actor 字段不区分身份**（『又是两套』= 架构错误信号）

---

## 一、问题陈述（4 份侦察报告综合）

玩家侧是**三容器并存**（敌方 enemies 已统一按层）：

| 容器 | 内容 | 定义行 | 问题 |
|---|---|---|---|
| `self.player` | 当前**焦点**玩家 actor（97+ 字面引用，`_p_*` 间接 257 处） | 660 | 副本里是**可切换指针**（`_load_player_state` 换绑） |
| `self.allies` | 副本存活玩家**快照引用**列表（含焦点本人） | 636-659 | 只在副本有；野外空 |
| `self.companions` | 宠物+召唤物 actor（side=player/kind） | 703 | v180-C 已 actor 化，但独立数组 + **无 owner 字段** |
| `self.enemies` | 敌方 actor 数组 | 610 | ✅ 唯一统一按层 |

**核心结论（recon_1 §5C）**：*"真正的单焦点瓶颈不在数据容器（已 actor 化），而在行动调度/管线入口"*。

### 4 个侦察 agent 确认的关键发现

1. **状态已 80% actor 化**（v180-B）：32 个 `_p_*` helper 全动态读 `self.player` dict，换绑即跟随；播种 23 键
2. **两套播种代码**：allies 快照只播 7 键（站位/buffs/ct），player 播 23 键——不一致，副本靠 `_load_player_state` 二次补播
3. **CTB 双轨**：野外单人用 Battle 级 `self.p_ct`（804/2578），副本各玩家独立 `snap["ct"]`（instance 层 `_instance_next_actor` 轮转）——本身就是"两套"
4. **副本 = "轮流载入焦点"**：`_instance_act` 每刻**重建 Battle + `b.player = snap`**；敌方打谁 `_load_player_state(qq_id)` 把 self.player 换绑成被打者。**敌方事件队列中途换绑 self.player**（当前靠"敌方段在 turn 尾部"才安全，recon_1 §3 ⚠️）
5. **承伤链伪 actor 化残留**：`_roll_dodge`/`_mitigate_chain`/`_retaliations_and_buffs`/`_post_hp_lethal`/`_on_taken_rewards` 按 class_name 读 `_p_*` 焦点袋而非 actor 自身（recon_2 §2）——非焦点玩家挨打会吃错被动
6. **随从无 owner 字段**：宠物/召唤物找主人靠 `_last_player or self.player`（"谁最后行动"隐式推断）——多人歧义；挡刀池不过滤归属
7. **序列化 = 单焦点扁平顶层键**（20+ 键 p_buffs/resources/...）——本质假设"一场=一个玩家状态"，**party 多玩家必然溢出**（recon_3 §4 最麻烦点）
8. **治疗指定队友已打通**（b1/b2 编号走 allies），但增益（K_BUFF）**无"对任意队友生效"的引擎内路径**（team_effects 只是广播）
9. **瞬态标记未 actor 化**：`_player_hit`/`first_attack_done`/`_death_pact_used`/`_set_immune_used` 等 Battle 实例槽
10. **副本死亡移除走 allies 过滤+compact**（9258-9264）——现成模板

---

## 二、目标架构

```
self.party: list[actor]   # 玩家侧统一阵列（玩家本体 rank1 + 随从按 rank）
  actor = {..., rank, side: "player", kind: "player"|"pet"|"summon",
           owner: actor|uid（随从）, ct: 绝对时刻, buffs/resources/stacks/...}
self.focus: actor         # 当前操作/结算焦点（原 self.player 语义，指向 party 内成员）
self.enemies: list[actor] # 不变
```

- **焦点 = party 内索引/引用**，不是独立数据——`_p_*` helper 收编成 `_actor_*(actor)` 或读 focus
- formation 的 select_aoe_targets/pick_by_policy **两侧共用**（传 party 或 enemies）
- 承伤/挡刀/治疗/DOT/buff 到期全遍历 party/enemies，无 player/allies/companions 特判
- **每个 party actor 自带 ct**——删 Battle 级 `self.p_ct` 单值，野外单成员自然退化一致
- 随从显式 `owner` 字段——挡刀/宠物行为/治疗归属读 owner 不猜 `_last_player`

---

## 三、分期建议（recon_3 §5 战略 + 鱼鱼"一次彻底"哲学平衡）

**鱼鱼要彻底**。但彻底 ≠ 一步到位（battle.py 万行 + instance 联动 + 566 测试 + 序列化重写，
一次性全改风险极高且难回归）。建议**仍分 2 期、每期是完整可交付的"彻底"**：

### 期 1：随从收编 party（平滑收口，序列化基本不动）
- companions + pet 并入 `self.party`（随从段）
- 随从补 `owner` 字段（装配时落），`_guard_check`/`_companion_act`/挡刀池按 owner 归属
- `self.summons` 降级为 property 扫 party
- tick actor_ref 扩展 `"party:pet"` 定位
- 序列化：新增 party 键承载随从；pet/summons 键降级兼容读
- **产出**：随从和玩家同在一个 party 数组（按 rank 层），挡刀归属正确，多人歧义消除

### 期 2：玩家收编 party（真正的重构，序列化重写）
- self.player + allies → party 玩家段；`focus` 语义化
- **序列化重写**：顶层 20+ 扁平键 → party 成员 actor dict 承载；顶层键只留旧档兼容读
- `_restore_pstate` → 废弃，改 party actor 直接携带状态
- `_p_*` 257 处 → `_actor_*`（传 actor）或读 focus
- 承伤链 5 函数伪 actor 化残留修复（读 actor 自身 dict）
- `_is_focus_player` 泛化 `is_player_side()`；`_player_dead` → party 循环判定
- instance.py st["players"] → party 装配（20+ 处）
- CTB 统一：删 self.p_ct，每 actor 自带 ct，`_instance_next_actor` 从 party+enemies 选
- **产出**：引擎完全 actor 化——玩家/随从/怪三侧统一 party/enemies 双数组，无任何三容器特判

### 测试迁移（每期同步）
- 构造签名 `Battle(enemy=..., player=...)` → `Battle(enemies=[...], party=[...])`
- 566 处测试迁移策略：conftest 加 `mk_battle(single_player)` 工厂（内部转 party），
  测试体尽量少改；但**签名彻底改**（鱼鱼拍板不留兼容层）
- 门禁：新 party 构造测试 + 全量回归

---

## 四、风险与对策

| 风险 | 对策 |
|---|---|
| 序列化格式变更丢档 | 旧档兼容读（顶层键 → 新 party 格式迁移函数） |
| 副本"每刻重建 Battle"性能 | 期 2 保持该模式（重建=装配 party），不引入引擎内轮转 |
| 566 测试迁移量大 | conftest 工厂 + 分批（子 agent 并行） |
| `_p_*` 257 处漏改 | grep 清单驱动，分期验收：期 1 后随从段零 `_p_*` |
| 敌方中途换绑 self.player 脆弱点 | 期 2 改 focus 后该语义消失（敌方打谁 = 传 actor 参数，不换绑） |

---

## 五、验收标准（每期）

- 全量回归 280+ 绿 + 数值门禁绿
- 新门禁：party 构造/随从归属 owner/挡刀按归属/AOE 打 party 一层
- grep 断言：期 1 后 companions 独立容器删除；期 2 后 self.player/self.allies 无新增、
  `_p_*` 仅剩兼容读（或清零）
- playtest：野外单挑、副本 2-6 人、治疗 b<N>、随从挡刀、敌方点名均正常

---

## 六、开工顺序（期 1 子任务草案）

1. `self.party` 数组建立（__init__ 装配 player+companions，随从带 owner）
2. companions 读写点迁移（增删/挡刀/死亡契约/上限计数 ~12 处）
3. pet 引用恢复（self.pet 保留或 party 内 kind 查找）
4. tick actor_ref `"party:pet"` 扩展
5. summons property 改扫 party
6. 测试迁移 + 门禁 + 全量回归
