// Favoritos.jsx — a lista de favoritos do olheiro: grade de cards + remover
// Rota: /favoritos (protegida: só olheiro logado consegue ver)
// Existe porque o superpoder do olheiro é FAVORITAR — sem esta página,
// ele marcaria atletas mas nunca teria a "pasta" de favoritos dele.
import { useEffect, useState } from 'react'
import { Navigate, Link } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import CartaoAtleta from '../components/CartaoAtleta'   // MESMO card da vitrine
import './Favoritos.css'

export default function Favoritos() {
    const { logado, usuario, ehOlheiro } = useAuth()
    const [lista, setLista] = useState(null)   // null = ainda carregando (diferente de vazio = '[]')
    const [erro, setErro] = useState(null)

    // Busca os favoritos, mas só se for OLHEIRO LOGADO (outros recebem 403)
    // ehOlheiro depende do /auth/me terminar, por isso o feito "espera" ele virar true
    // ntes de perguntar ao backend
    useEffect(() => {
        if (!logado || !ehOlheiro) return
        api('/meus-favoritos')
        .then(setLista)                     // setLista(dados) = guarda a lista
        .catch(e => setErro(e.detail))
    }, [logado, ehOlheiro])

    // PROTEÇÃO DE ROTA: são 3 'portões' nessa ordem (e a ordem importa muito)
    
    // 1º - logado mas usuário ainda null (/auth/me busca quem é)
    // pular direto pro redirect mandaria o olheiro pra home por engano
    // É o 'intervalo de dúvida' entre clicar em entrar e o backend responder
    if (logado && usuario === null) return <div className='pagina'>Carregando...</div>

    // 2º - sem token volta pro login (mesmo do portão do /perfil e /minha-conta)
    if (!logado) return <Navigate to="/login" replace />

    // 3º - logado mas NÃO é olheiro, aí é mandado para a home
    if (!ehOlheiro) return <Navigate to='/' replace />
    if (erro) return <div className='pagina'><p className="erro">Erro: {erro}</p></div>
    if (lista === null) return <div className='pagina'><p>Carregando…</p></div>

    //Remmove um favorito: apaga no banco e tira o card da tela (espelho do favoritar do perfil)
    async function remover(id) {
        try {
            await api(`/atletas/${id}/favoritar`, {method: 'DELETE'})
            setLista(lista.filter(a => a.id !== id))    // filter = nova lista sem esse id
        } catch (e) {
            // 404 - já não estava no banco; tira da tla mesmo assim sincroniza
            if (e.status === 404) setLista(lista.filter(a => a.id !== id))
                else setErro(e.detail)
        }
    }

    // Estado vazio: olheiro ainda não favoritou ninguém - então é dado dica do que fazer (dica de UX)
    if (lista.length === 0) {
        return (
            <div className='pagina'>
                <h1>⭐ Meus favoritos</h1>
                <p>Nenhum favorito ainda.</p>
                <p>Abra um atleta na  <Link to="/">vitrine</Link> e clique em 🤍 Favoritar.</p>
            </div>
        )
    }

    return (
    <div className="pagina">
      <h1>⭐ Meus favoritos ({lista.length})</h1>
      <div className="grade-favoritos">
        {lista.map(a => (
          // Wrapper = só pra empilhar card + botão de remover
          <div key={a.id} className="favorito-item">
            {/* /meus-favoritos devolve AtletaBuscaSaida = o MESMO formato da
                vitrine, então o CartaoAtleta serve direto, sem adaptar nada
                (reusar = menos código = menos bug) */}
            <CartaoAtleta atleta={a} />
            <button className="botao-remover" onClick={() => remover(a.id)}>
              ❌ Remover dos favoritos
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}