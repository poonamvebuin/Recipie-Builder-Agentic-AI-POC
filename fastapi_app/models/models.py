from sqlalchemy import (
    UUID,
    Column,
    ForeignKey,
    Integer,
    String,
    Boolean,
    TIMESTAMP,
    UniqueConstraint,
)
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector


Base = declarative_base()


class BelcAiAllergen(Base):
    __tablename__ = "belc_ai_allergen"
    __table_args__ = (UniqueConstraint("allergen_name", name="unique_allergen"),)

    allergen_id = Column(Integer, primary_key=True)
    allergen_name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP)
    is_delete = Column(Boolean, default=False)


class BelcAiAllergyDataEmbedding(Base):
    __tablename__ = "belc_ai_allergy_data_embedding"

    id = Column(Integer, primary_key=True)
    input_text = Column(String(255))
    allergen_id = Column(Integer, ForeignKey("belc_ai_allergen.allergen_id"))
    input_text_embedding = Column(JSONB)
    created_date = Column(TIMESTAMP, default=datetime.now)
    updated_date = Column(TIMESTAMP)
    is_delete = Column(Boolean, default=False)
    is_ignored = Column(Boolean, default=False)

    allergen = relationship("BelcAiAllergen")


class BelcAiAllergyDataEmbeddingClean(Base):
    __tablename__ = "belc_ai_allergy_data_embedding_clean"

    id = Column(Integer, primary_key=True)
    input_text = Column(String(255))
    allergen_id = Column(Integer, ForeignKey("belc_ai_allergen.allergen_id"))
    input_text_embedding = Column(JSONB)
    created_date = Column(TIMESTAMP, default=datetime.now)
    updated_date = Column(TIMESTAMP)
    is_delete = Column(Boolean, default=False)
    is_ignored = Column(Boolean, default=False)

    allergen = relationship("BelcAiAllergen")


class AllergyDataEmbeddingVector(Base):
    __tablename__ = "belc_ai_allergy_data_embedding_vector"
    __table_args__ = (
        UniqueConstraint("input_text", "allergen_id", name="unique_input_allergen"),
    )

    id = Column(Integer, primary_key=True)
    input_text = Column(String(255), nullable=False)
    allergen_id = Column(
        Integer, ForeignKey("belc_ai_allergen.allergen_id"), nullable=True
    )
    input_text_embedding = mapped_column(Vector(1536))
    created_date = Column(TIMESTAMP, default=datetime.now)
    updated_date = Column(TIMESTAMP)
    is_delete = Column(Boolean)
    is_ignored = Column(Boolean)


class AllergyHistory(Base):
    __tablename__ = "allergy_history"

    id = Column(Integer, primary_key=True)
    request_id = Column(UUID, nullable=False)
    input_data = Column(JSONB)
    prediction_output = Column(JSONB)
    response = Column(JSONB)
    status = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now)
    is_deleted = Column(Boolean, default=False)
