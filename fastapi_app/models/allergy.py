from datetime import datetime
import logging
import uuid
from typing import List
from sqlalchemy import and_, select, text
from sqlalchemy.orm import Session
from fastapi_app.models.models import (
    AllergyDataEmbeddingVector,
    BelcAiAllergen,
    AllergyHistory,
    BelcAiAllergyDataEmbeddingClean,
)
from fastapi_app.common.schema import Allergen
from fastapi import HTTPException
from collections import defaultdict
from psycopg2 import IntegrityError, extras

from fastapi_app.common.utils import get_embedding

extras.register_uuid()


def get_allergy(db: Session, skip: int = 0, limit: int = 10) -> List[Allergen]:
    try:
        return db.query(BelcAiAllergen).offset(skip).limit(limit).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")


def add_allergy(allergy: Allergen, db: Session) -> Allergen:
    try:
        db_allergy = BelcAiAllergen(allergen_name=allergy.allergen_name)
        db.add(db_allergy)
        db.commit()
        db.refresh(db_allergy)
        return db_allergy
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")


def get_similarity_out(input, db) -> list:
    result = None
    query = f"""
        SELECT data_emb.input_text, allergen.allergen_name, 1 - (data_emb.input_text_embedding <=> '{input}') AS cosine_similarity
        FROM
            belc_ai_allergy_data_embedding_vector AS data_emb
        JOIN
            belc_ai_allergen AS allergen ON data_emb.allergen_id = allergen.allergen_id
        WHERE
            data_emb.is_delete = false AND data_emb.is_ignored = false
        ORDER BY cosine_similarity DESC LIMIT 10;"""

    result = db.execute(text(query))

    print(result)

    return result

def ignore_word_query(db):
    ignore_word_query = (
        select(BelcAiAllergyDataEmbeddingClean.input_text, BelcAiAllergen.allergen_name)
        .join(
            BelcAiAllergen,
            BelcAiAllergyDataEmbeddingClean.allergen_id == BelcAiAllergen.allergen_id,
        )
        .where(
            and_(
                BelcAiAllergyDataEmbeddingClean.is_ignored == True,
                BelcAiAllergyDataEmbeddingClean.is_delete == False,
                BelcAiAllergen.is_delete == False,
            )
        )
    )
    ignore_word_db_data = db.execute(ignore_word_query).all()

    return ignore_word_db_data


def insert_history(db, data, response_body, response, status):
    history = AllergyHistory(
        request_id=str(uuid.uuid4()),
        input_data=data,
        prediction_output=response_body,
        response=response,
        status=status,
    )
    # Add the object to the session and commit the transaction
    db.add(history)
    db.commit()

def update_allergy(allergy_name: str, remove_ingrediant: list, db):
    for i in remove_ingrediant:
        query = f"""
            WITH allergen_info AS (
                SELECT allergen_id
                FROM belc_ai_allergen
                WHERE allergen_name = '{allergy_name}'
            )
            INSERT INTO public.belc_ai_allergy_data_embedding_vector (input_text, allergen_id, input_text_embedding, updated_date, is_delete, is_ignored)
            VALUES ('{i}', (SELECT allergen_id FROM allergen_info), '{get_embedding(i)['data'][0]['embedding']}', CURRENT_TIMESTAMP, false, TRUE)
            ON CONFLICT (input_text, allergen_id) DO UPDATE
            SET
                updated_date = CURRENT_TIMESTAMP,
                is_delete = TRUE,
                is_ignored = TRUE;     
            """
        db.execute(text(query))
        db.commit()
    logging.info(f"Updated Record for : {remove_ingrediant}")

    response = {
        "statusCode": 200,
        "body": {"result": f"Record Updated for {allergy_name}"},
    }

    return response


def insert_allergy(allergy_name: str, add_ingredian: list, db):
    allergen = BelcAiAllergen(allergen_name=allergy_name)

    # Add the instance to the session
    db.add(allergen)

    try:
        # Commit the session to insert the new record
        db.commit()
    except IntegrityError as e:
        # If the record already exists, handle the conflict error
        db.rollback()
        # You can optionally log or handle the error here
        print(f"Allergen '{allergy_name}' already exists.")
    except Exception as e:
        # Handle any other exceptions
        db.rollback()
        print(f"Error occurred: {str(e)}")

    # Without raw query
    allergen = (
        db.query(BelcAiAllergen)
        .filter(BelcAiAllergen.allergen_name == allergy_name)
        .first()
    )

    if not allergen:
        return None

    for i in add_ingredian:
        embedding = get_embedding(i)["data"][0]["embedding"]
        data_embedding = AllergyDataEmbeddingVector(
            input_text=i,
            allergen_id=allergen.allergen_id,
            input_text_embedding=embedding,
            is_delete=False,
            is_ignored=False,
        )
        existing_data = (
            db.query(AllergyDataEmbeddingVector)
            .filter(
                AllergyDataEmbeddingVector.input_text == i,
                AllergyDataEmbeddingVector.allergen_id == allergen.allergen_id,
            )
            .first()
        )

        if existing_data:
            existing_data.input_text_embedding = embedding
            existing_data.is_delete = False
            existing_data.is_ignored = False
            existing_data.updated_date = datetime.now()
        else:
            db.add(data_embedding)

    db.commit()

    logging.info(f"Updated Record for : {add_ingredian}")


    response = {
        "statusCode": 200,
        "body": {"result": f"Record Updated for {allergy_name}"},
    }

    return response
