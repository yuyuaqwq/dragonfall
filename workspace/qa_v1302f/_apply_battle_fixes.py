# -*- coding: utf-8 -*-
import io
p = r"game/battle.py"
s = io.open(p, encoding="utf-8", newline="").read()
NL = "\r\n"

def rep(tag, old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, "ANCHOR %s count=%d (want %d)" % (tag, n, count)
    s = s.replace(old, new, count)
    print("OK %s" % tag)

# ---------- 任务5b：_player_skill 潜行消费块 置标记 ----------
rep("T5b_skill_stealth_flag",
NL.join([
"        _stealth_hit = False",
'        if self.p_buffs.get("stealth"):',
"            is_crit = True",
"            _stealth_hit = True",
'            del self.p_buffs["stealth"]',
'            logs.append("🌙 潜行生效！本次攻击必定暴击！")',
]),
NL.join([
"        _stealth_hit = False",
"        self._stealth_atk = False  # v130.2f2（T11 P2）：潜行出手标记每次出手前复位",
'        if self.p_buffs.get("stealth"):',
"            is_crit = True",
"            _stealth_hit = True",
"            self._stealth_atk = True  # 潜行出手标记——供 _on_crit_resource（潜行出手额外+1 影步）与暗影之舞暴伤被动读取",
'            del self.p_buffs["stealth"]',
'            logs.append("🌙 潜行生效！本次攻击必定暴击！")',
]))

# ---------- 任务5：_on_crit_resource 读标记 ----------
rep("T5c_on_crit_read_flag",
NL.join([
'        if rd.get("on_crit"):',
'            gain = int(rd["on_crit"])',
'            if self.p_buffs.get("stealth"):',
'                gain += int(SHADOW_STEP_CFG.get("stealth_extra", 1) or 0)',
]),
NL.join([
'        if rd.get("on_crit"):',
'            gain = int(rd["on_crit"])',
"            # v130.2f2（T11 P2）：潜行已于出手处置 True 标记（消费点 3030-3034 先删 buff）——",
"            # 此处读标记而非二次查 buff，「潜行出手额外 +1 影步」不再空转",
'            if self.p_buffs.get("stealth") or getattr(self, "_stealth_atk", False):',
'                gain += int(SHADOW_STEP_CFG.get("stealth_extra", 1) or 0)',
]))

# ---------- 任务5（同根因）：暗影之舞 stealth_crit_dmg 读标记 ----------
rep("T5d_shadow_dance_flag",
NL.join(['            elif _sstat == "stealth_crit_dmg" and self.p_buffs.get("stealth"):']),
NL.join(['            elif _sstat == "stealth_crit_dmg" and (self.p_buffs.get("stealth") or getattr(self, "_stealth_atk", False)):']))

# ---------- 任务2：_resource_on_skill 被动渠道 ----------
rep("T2_skill_passive",
NL.join([
"        on_skill_extra = 0",
'        if cls in HUNT_MARK_ON_LAND_HIT and rd.get("on_hit"):',
'            on_skill_extra = int(rd["on_hit"])',
"        if gain or on_skill_extra:",
]),
NL.join([
"        on_skill_extra = 0",
'        if cls in HUNT_MARK_ON_LAND_HIT and rd.get("on_hit"):',
'            on_skill_extra = int(rd["on_hit"])',
"        # v130.2f2（T7 P1-2/P1-3）：被动加成并入技能命中渠道——战争咆哮 res_gain_bonus",
"        # 「怒气全渠道+1」/ 魔力贯穿 attack_res「施法命中+1沙」在施法命中时也生效。",
"        # 叠加语义：与技能自带 res_gain 累加（同一获取源不重复）；终结技早返回（2311 附近）在前，",
"        # 有 res_cost 且无 res_gain 的终结技依旧不获取，渠道扩展不破坏该语义。",
"        _pm_skill = self._passive_map(player)",
"        _skill_gain_log = []",
'        for _pn, _ps in _pm_skill["proc"].get("res_gain_bonus", []):',
'            if k in ("rage", "chi", "cp", "faith"):',
"                gain += 1",
'                _skill_gain_log.append(f"{_pn}+1")',
'        for _pn, _ps in _pm_skill["proc"].get("attack_res", []):',
'            if k == _ps.get("res", "") and _ps.get("gain"):',
'                gain += int(_ps.get("gain", 0))',
'                _skill_gain_log.append(f"{_pn}+{int(_ps.get(\'gain\', 0))}")',
"        if _skill_gain_log and logs is not None:",
'            _rd_n = (E.core_resource_def_by_key(k) or E.core_resource_def(cls) or {}).get("name", k)',
'            logs.append(f"⚡ 技能命中：{\' / \'.join(_skill_gain_log)}（{_rd_n}）")',
"        if gain or on_skill_extra:",
]))

# ---------- 任务3：_apply_mech_effect mark_extra ----------
rep("T3_mark_extra",
NL.join([
"        from .core.battle_mech import MECH_EFFECTS",
"        handler = MECH_EFFECTS.get(mech)",
"        if handler:",
"            handler(self, mval, p_mech, total, logs, skill_name, is_crit, info)",
]),
NL.join([
"        from .core.battle_mech import MECH_EFFECTS",
"        handler = MECH_EFFECTS.get(mech)",
"        if handler:",
"            handler(self, mval, p_mech, total, logs, skill_name, is_crit, info)",
"        # v130.2f2（T7 P1-1）：鹰眼 mark_extra 在游侠标记路径（mech=mark：林语印记/猎杀标记类技能）",
"        # 也独立 roll——与法师元素印记路径（_player_skill 3388-3390）同语义：每个被动独立 chance，",
"        # 额外层经同源 handler 叠加进目标 debuffs.mark（cap 5）。此前消费点只在 element 印记分支，",
"        # 全库 element 技能仅法师系持有，游侠/星语猎手标记被动（追踪印记 30%/鹰眼 15%）零触发=死被动。",
'        if mech == "mark":',
'            _pl_mark = getattr(self, "_last_player", None) or self.player or {}',
"            _extra_mark = 0",
"            _trig_mark = []",
'            for _pn_m, _ps_m in self._passive_map(_pl_mark)["proc"].get("mark_extra", []):',
'                if random.random() < float(_ps_m.get("chance", 0.15) or 0.15):',
"                    _extra_mark += 1",
"                    _trig_mark.append(_pn_m)",
"            if _extra_mark > 0:",
'                _mh_mark = MECH_EFFECTS.get("mark")',
"                if _mh_mark:",
"                    _mh_mark(self, _extra_mark, p_mech, total, logs, skill_name, is_crit, info)",
'                logs.append(f"🎯 {\'/\'.join(_trig_mark)}：额外标记 +{_extra_mark} 层！（与追踪印记叠加）")',
]))

# ---------- 任务4a：__init__ 新增字段 ----------
rep("T4a_init_fields",
NL.join([
'        self.p_eff: dict = {}              # v130.2 物品效果持久数据（resource_amp / mana_cost_down / buff_phys_next / phys_up / battle_start 预充标记），随战斗序列化',
]),
NL.join([
'        self.p_eff: dict = {}              # v130.2 物品效果持久数据（resource_amp / mana_cost_down / buff_phys_next / phys_up / battle_start 预充标记），随战斗序列化',
"        # v130.2f2：满溢转盾冷却（每回合限 1 次转盾，回合末 _end_round 重置，随战斗序列化）",
"        #            + 潜行出手标记（本次出手是否潜行，供暴击结算读；出手时置位/复位，瞬时态不序列化）",
"        self._overflow_shield_cd: bool = False",
"        self._stealth_atk: bool = False",
]))

# ---------- 任务4a：to_state ----------
rep("T4a_to_state",
NL.join([
'            "tailwind_prev_energy": getattr(self, "_tailwind_prev_energy", None),  # v130.2d 疾风余韵跨回合状态',
"        }",
]),
NL.join([
'            "tailwind_prev_energy": getattr(self, "_tailwind_prev_energy", None),  # v130.2d 疾风余韵跨回合状态',
'            "overflow_shield_cd": getattr(self, "_overflow_shield_cd", False),  # v130.2f2 满溢转盾冷却（断线恢复不重置冷却）',
"        }",
]))

# ---------- 任务4a：from_state ----------
rep("T4a_from_state",
NL.join([
'        b._tailwind_prev_energy = st.get("tailwind_prev_energy")  # v130.2d 疾风余韵跨回合状态',
]),
NL.join([
'        b._tailwind_prev_energy = st.get("tailwind_prev_energy")  # v130.2d 疾风余韵跨回合状态',
'        b._overflow_shield_cd = bool(st.get("overflow_shield_cd", False))  # v130.2f2 满溢转盾冷却随战斗序列化',
]))

# ---------- 任务4a/4b：_res_gain_class 冷却+泛化 key+日志 ----------
rep("T4_res_gain_class",
NL.join([
"    def _res_gain_class(self, cls: str, k: str, amount: int) -> int:",
'        """类主资源增加（带上限 + 隐藏线满溢转盾）。v130.2：悼咏 canticle overflow_shield=True',
"        时满 10 后每溢出 1 点转自身 5 点护盾（冷却 1 回合，priest.md §5.2）。\"\"\"",
"        rd = E.core_resource_def(cls)",
"        if not rd:",
"            return self.resources.get(k, 0)",
"        # v130.2 R1：上限口径与 _res_max 统一（词条 max_bonus + 套装 res_max）；无 player 参数取本场玩家；",
"        # self.player 为 None（from_state 恢复等）时按空 dict 守卫，套装/词条加成归 0",
"        _pl = self.player or {}",
"        mx = int(rd.get(\"max\", 99) or 99) + self._res_affix_max_bonus(_pl, k) + self._set_res_max_bonus(_pl, k)",
"        cur = int(self.resources.get(k, 0) or 0)",
"        amount = int(amount or 0)",
"        overflow = 0",
"        if amount > 0 and cur + amount > mx:",
"            overflow = cur + amount - mx",
"        new = min(mx, cur + amount)",
'        if rd.get("overflow_shield") and overflow > 0:',
"            shield = int(overflow * 5)",
'            self._add_shield("canticle_overflow", shield, 1)',
"        self.resources[k] = new",
"        return new",
]),
NL.join([
"    def _res_gain_class(self, cls: str, k: str, amount: int, logs: list | None = None) -> int:",
'        """类主资源增加（带上限 + 隐藏线满溢转盾）。v130.2：悼咏 canticle overflow_shield=True',
"        时满 10 后每溢出 1 点转自身 5 点护盾（冷却 1 回合，priest.md §5.2）。",
"        v130.2f2（T6 P1-1/P1-3）：①冷却 1 回合落地——转盾后置位 _overflow_shield_cd，",
"        本回合内不再转盾（多段受击不再段段白嫖），回合末 _end_round 重置；",
"        ②渠道统一——词条/套装/药水（_res_gain 主资源路由）与受击被动 res_gain（4848 改接）",
"        满溢也走本函数，满资源不再静默蒸发；③转盾 key 泛化（原硬编码 canticle_overflow，",
"        战士/拳师转盾也顶悼咏键名，现统一 overflow_shield 同源叠加）。\"\"\"",
"        rd = E.core_resource_def(cls)",
"        if not rd:",
"            return self.resources.get(k, 0)",
"        # v130.2 R1：上限口径与 _res_max 统一（词条 max_bonus + 套装 res_max）；无 player 参数取本场玩家；",
"        # self.player 为 None（from_state 恢复等）时按空 dict 守卫，套装/词条加成归 0",
"        _pl = self.player or {}",
"        mx = int(rd.get(\"max\", 99) or 99) + self._res_affix_max_bonus(_pl, k) + self._set_res_max_bonus(_pl, k)",
"        cur = int(self.resources.get(k, 0) or 0)",
"        amount = int(amount or 0)",
"        overflow = 0",
"        if amount > 0 and cur + amount > mx:",
"            overflow = cur + amount - mx",
"        new = min(mx, cur + amount)",
'        if rd.get("overflow_shield") and overflow > 0:',
'            if not getattr(self, "_overflow_shield_cd", False):',
"                shield = int(overflow * 5)",
'                self._add_shield("overflow_shield", shield, 1)',
'                self._overflow_shield_cd = True',
"                if logs is not None:",
'                    logs.append(f"🛡️ 满溢转化：{rd.get(\'name\', k)}溢出 {overflow} 点 → 护盾 +{shield}（每回合限 1 次转盾）")',
"            elif logs is not None:",
'                logs.append(f"🛡️ 满溢转化：{rd.get(\'name\', k)}溢出 {overflow} 点（本回合已转盾，冷却中）")',
"        self.resources[k] = new",
"        return new",
]))

# ---------- 任务4b：_res_gain 类主资源路由 ----------
rep("T4b_res_gain_route",
NL.join([
'        if key == "echo":',
"            # v130.2 收尾：echo 驻留叠层存 mech_stacks（战斗内不清零），不走 resources 影子槽",
"            return self._echo_add(player, logs if logs is not None else [], int(amount or 0))",
"        if E.core_resource_def_by_key(key):",
]),
NL.join([
'        if key == "echo":',
"            # v130.2 收尾：echo 驻留叠层存 mech_stacks（战斗内不清零），不走 resources 影子槽",
"            return self._echo_add(player, logs if logs is not None else [], int(amount or 0))",
"        # v130.2f2（T6 P1-2/P1-3）：渠道统一——词条/套装/药水/战前预充等渠道的类主资源增益",
"        # 统一走 _res_gain_class：上限含词条/套装加成（不再按裸 rd.max 封顶被回退），",
"        # 且满溢量按 overflow_shield 转盾（满资源不再静默蒸发）。副资源（resonance/echo 等）",
"        # 与键≠类主资源的情况仍走下方按 key 注册路径，行为不变。",
'        _crd_route = E.core_resource_def(player.get("class_name", ""))',
'        if _crd_route and key == _crd_route.get("key"):',
'            return self._res_gain_class(player.get("class_name", ""), key, int(amount or 0), logs)',
"        if E.core_resource_def_by_key(key):",
]))

# ---------- 任务4b：受击被动 res_gain 改接 ----------
rep("T4b_dmg_taken_resgain",
NL.join([
'                _rg = int(ps.get("res_gain") or 0)',
"                if _rg > 0:",
'                    _rcls = player.get("class_name", "")',
"                    _rdef = E.core_resource_def(_rcls)",
"                    if _rdef:",
'                        _rk = _rdef["key"]',
"                        self.resources[_rk] = E.core_resource_gain(_rcls, self.resources, _rg)",
'                        logs.append(f"⚡ {ps_name}：受击获取 {_rg} 点资源（{_rk} {self.resources[_rk]}）")',
]),
NL.join([
'                _rg = int(ps.get("res_gain") or 0)',
"                if _rg > 0:",
'                    _rcls = player.get("class_name", "")',
"                    _rdef = E.core_resource_def(_rcls)",
"                    if _rdef:",
'                        _rk = _rdef["key"]',
"                        # v130.2f2（T7 P2-1）：受击被动 res_gain（磐石体/墓穴护甲/守护姿态）改走",
"                        # _res_gain_class——与 on_hit 基础受击渠道同口径：上限含词条/套装加成，",
"                        # 满资源溢出转盾（不再直调 E.core_resource_gain 平顶蒸发）；满值时",
"                        # 真实增量判定防误报（转盾由 _res_gain_class 日志单独反馈）。",
"                        _rg_before = int(self.resources.get(_rk, 0) or 0)",
"                        self.resources[_rk] = self._res_gain_class(_rcls, _rk, _rg)",
"                        if int(self.resources.get(_rk, 0) or 0) > _rg_before:",
'                            logs.append(f"⚡ {ps_name}：受击获取 {_rg} 点资源（{_rk} {self.resources[_rk]}）")',
]))

# ---------- 任务4a：_end_round 冷却重置 ----------
rep("T4a_end_round_reset",
NL.join([
'        self._tailwind_prev_energy = int(self.resources.get("energy", 0) or 0)',
]),
NL.join([
'        self._tailwind_prev_energy = int(self.resources.get("energy", 0) or 0)',
"        # v130.2f2 满溢转盾冷却：回合末重置（本回合已转盾 → 下回合可再转，「冷却 1 回合」语义）",
"        self._overflow_shield_cd = False",
]))

io.open(p, "w", encoding="utf-8", newline="").write(s)
print("ALL PATCHES APPLIED")