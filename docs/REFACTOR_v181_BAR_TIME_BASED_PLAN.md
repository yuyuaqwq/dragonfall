# v181 破绽条时间化改造——引擎/核心改动方案（2026-09-10 修订 v2，待审批）

> 前置：`docs/REFACTOR_v181_P15_bar_passives.md`（被动实装 + 缺口 5 项）。
> 本文只写**需要动引擎/核心的改动**；能落内容层的另列。
> **v2 修订**：鱼鱼指出「buffs 已合并进 effects」——核实成立，且比预想更严重：
> `core/battle_bars.bar_state` 会**凭空新建一个 `buffs` 死容器**（V 系列已删除的容器，
> `make_actor` 不再播种），破绽条数据一直写在一个引擎和 battle2 都不认的地方。本版据此改写 §1。

## §0 改动分层

| # | 项 | 落点 | 是否动引擎 |
|---|---|---|---|
| A | 条上限 `max 50 → 125` | `data/battle_config.ENEMY_BAR_CFG` | ❌ 数据 |
| B | 衰减改「每刻 −1.7 小数累计」 | **`core/battle_bars.py`（核心容器）** | ⚠️ 核心 |
| C | 免疫窗口改时刻制（2 刻 / 期内不积蓄 / 到期可再触发） | **`core/battle_bars.py`** | ⚠️ 核心 |
| **C0** | **条容器从死掉的 `buffs` 迁进 `effects`（v2 新增）** | **`core/battle_bars.py` + 4 个读点** | ⚠️ 核心 |
| C2 | 让读点拿到「当刻值」 | **`battle2/schedule.py` + `effect_triggers.py`** | ✅ 引擎（6 行） |
| D | 推满语义（跳过下一动 vs 定身 2.0 刻） | 装配层（`mode=skip` 引擎已有） | ❌ |
| E | Boss 阶段保留 50% | `boss_script` 补 `fire("phase")`（当前零 fire 点） | ❌ 上层 |
| F | 反震（受击反弹 30% + 推条 +3） | 装配层 `on_taken` | ❌ |
| G | 展示当刻条值 | `commands/combat.py` 等读取处 | ❌ 上层 |

**必须动的仍然只有 `core/battle_bars.py`（B+C+C0 同批）＋推荐 C2（引擎 6 行）；A/D/E/F/G 全部内容层。**

证据（可复核）：
- `actors.py:106-111` 播种的是单 `effects` 容器（注释明写「原 state/buffs/hot/debuffs 四键合并」），
  **没有 `buffs`**；`core/battle_bars.py:64-67` 却 `enemy["buffs"] = {}` 自建 → 条写进死容器。
- 写侧全集：`buffs` 的写入者除 `battle_bars` 外，都在 N10 已死的旧模块
  （`potion_effects` / `effect_actions` / `battle_conds` / `passive_procs`）＋两处 `buffs={}` 占位
  （`commands/instance.py:1094,1116`）。battle2 侧只有 `battle_bars`。
- `on_taken` 已带 `source`+`dmg`（`landing.py:139`）→ 反震可写装配层（范例
  `services/battle2_we_procs.py:125 we_reflect`）。
- `"phase"` 在 `EVENTS` 已声明但**全库零 fire 点** → 阶段保留只缺上层一行。
- `core/battle_bars` 活跃消费方仅 `services/battle2_bar_procs.py` + 两个测试 → 可放心改造。

---

## §1 核心改动 C0+C1：`core/battle_bars.py` —— 迁进 effects + 时间化

### 1.1 条状态存放：`effects["bar:<key>"]`（命名空间前缀，**不是** `effects[<key>]`）

```text
实测撞键：ENEMY_BAR_CFG = ["shaken", "curse"]
  shaken    与 EFFECT_RULES 撞键? 否
  curse     与 EFFECT_RULES 撞键? 是 ⚠️（骨噬诅咒是活效果，带 vuln/acc）
  bar:shaken / bar:curse 撞键? 否 ✓
```

- 直接塞 `effects["curse"]` 会让「条状态」和「诅咒效果」抢同一个键（一边要 val/threshold，
  一边要 stacks/expire/vuln），必须隔离。
- 前缀 `bar:` 只是**内容层命名约定**（引擎按键查 `EFFECT_RULES`，找不到就什么都不做）；
  也满足项目既有原则——不给引擎加专用路径，也不新开散容器。
- 声明位置：`data/battle2_rules.BAR_STATE_PREFIX = "bar:"`（与 `BAR_INJECT_FIELDS` 同处）。

### 1.2 条条目字段

| 键 | 类型 | 语义 | 变更 |
|---|---|---|---|
| `val` | **float** | 积蓄（内部小数；展示 `int()`） | int → float |
| `threshold` | int | 当前阈值（触发 ×1.35，封顶 cap×base） | 不变 |
| `trigger_count` | int | 触发次数 | 不变 |
| `_at` | float | 上次结算时刻（`battle._now` 口径） | 新增 |
| `immune_until` | float | 免疫截止时刻（0 = 不在免疫） | 新增 |
| `immune_turns` | int | 派生 = 剩余免疫刻数 `ceil`（旧读取方不必改） | 保留派生 |

### 1.3 容器安全契约（必须成立，配断言测试）

条条目活在 `effects` 里，就要保证**四种容器自动化不会误碰它**：

| 自动化 | 触发条件 | 条条目必须 |
|---|---|---|
| 到期清理（`schedule._settle_time_effects`） | `entry.get("expire")` | **不带 `expire`** ✓ |
| 周期跳 DOT（同上） | `entry.period` 或 `EFFECT_RULES[key].period` | 键不在 EFFECT_RULES ✓ |
| 面板折算（`stats._apply_effects`） | `stacks>0` + `stat_scale`/`stat`+`mult` | 不带 `stacks`/`stat`/`mult` ✓ |
| 控制消费（`Battle.act`） | `entry.get("mode")` | 不带 `mode` ✓ |

断言：`for k in ENEMY_BAR_CFG: assert f"bar:{k}" not in all_state_effects()`；
条条目键集 ⊆ `{val, threshold, trigger_count, _at, immune_until, immune_turns}`。

### 1.4 读侧迁移（真人战斗存档兼容，必须）

```python
def bar_state(host, key, now=None):
    st = host.setdefault("effects", {})
    node = st.get("bar:" + key)
    if not isinstance(node, dict):
        legacy = (host.get("buffs") or {}).get(key)          # 旧存档/进行中的战斗
        node = legacy if isinstance(legacy, dict) else {}
        if legacy:
            (host.get("buffs") or {}).pop(key, None)         # 迁走即删旧键
            if not host.get("buffs"):
                host.pop("buffs", None)                      # 空容器不残留
        st["bar:" + key] = node
    ...
```

（进行中的战斗是随 actor 序列化落盘的，真人正在打——迁移必须读侧容错，不能只改写入端。）

### 1.5 API（`now` 可选关键字，旧调用退化=不结算）

```python
bar_state(host, key, now=None) -> dict
bar_settle(host, key, now, logs=None) -> dict       # 新增：dt=now−_at；免疫到期清；
                                                    #   val −= dt×decay（**不再 int()**）
bar_gain(host, key, amount, logs=None, now=None) -> float
                                                    # 结算；now<immune_until → 直接 return（不积蓄）
                                                    # 触发当帧注入 = 0（no_inject_on_trigger）
bar_should_trigger(host, key, now=None) -> bool     # val≥threshold 且 now≥immune_until
bar_trigger(host, key, logs=None, now=None) -> bool # 阈值递增；val=0；immune_until=now+immune_secs
bar_tick(host, key, logs=None, now=None) -> bool    # = settle + should_trigger（宿主兜底）
bar_preserve(host, key, pct=None)                   # 不变（Boss 阶段）
turn_start_bars(...)                                # 零调用 → 建议随批删（不留半死入口）
```

`immune_secs`：`bd.get("immune_secs")`，缺省回落 `bd["immune_turns"] × 1.0`（curse 的 0 行为不变）。

### 1.6 数值换算（验收口径）

```text
连招三连（hits=3、5/段）= 一次施放 +15
拳师循环 2.2 刻 → 衰减 −1.7×2.2 = −3.74 → 净 +11.26
首阈值 50 → 50/11.26 ≈ 4.44 次出手 → 对齐 v153 §六「约 4.5 次」
阈值序列 50→67→90→122→125（A 项 ×2.5 封顶）
```

---

## §2 引擎改动 C2：全局时钟事件（推荐，6 行）

容器时间化后，「谁去结算」决定读数正确性；读取点分散（`battle2_cond_procs._p_enemy_broken`、
`class_mech_proc` 两个谓词、注入点、展示层）——漏一处就脏读。引擎在时钟推进处广播一次即可。

```python
# ① game/battle2/effect_triggers.py —— EVENTS 元组追加（保持单行定义）
EVENTS = (..., "interrupt", "time_advance")

# ② game/battle2/schedule.py —— _advance_time 尾部
battle._now += dt
_settle_time_effects(battle, logs)
+ from .effect_triggers import fire as _fire
+ _fire(battle, "time_advance", {"dt": dt, "now": battle._now}, logs)
```

装配侧：`battle2_bar_procs._ensure_tick` 首次挂条时自安装
`{"event": "time_advance", "action": "bar_time_settle", "key": ...}`（只有真挂过条的单位才有条目）。
退化路径（不做 C2）：装配层在每个读点前手动 `bar_settle`（当前 4 个读点 + 展示层）。

---

## §3 装配/上层配套（内容层）

| 文件 | 改动 |
|---|---|
| `services/battle2_bar_procs.py` | 读写改 `effects["bar:<key>"]`；传 `now`；新增 `bar_time_settle` 动作；`_ensure_tick` 挂 `time_advance` |
| `services/class_mech_proc.py` | `target_bar_broken` 判定 + `passive_bar_extend` 的 `immune_turns +=` → `immune_until +=`；读点改前缀键 |
| `services/battle2_cond_procs.py` | `_p_enemy_broken` 同上 |
| `data/battle2_rules.py` | 新增 `BAR_STATE_PREFIX`；注释里 `buffs[bar]` 改 `effects[bar:*]` |
| `data/classes.py:403-409` | **删死声明** `enemy_bar.shaken`（零消费方 + `decay_per_turn: 4` 漂移）——数值单源 = `ENEMY_BAR_CFG` |
| `commands/boss_script.py` | 阶段转换处补 `fire("phase")` → 订阅方 `bar_preserve`（E） |
| `commands/combat.py` 等 | 展示 `int(val)`（G）；`commands/instance.py:1094,1116` 的 `copy["buffs"]={}` 占位一并清 |
| `docs/REFACTOR_v181_P15_bar_passives.md` | 「条容器 = core/battle_bars（buffs[bar]）」描述同步改（文档别留旧口径） |

---

## §4 数据层

```python
ENEMY_BAR_CFG["shaken"] = {
    "max": 125,                   # A：对齐 threshold_cap ×2.5 = 125
    "decay_per_turn": 1.7,        # B：语义 = 每刻，小数累计
    "immune_secs": 2.0,           # C：策划案「触发后 2 刻内不再积蓄」
    "no_inject_on_trigger": True, # 消费方落地（触发当帧注入 = 0）
    ...
}
```

## §5 验收门禁（新增 `tests/test_numeric_bar_decay.py`，纳入 `scripts/run_numeric_tests.py`）

```text
1  每 2.2 刻衰减 = 3.74 ± 0.01（float 语义，非 int 截断）
2  连招三连 4.5 次出手触发一次（模拟 15/次注入）
3  阈值序列 50/67/90/122/125（封顶）
4  免疫 2 刻内注入无效（val 保持 0）+ 到期后可再触发
5  自锁防护：触发当帧注入 = 0
6  破绽感知：衰减 1.7 → 0.85（P15 遗留的物理空转项）
7  反震：受击 30 → 反弹 9 + 攻击方推条 +3
8  Boss 阶段保留 50% 积蓄
9  容器安全：条键不在 EFFECT_RULES / 条目不带 expire|period|stat|mode|stacks
10 迁移：buffs[shaken] 旧存档 → 读一次后迁进 effects["bar:shaken"] 且旧键清除
```

## §6 待拍板（3 点）

1. **A**：`max 125`（推荐，放开阈值递增）还是 `threshold_cap 1.0`（阈值固定 50，放弃递增设计）？
2. **C 免疫期语义**：期内注入**忽略**（策划案字面，推荐）还是**保留但冻结触发**？
3. **C2 引擎时钟事件**：本批一起做（推荐）还是先只做容器改造、读点逐个手动结算？

## §7 风险与回退

- `val` int→float：序列化自动；旧 int 兼容；展示需 `int()`。
- **迁移必须读侧容错**：进行中的真人战斗存档在 `buffs` 里，迁移失败= 掉条。
- 阈值 125 后推满更慢但可多次触发 → 需实机体感复核（门禁挡退化，挡不了手感）。
- 回退：C0+C1 一个 commit、C2 独立 commit（可单独 revert）。
- 顺带卫生（不在本批）：`core/potion_effects.py` / `effect_actions.py` / `battle_conds.py` /
  `passive_procs.py` 仍在读写死容器 `buffs`（N10 后无活引用）→ 死代码清理候选。
