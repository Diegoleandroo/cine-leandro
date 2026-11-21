// "Onde assistir": serviços onde o filme está disponível legalmente no Brasil.
// Os dados vêm da JustWatch (via TMDB), e o crédito à JustWatch é obrigatório.

import { motion } from "motion/react";
import { api } from "../api.js";
import { MOLA } from "../animacoes.js";
import { useSessao } from "../contextos/Sessao.jsx";
import { useDados } from "./Basicos.jsx";

const grupoAnim = { inicial: {}, visivel: { transition: { staggerChildren: 0.06 } } };
const logoAnim = {
  inicial: { opacity: 0, scale: 0.6, y: 10 },
  visivel: { opacity: 1, scale: 1, y: 0, transition: MOLA },
};

export function OndeAssistir({ filmeId }) {
  const { t } = useSessao();
  const { dados, carregando } = useDados(() => api(`/filmes/${filmeId}/onde-assistir?regiao=BR`), [filmeId]);

  return (
    <section className="onde-assistir" aria-labelledby="titulo-onde">
      <h2 id="titulo-onde" className="titulo-pequeno">{t("onde.titulo")}</h2>

      {carregando && <div className="esqueleto esqueleto-linha" style={{ width: 240, height: 48 }} />}

      {dados && !dados.disponivel && <p className="onde-vazio">{t("onde.vazio")}</p>}

      {dados?.disponivel && (
        <>
          {dados.grupos.map((g) => (
            <div key={g.tipo} className="onde-grupo">
              <span className="onde-tipo">{t(`onde.${g.tipo}`)}</span>
              <motion.ul variants={grupoAnim} initial="inicial" animate="visivel">
                {g.provedores.map((p) => (
                  <motion.li key={p.id} variants={logoAnim} whileHover={{ y: -4, scale: 1.08 }}>
                    <a
                      href={dados.link || undefined}
                      target="_blank"
                      rel="noopener noreferrer"
                      title={`${p.nome} — ${t(`onde.${g.tipo}`)}`}
                      aria-label={`${p.nome} (${t(`onde.${g.tipo}`)}) — ${t("onde.abre")}`}
                    >
                      {p.logo_url ? <img src={p.logo_url} alt="" /> : <span className="logo-texto">{p.nome}</span>}
                    </a>
                  </motion.li>
                ))}
              </motion.ul>
            </div>
          ))}
          <p className="onde-fonte">
            {t("onde.fonte")}{" "}
            <a href="https://www.justwatch.com" target="_blank" rel="noopener noreferrer">JustWatch</a>
            {dados.link && (
              <>
                {" · "}
                <a href={dados.link} target="_blank" rel="noopener noreferrer">{t("onde.todas")} ↗</a>
              </>
            )}
          </p>
        </>
      )}
    </section>
  );
}
