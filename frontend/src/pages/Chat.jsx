// =============================================================================
// PÁGINA: CONVERSA (CHAT) — Fase 11.2
//
// O QUE FAZ: abre o histórico de mensagens com UMA pessoa (o id vem na URL:
// /mensagens/4 = conversa com o usuário 4). Mostra as falas em "bolhas",
// marca o que veio como NÃO LIDO como lido ao abrir, e tem campo de envio.
//
// POR QUÊ: é a tela onde a conversa realmente acontece — a caixa (11.1) é
// só a lista de quem falou com quem; aqui se lê e se responde.
//
// ENDPOINTS USADOS (backend pronto, Fase 4 — zero mudança no servidor):
//   - GET  /mensagens/conversa/{id} → histórico (cronológico)
//   - GET  /mensagens/conversas     → só pra descobrir o NOME do outro
//                                     (o histórico vem só com ids)
//   - PUT  /mensagens/lidas/{id}     → ao abrir, zera o badge vermelho
//   - POST /mensagens                → envia; 201 = ok, 403 = LGPD (aviso)
//
// REGRA DE ACESSO: qualquer logado (atleta E olheiro), igual à caixa.
// =============================================================================
import { useEffect, useRef, useState } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'
import './Chat.css'

export default function Chat() {
    // useParams lê o pedaço variável da URL, tipo: "/mensagens/4" → { usuarioId: "4" }
    const {usuarioId} = useParams()
    const {logado, usuario} = useAuth()                 // usuario = EU (pra saber se a fala é minha)
    const [mensagens, setMensagens] = useState(null)    // null = ainda carregando
    const [nome, setNome] = useState('Conversa')        // nome do outro (encontra nas conversas)
    const [erro, setErro] = useState(null)              
    const [texto, setTexto] = useState('')              // o que está sendo digitado
    const [aviso, setAviso] = useState(null)            // erro de envio / aviso LGPD
    const fimRef = useRef(null)                         // 'ponteiro' pro fim da lista (pra rolar sozinho)

    // Carrega histórico + nome em paralelo (Promise.all = as 2 ao mesmo tempo - se uma falhas, cai no catch junto
    // isso é mais rápido que uma atrás da outra)
    // ou seja, busca o histórico de mensagens da conversa, a lista de conversas, armazena as mensagens no estado do React,
    // descobre nome de outra pessoa, verifica mensagens não lidas e se existirem marca como lidas
    // caso ocorra um erro nas 2 requisições principais apresenta mensagem de erro
    useEffect(() => {
        if (!logado) return
        Promise.all([
            // 2 requisições simultâneas e assíncronas (ao mesmo tempo, sem fila)
            api(`/mensagens/conversa/${usuarioId}`),
            api('/mensagens/conversas'),
        ])
        // recebe os resultados das requisições depois de ammas terem sucesso
        // abaixo uma arrow function que desestrutura o array já que Promise devolveu juntas
        .then(([hist,convs]) => {
            setMensagens(hist)      // atualiza o estado mensagens com histórico recebido da API
            const outro = convs.find(c => c.usuario_id === Number(usuarioId))
            if (outro) setNome(outro.nome ?? 'Conversa')
            
            // Abriu a conversa -> o que veio dele e está não-lido passa a lido
            // .some = 'existe alguma?' (só vale a pena chamar o PUT se sim)
            // .catch vazio = se o PUT falhar, seguimos (badge atrassa, não quebra)
            const temNaoLidas = hist.some(m => m.remetente_id === Number(usuarioId) && !m.lida)
            if (temNaoLidas) api(`/mensagens/lidas/${usuarioId}`, {method: 'PUT'}).catch(() => {})
        })
        .catch(e => setErro(e.detail ?? 'Não foi possível carregar a conversa'))
    }, [logado, usuarioId])

    // Rola pro fim SEMPRE que a lista muda (abriu = ultima mensagem enviou = sua fala nova)
    // Este é o comportamento de app de chat
    useEffect(() => {
        fimRef.current?.scrollIntoView({behavior: 'smooth'})
    }, [mensagens])

    // Envia a mensagem digitada (onSubmit do form)
    // Exemplo: estamos em uma conversa e digitamos: 'Olá, tudo bem?"
    // Ao clicar em enviar: impede formulário recarregar página, remove espaços denevcessários
    // verifica se existe conteúdo para enviar, limpa eventuais avisos anteriores, envia a mensagem para o servidor
    // recebe a mensagem salva pelo servidor, adiciona mensagem ao histórico exibido na tela, limpa campo de digitação e
    // caso ocorra erros, apresenta um aviso
    async function enviar(e) {
        e.preventDefault()               // impede reccaregamento padrão do fomulário
        const conteudo = texto.trim()   // .trim() = remove espaços das pontas
        if (!conteudo) return           // interrompe caso esteja vazia
        setAviso(null)                  // limpa uma mensagem de aviso ou erro que tenha aparecido antes

        // tenta enviar a mensagem para a API solicitando a criação de uma nova mensagem
        try {
            const nova = await api('/mensagens', {
                method: 'POST',
                corpo: {destinatario_id: Number(usuarioId), conteudo}, 
            })
            // 201: adiciona mensagem no FIM da lista local (sem refazer o GET)
            setMensagens([...mensagens, nova])
            setTexto('')
        } catch(e) {
            // 403 = LGPD: olheiro tentou falar com menos sem responsável
            setAviso(e.status === 403           // comparação estrita
                ? (e.detail ?? 'Envio não permitido pela LGPD')     // se for 403 usa esse caso
                : (e.detail ?? 'Não foi possível enviar.'))         // se for diferente usa esse
        }
    }

    // Portões: espera → erro → carregando → conteúdo (padrão das outras páginas)
    if (!logado) return <Navigate to='/login' replace />    // se não logado, redireciona para login
    if (erro) return <div className='pagina'><p className='erro'>Erro: {erro}</p></div>     // se houver erro, exibe a mensagem
    if (mensagens === null) return <div className='pagina'><p>Carregando…</p></div>     // se as mensagens ainda não foram carregadas (null), exibe 'Carregando'

     return (
        <div className='pagina'>
            <Link to='/mensagens' className='voltar'>← Voltar</Link>
            <h1>💬 {nome}</h1>

            <div className='bolhas'>
                {/* Estado vazio: conversa existe mas ninguém falou nada ainda */}
                {mensagens.length === 0 && (
                    <p className='vazio'>Nenhuma mensagem ainda — diga oi!</p>
                )}

                {mensagens.map(m => {
                    // remetente_id === meu id → é MINHA fala (verde, direita)
                    const minha = m.remetente_id === usuario?.id
                    return (
                        <div key={m.id} className={`bolha ${minha ? 'minha' : 'outra'}`}>
                            <p>{m.conteudo}</p>
                            {/* hora curta "16:15" — o ISO completo é ruído visual */}
                            <span className='hora'>
                                {new Date(m.criado_em).toLocaleTimeString('pt-BR',
                                    { hour: '2-digit', minute: '2-digit' })}
                            </span>
                        </div>
                    )
                })}
                {/* Alvo invisível: scrollIntoView leva o scroll até ele (= fim) */}
                <div ref={fimRef} />
            </div>

            {/* Aviso de erro/LGPD aparece SOBRE o campo, em vermelho */}
            {aviso && <p className='aviso'>{aviso}</p>}

            <form className='enviar' onSubmit={enviar}>
                <input
                    value={texto}
                    onChange={e => setTexto(e.target.value)}   // controlled: valor = estado
                    placeholder='Escreva uma mensagem…'
                    maxLength={2000}   // mesmo limite do backend (schemas)
                />
                <button className='botao' disabled={!texto.trim()}>Enviar</button>
            </form>
        </div>
    )
}