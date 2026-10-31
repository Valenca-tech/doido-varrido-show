"""Gera o site estático em site/ a partir de dados/*.json.

Uso: python gerar.py
  dados/config.json      links, WhatsApp, PIX, serviços, letreiro e falas dos balões (editar à mão)
  dados/universo.json    vila, personagens, lendas (tirado da bíblia do Vilarejo Buraco Fundo)
  dados/videos.json      catálogo do canal (python ferramentas/atualizar_videos.py)
  dados/comentarios.json balões de avaliação: comentários reais do YouTube, escolhidos à mão
  dados/teste.json       perguntas do teste "Quem é você em Buraco Fundo?"
As imagens vêm de python ferramentas/preparar_imagens.py. CSS e JS ficam em site/css e site/js.
"""
import hashlib
import html
import json
import re
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import quote

RAIZ = Path(__file__).resolve().parent
DADOS = RAIZ / "dados"
SITE = RAIZ / "site"


def ler(nome):
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))


cfg, uni, cat = ler("config.json"), ler("universo.json"), ler("videos.json")
comentarios, teste = ler("comentarios.json"), ler("teste.json")

e = html.escape
MESES = "jan. fev. mar. abr. maio jun. jul. ago. set. out. nov. dez.".split()
FAMILIAS = ["Forró", "Embolada", "Vaquejada", "Cordel", "Pisadinha", "Piadas do Dia", "Românticas"]
GRUPOS = {
    "Família Valença": "A família do Doido",
    "Moradores de Buraco Fundo": "Moradores da vila",
    "Série cantada": "Cantadas de Buraco Fundo",
    "Folclore": "Lendas da estrada",
}
DESTAQUES = ["ze-pavio", "raimunda", "ze-tonhim-cafe-doce", "ze-encostado", "ze-fora-de-prumo", "ze-conversa",
             "coloral", "ze-coco", "ze-fiado", "ze-pega-ligeiro", "ze-corneteiro", "professora-marinalva"]
IMAGEM = {"cachorro-muxiba": "cachorro-ze-mochila"}  # id do personagem -> nome do retrato, quando difere
# nomes pelos quais os textos chamam cada morador, além do nome oficial (para ligar as páginas entre si)
APELIDOS = {
    "raimunda": ["Dona Raimunda"], "ze-promessa": ["Seu Lídio Promessa", "Seu Lídio"],
    "ze-conversa": ["Zé Nego Fábim", "Nego Fábim"], "ze-fora-de-prumo": ["Fora de Prumo"],
    "ze-tonhim-cafe-doce": ["Zé Tonhim"], "zezinho-da-mochila": ["Zézinho"], "professora-marinalva": ["Marinalva"],
    "lourinha-de-buraco-fundo": ["Lourinha"], "silfarnney-valenca": ["Doido Varrido Show"],
}
NOME_REDE = {"youtube": "YouTube", "instagram": "Instagram", "facebook": "Facebook", "tiktok": "TikTok", "kwai": "Kwai", "whatsapp": "WhatsApp"}

ICONE = {
    "play": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4.5v15l13-7.5z" fill="currentColor"/></svg>',
    "whats": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a9 9 0 0 0-7.7 13.6L3 21l4.5-1.2A9 9 0 1 0 12 3Z" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"/><path d="M9 8.5c0 3.5 2.6 6.5 6.5 6.8l1-1.6-2-1-1 .8c-1-.5-1.9-1.4-2.4-2.4l.8-1-1-2-1.6 1Z" fill="currentColor"/></svg>',
    "esq": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "dir": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "yt": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="4" fill="currentColor"/><path d="M10 9v6l5-3z" fill="#fff"/></svg>',
    "youtube": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2.5" y="5.5" width="19" height="13" rx="4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M10 9.2v5.6l4.8-2.8z" fill="currentColor"/></svg>',
    "instagram": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="17" rx="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.2" cy="6.8" r="1.2" fill="currentColor"/></svg>',
    "tiktok": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 3.5v11a3.4 3.4 0 1 1-3.4-3.4" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round"/><path d="M14 3.5c.5 2.7 2.4 4.4 5 4.6" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round"/></svg>',
    "facebook": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13.5 21v-7.5h2.6l.4-3h-3V8.6c0-.9.3-1.5 1.6-1.5h1.6V4.4c-.3 0-1.2-.1-2.3-.1-2.3 0-3.9 1.4-3.9 4v2.2H8v3h2.6V21z" fill="currentColor"/></svg>',
}


# ---------- utilidades ----------

def norm(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t.lower()).strip()


def fmt_num(n):
    """Arredonda para baixo (2.968 vira "2,9 mil", nunca "3 mil"): número de público não pode parecer maior do que é."""
    if n >= 1_000_000:
        valor = f"{n // 100_000 / 10:.1f}".replace(".", ",").replace(",0", "")
        return f"{valor} {'milhão' if n < 2_000_000 else 'milhões'}"
    if n >= 10_000:
        return f"{n // 1000} mil"
    if n >= 1000:
        return f"{n // 100 / 10:.1f}".replace(".", ",").replace(",0", "") + " mil"
    return str(n)


def fmt_views(n):
    return f"{fmt_num(n)} visualizaç{'ão' if n == 1 else 'ões'}"


def fmt_mes(iso):
    return f"{MESES[int(iso[5:7]) - 1]} {iso[:4]}" if iso else ""


def wa(msg):
    return f"https://wa.me/{cfg['whatsapp']}?text={quote(msg)}"


def yt(vid):
    return f"https://www.youtube.com/watch?v={vid}"


def capa(vid, q="hqdefault"):
    return f"https://i.ytimg.com/vi/{vid}/{q}.jpg"


def link_rede(rede):
    if rede == "whatsapp":
        return wa("Olá! Vim pelo site do Doido Varrido Show.") if cfg.get("whatsapp") else ""
    url = cfg["redes"].get(rede) or ""
    return f"{url}?sub_confirmation=1" if rede == "youtube" and url else url


def emoji_colorido(texto):
    """Coração escrito como texto (U+2764) vira o emoji colorido."""
    return re.sub("\u2764(?!\ufe0f)", "\u2764\ufe0f", texto)


def versao(caminho):
    """Marca do conteúdo do arquivo no endereço: quando o CSS ou o JS muda, o navegador não usa a cópia velha do cache."""
    return hashlib.sha1((SITE / caminho).read_bytes()).hexdigest()[:8]


def json_no_html(obj):
    """JSON seguro dentro de <script>."""
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


# ---------- dados derivados ----------

videos = [v for v in cat["videos"] if not v.get("oculto") and not v.get("repetido")]
musicas = [v for v in videos if v["familia"] in FAMILIAS]
mais_vistas = sorted([v for v in musicas if v["familia"] != "Piadas do Dia"], key=lambda v: -v["views"])[:10]
lancamento = next(v for v in videos if v["familia"] in FAMILIAS)
piadas = sorted([v for v in videos if v["familia"] == "Piadas do Dia"], key=lambda v: v["titulo"])
canal = cat.get("canal", {})


def tem_retrato(p):
    return (SITE / "img" / "personagens" / f"{IMAGEM.get(p['id'], p['id'])}.webp").exists()


personagens = [p for p in uni["personagens"] if tem_retrato(p)]
por_id = {p["id"]: p for p in personagens}
ordem_moradores = [p for g in GRUPOS for p in personagens if p.get("grupo") == g]


def retrato(p, prof=0):
    return f"{'../' * prof}img/personagens/{IMAGEM.get(p['id'], p['id'])}.webp"


def link_morador(p, prof=0):
    return f"{'../' * prof}personagens/{p['id']}.html"


_nomes = sorted(((n, p["id"]) for p in personagens for n in [p["nome"]] + APELIDOS.get(p["id"], [])),
                key=lambda x: -len(x[0]))
_re_nomes = re.compile(r"(?<!\w)(" + "|".join(re.escape(n) for n, _ in _nomes) + r")(?!\w)")
_id_do_nome = dict(_nomes)


def ligar_nomes(texto, proprio, prof):
    """Escapa o texto e transforma nomes de moradores em links para as fichas."""
    partes, pos = [], 0
    for m in _re_nomes.finditer(texto):
        pid = _id_do_nome[m.group(1)]
        partes.append(e(texto[pos:m.start()]))
        partes.append(e(m.group(1)) if pid == proprio else f'<a href="{link_morador(por_id[pid], prof)}">{e(m.group(1))}</a>')
        pos = m.end()
    partes.append(e(texto[pos:]))
    return "".join(partes)


def vizinhos_de(p):
    """Moradores citados nas relações e no lugar do personagem, na ordem em que aparecem."""
    ids = []
    for m in _re_nomes.finditer(f"{p.get('relacoes') or ''} {p.get('local') or ''}"):
        pid = _id_do_nome[m.group(1)]
        if pid != p["id"] and pid not in ids:
            ids.append(pid)
    return [por_id[i] for i in ids]


def videos_do_morador(p):
    termos = [norm(n) for n in [p["nome"]] + APELIDOS.get(p["id"], []) if len(n) > 6 and n != "Doido Varrido Show"]
    return [v for v in videos if any(t in norm(v["titulo_original"]) for t in termos)]


# ---------- pedaços de página ----------

def carrossel(itens, classe, rotulo):
    """Trilho com rolagem lateral; as setas e a régua só aparecem quando há o que rolar."""
    return (f'<div class="carrossel {classe}" data-carrossel>'
            f'<ul class="trilho" tabindex="0" aria-label="{e(rotulo)}">{"".join(itens)}</ul>'
            f'<div class="controles" hidden><button class="seta" type="button" data-anterior aria-label="Voltar">{ICONE["esq"]}</button>'
            f'<div class="regua" aria-hidden="true"><span></span></div>'
            f'<button class="seta" type="button" data-proximo aria-label="Avançar">{ICONE["dir"]}</button></div></div>')


def folheto(p, prof=0, com_balao=True):
    balao = f'<span class="balao rabo-cima">{e(p["bordao"])}</span>' if com_balao and p.get("bordao") else ""
    return (f'<li class="folheto"><a href="{link_morador(p, prof)}"><img src="{retrato(p, prof)}" alt="" width="520" height="780" loading="lazy">'
            f'{balao}<strong>{e(p["nome"])}</strong></a></li>')


def item_video(v, prof=0):
    meta = " · ".join(x for x in [v.get("genero") or v["familia"], v.get("duracao"), fmt_views(v["views"]), fmt_mes(v.get("publicado"))] if x)
    return (f'<li data-familia="{e(v["familia"])}" data-views="{v["views"]}" data-data="{e(v.get("publicado") or "")}" data-busca="{e(norm(v["titulo"]))}">'
            f'<a class="cartao-video" href="{yt(v["id"])}" data-video="{v["id"]}" data-titulo="{e(v["titulo"])}">'
            f'<img src="{capa(v["id"], "mqdefault")}" alt="" width="320" height="180" loading="lazy">'
            f'<span><span class="nome">{e(v["titulo"])}</span><span class="meta">{e(meta)}</span></span></a></li>')


def fala(p, texto_html, legenda_html, prof=0, rabo="40%"):
    return (f'<figure class="fala"><a href="{link_morador(p, prof)}"><img src="{retrato(p, prof)}" alt="{e(p["nome"])}" width="520" height="780" loading="lazy"></a>'
            f'<div><blockquote class="balao rabo-esq revelar" style="--rabo:{rabo}"><p>{texto_html}</p></blockquote>'
            f'<figcaption class="quem">{legenda_html}</figcaption></div></figure>')


def topo(ativo, prof):
    """Barra de palco: faixa escura, selo do Doido pendurado e, no celular, menu em painel com um morador por seção."""
    r = "../" * prof
    menu = [("musicas.html", "Músicas", "coloral", f"{len(musicas)} músicas, do forró à vaquejada"),
            ("vilarejo.html", "Vilarejo", "ze-corneteiro", "Lugares, lendas e a Lei dos Zés"),
            ("moradores.html", "Moradores", "ze-pavio", f"{len(personagens)} figuras da vila"),
            ("index.html#teste", "Quem é você?", "ze-conversa", "O teste de Buraco Fundo"),
            ("index.html#contrate", "Contrate", "ze-coco", "Música, jingle e divulgação")]
    itens = "".join(
        f'<li><a href="{r}{h}"{" aria-current=\"page\"" if h == ativo else ""}>'
        f'<img class="so-menu" src="{retrato(por_id[pid], prof)}" alt="" width="520" height="780" loading="lazy">'
        f'<span><span class="titulo-menu">{e(t)}</span><small class="so-menu">{e(dica)}</small></span></a></li>'
        for h, t, pid, dica in menu if pid in por_id)
    redes = [n for n in ("youtube", "instagram", "facebook", "tiktok") if cfg["redes"].get(n)]
    icones = "".join(f'<a href="{e(link_rede(n))}" target="_blank" rel="noopener" aria-label="{NOME_REDE[n]} do Doido Varrido">{ICONE[n]}</a>' for n in redes)
    botoes = "".join(f'<a class="botao {n}" href="{e(link_rede(n))}" target="_blank" rel="noopener">{NOME_REDE[n]}</a>' for n in redes)
    return f"""<a class="pular" href="#conteudo">Pular para o conteúdo</a>
<header class="topo" data-topo>
 <div class="miolo">
  <a class="marca" href="{r}index.html"><img src="{r}img/logo-doido-varrido.webp" alt="O Doido Varrido Show, página inicial" width="640" height="496"></a>
  <nav class="menu" id="menu" aria-label="Principal">
   <ul>{itens}</ul>
   <div class="menu-redes so-menu"><span>Siga o Doido:</span>{botoes}</div>
  </nav>
  <div class="topo-acoes">
   <div class="redes-topo">{icones}</div>
   <a class="botao apoiar" href="{r}index.html#apoie">Apoiar</a>
   <button class="abrir-menu" type="button" aria-expanded="false" aria-controls="menu" data-menu><span class="hamburguer" aria-hidden="true"></span><span class="rotulo">Menu</span></button>
  </div>
 </div>
</header>"""


def pregao(prof):
    pg = cfg.get("pregao") or {}
    p = por_id.get(pg.get("personagem", ""))
    if not p:
        return ""
    redes = "".join(f'<a href="{e(link_rede(r))}" target="_blank" rel="noopener">{NOME_REDE[r]}</a>'
                    for r in ["youtube", "instagram", "facebook", "tiktok"] if link_rede(r))
    return f"""<aside class="pregao" data-pregao hidden aria-label="Siga o Doido Varrido nas redes">
 <img src="{retrato(p, prof)}" alt="{e(p['nome'])}" width="520" height="780">
 <div class="balao rabo-dir"><p><b>{e(pg.get('titulo', ''))}</b>{e(pg.get('fala', ''))}</p><div class="redes-mini">{redes}</div></div>
 <button class="fechar" type="button" data-fechar-pregao aria-label="Fechar o aviso">×</button>
</aside>"""


def rodape(prof):
    r = "../" * prof
    links = [("YouTube", cfg["redes"].get("youtube")), ("Instagram", cfg["redes"].get("instagram")),
             ("Facebook", cfg["redes"].get("facebook")), ("TikTok", cfg["redes"].get("tiktok")),
             ("Kwai", cfg["redes"].get("kwai")), ("Canal no WhatsApp", cfg["redes"].get("canal_whatsapp")),
             ("Falar no WhatsApp", link_rede("whatsapp"))]
    lis = "".join(f'<li><a href="{e(u)}" rel="noopener" target="_blank">{n}</a></li>' for n, u in links if u)
    internos = [("Quem faz", "index.html#quem-faz", (cfg.get("quem_faz") or {}).get("ativo")),
                ("Vire morador de Buraco Fundo", "index.html#vire-morador", (cfg.get("vire_morador") or {}).get("ativo")),
                ("Anuncie na vila", "patrocinio.html", (cfg.get("patrocinio") or {}).get("ativo")),
                ("Figurinhas grátis", "figurinhas.html", bool(lista_figurinhas()))]
    lis_internos = "".join(f'<li><a href="{r}{h}">{n}</a></li>' for n, h, ok in internos if ok)
    return f"""<footer class="rodape">
 <div class="miolo">
  <img src="{r}img/logo-doido-varrido.webp" alt="" width="640" height="496">
  <div>
   <ul>{lis_internos}</ul>
   <ul>{lis}</ul>
   <p>O Doido Varrido Show e o Vilarejo Buraco Fundo são criações de {e(cfg['criador'])}. © {date.today().year}</p>
   {f'<p class="aviso-ficcao">{e(cfg["aviso_ficcao"])}</p>' if cfg.get("aviso_ficcao") else ""}
  </div>
 </div>
</footer>"""


def janela_video():
    return """<dialog class="janela-video" aria-label="Vídeo">
 <div class="barra"><span></span><button type="button" data-fechar>Fechar</button></div>
 <div class="tela"></div>
</dialog>"""


def pagina(arquivo, titulo, descricao, corpo, ativo="", prof=0, imagem="img/compartilhar.jpg", extra=""):
    r = "../" * prof
    base = cfg.get("endereco_site", "").rstrip("/")
    caminho = arquivo.replace("index.html", "")
    canon = f'<link rel="canonical" href="{base}/{caminho}">\n' if base else ""
    img_og = f"{base}/{imagem}" if base else f"{r}{imagem}"
    doc = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descricao)}">
{canon}<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="{e(cfg['nome'])}">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descricao)}">
<meta property="og:image" content="{e(img_og)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FBC02D">
<link rel="icon" href="{r}img/logo-doido-varrido.webp" type="image/webp">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Alegreya:ital,wght@0,400;0,700;1,400;1,700&family=Alegreya+Sans:wght@500;700;800&family=Ultra&display=swap">
<link rel="stylesheet" href="{r}css/estilo.css?v={versao('css/estilo.css')}">
<script>document.documentElement.classList.add("js")</script>
{extra}</head>
<body>
{topo(ativo, prof)}
<main id="conteudo">
{corpo}
</main>
{rodape(prof)}
{pregao(prof)}
{janela_video()}
<script src="{r}js/site.js?v={versao('js/site.js')}" defer></script>
</body>
</html>
"""
    destino = SITE / arquivo
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(doc, encoding="utf-8")
    return destino


# ---------- página inicial ----------

def inicio():
    silf = por_id["silfarnney-valenca"]
    frase = uni["silfarnney"]["frases"][2]
    meta_lanc = f"Lançamento · {lancamento.get('genero') or lancamento['familia']} · {fmt_views(lancamento['views'])}"
    plantao = "".join(f"<li>{e(t)}</li>" for t in cfg.get("plantao", []))

    parada = "".join(
        f'<li><a href="{yt(v["id"])}" data-faixa data-id="{v["id"]}" data-titulo="{e(v["titulo"])}" '
        f'data-meta="{e((v.get("genero") or v["familia"]) + " · " + fmt_views(v["views"]))}">'
        f'<img class="capa-faixa" src="{capa(v["id"], "mqdefault")}" alt="" width="320" height="180" loading="lazy">'
        f'<span class="pos">{i}</span><span><span class="nome">{e(v["titulo"])}</span>'
        f'<span class="meta">{e(v.get("genero") or v["familia"])}<span class="so-celular"> · {fmt_num(v["views"])}</span></span></span>'
        f'<span class="views">{fmt_num(v["views"])}</span></a></li>'
        for i, v in enumerate(mais_vistas, 1))

    baloes = [f'<li><figure class="comentario"><blockquote class="balao revelar"><p>{e(emoji_colorido(c["texto"]))}</p></blockquote>'
              f'<figcaption>{ICONE["yt"]}<span>Comentário em <a href="{yt(c["video_id"])}" data-video="{c["video_id"]}" '
              f'data-titulo="{e(c["video_titulo"])}">{e(c["video_titulo"])}</a></span></figcaption></figure></li>'
              for c in comentarios]

    frases_vila = re.split(r"(?<=[.!?])\s+", uni["universo"]["apresentacao"])
    resumo_vila = " ".join(frases_vila[1:]) if len(frases_vila) > 2 else uni["universo"]["apresentacao"]
    conversa = por_id["ze-conversa"]
    lenda_curta = ("Dizem que o governo dava um saco de milho e uma galinha poedeira pra quem registrasse o filho como Zé. "
                   "O povo correu pro cartório. Hoje, se gritar “Ô Zé!”, metade da vila responde.")

    destaque_ids = DESTAQUES + [p["id"] for p in ordem_moradores if p["id"] not in DESTAQUES]
    gente = [folheto(por_id[i]) for i in destaque_ids if i in por_id]

    ids_teste = list(dict.fromkeys(o["resultado"] for q in teste["perguntas"] for o in q["opcoes"]))
    dados_teste = {
        "perguntas": teste["perguntas"],
        "endereco": (cfg.get("endereco_site", "").rstrip("/") + "/#teste") if cfg.get("endereco_site") else "",
        "resultados": {i: {"nome": por_id[i]["nome"], "bordao": por_id[i].get("bordao", ""), "descricao": por_id[i].get("descricao", ""),
                           "img": retrato(por_id[i]), "link": link_morador(por_id[i])} for i in ids_teste},
    }
    rostos = "".join(f'<img src="{retrato(por_id[i])}" alt="" width="520" height="780" loading="lazy">' for i in ids_teste[:5])

    anuncios = [f'<li><article class="anuncio"><h3>{e(s["titulo"])}</h3><p>{e(s["texto"])}</p>'
                + (f'<p class="preco-anuncio">{e(s["preco"])}</p>' if s.get("preco") else "")
                + (f'<a class="botao" href="{e(s["link"])}">{e(s["botao"])}</a>' if s.get("link") else
                   f'<a class="botao" href="{e(wa(s["mensagem"]))}" target="_blank" rel="noopener">{ICONE["whats"]}{e(s["botao"])}</a>')
                + '</article></li>'
                for s in cfg["servicos"] if s.get("ativo")]
    eb = cfg.get("em_breve", {})
    em_breve = (f'<div class="em-breve"><div><h3>{e(eb["titulo"])}</h3><p>{e(eb["texto"])}</p></div>'
                f'<a class="botao papel" href="{e(wa(eb["mensagem"]))}" target="_blank" rel="noopener">{e(eb["botao"])}</a></div>') if eb.get("ativo") else ""
    numeros = [(fmt_num(canal["visualizacoes"]), "de visualizações no YouTube") if canal.get("visualizacoes") else None,
               (fmt_num(canal["inscritos"]), "inscritos no canal") if canal.get("inscritos") else None,
               (str(len(cat["videos"])), "vídeos no canal")]
    numeros_html = "".join(f"<li><strong>{a}</strong>{b}</li>" for a, b in filter(None, numeros))
    selo = (f'<p class="selo-views"><strong>{fmt_num(canal["visualizacoes"])}</strong>de visualizações</p>'
            if canal.get("visualizacoes") else "")

    pix = cfg.get("pix", {})
    apoie = cfg.get("apoie", {})
    fiado = por_id.get(apoie.get("personagem", ""))
    balcao = (f'<div class="balcao"><img src="img/recorte-ze-fiado.webp" alt="{e(fiado["nome"])}, dono do mercadinho" width="560" height="1276" loading="lazy">'
              f'<blockquote class="balao rabo-esq revelar"><p>“{e(apoie["fala"])}”</p></blockquote></div>') if fiado and (SITE / "img/recorte-ze-fiado.webp").exists() else ""

    redes = "".join(
        f'<li class="rede-chamada"><blockquote class="balao revelar"><p>{e(c["fala"])}</p></blockquote>'
        f'<img src="{retrato(por_id[c["personagem"]])}" alt="{e(por_id[c["personagem"]]["nome"])}" width="520" height="780" loading="lazy">'
        f'<a class="botao {c["rede"]}" href="{e(link_rede(c["rede"]))}" target="_blank" rel="noopener">{e(c["botao"])}</a></li>'
        for c in cfg.get("chamadas_redes", []) if c["personagem"] in por_id and link_rede(c["rede"]))

    ld = {"@context": "https://schema.org", "@type": "Person", "name": cfg["criador"], "alternateName": cfg["nome"],
          "description": cfg["descricao"], "sameAs": [u for u in cfg["redes"].values() if u]}

    corpo = f"""
<section class="cartaz serrilha-baixo">
 <div class="bandeirinhas" aria-hidden="true"></div>
 <div class="miolo">
  <div>
   <h1>{e(cfg['frase_capa'])}</h1>
   <p class="chamada">{e(cfg['descricao'])}</p>
   <div class="botoes">
    <a class="botao" href="#radio">{ICONE['play']}Ouvir as mais pedidas</a>
    <a class="botao papel" href="#teste">Quem é você em Buraco Fundo?</a>
   </div>
  </div>
  <div class="palco">
   <blockquote class="balao revelar"><p>“{e(frase)}”</p></blockquote>
   <figure class="retrato-capa">
    <img src="{retrato(silf)}" alt="Caricatura de Silfarnney Valença de terno preto e óculos escuros, segurando um microfone antigo" width="520" height="780" fetchpriority="high">
    <figcaption>{e(cfg['criador'])}</figcaption>
   </figure>
   {selo}
  </div>
 </div>
</section>

<aside class="letreiro" aria-label="Plantão extraordinário: notícias de Buraco Fundo">
 <span class="selo">Plantão extraordinário!</span>
 <div class="janela" tabindex="0"><div class="rolo"><ul>{plantao}</ul><ul aria-hidden="true">{plantao}</ul></div></div>
</aside>

<section class="faixa" id="radio" aria-labelledby="t-radio">
 <div class="miolo">
  <div class="cabeca-faixa">
   <h2 id="t-radio">As mais pedidas da Rádio Buraco Fundo FM</h2>
   <p><a class="ver-mais" href="musicas.html">Ver todas as {len(musicas)} músicas</a></p>
  </div>
  <div class="radio">
   <div class="tocador" data-tocador data-id="{lancamento['id']}" data-titulo="{e(lancamento['titulo'])}">
    <div class="tela">
     <img src="{capa(lancamento['id'], 'hqdefault')}" alt="" width="480" height="360">
     <button class="play" type="button" aria-label="Tocar {e(lancamento['titulo'])}">{ICONE['play']}</button>
    </div>
    <p class="legenda">{e(lancamento['titulo'])}<small>{e(meta_lanc)}</small></p>
   </div>
   <ol class="parada" aria-label="As dez mais vistas">{parada}</ol>
  </div>
 </div>
</section>

<section class="faixa clara" aria-labelledby="t-povo">
 <div class="miolo">
  <div class="cabeca-faixa">
   <h2 id="t-povo">O povo tá dizendo</h2>
   <p>Comentários de verdade, tirados dos vídeos do canal.</p>
  </div>
  {carrossel(baloes, "comentarios", "Comentários do povo no YouTube")}
 </div>
</section>
{quem_faz()}
<section aria-labelledby="t-vila">
 <div class="panorama">
  <img src="img/vila-panorama.webp" alt="Rua de terra do Vilarejo Buraco Fundo ao pôr do sol, com casas coloridas, mandacarus, um jegue e a igreja ao fundo" width="1920" height="1080" loading="lazy">
  <div class="placa">
   <img src="img/logo-buraco-fundo.webp" alt="Vilarejo Buraco Fundo" width="720" height="720">
   <p>{e(uni['universo']['slogans'][0])}</p>
  </div>
 </div>
 <div class="faixa">
  <div class="miolo duas">
   <div>
    <h2 id="t-vila">Onde o vento faz a curva</h2>
    <p>{e(resumo_vila)}</p>
    <div class="botoes">
     <a class="botao" href="vilarejo.html">Conhecer o vilarejo</a>
     <a class="botao papel" href="vilarejo.html#piadas">Assistir às Piadas do Dia</a>
    </div>
   </div>
   {fala(conversa, e(lenda_curta), f'{e(conversa["nome"])}, contando a Lenda dos Zés. <a href="vilarejo.html#zes">Ler a lenda inteira</a>')}
  </div>
 </div>
</section>

<section class="faixa clara" aria-labelledby="t-gente">
 <div class="miolo">
  <div class="cabeca-faixa">
   <h2 id="t-gente">Gente de Buraco Fundo</h2>
   <p><a class="ver-mais" href="moradores.html">Ver todos os {len(personagens)} moradores</a></p>
  </div>
  {carrossel(gente, "folhetos-trilho", "Moradores de Buraco Fundo")}
 </div>
</section>
{faixa_figurinhas()}
<section class="faixa ceu" id="teste" aria-labelledby="t-teste" data-teste>
 <script type="application/json">{json_no_html(dados_teste)}</script>
 <div class="miolo">
  <h2 id="t-teste">{e(teste['titulo'])}</h2>
  <div class="quadro-teste" aria-live="polite">
   <div class="teste-inicio">
    <div class="rostos">{rostos}</div>
    <div>
     <p>{e(teste['chamada'])}</p>
     <button class="botao" type="button" data-comecar>Começar o teste</button>
    </div>
   </div>
  </div>
 </div>
</section>
{vire_morador()}
<section class="faixa clara" id="contrate" aria-labelledby="t-contrate">
 <div class="miolo">
  <h2 id="t-contrate">Contrate o Doido Varrido</h2>
  <p class="sub">Música, jingle ou divulgação com a cara do Nordeste. Chame no WhatsApp, conte o que você quer e receba o orçamento.</p>
  <ul class="numeros">{numeros_html}</ul>
  {carrossel(anuncios, "anuncios-trilho", "Serviços")}
  {em_breve}
 </div>
</section>

<section class="faixa apoie" id="apoie" aria-labelledby="t-apoie">
 <div class="miolo">
  <div>
   <h2 id="t-apoie">Apoie o canal</h2>
   {balcao}
   <p>Mas apoio pode ser hoje: se o Doido Varrido já te fez rir, um PIX de qualquer valor ajuda o canal a continuar com vídeo novo toda semana.</p>
   <p>Não pode agora? <a href="{e(link_rede('youtube'))}" target="_blank" rel="noopener">Inscrever-se no canal</a> e mandar um vídeo para os amigos também ajuda, e não custa nada.</p>
  </div>
  <div class="pix">
   <p class="rotulo-pix">Chave PIX ({e(pix.get('tipo', ''))})</p>
   <p class="chave">{e(pix.get('como_aparece', ''))}</p>
   <button class="botao" type="button" data-copiar="{e(pix.get('chave', ''))}">Copiar chave PIX</button>
   <p class="aviso" role="status"></p>
  </div>
 </div>
</section>

<section class="faixa" id="siga" aria-labelledby="t-siga">
 <div class="miolo">
  <h2 id="t-siga">Siga o Doido Varrido</h2>
  <ul class="redes">{redes}</ul>
 </div>
</section>
"""
    extra = f'<script type="application/ld+json">{json_no_html(ld)}</script>\n'
    return pagina("index.html", f"{cfg['nome']}, com {cfg['criador']}", cfg["descricao"], corpo, "index.html", extra=extra)


# ---------- páginas internas ----------

def pagina_musicas():
    contagem = {f: sum(1 for v in musicas if v["familia"] == f) for f in FAMILIAS}
    filtros = f'<button type="button" data-familia="todas" aria-pressed="true">Todas <span>{len(musicas)}</span></button>'
    filtros += "".join(f'<button type="button" data-familia="{e(f)}" aria-pressed="false">{e(f)} <span>{n}</span></button>'
                       for f, n in contagem.items() if n)
    lista = "".join(item_video(v) for v in sorted(musicas, key=lambda v: -v["views"]))
    corpo = f"""
<section class="abertura serrilha-baixo">
 <div class="miolo">
  <h1>Todas as músicas</h1>
  <p>{len(musicas)} vídeos do canal, do forró cômico à vaquejada. Toque aqui mesmo, sem sair do site.</p>
  <div class="filtros" role="group" aria-label="Filtrar por estilo">{filtros}</div>
  <div class="busca">
   <label>Procurar pelo nome<input id="busca" type="search" placeholder="Ex.: mandamentos" autocomplete="off"></label>
   <label>Ordem<select id="ordem"><option value="views">Mais vistas primeiro</option><option value="data">Mais novas primeiro</option></select></label>
  </div>
 </div>
</section>
<section class="faixa" aria-label="Lista de músicas">
 <div class="miolo">
  <ul class="catalogo" data-catalogo>{lista}</ul>
  <p class="vazio" hidden>Nenhuma música com esse nome. Tente outra palavra ou escolha “Todas”.</p>
  <div class="mais-musicas"><p class="contador" role="status"></p><button class="botao papel" type="button" data-mais hidden>Mostrar mais músicas</button></div>
 </div>
</section>
"""
    return pagina("musicas.html", f"Músicas do {cfg['nome']}",
                  f"Forró cômico, embolada, vaquejada, cordel e pisadinha de {cfg['criador']}: {len(musicas)} músicas para ouvir no site.",
                  corpo, "musicas.html")


def pagina_vilarejo():
    u = uni["universo"]
    conversa = por_id["ze-conversa"]
    lugares = [f'<li><div class="cartao"><strong>{e(c["nome"])}</strong><span>{e(c["descricao"])}</span></div></li>'
               for c in u["cenarios"] if c.get("oficial")]
    artigos = [f'<li><div class="cartao artigo"><b>{e(a["artigo"])}</b><span>{e(a["texto"])}</span></div></li>' for a in u["lei_dos_zes"]]
    vilas = [f'<li><div class="cartao"><strong>{e(v["nome"])}</strong><em>“{e(v["slogan"])}”</em><span>{e(v["descricao"])}</span></div></li>'
             for v in u["vale_das_conversas"]]
    lendas = [f'<li><div class="cartao"><strong>{e(f["nome"])}</strong><span>{e(f["descricao"])}</span></div></li>'
              for f in u["folclore"] if "não descreve" not in f["descricao"]]
    festas = "".join(f"<li>{e(f)}</li>" for f in u["eventos"])
    lista_piadas = [item_video(v) for v in piadas]
    corpo = f"""
<section class="abertura serrilha-baixo">
 <div class="miolo duas">
  <div>
   <h1>Vilarejo Buraco Fundo</h1>
   <p>{e(u['apresentacao'])}</p>
   <p><strong>{e(u['populacao'])}</strong>, no {e(u['regiao'])}.</p>
  </div>
  <img src="img/bandeira-buraco-fundo.webp" alt="Bandeira do Vilarejo Buraco Fundo: um mandacaru e um chapéu de couro sobre fundo amarelo e verde, com a frase Mais fundo que o buraco é a conversa do povo" width="960" height="640">
 </div>
</section>

<section class="faixa" id="lugares" aria-labelledby="t-lugares">
 <div class="miolo">
  <div class="cabeca-faixa"><h2 id="t-lugares">Lugares da vila</h2><p>Arraste para o lado e dê uma volta pela vila.</p></div>
  {carrossel(lugares, "cartoes", "Lugares da vila")}
 </div>
</section>

<section class="faixa clara" id="piadas" aria-labelledby="t-piadas">
 <div class="miolo">
  <div class="cabeca-faixa"><h2 id="t-piadas">Piadas do Dia, direto do vilarejo</h2><p>A série em que {e(cfg['criador'])} conta os causos dos moradores.</p></div>
  {carrossel(lista_piadas, "videos-trilho", "Episódios das Piadas do Dia")}
 </div>
</section>

<section class="faixa" id="zes" aria-labelledby="t-zes">
 <div class="miolo">
  <h2 id="t-zes">A Lenda dos Zés</h2>
  {fala(conversa, e(u['lenda_dos_zes']['resumo']), f'Segundo {e(conversa["nome"])}. Ninguém sabe se é verdade. {e(u["lenda_dos_zes"]["bordao"])}', rabo="64px")}
  <div class="cabeca-faixa" style="margin-top:2.6rem"><h2>Lei Municipal nº&nbsp;01, a Lei dos Zés</h2></div>
  {carrossel(artigos, "cartoes", "Artigos da Lei dos Zés")}
 </div>
</section>

<section class="faixa clara" aria-labelledby="t-festas">
 <div class="miolo">
  <h2 id="t-festas">Festas do calendário</h2>
  <ul class="festas">{festas}</ul>
 </div>
</section>

<section class="faixa" aria-labelledby="t-vale">
 <div class="miolo">
  <div class="cabeca-faixa"><h2 id="t-vale">{e(u['regiao'])}</h2><p>Os vizinhos de Buraco Fundo, onde toda história aumenta antes de chegar ao fim.</p></div>
  {carrossel(vilas, "cartoes", "Vilarejos do Vale das Conversas Perdidas")}
 </div>
</section>

<section class="faixa clara" aria-labelledby="t-lendas">
 <div class="miolo">
  <div class="cabeca-faixa"><h2 id="t-lendas">Lendas da estrada</h2></div>
  {carrossel(lendas, "cartoes", "Lendas da região")}
  <div class="botoes"><a class="botao" href="moradores.html">Conhecer os moradores</a><a class="botao papel" href="index.html#teste">Quem é você em Buraco Fundo?</a></div>
 </div>
</section>
"""
    return pagina("vilarejo.html", "Vilarejo Buraco Fundo, o universo do Doido Varrido Show",
                  uni["universo"]["frase_institucional"], corpo, "vilarejo.html", imagem="img/vila-panorama.webp")


def pagina_moradores():
    blocos = []
    for g, titulo in GRUPOS.items():
        lista = [p for p in personagens if p.get("grupo") == g]
        if lista:
            classe = " clara" if len(blocos) % 2 else ""
            blocos.append(f'<section class="faixa{classe}" aria-label="{e(titulo)}"><div class="miolo"><h2>{e(titulo)}</h2>'
                          f'<ul class="grade">{"".join(folheto(p) for p in lista)}</ul></div></section>')
    corpo = f"""
<section class="abertura serrilha-baixo">
 <div class="miolo">
  <h1>Os moradores de Buraco Fundo</h1>
  <p>{len(personagens)} figuras da vila, cada uma com seu bordão. Toque num folheto para conhecer a história, ou <a href="index.html#teste">faça o teste</a> e descubra qual delas é você.</p>
  {f'<p class="aviso-ficcao-topo">{e(cfg["aviso_ficcao"])}</p>' if cfg.get("aviso_ficcao") else ""}
 </div>
</section>
{''.join(blocos)}
"""
    return pagina("moradores.html", f"Moradores do Vilarejo Buraco Fundo | {cfg['nome']}",
                  "Zé Pavio, Raimunda, Zé Tonhim Café Doce, Coloral e todos os moradores do Vilarejo Buraco Fundo.", corpo, "moradores.html",
                  imagem="img/povo-de-buraco-fundo.webp")


def fichas():
    for i, p in enumerate(ordem_moradores):
        ant, prox = ordem_moradores[i - 1], ordem_moradores[(i + 1) % len(ordem_moradores)]
        linhas = []
        if p.get("local"):
            linhas.append(("Onde encontrar", ligar_nomes(p["local"], p["id"], 1)))
        if p.get("relacoes"):
            linhas.append(("Na vila", ligar_nomes(p["relacoes"], p["id"], 1)))
        dl = "".join(f"<dt>{a}</dt><dd>{b}</dd>" for a, b in linhas)
        vids = videos_do_morador(p)
        nos_videos = (f'<h2 style="font-size:1.8rem;margin-top:2.2rem">Nos vídeos</h2>'
                      f'{carrossel([item_video(v, 1) for v in vids], "videos-trilho", "Vídeos com " + p["nome"])}') if vids else ""
        perto = vizinhos_de(p)
        gente_perto = (f'<section class="faixa clara" aria-labelledby="t-perto"><div class="miolo"><div class="cabeca-faixa">'
                       f'<h2 id="t-perto">Gente de perto</h2><p>Quem convive com {e(p["nome"])} na vila.</p></div>'
                       f'{carrossel([folheto(q, 1) for q in perto], "folhetos-trilho", "Moradores ligados a " + p["nome"])}</div></section>') if perto else ""
        bordao = f'<blockquote class="balao revelar"><p>“{e(p["bordao"])}”</p></blockquote>' if p.get("bordao") else ""
        corpo = f"""
<section class="faixa">
 <div class="miolo ficha">
  <div class="folheto-grande"><img src="{retrato(p, 1)}" alt="Ilustração de {e(p['nome'])}" width="520" height="780"></div>
  <div>
   <h1>{e(p['nome'])}</h1>
   <p class="papel">{e(p.get('papel') or '')}</p>
   {bordao}
   <p>{ligar_nomes(p.get('descricao') or '', p['id'], 1)}</p>
   <dl>{dl}</dl>
   {nos_videos}
  </div>
 </div>
</section>
{gente_perto}
<section class="faixa" aria-label="Continuar">
 <div class="miolo">
  <nav class="vizinhos" aria-label="Outros moradores">
   <a href="{ant['id']}.html">Anterior: {e(ant['nome'])}</a>
   <a href="../index.html#teste">Quem é você em Buraco Fundo?</a>
   <a href="{prox['id']}.html">Próximo: {e(prox['nome'])}</a>
  </nav>
 </div>
</section>
"""
        desc = f"{p['nome']}, {p.get('papel') or 'morador do Vilarejo Buraco Fundo'}. " + (p.get("descricao") or "")
        pagina(f"personagens/{p['id']}.html", f"{p['nome']} | Vilarejo Buraco Fundo", desc[:300], corpo, "moradores.html", prof=1,
               imagem=retrato(p))


def quem_faz():
    q = cfg.get("quem_faz") or {}
    if not q.get("ativo") or not (SITE / q.get("foto", "")).exists():
        return ""
    silf = por_id.get("silfarnney-valenca")
    caricatura = (f'<figure class="foto-vila"><img src="{retrato(silf)}" alt="Caricatura de {e(q["nome_completo"])} no Vilarejo Buraco Fundo" '
                  f'width="520" height="780" loading="lazy"><figcaption>Na vila</figcaption></figure>') if silf else ""
    titulos = {v["id"]: v["titulo"] for v in cat["videos"]}
    botoes = "".join(f'<a class="botao{" papel" if i else ""}" href="{yt(v["id"])}" data-video="{v["id"]}" '
                     f'data-titulo="{e(titulos.get(v["id"], v["rotulo"]))}">{ICONE["play"]}{e(v["rotulo"])}</a>'
                     for i, v in enumerate(q.get("videos", [])))
    dados = [("Idade", f'{q["idade"]} anos' if q.get("idade") else ""), ("Nasceu em", q.get("nasceu", "")), ("Mora em", q.get("mora", ""))]
    ficha = "".join(f"<div><dt>{a}</dt><dd>{e(b)}</dd></div>" for a, b in dados if b)
    return f"""
<section class="faixa quem-faz" id="quem-faz" aria-labelledby="t-quem">
 <div class="miolo duas">
  <div class="dupla">
   <figure class="foto-real"><img src="{q['foto']}" alt="Foto de {e(q['nome_completo'])}, sorrindo na praia, de boné e óculos" width="400" height="500" loading="lazy"><figcaption>Na vida real</figcaption></figure>
   {caricatura}
  </div>
  <div>
   <h2 id="t-quem">Quem faz o Doido Varrido</h2>
   <p class="nome-real">{e(q['nome_completo'])}</p>
   <dl class="ficha-rapida">{ficha}</dl>
   {"".join(f"<p>{e(t)}</p>" for t in q.get("paragrafos", []))}
   <div class="botoes">{botoes}</div>
  </div>
 </div>
</section>
"""


def pedido(mensagem, preco, rotulo_com_preco="Pedir pelo WhatsApp"):
    """Botão de pedido: com preço definido pede direto; sem preço, pede orçamento."""
    rotulo = rotulo_com_preco if preco else "Pedir orçamento"
    return f'<a class="botao" href="{e(wa(mensagem))}" target="_blank" rel="noopener">{ICONE["whats"]}{rotulo}</a>'


def vire_morador():
    vm = cfg.get("vire_morador") or {}
    if not vm.get("ativo"):
        return ""
    passos = "".join(f"<li>{e(t)}</li>" for t in vm.get("passos", []))
    pacotes = "".join(
        f'<li class="pacote"><h3>{e(p["nome"])}</h3><ul>{"".join(f"<li>{e(i)}</li>" for i in p["inclui"])}</ul>'
        + (f'<p class="preco">{e(p["preco"])}</p>' if p.get("preco") else "")
        + (f'<p class="prazo">Entrega em {e(p["prazo"])}</p>' if p.get("prazo") else "")
        + pedido(p["mensagem"], p.get("preco")) + "</li>"
        for p in vm.get("pacotes", []))
    vizinhos = [por_id[i] for i in ("ze-pavio", "raimunda") if i in por_id]
    cartao = lambda p, giro: (f'<figure class="cartao-morador" style="--giro:{giro}"><img src="{retrato(p)}" alt="" width="520" height="780" loading="lazy">'
                              f'<figcaption>{e(p["nome"])}</figcaption></figure>')
    vitrine = (cartao(vizinhos[0], "-7deg") if vizinhos else "") + (
        '<figure class="cartao-morador voce" style="--giro:1deg"><div class="vaga"><span>?</span></div><figcaption>Você</figcaption></figure>'
    ) + (cartao(vizinhos[1], "6deg") if len(vizinhos) > 1 else "")
    return f"""
<section class="faixa morador" id="vire-morador" aria-labelledby="t-morador">
 <div class="miolo duas">
  <div>
   <h2 id="t-morador">{e(vm['titulo'])}</h2>
   <p class="sub">{e(vm['texto'])}</p>
   <ol class="passos">{passos}</ol>
  </div>
  <div class="vitrine">
   <p class="balao revelar">{e(vm.get('fala', ''))}</p>
   <div class="fileira">{vitrine}</div>
  </div>
 </div>
 <div class="miolo">
  <ul class="pacotes">{pacotes}</ul>
  <p class="aviso-foto">{e(vm.get('aviso', ''))}</p>
 </div>
</section>
"""


def lista_figurinhas():
    """Figurinhas já desenhadas (node ferramentas/figurinhas.mjs), na ordem do dados/figurinhas.json."""
    dados = ler("figurinhas.json")
    lista = []
    for i, f in enumerate(dados["figurinhas"], 1):
        arq = f"figurinhas/{i:02d}-{f['personagem']}.webp"
        if (SITE / arq).exists():
            nome = por_id[f["personagem"]]["nome"] if f["personagem"] in por_id else f["personagem"]
            lista.append({"arq": arq, "texto": f["texto"], "nome": nome})
    return lista


def faixa_figurinhas():
    figs = lista_figurinhas()
    if not figs:
        return ""
    itens = [f'<li><img class="figurinha" src="{f["arq"]}" alt="Figurinha de {e(f["nome"])}: {e(f["texto"])}" width="512" height="512" loading="lazy"></li>'
             for f in figs]
    return f"""
<section class="faixa" aria-labelledby="t-figs">
 <div class="miolo">
  <div class="cabeca-faixa">
   <h2 id="t-figs">Figurinhas grátis pro seu WhatsApp</h2>
   <p><a class="ver-mais" href="figurinhas.html">Ver todas e baixar</a></p>
  </div>
  <p class="sub">{len(figs)} figurinhas com os moradores de Buraco Fundo e os bordões deles. É só baixar e usar.</p>
  {carrossel(itens, "figurinhas-trilho", "Figurinhas")}
  <div class="botoes"><a class="botao" href="figurinhas.html">Pegar as figurinhas</a></div>
 </div>
</section>
"""


def pagina_figurinhas():
    figs = lista_figurinhas()
    if not figs:
        return
    dados = ler("figurinhas.json")
    pacote = dados.get("link_pacote", "")
    endereco = cfg.get("endereco_site", "").rstrip("/")
    convite = "Olha as figurinhas grátis do Doido Varrido Show pro WhatsApp!" + (f" {endereco}/figurinhas.html" if endereco else "")
    grade = "".join(
        f'<li><figure><img class="figurinha" src="{f["arq"]}" alt="Figurinha de {e(f["nome"])}: {e(f["texto"])}" width="512" height="512" loading="lazy">'
        f'<figcaption><a class="botao papel" href="{f["arq"]}" download>Baixar</a></figcaption></figure></li>'
        for f in figs)
    botao_pacote = (f'<a class="botao verde" href="{e(pacote)}" target="_blank" rel="noopener">{ICONE["whats"]}Adicionar o pacote no WhatsApp</a>'
                    if pacote else "")
    corpo = f"""
<section class="abertura serrilha-baixo">
 <div class="miolo">
  <h1>Figurinhas grátis do Doido Varrido</h1>
  <p>{len(figs)} figurinhas com os moradores do Vilarejo Buraco Fundo, cada um com o seu bordão. Pode baixar, usar e mandar pros amigos.</p>
  <div class="botoes">
   {botao_pacote}
   <a class="botao papel" href="https://wa.me/?text={quote(convite)}" target="_blank" rel="noopener">{ICONE['whats']}Mandar pra um amigo</a>
  </div>
 </div>
</section>

<section class="faixa" aria-labelledby="t-como-fig">
 <div class="miolo duas">
  <div>
   <h2 id="t-como-fig">Como colocar no WhatsApp</h2>
   <ol class="passos">
    <li>No celular, toque em “Baixar” embaixo da figurinha (ou segure o dedo nela e salve a imagem).</li>
    <li>No WhatsApp, abra uma conversa, toque no ícone de figurinhas e depois em “Criar” ou no sinal de mais.</li>
    <li>Escolha a imagem que você salvou e envie. Ela fica guardada nas suas figurinhas.</li>
   </ol>
   <p class="nota">O botão de criar figurinha aparece nas versões mais novas do WhatsApp. Se não aparecer, atualize o aplicativo.</p>
  </div>
  <img class="figurinha destaque" src="{figs[0]['arq']}" alt="" width="512" height="512">
 </div>
</section>

<section class="faixa clara" aria-label="Todas as figurinhas">
 <div class="miolo">
  <ul class="grade-figurinhas">{grade}</ul>
 </div>
</section>
"""
    pagina("figurinhas.html", f"Figurinhas grátis do {cfg['nome']}",
           f"{len(figs)} figurinhas grátis do Vilarejo Buraco Fundo para o WhatsApp.", corpo, "", imagem=figs[0]["arq"])


def pagina_patrocinio():
    pt = cfg.get("patrocinio") or {}
    if not pt.get("ativo"):
        return
    rn = pt.get("redes_numeros", {})
    top = mais_vistas[0] if mais_vistas else None
    placar = [(fmt_num(canal["visualizacoes"]), "visualizações no YouTube") if canal.get("visualizacoes") else None,
              (fmt_num(canal["inscritos"]), "inscritos no YouTube") if canal.get("inscritos") else None,
              (fmt_num(rn["instagram"]), "seguidores no Instagram") if rn.get("instagram") else None,
              (fmt_num(rn["facebook"]), "seguidores no Facebook") if rn.get("facebook") else None,
              (str(len(cat["videos"])), "vídeos publicados"),
              (fmt_num(top["views"]), f"visualizações em “{top['titulo']}”, a mais vista") if top else None]
    placar_html = "".join(f"<li><strong>{a}</strong><span>{e(b)}</span></li>" for a, b in filter(None, placar))
    formatos = [f'<li><div class="cartao"><strong>{e(f["nome"])}</strong><span>{e(f["texto"])}</span>'
                + (f'<em class="preco">{e(f["preco"])}</em>' if f.get("preco") else "") + "</div></li>"
                for f in pt.get("formatos", [])]
    passos = "".join(f"<li>{e(t)}</li>" for t in pt.get("passos", []))
    corneteiro = por_id.get("ze-corneteiro")
    chamada = fala(corneteiro, e("Plantão extraordinário! Tem lugar na vila pra sua loja. Chama no WhatsApp que a gente conversa."),
                   f'{e(corneteiro["nome"])}, locutor da Rádio Buraco Fundo FM') if corneteiro else ""
    corpo = f"""
<section class="abertura serrilha-baixo">
 <div class="miolo">
  <h1>{e(pt['titulo'])}</h1>
  <p>{e(pt['texto'])}</p>
  <div class="botoes">
   <a class="botao" href="{e(wa(pt['mensagem']))}" target="_blank" rel="noopener">{ICONE['whats']}Quero anunciar</a>
   <a class="botao papel" href="#numeros">Ver os números</a>
  </div>
 </div>
</section>

<section class="faixa" id="numeros" aria-labelledby="t-numeros">
 <div class="miolo">
  <h2 id="t-numeros">Quem assiste</h2>
  <ul class="placar">{placar_html}</ul>
  <p class="sub">{e(pt.get('publico', ''))}</p>
  <p class="nota">Números do YouTube atualizados em {e(fmt_mes(cat.get('atualizado_em', '')[:10]))}; Instagram e Facebook em {e(rn.get('data', ''))}.</p>
 </div>
</section>

<section aria-label="Sua loja na vila">
 <div class="panorama">
  <img src="img/vila-rua.webp" alt="Rua do Vilarejo Buraco Fundo com casas coloridas e a igreja ao fundo" width="1600" height="900" loading="lazy">
  <div class="placa"><p>Sua loja aqui?</p></div>
 </div>
</section>

<section class="faixa clara" aria-labelledby="t-formatos">
 <div class="miolo">
  <div class="cabeca-faixa"><h2 id="t-formatos">Jeitos de aparecer</h2><p>Dá para combinar mais de um no mesmo mês.</p></div>
  {carrossel(formatos, "cartoes", "Formatos de patrocínio")}
 </div>
</section>

<section class="faixa" aria-labelledby="t-como">
 <div class="miolo duas">
  <div>
   <h2 id="t-como">Como funciona</h2>
   <ol class="passos">{passos}</ol>
   <div class="botoes"><a class="botao" href="{e(wa(pt['mensagem']))}" target="_blank" rel="noopener">{ICONE['whats']}Quero anunciar</a></div>
  </div>
  {chamada}
 </div>
</section>
"""
    pagina("patrocinio.html", f"Anuncie no {cfg['nome']}", pt["texto"], corpo, "index.html#contrate", imagem="img/vila-rua.webp")


def sitemap():
    base = cfg.get("endereco_site", "").rstrip("/")
    if not base:
        return
    urls = ["", "musicas.html", "vilarejo.html", "moradores.html", "patrocinio.html", "figurinhas.html"] + [f"personagens/{p['id']}.html" for p in personagens]
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"<url><loc>{base}/{u}</loc></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")
    # domínio próprio no GitHub Pages (o endereço gratuito github.io não leva CNAME)
    host = base.split("://", 1)[-1].split("/")[0]
    if not host.endswith("github.io"):
        (SITE / "CNAME").write_text(host + "\n", encoding="utf-8")


if __name__ == "__main__":
    inicio()
    pagina_musicas()
    pagina_vilarejo()
    pagina_moradores()
    fichas()
    pagina_patrocinio()
    pagina_figurinhas()
    sitemap()
    print(f"site gerado: {len(musicas)} músicas, {len(personagens)} moradores, {len(comentarios)} comentários, {len(piadas)} Piadas do Dia")
