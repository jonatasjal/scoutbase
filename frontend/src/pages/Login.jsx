// Login.jsx — tela de entrada: email + senha -> /auth/login
import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Login.css'

export default function Login() {
  const { entrar } = useAuth()          // pega a função do contexto
  const navegar = useNavigate()         // programa navegação (igual router.push)
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState(null)
  const [carregando, setCarregando] = useState(false)

  async function aoEnviar(e) {
    e.preventDefault()          // impede o formulário de recarregar a página
    setErro(null)
    setCarregando(true)
    try {
      await entrar(email, senha)
      navegar('/')              // logou -> volta pra vitrine
    } catch (e) {
      setErro(e.detail)         // ex.: "Credenciais inválidas"
    } finally {
      setCarregando(false)      // roda sempre (sucesso ou erro)
    }
  }

  return (
    <div className="pagina auth">
      <form className="caixa-auth" onSubmit={aoEnviar}>
        <h1>Entrar</h1>

        <label>
          E-mail
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
        </label>

        <label>
          Senha
          <input type="password" value={senha} onChange={e => setSenha(e.target.value)} required />
        </label>

        {erro && <p className="erro">{erro}</p>}

        <button type="submit" disabled={carregando}>
          {carregando ? 'Entrando…' : 'Entrar'}
        </button>

        <p className="rodape">
          Não tem conta? <Link to="/cadastro">Criar conta grátis</Link>
        </p>
      </form>
    </div>
  )
}