# Extensões do Instagram (IG Desk e IG Seguidores)

Duas extensões do Chrome (Manifest V3) para usar o Instagram no computador.

| Pasta | O que é |
|---|---|
| [ig-desk](ig-desk/) | Instagram numa **janela própria** (visual de celular ou de computador) e uma **janela de ferramentas** ao lado: editor de story, seguir/deixar de seguir e controles de vídeo. Inspirada na Inssist. |
| [ig-seguidores](ig-seguidores/) | Painel para ver quem você segue e quem te segue, com ações em lote **limitadas e confirmadas**. Tudo roda no seu navegador, com o seu login. |

`gerar_ig_desk.py` e `gerar_ig_seguidores.py` recriam as pastas das extensões (e os `.zip`) a partir de um único arquivo.

## Instalar
1. Abra `chrome://extensions` e ligue o **Modo do desenvolvedor**.
2. Clique em **Carregar sem compactação** e escolha a pasta `ig-desk` ou `ig-seguidores`.

Cada pasta tem um README próprio com os detalhes.

> Uso pessoal. Ações automáticas em excesso podem ser limitadas pelo Instagram, por isso as ações em lote têm limite.
