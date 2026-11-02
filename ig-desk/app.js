// IG Desk — janela de ferramentas
// O Instagram roda na outra janela (nível superior). Aqui ficam a barra lateral, o Crescimento,
// o editor de story e o diagnóstico; os comandos vão para a página pelo background.

const DEFAULTS = {
  mode: 'mobile',
  darkMode: false,
  videoControls: true,
  rememberVolume: true,
  zoom: 1
};

const $ = (s) => document.querySelector(s);
const panel = $('#panel');

let settings = { ...DEFAULTS };
let currentUrl = '';
let gotHello = false;
let staleReloaded = false;
let diagTimer = 0;
let pingTimer = 0;

// qualquer erro de JavaScript desta janela aparece na tela (e não só no console)
window.addEventListener('error', (e) => toast('Erro: ' + e.message));
window.addEventListener('unhandledrejection', (e) => {
  toast('Erro: ' + ((e.reason && e.reason.message) || e.reason));
});

// ---------------- comunicação com a página do Instagram ----------------

// mensagens da extensão só levam JSON: o arquivo vai como { name, type, base64 }
function fileToPayload(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => {
      const s = String(r.result);
      resolve({ name: file.name, type: file.type, base64: s.slice(s.indexOf(',') + 1) });
    };
    r.onerror = () => reject(r.error);
    r.readAsDataURL(file);
  });
}

// o contrário: { name, type, base64 } vindo da página do Instagram volta a ser um arquivo
function payloadToFile(p) {
  const bin = atob(p.base64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new File([bytes], p.name || 'story.jpg', { type: p.type || 'image/jpeg' });
}

async function sendToFrame(cmd, extra = {}) {
  const payload = { ...extra };
  if (payload.file instanceof Blob) payload.file = await fileToPayload(payload.file);
  const res = await chrome.runtime.sendMessage({ type: 'toPage', cmd, extra: payload }).catch(() => null);
  if ((!res || !res.ok) && cmd !== 'ping') toast((res && res.error) || 'A janela do Instagram não respondeu.');
  return res;
}

function setConn(state, text) {
  const c = $('#conn');
  c.classList.toggle('ok', state === 'ok');
  c.classList.toggle('bad', state === 'bad');
  $('#conn-text').textContent = text;
}

// mensagens que a página do Instagram envia (hello, url, toast, diag, auto)
chrome.runtime.onMessage.addListener((d, sender) => {
  if (!d || !d.__igd || !sender.tab) return;
  switch (d.type) {
    case 'hello':
      // script antigo na página (extensão atualizada com a janela aberta): recarrega uma vez
      if (d.v !== chrome.runtime.getManifest().version && !staleReloaded) {
        staleReloaded = true;
        toast('Atualizando a página do Instagram para a versão nova…');
        chrome.runtime.sendMessage({ type: 'reloadPage' });
        break;
      }
      gotHello = true;
      setConn('ok', 'Instagram conectado');
      if (d.url) setUrl(d.url);
      if (autoRunning) {
        // a página recarregou: o script que estava seguindo/deixando de seguir morreu junto
        setAuto(false);
        setAutoStatus('Interrompido: a página do Instagram recarregou.', 0);
      }
      break;
    case 'auto':
      handleAuto(d);
      break;
    case 'url':
      if (!gotHello) { gotHello = true; setConn('ok', 'Instagram conectado'); }
      setUrl(d.url);
      break;
    case 'toast':
      toast(d.text);
      break;
    case 'editStory':
      // botão "Efeitos e adesivos" na tela de story do Instagram
      if (d.file) openEditor(payloadToFile(d.file));
      break;
    case 'diag':
      clearTimeout(diagTimer);
      showDiag(d.text, copyText(d.text)
        ? 'Copiado para a área de transferência. Cole na conversa (Ctrl+V).'
        : 'Clique em Copiar (ou selecione o texto e use Ctrl+C).');
      break;
  }
});

function setUrl(url) {
  if (typeof url !== 'string' || !url.startsWith('https://')) return;
  currentUrl = url;
  let path = '/';
  try { path = new URL(url).pathname; } catch (_) {}
  $('#conn-url').textContent = 'Página: ' + path;
  document.querySelectorAll('[data-go]').forEach((b) => {
    const p = b.dataset.go;
    const on = p === '/' ? path === '/' : path.startsWith(p);
    b.classList.toggle('on', on);
  });
}

// ---------------- zoom e modo celular / computador ----------------

function setZoom(z) {
  z = Math.round(Math.min(1.5, Math.max(0.6, z)) * 10) / 10;
  settings.zoom = z;
  $('#z-val').textContent = Math.round(z * 100) + '%';
  chrome.runtime.sendMessage({ type: 'setZoom', zoom: z });
}

function modeTitle(mode) {
  return mode === 'mobile'
    ? 'Modo celular (clique para modo computador)'
    : 'Modo computador (clique para modo celular)';
}

async function setMode(mode) {
  settings.mode = mode;
  document.body.classList.toggle('desktop', mode === 'desktop');
  $('#btn-mode').title = modeTitle(mode);
  gotHello = false;
  setConn('', 'Trocando de modo…');
  await chrome.runtime.sendMessage({ type: 'setMode', mode });
  toast(mode === 'mobile' ? 'Modo celular' : 'Modo computador');
  startPing();
}

// ---------------- dark mode ----------------

function setDark(on) {
  settings.darkMode = on;
  $('#btn-dark').classList.toggle('on', on);
  chrome.storage.local.set({ darkMode: on });
}

// ---------------- toast ----------------

let toastTimer = 0;
function toast(text) {
  const t = $('#toast');
  t.textContent = text;
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, 3200);
}

// ---------------- eventos da UI ----------------

document.querySelectorAll('[data-cmd]').forEach((b) => {
  b.addEventListener('click', () => {
    const cmd = b.dataset.cmd;
    if (cmd === 'reload') { chrome.runtime.sendMessage({ type: 'reloadPage' }); return; }
    if (cmd === 'create' || cmd === 'story') {
      // story só existe no layout de celular; publicação (post/reel), só no de computador
      const need = cmd === 'story' ? 'mobile' : 'desktop';
      if (settings.mode !== need) {
        const nome = need === 'mobile' ? 'celular' : 'computador';
        const oque = cmd === 'story' ? 'Story' : 'Publicação (post ou reel)';
        if (confirm(oque + ' só existe no layout de ' + nome + ' do Instagram.\n\nTrocar para o modo ' + nome + ' agora?')) setMode(need);
        return;
      }
      // o seletor de arquivos abre aqui (clique real); o arquivo é entregue ao Instagram
      if (!gotHello) { toast('Espere o Instagram carregar e entre na sua conta.'); return; }
      pickCmd = cmd;
      $('#pick').click();
      return;
    }
    sendToFrame(cmd);
  });
});

let pickCmd = '';
$('#pick').addEventListener('change', () => {
  const file = $('#pick').files[0];
  $('#pick').value = '';
  if (!file || !pickCmd) return;
  // foto para story passa pelo editor (efeitos, texto, hashtags, emojis); vídeo vai direto
  if (pickCmd === 'story' && file.type.startsWith('image/')) { openEditor(file); return; }
  toast(pickCmd === 'story' ? 'Enviando ao story…' : 'Enviando à publicação…');
  sendToFrame(pickCmd, { file });
});

function showDiag(text, hint) {
  $('#dlg-text').value = text;
  $('#dlg-hint').textContent = hint;
  $('#dlg').hidden = false;
  $('#dlg-text').focus();
  $('#dlg-text').select();
}

$('#btn-diag').addEventListener('click', () => {
  panel.hidden = true;
  $('#btn-settings').classList.remove('on');
  sendToFrame('diag');
  // sem resposta = a página do Instagram está com o script antigo (ou ainda carregando)
  clearTimeout(diagTimer);
  diagTimer = setTimeout(() => {
    showDiag(
      [
        'IG Desk diagnóstico (SEM resposta do Instagram)',
        'versão da extensão: ' + chrome.runtime.getManifest().version,
        'Instagram conectado (hello): ' + gotHello,
        'url: ' + currentUrl,
        'modo: ' + settings.mode
      ].join('\n'),
      'O Instagram não respondeu. Feche as duas janelas do IG Desk e abra de novo; se persistir, cole este texto na conversa.'
    );
  }, 2500);
});
$('#dlg-close').addEventListener('click', () => { $('#dlg').hidden = true; });
$('#dlg-copy').addEventListener('click', () => {
  $('#dlg-text').select();
  toast(copyText($('#dlg-text').value) ? 'Copiado.' : 'Não consegui copiar: use Ctrl+C no texto selecionado.');
});

function copyText(text) {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.cssText = 'position:fixed;left:-9999px;top:0';
  document.body.appendChild(ta);
  ta.select();
  let ok = false;
  try { ok = document.execCommand('copy'); } catch (_) {}
  ta.remove();
  return ok;
}

document.querySelectorAll('[data-go]').forEach((b) => {
  b.addEventListener('click', () => sendToFrame('go', { path: b.dataset.go }));
});

$('#btn-mode').addEventListener('click', () => setMode(settings.mode === 'mobile' ? 'desktop' : 'mobile'));
$('#btn-dark').addEventListener('click', () => setDark(!settings.darkMode));
$('#btn-tab').addEventListener('click', () => chrome.runtime.sendMessage({ type: 'openTab' }));
$('#b-reload').addEventListener('click', () => chrome.runtime.sendMessage({ type: 'reloadPage' }));
$('#b-focus').addEventListener('click', () => chrome.runtime.sendMessage({ type: 'focusPage' }));
$('#b-story').addEventListener('click', () => document.querySelector('[data-cmd="story"]').click());

$('#btn-settings').addEventListener('click', (e) => {
  e.stopPropagation();
  panel.hidden = !panel.hidden;
  if (!panel.hidden) { autopanel.hidden = true; $('#btn-auto').classList.toggle('on', autoRunning); }
  $('#btn-settings').classList.toggle('on', !panel.hidden);
});
document.addEventListener('click', (e) => {
  if (!panel.hidden && !panel.contains(e.target)) {
    panel.hidden = true;
    $('#btn-settings').classList.remove('on');
  }
});

for (const key of ['videoControls', 'rememberVolume']) {
  const el = $('#opt-' + key);
  el.addEventListener('change', () => {
    settings[key] = el.checked;
    chrome.storage.local.set({ [key]: el.checked });
  });
}
$('#z-in').addEventListener('click', () => setZoom(settings.zoom + 0.1));
$('#z-out').addEventListener('click', () => setZoom(settings.zoom - 0.1));
$('#btn-shortcut').addEventListener('click', () => chrome.runtime.sendMessage({ type: 'openShortcuts' }));

// ---------------- crescimento (seguir / deixar de seguir) ----------------

const autopanel = $('#autopanel');
const AUTO_LABELS = {
  unfollow: 'Deixar de seguir quem não te segue',
  followback: 'Seguir de volta quem te segue',
  followNew: 'Seguir pessoas novas'
};
let autoRunning = false;
let autoCtx = null;

const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n));

function setAuto(running) {
  autoRunning = running;
  document.querySelectorAll('[data-auto]').forEach((b) => { b.disabled = running; });
  $('#auto-stop').disabled = !running;
  $('#btn-auto').classList.toggle('on', running || !autopanel.hidden);
}

function setAutoStatus(text, pct) {
  $('#auto-status').textContent = text;
  $('#auto-bar').style.width = clamp(pct || 0, 0, 100) + '%';
}

function handleAuto(d) {
  switch (d.state) {
    case 'collecting':
      setAutoStatus(d.text, 0);
      break;
    case 'ready': {
      const c = autoCtx || {};
      const mins = Math.max(1, Math.round((d.total * (c.minDelay || 30) * 1.3) / 60));
      const ex = (d.sample || []).map((u) => '@' + u).join(', ');
      const ok = confirm(
        `${AUTO_LABELS[c.task] || 'Automação'}\n\n` +
        `${d.total} conta(s) serão processadas (ex.: ${ex}).\n` +
        `Com pausas de ~${c.minDelay || 30}s, leva cerca de ${mins} min. Não feche nem recarregue a janela.\n\n` +
        'Continuar?'
      );
      setAutoStatus(ok ? 'Executando…' : 'Cancelado.', 0);
      sendToFrame(ok ? 'autoGo' : 'autoStop');
      break;
    }
    case 'running':
      setAutoStatus(d.text, d.total ? (d.done / d.total) * 100 : 0);
      break;
    case 'done':
    case 'stopped':
    case 'error':
      setAuto(false);
      setAutoStatus(d.text, d.state === 'done' ? 100 : 0);
      if (d.state === 'error') toast(d.text);
      break;
  }
}

document.querySelectorAll('[data-auto]').forEach((b) => {
  b.addEventListener('click', () => {
    if (!gotHello) { toast('Espere o Instagram carregar e entre na sua conta.'); return; }
    const delay = clamp(parseInt($('#auto-delay').value, 10) || 30, 20, 120);
    autoCtx = {
      task: b.dataset.auto,
      limit: clamp(parseInt($('#auto-limit').value, 10) || 40, 1, 150),
      minDelay: delay,
      maxDelay: Math.round(delay * 1.6),
      skipVerified: $('#auto-verified').checked,
      source: $('#auto-source').value.trim()
    };
    setAuto(true);
    setAutoStatus('Preparando…', 0);
    sendToFrame('auto', { opts: autoCtx });
  });
});

$('#auto-stop').addEventListener('click', () => {
  sendToFrame('autoStop');
  setAutoStatus('Parando…', 0);
});

$('#btn-auto').addEventListener('click', (e) => {
  e.stopPropagation();
  autopanel.hidden = !autopanel.hidden;
  if (!autopanel.hidden) { panel.hidden = true; $('#btn-settings').classList.remove('on'); }
  $('#btn-auto').classList.toggle('on', autoRunning || !autopanel.hidden);
});
$('#auto-close').addEventListener('click', () => {
  autopanel.hidden = true;
  $('#btn-auto').classList.toggle('on', autoRunning);
});

// ---------------- editor de story ----------------
// Efeitos, texto, #hashtags, @menções, emojis e desenho são gravados na própria imagem
// (1080x1920) e ela é entregue ao Instagram. Não são os adesivos interativos do app.

const ED_W = 1080;
const ED_H = 1920;
const FILTERS = {
  'Normal': 'none',
  'P&B': 'grayscale(1)',
  'Sépia': 'sepia(.85)',
  'Vívido': 'saturate(1.7) contrast(1.1)',
  'Frio': 'sepia(.15) hue-rotate(170deg) saturate(1.25)',
  'Quente': 'sepia(.35) saturate(1.5) hue-rotate(-12deg)',
  'Vintage': 'sepia(.5) contrast(.92) brightness(1.08) saturate(.8)',
  'Drama': 'contrast(1.4) saturate(.9) brightness(.92)',
  'Esmaecido': 'contrast(.82) brightness(1.12) saturate(.75)'
};
const EMOJIS = ['😍', '😂', '🔥', '❤️', '✨', '🎉', '😎', '🙌', '👏', '💯', '🥳', '😭',
  '🤩', '💪', '🙏', '🌈', '⭐', '🎶', '📍', '☀️', '🌙', '💋', '🍕', '🎂'];

const edEl = $('#ed');
const cv = $('#ed-canvas');
const ed = {
  file: null, img: null, items: [], sel: -1, filter: 'none', filterName: 'Normal',
  bright: 100, fit: 'contain', pen: false, drag: null, boxes: []
};

function roundRect(g, x, y, w, h, r) {
  g.beginPath();
  g.moveTo(x + r, y);
  g.arcTo(x + w, y, x + w, y + h, r);
  g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r);
  g.arcTo(x, y, x + w, y, r);
  g.closePath();
}

const isLight = (hex) => {
  const n = parseInt(hex.slice(1), 16);
  return (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255 > 0.6;
};

function edRender(showSelection = true) {
  const g = cv.getContext('2d');
  g.save();
  g.filter = 'none';
  g.fillStyle = '#000';
  g.fillRect(0, 0, ED_W, ED_H);

  if (ed.img) {
    const iw = ed.img.width, ih = ed.img.height;
    const filt = (ed.filter === 'none' ? '' : ed.filter + ' ') + 'brightness(' + ed.bright + '%)';
    const draw = (s) => g.drawImage(ed.img, (ED_W - iw * s) / 2, (ED_H - ih * s) / 2, iw * s, ih * s);
    if (ed.fit === 'contain') {
      g.filter = 'blur(40px) brightness(70%)';
      draw(Math.max(ED_W / iw, ED_H / ih) * 1.12);
      g.filter = filt;
      draw(Math.min(ED_W / iw, ED_H / ih));
    } else {
      g.filter = filt;
      draw(Math.max(ED_W / iw, ED_H / ih));
    }
    g.filter = 'none';
  }

  ed.boxes = [];
  ed.items.forEach((it, i) => {
    if (it.type === 'sticker') {
      const b = drawSticker(g, it);
      ed.boxes[i] = b;
      if (showSelection && i === ed.sel) {
        g.strokeStyle = '#fff';
        g.lineWidth = 4;
        g.setLineDash([16, 12]);
        g.strokeRect(b.x - 8, b.y - 8, b.w + 16, b.h + 16);
        g.setLineDash([]);
      }
      return;
    }
    if (it.type === 'img') {
      const h = it.size, w = it.bmp.width * (h / it.bmp.height);
      g.drawImage(it.bmp, it.x - w / 2, it.y - h / 2, w, h);
      ed.boxes[i] = { x: it.x - w / 2, y: it.y - h / 2, w, h };
      if (showSelection && i === ed.sel) {
        g.strokeStyle = '#fff';
        g.lineWidth = 4;
        g.setLineDash([16, 12]);
        g.strokeRect(ed.boxes[i].x, ed.boxes[i].y, ed.boxes[i].w, ed.boxes[i].h);
        g.setLineDash([]);
      }
      return;
    }
    if (it.type === 'draw') {
      g.strokeStyle = it.color;
      g.lineWidth = it.size;
      g.lineCap = 'round';
      g.lineJoin = 'round';
      g.beginPath();
      it.pts.forEach((p, k) => (k ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])));
      if (it.pts.length === 1) g.lineTo(it.pts[0][0] + 0.1, it.pts[0][1]);
      g.stroke();
      ed.boxes[i] = null;
      return;
    }
    let fs = it.size;
    const setFont = () => { g.font = '700 ' + fs + 'px "Segoe UI","Segoe UI Emoji","Apple Color Emoji",system-ui,sans-serif'; };
    setFont();
    while (g.measureText(it.text).width > ED_W * 0.92 && fs > 24) { fs -= 4; setFont(); }
    const w = g.measureText(it.text).width, h = fs * 1.3, pad = fs * 0.3;
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    if (it.bg) {
      g.fillStyle = isLight(it.color) ? 'rgba(0,0,0,.62)' : 'rgba(255,255,255,.92)';
      roundRect(g, it.x - w / 2 - pad, it.y - h / 2, w + pad * 2, h, fs * 0.25);
      g.fill();
    }
    g.fillStyle = it.color;
    g.fillText(it.text, it.x, it.y + fs * 0.04);
    ed.boxes[i] = { x: it.x - w / 2 - pad, y: it.y - h / 2, w: w + pad * 2, h };
    if (showSelection && i === ed.sel) {
      g.strokeStyle = '#fff';
      g.lineWidth = 4;
      g.setLineDash([16, 12]);
      g.strokeRect(ed.boxes[i].x, ed.boxes[i].y, ed.boxes[i].w, ed.boxes[i].h);
      g.setLineDash([]);
    }
  });
  g.restore();
}

async function openEditor(file) {
  let img;
  try {
    img = await createImageBitmap(file);
  } catch (_) {
    toast('Não consegui abrir essa imagem aqui (HEIC?). Enviando o original.');
    sendToFrame('story', { file });
    return;
  }
  Object.assign(ed, {
    file, img, items: [], sel: -1, filter: 'none', filterName: 'Normal',
    bright: 100, fit: 'contain', pen: false, drag: null
  });
  $('#ed-bright').value = 100;
  $('#ed-fit').value = 'contain';
  $('#ed-text').value = '';
  $('#ed-pen').textContent = 'Lápis: desligado';
  $('#ed-pen').classList.remove('on');
  cv.style.cursor = 'grab';
  document.querySelectorAll('#ed-filters button').forEach((b) => b.classList.toggle('on', b.textContent === 'Normal'));
  edEl.hidden = false;
  edRender();
}

function closeEditor() {
  edEl.hidden = true;
  ed.img = null;
  ed.file = null;
}

function edExport() {
  const prev = ed.sel;
  ed.sel = -1;
  edRender(false);
  return new Promise((resolve) => cv.toBlob((blob) => {
    ed.sel = prev;
    edRender();
    resolve(blob);
  }, 'image/jpeg', 0.92));
}

function edAddText(text, opts = {}) {
  const n = ed.items.filter((i) => i.type === 'text').length;
  ed.items.push({
    type: 'text', text,
    x: ED_W / 2, y: ED_H / 2 + ((n % 7) - 3) * 140,
    size: opts.size || Number($('#ed-size').value),
    color: opts.color || $('#ed-color').value,
    bg: opts.bg !== undefined ? opts.bg : $('#ed-bg').checked
  });
  ed.sel = ed.items.length - 1;
  edRender();
}

// ----- painel de ferramentas -----
for (const [name, css] of Object.entries(FILTERS)) {
  const b = document.createElement('button');
  b.textContent = name;
  if (name === 'Normal') b.classList.add('on');
  b.addEventListener('click', () => {
    ed.filter = css;
    ed.filterName = name;
    document.querySelectorAll('#ed-filters button').forEach((x) => x.classList.toggle('on', x === b));
    edRender();
  });
  $('#ed-filters').appendChild(b);
}
for (const em of EMOJIS) {
  const b = document.createElement('button');
  b.textContent = em;
  b.setAttribute('aria-label', 'Emoji ' + em);
  b.addEventListener('click', () => edAddText(em, { size: 220, bg: false }));
  $('#ed-emojis').appendChild(b);
}

$('#ed-bright').addEventListener('input', (e) => { ed.bright = Number(e.target.value); edRender(); });
$('#ed-fit').addEventListener('change', (e) => { ed.fit = e.target.value; edRender(); });

$('#ed-add').addEventListener('click', () => {
  const t = $('#ed-text').value.trim();
  if (!t) { toast('Digite o texto primeiro.'); return; }
  edAddText(t);
  $('#ed-text').value = '';
});
$('#ed-text').addEventListener('keydown', (e) => { if (e.key === 'Enter') $('#ed-add').click(); });
document.querySelectorAll('[data-ins]').forEach((b) => {
  b.addEventListener('click', () => {
    const t = $('#ed-text');
    t.value = b.dataset.ins;
    t.focus();
    t.setSelectionRange(t.value.length, t.value.length);
  });
});

// o controle serve a texto/emoji (tamanho da fonte) e a figurinhas (altura = valor x 5)
$('#ed-size').addEventListener('input', (e) => {
  const it = ed.items[ed.sel];
  if (!it) return;
  if (it.type === 'text') { it.size = Number(e.target.value); edRender(); }
  else if (it.type === 'img') { it.size = Number(e.target.value) * 5; edRender(); }
  else if (it.type === 'sticker') { it.scale = Number(e.target.value) / 90; edRender(); }
});

$('#ed-sticker').addEventListener('click', () => $('#ed-sticker-file').click());
$('#ed-sticker-file').addEventListener('change', async () => {
  const f = $('#ed-sticker-file').files[0];
  $('#ed-sticker-file').value = '';
  if (!f || !ed.img) return;
  try {
    const bmp = await createImageBitmap(f); // GIF: primeiro quadro
    ed.items.push({ type: 'img', bmp, x: ED_W / 2, y: ED_H / 2, size: 600 });
    ed.sel = ed.items.length - 1;
    $('#ed-size').value = 120;
    edRender();
  } catch (_) {
    toast('Não consegui abrir essa imagem.');
  }
});
$('#ed-del').addEventListener('click', () => {
  if (ed.sel < 0) { toast('Toque num texto ou emoji da imagem para selecioná-lo.'); return; }
  ed.items.splice(ed.sel, 1);
  ed.sel = -1;
  edRender();
});
$('#ed-undo').addEventListener('click', () => { ed.items.pop(); ed.sel = -1; edRender(); });
$('#ed-pen').addEventListener('click', () => {
  ed.pen = !ed.pen;
  $('#ed-pen').textContent = 'Lápis: ' + (ed.pen ? 'ligado' : 'desligado');
  $('#ed-pen').classList.toggle('on', ed.pen);
  cv.style.cursor = ed.pen ? 'crosshair' : 'grab';
  if (ed.pen) ed.sel = -1;
  edRender();
});

// ----- arrastar itens e desenhar na imagem -----
const edPos = (e) => {
  const r = cv.getBoundingClientRect();
  return [(e.clientX - r.left) * ED_W / r.width, (e.clientY - r.top) * ED_H / r.height];
};
cv.addEventListener('pointerdown', (e) => {
  if (!ed.img) return;
  const [x, y] = edPos(e);
  cv.setPointerCapture(e.pointerId);
  if (ed.pen) {
    ed.items.push({ type: 'draw', color: $('#ed-pcolor').value, size: Number($('#ed-psize').value), pts: [[x, y]] });
    ed.drag = { mode: 'pen' };
    edRender();
    return;
  }
  let hit = -1;
  for (let i = ed.items.length - 1; i >= 0; i--) {
    const b = ed.boxes[i];
    if (b && x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h) { hit = i; break; }
  }
  ed.sel = hit;
  if (hit >= 0) {
    const it = ed.items[hit];
    ed.drag = { mode: 'move', dx: it.x - x, dy: it.y - y };
    $('#ed-size').value = it.type === 'img' ? it.size / 5 : it.type === 'sticker' ? it.scale * 90 : it.size;
  }
  edRender();
});
cv.addEventListener('pointermove', (e) => {
  if (!ed.drag) return;
  const [x, y] = edPos(e);
  if (ed.drag.mode === 'pen') {
    ed.items[ed.items.length - 1].pts.push([x, y]);
  } else {
    const it = ed.items[ed.sel];
    if (!it) return;
    it.x = x + ed.drag.dx;
    it.y = y + ed.drag.dy;
  }
  edRender();
});
const edDragEnd = () => { ed.drag = null; };
cv.addEventListener('pointerup', edDragEnd);
cv.addEventListener('pointercancel', edDragEnd);

document.addEventListener('keydown', (e) => {
  if (edEl.hidden) return;
  if (e.key === 'Escape') closeEditor();
  else if (e.key === 'Delete' && ed.sel >= 0 && document.activeElement.tagName !== 'INPUT') $('#ed-del').click();
});

// ----- enviar -----
$('#ed-post').addEventListener('click', async () => {
  const blob = await edExport();
  if (!blob) { toast('Não consegui gerar a imagem.'); return; }
  const file = new File([blob], 'story.jpg', { type: 'image/jpeg' });
  closeEditor();
  toast('Abrindo o story no Instagram…');
  sendToFrame('story', { file });
});
$('#ed-raw').addEventListener('click', () => {
  const file = ed.file;
  closeEditor();
  if (file) { toast('Abrindo o story (original)…'); sendToFrame('story', { file }); }
});
$('#ed-cancel').addEventListener('click', closeEditor);

// ---------------- adesivos (só visuais) ----------------
// Cada adesivo é desenhado no canvas e gravado na imagem. Os que dependem do app do Instagram
// (enquete, perguntas, link, contagem, música, sua vez) ficam só no visual: não funcionam.

const STK_FONT = '"Segoe UI","Segoe UI Emoji","Apple Color Emoji",system-ui,sans-serif';
const stkFont = (g, px, weight = 800) => { g.font = weight + ' ' + px + 'px ' + STK_FONT; };

function stkGrad(g, w, colors) {
  const gr = g.createLinearGradient(-w / 2, 0, w / 2, 0);
  colors.forEach((c, i) => gr.addColorStop(colors.length === 1 ? 0 : i / (colors.length - 1), c));
  return gr;
}

// reduz a fonte até o texto caber em maxW; devolve a largura final
function stkFit(g, text, px, maxW, weight = 800) {
  let s = px;
  stkFont(g, s, weight);
  while (g.measureText(text).width > maxW && s > 18) { s -= 2; stkFont(g, s, weight); }
  return { px: s, w: g.measureText(text).width };
}

function stkShadow(g, on) {
  g.shadowColor = on ? 'rgba(0,0,0,.28)' : 'transparent';
  g.shadowBlur = on ? 22 : 0;
  g.shadowOffsetY = on ? 6 : 0;
}

// pílula com texto (Localização, Menção, Hashtag, Data...)
function stkPill(g, text, px, colors, bg) {
  const f = stkFit(g, text, px, 900);
  const w = f.w + px * 1.5, h = px * 1.95;
  stkShadow(g, true);
  roundRect(g, -w / 2, -h / 2, w, h, h / 2);
  g.fillStyle = bg || '#fff';
  g.fill();
  stkShadow(g, false);
  g.fillStyle = Array.isArray(colors) ? stkGrad(g, f.w, colors) : colors;
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.fillText(text, 0, px * 0.05);
  return { w, h };
}

function stkCard(g, w, h, r) {
  stkShadow(g, true);
  roundRect(g, -w / 2, -h / 2, w, h, r);
  g.fillStyle = '#fff';
  g.fill();
  stkShadow(g, false);
}

function stkCountdown(dateStr) {
  const t = new Date(dateStr + 'T00:00:00').getTime();
  let ms = isFinite(t) ? Math.max(0, t - Date.now()) : 0;
  const d = Math.floor(ms / 864e5); ms -= d * 864e5;
  const h = Math.floor(ms / 36e5); ms -= h * 36e5;
  const m = Math.floor(ms / 6e4); ms -= m * 6e4;
  const s = Math.floor(ms / 1e3);
  const p = (n) => String(n).padStart(2, '0');
  return [[p(d), 'DIAS'], [p(h), 'HORAS'], [p(m), 'MIN'], [p(s), 'SEG']];
}

// desenha o adesivo centrado em (it.x, it.y) na escala it.scale; devolve a caixa na tela
function drawSticker(g, it) {
  const k = it.kind, d = it.data || {};
  g.save();
  g.translate(it.x, it.y);
  g.scale(it.scale, it.scale);
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  let w = 400, h = 120;
  const up = (s) => String(s || '').toUpperCase();

  if (k === 'loc') ({ w, h } = stkPill(g, '📍 ' + up(d.text || 'Localização'), 62, ['#8134af', '#dd2a7b', '#f58529']));
  else if (k === 'mention') ({ w, h } = stkPill(g, '@' + String(d.text || 'usuario').replace(/^@/, ''), 62, ['#f58529', '#dd2a7b']));
  else if (k === 'hashtag') ({ w, h } = stkPill(g, '#' + String(d.text || 'hashtag').replace(/^#/, ''), 62, ['#3897f0', '#0a58b8']));
  else if (k === 'suavez') ({ w, h } = stkPill(g, '📷 ' + up(d.text || 'Sua vez'), 62, '#fff', '#e1306c'));
  else if (k === 'link') ({ w, h } = stkPill(g, '🔗 ' + up(d.text || 'Link'), 62, '#1d9bf0'));
  else if (k === 'data') ({ w, h } = stkPill(g, up(d.text), 62, '#111'));
  else if (k === 'hora') ({ w, h } = stkPill(g, d.text, 62, '#111'));
  else if (k === 'temp') ({ w, h } = stkPill(g, '☀️ ' + d.text, 62, '#111'));
  else if (k === 'perguntas') {
    w = 780; h = 340;
    stkCard(g, w, h, 46);
    g.save();
    roundRect(g, -w / 2, -h / 2, w, h, 46);
    g.clip();
    const gr = g.createLinearGradient(-w / 2, -h / 2, w / 2, 0);
    gr.addColorStop(0, '#833ab4'); gr.addColorStop(.55, '#fd1d1d'); gr.addColorStop(1, '#fcb045');
    g.fillStyle = gr;
    g.fillRect(-w / 2, -h / 2, w, 190);
    g.restore();
    const f = stkFit(g, d.q || 'Faça uma pergunta', 54, w - 110);
    g.fillStyle = '#fff';
    g.fillText(d.q || 'Faça uma pergunta', 0, -h / 2 + 95);
    roundRect(g, -w / 2 + 40, h / 2 - 125, w - 80, 85, 24);
    g.fillStyle = '#efefef';
    g.fill();
    stkFont(g, 36, 600);
    g.fillStyle = '#8e8e8e';
    g.textAlign = 'left';
    g.fillText('Escreva algo...', -w / 2 + 70, h / 2 - 82);
    g.textAlign = 'center';
  } else if (k === 'enquete') {
    w = 800; h = 360;
    stkCard(g, w, h, 46);
    const f = stkFit(g, d.q || 'Enquete', 56, w - 100);
    g.fillStyle = '#1c1e21';
    g.fillText(d.q || 'Enquete', 0, -h / 2 + 80);
    [[-1, d.a || 'Sim', '#0095f6'], [1, d.b || 'Não', '#ed4956']].forEach(([side, label, color]) => {
      const bw = 340, bh = 130, bx = side * 188;
      roundRect(g, bx - bw / 2, 20, bw, bh, 30);
      g.fillStyle = '#f2f3f5';
      g.fill();
      stkFit(g, label, 52, bw - 40);
      g.fillStyle = color;
      g.fillText(label, bx, 20 + bh / 2 + 2);
    });
  } else if (k === 'slider') {
    w = 780; h = 270;
    stkCard(g, w, h, 46);
    stkFit(g, d.q || 'Você gosta?', 52, w - 100);
    g.fillStyle = '#1c1e21';
    g.fillText(d.q || 'Você gosta?', 0, -h / 2 + 72);
    const tw = w - 150, ty = 52;
    roundRect(g, -tw / 2, ty - 12, tw, 24, 12);
    const gr = g.createLinearGradient(-tw / 2, 0, tw / 2, 0);
    gr.addColorStop(0, '#ffd166'); gr.addColorStop(1, '#ff4d6d');
    g.fillStyle = gr;
    g.fill();
    g.font = '700 96px ' + STK_FONT;
    g.fillStyle = '#000';
    g.fillText(d.emoji || '😍', tw * 0.22, ty + 6);
  } else if (k === 'contagem') {
    w = 720; h = 360;
    stkShadow(g, true);
    roundRect(g, -w / 2, -h / 2, w, h, 46);
    const gr = g.createLinearGradient(-w / 2, -h / 2, w / 2, h / 2);
    gr.addColorStop(0, '#5851db'); gr.addColorStop(.6, '#833ab4'); gr.addColorStop(1, '#c13584');
    g.fillStyle = gr;
    g.fill();
    stkShadow(g, false);
    stkFit(g, up(d.title || 'Faltam'), 54, w - 100);
    g.fillStyle = '#fff';
    g.fillText(up(d.title || 'Faltam'), 0, -h / 2 + 70);
    stkCountdown(d.date).forEach(([v, lab], i) => {
      const bx = (i - 1.5) * 160;
      roundRect(g, bx - 68, -h / 2 + 130, 136, 170, 26);
      g.fillStyle = 'rgba(255,255,255,.22)';
      g.fill();
      g.fillStyle = '#fff';
      g.font = '800 78px ' + STK_FONT;
      g.fillText(v, bx, -h / 2 + 195);
      g.font = '700 26px ' + STK_FONT;
      g.fillText(lab, bx, -h / 2 + 265);
    });
  } else if (k === 'musica') {
    w = 760; h = 200;
    stkCard(g, w, h, 44);
    roundRect(g, -w / 2 + 28, -h / 2 + 28, 144, 144, 26);
    const gr = g.createLinearGradient(-w / 2, -h / 2, -w / 2 + 170, h / 2);
    gr.addColorStop(0, '#ff7a18'); gr.addColorStop(1, '#e0245e');
    g.fillStyle = gr;
    g.fill();
    g.font = '800 84px ' + STK_FONT;
    g.fillStyle = '#fff';
    g.fillText('♪', -w / 2 + 100, 4);
    g.textAlign = 'left';
    stkFit(g, d.title || 'Música', 50, w - 330);
    g.fillStyle = '#1c1e21';
    g.fillText(d.title || 'Música', -w / 2 + 200, -28);
    stkFit(g, d.artist || '', 36, w - 330, 600);
    g.fillStyle = '#8e8e8e';
    g.fillText(d.artist || '', -w / 2 + 200, 34);
    g.textAlign = 'center';
  }
  g.restore();
  return { x: it.x - (w * it.scale) / 2, y: it.y - (h * it.scale) / 2, w: w * it.scale, h: h * it.scale };
}

// ----- bandeja -----
const STK_TILES = [
  { kind: 'loc', label: 'Localização', cls: 't-loc', html: '📍 LOCALIZAÇÃO' },
  { kind: 'mention', label: 'Menção', cls: 't-mention', html: '@MENÇÃO' },
  { kind: 'suavez', label: 'Sua vez', cls: 't-suavez', html: '📷 SUA VEZ', fake: true },
  { kind: 'perguntas', label: 'Perguntas', cls: 't-perg', html: 'PERGUNTAS', fake: true },
  { kind: 'gif', label: 'GIF', cls: 't-gif', html: '🔍 GIF' },
  { kind: 'musica', label: 'Música', cls: 't-musica', html: '▌▌ MÚSICA', fake: true },
  { kind: 'enquete', label: 'Enquete', cls: 't-enquete', html: '≡ ENQUETE', fake: true },
  { kind: 'slider', label: 'Emoji', cls: 't-slider', html: '<i></i>😍', fake: true },
  { kind: 'link', label: 'Link', cls: 't-link', html: '🔗 LINK', fake: true },
  { kind: 'hashtag', label: 'Hashtag', cls: 't-hash', html: '#HASHTAG' },
  { kind: 'contagem', label: 'Contagem regressiva', cls: 't-count', html: 'CONTAGEM REGRESSIVA', fake: true },
  { kind: 'data', label: 'Data', cls: 't-date', html: '' },
  { kind: 'hora', label: 'Hora', cls: 't-time', html: '' },
  { kind: 'temp', label: 'Temperatura', cls: 't-temp', html: '☀️ 24°C' }
];

const pad2 = (n) => String(n).padStart(2, '0');
const stkToday = () => new Date().toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' }).replace('.', '').replace(' de ', ' DE ').toUpperCase();
const stkNow = () => { const n = new Date(); return pad2(n.getHours()) + ':' + pad2(n.getMinutes()); };

// perguntas de cada adesivo: { id, label, val?, ph?, type? }
const STK_FORMS = {
  loc: ['Localização', [{ id: 'text', label: 'Local', ph: 'São Paulo, SP' }]],
  mention: ['Menção', [{ id: 'text', label: '@usuário', ph: '@usuario' }]],
  hashtag: ['Hashtag', [{ id: 'text', label: 'Hashtag', ph: '#viagem' }]],
  suavez: ['Sua vez', [{ id: 'text', label: 'Texto', val: 'Sua vez' }]],
  link: ['Link', [{ id: 'text', label: 'Texto do link', val: 'Link' }]],
  perguntas: ['Perguntas', [{ id: 'q', label: 'Pergunta', val: 'Faça uma pergunta' }]],
  enquete: ['Enquete', [{ id: 'q', label: 'Pergunta', val: 'Qual você prefere?' }, { id: 'a', label: 'Opção 1', val: 'Sim' }, { id: 'b', label: 'Opção 2', val: 'Não' }]],
  slider: ['Emoji', [{ id: 'q', label: 'Pergunta', val: 'Você gosta?' }, { id: 'emoji', label: 'Emoji', val: '😍' }]],
  contagem: ['Contagem regressiva', [{ id: 'title', label: 'Título', val: 'Faltam' }, { id: 'date', label: 'Data final', type: 'date' }]],
  musica: ['Música', [{ id: 'title', label: 'Música', ph: 'Nome da música' }, { id: 'artist', label: 'Artista', ph: 'Artista' }]],
  data: ['Data', [{ id: 'text', label: 'Data', val: stkToday() }]],
  hora: ['Hora', [{ id: 'text', label: 'Hora', val: stkNow() }]],
  temp: ['Temperatura', [{ id: 'text', label: 'Temperatura', val: '24°C' }]]
};

function askFields(title, fields) {
  return new Promise((resolve) => {
    $('#ask-title').textContent = title;
    const box = $('#ask-fields');
    box.textContent = '';
    for (const f of fields) {
      const l = document.createElement('label');
      l.textContent = f.label;
      const i = document.createElement('input');
      i.type = f.type || 'text';
      i.id = 'ask-' + f.id;
      i.placeholder = f.ph || '';
      i.value = f.val || '';
      i.autocomplete = 'off';
      l.appendChild(i);
      box.appendChild(l);
    }
    const done = (ok) => {
      $('#ask').hidden = true;
      $('#ask-ok').onclick = $('#ask-cancel').onclick = null;
      resolve(ok ? Object.fromEntries(fields.map((f) => [f.id, $('#ask-' + f.id).value.trim()])) : null);
    };
    $('#ask-ok').onclick = () => done(true);
    $('#ask-cancel').onclick = () => done(false);
    $('#ask').hidden = false;
    const first = box.querySelector('input');
    if (first) { first.focus(); first.select(); }
    box.onkeydown = (e) => { if (e.key === 'Enter') done(true); else if (e.key === 'Escape') done(false); };
  });
}

function closeTray() { $('#tray').hidden = true; }

async function addSticker(kind) {
  closeTray();
  if (kind === 'gif') { $('#ed-sticker').click(); return; }
  const [title, fields] = STK_FORMS[kind];
  const data = await askFields(title, fields);
  if (!data) return;
  const n = ed.items.filter((i) => i.type === 'sticker').length;
  ed.items.push({ type: 'sticker', kind, data, x: ED_W / 2, y: ED_H / 2 + ((n % 5) - 2) * 220, scale: 1 });
  ed.sel = ed.items.length - 1;
  $('#ed-size').value = 90;
  edRender();
}

function buildTray() {
  const grid = $('#tray-grid');
  grid.textContent = '';
  for (const t of STK_TILES) {
    const b = document.createElement('button');
    b.className = 'tile ' + t.cls;
    b.dataset.label = t.label.toLowerCase();
    const chip = document.createElement('span');
    chip.className = 'chip';
    if (t.kind === 'data') chip.textContent = stkToday();
    else if (t.kind === 'hora') chip.textContent = stkNow();
    else chip.innerHTML = t.html;
    b.appendChild(chip);
    if (t.fake) {
      const f = document.createElement('span');
      f.className = 'fake';
      f.textContent = 'só visual';
      b.appendChild(f);
    }
    b.title = t.fake ? t.label + ': só aparece na imagem, não funciona como no app' : t.label;
    b.addEventListener('click', () => addSticker(t.kind));
    grid.appendChild(b);
  }
}

const strip = (s) => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
$('#tray-q').addEventListener('input', (e) => {
  const q = strip(e.target.value.trim());
  document.querySelectorAll('#tray-grid .tile').forEach((t) => { t.hidden = !!q && !strip(t.dataset.label).includes(q); });
});
$('#ed-open-tray').addEventListener('click', () => {
  buildTray();
  $('#tray-q').value = '';
  $('#tray').hidden = false;
  $('#tray-q').focus();
});
$('#tray').addEventListener('click', (e) => { if (e.target === $('#tray')) closeTray(); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !$('#tray').hidden) { closeTray(); e.stopPropagation(); } }, true);

// ---------------- início ----------------

// a página do Instagram pode já ter carregado antes desta janela: pergunta até ela responder
function startPing() {
  clearInterval(pingTimer);
  const t0 = Date.now();
  pingTimer = setInterval(() => {
    if (gotHello) { clearInterval(pingTimer); return; }
    if (Date.now() - t0 > 20000) {
      clearInterval(pingTimer);
      setConn('bad', 'O Instagram não respondeu. Entre na sua conta na outra janela.');
      return;
    }
    sendToFrame('ping');
  }, 1500);
  sendToFrame('ping');
}

(async function init() {
  const stored = await chrome.storage.local.get(DEFAULTS);
  settings = { ...DEFAULTS, ...stored };
  const ready = await chrome.runtime.sendMessage({ type: 'toolsReady' }).catch(() => null);
  if (ready && ready.ok) { settings.mode = ready.mode; settings.zoom = ready.zoom; }

  document.body.classList.toggle('desktop', settings.mode === 'desktop');
  $('#btn-dark').classList.toggle('on', settings.darkMode);
  $('#opt-videoControls').checked = settings.videoControls;
  $('#opt-rememberVolume').checked = settings.rememberVolume;
  $('#z-val').textContent = Math.round(settings.zoom * 100) + '%';
  $('#btn-mode').title = modeTitle(settings.mode);
  $('#ver').textContent = 'IG Desk versão ' + chrome.runtime.getManifest().version;
  setConn('', 'Conectando ao Instagram…');
  startPing();
})();
