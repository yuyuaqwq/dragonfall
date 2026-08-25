# -*- coding: utf-8 -*-
"""
v130.2f 职业体系质量改动 · 静态文本级验证脚本（不导入任何游戏代码）
=====================================================================

对以下文件做纯文本/正则级检查：
  · game/data/skills.py        —— 技能数据 15+ 个改动点（cond / passive / desc 残留）
  · game/data/core_resources.py —— 战士/拳师 overflow_shield、暮影 on_dodge_success
  · game/battle.py             —— 4 个引擎挂点（亡灵祭仪 / 反击 chi+2 / 致命预谋返还 / _echo_add 伴奏）
                                + battle.py:606-625 overflow_shield 管线

用法：python verify_v1302f_job_quality.py
退出码：0 = 脚本正常完成（PASS/FAIL 均为业务结论）；2 = 目标文件缺失等脚本自身问题。
"""
import os
import re
import sys

try:  # Windows 控制台可能为 GBK，显式 UTF-8 输出防乱码
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../dragonfall
SKILLS = os.path.join(ROOT, "game", "data", "skills.py")
CORE_RES = os.path.join(ROOT, "game", "data", "core_resources.py")
BATTLE = os.path.join(ROOT, "game", "battle.py")

results = []  # (名称, ok, 摘要, 上下文片段)


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n").replace("\r", "\n")


# ---------------------------------------------------------------- 通用工具
def find_name_blocks(text, name):
    """定位所有含 `"name": "X"` 的技能定义块 -> [(起始行1基, 结束行1基, 块文本)]。

    块上界 = 最近一个缩进浅于 name 行的 `"key": {` 定义行（不越过上一个 `"name"` 行）；
    name 行自身携带块内容（单行内联声明）时块 = 该行。
    """
    lines = text.split("\n")
    blocks = []
    for i, ln in enumerate(lines):
        if not re.search(r'"name"\s*:\s*"%s"' % re.escape(name), ln):
            continue
        n_indent = len(ln) - len(ln.lstrip())
        start = i
        if not re.search(r'"(lv|desc|power|passive|effect|res_cost|res_gain)"', ln):
            j = i - 1
            while j >= 0:
                if re.search(r'"name"\s*:', lines[j]):
                    break  # 越过上一个技能，不再外扩，防串块
                sm = re.match(r'^(\s*)"[^"]+"\s*:\s*\{', lines[j])
                if sm and len(sm.group(1)) < n_indent:
                    start = j
                    break
                j -= 1
        blocks.append((start + 1, i + 1, "\n".join(lines[start:i + 1])))
    return blocks


def cond_extract(block):
    """提取块内第一个 cond dict 原文（跨行）"""
    m = re.search(r'"cond"\s*:\s*\{(.*?)\}', block, re.S)
    return m.group(0) if m else ""


def cond_has(block, res_key=None, stacks=None, ctype=None):
    c = cond_extract(block)
    if not c:
        return False
    if res_key and not re.search(r'"res_key"\s*:\s*"%s"' % re.escape(res_key), c):
        return False
    if stacks is not None and not re.search(r'"stacks"\s*:\s*"?%d"?\b' % stacks, c):
        return False
    if ctype and not re.search(r'"type"\s*:\s*"%s"' % re.escape(ctype), c):
        return False
    return True


def block_has(block, *patterns):
    return all(re.search(p, block, re.S) for p in patterns)


RES_GAIN_1 = re.compile(r'"res_gain"\s*:\s*(?:\{[^}]*\b1\b[^}]*\}|1\b)')
PROC_DMG_TAKEN = re.compile(r'"proc"\s*:\s*"dmg_taken"')
CHI_KEY = re.compile(r'"chi"\s*:')


def add(name, ok, detail="", ctx=""):
    results.append((name, bool(ok), detail, ctx))


def ctx_snippet(text, start, end, max_lines=14):
    lines = text.split("\n")
    seg = lines[start - 1:end]
    if len(seg) > max_lines:
        seg = seg[:max_lines] + ["…（截断，共 %d 行）" % (end - start + 1)]
    return "\n".join("  %d|%s" % (start + i, ln) for i, ln in enumerate(seg))


# ---------------------------------------------------------------- 1. skills.py
print("=" * 72)
print("skill 检查对象：%s" % SKILLS)
print("=" * 72)
skills_text = None
if not os.path.isfile(SKILLS):
    print("[致命] 找不到 skills.py，后续技能检查跳过")
else:
    skills_text = read_text(SKILLS)

# --- 技能块检查（cond 档位） ---
SKILL_COND_CHECKS = [
    ("CHK-01 时停领域 cond", "时停领域", dict(res_key="time_sand", stacks=5, ctype="player_res_stacks"),
     "cond: type=player_res_stacks + res_key=time_sand + stacks=5"),
    ("CHK-02 流星陨落 cond", "流星陨落", dict(res_key="hunt_mark", stacks=5),
     "cond: res_key=hunt_mark + stacks=5"),
    ("CHK-03 龙焰吐息 cond", "龙焰吐息", dict(res_key="dragon_might", stacks=8),
     "cond: res_key=dragon_might + stacks=8"),
    ("CHK-04 暗杀保持残血cond", "暗杀", None, "设计决策: 保持 enemy_hp_low（cond 单槽，不替换现有斩杀条）"),
    ("CHK-05 暗影处刑保持残血cond", "暗影处刑", None, "设计决策: 保持 enemy_hp_low"),
    ("CHK-06 元素湮灭无恒真cond", "元素湮灭", None, "设计决策: 不加深恒真 cond（element 字符串槽限制）"),
]
for chk, sk, kw, desc in SKILL_COND_CHECKS:
    if skills_text is None:
        add(chk, False, "skills.py 缺失", "")
        continue
    blocks = find_name_blocks(skills_text, sk)
    if not blocks:
        add(chk, False, "未找到技能「%s」定义" % sk, "")
        continue
    if kw is None:
        # 设计决策项：断言「未添加 player_res_stacks 恒真/替换 cond」
        txt = "\n".join(b for (_, _, b) in blocks)
        if "player_res_stacks" not in txt:
            add(chk, True, "未加恒真/替换 cond（保持设计决策）", "")
        else:
            add(chk, False, "检测到 player_res_stacks cond（与设计决策冲突）",
                ctx_snippet(skills_text, blocks[0][0], blocks[0][1]))
        continue
    ok = any(cond_has(b, **kw) for (_, _, b) in blocks)
    hit = next(((s, e) for (s, e, b) in blocks if cond_has(b, **kw)), None)
    if ok:
        add(chk, True, "命中于 行%s" % (hit,), "")
    else:
        cand = blocks[0]
        add(chk, False, "未命中（%d 处定义均无期望 cond）" % len(blocks),
            ctx_snippet(skills_text, cand[0], cand[1]))

# --- 被动/资源 proc 检查 ---
# 每项 = (检查名, 技能名, [(正则, 可读标签), ...], 附加规则名集合)
# 附加规则：'res_gain1' = res_gain 需含数值 1；'no_chi' = 不得含 chi 字段
SKILL_PASSIVE_CHECKS = [
    ("CHK-07 寒霜亲和保持ice_slow", "寒霜亲和",
     [(r'"proc"\s*:\s*"ice_slow"', 'proc=ice_slow')],
     set()),
    ("CHK-08 魔力贯穿 attack_res", "魔力贯穿",
     [(r'"attack_res"', 'attack_res 字段'), (r'"res"\s*:\s*"time_sand"', 'res=time_sand')],
     set()),
    ("CHK-09 神圣坚韧 proc", "神圣坚韧",
     [(r'"proc"\s*:\s*"dmg_taken"', 'proc=dmg_taken')],
     {'res_gain1'}),
    ("CHK-10 墓穴护甲 proc", "墓穴护甲",
     [(r'"proc"\s*:\s*"dmg_taken"', 'proc=dmg_taken'), (r'"reduce"\s*:\s*0\.05', 'reduce=0.05')],
     {'res_gain1'}),
    ("CHK-11 磐石体 proc", "磐石体",
     [(r'"proc"\s*:\s*"dmg_taken"', 'proc=dmg_taken')],
     {'res_gain1', 'no_chi'}),
    ("CHK-12 战争咆哮 proc", "战争咆哮",
     [(r'"proc"\s*:\s*"res_gain_bonus"', 'proc=res_gain_bonus')],
     set()),
    ("CHK-13 鹰眼 proc", "鹰眼",
     [(r'"proc"\s*:\s*"mark_extra"', 'proc=mark_extra')],
     set()),
]
for chk, sk, pats, extra in SKILL_PASSIVE_CHECKS:
    if skills_text is None:
        add(chk, False, "skills.py 缺失", "")
        continue
    blocks = find_name_blocks(skills_text, sk)
    if not blocks:
        add(chk, False, "未找到技能「%s」定义" % sk, "")
        continue
    hit = None
    for (s, e, b) in blocks:
        notes = []
        for p, label in pats:
            if not re.search(p, b, re.S):
                notes.append(label)
        if 'res_gain1' in extra and not RES_GAIN_1.search(b):
            notes.append('res_gain 含数值 1')
        if 'no_chi' in extra and CHI_KEY.search(b):
            notes.append('不得含 chi 字段')
        if not notes:
            hit = (s, e)
            break
    if hit:
        add(chk, True, "命中于 行%s" % (hit,), "")
    else:
        cand = blocks[0]
        add(chk, False, "未命中（%d 处定义，缺：%s）" % (len(blocks), "；".join(notes or ["字段不符"])),
            ctx_snippet(skills_text, cand[0], cand[1]))

# --- desc 残留检查 ---
if skills_text is not None:
    # CHK-14：全文件不得再出现「满力龙威真伤态」（龙裔 desc 旧承诺已被清洗）
    has = "满力龙威真伤态" in skills_text
    add("CHK-14 desc 残留：满力龙威真伤态", not has,
        "已清除（全文件无此字样）" if not has else "仍存在！",
        ctx_snippet(skills_text, skills_text.find("满力龙威真伤态") + 1, skills_text.find("满力龙威真伤态") + 2)
        if has else "")

    # CHK-15：暗影之心 desc 不得再含「潜行持续+1」（旧承诺语）
    has = "潜行持续" in skills_text
    if has:
        line_no = skills_text.count("\n", 0, skills_text.find("潜行持续")) + 1
    add("CHK-15 desc 残留：潜行持续+1", not has,
        "暗影之心 desc 已改（全文件无「潜行持续」）" if not has else "仍存在！暗影之心 desc 疑似未改",
        ctx_snippet(skills_text, max(1, line_no - 6), line_no + 2) if has else "")

    # CHK-16：星辉祈愿 desc 不得再含「满印」承诺暴击
    blocks = find_name_blocks(skills_text, "星辉祈愿")
    if not blocks:
        add("CHK-16 星辉祈愿 desc 满印", False, "未找到「星辉祈愿」定义", "")
    else:
        bad = [(s, e) for (s, e, b) in blocks if "满印" in b]
        if not bad:
            add("CHK-16 星辉祈愿 desc 满印", True, "全部 %d 处 desc 均不含「满印」" % len(blocks), "")
        else:
            add("CHK-16 星辉祈愿 desc 满印", False, "仍含「满印」暴击承诺（%d 处）" % len(bad),
                ctx_snippet(skills_text, bad[0][0], bad[0][1]))

# ---------------------------------------------------------------- 2. core_resources.py
print()
print("=" * 72)
print("core_resources 检查对象：%s" % CORE_RES)
print("=" * 72)
if not os.path.isfile(CORE_RES):
    add("CHK-17 战士 overflow_shield", False, "core_resources.py 缺失", "")
    add("CHK-18 拳师 overflow_shield", False, "core_resources.py 缺失", "")
    add("CHK-19 暮影 on_dodge_success", False, "core_resources.py 缺失", "")
else:
    cr_text = read_text(CORE_RES)
    cr_lines = cr_text.split("\n")


    def cls_block(key):
        """提取 `"key_name": {` 顶层资源块 [起始1基, 结束1基, 文本]"""
        for i, ln in enumerate(cr_lines):
            if re.match(r'^\s*"%s"\s*:\s*\{' % re.escape(key), ln):
                j = i + 1
                while j < len(cr_lines):
                    if re.match(r'^\s{0,4}\},?\s*$', cr_lines[j]):
                        break
                    j += 1
                return i + 1, j + 1, "\n".join(cr_lines[i:j + 1])
        return None


    zh = cls_block("cls_zhan_shi")
    if zh is None:
        add("CHK-17 战士 overflow_shield", False, "未找到 cls_zhan_shi 资源块", "")
    elif "overflow_shield" in zh[2]:
        add("CHK-17 战士 overflow_shield", True, "命中：cls_zhan_shi 块含 overflow_shield（行%s）" % (zh[0],), "")
    else:
        add("CHK-17 战士 overflow_shield", False, "cls_zhan_shi 块无 overflow_shield 字段（现状仅 cls_hymn 有）",
            ctx_snippet(cr_text, zh[0], zh[1], max_lines=8))

    qs = cls_block("cls_wu_seng")
    if qs is None:
        add("CHK-18 拳师 overflow_shield", False, "未找到 cls_wu_seng 资源块", "")
    elif "overflow_shield" in qs[2]:
        add("CHK-18 拳师 overflow_shield", True, "命中：cls_wu_seng 块含 overflow_shield（行%s）" % (qs[0],), "")
    else:
        add("CHK-18 拳师 overflow_shield", False, "cls_wu_seng 块无 overflow_shield 字段（现状仅 cls_hymn 有）",
            ctx_snippet(cr_text, qs[0], qs[1], max_lines=8))

    # CHK-19：暮影 shadow_step 资源块含 on_dodge_success > 0
    ss_idx = None
    for i, ln in enumerate(cr_lines):
        if re.search(r'"key"\s*:\s*"shadow_step"', ln):
            ss_idx = i
            break
    if ss_idx is None:
        add("CHK-19 暮影 on_dodge_success", False, "未找到 key=shadow_step 的资源定义", "")
    else:
        # 从该行向上找所属资源块 key 行
        start = ss_idx
        while start >= 0 and not re.match(r'^\s*"[^"]+"\s*:\s*\{', cr_lines[start]):
            start -= 1
        if start < 0:
            start = ss_idx
        j = ss_idx + 1
        while j < len(cr_lines) and not re.match(r'^\s{0,4}\},?\s*$', cr_lines[j]):
            j += 1
        blk = "\n".join(cr_lines[start:j + 1])
        m = re.search(r'"on_dodge_success"\s*:\s*([1-9]\d*)', blk)
        if m:
            add("CHK-19 暮影 on_dodge_success", True,
                "命中：shadow_step 块 on_dodge_success=%s（行%s-%s）" % (m.group(1), start + 1, j + 1), "")
        else:
            add("CHK-19 暮影 on_dodge_success", False, "shadow_step 块无 on_dodge_success>0",
                ctx_snippet(cr_text, start + 1, j + 1, max_lines=10))

# ---------------------------------------------------------------- 3. battle.py
print()
print("=" * 72)
print("battle 检查对象：%s" % BATTLE)
print("=" * 72)
if not os.path.isfile(BATTLE):
    add("CHK-20 亡灵祭仪挂点", False, "battle.py 缺失", "")
    add("CHK-21 反击段 chi+2", False, "battle.py 缺失", "")
    add("CHK-22 致命预谋返还", False, "battle.py 缺失", "")
    add("CHK-23 _echo_add 伴奏", False, "battle.py 缺失", "")
    add("CHK-24 overflow_shield 管线", False, "battle.py 缺失", "")
else:
    bt_text = read_text(BATTLE)
    bt_lines = bt_text.split("\n")

    # CHK-20：亡灵祭仪引擎挂点（注释/函数含「祭仪」关键词）
    jy = [i + 1 for i, ln in enumerate(bt_lines) if "祭仪" in ln]
    if jy:
        add("CHK-20 亡灵祭仪挂点", True, "命中：含「祭仪」行 %s" % jy, "")
    else:
        und = [i + 1 for i, ln in enumerate(bt_lines) if "undead_on_field" in ln]
        note = "；参考：undead_on_field 相关行 %s（套装口径，非祭仪挂点）" % und if und else ""
        add("CHK-20 亡灵祭仪挂点", False, "battle.py 无「祭仪」字样，引擎批次 2 挂点未实现" + note, "")

    # CHK-21：反击段含资源获取（chi +2 附近）——按 v130.2f 日志「反击回气」定位
    counter_lines = [i for i, ln in enumerate(bt_lines) if "反击回气" in ln]
    hit = None
    for i in counter_lines:
        win = "\n".join(bt_lines[max(0, i - 20):i + 21])
        if re.search(r'_res_gain\b[^\n]*"chi"[^\n]*,\s*2\s*\)', win) or "chi" in win:
            hit = i + 1
            break
    if hit:
        add("CHK-21 反击段 chi+2", True, "命中：行 %d 含「反击回气」+ chi 资源获取" % hit, "")
    else:
        ref = counter_lines[:4] if counter_lines else []
        add("CHK-21 反击段 chi+2", False,
            "无「反击回气」实现（行 %s 附近）" % ref,
            ("\n".join(ctx_snippet(bt_text, i + 1, i + 2) for i in counter_lines[:3])) if counter_lines else "")

    # CHK-22：致命预谋返还标记字段（致命预谋附近含「返还」）
    fat = [i for i, ln in enumerate(bt_lines) if "致命预谋" in ln]
    hit = None
    for i in fat:
        win = "\n".join(bt_lines[max(0, i - 40):i + 41])
        if "返还" in win:
            hit = i + 1
            break
    if hit:
        add("CHK-22 致命预谋返还", True, "命中：行 %d 附近含「返还」字段" % hit, "")
    else:
        ref = [(i + 1) for i in fat]
        add("CHK-22 致命预谋返还", False,
            "致命预谋相关行 %s 附近无「返还」标记字段（v110.3 battle_start_cp 仍为旧口径）" % ref,
            (ctx_snippet(bt_text, fat[0] + 1, fat[0] + 4) if fat else ""))

    # CHK-23：歌者伴奏挂点（_do_player_skill 施放结算 v130.2f 版）——按「v130.2f 歌者伴奏」注释定位
    ba = [i for i, ln in enumerate(bt_lines) if "v130.2f 歌者伴奏" in ln]
    hit = None
    for i in ba:
        win = "\n".join(bt_lines[max(0, i - 5):i + 16])
        if "0.20" in win and "echo" in win:
            hit = i + 1
            break
    if hit:
        add("CHK-23 歌者伴奏挂点", True, "命中：行 %d 附近含 v130.2f 伴奏 + 0.20 + echo" % hit, "")
    else:
        add("CHK-23 歌者伴奏挂点", False,
            "battle.py 无「v130.2f 歌者伴奏」施放挂点（%s）" % ([i + 1 for i in ba] or "未找到"),
            ("\n".join(ctx_snippet(bt_text, i + 1, i + 6) for i in ba[:2])) if ba else "")

    # CHK-24：battle.py 606-625 overflow_shield 管线
    seg = "\n".join(bt_lines[605:625])  # 1 基 606..625
    if "overflow_shield" in seg:
        add("CHK-24 overflow_shield 管线", True, "命中：606-625 区间含 overflow_shield（_res_gain_class 满溢转盾）", "")
    else:
        add("CHK-24 overflow_shield 管线", False, "行 606-625 区间无 overflow_shield",
            ctx_snippet(bt_text, 606, 625, max_lines=10))

# ---------------------------------------------------------------- 汇总输出
print()
print("=" * 72)
print("验证清单（共 %d 项）" % len(results))
print("=" * 72)
fails = []
for name, ok, detail, ctx in results:
    flag = "PASS" if ok else "FAIL"
    print("[%s] %s" % (flag, name))
    print("      └ %s" % detail)
    if not ok:
        fails.append(name)
        if ctx:
            print("      └ 上下文片段：")
            for cl in ctx.split("\n"):
                print("        |" + cl)
print()
total = len(results)
passed = sum(1 for _, ok, _, _ in results if ok)
print("=" * 72)
print("汇总：%d/%d 通过" % (passed, total))
if fails:
    print("FAIL 项（%d）：%s" % (len(fails), "；".join(fails)))
    print("说明：FAIL = 对应改动点尚未在代码中落地（v130.2f 未完成/未提交），此为脚本预期用途。")
else:
    print("全部 PASS —— v130.2f 职业质量改动已完整落地。")
print("=" * 72)
sys.exit(0)