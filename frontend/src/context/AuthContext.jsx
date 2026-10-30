// AuthContext.jsx — o "crachá" da sessão.
// Contexto = um compartilhamento GLOBAL de dados: o token fica guardado
// aqui e qualquer página (sem passar prop pra baixo) pode perguntar
// "quem está logado?" com useContext(AuthContext).
import { createContext, useContext, useState } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)   // null = "ainda ninguém se inscreveu"

export function AuthProvider({ children }) {
  // useState lê a gaveta na primeira vez: se tinha token, a sessão volta
  const [token, setToken] = useState(() => localStorage.getItem('token'))

  // entra e salva o token na gaveta (localStorage = persiste no navegador)
  async function entrar(email, senha) {
    const dados = await api('/auth/login', {
      method: 'POST',
      corpo: { email, senha },
    })
    localStorage.setItem('token', dados.access_token)
    setToken(dados.access_token)
  }

  // cria a conta e já entra (cadastro -> login automático)
  async function cadastrar(nome, email, senha, tipo_usuario) {
    await api('/auth/cadastro', {
      method: 'POST',
      corpo: { nome, email, senha, tipo_usuario },
    })
    await entrar(email, senha)
  }

  // sai: apaga a gaveta e o estado
  function sair() {
    localStorage.removeItem('token')
    setToken(null)
  }

  // o que todo mundo pode ler
  const valor = { token, logado: !!token, entrar, cadastrar, sair }
  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

// atalho: em vez de importar o contexto, importa useAuth() nas telas
export function useAuth() {
  return useContext(AuthContext)
}