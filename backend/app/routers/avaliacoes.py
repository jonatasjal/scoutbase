# =============================================================================
# ROTEADOR DE AVALIAÇÕES (Fase 6) — nota 0-10 nos dois sentidos
#
# - O bidirecional é resolvido SEM corpo extra: o tipo de quem LOGA decide
#   a direção. Olheiro só avalia atleta; atleta só avalia olheiro.
# - Upsert: existe nota do par? atualiza. Não? cria. (UniqueConstraint ajuda)
# =============================================================================
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Avaliacao, Atleta, Olheiro, TipoUsuario, Usuario
from app.schemas import AvaliacaoDados, AvaliacaoSaida, AvaliacaoResumo

router = APIRouter(prefix = '/avaliacoes', tags = ['avaliacoes'])


# --- Dar (ou atualizar) uma nota ---------------------------------------------
@router.post('', response_model = AvaliacaoSaida)
def avaliar(
    dados: AvaliacaoDados,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    # 1) O tipo de quem loga define a direção da seta
    if usuario.tipo_usuario == TipoUsuario.olheiro:
        avaliado_tipo = 'atleta'
        existe = db.get(Atleta, dados.avaliado_id)
    elif usuario.tipo_usuario == TipoUsuario.atleta:
        avaliado_tipo = 'olheiro'
        existe = db.get(Olheiro, dados.avaliado_id)
        # cuidado: é o id da tabela OLHEIRO, não do usuario!
    else:
        raise HTTPException(status_code = 403, detail = 'Só olheiros e atletas avaliam')

    # 2) Existe mesmo? (404 — inclui olheiro sem ficha, que não tem linha)
    if existe is None:
        raise HTTPException(status_code = 404, detail = 'Avaliado não encontrado')

    # 3) Upsert: já dei nota pra esse par? atualiza. senão cria.
    avaliacao = (
        db.query(Avaliacao)
        .filter(
            Avaliacao.avaliador_id == usuario.id,
            Avaliacao.avaliado_tipo == avaliado_tipo,
            Avaliacao.avaliado_id == dados.avaliado_id,
        )
        .first()
    )
    if avaliacao is None:
        avaliacao = Avaliacao(avaliador_id = usuario.id,
                              avaliado_tipo = avaliado_tipo,
                              avaliado_id = dados.avaliado_id)
        db.add(avaliacao)

    avaliacao.nota = Decimal(str(dados.nota))     # float do JSON → Decimal do banco
    avaliacao.comentario = dados.comentario.strip() if dados.comentario else None
    db.commit()
    db.refresh(avaliacao)
    return avaliacao


# --- Resumo de um avaliado (média + comentários) ------------------------------
@router.get('/{avaliado_tipo}/{avaliado_id}', response_model = AvaliacaoResumo)
def resumo(
    avaliado_tipo: str,
    avaliado_id: int,
    db: Session = Depends(get_db),
):
    if avaliado_tipo not in ('atleta', 'olheiro'):
        raise HTTPException(status_code = 404, detail = 'Tipo inválido (use atleta ou olheiro)')

    linhas = (
        db.query(Avaliacao)
        .filter(Avaliacao.avaliado_tipo == avaliado_tipo,
                Avaliacao.avaliado_id == avaliado_id)
        .order_by(Avaliacao.criado_em.desc())
        .all()
    )
    if not linhas:
        raise HTTPException(status_code = 404, detail = 'Ninguém avaliou isso ainda')

    media = sum(float(a.nota) for a in linhas) / len(linhas)
    return AvaliacaoResumo(
        avaliado_tipo = avaliado_tipo,
        avaliado_id = avaliado_id,
        total_avaliacoes = len(linhas),
        media_nota = round(media, 1),
        comentarios = [a.comentario for a in linhas if a.comentario],
    )


# --- O que eu avaliei ---------------------------------------------------------
@router.get('/minhas', response_model = list[AvaliacaoSaida])
def minhas_avaliacoes(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return (
        db.query(Avaliacao)
        .filter(Avaliacao.avaliador_id == usuario.id)
        .order_by(Avaliacao.id)
        .all()
    )


'''
⚠️ pegadinha de rota: /minhas precisa estar antes de /{avaliado_tipo}/{avaliado_id} senão o FastAPI lê "minhas" como um tipo. 
Está na ordem certa no bloco acima — mas se você digitar invertido, o teste 8 quebra.
'''