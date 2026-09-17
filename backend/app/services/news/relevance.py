import re
import time
import email.utils
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from app.services.news.base import NewsCategory, SeverityLevel

NER_STATES = {
    "ASSAM": [
        "assam", "guwahati", "silchar", "tezpur", "barak", "dibrugarh", "jorhat", "nagaon",
        "kaziranga", "dima hasao", "karbi anglong", "brahmaputra", "goalpara", "dhubri", "tinsukia",
        "অসম", "असम"
    ],
    "ARUNACHAL PRADESH": [
        "arunachal", "itanagar", "tawang", "sela", "bomdila", "bhalukpong", "pasighat", "kameng",
        "vartak", "ziro", "lohit", "অরুণাচল", "अरुणाचल"
    ],
    "MEGHALAYA": [
        "meghalaya", "shillong", "cherrapunji", "sohra", "dawki", "jowai", "khasi", "jaintia",
        "garo", "laitkor", "nh-06", "मेघालय"
    ],
    "MANIPUR": [
        "manipur", "imphal", "senapati", "mao gate", "jiribam", "churachandpur", "nh-37", "nh-102b",
        "nh-02", "মণিপুর", "मणिपुर"
    ],
    "MIZORAM": [
        "mizoram", "aizawl", "kolasib", "lunglei", "champai", "nh-54", "মিজোরাম", "मिजोरम"
    ],
    "NAGALAND": [
        "nagaland", "kohima", "dimapur", "chumukedima", "nh-29", "mokokchung", "mon", "नागालैंड"
    ],
    "TRIPURA": [
        "tripura", "agartala", "dharmanagar", "kailashahar", "nh-08", "udaipur", "ত্রিপুরা", "त्रिपुरा"
    ],
    "SIKKIM": [
        "sikkim", "gangtok", "rangpo", "pakyong", "mangan", "teesta", "rorathang", "nh-10",
        "swastik", "siliguri", "সিকিম", "सिक्किम"
    ]
}

DISASTER_KEYWORDS = [
    "flood", "landslide", "mudslide", "rockfall", "cloudburst", "cyclone", "earthquake", "quake",
    "extreme weather", "heavy rainfall", "torrential", "submerged", "inundated", "disaster", "calamity",
    "बनापानी", "धस", "भूस्खलन", "बाढ़", "বন্যা", "ধস"
]

TRANSPORT_KEYWORDS = [
    "road closure", "road blocked", "highway blocked", "bridge damage", "bridge collapse", "traffic disruption",
    "blockade", "detour", "convoy", "freight", "medical supply", "cold-chain", "fuel", "food logistics",
    "fci", "bro", "nhidcl", "pwd", "nh-", "highway", "rerouted", "জাতীয় সড়ক", "राजमार्ग"
]

CRITICAL_RULES = [
    "cloudburst", "massive landslide", "total blockade", "bridge collapse", "red alert",
    "severe flood", "state emergency", "highway completely closed", "deadly", "casualties",
    "कट ऑफ", "ठप्प", "विच्छेद", "সম্পূর্ণ বন্ধ"
]

HIGH_RULES = [
    "landslide", "blocked", "heavy rainfall", "orange alert", "disrupted", "evacuation",
    "advisory", "warning", "mudslide", "rockfall", "traffic halted", "भूस्खलन", "बाढ़", "ধস", "বন্যা"
]

MODERATE_RULES = [
    "repair", "maintenance", "slow traffic", "yellow alert", "construction", "delay",
    "regulated traffic", "single lane", "एकतरफा", "मजबूत"
]


def parse_pub_date_timestamp(pub_date_str: str) -> float:
    """
    Parses RSS pubDate (e.g. 'Tue, 30 Jun 2026 07:00:00 GMT' or ISO string) into unix epoch float.
    """
    if not pub_date_str:
        return time.time()
    try:
        dt = email.utils.parsedate_to_datetime(pub_date_str)
        return dt.timestamp()
    except Exception:
        pass
    try:
        # Try ISO format
        dt = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        return time.time()


NON_NER_KEYWORDS = [
    # English
    "jammu", "kashmir", "himachal", "uttarakhand", "kerala", "mumbai", "delhi", "punjab",
    "haryana", "rajasthan", "gujarat", "maharashtra", "chennai", "bengaluru", "kolkata",
    # Hindi / Devanagari
    "जम्मू", "कश्मीर", "हिमाचल", "उत्तराखंड", "पंजाब", "हरियाणा", "राजस्थान", "दिल्ली", "मुंबई",
    # Bengali
    "জম্মু", "কাশ্মীর", "হিমাচল", "উত্তরাখণ্ড", "পাঞ্জাব", "হরিয়ানা", "রাজস্থান", "দিল্লি", "মুম্বই"
]

def infer_location(text: str, fallback_location: Optional[str] = None) -> str:
    """
    Dynamically infers state location from text content.
    Prioritizes explicit state and district/city keyword matches over fallback.
    Identifies out-of-region non-NER articles cleanly.
    """
    text_lower = text.lower()
    for state_name, keywords in NER_STATES.items():
        if any(kw in text_lower for kw in keywords):
            return state_name
            
    # Check if text is explicitly about another non-NER Indian state
    if any(non_ner in text_lower for non_ner in NON_NER_KEYWORDS):
        return "OUT_OF_REGION"
            
    if any(k in text_lower for k in ["northeast", "north east", "ner", "পূর্বোত্তর", "पूर्वोत्तर"]):
        return "ALL NER"
        
    if fallback_location and fallback_location.upper() in NER_STATES:
        return fallback_location.upper()
        
    return "ALL NER"


def infer_category(title: str, summary: str) -> str:
    combined = (title + " " + summary).lower()
    if any(k in combined for k in ["landslide", "mudslide", "rockfall", "debris", "slope failure", "धस", "भूस्खलन"]):
        return NewsCategory.LANDSLIDE.value
    if any(k in combined for k in ["flood", "submerged", "inundated", "waterlogging", "teesta", "brahmaputra", "বন্যা", "बाढ़"]):
        return NewsCategory.FLOOD.value
    if any(k in combined for k in ["weather", "rain", "monsoon", "cloudburst", "cyclone", "fog", "storm", "imd", "बारिश", "मौसम"]):
        return NewsCategory.WEATHER.value
    if any(k in combined for k in ["fci", "freight", "cargo", "supply", "cold-chain", "logistics", "depot", "आपूर्ति"]):
        return NewsCategory.LOGISTICS.value
    if any(k in combined for k in ["bridge", "highway construction", "nhidcl", "tunnel", "power", "grid", "पुल"]):
        return NewsCategory.INFRASTRUCTURE.value
    if any(k in combined for k in ["road", "highway", "traffic", "nh-", "blockade", "detour", "bro", "रास्ता", "सड़क"]):
        return NewsCategory.ROAD_TRANSPORT.value
    if any(k in combined for k in ["advisory", "order", "government", "notification", "dc office", "एडवाइजरी"]):
        return NewsCategory.GOVERNMENT_ADVISORY.value
    if any(k in combined for k in ["rescue", "ndrf", "sdrf", "relief", "evacuation", "emergency response", "बचाव"]):
        return NewsCategory.EMERGENCY_RESPONSE.value
    if any(k in combined for k in ["disaster", "earthquake", "quake", "calamity", "आपदा"]):
        return NewsCategory.DISASTER.value
    return NewsCategory.GENERAL.value


def infer_severity(title: str, summary: str) -> str:
    combined = (title + " " + summary).lower()
    if any(rule in combined for rule in CRITICAL_RULES):
        return SeverityLevel.CRITICAL.value
    if any(rule in combined for rule in HIGH_RULES):
        return SeverityLevel.HIGH.value
    if any(rule in combined for rule in MODERATE_RULES):
        return SeverityLevel.MODERATE.value
    return SeverityLevel.LOW.value


def calculate_relevance_score(
    title: str,
    summary: str,
    location: str,
    severity: str,
    published_at: str
) -> Tuple[float, Dict[str, float]]:
    combined = (title + " " + summary).lower()

    # 1. Location relevance (max 35.0)
    location_score = 10.0
    if location == "OUT_OF_REGION":
        location_score = 0.0
    elif location != "ALL NER":
        location_score = 35.0
    elif any(kw in combined for kw in ["northeast", "north east", "ner", "assam", "meghalaya", "arunachal", "manipur", "mizoram"]):
        location_score = 25.0

    # 2. Disaster relevance (max 25.0)
    disaster_matches = sum(1 for kw in DISASTER_KEYWORDS if kw in combined)
    disaster_score = min(25.0, disaster_matches * 8.5)

    # 3. Transport & logistics relevance (max 20.0)
    transport_matches = sum(1 for kw in TRANSPORT_KEYWORDS if kw in combined)
    transport_score = min(20.0, transport_matches * 6.5)

    # 4. Severity bonus (max 10.0)
    severity_score_map = {
        SeverityLevel.CRITICAL.value: 10.0,
        SeverityLevel.HIGH.value: 7.5,
        SeverityLevel.MODERATE.value: 5.0,
        SeverityLevel.LOW.value: 2.5
    }
    sev_score = severity_score_map.get(severity, 2.5)

    # 5. Recency score (max 10.0)
    pub_ts = parse_pub_date_timestamp(published_at)
    now_ts = time.time()
    age_hours = max(0.0, (now_ts - pub_ts) / 3600.0)
    if age_hours < 24:
        recency_score = 10.0
    elif age_hours < 72:
        recency_score = 8.0
    elif age_hours < 168:
        recency_score = 6.0
    else:
        recency_score = 4.0

    total_score = round(min(100.0, location_score + disaster_score + transport_score + sev_score + recency_score), 1)

    breakdown = {
        "location_relevance": round(location_score, 1),
        "disaster_relevance": round(disaster_score, 1),
        "transport_relevance": round(transport_score, 1),
        "severity_bonus": round(sev_score, 1),
        "recency_score": round(recency_score, 1)
    }

    return total_score, breakdown
