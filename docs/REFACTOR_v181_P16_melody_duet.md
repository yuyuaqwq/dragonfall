# v181.M-passive P16：二重唱（melody_duet）实装（2026-09-10）

G6 收口：**圣化（信念·圣化 `faith_overload_heal`）早已实装并有测试**（`class_faith_overload`
读 `_learned_proc` + passive dict `heal_up`，验收 `tests/test_passive_p8.py`：对照组 0.015 /
圣化组 ×1.3）——本批只补 G6 的另一半：二重唱。

## 实装

| 项 | 数据（`skills.py:3711`） | 实装 |
|---|---|---|
| 二重唱 `melody_duet` | 诗人 lv44 `{"proc": "melody_duet", "add": 1}` | `act_cast` 动作 `passive_melody_duet`：`mech == melody_chant` 且已有旋律驻留（`name` 非空、强度 >0）→ 强度 `min(上限, +add)`，驻留光环按新强度重写 |

语义源 = 旧 `battle.py`（`379a792^`）`_skill_buff` 吟唱段（6208-6222）+ `flag_set_cond`
melody_duet 分支逐字：`add≤0` 不触发 / 无驻留不触发 / `min(max_stack, stack+add)` /
日志「二重唱，旋律强度额外 +1！（N/5）」。

顺带收口：
- `_MELODY_MAX_STACK = 5` 提为常量（原先 `class_melody_act` 里两处硬编码 `5`）——吟唱 cap、
  巅峰日志、二重唱共用一处来源。
- **顺序契约（同 bar_gain）**：`class_melody_act` 改为 `insert(0)` 排 `act_cast` 首位
  （原先 append，被动族先装配 → 二重唱会跑在基础叠层之前，读到旧强度）。同时补幂等去重。
  两处契约（bar / melody）在各自装配点 docstring 已写明。

## 验收

`tests/test_melody.py` 34/34（新增第 8 组）：
装配 ±（add=1 / judge mech_eq melody_chant / 未学不挂 / 首位顺序）/
唱新歌不触发（强度 1）/ 吟唱后 3（基础 +1 + 二重唱 +1）/ 再吟唱 5（cap）/
换歌回 1（不误加）/ 对照组（无二重唱）吟唱后 2。

全量 236/236 + 数值门禁 13/13。

## 剩余（不动）

- melody 数值公式（`pct × (1+0.25×(stacks-1))`）与 **`e_` 减益系 5 技能**仍标待 v153 重做
  ——见 roadmap G1（挽歌系，M 量级，可独立做）。
- G4 旋律驻留期不能普攻（v153 代价）：多攻击入口软拦截，S 量级，未做。
