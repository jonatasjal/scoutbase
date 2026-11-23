# ==========================================================================
# ROTA DE AUTENTICAÇÃO — cadastro (Fase 1)
#
# - APIRouter — "sub-restaurante": um bloco de rotas agrupadas que depois
#   encaixamos no main.py com include_router. Aqui tudo começa com /auth/...
#   (o prefixo do router). Por quê separar? Porque o sistema vai crescer:
#   cadastro aqui, perfil na Fase 2, busca na Fase 3... sem virar bagunça.
#
# - @router.post('/cadastro') — POST = "enviar/você está me dando dados"
#   (GET é só pedir para ler). Cadastro precisa de POST porque CHEGA um
#   JSON novo para ser gravado.
#
# - response_model=UsuarioSaida + status_code=201:
#   devolve só o que combinamos no schema de SAÍDA (sem senha!) e com o
#   código 201 = "Criado" (200 é "ok sem criar"; 201 avisa que nasceu algo).
#
# - Depends(get_db) — pede ao FastAPI: "antes de rodar, abra uma sessão
#   do banco e me entregue em `db`".
# ==========================================================================

# APIRouter agrupa rotas; HTTPException lança erros HTTP (409, 400...); status tem códigos prontos
from fastapi import APIRouter, Depends, HTTPException, status
# Session = tipo da sessão do banco
from sqlalchemy.orm import Session

# Tomada de conexão com o banco, model Usuario, schema de entrada/saída, hash de senha
from app.database import get_db
from app.models import Usuario, Atleta, TipoUsuario
from app.schemas import UsuarioCadastro, UsuarioLogin, Token, UsuarioSaida, EuSaida, EsqueciSenhaEntrada, EsqueciSenhaSaida, RedefinirSenhaEntrada
# verificar_senha = confere a senha; criar_token = emite o crachá JWT
from app.security import hash_senha, verificar_senha, criar_token
# O guarda de porta: só entrega o usuário se o token da requisição for válido
from app.deps import get_current_user

# Fase 15: secrets = token aleatorio; hashlib = resumo (hash) do token
import secrets
import hashlib
# datetime p/ calcular a validade (30 min) do token
from datetime import datetime, timedelta, timezone
# settings = configuracoes do .env (DEBUG, SMTP); enviar_email_reset = o "correio"
from app.config import settings
from app.email import enviar_email_reset

# Cria o roteador: todas as rotas daqui terão o caminho inicial /auth
router = APIRouter(prefix = '/auth', tags = ['auth'])


# ---------------------------------------------------------------------------
# POST /auth/cadastro — cria a conta (atleta ou olheiro)
# ---------------------------------------------------------------------------
@router.post('/cadastro', response_model = UsuarioSaida, status_code = status.HTTP_201_CREATED)
def cadastro(dados: UsuarioCadastro, db: Session = Depends(get_db)):
    # 1) Existe alguém com esse e-mail? (query = SELECT no banco)
    email_existe = db.query(Usuario).filter(Usuario.email == dados.email).first()

    # 2) Se sim, NÃO cadastra de novo (409 = "conflito": recurso já existe)
    if email_existe:
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = 'E-mail já cadastrado'
        )

    # 3) Monta a linha nova — A SENHA NUNCA VAI PURA: passa pelo hash_senha()
    novo_usuario = Usuario(
        nome = dados.nome,
        email = dados.email,
        senha_hash = hash_senha(dados.senha),
        tipo_usuario = dados.tipo_usuario
        # plano e criado_em pegam os defaults do model (gratuito / now())
    )

    # 4) add = anexa na sessão (rascunho); commit = grava de vez no banco
    db.add(novo_usuario)
    db.commit()
    # refresh = devolve a linha com o que o BANCO gerou (id, criado_em...)
    db.refresh(novo_usuario)

    # 5) Retorna 201 com UsuarioSaida (o Pydantic esconde senha_hash sozinho)
    return novo_usuario


# ---------------------------------------------------------------------------
# POST /auth/login — valida email+senha e DEVOLVE o token (o crachá JWT)
# ---------------------------------------------------------------------------
@router.post('/login', response_model = Token)
def login(dados: UsuarioLogin, db: Session = Depends(get_db)):
    # 1) Procura o usuário pelo e-mail
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()

    # 2) CHECAGEM ÚNICA E GENÉRICA: se não achou OU a senha não bate,
    #    a resposta é SEMPRE a mesma mensagem (401) — por quê? Se dissessemos
    #    "esse e-mail não existe", um invasor descobriria quais emails têm
    #    conta no sistema (enumeração). Assim ele nunca sabe qual dos 2 errou.
    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = 'E-mail ou senha incorretos',
            # Padrão RFC: avisa que a rota usa Bearer (aparece nas docs)
            headers = {'WWW-Authenticate': 'Bearer'}
        )

    # 3) Senha ok -> emite o crachá (id + tipo valem 60 min)
    #    .value = o texto do enum ('atleta'), não o objeto TipoUsuario.atleta
    token = criar_token(usuario.id, usuario.tipo_usuario.value)

    # 4) 200 com {"access_token": "...", "token_type": "bearer"}
    return Token(access_token = token)


# ---------------------------------------------------------------------------
# GET /auth/me — "quem sou eu?" com token válido (primeira rota PROTEGIDA)
# ---------------------------------------------------------------------------
@router.get('/me', response_model = EuSaida)
def meu_perfil(usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    # Se o token passou no guarda, temos o usuario — falta a ficha de atleta (se houver)
    atleta_id = None
    if usuario.tipo_usuario == TipoUsuario.atleta:
        ficha = db.query(Atleta).filter(Atleta.usuario_id == usuario.id).first()
        if ficha is not None:
            atleta_id = ficha.id
    # model_dump() = "desmonta" o schema em dicionário comum {...}
    dados = UsuarioSaida.model_validate(usuario).model_dump()
    return EuSaida(**dados, atleta_id = atleta_id)


# ---------------------------------------------------------------------------
# POST /auth/esqueci-senha — pede um token de redefinição (sem login)
# ---------------------------------------------------------------------------
@router.post('/esqueci-senha', response_model = EsqueciSenhaSaida)
def esqueci_senha(dados: EsqueciSenhaEntrada, db: Session = Depends(get_db)):
    # 1) Procura a conta (se não existir, a gente NEM AVISA - ver passo 3)
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()

    token = None
    if usuario:
        # 2) token aleatório (com 43 caracteres) - dificulta adivinhação
        token = secrets.token_urlsafe(32)
        # Guardamos o RESUMO (sha26) não o token: banco vaza, token não serv
        usuario.reset_token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        # Validade: 30min a partir de AGORA (UTC sem fuso par ao banco não se confundir)
        usuario.reset_token_expira = datetime.now(timezone.utc).replace(tzinfo = None) + timedelta(minutes = 30)
        db.commit()     # grava o pedido no banco
        # 3) Manda o e-mail (ou simula, se não tiver o SMTP)
        enviar_email_reset(dados.email, token)

    # 4) Resposta SEMPRE igual, exista conta ou não, pois se dissesse que "não existe"
    # algum invasor usaria a rota para descobrir quais emails tem conta (através de enumeração)
    resposta = {'detalhe': 'Se este e-mail estiver cadastrado, enviaremos instruções de redefinição'}

    # 5) DEBUG = true (só na máquina local): devolve o token na resposta para testar
    # sem precisar de SMTP. Em produção isso NUNCA rroda (debug = False)
    if token and settings.debug:
        resposta['token'] = token
    return resposta
