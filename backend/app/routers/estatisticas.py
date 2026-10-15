# ==========================================================================
# ROTAS DE ESTATÍSTICAS — o atleta lança seus números
# ==========================================================================
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario, Atleta, TipoUsuario, EstatisticaAtleta
from app.schemas import EstatisticaDados, EstatisticaSaida
from app.deps import get_current_user

router = APIRouter(prefix = '/estatisticas', tags = ['estatisticas'])

# É tipo um "guarda": somente atleta COM FICHA pode lançar número (rreaproveitamos a mesma regra
# do upload de vídeo = "complete o perfil antes")
def _pegar_ficha_do_atleta(usuario: Usuario, db: Session) -> Atleta:
    if usuario.tipo_usuario != TipoUsuario.atleta:
        raise HTTPException(status_code = 403, detail = 'Somente atletas lançam estatísticas')
    atleta = db.query(Atleta).filter(Atleta.usuario_id == usuario.id).first()
    if atleta is None:
        raise HTTPException(status_code = 403, detail = 'Complete seu perfil antes de lançar estatísticas')
    return atleta

@router.post('', response_model = EstatisticaSaida, status_code = 201)
def registrar_estatistica(
    dados: EstatisticaDados,
    usuario: Usuario = Depends(get_current_user),       # sem token = 401
    db: Session = Depends(get_db)
):
    # 1) Porteira: é atleta e em ficha?
    atleta = _pegar_ficha_do_atleta(usuario, db)

    # 2) Upsert - essa métrica já existe para esse atleta/competição/temporada?
    # (mesma combinação de chaves = mesma "linha de placar")
    estatistica = (
        db.query(EstatisticaAtleta)
        .filter(
            EstatisticaAtleta.atleta_id == atleta.id,
            EstatisticaAtleta.competicao == dados.competicao,
            EstatisticaAtleta.temporada == dados.temporada,
            EstatisticaAtleta.metrica == dados.metrica.lower()
        )
        .first()
    )

    if estatistica is None:
        # 2a) Primeira vez → cria a linha nova
        estatistica = EstatisticaAtleta(
            atleta_id = atleta.id,
            competicao = dados.competicao,
            temporada = dados.temporada,
            metrica = dados.metrica.lower(),
            valor = dados.valor
        )
        db.add(estatistica)
    else:
        # 2b) Já existe → atualiza SÓ o valor (a linha continua a mesma)
        estatistica.valor = dados.valor

    db.commit()
    db.refresh(estatistica)
    return estatistica      # 201 nos dois casos

