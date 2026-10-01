# ==========================================================================
# - app = FastAPI(...) — é como criar o restaurante: cria o "prédio" onde tudo vai acontecer. O title e o version são só o nome na fachada e a versão do cardápio — aparecem na página de documentação que o FastAPI gera sozinho (em /docs, tipo um cardápio online automático).
# - @app.get('/health') — aqui entra o decorator (em português, "decorador"): é uma palavra estranha que significa "etiqueta". A etiqueta diz: "quando alguém digitar meusite.com/health no navegador, execute a função de baixo". O get é o tipo de pedido — o mais simples, usado só para pegar/ler informação (outro famoso é post, para enviar dados).
# - def health(): — a função (o "prato") que roda quando chamam o endereço. Ela devolve um dicionário {'status': 'ok'}, que o FastAPI automaticamente transforma em JSON (o formato padrão de resposta de APIs — é só texto organizado que qualquer programa entende) e responde com código 200 ("deu certo").
# - Por que um endpoint /health? — É o "estou vivo?" da aplicação. Ferramentas de monitoramento, o Docker ou um servidor de hospedagem chamam esse endereço de tempos em tempos; se não responder ok, eles avisam que o sistema caiu.
# ==========================================================================

# Importa a classe que cria a aplicação web (servidor + roteador + docs automáticas)
from fastapi import FastAPI

# Cria a instância da API; title/version aparecem em /docs (Swagger) e /redoc
app = FastAPI(title= 'ScouteBase API', version = '0.1.0')

# Rota /health
@app.get('/health')
def health():
    # Retorn o json abaixo - A FastAPI serializa e responde HTTP 200
    return {'status': 'ok'}
