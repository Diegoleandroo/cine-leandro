import { useEffect, useRef } from "react";
import { AnimatePresence, motion } from "motion/react";
import { useSessao } from "../contextos/Sessao.jsx";

// Janela do trailer: abre "crescendo" a partir do centro e fecha com Esc.
export function JanelaTrailer({ trailer, aberto, aoFechar }) {
  const { t } = useSessao();
  const fechar = useRef(null);

  useEffect(() => {
    if (!aberto) return;
    const anterior = document.activeElement;
    fechar.current?.focus();
    const tecla = (e) => e.key === "Escape" && aoFechar();
    window.addEventListener("keydown", tecla);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", tecla);
      document.body.style.overflow = "";
      anterior?.focus?.();
    };
  }, [aberto, aoFechar]);

  return (
    <AnimatePresence>
      {aberto && trailer && (
        <motion.div
          className="fundo-modal"
          onClick={aoFechar}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-label={trailer.titulo}
            className="modal-trailer"
            onClick={(e) => e.stopPropagation()}
            initial={{ scale: 0.7, opacity: 0, rotateX: 18 }}
            animate={{ scale: 1, opacity: 1, rotateX: 0 }}
            exit={{ scale: 0.85, opacity: 0 }}
            transition={{ type: "spring", stiffness: 220, damping: 24 }}
          >
            <button ref={fechar} className="fechar-modal" onClick={aoFechar} aria-label={t("filme.fechar")}>
              ✕
            </button>
            <div className="video">
              <iframe
                src={`${trailer.url_embed}?autoplay=1&rel=0`}
                title={trailer.titulo}
                allow="autoplay; encrypted-media; picture-in-picture"
                allowFullScreen
              />
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
