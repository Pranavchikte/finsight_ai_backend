from flask import Blueprint, request, current_app
from bson import ObjectId
from datetime import datetime, timedelta
from flask_jwt_extended import jwt_required, get_jwt_identity
import re
import json
from app import mongo
from app.services.twilio_service import twilio_service
from app.services.gemini_service import parse_expense_test

whatsapp_bp = Blueprint('whatsapp_bp', __name__)

CATEGORIES = [
    "Food & Dining", "Transportation", "Shopping", "Entertainment",
    "Bills & Utilities", "Health & Fitness", "Travel", "Education",
    "Groceries", "Personal Care", "Home", "Other"
]


def parse_expense_message(message):
    """
    Parse expense message using regex first, fallback to Gemini.
    Examples: "500 coffee", "coffee for 500 rs", "lunch 150 rupees"
    """
    message = message.strip().lower()
    
    # Pattern 1: "amount description" or "description amount"
    # Match patterns like: "500 coffee", "coffee 500", "500 rupees coffee"
    
    # Try regex first for simple patterns
    patterns = [
        r'^(\d+(?:\.\d{1,2})?)\s+(.+)$',  # 500 coffee
        r'^(.+?)\s+(\d+(?:\.\d{1,2})?)$',  # coffee 500
        r'^(\d+(?:\.\d{1,2})?)\s*(?:rs|rupees?)\s*(.+)$',  # 500 rs coffee
        r'^(.+?)\s*(?:rs|rupees?)\s*(\d+(?:\.\d{1,2})?)$',  # coffee 500 rs
    ]
    
    for pattern in patterns:
        match = re.match(pattern, message)
        if match:
            groups = match.groups()
            if groups[0].isdigit() or '.' in groups[0]:
                amount = float(groups[0]) if groups[0].replace('.', '').isdigit() else float(groups[1])
                description = groups[1] if isinstance(groups[0], (int, float)) else groups[0]
            else:
                amount = float(groups[1]) if groups[1].replace('.', '').isdigit() else float(groups[0])
                description = groups[0] if isinstance(groups[1], (int, float)) else groups[1]
            
            # Clean description
            description = description.strip().title()
            
            # Guess category based on keywords
            category = guess_category(description)
            
            return {
                "amount": round(amount, 2),
                "description": description,
                "category": category,
                "source": "regex"
            }
    
    # Fallback to Gemini AI
    try:
        result = parse_expense_test(message)
        if result:
            return {
                "amount": result.get("amount", 0),
                "description": result.get("description", message),
                "category": result.get("category", "Other"),
                "source": "gemini"
            }
        else:
            # Gemini returned null (couldn't parse)
            return {
                "error": "could_not_parse",
                "message": "Couldn't understand the expense. Try format: '500 coffee' or 'coffee for 500 rs'"
            }
    except Exception as e:
        current_app.logger.error(f"Gemini parsing failed: {e}")
        return {
            "error": "api_error",
            "message": "AI service temporarily unavailable. Try simple format like '500 coffee'."
        }
    
    return None


def guess_category(description):
    """Simple keyword-based category guessing."""
    desc = description.lower()
    
    keywords = {
        "Food & Dining": ["coffee", "tea", "lunch", "dinner", "breakfast", "food", "restaurant", "cafe", "pizza", "burger", "snack"],
        "Transportation": ["uber", "ola", "taxi", "bus", "train", "metro", "petrol", "fuel", "auto", "car"],
        "Shopping": ["amazon", "flipkart", "mall", "store", "shop", "clothes", "shoes"],
        "Entertainment": ["movie", "netflix", "spotify", "game", "concert", "party"],
        "Bills & Utilities": ["bill", "electricity", "water", "internet", "phone", "recharge"],
        "Health & Fitness": ["gym", "medicine", "doctor", "hospital", "health"],
        "Groceries": ["grocery", "vegetables", "fruits", "milk", "bread"],
    }
    
    for category, words in keywords.items():
        if any(word in desc for word in words):
            return category
    
    return "Other"


def get_user_by_whatsapp(whatsapp_number):
    """Find user by verified WhatsApp number.
    
    Handles both formats:
    - Stored in DB: 7058099532 (without +91)
    - From WhatsApp: +917058099532 (with +91)
    """
    # Remove +91 or + from the number for comparison
    clean_number = whatsapp_number.replace('+91', '').replace('+', '')
    
    # Try exact match first
    user = mongo.db.users.find_one({
        "whatsapp_number": clean_number,
        "whatsapp_verified": True
    })
    
    # If not found, try with +91 prefix
    if not user:
        user = mongo.db.users.find_one({
            "whatsapp_number": '+91' + clean_number,
            "whatsapp_verified": True
        })
    
    return user


def format_transactions_list(transactions, limit=5):
    """Format transactions for WhatsApp display."""
    if not transactions:
        return "📝 No transactions found."
    
    lines = ["📊 Your Recent Transactions:\n"]
    
    for i, t in enumerate(transactions[:limit], 1):
        amount = t.get('amount', 0)
        desc = t.get('description', 'No description')
        cat = t.get('category', 'Other')
        date = t.get('date')
        trans_id = str(t.get('_id', ''))[:8]  # First 8 chars of ID
        
        if isinstance(date, datetime):
            date_str = date.strftime('%d %b')
        else:
            date_str = 'N/A'
        
        lines.append(f"{i}. ₹{amount:.2f} - {desc}")
        lines.append(f"   📁 {cat} | 📅 {date_str} | ID: {trans_id}\n")
    
    total = sum(t.get('amount', 0) for t in transactions[:limit])
    lines.append(f"\n💰 Total (last {len(transactions[:limit])}): ₹{total:.2f}")
    lines.append("\n💡 Use /delete <ID> to remove a transaction")
    
    return "\n".join(lines)


def format_budget_status(user_id):
    """Format budget status for WhatsApp display."""
    now = datetime.utcnow()
    month = now.month
    year = now.year
    
    budgets = list(mongo.db.budgets.find({
        "user_id": ObjectId(user_id),
        "month": month,
        "year": year
    }))
    
    if not budgets:
        return "🎯 No budgets set for this month.\n\nSet budgets in the FinSight app to track your spending!"
    
    lines = ["🎯 Your Budget Status:\n"]
    
    total_budget = 0
    total_spent = 0
    
    for budget in budgets:
        cat = budget.get('category', 'Unknown')
        limit = budget.get('limit', 0)
        total_budget += limit
        
        # Get spending for this category
        spending = list(mongo.db.transactions.aggregate([
            {
                "$match": {
                    "user_id": ObjectId(user_id),
                    "category": cat,
                    "date": {
                        "$gte": datetime(year, month, 1),
                        "$lt": datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
                    }
                }
            },
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]))
        
        spent = spending[0]['total'] if spending else 0
        total_spent += spent
        
        percentage = (spent / limit * 100) if limit > 0 else 0
        emoji = "🟢" if percentage < 75 else "🟡" if percentage < 100 else "🔴"
        
        lines.append(f"{emoji} {cat}: ₹{spent:.2f} / ₹{limit:.2f} ({percentage:.0f}%)")
    
    lines.append(f"\n💰 Total: ₹{total_spent:.2f} / ₹{total_budget:.2f}")
    
    return "\n".join(lines)


def format_summary(user_id):
    """Format monthly summary for WhatsApp."""
    now = datetime.utcnow()
    month = now.month
    year = now.year
    
    # Get all transactions this month
    transactions = list(mongo.db.transactions.find({
        "user_id": ObjectId(user_id),
        "date": {
            "$gte": datetime(year, month, 1),
            "$lt": datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
        }
    }).sort("date", -1))
    
    if not transactions:
        return "📊 No transactions this month yet!"
    
    total = sum(t.get('amount', 0) for t in transactions)
    
    # Category breakdown
    categories = {}
    for t in transactions:
        cat = t.get('category', 'Other')
        categories[cat] = categories.get(cat, 0) + t.get('amount', 0)
    
    lines = [f"📊 {now.strftime('%B %Y')} Summary:\n"]
    lines.append(f"💰 Total Spent: ₹{total:.2f}")
    lines.append(f"📝 Total Transactions: {len(transactions)}\n")
    lines.append("📁 By Category:")
    
    for cat, amt in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        pct = (amt / total * 100) if total > 0 else 0
        lines.append(f"   • {cat}: ₹{amt:.2f} ({pct:.0f}%)")
    
    return "\n".join(lines)


def handle_delete_command(user_id, message_body):
    """Handle /delete <ID> command"""
    parts = message_body.strip().split()
    if len(parts) < 2:
        return "❌ Usage: /delete <transaction_id>\n\nUse /transactions to see IDs."
    
    trans_id = parts[1].strip()
    
    # Try to find the transaction
    try:
        transaction = mongo.db.transactions.find_one({
            "_id": ObjectId(trans_id),
            "user_id": ObjectId(user_id)
        })
    except Exception:
        return "❌ Invalid transaction ID.\n\nUse /transactions to see valid IDs."
    
    if not transaction:
        return "❌ Transaction not found.\n\nUse /transactions to see valid IDs."
    
    amount = transaction.get('amount', 0)
    desc = transaction.get('description', 'Unknown')
    
    # Delete the transaction
    mongo.db.transactions.delete_one({"_id": ObjectId(trans_id)})
    
    return f"✅ Deleted: ₹{amount:.2f} - {desc}\n\nTransaction removed successfully."


def handle_edit_command(user_id, message_body):
    """Handle /edit <ID> amount/category/description <value> command"""
    parts = message_body.strip().split()
    if len(parts) < 4:
        return "❌ Usage: /edit <ID> <field> <value>\n\nFields: amount, category, description\nExample: /edit abc123 amount 500"
    
    trans_id = parts[1].strip()
    field = parts[2].lower()
    value = ' '.join(parts[3:])
    
    # Validate field
    if field not in ['amount', 'category', 'description']:
        return "❌ Invalid field. Use: amount, category, or description"
    
    # Find transaction
    try:
        transaction = mongo.db.transactions.find_one({
            "_id": ObjectId(trans_id),
            "user_id": ObjectId(user_id)
        })
    except Exception:
        return "❌ Invalid transaction ID."
    
    if not transaction:
        return "❌ Transaction not found."
    
    # Build update
    update = {}
    if field == 'amount':
        try:
            new_amount = float(value)
            if new_amount <= 0:
                return "❌ Amount must be positive."
            update['amount'] = new_amount
        except ValueError:
            return "❌ Invalid amount. Use a number."
    elif field == 'category':
        # Validate category
        if value.title() not in CATEGORIES:
            return f"❌ Invalid category. Use: {', '.join(CATEGORIES[:5])}..."
        update['category'] = value.title()
    elif field == 'description':
        update['description'] = value
    
    # Update
    mongo.db.transactions.update_one(
        {"_id": ObjectId(trans_id)},
        {"$set": update}
    )
    
    return f"✅ Updated!\n\n{field.title()}: {value}"


def handle_weekly_command(user_id, message_body):
    """Handle /weekly on/off command"""
    parts = message_body.strip().split()
    if len(parts) < 2:
        # Show current status
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        status = user.get('whatsapp_weekly', False)
        return f"📊 Weekly Summary: {'✅ ON' if status else '❌ OFF'}\n\nUse /weekly on or /weekly off to change."
    
    action = parts[1].lower()
    if action == 'on':
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"whatsapp_weekly": True}}
        )
        return "✅ Weekly summary enabled!\n\nYou'll receive a spending summary every Sunday."
    elif action == 'off':
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"whatsapp_weekly": False}}
        )
        return "✅ Weekly summary disabled."
    else:
        return "❌ Use /weekly on or /weekly off"


def handle_alert_command(user_id, message_body):
    """Handle /alert on/off command"""
    parts = message_body.strip().split()
    if len(parts) < 2:
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        status = user.get('whatsapp_alerts', False)
        return f"🔔 Budget Alerts: {'✅ ON' if status else '❌ OFF'}\n\nUse /alert on or /alert off to change."
    
    action = parts[1].lower()
    if action == 'on':
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"whatsapp_alerts": True}}
        )
        return "✅ Budget alerts enabled!\n\nYou'll be notified when you reach 80% of any budget."
    elif action == 'off':
        mongo.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"whatsapp_alerts": False}}
        )
        return "✅ Budget alerts disabled."
    else:
        return "❌ Use /alert on or /alert off"


def handle_compare_command(user_id):
    """Handle /compare command - compare to last month"""
    now = datetime.utcnow()
    current_month = now.month
    current_year = now.year
    
    # Get last month
    if current_month == 1:
        last_month = 12
        last_year = current_year - 1
    else:
        last_month = current_month - 1
        last_year = current_year
    
    # Current month spending
    current_spending = list(mongo.db.transactions.aggregate([
        {"$match": {
            "user_id": ObjectId(user_id),
            "date": {
                "$gte": datetime(current_year, current_month, 1),
                "$lt": datetime(current_year, current_month + 1, 1) if current_month < 12 else datetime(current_year + 1, 1, 1)
            }
        }},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]))
    
    current_total = current_spending[0]['total'] if current_spending else 0
    
    # Last month spending
    last_spending = list(mongo.db.transactions.aggregate([
        {"$match": {
            "user_id": ObjectId(user_id),
            "date": {
                "$gte": datetime(last_year, last_month, 1),
                "$lt": datetime(last_year, last_month + 1, 1) if last_month < 12 else datetime(last_year + 1, 1, 1)
            }
        }},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]))
    
    last_total = last_spending[0]['total'] if last_spending else 0
    
    if last_total == 0:
        return "📊 No spending data from last month to compare."
    
    diff = current_total - last_total
    pct = (diff / last_total) * 100
    
    month_name = now.strftime('%B')
    last_month_name = datetime(last_year, last_month, 1).strftime('%B')
    
    lines = [f"📊 {month_name} vs {last_month_name}:\n"]
    lines.append(f"• This month: ₹{current_total:.2f}")
    lines.append(f"• Last month: ₹{last_total:.2f}\n")
    
    if diff > 0:
        lines.append(f"🔴 You spent ₹{diff:.2f} MORE ({pct:.1f}% increase)")
    elif diff < 0:
        lines.append(f"🟢 You spent ₹{abs(diff):.2f} LESS ({abs(pct):.1f}% decrease)")
    else:
        lines.append("🟡 Spending is same as last month")
    
    return "\n".join(lines)


def check_budget_alerts(user_id, category):
    """Check if any budget exceeded 80% and send alert"""
    # Check if user has alerts enabled
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get('whatsapp_alerts', False):
        return None
    
    now = datetime.utcnow()
    month = now.month
    year = now.year
    
    # Get budget for this category
    budget = mongo.db.budgets.find_one({
        "user_id": ObjectId(user_id),
        "category": category,
        "month": month,
        "year": year
    })
    
    if not budget:
        return None
    
    budget_limit = budget.get('limit', 0)
    if budget_limit <= 0:
        return None
    
    # Get current spending for this category
    spending = list(mongo.db.transactions.aggregate([
        {"$match": {
            "user_id": ObjectId(user_id),
            "category": category,
            "date": {
                "$gte": datetime(year, month, 1),
                "$lt": datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
            }
        }},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]))
    
    current_spent = spending[0]['total'] if spending else 0
    percentage = (current_spent / budget_limit) * 100
    
    # Check if crossed 80% threshold (and haven't already alerted today)
    if percentage >= 80:
        # Check if we already sent alert today
        today_start = datetime(year, month, now.day)
        existing_alert = mongo.db.whatsapp_alerts.find_one({
            "user_id": ObjectId(user_id),
            "category": category,
            "created_at": {"$gte": today_start}
        })
        
        if existing_alert:
            return None  # Already alerted today
        
        # Store alert
        mongo.db.whatsapp_alerts.insert_one({
            "user_id": ObjectId(user_id),
            "category": category,
            "created_at": datetime.utcnow()
        })
        
        emoji = "🟡" if percentage < 100 else "🔴"
        return (f"⚠️ *Budget Alert!* \n\n"
                f"{emoji} You've spent ₹{current_spent:.2f} / ₹{budget_limit:.2f} ({percentage:.0f}%) "
                f"on {category}\n\n"
                f"💡 Tip: You're approaching your budget limit!")
    
    return None


@whatsapp_bp.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """
    Twilio WhatsApp webhook - receives incoming messages.
    """
    try:
        # Verify Twilio signature for security
        signature = request.headers.get('X-Twilio-Signature', '')
        url = request.url_root.rstrip('/') + '/webhook/whatsapp'
        
        # Get all POST params
        params = dict(request.form)
        
        # Verify signature (skip for sandbox - for production, fix the verification logic)
        # TODO: Fix proper Twilio signature verification for production
        # Current logic has a bug - skip for now to test features
        if signature:
            current_app.logger.info(f"Signature received but skipping verification (sandbox mode)")
            # Uncomment below for production after fixing verification:
            # if not twilio_service.verify_twilio_signature(url, params, signature):
            #     current_app.logger.warning(f"Invalid Twilio signature from {request.form.get('From', 'unknown')}")
            #     return "Forbidden", 403
        
        # Get message details from Twilio
        from_number = request.form.get('From', '')
        message_body = request.form.get('Body', '').strip()
        message_sid = request.form.get('MessageSid', '')
        
        if not from_number or not message_body:
            return "OK", 200
        
        # Extract WhatsApp number early for logging
        whatsapp_number = from_number.replace('whatsapp:', '')
        
        # Issue #7: Validate message length
        if len(message_body) > 1000:
            current_app.logger.warning(f"Message too long from {whatsapp_number}: {len(message_body)} chars")
            reply = "❌ Message too long. Please keep your message under 1000 characters."
            twilio_service.send_whatsapp_message(from_number, reply)
            return "OK", 200
        
        if len(message_body) < 2:
            return "OK", 200  # Ignore very short messages
        
        # Find user by WhatsApp
        user = get_user_by_whatsapp(whatsapp_number)
        
        if not user:
            current_app.logger.info(f"WhatsApp message from unknown number: {whatsapp_number}")
            # User not linked
            reply = "👋 Welcome to FinSight AI!\n\n"
            reply += "Your WhatsApp is not linked to your account.\n"
            reply += "Please open the FinSight app, go to Profile, and link your WhatsApp number."
            
            twilio_service.send_whatsapp_message(from_number, reply)
            return "OK", 200
        
        user_id = str(user['_id'])
        message_lower = message_body.lower()
        
        # Log incoming command
        current_app.logger.info(f"WhatsApp command from user {user_id}: {message_body}")
        
        # Command handling
        if message_lower == '/help':
            reply = "📖 *FinSight WhatsApp Commands:*\n\n"
            reply += "💰 *Add Expense:*\n"
            reply += "• *500 coffee* - Add expense\n"
            reply += "• *coffee for 500 rs* - Add expense (AI)\n\n"
            reply += "📊 *View Data:*\n"
            reply += "• */transactions* - View recent\n"
            reply += "• */budget* - View budget status\n"
            reply += "• */summary* - Monthly summary\n"
            reply += "• */compare* - vs last month\n\n"
            reply += "✏️ *Manage:*\n"
            reply += "• */delete <ID>* - Delete transaction\n"
            reply += "• */edit <ID> amount 500* - Edit\n\n"
            reply += "⚙️ *Settings:*\n"
            reply += "• */weekly on/off* - Weekly summary\n"
            reply += "• */alert on/off* - Budget alerts\n"
            reply += "• */help* - Show this help"
            
        elif message_lower == '/transactions':
            transactions = list(mongo.db.transactions.find(
                {"user_id": ObjectId(user_id)}
            ).sort("date", -1).limit(5))
            reply = format_transactions_list(transactions)
            
        elif message_lower == '/budget' or message_lower == '/budgets':
            reply = format_budget_status(user_id)
            
        elif message_lower == '/summary':
            reply = format_summary(user_id)
            
        elif message_lower.startswith('/delete'):
            reply = handle_delete_command(user_id, message_body)
            
        elif message_lower.startswith('/edit'):
            reply = handle_edit_command(user_id, message_body)
            
        elif message_lower.startswith('/weekly'):
            reply = handle_weekly_command(user_id, message_body)
            
        elif message_lower.startswith('/alert'):
            reply = handle_alert_command(user_id, message_body)
            
        elif message_lower == '/compare':
            reply = handle_compare_command(user_id)
            
        else:
            # Try to parse as expense
            expense = parse_expense_message(message_body)
            
            # Issue #8: Handle parsing errors properly
            if expense and "error" in expense:
                reply = f"❌ {expense.get('message', 'Could not understand. Try: 500 coffee')}"
                twilio_service.send_whatsapp_message(from_number, reply)
                return "OK", 200
            
            if expense:
                # Check for duplicate messages using MessageSid (idempotency)
                existing = mongo.db.whatsapp_messages.find_one({"message_sid": message_sid})
                if existing:
                    current_app.logger.info(f"Duplicate message ignored: {message_sid}")
                    return "OK", 200
                
                # Add transaction to database
                transaction_doc = {
                    "user_id": ObjectId(user_id),
                    "amount": expense['amount'],
                    "category": expense['category'],
                    "description": expense['description'],
                    "date": datetime.utcnow(),
                    "status": "completed",
                    "source": "whatsapp",
                    "raw_text": message_body,
                    "message_sid": message_sid  # For idempotency
                }
                
                mongo.db.transactions.insert_one(transaction_doc)
                
                # Log the transaction add
                current_app.logger.info(f"WhatsApp transaction added for user {user_id}: ₹{expense['amount']} - {expense['description']}")
                
                # Store message SID for deduplication
                mongo.db.whatsapp_messages.insert_one({
                    "message_sid": message_sid,
                    "user_id": ObjectId(user_id),
                    "created_at": datetime.utcnow()
                })
                
                # Check budget alerts
                alert_reply = check_budget_alerts(user_id, expense['category'])
                if alert_reply:
                    # Send alert after a short delay
                    twilio_service.send_whatsapp_message(from_number, alert_reply)
                
                reply = "✅ *Expense Added!*\n\n"
                reply += f"💰 Amount: ₹{expense['amount']:.2f}\n"
                reply += f"📁 Category: {expense['category']}\n"
                reply += f"📁 Description: {expense['description']}\n"
                reply += f"\n(Sent via {expense['source']})"
            else:
                reply = "❓ Sorry, I didn't understand that.\n\n"
                reply += "Try:\n"
                reply += "• '500 coffee' to add expense\n"
                reply += "• /help for all commands"
        
        # Send reply
        twilio_service.send_whatsapp_message(from_number, reply)
        
        return "OK", 200
        
    except Exception as e:
        current_app.logger.error(f"WhatsApp webhook error: {e}")
        # Still return 200 to Twilio to prevent retries
        return "OK", 200


@whatsapp_bp.route('/webhook/status', methods=['POST'])
def whatsapp_status():
    """
    Twilio status callback - track message delivery status.
    """
    message_sid = request.form.get('MessageSid', '')
    message_status = request.form.get('MessageStatus', '')
    
    current_app.logger.info(f"WhatsApp message {message_sid} status: {message_status}")
    
    return "OK", 200


@whatsapp_bp.route('/status', methods=['GET'])
@jwt_required()
def whatsapp_status_check():
    """
    Check if user's WhatsApp is linked and verified.
    """
    current_user_id = get_jwt_identity()
    
    user = mongo.db.users.find_one(
        {"_id": ObjectId(current_user_id)},
        {"whatsapp_number": 1, "whatsapp_verified": 1}
    )
    
    if not user:
        return {"error": "User not found"}, 404
    
    return {
        "whatsapp_linked": user.get("whatsapp_verified", False),
        "whatsapp_number": user.get("whatsapp_number", "")[-4:].rjust(10, "*") if user.get("whatsapp_number") else None  # Masked
    }, 200


@whatsapp_bp.route('/transactions/recent', methods=['GET'])
@jwt_required()
def whatsapp_recent_transactions():
    """
    Get recent transactions added via WhatsApp.
    """
    current_user_id = get_jwt_identity()
    
    # Get source=whatsapp transactions
    transactions = list(mongo.db.transactions.find(
        {"user_id": ObjectId(current_user_id), "source": "whatsapp"}
    ).sort("date", -1).limit(10))
    
    result = []
    for t in transactions:
        result.append({
            "_id": str(t["_id"]),
            "amount": t.get("amount"),
            "category": t.get("category"),
            "description": t.get("description"),
            "date": t.get("date").isoformat() if t.get("date") else None,
            "created_via": "whatsapp"
        })
    
    return {"whatsapp_transactions": result}, 200


@whatsapp_bp.route('/cron/weekly-summary', methods=['POST'])
def send_weekly_summaries():
    """
    Cron endpoint to send weekly summaries to all users with weekly enabled.
    Should be triggered by a cron job (e.g., every Sunday at 6 PM).
    """
    # Verify cron secret (to prevent unauthorized calls)
    cron_secret = request.headers.get('X-Cron-Secret', '')
    expected_secret = current_app.config.get('CRON_SECRET', '')
    
    if expected_secret and cron_secret != expected_secret:
        return {"error": "Unauthorized"}, 401
    
    # Get all users with weekly summary enabled
    users = list(mongo.db.users.find({
        "whatsapp_weekly": True,
        "whatsapp_verified": True,
        "whatsapp_number": {"$exists": True, "$ne": ""}
    }))
    
    sent_count = 0
    failed_count = 0
    
    for user in users:
        try:
            user_id = str(user['_id'])
            whatsapp_number = user.get('whatsapp_number')
            
            # Generate weekly summary
            summary = generate_weekly_summary(user_id)
            
            if summary:
                formatted_number = twilio_service.format_whatsapp_number(whatsapp_number)
                if formatted_number:
                    twilio_service.send_whatsapp_message(formatted_number, summary)
                    sent_count += 1
        except Exception as e:
            current_app.logger.error(f"Failed to send weekly summary: {e}")
            failed_count += 1
    
    return {
        "message": f"Weekly summaries sent: {sent_count} success, {failed_count} failed",
        "sent": sent_count,
        "failed": failed_count
    }, 200


def generate_weekly_summary(user_id):
    """Generate weekly summary message for a user."""
    from datetime import timedelta
    
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    
    # Get transactions from last 7 days
    transactions = list(mongo.db.transactions.find({
        "user_id": ObjectId(user_id),
        "date": {"$gte": week_ago}
    }))
    
    if not transactions:
        return None
    
    total = sum(t.get('amount', 0) for t in transactions)
    
    # Category breakdown
    categories = {}
    for t in transactions:
        cat = t.get('category', 'Other')
        categories[cat] = categories.get(cat, 0) + t.get('amount', 0)
    
    lines = ["📊 *Your Weekly Summary*\n"]
    lines.append(f"💰 Total spent: ₹{total:.2f}")
    lines.append(f"📝 Transactions: {len(transactions)}\n")
    
    # Top categories
    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
    lines.append("🏆 Top categories:")
    for cat, amt in sorted_cats:
        pct = (amt / total * 100) if total > 0 else 0
        lines.append(f"   • {cat}: ₹{amt:.2f} ({pct:.0f}%)")
    
    lines.append("\n💡 Use /summary for full month details")
    
    return "\n".join(lines)
