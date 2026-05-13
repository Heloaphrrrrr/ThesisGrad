MISSING_COLUMNS = [
    "domain",
    "location",
    "value",
    "transaction_count",
]

INVALID_RULES = {
    "domain": "UNKNOWN_DOMAIN",
    "value": -999,
    "transaction_count": -10,
}

ANOMALY_MULTIPLIERS = {
    "value": 10,
    "transaction_count": 1000,
}