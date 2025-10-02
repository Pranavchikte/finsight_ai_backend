
from app import create_app

flask_app = create_app()
from app import celery

# DEBUG: Print what broker Celery is actually using
# print("="*50)
# print(f"Broker URL: {celery.conf.broker_url}")
# print(f"Result Backend: {celery.conf.result_backend}")
# print("="*50)