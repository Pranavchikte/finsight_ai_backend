# tests/test_transactions.py
import json

def test_add_manual_transaction(test_client, auth_token):
    """
    GIVEN a valid auth token
    WHEN the '/api/transactions/' endpoint is posted to with valid manual data
    THEN check for a '201 Created' status and correct data in the response
    """
    headers = {
        'Authorization': f'Bearer {auth_token}'
    }
    response = test_client.post('/api/transactions/',
                                headers=headers,
                                data=json.dumps({
                                    "mode": "manual",
                                    "amount": 550.75,
                                    "category": "Shopping",
                                    "description": "New headphones"
                                }),
                                content_type='application/json')
    
    assert response.status_code == 201
    response_data = json.loads(response.data)
    assert response_data['amount'] == 550.75
    assert response_data['category'] == "Shopping"

def test_get_transactions_unauthorized(test_client):
    """
    GIVEN a Flask application
    WHEN the '/api/transactions/' endpoint is requested (GET) without a token
    THEN check for a '401 Unauthorized' status code
    """
    response = test_client.get('/api/transactions/')
    assert response.status_code == 401