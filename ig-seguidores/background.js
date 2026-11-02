// IG Seguidores — service worker
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
