from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from pydantic import ValidationError
from datetime import datetime

from app import mongo
from app.utils import success_response, error_response
from .schemas import BudgetSchema

budgets_bp = Blueprint('budgets_bp', __name__)

@budgets_bp.route('/', methods=['POST'])
@jwt_required()
def create_budget():
    """Creates a new budget for the user for a specific category and month."""
    current_user_id = get_jwt_identity()
    user_id = ObjectId(current_user_id)
    
    try:
        data = BudgetSchema(**request.get_json())
    except ValidationError as e:
        return error_response(e.errors(), 400)

    # FIX #4: Budget Amount Validation
    if data.limit <= 0:
        return error_response("Budget limit must be greater than zero", 400)
    if data.limit > 10000000:
        return error_response("Budget limit too large. Maximum is ₹10,000,000", 400)
    # Round to 2 decimal places
    data.limit = round(data.limit, 2)

    # FIX #10: Validate month/year not in past or too far in future
    current_date = datetime.utcnow()
    current_month = current_date.month
    current_year = current_date.year
    
    # Allow current month and next month only
    if data.year < current_year:
        return error_response("Cannot create budgets for past years", 400)
    
    if data.year == current_year and data.month < current_month:
        return error_response("Cannot create budgets for past months", 400)
    
    if data.year > current_year + 1:
        return error_response("Cannot create budgets more than 1 year in advance", 400)
    
    if data.year == current_year + 1 and data.month > current_month:
        return error_response("Cannot create budgets more than 1 year in advance", 400)

    # Check if a budget for this category/month/year already exists
    existing_budget = mongo.db.budgets.find_one({
        "user_id": user_id,
        "category": data.category,
        "month": data.month,
        "year": data.year
    })

    if existing_budget:
        return error_response(f"A budget for {data.category} in {data.month}/{data.year} already exists.", 409)

    budget_doc = {
        "user_id": user_id,
        "category": data.category,
        "limit": data.limit,
        "month": data.month,
        "year": data.year,
        "created_at": datetime.utcnow()
    }
    
    result = mongo.db.budgets.insert_one(budget_doc)
    
    # Return the newly created document
    new_budget = mongo.db.budgets.find_one({"_id": result.inserted_id})
    new_budget['_id'] = str(new_budget['_id'])
    new_budget['user_id'] = str(new_budget['user_id'])
    
    return success_response(new_budget, 201)



@budgets_bp.route('/', methods=['GET'])
@jwt_required()
def get_budgets_with_spending():
    """
    Fetches all budgets for the current month and enriches them with the
    current spending data for each corresponding category.
    """
    current_user_id = get_jwt_identity()
    user_id = ObjectId(current_user_id)
    
    now = datetime.utcnow()
    current_month = now.month
    current_year = now.year

    # This is a MongoDB Aggregation Pipeline. It's like a multi-step query.
    pipeline = [
        # 1. Match budgets for the current user, month, and year.
        {
            "$match": {
                "user_id": user_id,
                "month": current_month,
                "year": current_year
            }
        },
        # 2. Join with the 'transactions' collection.
        {
            "$lookup": {
                "from": "transactions",
                "let": {"budget_category": "$category", "budget_month": "$month", "budget_year": "$year"},
                "pipeline": [
                    # Pipeline to run on the transactions collection
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$user_id", user_id]},
                                    {"$eq": ["$status", "completed"]},
                                    {"$eq": ["$category", "$$budget_category"]},
                                    {"$eq": [{"$month": "$date"}, "$$budget_month"]},
                                    {"$eq": [{"$year": "$date"}, "$$budget_year"]}
                                ]
                            }
                        }
                    }
                ],
                "as": "spent_transactions" # Name for the array of matching transactions
            }
        },
        # 3. Calculate the sum of spent transactions.
        {
            "$addFields": {
                "current_spend": {"$sum": "$spent_transactions.amount"}
            }
        },
        # 4. Clean up the response.
        {
            "$project": {
                "spent_transactions": 0, # Don't include the full list of transactions
            }
        }
    ]

    result = list(mongo.db.budgets.aggregate(pipeline))

    # Convert BSON types to strings for JSON response
    for budget in result:
        budget['_id'] = str(budget['_id'])
        budget['user_id'] = str(budget['user_id'])

    return success_response(result)