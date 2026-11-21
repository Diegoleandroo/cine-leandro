// Cliente da API do Django. Guarda o token de login e manda o idioma em cada pedido.

const CHAVE_TOKEN = "cine.token";

export function lerToken() {
  try {
    return localStorage.getItem(CHAVE_TOKEN);
  } catch {
    return null;
  }
}

export function guardarToken(token) {
  try {
    if (token) localStorage.setItem(CHAVE_TOKEN, token);
    else localStorage.removeItem(CHAVE_TOKEN);
  } catch {
    /* navegador sem armazenamento: o login dura só esta aba */
  }
}

export class ErroApi extends Error {
  constructor(status, corpo) {
    super(corpo?.mensagem || "Erro inesperado.");
    this.status = status;
    this.codigo = corpo?.erro;
    this.campos = corpo?.campos;
  }
}

let idiomaAtual = "PT";
export const definirIdiomaDaApi = (idioma) => (idiomaAtual = idioma);

export async function api(caminho, { metodo = "GET", corpo } = {}) {
  const separador = caminho.includes("?") ? "&" : "?";
  const url = `/api${caminho}${metodo === "GET" ? `${separador}idioma=${idiomaAtual}` : ""}`;
  const headers = { Accept: "application/json" };
  if (corpo !== undefined) headers["Content-Type"] = "application/json";
  const token = lerToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let resposta;
  try {
    resposta = await fetch(url, { method: metodo, headers, body: corpo !== undefined ? JSON.stringify(corpo) : undefined });
  } catch {
    throw new ErroApi(0, { erro: "rede" });
  }
  if (resposta.status === 204) return null;
  const dados = await resposta.json().catch(() => null);
  if (resposta.status === 401 && dados?.erro === "nao_autenticado") {
    // Sessão acabou (token expirou ou foi revogado): avisa o app para voltar ao login.
    window.dispatchEvent(new Event("cine:sessao-encerrada"));
  }
  if (!resposta.ok) throw new ErroApi(resposta.status, dados);
  return dados;
}
