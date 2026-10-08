#!/usr/bin/env python3
"""Autoteste sem rede: confere a montagem de cada chamada à API da Meta.

  python3 test_ig.py      -> "OK: N verificações" ou o assert que quebrou
"""
import io
import json
import os
import sys
import tempfile
import urllib.parse
from contextlib import redirect_stderr, redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ig  # noqa: E402

N = 0


def ok(cond, msg):
    global N
    assert cond, msg
    N += 1


class Falsa:
    """Troca ig.abrir: grava cada pedido e responde pela ordem da fila."""

    def __init__(self, respostas):
        self.respostas, self.pedidos = list(respostas), []

    def __call__(self, req, timeout=120):
        u = urllib.parse.urlsplit(req.full_url)
        campos = dict(urllib.parse.parse_qsl(u.query or (req.data or b"").decode()))
        self.pedidos.append({"metodo": req.get_method(), "host": u.hostname, "path": u.path,
                             "campos": campos, "ua": req.get_header("User-agent")})
        st, corpo = self.respostas.pop(0)
        return st, json.dumps(corpo) if not isinstance(corpo, str) else corpo


def roda(argv, respostas, env=None):
    falsa = Falsa(respostas)
    ig.abrir, ig.dormir = falsa, (lambda s: None)
    antigo = dict(os.environ)
    os.environ.update(env or {})
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            cod = ig.main(argv)
    finally:
        os.environ.clear()
        os.environ.update(antigo)
    return cod, out.getvalue(), err.getvalue(), falsa.pedidos


FB = {"IG_ACCESS_TOKEN": "tokenDePaginaFalso123", "IG_USER_ID": "1784"}
IGL = {"IG_ACCESS_TOKEN": "IGtokenFalso456", "IG_USER_ID": "999"}
PRONTO = (200, {"status_code": "FINISHED"})


def teste_montar():
    f, p = ig.montar("foto", ["https://x/a.jpg"], "oi")
    ok(f == [] and p == {"image_url": "https://x/a.jpg", "caption": "oi"}, "foto")
    f, p = ig.montar("reel", ["https://x/v.mp4"], "oi", capa="https://x/c.jpg", so_reels=True)
    ok(p == {"media_type": "REELS", "video_url": "https://x/v.mp4", "caption": "oi",
             "share_to_feed": "false", "cover_url": "https://x/c.jpg"}, f"reel {p}")
    f, p = ig.montar("carrossel", ["https://x/a.jpg", "https://x/b.MP4?x=1"], "oi")
    ok(f[0] == {"image_url": "https://x/a.jpg", "is_carousel_item": "true"}, "item foto")
    ok(f[1] == {"media_type": "VIDEO", "video_url": "https://x/b.MP4?x=1",
                "is_carousel_item": "true"}, f"item video {f[1]}")
    ok(p == {"media_type": "CAROUSEL", "caption": "oi"} and "caption" not in f[0], "pai carrossel")


def teste_carrossel_fb():
    cod, out, err, ped = roda(
        ["carrossel", "https://x/a.jpg", "https://x/b.jpg", "--legenda", "Olá #teste"],
        [(200, {"id": "c1"}), PRONTO, (200, {"id": "c2"}), PRONTO, (200, {"id": "pai"}), PRONTO,
         (200, {"id": "m1"}), (200, {"permalink": "https://www.instagram.com/p/X/"})], FB)
    ok(cod == 0 and "PUBLICADO: https://www.instagram.com/p/X/" in out, f"saída {cod} {out} {err}")
    ok(all(p["host"] == "graph.facebook.com" for p in ped), "host FB")
    ok(all(p["ua"] == ig.UA for p in ped), "User-Agent explícito em toda chamada")
    ok(all(p["path"].startswith("/v25.0/") for p in ped), "versão na URL")
    ok(all(p["campos"].get("access_token") == FB["IG_ACCESS_TOKEN"] for p in ped), "token vai junto")
    pai = ped[4]
    ok(pai["metodo"] == "POST" and pai["path"] == "/v25.0/1784/media", "pai no /media")
    ok(pai["campos"]["children"] == "c1,c2" and pai["campos"]["media_type"] == "CAROUSEL", "children")
    ok(pai["campos"]["caption"] == "Olá #teste", "legenda chega inteira")
    ok(ped[6]["path"] == "/v25.0/1784/media_publish" and ped[6]["campos"]["creation_id"] == "pai",
       "media_publish com o container")


def teste_reel_host_ig():
    cod, out, err, ped = roda(
        ["reel", "https://x/v.mp4", "--legenda", "r"],
        [(200, {"id": "c"}), (200, {"status_code": "IN_PROGRESS"}), PRONTO,
         (200, {"id": "m"}), (200, {"permalink": "https://i/p/R/"})], IGL)
    ok(cod == 0, f"reel {err}")
    ok(all(p["host"] == "graph.instagram.com" for p in ped), "token IG vai pro graph.instagram.com")
    ok(ped[0]["campos"]["media_type"] == "REELS" and ped[0]["campos"]["share_to_feed"] == "true",
       "reel no feed por padrão")
    ok(sum(p["metodo"] == "GET" and p["campos"].get("fields") == "status_code,status"
           for p in ped) == 2, "esperou até FINISHED")


def teste_erro_da_meta_aparece():
    meta = {"error": {"message": "Invalid OAuth access token.", "code": 190, "error_subcode": 463}}
    cod, out, err, ped = roda(["foto", "https://x/a.jpg", "--legenda", "x"], [(400, meta)], FB)
    ok(cod == 1 and "Invalid OAuth access token." in err and "190/463" in err, f"erro calado: {err}")
    ok("configurar" in err, "dica do 190")
    ok(FB["IG_ACCESS_TOKEN"] not in err, "token não vaza no erro")
    meta = {"error": {"message": "Only photo or video can be accepted as media type.", "code": 9004,
                      "error_subcode": 2207052, "error_user_msg": "A mídia não pôde ser baixada"}}
    cod, out, err, _ = roda(["foto", "https://x/a.jpg"], [(400, meta)], FB)
    ok(cod == 1 and "A mídia não pôde ser baixada" in err and "2207052" in err, "user_msg aparece")
    cod, out, err, _ = roda(["reel", "https://x/v.mp4"],
                            [(200, {"id": "c"}), (200, {"status_code": "ERROR", "status": "codec"})], FB)
    ok(cod == 1 and "codec" in err and "ERROR" in err, "ERROR do container aparece")
    cod, out, err, _ = roda(["foto", "https://x/a.jpg"], [(200, "<html>bloqueado</html>")], FB)
    ok(cod == 1 and "bloqueado" in err, "resposta não-JSON vira erro legível")


def teste_validacoes_locais():
    cod, _, err, ped = roda(["carrossel", "https://x/a.jpg"], [], FB)
    ok(cod == 1 and "2 a 10" in err and not ped, "carrossel de 1 barrado sem rede")
    cod, _, err, ped = roda(["foto", "https://x/a.png"], [], FB)
    ok(cod == 1 and "JPEG" in err and not ped, "png barrado")
    cod, _, err, ped = roda(["foto", "https://x/a.jpg", "--legenda", "x" * 2201], [], FB)
    ok(cod == 1 and "2.200" in err and not ped, "legenda longa barrada")
    cod, _, err, ped = roda(["foto", "/nao/existe.jpg"], [], FB)
    ok(cod == 1 and "não encontrado" in err and not ped, "arquivo ausente")
    vazio = {"IG_ACCESS_TOKEN": "", "IG_USER_ID": ""}
    real = ig.ENV_USUARIO
    ig.ENV_USUARIO = "/nao/existe/.env"
    try:
        cod, _, err, ped = roda(["foto", "https://x/a.jpg"], [], vazio)
    finally:
        ig.ENV_USUARIO = real
    ok(cod == 1 and "configurar" in err and not ped, "sem credencial avisa")


def teste_seco_sem_rede():
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "a.jpg")
        open(a, "wb").write(b"\xff\xd8\xff")
        cod, out, err, ped = roda(["carrossel", a, "https://x/b.jpg", "--seco"], [], {})
    ok(cod == 0 and not ped, f"seco tocou a rede {ped} {err}")
    ok("is_carousel_item" in out and "media_publish" in out and "a.jpg" in out, "seco mostra o plano")


def teste_configurar():
    tmp = tempfile.mkdtemp()
    real = ig.ENV_USUARIO
    ig.ENV_USUARIO = os.path.join(tmp, "sub", ".env")
    try:
        paginas = {"data": [
            {"name": "Sem IG", "access_token": "x"},
            {"name": "Minha Página", "access_token": "tokenPaginaLonga",
             "instagram_business_account": {"id": "1784", "username": "fulano"}}]}
        cod, out, err, ped = roda(["configurar", "--app-id", "1", "--app-secret", "s"],
                                  [(200, {"access_token": "userLongo"}), (200, paginas)],
                                  {"IG_TOKEN_NOVO": "curtoFalso"})
        ok(cod == 0 and "@fulano" in out, f"configurar FB {err}")
        ok(ped[0]["path"] == "/v25.0/oauth/access_token" and
           ped[0]["campos"]["grant_type"] == "fb_exchange_token" and
           "access_token" not in ped[0]["campos"], "troca por token longo")
        ok(ped[1]["path"] == "/v25.0/me/accounts" and ped[1]["campos"]["access_token"] == "userLongo",
           "lista páginas com o token longo")
        env = ig.le_env(ig.ENV_USUARIO)
        ok(env == {"IG_ACCESS_TOKEN": "tokenPaginaLonga", "IG_USER_ID": "1784",
                   "IG_USERNAME": "fulano"}, f".env {env}")
        ok(oct(os.stat(ig.ENV_USUARIO).st_mode & 0o777) == "0o600", "env só do dono")

        cod, out, err, ped = roda(["configurar"], [(200, {"user_id": 555, "username": "ciclano"})],
                                  {"IG_TOKEN_NOVO": "IGfalso"})
        ok(cod == 0 and ped[0]["host"] == "graph.instagram.com" and ped[0]["path"] == "/v25.0/me",
           "configurar IG acha o id pelo /me")
        ok(ig.le_env(ig.ENV_USUARIO)["IG_USER_ID"] == "555", "id do IG gravado")

        cod, out, err, ped = roda(["renovar"], [(200, {"access_token": "IGnovo", "expires_in": 5184000})])
        ok(cod == 0 and ped[0]["path"] == "/refresh_access_token" and
           ped[0]["campos"]["grant_type"] == "ig_refresh_token", f"renovar {err}")
        ok(ig.le_env(ig.ENV_USUARIO)["IG_ACCESS_TOKEN"] == "IGnovo" and "60 dias" in out, "renovado")

        duas = {"data": [{"name": n, "access_token": "t", "instagram_business_account":
                          {"id": i, "username": n}} for n, i in (("a", "1"), ("b", "2"))]}
        cod, _, err, _ = roda(["configurar"], [(200, duas)], {"IG_TOKEN_NOVO": "x"})
        ok(cod == 1 and "--pagina" in err, "duas páginas pede escolha")
        cod, _, err, _ = roda(["configurar"], [(200, {"data": [{"name": "Loja"}]})],
                              {"IG_TOKEN_NOVO": "x"})
        ok(cod == 1 and "Loja" in err and "pages_show_list" in err, "sem IG explica")
    finally:
        ig.ENV_USUARIO = real


def teste_hospedar_multipart():
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "foto.jpg")
        open(a, "wb").write(b"JPEGDATA")
        visto = {}

        def falsa(req, timeout=0):
            visto.update(url=req.full_url, corpo=req.data, tipo=req.get_header("Content-type"),
                         ua=req.get_header("User-agent"))
            return 200, "https://litter.catbox.moe/abc.jpg\n"
        ig.abrir = falsa
        ok(ig.hospedar(a) == "https://litter.catbox.moe/abc.jpg", "url devolvida")
        ok(visto["ua"] == ig.UA and "boundary=" in visto["tipo"], "multipart com UA")
        ok(b'name="time"\r\n\r\n1h' in visto["corpo"] and b"JPEGDATA" in visto["corpo"], "corpo")
        ig.abrir = lambda req, timeout=0: (200, "erro qualquer")
        try:
            ig.hospedar(a)
            ok(False, "host ruim passou calado")
        except ig.Erro as e:
            ok("URL pública" in str(e), "host ruim avisa")


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("teste_"):
            f()
    print(f"OK: {N} verificações")
