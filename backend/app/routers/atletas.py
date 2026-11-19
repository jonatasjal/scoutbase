# ==========================================================================
# ROTEADOR DA VITRINE — busca pública de atletas (sem login!)
# ==========================================================================
# Ideias novas desta etapa:
#
# - JOIN (junção): o NOME está na tabela `usuario` e os dados esportivos na
#   `atleta`. A query precisa COSTURAR as duas tabelas — o ponto de costura é
#   `atleta.usuario_id == usuario.id` (a chave estrangeira que a Fase 0 criou).
#
# - Idade CALCULADA: guardamos data_nascimento (a verdade) e calculamos a
#   idade a cada requisição. Idade envelhece sozinha; se guardássemos "15",
#   em janeiro viraria mentira. É o ditado: guarde a receita, não o bolo.
# ==========================================================================
from datetime import date  # para calcular idade a partir da data

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_          # or_ = "OU" no WHERE (serve achar em qualquer campo)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Atleta, Usuario, Esporte 
from app.schemas import AtletaBuscaSaida, BuscaAtletasSaida

# Todas as rotas daqui começam com /atletas; tag agrupa no Swagger
router = APIRouter(prefix = '/atletas', tags= ['atletas'])

def calcular_idade(data_nascimento: date) -> int:
    '''Idade em anos COMPLETOS a partir da data de nascimento'''
    hoje = date.today()
    idade = hoje.year - data_nascimento.year
    # CUIDADO: se o aniversário ainda não chegou NO ANO CORRENTE, a pessoa ainda não completou a idade então retiramos 1
    if(hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day):
        idade -= 1
    return idade

# GET /atletas - é público e sem token: a vitrine que o olheiro visita
@router.get('', response_model = BuscaAtletasSaida)
def listar_atletas(
    # --- FILTROS: todos OPCIONAIS (None = "não filtrar por isso") ---
    esporte: Esporte | None = None,
    posicao: str | None = None,      # busca "por trecho": "zague" acha "Zagueiro"
    estado: str | None = None,       # 2 letras: SP, RJ...
    categoria: str | None = None,    # sub-17, sub-20...
    busca: str | None = None,        # texto livre: procura em nome, clube OU cidade
    # --- PAGINAÇÃO: com limites via Query (ge = mínimo, le = máximo) ---
    pagina: int = Query(1, ge = 1),                 # página começa no 1
    por_pagina: int = Query(20, ge = 1, le = 100),  # máx 100 por vez (senão...)
    db: Session = Depends(get_db),
):
    # Começa a query BASE (join) e VAI APENDANDO filtros — como um funil
    consulta = (
        db.query(Atleta, Usuario)
        .join(Usuario, Atleta.usuario_id == Usuario.id)
    )

    # Cada "if" = um filtro OPCIONAL: só entra no WHERE se o cliente mandou
    if esporte is not None:
        consulta = consulta.filter(Atleta.esporte == esporte)
    if posicao is not None:
        # ilike = LIKE sem sensível a maiúsculas; %...% = "contém"
        consulta = consulta.filter(Atleta.posicao.ilike(f'%{posicao}%'))
    if estado is not None:
        # .upper(): o cliente pode mandar "sp" → normalizamos para "SP"
        consulta = consulta.filter(Atleta.estado == estado.upper())
    if categoria is not None:
        consulta = consulta.filter(Atleta.categoria.ilike(f'%{categoria}%'))
    if busca is not None and busca.strip() != '':
        termo = f'%{busca.strip()}%'     # % = curinga do LIKE: 'contém o que foi digitado'
        # or_ = OU: vale se achar em qualquer um dos 3 campos
        # ilike = ignora maiúsculas/minusculas (busca "ana" e acha "Ana")
        consulta = consulta.filter(
            or_(
                Usuario.nome.ilike(termo),
                Atleta.clube_atual.ilike(termo),
                Atleta.cidade.ilike(termo)
            )
        )
        # Por que or_? Sem ele, o filtro pediria nome E clube E cidade ao mesmo tempo (ninguém tem tudo igual ao texto).
        # Com OU, digitar "ribeirao" acha quem mora lá; digitar "FC Santos" acha quem é do clube.

    # TOTAL antes do LIMIT: quantos casaram com os filtros (aí o front sabe
    # quantas páginas existem). count() = SELECT COUNT(*) com os MESMOS filtros
    total = consulta.count()

    # PAGINAÇÃO: pular (pagina-1)*por_pagina linhas e trazer só por_pagina
    # Página 1 = pula 0; página 2 = pula 20; página 3 = pula 40...
    linhas = (
        consulta
        .order_by(Atleta.id)
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
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

    # Divisão "com teto" SEM usar math: (total + por_pagina - 1) // por_pagina
    # Ex: 21 atletas / 20 = 2 páginas (a última com 1). Sem o truque, daria 1.
    total_paginas = (total + por_pagina - 1) // por_pagina

    return BuscaAtletasSaida(
        total = total,
        pagina = pagina,
        por_pagina = por_pagina,
        total_paginas = total_paginas,
        resultados = saida,
    )