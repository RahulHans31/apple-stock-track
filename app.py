import os
from flask import Flask, jsonify
from api.checker import check_apple_availability

# Initialize Flask app
app = Flask(__name__)

# --- Render Health Check and Cron Trigger ---
@app.route('/', methods=['GET', 'POST'])
def trigger_check():
    """
    This endpoint is what cron-job.org will hit to start the availability check.
    """
    try:
        # Run the core logic from checker.py
        check_apple_availability()
        
        # Return a simple success response
        return jsonify({
            "status": "success",
            "message": "Apple availability check executed.",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Flask App Error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# --- Standard Flask Execution ---
if __name__ == '__main__':
    # Render automatically provides a PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
