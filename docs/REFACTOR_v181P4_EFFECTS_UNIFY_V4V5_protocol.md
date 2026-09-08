# V4+V5 合并施工图——字段级执行协议（鱼鱼 2026-09-08 拍板 A 后细化）

> 会话口令：「继续 effects 统一，V4+V5 合并从动词收敛开始」
> 总纲见同目录 REFACTOR_v181P4_EFFECTS_UNIFY_design.md（目标形态 §2）+ 任务书
> REFACTOR_v181P4_EFFECTS_UNIFY_V4V5_task.md（分块）。本文件给字段级协议：
> apply/consume 的参数空间、每个旧动词/动作的迁移映射、EFFECT_RULES 表补齐清单。

---

## 1. 引擎动词最终注册表（effects.py）

| 注册名 | 语义 | 吸收旧动词 |
|---|---|---|
| `apply` | 挂/叠/置/刷新 effects[key] 条目（统一写入口） | act_buff + act_control + act_state_add + act_state_set |
| `consume` | 主动扣叠层（不足拦截提示） | act_state_spend |
| `shield` | 护盾（独立 shields 容器） | act_shield（不动） |
| `cleanse` / `cleanse_all` | 净化（遍历 effects） | 不动 |
| `heal` / `damage` / `interrupt` | landing 薄包装 | 不动 |

**删除的注册名**：buff / control / state_add / state_spend / state_set。
⚠️ 装配层/EFFECT_ACTIONS/测试里所有 `type: buff|control|state_add|state_set|state_spend`
必须同步换成 apply/consume（块 3/4），否则 resolve_actions 找不到 → 效果静默丢失。

---

## 2. apply 动词参数协议（块 2 effects.py 实现依据）

```python
@register_action("apply")
def act_apply(battle, caster, target, params, logs):
    # holder 解析：on=caster(缺省) → caster；on=target → target（control 原固定 target 语义
    #   由 EFFECT_ACTIONS 迁移时补 on=target / 装配层调用补 on=target）
    # key 解析：params.key 或 params.tag（旧 control 用 tag；统一读 key，tag 兼容）
    # 写入模式（优先级从上到下，互斥判定）：
    # ── A. 控制型：params.mode 存在（skip/no_skill）→
    #        effects[key] = {"expire": max(旧, now+turns), "mode": mode, "stacks": 1}
    #        boss 减半保留（is_boss/role==boss → turns=max(1,turns//2)）
    # ── B. 增益快照型：params.stat + params.mult 存在（或 mult 由 EFFECT_ACTIONS 参数带）→
    #        effects[key] = {"stacks": 1, "expire": max(旧, now+turns),
    #                        "stat": stat, "op": op or "mul", "mult": float(mult)}
    #        （动态 buff 数值随条目快照；stats._apply_effects 读条目优先、cfg.panel 回落）
    # ── C. value 型：params.value 存在（或 pct_from_mech_val 折算）→
    #        effects[key] = {"stacks": 1, "expire": max(旧, now+turns), "v": value}
    #        key=="reduce" 特例：holder["reduce_left"] 同步（原 act_buff 行为）
    # ── D. 纯状态/出手消费型：既无 mode 又无 stat/mult 又无 value →
    #        effects[key] = {"stacks": 1, "expire": max(旧, now+turns), "hit": {...}?}
    #        params.hit dict 存在则快照进条目（原 act_buff hit 分支）
    # ── E. 叠层型：params.op == "add" → effects[key].stacks += amount（cap 查表）
    # ── F. 叠层置值型：params.op == "set" → effects[key].stacks = amount（cap 查表）
    # （E/F 原 state_add/state_set；threshold 事件广播保留——块 2 内部逻辑从旧实现原样搬）
```

- **op 参数语义**（区分叠层加/置，是状态型还是快照型）：
  - 缺省无 op + 有 stat/mult 或 value 或 mode → 快照/状态型（B/C/D/A）
  - op="add" → 叠层加（E）
  - op="set" → 叠层置（F）
  - 兼容：旧 state_add/state_set 的调用在迁移时显式补 op；机械替换脚本见块 3。
- **兼容 read**：不动条目形态（stacks/expire/v/stat/op/mult/hit/mode 字段全部保留原样），
  stats/schedule/landing/actions 读点零改动 = 行为零变化的核心保证。

## 3. consume 动词参数协议

```python
@register_action("consume")
def act_consume(battle, caster, target, params, logs):
    # holder 解析同 apply（on）
    # effects[key].stacks -= amount；不足拦截提示（原 act_state_spend 全文搬）
```

## 4. effects_from_skill / _mech_to_effect（块 2）

- `_mech_to_effect` 里 `{"type": "state_add", "key": mech, "amount": mval, ...}`
  → `{"type": "apply", "op": "add", "key": mech, "amount": mval, ...}`

## 5. EFFECT_ACTIONS 动作收敛（块 3 battle2_rules.py）

每个名词动作序列里的动作值按旧 action 映射：

| 旧 action | 新动作 | 说明 |
|---|---|---|
| `buff`（33 处，静态 stat/op/mult 参数） | `{"action": "apply", ...原参数...}` | 数值暂仍快照（V5 表补 panel 后可瘦身为 key-only，见 §7） |
| `control`（6 处 stun/freeze/sleep/silence/slow/spd_down） | `{"action": "apply", "key": <tag>, "on": "target", "mode": ..., "turns": ...}` | tag→key；mode 保留；on=target 显式 |
| `state_set`（1 处 stacks_set） | `{"action": "apply", "op": "set", ...}` | |
| heal/shield/cleanse/interrupt/damage | 不动 | |

- CLEANSE_TAGS 注释更新：净化遍历 effects 时查表 negative/cleanse（act_cleanse 现有逻辑
  已用 all_state_effects 表 dot/on=target + CLEANSE_TAGS 双轨；保留现有即可，不扩功能）。

## 6. 装配层调用点（块 3）

### 6.1 battle2_equip_proc.py（9 buff + 2 state_add）
- 393/464/477/500/511/595/597/615/624：`"type": "buff"` → `"type": "apply"`（参数原样；
  动态数值 stat/op/mult 继续随动作参数快照——apply B 分支支持）
- 423：`"type": "state_add", "key": key, "amount": 1, "on": "caster"` → `"type": "apply", "op": "add", ...`
- 728：同 → `"type": "apply", "op": "add", ...`（death_guard cap=1）

### 6.2 battle2_we_procs.py（4 buff + 2 control 直发 + 4 处内部 _slow/_freeze 直调 act_*）
- 245/608/1061/1096：`"type": "buff"` → `"type": "apply"`（参数原样）
- 601/692：`"type": "control", "tag": ..., "mode": "skip"` → `"type": "apply", "key": <tag>, "on": "target", "mode": "skip"`（保留 turns；tag→key）
- 内部函数 _freeze/_slow 直调 `act_control/act_buff(...)` → 改调 `apply_effects(battle, owner, tgt, [{...}], logs)` 或直调 act_apply（同模块私有 `_add_stacks` 保留，仅本文件用）
- 内部 244 行附近 `from game.battle2.effects import act_buff` → import act_apply

### 6.3 battle2_item_use.py（I2 翻译器）
- hot/regen 分支已是 effects["regen_hot"]（V1 已切），核实无 type: buff/state_add 残留。

## 7. EFFECT_RULES 表补 panel 字段（V5 数据表迁移，块 3b，可选合并）

- 目标：静态 buff 数值从动作参数 → EFFECT_RULES[key].panel，动作瘦身 key-only。
- ⚠️ 判据：同 key 出现在多动作但数值不同（如 atk_up=1.30 只一处 → 可入表；
  spd_down 既作 control 又作 buff → 保持动作参数优先）。**保守做法**：本批先不改表内
  静态 buff（动作参数照旧），只保证"动词收敛 + 装配层同步"行为零变化；V5 表 panel 入表
  作为后续独立 commit（stats._apply_effects 已支持 cfg.panel 回落，条件已就绪）。

## 8. 测试断言同步（块 4，~170 处）

- tests 里直接 `apply_effects(..., [{"type": "state_add"|"state_set"|"state_spend"|"buff"|"control", ...}])`
  的字面量：
  - type: state_add → type: apply + op: add（key/amount/on 原样）
  - type: state_set → type: apply + op: set
  - type: state_spend → type: consume
  - type: buff → type: apply
  - type: control → type: apply + key=tag + on=target（如原无 on）+ mode 原样
- 涉及文件：test_battle2_n3_effects / n4_schedule / n8_events / n9_equip / coverage /
  hot_regen / item_use / cmdflow 等。V1 教训：正则替换后逐文件跑测试按报错行手改。

## 9. 验证顺序（每块绿再下一块）

1. 块 2（effects.py + effects_from_skill）改完：跑 n3_effects——断言会先挂（动词名没了），
   块 4 同步部分测试后转绿。为可验证，块 2+4 对 n3_effects 小文件先闭环，再铺开。
2. 块 3（rules + 装配层）后跑 n9_equip / n8_events / item_use / hot_regen / coverage。
3. 全套 battle2 21 文件 + run_all 333 基线对照（沙盒 df_wt_copy2e）。
