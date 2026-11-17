// Perfil.jsx — a ficha completa do atleta: dados + estatísticas + vídeos
import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'   // useParams = pegar :id da URL
import { api, API_BASE } from '../api/client'
import { useAuth } from '../context/AuthContext'     // NOVIDADE: quem está olhando?
import './Perfil.css'

// Função para calcular a idade a partir da data que backend manda (ISO: "2010-05-12")
function calcularIdade(iso) {
  const nasc = new Date(iso)
  const hoje = new Date()
  let idade = hoje.getFullYear() - nasc.getFullYear()
  const m = hoje.getMonth() - nasc.getMonth()

  // m < 0 indica que o aniversário ainda não chegou no mês do ano corrente, no caso de mesmo mês compara-se os dias
  // lembrando que em JS janeiro é zero (0) - Ou seja, caso os critérios não sejam atendidos, dimnuimos 1 na idade
  if (m < 0 || (m === 0 && hoje.getDate() < nasc.getDate())) idade--
  return idade
}

export default function Perfil() {
  // Pega o atleta_id da URL (em texto)
  const { atleta_id } = useParams()

  // Quem está olhando essa página? Isso vem do AuthContext (login)
  const {logado, ehOlheiro, usuario} = useAuth()   // usuario = EU (pra não conversar comigo mesmo)

  const [perfil, setPerfil] = useState(null)    // null = ainda está carregando
  const [videos, setVideos] = useState([])      // nenhum vídeo ainda
  const [stats, setStats] = useState([]) 
  const [erro, setErro] = useState(null) 

  // true = esse atleta já está nos favoritos do olheiro que está vendo
  const [favoritado, setFavoritado] = useState(false)

  // Erro da AÇÃO de favoritar: fica INLINE embaixo do botão (a página
  // inteira não pode sumir por causa de um clique — diferente do erro
  // de CARREGAMENTO do topo, que sim derruba a página)
  const [erroFavorito, setErroFavorito] = useState(null)

  // Aqui se faz  busca: fica + videos + estatisticas juntos e só renderiza quando as 3 chhegarem
  // ou seja, quando a página é aberta, ela precisa buscar tais informações e o código só continua se as 3 forem concluídas com sucesso
  useEffect(() => {     // useEffect executa uma ação quando o componente é carregado ou dependência muda
    Promise.all([       // Promise.all recebe várias operações assíncronas e aguarda todas terminarem
      api(`/perfil/${atleta_id}`),
      api(`/perfil/${atleta_id}/videos`),
      api(`/perfil/${atleta_id}/estatisticas`),
    ])
    // o .then só executado quando todas as operações terminarem com sucesso
    .then(([p, v, s]) => {setPerfil(p); setVideos(v); setStats(s)})
    .catch(e => setErro(e.detail))    // captura o erro caso ocorra
  }, [atleta_id])   // refaz a busca se o atleta da URL mudar

  // Aqui se pergunta ao backend: "este atleta está nos meus favoritos?"
  // só o olheiro logado pode perguntar (no outros recebem um 403)
  // usamos Number() porque o id da URL é o texto "1" e o da lista é o número 1
  useEffect(() => {
    if (!logado || !ehOlheiro) return   // não é olheiro? nem pergunta
    api('/meus-favoritos')
    .then(lista => setFavoritado(lista.some(a => a.id === Number(atleta_id))))
    .catch(() => {})      // falhou? trata como 'não favoritado' e siga com o restante
  }, [logado, ehOlheiro, atleta_id])

  // Essa função permite adicionar ou remover um atleta da lista de favoritos, dependendo da situação atual
  // clica no coração: favorita (POST) ou defavorita (DELETE) no backend
  async function alternarFavorito() {
    setErroFavorito(null)   // limpa o aviso de uma tentativa anterior
    try {
      if (favoritado) {
        await api(`/atletas/${atleta_id}/favoritar`, { method: 'DELETE' })  // faz requisição ao backend, espera resposta e apontamos o que deve ser feito
        setFavoritado(false)   // espelha a mudança na tela
      } else {
        await api(`/atletas/${atleta_id}/favoritar`, { method: 'POST' })
        setFavoritado(true)
      }
    } catch(e) {
      // 409/404 = a tela estava defasada do banco, então corrig o estado com informaões atuais
      if (e.status === 409) setFavoritado(true)         // já estava favoritado
      else if (e.status === 404) setFavoritado(false)    // não estava
      else setErroFavorito(e.detail)                    // erro de verdade (403 etc) — inline
    }
  }

  // Retornos condcionais: erro > carregando > conteúdo (hooks semprre acima!)
  if (erro) return <div className='pagina'><p className='erro'>Erro: {erro}</p></div>   // verifica se existe erro armazenado em 'erro', se existir retorna  mensagem de erro
  if (!perfil) return <div className='pagina'><p>Carregando...</p></div>                // perfil ainda não existe? Se não existir mostra 'Carregando... 

  // Agrupa métricas da mesma competição: {chave: [métrica1, métrica2, ...]}
  // reduce percorre uma lista e armazena informações até produzir um resultado final (acc é o acumulador - e é o elemento atual)
  const porCompeticao = stats.reduce((acc, e) => {      
    const chave = `${e.competicao} · ${e.temporada}`    // competicao e temporada do valor atual
    ;(acc[chave] ??= []).push(e)    // acessa o acumulador - ??=[] significa que se ainda não eistir (ou for Null) atribui lista vazia - push adiciona ao fnal da lista
    return acc
  }, {})

   return (
    <div className="pagina">
      <Link to="/" className="voltar">← Voltar pra vitrine</Link>

      {/* Cabeçalho: avatar, dados principais e bio */}
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

          {/* Coração: aparece só pra olheiro; muda de forma se favoritado */}
          {ehOlheiro && (
            <button
              className={`botao-favorito ${favoritado ? 'ativo' : ''}`}
              onClick={alternarFavorito}
            >
              {favoritado ? '❤️ Remover dos favoritos' : '🤍 Favoritar'}
            </button>
          )}

          {/* Erro do clique em favoritar: aviso inline (não derruba a página).
              403 = olheiro sem ficha → em vez de citar endpoint, damos o caminho */}
          {erroFavorito && (
            <p className="erro">
              {erroFavorito.includes('Complete seu perfil')
                ? <>Complete seu perfil na <Link to="/minha-conta">Minha Conta</Link> antes de favoritar.</>
                : erroFavorito}
            </p>
          )}

          {/* 💬 Conversar: qualquer logado puxa assunto com o atleta da ficha.
              O link usa o USUARIO_ID (mensagem é entre usuários, não entre atletas)
              e some no próprio perfil: ninguém conversa consigo mesmo. */}
          {logado && perfil.usuario_id && perfil.usuario_id !== usuario?.id && (
            <Link to={`/mensagens/${perfil.usuario_id}`} className="botao-conversar">
              💬 Conversar
            </Link>
          )}
        </div>
      </div>

      {/* Estatísticas: uma tabela por competição */}
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
              // Number() porque o Decimal chega como texto "5.00" no JSON
              <tr key={m.id}><td>{m.metrica}</td><td>{Number(m.valor)}</td></tr>
            ))}
          </tbody>
        </table>
      ))}

      {/* Vídeos enviados pelo atleta */}
      <h2>Vídeos ({videos.length})</h2>
      {videos.length === 0 && <p>Nenhum vídeo enviado.</p>}
      <div className="videos">
        {videos.map(v => (
          <div key={v.id} className="video-card">
            {/* Em dev API_BASE = '/api' (proxy do Vite); em produção = URL do
                Render direto (a Vercel não tem proxy). Mesmo caminho, 2 mundos. */}
            <video controls preload="metadata" src={`${API_BASE}${v.url_ou_caminho}`} />
            <p>{v.titulo}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

