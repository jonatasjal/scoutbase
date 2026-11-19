# ==========================================================================
# TESTES DA VITRINE — busca publica de atletas (sem login) + perfil publico
#
# A vitrine e o coracao do produto: e ELA que o olheiro abre. Aqui
# garantimos: listar, filtrar, calcular idade e NUNCA vazar email/senha.
# ==========================================================================


# ---------------------------------------------------------------------------
# Helper: monta um atleta COMPLETO em 3 passos (conta -> login -> ficha).
# Por que 3? Por que a ficha (PUT /perfil/completar) exige token de um
# usuario do tipo 'atleta' — entao antes tem que existir a conta e o login.
# Devolve o JSON da ficha (que traz o 'id' do atleta).
# ---------------------------------------------------------------------------
def criar_atleta(client, nome, email, posicao, categoria, estado,
                 cidade = 'Ribeirao Preto', data_nascimento = '2010-05-10',
                 clube = None):
    # Passo 1: cria a conta (201)
    client.post('/auth/cadastro', json = {
        'nome': nome,
        'email': email,
        'senha': 'senha123',
        'tipo_usuario': 'atleta',
    })

    # Passo 2: loga e guarda o cracha JWT
    login = client.post('/auth/login', json = {
        'email': email,
        'senha': 'senha123',
    })
    token = login.json()['access_token']

    # Passo 3: completa a ficha (PUT idempotente: 1a vez cria, 2a atualiza)
    resposta = client.put(
        '/perfil/completar',
        json = {
            'data_nascimento': data_nascimento,  # guardamos a DATA, nao a idade
            'posicao': posicao,
            'categoria': categoria,
            'cidade': cidade,
            'estado': estado,
            'clube_atual': clube
        },
        # Mesmo formato do frontend: 'Bearer <cracha>' (com ESPACO)
        headers = {'Authorization': f'Bearer {token}'},
    )
    return resposta.json()   # tem o 'id' da ficha de atleta


# ---------------------------------------------------------------------------
# 1) Vitrine vazia: 200 e lista vazia (nao pode dar erro sem dados)
# ---------------------------------------------------------------------------
def test_vitrine_vazia(client):
    resposta = client.get('/atletas')   # public: sem header nenhum

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados['total'] == 0
    assert dados['resultados'] == []
    assert dados['total_paginas'] == 0


# ---------------------------------------------------------------------------
# 2) Vitrine com 1 atleta: acha, calcula a idade e NAO vaza dados privados
# ---------------------------------------------------------------------------
def test_vitrine_lista_atleta(client):
    criar_atleta(
        client, nome = 'Ana Teste', email = 'ana@teste.com',
        posicao = 'Zagueiro', categoria = 'Sub-17', estado = 'SP',
    )

    resposta = client.get('/atletas')
    dados = resposta.json()

    assert dados['total'] == 1
    atleta = dados['resultados'][0]
    assert atleta['nome'] == 'Ana Teste'
    assert atleta['posicao'] == 'Zagueiro'

    # Idade e CALCULADA a cada busca (nunca guardada) — so precisa ser numero.
    # Nao fixamos o valor: se fixassemos 16, o teste quebraria todo ano!
    assert isinstance(atleta['idade'], int)

    # Privacidade: o cartao da vitrine nao pode conter email nem hash
    assert 'email' not in atleta
    assert 'senha_hash' not in atleta


# ---------------------------------------------------------------------------
# 3) Filtro por posicao: 'zague' (minusc., trecho) acha 'Zagueiro'
#    (ilike = sem sensivel a maiusculas + contem, tipo busca do Google)
# ---------------------------------------------------------------------------
def test_filtro_posicao(client):
    criar_atleta(client, 'Ana', 'ana@teste.com', 'Zagueiro', 'Sub-17', 'SP')
    criar_atleta(client, 'Bruno', 'bruno@teste.com', 'Atacante', 'Sub-20', 'RJ')

    # So o zagueiro deve voltar
    resposta = client.get('/atletas', params = {'posicao': 'zague'})
    dados = resposta.json()

    assert dados['total'] == 1
    assert dados['resultados'][0]['posicao'] == 'Zagueiro'
    assert dados['resultados'][0]['nome'] == 'Ana'


# ---------------------------------------------------------------------------
# 4) Filtro por estado: mandar 'sp' minusculo acha 'SP' — o endpoint
#    faz .upper() antes de filtrar (normalizacao na entrada)
# ---------------------------------------------------------------------------
def test_filtro_estado_minusculo(client):
    criar_atleta(client, 'Ana', 'ana@teste.com', 'Zagueiro', 'Sub-17', 'SP')
    criar_atleta(client, 'Bruno', 'bruno@teste.com', 'Atacante', 'Sub-20', 'RJ')

    resposta = client.get('/atletas', params = {'estado': 'sp'})  # minusculo!
    dados = resposta.json()

    assert dados['total'] == 1
    assert dados['resultados'][0]['estado'] == 'SP'


# ---------------------------------------------------------------------------
# 5) Perfil PUBLICO (sem token) devolve a ficha — mas SEM email/senha
#    (o response_model = escudo: so deixa passar os campos declarados)
# ---------------------------------------------------------------------------
def test_perfil_publico_sem_vazamento(client):
    ficha = criar_atleta(
        client, nome = 'Ana Teste', email = 'ana@teste.com',
        posicao = 'Zagueiro', categoria = 'Sub-17', estado = 'SP',
    )

    resposta = client.get(f"/perfil/{ficha['id']}")   # sem header!

    assert resposta.status_code == 200
    dados = resposta.json()
    assert dados['posicao'] == 'Zagueiro'
    # SEGURANCA: nem o email da conta pode aparecer no perfil publico
    assert 'email' not in dados
    assert 'senha_hash' not in dados


# ---------------------------------------------------------------------------
# 6) Idade inexistente = 404 (e NAO 401 — nao e falta de cracha,
#    e "esse id nao existe no mundo")
# ---------------------------------------------------------------------------
def test_perfil_inexistente_404(client):
    resposta = client.get('/perfil/999')

    assert resposta.status_code == 404
    assert resposta.json()['detail'] == 'Atleta não encontrado'


# ==========================================================================
# BUSCA AVANÇADA — texto livre combinando com os filtros
# ==========================================================================
def test_busca_texto_no_nome(client):
    criar_atleta(client, 'Ana Teste', 'ana@teste.com', 'Zagueiro', 'Sub-17', 'SP')
    criar_atleta(client, 'Bruno Silva', 'bruno@teste.com', 'Atacante', 'Sub-20', 'RJ')

    # 'ana' MINUSCULO acha 'Ana Teste' - ilie ignora maiúscula/minúscula
    resposta = client.get('/atletas', params = {'busca': 'ana'})
    dados = resposta.json()

    assert dados['total'] == 1
    assert dados['resultados'][0]['nome'] == 'Ana Teste'

def test_busca_texto_na_cidade(client):
    # a cidade padrão do helper é 'Ribeirao Preto'
    criar_atleta(client, 'Ana', 'ana@teste.com', 'Zagueiro', 'Sub-17', 'SP')

    resposta = client.get('/atletas', params = {'busca': 'ribeirao'})

    assert resposta.json()['total'] == 1


def test_busca_texto_no_clube(client):
    criar_atleta(
        client, 'Ana', 'ana@teste.com', 'Zagueiro', 'Sub-17', 'SP',
        clube = 'FC Exemplo',
    )

    resposta = client.get('/atletas', params = {'busca': 'exemplo'})

    assert resposta.json()['total'] == 1


def test_busca_combinada_com_estado(client):
    # 'teste' sozinho achava OS DOIS nomes; + estado 'sp' sobra só Ana
    criar_atleta(client, 'Ana Teste', 'ana@teste.com', 'Zagueiro', 'Sub-17', 'SP')
    criar_atleta(client, 'Bruno Teste', 'bruno@teste.com', 'Atacante', 'Sub-20', 'RJ')

    resposta = client.get(
        '/atletas', params = {'busca': 'teste', 'estado': 'sp'},
    )
    dados = resposta.json()

    assert dados['total'] == 1
    assert dados['resultados'][0]['nome'] == 'Ana Teste'


def test_busca_vazia_ignorada(client):
    # espaço em branco = "não buscou nada" -> devolve a lista inteira
    criar_atleta(client, 'Ana', 'ana@teste.com', 'Zagueiro', 'Sub-17', 'SP')

    resposta = client.get('/atletas', params = {'busca': '   '})

    assert resposta.json()['total'] == 1


