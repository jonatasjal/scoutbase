# ==========================================================================
# ROTAS DE PERFIL — o atleta preenche a ficha; depois (2.3) ela é vista
# ==========================================================================
# APIRouter = "sub-servidor" de rotas com prefixo próprio (vimos em auth.py)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Conexão com o banco, models, schemas do perfil e o "guarda de porta"
from app.database import get_db
from app.models import Usuario, Atleta, TipoUsuario, VideoAtleta, EstatisticaAtleta, Visualizacao
from app.schemas import (PerfilAtletaDados, PerfilAtletaSaida, VideoSaida, EstatisticaSaida,
                         VisualizacoesSaida, VisitanteRecente)
from app.deps import get_current_user, get_current_user_optional
from sqlalchemy import func   # COUNT, MAX, DISTINCT das métricas

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
# NOVIDADE Fase 8: visitante OPCIONAL — sem token a rota continua pública;
# com token, sabemos quem visitou (e o dono não conta view própria).
@router.get('/{atleta_id}', response_model = PerfilAtletaSaida)
def ver_perfil(
    atleta_id: int,
    visitante: Usuario | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    # 1) Procura a ficha do atleta no banco
    atleta = db.query(Atleta).filter(Atleta.id == atleta_id).first()

    # 2) Se não achou esse atleta, devolve 404 (não encontrado) (padrão web: a página
    #    que o navegador mostra quando o link está quebrado)
    #    Repare: 404 e não 401 — aqui não é "falta de permissão",
    #    é "este atleta não existe no mundo".
    if atleta is None:
        raise HTTPException(
            status_code = 404,
            detail = 'Atleta não encontrado'
        )

    # 3) REGISTRO DA VISITA — efeito colateral num GET (deliberado aqui):
    #    o produto é "contar quem olhou". REGRA DE OURO do tracking:
    #    se o insert falhar, a busca do perfil NUNCA pode quebrar por isso.
    try:
        # Anti-inflação: dono visitando o próprio perfil NÃO conta view
        if visitante is None or visitante.id != atleta.usuario_id:
            db.add(Visualizacao(
                atleta_id = atleta.id,
                # visitante.id ou None -> None = anônimo (mesmo sem login conta view)
                usuario_visitante_id = visitante.id if visitante else None
            ))
            db.commit()   # grava a visita
    except Exception:
        db.rollback()     # tracking deu erro? libera a sessão e segue a busca

    # 4) Devolve a ficha e o PerfilAtletaSaida garante que SÓ saiam dados públicos (sem email, sem senha, sem token)
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


# ---------------------------------------------------------------------------
# GET /perfil/{atleta_id}/visualizacoes — métricas de quem viu (SÓ o dono)
# ---------------------------------------------------------------------------
# Combina as duas portas que já conhecemos:
#   get_current_user → sem token = 401
#   comparação dono  → token de OUTRA pessoa = 403 (existe, mas não é seu)
@router.get('/{atleta_id}/visualizacoes', response_model = VisualizacoesSaida)
def minhas_visualizacoes(
    atleta_id: int,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1) O atleta existe? (404 ANTES de discussão de permissão — ordem importa)
    atleta = db.query(Atleta).filter(Atleta.id == atleta_id).first()
    if atleta is None:
        raise HTTPException(status_code = 404, detail = 'Atleta não encontrado')

    # 2) Só o DONO vê as métricas do próprio perfil
    if usuario.id != atleta.usuario_id:
        raise HTTPException(status_code = 403, detail = 'Só o próprio atleta vê as métricas do seu perfil')

    # 3) Os contadores — TUDO da mesma tabela visualizacao, então pode ser
    #    em várias queries pequenas sem medo de cross join (o erro da Fase 7!
    #    cross join só assusta quando você mistura tabelas DIFERENTES sem JOIN)
    base = db.query(Visualizacao).filter(Visualizacao.atleta_id == atleta_id)

    total = base.count()                                    # COUNT(*)
    anonimas = base.filter(Visualizacao.usuario_visitante_id.is_(None)).count()
    # DISTINCT: anônimos (NULL) não contam como "visitante único"
    unicos = (
        db.query(func.count(func.distinct(Visualizacao.usuario_visitante_id)))
        .filter(Visualizacao.atleta_id == atleta_id)
        .scalar() or 0                                      # None -> 0
    )
    # MAX(criado_em): a visita mais recente (None = ninguém visitou ainda)
    ultima = (
        db.query(func.max(Visualizacao.criado_em))
        .filter(Visualizacao.atleta_id == atleta_id)
        .scalar()
    )

    # 4) Últimos 10 visitantes — outerjoin no Usuario porque o anônimo
    #    NÃO tem linha de usuário (INNER JOIN descartaria a visita dele!)
    linhas = (
        db.query(Visualizacao, Usuario)
        .outerjoin(Usuario, Usuario.id == Visualizacao.usuario_visitante_id)
        .filter(Visualizacao.atleta_id == atleta_id)
        .order_by(Visualizacao.criado_em.desc())   # mais recente primeiro
        .limit(10)
        .all()
    )
    recentes = [
        VisitanteRecente(
            usuario_id = v.usuario_visitante_id,       # None = anônimo
            nome = u.nome if u else None,              # None = anônimo
            visto_em = v.criado_em,
        )
        for v, u in linhas     # cada linha é a TUPLA (visualizacao, usuario)
    ]

    return VisualizacoesSaida(
        atleta_id = atleta_id,
        total_visitas = total,
        visitantes_unicos = unicos,
        visitas_anonimas = anonimas,
        ultima_visita = ultima,
        visitantes_recentes = recentes,
    )
    
