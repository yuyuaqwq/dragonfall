# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - wild_king_data.py（v140 波2：野外 Boss 看守宝箱 · 野王体系）

设计依据：docs/方案 3.2 节（鱼鱼原创设计细化，2026-08-30）：
- 8 张高热度野外图各配 1 只『守箱野王』(b_guard_*)：全服同一时刻每图至多 1 只、
  全服 ≤3 只同时在场（刷新上限由 core/wild_king.py 保证）。
- 每日 4 个固定时段（08/14/20/02 点）刷新：日期+时段哈希全服一致选 1 只野王、
  只落在 8 张候选图之一，全服广播『🔥 野王现身于 xx 图，宝箱看守中！』。
- 消失条件：被击杀（立即消失解锁宝箱）/ 存活超时 90 分钟自动消失 / 每日 02 点强制重置。
- 宝箱解锁：Boss 尸体旁原地出现宝箱——击杀者（队伍）优先摸『战利箱』15 分钟，
  之后转公共箱（同图任意玩家每人 1 次）；每人每时段最多 1 次、每日最多 2 次。
- 内容：图纸保底 1 张 + 原石 20% + 装备碎片 25% + 独特收藏 5% + 高级强化石 + 金币
  （按野王等级带三档）；击杀者战利箱 100% 出保底图纸。
- 保底：① 个人连续 3 时段参与未开箱 → 第 4 时段保底券（保底券 = 自动获得一次开箱资格，
  不占时段/每日次数；记录在个人 wild_king_meta 的 pity 字段）
- 竞争：归属 = 最后一击 50% + 伤害贡献 50% 双因子；Boss 被抢杀不亏（宝箱 15 分钟后公共化）
- 安全：低等级野王伤害 ≈ 同级精英 ×1.3（单刷可过）；血量 = 1 人基准 ×(1+0.5×参战人数)弹性；
  打不过可等 15 分钟摸公共箱。

本文件纯数据、无逻辑（除轻量校验）；消费方为 core/wild_king.py + commands/combat.py。
⚠️ 不 import db；data/_assembly 加载期不允许 IO。
"""

# ================= 1. 时段定义（每日 4 时段，全服一致） =================
# hour：时段开始的小时（08/14/20/02）；label：展示名；next_hour：下一时段开始小时
WILD_KING_PERIODS = [
    {"hour": 2,  "label": "凌晨", "next_hour": 8},
    {"hour": 8,  "label": "上午", "next_hour": 14},
    {"hour": 14, "label": "下午", "next_hour": 20},
    {"hour": 20, "label": "夜晚", "next_hour": 2},
]

# 全服同时在场野王上限
WILD_KING_GLOBAL_LIMIT = 3
# 单只野王存活时长（秒）：90 分钟
WILD_KING_LIFETIME_SEC = 90 * 60
# 击杀者战利箱专属期（秒）：15 分钟
WILD_KING_LOOT_PRIORITY_SEC = 15 * 60
# 每日 4 时段最多开箱 1 次/时段、每日最多 2 次
WILD_KING_PER_PERIOD_LIMIT = 1
WILD_KING_PER_DAY_LIMIT = 2
# 个人保底：连续 N 个时段参与未开箱 → 下时段保底券
WILD_KING_PITY_PERIODS = 3
# 全服连续 N 个时段野王未击杀 → 下时段刷 2 只
WILD_KING_NO_KILL_EXTRA = 2
# 野王刷新时段（小时）
WILD_KING_SPAWN_HOURS = (2, 8, 14, 20)

# ================= 2. 野王定义（8 只，等级覆盖 20-90） =================
# key = b_guard_<拼音>（全服唯一，探索/战斗/宝箱按此定位）
# 字段：
#   name       展示名（西幻命名，含 '·'）
#   icon       emoji
#   map        固定出生图（8 张高热度野外图，lv 阶梯覆盖）
#   lv         野王等级（≈ 地图等级，覆盖 20-90）
#   hp_base    1 人基准血量（实际 = hp_base × (1 + 0.5×(参战人数-1))，见 core）
#   atk_mult   伤害倍率基准（≈ 同级精英 ×1.3；monster_stats 走 boss 模板再乘此值）
#   skills     技能 id 列表（MONSTER_SKILLS）
#   drops      材料掉落池（按名 resolve 材料，战利箱折算用）
#   chest_tier 宝箱档位（低/中/高 → WILD_KING_CHEST_TIERS）
#   desc       图鉴/遭遇风味
WILD_KINGS = {
    "b_guard_cang_mang": {
        "name": "苍狼王·铁鬃", "icon": "🐺", "map": "harbor_docks",
        "lv": 20, "hp_base": 26000, "atk_mult": 1.3,
        "skills": ["ms_zhong_ji", "ms_jiao_sha"],
        "drops": ["狼皮", "野猪牙"],
        "chest_tier": "low",
        "desc": "铁港码头的老霸主，据说它的宝箱里装着沉船上的财宝。",
    },
    "b_guard_ye_ge": {
        "name": "夜歌领主·黯羽", "icon": "🦉", "map": "silver_river",
        "lv": 28, "hp_base": 42000, "atk_mult": 1.3,
        "skills": ["ms_an_ying_zhua", "ms_an_ying_jian"],
        "drops": ["暗影精灵刃", "银辉月石"],
        "chest_tier": "low",
        "desc": "银铃河夜间的守望者，猫头鹰般的目光能看穿夜色。",
    },
    "b_guard_jin_sui": {
        "name": "金穗领主·沃土", "icon": "🌾", "map": "gold_plain",
        "lv": 38, "hp_base": 68000, "atk_mult": 1.3,
        "skills": ["ms_zhuang_ji", "ms_feng_ren"],
        "drops": ["金焰虎皮", "风之羽"],
        "chest_tier": "mid",
        "desc": "金穗平原的丰收之主，它的宝箱里藏着麦田深处的秘藏。",
    },
    "b_guard_lin_feng": {
        "name": "林风王·翠影", "icon": "🦌", "map": "silverwood",
        "lv": 48, "hp_base": 110000, "atk_mult": 1.3,
        "skills": ["ms_feng_ren", "ms_lie_yan_zhao"],
        "drops": ["林语之叶", "风之羽"],
        "chest_tier": "mid",
        "desc": "银月林海的守护巨鹿，角上缠着翡翠色的藤蔓。",
    },
    "b_guard_shuang_ya": {
        "name": "霜牙王·凛冬", "icon": "🐻‍❄️", "map": "frost_field",
        "lv": 60, "hp_base": 200000, "atk_mult": 1.3,
        "skills": ["ms_bing_xi", "ms_han_bing_zhu_fu"],
        "drops": ["冰狼牙", "霜白獠牙"],
        "chest_tier": "mid",
        "desc": "霜原上的巨熊，吐息能冻结整片雪原。",
    },
    "b_guard_yan_yan": {
        "name": "炎岩王·烬核", "icon": "🔥", "map": "cinder_mountain",
        "lv": 72, "hp_base": 360000, "atk_mult": 1.3,
        "skills": ["ms_huo_yan", "ms_lie_yan_zhao"],
        "drops": ["熔岩核心", "烬核"],
        "chest_tier": "high",
        "desc": "烬山之巅的火焰巨魔，它的宝箱像一座小型熔炉。",
    },
    "b_guard_long_gu": {
        "name": "龙脊王·裂岩", "icon": "🐉", "map": "dragon_ridge",
        "lv": 84, "hp_base": 620000, "atk_mult": 1.3,
        "skills": ["ms_long_zhao", "ms_long_lin_chong_ji", "ms_gu_long_wei_ya"],
        "drops": ["成年龙鳞", "古龙鳞"],
        "chest_tier": "high",
        "desc": "龙脊山脉的亚龙霸主，盘踞在古老龙骨之上。",
    },
    "b_guard_lei_ting": {
        "name": "雷霆王·裂空", "icon": "⚡", "map": "storm_plateau",
        "lv": 90, "hp_base": 900000, "atk_mult": 1.3,
        "skills": ["ms_lei_ji", "ms_feng_bao_zhi_yan"],
        "drops": ["雷晶", "雷霆之心"],
        "chest_tier": "high",
        "desc": "雷暴高原的霸主，振翅间引动九天雷霆。",
    },
}

# 候选出生图列表（8 张，与 WILD_KINGS 的 map 一致；刷新哈希只从这 8 张里选）
WILD_KING_MAPS = [k["map"] for k in WILD_KINGS.values()]

# ================= 3. 宝箱内容表（3 档：low / mid / high） =================
# 每次开箱独立 roll（图纸保底除外：战利箱 100% 图纸，公共箱 50%）。
# 字段：
#   gold_range  金币范围 [lo, hi]
#   bp_chance   图纸概率（0-1；战利箱强制 1.0 覆盖）
#   gem_chance  原石概率（C.roll_gem_drop 掉落——需传野王 monster 判定，命令层按此概率
#               roll 后调 C.roll_gem_drop(monster, boss_fixed) 生成 1 颗）
#   equip_chance 装备概率（成品装备：v140 装备掉落引擎 roll_drop_equip(野王lv, "boss")）
#   rune_chance 符文概率（蓝色/紫色品质，C.rune_item 构造）
#   stone_range 高级强化石数量范围 [lo, hi]（mat_gao_ji_qiang_hua_shi）
#   pages_range 图纸残页数量范围 [lo, hi]（mat_tu_zhi_can_ye，保底折算/已学图纸用）
#   mats        材料池（中文名，命令层 C.resolve("materials") 转 id；缺省用野王 drops）
#   collect     独特收藏池（中文名/材料 id；命中 → 收藏入包，低概率）
WILD_KING_CHEST_TIERS = {
    "low": {
        "gold_range": [300, 600],
        "bp_chance": 0.50,
        "gem_chance": 0.20,
        "equip_chance": 0.10,
        "rune_chance": 0.15,
        "stone_range": [1, 2],
        "pages_range": [2, 4],
        "mats": ["图纸残页", "高级强化石"],
        "collect": ["铁牌徽章"],
    },
    "mid": {
        "gold_range": [700, 1400],
        "bp_chance": 0.55,
        "gem_chance": 0.20,
        "equip_chance": 0.15,
        "rune_chance": 0.20,
        "stone_range": [2, 4],
        "pages_range": [3, 6],
        "mats": ["高级强化石", "战魂之尘"],
        "collect": ["余烬行者徽章"],
    },
    "high": {
        "gold_range": [1600, 3200],
        "bp_chance": 0.60,
        "gem_chance": 0.20,
        "equip_chance": 0.20,
        "rune_chance": 0.25,
        "stone_range": [3, 6],
        "pages_range": [4, 8],
        "mats": ["高级强化石", "敖澜之珠", "摩罗之冠"],
        "collect": ["余烬行者徽章"],
    },
}

# ================= 4. 保底券道具（发放用，纯记录；使用即视为开箱资格） =================
# 保底券 = 玩家 wild_king_meta 的 pity 计数（见 core），不新增物品表。
# 此处仅定义展示文案常量。
WILD_KING_PITY_VOUCHER_NAME = "野王保底券"


# ================= 5. 轻量启动校验（fail-fast，与 data/__init__ 风格一致） =================
def _validate():
    from ..data.items import MATERIALS  # 延迟导入防顶层循环
    from ..data.maps import MAP_BY_ID
    from ..data.monsters import MONSTER_SKILLS
    for kid, k in WILD_KINGS.items():
        assert k.get("map") in MAP_BY_ID, f"[WILD_KINGS:{kid}] 地图 {k.get('map')} 未定义"
        assert k.get("map") in WILD_KING_MAPS, f"[WILD_KINGS:{kid}] map 不在 WILD_KING_MAPS"
        assert MAP_BY_ID[k["map"]].get("type") == "野外", (
            f"[WILD_KINGS:{kid}] {k['map']} 不是野外图"
        )
        assert k.get("chest_tier") in WILD_KING_CHEST_TIERS, (
            f"[WILD_KINGS:{kid}] chest_tier {k.get('chest_tier')} 未定义"
        )
        for s in k.get("skills", []):
            assert s in MONSTER_SKILLS, f"[WILD_KINGS:{kid}] 技能 {s} 未定义"
        for d in k.get("drops", []):
            assert MATERIALS_BY_NAME(d) is not None or d in MATERIALS, (
                f"[WILD_KINGS:{kid}] 掉落材料 {d} 未在 MATERIALS 登记"
            )


def MATERIALS_BY_NAME(name):
    """按中文名在 MATERIALS 反查（延迟 import，与 core 层用法一致）。"""
    from ..data.items import MATERIALS
    for mid, m in MATERIALS.items():
        if m.get("name") == name:
            return mid
    return None
