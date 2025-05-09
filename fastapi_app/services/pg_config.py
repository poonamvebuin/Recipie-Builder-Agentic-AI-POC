# import os
# from app.common.constants import (
#     SECRETS_MANAGER_DB_CREDENTIAL,
#     PARAMETER_DATABASE_ENDPOINT,
#     DATABASE_USERNAME,
#     DATABASE_NAME,
#     DATABASE_PASSWORD
#     )
# from app.services.parameter_store import get_parameter_encrypted_value, \
#     get_secret_value


# class Param:
#     DB_HOST = get_parameter_encrypted_value(os.environ.get(PARAMETER_DATABASE_ENDPOINT))

# def get_pg_config():
#     credentials = get_secret_value(os.environ.get(SECRETS_MANAGER_DB_CREDENTIAL))
#     return {
#         "host": Param.DB_HOST,
#         "dbname": credentials[DATABASE_NAME],
#         "user": credentials[DATABASE_USERNAME],
#         "password": credentials[DATABASE_PASSWORD],
#         "port": 5432
#     }

# For Local Connection
def get_pg_config():

    return {
        "dbname": 'agno_db',
        "host":'localhost',
        "password": 'admin',
        "port": 5432,
        "user": 'postgres',
    }