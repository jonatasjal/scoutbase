# =============================================================================
# ROTEADOR DE MENSAGENS (Fase 4) — chat entre 2 usuários
#
# - Auto-relação: a tabela "mensagem" aponta 2x pra ela mesma (remetente e
#   destinatário são os DOIS a tabela "usuario" — não a própria mensagem).
#   O que parece complicado é só: cada linha é "fulano disse X pra ciclano".
#
# - Regra de ouro da conversa: qualquer um pode ENVIAR, mas só o DESTINATÁRIO
#   pode marcar como lida. E quem pede a conversa só vê as mensagens
#   em que PARTICIPOU (senão dava pra ler a conversa dos outros).
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Mensagem, Usuario
from app.schemas import MensagemEnvia, MensagemSaida, LidasSaida

router = APIRouter(prefix = '/mensagens', tags = ['mensagens'])
# prefix = /mensagens -> todas as rotas já naem com /mensagens na frente
# GET /mensagens/conversa/5 (em vez de /conversa/5 solto no ar)

# --- Enviar mensagem --------------------------------------------------------
@router.post('', response_model= MensagemSaida, status_code= 201)
def enviar_mensagem(
    dados: MensagemEnvia,
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user),
):
    # 1) Existe quem vai receber? (404 se não existir)
    destinatario = db.get(Usuario, dados.destinatario_id)
    if destinatario is None:
        raise HTTPException(status_code=404, detail= 'Destinatário não encontrado')

    # 2) Não deixa mandar mensagem em branco
    conteudo = dados.conteudo.strip()
    if not conteudo:
        raise HTTPException(status_code=422, detail= 'Mensagem não pode ser vazia')

    # 3) Cria e salva
    mensagem = Mensagem(
        remetente_id = usuario.id,
        destinatario_id = dados.destinatario_id,
        conteudo = conteudo,
    )
    db.add(mensagem)
    db.commit()
    db.refresh(mensagem)  # devolve o id e a data que o banco gerou

    return MensagemSaida(
        id = mensagem.id,
        remetente_id = mensagem.remetente_id,
        destinatario_id = mensagem.destinatario_id,
        remetente_nome = usuario.nome,  # quem enviou = o logado (nunca erra)
        conteudo = mensagem.conteudo,
        lida = mensagem.lida,
        criado_em = mensagem.criado_em,
    )
    
# --- Histórico da conversa ---------------------------------------------------
@router.get('/conversa/{outro_id}', response_model= list[MensagemSaida])
def conversa(
    outro_id: int,
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user),
):
    # WHERE (eu > você) OU (você > eu) - as duas metades da conversa
    linhas = (
        db.query(Mensagem)
        .filter(
            (Mensagem.remetente_id == usuario.id) & (Mensagem.destinatario_id == outro_id)
            |
            (Mensagem.remetente_id == outro_id) & (Mensagem.destinatario_id == usuario.id)
        )
        .order_by(Mensagem.criado_em)       # cronológica: mais antiga em cima
        .all()
    )

    # Precisamos do NOME de cada remetente -> busca só quem apareceu
    # (dicionário {id: nome} para não azer query dentro do loop)
    nomes = {
        u.id: u.nome
        for u in db.query(Usuario).filter(Usuario.id.in_({
            m.remetente_id for m in linhas
        })).all()
    }

    return [
        MensagemSaida(
            id= m.id,
            remetente_id= m.remetente_id,
            destinatario_id= m.destinatario_id,
            remetente_nome= nomes.get(m.remetente_id),
            conteudo= m.conteudo,
            lida= m.lida,
            criado_em= m.criado_em,
        )
        for m in linhas
    ]

# --- Marcar como lidas -------------------------------------------------------
@router.put('/lidas/{outro_id}', response_model= LidasSaida)
def marcar_lidas(
    outro_id: int,
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user),
):
    # Só marca as mensagens RECEBIDAS (destinatário = eu) e ainda NÃO lidas.
    # Nunca marca as que EU mandei — quem decide se leu é quem RECEBE.
    quantidade = (
        db.query(Mensagem)
        .filter(
            Mensagem.remetente_id == outro_id,      # vieram do outro
            Mensagem.destinatario_id == usuario.id, # e são pra mim
            Mensagem.lida == False,                 # e ainda não li
        )
        .update({"lida": True}, synchronize_session=False)
        # .update() = UPDATE direto no banco, em massa (1 comando SQL,
        # igual o upsert da Fase 2 — não é preciso buscar e salvar 1 a 1)
    )
    db.commit()
    return LidasSaida(mensagens_marcadas=quantidade)


# --- Quantas mensagens não lidas? --------------------------------------------
@router.get('/nao-lidas')
def contar_nao_lidas(
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user),
):
    # COUNT(*) = "conte as linhas" — o banco devolve só UM número,
    # não a lista inteira (mais leve e mais rápido)
    total = (
        db.query(Mensagem)
        .filter(
            Mensagem.destinatario_id == usuario.id,  # são pra mim
            Mensagem.lida == False,                   # e ainda não abri
        )
        .count()
    )
    return {"nao_lidas": total}

'''
Duas coisas novas pra reparar:
1. & e | com parênteses — SQL em Python não usa AND/OR como texto; usa & (E) e | (OU). Os parênteses são obrigatórios porque 
sem eles a precedência inverte o resultado (mesma regra de matemática: × antes de +).
2. .in_({...}) — "traga só os usuários cujo id está NESTE conjunto". O {...} é um set (conjunto, sem repetição) montado 
com set comprehension: {m.remetente_id for m in linhas}. Isso evita N queries — uma só.
'''