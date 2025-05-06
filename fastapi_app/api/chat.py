from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi_app.models.connect_db import SessionLocal
from fastapi_app.services.chat import RecipeChatAgent
from fastapi_app.common.schema import NewChatRequest, NewChatResponse, ChatData,SupervisorRequest,SupervisorResponse,SupervisorResponseData
from fastapi_app.common.constants import (NEW_CHAT,RECIPE_SUGGESSTION)
router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(NEW_CHAT, response_model=NewChatResponse)
def create_new_chat(request: NewChatRequest, db: Session = Depends(get_db)):
    """
    Create a new chat session using RecipeChatAgent (class-based).
    """
    recipe_agent = RecipeChatAgent(language=request.language)
    agent = recipe_agent.create_chat()
    welcome_data = recipe_agent.get_welcome_message(request.language)

    # Prepare response
    response = NewChatResponse(
        session_id=agent.session_id,
        data=ChatData(
            message=welcome_data["message"],
            options=welcome_data["options"],
            option_message=welcome_data["option_message"]
        )
    )

    return response


@router.post(RECIPE_SUGGESSTION, response_model=SupervisorResponse)
def create_new_chat(request: SupervisorRequest, db: Session = Depends(get_db)):
    """
    Create a new chat session using RecipeChatAgent (class-based).
    """
    recipe_agent = RecipeChatAgent(language=request.language)
    # Process the user message and get the response
    response_content = recipe_agent.process_user_message(request.session_id, request.data)
    # Prepare response (customize as needed)
    response = SupervisorResponse(
        success=True,
        status_code=200,
        message="Success",
        data=response_content
    )
    return response