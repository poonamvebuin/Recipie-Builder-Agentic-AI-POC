import boto3 # type: ignore
import json
from typing import Any, Dict


__ssm_client = boto3.client('ssm')
__secrets_manager_client = boto3.client('secretsmanager')

def get_parameter_value(name: str) -> Any:
    resp = __ssm_client.get_parameters(
            Names=[name],
            WithDecryption=False
        )
    param = resp['Parameters'][0]
    return param['Value']

def get_parameter_encrypted_value(name: str) -> Any:
    resp = __ssm_client.get_parameters(
            Names=[name],
            WithDecryption=True
        )
    return resp['Parameters'][0]['Value']

def get_secret_value(name: str) -> Dict[str, Any]:
    response = __secrets_manager_client.get_secret_value(SecretId=name)
    
    return json.loads(response['SecretString'])
