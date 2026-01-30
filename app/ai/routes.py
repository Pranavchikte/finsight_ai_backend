from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone

from app import celery, mongo
from app.utils import success_response, error_response
from app.transactions.tasks import get_ai_summary_task
from bson import ObjectId

ai_bp = Blueprint('ai_bp', __name__)

# ADDED: Track active AI summary generations per user (FIX #24 - spam prevention)
active_summary_tasks = {}  # {user_id: {"task_id": str, "started_at": datetime}}

@ai_bp.route('/summary', methods=['POST'])
@jwt_required()
def trigger_ai_summary():
    """
    Triggers the Celery task to generate an AI spending summary.
    Returns a task ID for the client to poll.
    """
    current_user_id = get_jwt_identity()
    
    # ADDED: Check if user already has an active summary generation (FIX #24)
    if current_user_id in active_summary_tasks:
        existing_task = active_summary_tasks[current_user_id]
        task_result = get_ai_summary_task.AsyncResult(existing_task["task_id"])
        
        # Only block if task is actually still running
        if task_result.state in ['PENDING', 'STARTED', 'RETRY']:
            return error_response("Summary generation already in progress. Please wait.", 429)
        else:
            # Clean up completed/failed task
            active_summary_tasks.pop(current_user_id, None)
    
    task = get_ai_summary_task.delay(current_user_id)
    
    # ADDED: Track this task (FIX #24)
    active_summary_tasks[current_user_id] = {
        "task_id": task.id,
        "started_at": datetime.now(timezone.utc)
    }
    
    return success_response({"task_id": task.id}, status_code=202)


@ai_bp.route('/summary/result/<string:task_id>', methods=['GET'])
@jwt_required()
def get_ai_summary_result(task_id):
    """
    Fetches the result of the AI summary generation task.
    """
    current_user_id = get_jwt_identity()
    task = get_ai_summary_task.AsyncResult(task_id)

    if task.state == 'PENDING':
        response = {"status": "pending"}
        return success_response(response)
    elif task.state == 'SUCCESS':
        # ADDED: Clean up tracking dict when task completes (FIX #24)
        active_summary_tasks.pop(current_user_id, None)
        response = {"status": "completed", "summary": task.result}
        return success_response(response)
    elif task.state != 'FAILURE':
        response = {"status": "processing"}
        return success_response(response)
    else:
        # ADDED: Clean up tracking dict on failure (FIX #24)
        active_summary_tasks.pop(current_user_id, None)
        return error_response("Failed to generate AI summary. Please try again later.", 500)