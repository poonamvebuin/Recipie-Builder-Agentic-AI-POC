from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi_app.models.connect_db import SessionLocal
from fastapi_app.services.chat import create_chat_agent, get_welcome_message
from fastapi_app.common.schema import NewChatRequest, NewChatResponse, ChatData

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/new-chat", response_model=NewChatResponse)
def create_new_chat(request: NewChatRequest, db: Session = Depends(get_db)):
    """
    Create a new chat session based on language preference
    """
    # try:
    # Create a new agent with the specified language
    agent = create_chat_agent(request.language)

    # Get welcome message in the selected language
    welcome_data = get_welcome_message(request.language)
    print(welcome_data)

    # Create response
    response = NewChatResponse(
        session_id=agent.session_id,
        data=ChatData(
            message=welcome_data["message"],
            options=welcome_data["options"],
            option_message=welcome_data["option_message"]
        )
    )

    return response
    
    # except Exception as e:
    #     # Log the error
    #     print(f"Error creating new chat: {str(e)}")
    #     raise HTTPException(status_code=500, detail=f"Failed to create chat session: {str(e)}")
#
#
# @router.post(ALLERGY, response_model=Allergen)
# def add_allergy_endpoint(allergy: Allergen, db: Session = Depends(get_db)):
#     print("POST allergy")
#     return add_allergy(db=db, allergy=allergy)
#
#
# @router.get(ALLERGY, response_model=list[Allergen])
# def get_allergy_endpoint(db: Session = Depends(get_db), skip: int = 0, limit: int = 10):
#     print("GET allergy")
#     return get_allergy(db, skip, limit)


# @router.post(PREDICT_ALLERGY)
# def predict_allergy(data: PredictAllergy, db: Session = Depends(get_db)):
#     print("POST predict_allergy")
#     return process(data=data, db=db)
#
#
# @router.post(ALLERGY_DETECTION_FEEDBACK)
# def allergy_detection_feedback(
#     feedback: AllergyFeedback, db: Session = Depends(get_db)
# ):
#     print("POST allergy_detection_feedback")
#     return update_or_insert_data_db(
#         feedback.allergy_name, feedback.remove_ingrediant, feedback.add_ingrediant, db
#     )
