// client.js — o "fio telefônico" com o backend
// Toda chamada à API passa por aqui. Um lugar só = fácil de
// mudar depois (ex.: adicionar o token automaticamente)

// Em dev: '/api' (o proxy do Vite repassa pra :8000 — como hoje).
// Em produção: a Vercel NÃO tem proxy, o frontend fala direto com o
// Render. O endereço vem da variável VITE_API_URL (criada na Vercel,
// nunca vai pro Git). Resumo: mesma linha, dois mundos.
const API_BASE = import.meta.env.VITE_API_URL || '/api'
export { API_BASE }   // Perfil.jsx importa pra montar o src do vídeo

// Método reutilizável: pega JSON, monta URL com parâmetros, trata erros
export async function api(caminho, { method = 'GET', corpo = null, token = null, params = null } = {}) {
  // Monta a query string: {estado:'SP'} -> "?estado=SP"
  const qs = params ? '?' + new URLSearchParams(params).toString() : ''

  const opcoes = { method, headers: {} }
  if (corpo !== null) {
    // FormData = "envelope" de arquivo (multipart). Nesse caso NÃO setamos
    // Content-Type na mão: o navegador cria o boundary (o "divisor" das partes).
    if (corpo instanceof FormData) {
      opcoes.body = corpo
    } else {
      opcoes.headers['Content-Type'] = 'application/json'
      opcoes.body = JSON.stringify(corpo)     // objeto -> texto JSON
    }
  }
  // NOVIDADE: se quem chamou não passou token, busca o do login salvo.
  // localStorage = "gaveta" do navegador que sobrevive ao fechar a aba.
  const tokenSalvo = token ?? localStorage.getItem('token')
  if (tokenSalvo) opcoes.headers['Authorization'] = `Bearer ${tokenSalvo}`

  const resp = await fetch(`${API_BASE}${caminho}${qs}`, opcoes)

  // 204 = sem conteúdo (ex.: DELETE ok)
  if (resp.status === 204) return null

  const dados = await resp.json().catch(() => null)
  if (!resp.ok) {
    // 401 = token expirado/inválido -> derruba a sessão (limpa a gaveta)
    if (resp.status === 401) localStorage.removeItem('token')
    // FastAPI devolve {detail: "mensagem"} em erro — repassa pro caller decidir
    throw { status: resp.status, detail: dados?.detail ?? 'Erro inesperado' }
  }
  return dados
}