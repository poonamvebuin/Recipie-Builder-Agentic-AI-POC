# fastapi_App/models.py

from sqlalchemy import (
    Boolean, Column, String, Integer, BigInteger, DateTime, Index, create_engine, ForeignKey, Text, TIMESTAMP
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

# Import the vector type from pgvector
from pgvector.sqlalchemy import Vector

Base = declarative_base()

# 1. AgentSessions Table (matches your SQL)
class AgentSession(Base):
    __tablename__ = "agent_sessions"
    __table_args__ = (
        Index("ix_ai_agent_sessions_agent_id", "agent_id"),
        Index("ix_ai_agent_sessions_team_session_id", "team_session_id"),
        Index("ix_ai_agent_sessions_user_id", "user_id"),
        {"schema": "ai"},
    )

    session_id = Column(String, primary_key=True)
    user_id = Column(String)
    memory = Column(JSONB)
    session_data = Column(JSONB)
    extra_data = Column(JSONB)
    created_at = Column(BigInteger, default=func.extract('epoch', func.now()))
    updated_at = Column(BigInteger)
    agent_id = Column(String)
    team_session_id = Column(String)
    agent_data = Column(JSONB)

# 2. Product Table (example fields, adjust as needed)
class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"schema": "ai"}

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String, nullable=False)    
    price = Column(String(50))  # Stored as string in DB
    weight = Column(Integer)
    unit = Column(String(50))
    tax = Column(String(50))
    is_vegan = Column(Boolean)
    brand = Column(String(255))
    image_url = Column(Text)
    

# 3. JSON Documents Table (for knowledge base)
class JSONDocument(Base):
    __tablename__ = "json_documents"
    __table_args__ = (
        Index("idx_json_documents_content_hash", "content_hash"),
        Index("idx_json_documents_id", "id"),
        Index("idx_json_documents_name", "name"),
        {"schema": "ai"},
    )

    id = Column(String, primary_key=True)
    name = Column(String)
    meta_data = Column(JSONB, default=dict)
    filters = Column(JSONB, default=dict)
    content = Column(Text)
    embedding = Column(Vector(1536))  # pgvector column
    usage = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True))
    content_hash = Column(String)


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = {"schema": "ai"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("ai.products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
