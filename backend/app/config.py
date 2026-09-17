import os
import logging
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

logger = logging.getLogger("neris.config")

class Settings(BaseSettings):
    """
    NERIS Application Configuration & Environment Management.
    Explicitly separates DEVELOPMENT mode (local FastAPI, localhost frontend, local utilities)
    from PRODUCTION mode (AWS Lambda, API Gateway, DynamoDB, S3, Cognito, Bedrock, EventBridge, CloudWatch).
    """

    # Environment Identity
    APP_NAME: str = Field(default="NERIS — North-East Regional Emergency Transit System")
    ENVIRONMENT: str = Field(
        default="development",
        description="Environment mode: 'development' (dev/local) or 'production' (prod)"
    )
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # AWS Core Parameters
    AWS_REGION: str = Field(default="ap-south-1", description="AWS Target Region")

    # Amazon DynamoDB Tables
    DYNAMODB_INCIDENTS_TABLE: str = Field(default="ner_incidents", description="DynamoDB Incidents Table")
    DYNAMODB_ALERTS_TABLE: str = Field(default="ner_alerts", description="DynamoDB Alerts Table")
    DYNAMODB_NEWS_TABLE: str = Field(default="ner_news_articles", description="DynamoDB Disaster News Table")
    DYNAMODB_FLEET_TABLE: str = Field(default="ner_fleet_telemetry", description="DynamoDB Fleet Telemetry Table")

    # Amazon S3 Media Bucket
    S3_BUCKET_EVIDENCE: str = Field(default="neris-evidence-photos-ap-south-1", description="S3 Evidence Bucket Name")

    # Amazon Cognito User Pool & App Client
    COGNITO_USER_POOL_ID: Optional[str] = Field(default=None, description="Cognito User Pool ID")
    COGNITO_CLIENT_ID: Optional[str] = Field(default=None, description="Cognito App Client ID")
    JWT_SECRET: str = Field(default="neris-jwt-secret-key-ap-south-1-2026", description="JWT Signing Secret Key")

    # Amazon Bedrock AI Model
    BEDROCK_MODEL_ID: str = Field(default="anthropic.claude-3-haiku-20240307-v1:0", description="Amazon Bedrock Model ID")

    # CORS Allowed Origins
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        description="Comma-separated allowed CORS origin URLs"
    )

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def is_production(self) -> bool:
        """Returns True if the application is executing in production mode."""
        return self.ENVIRONMENT.lower() in ("production", "prod")

    @property
    def is_development(self) -> bool:
        """Returns True if the application is executing in development mode."""
        return self.ENVIRONMENT.lower() in ("development", "dev", "local")

    def validate_production_config(self) -> List[str]:
        """
        Validates required environment configuration for PRODUCTION deployment.
        Returns a list of missing required parameters.
        """
        missing = []
        if not self.AWS_REGION:
            missing.append("AWS_REGION")
        if not self.DYNAMODB_INCIDENTS_TABLE:
            missing.append("DYNAMODB_INCIDENTS_TABLE")
        if not self.DYNAMODB_ALERTS_TABLE:
            missing.append("DYNAMODB_ALERTS_TABLE")
        if not self.DYNAMODB_NEWS_TABLE:
            missing.append("DYNAMODB_NEWS_TABLE")
        if not self.DYNAMODB_FLEET_TABLE:
            missing.append("DYNAMODB_FLEET_TABLE")
        if not self.S3_BUCKET_EVIDENCE:
            missing.append("S3_BUCKET_EVIDENCE")
        if not self.COGNITO_USER_POOL_ID:
            missing.append("COGNITO_USER_POOL_ID")
        if not self.COGNITO_CLIENT_ID:
            missing.append("COGNITO_CLIENT_ID")
        if not self.BEDROCK_MODEL_ID:
            missing.append("BEDROCK_MODEL_ID")
        if not self.JWT_SECRET or self.JWT_SECRET == "neris-jwt-secret-key-ap-south-1-2026":
            missing.append("JWT_SECRET (must be explicitly provided via environment variable or AWS Secrets Manager in production)")
        return missing

_settings_instance: Optional[Settings] = None

def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
        if _settings_instance.is_production:
            missing_vars = _settings_instance.validate_production_config()
            if missing_vars:
                err_msg = (
                    f"CRITICAL PRODUCTION CONFIGURATION FAILURE: Application is set to ENVIRONMENT='{_settings_instance.ENVIRONMENT}', "
                    f"but missing required AWS configuration variables: {', '.join(missing_vars)}. "
                    f"Production mode strictly forbids silent mock/local fallbacks. "
                    f"Please provide all required environment variables in deployment configuration."
                )
                logger.error(err_msg)
                raise RuntimeError(err_msg)
            logger.info("PRODUCTION MODE ACTIVE: AWS infrastructure settings validated successfully.")
        else:
            logger.info(
                f"DEVELOPMENT MODE ACTIVE (ENVIRONMENT='{_settings_instance.ENVIRONMENT}'): "
                f"Local development utilities and resilience fallbacks enabled."
            )
    return _settings_instance
