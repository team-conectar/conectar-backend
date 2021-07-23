from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.orm.session import Session
from starlette.responses import JSONResponse
from starlette.requests import Request
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from typing import List
from fastapi import HTTPException, status

from db import models
from db.pessoa.crud import get_pessoa_by_email

import os

MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_FROM = os.getenv('MAIL_FROM')
MAIL_PORT = int(os.getenv('MAIL_PORT'))
MAIL_SERVER = os.getenv('MAIL_SERVER')
MAIL_FROM_NAME = os.getenv('MAIN_FROM_NAME')


conf = ConnectionConfig(
    MAIL_USERNAME=MAIL_USERNAME,
    MAIL_PASSWORD=MAIL_PASSWORD,
    MAIL_FROM=MAIL_FROM,
    MAIL_PORT=MAIL_PORT,
    MAIL_SERVER=MAIL_SERVER,
    MAIL_FROM_NAME=MAIL_FROM_NAME,
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER='templates/'
)


async def envia_email_assincrono(
    db: Session,
    email_para: str,
):

    filtro = db.query(models.Pessoa).filter(models.Pessoa.email == email_para)

    if not filtro:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Email Não Cadastrado!"
        )

    pessoa = get_pessoa_by_email(db, email_para)

    message = MessageSchema(
        subject='Esqueci a senha',
        recipients=[email_para],
        template_body={'name': pessoa.nome},
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name='email.html')


def envia_email_bg(
    background_tasks: BackgroundTasks,
    subject: str,
    email_to: str,
    body: dict
):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype='html',
    )
    fm = FastMail(conf)
    background_tasks.add_task(
        fm.send_message, message, template_name='email.html')
