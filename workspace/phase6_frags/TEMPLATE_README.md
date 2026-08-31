# Phase 6 片段模板说明（子 agent 必读）
# ============================================================
# 每个子 agent 产出一个独立的 .py 片段文件，放到 workspace/phase6_frags/ 下。
# 片段文件是「纯数据声明」——所有 dict 定义好后，结尾必须有 MERGE 指令：
#
# MERGE = {
#     "EQUIP_ROSTER": { ... 新增名册条目 ... },
#     "SERIES_FIXED_AFFIX": { ... 新增固定词条 ... },
#     "SERIES_SETS": { ... 新增系列→套装名 ... },
#     "EQ_SERIES_THEME": { ... 新增系列描述 ... },
#     "MATERIALS": { ... 新增素材 ... },
#     "CRAFT_RECIPES": { ... 新增配方 ... },
# }
#
# 主 agent 会把 MERGE 里的条目合并进对应数据文件（equip_roster.py / affixes.py /
# sets.py / items.py / craft.py / class_sets.py），子 agent 不直接改源文件。
# ============================================================

# ---- 1. EQUIP_ROSTER 条目格式（game/data/equip_roster.py）----
# "eq_唯一id": {"name": "中文名", "slot": "weapon|helm|armor|legs|boots|ring|necklace",
#    "weapon_type": "sword|staff|bow|mace|dagger|fist|spear|shield"（仅武器）,
#    "quality": "white|green|blue|purple|orange", "lv": 等级,
#    "series": "系列名", "req": {"str|int|agi|vit": 数值}, "source": "锻造|图纸|商店"}
# 注意：id 必须是 eq_ + 拼音/英文唯一；name 全局唯一（用 workspace/phase6_frags/naming_plan.json 校验）

# ---- 2. SERIES_FIXED_AFFIX 条目格式（game/data/affixes.py）----
# "中文装备名": ["词条id1", "词条id2"]
# 词条 id 必须存在于 AFFIXES（game/data/affixes.py 已定义 104 种）。
# 常用词条：crit_up(暴击+5%) crit_dmg combo(连击) precise(精准) pierce(贯穿)
#   execute(处决) lifesteal(吸血) armor_break(破甲) charge(蓄力) counter(反击)
#   dodge(闪避) swift(迅捷) meditate(冥想) tenacity(坚韧) block(格挡)
#   dmg_reduce(减伤) shield(护盾) purify(净化) element_fire/ice/thunder(元素)
#   pene_phys(物穿) pene_magi(法穿) hunt(追猎) break_magic(破魔)
# 防御部位(helm/armor/legs/boots/ring/necklace)用 defense 类词条，
# 武器(weapon)用 attack 类词条（generate_roster_equip 会过滤 kind）。

# ---- 3. SERIES_SETS 条目格式（game/data/sets.py）----
# "系列名": "套装名"  （名册装备 series 命中 → 自动挂套装）

# ---- 4. EQ_SERIES_THEME 条目格式（game/data/equip_roster.py）----
# "系列名": "系列描述文案"

# ---- 5. MATERIALS 条目格式（game/data/items.py）----
# "mat_唯一id": {"price": 售价, "name": "中文名", "type": "兽材|矿石|布料|元素|图纸",
#    "desc": "描述文案"}

# ---- 6. CRAFT_RECIPES 条目格式（game/data/craft.py）----
# "rec_唯一id": {"slot": "部位", "quality": "品质", "lv": 等级,
#    "weapon_type": "武器类型"(仅武器), "mats": {"mat_id": 数量},
#    "gold": 金币, "desc": "描述", "name": "中文名", "roster_id": "eq_名册id",
#    "blueprint": "图纸名"(仅紫/橙品质需要)}

# ============================================================
# 校验脚本：片段产出后运行 python -c "import json,pathlib; ..." 检查 MERGE 结构合法
# ============================================================
