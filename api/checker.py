import requests
import json
from datetime import datetime, timedelta

# --- CONFIGURATION ---

MOCK_AVAILABILITY_MODE = False  # set True for testing

# Telegram Credentials
TELEGRAM_BOT_TOKEN = "YOUR_REAL_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "-5015233395"        # Group
TELEGRAM_PERSONAL_ID = "-5015233395"    # Alerts

# Store & Products
STORE_ID = "R756"
PRODUCTS = [
    {"name": "iPhone 17 256GB White", "sku": "MG6K4HN/A"},
    {"name": "iPhone 17 256GB Black", "sku": "MG6J4HN/A"},
    {"name": "iPhone 17 256GB Mist Blue", "sku": "MG6L4HN/A"},
    {"name": "iPhone 17 256GB Sage", "sku": "MG6N4HN/A"},
    {"name": "iPhone 17 256GB Lavender", "sku": "MG6M4HN/A"},
]

# Latest cookie (update manually when expired)
LATEST_APPLE_COOKIES = "PASTE YOUR COOKIE HERE"

# Apple API endpoint
APPLE_API_URL = "https://www.apple.com/in/shop/fulfillment-messages"

BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "x-skip-redirect": "true",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


# --- UTILITY FUNCTIONS ---

def send_telegram_message(chat_id, message):
    if "YOUR_REAL_TELEGRAM_BOT_TOKEN" in TELEGRAM_BOT_TOKEN:
        print("❌ Telegram token missing. Skipping Telegram.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}

    try:
        r = requests.post(url, json=payload, timeout=10)
        if not r.ok:
            print(f"Telegram Error {r.status_code}: {r.text}")
        r.raise_for_status()
    except Exception as e:
        print(f"Telegram send error: {e}")


def build_api_query():
    params = {
        "fae": "true",
        "little": "false",
        "mts.0": "regular",
        "mts.1": "sticky",
        "fts": "true",
    }
    for i, p in enumerate(PRODUCTS):
        params[f"parts.{i}"] = p["sku"]

    return "&".join([f"{k}={v}" for k, v in params.items()])


# --- REPLACED CURL WITH PYTHON REQUESTS ---

def run_apple_request(query_string):
    full_url = f"{APPLE_API_URL}?{query_string}"

    headers = BASE_HEADERS.copy()
    headers["Cookie"] = LATEST_APPLE_COOKIES
    headers["Referer"] = "https://www.apple.com/in/shop/buy-iphone/iphone-17/"

    try:
        print(f"Fetching Apple API for {len(PRODUCTS)} items...")
        r = requests.get(full_url, headers=headers, timeout=30)

        # Cookie expired
        if r.status_code in [401, 403]:
            alert = "🚨 COOKIE EXPIRED — Update the Cookie immediately!"
            print(alert)
            send_telegram_message(TELEGRAM_PERSONAL_ID, alert)
            return None

        return r.text

    except Exception as e:
        print(f"Request Error: {e}")
        return None


# --- MAIN LOGIC ---

def check_apple_availability():
    print("Starting Apple availability check...")

    query_string = build_api_query()
    data = {}

    if MOCK_AVAILABILITY_MODE:
        data = {
            "body": {
                "content": {
                    "pickupMessage": {
                        "stores": [
                            {
                                "storeNumber": STORE_ID,
                                "partsAvailability": {
                                    "MG6K4HN/A": {"pickupDisplay": "available", "pickupSearchQuote": "Today"},
                                    "MG6J4HN/A": {"pickupDisplay": "ships-to-store", "pickupSearchQuote": "Tomorrow"},
                                },
                            }
                        ]
                    }
                }
            }
        }
    else:
        response = run_apple_request(query_string)
        if response is None:
            return None

        try:
            data = json.loads(response)
        except:
            print("Invalid JSON from Apple.")
            return None

    # Parse store
    store_list = (
        data.get("body", {})
        .get("content", {})
        .get("pickupMessage", {})
        .get("stores", [])
    )

    store = next((s for s in store_list if s.get("storeNumber") == STORE_ID), None)

    if not store:
        msg = f"Store {STORE_ID} not found in response."
        print(msg)
        send_telegram_message(TELEGRAM_CHAT_ID, msg)
        return msg

    availability_list = []
    available_products = []

    for p in PRODUCTS:
        sku = p["sku"]
        name = p["name"]

        info = store.get("partsAvailability", {}).get(sku)

        if not info:
            availability_list.append(f"❓ {name} - No Data")
            continue

        pickup_display = info.get("pickupDisplay", "")
        pickup_quote = info.get("pickupSearchQuote", "")

        is_today = pickup_display == "available"
        is_tomorrow = "tomorrow" in pickup_quote.lower()
        is_available = is_today or is_tomorrow

        symbol = "✅" if is_available else "❌"

        if is_today:
            detail = " - Available Today"
        elif is_tomorrow:
            detail = " - Available Tomorrow"
        else:
            detail = f" - {pickup_quote}"

        if is_available:
            available_products.append(name)

        availability_list.append(f"{symbol} {name}{detail}")

    # Build final message
    count = len(available_products)

    if count > 0:
        header = "🎉 PICKUP AVAILABLE ALERT 🎉\n\n"
        summary = f"{count} iPhone(s) available!\n\n"
    else:
        header = "📅 Apple Availability Status 📅\n\n"
        summary = "No immediate pickup found.\n\n"

    final_message = (
        header
        + summary
        + f"Saket, New Delhi ({STORE_ID})\n"
        + "--------------------------\n"
        + "\n".join(availability_list)
    )

    # Print always (logs)
    print("\n----- FINAL MESSAGE -----")
    print(final_message)
    print("-------------------------\n")

    # Telegram only when available
    if count > 0:
        send_telegram_message(TELEGRAM_CHAT_ID, final_message)

    return final_message   # <-- ALWAYS returned


# Run
if __name__ == "__main__":
    msg = check_apple_availability()
    print("Returned Message:", msg)
