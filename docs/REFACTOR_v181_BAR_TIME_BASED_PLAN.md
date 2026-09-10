# v181 破绽条时间化改造——引擎/核心改动方案（2026-09-10 待审批）

> 前置：`docs/REFACTOR_v181_P15_bar_passives.md`（被动实装 + 缺口 5 项）。
> 本文只写**需要动引擎/核心的改动**；能落内容层的另列，不混在一起。

## §0 改动分层（先看这张）

| # | 项 | 落点 | 是否动引擎 |
|---|---|---|---|
| A | 条上限 `max 50 → 125`（阈值递增封顶 = max×2.5，注释自己写的 125） | `data/battle_config.ENEMY_BAR_CFG` | ❌ 数据 |
| B | 衰减改「每刻 −1.7 小数累计」 | **`core/battle_bars.py`（核心容器）** | ⚠️ 核心 |
| C | 免疫窗口改时刻制（2 刻 / 期内不积蓄 / 到期可再触发） | **`core/battle_bars.py`** | ⚠️ 核心 |
| C2 | 任何读取点拿到的都是「当刻值」（不必每处记得结算） | **`battle2/schedule.py` + `effect_triggers.py`** | ✅ 引擎（6 行） |
| D | 推满效果语义（跳过下一动 vs 定身 2.0 刻） | `battle2_bar_procs`（引擎已有 `mode=skip`） | ❌ 数据/装配 |
| E | Boss 阶段保留 50% | `boss_script` 转阶段处 `fire("phase")`（**当前零 fire 点**） | ❌ 上层 |
| F | 反震（受击反弹 30% + 推条 +3） | 装配层 `on_taken`（ctx 已带 `source`/`dmg`） | ❌ 装配 |
| G | 展示/状态面板显示当刻条值 | `commands/combat.py` 等读取处 | ❌ 上层 |

**结论：必须动的是 B/C（核心容器）＋推荐 C2（引擎 6 行）；A/D/E/F/G 全部内容层。**

证据（可复核）：
- battle2 引擎**功能上从不读 `actor["buffs"]`**（`game/battle2/*.py` 里 `buffs` 全是 `hit_buffs`
  局部变量 / docstring / 序列化白名单；`stats._apply_effects` 只遍历 `effects`）→ 条数据 100% 内容层。
- `on_taken` 已带 `source` + `dmg`（`landing.py:139`）→ 反震/反击类动作装配层可写（现成范例
  `services/battle2_we_procs.py:125 we_reflect`，用 `landing.deal_damage` 打回去）。
- `"phase"` 在 `EVENTS` 里**已声明但全库零 `fire` 点** → 阶段保留只缺上层一个 fire。
- `core/battle_bars.py` 的活跃消费方只有 `services/battle2_bar_procs.py` + 两个测试
  （`passive_procs`/`battle_conds` 引用均已随 N10 死亡）→ 容器可放心改造。

---

## §1 核心改动 C1：`core/battle_bars.py` 时间化（必做）

### 1.1 条状态结构（宿主 = 敌方 actor，存 `buffs[bar]`）

| 键 | 类型 | 语义 | 变更 |
|---|---|---|---|
| `val` | **float** | 积蓄（内部小数；展示 `int()`） | int → float |
| `threshold` | int | 当前阈值（触发后 ×1.35，封顶 cap×base） | 不变 |
| `trigger_count` | int | 触发次数 | 不变 |
| `_at` | float | **上次结算时刻**（`battle._now` 口径） | 新增 |
| `immune_until` | float | **免疫截止时刻**（0 = 不在免疫） | 新增 |
| `immune_turns` | int | 读侧兼容 = 剩余免疫刻数（`ceil`）；旧读取方/展示不必改 | 保留（派生） |

### 1.2 API（签名兼容，`now` 为可选关键字——旧调用不传则退化为「不结算」）

```python
bar_state(host, key, now=None) -> dict          # 初始化 _at = now or 0；immune_until = 0
bar_settle(host, key, now, logs=None) -> dict   # 新增：结算到 now（幂等，dt<=0 直接返回）
    dt = max(0.0, now - state["_at"]); state["_at"] = now
    if state["immune_until"] and now >= state["immune_until"]:
        state["immune_until"] = 0.0; state["immune_turns"] = 0     # 到期即出免疫
    decay = float(bd.get("decay_per_turn", 0) or 0)                # ← 不再 int()
    if dt > 0 and decay > 0:
        state["val"] = max(0.0, state["val"] - dt * decay)
bar_gain(host, key, amount, logs=None, now=None) -> float
    bar_settle(...)
    if now is not None and now < state["immune_until"]: return state["val"]   # 免疫期不积蓄
    if state.get("_no_inject_until") and now is not None and now < ...: return  # 自锁防护帧戳
    state["val"] = min(max_val, state["val"] + amount)
bar_should_trigger(host, key, now=None) -> bool
    return val >= threshold and (now is None or now >= immune_until)
bar_trigger(host, key, logs=None, now=None) -> bool
    阈值递增（不变）→ val = 0.0 → immune_until = now + immune_secs
    immune_turns = ceil(immune_secs)（派生，供只读旧字段的读取方）
bar_tick(host, key, logs=None, now=None) -> bool     # = bar_settle + should_trigger（宿主兜底）
bar_preserve(host, key, pct=None)                    # 不变（Boss 阶段）
turn_start_bars(...)                                 # 零调用 → 建议随本批删除（不留半死入口）
```

`immune_secs` 取值：`bd.get("immune_secs")`，缺省回落 `bd.get("immune_turns", 0) × 1.0`
（curse 等 `immune_turns: 0` 行为不变 ✅）。

### 1.3 数值语义换算（可复现验收）

```text
连招三连（hits=3, shaken_gain=5/段）= 一次施放 +15
拳师循环 ≈ 2.2 刻 → 衰减 −1.7 × 2.2 = −3.74 → 净 +11.26
首阈值 50 → 50 / 11.26 ≈ 4.44 次出手触发 → 对齐 v153 §六「约 4.5 次」
阈值序列：50 → 67 → 90 → 122 → 125（×2.5 封顶，A 项）
```

---

## §2 引擎改动 C2：全局时钟事件（推荐，6 行）

**为什么需要**：容器时间化后，衰减由「谁去调 `bar_settle`」决定。读取点分散在
`battle2_cond_procs._p_enemy_broken` / `class_mech_proc` 两个谓词 + 展示层 + 注入点——每处都要记得
结算，漏一处就是脏读。引擎在时钟推进处集中广播一次，内容层只挂声明，读点永远拿到当刻值。

```python
# game/battle2/effect_triggers.py —— EVENTS 元组追加（保持单行）
EVENTS = (..., "interrupt", "time_advance")

# game/battle2/schedule.py —— _advance_time 尾部新增
def _advance_time(battle, dt: float, logs: list):
    if dt <= 0:
        return
    battle._now += dt
    _settle_time_effects(battle, logs)
    from .effect_triggers import fire as _fire          # ← 新增
    _fire(battle, "time_advance", {"dt": dt, "now": battle._now}, logs)   # ← 新增
```

- 语义：通用动词「时钟推进」，与 `turn_start`/`on_taken` 同级；ctx `dt`/`now`，无主体（广播全体）。
- 装配：`battle2_bar_procs._ensure_tick` 在首次挂条时，除现有 `turn_start` 外再自安装
  `{"event": "time_advance", "action": "bar_time_settle", "key": ...}`（只有真挂过条的单位才有条目 → 零噪音）。
- 频率：每次时钟推进一次（与 `turn_start` 同量级，单位数 ≤10）。
- 不做 C2 的退化路径：装配层在每个读点前调 `bar_settle`（当前 4 个读点 + 展示，需逐个记得）。

---

## §3 装配层配套（内容层，不属引擎）

| 文件 | 改动 |
|---|---|
| `services/battle2_bar_procs.py` | `bar_gain_act` 传 `now=battle._now`；新增 `@register_action("bar_time_settle")`；`_ensure_tick` 挂 `time_advance`；`_settle` 传入 `now` 给 `bar_trigger` |
| `services/class_mech_proc.py` | `passive_bar_extend`：`immune_turns += ext` → `immune_until += ext`（同刻度语义）；`target_bar_broken` 判定改 `now < immune_until` |
| `services/battle2_cond_procs.py` | `_p_enemy_broken` 同上改读 `immune_until` |
| `data/battle2_rules.py` | 无（声明表不动） |

## §4 数据层

```python
ENEMY_BAR_CFG["shaken"] = {
    "max": 125,                  # A：对齐 threshold_cap ×2.5 = 125（原 50 = 第二次触发死锁）
    "decay_per_turn": 1.7,       # B：语义澄清 = 每刻，小数累计
    "immune_secs": 2.0,          # C：策划案「触发后 2 刻内不再积蓄」
    "no_inject_on_trigger": True # 消费方落地（触发当帧注入 = 0）
    ...
}
```
清理：`data/classes.py:403-409` 的 `enemy_bar.shaken` **死声明**（零消费方 + `decay_per_turn: 4` 漂移）
建议随批删除——数值单源 = `ENEMY_BAR_CFG`。

## §5 上层（非引擎）

- `commands/boss_script.py` 阶段转换处补 `fire(battle, "phase", {"actor": boss, "from": a, "to": b})`
  → 装配层订阅 `phase` 调 `bar_preserve`（E）。
- 展示读取处（`commands/combat.py` 等）显示 `int(val)`。

## §6 验收门禁（新增，防再漂）

新增 `tests/test_numeric_bar_decay.py` 并纳入 `scripts/run_numeric_tests.py`：

```text
1  每 2.2 刻衰减 = 3.74 ± 0.01（float 语义，非 int 截断）
2  拳师连招三连 4.5 次出手触发一次（模拟注入 15/次）
3  阈值序列 50/67/90/122/125（封顶）
4  免疫 2 刻内注入无效（val 保持 0）+ 免疫到期后可再触发（A 修好后）
5  自锁防护：触发当帧注入 = 0
6  破绽感知：衰减 1.7 → 0.85（半衰，P15 遗留的物理空转项）
7  反震：受击 30 点 → 反弹 9 点 + 攻击方推条 +3
8  Boss 阶段保留 50% 积蓄
```

## §7 待拍板（3 点）

1. **A**：`max 125`（推荐，放开阈值递增）还是 `threshold_cap 1.0`（固定 50 阈值，放弃递增设计）？
2. **C 免疫期语义**：期内注入**忽略**（策划案「不再积蓄」，推荐）还是**保留但冻结触发**（期内不衰减、到期满即触发）？
3. **C2 引擎时钟事件**：本批一起做（推荐——读数一致 + 展示正确）还是先只做 C1 的时间化、读点逐个结算？

## §8 风险与回退

- `val` int → float：序列化自动（白名单保留全部键）；旧存档 int 值天然兼容；展示需 `int()`。
- 阈值 125 后血条「推满」更慢但可多次触发——需实机体感复核（数值门禁能挡退化，挡不了手感）。
- 回退：单 commit 撤回即可（容器 + 配置 + 装配三层同批）；C2 独立 commit，可单独 revert。
