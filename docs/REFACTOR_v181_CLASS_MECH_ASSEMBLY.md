# battle2 职业机制装配层（mech 兑现/资源渠道）——R1 侦察蓝图 v1

> 2026-09-09 鱼鱼拍板"资源走 effect"后的施工蓝图（承接 N9.7 affix 分档遗留：
> 资源型 20 + 职业机制 12 词条 + 技能 mech 兑现缺口）。P0 侦察定稿，可据此分批实施。

## 1. 目标与边界

- **目标**：让技能表 40+ mech 值 + core_resources 渠道在 battle2 上完整生效——
  攒层（叠层）✅ 已通；**兑现/消费（终结技/引爆/倾泻）⬜ 缺口**；渠道喂养 ⬜ 缺口。
- **北极星**：引擎零职业知识零改动；全部落**装配层**（register_action 动作族 +
  EVENTS 事件钩子 + EFFECT_RULES/EFFECT_ACTIONS 声明表）。
- **不做的**：不改 skills 数据/desc；不考古旧 battle.py 单怪编排（语义参考 git 历史 +
  退役测试 + desc，按 battle2 CTB 语义重写）。

## 2. 现状分层（侦察结论）

| 层 | 状态 | 证据 |
|---|---|---|
| 叠层写入（技能 mech 命中攒层） | ✅ 已通 | effects.py `_mech_to_effect`（叠层资源型 apply op=add）+ EFFECT_RULES cap/stat_scale |
| 叠层自动折算（每层伤害/攻击加成） | ✅ 已通 | stats._apply_effects stat_scale（rage +12%/层、zhan_yi atk +4%/层） |
| DOT/控制/标记 | ✅ 已通 | EFFECT_RULES period/consume + EFFECT_ACTIONS 名词路径（stun/freeze/bleed/burn/poison/mark 族） |
| 兑现/消费动作（finisher/zhan_yi_cash/element_burst/faith_unload/poison_burst…） | ⬜ **缺口** | skills mech 值 40 种中兑现型无注册动作 → 技能半残（终结不按连段加成、引爆不爆、信念卸不掉） |
| 资源获取渠道（core_resources on_* / regen） | ⬜ 缺口 | 装配层无事件钩子写叠层（普攻+1 怒/治疗+2 信仰/自然回） |
| 词条微调（rage_forge 上限+2 等 32 条） | ⬜ 缺口 | affix 翻译器只覆盖 42 条，资源型未接 |
| 展示 | ✅ 部分 | combat 1838 已读 effects 叠层；_resource_line 旧 player.resources 残留待改 |
| 死字段 | — | player["resources"]/副本快照/engine.core_resource_* 待清理 |

## 3. ⚠️ 版本漂移警示（实施前必读）

职业机制经 v130→v139→v151→v153→v161 多轮重做，**数据源间存在漂移**：

- `core_resources.py`（v130.2）写战士 key=rage"满 10 掷背水一战"——但 skills 现用
  技能 mech **全是 zhan_yi（战意）**，无 rage mech 技能、无背水一战 → v151 后战士资源
  已是战意，rage 只残留在 EFFECT_RULES（dmg_mult 条目）与 core_resources。
- **语义权威判定顺序**：① skills.py 技能 desc（最新策划文案）② EFFECT_RULES 注释
  ③ 退役测试断言 ④ git 历史 battle_mech/battle.py（最旧，v151 前语义，只作参考）。
- 不确定的 mech 语义 → 先查 desc，再 grep 退役测试同名断言，禁止照旧 handler 硬抄。

## 4. mech 分派矩阵（skills.py 现用 40 值 → 落点）

类别 A = 叠层（已通，无需做，验证即可）；B = 兑现缺口（本蓝图主活）；C = 控制/标记（已通）；
D = 需查语义（desc 不明/可能死数据）。

| mech | 技能数 | 规则表 | 类别 | 语义源（desc 摘要） | 落点 |
|---|---|---|---|---|---|
| zhan_yi | 9 | ✅ cap10 atk4% | A | 每段命中积战意，满10狂暴 | — |
| lian_duan | 3 | ✅ cap10 | A | 命中积连段 | — |
| arcane | 3 | ✅ cap10 | A | 充能+1 | — |
| melody / melody_chant | 14 | — | D | 歌者驻留/吟唱强度（共鸣/回声系统） | 需单独设计（非叠层语义） |
| finisher | 3 | — | **B** | 终结：连段越高伤害越高（每段+10%），结算归零 | 兑现动作+dmg_calc 钩子 |
| zhan_yi_cash | 1 | — | **B** | 花 5 层战意 → 回 20% 生命+清 | 兑现动作 |
| zhan_yi_fury | 1 | — | **B** | 花 4 层战意，无视防御一击 | 兑现动作+dmg 钩子 |
| element_burst / _all / _3 | 3 | — | **B** | 引爆元素印记连锁/裁决/引燃迸发 | 兑现动作（读 fire/ice/thunder_mark 层） |
| element_multi_mark | 1 | — | A/B | 双色流光 2 段各挂印 | 已挂印（fire/ice_mark 叠层通），引爆缺 |
| arcane_burst | 2 | — | **B** | 倾泻全部奥术能量/奥能脉冲 | 兑现动作（耗 arcane 层） |
| faith_unload | 1 | — | **B** | 卸除 3 点信念 | 兑现动作 |
| poison_burst / poison_burst_finisher | 2 | — | **B** | 引爆毒层喷涌/体内毒素爆裂 | 兑现动作（读 poison 层） |
| guard_core_burst | 2 | — | **B** | 引爆磐核/气力汇拳 | 兑现动作（拳师破绽体系需查） |
| sacrifice | 1 | — | D | 献祭骸骨（死灵） | 查（可能召唤系，无 pet 引擎？） |
| curse / curse_refresh / bone_rush | 3 | — | D | 死灵咒/刷新 | 查（可能 v153 后新职业未入表） |
| stun/silence/spd_down/burn/bleed/poison/corros/fire_mark/ice_mark/thunder_mark/hunt_mark/soul_mark | 23 | ✅ | C | 控制/DOT/标记 | — |

## 5. 兑现动作技术通道（两类挂钩，全部装配层）

```
通道 1 · 伤害前修正（dmg_calc 事件钩子，EVENTS 已有）
   finisher：dmg_calc 读 caster effects.lian_duan.stacks → ctx 乘区 ×(1+0.10×n)
   zhan_yi_fury：dmg_calc 无视防御（def 减免置 0）
   兑现动作：技能结算后（act_done/技能尾）清层

通道 2 · 伤害后兑现（register_action 动词，技能名词/尾段调）
   mech_cash（通用：读 key 层数 → 附加伤害 = total×n×pct → 清层）
   用于 element_burst 族/poison_burst/arcane_burst/shield_burst/rage_burst
   zhan_yi_cash / faith_unload：层数转治疗/卸除（读层 → heal/减层 → 文案）

挂载方式：EFFECT_ACTIONS[mech] = [{"action": "<装配动作名>"}] +
           新 services/class_mech_actions.py 里 @register_action 实现
```

## 6. 渠道层（R2）技术方案

- core_resources on_attack/on_hit/on_skill/on_heal → 装配层注册 EVENTS 对应时机
  （on_attack 等已有事件位），读 actor class → CORE_RESOURCES[cls].on_* → 叠层 +n。
- 受击攒怒（blood_bath 词条 on_taken）→ EVENTS taken 时机。
- regen 自然回（energy 18/刻）→ EFFECT_RULES 资源条目声明 period dir=gain（需
  schedule period 加 gain 方向，引擎小扩展声明级）；或装配层 turn 事件钩子（先例：
  回春走 period 时间驱动拍板——倾向 period dir=gain 一致化）。
- 满溢转盾 overflow_shield → 叠层 cap clamp 时溢出转 shield（装配层动词）。
- 版本漂移处理：以 skills/EFFECT_RULES 现用为准，core_resources 渠道字段逐步并入
  battle2_rules（单源化）；v130 残留（rage 渠道/背水）不接，标死数据待清。

## 7. 分批实施（R1 兑现族先行）

> 🔴 B 类细分修正（2026-09-09 逐技能 desc 核对后）：
> - **B1 caster 层乘区清层**：arcane_burst（燃尽充能每层+15%，满5层×1.75——需核对
>   EFFECT_RULES arcane cap vs desc"满5层"漂移；focus 架设只烧一半=v139 形态缺口）
> - **B2 target 层兑现**（读 target 印记/毒 → 加成 + 清 target）：element_burst_all
>   （每层+12%）/element_burst_3（每系×1.2）/poison_burst（每层+15% 上限×1.75）
>   /poison_burst_finisher（毒+连段归零混合）——模式需 owner=target 方向扩展；
>   ⚠️ element_burst lv16 基础版"结算印记触发元素反应"= 元素反应系统（单独设计，非本轮）
> - **B3 主动施放兑现**：zhan_yi_cash（花5战意回20%血+清1减益）——技能施放时检查，
>   非命中事件通道；需施放点钩子设计
> - **B4 形态技**：zhan_yi_fury（花4战意无视门槛进狂暴）——v139 dual_form 形态层
> - **B5 效果声明缺失**（非兑现）：curse（全队对其伤害+20% 8刻，同 soul_mark 族——
>   EFFECT_RULES 补声明即生效）/curse_refresh（刷新 target 效果时长，需动作）
> - **B6 召唤/骷髅计数**：bone_rush（消耗骷髅每只+90%暗蚀）/sacrifice（暗蚀）——
>   无召唤物引擎原语，超范围记录
> - **B7 磐核**：guard_core_burst（消耗全部磐核每枚+70%）——磐核层来源待查（拳师）
> - **melody/melody_chant**：歌者驻留旋律 14 技能——单独系统评估（非叠层非兑现）

| 批 | 内容 | 验收 |
|---|---|---|
| R1a | finisher 族（样板）✅ dd92807 | 声明驱动 v2 形态 |
| R1b | B2 target 方向兑现（element_burst_all/_3 + poison_burst 族 + arcane_burst 若 cap 无漂移）| owner=target 执行器 + 声明 + 测试 |
| R1c | B3 heal_clear（施放点钩子设计先行）+ B5 curse 效果声明 | — |
| R1d | B4/B6/B7/melody 评估记录 | 缺口文档更新 |

## 8. 验证策略

- 语义源：skills desc → 退役测试（tests/_retired_old_engine/test_v107_mech.py /
  test_v1302c_mechanics.py / test_v1252_mech_behavior.py 等 688 处资源命中）→ 旧 handler。
- 新测试：tests/test_class_mech_actions.py（装配动作直测：构造 actor+effects 层 →
  施放兑现技能 → 断言伤害加成/清层/文案）。
- 每批独立 commit（v181.M-xxx）；全量 run_all 209 绿。
