# v151 职业技能落地任务卡（模板）

> 每职业一张卡，子 agent 只改自己负责的职业段。
> 完整字段映射见 workspace/v151_field_mapping.md（先读）
> 本职业技能表原文见 workspace/v151_skill_tables/quan_shi.md（先读）
> 注意：sk_ 开头的字符串在 Hermes 显示层会被脱敏成 ***，子 agent 用 Python 原生读文件核实，不要因此误报数据污染。

## 你的任务
把 v151 设计文档中 拳师 的技能表，翻译成 `game/data/skills.py` 的引擎字段格式，落地到：
1. **PLAYER_SKILLS** 里 拳师 的基础技能（Lv.1-26 两线共用）
2. **BRANCH_SKILLS** 里 拳师 的两条线（A线/B线，分支 key 用数字 1/2 或既有 key）

## 翻译规则（照抄，不要自己发明）
- v151 的 `base`（Lv.1 裸倍率）→ `power`
- `lv` → `lv`，`mp` → `mp`，`cd` → `cd`
- `kind`（物理/魔法/治疗/增益/被动/真伤/嘲讽）→ `kind`
- 命中+1战意/+1段/推条 → `mech: "zhan_yi"/"lian_duan"/"qi", mech_val: N`（若引擎支持）或 `mech_gain: {"key": N}`
- 战意≥N 条件 → `cond: {"type": "player_mech_stacks", "key": "zhan_yi", "min": N, "mult": X}`（若引擎支持）
- 破防 → `pierce: True`，AOE → `aoe: "front"/"all"`，点名 → `reach: 3`
- 吸血 → `lifesteal: 0.25`，眩晕 → `cc` 或 mech stun，减速 → mech spd_down
- 灼烧/毒/流血 → mech burn/poison/bleed
- 护盾 → shield effect，全队增益 → team: True，治疗 → kind 治疗 + heal
- 被动 → `passive: {"stat": "atk", "mult": X}`

## 落地铁律
- **只改 game/data/skills.py 里 拳师 的段**（PLAYER_SKILLS 对应技能 + BRANCH_SKILLS 对应职业），禁改其他职业/其他文件
- 新技能 key 用 `sk_<拼音>`，禁撞已有 key（先 grep 确认）
- desc 文案手写，但数值与 power 一致（满级eq = base×1.40 是参考值，desc 写 Lv.1 裸倍率即可，如 100%）
- 隐藏职业拆解：如果 v151 里 拳师 的线吸收了原隐藏职业机制（龙裔→血怒/时咒→时律/星语→疾风/暗影神谕→幽祷/暮影→影舞/淬势→破绽），把对应机制技能并入该线
- 完成验证：`python -c "from game.data import skills; print('ok')"`（在项目根目录跑）不崩
- **禁 commit，禁跑全量回归，禁改测试文件**
- 不读全项目！技能表原文 + 字段映射 + 下面样例就够

## 现有格式样例（抄这个）
```python
# PLAYER_SKILLS（基础技能）
"sk_hui_kan": {
    "lv": 1, "mp": 3, "power": 1.0, "kind": "物理",
    "res_gain": 1,   # ← 旧资源条字段，v151 换 mech_gain / mech+mech_val
    "cond": {"type": "player_first", "mult": 1.15, "label": "先手压制"},
    "desc": "长剑划出利落的弧光——造成 100% 物理伤害；若你的速度高于目标，先发剑势更盛(伤害＋15%)",
    "name": "挥砍",
},
# BRANCH_SKILLS（分支技能）
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
            },
        },
        2: {  # B线
            ...
        },
    },
},
```

## 输出
完成后报告：改了哪些技能（旧 key → 新 key）、新增哪些、哪些 v151 机制字段引擎不支持（列出来，主 agent 收尾处理）
