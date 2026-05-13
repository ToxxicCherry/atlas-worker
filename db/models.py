from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy import Column, BigInteger, Integer, String, DateTime, func, text, Text, Enum as SQLEnum, ForeignKey, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID as SQLUUID, JSONB
from schemas import db_schemas
from uuid import UUID, uuid4
from datetime import datetime

Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid4, server_default=text("gen_random_uuid()"), index=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tasks = relationship("TaskModel", back_populates="user", cascade="all, delete-orphan")


class TaskModel(Base):
    __tablename__ = 'tasks'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, server_default=text("gen_random_uuid()"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete='CASCADE'))
    source: Mapped[db_schemas.MarketPlace] = mapped_column(SQLEnum(db_schemas.MarketPlace, name='market_place'), default=db_schemas.MarketPlace.wildberries)
    type: Mapped[db_schemas.TaskType] = mapped_column(SQLEnum(db_schemas.TaskType), name='task_type', default=db_schemas.TaskType.fetch_cards)
    status: Mapped[db_schemas.TaskStatus] = mapped_column(SQLEnum(db_schemas.TaskStatus, name='task_status'), default=db_schemas.TaskStatus.pending)
    priority: Mapped[int] = mapped_column(default=0)
    payload: Mapped[dict] = mapped_column(JSONB)
    total_found: Mapped[int | None]
    error_message: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["UserModel"] = relationship('UserModel', back_populates='tasks')


class ProductSizeModel(Base):
    __tablename__ = 'product_sizes'

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, server_default=text("gen_random_uuid()"))
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("products.id"))
    name: Mapped[str]
    price_basic: Mapped[int]
    price_product: Mapped[int]

    products = relationship('ProductModel', back_populates='sizes')

class ProductModel(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str]
    brand: Mapped[str]
    brand_id: Mapped[int] = mapped_column(BigInteger)
    subject_id: Mapped[int] = mapped_column(BigInteger)
    total_quantity: Mapped[int]
    rating: Mapped[float]
    feedbacks: Mapped[int]
    supplier: Mapped[str]
    supplier_id: Mapped[int] = mapped_column(BigInteger)
    supplier_rating: Mapped[float]
    weight: Mapped[float]
    wh: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    sizes = relationship('ProductSizeModel', back_populates='products', cascade='all, delete-orphan')


class TaskProduct(Base):
    __tablename__ = 'task_products'

    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id", ondelete='CASCADE'), primary_key=True)
    product_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('products.id', ondelete='CASCADE'), primary_key=True)



class Cookie(Base):
    __tablename__ = "cookies"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid4, server_default=text("gen_random_uuid()"))
    source = Column(SQLEnum(db_schemas.MarketPlace, name="market_place"), nullable=False, default=db_schemas.MarketPlace.wildberries)
    x_wbaas_token = Column(Text, nullable=False)
    user_agent = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())



