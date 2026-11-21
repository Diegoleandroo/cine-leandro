import { useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router";
import { motion } from "motion/react";
import { api } from "../api.js";
import { sequencia, surgir } from "../animacoes.js";
import { useSessao } from "../contextos/Sessao.jsx";
import { ErroDaApi, Pagina, formatarData, useDados } from "../componentes/Basicos.jsx";
import { BotaoAviso, Contagem, Nota, Poster } from "../componentes/Filmes.jsx";
import { JanelaTrailer } from "../componentes/Trailer.jsx";
import { OndeAssistir } from "../componentes/OndeAssistir.jsx";
import { useMeusAvisos } from "./Lancamentos.jsx";

export default function Filme() {
  const { id } = useParams();
  const navegar = useNavigate();
  const [busca, setBusca] = useSearchParams();
  const { t, prefs } = useSessao();
  const { dados: filme, erro, carregando } = useDados(() => api(`/filmes/${id}`), [id, prefs.idioma]);
  const { dados: video } = useDados(() => api(`/filmes/${id}/trailer`), [id, prefs.idioma]);
  const [avisos, mudarAviso] = useMeusAvisos();
  const [trailerAberto, setTrailerAberto] = useState(busca.get("trailer") === "1");

  const fecharTrailer = () => {
    setTrailerAberto(false);
    if (busca.has("trailer")) setBusca({}, { replace: true });
  };

  if (erro) return <Pagina><ErroDaApi erro={erro} /></Pagina>;
  if (carregando || !filme) return <Pagina><div className="esqueleto esqueleto-detalhe" aria-label={t("carregando")} /></Pagina>;

  return (
    <Pagina titulo={filme.titulo} className="larga">
      <div className="detalhe">
        {filme.fundo_url && (
          <motion.div
            className="detalhe-fundo"
            style={{ backgroundImage: `url(${filme.fundo_url})` }}
            initial={{ opacity: 0, scale: 1.1 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1.2 }}
          />
        )}
        <div className="detalhe-veu" />
        <div className="detalhe-interno">
          <button className="voltar" onClick={() => navegar(-1)}>← {t("filme.voltar")}</button>
          <div className="detalhe-grade">
            <div className="detalhe-poster">
              <Poster filme={filme} tamanho="grande" />
            </div>
            <motion.div className="detalhe-info" variants={sequencia} initial="inicial" animate="visivel">
              <motion.div variants={surgir} className="destaque-selos">
                <Nota valor={filme.nota} />
                {filme.classificacao && <span className={`classificacao c${filme.classificacao}`}>{filme.classificacao}</span>}
                {filme.generos.map((g) => <span key={g.id} className="selo">{g.nome}</span>)}
              </motion.div>
              <motion.h1 variants={surgir}>{filme.titulo}</motion.h1>
              {!filme.ja_lancado && <motion.div variants={surgir}><Contagem dias={filme.dias_para_estreia} /></motion.div>}

              <motion.dl variants={surgir} className="ficha">
                <div>
                  <dt>{filme.ja_lancado ? t("filme.lancado") : t("filme.estreia")}</dt>
                  <dd>{formatarData(filme.data_lancamento, prefs.idioma)}</dd>
                </div>
                {filme.duracao_texto && (
                  <div><dt>{t("filme.duracao")}</dt><dd>{filme.duracao_texto}</dd></div>
                )}
                {filme.nota > 0 && (
                  <div><dt>{t("filme.nota")}</dt><dd>{filme.nota.toFixed(1)} / 10</dd></div>
                )}
              </motion.dl>

              <motion.section variants={surgir} aria-labelledby="titulo-sinopse">
                <h2 id="titulo-sinopse" className="titulo-pequeno">{t("filme.sinopse")}</h2>
                <p className="sinopse">{filme.sinopse || t("filme.semSinopse")}</p>
              </motion.section>

              <motion.div variants={surgir}>
                <OndeAssistir filmeId={filme.id} />
              </motion.div>

              <motion.div variants={surgir} className="acoes">
                <motion.button
                  className="botao"
                  disabled={!video?.disponivel}
                  onClick={() => setTrailerAberto(true)}
                  whileHover={video?.disponivel ? { scale: 1.05 } : undefined}
                  whileTap={{ scale: 0.95 }}
                >
                  ▶ {video?.disponivel ? t("filme.trailer") : t("filme.semTrailer")}
                </motion.button>
                {!filme.ja_lancado && <BotaoAviso filme={filme} ativo={avisos.has(filme.id)} aoMudar={mudarAviso} />}
              </motion.div>
            </motion.div>
          </div>
        </div>
      </div>
      <JanelaTrailer trailer={video?.trailer} aberto={trailerAberto && video?.disponivel} aoFechar={fecharTrailer} />
    </Pagina>
  );
}
