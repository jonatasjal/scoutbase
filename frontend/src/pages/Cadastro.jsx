// Cadastro.jsx — cria a conta e já loga (cadastro -> entrar)
import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Login.css'   // mesma folha do login (caixa igual)

export default function Cadastro() {
  const { cadastrar } = useAuth()
  const navegar = useNavigate()
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  // tipo_usuario: quem cria ficha de atleta marca atleta; olheiro vira scout
  const [tipo, setTipo] = useState('atleta')
  const [erro, setErro] = useState(null)
  const [carregando, setCarregando] = useState(false)

  async function aoEnviar(e) {
    e.preventDefault()
    setErro(null)
    setCarregando(true)
    try {
      await cadastrar(nome, email, senha, tipo)
      navegar('/')                 // já entrou -> vitrine
    } catch (e) {
      setErro(e.detail)            // ex.: "E-mail já cadastrado"
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div className="pagina auth">
      <form className="caixa-auth" onSubmit={aoEnviar}>
        <h1>Criar conta</h1>

        <label>
          Nome
          <input value={nome} onChange={e => setNome(e.target.value)} required />
        </label>

        <label>
          E-mail
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
        </label>

        <label>
          Senha (mínimo 6 caracteres)
          <input type="password" minLength={6} value={senha} onChange={e => setSenha(e.target.value)} required />
        </label>

        <label>
          Sou...
          <select value={tipo} onChange={e => setTipo(e.target.value)}>
            <option value="atleta">Atleta (quero aparecer na vitrine)</option>
            <option value="olheiro">Olheiro (quero encontrar atletas)</option>
            <option value="responsavel">Responsável legal</option>
          </select>
        </label>

        {erro && <p className="erro">{erro}</p>}

        <button type="submit" disabled={carregando}>
          {carregando ? 'Criando…' : 'Criar conta'}
        </button>

        <p className="rodape">
          Já tem conta? <Link to="/login">Entrar</Link>
        </p>
      </form>
    </div>
  )
}