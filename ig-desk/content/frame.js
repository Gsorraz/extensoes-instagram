// IG Desk — script da página do Instagram na janela do IG Desk.
// Dark mode, barra de controles de vídeo, volume lembrado e comandos da janela de ferramentas.
(() => {
  // só age na janela do IG Desk: o background marca a aba com window.name. Abas normais do
  // Instagram não são tocadas.
  try {
    if (window.top !== window || !String(window.name).startsWith('igdesk-')) return;
  } catch (_) {
    return;
  }

  const DEFAULTS = {
    darkMode: false,
    videoControls: true,
    rememberVolume: true,
    volume: 0.7,
    muted: false
  };
  let settings = { ...DEFAULTS };

  // ---------------- dark mode ----------------

  const FLIP = 'invert(1) hue-rotate(180deg)';
  const css = `
    html.igd-dark { filter: ${FLIP} !important; background: #fff !important; }
    html.igd-dark img,
    html.igd-dark video,
    html.igd-dark canvas,
    html.igd-dark picture,
    html.igd-dark [style*="background-image"],
    html.igd-dark #igd-vbar-host { filter: ${FLIP} !important; }
    html.igd-dark picture img,
    html.igd-dark [style*="background-image"] img { filter: none !important; }
  `;

  function injectStyle() {
    if (document.getElementById('igd-style')) return;
    const st = document.createElement('style');
    st.id = 'igd-style';
    st.textContent = css;
    (document.head || document.documentElement).appendChild(st);
  }

  function applyDark() {
    document.documentElement.classList.toggle('igd-dark', !!settings.darkMode);
  }

  injectStyle();

  // ---------------- comunicação com a janela ----------------

  // para a janela de ferramentas (app.html), que escuta chrome.runtime.onMessage
  function post(msg) {
    try { chrome.runtime.sendMessage({ __igd: 1, ...msg }).catch(() => {}); } catch (_) {}
  }

  let lastUrl = '';
  function checkUrl() {
    if (location.href !== lastUrl) {
      lastUrl = location.href;
      post({ type: 'url', url: lastUrl });
    }
  }
  setInterval(checkUrl, 400);

  // ---------- botão "Efeitos e adesivos" na tela de story do Instagram ----------
  // Se a foto foi escolhida pelo clique do próprio Instagram, ele não tem efeitos nem adesivos.
  // Este botão leva a foto ao editor do IG Desk e, ao concluir, o resultado volta ao Instagram.
  let lastImage = null;
  document.addEventListener('change', (e) => {
    const t = e.target;
    const f = t && t.tagName === 'INPUT' && t.type === 'file' && t.files && t.files[0];
    if (f && /^image\//.test(f.type)) lastImage = f;
  }, true);

  let fab = null;
  function ensureFab() {
    if (!location.pathname.startsWith('/create/story')) { if (fab) fab.style.display = 'none'; return; }
    if (!fab) {
      fab = document.createElement('div');
      fab.style.cssText = 'position:fixed;left:10px;top:10px;z-index:2147483647;';
      const root = fab.attachShadow({ mode: 'closed' });
      root.innerHTML = '<style>button{all:unset;cursor:pointer;font:700 13px system-ui,sans-serif;color:#fff;padding:9px 14px;' +
        'border-radius:999px;background:linear-gradient(135deg,#f0576b,#ff9f5a);box-shadow:0 4px 16px rgba(0,0,0,.45)}' +
        'button:hover{filter:brightness(1.1)}</style><button>✨ Efeitos e adesivos</button>';
      root.querySelector('button').addEventListener('click', (ev) => { ev.stopPropagation(); sendToEditor(); });
      for (const t of ['pointerdown', 'mousedown', 'touchstart', 'click']) fab.addEventListener(t, (ev) => ev.stopPropagation());
      document.documentElement.appendChild(fab);
    }
    fab.style.display = 'block';
  }

  async function sendToEditor() {
    if (!lastImage) {
      post({ type: 'toast', text: 'Escolha a foto pelo botão Story da janela de ferramentas para usar os efeitos.' });
      try { chrome.runtime.sendMessage({ type: 'focusTools' }).catch(() => {}); } catch (_) {}
      return;
    }
    const base64 = await new Promise((res) => {
      const r = new FileReader();
      r.onload = () => { const s = String(r.result); res(s.slice(s.indexOf(',') + 1)); };
      r.readAsDataURL(lastImage);
    });
    post({ type: 'editStory', file: { name: lastImage.name || 'story.jpg', type: lastImage.type, base64 } });
    try { chrome.runtime.sendMessage({ type: 'focusTools' }).catch(() => {}); } catch (_) {}
  }
  setInterval(ensureFab, 700);

  function findClickable(el) {
    return el && el.closest('a, button, [role="button"], [role="link"], [tabindex]');
  }

  // página de erro do Instagram ("Esta página não está disponível")
  function looksBroken() {
    // o título é confiável; o texto só conta em páginas curtas (evita falso positivo no feed)
    const title = String(document.title || '').toLowerCase();
    if (/página não encontrada|page not found|não está disponível|isn't available|página no encontrada/.test(title)) return true;
    const t = String((document.body && document.body.innerText) || '').toLowerCase();
    return t.length < 900 && /esta página não está disponível|this page isn't available|esta página no está disponible/.test(t);
  }

  function navigate(path) {
    // navegar "por dentro" de uma página de erro mantém o erro na tela: aí recarrega de verdade
    const a = looksBroken() ? null : document.querySelector(`a[href="${CSS.escape(path)}"]`);
    if (a) a.click();
    else location.assign(path);
  }

  const norm = (s) => String(s || '').trim().toLowerCase();

  // espera algo aparecer na tela (o Instagram monta a página aos poucos)
  async function waitFor(fn, ms = 7000) {
    const end = Date.now() + ms;
    for (;;) {
      const r = fn();
      if (r) return r;
      if (Date.now() > end) return null;
      await new Promise((res) => setTimeout(res, 250));
    }
  }

  const CREATE_LABELS = [
    'nova publicação', 'novo post', 'criar', 'new post', 'create', 'nueva publicación', 'crear'
  ];
  const STORY_LABELS = [
    'adicionar ao story', 'seu story', 'novo story', 'add to story', 'your story', 'new story',
    'tu historia', 'añadir a tu historia'
  ];

  // o "+" do Instagram celular só existe na tela inicial; a bolinha "Seu story" também
  function findCreate() {
    for (const el of document.querySelectorAll('svg[aria-label]')) {
      if (CREATE_LABELS.includes(norm(el.getAttribute('aria-label')))) return findClickable(el) || el.parentElement;
    }
    return null;
  }

  function findStory() {
    for (const el of document.querySelectorAll('[aria-label]')) {
      if (STORY_LABELS.includes(norm(el.getAttribute('aria-label')))) return findClickable(el) || el;
    }
    for (const el of document.querySelectorAll('button, [role="button"], a')) {
      if (STORY_LABELS.includes(norm(el.textContent))) return el;
    }
    return null;
  }

  // Se ir ao Início recarregar a página inteira, este script morre; o nome da ação
  // fica no sessionStorage e é retomado quando o script subir de novo (ver fim do arquivo).
  async function goAndClick(finder, name) {
    let target = finder();
    if (!target) {
      if (location.pathname !== '/') {
        try { sessionStorage.setItem('igdPending', name); } catch (_) {}
        navigate('/');
      }
      target = await waitFor(finder);
      try { sessionStorage.removeItem('igdPending'); } catch (_) {}
    }
    if (!target) return false;
    target.click();
    return true;
  }

  // entrega o arquivo escolhido na janela do IG Desk ao script do Instagram (mobile.js)
  // kind: 'story' (só vale para um campo com a assinatura de story) ou 'post'
  async function handFile(file, kind) {
    const ok = file && typeof file.name === 'string';
    window.postMessage({ __igdFile: 1, file: ok ? file : null, kind: kind || 'post' }, location.origin);
    await new Promise((res) => setTimeout(res, 60)); // a mensagem precisa chegar antes do clique
    return ok;
  }

  // texto para colar no suporte: o que o Instagram realmente mostra nesta tela
  function diagnostic() {
    const cut = (s, n) => String(s || '').replace(/\s+/g, ' ').trim().slice(0, n);
    const labels = [...new Set([...document.querySelectorAll('[aria-label]')]
      .map((e) => e.tagName.toLowerCase() + ':' + cut(e.getAttribute('aria-label'), 40)))].slice(0, 60);
    const clickables = [...document.querySelectorAll('a[href], button, [role="button"]')]
      .map((e) => e.tagName.toLowerCase() + ' "' + cut(e.textContent, 30) + '"' + (e.getAttribute('href') ? ' ' + e.getAttribute('href').slice(0, 40) : ''))
      .slice(0, 60);
    const c = findCreate(), s = findStory();
    return [
      'IG Desk diagnóstico',
      'url: ' + location.pathname + location.search.slice(0, 60),
      'logado (cookie): ' + !!cookie('ds_user_id'),
      'janela: ' + innerWidth + 'x' + innerHeight,
      'TELA DE ERRO do Instagram: ' + (looksBroken() ? 'SIM (feed não carregou)' : 'não'),
      'texto visível: ' + cut(document.body && document.body.innerText, 400),
      'inputs file: ' + document.querySelectorAll('input[type="file"]').length,
      'campos de arquivo: ' + [...document.querySelectorAll('input[type="file"]')]
        .map((i) => '[accept=' + cut(i.accept, 45) + ' multiple=' + i.multiple + ' pai=' + cut(i.parentElement && i.parentElement.outerHTML, 110) + ']').join(' '),
      'achou "+": ' + (c ? c.tagName + ' ' + cut(c.outerHTML, 160) : 'NÃO'),
      'achou story: ' + (s ? s.tagName + ' ' + cut(s.outerHTML, 160) : 'NÃO'),
      'aria-labels: ' + labels.join(' | '),
      'clicáveis: ' + clickables.join(' | ')
    ].join('\n');
  }

  // O Instagram celular traz campos <input type="file"> escondidos, e NEM TODO campo é de story:
  // há campos de foto de perfil, por exemplo. Entregar arquivo ao campo errado poderia trocar a foto
  // de perfil. Por isso só se entrega direto a um campo com a assinatura que já abriu o criador de
  // story na conta real: aceita AVIF **e** PNG. Sem esse campo na tela, o arquivo fica à espera do
  // seu clique no botão de story do próprio Instagram (ver mobile.js). A criação de publicação só
  // existe no layout de computador, onde o "+" ("Novo post") abre uma janela com o seu campo.
  const isStoryInput = (i) => /avif/.test(i.accept) && /png/.test(i.accept) && !i.closest('[role="dialog"]');

  function pickInput(kind) {
    const all = [...document.querySelectorAll('input[type="file"]')];
    if (kind === 'story') return all.find(isStoryInput) || null;
    return all.find((i) => i.closest('[role="dialog"]')) || null;
  }

  function injectFile(input, file) {
    try {
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    } catch (_) {
      return false;
    }
  }

  const isFile = (f) => !!f && typeof f.name === 'string' && typeof f.size === 'number';

  // os campos de arquivo só existem em algumas telas (no celular, no Início): vai até lá e espera
  async function inputFor(kind) {
    let input = pickInput(kind);
    if (!input && location.pathname !== '/') {
      navigate('/');
      input = await waitFor(() => pickInput(kind), 9000);
    }
    return input || (await waitFor(() => pickInput(kind), 4000));
  }

  // Publicação (post/reel): layout de computador. O "+" ("Novo post") abre uma janela com o
  // campo de arquivo; o arquivo escolhido entra nele.
  async function doCreate(file) {
    if (!isFile(file)) return;
    let input = pickInput('post');
    if (!input) {
      await handFile(file); // à espera, caso a entrega direta falhe e você clique em "Selecionar"
      if (!(await goAndClick(findCreate, 'create'))) {
        await handFile(null);
        post({ type: 'toast', text: 'Não achei o botão de criar. Publicação (post/reel) só existe no modo computador.' });
        return;
      }
      input = await waitFor(() => pickInput('post'), 6000);
    }
    if (input && injectFile(input, file)) {
      await handFile(null);
      post({ type: 'toast', text: 'Foto enviada à nova publicação. Siga as etapas do Instagram.' });
      return;
    }
    post({ type: 'toast', text: 'Arquivo pronto. No Instagram, clique em "Novo post" e depois em "Selecionar do computador": ele será usado.' });
  }

  // Story: entrega direto ao campo de story, se houver um na tela; senão deixa o arquivo à espera
  async function doStory(file) {
    if (!isFile(file)) return;
    const input = await inputFor('story');
    if (input && injectFile(input, file)) {
      await handFile(null);
      post({ type: 'toast', text: 'Foto enviada ao story. Confira no Instagram e toque em Compartilhar.' });
      return;
    }
    // sem campo seguro na tela: o Instagram desta conta não mostra o "Seu story" agora
    await handFile(file, 'story');
    post({ type: 'toast', text: 'Foto pronta. No Instagram, toque no seu story / no "+" para criar: ele vai usar esta foto (2 min).' });
  }

  function clickProfile() {
    const imgs = document.querySelectorAll('a[href^="/"] img[alt]');
    for (const img of imgs) {
      if (/perfil|profile/i.test(img.alt)) { img.closest('a').click(); return true; }
    }
    for (const span of document.querySelectorAll('a[href^="/"] span')) {
      if (/^(Perfil|Profile)$/.test(span.textContent.trim())) { span.closest('a').click(); return true; }
    }
    return false;
  }

  // o arquivo chega como { name, type, base64 } (mensagens da extensão só levam JSON)
  function rebuildFile(f) {
    if (!f || typeof f.base64 !== 'string') return null;
    try {
      const bin = atob(f.base64);
      const bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
      return new File([bytes], f.name || 'arquivo', { type: f.type || 'application/octet-stream' });
    } catch (_) {
      return null;
    }
  }

  // comandos da janela de ferramentas
  chrome.runtime.onMessage.addListener((msg) => {
    if (!msg || !msg.__igd || !msg.cmd) return;
    const { cmd, path } = msg;
    switch (cmd) {
      case 'back': history.back(); break;
      case 'forward': history.forward(); break;
      case 'reload': location.reload(); break;
      case 'go': if (typeof path === 'string' && path.startsWith('/')) navigate(path); break;
      case 'create': doCreate(rebuildFile(msg.file)); break;
      case 'story': doStory(rebuildFile(msg.file)); break;
      case 'diag': post({ type: 'diag', text: diagnostic() }); break;
      case 'profile':
        if (!clickProfile()) post({ type: 'toast', text: 'Não achei o link do perfil. Você está logado?' });
        break;
      case 'auto': runAuto(msg.opts || {}); break;
      case 'autoGo': if (auto.go) auto.go(true); break;
      case 'autoStop': auto.stop = true; if (auto.go) auto.go(false); break;
      case 'ping': post({ type: 'hello', url: location.href, v: chrome.runtime.getManifest().version }); break;
    }
  });

  // ---------------- controles de vídeo ----------------

  let host, ui, current = null, hideTimer = 0, overBar = false, raf = 0;

  const ICONS = {
    play: '<path d="M8 5v14l11-7z"/>',
    pause: '<path d="M7 5h4v14H7zM13 5h4v14h-4z"/>',
    vol: '<path d="M4 9v6h4l5 4V5L8 9H4z"/><path d="M16 8.5a5 5 0 0 1 0 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    mute: '<path d="M4 9v6h4l5 4V5L8 9H4z"/><path d="M17 9l4 6M21 9l-4 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    pip: '<rect x="3" y="5" width="18" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><rect x="12" y="12" width="7" height="5" rx="1"/>'
  };
  const svg = (name) => `<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">${ICONS[name]}</svg>`;

  function buildBar() {
    if (host) return;
    host = document.createElement('div');
    host.id = 'igd-vbar-host';
    host.style.cssText = 'position:fixed;z-index:2147483647;left:0;top:0;display:none;pointer-events:auto;';
    const root = host.attachShadow({ mode: 'closed' });
    root.innerHTML = `
      <style>
        :host { all: initial; }
        .bar { display:flex; align-items:center; gap:6px; height:40px; padding:0 8px;
          background:rgba(12,12,14,.82); backdrop-filter:blur(8px); border-radius:10px;
          color:#f2f2f2; font:600 12px/1 system-ui,-apple-system,"Segoe UI",sans-serif;
          box-shadow:0 4px 18px rgba(0,0,0,.35); user-select:none; box-sizing:border-box; width:100%; }
        button { all:unset; cursor:pointer; display:grid; place-items:center; width:28px; height:28px;
          border-radius:7px; color:inherit; flex:none; }
        button:hover { background:rgba(255,255,255,.14); }
        .speed { width:auto; padding:0 6px; font-size:11px; }
        .time { font-variant-numeric:tabular-nums; opacity:.9; flex:none; min-width:74px; text-align:center; }
        input[type=range] { -webkit-appearance:none; appearance:none; height:4px; border-radius:4px;
          background:rgba(255,255,255,.28); outline:none; cursor:pointer; margin:0; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance:none; width:12px; height:12px;
          border-radius:50%; background:#fff; border:none; }
        .seek { flex:1; min-width:40px; }
        .vol { width:64px; flex:none; }
        .narrow .vol, .narrow .speed, .narrow .pip { display:none; }
      </style>
      <div class="bar">
        <button class="pp" title="Play/Pausa"></button>
        <span class="time">0:00 / 0:00</span>
        <input class="seek" type="range" min="0" max="1000" value="0" title="Avançar/voltar">
        <button class="mt" title="Mudo"></button>
        <input class="vol" type="range" min="0" max="100" value="70" title="Volume">
        <button class="speed" title="Velocidade">1x</button>
        <button class="pip" title="Janela flutuante">${svg('pip')}</button>
      </div>`;
    ui = {
      bar: root.querySelector('.bar'),
      pp: root.querySelector('.pp'),
      time: root.querySelector('.time'),
      seek: root.querySelector('.seek'),
      mt: root.querySelector('.mt'),
      vol: root.querySelector('.vol'),
      speed: root.querySelector('.speed'),
      pip: root.querySelector('.pip'),
      seeking: false
    };

    // eventos não vazam para o Instagram (evita pausar story, abrir post etc.)
    for (const t of ['click', 'mousedown', 'mouseup', 'pointerdown', 'pointerup', 'touchstart', 'touchend', 'dblclick', 'keydown', 'wheel']) {
      host.addEventListener(t, ev => ev.stopPropagation());
    }
    host.addEventListener('mouseenter', () => { overBar = true; clearTimeout(hideTimer); });
    host.addEventListener('mouseleave', () => { overBar = false; scheduleHide(); });

    ui.pp.addEventListener('click', () => {
      if (!current) return;
      if (current.paused) current.play().catch(() => {}); else current.pause();
    });
    ui.seek.addEventListener('input', () => {
      ui.seeking = true;
      if (current && isFinite(current.duration)) {
        current.currentTime = (ui.seek.value / 1000) * current.duration;
      }
    });
    ui.seek.addEventListener('change', () => { ui.seeking = false; });
    ui.mt.addEventListener('click', () => {
      if (!current) return;
      current.muted = !current.muted;
      if (!current.muted && current.volume === 0) current.volume = 0.5;
      saveVolume();
    });
    ui.vol.addEventListener('input', () => {
      if (!current) return;
      current.volume = ui.vol.value / 100;
      current.muted = current.volume === 0;
      saveVolume();
    });
    const SPEEDS = [1, 1.25, 1.5, 2, 0.75];
    ui.speed.addEventListener('click', () => {
      if (!current) return;
      const i = SPEEDS.indexOf(current.playbackRate);
      current.playbackRate = SPEEDS[(i + 1) % SPEEDS.length];
      refresh();
    });
    ui.pip.addEventListener('click', async () => {
      if (!current) return;
      try {
        current.disablePictureInPicture = false;
        if (document.pictureInPictureElement) await document.exitPictureInPicture();
        else await current.requestPictureInPicture();
      } catch (_) {
        post({ type: 'toast', text: 'Esse vídeo não permite janela flutuante.' });
      }
    });

    document.documentElement.appendChild(host);
  }

  function saveVolume() {
    if (!current || !settings.rememberVolume) return;
    settings.volume = current.volume;
    settings.muted = current.muted;
    chrome.storage.local.set({ volume: current.volume, muted: current.muted });
  }

  const fmt = (s) => {
    if (!isFinite(s) || s < 0) return '0:00';
    s = Math.floor(s);
    const m = Math.floor(s / 60), r = s % 60;
    return m + ':' + String(r).padStart(2, '0');
  };

  function refresh() {
    if (!current || !ui) return;
    ui.pp.innerHTML = svg(current.paused ? 'play' : 'pause');
    ui.mt.innerHTML = svg(current.muted || current.volume === 0 ? 'mute' : 'vol');
    ui.vol.value = current.muted ? 0 : Math.round(current.volume * 100);
    ui.time.textContent = fmt(current.currentTime) + ' / ' + fmt(current.duration);
    if (!ui.seeking && isFinite(current.duration) && current.duration > 0) {
      ui.seek.value = Math.round((current.currentTime / current.duration) * 1000);
    }
    ui.speed.textContent = current.playbackRate + 'x';
  }

  const MEDIA_EVENTS = ['play', 'pause', 'timeupdate', 'volumechange', 'ratechange', 'durationchange', 'loadedmetadata'];

  function attach(v) {
    if (current === v) return;
    if (current) MEDIA_EVENTS.forEach(ev => current.removeEventListener(ev, refresh));
    current = v;
    MEDIA_EVENTS.forEach(ev => v.addEventListener(ev, refresh));
    refresh();
  }

  function position() {
    if (!host || !current || host.style.display === 'none') return;
    if (!current.isConnected) { hide(); return; }
    const r = current.getBoundingClientRect();
    const top = Math.max(0, r.top), bottom = Math.min(innerHeight, r.bottom);
    const left = Math.max(0, r.left), right = Math.min(innerWidth, r.right);
    if (bottom - top < 60 || right - left < 120) { hide(); return; }
    const w = right - left - 16;
    host.style.left = (left + 8) + 'px';
    host.style.top = (bottom - 48) + 'px';
    host.style.width = w + 'px';
    ui.bar.classList.toggle('narrow', w < 300);
    raf = requestAnimationFrame(position);
  }

  function show() {
    buildBar();
    refresh();
    if (host.style.display !== 'block') {
      host.style.display = 'block';
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(position);
    }
  }

  function hide() {
    if (!host) return;
    host.style.display = 'none';
    cancelAnimationFrame(raf);
  }

  function scheduleHide() {
    clearTimeout(hideTimer);
    hideTimer = setTimeout(() => { if (!overBar) hide(); }, 2500);
  }

  function videoAt(x, y) {
    let best = null, bestArea = 0;
    for (const v of document.querySelectorAll('video')) {
      const r = v.getBoundingClientRect();
      if (r.width < 100 || r.height < 80) continue;
      if (x >= r.left && x <= r.right && y >= r.top && y <= r.bottom) {
        const area = r.width * r.height;
        if (area > bestArea) { best = v; bestArea = area; }
      }
    }
    return best;
  }

  document.addEventListener('mousemove', (e) => {
    if (!settings.videoControls) return;
    if (host && e.target === host) return;
    const v = videoAt(e.clientX, e.clientY);
    if (v) { attach(v); show(); scheduleHide(); }
    else if (!overBar) hide();
  }, { capture: true, passive: true });

  // volume lembrado: aplica quando um vídeo começa a tocar
  document.addEventListener('play', (e) => {
    const v = e.target;
    if (!(v instanceof HTMLVideoElement) || !settings.rememberVolume) return;
    if (v.__igdApplied) return;
    v.__igdApplied = true;
    v.volume = Math.min(1, Math.max(0, Number(settings.volume) || 0));
    const active = navigator.userActivation && navigator.userActivation.hasBeenActive;
    if (settings.muted) v.muted = true;
    else if (active) v.muted = false;
  }, true);

  // ---------------- crescimento: seguir / deixar de seguir ----------------
  // Usa os mesmos endpoints que o site chama quando você clica em "Seguir" /
  // "Seguindo". Só roda quando a barra lateral manda, com limite diário, pausas
  // aleatórias, confirmação prévia e parada imediata se o Instagram recusar algo.

  const IG_APP_ID = '936619743392459';
  const DAILY_MAX = 150;
  const auto = { running: false, stop: false, go: null };

  class AutoError extends Error {}
  class AutoStop extends Error {}
  class BlockErr extends AutoError {}    // o Instagram bloqueou/limitou: para tudo
  class NoEffectErr extends AutoError {} // "ok" sem efeito: pode tentar o outro método
  const BLOCK_RE = /feedback_required|checkpoint|action_blocked|rate.?limit|please wait|spam/i;

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const rand = (a, b) => a + Math.random() * (b - a);
  const today = () => new Date().toLocaleDateString('sv-SE'); // AAAA-MM-DD, horário local
  const uid = (u) => String((u && (u.pk || u.pk_id || u.id)) || '');

  function cookie(name) {
    const m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : '';
  }

  function autoPost(state, text, extra) {
    post({ type: 'auto', state, text, ...extra });
  }

  function checkStop() {
    if (auto.stop) throw new AutoStop();
  }

  // pausa que acorda assim que o usuário clica em Parar
  async function wait(ms) {
    const end = Date.now() + ms;
    while (Date.now() < end) {
      checkStop();
      await sleep(Math.min(300, end - Date.now()));
    }
    checkStop();
  }

  async function api(path, method = 'GET') {
    let wwwClaim = '0';
    try { wwwClaim = sessionStorage.getItem('www-claim-v2') || '0'; } catch (_) {}
    const res = await fetch(path, {
      method,
      credentials: 'include',
      headers: {
        'X-IG-App-ID': IG_APP_ID,
        'X-CSRFToken': cookie('csrftoken'),
        'X-IG-WWW-Claim': wwwClaim,
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: method === 'POST' ? new URLSearchParams() : undefined
    });
    let data = null;
    try { data = await res.json(); } catch (_) {}
    if (res.status === 429) {
      throw new AutoError('O Instagram pediu para ir mais devagar (429). Parei por segurança; tente de novo mais tarde.');
    }
    if (!res.ok || (data && data.status === 'fail')) {
      const why = (data && (data.message || data.feedback_message)) || ('HTTP ' + res.status);
      throw new AutoError('O Instagram recusou a ação (' + why + '). Parei por segurança; espere algumas horas antes de tentar de novo.');
    }
    return data || {};
  }

  // lê uma lista paginada (seguidores / seguindo)
  async function listUsers(kind, userId, cap, label, dl) {
    const users = [];
    let maxId = '';
    let complete = false;
    for (;;) {
      checkStop();
      const q = new URLSearchParams({ count: '100' });
      if (maxId) q.set('max_id', maxId);
      const d = await api('/api/v1/friendships/' + userId + '/' + kind + '/?' + q);
      users.push(...(d.users || []));
      autoPost('collecting', label + ': ' + users.length + '…');
      if (!d.next_max_id) { complete = true; break; }
      if (users.length >= cap) break;
      maxId = d.next_max_id;
      await wait(rand(dl.pageMin, dl.pageMax));
    }
    return { users, complete };
  }

  // Ponte com mobile.js (contexto da página): chama a função do próprio site, que monta os
  // cabeçalhos e os tokens anti-abuso. Sem isso o Instagram ignora o pedido (responde vazio).
  let bridgeId = 0;
  const bridgeWait = new Map();
  window.addEventListener('message', (e) => {
    if (e.source !== window || !e.data || e.data.__igdBridgeRes !== 1) return;
    const w = bridgeWait.get(e.data.rid);
    if (w) { bridgeWait.delete(e.data.rid); w(e.data); }
  });
  function viaSite(op, u) {
    return new Promise((resolve, reject) => {
      const r = ++bridgeId;
      const t = setTimeout(() => {
        bridgeWait.delete(r);
        reject(new AutoError('A página do Instagram não respondeu à ponte. Recarregue a janela dele e tente de novo.'));
      }, 20000);
      bridgeWait.set(r, (d) => {
        clearTimeout(t);
        if (d.ok) { resolve(d.data); return; }
        const detalhe = (d.statusCode ? 'HTTP ' + d.statusCode + ' ' : '') + (d.text || d.error || 'sem detalhe');
        if (d.statusCode === 429) reject(new BlockErr('O Instagram pediu para ir mais devagar (429). Parei por segurança; tente de novo mais tarde.'));
        else reject(new (d.statusCode === 400 || BLOCK_RE.test(detalhe) ? BlockErr : AutoError)('O Instagram recusou a ação (' + detalhe + '). Parei por segurança.'));
      });
      window.postMessage({ __igdBridgeReq: 1, rid: r, op, userId: uid(u) }, '*');
    });
  }

  // O Instagram pode responder "ok" sem ter feito a ação. Só conta como feita se o estado da
  // amizade realmente mudou: pela própria resposta ou, se faltar, consultando (leitura).
  async function confirmAction(kind, u, resp) {
    const worked = (fs) => (kind === 'unfollow' ? fs.following === false : fs.following === true || fs.outgoing_request === true);
    if (resp && (resp.spam === true || resp.status === 'fail')) {
      throw new BlockErr('O Instagram sinalizou a ação como bloqueada (' + JSON.stringify(resp).slice(0, 160) + '). Parei por segurança.');
    }
    let fs = resp && resp.friendship_status;
    if (!fs || typeof fs.following !== 'boolean') {
      await wait(rand(700, 1400));
      fs = await api('/api/v1/friendships/show/' + uid(u) + '/');
    }
    if (typeof fs.following !== 'boolean' || !worked(fs)) {
      const raw = JSON.stringify(resp || {}).slice(0, 220);
      throw new NoEffectErr('O Instagram respondeu "ok", mas @' + u.username + (kind === 'unfollow' ? ' continua sendo seguido' : ' não foi seguido') +
        '. Resposta dele: ' + raw);
    }
  }

  // Método alternativo (o mesmo do projeto InstagramUnfollowers): endpoint "web/friendships" com o
  // cabeçalho mínimo. Só entra se o método do site não surtir efeito.
  async function viaLegacy(kind, u) {
    const res = await fetch('/web/friendships/' + uid(u) + '/' + (kind === 'unfollow' ? 'unfollow' : 'follow') + '/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'content-type': 'application/x-www-form-urlencoded',
        'x-csrftoken': cookie('csrftoken'),
        'x-ig-app-id': IG_APP_ID,
        'x-asbd-id': '129477',
        'x-requested-with': 'XMLHttpRequest'
      }
    });
    let data = null;
    try { data = await res.json(); } catch (_) {}
    const msg = String((data && (data.message || data.feedback_message)) || '');
    if (res.status === 429 || res.status === 400 || (data && (data.status === 'fail' || data.spam === true)) || BLOCK_RE.test(msg)) {
      throw new BlockErr('O Instagram limitou a ação (HTTP ' + res.status + (msg ? ' ' + msg.slice(0, 120) : '') + '). Parei por segurança; espere algumas horas.');
    }
    return data || {};
  }

  // tenta o método que funcionou por último e, se não surtir efeito, o outro; bloqueio para tudo
  async function doAction(kind, u) {
    const ordem = auto.strategy === 'legacy' ? ['legacy', 'site'] : ['site', 'legacy'];
    const falhas = [];
    for (const s of ordem) {
      try {
        const resp = s === 'site' ? await viaSite(kind, u) : await viaLegacy(kind, u);
        await confirmAction(kind, u, resp);
        auto.strategy = s;
        return;
      } catch (e) {
        if (!(e instanceof NoEffectErr) && !(e instanceof AutoError && !(e instanceof BlockErr) && s === 'site')) throw e;
        falhas.push((s === 'site' ? 'método do site' : 'método alternativo') + ': ' + e.message.replace(/^O Instagram respondeu "ok", mas /, ''));
      }
    }
    throw new AutoError('Nenhum dos dois métodos teve efeito. Parei: nada foi contado. ' + falhas.join(' | '));
  }

  async function runAuto(o) {
    if (auto.running) { autoPost('error', 'Já existe uma automação em andamento.'); return; }
    auto.running = true;
    auto.stop = false;
    auto.go = null;
    try {
      const me = cookie('ds_user_id');
      if (!me || !cookie('csrftoken')) throw new AutoError('Você não está logado no Instagram dentro da janela.');
      if (!['unfollow', 'followback', 'followNew'].includes(o.task)) throw new AutoError('Tarefa desconhecida.');

      const dl = { pageMin: o.pageMin ?? 1500, pageMax: o.pageMax ?? 3000 };
      const minDelay = Math.max(0, Number(o.minDelay) || 0);
      const maxDelay = Math.max(minDelay, Number(o.maxDelay) || minDelay);
      const skipVerified = o.skipVerified !== false;

      const st = await chrome.storage.local.get({ autoDay: null, autoSeen: [] });
      const day = st.autoDay && st.autoDay.date === today() ? st.autoDay : { date: today(), follow: 0, unfollow: 0 };
      const kind = o.task === 'unfollow' ? 'unfollow' : 'follow';
      const limit = Math.min(Math.max(1, Number(o.limit) || 1), DAILY_MAX);
      const left = DAILY_MAX - day[kind];
      if (left <= 0) throw new AutoError('Limite diário (' + DAILY_MAX + ') já atingido. Volte amanhã.');
      const max = Math.min(limit, left);

      const keep = (u) => !(skipVerified && u.is_verified);
      let cands = [];

      if (o.task === 'unfollow') {
        const fol = await listUsers('followers', me, 50000, 'Lendo seus seguidores', dl);
        // lista incompleta ou vazia faria o script achar que ninguém te segue
        if (!fol.complete || !fol.users.length) {
          throw new AutoError('Não consegui ler sua lista completa de seguidores. Por segurança, não deixei de seguir ninguém.');
        }
        const followers = new Set(fol.users.map(uid));
        const fing = await listUsers('following', me, 50000, 'Lendo quem você segue', dl);
        cands = fing.users.filter((u) => uid(u) && !followers.has(uid(u)) && keep(u));
      } else {
        const fing = await listUsers('following', me, 50000, 'Lendo quem você segue', dl);
        if (!fing.complete) {
          throw new AutoError('Não consegui ler a lista completa de quem você segue. Por segurança, não segui ninguém.');
        }
        const following = new Set(fing.users.map(uid));
        let pool = [];

        if (o.task === 'followback') {
          pool = (await listUsers('followers', me, 50000, 'Lendo seus seguidores', dl)).users;
        } else {
          const src = String(o.source || '').replace(/^@/, '').trim();
          if (src) {
            if (!/^[A-Za-z0-9._]{1,30}$/.test(src)) throw new AutoError('Nome de usuário inválido: ' + src);
            const prof = await api('/api/v1/users/web_profile_info/?username=' + encodeURIComponent(src));
            const srcId = prof && prof.data && prof.data.user && prof.data.user.id;
            if (!srcId) throw new AutoError('Não encontrei o perfil @' + src + '.');
            pool = (await listUsers('followers', srcId, 400, 'Lendo seguidores de @' + src, dl)).users;
          } else {
            const sug = await api('/api/v1/discover/chaining/?target_id=' + me);
            pool = sug.users || [];
          }
          const seen = new Set(st.autoSeen);
          pool = pool.filter((u) => !seen.has(uid(u)));
        }
        // perfis privados exigem aprovação: não vale gastar o limite diário com eles
        cands = pool.filter((u) => uid(u) && uid(u) !== me && !following.has(uid(u)) && !u.is_private && keep(u));
      }

      const seenIds = new Set();
      const list = cands.filter((u) => !seenIds.has(uid(u)) && seenIds.add(uid(u))).slice(0, max);
      checkStop();
      if (!list.length) {
        autoPost('done', 'Nada a fazer: nenhuma conta encontrada para essa ação.');
        return;
      }

      autoPost('ready', 'Pronto', { total: list.length, sample: list.slice(0, 3).map((u) => u.username) });
      const ok = await new Promise((resolve) => {
        auto.go = resolve;
        setTimeout(() => resolve(false), 5 * 60 * 1000); // sem resposta em 5 min: cancela
      });
      auto.go = null;
      if (!ok) throw new AutoStop();

      const endpoint = kind === 'unfollow' ? 'destroy' : 'create';
      const verb = kind === 'unfollow' ? 'Deixou de seguir' : 'Seguiu';
      const seen = new Set(st.autoSeen);
      let done = 0;
      try {
        for (const u of list) {
          checkStop();
          await doAction(kind, u);
          done++;
          day[kind]++;
          if (kind === 'follow') seen.add(uid(u));
          await chrome.storage.local.set({ autoDay: day, autoSeen: [...seen].slice(-5000) });
          autoPost('running', verb + ' @' + u.username + ' (' + done + '/' + list.length + ')', { done, total: list.length });
          if (done < list.length) {
            await wait(rand(minDelay, maxDelay) * 1000);
            // descanso mais longo a cada 10 ações
            if (done % 10 === 0) {
              const s = Math.round(rand(120, 240));
              autoPost('running', 'Descanso de segurança: ' + s + 's (a cada 10 ações)…', { done, total: list.length });
              await wait(s * 1000);
            }
          }
        }
      } catch (e) {
        e.done = done;
        throw e;
      }
      autoPost('done', 'Concluído: ' + done + ' conta(s). Hoje: ' + day.follow + ' seguidas, ' + day.unfollow + ' deixadas de seguir.');
    } catch (e) {
      if (e instanceof AutoStop) autoPost('stopped', 'Parado' + (e.done ? ' após ' + e.done + ' conta(s).' : '.'));
      else if (e instanceof AutoError) autoPost('error', e.message);
      else autoPost('error', 'Erro inesperado: ' + (e && e.message ? e.message : e));
    } finally {
      auto.running = false;
      auto.stop = false;
      auto.go = null;
    }
  }

  // ---------------- configurações ----------------

  chrome.storage.local.get(DEFAULTS).then((s) => {
    settings = { ...DEFAULTS, ...s };
    applyDark();
    if (!settings.videoControls) hide();
  });

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== 'local') return;
    for (const k of Object.keys(changes)) {
      if (k in DEFAULTS) settings[k] = changes[k].newValue;
    }
    applyDark();
    if (!settings.videoControls) hide();
  });

  // o Instagram às vezes recria <html>/<head>; garante estilo e classe
  new MutationObserver(() => {
    injectStyle();
    if (settings.darkMode && !document.documentElement.classList.contains('igd-dark')) applyDark();
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['class'], childList: true });

  // modo celular que não abriu (acontece em algumas contas/navegadores): aponta a saída
  if (window.name === 'igdesk-mobile') {
    window.addEventListener('load', () => setTimeout(() => {
      if (looksBroken() && !location.pathname.startsWith('/accounts/')) {
        post({ type: 'toast', text: 'O Instagram não abriu no modo celular. Clique no ícone do computador (modo computador): o "+" e as ferramentas funcionam lá.' });
      }
    }, 4500), { once: true });
  }

  // retoma "+" / Story que precisou recarregar a página para ir ao Início
  try {
    const pending = sessionStorage.getItem('igdPending');
    if (pending) {
      sessionStorage.removeItem('igdPending');
      if (location.pathname === '/') {
        window.addEventListener('load', () => {
          if (pending === 'create') doCreate();
          else if (pending === 'story') doStory();
        }, { once: true });
      }
    }
  } catch (_) {}

  const hello = () => {
    post({ type: 'hello', url: location.href, v: chrome.runtime.getManifest().version });
    checkUrl();
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', hello, { once: true });
  else hello();
})();
