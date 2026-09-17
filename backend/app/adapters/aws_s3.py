import os
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from app.config import get_settings

logger = logging.getLogger("neris.aws_s3")
settings = get_settings()

LOCAL_UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

def validate_image_magic_bytes(file_bytes: bytes) -> str:
    """
    Inspects image file header bytes to prevent MIME spoofing or uploading executable files disguised as images.
    """
    if not file_bytes or len(file_bytes) < 8:
        raise ValueError("File content is empty or too small to be a valid image file.")

    # JPEG magic header (\xFF\xD8\xFF)
    if file_bytes.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"

    # PNG magic header (\x89PNG\r\n\x1a\n)
    if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"

    # WEBP magic header (RIFF....WEBP)
    if file_bytes.startswith(b"RIFF") and len(file_bytes) >= 12 and file_bytes[8:12] == b"WEBP":
        return "image/webp"

    raise ValueError("Disallowed or corrupted image file content. Header magic byte validation failed (allowed image formats: JPG, JPEG, PNG, WEBP).")

class S3StorageAdapter:
    """
    Amazon S3 Object Storage Adapter for Field Evidence Media & Incident Photos.
    Enforces file type validation (JPG, JPEG, PNG, WEBP), magic header inspection, file size limit (10MB),
    AES256 server-side encryption, private object storage, and controlled presigned access.
    """
    def __init__(self, bucket_name: str = None, region_name: str = None):
        self.bucket_name = bucket_name or getattr(settings, "S3_BUCKET_EVIDENCE", None) or "neris-evidence-photos-ap-south-1"
        self.region_name = region_name or getattr(settings, "AWS_REGION", None) or "ap-south-1"
        self.s3_client = None
        self._init_client()

    def _init_client(self):
        try:
            self.s3_client = boto3.client("s3", region_name=self.region_name)
            logger.info(f"Initialized Amazon S3 client for bucket '{self.bucket_name}' in region '{self.region_name}'.")
        except Exception as err:
            logger.warning(f"Amazon S3 client notice: {err}. Using local media storage fallback.")

    def upload_evidence_photo(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """
        Validates file format, magic bytes & size, generates unique safe object key, and uploads to Amazon S3.
        """
        # 0. Path Traversal & Filename Sanitization
        safe_filename = os.path.basename(filename).replace("..", "").replace("/", "").replace("\\", "")

        # 1. File Size Validation (Max 10MB)
        file_size = len(file_bytes)
        if file_size > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"File size {round(file_size / 1024 / 1024, 2)}MB exceeds maximum allowed limit of 10MB.")

        # 2. File Extension & MIME Validation
        extension = safe_filename.split(".")[-1].lower() if "." in safe_filename else "jpg"
        if extension not in ALLOWED_EXTENSIONS or (content_type and content_type.lower() not in ALLOWED_CONTENT_TYPES):
            raise ValueError(f"Invalid file extension '.{extension}' or MIME type '{content_type}'. Allowed image formats: JPG, JPEG, PNG, WEBP.")

        # 3. Magic Header Byte Inspection
        detected_mime = validate_image_magic_bytes(file_bytes)

        # 4. Safe Server-Side S3 Object Key Generation (No user-controlled path traversal)
        timestamp_str = int(time.time())
        s3_key = f"evidence/{uuid.uuid4().hex[:12]}_{timestamp_str}.{extension}"
        iso_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # 5. Encryption & Private Object Upload to Amazon S3
        uploaded_to_s3 = False
        if self.s3_client:
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=file_bytes,
                    ContentType=detected_mime,
                    ServerSideEncryption="AES256"
                )
                logger.info(f"Successfully uploaded encrypted private evidence photo '{filename}' to Amazon S3 key '{s3_key}'.")
                uploaded_to_s3 = True
            except (BotoCoreError, ClientError) as err:
                if settings.is_production:
                    logger.error(f"Amazon S3 upload failed in PRODUCTION mode: {err}")
                    raise RuntimeError(f"Amazon S3 upload failed in PRODUCTION mode: {err}")
                logger.warning(f"Amazon S3 upload notice ({err}). Storing locally in development mode.")

        if not uploaded_to_s3:
            if settings.is_production:
                raise RuntimeError("Amazon S3 client unconfigured or unavailable in PRODUCTION mode.")
            # Local fallback media save (Development mode only)
            if not os.path.exists(LOCAL_UPLOADS_DIR):
                os.makedirs(LOCAL_UPLOADS_DIR, exist_ok=True)
            local_filename = f"{uuid.uuid4().hex[:8]}_{safe_filename}"
            local_path = os.path.join(LOCAL_UPLOADS_DIR, local_filename)
            try:
                with open(local_path, "wb") as f:
                    f.write(file_bytes)
                public_url = f"/uploads/{local_filename}"
            except Exception as e:
                logger.error(f"Error saving local upload: {e}")
                public_url = "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957"
        else:
            # Generate short-lived presigned download URL for private S3 object retrieval
            public_url = self.generate_presigned_download_url(s3_key) or f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{s3_key}"

        return {
            "status": "UPLOADED" if uploaded_to_s3 else "PENDING",
            "s3_confirmed": uploaded_to_s3,
            "evidence_status": "UPLOADED" if uploaded_to_s3 else "PENDING",
            "evidence_url": public_url,
            "uploaded_at": iso_now,
            "filename": safe_filename,
            "s3_key": s3_key,
            "s3_bucket": self.bucket_name,
            "aws_region": self.region_name
        }

    def delete_evidence_photo(self, s3_key: str) -> bool:
        """
        Deletes an orphaned S3 evidence object if associated incident creation fails.
        """
        if self.s3_client and s3_key:
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
                logger.info(f"Cleaned up orphaned S3 evidence object '{s3_key}' from bucket '{self.bucket_name}'.")
                return True
            except (BotoCoreError, ClientError) as err:
                logger.warning(f"Failed to delete orphaned S3 object '{s3_key}': {err}")
        return False

    def generate_presigned_download_url(self, s3_key: str, expiration_seconds: int = 3600) -> Optional[str]:
        """
        Generates a secure presigned GET URL for private S3 evidence objects.
        Valid for expiration_seconds (default: 1 hour). Prevents direct public access.
        """
        if not s3_key:
            return None

        if self.s3_client:
            try:
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': s3_key},
                    ExpiresIn=expiration_seconds
                )
                return url
            except (BotoCoreError, ClientError) as err:
                logger.error(f"Failed to generate S3 presigned URL for key '{s3_key}': {err}")

        safe_name = os.path.basename(s3_key)
        return f"/uploads/{safe_name}"

    def generate_presigned_upload_url(
        self,
        filename: str,
        content_type: str = "image/jpeg",
        expiration_seconds: int = 900
    ) -> Dict[str, Any]:
        """
        Generates a secure presigned PUT URL allowing authorized frontend clients
        to upload evidence photos directly to Amazon S3 without exposing AWS credentials.
        """
        safe_filename = os.path.basename(filename).replace("..", "").replace("/", "").replace("\\", "")
        extension = safe_filename.split(".")[-1].lower() if "." in safe_filename else "jpg"
        if extension not in ALLOWED_EXTENSIONS or content_type.lower() not in ALLOWED_CONTENT_TYPES:
            raise ValueError(f"Disallowed file format: extension '.{extension}', MIME '{content_type}'. Allowed image formats: JPG, JPEG, PNG, WEBP.")

        s3_key = f"evidence/{uuid.uuid4().hex[:12]}_{int(time.time())}.{extension}"
        if self.s3_client:
            try:
                presigned_url = self.s3_client.generate_presigned_url(
                    'put_object',
                    Params={
                        'Bucket': self.bucket_name,
                        'Key': s3_key,
                        'ContentType': content_type
                    },
                    ExpiresIn=expiration_seconds
                )
                return {
                    "presigned_url": presigned_url,
                    "s3_key": s3_key,
                    "s3_bucket": self.bucket_name,
                    "expires_in_seconds": expiration_seconds
                }
            except (BotoCoreError, ClientError) as err:
                logger.error(f"Failed to generate presigned upload URL: {err}")
                if settings.is_production:
                    raise RuntimeError(f"Presigned URL generation failed in PRODUCTION mode: {err}")
        return {}

_s3_adapter_instance: Optional[S3StorageAdapter] = None

def get_s3_adapter() -> S3StorageAdapter:
    global _s3_adapter_instance
    if _s3_adapter_instance is None:
        _s3_adapter_instance = S3StorageAdapter()
    return _s3_adapter_instance
