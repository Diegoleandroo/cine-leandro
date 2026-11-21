// Contexto global: quem está logado e quais são as preferências.
// Sem login, as preferências ficam no navegador; com login, são salvas na conta.

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, definirIdiomaDaApi, guardarToken, lerToken } from "../api.js";
import { LINGUA_HTML, TEXTOS } from "../i18n/textos.js";

const PADRAO = { tema: "ESCURO", idioma: "PT", tamanho_fonte: "M", reduzir_animacoes: false };
const CHAVE_PREFS = "cine.preferencias";

function prefsDoNavegador() {
  try {
    const salvas = JSON.parse(localStorage.getItem(CHAVE_PREFS) || "null");
    if (salvas) return { ...PADRAO, ...salvas };
  } catch {
    /* ignora */
  }
  const lingua = (navigator.language || "pt").slice(0, 2).toUpperCase();
  const tema = window.matchMedia?.("(prefers-contrast: more)").matches ? "ALTO_CONTRASTE" : PADRAO.tema;
  return { ...PADRAO, tema, idioma: ["PT", "EN", "ES"].includes(lingua) ? lingua : "PT" };
}

const Contexto = createContext(null);

export function SessaoProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  const [carregandoUsuario, setCarregandoUsuario] = useState(Boolean(lerToken()));
  const [prefs, setPrefs] = useState(prefsDoNavegador);
  // Vale já na primeira renderização: as páginas filhas buscam dados antes dos efeitos daqui.
  definirIdiomaDaApi(prefs.idioma);

  // Aplica as preferências no <html>: o CSS reage aos atributos data-*.
  useEffect(() => {
    const html = document.documentElement;
    html.dataset.tema = prefs.tema;
    html.dataset.fonte = prefs.tamanho_fonte;
    html.dataset.reduzir = prefs.reduzir_animacoes ? "sim" : "nao";
    html.lang = LINGUA_HTML[prefs.idioma];
    definirIdiomaDaApi(prefs.idioma);
    try {
      localStorage.setItem(CHAVE_PREFS, JSON.stringify(prefs));
    } catch {
      /* ignora */
    }
  }, [prefs]);

  // Ao abrir o site com um token guardado, descobre quem é o usuário.
  useEffect(() => {
    if (!lerToken()) return;
    api("/auth/eu")
      .then((u) => {
        setUsuario(u);
        setPrefs(u.preferencias);
      })
      .catch(() => guardarToken(null))
      .finally(() => setCarregandoUsuario(false));
  }, []);

  // Se a API disser que a sessão acabou, limpa tudo; as rotas privadas levam ao login.
  useEffect(() => {
    const encerrar = () => {
      guardarToken(null);
      setUsuario(null);
    };
    window.addEventListener("cine:sessao-encerrada", encerrar);
    return () => window.removeEventListener("cine:sessao-encerrada", encerrar);
  }, []);

  const entrarComSessao = useCallback((sessao) => {
    guardarToken(sessao.token);
    setUsuario(sessao.usuario);
    setPrefs(sessao.usuario.preferencias);
  }, []);

  const sair = useCallback(async () => {
    await api("/auth/logout", { metodo: "POST" }).catch(() => {});
    guardarToken(null);
    setUsuario(null);
  }, []);

  const mudarPrefs = useCallback(
    async (mudancas) => {
      if (mudancas.idioma) definirIdiomaDaApi(mudancas.idioma);
      setPrefs((atual) => ({ ...atual, ...mudancas })); // muda na hora (otimista)
      if (usuario) {
        const salvas = await api("/preferencias", { metodo: "PUT", corpo: mudancas });
        setPrefs(salvas);
      }
    },
    [usuario]
  );

  const t = useCallback(
    (chave, vars = {}) => {
      const texto = TEXTOS[prefs.idioma]?.[chave] ?? TEXTOS.PT[chave] ?? chave;
      return texto.replace(/\{(\w+)\}/g, (_, nome) => vars[nome] ?? "");
    },
    [prefs.idioma]
  );

  const valor = useMemo(
    () => ({ usuario, carregandoUsuario, prefs, mudarPrefs, entrarComSessao, sair, t }),
    [usuario, carregandoUsuario, prefs, mudarPrefs, entrarComSessao, sair, t]
  );
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export const useSessao = () => useContext(Contexto);
