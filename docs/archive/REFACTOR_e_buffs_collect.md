# e_buffs 老共享 dict 收口 — 侦察 + 改动方案（wt_ebuffs）

> 触发：鱼鱼 2026-09-07 晚反馈古王"内战"→ 4006b55 已修伤害日志显示错位（显示层读 _target_ctx）。
> 但根因（敌方 buffs 双路径并存）未除。鱼鱼拍板：**彻底改掉 + 不做旧存档兼容**。
> 本文件 = 收口前侦察清单 + 方案（未改 game/ 代码，纯设计）。

## 现状（全仓 173 处 e_buffs，12 文件）

| 文件 | 处数 | 性质 |
|---|---|---|
| game/core/battle_mech.py | 46 | 写入为主：battle.e_buffs["mon_atk_down"/"mark"/"stun"/"sleep"/...]=N |
| game/battle.py | 32 | property 定义 + 序列化 + 读写 + 衰减 |
| game/core/affix_effects.py | 31 | 写入为主：battle.e_buffs[...]=...（词条对敌 debuff） |
| game/core/_we_executors.py | 17 | 写入：特效对敌 debuff（slow/stun/heal_down/weaken） |
| game/core/battle_conds.py | 11 | 读取：条件判定 "freeze" in battle.e_buffs / stun/silence/mark |
| game/commands/instance.py | 10 | 序列化 st["e_buffs"] 存取/清空 |
| game/core/passive_procs.py | 8 | 读/写目标 buffs（部分已用 ctx["tgt_buffs"]=u.buffs 新路径） |
| game/commands/combat.py | 7 | 显示 L1687 for k,v in (b.e_buffs).items() + PVP 存档 L2517/2558 |
| game/core/weapon_effects.py | 6 | 写入：spd_down/freeze |
| game/store/battle_state.py | 3 | 状态存取 |
| game/engine.py | 1 | 注释/文档 |
| game/core/food_effects.py | 1 | 写入：spd_down |

## 双路径根因

- 老代码（单怪时代）：敌方 buffs 直写共享 `self.e_buffs` property
  （battle.py L1120-1126：`return self.enemy.setdefault("buffs", {})` = **主怪别名**）。
- 新代码（v177 actor 化后）：每怪 `u["buffs"]`（_enemy_turn L3134/3146 写 e=具体 unit；
  `_tgt_buffs()` L1830 读 `_tgt().setdefault("buffs",{})`；_tgt = _target_ctx 或 enemy）。
- **多怪（古王+王冠核心）时**：core 执行器写 battle.e_buffs → 全挂主怪；副怪该中的
  debuff 挂错人。显示层 combat.py L1687 只读主怪 e_buffs → 副怪 buff 状态栏不可见。

## 收口方向（候选 A：改 property 语义 — 最优雅但需精细）

把 e_buffs property 从"主怪别名"改成 **"当前战斗上下文敌方目标 buffs"**：
```python
@property
def e_buffs(self) -> dict:
    """v181 收口：目标级 buffs（= 当前管线目标 _tgt()，非固定主怪）。
    单怪/无管线上下文退化主怪（行为不变）；多怪管线中写=正确目标。"""
    return self._tgt().setdefault("buffs", {})
```
- 优点：core 执行器 69 个写入点 + 读点**零改动**自动落到正确目标；
  命令层显示（读 b.e_buffs）也自动跟当前目标。
- ⚠️ 风险：`_tgt()` = `_target_ctx or enemy`；`_target_ctx` 仅技能管线短暂设置
  （L6702/7706 设置、L6707/7743 恢复），**非管线写 e_buffs 会退化主怪**。
  需逐点核对：哪些 e_buffs 写发生在管线内（_target_ctx 有效）→ 自动正确；
  哪些在管线外（回合 tick/序列化/命令层）→ 需显式指定目标。

### 需要保留主怪语义的点（不能盲改 property）
1. **序列化 L1269** `"e_buffs": self.e_buffs` — 存档敌方 buffs。多怪时应存每怪自己的，
   或保持主怪存档键（读取端兼容）→ 由 P3 状态容器统一（enemies[] 里已含每怪 buffs，可弃用该键）。
2. **命令层 combat L2517/2558**（PVP 恢复/保存 b.e_buffs）— 需看是单怪 PVP 还是多怪。
3. **命令层 instance.py 10 处** st["e_buffs"] — 副本状态存取，同上。
4. **衰减 L9453 附近**：已有"副怪 buffs 不衰减"修正注释（v180G B4），读点可能已扫每怪。

## 推荐实施批次（每批独立 commit + 测试）

- **B1（battle.py 内部写读点收口）**：battle.py 6 个直写 e_buffs（L2840/5205/5227/5228/7484/10100）
  → 改 self._tgt_buffs()（或对应 actor.buffs）。这些在技能/受击管线内，_target_ctx 有效。
  顺带把 e_buffs property 语义改为 _tgt() 别名。
- **B2（core 执行器）**：battle_mech/affix_effects/_we_executors/weapon_effects/food_effects
  ~100 处 battle.e_buffs → battle._tgt_buffs()。若 B1 改了 property 语义则这些零改动自动正确——
  **取决于 B1 采取 A（改 property）还是 B（逐点改）**。
- **B3（命令层显示/恢复）**：combat L1687 状态栏读当前显示怪 buffs（需拿到"当前怪"上下文）；
  instance/combat PVP 存取按每怪。
- **B4（序列化）**：弃用/降级 st["e_buffs"] 键（enemies[] 每怪 buffs 已含）；不做旧档兼容（鱼鱼拍板）。
- **B5（battle_conds/被动读点）**：读 battle.e_buffs 的条件判定按"判定目标"改 _tgt_buffs()。

## 验证
- 每批 py_compile + 相关单测（战斗族：test_v1252_mech_behavior/test_v1302c/test_v138_dot/全量 numeric）
- 多怪行为专项：构造古王+核心双怪，核心中 debuff → 断言核心 u["buffs"] 有、主怪无；状态栏显示正确
- 全量 run_all 对照基线
