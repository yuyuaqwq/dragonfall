# -*- coding: utf-8 -*-
"""v101.25g 物品/装备描述批量补全（2026-08-12 鱼鱼：物品详情要有品质/分类/描述）

做法：把描述模板规则 + 注入循环写进数据文件底部（items.py / equip_roster.py），
     与 v101.25e 分类/品质注入同款风格——新加材料/装备零改动自动有描述。
已手写 desc 的条目保留不动；确定性哈希选变体（同名字永远同描述）。
"""
import hashlib
import os
import re
import sys

PLUGIN = r"C:\Users\yuyu\qqbot\data\plugins\dragonfall"
ITEMS_PY = os.path.join(PLUGIN, "game", "data", "items.py")
EQ_PY = os.path.join(PLUGIN, "game", "data", "equip_roster.py")


def pick(name, variants):
    h = int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16)
    return variants[h % len(variants)]


# ================= 材料描述模板（子关键词 → 变体列表） =================
MAT_TMPL = '''
# ================= 材料描述生成（v101.25g 鱼鱼：物品详情要有描述） =================
# 手写 desc 优先保留；缺省按类型/子关键词模板生成（确定性哈希选变体）
_MAT_DESC_RULES = {
    "兽材": {
        ("皮",): ["{name}，质地坚韧的兽皮，缝制护甲的上等材料。", "{name}，带着体温的皮革，铁匠铺常年收购。", "{name}，厚实耐用的皮毛，鞣制后能做护具内衬。"],
        ("毛", "鬃"): ["{name}，柔软蓬松的兽毛，填充护具能抵御寒风。", "{name}，粗硬的鬃毛，搓成绳索结实耐用。"],
        ("牙", "獠牙"): ["{name}，锋利的兽牙，可打磨成武器配件或饰品。", "{name}，泛着寒光的獠牙，是猎人的战利品。"],
        ("角",): ["{name}，坚硬有光泽的兽角，锻造与工艺的上佳材料。", "{name}，螺旋状的兽角，磨成粉末可入药。"],
        ("骨",): ["{name}，打磨光滑的兽骨，可雕刻成骨饰或工具柄。", "{name}，粗壮的兽骨，敲碎后髓质可提炼精华。"],
        ("爪",): ["{name}，弯钩般的兽爪，锋利程度不输刀刃。", "{name}，坚硬锐利的兽爪，镶嵌在武器上可增杀伤。"],
        ("羽",): ["{name}，色泽鲜亮的羽毛，箭矢尾羽的首选。", "{name}，轻盈柔韧的飞羽，风系附魔常用材料。"],
        ("壳",): ["{name}，坚硬厚实的甲壳，天然的保护材料。", "{name}，泛着光泽的甲壳，磨碎后是炼金原料。"],
        ("鳞",): ["{name}，细密交错的鳞片，防御与装饰两相宜。", "{name}，覆着微光的鳞片，水火不侵的天然护材。"],
        ("蹄",): ["{name}，厚实的兽蹄甲，耐磨程度超乎想象。", "{name}，结实的蹄甲，能加工成纽扣或小配件。"],
        ("尾",): ["{name}，柔韧的兽尾，编织后是上好的绳索。", "{name}，带着独特气息的尾毛，炼金师偶尔会用到。"],
        ("血",): ["{name}，腥气未散的兽血，炼金术的常用媒介。", "{name}，殷红的兽血，蕴含着一丝野性力量。"],
    },
    "食材": {
        ("鱼",): ["{name}，鲜活肥美的河鲜，烤一烤就香气四溢。", "{name}，鳞片银亮的鲜鱼，是酒馆菜单的常客。", "{name}，肉质细嫩的鱼，煮汤清甜可口。"],
        ("肉",): ["{name}，新鲜宰割的兽肉，篝火上一烤滋滋冒油。", "{name}，纹理分明的肉块，是冒险者的能量来源。"],
        ("蛋",): ["{name}，温润的禽蛋，煎炒蒸煮样样皆宜。", "{name}，个头饱满的蛋，敲开是金黄的蛋液。"],
        ("果",): ["{name}，饱满多汁的野果，酸甜解渴。", "{name}，挂在枝头的成熟果实，补充体力的小零嘴。"],
        ("菜", "蔬"): ["{name}，水灵灵的新鲜蔬菜，炊事兵的宝贝。", "{name}，带着泥土气息的野菜，洗净就能下锅。"],
        ("米", "麦"): ["{name}，颗粒饱满的谷物，磨成粉是主食来源。", "{name}，金黄的麦穗，烘烤后有麦芽的甜香。"],
        ("蜜",): ["{name}，金黄透亮的蜂蜜，甜到心坎里。", "{name}，野蜂巢里淌出的蜜露，滋补又美味。"],
        ("乳",): ["{name}，新鲜温热的奶，牧民家最朴实的馈赠。", "{name}，奶香浓郁的乳汁，发酵后别有风味。"],
        ("虾", "蟹", "贝", "腕足"): ["{name}，带着海水咸鲜的甲壳鲜物，清蒸最是原味。", "{name}，壳硬肉肥的海产，渔港最爱的下酒菜。"],
    },
    "草药": {
        ("草",): ["{name}，带着晨露的草药，叶片揉碎有清香。", "{name}，路旁常见的药草，晒干后能久存。"],
        ("花",): ["{name}，花瓣娇艳的花朵，入药有安神之效。", "{name}，香气袭人的花，晒干泡茶别有一番风味。"],
        ("根",): ["{name}，须根繁茂的药根，苦味入药最见效。", "{name}，粗壮有力的根茎，切片晒干是常用药材。"],
        ("叶",): ["{name}，肥厚翠绿的叶片，捣碎外敷能止血。", "{name}，脉络清晰的叶子，煮水有清热的功效。"],
        ("菇", "菌"): ["{name}，雨后冒出的菌菇，伞盖饱满肉质厚。", "{name}，躲藏在腐木下的蘑菇，小心甄别才能入菜。"],
        ("藤",): ["{name}，攀援缠绕的藤蔓，柔韧程度胜过绳索。", "{name}，表皮粗糙的老藤，蕴含丰富的汁液。"],
        ("参", "芝"): ["{name}，形如人形的珍贵药材，补气养元的佳品。", "{name}，菌盖上泛着光泽的灵芝，可遇不可求。"],
        ("芦",): ["{name}，青翠多汁的芦草，汁液清凉解毒。", "{name}，叶鞘肥厚的芦草，捣汁可外敷消肿。"],
    },
    "矿石": {
        ("矿", "岩", "石"): ["{name}，沉甸甸的矿石，敲开有闪烁的矿脉。", "{name}，边缘锋利的岩块，是锻造的原料基石。", "{name}，粗糙的矿石表面，隐约可见金属光泽。"],
        ("铁", "钢", "锭"): ["{name}，乌黑的铁锭，锻造台上叮当作响。", "{name}，淬炼过的金属块，是打造武器的骨干。"],
        ("铜", "锡", "铅"): ["{name}，泛着暗红的金属块，延展性极好。", "{name}，质地柔软的金属，新手铁匠的练习材料。"],
        ("银", "金"): ["{name}，泛着贵气光泽的金属，打磨后耀眼夺目。", "{name}，价值不菲的贵金属，珠宝匠人的心头好。"],
        ("玉", "砂"): ["{name}，温润细腻的玉料，雕刻成饰品价值倍增。", "{name}，颗粒均匀的矿砂，淘洗后可得精矿。"],
    },
    "木材": {
        ("木", "树"): ["{name}，纹理细密的木材，敲击有清脆的回响。", "{name}，年轮清晰的木料，烘干后不易变形。"],
        ("枝", "柴"): ["{name}，干爽的树枝，篝火的完美燃料。", "{name}，劈好的柴火，营地过夜全靠它。"],
        ("板",): ["{name}，刨平的好木板，木匠的必备料。", "{name}，厚薄均匀的木板，做箱做盾都合适。"],
    },
    "织物": {
        ("布",): ["{name}，织法细密的布料，缝缝补补的日常材料。", "{name}，手感柔软的棉布，裁衣做包皆可。"],
        ("丝", "绸"): ["{name}，光滑如水的丝绸，贵族才用得起的料子。", "{name}，泛着珠光的丝线织物，高级时装的灵魂。"],
        ("棉", "麻"): ["{name}，透气吸汗的麻布，远行者的首选。", "{name}，蓬松洁白的棉絮，保暖填充两相宜。"],
        ("绒", "线", "絮", "纱"): ["{name}，细软蓬松的绒料，冬天最暖和的里衬。", "{name}，捻得均匀的纱线，织布绣花都能用。"],
    },
    "宝石": {
        ("宝石", "水晶"): ["{name}，折射着光芒的晶体，镶嵌在首饰上璀璨夺目。", "{name}，晶莹剔透的水晶，蕴藏着纯粹的元素之力。"],
        ("珍珠", "珠"): ["{name}，圆润饱满的珍珠，贝母日积月累的馈赠。", "{name}，泛着柔和光泽的珠子，串成项链价值不菲。"],
        ("翡翠", "玛瑙", "琥珀", "钻石", "玉髓"): ["{name}，色泽温润的宝石，工匠手中的点睛之石。", "{name}，坚硬罕见的宝石，是身份与财富的象征。"],
    },
    "精华": {
        ("粉", "尘", "灰", "烬"): ["{name}，细腻如雪的粉末，炼金锅里咕嘟冒泡的常客。", "{name}，泛着微光的粉尘，附着着淡淡的魔力。"],
        ("液", "涎", "浆", "露", "泪"): ["{name}，装在瓶里晃荡的液体，气味奇异但很值钱。", "{name}，黏稠的浆液，炼金师视若珍宝。"],
        ("核", "晶", "髓"): ["{name}，凝聚着能量的核心，魔导器运转的燃料。", "{name}，散发着微光的晶核，蕴含着浓缩的力量。"],
        ("魂", "息", "精华"): ["{name}，带着神秘气息的精华，触碰时有微弱的共鸣。", "{name}，凝而不散的精华，是高级炼金的核心材料。"],
    },
    "杂物": [("{name}，看起来平平无奇，说不定在哪能派上用场。",), ("{name}，路边捡到的小物件，商贩们愿意收下。",), ("{name}，说不清来历的小东西，留着总没错。",), ("{name}，常见的小杂物，积少成多也是一笔收入。",)],
    "收藏": [("{name}，颇具纪念意义的藏品，收藏家愿意出高价。",)],
    "传说": [("{name}，传闻中才存在的至宝，价值无法估量。",)],
    "任务道具": [("{name}，与某个任务息息相关，最好随身携带。",)],
}
_MAT_DESC_FALLBACK = ["{name}，看似普通，却有它独到的用处。", "{name}，冒险路上常见的小材料，别小看它。"]


def _gen_mat_desc(name: str, mtype: str) -> str:
    rules = _MAT_DESC_RULES.get(mtype)
    if not rules:
        return _pick_desc(name, _MAT_DESC_FALLBACK).format(name=name)
    # 子关键词优先（取最长命中）
    best = None
    for kws, variants in rules.items():
        if isinstance(variants, tuple) and len(variants) == 1 and isinstance(variants[0], str):
            variants = [variants[0]]
        if any(k in name for k in kws):
            if best is None or len(kws[0]) > len(best[0]):
                best = (kws, variants)
    if best:
        return _pick_desc(name, best[1]).format(name=name)
    # 类型级兜底
    all_v = [v for kws, v in rules.items() for v in v] if isinstance(rules, dict) else []
    if all_v:
        return _pick_desc(name, all_v).format(name=name)
    return _pick_desc(name, _MAT_DESC_FALLBACK).format(name=name)


def _pick_desc(name: str, variants) -> str:
    _h = int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16)
    return variants[_h % len(variants)]
'''

MAT_INJECT = '''

# ================= 材料 desc 注入（v101.25g，手写优先） =================
for _mid, _m in MATERIALS.items():
    if not _m.get("desc"):
        _m["desc"] = _gen_mat_desc(_m["name"], _m.get("type", "杂物"))
'''

# ================= 装备描述模板 =================
EQ_TMPL = '''
# ================= 装备描述生成（v101.25g 鱼鱼：每个装备都要有描述） =================
# 系列主题 × 部位/武器类型模板；手写 desc 优先保留
_EQ_SERIES_THEME = {
    "橡木": "橡木镇匠人的朴实手艺，耐用又可靠",
    "白鹿": "白鹿之森猎人的精巧之作，轻便而灵动",
    "银铃": "银铃河畔工匠的细心打磨，线条干净利落",
    "翡翠": "翡翠森林的藤蔓缠绕纹样，带着自然的生机",
    "迷雾": "迷雾沼泽中锻造的神秘器物，蒙着一层水汽",
    "铁港": "铁港城船匠与铁匠的合作，透着海风的咸涩",
    "圣光": "圣光教会赐福的制式装备，纹着金色的圣徽",
    "月语": "月语精灵的月光工艺，优雅得不像凡物",
    "霜狼": "北境霜狼氏族的手笔，粗犷中带着寒气",
    "龙脊": "龙脊山脉矮人的重锤杰作，坚固得能扛住巨龙的吐息",
    "海神": "海神信徒的祭祀器物，浸泡过潮汐的低语",
    "地底": "地底矿脉深处出土的造物，沉静而厚重",
    "苍穹": "苍穹之上流云般轻盈的工艺，似乎随时会乘风而起",
    "星尘": "星尘降临之地的瑰丽造物，流转着点点星光",
    "灰烬守卫": "灰烬守卫的制式装备，淬炼过烈焰的余温",
}
_EQ_SLOT_DESC = {
    "weapon": {
        "sword": "{series}风格的长剑，剑脊笔直，护手朴素",
        "dagger": "{series}风格的短刃，轻巧锋利，适合贴身缠斗",
        "staff": "{series}风格的法杖，杖身刻着细密的魔纹",
        "bow": "{series}风格的长弓，弓臂弧度优美，弦声清越",
        "mace": "{series}风格的战锤，锤头沉重，一击足以破盾",
        "fist": "{series}风格的拳套，贴合拳面，攻防一体",
        "shield": "{series}风格的盾牌，盾面厚实，能挡下大部分攻击",
        "spear": "{series}风格的长枪，枪尖雪亮，横扫千军",
        "axe": "{series}风格的战斧，斧刃开得极利，势大力沉",
    },
    "helm": "{series}风格的头盔，护住要害，通风透气",
    "armor": "{series}风格的护甲，版型合体，活动自如",
    "legs": "{series}风格的护腿，膝盖处加厚，耐磨耐打",
    "boots": "{series}风格的靴子，鞋底防滑，走山路也稳当",
    "ring": "{series}风格的戒指，戒面光滑，指节处恰到好处",
    "necklace": "{series}风格的项链，链坠做工精细，贴身佩戴",
}


def _gen_eq_desc(e: dict) -> str:
    series = e.get("series", "冒险者")
    theme = _EQ_SERIES_THEME.get(series, f"{series}工匠的作品")
    slot = e.get("slot", "armor")
    if slot == "weapon":
        wt = e.get("weapon_type", "sword")
        sub = _EQ_SLOT_DESC["weapon"].get(wt, _EQ_SLOT_DESC["weapon"]["sword"])
        base = sub.format(series=series)
    else:
        base = _EQ_SLOT_DESC.get(slot, _EQ_SLOT_DESC["armor"]).format(series=series)
    extra = ""
    if e.get("source") == "boss":
        extra = "，据说是强者的战利品"
    elif e.get("source") == "legend":
        extra = "，传说中才有的名物"
    elif e.get("quality") == "orange":
        extra = "，绝非凡品"
    elif e.get("quality") == "purple":
        extra = "，做工考究"
    return f"{base}。{theme}{extra}。"
'''

EQ_INJECT = '''

# ================= 装备 desc 注入（v101.25g，手写优先） =================
for _rid, _r in EQUIP_ROSTER.items():
    if not _r.get("desc"):
        _r["desc"] = _gen_eq_desc(_r)
'''


def apply(path, anchor, block, inject):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    if "_gen_mat_desc" in src or "_gen_eq_desc" in src:
        print(f"{os.path.basename(path)}: 已注入过，跳过")
        return
    if anchor not in src:
        print(f"{os.path.basename(path)}: 锚点未找到！")
        return
    src = src.replace(anchor, anchor + block + inject)
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"{os.path.basename(path)}: 注入完成（{len(block)+len(inject)} chars）")


def main():
    apply(ITEMS_PY, "# 材料按名索引（背包显示/出售设施匹配用）", MAT_TMPL, MAT_INJECT)
    apply(EQ_PY, "# 名册查询辅助：按名称索引（锻造/掉落/商店通用）", EQ_TMPL, EQ_INJECT)


if __name__ == "__main__":
    main()
