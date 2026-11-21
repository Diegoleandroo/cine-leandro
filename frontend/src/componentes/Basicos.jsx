import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { pagina } from "../animacoes.js";
import { useSessao } from "../contextos/Sessao.jsx";

// ------------------------------------------------------------ Página com transição

export function Pagina({ children, className = "", titulo }) {
  useEffect(() => {
    if (titulo) document.title = `${titulo} · Cine Leandro`;
  }, [titulo]);
  return (
    <motion.div className={`pagina ${className}`} variants={pagina} initial="inicial" animate="visivel" exit="saida">
      {children}
    </motion.div>
  );
}

// ------------------------------------------------------------ Carregar dados da API

export function useDados(carregar, deps) {
  const [estado, setEstado] = useState({ dados: null, erro: null, carregando: true });
  const recarregar = useCallback(() => {
    let vivo = true;
    setEstado((e) => ({ ...e, carregando: true, erro: null }));
    carregar()
      .then((dados) => vivo && setEstado({ dados, erro: null, carregando: false }))
      .catch((erro) => vivo && setEstado({ dados: null, erro, carregando: false }));
    return () => (vivo = false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(recarregar, [recarregar]);
  return { ...estado, recarregar };
}

// ------------------------------------------------------------ Mensagens

export function Mensagem({ tipo = "erro", children }) {
  return (
    <motion.div
      role={tipo === "erro" ? "alert" : "status"}
      className={`mensagem mensagem-${tipo}`}
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: [-8, 6, -3, 0] }}
      transition={{ duration: 0.4 }}
    >
      {children}
    </motion.div>
  );
}

export function ErroDaApi({ erro }) {
  const { t } = useSessao();
  if (!erro) return null;
  return <Mensagem>{erro.codigo === "rede" ? t("erro.rede") : erro.message}</Mensagem>;
}

// ------------------------------------------------------------ Toasts (avisos rápidos)

const ToastCtx = createContext(() => {});

export function ToastProvider({ children }) {
  const [itens, setItens] = useState([]);
  const mostrar = useCallback((texto) => {
    const id = Math.random().toString(36).slice(2);
    setItens((l) => [...l, { id, texto }]);
    setTimeout(() => setItens((l) => l.filter((i) => i.id !== id)), 3800);
  }, []);
  return (
    <ToastCtx.Provider value={mostrar}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        <AnimatePresence>
          {itens.map((i) => (
            <motion.div
              key={i.id}
              className="toast"
              layout
              initial={{ opacity: 0, y: 30, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: 60, transition: { duration: 0.2 } }}
            >
              {i.texto}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastCtx.Provider>
  );
}

export const useToast = () => useContext(ToastCtx);

// ------------------------------------------------------------ Controle segmentado (abas / opções)

export function Segmentado({ rotulo, opcoes, valor, aoMudar, grupo }) {
  return (
    <div className="segmentado" role="radiogroup" aria-label={rotulo}>
      {opcoes.map((o) => {
        const ativo = o.valor === valor;
        return (
          <button
            key={o.valor}
            type="button"
            role="radio"
            aria-checked={ativo}
            className={ativo ? "ativo" : ""}
            onClick={() => aoMudar(o.valor)}
          >
            {ativo && <motion.span layoutId={`pilula-${grupo}`} className="pilula" transition={{ type: "spring", stiffness: 380, damping: 32 }} />}
            <span className="rotulo-seg">{o.rotulo}</span>
          </button>
        );
      })}
    </div>
  );
}

// ------------------------------------------------------------ Datas no idioma do usuário

export function formatarData(iso, idioma) {
  if (!iso) return "—";
  const locale = { PT: "pt-BR", EN: "en-US", ES: "es-ES" }[idioma];
  return new Date(`${iso}T12:00:00`).toLocaleDateString(locale, { day: "numeric", month: "long", year: "numeric" });
}
