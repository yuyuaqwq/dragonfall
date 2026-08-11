# -*- coding: utf-8 -*-
"""v95.28 补：24 个副本/特殊区域'入口'子区域场景描述（第一批扫描漏网，'XX入口'也是占位符）"""
import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SUBAREAS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game", "data", "subareas.py")

DESCS2 = {
    "goblin_camp": "哥布林营地入口：歪斜的木栅栏围出一片喧闹的营地，绿皮身影在篝火间窜动，臭味与叫嚷声隔着老远就能闻到。",
    "sea_cave": "海蚀洞窟入口：潮水在洞口涨落，岩壁上挂着海藻与盐霜。洞内漆黑，只有深处传来水珠滴落的回声。",
    "deer_fort": "鹿角要塞入口：废弃要塞的拱门爬满藤蔓，门楣上残存着白鹿纹章。风穿过门洞，带来陈年的铁锈气。",
    "old_king_tomb": "旧王陵入口：石门半掩在荒草间，门前的石狮已风化得面目模糊。王陵深处的黑暗仿佛在等待什么。",
    "secret_crypt": "圣堂地窖入口：大圣堂深处的暗门，石阶盘旋向下。烛台的余烬还冒着轻烟，空气里混着蜡与尘土的味道。",
    "holy_trial": "圣光试炼场入口：试炼场的石拱门刻着圣辉纹章，门前立着两尊持剑骑士像。据说只有通过试炼者才能踏过门槛。",
    "elven_ruins": "精灵废墟入口：坍塌的月白石柱散落一地，浮雕上的精灵文字已被风雨磨平。废墟深处有微光一闪而逝。",
    "moon_temple": "月神圣殿入口：银白的神殿大门半开，门楣上的月牙纹样在夜里会泛起柔光。殿内寂静得能听见自己的心跳。",
    "ash_temple": "烬山祭坛入口：黑曜石砌成的门廊布满焦痕，门内飘出硫磺与灰烬的气味。祭坛深处的火光忽明忽暗。",
    "abyss_gate": "深渊裂隙入口：大地裂开一道巨缝，边缘的岩石泛着诡异的紫光。缝隙深处传来若有若无的低语。",
    "frost_throne": "冰霜王座入口：冰晶凝结的拱门晶莹剔透，寒气从门内涌出，在门槛上结成一层薄霜。",
    "dragon_tomb": "龙之墓入口：巨龙骸骨的胸腔形成天然拱门，龙骨上还残留着微弱的魔力光辉。墓穴深处仿佛有龙吟回荡。",
    "storm_throne": "风暴王座入口：雷云在入口上空盘旋，石阶上布满焦黑的闪电痕迹。门内狂风不止，吹得人睁不开眼。",
    "sunken_ship": "沉船湾入口：一艘古船的残骸半埋在沙滩上，船身倾斜，桅杆折断。退潮时能看到船舷上的古老徽记。",
    "siren_nest": "海妖巢穴入口：礁石间的洞口被贝壳与海藻覆盖，洞口传出缥缈的歌声，让人不由自主地想要靠近。",
    "sea_god_temple": "海神神殿入口：珊瑚与贝壳砌成的殿门立在浅海中，门柱上雕刻着持三叉戟的海神像，潮水在门槛外徘徊。",
    "deep_dragon_palace": "深海龙宫入口：水晶拱门在深海中泛着蓝光，门两侧立着龙形的雕像，水压在这里骤然加重。",
    "gray_dwarf": "灰矮人要塞入口：厚重的石门嵌在岩壁中，门楣刻着矮人符文。门缝里透出熔炉的红光与沉闷的锻声。",
    "under_dragon": "地底龙巢入口：巨大的龙爪痕迹刻在岩壁上，洞口堆着磨得发亮的兽骨。巢内传来沉重的呼吸声。",
    "abyss_throne": "深渊王座入口：黑曜石巨门矗立在黑暗尽头，门上的纹路如同蠕动的触须。门后是深渊的最深处。",
    "eye_of_storm": "风暴之眼入口：风眼正对着一道石门，气流在门前旋转成漩涡。门内平静得反常，仿佛风暴都被驯服了。",
    "cloud_sanctum": "云中圣殿入口：云梯的尽头是一扇月光石大门，门框镶着风纹。殿门半开，圣光从门缝中倾泻而出。",
    "lost_library": "失落图书馆入口：石阶通向地下的穹顶大厅，门前的雕像捧着翻开的书卷。馆内飘着纸墨与灰尘的古老气息。",
    "ember_corridor": "灰烬回廊入口：焦黑的石廊在灰烬平原尽头敞开，廊壁上的浮雕描绘着烈焰与陨落。回廊深处红光隐现。",
}


def main():
    with open(SUBAREAS_PATH, encoding="utf-8") as f:
        lines = f.readlines()

    cur_map = None
    cur_id = None
    replaced = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('"') and line.strip().endswith('": ['):
            cur_map = line.strip().split('"')[1]
            continue
        m = re.search(r'"id"\s*:\s*"([^"]+)"', line)
        if m:
            cur_id = m.group(1)
            continue
        m = re.search(r'"desc"\s*:\s*"([^"]*)"', line)
        if m and cur_id and cur_map in DESCS2 and cur_id == f"{cur_map}_1":
            old = m.group(1)
            new = DESCS2[cur_map]
            lines[i] = line.replace(f'"{old}"', f'"{new}"', 1)
            replaced += 1
            cur_id = None

    print(f"替换入口描述: {replaced} / {len(DESCS2)}")
    with open(SUBAREAS_PATH, "w", encoding="utf-8", newline="") as f:
        f.writelines(lines)
    print("已写回 subareas.py")


if __name__ == "__main__":
    main()
