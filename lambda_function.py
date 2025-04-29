# import json
# from fastapi import FastAPI
# from app.models.connect_db import create_tables_on_startup
# from mangum import Mangum
# from app.api import allergy
# from contextlib import asynccontextmanager


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     create_tables_on_startup()
#     yield
    
# app = FastAPI()
# app.include_router(allergy.router, prefix="/Dev/allergy/api/v1")

# handler = Mangum(app)

# def lambda_handler(event, context):
#     print(f"event {event}")

#     return handler(event, context)

 
import os
import json
import uvicorn
from mangum import Mangum
from fastapi import FastAPI
from inspect import getmembers, isclass
import app.common.exception as exceptions
from contextlib import asynccontextmanager
from app.models.connect_db import create_tables_on_startup
from app.common.utils import exception_handler, custom_exception_handler
from app.api import allergy
# , raw_material, file, data_extraction, raw_material_allergy_mappings, raw_material_mappings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous context manager to execute setup tasks when the application starts up.
    Args:
        app (FastAPI): The FastAPI application instance.
    Yields:
        None
    """
    create_tables_on_startup()
    yield

def map_exception_handlers(app):
    """
    Binds custom exception handlers to the FastAPI application.
    Args:
        app (FastAPI): The FastAPI application instance.
    Returns:
        None
    This function iterates over all the classes in the `exceptions` module and adds an exception handler for each class
    to the `app` instance. The exception handler is `custom_exception_handler`. It also adds an exception handler for
    the base `Exception` class, which is `exception_handler`.
    """
    # Custom exception binding
    business_exception = dict(getmembers(exceptions, isclass))
    [
        app.add_exception_handler(exception_class, custom_exception_handler)
        for exception, exception_class in business_exception.items()
        if exception in exceptions.__all__
    ]
    # Handle Internal Server Error
    app.add_exception_handler(Exception, exception_handler)

app = FastAPI(lifespan=lifespan)
prefix = "/" +os.environ.get("API_PREFIX", "Dev")
app.include_router(allergy.router, prefix=prefix+"/allergy-detection/api/v1")
# app.include_router(raw_material.router, prefix=prefix+"/allergy-detection/api/v1")
# app.include_router(file.router, prefix=prefix + "/allergy-detection/api/v1")
# app.include_router(data_extraction.router, prefix=prefix+"/allergy-detection/api/v1")
# app.include_router(raw_material_allergy_mappings.router, prefix=prefix + "/allergy-detection/api/v1")
# app.include_router(raw_material_mappings.router, prefix=prefix + "/allergy-detection/api/v1")
map_exception_handlers(app)
handler = Mangum(app)

def lambda_handler(event, context):
    """
    Lambda function handler to process incoming events.
    Args:
        event (dict): The event data.
        context (object): The context object.
    Returns:
        dict: The response data.
    """
    try:
        # Attempt to process the first event type
        event["body"] = json.dumps(event["body"])
    except KeyError:
        try:
            # If KeyError, attempt to process the second event type
            event["body"] = json.dumps(event["Records"][0]["body"])
            print(f"Record event {event}")
        except (KeyError, IndexError) as e:
            # Handle any other errors that might occur
            print(f"Error processing event: {e}")
    print(f"event {event}")
    response = handler(event, context)
    print(response)
    return json.loads(response["body"])

if __name__ == "__main__":
    try:
        uvicorn.run("lambda_function:app", host="localhost", port=8000, reload=True)
    except Exception as e:
        print(f"Server exit with error: {e}")
 
 