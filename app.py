import os
from flask import Flask, jsonify
from datetime import datetime
# This import assumes checker.py (your logic file) is in the root directory
from api.checker import check_apple_availability_and_get_json

# Initialize Flask app
app = Flask(__name__)

# --- Render Health Check and Cron Trigger ---
@app.route('/', methods=['GET', 'POST'])
def trigger_check():
    """
    This endpoint is what cron-job.org will hit to start the availability check
    and returns the result as JSON.
    """
    
    # Run the core logic and capture the returned JSON data and HTTP status code
    data, status_code = check_apple_availability_and_get_json()
    
    # Return the JSON data directly with the appropriate HTTP status code
    return jsonify(data), status_code

# --- Standard Flask Execution ---
if __name__ == '__main__':
    # Render automatically provides a PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
