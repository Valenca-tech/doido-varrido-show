"""Atualiza dados/videos.json com os vídeos do canal do YouTube (títulos, views, data aproximada).

Uso: python ferramentas/atualizar_videos.py

Lê a aba Vídeos do canal pela mesma API que a página do YouTube usa (não precisa de chave).
Se o YouTube mudar e a leitura falhar, o script avisa e o dados/videos.json fica como estava.
Shorts não entram: a aba Vídeos só traz os vídeos longos.
Ajustes manuais (esconder vídeo, trocar título ou gênero) ficam em dados/videos_ajustes.json,
no formato {"<id do vídeo>": {"titulo": "...", "familia": "...", "oculto": true}}.
"""
import json
import re
import sys
import unicodedata
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQ = RAIZ / "dados" / "videos.json"
AJUSTES = RAIZ / "dados" / "videos_ajustes.json"
HANDLE = "@odoidovarridooficial"
CABECALHO = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Cookie": "SOCS=CAI; CONSENT=YES+",
}

# gênero como escrito no título -> família usada no filtro do site
GENEROS = {
    "forro": "Forró", "forro comico": "Forró", "electro forro swing": "Forró", "xote": "Forró",
    "forro embolado": "Embolada", "embolada": "Embolada",
    "forro vaquejada": "Vaquejada", "forro e vaquejada": "Vaquejada",
    "pisadinha": "Pisadinha", "cordel": "Cordel", "piadas do dia": "Piadas do Dia",
    "brega": "Românticas", "arrocha": "Românticas", "sertanejo": "Românticas",
    "sertanejo classico": "Românticas", "country": "Românticas", "sofrencia": "Românticas",
}
MINUSCULAS = {"a", "o", "as", "os", "e", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
              "com", "pra", "pro", "que", "um", "uma", "por", "se"}


def baixar(url, dados=None):
    extra = {"Content-Type": "application/json"} if dados else {}
    req = urllib.request.Request(url, data=dados, headers={**CABECALHO, **extra})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def sem_acento(t):
    t = unicodedata.normalize("NFKD", unicodedata.normalize("NFKC", t)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t.lower()).strip()


def numero(txt):
    """'216 mil' -> 216000, '1,1 mil' -> 1100, '1.308.664' -> 1308664."""
    m = re.search(r"([\d.,]+)\s*(mil|mi)?", txt or "")
    if not m:
        return 0
    if m.group(2):
        n = float(m.group(1).replace(".", "").replace(",", "."))
        return round(n * (1000 if m.group(2) == "mil" else 1_000_000))
    return int(m.group(1).replace(".", "").replace(",", ""))


def data_relativa(txt, hoje):
    """'há 9 meses' -> data aproximada (a lista do YouTube só mostra a data relativa)."""
    m = re.search(r"(\d+)\s*(seg|min|hora|dia|sem|mes|ano)", sem_acento(txt or ""))
    if not m:
        return None
    n, u = int(m.group(1)), m.group(2)
    dias = {"dia": n, "sem": 7 * n, "mes": 30.44 * n, "ano": 365.25 * n}.get(u, 0)
    return (hoje - timedelta(days=round(dias))).isoformat()


def caixa(t):
    """Título todo em maiúsculas vira caixa de título ('A BET LEVOU FOI TUDO!' -> 'A Bet Levou Foi Tudo!')."""
    letras = [c for c in t if c.isalpha()]
    if not letras or sum(c.isupper() for c in letras) / len(letras) < 0.8:
        return t
    palavras = t.lower().split(" ")
    return " ".join(p if i and p in MINUSCULAS else p[:1].upper() + p[1:] for i, p in enumerate(palavras))


def classificar(titulo):
    """Separa gênero e título de exibição: 'Forró — Quem Nunca? | Silfarnney Valença' -> ('Forró', 'Forró', 'Quem Nunca?')."""
    t = unicodedata.normalize("NFKC", titulo)
    t = re.sub(r"[\U0001F000-\U0001FAFF☀-➿️]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    partes = [p.strip() for p in t.split("|")]
    t, resto = partes[0], partes[1:]
    genero, nome = None, t
    m = re.match(r"^(.{3,80}?)\s+[—–-]\s+(.+)$", t)
    if m and sem_acento(m.group(1)) in GENEROS:
        genero, nome = m.group(1), m.group(2)
    elif m and sem_acento(m.group(2)) in GENEROS:
        genero, nome = m.group(2), m.group(1)
    else:
        for g in sorted(GENEROS, key=len, reverse=True):
            if sem_acento(t).startswith(g + " "):
                genero = t[: len(g)]
                break
        genero = genero or next((r for r in resto if sem_acento(r) in GENEROS), None)
    if genero and sem_acento(genero) == "piadas do dia":
        vol = re.search(r"VOL[:.]?\s*(\d+)", t, re.I)
        nome = f"Piadas do Dia, vol. {vol.group(1)}" if vol else t
    # rabicho de SEO depois de travessão ou hífen: corta quando é comprido
    m = re.match(r"^(.{4,60}?)\s+[—–-]\s+(.{25,})$", nome)
    if m:
        nome = m.group(1)
    if len(nome) > 2 and nome[0] in "\"“" and nome[-1] in "\"”":
        nome = nome[1:-1]
    nome = caixa(nome.strip())
    familia = GENEROS.get(sem_acento(genero), "Outros") if genero else "Outros"
    return familia, caixa(genero or ""), nome


def chave(nome):
    return re.sub(r"[^a-z0-9]", "", sem_acento(nome))


def varredura(hoje):
    html = baixar(f"https://www.youtube.com/{HANDLE}/videos?hl=pt&gl=BR")
    inicial = json.loads(re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S).group(1))
    versao = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', html).group(1)
    inscritos = re.search(r'"([\d.,]+\s*(?:mil|mi)?)\s*inscritos"', html)
    canal = {"inscritos": numero(inscritos.group(1).replace("\xa0", " ")) if inscritos else 0}
    try:
        sobre = baixar(f"https://www.youtube.com/{HANDLE}/about?hl=pt&gl=BR")
        # a página Sobre traz o total do canal junto com as views de cada vídeo: o total é o maior
        canal["visualizacoes"] = max(numero(n) for n in re.findall(r'"([\d.]+) visualizações"', sobre))
    except Exception:
        pass

    itens = []

    def ler(lista):
        prox = None
        for it in lista:
            c = it.get("richItemRenderer", {}).get("content", {})
            v = c.get("videoRenderer")
            if v:
                itens.append({"id": v["videoId"], "titulo_original": "".join(r["text"] for r in v["title"]["runs"]),
                              "views": numero(v.get("viewCountText", {}).get("simpleText", "")),
                              "publicado": data_relativa(v.get("publishedTimeText", {}).get("simpleText", ""), hoje),
                              "duracao": v.get("lengthText", {}).get("simpleText", "")})
            lk = c.get("lockupViewModel")
            if lk:
                meta = lk["metadata"]["lockupMetadataViewModel"]
                textos = re.findall(r'"content":\s*"([^"]+)"', json.dumps(meta.get("metadata", {}), ensure_ascii=False))
                dur = re.findall(r'"(\d{1,2}:\d{2}(?::\d{2})?)"', json.dumps(lk.get("contentImage", {})))
                itens.append({"id": lk["contentId"], "titulo_original": meta["title"]["content"],
                              "views": numero(textos[0] if textos else ""),
                              "publicado": data_relativa(textos[1] if len(textos) > 1 else "", hoje),
                              "duracao": dur[0] if dur else ""})
            tk = it.get("continuationItemRenderer", {}).get("continuationEndpoint", {}).get("continuationCommand", {}).get("token")
            if tk:
                prox = tk
        return prox

    aba = next(t["tabRenderer"] for t in inicial["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]
               if t.get("tabRenderer", {}).get("content", {}).get("richGridRenderer"))
    token = ler(aba["content"]["richGridRenderer"]["contents"])
    while token:
        corpo = json.dumps({"context": {"client": {"clientName": "WEB", "clientVersion": versao, "hl": "pt", "gl": "BR"}},
                            "continuation": token}).encode()
        r = json.loads(baixar("https://www.youtube.com/youtubei/v1/browse?prettyPrint=false", corpo))
        acoes = r.get("onResponseReceivedActions", [{}])
        token = ler(acoes[0].get("appendContinuationItemsAction", {}).get("continuationItems", []))
    return canal, itens


def main():
    hoje = date.today()
    base = json.loads(ARQ.read_text(encoding="utf-8")) if ARQ.exists() else {"canal": {}, "videos": []}
    ajustes = json.loads(AJUSTES.read_text(encoding="utf-8")) if AJUSTES.exists() else {}
    por_id = {v["id"]: v for v in base["videos"]}
    try:
        canal, itens = varredura(hoje)
    except Exception as e:
        sys.exit(f"Não consegui ler o canal ({e}); dados/videos.json não foi alterado.")
    if len(itens) < 0.8 * len(por_id):
        sys.exit(f"A leitura trouxe só {len(itens)} vídeos (o arquivo tem {len(por_id)}); nada foi alterado.")
    # visualização só cresce: se o total cair pela metade, a página veio diferente (outro idioma, "216K" lido como 216)
    antes = sum(v.get("views", 0) for v in por_id.values())
    agora = sum(it["views"] for it in itens)
    if antes and agora < 0.5 * antes:
        sys.exit(f"Total de visualizações caiu de {antes} para {agora}: leitura suspeita, nada foi alterado.")
    base["canal"].update({k: v for k, v in canal.items() if v})
    for it in itens:
        atual = por_id.setdefault(it["id"], {"id": it["id"]})
        if atual.get("publicado") and it["publicado"]:
            it["publicado"] = min(atual["publicado"], it["publicado"])  # a data relativa só arredonda para baixo
        atual.update(it)

    videos = []
    for v in por_id.values():
        familia, genero, nome = classificar(v["titulo_original"])
        v.update(familia=familia, genero=genero, titulo=nome, oculto=False)
        v.update(ajustes.get(v["id"], {}))
        videos.append(v)

    # relançamentos: a mesma música (mesmo título e família) em mais de um vídeo; fica visível o de mais views
    grupos = {}
    for v in videos:
        grupos.setdefault((v["familia"], chave(v["titulo"])), []).append(v)
    for g in grupos.values():
        g.sort(key=lambda v: -v.get("views", 0))
        for i, v in enumerate(g):
            v["repetido"] = i > 0

    videos.sort(key=lambda v: v.get("publicado") or "", reverse=True)
    base["videos"] = videos
    base["atualizado_em"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="minutes")
    ARQ.parent.mkdir(parents=True, exist_ok=True)
    ARQ.write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")
    vis = [v for v in videos if not v["oculto"] and not v["repetido"]]
    print(f"{len(videos)} vídeos no arquivo, {len(vis)} visíveis; canal: {base['canal']}")


if __name__ == "__main__":
    main()
