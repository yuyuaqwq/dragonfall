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

---

# v139 形态层设计留档（源 core_resources.py 退役迁移 · v181.M-R2b）

> 2026-09-09 v181.M-R2b：`game/data/core_resources.py`（v130.2 资源表）退役——战斗资源
> 名/cap 单源化到 EFFECT_RULES（battle2_rules.py），engine.core_resource_def/def_by_key 删除，
> 4 处调用点（combat 脱战校验/技能表、potion_effects、battle2_bridge v139 注入）改读新源。
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
