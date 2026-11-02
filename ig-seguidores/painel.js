// IG Seguidores — painel
// Lista quem não te segue de volta, fãs, novos/perdidos e descobre contas; segue e deixa de seguir
// com limite diário, pausa aleatória e confirmação. Os dados ficam só neste navegador.

const $ = (s) => document.querySelector(s);
const IG = 'https://www.instagram.com/';
const DAILY_MAX = 200;
const MIN_DELAY = 10;     // pausa mínima entre ações (s)
const REST_EVERY = 20;    // descanso maior a cada N ações (mesmo valor do coletor.js)
const PAGE = 100;

const TABS = [
  { id: 'naoSeguem', label: 'Não me seguem de volta', act: 'unfollow' },
  { id: 'fas', label: 'Fãs (me seguem, eu não)', act: 'follow' },
  { id: 'mutuos', label: 'Mútuos' },
  { id: 'seguindo', label: 'Seguindo', act: 'unfollow' },
  { id: 'seguidores', label: 'Seguidores' },
  { id: 'novos', label: 'Novos seguidores', act: 'follow' },
  { id: 'perdidos', label: 'Deixaram de me seguir' },
  { id: 'descobrir', label: 'Descobrir', act: 'follow' },
  { id: 'protegidos', label: 'Protegidos' }
];

let data = null;          // { ts, me, followers, following }
let snaps = [];           // últimas leituras (mais nova primeiro), só ids/usuário/nome
let prot = new Set();     // contas protegidas: nunca deixa de seguir
let seen = new Set();     // contas que esta ferramenta já seguiu
let discover = [];        // candidatos da aba Descobrir
let day = { date: '', follow: 0, unfollow: 0 };
let lists = {};
let byId = new Map();
let tab = 'naoSeguem';
let sel = new Set();
let shown = PAGE;
let running = null;       // 'lists' | 'act' | 'discover' | null
let queue = null;         // fila de ações que sobraram do limite do dia: { op, users: [{ id, u }] }
let unf = new Set();      // contas que você deixou de seguir (pela ferramenta ou à mão): nunca são seguidas de novo
let fSet = new Set();     // ids dos seus seguidores
let gSet = new Set();     // ids de quem você segue
let autoFollow = false;   // "Buscar e seguir automaticamente" em andamento
let acct = null;          // id da conta do Instagram cujos dados estão na tela
let accts = {};           // id -> @usuário de cada conta já lida (cada uma guarda os seus próprios dados)

const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n));
const today = () => new Date().toLocaleDateString('sv-SE');
const fmtDate = (ts) => new Date(ts).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });

let toastTimer = 0;
function toast(t) {
  const el = $('#toast');
  el.textContent = t;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 3800);
}
const setStatus = (t) => { $('#status').textContent = t; };

// Log de eventos e erros (guardado neste navegador, últimas 300 linhas). Nunca grava cookies, senhas nem tokens.
const LOG_MAX = 300;
let logChain = Promise.resolve();
function logEv(kind, text) {
  const linha = { t: new Date().toISOString(), k: kind, m: String(text == null ? '' : text).slice(0, 600) };
  logChain = logChain.then(async () => {
    const { log = [] } = await chrome.storage.local.get('log');
    log.push(linha);
    await chrome.storage.local.set({ log: log.slice(-LOG_MAX) });
  }).catch(() => {});
  return logChain;
}
async function logText() {
  const { log = [] } = await chrome.storage.local.get('log');
  return log.map((l) => l.t.replace('T', ' ').slice(0, 19) + ' [' + l.k + '] ' + l.m).join('\n');
}

window.addEventListener('error', (e) => { toast('Erro: ' + e.message); logEv('erro-js', e.message + (e.filename ? ' (' + e.filename.split('/').pop() + ':' + e.lineno + ')' : '')); });
window.addEventListener('unhandledrejection', (e) => { const m = (e.reason && e.reason.message) || e.reason; toast('Erro: ' + m); logEv('erro-js', m); });

// ---------------- dados ----------------

// Cada conta do Instagram tem as suas chaves: 'a:<id>' (listas, protegidos, histórico, fila) e 'day:<id>'
// (contador do dia, que o coletor.js também grava). As preferências da tela são comuns.
let saveTimer = 0;
function save(now) {
  clearTimeout(saveTimer);
  const go = () => {
    const o = {
      accts,
      prefs: { limit: Number($('#p-limit').value), delay: Number($('#p-delay').value), all: $('#p-all').checked, inc: $('#p-incog').checked, hv: $('#f-ver').checked, hp: $('#f-priv').checked }
    };
    if (acct) {
      o.active = acct;
      o['a:' + acct] = { data, snaps, prot: [...prot], seen: [...seen].slice(-5000), unfollowed: [...unf], queue };
      o['day:' + acct] = day;
    }
    return chrome.storage.local.set(o);
  };
  if (now) return go();
  saveTimer = setTimeout(go, 800);
}

// carrega os dados de uma conta (zerados se ainda não existir)
async function loadAcct(id) {
  acct = id ? String(id) : null;
  let a = {}, d = null;
  if (acct) {
    const s = await chrome.storage.local.get({ ['a:' + acct]: {}, ['day:' + acct]: null });
    a = s['a:' + acct] || {};
    d = s['day:' + acct];
  }
  data = a.data || null;
  snaps = a.snaps || [];
  prot = new Set(a.prot || []);
  seen = new Set(a.seen || []);
  unf = new Set(a.unfollowed || []);
  queue = a.queue && a.queue.users && a.queue.users.length ? a.queue : null;
  day = d && d.date === today() ? d : { date: today(), follow: 0, unfollow: 0 };
  discover = [];
  sel.clear();
  shown = PAGE;
}

// muda a conta mostrada no painel (guarda a atual antes)
async function switchAcct(id, username) {
  id = String(id);
  if (username) accts[id] = username;
  if (id === acct) { renderAcctSelect(); return; }
  if (acct) await save(true);
  if (!accts[id]) accts[id] = id;
  await loadAcct(id);
  derive();
  renderAcctSelect();
  render();
  save(true);
}

function renderAcctSelect() {
  const s = $('#acct');
  const ids = Object.keys(accts);
  s.textContent = '';
  if (!ids.length) {
    const o = document.createElement('option');
    o.textContent = 'Nenhuma conta lida';
    s.appendChild(o);
  }
  s.disabled = !ids.length || !!running;
  for (const id of ids) {
    const o = document.createElement('option');
    o.value = id;
    o.textContent = accts[id] && accts[id] !== id ? '@' + accts[id] : 'conta ' + id;
    o.selected = id === acct;
    s.appendChild(o);
  }
}

async function load() {
  const s = await chrome.storage.local.get({ active: null, accts: {}, prefs: null, data: null, snaps: [], prot: [], seen: [], unfollowed: [], day: null, queue: null });
  accts = s.accts || {};
  let active = s.active;
  // migração: versões antigas guardavam tudo de uma conta só, sem separar por conta
  if (!active && s.data && s.data.me && s.data.me.id) {
    active = String(s.data.me.id);
    accts[active] = s.data.me.username || active;
    await chrome.storage.local.set({
      active, accts,
      ['a:' + active]: { data: s.data, snaps: s.snaps, prot: s.prot, seen: s.seen, unfollowed: s.unfollowed, queue: s.queue },
      ['day:' + active]: s.day
    });
    await chrome.storage.local.remove(['data', 'snaps', 'prot', 'seen', 'unfollowed', 'day', 'queue']);
  }
  await loadAcct(active);
  if (s.prefs) {
    $('#p-limit').value = s.prefs.limit || 40;
    $('#p-delay').value = Math.max(MIN_DELAY, s.prefs.delay || 15);
    $('#p-all').checked = !!s.prefs.all;
    $('#p-incog').checked = s.prefs.inc !== false;
    $('#f-ver').checked = !!s.prefs.hv;
    $('#f-priv').checked = !!s.prefs.hp;
  }
}

function derive() {
  lists = {};
  byId = new Map();
  if (!data) return;
  const F = data.followers, G = data.following;
  for (const u of F) byId.set(u.id, u);
  for (const u of G) byId.set(u.id, byId.get(u.id) || u);
  fSet = new Set(F.map((u) => u.id));
  gSet = new Set(G.map((u) => u.id));
  lists.naoSeguem = G.filter((u) => !fSet.has(u.id));
  lists.fas = F.filter((u) => !gSet.has(u.id));
  lists.mutuos = G.filter((u) => fSet.has(u.id));
  lists.seguindo = G;
  lists.seguidores = F;
  // mudanças: compara com uma leitura anterior (de preferência com mais de 10 min)
  const old = snaps.slice(1).find((s) => snaps[0].ts - s.ts > 10 * 60 * 1000) || snaps[1] || null;
  if (old) {
    const oldF = new Set(old.followers.map((x) => x[0]));
    lists.novos = F.filter((u) => !oldF.has(u.id));
    lists.perdidos = old.followers.filter((x) => !fSet.has(x[0])).map((x) => ({ id: x[0], u: x[1], n: x[2] || '', v: 0, p: 0, pic: '' }));
    lists.mudancasDesde = old.ts;
  } else { lists.novos = []; lists.perdidos = []; }
  lists.protegidos = [...prot].map((id) => byId.get(id)).filter(Boolean);
}

// Quem vale a pena seguir: gente NOVA. Fica de fora quem você já segue, quem já te segue, quem
// você já deixou de seguir (nunca volta a ser seguido), quem esta ferramenta já seguiu e perfis privados.
function isCandidate(u) {
  return !!u.id && !u.p && !(data && data.me && data.me.id === u.id) &&
    !gSet.has(u.id) && !fSet.has(u.id) && !unf.has(u.id) && !seen.has(u.id);
}

function currentList() {
  if (tab === 'descobrir') return discover.filter(isCandidate);
  return lists[tab] || [];
}

function view() {
  const q = $('#q').value.trim().toLowerCase();
  let arr = currentList();
  if (q) arr = arr.filter((u) => u.u.toLowerCase().includes(q) || (u.n || '').toLowerCase().includes(q));
  if ($('#f-ver').checked) arr = arr.filter((u) => !u.v);
  if ($('#f-priv').checked) arr = arr.filter((u) => !u.p);
  if ($('#f-sort').value === 'az') arr = [...arr].sort((a, b) => a.u.localeCompare(b.u));
  return arr;
}

// ---------------- tela ----------------

function renderTabs() {
  const box = $('#tabs');
  box.textContent = '';
  for (const t of TABS) {
    const b = document.createElement('button');
    b.className = 'tab' + (t.id === tab ? ' on' : '');
    b.append(t.label);
    const c = document.createElement('b');
    c.textContent = t.id === 'descobrir' ? String(discover.length) : String((lists[t.id] || []).length);
    b.appendChild(c);
    b.addEventListener('click', () => { tab = t.id; sel.clear(); shown = PAGE; render(); });
    box.appendChild(b);
  }
}

// As fotos vêm do CDN do Instagram, que bloqueia <img> direto numa página de extensão
// (ERR_BLOCKED_BY_RESPONSE.NotSameOrigin). A extensão baixa a imagem (tem permissão do host) e mostra o resultado.
const picCache = new Map(); // id -> endereço local da imagem ('' = falhou)
const picQueue = [];
let picActive = 0;

function picPump() {
  while (picActive < 6 && picQueue.length) {
    const j = picQueue.shift();
    picActive++;
    fetch(j.url)
      .then((r) => (r.ok ? r.blob() : null))
      .then((b) => { const s = b ? URL.createObjectURL(b) : ''; picCache.set(j.id, s); j.resolve(s); })
      .catch(() => { picCache.set(j.id, ''); j.resolve(''); })
      .finally(() => { picActive--; picPump(); });
  }
}
function picLoad(url, id) {
  if (picCache.has(id)) return Promise.resolve(picCache.get(id));
  return new Promise((resolve) => { picQueue.push({ url, id, resolve }); picPump(); });
}

function avatar(u) {
  const slot = document.createElement('div');
  const fb = document.createElement('div');
  fb.className = 'av-fb';
  fb.textContent = (u.u || '?')[0].toUpperCase();
  slot.appendChild(fb);
  if (u.pic) {
    picLoad(u.pic, u.id).then((src) => {
      if (!src) return;
      const img = document.createElement('img');
      img.className = 'av';
      img.src = src;
      slot.replaceChildren(img);
    });
  }
  return slot;
}

function row(u) {
  const r = document.createElement('div');
  r.className = 'row' + (prot.has(u.id) ? ' protegido' : '');
  const cb = document.createElement('input');
  cb.type = 'checkbox';
  cb.checked = sel.has(u.id);
  cb.addEventListener('change', () => { if (cb.checked) sel.add(u.id); else sel.delete(u.id); updateBar(); });
  const who = document.createElement('div');
  who.className = 'who';
  const a = document.createElement('a');
  a.href = IG + encodeURIComponent(u.u) + '/';
  a.target = '_blank';
  a.rel = 'noopener';
  a.textContent = '@' + u.u;
  who.appendChild(a);
  if (u.v) { const b = document.createElement('span'); b.className = 'badge'; b.textContent = 'verificada'; who.appendChild(b); }
  if (u.p) { const b = document.createElement('span'); b.className = 'badge'; b.textContent = 'privada'; who.appendChild(b); }
  const nm = document.createElement('div');
  nm.className = 'nm';
  nm.textContent = u.n || '';
  who.appendChild(nm);
  const star = document.createElement('button');
  star.className = 'star' + (prot.has(u.id) ? ' on' : '');
  star.textContent = '★';
  star.title = prot.has(u.id) ? 'Protegida: nunca deixa de seguir. Clique para remover' : 'Proteger: nunca deixar de seguir esta conta';
  star.addEventListener('click', () => {
    if (prot.has(u.id)) prot.delete(u.id); else prot.add(u.id);
    save();
    derive();
    render();
  });
  r.append(cb, avatar(u), who, star);
  return r;
}

function renderQueue() {
  const q = $('#queue');
  q.hidden = !queue || !queue.users.length;
  if (q.hidden) return;
  $('#queue-text').textContent = 'Fila: ' + queue.users.length + ' conta(s) esperando para ' +
    (queue.op === 'unfollow' ? 'deixar de seguir' : 'seguir') + ' (o limite diário de ' + DAILY_MAX + ' deixou o resto para depois).';
  $('#queue-go').disabled = !!running;
}

function render() {
  renderQueue();
  renderTabs();
  $('#discover').hidden = tab !== 'descobrir';
  $('#prot-tools').hidden = tab !== 'protegidos';
  const arr = view();
  const box = $('#list');
  box.textContent = '';
  if (!data && tab !== 'descobrir') {
    const e = document.createElement('div');
    e.className = 'empty';
    e.textContent = 'Nenhuma lista ainda. Clique em "Atualizar listas" (pode levar alguns minutos, dependendo de quantas contas você segue).';
    box.appendChild(e);
  } else if (!arr.length) {
    const e = document.createElement('div');
    e.className = 'empty';
    e.textContent = (tab === 'novos' || tab === 'perdidos') && !lists.mudancasDesde
      ? 'Ainda não há uma leitura anterior para comparar. Atualize de novo mais tarde (horas ou dias) para ver as mudanças.'
      : tab === 'descobrir' ? 'Clique em "Buscar contas" para listar candidatos.' : 'Nada por aqui.';
    box.appendChild(e);
  } else {
    for (const u of arr.slice(0, shown)) box.appendChild(row(u));
  }
  $('#btn-more').hidden = arr.length <= shown;
  $('#btn-more').textContent = 'Mostrar mais (' + Math.min(PAGE, arr.length - shown) + ')';
  $('#n-filtered').textContent = String(arr.length);
  if ((tab === 'novos' || tab === 'perdidos') && lists.mudancasDesde) setStatus(statusLine() + ' • mudanças desde ' + fmtDate(lists.mudancasDesde));
  else setStatus(statusLine());
  updateBar();
}

function statusLine() {
  if (!data) return 'Clique em Atualizar listas para começar.';
  return (data.me && data.me.username ? '@' + data.me.username + ' • ' : '') + data.followers.length + ' seguidores • ' + data.following.length + ' seguindo • atualizado em ' + fmtDate(data.ts);
}

function updateBar() {
  const meta = TABS.find((t) => t.id === tab);
  const btn = $('#btn-act');
  const n = view().filter((u) => sel.has(u.id)).length;
  $('#sel-all').checked = n > 0 && n === view().length;
  if (meta && meta.act) {
    btn.hidden = false;
    btn.textContent = (meta.act === 'unfollow' ? 'Deixar de seguir' : 'Seguir') + ' (' + n + ')';
    btn.disabled = !n || !!running;
  } else {
    btn.hidden = true;
  }
  $('#daily').textContent = 'Hoje: ' + day.follow + ' seguidas e ' + day.unfollow + ' deixadas de seguir (limite de ' + DAILY_MAX + ' por tipo). Contas protegidas (★) nunca são deixadas de seguir.';
  $('#btn-refresh').disabled = !!running;
  $('#acct').disabled = !!running || !Object.keys(accts).length;
  $('#btn-addacct').disabled = !!running;
  $('#p-incog').disabled = !!running;
  $('#btn-discover').disabled = !!running;
  $('#btn-autofollow').disabled = !!running;
  $('#queue-go').disabled = !!running;
  $('#btn-stop').disabled = !running;
  $('#btn-pause').disabled = !running;
  if (!running) $('#btn-pause').textContent = 'Pausar';
}

function setRunning(r, pct) {
  running = r;
  const bar = $('#progress');
  const fill = $('#progress-fill');
  bar.hidden = !r;
  fill.classList.toggle('indeterminate', !!r && pct == null);
  fill.style.width = pct == null ? '' : clamp(pct, 0, 100) + '%';
  updateBar();
}

// ---------------- janela do Instagram ----------------

const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const igMsg = (tabId, cmd, extra) => chrome.tabs.sendMessage(tabId, { __igsCmd: 1, cmd, ...extra }).catch(() => null);

// usa uma janelinha própria do Instagram (visível, para o navegador não "congelar" os temporizadores)
// ----- logins guardados: a janela anônima nasce vazia, então o painel guarda o login de cada conta
// ('ck:<id>' = cookies do instagram.com) e o recoloca na janela quando você escolhe a conta -----

async function cookieStore(tabId) {
  const stores = await chrome.cookies.getAllCookieStores();
  const s = stores.find((x) => x.tabIds.includes(tabId));
  return s ? s.id : null;
}
const igCookies = (storeId) => chrome.cookies.getAll({ domain: 'instagram.com', storeId });

async function clearIgCookies(storeId) {
  for (const c of await igCookies(storeId)) {
    await chrome.cookies.remove({ url: 'https://' + c.domain.replace(/^\./, '') + c.path, name: c.name, storeId }).catch(() => {});
  }
}

async function saveLogin(tabId, id) {
  const store = await cookieStore(tabId);
  if (store == null) return;
  const cs = await igCookies(store);
  if (!cs.some((c) => c.name === 'sessionid')) return;
  await chrome.storage.local.set({
    ['ck:' + id]: cs.map((c) => ({ name: c.name, value: c.value, domain: c.domain, hostOnly: c.hostOnly, path: c.path, secure: c.secure, httpOnly: c.httpOnly, sameSite: c.sameSite, expirationDate: c.expirationDate }))
  });
}

async function restoreLogin(storeId, id) {
  const cs = (await chrome.storage.local.get('ck:' + id))['ck:' + id] || [];
  for (const c of cs) {
    const o = { url: 'https://www.instagram.com' + (c.path || '/'), name: c.name, value: c.value, path: c.path, secure: c.secure, httpOnly: c.httpOnly, sameSite: c.sameSite, storeId };
    if (!c.hostOnly) o.domain = c.domain;
    if (c.expirationDate) o.expirationDate = c.expirationDate;
    await chrome.cookies.set(o).catch(() => {});
  }
}

// pergunta qual conta abrir; devolve { id } (id null = entrar em outra conta) ou null se cancelou
function chooseAccount(saved) {
  return new Promise((resolve) => {
    const dlg = $('#pick');
    const list = $('#pick-list');
    let done = false;
    const end = (v) => { if (done) return; done = true; if (dlg.open) dlg.close(); resolve(v); };
    const fill = () => {
      list.textContent = '';
      for (const a of saved) {
        const r = document.createElement('div');
        r.className = 'pick-row';
        const b = document.createElement('button');
        b.className = 'primary';
        b.textContent = '@' + a.name;
        b.addEventListener('click', () => end({ id: a.id }));
        const x = document.createElement('button');
        x.className = 'ghost';
        x.textContent = 'esquecer login';
        x.title = 'Apaga só o login guardado desta conta (as listas dela continuam)';
        x.addEventListener('click', async () => {
          await chrome.storage.local.remove('ck:' + a.id);
          saved = saved.filter((s) => s.id !== a.id);
          if (!saved.length) end({ id: null }); else fill();
        });
        r.append(b, x);
        list.appendChild(r);
      }
    };
    fill();
    $('#pick-new').onclick = () => end({ id: null });
    $('#pick-cancel').onclick = () => end(null);
    dlg.oncancel = () => end(null);
    dlg.showModal();
  });
}

// abre (ou reaproveita) a janelinha do Instagram, visível para o navegador não "congelar" os temporizadores.
// forceChoose = mesmo com a janelinha aberta, pergunta de novo qual conta.
async function igWindow(focused, forceChoose) {
  // janela anônima = cookies separados do Chrome normal (o Instagram pessoal fica de fora)
  const inc = $('#p-incog').checked;
  // sem essa permissão o Chrome abre a janela anônima mas não a entrega à extensão (resposta nula): melhor nem abrir
  if (inc && !(await chrome.extension.isAllowedIncognitoAccess())) {
    throw new Error('Esta cópia da extensão (ID ' + chrome.runtime.id + ') não tem "Permitir em modo anônimo". Em chrome://extensions, procure o IG Seguidores com esse ID, abra Detalhes e ligue a opção. Se houver duas cópias, remova a que não usa.');
  }
  const { igWin } = await chrome.storage.session.get('igWin');
  let tabId = igWin && igWin.tabId;
  let windowId = igWin && igWin.windowId;
  if (tabId != null) {
    try {
      const t = await chrome.tabs.get(tabId);
      if (!/instagram\.com/.test(t.url || '') || !!t.incognito !== inc) tabId = null; // outra janela ou outro modo: abre uma nova
    } catch (_) { tabId = null; }
  }
  if (tabId != null && !forceChoose) {
    if (focused && windowId != null) await chrome.windows.update(windowId, { focused: true }).catch(() => {});
    return tabId;
  }

  let pick = { id: null };
  if (inc) {
    const ids = Object.keys(accts);
    const got = ids.length ? await chrome.storage.local.get(ids.map((i) => 'ck:' + i)) : {};
    const saved = ids.filter((i) => (got['ck:' + i] || []).length).map((i) => ({ id: i, name: accts[i] || i }));
    if (saved.length) {
      pick = await chooseAccount(saved);
      if (!pick) throw new Error('Nenhuma conta escolhida.');
    }
  }
  if (tabId != null && windowId != null) await chrome.windows.remove(windowId).catch(() => {});

  let w;
  try {
    w = await chrome.windows.create({
      url: inc ? 'about:blank' : IG, type: 'popup', width: 420, height: 640, left: Math.max(0, screen.availWidth - 440), top: 40, focused: !!focused, incognito: inc
    });
  } catch (e) {
    throw new Error(inc
      ? 'Não consegui abrir a janela anônima (' + e.message + '). Confira "Permitir em modo anônimo" em chrome://extensions > IG Seguidores > Detalhes, recarregue a extensão e tente de novo.'
      : e.message);
  }
  if (!w) throw new Error('o Chrome abriu a janela mas não a entregou à extensão (falta "Permitir em modo anônimo"; ID ' + chrome.runtime.id + '). Feche a janela em branco que abriu');
  windowId = w.id;
  let step = 'achar a aba da janela';
  try {
    // a aba nem sempre vem em w.tabs (janela anônima): procura pela janela
    tabId = w.tabs && w.tabs[0] ? w.tabs[0].id : null;
    for (let i = 0; tabId == null && i < 10; i++) {
      const ts = await chrome.tabs.query({ windowId });
      if (ts.length) tabId = ts[0].id; else await wait(200);
    }
    if (tabId == null) throw new Error('aba não encontrada');
    await chrome.storage.session.set({ igWin: { tabId, windowId } });
    if (inc) {
      // deixa só o login escolhido (ou nenhum, para entrar em outra conta) e então abre o Instagram
      step = 'isolar o login da janela anônima';
      const store = await cookieStore(tabId);
      if (store == null) throw new Error('janela sem área de cookies própria');
      await clearIgCookies(store);
      step = 'colocar o login guardado';
      if (pick.id) await restoreLogin(store, pick.id);
      step = 'abrir o Instagram';
      await chrome.tabs.update(tabId, { url: IG });
      await wait(700);
    }
    step = 'carregar o Instagram';
    let ok = false;
    for (let i = 0; i < 40 && !ok; i++) {
      const t = await chrome.tabs.get(tabId);
      ok = t.status === 'complete' && /instagram\.com/.test(t.url || t.pendingUrl || '');
      if (!ok) await wait(500);
    }
    if (!ok) throw new Error('a página não carregou');
  } catch (e) {
    await chrome.windows.remove(windowId).catch(() => {});
    throw new Error('Não consegui ' + step + ' (' + (e && e.message ? e.message : e) + '). A janelinha foi fechada; tente de novo.');
  }
  return tabId;
}

let whoWhy = ''; // por que não deu para descobrir o @ da conta (último caso)

async function ensureIg() {
  const tabId = await igWindow(false);
  await chrome.scripting.executeScript({ target: { tabId }, files: ['coletor.js'] }).catch(() => {});
  await chrome.scripting.executeScript({ target: { tabId }, files: ['ponte.js'], world: 'MAIN' }).catch(() => {});
  let r = null;
  for (let i = 0; i < 10 && !r; i++) { r = await igMsg(tabId, 'ping'); if (!r) await wait(700); }
  if (!r) throw new Error('Não consegui falar com a página do Instagram. Recarregue a janelinha dele e tente de novo.');
  if (!r.loggedIn) throw new Error('Você não está logado no Instagram. Entre na janelinha que abri e clique de novo.');
  const id = String(r.id);
  // na janela anônima, guarda o login desta conta para poder escolhê-la depois sem entrar de novo
  const tab = await chrome.tabs.get(tabId).catch(() => null);
  if (tab && tab.incognito) await saveLogin(tabId, id).catch(() => {});
  if (!accts[id]) { accts[id] = id; save(true); }
  // descobre o @ da conta logada para o seletor mostrar o nome em vez do número
  if (accts[id] === id) {
    const w = await igMsg(tabId, 'who');
    if (w && w.ok && w.username) { accts[id] = w.username; renderAcctSelect(); save(true); }
    else { whoWhy = w ? (w.why || 'sem resposta') : 'o script antigo da janelinha não respondeu: feche a janelinha do Instagram e tente de novo'; logEv('aviso', '@ da conta ' + id + ' não descoberto: ' + whoWhy); }
  }
  return { tabId, id };
}

async function start(cmd, extra, kind) {
  try {
    setRunning(kind);
    setStatus('Conectando ao Instagram…');
    const { tabId, id } = await ensureIg();
    if (cmd === 'lists') {
      await switchAcct(id); // ler as listas de outra conta passa o painel para ela
    } else if (acct && id !== acct) {
      throw new Error('A janelinha do Instagram está em outra conta (' + (accts[id] ? '@' + accts[id] : id) + '), mas o painel mostra @' +
        (accts[acct] || acct) + '. Entre na conta certa na janelinha, ou clique em "Atualizar listas" para trocar a conta do painel.');
    }
    $('#btn-stop').dataset.tab = String(tabId);
    const r = await igMsg(tabId, cmd, extra);
    if (!r || !r.ok) throw new Error('O Instagram não aceitou o comando.');
  } catch (e) {
    setRunning(null);
    toast(e.message);
    setStatus(e.message); // o erro fica na tela (o aviso some sozinho)
    logEv('erro', cmd + ': ' + e.message);
  }
}

// ---------------- mensagens do Instagram ----------------

chrome.runtime.onMessage.addListener((m, sender) => {
  if (!m || !m.__igs || !sender.tab) return;
  switch (m.type) {
    case 'progress': setStatus(m.text); break;
    case 'lists': onLists(m); break;
    case 'discover': {
      discover = m.users;
      const novos = discover.filter(isCandidate).length;
      toast(discover.length + ' conta(s) encontradas; ' + novos + ' são novas (sem repetir quem você já segue, já te segue ou já deixou de seguir).');
      if (autoFollow) { autoFollow = false; setTimeout(autoFollowRun, 400); }
      break;
    }
    case 'act': onAct(m); break;
    case 'paused':
      $('#btn-pause').textContent = m.value ? 'Retomar' : 'Pausar';
      setStatus(m.value ? 'Pausado. Clique em Retomar para continuar.' : 'Retomado.');
      break;
    case 'done': case 'stopped': case 'error':
      logEv(m.type === 'error' ? 'erro-ig' : 'info', m.text || m.type);
      if (m.type === 'error') toast(m.text);
      setStatus(m.text || statusLine());
      break;
    case 'idle':
      setRunning(null);
      render();
      break;
  }
});

async function onLists(m) {
  if (m.me && m.me.id) await switchAcct(m.me.id, m.me.username);
  // quem estava na lista de "seguindo" e saiu sem passar pela ferramenta foi deixado de seguir à mão:
  // também entra no histórico para nunca ser seguido de novo
  if (data) {
    const agora = new Set(m.following.map((u) => u.id));
    for (const u of data.following) if (!agora.has(u.id)) unf.add(u.id);
  }
  data = { ts: Date.now(), me: m.me, followers: m.followers, following: m.following };
  snaps = [{ ts: data.ts, followers: m.followers.map((u) => [u.id, u.u, u.n]), following: m.following.map((u) => [u.id, u.u, u.n]) }, ...snaps].slice(0, 5);
  sel.clear();
  derive();
  save(true);
  toast('Listas atualizadas.');
}

function onAct(m) {
  if (m.acct && m.acct !== acct) return; // ação de outra conta: não mexe nos dados desta
  day = m.day;
  if (m.op === 'unfollow') {
    data.following = data.following.filter((u) => u.id !== m.user.id);
    unf.add(m.user.id);
  } else {
    const full = byId.get(m.user.id) || discover.find((u) => u.id === m.user.id) || { id: m.user.id, u: m.user.u, n: '', v: 0, p: 0, pic: '' };
    if (!data.following.some((u) => u.id === full.id)) data.following.push(full);
    seen.add(m.user.id);
  }
  sel.delete(m.user.id);
  if (queue) queue.users = queue.users.filter((x) => x.id !== m.user.id);
  derive();
  save();
  setRunning('act', (m.done / m.total) * 100);
  setStatus((m.op === 'unfollow' ? 'Deixou de seguir' : 'Seguiu') + ' @' + m.user.u + ' (' + m.done + '/' + m.total + ')');
  render();
}

// ---------------- ações ----------------

$('#btn-refresh').addEventListener('click', () => start('lists', {}, 'lists'));
$('#btn-stop').addEventListener('click', async () => {
  const id = Number($('#btn-stop').dataset.tab);
  if (id) await igMsg(id, 'stop');
  setStatus('Parando…');
});

$('#btn-pause').addEventListener('click', async () => {
  const id = Number($('#btn-stop').dataset.tab);
  if (!id) return;
  await igMsg(id, $('#btn-pause').textContent === 'Pausar' ? 'pause' : 'resume');
});

// ----- contas protegidas: exportar / importar / colar -----
const byUsername = () => {
  const m = new Map();
  for (const u of byId.values()) m.set(u.u.toLowerCase(), u);
  return m;
};

$('#prot-export').addEventListener('click', () => {
  if (!prot.size) { toast('Nenhuma conta protegida para exportar.'); return; }
  const arr = [...prot].map((id) => ({ id, u: (byId.get(id) || {}).u || '' }));
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([JSON.stringify(arr, null, 2)], { type: 'application/json' }));
  a.download = 'ig-seguidores-protegidos-' + today() + '.json';
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  toast(arr.length + ' conta(s) exportada(s).');
});

$('#prot-import').addEventListener('click', () => $('#prot-file').click());
$('#prot-file').addEventListener('change', async () => {
  const f = $('#prot-file').files[0];
  $('#prot-file').value = '';
  if (!f) return;
  try {
    const arr = JSON.parse(await f.text());
    if (!Array.isArray(arr)) throw new Error('formato inválido (esperado uma lista)');
    const nomes = byUsername();
    let novos = 0, ignorados = 0;
    for (const x of arr) {
      const id = x && x.id && byId.has(String(x.id)) ? String(x.id)
        : x && x.u && nomes.has(String(x.u).toLowerCase()) ? nomes.get(String(x.u).toLowerCase()).id : null;
      if (!id) { ignorados++; continue; }
      if (!prot.has(id)) { prot.add(id); novos++; }
    }
    save(true); derive(); render();
    toast(novos + ' conta(s) protegida(s) importada(s)' + (ignorados ? '; ' + ignorados + ' fora das suas listas.' : '.'));
  } catch (e) {
    toast('Não consegui importar: ' + e.message);
  }
});

$('#prot-paste').addEventListener('click', () => {
  const tokens = $('#prot-text').value.split(/[\s,;]+/).map((s) => s.replace(/^@+/, '').trim().toLowerCase()).filter((s) => /^[a-z0-9._]+$/.test(s));
  if (!tokens.length) { toast('Nenhum usuário válido encontrado no texto.'); return; }
  const nomes = byUsername();
  let novos = 0, fora = 0;
  for (const t of new Set(tokens)) {
    const u = nomes.get(t);
    if (!u) { fora++; continue; }
    if (!prot.has(u.id)) { prot.add(u.id); novos++; }
  }
  $('#prot-text').value = '';
  save(true); derive(); render();
  toast(novos + ' conta(s) protegida(s)' + (fora ? '; ' + fora + ' não aparecem nas suas listas.' : '.'));
});

// perfis de origem separados por vírgula ou espaço (vazio = sugestões do Instagram)
const sourcesInput = () => $('#d-src').value.split(/[\s,;]+/).map((s) => s.replace(/^@/, '').trim()).filter(Boolean).slice(0, 5);

$('#btn-discover').addEventListener('click', () => {
  autoFollow = false;
  start('discover', { opts: { sources: sourcesInput(), max: 300 } }, 'discover');
});

// busca contas novas e já segue, tudo de uma vez (com confirmação e os mesmos limites)
$('#btn-autofollow').addEventListener('click', () => {
  if (!data) { toast('Atualize as listas primeiro: é com elas que a ferramenta evita repetir contas.'); return; }
  autoFollow = true;
  start('discover', { opts: { sources: sourcesInput(), max: 300 } }, 'discover');
});

function autoFollowRun() {
  const fila = discover.filter(isCandidate).filter((u) => !($('#f-ver').checked && u.v));
  launch('follow', fila);
}

// roda um lote: respeita o limite do dia, pede confirmação e guarda o que sobrar na fila
async function launch(op, users) {
  const delay = clamp(parseInt($('#p-delay').value, 10) || 15, MIN_DELAY, 120);
  const cap = $('#p-all').checked ? DAILY_MAX : clamp(parseInt($('#p-limit').value, 10) || 40, 1, DAILY_MAX);
  const limit = Math.min(cap, DAILY_MAX - day[op]);
  if (!users.length) { toast('Nenhuma conta elegível para esta ação.'); return; }
  if (limit <= 0) {
    queue = { op, users: users.map((u) => ({ id: u.id, u: u.u })) };
    save(true); renderQueue();
    toast('Limite diário atingido. A lista ficou na fila: continue amanhã.');
    return;
  }
  const n = Math.min(users.length, limit);
  const mins = Math.max(1, Math.round((n * delay * 1.3 + Math.floor(n / REST_EVERY) * 90) / 60));
  const ok = confirm(
    (op === 'unfollow' ? 'Deixar de seguir ' : 'Seguir ') + n + ' conta(s)' + (users.length > n ? ' (de ' + users.length + '; o resto fica na fila para os próximos dias)' : '') + '?\n\n' +
    'Pausa de ~' + delay + 's entre cada: leva cerca de ' + mins + ' min.\n' +
    'Mantenha a janelinha do Instagram aberta e visível. Você pode parar quando quiser.\n\n' +
    'Seguir e deixar de seguir em massa pode limitar a conta. Continuar?'
  );
  if (!ok) return;
  queue = users.length > n ? { op, users: users.slice(n).map((u) => ({ id: u.id, u: u.u })) } : null;
  save(true);
  renderQueue();
  await start('act', { opts: { acct, op, users: users.slice(0, n).map((u) => ({ id: u.id, u: u.u })), limit: n, minDelay: delay, maxDelay: Math.round(delay * 1.6) } }, 'act');
}

$('#btn-act').addEventListener('click', () => {
  const meta = TABS.find((t) => t.id === tab);
  if (!meta || !meta.act || !data) return;
  const op = meta.act;
  let users = view().filter((u) => sel.has(u.id));
  if (op === 'unfollow') users = users.filter((u) => !prot.has(u.id));
  if (op === 'follow') users = users.filter((u) => !unf.has(u.id) && !gSet.has(u.id));
  if (tab === 'descobrir') users = users.filter((u) => !u.p); // privadas exigem aprovação: não vale gastar o limite
  launch(op, users);
});

// retoma o que sobrou do limite do dia (só contas que ainda fazem sentido hoje)
$('#queue-go').addEventListener('click', () => {
  if (!queue || !data) return;
  const op = queue.op;
  let users = queue.users.map((x) => byId.get(x.id) || discover.find((u) => u.id === x.id) || { id: x.id, u: x.u, n: '', v: 0, p: 0, pic: '' });
  if (op === 'unfollow') users = users.filter((u) => gSet.has(u.id) && !prot.has(u.id));
  else users = users.filter((u) => !gSet.has(u.id) && !unf.has(u.id) && !fSet.has(u.id));
  launch(op, users);
});
$('#queue-clear').addEventListener('click', () => { queue = null; save(true); renderQueue(); toast('Fila limpa.'); });

$('#sel-all').addEventListener('change', (e) => {
  const arr = view();
  if (e.target.checked) arr.forEach((u) => sel.add(u.id)); else arr.forEach((u) => sel.delete(u.id));
  render();
});
$('#btn-more').addEventListener('click', () => { shown += PAGE; render(); });
for (const id of ['#q', '#f-ver', '#f-priv', '#f-sort']) $(id).addEventListener(id === '#q' ? 'input' : 'change', () => { shown = PAGE; save(); render(); });
// os campos mostram o valor que realmente vale (limite 1–150, pausa 20–120)
for (const [id, lo, hi] of [['#p-limit', 1, DAILY_MAX], ['#p-delay', MIN_DELAY, 120]]) {
  $(id).addEventListener('change', () => { $(id).value = clamp(parseInt($(id).value, 10) || lo, lo, hi); save(); });
}

$('#btn-csv').addEventListener('click', () => {
  const arr = view();
  if (!arr.length) { toast('Nada para exportar nesta lista.'); return; }
  const esc = (s) => '"' + String(s == null ? '' : s).replace(/"/g, '""') + '"';
  const csv = ['id,usuario,nome,verificada,privada'].concat(arr.map((u) => [u.id, u.u, esc(u.n), u.v ? 'sim' : 'não', u.p ? 'sim' : 'não'].join(','))).join('\r\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' }));
  a.download = 'ig-seguidores-' + tab + '-' + today() + '.csv';
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
});

$('#acct').addEventListener('change', (e) => switchAcct(e.target.value));
$('#p-incog').addEventListener('change', () => { save(true); toast($('#p-incog').checked ? 'Próxima janelinha abre em modo anônimo (login separado do Chrome).' : 'Atenção: a janelinha vai usar o login normal do seu Chrome.'); });

// dar nome à conta mostrada, se o @ não puder ser descoberto sozinho
$('#btn-name').addEventListener('click', () => {
  if (!acct) { toast('Nenhuma conta selecionada ainda. Clique em "Atualizar listas" primeiro.'); return; }
  const n = prompt('@ da conta ' + acct + ' (como você quer ver no seletor):', accts[acct] !== acct ? accts[acct] : '');
  if (n == null) return;
  const nome = n.replace(/^@+/, '').trim();
  if (!nome) return;
  accts[acct] = nome;
  renderAcctSelect();
  save(true);
});

// abre a janelinha do Instagram para entrar em outra conta; ao clicar em "Atualizar listas" o painel passa para ela
$('#btn-addacct').addEventListener('click', async () => {
  try {
    await igWindow(true, true); // pergunta qual conta
    // se a janelinha já abriu logada (login guardado), ensureIg descobre o @; sem login, não faz nada
    whoWhy = '';
    const r = await ensureIg().catch(() => null);
    const ok = !!r;
    if (r) await switchAcct(r.id, accts[r.id] !== r.id ? accts[r.id] : undefined); // o painel passa para a conta da janelinha
    if (whoWhy) { toast('Não consegui descobrir o @ desta conta (' + whoWhy + '). Use o botão ✎ para dar um nome a ela.'); return; }
    if (r) logEv('info', 'conta da janelinha: ' + (accts[r.id] || r.id));
    toast(ok ? 'Conta pronta: @' + (accts[r.id] || r.id) + '. Clique em "Atualizar listas".' : 'Entre na conta na janelinha do Instagram e depois clique em "Atualizar listas". O login fica guardado para a próxima vez.');
  } catch (e) {
    toast('Não consegui abrir o Instagram: ' + e.message);
    setStatus('Não consegui abrir o Instagram: ' + e.message); // fica na tela (o aviso some sozinho)
    logEv('erro', 'trocar conta: ' + e.message);
  }
});

// ----- botão Log: ver, copiar, baixar e limpar -----
$('#btn-log').addEventListener('click', async () => {
  $('#log-text').value = (await logText()) || '(vazio)';
  $('#logdlg').showModal();
  const t = $('#log-text'); t.scrollTop = t.scrollHeight;
});
$('#log-close').addEventListener('click', () => $('#logdlg').close());
$('#log-copy').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText($('#log-text').value); toast('Log copiado.'); } catch (_) { $('#log-text').select(); toast('Selecione e copie (Ctrl+C).'); }
});
$('#log-save').addEventListener('click', async () => {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([await logText()], { type: 'text/plain;charset=utf-8' }));
  a.download = 'ig-seguidores-log.txt';
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
});
$('#log-clear').addEventListener('click', async () => { await chrome.storage.local.remove('log'); $('#log-text').value = '(vazio)'; });

(async function init() {
  let inc = '?';
  try { inc = await chrome.extension.isAllowedIncognitoAccess(); } catch (_) {}
  logEv('info', 'painel aberto: v' + chrome.runtime.getManifest().version + ' • ID ' + chrome.runtime.id + ' • modo anônimo permitido: ' + inc + ' • ' + navigator.userAgent.replace(/.*Chrome\//, 'Chrome ').split(' ')[0]);
  await load();
  renderAcctSelect();
  derive();
  render();
})();
