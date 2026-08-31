# SA-2 任务卡：179 件蓝紫橙装备固定词条批量补全

## 目标
给 `C:/Users/yuyu/qqbot/data/plugins/dragonfall/game/data/affixes.py` 的 `SERIES_FIXED_AFFIX` 字典补上 v140 波1/2 新增的 179 件蓝紫橙装备的固定词条（目前缺失，测试 `固定词条全覆盖` 会红）。

## 背景
- `SERIES_FIXED_AFFIX` 是 dict：`{"装备名": [词条ID, ...]}`，按**装备中文名**索引（如 `"圣光长剑": ["armor_break"]`）
- 白装（white）/绿装（green）**豁免**（0/1 词条走随机池，不挂 SERIES_FIXED_AFFIX）
- 只有蓝（blue）/紫（purple）/橙（orange）需要固定词条
- v140 新增 179 件蓝紫橙装备缺固定词条，**规则：按同系列同部位继承已有成员的模式**

## 执行步骤
1. 运行脚本找出缺失清单：
```python
import sys, os
sys.path.insert(0, r"C:/Users/yuyu/qqbot")
sys.path.insert(0, r"C:/Users/yuyu/qqbot/data/plugins/dragonfall")
os.environ.setdefault("GWEN_GAME_DB", "tests/_tmp_sa2.db")
from game import content as C
miss = [(rid, r) for rid, r in C.EQUIP_ROSTER.items()
        if r["quality"] in ("blue", "purple", "orange") and r["name"] not in C.SERIES_FIXED_AFFIX]
print("missing:", len(miss))
for rid, r in miss:
    print(rid, r["name"], r["quality"], r["slot"], r.get("series", "?"), r.get("source", "?"))
```
2. **先人工核对**：跑下面脚本看每个系列的既有模式，再决定新成员配什么词条：
```python
from collections import defaultdict, Counter
patterns = defaultdict(lambda: defaultdict(list))
for rid, r in C.EQUIP_ROSTER.items():
    aff = C.SERIES_FIXED_AFFIX.get(r["name"])
    if aff is not None:
        patterns[r.get("series", "?")][r["slot"]].append(tuple(aff))
# 打印每个有缺失的系列的模式
for rid, r in miss_equips:  # 上一步的 miss
    s = r.get("series", "?")
    if s in patterns:
        print(f"== {s} ==")
        for slot, affs in patterns[s].items():
            print(f"  {slot}: {affs}")
```
3. **补词条规则**（重要）：
   - 同系列同部位有先例 → 继承最常用模式（如圣光 weapon 都是 armor_break）
   - 同系列无同部位 → 用同系列高频词条（出现最多的 2 个）
   - 系列完全无先例（新系列）→ 按武器类型/防具类型默认：
     - 武器：剑=armor_break / 法杖=meditate / 弓=precise,hunt / 匕首=crit_up,combo / 拳套=charge,combo / 权杖=heal_power / 盾=block / 枪=pierce
     - 防具：helm=dmg_reduce / armor=dmg_reduce,block 或 shield / legs=tenacity / boots=swift / necklace=meditate 或 purify / ring=crit_up
   - **尊重 special 特效主题**：装备有 special（特效描述）时，词条选和特效主题一致的（如铁壁胸甲 special 是"受击获得护盾" → 配 shield/dmg_reduce；霜羽长弓 special 是"冰属性伤害+减速" → 配 element_ice）
4. **落地**：把新词条追加到 `SERIES_FIXED_AFFIX` 字典末尾（在 `'守望者护符': ['crit_up', 'phys_ward']` 之后、`}` 之前），用 patch 工具或 Python 脚本。格式：
```python
    # ===== v140 波2 批量补全固定词条 =====
    '装备名': ['词条1', '词条2'],
```

## 可用的词条 ID（从 AFFIXES 抄）
bleed, armor_break, combo, execute, lifesteal, crit_up, crit_dmg, element_fire, element_ice, element_thunder, precise, pierce, pene_phys, pene_magi, pene_flat, pene_mflat, hunt, charge, counter, break_magic, purify, dragon_aw, block, thorns, dmg_reduce, phys_ward, magic_ward, thirst_phys, thirst_magi, shield, dodge, tenacity_cc, regen, meditate, swift, elem_resist, abyss_resist, hp_up, tenacity, luck, cdr, exp_bonus, gold_bonus, heal_power, shield_power

## 铁律
- **只改 `game/data/affixes.py` 的 SERIES_FIXED_AFFIX 字典**（追加条目），不碰其他文件
- **不 commit、不跑全量回归**（主 agent 收尾）
- 完成后运行验证：
```python
from game import content as C
miss = [(rid, r) for rid, r in C.EQUIP_ROSTER.items()
        if r["quality"] in ("blue", "purple", "orange") and r["name"] not in C.SERIES_FIXED_AFFIX]
print("剩余缺失:", len(miss))  # 应为 0
```
- 报告：补了多少件、按系列分类的清单、验证结果

## 注意
- affixes.py 是 **CRLF 行尾**大文件——改多行用 Python 行级脚本（readlines 定位锚点行后插入），**不要用 patch 工具多行替换**（CRLF 会缩进错乱）
- 文件末尾 SERIES_FIXED_AFFIX 的 `}` 在 995 行附近，锚点用 `'守望者护符': ['crit_up', 'phys_ward'],` 定位
