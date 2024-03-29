from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from db import models
from . import schemas


def create_seguir(
    db: Session, seguir: schemas.SeguirCreate
) -> schemas.Seguir:

    db_seguir = models.Seguir(
        seguido_id=seguir.seguido_id,
        seguidor_id=seguir.seguidor_id
    )

    db.add(db_seguir)
    db.commit()
    db.refresh(db_seguir)


def get_seguidores(
    db: Session, seguido_id: int
) -> schemas.Seguir:

    seguidores_tupla = db.query(models.Pessoa, models.Seguir).filter(
        models.Seguir.seguido_id == seguido_id).filter(models.Seguir.seguidor_id == models.Pessoa.id).all()

    seguidores = []
    for tupla in seguidores_tupla:
        seguidores.append(tupla[0])

    return seguidores


def get_seguindo(
    db: Session, seguidor_id: int
) -> schemas.Seguir:

    seguindo_tupla = db.query(models.Pessoa, models.Seguir).filter(
        models.Seguir.seguidor_id == seguidor_id).filter(models.Seguir.seguido_id == models.Pessoa.id).all()

    seguindo = []
    for tupla in seguindo_tupla:
        seguindo.append(tupla[0])

    return seguindo


def delete_seguir(
    db: Session,
    seguido_id: int,
    seguidor_id: int,
):

    db_seguir = db.query(models.Seguir)\
        .filter(models.Seguir.seguido_id == seguido_id)\
        .filter(models.Seguir.seguidor_id == seguidor_id)\
        .first()

    if not db_seguir:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Relação não encontrada."
        )
    db.delete(db_seguir)
    db.commit()
