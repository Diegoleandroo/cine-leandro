import { useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router";
import { motion } from "motion/react";
import { api } from "../api.js";
import { sequencia, surgir } from "../animacoes.js";
import { useSessao } from "../contextos/Sessao.jsx";
import { Mensagem, Pagina, useDados, useToast } from "../componentes/Basicos.jsx";

// Lado esquerdo das telas de acesso: a "vitrine" do Cine Leandro.
// Mostra os pôsteres dos PRÓXIMOS LANÇAMENTOS (rota pública /api/vitrine), descendo
// devagar em três colunas. Sem TMDB (ou sem lançamentos), usa cartazes ilustrativos.
const CORES_VITRINE = ["#3b2f63", "#6b2737", "#1f4e5f", "#5c4b1f", "#2f5233", "#4a2c55", "#24395c", "#5a3424"];

function dataCurta(iso, idioma) {
  if (!iso) return "";
  const locale = { PT: "pt-BR", EN: "en-US", ES: "es-ES" }[idioma];
  return new Date(`${iso}T12:00:00`).toLocaleDateString(locale, { day: "2-digit", month: "short" });
}

function Vitrine() {
  const { t, prefs } = useSessao();
  const { dados } = useDados(() => api("/vitrine"), [prefs.idioma]);
  const lancamentos = dados?.filmes || [];
  const temPosters = lancamentos.length >= 3;

  // Cada coluna recebe uma parte dos filmes, repetida para a animação não ter "buraco".
  const colunas = [0, 1, 2].map((c) => {
    if (!temPosters) return [...CORES_VITRINE, ...CORES_VITRINE].map((cor, i) => ({ cor, icone: ["🎬", "🍿", "🎞️", "⭐"][(i + c) % 4] }));
    let parte = lancamentos.filter((_, i) => i % 3 === c);
    if (!parte.length) parte = lancamentos;
    while (parte.length < 6) parte = [...parte, ...parte];
    return [...parte, ...parte];
  });

  return (
    <div className={`vitrine ${temPosters ? "com-posters" : ""}`} aria-hidden="true">
      <div className="vitrine-colunas">
        {colunas.map((itens, c) => (
          <motion.div
            key={`${c}-${temPosters}`}
            className="vitrine-coluna"
            animate={{ y: c % 2 ? ["-50%", "0%"] : ["0%", "-50%"] }}
            transition={{ duration: 46 + c * 8, repeat: Infinity, ease: "linear" }}
          >
            {itens.map((item, i) =>
              temPosters ? (
                <span key={i} className="vitrine-cartaz vitrine-poster">
                  <img src={item.poster_url} alt="" loading="lazy" />
                  {item.data_lancamento && <b>{dataCurta(item.data_lancamento, prefs.idioma)}</b>}
                </span>
              ) : (
                <span key={i} className="vitrine-cartaz" style={{ background: `linear-gradient(160deg, ${item.cor}, #0c0c0c)` }}>
                  <i>{item.icone}</i>
                </span>
              )
            )}
          </motion.div>
        ))}
      </div>
      <div className="vitrine-texto">
        <motion.p className="vitrine-marca" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <span className="marca-cine">CINE</span> LEANDRO
        </motion.p>
        {temPosters && (
          <motion.p className="vitrine-chamada" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
            🎟️ {t("acesso.emBreve")}
          </motion.p>
        )}
        <motion.h2 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.15 }}>
          {t("acesso.slogan")}
        </motion.h2>
        <motion.ul initial="inicial" animate="visivel" variants={sequencia}>
          {["acesso.item1", "acesso.item2", "acesso.item3"].map((k) => (
            <motion.li key={k} variants={surgir}>{t(k)}</motion.li>
          ))}
        </motion.ul>
      </div>
    </div>
  );
}

function Formulario({ titulo, sub, children, aoEnviar, botao, erro, sucesso, rodape }) {
  const { t } = useSessao();
  const [enviando, setEnviando] = useState(false);
  async function enviar(e) {
    e.preventDefault();
    setEnviando(true);
    try {
      await aoEnviar(new FormData(e.currentTarget));
    } finally {
      setEnviando(false);
    }
  }
  return (
    <Pagina titulo={titulo} className="larga">
      <div className="acesso">
        <Vitrine />
        <div className="acesso-form">
          <motion.form className="cartao-form" onSubmit={enviar} variants={sequencia} initial="inicial" animate="visivel" noValidate>
            <motion.h1 variants={surgir}>{titulo}</motion.h1>
            <motion.p variants={surgir} className="sub">{sub}</motion.p>
            {erro && <Mensagem>{erro}</Mensagem>}
            {sucesso && <Mensagem tipo="sucesso">{sucesso}</Mensagem>}
            <motion.div variants={surgir} className="campos">{children}</motion.div>
            <motion.button variants={surgir} className="botao largo" disabled={enviando} whileTap={{ scale: 0.97 }}>
              {enviando ? t("conta.aguarde") : botao}
            </motion.button>
            {rodape && <motion.p variants={surgir} className="rodape-form">{rodape}</motion.p>}
          </motion.form>
        </div>
      </div>
    </Pagina>
  );
}

function Campo({ rotulo, dica, erro, ...props }) {
  const id = `campo-${props.name}`;
  return (
    <div className="campo">
      <label htmlFor={id}>{rotulo}</label>
      <input id={id} aria-invalid={Boolean(erro)} aria-describedby={dica ? `${id}-dica` : undefined} {...props} />
      {dica && <small id={`${id}-dica`}>{dica}</small>}
    </div>
  );
}

// O "olhinho": mostra a senha por um momento, para conferir o que foi digitado.
function CampoSenha({ rotulo, dica, ...props }) {
  const { t } = useSessao();
  const [visivel, setVisivel] = useState(false);
  const [mudou, setMudou] = useState(false);
  const id = `campo-${props.name}`;
  return (
    <div className="campo">
      <label htmlFor={id}>{rotulo}</label>
      <div className="campo-senha">
        <input
          id={id}
          type={visivel ? "text" : "password"}
          aria-describedby={dica ? `${id}-dica` : undefined}
          autoCapitalize="none"
          autoCorrect="off"
          spellCheck={false}
          {...props}
        />
        <button
          type="button"
          className="olhinho"
          aria-controls={id}
          aria-pressed={visivel}
          aria-label={visivel ? t("conta.ocultarSenha") : t("conta.mostrarSenha")}
          title={visivel ? t("conta.ocultarSenha") : t("conta.mostrarSenha")}
          onClick={() => {
            setVisivel((v) => !v);
            setMudou(true);
          }}
        >
          <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" focusable="false">
            <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
            <circle cx="12" cy="12" r="3.2" fill="none" stroke="currentColor" strokeWidth="1.8" />
            {!visivel && <path d="M4 20 20 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />}
          </svg>
        </button>
      </div>
      {dica && <small id={`${id}-dica`}>{dica}</small>}
      {/* Leitores de tela ouvem quando a senha passa a aparecer ou some */}
      <span className="sr-only" aria-live="polite">{mudou ? t(visivel ? "conta.senhaVisivel" : "conta.senhaOculta") : ""}</span>
    </div>
  );
}

function mensagemDe(e, t) {
  if (e.codigo === "rede") return t("erro.rede");
  if (e.codigo === "muitas_tentativas") return t("erro.muitasTentativas");
  return e.message;
}

export function Entrar() {
  const { t, entrarComSessao } = useSessao();
  const navegar = useNavigate();
  const local = useLocation();
  const [erro, setErro] = useState(null);
  return (
    <Formulario
      titulo={t("conta.entrar")}
      sub={t("conta.entrarSub")}
      botao={t("conta.entrar")}
      erro={erro}
      aoEnviar={async (f) => {
        try {
          entrarComSessao(await api("/auth/login", { metodo: "POST", corpo: { email: f.get("email"), senha: f.get("senha") } }));
          navegar(local.state?.voltar || "/");
        } catch (e) {
          setErro(mensagemDe(e, t));
        }
      }}
      rodape={
        <>
          <Link to="/recuperar-senha">{t("conta.esqueci")}</Link> · {t("conta.semConta")} <Link to="/cadastrar" state={local.state}>{t("conta.criar")}</Link>
        </>
      }
    >
      <Campo rotulo={t("conta.email")} name="email" type="email" autoComplete="email" required />
      <CampoSenha rotulo={t("conta.senha")} name="senha" autoComplete="current-password" required />
    </Formulario>
  );
}

export function Cadastrar() {
  const { t, prefs, entrarComSessao } = useSessao();
  const navegar = useNavigate();
  const local = useLocation();
  const toast = useToast();
  const [erro, setErro] = useState(null);
  return (
    <Formulario
      titulo={t("conta.criar")}
      sub={t("conta.criarSub")}
      botao={t("conta.criar")}
      erro={erro}
      aoEnviar={async (f) => {
        try {
          const sessao = await api("/auth/cadastro", {
            metodo: "POST",
            corpo: { nome: f.get("nome"), email: f.get("email"), senha: f.get("senha"), preferencias: prefs },
          });
          entrarComSessao(sessao);
          toast(t("menu.ola", { nome: sessao.usuario.primeiro_nome }) + " 🎬");
          navegar(local.state?.voltar || "/");
        } catch (e) {
          setErro(mensagemDe(e, t));
        }
      }}
      rodape={<>{t("conta.temConta")} <Link to="/entrar" state={local.state}>{t("conta.entrar")}</Link></>}
    >
      <Campo rotulo={t("conta.nome")} name="nome" autoComplete="name" required />
      <Campo rotulo={t("conta.email")} name="email" type="email" autoComplete="email" required />
      <CampoSenha rotulo={t("conta.senha")} name="senha" autoComplete="new-password" dica={t("conta.senhaDica")} required />
    </Formulario>
  );
}

export function RecuperarSenha() {
  const { t } = useSessao();
  const [erro, setErro] = useState(null);
  const [sucesso, setSucesso] = useState(null);
  return (
    <Formulario
      titulo={t("conta.recuperar")}
      sub={t("conta.recuperarSub")}
      botao={t("conta.enviarLink")}
      erro={erro}
      sucesso={sucesso}
      aoEnviar={async (f) => {
        try {
          setErro(null);
          setSucesso((await api("/auth/recuperar-senha", { metodo: "POST", corpo: { email: f.get("email") } })).mensagem);
        } catch (e) {
          setErro(mensagemDe(e, t));
        }
      }}
      rodape={<Link to="/entrar">← {t("conta.entrar")}</Link>}
    >
      <Campo rotulo={t("conta.email")} name="email" type="email" autoComplete="email" required />
    </Formulario>
  );
}

export function RedefinirSenha() {
  const { t } = useSessao();
  const [busca] = useSearchParams();
  const navegar = useNavigate();
  const toast = useToast();
  const [erro, setErro] = useState(null);
  return (
    <Formulario
      titulo={t("conta.redefinir")}
      sub={t("conta.senhaDica")}
      botao={t("conta.salvar")}
      erro={erro}
      aoEnviar={async (f) => {
        try {
          const r = await api("/auth/redefinir-senha", {
            metodo: "POST",
            corpo: { token: busca.get("token") || "", nova_senha: f.get("senha") },
          });
          toast(r.mensagem);
          navegar("/entrar");
        } catch (e) {
          setErro(mensagemDe(e, t));
        }
      }}
    >
      <CampoSenha rotulo={t("conta.novaSenha")} name="senha" autoComplete="new-password" required />
    </Formulario>
  );
}
