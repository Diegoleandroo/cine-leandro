// Apresentação do Cine Leandro: abre o site para quem ainda não entrou
// e encaminha para a tela de login.
//
// Roteiro (~5 s): contagem regressiva de película (3, 2, 1) → as cortinas se abrem →
// o letreiro CINE LEANDRO aparece letra por letra → slogan → vai para Entrar.
// Com "Reduzir animações" (ou o ajuste do sistema), mostra só o letreiro, sem movimento.

import { useCallback, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useSessao } from "../contextos/Sessao.jsx";

export const CHAVE_APRESENTACAO = "cine.apresentacaoVista";

const DURACAO_CONTAGEM = 1800; // ms
const DURACAO_TOTAL = 5600; // ms até ir para o login

function Contagem() {
  const [numero, setNumero] = useState(3);
  useEffect(() => {
    const id = setInterval(() => setNumero((n) => Math.max(1, n - 1)), DURACAO_CONTAGEM / 3);
    return () => clearInterval(id);
  }, []);
  return (
    <motion.div className="ap-contagem" exit={{ opacity: 0, scale: 1.4, transition: { duration: 0.35 } }} aria-hidden="true">
      <svg viewBox="0 0 200 200">
        <circle cx="100" cy="100" r="88" className="ap-aro" />
        <line x1="100" y1="0" x2="100" y2="200" className="ap-cruz" />
        <line x1="0" y1="100" x2="200" y2="100" className="ap-cruz" />
        <motion.circle
          key={numero}
          cx="100" cy="100" r="70"
          className="ap-varredura"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: DURACAO_CONTAGEM / 3 / 1000, ease: "linear" }}
        />
      </svg>
      <AnimatePresence mode="popLayout">
        <motion.span key={numero} className="ap-numero"
          initial={{ opacity: 0, scale: 0.6 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 1.3 }}>
          {numero}
        </motion.span>
      </AnimatePresence>
    </motion.div>
  );
}

export default function Apresentacao() {
  const { t } = useSessao();
  const navegar = useNavigate();
  const local = useLocation();
  const sistemaReduz = useReducedMotion();
  const { prefs } = useSessao();
  const semMovimento = prefs.reduzir_animacoes || sistemaReduz;
  const [fase, setFase] = useState(semMovimento ? "letreiro" : "contagem");

  const irParaLogin = useCallback(() => {
    try {
      sessionStorage.setItem(CHAVE_APRESENTACAO, "1");
    } catch {
      /* ignora */
    }
    navegar("/entrar", { replace: true, state: local.state });
  }, [navegar, local.state]);

  useEffect(() => {
    document.title = "Cine Leandro";
    if (semMovimento) {
      const id = setTimeout(irParaLogin, 3500);
      return () => clearTimeout(id);
    }
    const a = setTimeout(() => setFase("letreiro"), DURACAO_CONTAGEM);
    const b = setTimeout(irParaLogin, DURACAO_TOTAL);
    return () => {
      clearTimeout(a);
      clearTimeout(b);
    };
  }, [semMovimento, irParaLogin]);

  // Enter, espaço ou Esc pulam a apresentação
  useEffect(() => {
    const tecla = (e) => ["Enter", " ", "Escape"].includes(e.key) && irParaLogin();
    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [irParaLogin]);

  const letras = "LEANDRO".split("");

  return (
    <div className="apresentacao" role="dialog" aria-label="Cine Leandro">
      {/* feixe de luz do projetor */}
      <motion.div className="ap-feixe" aria-hidden="true"
        initial={{ opacity: 0 }} animate={{ opacity: [0, 0.55, 0.35] }} transition={{ duration: 2.4 }} />
      <div className="ap-grao" aria-hidden="true" />

      <AnimatePresence>{fase === "contagem" && <Contagem key="contagem" />}</AnimatePresence>

      {fase === "letreiro" && (
        <>
          {/* cortinas se abrindo */}
          {!semMovimento && (
            <>
              <motion.div className="ap-cortina esquerda" aria-hidden="true"
                initial={{ x: "0%" }} animate={{ x: "-100%" }} transition={{ duration: 1.1, ease: [0.65, 0, 0.35, 1] }} />
              <motion.div className="ap-cortina direita" aria-hidden="true"
                initial={{ x: "0%" }} animate={{ x: "100%" }} transition={{ duration: 1.1, ease: [0.65, 0, 0.35, 1] }} />
            </>
          )}

          <div className="ap-letreiro">
            <h1 className="ap-titulo">
              <motion.span className="ap-cine"
                initial={{ scale: 0, rotate: -12 }} animate={{ scale: 1, rotate: -3 }}
                transition={{ type: "spring", stiffness: 220, damping: 12, delay: 0.55 }}>
                CINE
              </motion.span>
              <span className="ap-leandro" aria-label="LEANDRO">
                {letras.map((l, i) => (
                  <motion.span key={i} aria-hidden="true"
                    initial={{ opacity: 0, y: 40, rotateX: -90 }} animate={{ opacity: 1, y: 0, rotateX: 0 }}
                    transition={{ delay: 0.8 + i * 0.07, type: "spring", stiffness: 260, damping: 18 }}>
                    {l}
                  </motion.span>
                ))}
              </span>
            </h1>
            <motion.p className="ap-slogan" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.5, duration: 0.6 }}>
              {t("apresentacao.slogan")}
            </motion.p>
            <motion.button className="botao" onClick={irParaLogin}
              initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.9 }}
              whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
              {t("apresentacao.entrar")} →
            </motion.button>
            {!semMovimento && (
              <motion.div className="ap-barra" aria-hidden="true"
                initial={{ scaleX: 0 }} animate={{ scaleX: 1 }}
                transition={{ duration: (DURACAO_TOTAL - DURACAO_CONTAGEM) / 1000, ease: "linear" }} />
            )}
          </div>
        </>
      )}

      <button className="ap-pular" onClick={irParaLogin}>{t("apresentacao.pular")}</button>
    </div>
  );
}
