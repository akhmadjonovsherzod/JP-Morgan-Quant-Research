"""
Central place for settings. Everything is read from environment variables
(with safe local defaults), so the same code runs unchanged whether it's
started with `uvicorn` on a laptop or inside the Docker container.
"""

import os

from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "quant_research"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

# Standard banking assumption used everywhere expected loss is calculated.
# Kept in one place so the notebooks, the API, and Power BI can't drift apart.
RECOVERY_RATE = 0.10

# Probability of default at/above this level is treated as "will default"
# when we need a hard yes/no label (e.g. for the confusion matrix in Power BI).
DEFAULT_THRESHOLD = 0.60

RATING_LABELS = {
    1: "Very Low",
    2: "Low",
    3: "Medium",
    4: "High",
    5: "Very High",
    6: "Extreme",
}

RATING_COLORS = {
    1: "#00B050",
    2: "#92D050",
    3: "#FFC000",
    4: "#FF9900",
    5: "#FF3B30",
    6: "#7030A0",
}
