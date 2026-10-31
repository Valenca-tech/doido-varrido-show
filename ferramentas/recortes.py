"""Recortes transparentes dos personagens (insumos/recortes/<id>.png), usados nas figurinhas.

Uso: python ferramentas/recortes.py
Vêm de duas fontes: artes da bíblia que já têm fundo transparente e a imagem 'Personagens PNG.png',
que traz vários moradores lado a lado em fundo branco (o fundo é tirado e cada um é separado pela silhueta).
"""
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
BIBLIA = RAIZ / "insumos" / "biblia" / "vilarejo"
PROMPTS = BIBLIA / "personagens" / "prompts"
SAIDA = RAIZ / "insumos" / "recortes"
Image.MAX_IMAGE_PIXELS = None

TRANSPARENTES = {
    "silfarnney-valenca": next((PROMPTS / "silfarnney_doido_varrido").glob("*(5).png")),
    "verinha-valenca": PROMPTS / "silfarnney_doido_varrido" / "Verinha- Esposa Silfarnney.png",
    "raimunda": PROMPTS / "Zé Pavio “Merda Viva” Casa e Esposa" / "Raimunda.png",
    "ze-encostado": PROMPTS / "Tonho Encostado - O Preguiçoso" / "Zé Tonho Encostado Caricatura.png",
    "ze-conversa": PROMPTS / "Nego Fábim da Conversa - O MENTIROSO 2.png",
    "ze-promessa": PROMPTS / "Seu Lídio Promessa - POLÍTICO 2.png",
    "ze-fiado": PROMPTS / "ZÉ FIADO — DONO DO MERCADINHO DE BURACO FUNDO" / "Zé Fiado transparente.png",
    "ze-reza-forte": PROMPTS / "Zé Reza Forte — Tenha fé, meu filho" / "Zé Reza Forte.png",
    "professora-marinalva": PROMPTS / "Zézinho da Mochila e PROFESSORA DONA MARINALVA" / "PROFESSORA DONA MARINALVA.png",
    "auristela-do-sol": PROMPTS / "Personagens Série cantada" / "4.png",
    "ze-massilon": PROMPTS / "Personagens Série cantada" / "5.png",
    "jandira-raioforte": PROMPTS / "Personagens Série cantada" / "6.png",
    "mirela-da-lua": PROMPTS / "Personagens Série cantada" / "7.png",
}
# posição de cada morador no 'Personagens PNG.png', na ordem de leitura (linha de cima, depois a de baixo)
GRUPO = ["ze-pavio", "ze-tonhim-cafe-doce", "ze-fora-de-prumo", "ze-mochila", "lourinha-de-buraco-fundo", None,
         "ze-coco", "coloral", None, None, "ze-bola-murcha", "ze-corneteiro", "ze-pega-ligeiro", None, "ze-piloia", "ze-barrao"]


def aparar(im):
    return im.crop(im.getchannel("A").getbbox())


def separar_grupo(arq):
    im = Image.open(arq).convert("RGB")
    w, h = im.size
    tmp = im.copy()
    mag = (255, 0, 254)
    for x in range(0, w, 50):
        for y in (0, h - 1):
            if tmp.getpixel((x, y)) != mag:
                ImageDraw.floodfill(tmp, (x, y), mag, thresh=40)
    for y in range(0, h, 50):
        for x in (0, w - 1):
            if tmp.getpixel((x, y)) != mag:
                ImageDraw.floodfill(tmp, (x, y), mag, thresh=40)
    r, g, b = tmp.split()
    fundo = ImageChops.multiply(ImageChops.multiply(r.point(lambda v: 255 if v == 255 else 0), g.point(lambda v: 255 if v == 0 else 0)),
                                b.point(lambda v: 255 if v == 254 else 0)).filter(ImageFilter.MaxFilter(3))
    rgba = im.convert("RGBA")
    rgba.putalpha(ImageOps.invert(fundo))
    # manchas conectadas numa versão reduzida; cada uma vira a máscara de um personagem
    esc = 8
    peq = rgba.getchannel("A").resize((w // esc, h // esc)).point(lambda v: 255 if v > 128 else 0)
    pw, ph = peq.size
    px = peq.load()
    visto, manchas = set(), []
    for y in range(ph):
        for x in range(pw):
            if px[x, y] and (x, y) not in visto:
                pilha, pts = [(x, y)], []
                visto.add((x, y))
                while pilha:
                    cx, cy = pilha.pop()
                    pts.append((cx, cy))
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if 0 <= nx < pw and 0 <= ny < ph and px[nx, ny] and (nx, ny) not in visto:
                            visto.add((nx, ny))
                            pilha.append((nx, ny))
                if len(pts) > 300:
                    manchas.append(pts)
    manchas.sort(key=lambda m: (min(p[1] for p in m) * esc // 1200, min(p[0] for p in m)))
    for pts in manchas:
        m = Image.new("L", (pw, ph), 0)
        mp = m.load()
        for x, y in pts:
            mp[x, y] = 255
        m = m.filter(ImageFilter.MaxFilter(3)).resize((w, h), Image.NEAREST)
        p = rgba.copy()
        p.putalpha(ImageChops.multiply(p.getchannel("A"), m))
        yield aparar(p)


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    for ident, arq in TRANSPARENTES.items():
        aparar(Image.open(arq).convert("RGBA")).save(SAIDA / f"{ident}.png")
        print("transparente:", ident)
    for ident, im in zip(GRUPO, separar_grupo(BIBLIA / "personagens" / "Personagens PNG.png")):
        if ident and not (SAIDA / f"{ident}.png").exists():
            im.save(SAIDA / f"{ident}.png")
            print("do grupo:", ident)


if __name__ == "__main__":
    main()
