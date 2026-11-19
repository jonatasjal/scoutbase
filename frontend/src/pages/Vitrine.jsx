// Vitrine.jsx — a home: busca atletas na API e desenha os cartões
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import CartaoAtleta from '../components/CartaoAtleta'
import './Vitrine.css'

// "constantes" dos filtros (futebol é o único esporte da V1)
const ESTADOS = ['SP', 'RJ', 'MG', 'RS', 'PR', 'SC', 'BA', 'PE', 'CE', 'GO']

export default function Vitrine() {
  // === hooks (useState/useEffect): o estado do componente ===
  // dados = o que veio da API; setDados = função pra atualizar
  const [dados, setDados] = useState({ resultados: [], total: 0, pagina: 1, total_paginas: 1 })
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState(null)

  // filtros controlados: cada campo é um pedaço de estado
  const [posicao, setPosicao] = useState('')
  const [estado, setEstado] = useState('')
  const [categoria, setCategoria] = useState('')
  // busca tem DUAS versões (é o segredo do debounce):
  const [busca, setBusca] = useState('')              // o texto do input (muda a cada tecla)
  const [buscaNaApi, setBuscaNaApi] = useState('')    // o que VAI na requisição (muda só qd você para)
  const [pagina, setPagina] = useState(1)

  // DEBOUNCE: toda vez que o texto do input muda, espera 400ms...
  useEffect(() => {
    const timer = setTimeout(() => setBuscaNaApi(busca), 400)
    // ...mas se digitou de novo antes dos 400ms, CANCELA o timer anterior
    // (cleanup: o React roda isso quando 'busca' muda de novo ou a tela sai)
    return () => clearTimeout(timer)
  }, [busca])

  // useEffect = "roda quando ... muda"; [] = roda 1x ao abrir a tela
  // [posicao, estado, categoria, pagina] = refaz a busca quando algo muda
  useEffect(() => {
    setCarregando(true)
    // monta só os filtros preenchidos: {estado:'SP'} -> "?estado=SP"
    const params = { pagina }
    if (posicao) params.posicao = posicao
    if (estado) params.estado = estado
    if (categoria) params.categoria = categoria
    if (buscaNaApi) params.busca = buscaNaApi   // texto livre (nome, clube ou cidade)

    api('/atletas', { params })
      .then(d => { setDados(d); setErro(null) })
      .catch(e => setErro(e.detail))   // client.js joga {status, detail}
      .finally(() => setCarregando(false))
  }, [posicao, estado, categoria, pagina, buscaNaApi])

  return (
    <div className="vitrine">
      <h1>Atletas em destaque</h1>
      <p className="total">{dados.total} atleta(s) encontrado(s)</p>

      {/* barra de filtros */}
      <div className="filtros">
        <input
          type="search"
          placeholder="🔍 Buscar nome, clube ou cidade…"
          value={busca}
          onChange={e => { setBusca(e.target.value); setPagina(1) }}
        />

        <select value={posicao} onChange={e => { setPosicao(e.target.value); setPagina(1) }}>
          <option value="">Posição (todas)</option>
          <option value="goleiro">Goleiro</option>
          <option value="zagueiro">Zagueiro</option>
          <option value="meio-campo">Meio-campo</option>
          <option value="atacante">Atacante</option>
        </select>

        <select value={estado} onChange={e => { setEstado(e.target.value); setPagina(1) }}>
          <option value="">Estado (todos)</option>
          {ESTADOS.map(uf => <option key={uf} value={uf}>{uf}</option>)}
        </select>

        <select value={categoria} onChange={e => { setCategoria(e.target.value); setPagina(1) }}>
          <option value="">Categoria (todas)</option>
          <option value="sub-13">Sub-13</option>
          <option value="sub-15">Sub-15</option>
          <option value="sub-17">Sub-17</option>
          <option value="sub-20">Sub-20</option>
        </select>
      </div>

      {/* 3 estados possíveis da tela: carregando / erro / dados */}
      {carregando && <p>Carregando…</p>}
      {erro && <p className="erro">Erro: {erro}</p>}
      {/* nada encontrado com os filtros atuais */}
      {!carregando && !erro && dados.resultados.length === 0 && (
        <p>Nenhum atleta encontrado. Tente outro filtro ou texto.</p>
      )}

      <div className="grade">
        {dados.resultados.map(a => <CartaoAtleta key={a.id} atleta={a} />)}
      </div>

      {/* paginação: "◀ página 1 de 2 ▶" */}
      {dados.total_paginas > 1 && (
        <div className="paginacao">
          <button onClick={() => setPagina(p => p - 1)} disabled={pagina === 1}>◀</button>
          <span>Página {pagina} de {dados.total_paginas}</span>
          <button onClick={() => setPagina(p => p + 1)} disabled={pagina === dados.total_paginas}>▶</button>
        </div>
      )}
    </div>
  )
}