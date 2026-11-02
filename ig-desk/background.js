// IG Desk — service worker
// Abre o Instagram numa janela própria (nível superior, sem iframe) e uma janela de ferramentas
// ao lado. Aplica o disfarce de celular só na aba do IG Desk e leva os comandos entre as duas.

const IG_HOME = 'https://www.instagram.com/';
const TOOLS_W = 420;
const SIZES = { mobile: { w: 440, h: 900 }, desktop: { w: 1100, h: 900 } };

const UA_MOBILE =
  'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 ' +
  '(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1';

const TYPES = [
  'main_frame', 'sub_frame', 'xmlhttprequest', 'script', 'stylesheet', 'image',
  'media', 'font', 'websocket', 'ping', 'other'
];

// ---------- estado ----------

let queue = Promise.resolve();
function serial(fn) {
  queue = queue.then(fn, fn);
  return queue;
}

async function getDesk() {
  const { desk = null } = await chrome.storage.session.get('desk');
  return desk;
}
const clearDesk = () => chrome.storage.session.remove('desk');

// toda alteração do estado passa por aqui (ler + gravar numa fila): sem isso, duas atualizações
// ao mesmo tempo apagam uma à outra. fn recebe o estado atual e devolve o novo (null = apagar).
let deskQueue = Promise.resolve();
function updateDesk(fn) {
  deskQueue = deskQueue.then(async () => {
    const next = fn(await getDesk());
    if (next === null) await clearDesk();
    else await chrome.storage.session.set({ desk: next });
    return next;
  }, () => {});
  return deskQueue;
}

// marca a aba como "já preparada" uma única vez; devolve true só para quem conseguiu marcar
async function claimMark(tabId) {
  let won = false;
  await updateDesk((d) => {
    if (d && d.tabId === tabId && !d.marked) { won = true; return { ...d, marked: true }; }
    return d;
  });
  return won;
}

async function getPrefs() {
  const p = await chrome.storage.local.get({ mode: 'mobile', zoom: 1, bounds: {} });
  return p;
}

async function winAlive(id) {
  if (id == null) return false;
  try { await chrome.windows.get(id); return true; } catch (_) { return false; }
}

// ---------- regras de rede (só para a aba do IG Desk) ----------

function rebuildRules() {
  return serial(async () => {
    const desk = await getDesk();
    const { mode } = await getPrefs();
    const existing = await chrome.declarativeNetRequest.getSessionRules();
    const addRules = [];
    if (desk && mode === 'mobile') {
      addRules.push({
        id: 2,
        priority: 1,
        action: {
          type: 'modifyHeaders',
          requestHeaders: [
            { header: 'user-agent', operation: 'set', value: UA_MOBILE },
            { header: 'sec-ch-ua', operation: 'remove' },
            { header: 'sec-ch-ua-mobile', operation: 'remove' },
            { header: 'sec-ch-ua-platform', operation: 'remove' },
            { header: 'sec-ch-ua-platform-version', operation: 'remove' },
            { header: 'sec-ch-ua-full-version-list', operation: 'remove' },
            { header: 'sec-ch-ua-model', operation: 'remove' }
          ]
        },
        condition: { tabIds: [desk.tabId], requestDomains: ['instagram.com'], resourceTypes: TYPES }
      });
    }
    await chrome.declarativeNetRequest.updateSessionRules({
      removeRuleIds: existing.map((r) => r.id),
      addRules
    });
  });
}

// ---------- janelas ----------

// O nome da janela (window.name) marca a aba como IG Desk e sobrevive às navegações dentro do
// instagram.com. Os scripts da extensão só agem nas abas com esse nome; abas normais não mudam.
async function markAndGo(tabId) {
  const { mode } = await getPrefs();
  await chrome.scripting.executeScript({
    target: { tabId }, world: 'MAIN',
    func: (n) => { window.name = n; location.replace('/'); },
    args: ['igdesk-' + mode]
  });
}

chrome.tabs.onUpdated.addListener(async (tabId, info, tab) => {
  if (info.status !== 'complete') return;
  if (!/instagram\.com\/robots\.txt/.test(tab.url || '')) return;
  if (!(await claimMark(tabId))) return;
  try {
    await markAndGo(tabId);
  } catch (_) {
    await updateDesk((d) => (d && d.tabId === tabId ? { ...d, marked: false } : d));
  }
});

async function applyZoom() {
  const desk = await getDesk();
  if (!desk) return;
  const { zoom } = await getPrefs();
  try {
    // por aba: o zoom não muda as suas outras abas do Instagram
    await chrome.tabs.setZoomSettings(desk.tabId, { mode: 'automatic', scope: 'per-tab' });
    await chrome.tabs.setZoom(desk.tabId, zoom);
  } catch (_) {}
}

async function openDesk() {
  const cur = await getDesk();
  if (cur && (await winAlive(cur.windowId))) {
    await chrome.windows.update(cur.windowId, { focused: true });
    if (await winAlive(cur.toolsWindowId)) await chrome.windows.update(cur.toolsWindowId, { focused: true });
    return;
  }
  if (cur) { await updateDesk(() => null); await rebuildRules(); }

  const { mode, bounds } = await getPrefs();
  const size = SIZES[mode];
  const b = bounds[mode] || {};
  const want = {
    type: 'popup', width: b.width || size.w, height: b.height || size.h,
    left: b.left ?? TOOLS_W + 40, top: b.top ?? 20, focused: false
  };
  let igWin;
  try {
    igWin = await chrome.windows.create({ url: IG_HOME + 'robots.txt', ...want });
  } catch (_) {
    // posição salva inválida (ex.: monitor desconectado)
    igWin = await chrome.windows.create({ url: IG_HOME + 'robots.txt', type: 'popup', width: size.w, height: size.h });
  }
  const tabId = igWin.tabs[0].id;
  await updateDesk(() => ({ tabId, windowId: igWin.id }));
  await rebuildRules();

  const toolsLeft = Math.max(0, (igWin.left ?? want.left) - TOOLS_W - 8);
  const toolsWin = await chrome.windows.create({
    url: 'app.html', type: 'popup', width: TOOLS_W, height: igWin.height || size.h,
    left: toolsLeft, top: igWin.top ?? want.top, focused: true
  });
  await updateDesk((d) => (d ? { ...d, toolsTabId: toolsWin.tabs[0].id, toolsWindowId: toolsWin.id } : d));
  await applyZoom();

  // se o robots.txt já terminou de carregar antes de o estado existir
  try {
    const t = await chrome.tabs.get(tabId);
    if (t.status === 'complete' && /robots\.txt/.test(t.url || '') && (await claimMark(tabId))) await markAndGo(tabId);
  } catch (_) {}
}

async function setMode(mode) {
  mode = mode === 'desktop' ? 'desktop' : 'mobile';
  await chrome.storage.local.set({ mode });
  const desk = await getDesk();
  if (!desk) return { ok: true };
  await rebuildRules();
  const { bounds } = await getPrefs();
  const b = bounds[mode] || {};
  try {
    await chrome.windows.update(desk.windowId, { width: b.width || SIZES[mode].w, height: b.height || SIZES[mode].h });
  } catch (_) {}
  await chrome.scripting.executeScript({
    target: { tabId: desk.tabId }, world: 'MAIN',
    func: (n) => { window.name = n; }, args: ['igdesk-' + mode]
  });
  await chrome.tabs.reload(desk.tabId);
  return { ok: true };
}

chrome.action.onClicked.addListener(() => { openDesk(); });

// guarda a posição/tamanho da janela do Instagram (separado por modo)
let boundsTimer = 0;
chrome.windows.onBoundsChanged.addListener((win) => {
  clearTimeout(boundsTimer);
  boundsTimer = setTimeout(async () => {
    const desk = await getDesk();
    if (!desk || win.id !== desk.windowId || win.state !== 'normal') return;
    const { left, top, width, height } = win;
    if (![left, top, width, height].every(Number.isFinite) || left < -5000 || top < -5000) return;
    const { mode, bounds } = await getPrefs();
    await chrome.storage.local.set({ bounds: { ...bounds, [mode]: { left, top, width, height } } });
  }, 400);
});

// fechar uma das janelas fecha a outra
chrome.windows.onRemoved.addListener(async (windowId) => {
  const desk = await getDesk();
  if (!desk) return;
  if (windowId !== desk.windowId && windowId !== desk.toolsWindowId) return;
  await updateDesk(() => null);
  await rebuildRules();
  const other = windowId === desk.windowId ? desk.toolsWindowId : desk.windowId;
  if (other != null) { try { await chrome.windows.remove(other); } catch (_) {} }
});

// ---------- mensagens ----------

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  // mensagens da página do Instagram para a janela de ferramentas: quem as lê é o app.html
  if (!msg || msg.__igd) return false;

  (async () => {
    const desk = await getDesk();
    switch (msg.type) {
      case 'toPage': {
        if (!desk) return { ok: false, error: 'A janela do Instagram não está aberta.' };
        try {
          await chrome.tabs.sendMessage(desk.tabId, { __igd: 1, cmd: msg.cmd, ...(msg.extra || {}) });
          return { ok: true };
        } catch (e) {
          return { ok: false, error: 'O Instagram ainda está carregando. Tente de novo em instantes.' };
        }
      }
      case 'toolsReady': {
        const p = await getPrefs();
        return { ok: true, open: !!desk, mode: p.mode, zoom: p.zoom };
      }
      case 'setMode': return setMode(msg.mode);
      case 'setZoom': {
        const zoom = Math.min(1.5, Math.max(0.6, Number(msg.zoom) || 1));
        await chrome.storage.local.set({ zoom });
        await applyZoom();
        return { ok: true, zoom };
      }
      case 'reloadPage': {
        if (desk) await chrome.tabs.reload(desk.tabId);
        return { ok: true };
      }
      case 'openTab': {
        if (!desk) return { ok: false };
        const t = await chrome.tabs.get(desk.tabId);
        if (/^https:\/\/([a-z0-9-]+\.)*instagram\.com\//i.test(t.url || '')) await chrome.tabs.create({ url: t.url });
        return { ok: true };
      }
      case 'openShortcuts': {
        await chrome.tabs.create({ url: 'chrome://extensions/shortcuts' });
        return { ok: true };
      }
      case 'focusPage': {
        if (desk) await chrome.windows.update(desk.windowId, { focused: true });
        return { ok: true };
      }
      case 'focusTools': {
        if (desk && desk.toolsWindowId != null) await chrome.windows.update(desk.toolsWindowId, { focused: true, drawAttention: true });
        return { ok: true };
      }
      default:
        return { ok: false };
    }
  })().then(sendResponse, (e) => sendResponse({ ok: false, error: String(e) }));
  return true;
});

async function startup() { await rebuildRules(); }
chrome.runtime.onInstalled.addListener(() => { startup(); });
chrome.runtime.onStartup.addListener(() => { startup(); });
