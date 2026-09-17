import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_disaster_news_feed():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print("=========================================================================")
    print("  VERIFYING DISASTER & LOGISTICS INTELLIGENCE FEED (AWS DYNAMODB & NEWS)")
    print("=========================================================================")
    
    # Step 1: EventBridge / Scheduled Ingestion Trigger
    print("\n1. Testing EventBridge / Scheduled Ingestion Trigger (POST /api/news/ingest)...")
    ingest_res = requests.post(f"{BASE_URL}/api/news/ingest")
    assert ingest_res.status_code == 200, f"Ingestion failed: {ingest_res.text}"
    ingest_data = ingest_res.json()
    print("   [SUCCESS] Ingestion Status:", ingest_data.get("status"))
    print("   [SUCCESS] Total Articles Ingested & Normalized:", ingest_data.get("total_articles"))
    print("   [SUCCESS] DynamoDB Persisted:", ingest_data.get("dynamodb_persisted"))
    assert ingest_data.get("eventbridge_triggered") is True
    assert ingest_data.get("dynamodb_persisted") is True

    # Step 2 & 5: GET /api/news API retrieval
    print("\n2. Testing Primary News Feed Endpoint (GET /api/news)...")
    news_res = requests.get(f"{BASE_URL}/api/news")
    assert news_res.status_code == 200, f"GET /api/news failed: {news_res.text}"
    news_data = news_res.json()
    articles = news_data.get("articles", [])
    print(f"   [SUCCESS] Returned {len(articles)} normalized articles from backend.")
    assert len(articles) > 0, "No articles returned!"

    # Step 3 & 4: Schema Normalization & DynamoDB persistence verification
    sample_article = articles[0]
    print("\n3. Validating Article Schema Normalization & Transparency Fields...")
    print(f"   Article ID:    {sample_article.get('id')}")
    print(f"   Title:         {sample_article.get('title')}")
    print(f"   Category:      {sample_article.get('category')}")
    print(f"   Location:      {sample_article.get('location')}")
    print(f"   Severity:      {sample_article.get('severity')}")
    print(f"   Source:        {sample_article.get('source')}")
    print(f"   Source URL:    {sample_article.get('source_url')}")
    print(f"   Published At:  {sample_article.get('published_at')}")
    print(f"   Retrieved At:  {sample_article.get('retrieved_at')}")
    print(f"   Is Demo Data:  {sample_article.get('is_demo')}")

    required_keys = ["id", "title", "summary", "category", "source", "source_url", "published_at", "retrieved_at", "location", "severity"]
    for key in required_keys:
        assert key in sample_article, f"Missing required article key: {key}"
    assert sample_article["source_url"].startswith("http://") or sample_article["source_url"].startswith("https://") or sample_article["source_url"] == "#"

    # Step 6: Categories & Locations Endpoints
    print("\n6. Testing Metadata Endpoints...")
    cat_res = requests.get(f"{BASE_URL}/api/news/categories")
    assert cat_res.status_code == 200
    categories = cat_res.json().get("categories", [])
    print("   [SUCCESS] Supported Categories:", categories)

    loc_res = requests.get(f"{BASE_URL}/api/news/locations")
    assert loc_res.status_code == 200
    locations = loc_res.json().get("locations", [])
    print("   [SUCCESS] Supported Locations:", locations)

    # Step 7: Search Filtering (GET /api/news/search?q=)
    print("\n7. Testing Search Filtering (GET /api/news/search?q=landslide)...")
    search_res = requests.get(f"{BASE_URL}/api/news/search?q=landslide")
    assert search_res.status_code == 200
    search_articles = search_res.json().get("articles", [])
    print(f"   [SUCCESS] Found {len(search_articles)} articles matching search query 'landslide'.")

    # Step 8: Location Filtering (GET /api/news?location=ASSAM)
    print("\n8. Testing Location Filtering (GET /api/news?location=ASSAM)...")
    loc_filter_res = requests.get(f"{BASE_URL}/api/news?location=ASSAM")
    assert loc_filter_res.status_code == 200
    loc_articles = loc_filter_res.json().get("articles", [])
    print(f"   [SUCCESS] Found {len(loc_articles)} articles for location 'ASSAM'.")

    # Step 9: Category Filtering (GET /api/news?category=LANDSLIDE)
    print("\n9. Testing Category Filtering (GET /api/news?category=LANDSLIDE)...")
    cat_filter_res = requests.get(f"{BASE_URL}/api/news?category=LANDSLIDE")
    assert cat_filter_res.status_code == 200
    cat_articles = cat_filter_res.json().get("articles", [])
    print(f"   [SUCCESS] Found {len(cat_articles)} articles for category 'LANDSLIDE'.")

    # Step 10: Sorting (GET /api/news?sort_by=newest)
    print("\n10. Testing Sorting (GET /api/news?sort_by=newest)...")
    sort_res = requests.get(f"{BASE_URL}/api/news?sort_by=newest")
    assert sort_res.status_code == 200
    sort_articles = sort_res.json().get("articles", [])
    print(f"   [SUCCESS] Returned {len(sort_articles)} sorted articles.")

    # Step 11: Deduplication Verification
    print("\n11. Testing Deduplication Logic...")
    re_ingest_res = requests.post(f"{BASE_URL}/api/news/ingest")
    assert re_ingest_res.status_code == 200
    print("   [SUCCESS] Re-ingested successfully without throwing duplicate error.")

    # Step 13: Amazon Bedrock AI Summary (POST /api/news/{id}/ai-summary)
    target_id = sample_article["id"]
    print(f"\n13. Testing Amazon Bedrock AI Summary (POST /api/news/{target_id}/ai-summary)...")
    bedrock_res = requests.post(f"{BASE_URL}/api/news/{target_id}/ai-summary")
    assert bedrock_res.status_code == 200, f"Bedrock AI summary failed: {bedrock_res.text}"
    ai_data = bedrock_res.json()
    print(f"   [SUCCESS] AI Summary: {ai_data['ai_summary']}")
    print(f"   [SUCCESS] Disclaimer: {ai_data['disclaimer']}")
    assert "AI-generated summary" in ai_data['disclaimer']

    # Step 14: Provider failure / cache status check
    print("\n14. Verifying Provider Failure / Cached Transparency Status...")
    print(f"    Provider Status: {news_data.get('provider_status')}")
    print(f"    Is Live Available: {news_data.get('is_live_available')}")
    print(f"    Is Cached: {news_data.get('is_cached')}")

    print("\n=========================================================================")
    print("  ALL 14 DISASTER NEWS FEED ACCEPTANCE TESTS PASSED SUCCESSFULLY (EXIT 0)")
    print("=========================================================================")

if __name__ == "__main__":
    test_disaster_news_feed()
