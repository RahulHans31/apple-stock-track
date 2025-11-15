import requests
import json
import subprocess
from datetime import datetime, timedelta

# --- HARDCODED Configuration (All values provided by user) ---

# Set this to False for LIVE operation
MOCK_AVAILABILITY_MODE = False

# Telegram Credentials
TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
TELEGRAM_CHAT_ID = '-5015233395'  # Group ID for status notifications
TELEGRAM_PERSONAL_ID = '-5015233395'  # Personal ID for urgent cookie alerts

# Target store and product list
STORE_ID = 'R756'  # Saket, New Delhi (R756)
PRODUCTS = [
    {"name": "iPhone 17 256GB White", "sku": "MG6K4HN/A"},
    {"name": "iPhone 17 256GB Black", "sku": "MG6J4HN/A"},
    {"name": "iPhone 17 256GB Mist Blue", "sku": "MG6L4HN/A"},
    {"name": "iPhone 17 256GB Sage", "sku": "MG6N4HN/A"},
    {"name": "iPhone 17 256GB Lavender", "sku": "MG6M4HN/A"},
]

# --- DYNAMIC COOKIE VARIABLE (MUST be updated manually when expired) ---
# NOTE: Using the latest full Cookie string you provided.
LATEST_APPLE_COOKIES = (
    "dssid2=f0ec55d9-ed76-43b4-b778-a9af0364ebd3; dssf=1; pxro=1; as_uct=0; geo=IN; "
    "shld_bt_m=xlGeDjCnMmOEseHz9-13Ww|1763183691|9SvUT5Sh7_4cD1etH-l3xQ|sdg1-D8UxjNWYRuGJsidGZPU8BY; "
    "as_pcts=Aiz264T-KheTPDJnfRAap:eNlKU2b+pz7F_kP9BXSN9rRZb03aj709kAdz3HX_+xHCzscfAnGA9BkfiKHMfmIwwMzHwRhBNN6wQISP_XSlrYk7BJl9ovDVAt9anT-wlz9:rAqyxi:T7kE+hq4H+Wg-3YEVbJGd95GwHsnpqnZvba7ngasTa; "
    "as_dc=ucp5; sh_spksy=.; s_fid=67264CA68F03B9DA-0145A9054215BC30; s_cc=true; s_sq=%5B%5BB%5D%5D; "
    "at_check=true; mbox=session#190d980011074f1eb047c191c3d66b81#1763178321|PC#190d980011074f1eb047c191c3d66b81.38_0#1763178262; "
    "as_sfa=Mnxpbnxpbnx8ZW5fSU58Y29uc3VtZXJ8aW50ZXJuZXR8MHwwfDE; "
    "as_atb=1.0|MjAyNS0xMS0xNCAwNzoxNDo1MQ|49969a660e47c434c6413af292b0ba1a316a4540; "
    "as_rumid=e373e016-94c5-42b5-99af-3be287f3dbb7; "
    "shld_bt_ck=23-C4TCU03MMEv2_v6Fh8w|1763183670|chi4-3e-TvjaC-2PiVyDIp7ttNGqQlBONuLkJZFuhwVWENSf1cTYLQFer8N2NLOuAxfxrZHLNf0LDSbhkbt1he1xngK8pa-d1YqpHgRUn9iMaj7t1a4mFlGompiBicZn2FwXA02WBbpM4aHstRGZTVh6i6YpnjZ46XcgS2ZMylCxeisEvlgkJ78DSonuXhF_mIJ5o5pe8S3JE9PNFHCfKam0ZnBj7jgsRjFqcqtMGdpAP4p2nX7Iycy06oZR718CmZjpn68X4w-7rXF2XiXd49fS_3u8jnIaTiySZMHtqgi5rvXAPUZAlt793IAWvsASrw5vOHaz808w9odYX8tgBg|C25TvBmr_v1GJsU7nNEse6_BxAU; "
    "as_gloc=ee516fed121342f950c98bd0dd9b00a580ab9b74397a41a0f9367e4d8e6ac9cf8bcb9989e80125323520b4d09ba82a8b3958d0f1e6b27ce14e275dea97d7a58d8f7835e1019e1bb45714e83e52845776d5c9a81320e7c55551cfe1ce297097e9"
)

# Apple API Request details (for building headers)
APPLE_API_URL = "https://www.apple.com/in/shop/fulfillment-messages"
BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "x-skip-redirect": "true",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=4",
    "TE": "trailers",
}

# --- Utility Functions ---


def send_telegram_message(chat_id, message):
    if not TELEGRAM_BOT_TOKEN:
        print("Telegram token is not set. Cannot send message.")
        return

    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
    }

    try:
        response = requests.post(tg_url, json=payload, timeout=10)
        if not response.ok:
            try:
                response_json = response.json()
                error_description = response_json.get(
                    "description", "No description provided"
                )
            except Exception:
                error_description = "Unable to parse error description"
            print(
                f"FAILURE: Telegram API Error. Status: {response.status_code}. Details: {error_description}"
            )

        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")


def build_api_query():
    """Builds the base query parameters for the Apple API call."""
    params = {
        "fae": "true",
        "little": "false",
        "mts.0": "regular",
        "mts.1": "sticky",
        "fts": "true",
    }
    # Add all product SKUs to the query
    for i, product in enumerate(PRODUCTS):
        params[f"parts.{i}"] = product["sku"]

    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return query_string


def run_curl_command(query_string):
    """
    Executes the full curl command as a subprocess and returns the JSON response text.
    Handles cookie expiration alert if the response indicates failure.
    """
    full_url = f"{APPLE_API_URL}?{query_string}"

    # Base command parts
    command_parts = ["curl.exe", full_url]

    # Add headers, including the dynamic Cookie and Referer
    headers = BASE_HEADERS.copy()
    headers["Cookie"] = LATEST_APPLE_COOKIES
    headers[
        "Referer"
    ] = "https://www.apple.com/in/shop/buy-iphone/iphone-17/6.3%22-display-256gb-black"

    for key, value in headers.items():
        command_parts.extend(["-H", f"{key}: {value}"])

    try:
        print(f"Executing curl command for {len(PRODUCTS)} parts...")

        result = subprocess.run(
            command_parts,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

        response_text = result.stdout.strip()

        # --- Critical Check: Cookie Expiration / Auth Failure ---
        if (
            result.returncode != 0
            or "please sign in" in response_text.lower()
            or "apple.com/shop/login" in response_text.lower()
        ):
            cookie_alert = (
                "🚨 COOKIE EXPIRATION ALERT 🚨\n\n"
                f"The Apple session cookies have likely expired or are invalid. (Curl Exit Code: {result.returncode})\n\n"
                "Please obtain a new `Cookie` value and update the `LATEST_APPLE_COOKIES` constant immediately."
            )
            print(cookie_alert)
            send_telegram_message(TELEGRAM_PERSONAL_ID, cookie_alert)
            return None

        return response_text

    except subprocess.TimeoutExpired:
        print("Curl command timed out.")
        return None
    except FileNotFoundError:
        error_msg = "Error: 'curl.exe' not found. Ensure curl is in your system PATH."
        print(error_msg)
        send_telegram_message(TELEGRAM_PERSONAL_ID, error_msg)
        return None
    except Exception as e:
        print(f"An unexpected subprocess error occurred: {e}")
        return None


# --- Main Logic ---


def check_apple_availability():
    """Fetches availability and sends Telegram notifications."""
    print("Starting Apple availability check...")

    # Build the full query string
    query_string = build_api_query()

    data = {}

    if MOCK_AVAILABILITY_MODE:
        print("--- MOCK MODE ACTIVE: Skipping live API call. ---")
        mock_json_response = {
            "body": {
                "content": {
                    "pickupMessage": {
                        "stores": [
                            {
                                "storeNumber": STORE_ID,
                                "storeName": "Saket (MOCK)",
                                "partsAvailability": {
                                    "MG6K4HN/A": {
                                        "pickupDisplay": "ships-to-store",
                                        "pickupSearchQuote": "Available Fri 3 Dec",
                                    },
                                    "MG6J4HN/A": {
                                        "pickupDisplay": "unavailable",
                                        "pickupSearchQuote": "Available Fri 3 Dec",
                                    },
                                    "MG6L4HN/A": {
                                        "pickupDisplay": "available",
                                        "pickupSearchQuote": "Available Today",
                                    },
                                    "MG6N4HN/A": {
                                        "pickupDisplay": "ships-to-store",
                                        "pickupSearchQuote": "Available Tomorrow",
                                    },
                                    "MG6M4HN/A": {
                                        "pickupDisplay": "unavailable",
                                        "pickupSearchQuote": "Ships in 2-3 weeks",
                                    },
                                },
                            }
                        ]
                    }
                }
            }
        }
        data = mock_json_response
    else:
        response_text = run_curl_command(query_string)

        if response_text is None:
            return

        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            print(
                "Could not decode JSON response from curl. "
                f"Received (first 200 chars): {response_text[:200]}..."
            )
            return
        except Exception as e:
            print(f"An unexpected error occurred during JSON parsing: {e}")
            return

    # --- Availability Parsing ---

    stores = (
        data.get("body", {})
        .get("content", {})
        .get("pickupMessage", {})
        .get("stores", [])
    )
    target_store = next(
        (s for s in stores if s.get("storeNumber") == STORE_ID), None
    )

    if not target_store:
        msg = f"Store ID {STORE_ID} (Saket, New Delhi) not found in the response."
        send_telegram_message(TELEGRAM_CHAT_ID, msg)
        print(msg)
        return

    availability_list = []
    products_to_alert = []

    for product in PRODUCTS:
        sku = product["sku"]
        name = product["name"]
        part_fulfillment = target_store.get("partsAvailability", {}).get(sku)

        if part_fulfillment:
            is_available_today = (
                part_fulfillment.get("pickupDisplay", "unavailable") == "available"
            )
            quote_text = part_fulfillment.get("pickupSearchQuote", "")

            is_available_tomorrow = False
            if (
                not is_available_today
                and quote_text
                and "tomorrow" in quote_text.lower()
            ):
                is_available_tomorrow = True

            is_available = is_available_today or is_available_tomorrow

            status_symbol = "✅" if is_available else "❌"
            pickup_quote_text = ""

            if is_available:
                products_to_alert.append(name)

            if is_available_today:
                pickup_quote_text = " - Available Today"
            elif is_available_tomorrow:
                pickup_quote_text = " - Available Tomorrow"
            elif quote_text:
                pickup_quote_text = f" - Expected: {quote_text}"

            availability_list.append(f"{status_symbol} {name}{pickup_quote_text}")
        else:
            availability_list.append(f"❓ {name} - Data Missing")

    # --- Telegram Notification Generation ---

    available_count = len(products_to_alert)

    message_header = f"Saket, New Delhi ({STORE_ID})"
    message_content = "\n".join(availability_list)

    if available_count > 0:
        status_header = "🎉 PICKUP AVAILABLE ALERT 🎉\n\n"
        status_summary = (
            f"{available_count} iPhone(s) available for pickup today or tomorrow!\n\n"
        )
    else:
        status_header = "📅 Apple Availability Status 📅\n\n"
        status_summary = "No immediate pickup found. See detailed forecast below.\n\n"

    final_message_to_send = (
        status_header
        + status_summary
        + message_header
        + "\n"
        + "--------------------------\n"
        + message_content
    )

    print("\n--- Availability Check Results ---")
    print(final_message_to_send)
    print("----------------------------------\n")

    # Send to group chat ONLY if items are available today/tomorrow
    if available_count > 0:
        send_telegram_message(TELEGRAM_CHAT_ID, final_message_to_send)
        print(
            f"Available items found. Full status update sent to chat ID {TELEGRAM_CHAT_ID}."
        )
    else:
        print(
            "No immediate availability found. Skipping Telegram notification to group chat."
        )


if __name__ == "__main__":
    check_apple_availability()
