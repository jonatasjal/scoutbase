# =============================================================================
# ROTEADOR DE RESPONSÁVEIS LEGAIS (Fase 5) — o "botão" da regra LGPD
#
# - Na Fase 4.3 o BLOQUEIO já existia (olheiro não fala com menor sem
#   responsável). Faltaba o endpoint pra CRIAR o vínculo sem SQL manual.
#
# - Soft delete: DELETE não apaga a linha — só liga o "interruptor"
#   vinculo_ativo = false. Por quê? Auditoria: se um dia perguntarem
#   "quem autorizou aquela conversa em março?", a linha continua lá.
# =============================================================================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import ResponsavelLegal, TipoUsuario, Atleta
from app.schemas import ResponsavelDados, ResponsavelSaida
from app.routers.atletas import calcular_idade   # mesma função da vitrine (reuso!)

router = APIRouter(prefix = '/responsaveis', tags = ['responsaveis'])

# Guarda de porta: SOMENTE o tipo "responsável" passa (mesma pegadinha do olheiro.py)
def obter_responsavel_logado(usuario = Depends(get_current_user)):
    if usuario.tipo_usuario != TipoUsuario.responsavel:
        raise HTTPException(
            status_code = 403,
            detail = 'Acesso restrito a responsáveis legais',
        )
    return usuario


# --- Criar vínculo -----------------------------------------------------------
@router.post('', response_model = ResponsavelSaida, status_code = 201)
def criar_vinculo(
    dados: ResponsavelDados,
    db: Session = Depends(get_db),
    usuario = Depends(obter_responsavel_logado),
):
    # 1) O atleta existe? (404 se não)
    atleta = db.get(Atleta, dados.atleta_id)
    if atleta is None:
        raise HTTPException(status_code = 404, detail = 'Atleta não encontrado')

    # 2) É MENOR de idade? Regra da LGPD: vínculo de responsável só faz
    #    sentido pra quem ainda é menor — adulto se vira sozinho.
    #    Idade é CALCULADA na hora (não guardamos "idade" no banco, ele envelhece)
    if calcular_idade(atleta.data_nascimento) >= 18:
        raise HTTPException(
            status_code = 400,
            detail = 'Vínculo permitido apenas para menores de idade',
        )

    # 3) Já não tem vínculo ATIVO com esse atleta? (retorna 409 se já tiver)
    # "inativo" não barra, pois a mãe pode se vincular de novo depois de desvincular
    existente = (
        db.query(ResponsavelLegal)
        .filter(
            ResponsavelLegal.usuario_id == usuario.id,          # eu
            ResponsavelLegal.atleta_id == dados.atleta_id,      # com aquele atleta
            ResponsavelLegal.vinculo_ativo == True              # e está ativo
        )
        .first()
    )
    if existente is not None:
        raise HTTPException(status_code = 409, detail = 'Vínculo já existe')

    # 4) Cria e salva
    vinculo = ResponsavelLegal(
        usuario_id = usuario.id,
        atleta_id = dados.atleta_id,
        parentesco = dados.parentesco.strip(),
        vinculo_ativo = True,
    )
    db.add(vinculo)
    db.commit()
    db.refresh(vinculo)
    return vinculo


# --- Meus vínculos (ativos) --------------------------------------------------
@router.get('/meus-vinculos', response_model = list[ResponsavelSaida])
def meus_vinculos(
    db: Session = Depends(get_db),
    usuario = Depends(obter_responsavel_logado)
):
    # Somente os ativo - os desativados, o responsável não precisa ver no dia a dia
    # Mas vão continuar no banco para caso de auditoria
    return (
        db.query(ResponsavelLegal)
        .filter(
            ResponsavelLegal.usuario_id == usuario.id,
            ResponsavelLegal.vinculo_ativo == True,
        )
        .order_by(ResponsavelLegal.id)
        .all()
    )


# --- Desvincular (soft delete) -----------------------------------------------
@router.delete('/{vinculo_id}', response_model = ResponsavelSaida)
def desvincular(
    vinculo_id: int,
    db: Session = Depends(get_db),
    usuario = Depends(obter_responsavel_logado),
):
    vinculo = db.get(ResponsavelLegal, vinculo_id)
    if vinculo is None:
        raise HTTPException(status_code = 404, detail = 'Vínculo não encontrado')

    # Só o DONO do vínculo pode desvincular (se não, qualquer responsável
    # desligaria o vínculo dos outros — bagunça)
    if vinculo.usuario_id != usuario.id:
        raise HTTPException(status_code = 403, detail = 'Este vínculo não é seu')

    vinculo.vinculo_ativo = False   # interruptor, não apagão
    db.commit()
    db.refresh(vinculo)
    return vinculo
