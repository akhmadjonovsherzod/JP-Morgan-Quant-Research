"""
Bulk-scores every loan in the database in one call.

This used to loop over every loan and POST it to /predict individually
(10,000 HTTP round-trips). That work now happens inside the API itself
(see app/routers/predict.py -> score_all_loans), so this script is just
a thin CLI wrapper for people who'd rather run one command than open
the dashboard.
"""

import sys

import requests

API_URL = "http://127.0.0.1:8000/api/score-all"


def main():
    print(f"Requesting bulk scoring from {API_URL} ...")
    try:
        response = requests.post(API_URL, timeout=120)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"✗ Could not reach the API: {e}")
        sys.exit(1)

    result = response.json()
    print(f"✓ Scored {result['scored']:,} loans.")


if __name__ == "__main__":
    main()
