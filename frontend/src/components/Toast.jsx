// Toast.jsx — aviso flutuante que SOZINHO some da tela (padrão "toast")
// Ideia: sucesso é mensagem passageira — aparece, cumpre o aviso e some,
// sem exigir clique. Erro continua inline (precisa ser LIDO com atenção).
//
// Uso: <Toast mensagem={ok} aoSumir={() => setOk(null)} />
// - mensagem: texto a exibir (null/vazio = não renderiza nada)
// - aoSumir: chamado após ~3s — o "pai" limpa o estado (setOk(null))
import { useEffect, useRef } from 'react'
import './Toast.css'

export default function Toast({ mensagem, aoSumir }) {
  // Espelho estável da callback: guardamos a ÚLTIMA recebida num ref.
  // Por quê? Arrow function nova a cada render reiniciaria o timer do
  // zero dentro do useEffect — e o toast nunca sumiria.
  const refAoSumir = useRef(aoSumir)

  // Regra do React: NÃO se escreve em ref durante o render — só dentro
  // de um effect. Este roda sempre que aoSumir chega nova (a cada render
  // do pai, se for arrow function inline) e mantém o espelho atualizado.
  useEffect(() => {
    refAoSumir.current = aoSumir
  }, [aoSumir])

  useEffect(() => {
    if (!mensagem) return                 // sem mensagem, sem timer
    const timer = setTimeout(() => refAoSumir.current(), 3000)
    return () => clearTimeout(timer)      // cancela se trocar antes dos 3s
  }, [mensagem])                          // só a mensagem (re)inicia a contagem

  if (!mensagem) return null              // nada a avisar = não ocupa espaço

  return (
    // role="status" = leitores de tela anunciam sem interromper (acessibilidade)
    <div className="toast" role="status">
      {mensagem}
    </div>
  )
}
