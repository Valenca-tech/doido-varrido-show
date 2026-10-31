"""Busca os comentários mais curtidos dos vídeos mais vistos do canal, para escolher os balões de avaliação.

Uso: python ferramentas/buscar_comentarios.py [quantos_videos]   (padrão 12)
Grava dados/comentarios_candidatos.json (com o nome de quem comentou, só para consulta; não vai para o site).
Os escolhidos vão à mão para dados/comentarios.json, sem o nome do autor.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from atualizar_videos import baixar  # mesmo cabeçalho e cookies da leitura do canal

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "dados"


def achar(obj, chave):
    """Todos os valores de uma chave em qualquer profundidade do JSON."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == chave:
                yield v
            yield from achar(v, chave)
    elif isinstance(obj, list):
        for v in obj:
            yield from achar(v, chave)


def comentarios(vid):
    html = baixar(f"https://www.youtube.com/watch?v={vid}&hl=pt&gl=BR")
    inicial = json.loads(re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S).group(1))
    versao = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', html).group(1)
    secao = next(s for s in achar(inicial, "itemSectionRenderer") if s.get("sectionIdentifier") == "comment-item-section")
    token = next(achar(secao, "continuationCommand"))["token"]
    corpo = json.dumps({"context": {"client": {"clientName": "WEB", "clientVersion": versao, "hl": "pt", "gl": "BR"}},
                        "continuation": token}).encode()
    resp = json.loads(baixar("https://www.youtube.com/youtubei/v1/next?prettyPrint=false", corpo))
    for c in achar(resp, "commentEntityPayload"):
        prop, autor, barra = c.get("properties", {}), c.get("author", {}), c.get("toolbar", {})
        yield {
            "texto": prop.get("content", {}).get("content", ""),
            "publicado": prop.get("publishedTime", ""),
            "autor": autor.get("displayName", ""),
            "do_canal": bool(autor.get("isCreator")),
            "curtidas": barra.get("likeCountNotliked", "0"),
            "respostas": barra.get("replyCount", "0"),
        }


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    cat = json.loads((DADOS / "videos.json").read_text(encoding="utf-8"))
    videos = sorted([v for v in cat["videos"] if not v.get("repetido")], key=lambda v: -v["views"])[:n]
    todos = []
    for v in videos:
        try:
            lista = [dict(c, video_id=v["id"], video_titulo=v["titulo"]) for c in comentarios(v["id"])]
        except Exception as e:
            print(f"{v['titulo']}: falhou ({e})")
            continue
        todos += lista
        print(f"{v['titulo']}: {len(lista)} comentários")
    (DADOS / "comentarios_candidatos.json").write_text(json.dumps(todos, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(todos), "candidatos em dados/comentarios_candidatos.json")


if __name__ == "__main__":
    main()
