// App.jsx — o "planta baixa": cada URL mostra uma página
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { api } from './api/client'
import { AuthProvider, useAuth } from './context/AuthContext'
import Vitrine from './pages/Vitrine'
import Perfil from './pages/Perfil'
import Rankings from './pages/Rankings'
import Login from './pages/Login'
import Cadastro from './pages/Cadastro'
import MinhaConta from './pages/MinhaConta'
import Favoritos from './pages/Favoritos'
import Mensagens from './pages/Mensagens'
import Chat from './pages/Chat'

// Header separado porque precisa do contexto (useAuth só funciona
// DENTRO do AuthProvider — por isso App envolve e Header fica dentro)
function Topo() {
  // ehOlheiro = NOVIDADE: o topo precisa saber se é olheiro pra esconder/mostrar o ⭐
  const { logado, ehOlheiro, sair } = useAuth()

  // Contador de mensagens não-lidas
  const [naoLidas, setNaoLidas] = useState(0)     // 0 = sem badge
  const local = useLocation()                     // objeto da URL atual (local.pathname = "/perfil/1", etc)

  // Pergunta ao backend quantas não-lidas eu tenho
  // local.pathname nas dependências = refaz a busca A CADA troca de página:
  // assim, ao voltar do chat (onde leu as mensagens), o badge zera sozinho
  useEffect(() => {
    if (!logado) return                         // deslogado? nem chama a API
    // (não setamos 0 aqui de propósito: setState síncrono dentro de effect
    //  é proibido pela regra do lint. E nem precisa — o badge só renderiza
    //  quando logado; ao sair ele some, e ao voltar este effect busca de novo)
    api('/mensagens/nao-lidas')
    .then(r => setNaoLidas(r.nao_lidas))
    .catch(() => {})                            // falhou? fica o valor anterior (não quebra a barra)
  }, [logado, local.pathname])
  
  return (
    <header className="topo">
      <Link to="/" className="topo-logo">⚽ ScoutBase</Link>
      <nav>
        <Link to="/">Vitrine</Link>
        <Link to="/rankings">🏆 Rankings</Link>
        {/* Chat: qualquer logado usa (atleta E olheiro) — só aparece logado */}
        {logado && (
          <Link to='/mensagens'>
            💬 Mensagens
            {/*só pinta o badge se tiver mensagem nova (evita um '0' sem graça*/}
            {naoLidas > 0 && <span className='badge-topo'>{naoLidas}</span>}
          </Link>
        )}
        {ehOlheiro && <Link to="/favoritos">⭐ Favoritos</Link>}
        {logado
          ? <>
              <Link to="/minha-conta">Minha conta</Link>
              <button onClick={sair} className="botao-sair">Sair</button>
            </>
          : <Link to="/login">Entrar</Link>}
      </nav>
    </header>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Topo />
        <Routes>
          <Route path="/" element={<Vitrine />} />
          <Route path="/perfil/:atleta_id" element={<Perfil />} />
          <Route path="/rankings" element={<Rankings />} />
          <Route path="/login" element={<Login />} />
          <Route path="/cadastro" element={<Cadastro />} />
          <Route path="/minha-conta" element={<MinhaConta />} />
          <Route path="/favoritos" element={<Favoritos />} />
          <Route path="/mensagens" element={<Mensagens />} />
          <Route path="/mensagens/:usuarioId" element={<Chat />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}