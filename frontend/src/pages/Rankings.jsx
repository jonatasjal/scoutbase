// Rankings.jsx — a "sala de troféus": resumo geral + top atletas + top olheiros
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import './Rankings.css'

// medalhas por posição: 1º 🥇, 2º 🥇, 3º 🥇... resto só o número
function medalha(posicao) {
  return { 1: '🥇', 2: '🥈', 3: '🥉' }[posicao] ?? `${posicao}º`
}

export default function Rankings() {
  const [resumo, setResumo] = useState(null)
  const [topAtletas, setTopAtletas] = useState([])
  const [topOlheiros, setTopOlheiros] = useState([])
  const [erro, setErro] = useState(null)

  // as 3 rotas públicas do dashboard (Fase 7), em paralelo
  useEffect(() => {
    Promise.all([
      api('/dashboard/resumo'),
      api('/dashboard/top-atletas'),
      api('/dashboard/ranking-olheiros'),
    ])
      .then(([r, a, o]) => { setResumo(r); setTopAtletas(a); setTopOlheiros(o) })
      .catch(e => setErro(e.detail))
  }, [])

  if (erro) return <div className="pagina"><p className="erro">Erro: {erro}</p></div>
  if (!resumo) return <div className="pagina"><p>Carregando…</p></div>

  // toFixed(2) = "arredondar" 8.166666 → "8.17" com 2 casas decimais
  return (
    <div className="pagina">
      <h1>🏆 Rankings</h1>

      {/* ---- Cards de resumo geral (os 7 números do /resumo) ---- */}
      <div className="cards-resumo">
        <div className="card-num"><b>{resumo.total_usuarios}</b><span>usuários</span></div>
        <div className="card-num"><b>{resumo.total_atletas}</b><span>atletas</span></div>
        <div className="card-num"><b>{resumo.total_olheiros}</b><span>olheiros</span></div>
        <div className="card-num"><b>{resumo.total_avaliacoes}</b><span>avaliações</span></div>
        <div className="card-num destaque"><b>{resumo.media_geral_nota.toFixed(2)}</b><span>nota média</span></div>
        <div className="card-num"><b>{resumo.total_videos}</b><span>vídeos</span></div>
        <div className="card-num"><b>{resumo.total_mensagens}</b><span>mensagens</span></div>
      </div>

      <div className="colunas">
        {/* ---- Top atletas ---- */}
        <section>
          <h2>⭐ Top atletas</h2>
          {topAtletas.length === 0 && <p>Ninguém avaliado ainda.</p>}
          <ol className="lista-ranking">
            {topAtletas.map(a => (
              // key=atleta_id (não é o índice!) — e Link leva pro perfil
              <li key={a.atleta_id}>
                <span className="medalha">{medalha(a.ranking_posicao)}</span>
                <Link to={`/perfil/${a.atleta_id}`} className="nome">
                  {a.nome ?? 'Atleta'}  {/* mesma regra da vitrine */}
                </Link>
                <span className="detalhe">
                  {a.posicao} · <b>{a.media_nota.toFixed(2)}</b> ({a.total_avaliacoes} aval.)
                </span>
              </li>
            ))}
          </ol>
        </section>

        {/* ---- Top olheiros ---- */}
        <section>
          <h2>🔭 Top olheiros</h2>
          {topOlheiros.length === 0 && <p>Nenhum olheiro avaliado ainda.</p>}
          <ol className="lista-ranking">
            {topOlheiros.map(o => (
              <li key={o.olheiro_id}>
                <span className="medalha">{medalha(o.ranking_posicao)}</span>
                <span className="nome">{o.nome ?? 'Olheiro'}</span>
                <span className="detalhe">
                  {o.organizacao ?? '—'} · <b>{o.media_nota.toFixed(2)}</b> ({o.total_avaliacoes} aval.)
                </span>
              </li>
            ))}
          </ol>
        </section>
      </div>
    </div>
  )
}