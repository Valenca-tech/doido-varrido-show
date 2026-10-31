// Tira as telas do site como num celular e junta tudo num PDF, para mandar pelo WhatsApp.
// Uso: node ferramentas/previa_celular.mjs [endereço]   (padrão http://localhost:8770)
// Cada tela começa no início de uma seção, logo abaixo do cabeçalho. A página inicial ganha
// ainda as telas do teste (perguntas e resultado) e uma com o aviso das redes.
// Saída em previa/: imagens numeradas na ordem de leitura e Previa-site-Doido-Varrido.pdf.
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), "..");
const SAIDA = join(RAIZ, "previa");
const BASE = (process.argv[2] || "http://localhost:8770").replace(/\/$/, "");
const EDGE = ["C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Microsoft/Edge/Application/msedge.exe"].find(existsSync);
const LARGURA = 390, ALTURA = 844, ESCALA = 2; // tela de celular comum, em pixels CSS
// página, nome no arquivo, máximo de telas (listas longas mostram só o começo)
const PAGINAS = [
  ["index.html", "inicio", 99],
  ["musicas.html", "musicas", 2],
  ["vilarejo.html", "vilarejo", 99],
  ["moradores.html", "moradores", 3],
  ["personagens/ze-pavio.html", "ficha-ze-pavio", 3],
  ["patrocinio.html", "patrocinio", 99],
];

const espera = (ms) => new Promise((ok) => setTimeout(ok, ms));
const perfil = join(tmpdir(), `previa-edge-${Date.now()}`);
const porta = 9300 + Math.floor(Math.random() * 400);
const edge = spawn(EDGE, ["--headless=new", `--remote-debugging-port=${porta}`, `--user-data-dir=${perfil}`,
  "--hide-scrollbars", "--no-first-run", "about:blank"], { stdio: "ignore" });

try {
  let alvo;
  for (let i = 0; i < 75 && !alvo; i++) {
    try {
      alvo = (await (await fetch(`http://127.0.0.1:${porta}/json/list`)).json()).find((t) => t.type === "page");
    } catch { /* o Edge ainda está abrindo */ }
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
  await cdp("Emulation.setDeviceMetricsOverride", { width: LARGURA, height: ALTURA, deviceScaleFactor: ESCALA, mobile: true });
  rmSync(SAIDA, { recursive: true, force: true });
  mkdirSync(SAIDA, { recursive: true });

  const telas = [];
  const fotografar = async (nome) => {
    const { data } = await cdp("Page.captureScreenshot", { format: "jpeg", quality: 82 });
    writeFileSync(join(SAIDA, `${String(telas.length + 1).padStart(2, "0")}-${nome}.jpg`), Buffer.from(data, "base64"));
    telas.push(data);
  };
  const rolar = async (y, ms = 300) => { await avaliar(`window.scrollTo(0, ${y})`); await espera(ms); };

  for (const [caminho, nome, maximo] of PAGINAS) {
    const carregou = evento("Page.loadEventFired");
    await cdp("Page.navigate", { url: `${BASE}/${caminho}` });
    await carregou;
    // carrega todas as imagens, mostra os balões já abertos e esconde o aviso das redes nas telas comuns
    const { altura, topo, secoes } = await avaliar(`(async () => {
      document.documentElement.style.scrollBehavior = "auto";
      const estilo = document.createElement("style");
      estilo.id = "sem-aviso";
      estilo.textContent = ".pregao { display: none !important }";
      document.head.append(estilo);
      document.querySelectorAll("img[loading=lazy]").forEach((i) => { i.loading = "eager"; });
      document.querySelectorAll(".revelar").forEach((el) => el.classList.add("visto"));
      await document.fonts.ready;
      await Promise.all([...document.images].map((i) => i.complete ? 0 : new Promise((r) => { i.onload = i.onerror = r; })));
      const secoes = [...document.querySelectorAll("main > section, main > aside, footer")]
        .map((el) => ({ topo: el.offsetTop, fim: el.offsetTop + el.offsetHeight }));
      return { altura: document.documentElement.scrollHeight, topo: document.querySelector(".topo").offsetHeight, secoes };
    })()`);
    await espera(1200); // animação de entrada da capa

    // uma tela por seção, alinhada logo abaixo do cabeçalho; seção comprida continua na tela seguinte
    const maxRolagem = altura - ALTURA;
    const passo = ALTURA - topo;
    const posicoes = [];
    let ultima = -Infinity;
    for (const s of secoes) {
      if (s.fim <= ultima + ALTURA - 8) continue; // já apareceu inteira na tela anterior
      let y = Math.max(0, s.topo - topo);
      for (;;) {
        const yy = Math.min(y, maxRolagem);
        if (yy - ultima > 40) { posicoes.push(yy); ultima = yy; }
        if (y + ALTURA >= s.fim || yy === maxRolagem) break;
        y += passo;
      }
    }
    for (const [i, y] of posicoes.slice(0, maximo).entries()) {
      await rolar(y);
      await fotografar(`${nome}-${i + 1}`);
    }

    if (nome === "inicio") {
      // o teste: as cinco perguntas e um resultado
      const yTeste = await avaliar(`document.querySelector("#teste").offsetTop - document.querySelector(".topo").offsetHeight`);
      await avaliar(`document.querySelector("[data-comecar]").click()`);
      for (let k = 0; k < 5; k++) {
        await rolar(yTeste, 250);
        await fotografar(`teste-pergunta-${k + 1}`);
        await avaliar(`document.querySelectorAll(".quadro-teste .opcoes button")[${[0, 3, 0, 0, 1][k]}].click()`);
      }
      await rolar(yTeste, 400);
      await fotografar("teste-resultado");
      // o aviso das redes, como aparece depois de rolar a página
      await avaliar(`document.getElementById("sem-aviso").remove(); document.querySelector("[data-pregao]").hidden = false;`);
      await rolar(await avaliar(`document.querySelector("#radio").offsetTop - 60`), 900);
      await fotografar("aviso-redes");
      // o menu do celular aberto
      await avaliar(`document.querySelector("[data-pregao]").hidden = true; document.querySelector("[data-menu]").click()`);
      await rolar(0, 600);
      await fotografar("menu-aberto");
      await avaliar(`document.querySelector("[data-menu]").click()`);
    }
    console.log(`${caminho}: ${posicoes.slice(0, maximo).length} telas`);
  }

  // PDF: uma tela por página, no formato do celular
  await cdp("Emulation.clearDeviceMetricsOverride");
  const html = `<!doctype html><html><head><meta charset="utf-8"><style>
    @page { size: ${LARGURA}px ${ALTURA}px; margin: 0 }
    body { margin: 0 }
    img { display: block; width: ${LARGURA}px; height: ${ALTURA}px; break-after: page }
  </style></head><body>${telas.map((t) => `<img src="data:image/jpeg;base64,${t}">`).join("")}</body></html>`;
  const pagina = join(perfil, "previa.html");
  writeFileSync(pagina, html);
  const carregou = evento("Page.loadEventFired");
  await cdp("Page.navigate", { url: pathToFileURL(pagina).href });
  await carregou;
  // o PDF passa de 10 MB: vem em partes, não numa mensagem só
  const { stream } = await cdp("Page.printToPDF", { preferCSSPageSize: true, printBackground: true, transferMode: "ReturnAsStream" });
  const partes = [];
  for (;;) {
    const r = await cdp("IO.read", { handle: stream, size: 1 << 20 });
    partes.push(Buffer.from(r.data, r.base64Encoded ? "base64" : "utf8"));
    if (r.eof) break;
  }
  await cdp("IO.close", { handle: stream });
  writeFileSync(join(SAIDA, "Previa-site-Doido-Varrido.pdf"), Buffer.concat(partes));
  console.log(`${telas.length} telas e o PDF em ${SAIDA}`);
  ws.close();
} finally {
  edge.kill();
  await espera(500);
  try { rmSync(perfil, { recursive: true, force: true }); } catch { /* o Edge às vezes ainda segura o perfil */ }
}
