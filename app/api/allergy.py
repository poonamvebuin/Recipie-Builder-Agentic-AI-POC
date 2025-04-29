from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.common.schema import Allergen, AllergyFeedback, PredictAllergy
from app.models.allergy import add_allergy, get_allergy
from app.models.connect_db import SessionLocal
from app.common.constants import ALLERGY_DETECTION_FEEDBACK, ALLERGY, PREDICT_ALLERGY
from app.services.allergy import process, update_or_insert_data_db

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(ALLERGY, response_model=Allergen)
def add_allergy_endpoint(allergy: Allergen, db: Session = Depends(get_db)):
    print("POST allergy")
    return add_allergy(db=db, allergy=allergy)


@router.get(ALLERGY, response_model=list[Allergen])
def get_allergy_endpoint(db: Session = Depends(get_db), skip: int = 0, limit: int = 10):
    print("GET allergy")
    return get_allergy(db, skip, limit)


@router.post(PREDICT_ALLERGY)
def predict_allergy(data: PredictAllergy, db: Session = Depends(get_db)):
    print("POST predict_allergy")
    return process(data=data, db=db)


@router.post(ALLERGY_DETECTION_FEEDBACK)
def allergy_detection_feedback(
    feedback: AllergyFeedback, db: Session = Depends(get_db)
):
    print("POST allergy_detection_feedback")
    return update_or_insert_data_db(
        feedback.allergy_name, feedback.remove_ingrediant, feedback.add_ingrediant, db
    )
