"""Prepara o envio das músicas para as plataformas de streaming.

Uso: python ferramentas/streaming.py
Agrupa o catálogo do canal (dados/videos.json) em álbuns por estilo e grava em streaming/:
  fichas-streaming.xlsx  uma linha por faixa, com o que a distribuidora pede e colunas para preencher
  albuns.json           álbuns e faixas, lido por ferramentas/capas.mjs para desenhar as capas
A pasta streaming/ não vai para o repositório.
"""
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "streaming"
INTERPRETE = "O Doido Varrido Show"
COMPOSITOR = "Silfarnney Asevedo Valença"

# álbum: (título, famílias do catálogo, personagem da capa, cor da capa)
ALBUNS = [
    ("forro-1", "Forró do Doido, Vol. 1", ["Forró"], "silfarnney-valenca", "#F57C00"),
    ("forro-2", "Forró do Doido, Vol. 2", ["Forró"], "ze-coco", "#2E7D32"),
    ("forro-3", "Forró do Doido, Vol. 3", ["Forró"], "ze-tonhim-cafe-doce", "#1F6FE0"),
    ("emboladas", "Emboladas do Doido", ["Embolada"], "coloral", "#D62828"),
    ("vaquejada", "Forró de Vaquejada", ["Vaquejada"], "ze-massilon", "#795548"),
    ("romanticas", "Românticas do Doido", ["Românticas"], "auristela-do-sol", "#B8327F"),
    ("cordel-pisadinha", "Cordel e Pisadinha do Doido", ["Cordel", "Pisadinha"], "ze-conversa", "#6A3FA0"),
    ("piadas", "Piadas do Vilarejo Buraco Fundo", ["Piadas do Dia"], "ze-pavio", "#29B6F6"),
]
FORRO_POR_VOLUME = 16


def main():
    cat = json.loads((RAIZ / "dados" / "videos.json").read_text(encoding="utf-8"))
    videos = [v for v in cat["videos"] if not v.get("oculto") and not v.get("repetido")]
    forro = sorted([v for v in videos if v["familia"] == "Forró"], key=lambda v: -v["views"])
    albuns = []
    for ident, titulo, familias, personagem, cor in ALBUNS:
        if ident.startswith("forro-"):
            n = int(ident[-1]) - 1
            faixas = forro[n * FORRO_POR_VOLUME:(n + 1) * FORRO_POR_VOLUME]
        else:
            faixas = sorted([v for v in videos if v["familia"] in familias], key=lambda v: -v["views"])
        if faixas:
            albuns.append({"id": ident, "titulo": titulo, "personagem": personagem, "cor": cor,
                           "faixas": [{"titulo": v["titulo"], "genero": v.get("genero") or v["familia"], "duracao": v.get("duracao", ""),
                                       "views": v["views"], "publicado": v.get("publicado", ""), "id": v["id"]} for v in faixas]})

    SAIDA.mkdir(exist_ok=True)
    (SAIDA / "albuns.json").write_text(json.dumps(albuns, ensure_ascii=False, indent=1), encoding="utf-8")

    wb = Workbook()
    cab = Font(bold=True, color="FFFFFF")
    fundo = PatternFill("solid", fgColor="22140B")
    preencher = PatternFill("solid", fgColor="FFF3C4")

    ws = wb.active
    ws.title = "Faixas"
    colunas = ["Álbum", "Faixa", "Título", "Estilo", "Duração", "Visualizações no YouTube", "Lançado no YouTube", "Link do YouTube",
               "Intérprete", "Compositor (letra e música)", "Ferramenta usada na gravação", "Uso de IA a declarar",
               "Arquivo de áudio original", "Letra com palavrão? (explícita)"]
    ws.append(colunas)
    for a in albuns:
        for i, f in enumerate(a["faixas"], 1):
            ws.append([a["titulo"], i, f["titulo"], f["genero"], f["duracao"], f["views"], f["publicado"],
                       f"https://www.youtube.com/watch?v={f['id']}", INTERPRETE, COMPOSITOR, "", "", "", ""])
    for c in ws[1]:
        c.font, c.fill, c.alignment = cab, fundo, Alignment(wrap_text=True, vertical="center")
    for linha in ws.iter_rows(min_row=2, min_col=11, max_col=14):
        for c in linha:
            c.fill = preencher
    larguras = [30, 7, 42, 18, 9, 13, 13, 44, 20, 28, 24, 22, 30, 16]
    for i, w in enumerate(larguras, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 34
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = ws.dimensions

    wa = wb.create_sheet("Álbuns")
    wa.append(["Álbum", "Faixas", "Duração total", "Visualizações somadas", "Capa"])
    for a in albuns:
        seg = 0
        for f in a["faixas"]:
            if f["duracao"]:
                partes = [int(x) for x in f["duracao"].split(":")]
                seg += partes[-1] + 60 * partes[-2] + (3600 * partes[0] if len(partes) == 3 else 0)
        wa.append([a["titulo"], len(a["faixas"]), f"{seg // 60} min", sum(f["views"] for f in a["faixas"]), f"capas/{a['id']}.jpg"])
    for c in wa[1]:
        c.font, c.fill = cab, fundo
    for i, w in enumerate([34, 8, 14, 22, 26], 1):
        wa.column_dimensions[get_column_letter(i)].width = w

    wc = wb.create_sheet("Antes de enviar")
    itens = [
        "Confirmar em qual ferramenta cada música foi gravada (por exemplo, Suno) e em qual plano: gratuito ou pago.",
        "No Suno, só músicas feitas com plano pago têm direito de uso comercial; as do plano gratuito não podem ir para o streaming.",
        "Separar o áudio original de cada faixa (o arquivo baixado da ferramenta, não o som do vídeo do YouTube).",
        "Preencher a coluna 'Uso de IA a declarar': a distribuidora pergunta se a voz, a música ou a letra usaram IA.",
        "Marcar as faixas com palavrão como explícitas (duplo sentido sem palavrão não é explícito).",
        "Usar a foto real do Silfarnney no perfil de artista, para o Spotify não confundir com artista criado por IA.",
        "Não ativar o 'Content ID' do YouTube na distribuidora para estas músicas, ou liberar o próprio canal, para não haver reclamação nos vídeos dele.",
    ]
    wc.append(["Antes de enviar para a distribuidora"])
    wc["A1"].font = Font(bold=True, size=13)
    for t in itens:
        wc.append([t])
    wc.column_dimensions["A"].width = 120

    wb.save(SAIDA / "fichas-streaming.xlsx")
    total = sum(len(a["faixas"]) for a in albuns)
    for a in albuns:
        print(f"{a['titulo']:34} {len(a['faixas']):3} faixas")
    print(f"{total} faixas em {len(albuns)} álbuns; planilha em {SAIDA / 'fichas-streaming.xlsx'}")


if __name__ == "__main__":
    main()
