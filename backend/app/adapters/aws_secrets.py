import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from app.config import get_settings

logger = logging.getLogger("neris.aws_secrets")
settings = get_settings()

class SecretsManagerAdapter:
    """
    AWS Secrets Manager Adapter for securely retrieving external credentials, 
    API keys, and service secrets without hardcoding or logging raw secrets.
    """
    def __init__(self, region_name: str = None):
        self.region_name = region_name or getattr(settings, "AWS_REGION", "ap-south-1")
        self.client = None
        self._init_client()

    def _init_client(self):
        try:
            self.client = boto3.client("secretsmanager", region_name=self.region_name)
            logger.info(f"Initialized AWS Secrets Manager client in region '{self.region_name}'.")
        except Exception as err:
            logger.warning(f"AWS Secrets Manager client notice: {err}. Active fallback: Environment config mode.")

    def get_secret(self, secret_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a secret value by name from AWS Secrets Manager.
        """
        if not secret_name:
            return None

        if self.client:
            try:
                response = self.client.get_secret_value(SecretId=secret_name)
                if "SecretString" in response:
                    try:
                        return json.loads(response["SecretString"])
                    except json.JSONDecodeError:
                        return {"secret": response["SecretString"]}
            except (BotoCoreError, ClientError) as err:
                logger.warning(f"Secrets Manager lookup for '{secret_name}' notice: {err}.")

        return None

_secrets_adapter_instance: Optional[SecretsManagerAdapter] = None

def get_secrets_adapter() -> SecretsManagerAdapter:
    global _secrets_adapter_instance
    if _secrets_adapter_instance is None:
        _secrets_adapter_instance = SecretsManagerAdapter()
    return _secrets_adapter_instance
