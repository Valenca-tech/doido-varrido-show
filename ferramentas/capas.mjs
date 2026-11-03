// Capas dos álbuns para o streaming (3000x3000 JPG), a partir de streaming/albuns.json (python ferramentas/streaming.py).
// Uso: node ferramentas/capas.mjs
// A capa só leva o título do álbum e o nome do artista: as plataformas recusam link, @, preço ou outros textos.
// Fundo e raios são desenhados em CSS (nítidos em qualquer tamanho); o personagem vem de insumos/recortes.
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), "..");
const SAIDA = join(RAIZ, "streaming", "capas");
const albuns = JSON.parse(readFileSync(join(RAIZ, "streaming", "albuns.json"), "utf8"));
const EDGE = ["C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Microsoft/Edge/Application/msedge.exe"].find(existsSync);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const arq = (...p) => pathToFileURL(join(RAIZ, ...p)).href;
const BANDEIRAS = `url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='176' height='46'><path d='M0 5Q44 13 88 5T176 5' fill='none' stroke='%2322140B' stroke-width='2'/><g stroke='%2322140B' stroke-width='2' stroke-linejoin='round'><path d='M7 7h30v30l-15-8-15 8z' fill='%23F57C00'/><path d='M51 9h30v30l-15-8-15 8z' fill='%232E7D32'/><path d='M95 7h30v30l-15-8-15 8z' fill='%2329B6F6'/><path d='M139 9h30v30l-15-8-15 8z' fill='%23FBC02D'/></g></svg>")`;

// título em até duas linhas: a parte depois da vírgula ("Vol. 1") ou a última palavra vai para baixo, em laranja
function linhas(t) {
  if (t.includes(",")) { const [a, b] = t.split(/,\s*/); return [a, b]; }
  const p = t.split(" ");
  const meio = Math.ceil(p.length / 2);
  return [p.slice(0, meio).join(" "), p.slice(meio).join(" ")];
}

const capa = (a) => {
  const [l1, l2] = linhas(a.titulo);
  const tam = Math.max(l1.length, l2.length) > 16 ? 74 : Math.max(l1.length, l2.length) > 12 ? 86 : 98;
  return `<section class="capa" id="c-${a.id}" style="--cor:${a.cor}">
  <div class="raios"></div><div class="bandeiras"></div>
  <div class="placa"><h1 style="font-size:${tam}px"><span>${esc(l1)}</span><span class="destaque">${esc(l2)}</span></h1></div>
  <img class="figura" src="${arq("insumos", "recortes", `${a.personagem}.png`)}">
  <img class="logo" src="${arq("site", "img", "logo-doido-varrido.webp")}" alt="O Doido Varrido Show">
</section>`;
};

const html = `<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Ultra&display=block">
<style>
  body { margin: 0; }
  .capa { position: relative; width: 1000px; height: 1000px; overflow: hidden; margin-bottom: 20px;
    background: radial-gradient(circle at 50% 70%, color-mix(in srgb, var(--cor) 55%, #FFE14D) 0%, var(--cor) 62%, color-mix(in srgb, var(--cor) 70%, #22140B) 100%); }
  .raios { position: absolute; left: 50%; top: 70%; width: 2400px; height: 2400px; margin: -1200px 0 0 -1200px;
    background: repeating-conic-gradient(rgba(255, 236, 140, .30) 0 7deg, rgba(255, 236, 140, 0) 7deg 14deg);
    -webkit-mask: radial-gradient(circle, #000 12%, transparent 58%); }
  .bandeiras { position: absolute; left: 0; right: 0; top: 0; height: 84px; background: ${BANDEIRAS} repeat-x 0 0 / 321px 84px; }
  .placa { position: absolute; left: 70px; right: 70px; top: 110px; transform: rotate(-2.5deg); padding: 26px 30px 32px;
    border: 9px solid #3A1E0B; border-radius: 22px; z-index: 3;
    background:
      radial-gradient(circle at 24px 24px, #3A1E0B 8px, transparent 9px), radial-gradient(circle at calc(100% - 24px) 24px, #3A1E0B 8px, transparent 9px),
      radial-gradient(circle at 24px calc(100% - 24px), #3A1E0B 8px, transparent 9px), radial-gradient(circle at calc(100% - 24px) calc(100% - 24px), #3A1E0B 8px, transparent 9px),
      repeating-linear-gradient(176deg, rgba(0, 0, 0, .07) 0 3px, transparent 3px 22px), linear-gradient(180deg, #A8692E, #7A4519);
    box-shadow: 0 16px 0 rgba(34, 20, 11, .5); }
  .placa h1 { margin: 0; text-align: center; font-family: "Ultra", serif; font-weight: 400; }
  .placa span { display: block; line-height: 1; color: #FFE14D; -webkit-text-stroke: 14px #3A1E0B; paint-order: stroke fill; text-shadow: 0 9px 0 #3A1E0B; }
  .placa span.destaque { color: #FF7A1A; }
  .figura { position: absolute; left: 50%; bottom: 0; transform: translateX(-38%); height: 600px; max-width: 760px; object-fit: contain; object-position: bottom; z-index: 2;
    filter: drop-shadow(7px 0 0 #fff) drop-shadow(-7px 0 0 #fff) drop-shadow(0 7px 0 #fff) drop-shadow(0 -7px 0 #fff) drop-shadow(0 18px 16px rgba(0, 0, 0, .45)); }
  .logo { position: absolute; left: 36px; bottom: 30px; width: 270px; z-index: 4; filter: drop-shadow(0 8px 0 rgba(34, 20, 11, .45)); }
</style></head><body>
${albuns.map(capa).join("\n")}
</body></html>`;

const espera = (ms) => new Promise((ok) => setTimeout(ok, ms));
const perfil = join(tmpdir(), `capas-edge-${Date.now()}`);
mkdirSync(perfil, { recursive: true });
const pagina = join(perfil, "capas.html");
writeFileSync(pagina, html);
const porta = 9300 + Math.floor(Math.random() * 400);
const edge = spawn(EDGE, ["--headless=new", `--remote-debugging-port=${porta}`, `--user-data-dir=${perfil}`,
  "--allow-file-access-from-files", "--hide-scrollbars", "--no-first-run", "about:blank"], { stdio: "ignore" });

try {
  let alvo;
  for (let i = 0; i < 75 && !alvo; i++) {
    try { alvo = (await (await fetch(`http://127.0.0.1:${porta}/json/list`)).json()).find((t) => t.type === "page"); } catch { /* abrindo */ }
    if (!alvo) await espera(200);
  }
  if (!alvo) throw new Error("o Edge não abriu o modo de depuração");
  const ws = new WebSocket(alvo.webSocketDebuggerUrl);
  await new Promise((ok, erro) => { ws.onopen = ok; ws.onerror = erro; });
  let seq = 0;
  const pendentes = new Map();
  const ouvintes = new Set();
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.id && pendentes.has(d.id)) {
      const { ok, erro } = pendentes.get(d.id);
      pendentes.delete(d.id);
      d.error ? erro(new Error(d.error.message)) : ok(d.result);
    } else ouvintes.forEach((f) => f(d));
  };
  ws.onclose = () => pendentes.forEach(({ erro }) => erro(new Error("a conexão com o Edge caiu")));
  const cdp = (method, params = {}) => new Promise((ok, erro) => {
    const id = ++seq;
    pendentes.set(id, { ok, erro });
    ws.send(JSON.stringify({ id, method, params }));
  });
  const evento = (nome) => new Promise((ok) => {
    const f = (d) => { if (d.method === nome) { ouvintes.delete(f); ok(d.params); } };
    ouvintes.add(f);
  });
  const avaliar = async (expression) =>
    (await cdp("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true })).result.value;

  await cdp("Page.enable");
  // 1000 px de layout com escala 3 = 3000x3000 de verdade, com texto nítido
  await cdp("Emulation.setDeviceMetricsOverride", { width: 1000, height: 1000, deviceScaleFactor: 3, mobile: false });
  const carregou = evento("Page.loadEventFired");
  await cdp("Page.navigate", { url: pathToFileURL(pagina).href });
  await carregou;
  const ok = await avaliar(`(async () => { await document.fonts.ready; await document.fonts.load('40px Ultra');
    return { faltando: [...document.images].filter((i) => !i.complete || !i.naturalWidth).map((i) => i.src.split("/").pop()), fonte: document.fonts.check('40px Ultra') }; })()`);
  if (ok.faltando.length || !ok.fonte) throw new Error(`não carregou: ${ok.faltando.join(", ")} ${ok.fonte ? "" : "fonte Ultra"}`);
  await espera(300);

  mkdirSync(SAIDA, { recursive: true });
  for (const a of albuns) {
    const c = await avaliar(`(() => { const r = document.getElementById("c-${a.id}").getBoundingClientRect(); return { x: r.x, y: r.y + scrollY }; })()`);
    const { data } = await cdp("Page.captureScreenshot", { format: "jpeg", quality: 92, captureBeyondViewport: true,
      clip: { x: c.x, y: c.y, width: 1000, height: 1000, scale: 1 } });
    writeFileSync(join(SAIDA, `${a.id}.jpg`), Buffer.from(data, "base64"));
    console.log(`${a.id}.jpg`);
  }
  ws.close();
} finally {
  edge.kill();
  await espera(500);
  try { rmSync(perfil, { recursive: true, force: true }); } catch { /* o Edge às vezes ainda segura o perfil */ }
}
