# -*- coding: utf-8 -*-
"""奥兰迪亚·余烬纪年 数据层 - hidden_monsters.py（v87 04 章十六节：隐藏怪物）

低概率彩蛋怪——不在地图常规怪物列表，探索时独立判定出现（≤1%）。
格式同 maps.py 怪物 6 元组：["m_id", "名字", role, lv, [技能], [掉落]]
lv 用相对值（如 +2 = 地图等级+2），combat 展开时换算。
"""

# 隐藏怪物表：key = id，value = dict
# cond 出现条件（combat 判定）：
#   forest  森林类地图（type 或 id 含 forest/wood/glade）
#   water   水域类地图（river/lake/sea/reef/dock）
#   ruin    遗迹/地底（ruin/mine/abyss/battlefield/altar/underground）
#   night   仅夜间（时间系统时段为夜晚）
#   any     任意野外
HIDDEN_MONSTERS = {
    "e_gold_slime": {
        "id": "e_gold_slime", "name": "黄金史莱姆", "role": "elite",
        "lv_off": 2, "skills": ["ms_du_ya"],
        "drops": ["琥珀精华"], "gold_mult": 80,
        "cond": "any", "chance": 0.004, "tag": "✨ 隐藏",
        "flavor": "一只通体金黄的史莱姆，在阳光下闪闪发光！",
    },
    "e_white_stag": {
        "id": "e_white_stag", "name": "白鹿王", "role": "elite",
        "lv_off": 3, "skills": ["ms_chong_zhuang"],
        "drops": ["白鹿角"], "gold_mult": 40,
        "cond": "forest_night", "chance": 0.005, "tag": "✨ 隐藏",
        "flavor": "月光下，一匹通体雪白的巨鹿正低头饮水，鹿角泛着圣洁的光。",
    },
    "e_glimmer_fish": {
        "id": "e_glimmer_fish", "name": "荧光鱼群", "role": "elite",
        "lv_off": 1, "skills": ["ms_shui_dan"],
        "drops": ["荧光鳞"], "gold_mult": 20,
        "cond": "water", "chance": 0.005, "tag": "✨ 隐藏",
        "flavor": "水面下闪过一片荧光，一群发光的鱼正逆流而上！",
    },
    "e_rune_golem": {
        "id": "e_rune_golem", "name": "符文魔像", "role": "elite",
        "lv_off": 5, "skills": ["ms_fu_wen_chong_ji"],
        "drops": ["符文碎片"], "gold_mult": 30,
        "cond": "ruin", "chance": 0.003, "tag": "✨ 隐藏",
        "flavor": "一尊刻满符文的石像缓缓转动头颅，符文亮起猩红的光。",
    },
    "e_shadow_stalker": {
        "id": "e_shadow_stalker", "name": "暗影猎手", "role": "elite",
        "lv_off": 6, "skills": ["ms_an_ying_dan"],
        "drops": ["暗影精华"], "gold_mult": 50,
        "cond": "night_any", "chance": 0.003, "tag": "✨ 隐藏",
        "flavor": "黑暗中一双眼睛盯着你——下一秒，利刃已到面前！",
    },
    "e_fortune_fox": {
        "id": "e_fortune_fox", "name": "幸运灵狐", "role": "elite",
        "lv_off": 1, "skills": ["ms_du_ya"],
        "drops": ["幸运符"], "gold_mult": 60,
        "cond": "any", "chance": 0.002, "tag": "✨ 隐藏",
        "flavor": "一只通体赤红的小狐狸好奇地绕着你转圈，尾巴尖上闪着金光。",
    },
    # ============ v97.6 隐藏怪物扩容 6→25（区域分布：南境/中域/西境/北境/东境/海域/地底/天空） ============
    "e_forest_wolf_king": {
        "id": "e_forest_wolf_king", "name": "森林狼王", "role": "elite",
        "lv_off": 3, "skills": ["ms_chong_zhuang"],
        "drops": ["狼皮", "兽肉"], "gold_mult": 25,
        "cond": "forest", "chance": 0.004, "tag": "✨ 隐藏",
        "maps": ["oak_plain", "white_deer_forest", "emerald_forest"],
        "flavor": "灌木丛后传来低沉的呜咽——一头银灰色的巨狼缓缓走出，狼王的目光冰冷而威严。",
    },
    "e_swamp_croc": {
        "id": "e_swamp_croc", "name": "沼泽巨鳄", "role": "elite",
        "lv_off": 2, "skills": ["ms_shui_dan"],
        "drops": ["沼泽花", "甲壳残片"], "gold_mult": 20,
        "cond": "water", "chance": 0.004, "tag": "✨ 隐藏",
        "maps": ["misty_swamp", "silver_brook"],
        "flavor": "水面毫无征兆地裂开——一张布满利齿的大嘴直扑而来！",
    },
    "e_mine_troll": {
        "id": "e_mine_troll", "name": "矿洞巨魔", "role": "elite",
        "lv_off": 4, "skills": ["ms_fu_wen_chong_ji"],
        "drops": ["铁矿石", "精铁"], "gold_mult": 30,
        "cond": "ruin", "chance": 0.003, "tag": "✨ 隐藏",
        "maps": ["hill_mine", "deep_tunnel"],
        "flavor": "矿道深处传来沉重的脚步声——一个三米高的巨魔抡着矿锤，正把挡路的矿石砸得粉碎！",
    },
    "e_abbey_guardian": {
        "id": "e_abbey_guardian", "name": "圣堂武僧", "role": "elite",
        "lv_off": 5, "skills": ["ms_an_ying_dan"],
        "drops": ["圣水"], "gold_mult": 35,
        "cond": "any", "chance": 0.003, "tag": "✨ 隐藏",
        "maps": ["dawn_city", "dawn_cathedral", "white_abbey"],
        "flavor": "一个光头武僧双手合十拦住你：“施主，陪贫僧过两招。”——说完一拳已经招呼过来了！",
    },
    "e_royal_guard": {
        "id": "e_royal_guard", "name": "王都禁卫", "role": "elite",
        "lv_off": 6, "skills": ["ms_chong_zhuang"],
        "drops": ["副官勋章"], "gold_mult": 40,
        "cond": "any", "chance": 0.002, "tag": "✨ 隐藏",
        "maps": ["dawn_city", "king_road", "holy_trial"],
        "flavor": "一队巡逻的禁卫停下脚步，队长打量你片刻：“可疑人物，例行检查！”",
    },
    "e_moon_wolf": {
        "id": "e_moon_wolf", "name": "月狼", "role": "elite",
        "lv_off": 3, "skills": ["ms_du_ya"],
        "drops": ["月光精华"], "gold_mult": 45,
        "cond": "night_any", "chance": 0.003, "tag": "✨ 隐藏",
        "maps": ["silverwood", "moon_glade", "starlake", "moonshadow_wood"],
        "flavor": "月光下，一头银白的狼站在高处，毛尖泛着月华——它仰头长啸，啸声直穿夜空。",
    },
    "e_elf_sentinel": {
        "id": "e_elf_sentinel", "name": "精灵哨兵", "role": "elite",
        "lv_off": 4, "skills": ["ms_shui_dan"],
        "drops": ["林语之叶"], "gold_mult": 30,
        "cond": "forest", "chance": 0.003, "tag": "✨ 隐藏",
        "maps": ["silverwood", "ancient_tree", "moon_temple", "emerald_valley"],
        "flavor": "树影里无声无息地落下一道身影，精灵哨兵拉满长弓：“越过此线者，箭下不留情。”",
    },
    "e_frost_bear": {
        "id": "e_frost_bear", "name": "霜原巨熊", "role": "elite",
        "lv_off": 4, "skills": ["ms_chong_zhuang"],
        "drops": ["冰熊皮", "雪狼皮"], "gold_mult": 35,
        "cond": "any", "chance": 0.003, "tag": "✨ 隐藏",
        "maps": ["frost_horn", "frost_field", "winter_lake", "cold_ridge"],
        "flavor": "雪幕里站起一座山——霜原巨熊抖落身上的积雪，发出一声震得树挂簌簌落下的咆哮！",
    },
    "e_ash_salamander": {
        "id": "e_ash_salamander", "name": "烬火蝾螈", "role": "elite",
        "lv_off": 5, "skills": ["ms_fu_wen_chong_ji"],
        "drops": ["烬火余烬"], "gold_mult": 40,
        "cond": "ruin", "chance": 0.003, "tag": "✨ 隐藏",
        "maps": ["cinder_mountain", "ash_temple", "forge_valley", "molten_abyss"],
        "flavor": "熔岩般的鳞片在暗处明灭，烬火蝾螈从灰烬中爬出，所过之处留下灼热的爪印。",
    },
    "e_dragon_hatchling": {
        "id": "e_dragon_hatchling", "name": "幼龙", "role": "elite",
        "lv_off": 6, "skills": ["ms_an_ying_dan"],
        "drops": ["幼龙鳞"], "gold_mult": 60,
        "cond": "any", "chance": 0.002, "tag": "✨ 隐藏",
        "maps": ["dragon_pass", "dragon_ridge", "dragon_roost", "dragon_tomb"],
        "flavor": "崖壁的阴影里，一双琥珀色的竖瞳正打量着你——一只还没长开翅膀的幼龙！",
    },
    "e_storm_eagle": {
        "id": "e_storm_eagle", "name": "雷暴鹰", "role": "elite",
        "lv_off": 5, "skills": ["ms_du_ya"],
        "drops": ["天鹰羽"], "gold_mult": 35,
        "cond": "any", "chance": 0.003, "tag": "✨ 隐藏",
        "maps": ["storm_cliff", "storm_throne", "redridge_plateau"],
        "flavor": "雷云中劈下一道闪电——雷暴鹰穿过电光俯冲而来，爪尖噼啪作响！",
    },
    "e_sea_serpent": {
        "id": "e_sea_serpent", "name": "海蛇", "role": "elite",
        "lv_off": 5, "skills": ["ms_shui_dan"],
        "drops": ["珍珠贝", "湖珍珠"], "gold_mult": 40,
        "cond": "water", "chance": 0.003, "tag": "✨ 隐藏",
        "maps": ["nameless_harbor", "mist_trench", "storm_sea", "black_tide_strait"],
        "flavor": "海面隆起一道水脊，巨大的海蛇破浪而起，鳞片在阳光下泛着冷光！",
    },
    "e_siren": {
        "id": "e_siren", "name": "塞壬", "role": "elite",
        "lv_off": 6, "skills": ["ms_shui_dan"],
        "drops": ["深渊珍珠"], "gold_mult": 50,
        "cond": "water", "chance": 0.002, "tag": "✨ 隐藏",
        "maps": ["siren_nest", "mermaid_bay", "coral_reef"],
        "flavor": "歌声从礁石后传来，婉转悠扬——塞壬探出半个身子，笑得美丽又危险。",
    },
    "e_deep_angler": {
        "id": "e_deep_angler", "name": "深海鮟鱇", "role": "elite",
        "lv_off": 7, "skills": ["ms_an_ying_dan"],
        "drops": ["荧光鳞"], "gold_mult": 45,
        "cond": "water", "chance": 0.003, "tag": "✨ 隐藏",
        "maps": ["deep_dragon_palace", "mist_trench", "shipwreck_graveyard"],
        "flavor": "幽暗的水底亮起一盏小灯——深海鮟鱇甩着发光的诱饵，缓缓向你游来。",
    },
    "e_fungus_king": {
        "id": "e_fungus_king", "name": "真菌之王", "role": "elite",
        "lv_off": 4, "skills": ["ms_du_ya"],
        "drops": ["真菌肉", "腐冠菌"], "gold_mult": 25,
        "cond": "ruin", "chance": 0.003, "tag": "✨ 隐藏",
        "maps": ["fungus_forest", "under_market", "deep_tunnel"],
        "flavor": "菌林中央，一株顶着伞盖的巨型真菌缓缓拔地而起，孢子如雪花般飘散！",
    },
    "e_lava_golem": {
        "id": "e_lava_golem", "name": "熔岩魔像", "role": "elite",
        "lv_off": 6, "skills": ["ms_fu_wen_chong_ji"],
        "drops": ["熔岩甲壳"], "gold_mult": 45,
        "cond": "ruin", "chance": 0.003, "tag": "✨ 隐藏",
        "maps": ["molten_abyss", "lava_bed", "ember_camp"],
        "flavor": "岩浆翻涌，一尊由熔岩凝成的巨像从火海中站起，裂缝里流淌着赤红的光！",
    },
    "e_ghost_knight": {
        "id": "e_ghost_knight", "name": "幽灵骑士", "role": "elite",
        "lv_off": 6, "skills": ["ms_an_ying_dan"],
        "drops": ["幽灵之尘"], "gold_mult": 45,
        "cond": "night_any", "chance": 0.002, "tag": "✨ 隐藏",
        "maps": ["old_king_tomb", "secret_crypt", "ancient_battlefield"],
        "flavor": "马蹄声由远及近——一位身着残甲的幽灵骑士策马而来，眼窝里燃着幽蓝的火焰。",
    },
    "e_cloud_serpent": {
        "id": "e_cloud_serpent", "name": "云龙", "role": "elite",
        "lv_off": 6, "skills": ["ms_shui_dan"],
        "drops": ["云絮"], "gold_mult": 40,
        "cond": "any", "chance": 0.003, "tag": "✨ 隐藏",
        "maps": ["cloud_sea", "cloud_sanctum", "sky_ladder_path", "starlight_terrace"],
        "flavor": "云海翻腾，一条通体洁白的龙形生物在云雾间游动，卷起漫天的云絮！",
    },
    "e_iron_bull": {
        "id": "e_iron_bull", "name": "铁角蛮牛", "role": "elite",
        "lv_off": 2, "skills": ["ms_chong_zhuang"],
        "drops": ["山羊角", "兽肉"], "gold_mult": 20,
        "cond": "any", "chance": 0.003, "tag": "✨ 隐藏",
        "maps": ["gold_plain", "border_castle", "knight_yard", "ironshield_town"],
        "flavor": "平原上传来隆隆的蹄声——一头铁角蛮牛红着眼朝你冲来，大地都在颤抖！",
    },
}
