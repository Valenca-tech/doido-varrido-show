"""Converte as artes da bíblia (insumos/) em imagens leves para o site (site/img/).

Uso: python ferramentas/preparar_imagens.py
Rode de novo sempre que trocar ou acrescentar uma arte. Os retratos dos personagens vêm do
'Fotos Personagens Buraco Fundo.docx' (uma imagem antes de cada nome) e são salvos com o id
do personagem; para trocar o retrato de alguém, ponha um arquivo em insumos/retratos/<id>.png
(ou .jpg) que ele tem prioridade sobre o do docx.
"""
import io
import re
import unicodedata
from pathlib import Path

from docx import Document
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
BIBLIA = RAIZ / "insumos" / "biblia" / "vilarejo"
TROCAS = RAIZ / "insumos" / "retratos"
SAIDA = RAIZ / "site" / "img"
Image.MAX_IMAGE_PIXELS = None

# arte de origem -> (nome no site, largura máxima, recorte opcional (x0, y0, x1, y1) em fração)
ARTES = {
    "Logo Doido Varrido Show.png": ("logo-doido-varrido", 640, (0.1, 0.0, 0.9, 0.62)),
    "logo_buraco_fundo.png": ("logo-buraco-fundo", 720, None),
    "Bandeira do Vilarejo Buraco Fundo.png": ("bandeira-buraco-fundo", 960, None),
    "pano_de_fundo_nova_serie_buraco_fundo.png": ("vila-panorama", 1920, None),
    "Vilarejo Buraco Fundo.png": ("vila-rua", 1600, None),
    "Post com todos os personagens.png": ("povo-de-buraco-fundo", 1600, None),
    "banner_piadas_vilarejo_buraco_fundo_silfarnney_refeito.png": ("banner-piadas", 1600, None),
    "thumbnail-piadas-oficiais-v1-corrigida-1920x1080.png": ("piadas-oficiais", 1280, None),
    "Imagem do ChatGPT 13 de out. de 2026, 22_05_07.png": ("placa-bem-vindo", 800, None),
    "personagens/prompts/ZÉ FIADO — DONO DO MERCADINHO DE BURACO FUNDO/Zé Fiado transparente.png": ("recorte-ze-fiado", 560, None),
}
SEM_FUNDO = {"logo-buraco-fundo"}  # arte com fundo branco que precisa ficar transparente

# retratos alternativos da pasta de prompts, usados no lugar do docx (recortes da série Cantadas);
# recorte opcional em fração da imagem
PROMPTS = BIBLIA / "personagens" / "prompts"
ALTERNATIVOS = {
    "auristela-do-sol": (PROMPTS / "Personagens Série cantada" / "4.png", None),
    "ze-massilon": (PROMPTS / "Personagens Série cantada" / "5.png", None),
    "jandira-raioforte": (PROMPTS / "Personagens Série cantada" / "6.png", None),
    "mirela-da-lua": (PROMPTS / "Personagens Série cantada" / "7.png", None),
}


def slug(t):
    t = unicodedata.normalize("NFKD", t.split("—")[0].split("(")[0]).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def tirar_fundo_branco(im, tol=28):
    """Deixa transparente o branco ligado às bordas (não mexe no branco de dentro do desenho)."""
    im = im.convert("RGBA")
    tmp = im.convert("RGB")
    for canto in [(0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)]:
        if tmp.getpixel(canto) != (255, 0, 254):
            ImageDraw.floodfill(tmp, canto, (255, 0, 254), thresh=tol)
    r, g, b = tmp.split()
    # fundo = pixel exatamente (255, 0, 254), cor que não aparece nas artes
    fundo = ImageChops.multiply(ImageChops.multiply(r.point(lambda v: 255 if v == 255 else 0),
                                                    g.point(lambda v: 255 if v == 0 else 0)),
                                b.point(lambda v: 255 if v == 254 else 0))
    fundo = fundo.filter(ImageFilter.MaxFilter(3))  # come a franja clara do contorno
    im.putalpha(ImageChops.multiply(im.getchannel("A"), ImageOps.invert(fundo)))
    return im


def salvar(im, nome, largura, pasta=SAIDA, qualidade=80):
    pasta.mkdir(parents=True, exist_ok=True)
    if im.width > largura:
        im = im.resize((largura, round(im.height * largura / im.width)), Image.LANCZOS)
    tem_alfa = im.mode == "RGBA" and im.getchannel("A").getextrema()[0] < 250
    im = im if tem_alfa else im.convert("RGB")
    destino = pasta / f"{nome}.webp"
    im.save(destino, "WEBP", quality=qualidade, method=6)
    return destino, im.size


def artes():
    for origem, (nome, largura, recorte) in ARTES.items():
        im = Image.open(BIBLIA / origem)
        if recorte:
            w, h = im.size
            im = im.crop((round(recorte[0] * w), round(recorte[1] * h), round(recorte[2] * w), round(recorte[3] * h)))
        if nome in SEM_FUNDO:
            im = tirar_fundo_branco(im)
        if nome.startswith("recorte-"):  # recorte transparente: corta a sobra em volta do desenho
            im = im.crop(im.getchannel("A").getbbox())
        destino, tam = salvar(im, nome, largura)
        print(f"{destino.name:32} {tam}")


def retratos():
    doc = Document(str(BIBLIA / "Fotos Personagens Buraco Fundo.docx"))
    ns = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"
    rid = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
    fila, achados = [], {}
    for par in doc.paragraphs[1:]:  # a primeira linha é o título do documento
        for blip in par._p.iter(ns):
            fila.append(doc.part.related_parts[blip.get(rid)].blob)
        txt = par.text.strip()
        if txt and fila:
            achados[slug(txt)] = fila[0]
            fila = []
    pasta = SAIDA / "personagens"
    for ident, dados in achados.items():
        troca = next(iter(sorted(TROCAS.glob(f"{ident}.*"))), None) if TROCAS.exists() else None
        origem = "docx"
        if troca:
            im, origem = Image.open(troca), "insumos/retratos"
        elif ident in ALTERNATIVOS:
            arq, recorte = ALTERNATIVOS[ident]
            im, origem = Image.open(arq), "alternativo"
            if recorte:
                w, h = im.size
                im = im.crop((round(recorte[0] * w), round(recorte[1] * h), round(recorte[2] * w), round(recorte[3] * h)))
        else:
            im = Image.open(io.BytesIO(dados))
        recorte_transparente = im.mode == "RGBA" and im.getchannel("A").getextrema()[0] < 250
        im = im.convert("RGBA" if recorte_transparente else "RGB")
        # todos no mesmo formato de folheto (2:3); recorte transparente ganha margem, arte cheia é aparada
        alvo = 2 / 3
        if recorte_transparente:
            caixa = im.getchannel("A").getbbox()
            im = im.crop(caixa)
            w, h = (round(im.height * alvo), im.height) if im.width / im.height < alvo else (im.width, round(im.width / alvo))
            w, h = round(w * 1.06), round(h * 1.06)
            fundo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            fundo.paste(im, ((w - im.width) // 2, h - im.height - round(h * 0.02)), im)
            im = fundo
        elif im.width / im.height > alvo:
            nova = round(im.height * alvo)
            im = im.crop(((im.width - nova) // 2, 0, (im.width + nova) // 2, im.height))
        else:
            nova = round(im.width / alvo)
            im = im.crop((0, 0, im.width, nova))
        destino, tam = salvar(im, ident, 520, pasta, 78)
        print(f"personagens/{destino.name:34} {tam}  {origem}")


if __name__ == "__main__":
    artes()
    retratos()
