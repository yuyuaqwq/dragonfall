# 技能可用性契约（放不放得出 / 何时能再放）

> **一句话**：一次技能施放要过 **4 道判据**，全部由**引擎侧强制**；
> `cd` 存的是**绝对时刻**（不是「还剩几回合」）。

本页是 2026-09-11 引擎契约修复的沉淀（第三方骨架作者实跑暴露的两个缺口）：
冷却未被强制、AI 选招不做可执行性过滤。改动前 `actor["cooldown"]` 的**唯一读者是 AI 谓词**
`cd_ok`——写进去没人查，玩家侧等于零冷却。

---

## 1. 判据链（`actions.do_skill` 顺序，`actions.py:62`）

| # | 判据 | 实现 | 不满足时 |
|---|------|------|----------|
| 1 | 技能可**解析** | `ActCtx.__post_init__` 查 `actor["_skill_index"]`（**无全局兜底**） | `info={}` → 空动作，白耗一回合 |
| 2 | **冷却** | `_skill_usable` → `_cd_left_of`（`actions.py:141` / `:121`） | 拦截文案 + 不扣费 / 不写冷却 |
| 3 | **魔力 / 核心资源** | `_skill_pay_of`（`actions.py:266`）折算后比对 `mp` / `effects[key].stacks` | 拦截文案（同 2） |
| 4 | kind 分派执行 | `_do_heal` / `_do_buff` / 伤害管线 | — |

判据 2、3 **只对「学习过该技能的 actor」有意义**，但冷却检查**对全部 actor 生效**
（怪也有 `cooldown` 表）——调用点不再以 `class_name` 为门槛（`actions.py:78`）：

```python
# ---- 1. 技能可用性校验（冷却：全 actor 一视同仁；资源：职业 actor）----
if not _skill_usable(battle, actor, info, logs):
    return logs
```

### 静默探测 vs 玩家文案

`_skill_usable(battle, actor, info, logs=None)`：`logs=None` = **静默探测**，只返回判据、
不产生文案（给 AI 用）。**判据必须与文案解耦**——不要在 `logs is None` 时把整个检查短路，
否则静默探测恒判「可用」，AI 照样选放不出的招。

---

## 2. `cd`（技能冷却）语义

| 环节 | 约定 |
|------|------|
| **声明** | 技能表 `"cd": 12`，单位**刻**（CTB 刻度）。`0` / 缺省 = 无冷却 |
| **写入** | `actor["cooldown"][info["name"]] = battle._now + cd`（`actions.py:100`） |
| **key** | **技能显示名**（`info["name"]`，不是技能 key）——内容改名会让旧条目失配（无害：自然到期） |
| **读取** | `_cd_left_of` = `due - battle._now`；`<= 0` 视为就绪，顺手 `pop` 到期条目（惰性清理，防表无限增长） |
| **修正** | `cd_mult`：态内冷却加速，取多态**最速**（`min`），`max(1, …)` 保底 1 刻（`actions.py:88-99`） |
| **展示** | `combat.py:1684-1686` 技能列表按声明值显示 `冷却 N 刻`（静态展示，非剩余值） |

**绝对时刻制**（v152 `CTB_EVENT_QUEUE_REFACTOR` 起）：值 = 施放时刻 + cd，
用 `battle._now` 比较。**不要**把它当回合计数做 `-1` 递减。

---

## 3. 三个消费方（谁在强制）

| 位置 | 角色 | 行为 |
|------|------|------|
| 引擎 `do_skill`（`actions.py:62` 定义 / `:78` 调用） | **唯一强制点** | 拦下并返回 `⏳ 【X】冷却中：还需 N.N 刻！`；不扣费、不写冷却 |
| AI 决策器 `ai._skill_castable`（`ai.py:118`） | **静默判据** | 不可执行 → 跳过该 move（不产生玩家文案） |
| 命令层 `combat.py`（`:1335-1355`） | **体验预检** | 冷却中直接回话，**不扣体力、不耗回合**（对齐同区 `魔力不足` 的既有做法） |

> 命令层预检是体验优化，引擎拦截才是**契约**：脚本、AI、第三方集成直调 `human_act` 时，
> 只有引擎那道拦得住。

---

## 4. AI 决策器：可执行性过滤

`resolve_ai_move`（`ai.py:187`）选招后逐条过滤：

```
priority：从上往下第一个 when 全满足 **且 可执行** 的 move
weighted：when 命中的 move 先过滤，再按 weight 重抽（过滤后池空 → 回落）
全部不可执行 → 返回 None → 引擎回落普攻
```

`_move_castable`（`ai.py:139`）判据：
- `action` 不是 `skill` → 可执行（普攻/防御等）
- `skill` move：技能名要能**索引到**，且过 `_skill_castable`（冷却 / 资源 / 已学）
- `action=skill` 但无技能名 → 不可执行（`do_skill` 会空转）

### 为什么必须过滤（原 bug）

```
命中的招放不出（冷却中 / 资源不足）
  → do_skill 在资源判据处提前 return（冷却写在它之后）→ 冷却永不写入
  → cd_ok 恒真 → 每回合都选中它 → 永远放不出
  → 0 输出活锁，直到被打死（多人 / 世界 Boss 会中）
```

---

## 5. 运行期换招：`refresh_skill_index`

`_skill_index` 只在 **Battle 构造期**与 `add_actor` 建一次（`battle.py:217` / `:174`）。
剧本导演 / 机制在运行期 append `actor["skills"]`（转阶段换招）后，**索引会落后**：

- 症状：阶段新招解析不到 → `auto_act` / AI 选它 = 空放（掉一次出手）
- 修法：引擎在决策前调 `refresh_skill_index(actor)`（`battle.py:151`），
  幂等且快路径（技能数一致则直接返回）；
  取用点 = `human_act`（`:261`）与 `actor_auto`（`:352` 前后）

内容侧**不需要**手调——但要知道这条规则：**换招后索引自动跟上**，
前提是「append 进 `actor["skills"]`」这件事真的发生了。

---

## 6. 陷阱清单

1. **别把 `cd` 当回合数**——存的是绝对时刻，比较对象是 `battle._now`。
2. **别用 `logs is None` 短路判据**——那会让静默探测恒「可用」。
3. **内容侧 AI 声明的技能必须在该 actor 的 `skills` 里**（阶段追加要保证语句真执行）；
   `tools/audit_ai_moves_resolvable.py` 可审计。
4. **`cd` 只在战斗内生效**——脱战治疗无 battle 实例、无冷却表（既有设计选择，见 `combat.py:1212`）。
5. **冷却 key 是显示名**——重命名技能等于放弃旧冷却条目（无害，但别指望迁移）。

---

## 7. 相关测试与工具

| 类型 | 路径 | 覆盖 |
|------|------|------|
| 回归 | `tests/test_battle2_cooldown_enforce.py` | 54 断言：冷却写入/拦截/到期放行、AI 三判据、priority/weighted 过滤、活锁回归、索引自愈 |
| 探针 | `tools/probe_cooldown_enforcement.py` | 实跑取证：`cd` 声明 → 连续两次施放是否都命中 |
| 探针 | `tools/probe_phase_skill_index.py` | 转阶段换招 → 索引是否自动补上 + 新招真能打出 |
| 审计 | `tools/audit_ai_moves_resolvable.py` | 全部配 AI 的怪：AI 引用的招能否解析（三分类） |

---

## 8. 变更记录

| 日期 | 变更 |
|------|------|
| 2026-09-11 | 补装冷却强制（原 N10 重写丢失）：`_cd_left_of` + `_skill_usable` 冷却判据 + 全 actor 生效 |
| 2026-09-11 | AI 决策器加可执行性过滤（`_skill_castable` / `_move_castable`），修 `cd_ok` 活锁 |
| 2026-09-11 | `refresh_skill_index`：运行期换招索引自愈 |
| 2026-09-11 | 命令层冷却预检（不扣体力/不耗回合）；`_skill_usable` 判据与文案解耦 |
