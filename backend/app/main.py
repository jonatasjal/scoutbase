# ==========================================================================
# - app = FastAPI(...) — é como criar o restaurante: cria o "prédio" onde tudo vai acontecer. O title e o version são só o nome na fachada e a versão do cardápio — aparecem na página de documentação que o FastAPI gera sozinho (em /docs, tipo um cardápio online automático).
# - @app.get('/health') — aqui entra o decorator (em português, "decorador"): é uma palavra estranha que significa "etiqueta". A etiqueta diz: "quando alguém digitar meusite.com/health no navegador, execute a função de baixo". O get é o tipo de pedido — o mais simples, usado só para pegar/ler informação (outro famoso é post, para enviar dados).
# - def health(): — a função (o "prato") que roda quando chamam o endereço. Ela devolve um dicionário {'status': 'ok'}, que o FastAPI automaticamente transforma em JSON (o formato padrão de resposta de APIs — é só texto organizado que qualquer programa entende) e responde com código 200 ("deu certo").
# - Por que um endpoint /health? — É o "estou vivo?" da aplicação. Ferramentas de monitoramento, o Docker ou um servidor de hospedagem chamam esse endereço de tempos em tempos; se não responder ok, eles avisam que o sistema caiu.
# ==========================================================================

# Importa a classe que cria a aplicação web (servidor + roteador + docs automáticas)
from fastapi import FastAPI

# Importa o "servidor de arquivos estáticos" (imagens, vídeos...)
# e o os.path para montar o caminho da pasta
import os
from fastapi.staticfiles import StaticFiles

# Importa a resposta de "página mudou de endereço" (redirect) usada na rota /
from fastapi.responses import RedirectResponse

# Cria a instância da API; title/version aparecem em /docs (Swagger) e /redoc
app = FastAPI(title= 'ScouteBase API', version = '0.1.0')

# Encaixa o bloco de rotas de autenticação (prefixo /auth) no app principal
# Sem essa linha, as rotas do router existiriam mas ninguém conseguiria chamá-las
# Encaixa as rotas de perfil (prefixo /perfil) no app principal
from app.routers.auth import router as auth_router
from app.routers.perfil import router as perfil_router
from app.routers.videos import router as videos_router
from app.routers.estatisticas import router as estatisticas_router
from app.routers import auth, perfil, videos, estatisticas, atletas, olheiro

app.include_router(auth_router)
app.include_router(perfil_router)
app.include_router(videos_router)
app.include_router(estatisticas_router)
app.include_router(atletas.router)
app.include_router(olheiro.router)

# ==========================================================================
# ROTAS
# ==========================================================================
# Rota /health
@app.get('/health')
def health():
    # Retorn o json abaixo - A FastAPI serializa e responde HTTP 200
    return {'status': 'ok'}

# Rota / — portaria da API: quem chegar na raiz é mandado pro /docs
# RedirectResponse = "esta página mudou de endereço" (código HTTP 307)
@app.get('/')
def home():
    return RedirectResponse('/docs')


# Abre a pasta backend/media para a internet (depois de todas as rotas).
# Agora /media/uploads/xxx.mp4 = arquivo backend/media/uploads/xxx.mp4.
# Tradução: "toda vez que pedir algo começando com /media/, entregue o
# arquivo equivalente dentro da pasta backend/media" (mount = pendurar
# a pasta no endereço; name = 'media' = apelido interno do FastAPI).
app.mount(
    '/media',       # endereço na internet
    StaticFiles(directory = os.path.join(os.path.dirname(__file__), '..', 'media')),   # pasta no disco
    name = 'media'
)

'''
O StaticFiles adivinha o tipo pelo final do nome do arquivo (.mp4 → vídeo, .png → imagem) e 
coloca o cabeçalho correto. Sem ele, o navegador receberia bytes soltos e 
não saberia se é música, foto ou planilha.
'''

