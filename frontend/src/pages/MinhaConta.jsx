// MinhaConta.jsx — a área logada: quem sou, minha ficha, quem me viu, meus vídeos
import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'
import './MinhaConta.css'

export default function MinhaConta() {
  const { token } = useAuth()
  const [eu, setEu] = useState(null)        // /auth/me
  const [views, setViews] = useState(null)  // visualizações (só atleta)
  const [meusVideos, setMeusVideos] = useState([])
  const [ficha, setFicha] = useState({
    data_nascimento: '', posicao: '', categoria: '',
    cidade: '', estado: '', clube_atual: '', bio: '',
  })
  const [erro, setErro] = useState(null)
  const [ok, setOk] = useState(null)        // mensagens de sucesso
  const [salvando, setSalvando] = useState(false)  // loading do "Salvar ficha"
  const [enviando, setEnviando] = useState(false)  // loading do "Enviar vídeo"
  const [arquivo, setArquivo] = useState(null)
  const [tituloVideo, setTituloVideo] = useState('')

  // 1) quem sou eu
  useEffect(() => {
    if (!token) return                       // sem token não busca nada
    api('/auth/me')
      .then(setEu)
      .catch(e => setErro(e.detail))
  }, [token])

  // 2) se tenho ficha de atleta: busco visualizações, vídeos e a ficha atual
  useEffect(() => {
    if (!eu?.atleta_id) return               // ?. = "se existir" (olheiro não tem)
    Promise.all([
      api(`/perfil/${eu.atleta_id}/visualizacoes`),
      api(`/perfil/${eu.atleta_id}/videos`),
      api(`/perfil/${eu.atleta_id}`),
    ])
      .then(([v, vids, f]) => {
        setViews(v)
        setMeusVideos(vids)
        // pré-preenche o form com o que já existe no banco
        setFicha({
          data_nascimento: f.data_nascimento,
          posicao: f.posicao,
          categoria: f.categoria,
          cidade: f.cidade,
          estado: f.estado,
          clube_atual: f.clube_atual ?? '',
          bio: f.bio ?? '',
        })
      })
      .catch(e => setErro(e.detail))
  }, [eu?.atleta_id])

  // DEPOIS de todos os hooks (regra do React: hook nunca pode ficar
  // atrás de return condicional), a guarda da rota:
  if (!token) return <Navigate to="/login" replace />

  // Só um erro de CARREGAMENTO inicial derruba a página (sem `eu` não dá
  // pra renderizar nada). Erros de AÇÃO (salvar/enviar) são mostrados
  // embaixo do título — assim o formulário NÃO some da tela do usuário.
  if (!eu && erro) return <div className="pagina"><p className="erro">Erro: {erro}</p></div>
  if (!eu) return <div className="pagina"><p>Carregando…</p></div>

  // PUT /perfil/completar: cria OU atualiza (o backend decide)
  async function salvarFicha(e) {
    e.preventDefault()
    setErro(null); setOk(null); setSalvando(true)   // botão vira "Salvando…"
    try {
      await api('/perfil/completar', { method: 'PUT', corpo: ficha })
      setOk('Ficha salva! 🎉')
      // Primeira vez criando a ficha: /auth/me ainda não tinha atleta_id.
      // Recarrega pra "quem me viu" e vídeos aparecerem sem relogar.
      if (!eu.atleta_id) setEu(await api('/auth/me'))
    } catch (e) {
      setErro(e.detail)                              // fica inline, sem sumir com a página
    } finally {
      setSalvando(false)                             // roda sempre (sucesso ou erro)
    }
  }

  // POST /videos/upload — multipart (arquivo + título)
  async function enviarVideo(e) {
    e.preventDefault()
    setErro(null); setOk(null)
    if (!arquivo) { setErro('Escolha um arquivo de vídeo'); return }
    setEnviando(true)                                // botão vira "Enviando…"
    try {
      const form = new FormData()             // "envelope" multipart
      form.append('arquivo', arquivo)          // chave = mesmo nome do backend
      form.append('titulo', tituloVideo)
      await api('/videos/upload', { method: 'POST', corpo: form })
      setOk('Vídeo enviado! 🎉')
      setArquivo(null); setTituloVideo('')
      // recarrega a lista
      setMeusVideos(await api(`/perfil/${eu.atleta_id}/videos`))
    } catch (e) { setErro(e.detail) }
    finally { setEnviando(false) }
  }

  function campo(nome, tipo = 'text') {
    return (
      <input
        type={tipo}
        value={ficha[nome]}
        onChange={e => setFicha({ ...ficha, [nome]: e.target.value })}
      />
    )
  }

  return (
    <div className="pagina">
      <h1>Minha conta</h1>
      {ok && <p className="sucesso">{ok}</p>}
      {erro && <p className="erro">{erro}</p>}

      {/* ---- Dados da conta ---- */}
      <section className="cartao-secao">
        <h2>Dados da conta</h2>
        <p>
          {eu.nome ?? '(sem nome)'} · {eu.email}<br />
          Tipo: <b>{eu.tipo_usuario}</b> · Plano: {eu.plano}
        </p>
        {eu.atleta_id && (
          <Link to={`/perfil/${eu.atleta_id}`}>Ver meu perfil público →</Link>
        )}
      </section>

      {/* ---- Form da ficha: só quem tem atleta_id vê ---- */}
      {eu.tipo_usuario === 'atleta' && (
        <>
          <section className="cartao-secao">
            <h2>{eu.atleta_id ? 'Editar ficha do atleta' : 'Criar ficha de atleta'}</h2>
            <form onSubmit={salvarFicha} className="grade-campos">
              <label>Data de nascimento {campo('data_nascimento', 'date')}</label>
              <label>Posição {campo('posicao')}</label>
              <label>Categoria {campo('categoria')}</label>
              <label>Cidade {campo('cidade')}</label>
              <label>Estado (UF) {campo('estado')}</label>
              <label>Clube atual {campo('clube_atual')}</label>
              <label className="largura-toda">Bio {campo('bio')}</label>
              <button type="submit" className="largura-toda" disabled={salvando}>
                {salvando ? 'Salvando…' : 'Salvar ficha'}
              </button>
            </form>
          </section>

          {/* ---- Quem me viu ---- */}
          {views && (
            <section className="cartao-secao">
              <h2>👀 Quem viu meu perfil</h2>
              <p>
                <b>{views.total_visitas}</b> visitas ·{' '}
                <b>{views.visitantes_unicos}</b> pessoas únicas ·{' '}
                <b>{views.visitas_anonimas}</b> anônimas
              </p>
              <ul className="lista-recentes">
                {views.visitantes_recentes.map((v, i) => (
                  <li key={i}>
                    {v.nome ?? 'Visitante anônimo'}{' '}
                    <span>{new Date(v.visto_em).toLocaleString('pt-BR')}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* ---- Upload de vídeo ---- */}
          <section className="cartao-secao">
            <h2>🎬 Enviar vídeo (.mp4, .mov ou .webm)</h2>
            <form onSubmit={enviarVideo} className="grade-campos">
              <label>Título
                <input value={tituloVideo} onChange={e => setTituloVideo(e.target.value)} required />
              </label>
              <label>Arquivo
                <input type="file" accept=".mp4,.mov,.webm" onChange={e => setArquivo(e.target.files[0])} required />
              </label>
              <button type="submit" className="largura-toda" disabled={enviando}>
                {enviando ? 'Enviando…' : 'Enviar vídeo'}
              </button>
            </form>
            <h3>Meus vídeos ({meusVideos.length})</h3>
            <ul className="lista-videos">
              {meusVideos.map(v => (
                <li key={v.id}>{v.titulo} <span>{v.tipo_origem}</span></li>
              ))}
            </ul>
          </section>
        </>
      )}

      {/* ---- Área do olheiro ---- */}
      {eu.tipo_usuario === 'olheiro' && (
        <section className="cartao-secao">
          <h2>🔭 Área do olheiro</h2>
          <p>Favoritos e mensagens ficam nas próximas telas. Por ora, explore a <Link to="/">vitrine</Link>.</p>
        </section>
      )}
    </div>
  )
}
