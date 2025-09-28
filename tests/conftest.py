import json
import pytest
from app import create_app, mongo

@pytest.fixture(scope='module')
def test_client():
    # Create a Flask app configured for testing
    flask_app = create_app()
    flask_app.config.update({
        "TESTING": True,
        # Use a separate database for testing
        "MONGO_URI": "mongodb://localhost:27017/finsight_test_db"
    })

    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        # Establish an application context
        with flask_app.app_context():
            # Clean up the test database before and after the tests
            mongo.db.users.delete_many({})
            yield testing_client  # this is where the testing happens!
            mongo.db.users.delete_many({})

@pytest.fixture(scope='module')
def auth_token(test_client):
    """Fixture to register a user and get an auth token."""
    # Register a new user
    test_client.post('/api/auth/register',
                     data=json.dumps({
                         "email": "test-transactions@example.com",
                         "password": "password123"
                     }),
                     content_type='application/json')
    
    # Log in and get the token
    login_response = test_client.post('/api/auth/login',
                                     data=json.dumps({
                                         "email": "test-transactions@example.com",
                                         "password": "password123"
                                     }),
                                     content_type='application/json')
    
    token = json.loads(login_response.data)['access_token']
    yield token