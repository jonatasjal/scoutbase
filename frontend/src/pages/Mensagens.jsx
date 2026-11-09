// =============================================================================
// PÁGINA: CAIXA DE ENTRADA DE MENSAGENS (Fase 11.1)
//
// O QUE FAZ: mostra a lista de conversas do usuário logado — cada linha é
// "com quem eu falei", com nome, última mensagem, data e quantas mensagens
// ainda estão SEM LER (badge vermelho). Clicar numa linha leva pro chat.
//
// POR QUÊ: é o ponto central de entrada do sistema de mensagens (igual a
// aba de conversas do WhatsApp). Sem ela, não existiria como ver quem
// mandou mensagem pra você.
//
// DEPENDÊNCIAS: o backend já está pronto (Fase 4 + commit 476f1da) —
// esta página só CONSOME os endpoints, não muda nada no servidor:
//   - GET /mensagens/conversas  → a lista exibida
// (o envio e o histórico são do Bloco 11.2)
//
// REGRA DE ACESSO: qualquer tipo de usuário logado usa chat (atleta E
// olheiro) — diferente dos favoritos, aqui NÃO checamos ehOlheiro.
// =============================================================================
import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import './Mensagens.css'

export default function Mensagens() {
    const { logado } = useAuth()
    const [conversas, setConversas] = useState(null)  // null = ainda carregando
    const [erro, setErro] = useState(null)

    // Busca as conversas só depois de saber que está logado (senão 401)
    useEffect(() => {
        if (!logado) return
        api('/mensagens/conversas')
            .then(setConversas)
            .catch(e => setErro(e.detail ?? 'Não foi possível carregar as conversas'))
    }, [logado])

    // Portões de renderização: espera → erro → carregando → conteúdo
    if (!logado) return <Navigate to='/login' replace />
    if (erro) return <div className='pagina'><p className='erro'>Erro: {erro}</p></div>
    if (conversas === null) return <div className='pagina'><p>Carregando…</p></div>

    // Data curta: "21/10 16:15" — sem isso aparece "2026-10-21T16:15:27.522845" (ruído)
    function formatarData(iso) {
        const d = new Date(iso)
        const dia = String(d.getDate()).padStart(2, '0')
        const mes = String(d.getMonth() + 1).padStart(2, '0')
        const hora = String(d.getHours()).padStart(2, '0')
        const min = String(d.getMinutes()).padStart(2, '0')
        return `${dia}/${mes} ${hora}:${min}`
    }

    return (
        <div className='pagina'>
            <h1>💬 Mensagens</h1>

            {/* Estado vazio: não é "deu erro", é "você ainda não conversou" */}
            {conversas.length === 0 && (
                <div className='estado-vazio'>
                    <p>Nenhuma conversa ainda — visite um perfil e clique em 💬 Mensagem</p>
                    <Link className='botao' to='/'>Ver atletas na vitrine</Link>
                </div>
            )}

            <ul className='lista-conversas'>
                {conversas.map(c => (
                    <li key={c.usuario_id}>
                        {/* Cada linha é um Link: clicar abre a conversa (11.2) */}
                        <Link to={`/mensagens/${c.usuario_id}`} className='linha-conversa'>
                            <div className='linha-info'>
                                <strong>{c.nome ?? 'Usuário'}</strong>
                                {/* truncate = corta o texto na ponta com "…" (CSS) */}
                                <span className='ultima-msg'>{c.ultima_mensagem}</span>
                            </div>
                            <div className='linha-lado'>
                                <span className='data'>{formatarData(c.ultima_data)}</span>
                                {/* Badge vermelho só quando tem não-lidas (0 não aparece) */}
                                {c.nao_lidas > 0 && <span className='badge'>{c.nao_lidas}</span>}
                            </div>
                        </Link>
                    </li>
                ))}
            </ul>
        </div>
    )
}