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

# ==========================================================================
# CORS — "portaria entre domínios diferentes"
#
# Em produção o frontend mora em scoutbase-two.vercel.app e a API em
# scoutbase-api-a6qm.onrender.com. Sem CORS, o navegador BLOQUEIA a chamada
# (regra de segurança: site A não fala com site B sem autorização).
#
# - CORSMiddleware = "portaria" pronta do FastAPI que responde com o
#   cabeçalho "pode vir" para os domínios da lista.
# - allow_origins = quem pode falar comigo (dev local + o endereço real
#   do Vercel — scoutbase-two.vercel.app, descoberto no deploy 12.5).
# - allow_credentials = permite envio de credenciais (mantemos True
#   por padrão de mercado; nosso token vai no header Authorization).
# - allow_methods/allow_headers = libera todos os verbos (GET, POST...)
#   e cabeçalhos (Authorization, Content-Type) — em produção real
#   restringiríamos, em MVP liberamos tudo pra não travar em teste.
# ==========================================================================
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins = [
        "http://localhost:5173",          # dev: o Vite (vite na porta 5173)
        "https://scoutbase-two.vercel.app",   # produção: endereço real do Vercel (12.5)
    ],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

# Encaixa o bloco de rotas de autenticação (prefixo /auth) no app principal
# Sem essa linha, as rotas do router existiriam mas ninguém conseguiria chamá-las
# Encaixa as rotas de perfil (prefixo /perfil) no app principal
from app.routers.auth import router as auth_router
from app.routers.perfil import router as perfil_router
from app.routers.videos import router as videos_router
from app.routers.estatisticas import router as estatisticas_router
from app.routers import atletas, auth, avaliacoes, dashboard, estatisticas, mensagens, olheiro, perfil, responsaveis, videos

app.include_router(auth_router)
app.include_router(perfil_router)
app.include_router(videos_router)
app.include_router(estatisticas_router)
app.include_router(atletas.router)
app.include_router(olheiro.router)
app.include_router(mensagens.router)
app.include_router(responsaveis.router)
app.include_router(avaliacoes.router)
app.include_router(dashboard.router)

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

