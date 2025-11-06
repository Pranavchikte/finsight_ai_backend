import ssl
from celery import Celery

def create_celery_app(app):
    """
    Creates and configures a Celery app instance, linking it to the Flask app.
    Ensures compatibility with Celery 5.x+ by strictly using lowercase configuration keys.
    """
    # 1. Fetch settings from Flask config (loaded from Config.py/env vars)
    broker_url = app.config.get('BROKER_URL') or 'redis://127.0.0.1:6379/0'
    result_backend = app.config.get('RESULT_BACKEND') or 'redis://127.0.0.1:6379/0'

    # 2. Initialize Celery
    celery = Celery(
        app.import_name,
        broker=broker_url,
        backend=result_backend
    )

    # 3. Apply standard configuration using strictly lowercase keys
    # We DO NOT use celery.conf.update(app.config) here to avoid polluting
    # the standard Celery config with legacy uppercase keys (like BROKER_URL).
    celery.conf.update(
        broker_url=broker_url,
        result_backend=result_backend,
        broker_connection_retry_on_startup=True,
        # If you have other Celery-specific settings in Config.py,
        # map them manually here: e.g., task_serializer='json'
    )

    # 4. Auto-configure SSL for DigitalOcean Managed Valkey/Redis
    # If the URL starts with 'rediss://', we MUST tell Celery to ignore legitimate
    # certificate verification because DigitalOcean uses self-signed certs for these.
    if broker_url and broker_url.startswith('rediss://'):
        ssl_conf = {'ssl_cert_reqs': ssl.CERT_NONE}
        celery.conf.update(
            broker_use_ssl=ssl_conf,
            redis_backend_use_ssl=ssl_conf
        )

    # 5. Bind Celery tasks to Flask app context
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery