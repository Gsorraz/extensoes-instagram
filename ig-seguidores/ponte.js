// IG Seguidores — ponte dentro da página do Instagram (contexto da própria página).
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
