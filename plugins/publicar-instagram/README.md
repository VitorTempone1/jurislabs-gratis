# Publicar no Instagram pelo Claude Code

**Instalar (cole no Terminal, uma linha):**

```
claude plugin marketplace add VitorTempone1/jurislabs-gratis && claude plugin install publicar-instagram@jurislabs-gratis
```

Ou, dentro do Claude Code, uma linha de cada vez:

```
/plugin marketplace add VitorTempone1/jurislabs-gratis
/plugin install publicar-instagram@jurislabs-gratis
```

Depois feche e abra o Claude Code.

## O que ela faz

Você pede em português e o Claude publica no seu Instagram pela API oficial da Meta:

- **foto** única;
- **carrossel** de 2 a 10 fotos ou vídeos;
- **Reels**, com capa e a opção de aparecer ou não no feed.

Antes de publicar ele mostra a conta, os arquivos e a legenda, e só sai com o seu "sim".
Se a Meta recusar, você lê a mensagem dela, traduzida, com o que fazer. Nada falha calado.

## Como usar, em 3 passos

1. **Instale** com a linha acima.
2. **Conecte a conta:** diga *"configura meu Instagram"*. O Claude te leva pelo guia do
   token, um passo de cada vez, e descobre sozinho o id da sua conta. Feito uma vez só.
3. **Publique:** *"publica estas 5 imagens como carrossel com a legenda tal"*.

## O que você precisa

- Instagram **profissional** (Criador ou Empresa; trocar é grátis).
- Conta em developers.facebook.com (grátis).
- Python 3.9 ou mais novo (Mac e Linux já vêm com ele). Nada mais para instalar.

O guia completo do token, com os dois caminhos (com e sem Página do Facebook) e os erros
comuns, está em [`skills/publicar-instagram/GUIA-TOKEN.md`](skills/publicar-instagram/GUIA-TOKEN.md).

## Seu token fica com você

A chave mora no seu computador, em `~/.config/publicar-instagram/.env`, legível só pelo seu
usuário (ou nas variáveis `IG_ACCESS_TOKEN` e `IG_USER_ID`, se preferir). Ela nunca vai
para dentro da skill nem para nós.

## Bom saber

- **A API não agenda post.** Publica na hora. Para agendar: Meta Business Suite.
- **Foto só em JPEG.** O Claude converte se você mandar PNG.
- **A Meta baixa a mídia de um link público.** Arquivo do seu computador sobe antes para um
  endereço temporário (litterbox.catbox.moe) que se apaga em 1 hora. Conteúdo sigiloso:
  use um link seu.

## Conferir sem publicar

```
python3 skills/publicar-instagram/scripts/test_ig.py     # autoteste, sem internet
python3 skills/publicar-instagram/scripts/ig.py carrossel a.jpg b.jpg --seco
```

---

Feito pela **JurisLabs** · [@vitortempone](https://www.instagram.com/vitortempone) no Instagram.
Gratuito. Licença Apache 2.0.
