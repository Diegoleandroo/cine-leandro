import { useRef } from "react";
import { AnimatePresence, LayoutGroup, MotionConfig } from "motion/react";
import { Navigate, Route, Routes, useLocation } from "react-router";
import { useSessao } from "./contextos/Sessao.jsx";
import { ToastProvider } from "./componentes/Basicos.jsx";
import { Rodape, Topo } from "./componentes/Moldura.jsx";
import Inicio from "./paginas/Inicio.jsx";
import Lancamentos from "./paginas/Lancamentos.jsx";
import Filme from "./paginas/Filme.jsx";
import { Cadastrar, Entrar, RecuperarSenha, RedefinirSenha } from "./paginas/Conta.jsx";
import { ComoFunciona, MeusAvisos, NaoEncontrada, Preferencias } from "./paginas/Outras.jsx";
import Apresentacao, { CHAVE_APRESENTACAO } from "./paginas/Apresentacao.jsx";

function jaViuApresentacao() {
  try {
    return sessionStorage.getItem(CHAVE_APRESENTACAO) === "1";
  } catch {
    return true;
  }
}

// Rotas que exigem login. Sem usuário: primeiro a apresentação do Cine Leandro
// (uma vez por visita), depois a tela de Entrar; e depois de entrar, volta para
// a página que a pessoa queria abrir.
function Privada({ children }) {
  const { usuario, carregandoUsuario, t } = useSessao();
  const local = useLocation();
  if (carregandoUsuario) return <div className="tela-carregando" aria-busy="true">{t("carregando")}</div>;
  if (!usuario) {
    const destino = jaViuApresentacao() ? "/entrar" : "/apresentacao";
    return <Navigate to={destino} replace state={{ voltar: local.pathname + local.search }} />;
  }
  return children;
}

// Telas de acesso (entrar, cadastrar...): quem JÁ chega logado vai direto para os filmes.
// A decisão é tomada só na chegada: depois do login, quem navega é o próprio formulário
// (para a página que a pessoa queria abrir), sem disputar com a animação de saída.
function SoVisitante({ children }) {
  const { usuario, carregandoUsuario } = useSessao();
  const chegouLogado = useRef(null);
  if (carregandoUsuario) return null;
  if (chegouLogado.current === null) chegouLogado.current = Boolean(usuario);
  if (chegouLogado.current) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  const { prefs } = useSessao();
  const local = useLocation();
  const p = (elemento) => <Privada>{elemento}</Privada>;
  const v = (elemento) => <SoVisitante>{elemento}</SoVisitante>;
  return (
    // reducedMotion: "always" desliga os movimentos; "user" segue o ajuste do sistema operacional.
    <MotionConfig reducedMotion={prefs.reduzir_animacoes ? "always" : "user"}>
      <ToastProvider>
        <LayoutGroup>
          <Topo />
          <main id="conteudo" tabIndex={-1}>
            <AnimatePresence mode="wait" initial={false}>
              <Routes location={local} key={local.pathname}>
                {/* Públicas: a porta de entrada do sistema */}
                <Route path="/apresentacao" element={v(<Apresentacao />)} />
                <Route path="/entrar" element={v(<Entrar />)} />
                <Route path="/cadastrar" element={v(<Cadastrar />)} />
                <Route path="/recuperar-senha" element={v(<RecuperarSenha />)} />
                <Route path="/redefinir-senha" element={<RedefinirSenha />} />
                {/* Privadas: só com login */}
                <Route path="/" element={p(<Inicio />)} />
                <Route path="/lancamentos" element={p(<Lancamentos />)} />
                <Route path="/filme/:id" element={p(<Filme />)} />
                <Route path="/preferencias" element={p(<Preferencias />)} />
                <Route path="/avisos" element={p(<MeusAvisos />)} />
                <Route path="/como-funciona" element={p(<ComoFunciona />)} />
                <Route path="*" element={<NaoEncontrada />} />
              </Routes>
            </AnimatePresence>
          </main>
          <Rodape />
        </LayoutGroup>
      </ToastProvider>
    </MotionConfig>
  );
}
