#!/usr/bin/env python3
"""Publica no Instagram pela API oficial da Meta (Content Publishing). Só biblioteca padrão.

Uso:
  ig.py configurar [--app-id ID --app-secret SEGREDO] [--pagina NOME]   (token vem pelo teclado)
  ig.py conferir
  ig.py renovar                          (só token de Login do Instagram, o que começa com IG)
  ig.py foto ARQ_OU_URL --legenda "..."
  ig.py carrossel A B C ... --legenda "..."   (2 a 10 itens; foto .jpg ou vídeo .mp4/.mov)
  ig.py reel VIDEO --legenda "..." [--capa IMG] [--so-reels]
  Qualquer publicação aceita --seco: mostra as chamadas e não toca na rede.
  Legenda longa: --legenda-arquivo legenda.txt

Credenciais (nesta ordem): variáveis de ambiente IG_ACCESS_TOKEN e IG_USER_ID; arquivo .env
da pasta atual; ~/.config/publicar-instagram/.env (o `configurar` grava aqui, com chmod 600).

A API não aceita arquivo: ela BAIXA a mídia de uma URL pública. Arquivo local sobe antes
para o litterbox.catbox.moe (público, apaga sozinho em 1 h). Não use para nada sigiloso.
A API também não agenda: publica na hora.
"""
import argparse
import getpass
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

VERSAO = "v25.0"
HOST_FB = "graph.facebook.com"     # token de Página (Login do Facebook)
HOST_IG = "graph.instagram.com"    # token do Login do Instagram (começa com IG)
UA = "publicar-instagram/1.0 (+https://github.com/VitorTempone1/jurislabs-gratis)"
HOSPEDAGEM = "https://litterbox.catbox.moe/resources/internals/api.php"
ENV_USUARIO = os.path.expanduser("~/.config/publicar-instagram/.env")
VIDEO = (".mp4", ".mov")
FOTO = (".jpg", ".jpeg")
PASSO_S, TETO_S = 10, 600          # espera o container ficar pronto (reel pode levar minutos)
dormir = time.sleep


class Erro(Exception):
    pass


def redigir(s):
    return re.sub(r"((?:access_token|client_secret|fb_exchange_token)=)[^&\s\"']+", r"\1***", str(s))


def abrir(req, timeout=120):
    """Único ponto de rede. Devolve (status, texto). O teste troca esta função."""
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as e:
        raise Erro(f"sem conexão com {urllib.parse.urlsplit(req.full_url).hostname}: {e}")


def host_do(token):
    return HOST_IG if token.startswith("IG") else HOST_FB


def graph(host, token, metodo, caminho, versao=VERSAO, **campos):
    campos = {k: v for k, v in campos.items() if v is not None}
    if token:
        campos["access_token"] = token
    url = f"https://{host}/{versao + '/' if versao else ''}{caminho}"
    dados = None
    if metodo == "GET":
        url += "?" + urllib.parse.urlencode(campos)
    else:
        dados = urllib.parse.urlencode(campos).encode()
    st, txt = abrir(urllib.request.Request(url, data=dados, method=metodo,
                                           headers={"User-Agent": UA}))
    try:
        js = json.loads(txt or "{}")
    except ValueError:
        js = {"error": {"message": txt[:300]}}
    if st >= 400 or (isinstance(js, dict) and js.get("error")):
        e = js.get("error") or {}
        cod, sub = e.get("code"), e.get("error_subcode")
        msg = " | ".join(x for x in (e.get("message"), e.get("error_user_title"),
                                     e.get("error_user_msg")) if x) or txt[:300]
        dica = ""
        if cod == 190:
            dica = "\n  -> Token vencido ou inválido. Gere outro e rode `configurar` de novo."
        elif cod in (3, 10) or (isinstance(cod, int) and 200 <= cod <= 299):
            dica = "\n  -> Falta permissão no token. Veja GUIA-TOKEN.md, passo das permissões."
        raise Erro(redigir(f"a Meta recusou {metodo} /{caminho} (HTTP {st}, código {cod}"
                           f"{'/' + str(sub) if sub else ''}): {msg}{dica}"))
    return js


# ------------------------------------------------------------------ credenciais

def le_env(caminho):
    if not os.path.isfile(caminho):
        return {}
    out = {}
    for linha in open(caminho, encoding="utf-8"):
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            k, v = linha.split("=", 1)
            out[k.strip().removeprefix("export ").strip()] = v.strip().strip("'\"")
    return out


def credenciais():
    for fonte in (os.environ, le_env(".env"), le_env(ENV_USUARIO)):
        if fonte.get("IG_ACCESS_TOKEN") and fonte.get("IG_USER_ID"):
            t = fonte["IG_ACCESS_TOKEN"]
            return {"host": host_do(t), "token": t, "ig": fonte["IG_USER_ID"]}
    raise Erro("não achei IG_ACCESS_TOKEN e IG_USER_ID (nem no ambiente, nem em ./.env, "
               f"nem em {ENV_USUARIO}). Rode `ig.py configurar` primeiro.")


def grava_env(token, ig, usuario):
    os.makedirs(os.path.dirname(ENV_USUARIO), exist_ok=True)
    fd = os.open(ENV_USUARIO, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(f"# publicar-instagram (@{usuario})\nIG_ACCESS_TOKEN={token}\n"
                f"IG_USER_ID={ig}\nIG_USERNAME={usuario}\n")
    os.chmod(ENV_USUARIO, 0o600)


def descobre_conta(token, app_id=None, app_secret=None, pagina=None):
    """Do token colado ao (token final, id do Instagram, @). Acha o id sozinho."""
    if token.startswith("IG"):
        me = graph(HOST_IG, token, "GET", "me", fields="user_id,username")
        return token, str(me["user_id"]), me.get("username")
    if app_id and app_secret:
        token = graph(HOST_FB, None, "GET", "oauth/access_token", grant_type="fb_exchange_token",
                      client_id=app_id, client_secret=app_secret,
                      fb_exchange_token=token)["access_token"]
    pags = graph(HOST_FB, token, "GET", "me/accounts", limit=100,
                 fields="name,access_token,instagram_business_account{id,username}").get("data") or []
    ok = [p for p in pags if p.get("instagram_business_account")]
    if pagina:
        ok = [p for p in ok if pagina.lower() in (p.get("name") or "").lower()]
    if not ok:
        vistas = ", ".join(p.get("name", "?") for p in pags) or "nenhuma"
        raise Erro(f"nenhuma Página com Instagram profissional ligado (páginas que o token vê: "
                   f"{vistas}). Confira no GUIA-TOKEN.md: permissão pages_show_list, a Página "
                   "marcada na hora de gerar o token e o Instagram ligado à Página.")
    if len(ok) > 1:
        raise Erro("mais de uma Página com Instagram. Escolha com --pagina: " +
                   ", ".join(f"{p['name']} (@{p['instagram_business_account'].get('username')})"
                             for p in ok))
    ig = ok[0]["instagram_business_account"]
    return ok[0]["access_token"], str(ig["id"]), ig.get("username")


# ------------------------------------------------------------------ mídia

def eh_url(x):
    return x.startswith(("https://", "http://"))


def hospedar(caminho):
    """Sobe o arquivo para um host público temporário (1 h) e devolve a URL."""
    b = "----publicar" + uuid.uuid4().hex
    corpo = b"".join(
        f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
        for k, v in (("reqtype", "fileupload"), ("time", "1h")))
    with open(caminho, "rb") as f:
        corpo += (f'--{b}\r\nContent-Disposition: form-data; name="fileToUpload"; '
                  f'filename="{os.path.basename(caminho)}"\r\nContent-Type: '
                  f'application/octet-stream\r\n\r\n').encode() + f.read() + f"\r\n--{b}--\r\n".encode()
    st, txt = abrir(urllib.request.Request(HOSPEDAGEM, data=corpo, method="POST", headers={
        "User-Agent": UA, "Content-Type": f"multipart/form-data; boundary={b}"}), timeout=600)
    txt = txt.strip()
    if st >= 400 or not txt.startswith("https://"):
        raise Erro(f"não consegui subir {caminho} para a hospedagem temporária "
                   f"(HTTP {st}): {txt[:200]}. Passe uma URL pública no lugar do arquivo.")
    return txt


def confere_arquivo(x, aceitos):
    ext = os.path.splitext(urllib.parse.urlsplit(x).path if eh_url(x) else x)[1].lower()
    if not eh_url(x) and not os.path.isfile(x):
        raise Erro(f"arquivo não encontrado: {x}")
    if ext and ext not in aceitos:
        dica = (" A Meta só aceita foto em JPEG. No Mac: sips -s format jpeg foto.png --out foto.jpg"
                if aceitos == FOTO else "")
        raise Erro(f"{x}: formato {ext} não serve aqui (aceito: {', '.join(aceitos)}).{dica}")


def url_publica(x, seco):
    if eh_url(x):
        return x
    return f"<sobe {os.path.basename(x)} para URL temporária>" if seco else hospedar(x)


def montar(tipo, urls, legenda, capa=None, so_reels=False):
    """(filhos, pai): os campos de cada POST /{ig}/media, na ordem."""
    if tipo == "foto":
        return [], {"image_url": urls[0], "caption": legenda}
    if tipo == "reel":
        pai = {"media_type": "REELS", "video_url": urls[0], "caption": legenda,
               "share_to_feed": "false" if so_reels else "true"}
        if capa:
            pai["cover_url"] = capa
        return [], pai
    filhos = [({"media_type": "VIDEO", "video_url": u} if u.lower().split("?")[0].endswith(VIDEO)
               else {"image_url": u}) | {"is_carousel_item": "true"} for u in urls]
    return filhos, {"media_type": "CAROUSEL", "caption": legenda}


def espera(cfg, cid):
    limite = time.monotonic() + TETO_S
    while True:
        r = graph(cfg["host"], cfg["token"], "GET", cid, fields="status_code,status")
        code = r.get("status_code")
        if code in ("FINISHED", "PUBLISHED"):
            return
        if code in ("ERROR", "EXPIRED"):
            raise Erro(f"a Meta não aceitou a mídia (container {cid}, {code}): {r.get('status')}")
        if time.monotonic() >= limite:
            raise Erro(f"container {cid} ainda {code} depois de {TETO_S}s. Nada foi publicado.")
        dormir(PASSO_S)


def publicar(cfg, filhos, pai):
    host, tok, ig = cfg["host"], cfg["token"], cfg["ig"]
    if filhos:
        ids = []
        for f in filhos:
            ids.append(graph(host, tok, "POST", f"{ig}/media", **f)["id"])
            espera(cfg, ids[-1])
        pai = pai | {"children": ",".join(ids)}
    cid = graph(host, tok, "POST", f"{ig}/media", **pai)["id"]
    espera(cfg, cid)
    mid = graph(host, tok, "POST", f"{ig}/media_publish", creation_id=cid)["id"]
    link = graph(host, tok, "GET", mid, fields="permalink").get("permalink")
    return mid, link


# ------------------------------------------------------------------ comandos

def cmd_configurar(a):
    token = os.environ.get("IG_TOKEN_NOVO")
    if not token:
        try:
            token = getpass.getpass("Cole o token da Meta (não aparece na tela) e dê Enter: ")
        except (EOFError, OSError):
            raise Erro("aqui não tem teclado para colar o token. Rode este mesmo comando no app "
                       "Terminal, ou passe o token em IG_TOKEN_NOVO=... antes do comando.")
    token = token.strip()
    if not token:
        raise Erro("token vazio.")
    tok, ig, usuario = descobre_conta(token, a.app_id, a.app_secret, a.pagina)
    grava_env(tok, ig, usuario)
    print(f"OK: conta @{usuario} (id {ig}). Credenciais gravadas em {ENV_USUARIO} (só você lê).")
    if host_do(tok) == HOST_IG:
        print("Token do Login do Instagram: vale 60 dias. Rode `ig.py renovar` antes de vencer.")
    elif not (a.app_id and a.app_secret):
        print("Atenção: se o token colado era o curto (1 h), o de Página também vence logo. "
              "Estenda no Depurador de Token (GUIA-TOKEN.md, passo 6) e rode de novo.")


def cmd_conferir(_a):
    c = credenciais()
    campos = "username,followers_count,media_count"
    r = graph(c["host"], c["token"], "GET", c["ig"], fields=campos)
    print(f"Conectado: @{r.get('username')} · {r.get('followers_count')} seguidores · "
          f"{r.get('media_count')} posts · via {c['host']}")


def cmd_renovar(_a):
    c = credenciais()
    if c["host"] != HOST_IG:
        raise Erro("token de Página do Facebook não precisa renovar (não vence enquanto a "
                   "senha e o acesso do app não mudarem). Se parar, rode `configurar`.")
    r = graph(HOST_IG, c["token"], "GET", "refresh_access_token", versao=None,
              grant_type="ig_refresh_token")
    grava_env(r["access_token"], c["ig"], le_env(ENV_USUARIO).get("IG_USERNAME", "?"))
    print(f"Token renovado: vale mais {int(r.get('expires_in', 0)) // 86400} dias.")


def cmd_publicar(a):
    legenda = open(a.legenda_arquivo, encoding="utf-8").read().strip() if a.legenda_arquivo \
        else (a.legenda or "")
    if len(legenda) > 2200:
        raise Erro(f"legenda com {len(legenda)} caracteres; o Instagram aceita até 2.200.")
    itens = a.midia
    if a.tipo == "carrossel" and not 2 <= len(itens) <= 10:
        raise Erro(f"carrossel precisa de 2 a 10 itens; vieram {len(itens)}.")
    for x in itens:
        confere_arquivo(x, FOTO if a.tipo == "foto" else VIDEO if a.tipo == "reel" else FOTO + VIDEO)
    if getattr(a, "capa", None):
        confere_arquivo(a.capa, FOTO)
    cfg = {"host": "?", "token": "", "ig": "{IG_USER_ID}"} if a.seco else credenciais()
    urls = [url_publica(x, a.seco) for x in itens]
    capa = url_publica(a.capa, a.seco) if getattr(a, "capa", None) else None
    filhos, pai = montar(a.tipo, urls, legenda, capa, getattr(a, "so_reels", False))
    if a.seco:
        print("SECO: nada sai daqui. Estas seriam as chamadas:")
        for f in filhos:
            print(f"  POST /{cfg['ig']}/media {json.dumps(f, ensure_ascii=False)}  (espera FINISHED)")
        if filhos:
            pai = pai | {"children": "<ids dos itens acima>"}
        print(f"  POST /{cfg['ig']}/media {json.dumps(pai, ensure_ascii=False)}  (espera FINISHED)")
        print(f"  POST /{cfg['ig']}/media_publish {{\"creation_id\": \"<id acima>\"}}")
        return
    mid, link = publicar(cfg, filhos, pai)
    print(f"PUBLICADO: {link or '(sem link; id ' + mid + ')'}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="ig.py", description="Publica no Instagram pela API da Meta.")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("configurar", help="cola o token, acha a conta e grava o .env")
    c.add_argument("--app-id")
    c.add_argument("--app-secret")
    c.add_argument("--pagina", help="parte do nome da Página, se houver mais de uma")
    sub.add_parser("conferir", help="mostra a conta conectada")
    sub.add_parser("renovar", help="renova o token do Login do Instagram (+60 dias)")
    for tipo, n in (("foto", None), ("carrossel", "+"), ("reel", None)):
        s = sub.add_parser(tipo)
        s.add_argument("midia", nargs=n or 1)
        s.add_argument("--legenda")
        s.add_argument("--legenda-arquivo")
        s.add_argument("--seco", action="store_true", help="só mostra as chamadas")
        if tipo == "reel":
            s.add_argument("--capa", help="imagem .jpg de capa (arquivo ou URL)")
            s.add_argument("--so-reels", action="store_true", help="não aparece no feed")
        s.set_defaults(tipo=tipo)
    a = p.parse_args(argv)
    try:
        {"configurar": cmd_configurar, "conferir": cmd_conferir,
         "renovar": cmd_renovar}.get(a.cmd, cmd_publicar)(a)
    except Erro as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
