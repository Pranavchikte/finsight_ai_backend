from celery import Celery

def create_celery_app(app):
    """
    Creates and configures a Celery app instance, linking it to the Flask app.
    """
    broker_url = app.config.get('BROKER_URL') or app.config.get('broker_url') or 'redis://127.0.0.1:6379/0'
    result_backend = app.config.get('RESULT_BACKEND') or app.config.get('result_backend') or 'redis://127.0.0.1:6379/0'
    
    celery = Celery(
        app.import_name,
        broker=broker_url,
        backend=result_backend
    )
    
    # Explicitly set Celery config
    celery.conf.broker_url = broker_url
    celery.conf.result_backend = result_backend
    celery.conf.broker_connection_retry_on_startup = True
    
    # Update with any other Flask config
    celery.conf.update(app.config)

    # This boilerplate ensures that tasks run within the Flask application context,
    # so they have access to extensions like our database connection.
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
