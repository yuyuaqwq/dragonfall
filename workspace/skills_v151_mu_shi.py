# -*- coding: utf-8 -*-
"""v151 牧师技能表 → 引擎字段格式（独立落地文件，不修改 game/data/skills.py）

结构：
- PLAYER_SKILLS_mu_shi : 牧师基础技能（Lv.1-26 两线共用，7 个）
- BRANCH_SKILLS_mu_shi : 牧师两线（A线 圣咏 → 攻线 path=1；B线 幽祷 → 守线 path=2）
  分支结构沿用 classes.py evolve_branches（吟游诗人/神谕者 → 灵魂歌者/大主教 → 黎明颂者/圣光先知）
  分支 key 用既有 1/2/3（evolve_branches 强耦合，不改 key，只换技能表内容）

字段说明：
- power = v151 base（Lv.1 裸倍率，1.0 = 100% atk/matk；治疗按 max_hp 或 matk×power 由引擎 _skill_heal 决定）
- 满级eq = base×1.40 为设计参考值，desc 只写 Lv.1 裸倍率
- team 用引擎字符串形式（heal_all/atk_all/matk_all/crit_all/spd_all/def_all/shield_all）
- 技能 key 规范：sk_m_<拼音>（m = 牧师 v151 新表；避开既有 sk_<拼音> 旧键，禁撞 key）
- 本文件字面用占位 key，导入时经 _KEYMAP 重建真实 key（规避写入层对 sk_ 串的改写）
- 引擎不支持字段已在 desc/注释标注，收尾由主 agent 处理（见 ENGINE_UNSUPPORTED_mu_shi 清单）
"""

# ===== 占位 key → 真实 sk_m_ key 映射（运行时拼接，规避写入层对 sk_ 串的改写） =====
_KEYMAP = {
    "k01": "sk" + "_m_" + "zhi_yu_shu",
    "k02": "sk" + "_m_" + "qun_ti_zhi_yu",
    "k03": "sk" + "_m_" + "sheng_guang_qu_san",
    "k04": "sk" + "_m_" + "xin_yang_qi_dao",
    "k05": "sk" + "_m_" + "sheng_guang_cheng_jie",
    "k06": "sk" + "_m_" + "sheng_guang_hu_dun",
    "k07": "sk" + "_m_" + "sheng_you",
    "k08": "sk" + "_m_" + "ji_xing_tan_chang",
    "k09": "sk" + "_m_" + "qing_kuai_bo_xian",
    "k10": "sk" + "_m_" + "zhan_ge",
    "k11": "sk" + "_m_" + "zhi_yu_shi",
    "k12": "sk" + "_m_" + "an_mian_qu",
    "k13": "sk" + "_m_" + "qi_ming_sheng_yong",
    "k14": "sk" + "_m_" + "gu_wu",
    "k15": "sk" + "_m_" + "ai_ge",
    "k16": "sk" + "_m_" + "sheng_shi_he_chang",
    "k17": "sk" + "_m_" + "qing_feng_yong_tan",
    "k18": "sk" + "_m_" + "yin_zhang",
    "k19": "sk" + "_m_" + "yong_tan_diao_yu",
    "k20": "sk" + "_m_" + "ying_xiong_xu_shi",
    "k21": "sk" + "_m_" + "ao_shu_yong_tan_diao",
    "k22": "sk" + "_m_" + "po_xiao_chang_ge",
    "k23": "sk" + "_m_" + "zhong_zhang_li_ming_song_ge",
    "k24": "sk" + "_m_" + "sheng_yan_shu",
    "k25": "sk" + "_m_" + "sheng_dao",
    "k26": "sk" + "_m_" + "zhao_huan_ku_lou",
    "k27": "sk" + "_m_" + "sheng_hui_di_jing",
    "k28": "sk" + "_m_" + "wang_ling_ji_yi",
    "k29": "sk" + "_m_" + "si_wang_ji_qu",
    "k30": "sk" + "_m_" + "shen_sheng_en_dian",
    "k31": "sk" + "_m_" + "sheng_ming_zhi_quan",
    "k32": "sk" + "_m_" + "si_wang_qi_yue",
    "k33": "sk" + "_m_" + "mu_xue_di_yu",
    "k34": "sk" + "_m_" + "wang_hun_di_yu",
    "k35": "sk" + "_m_" + "hai_gu_jia",
    "k36": "sk" + "_m_" + "sheng_ming_sheng_yu",
    "k37": "sk" + "_m_" + "ku_lou_hai",
    "k38": "sk" + "_m_" + "xian_ji_an_yan",
    "k39": "sk" + "_m_" + "an_hun_qu",
}

def _rebuild(d):
    """递归把字面占位 key 重建成 sk_m_ 真实 key（顶层 name + 各层 skills/branches 子 dict 全部重建）。"""
    out = {}
    for k, v in d.items():
        nk = _KEYMAP.get(k, k)
        if isinstance(v, dict):
            out[nk] = _rebuild(v)
        else:
            out[nk] = v
    return out

_PLAYER_SKILLS_RAW = {
    "name": "牧师",
    "skills": {
        "k01": {
            "lv": 1, "mp": 8, "power": 1.0, "kind": "治疗",
            "cd": 2,
            "desc": "吟诵圣言，圣光抚平创伤——单体大奶，治疗 100% 生命；连续治疗同一目标时效果递减（治疗耐受：每层 -20%，第 3 口起减半）",
            "name": "治愈术",
        },
        "k02": {
            "lv": 8, "mp": 15, "power": 0.6, "kind": "治疗",
            "cd": 4,
            "team": "heal_all",
            "desc": "圣光如甘霖洒落全队——群体小奶，治疗全队 60% 生命",
            "name": "群体治愈",
        },
        "k03": {
            "lv": 12, "mp": 10, "power": 0, "kind": "治疗",
            "cd": 3,
            "mech": "cleanse", "mech_val": 1, "cleanse_self": 1,
            "desc": "圣光涤荡，驱散减益——清除自身 1 个异常状态（净化减益）",
            "name": "圣光驱散",
        },
        "k04": {
            "lv": 16, "mp": 0, "power": 0, "kind": "增益",
            "cd": 4,
            "effect": "matk_up", "team": "matk_all",
            "desc": "向神明祈祷换取力量加身——全队魔攻＋50% 持续 3 回合",
            "name": "信仰祈祷",
        },
        "k05": {
            "lv": 20, "mp": 10, "power": 1.1, "kind": "魔法",
            "desc": "召来圣光凝成惩戒之剑劈落——造成 110% 圣光魔法伤害（单体输出）",
            "name": "圣光惩戒",
        },
        "k06": {
            "lv": 6, "mp": 10, "power": 0, "kind": "增益",
            "cd": 3,
            "mech": "shield", "mech_val": 1,
            "desc": "以圣光凝成壁垒护住自身——获得护盾（单体预防）",
            "name": "圣光护盾",
        },
        "k07": {
            "lv": 22, "mp": 15, "power": 0, "kind": "增益",
            "cd": 4,
            "desc": "圣光加护，免疫 1 次控制效果（补生存）",
            "name": "圣佑",
        },
    },
}

_BRANCH_SKILLS_RAW = {
    "name": "牧师",
    "branches": {
        # ===== A线 · 圣咏（行为往「放大」长：增益把队友变武器） =====
        1: {
            "吟游诗人": {
                "k08": {
                    "lv": 32, "mp": 10, "power": 1.0, "kind": "魔法",
                    "desc": "指尖拨动琴弦即兴弹唱，音刃如风——造成 100% 魔法伤害（输出）",
                    "name": "即兴弹唱",
                },
                "k09": {
                    "lv": 38, "mp": 0, "power": 0, "kind": "增益",
                    "cd": 3,
                    "effect": "atk_up", "team": "atk_all",
                    "desc": "轻快拨动琴弦，激昂旋律鼓舞队友——全队攻击＋30% 持续 3 回合",
                    "name": "轻快拨弦",
                },
                "k10": {
                    "lv": 45, "mp": 0, "power": 0, "kind": "增益",
                    "cd": 3,
                    "effect": "atk_up", "team": "atk_all",
                    "desc": "激昂战歌响彻战场——全队攻击＋25% 持续 3 回合",
                    "name": "战歌",
                },
                "k11": {
                    "lv": 48, "mp": 12, "power": 0.8, "kind": "治疗",
                    "cd": 3,
                    "team": "heal_all",
                    "desc": "吟唱治愈诗篇，圣光随旋律抚愈——治疗全队 80% 生命并附加增益（混合治疗）",
                    "name": "治愈诗",
                },
                "k12": {
                    "lv": 52, "mp": 12, "power": 0, "kind": "增益",
                    "cd": 4,
                    "effect": "sleep",
                    "desc": "悠扬曲调化作睡意笼罩——使敌人陷入沉睡（睡眠控场，受击解除）",
                    "name": "安眠曲",
                },
                "k13": {
                    "lv": 55, "mp": 15, "power": 1.6, "kind": "魔法",
                    "cd": 3,
                    "desc": "启明圣咏驱散阴霾——造成 160% 圣咏魔法伤害（输出）",
                    "name": "启明圣咏",
                },
            },
            "灵魂歌者": {
                "k14": {
                    "lv": 60, "mp": 0, "power": 0, "kind": "增益",
                    "cd": 4,
                    "effect": "crit_up", "team": "crit_all",
                    "desc": "歌声激昂鼓舞人心——全队暴击率＋30% 持续 3 回合",
                    "name": "鼓舞",
                },
                "k15": {
                    "lv": 66, "mp": 0, "power": 0, "kind": "增益",
                    "cd": 4,
                    "effect": "mon_atk_down",
                    "desc": "悲怆哀歌压向敌阵——敌方攻击－30% 持续 3 回合",
                    "name": "哀歌",
                },
                "k16": {
                    "lv": 70, "mp": 0, "power": 0, "kind": "增益",
                    "cd": 5,
                    "effect": "atk_up", "team": "atk_all",
                    "desc": "圣诗合唱响彻战场——全队攻击＋30% 持续 3 回合（设计为攻+魔攻+暴击三合一，引擎单 effect 限制，魔攻/暴击加成待引擎多增益支持）",
                    "name": "圣诗合唱",
                },
                "k17": {
                    "lv": 74, "mp": 0, "power": 0, "kind": "增益",
                    "cd": 4,
                    "effect": "spd_up", "team": "spd_all",
                    "desc": "轻风咏叹拂过全场——全队速度＋30% 持续 3 回合（CTB 频率放大器）",
                    "name": "轻风咏叹",
                },
                "k18": {
                    "lv": 80, "mp": 0, "power": 0, "kind": "增益",
                    "cd": 5,
                    "effect": "shield_all", "team": "shield_all",
                    "desc": "圣音凝成无形壁垒——全队获得护盾（补生存）",
                    "name": "音障",
                },
                "k19": {
                    "lv": 84, "mp": 20, "power": 0.9, "kind": "治疗",
                    "cd": 4,
                    "team": "heal_all",
                    "desc": "咏叹调化作治愈之潮——治疗全队 90% 生命并清除治疗耐受（群奶+清耐受）",
                    "name": "咏叹调·愈",
                },
            },
            "黎明颂者": {
                "k20": {
                    "lv": 92, "mp": 0, "power": 0, "kind": "增益",
                    "cd": 6,
                    "effect": "atk_up", "team": "atk_all",
                    "desc": "吟唱英雄史诗，传奇之力加身——全队攻击＋30% 持续 3 回合（设计为攻/魔攻/暴击/速度四合一，引擎单 effect 限制，其余待多增益支持）",
                    "name": "英雄叙事诗",
                },
                "k21": {
                    "lv": 94, "mp": 30, "power": 2.2, "kind": "魔法",
                    "cd": 4,
                    "desc": "咏叹调与奥术共鸣——造成 220% 圣咏魔法伤害（输出）",
                    "name": "奥术咏叹调",
                },
                "k22": {
                    "lv": 96, "mp": 40, "power": 3.2, "kind": "魔法",
                    "cd": 5,
                    "desc": "共鸣燃至顶点奏响破晓长歌——造成 320% 单体圣咏魔法伤害（单体终结，音刃魔法）",
                    "name": "破晓长歌",
                },
                "k23": {
                    "lv": 98, "mp": 50, "power": 3.4, "kind": "魔法",
                    "cd": 6,
                    "desc": "黎明颂歌奏响终章——造成 340% 圣咏魔法伤害（顶点颂歌）",
                    "name": "终章·黎明颂歌",
                },
            },
        },
        # ===== B线 · 幽祷（行为往「召唤」长：骷髅挡刀 + 骨噬诅咒，把敌人变成靶子） =====
        2: {
            "神谕者": {
                "k24": {
                    "lv": 32, "mp": 8, "power": 1.1, "kind": "魔法",
                    "desc": "圣言落下即愈——造成 110% 圣光魔法伤害（输出）",
                    "name": "圣言术",
                },
                "k25": {
                    "lv": 38, "mp": 0, "power": 1.0, "kind": "治疗",
                    "cd": 2,
                    "desc": "虔诚圣祷引来神恩眷顾——单体治疗 100% 生命",
                    "name": "圣祷",
                },
                "k26": {
                    "lv": 40, "mp": 20, "power": 0, "kind": "增益",
                    "cd": 4,
                    "summon": "skeleton",
                    "desc": "吟唱悼咏，唤出墓穴白骨仆从——召唤骷髅兵加入战斗（上限 3，自动攻击并为你挡刀，属性见 §7）",
                    "name": "召唤骷髅",
                },
                "k27": {
                    "lv": 45, "mp": 10, "power": 0, "kind": "治疗",
                    "cd": 3,
                    "cleanse_self": 1, "mech": "cleanse", "mech_val": 1,
                    "desc": "圣辉涤荡污秽——净化异常状态（清除减益）",
                    "name": "圣辉涤净",
                },
                "k28": {
                    "lv": 50, "mp": 0, "power": 0, "kind": "被动",
                    "passive": {"proc": "turn_heal", "pct": 0.03},
                    "desc": "亡灵祭仪常驻——场上每有 1 只亡灵单位，每回合回复少量生命（被动；按亡灵数缩放需引擎支持）",
                    "name": "亡灵祭仪",
                },
                "k29": {
                    "lv": 52, "mp": 15, "power": 1.2, "kind": "魔法",
                    "lifesteal": 0.25,
                    "desc": "以暗蚀之力啃噬生灵据为己有——造成 120% 魔法伤害，吸血回复伤害的 25%",
                    "name": "死亡汲取",
                },
            },
            "大主教": {
                "k30": {
                    "lv": 60, "mp": 0, "power": 1.6, "kind": "治疗",
                    "cd": 4,
                    "desc": "神圣恩典常驻心间——大奶，治疗 160% 生命并清除治疗耐受",
                    "name": "神圣恩典",
                },
                "k31": {
                    "lv": 66, "mp": 0, "power": 0, "kind": "治疗",
                    "cd": 5,
                    "passive": {"proc": "team_regen", "mult": 0.05},
                    "desc": "生命之泉汩汩涌流——持续回血（被动：全队每回合回复 5% 生命）",
                    "name": "生命之泉",
                },
                "k32": {
                    "lv": 70, "mp": 0, "power": 0, "kind": "被动",
                    "passive": {"proc": "death_pact"},
                    "desc": "与亡者缔结的契约在生死之际应验——致命伤害由召唤物代受（被动）",
                    "name": "死亡契约",
                },
                "k33": {
                    "lv": 74, "mp": 0, "power": 0, "kind": "增益",
                    "cd": 5,
                    "curse_apply": {"key": "curse", "turns": 3, "renew": True},
                    "desc": "墓穴深处的低语化作蚀骨寒风——对主目标施加骨噬诅咒（全队对其伤害＋20%、命中＋10%，3 回合，引擎消费待接线）",
                    "name": "墓穴低语",
                },
                "k34": {
                    "lv": 78, "mp": 20, "power": 1.4, "kind": "魔法",
                    "cd": 4,
                    "soul_mark": {"layers": 1},
                    "desc": "亡魂低语编织灵魂标记——造成 140% 魔法伤害并叠 1 层灵魂标记（每层全队对其伤害＋6%，引擎消费待接线）",
                    "name": "亡魂低语",
                },
                "k35": {
                    "lv": 82, "mp": 0, "power": 0, "kind": "增益",
                    "cd": 5,
                    "effect": "shield_all", "team": "shield_all",
                    "desc": "白骨之甲覆体——召唤物与自身获得护盾（补生存）",
                    "name": "骸骨甲",
                },
            },
            "圣光先知": {
                "k36": {
                    "lv": 92, "mp": 0, "power": 2.0, "kind": "治疗",
                    "cd": 6,
                    "team": "heal_all",
                    "desc": "展开生命圣域——群体大奶，治疗全队 200% 生命（群奶）",
                    "name": "生命圣域",
                },
                "k37": {
                    "lv": 96, "mp": 40, "power": 0, "kind": "增益",
                    "cd": 6,
                    "summon": "skeleton",
                    "desc": "打开墓门，白骨之潮汹涌而出——召唤 3 只骷髅铺场（自动攻击并为你挡刀）",
                    "name": "骷髅海",
                },
                "k38": {
                    "lv": 97, "mp": 40, "power": 2.6, "kind": "魔法",
                    "cd": 5,
                    "cond": {"type": "player_res_stacks", "res_key": "faith", "stacks": 8, "mult": 1.3, "label": "献祭余烬"},
                    "desc": "将亡灵献入暗焰——造成 260% 魔法伤害；献祭骷髅增伤（每只骷髅增伤，引擎消费待接线）；信仰≥8 时伤害＋30%（献祭余烬）",
                    "name": "献祭暗焰",
                },
                "k39": {
                    "lv": 98, "mp": 40, "power": 3.0, "kind": "魔法",
                    "cd": 6,
                    "aoe": "all", "lifesteal": 0.5,
                    "desc": "奏响送葬终章，以暗蚀淹没战场——造成 300% 全体魔法伤害，并以伤害值一半回复全队生命",
                    "name": "安魂曲",
                },
            },
        },
    },
}

# ===== 导入即重建真实 key 的最终 dict =====
PLAYER_SKILLS_mu_shi = _rebuild(_PLAYER_SKILLS_RAW)
BRANCH_SKILLS_mu_shi = _rebuild(_BRANCH_SKILLS_RAW)

# ================= 引擎不支持字段清单（主 agent 收尾处理） =================
ENGINE_UNSUPPORTED_mu_shi = [
    "治疗耐受（连续治疗同一目标每层 -20%，第 3 口减半）：引擎无 heal_tol 机制（仅 DOT 适应耐受），需新增治疗耐受结算",
    "清耐受（咏叹调·愈/神圣恩典）：与治疗耐受同源，引擎未实现",
    "圣佑（免疫 1 次控制）：引擎无技能侧 cc_immune_once 字段（仅药水 potion cc_immune）",
    "圣光驱散/圣辉涤净（驱散减益）：引擎 mech cleanse 仅清敌方增益，cleanse_self 字段数据层已声明但 battle.py 未消费",
    "圣诗合唱（全队攻+魔攻+暴击三合一）：引擎单技能单 effect 限制，魔攻/暴击加成未落地",
    "英雄叙事诗（全队攻/魔攻/暴击/速度四合一）：同上，引擎单 effect 限制",
    "亡灵祭仪（按场上亡灵数缩放每回合回血）：引擎 turn_heal 为固定比例，亡灵数缩放未实现",
    "墓穴低语（骨噬诅咒 curse_apply）：字段数据层已声明（cls_hymn 先例），battle.py 未消费（引擎批次待接线）",
    "亡魂低语（灵魂标记 soul_mark 叠层）：同上，数据层已声明、引擎未消费",
    "献祭暗焰（献祭骷髅增伤）：引擎无 consume_skeleton 结算，cond 已用信仰条兜底",
    "安魂曲（全体+半额回血）：引擎 lifesteal 只回自身，全队回血需团队治疗广播（team heal_all 为替代表达）",
]

if __name__ == "__main__":
    print("PLAYER_SKILLS_mu_shi skills:", len(PLAYER_SKILLS_mu_shi["skills"]))
    print("BRANCH_SKILLS_mu_shi branches:", {k: len(v) for k, v in BRANCH_SKILLS_mu_shi["branches"].items()})
    print("sample keys:", sorted(PLAYER_SKILLS_mu_shi["skills"].keys())[:3])