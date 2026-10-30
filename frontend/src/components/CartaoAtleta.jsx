// CartaoAtleta.jsx — o "cartão-postal" de um atleta na vitrine
// Componente = peça reutilizável; recebe dados via "props" (atributos)
import { Link } from 'react-router-dom'
import './CartaoAtleta.css'


export default  function CartaoAtleta({ atleta }) {
    // Em vez de receber 'props' e ter que acessar 'props.atleta'o tempo todo, a desestruturação ({atleta})
    // já extrai diretamete a propriedade 'atleta' do objeto de parâmetros, deixando o código mais limpo
    
    // Contas antigas podem ter o campo 'nome' como null ou undefined, por isso o operador '??'
    // retorna o valor do lado direito apenas quando o operando do lado esquerdo for null ou undefined (ou ausente)
    // isso evita erros de renderização e garante que não irá quebrar
    const nome = atleta.nome ?? 'Atleta'

    return (
        // Em aplicações React modernas, usar tag HTML padrão <a href...> faria com que o navegador recarregasse a página inteira
        // perdendo o estado da aplicação e gerando atraso visual, o componente <Link> intercepta o clique, altera a URL dinamicamente
        // via JS e renderiza a nova página de forma instantânea e fluída
        <Link to = {`/perfil/${atleta.id}`} className = 'cartao'>
            {/* Cria avatares visuais (letra inicial do nome) rápidos quando não há foto de perfil cadastrada */}
            <div className= 'cartao-avatar'>{nome[0].toUpperCase()}</div>
            <h3>{nome}</h3>
            <p>⚽ {atleta.esporte} · {atleta.posicao}</p>
            <p>📍 {atleta.cidade}/{atleta.estado} · {atleta.idade} anos</p>
            {/* Como nem todo atleta possui um clube atual cadastrado, colocamos operador lógico para exibir caso tenha */}
            {atleta.clube_atual && <p>🏟️ {atleta.clube_atual}</p>}
            <span className = 'cartao-categoria'>{atleta.categoria}</span>
        </Link>
    )
}