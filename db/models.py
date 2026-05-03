from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, BigInteger, Integer, String, DateTime, func, text, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from schemas import db_schemas
import enum
import uuid

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    source = Column(SQLEnum(db_schemas.MarketPlace, name='market_place'), nullable=False, default=db_schemas.MarketPlace.wildberries)
    type = Column(SQLEnum(db_schemas.TaskType), nullable=False, default=db_schemas.TaskType.fetch_cards)
    status = Column(SQLEnum(db_schemas.TaskStatus, name='task_status'), default=db_schemas.TaskStatus.pending)
    priority = Column(Integer, default=0)
    payload = Column(JSONB, nullable=False)
    total_found = Column(Integer)
    error_message = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))

class Cookie(Base):
    __tablename__ = "cookies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    source = Column(SQLEnum(db_schemas.MarketPlace, name="market_place"), nullable=False, default=db_schemas.MarketPlace.wildberries)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())