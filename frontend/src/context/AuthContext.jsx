// AuthContext.jsx — o "crachá" da sessão.
// Contexto = um compartilhamento GLOBAL de dados: o token fica guardado
// aqui e qualquer página (sem passar prop pra baixo) pode perguntar
// "quem está logado?" com useContext(AuthContext).
import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)       // null = "ainda ninguém se inscreveu"

export function AuthProvider({ children }) {
  // useState lê a gaveta na primeira vez: se tinha token, a sessão volta
  const [token, setToken] = useState(() => localStorage.getItem('token'))

  // Guarda o usuário inteiro (/auth/me), não só o token, pra poder saber nome e tipo
  const [usuario, setUsuario] = useState(null)    // null = ainda não sabemos quem é

  // Sempre que o token mudar, perguntamos ao backend "quem é esse token?"
  // Isso cobre 2 casos com um único código: logar agora (token novo) e
  // recarregar a página (token velho da gaveta)
  useEffect(() => {
    if (!token) return   // sem token não busca nada (o sair() limpa o usuário)
    api('/auth/me')
      .then(setUsuario)  // se o token é válido, guarda o usuário
      .catch(() => {     // se o token é inválido (erro 401), limpa tudo
        localStorage.removeItem('token')
        setToken(null)
        setUsuario(null)
      })
  }, [token])   // refaz quando o token aparece ou some

  // entra e salva o token na gaveta (localStorage = persiste no navegador)
  async function entrar(email, senha) {
    const dados = await api('/auth/login', {
      method: 'POST',
      corpo: { email, senha },
    })
    localStorage.setItem('token', dados.access_token)
    setToken(dados.access_token)  // dispara o useEffect acima para buscar '/auth/me'
  }

  // cria a conta e já entra (cadastro -> login automático)
  async function cadastrar(nome, email, senha, tipo_usuario) {
    await api('/auth/cadastro', {
      method: 'POST',
      corpo: { nome, email, senha, tipo_usuario },
    })
    await entrar(email, senha)  // dispara o useEffect acima para buscar '/auth/me'
  }

  // sai e limpa o token da gaveta
  function sair() {
    localStorage.removeItem('token')
    setToken(null)
    setUsuario(null)   // sem isso, o usuário antigo ficaria na tela após sair
  }

  // ehOlheiro = atalho booleano (true/false) pras telas não precisarem ficar
  // digitando usuario?.tipo_usuario === 'olheiro' o tempo todo.
  // O '===' compara tipo E valor: só é true se for exatamente a string 'olheiro'
  const ehOlheiro = usuario?.tipo_usuario === 'olheiro'

  // o que todo mundo pode ler
  const valor = { token, logado: !!token, usuario, ehOlheiro, entrar, cadastrar, sair }
  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

// atalho: em vez de importar o contexto, importa useAuth() nas telas.
// O disable é porque o ESLint (fast refresh) quer SÓ componentes neste arquivo;
// é o padrão do React manter o hook junto do contexto — não é bug, é exceção conhecida
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext)
}
