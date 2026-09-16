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
  battle_rules（单源化）；v130 残留（rage 渠道/背水）不接，标死数据待清。

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

---

# v139 形态层设计留档（源 core_resources.py 退役迁移 · v181.M-R2b）

> 2026-09-09 v181.M-R2b：`game/data/core_resources.py`（v130.2 资源表）退役——战斗资源
> 名/cap 单源化到 EFFECT_RULES（battle_rules.py），engine.core_resource_def/def_by_key 删除，
> 4 处调用点（combat 脱战校验/技能表、potion_effects、battle_bridge v139 注入）改读新源。
> 本文件保留旧表内 **v139 职业融合形态层设计原文**（dual_form/focus/vent/vow/resonance/echo），
> 字段值/注释要点逐项抄录，作为未来形态层（B4 形态技 / focus 架设态）实施参考。
> ⚠️ 该层尚未实现：v139 字段仅数据定义，引擎无形态机消费（battle_modes/battle_conds 为空壳）。
> v151+ 职业机制重做后旧渠道字段（on_attack/on_hit/on_skill/overflow_shield 等）多数无消费端，
> 有效部分（energy regen 18/start_full）已由 R2a 迁 EFFECT_RULES energy 条目（period dir=gain）。

## 0. v139 签名字段总述（旧 core_resources.py 模块 docstring 原文摘录）

v139 职业融合签名字段（2026-08-29 · 参考 design/new_world/参考_云海猎团职业融合_v139_*.md）：
仅新增数据字段，不动既有 key/max/regen/on_* 字段；字段缺失时引擎默认不启用：
- dual_form（双形态）：cls_zhan_shi 狂暴 / cls_dragon_oath 龙焰 / cls_shadow_blade 影舞 / cls_wu_sheng 蓄势·倾泻
- focus（架设/凝滞态）：cls_fa_shi 元素架设 / cls_chronomancer 时间凝滞
- vent（节流阀/排气）：cls_you_xia 凝神屏息 / cls_wild_hunter 猎印强制排气
- 其余 v139 落点：vow 圣律（守线神谕副资源）、idle_floor_turns（暗影神谕亡灵祭仪保底律）

v130.2 三大口径（背景）：
1. 基础职业瘦身 = 通用基底；专属花活下放转职线（攻线/守线/隐藏线）。
2. 法师例外：基础法师无任何核心资源（纯蓝施法），元素亲和充能条(0-5) 是攻线·元素法师 /
   守线·奥秘法师 转职首获的专属资源（旧表 cls_fa_shi 保留 element 定义作多分支共用根，on_* 渠道全 0）。
3. 牧师歌者双资源 = 共鸣(resonance) + 回声(echo)：攻线歌者转职后专属。

## 1. cls_zhan_shi · dual_form 狂暴（攻线狂战士双形态）

旧表注释原文：满怒入狂暴（免费切换不占行动）→ 双段普攻 + 维持 -1 → <4 强制回斧（无惩罚）
```python
"dual_form": {
    "enter_requirement": 10,    # 入狂暴门槛（怒气 ≥10，可战前下调到 7）
    "maintain_cost": 0.6,       # v153：狂暴中每刻 -0.6 怒气（v151 为 1，v153 §1 标定）
    "hit_cost": 1,              # 狂暴中受击 -1 怒气
    "hit_cost_cap": 1,          # 单刻受击至多 -1
    "force_return": 4,          # 怒气 <4 强制回斧（无惩罚）
    "return_penalty": "none",   # 强制回斧无惩罚
    "form": "fury",             # 狂暴形态资源键
}
```
v130.2 口径：基础战士只留「普攻/技能/受击三路攒怒 → 满怒大招 背水一战」骨架；
血债怒火/沸血二段/破墨之志 → 攻线狂战士/狂战统领；血誓壁垒/守誓坦化 → 守线盾卫士。
v130.2.1：满溢转盾（overflow_shield）开放——满 10 后受击溢出转 5 护盾（overflow_ratio: 5, v176 ×5 系数数据化）。

## 2. cls_fa_shi · focus 元素架设 / 深度冥想（守线）

旧表注释原文：状态型开关（与狂战士「资源型双形态」并列的免费切换家族第二例）：开启后魔法技能
伤害 +40%（pmult 连乘，SKILL_PMULT_CAP=6.0 封顶）、受击 +20%、不能普攻/技能/换系（可防御/道具/
逃跑）、施法命中充能额外 +1、被打断只掉 1 层充能不清零、被控强解；主动解除免费无损（不占行动）。
守线深度冥想 = 守线版：增伤同 +40%，架设中每刻开始 arcane 叠层 +1，奥术脉冲燃尽改烧一半。
架设只在转职后（evolve_path≥1 && class_tier≥1）可用——基础纯蓝身份不动。
```python
"focus": {
    "enter_turn": 1,            # 进入占 1 刻（施放「元素聚焦/深度冥想」开启技，当刻不出伤）
    "dmg_bonus": 0.40,          # 架设中魔法技能伤害 +40%（乘区挂 pmult 连乘，受 SKILL_PMULT_CAP=6.0 封顶）
    "taken_bonus": 0.20,        # 架设中受击伤害 +20%（走 _damage_actor 惩罚分支，同熔核之心 reduce_all<0 先例）
    "max_turns": 3,             # 维持上限 3 刻（时间过载自动解除）
    "free_exit": True,          # 主动解除免费、无损、不占行动（同狂战士「免费切换」承重墙）
    "no_burst_skills": True,    # 架设中不能普攻/技能/换系（元素跃迁视为换系被拦）；可「防御」「使用 <道具>」
}
```
element 落地口径（勿改 on_skill=1，否则基础法师每施放一次白加 1 充能破坏「纯蓝」）：转职后由
元素法师/奥秘法师技能显式 res_gain{element:1} 挂载、充能条随技能生效。

## 3. cls_you_xia · vent 凝神屏息（v153 废弃，专注流量制）

v153 专注流量制：废弃 v139 凝神屏息（vent 自动排气），专注是持续流量非攒满爆发。
```python
"vent": {
    "trigger": 999,              # v153：废弃凝神屏息（专注流量制），trigger 999 永不到达
    "reset": 0,                 # 触发后精力归 0
    "seg_bonus": 1,             # 下刻低耗档技能 段数 +1（疾风连射 2→3、双重射击 2→3、致命连射 4→5…）
    "vent_on_dodge": 15,        # 闪避成功泄压量（-15 精力，把精力从 100 拉回 85 推迟强制屏息）
    "max_delay": 1,             # 深排：凝神屏息可延迟 1 刻释放，段数加成持续 2 刻
}
```
energy 现网口径（R2a 已迁 EFFECT_RULES）：name=精力 cap=100 start_full=True start_classes=[cls_you_xia]
period {dir=gain, interval=1.0, amount=18}——每刻自然回 18，开局满额。

## 4. 歌者双资源（牧师攻线分支 · 共鸣 resonance + 回声 echo）

架构落位结论（旧表注释要点）：歌者 = cls_mu_shi 攻线分支（吟游诗人→灵魂歌者→黎明颂者），
是分支而非独立 class；旧 battle.py `core_resource_def(cls)` 只按 class_name（转职后仍 = cls_mu_shi）
解析单资源 → 转职歌者后仍只会取到 faith。故 resonance/echo **以资源 key 直接注册**（非 class id），
供引擎批次 2 实现分支级 resource_override（classes.py evolve_branches 攻线侧指定资源）。
resonance 消耗侧 res_cost 可显式 {resonance:-N} 走通；获取侧（res_gain 副 key）需引擎批次 2。
echo 建议落 mech_stacks 驻留叠层（战斗内不清零天然契合长周期驻留语义）；每层刻一始全队恢复
6 点体力 + 增益续时需引擎批次 2 新增 echo 结算挂点。
```python
"resonance": {"key": "resonance", "name": "共鸣", "max": 10, "regen": 0,
              # 歌类/咏叹技 +1(治疗赛诗 +2)，消耗放大增益/大招(启明圣咏 -3 / 终章·黎明颂歌 -5)，攒满约 4 刻
              "on_attack": 0, "on_hit": 0, "on_skill": 1}
"echo": {"key": "echo", "name": "回声", "max": 3, "regen": 0,
         # max=展示/注册用（叠层实际由 battle_config ECHO_CFG.max_layers / MECH_CFG['echo'] 管，
         # 引擎 _res_gain echo→mech_stacks 不经 core_resource_gain_key 上限注册）；
         # P2E-P1b 后回声无「歌类技」判定生产者（v153 后 = _res_gain echo 单通道按技能数据叠加）
         "on_attack": 0, "on_hit": 0, "on_skill": 1}
```

## 5. vow 圣律（守线神谕随附支援燃料条 0-3）

参考_云海猎团职业融合_v139_牧师.md §4.4：治疗命中 +1 / 受击 +1（每刻至多 1），消耗 1 点
施放圣辉支援（不占主行动）。注册：BRANCH_RESOURCE_OVERRIDE[("cls_mu_shi", 2)] = ("vow", "faith")
（引擎批次 2，同歌者 resonance 先例）。
```python
"vow": {"key": "vow", "name": "圣律", "max": 3, "regen": 0,
        "on_attack": 0, "on_hit": 1, "on_skill": 0, "on_heal": 1, "per_turn_cap": 1}
```
注：暗影神谕「亡灵祭仪保底律 idle_floor_turns」为独立配置常量（原放 battle_config.py，不占 CORE_RESOURCES 条目）。

## 6. 其余旧表条目（展示元数据，v130.2 name 值已对照迁移 EFFECT_RULES）

| class/key | name（旧表） | max（=EFFECT_RULES cap） | 备注 |
|---|---|---|---|
| cls_zhan_shi rage | 怒气 | 10 | R2b 已迁 |
| cls_fa_shi element | 元素亲和 | 5 | 基础纯蓝不经营，转职首获充能条 |
| cls_you_xia energy | 精力 | 100 | R2a 已迁（含 start_full/period） |
| cls_mu_shi faith | 信仰值 | 10 | 负载四档：0-3 清醒/4-7 专注(×1.25)/8-9 透支(×1.5)/10 过载(强制清零全队回复)，每刻 −0.7 |
| cls_ci_ke cp | 连击点 | 5 | 普攻/技能命中 +1 |
| cls_wu_seng chi | 气 | 10 | 3 气崩拳/10 气破岳拳双档 |
| vow | 圣律 | 3 | 见 §5 |
| resonance | 共鸣 | 10 | 见 §4 |
| echo | 回声 | 3 | 见 §4 |
| zhan_yi / lian_duan / arcane | 战意/连段/奥术 | 10 | v151+ battle2 叠层资源，name 对齐 RESOURCE_STACK_CN |

> 退役后仍存活读点（数据文件本体保留中，未 git rm）：job_guide 职业速查 desc 原文派生
> （data/job_guide.py + commands/job_guide.py EXTRA_RESOURCES 共鸣/回声展示）、
> commands/player.py `_RES_CN` 技能详情资源名、data/__init__.py re-export、tests 结构断言——归后续批次。

---

# M-R2d 渠道装配设计（v181.M-R2d · 2026-09-09）

> §6「渠道层（R2）技术方案」落地批。前置：R2a energy period dir=gain（dd94ddc）、
> R2b/R2c core_resources.py 退役删除（渠道字段 on_attack/on_hit/on_skill/on_heal 随文件消失，
> 资源 name/cap 单源 EFFECT_RULES）。本批 = **把「旧表职业主资源事件型攒取渠道」按现网技能
> 口径核实后，以 EFFECT_RULES 声明 + class_mech_proc 装配层事件钩子重建**。

## 1. 核实结论：现网职业资源口径矩阵（动手前逐项核实）

核实源（语义权威顺序）：skills.py 现网玩家技能（PLAYER 56 + BRANCH 238，v151+/v153 世代）
→ EFFECT_RULES → 退役测试断言 → 旧 battle.py 渠道实现（git 379a792^ 退役前世代，已 N10-C 删）。

| 职业 | EFFECT_RULES 资源 key | 现网技能攒端 | 现网技能消费端 | 判定 |
|---|---|---|---|---|
| 战士 | **zhan_yi 战意** cap10 | ✅ 技能 mech 命中攒层已通（挥砍/破甲斩/旋风斩/战吼+3/怒斩/怒涛/狂战怒吼 等 9 技能，desc「命中积攒 1 点战意」） | ✅ res_cost zhan_yi5（冷静 R1c）+ 血祭/坚韧 desc | v151 语义主资源；**攒层引擎已通（skill 内嵌 mech）→ 本批不重复装配** |
| 战士 | **rage 怒气** cap10 | ❌ 现网技能表 **零** mech/res_gain/res_cost rage | ❌ 零技能消费（v130「满 10 背水/狂暴」随 battle.py 形态机退役，battle2 无 dual_form 消费端） | **技能域死 key** → 渠道不接（§3）；affix 词条域（war_spirit/blood_bath/boiling_blood）仍由 R4 we_affix_res_gain 通道喂，不动 |
| 法师 | element 元素亲和 cap5 | ❌ 零技能使用（v151 印记体系 fire/ice/thunder_mark mech 取代；v139 注释亦明示基础不经营） | ❌ 零消费 | **死 key**（affix arcana_flux R4 域照旧）→ 不接 |
| 法师 | arcane 奥术 cap10 | ✅ BRANCH 奥术学者 mech 充能 +1/+2 已通（奥术弹幕/爆破等） | arcane_burst 兑现（MECH_CASH 未声明=R1 记缺口，cap 漂移 10 vs desc 5） | 攒层已通 → 不重复；兑现缺口归 R1 |
| 游侠 | energy cap100 | ✅ R2a period dir=gain 18/刻 + start_full 已通 | ✅ res_cost 全系 | ✅ 完成不回退 |
| 牧师 | **faith 信仰值** cap10 | ❌ **缺**：现网技能表零攒点字段（v153 重做丢了 per-skill res_gain；旧表 on_heal:2/on_hit:1 渠道随 core_resources 退役） | ✅ 真实消费端：卸负（mech=faith_unload 卸 3 点信念回血）；desc「圣光惩戒…不增信念」反证攻击系默认攒信念 | **活 key 且攒端断 → 本批接渠道**（圣光/死灵两线共用 cls_mu_shi） |
| 刺客 | **lian_duan 连段** cap10 | ✅ 技能 mech 命中攒段已通（刺击/影袭/影刃/双刃乱舞 mech lian_duan） | ✅ finisher 兑现（R1a 已装）+ poison_burst_finisher | v151 主资源；攒层已通 → 不重复 |
| 刺客 | cp 连击点 cap5 | ❌ 零技能使用（v151 lian_duan 取代 v130 cp） | ❌ 零消费 | **死 key**（affix crit_return R4 域照旧）→ 不接 |
| 武僧 | chi 气 cap10 | ❌ 零技能使用（v151 破绽条 shaken + 磐核体系取代 v130 气/崩拳） | ❌ 零消费（3 气崩拳/10 气破岳拳 v130 语义已随技能重做消失） | **死 key**（affix rock_rest/opening_stance R4 域照旧）→ 不接 |
| 诗人 | （无主资源） | melody 驻留体系 = 单独系统（蓝图 §7 R1d 记录） | — | 非本批 |
| 全职业 | 普攻攒点 | ❌ classes.py basic_skill 现网无 mech/无 dict res_gain（战士挥剑斩击带 `res_gain: 1` int 死字段——旧「普攻攒 1 主资源」泛语义，无 key 无消费端） | — | **普攻渠道无现网数据/desc 证据 → 不接**（§3 缺口） |

**渠道只接一条**：牧师 faith（治疗施放 +2 / 受击 +1——旧表 on_heal:2/on_hit:1 逐字值；
on_hit 终代语义 = 受击，JOB_GUIDE desc「治疗攒点(on_heal +2)/受击 +1」佐证一致）。

## 2. 数据形态与装配器（字段级）

### 2.1 渠道声明（EFFECT_RULES 资源条目扩展）

```python
"faith": {
    "name": "信仰值", "cap": 10,
    # v181.M-R2d 攒取渠道（源 core_resources.cls_mu_shi on_heal:2/on_hit:1，文件 R2c 退役）：
    #   heal_cast 治疗施放 +2 / taken 受击 +1——装配层按 start_classes 归属挂事件钩子。
    #   （攻击系攒信念 = v130 per-skill res_gain 数据语义，v153 skills 重做未回填 → §3 缺口）
    "start_classes": ["cls_mu_shi"],       # 渠道归属职业（复用 start_full 归属字段语义：防白拿）
    "channels": {"heal_cast": 2, "taken": 1},
}
```

- `channels`：dict {渠道时机名: 每事件加值}。时机名是装配层语义层（非 battle2 事件名直接裸露），
  由装配器映射展开——防止渠道语义与事件位细节耦合（事件位若日后调整只改映射表）。
- `start_classes`：归属职业（空 = 不装配，防白拿）。复用 start_full 同名字段（R2a 先例），
  语义泛化为「本条目的装配归属职业」（start_full 与 channels 各自按它过滤）。

### 2.2 时机名 → battle2 事件映射（class_mech_proc 私有表）

| 时机名 | battle2 事件 | 附加过滤 | 说明 |
|---|---|---|---|
| attack_hit | attack_hit | — | 普攻命中（basic 专属事件） |
| skill_hit | skill_hit | — | 技能命中 |
| heal_cast | act_cast | kind=治疗 | 治疗「施放」与「命中」同刻（R4 holy_echo 同款折中）；act_cast 每技能施放 1 次 → 无多目标重复 |
| taken | on_taken | — | 受击（真实承伤后 fire，subject=受击者） |
| cast | act_cast | not_basic | （预留：技能施放，未装配用） |

未映射时机名 → 装配器静默跳过（版本漂移保护，同 R4 affix 翻译器缺口词条行为）。

### 2.3 装配器落点：并入 class_mech_proc（不新建文件、不碰 battle_equip_proc）

- 装配函数：`class_mech_proc.apply_class_mech(actor)` 内新增「渠道段」（与既有 start_full 段并列；
  同一幂等装配入口）。**装配点零改动**——apply_class_mech 已由 _open_battle2 / PVP / tower 四处
  并列 `_EP_apply + _CM_apply` 调用（combat.py L622/L2804、tower.py L154；instance 控制器
  现状未接 class_mech，渠道随之不在副本生效——与 mech 兑现现状一致，不新增风险）。
- 渠道效果形态：`actor.triggers[事件]` 挂 `{"type": "class_res_channel_gain", "res", "gain",
  "kind"/"not_basic", "label", "icon"}`——与 affix R4 产出同构（battle2 事件总线统一分发），
  但 **type 用 class_mech_proc 自注册动作**（R1a mech_cash_* 先例），零跨文件私有耦合：
  - 不动 battle_we_procs.py（并行 agent 域 + R4 词条动作命名域）
  - 不 import battle_equip_proc 的 _AFFIX_RES_GAIN_ON（私有表，affix 域时机语义带 on_ 前缀）
- 动作 `class_res_channel_gain`（~20 行，参数化零资源硬编码）：
  kind/not_basic 过滤（读 battle._fire_ctx.info）→ owner=声明者（_owner 或 caster）存活检查 →
  effects[res].stacks += gain，cap clamp 查 state_def(res).cap → 日志「✦ {label} +{gain}（{n}/{cap}）」。
  （叠层写入与引擎 apply op=add 同口径；独立动作只因需事件过滤 + 统一日志。）

### 2.4 范围与防刷约束

- 只接核实过「现网有技能/机制在用的资源」渠道；energy period 不回退。
- 渠道值全来自 EFFECT_RULES 声明（零默认值铁律：无 channels 字段 = 无渠道）。
- clamp cap：动作侧 min(cap, cur+gain)（溢出不产生任何值——防刷资源）。
- 层数无 stat_scale 副作用（faith 纯 cap 容器）→ 攒满/溢出无属性影响；等卸负兑现（R1c
  heal_clear 族缺口）+ 负载档位装配后闭环（§3）。

## 3. 死 key 判定与处理（不接 + 标注）

| key | 判定依据 | 处理 |
|---|---|---|
| rage | skills.py 全表零 mech/res_gain/res_cost；battle2 无 dual_form 形态机消费（v139 留档）；EFFECT_RULES stat_scale dmg_mult 0.12/层为 v151 前残留——若渠道误喂，满层 +120% dmg 无人消费 = 数值崩坏 | EFFECT_RULES 注释标注「技能域渠道死 key」，渠道不接；affix 域由 R4 通道照旧 |
| cp / chi / element | v151+ 技能零使用（lian_duan / 破绽条·磐核 / 印记体系取代） | 同上标注（EFFECT_RULES 条目注释） |
| 普攻攒 zhan_yi/lian_duan | 现网 basic_skill 无 mech/无 dict res_gain；v151 desc 攒点语义全内嵌技能 mech（普攻用 lv1 无 cd 技能承担攒点职责，如挥砍/刺击/圣光弹） | 不接，注释缺口（若策划要普攻直接攒 → basic_skill 加 mech 或 channels 声明 attack_hit 一行，勿在装配层硬编码） |

## 4. 缺口注释（本批不做，留档）

- 牧师攻击系攒信念：v130 per-skill res_gain（圣光弹/圣光惩击 +1、圣光惩戒「不增信念」无字段）
  在 v153 skills 重做时未回填 → 需技能数据回填 res_gain（蓝图边界：不改 skills 数据，归数据批次）。
- faith_unload（卸负）兑现装配：mech 值在 MECH_CASH 无声明 → 信念攒出后暂无人消费（层 clamp cap
  无副作用）；兑现 + 负载四档（0-3/4-7 ×1.25/8-9 ×1.5/10 过载清零）+ 每刻 −0.7 衰减 = v130 负载制
  整体装配，记缺口（同 passive_procs tick_faith 族未挂接现状）。
- 战士普攻攒战意 / 刺客普攻攒连段：无现网证据，若策划确认需 basic_skill mech 或 channels 声明。
- overflow_shield 满溢转盾：v130.2.1 三资源（rage/chi 域）随死 key 不接；活 key 侧无声明需求，不引入。
- v153 被动族（passive_procs.py 52 proc：arcane_intuition 每刻充能 / undead_faith 亡灵在场回信念等）
  挂点未接 battle2——被动回复属 tick 族装配批次，非事件渠道。

## 5. 测试计划（tests/test_class_mech_r2d.py，仿 R2a 样板）

1. 装配：牧师 apply_class_mech → triggers.act_cast（kind=治疗 gain2）+ triggers.on_taken（gain1）；
   战士/游侠无 faith 渠道条目（start_classes 归属防白拿）
2. 治疗施放攒：A.do_skill kind=治疗 → effects.faith 0→2
3. 连续治疗 clamp cap：堆到 cap 10 不再涨（溢出安全）
4. 受击攒：敌方真实扣血（landing.deal_damage）→ faith +1
5. 负向：普攻（物理 act_cast）/攻击技能命中（skill_hit）不增 faith（kind 过滤，无双计数）
6. 负向：非牧师职业受击/治疗无 faith 条目（无渠道装配 + 无副作用）
7. 回归：energy start_full/period 不受影响（faith 无 start_full 无 period → 牧师开局无 faith 条目）
