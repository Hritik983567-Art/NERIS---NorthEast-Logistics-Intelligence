import logging
from typing import List, Dict, Any, Optional
from app.adapters.aws_dynamodb import get_dynamodb_adapter
from app.adapters.aws_s3 import get_s3_adapter

logger = logging.getLogger("neris.incidents_service")

class IncidentsService:
    """
    AWS-backed Incidents Domain Service coordinating Amazon DynamoDB persistence and Amazon S3 evidence storage.
    """
    def __init__(self):
        self.dynamodb = get_dynamodb_adapter()
        self.s3 = get_s3_adapter()

    def get_live_incidents(self) -> List[Dict[str, Any]]:
        """
        Retrieves all incidents from AWS DynamoDB.
        """
        return self.dynamodb.get_all_incidents()

    def create_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Persists a new incident item into AWS DynamoDB.
        """
        return self.dynamodb.save_incident(incident_data)

    def get_incident_by_id(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single incident by ID from AWS DynamoDB.
        """
        return self.dynamodb.get_incident_by_id(incident_id)

    def update_incident(self, incident_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Updates an existing incident in AWS DynamoDB.
        """
        return self.dynamodb.update_incident(incident_id, updates)

    def upload_evidence(self, file_bytes: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """
        Uploads a field evidence photo to Amazon S3.
        """
        return self.s3.upload_evidence_photo(file_bytes, filename, content_type)

_incidents_service_instance: Optional[IncidentsService] = None

def get_incidents_service() -> IncidentsService:
    global _incidents_service_instance
    if _incidents_service_instance is None:
        _incidents_service_instance = IncidentsService()
    return _incidents_service_instance
