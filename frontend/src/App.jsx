// App.jsx — o "planta baixa": cada URL mostra uma página
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Vitrine from './pages/Vitrine'
import Perfil from './pages/Perfil'
import Rankings from './pages/Rankings'
import Login from './pages/Login'
import Cadastro from './pages/Cadastro'
import MinhaConta from './pages/MinhaConta'

// Header separado porque precisa do contexto (useAuth só funciona
// DENTRO do AuthProvider — por isso App envolve e Header fica dentro)
function Topo() {
  const { logado, sair } = useAuth()
  return (
    <header className="topo">
      <Link to="/" className="topo-logo">⚽ ScoutBase</Link>
      <nav>
        <Link to="/">Vitrine</Link>
        <Link to="/rankings">🏆 Rankings</Link>
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
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}