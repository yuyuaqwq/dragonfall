# 审计 T6 — 意见#7：技能升级之后描述不变

- 提出人：鱼鱼本人（qq=1454832774，群 1095961596）「技能升级之后描述不变，看看如何调整」
- 状态：new → ✅ 已修复
- 日期：2026-08-27

## ① 现状核实（根因确认）

| 环节 | 位置 | 现状 |
|---|---|---|
| 『技能详情』渲染 | `game/commands/player.py:1235-1322`（`skill_detail`） | 详情第 4 行 `效果：{info['desc']}`（`player.py:1279`）输出 **静态写死 desc 文本**（数据表 `skills.py` 的 desc 字段，如挥砍「基础斩击，100% 物理伤害…」），**不随技能等级变化** → 升级前后看到的效果描述完全一致，玩家感知不到提升 |
| 升级成长配置 | `game/data/skill_up.py`（SKILL_UP 表：p=每级伤害/治疗倍率 +x%；c=每级条件倍率 +c；m=每 m 级叠层 +1；l=每级吸血 +2%；max=满级） | 数据齐全（覆盖率铁律：每主动技必配） |
| 成长公式 | `game/engine.py:711-746` | `skill_power_mult = 1 + p/100×(lv-1)`；`skill_buff_turns = base + (lv-1)`；`skill_cond_mult = mult + c×(lv-1)`；`skill_mech_val = base + (lv-1)//m`；`skill_lifesteal_pct = base + l/100×(lv-1)` |
| 等级来源 | `game/engine.py:749-760` `skill_level_of` | 兼容 skill_levels key 中文名/ID |
| 既有升级提示 | `player.py:1314-1317` | 只在未满级时展示**下一级**预览（`_skill_upgrade_gains(info, slv+1)`），无「当前等级」数值行 |
| 可复用计算 | `player.py:1404-1423` `_skill_upgrade_gains(info, lv)` | 已实现按等级输出 `伤害 X% / 持续 N 回合 / 条件 ×X / 叠层 N / 吸血 X%`，直接复用 |

**结论**：根因 = desc 静态文本 + 详情页无「当前等级数值」行。战斗内数值实际按等级计算（engine 公式），只是详情页没展示。

## ② 改动清单（最小 diff，仅 1 文件 +2 行）

`game/commands/player.py` `skill_detail` 中，`效果：{desc}` 行之后（第 1280 行 `]` 后）追加：

```python
if is_learned and info.get("kind") != "被动" and mx > 1:
    lines.append(f"📈 Lv.{slv} 当前效果：{' · '.join(self._skill_upgrade_gains(info, slv))}")
```

- 文件:行号：`game/commands/player.py:1281-1282`
- 逻辑：仅 **已学会 + 非被动 + 可升级（SKILL_UP max>1）** 时显示；数值按当前技能等级 `slv = E.skill_level_of(player, skill_name)` 经 `_skill_upgrade_gains`（内部走 engine 成长公式 + SKILL_UP 配置）实时计算；
- 原 `效果：desc` 静态文本保持不变（防玩家混淆），新增行以 `📈 Lv.X 当前效果：` 新格式标注；
- 被动技能（max=1，如战意高涨）与未学会技能不显示该行（符合需求：无成长不展示）。

## ③ 验证（证据）

脚本：`workspace/feedback_fix/verify_T6.py`（`python workspace/feedback_fix/verify_T6.py`）→ **13/13 通过**

升级前（已学 Lv.1）`技能详情 挥砍` 实测输出：

```
📜 【挥砍】｜✅ 已学会 Lv.1/5
类型：物理 ｜ 需求等级：Lv.1 ｜ 消耗：3 魔力
效果：基础斩击，100% 物理伤害。先手(速度高于目标)时伤害＋15%
📈 Lv.1 当前效果：伤害 100% · 条件 ×1.15
⚔️ 条件转化：先手行动时激活『先手压制』(威力 ×1.15)
💡 『技能升级 挥砍』花 1 点升到 Lv.2（伤害 112% · 条件 ×1.2，当前 100 点）
```

升级后（Lv.2）`技能详情 挥砍` 实测输出：

```
📜 【挥砍】｜✅ 已学会 Lv.2/5
类型：物理 ｜ 需求等级：Lv.1 ｜ 消耗：3 魔力
效果：基础斩击，100% 物理伤害。先手(速度高于目标)时伤害＋15%
📈 Lv.2 当前效果：伤害 112% · 条件 ×1.2
⚔️ 条件转化：先手行动时激活『先手压制』(威力 ×1.15)
💡 『技能升级 挥砍』花 2 点升到 Lv.3（伤害 124% · 条件 ×1.25，当前 99 点）
```

- ✅ 升级前后数值可感知变化：Lv.1 `伤害 100% · 条件 ×1.15` → Lv.2 `伤害 112% · 条件 ×1.2`（p=12、c=0.05 成长公式）；
- ✅ desc 静态原文升级前后不变（`效果：` 行一致）；
- ✅ 被动技能「战意高涨」（SKILL_UP max=1）详情 **无** `📈 Lv.` 行，保留「被动技能，无需升级」提示；
- ✅ 未学会技能「裂地斩」详情无 `📈 Lv.` 行；
- ✅ 既有提示行（下一级预览）不受影响。

回归：`tests/test_commands_skills.py`（技能域既有测试，含技能详情用例）→ **41/41 通过，0 失败**。

## 文件清单

| 文件 | 动作 |
|---|---|
| `game/commands/player.py:1281-1282` | 修改（+2 行：当前等级效果动态行） |
| `workspace/feedback_fix/verify_T6.py` | 新建（验证脚本，13 断言） |
| `workspace/feedback_fix/audit_T6.md` | 新建（本报告） |