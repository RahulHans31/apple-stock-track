import requests
import os
import json
from urllib.parse import urlencode
from datetime import datetime, timedelta

# --- Configuration (Kept as is for environment variable loading) ---
# Set this to False for LIVE operation (checking the real Apple API)
MOCK_AVAILABILITY_MODE = False

# Target store and product list based on your request and image
STORE_ID = 'R756'  # Saket, New Delhi (R756)
PRODUCTS = [
    {"name": "iPhone 17 256GB White", "sku": "MG6K4HN/A"},
    {"name": "iPhone 17 256GB Black", "sku": "MG6J4HN/A"},
    {"name": "iPhone 17 256GB Mist Blue", "sku": "MG6L4HN/A"},
    {"name": "iPhone 17 256GB Sage", "sku": "MG6N4HN/A"},
    {"name": "iPhone 17 256GB Lavender", "sku": "MG6M4HN/A"},
]

# Apple API Request details
APPLE_API_URL = "https://www.apple.com/in/shop/fulfillment-messages"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://www.apple.com/in/shop/buy-iphone/iphone-17/6.3%22-display-256gb-white",
    "x-skip-redirect": "true",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=4",
    "TE": "trailers",
}

# --- Utility Functions ---

def send_telegram_message(chat_id, message, is_personal=False):
    """
    Sends a message to the specified Telegram chat/user using plain text (no Markdown).
    """
    # Load env variables for utility functions too
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8428862886:AAF0yZfs2z1b8UHkximmvobIbN5uWo67Xk8')
    
    if not TELEGRAM_BOT_TOKEN:
        print("Telegram token is not set. Cannot send message.")
        return

    tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
    }

    try:
        response = requests.post(tg_url, json=payload, timeout=10)
        
        if not response.ok:
            response_json = response.json()
            error_description = response_json.get('description', 'No description provided')
            print(f"FAILURE: Telegram API Error. Status: {response.status_code}. Details: {error_description}")
        
        response.raise_for_status() 

    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")


def build_api_query():
    """Builds the full query parameters for the Apple API call."""
    params = {
        'fae': 'true',
        'little': 'false',
        'mts.0': 'regular',
        'mts.1': 'sticky',
        'fts': 'true'
    }
    # Add all product SKUs to the query
    for i, product in enumerate(PRODUCTS):
        params[f'parts.{i}'] = product['sku']

    return params

# --- Main Logic ---

def check_apple_availability_and_get_json():
    """
    Fetches availability, sends urgent Telegram alerts on cookie failure,
    and returns structured availability data for the Flask endpoint.
    """
    print("Starting Apple availability check for JSON endpoint...")

    # Load environment variables/fallbacks
    TELEGRAM_PERSONAL_ID = os.environ.get('TELEGRAM_PERSONAL_ID', '-5015233395') 
    APPLE_COOKIES = os.environ.get('APPLE_COOKIES', 
        "dssid2=f0ec55d9-ed76-43b4-b778-a9af0364ebd3; dssf=1; as_sfa=Mnxpbnxpbnx8ZW5fSU58Y29uc3VtZXJ8aW50ZXJuZXR8MHwwfDE; pxro=1; as_uct=0; shld_bt_m=XP3h4P9zCIGtgKK5RKAggQ|1763143489|lvQnJl5nCuxX7e7pTDT0Ow|A3bUZjRCFmuxFzoc9TXGAZ5KqjA; as_pcts=vJcd6BAai9s_aVNxzU2ZuHqpuQSRs5FWe0QY:_U5mGx_jrQERHLq0MRyWpJZKav6:ZwCr0EEwtjNOhvkxrsK2+oMbKCTFkv9C01Zv4dhA3ycH; as_dc=ucp5; geo=IN; as_atb=1.0|MjAyNS0xMS0xNCAwODowNDo0OA|dd04db0a750780947d9b42ac64b463e0d10cd074; s_fid=4E20B634B794BB49-0CEF6989873D44DE; s_cc=true; as_rumid=70f9af1f-6756-4a00-8017-29b878212a22; shld_bt_ck=V9PgFaoFvN1x58xgAqUTHA|1763140456|8gn4nkPIO7DOo5F9D2TBCBYuEdgNLuz5-EoVEguxRm50TS6-RTXa6WlVqq-jF_IRwP-q73RI3y2v7ld2xoJe3gAsisEiQbDKpaJtm1g0CBoKPDyjaJXw0f8VDKOmP6ybjWmzgQr89A1cTxCw-3vCDxaBiHNGPWRZWNZGR_4u2r-R9yugq-hP3vdOLWpgYyKCt_eOo12ZtyAmRmi4Bcea-4QMyfZA4qy95saX6zZhWsnTyg4w8VljGCBbfPp_pxhqGc-leJiG0apExUP1F4Wj6Qy6mxAyRXFZU8CnIKYw6fmjdb7GUVNgnZ5mNgIyjOkukLCyN9RL4LQ_WI6OK-I_ZA|T1JJrg-LSRANleXKYwAfnBugSns; sh_spksy=.; as_gloc=0397e3bd0db7a25e4e2f6685cfa6ba6c534f7b09c675cdb72b9536340db85b8f243e3a676cfcafab4413e9bceff8fbefc333856acc0493a4770075a0aadb2b4ebccaaf1ddfc153b2e939e57e79839b31a50f5ae3c8b71761bbdbdce99166c18d")

    if not APPLE_COOKIES:
        error_msg = "FATAL: APPLE_COOKIES environment variable is not set. Cannot proceed with checking."
        send_telegram_message(TELEGRAM_PERSONAL_ID, error_msg, is_personal=True)
        return {"status": "error", "message": "Configuration error: APPLE_COOKIES not set."}, 500

    # Set dynamic Cookie header
    request_headers = HEADERS.copy()
    request_headers['Cookie'] = APPLE_COOKIES
    
    # Build the full URL with all product parts
    query_params = build_api_query()
    full_url = APPLE_API_URL + '?' + urlencode(query_params)

    data = {}

    if MOCK_AVAILABILITY_MODE:
        # MOCK MODE (Use for testing only)
        # We need a proper JSON structure for the parsing logic to work
        mock_json_response = {
            "body": {"content": {"pickupMessage": {"stores": [{
                "storeNumber": STORE_ID,
                "storeName": "Saket (MOCK)",
                "partsAvailability": {
                    "MG6K4HN/A": {"pickupDisplay": "ships-to-store", "pickupSearchQuote": "Available 20 Dec"},
                    "MG6J4HN/A": {"pickupDisplay": "unavailable", "pickupSearchQuote": "Available Fri 3 Dec"},
                    "MG6L4HN/A": {"pickupDisplay": "available", "pickupSearchQuote": "Available Today"}, 
                    "MG6N4HN/A": {"pickupDisplay": "ships-to-store", "pickupSearchQuote": "Available Tomorrow"},
                    "MG6M4HN/A": {"pickupDisplay": "unavailable", "pickupSearchQuote": "Ships in 2-3 weeks"}
                }
            }]}}}
        }
        data = mock_json_response
    else:
        try:
            response = requests.get(full_url, headers=request_headers, timeout=30)
            
            # --- Critical Check: Cookie Expiration / Auth Failure ---
            if response.status_code in [401, 403, 541] or 'please sign in' in response.text.lower() or 'apple.com/shop/login' in response.text.lower():
                cookie_alert = (
                    f"🚨 COOKIE EXPIRATION ALERT 🚨\n\n"
                    f"The Apple session cookies have likely expired or are invalid. (Status Code: {response.status_code})\n\n"
                    f"Please obtain a new `Cookie` value and update the `APPLE_COOKIES` environment variable."
                )
                print(cookie_alert)
                send_telegram_message(TELEGRAM_PERSONAL_ID, cookie_alert)
                return {"status": "error", "message": "Authentication failed. Cookies expired. Alert sent to personal chat."}, response.status_code

            response.raise_for_status() 
            data = response.json()
        
        except requests.exceptions.HTTPError as e:
            return {"status": "error", "message": f"HTTP Error during API call: {e}"}, 500
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Network/Request Error: {e}"}, 500
        except json.JSONDecodeError:
            return {"status": "error", "message": f"Could not decode JSON response. Received: {response.text[:200]}..."}, 500
        except Exception as e:
            return {"status": "error", "message": f"An unexpected error occurred: {e}"}, 500
    
    # --- Availability Parsing for JSON Response ---
    
    stores = data.get('body', {}).get('content', {}).get('pickupMessage', {}).get('stores', [])
    target_store = next((s for s in stores if s.get('storeNumber') == STORE_ID), None)
    
    if not target_store:
        return {"status": "error", "message": f"Store ID {STORE_ID} not found in the response."}, 404

    store_name = target_store.get('storeName', 'Unknown Store')
    results = []
    total_urgent_available = 0
    
    # Iterate through all requested parts to build the JSON result
    for product in PRODUCTS:
        sku = product['sku']
        name = product['name']
        part_fulfillment = target_store.get('partsAvailability', {}).get(sku)
        
        if part_fulfillment:
            
            is_available_today = part_fulfillment.get('pickupDisplay', 'unavailable') == 'available'
            quote_text = part_fulfillment.get('pickupSearchQuote', '')
            is_available_tomorrow = "tomorrow" in quote_text.lower()
            
            is_urgent_available = is_available_today or is_available_tomorrow
            if is_urgent_available:
                total_urgent_available += 1
                
            # Determine the exact pickup quote/date for the JSON output
            pickup_status = "Available Today" if is_available_today else \
                            "Available Tomorrow" if is_available_tomorrow else \
                            quote_text
            
            results.append({
                "sku": sku,
                "product_name": name,
                "is_available_today_or_tomorrow": is_urgent_available,
                "availability_status": part_fulfillment.get('pickupDisplay', 'unavailable'),
                "pickup_date_or_quote": pickup_status 
            })
        else:
             results.append({"sku": sku, "product_name": name, "availability_status": "data_missing"})
            
    # Return the structured data for the Flask endpoint
    return {
        "status": "ok", 
        "store": store_name, 
        "store_id": STORE_ID,
        "total_urgent_available": total_urgent_available, 
        "products": results,
        "checked_at": datetime.now().isoformat()
    }, 200

# The handler and __main__ blocks are removed from here as they belong in app.py
