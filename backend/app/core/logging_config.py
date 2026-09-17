import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

SENSITIVE_KEY_PATTERNS = re.compile(
    r"(?i)(password|authorization|token|bearer|secret|access_key|secret_key|api_key|credential|private_key)"
)

def redact_sensitive_data(data: Any) -> Any:
    """
    Recursively redacts sensitive keys (passwords, tokens, credentials, secrets)
    and truncates large Base64 binary strings.
    """
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if SENSITIVE_KEY_PATTERNS.search(str(key)):
                cleaned[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 1000 and ("data:image" in value or ";base64," in value):
                cleaned[key] = f"[BASE64_MEDIA_TRUNCATED_LEN_{len(value)}]"
            else:
                cleaned[key] = redact_sensitive_data(value)
        return cleaned
    elif isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]
    elif isinstance(data, str) and len(data) > 1000 and ("data:image" in data or ";base64," in data):
        return f"[BASE64_MEDIA_TRUNCATED_LEN_{len(data)}]"
    return data


class StructuredJsonFormatter(logging.Formatter):
    """
    Structured JSON Formatter for AWS CloudWatch Insights queryability.
    Formats Python log records into structured JSON payloads with request_id and metadata.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_event: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Extra attributes explicitly passed via extra={...}
        for attr in ("request_id", "user_id", "incident_id", "method", "path", "status_code", "duration_ms", "bedrock_latency_ms", "table_name", "bucket_name", "error_type"):
            if hasattr(record, attr):
                log_event[attr] = getattr(record, attr)

        if record.exc_info:
            log_event["exception"] = self.formatException(record.exc_info)

        # Redact any accidental sensitive data
        cleaned_event = redact_sensitive_data(log_event)
        return json.dumps(cleaned_event)


def setup_structured_logging():
    """
    Configures root logger with StructuredJsonFormatter.
    """
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())
    
    # Avoid adding duplicate handlers
    if not any(isinstance(h, logging.StreamHandler) and isinstance(h.formatter, StructuredJsonFormatter) for h in root_logger.handlers):
        root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)
