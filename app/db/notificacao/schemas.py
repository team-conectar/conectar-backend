from pydantic import BaseModel
from datetime import datetime
import typing as t


class NotificacaoBase(BaseModel):
    remetente_id: int
    destinatario_id: int
    projeto_id: t.Optional[int]
    pessoa_projeto_id: t.Optional[int]
    situacao: str
    foto: t.Optional[str]
    anexo: t.Optional[str]
    lido: bool
    link: t.Optional[str]


class NotificacaoCreate(NotificacaoBase):
    situacao: t.Optional[str]
    link: t.Optional[str] = None

    class Config:
        orm_mode = True


class Notificacao(NotificacaoBase):
    id: int
    data_criacao: datetime
    data_atualizacao: t.Optional[datetime]

    class Config:
        orm_mode = True


class NotificacaoOut(NotificacaoBase):
    situacao: str
    foto: t.Optional[str]
    link: t.Optional[str]

    class Config:
        orm_mode = True


class NotificacaoEdit(NotificacaoBase):
    remetente_id: t.Optional[int]
    destinatario_id: t.Optional[int]
    projeto_id: t.Optional[int]
    pessoa_projeto_id: t.Optional[int]
    situacao: t.Optional[str]
    lido: t.Optional[bool]
    data_atualizacao: t.Optional[datetime]

    class Config:
        orm_mode = True
