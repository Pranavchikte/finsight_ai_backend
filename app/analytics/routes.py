from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime, timezone

from app import mongo
from app.utils import success_response, error_response

analytics_bp = Blueprint('analytics_bp', __name__)

@analytics_bp.route('/report', methods=['GET'])
@jwt_required()
def get_analytics_report():
    """
    Generates a comprehensive analytics report for a given date range.
    """
    current_user_id = get_jwt_identity()
    user_id = ObjectId(current_user_id)

    # Get date range from query parameters, default to the last 30 days
    try:
        end_date = datetime.now(timezone.utc)
        start_date_str = request.args.get('start_date')
        if not start_date_str:
            # Default to the first day of the current month if not provided
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = datetime.fromisoformat(start_date_str).replace(tzinfo=timezone.utc)
    except ValueError:
        return error_response("Invalid date format. Use ISO 8601 format.", 400)

    # This is the main aggregation pipeline
    pipeline = [
        # Stage 1: Filter transactions by user and date range
        {
            "$match": {
                "user_id": user_id,
                "status": "completed",
                "date": {"$gte": start_date, "$lte": end_date}
            }
        },
        # Stage 2: Use $facet to run multiple aggregations in parallel
        {
            "$facet": {
                # Aggregation 1: Total spending in the range
                "totalSpendInRange": [
                    {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
                ],
                # Aggregation 2: Spending breakdown by category
                "spendingByCategory": [
                    {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}},
                    {"$project": {"category": "$_id", "total": 1, "_id": 0}},
                    {"$sort": {"total": -1}}
                ],
                # Aggregation 3: Spending trend over time (by day)
                "spendingOverTime": [
                    {
                        "$group": {
                            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$date"}},
                            "total": {"$sum": "$amount"}
                        }
                    },
                    {"$project": {"date": "$_id", "total": 1, "_id": 0}},
                    {"$sort": {"date": 1}}
                ]
            }
        }
    ]

    result = list(mongo.db.transactions.aggregate(pipeline))

    # The result will be a list with one document, let's format it nicely
    if not result:
        return error_response("No data found for the given range.", 404)

    report_data = result[0]
    
    # Extract and format the final response
    total_spend = report_data['totalSpendInRange'][0]['total'] if report_data['totalSpendInRange'] else 0
    
    final_report = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "totalSpendInRange": total_spend,
        "spendingByCategory": report_data['spendingByCategory'],
        "spendingOverTime": report_data['spendingOverTime']
    }

    return success_response(final_report)