import { Link, Navigate } from "react-router";
import { AnimatePresence, motion } from "motion/react";
import { api } from "../api.js";
import { MOLA, sequencia, surgir } from "../animacoes.js";
import { useSessao } from "../contextos/Sessao.jsx";
import { TEXTOS } from "../i18n/textos.js";
import { ErroDaApi, Mensagem, Pagina, Segmentado, formatarData, useDados, useToast } from "../componentes/Basicos.jsx";

// ------------------------------------------------------------ Preferências

export function Preferencias() {
  const { t, prefs, mudarPrefs, usuario } = useSessao();
  const toast = useToast();
  const mudar = async (m) => {
    try {
      await mudarPrefs(m);
      toast(TEXTOS[m.idioma || prefs.idioma]["pref.salvo"]); // já no idioma novo
    } catch (e) {
      toast(e.message);
    }
  };
  return (
    <Pagina titulo={t("pref.titulo")} className="media">
      <motion.div variants={sequencia} initial="inicial" animate="visivel">
        <motion.h1 variants={surgir}>{t("pref.titulo")}</motion.h1>
        <motion.p variants={surgir} className="sub">
          {t("pref.sub", { onde: usuario ? t("pref.ondeConta") : t("pref.ondeLocal") })}
        </motion.p>

        <motion.section variants={surgir} className="bloco-pref">
          <h2>{t("pref.tema")}</h2>
          <div className="temas">
            {["ESCURO", "CLARO", "ALTO_CONTRASTE"].map((tema) => (
              <motion.button
                key={tema}
                type="button"
                className={`amostra amostra-${tema} ${prefs.tema === tema ? "ativo" : ""}`}
                aria-pressed={prefs.tema === tema}
                onClick={() => mudar({ tema })}
                whileHover={{ y: -4 }}
                whileTap={{ scale: 0.96 }}
              >
                <span className="amostra-tela" aria-hidden="true"><i /><i /><i /></span>
                {t(`pref.${tema}`)}
                {prefs.tema === tema && <motion.span layoutId="check-tema" className="check" transition={MOLA}>✓</motion.span>}
              </motion.button>
            ))}
          </div>
        </motion.section>

        <motion.section variants={surgir} className="bloco-pref">
          <h2>{t("pref.idioma")}</h2>
          <Segmentado
            grupo="idioma"
            rotulo={t("pref.idioma")}
            valor={prefs.idioma}
            aoMudar={(idioma) => mudar({ idioma })}
            opcoes={[
              { valor: "PT", rotulo: "🇧🇷 Português" },
              { valor: "EN", rotulo: "🇺🇸 English" },
              { valor: "ES", rotulo: "🇪🇸 Español" },
            ]}
          />
        </motion.section>

        <motion.section variants={surgir} className="bloco-pref">
          <h2>{t("pref.acess")}</h2>
          <h3>{t("pref.fonte")}</h3>
          <Segmentado
            grupo="fonte"
            rotulo={t("pref.fonte")}
            valor={prefs.tamanho_fonte}
            aoMudar={(tamanho_fonte) => mudar({ tamanho_fonte })}
            opcoes={["P", "M", "G"].map((v) => ({ valor: v, rotulo: t(`pref.${v}`) }))}
          />
          <label className="interruptor">
            <input
              type="checkbox"
              role="switch"
              checked={prefs.reduzir_animacoes}
              onChange={(e) => mudar({ reduzir_animacoes: e.target.checked })}
            />
            <span className="trilho" aria-hidden="true">
              <motion.span className="bolinha" layout transition={MOLA} />
            </span>
            <span>
              <strong>{t("pref.animacoes")}</strong>
              <small>{t("pref.animacoesDica")}</small>
            </span>
          </label>
        </motion.section>
      </motion.div>
    </Pagina>
  );
}

// ------------------------------------------------------------ Meus avisos

export function MeusAvisos() {
  const { t, usuario, carregandoUsuario, prefs } = useSessao();
  const { dados, erro, recarregar } = useDados(() => (usuario ? api("/avisos") : Promise.resolve([])), [usuario]);
  if (!carregandoUsuario && !usuario) return <Navigate to="/entrar" state={{ voltar: "/avisos" }} replace />;

  const cancelar = async (filmeId) => {
    await api(`/avisos/${filmeId}`, { metodo: "DELETE" });
    recarregar();
  };

  return (
    <Pagina titulo={t("avisos.titulo")} className="media">
      <h1>{t("avisos.titulo")}</h1>
      <ErroDaApi erro={erro} />
      {dados?.length === 0 && (
        <Mensagem tipo="info">
          {t("avisos.vazio")} <Link to="/lancamentos">{t("menu.lancamentos")} →</Link>
        </Mensagem>
      )}
      <motion.ul className="lista-avisos" variants={sequencia} initial="inicial" animate="visivel">
        <AnimatePresence>
          {dados?.map((a) => (
            <motion.li
              key={a.id}
              layout
              variants={surgir}
              exit={{ opacity: 0, x: 80, height: 0, marginBottom: 0, transition: { duration: 0.25 } }}
              className={`aviso ${a.enviado ? "enviado" : ""}`}
            >
              <div className="aviso-data" aria-hidden="true">
                <span className="dia">{a.data_lancamento.slice(8, 10)}</span>
                <span className="mes">{new Date(`${a.data_lancamento}T12:00`).toLocaleDateString(prefs.idioma === "EN" ? "en" : prefs.idioma.toLowerCase(), { month: "short" })}</span>
              </div>
              <div className="aviso-info">
                <Link to={`/filme/${a.filme_id}`}><strong>{a.filme_titulo}</strong></Link>
                <span>{formatarData(a.data_lancamento, prefs.idioma)}</span>
                <span className="selo">
                  {a.enviado ? `✉️ ${t("avisos.enviado")}` : a.dias_para_estreia === 0 ? t("avisos.hoje") : t("avisos.faltam", { dias: a.dias_para_estreia })}
                </span>
              </div>
              {!a.enviado && (
                <button className="botao fantasma pequeno" onClick={() => cancelar(a.filme_id)}>{t("aviso.cancelar")}</button>
              )}
            </motion.li>
          ))}
        </AnimatePresence>
      </motion.ul>
    </Pagina>
  );
}

// ------------------------------------------------------------ Como funciona (Arquitetura Limpa)

const CORES = ["#ffb3a7", "#ffd98a", "#a8e6a1", "#8fd3f4"];

export function ComoFunciona() {
  const { t } = useSessao();
  const { dados, erro } = useDados(() => api("/sistema"), []);
  return (
    <Pagina titulo={t("como.titulo")}>
      <h1>{t("como.titulo")}</h1>
      <p className="sub">{t("como.sub")}</p>
      <ErroDaApi erro={erro} />
      {dados && (
        <div className="arquitetura">
          <div className="circulos" aria-hidden="true">
            {[...dados.camadas].reverse().map((c, i) => (
              <motion.div
                key={c.nome}
                className="circulo"
                style={{ background: CORES[3 - i], width: `${100 - i * 22}%`, height: `${100 - i * 22}%` }}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ ...MOLA, delay: i * 0.15 }}
              >
                <span>{c.nome}</span>
              </motion.div>
            ))}
          </div>
          <motion.div className="camadas" variants={sequencia} initial="inicial" animate="visivel">
            {dados.camadas.map((c, i) => (
              <motion.section key={c.nome} variants={surgir} className="camada" style={{ borderColor: CORES[i] }}>
                <h2>{c.nome} <code>{c.pasta}</code></h2>
                <p>{c.itens.join(" · ")}</p>
              </motion.section>
            ))}
            <motion.p variants={surgir}><strong>{t("como.catalogo")}:</strong> {dados.catalogo}</motion.p>
          </motion.div>
        </div>
      )}
    </Pagina>
  );
}

export function NaoEncontrada() {
  const { t } = useSessao();
  return (
    <Pagina className="estreita">
      <motion.div className="centro" initial={{ rotate: -8, scale: 0.8 }} animate={{ rotate: 0, scale: 1 }} transition={MOLA}>
        <p className="numero-404">404</p>
        <p>{t("erro.404")}</p>
        <Link to="/" className="botao">{t("menu.inicio")}</Link>
      </motion.div>
    </Pagina>
  );
}

export { ErroDaApi };
