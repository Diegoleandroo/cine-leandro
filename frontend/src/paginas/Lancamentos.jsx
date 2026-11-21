import { useCallback, useEffect, useState } from "react";
import { motion } from "motion/react";
import { api } from "../api.js";
import { sequencia, surgir } from "../animacoes.js";
import { useSessao } from "../contextos/Sessao.jsx";
import { ErroDaApi, Mensagem, Pagina } from "../componentes/Basicos.jsx";
import { GradeDeFilmes } from "../componentes/Filmes.jsx";
import { FiltroGeneros, useListaDeFilmes } from "./Inicio.jsx";

// Ids dos filmes que o usuário já pediu aviso (para pintar o sino de amarelo).
export function useMeusAvisos() {
  const { usuario } = useSessao();
  const [ids, setIds] = useState(new Set());
  useEffect(() => {
    if (!usuario) return setIds(new Set());
    api("/avisos").then((avisos) => setIds(new Set(avisos.map((a) => a.filme_id)))).catch(() => {});
  }, [usuario]);
  const mudar = useCallback((filmeId, ativo) => {
    setIds((atual) => {
      const novo = new Set(atual);
      ativo ? novo.add(filmeId) : novo.delete(filmeId);
      return novo;
    });
  }, []);
  return [ids, mudar];
}

export default function Lancamentos() {
  const { t } = useSessao();
  const [genero, setGenero] = useState("");
  const { filmes, carregando, erro, temMais, carregarMais } = useListaDeFilmes("/filmes/lancamentos", null, genero);
  const [avisos, mudarAviso] = useMeusAvisos();

  return (
    <Pagina titulo={t("lanc.titulo")}>
      <motion.div className="cabecalho-secao" variants={sequencia} initial="inicial" animate="visivel">
        <motion.h1 variants={surgir}>{t("lanc.titulo")}</motion.h1>
        <motion.p variants={surgir} className="sub">{t("lanc.sub")}</motion.p>
      </motion.div>
      <div className="barra-filtros">
        <FiltroGeneros valor={genero} aoMudar={setGenero} />
      </div>
      <ErroDaApi erro={erro} />
      {!carregando && !erro && filmes.length === 0 && <Mensagem tipo="info">{t("lanc.vazio")}</Mensagem>}
      <GradeDeFilmes filmes={filmes} carregando={carregando} avisos={avisos} aoMudarAviso={mudarAviso} />
      {temMais && !carregando && (
        <div className="centro">
          <button className="botao secundario" onClick={carregarMais}>{t("maisFilmes")}</button>
        </div>
      )}
    </Pagina>
  );
}
