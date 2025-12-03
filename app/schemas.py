from datetime import date, time, datetime
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, field_validator


class TipoTurnoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    cor_calendario: Optional[str] = None


class TipoTurnoCreate(TipoTurnoBase):
    pass


class TipoTurnoRead(TipoTurnoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class TurnoBase(BaseModel):
    data_referencia: date
    hora_inicio: time
    hora_fim: time
    tipo: Optional[str] = None
    descricao_opcional: Optional[str] = None

    @field_validator("tipo")
    @classmethod
    def normalize_tipo(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v or None


class TurnoCreate(TurnoBase):
    origem: Literal["telegram", "api"] = "api"


class TurnoRead(BaseModel):
    id: int
    data_referencia: date
    hora_inicio: time
    hora_fim: time
    duracao_minutos: int
    tipo: Optional[str] = None
    descricao_opcional: Optional[str] = None
    criado_em: datetime
    atualizado_em: datetime
    model_config = ConfigDict(from_attributes=True)


class RelatorioDia(BaseModel):
    data: date
    total_minutos: int
    por_tipo: dict[str, int]


class RelatorioPeriodo(BaseModel):
    inicio: date
    fim: date
    total_minutos: int
    dias: list[RelatorioDia]


class UsuarioBase(BaseModel):
    nome: str
    numero_funcionario: str


class UsuarioCreate(UsuarioBase):
    telegram_user_id: int


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    numero_funcionario: Optional[str] = None


class UsuarioRead(UsuarioBase):
    id: int
    telegram_user_id: int
    criado_em: datetime
    atualizado_em: datetime
    model_config = ConfigDict(from_attributes=True)


