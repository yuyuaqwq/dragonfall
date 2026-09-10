/* app.js —— 域列表 / 技能列表 / 表单 / 原始 JSON / 差异预览 / 保存（原生 JS，零依赖） */
'use strict';

const D = {
  domain: 'skills',
  list: null,
  info: {},
  key: null,
  meta: null,
  original: null,
  current: null,
  schema: null,
  filter: '',
  dirty: false,
  formHandle: null,
};

const $ = (id) => document.getElementById(id);

async function api(url, opts) {
  const r = await fetch(url, opts);
  let body = null;
  try { body = await r.json(); } catch (e) { body = { ok: false, message: '响应不是 JSON' }; }
  return { status: r.status, body: body };
}

function setStatus(msg) { $('statusbar').textContent = msg; }
function deepCopy(o) { return JSON.parse(JSON.stringify(o)); }

/* --------------------------------------------------------------- diff */
function diff(before, after, path) {
  path = path || '';
  const out = [];
  if (Array.isArray(before) && Array.isArray(after)) {
    if (before.length !== after.length) return [{ path: path, before: before, after: after }];
    before.forEach((b, i) => { out.push(...diff(b, after[i], path + '[' + i + ']')); });
    return out;
  }
  if (before && after && typeof before === 'object' && typeof after === 'object') {
    const keys = Array.from(new Set([...Object.keys(before), ...Object.keys(after)]));
    keys.sort();
    keys.forEach((k) => {
      const sub = path ? path + '.' + k : k;
      if (!(k in before)) out.push({ path: sub, before: undefined, after: after[k] });
      else if (!(k in after)) out.push({ path: sub, before: before[k], after: undefined });
      else out.push(...diff(before[k], after[k], sub));
    });
    return out;
  }
  if (before !== after) out.push({ path: path, before: before, after: after });
  return out;
}
function fmt(v) {
  if (v === undefined) return '（不存在）';
  return typeof v === 'string' ? JSON.stringify(v) : JSON.stringify(v);
}

/* ------------------------------------------------------------ boot */
async function boot() {
  setStatus('加载域列表…');
  const res = await api('/api/domains');
  if (!res.body.ok) { setStatus('❌ /api/domains 失败: ' + res.body.message); return; }
  const info = res.body;
  D.info = info;
  const box = $('domains');
  box.innerHTML = '';
  info.domains.forEach((d) => {
    const b = document.createElement('button');
    b.textContent = d.label;
    b.className = d.id === D.domain ? 'active' : '';
    b.addEventListener('click', () => { if (d.id !== D.domain) { D.domain = d.id; boot(); } });
    box.appendChild(b);
  });
  const badge = $('badge-source');
  badge.textContent = info.source === 'workcopy' ? '数据来源：工作副本' : '数据来源：py 源文件（只读）';
  badge.className = 'badge ' + (info.source === 'workcopy' ? 'workcopy' : 'source');
  $('notice').textContent = '⚠ ' + info.note +
    '　·　校验器: ' + info.validator + '　·　副本路径: ' + info.copy_path;
  await loadList();
  // 深链：index.html#<urlencoded key> 直接打开某条技能
  const h = decodeURIComponent((location.hash || '').replace(/^#/, ''));
  if (h && h.indexOf('~') >= 0) await selectEntry(h);
}

window.addEventListener('DOMContentLoaded', () => {
  bindUi();
  boot().catch((e) => setStatus('❌ 初始化异常: ' + e));
});

/* ------------------------------------------------------------ list */
async function loadList() {
  setStatus('加载技能列表…');
  const res = await api('/api/domain/' + D.domain);
  if (!res.body.ok) { setStatus('❌ 列表失败: ' + res.body.message); return; }
  D.list = res.body;
  renderTree();
  setStatus('共 ' + D.list.total + ' 条技能（' + D.list.groups.length + ' 个分组）');
}

function renderTree() {
  const q = D.filter.trim().toLowerCase();
  const tree = $('tree');
  tree.innerHTML = '';
  let shown = 0;
  D.list.groups.forEach((g) => {
    const hit = g.entries.filter((e) => {
      if (!q) return true;
      return [e.name, e.sk_id, e.kind, g.cls_name, g.label, e.group].join(' ').toLowerCase().indexOf(q) >= 0;
    });
    if (!hit.length) return;
    shown += hit.length;
    const gh = document.createElement('div');
    gh.className = 'group';
    gh.textContent = g.label + '  (' + hit.length + ')';
    tree.appendChild(gh);
    hit.forEach((e) => {
      const it = document.createElement('div');
      it.className = 'item' + (e.key === D.key ? ' active' : '');
      const nm = document.createElement('span');
      nm.className = 'nm';
      nm.textContent = (e.name || e.sk_id) + '  ';
      const id = document.createElement('span');
      id.style.color = 'var(--fg2)';
      id.style.fontSize = '11px';
      id.textContent = e.sk_id;
      nm.appendChild(id);
      const kd = document.createElement('span');
      kd.className = 'kd k-' + e.kind;
      kd.textContent = e.kind + (e.lv ? ' Lv' + e.lv : '');
      it.appendChild(nm); it.appendChild(kd);
      it.title = e.key;
      it.addEventListener('click', () => selectEntry(e.key));
      tree.appendChild(it);
    });
  });
  $('list-count').textContent = q ? ('匹配 ' + shown + ' / ' + D.list.total) : ('共 ' + D.list.total + ' 条');
}

/* ------------------------------------------------------- selection */
async function selectEntry(key) {
  if (D.dirty && !confirm('当前有未保存改动，确定丢弃并切换？')) return;
  const res = await api('/api/domain/' + D.domain + '/' + encodeURIComponent(key));
  if (!res.body.ok) { setStatus('❌ 读取失败: ' + res.body.message); return; }
  D.key = key;
  D.meta = res.body.meta;
  D.original = res.body.data;
  D.current = deepCopy(res.body.data);
  D.schema = res.body.schema;
  $('empty').hidden = true;
  $('editor').hidden = false;
  $('sk-title').textContent = (D.meta.name || '') + '　' + (D.meta.sk_id || '');
  $('sk-meta').textContent =
    D.meta.table + ' · ' + (D.meta.cls_name || D.meta.cls_id) +
    (D.meta.group ? ' · ' + D.meta.group + '（Lv' + D.meta.branch_lv + '）' : '') +
    ' · kind=' + D.meta.kind;
  renderTree();
  renderForm();
  renderDiff();
  syncJson();
  setDirty(false);
  savebar(null);
  const v = res.body.validation || {};
  setStatus('已载入 ' + key + (v.ok ? '　·　当前值 schema 校验 ✅' : '　·　当前值有 ' + v.errors.length + ' 处违规'));
}

function renderForm() {
  const box = $('tab-form');
  box.innerHTML = '';
  const rootSchema = D.schema.$defs.skill;
  D.formHandle = SchemaForm.render(rootSchema, D.current, {
    onChange: onModelChange,
    onRerender: () => { renderForm(); },
  });
  box.appendChild(D.formHandle.el);
  if (D.saveErrors) SchemaForm.markErrors(box, D.saveErrors);
}

function onModelChange() {
  renderDiff();
  syncJson();
  setDirty(true);
}

function setDirty(b) {
  D.dirty = b;
  $('dirty-flag').hidden = !b;
  $('btn-save').disabled = !b;
  $('btn-reset').disabled = !b;
}

/* ----------------------------------------------------------- diff tab */
function renderDiff() {
  if (!D.original) return;
  const changes = diff(D.original, D.current);
  const pill = $('diff-count');
  pill.textContent = changes.length;
  pill.className = 'pill' + (changes.length ? ' nz' : '');
  const body = $('diff-body');
  body.innerHTML = '';
  if (!changes.length) {
    body.appendChild(Object.assign(document.createElement('div'), { className: 'diff-none', textContent: '暂无改动。' }));
    return;
  }
  const t = document.createElement('table');
  t.className = 'diff';
  t.innerHTML = '<thead><tr><th>字段</th><th>改前</th><th>改后</th></tr></thead>';
  const tb = document.createElement('tbody');
  changes.forEach((c) => {
    const tr = document.createElement('tr');
    [c.path, c.before, c.after].forEach((v, i) => {
      const td = document.createElement('td');
      if (i === 0) { td.textContent = v; td.style.color = 'var(--accent)'; }
      else { td.className = i === 1 ? 'before' : 'after'; td.textContent = fmt(v); }
      tr.appendChild(td);
    });
    tb.appendChild(tr);
  });
  t.appendChild(tb);
  body.appendChild(t);
}

/* ------------------------------------------------------------ json tab */
function syncJson() { $('json-area').value = JSON.stringify(D.current, null, 2); }

function applyJson() {
  try {
    const parsed = JSON.parse($('json-area').value);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('技能必须是 JSON 对象');
    D.current = parsed;
    $('json-area').classList.remove('bad');
    renderForm(); renderDiff(); setDirty(true);
    setStatus('已从 JSON 同步到表单');
  } catch (e) {
    $('json-area').classList.add('bad');
    setStatus('❌ JSON 解析失败: ' + e.message);
  }
}

/* -------------------------------------------------------------- save */
function savebar(kind, msg, errors) {
  const bar = $('savebar');
  if (!kind) { bar.hidden = true; bar.textContent = ''; return; }
  bar.hidden = false;
  bar.className = 'savebar ' + kind;
  bar.textContent = msg;
  if (errors && errors.length) {
    const ul = document.createElement('ul');
    ul.className = 'err-list';
    errors.slice(0, 40).forEach((e) => {
      const li = document.createElement('li');
      li.textContent = e.path + '  →  ' + e.message;
      ul.appendChild(li);
    });
    bar.appendChild(ul);
  }
}

async function save() {
  D.saveErrors = null;
  const res = await api('/api/domain/' + D.domain + '/' + encodeURIComponent(D.key), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: D.current }),
  });
  if (res.status === 200 && res.body.ok) {
    D.original = deepCopy(D.current);
    setDirty(false);
    renderDiff(); syncJson();
    const n = (res.body.changed || []).length;
    savebar('ok', '✅ 保存成功（' + (res.body.created ? '新建' : '更新 ' + n + ' 个字段') +
      '）→ ' + res.body.saved_to);
    setStatus('已写入 ' + res.body.saved_to + '　·　schema 校验 ✅ (' + res.body.validation.engine + ')');
    await loadList();
  } else {
    const v = (res.body.validation || {});
    D.saveErrors = v.errors || [];
    renderForm();
    savebar('err', '❌ ' + (res.body.message || '保存失败') + '（未写盘）', D.saveErrors);
    const first = (D.saveErrors[0] || {});
    if (first.path) {
      const el = document.querySelector('#tab-form .field[data-path="' + first.path.replace(/^\$\.?/, '') + '"]');
      if (el) el.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
    setStatus('校验拦截：' + D.saveErrors.length + ' 处违规，数据未写入');
  }
}

function reset() {
  D.current = deepCopy(D.original);
  D.saveErrors = null;
  renderForm(); renderDiff(); syncJson(); setDirty(false); savebar(null);
  setStatus('已还原为载入时的值');
}

async function cloneEntry() {
  if (!D.key) return;
  const parts = D.key.split('~');
  const old = parts[parts.length - 1];
  const nid = prompt('新技能 id（将作为 key 的最后一段；同表同职业/分支下新建）', old + '_copy');
  if (!nid) return;
  parts[parts.length - 1] = nid.trim();
  const newKey = parts.join('~');
  const exists = D.list.groups.some((g) => g.entries.some((e) => e.key === newKey));
  if (exists) { alert('已存在同名 key：' + newKey); return; }
  const res = await api('/api/domain/' + D.domain + '/' + encodeURIComponent(newKey), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data: D.current }),
  });
  if (res.status === 200 && res.body.ok) {
    setStatus('已新建 ' + newKey);
    await loadList();
    selectEntry(newKey);
  } else {
    savebar('err', '❌ 新建失败（未写盘）', (res.body.validation || {}).errors || []);
  }
}

/* --------------------------------------------------------------- ui */
function bindUi() {
  $('search').addEventListener('input', (e) => { D.filter = e.target.value; if (D.list) renderTree(); });
  $('btn-save').addEventListener('click', save);
  $('btn-reset').addEventListener('click', reset);
  $('btn-json-apply').addEventListener('click', applyJson);
  $('btn-clone').addEventListener('click', cloneEntry);
  $('tabs').addEventListener('click', (e) => {
    const b = e.target.closest('button[data-tab]');
    if (!b) return;
    document.querySelectorAll('#tabs button[data-tab]').forEach((x) => x.classList.toggle('active', x === b));
    ['form', 'json', 'diff'].forEach((t) => { $('tab-' + t).hidden = (t !== b.dataset.tab); });
  });
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') { e.preventDefault(); if (D.dirty) save(); }
  });
  window.addEventListener('beforeunload', (e) => {
    if (D.dirty) { e.preventDefault(); e.returnValue = ''; }
  });
}
