# N10-B：删旧前上层缺口补完（5c P5 盘点 + 鱼鱼 2026-09-09 拍板并入 N10）

> 状态：施工方案（2026-09-09 下午）
> 前置：5c P1-P5 + e2e 完成（109 断言绿）、N5B 怪 AI 完成、N10-P0 提交（e46a5a5）
> 铁律沿用：引擎零游戏知识；actors 只留数据+纯读；效果数值从效果数据/动作配置读；
> 缺口处置三原则 = 能表达走配置翻译 / 真缺原语列独立小批 / 文案虚标记清单不造系统。

## 0. 背景

5c P5 原语盘点（refs/v181-n5b5c-boss-script-director.md §P5）留下 5 项缺口，
鱼鱼拍板「缺口并入 N10 批内补完（副本 Boss 机制零丢失）」。逐项：旧引擎语义 →
battle2 现状 → 落点。

## 1. 缺口清单与处置

| # | 缺口 | 旧引擎语义（语义参考，N10 删） | battle2 现状 | 处置 | 规模 |
|---|---|---|---|---|---|
| G1 | element_immune/weak + 元素伤害 | battle.py:8422-8461 元素免疫（伤害归 0）/弱点（×倍率）；ELEMENT_MARKS fire/ice/thunder + last_element 连发记忆；_hostile_mitigate 元素抗 | landing/effects **无 elem 消费**；bridge 已透传 element_immune/element_weak 到 actor（无人读）；玩家技能 kind=魔法·火/冰/雷 5 个 + 圣/暗词缀 24/14 已存在数据 | 引擎补元素伤害上下文传递 + 免疫/弱点消费；装配/数据声明 | 🔴 大（需字段级设计） |
| G2 | **吸血系统主链**（含 mortal_wound 减半） | battle.py `_settle_lifesteal`:4958（面板吸血率统一结算：lifesteal/lifesteal_phys/lifesteal_magi 乘算合成、cap30%、真伤不吸、淬血每层+1.5%、药水 lifesteal_pot +15% 乘算、mortal_wound ×0.5）；技能级 `info.lifesteal`:6408（嗜血斩 0.25 经 skill_lifesteal_pct）；普攻=basic_skill 同管道（v174.1）→ 全部经 _skill_finalize_damage 结算；AOE **不吸血** | battle2 actions/landing **零 lifesteal 消费**（引擎+rules 全 0 命中）；装配层仅词条级 novice_lifesteal 翻译（hit 5%）；affix stat 型吸血词条折算面板但无消费端 → 玩家词条吸血整体失效；mortal_wound boss_script 已落玩家 effects（无人读） | actions 新增 `_settle_lifesteal`（对齐旧语义：面板率×实际伤害、phys/magi 分账、cap30%、mortal_wound effects ×0.5、真伤跳过、AOE 跳过）；技能级 info.lifesteal 同处消费 | 🟠 中（主链批） |
| G3 | reflect Boss 级（血<25% 反弹 15%） | battle_mech mech reflect token（×1 boss 配） | 装配层 we_reflect 已有（on_taken 声明批，武器/词条用）；boss mech token 门槛已收但导演未实现挂载 | 导演 _check_reflect：血<25% once → boss actor 挂 reflect 效果（复用 we_reflect 语义/或 effects 声明） | 🟡 中 |
| G4 | defend_reduce（方向性防御 v178 E6） | battle.py:3766-3776 敌方防御时技能配 defend_reduce 覆盖默认 0.5（云怒风眼 0.8）；DEFEND_REDUCE=0.5 | battle2 landing:58 defending 固定 ×0.5，**无按技能覆盖** | landing 减伤前查当前施法技能 defend_reduce（数据字段）→ 覆盖 0.5 | 🟡 中 |
| G5 | 形态轮换（烛影/蚀夜双态） | phases + element 组合（v178 E5） | phases 导演已可触发换阶段演出/换招；形态无伤害差异因 G1 未落 | 依赖 G1：phase 切换时更新 actor element_immune/weak（数据已配）→ G1 落地即闭环 | 🟢 随 G1 |

## 2. 落点分层（沿用北极星）

```
引擎 battle2：只加最小通用能力
  G1 → actions/landing 伤害上下文带 elem（从技能数据 kind/元素字段读，零名词）
        + 免疫/弱点乘区消费（查 actor.element_immune/element_weak，数据已透传）
  G4 → landing defending 减伤前查施法技能 defend_reduce 字段（数字覆盖 0.5）
导演 boss_script.py（命令层）：G3 血<25% reflect once 挂载
装配/数据：G2 吸血×0.5 消费点（读 effects mortal_wound）；G5 数据已齐零代码
```

## 3. 拆批

| 批 | 内容 | 引擎改动 | 验证 |
|---|---|---|---|
| N10-B1 | G2 mortal_wound 消费（最小，先立样板） | 0（装配层/导演） | 吸血装配测试 + boss_script opening 重创 e2e |
| N10-B2 | G4 defend_reduce 按技能覆盖 | landing 小改（查字段，缺省 0.5 零变化） | 方向性防御单测（云怒 0.8 / 缺省 0.5） |
| N10-B3 | G3 reflect Boss 级 | 0（导演帧） | 血<25% once 反弹测试 |
| N10-B4 | G1 element 元素伤害 + 免疫/弱点（最大，需字段级设计先行） | actions/landing 小扩展 | 元素技能×免疫/弱点矩阵 + 蚀夜/冰霜领主 e2e |
| N10-B5 | G5 形态轮换闭环（随 G1 验收） | 0 | 烛影/蚀夜 phase 切换 element 变更 |

顺序：B1（样板）→ B2/B3（小）→ B4（主工程，先出字段级设计）→ B5（验收）。
每批独立 commit + 测试 + 全套 battle2 回归对照基线零新增。
