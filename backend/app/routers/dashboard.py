# ROTEADOR DO DASHBOARD (Fase 7) — a "sala de troféus" da plataforma
# Aqui o banco trabalha duro: agrupa (GROUP BY), soma, tira média (AVG)
# e devolve rankings prontos. Nada de Python lendo linha por linha!

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Atleta, Avaliacao, Mensagem, Olheiro, Usuario, VideoAtleta
from app.schemas import ResumoDashboardSaida, TopAtletaSaida, TopOlheiroSaida

router = APIRouter(prefix = '/dashboard', tags = ['Dashboard'])

# ------------------------------------------------------------------
# 1) RANKING DE ATLETAS
# ------------------------------------------------------------------
# O SQL que o SQLAlchemy monta (entenda a tradução):
#
#   SELECT atleta.id, usuario.nome, atleta.posicao,
#          AVG(avaliacao.nota), COUNT(*)      ← média e contagem POR pilha
#     FROM avaliacao
#     JOIN atleta   ON atleta.id = avaliacao.avaliado_id
#     JOIN usuario  ON usuario.id = atleta.usuario_id
#    WHERE avaliacao.avaliado_tipo = 'atleta'  ← só pilhas de atleta
#    GROUP BY atleta.id                        ← separa em pilhas POR atleta
#   HAVING COUNT(*) >= 1                       ← só pilhas com pelo menos 1 nota
# ORDER BY AVG(avaliacao.nota) DESC            ← maior média primeiro
#      LIMIT :limite                           ← corta no top N
@router.get('/top-atletas', response_model = list[TopAtletaSaida])
def top_atletas(
    limite: int = Query(10, ge = 1, le = 50),   # ?limites = 5 (padrão é 10)
    db: Session = Depends(get_db),
):
    linhas = db.execute(
        select(
            Atleta.id,
            Usuario.nome,
            Atleta.posicao,
            func.avg(Avaliacao.nota),       # mediia da pilha
            func.count(Avaliacao.id),       # tamanho da pilha
        )
        .join(Atleta, Atleta.id == Avaliacao.avaliado_id)
        .join(Usuario, Usuario.id == Atleta.usuario_id)
        .where(Avaliacao.avaliado_tipo == 'atleta')
        .group_by(Atleta.id, Usuario.nome, Atleta.posicao)
        .having(func.count(Avaliacao.id) >= 1)
        .order_by(func.avg(Avaliacao.nota).desc())
        .limit(limite)
    ).all()

    # O banco devolveu só os dados "crus", aqui a gente vira objetos do schema e escreve a posição de rankng(1, 2, 3...) dada a ordem da lista
    return [
        TopAtletaSaida(
            atleta_id = id,
            nome = nome,
            posicao = posicao,
            media_nota = float(media or 0),      # converte-se Decimal -> float(para a exibição)
            total_avaliacoes = total,
            ranking_posicao = indice + 1,        # 1ª linha = 1º lugar
        )
        for indice, (id, nome, posicao, media, total) in enumerate(linhas)
    ]

# ------------------------------------------------------------------
# 2) RANKING DE OLHEIROS (reputação de quem olha)
# ------------------------------------------------------------------
# Mesmíssimo raciocínio, só troca as pilhas: GROUP BY olheiro.id
# (avaliado_tipo = 'olheiro')
@router.get('/ranking-olheiros', response_model = list[TopOlheiroSaida])
def ranking_olheiros(
    limite: int = Query(10, ge = 1, le = 50),
    db: Session = Depends(get_db),
):
    linhas = db.execute(
        select(
            Olheiro.id,
            Usuario.nome,
            Olheiro.organizacao,
            func.avg(Avaliacao.nota),
            func.count(Avaliacao.id),
        )
        .join(Olheiro, Olheiro.id == Avaliacao.avaliado_id)   # olheiro ↔ avaliação
        .join(Usuario, Usuario.id == Olheiro.usuario_id)      # olheiro ↔ usuário
        .where(Avaliacao.avaliado_tipo == 'olheiro')          # só olheiros
        .group_by(Olheiro.id, Usuario.nome, Olheiro.organizacao)
        .having(func.count(Avaliacao.id) >= 1)
        .order_by(func.avg(Avaliacao.nota).desc())
        .limit(limite)
    ).all()

    return [
        TopOlheiroSaida(
            olheiro_id = id,
            nome = nome,
            organizacao = organizacao,
            media_nota = float(media or 0),
            total_avaliacoes = total,
            ranking_posicao = indice + 1,
        )
        for indice, (id, nome, organizacao, media, total) in enumerate(linhas)
    ]

# ------------------------------------------------------------------
# 3) RESUMO GERAL (os números do topo do painel)
# ------------------------------------------------------------------
# Aqui NÃO agrupamos: queremos contagens de tabelas inteiras.
# REGRA DE OURO: só misture tabelas num SELECT se elas tiverem JOIN
# de verdade. Sem JOIN, o SQL faz PRODUTO CARTESIANO: 6 usuarios
# x 2 videos x 5 mensagens = 60 linhas fantasma (bug do "60 usuarios").
# Por isso cada tabela é contada SOZINHA, numa query própria:
# sem join = sem cruzamento = número na mosca.
@router.get('/resumo', response_model = ResumoDashboardSaida)
def resumo(db: Session = Depends(get_db)):
    total_usuarios = db.scalar(select(func.count(Usuario.id))) or 0
    total_atletas = db.scalar(select(func.count(Atleta.id))) or 0
    total_olheiros = db.scalar(select(func.count(Olheiro.id))) or 0
    total_videos = db.scalar(select(func.count(VideoAtleta.id))) or 0
    total_mensagens = db.scalar(select(func.count(Mensagem.id))) or 0
    total_avaliacoes = db.scalar(select(func.count(Avaliacao.id))) or 0

    # Média geral: AVG sem GROUP BY = UM número só (toda a tabela = 1 pilha)
    media_geral = db.scalar(select(func.avg(Avaliacao.nota)))

    return ResumoDashboardSaida(
        total_usuarios = total_usuarios,
        total_atletas = total_atletas,
        total_olheiros = total_olheiros,
        total_avaliacoes = total_avaliacoes,
        media_geral_nota = float(round(media_geral or 0, 2)),
        total_videos = total_videos,
        total_mensagens = total_mensagens,
    )

# ------------------------------------------------------------------
# 4) 404 padronizado (bônus didático)
# ------------------------------------------------------------------
# Não tem rota com ":id" aqui, mas deixo o padrão pronto pro futuro:
# se um dia existir /dashboard/rankings/{temporada}, ele usa este helper.
def exigir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise HTTPException(status_code = 404, detail = mensagem)

'''
- func.avg / func.count = o banco calcula (rápido, dados não viajam pro Python)
- group_by(...) = "separar em pilhas" — tudo que não é agregado precisa estar nele (Atleta.id, Usuario.nome, Atleta.posicao)
- HAVING ≠ WHERE: WHERE filtra linhas (antes de agrupar), HAVING filtra pilhas (depois)
- Query(10, ge=1, le=50) = parâmetro de URL com validação: ?limite=999 → erro 422 automático
'''