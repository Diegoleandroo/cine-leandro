import { useState } from "react";
import { Link } from "react-router";
import { motion } from "motion/react";
import { api } from "../api.js";
import { grade, itemDaGrade, MOLA } from "../animacoes.js";
import { useSessao } from "../contextos/Sessao.jsx";
import { useToast } from "./Basicos.jsx";

// ------------------------------------------------------------ Pôster (imagem ou tipográfico)

const TONS = ["#3b2f63", "#6b2737", "#1f4e5f", "#5c4b1f", "#2f5233", "#4a2c55", "#24395c", "#5a3424"];

function tom(titulo) {
  let h = 2166136261; // FNV-1a: o mesmo título sempre ganha a mesma cor
  for (const c of titulo) h = Math.imul(h ^ c.charCodeAt(0), 16777619) >>> 0;
  return TONS[h % TONS.length];
}

// layoutId liga o pôster da grade ao da página do filme: ao clicar, ele "voa" até lá.
export function Poster({ filme, tamanho = "medio", compartilhado = true }) {
  return (
    <motion.div className={`poster poster-${tamanho}`} layoutId={compartilhado ? `poster-${filme.id}` : undefined} transition={MOLA}>
      {filme.poster_url ? (
        <img src={filme.poster_url} alt="" loading="lazy" />
      ) : (
        <div className="poster-tipografico" style={{ background: tom(filme.titulo) }} aria-hidden="true">
          <span className="poster-genero">{filme.generos[0]?.nome}</span>
          <span className="poster-titulo">{filme.titulo}</span>
          <span className="poster-ano">{filme.ano}</span>
        </div>
      )}
    </motion.div>
  );
}

export function Nota({ valor }) {
  if (!valor) return null;
  const cor = valor >= 7.5 ? "alta" : valor >= 6 ? "media" : "baixa";
  return (
    <span className={`nota nota-${cor}`} aria-label={`${valor.toFixed(1)} / 10`}>
      ★ {valor.toFixed(1)}
    </span>
  );
}

// ------------------------------------------------------------ Contagem regressiva

export function Contagem({ dias }) {
  const { t } = useSessao();
  if (dias <= 0) return null;
  return (
    <motion.span className="contagem" initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={MOLA}>
      {dias === 1 ? t("lanc.amanha") : t("lanc.em", { dias })}
    </motion.span>
  );
}

// ------------------------------------------------------------ Cartaz na grade

export function CartazFilme({ filme, mostrarAviso = false, avisoAtivo, aoMudarAviso }) {
  return (
    <motion.li className="cartaz" variants={itemDaGrade} whileHover={{ y: -8 }} transition={MOLA}>
      <Link to={`/filme/${filme.id}`} className="cartaz-link">
        <div className="cartaz-imagem">
          <Poster filme={filme} />
          <motion.div className="cartaz-brilho" initial={{ opacity: 0 }} whileHover={{ opacity: 1 }} aria-hidden="true" />
          <div className="cartaz-selos">
            <Nota valor={filme.nota} />
          </div>
          {!filme.ja_lancado && <Contagem dias={filme.dias_para_estreia} />}
        </div>
        <h3 className="cartaz-titulo">{filme.titulo}</h3>
        <p className="cartaz-meta">
          {filme.ano && <span>{filme.ano}</span>}
          {filme.generos.slice(0, 2).map((g) => (
            <span key={g.id}>{g.nome}</span>
          ))}
        </p>
      </Link>
      {mostrarAviso && !filme.ja_lancado && (
        <BotaoAviso filme={filme} ativo={avisoAtivo} aoMudar={aoMudarAviso} compacto />
      )}
    </motion.li>
  );
}

export function GradeDeFilmes({ filmes, carregando, ...resto }) {
  if (carregando && !filmes?.length) {
    return (
      <ul className="grade" aria-busy="true">
        {Array.from({ length: 10 }, (_, i) => (
          <li key={i} className="cartaz">
            <div className="esqueleto esqueleto-poster" />
            <div className="esqueleto esqueleto-linha" />
            <div className="esqueleto esqueleto-linha curta" />
          </li>
        ))}
      </ul>
    );
  }
  return (
    <motion.ul className="grade" variants={grade} initial="inicial" animate="visivel" key={filmes?.[0]?.id || "vazia"}>
      {filmes.map((f) => (
        <CartazFilme key={f.id} filme={f} {...(resto.avisos ? {
          mostrarAviso: true,
          avisoAtivo: resto.avisos.has(f.id),
          aoMudarAviso: resto.aoMudarAviso,
        } : {})} />
      ))}
    </motion.ul>
  );
}

// ------------------------------------------------------------ Botão de aviso de estreia

export function BotaoAviso({ filme, ativo, aoMudar, compacto = false }) {
  const { usuario, t } = useSessao();
  const toast = useToast();
  const [ocupado, setOcupado] = useState(false);

  if (!usuario) {
    return (
      <Link to="/entrar" state={{ voltar: `/filme/${filme.id}` }} className={`botao secundario ${compacto ? "pequeno" : ""}`}>
        🔔 {t("aviso.entrar")}
      </Link>
    );
  }

  async function alternar() {
    setOcupado(true);
    try {
      if (ativo) {
        await api(`/avisos/${filme.id}`, { metodo: "DELETE" });
        aoMudar?.(filme.id, false);
      } else {
        await api("/avisos", { metodo: "POST", corpo: { filme_id: filme.id } });
        aoMudar?.(filme.id, true);
        toast(t("aviso.ok", { titulo: filme.titulo }));
      }
    } catch (e) {
      toast(e.message);
    } finally {
      setOcupado(false);
    }
  }

  return (
    <motion.button
      type="button"
      className={`botao ${ativo ? "ativo-aviso" : "secundario"} ${compacto ? "pequeno" : ""}`}
      onClick={alternar}
      disabled={ocupado}
      aria-pressed={Boolean(ativo)}
      whileTap={{ scale: 0.94 }}
    >
      <motion.span
        className="sino"
        aria-hidden="true"
        key={ativo ? "on" : "off"}
        initial={{ rotate: 0 }}
        animate={ativo ? { rotate: [0, -22, 18, -12, 8, 0] } : { rotate: 0 }}
        transition={{ duration: 0.7 }}
      >
        {ativo ? "🔔" : "🔕"}
      </motion.span>
      {ativo ? (compacto ? t("aviso.ativo") : t("aviso.cancelar")) : t("aviso.ativar")}
    </motion.button>
  );
}
