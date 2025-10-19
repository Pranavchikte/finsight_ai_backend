from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import celery
from app.utils import success_response, error_response
from app.transactions.tasks import get_ai_summary_task

ai_bp = Blueprint('ai_bp', __name__)

@ai_bp.route('/summary', methods=['POST'])
@jwt_required()
def trigger_ai_summary():
    """
    Triggers the Celery task to generate an AI spending summary.
    Returns a task ID for the client to poll.
    """
    current_user_id = get_jwt_identity()
    task = get_ai_summary_task.delay(current_user_id)
    return success_response({"task_id": task.id}, status_code=202)


@ai_bp.route('/summary/result/<string:task_id>', methods=['GET'])
@jwt_required()
def get_ai_summary_result(task_id):
    """
    Fetches the result of the AI summary generation task.
    """
    task = get_ai_summary_task.AsyncResult(task_id)

    if task.state == 'PENDING':
        # Task is still in the queue
        response = {"status": "pending"}
        return success_response(response)
    elif task.state == 'SUCCESS':
        # Task completed successfully
        response = {"status": "completed", "summary": task.result}
        return success_response(response)
    elif task.state != 'FAILURE':
        # Task is in progress (e.g., 'STARTED', 'RETRY')
        response = {"status": "processing"}
        return success_response(response)
    else:
        # Task failed
        return error_response("Failed to generate AI summary. Please try again later.", 500)