import re

SECURITY_KEYWORDS = [
    "auth", "password", "token", "secret", "key", "credentials", "sudo", "admin"
]

CRITICAL_OPS = [
    "delete", "drop", "update", "insert", "payment", "transaction", "transfer"
]

BUSINESS_LOGIC = [
    "api", "config", "env", "feature_flag", "workflow", "pipeline"
]

TEST_KEYWORDS = [
    "test_", "assert", "mock", "fixture"
]

def compute_risk(diff_text: str) -> str:
    text = diff_text.lower()

    security_hits = sum(1 for k in SECURITY_KEYWORDS if k in text)
    critical_hits = sum(1 for k in CRITICAL_OPS if k in text)
    business_hits = sum(1 for k in BUSINESS_LOGIC if k in text)
    test_hits = sum(1 for k in TEST_KEYWORDS if k in text)

    # Risk scoring
    score = 0
    score += security_hits * 5
    score += critical_hits * 4
    score += business_hits * 2
    score -= test_hits * 1  # tests reduce risk

    if score >= 8:
        return "High"
    elif score >= 4:
        return "Medium"
    else:
        return "Low"
