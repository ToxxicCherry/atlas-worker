from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, BigInteger, Integer, String, DateTime, func, text, Text, Enum as SQLEnum, ForeignKey, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from schemas import db_schemas
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"), index=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tasks = relationship("Task", backref="user", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
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


class ProductSize(Base):
    __tablename__ = 'product_sizes'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    product_id = Column(BigInteger, ForeignKey("products.id"), nullable=False)
    name = Column(String, nullable=False)
    price_basic = Column(Integer, nullable=False)
    price_product = Column(Integer, nullable=False)

class Product(Base):
    __tablename__ = 'products'

    id = Column(BigInteger, primary_key=True)
    name = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    brand_id = Column(BigInteger, nullable=False)
    subject_id = Column(BigInteger, nullable=False)
    total_quantity = Column(Integer, nullable=False)
    rating = Column(Float, nullable=False)
    feedbacks = Column(Integer, nullable=False)
    supplier = Column(String, nullable=False)
    supplier_id = Column(BigInteger, nullable=False)
    supplier_rating = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    wh = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    sizes = relationship('ProductSize', backref='product', cascade='all, delete-orphan')


class TaskProduct(Base):
    __tablename__ = 'task_products'

    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete='CASCADE'), primary_key=True)
    product_id = Column(BigInteger, ForeignKey('products.id', ondelete='CASCADE'), primary_key=True)



class Cookie(Base):
    __tablename__ = "cookies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    source = Column(SQLEnum(db_schemas.MarketPlace, name="market_place"), nullable=False, default=db_schemas.MarketPlace.wildberries)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())



