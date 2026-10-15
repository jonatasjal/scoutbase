# ==========================================================================
# ROTAS DE PERFIL — o atleta preenche a ficha; depois (2.3) ela é vista
# ==========================================================================
# APIRouter = "sub-servidor" de rotas com prefixo próprio (vimos em auth.py)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Conexão com o banco, models, schemas do perfil e o "guarda de porta"
from app.database import get_db
from app.models import Usuario, Atleta, TipoUsuario, VideoAtleta, EstatisticaAtleta
from app.schemas import PerfilAtletaDados, PerfilAtletaSaida, VideoSaida, EstatisticaSaida
from app.deps import get_current_user

# prefix = toda rota começa com /perfil ; tags = grupo no Swagger
router = APIRouter(prefix = '/perfil', tags = ['perfil'])

# ---------------------------------------------------------------------------
# PUT /perfil/completar — criar OU atualizar a ficha do atleta logado
# ---------------------------------------------------------------------------
# PUT (em vez de POST) = "coloque estes dados neste lugar" — a operação é
# IDEMPOTENTE: mandar 2x o mesmo body dá o mesmo resultado (não cria ficha dupla)
@router.put('/completar', response_model = PerfilAtletaSaida)
def completar_perfil(
    dados: PerfilAtletaDados,
    usuario: Usuario = Depends(get_current_user),   # sem token = 401 antes de tudo
    db: Session = Depends(get_db)
):
    #1) Quem é dono da ficha? O USUÁRIO DO TOKEN - não vem com "id" no bdody
    # Se viesse, um atle poderia poreencher o perfil de outro atleta (ataque!)
    # Por isso a identidade vem SEMPRE do token, nunca do corpo da mensagem

    # 2) Só atletas podem ter ficha de atleta (olheiro logado -> 403)
    if usuario.tipo_usuario != TipoUsuario.atleta:
        raise HTTPException(
            status_code = 403,
            detail = 'Apenas usuarios do tipo atleta possuem perfil de atleta'
        )
    # 3) Procura a ficha existente (relação 1-1: máximo de 1 por conta)
    atleta = db.query(Atleta).filter(Atleta.usuario_id == usuario.id).first()

    if atleta is None:
        # 3a) Primeira vez > cria: liga a ficha ao dono vindo do token
        atleta = Atleta(usuario_id = usuario.id, **dados.model_dump())
        db.add(atleta)
    else:
        # 3b) Já tem ficha > atualiza campo a campo (update)
        for campo, valor in dados.model_dump().items():
            setattr(atleta, campo, valor)
            # setattr(obj, 'cidade', 'SP') = mesmo que obj.cidade = 'SP'
    
    db.commit()         # grava de verdade no Postgres
    db.refresh(atleta)  # recarrega a linha: agora tem o 'id' que o banco gerou
    return atleta       # devolve a ficha atualizada (ou criada) para o cliente

# ---------------------------------------------------------------------------
# GET /perfil/{atleta_id} — ver a ficha de QUALQUER atleta (PÚBLICO)
# ---------------------------------------------------------------------------
# {atleta_id} = "variável na URL": /perfil/1, /perfil/2, /perfil/3...
# O FastAPI lê o número depois da barra e entrega em atleta_id (string "1"
# vira int automaticamente; "abc" vira erro 422 — nem chega na função).
#
# SEM Depends(get_current_user) de propósito! É público: o olheiro que ainda
# não tem conta pode olhar o vitrine antes de se cadastrar.
@router.get('/{atleta_id}', response_model = PerfilAtletaSaida)
def ver_perfil(atleta_id: int, db: Session = Depends(get_db)):
    # 1) Procura a ficha do atleta no banco
    atleta = db.query(Atleta).filter(Atleta.id == atleta_id).first()

    # 2) Se não achou esse atleta, devolve 404 (não encontrado) (padrão web: a página
    #    que o navegador mostra quando o link está quebrado)
    #    Repare: 404 e não 401 — aqui não é "falta de permissão",
    #    é "este atleta não existe".
    if atleta is None:
        raise HTTPException(
            status_code = 404,
            detail = 'Atleta não encontrado'
        )
    # 3) Devolve a ficha e o PerfilAtletaSaida garante que SÓ saiam dados públicos (sem email, sem senha, sem token)
    return atleta


# 3 detalhes importantes:
'''
Sem token = público — diferente do PUT /completar (que exige get_current_user). Mesmo arquivo, portas 
com regras diferentes. 404 e não 401 — 401 = "falta crachá"; 404 = "esse id não existe no mundo".
response_model = PerfilAtletaSaida — o escudo: mesmo que o objeto atleta no banco tenha campos 
internos, o Swagger só deixa passar os campos declarados no schema (por isso a senha/email nunca vazam).
'''

# ---------------------------------------------------------------------------
# GET /perfil/{atleta_id}/videos — lista os vídeos daquele atleta (PÚBLICO)
# ---------------------------------------------------------------------------
# O FastAPI separa dos outros por "nível de profundidade":
#   /perfil/1        -> ver_perfil      (1 nível)
#   /perfil/1/videos -> listar_videos   (2 níveis) — sem conflito!
@router.get('/{atleta_id}/videos', response_model = list[VideoSaida])
def listar_videos_do_perfil(atleta_id: int, db: Session = Depends(get_db)):
    # O atleta existe? Se não, 404 (mesma regra de ver_perfil)
    atleta = db.query(Atleta).filter(Atleta.id == atleta_id).first()
    if atleta is None:
        raise HTTPException(status_code = 404, detail = 'Atleta não encontrado')

    # Traz todos os vídeos do atleta, do mais novo para o mais antigo
    videos = (
        db.query(VideoAtleta)
        .filter(VideoAtleta.atleta_id == atleta_id)
        .order_by(VideoAtleta.data_upload.desc())
        .all()
    )
    return videos  # traz a lista inteira, o responde_model deixa só campos públicos

# ---------------------------------------------------------------------------
# GET /perfil/{atleta_id}/estatisticas — números públicos do atleta
# ---------------------------------------------------------------------------
# NOVIDADE: "query params" = filtros Opcionais depois do "?":
#   /perfil/1/estatisticas                    -> tudo
#   /perfil/1/estatisticas?temporada=2026     -> só a temporada 2026
#   /perfil/1/estatisticas?competicao=Copa+X  -> só aquela competição
# (o + ou %20 = espaço na URL). Quem não manda o filtro = None = "não filtra".
@router.get('/{atleta_id}/estatisticas', response_model = list[EstatisticaSaida])
def listar_estatisticas_do_perfil(
    atleta_id: int,
    competicao: str | None = None,      # padrão None = filtro desligado
    temporada: str | None = None,
    db: Session = Depends(get_db)
):
    # O atleta existe? (mesma regra das outras rotas públicas)
    atleta = db.query(Atleta).filter(Atleta.id == atleta_id).first()
    if atleta is None:
        raise HTTPException(status_code = 404, detail = 'Atleta não encontrado!')

    # Monta a busca em cadeia: começa básica e vai ganhando cláusulas
    consulta = db.query(EstatisticaAtleta).filter(
        EstatisticaAtleta.atleta_id == atleta_id
    )
    if competicao:      # só entra no filtro se o valor veio preenchido
        consulta = consulta.filter(EstatisticaAtleta.competicao == competicao)
    if temporada:
        consulta = consulta.filter(EstatisticaAtleta.temporada == temporada)

    return consulta.order_by(EstatisticaAtleta.metrica).all()      # ordem alfabética
    
