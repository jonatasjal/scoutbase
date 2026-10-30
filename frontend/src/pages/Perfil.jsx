// Perfil.jsx — a ficha completa do atleta: dados + estatísticas + vídeos
import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'   // useParams = pegar :id da URL
import { api } from '../api/client'
import './Perfil.css'

// calcula a idade a partir da data que o backend manda (ISO: "2010-05-12")
function calcularIdade(iso) {
  const nasc = new Date(iso)
  const hoje = new Date()
  let idade = hoje.getFullYear() - nasc.getFullYear()
  const m = hoje.getMonth() - nasc.getMonth()
  if (m < 0 || (m === 0 && hoje.getDate() < nasc.getDate())) idade--
  return idade
}

export default function Perfil() {
  // O react-router deixa o ":atleta_id" da URL acessível aqui
  const { atleta_id } = useParams()      // URL /perfil/3 -> atleta_id = "3"

  const [perfil, setPerfil] = useState(null)
  const [videos, setVideos] = useState([])
  const [stats, setStats] = useState([])
  const [erro, setErro] = useState(null)

  // 3 chamadas à API de uma vez; Promise.all espera as 3 e só aí renderiza
  useEffect(() => {
    Promise.all([
      api(`/perfil/${atleta_id}`),
      api(`/perfil/${atleta_id}/videos`),
      api(`/perfil/${atleta_id}/estatisticas`),
    ])
      .then(([p, v, s]) => { setPerfil(p); setVideos(v); setStats(s) })
      .catch(e => setErro(e.detail))
  }, [atleta_id])   // refaz se o id da URL mudar (navegar de /perfil/1 pra /perfil/2)

  if (erro) return <div className="pagina"><p className="erro">Erro: {erro}</p></div>
  if (!perfil) return <div className="pagina"><p>Carregando…</p></div>

  // agrupa estatísticas por competição+temporada (tabela 1 por competição)
  // reduce = "reduzir" a lista a um OBJETO {competicao: [métricas...]}
  const porCompeticao = stats.reduce((acc, e) => {
    const chave = `${e.competicao} · ${e.temporada}`
    ;(acc[chave] ??= []).push(e)     // ??= = se não existir, cria []
    return acc
  }, {})

  return (
    <div className="pagina">
      <Link to="/" className="voltar">← Voltar pra vitrine</Link>

      {/* ---- Cabeçalho da ficha ---- */}
      <div className="perfil-topo">
        <div className="perfil-avatar">A</div>
        <div>
          <h1>Ficha do atleta #{perfil.id}</h1>
          <p>
            ⚽ {perfil.esporte} · {perfil.posicao} · {perfil.categoria}<br />
            📍 {perfil.cidade}/{perfil.estado} · {calcularIdade(perfil.data_nascimento)} anos
            {perfil.clube_atual && <> · 🏟️ {perfil.clube_atual}</>}
          </p>
          {perfil.bio && <p className="bio">"{perfil.bio}"</p>}
        </div>
      </div>

      {/* ---- Estatísticas: uma tabela por competição ---- */}
      <h2>Estatísticas</h2>
      {Object.keys(porCompeticao).length === 0 && <p>Nenhuma estatística registrada.</p>}
      {Object.entries(porCompeticao).map(([chave, metricas]) => (
        <table key={chave} className="tabela-stats">
          <caption>{chave}</caption>
          <thead>
            <tr><th>Métrica</th><th>Valor</th></tr>
          </thead>
          <tbody>
            {metricas.map(m => (
              // Number(m.valor): Decimal vem como texto "5.00" no JSON
              <tr key={m.id}><td>{m.metrica}</td><td>{Number(m.valor)}</td></tr>
            ))}
          </tbody>
        </table>
      ))}

      {/* ---- Vídeos ---- */}
      <h2>Vídeos ({videos.length})</h2>
      {videos.length === 0 && <p>Nenhum vídeo enviado.</p>}
      <div className="videos">
        {videos.map(v => (
          <div key={v.id} className="video-card">
            {/* caminho do banco já vem como "/media/uploads/xxx.mp4";
                o /api na frente faz o Vite repassar pro backend */}
            <video controls preload="metadata" src={`/api${v.url_ou_caminho}`} />
            <p>{v.titulo}</p>
          </div>
        ))}
      </div>
    </div>
  )
}