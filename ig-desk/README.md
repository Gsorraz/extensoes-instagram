# IG Desk — extensão do Chrome

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
