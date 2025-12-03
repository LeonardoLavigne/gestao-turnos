from datetime import datetime, date, time
from typing import Optional

from sqlalchemy import Integer, String, Date, Time, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class TipoTurno(Base):
    __tablename__ = "tipos_turno"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # ✅ Multi-tenancy: isolamento por usuário
    telegram_user_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True,
        doc="ID do usuário do Telegram (multi-tenancy)"
    )
    
    nome: Mapped[str] = mapped_column(String(50), index=True)
    descricao: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cor_calendario: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    turnos: Mapped[list["Turno"]] = relationship("Turno", back_populates="tipo")


class Turno(Base):
    __tablename__ = "turnos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # ✅ Multi-tenancy: isolamento por usuário
    telegram_user_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True,
        doc="ID do usuário do Telegram (multi-tenancy)"
    )

    data_referencia: Mapped[date] = mapped_column(Date, index=True)
    hora_inicio: Mapped[time] = mapped_column(Time)
    hora_fim: Mapped[time] = mapped_column(Time)

    duracao_minutos: Mapped[int] = mapped_column(Integer)

    tipo_turno_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("tipos_turno.id"), nullable=True
    )
    tipo_livre: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, doc="Nome do tipo quando não vinculado a TipoTurno."
    )

    descricao_opcional: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    tipo: Mapped[Optional[TipoTurno]] = relationship(
        "TipoTurno",
        back_populates="turnos",
    )

    integracao: Mapped[Optional["IntegracaoCalendario"]] = relationship(
        "IntegracaoCalendario",
        back_populates="turno",
        uselist=False,
    )


class IntegracaoCalendario(Base):
    __tablename__ = "integracao_calendario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    turno_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("turnos.id"), unique=True, index=True
    )

    provedor: Mapped[str] = mapped_column(
        String(50), default="disroot_caldav", nullable=False
    )
    event_uid: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="UID do evento no calendário remoto.",
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    turno: Mapped[Turno] = relationship(
        "Turno",
        back_populates="integracao",
    )


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_user_id: Mapped[int] = mapped_column(
        Integer, unique=True, index=True, nullable=False
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    numero_funcionario: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class Assinatura(Base):
    __tablename__ = "assinaturas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # ✅ Multi-tenancy: isolamento por usuário
    telegram_user_id: Mapped[int] = mapped_column(
        Integer, unique=True, index=True, nullable=False,
        doc="ID do usuário do Telegram (dono da assinatura)"
    )
    
    stripe_customer_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), default="inactive", nullable=False)
    plano: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    
    data_inicio: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    data_fim: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


