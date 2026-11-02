// IG Seguidores — script da página do Instagram.
// Faz as mesmas chamadas que o site faz (mesma origem, com o seu login) e manda o resultado ao painel.
// Só age quando o painel pede; nada roda sozinho.
(() => {
  // versão do script: depois de recarregar a extensão, a aba do Instagram ainda tem o script antigo; mudar este número faz o novo entrar
  const BUILD = 3;
  if (window.__igsLoaded === BUILD) return;
  window.__igsLoaded = BUILD;

  const IG_APP_ID = '936619743392459';
  const DAILY_MAX = 200;
  const REST_EVERY = 20; // descanso maior a cada N ações (mesmo valor do painel.js)
  const job = { busy: false, stop: false, paused: false, strategy: 'site' };

  class Fail extends Error {}
  class Stop extends Error {}
  class Block extends Fail {}     // o Instagram bloqueou/limitou: para tudo, não tenta outro método
  class NoEffect extends Fail {}  // o pedido "deu certo" mas o estado não mudou: pode tentar outro método

  // sinais de bloqueio de ação (os mesmos que o InstagramUnfollowers trata como bloqueio)
  const BLOCK_RE = /feedback_required|checkpoint|action_blocked|rate.?limit|please wait|spam/i;

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const rand = (a, b) => a + Math.random() * (b - a);
  const today = () => new Date().toLocaleDateString('sv-SE'); // AAAA-MM-DD, horário local

  // mensagens para o painel
  const send = (msg) => { try { chrome.runtime.sendMessage({ __igs: 1, ...msg }).catch(() => {}); } catch (_) {} };

  function cookie(name) {
    const m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : '';
  }

  async function api(path, method = 'GET') {
    let claim = '0';
    try { claim = sessionStorage.getItem('www-claim-v2') || '0'; } catch (_) {}
    const res = await fetch(path, {
      method,
      credentials: 'include',
      headers: {
        'X-IG-App-ID': IG_APP_ID,
        'X-CSRFToken': cookie('csrftoken'),
        'X-IG-WWW-Claim': claim,
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: method === 'POST' ? new URLSearchParams() : undefined
    });
    let data = null;
    try { data = await res.json(); } catch (_) {}
    if (res.status === 429) throw new Block('O Instagram pediu para ir mais devagar (429). Parei por segurança; tente de novo mais tarde.');
    if (!res.ok || (data && data.status === 'fail')) {
      const why = (data && (data.message || data.feedback_message)) || ('HTTP ' + res.status);
      const Cls = BLOCK_RE.test(String(why)) ? Block : Fail;
      throw new Cls('O Instagram recusou a ação (' + why + '). Parei por segurança; espere algumas horas antes de tentar de novo.');
    }
    return data || {};
  }

  const slim = (u) => ({
    id: String(u.pk || u.pk_id || u.id || ''),
    u: u.username || '',
    n: u.full_name || '',
    v: u.is_verified ? 1 : 0,
    p: u.is_private ? 1 : 0,
    pic: u.profile_pic_url || ''
  });

  const checkStop = () => { if (job.stop) throw new Stop(); };
  async function wait(ms) {
    let end = Date.now() + ms;
    while (Date.now() < end) {
      checkStop();
      if (job.paused) { end += 300; await sleep(300); continue; } // em pausa o relógio não corre
      await sleep(Math.min(300, end - Date.now()));
    }
    checkStop();
  }

  // pausa inicial: se estiver pausado antes de uma ação, espera aqui
  async function whilePaused() {
    while (job.paused) { checkStop(); await sleep(300); }
  }

  // lê uma lista paginada (seguidores / seguindo); "complete" = chegou ao fim de verdade
  async function readList(kind, userId, cap, label) {
    const byId = new Map(); // o Instagram às vezes repete contas entre páginas: guarda cada uma uma vez
    let maxId = '';
    let complete = false;
    for (;;) {
      checkStop();
      const q = new URLSearchParams({ count: '100' });
      if (maxId) q.set('max_id', maxId);
      // limite de uso (429): espera e tenta de novo em vez de desistir (até 3 vezes)
      let d;
      for (let tentativa = 1; ; tentativa++) {
        try { d = await api('/api/v1/friendships/' + userId + '/' + kind + '/?' + q); break; } catch (e) {
          if (!(e instanceof Block) || tentativa > 3) throw e;
          const s = 30 * tentativa;
          send({ type: 'progress', text: 'O Instagram pediu calma. Esperando ' + s + 's antes de continuar…' });
          await wait(s * 1000);
        }
      }
      for (const raw of d.users || []) {
        const u = slim(raw);
        if (u.id && !byId.has(u.id)) byId.set(u.id, u);
      }
      send({ type: 'progress', text: label + ': ' + byId.size + '…', n: byId.size, kind });
      if (!d.next_max_id) { complete = true; break; }
      if (byId.size >= cap) break;
      maxId = d.next_max_id;
      await wait(rand(1500, 3000));
    }
    return { users: [...byId.values()], complete };
  }

  // @ da conta logada: tenta várias fontes; "why" junta o motivo de cada falha (para diagnóstico)
  async function myUsername(id, why) {
    const nota = (s, e) => { if (why) why.push(s + ': ' + ((e && e.message) || e || 'sem usuário').toString().slice(0, 80)); };
    try {
      const d = await api('/api/v1/users/' + id + '/info/');
      if (d && d.user && d.user.username) return d.user.username;
      nota('info', 'sem usuário');
    } catch (e) { nota('info', e); }
    try {
      const d = await api('/api/v1/accounts/current_user/?edit=true');
      if (d && d.user && d.user.username) return d.user.username;
      nota('current_user', 'sem usuário');
    } catch (e) { nota('current_user', e); }
    // dados que a própria página já traz: um "username" colado ao id da conta
    try {
      const html = document.documentElement.innerHTML;
      const re = new RegExp('"username":"([A-Za-z0-9._]{1,30})"[^{}]{0,300}"(?:pk|id|pk_id)":"' + id + '"|"(?:pk|id|pk_id)":"' + id + '"[^{}]{0,300}"username":"([A-Za-z0-9._]{1,30})"');
      const m = html.match(re);
      if (m) return m[1] || m[2];
      nota('página', 'não achei');
    } catch (e) { nota('página', e); }
    for (const a of document.querySelectorAll('a[href^="/"]')) {
      const m = (a.getAttribute('href') || '').match(/^\/([A-Za-z0-9._]{1,30})\/$/);
      if (m && a.querySelector('img') && !['explore', 'reels', 'direct', 'accounts'].includes(m[1])) return m[1];
    }
    nota('links', 'não achei');
    return '';
  }

  // ---------------- tarefas ----------------

  async function taskLists() {
    const me = cookie('ds_user_id');
    if (!me || !cookie('csrftoken')) throw new Fail('Você não está logado no Instagram.');
    const username = await myUsername(me);
    const fol = await readList('followers', me, 60000, 'Lendo seus seguidores');
    if (!fol.complete) throw new Fail('A lista de seguidores é grande demais ou foi interrompida. Nada foi alterado.');
    const fing = await readList('following', me, 60000, 'Lendo quem você segue');
    if (!fing.complete) throw new Fail('A lista de quem você segue é grande demais ou foi interrompida. Nada foi alterado.');
    send({ type: 'lists', me: { id: me, username }, followers: fol.users, following: fing.users });
  }

  // candidatos para seguir: sugestões do Instagram ou seguidores de um perfil
  async function taskDiscover(opts) {
    const me = cookie('ds_user_id');
    if (!me) throw new Fail('Você não está logado no Instagram.');
    const pool = new Map(); // sem repetir contas entre os perfis de origem
    const sources = (Array.isArray(opts.sources) ? opts.sources : [opts.source])
      .map((s) => String(s || '').replace(/^@/, '').trim()).filter(Boolean).slice(0, 5);
    if (sources.length) {
      for (const src of sources) {
        if (!/^[A-Za-z0-9._]{1,30}$/.test(src)) throw new Fail('Nome de usuário inválido: ' + src);
        const prof = await api('/api/v1/users/web_profile_info/?username=' + encodeURIComponent(src));
        const sid = prof && prof.data && prof.data.user && prof.data.user.id;
        if (!sid) throw new Fail('Não encontrei o perfil @' + src + '.');
        const lst = await readList('followers', sid, Math.min(Number(opts.max) || 300, 1000), 'Lendo seguidores de @' + src);
        for (const u of lst.users) if (!pool.has(u.id)) pool.set(u.id, u);
        await wait(rand(2000, 4000));
      }
    } else {
      const d = await api('/api/v1/discover/chaining/?target_id=' + me);
      for (const raw of d.users || []) { const u = slim(raw); if (u.id) pool.set(u.id, u); }
    }
    send({ type: 'discover', users: [...pool.values()].filter((u) => u.id !== me) });
  }

  // Ponte com o contexto da página (ponte.js): chama a função do próprio site para seguir/deixar de
  // seguir (ela monta cabeçalhos e o token anti-abuso). Sem isso o Instagram ignora o pedido.
  let rid = 0;
  const waiting = new Map();
  window.addEventListener('message', (e) => {
    if (e.source !== window || !e.data || e.data.__igsRes !== 1) return;
    const w = waiting.get(e.data.rid);
    if (w) { waiting.delete(e.data.rid); w(e.data); }
  });
  function bridge(op, userId) {
    return new Promise((resolve, reject) => {
      const r = ++rid;
      const t = setTimeout(() => {
        waiting.delete(r);
        reject(new Fail('A página do Instagram não respondeu à ponte. Recarregue a janelinha dele e tente de novo.'));
      }, 20000);
      waiting.set(r, (d) => { clearTimeout(t); resolve(d); });
      window.postMessage({ __igsReq: 1, rid: r, op, userId }, '*');
    });
  }
  async function viaSite(op, u) {
    const res = await bridge(op, u.id);
    if (!res.ok) {
      const detalhe = (res.statusCode ? 'HTTP ' + res.statusCode + ' ' : '') + (res.text || res.error || 'sem detalhe');
      if (res.statusCode === 429) throw new Block('O Instagram pediu para ir mais devagar (429). Parei por segurança; tente de novo mais tarde.');
      const Cls = res.statusCode === 400 || BLOCK_RE.test(detalhe) ? Block : Fail;
      throw new Cls('O Instagram recusou a ação (' + detalhe + '). Parei por segurança; espere algumas horas antes de tentar de novo.');
    }
    return res.data;
  }

  // Método alternativo (o mesmo do projeto InstagramUnfollowers): endpoint "web/friendships" com o
  // cabeçalho mínimo. Só entra se o método do site não surtir efeito.
  async function viaLegacy(op, u) {
    const res = await fetch('/web/friendships/' + u.id + '/' + (op === 'unfollow' ? 'unfollow' : 'follow') + '/', {
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
      throw new Block('O Instagram limitou a ação (HTTP ' + res.status + (msg ? ' ' + msg.slice(0, 120) : '') + '). Parei por segurança; espere algumas horas.');
    }
    return data || {};
  }

  // O Instagram pode responder "ok" sem ter feito a ação. Só conta como feita se o estado da
  // amizade realmente mudou: primeiro pela própria resposta, senão consultando (leitura).
  async function confirmAction(op, u, resp) {
    const worked = (fs) => (op === 'unfollow' ? fs.following === false : fs.following === true || fs.outgoing_request === true);
    if (resp && (resp.spam === true || resp.status === 'fail')) {
      throw new Block('O Instagram sinalizou a ação como bloqueada (' + JSON.stringify(resp).slice(0, 160) + '). Parei por segurança.');
    }
    let fs = resp && resp.friendship_status;
    if (!fs || typeof fs.following !== 'boolean') {
      await wait(rand(700, 1400));
      try { fs = await viaSite('show', u); } catch (e) {
        if (e instanceof Stop) throw e;
        fs = await api('/api/v1/friendships/show/' + u.id + '/');
      }
    }
    if (typeof fs.following !== 'boolean' || !worked(fs)) {
      const raw = JSON.stringify(resp || {}).replace(/"(csrf|token)[^,}]*[,}]?/gi, '').slice(0, 220);
      throw new NoEffect('O Instagram respondeu "ok", mas @' + u.u + (op === 'unfollow' ? ' continua sendo seguido' : ' não foi seguido') +
        '. Resposta dele: ' + raw);
    }
  }

  // tenta o método que funcionou por último e, se não surtir efeito, o outro; bloqueio para tudo
  async function doAction(op, u) {
    const ordem = job.strategy === 'legacy' ? ['legacy', 'site'] : ['site', 'legacy'];
    const falhas = [];
    for (const s of ordem) {
      try {
        const resp = s === 'site' ? await viaSite(op, u) : await viaLegacy(op, u);
        await confirmAction(op, u, resp);
        job.strategy = s;
        return;
      } catch (e) {
        if (!(e instanceof NoEffect) && !(e instanceof Fail && !(e instanceof Block) && s === 'site')) throw e;
        falhas.push((s === 'site' ? 'método do site' : 'método alternativo') + ': ' + e.message.replace(/^O Instagram respondeu "ok", mas /, ''));
      }
    }
    throw new Fail('Nenhum dos dois métodos teve efeito. Parei: nada foi contado. ' + falhas.join(' | '));
  }

  // segue / deixa de seguir, uma conta por vez, com pausa aleatória
  async function taskAct(opts) {
    const op = opts.op === 'unfollow' ? 'unfollow' : 'follow';
    const me = cookie('ds_user_id');
    if (!me) throw new Fail('Você não está logado no Instagram.');
    if (opts.acct && String(opts.acct) !== me) throw new Fail('A janelinha do Instagram está em outra conta que a do painel. Parei: nada foi feito.');
    const dayKey = 'day:' + me; // o contador do dia é de cada conta
    const st = await chrome.storage.local.get({ [dayKey]: null });
    const day = st[dayKey] && st[dayKey].date === today() ? st[dayKey] : { date: today(), follow: 0, unfollow: 0 };
    const left = DAILY_MAX - day[op];
    if (left <= 0) throw new Fail('Limite diário (' + DAILY_MAX + ') já atingido. Volte amanhã.');
    const minD = Math.max(0, Number(opts.minDelay) || 0);
    const maxD = Math.max(minD, Number(opts.maxDelay) || minD);
    const list = (opts.users || []).slice(0, Math.min(left, Math.max(1, Number(opts.limit) || 1)));
    let done = 0;
    for (const u of list) {
      checkStop();
      await whilePaused();
      if (cookie('ds_user_id') !== me) throw new Fail('A conta do Instagram na janelinha mudou durante a execução. Parei por segurança.');
      await doAction(op, u);
      done++;
      day[op]++;
      await chrome.storage.local.set({ [dayKey]: day });
      send({ type: 'act', op, done, total: list.length, user: u, day, acct: me });
      if (done < list.length) {
        await wait(rand(minD, maxD) * 1000);
        // descanso mais longo a cada REST_EVERY ações (o InstagramUnfollowers descansa 5 min a cada 5)
        if (done % REST_EVERY === 0) {
          const s = Math.round(rand(60, 120));
          send({ type: 'progress', text: 'Descanso de segurança: ' + s + 's (a cada ' + REST_EVERY + ' ações)…' });
          await wait(s * 1000);
        }
      }
    }
    send({ type: 'done', text: 'Concluído: ' + done + ' conta(s).', day });
  }

  async function run(name, fn, arg) {
    if (job.busy) { send({ type: 'error', text: 'Já existe uma tarefa em andamento.' }); return; }
    job.busy = true;
    job.stop = false;
    try {
      await fn(arg);
    } catch (e) {
      if (e instanceof Stop) send({ type: 'stopped', text: 'Parado.' });
      else if (e instanceof Fail) send({ type: 'error', text: e.message });
      else send({ type: 'error', text: 'Erro inesperado: ' + (e && e.message ? e.message : e) });
    } finally {
      job.busy = false;
      job.stop = false;
      send({ type: 'idle', name });
    }
  }

  // ---------------- comandos do painel ----------------

  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (!msg || !msg.__igsCmd) return false;
    if (msg.cmd === 'who') { // @ da conta logada (resposta assíncrona)
      const id = cookie('ds_user_id');
      if (!id) { sendResponse({ ok: false }); return false; }
      const why = [];
      myUsername(id, why).then((username) => sendResponse({ ok: true, id, username, why: why.join(' | ') }), () => sendResponse({ ok: false }));
      return true;
    }
    switch (msg.cmd) {
      case 'ping': {
        const id = cookie('ds_user_id');
        sendResponse({ ok: true, loggedIn: !!id && !!cookie('csrftoken'), id, busy: job.busy, v: chrome.runtime.getManifest().version });
        break;
      }
      case 'lists': run('lists', taskLists); sendResponse({ ok: true }); break;
      case 'discover': run('discover', taskDiscover, msg.opts || {}); sendResponse({ ok: true }); break;
      case 'act': run('act', taskAct, msg.opts || {}); sendResponse({ ok: true }); break;
      case 'stop': job.stop = true; job.paused = false; sendResponse({ ok: true }); break;
      case 'pause': job.paused = true; send({ type: 'paused', value: true }); sendResponse({ ok: true }); break;
      case 'resume': job.paused = false; send({ type: 'paused', value: false }); sendResponse({ ok: true }); break;
      default: sendResponse({ ok: false });
    }
    return false;
  });
})();
