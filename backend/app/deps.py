# ==========================================================================
# DEPENDÊNCIAS COMPARTILHADAS — o "guarda de porta" das rotas protegidas
#
# - Dependência (Depends) = algo que o FastAPI resolve ANTES de rodar seu
#   endpoint, te entregando pronto o que você pediu. Aqui: "me dá o usuário
#   DONO deste token" — e, se não der, ele nem chega no endpoint.
#
# - HTTPBearer = lê o cabeçalho `Authorization: Bearer <token>` da requisição.
#   auto_error=False = NÃO deixa o FastAPI responder sozinho (403); respondemos
#   401 nós mesmos pra todas as falhas usarem o MESMO código/mensagem.
#   Ele também faz o botão "Authorize" aparecer no Swagger 😉
# ==========================================================================

# Depends injeta; HTTPBearer lê o header; HTTPAuthorizationCredentials = o token extraído; HTTPException = erro HTTP
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario
from app.security import verificar_token

# Instância do esquema Bearer (token no cabeçalho Authorization)
bearer = HTTPBearer(auto_error = False)


# ---------------------------------------------------------------------------
# get_current_user — transforma "token recebido" em "objeto Usuario do banco"
# ---------------------------------------------------------------------------
def get_current_user(
    # O FastAPI lê o header Authorization e entrega o token já extraído
    credenciais: HTTPAuthorizationCredentials | None = Depends(bearer),
    # E abre uma sessão do banco (mesma tomada do cadastro/login)
    db: Session = Depends(get_db)
) -> Usuario:
    # 1) Nem mandou token -> 401 (mesmo código de "senha errada": nada de detalhes)
    if credenciais is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = 'Token ausente',
            headers = {'WWW-Authenticate': 'Bearer'}
        )

    # 2) Assinatura quebrada ou expirada -> verificar_token devolve None
    payload = verificar_token(credenciais.credentials)
    if payload is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = 'Token inválido ou expirado',
            headers = {'WWW-Authenticate': 'Bearer'}
        )

    # 3) Token ok -> pega o id de dentro ('sub') e carrega o usuário REAL
    usuario = db.query(Usuario).filter(Usuario.id == int(payload['sub'])).first()

    # 4) Caso raro: token válido de conta que foi apagada depois
    if usuario is None:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = 'Usuário não encontrado'
        )

    # 5) Entrega o usuário para o endpoint usar
    return usuario
