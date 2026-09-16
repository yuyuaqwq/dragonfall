# v180-B actor 通用化实施计划（第一步：actor 身份/面板/数据入口统一）

## 目标（鱼鱼 2026-09-06）
扩展性：加新 actor（宠物上场/怪扮职业/召唤物独立）**不写新引擎代码**——
新 actor = "配数据的 actor 实例"（class_name+equipment+learned_skills+skills+buffs+...）。

## 根因
引擎 ~60 处身份 if 用 `actor.get("class_name")` 有无判玩家/怪——class_name 是玩家 DB 字段，
怪天然没有 → 怪不能配职业/装备/被动；玩家侧战斗状态（resources/mech_stacks/...）在 Battle
焦点字段不在 actor dict → 新 actor 无状态容器只能开小灶（宠物 pet_act 专用代码）。

## 第一步范围（本计划）：身份判定 side 化 + 面板路由统一 + 数据入口
不迁状态容器（第二步/存档兼容大工程另做）——但必须让"配了 class_name 的怪/新 actor"
不被误判成玩家（side 判定），且面板走玩家全公式。

### 阶段 1：side 阵营字段引入（身份判定地基）
- actor 加 `side` 字段：玩家="player"、怪="enemy"（build_monster 默认设）、PVP 敌方快照="enemy"
- `_tgt_is_player()`/`_cast_is_player()`/`_damage_actor._is_player` 从 class_name 判定 →
  side 判定（兼容兜底：无 side 时有 class_name=player 无=怪，保持存量行为）
- 收益：怪配 class_name 后身份仍是 enemy——治疗落自己、被玩家当敌打、不吃玩家专属

### 阶段 2：中央面板路由 `_actor_stats_of` 收敛
- actor 带 class_name → player_final_stats 全公式（含 equipment/learned_skills/race）
- 无 class_name → _enemy_stats 原语聚合（存量怪不变）
- 面板调用点收敛到 _actor_stats_of（_player_skill 内 est 已 actor 化 P1 完成）

### 阶段 3：build_monster/新 actor 数据入口
- build_monster 支持 actor_cfg/MONSTER_MODS 透传 class_name/equipment/learned_skills/
  skill_levels/title_bonus/race
- 面板：class_name 存在且 mode="class" → 走 _actor_stats_of 玩家公式

### 验证场景
1. 存量怪无 class_name → 行为零变化（全量回归）
2. 新 actor：怪 dict 塞 class_name=cls_zhan_shi + equipment + learned_skills → _actor_stats_of
   出玩家同构面板；side=enemy 身份正确（被玩家打、技能打玩家）
3. 宠物先例：pet 实体若带 class_name → 引擎像玩家一样处理（下一步做真正宠物上场的 tick 收编）

## 不做（第二步）
玩家焦点字段（resources/mech_stacks/p_shields/charging/cooldown）迁 actor dict +
to_state/from_state/副本 _load_player_state 序列化兼容。

## 门禁
- run_numeric_tests.py 43 文件全绿（不能比现状少）
- 全量 run_all_tests.py --jobs=16：257 过/17 存量红（零新增）
- 新测试 test_numeric_actor_class.py：怪配 class_name 面板/身份/被动验证
