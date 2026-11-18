# ==========================================================================
# TESTES DE REGRAS DE NEGOCIO — as trancas do sistema:
# - LGPD: vinculo so com MENOR de idade (400 se adulto)
# - Duplicidade: 409 (vinculo e favorito sao unicos)
# - Permissao: 403 (so olheiro favorita, so responsavel vincula)
# - Seguranca: 401 com token forjado em rota OPCIONAL
#   (esse ultimo teste vai REVELAR um bug real escondido no deps.py!)
# ==========================================================================

# Reusa o helper de criar atleta (conta -> login -> ficha) do bloco 13.3
from test_atletas import criar_atleta


# ---------------------------------------------------------------------------
# Helper: conta de RESPONSAVEL logado (tipo 'responsavel')
# ---------------------------------------------------------------------------
def logar_responsavel(client, email = 'mae@teste.com'):
    client.post('/auth/cadastro', json = {
        'nome': 'Mae Teste',
        'email': email,
        'senha': 'senha123',
        'tipo_usuario': 'responsavel',
    })
    login = client.post('/auth/login', json = {
        'email': email,
        'senha': 'senha123',
    })
    return login.json()['access_token']


# ---------------------------------------------------------------------------
# Helper: conta de OLHEIRO + ficha preenchida (obrigatoria: sem ficha da 403)
# ---------------------------------------------------------------------------
def logar_olheiro(client, email = 'olheiro@teste.com'):
    client.post('/auth/cadastro', json = {
        'nome': 'Olheiro Teste',
        'email': email,
        'senha': 'senha123',
        'tipo_usuario': 'olheiro',
    })
    login = client.post('/auth/login', json = {
        'email': email,
        'senha': 'senha123',
    })
    token = login.json()['access_token']

    # PUT /olheiro/completar cria a ficha (upsert: cria ou atualiza)
    client.put(
        '/olheiro/completar',
        json = {'organizacao': 'CT Teste', 'cargo': 'Olheiro'},
        headers = {'Authorization': f'Bearer {token}'},
    )
    return token


# ---------------------------------------------------------------------------
# 1) LGPD feliz: responsavel vincula a MENOR de idade -> 201 Criado
# ---------------------------------------------------------------------------
def test_vinculo_com_menor_201(client):
    ficha = criar_atleta(
        client, 'Ana', 'ana@teste.com', 'Zagueiro', 'Sub-17', 'SP',
        # 2010 = menor de idade hoje
    )
    token = logar_responsavel(client)

    resposta = client.post(
        '/responsaveis',
        json = {'atleta_id': ficha['id'], 'parentesco': 'mae'},
        headers = {'Authorization': f'Bearer {token}'},
    )

    assert resposta.status_code == 201
    assert resposta.json()['parentesco'] == 'mae'
    assert resposta.json()['atleta_id'] == ficha['id']


# ---------------------------------------------------------------------------
# 2) LGPD trancada: ADULTO nao precisa de responsavel -> 400
#    (a idade e calculada NA HORA a partir da data de nascimento)
# ---------------------------------------------------------------------------
def test_vinculo_com_adulto_400(client):
    ficha = criar_atleta(
        client, 'Velho', 'velho@teste.com', 'Atacante', 'Pro', 'SP',
        data_nascimento = '2000-01-01',   # 26 anos = adulto
    )
    token = logar_responsavel(client)

    resposta = client.post(
        '/responsaveis',
        json = {'atleta_id': ficha['id'], 'parentesco': 'pai'},
        headers = {'Authorization': f'Bearer {token}'},
    )

    assert resposta.status_code == 400
    assert resposta.json()['detail'] == 'Vínculo permitido apenas para menores de idade'


# ---------------------------------------------------------------------------
# 3) Duplicidade: mesmo vinculo 2 vezes = 409 Conflito
# ---------------------------------------------------------------------------
def test_vinculo_duplicado_409(client):
    ficha = criar_atleta(
        client, 'Ana', 'ana@teste.com', 'Zagueiro', 'Sub-17', 'SP',
    )
    token = logar_responsavel(client)
    corpo = {'atleta_id': ficha['id'], 'parentesco': 'mae'}

    primeira = client.post(
        '/responsaveis', json = corpo,
        headers = {'Authorization': f'Bearer {token}'},
    )
    segunda = client.post(
        '/responsaveis', json = corpo,
        headers = {'Authorization': f'Bearer {token}'},
    )

    assert primeira.status_code == 201
    assert segunda.status_code == 409
    assert segunda.json()['detail'] == 'Vínculo já existe'


# ---------------------------------------------------------------------------
# 4) Favorito: olheiro marca (201) e remarca (409)
# ---------------------------------------------------------------------------
def test_favoritar_ok_e_duplicado_409(client):
    ficha = criar_atleta(
        client, 'Ana', 'ana@teste.com', 'Zagueiro', 'Sub-17', 'SP',
    )
    token = logar_olheiro(client)

    primeira = client.post(
        f"/atletas/{ficha['id']}/favoritar",
        headers = {'Authorization': f'Bearer {token}'},
    )
    segunda = client.post(
        f"/atletas/{ficha['id']}/favoritar",
        headers = {'Authorization': f'Bearer {token}'},
    )

    assert primeira.status_code == 201
    assert segunda.status_code == 409
    assert segunda.json()['detail'] == 'Este atleta já está nos seus "favoritos"'


# ---------------------------------------------------------------------------
# 5) Permissao: atleta NAO pode favoritar (403) — ele nao e olheiro
# ---------------------------------------------------------------------------
def test_atleta_nao_favorita_403(client):
    ficha = criar_atleta(
        client, 'Ana', 'ana@teste.com', 'Zagueiro', 'Sub-17', 'SP',
    )
    # Mesmo atleta tentando favoritar OUTRO... loga como atleta
    login = client.post('/auth/login', json = {
        'email': 'ana@teste.com', 'senha': 'senha123',
    })
    token = login.json()['access_token']

    resposta = client.post(
        f"/atletas/{ficha['id']}/favoritar",
        headers = {'Authorization': f'Bearer {token}'},
    )

    assert resposta.status_code == 403
    assert resposta.json()['detail'] == 'Só contas do tipo "olheiro" podem favoritar'


# ---------------------------------------------------------------------------
# 6) SEGURANCA: token FORJADO em rota OPCIONAL (GET /perfil/{id} aceita
#    visitante anem com token... mas token invalido tem que dar 401!
#    ROTA OPCIONAL = "sem token tudo bem; COM token ele tem que ser VALIDO".
#
#    ATENCAO: este teste vai FALHAR agora — e isso e PROPOSITAL.
#    O deps.py tem a funcao get_current_user_optional DUPLICADA, e a
#    copia que vale usa 'header=' em vez de 'headers=' -> o Python
#    engasga com TypeError (500) em vez de responder 401.
#    Depois que rodar, a gente conserta o deps.py e este teste fica verde.
# ---------------------------------------------------------------------------
def test_token_invalido_em_rota_opcional_401(client):
    resposta = client.get(
        '/perfil/1',
        # Token inventado: assinatura nao bate com a SECRET_KEY
        headers = {'Authorization': 'Bearer abc.def.ghi'},
    )

    assert resposta.status_code == 401
    assert resposta.json()['detail'] == 'Token inválido ou expirado'