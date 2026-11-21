// Carrossel dos filmes populares no topo da página inicial.
// - troca sozinho a cada 7 s (pausa com o mouse em cima, com o foco do teclado
//   ou com "Reduzir animações" ligado);
// - setas, bolinhas, miniaturas "A seguir", teclado (← →) e arrastar no celular.

import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import { AnimatePresence, motion, useReducedMotion, useScroll, useTransform } from "motion/react";
import { api } from "../api.js";
import { sequencia, surgir } from "../animacoes.js";
import { useSessao } from "../contextos/Sessao.jsx";
import { useDados } from "./Basicos.jsx";
import { Nota, Poster } from "./Filmes.jsx";

const INTERVALO = 7000;
const MAXIMO = 8;

const deslizar = {
  entra: (direcao) => ({ opacity: 0, x: direcao > 0 ? 80 : -80, scale: 1.06 }),
  centro: { opacity: 1, x: 0, scale: 1, transition: { duration: 0.9, ease: [0.22, 1, 0.36, 1] } },
  sai: (direcao) => ({ opacity: 0, x: direcao > 0 ? -80 : 80, transition: { duration: 0.5 } }),
};

export function CarrosselPopulares() {
  const { t, prefs } = useSessao();
  const { dados } = useDados(() => api("/filmes?lista=POPULARES"), [prefs.idioma]);
  const sistemaReduz = useReducedMotion();
  const semMovimento = prefs.reduzir_animacoes || sistemaReduz;

  const todos = dados?.filmes || [];
  const comFundo = todos.filter((f) => f.fundo_url);
  const filmes = (comFundo.length >= 3 ? comFundo : todos).slice(0, MAXIMO);

  const [[indice, direcao], setPosicao] = useState([0, 1]);
  const [pausado, setPausado] = useState(false);
  const raiz = useRef(null);

  const total = filmes.length;
  const atual = total ? filmes[((indice % total) + total) % total] : null;
  const posicao = total ? ((indice % total) + total) % total : 0;

  const ir = useCallback((passo) => setPosicao(([i]) => [i + passo, passo]), []);
  const irPara = (alvo) => setPosicao(([i]) => [alvo, alvo >= ((i % total) + total) % total ? 1 : -1]);

  // Troca automática
  useEffect(() => {
    if (!total || pausado || semMovimento) return;
    const id = setTimeout(() => ir(1), INTERVALO);
    return () => clearTimeout(id);
  }, [indice, total, pausado, semMovimento, ir]);

  // Parallax suave ao rolar a página
  const { scrollY } = useScroll();
  const deslocamento = useTransform(scrollY, [0, 500], [0, 110]);

  if (!atual) return <section className="carrossel carregando" aria-busy="true" />;

  const proximos = Array.from({ length: Math.min(4, total - 1) }, (_, k) => filmes[(posicao + k + 1) % total]);

  return (
    <section
      ref={raiz}
      className={`carrossel ${atual.fundo_url ? "" : "sem-fundo"}`}
      aria-roledescription="carrossel"
      aria-label={t("carrossel.titulo")}
      onMouseEnter={() => setPausado(true)}
      onMouseLeave={() => setPausado(false)}
      onFocus={() => setPausado(true)}
      onBlur={(e) => !raiz.current?.contains(e.relatedTarget) && setPausado(false)}
      onKeyDown={(e) => {
        if (e.key === "ArrowRight") ir(1);
        if (e.key === "ArrowLeft") ir(-1);
      }}
    >
      <AnimatePresence initial={false} custom={direcao} mode="popLayout">
        <motion.div
          key={atual.id}
          className="destaque-fundo"
          custom={direcao}
          variants={deslizar}
          initial="entra"
          animate="centro"
          exit="sai"
          style={{ y: deslocamento, backgroundImage: atual.fundo_url ? `url(${atual.fundo_url})` : undefined }}
          drag="x"
          dragConstraints={{ left: 0, right: 0 }}
          dragElastic={0.25}
          onDragEnd={(_, info) => {
            if (info.offset.x < -80) ir(1);
            else if (info.offset.x > 80) ir(-1);
          }}
        />
      </AnimatePresence>
      <div className="destaque-veu" />

      <motion.div
        className="destaque-texto"
        key={`t-${atual.id}`}
        variants={sequencia}
        initial="inicial"
        animate="visivel"
        role="group"
        aria-roledescription="slide"
        aria-label={`${posicao + 1} / ${total}: ${atual.titulo}`}
      >
        <motion.p variants={surgir} className="carrossel-rotulo">
          🔥 {t("carrossel.titulo")} · #{posicao + 1}
        </motion.p>
        <motion.div variants={surgir} className="destaque-selos">
          <Nota valor={atual.nota} />
          {atual.ano && <span className="selo">{atual.ano}</span>}
          {atual.generos.slice(0, 3).map((g) => <span key={g.id} className="selo">{g.nome}</span>)}
        </motion.div>
        <motion.h2 variants={surgir}>{atual.titulo}</motion.h2>
        <motion.p variants={surgir} className="destaque-sinopse">{atual.sinopse}</motion.p>
        <motion.div variants={surgir} className="acoes">
          <Link to={`/filme/${atual.id}`} className="botao">{t("destaque.ver")} →</Link>
          {atual.origem === "tmdb" && (
            <Link to={`/filme/${atual.id}?trailer=1`} className="botao secundario">▶ {t("destaque.trailer")}</Link>
          )}
        </motion.div>
      </motion.div>

      {!atual.fundo_url && (
        <motion.div className="destaque-poster" key={`p-${atual.id}`}
          initial={{ opacity: 0, rotate: 6, x: 60 }} animate={{ opacity: 1, rotate: -3, x: 0 }}
          transition={{ type: "spring", stiffness: 120, damping: 16 }}>
          <Poster filme={atual} tamanho="grande" compartilhado={false} />
        </motion.div>
      )}

      {/* Miniaturas "A seguir" (só em telas grandes) */}
      {proximos.length > 0 && (
        <div className="carrossel-seguir" aria-hidden="true">
          <span>{t("carrossel.seguir")}</span>
          <div>
            {proximos.map((f, k) => (
              <motion.button
                key={f.id}
                tabIndex={-1}
                className="miniatura"
                onClick={() => ir(k + 1)}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0, transition: { delay: 0.3 + k * 0.08 } }}
                whileHover={{ y: -6, scale: 1.05 }}
              >
                <Poster filme={f} tamanho="pequeno" compartilhado={false} />
              </motion.button>
            ))}
          </div>
        </div>
      )}

      {/* Controles */}
      <div className="carrossel-controles">
        <button className="seta" onClick={() => ir(-1)} aria-label={t("carrossel.anterior")}>‹</button>
        <div className="bolinhas">
          {filmes.map((f, k) => (
            <button
              key={f.id}
              className={k === posicao ? "ativa" : ""}
              aria-label={t("carrossel.ir", { titulo: f.titulo })}
              aria-current={k === posicao}
              onClick={() => irPara(k)}
            >
              {k === posicao && !semMovimento && !pausado && (
                <motion.span
                  key={indice}
                  className="progresso"
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{ duration: INTERVALO / 1000, ease: "linear" }}
                />
              )}
            </button>
          ))}
        </div>
        <button className="seta" onClick={() => ir(1)} aria-label={t("carrossel.proximo")}>›</button>
      </div>
    </section>
  );
}
