# V4+V5 合并施工图（鱼鱼 2026-09-08 拍板 A：动词收敛 apply/consume + 数据表全字段迁移 一次做完）

> 2026-09-08。V1（bf6c590）+ V1b（15a8ba0）已完成容器统一（4 容器 → actor["effects"] 单容器，
> EFFECT_RULES 单表挂载）。V1 落地时鱼鱼纠正两次：不搞回落 helper、不搞改名换汤的薄 API 层。
> 当前 effects.py 11 个动词**实现**已全部写 effects 容器（语义已对），剩的是：注册名还是旧名
> （buff/control/state_add/state_spend/state_set）+ EFFECT_RULES 表还是 STATE_EFFECTS 改名镜像
> （没 panel/consume/period/cleanse/negative 新字段）。V4+V5 合并 = 把这两件事一次原子切换做完。
> 会话口令：「继续 effects 统一，V4+V5 合并从动词收敛开始」

## 0. 目标终态（与 V1 设计文档 §2 一致）

```python
actor["effects"][key] = {
    "stacks": int|float,     # 叠层；非叠层数值（百分比/固定量）进 value 不入 stacks
    "expire": float|None,    # 到期绝对时刻；None=常驻
    "value": dict|None,      # 动态数值覆盖（heal_amp_pct.value.amp 等）
    "hit": {...},            # 出手消费声明（dmg_mult/guaranteed_crit/bonus_atk_pct）
    "period": {...},         # 周期声明（dir/interval/数值）——优先于表声明
    "stat"/"op"/"mult",      # 面板快照（动态 buff 由调用方带；静态查 EFFECT_RULES.panel）
    "v", "mode", ...
}
EFFECT_RULES[key] = { "cap", "on", "panel", "stat_scale", "debuff_scale",
                      "period", "consume", "cleanse", "negative", "tag",
                      "threshold", "guard", "heal_down" }
```

## 1. 动词注册名收敛（effects.py）

| 现状注册名 | 目标 | 说明 |
|---|---|---|
| `buff` | **删**，并入 `apply` | 写 effects 条目（快照/value/hit/纯状态） |
| `state_add` | **删**，并入 `apply` | apply 按参数语义写 stacks += |
| `state_set` | **删**，并入 `apply` | apply 写 stacks = |
| `control` | **删**，并入 `apply` | apply 写 effects[tag] = {stacks, expire, mode}；boss 减半保留逻辑 |
| `state_spend` | **删**，并入 `consume` | consume 写 stacks -= |
| `apply` | **新注册** | 通用挂效果条目（含叠层增/置值/控制 tag/快照），唯一写入口 |
| `consume` | **新注册** | 通用扣减（stacks -= amount；不足拦截） |
| `shield` | 保留 | 独立 shields 容器动词 |
| `cleanse`/`cleanse_all` | 保留 | 遍历 effects 清减益 |
| `heal`/`damage`/`interrupt` | 保留 | landing 薄包装 |

- **不搞**：薄壳注册名（register 多个名转发同一个函数 = 鱼鱼两次纠正对象）；config 回落；
  actors.py 操作 API 族。**唯一允许**：effects.py 文件内部私有函数（如 apply 内部共用的
  entry 定位/expire 取 max 小函数），非公共 API。
- **EFFECT_ACTIONS 映射表**是装配层 API，名词（stun/buff_atk/...）保留，动作值收敛为
  {"action": "apply"|"consume"|"shield"|...} + 剩余参数。

## 2. EFFECT_RULES 数据表全字段迁移（battle2_rules.py）

现状 = STATE_EFFECTS 改名镜像（只有 cap/stat_scale/dot/on/on_threshold/guard/heal_down）。
目标：每 key 补全字段谱，把散在 EFFECT_ACTIONS 动作参数里的**静态数值**搬进表：

- **buff 静态增益**（EFFECT_ACTIONS 33 条 action: buff，数值 stat/op/mult 写死在动作参数）→
  对应 key 进 EFFECT_RULES 带 `"panel": {"stat": ..., "op": ..., "mult": ...}`；
  EFFECT_ACTIONS 里该条目瘦身为 `{"action": "apply", "key": "atk_up"}`（数值查表）。
- **控制 tag**（stun/freeze/sleep/silence/spd_down）→ EFFECT_RULES 带
  `"consume": {"mode": "skip"|"no_skill"}`（sleep 额外 wake_on_hit 声明）；turns 仍由调用方给。
- **周期**（DOT 表 dot → 统一 `"period": {"dir": "damage", "interval": 1.0, ...}`；
  hot 无表条目，动态声明进条目 value/period——regen_hot 由 I2 翻译器带）。
- **cleanse 语义**：CLEANSE_TAGS 硬清单 → 表内 `"cleanse": True` / `"negative": True` 声明
  （act_cleanse 遍历 effects 查表，不再靠 CLEANSE_TAGS 白名单）。
- heal_down/death_guard/stat_scale 已入表不动；cap 保留。

⚠️ 装配层（equip_proc/we_procs）发的 buff 是**动态数值**（wd["spd_pct"] 等运行时算），
   不能查表——这些调用点改发 `apply` 并保留参数（apply 支持 value/stat/op/mult 参数覆盖表）。
   静态名词（技能 buff_atk 等）走表 panel；动态（装备 proc）走参数。两者同落 effects[key] 条目。

## 3. 调用面同步清单（删旧注册名前必须全改）

- `game/data/battle2_rules.py` EFFECT_ACTIONS：33 buff + 6 control + 1 state_set → apply/consume
- `game/services/battle2_equip_proc.py`：9 buff + 2 state_add（393/423/464/477/500/511/595/597/615/624/728）
- `game/services/battle2_we_procs.py`：4 buff + 2 control（245/601/608/692/1061/1096）
- `game/commands/battle2_item_use.py`：hot/regen 相关改 apply + period 声明（V1 已切 effects，复查）
- `game/battle2/effects.py` effects_from_skill/_mech_to_effect：mech → apply
- `game/battle2/actions.py`：名词 effect 走 apply_effects 已 OK；确认无直调 act_buff/state_*
- 服务层 battle2_we_procs 里 `_freeze/_slow` 直调 act_buff/act_control → 改调 apply_effects(apply)
- `tests/`：n3_effects/n4_schedule/n8_events/n9_equip/coverage/hot_regen/item_use 等 type:
  buff/state_add/state_spend/state_set/control 断言 → apply/consume + 语义保持

## 4. 分块 + 验证（每块全绿再下一块；最终一个原子大 commit 或分 2 commit 全绿可提交）

1. **块 1 表先行**：EFFECT_RULES 补 panel/consume/period/cleanse 字段 + EFFECT_ACTIONS 静态动作
   瘦身（数值入表）。表动了但引擎读表点（stats._apply_effects/schedule）需先支持 panel/period
   读法——V1 已支持 cfg.panel（stats 40-82 行）+ 条目 period 优先表 dot 回落（schedule 226-236）。
2. **块 2 动词**：effects.py 注册 apply/consume，删 buff/control/state_add/state_spend/state_set，
   更新 effects_from_skill/mech 分派。
3. **块 3 调用面**：装配层/services/命令层 type 全改 apply/consume + 参数保留。
4. **块 4 测试同步**：~170 处断言机械替换（V1 教训：逐文件跑测试看报错行手改最稳）。
5. **块 5 回归**：battle2 21 文件全绿 + run_all 333 基线对照（沙盒 df_wt_copy2e）。
6. HANDOFF/设计文档/skill reference 同步，commit + 汇报鱼鱼。

## 5. 铁律提醒

- 改码前 git status 干净（先 commit 再动）；出事先 git checkout。
- 不建双轨/回落壳/过渡 helper；终态就在。
- 动词注册名删除是原子动作（删了调用面没改 = 崩）——三块一起改，测试绿才算完成。
- value 型数值不进 stacks（int() 截断 0.15 教训）；非叠层数值进 value/面板快照字段。
- 行为零变化：只收敛名字/数值位置，不改变任何效果数值与语义。
