# N5b4-5 副本（instance）切 battle2 —— 引擎缺口详细设计（待鱼鱼审查）

> 2026-09-08 侦查产出。分支 wt_ebuffs。背景：设计文档 §7 假设 instance 只是
> "命令层换 API"，实际侦查发现副本对旧引擎 Battle 做了**深度定制**（状态内聚注入 +
> 事件队列驱动 + 仇恨/团队广播/剧本），切 battle2 前必须先定 4 个缺口怎么补。
> 本文档给行级/函数级设计，供鱼鱼审查拍板后实施。

---

## 0. 副本现状模型（为什么不能直接切）

副本战斗（`game/commands/instance.py` `_instance_act` 2444-3077）当前架构：
- st = 副本实例状态（顶楼，含 players 快照/enemies 阵列/进度/账务）
- **每次玩家行动重建一个旧 `BT.Battle`**：`from_state({...50 键...})`，把 st 内对象
  **引用注入**（allies=存活玩家快照引用、players/alive/threat/taunt 挂 `b._st`、回调
  挂 `b._inst_cb`）→ `b.actor_act(..., enemy_act=True)` 让旧 Battle 事件队列一次跑完
  （玩家技能 + 敌方行动 + DOT + 宠物 + 召唤 + 团队效果）→ 行动后从 `b.*` 读回 20+ 键
  写回 st（enemies/p_ct/tick_effects/pet/killed_enemies/team_effects/defending...）。
- 副本层自己的账务（仇恨/贡献/dealt/击杀/通关）在命令层。

耦合面 = 旧 Battle 私有 API 一长串：`b.enemies / b.e_minions / b.p_ct / b._focus /
b._now / b._tick_no() / b._player_hit / b.team_effects / b.tick_effects /
b.killed_enemies / b.pet / b.companions / b._st / b._inst_cb`。

battle2 直接替代后缺失的能力（缺口）：
| # | 缺口 | 旧实现位置 | 影响 |
|---|---|---|---|
| G1 | 自动 actor 目标选择（仇恨/嘲讽/target_policy） | battle.py `_pick_instance_target` 1440-1479 | 副本 Boss 打谁全乱 |
| G2 | 团队技能广播（team 字段 heal_all/buff_all/taunt...） | battle.py 6176/6256/7202 生成 `team_effects` | 群奶/群体增益/嘲讽失效 |
| G3 | Boss 剧本机制（mech DSL：phase_open/player_low/summon） | battle.py 7549+ v116.1 敌方行动段 | Boss 战退化 |
| G4 | 宠物/召唤物驱动 | v167.3/v180 companions | 与野外同待"宠物批" |

---

## 1. G1 + G2 统一设计：战斗级注入钩子（引擎小扩展，零游戏知识）

侦查结论：G1/G2 都是"战斗需要外部（命令层）参与决策/记账"，battle2 目前只有
actor.triggers（声明式效果），缺"战斗级回调注入"。补两个构造参数即可，引擎不认识
仇恨/团队/剧本任何一个词：

```python
# game/battle2/battle.py Battle.__init__ 增加两个可选参数（与 title_bonus/pet 同级）：
def __init__(self, btype="monster", sides=None, title_bonus=None, dmg_mult=1.0,
             pet=None, st=None, hostile_map=None,
             target_picker=None,        # 新：callable(battle, actor) -> Optional[actor]
             on_event=None,             # 新：callable(battle, evt_name, ctx, logs) -> None
             **kwargs):
    ...
    self.target_picker = target_picker   # 自动 actor 行动前问外部"打谁"
    self.on_event = on_event             # 事件总线 fire 尾部通知外部观察者（只读记账）
```

### G1 target_picker：自动 actor 目标选择
- **改点 1**：`Battle.__init__` 存参数（上面）。
- **改点 2**：`Battle.actor_auto`（battle.py ~197-221）target 解析处：
  ```python
  if ctx_target is None and self.target_picker is not None:
      try:
          _picked = self.target_picker(self, actor)
          if _picked is not None:
              ctx_target = _picked
      except Exception:
          ctx_target = None
  ```
  之后照旧 `ActCtx(..., target=ctx_target)`。schedule.advance 调 actor_auto 不传 target
  → 走 picker；玩家 human_act 显式 target 不受影响。
- **改点 3**：无需动 act/do_skill（ctx.target 非 None 已直用）。
- 序列化：picker 是运行回调不落盘（副本战斗不 from_state，每次行动从 st 重建时传入）。
- **副本命令层 picker 实现**（instance.py 新增，逻辑抄 `_pick_instance_target`）：
  ```python
  def _instance_target_picker(st, alive_actors):   # 闭包：读 st 返回闭包
      def pick(battle, actor):
          # actor = 将行动的自动怪（side=enemy）
          # ① 嘲讽强制：st.taunt_target 存活 → 返回该玩家 actor（sides["player"] 匹配 qq_id）
          # ② 按怪 target_policy（C.MONSTER_MODS[id].target_policy，缺省 boss=hate_top/其他=front）
          #    + st.threat 表 → FM.pick_by_policy（game/core/formation.py 公共模块复用）
          # ③ 返回选中的玩家 actor；None → 引擎回落默认（hostile 首个存活）
          ...
      return pick
  ```
- 野外人 None → 行为零变化。世界Boss 玩家侧单 actor → 无影响。

### G2 on_event：团队技能广播翻译器（战斗级观察者）
- **改点 1**：`Battle.__init__` 存 on_event（上面）。
- **改点 2**：`game/battle2/effect_triggers.py` `fire()` 尾部追加：
  ```python
  if getattr(battle, "on_event", None) is not None:
      try:
          battle.on_event(battle, evt_name, ctx, logs)
      except Exception:
          pass   # 观察者异常不阻断战斗
  ```
  （fire 已有 logs 参数；ctx 含 _owner/actor/info 等。on_event 只读+记账+可用引擎动词
  改状态——与扩展动作同权，外部系统视角。）
- **副本命令层 on_event 实现**（instance.py）：
  - `act_cast`（do_skill 扣费后结算前 fire，ctx.info 带技能定义）→ **团队技能翻译器**：
    ```python
    if evt == "act_cast" and ctx.get("info", {}).get("team"):
        _team = ctx["info"]["team"]          # "heal_all"/"def_all"/"taunt"/"shield_all"/...
        if _team == "taunt":
            st["taunt_target"] = 施放者qq; st["taunt_turns"] = ...   # 敌方下次行动前生效 ✓
        else:
            for 队友 actor in battle.sides_of("player") 存活且非施放者:
                调引擎动词：heal_actor / buff 写 actor["buffs"] / shields...（heal_all 等）
                或复用 instance._apply_team_effect 改写到 battle2 actor
    ```
    翻译规则对照旧 battle 6176/6256/7202 生成的 te dict（kind/effect/lv/stats）+ 现有
    `_apply_team_effect` 消费端。⚠️ act_cast 在结算前 fire → 团队效果与主技能同刻生效，
    敌方 advance 前完成 ✓（解决时序问题）。
  - `on_death`（死亡统一钩子）→ st 存活标记/alive 同步（替代 _instance_battle_cb 的
    enemy_acted 记账）。
  - `act_done` → 玩家行动完成账务（dealt/贡献/仇恨由命令层主流程自算，可不动）。
- **不需要新引擎原语**：heal/buff/shield 都是引擎现有动词（扩展动作同款调用）。

---

## 2. G3 Boss 剧本/怪 AI —— 建议独立"剧本机制批"，N5b4-5 只跑通主线

现状：怪 mech 字段 = DSL token（v116.1 phase_open/player_low/pv_broken、召唤、转阶段），
旧 Battle 敌方行动段消费；副本 Boss 另有 INSTANCES 配置 phases/opening/triggers
（v178）。battle2 无 mech 执行器。

设计（不在本批全量迁移）：
- N5b4-5 主流程先保证：普通怪/精英/Boss **数值行动**正确（auto_act 配首技能，同
  N5b4-3 worldboss 做法）。
- Boss 剧本 = 副本命令层"导演"：human_act 返回后（on_event act_done/或主流程）检查
  Boss 血量/回合 → 触发剧本动作（转阶段文案/召唤 sides append/强化），现有 st 内
  mech DSL 解析器逐步移植（每剧本一个命令层动作，量 = 副本内容翻译工程）。
- 完整怪 AI（技能轮换/多段 AI）→ HANDOFF 已记"上层怪 AI 模块"。

## 3. G4 宠物/召唤物 —— 并入未来"宠物批"（与野外同批）

battle2 Battle pet 参数"只存不驱动"是 N5b 已知过渡（野外 N5b4-2 已同态）。副本切
battle2 后宠物与野外一致（待宠物批统一驱动）。召唤物（v180 companions）同归随从批。

---

## 4. 副本 battle2 化映射表（_instance_act 改造蓝图）

| 旧（_instance_act 内） | battle2 等价 | 说明 |
|---|---|---|
| `BT.Battle.from_state({50键})` | `B2("instance", sides=组好, title_bonus={}, pet=当前行动者宠物, target_picker=..., on_event=...)` | 每次行动重建（不落盘 battle state，st 为顶楼） |
| sides 组装 | player side = 存活成员 actors（player_to_actor(snap 补 stat_bonus/装配)），enemy side = st enemies actors（monster_to_actor 透传） | 参照 PVP 构造 |
| `b._focus = snap` | 当前行动者 actor 副本；行动后 sync 写回 snap（hp/mp/buffs/shields/ct/state/defending/charging） | 参照 sync_player_from_actor，扩展每人 |
| `b.actor_act(...enemy_act=True)` | `b.human_act(action, skill, actor=当前actor, target=目标actor或None)` | advance 内含敌自动行动+时间结算 |
| `b.enemies / b.e_minions` | `b.sides_of("enemy")`（增援=命令层 append actor 进 sides，st 同容器同步） | 死亡不移除 → 命令层压缩 st（保留现有 compact） |
| `b.p_ct` → snap.ct | `actor["ct"]` 写回 | 命令层轮转读 st players[k].ct（保留现有） |
| `b._now / b._tick_no()` | `b._now`（st["now"] 写回） | 展示轮次命令层自算 |
| `b._player_hit` | 命令层 dealt 自算（现有逻辑） | 不需要 |
| `b.team_effects` | on_event(act_cast) 翻译器（§G2） | 删 b.team_effects 读 |
| `b.tick_effects` 序列化/重绑 | **退役**：DOT 在 actor.state 随 st 持久化，schedule 自动结算 | 删 tick_effects 段 |
| `b.killed_enemies` | `b.killed_actors`（uid）+ 命令层去重入 st killed_enemies | 保留副本任务账 |
| `_instance_battle_cb(enemy_acted)` | on_event(on_death/act_done) | 删 _cb |
| 敌方 DOT/毒（dot_pending 闸门） | battle2 schedule 自动（actor.state dot 声明） | 退役闸门 |
| heal/buff 指定队友 | human_act target=队友 actor dict ✓ | 引擎已支持 |
| 宠物 b.pet | B2 pet 参数（暂不驱动） | 宠物批统一 |

## 5. 批次建议（每批独立验证 + commit）

| 批 | 内容 | 引擎改动 | 验证 |
|---|---|---|---|
| N5b4-5E（引擎批） | Battle +target_picker +on_event（构造/actor_auto/fire 尾部 ≈20 行）+ 单测 | 是（小） | battle2 全套 + 新单测 |
| N5b4-5a（主流程） | _instance_act 重建 battle2 化：sides 组装/行动/每人回写/敌同步压缩/增援 append/轮转保留 | 否 | 副本拟真流程测试 |
| N5b4-5b（账务） | 仇恨 picker + team 广播翻译器 + 死亡/击杀同步 | 否 | 多人仇恨/群奶用例 |
| N5b4-5c（剧本） | Boss mech DSL 最小导演执行（转阶段/召唤） | 否 | Boss 战用例 |
| 宠物/随从 | 并入未来宠物批（野外同批） | — | — |

## 6. 风险与边界

- 副本是玩家多人核心玩法——每批手测闭环 + 流程测试，回退先 git checkout
- team/剧本是"内容翻译"（旧机制 → 引擎动词/命令层导演），量级取决于技能/剧本数据
  规模（实施时盘点 team 字段技能数与 mech token 数）
- on_event 观察者与 actor.triggers 正交：trigger 是声明效果（改战斗），on_event 是
  外部记账/广播；别让 on_event 返回影响结算（只读 ctx，需要改状态用引擎动词）
- from_state 恢复的 battle（非副本重建路径）无 picker/on_event → 回落默认行为 ✓
