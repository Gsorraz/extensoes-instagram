# IG Seguidores — extensão do Chrome

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

O limite do Instagram para este tipo de ação é baixo. Marque **Usar todo o limite do dia** para gastar os 200 de uma vez, ou
defina o máximo por execução. O que sobrar vai para a **Fila** (aparece no painel e fica guardada): amanhã, clique em
**Continuar fila**. Ela reconfere cada conta antes (por exemplo, ignora quem você já deixou de seguir nesse meio-tempo).

## Várias contas

Cada conta do Instagram guarda os seus próprios dados: listas, fila, protegidos, histórico de "já deixei de seguir" e o
contador do dia. O seletor de conta fica sempre no topo; o botão **+ Conta** abre a janelinha do Instagram para você entrar
em outra conta (depois, **Atualizar listas**). O painel segue a conta logada na janelinha do Instagram: ao clicar em **Atualizar listas**, ele passa para
ela (e aparece um seletor no topo quando há mais de uma conta). Seguir/deixar de seguir só roda se a conta da janelinha for
a mesma do painel; se for outra (ou mudar no meio), a ferramenta para sem fazer nada. Os dados de antes desta versão passam
para a conta a que pertenciam.

### Janela anônima (não mistura com o seu Instagram pessoal)

Por padrão a janelinha do Instagram abre em **modo anônimo**, que tem login separado do seu Chrome: o seu Instagram pessoal
continua como está e você entra na outra conta só nessa janelinha. Para isso, ative uma vez **Permitir em modo anônimo** em
`chrome://extensions` > IG Seguidores > Detalhes. Sem essa permissão a ferramenta avisa e não abre nada (ela não usa o login
normal sem você desmarcar a opção). O login anônimo some quando a janelinha é fechada, então o painel **guarda o login de cada conta** (cookies do instagram.com,
só neste navegador, na permissão `cookies`). Ao abrir o Instagram ele pergunta **qual conta** e já entra nela; **Trocar conta**
faz a mesma pergunta quando a janelinha já está aberta. Conta nova: escolha "Entrar em outra conta", faça login uma vez e pronto.
O botão "esquecer login" apaga o login guardado de uma conta. Quem tiver acesso a este perfil do Chrome tem acesso a esses logins:
não use em computador compartilhado. Se o Instagram encerrar a sessão, é só entrar de novo.

## Pausar, retomar e proteger contas

- **Pausar / Retomar:** vale a partir da próxima ação (a que já estava em andamento termina).
- **Descanso:** a cada 20 ações há uma pausa maior (1 a 2 min), além da pausa normal entre cada uma (mín. 10 s).
- **Protegidos (★):** na aba **Protegidos** dá para **exportar** a lista (JSON), **importar** de volta e **colar @usuários**
  de uma vez. Só entram contas que aparecem nas suas listas.

## Segurança

- Limite diário de **200** para seguir e **200** para deixar de seguir; pausa aleatória (mín. 10 s) entre ações.
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
