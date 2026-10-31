// Desenha as figurinhas do WhatsApp a partir de dados/figurinhas.json e dos recortes em insumos/recortes.
// Uso: node ferramentas/figurinhas.mjs
// Saída em site/figurinhas/: NN-<personagem>.webp (512x512, fundo transparente, até 100 KB) e bandeja.png (96x96).
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), "..");
const SAIDA = join(RAIZ, "site", "figurinhas");
const dados = JSON.parse(readFileSync(join(RAIZ, "dados", "figurinhas.json"), "utf8"));
const EDGE = ["C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Microsoft/Edge/Application/msedge.exe"].find(existsSync);
const LADO = 512, LIMITE = 100 * 1024;
const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
// tamanho da letra pelo comprimento da frase e pela palavra mais longa (a Ultra é larga: ~0,8 em por letra)
const tamanho = (t) => {
  const pelaFrase = t.length <= 10 ? 84 : t.length <= 18 ? 62 : t.length <= 26 ? 52 : 45;
  const maior = Math.max(...t.split(/\s+/).map((p) => p.length));
  return Math.min(pelaFrase, Math.floor(450 / (maior * 0.8)));
};

const figs = dados.figurinhas.map((f, i) => ({ ...f, nome: `${String(i + 1).padStart(2, "0")}-${f.personagem}` }));
const html = `<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Ultra&display=block">
<style>
  body { margin: 0; background: transparent; }
  .fig { position: relative; width: ${LADO}px; height: ${LADO}px; margin-bottom: 20px; }
  /* contorno branco de adesivo em volta do personagem e da frase */
  .corte { position: absolute; inset: 18px;
    filter: drop-shadow(5px 0 0 #fff) drop-shadow(-5px 0 0 #fff) drop-shadow(0 5px 0 #fff) drop-shadow(0 -5px 0 #fff)
            drop-shadow(0 0 1.5px rgba(34, 20, 11, .55)); }
  .pessoa { position: absolute; inset: 0 0 64px; display: flex; align-items: flex-end; justify-content: center; }
  .pessoa img { max-width: 100%; max-height: 100%; }
  .frase { position: absolute; left: 0; right: 0; bottom: 0; margin: 0; text-align: center; transform: rotate(-3deg);
    font-family: "Ultra", serif; line-height: 1.02; color: #FBC02D; -webkit-text-stroke: 10px #22140B; paint-order: stroke fill; }
</style></head><body>
${figs.map((f) => `<div class="fig" id="f${f.nome}"><div class="corte">
  <div class="pessoa"><img src="${pathToFileURL(join(RAIZ, "insumos", "recortes", `${f.personagem}.png`)).href}"></div>
  <p class="frase" style="font-size:${tamanho(f.texto)}px;-webkit-text-stroke-width:${Math.round(tamanho(f.texto) * 0.17)}px">${esc(f.texto)}</p></div></div>`).join("\n")}
</body></html>`;

const espera = (ms) => new Promise((ok) => setTimeout(ok, ms));
const perfil = join(tmpdir(), `figurinhas-edge-${Date.now()}`);
mkdirSync(perfil, { recursive: true });
const pagina = join(perfil, "figurinhas.html");
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
  const avaliar = async (expression) => {
    const r = await cdp("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
    return r.result.value;
  };

  await cdp("Page.enable");
  await cdp("Emulation.setDeviceMetricsOverride", { width: LADO, height: 900, deviceScaleFactor: 1, mobile: false });
  await cdp("Emulation.setDefaultBackgroundColorOverride", { color: { r: 0, g: 0, b: 0, a: 0 } });
  const carregou = evento("Page.loadEventFired");
  await cdp("Page.navigate", { url: pathToFileURL(pagina).href });
  await carregou;
  const ok = await avaliar(`(async () => { await document.fonts.ready; await document.fonts.load('40px Ultra');
    return [...document.images].every((i) => i.complete && i.naturalWidth > 0) && document.fonts.check('40px Ultra'); })()`);
  if (!ok) throw new Error("fonte Ultra ou algum recorte não carregou (precisa de internet para a fonte)");

  rmSync(SAIDA, { recursive: true, force: true });
  mkdirSync(SAIDA, { recursive: true });
  // PNG da tela -> WebP pelo próprio navegador, baixando a qualidade até caber em 100 KB
  const paraWebp = (png, lado, limite) => avaliar(`(async () => {
    const img = new Image(); img.src = "data:image/png;base64,${png}"; await img.decode();
    const c = document.createElement("canvas"); c.width = c.height = ${lado};
    c.getContext("2d").drawImage(img, 0, 0, ${lado}, ${lado});
    for (let q = 0.92; q >= 0.3; q -= 0.06) {
      const url = c.toDataURL("image/webp", q);
      const b64 = url.split(",")[1];
      if (b64.length * 3 / 4 <= ${limite}) return { b64, q: +q.toFixed(2) };
    }
    return null; })()`);

  for (const f of figs) {
    const caixa = await avaliar(`(() => { const r = document.getElementById("f${f.nome}").getBoundingClientRect(); return { x: r.x, y: r.y + scrollY }; })()`);
    const { data } = await cdp("Page.captureScreenshot", { format: "png", captureBeyondViewport: true,
      clip: { x: caixa.x, y: caixa.y, width: LADO, height: LADO, scale: 1 } });
    const webp = await paraWebp(data, LADO, LIMITE);
    if (!webp) throw new Error(`${f.nome} não coube em 100 KB`);
    writeFileSync(join(SAIDA, `${f.nome}.webp`), Buffer.from(webp.b64, "base64"));
    console.log(`${f.nome}.webp  ${Math.round(webp.b64.length * 0.75 / 1024)} KB (qualidade ${webp.q})`);
  }

  // ícone da bandeja (aparece na lista de pacotes do WhatsApp): 96x96 PNG
  const logo = readFileSync(join(RAIZ, "site", "img", "logo-doido-varrido.webp")).toString("base64");
  const bandeja = await avaliar(`(async () => {
    const img = new Image(); img.src = "data:image/webp;base64,${logo}"; await img.decode();
    const c = document.createElement("canvas"); c.width = c.height = 96;
    const s = Math.min(96 / img.width, 96 / img.height);
    c.getContext("2d").drawImage(img, (96 - img.width * s) / 2, (96 - img.height * s) / 2, img.width * s, img.height * s);
    return c.toDataURL("image/png").split(",")[1]; })()`);
  writeFileSync(join(SAIDA, "bandeja.png"), Buffer.from(bandeja, "base64"));
  console.log(`${figs.length} figurinhas e bandeja.png em ${SAIDA}`);
  ws.close();
} finally {
  edge.kill();
  await espera(500);
  try { rmSync(perfil, { recursive: true, force: true }); } catch { /* o Edge às vezes ainda segura o perfil */ }
}
