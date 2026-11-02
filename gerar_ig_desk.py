#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador da extensão IG Desk (Chrome, Manifest V3): Instagram em janela própria + janela de ferramentas.

Rode este arquivo (no VS Code: botão ▶ ou `python gerar_ig_desk.py`).
Ele cria a pasta `ig-desk` ao lado deste script e um `ig-desk.zip`.

Depois, no Chrome:
  1. chrome://extensions
  2. Ligue "Modo do desenvolvedor"
  3. "Carregar sem compactação" -> escolha a pasta ig-desk

Para mudar algo: edite o texto do arquivo dentro de FILES abaixo,
rode de novo e clique em recarregar a extensão em chrome://extensions.
ATENÇÃO: cada execução apaga e recria a pasta ig-desk. Edições feitas direto
nos arquivos dela se perdem; faça as mudanças aqui, neste script.
"""

import base64
import shutil
import sys
import zipfile
from pathlib import Path

NOME_PASTA = "ig-desk"

# ---------------------------------------------------------------------------
# Arquivos de texto da extensão
# ---------------------------------------------------------------------------
FILES = {}

# ===== README.md =====
FILES['README.md'] = r'''# IG Desk — extensão do Chrome

Instagram numa **janela própria** (como no celular, ou como no computador) e uma **janela de
ferramentas** ao lado, com editor de story, seguir/deixar de seguir e controles de vídeo.

## Instalar (modo desenvolvedor)

1. Abra `chrome://extensions`
2. Ligue **Modo do desenvolvedor** (canto superior direito)
3. Clique **Carregar sem compactação** e escolha a pasta `ig-desk`
4. Clique no ícone da extensão (ou **Alt+Shift+I**): abrem as duas janelas

Atualizando de uma versão antiga: clique em recarregar o IG Desk, **feche as duas janelas** e abra de novo.
Se o Chrome mostrar a extensão desativada por permissão nova, remova e use "Carregar sem compactação" de novo.

## As duas janelas

- **Instagram:** o site em nível superior (login e cookies normais, cliques reais). Só essa janela recebe o
  disfarce de celular; suas abas normais do Instagram não são tocadas.
- **Ferramentas:** barra lateral, Crescimento, editor de story e diagnóstico. Fechar uma janela fecha a outra.

## Botões da barra lateral

| Botão | O que faz |
|---|---|
| ← → ⟳ | Voltar, avançar, recarregar |
| Início, Explorar, Reels, Mensagens, Perfil | Navegação rápida |
| **+** (colorido) | Nova publicação (post/reel). Existe só no **modo computador**; você escolhe o arquivo e segue as etapas do Instagram |
| **Story** (círculo tracejado) | Escolhe a foto e abre o **editor de story**; o resultado vai para o criador de story do Instagram. Só no **modo celular** |
| Pessoa com seta | **Crescimento**: deixar de seguir quem não te segue, seguir de volta, seguir novos |
| Celular / computador | Troca o layout da janela do Instagram |
| Lua | Dark mode |
| Seta para fora | Abre a página atual numa aba normal do Chrome |
| Engrenagem | Barra de vídeo, lembrar volume, zoom, atalho, diagnóstico |

**Barra de vídeo:** passe o mouse sobre um vídeo/reel → play/pausa, tempo, avançar/voltar, mudo, volume,
velocidade e janela flutuante (PiP).

## Editor de story

Escolha uma foto no botão Story. O editor tem:

- **Bandeja de Adesivos** (como a do celular, com busca): Localização, @Menção, #Hashtag, Data, Hora,
  Temperatura, GIF (imagem), e os cartões Sua vez, Perguntas, Enquete, Emoji, Link, Contagem regressiva e Música.
- 9 efeitos (P&B, Sépia, Vívido, Frio, Quente, Vintage, Drama, Esmaecido), brilho e enquadramento.
- Texto com atalhos para `#hashtag`, `@menção` e `📍 local`, 24 emojis, figurinhas de imagem, lápis e desfazer.

**Se você escolher a foto pelo próprio Instagram** (clicando no seu story), o editor não abre sozinho: use o botão **✨ Efeitos e adesivos** que aparece no canto da tela de story do Instagram; ele leva a foto ao editor e o resultado volta ao Instagram.

**Segurança do envio:** o arquivo só é entregue direto a um campo com a assinatura de story (aceita AVIF e PNG). Campos de foto de perfil e outros desconhecidos nunca recebem arquivo. Se o Instagram não mostrar o seu story na tela, o arquivo fica à espera (2 min) e é usado quando você tocar no botão de story do próprio Instagram.

Arraste os itens na imagem; o controle de tamanho vale para o item selecionado. Tudo é gravado na imagem
(1080×1920) e enviada ao Instagram; você confere e toca em **Compartilhar story** lá.

**Limites reais do Instagram na web (testados):**

- O story pela web **só aceita foto**. Foi testado entregar um vídeo com áudio: o Instagram ignora. Por isso
  não há música, trecho/duração de música nem GIF animado.
- Os adesivos marcados **só visual** (Sua vez, Perguntas, Enquete, Emoji, Link, Contagem, Música) aparecem como
  no app, mas **não funcionam**: ninguém vota, responde, toca ou ouve. O Instagram só libera isso no app
  (use um emulador Android se precisar do app completo).
## Crescimento (automação)

Automatizar seguir/deixar de seguir **viola os termos do Instagram** e pode limitar ou bloquear a conta.
Para reduzir o risco, a ferramenta:

- mostra quantas contas serão afetadas e pede confirmação antes de começar;
- respeita um limite diário (150 por tipo de ação) e uma pausa aleatória entre ações (mín. 20 s);
- ignora contas verificadas (opcional) e perfis privados ao seguir;
- não deixa de seguir ninguém se não conseguir ler a lista completa dos seus seguidores;
- para na hora se o Instagram recusar qualquer ação ou se você clicar em **Parar**.

Primeiro use **1** conta para conferir que a ação realmente acontece no Instagram; depois suba aos poucos.
A leitura das listas pode levar vários minutos. Mantenha as janelas abertas e **não recarregue** o Instagram
durante a execução.

## Permissões

- `declarativeNetRequest`: aplica o User-Agent de iPhone **somente** na aba do IG Desk (modo celular).
- `scripting`: marca a aba do IG Desk (nome da janela) para que os scripts só ajam nela.
- `tabs`: abrir/recarregar/dar zoom na aba do IG Desk.
- `storage`: guardar suas preferências.
- Acesso a `instagram.com`. Nada é enviado a servidores de terceiros.

## Como funciona

- `background.js` abre as duas janelas, aplica as regras de rede por aba e leva os comandos entre elas.
- `content/mobile.js` (no contexto da página) faz o disfarce de celular (tela, plataforma, toque) só na janela do IG Desk.
- `content/frame.js` faz dark mode, barra de vídeo, volume lembrado, Crescimento e entrega de arquivos ao Instagram.
- `app.html/app.js` é a janela de ferramentas.

## Se algo não abrir

Em **Configurações → Copiar diagnóstico da tela**: mostra o que o Instagram exibe (rótulos de botões, campos de
arquivo) para ajustar a extensão. Erros: `chrome://extensions` → IG Desk → **service worker**.
'''

# ===== app.css =====
FILES['app.css'] = r''':root {
  --bg: #0e0f13;
  --side: #15171d;
  --line: #262933;
  --fg: #e9eaee;
  --muted: #8b8f9c;
  --hover: #22252e;
  --active: #2c3040;
  --accent: #f0576b;
  --accent-2: #ff9f5a;
  --radius: 22px;
  color-scheme: dark;
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  height: 100%;
  background: var(--bg);
  color: var(--fg);
  font: 14px/1.4 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  overflow: hidden;
}

body {
  display: grid;
  grid-template-columns: 56px 1fr;
}

/* ---------- barra lateral ---------- */

.side {
  background: var(--side);
  border-right: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 0;
  gap: 10px;
  overflow-y: auto;
  scrollbar-width: none;
}

.group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--line);
}
.group:last-child { border-bottom: 0; }
.group.bottom { margin-top: auto; }

.side button {
  all: unset;
  width: 40px;
  height: 40px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  cursor: pointer;
  color: var(--muted);
  transition: background .12s, color .12s;
}
.side button:hover { background: var(--hover); color: var(--fg); }
.side button:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
.side button.on { background: var(--active); color: var(--fg); }

.side svg {
  width: 22px;
  height: 22px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.side button.accent { color: #fff; background: linear-gradient(135deg, var(--accent), var(--accent-2)); }
.side button.accent:hover { filter: brightness(1.08); }

#btn-mode .ic-desktop { display: none; }
body.desktop #btn-mode .ic-mobile { display: none; }
body.desktop #btn-mode .ic-desktop { display: block; }

/* ---------- palco ---------- */

.stage {
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: stretch;
  padding: 14px 16px;
  background:
    radial-gradient(1200px 500px at 50% -10%, #1c1f29 0%, transparent 60%),
    var(--bg);
}

.device {
  position: relative;
  height: 100%;
  border-radius: var(--radius);
  overflow: hidden;
  background: #000;
  box-shadow: 0 0 0 1px #2b2e38, 0 18px 50px rgba(0, 0, 0, .55);
  flex: none;
}

body.desktop .stage { padding: 0; }
body.desktop .device { border-radius: 0; box-shadow: none; width: 100% !important; flex: 1; }

.device iframe {
  position: absolute;
  top: 0;
  left: 0;
  border: 0;
  transform-origin: 0 0;
  background: #fff;
}

.loading {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: #000;
  z-index: 2;
  transition: opacity .25s;
}
.loading.done { opacity: 0; pointer-events: none; }

.spinner {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 3px solid #333;
  border-top-color: var(--accent);
  animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.blocked {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  text-align: center;
  padding: 24px;
  background: rgba(14, 15, 19, .94);
  z-index: 5;
}
.blocked[hidden] { display: none; }
.b-title { font-size: 17px; font-weight: 650; margin: 0 0 6px; }
.b-text { color: var(--muted); max-width: 320px; margin: 0 auto 16px; }
.b-actions { display: flex; gap: 8px; justify-content: center; }
.b-actions button, .panel .link {
  font: inherit;
  cursor: pointer;
}
.b-actions button {
  border: 0;
  border-radius: 10px;
  padding: 9px 14px;
  background: var(--accent);
  color: #fff;
  font-weight: 600;
}
.b-actions button.ghost { background: var(--hover); color: var(--fg); }

/* ---------- painel de configurações ---------- */

.panel {
  position: fixed;
  left: 64px;
  bottom: 12px;
  width: 290px;
  max-width: calc(100vw - 80px);
  background: #1a1c23;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 14px 16px 12px;
  box-shadow: 0 14px 40px rgba(0, 0, 0, .5);
  z-index: 10;
}
.panel[hidden] { display: none; }
.panel h2 { font-size: 14px; margin: 0 0 10px; }

.row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 0;
  cursor: pointer;
}
.row input { width: 16px; height: 16px; accent-color: var(--accent); margin: 0; }
.row.zoom { justify-content: space-between; cursor: default; }

.zctl { display: flex; align-items: center; gap: 4px; }
.zctl button {
  width: 28px; height: 28px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--hover);
  color: var(--fg);
  font-size: 16px;
  cursor: pointer;
}
.zctl output { min-width: 46px; text-align: center; font-variant-numeric: tabular-nums; }

.hint { color: var(--muted); font-size: 12px; margin: 8px 0 6px; }

.panel .link {
  border: 0;
  background: none;
  color: var(--accent-2);
  padding: 0;
  font-size: 12px;
  text-decoration: underline;
}

/* ---------- toast ---------- */

.toast {
  position: fixed;
  left: 50%;
  bottom: 22px;
  transform: translateX(-50%);
  background: #23262f;
  color: var(--fg);
  border: 1px solid var(--line);
  padding: 9px 14px;
  border-radius: 10px;
  font-size: 13px;
  z-index: 20;
  max-width: calc(100vw - 100px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, .4);
}
.toast[hidden] { display: none; }

/* ---------- painel de crescimento ---------- */

.panel.auto { width: 330px; max-height: calc(100vh - 24px); overflow-y: auto; }
.panel.auto h2 { display: flex; justify-content: space-between; align-items: center; }
.panel .x { all: unset; cursor: pointer; font-size: 20px; line-height: 1; padding: 0 4px; color: var(--muted); }
.panel .x:hover { color: var(--fg); }
.warn {
  margin: 0 0 10px; padding: 8px 10px; font-size: 12px; border-radius: 8px;
  background: rgba(240, 87, 107, .12); color: #ffb3bd; border: 1px solid rgba(240, 87, 107, .35);
}
.field { display: grid; gap: 4px; font-size: 12px; color: var(--muted); margin: 8px 0; }
.field input {
  font: inherit; color: var(--fg); background: var(--hover);
  border: 1px solid var(--line); border-radius: 8px; padding: 6px 8px;
}
.abtns { display: grid; gap: 6px; margin: 12px 0 8px; }
.abtns button {
  font: inherit; cursor: pointer; border: 0; border-radius: 9px; padding: 9px 10px;
  background: var(--accent); color: #fff; font-weight: 600; text-align: left;
}
.abtns button.ghost { background: var(--hover); color: var(--fg); text-align: center; }
.abtns button:disabled { opacity: .45; cursor: not-allowed; }
.dlg {
  position: fixed; inset: 0; z-index: 30; display: grid; place-items: center;
  background: rgba(0, 0, 0, .55);
}
.dlg[hidden] { display: none; }
.dlg-box {
  width: min(560px, calc(100vw - 32px)); max-height: calc(100vh - 32px);
  background: #1a1c23; border: 1px solid var(--line); border-radius: 14px; padding: 14px 16px;
  box-shadow: 0 14px 40px rgba(0, 0, 0, .5);
}
.dlg-box h2 { font-size: 15px; margin: 0 0 6px; }
.dlg-box textarea {
  width: 100%; height: min(320px, 50vh); resize: none; box-sizing: border-box;
  font: 12px/1.4 ui-monospace, Consolas, monospace; color: var(--fg);
  background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 8px;
}
.abtns.row2 { grid-template-columns: 1fr 1fr; }

/* ---------- editor de story ---------- */

.ed { position: fixed; inset: 0; z-index: 25; background: var(--bg); display: flex; flex-direction: column; }
.ed[hidden] { display: none; }
.ed-stage { flex: none; height: 54vh; display: grid; place-items: center; background: #000; overflow: hidden; }
.ed-stage canvas {
  height: min(calc(54vh - 16px), calc((100vw - 16px) * 16 / 9));
  width: auto; border-radius: 12px; touch-action: none; background: #000; cursor: grab;
}
.ed-tools { flex: 1; overflow-y: auto; padding: 10px 14px 18px; min-height: 0; }
.ed-tools h2 { font-size: 15px; margin: 0 0 4px; }
@media (min-width: 900px) {
  .ed { flex-direction: row; }
  .ed-stage { flex: 1; height: auto; }
  .ed-stage canvas { height: calc(100vh - 20px); }
  .ed-tools { flex: none; width: 340px; border-left: 1px solid var(--line); }
}
.ed-sec { display: grid; gap: 6px; margin: 12px 0; font-size: 12px; color: var(--muted); }
.ed-sec b { color: var(--fg); font-size: 13px; }
.ed-sec label { display: grid; gap: 4px; }
.ed-sec label.chk { display: flex; align-items: center; gap: 6px; }
.ed-tools input[type=text], .ed-tools select {
  font: inherit; color: var(--fg); background: var(--hover);
  border: 1px solid var(--line); border-radius: 8px; padding: 6px 8px; width: 100%;
}
.ed-tools input[type=color] { width: 38px; height: 30px; padding: 0; border: 0; background: none; cursor: pointer; }
.ed-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 6px 0; }
.ed-row input[type=range] { flex: 1; min-width: 80px; }
.ed-tools button {
  font: inherit; font-size: 12px; cursor: pointer; border: 1px solid var(--line); border-radius: 8px;
  padding: 6px 10px; background: var(--hover); color: var(--fg);
}
.ed-tools button:hover { background: var(--active); }
.ed-tools button.on { background: var(--accent); border-color: var(--accent); color: #fff; }
.ed-tools .abtns button { border: 0; padding: 9px 10px; font-size: 14px; background: var(--accent); color: #fff; font-weight: 600; text-align: center; }
.ed-tools .abtns button.ghost { background: var(--hover); color: var(--fg); }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chips.emo button { font-size: 20px; padding: 2px 6px; line-height: 1.3; }

/* ---------- bandeja de adesivos ---------- */

.ed-tools button.big { width: 100%; padding: 10px; font-size: 14px; font-weight: 700; margin: 8px 0 2px; background: var(--accent); border-color: var(--accent); color: #fff; }
.tray { position: fixed; inset: 0; z-index: 28; display: flex; align-items: flex-end; background: rgba(0, 0, 0, .5); }
.tray[hidden] { display: none; }
.tray-sheet {
  width: 100%; max-height: 82vh; overflow-y: auto; background: #1b1c22; border-radius: 22px 22px 0 0;
  padding: 8px 14px 18px; box-shadow: 0 -10px 40px rgba(0, 0, 0, .5);
}
.tray-grip { width: 42px; height: 5px; border-radius: 3px; background: #555a68; margin: 4px auto 10px; }
.tray-sheet input[type=search] {
  width: 100%; box-sizing: border-box; font: inherit; color: var(--fg); background: #2a2c35;
  border: 0; border-radius: 10px; padding: 9px 12px;
}
.tray-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px 8px; padding: 14px 0 6px; }
.tile {
  all: unset; cursor: pointer; display: grid; place-items: center; min-height: 74px; position: relative;
  text-align: center; border-radius: 12px;
}
.tile:hover { background: rgba(255, 255, 255, .06); }
.tile:focus-visible { outline: 2px solid var(--accent); }
.tile .chip {
  display: inline-block; padding: 8px 12px; border-radius: 12px; font-weight: 800; font-size: 12px;
  letter-spacing: .2px; background: #fff; color: #111; box-shadow: 0 3px 10px rgba(0, 0, 0, .35);
}
.tile .fake {
  position: absolute; top: 0; right: 2px; font-size: 9px; font-weight: 700; color: #ffd27a;
  background: rgba(0, 0, 0, .55); border-radius: 6px; padding: 1px 5px;
}
.t-loc .chip { color: #8134af; } .t-mention .chip { color: #f58529; }
.t-suavez .chip { background: #e1306c; color: #fff; }
.t-gif .chip { background: #6b6e78; color: #fff; }
.t-musica .chip { color: #e0245e; } .t-enquete .chip { color: #2b2f3a; }
.t-slider .chip { padding: 8px 10px; display: flex; align-items: center; gap: 6px; }
.t-slider .chip i { display: block; width: 46px; height: 8px; border-radius: 4px; background: linear-gradient(90deg, #ff4d6d, #ffd166); }
.t-link .chip { color: #1d9bf0; } .t-hash .chip { color: #3897f0; }
.t-perg .chip { background: linear-gradient(135deg, #833ab4, #fd1d1d); color: #fff; }
.t-count .chip { background: linear-gradient(135deg, #5851db, #c13584); color: #fff; font-size: 10px; }
#ask-fields label { display: grid; gap: 4px; margin: 8px 0; font-size: 12px; color: var(--muted); }
#ask-fields input { font: inherit; color: var(--fg); background: var(--hover); border: 1px solid var(--line); border-radius: 8px; padding: 7px 9px; }

/* ---------- janela de ferramentas ---------- */

.info { padding: 18px 16px; overflow-y: auto; }
.info h1 { font-size: 18px; margin: 0 0 10px; }
.conn { display: flex; align-items: center; gap: 8px; margin: 0 0 4px; font-weight: 600; }
.dot { width: 9px; height: 9px; border-radius: 50%; background: #c9a227; flex: none; }
.conn.ok .dot { background: #3ecf8e; }
.conn.bad .dot { background: var(--accent); }
.tips { margin: 14px 0 0; }
.tips p { margin: 8px 0; font-size: 12.5px; color: var(--muted); }
.tips b { color: var(--fg); }
.info .b-actions { flex-direction: column; align-items: stretch; margin-top: 16px; }
.pbar { height: 5px; border-radius: 5px; background: var(--hover); overflow: hidden; }
.pbar span { display: block; height: 100%; width: 0; background: linear-gradient(90deg, var(--accent), var(--accent-2)); transition: width .3s; }
'''

# ===== app.html =====
FILES['app.html'] = r'''<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>IG Desk</title>
  <link rel="stylesheet" href="app.css">
</head>
<body>
  <nav class="side" aria-label="Ferramentas">
    <div class="group">
      <button data-cmd="back" title="Voltar"><svg viewBox="0 0 24 24"><path d="M15 6l-6 6 6 6"/></svg></button>
      <button data-cmd="forward" title="Avançar"><svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg></button>
      <button data-cmd="reload" title="Recarregar"><svg viewBox="0 0 24 24"><path d="M20 12a8 8 0 1 1-2.3-5.6"/><path d="M20 4v5h-5"/></svg></button>
    </div>

    <div class="group">
      <button data-go="/" title="Início"><svg viewBox="0 0 24 24"><path d="M4 11l8-7 8 7v9h-5v-6H9v6H4z"/></svg></button>
      <button data-go="/explore/" title="Explorar"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M15 9l-2 4-4 2 2-4z"/></svg></button>
      <button data-go="/reels/" title="Reels"><svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="4"/><path d="M4 9h16M9 4l2 5M14 4l2 5"/><path d="M10.5 12.5v4l3.5-2z"/></svg></button>
      <button data-go="/direct/inbox/" title="Mensagens"><svg viewBox="0 0 24 24"><path d="M21 4L10 14"/><path d="M21 4l-7 17-4-7-7-4z"/></svg></button>
      <button data-cmd="create" class="accent" title="Nova publicação: post ou reel (modo computador)"><svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="5"/><path d="M12 8v8M8 12h8"/></svg></button>
      <button data-cmd="story" class="accent" title="Criar story (modo celular)"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8" stroke-dasharray="3 2.4"/><path d="M12 9v6M9 12h6"/></svg></button>
      <button data-cmd="profile" title="Meu perfil"><svg viewBox="0 0 24 24"><circle cx="12" cy="9" r="4"/><path d="M5 20c1.5-3.5 4-5 7-5s5.5 1.5 7 5"/></svg></button>
    </div>

    <div class="group bottom">
      <button id="btn-auto" title="Crescimento: seguir / deixar de seguir"><svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.2"/><path d="M3 19c.8-3 3.1-4.6 6-4.6"/><path d="M15 12l3 3 3-3M18 15V9"/></svg></button>
      <button id="btn-mode" title="Alternar modo celular / computador">
        <svg class="ic-mobile" viewBox="0 0 24 24"><rect x="7" y="3" width="10" height="18" rx="2"/><path d="M11 18h2"/></svg>
        <svg class="ic-desktop" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M9 20h6M12 16v4"/></svg>
      </button>
      <button id="btn-dark" title="Dark mode"><svg viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg></button>
      <button id="btn-tab" title="Abrir esta página numa aba do Chrome"><svg viewBox="0 0 24 24"><path d="M14 4h6v6"/><path d="M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg></button>
      <button id="btn-settings" title="Configurações"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/></svg></button>
    </div>
  </nav>

  <main class="info" id="info">
    <h1>IG Desk</h1>
    <p class="conn" id="conn"><span class="dot"></span><span id="conn-text">Conectando ao Instagram…</span></p>
    <p class="hint" id="conn-url"></p>
    <p class="hint" id="ver"></p>

    <div class="tips">
      <p><b>+</b> escolhe uma foto ou vídeo do computador e abre a nova publicação.</p>
      <p><b>Story</b> (ou o botão rosa abaixo): escolha a foto e abre o <b>editor com efeitos e Adesivos</b>; ao concluir, vai ao story do Instagram. Se você escolher a foto pelo próprio Instagram, use o botão <b>✨ Efeitos e adesivos</b> que aparece no canto da tela dele.</p>
      <p><b>Pessoa com seta</b> abre o Crescimento: seguir e deixar de seguir.</p>
      <p><b>Celular / computador</b> troca o layout da janela do Instagram.</p>
    </div>

    <div class="b-actions">
      <button id="b-story">✨ Criar story com efeitos e adesivos</button>
      <button id="b-reload" class="ghost">Recarregar o Instagram</button>
      <button id="b-focus" class="ghost">Ir para a janela do Instagram</button>
    </div>
  </main>

  <section class="panel" id="panel" hidden>
    <h2>Configurações</h2>
    <label class="row"><input type="checkbox" id="opt-videoControls"><span>Barra de controles nos vídeos</span></label>
    <label class="row"><input type="checkbox" id="opt-rememberVolume"><span>Lembrar o volume</span></label>
    <div class="row zoom">
      <span>Zoom</span>
      <div class="zctl">
        <button id="z-out" aria-label="Diminuir zoom">−</button>
        <output id="z-val">100%</output>
        <button id="z-in" aria-label="Aumentar zoom">+</button>
      </div>
    </div>
    <p class="hint">Modo celular mostra o Instagram como no celular (necessário para story). Modo computador mostra o site normal.</p>
    <button class="link" id="btn-shortcut">Atalho de teclado: Alt+Shift+I (alterar)</button><br>
    <button class="link" id="btn-diag">Copiar diagnóstico da tela (para suporte)</button>
  </section>

  <section class="panel auto" id="autopanel" hidden>
    <h2>Crescimento <button class="x" id="auto-close" aria-label="Fechar">×</button></h2>
    <p class="warn">Automatizar seguir/deixar de seguir vai contra os termos do Instagram e pode limitar ou bloquear a conta. Use limites baixos, não todos os dias, e não recarregue nem feche as janelas durante a execução.</p>
    <label class="field">Máximo de ações nesta execução (limite diário: 150)
      <input type="number" id="auto-limit" min="1" max="150" value="40"></label>
    <label class="field">Pausa entre ações, em segundos (mín. 20)
      <input type="number" id="auto-delay" min="20" max="120" value="30"></label>
    <label class="row"><input type="checkbox" id="auto-verified" checked><span>Ignorar contas verificadas</span></label>
    <label class="field">Seguir novos a partir dos seguidores de @ (opcional)
      <input type="text" id="auto-source" placeholder="usuario (vazio = sugestões do Instagram)" autocomplete="off"></label>
    <div class="abtns">
      <button data-auto="unfollow">Deixar de seguir quem não me segue</button>
      <button data-auto="followback">Seguir de volta quem me segue</button>
      <button data-auto="followNew">Seguir pessoas novas</button>
      <button id="auto-stop" class="ghost" disabled>Parar</button>
    </div>
    <div class="pbar"><span id="auto-bar"></span></div>
    <p class="hint" id="auto-status">Parado.</p>
  </section>

  <div class="ed" id="ed" hidden>
    <div class="ed-stage"><canvas id="ed-canvas" width="1080" height="1920"></canvas></div>
    <aside class="ed-tools">
      <h2>Editor de story</h2>
      <p class="hint">Efeitos, texto, emojis e adesivos ficam gravados na imagem. O story web só aceita foto: não há música, vídeo nem adesivo clicável.</p>

      <button id="ed-open-tray" class="big">☺ Adesivos</button>

      <div class="ed-sec"><b>Efeito</b><div class="chips" id="ed-filters"></div></div>

      <div class="ed-sec"><b>Ajustes</b>
        <label>Brilho <input type="range" id="ed-bright" min="60" max="140" value="100"></label>
        <label>Enquadrar
          <select id="ed-fit">
            <option value="contain">Imagem inteira (fundo desfocado)</option>
            <option value="cover">Preencher a tela</option>
          </select>
        </label>
      </div>

      <div class="ed-sec"><b>Texto</b>
        <input type="text" id="ed-text" placeholder="Digite o texto…" maxlength="120" autocomplete="off">
        <div class="ed-row">
          <input type="color" id="ed-color" value="#ffffff" aria-label="Cor do texto">
          <label class="chk"><input type="checkbox" id="ed-bg" checked> Fundo</label>
          <button id="ed-add">Adicionar</button>
        </div>
        <div class="ed-row">
          <button data-ins="#">#hashtag</button>
          <button data-ins="@">@menção</button>
          <button data-ins="📍 ">📍 local</button>
        </div>
        <label>Tamanho do item selecionado <input type="range" id="ed-size" min="20" max="260" value="90"></label>
        <button id="ed-del" class="ghost">Apagar item selecionado</button>
      </div>

      <div class="ed-sec"><b>Emojis</b><div class="chips emo" id="ed-emojis"></div></div>

      <div class="ed-sec"><b>Figurinha (imagem ou GIF)</b>
        <button id="ed-sticker">Adicionar do computador</button>
        <span class="hint">GIF entra como imagem parada (o primeiro quadro). O story é uma imagem.</span>
      </div>

      <div class="ed-sec"><b>Desenhar</b>
        <div class="ed-row">
          <button id="ed-pen">Lápis: desligado</button>
          <input type="color" id="ed-pcolor" value="#ff3b5c" aria-label="Cor do lápis">
          <input type="range" id="ed-psize" min="4" max="44" value="14" aria-label="Espessura">
        </div>
      </div>

      <div class="ed-row"><button id="ed-undo" class="ghost">Desfazer</button><button id="ed-raw" class="ghost">Enviar original</button></div>
      <div class="abtns">
        <button id="ed-post">Postar no story</button>
        <button id="ed-cancel" class="ghost">Cancelar</button>
      </div>
    </aside>
  </div>

  <div class="tray" id="tray" hidden>
    <div class="tray-sheet" role="dialog" aria-label="Adesivos">
      <div class="tray-grip"></div>
      <input type="search" id="tray-q" placeholder="Pesquisar" autocomplete="off">
      <p class="hint">Os adesivos ficam gravados na imagem. Os marcados <b>só visual</b> aparecem como no app, mas <b>não funcionam</b> (ninguém vota, responde ou toca): o Instagram só libera isso no app.</p>
      <div class="tray-grid" id="tray-grid"></div>
    </div>
  </div>

  <div class="dlg" id="ask" hidden>
    <div class="dlg-box" role="dialog" aria-label="Adesivo">
      <h2 id="ask-title"></h2>
      <div id="ask-fields"></div>
      <div class="abtns row2">
        <button id="ask-ok">Adicionar</button>
        <button id="ask-cancel" class="ghost">Cancelar</button>
      </div>
    </div>
  </div>

  <input type="file" id="pick" accept="image/*,video/*" hidden>
  <input type="file" id="ed-sticker-file" accept="image/*" hidden>

  <div class="dlg" id="dlg" hidden>
    <div class="dlg-box" role="dialog" aria-label="Diagnóstico">
      <h2>Diagnóstico da tela</h2>
      <p class="hint" id="dlg-hint"></p>
      <textarea id="dlg-text" readonly spellcheck="false"></textarea>
      <div class="abtns row2">
        <button id="dlg-copy">Copiar</button>
        <button id="dlg-close" class="ghost">Fechar</button>
      </div>
    </div>
  </div>
  <div class="toast" id="toast" role="status" hidden></div>

  <script src="app.js"></script>
</body>
</html>
'''

# ===== app.js =====
FILES['app.js'] = r'''// IG Desk — janela de ferramentas
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
'''

# ===== background.js =====
FILES['background.js'] = r'''// IG Desk — service worker
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
'''

# ===== content/frame.js =====
FILES['content/frame.js'] = r'''// IG Desk — script da página do Instagram na janela do IG Desk.
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
'''

# ===== content/mobile.js =====
FILES['content/mobile.js'] = r'''// IG Desk — roda no contexto da própria página do Instagram (world: MAIN),
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
'''

# ===== manifest.json =====
FILES['manifest.json'] = r'''{
  "manifest_version": 3,
  "name": "IG Desk",
  "version": "1.4.4",
  "description": "Instagram em janela própria, em modo celular: poste stories e reels pelo PC, com editor de story, dark mode e controles de vídeo.",
  "minimum_chrome_version": "111",
  "icons": {
    "16": "icons/icon16.png",
    "32": "icons/icon32.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "action": {
    "default_title": "Abrir IG Desk",
    "default_icon": {
      "16": "icons/icon16.png",
      "32": "icons/icon32.png"
    }
  },
  "background": {
    "service_worker": "background.js"
  },
  "permissions": ["declarativeNetRequest", "storage", "scripting", "tabs"],
  "host_permissions": ["https://*.instagram.com/*"],
  "content_scripts": [
    {
      "matches": ["https://*.instagram.com/*"],
      "js": ["content/mobile.js"],
      "run_at": "document_start",
      "all_frames": false,
      "world": "MAIN"
    },
    {
      "matches": ["https://*.instagram.com/*"],
      "js": ["content/frame.js"],
      "run_at": "document_start",
      "all_frames": false
    }
  ],
  "commands": {
    "_execute_action": {
      "suggested_key": { "default": "Alt+Shift+I" },
      "description": "Abrir IG Desk"
    }
  }
}
'''

# ---------------------------------------------------------------------------
# Ícones (PNG em base64)
# ---------------------------------------------------------------------------
ICONS = {
    'icons/icon128.png': (
        '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'
    ),
    'icons/icon16.png': (
        'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAACaUlEQVR4nG2TzYvWVRTHP99zfr+ZZp4ZFy1CUhh9hlGonaQ0uXDS'
        'EHsBEdtWFG2CfNvYQmiVtMiFC3eF9A+Iq6KVgaH4AhW0a3CgRYEULfJ5n+ee0+J5mSm8lwuXy/l++d7PPVcAS82Dp8z8chIrgLu7'
        'MpPtQxJRSiYUYesR5dJvGw9vas/yoZNmfkPgE1Gr1cZMgKYGJYKFhXmEkERCiSintby8+sjMmpFRTPJ+f8DHZz7g6KuHiQgAzI0f'
        'bt/n6tUvqWdqMrOYzCNiozJZkyQrc+90erzw4j7efedtPrn4GRkJEhHBF1c+5datO/z04y80Gg2PiDRZszIJQCYjM1lsNPj9j8d8'
        '9+33+ExNApvdHmfPfcjiQoNMMGkEBaiEjSBhGEZGMlvXzO9Y5NmZOQQ8rts8M1OTkRiGsCmdarKdHLuMQQS7fJavDuyhcuP9u7/S'
        'j8D/I9fEwMYGkykGmeyt59i/NAsulh/OMcjcVmPT16nGV0ESJpGIBXMe9Fp8fvtPXMadbosL5tO6yXpqAo2jOcbXf/1NjumMIj8l'
        'wRYDthmI2hw6fUhhdYW03WKLgWmKZSSuzCmbQ1r/dHjtxBrH3zpK+0mXzcGQynxctaWZ9EFKkrvT6/bZ+fxzrB1bZWnvbsyMtWOr'
        '7Nq9k163j7tP+iAB6eD+1x+ZvBlZimS+ORjw0fn3eOXIS7SetMmExR0NHtz9mWtXrlPV1biV3SPLhg7te+Okmd2QzCMKAO1Wh6qq'
        'MB/BihIMh0PmG/NIYOZkRomI0wJ4eeXNU+bV5chcEenmpoz/fWcTUSITFZPWowwv3Vv/5ua/19XsfXeLqskAAAAASUVORK5CYII='
    ),
    'icons/icon32.png': (
        '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'
    ),
    'icons/icon48.png': (
        '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'
        'Zvwb9JzxAAAAAElFTkSuQmCC'
    ),
}


def gerar(destino: Path) -> None:
    if destino.exists():
        shutil.rmtree(destino)
    for rel, conteudo in FILES.items():
        arq = destino / rel
        arq.parent.mkdir(parents=True, exist_ok=True)
        # write_bytes: `newline=` em write_text só existe no Python 3.10+
        arq.write_bytes(conteudo.encode("utf-8"))
    for rel, b64 in ICONS.items():
        arq = destino / rel
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_bytes(base64.b64decode(b64))


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
    total = len(FILES) + len(ICONS)
    print(f"OK: {total} arquivos gerados em {destino}")
    print(f"ZIP: {zip_path}")
    print()
    print("Para instalar no Chrome:")
    print("  1. Abra chrome://extensions")
    print("  2. Ligue 'Modo do desenvolvedor'")
    print(f"  3. 'Carregar sem compactação' -> {destino}")
    print("  4. Clique no ícone do IG Desk (ou Alt+Shift+I)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
