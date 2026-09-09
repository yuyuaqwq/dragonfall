# N10-B1：battle2 吸血系统主链补完（G2，含 mortal_wound 减半）——设计文档

> 状态：待鱼鱼审查（2026-09-09）
> 依据：docs/REFACTOR_v181P4_N10B_gap_fill.md §1 G2 行（侦察结论：battle2 吸血主链整体缺失）
> 铁律：行为对齐旧引擎 _settle_lifesteal 语义；引擎零游戏知识（吸血率=面板数据，引擎不认名词）；
> AOE 不吸血（旧语义）；真伤不吸血（v107 鱼鱼拍板）；不造"死后复活"式半套系统。

---

## 1. 问题：battle2 吸血主链缺失（比 5c P5 盘点更严重）

侦察证据：
- battle2 引擎 + data/battle2_rules.py **零 lifesteal 命中**（grep 全 0）
- 装配层只有词条级 `novice_lifesteal`（we_extra_dmg hit 事件 heal_pct 回血）——这是"装备词条自带吸血"
  的翻译，**不是**玩家面板吸血率体系
- affix stat 型吸血词条（`lifesteal/lifesteal_phys/lifesteal_magi`，trigger=stat，如吸血+8%）在生成时折算进
  item.stats → E.player_final_stats 面板 st["lifesteal"]=0.08 ✓（probe 实测），但 **battle2 伤害管线无人消费该面板值**
  → 玩家带吸血词条装备在 battle2 下攻击**不回血**（与旧引擎行为断裂）
- 技能级 `info.lifesteal`（嗜血斩 0.25）battle2 do_skill 未消费 → 嗜血斩吸血失效
- 淬血（zhan_yi 每层+1.5% 吸血）→ battle2_rules 只声明了 zhan_yi atk 叠层，吸血消费缺（旧引擎在
  _settle_lifesteal 里 run_proc_family 消费）
- 药水 lifesteal_pot（嗜血药剂 +15%）→ battle2 无声明/无消费

## 2. 旧引擎语义（语义参考，N10 删 battle.py）

### 2.1 _settle_lifesteal（battle.py:4958）——面板吸血率统一结算

```
触发点：_skill_finalize_damage 尾部（玩家普攻/技能命中后，battle.py:6734-6740）
  - 普攻 = basic_skill 走 _actor_skill 同管道（v174.1 鱼鱼拍板）
  - 混合段分账：魔能斩类 _magi_part>0 时，物段走 phys 吸血、魔段走 magi 吸血
  - AOE 不吸血（_aoe_damage 独立路径无 _settle_lifesteal 调用）
口径：
  1. dmg<=0 或 dmg_type=="true" → return（真伤不吸血）
  2. rate = st["lifesteal"]（通用吸血率，词条/种族/被动/药水汇聚）
  3. magic 时合成 lifesteal_magi，非 magic 合成 lifesteal_phys：rate = 1-(1-rate)(1-sub)
  4. 药水 buff lifesteal_pot：rate = 1-(1-rate)(1-0.15)
  5. 淬血 zhan_yi_lifesteal：每层战意额外 +1.5%（proc 消费，读 _ps per_layer）
  6. cap 30%：rate = min(rate, 0.30)
  7. mortal_wound（玩家被 Boss『重创』施加）：rate *= 0.5
  8. heal = dmg × rate → _heal_actor 落地
```

### 2.2 技能自带吸血（battle.py:6408-6413）

```
if info.get("lifesteal"):            # 技能数据 lifesteal 字段（嗜血斩 0.25）
    heal = int(total × skill_lifesteal_pct(info, lv))   # 随等级成长
    if mortal_wound: heal *= 0.5
    _heal_actor(player, heal)
```

### 2.3 玩家被重创标记（mortal_wound）

- 施加方：Boss opening effect=mortal_wound（battle_mech.py:825-827），3 个 Boss（b_om_shadow/b_cardinal/b_aolan）
- 落点：旧引擎写玩家 buffs["mortal_wound"]；battle2 5c 导演 boss_script.py:310-320 **已落玩家
  effects["mortal_wound"] = {stacks:1, expire: now+power}**（✅ 无需改，只差消费端）

## 3. battle2 落点设计

### 3.1 新增函数：actions.py `_settle_lifesteal`

```python
def _settle_lifesteal(battle, actor, dmg_total, kind, logs, magi_part=0,
                      skill_info=None, skill_lv=0):
    """玩家攻击吸血统一结算（对齐旧 _settle_lifesteal + info.lifesteal 技能级）。

    - 引擎零游戏知识：吸血率 = actor 面板数据（S.actor_stats），引擎不认"吸血"名词，
      只做通用"攻击者按面板吸血率回血"——纯怪无 lifesteal 面板 → 零行为（天然安全）
    - 真伤不吸（kind==K_TRUE → return）
    - AOE 不吸（调用方 _deal_aoe 不传，见 3.3）
    - mortal_wound：actor.effects["mortal_wound"] 存活（expire 未到）→ ×0.5
    """
```

内部口径（对齐 §2.1/2.2）：
1. 通用段：`st = S.actor_stats(battle, actor)`，rate = st.get("lifesteal",0)
   - 物/魔细分：kind 判断（K_PHYS→lifesteal_phys，K_MAGI→lifesteal_magi 合成；混合段由调用方
     拆传 dmg 比例——先做简化版：混合段按 magi_part 拆两次调用，与旧 6734-6740 一致）
2. 技能级：`skill_info.get("lifesteal")` → 额外算 `E.skill_lifesteal_pct(skill_info, skill_lv)`，
   同 ×(0.5 if mortal_wound)
3. cap 30%、mortal_wound ×0.5、heal_actor 落地、日志 `🩸 吸血：回复 N 点生命！`

### 3.2 挂点：_single_target_pipeline 主伤害落地后

```
_single_target_pipeline（battle2/actions.py:197）
  …total 汇总完成、_deal_hit 落地、附伤/命中效果完成后 →
  if not is_aoe_call:  # AOE 逐目标也走本函数 → 需区分
      _settle_lifesteal(battle, actor, total, kind, logs,
                        magi_part=magi_part, skill_info=info, skill_lv=lv)
```

- 普攻也走这里（do_attack → resolve_basic_skill → 同 pipeline）→ 天然覆盖普攻 ✓
- 混合段（魔能斩）：magi_part>0 时拆 phys/magi 两段调（对齐旧 6734-6740）

### 3.3 AOE 区分

battle2 `_deal_aoe` 逐目标循环调 `_single_target_pipeline`（每目标独立结算），旧引擎 AOE 不吸血。
→ 加参数 `_no_lifesteal: bool = False`，_deal_aoe 内调用传 True；普通单目标路径默认 False。

### 3.4 mortal_wound 消费（到期判定）

- 读取：`ef = actor.get("effects") or {}; mw = ef.get("mortal_wound")`
- 判定存活：`isinstance(mw, dict) and (mw.get("expire") is None or now < float(mw.get("expire")))`
  —— 过期条目由 schedule._settle_time_effects 自动清（已有兜底），此处仅防御性判断
- 位置：_settle_lifesteal 内（通用段 + 技能级共用）

### 3.5 淬血 zhan_yi / 药水 lifesteal_pot（分期）

| 项 | 旧引擎 | battle2 现状 | B1 是否做 |
|---|---|---|---|
| 淬血每层+1.5% 吸血 | _settle_lifesteal 内 proc | battle2_rules 只声明 zhan_yi atk 叠层 | ⏳ 随被动装配批（zhan_yi proc 族迁 battle2 后接）；B1 先留 TODO 注释 |
| 嗜血药剂 lifesteal_pot +15% | buff 乘算 | battle2 无声明 | ⏳ 随药水效果批（POTION_EFFECTS 迁移时声明 lifesteal_pot effects 条目） |
| 词条 stat 型吸血 | 面板 st["lifesteal"] | 面板已有 ✓ | ✅ B1 主链消费它 |
| 技能自带 lifesteal | info.lifesteal | 无消费 | ✅ B1 做 |
| mortal_wound ×0.5 | buffs 消费 | effects 已落无消费 | ✅ B1 做 |

### 3.6 引擎改动清单（本次全部落 actions.py，landing/stats/schedule 零改动）

| 文件 | 改动 | 行量 |
|---|---|---|
| game/battle2/actions.py | +_settle_lifesteal 函数 + _single_target_pipeline 挂点 + _deal_aoe 传 _no_lifesteal | ~50 行 |
| game/battle2/actions.py | _single_target_pipeline/_deal_aoe 签名加 _no_lifesteal 参数 | ~4 处 |

## 4. 测试计划（tests/test_battle2_n10_b1_lifesteal.py 新建）

| # | 场景 | 断言 |
|---|---|---|
| 1 | 玩家面板 lifesteal=0.10（actor 直接塞 st 字段）普攻打怪 100 → 回 10 | hp = 战前 + 10 |
| 2 | 同上 + mortal_wound effects（未过期）→ 回 5 | hp = 战前 + 5 |
| 3 | mortal_wound 已过期 → 回 10（不误判） | hp = 战前 + 10 |
| 4 | 真伤段 → 不回血 | hp 不变 |
| 5 | AOE 打 2 怪 → 不回血（_no_lifesteal） | hp 不变 |
| 6 | 技能级 info.lifesteal=0.25（嗜血斩）→ 回 dmg×25%（skill_lifesteal_pct） | hp = 战前 + heal |
| 7 | 混合段：物段+魔段按各自吸血率 | 对齐旧分账 |
| 8 | 纯怪（无 class_name、无 lifesteal 字段）攻击 → 零行为不崩 | 无异常 |
| 9 | boss_script opening mortal_wound e2e：玩家吸血被减半（可复用 test_boss_script_p2 场景） | 减半生效 |
| 10 | battle2 全套回归基线对照零新增（沙盒跑） | 与基线同名单 |

## 5. 验证顺序

1. 本文件 → git status 干净确认 → 改 actions.py → py_compile
2. 新测试 test_battle2_n10_b1_lifesteal.py 全绿
3. 全套 battle2 测试（沙盒）对照基线零新增
4. 汇报鱼鱼 → commit（v181.N10-B1 格式）

## 6. 不做的（边界）

- 不建"面板吸血率 ≠ 通用回血"之外的任何名词判断（引擎零知识）
- 不做淬血/药水（记 ⏳ 上层批，见 §3.5）
- 不改 landing.heal_actor（已有 heal_down/_anti_heal_pct 禁疗修正，mortal_wound 是吸血侧乘区，不混）
- 不碰 boss_script 已落的 mortal_wound 条目形态（stacks/expire 已在）
