# ==========================================================================
# ROTEADOR DO OLHEIRO — completar ficha + favoritar atletas
# ==========================================================================
# Ideias novas desta etapa:
#
# - Upsert (de novo): PUT /olheiro/completar CRIA a linha em "olheiro"
#   se não existe; se já existe, ATUALIZA. Um endpoint, dois caminhos.
#
# - 401 vs 403: 401 = "não fez login"; 403 = "fez login, mas não pode".
#   Aqui: atleta logado não pode favoritar (403) — ele não é olheiro.
#
# - UniqueConstraint como dupla segurança: o BANCO já barre favorito
#   repetido (uq_favorito_olheiro_atleta); nós checamos ANTES para
#   responder 409 com mensagem amigável em vez de estourar 500.
# ==========================================================================
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Atleta, Favorito, Olheiro, TipoUsuario, Usuario
from app.routers.atletas import AtletaBuscaSaida, calcular_idade
from app.schemas import FavoritoSaida, OlheiroCompleta, OlheiroSaida

# Sem prefixo fixo: cada rota declara o caminho inteiro (/olheiro/...,
# /atletas/{id}/favoritar) porque elas "moram" em endereços diferentes
router = APIRouter(tags = ['olheiro'])

# ---------------------------------------------------------------------------
# Helper (função auxiliar) — as rotas de favorito precisam das MESMAS
# checagens; em vez de repetir 3x, guardamos aqui e chamamos com Depends.
# ---------------------------------------------------------------------------
def obter_olheiro_logado(
        usuario: Usuario = Depends(get_current_user),
        db: Session = Depends(get_db),
) -> Olheiro:
    # 1) Tipo errado -> 403 (logado, mas sem permissão de olheiro)
    if usuario.tipo_usuario != TipoUsuario.olheiro:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = 'Só contas do tipo "olheiro" podem favoritar'
        )

    # 2) Tipo certo mas sem ficha ainda -> 403 com dica do próximo passo
    olheiro = (
        db.query(Olheiro)
        .filter(Olheiro.usuario_id == usuario.id)
        .first()
    )
    if olheiro is None:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = 'Complete seu perfil em PUT /olheiro/completar antes de favoritar'
        )
    return olheiro

# ---------------------------------------------------------------------------
# PUT /olheiro/completar — cria OU atualiza a ficha do olheiro (UPSERT)
# ---------------------------------------------------------------------------
@router.put('/olheiro/completar', response_model = OlheiroSaida)
def completar_olheiro(
    dados: OlheiroCompleta,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # 1) Só quem se cadastrou como olheiro pode completar ficha de olheiro
    if usuario.tipo_usuario != TipoUsuario.olheiro:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = 'Esta conta não é do tipo "olheiro"'
        )

    # Já tem ficha? Atualiza | Não tem? Cria o upsert
    olheiro = (
        db.query(Olheiro)
        .filter(Olheiro.usuario_id == usuario.id)
        .first()
    )
    if olheiro is None:
        olheiro = Olheiro(usuario_id = usuario.id)
        db.add(olheiro)

    # ..model_dump() = dict do Pydanttic, None sobrescreve? Então só aplicamos o que veio preenchido
    # assim um PUT partcial não apaga o resto
    if dados.organizacao is not None:
        olheiro.organizacao = dados.organizacao
    if dados.cargo is not None:
        olheiro.cargo = dados.cargo

    db.commit()
    db.refresh(olheiro)     # recarrega a linha com o id gerado pelo banco
    return olheiro

# ---------------------------------------------------------------------------
# GET /olheiro — devolve a ficha do olheiro logado (o form usa pra pré-preencher)
# ---------------------------------------------------------------------------
@router.get('/olheiro', response_model = OlheiroSaida)
def ver_ficha_olheiro(olheiro: Olheiro = Depends(obter_olheiro_logado)):
    # obter_olheiro_logado já faz as 3 checagens: logado? tipo olheiro? tem ficha?
    # Sem ficha = 403 com a dica do PUT (o frontend trata como "form vazio")
    return olheiro

# ---------------------------------------------------------------------------
# POST /atletas/{atleta_id}/favoritar — marcar atleta de interesse
# ---------------------------------------------------------------------------
@router.post('/atletas/{atleta_id}/favoritar', response_model = FavoritoSaida, status_code = status.HTTP_201_CREATED)
def favoritar_atleta(
    atleta_id: int,
    olheiro: Olheiro = Depends(obter_olheiro_logado),
    db: Session = Depends(get_db)
):
    # 1) O atleta existe? (404 = 'não achei esse id')
    atleta = db.query(Atleta).filter(Atleta.id == atleta_id).first()
    if atleta is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = 'Atleta não encontrado'
        )

    # 2) Já favoritou? -> 409 (conflict): pedido contradiz o estado atual
    ja_favoritou = (
        db.query(Favorito)
        .filter(
            Favorito.olheiro_id == olheiro.id,
            Favorito.atleta_id == atleta_id,
        )
        .first()
    )
    if ja_favoritou is not None:
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = 'Este atleta já está nos seus "favoritos"'
        )

    # 3) Grava - o UniqyeConstraint ainda protege por baixo (corrida)
    favorito = Favorito(olheiro_id = olheiro.id, atleta_id = atleta_id)
    db.add(favorito)
    db.commit()
    db.refresh(favorito)
    return favorito


# ---------------------------------------------------------------------------
# DELETE /atletas/{atleta_id}/favoritar — desmarcar
# ---------------------------------------------------------------------------
@router.delete('/atletas/{atleta_id}/favoritar', status_code = status.HTTP_200_OK)
def desfavoritar_atleta(
    atleta_id: int,
    olheiro: Olheiro = Depends(obter_olheiro_logado),
    db: Session = Depends(get_db),
):
    favorito = (
        db.query(Favorito)
        .filter(
            Favorito.olheiro_id == olheiro.id,
            Favorito.atleta_id == atleta_id,
        )
        .first()
    )
    # Desfavoritar algo que não está favoritado = 404 (não existe)
    if favorito is None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = 'Este atleta não está nos seus favoritos'
        )

    db.delete(favorito)
    db.commit()
    return {'mensagem': 'Atleta removido dos favoritos'}


# ---------------------------------------------------------------------------
# GET /meus-favoritos — a lista do olheiro logado
# Reusa o MESMO schema da vitrine (AtletaBuscaSaida): mesmo "cartão",
# o que muda é de QUEM vem a lista (da tabela favorito, não de todos)
# ---------------------------------------------------------------------------
@router.get('/meus-favoritos', response_model = list[AtletaBuscaSaida])
def meus_favoritos(
    olheiro: Olheiro = Depends(obter_olheiro_logado),
    db: Session = Depends(get_db),
):
    # JOIN de TRÊS tabelas: favorito costura olheiro×atleta;
    # atleta costura com usuario (para o nome)
    linhas = (
        db.query(Atleta, Usuario)
        .join(Favorito, Favorito.atleta_id == Atleta.id)
        .join(Usuario, Atleta.usuario_id == Usuario.id)
        .filter(Favorito.olheiro_id == olheiro.id)
        .order_by(Favorito.criado_em)   # mais antigo primeiro
        .all()
    )

    saida = []
    for atleta, usuario in linhas:
        saida.append(
            AtletaBuscaSaida(
                id = atleta.id,
                nome = usuario.nome or 'Atleta',
                esporte = atleta.esporte,
                posicao = atleta.posicao,
                categoria = atleta.categoria,
                cidade = atleta.cidade,
                estado = atleta.estado,
                clube_atual = atleta.clube_atual,
                idade = calcular_idade(atleta.data_nascimento),
            )
        )
    return saida

