# 审计：埋点声明 ↔ 发射端对不齐（2026-09-13，导出侧研究附带发现）

> 来源：把奥兰迪亚埋点声明（`game/data/tlogs.json`，18 条）导进框架数据包时的只读研究；
> 下面是**我（主 agent）独立复核过**的部分（读码 + grep 调用点 + 对表），不是二手转述。
> **定性：这些都不是导出/数据包的问题** —— 包忠实搬运了声明表。要修的是游戏仓的**发射端**或**声明**本身。

## 一、真 bug：`battle.end` 在生产路径上永不发出（已复核）

`game/services/battle_tlog.py`：

```
169  def _maybe_end(self, b) -> None:          # 「零侵入」自动收尾
175      if self._end_sent or not self.enabled: return
177      if getattr(b, "result", None):
178          self._end_sent = True              # ← 先置位
179          self.on_end(b)                     # ← 再调用
183  def on_end(self, b, *, ..., force: bool = False) -> None:
187      if self._end_sent and not force: return   # ← 幂等守卫把它挡掉了
```

**顺序反了**：`_maybe_end` 先把 `_end_sent` 置真，`on_end` 的幂等守卫随即 `return` → `battle.end` 一条都不发。

调用点确认（全仓）：
```
game/services/battle_tlog.py:179    ← 唯一的生产调用点（就是上面那条）
tests/test_v182_battle_tlog.py:97   bt.on_end(b, extra={...}, force=True)   ← 手动补发
tests/test_v182_battle_tlog.py:132  bt.on_end(b)
tests/test_v182_battle_tlog.py:195  bt.on_end(b)
```
→ 除测试外**没有**第二个 `on_end` 调用点；生产只能靠 `_maybe_end`，而它被自己的置位挡死。

**后果**：`battle.end` 声明里的 `result / rounds / p_acts` 正是回放闭环的判据
（`tlogs.json` 的 desc 原话：「回放对比就是比这三个」）——闭环拿不到判据，`matched` 恒 False。

**修法（2 行，改 `_maybe_end`）**：
```python
        if getattr(b, "result", None):
            self.on_end(b)          # 先发（on_end 内部不置位）
            self._end_sent = True    # 再置位，保证幂等
```
⚠ **必须同批改测试**：`tests/test_v182_battle_tlog.py:97` 现在用 `force=True` 手动补一条，
并在 :115-116 断言「自动收尾只发一条 battle.end（幂等）」——修好后自动路径会先发一条，
那条手动补发就变成第二条 → 套件会红。正确改法是让该用例**依赖自动路径**（删掉手动 `on_end(force=True)`，
或改为断言「自动 1 条 + force 1 条 = 2 条」并说明为何这么测）。

## 二、声明 ↔ 发射端字段漂移（7 处，已复核声明侧）

声明表（`game/data/tlogs.json`）与发射点实际写的字段对不上（`KindTable.check_record(strict=False)` 只上报不抛，
所以一直没暴露）：

| kind | 声明字段 | 发射端实际 | 差异 |
|---|---|---|---|
| `battle.hit` | caster / subject / dmg / **crit** / skill | 见 `battle_tlog.py:162-166` | `crit` 只在 `is_crit` 存在时才写 → **常缺** |
| `battle.crit` | caster / subject / dmg | 同上 | 多发 `skill` |
| `battle.taken` | caster / subject / dmg / **real** | 同上 | `real` 常缺；且攻击者 `source` 被丢弃 |
| `shop.buy` | item / qty / unit_price / gold_after | 调用点发 `key / qty / discount` | 字段名与集合都不一致 |
| `instance.clear` | iid / rounds / deaths | 调用点发 `iid / first_clear` | 集合不一致 |
| `drop.grant` | item / qty / source | `reward.py` 发 `exp / gold / items` | 集合不一致 |

另有 6 个 kind（`quest.accept` / `quest.done` / `shop.sell` / `instance.enter` / `level.up` / `travel.move`）
**已登记未接线** —— 设计稿 `docs/REFACTOR_tlog_landing.md:152` 明说「先登记词表、暂不埋点」，**这是意图，不是 bug**。

**建议修法**：二选一，但**别两边各改一半** ——
① 声明向发射端对齐（改 `tlogs.json` 的字段集）；或 ② 发射端向声明对齐（补/改字段）。
另加一条门禁：跑一场战斗，把每条记录喂 `KindTable.check_record(strict=True)`，不一致即红
（现状是「只上报」，所以漂移能活很久）。

## 三、怎么复现

```bash
cd C:/Users/yuyu/qqbot/data/plugins/dragonfall
# ① 看调用点
grep -rn "\.on_end(" game/ tests/ --include=*.py
# ② 看声明表
python -c "import json;d=json.load(open('game/data/tlogs.json',encoding='utf-8'));print({k:v.get('fields') for k,v in d.items()})"
# ③ 跑一场战斗看实际发出的 kind（研究期实测：只出 battle.start / battle.act）
python tests/test_v182_battle_tlog.py
```

> 包侧现状：`games/orlandia/content/data/tlogs.json` = 真源**原样照搬**（18 条，逐字节可复现），
> 所以上面这些漂移在包里也能看见（这正是数据包的价值：把「声明与实现不一致」摆到明面上）。
