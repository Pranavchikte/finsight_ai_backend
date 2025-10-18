from flask import jsonify

def success_response(data, status_code=200):
  
    response = {
        "status": "success",
        "data": data
    }
    return jsonify(response), status_code

def error_response(message, status_code):
    
    status = "fail" if 400 <= status_code < 500 else "error"
    
    response_data_key = "details" if isinstance(message, dict) or isinstance(message, list) else "message"

    response = {
        "status": status,
        "data": {response_data_key: message}
    }
    return jsonify(response), status_code