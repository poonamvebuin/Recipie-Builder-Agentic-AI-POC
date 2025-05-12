from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Union,Dict,Any


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


class NewChatRequest(BaseModel):
    language: str = Field(
        ..., description="The language preference for the chat session"
    )


class ChatData(BaseModel):
    message: str
    options: List[str]
    option_message: List[str]


class NewChatResponse(BaseModel):
    session_id: str
    data: ChatData


class Preferences(BaseModel):
    taste: Optional[str]
    cooking_time: Optional[str]
    ingredients: List[str]
    allergy_or_ingredient_to_avoid: List[str]
    dietry: Optional[str]


class Data(BaseModel):
    prompt: str
    preferences: Preferences


class SupervisorRequest(BaseModel):
    language: str
    session_id: Optional[str] = ""
    data: Data


class SupervisorResponseData(BaseModel):
    response: str
    suggestions: List[str]


class SupervisorResponse(BaseModel):
    success: bool
    status_code: int
    message: str
    data: SupervisorResponseData


class RecipeData(BaseModel):
    selected_recipes: str
    preferences: Preferences


class Nutrient(BaseModel):
    value: Union[int, float]
    unit: str


class RecipeDetail(BaseModel):
    recipe_title: str
    cuisine_type: str
    total_time: str
    serving_size: Optional[str] = None
    ingredients: List[str]
    instructions: List[str]
    image_url: Optional[str] = None
    mp4_url: Optional[str] = None
    nutritional_info: Optional[Dict[str, str]] = None
    difficulty_level: Optional[str] = None


class RecipeResponseData(BaseModel):
    recipe: RecipeDetail


class RecipeDetailResponse(BaseModel):
    success: bool
    status_code: int
    message: str
    data: RecipeResponseData


class RecipeDetailRequest(BaseModel):
    language: str
    session_id: Optional[str]
    data : RecipeData


class Product(BaseModel):
    product_id: int
    product_name: str
    price: str
    weight: int
    unit: str
    tax: str
    is_vegan: bool
    brand: Optional[str] = None
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel):
    total: int
    items: List[Product]


class ProductListResponse(BaseModel):
    success: bool
    status_code: int
    message: str
    data: PaginatedResponse  
    
    model_config = ConfigDict(from_attributes=True)


class ProductItem(BaseModel):
    product_id: str
    product_name: str
    price: str
    tax: str
    price_with_tax: str
    weight: str


class ProductResponseData(BaseModel):
    products: List[ProductItem]


class ProductResponse(BaseModel):
    success: bool
    status_code: int
    message: str
    data: ProductResponseData


class RecipeOutput(BaseModel):
    recipe_title: str
    cuisine_type: Optional[str] = None
    cook_time: Optional[str] = None
    total_time: Optional[str] = None
    ingredients: Optional[str] = None
    instructions: Optional[List[str]] = None
    nutrients: Optional[Dict[str, str]] = None
    difficulty_level: Optional[str] = None
    serving_size: Optional[str] = None
    extra_features: Optional[Dict[str, str]] = None
    image_url: Optional[str] = None
    suggestions: Optional[List[str]] = None
    explanation: Optional[str] = None
    mp4_url: Optional[str] = None



