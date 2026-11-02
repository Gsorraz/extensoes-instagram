#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador da extensão IG Seguidores (Chrome, Manifest V3).

Rode este arquivo (no VS Code: botão ▶ ou `python gerar_ig_seguidores.py`).
Ele cria a pasta `ig-seguidores` ao lado deste script e um `ig-seguidores.zip`.

Depois, no Chrome:
  1. chrome://extensions
  2. Ligue "Modo do desenvolvedor"
  3. "Carregar sem compactação" -> escolha a pasta ig-seguidores
  4. Clique no ícone (ou Alt+Shift+F)

Para mudar algo: edite o texto do arquivo dentro de FILES abaixo e rode de novo.
ATENÇÃO: cada execução apaga e recria a pasta ig-seguidores; faça as mudanças aqui, neste script.
"""

import shutil
import struct
import sys
import zlib
import zipfile
from pathlib import Path

NOME_PASTA = "ig-seguidores"

FILES = {}

# ===== README.md =====
FILES['README.md'] = r'''# IG Seguidores — extensão do Chrome

Painel para ver e organizar quem você segue e quem te segue, no estilo de "InstaUnfollow" e "Followers Tracker",
com ações em lote **limitadas e confirmadas**. Tudo roda no seu navegador, com o seu login; nada é enviado a servidores.

## Instalar (modo desenvolvedor)

1. Abra `chrome://extensions`
2. Ligue **Modo do desenvolvedor**
3. **Carregar sem compactação** → escolha a pasta `ig-seguidores`
4. Clique no ícone (ou **Alt+Shift+F**): abre o painel numa aba

Você precisa estar logado no Instagram neste Chrome.

## O que o painel mostra

| Aba | O que é |
|---|---|
| **Não me seguem de volta** | Contas que você segue e que não te seguem |
| **Fãs** | Contas que te seguem e que você não segue |
| **Mútuos** | Se seguem nos dois sentidos |
| **Seguindo / Seguidores** | As listas completas |
| **Novos seguidores / Deixaram de me seguir** | Comparação com uma leitura anterior (guarda as últimas 5) |
| **Descobrir** | Contas para seguir: sugestões do Instagram ou seguidores de um perfil que você escolher |
| **Protegidos** | Contas marcadas com ★: nunca são deixadas de seguir |

Cada lista tem busca, filtros (ocultar verificadas/privadas), ordenação, seleção em lote e **Exportar CSV**.

## Como usar

1. **Atualizar listas** (leva de 1 a vários minutos, conforme o tamanho da conta). Uma janelinha do Instagram abre
   no canto da tela: deixe-a aberta e **visível** (sem minimizar nem cobrir por completo), senão o Chrome
   desacelera o trabalho dela.
2. Abra uma aba, marque as contas (ou "Selecionar todas") e use o botão de ação.
3. Antes de rodar, aparece uma confirmação com o total, o tempo estimado e os limites.
4. **Parar** interrompe na hora. Se o Instagram recusar qualquer ação, a ferramenta para sozinha.

**Primeira vez: use 1 conta** (Máx. = 1) e confira no Instagram que a ação realmente aconteceu. Depois suba aos poucos,
20 a 40 por dia, e não todos os dias.

## Seguir pessoas novas automaticamente

Na aba **Descobrir**, informe até 5 perfis do seu nicho (ou deixe vazio para usar as sugestões do Instagram) e clique em
**Buscar e seguir automaticamente**. A ferramenta junta os seguidores desses perfis e segue só gente **nova**. Ela nunca segue:

- quem você já segue;
- quem já te segue (essas contas estão na aba **Fãs**, para seguir de volta se você quiser, à parte);
- quem você já deixou de seguir, seja pela ferramenta ou **à mão** (detectado ao comparar duas leituras);
- perfis privados.

## Fila e limite do dia

O limite do Instagram para este tipo de ação é baixo. Marque **Usar todo o limite do dia** para gastar os 150 de uma vez, ou
defina o máximo por execução. O que sobrar vai para a **Fila** (aparece no painel e fica guardada): amanhã, clique em
**Continuar fila**. Ela reconfere cada conta antes (por exemplo, ignora quem você já deixou de seguir nesse meio-tempo).

## Pausar, retomar e proteger contas

- **Pausar / Retomar:** vale a partir da próxima ação (a que já estava em andamento termina).
- **Descanso:** a cada 10 ações há uma pausa maior (2 a 4 min), além da pausa normal entre cada uma.
- **Protegidos (★):** na aba **Protegidos** dá para **exportar** a lista (JSON), **importar** de volta e **colar @usuários**
  de uma vez. Só entram contas que aparecem nas suas listas.

## Segurança

- Limite diário de **150** para seguir e **150** para deixar de seguir; pausa aleatória (mín. 20 s) entre ações.
- Contas protegidas (★) nunca são deixadas de seguir; perfis privados da aba Descobrir são ignorados.
- Não deixa de seguir ninguém sem ter lido a lista completa de seguidores.
- **Dois métodos:** se o método do próprio site não surtir efeito, tenta o alternativo (endpoint `web/friendships`, o mesmo do projeto InstagramUnfollowers), confere de novo e lembra qual funcionou. Se o Instagram sinalizar bloqueio (429, 400, `feedback_required`, `checkpoint`), **para tudo** sem tentar outro método.
- **Confere cada ação:** só conta como feita se o Instagram confirmar que a conta realmente passou a ser (ou deixou de ser) seguida. Os pedidos são feitos chamando a própria função do site (os mesmos cabeçalhos e tokens anti-abuso do botão Seguir/Seguindo). Se ele responder "ok" sem efeito, a ferramenta para, não conta e mostra a resposta dele.
- **Seguir e deixar de seguir em massa viola os termos do Instagram** e pode limitar ou bloquear a conta.

## Permissões

- `host_permissions` do instagram.com: fazer as mesmas chamadas que o site faz; e do CDN de imagens do Instagram (fbcdn.net / cdninstagram.com): só para mostrar as fotos de perfil.
- `scripting`: colocar o coletor na aba do Instagram que já estava aberta.
- `tabs`: abrir/focar o painel e a janelinha do Instagram.
- `storage` / `unlimitedStorage`: guardar as listas e preferências neste navegador.
'''

# ===== manifest.json =====
FILES['manifest.json'] = r'''{
  "manifest_version": 3,
  "name": "IG Seguidores",
  "version": "1.3.0",
  "description": "Veja quem não te segue de volta, seus fãs, novos seguidores e quem deixou de seguir; siga e deixe de seguir com limites e confirmação.",
  "minimum_chrome_version": "111",
  "icons": {
    "16": "icons/icon16.png",
    "32": "icons/icon32.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "action": {
    "default_title": "Abrir IG Seguidores",
    "default_icon": {
      "16": "icons/icon16.png",
      "32": "icons/icon32.png"
    }
  },
  "background": {
    "service_worker": "background.js"
  },
  "permissions": ["storage", "unlimitedStorage", "scripting", "tabs"],
  "host_permissions": ["https://*.instagram.com/*", "https://*.fbcdn.net/*", "https://*.cdninstagram.com/*"],
  "content_scripts": [
    {
      "matches": ["https://*.instagram.com/*"],
      "js": ["coletor.js"],
      "run_at": "document_idle",
      "all_frames": false
    },
    {
      "matches": ["https://*.instagram.com/*"],
      "js": ["ponte.js"],
      "run_at": "document_idle",
      "all_frames": false,
      "world": "MAIN"
    }
  ],
  "commands": {
    "_execute_action": {
      "suggested_key": { "default": "Alt+Shift+F" },
      "description": "Abrir IG Seguidores"
    }
  }
}
'''

# ===== background.js =====
FILES['background.js'] = r'''// IG Seguidores — service worker
// Abre (ou traz para a frente) a tela do painel quando você clica no ícone ou usa Alt+Shift+F.

chrome.action.onClicked.addListener(async () => {
  const url = chrome.runtime.getURL('painel.html');
  const abertas = await chrome.tabs.query({ url });
  if (abertas.length) {
    await chrome.tabs.update(abertas[0].id, { active: true });
    await chrome.windows.update(abertas[0].windowId, { focused: true });
  } else {
    await chrome.tabs.create({ url });
  }
});
'''

# ===== coletor.js =====
FILES['coletor.js'] = r'''// IG Seguidores — script da página do Instagram.
// Faz as mesmas chamadas que o site faz (mesma origem, com o seu login) e manda o resultado ao painel.
// Só age quando o painel pede; nada roda sozinho.
(() => {
  if (window.__igsLoaded) return;
  window.__igsLoaded = true;

  const IG_APP_ID = '936619743392459';
  const DAILY_MAX = 150;
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

  async function myUsername(id) {
    try {
      const d = await api('/api/v1/users/' + id + '/info/');
      if (d && d.user && d.user.username) return d.user.username;
    } catch (_) {}
    for (const a of document.querySelectorAll('a[href^="/"]')) {
      const m = (a.getAttribute('href') || '').match(/^\/([A-Za-z0-9._]{1,30})\/$/);
      if (m && a.querySelector('img') && !['explore', 'reels', 'direct', 'accounts'].includes(m[1])) return m[1];
    }
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
    const st = await chrome.storage.local.get({ day: null });
    const day = st.day && st.day.date === today() ? st.day : { date: today(), follow: 0, unfollow: 0 };
    const left = DAILY_MAX - day[op];
    if (left <= 0) throw new Fail('Limite diário (' + DAILY_MAX + ') já atingido. Volte amanhã.');
    const minD = Math.max(0, Number(opts.minDelay) || 0);
    const maxD = Math.max(minD, Number(opts.maxDelay) || minD);
    const list = (opts.users || []).slice(0, Math.min(left, Math.max(1, Number(opts.limit) || 1)));
    let done = 0;
    for (const u of list) {
      checkStop();
      await whilePaused();
      await doAction(op, u);
      done++;
      day[op]++;
      await chrome.storage.local.set({ day });
      send({ type: 'act', op, done, total: list.length, user: u, day });
      if (done < list.length) {
        await wait(rand(minD, maxD) * 1000);
        // descanso mais longo a cada 10 ações (o InstagramUnfollowers descansa 5 min a cada 5)
        if (done % 10 === 0) {
          const s = Math.round(rand(120, 240));
          send({ type: 'progress', text: 'Descanso de segurança: ' + s + 's (a cada 10 ações)…' });
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
'''

# ===== ponte.js =====
FILES['ponte.js'] = r'''// IG Seguidores — ponte dentro da página do Instagram (contexto da própria página).
// Chama a mesma função que o botão "Seguir"/"Seguindo" do site chama (PolarisInstapi), que monta
// sozinha os cabeçalhos e o token anti-abuso do pedido. Só responde a pedidos do coletor.js.
(() => {
  if (window.__igsPonte) return;
  window.__igsPonte = true;

  function modulos() {
    const R = window.require;
    if (typeof R !== 'function') throw new Error('o site não expõe o carregador de módulos');
    return { api: R('PolarisInstapi'), cm: R('PolarisContainerModuleUtils'), nc: R('IGNavChain') };
  }

  async function chamar(op, userId) {
    const { api, cm, nc } = modulos();
    let container = 'profile';
    let nav;
    try {
      const inst = nc.getInstance();
      const last = inst.last && inst.last();
      container = cm.getContainerModule(last && last.pageID) || container;
      nav = inst.getNavChainForSend();
    } catch (_) {}
    if (op === 'show') {
      return api.apiGet('/api/v1/friendships/show/{user_id}/', { path: { user_id: userId } });
    }
    if (op === 'follow') {
      return api.apiPost('/api/v1/friendships/create/{target_user_id}/', {
        body: { container_module: container, include_follow_friction_check: true, nav_chain: nav, user_id: userId },
        path: { target_user_id: userId }
      });
    }
    return api.apiPost('/api/v1/friendships/destroy/{target_user_id}/', {
      body: { container_module: container, nav_chain: nav, user_id: userId },
      path: { target_user_id: userId }
    });
  }

  window.addEventListener('message', async (e) => {
    if (e.source !== window || !e.data || e.data.__igsReq !== 1) return;
    const { rid, op, userId } = e.data;
    if (!/^\d{3,20}$/.test(String(userId)) || !['follow', 'unfollow', 'show'].includes(op)) return;
    try {
      const r = await chamar(op, String(userId));
      window.postMessage({ __igsRes: 1, rid, ok: true, data: r && r.data, statusCode: r && r.statusCode }, '*');
    } catch (err) {
      window.postMessage({
        __igsRes: 1, rid, ok: false,
        error: String((err && err.message) || err).slice(0, 200),
        statusCode: err && err.statusCode,
        text: err && err.responseText ? String(err.responseText).slice(0, 300) : ''
      }, '*');
    }
  });
})();
'''

# ===== painel.html =====
FILES['painel.html'] = r'''<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>IG Seguidores</title>
  <link rel="stylesheet" href="painel.css">
</head>
<body>
  <header class="top">
    <div class="brand">
      <h1>IG Seguidores</h1>
      <p class="sub" id="status">Clique em <b>Atualizar listas</b> para começar.</p>
    </div>
    <div class="top-actions">
      <button id="btn-refresh" class="primary">Atualizar listas</button>
      <button id="btn-pause" class="ghost" disabled>Pausar</button>
      <button id="btn-stop" class="ghost" disabled>Parar</button>
      <button id="btn-csv" class="ghost">Exportar CSV</button>
    </div>
  </header>

  <p class="warn">Seguir e deixar de seguir em massa viola os termos do Instagram e pode limitar ou bloquear a conta. Use poucas ações por dia, comece com 1 conta para conferir, e mantenha a janelinha do Instagram aberta e <b>visível</b> (sem minimizar) enquanto roda.</p>

  <div class="bar" id="progress" hidden>
    <div class="bar-fill" id="progress-fill"></div>
  </div>

  <nav class="tabs" id="tabs" aria-label="Listas"></nav>

  <section class="tools">
    <input type="search" id="q" placeholder="Buscar por usuário ou nome" autocomplete="off">
    <label class="chk"><input type="checkbox" id="f-ver"> Ocultar verificadas</label>
    <label class="chk"><input type="checkbox" id="f-priv"> Ocultar privadas</label>
    <label class="sel">Ordem
      <select id="f-sort"><option value="rec">Mais recentes</option><option value="az">A–Z</option></select>
    </label>
  </section>

  <section class="discover" id="discover" hidden>
    <label>Seguidores de @ (até 5 perfis, separados por vírgula; vazio = sugestões do Instagram)
      <input type="text" id="d-src" placeholder="perfil1, perfil2" autocomplete="off">
    </label>
    <button id="btn-discover" class="ghost">Só buscar contas</button>
    <button id="btn-autofollow" class="primary">Buscar e seguir automaticamente</button>
    <p class="note">Nunca segue quem você já segue, quem já te segue, quem você já deixou de seguir (pela ferramenta ou à mão), nem perfis privados. Escolha perfis do seu nicho: contas do mesmo público tendem a seguir de volta.</p>
  </section>

  <section class="discover" id="prot-tools" hidden>
    <button id="prot-export" class="ghost">Exportar protegidos (JSON)</button>
    <button id="prot-import" class="ghost">Importar protegidos (JSON)</button>
    <input type="file" id="prot-file" accept=".json,application/json" hidden>
    <label>Colar @usuários para proteger (separados por vírgula, espaço ou linha)
      <textarea id="prot-text" rows="2" placeholder="amigo1, amigo2, cliente3"></textarea>
    </label>
    <button id="prot-paste" class="primary">Proteger estes</button>
    <p class="note">Só entram contas que aparecem nas suas listas de seguindo ou seguidores. Contas protegidas (★) nunca são deixadas de seguir.</p>
  </section>

  <section class="actionbar">
    <label class="chk"><input type="checkbox" id="sel-all"> Selecionar todas (<span id="n-filtered">0</span>)</label>
    <span class="grow"></span>
    <label class="chk"><input type="checkbox" id="p-all"> Usar todo o limite do dia</label>
    <label class="num">Máx. nesta execução <input type="number" id="p-limit" min="1" max="150" value="40"></label>
    <label class="num">Pausa (s, mín. 20) <input type="number" id="p-delay" min="20" max="120" value="30"></label>
    <button id="btn-act" class="danger" disabled>Ação</button>
  </section>
  <p class="daily" id="daily"></p>

  <section class="queue" id="queue" hidden>
    <span id="queue-text"></span>
    <button id="queue-go" class="primary">Continuar fila</button>
    <button id="queue-clear" class="ghost">Limpar fila</button>
  </section>

  <main class="list" id="list"></main>
  <div class="more"><button id="btn-more" class="ghost" hidden>Mostrar mais</button></div>

  <div class="toast" id="toast" role="status" hidden></div>
  <script src="painel.js"></script>
</body>
</html>
'''

# ===== painel.css =====
FILES['painel.css'] = r''':root {
  --bg: #0e0f13;
  --card: #16181f;
  --line: #262933;
  --fg: #e9eaee;
  --muted: #8b8f9c;
  --hover: #1f222b;
  --accent: #7c5cff;
  --accent-2: #f0576b;
  --ok: #3ecf8e;
  --radius: 12px;
  color-scheme: dark;
}

* { box-sizing: border-box; }
html, body { margin: 0; background: var(--bg); color: var(--fg); font: 14px/1.45 system-ui, "Segoe UI", Roboto, sans-serif; }
body { max-width: 980px; margin: 0 auto; padding: 18px 18px 90px; }

.top { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; }
.brand h1 { margin: 0 0 2px; font-size: 22px; }
.sub { margin: 0; color: var(--muted); }
.top-actions { display: flex; gap: 8px; flex-wrap: wrap; }

button {
  font: inherit; cursor: pointer; border: 1px solid var(--line); border-radius: 10px; padding: 8px 14px;
  background: var(--hover); color: var(--fg);
}
button:hover:not(:disabled) { filter: brightness(1.15); }
button:disabled { opacity: .45; cursor: not-allowed; }
button.primary { background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 650; }
button.danger { background: var(--accent-2); border-color: var(--accent-2); color: #fff; font-weight: 650; }
button.ghost { background: transparent; }

.warn {
  margin: 14px 0 10px; padding: 9px 12px; font-size: 12.5px; border-radius: 10px;
  background: rgba(240, 87, 107, .1); color: #ffb3bd; border: 1px solid rgba(240, 87, 107, .35);
}

.bar { height: 6px; border-radius: 6px; background: var(--hover); overflow: hidden; margin: 0 0 10px; }
.bar[hidden] { display: none; }
.bar-fill { height: 100%; width: 0; background: linear-gradient(90deg, var(--accent), var(--accent-2)); transition: width .3s; }
.bar-fill.indeterminate { width: 40%; animation: slide 1.1s ease-in-out infinite alternate; }
@keyframes slide { from { margin-left: 0; } to { margin-left: 60%; } }

.tabs { display: flex; gap: 6px; flex-wrap: wrap; margin: 8px 0 12px; }
.tab {
  padding: 7px 12px; border-radius: 999px; font-size: 13px; border: 1px solid var(--line); background: var(--card);
}
.tab b { color: var(--muted); font-weight: 600; margin-left: 4px; }
.tab.on { background: var(--accent); border-color: var(--accent); color: #fff; }
.tab.on b { color: #e6dfff; }

.tools { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 10px; }
.tools input[type=search] { flex: 1; min-width: 200px; }
input[type=search], input[type=text], input[type=number], select {
  font: inherit; color: var(--fg); background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 8px 10px;
}
.chk { display: inline-flex; align-items: center; gap: 6px; color: var(--muted); font-size: 13px; }
.sel { color: var(--muted); font-size: 13px; display: inline-flex; gap: 6px; align-items: center; }

.discover { display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap; margin: 0 0 12px; padding: 12px; border: 1px solid var(--line); border-radius: var(--radius); background: var(--card); }
.discover[hidden] { display: none; }
.discover label { display: grid; gap: 4px; color: var(--muted); font-size: 12.5px; flex: 1; min-width: 220px; }
.discover .note { flex-basis: 100%; margin: 0; color: var(--muted); font-size: 12.5px; }
.discover textarea {
  font: inherit; color: var(--fg); background: var(--card); border: 1px solid var(--line); border-radius: 10px;
  padding: 8px 10px; resize: vertical;
}

.actionbar {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap; padding: 10px 12px; margin: 0 0 4px;
  border: 1px solid var(--line); border-radius: var(--radius); background: var(--card);
  position: sticky; top: 0; z-index: 5;
}
.actionbar .grow { flex: 1; }
.num { color: var(--muted); font-size: 12.5px; display: inline-flex; gap: 6px; align-items: center; }
.num input { width: 70px; padding: 6px 8px; }
.daily { margin: 6px 2px 10px; color: var(--muted); font-size: 12.5px; }

.queue {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin: 0 0 12px; padding: 10px 12px;
  border: 1px solid rgba(124, 92, 255, .5); border-radius: var(--radius); background: rgba(124, 92, 255, .1);
}
.queue[hidden] { display: none; }
.queue #queue-text { flex: 1; min-width: 220px; }

.list { display: grid; gap: 4px; }
.row {
  display: grid; grid-template-columns: 26px 44px 1fr auto; gap: 12px; align-items: center;
  padding: 8px 12px; border: 1px solid var(--line); border-radius: 10px; background: var(--card);
}
.row:hover { background: var(--hover); }
.row.protegido { border-color: rgba(240, 190, 80, .45); }
.av, .av-fb {
  width: 44px; height: 44px; border-radius: 50%; object-fit: cover; background: var(--hover);
  display: grid; place-items: center; font-weight: 700; color: var(--muted);
}
.who { min-width: 0; }
.who a { color: var(--fg); text-decoration: none; font-weight: 650; }
.who a:hover { text-decoration: underline; }
.who .nm { color: var(--muted); font-size: 12.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.badge { font-size: 11px; margin-left: 6px; padding: 1px 6px; border-radius: 6px; background: var(--hover); color: var(--muted); }
.star { all: unset; cursor: pointer; font-size: 18px; color: var(--muted); padding: 4px 6px; border-radius: 8px; }
.star:hover { background: var(--hover); }
.star.on { color: #f0be50; }
.empty { text-align: center; color: var(--muted); padding: 40px 10px; }
.more { text-align: center; margin: 14px 0; }

.toast {
  position: fixed; left: 50%; bottom: 22px; transform: translateX(-50%); background: #23262f; color: var(--fg);
  border: 1px solid var(--line); padding: 10px 16px; border-radius: 10px; z-index: 20; max-width: 90vw;
  box-shadow: 0 8px 24px rgba(0, 0, 0, .4);
}
.toast[hidden] { display: none; }
'''

# ===== painel.js =====
FILES['painel.js'] = r'''// IG Seguidores — painel
// Lista quem não te segue de volta, fãs, novos/perdidos e descobre contas; segue e deixa de seguir
// com limite diário, pausa aleatória e confirmação. Os dados ficam só neste navegador.

const $ = (s) => document.querySelector(s);
const IG = 'https://www.instagram.com/';
const DAILY_MAX = 150;
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

window.addEventListener('error', (e) => toast('Erro: ' + e.message));
window.addEventListener('unhandledrejection', (e) => toast('Erro: ' + ((e.reason && e.reason.message) || e.reason)));

// ---------------- dados ----------------

let saveTimer = 0;
function save(now) {
  clearTimeout(saveTimer);
  const go = () => chrome.storage.local.set({
    data, snaps, prot: [...prot], seen: [...seen].slice(-5000), unfollowed: [...unf], day, queue,
    prefs: { limit: Number($('#p-limit').value), delay: Number($('#p-delay').value), all: $('#p-all').checked, hv: $('#f-ver').checked, hp: $('#f-priv').checked }
  });
  if (now) go(); else saveTimer = setTimeout(go, 800);
}

async function load() {
  const s = await chrome.storage.local.get({ data: null, snaps: [], prot: [], seen: [], unfollowed: [], day: null, prefs: null, queue: null });
  data = s.data;
  unf = new Set(s.unfollowed);
  queue = s.queue && s.queue.users && s.queue.users.length ? s.queue : null;
  snaps = s.snaps;
  prot = new Set(s.prot);
  seen = new Set(s.seen);
  day = s.day && s.day.date === today() ? s.day : { date: today(), follow: 0, unfollow: 0 };
  if (s.prefs) {
    $('#p-limit').value = s.prefs.limit || 40;
    $('#p-delay').value = s.prefs.delay || 30;
    $('#p-all').checked = !!s.prefs.all;
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
async function ensureIg() {
  const { igWin } = await chrome.storage.session.get('igWin');
  let tabId = igWin && igWin.tabId;
  if (tabId != null) {
    try { const t = await chrome.tabs.get(tabId); if (!/instagram\.com/.test(t.url || '')) tabId = null; } catch (_) { tabId = null; }
  }
  if (tabId == null) {
    const w = await chrome.windows.create({
      url: IG, type: 'popup', width: 420, height: 640, left: Math.max(0, screen.availWidth - 440), top: 40, focused: false
    });
    tabId = w.tabs[0].id;
    await chrome.storage.session.set({ igWin: { tabId, windowId: w.id } });
    for (let i = 0; i < 40; i++) { const t = await chrome.tabs.get(tabId); if (t.status === 'complete') break; await wait(500); }
  }
  await chrome.scripting.executeScript({ target: { tabId }, files: ['coletor.js'] }).catch(() => {});
  await chrome.scripting.executeScript({ target: { tabId }, files: ['ponte.js'], world: 'MAIN' }).catch(() => {});
  let r = null;
  for (let i = 0; i < 10 && !r; i++) { r = await igMsg(tabId, 'ping'); if (!r) await wait(700); }
  if (!r) throw new Error('Não consegui falar com a página do Instagram. Recarregue a janelinha dele e tente de novo.');
  if (!r.loggedIn) throw new Error('Você não está logado no Instagram. Entre na janelinha que abri e clique de novo.');
  return tabId;
}

async function start(cmd, extra, kind) {
  try {
    setRunning(kind);
    setStatus('Conectando ao Instagram…');
    const tabId = await ensureIg();
    $('#btn-stop').dataset.tab = String(tabId);
    const r = await igMsg(tabId, cmd, extra);
    if (!r || !r.ok) throw new Error('O Instagram não aceitou o comando.');
  } catch (e) {
    setRunning(null);
    toast(e.message);
    setStatus(statusLine());
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
      if (m.type === 'error') toast(m.text);
      setStatus(m.text || statusLine());
      break;
    case 'idle':
      setRunning(null);
      render();
      break;
  }
});

function onLists(m) {
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
  const delay = clamp(parseInt($('#p-delay').value, 10) || 30, 20, 120);
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
  const mins = Math.max(1, Math.round((n * delay * 1.3) / 60));
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
  await start('act', { opts: { op, users: users.slice(0, n).map((u) => ({ id: u.id, u: u.u })), limit: n, minDelay: delay, maxDelay: Math.round(delay * 1.6) } }, 'act');
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
for (const [id, lo, hi] of [['#p-limit', 1, DAILY_MAX], ['#p-delay', 20, 120]]) {
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

(async function init() {
  await load();
  derive();
  render();
})();
'''



# ---------------------------------------------------------------------------
# Ícones (desenhados aqui, sem arquivos binários embutidos)
# ---------------------------------------------------------------------------
def _png(size, rgba):
    raw = bytearray()
    row = size * 4
    for y in range(size):
        raw.append(0)
        raw += rgba[y * row:(y + 1) * row]

    def chunk(tag, body):
        c = struct.pack(">I", len(body)) + tag + body
        return c + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def _inside_round_square(x, y, r=0.22):
    cx = min(max(x, r), 1 - r)
    cy = min(max(y, r), 1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def _person(x, y, hx, hy, hr, bx, by, brx, bry, floor):
    if (x - hx) ** 2 + (y - hy) ** 2 <= hr * hr:
        return True
    if y <= floor and ((x - bx) / brx) ** 2 + ((y - by) / bry) ** 2 <= 1:
        return True
    return False


def icone(size):
    ss = 3
    out = bytearray(size * size * 4)
    for py in range(size):
        for px in range(size):
            r = g = b = a = 0.0
            for sy in range(ss):
                for sx in range(ss):
                    x = (px + (sx + 0.5) / ss) / size
                    y = (py + (sy + 0.5) / ss) / size
                    if not _inside_round_square(x, y):
                        continue
                    t = (x + y) / 2
                    cr, cg, cb = 124 + (240 - 124) * t, 92 + (87 - 92) * t, 255 + (107 - 255) * t
                    if _person(x, y, 0.66, 0.34, 0.10, 0.68, 0.74, 0.18, 0.20, 0.86):
                        cr, cg, cb = cr * 0.45 + 255 * 0.55, cg * 0.45 + 255 * 0.55, cb * 0.45 + 255 * 0.55
                    if _person(x, y, 0.40, 0.38, 0.13, 0.40, 0.84, 0.25, 0.28, 0.90):
                        cr, cg, cb = 255, 255, 255
                    r += cr; g += cg; b += cb; a += 1.0
            n = ss * ss
            i = (py * size + px) * 4
            if a:
                out[i], out[i + 1], out[i + 2] = int(r / a), int(g / a), int(b / a)
            out[i + 3] = int(255 * a / n)
    return _png(size, out)


def gerar(destino: Path) -> None:
    if destino.exists():
        shutil.rmtree(destino)
    for rel, conteudo in FILES.items():
        arq = destino / rel
        arq.parent.mkdir(parents=True, exist_ok=True)
        # write_bytes: `newline=` em write_text só existe no Python 3.10+
        arq.write_bytes(conteudo.encode("utf-8"))
    for tam in (16, 32, 48, 128):
        arq = destino / "icons" / ("icon%d.png" % tam)
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_bytes(icone(tam))


def zipar(pasta: Path) -> Path:
    zip_path = pasta.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for arq in sorted(pasta.rglob("*")):
            if arq.is_file():
                z.write(arq, Path(pasta.name) / arq.relative_to(pasta))
    return zip_path


def main() -> int:
    base = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
    destino = base / NOME_PASTA
    gerar(destino)
    zip_path = zipar(destino)
    print("OK: %d arquivos + 4 ícones gerados em %s" % (len(FILES), destino))
    print("ZIP: %s" % zip_path)
    print()
    print("Para instalar no Chrome:")
    print("  1. Abra chrome://extensions")
    print("  2. Ligue 'Modo do desenvolvedor'")
    print("  3. 'Carregar sem compactação' -> %s" % destino)
    print("  4. Clique no ícone do IG Seguidores (ou Alt+Shift+F)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
