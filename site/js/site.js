// O Doido Varrido Show: tocador, trilhos, balões, teste, catálogo, PIX e o aviso das redes.
// Sem JavaScript o conteúdo continua todo na página e os vídeos abrem no YouTube.
(() => {
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const iframe = (id, titulo) =>
    `<iframe src="https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?autoplay=1&rel=0" title="${esc(titulo)}"
      allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe>`;
  const sem = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const guardar = (k, v) => { try { localStorage.setItem(k, v); } catch { /* navegador sem armazenamento */ } };
  const lembrar = (k) => { try { return localStorage.getItem(k); } catch { return null; } };

  // Barra: o selo encolhe quando a página rola; no celular o menu abre num painel
  const topo = document.querySelector("[data-topo]");
  if (topo) {
    const aoRolar = () => topo.classList.toggle("rolou", scrollY > 40);
    addEventListener("scroll", aoRolar, { passive: true });
    aoRolar();
    const botao = topo.querySelector("[data-menu]");
    const menu = document.getElementById("menu");
    const rotulo = botao.querySelector(".rotulo");
    const aberto = () => menu.classList.contains("aberto");
    const fechar = () => { menu.classList.remove("aberto"); botao.setAttribute("aria-expanded", "false"); rotulo.textContent = "Menu"; };
    const abrir = () => {
      menu.classList.add("aberto");
      botao.setAttribute("aria-expanded", "true");
      rotulo.textContent = "Fechar";
      menu.querySelector("a")?.focus({ preventScroll: true });
    };
    botao.addEventListener("click", () => (aberto() ? fechar() : abrir()));
    menu.addEventListener("click", (ev) => { if (ev.target.closest("a")) fechar(); });
    document.addEventListener("click", (ev) => { if (aberto() && !topo.contains(ev.target)) fechar(); });
    document.addEventListener("keydown", (ev) => { if (ev.key === "Escape" && aberto()) { fechar(); botao.focus(); } });
    addEventListener("resize", () => { if (aberto() && innerWidth > 880) fechar(); });
  }

  // Balões que aparecem quando entram na tela
  const revelar = document.querySelectorAll(".revelar");
  if ("IntersectionObserver" in window) {
    const olho = new IntersectionObserver((itens) => itens.forEach((it) => {
      if (it.isIntersecting) { it.target.classList.add("visto"); olho.unobserve(it.target); }
    }), { threshold: 0.25 });
    revelar.forEach((el) => olho.observe(el));
  } else revelar.forEach((el) => el.classList.add("visto"));

  // Trilhos com rolagem lateral: setas, régua de posição e esconde os controles quando cabe tudo
  document.querySelectorAll("[data-carrossel]").forEach((c) => {
    const trilho = c.querySelector(".trilho");
    const controles = c.querySelector(".controles");
    const regua = controles.querySelector(".regua");
    const ant = controles.querySelector("[data-anterior]");
    const prox = controles.querySelector("[data-proximo]");
    const atualizar = () => {
      const max = trilho.scrollWidth - trilho.clientWidth;
      controles.hidden = max <= 4;
      if (max <= 4) return;
      const parte = trilho.clientWidth / trilho.scrollWidth;
      const pos = trilho.scrollLeft / max;
      regua.style.setProperty("--parte", `${(parte * 100).toFixed(2)}%`);
      regua.style.setProperty("--pos", `${(pos * (1 / parte - 1) * 100).toFixed(2)}%`);
      ant.disabled = trilho.scrollLeft <= 4;
      prox.disabled = trilho.scrollLeft >= max - 4;
    };
    const passo = (dir) => trilho.scrollBy({ left: dir * trilho.clientWidth * 0.85, behavior: "smooth" });
    ant.addEventListener("click", () => passo(-1));
    prox.addEventListener("click", () => passo(1));
    trilho.addEventListener("scroll", atualizar, { passive: true });
    if ("ResizeObserver" in window) new ResizeObserver(atualizar).observe(trilho);
    atualizar();
  });

  // Rádio da página inicial: a parada troca o vídeo do tocador
  const tocador = document.querySelector("[data-tocador]");
  if (tocador) {
    const tela = tocador.querySelector(".tela");
    const legenda = tocador.querySelector(".legenda");
    const tocar = () => { tela.innerHTML = iframe(tocador.dataset.id, tocador.dataset.titulo); };
    tela.querySelector(".play")?.addEventListener("click", tocar);
    const faixas = document.querySelectorAll("[data-faixa]");
    faixas.forEach((f) => f.addEventListener("click", (ev) => {
      ev.preventDefault();
      faixas.forEach((x) => x.removeAttribute("aria-current"));
      f.setAttribute("aria-current", "true");
      tocador.dataset.id = f.dataset.id;
      tocador.dataset.titulo = f.dataset.titulo;
      legenda.innerHTML = `${esc(f.dataset.titulo)}<small>${esc(f.dataset.meta)}</small>`;
      tocar();
      if (matchMedia("(max-width: 900px)").matches) tocador.scrollIntoView({ block: "center" });
    }));
  }

  // Janela de vídeo para os cartões do catálogo, dos comentários, das Piadas do Dia e das fichas
  const janela = document.querySelector("dialog.janela-video");
  if (janela && janela.showModal) {
    const tela = janela.querySelector(".tela");
    const nome = janela.querySelector(".barra span");
    document.addEventListener("click", (ev) => {
      const a = ev.target.closest("[data-video]");
      if (!a || ev.ctrlKey || ev.metaKey || ev.shiftKey) return;
      ev.preventDefault();
      nome.textContent = a.dataset.titulo;
      tela.innerHTML = iframe(a.dataset.video, a.dataset.titulo);
      janela.showModal();
    });
    janela.querySelector("[data-fechar]").addEventListener("click", () => janela.close());
    janela.addEventListener("click", (ev) => { if (ev.target === janela) janela.close(); });
    janela.addEventListener("close", () => { tela.innerHTML = ""; });
  }

  // Catálogo de músicas: estilo, busca, ordem e "mostrar mais" de 12 em 12
  const lista = document.querySelector("[data-catalogo]");
  if (lista) {
    const itens = [...lista.children];
    const botoes = document.querySelectorAll("[data-familia]");
    const busca = document.querySelector("#busca");
    const ordem = document.querySelector("#ordem");
    const vazio = document.querySelector(".vazio");
    const contador = document.querySelector(".contador");
    const mais = document.querySelector("[data-mais]");
    const LOTE = 12;
    let familia = "todas";
    let limite = LOTE;
    const aplicar = () => {
      const q = sem(busca.value.trim());
      const porViews = ordem.value === "views";
      itens.sort((a, b) => porViews ? b.dataset.views - a.dataset.views : b.dataset.data.localeCompare(a.dataset.data))
        .forEach((li) => lista.appendChild(li));
      let n = 0;
      itens.forEach((li) => {
        const ok = (familia === "todas" || li.dataset.familia === familia) && (!q || li.dataset.busca.includes(q));
        li.hidden = !ok;
        if (ok) n++;
        li.classList.toggle("oculto-limite", ok && n > limite);
      });
      vazio.hidden = n > 0;
      contador.textContent = n ? `Mostrando ${Math.min(n, limite)} de ${n} músicas` : "";
      mais.hidden = n <= limite;
    };
    const recomecar = () => { limite = LOTE; aplicar(); };
    botoes.forEach((b) => b.addEventListener("click", () => {
      familia = b.dataset.familia;
      botoes.forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      recomecar();
    }));
    busca.addEventListener("input", recomecar);
    ordem.addEventListener("change", recomecar);
    mais.addEventListener("click", () => { limite += LOTE; aplicar(); });
    aplicar();
  }

  // PIX: copiar a chave
  document.querySelectorAll("[data-copiar]").forEach((b) => b.addEventListener("click", async () => {
    const aviso = b.parentElement.querySelector(".aviso");
    try {
      await navigator.clipboard.writeText(b.dataset.copiar);
      aviso.textContent = "Peguei foi ligeiro! Chave copiada, agora é só colar no aplicativo do banco.";
    } catch {
      aviso.textContent = "Não deu para copiar sozinho: segure o dedo sobre a chave e copie.";
    }
  }));

  // Teste: quem é você em Buraco Fundo?
  const teste = document.querySelector("[data-teste]");
  if (teste) {
    const dados = JSON.parse(teste.querySelector('script[type="application/json"]').textContent);
    const quadro = teste.querySelector(".quadro-teste");
    const total = dados.perguntas.length;
    let i = 0;
    let pontos = {};
    let ordem = [];
    const foco = () => quadro.querySelector("h3")?.focus({ preventScroll: true });
    const pergunta = () => {
      const q = dados.perguntas[i];
      quadro.innerHTML = `<div class="progresso" aria-hidden="true">${dados.perguntas.map((_, k) => `<span class="${k < i ? "feito" : ""}"></span>`).join("")}</div>
        <p class="sr">Pergunta ${i + 1} de ${total}</p>
        <h3 tabindex="-1">${esc(q.texto)}</h3>
        <ul class="opcoes">${q.opcoes.map((o, k) => `<li><button type="button" class="balao" data-k="${k}">${esc(o.texto)}</button></li>`).join("")}</ul>`;
      foco();
    };
    const resultado = () => {
      const max = Math.max(...Object.values(pontos));
      const empatados = Object.keys(pontos).filter((k) => pontos[k] === max);
      const id = [...ordem].reverse().find((r) => empatados.includes(r));
      const p = dados.resultados[id];
      const texto = `Fiz o teste do Vilarejo Buraco Fundo e deu ${p.nome}! “${p.bordao}”${dados.endereco ? ` Descubra o seu: ${dados.endereco}` : ""}`;
      quadro.innerHTML = `<div class="resultado">
        <img src="${esc(p.img)}" alt="Ilustração de ${esc(p.nome)}" width="520" height="780">
        <div>
          <p class="deu">Em Buraco Fundo, você seria</p>
          <h3 tabindex="-1">${esc(p.nome)}</h3>
          <blockquote class="balao rabo-esq"><p>“${esc(p.bordao)}”</p></blockquote>
          <p>${esc(p.descricao)}</p>
          <div class="botoes">
            <a class="botao verde" href="https://wa.me/?text=${encodeURIComponent(texto)}" target="_blank" rel="noopener">Mandar no WhatsApp</a>
            <a class="botao papel" href="${esc(p.link)}">Ver a ficha</a>
            <button class="botao papel" type="button" data-refazer>Refazer o teste</button>
          </div>
        </div>
      </div>`;
      foco();
    };
    quadro.addEventListener("click", (ev) => {
      if (ev.target.closest("[data-comecar], [data-refazer]")) {
        i = 0; pontos = {}; ordem = [];
        pergunta();
        return;
      }
      const b = ev.target.closest(".opcoes button");
      if (!b) return;
      const r = dados.perguntas[i].opcoes[Number(b.dataset.k)].resultado;
      pontos[r] = (pontos[r] || 0) + 1;
      ordem.push(r);
      i += 1;
      if (i < total) pergunta(); else resultado();
    });
  }

  // Zé Corneteiro chama para as redes depois de um tempo de visita; fechado, some por uma semana
  const pregao = document.querySelector("[data-pregao]");
  if (pregao) {
    const CHAVE = "doido-varrido-pregao-fechado";
    const SEMANA = 7 * 24 * 3600 * 1000;
    const fechadoEm = Number(lembrar(CHAVE)) || 0;
    if (Date.now() - fechadoEm > SEMANA) {
      let feito = false;
      const mostrar = () => {
        if (feito) return;
        feito = true;
        pregao.hidden = false;
        removeEventListener("scroll", aoRolar);
      };
      const aoRolar = () => { if (scrollY > innerHeight * 1.5) mostrar(); };
      addEventListener("scroll", aoRolar, { passive: true });
      setTimeout(mostrar, 40000);
    }
    pregao.querySelector("[data-fechar-pregao]").addEventListener("click", () => {
      pregao.hidden = true;
      guardar(CHAVE, String(Date.now()));
    });
  }
})();
