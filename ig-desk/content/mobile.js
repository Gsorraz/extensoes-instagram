// IG Desk — roda no contexto da própria página do Instagram (world: MAIN),
// só quando ela está dentro da janela do IG Desk.
(() => {
  // janela própria do IG Desk (Instagram em nível superior): marcada com window.name pelo background
  if (window.top !== window || !String(window.name).startsWith('igdesk-')) return;
  // O service worker do Instagram faria requisições fora da aba (sem as regras
  // do IG Desk). Dentro da janela, ele fica desativado.
  try {
    const sw = navigator.serviceWorker;
    if (sw) {
      sw.getRegistrations().then(rs => rs.forEach(r => r.unregister())).catch(() => {});
      Object.defineProperty(ServiceWorkerContainer.prototype, 'register', {
        configurable: true,
        value: function () {
          return Promise.reject(new DOMException('Desativado pelo IG Desk', 'SecurityError'));
        }
      });
    }
  } catch (_) {}

  // Ponte do Crescimento: chama a função do próprio site para seguir/deixar de seguir (ela monta
  // os cabeçalhos e os tokens anti-abuso do pedido). O frame.js pede por window.postMessage.
  window.addEventListener('message', async (e) => {
    if (e.source !== window || !e.data || e.data.__igdBridgeReq !== 1) return;
    const { rid, op, userId } = e.data;
    if (!/^\d{3,20}$/.test(String(userId)) || !['follow', 'unfollow', 'show'].includes(op)) return;
    try {
      const R = window.require;
      if (typeof R !== 'function') throw new Error('o site não expõe o carregador de módulos');
      const api = R('PolarisInstapi');
      let container = 'profile';
      let nav;
      try {
        const inst = R('IGNavChain').getInstance();
        const last = inst.last && inst.last();
        container = R('PolarisContainerModuleUtils').getContainerModule(last && last.pageID) || container;
        nav = inst.getNavChainForSend();
      } catch (_) {}
      const id = String(userId);
      let r;
      if (op === 'show') r = await api.apiGet('/api/v1/friendships/show/{user_id}/', { path: { user_id: id } });
      else if (op === 'follow') {
        r = await api.apiPost('/api/v1/friendships/create/{target_user_id}/', {
          body: { container_module: container, include_follow_friction_check: true, nav_chain: nav, user_id: id },
          path: { target_user_id: id }
        });
      } else {
        r = await api.apiPost('/api/v1/friendships/destroy/{target_user_id}/', {
          body: { container_module: container, nav_chain: nav, user_id: id },
          path: { target_user_id: id }
        });
      }
      window.postMessage({ __igdBridgeRes: 1, rid, ok: true, data: r && r.data, statusCode: r && r.statusCode }, '*');
    } catch (err) {
      window.postMessage({
        __igdBridgeRes: 1, rid, ok: false,
        error: String((err && err.message) || err).slice(0, 200),
        statusCode: err && err.statusCode,
        text: err && err.responseText ? String(err.responseText).slice(0, 300) : ''
      }, '*');
    }
  });

  // Os botões "+" e Story da barra lateral não têm um clique real DENTRO do Instagram,
  // então o Chrome bloquearia o seletor de arquivos dele. O arquivo é escolhido na
  // janela do IG Desk e entregue aqui: quando o Instagram tenta abrir o seletor,
  // o arquivo escolhido entra no lugar, como se você o tivesse selecionado.
  let pendingFile = null;
  let pendingTimer = 0;

  let pendingKind = 'post';

  const giveFile = (input) => {
    if (!pendingFile || input.type !== 'file') return false;
    // arquivo de story só vai para um campo com a assinatura de story (AVIF + PNG): nunca para o
    // de foto de perfil ou outro desconhecido
    if (pendingKind === 'story' && !(/avif/.test(input.accept) && /png/.test(input.accept))) return false;
    // arquivo de publicação só vai para o campo da janela "Criar nova publicação"
    if (pendingKind === 'post' && !input.closest('[role="dialog"]')) return false;
    const f = pendingFile;
    pendingFile = null;
    clearTimeout(pendingTimer);
    try {
      const dt = new DataTransfer();
      dt.items.add(f);
      input.files = dt.files;
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    } catch (_) {
      return false;
    }
  };

  for (const name of ['click', 'showPicker']) {
    const orig = HTMLInputElement.prototype[name];
    if (typeof orig !== 'function') continue;
    Object.defineProperty(HTMLInputElement.prototype, name, {
      configurable: true,
      writable: true,
      value: function () {
        if (giveFile(this)) return undefined;
        return orig.apply(this, arguments);
      }
    });
  }

  window.addEventListener('message', (e) => {
    if (e.source !== window || !e.data || !e.data.__igdFile) return;
    clearTimeout(pendingTimer);
    pendingFile = e.data.file || null;
    pendingKind = e.data.kind === 'story' ? 'story' : 'post';
    if (pendingFile) pendingTimer = setTimeout(() => { pendingFile = null; }, 120000);
  });

  if (window.name !== 'igdesk-mobile') return;

  const UA =
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 ' +
    '(KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1';

  const def = (obj, prop, val) => {
    try {
      Object.defineProperty(obj, prop, { configurable: true, get: () => val });
    } catch (_) {}
  };

  const N = Navigator.prototype;
  def(N, 'userAgent', UA);
  def(N, 'appVersion', UA.replace(/^Mozilla\//, ''));
  def(N, 'platform', 'iPhone');
  def(N, 'vendor', 'Apple Computer, Inc.');
  def(N, 'maxTouchPoints', 5);
  def(N, 'userAgentData', undefined);

  // Tela de celular em retrato. Sem isso o Instagram vê o monitor (paisagem) e,
  // na criação de story, mostra "Gire seu dispositivo para adicionar ao seu story".
  const S = Screen.prototype;
  def(S, 'width', 412);
  def(S, 'height', 915);
  def(S, 'availWidth', 412);
  def(S, 'availHeight', 915);
  if (typeof ScreenOrientation !== 'undefined') {
    def(ScreenOrientation.prototype, 'type', 'portrait-primary');
    def(ScreenOrientation.prototype, 'angle', 0);
  }
  def(window, 'orientation', 0); // propriedade antiga do iOS/Safari
})();
