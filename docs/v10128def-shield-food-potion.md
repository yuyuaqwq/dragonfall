# v101.28d/e/f 战斗消耗品三连改（2026-08-12 鱼鱼睡前拍板，醒来全做）

鱼鱼睡前问三连：①盾能不能 buff 化（叠加+不同消失回合）②装备词条怎么实现的 ③食物别复用词条 ④药水有什么特殊效果。
醒来一句"全做" → 三个 commit：

## v101.28d 盾 buff 化（commit 35d1d7b）

**旧**：`self.shield: int = 0` 单数值池，无回合概念，词条盾取高（`max`）符文/技能盾加法——来源规则分裂。
**新**：`self.p_shields: dict = {来源: {"value": N, "turns": T}}`
- `_add_shield(key, value, turns)`：同源 value **叠加** + turns 取 max；异源并存各计各的回合
- `_end_round` 各来源 turns -1，到 0 消失（与 p_buffs 递减并排）
- `_damage_player` 按 dict 插入序逐个扣盾，汇总播报 `✨ 护盾吸收 X 点伤害(剩余 Y)`
- 来源表：affix_shield(开战10%×3) / food_shield(圣餐面包10%×3) / rune_barrier(符文壁垒×2) / overflow(庇护之光×2) / bless(神恩×2) / team_bless(副本团队技能×3) / potion(药水盾×3) / legacy(旧格式迁移999回合)
- **兼容**：battle_state 旧 `shield` 字段 → `{"legacy": {value, 999}}`（from_state + instance.py 快照双处）
- 状态行显示各来源：`✨护盾50(3回合)`（legacy 不显示回合）

**坑**：旧 `self.shield` 声明残留（__init__ 里 89 行）要一起删，grep `self\.shield` 全清；instance.py 三处（from_state 传参/写回 snap/team shield_all）都要改，team_bless 手动实现叠加逻辑（无 Battle 实例）。

## v101.28e 食物效果独立化（commit 14766ae）

鱼鱼"食物料理别复用词条，自己搞点特殊效果就行"——因为玩家认知里"词条"是装备上的东西，食物获得词条很怪。

**新**：`game/core/food_effects.py` 独立注册表（HIT/TAKEN/TURN_START 三表 + FOOD_EFFECT_NAMES 显示名）
- 数据字段 `affix` → `food_effect`；payload `affix:` → `foodfx:`
- `_equip_affix_ids` **不再合并食物**（词条系统彻底解耦）
- battle 新挂点 `_food_on_hit/_food_on_taken/_food_turn_start`（普攻 741/技能 1291/回合开始 1693/受击 1764 四处调用）
- 17 个效果独立实现，行为与 28c 对齐（吸血8%/流血20%×5%×3/破甲25%×15%×2/连击15%×50%/龙语印记×2%上限5/元素5%/贯穿20%/蓄力10%×150%/反击20%×60%/反伤10%×30%/回春1%/冥想1%/晨曦2%）
- **伤害倍率类**（处决/精准）走 `_affix_dmg_mult` → 抽 `_extra_dmg_mult`（见 28f 坑）
- 兼容：battle_state/副本状态旧 `p_food_affixes` 读时兜底
- 17 件料理 desc 补全数值（"获得【吸血】：攻击回复 8% 伤害为生命" 风格）

**坑**：test_v101_28_food_hot.py 断言大改（infer/payload/p_food_effects/独立触发验证）。

## v101.28f 药水特殊效果 + desc 造假全修（commit ae19f09）

**旧**：28 种药水（商店8+炼金20）全部挂 5 个 buff key，desc 写"本回合+30%/下一次+50%/本回合+40%"全假（实际都是 atk_up 1.30×3回合）。名字（荆棘/影步/死神/破甲）和效果（全是属性buff）完全脱节。

**新**：
- BUFF_MULT 强度分档：atk_up_big(+40%)/atk_up_small(+20%)/spd_up_small(+20%)/crit_up_small(+15%)/crit_up_big(+30%)
- `special:` payload 新分支 → `_apply_potion_special` 10 种：
  next_atk_up(狂怒=下次攻击+50%一次性) / heal_up(圣光=治疗+20%×3) / magic_resist(龙鳞=魔伤-15%×3) /
  thorns_pot(荆棘=受击反弹30%×3) / dodge_pot(影步=15%闪避×3) / cc_immune(不动=免疫眩晕冻结减速×3) /
  execute_pot(死神=<30%+30%×3) / def_down(破甲=敌防-15%×2) / shield_small(岩盾=10%盾×3) / shield_big(圣盾=15%盾×3)
- 消费点：_affix_dmg_mult(狂怒/死神) / _skill_heal(圣光) / _enemy_turn魔法段(龙鳞) / _damage_player(影步闪避+荆棘反弹) / battle_mech MON_CTRL_EFFECTS(不动免疫三处)
- item_templates `_BUFF_KEYS` 映射扩展（含特殊→"special:xxx"），`_make_buff_tpl` 支持 special 前缀
- combat.py `_P_BUFF_NAMES` 加全部新 key 显示
- 28 种药水 effect + desc 全部修正（脚本逐行定位，**desc 在下一行的多行条目坑**）

**坑（重要）**：
1. **`_affix_dmg_mult` 的 `if not ids: return` 提前返回 bug**——无词条装备时食物/药水倍率被跳过（狂怒/死神/食物处决全失效）！修法：hp_ratio 提前定义 + 抽 `_extra_dmg_mult(hp_ratio, mult, tags)` 方法，无词条和词条路径都统一调它
2. **批量改 items.py 多行条目**：条目 `{...effect...,\n "desc": ...}` 跨行——正则 `[^\n]*` 只匹配第一行，desc 换不掉；用**按行定位**（key 行号 + 后 2 行内找 effect/desc 行）最稳。正则替换还出过"effect 拼坏"（`"buff_atk""effect": "buff_atk"`），git checkout 恢复重来
3. 玩家闪避机制原本**根本没实现**（battle.py dodge 消费=0）——影步药水"15% 闪避"是新增机制（_damage_player 开头拦截）
4. 药水 desc"本回合"是系统性造假（实际都 3 回合），改 desc 时全部改成"3 回合"真实值；强度分档后 desc 数值=BUFF_MULT 真实值（战吼 40%≠力量 30%）

## 测试
- test_v101_28_food_hot.py 44 断言（28e 更新）
- test_v101_28f_potion_special.py 19 断言（数据一致性+payload+战斗内生效）
- 回归：battle 27 / v98 42 / v59 11 / instance 75 / item_use 8 全绿

## 遗留
- 药水战斗外使用提示"战斗药水只能在战斗中使用"保留
- 副本玩家用战斗药水：battle_state 持久化 p_buffs 自动带特殊效果（无需额外处理）
