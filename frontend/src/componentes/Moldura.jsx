import { Link, NavLink, useNavigate } from "react-router";
import { motion } from "motion/react";
import { useSessao } from "../contextos/Sessao.jsx";
import { useDados } from "./Basicos.jsx";
import { api } from "../api.js";

const LINKS = [
  { para: "/", chave: "menu.inicio" },
  { para: "/lancamentos", chave: "menu.lancamentos" },
  { para: "/avisos", chave: "menu.avisos" },
  { para: "/preferencias", chave: "menu.preferencias" },
  { para: "/como-funciona", chave: "menu.como" },
];

const TEMAS = ["ESCURO", "CLARO", "ALTO_CONTRASTE"];
const ICONE_TEMA = { ESCURO: "🌙", CLARO: "☀️", ALTO_CONTRASTE: "◐" };

// Antes do login: idioma e tema continuam ao alcance (ficam salvos no navegador).
function AjustesRapidos() {
  const { prefs, mudarPrefs, t } = useSessao();
  const proximoTema = TEMAS[(TEMAS.indexOf(prefs.tema) + 1) % TEMAS.length];
  return (
    <div className="ajustes-rapidos">
      <label className="sr-only" htmlFor="idioma-rapido">{t("pref.idioma")}</label>
      <select id="idioma-rapido" value={prefs.idioma} onChange={(e) => mudarPrefs({ idioma: e.target.value })}>
        <option value="PT">🇧🇷 PT</option>
        <option value="EN">🇺🇸 EN</option>
        <option value="ES">🇪🇸 ES</option>
      </select>
      <motion.button
        type="button"
        className="botao fantasma pequeno"
        onClick={() => mudarPrefs({ tema: proximoTema })}
        aria-label={`${t("pref.tema")}: ${t(`pref.${prefs.tema}`)}`}
        whileTap={{ rotate: 180 }}
      >
        {ICONE_TEMA[prefs.tema]}
      </motion.button>
    </div>
  );
}

export function Topo() {
  const { usuario, sair, t } = useSessao();
  const navegar = useNavigate();
  return (
    <header className="topo">
      <a href="#conteudo" className="pular">{t("pular")}</a>
      <div className="topo-interno">
        <Link to={usuario ? "/" : "/entrar"} className="marca" aria-label="Cine Leandro">
          <motion.span className="marca-cine" whileHover={{ rotate: -4, scale: 1.08 }}>CINE</motion.span>
          <span>LEANDRO</span>
        </Link>
        {usuario ? (
          <>
            <nav className="menu" aria-label="Principal">
              {LINKS.map((l) => (
                <NavLink key={l.para} to={l.para} end={l.para === "/"}>
                  {({ isActive }) => (
                    <>
                      {t(l.chave)}
                      {isActive && <motion.span layoutId="sublinhado" className="sublinhado" />}
                    </>
                  )}
                </NavLink>
              ))}
            </nav>
            <div className="conta">
              <span className="ola">{t("menu.ola", { nome: usuario.primeiro_nome })}</span>
              <button
                className="botao fantasma pequeno"
                onClick={async () => {
                  await sair();
                  navegar("/entrar", { replace: true });
                }}
              >
                {t("menu.sair")}
              </button>
            </div>
          </>
        ) : (
          <AjustesRapidos />
        )}
      </div>
    </header>
  );
}

export function Rodape() {
  const { t } = useSessao();
  const { dados } = useDados(() => api("/sistema"), []);
  return (
    <footer className="rodape">
      <p>{dados && !dados.tem_tmdb ? t("rodape.local") : t("rodape.tmdb")}</p>
      <p className="rodape-pilha">React · Motion · Django · PostgreSQL · AWS</p>
    </footer>
  );
}
