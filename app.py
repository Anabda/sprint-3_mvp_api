from flask_openapi3 import OpenAPI, Info, Tag
from sqlalchemy.exc import IntegrityError
from flask_cors import CORS
from flask import redirect
import requests

from model import Session, Aparelho
from schemas import *

info = Info(title="Minha API", version="1.0.0")
app = OpenAPI(__name__, info=info)
CORS(app)

# tags
home_tag = Tag(name="Documentação", description="Seleção de documentação: Swagger, Redoc ou RapiDoc")
aparelho_tag = Tag(name="Aparelho", description="Cria, lista e remove aparelhos da base")
integracao_tag = Tag(name="Integrações", description="Serviços de integração com outras APIs")

def verifica_existencia_comodo(nome_comodo):
    """
    Verifica se um cômodo existe na API de cômodos
    """
    # Chamada à API de cômodo para verificar se o cômodo existe
    url = f'http://172.17.0.1:5001/comodo?nome={nome_comodo}'
    response = requests.get(url)
    
    if response.status_code == 200:
        # O cômodo existe
        return True
    else:
        # O cômodo não existe
        return False

@app.get('/', tags=[home_tag])
def home():
    """Redireciona para /openapi, tela que permite a escolha do estilo de documentação.
    """
    return redirect('/openapi')


@app.post('/aparelho', tags=[aparelho_tag],
          responses={"200": AparelhoViewSchema, "409": ErrorSchema, "400": ErrorSchema})
def add_aparelho(form: AparelhoSchema):
    """Adiciona um novo Aparelho à base de dados. Quando preenchido, verifica se o cômodo informado existe na API de cômodos.
    """
    comodo=form.comodo
    if comodo!=None:
        if not verifica_existencia_comodo(comodo):
            error_msg = "O cômodo especificado não existe"
            return {"message": error_msg}, 400

    aparelho = Aparelho(
        codigo=form.codigo, 
        nome=form.nome,
        potencia=form.potencia,
        voltagem=form.voltagem,
        comodo=comodo,
        amperagem=form.amperagem,
        diametro_fio=form.diametro_fio)
    
    try:
        session = Session()
        session.add(aparelho)
        session.commit()
        return apresenta_aparelho(aparelho), 200

    except IntegrityError as e:
        error_msg = "Não foi possível cadastrar o aparelho, pois já existe um aparelho com esse código"
        print("erro: aparelho já cadastrado")
        return {"mesage": error_msg}, 409

    except Exception as e:
        error_msg = "Erro inesperado, o aparelho inserido não foi cadastrado"
        print("erro!")
        return {"mesage": error_msg}, 400


@app.get('/aparelhos', tags=[aparelho_tag],
         responses={"200": ListagemAparelhosSchema, "404": ErrorSchema})
def get_aparelhos():
    """Retorna uma listagem de aparelhos cadastrados na base.
    """
    
    session = Session()
    aparelhos = session.query(Aparelho).all()

    if not aparelhos:
        return {"aparelhos": []}, 200
    return apresenta_aparelhos(aparelhos), 200

@app.get('/aparelho', tags=[aparelho_tag],
            responses={"200": AparelhoViewSchema, "404": ErrorSchema})
def get_aparelho(query: AparelhoBuscaSchema):
    """Encontra um Aparelho a partir do nome informado

    Retorna o aparelho.
    """
    codigo = query.codigo
    session = Session()
    aparelho = session.query(Aparelho).filter(Aparelho.codigo == codigo).first()
    if aparelho:
        return apresenta_aparelho(aparelho), 200
    error_msg = "Aparelho não encontrado"
    return {"mesage": error_msg}, 404

@app.put('/aparelho', tags=[aparelho_tag],
          responses={"200": AparelhoViewSchema, "409": ErrorSchema, "400": ErrorSchema})
def edit_aparelho(query: AparelhoBuscaSchema, form: AparelhoUpdateSchema):
    """Edita um Aparelho existente na base de dados. Quando preenchido, verifica se o cômodo informado existe na API de cômodos.
    """
    codigo=query.codigo
    comodo=form.comodo
    if comodo!=None:
        if not verifica_existencia_comodo(comodo):
            error_msg = "O cômodo especificado não existe"
            return {"message": error_msg}, 400
    session = Session()
    aparelho = session.query(Aparelho).filter(Aparelho.codigo == codigo).first()

    if aparelho is None:
        error_msg = "Não foi possível editar o aparelho, pois não existe um aparelho com esse código"
        return {"message": error_msg}, 409
    
    try:
        aparelho.nome = form.nome
        aparelho.potencia = form.potencia
        aparelho.voltagem = form.voltagem
        aparelho.comodo = comodo
        aparelho.amperagem = form.amperagem
        aparelho.diametro_fio = form.diametro_fio
        session.commit()
        return apresenta_aparelho(aparelho), 200

    except IntegrityError as e:
        error_msg = "Não foi possível editar o aparelho, pois não existe um aparelho com esse código"
        print("erro: aparelho não existente")
        return {"mesage": error_msg}, 409

    except Exception as e:
        error_msg = "Erro inesperado, o aparelho não foi editado"
        print("erro na edição!")
        return {"mesage": error_msg}, 400
    

@app.delete('/aparelho', tags=[aparelho_tag],
            responses={"200": AparelhoDelSchema, "404": ErrorSchema})
def del_aparelho(query: AparelhoBuscaSchema):
    """Deleta um Aparelho a partir do nome informado

    Retorna uma mensagem de confirmação da remoção.
    """
    codigo = query.codigo
    session = Session()
    count = session.query(Aparelho).filter(Aparelho.codigo == codigo).delete()
    session.commit()

    if count:
        return {"mesage": "Aparelho removido", "aparelho": codigo}
    error_msg = "Aparelho não encontrado"
    return {"mesage": error_msg}, 404
    