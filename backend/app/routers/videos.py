# ==========================================================================
# ROTAS DE VÍDEO — upload do "currículo visual" do atleta
# ==========================================================================
# Aqui o mundo é diferente das outras rotas: NÃO é JSON que chega, é um
# ARQUIVO binário no formato multipart/form-data (o mesmo de um <form> de
# HTML com botão "escolher arquivo"). Por isso importamos UploadFile/File/Form
import os
import uuid  # gerador de nomes únicos (ex: a3f9c2...) — vira mais

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario, Atleta, TipoUsuario, VideoAtleta, TipoOrigemVideo
from app.schemas import VideoSaida
from app.deps import get_current_user

router = APIRouter(prefix = '/videos', tags = ['videos'])

# Lugar onde os arquivos vão parar no disco (backend/media/uploads/)
#dirname x3 = sobe de routers/ -> app/ -> backend/
PASTA_UPLOADS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'media', 'uploads'
) 

# Regras para aceitação (validação de segurança BÁSICA)
EXTENSOES_PERMITIDAS = {'.mp4', '.mov', '.webm'}        # set = conjunto de válidos
TAMANHO_MAXIMO = 100 * 1024 * 1024                      # 100mb (em bytes)

@router.post('/upload', response_model = VideoSaida, status_code = 201)
def upload_video(
    arquivo: UploadFile = File(..., description = 'Arquivo de vídeo do atleta'),
    titulo: str = Form(..., description = 'Título do vídeo'),
    usuario: Usuario = Depends(get_current_user),    # sem token = 401
    db: Session = Depends(get_db)
):
    # 1) Somente atleta COM FICHA pode enviar vídeo (olheiro ou sem perfil = 403)
    if usuario.tipo_usuario != TipoUsuario.atleta:
        raise HTTPException(status_code = 403, detail = 'Somente atletas enviam videos')

    atleta = db.query(Atleta).filter(Atleta.usuario_id == usuario.id).first()
    if atleta is None:
        raise HTTPException(status_code = 403, detail = 'Complete seu perfil antes de enviar video')

    # 2) Qual a extensão do arquivo? (mp4, txt...)
    # Vamos confiar somente no sufixo e nunca no nome inteiro que veio da internet
    extensao = os.path.splitext(arquivo.filename or '')[1].lower()

    if extensao not in EXTENSOES_PERMITIDAS:
        raise HTTPException(
            status_code = 400,
            detail = f'Formato nao permitido: {extensao}. Aceitos: .mp4, .mov, .webm'
        )

    # 3) Garante que a asta de destino exista, caso não exista ela é criada
    os.makedirs(PASTA_UPLOADS, exist_ok = True)

    # 4) Nome seguro no servior: uuid (hex aleatório) + nossa extensão
    # E por que não nome original? Porque o usuário pode mandar "../../../senha.txt" para escapar da pasta (ataque "path traversal").
    # COm o uuid, o nome sai do teclado dele e vira algo como: "9f2b...c1.mp4"
    nome_salvo = f'{uuid.uuid4().hex}{extensao}'
    caminho_completo =  os.path.join(PASTA_UPLOADS, nome_salvo)

    # 5) Copia o arquivo pro disco EM BLOCOS de 1mb
    # Por que não o arquivo.head() de uma vez?" Um vídeo de 100mb dentro da RAM mata o servidor. 
    # Em blocos a mmemória sempre fica em ~1mb e já vamos contando os bytes (tamanho_byts da tabela)
    tamanho = 0
    try:
        with open(caminho_completo, 'wb') as destino:
            while True:
                bloco = arquivo.file.read(1024 * 1024)
                if not bloco:
                    break
                tamanho += len(bloco)
                if tamanho > TAMANHO_MAXIMO:
                    # Esturou o limite e lança o ERRO
                    raise HTTPException(status_code = 413, detail = 'Arquivo maior que 100 MB')
                destino.write(bloco)
    except HTTPException:
        # Apaga o arquivo pela metade antes de morrer (não deixando lixo)
        if os.path.exists(caminho_completo):
            os.remove(caminho_completo)
        raise       # re-lança 0 413 pro cliente

    # 6) Tudo certo? Então grava-se a linha no banco (o arquivo está no disco)
    # o banco só guarda o endereço dele, ou seja, o banco não segura binário
    video = VideoAtleta(
        atleta_id = atleta.id,
        tipo_origem = TipoOrigemVideo.arquivo_upload,
        url_ou_caminho= f'/media/uploads/{nome_salvo}',     # caminho público futuro
        titulo = titulo,
        tamanho_bytes = tamanho
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video        # 201 com a ficha do víde recém-criado



    
    