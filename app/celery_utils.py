# In app/celery_utils.py

from celery import Celery

def create_celery_app(app):
    """
    Creates and configures a Celery app instance, linking it to the Flask app.
    """
    # --- FIX: Prioritize uppercase, keep lowercase as fallback ---
    broker_url = app.config.get('BROKER_URL') or app.config.get('broker_url') or 'redis://127.0.0.1:6379/0'
    result_backend = app.config.get('RESULT_BACKEND') or app.config.get('result_backend') or 'redis://127.0.0.1:6379/0'
    # -----------------------------------------------------------
    
    celery = Celery(
        app.import_name,
        broker=broker_url,
        backend=result_backend
    )
    
    # Explicitly set Celery config using the resolved URLs
    celery.conf.broker_url = broker_url
    celery.conf.result_backend = result_backend
    
    # --- FIX: Use consistent uppercase name ---
    celery.conf.broker_connection_retry_on_startup = app.config.get('BROKER_CONNECTION_RETRY_ON_STARTUP', True)
    # ------------------------------------------

    # Update with any other Flask config (this line might be redundant now but is harmless)
    celery.conf.update(app.config) 

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery