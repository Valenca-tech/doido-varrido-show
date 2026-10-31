# Site do O Doido Varrido Show

Site estático (HTML, CSS e um pouco de JavaScript, sem servidor) gerado por script Python a partir dos dados da pasta `dados/`. O que vai para a internet é só a pasta `site/`.

## Pastas

- `insumos/biblia/` arquivos originais da bíblia do Vilarejo Buraco Fundo (não publicar).
- `dados/config.json` links das redes, WhatsApp, PIX, serviços do "Contrate", bloco "em breve", frases do letreiro "Plantão extraordinário" (`plantao`), falas dos balões que chamam para as redes (`chamadas_redes`), o personagem flutuante (`pregao`) e a fala do Apoie (`apoie`). Campo vazio esconde o botão; `"ativo": false` esconde o serviço.
- `dados/universo.json` vila, lendas, Lei dos Zés e os personagens (nome, bordão, descrição, relações).
- `dados/videos.json` catálogo do canal, gerado pelo atualizador. Correções de título ou gênero vão em `dados/videos_ajustes.json`.
- `dados/comentarios.json` balões de avaliação: comentários reais do YouTube escolhidos à mão, sem o nome de quem comentou. `dados/comentarios_candidatos.json` traz os nomes e serve só para consulta (não publicar).
- `dados/teste.json` perguntas do teste "Quem é você em Buraco Fundo?"; cada resposta soma um ponto para um morador.
- `ferramentas/` scripts de imagens, vídeos, comentários e da prévia para celular.
- `site/` resultado final (páginas, `css/`, `js/`, `img/`).

## Como atualizar

```
python ferramentas/atualizar_videos.py   # lê o canal do YouTube (títulos, views)
python ferramentas/preparar_imagens.py   # só quando trocar ou acrescentar arte
python ferramentas/buscar_comentarios.py # traz comentários novos para escolher (opcional)
python gerar.py                          # refaz as páginas
```

Para trocar o retrato de um morador, coloque a imagem em `insumos/retratos/<id>.png` (o id é o nome do arquivo em `site/personagens/`) e rode as imagens e o gerar de novo.

## Figurinhas e artes de divulgação

```
python ferramentas/recortes.py      # recortes transparentes dos personagens (insumos/recortes)
node ferramentas/figurinhas.mjs     # figurinhas do WhatsApp em site/figurinhas (frases em dados/figurinhas.json)
node ferramentas/artes.mjs          # stories e posts em artes/ (textos em dados/artes.json)
python gerar.py
```

As figurinhas saem em WebP 512x512 com fundo transparente e até 100 KB, mais `bandeja.png` (96x96), que é o que os aplicativos de pacote de figurinhas pedem. Quando o pacote estiver publicado num desses aplicativos, ponha o link em `link_pacote` no `dados/figurinhas.json` e a página de figurinhas ganha o botão "Adicionar o pacote no WhatsApp". As duas ferramentas em Node precisam de internet para as fontes.

## Ver no computador

```
python -m http.server 8770 --directory site
```

e abra http://localhost:8770.

## Mandar a prévia para alguém avaliar

Com o site aberto em http://localhost:8770, rode

```
node ferramentas/previa_celular.mjs
```

Ele usa o Edge para tirar as telas como num celular e grava em `previa/` as imagens numeradas e `Previa-site-Doido-Varrido.pdf`, prontos para o WhatsApp. Nada vai para a internet.

## Publicação

O site é publicado pelo GitHub Pages. A cada envio para o repositório e todo dia de manhã, a rotina em `.github/workflows/publicar.yml` atualiza o catálogo de vídeos, refaz as páginas e publica a pasta `site/`. Ficam fora do repositório (`.gitignore`) a pasta `insumos/` (bíblia original, fotos e notas internas), `previa/`, `artes/` e os comentários com nome de autor.
