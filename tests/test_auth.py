# tests/test_auth.py
import json

def test_registration(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/api/auth/register' endpoint is posted to (POST)
    THEN check that a '201 Created' status code is returned
    """
    response = test_client.post('/api/auth/register',
                                data=json.dumps({
                                    "email": "test@example.com",
                                    "password": "password123"
                                }),
                                content_type='application/json')
    assert response.status_code == 201

def test_duplicate_registration(test_client):
    """
    GIVEN a user that is already registered
    WHEN the '/api/auth/register' endpoint is posted to again with the same email
    THEN check that a '409 Conflict' status code is returned
    """
    # First, register the user (we assume this works from the test above)
    test_client.post('/api/auth/register',
                     data=json.dumps({
                         "email": "another@example.com",
                         "password": "password123"
                     }),
                     content_type='application/json')
    
    # Now, try to register the same user again
    response = test_client.post('/api/auth/register',
                                data=json.dumps({
                                    "email": "another@example.com",
                                    "password": "password123"
                                }),
                                content_type='application/json')
    assert response.status_code == 409

def test_login(test_client):
    """
    GIVEN a registered user
    WHEN the '/api/auth/login' endpoint is posted to with correct credentials
    THEN check for a '200 OK' and a valid access_token in the response
    """
    # First, register a user to test login with
    test_client.post('/api/auth/register',
                     data=json.dumps({
                         "email": "loginuser@example.com",
                         "password": "password123"
                     }),
                     content_type='application/json')

    # Now, log in
    response = test_client.post('/api/auth/login',
                                data=json.dumps({
                                    "email": "loginuser@example.com",
                                    "password": "password123"
                                }),
                                content_type='application/json')
    
    assert response.status_code == 200
    response_data = json.loads(response.data)
    assert "access_token" in response_data