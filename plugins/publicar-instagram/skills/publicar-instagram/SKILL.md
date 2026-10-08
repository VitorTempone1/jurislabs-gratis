---
name: publicar-instagram
description: Publica no Instagram pela API oficial da Meta, direto do Claude Code. Foto, carrossel (2 a 10) e Reels, com legenda. Também conecta a conta pela primeira vez, guiando passo a passo até o token. Use quando o usuário disser "publica no Instagram", "posta isso no meu Instagram", "sobe esse carrossel", "publica esse reels", "conecta meu Instagram", "configura o Instagram", "meu token venceu" ou "/publicar-instagram".
---

# Publicar no Instagram

Script: `${CLAUDE_PLUGIN_ROOT}/skills/publicar-instagram/scripts/ig.py` (só Python 3.9+, nada a
instalar). Se esse caminho não existir, o script está em `scripts/ig.py`, na mesma pasta deste
arquivo. Abaixo, `IG` quer dizer `python3 "<esse caminho>"`.

## 1. Antes de tudo: a conta está conectada?

Rode `IG conferir`.

- Mostrou `Conectado: @fulano`: pule para a parte 3.
- Deu erro de credencial: siga a parte 2. Não peça o token antes de a pessoa ter um.

## 2. Primeira vez: conectar a conta

Abra `GUIA-TOKEN.md` (ao lado deste arquivo) e conduza a pessoa **um passo por vez**,
esperando ela dizer que fez. Se ela mandar print, leia a tela e diga o próximo clique pelo
nome exato do botão. Os dois tropeços mais comuns estão no guia: "função de desenvolvedor
insuficiente" (falta aceitar o convite de testador) e Página sem Instagram ligado.

Com o token na mão, ofereça os dois jeitos de entregar e deixe a pessoa escolher:

1. **Mais seguro:** ela abre o app Terminal e cola `python3 "<caminho do ig.py>" configurar`.
   O token é colado lá e não aparece na tela nem nesta conversa.
2. **Mais fácil:** ela cola o token aqui e você roda
   `IG_TOKEN_NOVO='<token>' IG configurar`. Avise antes, numa frase, que o token fica no
   histórico desta conversa.

O `configurar` descobre sozinho o id da conta e o @, e grava tudo em
`~/.config/publicar-instagram/.env` (só o dono lê). Caminho B do guia (token de Página): se
a pessoa tiver o ID e a Chave Secreta do app, acrescente `--app-id` e `--app-secret`, que o
script troca pelo token longo sozinho. Mais de uma Página: ele lista e pede `--pagina NOME`.

Termine com `IG conferir` e mostre o @ e os seguidores, para ela ver que ligou.

## 3. Publicar

Sempre nesta ordem:

1. **Mostre o que vai sair**: o @ da conta, os arquivos na ordem e a legenda inteira.
   Rode o comando com `--seco` (não toca na rede) e **peça um "sim"**. Publicação não tem
   desfazer pela API: apagar, só pelo app.
2. Com o "sim", rode o mesmo comando sem `--seco`.
3. Devolva o link que o script imprime em `PUBLICADO:`.

```bash
IG foto foto.jpg --legenda "texto"
IG carrossel 1.jpg 2.jpg 3.jpg --legenda "texto"        # 2 a 10, pode misturar .mp4
IG reel video.mp4 --legenda "texto" --capa capa.jpg     # --so-reels: fora do feed
IG foto foto.jpg --legenda-arquivo legenda.txt          # legenda longa ou com aspas
```

Regras que o script já confere, para você explicar quando barrar:

- **Foto só em JPEG.** PNG ou outro formato: converta antes. No Mac,
  `sips -s format jpeg foto.png --out foto.jpg`.
- Legenda até 2.200 caracteres; carrossel de 2 a 10 itens; vídeo `.mp4` ou `.mov`.
- **A API não recebe arquivo, ela baixa de um link público.** Arquivo do computador sobe
  antes para um endereço temporário público (litterbox.catbox.moe, apaga sozinho em 1 hora).
  Diga isso à pessoa antes da primeira vez. Se o conteúdo for sigiloso, peça um link próprio
  (Google Drive não serve: o link dele abre uma página, não o arquivo).

## 4. Quando der erro

O script nunca falha calado: imprime `ERRO:` com a mensagem da própria Meta. Leia para a
pessoa em português simples e diga o conserto:

- código **190**: token vencido ou revogado. Volte à parte 2 (ou `IG renovar`, abaixo).
- código **10** ou **200 a 299**: falta permissão no token. Guia, passo das permissões.
- mensagem dizendo que a mídia não pôde ser baixada (*fetched*): o link não é público ou não
  aponta direto para o arquivo.
- container em **ERROR**: a Meta não aceitou o vídeo ou a foto (formato, tamanho, proporção
  fora de 4:5 a 1,91:1). Diga o que veio no erro.

## 5. Manutenção

- Token do caminho A (começa com `IG`) vale 60 dias. `IG renovar` estende por mais 60
  (precisa ter mais de 24 h e ainda não ter vencido).
- Token de Página (caminho B) não vence sozinho; para se a senha do Facebook mudar.

## O que a API não faz (diga sem rodeio se pedirem)

- **Agendar:** a API publica na hora, não tem agendamento. Para agendar, use o Meta Business
  Suite ou o app do Instagram.
- Stories, música do catálogo e marcar produto: fora desta skill.
- Limite da Meta: publicações por API numa janela de 24 h (a documentação fala em 50 num
  trecho e 100 noutro). Estourou, o erro da Meta diz.

---
Feito por JurisLabs · @vitortempone
