from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi_app.models.connect_db import SessionLocal
from fastapi_app.services.recipe import RecipeDetailsAgent
from fastapi_app.common.schema import RecipeDetailRequest,RecipeDetailResponse,RecipeDetail,RecipeResponseData
from fastapi_app.common.constants import (RECIPE_DETAILS)
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(RECIPE_DETAILS, response_model=RecipeDetailResponse)
def get_recipe_details(request: RecipeDetailRequest, db: Session = Depends(get_db)):

    recipe_agent = RecipeDetailsAgent(language=request.language)
    response_content = recipe_agent.get_recipe(request.session_id, request.data)

    if not response_content:
        raise HTTPException(status_code=404, detail="Recipe not found")

    try:
        # Fix ingredients if they are in string format
        if isinstance(response_content.ingredients, str):
            response_content.ingredients = [line.strip() for line in response_content.ingredients.splitlines() if line.strip()]

        # Additional cleanup even if it's already a list
        elif isinstance(response_content.ingredients, list):
            response_content.ingredients = [item.strip() for item in response_content.ingredients if item.strip()]

        # Same can apply to instructions if needed
        if isinstance(response_content.instructions, str):
            response_content.instructions = response_content.instructions.splitlines()
        
        # Convert nutrients to nutritional_info
        nutrient_info = {}
        if response_content.nutrients:

            nutrients_raw = response_content.nutrients 

            for name, nutrient in nutrients_raw.items():
                try:
                    nutrient_info[name] = f"{nutrient.value}{nutrient.unit}"
                except AttributeError:
                    nutrient_info[name] = nutrient  # If already formatted

        # Convert response_content to dict and inject nutritional_info
            content_dict = response_content.dict()
            content_dict["nutritional_info"] = nutrient_info
            content_dict.pop("nutrients", None)  
        else:
            content_dict = response_content.dict()

        #use updated dict to create RecipeDetail
        recipe_detail = RecipeDetail(**content_dict)

        response = RecipeDetailResponse(
            success=True,
            status_code=200,
            message="Success",
            data=RecipeResponseData(recipe=recipe_detail)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invalid recipe structure: {e}")

    return response
