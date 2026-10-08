# Como pegar o token do Instagram (feito uma vez só)

O token é a "chave" que deixa o Claude publicar na sua conta. Ele sai do site de
desenvolvedores da Meta, de graça. Leva uns 15 minutos.

Os nomes dos botões mudam um pouco de tempos em tempos. Travou numa tela diferente? Tire um
print e mande pro Claude: ele lê a tela e diz o próximo clique.

## Antes de começar (vale para os dois caminhos)

1. **Sua conta do Instagram precisa ser profissional** (Criador de conteúdo ou Empresa). É
   grátis e você não perde seguidor. No app: seu perfil → menu (☰) → **Tipo de conta e
   ferramentas** → **Mudar para conta profissional**. Se já aparece "Conta profissional",
   está pronto.
2. Entre em **developers.facebook.com** com o seu Facebook e clique em **Começar** (ou *Get
   Started*) para virar desenvolvedor. É um cadastro rápido, pede confirmar e-mail ou celular.

## Qual caminho escolher

| | Caminho A (recomendado) | Caminho B |
|---|---|---|
| Precisa de Página do Facebook? | **Não** | Sim, ligada ao Instagram |
| Quanto tempo o token vale | 60 dias (renova com 1 comando) | Não vence |
| Passos | menos | mais |

Na dúvida, vá de **A**.

---

## Caminho A: Login do Instagram, sem Página

**A1. Crie o app.** Em developers.facebook.com → **Meus apps** → **Criar app**. Dê um nome
qualquer (ex.: "Publicador"). Quando perguntar o **caso de uso**, escolha **Gerenciar
mensagens e conteúdo no Instagram**. Se pedir portfólio empresarial, pode seguir sem
conectar. Termine em **Criar app** (ele pede sua senha do Facebook).

**A2. Abra a tela do token.** Dentro do app: **Casos de uso** → no do Instagram, clique em
**Personalizar** → **Configuração da API com login comercial do Instagram** (*API setup with
Instagram business login*). Procure a seção **Gerar tokens de acesso**.

**A3. Vire testador da sua própria conta** (é aqui que quase todo mundo trava). Se ao clicar
em **Adicionar conta** aparecer *"função de desenvolvedor insuficiente"*:

1. No menu do app: **Funções do app** → **Funções** → **Adicionar pessoas** → escolha
   **Testador do Instagram** e digite o seu @.
2. Abra o Instagram no **navegador** (não no celular): **instagram.com/accounts/manage_access**
   → aba **Convites de testador** → **Aceitar**.
3. Volte à tela do A2 e atualize a página.

**A4. Gere o token.** Em **Gerar tokens de acesso** → **Adicionar conta** → entre com o
Instagram → **Permitir** em tudo → clique em **Gerar token** ao lado da conta → marque que
está ciente → **Copiar**.

Esse token já é o de longa duração (60 dias). Ele começa com as letras `IG`. Pule para
**"Entregar o token ao Claude"**, lá embaixo.

---

## Caminho B: Página do Facebook (token que não vence)

**B1. Ligue o Instagram a uma Página.** No Facebook, abra a sua Página → **Configurações** →
**Contas vinculadas** → **Instagram** → **Conectar**. Não tem Página? Crie uma em
facebook.com/pages/create, leva 1 minuto.

**B2. Crie o app.** developers.facebook.com → **Meus apps** → **Criar app** → tipo
**Empresa** (*Business*), ou o caso de uso de Instagram com login do Facebook se ele
oferecer. Nome qualquer.

**B3. Gere o token no Explorador.** Abra **developers.facebook.com/tools/explorer**:

1. Em **App da Meta**, escolha o app que você criou.
2. Em **Usuário ou Página**, deixe **Token de acesso do usuário**.
3. Em **Permissões**, adicione as quatro (digite o nome e clique):
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
   - `pages_read_engagement`

   Se a sua Página está num portfólio empresarial (Business Manager), acrescente também
   `business_management`.
4. Clique em **Generate Access Token**. Na janela do Facebook, **marque a sua Página e a
   conta do Instagram** quando ele perguntar quais liberar. Esse é o passo que mais falha:
   sem a Página marcada, o Claude não acha a sua conta.

**B4. Deixe o token longo.** O token que sai do Explorador vale 1 hora. Dois jeitos de
estender, escolha um:

- **Sem mexer em chave:** clique no **ⓘ** ao lado do token → **Abrir na Ferramenta de token
  de acesso** → **Estender token de acesso** (*Extend Access Token*) → copie o token novo.
- **Pelo Claude:** pegue o **ID do app** e a **Chave Secreta do app** em
  **Configurações do app → Básico** e entregue junto com o token (o Claude roda o
  `configurar` com `--app-id` e `--app-secret` e faz a troca sozinho). A Chave Secreta é
  senha: não compartilhe com mais ninguém.

Com o token longo, o `configurar` pega o token da sua Página, que **não vence**.

**Não precisa de "Revisão do app" da Meta.** Você é o administrador do app e publica na sua
própria conta: o modo desenvolvimento basta.

---

## Entregar o token ao Claude

Volte ao Claude Code e diga **"configura meu Instagram"**. Ele oferece dois jeitos:

- **Mais seguro:** você abre o app **Terminal**, cola o comando que ele mostrar e cola o
  token quando pedir (ele não aparece na tela).
- **Mais fácil:** você cola o token direto no chat. Fica no histórico da conversa.

Ele descobre sozinho qual é a sua conta, grava a chave em
`~/.config/publicar-instagram/.env` (só você lê) e mostra o seu @ e o número de seguidores.
Apareceu o seu @? Pronto, está ligado. Peça: **"publica esta foto no meu Instagram com a
legenda tal"**.

## Problemas comuns

| O que aparece | O que fazer |
|---|---|
| "função de desenvolvedor insuficiente" | Passo A3: aceitar o convite de testador. |
| "nenhuma Página com Instagram profissional ligado" | B1 (ligar a Página) e B3 item 4 (marcar a Página ao gerar). |
| código 190 | Token vencido. Caminho A: peça "renova meu token do Instagram". Caminho B: gere de novo. |
| código 10 ou 200 | Faltou permissão. Refaça B3 com as quatro marcadas. |
| "só aceita foto em JPEG" | Peça ao Claude para converter a imagem para .jpg. |

## Limites da própria API (não é a skill)

- **Não agenda:** publica na hora. Para agendar, Meta Business Suite ou o app.
- Foto só em **JPEG**, proporção de 4:5 a 1,91:1, até 8 MB.
- Carrossel até **10** itens (o app deixa 20, a API não).
- A mídia precisa estar num **link público**. Arquivo do computador o Claude sobe sozinho
  para um endereço temporário que apaga em 1 hora.

Documentação oficial, se quiser conferir: developers.facebook.com/docs/instagram-platform

---
JurisLabs · @vitortempone
