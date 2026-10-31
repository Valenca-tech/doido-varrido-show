// Artes de divulgação para Instagram, Facebook e status do WhatsApp, a partir de dados/artes.json.
// Uso: node ferramentas/artes.mjs
// Saída em artes/: story-<id>.jpg (1080x1920) e feed-<id>.jpg (1080x1350), na linguagem das capas do canal:
// cena da vila ao fundo, raios de sol, título amarelo com contorno grosso numa placa de madeira, faixa azul,
// selo estourado, personagem grande e botão verde do WhatsApp.
// Precisa de internet para as fontes (Google Fonts). No story, os textos ficam longe do topo e do rodapé,
// onde o Instagram põe a barra e o campo de resposta.
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), "..");
const SAIDA = join(RAIZ, "artes");
const dados = JSON.parse(readFileSync(join(RAIZ, "dados", "artes.json"), "utf8"));
const cfg = JSON.parse(readFileSync(join(RAIZ, "dados", "config.json"), "utf8"));
const figs = JSON.parse(readFileSync(join(RAIZ, "dados", "figurinhas.json"), "utf8")).figurinhas;
const EDGE = ["C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Microsoft/Edge/Application/msedge.exe"].find(existsSync);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const arq = (...p) => pathToFileURL(join(RAIZ, ...p)).href;
const recorte = (id) => arq("insumos", "recortes", `${id}.png`);
const retrato = (id) => arq("site", "img", "personagens", `${id}.webp`);
const telefone = cfg.pix?.como_aparece || "";

const BANDEIRAS = `url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='176' height='46'><path d='M0 5Q44 13 88 5T176 5' fill='none' stroke='%2322140B' stroke-width='2'/><g stroke='%2322140B' stroke-width='2' stroke-linejoin='round'><path d='M7 7h30v30l-15-8-15 8z' fill='%23F57C00'/><path d='M51 9h30v30l-15-8-15 8z' fill='%232E7D32'/><path d='M95 7h30v30l-15-8-15 8z' fill='%2329B6F6'/><path d='M139 9h30v30l-15-8-15 8z' fill='%23E53935'/></g></svg>")`;
const WHATS = `<svg viewBox="0 0 24 24"><path d="M12 3a9 9 0 0 0-7.7 13.6L3 21l4.5-1.2A9 9 0 1 0 12 3Z" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"/><path d="M9 8.5c0 3.5 2.6 6.5 6.5 6.8l1-1.6-2-1-1 .8c-1-.5-1.9-1.4-2.4-2.4l.8-1-1-2-1.6 1Z" fill="currentColor"/></svg>`;
// estrela de 24 pontas para o selo
const ESTRELA = Array.from({ length: 48 }, (_, i) => {
  const ang = (i / 48) * 2 * Math.PI, r = i % 2 ? 41 : 50;
  return `${(50 + r * Math.cos(ang)).toFixed(1)}% ${(50 + r * Math.sin(ang)).toFixed(1)}%`;
}).join(",");

function visual(a) {
  if (a.visual === "personagem") return `<img class="figura" src="${recorte(a.recorte)}">`;
  if (a.visual === "morador") {
    const carta = (id, giro) => `<figure class="carta" style="--giro:${giro}"><img src="${retrato(id)}"></figure>`;
    return `<div class="cartas">${carta("ze-pavio", "-10deg")}<figure class="carta voce"><div class="vaga">?</div><figcaption>VOCÊ</figcaption></figure></div>`;
  }
  const escolhidas = [1, 2, 10, 11].map((i) => `${String(i + 1).padStart(2, "0")}-${figs[i].personagem}.webp`);
  return `<div class="figs">${escolhidas.map((f) => `<img src="${arq("site", "figurinhas", f)}">`).join("")}</div>`;
}

const peca = (a, formato) => `<section class="arte ${formato}" id="${formato}-${a.id}">
  <div class="cena-fundo"></div><div class="raios"></div><div class="bandeiras"></div>
  <img class="logo" src="${arq("site", "img", "logo-doido-varrido.webp")}">
  <div class="placa"><h1>${a.linhas.map((l) => `<span class="${l.destaque ? "destaque" : ""}">${esc(l.t)}</span>`).join("")}</h1></div>
  <p class="faixa"><span>${esc(a.faixa)}</span></p>
  <div class="corpo v-${a.visual}">
    <div class="quadro">
      <h2>O que você recebe</h2>
      <ul class="itens">${a.itens.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>
      <h2>Como funciona</h2>
      <ol class="passos">${a.passos.map((i) => `<li>${esc(i)}</li>`).join("")}</ol>
    </div>
    <div class="palco">${visual(a)}<p class="selo">${/^a partir de /i.test(a.selo)
      ? `<span class="preco"><small>a partir de</small><strong>${esc(a.selo.replace(/^a partir de /i, ""))}</strong></span>`
      : `<span style="font-size:${Math.min(40, Math.floor(200 / (Math.max(...a.selo.split(/\s+/).map((w) => w.length)) * 0.82)))}px">${esc(a.selo)}</span>`}</p></div>
  </div>
  <div class="chamada">
    <span class="icone">${WHATS}</span>
    <span class="dizeres"><b>${esc(a.chamada)}</b>${a.visual === "figurinhas" ? "" : `<em>${esc(telefone)}</em>`}<small>${esc(dados.arroba)}</small></span>
    <span class="rodape">${esc(a.rodape || "")}</span>
  </div>
</section>`;

const html = `<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Alegreya+Sans:wght@800;900&family=Ultra&display=block">
<style>
  body { margin: 0; }
  .arte { position: relative; overflow: hidden; width: 1080px; margin-bottom: 40px; box-sizing: border-box;
    display: flex; flex-direction: column; align-items: center; color: #3A1E0B; }
  /* cena da vila, com o pôr do sol, e raios saindo de trás do personagem */
  .cena-fundo { position: absolute; inset: 0; background: url("${arq("site", "img", "vila-panorama.webp")}") center 30% / cover; }
  .cena-fundo::after { content: ""; position: absolute; inset: 0;
    background: linear-gradient(180deg, rgba(251, 192, 45, .55) 0%, rgba(245, 124, 0, .25) 45%, rgba(58, 30, 11, .55) 100%); }
  .raios { position: absolute; left: 50%; top: 62%; width: 2600px; height: 2600px; margin: -1300px 0 0 -1300px;
    background: repeating-conic-gradient(rgba(255, 236, 140, .42) 0 7deg, rgba(255, 236, 140, 0) 7deg 14deg);
    -webkit-mask: radial-gradient(circle, #000 18%, transparent 55%); }
  .bandeiras { position: absolute; left: 0; right: 0; top: 0; height: 110px; background: ${BANDEIRAS} repeat-x 0 0 / 421px 110px; z-index: 2; }
  .logo { position: absolute; z-index: 5; filter: drop-shadow(0 10px 0 rgba(58, 30, 11, .45)); }

  /* título na placa de madeira, como nas capas */
  .placa { position: relative; z-index: 4; transform: rotate(-2.5deg); padding: 34px 46px 40px; border: 10px solid #3A1E0B; border-radius: 22px;
    background:
      radial-gradient(circle at 26px 26px, #3A1E0B 9px, transparent 10px), radial-gradient(circle at calc(100% - 26px) 26px, #3A1E0B 9px, transparent 10px),
      radial-gradient(circle at 26px calc(100% - 26px), #3A1E0B 9px, transparent 10px), radial-gradient(circle at calc(100% - 26px) calc(100% - 26px), #3A1E0B 9px, transparent 10px),
      repeating-linear-gradient(176deg, rgba(0, 0, 0, .07) 0 3px, transparent 3px 22px),
      linear-gradient(180deg, #A8692E, #7A4519);
    box-shadow: 0 18px 0 rgba(58, 30, 11, .55); }
  .placa h1 { margin: 0; text-align: center; font-family: "Ultra", serif; font-weight: 400; }
  .placa span { display: block; line-height: .98; color: #FFE14D; -webkit-text-stroke: 16px #3A1E0B; paint-order: stroke fill;
    text-shadow: 0 10px 0 #3A1E0B; }
  .placa span.destaque { color: #FF7A1A; }

  .faixa { position: relative; z-index: 4; margin: 0; transform: rotate(1.5deg); background: #1F6FE0; border: 8px solid #3A1E0B;
    clip-path: polygon(0 0, 100% 0, 97% 50%, 100% 100%, 0 100%, 3% 50%); padding: 18px 70px; box-shadow: 0 10px 0 rgba(58, 30, 11, .5); }
  .faixa span { font: 400 46px/1.15 "Ultra", serif; color: #FFE14D; -webkit-text-stroke: 9px #10223F; paint-order: stroke fill; }

  .palco { position: relative; z-index: 3; flex: 1; min-height: 0; width: 100%; display: flex; align-items: flex-end; justify-content: center; }
  .figura { max-height: 100%; max-width: 100%;
    filter: drop-shadow(8px 0 0 #fff) drop-shadow(-8px 0 0 #fff) drop-shadow(0 8px 0 #fff) drop-shadow(0 -8px 0 #fff) drop-shadow(0 18px 14px rgba(0, 0, 0, .45)); }
  .selo { position: absolute; margin: 0; width: 300px; height: 300px; display: grid; place-items: center; text-align: center; transform: rotate(12deg); z-index: 5;
    background: #3A1E0B; clip-path: polygon(${ESTRELA}); }
  .selo::before { content: ""; position: absolute; inset: 12px; background: #E53935; clip-path: polygon(${ESTRELA}); }
  .selo span { position: relative; width: 70%; font: 400 40px/1.02 "Ultra", serif; color: #FFE14D; -webkit-text-stroke: 7px #3A1E0B; paint-order: stroke fill; }
  .selo .preco { display: flex; flex-direction: column; align-items: center; gap: 2px; width: 82%; }
  .selo .preco small { font: 900 30px/1 "Alegreya Sans", sans-serif; color: #fff; -webkit-text-stroke: 6px #3A1E0B; paint-order: stroke fill; }
  .selo .preco strong { font: 400 40px/1 "Ultra", serif; color: #FFE14D; -webkit-text-stroke: 9px #3A1E0B; paint-order: stroke fill; white-space: nowrap; }
  .feed .selo .preco small { font-size: 22px; } .feed .selo .preco strong { font-size: 33px; }
  .arroba { position: absolute; left: 0; top: 6px; margin: 0; z-index: 5; background: #3A1E0B; color: #FFE14D; border-radius: 999px;
    font: 900 34px/1 "Alegreya Sans", sans-serif; padding: 14px 26px; }

  /* botão verde do WhatsApp, com relevo */
  .chamada { position: relative; z-index: 6; width: 100%; box-sizing: border-box; display: flex; align-items: center; gap: 28px;
    background: linear-gradient(180deg, #2FC25B, #1E9445); border: 8px solid #3A1E0B; border-radius: 26px; padding: 26px 34px;
    box-shadow: 0 16px 0 #14592A, 0 22px 24px rgba(0, 0, 0, .35); color: #fff; }
  .chamada .icone { flex: none; width: 118px; height: 118px; border-radius: 50%; background: #fff; color: #1E9445; display: grid; place-items: center; border: 6px solid #3A1E0B; }
  .chamada svg { width: 76px; height: 76px; }
  .chamada .dizeres { flex: 1; }
  .chamada b { display: block; font: 400 50px/1.05 "Ultra", serif; color: #fff; -webkit-text-stroke: 9px #14592A; paint-order: stroke fill; }
  .chamada em { display: block; font: 900 58px/1.1 "Alegreya Sans", sans-serif; font-style: normal; color: #FFE14D; margin-top: 4px;
    -webkit-text-stroke: 7px #14592A; paint-order: stroke fill; }
  .chamada .rodape { position: absolute; right: 26px; top: -34px; background: #FFE14D; color: #3A1E0B; border: 6px solid #3A1E0B; border-radius: 999px;
    font: 900 32px/1 "Alegreya Sans", sans-serif; padding: 12px 24px; transform: rotate(3deg); }
  .chamada .rodape:empty { display: none; }

  .cartas { display: flex; align-items: flex-end; justify-content: center; width: 100%; padding-bottom: 20px; }
  .carta { margin: 0 -18px; width: 27%; background: #FFFBF0; border: 8px solid #3A1E0B; padding: 12px 12px 0; box-sizing: border-box; transform: rotate(var(--giro, 0deg));
    box-shadow: 0 14px 0 rgba(58, 30, 11, .45); }
  .carta img, .carta .vaga { display: block; width: 100%; aspect-ratio: 2 / 3; object-fit: cover; border: 5px solid #3A1E0B; box-sizing: border-box; }
  .carta.voce { position: relative; z-index: 1; width: 32%; background: #FF7A1A; }
  .carta .vaga { display: grid; place-items: center; background: #FFFBF0; border-style: dashed; font: 400 170px/1 "Ultra", serif; color: #FF7A1A; -webkit-text-stroke: 8px #3A1E0B; paint-order: stroke fill; }
  .carta figcaption { font: 400 50px/1 "Ultra", serif; text-align: center; padding: 14px 0 16px; color: #FFE14D; -webkit-text-stroke: 9px #3A1E0B; paint-order: stroke fill; }
  .figs { display: grid; grid-template-columns: 1fr 1fr; gap: 0 10px; height: 100%; aspect-ratio: 1; padding-top: 50px; box-sizing: border-box; }
  .figs { grid-template-rows: minmax(0, 1fr) minmax(0, 1fr); }
  .figs img { width: 100%; height: 100%; object-fit: contain; min-height: 0; transform: rotate(-4deg); filter: drop-shadow(0 12px 10px rgba(0, 0, 0, .4)); }
  .figs img:nth-child(even) { transform: rotate(5deg); }

  /* quadro de venda: o que a pessoa recebe e como funciona */
  .corpo { position: relative; z-index: 3; flex: 1; min-height: 0; width: 100%; display: grid; grid-template-columns: 1.25fr .75fr; gap: 14px; }
  .quadro { align-self: center; background: #FFFBF0; border: 8px solid #3A1E0B; border-radius: 26px; padding: 28px 30px 30px;
    box-shadow: 0 14px 0 rgba(58, 30, 11, .5); display: flex; flex-direction: column; gap: 16px; transform: rotate(-1deg); }
  .quadro h2 { margin: 0; font: 400 40px/1 "Ultra", serif; color: #D62828; }
  .quadro h2 + ul, .quadro h2 + ol { margin-top: -2px; }
  .itens { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 14px; }
  .itens li { display: grid; grid-template-columns: 50px 1fr; gap: 14px; align-items: start; font: 800 34px/1.16 "Alegreya Sans", sans-serif; color: #3A1E0B; }
  .itens li::before { content: "✓"; width: 50px; height: 50px; box-sizing: border-box; border-radius: 50%; background: #2FC25B; border: 4px solid #3A1E0B;
    color: #fff; display: grid; place-items: center; font: 900 30px/1 "Alegreya Sans", sans-serif; }
  .passos { list-style: none; counter-reset: passo; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
  .passos li { counter-increment: passo; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center;
    font: 800 27px/1.12 "Alegreya Sans", sans-serif; color: #3A1E0B; }
  .passos li::before { content: counter(passo); width: 62px; height: 62px; box-sizing: border-box; border-radius: 50%; background: #FF7A1A; border: 5px solid #3A1E0B;
    display: grid; place-items: center; font: 400 34px/1 "Ultra", serif; color: #fff; }
  .corpo .palco { height: 100%; }
  .corpo .selo { right: -20px; top: 0; width: 250px; height: 250px; }
  .chamada small { display: block; font: 900 30px/1.1 "Alegreya Sans", sans-serif; color: #EAFBEA; margin-top: 4px; }
  .corpo .cartas { padding-bottom: 10px; }
  .corpo .carta { width: 62%; margin: 0 -34% 0 0; }
  .corpo .carta.voce { width: 70%; margin: 0; }
  .corpo .figs { height: auto; width: 100%; aspect-ratio: auto; padding: 0; align-self: center; }
  .corpo .figs img { height: auto; }
  .arte .corpo.v-figurinhas { grid-template-columns: 1fr 1fr; }
  .corpo.v-figurinhas .selo { top: -40px; }

  /* story 1080x1920: o topo (~250 px) e o rodapé (~230 px) ficam por conta do Instagram */
  .story { height: 1920px; padding: 255px 56px 235px; gap: 22px; }
  .story .logo { top: 96px; left: 40px; width: 230px; }
  .story .placa span { font-size: 74px; -webkit-text-stroke-width: 13px; }
  .story .placa { padding: 26px 40px 32px; }
  .story .corpo { grid-template-columns: 1.42fr .58fr; }
  .story .quadro { padding: 24px 26px 26px; gap: 13px; }
  .story .quadro h2 { font-size: 36px; }
  .story .itens { gap: 11px; } .story .itens li { font-size: 32px; grid-template-columns: 46px 1fr; gap: 12px; }
  .story .itens li::before { width: 46px; height: 46px; font-size: 27px; }
  .story .passos li { font-size: 26px; } .story .passos li::before { width: 54px; height: 54px; font-size: 30px; }
  .story .corpo .selo { width: 250px; height: 250px; right: -24px; }
  .story .faixa span { font-size: 34px; }
  .story .faixa { padding: 14px 60px; }
  .story .selo { right: -10px; top: 0; }
  /* feed 1080x1350 */
  .feed { height: 1350px; padding: 70px 50px 56px; gap: 24px; }
  .feed .bandeiras { height: 80px; background-size: 306px 80px; }
  .feed .logo { top: 14px; left: 26px; width: 150px; }
  .feed .placa { padding: 24px 40px 30px; }
  .feed .placa span { font-size: 70px; -webkit-text-stroke-width: 12px; }
  .feed .corpo { grid-template-columns: 1.3fr .7fr; }
  .feed .quadro { padding: 20px 22px 22px; gap: 11px; border-width: 7px; }
  .feed .quadro h2 { font-size: 34px; }
  .feed .quadro h2:nth-of-type(2), .feed .passos, .feed .itens li:nth-child(n+4) { display: none; }
  .feed .itens { gap: 14px; } .feed .itens li { font-size: 31px; grid-template-columns: 44px 1fr; gap: 12px; }
  .feed .itens li::before { width: 44px; height: 44px; font-size: 25px; border-width: 4px; }
  .feed .passos li { font-size: 21px; gap: 6px; } .feed .passos li::before { width: 46px; height: 46px; font-size: 26px; border-width: 4px; }
  .feed .corpo .selo { width: 200px; height: 200px; right: -14px; }
  .feed .chamada small { font-size: 24px; }

  .feed .faixa { padding: 12px 54px; } .feed .faixa span { font-size: 30px; }
  .feed .selo { width: 250px; height: 250px; right: -6px; top: -10px; } .feed .selo span { font-size: 34px; }
  .feed .arroba { font-size: 28px; padding: 11px 20px; }
  .feed .chamada { padding: 18px 28px; } .feed .chamada .icone { width: 96px; height: 96px; } .feed .chamada svg { width: 60px; height: 60px; }
  .feed .chamada b { font-size: 42px; } .feed .chamada em { font-size: 48px; }
  .feed .carta figcaption { font-size: 40px; } .feed .carta .vaga { font-size: 130px; }
</style></head><body>
${dados.artes.map((a) => peca(a, "story") + peca(a, "feed")).join("\n")}
</body></html>`;

const espera = (ms) => new Promise((ok) => setTimeout(ok, ms));
const perfil = join(tmpdir(), `artes-edge-${Date.now()}`);
mkdirSync(perfil, { recursive: true });
const pagina = join(perfil, "artes.html");
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
  await cdp("Emulation.setDeviceMetricsOverride", { width: 1080, height: 1920, deviceScaleFactor: 1, mobile: false });
  const carregou = evento("Page.loadEventFired");
  await cdp("Page.navigate", { url: pathToFileURL(pagina).href });
  await carregou;
  const ok = await avaliar(`(async () => { await document.fonts.ready; await document.fonts.load('40px Ultra');
    const faltando = [...document.images].filter((i) => !i.complete || !i.naturalWidth).map((i) => i.src.split("/").pop());
    return { faltando, fonte: document.fonts.check('40px Ultra') }; })()`);
  if (ok.faltando.length || !ok.fonte) throw new Error(`não carregou: ${ok.faltando.join(", ")} ${ok.fonte ? "" : "fonte Ultra"}`);
  await espera(400);

  mkdirSync(SAIDA, { recursive: true });
  for (const a of dados.artes) {
    for (const formato of ["story", "feed"]) {
      const c = await avaliar(`(() => { const r = document.getElementById("${formato}-${a.id}").getBoundingClientRect();
        return { x: r.x, y: r.y + scrollY, w: r.width, h: r.height }; })()`);
      const { data } = await cdp("Page.captureScreenshot", { format: "jpeg", quality: 90, captureBeyondViewport: true,
        clip: { x: c.x, y: c.y, width: c.w, height: c.h, scale: 1 } });
      writeFileSync(join(SAIDA, `${formato}-${a.id}.jpg`), Buffer.from(data, "base64"));
      console.log(`${formato}-${a.id}.jpg`);
    }
  }
  ws.close();
} finally {
  edge.kill();
  await espera(500);
  try { rmSync(perfil, { recursive: true, force: true }); } catch { /* o Edge às vezes ainda segura o perfil */ }
}
