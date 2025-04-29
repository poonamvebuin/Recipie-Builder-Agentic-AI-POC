from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class AllergenBase(BaseModel):
    allergen_name: str


class Allergen(AllergenBase):
    allergen_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_delete: Optional[bool]

    class Config:
        from_attributes = True


class AllergyDataEmbeddingBase(BaseModel):
    input_text: str
    allergen_id: int
    input_text_embedding: dict


class AllergyDataEmbedding(AllergyDataEmbeddingBase):
    id: int
    created_date: Optional[datetime]
    updated_date: Optional[datetime]
    is_delete: Optional[bool]
    is_ignored: Optional[bool]

    class Config:
        from_attributes = True


class AllergyDataEmbeddingVectorBase(BaseModel):
    input_text: str
    allergen_id: int
    input_text_embedding: list[float]


class AllergyDataEmbeddingVector(AllergyDataEmbeddingVectorBase):
    id: int
    created_date: Optional[datetime]
    updated_date: Optional[datetime]
    is_delete: Optional[bool]
    is_ignored: Optional[bool]

    class Config:
        from_attributes = True


class AllergyHistoryBase(BaseModel):
    request_id: UUID
    input_data: dict
    prediction_output: dict
    response: dict
    status: int


class AllergyHistory(AllergyHistoryBase):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    is_deleted: Optional[bool]

    class Config:
        from_attributes = True


class PredictionResponse(BaseModel):
    statusCode: int


class AllergyFeedback(BaseModel):
    AI: bool
    allergy_name: str
    remove_ingrediant: list
    add_ingrediant: list

    class Config:
        from_attributes = True


class PredictAllergy(BaseModel):
    data: str
    allergy_list: list

    class Config:
        from_attributes = True
