# v151 技能字段映射表（子 agent 落地参考）

> 主 agent 从现有 skills.py 实际字段 + v151 §10 引擎字段映射整理。
> 落地时把 v151 技能表翻译成这个格式，写进 PLAYER_SKILLS/BRANCH_SKILLS。

## v151 设计字段 → skills.py 引擎字段

| v151 设计字段 | skills.py 字段 | 说明 |
| --- | --- | --- |
| base（Lv.1 裸倍率） | `power` | 1.0 = 100% atk/matk |
| lv | `lv` | 学习等级 |
| mp | `mp` | 魔力消耗 |
| kind（物理/魔法/治疗/增益/真伤/被动/嘲讽） | `kind` | 中文串：物理/魔法/治疗/增益/被动/真伤/嘲讽 |
| cd | `cd` | 冷却（CTB 下=自己出手次数） |
| 命中+1战意 / +1段 / 推条+N | `mech_gain` / `mech`+`mech_val` | 自身叠层（mech_stacks）增减 |
| 战意≥N 条件 | `cond` `{"type": "player_mech_stacks", "key": "zhan_yi", "min": N, "mult": X}` | 需要引擎支持（侦察确认） |
| 敌身印记/破绽/标记 | `enemy_bar` / `mark` effect | enemy_bar 已有（battle_bars.py） |
| 反应表（蒸发/超载/冻结/感电） | `REACTION_TABLE` 已有（battle_config.py:128） | 元素印记系统已存在 |
| 破防 | `pierce: True` | 已有 |
| AOE | `aoe: "front"` / `"all"` | 已有 |
| 点名/后排 | `reach: 3` | 已有 |
| 吸血 | `lifesteal: 0.25` | 已有 |
| 眩晕 | `cc` / mech `stun` | 已有 |
| 减速 | mech `spd_down` | 已有 |
| 灼烧 | mech `burn` | 已有 |
| 流血 | mech `bleed` | 已有 |
| 毒 | mech `poison` | 已有 |
| 护盾 | `shield` effect / p_shields | 已有 |
| 被动（stat 加成） | `passive: {"stat": "atk", "mult": X}` | 已有 |
| 全队增益 | `team: True` / `team_buff` | 已有 |
| 治疗 | `kind: "治疗"` + `heal` | 已有 |

## 现有技能字段完整样例（抄这个格式）

### PLAYER_SKILLS 战士基础
```python
"cls_zhan_shi": {
    "name": "战士",
    "skills": {
        "sk_hui_kan": {
            "lv": 1, "mp": 3, "power": 1.0, "kind": "物理",
            "res_gain": 1,   # ← 旧资源条字段，v151 换 mech_gain
            "cond": {"type": "player_first", "mult": 1.15, "label": "先手压制"},
            "desc": "长剑划出利落的弧光——造成 100% 物理伤害；若你的速度高于目标，先发剑势更盛(伤害＋15%)",
            "name": "挥砍",
        },
        ...
```

### BRANCH_SKILLS 战士分支
```python
"cls_zhan_shi": {
    "name": "战士",
    "branches": {
        1: {  # A线
            "血怒": {
                "怒斩": {
                    "lv": 32, "power": 1.166, "kind": "物理",
                    "res_gain": 2,
                    "cond": {"type": "player_hp_low", "hp_pct": 0.5, "mult": 1.25, "label": "狂战血统"},
                    "mp": 5,
                    "desc": "...",
                    "name": "怒斩",
                },
                ...
            },
        },
        2: {  # B线
            ...
        },
    },
},
```

## 关键差异（v151 落地必须改的点）
1. **`res_gain`/`res_cost` 是旧资源条字段**（rage/element/energy/cp/chi 等 12 资源）。v151 废弃资源条，换成：
   - 自身叠层 → `mech_gain: {"zhan_yi": 1}` / `mech_stacks` 读写
   - 敌身挂账 → enemy_bar / mark / debuffs
2. **隐藏职业（cls_dragon_oath/chronomancer/wild_hunter/hymn/shadow_blade/wu_sheng）技能拆解并入对应线**
   - 龙裔→战士血怒（真伤/灼烧轴）
   - 时咒→法师时律（控制链）
   - 星语→游侠疾风（点名权）
   - 暗影神谕→牧师幽祷（骷髅/诅咒）
   - 暮影→刺客影舞（影舞态）
   - 淬势→拳师破绽（撼岳）
3. **分支 key 一律不改**（evolve_branches 强耦合），只改展示名 + aliases

## 落地铁律
- 只改 game/data/skills.py 的对应职业段，禁改其他职业
- 新技能 key 用 `sk_<职业>_<拼音>` 命名，禁撞已有 key
- desc 文案手写，但数值要与 power 一致（满级eq = base×1.40，参考值）
- 完成后 `python -c "from game.data import skills; print('ok')"` 验证 import 不崩
- 禁 commit，禁跑全量回归，只许 py_compile + import 验证
- 不读全项目！字段格式以上表为准，翻译 v151 技能表即可
