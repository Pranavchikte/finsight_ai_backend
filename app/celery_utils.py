import ssl
from celery import Celery

def create_celery_app(app):
    """
    Creates and configures a Celery app instance, linking it to the Flask app.
    """
    # Prioritize uppercase config, fallback to lowercase, then default local Redis
    broker_url = app.config.get('BROKER_URL') or app.config.get('broker_url') or 'redis://127.0.0.1:6379/0'
    result_backend = app.config.get('RESULT_BACKEND') or app.config.get('result_backend') or 'redis://127.0.0.1:6379/0'

    celery = Celery(
        app.import_name,
        broker=broker_url,
        backend=result_backend
    )

    # Load standard Flask config first
    celery.conf.update(app.config)

    # Explicitly ensure core settings are set
    celery.conf.broker_url = broker_url
    celery.conf.result_backend = result_backend
    celery.conf.broker_connection_retry_on_startup = app.config.get('BROKER_CONNECTION_RETRY_ON_STARTUP', True)

    # --- SSL FIX FOR DIGITALOCEAN VALKEY/REDIS ---
    # If the URL is secure (rediss://), automatically inject the required SSL settings.
    # This fixes the "Invalid SSL Certificate Requirements Flag" error.
    if broker_url and broker_url.startswith('rediss://'):
        celery.conf.update(
            broker_use_ssl={
                'ssl_cert_reqs': ssl.CERT_NONE
            },
            redis_backend_use_ssl={
                'ssl_cert_reqs': ssl.CERT_NONE
            }
        )
    # ---------------------------------------------

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery