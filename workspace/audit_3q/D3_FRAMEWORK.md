# D3 独特装备加量版 - 公共框架（FRAMEWORK）

## 背景
鱼鱼要求装备"有一部分独特的"，D2 设计了 44 件（占 631 件名册仅 7%，塔尖太小），鱼鱼问"够多吗"→ 要加量。目标：
- 独特装备 **80-100 件**（占 631 件 13-16%）
- 新独特效果库 **40-50 个**（D2 已设计 24 个，需再补 20-30 个）
- 结构健康：白/绿 0 独特（新手阶梯不破）、蓝少量轻量、紫 20-25%、橙 100%

## 拆批（按等级阶段，5 个 agent 并行，每 agent 只做自己的阶段）
| agent | 阶段 | 等级 | 独特装备目标 | 说明 |
|---|---|---|---|---|
| A | 前期 | 0-29 | 4-6 件 | 蓝装轻量 2-3 件 + 橙装全挂（4 件橙已有） |
| B | 中期 | 30-49 | 12-15 件 | 紫装主力挂载（51 件紫装选 8-10 件）+ 橙装全挂 |
| C | 后期 | 50-69 | 25-30 件 | 紫装主力（106 件紫装选 18-22 件）+ 橙装全挂（11 件） |
| D | 末期 | 70-89 | 25-30 件 | 紫装（52 件选 15-18 件）+ 橙装全挂（33 件） |
| E | 终局 | 90+ | 15-20 件 | 紫装（11 件选 5-6 件）+ 橙装全挂（23 件） |

## 效果库扩容（所有 agent 共享）
- D2 已有 24 个效果（龙鳞庇护/黑曜壁垒/铁壁意志/磐石之心/生命泉涌/奥术屏障/亡者守护/风暴使者/霜结之纱/猩红獠牙/噬魂者/处刑者/烈日迸发/连锁过载/猎杀印记/巨兽屠戮/记忆撕裂/战吼/顶尖猎手/致伤重击/秘法回响/汲力/召唤契约/最后一息）
- 每个 agent **设计 4-6 个新效果**（格式与 LEGENDARY_EFFECTS 完全兼容），要求与已有效果不同、贴合自己阶段的主题
- 汇总后主 agent 去重、合并，目标 40-50 个
- **新效果设计铁律**：
  - trigger 只用六种：stat / on_hit / on_taken / turn_start / battle_start / passive
  - effect 键复用既有语义（dmg_mult/pct/burn_pct/turns/execute_threshold/mark_pct/max_mark/elem_res/abyss_res/hp_pct/lifesteal/crit/crit_dmg/dodge 等）
  - 强效果必须有代价/条件（数值代价/条件生效/次数限制）
  - 总强度 ≤ 同品质同级基准等效 ±15%
  - 禁止设计引擎不支持的 trigger（先 grep battle.py 确认 _affix_on_hit/_affix_on_taken/_affix_turn_start/_affix_dmg_mult 的消费集合）

## 挂载表设计铁律（每 agent 遵守）
1. **橙装全部挂**：该阶段所有橙装（EQUIP_ROSTER quality==orange）必须挂独特效果（用已有 LEGENDARY_EFFECTS key 或新效果 key）
2. **紫装选挂 20-25%**：从该阶段紫装里挑选，优先挑：Boss 掉落、图纸、支线奖励、有主题名（如"龙鳞""烈焰""霜"）的
3. **蓝装轻量**：每阶段 2-3 件蓝装挂轻量效果（小数值，如 5% 概率回 3 魔力、受击 5% 回 1% 生命）
4. **效果主题贴合装备名**：龙系装挂龙系效果、冰系装挂冰系、Boss 掉落挂对应 Boss 主题
5. **不许重复挂同一效果到同阶段多件装备**（效果要有唯一感；不同阶段可复用但标注）
6. 每件挂载给：装备名 + rid（EQUIP_ROSTER 里的 key，先去代码查准）+ 品质 + 等级 + 效果 key + 效果说明 + 获得方式（source 字段）

## 输出格式
每 agent 输出两份：
1. **新效果清单**（4-6 个）：key/name/kind/trigger/chance?/effect/desc/数值健康说明
2. **挂载表**（该阶段全部独特装备）：表格（装备名/rid/品质/等级/效果key/效果说明/获得方式）

报告写 `workspace/audit_3q/D3_<阶段>.md` + summary 返回全文（中文）

## 必读
- D2 设计稿：`workspace/audit_3q/D2_design.md`（已有 24 效果 + 44 件挂载，可复用/避免重复）
- 名册数据：`game/data/equip_roster.py`（grep 自己阶段范围的装备）
- 效果库：`game/data/affixes.py:518-665`（LEGENDARY_EFFECTS 既有 58 效果）
- 消费链：`game/battle.py` `_affix_on_hit`(L3139)/`_affix_on_taken`(L3158)/`_affix_turn_start`(L3170)/`_affix_dmg_mult`(L2997)
