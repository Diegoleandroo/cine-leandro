import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { api } from "../api.js";
import { sequencia, surgir } from "../animacoes.js";
import { useSessao } from "../contextos/Sessao.jsx";
import { ErroDaApi, Pagina, Segmentado, useDados } from "../componentes/Basicos.jsx";
import { GradeDeFilmes } from "../componentes/Filmes.jsx";
import { CarrosselPopulares } from "../componentes/Carrossel.jsx";

const LISTAS = ["EM_CARTAZ", "POPULARES", "MAIS_BEM_AVALIADOS"];

// Filtro de categorias + paginação "carregar mais", usado aqui e em Lançamentos.
export function useListaDeFilmes(caminhoBase, lista, genero) {
  const [pagina, setPagina] = useState(1);
  const [filmes, setFilmes] = useState([]);
  const [total, setTotal] = useState(1);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState(null);
  const { prefs } = useSessao();

  useEffect(() => {
    setPagina(1);
    setFilmes([]);
  }, [lista, genero, prefs.idioma]);

  useEffect(() => {
    let vivo = true;
    const p = new URLSearchParams({ pagina });
    if (lista) p.set("lista", lista);
    if (genero) p.set("genero", genero);
    setCarregando(true);
    api(`${caminhoBase}?${p}`)
      .then((r) => {
        if (!vivo) return;
        setFilmes((atuais) => (pagina === 1 ? r.filmes : [...atuais, ...r.filmes.filter((f) => !atuais.some((a) => a.id === f.id))]));
        setTotal(r.total_paginas);
        setErro(null);
      })
      .catch((e) => vivo && setErro(e))
      .finally(() => vivo && setCarregando(false));
    return () => (vivo = false);
  }, [caminhoBase, lista, genero, pagina, prefs.idioma]);

  return { filmes, carregando, erro, temMais: pagina < total, carregarMais: () => setPagina((n) => n + 1) };
}

export function FiltroGeneros({ valor, aoMudar }) {
  const { t, prefs } = useSessao();
  const { dados: generos } = useDados(() => api("/filmes/generos"), [prefs.idioma]);
  return (
    <label className="filtro">
      <span className="sr-only">{t("filtro.rotulo")}</span>
      <select value={valor} onChange={(e) => aoMudar(e.target.value)} aria-label={t("filtro.rotulo")}>
        <option value="">{t("filtro.todos")}</option>
        {generos?.map((g) => (
          <option key={g.id} value={g.id}>{g.nome}</option>
        ))}
      </select>
    </label>
  );
}

export default function Inicio() {
  const { t } = useSessao();
  const [lista, setLista] = useState("EM_CARTAZ");
  const [genero, setGenero] = useState("");
  const { filmes, carregando, erro, temMais, carregarMais } = useListaDeFilmes("/filmes", lista, genero);

  return (
    <Pagina titulo={t("menu.inicio")} className="larga">
      <CarrosselPopulares />
      <div className="conteudo">
        <motion.div className="cabecalho-secao" variants={sequencia} initial="inicial" animate="visivel">
          <motion.h1 variants={surgir}>{t("inicio.titulo")}</motion.h1>
          <motion.p variants={surgir} className="sub">{t("inicio.sub")}</motion.p>
        </motion.div>
        <div className="barra-filtros">
          <Segmentado
            grupo="listas"
            rotulo={t("menu.inicio")}
            valor={lista}
            aoMudar={setLista}
            opcoes={LISTAS.map((l) => ({ valor: l, rotulo: t(`lista.${l}`) }))}
          />
          <FiltroGeneros valor={genero} aoMudar={setGenero} />
        </div>
        <ErroDaApi erro={erro} />
        <GradeDeFilmes filmes={filmes} carregando={carregando} />
        {temMais && !carregando && (
          <div className="centro">
            <motion.button className="botao secundario" onClick={carregarMais} whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }}>
              {t("maisFilmes")}
            </motion.button>
          </div>
        )}
      </div>
    </Pagina>
  );
}
