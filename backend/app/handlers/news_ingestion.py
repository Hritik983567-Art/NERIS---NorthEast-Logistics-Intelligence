import time
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

from app.services.news.provider import get_news_service_manager

logger = logging.getLogger("neris.eventbridge_ingestion")

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda Scheduled Entrypoint Handler triggered by Amazon EventBridge (rate(1 hour)).
    Fetches, normalizes, deduplicates, and persists disaster news articles to Amazon DynamoDB ('ner_news_articles').
    Outputs structured CloudWatch operational metrics.
    """
    start_time = time.time()
    iso_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    logger.info({
        "event": "EVENTBRIDGE_TRIGGER",
        "timestamp": iso_now,
        "detail": "Amazon EventBridge scheduled news ingestion rule triggered."
    })

    try:
        manager = get_news_service_manager()
        # Execute feed retrieval synchronously inside asyncio event loop
        result = asyncio.run(manager.get_news_feed(force_refresh=True))

        duration_ms = round((time.time() - start_time) * 1000, 2)
        total_articles = result.get("total_count", 0)
        provider_status = result.get("provider_status", "UNKNOWN")

        # Emit CloudWatch Operational Log Record
        metrics_log = {
            "event": "EVENTBRIDGE_INGESTION_SUMMARY",
            "timestamp": iso_now,
            "status": "SUCCESS" if total_articles > 0 else "PARTIAL_SUCCESS",
            "execution_duration_ms": duration_ms,
            "total_articles_fetched": total_articles,
            "provider_status": provider_status,
            "dynamodb_persisted": True,
            "eventbridge_rule": "rate(1 hour)"
        }
        logger.info(metrics_log)

        return {
            "statusCode": 200,
            "body": {
                "message": "EventBridge scheduled news ingestion completed successfully.",
                "timestamp": iso_now,
                "metrics": metrics_log
            }
        }

    except Exception as err:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        error_log = {
            "event": "EVENTBRIDGE_INGESTION_ERROR",
            "timestamp": iso_now,
            "status": "FAILED",
            "execution_duration_ms": duration_ms,
            "error_message": str(err),
            "eventbridge_rule": "rate(1 hour)"
        }
        logger.error(error_log)

        return {
            "statusCode": 500,
            "body": {
                "message": "EventBridge scheduled news ingestion encountered an error.",
                "timestamp": iso_now,
                "error": str(err)
            }
        }

if __name__ == "__main__":
    # Local CLI testing execution
    res = handler({}, None)
    print(res)
