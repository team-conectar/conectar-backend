from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import typing as t
from datetime import datetime

from app.db import models
from app.db.notificacao import schemas
from app.db.pessoa_projeto.crud import get_pessoa_projeto
from app.db.pessoa.crud import get_pessoa
from app.db.projeto.crud import get_projeto

def get_notificacao_by_id(db: Session, notificacao_id: int):
    notificacao = db.query(models.Notificacao)\
                    .filter(models.Notificacao.id == notificacao_id)\
                    .first()

    if not notificacao:
        raise HTTPException(status_code=404, detail="notificacao não encontrada")
    return notificacao


def get_notificacao_by_destinatario(db: Session, destinatario_id: int):
    
    notificacao = db.query(models.Notificacao)\
                    .filter(models.Notificacao.destinatario_id == destinatario_id)\
                    .all()

    if not notificacao:
        raise HTTPException(status_code=404, detail="notificacao não encontrada")
    return notificacao


"""
CRIADA = Vaga criada sem enviar convites
notificação referente -> Não cria notificação
(Botão "Buscar time")
PENDENTE_IDEALIZADOR = Time encontrado mas não confirmado envio por parte do idealizador
notificacao referente -> 
    remetente_id: current_pessoa_id
    destinatario_id: current_pessoa_id
    projeto_id: X
    pessoa_projeto_id: l[Y]
    situacao: "Finalize o cadastro do projeto 'X.name' e encontre o time ideal"

(Botão "Enviar Convites")
PENDENTE_COLABORADOR = Colaborador não aceitou/recusou convite ainda
    se (Data de hoje.day == pessoa_projeto.data_atualização.day)
    notificacao referente -> 
        remetente_id: current_pessoa_id
        destinatario_id: pessoa_projeto.pessoa_id
        projeto_id: X
        pessoa_projeto_id: Y
        situacao: "remetente.name te fez um convite para o projeto X.name"

CRON
    se (Data de hoje - pessoa_projeto.data_atualização >=1 e < 5)
        notificacao referente -> 
        remetente_id: current_pessoa_id
        destinatario_id: pessoa_projeto.pessoa_id
        projeto_id: X
        pessoa_projeto_id: Y
        situacao: "Você tem 'Data de hoje - pessoa_projeto.data_atualização' dias para
        responder ao convite de remetente.name para o projeto X.name"

    se (Data de hoje - pessoa_projeto.data_atualização > 5)
        notificacao referente -> 
        remetente_id: current_pessoa_id
        destinatario_id: pessoa_projeto.pessoa_id
        projeto_id: X
        pessoa_projeto_id: Y
        situacao: "O prazo de resposta de destinatario.name expirou"


(Botão "Recusar")
RECUSADO = Colaborador recusou o convite
notificacao referente -> 
    remetente_id: current_pessoa_id
    destinatario_id: projeto.pessoa_id
    projeto_id: X
    pessoa_projeto_id: Y
    situacao: "remetente.name recusou seu convite para o projeto X.name"

(Botão "Aceitar")
ACEITO = Colaborador aceitou convite
notificacao referente -> 
    remetente_id: current_pessoa_id
    destinatario_id: projeto.pessoa_id
    projeto_id: X
    pessoa_projeto_id: Y
    situacao: "remetente.name aceitou seu convite para o projeto "X.name, finalize o acordo"

FINALIZADA = Idealizador finalizou as vagas
notificação referente -> Não cria notificação

"""

def create_notificacao_vaga(db: Session,
                        remetente_id: int,
                        pessoa_projeto_id: int):
    
    hoje = datetime.today()

    pessoa_projeto = get_pessoa_projeto(db, pessoa_projeto_id)
    projeto_id = pessoa_projeto.projeto_id
    projeto = get_projeto(db, projeto_id)
    pessoa = get_pessoa(db, remetente_id)

    if pessoa_projeto.situacao == "PENDENTE_IDEALIZADOR": 
        situacao = "Finalize o cadastro do projeto " + projeto.nome + " e encontre o time ideal"
        destinatario_id = remetente_id

    elif pessoa_projeto.situacao == "RECUSADO":
        situacao = pessoa.nome + " recusou seu convite para o projeto " + projeto.nome + ". Realize uma nova busca"
        destinatario_id = projeto.pessoa_id

    elif pessoa_projeto.situacao == "ACEITO":
        situacao = pessoa.nome + " aceitou seu convite para o projeto " + projeto.nome + ". Finalize o acordo e preencha essa vaga!"
        destinatario_id = projeto.pessoa_id

    elif pessoa_projeto.situacao == "PENDENTE_COLABORADOR":
        if(hoje.day == pessoa_projeto.data_atualizacao.day):
            situacao = pessoa.nome + " te fez um convite para o projeto " + projeto.nome + ". Confira!"
            destinatario_id = pessoa_projeto.pessoa_id


    db_notificacao = models.Notificacao(
        remetente_id = remetente_id,
        destinatario_id = destinatario_id,
        projeto_id = projeto_id,
        pessoa_projeto_id = pessoa_projeto_id,
        situacao = situacao,
        lido = False,
    )
    
    
    db.add(db_notificacao)
    db.commit()
    db.refresh(db_notificacao)
    return db_notificacao


def check_notificacao_vaga(db: Session):

    hoje = datetime.today()

    vagas = db.query(models.PessoaProjeto)\
            .filter(models.PessoaProjeto.situacao == "PENDENTE_COLABORADOR" 
            and hoje.day != models.PessoaProjeto.data_atualizacao.day)\
            .all()

    notificacao = []


    for vaga in vagas:
        projeto = get_projeto(db, vaga.projeto_id)
        att_str = datetime.strftime(vaga.data_atualizacao, "%Y-%m-%d")
        att = datetime.strptime(att_str, "%Y-%m-%d")

        diff = hoje - att
        
        if(diff.days < 6):
            remetente = get_pessoa(db, projeto.pessoa_id)
            situacao = "Você tem " + str(6-diff.days) + " dias para responder ao convite de " + remetente.nome + " para o projeto " + projeto.nome,
            destinatario_id = vaga.pessoa_id

        elif(diff.days == 6):
            remetente = get_pessoa(db, vaga.pessoa_id)
            situacao = "O prazo de resposta de " + remetente.nome + " expirou! Faça uma nova busca."
            destinatario_id = projeto.pessoa_id,
        
        db_notificacao = models.Notificacao(
                remetente_id = remetente.id,
                destinatario_id = destinatario_id,
                projeto_id = vaga.projeto_id,
                pessoa_projeto_id = vaga.id,
                situacao = situacao,
                lido = False,
                )

        db.add(db_notificacao)
        db.commit()
        db.refresh(db_notificacao)

        notificacao.append(db_notificacao)
    
    return notificacao

def edit_notificacao(
    db: Session, notificacao_id, notificacao: schemas.NotificacaoEdit
) -> schemas.Notificacao:
    
    db_notificacao = get_notificacao_by_id(db, notificacao_id)
    if not db_notificacao:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="notificacao não encontrada",
        )
    update_data = notificacao.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_notificacao, key, value)

    db.add(db_notificacao)
    db.commit()
    db.refresh(db_notificacao)
    return db_notificacao


def delete_notificacao(db: Session, notificacao_id: int):
    notificacao = get_notificacao_by_id(db, notificacao_id)
    if not notificacao:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail="notificacao não encontrada",
        )
    db.delete(notificacao)
    db.commit()
    return notificacao