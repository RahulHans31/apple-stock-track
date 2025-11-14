import requests
import json
from urllib.parse import urlencode
from datetime import datetime, timedelta

# --- HARDCODED Configuration (All values provided by user) ---

# Set this to False for LIVE operation
MOCK_AVAILABILITY_MODE = False


# Telegram Credentials
TELEGRAM_BOT_TOKEN = '8428862886:AAF0yZfs2z1b8UHkximmvobIbN5uWo67Xk8'
TELEGRAM_CHAT_ID = '-5015233395'  # Group ID for status notifications
TELEGRAM_PERSONAL_ID = '-5015233395' # Personal ID for urgent cookie alerts (using Group ID as fallback)

# Apple Session Cookie (MUST be updated manually in this file when expired)
APPLE_COOKIES = (
    "dssid2=f0ec55d9-ed76-43b4-b778-a9af0364ebd3; dssf=1; as_sfa=Mnxpbnxpbnx8ZW5fSU58Y29uc3VtZXJ8aW50ZXJuZXR8MHwwfDE; pxro=1; as_uct=0; shld_bt_m=XP3h4P9zCIGtgKK5RKAggQ^|1763149843^|FyWtXTLck7Hga-RhiEM4JQ^|XDacKFB1tY_0EHNN-AvITAneDTo; as_pcts=vJcd6BAai9s_aVNxzU2ZuHqpuQSRs5FWe0QY:_U5mGx_jrQERHLq0MRyWpJZKav6:ZwCr0EEwtqNOhvkxrsK2+oMbKCTFkv9C1m1Zv4dhA3ycH; as_dc=ucp5; geo=IN; as_atb=1.0^|MjAyNS0xMS0xNCAwOTo1MDo0Mw^|3b37ab7e63e7ef54e08ce5e53b1c1c8f1862ad8e; s_cc=true; as_rumid=70f9af1f-6756-4a00-8017-29b878212a22; as_gloc=0397e3bd0db7a25e4e2f6685cfa6ba6c534f7b09c675cdb72b9536340db85b8f243e3a676cfcafab4413e9bceff8fbefc333856acc0493a4770075a0aadb2b4ebccaaf1ddfc153b2e939e57e79839b31a50f5ae3c8b71761bbdbdce99166c18d; s_sq=^%^5B^%^5BB^%^5D^%^5D; s_fid=4047AC034C9040AF-3F65683723B03B0A; shld_bt_ck=nHqswYbGmDfKJkoIm42TuA^|1763149820^|GiBaACLmczEGywoY8DeJ-vtvjB5OGVX8j1FjI5r85eCGGk3EbFzE2DCzp-b9G0yLErq0vpAT-bHHf5BA1b0l8MpaXK-XIjS118fFPtNBDt__8vVYp7rapfDe55BA9keoJF3sOhSYI4616W_2cpWl6Th46MZg1FscLd-mCr4u1W12pzKoF_-nSLucxhs7HZqfzFl0KFcbh6UgWBojhVOsRZ0Wr-psoimBxxsSwFcVMuMfBVyiz1eK_H3fFBhYw_Ok3Dh-_eadFSBnpiBGN7pkk7l-CCnk0XWuj5r8jQfTQFPPa0rDAso3gbych_Zru-luam7Y1WYI93jRL4ngy1lG3A^|MDlC4X5p4ojQi_s8w74OOqjJbo8"
)

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

def send_telegram_message(chat_id, message):
    """
    Sends a message to the specified Telegram chat/user using plain text (no Markdown).
    """
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

def check_apple_availability():
    """Fetches availability and sends Telegram notifications."""
    print("Starting Apple availability check...")

    # Set dynamic Cookie header
    request_headers = HEADERS.copy()
    request_headers['Cookie'] = APPLE_COOKIES
    
    # Build the full URL with all product parts
    query_params = build_api_query()
    full_url = APPLE_API_URL + '?' + urlencode(query_params)

    data = {}

    if MOCK_AVAILABILITY_MODE:
        print("--- MOCK MODE ACTIVE: Skipping live API call. ---")
        # Simulated response for testing purposes
        mock_json_response = {
            "body": {"content": {"pickupMessage": {"stores": [{
                "storeNumber": STORE_ID,
                "storeName": "Saket (MOCK)",
                "partsAvailability": {
                    "MG6K4HN/A": {"pickupDisplay": "ships-to-store", "pickupSearchQuote": "Available Fri 3 Dec"},
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
                    f"Please obtain a new `Cookie` value from your browser and update the `APPLE_COOKIES` constant in checker.py immediately."
                )
                print(cookie_alert)
                # Send urgent alert to personal ID
                send_telegram_message(TELEGRAM_PERSONAL_ID, cookie_alert)
                return

            response.raise_for_status()
            data = response.json()
        
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error during API call: {e}")
            return
        except requests.exceptions.RequestException as e:
            print(f"Network/Request Error: {e}")
            return
        except json.JSONDecodeError:
            print(f"Could not decode JSON response. Received: {response.text[:200]}...")
            return
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return
    
    # --- Availability Parsing ---
    
    stores = data.get('body', {}).get('content', {}).get('pickupMessage', {}).get('stores', [])
    target_store = next((s for s in stores if s.get('storeNumber') == STORE_ID), None)
    
    if not target_store:
        msg = f"Store ID {STORE_ID} (Saket, New Delhi) not found in the response."
        send_telegram_message(TELEGRAM_CHAT_ID, msg)
        print(msg)
        return

    availability_list = []
    products_to_alert = []
    
    for product in PRODUCTS:
        sku = product['sku']
        name = product['name']
        part_fulfillment = target_store.get('partsAvailability', {}).get(sku)
        
        if part_fulfillment:
            is_available_today = part_fulfillment.get('pickupDisplay', 'unavailable') == 'available'
            quote_text = part_fulfillment.get('pickupSearchQuote', '')
            
            is_available_tomorrow = False
            if not is_available_today and quote_text and "tomorrow" in quote_text.lower():
                is_available_tomorrow = True

            is_available = is_available_today or is_available_tomorrow
            
            status_symbol = "✅" if is_available else "❌"
            pickup_quote_text = ""
            
            if is_available:
                products_to_alert.append(name)
            
            if is_available_today:
                pickup_quote_text = " - Available Today"
            elif is_available_tomorrow:
                pickup_quote_text = f" - Available Tomorrow"
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
        status_header = f"🎉 PICKUP AVAILABLE ALERT 🎉\n\n"
        status_summary = f"{available_count} iPhone(s) available for pickup today or tomorrow!\n\n"
    else:
        status_header = f"📅 Apple Availability Status 📅\n\n"
        status_summary = f"No immediate pickup found. See detailed forecast below.\n\n"
    
    final_message_to_send = (
        status_header + 
        status_summary +
        message_header + "\n" +
        "--------------------------\n" +
        message_content
    )
    
    print("\n--- Availability Check Results ---")
    print(final_message_to_send) 
    print("----------------------------------\n")
    
    # Send the full status update to the Telegram group chat
    send_telegram_message(TELEGRAM_CHAT_ID, final_message_to_send)
    print(f"Full status update sent to chat ID {TELEGRAM_CHAT_ID}.")

if __name__ == "__main__":
    check_apple_availability()
