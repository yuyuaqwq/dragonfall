# SA-1 任务卡：8 个新手特效 handler（novice_*）实现

## 目标
在 `C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/core/weapon_effects.py` **文件尾部**追加 8 个新手特效 handler，让 8 件新手紫装的特效真正生效。

## 背景
8 件新手紫装（Lv.10-15）的 `special` 字段是 dict 结构 `{"id": "novice_xxx", "trigger": "xxx", "value": X}`，但**没有任何消费端**（死特效）。主 agent 已把数据层改成 `"weapon_effect": "novice_xxx"` 字符串格式（同现有 70 件特效装备一致），由 weapon_effects.py 的 `has_effect`/`weapon_effect_ids` 读取。

## 8 个特效语义（从数据 desc 抄录）
| weapon_effect key | 触发事件 | 效果 |
|---|---|---|
| novice_lifesteal | stat（常驻面板） | 伤害的 5% 转化为生命回复 |
| novice_first_turn_guard | battle_start | 每场战斗首回合受击伤害 -10% |
| novice_spark_followup | skill_after | 释放技能后，下次普攻伤害 +10% |
| novice_hunt_combo | on_crit | 暴击后，本场战斗连击率 +8% |
| novice_regen_heal | stat（常驻面板） | 受到的治疗效果 +10% |
| novice_wind_spd | on_hit | 攻击命中后，自身速度 +5%（持续 2 回合） |
| novice_first_turn_dodge | battle_start | 每场战斗首回合闪避率 +5% |
| novice_dawn_mana | first_skill | 每场战斗首次释放技能时回复 10 点魔力 |

## 实现要求（照现有 handler 模式，先例见文件内）
- 每个 handler 用 `@register("事件名")` 装饰，函数名 `_we_novice_xxx(battle, player, ctx, logs)`
- **开头必须** `if not has_effect(battle, player, "novice_xxx"): return`（防串场）
- 参考先例（同文件已有）：
  - `_we_starlight_bulwark`（battle_start 护盾）
  - `_we_gale_step`（battle_start 挂 buff）
  - `_we_wind_mark`（hit 叠层）
  - `_we_smith_blaze_wound`（hit 概率特效）
  - `_we_arcane_firmament_p`（passive 增伤）
- 通用工具直接用：`_heal_player(battle, player, amount, logs, source)` / `_add_shield`（battle 方法）/ `_pstats(battle, player)` / `battle.mech_stacks`（叠层）/ `battle.p_buffs`（玩家 buff）/ `battle.p_eff`（特效状态）/ `random.random()`

## 各特效实现建议
1. **novice_lifesteal**：`@register("hit")` 挂命中——用 `_pstats(battle, player)` 拿 atk 算伤害的 5% 回血（简化为每次命中回 `atk*0.05`，因为吸血按伤害 5% 折算，用 atk 近似即可；或用 ctx 里的 dmg 字段：`ctx.get("dmg")` 存在就用 dmg*0.05，不存在用 atk*0.05）。**注意：这个不是 stat 面板特效，是 hit 触发回血**——desc 说"伤害的 5% 转化为生命回复（常驻）"意思是每击吸血，不是面板属性。
2. **novice_first_turn_guard**：`@register("battle_start")` 设 `battle.p_eff["novice_guard_active"] = True` + 记录回合数。真正的减伤要在 battle.py 的 `_damage_player` 里消费（主 agent 已接线：检查 `p_eff["novice_guard_active"]` 且首回合 → dmg * 0.9）。handler 只负责 battle_start 挂标记。
3. **novice_spark_followup**：`@register("skill_cast")` 或 `skill_after`——设 `battle.mech_stacks["novice_spark"] = True`，主 agent 在 `_player_attack` 消费（有标记则伤害 +10% 并清标记）。handler 只负责技能后挂标记。
4. **novice_hunt_combo**：`@register("hit")` 里判断 `ctx.get("is_crit")`，是暴击则 `battle.mech_stacks["novice_combo"] = min(5, +1)`，每层连击率 +8%——主 agent 在连击判定消费（st["combo"] 或类似字段）。
5. **novice_regen_heal**：主 agent 在 `_skill_heal` 消费（治疗时 +10%）。handler 可注册 `heal` 事件：`ctx["heal"] = int(ctx["heal"] * 1.10)`（参考 `_we_holy_radiance_mail` 先例）。
6. **novice_wind_spd**：`@register("hit")`——命中后 `battle.p_buffs["novice_wind_spd"] = 2`（2 回合），`battle.p_eff["novice_wind_pct"] = 0.05`，主 agent 在 `_player_stats` 消费速度加成。
7. **novice_first_turn_dodge**：`@register("battle_start")` 设 `battle.p_eff["novice_dodge_active"] = True`，主 agent 在闪避判定消费（首回合 dodge +5%）。
8. **novice_dawn_mana**：`@register("skill_cast")`——`if not battle.p_eff.get("novice_mana_used"): battle.p_eff["novice_mana_used"] = True; player["mp"] = min(player.get("max_mp", 999), player.get("mp", 0) + 10); logs.append(...)`。

## 铁律
- **只追加新函数到文件尾部，不修改现有任何 handler/函数**（避免并行冲突）
- 不改数据文件、不改 battle.py（主 agent 负责接线）
- 不 commit、不跑全量回归（主 agent 收尾）
- 写完 `python -c "import ast; ast.parse(open('game/core/weapon_effects.py', encoding='utf-8').read())"` 验证语法
- 完成后报告：每个特效的行号 + 语法验证结果

## 验证（可选，用独立私有库）
```python
import sys, os
sys.path.insert(0, r"C:/Users/yuyu/qqbot")
os.environ.setdefault("GWEN_GAME_DB", "tests/_tmp_sa1.db")
from game.core.weapon_effects import WEAPON_EFFECTS
# 确认 8 个 key 已注册
for k in ["novice_lifesteal", "novice_first_turn_guard", "novice_spark_followup",
          "novice_hunt_combo", "novice_regen_heal", "novice_wind_spd",
          "novice_first_turn_dodge", "novice_dawn_mana"]:
    assert k in WEAPON_EFFECTS, f"{k} 未注册"
print("8 个新手特效全部注册 OK")
```
